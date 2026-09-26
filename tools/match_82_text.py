# -*- coding: utf-8 -*-
"""从本地 CSV 匹配 82 首诗词正文"""
import os
import re
import pandas as pd

BASE = r'D:\DigitalHumanities\6.论文选题\2.投稿中==选题：面向国际中文教育的古诗文分级计量研究'
OUT = r'D:\app\wampsever\GPDI-Analyzer\data\poems_82_text.csv'


def read_csv_auto(p):
    for enc in ('utf-8-sig', 'utf-8', 'gbk', 'gb18030'):
        try:
            return pd.read_csv(p, encoding=enc)
        except Exception:
            pass
    return None


def norm_title(t):
    t = str(t)
    t = re.sub(r'[（(].*?[)）]', '', t)   # 去括号内容
    t = re.sub(r'\s+', '', t)
    return t.strip()


def pick_text_col(df):
    for pref in ['content_clean', 'content_simplified', 'content', '正文', 'text']:
        for c in df.columns:
            if str(c).lower() == pref.lower():
                s = df[c].dropna().astype(str)
                if len(s) and s.str.len().mean() > 10:
                    return c
    best, bestlen = None, 0
    for c in df.columns:
        s = df[c].dropna().astype(str)
        if len(s) == 0:
            continue
        m = s.str.len().mean()
        if m > bestlen:
            best, bestlen = c, m
    return best if bestlen > 15 else None


def pick_title_col(df):
    for pref in ['title', 'clean_title', '诗题', '题目']:
        for c in df.columns:
            if str(c).lower() == pref.lower():
                return c
    return None


frozen = pd.read_csv(r'D:\app\wampsever\GPDI-Analyzer\data\corpus_frozen.csv', encoding='utf-8-sig')
po = frozen[(frozen['in_poetry_corpus'] == 'Y') & (frozen['is_duplicate'] == 'N')].copy()
print('待匹配 82 首数量:', len(po))

index = {}
sources = ['k12_poem_texts.csv', '5.20_324new-tcsol-poem.csv', 'quantangshi.csv', 'quansongci_texts.csv']
for fn in sources:
    p = os.path.join(BASE, fn)
    if not os.path.exists(p):
        print('  缺文件:', fn)
        continue
    df = read_csv_auto(p)
    if df is None:
        print('  读取失败:', fn)
        continue
    tc, tt = pick_text_col(df), pick_title_col(df)
    if tc is None or tt is None:
        print(f'  {fn}: 未找到正文/标题列 (cols={df.columns.tolist()[:8]})')
        continue
    print(f'  {fn}: {len(df)}行, 标题列={tt}, 正文列={tc}')
    for _, r in df.iterrows():
        t, x = norm_title(r[tt]), str(r[tc])
        if t and x and x != 'nan':
            if t not in index or len(x) > len(index[t][0]):
                index[t] = (x, fn)

print('索引标题数:', len(index))

rows, miss = [], []
for _, r in po.iterrows():
    ct = r['clean_title']
    hit = index.get(norm_title(ct))
    if hit is None:
        hit = index.get(norm_title(r['title']))
    if hit:
        rows.append({'id': r['id'], 'clean_title': ct, 'title': r['title'],
                     'author': r['author'], 'source_file': hit[1], 'text': hit[0],
                     'N_frozen': r['N']})
    else:
        miss.append(ct)

out = pd.DataFrame(rows)
out.to_csv(OUT, index=False, encoding='utf-8-sig')
print(f'\n匹配成功: {len(out)} / {len(po)}')
print(f'未匹配: {len(miss)}')
for m in miss[:25]:
    print('   未匹配:', m)
print('\n已保存:', OUT)
