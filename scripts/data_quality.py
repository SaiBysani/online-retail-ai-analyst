"""Data-quality checks on data/processed/online_retail_II.csv.

Runs every check the data-quality skill needs (schema, row counts, nulls, duplicates,
negative quantities, invalid prices, cancellations, date ranges, suspicious values,
revenue lines reversed by a later cancellation)
and writes:

- outputs/data_quality_report.md   the generated report (evidence tables per check)
- outputs/data_quality_checks.json one record per check: status, headline, key numbers

Status per check: PASS (as expected), WARN (needs handling, already covered by a
CLAUDE.md rule or stated assumption), FAIL (breaks an assumption the analysis relies on).

Read-only: never touches data/raw/ and never writes to data/.

Usage (from the repo root):
    python scripts/data_quality.py [--out-dir outputs]
"""
import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd

from retail_common import (DATA, EXPECTED_COLUMNS, NON_PRODUCT, OUT, OVERLAP_END, OVERLAP_START,
                           SHEETS, deduplicated, gbp, load, md_table, pct, revenue_rows)

checks = []   # (id, title, status, headline, numbers, markdown body)


def check(cid, title, status, headline, numbers, body):
    checks.append({"id": cid, "title": title, "status": status, "headline": headline,
                   "numbers": numbers, "body": body})


def run_checks(raw):
    df = load()
    n = len(df)
    d = deduplicated(df)

    # 1. Schema -----------------------------------------------------------------
    missing = [c for c in EXPECTED_COLUMNS if c not in raw.columns]
    extra = [c for c in raw.columns if c not in EXPECTED_COLUMNS]
    bad_dates = int(df.InvoiceDate.isna().sum())
    qty_non_int = int((df.Quantity.dropna() % 1 != 0).sum())
    inv_pattern = df.Invoice.str.extract(r"^([A-Z]?)\d{6}$")[0]
    inv_counts = inv_pattern.fillna("other").replace("", "digits only").value_counts()
    cust_bad = int((~df["Customer ID"].dropna().str.fullmatch(r"\d{5}(\.0)?")).sum())
    dtypes = pd.DataFrame({"dtype as read": df[EXPECTED_COLUMNS].dtypes.astype(str)})
    status = "FAIL" if missing or bad_dates or qty_non_int else "PASS"
    check("schema", "Schema and types", status,
          f"{len(raw.columns)} columns; missing {missing or 'none'}; {bad_dates} unparseable dates; "
          f"{qty_non_int} non-integer quantities",
          {"columns": list(raw.columns), "missing": missing, "extra": extra,
           "unparseable_dates": bad_dates, "non_integer_quantities": qty_non_int,
           "invoice_formats": inv_counts.to_dict(), "malformed_customer_ids": cust_bad},
          f"{md_table(dtypes)}\n\nInvoice number formats (prefix + 6 digits):\n\n"
          f"{md_table(inv_counts.rename('rows').to_frame(), floatfmt='{:,.0f}')}\n\n"
          f"Customer IDs not matching 5 digits: {cust_bad:,}. Extra columns: {extra or 'none'}.")

    # 2. Row counts -------------------------------------------------------------
    per_sheet = df.source_sheet.value_counts().reindex(SHEETS)
    rev, audit = revenue_rows(df)
    audit_tbl = pd.DataFrame(audit, columns=["filter (applied in order)", "rows removed", "line value removed"])
    audit_tbl["line value removed"] = audit_tbl["line value removed"].map(gbp)
    unknown_sheet = int((~df.source_sheet.isin(SHEETS)).sum())
    check("row_counts", "Row counts and revenue filter audit", "FAIL" if unknown_sheet else "PASS",
          f"{n:,} rows; {len(d):,} after the overlap; {len(rev):,} revenue rows worth {gbp(rev.line_value.sum())}",
          {"rows": n, "rows_per_sheet": per_sheet.to_dict(), "rows_after_overlap": len(d),
           "revenue_rows": len(rev), "revenue_total": round(float(rev.line_value.sum()), 2),
           "audit": [{"step": s, "rows": r, "value": round(v, 2)} for s, r, v in audit]},
          f"{md_table(per_sheet.rename('rows').to_frame())}\n\n"
          f"Approved revenue definition, step by step (CLAUDE.md):\n\n{md_table(audit_tbl, index=False)}\n\n"
          f"Revenue rows: **{len(rev):,}**, total **{gbp(rev.line_value.sum(), 2)}**.")

    # 3. Nulls -----------------------------------------------------------------
    nulls = pd.DataFrame({"null rows": df[EXPECTED_COLUMNS].isna().sum()})
    nulls["share"] = (nulls["null rows"] / n).map(pct)
    no_cust = rev["Customer ID"].isna()
    blank_desc = df.Description.isna()
    blank_desc_price0 = int((blank_desc & (df.Price == 0)).sum())
    critical = int(df[["Invoice", "StockCode", "Quantity", "InvoiceDate", "Price"]].isna().sum().sum())
    check("nulls", "Missing values", "FAIL" if critical else "WARN",
          f"Customer ID missing on {pct(df['Customer ID'].isna().mean())} of rows "
          f"({pct(rev.line_value[no_cust].sum() / rev.line_value.sum())} of revenue)",
          {"nulls": nulls["null rows"].to_dict(),
           "revenue_without_customer": round(float(rev.line_value[no_cust].sum()), 2),
           "revenue_share_without_customer": float(rev.line_value[no_cust].sum() / rev.line_value.sum()),
           "blank_description_rows": int(blank_desc.sum()), "blank_description_price0": blank_desc_price0},
          f"{md_table(nulls)}\n\n"
          f"Revenue rows without a Customer ID: {int(no_cust.sum()):,} rows, "
          f"{gbp(rev.line_value[no_cust].sum())} "
          f"({pct(rev.line_value[no_cust].sum() / rev.line_value.sum())} of revenue). They count for revenue "
          f"but must be excluded from customer-level metrics.\n\n"
          f"Blank Description: {int(blank_desc.sum()):,} rows, of which {blank_desc_price0:,} have Price 0.")

    # 4. Duplicates --------------------------------------------------------------
    key = [c for c in EXPECTED_COLUMNS if c != "source_sheet"]
    ov1 = df[(df.source_sheet == SHEETS[0]) & (df.InvoiceDate >= OVERLAP_START)]
    ov2 = df[df.is_overlap_copy]
    same = (ov1[key].astype(str).sort_values(key).reset_index(drop=True)
            .equals(ov2[key].astype(str).sort_values(key).reset_index(drop=True)))
    dup_mask = d.duplicated(subset=key, keep="first")
    rev_dup = rev.duplicated(subset=key, keep="first")
    check("duplicates", "Duplicates", "WARN" if same else "FAIL",
          f"{len(ov2):,} overlap rows (copies identical: {same}); {int(dup_mask.sum()):,} further exact "
          f"duplicate lines, {int(rev_dup.sum()):,} of them inside revenue ({gbp(rev.line_value[rev_dup].sum())})",
          {"overlap_rows_sheet1": len(ov1), "overlap_rows_sheet2": len(ov2), "overlap_copies_identical": bool(same),
           "overlap_window": [str(OVERLAP_START), str(OVERLAP_END)],
           "exact_duplicates_after_overlap": int(dup_mask.sum()),
           "exact_duplicates_in_revenue": int(rev_dup.sum()),
           "exact_duplicate_revenue_value": round(float(rev.line_value[rev_dup].sum()), 2)},
          f"- Sheet overlap: sheet 1 has {len(ov1):,} rows dated on or after {OVERLAP_START:%Y-%m-%d}; sheet 2 has "
          f"{len(ov2):,} rows on or before {OVERLAP_END}. Identical as multisets: **{same}**. The approved definition "
          f"drops the sheet-2 copies.\n"
          f"- Exact duplicate lines remaining after the overlap (same invoice, code, quantity, price, minute, "
          f"customer): {int(dup_mask.sum()):,}. Inside revenue rows: {int(rev_dup.sum()):,} worth "
          f"{gbp(rev.line_value[rev_dup].sum())} ({pct(rev.line_value[rev_dup].sum() / rev.line_value.sum())} of revenue). "
          f"**The approved definition keeps them**; they may be genuine repeat scans, so this is a stated "
          f"assumption, not a fix.")

    # 5. Negative quantities -----------------------------------------------------
    neg = d[d.Quantity < 0]
    neg_kind = pd.Series("other", index=neg.index)
    neg_kind[neg.is_cancel] = "cancellation (C invoice)"
    neg_kind[~neg.is_cancel & (neg.Price == 0)] = "stock adjustment (no C, price 0)"
    neg_kind[~neg.is_cancel & neg.is_bad_debt] = "bad-debt adjustment (A)"
    neg_tbl = (neg.assign(kind=neg_kind).groupby("kind")
               .agg(rows=("Invoice", "size"), units=("Quantity", "sum"),
                    line_value=("line_value", "sum"), with_customer=("Customer ID", "count")))
    adj = neg[neg_kind == "stock adjustment (no C, price 0)"]
    adj_desc = adj.Description.fillna("(blank)").str.strip().value_counts().head(12)
    other_neg = int((neg_kind == "other").sum())
    pos_cancel = d[d.is_cancel & (d.Quantity > 0)]
    check("negative_quantities", "Negative quantities", "FAIL" if other_neg else "WARN",
          f"{len(neg):,} negative-quantity rows: {int(neg.is_cancel.sum()):,} cancellations, "
          f"{len(adj):,} price-0 stock adjustments, {other_neg:,} unexplained",
          {"negative_rows": len(neg), "by_kind": neg_tbl.rows.to_dict(),
           "stock_adjustments_with_customer": int(adj["Customer ID"].notna().sum()),
           "unexplained_negative_rows": other_neg, "cancel_rows_positive_qty": len(pos_cancel)},
          f"Counted once across the overlap.\n\n{md_table(neg_tbl)}\n\n"
          f"Stock adjustments with a Customer ID: {int(adj['Customer ID'].notna().sum()):,}. "
          f"Most common descriptions on them:\n\n{md_table(adj_desc.rename('rows').to_frame())}\n\n"
          f"Cancellation lines with a *positive* quantity: {len(pos_cancel):,} "
          f"({', '.join(pos_cancel.Invoice.head(5)) or 'none'}).\n\n"
          f"None of these reach revenue: the Quantity > 0 and not-C filters remove them.")

    # 6. Invalid prices ------------------------------------------------------------
    zero = d[d.Price == 0]
    negp = d[d.Price < 0]
    zero_pos = zero[zero.Quantity > 0]
    top_zero = (zero_pos.groupby(["StockCode", "Description"], dropna=False).Quantity.sum()
                .sort_values(ascending=False).head(5).rename("units at £0").to_frame())
    top_price = (d[d.Price > 0].nlargest(10, "Price")[["Invoice", "StockCode", "Description", "Quantity", "Price"]])
    top_price_prod = d[(d.Price > 0) & ~d.is_non_product & ~d.is_cancel].nlargest(5, "Price")[
        ["Invoice", "StockCode", "Description", "Quantity", "Price"]]
    check("invalid_prices", "Invalid prices", "FAIL" if (negp.Invoice.str[0] != "A").any() else "WARN",
          f"{len(zero):,} rows at £0 ({len(zero_pos):,} with positive quantity); {len(negp)} negative-price rows "
          f"(invoices {', '.join(negp.Invoice.unique())})",
          {"zero_price_rows": len(zero), "zero_price_positive_qty": len(zero_pos),
           "zero_price_positive_qty_with_customer": int(zero_pos["Customer ID"].notna().sum()),
           "negative_price_rows": len(negp), "negative_price_invoices": sorted(negp.Invoice.unique()),
           "max_price": float(d.Price.max()), "max_product_price": float(top_price_prod.Price.max())},
          f"- Price = 0: {len(zero):,} rows; {len(zero_pos):,} of them have a positive quantity "
          f"({int(zero_pos['Customer ID'].notna().sum()):,} with a customer: free items or samples). Largest free "
          f"quantities:\n\n{md_table(top_zero)}\n\n"
          f"- Price < 0:\n\n{md_table(negp[['Invoice', 'StockCode', 'Description', 'Quantity', 'Price']], index=False)}\n\n"
          f"- Highest prices overall (expect fees and manual adjustments):\n\n{md_table(top_price, index=False)}\n\n"
          f"- Highest prices on real product sales:\n\n{md_table(top_price_prod, index=False)}")

    # 7. Cancellations -----------------------------------------------------------------
    c = d[d.is_cancel]
    c_prod = c[~c.is_non_product]
    gross = rev.line_value.sum()
    c_codes = (c[c.is_non_product].groupby("StockCode").line_value.sum().sort_values().head(8)
               .map(gbp).rename("cancelled value").to_frame())
    sales_inv = d[~d.is_cancel & ~d.is_bad_debt].Invoice.nunique()
    with_orig = c.Invoice.str[1:].isin(set(d.Invoice)).mean()
    check("cancellations", "Cancellations", "WARN",
          f"{c.Invoice.nunique():,} C invoices, {len(c):,} lines, {gbp(c.line_value.sum())} "
          f"({gbp(c_prod.line_value.sum())} on products = {pct(-c_prod.line_value.sum() / gross)} of revenue)",
          {"cancel_invoices": int(c.Invoice.nunique()), "cancel_rows": len(c),
           "cancel_value": round(float(c.line_value.sum()), 2),
           "cancel_value_products": round(float(c_prod.line_value.sum()), 2),
           "cancel_value_products_share_of_revenue": float(-c_prod.line_value.sum() / gross),
           "cancel_invoice_share": float(c.Invoice.nunique() / (c.Invoice.nunique() + sales_inv)),
           "cancel_rows_with_customer": float(c["Customer ID"].notna().mean()),
           "cancel_number_matches_sales_invoice": float(with_orig)},
          f"- {c.Invoice.nunique():,} cancellation invoices vs {sales_inv:,} other invoices "
          f"({pct(c.Invoice.nunique() / (c.Invoice.nunique() + sales_inv))} of all invoices).\n"
          f"- Total cancelled line value {gbp(c.line_value.sum())}; on products only {gbp(c_prod.line_value.sum())}, "
          f"equal to {pct(-c_prod.line_value.sum() / gross)} of approved revenue.\n"
          f"- {pct(c['Customer ID'].notna().mean())} of cancellation lines have a Customer ID.\n"
          f"- Cancellation numbers that match a sales invoice number (C + same digits): {pct(with_orig)}, "
          f"so returns cannot be linked to their original sale by number.\n\n"
          f"Largest cancelled non-product codes (fees and adjustments, not product returns):\n\n{md_table(c_codes)}")

    # 8. Date ranges -------------------------------------------------------------------
    rng = df.groupby("source_sheet").InvoiceDate.agg(["min", "max"]).reindex(SHEETS).astype(str)
    monthly = d.groupby("month").agg(rows=("Invoice", "size"), days=("InvoiceDate", lambda s: s.dt.date.nunique()))
    all_months = pd.period_range(monthly.index.min(), monthly.index.max(), freq="M")
    gaps = [str(m) for m in all_months if m not in monthly.index]
    dow = d.InvoiceDate.dt.day_name().value_counts()
    status = "FAIL" if gaps or d.InvoiceDate.min() < pd.Timestamp("2009-12-01") or d.InvoiceDate.max() > pd.Timestamp("2011-12-10") else "WARN"
    monthly.index = monthly.index.astype(str)
    check("date_ranges", "Date ranges", status,
          f"{d.InvoiceDate.min()} to {d.InvoiceDate.max()}; {len(all_months)} months, missing months: "
          f"{gaps or 'none'}; last month has {monthly['days'].iloc[-1]} trading days",
          {"min": str(d.InvoiceDate.min()), "max": str(d.InvoiceDate.max()), "missing_months": gaps,
           "by_sheet": rng.to_dict(orient="index"), "weekday_rows": dow.to_dict(),
           "last_month_trading_days": int(monthly["days"].iloc[-1])},
          f"{md_table(rng)}\n\nRows and trading days per month (after the overlap):\n\n{md_table(monthly)}\n\n"
          f"Rows by weekday:\n\n{md_table(dow.rename('rows').to_frame())}\n\n"
          f"Edge effects: the first month makes every customer look new; the last month is partial and must not be "
          f"compared with full months.")

    # 9. Suspicious values ------------------------------------------------------------------
    big = d[d.Quantity.abs() >= 10000][["Invoice", "StockCode", "Description", "Quantity", "Price", "InvoiceDate", "Customer ID"]]
    top_lines = rev.nlargest(10, "line_value")[["Invoice", "StockCode", "Description", "Quantity", "Price", "line_value", "Customer ID"]]
    odd_codes = d[~d.is_non_product & ~d.StockCode.str.fullmatch(r"\d{5}[A-Za-z]{0,2}")]
    odd_code_tbl = (odd_codes.groupby("StockCode").agg(rows=("Invoice", "size"), value=("line_value", "sum"))
                    .sort_values("rows", ascending=False).head(15))
    odd_in_rev = rev[~rev.StockCode.str.fullmatch(r"\d{5}[A-Za-z]{0,2}")]
    lower_desc = d[d.Description.notna() & (d.Description.str.strip() != d.Description.str.strip().str.upper())]
    countries = d.Country.value_counts()
    odd_countries = countries[countries.index.isin(["Unspecified", "European Community", "EIRE", "RSA", "West Indies"])]
    multi_country = int(d.dropna(subset=["Customer ID"]).groupby("Customer ID").Country.nunique().gt(1).sum())
    np_tbl = (d[d.is_non_product].groupby("StockCode").agg(rows=("Invoice", "size"), value=("line_value", "sum"))
              .sort_values("rows", ascending=False))
    unlisted_np = sorted(set(NON_PRODUCT) - set(np_tbl.index))
    q = rev.Quantity.describe(percentiles=[.5, .9, .99, .999])
    check("suspicious_values", "Suspicious values", "WARN",
          f"{len(big)} lines with |Quantity| >= 10,000; {len(odd_in_rev):,} revenue rows on non-standard codes "
          f"({gbp(odd_in_rev.line_value.sum())}); {len(lower_desc):,} lower-case descriptions; "
          f"{multi_country} customers in >1 country",
          {"extreme_quantity_lines": len(big), "top_revenue_line": float(top_lines.line_value.max()),
           "nonstandard_code_revenue_rows": len(odd_in_rev),
           "nonstandard_code_revenue_value": round(float(odd_in_rev.line_value.sum()), 2),
           "lowercase_description_rows": len(lower_desc), "customers_multi_country": multi_country,
           "non_product_rows": int(np_tbl.rows.sum()), "non_product_value": round(float(np_tbl.value.sum()), 2),
           "revenue_quantity_percentiles": {k: float(v) for k, v in q.items()}},
          f"**Extreme quantities (|Quantity| >= 10,000):**\n\n{md_table(big, index=False)}\n\n"
          f"**Top 10 revenue lines:**\n\n{md_table(top_lines, index=False)}\n\n"
          f"**Quantity distribution on revenue rows** (wholesale skew):\n\n{md_table(q.rename('Quantity').to_frame())}\n\n"
          f"**Codes outside the 5-digit product pattern and not on the non-product list** "
          f"(these stay in revenue under the approved definition; {len(odd_in_rev):,} revenue rows, "
          f"{gbp(odd_in_rev.line_value.sum())}):\n\n{md_table(odd_code_tbl)}\n\n"
          f"**Non-product codes** (excluded from revenue):\n\n{md_table(np_tbl)}\n\n"
          f"Listed non-product codes never seen in the data: {unlisted_np or 'none'}.\n\n"
          f"**Text and reference values:** {len(lower_desc):,} rows have lower-case descriptions (warehouse notes "
          f"such as 'damaged', 'check'); {multi_country} customers appear under more than one country; "
          f"non-standard country values:\n\n{md_table(odd_countries.rename('rows').to_frame())}")

    # 10. Revenue lines reversed by a later cancellation ----------------------------------------
    # A revenue line is "reversed" if the same customer has a C line within 24h after it that either
    # (a) has the same StockCode and Price and exactly the opposite Quantity, or
    # (b) is a manual 'M' line whose value equals minus the revenue line value.
    # Rows without a Customer ID cannot be matched. Each revenue line counts once.
    win = pd.Timedelta(hours=24)
    r = rev.dropna(subset=["Customer ID"]).reset_index().rename(columns={"index": "rid"})
    cc = d[d.is_cancel].dropna(subset=["Customer ID"])
    m1 = r.merge(cc[["Customer ID", "StockCode", "Price", "Quantity", "InvoiceDate", "Invoice"]]
                 .assign(Quantity=lambda x: -x.Quantity),
                 on=["Customer ID", "StockCode", "Price", "Quantity"], suffixes=("", "_c"))
    cm = cc[cc.StockCode == "M"][["Customer ID", "line_value", "InvoiceDate", "Invoice"]].assign(
        line_value=lambda x: (-x.line_value).round(2))
    m2 = r.assign(line_value=r.line_value.round(2)).merge(cm, on=["Customer ID", "line_value"], suffixes=("", "_c"))
    matched = pd.concat([m1.assign(match="same code"), m2.assign(match="manual M")])
    dt = matched.InvoiceDate_c - matched.InvoiceDate
    matched = matched[(dt >= pd.Timedelta(0)) & (dt <= win)].assign(minutes=(dt[(dt >= pd.Timedelta(0)) & (dt <= win)]
                                                                             .dt.total_seconds() / 60))
    matched = matched.sort_values("minutes").drop_duplicates("rid")
    rev_line = rev.set_index(rev.index).line_value
    val = float(rev_line.loc[matched.rid].sum())
    big_rev = matched[matched.line_value.abs() >= 5000]
    big_val = float(rev_line.loc[big_rev.rid].sum())
    top_rev = (matched.assign(value=rev_line.loc[matched.rid].values)
               .nlargest(10, "value")[["Invoice", "Invoice_c", "match", "StockCode", "Quantity", "value",
                                       "minutes", "Customer ID"]])
    check("reversed_sales", "Revenue lines reversed by a later cancellation", "WARN",
          f"{len(matched):,} revenue lines ({gbp(val)}, {pct(val / gross)} of revenue) cancelled by the same "
          f"customer within 24h; {len(big_rev)} of them >= £5,000 worth {gbp(big_val)}",
          {"reversed_rows": len(matched), "reversed_value": round(val, 2),
           "reversed_share_of_revenue": float(val / gross),
           "reversed_rows_same_code": int((matched.match == "same code").sum()),
           "reversed_rows_manual_m": int((matched.match == "manual M").sum()),
           "reversed_rows_ge_5000": len(big_rev), "reversed_value_ge_5000": round(big_val, 2),
           "window_hours": 24},
          f"Matching rule: same Customer ID, cancellation dated 0-24h after the sale, and either the same "
          f"StockCode + Price with the opposite Quantity, or a manual `M` cancellation whose value equals the "
          f"sale line value. Rows without a Customer ID cannot be matched, so this is a lower bound.\n\n"
          f"- Matched revenue lines: {len(matched):,}, worth {gbp(val)} ({pct(val / gross)} of approved revenue).\n"
          f"- The approved definition keeps these sales in revenue and drops the cancellations (C rows are "
          f"excluded, and `M` is a non-product code), so revenue includes sales that were reversed.\n"
          f"- Lines >= £5,000: {len(big_rev)}, worth {gbp(big_val)}.\n\n"
          f"Largest reversed revenue lines:\n\n{md_table(top_rev, index=False)}")


def write(out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = pd.DataFrame([(c["title"], c["status"], c["headline"]) for c in checks],
                           columns=["check", "status", "result"])
    parts = [
        "# Data Quality Report: Online Retail II", "",
        f"Generated {date.today()} by `scripts/data_quality.py` from `{DATA.relative_to(DATA.parents[2])}`. "
        f"Read-only: nothing in `data/` was changed. Machine-readable results: `data_quality_checks.json`.", "",
        "Status: **PASS** = as expected. **WARN** = a known issue that a CLAUDE.md rule or a stated assumption "
        "handles. **FAIL** = breaks an assumption the analysis relies on; resolve before analysing.", "",
        "## Summary", "", md_table(summary, index=False), "",
        "## Analyst notes", "", "<!-- ANALYST NOTES: filled in by the data-quality skill -->", "",
    ]
    for i, c in enumerate(checks, 1):
        parts += [f"## {i}. {c['title']} ({c['status']})", "", c["body"], ""]
    (out_dir / "data_quality_report.md").write_text("\n".join(parts))
    (out_dir / "data_quality_checks.json").write_text(json.dumps(
        [{k: v for k, v in c.items() if k != "body"} for c in checks], indent=2, default=str))
    print(md_table(summary, index=False))
    print(f"\nwrote {out_dir / 'data_quality_report.md'}\nwrote {out_dir / 'data_quality_checks.json'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", type=Path, default=OUT)
    args = ap.parse_args()
    raw = pd.read_csv(DATA, nrows=5)
    run_checks(raw)
    write(args.out_dir)


if __name__ == "__main__":
    main()
