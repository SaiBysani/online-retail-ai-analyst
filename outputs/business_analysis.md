# Business Analysis: Online Retail II

**Scope:** invoice lines from a UK online gift and homeware wholesaler, 2009-12-01 to 2011-12-09 (UCI Online Retail II, `data/processed/online_retail_II.csv`). Currency GBP. Generated 2026-09-27 by the retail-analysis skill from `scripts/retail_analysis.py`.

**Revenue follows the approved CLAUDE.md definition.** Cancellations (C invoices), bad-debt adjustments (A invoices), non-product codes, and rows with Quantity ≤ 0 or Price ≤ 0 are excluded. The sheet overlap is counted once.

Evidence: tables are in `outputs/analysis/` and metric keys refer to `outputs/analysis/metrics.json`.

---

## 1. Assumptions

From `metrics.json → assumptions`:

1. Revenue = approved CLAUDE.md definition. Exact duplicate lines are kept, as the definition does.
2. FY1 = Dec 2009 to Nov 2010, FY2 = Dec 2010 to Nov 2011. Dec 2011 (1 to 9 Dec) is partial and excluded from year-on-year comparisons.
3. Customer metrics use revenue rows with a Customer ID only.
4. Order = one revenue invoice. AOV = revenue / revenue invoices.
5. Repeat customer = bought on 2 or more distinct days (same-day split invoices count once).
6. Cancellation value = C-invoice lines on product codes (non-product codes excluded, to match revenue). Cancellation rate = cancellation value / (revenue + cancellation value).
7. *(Added for this report)* "Reversed big orders" are sales lines of £5,000 or more that were later cancelled with the same product, quantity and customer (`anomaly_reversed_orders.csv`). The approved definition **keeps** them in revenue. Where a figure excludes them, the text says so.

Data-quality caveats that affect interpretation (see [`data_quality_report.md`](data_quality_report.md), verdict **fit for analysis: yes with caveats**):

- 13.1% of revenue (£2,576,013) has no Customer ID, so customer metrics describe about 87% of revenue (DQ §3).
- 11,731 exact-duplicate lines (£57,093, 0.3%) stay in revenue under the definition (DQ §4).
- Dec 2011 has only 8 trading days (DQ §8), and in Dec 2009 every customer looks new.
- Several very large orders were reversed minutes later but still count as revenue (DQ §9, and §10 below).

## 2. Headline scorecard (FY1 vs FY2)

| Metric | FY1 (Dec 09 to Nov 10) | FY2 (Dec 10 to Nov 11) | Change | Evidence |
|---|---|---|---|---|
| Revenue | £9,429,521 | £9,655,940 | +2.4% | `revenue_FY1`, `revenue_FY2`, `revenue_growth_FY2_vs_FY1` |
| Revenue, excl. reversed big orders | | | +1.3% | `revenue_growth_excl_reversed` |
| Orders | 19,743 | 18,957 | −4.0% | `orders_FY1`, `orders_FY2`, `orders_growth` |
| Average order value | £477.61 | £509.36 | +6.6% | `aov_FY1`, `aov_FY2`, `aov_growth` |
| Identified customers | 4,239 | 4,293 | +1.3% | `customers_FY1`, `customers_FY2` |
| Revenue with a Customer ID | £8,363,874 | £8,247,836 | −1.4% | `revenue_identified_growth` |
| Revenue without a Customer ID | £1,065,647 | £1,408,104 | +32.1% | `revenue_unidentified_growth` |
| Cancellation rate | 2.5% | 3.1% | +0.6 pts | `cancel_rate_FY1`, `cancel_rate_FY2` |
| Cancellation rate, excl. reversed big orders | 2.5% | 2.3% | −0.2 pts | `cancel_rate_FY1_excl_reversed`, `cancel_rate_FY2_excl_reversed` |
| UK share of revenue | 86.0% | 84.7% | −1.3 pts | `uk_share_FY1`, `uk_share_FY2` |

**Reading:** the business was essentially flat. Revenue grew 2.4%, and only 1.3% once reversed bulk orders are removed. Growth came from higher order values rather than more orders. Identified customers actually spent less (−1.4%). All of the net growth sits in revenue that has no Customer ID (+£342K), so the growth can't be attributed to any customer.

Total revenue across the whole period: **£19,700,954** (`revenue_total`).

## 3. Revenue and monthly trends

**The business is strongly seasonal, and the year-on-year picture is flat with a weak spring and a stronger late summer.**

- Sep to Nov 2011 produced **37.2% of FY2 revenue** (`peak_season_share_FY2`). November is the peak month in both years: £1,435,680 (Nov 2010) and £1,457,746 (Nov 2011) (`monthly.csv`).
- Year-on-year by month in FY2 (`monthly.csv → revenue_yoy`):

| Month | Revenue | YoY | Note |
|---|---|---|---|
| 2010-12 | £777,932 | −2.9% | |
| 2011-01 | £671,933 | +9.5% | includes the £77,184 order reversed 16 minutes later (§10) |
| 2011-02 | £508,886 | −5.7% | |
| 2011-03 | £691,258 | −9.6% | |
| 2011-04 | £516,218 | −20.5% | 21 trading days vs 23 in Apr 2010 (Easter) |
| 2011-05 | £741,192 | +14.8% | |
| 2011-06 | £738,752 | +5.6% | includes the £38,970 reversed picnic-basket line |
| 2011-07 | £689,364 | +8.6% | |
| 2011-08 | £725,514 | +7.3% | |
| 2011-09 | £1,030,475 | +18.2% | |
| 2011-10 | £1,106,670 | +0.8% | |
| 2011-11 | £1,457,746 | +1.5% | |

- The first half of FY2 (Dec to Apr) was below the prior year in 4 of 5 months. From May to September every month was up year on year. October and November, the largest months, were flat (+0.8%, +1.5%).
- **Dec 2011 (£615,493, 8 trading days) is partial and not compared.** Its high AOV (£754) comes from the £168,470 order that was reversed 12 minutes later (§10).

## 4. Products

**The range is broad but concentrated. Around 1,040 of 4,895 selling stock codes (21%) make up 80% of revenue** (`a_class_products`, `products_sold`, `products.csv → abc`).

Top 10 products by revenue (`products.csv`):

| # | Product | Revenue | Cancel rate |
|---|---|---|---|
| 1 | 22423 REGENCY CAKESTAND 3 TIER | £331,084 | 4.8% |
| 2 | 85123A WHITE HANGING HEART T-LIGHT HOLDER | £258,066 | 3.5% |
| 3 | 85099B JUMBO BAG RED RETROSPOT | £180,888 | 1.2% |
| 4 | 23843 PAPER CRAFT, LITTLE BIRDIE | £168,470 | 50.0% (one order, fully reversed) |
| 5 | 47566 PARTY BUNTING | £148,396 | 0.8% |
| 6 | 84879 ASSORTED COLOUR BIRD ORNAMENT | £129,681 | 0.6% |
| 7 | 22086 PAPER CHAIN KIT 50'S CHRISTMAS | £117,884 | 1.2% |
| 8 | 23166 MEDIUM CERAMIC TOP STORAGE JAR | £81,701 | 48.7% (mostly one reversed order) |
| 9 | 79321 CHILLI LIGHTS | £80,873 | 0.8% |
| 10 | 22197 SMALL POPCORN HOLDER | £79,553 | 0.8% |

Two of the top 10 (#4 and #8) are there only because of a single bulk order that was cancelled within minutes. Without them, the top of the ranking is stable, established lines.

**Risers and fallers, FY1 to FY2** (`product_movers.csv`, products with ≥ £5K in either year):

- *Risers* are mostly **new FY2 lines**: RABBIT NIGHT LIGHT (+£57,322), SPOTTY BUNTING (+£42,418), JUMBO BAG VINTAGE DOILY (+£40,716), SET OF 3 CAKE TINS PANTRY DESIGN (+£37,070), and DOORMAT KEEP CALM AND COME IN (+£36,592), all with £0 in FY1. PARTY BUNTING roughly doubled (+£49,694). The top riser on paper, MEDIUM CERAMIC TOP STORAGE JAR (+£81,448), is mostly the reversed 74,215-unit order.
- *Fallers* include the #2 product, WHITE HANGING HEART T-LIGHT HOLDER (−£51,255, from £153,547 to £102,292), plus lines discontinued in FY2 such as TEA TIME CAKE STAND IN GIFT BOX (−£25,471) and WHITE CHERRY LIGHTS (−£18,049). RED RETROSPOT CAKE STAND fell too (−£23,596).

**Products with unusually high cancellation** (`products_high_cancel.csv`, ≥ £5K revenue):

- After the two reversed bulk orders, the highest rates are PANTRY CHOPPING BOARD (45.0%) and SMALL FAIRY CAKE FRIDGE MAGNETS (34.7%).
- The CHERRY LIGHTS family stands out: WHITE 26.2%, LIGHT PINK 24.2% and PINK 22.6%, all dropped in FY2. That pattern is consistent with a quality or supply problem.
- FAIRY CAKE FLANNEL (20.6%) and VINTAGE BLUE KITCHEN CABINET (20.3%) are also high, compared with 3.5% overall (`cancel_rate_total`).

## 5. Customers

**Revenue depends heavily on a small group of loyal wholesale accounts.**

- **Concentration** (`customer_concentration.csv`): the top 1% of customers (59) generate 32.0% of identified revenue, the top 10% (585) generate **63.8%** (`top_10pct_customer_share`), and the top 20% generate 77.1%.
- **Retention FY1 to FY2** (`customer_lifecycle.csv`): **63.9%** of FY1 customers bought again in FY2 (`customer_retention_FY1_to_FY2`), which is 2,708 retained customers. The 1,531 customers lost had spent £1,059,110 in FY1.
- **New vs retained, FY2**: 1,585 new customers (`new_customers_FY2`) brought in £1,453,577. The 2,708 retained customers brought in £6,794,259, or 82% of identified FY2 revenue. New customers (£1.45M) more than replaced the FY1 spend of lost customers (£1.06M), yet identified revenue still fell £116K. The retained customers spent less: £6.79M in FY2 against about £7.30M in FY1 (FY1 identified revenue minus lost customers' spend).
- **Revenue per identified customer** fell from £1,973 to £1,921 (−2.6%, `customer_lifecycle.csv → revenue_per_customer`).
- **Acquisition is slowing.** New customers per month fell from 163 to 441 in FY1 (Jan to Nov 2010) to 72 to 221 in FY2 (`monthly.csv → new_customers`). Part of this is structural, because in FY1 many long-standing customers appear "new" the first time we see them. But even Sep to Nov 2011 (188 / 221 / 191) was below Sep to Nov 2010 (239 / 375 / 326).
- **Cohort retention** (`cohort_retention.csv`): the Dec 2009 cohort (really the existing customer base) keeps about 38% active at month 12. Genuine 2010 cohorts keep 13 to 25% at month 12. Month-1 return rates for 2011 cohorts (14 to 32%) are similar to or better than those for 2010 cohorts (16 to 26%). Blank cells are periods the data doesn't reach yet. Ages that land in Dec 2011 (e.g. the Jun 2011 cohort's m6, 8.3%) cover only 8 days and understate retention.
- **Revenue without a Customer ID** is 13.1% of all revenue (`revenue_share_without_customer_id`) and grew 32.1% year on year (`revenue_unidentified_growth`). These are most likely guest or one-off checkouts. None of the customer metrics above can see them.

## 6. Repeat purchases

**Repeat buyers are the business: 71.4% of identified customers bought on 2 or more days, and they generate 96.2% of identified revenue** (`repeat_customer_rate`, `repeat_customer_revenue_share`).

Purchase-frequency bands (`repeat_purchases.csv`):

| Purchase days | Customers | Share of customers | Share of revenue |
|---|---|---|---|
| 1 | 1,673 | 28.6% | 3.8% |
| 2 | 1,010 | 17.3% | 5.5% |
| 3 to 5 | 1,500 | 25.6% | 12.6% |
| 6 to 10 | 912 | 15.6% | 16.7% |
| 11 to 25 | 602 | 10.3% | 26.6% |
| 26+ | 155 | 2.7% | 34.8% |

- The 155 most frequent buyers (26+ purchase days) produce **34.8%** of identified revenue. The 757 customers with 11 or more purchase days produce 61.4%.
- The median repeat customer buys about **every 80 days** (`median_days_between_purchases` = 79.7), which is roughly quarterly and consistent with shops restocking by season.

## 7. Countries

**The UK is 85.6% of revenue and barely grew. International markets grew 12.1% and are where the growth is** (`uk_revenue_share`, `uk_growth_FY2_vs_FY1` = +0.8%, `non_uk_growth_FY2_vs_FY1` = +12.1%).

Top 10 markets (`countries.csv`):

| Country | Revenue | Share | FY1 to FY2 | AOV | Cancel rate |
|---|---|---|---|---|---|
| United Kingdom | £16,856,331 | 85.6% | +0.8% | £466 | 3.6% |
| EIRE | £623,796 | 3.2% | −25.1% | £1,074 | 3.2% |
| Netherlands | £549,775 | 2.8% | +2.4% | £2,545 | 0.7% |
| Germany | £383,848 | 1.9% | +11.4% | £510 | 2.2% |
| France | £311,288 | 1.6% | +40.5% | £521 | 5.4% |
| Australia | £167,868 | 0.9% | +365.3% | £1,886 | 0.9% |
| Spain | £97,818 | 0.5% | +31.7% | £679 | 11.7% |
| Switzerland | £94,047 | 0.5% | +29.6% | £1,106 | 1.2% |
| Sweden | £86,353 | 0.4% | −26.1% | £872 | 2.2% |
| Denmark | £67,423 | 0.3% | −63.3% | £1,605 | 5.7% |

- **Growth markets:** France (+40.5%), Germany (+11.4%), Australia (£29,696 to £138,171), Japan (£5,608 to £37,416) and Norway (£6,121 to £29,709).
- **Declining markets:** EIRE, the second-largest market, fell 25.1% (£352,632 to £264,023). It has only 3 identified customers, so the loss is probably one or two accounts. Denmark and Sweden also fell.
- **AOV:** international orders are much larger. The Netherlands averages £2,545 per order and Australia £1,886, against £466 in the UK. These look like distributor or wholesale accounts.
- **Cancellation by country:** Spain (11.7%) and USA (20.8%, on small revenue) are high. France (5.4%) and Denmark (5.7%) are above average.
- The data has 43 country values with revenue (`countries`), including "Unspecified" and "European Community" (DQ §9).

## 8. Cancellations

**Cancelled product value was £719,656, or 3.5% of gross product sales** (`cancel_value_total`, `cancel_rate_total`). Cancellations are **excluded from revenue** and are shown here only as a separate rate.

- The headline rate rose from 2.5% (FY1) to 3.1% (FY2) (`cancel_rate_FY1`, `cancel_rate_FY2`). **Remove the reversed bulk orders and FY2 is 2.3%, below FY1** (`cancel_rate_FY2_excl_reversed`). The apparent rise is almost entirely the one £77,184 storage-jar order in January 2011, whose cancellation pushed that month's rate to 12.0% (`monthly.csv`).
- Other spikes: May 2010 (5.5%) and April 2011 (6.1%). Dec 2011 (22.1%) is driven by the £168,470 reversal (`monthly.csv`).
- Cancellations concentrate in the UK (£635,213 of £719,656, a 3.6% rate) and in the product lines listed in §4 (`countries.csv`, `products_high_cancel.csv`).
- Cancellation invoice numbers never match a sale number (DQ §7), so returns can't be linked to their original order by number. They can only be matched on customer, product and quantity, which is how §10 finds them.

## 9. Anomalies

**13 trading days are statistical outliers** (|robust z| ≥ 4 against a median day of £28,234, `anomaly_days`, `anomaly_days.csv`).

- **11 of the 13 outlier days are genuine seasonal peaks** (Sep to Dec, 70 to 131 orders, no single line above 18% of the day, `largest_line_share`).
- **Two outlier days are single-order events.** 2011-12-09 (£198,114, z = 13.6) has 85% of its revenue in one line, and 2011-01-18 (£94,395, z = 5.3) has 82% in one line. Both lines were reversed.

**Big orders later reversed but still counted in revenue:** 5 lines, £306,981 in total (`reversed_big_orders_value`, `anomaly_reversed_orders.csv`):

| Sale | Date | Product | Qty | Value | Cancelled by | Delay |
|---|---|---|---|---|---|---|
| 581483 | 2011-12-09 | PAPER CRAFT, LITTLE BIRDIE | 80,995 | £168,470 | C581484 | 12 min |
| 541431 | 2011-01-18 | MEDIUM CERAMIC TOP STORAGE JAR | 74,215 | £77,184 | C541433 | 16 min |
| 556444 | 2011-06-10 | PICNIC BASKET WICKER 60 PIECES | 60 | £38,970 | C556448 | 11 min |
| 530715 | 2010-11-04 | ROTATING SILVER ANGELS T-LIGHT HLDR | 9,360 | £15,818 | C536757 | 4 weeks |
| 540815 | 2011-01-11 | FAIRY CAKE FLANNEL ASSORTED COLOUR | 3,114 | £6,539 | C550456 | 3 months |

- **Impact:** £15,818 of this is in FY1 and £122,693 in FY2 (`reversed_orders_revenue_FY1`, `reversed_orders_revenue_FY2`). Excluding them cuts FY2 growth from 2.4% to 1.3% (`revenue_growth_excl_reversed`). The remaining £168,470 sits in the partial Dec 2011.
- The first three look like **keying errors** (absurd quantities or a £649.50 unit price, fixed within minutes). The last two look like genuine returns.

**Price outliers** (`anomaly_price_outliers.csv`): the largest is the picnic-basket line above (£649.50 vs a median of £5.95). The rest are small: FLAG OF ST GEORGE CAR FLAG sold singly at £1,157 and £868 against a £0.42 median, and lunch bags at about £5 against a £1.65 median (probably pack or retail pricing). Apart from the picnic basket, their revenue impact is under £1,200 per line.

## 10. Key findings

1. **Revenue was flat: +2.4% FY2 vs FY1 (£9.43M to £9.66M), and +1.3% excluding reversed bulk orders.** *(Evidence: `monthly.csv`, `revenue_growth_FY2_vs_FY1`, `revenue_growth_excl_reversed`)*
2. **Growth came from bigger orders, not more orders.** AOV rose 6.6% to £509 while orders fell 4.0%. *(Evidence: `monthly.csv`, `aov_growth`, `orders_growth`)*
3. **Identified customers spent 1.4% less. All net growth is in revenue without a Customer ID (+32.1%), so it can't be tied to any customer.** *(Evidence: `customer_lifecycle.csv`, `revenue_identified_growth`, `revenue_unidentified_growth`)*
4. **The business runs on a loyal core: 64% of customers were retained, the top 10% of customers bring 63.8% of identified revenue, and repeat buyers bring 96.2%.** Losing 1,531 FY1 customers put £1.06M of prior spend at risk. *(Evidence: `customer_lifecycle.csv`, `customer_concentration.csv`, `customer_retention_FY1_to_FY2`, `top_10pct_customer_share`, `repeat_customer_revenue_share`)*
5. **International markets are where the growth is (+12.1% vs +0.8% in the UK).** France, Germany and Australia are growing, while EIRE, the #2 market, fell 25.1%. *(Evidence: `countries.csv`, `non_uk_growth_FY2_vs_FY1`, `uk_growth_FY2_vs_FY1`)*
6. **Seasonality is severe: Sep to Nov delivers 37.2% of annual revenue, and peak 2011 was only flat on peak 2010 (Oct +0.8%, Nov +1.5%).** *(Evidence: `monthly.csv`, `peak_season_share_FY2`)*
7. **The rise in cancellation rate (2.5% to 3.1%) is one reversed order. Excluding reversed bulk orders, FY2 is 2.3%.** Product-level problems (the CHERRY LIGHTS range, PANTRY CHOPPING BOARD) are the real cancellation issue. *(Evidence: `monthly.csv`, `products_high_cancel.csv`, `cancel_rate_FY2`, `cancel_rate_FY2_excl_reversed`)*
8. **£306,981 of revenue sits on big orders that were later reversed, mostly keying errors cancelled within minutes. The approved definition still counts them.** *(Evidence: `anomaly_reversed_orders.csv`, `reversed_big_orders_value`)*

## 11. Caveats and open questions

- **Reversed orders in revenue.** The approved definition counts sales that were cancelled minutes later. Should the definition net out matched cancellations of keying errors? That decision belongs to the business, and this report doesn't change the definition.
- **Unidentified revenue.** 13.1% of revenue, growing 32%, has no Customer ID. What channel is it (guest checkout, marketplace, trade counter)? Customer metrics can't see it.
- **Customer "newness" in FY1.** Customers are only visible from Dec 2009, so FY1 "new" customers include long-standing accounts. Treat FY1 acquisition figures as an upper bound.
- **Partial Dec 2011.** Dec 2011 has 8 trading days and a £168K reversed order, so it's excluded from comparisons. Cohort ages that land in Dec 2011 understate retention.
- **Exact duplicates.** £57,093 (0.3%) of duplicate lines are kept per the definition (DQ §4). This is immaterial to the conclusions.
- **EIRE decline.** Is this one lost distributor? With only 3 identified customers, it's worth checking account by account.
- **Margins are unknown.** The data has no cost data, so a higher AOV may or may not mean higher profit.
