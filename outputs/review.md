# Review: December 2011 month-to-date business review (pre-leadership)

Reviewer: reviewer agent, 2026-09-27. This replaces the earlier FY review, which is still in git history (`git show HEAD:outputs/review.md`).

**What I reviewed:**
- `outputs/mbr_2011_12/executive_report.md`
- `outputs/mbr_2011_12/metrics.json` and the six CSVs
- the four charts in `outputs/mbr_2011_12/charts/`
- `scripts/mbr_analysis.py`, `scripts/retail_common.py` and `anomaly_tables` in `scripts/retail_analysis.py`
- `outputs/data_quality_report.md` §11 and the new check 11 in `scripts/data_quality.py`

**Evidence:** `scripts/review_recheck.py`, section "MBR Dec 2011 month-to-date recheck", run with `.venv/bin/python`. I appended this section; the existing FY checks still run and still match. The script is an independent pandas implementation of the CLAUDE.md definition and imports no project script. Its output quoted below is labelled `recheck: <key>`.

**Recheck assumptions:**
- **Windows.** Inclusive at both ends: [1st 00:00, 9th 12:50] for Dec 2011, Dec 2010 and Nov 2011.
- **Sheet overlap.** Drop rows with `source_sheet == "Year 2010-2011"` dated on or before 2010-12-09 20:01.
- **Revenue.** Quantity × Price over rows that are not C or A invoices, have Quantity > 0 and Price > 0, and are not on the non-product list or `gift_0001_*`.
- **Cancellations.** Cancellation value = −Σ(Q×P) over C rows on product codes, after the overlap rule. Rate = value / (revenue + value), which is the report's stated basis.
- **Orders and customers.** Order = distinct revenue invoice. Customers = distinct Customer IDs on revenue rows.
- **New and returning.** "New (all history)" means no revenue row before the window starts. "New (12m)" means no revenue row in the 12 months before the window starts. Returning = customers − new, under each definition.
- **Reversed order.** Invoice 581483 as it appears in the data, paired with C581484 (same customer 16446, same code 23843, −80,995 units, 12 minutes later). My broader cross-check matches same customer, code, opposite quantity and same price within 24h, at any size.

## Verdict: **ready after fixes**

All 40+ numbers I recomputed match to rounding: every scorecard value, the UK, international and Netherlands revenue, and the reversal. The definitions are implemented correctly. The headline keeps the approved definition (£615K), and the reversal appears only as a labelled sensitivity.

Three claims do not hold and must be fixed before leadership sees the report:
- one false superlative in the Bottom line;
- an inconsistent "returning customers" figure;
- an unsupported "not from new customers" attribution.

## Definitions check

| Rule (CLAUDE.md) | `retail_common.py` / `mbr_analysis.py` | OK |
|---|---|---|
| Overlap: drop 2010-2011 copies dated on or before 2010-12-09 20:01 | `is_overlap_copy = sheet == "Year 2010-2011" & InvoiceDate <= 2010-12-09 20:01` | yes |
| C and A excluded | `is_cancel`, `is_bad_debt` in `REVENUE_STEPS` | yes |
| Quantity > 0 and Price > 0 | `(Quantity <= 0) \| (Price <= 0)` removed | yes |
| Non-product list incl. `gift_0001_*` | all 18 codes, plus `str.startswith("gift_0001_")` | yes |
| Does not use `scripts/analyze_business.py` | only its chart colour tokens are mentioned in a comment; no import | yes |
| Dec 2010 window counted once | recheck: both sheets have 20,240 rows in the window and are identical as multisets (checked independently); DQ §11 agrees | yes |

## Recheck table

| Metric | Reported | Source | Recomputed | Match |
|---|---|---|---|---|
| Revenue Dec 11 / Dec 10 / Nov 11 | £615,493.27 / £379,727.00 / £414,699.81 | `revenue` | 615,493.27 / 379,727.00 / 414,699.81 | yes |
| Revenue growth vs LY / vs LM | +62.1% / +48.4% | `revenue` | +62.09% / +48.42% | yes |
| Orders | 816 / 766 / 718 | `orders` | 816 / 766 / 718 | yes |
| AOV (reported basis) | £754 / £496 / £578 | `aov` | 754.28 / 495.73 / 577.58 | yes |
| AOV excl. reversed | £548 (+10.6%, −5.0%) | `aov_excl_reversed` | 548.50 (+10.64%, −5.04%) | yes |
| Active customers | 614 / 534 / 574 | `customers` | 614 / 534 / 574 | yes |
| Cancellation rate (reported basis) | 22.1% / 1.5% / 2.2% | `cancel_rate` | 22.05% / 1.52% / 2.24% | yes |
| Cancellation rate excl. reversed | 1.3% | `cancel_rate_excl_reversed` | 1.25% | yes |
| UK revenue | £572,283 / £348,895 / £380,888 | `uk_revenue` | 572,282.68 / 348,894.56 / 380,887.54 | yes |
| UK excl. reversed, growth vs LY | £404K, +15.7% | `uk_revenue_excl_reversed` | 403,813.08, +15.74% | yes |
| International revenue | £43,211 / £30,832 / £33,812 (+40%) | `international_revenue` | 43,210.59 / 30,832.44 / 33,812.27 (+40.15%) | yes |
| Netherlands revenue | £11.7K vs £178, all from 14646 | `countries.csv` | 11,728.02 (one customer, 14646, 3 invoices) vs 177.60 (customer 12791); Nov 11: 4,486.91 | yes |
| International excl. NL | £31.5K vs £30.7K, +2.7% | `countries.csv` | 31,482.57 vs 30,654.84, +2.70% | yes |
| Reversed order 581483 | £168,469.60, 27% of revenue, cancelled 12 min later | `reversals.csv` | 168,469.60; 27.37%; C581484 at 09:27 | yes |
| Revenue excl. reversed | £447,024, +17.7% / +7.8% | `revenue_excl_reversed` | 447,023.67; +17.72% / +7.79% | yes |
| Broad 24h any-size sensitivity | £446,471 vs £379,179 | DQ §11 | 446,470.71 vs 379,179.05 (Nov 11: 408,565.13) | yes |
| Cumulative to end of 8 Dec | £417K vs £359K (+16.2%) | `daily.csv` | 417,379.01 vs 359,196.05 (+16.20%) | yes |
| First-9-days YoY, Oct / Nov | +1.3% / +2.2% | `mtd_trend.csv` | +1.3% / +2.2% | yes |
| Returning customers | 586 vs 489 (+19.8%) | `returning_customers` | all-history 586 vs 489; **12-month basis 573 vs 489 (+17.2%)** | number yes; **definition no** (Issue 2) |
| New customers, 12m look-back | 41 / 45 / 81 | `new_customers_12m_lookback` | 41 / 45 / 81 | yes |
| Unidentified revenue | £102K vs £87K (+17%), "about 23%" | DQ §11, `unidentified_revenue_share` | 102,262.84 vs 87,311.20 (+17.1%); **16.6% of reported**, 22.9% of excl.-reversed | amount yes; **cited share no** (Issue 4) |
| Top-10 share of identified revenue | 47.1%; 22.3% excl. vs 25.3% | `top10_*` | 22.34% excl.; 25.32% | yes |
| Customer 16000 | £12.4K, new | `customers.csv` | 12,393.70; first purchase 2011-12-07 12:14 | yes |
| FY1 / FY2 / growth (cited FY context) | +2.4%; +1.2% excl. reversed | `outputs/analysis/metrics.json` | FY1 9,429,521.38; FY2 9,655,939.79; +2.40%; +1.17% | yes |
| Total revenue / top country (FY review regression) | £19,700,954; UK | `outputs/analysis/metrics.json` | 19,700,954.44; United Kingdom £16,856,331 | yes |

## Issues

### 1. *Blocking*: "strongest year-on-year gain in the first nine days of any month in the data" is false
- **Where:** Bottom line, third sentence. Change #1 builds on the same framing: "against about +2% in Oct and Nov … December is a clear step-up".
- **Evidence:** `recheck: MBR first-9-days … YoY` gives Sep 2011 **+22.0%** (£230,774 vs £189,183) and Aug 2011 **+19.3%** (£197,907 vs £165,881). Both windows have 8 trading days in each year, and neither contains a reversed order. Dec 2011's +17.7% ranks third. `mtd_trend.csv` in the report's own evidence set contains the same numbers, and chart 2 shows them visibly.
- **Why it matters:** first-9-days YoY over the last 13 months runs from −15.5% (Mar) to +22.0% (Sep). A single +17.7% sits inside that range. The step-up from +1-2% in Oct-Nov is real, but it is a return to the Aug-Sep level, not an unprecedented jump. Calling it "clear" overstates the evidence from 8 trading days.
- **Fix:** delete the superlative. Reword change #1, for example: "+17.7%, after +1-2% in Oct-Nov and +19-22% in Aug-Sep on the same first-9-days basis. The first-9-days comparison is volatile (−15% to +22% over the last year)."
- **Owner:** business-analyst (report author).

### 2. *Blocking*: "returning" customers mix two look-back definitions (586 vs 489 should be 573 vs 489)
- **Where:** Change #2: "all of it from customers who had bought before: 586 vs 489 (+19.8%). New customers, measured the same way in both years (no purchase in the prior 12 months), were 41 vs 45."
- **Evidence:**
  - `returning_customers` is `customers − new_customers` under the all-history definition (`mbr_analysis.py`, `window_metrics`). Dec 2011 has 24 months of history and Dec 2010 only 12 (`metrics.json` → `assumptions`).
  - 586 + 41 = 627, not 614.
  - `recheck: mbr_Dec11_returning_12` = 573 and `mbr_Dec11_reactivated` = 13. So 13 customers are counted as both "returning" and "new".
  - On the like-for-like 12-month basis, returning is 573 vs 489, **+17.2%**, not +19.8%. Nov 2011 also shifts: 493, not 516.
- **Fix:**
  - Report 573 vs 489 (+17.2%), or show both bases with labels.
  - In `mbr_analysis.py`, add `returning_customers_12m_lookback`, or recompute `returning_customers` on the 12-month basis.
  - Also align `new_customer_revenue_share_of_identified`, which still uses the all-history "new".
- **Owner:** customer-analyst for the definition, business-analyst for the report text.

### 3. *Blocking*: "The gain comes from more returning customers ordering, not from new ones" is not supported for revenue
- **Where:** Bottom line, fourth sentence. Change #2 heading.
- **Evidence** (recheck, excluding 581483, 12-month basis):
  - New-customer revenue rose from £12,091 to **£26,712 (+121%)**. That is 28% of the £52,345 gain in identified revenue (`mbr_new12_share_of_identified_gain_x`).
  - Returning-customer revenue rose 13.5% (£280,325 → £318,048).
  - A further **£14,952 of the £67,297 total gain (22%) is unidentified revenue**, which cannot be attributed to new or returning customers at all.
  - The customer-count statement is correct: returning +84, new −4. Revenue is a different matter: returning customers explain about 56% of the gain, new customers about 22% (one new account, 16000, gives £12.4K), and unidentified revenue the rest.
- **Fix:** separate counts from revenue. For example: "Customer growth is all returning accounts (573 vs 489). Of the £67K revenue gain, about £38K came from returning customers, £15K from new customers (mostly one account, 16000) and £15K from orders without a Customer ID."
- **Owner:** business-analyst / customer-analyst.

### 4. *Should fix*: Risk 3's "about 23%" does not match the metric it cites
- **Where:** Risk 3 heading and text. Cites `unidentified_revenue_share`.
- **Evidence:** `unidentified_revenue_share.current` = **0.1661 (16.6%)**, because it is measured against reported revenue. The 23% is £102,263 / £447,024 = 22.9% (`recheck: mbr_Dec11_unident_share_x`), which appears in no metric. The Dec 2010 figure is 23.0% on either basis.
- **Fix:** state the basis, e.g. "16.6% of reported revenue, 22.9% excluding the reversed order". Alternatively, add an `unidentified_revenue_share_excl_reversed` metric and cite that.
- **Owner:** business-analyst.

### 5. *Should fix*: wrong section cited for the Oct-Nov full-year growth
- **Where:** Risk 2: "The full-year peak (Oct-Nov) grew only 0.8-1.5% (`business_analysis.md` §4)".
- **Evidence:** `outputs/business_analysis.md` §4 is "Products". The +0.8% and +1.5% are in §3, lines 69-74, and key finding 5.
- **Fix:** change the citation to §3.
- **Owner:** business-analyst.

### 6. *Should fix*: the small base is acknowledged, but the gain's concentration is not shown
- **Where:** Risk 2 and change #1.
- **Evidence:** two accounts give £24.1K of the £67.3K gain, or 36%:
  - 16000 is new: £12,394 (`customers.csv`).
  - 14646 bought nothing in the Dec 2010 window: £11,728 (recheck; Netherlands Dec 2010 revenue is customer 12791 only).
- **Fix:** add one sentence to Risk 2 so leadership can judge how fragile the +17.7% is.
- **Owner:** business-analyst.

### 7. *Should fix*: the weekday-mix difference is mentioned but its effect is not assessed
- **Where:** the note under the scorecard ("They start on different weekdays").
- **Evidence** (`daily.csv`, recheck daily):
  - All three windows have one Sunday and 7 weekday trading days, but the partial 9th falls on different weekdays: a Friday in Dec 2011 (£29.6K excluding the reversal) and a Thursday in Dec 2010 (£20.5K). That +£9.1K is 14% of the gain.
  - Dec 2011 has two Fridays and two Thursdays; Dec 2010 has two Wednesdays and two Thursdays.
  - The to-8-Dec comparison (7 full trading days each, +16.2%) already shows most of the gain survives. The report should say that this is why it is quoted.
  - Weekday effects on the full days cannot be separated with 8 days of data. Say so rather than leave it implicit.
- **Owner:** business-analyst.

### 8. *Should fix*: chart labels
- **Chart 2** (`02_mtd_window_trend.png`): the "£415K" label on Nov 11 is overprinted by the black "excl. reversed" marker and the "£447K" label. Move one of them.
- **Chart 4** (`04_markets.png`): the subtitle "UK (not shown): £572K vs £349K" includes the reversed £168K without saying so, while charts 1 and 3 do call it out. Add "(£404K excl. the reversed order)".
- **Chart 1** (`01_mtd_cumulative_revenue.png`): the subtitle "dashed line removes orders cancelled after the sale" overstates the rule. It removes only reversed lines of £5K or more (one order). £553 of smaller 24h reversals stays in, per DQ §11. Reword to "removes the reversed order 581483".
- **Charts 1 and 3:** titles and values match the data. Chart 3's product bars match `products.csv`.
- **Owner:** business-analyst (`mbr_analysis.py` `charts()`).

### 9. *Note*: "same rule as `scripts/retail_analysis.py`" for reversals
- **Where:** Basis and caveats.
- **What's wrong:** `mbr_analysis.py` uses every `anomaly_tables` match of £5K or more at any lag. The FY sensitivity in `retail_analysis.py` keeps only `within_24h`. In these windows the only match is 581483 (0.2h), so no number changes, but the two rules are not the same.
- **Fix:** filter on `within_24h` or reword the caveat.

### 10. *Note*: active customers include the reversed order's customer
- **What's wrong:** 16446's only purchase in the window is the reversed line (`customers.csv`: revenue_excl_reversed = 0). Excluding it gives 613 customers (+14.8%), not 614. Immaterial, but the scorecard mixes "excl. reversed" rows with a customer count that includes the reversal.

### 11. *Note*: "about flat" international hides a mix shift
- **What's wrong:** excluding the Netherlands, the top-7 other markets rose, while the long tail fell from £10.0K to £3.3K (chart 4 "All other"; Japan £4.1K and Lithuania £1.7K in Dec 2010, none in Dec 2011). The +2.7% net figure is correct.

### 12. *Note*: wording details in change #2 and change #3
- **Customer 16000's "first week":** the account's first purchase was on 7 Dec, so this was its first 2 days.
- **Customer 14646's "3 orders":** these are this window's invoices, not lifetime orders. The account also accounts for all of the £4.5K Netherlands revenue in the Nov window, which bears on leadership question 3.

### 13. *Note*: data-quality §11 and the new check
- **Code:** check 11 in `scripts/data_quality.py` is sound. Windows are inclusive, the multiset comparison of the Dec 2010 copies is correct, and negative rows are classified before interpretation.
- **Figures:** the §11 figures I recomputed match: revenue, no-customer revenue, broad reversal totals of £169,023 / £548 / £6,135, and the excl.-reversed values.
- **Label:** "stock adjustment" is an inference from Price = 0 on a non-C negative row. That is reasonable, but it is a label, not a field in the data.
- **Missing sign-off:** the DQ analyst note's question (report revenue as defined, or net out 24h reversals) is the same as leadership question 1 and still has no answer.

## What is fine

- The headline keeps the approved definition: £615K and +62% come first. Every "excl. reversed" figure is labelled a sensitivity, and the definition change is escalated to leadership rather than applied.
- The comparison is not with a full month: all three windows are like-for-like to 12:50 on the 9th.
- The Dec 2010 window is counted once (verified independently).
- Negative quantities are classified before use: 0 unexplained (DQ §11).
- Unidentified revenue is excluded from customer metrics, and the report says so.
- Apart from Issues 4 and 5, every number in the report traces to a cited metric key or CSV.

## Open questions for the user

1. **Revenue net of same-day reversals.** Should management reporting net out same-day reversals? This would change the approved definition. Until you decide, the report correctly shows both figures.
2. **Customer look-back.** Which look-back should the business use for "new" and "returning": 12 months, like-for-like across years, or all history? The answer decides whether 586 or 573 is the returning figure going forward.
3. **Leadership questions 2-4.** The report's questions on the December promotion or timing, account 14646 and the channel behind orders without a Customer ID cannot be answered from this dataset and need business input.
