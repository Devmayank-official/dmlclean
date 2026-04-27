# DMLClean Roadmap

This document outlines the development roadmap for DMLClean.

**Last Updated**: March 1, 2026

---

## 📍 Current Status: v0.1.0 (Alpha)

- ✅ Core scanning engine complete
- ✅ All 14 cleaning categories implemented
- ✅ Safety mechanisms (Protected Zone, Manifest, Undo)
- ✅ SQLite persistence layer
- ✅ CLI commands (scan, clean, schedule, config, protect, history, report, doctor)
- ✅ Cross-platform support (Windows, macOS, Linux)
- ✅ CI/CD pipeline
- ✅ Docker support
- ✅ 383 tests passing

---

## 🚀 Upcoming Releases

### v0.2.0 (Beta) - Q2 2026

**Theme**: Polish & Performance

#### Features
- [ ] Plugin system for custom cleaning categories
- [ ] Cloud storage cleaning (Google Drive, Dropbox, OneDrive)
- [ ] Duplicate file finder with preview
- [ ] Large file explorer with sorting
- [ ] Real-time disk usage monitoring
- [ ] System tray icon with quick actions

#### Performance
- [ ] Incremental scanning (cache previous results)
- [ ] Parallel file hashing
- [ ] Memory-efficient streaming for large directories
- [ ] Scan speed improvements (target: <2s for fast scan)

#### Quality
- [ ] 90%+ test coverage
- [ ] Zero mypy errors
- [ ] Zero ruff errors
- [ ] Complete documentation

---

### v0.3.0 (Stable) - Q3 2026

**Theme**: Enterprise Ready

#### Features
- [ ] Multi-user support with per-user profiles
- [ ] Centralized configuration management
- [ ] Audit logging for compliance
- [ ] Custom report templates
- [ ] Email notifications
- [ ] Slack/Teams integration
- [ ] API for programmatic access

#### Security
- [ ] Encrypted manifest storage
- [ ] Signed binary releases
- [ ] SBOM (Software Bill of Materials)
- [ ] Third-party security audit

#### Platform Support
- [ ] Homebrew formula for macOS
- [ ] AUR package for Arch Linux
- [ ] Windows Store app
- [ ] Snap package for Linux

---

### v0.4.0 - Q4 2026

**Theme**: Smart Cleaning

#### AI/ML Features
- [ ] ML-based file classification
- [ ] Usage pattern learning
- [ ] Smart recommendations
- [ ] Predictive cleaning suggestions

#### Advanced Features
- [ ] Versioned backups before deletion
- [ ] Integration with cloud backup services
- [ ] Custom cleaning workflows
- [ ] Pre/post cleaning scripts

---

### v1.0.0 (GA) - Q1 2027

**Theme**: Production Ready

#### Goals
- [ ] 100K+ downloads
- [ ] Enterprise customers
- [ ] Full documentation
- [ ] Long-term support (LTS) version
- [ ] Stability guarantee

---

## 🎯 Long-term Vision (2027+)

### Platform Expansion
- [ ] Mobile app (iOS/Android) for remote monitoring
- [ ] Web dashboard for multi-device management
- [ ] Browser extension for browser cache management
- [ ] NAS/Server support

### Integration
- [ ] Integration with popular launchers (Alfred, Raycast)
- [ ] VS Code extension for dev cleanup
- [ ] CI/CD integration for build artifact cleanup
- [ ] Docker volume cleanup integration

### Advanced Features
- [ ] Blockchain-based audit trail (for enterprise)
- [ ] Compliance reporting (GDPR, HIPAA, SOC2)
- [ ] Automated cleanup policies based on disk space
- [ ] Team/organization management

---

## 📋 Backlog (Unscheduled)

### Features
- [ ] GUI application (TBD: Tauri, Electron, or native)
- [ ] Interactive TUI (Text User Interface)
- [ ] Wizard mode for beginners
- [ ] Comparison with other cleaning tools
- [ ] Import/export configurations
- [ ] Profile sharing marketplace

### Improvements
- [ ] i18n/L10n support (multiple languages)
- [ ] Accessibility improvements
- [ ] Performance benchmarks suite
- [ ] Chaos testing for edge cases

### Documentation
- [ ] Video tutorials
- [ ] Interactive examples
- [ ] API documentation
- [ ] Architecture decision records (ADRs)
- [ ] Contributor guide

---

## 🏗️ In Progress

Currently, no major features are in active development. The focus is on:

1. Completing the target file tree structure
2. Achieving quality gates (70%+ coverage, 0 mypy/ruff errors)
3. Finalizing documentation

---

## 🤝 Community Requests

Top requested features from the community:

1. **GUI Application** - Most requested
2. **Mobile App** - Remote monitoring
3. **Cloud Storage Support** - Google Drive, Dropbox
4. **Plugin Marketplace** - Share custom cleaning rules
5. **Dark Mode** - For TUI

---

## 📊 Metrics & Goals

### Key Metrics
- Downloads per month
- Active users
- Test coverage percentage
- Issue resolution time
- Community contributions

### 2026 Goals
- 10K+ downloads
- 1K+ monthly active users
- 90%+ test coverage
- <48 hour issue response time
- 10+ community contributors

---

## 🎖️ How to Help

Want to help us achieve this roadmap? Here's how:

1. **Contribute Code**: Pick an issue from the backlog
2. **Report Bugs**: Help us improve quality
3. **Write Documentation**: Improve guides and tutorials
4. **Spread the Word**: Star the repo, share on social media
5. **Sponsor**: Support development financially

---

## 📅 Release Schedule

| Version | Status | ETA |
|---------|--------|-----|
| v0.1.0  | ✅ Done | Feb 2026 |
| v0.2.0  | Planning | Q2 2026 |
| v0.3.0  | Planned | Q3 2026 |
| v0.4.0  | Planned | Q4 2026 |
| v1.0.0  | Planned | Q1 2027 |

---

**Note**: This roadmap is subject to change based on community feedback and priorities.

For the most up-to-date information, check the [GitHub Projects](https://github.com/dmlclean/dmlclean/projects) page.
