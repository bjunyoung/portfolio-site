"""Export the vetted ACC aggregate workbook into the site's data folder.

Source of truth: `Outputs/ACC Aggregate Results 2019 and 2026 (<date>).xlsx` in the
ACC project (aggregates only; small cells already suppressed there).
Writes one CSV per sheet plus a copy of the workbook, then regenerates
data/acc/MANIFEST.tsv, the allowlist that scripts/check_aggregates.py enforces.

Usage:
    python scripts/export_acc_data.py "/path/to/ACC Aggregate Results 2019 and 2026 (20261004).xlsx"
"""
import csv, hashlib, shutil, sys
from pathlib import Path
import openpyxl

SITE = Path(__file__).resolve().parent.parent
OUT = SITE / "data" / "acc"

# sheet -> (csv name, header row index, 1-based)
SHEETS = {
    "Editions": ("editions.csv", 3),
    "Titles per Decade": ("titles_per_decade.csv", 4),
    "Titles per 5yr": ("titles_per_5yr.csv", 4),
    "Languages": ("languages.csv", 3),
    "Types": ("types.csv", 3),
    "Drift Steps": ("drift_steps.csv", 4),
    "Coherence": ("coherence.csv", 4),
    "Topic Shares": ("topic_shares.csv", 4),
    "Topic by Decade": ("topic_by_decade.csv", 4),
    "Parser Accuracy": ("parser_accuracy.csv", 4),
}
WORKBOOK_NAME = "ACC Aggregate Results 2019 and 2026.xlsx"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(src: str) -> None:
    src = Path(src)
    wb = openpyxl.load_workbook(src, data_only=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for sheet, (name, header) in SHEETS.items():
        ws = wb[sheet]
        rows = [r for r in ws.iter_rows(min_row=header, values_only=True)]
        width = max(i + 1 for i, v in enumerate(rows[0]) if v is not None)
        with open(OUT / name, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            for r in rows:
                r = list(r[:width])
                if all(v is None for v in r):
                    break  # stop at the first blank row (notes follow)
                w.writerow(["" if v is None else v for v in r])
    shutil.copyfile(src, OUT / WORKBOOK_NAME)
    files = sorted(p for p in OUT.iterdir() if p.name != "MANIFEST.tsv")
    with open(OUT / "MANIFEST.tsv", "w", encoding="utf-8") as f:
        f.write(f"# source\t{src.name}\n")
        for p in files:
            f.write(f"{p.name}\t{sha256(p)}\n")
    print(f"exported {len(files)} files to {OUT}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
