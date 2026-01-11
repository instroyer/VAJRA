# Security Policy

This document outlines security considerations for VAJRA-OSP and the responsible disclosure process.

---

## 📋 Table of Contents

1. [Supported Versions](#supported-versions)
2. [Reporting a Vulnerability](#reporting-a-vulnerability)
3. [Security Considerations](#security-considerations)
4. [Responsible Use](#responsible-use)
5. [Known Security Limitations](#known-security-limitations)
6. [Security Best Practices](#security-best-practices)

---

## 🔒 Supported Versions

| Version | Supported |
|---------|-----------|
| Latest (main branch) | ✅ Yes |
| Previous releases | ⚠️ Critical fixes only |
| Development branches | ❌ No |

We recommend always using the latest version from the main branch.

---

## 🚨 Reporting a Vulnerability

### For Security Issues in VAJRA

If you discover a security vulnerability in VAJRA itself (the platform code), please:

1. **DO NOT** open a public GitHub issue
2. **Email** the maintainers directly (if contact provided) or use GitHub's private vulnerability reporting
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

| Stage | Timeframe |
|-------|-----------|
| Acknowledgment | 48 hours |
| Initial assessment | 1 week |
| Fix development | 2-4 weeks |
| Public disclosure | After fix is released |

### For External Tools

VAJRA wraps external security tools (nmap, hashcat, etc.). Vulnerabilities in those tools should be reported to their respective maintainers:

- **Nmap**: https://nmap.org/book/man-bugs.html
- **Hashcat**: https://github.com/hashcat/hashcat/security
- **Nuclei**: https://github.com/projectdiscovery/nuclei/security
- **Hydra**: https://github.com/vanhauser-thc/thc-hydra/issues

---

## ⚠️ Security Considerations

### Command Injection Prevention

VAJRA executes shell commands based on user input. We mitigate command injection through:

1. **`shlex.quote()`**: All user inputs are quoted before shell execution
2. **Input validation**: Targets are normalized and validated
3. **No direct string formatting**: Commands built using arrays, not f-strings

**Example (Correct)**:
```python
import shlex
target = shlex.quote(user_input)
cmd = ["nmap", "-sV", target]
```

**Anti-pattern (Avoid)**:
```python
# DANGEROUS - DO NOT DO THIS
cmd = f"nmap -sV {user_input}"
```

### Subprocess Execution

- All tool execution uses `subprocess.Popen` with explicit argument lists
- `shell=True` is avoided where possible
- When shell mode is required, commands are properly escaped

### File Path Handling

- User-provided file paths are validated
- Paths are normalized using `os.path.normpath()`
- Results are stored in isolated directories per scan

### No Network Exfiltration

VAJRA does not:
- Send telemetry data
- Phone home to external servers
- Upload scan results anywhere

All data stays local on your machine.

---

## 🎯 Responsible Use

### Legal Disclaimer

**VAJRA is designed for authorized security testing only.**

- ✅ Use on systems you **own**
- ✅ Use on systems with **explicit written permission**
- ✅ Use in **authorized penetration testing engagements**
- ✅ Use in **CTF competitions** and **lab environments**
- ❌ **NEVER** use against systems without authorization
- ❌ **NEVER** use for malicious purposes

**Unauthorized access to computer systems is illegal** under laws including:
- Computer Fraud and Abuse Act (USA)
- Computer Misuse Act (UK)
- Similar laws in most jurisdictions

### Scope of Tools

Each tool in VAJRA has different legal implications:

| Tool Category | Typical Authorization Needed |
|---------------|------------------------------|
| Info Gathering (Whois, Dig) | Usually public data, low risk |
| Port Scanning (Nmap) | Written permission required |
| Vulnerability Scanning | Explicit authorization required |
| Password Cracking | Only on credentials you own |
| Exploitation | Formal pentest agreement required |

### User Responsibility

By using VAJRA, you acknowledge that:

1. You are solely responsible for your actions
2. You will only use the tools legally and ethically
3. The developers are not liable for misuse
4. You understand the potential consequences of security testing

---

## ⚡ Known Security Limitations

### 1. Local Privilege Escalation

Some tools (nmap SYN scan, etc.) require root privileges. Running VAJRA as root means:
- All tools run with elevated privileges
- A bug could affect the entire system

**Mitigation**: Use `sudo` only when needed, or use polkit for specific operations.

### 2. Credential Storage

VAJRA does not store credentials, but external tools may:
- **Hashcat**: Potfile stores cracked hashes
- **Hydra**: May log credentials in output
- **John**: Session files contain password data

**Mitigation**: Clear `/tmp/Vajra-results/` after sensitive engagements.

### 3. Output File Permissions

Scan results are stored in `/tmp/Vajra-results/` with default permissions.

**Mitigation**:
```bash
# Restrict permissions manually
chmod -R 700 /tmp/Vajra-results/
```

### 4. Process Visibility

Running processes are visible to all users via `ps aux`:
```
user 12345 nmap -sV target.com
```

**Mitigation**: Use on isolated systems where process visibility isn't a concern.

### 5. No Input Sanitization Display

User input is displayed in the UI as-is. Malicious HTML in tool output could render.

**Mitigation**: Output is escaped using `html.escape()` where rendered as HTML.

---

## 🛡️ Security Best Practices

### For Users

1. **Keep tools updated**:
   ```bash
   sudo apt update && sudo apt upgrade
   pip install --upgrade -r requirements.txt
   ```

2. **Use dedicated testing environments**:
   - Virtual machines for testing
   - Isolated networks
   - Clean up after engagements

3. **Protect scan results**:
   ```bash
   # Encrypt sensitive results
   tar czf results.tar.gz /tmp/Vajra-results/
   gpg -c results.tar.gz
   rm -rf /tmp/Vajra-results/
   ```

4. **Audit external tools**:
   - Verify tool sources before installation
   - Check for CVEs in tool dependencies

### For Developers

1. **Never hardcode credentials**
2. **Always use `shlex.quote()` for shell arguments**
3. **Validate all user inputs**
4. **Don't log sensitive data in plaintext**
5. **Review subprocess commands in PRs carefully**
6. **Test with malicious inputs** (e.g., `; rm -rf /`, `$(whoami)`)

### For Reviewers

When reviewing PRs, check for:

- [ ] All user inputs are escaped with `shlex.quote()`
- [ ] No hardcoded paths or credentials
- [ ] `shell=True` is avoided or justified
- [ ] Output doesn't leak sensitive info
- [ ] File permissions are appropriate

---

## 📊 Security Audit Checklist

For periodic security reviews:

### Code Review
- [ ] Grep for `shell=True` and verify each usage
- [ ] Grep for f-strings with subprocess commands
- [ ] Check for `eval()`, `exec()` usage
- [ ] Review file path handling

### Dependency Audit
```bash
# Check Python dependencies
pip install pip-audit
pip-audit

# Check for known vulnerabilities
pip install safety
safety check
```

### Permission Review
```bash
# Check file permissions in project
find . -type f -perm /go+w -ls

# Check output directory permissions
ls -la /tmp/Vajra-results/
```

---

## 📜 License & Warranty Disclaimer

VAJRA is provided "AS IS" without warranty of any kind. The developers are not responsible for:

- Damage caused by tool misuse
- Legal consequences of unauthorized testing
- Data loss or corruption
- Security breaches resulting from tool bugs

See [LICENSE](LICENSE) for complete terms.

---

## 📞 Contact

For security-related inquiries:
- Open a private security advisory on GitHub
- Email maintainers directly (if contact info available)

For general questions, use GitHub Issues or Discussions.
