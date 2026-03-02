<div align="center">

<img src="Resources/logo.png" alt="VAJRA Logo" width="150"/>

# VAJRA
### Offensive Security Platform

*A unified, professional-grade penetration testing environment integrating 32+ powerful security tools.*

[![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg)](#)
[![Platform](https://img.shields.io/badge/Platform-Linux-1c7ed6.svg?logo=linux&logoColor=white)](#)
[![Interface](https://img.shields.io/badge/Interface-GUI-purple.svg)](#)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](#)
[![Status](https://img.shields.io/badge/Status-Stable-success.svg)](#)

Built by **Yash Javiya**
</div>

---

<div align="center">

<a href="#-overview">Overview</a> &nbsp;•&nbsp;
<a href="#-quick-shortcuts">Quick Shortcuts</a> &nbsp;•&nbsp;
<a href="#-platform-highlights">Platform Highlights</a> &nbsp;•&nbsp;
<a href="#-integrated-arsenal">Integrated Arsenal</a> &nbsp;•&nbsp;
<a href="#-installation--setup">Installation</a>
<br>
<a href="#-output-structure">Output Structure</a> &nbsp;•&nbsp;
<a href="#-security--privacy">Security & Privacy</a> &nbsp;•&nbsp;
<a href="#-feature-requests--feedback">Feedback</a> &nbsp;•&nbsp;
<a href="#-support-the-project">Support</a> &nbsp;•&nbsp;
<a href="#-legal-disclaimer">Legal</a>

</div>

## 📋 Overview

**VAJRA** is a standalone, professional **GUI-based** offensive security platform designed to streamline the penetration testing workflow. By unifying 32+ industry-standard tools into a single, cohesive graphical interface, it eliminates the need for scattered terminal windows and manual command chaining.

Built for speed, efficiency, and depth, VAJRA empowers security professionals to execute complex audits—from reconnaissance to exploitation—with precision, all from a single binary.

> 📘 **Documentation**: For a detailed breakdown of all tools, features, and settings, please read the [Official Documentation](documentation.md).

---

## ⚡ Quick Shortcuts

| Action | Shortcut | Description |
|--------|----------|-------------|
| **Command Palette** | `Ctrl+K` | Find any tool or action instantly |
| **Terminal Drawer** | `Ctrl+`` ` | Toggle the built-in shell |
| **Run Tool** | `Ctrl+R` | Execute the active tool |
| **Stop Tool** | `Ctrl+Q` | Terminate the current process |
| **Clear Output** | `Ctrl+L` | Clear the active output panel |
| **Focus Input** | `Ctrl+I` | Jump focus to the primary target field |
| **Save Session** | `Ctrl+S` | Save the current workspace state |
| **Load Session** | `Ctrl+O` | Load a saved workspace |

---

## 🌟 Platform Highlights

### 🎨 Modern UI/UX

* **Dynamic Theming**: Switch between **GitHub Dark**, **GitHub Light**, **One Dark**, and **Industrial Orange** themes instantly — every element updates live.
* **Mission Control Dashboard**: Monitor system performance (CPU/RAM gauges), Active Processes, and Local IP Address at a glance.
* **Welcome Experience**: A clean landing page shown on freshly opened sessions.
* **Command Palette** (`Ctrl+K`): A Spotlight-style search interface for instant navigation to any tool, theme, or action.
* **Integrated Terminal** (`Ctrl+`` `): A full-featured terminal drawer with command history and live streaming output.
* **Session Management**: Save your entire pentest state and resume exactly where you left off.
* **Tab System**: Each tool opens in its own moveable, closeable tab — run multiple tools in parallel.
* **Collapsible Sidebar**: Category-grouped tool navigation, toggleable to maximize screen space.

### 🛠️ Core Capabilities

* **Integrated Arsenal**: 32+ specialized security tools categorized for efficient workflow.
* **Automated Pipeline**: A "Fire & Forget" bug bounty workflow that chains recon → scanning → vulnerability detection.
* **Real-time Streaming**: Watch tool output live as it is produced.
* **Smart Installer**: Auto-detects and installs missing external dependencies.
* **Organized Output**: Every scan auto-creates timestamped `Logs/`, `Reports/`, and `JSON/` folders under `~/Vajra-results/`.
* **Command Preview**: Every tool shows the exact CLI command it will run — fully transparent.

### 🎯 Who is this tool for?

* **Penetration Testers**: Simplify complex workflows and manage assessments in one place.
* **Bug Bounty Hunters**: Automate reconnaissance and discovery to find low-hanging fruit faster.
* **Red Teamers**: Maintain a persistent, organized workspace during engagements.
* **Security Researchers**: Experiment with tools and analyze output in a unified environment.

---

## 🛠️ Integrated Arsenal

<div align="center">

[![Automation](https://img.shields.io/badge/🤖-Automation-0D1117?style=flat-square)](#-automation)
[![Info Gathering](https://img.shields.io/badge/📡-Info_Gathering-0D1117?style=flat-square)](#-info-gathering)
[![Subdomain](https://img.shields.io/badge/🌐-Subdomain-0D1117?style=flat-square)](#-subdomain-enumeration)
[![Live Subs](https://img.shields.io/badge/🟢-Live_Subs-0D1117?style=flat-square)](#-live-subdomains)
[![Port Scan](https://img.shields.io/badge/🔍-Port_Scan-0D1117?style=flat-square)](#-port-scanning)
[![Visual](https://img.shields.io/badge/📸-Visual-0D1117?style=flat-square)](#-web-screenshots)
<br>
[![Web Scan](https://img.shields.io/badge/🕸️-Web_Scan-0D1117?style=flat-square)](#-web-scanning)
[![Injection](https://img.shields.io/badge/💉-Injection-0D1117?style=flat-square)](#-web-injection)
[![Vuln Scan](https://img.shields.io/badge/🔓-Vuln_Scan-0D1117?style=flat-square)](#-vulnerability-scanner)
[![Cracker](https://img.shields.io/badge/🔐-Cracker-0D1117?style=flat-square)](#-cracker)
[![Payloads](https://img.shields.io/badge/🚀-Payloads-0D1117?style=flat-square)](#-payload-generator)
[![Analysis](https://img.shields.io/badge/📄-Analysis-0D1117?style=flat-square)](#-file-analysis)
[![OSINT](https://img.shields.io/badge/🔎-OSINT-0D1117?style=flat-square)](#-osint)

</div>

### 🤖 Automation
| Tool | Description |
|------|-------------|
| **Automation** | End-to-end recon & audit pipeline (Whois → Subdomains → Live Hosts → Nmap → Nuclei → Report) |

### 📡 Info Gathering
| Tool | Description |
|------|-------------|
| **Whois** | Domain registry & registrar lookup |
| **Dig** | Advanced DNS record enumeration (A, MX, NS, TXT, SOA) |
| **DNSRecon** | DNS zone transfers, record analysis & wildcard detection |
| **WAFW00F** | WAF detection and fingerprinting (Cloudflare, Akamai, Imperva…) |
| **SearchSploit** | Offline Exploit-DB archive search |

### 🌐 Subdomain Enumeration
| Tool | Description |
|------|-------------|
| **Subfinder** | Passive subdomain discovery via 40+ online sources |
| **Amass** | In-depth attack surface mapping (active + passive) |
| **theHarvester** | OSINT — emails, subdomains, hosts from multiple public sources |
| **Sublist3r** | Search engine-based subdomain enumeration |
| **Chaos** | ProjectDiscovery internet-wide dataset integration |

### 🟢 Live Subdomains
| Tool | Description |
|------|-------------|
| **Httpx** | Fast multi-purpose HTTP probing of live hosts |

### 🔍 Port Scanning
| Tool | Description |
|------|-------------|
| **Nmap** | Industry-standard network mapper (SYN/TCP/UDP/ACK scans, NSE scripts) |
| **Port Scanner** | Custom async multi-threaded TCP scanner with stealth mode & banner grabbing |

### 📸 Web Screenshots
| Tool | Description |
|------|-------------|
| **Eyewitness** | Automated web screenshots for large host lists |

### 🕸️ Web Scanning
| Tool | Description |
|------|-------------|
| **FFUF** | Fast web fuzzer for directory, file, and parameter discovery |
| **Gobuster** | Directory, DNS, and virtual host brute-forcing |

### 💉 Web Injection
| Tool | Description |
|------|-------------|
| **SQLi Hunter** | Native Python SQL Injection engine (error-based & boolean-blind) |
| **Web Fuzzer** | High-performance payload-based endpoint and parameter fuzzer |
| **API Tester** | REST & GraphQL endpoint security auditing |
| **Crawler** | Web application spidering and site-map builder |

### 🔓 Vulnerability Scanner
| Tool | Description |
|------|-------------|
| **Nuclei** | Template-based CVE and misconfiguration scanner |
| **Nikto** | Comprehensive web server vulnerability scanner |

### 🔐 Cracker
| Tool | Description |
|------|-------------|
| **Hashcat** | GPU-accelerated password recovery with rule and mask attacks |
| **John** | CPU-based password auditor (100+ hash formats) |
| **Hydra** | Parallelized network login cracker (SSH, FTP, HTTP, SMB…) |
| **Hash Finder** | Heuristic hash-type identifier (200+ algorithm signatures) |
| **Dencoder** | Universal encoder/decoder (Base64, Hex, URL, ROT13, JWT…) |

### 🚀 Payload Generator
| Tool | Description |
|------|-------------|
| **MSFVenom** | Metasploit payload builder with encoder and template injection support |
| **ShellForge** | 100+ reverse/bind shell one-liners with listener auto-generation |

### 📄 File Analysis
| Tool | Description |
|------|-------------|
| **Strings** | Binary printable-text extractor |

### 🔎 OSINT
| Tool | Description |
|------|-------------|
| **HTTrack** | Full website mirroring and offline browsing |

---

## 🚀 Installation & Setup

### 1. Download & Run
VAJRA is distributed as a portable binary.

1. **Download** the `vajra` binary.
2. **Make Executable**:
   ```bash
   chmod +x vajra
   ```
3. **Launch**:
   ```bash
   ./vajra
   ```
   *Note: Raw-socket scans (e.g., Nmap SYN) require root privileges:*
   ```bash
   sudo ./vajra
   ```

### 2. Install External Tools
1. Launch VAJRA.
2. Go to **Settings (⚙️)** → **Tool Installer**.
3. Click **"Check Dependencies"**.
4. The built-in manager detects your OS (Debian/Arch/Fedora) and installs missing tools automatically.

---

## 📖 Output Structure

All scan results are automatically organized by target and session:

```
~/Vajra-results/
└── example.com_01032026_191500/
    ├── Logs/              # Raw tool logs (nmap.xml, nuclei.txt, whois.txt…)
    ├── JSON/              # Consolidated findings (final.json)
    ├── Reports/           # Generated HTML reports
    └── Screenshots/       # EyeWitness captures
```

> For file-input scans (multiple targets): `~/Vajra-results/<group>/<target>_<timestamp>/`

---

## 🛡️ Security & Privacy

* **Local Execution**: VAJRA runs entirely on your local machine. No data is sent to the cloud.
* **Root Privileges**: Only specific subprocesses (e.g., Nmap SYN scans) require elevated privileges when needed.
* **Process Supervision**: Child processes use `PR_SET_PDEATHSIG` — if VAJRA closes, all spawned processes terminate automatically.

---

## 💡 Feature Requests & Feedback

- **Feature Requests**: Open an [Issue](https://github.com/instroyer/VAJRA/issues) with the "Enhancement" label.
- **Bug Reports**: Open an [Issue](https://github.com/instroyer/VAJRA/issues) with the "Bug" label.

## ❤️ Support the Project

- ⭐ **Star** the repository on GitHub.
- 🍴 **Fork** the repository to your profile.
- 🗣️ **Share** it with your network and fellow security professionals.
- ☕ **Tip the Developer**: [Buy me a Coffee on Ko-fi](https://ko-fi.com/yashjaviya)!

---

## ⚠️ Legal Disclaimer

**VAJRA is a proprietary tool designed for authorized security testing ONLY.**

By downloading and using this software, you agree that:
- ✅ You will use it only on systems you own or have explicit written permission to test.
- ✅ You will comply with all applicable local, state, and federal laws.
- ❌ The developers assume **NO LIABILITY** for misuse or damage caused by this software.
- ❌ **Reverse engineering, decompilation, or unauthorized redistribution of this binary is strictly prohibited.**

**Unauthorized access to computer systems is illegal.**

---

<div align="center">

**Built for security professionals, by Yash Javiya**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue.svg?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/yash--javiya/)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support-FF5E5B.svg?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/yashjaviya)

*VAJRA v1.0*

</div>
