# -*- coding: utf-8 -*-
"""Replace the two mis-matched poems (id 16 浪淘沙 / id 20 水调歌头) with the
textbook texts found in the tcsol-poem table (国际中文教材诗词表).

id 16  浪淘沙   李煜   《浪淘沙令·帘外雨潺潺》 54 字
id 20  水调歌头 苏轼*  辛弃疾《水调歌头·我饮不须劝》含小序 155 字
       (* DB 作者栏沿用教材标注「苏轼」，与冻结语料一致；实际作者为辛弃疾)
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, '..', 'data', 'poems_82_text.csv')

FIX = {
    '16': ('浪淘沙', '李煜', 'tcsol',
           '帘外雨潺潺春意阑珊罗衾不耐五更寒梦里不知身是客一晌贪欢独自莫凭栏无限江山别时容易见时难流水落花春去也天上人间',
           '54'),
    '20': ('水调歌头', '苏轼', 'tcsol',
           '淳熙丁酉自江陵移帅隆兴到官之三月被召司马监赵卿王漕饯别司马赋水调歌头席间次韵时王公明枢密薨坐客终夕为兴门户之叹故前章及之我饮不须劝正怕酒樽空别离亦复何恨此别恨匆匆头上貂蝉贵客苑外麒麟高冢人世竟谁雄一笑出门去千里落花风孙刘辈能使我不为公余发种种如是此事付渠侬但觉平生湖海除了醉吟风月此外百无功毫发皆帝力更乞鉴湖东',
           '155'),
}

rows = []
with open(CSV_PATH, encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for r in reader:
        rows.append(r)

changed = []
for r in rows:
    fx = FIX.get(r['id'])
    if not fx:
        continue
    title, author, src, text, n = fx
    r['clean_title'] = title
    r['author'] = author
    r['source_table'] = src
    r['text'] = text
    r['N_frozen'] = n
    r['n_exact'] = 'Y'
    changed.append('%s(id=%s)' % (title, r['id']))

with open(CSV_PATH, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

print('updated:', ', '.join(changed))
