# -*- coding: utf-8 -*-
"""Pack the graded character inventory for shipment, and stage the data dir.

Why this exists
---------------
The inventory (`data/char_inventory.csv`) is an internal research asset: it is
deliberately kept out of the repository and is meant to reach users only
*embedded in the compiled application*. Passing `--add-data "data;data"` to
PyInstaller defeated that: it copied the raw CSV into the bundle, so every
download of the Windows/macOS archive contained a plain, Excel-openable table of
all 3,500 characters with their 甲/乙/丙/丁/戊 labels.

This script builds `build_data/` instead:

  build_data/char_inventory.bin    the inventory, packed and zlib-compressed
  build_data/variant_map.tsv       glyph-normalisation table (public)
  build_data/corpus_frozen.csv     reference statistics (withheld, private build)
  build_data/poems_82_text.csv     reference texts (withheld, private build)
  build_data/titles_82.tsv         reference index (withheld, private build)

The build scripts point PyInstaller at `build_data/`, so `data/` - and with it
the raw CSV - never enters the bundle.

Two modes
---------

    python tools/pack_inventory.py            private build: everything above
    python tools/pack_inventory.py --public   public build: variant_map.tsv only

The public mode is what the released archive is made of. It carries neither the
inventory nor the reference corpus - the inventory because it is a third-party
research asset, the corpus because its per-poem figures are not published yet.
The application therefore starts without an inventory and the user loads one
they are entitled to use; see the "What is not included" section of the README.

Honest scope of the protection: the packed file is compressed, not encrypted.
Anyone who unpacks the application can still recover the table with a few lines
of Python. That is precisely why the public mode omits it altogether rather than
relying on the packing.

Blob format (all integers big-endian):

    b'GPIN1' | zlib( uint32 n | uint32 chars_len | chars (utf-8) | n level bytes )

The magic sits outside the compressed section so the file can be identified
without decompressing it.

Run from the project root:

    python tools/pack_inventory.py
"""

import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
DATA = os.path.join(ROOT, 'data')
STAGE = os.path.join(ROOT, 'build_data')

MAGIC = b'GPIN1'
HEADER = struct.Struct('>II')

SRC_CSV = os.path.join(DATA, 'char_inventory.csv')
OUT_BIN = os.path.join(STAGE, 'char_inventory.bin')

# staged in both modes
PUBLIC = ['variant_map.tsv']
# staged in a private build only - per-poem figures that are not published yet
WITHHELD = ['corpus_frozen.csv', 'poems_82_text.csv', 'titles_82.tsv']
# never staged in any mode
FORBIDDEN = ['char_inventory.csv']


def read_csv(path):
    """char_inventory.csv -> (chars, levels). Mirrors gpdi.load_inventory()."""
    import csv
    chars, levels = [], []
    with open(path, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            ch = (row.get('char') or '').strip()
            if not ch:
                continue
            try:
                lv = int(row['level_value'])
            except (TypeError, ValueError):
                continue
            chars.append(ch)
            levels.append(lv)
    return chars, levels


def pack(chars, levels):
    """-> (uncompressed payload, file blob).

    The magic stays outside the compressed section so the file can be
    identified without decompressing it.
    """
    chars_bytes = ''.join(chars).encode('utf-8')
    payload = HEADER.pack(len(chars), len(chars_bytes)) + chars_bytes \
        + bytes(levels)
    return payload, MAGIC + zlib.compress(payload, 9)


def unpack(blob):
    """Inverse of pack() - used by the self-check below and by gpdi.py."""
    if blob[:5] != MAGIC:
        raise ValueError('not a packed inventory')
    raw = zlib.decompress(blob[5:])
    n, clen = HEADER.unpack(raw[:8])
    chars = raw[8:8 + clen].decode('utf-8')
    levels = raw[8 + clen:8 + clen + n]
    if len(chars) != n or len(levels) != n:
        raise ValueError('packed inventory is inconsistent')
    return chars, levels


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    public = '--public' in argv

    if not os.path.isdir(STAGE):
        os.makedirs(STAGE)

    # A stale blob from an earlier private build must never survive into a
    # public one, so clear the stage before staging anything.
    for stale in os.listdir(STAGE):
        os.remove(os.path.join(STAGE, stale))

    if public:
        print('mode      : public (no inventory, no reference corpus)')
    else:
        if not os.path.exists(SRC_CSV):
            sys.stderr.write(
                'ERROR: %s not found.\n'
                'The graded inventory is not distributed with the repository. '
                'Place the file in data/ before a private build, or pass '
                '--public to build the distributable bundle.\n' % SRC_CSV)
            return 2

    copied = []
    names = list(PUBLIC) if public else list(PUBLIC) + list(WITHHELD)
    for name in names:
        src = os.path.join(DATA, name)
        if os.path.exists(src):
            dst = os.path.join(STAGE, name)
            with open(src, 'rb') as fi, open(dst, 'wb') as fo:
                fo.write(fi.read())
            copied.append(name)

    if public:
        for name in copied:
            print('staged    : %s' % os.path.join(STAGE, name))
        print('The inventory and the reference corpus are NOT staged.')
        return 0

    chars, levels = read_csv(SRC_CSV)
    payload, blob = pack(chars, levels)
    with open(OUT_BIN, 'wb') as f:
        f.write(blob)

    # round-trip check before the build trusts the file
    r_chars, r_levels = unpack(blob)
    if list(r_chars) != chars or list(r_levels) != levels:
        sys.stderr.write('ERROR: packed inventory does not round-trip\n')
        return 3

    print('mode      : private (inventory packed, reference corpus included)')
    print('inventory : %d characters' % len(chars))
    print('raw bytes : %d -> packed %d (%.1f%% of the CSV)'
          % (len(payload), len(blob),
             100.0 * len(blob) / max(os.path.getsize(SRC_CSV), 1)))
    print('staged    : %s' % OUT_BIN)
    for name in copied:
        print('            %s' % os.path.join(STAGE, name))
    print('The raw CSV in data/ is NOT copied - it must not enter the bundle.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
