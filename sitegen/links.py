# <wtl> project: watchthelight-labs.github.io | file: sitegen/links.py | author: watchthelight </wtl>
"""Rewrite the links in GitHub-rendered HTML so our own content stays on the site.

- github.com/<org>/<repo>, its .md files, issues, releases  -> the matching site page
- relative .md links                                         -> the site page of that file
- relative images                                            -> raw.githubusercontent.com (so they show)
- other files of ours (code, plists)                         -> GitHub's file view, marked as leaving the site
- everything else (third-party sites)                        -> unchanged, opens in a new tab, marked as leaving
"""
import posixpath
import re
import urllib.parse

ATTR = re.compile(r'\b(href|src)="([^"]*)"')


def md_page(repo: str, path: str) -> str:
    """Site URL of a markdown file: docs/X.md -> /repo/docs/X/, dir/README.md -> /repo/dir/, README.md -> /repo/"""
    p = path[:-3] if path.lower().endswith(".md") else path
    base = posixpath.basename(p)
    if base.lower() == "readme":
        p = posixpath.dirname(p)
    return f"/{repo}/" + (urllib.parse.quote(p) + "/" if p else "")


class Linker:
    def __init__(self, org: str, repos: dict):
        """repos: name -> {"slug" (URL folder), "branch", "docs": set of md paths, "issues": set of numbers}"""
        self.org, self.repos = org, repos
        self.gh = re.compile(rf"^https?://github\.com/{re.escape(org)}/([^/?#]+)(/[^?#]*)?(\?[^#]*)?(#.*)?$", re.I)

    def _ours(self, repo, rest, anchor):
        """A github.com/<org>/<repo>/... URL -> site path, or None if the site has no page for it."""
        info = self.repos.get(repo)
        if not info:
            return None
        rest = (rest or "").rstrip("/")
        anchor = anchor or ""
        s = info["slug"]
        if rest == "":
            return f"/{s}/{anchor}"
        m = re.match(r"^/(?:blob|tree)/[^/]+/(.+)$", rest)
        if m:
            path = urllib.parse.unquote(m.group(1))
            if path.lower().endswith(".md") and (path in info["docs"] or path.lower() == "readme.md"):
                return md_page(s, path) + anchor
            return None
        m = re.match(r"^/issues/(\d+)$", rest)
        if m and int(m.group(1)) in info["issues"]:
            return f"/{s}/issues/{m.group(1)}/{anchor}"
        if rest in ("/issues", "/issues/new") or rest.startswith("/issues?"):
            return f"/{s}/issues/"
        m = re.match(r"^/releases(?:/tag/(.+))?$", rest)
        if m:
            return f"/{s}/releases/" + (f"#{urllib.parse.unquote(m.group(1))}" if m.group(1) else "")
        return None

    def rewrite(self, html: str, repo: str, doc_path: str = "README.md") -> str:
        info = self.repos[repo]
        branch = info["branch"]
        here = posixpath.dirname(doc_path)

        def one(m):
            attr, url = m.group(1), m.group(2)
            if not url or url.startswith(("#", "mailto:", "data:")):
                return m.group(0)
            if url.startswith(("http://", "https://")):
                g = self.gh.match(url)
                if g and attr == "src":
                    b = re.match(r"^/(?:blob|raw)/(.+)$", g.group(2) or "")
                    if b:
                        return f'src="https://raw.githubusercontent.com/{self.org}/{g.group(1)}/{b.group(1)}"'
                    return m.group(0)
                if g:
                    site = self._ours(g.group(1), g.group(2), g.group(4))
                    if site:
                        return f'{attr}="{site}"'
                return f'{attr}="{url}"' + (' data-ext="1"' if attr == "href" else "")
            if url.startswith("/"):   # root-relative github.com path, e.g. /watchthelight-labs/x/issues/3
                return one(re.match(ATTR, f'{attr}="https://github.com{url}"'))
            # relative to the file this HTML came from
            path, _, anchor = url.partition("#")
            path = urllib.parse.unquote(path.split("?")[0])
            target = posixpath.normpath(posixpath.join(here, path)) if path else doc_path
            if target.startswith("../"):
                return f'{attr}="https://github.com/{self.org}/{repo}"' + (' data-ext="1"' if attr == "href" else "")
            if attr == "src":
                return f'src="https://raw.githubusercontent.com/{self.org}/{repo}/{branch}/{urllib.parse.quote(target)}"'
            if target.lower().endswith(".md") and (target in info["docs"] or target.lower() == "readme.md"):
                return f'href="{md_page(info["slug"], target)}' + (f"#{anchor}" if anchor else "") + '"'
            kind = "blob" if "." in posixpath.basename(target) else "tree"
            return f'href="https://github.com/{self.org}/{repo}/{kind}/{branch}/{urllib.parse.quote(target)}" data-ext="1"'

        html = ATTR.sub(one, html)
        # GitHub prefixes heading ids with "user-content-"; strip it so #anchors work on the site
        html = html.replace('id="user-content-', 'id="').replace('name="user-content-', 'name="')
        # leaving the site: new tab, no opener, and a small arrow (merged into whatever the tag already has)
        return re.sub(r"<a\b[^>]*>", ext_tag, html)


def ext_tag(m):
    tag = m.group(0)
    if 'data-ext="1"' not in tag:
        return tag
    tag = re.sub(r'\s(?:data-ext|target|rel)="[^"]*"', "", tag)
    if re.search(r'\sclass="', tag):
        tag = re.sub(r'\sclass="([^"]*)"', r' class="\1 ext"', tag, count=1)
    else:
        tag = tag[:-1] + ' class="ext">'
    return tag[:-1] + ' target="_blank" rel="noopener">'
