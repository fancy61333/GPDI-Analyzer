# -*- coding: utf-8 -*-
"""The graded inventory must never ship as a raw, openable table.

Background: the release archives used to be built with `--add-data "data;data"`,
which copied `data/char_inventory.csv` - 45 KB of plain text listing all 3,500
characters with their 甲/乙/丙/丁/戊 labels - straight into the bundle. Anyone
downloading the release zip could open it in Excel.

This test fails if that comes back. Three checks:

  1. the packed blob round-trips to exactly the CSV inventory;
  2. the build staging directory holds no raw inventory file;
  3. no build script or spec points PyInstaller at `data/`.

Run from the project root:  .venv\\Scripts\\python tests\\test_inventory_pack.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(ROOT, 'core'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import gpdi                       # noqa: E402
import pack_inventory             # noqa: E402

if not os.path.exists(os.path.join(ROOT, 'data', 'char_inventory.csv')):
    print('SKIPPED - the graded inventory is not distributed with this '
          'repository; see the README section "What is not included".')
    sys.exit(0)

CSV = os.path.join(ROOT, 'data', 'char_inventory.csv')
STAGE = os.path.join(ROOT, 'build_data')


def main():
    failures = []

    # --- 1. round-trip ------------------------------------------------------
    if not os.path.exists(CSV):
        print('SKIP  data/char_inventory.csv not present (not distributed)')
    else:
        chars, levels = pack_inventory.read_csv(CSV)
        payload, blob = pack_inventory.pack(chars, levels)
        r_chars, r_levels = pack_inventory.unpack(blob)
        ok = list(r_chars) == chars and list(r_levels) == levels
        print('%-5s packed blob round-trips to the CSV (%d characters)'
              % ('PASS' if ok else 'FAIL', len(chars)))
        if not ok:
            failures.append('round-trip')

        from_csv = gpdi.load_inventory(CSV)
        if os.path.exists(os.path.join(STAGE, 'char_inventory.bin')):
            from_bin = gpdi.load_inventory(os.path.join(STAGE,
                                                        'char_inventory.bin'))
            ok = from_csv == from_bin
            print('%-5s gpdi.load_inventory(bin) == gpdi.load_inventory(csv)'
                  % ('PASS' if ok else 'FAIL'))
            if not ok:
                failures.append('loader equivalence')

    # --- 2. nothing raw in the staging directory -----------------------------
    if os.path.isdir(STAGE):
        bad = [n for n in os.listdir(STAGE)
               if n.lower().startswith('char_inventory')
               and not n.endswith('.bin')]
        ok = not bad
        print('%-5s build_data/ holds no raw inventory file%s'
              % ('PASS' if ok else 'FAIL',
                 '' if ok else ' -> ' + ', '.join(bad)))
        if not ok:
            failures.append('staged raw inventory')
    else:
        print('SKIP  build_data/ not staged yet (run tools/pack_inventory.py)')

    # --- 3. build definitions must not point at data/ ------------------------
    for name, needle in (('build_windows.bat', '"data;data"'),
                         ('build_macos.sh', '"data:data"'),
                         ('GPDI-Analyzer.spec', "('data', 'data')")):
        path = os.path.join(ROOT, name)
        if not os.path.exists(path):
            print('SKIP  %s not found' % name)
            continue
        text = open(path, 'r', encoding='utf-8', errors='replace').read()
        ok = needle not in text
        print('%-5s %s does not bundle the raw data/ directory'
              % ('PASS' if ok else 'FAIL', name))
        if not ok:
            failures.append('%s bundles data/' % name)

    print()
    if failures:
        print('RESULT: %d check(s) failed -> %s' % (len(failures),
                                                    ', '.join(failures)))
        return 1
    print('RESULT: all checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
