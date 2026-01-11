# 🛡️ VAJRA - Offensive Security Platform

<div align="center">

**A comprehensive, modular penetration testing platform built with PySide6**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/PySide6-Qt_for_Python-green.svg)](https://pypi.org/project/PySide6/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tools](https://img.shields.io/badge/Tools-24-orange.svg)](#-integrated-tools-24-total)

</div>

---

## 📋 Overview

**VAJRA** (Versatile Automated Jailbreak and Reconnaissance Arsenal) is a professional-grade offensive security platform that integrates **24 powerful penetration testing tools** into a unified, easy-to-use graphical interface. Built with a modular plugin architecture and centralized styling system, VAJRA streamlines reconnaissance, vulnerability assessment, and security testing workflows.

### ✨ Key Features

- 🎨 **Modern Dark Theme UI** - Professional VS Code-inspired interface with consistent styling
- 🔌 **Plugin Architecture** - Auto-discovery of tool modules at runtime
- 🚀 **Real-time Output** - Live command execution streaming with color-coded output
- 📊 **Organized Results** - Timestamped, target-specific directory structures
- ⚡ **Non-blocking Execution** - Background worker threads keep UI responsive
- 🎯 **Batch Processing** - Process multiple targets from file input
- 📝 **Automated Reporting** - Professional HTML/PDF reports with CVSS severity system
- 🔧 **Centralized Styling** - All UI components use `ui/styles.py` for consistency
- ⌨️ **Keyboard Shortcuts** - Ctrl+R (Run), Ctrl+Q (Stop), Ctrl+L (Clear)

---

## 🛠️ Integrated Tools (24 Total)

### 🤖 Automation
- **Automation** - Complete 8-step reconnaissance pipeline:
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

- **Python 3.10+** (recommended: Python 3.11+)
- **External Security Tools** (see below)

### Quick Install (Recommended)

Use the included installer script to install all required tools:

```bash
# Clone the repository
git clone https://github.com/yourusername/VAJRA-OSP.git
cd VAJRA-OSP

# Run the tool installer (installs all external tools)
chmod +x install_tools.sh
./install_tools.sh

# Or just verify which tools you have
./install_tools.sh --verify

# Quick install (skip slow tools like metasploit)
./install_tools.sh --quick
```

### Manual Installation

If you prefer to install tools manually:

```bash
# Debian/Ubuntu/Kali
sudo apt update
sudo apt install -y nmap gobuster subfinder amass httpx-toolkit dnsutils dnsrecon \
                    hashcat john hydra eyewitness whois nikto ffuf nuclei wafw00f \
                    exploitdb

# Arch Linux
sudo pacman -S nmap gobuster subfinder amass httpx dnsutils dnsrecon \
               hashcat john hydra whois nikto ffuf nuclei

# macOS (Homebrew)
brew install nmap gobuster subfinder amass httpx bind dnsrecon \
             hashcat john hydra whois nikto ffuf nuclei
```

### Install VAJRA

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/VAJRA-OSP.git
   cd VAJRA-OSP
   ```

2. **Create virtual environment and install dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or: .\venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **Run VAJRA**:
   ```bash
   python main.py
   ```

---

## 🚀 Quick Start

### Basic Usage

1. **Launch the application**:
   ```bash
   python main.py
   ```

2. **Select a tool** from the left sidebar (organized by 11 categories)

3. **Configure the tool**:
   - Enter target (domain, IP, CIDR, or select file with multiple targets)
   - Set tool-specific options
   - Review auto-generated command (editable)

4. **Click RUN** (or press `Ctrl+R`) to execute

5. **View results**:
   - Live output in the console with color-coded messages
   - Results saved to `/tmp/Vajra-results/{target}_{timestamp}/`

### Automated Reconnaissance

1. Open the **Automation** tool from the sidebar
2. Enter a target domain
3. Configure which steps to run (Subfinder, Amass, HTTPX, Nmap, etc.)
4. Click **Run Pipeline**
5. Monitor progress with real-time status indicators
6. View generated HTML report in `Reports/final_report.html`

---

## 🏗️ Architecture

### Directory Structure

```
VAJRA-OSP/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── modules/                # Tool plugins (auto-discovered)
│   ├── bases.py            # Base classes (ToolBase, ToolCategory)
│   ├── automation.py       # 8-step automated pipeline
│   ├── nmap.py, hashcat.py, ... (24 tools total)
├── ui/                     # User interface components
│   ├── main_window.py      # Main application window
│   ├── sidepanel.py        # Tool navigation sidebar
│   ├── worker.py           # Background subprocess workers
│   ├── styles.py           # Centralized styling & widgets
│   └── notification.py     # Toast notification system
├── core/                   # Core utilities
│   ├── fileops.py          # File/directory management
│   ├── tgtinput.py         # Target input parsing
│   ├── reportgen.py        # HTML/PDF report generation
│   ├── jsonparser.py       # JSON data aggregation
│   └── config.py           # Configuration management
└── linux_setup/            # Platform-specific setup
```

### Result Directory Structure

Results are organized by target and timestamp:

```
/tmp/Vajra-results/
└── example.com_11012026_150821/
    ├── Logs/              # whois.txt, dig.txt, dnsrecon.txt
    ├── Subdomains/        # amass.txt, subfinder.txt, alive.txt
    ├── Scans/             # nmap*.xml, portscan.txt
    ├── Httpx/             # httpx.json
    ├── Nuclei/            # nuclei.json
    ├── Nikto/             # nikto_*.csv
    ├── Eyewitness/        # screenshots/
    ├── JSON/              # final.json (aggregated data)
    └── Reports/           # final_report.html, final_report.pdf
```

---

## 🔌 Plugin Architecture

VAJRA uses a dynamic plugin system for easy extensibility. To add a new tool:

```python
# modules/mytool.py
from modules.bases import ToolBase, ToolCategory
from ui.styles import StyledToolView, SafeStop

class MyTool(ToolBase):
    name = "My Tool"
    category = ToolCategory.INFO_GATHERING
    
    def get_widget(self, main_window):
        return MyToolView(main_window)

class MyToolView(StyledToolView, SafeStop):
    # ... implement UI and logic
```

The tool will be automatically discovered and added to the sidebar on next launch.

---

## 📊 Reports

VAJRA generates professional HTML reports with:
- **Executive Summary**: High-level statistics and risk assessment
- **CVSS-Based Severity**: Color-coded vulnerability ratings
- **Collapsible Sections**: Whois, DNS, Subdomains, Services, Nmap, Nuclei, Nikto
- **Interactive Tables**: Sortable and searchable results
- **Export Options**: HTML (standalone) and PDF formats

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+R` | Run active tool |
| `Ctrl+Q` | Stop active tool |
| `Ctrl+L` | Clear output |
| `Ctrl+I` | Focus primary input |

---

## ⚠️ Legal Disclaimer

**VAJRA is designed for authorized security testing only.**

- ✅ Use on systems you own or have explicit written permission to test
- ❌ Unauthorized access to computer systems is illegal
- ⚠️ User assumes all legal responsibility for tool usage
- 📋 Always obtain proper authorization before testing

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-tool`)
3. Commit your changes (`git commit -m 'Add amazing tool'`)
4. Push to the branch (`git push origin feature/amazing-tool`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ for the Security Community**

⭐ **Star this repo** if you find it useful!

</div>
