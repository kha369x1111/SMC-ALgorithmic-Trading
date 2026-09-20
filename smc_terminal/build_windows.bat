@echo off
REM ==============================================================================
REM SMC / ICT Algorithmic Trading Terminal - Windows Desktop Build Script
REM Builds standalone SMC-Trading-Terminal.exe via PyInstaller
REM Credentials and secrets are strictly excluded from the executable bundle.
REM ==============================================================================

echo [1/4] Checking Python environment...
python --version
if errorlevel 1 (
    echo Python 3.10+ is required. Please ensure python is in PATH.
    pause
    exit /b 1
)

echo [2/4] Installing / Verifying requirements...
pip install -r requirements.txt

echo [3/4] Running unit test safety suite before packaging...
python -m unittest discover tests
if errorlevel 1 (
    echo UNIT TESTS FAILED! Aborting packaging to guarantee execution safety.
    pause
    exit /b 1
)

echo [4/4] Packaging Windows Desktop Executable with PyInstaller...
pyinstaller --noconfirm --onedir --windowed ^
    --name "SMC-Trading-Terminal" ^
    --add-data "config.yaml;." ^
    --hidden-import "pydantic" ^
    --hidden-import "yaml" ^
    --hidden-import "sqlalchemy" ^
    main.py

echo ==============================================================================
echo Build Completed Successfully!
echo Output executable located at: dist\SMC-Trading-Terminal\SMC-Trading-Terminal.exe
echo ==============================================================================
pause
