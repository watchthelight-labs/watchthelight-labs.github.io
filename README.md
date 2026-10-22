<!-- <wtl> project: watchthelight-labs.github.io | file: README.md | author: watchthelight </wtl> -->
# labs.watchthelight.org

> **Heads up:** a good portion of this code is AI generated. I do understand how it works, and I'm happy to explain any of it. If something looks wrong or you have a question, open an issue or ping me on Discord (`watchthelight`).

The front page of [watchthelight-labs](https://github.com/watchthelight-labs), live at **https://labs.watchthelight.org**.

- **Build:** `build.py` reads every public repo of the org from the GitHub API, places them by `site.json`, and writes `dist/`. A repo `site.json` doesn't mention yet shows up under "More".
- **Deploy:** `.github/workflows/deploy.yml` deploys to GitHub Pages on every push and every 6 hours, so new repos and releases appear without anyone touching the site.
- **Look:** the old uprooted.sh style. Near-black, square tiles, sage green, monospace, and a square-pixel starfield (`src/starfield.js`) whose three depth layers follow the cursor and the scroll. It sits still when the system asks for reduced motion.
- **Link preview:** `src/og.png`, drawn by `tools/og_image.py` with Space Mono.

Local preview: `python build.py && python -m http.server -d dist`.
