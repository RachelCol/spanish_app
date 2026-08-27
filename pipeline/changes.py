"""What moved since the last commit.

The deck is rebuilt often and by scripts, and until now the only way to know
what a rebuild did was to notice a card misbehaving during review. This prints
the difference between the deck in the working tree and the deck as committed
-- cards gained and lost, senses rewritten, parts of speech changed, Italian
words that can or can no longer be asked.

Git is the snapshot: there is no second copy of the deck to keep in step, and
the comparison is always against the last state that was deliberately saved.
Rebuild five times before committing and you see the total of all five, which
is the useful thing to see.

    python pipeline/changes.py            # against the last commit
    python pipeline/changes.py HEAD~5     # against any earlier point
    python pipeline/changes.py stable-v56 # against a tag
"""
import json
import subprocess
import sys


def committed(path, ref="HEAD"):
    """`path` as of `ref`, or None if it is not there."""
    try:
        out = subprocess.run(["git", "show", f"{ref}:{path}"],
                             capture_output=True, check=True)
        return json.loads(out.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def by_id(deck):
    return {c["es"]: c for c in deck}


def pos_of(card):
    groups = {"vblex": "vblex", "vbmod": "vblex", "vbhaver": "vblex",
              "vbser": "vblex", "adv": "adv", "preadv": "adv",
              "cnjcoo": "cnj", "cnjsub": "cnj", "cnjadv": "cnj"}
    tags = card.get("pos_all") or [card.get("pos")]
    return sorted({groups.get(str(t), str(t)) for t in tags if t})


def deck_changes(old, new):
    o, n = by_id(old), by_id(new)
    added = sorted(set(n) - set(o))
    removed = sorted(set(o) - set(n))
    resensed, reposed = [], []
    for w in sorted(set(o) & set(n)):
        if o[w].get("senses") != n[w].get("senses"):
            resensed.append((w, o[w]["senses"], n[w]["senses"]))
        if pos_of(o[w]) != pos_of(n[w]):
            reposed.append((w, pos_of(o[w]), pos_of(n[w])))
    return added, removed, resensed, reposed, o, n


def prompt_changes(old, new):
    if old is None or new is None:
        return [], [], []
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = []
    for p in sorted(set(old) & set(new)):
        a = [x["es"] for x in old[p]]
        b = [x["es"] for x in new[p]]
        if a != b:
            changed.append((p, a, b))
    return added, removed, changed


def report(ref="HEAD"):
    new_deck = json.load(open("data/deck.json"))
    old_deck = committed("data/deck.json", ref)
    if old_deck is None:
        return f"data/deck.json is not in {ref} — nothing to compare against.\n"

    added, removed, resensed, reposed, o, n = deck_changes(old_deck, new_deck)
    p_add, p_del, p_chg = prompt_changes(committed("data/prompts.json", ref),
                                         json.load(open("data/prompts.json")))

    L = []
    w = L.append
    w(f"# What changed since {ref}\n")
    w(f"Cards: {len(old_deck)} → {len(new_deck)}  "
      f"({len(added)} added, {len(removed)} removed, "
      f"{len(resensed)} redefined, {len(reposed)} re-tagged)\n")

    if removed:
        w(f"\n## Cards removed ({len(removed)})\n")
        for word in removed:
            w(f"- **{word}** — was {', '.join(o[word]['senses'])} "
              f"[{o[word]['tier']}]")
    if added:
        w(f"\n## Cards added ({len(added)})\n")
        for word in added:
            w(f"- **{word}** — {', '.join(n[word]['senses'])} "
              f"[{n[word]['tier']}]")
    if resensed:
        w(f"\n## Definitions changed ({len(resensed)})\n")
        for word, before, after in resensed:
            gone = [s for s in before if s not in after]
            new_ = [s for s in after if s not in before]
            bits = []
            if gone:
                bits.append("dropped " + ", ".join(gone))
            if new_:
                bits.append("added " + ", ".join(new_))
            w(f"- **{word}** — {'; '.join(bits) or 'reordered'}  "
              f"(`{', '.join(before)}` → `{', '.join(after)}`)")
    if reposed:
        w(f"\n## Parts of speech changed ({len(reposed)})\n")
        for word, before, after in reposed:
            w(f"- **{word}** — {', '.join(before)} → {', '.join(after)}")

    if p_add or p_del or p_chg:
        w(f"\n## Italian prompts\n")
        w(f"{len(p_del)} can no longer be asked, {len(p_add)} newly askable, "
          f"{len(p_chg)} answer differently\n")
        for p in p_del:
            w(f"- **{p}** — gone")
        for p in p_add:
            w(f"- **{p}** — new")
        for p, before, after in p_chg:
            w(f"- **{p}** — {', '.join(before)} → {', '.join(after)}")

    if not any([added, removed, resensed, reposed, p_add, p_del, p_chg]):
        w("\nNothing changed.")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    text = report(sys.argv[1] if len(sys.argv) > 1 else "HEAD")
    with open("changes.md", "w") as fh:
        fh.write(text)
    # Print the head of it; the file has everything.
    lines = text.splitlines()
    print("\n".join(lines[:40]))
    if len(lines) > 40:
        print(f"\n... {len(lines) - 40} more lines in changes.md")
