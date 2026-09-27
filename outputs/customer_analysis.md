# Customer Analysis: Online Retail II

Generated 2026-09-27 by `scripts/customer_analysis.py` (run with `.venv/bin/python scripts/customer_analysis.py`). Evidence tables are in `outputs/customers/`, and headline metrics with definitions are in `outputs/customers/customer_metrics.json` (metric keys are shown in `code`). Input: `data/processed/online_retail_II.csv`. Nothing in `data/` was changed. Data-quality verdict: **fit for analysis with caveats** (`outputs/data_quality_report.md`, no FAILs). Revised the same day to apply the corrections in [`review.md`](review.md).

## 1. Scope and assumptions

These assumptions are stated before any metric is calculated. They are also in the script docstring and in `customer_metrics.json` → `assumptions`.

- **Revenue** follows the approved CLAUDE.md definition (total £19,700,954, `revenue_total`). C invoices (cancellations) and A invoices (bad-debt adjustments) are never counted as revenue.
- **Scope:** only approved-revenue rows that have a Customer ID. Rows without one make up **13.1% of revenue** (£2,576,013, `revenue_share_without_customer_id`) and are excluded. That leaves £17,124,941 of identified revenue (`revenue_identified`). **Customer totals therefore do not reconcile to total revenue.** 23 Customer IDs have cancellations but no approved revenue, so they are outside RFM (`customers_cancel_only`).
- **Monetary (M)** = gross approved revenue per customer. Cancellations are never netted in. Each customer's cancelled product value is reported separately (`cancel_value` and `cancel_rate` in `customers_rfm.csv`; £711,604 in total across customers, `customer_cancel_value`).
- **Frequency (F)** = distinct purchase days, so split invoices on the same day count once. This matches the project's repeat-customer definition. Distinct invoices are kept as `invoices`.
- **Recency (R)** = days from the last purchase day to a **snapshot of 2011-12-10**, the day after the last invoice. Dec 2011 is partial (1-9 Dec, 8 trading days) and is never treated as a full month.
- **Scoring:** R, F and M are scored 1-5 by quintile of percentile rank. Tied values share a score, and the most recent customers get R = 5. F is heavily tied (28.6% of customers bought on only one day), so F=1 is exactly 1 day, F=2 is 2 days, F=3 is 3 days, F=4 is 4-7 days and F=5 is 8 or more (`rfm_score_bounds.csv`).
- **Segments** come from an ordered rule table where the first match wins (`rfm_segment_rules.csv`):

  | order | segment | rule |
  |---|---|---|
  | 1 | Champions | R>=4 and F>=4 and M>=4 |
  | 2 | Loyal | R>=3 and F>=3 |
  | 3 | Big spenders | R>=3 and M>=4 (F<=2) |
  | 4 | New | R>=4 and F=1 |
  | 5 | Can't lose | R<=2 and F>=4 and M>=4 |
  | 6 | At risk | R<=2 and (F>=3 or M>=3) |
  | 7 | Need attention | R>=3, low F and M |
  | 8 | Hibernating | everything else (R<=2, F<=2, M<=2) |

- **Country:** each customer gets one country, the one on most of their revenue lines (ties go alphabetically). 12 customers have revenue lines in more than one country (`customers_multi_country`, `multi_country_customers.csv`). The data-quality report counts 13 because it also includes cancellation rows.
- **Usual gap** = the median number of days between a customer's consecutive purchase days. It needs 2 or more purchase days.
- **High-value at risk:** the customer is in the top 20% by monetary (1,170 customers, M ≥ £2,900), has 2 or more purchase days, and has recency > **2 ×** their usual gap **and** > **90 days**. These are the constants `TOP_VALUE_SHARE`, `GAP_MULTIPLE` and `MIN_RECENCY_DAYS`. High-value one-day buyers have no usual gap, so they are counted separately.
- **Distortion checks** (column `distortion_flags`):
  - Reversed sales: revenue lines cancelled by the same customer within 24h. This is the data-quality rule, and it matches 1,444 lines worth £403,195 (`reversed_lines`, `reversed_value_identified`).
  - Large orders reversed later: `outputs/analysis/anomaly_reversed_orders.csv`.
  - Single-order-dominated customers: largest purchase day ≥ 50% of monetary and ≥ £5,000.
  - High cancellation rate: ≥ 25%.
  - `starts_dec2009`: the customer's history is cut off at the start of the data.

  The approved definition keeps reversed sales in revenue, so they stay in M. Every at-risk figure and concentration figure also has a view with reversed sales removed. **Scope:** in this report "excl. reversed" always means all 1,444 lines reversed by the same customer within 24h (£403,195). `business_analysis.md` uses only the three £5k+ same-day reversals (£284,623) for its revenue sensitivity line.
- **Cohort baseline:** customers first seen in Dec 2009 (951, `customers_starting_dec2009`) are a baseline, not acquisitions. Repeat-within-N-days metrics only use customers first seen from 2010-01-01 who had at least 180 days of observation before the snapshot (4,006 customers).

## 2. Customer base and concentration

| KPI | value | evidence |
|---|---|---|
| Customers with approved revenue | 5,852 | `customers` |
| Identified revenue | £17,124,941 (86.9% of total) | `revenue_identified` |
| Median / mean revenue per customer | £860 / £2,926 | `monetary_median`, `monetary_mean` |
| Top 1% (59 customers) share of identified revenue | 32.0% (31.2% excl. all 1,444 reversed lines) | `top_1pct_customer_share`, `top_1pct_share_excl_reversed` |
| Top 10% (585) share | 63.8% | `top_10pct_customer_share` |
| Top 20% (1,170) share | 77.1% | `top_20pct_customer_share` |
| Repeat customers (2+ purchase days) | 71.4% of customers, 96.2% of identified revenue | `repeat_customer_rate`, `repeat_customer_revenue_share` |

These figures reconcile with `outputs/analysis/metrics.json`: customers 5,852, `top_10pct_customer_share` 0.6378, `repeat_customer_rate` 0.7141 and `median_days_between_purchases` 79.7, which is reproduced as `median_mean_gap_days`. Source tables: `concentration.csv`, `repeat_bands.csv`.

**Top-customer distortions** (`top_customers.csv`, `reversed_by_customer.csv`):
- Customer **16446** ranks #8 at £168,473, but £168,470 of that is invoice 581483, reversed 12 minutes later on 2011-12-09. Their real value is £3.
- Customer **12346** ranks #19 at £77,353. Of that, £77,184 is invoice 541431, reversed within 16 minutes, leaving £169.
- Customer **15098** ranks #40 at £39,917. Of that, £39,267 was reversed: £38,970 on invoice 556444 (by the manual `M` line C556445) and £297 on invoice 556442 (by C556448).
- In total, 5 customers leave the top 20% once reversed sales are removed (`top20_changed_by_reversals`).
- 15 top-20% customers are single-order dominated (`customers_single_order_dominated_top20`).
- 40.1% of top-20% customers were first seen in Dec 2009 (`top20_share_starting_dec2009`). Their true lifetime value is understated, not overstated.

## 3. RFM segments

Source: `rfm_segments.csv`. The £ figures are gross identified revenue over the whole period.

| segment | customers | % customers | revenue £ | % identified revenue | avg recency (days) | avg purchase days | avg £ | avg R | avg F | avg M |
|---|---|---|---|---|---|---|---|---|---|---|
| Champions | 1,321 | 22.6% | 11,744,645 | 68.6% | 20 | 14.7 | 8,891 | 4.57 | 4.68 | 4.63 |
| Loyal | 1,202 | 20.5% | 2,357,106 | 13.8% | 75 | 5.5 | 1,961 | 3.56 | 3.83 | 3.45 |
| Big spenders | 85 | 1.5% | 412,549 | 2.4% | 61 | 1.8 | 4,854 | 3.78 | 1.78 | 4.22 |
| New | 240 | 4.1% | 72,961 | 0.4% | 30 | 1.0 | 304 | 4.30 | 1.00 | 1.53 |
| Can't lose | 252 | 4.3% | 969,584 | 5.7% | 344 | 7.2 | 3,848 | 1.73 | 4.28 | 4.33 |
| At risk | 702 | 12.0% | 890,162 | 5.2% | 386 | 2.8 | 1,268 | 1.61 | 2.64 | 3.09 |
| Need attention | 665 | 11.4% | 312,096 | 1.8% | 75 | 1.6 | 469 | 3.57 | 1.64 | 2.00 |
| Hibernating | 1,385 | 23.7% | 365,837 | 2.1% | 461 | 1.2 | 264 | 1.41 | 1.23 | 1.43 |

Reading notes:
- **Big spenders is half made of reversed sales.** £207,781 of its £412,549 comes from reversed sales, almost all of it from customers 16446 and 15098 (column `reversed_value`). Without them the segment is about £205k.
- **Can't lose** (252 customers, £969,584) contains former frequent, high-value buyers. 38% of them started in Dec 2009, so they are long-standing accounts that have gone quiet. Their average recency is 344 days.
- **New** reflects first purchases in roughly the last 60 days, which falls in the Q4 2011 peak (R ≥ 4 means recency of 59 days or less).

## 4. High-value customers at risk

Definition from section 1: top 20% by monetary, 2+ purchase days, recency > 2 × usual gap and > 90 days. Source: `high_value_at_risk.csv`.

The **lead figures are the right-hand column**: ranking the top 20% without reversed sales removes customer 12346, whose FY2 revenue is almost entirely the £77,184 order 541431 cancelled 16 minutes later (23% of the gross FY2 figure).

| measure | top 20% ranked excl. reversed sales (lead) | default rule on gross M | evidence |
|---|---|---|---|
| Customers meeting the at-risk rule | **150** | 151 (12.9% of the top 20%) | `high_value_at_risk_customers_excl_reversed`, `high_value_at_risk_customers` |
| Lifetime revenue of these customers | £1,123,018 | £1,204,188 (£1,109,583 net of their reversed sales) | `..._excl_reversed_basis`, `high_value_at_risk_monetary` |
| FY2 revenue from these customers (upper bound if all were lost) | **£263,703** | £339,546 | `..._revenue_FY2_excl_reversed_basis`, `high_value_at_risk_revenue_FY2` |

The FY2 figure is not revenue "at stake": it assumes every one of these customers is lost, yet 112 of the 151 still bought in FY2, and their last-365-day revenue is £311,825 on the gross basis (`default_at_risk_row`). The rule is a threshold, not a churn prediction, and the count ranges from 27 to 207 depending on thresholds (see below).
| Of which with a distortion flag other than Dec-2009 start | 23 | | `high_value_at_risk_flagged` |

- 136 of the 151 are UK customers.
- By RFM segment: 79 are Can't lose, 54 Loyal and 18 At risk.
- 112 of them still bought in FY2, so most lapsed recently rather than long ago.
- Median recency is 242 days. 28 of them last bought in Aug 2011, just past the 90-day floor, so this group is the most sensitive to the thresholds.
- Separately, 8 top-20% customers bought on only one day and have been inactive for more than 90 days. They are worth £94,746 lifetime (`high_value_oneoff_lapsed_customers`, `high_value_oneoff_lapsed_monetary`).

**Top 10 by lifetime revenue** (`high_value_at_risk.csv`):

| Customer ID | country | lifetime £ | £ excl. reversed | FY2 £ | purchase days | last purchase | recency (days) | usual gap (days) | recency / gap | flags |
|---|---|---|---|---|---|---|---|---|---|---|
| 12346 | UK | 77,353 | 169 | 77,184 | 3 | 2011-01-18 | 326 | 161 | 2.0 | **reversed ≥50%**, single order, high cancel: **not a real at-risk account** |
| 16754 | UK | 65,500 | 57,109 | 2,002 | 19 | 2010-12-02 | 373 | 11 | 33.9 | reversed sale (£8,391) |
| 13093 | UK | 54,144 | 54,144 | 7,832 | 43 | 2011-03-09 | 276 | 11 | 25.1 | starts Dec 2009 |
| 17850 | UK | 51,209 | 51,209 | 5,391 | 23 | 2010-12-02 | 373 | 1.5 | 248.7 | starts Dec 2009 |
| 15749 | UK | 44,534 | 44,534 | 44,534 | 2 | 2011-04-18 | 236 | 97 | 2.4 | big order reversed after 3 months (C550456), 34% cancel rate, single order: **treat with caution** |
| 13902 | Denmark | 34,023 | 34,023 | 0 | 5 | 2010-03-17 | 633 | 26.5 | 23.9 | starts Dec 2009 |
| 13802 | UK | 26,259 | 25,839 | 4,599 | 18 | 2011-07-24 | 139 | 21 | 6.6 | reversed sale (£420) |
| 12482 | Sweden | 21,942 | 21,942 | 0 | 5 | 2010-05-12 | 577 | 17 | 33.9 | none |
| 15808 | UK | 17,388 | 17,388 | 3,735 | 21 | 2011-02-06 | 307 | 21 | 14.6 | starts Dec 2009 |
| 13027 | UK | 17,335 | 17,335 | 6,912 | 19 | 2011-08-18 | 114 | 27.5 | 4.1 | none |

Genuine, clean at-risk accounts from this list include 16754, 13093, 17850, 13802, 13027, 16553 and 16180. They are established multi-day buyers whose current silence is 4-250 times their usual gap. Accounts 13902 and 12482 have not bought since spring 2010 and are more likely already lost than at risk.

**Threshold sensitivity** (`at_risk_sensitivity.csv`, `at_risk_count_range`, `at_risk_monetary_range`):

| top share | gap multiple | min recency 60d | 90d | 180d |
|---|---|---|---|---|
| 20% | 1.5× | 207 / £1.56M | 169 / £1.28M | 103 / £0.86M |
| 20% | 2× | 171 / £1.38M | **151 / £1.20M** | 99 / £0.84M |
| 20% | 3× | 129 / £1.04M | 120 / £0.94M | 84 / £0.66M |
| 10% | 2× | 71 / £0.99M | 60 / £0.86M | 33 / £0.59M |

Each cell shows customers / lifetime £. Across the full grid the count ranges from 27 to 207 and lifetime £ from £0.44M to £1.56M. The minimum-recency floor moves the result more than the gap multiple does.

## 5. Repeat-purchase behaviour

| metric | value | evidence |
|---|---|---|
| Repeat rate (2+ purchase days, all customers) | 71.4% | `repeat_customer_rate`, `repeat_bands.csv` |
| Repeat rate excluding Dec-2009 starters | 67.6% | `repeat_rate_new_2010_2011` |
| Revenue share from repeat customers | 96.2% | `repeat_customer_revenue_share` |
| Median days from first to second purchase day (repeaters) | 63 | `median_days_first_to_second`, `repeat_first_to_second.csv` |
| Median usual gap between purchase days (repeaters) | 64 days (79.7 on the business-analysis average-gap basis) | `median_usual_gap_days`, `median_mean_gap_days` |
| New customers repeating within 30 / 60 / 90 / 180 days | 16.0% / 30.4% / 40.2% / 56.5% (n = 4,006) | `repeat_within_90d`, `repeat_within_180d`, `repeat_curve.csv` |

Time from first to second purchase (`repeat_first_to_second.csv`): 27% of repeaters return within 30 days, 61% within 90 days and 82% within 180 days. 4.5% take more than a year.

What distinguishes customers who come back (new customers from 2010-01-01 onwards, repeat within 180 days):

- **First-order size** (`repeat_by_first_order_value.csv`): the repeat rate rises from 40.6% for first orders under £100 to 49.8% (£100-250), 60.6% (£250-500) and 67.0% (£500-1k). Above £1k it levels off at 61-69%, and the bands are small. Breadth of the first basket shows the same pattern (`repeat_by_first_order_products.csv`): 46.0% with 1-5 distinct products against 69.3% with 51 or more.
- **One-off vs repeat buyers** (`one_off_vs_repeat.csv`): one-off buyers' first order has a median value of £233 and 16 products, against £309 and 19 products for repeaters. The UK share is the same (91% vs 91%). One-off buyers are 28.6% of customers but only 3.8% of identified revenue.
- **Country** (`repeat_by_country.csv`): there is no meaningful UK/non-UK difference (UK 56.4% vs non-UK 57.6%). Germany (64.4%, n=73) and France (66.7%, n=57) are slightly higher, but their samples are small.
- **First product** (`repeat_by_first_product.csv`, 180 products that appear in 100+ first orders): repeat rates range from 45.8% to 76.7%. The highest are lunch bags, cake cases and children's aprons (72-77%). The lowest include ANTIQUE SILVER TEA GLASS ETCHED (45.8%) and PACK OF 6 PANNETONE GIFT BOXES (47.3%). Both groups have similar median first-order values (about £380-£480 for the high group vs about £225-£425 for the low group), so the gap is not purely basket size. This is suggestive only and does not show cause.
- **FY1 vs FY2 acquisition cannot be compared** (`repeat_by_acquisition_fy.csv`). The table shows 642 customers first buying in 1 Jan-13 Jun 2011 (the 180-day eligibility cut-off), repeating at 53.1%, against 2,000 in Jan-Jun 2010 at 63.3%. That gap is a data-window artefact, not a trend. A 2010 customer counts as "new" if absent since Dec 2009 (one month of history); a 2011 customer must have been absent for 12+ months. On an equal one-month look-back, the 2011 cohort is 1,949 customers repeating at 62.3%, essentially the same as 2010, and 1,307 of them had bought in FY1 (`scripts/review_recheck.py`, review.md B1). What can be said: FY2 brought 1,585 customers not seen in the prior 12 months (`outputs/analysis/metrics.json`, `new_customers_FY2`).
- **Monthly cohort retention:** see `cohort_retention.csv`, which is identical to `outputs/analysis/cohort_retention.csv`. The Dec 2009 baseline cohort keeps 37.6% at month 12. Later 2010 cohorts mostly keep 13-25%.

## 6. Key findings

1. **Value is highly concentrated in a small, repeat-buying core.** The top 1% of customers (59) generate 32.0% of identified revenue, and the top 10% generate 63.8%. The Champions segment (22.6% of customers) brings in 68.6%. Removing reversed sales barely changes the concentration (the top 1% share drops to 31.2%). *(Evidence: `concentration.csv`, `rfm_segments.csv`, `top_1pct_customer_share`, `top_10pct_customer_share`, `segment_revenue_share_champions`)*
2. **150 high-value customers meet our at-risk rule (27 to 207 depending on thresholds).** They spent **£263,703 in FY2**, an upper bound on the revenue that would go if all of them were lost; most are still buying occasionally (112 of the default 151 bought in FY2). Their lifetime value is £1.12M. These figures rank the top 20% without reversed sales; on gross value the rule gives 151 customers and £339,546, but £77,184 of that is customer 12346's order reversed within 16 minutes. 15749 is a single large order partly returned three months later and needs care. The largest clean accounts are 16754, 13093, 17850, 13802 and 13027. *(Evidence: `high_value_at_risk.csv`, `at_risk_sensitivity.csv`, `high_value_at_risk_customers_excl_reversed`, `high_value_at_risk_revenue_FY2_excl_reversed_basis`, `at_risk_count_range`)*
3. **Repeat buyers are the business: 71.4% of customers and 96.2% of identified revenue.** One-off buyers (28.6%) contribute 3.8%. The typical repeater comes back after about 2 months: 63 days median to the second purchase, and a 64-day usual gap. *(Evidence: `repeat_bands.csv`, `one_off_vs_repeat.csv`, `repeat_customer_rate`, `repeat_customer_revenue_share`, `median_days_first_to_second`)*
4. **The size and breadth of the first order is the strongest early signal of coming back; country is not.** The 180-day repeat rate is 40.6% for first orders under £100 and 67.0% for £500-1k. Across countries it is flat: UK 56.4% vs non-UK 57.6%. *(Evidence: `repeat_by_first_order_value.csv`, `repeat_by_first_order_products.csv`, `repeat_by_country.csv`, `repeat_within_180d`)*
5. **New-customer acquisition and early repeat rates cannot be compared between FY1 and FY2 on this data.** The apparent fall (642 vs 2,000 customers; 53.1% vs 63.3% repeating) disappears on an equal look-back (1,949 customers, 62.3%), because the data starts in Dec 2009. FY2 brought 1,585 customers not seen in the prior 12 months, with no comparable FY1 figure. *(Evidence: `repeat_by_acquisition_fy.csv`, `repeat_within_180d_FY2_new`; `scripts/review_recheck.py`, review.md B1)*
6. **Reversed and one-off large orders distort the value lists and must be flagged before they are used.** 297 customers have reversed sales, totalling £403,195. Five customers leave the top 20% when reversed sales are removed. The "Big spenders" segment is about 50% reversed sales. *(Evidence: `reversed_by_customer.csv`, `rfm_segments.csv`, `customers_with_reversed_sales`, `top20_changed_by_reversals`)*

## 7. Caveats and open questions

- **13.1% of revenue has no Customer ID** and is outside every figure here. If guest checkouts behave differently (for example, more one-off buying), the repeat rate is overstated for the business as a whole.
- **Reversed sales are pending a user decision.** The approved definition keeps them. This report shows gross figures and a sensitivity view. If the business decides to exclude them, `monetary_excl_reversed` and the `_excl_reversed` metrics apply.
- The 24h reversal rule misses slower reversals. 15749 (reversed after 3 months) is only caught through `outputs/analysis/anomaly_reversed_orders.csv` and the high-cancel flag.
- **The data window is only 2 years.** Dec 2009 starters have truncated histories (40% of the top 20%), and customers first seen late have had less time to repeat. That is why repeat-within-N metrics use an eligibility window.
- **Segment shares are outputs of the rule table**, not natural groups: Champions' 68.6% depends on the thresholds in `rfm_segment_rules.csv`, and F is not a true quintile (F = 1/2/3 are exactly 1/2/3 days).
- **Snapshot and Dec 2011:** recency is measured from 2011-12-10 and Dec 2011 has only 8 trading days. Some customers flagged in Aug-Sep 2011 may simply buy seasonally. Sending them a win-back offer before Christmas is low cost, but not all of them are truly lapsed.
- **"At-risk" is a behavioural rule, not a churn model.** It has not been validated against later purchases because there is no data after 2011-12-09.
- **Open questions for the business:** (1) Should reversed orders be excluded from customer value? (2) Is there a wholesale/retail flag that could separate trade accounts from consumers? (3) Can guest orders be linked to accounts, for example by email?
