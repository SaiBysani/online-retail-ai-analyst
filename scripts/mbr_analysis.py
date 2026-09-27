"""Monthly business review (month-to-date) tables, metrics and charts.

Compares a partial current month with the same window last year and the same window in
the previous month, using the approved revenue definition (CLAUDE.md, via retail_common.py).
Default: Dec 2011 month-to-date, i.e. 2011-12-01 00:00 to 2011-12-09 12:50 (the last
timestamp in the data), against 2010-12-01 .. 2010-12-09 12:50 and 2011-11-01 .. 2011-11-09 12:50.

Writes to outputs/mbr_<YYYY_MM>/:
- metrics.json      headline numbers for each window, each with a definition and source table
- *.csv             evidence tables (daily, products, countries, customers, reversals, mtd_trend)
- charts/*.png      four charts for the report

Assumptions (ASSUMPTIONS below; also written to metrics.json):
- Revenue = approved CLAUDE.md definition (sheet overlap counted once; C, A, Quantity <= 0,
  Price <= 0 and non-product codes excluded). Exact duplicate lines are kept.
- Like-for-like windows end at the same day and clock time as the last timestamp in the data.
- Order = one revenue invoice; AOV = revenue / orders.
- Customer metrics use revenue rows with a Customer ID only. A "new" customer has no revenue
  row before the window (the data starts 2009-12-01, so Dec 2010 "new" means no purchase in the
  previous 12 months, while Dec 2011 has 24 months of history).
- Cancellation value = C-invoice lines on product codes; rate = value / (revenue + value).
- Reversed orders = sales lines >= £5K matched to a later cancellation (retail_analysis.py matcher, any lag);
  "excl. reversed" figures are a sensitivity only, never the headline.

Usage (from the repo root):
    python scripts/mbr_analysis.py [--month 2011-12]
"""
import argparse
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from retail_analysis import anomaly_tables  # noqa: E402
from retail_common import OUT, cancellation_rows, load, revenue_rows  # noqa: E402

ASSUMPTIONS = [
    "Revenue = approved CLAUDE.md definition (sheet overlap counted once; C, A, Quantity <= 0, Price <= 0 "
    "and non-product codes excluded); exact duplicate lines are kept.",
    "Like-for-like windows: each window runs from the 1st of its month to the same day and clock time as the "
    "last timestamp in the data.",
    "Order = one revenue invoice; AOV = revenue / orders.",
    "Customer metrics use revenue rows with a Customer ID only. New customer = no revenue row before the window "
    "(data starts 2009-12-01, so the prior-year window has 12 months of look-back, the current window 24).",
    "Cancellation value = C-invoice lines on product codes; cancellation rate = value / (revenue + value).",
    "Reversed orders = revenue lines >= £5K matched to a later cancellation of the same product, quantity, price "
    "and customer (or a manual M line of equal value), using the retail_analysis.py matcher with no 24h filter. Figures 'excl. reversed' are a "
    "sensitivity; headline revenue keeps the approved definition.",
]

# Chart tokens: same system as scripts/analyze_business.py (slots validated with the dataviz validator).
SURFACE, INK, INK_2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
CURRENT, PRIOR, GRAY = "#2a78d6", "#eb6834", "#c3c2b7"
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial"], "font.size": 10,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "axes.edgecolor": AXIS,
    "axes.labelcolor": INK_2, "axes.titlecolor": INK, "axes.titlesize": 13, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "axes.titlepad": 24, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelcolor": INK_2, "ytick.labelcolor": INK_2, "legend.frameon": False, "legend.labelcolor": INK_2,
    "savefig.dpi": 150, "savefig.bbox": "tight", "savefig.facecolor": SURFACE,
})
GBP_K = FuncFormatter(lambda v, _: f"£{v / 1e3:,.0f}K")


def windows(month, last_ts):
    """Current month-to-date, same window last year, same window previous month."""
    start = month.to_timestamp()
    offset = last_ts - start
    out = {}
    for key, m in [("current", month), ("prior_year", month - 12), ("prior_month", month - 1)]:
        s = m.to_timestamp()
        out[key] = (s, s + offset)
    return out


def in_window(frame, w):
    return frame[(frame.InvoiceDate >= w[0]) & (frame.InvoiceDate <= w[1])]


def change(a, b):
    return None if not a else float(b / a - 1)


def window_metrics(rev, canc, rev_x, canc_x, w, first_purchase):
    r, c, rx, cx = in_window(rev, w), in_window(canc, w), in_window(rev_x, w), in_window(canc_x, w)
    revenue = float(r.line_value.sum())
    cancel = float(-c.line_value.sum())
    ident = r.dropna(subset=["Customer ID"])
    custs = ident["Customer ID"].unique()
    new = [cid for cid in custs if first_purchase[cid] >= w[0]]
    # Same 12-month look-back in every window, so years with more history are comparable.
    lookback = rev[(rev.InvoiceDate >= w[0] - pd.DateOffset(months=12)) & (rev.InvoiceDate < w[0])]
    new12 = set(custs) - set(lookback["Customer ID"].dropna())
    ident_x = rx.dropna(subset=["Customer ID"])
    new12_rev_x = float(ident_x[ident_x["Customer ID"].isin(new12)].line_value.sum())
    unident_x = float(rx[rx["Customer ID"].isna()].line_value.sum())
    cust_rev_x = rx.dropna(subset=["Customer ID"]).groupby("Customer ID").line_value.sum() \
        .sort_values(ascending=False)
    cancel_x = float(-cx.line_value.sum())
    new_rev = float(ident[ident["Customer ID"].isin(new)].line_value.sum())
    cust_rev = ident.groupby("Customer ID").line_value.sum().sort_values(ascending=False)
    uk = float(r[r.Country == "United Kingdom"].line_value.sum())
    orders = r.Invoice.nunique()
    return {
        "revenue": revenue,
        "orders": int(orders),
        "aov": revenue / orders if orders else None,
        "units": int(r.Quantity.sum()),
        "trading_days": int(r.InvoiceDate.dt.date.nunique()),
        "revenue_per_trading_day": revenue / max(r.InvoiceDate.dt.date.nunique(), 1),
        "customers": int(len(custs)),
        "new_customers": int(len(new)),
        "new_customers_12m_lookback": int(len(new12)),
        "returning_customers_12m_lookback": int(len(custs) - len(new12)),
        "new_12m_revenue_excl_reversed": new12_rev_x,
        "returning_12m_revenue_excl_reversed": float(ident_x.line_value.sum()) - new12_rev_x,
        "unidentified_revenue_excl_reversed": unident_x,
        "unidentified_share_excl_reversed": unident_x / float(rx.line_value.sum()),
        "new_customer_revenue_share_of_identified": new_rev / float(ident.line_value.sum()) if len(ident) else None,
        "revenue_per_customer": float(ident.line_value.sum()) / len(custs) if len(custs) else None,
        "unidentified_revenue_share": float(r[r["Customer ID"].isna()].line_value.sum()) / revenue,
        "top10_customer_share_of_identified": float(cust_rev.head(10).sum() / cust_rev.sum()),
        "uk_share": uk / revenue,
        "uk_revenue": uk,
        "international_revenue": revenue - uk,
        "uk_revenue_excl_reversed": float(rx[rx.Country == "United Kingdom"].line_value.sum()),
        "countries": int(r.Country.nunique()),
        "products_sold": int(r.StockCode.nunique()),
        "cancel_value": cancel,
        "cancel_rate": cancel / (revenue + cancel) if revenue + cancel else None,
        "revenue_excl_reversed": float(rx.line_value.sum()),
        "orders_excl_reversed": int(rx.Invoice.nunique()),
        "aov_excl_reversed": float(rx.line_value.sum()) / rx.Invoice.nunique() if len(rx) else None,
        "cancel_value_excl_reversed": cancel_x,
        "cancel_rate_excl_reversed": cancel_x / (float(rx.line_value.sum()) + cancel_x),
        "top10_customer_share_excl_reversed": float(cust_rev_x.head(10).sum() / cust_rev_x.sum()),
    }


DEFINITIONS = {
    "revenue": ("Approved revenue in the window", "daily.csv"),
    "orders": ("Distinct revenue invoices", "daily.csv"),
    "aov": ("Revenue / orders", "daily.csv"),
    "units": ("Sum of Quantity on revenue rows", "daily.csv"),
    "trading_days": ("Days with at least one revenue row", "daily.csv"),
    "revenue_per_trading_day": ("Revenue / trading days", "daily.csv"),
    "customers": ("Distinct Customer IDs with revenue", "customers.csv"),
    "new_customers": ("Customers whose first revenue row in the whole data falls in the window "
                      "(look-back differs by year; use new_customers_12m_lookback to compare)", "customers.csv"),
    "new_customers_12m_lookback": ("Customers with no revenue row in the 12 months before the window "
                                   "(like-for-like 'new')", "customers.csv"),
    "returning_customers_12m_lookback": ("Customers with a revenue row in the 12 months before the window; "
                                         "customers = new + returning on this basis", "customers.csv"),
    "new_12m_revenue_excl_reversed": ("Revenue excl. reversed lines from new (12-month look-back) customers",
                                      "customers.csv"),
    "returning_12m_revenue_excl_reversed": ("Revenue excl. reversed lines from returning (12-month look-back) "
                                            "customers", "customers.csv"),
    "unidentified_revenue_excl_reversed": ("Revenue excl. reversed lines with no Customer ID", "daily.csv"),
    "unidentified_share_excl_reversed": ("Sensitivity: no-Customer-ID revenue / revenue, reversed lines removed",
                                         "daily.csv"),
    "new_customer_revenue_share_of_identified": ("New-customer revenue / identified revenue", "customers.csv"),
    "revenue_per_customer": ("Identified revenue / customers", "customers.csv"),
    "unidentified_revenue_share": ("Revenue with no Customer ID / revenue", "daily.csv"),
    "top10_customer_share_of_identified": ("Top 10 customers' revenue / identified revenue", "customers.csv"),
    "uk_share": ("United Kingdom revenue / revenue", "countries.csv"),
    "uk_revenue": ("United Kingdom revenue", "countries.csv"),
    "international_revenue": ("Revenue outside the United Kingdom", "countries.csv"),
    "uk_revenue_excl_reversed": ("Sensitivity: United Kingdom revenue with reversed lines removed", "reversals.csv"),
    "countries": ("Countries with revenue", "countries.csv"),
    "products_sold": ("Distinct product codes with revenue", "products.csv"),
    "cancel_value": ("C-invoice value on product codes (positive £)", "daily.csv"),
    "cancel_rate": ("Cancellation value / (revenue + cancellation value)", "daily.csv"),
    "revenue_excl_reversed": ("Sensitivity: revenue minus lines later reversed (reversals.csv)", "reversals.csv"),
    "orders_excl_reversed": ("Sensitivity: orders with reversed lines removed", "reversals.csv"),
    "aov_excl_reversed": ("Sensitivity: AOV with reversed lines removed", "reversals.csv"),
    "cancel_value_excl_reversed": ("Sensitivity: cancellation value minus the cancellations that reversed "
                                   "the lines in reversals.csv", "reversals.csv"),
    "cancel_rate_excl_reversed": ("Sensitivity: cancellation rate with reversed sales and their "
                                  "cancellations removed", "reversals.csv"),
    "top10_customer_share_excl_reversed": ("Sensitivity: top 10 customers' share with reversed lines removed",
                                           "customers.csv (revenue_excl_reversed)"),
}


def daily_table(rev, canc, w, label):
    r, c = in_window(rev, w), in_window(canc, w)
    d = r.groupby(r.InvoiceDate.dt.date).agg(revenue=("line_value", "sum"), orders=("Invoice", "nunique"),
                                             customers=("Customer ID", "nunique"),
                                             largest_line=("line_value", "max"))
    d["cancel_value"] = -c.groupby(c.InvoiceDate.dt.date).line_value.sum().reindex(d.index, fill_value=0)
    d.index = pd.to_datetime(d.index)
    d.insert(0, "window", label)
    d.insert(1, "day_of_month", d.index.day)
    d.insert(2, "weekday", d.index.day_name())
    d["cum_revenue"] = d.revenue.cumsum()
    return d.rename_axis("date")


def by_key(rev, wins, key, cols=("current", "prior_year")):
    t = pd.concat({k: in_window(rev, wins[k]).groupby(key).line_value.sum() for k in cols}, axis=1).fillna(0)
    t["change"] = t.current - t.prior_year
    t["change_pct"] = t.current / t.prior_year.replace(0, np.nan) - 1
    return t


def mtd_trend(rev, rev_x, day, clock):
    """Revenue for the same day-of-month window (1st .. day at clock) in every month."""
    offset = pd.Timedelta(days=day - 1) + clock
    rows = []
    for m in pd.period_range(rev.month.min(), rev.month.max(), freq="M"):
        w = (m.to_timestamp(), m.to_timestamp() + offset)
        r, rx = in_window(rev, w), in_window(rev_x, w)
        rows.append({"month": str(m), "revenue": r.line_value.sum(), "orders": r.Invoice.nunique(),
                     "revenue_excl_reversed": rx.line_value.sum(),
                     "trading_days": r.InvoiceDate.dt.date.nunique()})
    t = pd.DataFrame(rows).set_index("month")
    t["revenue_yoy"] = t.revenue / t.revenue.shift(12) - 1
    t["revenue_excl_reversed_yoy"] = t.revenue_excl_reversed / t.revenue_excl_reversed.shift(12) - 1
    return t


def title(ax, text, subtitle):
    ax.set_title(text)
    ax.text(0, 1.015, subtitle, transform=ax.transAxes, color=INK_2, fontsize=9.5, va="bottom")


def charts(out, daily, trend, products, countries, label_cur, label_ly, rev_cur, rev_x_cur):
    cdir = out / "charts"
    cdir.mkdir(parents=True, exist_ok=True)

    # 1. Cumulative revenue by day of month, current vs prior year, with the reversal sensitivity.
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for label, colour in [(label_ly, PRIOR), (label_cur, CURRENT)]:
        d = daily[daily.window == label]
        ax.plot(d.day_of_month, d.cum_revenue, color=colour, lw=2, marker="o", ms=5, label=label)
        ax.annotate(f"£{d.cum_revenue.iat[-1] / 1e3:,.0f}K", (d.day_of_month.iat[-1], d.cum_revenue.iat[-1]),
                    xytext=(6, 0), textcoords="offset points", va="center", color=INK, fontsize=9)
    d = daily[daily.window == label_cur]
    cum_x = d.cum_revenue - d.reversed_value.cumsum()
    ax.plot(d.day_of_month, cum_x, color=CURRENT, lw=2, ls=(0, (3, 2)), label=f"{label_cur} excl. order 581483")
    ax.annotate(f"£{cum_x.iat[-1] / 1e3:,.0f}K", (d.day_of_month.iat[-1], cum_x.iat[-1]),
                xytext=(6, 0), textcoords="offset points", va="center", color=INK_2, fontsize=9)
    ax.yaxis.set_major_formatter(GBP_K)
    ax.set_xticks(range(1, 10))
    ax.set_xlabel("Day of month (9th to 12:50)")
    ax.set_ylim(0)
    ax.set_xlim(0.7, 10)
    ax.legend(loc="upper left")
    title(ax, "Month-to-date revenue, 1-9 December", "Cumulative approved revenue by day; dashed line removes the "
          "£168K order 581483, cancelled 12 minutes after the sale")
    fig.savefig(cdir / "01_mtd_cumulative_revenue.png")
    plt.close(fig)

    # 2. Same-window revenue for every month (like-for-like trend).
    fig, ax = plt.subplots(figsize=(9, 4.2))
    x = np.arange(len(trend))
    colours = [CURRENT if i == len(trend) - 1 else (PRIOR if i == len(trend) - 13 else GRAY) for i in x]
    ax.bar(x, trend.revenue, color=colours, width=0.72, zorder=2)
    ax.plot(x[-1:], trend.revenue_excl_reversed.iloc[-1:], marker="_", ms=15, mew=2.5, color=INK, ls="none",
            zorder=3, label="Dec 2011 excl. reversed order 581483")
    for i, dx, ha in ((len(trend) - 13, 0, "center"), (len(trend) - 2, -4, "right"), (len(trend) - 1, 0, "center")):
        ax.annotate(f"£{trend.revenue.iat[i] / 1e3:,.0f}K", (x[i], trend.revenue.iat[i]), xytext=(dx, 4),
                    textcoords="offset points", ha=ha, va="bottom", color=INK, fontsize=8.5)
    ax.annotate(f"£{trend.revenue_excl_reversed.iat[-1] / 1e3:,.0f}K", (x[-1], trend.revenue_excl_reversed.iat[-1]),
                xytext=(18, 0), textcoords="offset points", ha="left", va="center", color=INK, fontsize=8.5)
    ax.set_xlim(-0.7, len(trend) + 1.2)
    ax.set_xticks(x[::2], [pd.Period(m).strftime("%b %y") for m in trend.index[::2]], rotation=0, fontsize=8.5)
    ax.yaxis.set_major_formatter(GBP_K)
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left")
    title(ax, "Revenue in the first 9 days of each month", "Days 1-9 to 12:50, every month Dec 2009-Dec 2011; "
          "blue = Dec 2011, orange = Dec 2010")
    fig.savefig(cdir / "02_mtd_window_trend.png")
    plt.close(fig)

    # 3. Top 10 products this month-to-date, with prior-year value.
    top = products[~products.reversed_in_current].sort_values("current", ascending=False).head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    y = np.arange(len(top))
    ax.barh(y + 0.2, top.current, height=0.38, color=CURRENT, label=label_cur, zorder=2)
    ax.barh(y - 0.2, top.prior_year, height=0.38, color=PRIOR, label=label_ly, zorder=2)
    ax.set_yticks(y, [f"{d[:34]}" for d in top.description], fontsize=8.5)
    ax.xaxis.set_major_formatter(GBP_K)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right")
    title(ax, "Top 10 products, month-to-date", "Approved revenue, 1-9 Dec to 12:50; excludes the reversed "
          f"£{products[products.reversed_in_current].current.sum() / 1e3:,.0f}K order (chart 1)")
    fig.savefig(cdir / "03_top_products.png")
    plt.close(fig)

    # 4. Revenue by market: UK and the top international countries.
    c = countries.drop(index="United Kingdom").sort_values("current", ascending=False)
    shown = pd.concat([c.head(8), c.iloc[8:].sum().to_frame("All other").T])[["current", "prior_year"]]
    shown = shown.iloc[::-1]
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    y = np.arange(len(shown))
    ax.barh(y + 0.2, shown.current, height=0.38, color=CURRENT, label=label_cur, zorder=2)
    ax.barh(y - 0.2, shown.prior_year, height=0.38, color=PRIOR, label=label_ly, zorder=2)
    ax.set_yticks(y, shown.index, fontsize=9)
    ax.xaxis.set_major_formatter(GBP_K)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="center right")
    uk = countries.loc["United Kingdom"]
    title(ax, "International revenue by market, month-to-date",
          f"1-9 Dec to 12:50; top 8 non-UK countries. UK (not shown): £{uk.current / 1e3:,.0f}K "
          f"(£{(uk.current - rev_cur + rev_x_cur) / 1e3:,.0f}K excl. reversed order) vs £{uk.prior_year / 1e3:,.0f}K")
    fig.savefig(cdir / "04_markets.png")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--month", default=None, help="Review month YYYY-MM (default: last month in the data)")
    args = ap.parse_args()

    df = load()
    rev, audit = revenue_rows(df)
    canc = cancellation_rows(df)
    last_ts = df.InvoiceDate.max()
    month = pd.Period(args.month, "M") if args.month else last_ts.to_period("M")
    if month != last_ts.to_period("M"):
        last_ts = (month + 1).to_timestamp() - pd.Timedelta(minutes=1)  # full month if not the latest
    wins = windows(month, last_ts)
    out = OUT / f"mbr_{month.strftime('%Y_%m')}"
    out.mkdir(parents=True, exist_ok=True)

    # Reversed large orders (same detector as retail_analysis.py), for the sensitivity.
    _, _, reversed_, _, _, _ = anomaly_tables(rev, canc, df)
    rev_keys = set(zip(reversed_.Invoice, reversed_.StockCode))
    is_rev = pd.Series([k in rev_keys for k in zip(rev.Invoice, rev.StockCode)], index=rev.index)
    rev_x = rev[~is_rev]
    canc_keys = set(zip(reversed_.Invoice_cancel, reversed_.StockCode_cancel))
    canc_x = canc[[k not in canc_keys for k in zip(canc.Invoice, canc.StockCode)]]
    rev_windows = pd.concat([in_window(reversed_, wins[k]).assign(window=k) for k in wins])

    first_purchase = rev.dropna(subset=["Customer ID"]).groupby("Customer ID").InvoiceDate.min()
    labels = {k: f"{w[0]:%b %Y}" for k, w in wins.items()}
    metrics = {k: window_metrics(rev, canc, rev_x, canc_x, w, first_purchase) for k, w in wins.items()}

    # Evidence tables.
    daily = pd.concat([daily_table(rev, canc, wins[k], labels[k]) for k in ("prior_year", "prior_month", "current")])
    rv = rev[is_rev].groupby(rev[is_rev].InvoiceDate.dt.normalize()).line_value.sum()
    daily["reversed_value"] = rv.reindex(daily.index, fill_value=0).values
    desc = rev.groupby("StockCode").Description.agg(lambda s: s.dropna().str.strip().mode().iat[0]
                                                    if s.notna().any() else "")
    products = by_key(rev, wins, "StockCode")
    products.insert(0, "description", desc.reindex(products.index))
    products["current_units"] = in_window(rev, wins["current"]).groupby("StockCode").Quantity.sum() \
        .reindex(products.index, fill_value=0)
    products["reversed_in_current"] = products.index.isin(in_window(reversed_, wins["current"]).StockCode)
    products = products.sort_values("current", ascending=False)
    countries = by_key(rev, wins, "Country", cols=("current", "prior_year", "prior_month"))
    countries["share_current"] = countries.current / countries.current.sum()
    countries = countries.sort_values("current", ascending=False)
    cur = in_window(rev, wins["current"]).dropna(subset=["Customer ID"])
    customers = cur.groupby("Customer ID").agg(country=("Country", "first"), revenue=("line_value", "sum"),
                                               orders=("Invoice", "nunique"))
    customers["first_purchase"] = first_purchase.reindex(customers.index)
    customers["new_this_month"] = customers.first_purchase >= wins["current"][0]
    prior12 = rev[(rev.InvoiceDate >= wins["current"][0] - pd.DateOffset(months=12))
                  & (rev.InvoiceDate < wins["current"][0])]["Customer ID"].dropna().unique()
    customers["new_12m_lookback"] = ~customers.index.isin(prior12)
    customers["revenue_excl_reversed"] = in_window(rev_x, wins["current"]).groupby("Customer ID") \
        .line_value.sum().reindex(customers.index, fill_value=0)
    customers = customers.sort_values("revenue", ascending=False)
    customers["share_of_identified"] = customers.revenue / customers.revenue.sum()
    trend = mtd_trend(rev, rev_x, last_ts.day, last_ts - last_ts.normalize())

    tables = {"daily.csv": daily, "products.csv": products, "countries.csv": countries,
              "customers.csv": customers, "reversals.csv": rev_windows, "mtd_trend.csv": trend}
    for name, t in tables.items():
        t.to_csv(out / name, index=name != "reversals.csv", float_format="%.4f")

    # Metrics: every window value with definition and source, plus comparisons.
    result = {"generated": pd.Timestamp.now().isoformat(timespec="seconds"),
              "data_last_timestamp": str(last_ts),
              "windows": {k: {"label": labels[k], "start": str(w[0]), "end": str(w[1])} for k, w in wins.items()},
              "assumptions": ASSUMPTIONS,
              "revenue_filter_audit_all_data": [{"step": s, "rows_removed": n, "value_removed": round(v, 2)}
                                                for s, n, v in audit],
              "metrics": {}}
    for key, (definition, source) in DEFINITIONS.items():
        vals = {k: metrics[k][key] for k in wins}
        entry = {"definition": definition, "source": source,
                 **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in vals.items()}}
        if "share" in key or "rate" in key:  # ratios: change in percentage points
            entry["change_vs_prior_year_pts"] = (None if vals["current"] is None or vals["prior_year"] is None
                                                 else round(vals["current"] - vals["prior_year"], 4))
            entry["change_vs_prior_month_pts"] = (None if vals["current"] is None or vals["prior_month"] is None
                                                  else round(vals["current"] - vals["prior_month"], 4))
        else:
            entry["change_vs_prior_year"] = change(vals["prior_year"], vals["current"])
            entry["change_vs_prior_month"] = change(vals["prior_month"], vals["current"])
        result["metrics"][key] = entry
    result["reversed_orders_in_windows"] = [
        {"window": r.window, "invoice": r.Invoice, "date": str(r.InvoiceDate), "stock_code": r.StockCode,
         "description": r.Description, "quantity": int(r.Quantity), "value": round(float(r.line_value), 2),
         "customer": r["Customer ID"], "cancel_invoice": r.Invoice_cancel,
         "hours_to_cancel": round(float(r.hours_to_cancel), 2)} for _, r in rev_windows.iterrows()]
    (out / "metrics.json").write_text(json.dumps(result, indent=2, default=str))

    charts(out, daily, trend, products, countries, labels["current"], labels["prior_year"],
           metrics["current"]["revenue"], metrics["current"]["revenue_excl_reversed"])

    print(f"Wrote {out}")
    for k in ("revenue", "orders", "aov", "customers", "new_customers", "new_customers_12m_lookback",
              "cancel_rate", "cancel_rate_excl_reversed", "revenue_excl_reversed",
              "top10_customer_share_excl_reversed"):
        m = result["metrics"][k]
        print(f"{k:24s} cur={m['current']!s:>14} ly={m['prior_year']!s:>14} pm={m['prior_month']!s:>14}")
    print("Reversed orders in windows:")
    for r in result["reversed_orders_in_windows"]:
        print(" ", r)


if __name__ == "__main__":
    main()
