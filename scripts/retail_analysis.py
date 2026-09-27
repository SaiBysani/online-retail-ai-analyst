"""Business analysis tables for the retail-analysis skill.

Computes revenue, monthly trends, products, customers, countries, cancellations,
repeat purchases and anomalies using the approved revenue definition (CLAUDE.md,
via retail_common.py), and writes:

- outputs/analysis/metrics.json   headline numbers, each with a short definition
- outputs/analysis/*.csv          one evidence table per topic (listed in metrics.json)

Assumptions (ASSUMPTIONS below; also written to metrics.json):
- Revenue = approved definition. Exact duplicate lines are kept, as the definition does.
- Periods: FY1 = Dec 2009-Nov 2010, FY2 = Dec 2010-Nov 2011. Dec 2011 (1-9 Dec) is
  partial and excluded from year-on-year comparisons.
- Customer metrics use revenue rows with a Customer ID only.
- Order = one revenue invoice. AOV = revenue / revenue invoices.
- Repeat customer = bought on 2 or more distinct days (same-day split invoices count once).
- Cancellation value = C-invoice lines on product codes (non-product codes excluded, to
  match revenue); cancellation rate = cancellation value / (revenue + cancellation value).

Usage (from the repo root):
    python scripts/retail_analysis.py [--out-dir outputs/analysis]
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from retail_common import OUT, cancellation_rows, load, revenue_rows

FULL_YEARS = ["FY1", "FY2"]
ASSUMPTIONS = [
    "Revenue = approved CLAUDE.md definition; exact duplicate lines are kept, as the definition does.",
    "FY1 = Dec 2009-Nov 2010, FY2 = Dec 2010-Nov 2011; Dec 2011 (1-9 Dec) is partial and excluded "
    "from year-on-year comparisons.",
    "Customer metrics use revenue rows with a Customer ID only.",
    "Order = one revenue invoice; AOV = revenue / revenue invoices.",
    "Repeat customer = bought on 2 or more distinct days (same-day split invoices count once).",
    "Cancellation value = C-invoice lines on product codes (non-product codes excluded, to match revenue); "
    "cancellation rate = cancellation value / (revenue + cancellation value).",
]


def change(a, b):
    return None if not a else float(b / a - 1)


def by_fy(frame, value="line_value"):
    return frame[frame.fy.isin(FULL_YEARS)].groupby("fy")[value].sum().reindex(FULL_YEARS, fill_value=0)


def monthly_table(rev, canc):
    m = rev.groupby("month").agg(revenue=("line_value", "sum"), orders=("Invoice", "nunique"),
                                 customers=("Customer ID", "nunique"))
    first = rev.dropna(subset=["Customer ID"]).groupby("Customer ID").month.min()
    m["new_customers"] = first.value_counts().reindex(m.index, fill_value=0)
    m["aov"] = m.revenue / m.orders
    m["cancel_value"] = -canc.groupby("month").line_value.sum().reindex(m.index, fill_value=0)
    m["cancel_rate"] = m.cancel_value / (m.revenue + m.cancel_value)
    m["revenue_yoy"] = m.revenue / m.revenue.shift(12) - 1
    m["trading_days"] = rev.groupby("month").InvoiceDate.apply(lambda s: s.dt.date.nunique())
    m.index = m.index.astype(str)
    return m


def product_tables(rev, canc):
    p = rev.groupby("StockCode").agg(description=("Description", lambda s: s.dropna().str.strip().mode().iat[0]
                                                  if s.notna().any() else ""),
                                     revenue=("line_value", "sum"), units=("Quantity", "sum"),
                                     orders=("Invoice", "nunique"), customers=("Customer ID", "nunique"))
    fy = rev[rev.fy.isin(FULL_YEARS)].pivot_table(index="StockCode", columns="fy", values="line_value",
                                                  aggfunc="sum", fill_value=0)
    p = p.join(fy.reindex(columns=FULL_YEARS, fill_value=0))
    p["cancel_value"] = -canc.groupby("StockCode").line_value.sum().reindex(p.index, fill_value=0)
    p["cancel_rate"] = p.cancel_value / (p.revenue + p.cancel_value)
    p = p.sort_values("revenue", ascending=False)
    p["share"] = p.revenue / p.revenue.sum()
    p["cum_share"] = p.share.cumsum()
    p["abc"] = np.select([p.cum_share <= .8, p.cum_share <= .95], ["A", "B"], "C")
    movers = p[(p.FY1 >= 5000) | (p.FY2 >= 5000)].assign(fy_change=lambda x: x.FY2 - x.FY1)
    movers = pd.concat([movers.nlargest(15, "fy_change"), movers.nsmallest(15, "fy_change")])
    high_cancel = p[p.revenue >= 5000].nlargest(20, "cancel_rate")
    return p, movers, high_cancel


def customer_tables(rev):
    rc = rev.dropna(subset=["Customer ID"])
    c = rc.groupby("Customer ID").agg(revenue=("line_value", "sum"), orders=("Invoice", "nunique"),
                                      purchase_days=("InvoiceDate", lambda s: s.dt.normalize().nunique()),
                                      first=("InvoiceDate", "min"), last=("InvoiceDate", "max"),
                                      country=("Country", lambda s: s.mode().iat[0]))
    c = c.sort_values("revenue", ascending=False)
    c["cum_share"] = c.revenue.cumsum() / c.revenue.sum()
    n = len(c)
    conc = pd.DataFrame({"top_share_of_customers": [.01, .05, .10, .20, .50]})
    conc["customers"] = (conc.top_share_of_customers * n).round().astype(int)
    conc["share_of_identified_revenue"] = [c.revenue.iloc[:k].sum() / c.revenue.sum() for k in conc.customers]

    fy_sets = {fy: set(rc[rc.fy == fy]["Customer ID"]) for fy in FULL_YEARS}
    retained = fy_sets["FY1"] & fy_sets["FY2"]
    fy_rev = rc[rc.fy.isin(FULL_YEARS)].groupby(["fy", "Customer ID"]).line_value.sum()
    lifecycle = pd.DataFrame({
        "customers": [len(fy_sets["FY1"]), len(fy_sets["FY2"])],
        "new": [len(fy_sets["FY1"]), len(fy_sets["FY2"] - fy_sets["FY1"])],
        "retained_from_prior_year": [np.nan, len(retained)],
        "lost_from_prior_year": [np.nan, len(fy_sets["FY1"] - fy_sets["FY2"])],
        "revenue": [fy_rev["FY1"].sum(), fy_rev["FY2"].sum()],
    }, index=pd.Index(FULL_YEARS, name="fy"))
    lifecycle["revenue_per_customer"] = lifecycle.revenue / lifecycle.customers
    lifecycle["retention_rate"] = lifecycle.retained_from_prior_year / lifecycle.customers.shift(1)
    lifecycle.loc["FY2", "revenue_from_retained"] = fy_rev["FY2"][list(retained)].sum()
    lifecycle.loc["FY2", "revenue_from_new"] = fy_rev["FY2"].sum() - fy_rev["FY2"][list(retained)].sum()
    lost_rev = fy_rev["FY1"][list(fy_sets["FY1"] - fy_sets["FY2"])].sum()
    lifecycle.loc["FY2", "fy1_revenue_of_lost_customers"] = lost_rev

    # Monthly acquisition cohorts: share of each cohort buying again N months later.
    rc_m = rc.assign(cohort=rc.groupby("Customer ID").month.transform("min"))
    rc_m["age"] = (rc_m.month - rc_m.cohort).apply(lambda x: x.n)
    size = rc_m.groupby("cohort")["Customer ID"].nunique()
    active = rc_m.groupby(["cohort", "age"])["Customer ID"].nunique().unstack(fill_value=0)
    cohorts = active[[a for a in (1, 3, 6, 12) if a in active]].div(size, axis=0)
    cohorts.columns = [f"m{a}" for a in cohorts.columns]
    cohorts.insert(0, "size", size)
    cohorts.index = cohorts.index.astype(str)
    return c, conc, lifecycle, cohorts


def repeat_tables(c):
    bands = pd.cut(c.purchase_days, [0, 1, 2, 5, 10, 25, np.inf],
                   labels=["1 day", "2 days", "3-5", "6-10", "11-25", "26+"])
    t = c.groupby(bands, observed=False).agg(customers=("revenue", "size"), revenue=("revenue", "sum"))
    t["share_customers"] = t.customers / t.customers.sum()
    t["share_revenue"] = t.revenue / t.revenue.sum()
    t.index.name = "purchase_days"
    rep = c[c.purchase_days > 1]
    gap_days = ((rep["last"] - rep["first"]).dt.days / (rep.purchase_days - 1))
    return t, float(gap_days.median())


def country_table(rev, canc):
    t = rev.groupby("Country").agg(revenue=("line_value", "sum"), orders=("Invoice", "nunique"),
                                   customers=("Customer ID", "nunique"))
    t = t.join(by_fy_pivot(rev, "Country"))
    t["share"] = t.revenue / t.revenue.sum()
    t["aov"] = t.revenue / t.orders
    t["fy_change"] = t.FY2 / t.FY1.replace(0, np.nan) - 1
    t["cancel_value"] = -canc.groupby("Country").line_value.sum().reindex(t.index, fill_value=0)
    t["cancel_rate"] = t.cancel_value / (t.revenue + t.cancel_value)
    return t.sort_values("revenue", ascending=False)


def by_fy_pivot(frame, key):
    return (frame[frame.fy.isin(FULL_YEARS)].pivot_table(index=key, columns="fy", values="line_value",
                                                         aggfunc="sum", fill_value=0)
            .reindex(columns=FULL_YEARS, fill_value=0))


def anomaly_tables(rev, canc, all_rows):
    daily = rev.groupby(rev.InvoiceDate.dt.date).agg(revenue=("line_value", "sum"), orders=("Invoice", "nunique"))
    med = daily.revenue.median()
    mad = (daily.revenue - med).abs().median() * 1.4826
    daily["robust_z"] = (daily.revenue - med) / mad
    top_line = rev.groupby(rev.InvoiceDate.dt.date).line_value.max()
    daily["largest_line_share"] = top_line / daily.revenue
    days = daily[daily.robust_z.abs() >= 4].sort_values("robust_z", ascending=False)

    # Big orders followed by a cancellation of the same product and quantity.
    big = rev[rev.line_value >= 5000]
    c = canc.assign(q=-canc.Quantity)
    reversed_ = big.merge(c[["StockCode", "q", "Invoice", "InvoiceDate", "Customer ID"]],
                          left_on=["StockCode", "Quantity", "Customer ID"],
                          right_on=["StockCode", "q", "Customer ID"], suffixes=("", "_cancel"))
    reversed_ = reversed_[reversed_.InvoiceDate_cancel >= reversed_.InvoiceDate]
    reversed_ = reversed_[["Invoice", "InvoiceDate", "StockCode", "Description", "Quantity", "line_value",
                           "Customer ID", "Invoice_cancel", "InvoiceDate_cancel"]]

    lines = rev.nlargest(20, "line_value")[["Invoice", "InvoiceDate", "StockCode", "Description", "Quantity",
                                            "Price", "line_value", "Customer ID", "Country"]]
    lines["reversed_by_cancellation"] = lines.Invoice.isin(reversed_.Invoice)
    # Price jumps: product lines charged at over 3x that product's median price.
    med_price = rev.groupby("StockCode").Price.transform("median")
    price_out = rev[(rev.Price > 3 * med_price) & (rev.line_value >= 200)]
    price_out = (price_out.assign(median_price=med_price[price_out.index])
                 .nlargest(20, "line_value")[["Invoice", "StockCode", "Description", "Quantity", "Price",
                                              "median_price", "line_value"]])
    return days, lines, reversed_, price_out, float(med), float(mad)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", type=Path, default=OUT / "analysis")
    out = ap.parse_args().out_dir
    out.mkdir(parents=True, exist_ok=True)

    df = load()
    rev, audit = revenue_rows(df)
    canc = cancellation_rows(df, products_only=True)

    monthly = monthly_table(rev, canc)
    products, movers, high_cancel = product_tables(rev, canc)
    customers, conc, lifecycle, cohorts = customer_tables(rev)
    repeat, median_gap = repeat_tables(customers)
    countries = country_table(rev, canc)
    days, top_lines, reversed_, price_out, day_med, day_mad = anomaly_tables(rev, canc, df)

    tables = {
        "monthly.csv": monthly, "products.csv": products, "product_movers.csv": movers,
        "products_high_cancel.csv": high_cancel, "customer_concentration.csv": conc,
        "customer_lifecycle.csv": lifecycle, "cohort_retention.csv": cohorts,
        "repeat_purchases.csv": repeat, "countries.csv": countries, "anomaly_days.csv": days,
        "anomaly_top_lines.csv": top_lines, "anomaly_reversed_orders.csv": reversed_,
        "anomaly_price_outliers.csv": price_out,
    }
    for name, t in tables.items():
        t.to_csv(out / name, float_format="%.4f")

    fy_rev, fy_canc = by_fy(rev), -by_fy(canc)
    fy_orders = rev[rev.fy.isin(FULL_YEARS)].groupby("fy").Invoice.nunique().reindex(FULL_YEARS)
    rc = rev.dropna(subset=["Customer ID"])
    fy_cust = rc[rc.fy.isin(FULL_YEARS)].groupby("fy")["Customer ID"].nunique().reindex(FULL_YEARS)
    fy_aov = fy_rev / fy_orders
    peak = monthly.loc[[m for m in monthly.index if m[-2:] in ("09", "10", "11")]]
    uk = countries.loc["United Kingdom"]
    total = rev.line_value.sum()
    canc_total = -canc.line_value.sum()
    repeaters = customers.purchase_days > 1

    def m(value, definition, source):
        return {"value": value, "definition": definition, "source": source}

    metrics = {
        "assumptions": ASSUMPTIONS,
        "revenue_filter_audit": [{"step": s, "rows": r, "value": round(v, 2)} for s, r, v in audit],
        "tables": sorted(tables),
        "metrics": {
            "revenue_total": m(round(total, 2), "Approved revenue, 2009-12-01 to 2011-12-09", "revenue_filter_audit"),
            "revenue_FY1": m(round(fy_rev.FY1, 2), "Revenue Dec 2009-Nov 2010", "monthly.csv"),
            "revenue_FY2": m(round(fy_rev.FY2, 2), "Revenue Dec 2010-Nov 2011", "monthly.csv"),
            "revenue_growth_FY2_vs_FY1": m(change(fy_rev.FY1, fy_rev.FY2), "FY2 / FY1 - 1", "monthly.csv"),
            "orders_FY1": m(int(fy_orders.FY1), "Distinct revenue invoices", "monthly.csv"),
            "orders_FY2": m(int(fy_orders.FY2), "Distinct revenue invoices", "monthly.csv"),
            "aov_FY1": m(round(fy_aov.FY1, 2), "Revenue / orders", "monthly.csv"),
            "aov_FY2": m(round(fy_aov.FY2, 2), "Revenue / orders", "monthly.csv"),
            "customers_FY1": m(int(fy_cust.FY1), "Distinct Customer IDs with revenue", "customer_lifecycle.csv"),
            "customers_FY2": m(int(fy_cust.FY2), "Distinct Customer IDs with revenue", "customer_lifecycle.csv"),
            "customer_retention_FY1_to_FY2": m(float(lifecycle.loc["FY2", "retention_rate"]),
                                               "FY1 customers who also bought in FY2", "customer_lifecycle.csv"),
            "new_customers_FY2": m(int(lifecycle.loc["FY2", "new"]), "FY2 customers not seen in FY1",
                                   "customer_lifecycle.csv"),
            "revenue_share_without_customer_id": m(float(rev.line_value[rev["Customer ID"].isna()].sum() / total),
                                                   "Revenue on rows with no Customer ID", "data_quality_checks.json"),
            "top_10pct_customer_share": m(float(conc.set_index("top_share_of_customers")
                                                .loc[.10, "share_of_identified_revenue"]),
                                          "Share of identified revenue from the top 10% of customers",
                                          "customer_concentration.csv"),
            "repeat_customer_rate": m(float(repeaters.mean()), "Customers buying on 2+ distinct days",
                                      "repeat_purchases.csv"),
            "repeat_customer_revenue_share": m(float(customers.revenue[repeaters].sum() / customers.revenue.sum()),
                                               "Share of identified revenue from repeat customers",
                                               "repeat_purchases.csv"),
            "median_days_between_purchases": m(median_gap, "Median over repeat customers of "
                                               "(last - first purchase) / (purchase days - 1)", "repeat_purchases.csv"),
            "peak_season_share_FY2": m(float(peak.loc[peak.index >= "2011-09", "revenue"].sum() / fy_rev.FY2),
                                       "Sep-Nov 2011 revenue / FY2 revenue", "monthly.csv"),
            "uk_revenue_share": m(float(uk.share), "UK share of total revenue", "countries.csv"),
            "non_uk_growth_FY2_vs_FY1": m(change(countries.drop("United Kingdom").FY1.sum(),
                                                 countries.drop("United Kingdom").FY2.sum()),
                                          "Non-UK FY2 / FY1 - 1", "countries.csv"),
            "uk_growth_FY2_vs_FY1": m(change(uk.FY1, uk.FY2), "UK FY2 / FY1 - 1", "countries.csv"),
            "countries": m(int(len(countries)), "Country values with revenue", "countries.csv"),
            "cancel_value_total": m(round(canc_total, 2), "Cancelled product value (C invoices, product codes)",
                                    "monthly.csv"),
            "cancel_rate_total": m(float(canc_total / (total + canc_total)),
                                   "Cancelled value / (revenue + cancelled value)", "monthly.csv"),
            "cancel_rate_FY1": m(float(fy_canc.FY1 / (fy_rev.FY1 + fy_canc.FY1)), "As above, FY1", "monthly.csv"),
            "cancel_rate_FY2": m(float(fy_canc.FY2 / (fy_rev.FY2 + fy_canc.FY2)), "As above, FY2", "monthly.csv"),
            "products_sold": m(int(len(products)), "Stock codes with revenue", "products.csv"),
            "a_class_products": m(int((products.abc == "A").sum()), "Codes making up the first 80% of revenue",
                                  "products.csv"),
            "top_product": m(f"{products.index[0]} {products.description.iloc[0]}", "Highest-revenue stock code",
                             "products.csv"),
            "top_product_revenue": m(round(float(products.revenue.iloc[0]), 2), "", "products.csv"),
            "anomaly_days": m(int(len(days)), f"Days with |robust z| >= 4 (median £{day_med:,.0f}, "
                              f"scaled MAD £{day_mad:,.0f})", "anomaly_days.csv"),
            "reversed_big_orders_value": m(round(float(reversed_.drop_duplicates("Invoice").line_value.sum()), 2)
                                           if len(reversed_) else 0.0,
                                           "Value of >=£5K lines later cancelled with the same code, quantity "
                                           "and customer (still counted in revenue)", "anomaly_reversed_orders.csv"),
        },
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str))

    print(f"Revenue £{total:,.0f} | FY1 £{fy_rev.FY1:,.0f} | FY2 £{fy_rev.FY2:,.0f} "
          f"({change(fy_rev.FY1, fy_rev.FY2):+.1%})")
    for k, v in metrics["metrics"].items():
        val = v["value"]
        print(f"  {k:<36} {val:,.4f}" if isinstance(val, float) else f"  {k:<36} {val}")
    print(f"\nwrote {len(tables)} tables and metrics.json to {out}")


if __name__ == "__main__":
    main()
