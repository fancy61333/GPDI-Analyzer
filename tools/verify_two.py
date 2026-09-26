# -*- coding: utf-8 -*-
"""Verify the two tcsol textbook texts against the frozen metrics."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'core'))
import gpdi

inv = gpdi.load_inventory()
PUNC = '，。、？！；：「」『』《》（）,.?!;:'

def manual(text):
    chars = [c for c in text if not c.isspace() and c not in PUNC]
    N = len(chars)
    vals = [inv.get(c, gpdi.OOV_VALUE) for c in chars]
    S = sum(vals)
    acd = S / N
    acds = (acd - 1) / 5
    hdcr = sum(1 for v in vals if v in (4, 5)) / N
    oovr = sum(1 for v in vals if v == 6) / N
    tl = math.log(N + 1) / math.log(gpdi.N_REF_MAX + 1)
    gchar = 100 * (gpdi.W_ACD * acds + gpdi.W_HDCR * hdcr + gpdi.W_OOVR * oovr)
    g = 100 * (0.9 * (gpdi.W_ACD * acds + gpdi.W_HDCR * hdcr + gpdi.W_OOVR * oovr) + 0.1 * tl)
    return dict(N=N, sum=S, ACD_star=acds, HDCR=hdcr, OOVR=oovr, TL=tl, GPDI=g, CHAR=gchar)

T = {
 16: ('浪淘沙', '帘外雨潺潺春意阑珊罗衾不耐五更寒梦里不知身是客一晌贪欢独自莫凭栏无限江山别时容易见时难流水落花春去也天上人间'),
 20: ('水调歌头', '淳熙丁酉自江陵移帅隆兴到官之三月被召司马监赵卿王漕饯别司马赋水调歌头席间次韵时王公明枢密薨坐客终夕为兴门户之叹故前章及之我饮不须劝正怕酒樽空别离亦复何恨此别恨匆匆头上貂蝉贵客苑外麒麟高冢人世竟谁雄一笑出门去千里落花风孙刘辈能使我不为公余发种种如是此事付渠侬但觉平生湖海除了醉吟风月此外百无功毫发皆帝力更乞鉴湖东'),
}
F = {
 16: dict(N=54, sum=138, ACD_star=0.3111, HDCR=0.1481, OOVR=0.0926, TL=0.6955, GPDI=26.51, CHAR=21.728),
 20: dict(N=155, sum=405, ACD_star=0.3226, HDCR=0.2, OOVR=0.0581, TL=0.8764, GPDI=29.44, CHAR=22.98),
}
for k, (name, text) in T.items():
    m = manual(text)
    f = F[k]
    print('%s (id=%d)' % (name, k))
    print('  calc  N=%d sum=%d ACD*=%.4f HDCR=%.4f OOVR=%.4f TL*=%.4f GPDI=%.2f CHAR=%.3f' % (
        m['N'], m['sum'], m['ACD_star'], m['HDCR'], m['OOVR'], m['TL'], m['GPDI'], m['CHAR']))
    print('  froz  N=%d sum=%d ACD*=%.4f HDCR=%.4f OOVR=%.4f TL*=%.4f GPDI=%.2f CHAR=%.3f' % (
        f['N'], f['sum'], f['ACD_star'], f['HDCR'], f['OOVR'], f['TL'], f['GPDI'], f['CHAR']))
    ok = (m['N'] == f['N'] and abs(m['GPDI'] - f['GPDI']) < 0.01)
    print('  => %s' % ('MATCH' if ok else 'MISMATCH'))
