# Cloudflare Pages test site — browser-version-refresh

This configuration is intended for the isolated Git branch:

`feature/browser-version-refresh`

It does not change the production `main` branch or the existing GitHub Pages site.

## Create the separate Cloudflare Pages project

1. Open the [Cloudflare dashboard](https://dash.cloudflare.com/) and choose **Workers & Pages**.
2. Choose **Create application** → **Pages** → **Connect to Git** (wording may differ slightly in the dashboard).
3. Authorize the Cloudflare GitHub integration if prompted, and select repository **harfock/4letters**.
4. Name the new project something separate, for example **chengyu-browser-test**.
5. In build settings, use these exact values:

   | Setting | Value |
   | --- | --- |
   | Production branch | `feature/browser-version-refresh` |
   | Framework preset | None / None preset |
   | Build command | `python -m pip install cairosvg && python tools/build_cloudflare_pages.py` |
   | Build output directory | `dist` |
   | Root directory | repository root (leave blank/default) |

6. Save and start the first deployment. The test site will receive its own `*.pages.dev` URL. Use that test URL while evaluating the version-refresh feature.

## What the branch build does

- Stamps `index.html` with the current Cloudflare commit SHA.
- Publishes `version.json` with the same version ID for browser checks.
- Copies the game datasets, manifest and SVG artwork to the Pages output.
- Generates the referenced 180/192/512 PNG icon sizes.
- Adds `_headers` rules to prevent the HTML and `version.json` freshness pointer from being held in stale browser/edge caches.
- Validates that the dataset contains 21 levels and 420 placements.

The build script uses `CF_PAGES_COMMIT_SHA`, provided by Cloudflare Pages, as the version ID. If its deployment changes the version, an already-open game should detect the mismatch and reload. After two unsuccessful automatic retries, it shows a manual refresh notice instead of refreshing indefinitely.

## Keeping it isolated

Do not change the production branch setting of any existing Cloudflare Pages project. Create a **new** Pages project with the feature branch set as that new project's production branch. The Pages subdomain and its deployments will then be separate from the existing production site.
