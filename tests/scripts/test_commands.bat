@echo off
REM DMLClean v0.1.0 - Comprehensive Command Test Suite
REM Tests all 90+ commands + 10+ edge cases with detailed error reporting

setlocal enabledelayedexpansion

REM Configuration
set TIMEOUT_SECONDS=120
set OUTPUT_DIR=%TEMP%\dmlclean-test-%RANDOM%
set LOG_FILE=%OUTPUT_DIR%\test_results.txt
set JSON_FILE=%OUTPUT_DIR%\test_results.json

REM Counters
set /a TOTAL=0
set /a PASS=0
set /a FAIL=0

REM Create output directory
mkdir "%OUTPUT_DIR%" 2>nul

REM Initialize log
echo DMLClean v0.1.0 - Command Test Suite > "%LOG_FILE%"
echo Started: %DATE% %TIME% >> "%LOG_FILE%"
echo ================================================ >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM JSON array start
echo [ > "%JSON_FILE%"

set FIRST_ENTRY=1

REM Color codes
set GREEN=[32m
set RED=[31m
set YELLOW=[33m
set BLUE=[34m
set NC=[0m

REM Function to test command
:test_command
set CMD=%~1
set DESC=%~2

set /a TOTAL+=1

echo Testing [%TOTAL%]: %DESC%
echo   Command: %CMD% >> "%LOG_FILE%"

REM Run command with timeout
set START_TIME=%TIME%
set EXIT_CODE=
set OUTPUT=

for /f "delims=" %%i in ('timeout /t %TIMEOUT_SECONDS% /nobreak ^& %CMD% 2^>^&1') do set "OUTPUT=!OUTPUT! %%i"
set EXIT_CODE=%ERRORLEVEL%

set END_TIME=%TIME%

if %EXIT_CODE% EQU 0 (
    echo   %GREEN%✅ PASS%NC%
    set /a PASS+=1
    set RESULT=PASS
) else (
    echo   %RED%❌ FAIL (exit code: %EXIT_CODE%)%NC%
    echo   ERROR: %OUTPUT% >> "%LOG_FILE%"
    set /a FAIL+=1
    set RESULT=FAIL
)

echo   Exit Code: %EXIT_CODE% >> "%LOG_FILE%"
echo   Output: %OUTPUT:~0,200% >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM Write JSON entry
if %FIRST_ENTRY% EQU 0 (
    echo , >> "%JSON_FILE%"
)
set FIRST_ENTRY=0

echo   { >> "%JSON_FILE%"
echo     "id": %TOTAL%, >> "%JSON_FILE%"
echo     "description": "%DESC%", >> "%JSON_FILE%"
echo     "command": "%CMD%", >> "%JSON_FILE%"
echo     "exit_code": %EXIT_CODE%, >> "%JSON_FILE%"
echo     "result": "%RESULT%", >> "%JSON_FILE%"
echo     "start_time": "%START_TIME%", >> "%JSON_FILE%"
echo     "end_time": "%END_TIME%" >> "%JSON_FILE%"
echo   } >> "%JSON_FILE%"

goto :eof

REM ============================================================================
REM MAIN TEST EXECUTION
REM ============================================================================

echo.
echo ================================================================
echo   DMLClean v0.1.0 - Full Command Suite Test
echo   Testing 90+ commands + 10+ edge cases
echo   Output: %OUTPUT_DIR%
echo ================================================================
echo.

REM SECTION 1: Version & Help
echo [SECTION 1/16] Version ^& Help Commands
call :test_command "python -m dmlclean --version" "Show version (--version)"
call :test_command "python -m dmlclean version" "Version command"
call :test_command "python -m dmlclean --help" "Main help"
call :test_command "python -m dmlclean scan --help" "Scan help"
call :test_command "python -m dmlclean clean --help" "Clean help"
call :test_command "python -m dmlclean --config" "Config option help"
call :test_command "python -m dmlclean --verbose" "Verbose mode"
call :test_command "python -m dmlclean --quiet" "Quiet mode"

REM SECTION 2: Scan Commands
echo.
echo [SECTION 2/16] Scan Commands
call :test_command "python -m dmlclean scan" "Basic scan (fast mode)"
call :test_command "python -m dmlclean scan --mode fast" "Scan fast mode"
call :test_command "python -m dmlclean scan --mode deep" "Scan deep mode"
call :test_command "python -m dmlclean scan --json" "Scan with JSON output"
call :test_command "python -m dmlclean scan --categories browser" "Scan specific category"
call :test_command "python -m dmlclean scan --categories browser,dev_python" "Scan multiple categories"
call :test_command "python -m dmlclean scan --path C:\Windows\Temp" "Scan specific path"
call :test_command "python -m dmlclean scan --follow-symlinks" "Scan with symlinks"
call :test_command "python -m dmlclean scan --max-depth 2" "Scan with depth limit"

REM SECTION 3: Clean Commands
echo.
echo [SECTION 3/16] Clean Commands
call :test_command "python -m dmlclean clean --mode dry-run" "Clean dry-run (default)"
call :test_command "python -m dmlclean clean --mode trash --force" "Clean trash mode (forced)"
call :test_command "python -m dmlclean clean --profile developer --mode dry-run" "Clean with profile"
call :test_command "python -m dmlclean clean --categories browser --mode dry-run" "Clean specific category"
call :test_command "python -m dmlclean clean --min-age-days 7 --mode dry-run" "Clean with age filter"
call :test_command "python -m dmlclean clean --min-size-mb 10 --mode dry-run" "Clean with size filter"
call :test_command "python -m dmlclean clean --profile designer --mode trash --force" "Clean designer profile"
call :test_command "python -m dmlclean clean --profile system-admin --mode dry-run" "Clean system-admin profile"

REM SECTION 4: Protect Commands
echo.
echo [SECTION 4/16] Protect Commands
call :test_command "python -m dmlclean protect list" "List protected paths"
call :test_command "python -m dmlclean protect check C:\Windows" "Check if path protected"
call :test_command "python -m dmlclean protect check %TEMP%" "Check temp path protected"

REM SECTION 5: History Commands
echo.
echo [SECTION 5/16] History Commands
call :test_command "python -m dmlclean history list" "List history"
call :test_command "python -m dmlclean history list --limit 10" "List history with limit"
call :test_command "python -m dmlclean history list --json" "List history JSON"

REM SECTION 6: Schedule Commands
echo.
echo [SECTION 6/16] Schedule Commands
call :test_command "python -m dmlclean schedule list" "List schedules"
call :test_command "python -m dmlclean schedule list --json" "List schedules JSON"

REM SECTION 7: Config Commands
echo.
echo [SECTION 7/16] Config Commands
call :test_command "python -m dmlclean config show" "Show config"
call :test_command "python -m dmlclean config show --json" "Show config JSON"
call :test_command "python -m dmlclean config validate" "Validate config"

REM SECTION 8: Report Commands
echo.
echo [SECTION 8/16] Report Commands
call :test_command "python -m dmlclean report last" "Show last report"
call :test_command "python -m dmlclean report last --json" "Last report JSON"

REM SECTION 9: Trends Commands
echo.
echo [SECTION 9/16] Trends Commands
call :test_command "python -m dmlclean trends" "Show trends (default)"
call :test_command "python -m dmlclean trends --since 7" "Trends last 7 days"
call :test_command "python -m dmlclean trends --days 30" "Trends last 30 days (--days)"
call :test_command "python -m dmlclean trends --json" "Trends JSON"

REM SECTION 10: Profile Commands
echo.
echo [SECTION 10/16] Profile Commands
call :test_command "python -m dmlclean profile list" "List profiles"
call :test_command "python -m dmlclean profile show developer" "Show developer profile"
call :test_command "python -m dmlclean profile show designer" "Show designer profile"
call :test_command "python -m dmlclean profile show system-admin" "Show system-admin profile"
call :test_command "python -m dmlclean profile show gamer" "Show gamer profile"
call :test_command "python -m dmlclean profile show minimal" "Show minimal profile"

REM SECTION 11: Plugin Commands
echo.
echo [SECTION 11/16] Plugin Commands
call :test_command "python -m dmlclean plugin list" "List plugins"
call :test_command "python -m dmlclean plugin list --json" "List plugins JSON"
call :test_command "python -m dmlclean plugin info browser" "Plugin info (browser)"
call :test_command "python -m dmlclean plugin info dev_python" "Plugin info (dev_python)"
call :test_command "python -m dmlclean plugin info system_junk" "Plugin info (system_junk)"

REM SECTION 12: Storage Commands
echo.
echo [SECTION 12/16] Storage Commands
call :test_command "python -m dmlclean storage path" "Show storage path"
call :test_command "python -m dmlclean storage path --location base" "Show base location"
call :test_command "python -m dmlclean storage path --location config" "Show config location"
call :test_command "python -m dmlclean storage path --location data" "Show data location"
call :test_command "python -m dmlclean storage path --location logs" "Show logs location"
call :test_command "python -m dmlclean storage path --location history" "Show history location"

REM SECTION 13: System Commands
echo.
echo [SECTION 13/16] System Commands
call :test_command "python -m dmlclean system info" "System information"
call :test_command "python -m dmlclean system version" "System version"
call :test_command "python -m dmlclean system self-update --check" "Check for updates"

REM SECTION 14: Doctor Commands
echo.
echo [SECTION 14/16] Doctor Commands
call :test_command "python -m dmlclean doctor" "System diagnostics"
call :test_command "python -m dmlclean doctor --json" "Doctor JSON output"

REM SECTION 15: Nested & Complex Commands
echo.
echo [SECTION 15/16] Nested ^& Complex Commands
call :test_command "python -m dmlclean scan --mode deep --categories browser,dev_python,system_junk --json" "Complex scan"
call :test_command "python -m dmlclean clean --profile developer --mode dry-run --categories browser --min-age-days 1" "Complex clean"
call :test_command "python -m dmlclean scan --mode fast --path %TEMP% --path C:\Windows\Temp --json" "Multi-path scan"
call :test_command "python -m dmlclean clean --mode trash --force --profile system-admin --min-size-mb 5" "Complex trash"
call :test_command "python -m dmlclean trends --since 30 --json" "Trends with JSON"
call :test_command "python -m dmlclean report last --format json" "Report with format"
call :test_command "python -m dmlclean doctor --verbose" "Doctor verbose"
call :test_command "python -m dmlclean config show --json" "Config JSON verbose"
call :test_command "python -m dmlclean plugin list --all" "Plugin list all"
call :test_command "python -m dmlclean history list --limit 50 --json" "History large limit"
call :test_command "python -m dmlclean protect list --json" "Protect list JSON"
call :test_command "python -m dmlclean schedule list --all" "Schedule list all"

REM SECTION 16: Edge Cases & Error Handling
echo.
echo [SECTION 16/16] Edge Cases ^& Error Handling
call :test_command "python -m dmlclean scan --mode invalid" "Invalid scan mode (should fail)"
call :test_command "python -m dmlclean clean --mode invalid" "Invalid clean mode (should fail)"
call :test_command "python -m dmlclean clean --min-age-days -1" "Negative age (should fail)"
call :test_command "python -m dmlclean scan --categories nonexistent_category" "Invalid category (should fail)"
call :test_command "python -m dmlclean profile show invalid_profile" "Invalid profile (should fail)"
call :test_command "python -m dmlclean plugin info nonexistent_plugin" "Invalid plugin (should fail)"
call :test_command "python -m dmlclean storage path --location invalid" "Invalid location (should fail)"
call :test_command "python -m dmlclean trends --since -5" "Negative days (should fail)"
call :test_command "python -m dmlclean history list --limit 0" "Zero limit (should fail)"
call :test_command "python -m dmlclean history list --limit 9999" "Extreme limit (should fail)"
call :test_command "python -m dmlclean scan --max-depth -1" "Negative depth (should fail)"
call :test_command "python -m dmlclean clean --min-size-mb -100" "Negative size (should fail)"

REM Close JSON array
echo ] >> "%JSON_FILE%"

REM Print summary
echo.
echo ================================================================
echo   TEST SUMMARY
echo ================================================================
echo   Total Commands Tested: %TOTAL%
echo   Passed: %PASS%
echo   Failed: %FAIL%

if %TOTAL% GTR 0 (
    set /a PASS_RATE=%PASS% * 100 / %TOTAL%
    echo   Pass Rate: %PASS_RATE%%
)

echo.
echo   Results saved to:
echo   - Text Log: %LOG_FILE%
echo   - JSON Report: %JSON_FILE%
echo.

if %FAIL% EQU 0 (
    echo [32m🎉 SUCCESS: 100%% PASS RATE ACHIEVED![0m
    echo    All %TOTAL% commands executed successfully!
    exit /b 0
) else (
    echo [31m❌ FAILURE: %FAIL% commands failed[0m
    echo    Review detailed logs in: %OUTPUT_DIR%
    exit /b 1
)
