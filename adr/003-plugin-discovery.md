# ADR 003: Plugin Discovery via GitHub Releases + Local Cache

**Date:** 2026-03-11  
**Status:** Accepted  
**Deciders:** DML Labs  

---

## Context

DMLClean needs an extensible plugin system that allows:
- Built-in plugins (14 cleaning categories)
- External plugins (community contributions)
- Easy discovery and installation
- No hosting costs (avoid PyPI, AWS)

---

## Decision

**Plugin Discovery Strategy:**

1. **GitHub Releases API** for plugin registry
   - Host `plugins.json` in `dmlclean/plugin-registry` repository
   - Use GitHub Releases for versioned plugin packages
   - Free hosting via GitHub CDN

2. **Local Cache** for offline support
   - Cache registry in `~/.dmlclean/cache/plugins/registry.json`
   - 24-hour TTL before refresh
   - Fallback to stale cache if GitHub unavailable

3. **pip install from Git** for installation
   - `pip install git+https://github.com/.../plugin.git@v1.0.0`
   - Automatic dependency resolution
   - Standard Python packaging

---

## Plugin Registry Format

```json
{
  "plugins": [
    {
      "name": "aws-cleanup",
      "version": "1.2.0",
      "repo": "dmlclean/aws-plugin",
      "download_url": "https://github.com/dmlclean/aws-plugin/archive/refs/tags/v1.2.0.zip",
      "entry_point": "dmlclean_aws_plugin:AWSPlugin",
      "verified": true,
      "author": "DML Labs",
      "description": "Clean AWS resources (S3, CloudWatch, EBS)"
    }
  ]
}
```

---

## Commands

```bash
dmlclean plugin list              # List available plugins
dmlclean plugin install aws       # Install plugin
dmlclean plugin uninstall aws     # Remove plugin
dmlclean plugin update            # Update all plugins
```

---

## Related

- ADR 001: Repository Pattern
- ADR 002: Service Layer
- ADR 004: GitHub Releases Registry
