"""Copy the app into lab/ as a second, independently installable PWA.

The point is somewhere to try changes that would be disruptive to make in
place -- dropping a study direction, rebuilding the sentence bank -- while the
app you actually use every day stays exactly as it is.

Three things must diverge or the two copies corrupt each other:

  the IndexedDB name   both copies live on one origin, so sharing the name
                       would mean sharing your progress, and a schema change
                       in the lab would migrate your real data
  the cache name       so a service worker update in one does not evict or
                       serve the other's files
  the manifest id      so the phone installs two apps rather than replacing
                       one with the other

Run it again to re-sync the lab with main; anything the lab has diverged on
is overwritten, which is the intended behaviour -- diverge in git, not here.
"""
import pathlib
import re
import shutil

ROOT = pathlib.Path('.')
LAB = ROOT / 'lab'

FILES = ['index.html', 'app.css', 'manifest.webmanifest', 'sw.js']
DIRS = ['js', 'data', 'icons']


def copy():
    if LAB.exists():
        shutil.rmtree(LAB)
    LAB.mkdir()
    for f in FILES:
        shutil.copy2(ROOT / f, LAB / f)
    for d in DIRS:
        shutil.copytree(ROOT / d, LAB / d)


def sub(path, pairs):
    p = LAB / path
    text = p.read_text()
    for old, new in pairs:
        if old not in text:
            raise SystemExit(f'make_lab: {path} no longer contains {old!r}')
        text = text.replace(old, new)
    p.write_text(text)


def isolate():
    sub('js/db.js', [("const DB_NAME = 'spanish_app';",
                      "const DB_NAME = 'spanish_app_lab';")])

    sw = (LAB / 'sw.js').read_text()
    sw = re.sub(r"const CACHE = 'spanish-app-v(\d+)';",
                r"const CACHE = 'spanish-lab-v\1';", sw)
    (LAB / 'sw.js').write_text(sw)

    sub('manifest.webmanifest', [
        ('"name": "Spanish from Italian"', '"id": "spanish-from-italian-lab",\n  '
                                           '"name": "Spanish from Italian (Lab)"'),
        ('"short_name": "Español"', '"short_name": "Español Lab"'),
    ])

    # A badge, so there is never a question which copy is on screen.
    sub('index.html', [
        ('<body>', '<body data-lab="1">'),
    ])
    css = (LAB / 'app.css').read_text() + """

/* --- lab build --- */
body[data-lab]::before {
  content: 'LAB';
  position: fixed; top: 0; left: 0; z-index: 99;
  padding: .12rem .45rem .18rem;
  font-size: .58rem; font-weight: 700; letter-spacing: .12em;
  color: var(--surface); background: var(--easy);
  border-bottom-right-radius: 6px;
  pointer-events: none;
}
"""
    (LAB / 'app.css').write_text(css)


if __name__ == '__main__':
    copy()
    isolate()
    n = sum(1 for _ in LAB.rglob('*') if _.is_file())
    print(f'lab/ rebuilt from main: {n} files')
    print('  IndexedDB : spanish_app_lab')
    print('  cache     : ' + re.search(r"'(spanish-lab-v\d+)'",
                                       (LAB / 'sw.js').read_text()).group(1))
    print('  manifest  : Spanish from Italian (Lab)')
