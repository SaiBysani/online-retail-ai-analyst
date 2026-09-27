# Business Performance Review: Online Retail II

**Scope:** UCI Online Retail II invoice lines, 2009-12-01 to 2011-12-09 (GBP), from `data/processed/online_retail_II.csv`. Generated 2026-09-27 by `scripts/retail_analysis.py`; revised the same day to apply the corrections in [`review.md`](review.md). Evidence tables are in `outputs/analysis/`, and headline metrics are in `outputs/analysis/metrics.json` (cited below as `metric_key`).

**Revenue follows the approved CLAUDE.md definition.** Cancellations (C) and bad-debt adjustments (A) are never counted as revenue.

---

## 1. Assumptions

From `metrics.json` → `assumptions`:

1. Revenue uses the approved CLAUDE.md definition. Exact duplicate lines are kept, as the definition requires.
2. FY1 = Dec 2009 to Nov 2010, FY2 = Dec 2010 to Nov 2011. Dec 2011 (1-9 Dec) is partial and is excluded from all year-on-year comparisons.
3. Customer metrics use only revenue rows that have a Customer ID.
4. An order is one revenue invoice. AOV = revenue / revenue invoices.
5. A repeat customer is one who bought on 2 or more distinct days. Split invoices on the same day count once.
6. Cancellation value = C-invoice lines on product codes (non-product codes excluded, to match revenue). Cancellation rate = cancellation value / (revenue + cancellation value).

Data-quality caveats that affect interpretation (from [`data_quality_report.md`](data_quality_report.md), verdict "fit for analysis: yes with caveats", no FAIL):

- **Reversed orders are still in revenue.** Three sales lines of £5,000 or more were cancelled by the same customer within 24 hours. Together they are worth £284,623 (`reversed_24h_value`):
  - invoice 581483: £168,470, 2011-12-09, customer 16446
  - invoice 541431: £77,184, 2011-01-18, customer 12346
  - invoice 556444: £38,970, 2011-06-10, customer 15098

  The headline figures keep the approved definition. Every section also shows a **sensitivity figure that excludes these three sales and their cancellations** (the `*_excl_reversed_24h` columns and metrics). **Scope:** in this report "excl. reversals" always means these three lines (£284,623). `customer_analysis.md` uses the broader set of all 1,444 lines reversed by the same customer within 24h (£403,195), because it needs every small reversal at customer level. A wider rule (any lag, £5,000 or more) also catches 540815 (£6,539, cancelled 3 months later), giving `reversed_any_lag_value` of £291,163. That is an ordinary return, not a same-day reversal, so it is not in the sensitivity figure (`anomaly_reversed_orders.csv`, `hours_to_cancel`). Matching requires the same customer, code, quantity **and price**, or a manual `M` cancellation line of the same value: 556444 is reversed by C556445 (manual `M`, £38,970). Order 530715 (£15,818) is not a reversal: its cancellation C536757 credited the 9,360 units at £0.03 each, only £281.
- **Revenue is gross of returns.** Product cancellations total £719,656, or 3.7% of revenue. C invoices cannot be linked to the sale they reverse.
- **Customer ID is missing on 13.1% of revenue** (`revenue_share_without_customer_id`). Customer figures therefore cover about 86.9% of revenue and will not reconcile with total revenue.
- **11,731 exact duplicate lines worth £57,093 (0.3%) remain in revenue** under the approved definition. They are reported here, not removed.
- **Country rule:** country figures are at line level. Each line takes the Country value recorded on it. The 12 customers who have revenue lines under more than one country (13 if cancellation rows are counted) contribute revenue to each country they bought under, and are counted in each country's `customers` column. Country values are used exactly as recorded. EIRE (Ireland), RSA (South Africa), Unspecified and European Community are kept as separate values. "International" means every value other than United Kingdom.
- Dec 2009 is the first month, so every customer seen then looks new. It is used only as a cohort baseline.

## 2. Headline scorecard (FY1 vs FY2)

Total approved revenue for the whole period is **£19,700,954** (`revenue_total`). Excluding the three 24h reversals it is £19,416,331 (`revenue_total_excl_reversed_24h`).

| Metric | FY1 (Dec09-Nov10) | FY2 (Dec10-Nov11) | Change | FY2 excl. 24h reversals | Evidence |
|---|---|---|---|---|---|
| Revenue | £9,429,521 | £9,655,940 | +2.4% | £9,539,786 (+1.2%) | `revenue_FY1`, `revenue_FY2`, `revenue_growth_FY2_vs_FY1`, `revenue_growth_excl_reversed_24h` |
| Orders | 19,743 | 18,957 | -4.0% | n/a | `orders_FY1`, `orders_FY2`, `orders_growth` |
| AOV | £477.61 | £509.36 | +6.6% | £503.29 (+5.4%) | `aov_FY1`, `aov_FY2`, `aov_growth`, `aov_growth_excl_reversed_24h` |
| Customers (with ID) | 4,239 | 4,293 | +1.3% | n/a | `customers_FY1`, `customers_FY2` |
| Revenue with a Customer ID | £8,363,874 | £8,247,836 | -1.4% | -2.8% | `revenue_identified_growth`, `revenue_identified_growth_excl_reversed_24h` |
| Revenue without a Customer ID | £1,065,647 | £1,408,104 | +32.1% | n/a | `revenue_unidentified_growth` |
| Cancellation rate | 2.5% | 3.1% | +0.6 pts | 2.3% | `cancel_rate_FY1`, `cancel_rate_FY2`, `cancel_rate_FY2_excl_reversed_24h` |
| UK share of revenue | 86.0% | 84.7% | -1.3 pts | n/a | `uk_share_FY1`, `uk_share_FY2` |

**Reading:** revenue was roughly flat, +2.4% as reported and +1.2% without the reversed orders. Growth came from larger baskets (AOV +6.6%) while order count fell 4.0%. The entire increase sits in revenue **without** a Customer ID (+32.1%). Revenue from identified customers fell 1.4%, or 2.8% without the reversals.

## 3. Revenue and monthly trends

**The business is strongly seasonal, and FY2 was weak in the first half and firmer from May.** Sep-Nov produced 36.1% of FY1 revenue and 37.2% of FY2 revenue (`peak_season_share_FY1`, `peak_season_share_FY2`). November is the peak month in both years: £1,435,680 in Nov 2010 and £1,457,746 in Nov 2011 (`monthly.csv`).

Year-on-year change by month (`monthly.csv`, `revenue_yoy` and `revenue_yoy_excl_reversed_24h`):

| Month (FY2) | Revenue | YoY | YoY excl. 24h reversals |
|---|---|---|---|
| Dec 2010 | £777,932 | -2.9% | -2.9% |
| Jan 2011 | £671,933 | +9.5% | **-3.1%** |
| Feb 2011 | £508,886 | -5.7% | -5.7% |
| Mar 2011 | £691,258 | -9.6% | -9.6% |
| Apr 2011 | £516,218 | -20.5% | -20.5% |
| May 2011 | £741,192 | +14.8% | +14.8% |
| Jun 2011 | £738,752 | +5.6% | **+0.1%** |
| Jul 2011 | £689,364 | +8.6% | +8.6% |
| Aug 2011 | £725,514 | +7.3% | +7.3% |
| Sep 2011 | £1,030,475 | +18.2% | +18.2% |
| Oct 2011 | £1,106,670 | +0.8% | +0.8% |
| Nov 2011 | £1,457,746 | +1.5% | +1.5% |

- Without the reversed orders, **every month from Dec 2010 to Apr 2011 declined** year on year. The reported +9.5% in Jan 2011 comes entirely from the £77,184 order 541431, which was cancelled 16 minutes later.
- April 2011 had 21 trading days against 23 in April 2010 (`monthly.csv`, `trading_days`). That explains part of its -20.5%, but not all of it.
- The peak season grew only modestly. September was strong (+18.2%), but October and November were almost flat (+0.8% and +1.5%).
- **Dec 2011 is partial** (8 trading days, £615,493) and is not compared with any full month. £168,470 of it is the reversed order 581483. Without it, Dec 2011 is £447,024 and its AOV falls from £754 to £548 (`monthly.csv`, `revenue_excl_reversed_24h`, `aov_excl_reversed_24h`).

## 4. Products

**Revenue is spread across a long range, and the headline product ranking is distorted by reversed orders.** 4,895 stock codes sold. 1,040 of them (class A) make up 80% of revenue (`products_sold`, `a_class_products`, `products.csv`).

Top products by revenue (`products.csv`):

| # | Product | Revenue | FY1 → FY2 |
|---|---|---|---|
| 1 | 22423 REGENCY CAKESTAND 3 TIER | £331,084 | £156,600 → £168,478 |
| 2 | 85123A WHITE HANGING HEART T-LIGHT HOLDER | £258,066 | £153,547 → £102,292 |
| 3 | 85099B JUMBO BAG RED RETROSPOT | £180,888 | £86,548 → £92,113 |
| 4 | 23843 PAPER CRAFT, LITTLE BIRDIE | £168,470 | Dec 2011 only. **Its whole revenue is one reversed order (581483)**, so excluding it this product has £0 |
| 5 | 47566 PARTY BUNTING | £148,396 | £48,892 → £98,586 |
| 6 | 84879 ASSORTED COLOUR BIRD ORNAMENT | £129,681 | £70,586 → £56,932 |
| 7 | 22086 PAPER CHAIN KIT 50'S CHRISTMAS | £117,884 | £52,932 → £58,082 |

Excluding the 24h reversals, 23843 drops out and the genuine top 6 is the list above without it (`products.csv`, `rank_excl_reversed_24h`).

**Risers FY1 → FY2** (`product_movers.csv`):

- 23166 MEDIUM CERAMIC TOP STORAGE JAR is the largest riser at +£81,448, but **£77,184 of that is reversed order 541431**. Its FY2 revenue without the reversal is £4,265 (`FY2_excl_reversed_24h`).
- 22502 PICNIC BASKET WICKER SMALL shows +£41,929, but £38,970 of that is reversed order 556444, a line priced at £649.50 against a median of £5.95 (`anomaly_price_outliers.csv`). Without it, FY2 is £12,457 against £9,498 in FY1.
- The genuine risers are mostly **new FY2 lines** (FY1 = £0): 23084 RABBIT NIGHT LIGHT (+£57,322), 23298 SPOTTY BUNTING (+£42,418), 23203 JUMBO BAG VINTAGE DOILY (+£40,716), 22720 SET OF 3 CAKE TINS PANTRY (+£37,070) and 23284 DOORMAT KEEP CALM (+£36,592). 47566 PARTY BUNTING doubled (+£49,694).

**Fallers FY1 → FY2** (`product_movers.csv`):

- 85123A WHITE HANGING HEART fell £51,255, the largest decline among the top sellers.
- Several lines were discontinued (FY2 = £0): 37503 TEA TIME CAKE STAND (-£25,471), 79323W WHITE CHERRY LIGHTS (-£18,049) and 84467 QUILTED THROW (-£17,478).
- 84347 ROTATING SILVER ANGELS fell £21,135. Its FY1 includes the single £15,818 order 530715. That order's quantity was cancelled 28 days later but credited at £0.03 a unit (£281), so it stays in revenue on any basis.

**High cancellation** (`products_high_cancel.csv`, products with at least £5,000 revenue):

- Apart from the two reversal-driven codes (23843 at 50.0%, 23166 at 48.7%), the highest rates are:
  - 23113 PANTRY CHOPPING BOARD: 45.0%
  - 85220 FAIRY CAKE MAGNETS: 34.7%
  - the cherry-lights family 79323W / 79323LP / 79323P: 22-26%, all discontinued in FY2
  - 21108 FAIRY CAKE FLANNEL: 20.6%
- Cabinets and clocks (22656, 22655, 21735, 22191) cancel at 14-20%. The data holds no cancellation reason, so whether this reflects quality, delivery or ordering behaviour is unknown.

## 5. Customers

Customer figures cover revenue with a Customer ID only (86.9% of revenue). Detailed segmentation (RFM, at-risk customers, repeat behaviour) is in [`customer_analysis.md`](customer_analysis.md) and is not repeated here. Its headlines: the Champions segment (22.6% of customers) brings in 68.6% of identified revenue, and 150 high-value customers meet its at-risk rule (27-207 depending on thresholds).

- **Revenue is concentrated in a few customers.** The top 1% of customers (59) produce 32.0% of identified revenue. The top 10% (585) produce 63.8% (`customer_concentration.csv`, `top_10pct_customer_share`). Customers 12346, 16446 and 15098 rank high partly because of their reversed orders, so any top-customer list must flag them.
- **Customers were retained but spent less.** 63.9% of FY1 customers bought again in FY2 (2,708 of 4,239), and 1,585 new customers arrived (`customer_retention_FY1_to_FY2`, `new_customers_FY2`, `customer_lifecycle.csv`). In FY2, retained customers produced £6,794,259 and new customers £1,453,577. The 1,531 lost customers had produced £1,059,110 in FY1. Revenue per customer fell from £1,973 to £1,921 (`customer_lifecycle.csv`).
- **New-customer acquisition cannot be compared year on year.** FY2 brought 1,585 customers not seen in the prior 12 months (`new_customers_FY2`). No comparable FY1 figure exists: the data starts in Dec 2009, so a 2010 "new" customer only had to be absent for one month, and many were existing accounts. The monthly `new_customers` column in `monthly.csv` has the same bias and must not be read as a trend. On an equal one-month look-back, monthly counts for Jan-Jun 2011 (416/380/452/300/284/242) are in line with 2010 (368/375/441/294/255/267), so there is no evidence of a slowdown (`scripts/review_recheck.py`, review.md B1). Cohorts from mid-2010 onwards keep 13-25% of their customers at 12 months; the Dec 2009 cohort (37.6%) is the data-edge cohort and overstates retention (`cohort_retention.csv`).
- **The revenue without a Customer ID is growing, from fewer but larger invoices.** It rose 32.1% to £1,408,104 in FY2 (`revenue_unidentified_growth`): +£342,457, against a -£116,038 fall in identified revenue and a +£226,418 net gain. Invoices without a Customer ID **fell** 14% (1,551 → 1,331), so the average rose from about £687 to about £1,058. The increase is all UK (+£348,759 UK, -£6,302 international) and peaks in Dec 2010 (27.1% of that month's revenue, against 15.0% in Dec 2009) and Nov 2011 (21.6%) (`scripts/review_recheck.py`, review.md S1). Fewer, larger invoices fit poorly with "new guest buyers"; the cause is unknown, and until data capture is ruled out the fall in identified-customer revenue should not be read as customers spending less.

## 6. Repeat purchases

**Repeat buyers are almost the whole business.** 71.4% of identified customers bought on two or more days, and they produce 96.2% of identified revenue (`repeat_customer_rate`, `repeat_customer_revenue_share`).

Purchase-frequency bands (`repeat_purchases.csv`):

| Purchase days | Customers | Share of customers | Share of revenue |
|---|---|---|---|
| 1 | 1,673 | 28.6% | 3.8% |
| 2 | 1,010 | 17.3% | 5.5% |
| 3-5 | 1,500 | 25.6% | 12.6% |
| 6-10 | 912 | 15.6% | 16.7% |
| 11-25 | 602 | 10.3% | 26.6% |
| 26+ | 155 | 2.7% | 34.8% |

- The 155 customers who bought on 26 or more days produce 34.8% of identified revenue.
- The typical repeat buyer returns about every two months: the median usual gap between purchase days is 64 days (`customer_analysis.md` §5, `median_usual_gap_days`). *Footnote: the average-gap basis used in this script, (last − first purchase) / (purchase days − 1), gives a median of 79.7 days (`median_days_between_purchases`); it is pulled up by long silences, so the 64-day figure is the one to quote.*

## 7. Countries

**The UK is 85.6% of revenue but is flat. International markets grew.** UK revenue grew 0.8% FY1 → FY2 (`uk_growth_FY2_vs_FY1`). Without the three reversed orders, all of which were UK customers, it **fell 0.6%** (`uk_growth_excl_reversed_24h`). International revenue grew 12.1% (`non_uk_growth_FY2_vs_FY1`), and the UK share fell from 86.0% to 84.7%. Revenue came from 43 country values (`countries`).

Top markets (`countries.csv`):

| Country | Revenue | FY1 → FY2 change | AOV | Cancellation rate |
|---|---|---|---|---|
| United Kingdom | £16,856,331 | +0.8% (-0.6% excl. reversals) | £466 | 3.6% |
| EIRE | £623,796 | -25.1% | £1,074 | 3.2% |
| Netherlands | £549,775 | +2.4% | £2,545 | 0.7% |
| Germany | £383,848 | +11.4% | £510 | 2.2% |
| France | £311,288 | +40.5% | £521 | 5.4% |
| Australia | £167,868 | +365.3% | £1,886 | 0.9% |
| Spain | £97,818 | +31.7% | £679 | 11.7% |
| Switzerland | £94,047 | +29.6% | £1,106 | 1.2% |
| Sweden | £86,353 | -26.1% | £872 | 2.2% |
| Denmark | £67,423 | -63.3% | £1,605 | 5.7% |

- **International growth is broad and comes from small bases.** France (£126,706 → £178,044), Australia (£29,696 → £138,171), Japan, Norway and Belgium grew. EIRE (3 customers), Denmark and Sweden fell (`countries.csv`, `FY1`, `FY2`).
- EIRE has 3 customers and the Netherlands 22, so these markets depend on a few accounts.
- **International buyers place larger orders:** Netherlands AOV is £2,545 and Australia's is £1,886, against £466 for the UK. The data has no customer-type field, so whether these are trade buyers is not known.
- Among markets over £50,000, cancellation rates are highest in **Spain (11.7%)**, Denmark (5.7%) and France (5.4%). The UK is at 3.6%.

## 8. Cancellations

**Cancellations are moderate and not rising once the reversed orders are removed.** Product cancellations total £719,656 (`cancel_value_total`). That is a cancellation rate of 3.5% of revenue plus cancellations (`cancel_rate_total`), the basis used for every rate in this report; §1's 3.7% is the same value divided by revenue alone.

- As reported, the rate rose from 2.5% in FY1 to 3.1% in FY2 (`cancel_rate_FY1`, `cancel_rate_FY2`).
- Excluding the three 24h reversals and their cancellations, **FY2 is 2.3%**, slightly below FY1 (`cancel_rate_FY2_excl_reversed_24h`). The apparent increase is therefore the reversed orders, not a trend.
- Monthly spikes (`monthly.csv`, `cancel_rate`):
  - Jan 2011 (12.0%) and Dec 2011 (22.1%) are reversal-driven. They are 2.4% and 1.3% without the reversals (`cancel_rate_excl_reversed_24h`).
  - May 2010 (5.5%), Apr 2011 (6.1%) and Oct 2011 (3.8%) are genuine spikes.
- Cancellations are concentrated in bulky items, discontinued lines (cherry lights) and a few markets (Spain, France, Denmark). See sections 4 and 7.
- **Treatment:** C invoices are never counted as revenue. Revenue is gross of returns. No "net revenue" figure is shown, because cancellations cannot be matched to their original sale (`data_quality_report.md` §7).

## 9. Anomalies

- **Outlier days.** 13 days have a robust z-score of 4 or more (daily median £28,234) (`anomaly_days`, `anomaly_days.csv`).
  - Two of them are single reversed orders. On 2011-12-09 (£198,114) the largest line is 85.0% of the day's revenue. On 2011-01-18 (£94,394) it is 81.8%.
  - On 2010-11-04 (£89,297), 17.7% of the day is order 530715, whose quantity was later cancelled but credited at only £281.
  - The other 10 are genuine peak-season trading days (Sep-Dec), where no line exceeds 7% of the day.
- **Large reversed orders still in revenue.** The £284,623 of 24h reversals (`reversed_24h_value`) inflate:
  - FY2 growth: +2.4% reported vs +1.2% without them
  - UK growth: +0.8% vs -0.6%
  - FY2 AOV: £509 vs £503
  - Jan and Jun 2011 year-on-year growth
  - Dec 2011 revenue
  - the product ranking (23843, 23166, 22502)
  - the value of customers 16446, 12346 and 15098

  (`anomaly_reversed_orders.csv`, `anomaly_top_lines.csv`)
- **Price outliers.** Apart from 556444 (60 × £649.50 against a £5.95 median, and reversed), the outliers are small: FLAG OF ST GEORGE lines at £408-£1,157 against a £0.42 median, and lunch bags and tissues at about 3× median. Each line is under £1,200 (`anomaly_price_outliers.csv`). They do not move any headline.
- The £57,093 of exact duplicate lines is not investigated here (see caveats).

## 10. Key findings

1. **Revenue was essentially flat: +2.4% FY1 → FY2 (£9.43m → £9.66m), or +1.2% without three orders reversed within minutes.** *(Evidence: `monthly.csv`, `revenue_growth_FY2_vs_FY1`, `revenue_growth_excl_reversed_24h`)*
2. **Growth came from basket size, not volume.** Orders fell 4.0% and AOV rose 6.6% (5.4% without the reversals). *(Evidence: `monthly.csv`, `orders_growth`, `aov_growth`, `aov_growth_excl_reversed_24h`)*
3. **Identified-customer revenue fell (-1.4%, or -2.8% without the reversals), while revenue with no Customer ID rose 32.1%.** All reported growth sits in revenue we cannot attribute to a customer, and it came from fewer, larger UK invoices (1,551 → 1,331), so a data-capture or channel change is as likely as real customer behaviour. FY2 brought 1,585 customers not seen in the prior 12 months; no comparable FY1 figure exists. *(Evidence: `customer_lifecycle.csv`, `revenue_identified_growth`, `revenue_identified_growth_excl_reversed_24h`, `revenue_unidentified_growth`, `new_customers_FY2`; review.md S1, B1)*
4. **The UK (85.6% of revenue) was flat to slightly down (-0.6% without the reversals). International markets grew 12.1%**, led by France, Australia, Germany and Spain, with much larger AOVs. *(Evidence: `countries.csv`, `uk_growth_excl_reversed_24h`, `non_uk_growth_FY2_vs_FY1`)*
5. **Seasonality dominates.** Sep-Nov is 36-37% of the year. H1 of FY2 (Dec-Apr) declined year on year in every month once reversals are removed. Growth came from May-Sep, and the Oct-Nov peak was flat (+0.8% and +1.5%). *(Evidence: `monthly.csv`, `revenue_yoy_excl_reversed_24h`, `peak_season_share_FY1`, `peak_season_share_FY2`)*
6. **The apparent rise in cancellations (2.5% → 3.1%) is an artefact of the reversed orders.** Excluding them, the FY2 rate is 2.3%. Genuine hot spots are bulky furniture, discontinued lighting lines and Spain (11.7%). *(Evidence: `cancel_rate_FY2_excl_reversed_24h`, `products_high_cancel.csv`, `countries.csv`)*
7. **Headline product and top-day rankings are distorted by reversed orders.** The #4 product (23843), the top riser (23166) and the #5 riser (22502) are mostly or entirely reversed orders. The real growth engine is new FY2 lines (rabbit night light, bunting, pantry tins). *(Evidence: `products.csv`, `product_movers.csv`, `rank_excl_reversed_24h`, `FY2_excl_reversed_24h`, `anomaly_top_lines.csv`)*
8. **The business depends on a small base of loyal repeat buyers.** The top 10% of customers produce 63.8% of identified revenue. Repeat buyers produce 96.2%, returning about every two months (64-day median usual gap). *(Evidence: `customer_concentration.csv`, `repeat_purchases.csv`, `top_10pct_customer_share`, `repeat_customer_revenue_share`; `customer_analysis.md` §5, `median_usual_gap_days`)*

## 11. Caveats and open questions

- **Reversed orders (user decision pending).** Should same-day reversals be removed from the approved revenue definition? This review keeps them in the headline and shows a sensitivity figure. The decision changes the UK growth sign and the cancellation-rate trend.
- **Why is revenue without a Customer ID growing 32% on 14% fewer invoices?** It is all UK and concentrated in Dec 2010 and Nov 2011. A trade counter, a new channel or a change in data capture are all possible. Until this is answered, the "customers are spending less" finding may be a data-capture effect.
- **Returns are not netted.** Revenue is gross of returns (-£719,656 of product cancellations). A true net-revenue figure needs a way to link returns to sales.
- **Duplicate lines.** The £57,093 of exact duplicate lines is kept. If these are double scans, revenue is overstated by 0.3%.
- **Small-base international growth.** Australia (+365%), Japan and Norway grew from small bases with few customers. Treat them as early signals, not trends.
- **April 2011 decline (-20.5%).** Only part of it is explained by 2 fewer trading days. What else happened?
- **Customer segmentation** (RFM, at-risk customers, top-customer list with reversal flags) is in [`customer_analysis.md`](customer_analysis.md).
