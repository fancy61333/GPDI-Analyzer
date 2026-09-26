# -*- coding: utf-8 -*-
"""
GPDI Analyzer — scoring core (spec 1.0.2)

GPDI = Graded Poetry Difficulty Index
GPRS = 100 - GPDI   (readability score; reported next to GPDI in the
                     manuscript's grading table)

Scoring specification frozen from the FLA manuscript corpus
(01_GPDI_final_poetry_corpus.xlsx, 100 texts / 82 deduplicated poems).

    ACD*  = (ACD - 1) / 5
    TL*   = min(ln(N+1) / ln(N_ref_max+1), 1),   N_ref_max = 317
    GPDI      = 100 * (0.45*ACD* + 0.25*HDCR + 0.20*OOVR + 0.10*TL*)
    GPDI_char = 100 * (0.50*ACD* + 0.278*HDCR + 0.222*OOVR)

The GPDI weights are applied directly, exactly as printed in the paper —
0.45 / 0.25 / 0.20 / 0.10. (Earlier builds reached the character layer through
0.90 x (0.50 / 0.278 / 0.222), which expands to 0.45 / 0.2502 / 0.1998;
the difference is < 0.003 GPDI points but it is not "exact", so it was removed.)

GPDI_char is the character-only variant: the character layer on its own 0-100
scale, with the coefficients printed in the manuscript. It is the manuscript's
character-only robustness scenario (50 / 27.8 / 22.2 / 0), i.e. 45 / 25 / 20
renormalised over the character layer; the study does not name it as a second
index. Reproducing the manuscript's own
GPDI_char column requires those three printed coefficients: with the exact
renormalisation (25/90, 20/90) the residual is 0.014, with 0.278 / 0.222 it is
0.0005 — the rounding of the published column. See tools/robustness.py.

Because 0.278 / 0.222 are 3-dp printings of 0.277778 / 0.222222,
GPDI = 0.90*GPDI_char + 10*TL* holds only to within 0.013 of a GPDI point;
GPDI itself is computed from the 0.45 / 0.25 / 0.20 / 0.10 weights alone, so the
index the study reports is unaffected.
"""

import csv
import math
import os
import struct
import zlib

# ---------------------------------------------------------------------------
# Frozen constants (spec 1.0.2 — do not change without a version bump)
# ---------------------------------------------------------------------------
SPEC_VERSION = '1.0.2'      # algorithm spec - bump it whenever a constant moves
RELEASE_VERSION = '1.0.0'   # the distributed build; what the paper cites

W_ACD = 0.45      # GPDI weight of ACD*      (paper: .45)
W_HDCR = 0.25     # GPDI weight of HDCR      (paper: .25)
W_OOVR = 0.20     # GPDI weight of OOVR      (paper: .20)
W_LEN = 0.10      # GPDI weight of TL*       (paper: .10)
W_CHAR = W_ACD + W_HDCR + W_OOVR   # 0.90 — the character layer's total share

# GPDI_char coefficients, exactly as printed in the manuscript (Section 4.6,
# character-only scenario 50/27.8/22.2/0 = the character layer renormalised).
W_CHAR_ACD = 0.50
W_CHAR_HDCR = 0.278
W_CHAR_OOVR = 0.222

OOV_VALUE = 6     # numeric value assigned to a character outside the 3500 inventory
ACD_MIN = 1.0     # ACD normalisation floor (level value of the easiest band)
ACD_SPAN = 5.0    # ACD normalisation span (6 - 1)
N_REF_MAX = 317   # longest text in the reference corpus; denominator of TL*

HDCR_LEVELS = (4, 5)   # 丁 + 戊 count as high-difficulty characters

LEVEL_LABEL = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', OOV_VALUE: 'OOV'}
LEVEL_NAME = {1: '甲级', 2: '乙级', 3: '丙级', 4: '丁级', 5: '戊级', OOV_VALUE: '超纲'}

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INVENTORY = os.path.join(HERE, '..', 'data', 'char_inventory.csv')
# what the released bundles actually carry - see tools/pack_inventory.py
DEFAULT_INVENTORY_PACKED = os.path.join(HERE, '..', 'data', 'char_inventory.bin')
DEFAULT_REFERENCE = os.path.join(HERE, '..', 'data', 'corpus_frozen.csv')
DEFAULT_VARIANT_MAP = os.path.join(HERE, '..', 'data', 'variant_map.tsv')

_INVENTORY_MAGIC = b'GPIN1'


class InventoryMissing(Exception):
    """No graded character inventory is available.

    The inventory is not distributed with the software - see the "What is not
    included" section of the README. A public bundle therefore starts empty and
    the user has to point the application at a copy they are entitled to use.
    """


def find_inventory():
    """Path of the first inventory file that exists, or None.

    Packed blob first (what a private bundle carries), raw CSV second (what a
    research checkout has). Neither is present in a public build.
    """
    for p in (DEFAULT_INVENTORY_PACKED, DEFAULT_INVENTORY):
        if os.path.exists(p):
            return p
    return None


def load_inventory(path=None):
    """Load the 3500-character inventory: char -> level value (1..5).

    Accepts either form:
      * a packed, compressed blob (`char_inventory.bin`) - what a private
        bundle carries, produced by tools/pack_inventory.py;
      * the raw CSV (`char_inventory.csv`) - the research source file,
        deliberately not distributed.

    With no argument the packed blob is preferred and the CSV is the fallback,
    so the same code path works in a source checkout and in a frozen bundle.
    Raises InventoryMissing when neither is present, which is the normal state
    of a public build.
    """
    if path is None:
        path = find_inventory()
        if path is None:
            raise InventoryMissing(
                'No graded character inventory found.\n\n'
                'GPDI Analyzer is distributed without one. Supply a copy you '
                'are entitled to use: a CSV with char,level_value columns, or '
                'the packed .bin form written by tools/pack_inventory.py.')

    with open(path, 'rb') as f:
        head = f.read(5)

    if head == _INVENTORY_MAGIC:
        return _load_inventory_packed(path)

    inv = {}
    with open(path, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            ch = (row.get('char') or '').strip()
            if not ch:
                continue
            try:
                inv[ch] = int(row['level_value'])
            except (TypeError, ValueError):
                continue
    return inv


def _load_inventory_packed(path):
    """Read the packed inventory blob written by tools/pack_inventory.py.

    Format: b'GPIN1' | zlib( uint32 n | uint32 chars_len | chars | n level
    bytes ). Compressed, not encrypted - see the note in tools/pack_inventory.py
    about what that does and does not guarantee.
    """
    blob = open(path, 'rb').read()
    if blob[:5] != _INVENTORY_MAGIC:
        raise ValueError('not a packed inventory: %s' % path)
    raw = zlib.decompress(blob[5:])
    n, chars_len = struct.unpack('>II', raw[:8])
    chars = raw[8:8 + chars_len].decode('utf-8')
    levels = raw[8 + chars_len:8 + chars_len + n]
    if len(chars) != n or len(levels) != n:
        raise ValueError('packed inventory is inconsistent: %s' % path)
    return dict(zip(chars, levels))


def load_variant_map(path=DEFAULT_VARIANT_MAP):
    """Glyph normalisation table: traditional / non-standard form -> standard form.

    Generated by tools/build_variant_map.py (from zhconv, zh-cn). Source glyphs
    that occur in the 82-poem frozen corpus are excluded at build time, so the
    table can never move a published figure. Missing file -> empty table.
    """
    vmap = {}
    if not os.path.exists(path):
        return vmap
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) != 2:
                continue
            src, dst = parts[0].strip(), parts[1].strip()
            if src and dst:
                vmap[src] = dst
    return vmap


def normalize(text, inventory=None, variant_map=None):
    """Strip punctuation, whitespace, digits and latin characters, then apply
    glyph normalisation.

    Two steps:
      1. keep CJK ideographs only (punctuation, latin, digits, spacing dropped);
      2. any character the inventory does not contain is looked up in the glyph
         table and replaced by its standard form (traditional -> simplified, and
         other established one-to-one mappings).

    Characters that are already in the inventory are left untouched, so a
    standard-form text is scored exactly as written. Variant forms that the
    reference corpus itself uses (峯, 邨, 敎 …) are deliberately not merged —
    see tools/build_variant_map.py and docs/corpus_provenance.md.
    """
    if inventory is None:
        inventory = load_inventory()
    if variant_map is None:
        variant_map = load_variant_map()

    out = []
    for ch in text or '':
        o = ord(ch)
        if not (0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF or 0xF900 <= o <= 0xFAFF):
            continue                       # punctuation, latin, digits, spaces
        if ch in inventory:
            out.append(ch)                 # standard form already
        else:
            out.append(variant_map.get(ch, ch))
    return ''.join(out)


def analyze(text, inventory=None, reference_bands=None):
    """Score one poem.

    Returns a dict with N, ACD, ACD*, HDCR, OOVR, TL*, GPDI_char, GPDI, GPRS,
    the A-E / OOV character profile, and (if reference_bands given) the
    corpus-relative band.
    """
    if inventory is None:
        inventory = load_inventory()

    clean = normalize(text, inventory)
    n = len(clean)
    if n == 0:
        return {'error': 'empty text after normalisation'}

    level_sum = 0
    hd_count = 0
    oov_count = 0
    dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, OOV_VALUE: 0}
    profile = []

    for ch in clean:
        lv = inventory.get(ch, OOV_VALUE)
        level_sum += lv
        dist[lv] = dist.get(lv, 0) + 1
        if lv == OOV_VALUE:
            oov_count += 1
        elif lv in HDCR_LEVELS:
            hd_count += 1
        profile.append({'char': ch, 'level': lv, 'label': LEVEL_LABEL.get(lv, '?')})

    acd = level_sum / n
    acd_star = (acd - ACD_MIN) / ACD_SPAN
    hdcr = hd_count / n
    oovr = oov_count / n
    # TL* is a normalised index, so it saturates at 1. The clamp never binds for
    # a text inside the reference range (the longest poem in the 82-poem corpus is
    # 155 characters against N_ref_max = 317); it only stops texts longer than the
    # reference maximum from pushing the length term above its 10% weight.
    tl_star = min(math.log(n + 1) / math.log(N_REF_MAX + 1), 1.0)

    # paper-exact weights, applied directly (no intermediate rounding)
    char_share = W_ACD * acd_star + W_HDCR * hdcr + W_OOVR * oovr   # .45/.25/.20
    gpdi = 100.0 * (char_share + W_LEN * tl_star)
    gpdi_char = 100.0 * (W_CHAR_ACD * acd_star + W_CHAR_HDCR * hdcr
                         + W_CHAR_OOVR * oovr)
    gprs = 100.0 - gpdi

    result = {
        'N': n,
        'ACD': round(acd, 4),
        'ACD_star': round(acd_star, 4),
        'HDCR': round(hdcr, 4),
        'OOVR': round(oovr, 4),
        'TL_star': round(tl_star, 4),
        'GPDI_char': round(gpdi_char, 2),
        'GPDI': round(gpdi, 2),
        'GPRS': round(gprs, 2),
        'char_distribution': {LEVEL_LABEL[k]: v for k, v in dist.items() if v},
        'profile': profile,
        'text_normalized': clean,
    }

    if reference_bands:
        # compare on the published two-decimal scale: the cut-points are read
        # off the frozen GPDI column, which is itself rounded to two decimals
        result['corpus_band'] = band_of(round(gpdi, 2), reference_bands)
    return result


def load_reference_bands(path=DEFAULT_REFERENCE):
    """Cut-points of the five corpus bands, taken from the frozen assignment.

    The study groups the 82 poems 17 / 17 / 16 / 16 / 16 — not five equal
    fifths — so the cut-points are read off the frozen `final_band` column
    instead of being recomputed as quantiles: band k covers every GPDI from its
    own lower bound up to the lower bound of band k+1. Scheme:

        band 1  GPDI <  21.63      (17 poems, 4.94 – 21.31)
        band 2  21.63 – 25.17      (17 poems)
        band 3  25.17 – 27.19      (16 poems)
        band 4  27.19 – 30.24      (16 poems)
        band 5  GPDI >= 30.24      (16 poems, 30.24 – 44.02)

    Reproducing the frozen band of all 82 poems is asserted by
    tests/test_bands.py.
    """
    rows = []
    with open(path, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if (row.get('in_poetry_corpus') or '').strip() != 'Y':
                continue
            if (row.get('is_duplicate') or '').strip() == 'Y':
                continue
            rows.append(row)

    by_band = {}
    for row in rows:
        try:
            b = int(str(row.get('final_band') or '').strip())
            gp = float(row['GPDI'])
        except (TypeError, ValueError):
            continue
        by_band.setdefault(b, []).append(gp)

    if len(by_band) >= 5:
        sizes = {b: len(v) for b, v in sorted(by_band.items())}
        cuts = [min(by_band[b]) for b in sorted(by_band) if b >= 2]
        allgp = sorted(g for v in by_band.values() for g in v)
        return {'cuts': cuts, 'min': allgp[0], 'max': allgp[-1],
                'n': len(allgp), 'sizes': sizes,
                'scheme': 'frozen-band-lower-bound'}

    # fallback for a corpus file without the frozen band column
    gps = sorted(float(r['GPDI']) for r in rows if r.get('GPDI'))
    if len(gps) < 5:
        return None
    k = len(gps) // 5
    return {'cuts': [gps[i * k] for i in range(1, 5)], 'min': gps[0],
            'max': gps[-1], 'n': len(gps), 'sizes': {},
            'scheme': 'equal-quantile-fallback'}


def band_of(gpdi, bands):
    """Corpus-relative band 1 (easiest) .. 5 (hardest)."""
    if not bands:
        return None
    for i, c in enumerate(bands['cuts'], start=1):
        if gpdi < c:
            return i
    return 5


DISCLAIMER = (
    "GPDI measures character-level textual demand. It does not estimate overall "
    "readability, literary difficulty, or individual learner proficiency."
)


if __name__ == '__main__':
    inv = load_inventory()
    bands = load_reference_bands()
    demo = "白日依山尽，黄河入海流。欲穷千里目，更上一层楼。"
    r = analyze(demo, inv, bands)
    print("诗     :", demo)
    print("字级标注:", ' '.join(f"{p['char']}[{p['label']}]" for p in r['profile']))
    print("-" * 60)
    print(f"N      (字数)   : {r['N']}")
    print(f"ACD    (平均字级): {r['ACD']}")
    print(f"ACD*   (归一)   : {r['ACD_star']}")
    print(f"HDCR   (高难字) : {r['HDCR']:.2%}")
    print(f"OOVR   (超纲字) : {r['OOVR']:.2%}")
    print(f"TL*    (长度)   : {r['TL_star']}")
    print(f"GPDI_char       : {r['GPDI_char']}")
    print(f"GPDI            : {r['GPDI']}")
    print(f"GPRS            : {r['GPRS']}")
    print(f"Corpus band     : Band {r.get('corpus_band')}")
    print("字级分布:", r['char_distribution'])
    print("-" * 60)
    print(DISCLAIMER)
