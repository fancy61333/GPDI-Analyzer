# -*- coding: utf-8 -*-
"""Leak guard: check built archives against what they are allowed to carry.

The graded character inventory is a third-party research asset and the
per-poem reference figures are not published yet, so a *distributed* archive
must carry neither. A private build, made on a machine that holds the
inventory, may carry it as the compressed `char_inventory.bin` - never as a
readable table.

Usage:
    python tools/audit_leak.py                # private profile: dist/*.zip
    python tools/audit_leak.py --public       # public profile: dist/*.zip
    python tools/audit_leak.py --public dist/x.zip

Exits non-zero if an archive violates the profile it is checked against.
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# never shippable in any profile: a readable inventory table
PLAIN_INVENTORY = re.compile(r'char_inventory\.(csv|tsv|txt|json)$', re.I)
# any trace of the inventory, packed or not
ANY_INVENTORY = re.compile(r'char_inventory\.', re.I)
# per-poem figures that are not published yet
WITHHELD = re.compile(r'(corpus_frozen|poems_82_text|titles_82)\.(csv|tsv)$', re.I)
# always fine
ALLOWED = ('variant_map.tsv',)


def verify(path: Path, public: bool):
    """Return (state, problems) for one archive under the given profile."""
    with zipfile.ZipFile(path) as z:
        names = [i.filename for i in z.infolist()]
    problems = []

    for n in names:
        base = n.rsplit('/', 1)[-1]
        if PLAIN_INVENTORY.search(base):
            problems.append(f'plain-text inventory shipped: {n}')
        if public and ANY_INVENTORY.search(base):
            problems.append(f'inventory shipped in a public archive: {n}')
        if public and WITHHELD.search(base):
            problems.append(f'unpublished reference figures shipped: {n}')

    if not public and not any(ANY_INVENTORY.search(n.rsplit('/', 1)[-1])
                              for n in names):
        problems.append('no inventory at all - private build is incomplete')

    if problems:
        return 'FAIL', problems
    return ('clean' if public else 'packed-only'), []


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith('--')]
    public = '--public' in argv[1:]
    profile = 'public' if public else 'private'
    targets = [Path(a) for a in args] or sorted((ROOT / 'dist').glob('*.zip'))
    if not targets:
        print('no archives to scan')
        return 0

    failed = False
    for p in targets:
        if not p.exists():
            print(f'{p.name}: missing')
            continue
        state, problems = verify(p, public)
        print(f'{p.name}: [{profile}] {state}')
        for msg in problems:
            print(f'    !! {msg}')
            failed = True
    if failed:
        print(f'\nFAIL: at least one archive violates the {profile} profile.')
    else:
        print(f'\nOK: every archive satisfies the {profile} profile '
              f'(allowed members: {", ".join(ALLOWED)}'
              + ('' if public else ' + char_inventory.bin') + ').')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
