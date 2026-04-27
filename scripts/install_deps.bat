@echo off
REM DMLClean Development Dependencies Installer
REM Installs all required Python dependencies

echo ========================================
echo   DMLClean - Install Dependencies
echo ========================================
echo.

REM Check if Python is installed
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed
    exit /b 1
)

python --version > temp_version.txt
set /p PYTHON_VERSION=<temp_version.txt
del temp_version.txt

echo Found Python %PYTHON_VERSION%

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
python -m pip install -e ".[dev]"

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo To activate the virtual environment:
echo   .venv\Scripts\activate
echo.
echo Then run DMLClean:
echo   dmlclean --help
echo.

endlocal
