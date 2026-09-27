---
name: retail-analysis
description: Full business analysis of the Online Retail II data - revenue, monthly trends and seasonality, products, customers and retention, countries, cancellations, repeat purchases and anomalies - saved as outputs/business_analysis.md, then summarised for leadership. Use when asked for a business analysis, business health report, performance review, or a refresh of the analysis after the data or definitions change. Runs the data-quality skill first and the executive-summary skill last. For a single quick number (e.g. revenue for one country) run a script directly instead.
---

# Retail business analysis

End-to-end pipeline: data quality → analysis tables → written report → executive summary.

All calculations live in `scripts/retail_analysis.py` (tables and headline metrics) on top of `scripts/retail_common.py` (the CLAUDE.md definitions). Do not use `scripts/analyze_business.py` for figures: it predates CLAUDE.md and uses a different product and duplicate rule.

## Rules

- Follow CLAUDE.md: approved revenue definition only; C invoices are cancellations, never revenue; never modify `data/raw/`; save outputs in `outputs/`.
- State the assumptions before presenting any metric (step 3).
- Every conclusion in the report must cite its evidence: a table file in `outputs/analysis/` and/or a metric key in `outputs/analysis/metrics.json`. No number may appear that isn't in those files or in the data-quality report.
- If you need a number the script doesn't produce, add it to `scripts/retail_analysis.py`, re-run it, and cite the new output. Don't compute it in an ad-hoc snippet.

## Steps

1. **Run the data-quality skill first** (invoke `data-quality` with the Skill tool). If its verdict is "no" or any check is FAIL, stop and report the blocking issue instead of analysing.

2. **Run the analysis script.**
   ```bash
   .venv/bin/python scripts/retail_analysis.py
   ```
   It writes `outputs/analysis/metrics.json` (headline metrics, each with its definition and source table, plus the assumptions and the revenue filter audit) and one CSV per topic in `outputs/analysis/`. It takes about 10 seconds.

3. **Read everything before writing.** Read `metrics.json` in full, then the CSVs you need. Key tables:

   | Topic | Tables |
   |---|---|
   | Revenue and monthly trend | `monthly.csv` (revenue, orders, customers, new customers, AOV, cancellations, YoY, trading days) |
   | Products | `products.csv` (with ABC class and per-product cancel rate), `product_movers.csv`, `products_high_cancel.csv` |
   | Customers | `customer_concentration.csv`, `customer_lifecycle.csv`, `cohort_retention.csv` |
   | Repeat purchases | `repeat_purchases.csv` |
   | Countries | `countries.csv` |
   | Cancellations | `monthly.csv`, `countries.csv`, `products_high_cancel.csv` |
   | Anomalies | `anomaly_days.csv`, `anomaly_top_lines.csv`, `anomaly_reversed_orders.csv`, `anomaly_price_outliers.csv` |

   Look for the story behind the numbers. For example, check whether total revenue and identified-customer revenue move in the same direction, what drives growth (orders vs AOV, UK vs non-UK, new vs retained customers), and whether large orders were later reversed.

4. **Write `outputs/business_analysis.md`** (this replaces any earlier version). Structure:
   1. **Title and scope**: data period, source, date generated, and "Revenue follows the approved CLAUDE.md definition".
   2. **Assumptions**: the `assumptions` list from `metrics.json`, plus the data-quality caveats that affect interpretation (link `data_quality_report.md`).
   3. **Headline scorecard**: FY1 vs FY2 table (revenue, orders, AOV, customers, cancellation rate, UK share) with the change.
   4. **Revenue and monthly trends**: growth, seasonality (peak season share), YoY by month. Don't compare the partial Dec 2011 with full months.
   5. **Products**: concentration (ABC), top products, biggest risers and fallers, products with unusually high cancellation.
   6. **Customers**: concentration, new vs retained, retention FY1→FY2, cohort retention, revenue without a Customer ID.
   7. **Repeat purchases**: repeat rate, revenue share from repeat buyers, purchase frequency bands, typical gap between purchases.
   8. **Countries**: UK vs international, growth by market, AOV differences, country cancellation rates.
   9. **Cancellations**: level and trend, where they concentrate, and how they're treated.
   10. **Anomalies**: outlier days, large reversed orders still counted in revenue, price outliers, and what each means for the numbers above.
   11. **Key findings**: 5-8 numbered findings, each ending with *(Evidence: `table.csv`, `metric_key`)*.
   12. **Caveats and open questions**.

   Style: lead each section with the finding, not the method. Format money as £ with thousands separators and percentages to one decimal. Keep tables short (top 10). Cite evidence inline in every section.

5. **Check the report.** Spot-check at least five numbers in the report against `metrics.json` or the CSVs. Confirm that every finding has an evidence pointer and that nothing counts cancellations as revenue.

6. **Run the executive-summary skill** (invoke `executive-summary` with the Skill tool) to produce `outputs/executive_summary.md`.

7. **Report back** in chat: 3-5 headline findings with their numbers, and the paths to `data_quality_report.md`, `business_analysis.md` and `executive_summary.md`.
