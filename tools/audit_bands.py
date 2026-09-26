# -*- coding: utf-8 -*-
"""Audit: how does the frozen corpus distribute across bands / sample layers,
and what cut-points follow from the frozen final_band assignment?"""
import csv, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN = os.path.join(HERE, '..', 'data', 'corpus_frozen.csv')
TEXTS = os.path.join(HERE, '..', 'data', 'poems_82_text.csv')

rows = []
with open(FROZEN, encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if r.get('in_poetry_corpus') == 'Y' and r.get('is_duplicate') == 'N':
            rows.append(r)

print('poems:', len(rows))

# --- sample layer / textbook distribution
print('\n--- sample_layer ---')
for k, v in collections.Counter((r.get('sample_layer') or '').strip() for r in rows).most_common():
    print('  %-30s %d' % (k, v))
print('\n--- textbook_name ---')
for k, v in collections.Counter((r.get('textbook_name') or '').strip() for r in rows).most_common():
    print('  %-40s %d' % (k, v))

# --- source table of the matched texts
with open(TEXTS, encoding='utf-8-sig') as f:
    src = collections.Counter(r['source_table'] for r in csv.DictReader(f))
print('\n--- source_table (matched texts) ---')
for k, v in src.most_common():
    print('  %-10s %d' % (k, v))

# --- band distribution from frozen final_band
print('\n--- final_band distribution ---')
bc = collections.Counter(r.get('final_band') for r in rows)
for k in sorted(bc, key=lambda x: (x is None, x)):
    print('  band %s : %d' % (k, bc[k]))

# --- GPDI range / cut points per frozen band
by_band = collections.defaultdict(list)
for r in rows:
    b = (r.get('final_band') or '').strip()
    by_band[b].append(float(r['GPDI']))
print('\n--- GPDI range per frozen band ---')
cuts = []
prev_max = None
for b in sorted(by_band, key=lambda x: int(x)):
    v = sorted(by_band[b])
    print('  band %s : n=%2d  min=%.2f  max=%.2f' % (b, len(v), v[0], v[-1]))
    if prev_max is not None:
        mid = (prev_max + v[0]) / 2
        cuts.append((b, round(v[0], 4), round(mid, 4), prev_max))
    prev_max = v[-1]

print('\n--- candidate cut schemes ---')
mins = [round(sorted(by_band[b])[0], 2) for b in sorted(by_band, key=lambda x: int(x))]
print('  lower bound of each band (band2..band5):', mins[1:])
mids = []
order = sorted(by_band, key=lambda x: int(x))
for i in range(1, len(order)):
    a = sorted(by_band[order[i - 1]])[-1]
    b = sorted(by_band[order[i]])[0]
    mids.append(round((a + b) / 2, 2))
print('  midpoint between adjacent bands       :', mids)

# check monotonicity: is final_band consistent with GPDI ordering?
srt = sorted(rows, key=lambda r: float(r['GPDI']))
bad = [(r['clean_title'], r['GPDI'], r['final_band']) for r in srt if False]
prev = -1
viol = []
for r in srt:
    b = int(r['final_band'])
    if b < prev:
        viol.append((r['clean_title'], r['GPDI'], b))
    prev = max(prev, b)
print('\nmonotonic violations (GPDI order vs band):', len(viol))
for v in viol[:10]:
    print('   ', v)
