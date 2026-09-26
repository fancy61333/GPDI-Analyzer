# -*- coding: utf-8 -*-
"""诊断：1) HDCR 到底是 戊/N 还是 (丁+戊)/N  2) 哪些正文取错了（N 不匹配）"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'core'))
import gpdi

from _skip import require
require('data/corpus_frozen.csv')

BASE = os.path.join(HERE, '..')
inv = gpdi.load_inventory()

frozen = {}
with open(os.path.join(BASE, 'data', 'corpus_frozen.csv'), encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        if row.get('in_poetry_corpus') == 'Y' and row.get('is_duplicate') == 'N':
            frozen[row['id']] = row

texts = []
with open(os.path.join(BASE, 'data', 'poems_82_text.csv'), encoding='utf-8-sig') as f:
    texts = list(csv.DictReader(f))

e_hit = 0      # HDCR == 戊 / N
de_hit = 0     # HDCR == (丁+戊) / N
tot = 0
nmis = []
acd_bad = []

for t in texts:
    fr = frozen[t['id']]
    res = gpdi.analyze(t['text'], inv)
    Nf, Nc = float(fr['N']), float(res['N'])
    if abs(Nc - Nf) > 0.5:
        nmis.append((t['clean_title'], int(Nf), int(Nc), t['source_table'],
                     fr.get('textbook_name', '')))
        continue
    tot += 1
    d = res['char_distribution']
    e_cnt = d.get('E', 0)
    d_cnt = d.get('D', 0)
    hd_frozen = float(fr['HDCR']) * Nf
    if abs(hd_frozen - e_cnt) < 0.6:
        e_hit += 1
    if abs(hd_frozen - (e_cnt + d_cnt)) < 0.6:
        de_hit += 1
    # ACD 偏差
    if abs(float(fr['ACD_star']) - float(res['ACD_star'])) > 0.002:
        acd_bad.append((t['clean_title'], int(Nf), float(fr['ACD_star']),
                        float(res['ACD_star']), d))

print('=== N 匹配的诗 ===', tot)
print(f'HDCR == 戊/N        : {e_hit} / {tot}')
print(f'HDCR == (丁+戊)/N   : {de_hit} / {tot}')
print()
print(f'=== N 不匹配的诗 ({len(nmis)}) ===')
for x in nmis:
    print(f'  {x[0]:<20} frozen N={x[1]:<4} 取回 N={x[2]:<4} src={x[3]:<6} 教材={x[4]}')
print()
print(f'=== N 匹配但 ACD* 不一致 ({len(acd_bad)}) ===')
for x in acd_bad[:12]:
    print(f'  {x[0]:<16} N={x[1]:<4} frozen ACD*={x[2]:.4f} computed={x[3]:.4f} 分布={x[4]}')
