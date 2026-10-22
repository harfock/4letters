# 4Letters — Ongoing Development Notes

Last updated: 2026-10-23  
Current production game version: **021**  
Production commit at the time of this note: `10d10c863b2e5a77d9f7bad1a9f93c87e7cfddee`

This file records deployment lessons and non-negotiable checks for future game updates. Read it before changing data files, the startup loader, or Cloudflare deployment settings.

## 1. Which site and branch?

- **Production:** [https://4letters.pages.dev/](https://4letters.pages.dev/) — Cloudflare Pages connected to GitHub `main`.
- **Test/preview:** [https://4letters-s.pages.dev/](https://4letters-s.pages.dev/) — Cloudflare Pages connected to `feature/kinetic-comic-opening`.
- The test project's settings are documented in [`CLOUDFLARE_TEST_SETUP.md`](CLOUDFLARE_TEST_SETUP.md). Its build command is `python -m pip install cairosvg && python tools/build_cloudflare_pages.py`, output directory `dist`, root directory the repository root.
- Do not assume that a successful preview deployment means production has deployed. Check the correct Cloudflare project and its latest deployment separately.

## 2. Current canonical game data

- `data/levels.json`: **40 levels / 980 placements**.
- `data/reference/hk_written_chinese_idioms.json`: **384 idiom explanations**.
- `index.html` embeds both datasets so the game can start even if a host or routing rule returns HTML instead of a separate JSON asset.
- The board is embedded between `/* LEVELS_JSON_START */` and `/* LEVELS_JSON_END */`.
- The explanation records are embedded between `/* IDIOM_MEANINGS_JSON_START */` and `/* IDIOM_MEANINGS_JSON_END */`.

The embedded copies and the canonical JSON files must be identical. `tools/build_cloudflare_pages.py` validates both. **When editing levels or explanations, update the canonical data and the matching embedded block in `index.html` in the same change. Do not remove the build-time equality checks.**

The current UI badge is **021**. The build script stamps the HTML app-version metadata and `version.json` with the deployment commit. Keep the visible version badge updated intentionally when preparing a new release.

## 3. Incident history — errors to prevent

### A. Cloudflare build failed on the level-count guard

The build reported **21 levels / 420 placements**, but the Cloudflare app requires **40 levels / 980 placements**. The source data on `main` had been restored, but a legacy step in `.github/workflows/deploy.yml` regenerated the old 21/420 dataset and pushed it back to `main`.

**Prevention:** that automatic write-back has been removed, and workflow `contents` permission is read-only. Do not reintroduce a step that copies generated legacy data into the repository and runs `git push origin HEAD:main`. The GitHub Pages workflow and the Cloudflare Pages build are separate pipelines; do not let the GitHub Pages artifact overwrite Cloudflare's canonical data.

### B. Explanations URL returned HTML instead of JSON

The request to `/data/reference/hk_written_chinese_idioms.json` returned HTTP 200 but the content type was `text/html; charset=utf-8`, with a body starting `<!doctype html>`. This is an HTML fallback, not valid JSON. HTTP 200 alone does not prove that the correct static file was served.

**Prevention:** v020 embedded the 384 explanations into `index.html`. The game must not depend on a runtime fetch of the explanation JSON file. Keep the canonical JSON for maintenance and build-time validation.

### C. Version 020 loaded but the game board remained empty

The page still fetched `data/levels.json` at runtime. The live endpoint did not deliver the required 40-level dataset, so the game displayed “棋盤資料格式錯誤：需要 40 關” even though the GitHub source contained 40 levels.

**Prevention:** v021 embeds the validated 40-level board in `index.html` and initializes the game from that object. The game must not depend on a runtime fetch of `data/levels.json`. The build checks that the embedded board matches the canonical JSON.

## 4. Required release checklist

Before merging a future update:

1. **Work on the test branch first** and preserve the separation between test and production. Merge into `main` only after the preview and automated checks are good.
2. If changing levels or explanations, update both the canonical JSON and the matching embedded data in `index.html`.
3. Run the Cloudflare build:
   ```bash
   python -m pip install cairosvg
   CF_PAGES_COMMIT_SHA=local-validation python tools/build_cloudflare_pages.py
   ```
   The script must pass its checks, including **40 levels / 980 placements**, 384 explanations, and exact equality between embedded and canonical data. A local run may use the placeholder commit label only for validation; deployed builds should use Cloudflare's real commit SHA.
4. Run the inline JavaScript syntax check used by `.github/workflows/validate-browser-version-refresh.yml` (Node `--check`) when changing `index.html`.
5. Confirm the Cloudflare test deployment is **successful**, then merge the tested changes to `main`.
6. After the main deployment, verify the **production** page itself: the expected version badge appears, the game board renders, candidate letters load, and both hint and completed-idiom explanations appear. Do not treat a merge, GitHub check, or version badge alone as proof that the whole game works.
7. If a request for a `.json` file returns HTML, inspect the actual response's `content-type` and first bytes, then inspect the published build output and routing. Do not just retry `fetch()` with a different cache option or weaken the data validation.
8. Do not restore the legacy GitHub Actions write-back to `main`. Never lower the expected dataset counts just to make a build pass.

## 5. Quick source-of-truth checks

- Board: [`data/levels.json`](data/levels.json)
- Explanations: [`data/reference/hk_written_chinese_idioms.json`](data/reference/hk_written_chinese_idioms.json)
- Runtime and embedded data: [`index.html`](index.html)
- Cloudflare builder and consistency checks: [`tools/build_cloudflare_pages.py`](tools/build_cloudflare_pages.py)
- Test deployment settings: [`CLOUDFLARE_TEST_SETUP.md`](CLOUDFLARE_TEST_SETUP.md)
- Main deployment workflow: [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)

**Core lesson:** validate the final published app, not only the source files. Keep canonical and embedded data synchronized, keep regression checks strict, and never reintroduce runtime dependencies on static JSON routes that have already served HTML fallbacks.
