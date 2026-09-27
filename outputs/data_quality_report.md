# Data Quality Report: Online Retail II

Generated 2026-09-27 by `scripts/data_quality.py` from `data/processed/online_retail_II.csv`. Read-only: nothing in `data/` was changed. Machine-readable results: `data_quality_checks.json`.

Status: **PASS** = as expected. **WARN** = a known issue that a CLAUDE.md rule or a stated assumption handles. **FAIL** = breaks an assumption the analysis relies on; resolve before analysing.

## Summary

| check | status | result |
|---|---|---|
| Schema and types | PASS | 9 columns; missing none; 0 unparseable dates; 0 non-integer quantities |
| Row counts and revenue filter audit | PASS | 1,067,371 rows; 1,044,848 after the overlap; 1,015,071 revenue rows worth £19,700,954 |
| Missing values | WARN | Customer ID missing on 22.8% of rows (13.1% of revenue) |
| Duplicates | WARN | 22,523 overlap rows (copies identical: True); 11,812 further exact duplicate lines, 11,731 of them inside revenue (£57,093) |
| Negative quantities | WARN | 22,557 negative-quantity rows: 19,164 cancellations, 3,393 price-0 stock adjustments, 0 unexplained |
| Invalid prices | WARN | 6,024 rows at £0 (2,631 with positive quantity); 5 negative-price rows (invoices A506401, A516228, A528059, A563186, A563187) |
| Cancellations | WARN | 8,292 C invoices, 19,165 lines, -£1,465,304 (-£719,656 on products = 3.7% of revenue) |
| Date ranges | WARN | 2009-12-01 07:45:00 to 2011-12-09 12:50:00; 25 months, missing months: none; last month has 8 trading days |
| Suspicious values | WARN | 15 lines with \|Quantity\| >= 10,000; 127 revenue rows on non-standard codes (£1,186); 5,866 lower-case descriptions; 13 customers in >1 country |
| Revenue lines reversed by a later cancellation | WARN | 1,444 revenue lines (£403,195, 2.0% of revenue) cancelled by the same customer within 24h; 3 of them >= £5,000 worth £284,623 |

## Analyst notes

No check FAILs; all WARNs are handled by CLAUDE.md rules or by the stated assumptions below. Figures are counted once across the sheet overlap unless stated.

- **Customer ID missing.** 243,007 rows (22.8%) have no Customer ID; within approved revenue that is 226,882 rows worth £2,576,013 (13.1% of £19,700,954). These rows count towards revenue but **must be excluded from customer-level metrics** (customer counts, AOV per customer, retention, RFM, CLV). Customer metrics therefore cover about 86.9% of revenue, and totals from customer analysis will not reconcile with total revenue. (§3 Missing values; `nulls.revenue_without_customer`)
- **Sheet overlap and duplicates.** The 22,523 overlap rows (£377,488) are identical copies (`overlap_copies_identical: true`), and the approved definition drops the 2010-2011 copies. A further 11,731 exact-duplicate lines remain inside revenue, worth £57,093 (0.3%). The approved definition keeps them as possible repeat scans; this is a stated assumption, not a fix. (§4 Duplicates)
- **Negative quantities are all classified.** 22,557 rows: 19,164 cancellations (C) and 3,393 price-£0 stock adjustments (warehouse notes such as 'damaged' or 'check', none with a customer). `unexplained_negative_rows` = 0. The 6 bad-debt rows (A invoices, -£147,614) have positive quantity and negative price. One C line has a positive quantity (C496350). None of these rows reach revenue. (§5 Negative quantities, §6 Invalid prices, §2 audit)
- **Cancellations.** 8,292 C invoices (15.5% of invoices), 19,165 lines, -£1,465,304 in total; -£719,656 of that is on products (3.7% of revenue). C numbers never match their original sale number, so returns cannot be linked by invoice. Revenue is **gross of returns**: any "net revenue" figure must be labelled as such and cannot be allocated back to the original sale. (§7 Cancellations)
- **Large sales reversed minutes later (possible issue with the approved definition).** 1,444 revenue lines (£403,195, 2.0% of revenue) are reversed by the same customer within 24h. The figure is approximate: rows without a customer cannot be matched, and a cancellation can match more than one sale. Three reversals account for £284,623: 581483 (£168,470, reversed after 12 min, and 2011-12-09, so inside the partial month), 541431 (£77,184, 16 min; customer 12346) and 556444 (£38,970, reversed via a manual `M` line after 3 min). The approved definition keeps the sales and drops the reversals, which inflates Dec 2011, Jan 2011 and Jun 2011 revenue and the value of customers 16446, 12346 and 15098. **Not changed.** Question for the user: should these reversed orders be netted out or excluded from revenue, or at least reported in a sensitivity line? Until the user answers, downstream work must flag them wherever they move a result: top products, top customers, monthly peaks, AOV. (§10 Revenue lines reversed; §9 Suspicious values)
- **Time-window edges.** Data runs 2009-12-01 to 2011-12-09 with no missing months. Dec 2011 has only 8 trading days and must not be compared with full months or used in growth rates; compare FY1 (Dec09-Nov10) with FY2 (Dec10-Nov11). Dec 2009 is the first month, so every customer there looks "new"; do not read it as acquisition, and use it only as a baseline for cohort and retention work. Saturday is almost absent (402 rows), so weekday patterns reflect the trading calendar. (§8 Date ranges)
- **Minor items that stay in revenue or need care.** 127 revenue rows on non-standard codes (`DCGS*`, `SP1002`) worth £1,186, kept by the approved definition. 2,631 positive-quantity £0 lines (free items) are excluded by Price > 0. EIRE, RSA, Unspecified (756 rows) and European Community appear as country values, and 13 customers appear under more than one country, so country analysis must pick one country per customer or work at line level. Non-product codes removed £821,725 of line value, mostly DOT and POST. (§9 Suspicious values, §6 Invalid prices, §2 audit)
- **Fit for analysis: yes with caveats.** Schema and row counts PASS and every negative row is explained. The approved revenue of £19,700,954 over 1,015,071 rows is reproducible (§2). Downstream analysis must carry these caveats: exclude missing Customer IDs from customer metrics (13.1% of revenue), treat Dec 2011 as partial and Dec 2009 as a cohort edge, and flag the £284,623 of large same-day reversals that the approved definition keeps in revenue. The last is pending a user decision.

## 1. Schema and types (PASS)

| index | dtype as read |
|---|---|
| source_sheet | str |
| Invoice | str |
| StockCode | str |
| Description | str |
| Quantity | int64 |
| InvoiceDate | datetime64[us] |
| Price | float64 |
| Customer ID | str |
| Country | str |

Invoice number formats (prefix + 6 digits):

| 0 | rows |
|---|---|
| digits only | 1,047,871 |
| C | 19,494 |
| A | 6 |

Customer IDs not matching 5 digits: 0. Extra columns: none.

## 2. Row counts and revenue filter audit (PASS)

| source_sheet | rows |
|---|---|
| Year 2009-2010 | 525,461 |
| Year 2010-2011 | 541,910 |

Approved revenue definition, step by step (CLAUDE.md):

| filter (applied in order) | rows removed | line value removed |
|---|---|---|
| sheet overlap (2010-2011 copy) | 22,523 | £377,488 |
| cancellations (C) | 19,165 | -£1,465,304 |
| bad-debt adjustments (A) | 6 | -£147,614 |
| Quantity <= 0 or Price <= 0 | 6,024 | £0 |
| non-product codes | 4,582 | £821,725 |

Revenue rows: **1,015,071**, total **£19,700,954.44**.

## 3. Missing values (WARN)

| index | null rows | share |
|---|---|---|
| source_sheet | 0 | 0.0% |
| Invoice | 0 | 0.0% |
| StockCode | 0 | 0.0% |
| Description | 4,382 | 0.4% |
| Quantity | 0 | 0.0% |
| InvoiceDate | 0 | 0.0% |
| Price | 0 | 0.0% |
| Customer ID | 243,007 | 22.8% |
| Country | 0 | 0.0% |

Revenue rows without a Customer ID: 226,882 rows, £2,576,013 (13.1% of revenue). They count for revenue but must be excluded from customer-level metrics.

Blank Description: 4,382 rows, of which 4,382 have Price 0.

## 4. Duplicates (WARN)

- Sheet overlap: sheet 1 has 22,523 rows dated on or after 2010-12-01; sheet 2 has 22,523 rows on or before 2010-12-09 20:01:00. Identical as multisets: **True**. The approved definition drops the sheet-2 copies.
- Exact duplicate lines remaining after the overlap (same invoice, code, quantity, price, minute, customer): 11,812. Inside revenue rows: 11,731 worth £57,093 (0.3% of revenue). **The approved definition keeps them**; they may be genuine repeat scans, so this is a stated assumption, not a fix.

## 5. Negative quantities (WARN)

Counted once across the overlap.

| kind | rows | units | line_value | with_customer |
|---|---|---|---|---|
| cancellation (C invoice) | 19,164 | -478,964 | -1,465,677.23 | 18,446 |
| stock adjustment (no C, price 0) | 3,393 | -569,314 | 0.00 | 0 |

Stock adjustments with a Customer ID: 0. Most common descriptions on them:

| Description | rows |
|---|---|
| (blank) | 2,633 |
| check | 121 |
| damages | 83 |
| ? | 81 |
| damaged | 78 |
| missing | 27 |
| sold as set on dotcom | 20 |
| Damaged | 17 |
| smashed | 9 |
| thrown away | 9 |
| Unsaleable, destroyed. | 9 |
| dotcom | 8 |

Cancellation lines with a *positive* quantity: 1 (C496350).

None of these reach revenue: the Quantity > 0 and not-C filters remove them.

## 6. Invalid prices (WARN)

- Price = 0: 6,024 rows; 2,631 of them have a positive quantity (70 with a customer: free items or samples). Largest free quantities:

| StockCode | Description | units at £0 |
|---|---|---|
| 84016 | FLAG OF ST GEORGE CAR FLAG | 17,996 |
| 84826 | ASSTD DESIGN 3D PAPER STICKERS | 12,540 |
| 22759 |  | 9,600 |
| 22752 |  | 6,000 |
| 37413 |  | 5,568 |

- Price < 0:

| Invoice | StockCode | Description | Quantity | Price |
|---|---|---|---|---|
| A506401 | B | Adjust bad debt | 1 | -53,594.36 |
| A516228 | B | Adjust bad debt | 1 | -44,031.79 |
| A528059 | B | Adjust bad debt | 1 | -38,925.87 |
| A563186 | B | Adjust bad debt | 1 | -11,062.06 |
| A563187 | B | Adjust bad debt | 1 | -11,062.06 |

- Highest prices overall (expect fees and manual adjustments):

| Invoice | StockCode | Description | Quantity | Price |
|---|---|---|---|---|
| C556445 | M | Manual | -1 | 38,970.00 |
| C512770 | M | Manual | -1 | 25,111.09 |
| 512771 | M | Manual | 1 | 25,111.09 |
| C520667 | BANK CHARGES | Bank Charges | -1 | 18,910.69 |
| C580605 | AMAZONFEE | AMAZON FEE | -1 | 17,836.46 |
| C540117 | AMAZONFEE | AMAZON FEE | -1 | 16,888.02 |
| C540118 | AMAZONFEE | AMAZON FEE | -1 | 16,453.71 |
| C537630 | AMAZONFEE | AMAZON FEE | -1 | 13,541.33 |
| 537632 | AMAZONFEE | AMAZON FEE | 1 | 13,541.33 |
| C537651 | AMAZONFEE | AMAZON FEE | -1 | 13,541.33 |

- Highest prices on real product sales:

| Invoice | StockCode | Description | Quantity | Price |
|---|---|---|---|---|
| 507637 | 84016 | FLAG OF ST GEORGE CAR FLAG | 1 | 1,157.15 |
| 502451 | 84016 | FLAG OF ST GEORGE CAR FLAG | 1 | 867.79 |
| 556444 | 22502 | PICNIC BASKET WICKER 60 PIECES | 60 | 649.50 |
| 556446 | 22502 | PICNIC BASKET WICKER 60 PIECES | 1 | 649.50 |
| 506571 | 84016 | FLAG OF ST GEORGE CAR FLAG | 1 | 408.40 |

## 7. Cancellations (WARN)

- 8,292 cancellation invoices vs 45,330 other invoices (15.5% of all invoices).
- Total cancelled line value -£1,465,304; on products only -£719,656, equal to 3.7% of approved revenue.
- 96.2% of cancellation lines have a Customer ID.
- Cancellation numbers that match a sales invoice number (C + same digits): 0.0%, so returns cannot be linked to their original sale by number.

Largest cancelled non-product codes (fees and adjustments, not product returns):

| StockCode | cancelled value |
|---|---|
| M | -£422,566 |
| AMAZONFEE | -£241,988 |
| BANK CHARGES | -£36,001 |
| POST | -£15,252 |
| D | -£13,278 |
| CRUK | -£7,933 |
| S | -£6,138 |
| ADJUST | -£2,063 |

## 8. Date ranges (WARN)

| source_sheet | min | max |
|---|---|---|
| Year 2009-2010 | 2009-12-01 07:45:00 | 2010-12-09 20:01:00 |
| Year 2010-2011 | 2010-12-01 08:26:00 | 2011-12-09 12:50:00 |

Rows and trading days per month (after the overlap):

| month | rows | days |
|---|---|---|
| 2009-12 | 45,228 | 21 |
| 2010-01 | 31,555 | 24 |
| 2010-02 | 29,388 | 24 |
| 2010-03 | 41,511 | 27 |
| 2010-04 | 34,057 | 23 |
| 2010-05 | 35,323 | 24 |
| 2010-06 | 39,983 | 26 |
| 2010-07 | 33,383 | 26 |
| 2010-08 | 33,306 | 26 |
| 2010-09 | 42,091 | 26 |
| 2010-10 | 59,098 | 26 |
| 2010-11 | 78,015 | 26 |
| 2010-12 | 42,481 | 20 |
| 2011-01 | 35,147 | 24 |
| 2011-02 | 27,707 | 24 |
| 2011-03 | 36,748 | 27 |
| 2011-04 | 29,916 | 21 |
| 2011-05 | 37,030 | 25 |
| 2011-06 | 36,874 | 26 |
| 2011-07 | 39,518 | 26 |
| 2011-08 | 35,284 | 26 |
| 2011-09 | 50,226 | 26 |
| 2011-10 | 60,742 | 26 |
| 2011-11 | 84,711 | 26 |
| 2011-12 | 25,526 | 8 |

Rows by weekday:

| InvoiceDate | rows |
|---|---|
| Thursday | 198,149 |
| Tuesday | 193,663 |
| Monday | 185,206 |
| Wednesday | 179,296 |
| Friday | 151,601 |
| Sunday | 136,531 |
| Saturday | 402 |

Edge effects: the first month makes every customer look new; the last month is partial and must not be compared with full months.

## 9. Suspicious values (WARN)

**Extreme quantities (|Quantity| >= 10,000):**

| Invoice | StockCode | Description | Quantity | Price | InvoiceDate | Customer ID |
|---|---|---|---|---|---|---|
| 497946 | 37410 | BLACK AND WHITE PAISLEY FLOWER MUG | 19,152 | 0.10 | 2010-02-15 11:57:00 | 13902 |
| 501534 | 21099 | SET/6 STRAWBERRY PAPER CUPS | 12,960 | 0.10 | 2010-03-17 13:09:00 | 13902 |
| 501534 | 21092 | SET/6 STRAWBERRY PAPER PLATES | 12,480 | 0.10 | 2010-03-17 13:09:00 | 13902 |
| 501534 | 21091 | SET/6 WOODLAND PAPER PLATES | 12,960 | 0.10 | 2010-03-17 13:09:00 | 13902 |
| 501534 | 21085 | SET/6 WOODLAND PAPER CUPS | 12,744 | 0.10 | 2010-03-17 13:09:00 | 13902 |
| 502269 | 21984 | PACK OF 12 PINK PAISLEY TISSUES  | 10,000 | 0.25 | 2010-03-23 15:36:00 | 17940 |
| 502269 | 21982 | PACK OF 12 SUKI TISSUES  | 10,000 | 0.25 | 2010-03-23 15:36:00 | 17940 |
| 502269 | 21980 | PACK OF 12 RED SPOTTY TISSUES  | 10,000 | 0.25 | 2010-03-23 15:36:00 | 17940 |
| 502269 | 21981 | PACK OF 12 WOODLAND TISSUES  | 10,000 | 0.25 | 2010-03-23 15:36:00 | 17940 |
| 507637 | 84016 | FLAG OF ST GEORGE CAR FLAG | 10,200 | 0.00 | 2010-05-10 14:55:00 |  |
| 541431 | 23166 | MEDIUM CERAMIC TOP STORAGE JAR | 74,215 | 1.04 | 2011-01-18 10:01:00 | 12346 |
| C541433 | 23166 | MEDIUM CERAMIC TOP STORAGE JAR | -74,215 | 1.04 | 2011-01-18 10:17:00 | 12346 |
| 578841 | 84826 | ASSTD DESIGN 3D PAPER STICKERS | 12,540 | 0.00 | 2011-11-25 15:57:00 | 13256 |
| 581483 | 23843 | PAPER CRAFT , LITTLE BIRDIE | 80,995 | 2.08 | 2011-12-09 09:15:00 | 16446 |
| C581484 | 23843 | PAPER CRAFT , LITTLE BIRDIE | -80,995 | 2.08 | 2011-12-09 09:27:00 | 16446 |

**Top 10 revenue lines:**

| Invoice | StockCode | Description | Quantity | Price | line_value | Customer ID |
|---|---|---|---|---|---|---|
| 581483 | 23843 | PAPER CRAFT , LITTLE BIRDIE | 80,995 | 2.08 | 168,469.60 | 16446 |
| 541431 | 23166 | MEDIUM CERAMIC TOP STORAGE JAR | 74,215 | 1.04 | 77,183.60 | 12346 |
| 556444 | 22502 | PICNIC BASKET WICKER 60 PIECES | 60 | 649.50 | 38,970.00 | 15098 |
| 530715 | 84347 | ROTATING SILVER ANGELS T-LIGHT HLDR | 9,360 | 1.69 | 15,818.40 | 15838 |
| 511465 | 15044A | PINK PAPER PARASOL  | 3,500 | 2.55 | 8,925.00 | 18008 |
| 567423 | 23243 | SET OF TEA COFFEE SUGAR TINS PANTRY | 1,412 | 5.06 | 7,144.72 | 17450 |
| 540815 | 21108 | FAIRY CAKE FLANNEL ASSORTED COLOUR | 3,114 | 2.10 | 6,539.40 | 15749 |
| 550461 | 21108 | FAIRY CAKE FLANNEL ASSORTED COLOUR | 3,114 | 2.10 | 6,539.40 | 15749 |
| 533027 | 22086 | PAPER CHAIN KIT 50'S CHRISTMAS  | 835 | 6.95 | 5,803.25 |  |
| 525968 | 84347 | ROTATING SILVER ANGELS T-LIGHT HLDR | 3,120 | 1.66 | 5,179.20 | 15838 |

**Quantity distribution on revenue rows** (wholesale skew):

| index | Quantity |
|---|---|
| count | 1,015,071.00 |
| mean | 11.06 |
| std | 128.01 |
| min | 1.00 |
| 50% | 3.00 |
| 90% | 24.00 |
| 99% | 100.00 |
| 99.9% | 499.86 |
| max | 80,995.00 |

**Codes outside the 5-digit product pattern and not on the non-product list** (these stay in revenue under the approved definition; 127 revenue rows, £1,186):

| StockCode | rows | value |
|---|---|---|
| DCGS0058 | 31 | 34.82 |
| DCGSSGIRL | 25 | 295.63 |
| DCGSSBOY | 23 | 251.35 |
| DCGS0003 | 14 | 32.59 |
| DCGS0076 | 14 | 275.96 |
| DCGS0069 | 6 | 80.31 |
| DCGS0004 | 5 | 67.94 |
| DCGS0066N | 4 | 17.30 |
| DCGS0072 | 4 | 20.68 |
| DCGS0070 | 3 | 25.44 |
| DCGS0068 | 3 | 17.12 |
| SP1002 | 3 | 14.75 |
| DCGS0037 | 2 | 12.72 |
| DCGS0062 | 2 | 2.51 |
| DCGS0006 | 1 | 0.00 |

**Non-product codes** (excluded from revenue):

| StockCode | rows | value |
|---|---|---|
| POST | 2,086 | 110,430.41 |
| DOT | 1,425 | 309,844.10 |
| M | 1,398 | -82,950.62 |
| C2 | 277 | 13,136.00 |
| D | 173 | -12,879.63 |
| S | 102 | -6,000.85 |
| BANK CHARGES | 100 | -35,482.25 |
| ADJUST | 67 | 6,835.24 |
| AMAZONFEE | 36 | -221,520.50 |
| gift_0001_20 | 29 | 471.06 |
| gift_0001_30 | 29 | 610.09 |
| PADS | 19 | -36.58 |
| CRUK | 16 | -7,933.43 |
| gift_0001_10 | 16 | 126.21 |
| TEST001 | 15 | 202.50 |
| gift_0001_50 | 8 | 253.59 |
| gift_0001_40 | 7 | 166.09 |
| B | 6 | -147,614.08 |
| m | 5 | 15.05 |
| gift_0001_80 | 4 | 0.00 |
| gift_0001_70 | 3 | 59.57 |
| ADJUST2 | 3 | 731.05 |
| TEST002 | 2 | 1.00 |
| gift_0001_60 | 2 | 0.00 |
| gift_0001_90 | 2 | 0.00 |
| GIFT | 1 | 0.00 |
| C3 | 1 | 0.00 |

Listed non-product codes never seen in the data: none.

**Text and reference values:** 5,866 rows have lower-case descriptions (warehouse notes such as 'damaged', 'check'); 13 customers appear under more than one country; non-standard country values:

| Country | rows |
|---|---|
| EIRE | 17,689 |
| Unspecified | 756 |
| RSA | 169 |
| European Community | 61 |
| West Indies | 54 |

## 10. Revenue lines reversed by a later cancellation (WARN)

Matching rule: same Customer ID, cancellation dated 0-24h after the sale, and either the same StockCode + Price with the opposite Quantity, or a manual `M` cancellation whose value equals the sale line value. Rows without a Customer ID cannot be matched, so this is a lower bound.

- Matched revenue lines: 1,444, worth £403,195 (2.0% of approved revenue).
- The approved definition keeps these sales in revenue and drops the cancellations (C rows are excluded, and `M` is a non-product code), so revenue includes sales that were reversed.
- Lines >= £5,000: 3, worth £284,623.

Largest reversed revenue lines:

| Invoice | Invoice_c | match | StockCode | Quantity | value | minutes | Customer ID |
|---|---|---|---|---|---|---|---|
| 581483 | C581484 | same code | 23843 | 80,995 | 168,469.60 | 12.00 | 16446 |
| 541431 | C541433 | same code | 23166 | 74,215 | 77,183.60 | 16.00 | 12346 |
| 556444 | C556445 | manual M | 22502 | 60 | 38,970.00 | 3.00 | 15098 |
| 567423 | C567527 | same code | 23113 | 756 | 3,825.36 | 1,331.00 | 17450 |
| 529350 | C529352 | same code | 71477 | 1,152 | 3,168.00 | 3.00 | 17450 |
| 515296 | C515299 | same code | 84078A | 85 | 2,970.75 | 6.00 | 13734 |
| 515281 | C515299 | same code | 84078A | 85 | 2,970.75 | 93.00 | 13734 |
| 569385 | C569387 | same code | 23284 | 200 | 1,416.00 | 1.00 | 14031 |
| 572324 | C572343 | same code | 23056 | 240 | 1,293.60 | 48.00 | 14607 |
| 539109 | C539329 | same code | 85123A | 500 | 1,275.00 | 1,350.00 | 16013 |
