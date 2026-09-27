---
name: data-quality
description: Run the data-quality checks on the Online Retail II data (schema, row counts, nulls, duplicates and the sheet overlap, negative quantities, zero/negative prices, cancellations, date ranges, suspicious values) and save outputs/data_quality_report.md. Use before any analysis or metric on this dataset, when the processed CSV has been rebuilt, when asked whether the data is clean or trustworthy, or when a number looks off and you need to rule out a data problem. The retail-analysis skill runs this first.
---

# Data quality check

Produces `outputs/data_quality_report.md` (human-readable) and `outputs/data_quality_checks.json` (one record per check). All calculations live in `scripts/data_quality.py`; shared definitions live in `scripts/retail_common.py`, which implements the CLAUDE.md business definitions. Do not re-implement checks inline.

## Rules

- Read `data/processed/online_retail_II.csv` only. Never modify anything in `data/raw/` or `data/`.
- Do not change the approved revenue definition. If a check suggests it is wrong, say so in the notes and ask; don't silently apply a different rule.
- Every statement in the notes must cite the report section (e.g. "see §4 Duplicates") or a key in `data_quality_checks.json`.

## Steps

1. **Check inputs.** Confirm `data/processed/online_retail_II.csv` exists. If not, stop and tell the user to run `python scripts/prepare_data.py` (see README). Use the project venv: `.venv/bin/python` (or `python` if it is activated).

2. **Run the checks.**
   ```bash
   .venv/bin/python scripts/data_quality.py
   ```
   It prints a status table (PASS / WARN / FAIL per check) and writes both files. It takes about 10 seconds.

3. **Read the results.** Read `outputs/data_quality_report.md` in full and `outputs/data_quality_checks.json`.

4. **Investigate before interpreting.** For each WARN or FAIL, make sure the report explains it. In particular:
   - *Negative quantities* (CLAUDE.md rule): confirm every negative row is classified (cancellation, price-0 stock adjustment, or bad-debt adjustment) and `unexplained_negative_rows` is 0. If not, look at the unexplained rows directly and describe what they are.
   - *Duplicates*: confirm `overlap_copies_identical` is true. Note how much revenue sits on the remaining exact duplicates, which the approved definition keeps.
   - *Suspicious values*: note the extreme orders that were cancelled minutes later and the non-standard stock codes (e.g. `DCGS*`) that stay in revenue.
   - If something needs a new check, add it to `scripts/data_quality.py` and re-run, rather than running a one-off query.

5. **Write the analyst notes.** Replace the line `<!-- ANALYST NOTES: filled in by the data-quality skill -->` in the report with 5-8 bullets:
   - one bullet per material issue: what it is, its size (rows and £), how the approved definition handles it, and the section it comes from;
   - which issues limit later analysis (e.g. missing Customer IDs exclude part of revenue from customer metrics; the partial last month; the first month making every customer "new");
   - a final bullet: **"Fit for analysis: yes / yes with caveats / no"**, with the reason.

6. **Handle FAILs.** If any check is FAIL, say so at the top of the notes and tell the user (or the calling skill) that analysis should not proceed until it is resolved.

7. **Report back** in chat: the status table, the fit-for-analysis verdict, and the path to the report. Keep it short; the details are in the file.
