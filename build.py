#!/usr/bin/env python3
# <wtl> project: watchthelight-labs.github.io | file: build.py | author: watchthelight </wtl>
"""Build labs.watchthelight.org into dist/ from the live repo list of the org plus site.json.

  python build.py [--offline repos.json]

GITHUB_TOKEN (set in Actions) or `gh auth token` is used for the API. Every public repo of the org appears: the
ones site.json places go in their group, any new one lands in the "More" group until it's placed. Python 3.9+,
stdlib only.
"""
import argparse
import datetime as dt
import html
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC, DIST = ROOT / "src", ROOT / "dist"
SITE = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
LANG = {"C": "#8a8e96", "C++": "#c45454", "Python": "#b8a44a", "Rust": "#c8885a", "Shell": "#6a9a6e",
        "Swift": "#d0805a", "Objective-C": "#5a8ab8", "TypeScript": "#5a8ab8", "JavaScript": "#c8b85a"}
BADGE = "style=flat-square&labelColor=0d0e12"


def token():
    t = os.environ.get("GITHUB_TOKEN")
    if t:
        return t
    try:
        return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:   # noqa: BLE001  unauthenticated still works for a public org, just rate-limited
        return ""


def api(path, tok):
    req = urllib.request.Request("https://api.github.com" + path, headers={
        "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
        **({"Authorization": f"Bearer {tok}"} if tok else {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def fetch():
    tok = token()
    repos = api(f"/orgs/{SITE['org']}/repos?type=public&per_page=100", tok) or []
    out = []
    for r in repos:
        if r["private"] or r["archived"] or r["name"] in SITE["hidden"]:
            continue
        rel = api(f"/repos/{r['full_name']}/releases/latest", tok)
        out.append({"name": r["name"], "url": r["html_url"], "description": r.get("description") or "",
                    "language": r.get("language"), "license": (r.get("license") or {}).get("spdx_id"),
                    "stars": r.get("stargazers_count", 0), "issues": r.get("open_issues_count", 0),
                    "pushed": r.get("pushed_at"), "topics": r.get("topics", []),
                    "release": rel["tag_name"] if rel else None, "has_pages": r.get("has_pages")})
    return out


def ago(iso):
    if not iso:
        return ""
    d = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if d.days >= 30:
        return f"{d.days // 30} mo ago"
    if d.days >= 1:
        return f"{d.days} d ago"
    h = d.seconds // 3600
    return f"{h} h ago" if h else "just now"


def esc(s):
    return html.escape(s or "", quote=True)


def tile(r):
    o, n = SITE["org"], r["name"]
    badges = []
    if r["release"]:
        badges.append(f'<img src="https://img.shields.io/github/v/release/{o}/{n}?{BADGE}&color=4d7a51&label=release" '
                      f'alt="latest release {esc(r["release"])}" loading="lazy">')
    if r["license"] and r["license"] != "NOASSERTION":
        badges.append(f'<img src="https://img.shields.io/github/license/{o}/{n}?{BADGE}&color=2a2d33" '
                      f'alt="licence {esc(r["license"])}" loading="lazy">')
    badges.append(f'<img src="https://img.shields.io/github/last-commit/{o}/{n}?{BADGE}&color=2a2d33&label=commit" '
                  f'alt="last commit" loading="lazy">')
    lang = (f'<span class="lang" style="--lc:{LANG.get(r["language"], "#5a5e66")}">{esc(r["language"])}</span>'
            if r["language"] else "")
    stars = f"<span>&#9733; {r['stars']}</span>" if r["stars"] else ""
    rel_link = f'<a href="{r["url"]}/releases">releases</a>' if r["release"] else ""
    return f"""<article class="tile">
  <h4><a href="{r['url']}">{esc(n)}</a></h4>
  <p>{esc(r['description'])}</p>
  <div class="meta">{lang}{stars}<span>updated {ago(r['pushed'])}</span></div>
  <div class="badges">{''.join(badges)}</div>
  <div class="links"><a href="{r['url']}">code</a>{rel_link}<a href="{r['url']}/issues">issues</a></div>
</article>"""


def render(repos):
    by = {r["name"]: r for r in repos}
    placed, sections = set(), []
    groups = [dict(g) for g in SITE["groups"]]
    rest = [r["name"] for r in repos if not any(r["name"] in g["repos"] for g in groups)]
    if rest:
        groups.append({"title": SITE["other_group"], "repos": sorted(rest, key=str.lower)})
    for i, g in enumerate(groups, 1):
        items = [by[n] for n in g["repos"] if n in by]
        if not items:
            continue
        placed.update(r["name"] for r in items)
        sections.append(f"""<section class="group" id="g{i}">
  <div class="group-head"><span class="n">{i:02d}</span><h3>{esc(g['title'])}</h3><span class="rule"></span></div>
  <div class="grid">{''.join(tile(r) for r in items)}</div>
</section>""")
    f = SITE["featured"]
    releases = sum(1 for r in repos if r["release"])
    stars = sum(r["stars"] for r in repos)
    nav = "".join(f'<a href="{esc(l["url"])}">{esc(l["label"])}</a>' for l in SITE["links"])
    built = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    tpl = (SRC / "index.html").read_text(encoding="utf-8")
    tag = esc(SITE["tagline"])
    accent = esc(SITE.get("tagline_accent", ""))
    tag_html = tag.replace(accent, f"<span>{accent}</span>", 1) if accent and accent in tag else tag
    return (tpl.replace("{{TITLE}}", esc(SITE["title"])).replace("{{TAGLINE_HTML}}", tag_html)
            .replace("{{TAGLINE}}", tag)
            .replace("{{INTRO}}", esc(SITE["intro"])).replace("{{URL}}", SITE["url"]).replace("{{NAV}}", nav)
            .replace("{{N_REPOS}}", str(len(repos))).replace("{{N_RELEASES}}", str(releases))
            .replace("{{N_STARS}}", str(stars))
            .replace("{{F_NAME}}", esc(f["name"])).replace("{{F_MACHINE}}", esc(f["machine"]))
            .replace("{{F_CHIPS}}", "".join(f'<span class="chip">{esc(s)}</span>' for s in f["specs"])
                     + f'<span class="chip os">{esc(f["os"])}</span>')
            .replace("{{F_WORKS}}", "".join(f"<li>{esc(w)}</li>" for w in f["works"])).replace("{{F_NEXT}}", esc(f["next"]))
            .replace("{{SECTIONS}}", "\n".join(sections))
            .replace("{{BUILT}}", built).replace("{{ORG}}", SITE["org"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--offline", help="use a saved repo list instead of the API")
    a = ap.parse_args()
    repos = json.loads(Path(a.offline).read_text(encoding="utf-8")) if a.offline else fetch()
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    for f in SRC.iterdir():
        if f.name != "index.html":
            shutil.copy2(f, DIST / f.name)
    (DIST / "index.html").write_text(render(repos), encoding="utf-8")
    (DIST / "CNAME").write_text(SITE["url"].split("//", 1)[1] + "\n", encoding="utf-8")
    (DIST / "repos.json").write_text(json.dumps(repos, indent=1) + "\n", encoding="utf-8")
    print(f"built dist/ with {len(repos)} repos", file=sys.stderr)


if __name__ == "__main__":
    main()
