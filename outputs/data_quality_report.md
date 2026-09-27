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
| Review windows (1-9 Dec 2011 / 1-9 Dec 2010 / 1-9 Nov 2011, to 12:50) | WARN | Dec 2010 window overlap copies identical: True, one copy kept: True; 0 unexplained negative rows in windows; Dec 2011 MTD revenue £615,493 includes £169,023 reversed within 24h |

## Analyst notes

No check FAILs. Every WARN is handled by a CLAUDE.md rule or a stated assumption. The notes below use the approved revenue definition unchanged, with windows inclusive from 00:00 on the 1st to 12:50 on the 9th. They are written for the Dec 2011 MTD business review.

- **Reversed £168k order in Dec 2011 MTD (the main risk for the review).** Invoice 581483, StockCode 23843 (PAPER CRAFT, LITTLE BIRDIE), 80,995 units x £2.08 = **£168,469.60**, customer 16446, 2011-12-09 09:15. It was cancelled 12 minutes later by C581484 (-80,995, -£168,469.60). The approved definition keeps the sale and drops the cancellation, so it makes up **27.4% of Dec 2011 MTD revenue (£615,493)**. Without the 12 reversed lines (£169,023) the window is £446,471 (sensitivity only). The comparison windows have little reversal: Dec 2010 £548 across 16 lines, Nov 2011 £6,135 across 47 lines. All reversing cancellations fall inside their windows. (§11 Review windows; `review_windows.windows.*.reversed_value`; §10; §9.) *Question for the user:* should the review report revenue as defined, with this line called out, or should it net out same-customer reversals within 24h? The second option changes the approved definition, so it needs sign-off. I have not applied it.
- **Sheet overlap in Dec 2010 window: clean.** Each sheet has 20,240 rows dated 1-9 Dec 2010 to 12:50. The two sets are identical as multisets. After deduplication 20,240 rows remain and none come from sheet 2, so exactly one copy is kept (`review_windows.dec2010_overlap_copies_identical` = true, `dec2010_dedup_leaves_one_copy` = true). Whole overlap: 22,523 rows, identical (§4 Duplicates). Aggregating without the overlap rule would double Dec 2010 (40,480 rows).
- **Negative quantities: all explained.** Across the dataset there are 22,557 negative rows: 19,164 cancellations and 3,393 price-0 stock adjustments, with `unexplained_negative_rows` = 0 (§5). In the windows: Dec 2011 has 360 cancellations and 30 stock adjustments, Dec 2010 has 261 and 48, Nov 2011 has 363 and 27. None are unexplained (`review_windows.unexplained_negative_rows_in_windows` = 0). None reach revenue.
- **Partial last day and weekday mix.** The data ends at 2011-12-09 12:50 (§8). All three windows use the same 12:50 cut-off on the 9th, so clock time is like-for-like. Each window has 8 trading days, and no Saturdays trade. The weekday mix differs. Dec 2011 covers Thu-Fri twice, Dec 2010 covers Wed-Thu twice and Nov 2011 covers Tue-Wed twice (§11). Dec 2011 must not be compared with full months (§8). We cannot tell whether trading after 12:50 on 9 Dec 2011 is missing or never happened.
- **Missing Customer ID.** Across the dataset, 13.1% of revenue (226,882 rows, £2,576,013) has no Customer ID (§3). In the windows: Dec 2011 £102,263 (7,789 rows, 16.6%), Dec 2010 £87,311 (6,467 rows, 23.0%) and Nov 2011 £88,232 (3,655 rows, 21.3%) (`review_windows.windows.*.revenue_no_customer`). This revenue counts toward the totals but must be left out of customer metrics. Reversal matching needs a Customer ID, so §10 and §11 reversal figures are lower bounds.
- **Cancellations and non-product items.** Product cancellations are Dec 2011 -£174,127 (348 rows, including C581484), Dec 2010 -£5,868 and Nov 2011 -£9,486 (`cancel_value_products`). AMAZONFEE credits appear in the windows (Dec 2011 C580604/C580605, -£29,423; Dec 2010 five C invoices plus 537632; Nov 2011 C574897/C574902). They are non-product codes and are excluded from revenue (§9, §11). The whole dataset holds 11,731 exact duplicate revenue lines worth £57,093 (0.3%), which the definition keeps. In the windows they are worth £1,002 (Dec 2011), £1,196 (Dec 2010) and £1,592 (Nov 2011) (§4, §11).
- **Other caveats.** In Dec 2009 (the first month) every customer looks new (§8). There are 127 revenue rows (£1,186) on DCGS*/SP1002 codes that stay in revenue (§9). Five A-invoice bad-debt rows (-£147,614) are excluded (§6). The other outlier in the dataset, 541431/C541433 (74,215 units, £77,184, Jan 2011), falls outside the review windows (§9, §10).
- **Fit for analysis: yes with caveats.** No FAILs. The overlap is removed correctly and all negative rows are explained. The Dec 2011 MTD comparison is invalid unless the review names the £168,469.60 reversed order 581483/C581484 and shows its effect. The review must also state the 12:50 cut-off and weekday mix, and keep no-Customer-ID revenue out of customer metrics.

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

## 11. Review windows (1-9 Dec 2011 / 1-9 Dec 2010 / 1-9 Nov 2011, to 12:50) (WARN)

Windows are inclusive, 00:00 on the 1st to 12:50 on the 9th (the last timestamp in the data is 2011-12-09 12:50). Approved revenue definition unchanged; the 'excl. reversed' column is a sensitivity only.

| window | rows (dedup) | revenue rows | revenue | no-customer revenue | trading days | neg rows | unexplained neg | reversed lines | reversed £ | revenue excl. reversed (sensitivity) |
|---|---|---|---|---|---|---|---|---|---|---|
| Dec 2011 MTD | 25,526 | 25,031 | £615,493 | £102,263 | 8 | 390 | 0 | 12 | £169,023 | £446,471 |
| Dec 2010 same window | 20,240 | 19,765 | £379,727 | £87,311 | 8 | 309 | 0 | 16 | £548 | £379,179 |
| Nov 2011 same window | 20,352 | 19,870 | £414,700 | £88,232 | 8 | 390 | 0 | 47 | £6,135 | £408,565 |

- Dec 2010 window vs sheet overlap: sheet 1 has 20,240 rows, sheet 2 has 20,240; identical as multisets: **True**. After deduplication 20,240 rows remain, 0 from sheet 2: exactly one copy kept: **True**.
- Weekdays covered: Dec 2011 MTD: Thu, Fri, Sun, Mon, Tue, Wed, Thu, Fri; Dec 2010 same window: Wed, Thu, Fri, Sun, Mon, Tue, Wed, Thu; Nov 2011 same window: Tue, Wed, Thu, Fri, Sun, Mon, Tue, Wed.
- Last day of each window (the 9th, to 12:50): Dec 2011 MTD: 1,633 rows, last 2011-12-09 12:50:00; Dec 2010 same window: 608 rows, last 2010-12-09 12:49:00; Nov 2011 same window: 898 rows, last 2011-11-09 12:49:00.
- Negative rows by kind: Dec 2011 MTD: {'cancellation': 360, 'stock adjustment': 30}; Dec 2010 same window: {'cancellation': 261, 'stock adjustment': 48}; Nov 2011 same window: {'cancellation': 363, 'stock adjustment': 27}.

Extreme lines in the windows (|Quantity| >= 1,000 or |line value| >= £2,000):

| window | Invoice | StockCode | Quantity | Price | line_value | InvoiceDate | Customer ID | in revenue | reversed |
|---|---|---|---|---|---|---|---|---|---|
| Dec 2011 MTD | 579936 | 21787 | 1,200 | 0.65 | 780.00 | 2011-12-01 10:07:00 | 12901 | 1 | 0 |
| Dec 2011 MTD | 580170 | 22197 | 1,000 | 0.72 | 720.00 | 2011-12-02 11:39:00 | 17949 | 1 | 0 |
| Dec 2011 MTD | 580243 | 21915 | 1,120 | 1.06 | 1,187.20 | 2011-12-02 12:19:00 | 16333 | 1 | 0 |
| Dec 2011 MTD | 580363 | 23582 | 1,500 | 1.79 | 2,685.00 | 2011-12-02 16:32:00 | 13868 | 1 | 0 |
| Dec 2011 MTD | C580604 | AMAZONFEE | -1 | 11,586.50 | -11,586.50 | 2011-12-05 11:35:00 |  | 0 | 0 |
| Dec 2011 MTD | C580605 | AMAZONFEE | -1 | 17,836.46 | -17,836.46 | 2011-12-05 11:36:00 |  | 0 | 0 |
| Dec 2011 MTD | 580610 | DOT | 1 | 2,196.67 | 2,196.67 | 2011-12-05 11:48:00 |  | 0 | 0 |
| Dec 2011 MTD | 580612 | DOT | 1 | 2,114.00 | 2,114.00 | 2011-12-05 11:58:00 |  | 0 | 0 |
| Dec 2011 MTD | 581107 | 23461 | 620 | 3.30 | 2,046.00 | 2011-12-07 12:15:00 | 16000 | 1 | 0 |
| Dec 2011 MTD | 581110 | 23486 | 150 | 13.35 | 2,002.50 | 2011-12-07 12:17:00 | 16000 | 1 | 0 |
| Dec 2011 MTD | 581115 | 22413 | 1,404 | 2.75 | 3,861.00 | 2011-12-07 12:20:00 | 15195 | 1 | 0 |
| Dec 2011 MTD | 581175 | 23084 | 1,440 | 1.79 | 2,577.60 | 2011-12-07 15:16:00 | 14646 | 1 | 0 |
| Dec 2011 MTD | 581212 | 22578 | -1,050 | 0.00 | -0.00 | 2011-12-07 18:38:00 |  | 0 | 0 |
| Dec 2011 MTD | 581375 | 21137 | 960 | 3.39 | 3,254.40 | 2011-12-08 12:36:00 | 16210 | 1 | 0 |
| Dec 2011 MTD | 581457 | 23543 | 698 | 4.15 | 2,896.70 | 2011-12-08 18:43:00 | 18102 | 1 | 0 |
| Dec 2011 MTD | 581458 | 22197 | 1,500 | 0.72 | 1,080.00 | 2011-12-08 18:45:00 | 17949 | 1 | 0 |
| Dec 2011 MTD | 581459 | 22197 | 1,200 | 0.72 | 864.00 | 2011-12-08 18:46:00 | 17949 | 1 | 0 |
| Dec 2011 MTD | 581483 | 23843 | 80,995 | 2.08 | 168,469.60 | 2011-12-09 09:15:00 | 16446 | 1 | 1 |
| Dec 2011 MTD | C581484 | 23843 | -80,995 | 2.08 | -168,469.60 | 2011-12-09 09:27:00 | 16446 | 0 | 0 |
| Dec 2010 same window | C536757 | 84347 | -9,360 | 0.03 | -280.80 | 2010-12-02 14:23:00 | 15838 | 0 | 0 |
| Dec 2010 same window | 536809 | 84950 | 1,824 | 0.55 | 1,003.20 | 2010-12-02 16:48:00 | 15299 | 1 | 0 |
| Dec 2010 same window | 536830 | 84077 | 2,880 | 0.18 | 518.40 | 2010-12-02 17:38:00 | 16754 | 1 | 0 |
| Dec 2010 same window | 536830 | 21915 | 1,400 | 1.06 | 1,484.00 | 2010-12-02 17:38:00 | 16754 | 1 | 0 |
| Dec 2010 same window | 536890 | 17084R | 1,440 | 0.16 | 230.40 | 2010-12-03 11:48:00 | 14156 | 1 | 0 |
| Dec 2010 same window | C537630 | AMAZONFEE | -1 | 13,541.33 | -13,541.33 | 2010-12-07 15:04:00 |  | 0 | 0 |
| Dec 2010 same window | 537632 | AMAZONFEE | 1 | 13,541.33 | 13,541.33 | 2010-12-07 15:08:00 |  | 0 | 0 |
| Dec 2010 same window | C537644 | AMAZONFEE | -1 | 13,474.79 | -13,474.79 | 2010-12-07 15:34:00 |  | 0 | 0 |
| Dec 2010 same window | C537647 | AMAZONFEE | -1 | 5,519.25 | -5,519.25 | 2010-12-07 15:41:00 |  | 0 | 0 |
| Dec 2010 same window | C537651 | AMAZONFEE | -1 | 13,541.33 | -13,541.33 | 2010-12-07 15:49:00 |  | 0 | 0 |
| Dec 2010 same window | C537652 | AMAZONFEE | -1 | 6,706.71 | -6,706.71 | 2010-12-07 15:51:00 |  | 0 | 0 |
| Dec 2010 same window | 537657 | 22189 | 972 | 2.31 | 2,245.32 | 2010-12-07 16:42:00 | 18102 | 1 | 0 |
| Dec 2010 same window | 537657 | 22188 | 972 | 2.31 | 2,245.32 | 2010-12-07 16:42:00 | 18102 | 1 | 0 |
| Dec 2010 same window | 537657 | 21623 | 408 | 6.38 | 2,603.04 | 2010-12-07 16:42:00 | 18102 | 1 | 0 |
| Dec 2010 same window | 537659 | 22189 | 1,008 | 2.31 | 2,328.48 | 2010-12-07 16:43:00 | 18102 | 1 | 0 |
| Dec 2010 same window | 537659 | 22188 | 1,008 | 2.31 | 2,328.48 | 2010-12-07 16:43:00 | 18102 | 1 | 0 |
| Dec 2010 same window | 537659 | 21623 | 600 | 6.38 | 3,828.00 | 2010-12-07 16:43:00 | 18102 | 1 | 0 |
| Dec 2010 same window | 537659 | 82484 | 600 | 4.78 | 2,868.00 | 2010-12-07 16:43:00 | 18102 | 1 | 0 |
| Dec 2010 same window | 537659 | 22833 | 72 | 32.69 | 2,353.68 | 2010-12-07 16:43:00 | 18102 | 1 | 0 |
| Dec 2010 same window | 537841 | 16014 | 1,000 | 0.32 | 320.00 | 2010-12-08 15:10:00 | 13848 | 1 | 0 |
| Dec 2010 same window | 537899 | 22328 | 1,488 | 2.55 | 3,794.40 | 2010-12-09 10:44:00 | 12755 | 1 | 0 |
| Dec 2010 same window | 537981 | 22492 | 1,394 | 0.55 | 766.70 | 2010-12-09 11:35:00 | 17857 | 1 | 0 |
| Nov 2011 same window | 573995 | 16014 | 3,000 | 0.32 | 960.00 | 2011-11-02 11:24:00 | 16308 | 1 | 0 |
| Nov 2011 same window | 574293 | 85123A | 992 | 3.20 | 3,174.40 | 2011-11-03 15:32:00 | 17450 | 1 | 0 |
| Nov 2011 same window | 574294 | 22086 | 1,020 | 2.55 | 2,601.00 | 2011-11-03 15:47:00 | 16333 | 1 | 0 |
| Nov 2011 same window | 574294 | 21915 | 2,100 | 1.06 | 2,226.00 | 2011-11-03 15:47:00 | 16333 | 1 | 0 |
| Nov 2011 same window | 574816 | 85036C | -1,560 | 0.00 | -0.00 | 2011-11-07 10:37:00 |  | 0 | 0 |
| Nov 2011 same window | 574822 | 85036B | -1,284 | 0.00 | -0.00 | 2011-11-07 10:38:00 |  | 0 | 0 |
| Nov 2011 same window | C574897 | AMAZONFEE | -1 | 5,877.18 | -5,877.18 | 2011-11-07 15:03:00 |  | 0 | 0 |
| Nov 2011 same window | C574902 | AMAZONFEE | -1 | 8,286.22 | -8,286.22 | 2011-11-07 15:21:00 |  | 0 | 0 |
| Nov 2011 same window | 574941 | 23344 | 484 | 4.95 | 2,395.80 | 2011-11-07 17:42:00 |  | 1 | 0 |
| Nov 2011 same window | 574941 | 23084 | 628 | 4.95 | 3,108.60 | 2011-11-07 17:42:00 |  | 1 | 0 |
| Nov 2011 same window | 574941 | 22197 | 1,820 | 1.95 | 3,549.00 | 2011-11-07 17:42:00 |  | 1 | 0 |
| Nov 2011 same window | 574941 | 22086 | 478 | 6.95 | 3,322.10 | 2011-11-07 17:42:00 |  | 1 | 0 |

Largest revenue lines in the windows reversed by the same customer within 24h (check 10 rule):

| window | Invoice | Invoice_c | StockCode | Quantity | value | minutes | cancel after window end |
|---|---|---|---|---|---|---|---|
| Dec 2011 MTD | 581483 | C581484 | 23843 | 80,995 | 168,469.60 | 12.00 | 0 |
| Dec 2011 MTD | 580704 | C580702 | 23494 | 40 | 238.00 | 0.00 | 0 |
| Dec 2011 MTD | 580169 | C580171 | 23108 | 24 | 81.36 | 4.00 | 0 |
| Dec 2011 MTD | 580175 | C580174 | 20961 | 50 | 62.50 | 0.00 | 0 |
| Dec 2011 MTD | 580128 | C580131 | 85034C | 12 | 51.00 | 16.00 | 0 |
| Dec 2010 same window | 537410 | C537413 | 22834 | 72 | 151.20 | 4.00 | 0 |
| Dec 2010 same window | 537609 | C537611 | 22865 | 36 | 75.60 | 3.00 | 0 |
| Dec 2010 same window | 537217 | C537402 | 22849 | 4 | 59.80 | 1,383.00 | 0 |
| Dec 2010 same window | 537217 | C537402 | 22847 | 4 | 59.80 | 1,383.00 | 0 |
| Dec 2010 same window | 537144 | C537157 | 35953 | 24 | 30.00 | 9.00 | 0 |
| Nov 2011 same window | 574319 | C574584 | 82486 | 24 | 195.60 | 1,376.00 | 0 |
| Nov 2011 same window | 574319 | C574584 | 82483 | 32 | 190.40 | 1,376.00 | 0 |
| Nov 2011 same window | 574319 | C574584 | 82482 | 72 | 183.60 | 1,376.00 | 0 |
| Nov 2011 same window | 574319 | C574584 | 72802C | 180 | 180.00 | 1,376.00 | 0 |
| Nov 2011 same window | 574319 | C574584 | 85036C | 180 | 180.00 | 1,376.00 | 0 |
