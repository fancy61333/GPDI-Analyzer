# -*- coding: utf-8 -*-
"""
GUI smoke test (headless, QT_QPA_PLATFORM=offscreen).

Verifies that the desktop GUI wires the scoring core correctly:
  - Load .txt batch   -> table populated
  - Export CSV        -> file written with expected columns
"""
import os
import sys
import csv
import tempfile

os.environ['QT_QPA_PLATFORM'] = 'offscreen'      # must be set before Qt import

GUI_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'gui')
sys.path.insert(0, GUI_DIR)

from PySide6.QtWidgets import QApplication   # noqa: E402
from app import MainWindow, EXPORT_COLUMNS   # noqa: E402

import _skip                                  # noqa: E402
_skip.require()

POEM ='白日依山尽，黄河入海流。欲穷千里目，更上一层楼。'
# reference values reproduced from the paper (frozen v1.0)
EXPECT = {'GPDI': 15.53, 'ACD_star': 0.200, 'HDCR': 5.00, 'OOVR': 0.00, 'TL_star': 0.528}


def main():
    app = QApplication([])
    win = MainWindow()

    print('inventory chars :', len(win.inventory))
    print('reference bands :', win.bands)

    win.input.setPlainText(POEM)
    win.on_analyze()

    got = {
        'GPDI': float(win.v_gpdi.text()),
        'ACD_star': float(win.v_acd.text()),
        'HDCR': float(win.v_hdcr.text().rstrip('%')),
        'OOVR': float(win.v_oovr.text().rstrip('%')),
        'TL_star': float(win.v_tl.text()),
    }
    print('\n--- single-poem metrics ---')
    ok = True
    for k, exp in EXPECT.items():
        diff = abs(got[k] - exp)
        flag = 'OK ' if diff < 0.01 else 'FAIL'
        if diff >= 0.01:
            ok = False
        print('  %-9s expected %8.3f   got %8.3f   %s' % (k, exp, got[k], flag))

    print('  N            =', win.v_n.text())
    print('  GPDI_char    =', win.v_gpdi_char.text())
    print('  GPRS         =', win.v_gprs.text())
    print('  band         =', win.v_band.text())
    print('  distribution =', win.v_dist.text())
    print('  table rows   =', win.table.rowCount())

    # --- batch + export ---
    tmpdir = tempfile.mkdtemp()
    txt = os.path.join(tmpdir, 'demo.txt')
    with open(txt, 'w', encoding='utf-8') as f:
        f.write(POEM)
    csv_in = os.path.join(tmpdir, 'demo.csv')
    with open(csv_in, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['title', 'text'])
        w.writerow(['春晓', '春眠不觉晓，处处闻啼鸟。夜来风雨声，花落知多少。'])
        w.writerow(['登鹳雀楼', POEM])

    win._read_file  # ensure attribute exists
    rows_from_txt = list(win._read_file(txt))
    rows_from_csv = list(win._read_file(csv_in))
    print('\n--- batch readers ---')
    print('  txt  ->', len(rows_from_txt), 'item(s):', rows_from_txt[0][0])
    print('  csv  ->', len(rows_from_csv), 'item(s):',
          [r[0] for r in rows_from_csv])

    out = os.path.join(tmpdir, 'out.csv')
    win.rows = []
    for title, text in rows_from_csv:
        import gpdi
        win._add_row(title, gpdi.analyze(text, inventory=win.inventory,
                                         reference_bands=win.bands))
    with open(out, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=EXPORT_COLUMNS)
        w.writeheader()
        w.writerows(win.rows)
    with open(out, encoding='utf-8-sig') as f:
        back = list(csv.DictReader(f))
    print('  exported rows:', len(back), '| columns ok:',
          list(back[0].keys()) == EXPORT_COLUMNS)
    for r in back:
        print('    %-8s N=%-3s GPDI=%-6s band=%s'
              % (r['title'], r['N'], r['GPDI'], r['corpus_band']))

    print('\nRESULT:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
