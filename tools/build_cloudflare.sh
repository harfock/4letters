#!/usr/bin/env bash
set -euo pipefail

# Cloudflare Pages build for harfock/4letters.
# Output directory: public/
# Keep this in sync with .github/workflows/deploy.yml.

python -m pip install --upgrade pip
python -m pip install openpyxl pillow cairosvg

mkdir -p public/data
cp index.html public/index.html
cp app-icon.svg public/app-icon.svg
cp manifest.webmanifest public/manifest.webmanifest

python - <<'PY'
import cairosvg
for size, name in [(180, "apple-touch-icon.png"), (192, "icon-192.png"), (512, "icon-512.png")]:
    cairosvg.svg2png(
        url="app-icon.svg",
        write_to="public/" + name,
        output_width=size,
        output_height=size,
    )
PY

python -m py_compile tools/build_levels.py tools/build_stroke_counts.py
python - <<'PY'
import re
from pathlib import Path
html = Path("index.html").read_text(encoding="utf-8")
match = re.search(r"<script\b[^>]*>(.*?)</script\s*>", html, re.S | re.I)
if not match:
    raise SystemExit("No inline JavaScript found")
Path("/tmp/4letters-game.js").write_text(match.group(1), encoding="utf-8")
PY
node --check /tmp/4letters-game.js

curl -L --fail --retry 3 -o /tmp/4letters-moe-source.zip \
  https://language.moe.gov.tw/001/Upload/Files/site_content/M0001/respub/download/dict_idioms_2020_20260929.zip

python - <<'PY'
import zipfile
from pathlib import Path
with zipfile.ZipFile("/tmp/4letters-moe-source.zip") as archive:
    workbooks = [name for name in archive.namelist() if name.lower().endswith(".xlsx")]
    if not workbooks:
        raise SystemExit("Official MOE ZIP contains no XLSX workbook")
    Path("/tmp/4letters-source.xlsx").write_bytes(archive.read(workbooks[0]))
PY

python tools/build_levels.py /tmp/4letters-source.xlsx public/data/levels.json

mkdir -p /tmp/4letters-stroke-data
curl -L --fail --retry 3 -o /tmp/4letters-stroke-data/1.4e00-9fff.txt \
  https://raw.githubusercontent.com/caiguanhao/ChineseStrokes/master/data/1.4e00-9fff.txt
curl -L --fail --retry 3 -o /tmp/4letters-stroke-data/2.3400-4dbf.txt \
  https://raw.githubusercontent.com/caiguanhao/ChineseStrokes/master/data/2.3400-4dbf.txt

python tools/build_stroke_counts.py public/data/levels.json /tmp/4letters-stroke-data public/data/strokes.json

echo "Cloudflare Pages build completed. Publish directory: public/"
