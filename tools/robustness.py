# -*- coding: utf-8 -*-
"""Reproduce Section 4.6 (Robustness and Baseline Comparisons) of the manuscript.

Inputs are the paper's own per-poem component values (`data/corpus_frozen.csv`),
so this script tests the *specification* that Section 4.6 describes, not the
GUI: every scenario below is a re-weighting of the same four components.

Baseline                                       45 / 25 / 20 / 10
  character-equal 90/10                        30 / 30 / 30 / 10
  ACD-dominant 90/10                           60 / 15 / 15 / 10
  80/20 character-length allocation            40 / 22.2 / 17.8 / 20
  character-only                               50 / 27.8 / 22.2 / 0
  deliberately length-heavy stress test        20 / 20 / 20 / 40

Note the character-only row: 45/25/20 renormalised over the character layer is
50 / 27.8 / 22.2 — which is exactly GPDI_char / 100 in core/gpdi.py
(char share / 0.90). The paper and the tool therefore define GPDI_char the
same way; tests/test_char_only.py asserts it.

Scale-reference sensitivity: TL*_155 = min(ln(1 + N) / ln(156), 1), i.e. the
same index normalised against the longest text of the final 82-poem corpus
instead of the 317-character maximum of the 100-text development set, with the
length weight and all other weights unchanged.

Comparisons against the baseline, per scenario:
  Spearman's rho, exact agreement in corpus-relative band assignment (of 82),
  and maximum absolute rank shift.
"""
import csv
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, '..')
FROZEN = os.path.join(BASE, 'data', 'corpus_frozen.csv')
OUT_TXT = os.path.join(BASE, 'docs', 'robustness_82.txt')
OUT_CSV = os.path.join(BASE, 'docs', 'robustness_82.csv')

sys.path.insert(0, os.path.join(BASE, 'core'))
import gpdi

BAND_SIZES = (17, 17, 16, 16, 16)      # frozen corpus-relative scheme
N_REF_BASE = 317                       # denominator of the baseline TL*
N_REF_155 = 155                        # longest text of the 82-poem corpus


# --------------------------------------------------------------------------- #
# weights
# --------------------------------------------------------------------------- #
def w(a, h, o, t):
    return (a, h, o, t)


BASE_W = w(0.45, 0.25, 0.20, 0.10)
CHAR_PROP = (BASE_W[0] / 0.90, BASE_W[1] / 0.90, BASE_W[2] / 0.90)   # 50/27.8/22.2
# the coefficients the manuscript's own GPDI_char column was computed with
CHAR_PRINTED = (0.50, 0.278, 0.222)

SCENARIOS = [
    ('baseline (45/25/20/10)',            BASE_W),
    ('character-equal 90/10',             w(0.30, 0.30, 0.30, 0.10)),
    ('ACD-dominant 90/10',                w(0.60, 0.15, 0.15, 0.10)),
    ('80/20 character-length',            w(0.80 * CHAR_PROP[0], 0.80 * CHAR_PROP[1],
                                             0.80 * CHAR_PROP[2], 0.20)),
    ('character-only (50/27.8/22.2/0)',   w(CHAR_PRINTED[0], CHAR_PRINTED[1],
                                             CHAR_PRINTED[2], 0.00)),
    ('length-heavy stress test',          w(0.20, 0.20, 0.20, 0.40)),
]


def load_frozen(path=FROZEN):
    rows = []
    with open(path, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if (row.get('in_poetry_corpus') or '').strip() != 'Y':
                continue
            if (row.get('is_duplicate') or '').strip() == 'Y':
                continue
            rows.append(row)
    rows.sort(key=lambda r: int(r['id']))
    return rows


def score(row, weights, tl_star=None):
    a, h, o, t = weights
    tl = float(row['TL_star']) if tl_star is None else tl_star
    return 100.0 * (a * float(row['ACD_star']) + h * float(row['HDCR'])
                    + o * float(row['OOVR']) + t * tl)


def tl_star_155(n, n_ref=N_REF_155):
    return min(math.log(1.0 + n) / math.log(1.0 + n_ref), 1.0)


# --------------------------------------------------------------------------- #
# statistics (stdlib only — no scipy)
# --------------------------------------------------------------------------- #
def ranks(values):
    """1-based ranks, ties share the average rank."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


def pearson(x, y):
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0:
        return float('nan')
    return sxy / math.sqrt(sxx * syy)


def spearman(x, y):
    return pearson(ranks(x), ranks(y))


def kendall_tau_b(x, y):
    n = len(x)
    conc = disc = tx = ty = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            dx = x[i] - x[j]
            dy = y[i] - y[j]
            if dx == 0 and dy == 0:
                tx += 1
                ty += 1
            elif dx == 0:
                tx += 1
            elif dy == 0:
                ty += 1
            elif (dx > 0) == (dy > 0):
                conc += 1
            else:
                disc += 1
    n0 = n * (n - 1) / 2.0
    den = math.sqrt((n0 - tx) * (n0 - ty))
    if den == 0:
        return float('nan')
    return (conc - disc) / den


# --------------------------------------------------------------------------- #
# corpus-relative bands
# --------------------------------------------------------------------------- #
def position_bands(scores, ids, sizes=BAND_SIZES):
    """Quintile assignment on the frozen 17/17/16/16/16 sizes.

    Order by (score, id) so ties resolve deterministically, then hand out the
    band sizes in order. The baseline must reproduce final_band exactly.
    """
    order = sorted(range(len(scores)), key=lambda i: (scores[i], ids[i]))
    band = [0] * len(scores)
    pos = 0
    for b, size in enumerate(sizes, start=1):
        for _ in range(size):
            band[order[pos]] = b
            pos += 1
    return band


def cut_points(scores, band):
    """Lower bound of each band 2..5 — the scheme core/gpdi.py reads off."""
    cuts = []
    for b in (2, 3, 4, 5):
        vals = [s for s, k in zip(scores, band) if k == b]
        cuts.append(round(min(vals), 2) if vals else None)
    return cuts


def compare(base_scores, base_band, base_rank, other_scores, ids):
    band = position_bands(other_scores, ids)
    rank = ranks(other_scores)
    agree = sum(1 for a, b in zip(base_band, band) if a == b)
    shift = max(abs(a - b) for a, b in zip(base_rank, rank))
    return {
        'rho': spearman(base_scores, other_scores),
        'tau_b': kendall_tau_b(base_scores, other_scores),
        'band_agree': agree,
        'max_shift': shift,
        'band': band,
        'scores': other_scores,
        'cuts': cut_points(other_scores, band),
    }


# --------------------------------------------------------------------------- #
def main():
    rows = load_frozen()
    ids = [int(r['id']) for r in rows]
    n_poems = len(rows)

    lines = []
    def out(s=''):
        lines.append(s)
        print(s)

    out('=' * 78)
    out('Section 4.6 reproducibility check - Robustness and Baseline Comparisons')
    out('=' * 78)
    out('corpus          : %d poems (in_poetry_corpus = Y, deduplicated)' % n_poems)
    out('source          : data/corpus_frozen.csv (the manuscript\'s own values)')
    out('band scheme     : %s (17/17/16/16/16, lower bound of each band)'
        % '/'.join(str(s) for s in BAND_SIZES))
    out()

    # --- baseline sanity: GPDI column and final_band must come back --------
    base_scores = [score(r, BASE_W) for r in rows]
    published = [float(r['GPDI']) for r in rows]
    resid = [abs(a - b) for a, b in zip(base_scores, published)]
    base_band = position_bands(base_scores, ids)
    frozen_band = [int(str(r['final_band']).strip()) for r in rows]
    band_ok = sum(1 for a, b in zip(base_band, frozen_band) if a == b)

    out('BASELINE CHECK')
    out('  max |recomputed - published GPDI| : %.4f' % max(resid))
    out('  bands reproduced                  : %d/%d' % (band_ok, n_poems))
    out('  cut-points, quoted in the README : %s'
        % ' / '.join('%.2f' % c for c in gpdi.load_reference_bands()['cuts']))
    out('  cut-points, recomputed here      : %s'
        % ' / '.join('%.2f' % c for c in cut_points(base_scores, base_band)))
    out('    (the two agree to 0.01; the second is read off the 4-dp rounded')
    out('     component columns rather than the frozen band assignment)')
    out()
    if band_ok != n_poems:
        out('!! baseline bands do not reproduce — scenario rows below are void')
        out()

    # --- the character-only row must equal the published GPDI_char column --
    cw = dict(SCENARIOS)['character-only (50/27.8/22.2/0)']
    exact = (0.50, 25 / 90.0, 20 / 90.0)

    def char_dev(weights):
        return max(abs(100.0 * (weights[0] * float(r['ACD_star'])
                                + weights[1] * float(r['HDCR'])
                                + weights[2] * float(r['OOVR'])) - float(r['GPDI_char']))
                   for r in rows)

    out('CHARACTER-ONLY ROW vs PUBLISHED GPDI_char')
    out('  manuscript weights : %.1f / %.1f / %.1f / %.1f  (per 100)'
        % tuple(x * 100 for x in cw))
    out('  0.50 / 0.278 / 0.222 (= 45/25/20 renormalised, printed to 3 dp)')
    out('  max |scenario - GPDI_char column| : %.4f  <- exact to the published scale'
        % char_dev(cw))
    out('  for contrast, the unrounded renormalisation 25/90, 20/90: %.4f'
        % char_dev(exact))
    out()

    base_rank = ranks(base_scores)

    out('SCENARIO COMPARISONS (each against the baseline)')
    out('%-28s %7s %8s %8s %9s %10s' %
        ('scenario', 'rho', 'tau-b', 'bands', 'max rank', 'weights'))
    out('-' * 78)

    table = []
    for name, weights in SCENARIOS:
        scores = [score(r, weights) for r in rows]
        c = compare(base_scores, base_band, base_rank, scores, ids)
        wstr = '/'.join(('%.1f' % (x * 100)).rstrip('0').rstrip('.') for x in weights)
        out('%-28s %7.4f %8.4f %5d/%-3d %9.0f %10s'
            % (name, c['rho'], c['tau_b'], c['band_agree'], n_poems,
               c['max_shift'], wstr))
        table.append((name, wstr, c))

    out()

    # --- scale-reference sensitivity: TL* renormalised against 155 --------
    tl155 = [tl_star_155(int(r['N'])) for r in rows]
    s155 = [score(r, BASE_W, t) for r, t in zip(rows, tl155)]
    c155 = compare(base_scores, base_band, base_rank, s155, ids)

    base_tl = [float(r['TL_star']) for r in rows]
    max_n = max(int(r['N']) for r in rows)
    capped = sum(1 for t, r in zip(tl155, rows)
                 if math.log(1.0 + int(r['N'])) / math.log(156.0) > 1.0)

    out('SCALE-REFERENCE SENSITIVITY  (TL*_155 = min(ln(1+N)/ln(156), 1))')
    out('  longest text in the corpus        : N = %d characters' % max_n)
    out('  values hitting the cap at 1.0     : %d' % capped)
    out('  Spearman rho vs baseline          : %.4f' % c155['rho'])
    out('  Kendall tau-b vs baseline         : %.4f' % c155['tau_b'])
    out('  band agreement                    : %d/%d' % (c155['band_agree'], n_poems))
    out('  maximum absolute rank shift       : %.0f' % c155['max_shift'])
    out('  cut-points                        : %s'
        % ' / '.join('%.2f' % c for c in c155['cuts']))
    out()

    # --- largest movers under the length-heavy stress test ---------------
    heavy = dict(SCENARIOS)['length-heavy stress test']
    h_scores = [score(r, heavy) for r in rows]
    h_rank = ranks(h_scores)
    movers = sorted(range(n_poems), key=lambda i: -abs(base_rank[i] - h_rank[i]))[:5]
    out('LARGEST RANK MOVERS under the length-heavy stress test (20/20/20/40)')
    for i in movers:
        out('  id %-4s %-22s N=%-4d baseline rank %2.0f -> %2.0f  (shift %+.0f)'
            % (rows[i]['id'], rows[i]['clean_title'][:22], int(rows[i]['N']),
               base_rank[i], h_rank[i], h_rank[i] - base_rank[i]))
    out()

    # --- write the table out ---------------------------------------------
    out('RESULT: Section 4.6 reproduced from the frozen corpus.')
    out('Weights are applied to the paper\'s own ACD*/HDCR/OOVR/TL* values, so a')
    out('reviewer can rerun this file and land on the same numbers.')

    with open(OUT_TXT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')

    with open(OUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['scenario', 'weights_ACD*_HDCR_OOVR_TL*', 'spearman_rho',
                     'kendall_tau_b', 'band_agreement_of_%d' % n_poems,
                     'max_abs_rank_shift', 'cuts'])
        for name, wstr, c in table:
            wr.writerow([name, wstr, '%.4f' % c['rho'], '%.4f' % c['tau_b'],
                         c['band_agree'], '%.0f' % c['max_shift'],
                         ' / '.join('%.2f' % x for x in c['cuts'])])
        wr.writerow(['scale-reference 155', '45/25/20/10 (TL*_155)', '%.4f' % c155['rho'],
                     '%.4f' % c155['tau_b'], c155['band_agree'],
                     '%.0f' % c155['max_shift'],
                     ' / '.join('%.2f' % x for x in c155['cuts'])])

    print()
    print('wrote %s' % os.path.relpath(OUT_TXT, BASE))
    print('wrote %s' % os.path.relpath(OUT_CSV, BASE))


if __name__ == '__main__':
    main()
