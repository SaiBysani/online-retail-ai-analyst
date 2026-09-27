"""Total revenue and revenue by country, using the approved revenue definition (CLAUDE.md).

Revenue = Quantity x Price over rows that:
- are not cancellations (Invoice starts with C) or bad-debt adjustments (starts with A);
- have Quantity > 0 and Price > 0;
- are not non-product codes (postage, fees, adjustments);
- are counted once across the sheet overlap (drop the 'Year 2010-2011' copies
  dated on or before 2010-12-09 20:01).

Writes outputs/revenue_by_country.csv and prints a summary with the filter audit.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "online_retail_II.csv"
OUT = ROOT / "outputs"

NON_PRODUCT = {"POST", "DOT", "C2", "C3", "M", "m", "D", "S", "B", "BANK CHARGES",
               "AMAZONFEE", "CRUK", "ADJUST", "ADJUST2", "TEST001", "TEST002", "PADS", "GIFT"}
OVERLAP_END = pd.Timestamp("2010-12-09 20:01")


def load():
    df = pd.read_csv(DATA, dtype={"Invoice": str, "StockCode": str, "Customer ID": str},
                     parse_dates=["InvoiceDate"])
    df["line_value"] = df.Quantity * df.Price
    return df


def apply_definition(df):
    """Apply each filter in turn; return the revenue rows and an audit of what each step removed."""
    steps = [
        ("sheet overlap (2010-2011 copy)",
         (df.source_sheet == "Year 2010-2011") & (df.InvoiceDate <= OVERLAP_END)),
        ("cancellations (C)", df.Invoice.str.startswith("C")),
        ("bad-debt adjustments (A)", df.Invoice.str.startswith("A")),
        ("Quantity <= 0 or Price <= 0", (df.Quantity <= 0) | (df.Price <= 0)),
        ("non-product codes",
         df.StockCode.isin(NON_PRODUCT) | df.StockCode.str.startswith("gift_0001_")),
    ]
    keep = pd.Series(True, index=df.index)
    audit = []
    for name, drop in steps:
        removed = keep & drop
        audit.append((name, int(removed.sum()), df.loc[removed, "line_value"].sum()))
        keep &= ~drop
    return df[keep], audit


def main():
    df = load()
    rev, audit = apply_definition(df)
    total = rev.line_value.sum()

    by_country = (rev.groupby("Country")
                  .agg(revenue=("line_value", "sum"),
                       invoices=("Invoice", "nunique"),
                       customers=("Customer ID", "nunique"))
                  .sort_values("revenue", ascending=False))
    by_country["share"] = by_country.revenue / total
    by_country["avg_order_value"] = by_country.revenue / by_country.invoices
    OUT.mkdir(exist_ok=True)
    by_country.round(4).to_csv(OUT / "revenue_by_country.csv")

    print(f"Rows in data: {len(df):,}")
    for name, n, value in audit:
        print(f"  removed {name:<32} {n:>8,} rows  (line value £{value:,.0f})")
    print(f"Revenue rows: {len(rev):,}")
    dup = rev.duplicated(subset=[c for c in rev.columns if c != "source_sheet"])
    print(f"  of which exact duplicate lines: {dup.sum():,} (£{rev.line_value[dup].sum():,.0f})")
    print(f"\nTOTAL REVENUE: £{total:,.2f}")
    print(f"Countries: {len(by_country)}")
    print(f"\nTop 15 countries:\n{by_country.head(15).to_string(float_format=lambda x: f'{x:,.3f}')}")
    non_uk = by_country.drop("United Kingdom", errors="ignore")
    print(f"\nNon-UK total: £{non_uk.revenue.sum():,.0f} ({non_uk.revenue.sum() / total:.1%})")


if __name__ == "__main__":
    main()
