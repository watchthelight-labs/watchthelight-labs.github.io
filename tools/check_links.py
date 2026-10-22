#!/usr/bin/env python3
# <wtl> project: watchthelight-labs.github.io | file: tools/check_links.py | author: watchthelight </wtl>
"""Check dist/ after a build. Fails when:
- an internal link (href="/...") points to a page or file that wasn't generated, or to an #anchor missing there;
- a link on the home page leaves the site (badges are images, so they don't count);
- a link to github.com/watchthelight-labs/... is left on any page without being marked as leaving (class "ext"),
  which means the rewrite missed something the site has a page for.

  python tools/check_links.py [dist]
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

DIST = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "dist")
A = re.compile(r"<a\b[^>]*>")
HREF = re.compile(r'\bhref="([^"]*)"')
IDS = re.compile(r'\b(?:id|name)="([^"]+)"')


def target(url):
    path, _, anchor = url.partition("#")
    path = path.split("?")[0]
    f = DIST / path.lstrip("/")
    if path.endswith("/") or not path:
        f = f / "index.html"
    return f, anchor


def main():
    pages = sorted(DIST.rglob("*.html"))
    ids = {}
    problems = defaultdict(list)
    for p in pages:
        ids[p] = set(IDS.findall(p.read_text(encoding="utf-8")))
    internal = 0
    for p in pages:
        text = p.read_text(encoding="utf-8")
        home = p == DIST / "index.html"
        for tag in A.findall(text):
            m = HREF.search(tag)
            if not m:
                continue
            url = m.group(1).replace("&amp;", "&")
            if url.startswith("/"):
                internal += 1
                f, anchor = target(url)
                if not f.exists():
                    problems["missing page"].append(f"{p.relative_to(DIST)} -> {url}")
                elif anchor and f.suffix == ".html" and anchor not in ids.get(f, set()):
                    problems["missing anchor"].append(f"{p.relative_to(DIST)} -> {url}")
            elif url.startswith("#"):
                if url[1:] and url[1:] not in ids[p]:
                    problems["missing anchor"].append(f"{p.relative_to(DIST)} -> {url}")
            elif url.startswith(("http://", "https://")):
                if home:
                    problems["home page leaves the site"].append(url)
                if re.match(r"https?://github\.com/watchthelight-labs/", url) and "ext" not in tag:
                    problems["unmarked github link"].append(f"{p.relative_to(DIST)} -> {url}")
    print(f"{len(pages)} pages, {internal} internal links checked")
    hard = ("missing page", "home page leaves the site", "unmarked github link")
    for kind, items in problems.items():
        print(f"\n{kind}: {len(items)}")
        for x in items[:25]:
            print("  " + x)
    sys.exit(1 if any(problems.get(k) for k in hard) else 0)


if __name__ == "__main__":
    main()
