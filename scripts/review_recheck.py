"""Independent recheck of headline numbers for the reviewer (outputs/review.md).

Deliberately does NOT import retail_common or any other project script, so a shared
bug cannot hide. Implements the CLAUDE.md approved revenue definition directly:

Assumptions (stated before calculating):
- Input: data/processed/online_retail_II.csv (read-only).
- Overlap: drop rows with source_sheet == 'Year 2010-2011' and InvoiceDate <= 2010-12-09 20:01.
- Revenue rows: Invoice not starting with 'C' or 'A'; Quantity > 0; Price > 0;
  StockCode not in the CLAUDE.md non-product list and not starting with 'gift_0001_'.
- Revenue = sum(Quantity * Price) over revenue rows.
- FY1 = 2009-12-01 <= date < 2010-12-01; FY2 = 2010-12-01 <= date < 2011-12-01.
  Dec 2011 (1-9 Dec) is partial and excluded from FY comparisons.
- Order = distinct revenue Invoice; AOV = revenue / orders.
- Cancellation value = -(Quantity * Price) on C-invoice rows, overlap removed, product codes only.
  Cancellation rate = cancel value / (revenue + cancel value) (the reports' stated basis).
- 24h reversals: the three sale lines named in the reports (581483, 541431, 556444),
  re-identified here from the data by invoice; their cancellations are found by
  same customer, cancelled within 24h, same StockCode and opposite quantity, or an 'M'
  line of equal value.
- Customers: revenue rows with a Customer ID only. Repeat = 2+ distinct purchase days.
- High-value at risk: top 20% by monetary (rank by M descending, top ceil/round?
  -> top int(0.2*n) customers), 2+ purchase days, recency (to 2011-12-10) > 2 x median
  gap between consecutive purchase days and > 90 days.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "processed" / "online_retail_II.csv"

NON_PRODUCT = {"POST", "DOT", "C2", "C3", "M", "m", "D", "S", "B", "BANK CHARGES",
               "AMAZONFEE", "CRUK", "ADJUST", "ADJUST2", "TEST001", "TEST002", "PADS", "GIFT"}

raw = pd.read_csv(CSV, dtype={"Invoice": str, "StockCode": str, "Customer ID": str},
                  parse_dates=["InvoiceDate"])
raw["val"] = raw.Quantity * raw.Price
overlap = (raw.source_sheet == "Year 2010-2011") & (raw.InvoiceDate <= pd.Timestamp("2010-12-09 20:01"))
d = raw[~overlap].copy()
nonprod = d.StockCode.isin(NON_PRODUCT) | d.StockCode.str.startswith("gift_0001_")
is_c = d.Invoice.str.startswith("C")
is_a = d.Invoice.str.startswith("A")
rev = d[~is_c & ~is_a & (d.Quantity > 0) & (d.Price > 0) & ~nonprod].copy()
canc = d[is_c & ~nonprod].copy()


def fy(s):
    return np.select([(s >= "2009-12-01") & (s < "2010-12-01"),
                      (s >= "2010-12-01") & (s < "2011-12-01")], ["FY1", "FY2"], "other")


rev["fy"] = fy(rev.InvoiceDate)
canc["fy"] = fy(canc.InvoiceDate)
out = {}


def show(k, v):
    out[k] = v
    if isinstance(v, float):
        print(f"{k:55s} {v:,.4f}")
    else:
        print(f"{k:55s} {v}")


print("== Row audit")
show("rows_total", len(raw))
show("rows_after_overlap", len(d))
show("revenue_rows", len(rev))
show("revenue_total", rev.val.sum())
R = rev.groupby("fy").val.sum()
show("revenue_FY1", R["FY1"]); show("revenue_FY2", R["FY2"]); show("revenue_Dec11", R["other"])
show("growth_FY2_vs_FY1", R["FY2"] / R["FY1"] - 1)

print("== 24h reversals")
rv_inv = ["581483", "541431", "556444"]
rv = rev[rev.Invoice.isin(rv_inv)]
print(rv[["Invoice", "StockCode", "Quantity", "Price", "val", "InvoiceDate", "Customer ID", "fy"]].to_string())
show("reversed_3_total", rv.val.sum())
# find each reversal's cancellation (any code, incl. M)
allc = d[is_c]
for _, r in rv.iterrows():
    c = allc[(allc["Customer ID"] == r["Customer ID"]) & (allc.InvoiceDate >= r.InvoiceDate)
             & (allc.InvoiceDate <= r.InvoiceDate + pd.Timedelta("24h"))
             & (((allc.StockCode == r.StockCode) & (allc.Quantity == -r.Quantity))
                | ((allc.StockCode == "M") & np.isclose(-allc.val, r.val)))]
    print("  sale", r.Invoice, "->", c[["Invoice", "StockCode", "Quantity", "Price", "val", "InvoiceDate"]].values.tolist())
rv_c_prod = canc[canc.Invoice.isin(["C581484", "C541433"])]  # product-code cancellations of the reversals
fy2_rv = rv[rv.fy == "FY2"].val.sum()
show("revenue_FY2_excl_reversed", R["FY2"] - fy2_rv)
show("growth_excl_reversed", (R["FY2"] - fy2_rv) / R["FY1"] - 1)
# wider (any-lag) rule used by the older executive summary
show("growth_excl_reversed_wide (530715 FY1, 540815 FY2 also)",
     (R["FY2"] - fy2_rv - 6539.4) / (R["FY1"] - 15818.4) - 1)

print("== Orders / AOV")
O = rev.groupby("fy").Invoice.nunique()
show("orders_FY1", int(O["FY1"])); show("orders_FY2", int(O["FY2"]))
show("orders_growth", O["FY2"] / O["FY1"] - 1)
show("aov_FY1", R["FY1"] / O["FY1"]); show("aov_FY2", R["FY2"] / O["FY2"])
show("aov_growth", (R["FY2"] / O["FY2"]) / (R["FY1"] / O["FY1"]) - 1)
# excl reversals: the reversed invoices stay as orders if they have other lines
o2x = rev[(rev.fy == "FY2") & ~rev.index.isin(rv.index)].Invoice.nunique()
show("orders_FY2_excl_reversed_lines", o2x)
show("aov_FY2_excl_reversed", (R["FY2"] - fy2_rv) / o2x)

print("== Cancellation rate")
C = -canc.groupby("fy").val.sum()
show("cancel_value_total", -canc.val.sum())
show("cancel_rate_total", -canc.val.sum() / (rev.val.sum() - canc.val.sum()))
show("cancel_value_pct_of_revenue", -canc.val.sum() / rev.val.sum())
for f in ["FY1", "FY2"]:
    show(f"cancel_rate_{f}", C[f] / (R[f] + C[f]))
c2x = C["FY2"] + rv_c_prod[rv_c_prod.fy == "FY2"].val.sum()
show("cancel_rate_FY2_excl_reversed", c2x / (R["FY2"] - fy2_rv + c2x))

print("== Identified vs unidentified")
rev["has_id"] = rev["Customer ID"].notna()
I = rev.groupby(["fy", "has_id"]).val.sum()
show("identified_FY1", I["FY1", True]); show("identified_FY2", I["FY2", True])
show("identified_growth", I["FY2", True] / I["FY1", True] - 1)
show("unidentified_FY1", I["FY1", False]); show("unidentified_FY2", I["FY2", False])
show("unidentified_growth", I["FY2", False] / I["FY1", False] - 1)
show("identified_growth_excl_reversed", (I["FY2", True] - fy2_rv) / I["FY1", True] - 1)
show("delta_total_FY2_minus_FY1", R["FY2"] - R["FY1"])
show("delta_unidentified", I["FY2", False] - I["FY1", False])
show("delta_identified", I["FY2", True] - I["FY1", True])
# where does the unidentified growth sit?
u = rev[~rev.has_id & rev.fy.isin(["FY1", "FY2"])]
u_uk = u.assign(uk=u.Country == "United Kingdom").groupby(["fy", "uk"]).val.sum().unstack()
print("  unidentified revenue by FY x UK:\n", u_uk.round(0).to_string())
print("  unidentified share of revenue by month:")
m = rev.assign(mo=rev.InvoiceDate.dt.to_period("M")).groupby(["mo", "has_id"]).val.sum().unstack()
print((m[False] / m.sum(axis=1)).round(3).to_string())
ui = u.groupby("fy").Invoice.nunique()
show("unidentified_invoices_FY1", int(ui["FY1"])); show("unidentified_invoices_FY2", int(ui["FY2"]))

print("== Countries")
uk = rev.Country == "United Kingdom"
show("uk_share_total", rev[uk].val.sum() / rev.val.sum())
cf = rev.assign(uk=uk).groupby(["fy", "uk"]).val.sum()
show("uk_growth", cf["FY2", True] / cf["FY1", True] - 1)
rv_uk_fy2 = rv[(rv.fy == "FY2") & (rv.Country == "United Kingdom")].val.sum()
show("uk_growth_excl_reversed", (cf["FY2", True] - rv_uk_fy2) / cf["FY1", True] - 1)
show("intl_growth", cf["FY2", False] / cf["FY1", False] - 1)
show("uk_share_FY1", cf["FY1", True] / R["FY1"]); show("uk_share_FY2", cf["FY2", True] / R["FY2"])
top = rev.groupby("Country").val.sum().sort_values(ascending=False)
show("top_country", f"{top.index[0]} {top.iloc[0]:,.0f}")
# multi-country customers
mc_rev = rev.dropna(subset=["Customer ID"]).groupby("Customer ID").Country.nunique()
show("multi_country_customers_revenue_rows", int((mc_rev > 1).sum()))
mc_all = d.dropna(subset=["Customer ID"]).groupby("Customer ID").Country.nunique()
show("multi_country_customers_all_rows", int((mc_all > 1).sum()))

print("== Customers")
cr = rev[rev.has_id].copy()
cr["day"] = cr.InvoiceDate.dt.normalize()
M = cr.groupby("Customer ID").val.sum().sort_values(ascending=False)
n = len(M)
show("customers", n)
show("identified_revenue", M.sum()); show("identified_share", M.sum() / rev.val.sum())
for p in [0.01, 0.10, 0.20]:
    k = int(round(n * p))
    show(f"top_{int(p*100)}pct_n", k); show(f"top_{int(p*100)}pct_share", M.iloc[:k].sum() / M.sum())
days = cr.groupby("Customer ID").day.nunique()
show("repeat_rate", (days >= 2).mean())
show("repeat_revenue_share", M[days[days >= 2].index].sum() / M.sum())
show("rev_16446", M.get("16446")); show("rev_12346", M.get("12346")); show("rev_15098", M.get("15098"))
print("  15098 lines:\n", cr[cr["Customer ID"] == "15098"][["Invoice", "StockCode", "Quantity", "Price", "val", "InvoiceDate"]].to_string())
print("  15098 cancellations:\n", d[is_c & (d["Customer ID"] == "15098")][["Invoice", "StockCode", "Quantity", "Price", "val", "InvoiceDate"]].to_string())

print("== High-value at risk (independent implementation)")
snap = pd.Timestamp("2011-12-10")
ud = cr.groupby("Customer ID").day.apply(lambda s: np.sort(s.unique()))
gap = ud.apply(lambda a: np.median(np.diff(a).astype("timedelta64[D]").astype(float)) if len(a) > 1 else np.nan)
last = ud.apply(lambda a: a[-1])
rec = (snap - pd.to_datetime(last)).dt.days
k20 = int(round(n * 0.2))
top20 = M.iloc[:k20].index
show("top20_n", k20); show("top20_min_M", float(M.iloc[k20 - 1]))
ar = [c for c in top20 if days[c] >= 2 and rec[c] > 2 * gap[c] and rec[c] > 90]
show("at_risk_n", len(ar))
show("at_risk_lifetime", M[ar].sum())
fy2c = cr[cr.fy == "FY2"].groupby("Customer ID").val.sum()
show("at_risk_FY2", fy2c.reindex(ar).fillna(0).sum())
show("at_risk_FY2_from_12346", fy2c.get("12346", 0.0) if "12346" in ar else 0.0)
show("at_risk_still_bought_FY2", int((fy2c.reindex(ar).fillna(0) > 0).sum()))
last12 = cr[cr.InvoiceDate >= "2010-12-10"].groupby("Customer ID").val.sum()
show("at_risk_last_365d", last12.reindex(ar).fillna(0).sum())

print("== Acquisition cohorts, 180-day repeat")
first = ud.apply(lambda a: pd.Timestamp(a[0]))
second = ud.apply(lambda a: pd.Timestamp(a[1]) if len(a) > 1 else pd.NaT)
rep180 = (second - first).dt.days <= 180
elig = first <= snap - pd.Timedelta(days=180)
for lab, a, b in [("H1_2010", "2010-01-01", "2010-07-01"), ("H1_2011", "2011-01-01", "2011-07-01")]:
    sel = (first >= a) & (first < b) & elig
    show(f"cohort_{lab}_n", int(sel.sum())); show(f"cohort_{lab}_repeat180", float(rep180[sel].mean()))
    show(f"cohort_{lab}_latest_first_date", str(first[sel].max().date()))
# like-for-like: 2011 cohort with the same 1-month look-back that 2010 has
# (i.e. only data from 2010-12-01 onward is visible, as only data from 2009-12-01 is visible for 2010)
cr11 = cr[cr.InvoiceDate >= "2010-12-01"]
ud11 = cr11.groupby("Customer ID").day.apply(lambda s: np.sort(s.unique()))
f11 = ud11.apply(lambda a: pd.Timestamp(a[0]))
s11 = ud11.apply(lambda a: pd.Timestamp(a[1]) if len(a) > 1 else pd.NaT)
sel = (f11 >= "2011-01-01") & (f11 < "2011-07-01") & (f11 <= snap - pd.Timedelta(days=180))
show("cohort_H1_2011_1mo_lookback_n", int(sel.sum()))
show("cohort_H1_2011_1mo_lookback_repeat180", float(((s11 - f11).dt.days <= 180)[sel].mean()))
seen_before = sel & sel.index.isin(cr[cr.InvoiceDate < "2010-12-01"]["Customer ID"].unique())
show("  of which bought in FY1 (i.e. not truly new)", int(seen_before.sum()))

print("== New customers per month: full look-back vs 1-month look-back (Jan-Nov 2011)")
nm_full = first[(first >= "2011-01-01") & (first < "2011-12-01")].dt.to_period("M").value_counts().sort_index()
nm_1mo = f11[(f11 >= "2011-01-01") & (f11 < "2011-12-01")].dt.to_period("M").value_counts().sort_index()
nm_2010 = first[(first >= "2010-01-01") & (first < "2010-12-01")].dt.to_period("M").value_counts().sort_index()
print(pd.DataFrame({"2010 (1mo lookback)": nm_2010.values, "2011 full lookback": nm_full.values,
                    "2011 1mo lookback": nm_1mo.values}, index=[p.strftime("%b") for p in nm_full.index]).to_string())
