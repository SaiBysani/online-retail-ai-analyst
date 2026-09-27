"""Convert the raw Excel workbook into a single CSV, once.

Reading the 1M-row workbook with pandas is slow (a minute or more). Reading a CSV
takes seconds. So we convert once and every later analysis reads the CSV.

This is a faithful FORMAT CONVERSION ONLY:
- no cleaning, no de-duplication, no filtering, no type fixes;
- every row of both sheets is kept, in the original order;
- one column is added at the front, `source_sheet`, with the sheet name
  ("Year 2009-2010" or "Year 2010-2011"), because the two sheets overlap
  slightly and you may want to tell them apart later.

Invoice, StockCode and Customer ID are read as text so nothing gets mangled
(e.g. Customer ID stays "13085", not "13085.0"). Blank cells stay blank.

Input:  data/raw/online_retail_II.xlsx      (never modified)
Output: data/processed/online_retail_II.csv (UTF-8, gitignored)

Usage (from the repo root):
    python scripts/prepare_data.py           # skips if the CSV is up to date
    python scripts/prepare_data.py --force   # rebuild anyway
"""

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_FILE = REPO_ROOT / "data" / "raw" / "online_retail_II.xlsx"
OUT_FILE = REPO_ROOT / "data" / "processed" / "online_retail_II.csv"
SHEETS = ["Year 2009-2010", "Year 2010-2011"]

# Columns that look numeric but are really identifiers: keep them as text.
TEXT_COLUMNS = {"Invoice": str, "StockCode": str, "Customer ID": str}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="rebuild even if the CSV is up to date")
    args = parser.parse_args()

    if not RAW_FILE.exists():
        print(f"ERROR: {RAW_FILE.relative_to(REPO_ROOT)} not found.")
        print("Run this first:  python scripts/download_data.py")
        return 1

    # Skip the slow step if the CSV already exists and is newer than the workbook.
    if OUT_FILE.exists() and OUT_FILE.stat().st_mtime > RAW_FILE.stat().st_mtime and not args.force:
        print(f"{OUT_FILE.relative_to(REPO_ROOT)} is already up to date. Nothing to do.")
        print("Use --force to rebuild it.")
        return 0

    start = time.time()
    frames = []
    for sheet in SHEETS:
        print(f"Reading sheet '{sheet}' (this takes a while)...")
        df = pd.read_excel(RAW_FILE, sheet_name=sheet, dtype=TEXT_COLUMNS)
        df.insert(0, "source_sheet", sheet)  # remember where each row came from
        print(f"  {len(df):,} rows")
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)  # sheet 1 rows first, then sheet 2
    print(f"Total: {len(combined):,} rows")

    # Write to a temporary file first, then rename, so a crash never leaves
    # a half-written CSV that looks "up to date".
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = OUT_FILE.with_suffix(".csv.part")
    combined.to_csv(tmp_file, index=False, encoding="utf-8", date_format="%Y-%m-%d %H:%M:%S")
    tmp_file.replace(OUT_FILE)

    size_mb = OUT_FILE.stat().st_size / 1e6
    print(f"Wrote {OUT_FILE.relative_to(REPO_ROOT)} ({size_mb:.1f} MB) in {time.time() - start:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
