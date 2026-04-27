# ADR 002: Service Layer for Domain Logic

**Date:** 2026-03-11  
**Status:** Accepted  
**Deciders:** DML Labs  

---

## Context

With Repository Pattern established (ADR 001), we need a layer to orchestrate business logic across multiple repositories.

---

## Decision

Implement **Service Layer** with 6 domain services:

1. **CleaningService** — Orchestrates scan/analyze/clean pipeline
2. **HistoryService** — Manages cleaning history operations
3. **ScheduleService** — Manages scheduled cleaning jobs
4. **ProtectionService** — Manages protected zone configuration
5. **PluginService** — Manages plugin discovery and installation
6. **ReportService** — Generates reports and exports

---

## Architecture

```
CLI Commands → Services → Repositories → Database
                   ↓
               Core Engine (Scanner, Analyzer, Cleaner)
```

---

## Implementation

See `src/dmlclean/services/` for all service implementations.

---

## Related

- ADR 001: Repository Pattern
- ADR 003: Plugin Discovery
- ADR 004: GitHub Releases Registry
