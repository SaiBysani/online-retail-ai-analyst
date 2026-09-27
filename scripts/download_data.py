"""Download the UCI Online Retail II dataset into data/raw/.

Standard library only. Safe to run more than once:
- If data/raw/online_retail_II.xlsx already exists and its SHA256 matches,
  nothing is downloaded.
- If it exists but the SHA256 does NOT match, the file is left untouched and
  the script exits with an error. It never overwrites an existing file.

Usage (from the repo root):
    python scripts/download_data.py
"""

import hashlib
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
FILENAME = "online_retail_II.xlsx"
EXPECTED_SHA256 = "bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980"

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
TARGET = RAW_DIR / FILENAME
ZIP_PATH = RAW_DIR / "online_retail_II.zip"
TMP_TARGET = RAW_DIR / (FILENAME + ".part")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "online-retail-ai-analyst"})
    with urllib.request.urlopen(request, timeout=60) as response, open(dest, "wb") as out:
        # UCI's server does not always send a file size, so report MB downloaded.
        total = int(response.headers.get("Content-Length") or 0)
        size_note = f" of {total / 1e6:.1f}" if total else ""
        done = 0
        next_report = 5_000_000
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if done >= next_report:
                print(f"  {done / 1e6:.0f}{size_note} MB downloaded...")
                next_report += 5_000_000
        print(f"  done: {done / 1e6:.1f} MB")
    if total and done != total:
        raise IOError(f"Download incomplete: got {done} of {total} bytes")


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if TARGET.exists():
        print(f"Found existing {TARGET.relative_to(REPO_ROOT)}; checking SHA256...")
        actual = sha256_of(TARGET)
        if actual == EXPECTED_SHA256:
            print("OK: file already present and checksum matches. Nothing to download.")
            return 0
        print("WARNING: the existing file does NOT match the expected checksum.")
        print(f"  expected: {EXPECTED_SHA256}")
        print(f"  actual:   {actual}")
        print("The file was left untouched. Move or delete it yourself, then run this script again.")
        return 1

    try:
        print(f"Downloading {URL}")
        download(URL, ZIP_PATH)

        print(f"Extracting {FILENAME}...")
        with zipfile.ZipFile(ZIP_PATH) as zf:
            member = next((n for n in zf.namelist() if Path(n).name == FILENAME), None)
            if member is None:
                print(f"ERROR: {FILENAME} not found in the zip. Contents: {zf.namelist()}")
                return 1
            with zf.open(member) as src, open(TMP_TARGET, "wb") as dst:
                shutil.copyfileobj(src, dst)

        print("Verifying SHA256...")
        actual = sha256_of(TMP_TARGET)
        if actual != EXPECTED_SHA256:
            print("ERROR: downloaded file does NOT match the expected checksum.")
            print(f"  expected: {EXPECTED_SHA256}")
            print(f"  actual:   {actual}")
            print("The source file may have changed. Nothing was saved.")
            return 1

        if TARGET.exists():  # appeared while we were downloading; never overwrite
            print(f"WARNING: {TARGET.relative_to(REPO_ROOT)} appeared during download; left it untouched.")
            return 1
        TMP_TARGET.rename(TARGET)
        print(f"OK: saved {TARGET.relative_to(REPO_ROOT)} ({TARGET.stat().st_size:,} bytes), checksum matches.")
        return 0
    finally:
        for leftover in (ZIP_PATH, TMP_TARGET):
            if leftover.exists():
                leftover.unlink()


if __name__ == "__main__":
    sys.exit(main())
