# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**IMPORTANT: Please do not create a public GitHub issue for security vulnerabilities.**

### How to Report

1. **Email**: Send details to dmlclean@dmlabs.dev
2. **Subject Line**: Use "Security Vulnerability - [Brief Description]"
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)
   - Your contact information for follow-up

### What to Expect

- **Initial Response**: Within 48 hours
- **Status Update**: Within 1 week
- **Resolution Timeline**: Depends on severity (see below)

### Severity Levels

| Severity | Description | Target Resolution |
|----------|-------------|-------------------|
| Critical | Remote code execution, data loss | 24-48 hours |
| High | Privilege escalation, data exposure | 1 week |
| Medium | Limited impact vulnerabilities | 2 weeks |
| Low | Minor security improvements | 1 month |

## Security Best Practices

### For Users

1. **Keep Updated**: Always use the latest version
2. **Verify Downloads**: Check SHA256 checksums for binaries
3. **Review Permissions**: Understand what DMLClean can access
4. **Protected Zone**: Keep default protections enabled
5. **Audit Logs**: Review operation manifests regularly

### For Contributors

1. **No Secrets**: Never commit API keys, passwords, or credentials
2. **Secure Dependencies**: Pin dependency versions
3. **Input Validation**: Validate all user inputs
4. **Path Traversal**: Prevent directory traversal attacks
5. **Race Conditions**: Handle concurrent operations safely

## Security Features

### Built-in Protections

- **Protected Zone**: Blocks critical system paths
- **Immutable Protections**: Cannot remove certain protections
- **Manifest Logging**: All operations are logged
- **Dry-Run Default**: Preview before deletion
- **Confirmation Prompts**: Required for destructive operations

### What DMLClean Does NOT Do

- ❌ No network calls (air-gapped compatible)
- ❌ No telemetry or data collection
- ❌ No access to browser passwords/cookies
- ❌ No modification of system files
- ❌ No execution of downloaded files

## Known Limitations

1. **Trash Restore**: Cannot restore from trash on all platforms
2. **Symlinks**: Follow-symlinks option can be dangerous if misused
3. **Root/Admin**: Running as admin bypasses some protections

## Security Audit

DMLClean undergoes regular security audits:

- **Automated**: Bandit security scanner on every CI run
- **Manual**: Code review before each release
- **Third-party**: Annual external security audit (planned)

## Vulnerability Disclosure Policy

We follow a **coordinated disclosure** process:

1. Reporter submits vulnerability privately
2. We assess and confirm the issue
3. We develop and test a fix
4. Fix is deployed to supported versions
5. Public disclosure after 30 days (or by mutual agreement)

## Contact

- **Security Email**: dmlclean@dmlabs.dev
- **PGP Key**: [Available upon request]

## Acknowledgments

We thank all security researchers and contributors who help keep DMLClean secure.

---

**Last Updated**: March 1, 2026
