# Review: data quality, business and customer reports (pre-leadership)

Reviewer: reviewer agent, 2026-09-27. Reviewed: `outputs/data_quality_report.md` (+ `data_quality_checks.json`), `outputs/business_analysis.md` (+ `outputs/analysis/`), `outputs/customer_analysis.md` (+ `outputs/customers/`), and `outputs/executive_summary.md`. That summary is from the Day 3 commit 0fd0626 and has not been regenerated.

Evidence: `scripts/review_recheck.py` (run with `.venv/bin/python`). It is an independent pandas implementation of the CLAUDE.md definition and does **not** import `retail_common` or any other project script.

## Verdict: **ready after fixes** (not ready as-is)

Every headline number I recomputed matches to rounding, and the revenue definition is implemented correctly. Three things must be fixed before leadership sees these reports:

1. The "new-customer acquisition fell / new customers repeat less" claims are a data-window artefact.
2. The top of the "£0.26M-£0.34M at stake" range includes a £77k order that was reversed within 16 minutes.
3. `executive_summary.md` is stale and contradicts the current business report.

## Definitions check

- **`scripts/retail_common.py` matches CLAUDE.md line by line:**
  - C and A invoices are excluded.
  - Quantity <= 0 and Price <= 0 rows are excluded.
  - All 18 non-product codes plus the `gift_0001_` prefix are excluded.
  - The overlap drops `Year 2010-2011` rows dated <= 2010-12-09 20:01.
  - FY bounds are [2009-12-01, 2010-12-01) and [2010-12-01, 2011-12-01), so the partial Dec 2011 is outside both FYs.
- **Scripts:** `retail_analysis.py`, `customer_analysis.py` and `data_quality.py` all import `retail_common`. No report uses `scripts/analyze_business.py` (grep of `outputs/*.md`: no hits).
- **Partial Dec 2011:** it is correctly excluded from every FY comparison. My recheck puts Dec 2011 at £615,493, outside FY1 and FY2. The biggest reversal (581483, £168,470) is in Dec 2011, so it does not affect FY growth. The reports say this correctly.
- **Negative quantities:** all 22,557 are classified in DQ §5 as cancellations or price-£0 stock adjustments, with 0 unexplained. None are interpreted as sales.

## Recheck table

My assumptions are listed in the `review_recheck.py` docstring:
- approved revenue definition as above;
- FY1 = Dec09-Nov10, FY2 = Dec10-Nov11;
- order = distinct revenue invoice;
- cancellation rate = product-code C value / (revenue + that value);
- customers = revenue rows with a Customer ID;
- repeat = 2+ distinct purchase days;
- at-risk rule re-implemented from the stated definition (top 20% by M, 2+ days, recency to 2011-12-10 > 2x median gap and > 90 days).

| Metric | Reported | Source | Recomputed | Match |
|---|---|---|---|---|
| Revenue rows / total revenue | 1,015,071 / £19,700,954 | DQ §2, `revenue_total` | 1,015,071 / £19,700,954.44 | yes |
| FY1 revenue | £9,429,521 | `revenue_FY1` | £9,429,521.38 | yes |
| FY2 revenue | £9,655,940 | `revenue_FY2` | £9,655,939.79 | yes |
| FY2 vs FY1 | +2.4% | `revenue_growth_FY2_vs_FY1` | +2.40% | yes |
| Three 24h reversals | £284,623 | `reversed_24h_value` | £284,623.20 (541431 £77,183.60 FY2; 556444 £38,970 FY2; 581483 £168,469.60 Dec11) | yes |
| FY2 excl. 24h reversals / growth | £9,539,786 / +1.2% | `revenue_FY2_excl_reversed_24h`, `revenue_growth_excl_reversed_24h` | £9,539,786.19 / +1.17% | yes |
| Orders FY1 / FY2 | 19,743 / 18,957 (-4.0%) | `orders_*` | 19,743 / 18,957 (-3.98%) | yes |
| AOV FY1 / FY2 | £477.61 / £509.36 (+6.6%) | `aov_*` | £477.61 / £509.36 (+6.65%) | yes |
| AOV FY2 excl. reversals | £503.29 | `aov_FY2_excl_reversed_24h` | £503.29 | yes |
| Cancellation rate FY1 / FY2 | 2.5% / 3.1% | `cancel_rate_FY1/FY2` | 2.49% / 3.06% | yes |
| Cancellation rate FY2 excl. reversals | 2.3% | `cancel_rate_FY2_excl_reversed_24h` | 2.33% | yes |
| Identified revenue FY1 → FY2 | £8,363,874 → £8,247,836 (-1.4%) | `revenue_identified_growth` | same (-1.39%); -2.78% excl. reversals | yes |
| No-ID revenue FY1 → FY2 | £1,065,647 → £1,408,104 (+32.1%) | `revenue_unidentified_growth` | same (+32.14%) | yes |
| Top country / UK share | UK £16,856,331, 85.6% | `countries.csv`, `uk_revenue_share` | UK £16,856,331, 85.56% | yes |
| UK growth / excl. reversals / international | +0.8% / -0.6% / +12.1% | `uk_growth_*`, `non_uk_growth_FY2_vs_FY1` | +0.82% / -0.61% / +12.11% | yes |
| Customers / identified revenue | 5,852 / £17,124,941 (86.9%) | `customers`, `revenue_identified` | 5,852 / £17,124,940.98 (86.92%) | yes |
| Top 1% / 10% / 20% share | 32.0% / 63.8% / 77.1% | `concentration.csv` | 32.01% / 63.78% / 77.08% (59 / 585 / 1,170 customers) | yes |
| Repeat rate / repeat revenue share | 71.4% / 96.2% | `repeat_customer_rate` | 71.41% / 96.23% | yes |
| Champions | 22.6% of customers / 68.6% of revenue | `rfm_segments.csv` | 1,321 / 5,852 = 22.57%, £11,744,645 = 68.58%. This is internally consistent from `customers_rfm.csv`, and every Champion meets R>=4, F>=4, M>=4. **The quintile scoring itself was not reproduced independently.** | yes (consistency only) |
| High-value at risk | 151; £1,204,188 lifetime; £339,546 FY2 | `high_value_at_risk_*` | 151; £1,204,187.73; £339,546.07. Of the FY2 figure, £77,183.60 is customer 12346's reversed order; 112 of the 151 bought in FY2; last-365-day revenue is £311,825 | yes (but see B2) |
| 180-day repeat, H1 2011 vs H1 2010 | 53.1% (n=642) vs 63.3% (n=2,000) | `repeat_by_acquisition_fy.csv` | 53.12% (642) vs 63.30% (2,000) | yes (but see B1) |
| Multi-country customers | 12 (customer) vs 13 (DQ, business) | `customers_multi_country`, DQ §9 | 12 on revenue rows, 13 on all rows | both correct on their own basis (see S3) |

## Issues

### Blocking

**B1. "Acquisition slowed" and "FY2 new customers came back less often" are artefacts of the data window.** *Owner: customer-analyst and business-analyst.*
- **Where:**
  - `customer_analysis.md` §6 finding 5 and §5 last-but-one bullet ("642 vs 2,000", "53.1% vs 63.3%").
  - `business_analysis.md` §5 bullet 3 ("New customers per month fell from 163-441 ... to 72-221") and §10 finding 3 ("New customer acquisition also slowed").
- **What's wrong:** a 2010 customer is "new" if not seen since 2009-12-01, which is only 1 month of look-back. A 2011 customer is "new" only if not seen in the previous 12-13 months. Existing accounts that simply didn't order in Dec 2009 are counted as 2010 "new customers". The median usual gap is 64 days, so there are many of them, and they are established buyers who repeat more.
- **Evidence (`review_recheck.py`, "Acquisition cohorts" and "New customers per month"):** apply the same 1-month look-back to 2011, counting customers not seen since 2010-12-01.
  - The H1 2011 cohort becomes **1,949 customers with a 62.3% 180-day repeat rate**, against 2,000 and 63.3% for H1 2010. That is essentially the same.
  - 1,307 of those 1,949 had bought in FY1, so they were not new.
  - Monthly counts on the same basis are 416/380/452/300/284/242 (Jan-Jun 2011) against 368/375/441/294/255/267 (2010), so there is no slowdown.
  - The 2011 figures (642, 53.1%) measure genuinely new customers. The 2010 figures mostly measure reactivations. The data cannot measure true 2010 acquisition.
  - The customer report mentions this as "one caveat", but the headline finding states the gap as fact. CLAUDE.md and the DQ report both warn about first-month "new" customers.
- **Fix:**
  - Withdraw both claims.
  - Replace them with this: "FY2 brought 1,585 customers not seen in the prior 12 months. A comparable FY1 figure cannot be computed because the data starts in Dec 2009."
  - If a trend is wanted, compare Jun-Nov 2011 against Jun-Nov 2010 using a fixed look-back that both years can support (for example 6 months). Report it as indicative only.

**B2. The upper end of the "£0.26M-£0.34M of annual revenue at stake" range includes a £77k order known to be reversed.** *Owner: customer-analyst.*
- **Where:** `customer_analysis.md` §6 finding 2 and the §4 table ("Their FY2 revenue (annual £ at stake) £339,546").
- **What's wrong:**
  - £77,183.60 of the £339,546 is customer 12346's invoice 541431, cancelled 16 minutes later. That is 23% of the figure (recheck: `at_risk_FY2_from_12346`). The same report calls 12346 "not a real at-risk account".
  - 15749's £44,534 is one order that was partly returned after 3 months.
  - Calling FY2 revenue "annual revenue at stake" assumes all of it is lost. 112 of the 151 customers bought in FY2, and their last-365-day revenue is £311,825.
  - "151 high-value customers are lapsing" presents a rule-based threshold as a fact. The report's own grid gives 27-207 customers, and the rule is unvalidated (§7).
- **Fix:**
  - Lead with **£263,703** (the basis that excludes reversed sales), or at least exclude 12346 from the default list.
  - Label the figure "FY2 revenue from customers meeting the at-risk rule (upper bound if all were lost)".
  - Reword "are lapsing" to "meet our at-risk rule (count ranges from 27 to 207 depending on thresholds)".

**B3. `executive_summary.md` is stale and contradicts the current reports. Do not send it to leadership until it is regenerated.** *Owner: whoever runs the executive-summary skill (business-analyst).*
- **Where and evidence:**
  - Line 4 and the KPI table say "+1.3% excl. reversed orders", citing the legacy key `revenue_growth_excl_reversed`. That uses the wider any-lag rule (my recheck gives 1.27%). The current business report uses the 24h rule: +1.2%.
  - Risk 2 says "£307K" (`reversed_big_orders_value`), while the business and DQ reports lead with £284,623.
  - Risk 2 says "Three were apparent keying errors ... (up to £168K each)". The £168K one (581483) is in Dec 2011 and does not affect FY2 growth at all.
  - Change 3 says "The whole net gain (+£342K) came from untracked sales". **The net gain is +£226,418.** +£342,457 is the increase in no-ID revenue, which offset a -£116,038 fall in identified revenue (recheck: `delta_*`). As written, the number is wrong.
  - It contains no customer-analysis findings at all.
- **Fix:** regenerate it from the corrected `business_analysis.md` and `customer_analysis.md`, using only the `*_24h` keys.

### Should fix

**S1. The no-Customer-ID growth claim is arithmetically correct but needs context.** *Owner: business-analyst.*
- **Where:** `business_analysis.md` §2 Reading, §5 bullet 4, §10 finding 3, §11.
- **Check:** confirmed. Total +£226,418 = no-ID +£342,457 + identified -£116,038. "All growth sits in no-ID revenue" is fair as arithmetic.
- **Context the report does not give (recheck):**
  - No-ID **invoices fell** from 1,551 to 1,331 (-14%), while the value rose 32%, so the average no-ID invoice went from about £687 to about £1,058.
  - The rise is all UK: +£348,759 UK and -£6,302 international.
  - It peaks in Dec 2010 (27.1% of that month's revenue, against 15.0% in Dec 2009) and Nov 2011 (21.6%).
  - Fewer, larger invoices do not fit well with the "new buyers / guest checkouts" explanation in §5 and §11. Either way, the cause is unknown.
- **Fix:** add these facts. Keep the "cannot tell why" framing. Avoid implying that identified customers' decline is real until data capture is ruled out; §11 already hints at this, so promote it to the finding.

**S2. Two different "reversed" scopes are used without saying which.** *Owners: business-analyst (metrics.json) and customer-analyst (report wording).*
- **Where:** `business_analysis.md` uses the 3 lines of £5,000 or more (£284,623). `customer_analysis.md` "excl. reversed" views (top 1% 31.2%, the £263,703 at-risk figure, top 20% changes) use all 1,444 24h-matched lines (£403,195). `metrics.json` also still carries the legacy keys `revenue_growth_excl_reversed` (1.27%) and `cancel_rate_FY2_excl_reversed` (2.26%, any-lag rule) next to the `*_24h` keys. The exec summary picked those up (B3).
- **Fix:**
  - Each report should name its scope wherever it says "excl. reversed", for example "excl. the 3 same-day reversals of £5k+ (£284,623)" or "excl. all 1,444 same-day reversed lines (£403,195)".
  - Drop or rename the legacy keys in `metrics.json`.

**S3. Stale cross-references and the multi-country count.** *Owner: business-analyst.*
- **Where:**
  - `business_analysis.md` line 118 says segmentation "is being produced by customer-analyst". The report now exists, so link it and cite its headline figures.
  - Line 31 says "The 13 customers who appear under more than one country contribute revenue to each country". On revenue rows it is **12**. The 13th only has cancellation rows under a second country (recheck: 12 revenue rows, 13 all rows).
  - `customer_metrics.json` assumption text also says "13 customers have >1" while its own metric says 12.
- **Fix:** change line 31 to 12, or say "13 including cancellation rows". Update the reference on line 118 (and line 217). The customer-analyst should fix the JSON assumption text.

**S4. Different "repeat interval" figures for the same idea.** *Owners: business-analyst and customer-analyst.*
- **Where:** `business_analysis.md` §6 and finding 8 say "returns every 80 days ... roughly quarterly" (mean-gap basis). `customer_analysis.md` §5 and finding 3 say "about 2 months" (63-day first-to-second gap, 64-day median usual gap).
- **Fix:** both are computed correctly, but leadership will see a contradiction. Pick one (the 64-day median usual gap is the more robust), and footnote the other.

**S5. Causal and characterising wording that the data cannot support.** *Owner: business-analyst.*
- "Cabinets and clocks ... cancel at 14-20%, which **suggests quality or delivery issues**" (§4). Cancellation reasons are not in the data.
- "loyal **wholesale** buyers" (§10 finding 8, §6) and "consistent with export wholesale buyers" (§7). There is no customer-type field, and the customer report asks for one as an open question.
- **Fix:** rephrase as hypotheses ("could reflect ..."), or drop them.

### Notes

- **N1.** `outputs/analysis/anomaly_reversed_orders.csv` row 4 pairs 556444 with **C556448**. That line is 60 x £4.95 = £297 and reverses invoice 556442. The true reversal of 556444 is **C556445** (manual `M`, £38,970), as the DQ report §10 says (recheck output). The totals are unaffected. Relatedly, `customer_analysis.md` §2 says "£39,267 was reversed via invoice 556444 and a manual M line". It is actually £38,970 on 556444 (via C556445) plus £297 on 556442 (via C556448). *Owners: business-analyst (matching rule should also require the same price) and customer-analyst (wording).*
- **N2.** `business_analysis.md` gives product cancellations as "3.7% of revenue" in §1 and as a "cancellation rate of 3.5%" in §8. Both are right (£719,656 / revenue = 3.65%; / (revenue + cancellations) = 3.52%), but they use different denominators. Label the difference or use one. *Owner: business-analyst.*
- **N3.** The "Jan-Jun 2011" cohort actually covers 1 Jan to 13 Jun 2011, because of the 180-day eligibility cut-off (latest first purchase 2011-06-13 in the recheck). Say so in `customer_analysis.md` §5. *Owner: customer-analyst.*
- **N4.** RFM segment shares (Champions 68.6%) depend on the chosen rule table, and F is not a true quintile (F=1/2/3 are exactly 1/2/3 days). Both points are disclosed in §1. When presenting, describe the shares as outputs of these rules, not as natural groups. *Owner: customer-analyst.*
- **N5.** "The apparent rise in cancellations ... is an artefact of the reversed orders" (`business_analysis.md` finding 6) is supported: FY1 2.49% against FY2 2.33% excl. reversals (recheck). FY1 contains no 24h reversal of £5,000 or more, so the comparison is fair.
- **N6.** Small bases: the business report flags these correctly (Australia +365%, EIRE 3 customers, Netherlands 22), and I have no further issue.

## Open questions for the user

1. **Reversed orders:** should the 3 same-day reversals (£284,623) or all 1,444 reversed lines (£403,195) be excluded from approved revenue? Until you decide, which scope should be the standard sensitivity line in every report?
2. **No-Customer-ID revenue:** do you know what changed in Dec 2010 and Nov 2011? For example, a trade counter, a new sales channel, or a checkout change. The fewer-but-larger no-ID invoices suggest something other than guest retail buyers.
3. **Executive summary:** should it be regenerated from both corrected reports, with customer findings included?
4. I did not independently reproduce the RFM quintile scoring. I only checked that the segment table is consistent with `customers_rfm.csv`. Tell me if you need that before the review.

## Resolution (applied 2026-09-27, main session)

The fixes were applied directly; the reports were not sent back to the analysts.

| Issue | Resolution |
|---|---|
| B1 | Acquisition-slowdown and new-customer repeat claims withdrawn from `business_analysis.md` §5 and §10 finding 3, and from `customer_analysis.md` §5 and §6 finding 5. They are replaced by "1,585 customers not seen in the prior 12 months; no comparable FY1 figure", with the equal look-back evidence. |
| B2 | `customer_analysis.md` §4 and finding 2 now lead with 150 customers / £263,703 (the basis without reversed sales, which removes 12346), label it an upper bound, and say "meet our at-risk rule (27-207)". |
| B3 | `executive_summary.md` regenerated from both corrected reports using only the `*_24h` keys, with customer findings included. |
| S1 | No-ID invoice counts, UK split and monthly peaks added to `business_analysis.md` §5, finding 3 and §11. |
| S2 | Each report states its reversal scope. The old any-lag keys in `metrics.json` are renamed `*_excl_reversed_any_lag`, `reversed_any_lag_*` and `reversed_any_lag_value` (`scripts/retail_analysis.py`). |
| S3 | Cross-references to `customer_analysis.md` updated. Multi-country count is 12 (13 incl. cancellation rows) in `business_analysis.md` §1 and in the `customer_metrics.json` assumption text. |
| S4 | Both reports lead with the 64-day median usual gap; the business report footnotes 79.7 days. |
| S5 | "Quality or delivery issues" and "wholesale" wording removed or reworded as unknown. |
| N1 | Reversal matching in `retail_analysis.py` now requires the same price, or a manual `M` line of the same value: 556444 → C556445. As a result, 530715 is no longer a match (C536757 credited £281 at £0.03/unit, not £15,818). Any-lag value is now £291,163. The standard 24h figures are unchanged, apart from `cancel_rate_FY2_excl_reversed_24h`: 0.02325 → 0.02328. |
| N2 | `business_analysis.md` §8 labels the 3.5% (of revenue + cancellations) vs 3.7% (of revenue) bases. |
| N3 | Cohort window stated as 1 Jan-13 Jun 2011 in `customer_analysis.md` §5. |
| N4 | Segment-shares caveat added to `customer_analysis.md` §7. |
