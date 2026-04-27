# =============================================================================
# DMLClean Multi-Stage Dockerfile
# =============================================================================
# Production-Ready Docker Image
# Developed by DML Labs | Lead Engineer: @Devmayank-official
#
# Build Stages:
# - base: Common dependencies and setup
# - builder: Build Python package and binary
# - production: Minimal runtime image
# - test: Testing image with dev dependencies
#
# Features:
# - Multi-architecture support (linux/amd64, linux/arm64)
# - Non-root user for security
# - Health check included
# - Trivy security scan ready
# - Optimized layer caching
# =============================================================================

# =============================================================================
# Stage 1: Base (Common Setup)
# =============================================================================
FROM python:3.12-slim AS base

# Build arguments for versioning
ARG APP_VERSION=0.1.0
ARG BUILD_DATE

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# =============================================================================
# Stage 2: Builder (Build Package)
# =============================================================================
FROM base AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project files (optimized for layer caching)
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY dmlclean.spec ./

# Install build tools
RUN pip install --upgrade pip && \
    pip install hatch pyinstaller

# Build Python package (wheel and sdist)
RUN hatch build --clean

# Build PyInstaller binary (optional, for standalone execution)
# Note: This increases build time significantly
# RUN pyinstaller dmlclean.spec --clean

# =============================================================================
# Stage 3: Production (Minimal Runtime Image)
# =============================================================================
FROM python:3.12-slim AS production

# Labels for OCI image specification
LABEL org.opencontainers.image.title="DML Clean" \
      org.opencontainers.image.description="Enterprise-grade, module-driven framework engineered for automated system maintenance and storage lifecycle management." \
      org.opencontainers.image.url="https://github.com/Devmayank-official/dmlclean" \
      org.opencontainers.image.source="https://github.com/Devmayank-official/dmlclean" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.created="2026-03-13" \
      org.opencontainers.image.revision="main" \
      org.opencontainers.image.vendor="DML Labs" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.authors="DML Labs <devmayank.inbox@gmail.com>"

# Human-readable labels
LABEL maintainer="DML Labs <devmayank.inbox@gmail.com>"
LABEL description="DMLClean - Production-grade disk cleaning utility"
LABEL version="0.1.0"
LABEL vendor="DML Labs"

# Create non-root user for security
RUN groupadd --gid 1000 dmlclean && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash dmlclean

# Switch to non-root user
USER dmlclean

WORKDIR /home/dmlclean/app

# Copy Python package from builder
COPY --from=builder --chown=dmlclean:dmlclean /app/dist/*.whl ./
COPY --from=builder --chown=dmlclean:dmlclean /app/src/ ./src/

# Install the package
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir *.whl && \
    rm -f *.whl

# Create directories for config, data, cache, and logs
RUN mkdir -p \
    /home/dmlclean/.config/DML\ Labs/DMLClean \
    /home/dmlclean/.local/share/DML\ Labs/DMLClean \
    /home/dmlclean/.cache/DML\ Labs/DMLClean \
    /home/dmlclean/.local/state/DML\ Labs/DMLClean/Logs && \
    chown -R dmlclean:dmlclean /home/dmlclean

# Set environment variables
ENV DMLCLEAN_CONFIG=/home/dmlclean/.config/DML\ Labs/DMLClean/config.toml \
    DMLCLEAN_HOME=/home/dmlclean/.local/share/DML\ Labs/DMLClean \
    XDG_CONFIG_HOME=/home/dmlclean/.config \
    XDG_DATA_HOME=/home/dmlclean/.local/share \
    XDG_CACHE_HOME=/home/dmlclean/.cache

# No ports exposed (CLI application)

# Volume for mounting host filesystem (read-only recommended)
VOLUME ["/host"]

# Volume for config directory
VOLUME ["/home/dmlclean/.config/DML Labs/DMLClean"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD dmlclean version || exit 1

# Default command
ENTRYPOINT ["dmlclean"]
CMD ["--help"]

# =============================================================================
# Stage 4: Test (Development & Testing)
# =============================================================================
FROM base AS test

# Install test dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY tests/ ./tests/
COPY noxfile.py Makefile ./

# Install with dev dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -e ".[dev,docs]"

# Set test environment variables
ENV PYTEST_ADDOPTS="-v --tb=short" \
    COVERAGE_FILE=/app/.coverage

# Default test command
CMD ["pytest", "tests/", "--cov=src/dmlclean", "--cov-report=term-missing"]

# =============================================================================
# Build Instructions
# =============================================================================
#
# Basic Build:
#   docker build -t ghcr.io/devmayank-official/dml-clean:latest .
#
# Multi-Architecture Build:
#   docker buildx create --use
#   docker buildx build \
#     --platform linux/amd64,linux/arm64 \
#     -t ghcr.io/devmayank-official/dml-clean:latest \
#     -t devmayankofficial/dml-clean:latest \
#     --push .
#
# Build Specific Stage:
#   docker build --target production -t dmlclean:latest .
#   docker build --target test -t dmlclean:test .
#
# Build with Build Args:
#   docker build \
#     --build-arg APP_VERSION=0.1.0 \
#     --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
#     -t dmlclean:latest .
#
# =============================================================================
# Usage Examples
# =============================================================================
#
# Run scan on host filesystem (read-only):
#   docker run --rm -v /:/host:ro \
#     ghcr.io/devmayank-official/dml-clean:latest \
#     scan --path /host/tmp
#
# Run cleaning (use with caution):
#   docker run --rm -v /:/host:ro \
#     ghcr.io/devmayank-official/dml-clean:latest \
#     clean --mode trash --path /host/tmp
#
# Run with custom config:
#   docker run --rm \
#     -v /path/to/config:/home/dmlclean/.config/DML\ Labs/DMLClean \
#     ghcr.io/devmayank-official/dml-clean:latest \
#     scan
#
# Interactive mode:
#   docker run --rm -it \
#     -v /:/host:ro \
#     ghcr.io/devmayank-official/dml-clean:latest \
#     bash
#
# Run tests:
#   docker build --target test -t dmlclean:test .
#   docker run --rm dmlclean:test
#
# Docker Compose:
#   docker-compose -f docker/docker-compose.yml up dmlclean
#
# =============================================================================
# Security Notes
# =============================================================================
#
# 1. Run as non-root user (default)
# 2. Mount host filesystem as read-only when possible
# 3. Don't run with --privileged flag
# 4. Scan image for vulnerabilities:
#    trivy image ghcr.io/devmayank-official/dml-clean:latest
# 5. Keep image updated with latest security patches
#
# =============================================================================
