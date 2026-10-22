#!/usr/bin/env python3
"""Build a self-contained static site for the Cloudflare Pages test project."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist"


def build_version() -> str:
    for key in ("CF_PAGES_COMMIT_SHA", "GITHUB_SHA"):
        value = os.environ.get(key, "").strip()
        if value and not value.startswith("__"):
            return value
    try:
        value = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        if value:
            return value
    except (OSError, subprocess.CalledProcessError):
        pass
    raise SystemExit(
        "Cannot determine build version. Cloudflare Pages should provide CF_PAGES_COMMIT_SHA."
    )


def copy_file(relative_path: str) -> None:
    src = ROOT / relative_path
    if not src.is_file():
        raise SystemExit(f"Required file is missing: {relative_path}")
    dest = OUT / relative_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def main() -> None:
    version = build_version()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    html = (ROOT / "index.html").read_text(encoding="utf-8")
    pattern = r'(<meta name="app-version" content=")[^"]*(">)'
    stamped, count = re.subn(
        pattern, lambda match: match.group(1) + version + match.group(2), html, count=1
    )
    if count != 1:
        raise SystemExit('index.html must contain <meta name="app-version" ...>.')
    version_meta = re.search(r'<meta name="app-version" content="([^"]+)"', stamped)
    if not version_meta or version_meta.group(1) != version:
        raise SystemExit("The app-version meta tag was not stamped correctly.")
    (OUT / "index.html").write_text(stamped, encoding="utf-8")

    for relative in (
        "app-icon.svg",
        "manifest.webmanifest",
        "data/levels.json",
        "data/strokes.json",
        "data/reference/hk_written_chinese_idioms.json",
    ):
        copy_file(relative)

    # The opening and homepage use this locally served cinematic background.
    assets = ROOT / "assets"
    if not assets.is_dir():
        raise SystemExit("Required folder is missing: assets")
    shutil.copytree(assets, OUT / "assets")

    # Generate the PNG icon sizes referenced by the manifest and Apple touch icon.
    try:
        import cairosvg
    except ImportError as exc:
        raise SystemExit(
            "CairoSVG is required. Set the Cloudflare Pages build command to "
            "'python -m pip install cairosvg && python tools/build_cloudflare_pages.py'."
        ) from exc

    for size, filename in (
        (180, "apple-touch-icon.png"),
        (192, "icon-192.png"),
        (512, "icon-512.png"),
    ):
        cairosvg.svg2png(
            url=str(ROOT / "app-icon.svg"),
            write_to=str(OUT / filename),
            output_width=size,
            output_height=size,
        )

    (OUT / "version.json").write_text(
        json.dumps({"version": version}, ensure_ascii=False),
        encoding="utf-8",
    )

    # Avoid serving stale HTML or the version pointer from browser/edge caches.
    (OUT / "_headers").write_text(
        "/\n"
        "  Cache-Control: no-store, no-cache, must-revalidate, max-age=0\n"
        "/index.html\n"
        "  Cache-Control: no-store, no-cache, must-revalidate, max-age=0\n"
        "/version.json\n"
        "  Cache-Control: no-store, no-cache, must-revalidate, max-age=0\n"
        "/data/reference/hk_written_chinese_idioms.json\n"
        "  Cache-Control: no-store, no-cache, must-revalidate, max-age=0\n",
        encoding="utf-8",
    )

    # Validate that the explanation JSON is in the published artifact, not just in the source tree.
    explanation_path = OUT / "data/reference/hk_written_chinese_idioms.json"
    if not explanation_path.is_file():
        raise SystemExit("Required explanation JSON is missing from the build output.")
    explanation_data = json.loads(explanation_path.read_text(encoding="utf-8"))
    explanation_entries = explanation_data.get("entries", [])
    if len(explanation_entries) != 384:
        raise SystemExit(
            f"Unexpected idiom explanation dataset: {len(explanation_entries)} entries; expected 384."
        )
    if any(not entry.get("idiom") or not entry.get("meaning") for entry in explanation_entries):
        raise SystemExit("The idiom explanation dataset contains an entry without an idiom or meaning.")

    # Explanation meanings are embedded in index.html so they still work if a
    # hosting configuration returns the SPA HTML fallback for JSON asset URLs.
    source_html = (ROOT / "index.html").read_text(encoding="utf-8")
    start_marker = "/* IDIOM_MEANINGS_JSON_START */"
    end_marker = "/* IDIOM_MEANINGS_JSON_END */"
    if start_marker not in source_html or end_marker not in source_html:
        raise SystemExit("index.html is missing its embedded idiom explanation data markers.")
    embedded_json = source_html.split(start_marker, 1)[1].split(end_marker, 1)[0]
    try:
        embedded_entries = json.loads(embedded_json)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Embedded idiom explanations are invalid JSON: {exc}") from exc
    expected_entries = [
        {"idiom": entry["idiom"], "meaning": entry["meaning"]}
        for entry in explanation_entries
    ]
    if embedded_entries != expected_entries:
        raise SystemExit(
            "Embedded idiom explanations do not match data/reference/hk_written_chinese_idioms.json."
        )

    data = json.loads((OUT / "data/levels.json").read_text(encoding="utf-8"))
    levels = data.get("levels", [])
    placements = sum(len(level.get("placements", [])) for level in levels)
    expected_levels = 40
    expected_placements = 980
    if len(levels) != expected_levels or placements != expected_placements:
        raise SystemExit(
            f"Unexpected crossword dataset: {len(levels)} levels, {placements} placements; "
            f"expected {expected_levels} levels and {expected_placements} placements."
        )

    # Validate every crossword map: entries are four characters, overlaps agree,
    # and no horizontal or vertical contiguous occupied run exceeds four squares.
    for level_index, level in enumerate(levels, start=1):
        placements_in_level = level.get("placements", [])
        seen_words = set()
        occupied = {}
        row_cells = {}
        col_cells = {}
        for placement in placements_in_level:
            word = placement.get("word", "")
            direction = placement.get("direction")
            row = placement.get("row")
            col = placement.get("col")
            if len(word) != 4 or direction not in ("across", "down"):
                raise SystemExit(f"Level {level_index}: invalid four-character crossword entry {word!r}")
            if word in seen_words:
                raise SystemExit(f"Level {level_index}: duplicate idiom {word!r}")
            seen_words.add(word)
            if not isinstance(row, int) or not isinstance(col, int) or row < 0 or col < 0:
                raise SystemExit(f"Level {level_index}: invalid crossword coordinates for {word!r}")
            for offset, character in enumerate(word):
                r = row + (offset if direction == "down" else 0)
                c = col + (offset if direction == "across" else 0)
                key = (r, c)
                previous = occupied.get(key)
                if previous:
                    if previous["character"] != character:
                        raise SystemExit(f"Level {level_index}: conflicting letters at {key}")
                    if direction in previous["directions"]:
                        raise SystemExit(f"Level {level_index}: same-direction overlap at {key}")
                    previous["directions"].add(direction)
                else:
                    occupied[key] = {"character": character, "directions": {direction}}
                row_cells.setdefault(r, set()).add(c)
                col_cells.setdefault(c, set()).add(r)

        def max_contiguous_run(axis_cells):
            maximum = 0
            for positions in axis_cells.values():
                run = 0
                previous = None
                for position in sorted(positions):
                    run = run + 1 if previous is not None and position == previous + 1 else 1
                    maximum = max(maximum, run)
                    previous = position
            return maximum

        max_horizontal_run = max_contiguous_run(row_cells)
        max_vertical_run = max_contiguous_run(col_cells)
        if max_horizontal_run > 4 or max_vertical_run > 4:
            raise SystemExit(
                f"Level {level_index}: contiguous occupied-square run exceeds four "
                f"(horizontal={max_horizontal_run}, vertical={max_vertical_run})"
            )

    print(f"Cloudflare Pages site ready: version={version}, levels={len(levels)}, placements={placements}, output={OUT}")


if __name__ == "__main__":
    main()
