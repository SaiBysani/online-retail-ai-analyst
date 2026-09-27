"""Customer analysis: RFM segments, high-value customers at risk, repeat-purchase behaviour.

Builds on the approved revenue definition (CLAUDE.md, via retail_common.py) and reuses
retail_analysis.customer_tables / repeat_tables so customer counts, concentration and
repeat rates reconcile with outputs/analysis/metrics.json. Writes:

- outputs/customers/*.csv                one evidence table per topic
- outputs/customers/customer_metrics.json headline numbers (value, definition, source) + assumptions

Assumptions (ASSUMPTIONS below; also written to customer_metrics.json):
- Scope: approved-revenue rows with a Customer ID only. Rows without one (13.1% of revenue)
  are excluded, so customer totals do not reconcile to total revenue.
- Monetary = approved revenue per customer (gross). Cancellations are never netted in; each
  customer's cancelled product value (C invoices, product codes) is reported separately.
- Frequency = distinct purchase days (same-day split invoices count once); distinct invoices kept too.
- Recency = days from the last purchase day to SNAPSHOT (2011-12-10, the day after the last invoice).
  Dec 2011 is partial (1-9 Dec) and is never treated as a full month.
- R, F, M scored 1-5 by quintile of percentile rank (ties share a score; recency reversed so
  recent = 5). Segments come from the ordered rule table SEGMENT_RULES (first match wins).
- Country: one per customer = the country on most of their revenue lines (ties: alphabetical).
- Usual gap = median days between a customer's consecutive purchase days (needs 2+ purchase days).
- High-value at risk = top TOP_VALUE_SHARE of customers by monetary, 2+ purchase days, recency >
  GAP_MULTIPLE x usual gap AND recency > MIN_RECENCY_DAYS. One-day high-value customers have no usual
  gap; they are counted separately as "high-value one-off, lapsed" (recency > MIN_RECENCY_DAYS).
- Reversed sales: revenue lines cancelled by the same customer within 24h (same code + price + opposite
  quantity, or a manual M cancellation of equal value), the data-quality rule. They stay in monetary
  (approved definition) but are flagged, and a sensitivity view removes them.
- Distortion flags: reversed sales, single-order-dominated customers (largest purchase day >=
  DOMINANT_SHARE of monetary and >= LARGE_ORDER_GBP), and history starting in Dec 2009 (left-censored).
- Repeat-within-N-days metrics use customers first seen 2010-01-01 or later (Dec 2009 is only a
  baseline) with at least REPEAT_WINDOW_DAYS of observation before SNAPSHOT.

Usage (from the repo root):
    .venv/bin/python scripts/customer_analysis.py [--out-dir outputs/customers]
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from retail_analysis import customer_tables, repeat_tables
from retail_common import OUT, cancellation_rows, load, revenue_rows

SNAPSHOT = pd.Timestamp("2011-12-10")
DATA_START = pd.Timestamp("2009-12-01")
BASELINE_END = pd.Timestamp("2010-01-01")      # first purchases before this are the Dec 2009 baseline
TOP_VALUE_SHARE = 0.20
GAP_MULTIPLE = 2.0
MIN_RECENCY_DAYS = 90
REVERSAL_WINDOW = pd.Timedelta(hours=24)
LARGE_ORDER_GBP = 5000
DOMINANT_SHARE = 0.5
REPEAT_WINDOW_DAYS = 180
HIGH_CANCEL_RATE = 0.25
ANALYSIS_REVERSED = OUT / "analysis" / "anomaly_reversed_orders.csv"
MIN_FIRST_ORDERS_PER_PRODUCT = 100
MIN_CUSTOMERS_PER_COUNTRY = 30

SEGMENT_RULES = [  # (segment, rule text, predicate on R, F, M scores); first match wins
    ("Champions", "R>=4 and F>=4 and M>=4", lambda r, f, m: (r >= 4) & (f >= 4) & (m >= 4)),
    ("Loyal", "R>=3 and F>=3", lambda r, f, m: (r >= 3) & (f >= 3)),
    ("Big spenders", "R>=3 and M>=4 (F<=2)", lambda r, f, m: (r >= 3) & (m >= 4)),
    ("New", "R>=4 and F=1", lambda r, f, m: (r >= 4) & (f == 1)),
    ("Can't lose", "R<=2 and F>=4 and M>=4", lambda r, f, m: (r <= 2) & (f >= 4) & (m >= 4)),
    ("At risk", "R<=2 and (F>=3 or M>=3)", lambda r, f, m: (r <= 2) & ((f >= 3) | (m >= 3))),
    ("Need attention", "R>=3 (low F and M)", lambda r, f, m: r >= 3),
    ("Hibernating", "everything else (R<=2, F<=2, M<=2)", lambda r, f, m: r > 0),
]

ASSUMPTIONS = [
    "Scope: approved-revenue rows with a Customer ID only; rows without one are excluded "
    "(see revenue_share_without_customer_id), so customer totals do not reconcile to total revenue.",
    "Monetary = approved (gross) revenue per customer; cancellations are never netted in and are reported "
    "separately per customer as cancel_value (C invoices, product codes).",
    "Frequency = distinct purchase days (same-day split invoices count once); distinct invoices kept as orders.",
    f"Recency = days from last purchase day to snapshot {SNAPSHOT.date()} (day after the last invoice). "
    "Dec 2011 is partial (1-9 Dec).",
    "R, F, M scored 1-5 by quintile of percentile rank (ties share a score; recent = 5). Segments follow "
    "the ordered rule table in rfm_segment_rules.csv (first match wins).",
    "Country per customer = country on most of their revenue lines (ties alphabetical); 12 customers have revenue lines in >1 (13 if cancellation rows are counted).",
    "Usual gap = median days between a customer's consecutive purchase days (2+ purchase days needed).",
    f"High-value at risk = top {TOP_VALUE_SHARE:.0%} by monetary, 2+ purchase days, recency > "
    f"{GAP_MULTIPLE:g} x usual gap and > {MIN_RECENCY_DAYS} days. One-day high-value customers are counted "
    "separately (no usual gap).",
    "Reversed sales = revenue lines cancelled by the same customer within 24h (data-quality rule). Kept in "
    "monetary per the approved definition, flagged, and removed in the sensitivity views.",
    "Dec 2009 is the first month of data: customers first seen then are left-censored (flag "
    "starts_dec2009) and are a cohort baseline, not acquisition.",
    f"Repeat-within-{REPEAT_WINDOW_DAYS}-days metrics use customers first seen from 2010-01-01 with at "
    f"least {REPEAT_WINDOW_DAYS} days of observation before the snapshot.",
]


def score(s, ascending=True):
    """1-5 quintile score from percentile rank; tied values share a score."""
    p = s.rank(pct=True, method="average", ascending=ascending)
    return np.clip(np.ceil(p * 5), 1, 5).astype(int)


def reversed_lines(rev, df):
    """Revenue rows reversed by the same customer within 24h (same rule as data_quality.py §10)."""
    d = df[~df.is_overlap_copy]
    r = rev.dropna(subset=["Customer ID"]).reset_index().rename(columns={"index": "rid"})
    cc = d[d.is_cancel].dropna(subset=["Customer ID"])
    m1 = r.merge(cc[["Customer ID", "StockCode", "Price", "Quantity", "InvoiceDate", "Invoice"]]
                 .assign(Quantity=lambda x: -x.Quantity),
                 on=["Customer ID", "StockCode", "Price", "Quantity"], suffixes=("", "_c"))
    cm = cc[cc.StockCode == "M"][["Customer ID", "line_value", "InvoiceDate", "Invoice"]].assign(
        line_value=lambda x: (-x.line_value).round(2))
    m2 = r.assign(line_value=r.line_value.round(2)).merge(cm, on=["Customer ID", "line_value"], suffixes=("", "_c"))
    matched = pd.concat([m1, m2])
    dt = matched.InvoiceDate_c - matched.InvoiceDate
    matched = matched[(dt >= pd.Timedelta(0)) & (dt <= REVERSAL_WINDOW)].drop_duplicates("rid")
    return pd.Index(matched.rid)


def purchase_days(rc):
    days = rc.assign(day=rc.InvoiceDate.dt.normalize()).groupby(["Customer ID", "day"]).line_value.sum()
    return days.reset_index().sort_values(["Customer ID", "day"])


def build_customers(rev, rc, canc, rev_idx):
    c, conc, lifecycle, cohorts = customer_tables(rev)
    c = c.rename(columns={"revenue": "monetary", "orders": "invoices"})
    c["first_day"], c["last_day"] = c["first"].dt.normalize(), c["last"].dt.normalize()
    c["recency_days"] = (SNAPSHOT - c.last_day).dt.days
    c["tenure_days"] = (c.last_day - c.first_day).dt.days

    pdays = purchase_days(rc)
    pdays["gap"] = pdays.groupby("Customer ID").day.diff().dt.days
    c["usual_gap_days"] = pdays.groupby("Customer ID").gap.median()
    second = pdays.groupby("Customer ID").day.nth(1)
    c["days_first_to_second"] = (pd.Series(second.values, index=pdays.loc[second.index, "Customer ID"])
                                 - c.first_day).dt.days
    c["largest_day_value"] = pdays.groupby("Customer ID").line_value.max()
    c["largest_day_share"] = c.largest_day_value / c.monetary

    fy = rc[rc.fy.isin(["FY1", "FY2"])].pivot_table(index="Customer ID", columns="fy", values="line_value",
                                                    aggfunc="sum", fill_value=0)
    c["revenue_FY1"] = fy.FY1.reindex(c.index, fill_value=0)
    c["revenue_FY2"] = fy.FY2.reindex(c.index, fill_value=0)
    c["revenue_last_365d"] = rc[rc.InvoiceDate >= SNAPSHOT - pd.Timedelta(days=365)].groupby(
        "Customer ID").line_value.sum().reindex(c.index, fill_value=0)

    cc = canc.dropna(subset=["Customer ID"])
    c["cancel_value"] = -cc.groupby("Customer ID").line_value.sum().reindex(c.index, fill_value=0)
    c["cancel_rate"] = c.cancel_value / (c.monetary + c.cancel_value)
    c["reversed_value"] = rev.loc[rev_idx].groupby("Customer ID").line_value.sum().reindex(c.index, fill_value=0)
    c["monetary_excl_reversed"] = c.monetary - c.reversed_value

    # Country: mode over revenue lines (customer_tables); ties resolve alphabetically.
    n_countries = rc.groupby("Customer ID").Country.nunique()
    c["n_countries"] = n_countries.reindex(c.index)
    c["starts_dec2009"] = c.first_day < BASELINE_END
    c["single_order_dominated"] = (c.largest_day_share >= DOMINANT_SHARE) & (c.largest_day_value >= LARGE_ORDER_GBP)
    c["high_cancel"] = c.cancel_rate >= HIGH_CANCEL_RATE
    big_rev = pd.read_csv(ANALYSIS_REVERSED, dtype={"Customer ID": str})["Customer ID"] if ANALYSIS_REVERSED.exists() \
        else pd.Series(dtype=str)
    c["in_analysis_reversed_orders"] = c.index.isin(big_rev)
    flags = {"reversed>=50%": c.reversed_value >= 0.5 * c.monetary, "reversed_sale": c.reversed_value > 0,
             "big_order_reversed(analysis)": c.in_analysis_reversed_orders,
             "single_order_dominated": c.single_order_dominated, "high_cancel": c.high_cancel,
             "starts_dec2009": c.starts_dec2009}
    c["distortion_flags"] = [";".join(k for k, v in flags.items() if v.iloc[i]) for i in range(len(c))]

    c["R"] = score(c.recency_days, ascending=False)
    c["F"] = score(c.purchase_days)
    c["M"] = score(c.monetary)
    c["segment"] = None
    for name, _, rule in SEGMENT_RULES:
        hit = c.segment.isna() & rule(c.R, c.F, c.M)
        c.loc[hit, "segment"] = name
    c["value_rank"] = c.monetary.rank(ascending=False, method="first").astype(int)
    return c, conc, cohorts, pdays


def at_risk_mask(c, top_share=TOP_VALUE_SHARE, gap_mult=GAP_MULTIPLE, min_rec=MIN_RECENCY_DAYS, col="monetary"):
    top = c[col].rank(ascending=False, method="first") <= round(top_share * len(c))
    lapsed = (c.purchase_days >= 2) & (c.recency_days > gap_mult * c.usual_gap_days) & (c.recency_days > min_rec)
    return top & lapsed, top


def segment_table(c):
    g = c.groupby("segment").agg(customers=("monetary", "size"), revenue=("monetary", "sum"),
                                 avg_recency_days=("recency_days", "mean"),
                                 avg_purchase_days=("purchase_days", "mean"),
                                 avg_monetary=("monetary", "mean"), avg_R=("R", "mean"), avg_F=("F", "mean"),
                                 avg_M=("M", "mean"), revenue_last_365d=("revenue_last_365d", "sum"),
                                 reversed_value=("reversed_value", "sum"), cancel_value=("cancel_value", "sum"))
    g["share_customers"] = g.customers / g.customers.sum()
    g["share_revenue"] = g.revenue / g.revenue.sum()
    return g.reindex([s for s, _, _ in SEGMENT_RULES]).dropna(how="all")


def score_bounds(c):
    rows = []
    for k, col in [("R", "recency_days"), ("F", "purchase_days"), ("M", "monetary")]:
        for s in range(1, 6):
            v = c.loc[c[k] == s, col]
            rows.append({"score": k, "value": s, "customers": len(v), "min": v.min(), "max": v.max()})
    return pd.DataFrame(rows)


def repeat_views(c, rc):
    """First-to-second timing, and what first orders of repeaters vs one-off buyers look like."""
    elig = c[(c.first_day >= BASELINE_END) & (c.first_day <= SNAPSHOT - pd.Timedelta(days=REPEAT_WINDOW_DAYS))].copy()
    elig["repeat_in_window"] = elig.days_first_to_second.le(REPEAT_WINDOW_DAYS)
    elig["repeat_ever"] = elig.purchase_days >= 2

    first = rc.merge(c[["first_day"]], left_on="Customer ID", right_index=True)
    first = first[first.InvoiceDate.dt.normalize() == first.first_day]
    fo = first.groupby("Customer ID").agg(first_value=("line_value", "sum"), first_lines=("StockCode", "size"),
                                          first_products=("StockCode", "nunique"))
    elig = elig.join(fo)

    def rate_table(key, frame=elig):
        t = frame.groupby(key, observed=True).agg(customers=("repeat_in_window", "size"),
                                                  repeat_in_window=("repeat_in_window", "mean"),
                                                  repeat_ever=("repeat_ever", "mean"),
                                                  median_first_value=("first_value", "median"),
                                                  median_monetary=("monetary", "median"))
        return t

    bands = pd.cut(elig.first_value, [0, 100, 250, 500, 1000, 2500, np.inf],
                   labels=["<£100", "£100-250", "£250-500", "£500-1k", "£1k-2.5k", "£2.5k+"])
    by_value = rate_table(bands)
    by_value.index.name = "first_order_value"
    lbands = pd.cut(elig.first_products, [0, 5, 10, 20, 50, np.inf], labels=["1-5", "6-10", "11-20", "21-50", "51+"])
    by_lines = rate_table(lbands)
    by_lines.index.name = "first_order_distinct_products"

    by_country = rate_table("country")
    uk = rate_table(np.where(elig.country == "United Kingdom", "United Kingdom", "Non-UK"))
    uk.index.name = "country"
    by_country = pd.concat([uk, by_country[by_country.customers >= MIN_CUSTOMERS_PER_COUNTRY]
                            .drop("United Kingdom", errors="ignore")]).sort_values("customers", ascending=False)

    # First product: customers whose first order contained the product (products in >= N first orders).
    fp = first[first["Customer ID"].isin(elig.index)][["Customer ID", "StockCode", "Description"]]
    fp = fp.drop_duplicates(["Customer ID", "StockCode"]).join(elig[["repeat_in_window", "first_value"]],
                                                               on="Customer ID")
    by_prod = fp.groupby("StockCode").agg(description=("Description", lambda s: s.dropna().str.strip().mode().iat[0]
                                                       if s.notna().any() else ""),
                                          customers=("repeat_in_window", "size"),
                                          repeat_in_window=("repeat_in_window", "mean"),
                                          median_first_value=("first_value", "median"))
    by_prod = by_prod[by_prod.customers >= MIN_FIRST_ORDERS_PER_PRODUCT].sort_values("repeat_in_window",
                                                                                     ascending=False)

    # FY acquisition comparison: new customers of FY1 (excl. Dec 2009) vs FY2, same observation window.
    # Like-for-like months (Jan-Jun first purchases) so seasonality does not drive the comparison.
    m = elig.first_day.dt.month.le(6)
    acq = np.where(elig.first_day.dt.year == 2010, "FY1: first bought Jan-Jun 2010", "FY2: first bought Jan-Jun 2011")
    by_fy = rate_table(pd.Series(acq, index=elig.index)[m], elig[m])
    by_fy.index.name = "acquisition"

    # One-off vs repeat profile (all identified customers).
    allc = c.join(fo)
    allc["buyer_type"] = np.where(allc.purchase_days >= 2, "repeat (2+ days)", "one-off (1 day)")
    profile = allc.groupby("buyer_type").agg(customers=("monetary", "size"), revenue=("monetary", "sum"),
                                             median_first_value=("first_value", "median"),
                                             median_first_products=("first_products", "median"),
                                             share_uk=("country", lambda s: (s == "United Kingdom").mean()),
                                             share_starts_dec2009=("starts_dec2009", "mean"),
                                             median_recency_days=("recency_days", "median"),
                                             median_monetary=("monetary", "median"),
                                             cancel_value=("cancel_value", "sum"))
    profile["share_customers"] = profile.customers / profile.customers.sum()
    profile["share_revenue"] = profile.revenue / profile.revenue.sum()

    # Time from first to second purchase day (repeaters), and cumulative repeat curve (eligible).
    rep = c[c.purchase_days >= 2]
    tb = pd.cut(rep.days_first_to_second, [0, 7, 30, 60, 90, 180, 365, np.inf],
                labels=["1-7", "8-30", "31-60", "61-90", "91-180", "181-365", "366+"])
    t2 = rep.groupby(tb, observed=False).size().rename("customers").to_frame()
    t2["share"] = t2.customers / t2.customers.sum()
    t2["cum_share"] = t2.share.cumsum()
    t2.index.name = "days_first_to_second"
    curve = pd.DataFrame({"within_days": [30, 60, 90, 180]})
    curve["share_repeated"] = [float(elig.days_first_to_second.le(d).mean()) for d in curve.within_days]
    curve["eligible_customers"] = len(elig)
    return elig, by_value, by_lines, by_country, by_prod, by_fy, profile, t2, curve


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", type=Path, default=OUT / "customers")
    out = ap.parse_args().out_dir
    out.mkdir(parents=True, exist_ok=True)

    df = load()
    rev, _ = revenue_rows(df)
    rc = rev.dropna(subset=["Customer ID"])
    canc = cancellation_rows(df, products_only=True)
    rev_idx = reversed_lines(rev, df)

    c, conc, cohorts, pdays = build_customers(rev, rc, canc, rev_idx)
    repeat_bands, mean_gap_median = repeat_tables(c.rename(columns={"monetary": "revenue"}))
    segs = segment_table(c)
    rules = pd.DataFrame([(s, t) for s, t, _ in SEGMENT_RULES], columns=["segment", "rule"])
    rules.index = pd.RangeIndex(1, len(rules) + 1, name="order")

    # High-value at risk, with the sensitivity grid.
    risk, top = at_risk_mask(c)
    flag_cols = ["country", "monetary", "monetary_excl_reversed", "reversed_value", "revenue_FY2",
                 "revenue_last_365d", "cancel_value", "invoices", "purchase_days", "first_day", "last_day",
                 "recency_days", "usual_gap_days", "segment", "value_rank", "starts_dec2009",
                 "single_order_dominated", "largest_day_share", "cancel_rate", "distortion_flags"]
    at_risk = c.loc[risk, flag_cols].sort_values("monetary", ascending=False)
    at_risk["recency_over_gap"] = at_risk.recency_days / at_risk.usual_gap_days
    oneoff_lapsed = top & (c.purchase_days == 1) & (c.recency_days > MIN_RECENCY_DAYS)
    sens = []
    for col in ["monetary", "monetary_excl_reversed"]:
        for ts in (0.10, 0.20):
            for gm in (1.5, 2.0, 3.0):
                for mr in (60, 90, 180):
                    mk, _ = at_risk_mask(c, ts, gm, mr, col)
                    sens.append({"value_basis": col, "top_share": ts, "gap_multiple": gm, "min_recency_days": mr,
                                 "customers": int(mk.sum()), "monetary": c.loc[mk, "monetary"].sum(),
                                 "revenue_last_365d": c.loc[mk, "revenue_last_365d"].sum(),
                                 "revenue_FY2": c.loc[mk, "revenue_FY2"].sum(),
                                 "default": (col, ts, gm, mr) == ("monetary", TOP_VALUE_SHARE, GAP_MULTIPLE,
                                                                  MIN_RECENCY_DAYS)})
    sens = pd.DataFrame(sens)

    # Top customers with distortion flags; concentration with and without reversed sales.
    top_customers = c.nsmallest(25, "value_rank")[flag_cols + ["R", "F", "M"]]
    conc_x = c.monetary_excl_reversed.sort_values(ascending=False)
    conc["share_excl_reversed"] = [conc_x.iloc[:k].sum() / conc_x.sum() for k in conc.customers]
    conc = conc.set_index("top_share_of_customers")
    top20_x = c.monetary_excl_reversed.rank(ascending=False, method="first") <= round(TOP_VALUE_SHARE * len(c))
    reversed_by_cust = c[c.reversed_value > 0][["country", "monetary", "reversed_value", "monetary_excl_reversed",
                                                "value_rank", "segment"]].sort_values("reversed_value",
                                                                                      ascending=False)
    reversed_by_cust["in_top20_gross"] = top.reindex(reversed_by_cust.index)
    reversed_by_cust["in_top20_excl_reversed"] = top20_x.reindex(reversed_by_cust.index)
    multi = (rc[rc["Customer ID"].isin(c.index[c.n_countries > 1])]
             .groupby(["Customer ID", "Country"]).agg(lines=("line_value", "size"), revenue=("line_value", "sum"))
             .join(c.country.rename("assigned_country")))

    elig, by_value, by_lines, by_country, by_prod, by_fy, profile, t2, curve = repeat_views(c, rc)

    customers_out = c.drop(columns=["first", "last", "cum_share"])
    tables = {
        "customers_rfm.csv": customers_out, "rfm_segments.csv": segs, "rfm_segment_rules.csv": rules,
        "rfm_score_bounds.csv": score_bounds(c), "high_value_at_risk.csv": at_risk,
        "at_risk_sensitivity.csv": sens, "top_customers.csv": top_customers, "concentration.csv": conc,
        "reversed_by_customer.csv": reversed_by_cust, "multi_country_customers.csv": multi,
        "repeat_bands.csv": repeat_bands, "repeat_first_to_second.csv": t2, "repeat_curve.csv": curve,
        "repeat_by_first_order_value.csv": by_value, "repeat_by_first_order_products.csv": by_lines,
        "repeat_by_country.csv": by_country, "repeat_by_first_product.csv": by_prod,
        "repeat_by_acquisition_fy.csv": by_fy, "one_off_vs_repeat.csv": profile,
        "cohort_retention.csv": cohorts,
    }
    for name, t in tables.items():
        t.to_csv(out / name, float_format="%.4f", index=name not in ("at_risk_sensitivity.csv", "rfm_score_bounds.csv"))

    total = rev.line_value.sum()
    ident = c.monetary.sum()
    rep = c.purchase_days >= 2
    dflt = sens[sens["default"]].iloc[0]
    dflt_x = sens[(sens.value_basis == "monetary_excl_reversed") & (sens.top_share == TOP_VALUE_SHARE)
                  & (sens.gap_multiple == GAP_MULTIPLE) & (sens.min_recency_days == MIN_RECENCY_DAYS)].iloc[0]

    def m(value, definition, source):
        if isinstance(value, (np.floating, np.integer)):
            value = value.item()
        if isinstance(value, float):
            value = round(value, 4)
        return {"value": value, "definition": definition, "source": source}

    seg_share = {f"segment_revenue_share_{s.lower().replace(' ', '_').replace(chr(39), '')}":
                 m(float(segs.loc[s, "share_revenue"]), f"Share of identified revenue from {s} "
                   f"({int(segs.loc[s, 'customers'])} customers)", "rfm_segments.csv") for s in segs.index}
    metrics = {
        "assumptions": ASSUMPTIONS,
        "constants": {"snapshot": str(SNAPSHOT.date()), "top_value_share": TOP_VALUE_SHARE,
                      "gap_multiple": GAP_MULTIPLE, "min_recency_days": MIN_RECENCY_DAYS,
                      "reversal_window_hours": 24, "large_order_gbp": LARGE_ORDER_GBP,
                      "dominant_share": DOMINANT_SHARE, "repeat_window_days": REPEAT_WINDOW_DAYS},
        "tables": sorted(tables),
        "metrics": {
            "revenue_total": m(total, "Approved revenue, all rows", "outputs/analysis/metrics.json"),
            "revenue_identified": m(ident, "Approved revenue on rows with a Customer ID", "customers_rfm.csv"),
            "revenue_share_without_customer_id": m(1 - ident / total, "Share of approved revenue with no "
                                                   "Customer ID (excluded from all customer metrics)",
                                                   "outputs/analysis/metrics.json"),
            "customers": m(int(len(c)), "Distinct Customer IDs with approved revenue", "customers_rfm.csv"),
            "customers_cancel_only": m(int((~canc.dropna(subset=["Customer ID"])["Customer ID"]
                                            .drop_duplicates().isin(c.index)).sum()),
                                       "Customer IDs with cancellations but no approved revenue (not in RFM)",
                                       "customers_rfm.csv"),
            "customers_multi_country": m(int((c.n_countries > 1).sum()), "Customers with revenue lines in >1 "
                                         "country; assigned their modal country", "multi_country_customers.csv"),
            "customers_starting_dec2009": m(int(c.starts_dec2009.sum()), "Customers first seen in Dec 2009 "
                                            "(left-censored history)", "customers_rfm.csv"),
            "monetary_median": m(float(c.monetary.median()), "Median revenue per customer", "customers_rfm.csv"),
            "monetary_mean": m(float(c.monetary.mean()), "Mean revenue per customer", "customers_rfm.csv"),
            "top_1pct_customer_share": m(float(conc.loc[.01, "share_of_identified_revenue"]),
                                         "Identified revenue share of top 1% customers", "concentration.csv"),
            "top_10pct_customer_share": m(float(conc.loc[.10, "share_of_identified_revenue"]),
                                          "Identified revenue share of top 10% customers", "concentration.csv"),
            "top_20pct_customer_share": m(float(conc.loc[.20, "share_of_identified_revenue"]),
                                          "Identified revenue share of top 20% customers", "concentration.csv"),
            "top_1pct_share_excl_reversed": m(float(conc.loc[.01, "share_excl_reversed"]),
                                              "As top_1pct_customer_share with reversed sales removed",
                                              "concentration.csv"),
            "reversed_value_identified": m(float(c.reversed_value.sum()), "Revenue on lines reversed by the same "
                                           "customer within 24h (kept in monetary)", "reversed_by_customer.csv"),
            "reversed_lines": m(int(len(rev_idx)), "Revenue lines reversed within 24h", "reversed_by_customer.csv"),
            "customers_with_reversed_sales": m(int((c.reversed_value > 0).sum()), "Customers with any reversed "
                                               "sale", "reversed_by_customer.csv"),
            "top20_changed_by_reversals": m(int((top & ~top20_x).sum()),
                                            "Customers who leave the top 20% when reversed sales are removed",
                                            "reversed_by_customer.csv"),
            "customer_cancel_value": m(float(c.cancel_value.sum()), "Cancelled product value of identified "
                                       "customers (C invoices; not netted into monetary)", "customers_rfm.csv"),
            **seg_share,
            "high_value_at_risk_customers": m(int(risk.sum()), "Top 20% by monetary, 2+ purchase days, recency > "
                                              "2x usual gap and > 90 days", "high_value_at_risk.csv"),
            "high_value_at_risk_monetary": m(float(at_risk.monetary.sum()), "Lifetime monetary of those customers",
                                             "high_value_at_risk.csv"),
            "high_value_at_risk_revenue_FY2": m(float(at_risk.revenue_FY2.sum()), "Their FY2 (Dec10-Nov11) "
                                                "revenue: the annual revenue at stake", "high_value_at_risk.csv"),
            "high_value_at_risk_monetary_excl_reversed": m(float(at_risk.monetary_excl_reversed.sum()),
                                                           "As above, excluding reversed sales",
                                                           "high_value_at_risk.csv"),
            "high_value_at_risk_share_of_top20": m(float(risk.sum() / top.sum()), "At-risk share of top-20% "
                                                   "customers", "high_value_at_risk.csv"),
            "high_value_at_risk_flagged": m(int((at_risk.distortion_flags.str.replace("starts_dec2009", "")
                                                 .str.strip(";") != "").sum()),
                                            "At-risk customers with a distortion flag other than starts_dec2009",
                                            "high_value_at_risk.csv"),
            "high_value_at_risk_customers_excl_reversed": m(int(dflt_x.customers), "At-risk count when top 20% "
                                                            "is ranked on monetary excluding reversed sales",
                                                            "at_risk_sensitivity.csv"),
            "high_value_at_risk_monetary_excl_reversed_basis": m(float(dflt_x.monetary), "Their gross monetary",
                                                                 "at_risk_sensitivity.csv"),
            "high_value_at_risk_revenue_FY2_excl_reversed_basis": m(float(dflt_x.revenue_FY2), "Their FY2 revenue",
                                                                    "at_risk_sensitivity.csv"),
            "high_value_oneoff_lapsed_customers": m(int(oneoff_lapsed.sum()), "Top-20% customers with one purchase "
                                                    "day and recency > 90 days (no usual gap; not in at-risk list)",
                                                    "customers_rfm.csv"),
            "high_value_oneoff_lapsed_monetary": m(float(c.loc[oneoff_lapsed, "monetary"].sum()), "Their monetary",
                                                   "customers_rfm.csv"),
            "at_risk_count_range": m(f"{int(sens.customers.min())}-{int(sens.customers.max())}",
                                     "Min-max at-risk count across the sensitivity grid", "at_risk_sensitivity.csv"),
            "at_risk_monetary_range": m(f"{sens.monetary.min():,.0f}-{sens.monetary.max():,.0f}",
                                        "Min-max at-risk monetary across the grid", "at_risk_sensitivity.csv"),
            "repeat_customer_rate": m(float(rep.mean()), "Customers buying on 2+ distinct days", "repeat_bands.csv"),
            "repeat_customer_revenue_share": m(float(c.monetary[rep].sum() / ident), "Identified revenue from "
                                               "repeat customers", "repeat_bands.csv"),
            "median_days_first_to_second": m(float(c.days_first_to_second.median()), "Median days from first to "
                                             "second purchase day (repeaters)", "repeat_first_to_second.csv"),
            "median_usual_gap_days": m(float(c.usual_gap_days.median()), "Median over repeaters of their median "
                                       "gap between consecutive purchase days", "customers_rfm.csv"),
            "median_mean_gap_days": m(mean_gap_median, "Median of (last-first)/(purchase days-1); matches "
                                      "median_days_between_purchases in outputs/analysis/metrics.json",
                                      "repeat_bands.csv"),
            "customers_single_order_dominated_top20": m(int((top & c.single_order_dominated).sum()),
                                                        "Top-20% customers whose largest purchase day is >=50% of "
                                                        "monetary and >=£5,000", "customers_rfm.csv"),
            "top20_share_starting_dec2009": m(float(c.loc[top, "starts_dec2009"].mean()), "Share of top-20% "
                                              "customers first seen in Dec 2009 (history left-censored)",
                                              "customers_rfm.csv"),
            "repeat_rate_new_2010_2011": m(float((c.loc[~c.starts_dec2009, "purchase_days"] >= 2).mean()),
                                           "Repeat rate excluding customers first seen in Dec 2009", "customers_rfm.csv"),
            "repeat_within_90d": m(float(curve.set_index("within_days").loc[90, "share_repeated"]),
                                   "Eligible new customers (first seen Jan 2010-Jun 2011) buying again within "
                                   "90 days", "repeat_curve.csv"),
            "repeat_within_180d": m(float(curve.set_index("within_days").loc[180, "share_repeated"]),
                                    "As above, within 180 days", "repeat_curve.csv"),
            "repeat_within_180d_FY1_new": m(float(by_fy.iloc[0]["repeat_in_window"]), "New customers first "
                                            "buying Jan-Jun 2010 who bought again within 180 days",
                                            "repeat_by_acquisition_fy.csv"),
            "repeat_within_180d_FY2_new": m(float(by_fy.iloc[1]["repeat_in_window"]), "New customers first "
                                            "buying Jan-Jun 2011 who bought again within 180 days",
                                            "repeat_by_acquisition_fy.csv"),
            "default_at_risk_row": m({k: (v.item() if hasattr(v, "item") else v) for k, v in dflt.items()},
                                     "Default row of the sensitivity grid", "at_risk_sensitivity.csv"),
        },
    }
    (out / "customer_metrics.json").write_text(json.dumps(metrics, indent=2, default=str))

    print(f"Identified revenue £{ident:,.0f} of £{total:,.0f} ({1 - ident / total:.1%} without Customer ID); "
          f"{len(c):,} customers; {len(rev_idx):,} reversed lines £{c.reversed_value.sum():,.0f}")
    for k, v in metrics["metrics"].items():
        print(f"  {k:<46} {v['value']}")
    print(f"\nwrote {len(tables)} tables and customer_metrics.json to {out}")


if __name__ == "__main__":
    main()
