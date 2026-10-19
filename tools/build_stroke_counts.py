#!/usr/bin/env python3
"""Create a compact stroke-count map for the characters used by the game.

Usage:
  python tools/build_stroke_counts.py public/data/levels.json /tmp/stroke-data public/data/strokes.json

Input data is from ChineseStrokes (source: zidian.911cha.com):
https://github.com/caiguanhao/ChineseStrokes
"""
import json
import re
import sys
from pathlib import Path

PAIR = re.compile(r'^\s*(\d+)\s+(\d+)\s*$')


def main():
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    levels_path, source_dir, output_path = map(Path, sys.argv[1:])
    levels = json.loads(levels_path.read_text(encoding='utf-8'))
    chars = sorted({ch for level in levels['levels'] for p in level['placements'] for ch in p['word']})
    counts = {}
    for path in source_dir.rglob('*.txt'):
        for line in path.read_text(encoding='utf-8-sig', errors='replace').splitlines():
            m = PAIR.match(line)
            if m:
                codepoint, count = int(m.group(1)), int(m.group(2))
                if 0 <= codepoint <= 0x10FFFF:
                    counts[chr(codepoint)] = count
    missing = [ch for ch in chars if ch not in counts]
    if missing:
        raise SystemExit('Missing stroke counts for: ' + ''.join(missing))
    result = {ch: counts[ch] for ch in chars}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    print(f'PASS: stroke counts for {len(result)} unique game characters -> {output_path}')


if __name__ == '__main__':
    main()
