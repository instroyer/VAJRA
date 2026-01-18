# 🛡️ VAJRA - Offensive Security Platform

<div align="center">

**A comprehensive, professional-grade penetration testing platform with 28 integrated security tools**

[![Tools](https://img.shields.io/badge/Tools-28-orange.svg)](#-integrated-tools-28-total)
[![Platform](https://img.shields.io/badge/Platform-Linux-blue.svg)](#)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](#)

</div>

---

## 📋 Overview

**VAJRA** (Versatile Automated Jailbreak and Reconnaissance Arsenal) is a professional-grade offensive security platform that integrates **28 powerful penetration testing tools** into a unified, easy-to-use graphical interface. VAJRA streamlines reconnaissance, vulnerability assessment, web injection testing, and comprehensive security workflows.

### ✨ Key Features

- 🎨 **Modern Dark Theme UI** - Professional interface with consistent styling
- 🚀 **Real-time Output** - Live command execution streaming with color-coded output
- 📊 **Organized Results** - Timestamped, target-specific directory structures
- ⚡ **Non-blocking Execution** - Background worker threads keep UI responsive
- 🎯 **Batch Processing** - Process multiple targets from file input
- 📝 **Automated Reporting** - Professional HTML/PDF reports with CVSS severity system
- ⌨️ **Keyboard Shortcuts** - Ctrl+R (Run), Ctrl+Q (Stop), Ctrl+L (Clear)

---

## 🛠️ Integrated Tools (28 Total)

### 🤖 Automation
- **Automation Pipeline** - Complete 8-step reconnaissance:
  1. Whois lookup → 2. Dig (DNS) → 3. Subfinder → 4. TheHarvester
  5. HTTPX probing → 6. Nmap scanning → 7. Nuclei (optional) → 8. Nikto (optional)

### 🔍 Information Gathering
| Tool | Description |
|------|-------------|
| **Whois** | Domain registration and ownership lookup |
| **Dig** | DNS queries (10 record types: A, AAAA, MX, NS, TXT, CNAME, SOA, PTR, ANY, AXFR) |
| **DNSRecon** | Comprehensive DNS enumeration (8 scan modes) |
| **WAFW00F** | Web Application Firewall detection |
| **SearchSploit** | Exploit-DB local search with CVE/platform filters |

### 🌐 Subdomain Enumeration
| Tool | Description |
|------|-------------|
| **Subfinder** | Passive subdomain discovery (40+ sources) |
| **Amass** | OWASP Amass OSINT-based enumeration |

### 🌍 Live Host Detection
| Tool | Description |
|------|-------------|
| **HTTPX** | Fast HTTP probing with JSON output |

### 🔓 Port Scanning
| Tool | Description |
|------|-------------|
| **Nmap** | Industry-standard scanner (TCP/UDP/SYN, NSE scripts, OS detection) |
| **Port Scanner** | Custom Python scanner (TCP/SYN/UDP, banner grabbing, stealth mode) |

### 🕸️ Web Scanning
| Tool | Description |
|------|-------------|
| **Gobuster** | Directory/DNS/VHost/Fuzz/S3 brute-forcing (5 modes) |
| **FFUF** | Fast web fuzzer with advanced filters and matchers |
| **EyeWitness** | Web application screenshot capture |

### 💉 Web Injection
| Tool | Description |
|------|-------------|
| **SQLi Hunter** | Native SQL injection scanner (error-based, boolean-blind, time-blind) |
| **Web Crawler** | BurpSuite-style web spider with depth control |
| **API Tester** | Postman-like API testing with authentication support |
| **Web Fuzzer** | Custom web fuzzer with concurrent requests |

### 🛡️ Vulnerability Assessment
| Tool | Description |
|------|-------------|
| **Nuclei** | Template-based vulnerability scanner with severity filtering |
| **Nikto** | Web server vulnerability scanner with CVSS color coding |

### 🔐 Password Cracking
| Tool | Description |
|------|-------------|
| **Hashcat** | GPU-accelerated hash cracking (180+ hash types, 4 attack modes) |
| **John the Ripper** | CPU-based password recovery (100+ formats, 4 attack modes) |
| **Hydra** | Network authentication brute-forcing (50+ protocols) |
| **Hash Finder** | Hash type identification and analysis |
| **Dencoder** | Encode/decode in 50+ formats (Base64, URL, Hex, JWT, XSS/SQL payloads) |

### 🎯 Payload Generation
| Tool | Description |
|------|-------------|
| **ShellForge** | Reverse/bind shell command generator (20+ shell types) |
| **MSFVenom** | Metasploit payload generator (Windows/Linux/macOS/Android) |

### 📂 File Analysis
| Tool | Description |
|------|-------------|
| **Strings** | Extract readable strings from binary files (ASCII/Unicode/UTF-8) |

---

## 📦 Installation

### Prerequisites

Before running VAJRA, you need to install the external security tools it wraps.

### Install Security Tools

Run the automated installer (supports Debian/Ubuntu/Kali, Arch Linux, macOS):

```bash
chmod +x Tool_Installation.sh
sudo ./Tool_Installation.sh
```

The script automatically detects and installs missing tools:
- **Package Manager Tools**: nmap, gobuster, ffuf, hashcat, john, hydra, nikto, etc.
- **Go Tools**: subfinder, httpx, nuclei, amass (installed to `~/go/bin`)

### Manual Installation

If you prefer to install tools manually:

```bash
# Debian/Ubuntu/Kali
sudo apt update
sudo apt install -y nmap gobuster subfinder amass httpx-toolkit dnsutils dnsrecon \
                    hashcat john hydra eyewitness whois nikto ffuf nuclei wafw00f \
                    exploitdb theharvester

# Arch Linux
sudo pacman -S nmap gobuster subfinder amass httpx dnsutils dnsrecon \
               hashcat john hydra whois nikto ffuf nuclei

# macOS (Homebrew)
brew install nmap gobuster subfinder amass httpx bind dnsrecon \
             hashcat john hydra whois nikto ffuf nuclei
```

---

## 🚀 Running VAJRA

### Quick Start

1. **Make the executable runnable**:
   ```bash
   chmod +x vajra
   ```

2. **Launch VAJRA**:
   ```bash
   ./vajra
   ```

3. **Select a tool** from the left sidebar (organized by 12 categories)

4. **Configure the tool**:
   - Enter target (domain, IP, CIDR, or select file with multiple targets)
   - Set tool-specific options
   - Review auto-generated command (editable)

5. **Click RUN** (or press `Ctrl+R`) to execute

6. **View results**:
   - Live output in the console with color-coded messages
   - Results saved to `/tmp/Vajra-results/{target}_{timestamp}/`

### Automated Reconnaissance

1. Open the **Automation** tool from the sidebar
2. Enter a target domain
3. Configure which steps to run (Subfinder, Amass, HTTPX, Nmap, Nuclei, Nikto)
4. Click **Run Pipeline**
5. Monitor progress with real-time status indicators
6. View generated HTML report in `Reports/final_report.html`

---

## 📊 Result Organization

Results are automatically organized by target and timestamp:

```
/tmp/Vajra-results/
└── example.com_18012026_213000/
    ├── Logs/              # Tool outputs (whois, dig, nmap, nuclei, etc.)
    ├── Reports/           # HTML/PDF reports
    └── JSON/              # Aggregated JSON data
```

All scan outputs are saved in the **Logs/** directory with descriptive filenames.

---

## 📝 Reports

VAJRA generates professional HTML reports with:
- **Executive Summary**: High-level statistics and risk assessment
- **CVSS-Based Severity**: Color-coded vulnerability ratings (Critical, High, Medium, Low)
- **Collapsible Sections**: Whois, DNS, Subdomains, Services, Nmap, Nuclei, Nikto, EyeWitness
- **Interactive Tables**: Sortable and searchable results
- **Export Options**: HTML (standalone) and PDF formats

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+R` | Run active tool |
| `Ctrl+Q` | Stop active tool |
| `Ctrl+L` | Clear output |

---

## 🔧 System Requirements

- **OS**: Linux (Debian/Ubuntu/Kali, Arch Linux, or compatible)
- **RAM**: 4GB minimum, 8GB recommended
- **Display**: 1280x720 minimum resolution
- **Disk**: 500MB free space for installation + results storage

---

## 📍 Tool Installation Locations

After running `Tool_Installation.sh`:

- **System Tools**: `/usr/bin/` and `/usr/local/bin/` (nmap, hashcat, john, etc.)
- **Go Tools**: `~/go/bin/` (subfinder, httpx, nuclei, amass)

**Important:** Add Go tools to PATH if not already:
```bash
export PATH=$PATH:$(go env GOPATH)/bin
# Add to ~/.bashrc or ~/.zshrc to make permanent
```

---

## ⚠️ Legal Disclaimer

**VAJRA is designed for authorized security testing only.**

- ✅ Use on systems you **own** or have **explicit written permission** to test
- ✅ Use in authorized penetration testing engagements
- ✅ Use in CTF competitions and lab environments
- ❌ **NEVER** use against systems without authorization
- ❌ **NEVER** use for malicious purposes

**Unauthorized access to computer systems is illegal** under laws including:
- Computer Fraud and Abuse Act (USA)
- Computer Misuse Act (UK)
- Similar laws in most jurisdictions

⚠️ **User assumes all legal responsibility for tool usage.**  
📋 **Always obtain proper authorization before testing.**

---

## 🛡️ Security Best Practices

### For Users

1. **Keep tools updated**:
   ```bash
   sudo apt update && sudo apt upgrade
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

4. **Verify tools**:
   - Check tool versions: `nmap --version`, `nuclei -version`
   - Verify installations are legitimate

---

## 📞 Support

For issues or questions:
- Check that all external tools are properly installed
- Verify Go tools are in PATH: `echo $PATH | grep go`
- Review scan logs in `/tmp/Vajra-results/`

---

## 📜 License

**VAJRA is proprietary software.**  
© 2026 All rights reserved.

This software is provided for authorized security testing purposes only.  
Redistribution, modification, or reverse engineering is prohibited without explicit written permission.

---

<div align="center">

**Built for Professional Security Researchers**

🛡️ **VAJRA** - Comprehensive Offensive Security Platform

</div>
