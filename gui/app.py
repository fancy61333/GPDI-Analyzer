# -*- coding: utf-8 -*-
"""
GPDI Analyzer — desktop GUI (PySide6)

A Character-Level Text Profiling Tool for Classical Chinese Poetry

Pipeline: input poem -> character normalisation -> 3500-character inventory
matching -> ACD* / HDCR / OOVR / TL* -> GPDI -> A-E / OOV character profile ->
corpus-relative band (82-poem reference) -> CSV export.
"""

import csv
import os
import sys
import tempfile

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QGroupBox, QHeaderView, QAbstractItemView,
)

# ---- locate core / data both in dev and in a PyInstaller bundle ----
if getattr(sys, 'frozen', False):
    ROOT = sys._MEIPASS
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(ROOT, 'core'))
import gpdi  # noqa: E402


def resource_path(rel):
    return os.path.join(ROOT, rel)


REFERENCE_PATH = resource_path(os.path.join('data', 'corpus_frozen.csv'))

LEVEL_COLOR = {
    'A': '#27AE60', 'B': '#2ECC71', 'C': '#F39C12',
    'D': '#E67E22', 'E': '#C0392B', 'OOV': '#95A5A6',
}

EXPORT_COLUMNS = ['title', 'N', 'ACD', 'ACD_star', 'HDCR', 'OOVR',
                  'TL_star', 'GPDI_char', 'GPDI', 'GPRS', 'corpus_band']


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('GPDI Analyzer v%s' % gpdi.RELEASE_VERSION)
        self.resize(820, 760)

        # A public build carries no inventory, so start empty rather than
        # crash - the user loads one they are entitled to use.
        self.inventory = None
        self.inventory_path = gpdi.find_inventory()
        if self.inventory_path:
            self.inventory = gpdi.load_inventory(self.inventory_path)
        try:
            self.bands = gpdi.load_reference_bands(REFERENCE_PATH)
        except Exception:
            self.bands = None
        self.rows = []          # accumulated results for CSV export

        self._build_ui()

    # ---------------------------------------------------------------- UI
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(16, 14, 16, 12)

        title = QLabel('GPDI Analyzer')
        title.setFont(QFont('Segoe UI', 17, QFont.Bold))
        sub = QLabel('A Character-Level Text Profiling Tool for Classical Chinese Poetry')
        sub.setStyleSheet('color:#666;')
        root.addWidget(title)
        root.addWidget(sub)

        # --- inventory status ---
        inv_row = QHBoxLayout()
        self.lbl_inv = QLabel()
        self.lbl_inv.setWordWrap(True)
        inv_row.addWidget(self.lbl_inv, 1)
        self.btn_inv = QPushButton('Load inventory …')
        self.btn_inv.clicked.connect(self.on_load_inventory)
        inv_row.addWidget(self.btn_inv)
        root.addLayout(inv_row)

        # --- input ---
        root.addWidget(QLabel('Paste Classical Chinese poem:'))
        self.input = QTextEdit()
        self.input.setPlaceholderText('白日依山尽，黄河入海流。欲穷千里目，更上一层楼。')
        self.input.setFixedHeight(110)
        root.addWidget(self.input)

        btn_row = QHBoxLayout()
        self.btn_analyze = QPushButton('Analyze')
        self.btn_analyze.setDefault(True)
        self.btn_analyze.clicked.connect(self.on_analyze)
        self.btn_batch = QPushButton('Load .txt / .csv …')
        self.btn_batch.clicked.connect(self.on_batch)
        self.btn_export = QPushButton('Export CSV')
        self.btn_export.clicked.connect(self.on_export)
        self.btn_clear = QPushButton('Clear')
        self.btn_clear.clicked.connect(self.on_clear)
        for b in (self.btn_analyze, self.btn_batch, self.btn_export, self.btn_clear):
            btn_row.addWidget(b)
        root.addLayout(btn_row)

        # --- metrics ---
        box = QGroupBox('Metrics')
        g = QGridLayout(box)
        self.v_gpdi = self._big_label(g, 0, 0, 'GPDI')
        self.v_gprs = self._small_label(g, 0, 1, 'GPRS')
        self.v_acd = self._small_label(g, 1, 0, 'ACD*')
        self.v_hdcr = self._small_label(g, 1, 1, 'HDCR')
        self.v_oovr = self._small_label(g, 1, 2, 'OOVR')
        self.v_tl = self._small_label(g, 1, 3, 'TL*')
        self.v_n = self._small_label(g, 2, 0, 'N (chars)')
        self.v_gpdi_char = self._small_label(g, 2, 1, 'GPDI_char')
        self.v_band = self._small_label(g, 2, 2, 'Corpus band')
        self.v_dist = self._small_label(g, 2, 3, 'A–E / OOV')
        root.addWidget(box)

        # --- character profile ---
        root.addWidget(QLabel('Character profile'))
        self.profile = QTextEdit()
        self.profile.setReadOnly(True)
        self.profile.setFixedHeight(96)
        root.addWidget(self.profile)

        # --- batch table ---
        self.table = QTableWidget(0, len(EXPORT_COLUMNS))
        self.table.setHorizontalHeaderLabels(EXPORT_COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setMinimumHeight(150)
        root.addWidget(self.table)

        # --- fixed disclaimer (must match the paper's construct boundary) ---
        disc = QLabel(gpdi.DISCLAIMER)
        disc.setWordWrap(True)
        disc.setStyleSheet('color:#888; font-size:10px; padding-top:4px;')
        root.addWidget(disc)

        self._refresh_inventory_status()

    def _refresh_inventory_status(self):
        if self.inventory:
            self.lbl_inv.setText('Inventory: %s  ·  %d characters'
                                 % (os.path.basename(self.inventory_path),
                                    len(self.inventory)))
            self.lbl_inv.setStyleSheet('color:#27AE60;')
        else:
            self.lbl_inv.setText(
                'No character inventory loaded. The graded inventory is not '
                'distributed with this software — load a copy you are '
                'entitled to use to start analysing text.')
            self.lbl_inv.setStyleSheet('color:#C0392B;')
        self.btn_analyze.setEnabled(bool(self.inventory))
        self.btn_batch.setEnabled(bool(self.inventory))

    def on_load_inventory(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Select a graded character inventory', '',
            'Inventory (*.csv *.bin);;All files (*)')
        if not path:
            return
        try:
            inv = gpdi.load_inventory(path)
        except Exception as exc:
            QMessageBox.warning(self, 'GPDI Analyzer',
                                'Could not read that file:\n%s' % exc)
            return
        if not inv:
            QMessageBox.warning(self, 'GPDI Analyzer',
                                'That file contains no character entries.')
            return
        self.inventory = inv
        self.inventory_path = path
        self._refresh_inventory_status()

    def _big_label(self, grid, r, c, name):
        grid.addWidget(QLabel(name), r, c)
        lab = QLabel('—')
        lab.setFont(QFont('Segoe UI', 20, QFont.Bold))
        lab.setStyleSheet('color:#2C3E50;')
        grid.addWidget(lab, r, c, alignment=Qt.AlignLeft)
        return lab

    def _small_label(self, grid, r, c, name):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        n = QLabel(name)
        n.setStyleSheet('color:#888; font-size:10px;')
        val = QLabel('—')
        val.setFont(QFont('Segoe UI', 12, QFont.Bold))
        v.addWidget(n)
        v.addWidget(val)
        grid.addWidget(w, r, c)
        return val

    # ------------------------------------------------------------ actions
    def on_analyze(self):
        if not self.inventory:
            QMessageBox.information(self, 'GPDI Analyzer',
                                    'Load a character inventory first.')
            return
        text = self.input.toPlainText().strip()
        if not text:
            QMessageBox.information(self, 'GPDI Analyzer', 'Please paste a poem first.')
            return
        res = gpdi.analyze(text, inventory=self.inventory, reference_bands=self.bands)
        if 'error' in res:
            QMessageBox.warning(self, 'GPDI Analyzer', res['error'])
            return
        self._show_single(res)
        self._add_row('(input)', res)

    def on_batch(self):
        if not self.inventory:
            QMessageBox.information(self, 'GPDI Analyzer',
                                    'Load a character inventory first.')
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self, 'Select .txt or .csv files', '', 'Text / CSV (*.txt *.csv)')
        if not paths:
            return
        done = 0
        for p in paths:
            for title, text in self._read_file(p):
                res = gpdi.analyze(text, inventory=self.inventory, reference_bands=self.bands)
                if 'error' in res:
                    continue
                self._add_row(title, res)
                done += 1
        QMessageBox.information(self, 'GPDI Analyzer', 'Analysed %d text(s).' % done)

    def _read_file(self, path):
        """Yield (title, text) pairs from a .txt or .csv file."""
        ext = os.path.splitext(path)[1].lower()
        base = os.path.basename(path)
        if ext == '.txt':
            with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                yield (base, f.read())
            return
        with open(path, 'r', encoding='utf-8-sig', errors='ignore', newline='') as f:
            rd = csv.DictReader(f)
            fields = rd.fieldnames or []
            lower = {k.lower().strip(): k for k in fields}
            tcol = lower.get('title') or lower.get('clean_title')
            xcol = lower.get('text') or lower.get('content') or lower.get('content_clean')
            for i, row in enumerate(rd, 1):
                if xcol:
                    text = row.get(xcol) or ''
                    title = (row.get(tcol) if tcol else None) or 'row%d' % i
                else:
                    vals = [v for v in row.values() if v]
                    text = vals[-1] if vals else ''
                    title = vals[0] if vals else 'row%d' % i
                if text.strip():
                    yield (title, text)

    def _show_single(self, res):
        self.v_gpdi.setText('%.2f' % res['GPDI'])
        self.v_gprs.setText('%.2f' % res['GPRS'])
        self.v_acd.setText('%.3f' % res['ACD_star'])
        self.v_hdcr.setText('%.2f%%' % (res['HDCR'] * 100))
        self.v_oovr.setText('%.2f%%' % (res['OOVR'] * 100))
        self.v_tl.setText('%.3f' % res['TL_star'])
        self.v_n.setText('%d' % res['N'])
        self.v_gpdi_char.setText('%.2f' % res['GPDI_char'])
        self.v_band.setText('Band %s' % res['corpus_band'] if res.get('corpus_band') else '—')
        dist = res['char_distribution']
        self.v_dist.setText('  '.join('%s:%d' % (k, dist[k])
                                      for k in ['A', 'B', 'C', 'D', 'E', 'OOV'] if dist.get(k)))
        self.profile.setHtml(self._profile_html(res['profile']))

    def _profile_html(self, profile):
        parts = []
        for p in profile:
            col = LEVEL_COLOR.get(p['label'], '#333')
            parts.append('%s<span style="color:%s;font-weight:bold">[%s]</span>'
                         % (p['char'], col, p['label']))
        return '<span style="font-size:15px;line-height:1.9">%s</span>' % ' '.join(parts)

    def _add_row(self, title, res):
        self.rows.append({
            'title': title, 'N': res['N'], 'ACD': res['ACD'],
            'ACD_star': res['ACD_star'], 'HDCR': res['HDCR'], 'OOVR': res['OOVR'],
            'TL_star': res['TL_star'], 'GPDI_char': res['GPDI_char'],
            'GPDI': res['GPDI'], 'GPRS': res['GPRS'],
            'corpus_band': res.get('corpus_band') or '',
        })
        r = self.table.rowCount()
        self.table.insertRow(r)
        for c, key in enumerate(EXPORT_COLUMNS):
            v = self.rows[-1][key]
            txt = ('%.4f' % v) if isinstance(v, float) else str(v)
            self.table.setItem(r, c, QTableWidgetItem(txt))

    def on_export(self):
        if not self.rows:
            QMessageBox.information(self, 'GPDI Analyzer', 'Nothing to export yet.')
            return
        path, _ = QFileDialog.getSaveFileName(
            self, 'Export results', 'gpdi_results.csv', 'CSV (*.csv)')
        if not path:
            return
        with open(path, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=EXPORT_COLUMNS)
            w.writeheader()
            w.writerows(self.rows)
        QMessageBox.information(self, 'GPDI Analyzer', 'Exported %d row(s).' % len(self.rows))

    def on_clear(self):
        self.input.clear()
        self.profile.clear()
        self.table.setRowCount(0)
        self.rows = []
        for lab in (self.v_gpdi, self.v_gprs, self.v_acd, self.v_hdcr, self.v_oovr,
                    self.v_tl, self.v_n, self.v_gpdi_char, self.v_band, self.v_dist):
            lab.setText('—')


DEMO = '白日依山尽，黄河入海流。欲穷千里目，更上一层楼。'


def selftest():
    """Headless self-check for the frozen bundle.

    If an inventory is present it verifies that the reference poem reproduces
    the frozen spec figures.  A public bundle ships without one, so the check
    reports that and stops.  The result is written to %TEMP%/gpdi_selftest.txt
    because a --windowed build has no console.
    """
    path = os.path.join(tempfile.gettempdir(), 'gpdi_selftest.txt')
    inv_path = gpdi.find_inventory()
    with open(path, 'w', encoding='utf-8') as f:
        f.write('release=%s\n' % gpdi.RELEASE_VERSION)
        f.write('spec=%s\n' % gpdi.SPEC_VERSION)
        if inv_path is None:
            f.write('inventory=none\n')
            f.write('note=no inventory bundled (see README, "What is not '
                    'included"); load one to run the numeric check\n')
            return path
        inv = gpdi.load_inventory(inv_path)
        try:
            bands = gpdi.load_reference_bands(REFERENCE_PATH)
        except Exception:
            bands = None
        r = gpdi.analyze(DEMO, inventory=inv, reference_bands=bands)
        f.write('inventory_chars=%d\n' % len(inv))
        f.write('bands=%s\n' % (bands['cuts'] if bands else None))
        for k in ('N', 'ACD_star', 'HDCR', 'OOVR', 'TL_star',
                  'GPDI_char', 'GPDI', 'GPRS'):
            f.write('%s=%s\n' % (k, r[k]))
        f.write('corpus_band=%s\n' % r.get('corpus_band'))
    return path


def main():
    if '--selftest' in sys.argv:
        selftest()
        return 0
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
