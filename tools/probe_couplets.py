# -*- coding: utf-8 -*-
"""
对「游山西村」「登幽州台歌」穷举可能的教材引文候选，
用冻结指标（ACD*/HDCR/OOVR/GPDI_char）反查当年到底用了哪一段。

frozen 目标：
  游山西村  N=14  ACD_star=0.2000  HDCR=0.0714  OOVR=0  GPDI_char=11.985
  登幽州台歌 N=8  ACD_star=0.0250  HDCR=0.0000  OOVR=0  GPDI_char=1.2500
            -> ACD=1.125, sum=9 -> 7个甲(1)+1个乙(2)；TL*=ln(9)/ln(318)=0.3813 自洽
"""
import sys
import os

sys.path.insert(0, r'D:/app/wampsever/GPDI-Analyzer/core')
import gpdi  # noqa

inv = gpdi.load_inventory()

# 游山西村 全诗（去标点，56字，每句7字）
YOU_FULL = ("莫笑农家腊酒浑" "丰年留客足鸡豚"
            "山重水复疑无路" "柳暗花明又一村"
            "箫鼓追随春社近" "衣冠简朴古风存"
            "从今若许闲乘月" "拄杖无时夜叩门")

# 登幽州台歌 全诗（去标点，22字）
DENG_FULL = "前不见古人" "后不见来者" "念天地之悠悠" "独怆然而涕下"

TARGET = {
    '游山西村':    dict(ACD_star=0.2000, HDCR=0.0714, OOVR=0.0, GPDI_char=11.985),
    '登幽州台歌':  dict(ACD_star=0.0250, HDCR=0.0000, OOVR=0.0, GPDI_char=1.2500),
}


def metrics_of(text):
    r = gpdi.analyze(text, inventory=inv)
    return {
        'N': r['N'],
        'ACD_star': round(r['ACD_star'], 4),
        'HDCR': round(r['HDCR'], 4),
        'OOVR': round(r['OOVR'], 4),
        'GPDI_char': round(r['GPDI_char'], 3),
    }


def check(name, text):
    m = metrics_of(text)
    t = TARGET[name]
    ok = (abs(m['ACD_star'] - t['ACD_star']) < 0.002
          and abs(m['HDCR'] - t['HDCR']) < 0.002
          and abs(m['OOVR'] - t['OOVR']) < 0.002
          and abs(m['GPDI_char'] - t['GPDI_char']) < 0.05)
    flag = '  <== MATCH' if ok else ''
    return ok, m, flag


def report(name, cands):
    print('=' * 100)
    print('%s   frozen: %s' % (name, TARGET[name]))
    hits = []
    for label, text in cands:
        ok, m, flag = check(name, text)
        if ok:
            hits.append((label, text))
        print('  %-18s N=%-3d ACD*=%.4f HDCR=%.4f OOVR=%.4f GPDI_char=%7.3f%s'
              % (label, m['N'], m['ACD_star'], m['HDCR'], m['OOVR'],
                 m['GPDI_char'], flag))
        print('       %s' % text)
    if hits:
        print('  >>> 命中: %s' % ', '.join(h[0] for h in hits))
    else:
        print('  >>> 无候选命中')
    return hits


# ---- 游山西村：4 组对句 ----
you_cands = [
    ('首联(1-2句)', YOU_FULL[0:14]),
    ('颔联(3-4句)', YOU_FULL[14:28]),
    ('颈联(5-6句)', YOU_FULL[28:42]),
    ('尾联(7-8句)', YOU_FULL[42:56]),
]
report('游山西村', you_cands)

# ---- 登幽州台歌：前两句/后两句/全文/连续8字窗口 ----
deng_cands = [
    ('前两句(10字)', DENG_FULL[0:10]),
    ('后两句(12字)', DENG_FULL[10:22]),
    ('全文(22字)', DENG_FULL),
]
# 穷举连续8字窗口，找 sum=9 的（7甲+1乙, 无丁戊, 无OOV）
for s in range(0, len(DENG_FULL) - 8 + 1):
    w = DENG_FULL[s:s + 8]
    m = metrics_of(w)
    if abs(m['HDCR']) < 1e-9 and abs(m['OOVR']) < 1e-9 and abs(m['ACD_star'] - 0.025) < 0.002:
        deng_cands.append(('8字窗[%d:%d]' % (s, s + 8), w))
report('登幽州台歌', deng_cands)
