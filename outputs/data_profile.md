# Data Profile: Online Retail II

Profiled 2026-09-27. Nothing was modified: the raw workbook still matches its SHA256 in `data/README.md`, and all figures below come from reading `data/processed/online_retail_II.csv` (a straight conversion of both sheets, no cleaning).

## At a glance

| | |
|---|---|
| Rows | 1,067,371 (525,461 from sheet `Year 2009-2010`, 541,910 from `Year 2010-2011`) |
| Columns | 9 (8 original columns plus `source_sheet`) |
| Grain | One row per **invoice line**: one product on one invoice |
| Date range | 2009-12-01 07:45 to 2011-12-09 12:50 |
| Distinct invoices | 53,628 (8,292 of them are cancellations) |
| Distinct customers | 5,942 (for rows that have a Customer ID) |
| Distinct stock codes | 5,305 (about 5,240 real products; the rest are fees, postage and adjustments) |
| Countries | 43 values; United Kingdom has 91.9% of rows |
| Business | UK online retailer of giftware. Many of its customers are wholesalers, which explains the large quantities |

## Column dictionary

| Column | Type | Meaning | Notes |
|---|---|---|---|
| `source_sheet` | text | Which Excel sheet the row came from. **Added by `prepare_data.py`**, not in the source | 2 values. Needed for removing duplicates (see issue 1) |
| `Invoice` | text | Invoice number. All lines of one order share it | 6 digits for normal sales. A **`C` prefix means a cancellation or return** (19,494 rows). An **`A` prefix means a bad-debt accounting adjustment** (6 rows). Read it as text, not a number |
| `StockCode` | text | Product (item) code | Normally 5 digits, sometimes followed by a letter for a variant (e.g. `79323P` / `79323W`, pink and white). Some codes aren't products at all: `POST`, `DOT` (postage), `M` (manual), `D` (discount), `C2` (carriage), `BANK CHARGES`, `AMAZONFEE`, `CRUK` (charity commission), `S` (samples), `B` (bad debt), `ADJUST*`, `TEST00*`, `gift_0001_*` (gift vouchers), `DCGS*` (items from a separate "dotcom" channel) |
| `Description` | text | Product name | Usually upper case. Lower-case values are warehouse notes, not product names ("damaged", "check", "?", "wrongly coded 23343") |
| `Quantity` | integer | Units on the line | **Negative on cancellations** and on stock write-offs. Ranges from −80,995 to +80,995 |
| `InvoiceDate` | datetime | Date and time the invoice was created | Recorded to the minute (seconds are always 0). Timestamps are local UK time with no time zone |
| `Price` | decimal | Price of **one unit** in pounds sterling (£) | Line revenue = `Quantity × Price`. 6,202 rows have a price of 0. 5 rows are negative (bad-debt rows) |
| `Customer ID` | text | 5-digit customer number (12346 to 18287) | **Missing on 22.8% of rows.** Read it as text so it doesn't turn into `13085.0` |
| `Country` | text | Country where the customer lives | Belongs to the customer, not to the shipment. Constant within an invoice |

## Data-quality problems

Listed roughly from most to least serious.

1. **The two sheets overlap: 22,523 rows appear twice.** Both sheets contain every line from 2010-12-01 to 2010-12-09, and the two copies are identical. If you stack the sheets without handling this, December 2010 sales are counted twice. **Fix:** remove sheet 1 rows dated on or after 2010-12-01, or drop exact duplicates across all columns except `source_sheet`.
2. **About 11,800 more exact duplicate lines**, even after removing the overlap. Same invoice, product, quantity, price and minute. Some may be real double scans and some may be data-entry duplicates; the data can't tell them apart. For revenue analysis the usual choice is to drop them, but state that assumption.
3. **Customer ID is missing on 243,007 rows (22.8%)**, which is about 13.7% of gross revenue. These are real sales. They matter for revenue totals, but you can't use them for customer-level analysis (RFM, cohorts, CLV). The missing share is higher in 2010–11 (24.9%) than in 2009–10 (20.5%).
4. **Returns are mixed in with sales.** 8,292 cancellation invoices (`C` prefix) with negative quantities total about **−£1.46M**. Most of them don't point back to the original invoice, so you can't reliably match a return to its sale. One `C` row (`C496350`, "Manual") has a positive quantity.
5. **Stock write-offs look like sales lines.** 3,457 rows have a negative quantity but no `C` prefix. All of them have price 0 and no customer, and descriptions such as "damaged", "smashed", "thrown away", "missing", "check" or blank. They are inventory adjustments, not sales.
6. **Some stock codes aren't products** (about 6,100 rows). Postage, fees, Amazon charges, bank charges, manual adjustments, discounts, samples, test items and gift vouchers. They distort product rankings and average price. `AMAZONFEE` alone is about −£261K and the `B` bad-debt rows about −£148K. Exclude them from product analysis and report them separately if needed.
7. **Extreme outliers that cancel each other out.** The two largest orders (80,995 × "PAPER CRAFT, LITTLE BIRDIE" and 74,215 × "MEDIUM CERAMIC TOP STORAGE JAR") were each cancelled within minutes. They are fine in net figures but distort anything computed on gross sales only. The highest prices (up to £38,970) are all `M`/`AMAZONFEE`/`BANK CHARGES` rows.
8. **Zero-price rows (6,202).** Mostly the stock adjustments above, plus some real free items (e.g. 12,540 × "ASSTD DESIGN 3D PAPER STICKERS" at £0). All 4,382 rows with a blank Description have price 0.
9. **Descriptions are inconsistent.** 1,232 stock codes have more than one description, and 293 descriptions map to more than one code. About 217K descriptions have leading or trailing spaces, and about 51K contain double spaces. Group products by `StockCode`, not by `Description`, and trim text before comparing.
10. **Stock code letter case varies.** 3,366 rows have a lower-case variant suffix (e.g. `72349b`). Check whether each one matches an upper-case code before grouping.
11. **Country values need cleaning.** `Unspecified` (756 rows) and `European Community` (61) are not countries. Several names are old or unusual: `EIRE` (Ireland), `RSA` (South Africa), `USA`, `Korea`, `West Indies`, `Channel Islands`. 13 customers appear under more than one country.
12. **Gaps and edge effects in the dates.**
    - December 2011 stops on the 9th. Don't compare it to full months.
    - December 2009 is the first month, so every customer looks "new" then.
    - Saturdays are almost absent: the only Saturday with data is 2009-12-05. Christmas and UK bank holidays are missing, so zero-sales days are closures, not a lack of demand.
    - 83 invoices have lines with more than one timestamp.
13. **Wholesale buyers skew the numbers.** The median line is 3 units at £2.10, but the mean quantity is about 10 with a standard deviation of 173. Use medians and percentiles, or split wholesale from retail customers, rather than relying on averages.

### Recommended cleaning rules (for a later step; not applied)

Write the cleaned output to `data/processed/`, never to `data/raw/`:
- Drop the overlapping sheet-1 rows (issue 1), then drop exact duplicates (issue 2).
- Add flags instead of deleting rows: `is_cancellation`, `is_stock_adjustment`, `is_non_product`, `has_customer`.
- Add `revenue = Quantity × Price`.
- Trim descriptions and upper-case stock codes.
- Map country aliases to standard names.

After removing duplicates, sales of real products (quantity > 0, price > 0) total **about £19.64M** over roughly 1.0M lines.

## 10 business questions this data can answer

1. **How are revenue, orders and average order value trending month by month?** How strong is the Sept–Nov peak, and did 2011 grow compared with 2010?
2. **Who are the most valuable customers?** Segment them with RFM (recency, frequency, monetary value) and find how much revenue comes from the top 10% (checks the Pareto 80/20 pattern).
3. **How well are customers retained?** Build monthly acquisition cohorts and see what share of each cohort buys again 1, 3, 6 and 12 months later.
4. **Which products drive revenue, and which are the "long tail"?** Run an ABC analysis on stock codes.
5. **What is the return/cancellation rate** by product, customer and country, and which products are returned unusually often?
6. **Which international markets matter most outside the UK**, and how do their order size and frequency compare with the UK?
7. **Which products are bought together?** Run a market-basket analysis for cross-sell and bundle ideas.
8. **When do customers order?** Look at day of week and hour to guide staffing, email timing and dispatch cut-offs.
9. **How do wholesale and retail customers differ?** Compare order size, product mix, seasonality and value.
10. **Who is at risk of churning, and what does a customer lose look like?** Find formerly active customers who have stopped buying, and estimate the revenue involved.

(Other options: price changes per product over time, and how much the untracked guest/unknown-customer revenue is worth.)
