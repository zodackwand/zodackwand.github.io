#!/usr/bin/env python3
"""Build the site.  Python 3 standard library only, no dependencies.

    python3 build.py            build into the repo root
    python3 build.py --serve    build, then serve http://localhost:8000/
    python3 build.py new "Some title"    start a new note

Everything you edit lives in _src/.  Everything the build writes to the
repo root is generated: index.html, notes/, research/, 404.html.
Exceptions, which are edited by hand and never touched by the build:
style.css, assets/, .nojekyll.
"""

import os, re, shutil, sys, datetime

SRC   = "_src"
OUT   = "."
SITE  = "Roman Bikbulatov"

# Sidebar sections, in order: (label, url, source page)
SECTIONS = [("Home", "/", "index"),
            ("Notes", "/notes/", None),
            ("Research", "/research/", "research")]

# Pages that are not notes: source name -> output path
PAGES = {"index": "index.html",
         "research": "research/index.html",
         "404": "404.html"}


# --- reading sources ------------------------------------------------

def parse(path):
    """Split `key: value` front matter from the body at the first '---'."""
    text = open(path, encoding="utf-8").read()
    head, _, body = text.partition("\n---\n")
    if not _:
        raise SystemExit(f"{path}: missing '---' separator after front matter")
    meta = {}
    for line in head.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    return meta, body.strip()


def load_notes():
    """Notes are _src/notes/YYYY-MM-DD-slug.html; date and slug come from
    the filename, so the front matter only needs a title."""
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
        notes.append({
            "slug":  slug,
            "url":   f"/notes/{slug}/",
            "date":  datetime.date(int(y), int(mo), int(d)),
            "title": meta["title"],
            "desc":  meta.get("description", ""),
            "body":  body,
        })
    notes.sort(key=lambda n: n["date"], reverse=True)
    return notes


# --- rendering ------------------------------------------------------

def fmt(date):
    return f"{date.day} {date:%b} {date.year}"


def sidebar(here):
    """Sections only. `here` is the url of the current page, so it can be
    marked; a note marks Notes."""
    out = ['<ul class="sect">']
    for label, url, _ in SECTIONS:
        cls = ' class="here"' if url == here or (
            url == "/notes/" and here.startswith("/notes/")) else ""
        out.append(f'<li{cls}><a href="{url}">{label}</a></li>')
    out.append("</ul>")
    return "\n".join(out)


def entries(notes, show_year=True):
    out = ['<ul class="entries">']
    for n in notes:
        d = fmt(n["date"]) if show_year else f'{n["date"].day} {n["date"]:%b}'
        out.append(f'<li><span class="d">{d}</span>'
                   f'<a href="{n["url"]}">{n["title"]}</a></li>')
    out.append("</ul>")
    return "\n".join(out)


def section(body, name, keep):
    """Drop a {{#name}}...{{/name}} block unless `keep`; keep just its
    contents when we do."""
    pat = re.compile(r"\{\{#%s\}\}(.*?)\{\{/%s\}\}" % (name, name), re.S)
    return pat.sub((lambda m: m.group(1).strip()) if keep else "", body)


def write(path, html):
    path = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    open(path, "w", encoding="utf-8").write(html)
    print(f"  {path}  {len(html)} b")


def render(tpl, *, title, desc, here, content, crumbs):
    page = tpl
    for key, value in [("title", title), ("description", desc),
                       ("nav", sidebar(here)),
                       ("content", content), ("crumbs", crumbs)]:
        page = page.replace("{{%s}}" % key, value)
    return page


# --- the build ------------------------------------------------------

def build():
    tpl   = open(f"{SRC}/template.html", encoding="utf-8").read()
    notes = load_notes()
    print("building:")

    for name, out in PAGES.items():
        meta, body = parse(f"{SRC}/pages/{name}.html")
        here = "/" if name == "index" else f"/{name}/"
        body = section(body, "notes", bool(notes))
        body = body.replace("{{recent}}", entries(notes[:4]))
        crumbs = (f'<a href="/">{SITE}</a>: {meta["title"]}'
                  if name != "index" else SITE)
        write(out, render(tpl, title=meta.get("head_title", meta["title"]),
                          desc=meta.get("description", ""), here=here,
                          content=body, crumbs=crumbs))

    # Notes archive, grouped by year, newest first.
    body = ["<h1>Notes</h1>"]
    if not notes:
        body.append("<p>Nothing here yet.</p>")
    for year in sorted({n["date"].year for n in notes}, reverse=True):
        body.append(f'<h2 class="year">{year}</h2>')
        body.append(entries([n for n in notes if n["date"].year == year], False))
    write("notes/index.html",
          render(tpl, title=f"Notes — {SITE}", desc="Everything written, newest first.",
                 here="/notes/", content="\n".join(body),
                 crumbs=f'<a href="/">{SITE}</a>: Notes'))

    # One directory per note, so URLs stay clean.
    for i, n in enumerate(notes):
        nav = []
        if i + 1 < len(notes):                       # older
            nav.append(f'<a href="{notes[i+1]["url"]}">&larr; {notes[i+1]["title"]}</a>')
        if i > 0:                                    # newer
            nav.append(f'<a href="{notes[i-1]["url"]}">{notes[i-1]["title"]} &rarr;</a>')
        content = (f'<h1>{n["title"]}</h1>\n'
                   f'<div class="date">{fmt(n["date"])}</div>\n{n["body"]}\n'
                   + (f'<p class="prevnext">{" ".join(nav)}</p>' if nav else ""))
        write(f'notes/{n["slug"]}/index.html',
              render(tpl, title=n["title"], desc=n["desc"], here=n["url"],
                     content=content,
                     crumbs=f'<a href="/">{SITE}</a>: '
                            f'<a href="/notes/">Notes</a>: {n["title"]}'))

    print(f"done: {len(notes)} notes")


def new(title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    path = f"{SRC}/notes/{datetime.date.today()}-{slug}.html"
    if os.path.exists(path):
        raise SystemExit(f"{path} already exists")
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
