# DMLClean Makefile
# Development shortcuts for common tasks

.PHONY: help install dev test lint type-check security clean build release docker

# Default target
help:
	@echo "DMLClean Development Commands"
	@echo ""
	@echo "  install       - Install dependencies"
	@echo "  dev           - Install dev dependencies"
	@echo "  test          - Run tests with coverage"
	@echo "  test-fast     - Run tests without coverage"
	@echo "  lint          - Run linter (ruff)"
	@echo "  format        - Format code (ruff)"
	@echo "  type-check    - Run type checker (mypy)"
	@echo "  security      - Run security scan (bandit)"
	@echo "  clean         - Clean build artifacts"
	@echo "  build         - Build package"
	@echo "  build-binary  - Build PyInstaller binary"
	@echo "  release       - Full release build"
	@echo "  docker-build  - Build Docker image"
	@echo "  docker-run    - Run Docker container"
	@echo "  docker-test   - Run tests in Docker"

# Install dependencies
install:
	pip install -e .

# Install dev dependencies
dev:
	pip install -e ".[dev]"

# Run tests with coverage
test:
	hatch run test:cov

# Run tests quickly without coverage
test-fast:
	hatch run test:quick

# Run linter
lint:
	hatch run lint:check

# Format code
format:
	hatch run lint:format

# Run type checker
type-check:
	hatch run type:check

# Run security scan
security:
	hatch run security:scan

# Run all quality checks
check: lint type-check security

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info .hatch/ .pytest_cache/ .mypy_cache/
	rm -rf coverage.xml htmlcov/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build package
build:
	hatch build --clean

# Build PyInstaller binary
build-binary:
	pyinstaller dmlclean.spec --clean

# Full release build
release: clean test lint type-check security build build-binary

# Build Docker image
docker-build:
	docker build -t dmlclean:latest .

# Run Docker container
docker-run:
	docker run -it -v /:/host dmlclean:latest

# Run tests in Docker
docker-test:
	docker-compose run test

# Pre-commit hook
pre-commit:
	pre-commit run --all-files

# Initialize pre-commit hooks
install-hooks:
	pre-commit install

# Show version
version:
	hatch version

# Run CLI
run:
	python -m dmlclean $(ARGS)

# Run scan
scan:
	python -m dmlclean scan $(ARGS)

# Run clean
clean-files:
	python -m dmlclean clean --mode dry-run $(ARGS)

# Generate docs
docs:
	mkdocs build

# Serve docs
docs-serve:
	mkdocs serve
