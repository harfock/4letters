#!/usr/bin/env python3
"""Validate precomputed crossword levels.

Expected JSON:
{"levels":[{"level":1,"placements":[
 {"word":"胸有成竹","row":4,"col":2,"direction":"across"},
 {"word":"成語接龍","row":4,"col":4,"direction":"down"}
]}]}

Coordinates are zero-based. Words must intersect by matching characters to
belong to the same connected crossword graph.
"""
import json
import sys
from collections import defaultdict, deque
from pathlib import Path


def validate_level(level):
    errors = []
    placements = level.get("placements", [])
    number = level.get("level", "?")
    if not 10 <= len(placements) <= 30:
        errors.append(f"level {number}: expected 10–30 placements, got {len(placements)}")

    cells = defaultdict(list)
    words = set()
    for i, p in enumerate(placements):
        word = p.get("word", "")
        row, col, direction = p.get("row"), p.get("col"), p.get("direction")
        if not isinstance(word, str) or len(word) != 4:
            errors.append(f"level {number}: placement {i} must be a four-character word")
            continue
        if word in words:
            errors.append(f"level {number}: duplicate word {word}")
        words.add(word)
        if not isinstance(row, int) or not isinstance(col, int) or direction not in ("across", "down"):
            errors.append(f"level {number}: invalid coordinates/direction for {word}")
            continue
        for offset, char in enumerate(word):
            r = row + (offset if direction == "down" else 0)
            c = col + (offset if direction == "across" else 0)
            cells[(r, c)].append((i, char, direction, word))

    adjacency = [set() for _ in placements]
    for pos, entries in cells.items():
        chars = {entry[1] for entry in entries}
        if len(chars) > 1:
            errors.append(f"level {number}: conflicting characters at {pos}: {sorted(chars)}")
        if len(entries) > 1:
            if len({entry[2] for entry in entries}) < 2:
                errors.append(f"level {number}: same-direction overlap at {pos}")
            for i, *_ in entries:
                for j, *_ in entries:
                    if i != j:
                        adjacency[i].add(j)

    if placements:
        reached, queue = {0}, deque([0])
        while queue:
            current = queue.popleft()
            for nxt in adjacency[current] - reached:
                reached.add(nxt)
                queue.append(nxt)
        if len(reached) != len(placements):
            isolated = [placements[i].get("word", f"#{i}") for i in range(len(placements)) if i not in reached]
            errors.append(f"level {number}: disconnected placements: {', '.join(isolated)}")
    return errors


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python tools/validate_levels.py data/levels.json")
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    levels = data.get("levels")
    if not isinstance(levels, list) or len(levels) != 21:
        raise SystemExit(f"Expected exactly 21 levels; got {len(levels) if isinstance(levels, list) else 'invalid'}")
    errors, ids, total = [], set(), 0
    for level in levels:
        level_id = level.get("level")
        if level_id in ids:
            errors.append(f"duplicate level id {level_id}")
        ids.add(level_id)
        total += len(level.get("placements", []))
        errors.extend(validate_level(level))
    if ids != set(range(1, 22)):
        errors.append("level ids must be exactly 1–21")
    if total != 420:
        errors.append(f"expected 420 total placements, got {total}")
    if errors:
        print("\n".join("ERROR: " + e for e in errors))
        raise SystemExit(1)
    print("PASS: 21 levels, 420 placements, each level connected, crossing characters consistent.")


if __name__ == "__main__":
    main()
