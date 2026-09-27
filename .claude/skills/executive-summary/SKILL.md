---
name: executive-summary
description: Turn the completed retail analysis into a one-page leadership brief - 5 KPIs, 3 important changes, 3 risks, the evidence behind each, and questions for leadership - saved as outputs/executive_summary.md. Use when asked for an executive summary, leadership or board update, KPI brief, or "the headline version" of the analysis. Needs outputs/business_analysis.md and outputs/analysis/metrics.json to exist; if they don't, run the retail-analysis skill instead (it ends by running this one).
---

# Executive summary

A one-page brief for leadership, built only from finished analysis. This skill does no new calculation: every number must already exist in the inputs below.

## Inputs

- `outputs/analysis/metrics.json`: headline metrics, each with a definition and source table. This is the source of truth for numbers.
- `outputs/business_analysis.md`: findings and context.
- `outputs/data_quality_report.md`: caveats (analyst notes section).
- The CSVs in `outputs/analysis/` when you need detail behind a metric.

If `metrics.json` or `business_analysis.md` is missing, or `metrics.json` is older than `data/processed/online_retail_II.csv`, stop and run the retail-analysis skill instead (don't run it from here if retail-analysis called you; tell the user the inputs are stale).

## Rules

- No new numbers. If a KPI you want isn't in `metrics.json`, add it to `scripts/retail_analysis.py` and re-run that script, or pick another KPI.
- Numbers must match `metrics.json` exactly (rounded for display only). Revenue always means the approved CLAUDE.md definition.
- Every KPI, change and risk has an **Evidence** pointer: the metric key and/or table file, plus the section of `business_analysis.md`.
- Write for a non-technical reader: plain words, no column names in the prose (they go in the evidence pointers), and £ figures rounded to £K or £M.
- Keep it to about one page. Leadership should be able to read it in two minutes.

## Steps

1. Read the inputs in full.

2. **Choose 5 KPIs** that together describe the health of the business. Prefer FY1 vs FY2 comparisons (full Dec-Nov years). A good default set is revenue, AOV or orders, active customers or retention, repeat-customer revenue share, and cancellation rate. Swap one if the analysis shows something more important (e.g. international growth or customer concentration).

3. **Choose 3 important changes**: the biggest movements between FY1 and FY2 that leadership should know about. Each gets what changed, by how much, and the likely driver according to the analysis.

4. **Choose 3 risks**: things that could hurt revenue or mislead decisions (e.g. customer concentration, retention decline, seasonality dependence, data gaps such as revenue without a Customer ID, reversed large orders inflating revenue). Each gets why it matters, its size in £ or %, and the evidence.

5. **Write 3-5 questions for leadership**: decisions or information only they can provide, each tied to a change or risk above (e.g. "Were the Dec 2011 bulk orders intentional test orders?", "Is the international growth a deliberate strategy we should fund?").

6. **Write `outputs/executive_summary.md`** in this structure:

   ```markdown
   # Executive Summary: Online Retail, FY2 (Dec 2010-Nov 2011) vs FY1
   _Generated <date> from outputs/business_analysis.md. Revenue follows the approved definition in CLAUDE.md._

   **Bottom line:** <two sentences>

   ## 5 KPIs
   | KPI | FY1 | FY2 | Change | Evidence |

   ## 3 important changes
   1. **<headline with number>.** <1-2 sentences.> *Evidence: `metric_key`, `table.csv`; business_analysis.md §<n>.*

   ## 3 risks
   1. **<headline with number>.** <why it matters.> *Evidence: ...*

   ## Questions for leadership
   1. ...

   ## Basis and caveats
   <3 bullets max: period, main assumptions, main data caveats (link data_quality_report.md).>
   ```

7. **Check it**: every number traces to `metrics.json` or a named table; there are exactly 5 KPIs, 3 changes and 3 risks; nothing contradicts `business_analysis.md`.

8. **Report back** in chat: the bottom line and the path to the file.
