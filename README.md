# 🛡️ VAJRA - Offensive Security Platform

<div align="center">

**A comprehensive, modular penetration testing platform built with PySide6**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/PySide6-Qt_for_Python-green.svg)](https://pypi.org/project/PySide6/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📋 Overview

**VAJRA** (Versatile Automated Jailbreak and Reconnaissance Arsenal) is a professional-grade offensive security platform that integrates **24 powerful penetration testing tools** into a unified, easy-to-use graphical interface. Built with a modular plugin architecture and centralized styling system, VAJRA streamlines reconnaissance, vulnerability assessment, and security testing workflows.

### ✨ Key Features

- 🎨 **Modern Dark Theme UI** - Professional VS Code-inspired interface with consistent styling
- 🔌 **Plugin Architecture** - Auto-discovery of tool modules at runtime
- 🚀 **Real-time Output** - Live command execution streaming
- 📊 **Organized Results** - Timestamped, target-specific directory structures
- ⚡ **Non-blocking Execution** - Background worker threads keep UI responsive
- 🎯 **Batch Processing** - Process multiple targets from file input
- 📝 **Automated Reporting** - Professional HTML reports with embedded CSS
- 🔧 **Centralized Styling** - All UI components use `ui/styles.py` for consistency

---

## 🛠️ Integrated Tools (24 Total)

### 🔍 Information Gathering
- **Whois** - Domain registration and ownership lookup
- **Dig** - DNS queries (10 record types: A, AAAA, MX, NS, TXT, CNAME, SOA, PTR, ANY, AXFR)
- **DNSRecon** - Comprehensive DNS enumeration (8 scan modes)
- **WAFW00F** - Web Application Firewall detection

### 🌐 Subdomain Enumeration
- **Subfinder** - Passive subdomain discovery (40+ sources)
- **Amass** - OWASP Amass OSINT-based enumeration

### 🌍 Web Reconnaissance
- **Httpx** - Fast HTTP probing with JSON output
- **Gobuster** - Directory/DNS/VHost/Fuzz/S3 brute-forcing (5 modes)
- **FFUF** - Fast web fuzzer with filters and matchers
- **Eyewitness** - Web screenshot capture with batch processing
- **Nikto** - Web server vulnerability scanner

### 🔓 Port Scanning
- **Nmap** - Industry-standard network scanner (TCP/UDP/SYN, NSE scripts, OS detection)
- **Port Scanner** - Custom Python scanner (TCP/SYN/UDP, banner grabbing, stealth mode)

### 🔐 Password Cracking
- **Hashcat** - GPU-accelerated hash cracking (180+ hash types, 4 attack modes)
- **John the Ripper** - CPU-based password recovery (100+ formats, 4 attack modes)
- **Hydra** - Network authentication brute-forcing (50+ protocols)
- **Hash Finder** - Hash type identification

### 🎯 Vulnerability Assessment
- **Nuclei** - Fast vulnerability scanner with YAML templates
- **SearchSploit** - Exploit-DB local search

### 🔧 Utility Tools
- **Dencoder** - Encode/decode in 50+ formats (Base64, URL, Hex, JWT, XSS/SQL payloads)
- **Strings** - Extract readable strings from binary files (ASCII/Unicode/UTF-8/UTF-16)
- **MSFVenom** - Metasploit payload generator

### 🐚 Exploitation
- **ShellForge** - Reverse shell command generator

### 🤖 Automation
- **Automation** - 6-step automated pipeline:
  1. Whois lookup
  2. Subfinder enumeration
  3. Amass enumeration
  4. HTTPX probing
  5. Nmap port scanning
  6. HTML report generation

---

## 📦 Installation

### Prerequisites

- **Python 3.10+** (recommended: Python 3.11)
- **Required External Tools** (install separately):
  ```bash
  # Debian/Ubuntu
  sudo apt update
  sudo apt install -y nmap gobuster subfinder amass httpx dig dnsrecon \
                      hashcat john hydra eyewitness whois nikto ffuf nuclei wafw00f

  # macOS (Homebrew)
  brew install nmap gobuster subfinder amass httpx bind dnsrecon \
               hashcat john hydra eyewitness whois nikto ffuf nuclei
  ```

### Install VAJRA

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/VAJRA-Offensive-Security-Platform.git
   cd VAJRA-Offensive-Security-Platform
   ```

2. **Create virtual environment and install dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
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

2. **Select a tool** from the left sidebar (organized by category)

3. **Configure the tool**:
   - Enter target (domain, IP, CIDR, or select file with multiple targets)
   - Set tool-specific options
   - Review auto-generated command

4. **Click RUN** to execute

5. **View results**:
   - Live output in the console
   - Results saved to `/tmp/Vajra-results/{target}_{timestamp}/`

---

## 🏗️ Architecture

### Directory Structure

```
VAJRA-Offensive-Security-Platform/
├── main.py                 # Application entry point
├── modules/                # Tool plugins (auto-discovered)
│   ├── bases.py            # Base classes (ToolBase, ToolCategory)
│   ├── automation.py       # Automated pipeline
│   ├── nmap.py             # Nmap integration
│   ├── hashcat.py          # Hashcat integration
│   └── ... (20 more tools)
├── ui/                     # User interface components
│   ├── main_window.py      # Main application window
│   ├── sidepanel.py        # Tool navigation sidebar
│   ├── worker.py           # Background subprocess workers
│   ├── styles.py           # Centralized styling & widgets
│   └── notification.py     # Toast notification system
├── core/                   # Core utilities
│   ├── fileops.py          # File/directory management
│   ├── tgtinput.py         # Target input parsing
│   ├── reportgen.py        # HTML report generation
│   └── jsonparser.py       # JSON data aggregation
└── requirements.txt        # Python dependencies
```

### Result Directory

Results are organized by target and timestamp:

```
/tmp/Vajra-results/
├── example.com_01012026_120530/
│   ├── Logs/
│   ├── Reports/
│   ├── JSON/
│   └── Subdomains/
```

---

## ⚠️ Legal Disclaimer

**VAJRA is designed for authorized security testing only.**

- ✅ Use on systems you own or have explicit permission to test
- ❌ Unauthorized access to computer systems is illegal
- ⚠️ User assumes all legal responsibility for tool usage

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ for the Security Community**

⭐ **Star this repo** if you find it useful!

</div>
