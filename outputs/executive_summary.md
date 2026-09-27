# Executive Summary: Online Retail, FY2 (Dec 2010 to Nov 2011) vs FY1
_Final, 2026-09-27. Built from outputs/business_analysis.md and outputs/customer_analysis.md after the corrections in outputs/review.md were applied. Every headline number was independently rechecked. Revenue follows the approved definition in CLAUDE.md._

**Bottom line:** Sales were essentially flat, up 2.4% to £9.66M, or 1.2% once three large orders cancelled within minutes are taken out. Customers placed fewer, larger orders. International markets grew while the UK stood still. All of the net gain came from sales with no customer on record, and revenue depends heavily on a small base of repeat customers.

## 5 KPIs

| KPI | FY1 | FY2 | Change | Evidence |
|---|---|---|---|---|
| Revenue | £9.43M | £9.66M | +2.4% (+1.2% excl. 3 reversed orders) | `revenue_FY1`, `revenue_FY2`, `revenue_growth_excl_reversed_24h`; business §2 |
| Average order value | £478 | £509 | +6.6% (+5.4% excl. reversals); orders −4.0% | `aov_FY1`, `aov_FY2`, `aov_growth`, `orders_growth`; business §2 |
| Active identified customers | 4,239 | 4,293 | +1%; 63.9% of FY1 customers bought again | `customers_FY1`, `customers_FY2`, `customer_retention_FY1_to_FY2`; business §5 |
| Top 10% customers' share of identified revenue | 63.8% (whole period) | | Top 1% (59 customers) = 32.0% | `top_10pct_customer_share`, `top_1pct_customer_share`; customer §2 |
| Cancellation rate | 2.5% | 3.1% (2.3% excl. reversals) | +0.6 pts reported, −0.2 pts underlying | `cancel_rate_FY1`, `cancel_rate_FY2`, `cancel_rate_FY2_excl_reversed_24h`; business §8 |

## 3 important changes

1. **Bigger baskets, fewer orders: order value up 6.6%, orders down 4.0%.** All of the growth came from customers spending more per order, not from ordering more often. *Evidence: `aov_growth`, `orders_growth`, `monthly.csv`; business §2.*
2. **International up 12.1% while the UK was flat (+0.8%, or −0.6% underlying).** The UK is 86% of revenue. France, Australia, Germany and Spain led the international growth, but several markets grew from small bases or depend on a few accounts. *Evidence: `non_uk_growth_FY2_vs_FY1`, `uk_growth_FY2_vs_FY1`, `uk_growth_excl_reversed_24h`, `countries.csv`; business §7.*
3. **Sales to known customers fell 1.4% (−2.8% underlying), while sales with no customer on record rose 32% to £1.41M.** The no-ID increase (+£342K) is more than the whole net gain (+£226K). Those sales came from *fewer* invoices (−14%), were all in the UK, and peaked in Dec 2010 at 27% of that month's revenue. That looks more like a few large unrecorded accounts or a change in how orders are captured than like new guest buyers. *Evidence: `revenue_identified_growth`, `revenue_identified_growth_excl_reversed_24h`, `revenue_unidentified_growth`, `customer_lifecycle.csv`; business §2, §5 (invoice counts and monthly shares from `scripts/review_recheck.py`).*

## 3 risks

1. **Heavy reliance on repeat customers, some of whom are going quiet.** Repeat customers bring in 96% of identified revenue, and the "Champions" segment (23% of customers) brings in 69%. 150 high-value accounts meet the at-risk rule, having gone unusually long without an order. They spent up to £264K in FY2; treat that as an upper bound, not a forecast. The count ranges from 27 to 207 depending on thresholds. *Evidence: `repeat_customer_revenue_share`, `segment_revenue_share_champions`, `high_value_at_risk_customers_excl_reversed`, `high_value_at_risk_revenue_FY2_excl_reversed_basis`, `at_risk_count_range`, `high_value_at_risk.csv`; customer §3, §4.*
2. **£285K of reported revenue is three orders cancelled within minutes (£403K across all 1,444 same-day reversed lines).** The approved definition keeps them. They make FY2 growth look twice as strong (2.4% vs 1.2%), create an apparent rise in cancellations, and put orders that never really happened into the product and customer top lists (for example the £168K order on 9 Dec 2011, which falls outside both financial years). *Scope used here: "underlying" or "excl. reversals" means the three £5K+ orders unless stated.* *Evidence: `reversed_24h_value`, `reversed_value_identified`, `anomaly_reversed_orders.csv`, `reversed_by_customer.csv`; business §9; customer §2.*
3. **Seasonal dependence: Sep–Nov is 37% of the year, and peak 2011 was flat on peak 2010** (Oct +0.8%, Nov +1.5%). Without the reversals, every month from Dec 2010 to Apr 2011 was down year on year. A weak autumn can't be made up later. *Evidence: `peak_season_share_FY1`, `peak_season_share_FY2`, `revenue_yoy_excl_reversed_24h` in `monthly.csv`; business §3.*

## Questions for leadership

1. Should orders cancelled within minutes (apparent keying errors) be taken out of reported revenue? If so, should that be only the 3 large ones (£285K) or all same-day reversals (£403K)? Either would change the approved definition. (Risk 2)
2. What are the sales with no customer on record: a trade counter, a marketplace, or large accounts not being captured? They are 13% of revenue and grew 32%. (Change 3)
3. Should Sales start a win-back programme for the at-risk high-value accounts, starting with the largest confirmed ones? (Risk 1)
4. Is international growth a strategy we should fund, given that some markets depend on a handful of accounts? (Change 2)

## Basis and caveats

- Period: FY1 = Dec 2009–Nov 2010, FY2 = Dec 2010–Nov 2011. The partial Dec 2011 (8 trading days, £615K) is excluded from comparisons. Revenue is gross of returns (£720K of product cancellations).
- Customer figures cover the 87% of revenue that has a Customer ID. New-customer acquisition and early repeat rates can't be compared year on year, because the data starts in Dec 2009. The apparent slowdown disappears on a like-for-like basis, so it is not reported (business §5, customer §5).
- Data verdict: fit for analysis with caveats ([data_quality_report.md](data_quality_report.md)). Every headline number was independently rechecked ([review.md](review.md)).
