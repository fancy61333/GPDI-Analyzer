# -*- coding: utf-8 -*-
"""Coefficient test: which weights reproduce the manuscript's own columns.

Two claims are asserted, both against the frozen corpus:

  1. GPDI      = 100 * (0.45*ACD* + 0.25*HDCR + 0.20*OOVR + 0.10*TL*)
  2. GPDI_char = 100 * (0.50*ACD* + 0.278*HDCR + 0.222*OOVR)

Claim 2 is the one worth guarding. The character-only scenario in Section 4.6 is
printed as 50/27.8/22.2/0, i.e. 45/25/20 renormalised over the character layer.
Using those coefficients as printed reproduces the corpus's GPDI_char column to
0.001; using the unrounded renormalisation (divided by 0.90) leaves a 0.014
residual, which is larger than the published rounding. So the printed
coefficients are used, and the test fails if anyone reverts them.

Residuals are computed from the *text* (full-precision components), which is what
the shipped software does. That is why the tolerance is one hundredth of a point
rather than the 0.0005 the component-column probe in tools/robustness.py shows.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(BASE, 'core'))
import gpdi

from _skip import require
require('data/poems_82_text.csv', 'data/corpus_frozen.csv')

TOL = 0.011        # one hundredth of a GPDI point (the published precision)

frozen = {}
with open(os.path.join(BASE, 'data', 'corpus_frozen.csv'), encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        if row.get('in_poetry_corpus') == 'Y' and row.get('is_duplicate') == 'N':
            frozen[row['id']] = row

with open(os.path.join(BASE, 'data', 'poems_82_text.csv'), encoding='utf-8-sig') as f:
    texts = list(csv.DictReader(f))

inv = gpdi.load_inventory()

worst = {'GPDI': 0.0, 'GPDI_char': 0.0, 'GPDI_char_renorm': 0.0}
for t in texts:
    fr = frozen.get(t['id'])
    if fr is None:
        continue
    res = gpdi.analyze(t['text'], inv)
    a, h, o = res['ACD_star'], res['HDCR'], res['OOVR']
    tl = res['TL_star']
    # recompute from full precision, not from the rounded dict
    char_share = gpdi.W_ACD * (res['ACD'] - 1) / 5 + gpdi.W_HDCR * h + gpdi.W_OOVR * o
    worst['GPDI'] = max(worst['GPDI'],
                        abs(100.0 * (char_share + gpdi.W_LEN * tl) - float(fr['GPDI'])))
    worst['GPDI_char'] = max(worst['GPDI_char'],
                             abs(res['GPDI_char'] - float(fr['GPDI_char'])))
    renorm = 100.0 * (char_share / gpdi.W_CHAR)
    worst['GPDI_char_renorm'] = max(worst['GPDI_char_renorm'],
                                    abs(renorm - float(fr['GPDI_char'])))

print('GPDI Analyzer spec %s - coefficient test' % gpdi.SPEC_VERSION)
print('=' * 62)
print('poems                                  : %d' % len(texts))
print('GPDI      vs published column          : %.4f  (tol %.3f)'
      % (worst['GPDI'], TOL))
print('GPDI_char vs published column (0.278/0.222) : %.4f  (tol %.3f)'
      % (worst['GPDI_char'], TOL))
print('GPDI_char via share/0.90 (must exceed tol)  : %.4f'
      % worst['GPDI_char_renorm'])
print()

ok = (worst['GPDI'] <= TOL
      and worst['GPDI_char'] <= TOL
      and worst['GPDI_char_renorm'] > TOL)

print('weights in use : GPDI %.2f/%.2f/%.2f/%.2f | GPDI_char %.3f/%.3f/%.3f'
      % (gpdi.W_ACD, gpdi.W_HDCR, gpdi.W_OOVR, gpdi.W_LEN,
         gpdi.W_CHAR_ACD, gpdi.W_CHAR_HDCR, gpdi.W_CHAR_OOVR))
print('RESULT: %s' % ('COEFFICIENTS MATCH THE PUBLISHED COLUMNS' if ok
                      else 'MISMATCH - see the residuals above'))
sys.exit(0 if ok else 1)
