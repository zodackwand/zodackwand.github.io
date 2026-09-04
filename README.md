# zodackwand.github.io

Static HTML. No Jekyll, no dependencies, no JavaScript. The only tool is
`build.py`, which uses nothing outside the Python 3 standard library.

## Working on it

    python3 build.py --serve     build, then serve http://localhost:8000/
    python3 build.py             build only

There is no watcher: after an edit, re-run the command.

## What you edit

    _src/template.html        the page shell — every page uses this one
    _src/pages/index.html     front page
    _src/pages/research.html
    _src/pages/404.html
    _src/notes/*.html         one file per note
    style.css                 the entire design
    assets/img/               photo and favicons

Everything else in the repo root (`index.html`, `notes/`, `research/`,
`404.html`) is build output. It is committed so that GitHub Pages can serve
it, but never edited by hand — the next build overwrites it.

## Adding a note

    python3 build.py new "Trains, and the arithmetic of being late"

That creates `_src/notes/YYYY-MM-DD-slug.html`. Write the body in it, then
`python3 build.py`. The sidebar, the archive, the "recent notes" list on the
front page and the previous/next links all update themselves.

A note source is a couple of `key: value` lines, then `---`, then plain HTML:

    title: Trains, and the arithmetic of being late
    description: One sentence, used for the meta tag.
    ---

    <p>The body, as ordinary HTML.</p>

The date and the URL slug come from the filename, so renaming the file is how
you change either. Backdating a note means renaming it.

## Editing page text

`_src/pages/*.html` have the same shape. `{{recent}}` anywhere in the front
page body expands to the four most recent notes.

## Deploying

GitHub Pages serves the default branch from the repository root, and
`.nojekyll` tells it to serve the files as they are. Build, commit both the
sources and the output, merge into `main`.
