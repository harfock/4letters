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
    ):
        copy_file(relative)

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
        "  Cache-Control: no-store, no-cache, must-revalidate, max-age=0\n",
        encoding="utf-8",
    )

    data = json.loads((OUT / "data/levels.json").read_text(encoding="utf-8"))
    levels = data.get("levels", [])
    placements = sum(len(level.get("placements", [])) for level in levels)
    if len(levels) != 21 or placements != 420:
        raise SystemExit(
            f"Unexpected crossword dataset: {len(levels)} levels, {placements} placements."
        )

    print(f"Cloudflare Pages site ready: version={version}, levels={len(levels)}, placements={placements}, output={OUT}")


if __name__ == "__main__":
    main()
