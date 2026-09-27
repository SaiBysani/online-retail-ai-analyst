"""Shared loading and business definitions for the analysis scripts.

Everything here follows the "Business definitions" section of CLAUDE.md, so every
script that imports it uses the same revenue, cancellation and overlap rules:

- Cancellation: Invoice starts with C. Bad-debt adjustment: Invoice starts with A.
- Sheet overlap: drop the 'Year 2010-2011' copies dated on or before 2010-12-09 20:01.
- Non-product codes: NON_PRODUCT below, plus any code starting with gift_0001_.
- Revenue: Quantity x Price over rows that survive all of REVENUE_STEPS.

Financial years run December to November so both are complete 12-month periods:
FY1 = Dec 2009-Nov 2010, FY2 = Dec 2010-Nov 2011. Dec 2011 has only 1-9 Dec.

Reads data/processed/online_retail_II.csv only. Nothing is written back to data/.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "online_retail_II.csv"
OUT = ROOT / "outputs"

EXPECTED_COLUMNS = ["source_sheet", "Invoice", "StockCode", "Description", "Quantity",
                    "InvoiceDate", "Price", "Customer ID", "Country"]
SHEETS = ["Year 2009-2010", "Year 2010-2011"]
NON_PRODUCT = {"POST", "DOT", "C2", "C3", "M", "m", "D", "S", "B", "BANK CHARGES",
               "AMAZONFEE", "CRUK", "ADJUST", "ADJUST2", "TEST001", "TEST002", "PADS", "GIFT"}
OVERLAP_START = pd.Timestamp("2010-12-01")
OVERLAP_END = pd.Timestamp("2010-12-09 20:01")
FY_BOUNDS = [("FY1", "2009-12-01", "2010-12-01"),
             ("FY2", "2010-12-01", "2011-12-01"),
             ("Dec11 (partial)", "2011-12-01", "2012-01-01")]


def load(path=DATA):
    """Read the processed CSV with safe dtypes and add line_value and flag columns."""
    df = pd.read_csv(path, dtype={"Invoice": str, "StockCode": str, "Customer ID": str},
                     parse_dates=["InvoiceDate"])
    return add_flags(df)


def add_flags(df):
    df = df.copy()
    df["line_value"] = df.Quantity * df.Price
    df["is_overlap_copy"] = (df.source_sheet == "Year 2010-2011") & (df.InvoiceDate <= OVERLAP_END)
    df["is_cancel"] = df.Invoice.str.startswith("C")
    df["is_bad_debt"] = df.Invoice.str.startswith("A")
    df["is_non_product"] = df.StockCode.isin(NON_PRODUCT) | df.StockCode.str.startswith("gift_0001_")
    df["month"] = df.InvoiceDate.dt.to_period("M")
    df["fy"] = fiscal_year(df.InvoiceDate)
    return df


def fiscal_year(dates):
    conds = [(dates >= start) & (dates < end) for _, start, end in FY_BOUNDS]
    return pd.Series(np.select(conds, [name for name, _, _ in FY_BOUNDS], "outside"), index=dates.index)


REVENUE_STEPS = [
    ("sheet overlap (2010-2011 copy)", lambda d: d.is_overlap_copy),
    ("cancellations (C)", lambda d: d.is_cancel),
    ("bad-debt adjustments (A)", lambda d: d.is_bad_debt),
    ("Quantity <= 0 or Price <= 0", lambda d: (d.Quantity <= 0) | (d.Price <= 0)),
    ("non-product codes", lambda d: d.is_non_product),
]


def deduplicated(df):
    """All rows counted once across the sheet overlap (no other filtering)."""
    return df[~df.is_overlap_copy]


def revenue_rows(df):
    """Apply the approved revenue definition in order.

    Returns (revenue rows, audit) where audit is a list of
    (step name, rows removed, line value removed) in the order applied.
    """
    keep = pd.Series(True, index=df.index)
    audit = []
    for name, rule in REVENUE_STEPS:
        removed = keep & rule(df)
        audit.append((name, int(removed.sum()), float(df.loc[removed, "line_value"].sum())))
        keep &= ~removed
    return df[keep], audit


def cancellation_rows(df, products_only=True):
    """Cancellation lines (C invoices), counted once across the overlap.

    products_only=True drops non-product codes, which makes the value comparable
    with approved revenue (which also excludes them).
    """
    d = deduplicated(df)
    mask = d.is_cancel
    if products_only:
        mask &= ~d.is_non_product
    return d[mask]


def gbp(x, dp=0):
    return f"-£{abs(x):,.{dp}f}" if x < 0 else f"£{x:,.{dp}f}"


def pct(x, dp=1):
    return "n/a" if x is None or pd.isna(x) else f"{x:.{dp}%}"


def md_table(df, index=True, floatfmt="{:,.2f}"):
    """Small dependency-free DataFrame -> Markdown table (pandas.to_markdown needs tabulate)."""
    d = df.reset_index() if index else df
    cols = [str(c) for c in d.columns]

    def fmt(v):
        if isinstance(v, (float, np.floating)):
            return "" if pd.isna(v) else floatfmt.format(v)
        if isinstance(v, (int, np.integer)):
            return f"{v:,}"
        return str(v).replace("|", "\\|")

    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in d.itertuples(index=False)]
    return "\n".join(lines)
