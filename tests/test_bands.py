# -*- coding: utf-8 -*-
"""Band consistency test.

Recomputes GPDI for all 82 reference poems and asserts that band_of() returns
exactly the frozen `final_band` from the study.

Also prints the resulting cut-points and band sizes, which are what the README
and the paper should quote.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'core'))
import gpdi

from _skip import require
require('data/poems_82_text.csv', 'data/corpus_frozen.csv')

BASE = os.path.join(HERE, '..')
FROZEN = os.path.join(BASE, 'data', 'corpus_frozen.csv')
TEXTS = os.path.join(BASE, 'data', 'poems_82_text.csv')

inv = gpdi.load_inventory()
bands = gpdi.load_reference_bands()

print('=' * 70)
print('GPDI Analyzer spec %s - band consistency test' % gpdi.SPEC_VERSION)
print('=' * 70)
print('scheme      :', bands['scheme'])
print('cut-points  :', bands['cuts'])
print('band sizes  :', bands['sizes'])
print('GPDI range  : %.2f - %.2f  (n=%d)' % (bands['min'], bands['max'], bands['n']))
print()

frozen = {}
with open(FROZEN, encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        if row.get('in_poetry_corpus') == 'Y' and row.get('is_duplicate') == 'N':
            frozen[row['id']] = row

mismatch = []
with open(TEXTS, encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

for r in rows:
    fr = frozen.get(r['id'])
    if fr is None:
        continue
    res = gpdi.analyze(r['text'], inv, bands)
    got = res.get('corpus_band')
    want = int(str(fr['final_band']).strip())
    if got != want:
        mismatch.append((r['clean_title'], r['id'], float(fr['GPDI']), res['GPDI'], want, got))

print('poems checked      : %d' % len(rows))
print('band mismatches    : %d' % len(mismatch))
for m in mismatch:
    print('   %s (id=%s): frozen GPDI %.2f band %d | computed GPDI %.2f band %s'
          % (m[0], m[1], m[2], m[4], m[3], m[5]))

ok = not mismatch
print()
print('RESULT: %s' % ('ALL 82 BANDS REPRODUCED' if ok else 'MISMATCH — see above'))
sys.exit(0 if ok else 1)
