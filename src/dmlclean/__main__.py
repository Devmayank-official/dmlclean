"""
Entry point for running DMLClean as a module.

Usage:
    python -m dmlclean [OPTIONS] COMMAND [ARGS]

Or when installed:
    dmlclean [OPTIONS] COMMAND [ARGS]
"""

from dmlclean.cli.app import app

if __name__ == "__main__":
    app()
