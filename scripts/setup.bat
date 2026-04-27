@echo off
REM DMLClean Setup Script for Windows
REM This script sets up the development environment

setlocal enabledelayedexpansion

REM Colors for output (Windows 10+)
set "BLUE=[94m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "NC=[0m"

REM Helper functions
:log_info
echo %BLUE%[INFO]%NC% %1
goto :eof

:log_success
echo %GREEN%[SUCCESS]%NC% %1
goto :eof

:log_warning
echo %YELLOW%[WARNING]%NC% %1
goto :eof

:log_error
echo %RED%[ERROR]%NC% %1
goto :eof

REM Check Python version
:check_python
call :log_info "Checking Python version..."

where python >nul 2>&1
if %errorlevel% neq 0 (
    call :log_error "Python is not installed. Please install Python 3.11 or higher."
    exit /b 1
)

python --version > temp_version.txt
set /p PYTHON_VERSION=<temp_version.txt
del temp_version.txt

for /f "tokens=2" %%i in ("%PYTHON_VERSION%") do set "VERSION=%%i"
for /f "tokens=1,2 delims=." %%a in ("%VERSION%") do (
    set "PYTHON_MAJOR=%%a"
    set "PYTHON_MINOR=%%b"
)

if %PYTHON_MAJOR% lss 3 (
    call :log_error "Python 3.11 or higher is required. Found: %PYTHON_VERSION%"
    exit /b 1
)
if %PYTHON_MAJOR% equ 3 if %PYTHON_MINOR% lss 11 (
    call :log_error "Python 3.11 or higher is required. Found: %PYTHON_VERSION%"
    exit /b 1
)

call :log_success "Python %PYTHON_VERSION% found"
goto :eof

REM Create virtual environment
:create_venv
call :log_info "Creating virtual environment..."

if exist ".venv" (
    call :log_warning "Virtual environment already exists. Removing..."
    rmdir /s /q .venv
)

python -m venv .venv
call :log_success "Virtual environment created"
goto :eof

REM Activate virtual environment
:activate_venv
call :log_info "Activating virtual environment..."
call .venv\Scripts\activate.bat
call :log_success "Virtual environment activated"
goto :eof

REM Install dependencies
:install_deps
call :log_info "Upgrading pip..."
python -m pip install --upgrade pip

call :log_info "Installing development dependencies..."
python -m pip install -e ".[dev]"

call :log_success "Dependencies installed"
goto :eof

REM Install pre-commit hooks
:install_hooks
call :log_info "Installing pre-commit hooks..."
pre-commit install
call :log_success "Pre-commit hooks installed"
goto :eof

REM Main setup
echo ========================================
echo   DMLClean Setup Script
echo ========================================
echo.

call :check_python
call :create_venv
call :activate_venv
call :install_deps
call :install_hooks

echo.
call :log_success "Setup complete!"
echo.
echo To get started:
echo   1. Activate the virtual environment:
echo      .venv\Scripts\activate
echo.
echo   2. Run DMLClean:
echo      dmlclean --help
echo.
echo   3. Run tests:
echo      pytest tests/
echo.
echo   4. Scan for cleanable files:
echo      dmlclean scan
echo.

endlocal
