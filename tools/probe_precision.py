# -*- coding: utf-8 -*-
"""Two precision probes.

1) Which coefficient set reproduces the published GPDI_char column exactly —
   the rounded 0.50/0.278/0.222, or the exact renormalisation 25/90, 20/90?
2) Where do the baseline band cut-points land once the published two-decimal
   scale is used (27.19/30.24) instead of raw recomputed scores (27.20/30.25)?
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, '..')
FROZEN = os.path.join(BASE, 'data', 'corpus_frozen.csv')

sys.path.insert(0, os.path.join(BASE, 'core'))
import gpdi

rows = []
with open(FROZEN, encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if r.get('in_poetry_corpus') == 'Y' and r.get('is_duplicate') == 'N':
            rows.append(r)

def col(r, k):
    return float(r[k])

print('=' * 74)
print('PROBE 1 - GPDI_char coefficients')
print('=' * 74)

cands = {
    '0.50 / 0.278 / 0.222 (rounded, as printed in 4.6)': (0.50, 0.278, 0.222),
    'exact 25/90 = 0.277778, 20/90 = 0.222222':          (0.50, 25 / 90.0, 20 / 90.0),
}
for name, (a, h, o) in cands.items():
    dev = []
    for r in rows:
        calc = 100.0 * (a * col(r, 'ACD_star') + h * col(r, 'HDCR') + o * col(r, 'OOVR'))
        dev.append(abs(calc - col(r, 'GPDI_char')))
    print('  %-52s max dev %.4f  mean %.4f' % (name, max(dev), sum(dev) / len(dev)))

print()
print('  published GPDI_char vs GPDI: is GPDI = 0.90*GPDI_char + 10*TL* ?')
dev2 = [abs(100.0 * (0.45 * col(r, 'ACD_star') + 0.25 * col(r, 'HDCR')
                     + 0.20 * col(r, 'OOVR') + 0.10 * col(r, 'TL_star')) - col(r, 'GPDI'))
        for r in rows]
print('  max dev (published columns only) : %.4f' % max(dev2))

print()
print('=' * 74)
print('PROBE 2 - band cut-points on the published two-decimal scale')
print('=' * 74)

by_band = {}
for r in rows:
    by_band.setdefault(int(r['final_band']), []).append(r)

for b in sorted(by_band):
    vals = sorted(col(r, 'GPDI') for r in by_band[b])
    ns = sorted(int(r['N']) for r in by_band[b])
    print('  band %d: n=%-3d GPDI %6.2f - %6.2f   N %d - %d'
          % (b, len(vals), vals[0], vals[-1], ns[0], ns[-1]))

frac = lambda x: round(x - int(x), 3)
print()
print('  lowest GPDI of each band, and its fractional part:')
for b in sorted(by_band):
    v = min(col(r, 'GPDI') for r in by_band[b])
    print('    band %d min = %6.2f  (raw is 2dp already: %s)' % (b, v, v))

# recompute from text and show the boundary poems raw vs published
bands = gpdi.load_reference_bands()
inv = gpdi.load_inventory()
texts = {}
with open(os.path.join(BASE, 'data', 'poems_82_text.csv'), encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        texts[r['id']] = r['text']

print()
print('  boundary poems: recomputed raw GPDI vs the published value')
for target in (21.63, 25.17, 27.19, 30.24):
    near = sorted(rows, key=lambda r: abs(col(r, 'GPDI') - target))[:2]
    for r in near:
        res = gpdi.analyze(texts[r['id']], inv)
        print('    %-14s published %6.2f  recomputed %9.6f -> round %6.2f  band %s'
              % (r['clean_title'][:14], col(r, 'GPDI'), res['GPDI'],
                 round(res['GPDI'], 2), r['final_band']))
