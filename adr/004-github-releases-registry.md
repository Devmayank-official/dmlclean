# ADR 004: GitHub Releases Registry for Plugin Distribution

**Date:** 2026-03-11  
**Status:** Accepted  
**Deciders:** DML Labs  

---

## Context

Building on ADR 003 (Plugin Discovery), we need a concrete implementation for the plugin registry.

---

## Decision

**GitHub Repository Structure:**

```
github.com/dmlclean/
├── plugin-registry/          # Registry repository
│   └── plugins.json          # Plugin metadata
├── aws-plugin/               # Example plugin
│   ├── pyproject.toml
│   └── dmlclean_aws_plugin/
└── gcp-plugin/               # Another plugin
```

---

## Registry Repository

**Repository:** `dmlclean/plugin-registry`

**File:** `plugins.json`

**Update Process:**
1. Plugin author submits PR to `plugin-registry`
2. DML Labs reviews and merges
3. Plugin appears in `dmlclean plugin list`

---

## Verified Badge

- **verified: true** — Official DML Labs plugins
- **verified: false** — Community plugins (user discretion)

---

## Installation Flow

```bash
# User runs:
dmlclean plugin install aws-cleanup

# Behind the scenes:
# 1. Fetch plugins.json from GitHub
# 2. Find aws-cleanup entry
# 3. Run: pip install git+https://github.com/dmlclean/aws-plugin.git@v1.2.0
# 4. Plugin installed and ready to use
```

---

## Costs

- **Hosting:** $0/month (GitHub Free)
- **Bandwidth:** $0/month (GitHub CDN)
- **Maintenance:** ~1 hour/week (review PRs)

---

## Related

- ADR 001: Repository Pattern
- ADR 002: Service Layer
- ADR 003: Plugin Discovery
