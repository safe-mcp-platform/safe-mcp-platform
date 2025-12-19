# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

### 1. GitHub Security Advisories (Preferred)

Report directly through our [GitHub Security Advisories](https://github.com/safe-mcp-platform/safe-mcp-platform/security/advisories/new) page.

### 2. Email

Send an email to **security@safe-mcp-platform.io** with:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability, including how an attacker might exploit it

### 3. Encrypted Communication

For highly sensitive disclosures, use our PGP key:

```
-----BEGIN PGP PUBLIC KEY BLOCK-----
[PGP KEY WILL BE ADDED]
-----END PGP PUBLIC KEY BLOCK-----
```

## Response Timeline

- **24 hours**: Initial acknowledgment of your report
- **72 hours**: Initial assessment and severity classification
- **7 days**: Detailed response with remediation timeline
- **30 days**: Public disclosure (after patch is released)

## Security Update Process

1. **Receive Report** → Security team reviews
2. **Validate** → Confirm vulnerability exists
3. **Assess** → Determine severity (CVSS score)
4. **Develop Fix** → Create patch
5. **Test** → Verify fix and check for regressions
6. **Release** → Deploy patched version
7. **Disclose** → Publish security advisory

## Disclosure Policy

- We follow **coordinated disclosure** principles
- We aim to patch critical vulnerabilities within **7 days**
- We publicly disclose after patch is released (minimum 30 days from report)
- Reporters are credited in security advisories (unless anonymity is requested)

## Security Advisories

View published security advisories:
- [GitHub Security Advisories](https://github.com/safe-mcp-platform/safe-mcp-platform/security/advisories)
- [Website](https://safe-mcp-platform.io/security)

## Vulnerability Categories

We classify vulnerabilities using CVSS 3.1:

| Severity | CVSS Score | Response Time |
|----------|------------|---------------|
| **Critical** | 9.0 - 10.0 | 24 hours |
| **High** | 7.0 - 8.9 | 7 days |
| **Medium** | 4.0 - 6.9 | 30 days |
| **Low** | 0.1 - 3.9 | 90 days |

### Examples of Critical Vulnerabilities

- Remote code execution (RCE)
- SQL injection leading to data breach
- Authentication bypass
- Privilege escalation to admin
- Exposure of cryptographic keys

### Examples of High Vulnerabilities

- Cross-site scripting (XSS) with data access
- Server-side request forgery (SSRF)
- Path traversal with file read/write
- Denial of service (DoS) affecting availability

### Out of Scope

The following are **not** considered security vulnerabilities:

- Theoretical vulnerabilities without proof of concept
- Vulnerabilities in dependencies (report to upstream)
- Social engineering attacks
- Physical attacks
- Attacks requiring physical access to the server
- Attacks that require user to install malicious software
- Brute force attacks without rate limiting bypass

## Security Best Practices

When using SAFE-MCP-Platform:

1. **Keep Updated**: Always use the latest version
2. **Secure Credentials**: Use strong API keys, rotate regularly
3. **Network Security**: Deploy behind firewall, use TLS
4. **Access Control**: Implement least privilege principle
5. **Audit Logs**: Enable and monitor audit logs
6. **Input Validation**: Validate all MCP inputs
7. **Rate Limiting**: Configure appropriate rate limits

## Security Features

SAFE-MCP-Platform includes:

- ✅ **4-Layer Detection**: Pattern, Rules, ML, Behavioral
- ✅ **Audit Logging**: Complete audit trail of all actions
- ✅ **Rate Limiting**: Built-in DoS protection
- ✅ **API Authentication**: Key-based authentication
- ✅ **TLS Support**: Encrypted communication
- ✅ **Input Validation**: Comprehensive input sanitization
- ✅ **Sandboxing**: Isolated execution environments

## Compliance

We maintain security controls aligned with:

- **SOC 2 Type II** (in progress)
- **ISO 27001** (planned)
- **GDPR** requirements
- **OWASP Top 10**

## Bug Bounty Program

**Coming Q1 2026**: We will launch a bug bounty program with rewards:

- **Critical**: $5,000 - $10,000
- **High**: $1,000 - $5,000
- **Medium**: $500 - $1,000
- **Low**: $100 - $500

Early reporters will receive priority access to the program.

## Hall of Fame

Security researchers who responsibly disclose vulnerabilities:

*(None yet - be the first!)*

## Contact

- **Security Team**: security@safe-mcp-platform.io
- **General Inquiries**: hello@safe-mcp-platform.io
- **Website**: https://safe-mcp-platform.io/security

## PGP Key Fingerprint

```
[TO BE ADDED]
```

---

**Thank you for helping keep SAFE-MCP-Platform and our users safe!** 🛡️

