# <wtl> project: watchthelight-labs.github.io | file: sitegen/fetch.py | author: watchthelight </wtl>
"""Everything the site shows, from the GitHub API: repos, READMEs and other markdown files already rendered to
HTML by GitHub (Accept: application/vnd.github.html+json), releases, issues and their comments.

With cache=True every response is kept in .cache/ (local runs only; CI always fetches fresh).
"""
import hashlib
import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache"
HTML = "application/vnd.github.html+json"
JSON = "application/vnd.github+json"
# folders whose markdown is data, not pages (the research repo's 1,000 log files)
SKIP_MD = re.compile(r"^(logs/|node_modules/|vendor/|third_party/|\.github/)", re.I)


class GitHub:
    def __init__(self, cache=False):
        self.token = os.environ.get("GITHUB_TOKEN") or self._gh_token()
        self.cache = cache
        self.calls = 0

    @staticmethod
    def _gh_token():
        try:
            return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()
        except Exception:   # noqa: BLE001  public data works without a token, just rate-limited
            return ""

    def get(self, path, accept=JSON, raw=False):
        url = path if path.startswith("http") else "https://api.github.com" + path
        key = CACHE / (hashlib.sha1(f"{accept}|{url}".encode()).hexdigest() + (".txt" if raw else ".json"))
        if self.cache and key.exists():
            text = key.read_text(encoding="utf-8")
            return text if raw else json.loads(text)
        req = urllib.request.Request(url, headers={"Accept": accept, "X-GitHub-Api-Version": "2022-11-28",
                                                   **({"Authorization": f"Bearer {self.token}"} if self.token else {})})
        self.calls += 1
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                text = r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code in (404, 409):
                return None
            raise
        if self.cache:
            CACHE.mkdir(exist_ok=True)
            key.write_text(text, encoding="utf-8")
        return text if raw else json.loads(text)

    def pages(self, path, accept=JSON, limit=10):
        out = []
        for page in range(1, limit + 1):
            sep = "&" if "?" in path else "?"
            data = self.get(f"{path}{sep}per_page=100&page={page}", accept) or []
            out += data
            if len(data) < 100:
                break
        return out


def article(html: str) -> str:
    """GitHub wraps rendered files in <div id="file"><article class="markdown-body ...">; keep the inside."""
    m = re.search(r'<article[^>]*class="[^"]*markdown-body[^"]*"[^>]*>(.*)</article>', html or "", re.S)
    return (m.group(1) if m else (html or "")).strip()


def collect(org: str, skip, cache=False):
    """Every public, unarchived repo of the org except the names in skip."""
    gh = GitHub(cache)
    repos = []
    for r in gh.pages(f"/orgs/{org}/repos?type=public&sort=full_name"):
        name, branch = r["name"], r["default_branch"]
        if r["private"] or r["archived"] or name in skip:
            continue
        rel_list = gh.pages(f"/repos/{org}/{name}/releases", HTML, 3)
        issues = [i for i in gh.pages(f"/repos/{org}/{name}/issues?state=all", HTML, 5) if "pull_request" not in i]
        for i in issues:
            i["comment_list"] = gh.pages(f"/repos/{org}/{name}/issues/{i['number']}/comments", HTML, 3) if i["comments"] else []
        tree = gh.get(f"/repos/{org}/{name}/git/trees/{branch}?recursive=1") or {"tree": []}
        md = sorted(t["path"] for t in tree["tree"] if t["type"] == "blob" and t["path"].lower().endswith(".md")
                    and not SKIP_MD.match(t["path"]))
        readme = article(gh.get(f"/repos/{org}/{name}/readme", HTML, raw=True) or "")
        docs = {}
        for p in md:
            if p.lower() == "readme.md":
                continue
            docs[p] = article(gh.get(f"/repos/{org}/{name}/contents/{urllib.parse.quote(p)}?ref={branch}", HTML, raw=True) or "")
        repos.append({
            "name": name, "branch": branch, "url": r["html_url"], "description": r.get("description") or "",
            "language": r.get("language"), "license": (r.get("license") or {}).get("spdx_id"),
            "stars": r.get("stargazers_count", 0), "pushed": r.get("pushed_at"), "topics": r.get("topics", []),
            "homepage": r.get("homepage"),
            "release": rel_list[0]["tag_name"] if rel_list else None,
            "releases": [{"tag": x["tag_name"], "name": x.get("name") or x["tag_name"], "published": x.get("published_at"),
                          "prerelease": x.get("prerelease"), "url": x["html_url"], "body_html": x.get("body_html") or "",
                          "assets": [{"name": a["name"], "size": a["size"], "url": a["browser_download_url"],
                                      "downloads": a.get("download_count", 0)} for a in x.get("assets", [])]}
                         for x in rel_list],
            "issues": [{"number": i["number"], "title": i["title"], "state": i["state"], "url": i["html_url"],
                        "user": i["user"]["login"], "created": i["created_at"], "updated": i["updated_at"],
                        "closed": i.get("closed_at"), "labels": [l["name"] for l in i.get("labels", [])],
                        "body_html": i.get("body_html") or "",
                        "comments": [{"user": c["user"]["login"], "created": c["created_at"], "url": c["html_url"],
                                      "body_html": c.get("body_html") or ""} for c in i["comment_list"]]}
                       for i in issues],
            "readme_html": readme, "docs": docs,
        })
    return repos, gh.calls
