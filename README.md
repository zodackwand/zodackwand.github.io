# zodackwand.github.io

Hand-written static HTML. No Jekyll, no build step, no dependencies.

## Local preview

    python3 -m http.server 8000

Then open <http://localhost:8000/>.

## Layout

    index.html          front page
    notes/index.html    archive
    notes/<slug>/       one directory per note, containing index.html
    research/index.html
    404.html            served by GitHub Pages on a miss
    style.css           the entire design, ~4 KB
    rss.xml             hand-maintained feed
    .nojekyll           tells GitHub Pages to serve the files as-is

## Adding a note

Copy an existing `notes/<slug>/index.html`, change the title, date and body,
then add one line to `notes/index.html`, one to the "Recent notes" list on
`index.html`, and one `<item>` to `rss.xml`. That is deliberately manual: three
edits is cheap, and a build step is not.

## Deploying

GitHub Pages serves the default branch from the repository root. Merge into
`main` and it is live.
