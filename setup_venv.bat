@echo off
setlocal

set ROOT_DIR=%~dp0
set VENV_DIR=%ROOT_DIR%.venv

where python >nul 2>nul
if errorlevel 1 (
    echo python was not found. Please install Python and add it to PATH.
    exit /b 1
)

echo [1/4] Creating virtual environment: %VENV_DIR%
python -m venv "%VENV_DIR%"
if errorlevel 1 exit /b 1

echo [2/4] Activating virtual environment
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 exit /b 1

echo [3/4] Upgrading pip
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1

echo [4/4] Installing dependencies
pip install -r "%ROOT_DIR%requirements.txt"
if errorlevel 1 exit /b 1

echo Done. The virtual environment is active in this window.
endlocal
