# =============================================================================
# DMLClean GitHub Secrets Configuration
# =============================================================================
# This file documents the required GitHub Secrets for CI/CD
# DO NOT commit actual secret values to version control!
# =============================================================================

# =============================================================================
# REQUIRED SECRETS (Configure in GitHub Settings > Secrets and variables > Actions)
# =============================================================================

## Docker Hub Credentials (For Docker image push)
# -----------------------------------------------------------------------------
# Secret Name: DOCKER_HUB_USERNAME
# Value: devmayankofficial
# Description: Docker Hub username for pushing images

# Secret Name: DOCKER_HUB_TOKEN
# Value: <your-docker-hub-personal-access-token>
# Description: Docker Hub access token (generate from Docker Hub settings)
# How to generate:
#   1. Login to https://hub.docker.com
#   2. Go to Account Settings > Security
#   3. Click "New Access Token"
#   4. Give it a name (e.g., "GitHub Actions DMLClean")
#   5. Select "Read & Write" permissions
#   6. Copy the token and add to GitHub Secrets
# ==============================================================================

## PyPI Credentials (DISABLED for v0.1.0 - Enable for v0.2.0+)
# -----------------------------------------------------------------------------
# Secret Name: PYPI_API_TOKEN
# Value: pypi-<your-pypi-token>
# Description: PyPI API token for package publishing
# Note: Not required for v0.1.0 (ENABLE_PYPI=false)

# How to generate (for future use):
#   1. Login to https://pypi.org
#   2. Go to Account Settings > API Tokens
#   3. Click "Add API Token"
#   4. Give it a name (e.g., "DMLClean GitHub Actions")
#   5. Select "Entire project" scope
#   6. Copy the token and add to GitHub Secrets
# ==============================================================================

## Codecov Token (Optional - for coverage reporting)
# -----------------------------------------------------------------------------
# Secret Name: CODECOV_TOKEN
# Value: <your-codecov-token>
# Description: Codecov upload token (optional, public repos don't require)
# How to get:
#   1. Go to https://codecov.io
#   2. Login with GitHub
#   3. Add your repository
#   4. Go to Settings > General
#   5. Copy "Repository Upload Token"
# ==============================================================================

# =============================================================================
# OPTIONAL SECRETS (For enhanced features)
# =============================================================================

## Sentry DSN (For error tracking - Future feature)
# -----------------------------------------------------------------------------
# Secret Name: SENTRY_DSN
# Value: https://<key>@<project>.ingest.sentry.io/<id>
# Description: Sentry DSN for error tracking (if implemented)
# ==============================================================================

## Slack Webhook (For notifications - Future feature)
# -----------------------------------------------------------------------------
# Secret Name: SLACK_WEBHOOK_URL
# Value: https://hooks.slack.com/services/...
# Description: Slack webhook URL for build notifications
# ==============================================================================

# =============================================================================
# ENVIRONMENT CONFIGURATION
# =============================================================================

# GitHub Environments to configure:
# 1. pypi (for PyPI releases - future use)
#    - Go to Settings > Environments > New environment: "pypi"
#    - Add required reviewers (optional)
#    - Add deployment branches: refs/tags/v*
#    - Add environment secrets if different from repo secrets

# 2. github-pages (for documentation deployment)
#    - Automatically created by GitHub Pages
#    - No additional configuration needed
# ==============================================================================

# =============================================================================
# VERIFICATION STEPS
# =============================================================================

# After configuring secrets, verify they work:

# 1. Test Docker Hub login:
#    - Push a test tag to repository
#    - Check Actions > docker job
#    - Verify "Login to Docker Hub" step succeeds

# 2. Test GHCR login:
#    - Automatically uses GITHUB_TOKEN
#    - Should work without additional configuration

# 3. Test PyPI (when enabled):
#    - Create test tag: git tag v0.1.0-test && git push origin v0.1.0-test
#    - Check Actions > release-pypi job
#    - Verify upload succeeds (or skip if ENABLE_PYPI=false)

# 4. Test Codecov:
#    - Check Actions > test job
#    - Verify "Upload coverage to Codecov" step succeeds
#    - Check codecov.io for coverage report
# ==============================================================================

# =============================================================================
# SECURITY BEST PRACTICES
# =============================================================================

# 1. Never commit secrets to version control
# 2. Use environment-specific secrets when possible
# 3. Rotate secrets regularly (every 90 days recommended)
# 4. Use minimum required permissions for tokens
# 5. Enable secret scanning in repository settings
# 6. Review secret usage in workflow logs
# 7. Use OIDC (OpenID Connect) where supported (more secure than tokens)
# ==============================================================================

# =============================================================================
# TROUBLESHOOTING
# =============================================================================

# Issue: "Login to Docker Hub failed"
# Solution:
#   - Verify DOCKER_HUB_USERNAME and DOCKER_HUB_TOKEN are correct
#   - Check token has "Read & Write" permissions
#   - Regenerate token if expired

# Issue: "Permission denied" for GHCR
# Solution:
#   - GITHUB_TOKEN should have automatic permissions
#   - Check repository has "Read and write permissions" in Settings > Actions

# Issue: PyPI upload fails
# Solution:
#   - Verify ENABLE_PYPI is set to "false" for v0.1.0
#   - Check PYPI_API_TOKEN is correct (when enabled)
#   - Verify package name doesn't already exist on PyPI

# Issue: Codecov upload fails
# Solution:
#   - CODECOV_TOKEN is optional for public repos
#   - Set fail_ci_if_error: false in workflow (already configured)
#   - Check codecov.io repository is activated
# ==============================================================================

# =============================================================================
# LAST UPDATED
# =============================================================================
# Date: 2026-03-13
# Version: v0.1.0
# Status: Ready for production use
# ==============================================================================
