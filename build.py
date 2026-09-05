#!/usr/bin/env python3
"""Build the site.  Python 3 standard library only, no dependencies.

    python3 build.py            build into the repo root
    python3 build.py --serve    build, then serve http://localhost:8000/
    python3 build.py new "Some title"    start a new note

Everything you edit lives in _src/.  Everything the build writes to the
repo root is generated: index.html, notes/, research/, 404.html,
sitemap.xml, robots.txt.  Exceptions, edited by hand and never touched by
the build: style.css, assets/, favicon.ico, .nojekyll.
"""

import os, re, sys, datetime

SRC  = "_src"
OUT  = "."
SITE = "Roman Bikbulatov"
BASE = "https://zodackwand.github.io"

# Sidebar sections, in order: (label, url)
SECTIONS = [("Home", "/"), ("Now", "/now/"),
            ("Notes", "/notes/"), ("Research", "/research/")]

# Pages that are not notes: source name -> (output path, url)
PAGES = {"index":    ("index.html", "/"),
         "now":      ("now/index.html", "/now/"),
         "research": ("research/index.html", "/research/"),
         "404":      ("404.html", "/404.html")}


# --- reading sources ------------------------------------------------

def parse(path):
    """Split `key: value` front matter from the body at the first '---'."""
    text = open(path, encoding="utf-8").read()
    head, sep, body = text.partition("\n---\n")
    if not sep:
        raise SystemExit(f"{path}: missing '---' separator after front matter")
    meta = {}
    for line in head.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    meta["mtime"] = datetime.date.fromtimestamp(os.path.getmtime(path))
    return meta, body.strip()


def load_notes():
    """Notes are _src/notes/YYYY-MM-DD-slug.html; the date and the URL slug
    come from the filename, so the front matter only needs a title."""
    notes = []
    if not os.path.isdir(f"{SRC}/notes"):
        return notes
    for name in sorted(os.listdir(f"{SRC}/notes")):
        if not name.endswith(".html"):
            continue
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})-(.+)\.html$", name)
        if not m:
            raise SystemExit(f"{name}: expected YYYY-MM-DD-slug.html")
        y, mo, d, slug = m.groups()
        meta, body = parse(f"{SRC}/notes/{name}")
        notes.append({"slug": slug, "url": f"/notes/{slug}/",
                      "date": datetime.date(int(y), int(mo), int(d)),
                      "title": meta["title"], "desc": meta.get("description", ""),
                      "mtime": meta["mtime"], "body": body})
    notes.sort(key=lambda n: n["date"], reverse=True)
    return notes


# --- fragments ------------------------------------------------------

def fmt(date):
    return f"{date.day} {date:%B} {date.year}"


def time_tag(date, text=None):
    return f'<time datetime="{date.isoformat()}">{text or fmt(date)}</time>'


def sidebar(here):
    out = ['<ul class="sect">']
    for label, url in SECTIONS:
        current = url == here or (url == "/notes/" and here.startswith("/notes/"))
        out.append(f'<li{" class=\"here\"" if current else ""}>'
                   f'<a href="{url}">{label}</a></li>')
    out.append("</ul>")
    return "\n".join(out)


def entries(notes, year=True):
    out = ['<ul class="entries">']
    for n in notes:
        label = fmt(n["date"]) if year else f'{n["date"].day} {n["date"]:%B}'
        out.append(f'<li><span class="d">{time_tag(n["date"], label)}</span>'
                   f'<a href="{n["url"]}">{n["title"]}</a></li>')
    out.append("</ul>")
    return "\n".join(out)


def section(body, name, keep):
    """Drop a {{#name}}...{{/name}} block unless `keep`; keep just its
    contents when we do."""
    pat = re.compile(r"\{\{#%s\}\}(.*?)\{\{/%s\}\}" % (name, name), re.S)
    return pat.sub((lambda m: m.group(1).strip()) if keep else "", body)


def anchors(body):
    """Give every h2/h3 an id and a link to itself, so sections in a long
    note can be linked to. The marker is invisible until hovered."""
    def one(m):
        level, text = m.group(1), m.group(2)
        slug = re.sub(r"[^a-z0-9]+", "-", re.sub("<[^>]+>", "", text).lower()).strip("-")
        return (f'<h{level} id="{slug}">{text}'
                f'<a class="anchor" href="#{slug}" aria-label="Link to this section">#</a>'
                f'</h{level}>')
    return re.sub(r"<h([23])>(.*?)</h\1>", one, body, flags=re.S)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")


# --- rendering ------------------------------------------------------

def write(path, text):
    path = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    open(path, "w", encoding="utf-8").write(text)
    print(f"  {path}  {len(text)} b")


def render(tpl, **v):
    v["nav"] = sidebar(v["here"])
    v.setdefault("ogtype", "website")
    v["canonical"] = BASE + v["here"]
    v["description"] = esc(v.get("description", ""))
    v["title"] = esc(v["title"])
    for key, value in v.items():
        tpl = tpl.replace("{{%s}}" % key, str(value))
    return tpl


# --- the build ------------------------------------------------------

def build():
    tpl   = open(f"{SRC}/template.html", encoding="utf-8").read()
    notes = load_notes()
    urls  = []
    print("building:")

    for name, (out, url) in PAGES.items():
        meta, body = parse(f"{SRC}/pages/{name}.html")
        body = section(body, "notes", bool(notes))
        body = anchors(body.replace("{{recent}}", entries(notes[:4])))
        write(out, render(tpl, title=meta.get("head_title", meta["title"]),
                          description=meta.get("description", ""), here=url,
                          content=body, updated=time_tag(meta["mtime"]),
                          crumbs=(SITE if name == "index" else
                                  f'<a href="/">{SITE}</a>: {meta["title"]}')))
        if name != "404":
            urls.append((url, meta["mtime"]))

    # Archive, grouped by year, newest first.
    body = ["<h1>Notes</h1>"]
    if not notes:
        body.append("<p>Nothing here yet.</p>")
    for year in sorted({n["date"].year for n in notes}, reverse=True):
        body.append(f'<h2 class="year">{year}</h2>')
        body.append(entries([n for n in notes if n["date"].year == year], False))
    newest = max([n["mtime"] for n in notes], default=datetime.date.today())
    write("notes/index.html",
          render(tpl, title=f"Notes — {SITE}", description="Everything written, newest first.",
                 here="/notes/", content="\n".join(body), updated=time_tag(newest),
                 crumbs=f'<a href="/">{SITE}</a>: Notes'))
    urls.append(("/notes/", newest))

    # One directory per note, so the URLs stay clean.
    for i, n in enumerate(notes):
        nav = []
        if i + 1 < len(notes):
            nav.append(f'<a href="{notes[i+1]["url"]}">&larr; {notes[i+1]["title"]}</a>')
        if i > 0:
            nav.append(f'<a href="{notes[i-1]["url"]}">{notes[i-1]["title"]} &rarr;</a>')
        write(f'notes/{n["slug"]}/index.html',
              render(tpl, title=n["title"], description=n["desc"], here=n["url"],
                     updated=time_tag(n["mtime"]), ogtype="article",
                     content=f'<article>\n<h1>{n["title"]}</h1>\n'
                             f'<div class="date">{time_tag(n["date"])}</div>\n'
                             f'{anchors(n["body"])}\n</article>'
                             + (f'<p class="prevnext">{" ".join(nav)}</p>' if nav else ""),
                     crumbs=f'<a href="/">{SITE}</a>: <a href="/notes/">Notes</a>: {n["title"]}'))
        urls.append((n["url"], n["mtime"]))

    write("sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{BASE}{u}</loc><lastmod>{m}</lastmod></url>\n"
                    for u, m in urls)
          + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")

    print(f"done: {len(notes)} notes, {len(urls)} urls")


def new(title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    path = f"{SRC}/notes/{datetime.date.today()}-{slug}.html"
    if os.path.exists(path):
        raise SystemExit(f"{path} already exists")
    os.makedirs(f"{SRC}/notes", exist_ok=True)
    open(path, "w", encoding="utf-8").write(
        f"title: {title}\ndescription: \n---\n\n<p>Write here.</p>\n")
    print(f"created {path}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "new":
        new(" ".join(args[1:]) or "Untitled")
    else:
        build()
        if args and args[0] == "--serve":
            import http.server, socketserver
            os.chdir(OUT)
            print("\nhttp://localhost:8000/   (ctrl-c to stop)")
            socketserver.TCPServer.allow_reuse_address = True
            socketserver.TCPServer(("127.0.0.1", 8000),
                http.server.SimpleHTTPRequestHandler).serve_forever()
