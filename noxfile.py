# Noxfile.py - Test automation for DMLClean
# https://nox.thea.codes/

import nox

# Python versions to test against
PYTHON_VERSIONS = ["3.11", "3.12", "3.13"]

# Default sessions to run
nox.options.sessions = ["lint", "type_check", "tests", "build"]


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run test suite with coverage."""
    session.install("-e", ".[dev]")
    session.run(
        "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--cov=src/dmlclean",
        "--cov-report=term-missing",
        "--cov-report=xml",
        "--cov-report=html",
        "--cov-fail-under=70",
        *session.posargs,
    )


@nox.session(python="3.12")
def lint(session: nox.Session) -> None:
    """Run linters (ruff)."""
    session.install("ruff")
    session.run("ruff", "check", "src/", "tests/")
    session.run("ruff", "format", "--check", "src/", "tests/")


@nox.session(python="3.12")
def type_check(session: nox.Session) -> None:
    """Run type checker (mypy)."""
    session.install("-e", ".[dev]")
    session.run("mypy", "--strict", "src/")


@nox.session(python="3.12")
def security(session: nox.Session) -> None:
    """Run security scanner (bandit)."""
    session.install("bandit")
    session.run("bandit", "-r", "src/", "-ll")


@nox.session(python="3.12")
def build(session: nox.Session) -> None:
    """Build package and binary."""
    session.install("hatch", "pyinstaller")
    session.run("hatch", "build", "--clean")
    session.run("pyinstaller", "dmlclean.spec", "--clean")


@nox.session(python="3.12")
def docs(session: nox.Session) -> None:
    """Build documentation."""
    session.install("mkdocs", "mkdocs-material")
    session.run("mkdocs", "build")


@nox.session(python="3.12")
def docs_serve(session: nox.Session) -> None:
    """Serve documentation locally."""
    session.install("mkdocs", "mkdocs-material")
    session.run("mkdocs", "serve")


@nox.session(python="3.12")
def pre_commit(session: nox.Session) -> None:
    """Run pre-commit hooks."""
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files")


@nox.session(python="3.12")
def coverage(session: nox.Session) -> None:
    """Generate coverage report."""
    session.install("-e", ".[dev]")
    session.run(
        "pytest",
        "tests/",
        "-v",
        "--cov=src/dmlclean",
        "--cov-report=html",
        "--cov-report=term",
    )


@nox.session(python="3.12", name="release")
def release(session: nox.Session) -> None:
    """Full release build: lint, test, type-check, build."""
    # Install all dependencies
    session.install("-e", ".[dev]")

    # Run lint
    session.run("ruff", "check", "src/", "tests/")
    session.run("ruff", "format", "--check", "src/", "tests/")

    # Run type check
    session.run("mypy", "--strict", "src/")

    # Run security scan
    session.run("bandit", "-r", "src/", "-ll")

    # Run tests
    session.run(
        "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--cov=src/dmlclean",
        "--cov-fail-under=70",
    )

    # Build package
    session.run("hatch", "build", "--clean")

    # Build binary
    session.install("pyinstaller")
    session.run("pyinstaller", "dmlclean.spec", "--clean")
