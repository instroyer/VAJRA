<div align="center">

<img src="Resources/logo.png" alt="VAJRA Logo" width="150"/>

# VAJRA
### Offensive Security Platform



*A unified, professional-grade penetration testing environment integrating 31+ powerful security tools.*

[![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg)](#)
[![Platform](https://img.shields.io/badge/Platform-Linux-grey.svg)](#)
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

**VAJRA** is a standalone, professional **GUI-based** offensive security platform designed to streamline the penetration testing workflow. By unifying 31 industry-standard tools into a single, cohesive graphical interface, it eliminates the need for scattered terminal windows and manual command chaining.

Built for speed, efficiency, and depth, VAJRA empowers security professionals to execute complex audits—from reconnaissance to exploitation—with precision, all from a single binary.

> 📘 **Documentation**: For a detailed breakdown of all tools, features, and settings, please read the [Official Documentation](documentation.md).

---

## ⚡ Quick Shortcuts

| Action | Shortcut | Description |
|--------|----------|-------------|
| **Command Palette** | `Ctrl+K` | Find any tool or setting instantly |
| **Terminal Drawer** | `Ctrl+\`` | Toggle the built-in shell |
| **Run Tool** | `Ctrl+R` | Execute the active tool |
| **Stop Tool** | `Ctrl+Q` | Terminate current process |
| **Save Session** | `Ctrl+S` | Save current workspace |
| **Load Session** | `Ctrl+O` | Load a saved workspace |

---

## 🌟 Platform Highlights

### 🎨 Modern UI/UX

* **Dynamic Theming**: Switch between **GitHub Dark**, **GitHub Light**, **One Dark**, and **Industrial Orange** themes instantly.
* **Mission Control Dashboard**: Monitor system performance (CPU/RAM), Active Processes, and Local IP Address.
* **Welcome Experience**: A dedicated landing page ensuring a clean startup environment.
* **Command Palette**: A Spotlight-like search interface for instant navigation.
* **Integrated Terminal**: A full-featured terminal drawer with persistent history adjacent to your tools.
* **Session Management**: Save your entire pentest state and pick up exactly where you left off.

### 🛠️ Core Capabilities

* **Integrated Arsenal**: 31+ specialized security tools categorized for efficient workflow.
* **Automated Pipeline**: A "Fire & Forget" bug bounty workflow that chains reconnaissance tools.
* **Real-time Streaming**: Watch tool output live with ANSI color support.
* **Smart Installer**: Auto-detects and installs missing external dependencies.

### 🎯 Who is this tool for?

VAJRA is tailored for professionals who demand efficiency without compromising depth:
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

</div>

### 🤖 Automation
| Tool | Description |
|------|-------------|
| **Automation Pipeline** | End-to-end reconnaissance workflow (Whois → Nuclei) |

### 📡 Info Gathering
| Tool | Description |
|------|-------------|
| **Whois** | Domain registry lookup |
| **Dig** | Advanced DNS enumeration |
| **DNSRecon** | DNS zone transfer and record analysis |
| **WAFW00F** | WAF detection and fingerprinting |
| **SearchSploit** | Offline exploit database search |

### 🌐 Subdomain Enumeration
| Tool | Description |
|------|-------------|
| **Subfinder** | Passive subdomain discovery |
| **Amass** | OWASP attack surface mapping |
| **TheHarvester** | OSINT intelligence gathering |
| **Sublist3r** | Search engine-based enumeration |
| **Chaos** | Public bug bounty dataset integration |

### 🟢 Live Subdomains
| Tool | Description |
|------|-------------|
| **HTTPX** | Fast IP/domain probing |

### 🔍 Port Scanning
| Tool | Description |
|------|-------------|
| **Nmap** | Network port scanning (Supports SYN/UDP) |
| **Port Scanner** | Lightweight custom scanner |

### 📸 Web Screenshots
| Tool | Description |
|------|-------------|
| **EyeWitness** | Automated web screenshots |

### 🕸️ Web Scanning
| Tool | Description |
|------|-------------|
| **FFUF** | Fast web fuzzer |
| **Gobuster** | Directory and DNS brute-forcing |

### 💉 Web Injection
| Tool | Description |
|------|-------------|
| **SQLi Hunter** | Heuristic SQL injection scanner |
| **Web Fuzzer** | Parameter and endpoint fuzzing |
| **API Tester** | API endpoint security auditing |
| **Crawler** | Site mapping and spidering |

### 🔓 Vulnerability Scanner
| Tool | Description |
|------|-------------|
| **Nuclei** | Template-based vulnerability scanner |
| **Nikto** | Comprehensive web server vulnerability scanner |

### 🔐 Cracker
| Tool | Description |
|------|-------------|
| **Hashcat** | GPU-accelerated password recovery |
| **John the Ripper** | Advanced password auditor |
| **Hydra** | Network login cracker |
| **Hash Finder** | Hash type identifier |
| **Dencoder** | Encoding/Decoding utility |

### 🚀 Payload Generator
| Tool | Description |
|------|-------------|
| **MSFVenom** | Metasploit payload builder |
| **ShellForge** | Reverse shell generator |

### 📄 File Analysis
| Tool | Description |
|------|-------------|
| **Strings** | Binary text extractor |

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
   *Note: detailed scanning (e.g., Nmap SYN scans) may require root privileges:*
   ```bash
   sudo ./vajra
   ```

### 2. Install External Tools
VAJRA orchestrates powerful external tools. You don't need to install them manually.

1. Launch VAJRA.
2. Go to **Settings (⚙️)** → **Tool Installer**.
3. Click **"Check Dependencies"**.
4. The built-in manager will detect your OS (Debian/Arch/Fedora) and install missing tools automatically.

---

## 📖 Output Structure

All scan results are automatically organized by session:

```
/tmp/Vajra-results/
└── example.com_SESSION_TIMESTAMP/
    ├── Logs/              # Raw tool logs (nmap.xml, nuclei.txt)
    ├── JSON/              # Consolidated findings (final.json)
    ├── Reports/           # HTML Reports
    └── Screenshots/       # EyeWitness captures
```

---

## 🛡️ Security & Privacy

* **Local Execution**: VAJRA runs entirely on your local machine. No data is sent to the cloud.
* **Root Privileges**: VAJRA separates UI logic from execution to run safely. Only specific subprocesses (like Nmap) utilize elevated privileges when required.

---

## 💡 Feature Requests & Feedback

We value your feedback! If you have ideas for new features or encounter any bugs, please use the modern standard for collaboration:

- **Feature Requests**: Open an [Issue](https://github.com/instroyer/VAJRA/issues) with the "Enhancement" label.
- **Bug Reports**: Open an [Issue](https://github.com/instroyer/VAJRA/issues) with the "Bug" label.

## ❤️ Support the Project

If you find VAJRA useful for your security workflow, please consider supporting the project:

- ⭐ **Star** the repository on GitHub to show your appreciation.
- 🍴 **Fork** the repository to save it to your profile.
- 🗣️ **Share** it with your network and fellow security professionals.
- ☕ **Tip the Developer**: If you love the tool, you can [Buy me a Coffee on Ko-fi](https://ko-fi.com/yashjaviya)!

Your support helps keep the project alive and growing!

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
