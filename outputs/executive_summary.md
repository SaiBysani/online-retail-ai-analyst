# Executive Summary: Online Retail, FY2 (Dec 2010 to Nov 2011) vs FY1
_Generated 2026-09-27 from outputs/business_analysis.md. Revenue follows the approved definition in CLAUDE.md._

**Bottom line:** Sales were essentially flat, up 2.4% to £9.66M, or just 1.3% once bulk orders that were entered and then cancelled are removed. Customers placed fewer but larger orders. International markets grew while the UK stood still, and the business still depends on a loyal core of repeat wholesale buyers.

## 5 KPIs

| KPI | FY1 | FY2 | Change | Evidence |
|---|---|---|---|---|
| Revenue | £9.43M | £9.66M | +2.4% (+1.3% excl. reversed orders) | `revenue_FY1`, `revenue_FY2`, `revenue_growth_excl_reversed`; §2 |
| Average order value | £478 | £509 | +6.6% (orders −4.0%) | `aov_FY1`, `aov_FY2`, `aov_growth`, `orders_growth`; §2 |
| Customer retention (FY1 customers buying again in FY2) | n/a | 63.9% | 1,531 customers lost | `customer_retention_FY1_to_FY2`, `customer_lifecycle.csv`; §5 |
| Revenue from repeat customers | 96.2% of identified revenue (whole period) | | | `repeat_customer_revenue_share`, `repeat_purchases.csv`; §6 |
| Cancellation rate | 2.5% | 3.1% (2.3% excl. reversed orders) | +0.6 pts (−0.2 pts underlying) | `cancel_rate_FY1`, `cancel_rate_FY2`, `cancel_rate_FY2_excl_reversed`; §8 |

## 3 important changes

1. **Bigger baskets, fewer orders: order value up 6.6%, orders down 4.0%.** All of the revenue growth came from customers spending more per order, not from more orders. *Evidence: `aov_growth`, `orders_growth`, `monthly.csv`; business_analysis.md §2.*
2. **International up 12.1%, UK up 0.8%.** France (+41%), Germany (+11%) and Australia (from £30K to £138K) led the growth, but Ireland, the second-largest market, fell 25%. *Evidence: `non_uk_growth_FY2_vs_FY1`, `uk_growth_FY2_vs_FY1`, `countries.csv`; §7.*
3. **Sales to known customers fell 1.4%, while sales with no customer on record rose 32%.** The whole net gain (+£342K) came from untracked sales that can't be linked to any customer. Retained customers spent less than the year before. *Evidence: `revenue_identified_growth`, `revenue_unidentified_growth`, `customer_lifecycle.csv`; §2, §5.*

## 3 risks

1. **Concentration on a small loyal base: the top 10% of customers bring 63.8% of identified revenue.** Losing a handful of large accounts would show up directly in sales. Last year's lost customers had spent £1.06M. *Evidence: `top_10pct_customer_share`, `customer_concentration.csv`, `customer_lifecycle.csv`; §5.*
2. **£307K of reported revenue sits on large orders that were later cancelled.** Three were apparent keying errors reversed within minutes (up to £168K each). The approved definition still counts them, which flatters FY2 growth (2.4% reported vs 1.3% underlying) and Dec 2011. *Evidence: `reversed_big_orders_value`, `reversed_orders_revenue_FY2`, `anomaly_reversed_orders.csv`; §9.*
3. **Seasonal dependence: Sep to Nov delivers 37.2% of the year, and peak 2011 was flat on peak 2010** (Oct +0.8%, Nov +1.5%). A weak autumn cannot be recovered later in the year. *Evidence: `peak_season_share_FY2`, `monthly.csv`; §3.*

## Questions for leadership

1. Should revenue reporting net out orders that are cancelled within minutes as keying errors? That would change the approved definition. (Risk 2)
2. What are the sales with no customer on record: guest checkout, a marketplace, or a trade counter? They are 13% of revenue and growing 32%. (Change 3)
3. Is the international growth a deliberate strategy we should fund, and what happened with the Ireland account(s)? (Change 2)
4. Do we have margin data? A higher order value only helps if it isn't coming from discounting on bulk orders. (Change 1)

## Basis and caveats

- Period: FY1 = Dec 2009 to Nov 2010, FY2 = Dec 2010 to Nov 2011. The partial Dec 2011 (8 trading days) is excluded from comparisons.
- Revenue excludes cancellations, bad-debt adjustments, postage and fees. Customer figures cover the 87% of revenue that has a Customer ID.
- Data verdict: fit for analysis with caveats. See [data_quality_report.md](data_quality_report.md).
