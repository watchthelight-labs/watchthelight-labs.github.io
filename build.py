#!/usr/bin/env python3
# <wtl> project: watchthelight-labs.github.io | file: build.py | author: watchthelight </wtl>
"""Build labs.watchthelight.org into dist/ from the org's public repos and site.json.

  python build.py [--cache]

Every repo gets its own pages: README, every other markdown file, releases, issues and each issue thread, all
rendered by GitHub and with links to our own content pointed back into the site (sitegen/links.py). GITHUB_TOKEN
(set in Actions) or `gh auth token` is used for the API. --cache keeps API answers in .cache/ for quick local
rebuilds. Needs Pillow for the link-preview images.
"""
import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

from sitegen.fetch import collect
from sitegen.links import Linker, md_page
from sitegen.render import Pages

sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))
import og_image  # noqa: E402

ROOT = Path(__file__).resolve().parent
SRC, DIST = ROOT / "src", ROOT / "dist"


def write(path: str, text: str, seen: dict, origin: str):
    """path is a site URL ("/x/y/" or "/404.html")."""
    rel = path.strip("/")
    f = DIST / (rel if rel.endswith((".html", ".xml", ".txt")) else (rel + "/index.html" if rel else "index.html"))
    if f in seen:
        sys.exit(f"two pages want {path}: {seen[f]} and {origin}")
    seen[f] = origin
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8", newline="\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cache", action="store_true", help="reuse API answers saved in .cache/")
    a = ap.parse_args()
    site = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
    skip = set(site["hidden"]) - {site["site_repo"]}
    repos, calls = collect(site["org"], skip, a.cache)
    for r in repos:
        r["slug"] = "site" if r["name"] == site["site_repo"] else r["name"]
        r["hidden"] = r["name"] in site["hidden"]
    linker = Linker(site["org"], {r["name"]: {"slug": r["slug"], "branch": r["branch"], "docs": set(r["docs"]),
                                              "issues": {i["number"] for i in r["issues"]}} for r in repos})
    built = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pages = Pages(site, built)

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    for name in ("style.css", "starfield.js", "copy.js", "favicon.svg"):
        shutil.copy2(SRC / name, DIST / name)
    og_image.draw(DIST / "og.png", "watchthelight labs")

    seen, urls = {}, ["/", "/about/"]
    write("/", pages.home(repos), seen, "home")
    write("/about/", pages.about(), seen, "about")
    write("/404.html", pages.not_found(), seen, "404")
    for r in repos:
        n, s = r["name"], r["slug"]
        og_image.draw(DIST / s / "og.png", n, "watchthelight labs")
        write(f"/{s}/", pages.repo_page(r, linker.rewrite(r["readme_html"], n)), seen, f"{n} README")
        urls.append(f"/{s}/")
        for path, html_ in r["docs"].items():
            url = md_page(s, path)
            write(url, pages.doc_page(r, path, linker.rewrite(html_, n, path)), seen, f"{n} {path}")
            urls.append(url)
        if r["releases"]:
            write(f"/{s}/releases/", pages.releases_page(r, linker), seen, f"{n} releases")
            urls.append(f"/{s}/releases/")
        if r["issues"]:
            write(f"/{s}/issues/", pages.issues_page(r), seen, f"{n} issues")
            urls.append(f"/{s}/issues/")
            for i in r["issues"]:
                write(f"/{s}/issues/{i['number']}/", pages.issue_page(r, i, linker), seen, f"{n} #{i['number']}")
                urls.append(f"/{s}/issues/{i['number']}/")

    base = site["url"]
    (DIST / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + "".join(f"<url><loc>{base}{u}</loc></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")
    (DIST / "CNAME").write_text(base.split("//", 1)[1] + "\n", encoding="utf-8")
    # the slim list the org profile README is generated from
    (DIST / "repos.json").write_text(json.dumps(
        [{k: r[k] for k in ("name", "url", "description", "language", "license", "stars", "pushed", "topics", "release")}
         for r in repos if not r["hidden"]], indent=1) + "\n", encoding="utf-8")
    print(f"built dist/: {len(seen)} pages from {len(repos)} repos, {calls} API calls", file=sys.stderr)


if __name__ == "__main__":
    main()
