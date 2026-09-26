#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# GPDI Analyzer - macOS build script
#
# PyInstaller cannot cross-compile: a macOS build must be produced ON a Mac.
# Run this from the project root (the folder containing this file):
#
#   chmod +x build_macos.sh
#   ./build_macos.sh              # private build: carries the inventory
#   ./build_macos.sh --public     # the distributable build: carries neither the
#                                 # inventory nor the reference corpus
#
# Output : dist/GPDI-Analyzer.app
#          dist/GPDI-Analyzer-macOS-v1.0.0.zip          (private)
#          dist/GPDI-Analyzer-macOS-v1.0.0-public.zip   (public)
#
# Note   : the graded character inventory data/char_inventory.csv is NOT in the
#          repository (it is embedded, not published). Obtain it before a
#          private build, or build with --public. See tools/pack_inventory.py.
# -----------------------------------------------------------------------------
set -euo pipefail

VERSION="v1.0.0"
SUFFIX=""
PUBLIC=0
if [[ "${1:-}" == "--public" ]]; then PUBLIC=1; SUFFIX="-public"; fi
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "==> Creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate

echo "==> Installing build dependencies..."
python -m pip install --upgrade pip
python -m pip install PySide6 PyInstaller

echo "==> Staging data files..."
if [ "$PUBLIC" -eq 1 ]; then
    python tools/pack_inventory.py --public
else
    python tools/pack_inventory.py
fi

echo "==> Building .app bundle..."
python -m PyInstaller --noconfirm --clean --windowed \
    --name "GPDI-Analyzer" \
    --add-data "build_data:data" \
    --add-data "core:core" \
    --hidden-import "gpdi" \
    --distpath "dist" \
    --workpath "build" \
    --specpath "." \
    "gui/app.py"

echo "==> Self-checking the bundle..."
"dist/GPDI-Analyzer.app/Contents/MacOS/GPDI-Analyzer" --selftest
cat "${TMPDIR:-/tmp}/gpdi_selftest.txt"

echo "==> Packaging zip..."
cd dist
ditto -c -k --keepParent "GPDI-Analyzer.app" "../GPDI-Analyzer-macOS-${VERSION}${SUFFIX}.zip.tmp"
mv "../GPDI-Analyzer-macOS-${VERSION}${SUFFIX}.zip.tmp" "../GPDI-Analyzer-macOS-${VERSION}${SUFFIX}.zip"
cd ..

echo
echo "Done: GPDI-Analyzer-macOS-${VERSION}${SUFFIX}.zip"
echo
echo "Because the .app is not notarised, macOS Gatekeeper will block the first"
echo "launch. Whoever downloads it should run once:"
echo
echo "    xattr -dr com.apple.quarantine GPDI-Analyzer.app"
echo
