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

By default this only rebuilds the lab's own data files. The lab's app code is
expected to diverge from main -- that is the entire point of it -- so a plain
run never touches lab/*.html, lab/*.css or lab/js/. Use --recreate to throw the
lab away and copy main over it, which is destructive and asks first.

The lab also has data of its own -- a prompt map keyed on Italian words, and a
sentence bank that requires both halves to contain the word. Those are rebuilt
here after the copy, so the lab is never left holding main's versions.
"""
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path('.')
LAB = ROOT / 'lab'

# Bump when the lab's own files change but main's have not, so the lab's
# service worker still sees a new cache name.
LAB_REV = 'a'

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
                rf"const CACHE = 'spanish-lab-v\1{LAB_REV}';", sw)
    # the lab is driven by a prompt map, not the collision list
    sw = sw.replace("  'data/collisions.json',", "  'data/prompts.json',")
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


def lab_data():
    for script in ('pipeline/build_prompts.py', 'pipeline/build_lab_sentences.py'):
        print(f'  {script} ...', flush=True)
        subprocess.run([sys.executable, script], check=True,
                       stdout=subprocess.DEVNULL)


if __name__ == '__main__':
    if '--recreate' in sys.argv:
        if LAB.exists() and '--force' not in sys.argv:
            raise SystemExit(
                'make_lab: --recreate deletes lab/ and copies main over it, '
                'discarding every change the lab has made.\n'
                'Commit lab/ first, then pass --force if that is really what '
                'you want.')
        copy()
        isolate()
        lab_data()
        n = sum(1 for _ in LAB.rglob('*') if _.is_file())
        cache = re.search(r"'(spanish-lab-[^']+)'", (LAB / 'sw.js').read_text())
        print(f'lab/ recreated from main: {n} files')
        print('  IndexedDB : spanish_app_lab')
        print('  cache     : ' + (cache.group(1) if cache else '?'))
        print('  manifest  : Spanish from Italian (Lab)')
    else:
        lab_data()
        print('lab data rebuilt. App code in lab/ left alone '
              '(use --recreate to copy main over it).')
