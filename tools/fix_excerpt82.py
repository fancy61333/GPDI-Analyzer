# -*- coding: utf-8 -*-
"""
修正教材节选诗的正文（显式引文覆盖，不做机械截断）。

背景：frozen 语料里若干首的 N 远小于全文，原因是教材只引用了片段，
数据库里只有全文，此前取全文导致 N 与指标全部对不上。

经 tools/probe_couplets.py 用冻结指标反查，确定教材实际引文如下：

  id=6  游山西村  (陆游)  56字全文 -> 教材引「颔联」14字
        山重水复疑无路，柳暗花明又一村      <- 千古名句，教材节选最爱
        (注意：不是首联「莫笑农家腊酒浑…」，首联算得 GPDI_char=25.24，与 frozen 11.985 不符)

  id=8  题西林壁  (苏轼)  28字全文 -> 教材引「前两句」14字
        横看成岭侧成峰，远近高低各不同

  id=12 登幽州台歌(陈子昂) 22字全文 -> 【用户 2026-09-24 裁定】采用 8 字截断
        前不见古人后不见
        裁定理由：frozen N=8 且 ACD*=0.0250 / HDCR=0 / OOVR=0 / GPDI_char=1.2500 /
                  TL*=0.3813(=ln9/ln318) 四项数值严丝合缝、完全自洽，
                  说明当年跑的就是这 8 个字（Σ字级=9 即 7甲+1乙）。
                  虽「前不见古人后不见」是生硬截断（"后不见"未完），
                  但可复现性优先——软件必须与论文冻结数据逐篇一致。
        （对照组：「前两句」10字 前不见古人后不见来者 → ACD*=0.0200, GPDI_char=1.000，不符）
"""
import csv

CSV_PATH = r'D:/app/wampsever/GPDI-Analyzer/data/poems_82_text.csv'

# id -> 教材实际引文（去标点）
EXCERPT = {
    '6': '山重水复疑无路柳暗花明又一村',   # 游山西村 颔联
    '8': '横看成岭侧成峰远近高低各不同',   # 题西林壁 前两句
    '12': '前不见古人后不见',              # 登幽州台歌 8字截断（用户裁定，复现 frozen）
}


def main():
    with open(CSV_PATH, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0].keys())

    changed = []
    for row in rows:
        pid = row['id']
        if pid not in EXCERPT:
            continue
        old = row['text']
        new = EXCERPT[pid]
        row['text'] = new
        row['n_exact'] = 'Y' if str(len(new)) == row['N_frozen'] else 'N'
        changed.append((pid, row['clean_title'], len(old), len(new),
                        row['N_frozen'], row['n_exact'], new))

    with open(CSV_PATH, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print('=== 已按教材实际引文修正 %d 首 ===' % len(changed))
    for pid, title, oldn, newn, frozen_n, exact, new in changed:
        print('id=%s %s: 全文%d字 -> 引文%d字 (frozen N=%s, n_exact=%s)'
              % (pid, title, oldn, newn, frozen_n, exact))
        print('     正文:', new)


if __name__ == '__main__':
    main()
