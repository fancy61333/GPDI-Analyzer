# -*- coding: utf-8 -*-
"""Regression test: recompute all 82 poems and compare with the frozen corpus."""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'core'))
import gpdi

from _skip import require
require('data/poems_82_text.csv', 'data/corpus_frozen.csv')

BASE = os.path.join(HERE, '..')
TEXT_CSV = os.path.join(BASE, 'data', 'poems_82_text.csv')
FROZEN_CSV = os.path.join(BASE, 'data', 'corpus_frozen.csv')
REPORT = os.path.join(BASE, 'docs', 'regression_82.txt')

TOL = {'N': 0.5, 'ACD_star': 0.002, 'HDCR': 0.002, 'OOVR': 0.002,
       'TL_star': 0.002, 'GPDI': 0.05, 'GPDI_char': 0.05, 'GPRS': 0.05}
METRICS = ['N', 'ACD_star', 'HDCR', 'OOVR', 'TL_star', 'GPDI_char', 'GPDI', 'GPRS']

inv = gpdi.load_inventory()

frozen = {}
with open(FROZEN_CSV, encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        if row.get('in_poetry_corpus') == 'Y' and row.get('is_duplicate') == 'N':
            frozen[row['id']] = row

texts = []
with open(TEXT_CSV, encoding='utf-8-sig') as f:
    texts = list(csv.DictReader(f))

lines = []


def P(s=''):
    print(s)
    lines.append(str(s))


P('=' * 70)
P('GPDI Analyzer spec %s - 82-poem regression test' % gpdi.SPEC_VERSION)
P('=' * 70)
P(f'texts matched : {len(texts)}')
P(f'frozen rows   : {len(frozen)}')

maxerr = {m: 0.0 for m in METRICS}
fails = []
nmis = 0
done = 0

for t in texts:
    fr = frozen.get(t['id'])
    if fr is None:
        P(f"  [no frozen row] id={t['id']} {t['clean_title']}")
        continue
    res = gpdi.analyze(t['text'], inv)
    if 'error' in res:
        P(f"  [analyze error] {t['clean_title']}: {res['error']}")
        continue
    done += 1
    rec = {'id': t['id'], 'title': t['clean_title'], 'src': t['source_table'], 'vals': {}}
    bad = False
    for m in METRICS:
        fv = float(fr[m])
        cv = float(res[m])
        d = abs(cv - fv)
        rec['vals'][m] = (fv, cv, d)
        maxerr[m] = max(maxerr[m], d)
        if d > TOL[m]:
            bad = True
    if abs(res['N'] - float(fr['N'])) > 0.5:
        nmis += 1
    if bad:
        fails.append(rec)

P('')
P('--- max absolute error per metric ---')
for m in METRICS:
    P(f'  {m:<10}: {maxerr[m]:.6f}   (tol {TOL[m]})')
P('')
npass = done - len(fails)
P(f'PASS {npass} / {done}   FAIL {len(fails)}')
P(f'N mismatch (retrieved text differs in length from frozen N): {nmis}')
P('')

if fails:
    P('--- failing poems (first 15) ---')
    for rec in fails[:15]:
        P(f"  {rec['title']}  [id={rec['id']}, src={rec['src']}]")
        for m in METRICS:
            fv, cv, d = rec['vals'][m]
            flag = '  <== ' if d > TOL[m] else ''
            P(f"      {m:<10} frozen={fv:<10.4f} computed={cv:<10.4f} diff={d:.4f}{flag}")
else:
    P('ALL POEMS REPRODUCE THE FROZEN METRICS WITHIN TOLERANCE.')

with open(REPORT, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines) + '\n')
P('')
P('report -> ' + REPORT)
