# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.7.x   | Yes       |
| < 0.7   | No        |

## Reporting a Vulnerability

DartLab handles financial disclosure data (DART, EDGAR).
If you discover a security vulnerability, **do not open a public issue**.

1. Email **eddmpython@gmail.com** with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
2. You will receive an acknowledgment within **48 hours**.
3. A fix will be developed privately and released as a patch.
4. After the fix is released, the vulnerability will be disclosed in the changelog.

## Scope

The following are in scope:

- API key / credential leakage paths
- Data injection through DART/EDGAR responses
- Dependency vulnerabilities (pip-audit runs in CI)
- Code injection via user-supplied stock codes or parameters

## Out of Scope

- Vulnerabilities in third-party services (DART OpenAPI, SEC EDGAR)
- Issues requiring physical access to the machine
