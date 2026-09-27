"""Business-health analysis: builds the charts for outputs/business_analysis.md.

Reads data/processed/online_retail_II.csv (never the raw workbook), applies the
cleaning rules from outputs/data_profile.md in memory only, and writes PNG
charts to outputs/charts/. It prints the headline numbers the report quotes.

Cleaning applied (nothing is written back to disk):
- drop the 2010-12-01..09 rows duplicated in sheet "Year 2009-2010";
- drop remaining exact duplicate lines;
- upper-case StockCode, trim Description, map EIRE -> Ireland, RSA -> South Africa;
- "product" = StockCode of 5 digits + optional letters (excludes postage, fees...);
- sales = product lines, not cancelled, Quantity > 0 and Price > 0;
- net revenue = sales + product cancellations (C-invoices, negative).

Financial years run Dec-Nov so both are complete 12-month periods:
FY1 = Dec 2009-Nov 2010, FY2 = Dec 2010-Nov 2011. Dec 2011 (1-9 only) is partial.

Usage (from the repo root):
    python scripts/analyze_business.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, PercentFormatter

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = REPO_ROOT / "data" / "processed" / "online_retail_II.csv"
CHART_DIR = REPO_ROOT / "outputs" / "charts"

# Chart tokens (light mode, validated categorical slots 1-2).
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SERIES_1 = "#2a78d6"  # blue
SERIES_2 = "#eb6834"  # orange
GRAY_MARK = "#c3c2b7"
SEQ_BLUES = ["#f0f5fc", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial"],
    "font.size": 10,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": AXIS,
    "axes.labelcolor": INK_2,
    "axes.titlecolor": INK,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.titlepad": 24,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "xtick.labelcolor": INK_2,
    "ytick.labelcolor": INK_2,
    "legend.frameon": False,
    "legend.labelcolor": INK_2,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "savefig.facecolor": SURFACE,
})

GBP_K = FuncFormatter(lambda v, _: f"£{v / 1e3:,.0f}K")
GBP_M = FuncFormatter(lambda v, _: f"£{v / 1e6:,.1f}M")


def load() -> pd.DataFrame:
    df = pd.read_csv(
        DATA_FILE,
        dtype={"Invoice": str, "StockCode": str, "Customer ID": str},
        parse_dates=["InvoiceDate"],
    )
    cols = [c for c in df.columns if c != "source_sheet"]
    overlap = (df.source_sheet == "Year 2009-2010") & (df.InvoiceDate >= "2010-12-01")
    df = df[~overlap].drop_duplicates(subset=cols).copy()
    df["StockCode"] = df.StockCode.str.upper()
    df["Description"] = df.Description.str.strip()
    df["Country"] = df.Country.replace({"EIRE": "Ireland", "RSA": "South Africa"})
    df["rev"] = df.Quantity * df.Price
    df["is_cancel"] = df.Invoice.str.startswith("C")
    df["is_product"] = df.StockCode.str.match(r"^\d{5}[A-Z]{0,2}$")
    df["month"] = df.InvoiceDate.dt.to_period("M")
    df["fy"] = np.select(
        [df.InvoiceDate < "2010-12-01", df.InvoiceDate < "2011-12-01"], ["FY1", "FY2"], "Dec11"
    )
    return df


def title(ax, text, subtitle):
    ax.set_title(text)
    ax.text(0, 1.015, subtitle, transform=ax.transAxes, color=INK_2, fontsize=9.5, va="bottom")


def save(fig, name):
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(CHART_DIR / name)
    plt.close(fig)
    print(f"  wrote outputs/charts/{name}")


def chart_monthly_revenue(net):
    m = net.groupby("month").rev.sum()
    fy1 = m["2009-12":"2010-11"].values
    fy2 = m["2010-12":"2011-11"].values
    labels = ["Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov"]
    x = np.arange(12)
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.plot(x, fy1, color=SERIES_1, lw=2, marker="o", ms=5, label="FY1 (Dec 2009–Nov 2010)")
    ax.plot(x, fy2, color=SERIES_2, lw=2, marker="o", ms=5, label="FY2 (Dec 2010–Nov 2011)")
    for y, dy in [(fy1, -9), (fy2, 9)]:
        ax.annotate(f"£{y[-1] / 1e6:.2f}M", (11, y[-1]), xytext=(8, dy), textcoords="offset points",
                    va="center", color=INK_2, fontsize=9)
    ax.set_xticks(x, labels)
    ax.set_xlim(-0.4, 11.9)
    ax.set_ylim(0, 1.6e6)
    ax.yaxis.set_major_formatter(GBP_M)
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left", ncols=2)
    title(ax, "Net revenue by month: the same shape two years running",
          "Net product revenue (sales minus cancellations). September–November brings in over a third of the year.")
    save(fig, "01_monthly_revenue_yoy.png")


def chart_new_vs_returning(cs):
    first = cs.groupby("Customer ID").month.min().rename("cohort")
    x = cs.merge(first, left_on="Customer ID", right_index=True)
    x["kind"] = np.where(x.month == x.cohort, "New", "Returning")
    t = x.groupby(["month", "kind"])["Customer ID"].nunique().unstack()
    t = t.loc["2010-01":"2011-11"]  # Dec 2009 is all "new" by construction; Dec 2011 partial
    idx = np.arange(len(t))
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    ax.bar(idx, t["Returning"], width=0.72, color=SERIES_1, label="Returning customers",
           edgecolor=SURFACE, linewidth=1)
    ax.bar(idx, t["New"], width=0.72, bottom=t["Returning"], color=SERIES_2, label="New customers",
           edgecolor=SURFACE, linewidth=1)
    ax.set_xticks(idx, [p.strftime("%b\n%Y") if p.month in (1, 7) else p.strftime("%b") for p in t.index])
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left", ncols=2)
    ax.set_ylabel("Active customers")
    title(ax, "Fewer new customers each month in 2011",
          "Customers with an ID who bought in each month. Early-2010 \"new\" counts are inflated: data starts Dec 2009.")
    save(fig, "02_new_vs_returning_customers.png")


def chart_concentration(cs):
    c = cs.groupby("Customer ID").rev.sum().sort_values(ascending=False)
    c = c[c > 0]
    share = c.cumsum() / c.sum()
    pct = np.arange(1, len(c) + 1) / len(c)
    fig, ax = plt.subplots(figsize=(7, 4.8))
    ax.plot(pct, share.values, color=SERIES_1, lw=2)
    ax.plot([0, 1], [0, 1], color=AXIS, lw=1)
    for p in (0.01, 0.10, 0.20):
        v = share.iloc[int(len(c) * p) - 1]
        ax.plot(p, v, "o", color=SERIES_1, ms=7, mec=SURFACE, mew=2)
        ax.annotate(f"Top {p:.0%} → {v:.0%} of revenue", (p, v), xytext=(10, -12),
                    textcoords="offset points", color=INK_2, fontsize=9)
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Share of customers (ranked by revenue)")
    ax.set_ylabel("Cumulative share of revenue")
    title(ax, "A few customers carry the business",
          f"{len(c):,} identified customers, net product revenue Dec 2009–Dec 2011.")
    save(fig, "03_customer_concentration.png")


def chart_cohort_retention(cs):
    first = cs.groupby("Customer ID").month.min().rename("cohort")
    act = cs[["Customer ID", "month"]].drop_duplicates().merge(first, left_on="Customer ID", right_index=True)
    act["age"] = (act.month - act.cohort).apply(lambda d: d.n)
    tab = act.groupby(["cohort", "age"])["Customer ID"].nunique().unstack()
    rate = tab.div(tab[0], axis=0).loc["2010-01":"2011-10", 1:12]
    sizes = tab.loc[rate.index, 0]
    from matplotlib.colors import ListedColormap, BoundaryNorm
    bounds = [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
    cmap = ListedColormap(SEQ_BLUES)
    norm = BoundaryNorm(bounds, cmap.N)
    fig, ax = plt.subplots(figsize=(9, 7.4))
    im = ax.imshow(rate.values, cmap=cmap, norm=norm, aspect="auto")
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    for i in range(rate.shape[0]):
        for j in range(rate.shape[1]):
            v = rate.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.0%}", ha="center", va="center", fontsize=7.5,
                        color="#ffffff" if v >= 0.20 else INK_2)
    ax.set_xticks(range(12), [str(a) for a in rate.columns])
    ax.set_yticks(range(len(rate)), [f"{p.strftime('%b %Y')}  (n={int(sizes[p])})" for p in rate.index])
    ax.set_xlabel("Months since first purchase")
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, shrink=0.6, pad=0.02, format=PercentFormatter(1, decimals=0), extend="max")
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=MUTED, labelcolor=INK_2)
    title(ax, "Only 1 in 5 new customers comes back in any given month",
          "Share of each monthly cohort that bought again N months later. Dec 2009 cohort omitted (includes pre-2009 customers).")
    save(fig, "04_cohort_retention.png")


def chart_top_products(net, sales):
    name = sales.groupby("StockCode").Description.agg(lambda s: s.mode().iloc[0])
    p = net.groupby("StockCode").rev.sum().nlargest(15)
    labels = [name[c].title() for c in p.index]
    y = np.arange(len(p))[::-1]
    fig, ax = plt.subplots(figsize=(8.5, 5.6))
    ax.barh(y, p.values, height=0.68, color=SERIES_1)
    for yi, v in zip(y, p.values):
        ax.text(v, yi, f"  £{v / 1e3:,.0f}K", va="center", color=INK_2, fontsize=8.5)
    ax.set_yticks(y, labels)
    ax.xaxis.set_major_formatter(GBP_K)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, p.max() * 1.15)
    total = net.rev.sum()
    title(ax, "Top 15 products: home décor and party goods",
          f"Net revenue Dec 2009–Dec 2011. Together {p.sum() / total:.0%} of product revenue across ~4,700 SKUs.")
    save(fig, "05_top_products.png")


def chart_countries(net):
    g = net[net.fy != "Dec11"].groupby(["Country", "fy"]).rev.sum().unstack().fillna(0)
    g = g.drop(index="United Kingdom").nlargest(12, "FY2").iloc[::-1]
    y = np.arange(len(g))
    h = 0.38
    fig, ax = plt.subplots(figsize=(8.5, 6))
    ax.barh(y + h / 2 + 0.01, g.FY1, height=h, color=SERIES_1, label="FY1")
    ax.barh(y - h / 2 - 0.01, g.FY2, height=h, color=SERIES_2, label="FY2")
    for yi, (a, b) in zip(y, zip(g.FY1, g.FY2)):
        chg = b / a - 1 if a > 0 else np.nan
        ax.text(max(a, b), yi, f"  {chg:+.0%}", va="center", color=INK_2, fontsize=8.5)
    ax.set_yticks(y, g.index)
    ax.xaxis.set_major_formatter(GBP_K)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, g.values.max() * 1.15)
    ax.legend(loc="lower right")
    title(ax, "Outside the UK: Europe and Australia grew, Ireland shrank",
          "Net revenue, top 12 non-UK countries by FY2. The UK (85% of revenue) is flat at £7.9M both years.")
    save(fig, "06_international_markets.png")


def chart_cancellations(sales, canc):
    s = sales.groupby("month").rev.sum()
    c = -canc.groupby("month").rev.sum()
    mega = canc.Quantity <= -70000
    c_mega = -canc[mega].groupby("month").rev.sum().reindex(c.index).fillna(0)
    rate_all = c / s
    rate_ex = (c - c_mega) / s
    idx = np.arange(len(s))
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    ax.bar(idx, rate_ex.values, width=0.72, color=SERIES_1, label="Cancellations")
    ax.bar(idx, (rate_all - rate_ex).values, width=0.72, bottom=rate_ex.values, color=GRAY_MARK,
           label="Two single mega-orders (74,215 and 80,995 units)", edgecolor=SURFACE, linewidth=1)
    ticks = [i for i, p in enumerate(s.index) if p.month in (1, 4, 7, 10)]
    ax.set_xticks(ticks, [s.index[i].strftime("%b\n%Y") if s.index[i].month == 1 else s.index[i].strftime("%b")
                          for i in ticks])
    ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left")
    title(ax, "Cancellations run at 1–6% of sales, apart from two outliers",
          "Value of cancelled product lines as a share of that month's product sales. Dec 2011 covers 1–9 Dec only.")
    save(fig, "07_cancellation_rate.png")


def chart_weekday_hour(sales):
    x = sales.assign(dow=sales.InvoiceDate.dt.dayofweek, hr=sales.InvoiceDate.dt.hour)
    x = x[x.dow != 5]  # Saturday: one trading day in two years
    t = x.groupby(["dow", "hr"]).rev.sum().unstack().reindex(columns=range(7, 21)).fillna(0)
    t = t.reindex([0, 1, 2, 3, 4, 6])
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("blues", SEQ_BLUES)
    fig, ax = plt.subplots(figsize=(9, 3.8))
    im = ax.imshow(t.values / 1e3, cmap=cmap, aspect="auto")
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks(range(t.shape[1]), [f"{h:02d}:00" for h in t.columns], rotation=0, fontsize=8)
    ax.set_yticks(range(6), ["Mon", "Tue", "Wed", "Thu", "Fri", "Sun"])
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, pad=0.02, format=FuncFormatter(lambda v, _: f"£{v:,.0f}K"))
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=MUTED, labelcolor=INK_2)
    title(ax, "Orders arrive in office hours, Sunday is a half day",
          "Product sales by weekday and hour of invoice, Dec 2009–Dec 2011. No Saturday trading.")
    save(fig, "08_weekday_hour.png")


def main():
    df = load()
    sales = df[df.is_product & ~df.is_cancel & (df.Quantity > 0) & (df.Price > 0)]
    canc = df[df.is_product & df.is_cancel]
    net = pd.concat([sales, canc])
    cs = sales.dropna(subset=["Customer ID"])

    print("Headline numbers")
    for fy in ["FY1", "FY2", "Dec11"]:
        s, n = sales[sales.fy == fy], net[net.fy == fy]
        print(f"  {fy}: sales £{s.rev.sum():,.0f}  net £{n.rev.sum():,.0f}  orders {s.Invoice.nunique():,}  "
              f"customers {s['Customer ID'].nunique():,}  AOV £{s.rev.sum() / s.Invoice.nunique():,.0f}")

    print("Charts")
    chart_monthly_revenue(net)
    chart_new_vs_returning(cs)
    chart_concentration(net.dropna(subset=["Customer ID"]))
    chart_cohort_retention(cs)
    chart_top_products(net, sales)
    chart_countries(net)
    chart_cancellations(sales, canc)
    chart_weekday_hour(sales)


if __name__ == "__main__":
    main()
