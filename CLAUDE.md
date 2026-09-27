# online-retail-ai-analyst

Analysis project on the UCI Online Retail II dataset: invoice line items from a UK online retailer, 2009-12-01 to 2011-12-09. Currency is GBP.

## Operating model

For every request, pick one mode before doing anything, and say which one:

- **Answer:** the request is clear, uses the approved definitions and data below, and changes nothing outside `outputs/`; do it, state assumptions, cite the evidence.
- **Clarify:** an ambiguity would change the number (undefined metric, period, segment, currency, or a definition that conflicts with this file); ask one targeted question before calculating.
- **Review:** the result will go to leadership or another reader, changes a business definition, or disputes an existing number; do the work, then pass it to the `reviewer` agent before calling it done.
- **Stop:** the request would break a rule here (touch `data/raw/`, count cancellations or adjustments as revenue, push without approval) or the data cannot support it; decline, say why, and say what would unblock it.

## Data

- `data/raw/online_retail_II.xlsx`: the original download. Read-only.
- `data/processed/online_retail_II.csv`: the same data as one CSV (built by `scripts/prepare_data.py`). Use this for analysis.
- One row = one invoice line. Columns: `source_sheet`, `Invoice`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `Price` (unit price), `Customer ID`, `Country`.

## Folders

- `scripts/`: reusable Python scripts.
- `outputs/`: everything you generate (reports, tables, charts).

## Business definitions

- **Cancellation:** an invoice starting with `C`. Not completed revenue.
- **Bad-debt adjustment:** an invoice starting with `A`. Not revenue.
- **Sheet overlap:** the two sheets both contain 2010-12-01 to 2010-12-09. Count those rows once (drop the `Year 2010-2011` copies dated on or before 2010-12-09 20:01).
- **Non-product codes:** postage, fees and adjustments, not products: `POST`, `DOT`, `C2`, `C3`, `M`, `m`, `D`, `S`, `B`, `BANK CHARGES`, `AMAZONFEE`, `CRUK`, `ADJUST`, `ADJUST2`, `TEST001`, `TEST002`, `PADS`, `GIFT` and `gift_0001_*`.
- **Revenue (approved definition):** Quantity x Price, summed over rows that are not cancellations or bad-debt adjustments, have Quantity > 0 and Price > 0, are not non-product codes, and are counted once across the sheet overlap.

## Rules

The raw-data, delete, push and `outputs/` rules are also enforced by permission rules in `.claude/settings.json`.

- Never modify anything in `data/raw/`.
- Treat invoices beginning with C as cancellations; don't count them as completed revenue.
- Investigate negative quantities before interpreting them.
- Revenue = Quantity x Price only for rows that meet the approved revenue definition above.
- State your assumptions before calculating a business metric.
- Save generated outputs in `outputs/`.
- Every major conclusion must point back to the analysis or calculation behind it.
