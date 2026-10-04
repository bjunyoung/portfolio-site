"""Pre-render guard: only vetted aggregate files may sit in data/.

Every file under data/ must be listed in its folder's MANIFEST.tsv with a
matching SHA-256 (written by export_acc_data.py from the vetted workbook).
Anything else -- an entry-level export, a stray JSONL, an edited CSV -- stops
the build. Run automatically by Quarto (pre-render in _quarto.yml).
"""
import hashlib, sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
DATA = SITE / "data"
MAX_BYTES = 2_000_000          # aggregates are small; a big file is a red flag
BANNED_SUFFIXES = {".jsonl", ".npy", ".docx", ".pdf", ".tsv"}  # except MANIFEST.tsv

problems = []
for p in sorted(DATA.rglob("*")):
    if p.is_dir() or p.name == ".DS_Store":
        continue
    rel = p.relative_to(SITE)
    if p.name == "MANIFEST.tsv":
        continue
    manifest = p.parent / "MANIFEST.tsv"
    allowed = {}
    if manifest.exists():
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#"):
                name, digest = line.split("\t")
                allowed[name] = digest
    if p.suffix.lower() in BANNED_SUFFIXES:
        problems.append(f"{rel}: file type not allowed on the site")
    elif p.name not in allowed:
        problems.append(f"{rel}: not in {manifest.relative_to(SITE)}")
    elif hashlib.sha256(p.read_bytes()).hexdigest() != allowed[p.name]:
        problems.append(f"{rel}: changed since export (hash mismatch)")
    elif p.stat().st_size > MAX_BYTES:
        problems.append(f"{rel}: larger than {MAX_BYTES} bytes")

if problems:
    print("Aggregates-only check FAILED:\n  " + "\n  ".join(problems), file=sys.stderr)
    sys.exit(1)
print("Aggregates-only check passed.")
