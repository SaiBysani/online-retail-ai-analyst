# Data

## Source

UCI Machine Learning Repository: **Online Retail II**
https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip

The download is a zip containing one Excel file, `online_retail_II.xlsx`, with two sheets (`Year 2009-2010` and `Year 2010-2011`).

## License

CC BY 4.0 (Creative Commons Attribution 4.0 International).

## Citation

Chen, D. (2012). Online Retail II [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D

## Checksum

`data/raw/online_retail_II.xlsx` (45,622,278 bytes)

SHA256: `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`

## Rules

Raw data is never modified. The file is not committed to git (`data/raw/` is gitignored).
To get it, run:

```bash
python scripts/download_data.py
```
