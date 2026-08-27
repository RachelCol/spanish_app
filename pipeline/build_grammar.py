"""Emit the Comparisons lessons the app reads.

The lessons live in content/grammar.py as written prose -- this only serialises
them. It exists because data/grammar.json was previously produced by hand,
which meant editing the lessons and shipping them were separate acts and could
silently drift apart.
"""
import json
import sys

sys.path.insert(0, 'content')

import grammar  # noqa: E402


def main(out='data/grammar.json'):
    with open(out, 'w') as fh:
        json.dump(grammar.LESSONS, fh, ensure_ascii=False, separators=(',', ':'))
    pairs = sum(len(l['pairs']) for l in grammar.LESSONS)
    print(f'{len(grammar.LESSONS)} lessons, {pairs} pairs -> {out}')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'data/grammar.json')
