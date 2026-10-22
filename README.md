<!-- <wtl> project: watchthelight-labs.github.io | file: README.md | author: watchthelight </wtl> -->
# labs.watchthelight.org

The site for [watchthelight-labs](https://github.com/watchthelight-labs), live at **https://labs.watchthelight.org**.

Every public repo of the org gets its own pages: the README, every other markdown file, the releases, and each issue with its comments. Links between them stay on the site. Links to code files, downloads and other people's sites open GitHub or that site in a new tab, marked with an arrow.

## How it's built

- **Fetch** (`sitegen/fetch.py`): the GitHub API returns each README, markdown file, release note and issue already rendered to HTML, so tables, callouts and code look the way GitHub shows them. A full build is about 270 API calls.
- **Links** (`sitegen/links.py`): rewrites `github.com/watchthelight-labs/...` links and relative `.md` links to the matching site page, points relative images at `raw.githubusercontent.com`, and marks everything else as leaving the site.
- **Pages** (`sitegen/render.py`, `src/page.html`): one shell with the header, the nav and the starfield, plus a template for each page type.
- **Previews** (`tools/og_image.py`): a 1200x630 image for the site and one for each repo, showing just the name over the starfield. Space Mono is in `tools/fonts/` under the SIL Open Font License.
- **Checks**: `tools/check_links.py` fails the build on a link to a page that doesn't exist, or on any home-page link that leaves the site. `tools/lint_text.py` checks the site's own text for em dashes and stock AI phrases.
- **Deploy** (`.github/workflows/deploy.yml`): GitHub Pages on every push and every 6 hours, so new repos, releases and issues show up by themselves. A repo that `site.json` doesn't place yet lands under "More".

## Look

The old uprooted.sh style: near-black, square tiles, sage green, monospace, and a square-pixel starfield (`src/starfield.js`) whose three depth layers follow the cursor and the scroll. It stays still when the system asks for reduced motion.

## Local preview

```sh
pip install pillow
python build.py --cache        # --cache keeps API answers in .cache/ for quick rebuilds
python tools/check_links.py
python -m http.server -d dist
```
