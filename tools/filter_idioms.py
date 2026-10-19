#!/usr/bin/env python3
"""Build a four-character headword candidate list from the MOE workbook.

Usage:
  python tools/filter_idioms.py dict_idioms_2020_20260929.xlsx data/idioms.json

Only headwords and pronunciation are exported; dictionary definitions,
examples, and citations are not redistributed.
"""
import json
import re
import sys
from pathlib import Path

from openpyxl import load_workbook

# The official data uses forms such as 即「紙醉金迷」。見「紙醉金迷」條。
REDIRECT = re.compile(
    r'^\s*即[「『《](.+?)[」』》][。；;，,]?\s*見[「『《](.+?)[」』》]條'
)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    source, destination = map(Path, sys.argv[1:])
    wb = load_workbook(source, read_only=True, data_only=True)
    if '成語資料' not in wb.sheetnames:
        raise SystemExit('Missing expected worksheet: 成語資料')
    ws = wb['成語資料']
    records = []
    skipped_redirects = []
    seen = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        word, pinyin, definition, marker = row[1], row[3], str(row[4] or ''), str(row[21] or '').strip()
        if not isinstance(word, str):
            continue
        word = word.strip()
        if len(word) != 4:
            continue
        # Column E's explicit redirect is authoritative even if a future
        # workbook version accidentally marks that row as a main entry.
        match = REDIRECT.search(definition)
        if match and match.group(1) == match.group(2) and match.group(1) != word:
            skipped_redirects.append({'word': word, 'canonical': match.group(1)})
            continue
        if marker != '主條成語' or word in seen:
            continue
        seen.add(word)
        records.append({'word': word, 'pinyin': str(pinyin or '').strip()})
    records.sort(key=lambda item: item['word'])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    words = {item['word'] for item in records}
    print(f'Candidates: {len(records)}')
    print(f'Explicit redirects skipped: {len(skipped_redirects)}')
    print(f'Output: {destination}')
    if '紙醉金迷' not in words or '金迷紙醉' in words:
        raise SystemExit('Canonical-entry validation failed for 紙醉金迷 / 金迷紙醉')


if __name__ == '__main__':
    main()
