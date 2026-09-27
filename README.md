# online-retail-ai-analyst

A demo repo for a Claude Code tutorial series for data professionals. It is built on the UCI Online Retail II dataset: about 1.07 million invoice line items from a UK-based online retailer between 2009 and 2011 (invoices, products, quantities, prices, customers, countries). Each day of the series adds to this same repo.

## Setup

Requires Python 3 and Git.

```bash
git clone <this repo's URL>
cd online-retail-ai-analyst

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
python scripts/download_data.py
```

The download script fetches the dataset (about 45 MB) from UCI into `data/raw/` and checks its SHA256. Running it again is safe: it skips the download if the file is already there and correct.

## Folder layout

```
online-retail-ai-analyst/
├── README.md
├── requirements.txt          Python packages (pandas, openpyxl, matplotlib)
├── data/
│   ├── README.md             dataset source, license, citation, checksum
│   └── raw/                  original dataset, never modified (gitignored)
└── scripts/
    └── download_data.py      downloads and verifies the dataset
```
