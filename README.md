# online-retail-ai-analyst

A demo repo for a Claude Code tutorial series for data professionals. It is built on the UCI Online Retail II dataset: about 1.07 million invoice line items from a UK-based online retailer between 2009 and 2011 (invoices, products, quantities, prices, customers, countries). Each day of the series adds to this same repo.

## Setup

Requires Python 3 and Git.

```bash
git clone https://github.com/SaiBysani/online-retail-ai-analyst.git
cd online-retail-ai-analyst

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
python scripts/download_data.py
python scripts/prepare_data.py
```

The download script fetches the dataset (about 45 MB) from UCI into `data/raw/` and checks its SHA256. Running it again is safe: it skips the download if the file is already there and correct.

The prepare script converts the Excel workbook (both sheets) into one CSV, `data/processed/online_retail_II.csv`, so later analysis doesn't have to re-read the slow 1M-row workbook every time. It is a straight format conversion: no cleaning, no rows dropped. It takes about a minute, and running it again skips the work if the CSV is already up to date (add `--force` to rebuild).

## Rerun the analysis (from `day-3` on)

With the venv active, run the scripts in this order. Each one writes into `outputs/`.

```bash
python scripts/data_quality.py        # data checks -> outputs/data_quality_report.md
python scripts/retail_analysis.py     # business analysis -> outputs/analysis/
python scripts/customer_analysis.py   # customer analysis (day-4 on) -> outputs/customers/
python scripts/mbr_analysis.py        # monthly business review (day-5); add --month YYYY-MM for another month
python scripts/review_recheck.py      # reviewer's recheck of headline numbers (day-4 on)
```

On Windows without an active venv, call the venv's Python directly, e.g. `.venv\Scripts\python.exe scripts\data_quality.py`.

The Claude Code setup lives in `CLAUDE.md` (project rules and, from `day-5`, the Answer / Clarify / Review / Stop operating model), `.claude/skills/` (day-3), `.claude/agents/` (day-4) and `.claude/settings.json` (permission rules, day-5).

## Folder layout

```
online-retail-ai-analyst/
├── README.md
├── requirements.txt          Python packages (pandas, openpyxl, matplotlib)
├── data/
│   ├── README.md             dataset source, license, citation, checksum
│   ├── raw/                  original dataset, never modified (gitignored)
│   └── processed/            generated CSV, not committed (gitignored)
├── CLAUDE.md                 project rules and operating model for Claude Code
├── .claude/                  skills, agents and settings.json permission rules
├── outputs/                  reports, charts and metrics written by the scripts
└── scripts/
    ├── download_data.py      downloads and verifies the dataset
    ├── prepare_data.py       converts the workbook to one CSV (run once)
    ├── retail_common.py      shared definitions used by the analysis scripts
    └── *_analysis.py, data_quality.py, review_recheck.py   the analyses above
```
