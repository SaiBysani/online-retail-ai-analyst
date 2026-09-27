# Total revenue and top countries

Source: `scripts/revenue_by_country.py` (full table in `outputs/revenue_by_country.csv`).
Period 2009-12-01 to 2011-12-09. All figures in GBP.

## Assumptions

- Revenue follows the approved definition in CLAUDE.md. It is Quantity × Price, summed over rows that meet all of these:
  - not a `C` or `A` invoice
  - Quantity > 0 and Price > 0
  - not a non-product code
  - counted once across the sheet overlap (the `Year 2010-2011` rows dated on or before 2010-12-09 20:01 are dropped)
- This is gross completed revenue. Cancellations are left out, not subtracted.
- Country is the value recorded on each invoice line.
- Exact duplicate lines are kept (11,731 rows, £57K, 0.3%), because the definition doesn't say to remove them.

## Filter audit (applied in order)

| Step | Rows removed | Line value removed |
|---|---:|---:|
| Sheet overlap (2010-2011 copy) | 22,523 | £377,488 |
| Cancellations (C) | 19,165 | −£1,465,304 |
| Bad-debt adjustments (A) | 6 | −£147,614 |
| Quantity ≤ 0 or Price ≤ 0 | 6,024 | £0 |
| Non-product codes | 4,582 | £821,725 |
| **Revenue rows kept** | **1,015,071** | **£19,700,954** |

## Total revenue: £19,700,954.44

## Top 10 countries

| # | Country | Revenue | Share | Invoices | Customers | Avg order |
|---|---|---:|---:|---:|---:|---:|
| 1 | United Kingdom | £16,856,331 | 85.6% | 36,184 | 5,334 | £466 |
| 2 | EIRE | £623,796 | 3.2% | 581 | 3 | £1,074 |
| 3 | Netherlands | £549,775 | 2.8% | 216 | 22 | £2,545 |
| 4 | Germany | £383,848 | 1.9% | 753 | 107 | £510 |
| 5 | France | £311,288 | 1.6% | 598 | 93 | £521 |
| 6 | Australia | £167,868 | 0.9% | 89 | 15 | £1,886 |
| 7 | Spain | £97,818 | 0.5% | 144 | 38 | £679 |
| 8 | Switzerland | £94,047 | 0.5% | 85 | 22 | £1,106 |
| 9 | Sweden | £86,353 | 0.4% | 99 | 19 | £872 |
| 10 | Denmark | £67,423 | 0.3% | 42 | 12 | £1,605 |

The other 33 countries make up the rest. All non-UK countries together: £2.84M (14.4%).

## Findings

- **The UK is 85.6% of revenue.** Every other country is 3.2% or less.
- **The Netherlands and Australia each rest on one account.** One customer brings in 96% of Netherlands revenue (customer 14646) and 86% of Australia's (customer 12415). EIRE has only 3 customer IDs, and one of them brings in 49%. Each of these countries' rankings depends on a single wholesale relationship.
- **Germany and France are the broad-based export markets.** They have 107 and 93 customers, and no single customer brings in more than 10%. That is the healthiest country-level demand outside the UK.
- 13.1% of total revenue has no Customer ID. The country field is still filled in for those rows, so they are counted in the country totals.
