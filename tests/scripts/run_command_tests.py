#!/usr/bin/env python3
"""
DMLClean v0.1.0 - Comprehensive Command Test Suite

Tests all 90+ commands + 10+ edge cases with:
- 2-minute timeout per command
- Detailed error reporting
- JSON + TXT output
- Proper exit code handling
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class TestResult:
    """Single test result."""

    id: int
    description: str
    command: str
    exit_code: int | None = None
    output: str = ""
    error: str = ""
    duration_seconds: float = 0.0
    passed: bool = False
    timed_out: bool = False


@dataclass
class TestReport:
    """Complete test report."""

    started_at: str = ""
    completed_at: str = ""
    total: int = 0
    passed: int = 0
    failed: int = 0
    pass_rate: float = 0.0
    results: list[TestResult] = field(default_factory=list)
    failures: list[TestResult] = field(default_factory=list)


# ============================================================================
# TEST COMMANDS
# ============================================================================

TEST_COMMANDS = [
    # SECTION 1: Version & Help (8 commands)
    ("python -m dmlclean --version", "Show version (--version)"),
    ("python -m dmlclean version", "Version command"),
    ("python -m dmlclean --help", "Main help"),
    ("python -m dmlclean scan --help", "Scan help"),
    ("python -m dmlclean clean --help", "Clean help"),
    ("python -m dmlclean --config config.toml", "Config option with value"),
    ("python -m dmlclean --verbose scan", "Verbose mode"),
    ("python -m dmlclean --quiet scan", "Quiet mode"),
    # SECTION 2: Scan Commands (9 commands)
    ("python -m dmlclean scan", "Basic scan (fast mode)"),
    ("python -m dmlclean scan --mode fast", "Scan fast mode"),
    ("python -m dmlclean scan --mode deep", "Scan deep mode"),
    ("python -m dmlclean scan --json", "Scan with JSON output"),
    ("python -m dmlclean scan --categories browser", "Scan specific category"),
    ("python -m dmlclean scan --categories browser,dev_python", "Scan multiple categories"),
    (f"python -m dmlclean scan --path {tempfile.gettempdir()}", "Scan specific path"),
    ("python -m dmlclean scan --quiet", "Scan quiet mode"),
    ("python -m dmlclean scan --mode deep --json", "Scan deep JSON"),
    # SECTION 3: Clean Commands (8 commands)
    ("python -m dmlclean clean --mode dry-run", "Clean dry-run (default)"),
    ("python -m dmlclean clean --mode trash --force", "Clean trash mode (forced)"),
    ("python -m dmlclean clean --profile developer --mode dry-run", "Clean with profile"),
    ("python -m dmlclean clean --categories browser --mode dry-run", "Clean specific category"),
    ("python -m dmlclean clean --min-age 7 --mode dry-run", "Clean with age filter"),
    ("python -m dmlclean clean --min-size 10 --mode dry-run", "Clean with size filter"),
    ("python -m dmlclean clean --profile designer --mode trash --force", "Clean designer profile"),
    (
        "python -m dmlclean clean --profile system-admin --mode dry-run",
        "Clean system-admin profile",
    ),
    # SECTION 4: Protect Commands (3 commands)
    ("python -m dmlclean protect list", "List protected paths"),
    (
        f"python -m dmlclean protect check {Path('C:\\Windows').as_posix()}",
        "Check if path protected",
    ),
    (f"python -m dmlclean protect check {tempfile.gettempdir()}", "Check temp path protected"),
    # SECTION 5: History Commands (3 commands)
    ("python -m dmlclean history list", "List history"),
    ("python -m dmlclean history list --limit 10", "List history with limit"),
    ("python -m dmlclean history list --json", "List history JSON"),
    # SECTION 6: Schedule Commands (2 commands)
    ("python -m dmlclean schedule list", "List schedules"),
    ("python -m dmlclean schedule list --json", "List schedules JSON"),
    # SECTION 7: Config Commands (3 commands)
    ("python -m dmlclean config show", "Show config"),
    ("python -m dmlclean config show --json", "Show config JSON"),
    ("python -m dmlclean config validate", "Validate config"),
    # SECTION 8: Report Commands (3 commands)
    ("python -m dmlclean report last", "Show last report"),
    ("python -m dmlclean report last --json", "Last report JSON"),
    ("python -m dmlclean report export json /tmp/report", "Report export"),
    # SECTION 9: Trends Commands (4 commands)
    ("python -m dmlclean trends", "Show trends (default)"),
    ("python -m dmlclean trends --since 7", "Trends last 7 days"),
    ("python -m dmlclean trends --days 30", "Trends last 30 days (--days)"),
    ("python -m dmlclean trends --json", "Trends JSON"),
    # SECTION 10: Profile Commands (6 commands)
    ("python -m dmlclean profile list", "List profiles"),
    ("python -m dmlclean profile show developer", "Show developer profile"),
    ("python -m dmlclean profile show designer", "Show designer profile"),
    ("python -m dmlclean profile show system-admin", "Show system-admin profile"),
    ("python -m dmlclean profile show gamer", "Show gamer profile"),
    ("python -m dmlclean profile show minimal", "Show minimal profile"),
    # SECTION 11: Plugin Commands (5 commands)
    ("python -m dmlclean plugin list", "List plugins"),
    ("python -m dmlclean plugin list --json", "List plugins JSON"),
    ("python -m dmlclean plugin info browser", "Plugin info (browser)"),
    ("python -m dmlclean plugin info dev_python", "Plugin info (dev_python)"),
    ("python -m dmlclean plugin info system_junk", "Plugin info (system_junk)"),
    # SECTION 12: Storage Commands (6 commands)
    ("python -m dmlclean storage path", "Show storage path (default)"),
    ("python -m dmlclean storage path base", "Show base location"),
    ("python -m dmlclean storage path config", "Show config location"),
    ("python -m dmlclean storage path data", "Show data location"),
    ("python -m dmlclean storage path logs", "Show logs location"),
    ("python -m dmlclean storage path history", "Show history location"),
    # SECTION 13: System Commands (3 commands)
    ("python -m dmlclean system info", "System information"),
    ("python -m dmlclean system version", "System version"),
    ("python -m dmlclean system self-update --check", "Check for updates"),
    # SECTION 14: Doctor Commands (2 commands)
    ("python -m dmlclean doctor", "System diagnostics"),
    ("python -m dmlclean doctor --json", "Doctor JSON output"),
    # SECTION 15: Nested & Complex Commands (12 commands)
    (
        "python -m dmlclean scan --mode deep --categories browser,dev_python,system_junk --json",
        "Complex scan",
    ),
    (
        "python -m dmlclean clean --profile developer --mode dry-run --categories browser --min-age 1",
        "Complex clean",
    ),
    (
        f"python -m dmlclean scan --mode fast --path {tempfile.gettempdir()} --path C:\\Windows\\Temp --json",
        "Multi-path scan",
    ),
    (
        "python -m dmlclean clean --mode trash --force --profile system-admin --min-size 5",
        "Complex trash",
    ),
    ("python -m dmlclean trends --since 30 --json", "Trends with JSON"),
    ("python -m dmlclean report export json /tmp/report", "Report export"),
    ("python -m dmlclean doctor", "Doctor (no verbose option)"),
    ("python -m dmlclean config show --json", "Config JSON"),
    ("python -m dmlclean plugin list", "Plugin list (no --all option)"),
    ("python -m dmlclean history list --limit 50 --json", "History large limit"),
    ("python -m dmlclean protect list", "Protect list (no JSON option)"),
    ("python -m dmlclean schedule list", "Schedule list (no --all option)"),
    # SECTION 16: Edge Cases & Error Handling (12 commands)
    ("python -m dmlclean scan --mode invalid", "Invalid scan mode (should fail)"),
    ("python -m dmlclean clean --mode invalid", "Invalid clean mode (should fail)"),
    ("python -m dmlclean clean --min-age -1", "Negative age (should fail)"),
    ("python -m dmlclean scan --categories nonexistent_category", "Invalid category (should fail)"),
    ("python -m dmlclean profile show invalid_profile", "Invalid profile (should fail)"),
    ("python -m dmlclean plugin info nonexistent_plugin", "Invalid plugin (should fail)"),
    ("python -m dmlclean storage path invalid", "Invalid location (should fail)"),
    ("python -m dmlclean trends --since -5", "Negative days (should fail)"),
    ("python -m dmlclean history list --limit 0", "Zero limit (should fail)"),
    ("python -m dmlclean history list --limit 9999", "Extreme limit (should fail)"),
    ("python -m dmlclean clean --min-size -100", "Negative size (should fail)"),
    ("python -m dmlclean trends --days -10", "Negative days via --days (should fail)"),
]


def run_test(command: str, description: str, timeout_seconds: int = 120) -> TestResult:
    """Run a single test command."""
    result = TestResult(
        id=0,
        description=description,
        command=command,
    )

    start_time = time.time()

    try:
        # Parse command into list for subprocess
        import shlex

        cmd_list = shlex.split(command) if " " in command else [command]

        # Ensure python is first
        if cmd_list[0] == "python":
            cmd_list[0] = sys.executable

        proc = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=Path(__file__).parent.parent.parent,
            encoding="utf-8",
            errors="replace",
        )
        result.exit_code = proc.returncode
        result.output = proc.stdout[:2000]  # Limit output
        result.error = proc.stderr[:2000]
        result.passed = proc.returncode == 0

    except subprocess.TimeoutExpired:
        result.timed_out = True
        result.error = f"TIMEOUT: Command exceeded {timeout_seconds} seconds"
        result.passed = False

    except Exception as e:
        result.error = f"ERROR: {e!s}"
        result.passed = False

    result.duration_seconds = time.time() - start_time
    return result


def print_colored(text: str, color: str = "") -> None:
    """Print colored text to console."""
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "reset": "\033[0m",
    }
    colors.get(color, "")
    colors["reset"]
    # Replace emoji with ASCII for Windows compatibility
    text = text.replace("✅", "[PASS]").replace("❌", "[FAIL]").replace("🎉", "[SUCCESS]")


def main() -> int:
    """Main test runner."""
    # Create output directory
    output_dir = (
        Path(tempfile.gettempdir()) / f"dmlclean-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    txt_log = output_dir / "test_results.txt"
    json_report = output_dir / "test_results.json"

    # Initialize report
    report = TestReport(
        started_at=datetime.now().isoformat(),
    )

    # Print header
    print_colored("=" * 70, "blue")
    print_colored("  DMLClean v0.1.0 - Full Command Suite Test", "blue")
    print_colored(f"  Testing {len(TEST_COMMANDS)} commands", "blue")
    print_colored(f"  Output: {output_dir}", "blue")
    print_colored("=" * 70, "blue")

    # Open log file
    with open(txt_log, "w", encoding="utf-8") as log_file:
        log_file.write("DMLClean v0.1.0 - Command Test Suite\n")
        log_file.write(f"Started: {report.started_at}\n")
        log_file.write("=" * 70 + "\n\n")

        # Run tests
        for idx, (command, description) in enumerate(TEST_COMMANDS, 1):
            log_file.write(f"[{idx}] {description}\n")
            log_file.write(f"    Command: {command}\n")

            result = run_test(command, description)
            result.id = idx
            report.results.append(result)
            report.total += 1

            if result.passed:
                report.passed += 1
                print_colored("✅ PASS", "green")
                log_file.write(f"    ✅ PASS (exit: {result.exit_code})\n")
            else:
                report.failed += 1
                report.failures.append(result)
                print_colored(f"❌ FAIL (exit: {result.exit_code})", "red")
                log_file.write(f"    ❌ FAIL (exit: {result.exit_code})\n")
                if result.timed_out:
                    log_file.write(f"    TIMEOUT: {result.error}\n")
                else:
                    log_file.write(f"    Output: {result.output[:200]}\n")
                    log_file.write(f"    Error: {result.error[:200]}\n")

            log_file.write(f"    Duration: {result.duration_seconds:.2f}s\n\n")

        # Calculate pass rate
        if report.total > 0:
            report.pass_rate = (report.passed / report.total) * 100

        report.completed_at = datetime.now().isoformat()

        # Write summary to log
        log_file.write("\n" + "=" * 70 + "\n")
        log_file.write("TEST SUMMARY\n")
        log_file.write("=" * 70 + "\n")
        log_file.write(f"Total: {report.total}\n")
        log_file.write(f"Passed: {report.passed}\n")
        log_file.write(f"Failed: {report.failed}\n")
        log_file.write(f"Pass Rate: {report.pass_rate:.1f}%\n")
        log_file.write(f"Completed: {report.completed_at}\n")

        if report.failures:
            log_file.write("\n" + "=" * 70 + "\n")
            log_file.write("FAILED COMMANDS\n")
            log_file.write("=" * 70 + "\n")
            for failure in report.failures:
                log_file.write(f"\n[{failure.id}] {failure.description}\n")
                log_file.write(f"    Command: {failure.command}\n")
                log_file.write(f"    Exit Code: {failure.exit_code}\n")
                log_file.write(f"    Error: {failure.error[:500]}\n")

    # Write JSON report
    with open(json_report, "w", encoding="utf-8") as json_file:
        json.dump(
            {
                "started_at": report.started_at,
                "completed_at": report.completed_at,
                "total": report.total,
                "passed": report.passed,
                "failed": report.failed,
                "pass_rate": report.pass_rate,
                "results": [
                    {
                        "id": r.id,
                        "description": r.description,
                        "command": r.command,
                        "exit_code": r.exit_code,
                        "output": r.output,
                        "error": r.error,
                        "duration_seconds": r.duration_seconds,
                        "passed": r.passed,
                        "timed_out": r.timed_out,
                    }
                    for r in report.results
                ],
                "failures": [
                    {
                        "id": f.id,
                        "description": f.description,
                        "command": f.command,
                        "exit_code": f.exit_code,
                        "error": f.error,
                        "duration_seconds": f.duration_seconds,
                    }
                    for f in report.failures
                ],
            },
            json_file,
            indent=2,
        )

    # Print summary
    print_colored("=" * 70, "blue")
    print_colored("TEST SUMMARY", "blue")
    print_colored("=" * 70, "blue")
    print_colored(f"✅ Passed: {report.passed}", "green")
    print_colored(f"❌ Failed: {report.failed}", "red")

    if report.failed == 0:
        print_colored("🎉 SUCCESS: 100% PASS RATE ACHIEVED!", "green")
        print_colored(f"   All {report.total} commands executed successfully!", "green")
        return 0
    else:
        print_colored(f"❌ FAILURE: {report.failed} commands failed", "red")
        print_colored("   Review detailed logs for debugging", "yellow")
        print_colored("Failed Commands:", "red")
        for failure in report.failures[:10]:  # Show first 10 failures
            pass
        if len(report.failures) > 10:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
