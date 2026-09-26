@echo off
REM ---------------------------------------------------------------
REM GPDI Analyzer - public Windows build (distributable)
REM
REM Produces dist\GPDI-Analyzer-Windows-v1.0.0.zip, which carries:
REM     the application, the glyph-normalisation table, the source
REM It deliberately carries:
REM     NO graded character inventory  (third-party research asset)
REM     NO reference corpus            (per-poem figures unpublished)
REM
REM The application therefore starts with no inventory loaded and the
REM user supplies one they are entitled to use - see README,
REM "What is not included".
REM
REM For a build that carries the inventory, use build_windows.bat.
REM ---------------------------------------------------------------

setlocal

IF NOT EXIST ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Installing build dependencies...
".venv\Scripts\python.exe" -m pip install PySide6 PyInstaller

echo Staging public data files (no inventory, no reference corpus)...
".venv\Scripts\python.exe" tools\pack_inventory.py --public
IF ERRORLEVEL 1 (
    echo BUILD FAILED: could not stage the data files
    exit /b 1
)

echo Building...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --windowed ^
    --name "GPDI-Analyzer" ^
    --add-data "build_data;data" ^
    --add-data "core;core" ^
    --hidden-import "gpdi" ^
    --distpath "dist_public" ^
    --workpath "build" ^
    --specpath "." ^
    "gui\app.py"

IF ERRORLEVEL 1 (
    echo BUILD FAILED
    exit /b 1
)

echo.
echo Build succeeded.
echo Self-checking the bundle...
"dist_public\GPDI-Analyzer\GPDI-Analyzer.exe" --selftest
type "%TEMP%\gpdi_selftest.txt"

IF NOT EXIST "dist" mkdir "dist"

echo Packaging...
".venv\Scripts\python.exe" -c "import shutil; shutil.make_archive('dist/GPDI-Analyzer-Windows-v1.0.0', 'zip', 'dist_public/GPDI-Analyzer')"
IF ERRORLEVEL 1 (
    echo PACKAGING FAILED
    exit /b 1
)

echo Auditing the archive against the public profile...
".venv\Scripts\python.exe" tools\audit_leak.py --public "dist\GPDI-Analyzer-Windows-v1.0.0.zip"
IF ERRORLEVEL 1 (
    echo AUDIT FAILED: the archive carries something it must not
    exit /b 1
)

echo.
echo Done: dist\GPDI-Analyzer-Windows-v1.0.0.zip

endlocal
