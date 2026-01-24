# VAJRA-OSP

<div align="center">

**Versatile Automated Jailbreak and Reconnaissance Arsenal**

A professional penetration testing platform integrating 31 security tools into a unified Qt-based GUI

[![Tools](https://img.shields.io/badge/Tools-31-orange.svg)](#integrated-tools)
[![Platform](https://img.shields.io/badge/Platform-Linux-blue.svg)](#installation)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](#prerequisites)

</div>

---

## 📋 Overview

VAJRA is a comprehensive offensive security platform that unifies 31 powerful penetration testing tools under a single graphical interface. Built with PySide6, it streamlines the entire security testing workflow from reconnaissance to exploitation.

### ✨ Key Features

- **31 Integrated Tools** - Complete toolkit for all penetration testing phases
- **Automated Pipeline** - 8-step reconnaissance workflow with one click
- **Real-time Output** - Live streaming of tool execution with color-coded results
- **Professional Reports** - HTML/PDF report generation with findings aggregation
- **Modern UI** - Clean interface with organized tool categories
- **Plugin Architecture** - Easy tool integration via simple Python plugins
- **Smart Management** - Organized output structure with automatic timestamping

---

## 🛠️ Integrated Tools

### 🤖 Automation
- **Automation Pipeline** - Complete workflow: Whois → Dig → Subdomain Enum → HTTPX → Nmap → Nuclei → Nikto → Report

### 📡 Information Gathering
- **Whois** - Domain registration and ownership lookup
- **Dig** - DNS record enumeration (A, MX, NS, TXT, SOA, etc.)
- **DNSRecon** - Advanced DNS reconnaissance
- **WAFW00F** - Web Application Firewall detection
- **SearchSploit** - Exploit database search

### 🌐 Subdomain Enumeration
- **Subfinder** - Passive subdomain discovery
- **Amass** - OWASP attack surface mapping
- **Sublist3r** - Search engine-based enumeration
- **TheHarvester** - OSINT data gathering
- **Chaos** - Bug bounty dataset integration

### 🎯 Live Host Detection
- **HTTPX** - Fast HTTP probing and tech detection

### 🔍 Port Scanning
- **Nmap** - Network scanner with OS detection and NSE scripts
- **Port Scanner** - Custom Python scanner with banner grabbing

### 🌐 Web Scanning
- **Gobuster** - Directory/DNS/Vhost brute-forcing
- **FFUF** - Web fuzzer with advanced filtering
- **Nikto** - Web server vulnerability scanner
- **EyeWitness** - Web screenshot capture

### 💉 Web Injection
- **SQLi Hunter** - SQL injection detection
- **Web Crawler** - Intelligent web spidering
- **API Tester** - OWASP API security testing
- **Web Fuzzer** - Concurrent endpoint fuzzing

### 🔓 Vulnerability Scanning
- **Nuclei** - Template-based vulnerability scanner

### 🔐 Password Cracking
- **Hashcat** - GPU-accelerated hash cracking
- **John the Ripper** - Password recovery tool
- **Hydra** - Network login cracker
- **Hash Finder** - Hash type identifier

### 🚀 Payload Generation
- **ShellForge** - Reverse/bind shell generator
- **MSFVenom** - Metasploit payload creator

### 📄 File Analysis
- **Strings** - Binary string extraction
- **Dencoder** - Multi-format encoder/decoder

---

## 🚀 Installation

### Prerequisites

- **Python 3.10+** (3.11+ recommended)
- **Operating System**: Linux (primary), macOS (experimental)
- **RAM**: 4GB minimum, 8GB recommended

### Quick Start

```bash
# Clone repository
git clone <repository-url>
cd VAJRA-OSP

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch VAJRA
python main.py
```

### Installing Security Tools

VAJRA wraps external security tools. Install what you need:

**Debian/Ubuntu/Kali:**
```bash
sudo apt update
sudo apt install -y nmap gobuster subfinder amass httpx-toolkit \
    dnsutils dnsrecon hashcat john hydra eyewitness whois \
    nikto ffuf nuclei wafw00f exploitdb theharvester sublist3r
```

**Or use the built-in installer:**
1. Open VAJRA → Settings (⚙️) → Tool Installer
2. Click "Install Missing Tools"

---

## 📖 Usage

### Basic Workflow

1. **Launch**: `python main.py`
2. **Select Tool**: Click from sidebar (organized by category)
3. **Configure**: Enter target and options
4. **Execute**: Click RUN or press `Ctrl+R`
5. **Monitor**: View real-time output
6. **Results**: Auto-saved to `/tmp/Vajra-results/`

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+R` | Run scan |
| `Ctrl+Q` | Stop scan |
| `Ctrl+L` | Clear output |
| `Ctrl+I` | Focus input |

### Output Structure

```
/tmp/Vajra-results/
└── example.com_22012026_161500/
    ├── Logs/              # Raw tool outputs
    ├── JSON/              # Parsed results (final.json)
    ├── Reports/           # HTML/PDF reports
    └── Screenshots/       # EyeWitness captures
```

---

## 🔧 Development

### Project Structure

```
VAJRA-OSP/
├── main.py              # Application entry point
├── core/                # Qt-free business logic
├── ui/                  # PySide6 UI components
├── modules/             # Tool plugins (31 tools)
├── builder/             # Build scripts
└── db/                  # Wordlists and resources
```

### Adding a New Tool

Tools are auto-discovered! Just create a plugin:

```python
# modules/mytool.py
from modules.bases import ToolBase, ToolCategory

class MyTool(ToolBase):
    name = "My Tool"
    category = ToolCategory.INFO_GATHERING
    
    def get_widget(self, main_window):
        return MyToolView(main_window)
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed guide.

---

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and patterns
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development setup and workflow
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

---

## ⚠️ Legal Disclaimer

**VAJRA is for authorized security testing and educational purposes ONLY.**

- ✅ Use on systems you own or have written permission to test
- ✅ Comply with all applicable laws
- ❌ DO NOT use for unauthorized access or illegal activities

**Unauthorized access to computer systems is illegal.** The developers assume NO LIABILITY for misuse.

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 🙏 Acknowledgments

VAJRA integrates tools from the open-source security community:
- Network: Nmap, Whois, Dig, DNSRecon
- Subdomain: Subfinder, Amass, Sublist3r, TheHarvester
- Web: Gobuster, FFUF, Nikto, Nuclei, EyeWitness
- Cracking: Hashcat, John the Ripper, Hydra
- Exploitation: Metasploit Framework

Special thanks to all tool developers and contributors.

---

<div align="center">

**Built for security professionals, by security professionals**

</div>
