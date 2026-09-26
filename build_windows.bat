@echo off
REM ---------------------------------------------------------------
REM GPDI Analyzer - Windows build script
REM Run from the project root (the folder containing this file).
REM Produces: dist\GPDI-Analyzer\GPDI-Analyzer.exe
REM ---------------------------------------------------------------

setlocal

IF NOT EXIST ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Installing build dependencies...
".venv\Scripts\python.exe" -m pip install PySide6 PyInstaller

REM The graded inventory is packed into a compressed blob and staged in
REM build_data\ together with the public data files. Pointing PyInstaller at
REM data\ would copy the raw CSV into the bundle, which is exactly what must
REM not happen - see tools\pack_inventory.py.
echo Staging data files...
".venv\Scripts\python.exe" tools\pack_inventory.py
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
    --distpath "dist" ^
    --workpath "build" ^
    --specpath "." ^
    "gui\app.py"

IF ERRORLEVEL 1 (
    echo BUILD FAILED
    exit /b 1
)

echo.
echo Build succeeded: dist\GPDI-Analyzer\GPDI-Analyzer.exe
echo Self-checking the bundle...
"dist\GPDI-Analyzer\GPDI-Analyzer.exe" --selftest
type "%TEMP%\gpdi_selftest.txt"

endlocal
