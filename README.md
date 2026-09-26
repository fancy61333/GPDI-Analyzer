# GPDI Analyzer

**A Character-Level Text Profiling Tool for Classical Chinese Poetry**

GPDI Analyzer is a standalone desktop application that computes the
**Graded Poetry Difficulty Index (GPDI)** for classical Chinese poetry — a
character-level profile of how demanding a text is, relative to a graded
character inventory.

> GPDI measures character-level textual demand. It does not estimate overall
> readability, literary difficulty, or individual learner proficiency.

---

## Download

**Release v1.0.0** — Windows:
[`GPDI-Analyzer-Windows-v1.0.0.zip`](https://github.com/fancy61333/GPDI-Analyzer/releases/download/v1.0.0/GPDI-Analyzer-Windows-v1.0.0.zip)

Unzip and run `GPDI-Analyzer.exe`. No Python installation is required.
macOS builds are produced on a Mac — see *Building from source*.

---

## What is included

| Included | Where |
|---|---|
| The application (source and compiled build) | `core/`, `gui/`, Release assets |
| Usage documentation | this file |
| The full scoring code, including every constant and weight | `core/gpdi.py` |
| Glyph-normalisation table | `data/variant_map.tsv` |
| Sample input data | `samples/sample_poems.csv` |
| Build scripts and the leak guard | `build_*.bat`, `build_macos.sh`, `tools/` |
| Licence and citation metadata | `LICENSE`, `CITATION.cff` |

---

## What is not included, and why

Two assets are deliberately withheld. Both are stated here rather than left
implicit, so that anyone reproducing the work knows exactly what they have and
what they still need.

| Not included | Reason |
|---|---|
| **The graded character inventory** (`char_inventory.csv`) | It derives from prior work of the research group and is subject to that group's intellectual-property position. It is therefore not ours to redistribute as an open data file, and no copy of it — plain-text, packed, or otherwise — is published here or in any release asset. |
| **The 82-poem reference corpus** (`corpus_frozen.csv`, `poems_82_text.csv`, `titles_82.tsv`) | Its per-poem figures are results of the associated study and are not published yet. Releasing them here would pre-empt the manuscript. |

What this means in practice:

- **The application starts with no inventory loaded.** The status line says so
  and *Analyze* stays disabled until you load one. Use **Load inventory …** and
  point the application at a copy you are entitled to use — either a CSV with
  `char,level_value` columns, or the packed `.bin` form written by
  `tools/pack_inventory.py`.
- **The corpus-relative band is unavailable** in the distributed build, because
  it is read from the reference corpus. Every other measure — GPDI, GPRS,
  ACD\*, HDCR, OOVR, TL\*, GPDI_char and the per-character profile — works as
  soon as an inventory is loaded.
- **The packaged archive is audited.** `tools/audit_leak.py --public` fails the
  build if a release archive ever carries the inventory or the reference
  corpus again.

Nothing is withheld about *how* the index is computed: the scoring code is
complete and unmodified, and every constant it uses is readable in
`core/gpdi.py`. What is withheld is an input asset and a set of unpublished
numbers.

---

## What it does

```
input poem
   -> character normalisation (CJK ideographs only; punctuation, digits,
      whitespace and latin characters removed)
   -> glyph normalisation (traditional / non-standard forms -> standard form)
   -> matching against a graded character inventory
   -> component measures: ACD*  /  HDCR  /  OOVR  /  TL*
   -> GPDI
   -> character profile (+ corpus-relative band, when a reference corpus
      is present)
   -> CSV export
```

Features:

- **Single text** — paste a poem, press *Analyze*
- **Batch input** — load `.txt` (one poem per file) or `.csv` (`title`, `text` columns)
- **Metrics panel** — GPDI, GPRS, ACD\*, HDCR, OOVR, TL\*, N, GPDI_char, corpus band
- **Character profile** — every character tagged and colour-coded
- **CSV export** — UTF-8 with BOM, opens cleanly in Excel
- **Disclaimer** — the scope statement is fixed at the bottom of the interface

The definitions of the component measures, the weighting scheme and the band
boundaries belong to the associated study and are not restated here. This
repository documents the tool, not the method.

---

## Sample data

`samples/sample_poems.csv` holds a handful of well-known classical poems in the
batch-input format (`title`, `text`). It is input data only — the texts are
public domain — and lets anyone with an inventory check their installation
end to end via *Load .txt / .csv …*.

---

## Text normalisation

Two steps, implemented in `core/gpdi.py: normalize()`:

1. **Character filtering** — only CJK ideographs are kept; punctuation, digits,
   latin characters and whitespace are dropped.
2. **Glyph normalisation** — any character the inventory does *not* contain is
   mapped to its standard form through `data/variant_map.tsv`
   (traditional → simplified and other established one-to-one mappings,
   generated from `zhconv` by `tools/build_variant_map.py`).
   Characters already in the inventory are left exactly as written.

Known limitation: normalisation is applied character by character, so
context-sensitive merges are not resolved.

---

## Building from source

### Public build (what the release assets are made of)

```bat
build_windows_public.bat          REM Windows -> dist\GPDI-Analyzer-Windows-v1.0.0.zip
```

```bash
./build_macos.sh --public         # macOS  -> GPDI-Analyzer-macOS-v1.0.0-public.zip
```

These stage only `variant_map.tsv` — no inventory, no reference corpus — and
then run `tools/audit_leak.py --public` over the resulting archive, which fails
the build if either reappears.

### Private build (on a machine that holds the inventory)

```bat
build_windows.bat
```

```bash
./build_macos.sh
```

These pack the inventory into `build_data/char_inventory.bin` with
`tools/pack_inventory.py` and include the reference corpus, so the build
reproduces the study's own figures. Such a build is **not** for distribution:
the packed blob is compressed, not encrypted, and anyone holding it can recover
the table. That is precisely why the public build omits it altogether instead
of relying on the packing.

Self-check a frozen bundle (writes `%TEMP%\gpdi_selftest.txt`):

```bat
dist\GPDI-Analyzer\GPDI-Analyzer.exe --selftest
```

### macOS

PyInstaller builds are **platform-specific** — a macOS `.app` can only be
produced on a Mac. Copy the repository to the Mac and run the script above.
The bundle is ad-hoc signed at best, so Gatekeeper will refuse the first launch
until the user runs:

```bash
xattr -dr com.apple.quarantine GPDI-Analyzer.app
```

(Apple Silicon and Intel Macs each need their own build; add
`--target-arch universal2` to the PyInstaller call for a combined binary.)

---

## Tests

The suite in `tests/` validates the implementation against the reference
corpus. It therefore needs both withheld assets and reports `SKIPPED` in a
public clone:

```bat
.venv\Scripts\python tests\regression_82.py
.venv\Scripts\python tests\test_bands.py
.venv\Scripts\python tests\test_coefficients.py
.venv\Scripts\python tests\test_inventory_pack.py
.venv\Scripts\python tests\gui_smoke.py
```

---

## Citation

If you use this tool, please cite the associated study:

> [Author(s)]. (2026). *Graded Poetry Difficulty Index: character-level
> profiling of classical Chinese poetry for International Chinese Language
> Education*. **[journal / status — to be completed]**

Software citation:

> GPDI Analyzer (Version 1.0.0) [Computer software].
> https://github.com/fancy61333/GPDI-Analyzer

---

## Licence and scope

The application is released for research use under the MIT licence
(`LICENSE`). The graded character inventory is **not** covered by that licence:
it is not distributed with the software in any form, and the MIT grant applies
to the code only.

**Disclaimer (displayed in the application interface):**

> GPDI measures character-level textual demand. It does not estimate overall
> readability, literary difficulty, or individual learner proficiency.
