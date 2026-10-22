# <wtl> project: watchthelight-labs.github.io | file: sitegen/render.py | author: watchthelight </wtl>
"""Page templates. Every page goes through shell() (src/page.html): header, nav, starfield, footer."""
import datetime as dt
import html
import re
from pathlib import Path

from .links import md_page

SRC = Path(__file__).resolve().parents[1] / "src"
LANG = {"C": "#8a8e96", "C++": "#c45454", "Python": "#b8a44a", "Rust": "#c8885a", "Shell": "#6a9a6e",
        "Swift": "#d0805a", "Objective-C": "#5a8ab8", "TypeScript": "#5a8ab8", "JavaScript": "#c8b85a"}
BADGE = "style=flat-square&labelColor=0d0e12"
CUR = ' aria-current="page"'


def esc(s):
    return html.escape(s or "", quote=True)


def when(iso):
    return iso[:10] if iso else ""


def ago(iso):
    if not iso:
        return ""
    d = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if d.days >= 365:
        return f"{d.days // 365} y ago"
    if d.days >= 30:
        return f"{d.days // 30} mo ago"
    if d.days >= 1:
        return f"{d.days} d ago"
    h = d.seconds // 3600
    return f"{h} h ago" if h else "just now"


class Pages:
    def __init__(self, site: dict, built: str):
        self.site, self.built = site, built
        self.tpl = (SRC / "page.html").read_text(encoding="utf-8")

    def shell(self, path, title, desc, body, og="/og.png", nav=""):
        out = self.tpl
        for key in ("HOME", "RESEARCH", "AGENTS", "ABOUT"):
            out = out.replace(f"{{{{NAV_{key}}}}}", ' aria-current="page"' if nav == key else "")
        return (out.replace("{{TITLE}}", esc(title)).replace("{{DESC}}", esc(desc)).replace("{{SITE}}", self.site["url"])
                .replace("{{PATH}}", path).replace("{{OG}}", og).replace("{{BODY}}", body).replace("{{BUILT}}", self.built))

    # ---------- home ----------
    def tile(self, r):
        n, o, s = r["name"], self.site["org"], r["slug"]
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
        rel = f'<a href="/{s}/releases/">releases</a>' if r["releases"] else ""
        iss = f'<a href="/{s}/issues/">issues</a>' if r["issues"] else ""
        return f"""<article class="tile">
  <h4><a href="/{s}/">{esc(n)}</a></h4>
  <p>{esc(r['description'])}</p>
  <div class="meta">{lang}{stars}<span>updated {ago(r['pushed'])}</span></div>
  <div class="badges">{''.join(badges)}</div>
  <div class="links"><a href="/{s}/">read</a>{rel}{iss}</div>
</article>"""

    def home(self, repos):
        s, f = self.site, self.site["featured"]
        shown = [r for r in repos if not r["hidden"]]
        by = {r["name"]: r for r in shown}
        groups = [dict(g) for g in s["groups"]]
        rest = sorted((r["name"] for r in shown if not any(r["name"] in g["repos"] for g in groups)), key=str.lower)
        if rest:
            groups.append({"title": s["other_group"], "repos": rest})
        sections, i = [], 0
        for g in groups:
            items = [by[n] for n in g["repos"] if n in by]
            if not items:
                continue
            i += 1
            sections.append(f"""<section class="group">
  <div class="group-head"><span class="n">{i:02d}</span><h3>{esc(g['title'])}</h3><span class="rule"></span></div>
  <div class="grid">{''.join(self.tile(r) for r in items)}</div>
</section>""")
        head = esc(s["headline"]).replace(esc(s["headline_accent"]), f'<span>{esc(s["headline_accent"])}</span>', 1)
        body = f"""  <main>
    <section class="hero">
      <h1>{head}</h1>
      <p>{esc(s['intro'])}</p>
      <div class="stats" role="list">
        <div role="listitem"><b>{len(shown)}</b><small>repositories</small></div>
        <div role="listitem"><b>{sum(1 for r in shown if r['release'])}</b><small>with releases</small></div>
        <div role="listitem"><b>26.7.1</b><small>macOS Tahoe</small></div>
      </div>
    </section>
    <section class="legion" aria-labelledby="legion-title">
      <div>
        <div class="eyebrow">the machine</div>
        <h2 id="legion-title">{esc(f['name'])}</h2>
        <div class="machine">{esc(f['machine'])}</div>
        <div class="chips">{''.join(f'<span class="chip">{esc(x)}</span>' for x in f['specs'])}<span class="chip os">{esc(f['os'])}</span></div>
      </div>
      <div>
        <ul class="works">{''.join(f'<li>{esc(w)}</li>' for w in f['works'])}</ul>
        <div class="next">{esc(f['next'])}</div>
      </div>
    </section>
    {''.join(sections)}
    <section class="duo">
      <div class="panel"><h3>Research</h3><p>{esc(s['research_blurb'])}</p><a href="/research/">Open the research pages</a></div>
      <div class="panel"><h3>Agents</h3><p>{esc(s['agents_blurb'])}</p><a href="/agents/">See how it's set up</a></div>
    </section>
  </main>"""
        return self.shell("/", s["title"], s["description"], body, nav="HOME")

    # ---------- repo pages ----------
    def side(self, r, here):
        n, o, s = r["name"], self.site["org"], r["slug"]
        rows = [("Language", esc(r["language"] or "-")), ("Licence", esc(r["license"] if r["license"] not in (None, "NOASSERTION") else "see repo")),
                ("Updated", ago(r["pushed"]))]
        if r["release"]:
            rows.insert(0, ("Release", f'<a href="/{s}/releases/">{esc(r["release"])}</a>'))
        if r["stars"]:
            rows.append(("Stars", str(r["stars"])))
        meta = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
        docs = sorted(r["docs"])
        doc_links = "".join(
            f'<li><a href="{md_page(s, p)}"{CUR if p == here else ""}>{esc(p[:-3])}</a></li>' for p in docs)
        docs_html = ""
        if docs:
            open_ = " open" if len(docs) <= 12 or (here and here != "README.md") else ""
            docs_html = f'<details class="side-docs"{open_}><summary>Docs ({len(docs)})</summary><ul>{doc_links}</ul></details>'
        clone = f"git clone https://github.com/{o}/{n}"
        open_issues = sum(1 for i in r["issues"] if i["state"] == "open")
        sub = []
        if here != "README.md" or True:
            sub.append(f'<a href="/{s}/"{CUR if here == "README.md" else ""}>Overview</a>')
        if r["releases"]:
            sub.append(f'<a href="/{s}/releases/"{CUR if here == "#releases" else ""}>Releases ({len(r["releases"])})</a>')
        if r["issues"]:
            sub.append(f'<a href="/{s}/issues/"{CUR if here == "#issues" else ""}>Issues ({open_issues} open)</a>')
        return f"""<aside class="side">
  <div class="side-title"><a href="/{s}/">{esc(n)}</a></div>
  <p class="side-desc">{esc(r['description'])}</p>
  <nav class="side-nav" aria-label="{esc(n)}">{''.join(sub)}</nav>
  <dl class="side-meta">{meta}</dl>
  <div class="clone"><code>{esc(clone)}</code><button type="button" data-copy="{esc(clone)}">copy</button></div>
  {docs_html}
  <a class="ext gh" href="{r['url']}" target="_blank" rel="noopener">View on GitHub</a>
</aside>"""

    def crumbs(self, r, parts):
        items = [f'<a href="/">Repositories</a>', f'<a href="/{r["slug"]}/">{esc(r["name"])}</a>'] + parts
        return f'<nav class="crumbs" aria-label="Breadcrumb">{" / ".join(items)}</nav>'

    def repo_layout(self, r, here, crumbs, content):
        return f"""  <main class="repo">
    {crumbs}
    <div class="repo-grid">
      {self.side(r, here)}
      <article class="prose">{content}</article>
    </div>
  </main>"""

    def repo_page(self, r, readme_html):
        body = self.repo_layout(r, "README.md", self.crumbs(r, []), readme_html or "<p>No README yet.</p>")
        return self.shell(f"/{r['slug']}/", f"{r['name']} · watchthelight labs", r["description"] or r["name"], body,
                          og=f"/{r['slug']}/og.png", nav=self.nav_for(r))

    def doc_page(self, r, path, html_):
        url = md_page(r["slug"], path)
        parts = path[:-3].split("/")
        body = self.repo_layout(r, path, self.crumbs(r, [esc(p) for p in parts]), html_)
        return self.shell(url, f"{parts[-1]} · {r['name']}", f"{r['name']}: {path}", body,
                          og=f"/{r['slug']}/og.png", nav=self.nav_for(r))

    def releases_page(self, r, linker):
        out = []
        for x in r["releases"]:
            assets = "".join(f'<li><a class="ext" href="{a["url"]}" target="_blank" rel="noopener">{esc(a["name"])}</a>'
                             f' <span class="dim">{a["size"] // 1024} KB · {a["downloads"]} downloads</span></li>'
                             for a in x["assets"])
            pre = ' <span class="tag-pre">pre-release</span>' if x["prerelease"] else ""
            out.append(f"""<section class="release" id="{esc(x['tag'])}">
  <h2>{esc(x['name'])}{pre}</h2>
  <div class="dim">{esc(x['tag'])} · {when(x['published'])}</div>
  <div class="prose-inner">{linker.rewrite(x['body_html'], r['name']) or '<p class="dim">No notes.</p>'}</div>
  {f'<h3>Downloads</h3><ul class="assets">{assets}</ul>' if assets else ''}
</section>""")
        body = self.repo_layout(r, "#releases", self.crumbs(r, ["Releases"]), "<h1>Releases</h1>" + "".join(out))
        return self.shell(f"/{r['slug']}/releases/", f"Releases · {r['name']}", f"Every release of {r['name']}", body,
                          og=f"/{r['slug']}/og.png", nav=self.nav_for(r))

    def issues_page(self, r):
        def row(i):
            labels = "".join(f'<span class="label">{esc(l)}</span>' for l in i["labels"])
            state = f'<span class="state {i["state"]}">{i["state"]}</span>'
            return (f'<li>{state}<a href="/{r["slug"]}/issues/{i["number"]}/">#{i["number"]} {esc(i["title"])}</a>'
                    f'<div class="dim">{esc(i["user"])} · opened {ago(i["created"])} · {len(i["comments"])} comments {labels}</div></li>')
        open_ = [i for i in r["issues"] if i["state"] == "open"]
        closed = [i for i in r["issues"] if i["state"] != "open"]
        content = (f"<h1>Issues</h1><p class=\"dim\">To open a new one, use <a class=\"ext\" href=\"{r['url']}/issues/new/choose\" "
                   f"target=\"_blank\" rel=\"noopener\">GitHub</a>.</p>"
                   + (f"<h2>Open ({len(open_)})</h2><ul class=\"issue-list\">{''.join(row(i) for i in open_)}</ul>" if open_ else "<p>No open issues.</p>")
                   + (f"<h2>Closed ({len(closed)})</h2><ul class=\"issue-list\">{''.join(row(i) for i in closed)}</ul>" if closed else ""))
        body = self.repo_layout(r, "#issues", self.crumbs(r, ["Issues"]), content)
        return self.shell(f"/{r['slug']}/issues/", f"Issues · {r['name']}", f"Issues for {r['name']}", body,
                          og=f"/{r['slug']}/og.png", nav=self.nav_for(r))

    def issue_page(self, r, i, linker):
        n, s = r["name"], r["slug"]

        def post(user, created, body_html, first=False, url=""):
            idattr = f' id="{url.rpartition("#")[2]}"' if "#issuecomment-" in url else ""
            return (f'<div class="post{" first" if first else ""}"{idattr}><div class="post-head"><b>{esc(user)}</b>'
                    f' <span class="dim">{when(created)}</span></div>'
                    f'<div class="prose-inner">{linker.rewrite(body_html, n) or "<p class=dim>(no text)</p>"}</div></div>')
        labels = "".join(f'<span class="label">{esc(l)}</span>' for l in i["labels"])
        thread = post(i["user"], i["created"], i["body_html"], True) + "".join(post(c["user"], c["created"], c["body_html"], url=c["url"]) for c in i["comments"])
        content = (f'<h1>{esc(i["title"])} <span class="dim">#{i["number"]}</span></h1>'
                   f'<div class="issue-meta"><span class="state {i["state"]}">{i["state"]}</span>{labels}</div>{thread}'
                   f'<p class="reply"><a class="ext" href="{i["url"]}" target="_blank" rel="noopener">Reply on GitHub</a></p>')
        body = self.repo_layout(r, "#issues", self.crumbs(r, [f'<a href="/{s}/issues/">Issues</a>', f"#{i['number']}"]), content)
        return self.shell(f"/{s}/issues/{i['number']}/", f"{i['title']} · {n} #{i['number']}",
                          f"{n} issue #{i['number']}: {i['title']}", body, og=f"/{s}/og.png", nav=self.nav_for(r))

    @staticmethod
    def nav_for(r):
        return {"research": "RESEARCH", "agents": "AGENTS"}.get(r["name"], "HOME")

    # ---------- about, 404, site ----------
    def about(self):
        a = self.site["about"]
        paras = "".join(f"<p>{x}</p>" for x in a["paragraphs"])
        contact = "".join(f'<li><a class="ext" href="{esc(c["url"])}" target="_blank" rel="noopener">{esc(c["label"])}</a></li>'
                          for c in a["contact"])
        body = f"""  <main class="page">
    <article class="prose">
      <h1>About</h1>
      {paras}
      <h2>Get in touch</h2>
      <ul>{contact}</ul>
      <p>Questions about one project are best asked on that project's issues page, so the answer helps the next person too.</p>
    </article>
  </main>"""
        return self.shell("/about/", "About · watchthelight labs", a["description"], body, nav="ABOUT")

    def not_found(self):
        body = """  <main class="page"><article class="prose"><h1>Not here</h1>
    <p>That page doesn't exist, or a repository was renamed. The <a href="/">repository list</a> has everything.</p></article></main>"""
        return self.shell("/404.html", "Not found · watchthelight labs", "Page not found", body)
