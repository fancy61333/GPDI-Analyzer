# -*- coding: utf-8 -*-
"""扫描论文文件夹：本地是否已存在 82 首诗词正文"""
import os
import pandas as pd

BASE = r'D:\DigitalHumanities\6.论文选题\2.投稿中==选题：面向国际中文教育的古诗文分级计量研究'
TITLES = ['登鹳雀楼', '静夜思', '春晓', '望庐山瀑布', '绝句']

alltab = []
print('=== 所有 xlsx/csv 文件 ===')
for root, dirs, files in os.walk(BASE):
    dirs[:] = [d for d in dirs if d not in ('.venv', 'node_modules', '__pycache__', '.git')]
    for fn in files:
        ext = os.path.splitext(fn)[1].lower()
        if ext in ('.xlsx', '.xls', '.csv'):
            alltab.append(os.path.join(root, fn))
for p in alltab[:40]:
    print('  ', os.path.relpath(p, BASE))
print('  共', len(alltab), '个表格文件')

print()
print('=== 含“诗词正文”特征的列 ===')
hits = []
for p in alltab:
    ext = os.path.splitext(p)[1].lower()
    try:
        df = pd.read_excel(p) if ext in ('.xlsx', '.xls') else pd.read_csv(p, encoding='utf-8-sig')
    except Exception:
        continue
    for c in df.columns:
        cl = str(c).lower()
        if any(k in cl for k in ['text', 'content', '正文', 'poem', 'clean', 'raw', '内容']):
            s = df[c].dropna().astype(str)
            if len(s) == 0:
                continue
            first = s.iloc[0]
            if any(t in first for t in TITLES) or (len(first) > 20 and ('。' in first or '，' in first)):
                hits.append((p, c, len(df), first[:70]))
if hits:
    for p, c, n, f in hits[:50]:
        print(f'  [{n}行] {os.path.basename(p)} :: 列={c} :: {f}')
else:
    print('  未找到含诗词正文的表格列')

print()
print('=== txt/json/md 中含诗词标题的文件 ===')
thits = []
for root, dirs, files in os.walk(BASE):
    dirs[:] = [d for d in dirs if d not in ('.venv', 'node_modules', '__pycache__', '.git')]
    for fn in files:
        ext = os.path.splitext(fn)[1].lower()
        if ext not in ('.txt', '.json', '.md'):
            continue
        p = os.path.join(root, fn)
        try:
            with open(p, encoding='utf-8', errors='ignore') as fh:
                t = fh.read(300000)
        except Exception:
            continue
        if any(tt in t for tt in TITLES[:3]):
            thits.append((p, len(t)))
if thits:
    for p, n in thits[:30]:
        print(f'  [{n}字符] {os.path.relpath(p, BASE)}')
else:
    print('  未找到')
