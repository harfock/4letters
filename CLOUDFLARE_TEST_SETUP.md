# Cloudflare Pages deployment — 4letters-s

The Cloudflare Pages project for this game is **4letters-s**, served at:

https://4letters-s.pages.dev/

Its connected Git branch is:

`feature/kinetic-comic-opening`

## Required Cloudflare Pages build settings

In Cloudflare Dashboard → Workers & Pages → **4letters-s** → Settings → Builds & deployments, use:

| Setting | Value |
| --- | --- |
| Production branch | `feature/kinetic-comic-opening` |
| Framework preset | None |
| Build command | `python -m pip install cairosvg && python tools/build_cloudflare_pages.py` |
| Build output directory | `dist` |
| Root directory | repository root (default / blank) |

Keep these settings in place so Cloudflare publishes a complete built site, including the local comic background and a version marker that is generated from `CF_PAGES_COMMIT_SHA`.

## Version refresh

The build script stamps both the app's `app-version` meta tag and `version.json` with the same deployment commit SHA. At each fresh page launch, the browser requests `version.json` without using the cache. If the loaded page is older than the deployed version, it automatically reloads with a cache-busting query. After repeated failed refreshes, it displays a manual reload notice rather than looping forever.

The build output also includes `_headers` rules for `index.html` and `version.json` so stale client-side copies are less likely to be reused.

## Output validation

The build script checks the included dataset for 21 levels and 420 placements. It also copies `assets/opening-comic-bg.svg`, the data files, the manifest, and generated icons into `dist`. The GitHub Pages workflow for `main` remains separate; Cloudflare deployments use this Pages build script on the connected feature branch.
