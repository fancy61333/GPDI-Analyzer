# -*- coding: utf-8 -*-
"""Impact check: with 'apply the glyph map only to characters that MISS the
inventory', do any of the 82 reference poems change?"""
import csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'core'))
import gpdi

inv = gpdi.load_inventory()
vmap = {}
with open(os.path.join(HERE, '..', 'data', 'variant_map.tsv'), encoding='utf-8') as f:
    for line in f:
        line = line.rstrip('\n')
        if not line or line.startswith('#'):
            continue
        a, b = line.split('\t')
        vmap[a] = b

rows = []
with open(os.path.join(HERE, '..', 'data', 'poems_82_text.csv'), encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

affected = []
for r in rows:
    clean = gpdi.normalize(r['text'])
    oov_src = sorted({c for c in clean if c not in inv})
    mapped = {c: vmap[c] for c in oov_src if c in vmap}
    if not mapped:
        continue
    # would any of them now land inside the inventory?
    entering = {c: vmap[c] for c in mapped if vmap[c] in inv}
    affected.append((r['clean_title'], r['id'], oov_src, entering))

print('poems with mappable OOV characters: %d / %d' % (len(affected), len(rows)))
for title, pid, oov, ent in affected:
    print('\n%s (id=%s)' % (title, pid))
    print('   OOV chars  :', ''.join(oov))
    print('   mapped     :', {c: vmap[c] for c in oov if c in vmap})
    print('   -> in inv  :', ent)
