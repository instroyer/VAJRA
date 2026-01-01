# 🛡️ VAJRA - Offensive Security Platform

<div align="center">

**A comprehensive, modular penetration testing platform built with PySide6**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/PySide6-Qt_for_Python-green.svg)](https://pypi.org/project/PySide6/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📋 Overview

**VAJRA** (Versatile Automated Jailbreak and Reconnaissance Arsenal) is a professional-grade offensive security platform that integrates 17+ powerful penetration testing tools into a unified, easy-to-use graphical interface. Built with a modular plugin architecture, VAJRA streamlines reconnaissance, vulnerability assessment, and security testing workflows.

### ✨ Key Features

- 🎨 **Modern Dark Theme UI** - Professional VS Code-inspired interface
- 🔌 **Plugin Architecture** - Auto-discovery of tool modules at runtime
- 🚀 **Real-time Output** - Live command execution streaming
- 📊 **Organized Results** - Timestamped, target-specific directory structures
- ⚡ **Non-blocking Execution** - Background worker threads keep UI responsive
- 🎯 **Batch Processing** - Process multiple targets from file input
- 📝 **Automated Reporting** - Professional HTML reports with embedded CSS
- 🔧 **Customizable Tools** - Extensive configuration options per tool

---

## 🛠️ Integrated Tools (17 Total)

### 🔍 Information Gathering
- **Whois** - Domain registration and ownership lookup
- **Dig** - DNS queries (10 record types: A, AAAA, MX, NS, TXT, CNAME, SOA, PTR, ANY, AXFR)
- **DNSRecon** - Comprehensive DNS enumeration (8 scan modes)

### 🌐 Subdomain Enumeration
- **Subfinder** - Passive subdomain discovery (40+ sources)
- **Amass** - OWASP Amass OSINT-based enumeration

### 🌍 Web Reconnaissance
- **Httpx** - Fast HTTP probing with JSON output
- **Gobuster** - Directory/DNS/VHost/Fuzz/S3 brute-forcing (5 modes)
- **Eyewitness** - Web screenshot capture with batch processing

### 🔓 Port Scanning
- **Nmap** - Industry-standard network scanner (TCP/UDP/SYN, NSE scripts, OS detection)
- **Port Scanner** - Custom Python scanner (TCP/SYN/UDP, banner grabbing, stealth mode)

### 🔐 Password Cracking
- **Hashcat** - GPU-accelerated hash cracking (180+ hash types, 4 attack modes)
- **John the Ripper** - CPU-based password recovery (100+ formats, 4 attack modes)
- **Hydra** - Network authentication brute-forcing (50+ protocols)

### 🔧 Utility Tools
- **Dencoder** - Encode/decode in 50+ formats (Base64, URL, Hex, JWT, XSS/SQL payloads)
- **Strings** - Extract readable strings from binary files (ASCII/Unicode/UTF-8/UTF-16)

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
                      hashcat john hydra eyewitness whois
  
  # macOS (Homebrew)
  brew install nmap gobuster subfinder amass httpx bind dnsrecon \
               hashcat john hydra eyewitness whois
  ```

### Install VAJRA

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/VAJRA-Offensive-Security-Platform.git
   cd VAJRA-Offensive-Security-Platform
   ```

2. **Install Python dependencies**:
   ```bash
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

### Example: Subdomain Enumeration

```bash
# 1. Click "Subfinder" in the sidebar
# 2. Enter target: example.com
# 3. Click RUN
# Results saved to: /tmp/Vajra-results/example.com_01012026_120530/Subdomains/subfinder.txt
```

### Example: Automated Pipeline

```bash
# 1. Click "Automation" in the sidebar
# 2. Enter target: example.com
# 3. Skip unwanted steps (optional)
# 4. Click RUN
# HTML report generated: /tmp/Vajra-results/example.com_*/Reports/final_report.html
```

### Batch Processing

```bash
# Create a targets.txt file:
echo "example1.com" > targets.txt
echo "example2.com" >> targets.txt
echo "example3.com" >> targets.txt

# In VAJRA:
# 1. Click 📁 file picker button
# 2. Select targets.txt
# 3. Click RUN
# Results organized: /tmp/Vajra-results/targets/example1.com_*/
#                    /tmp/Vajra-results/targets/example2.com_*/
```

---

## 🏗️ Architecture

### Directory Structure

```
VAJRA-Offensive-Security-Platform/
├── main.py                 # Application entry point
├── modules/                # Tool plugins (auto-discovered)
│   ├── bases.py           # Base classes (ToolBase, ToolCategory)
│   ├── automation.py      # Automated pipeline
│   ├── gobuster.py        # Gobuster integration
│   ├── nmap.py            # Nmap integration
│   ├── hashcat.py         # Hashcat integration
│   └── ... (14 more tools)
├── ui/                    # User interface components
│   ├── main_window.py     # Main application window
│   ├── sidepanel.py       # Tool navigation sidebar
│   ├── widgets.py         # Reusable UI components (BaseToolView)
│   ├── worker.py          # Background subprocess workers
│   ├── styles.py          # Centralized dark theme styling
│   └── notification.py    # Toast notification system
├── core/                  # Core utilities
│   ├── fileops.py         # File/directory management
│   ├── tgtinput.py        # Target input parsing
│   ├── reportgen.py       # HTML report generation
│   └── jsonparser.py      # JSON data aggregation
└── requirements.txt       # Python dependencies
```

### Plugin System

VAJRA uses **automatic plugin discovery**:

```python
# 1. Create a new tool in modules/mytool.py
from modules.bases import ToolBase, ToolCategory

class MyTool(ToolBase):
    @property
    def name(self):
        return "My Tool"
    
    @property
    def category(self):
        return ToolCategory.INFO_GATHERING
    
    def get_widget(self, main_window):
        return MyToolView(main_window)

# 2. Tool automatically appears in sidebar on restart!
```

### Output Organization

Results are organized by target and timestamp:

```
/tmp/Vajra-results/
├── example.com_01012026_120530/
│   ├── Logs/
│   │   ├── whois.txt
│   │   ├── dig.txt
│   │   └── nmap.txt
│   ├── Reports/
│   │   └── final_report.html
│   ├── JSON/
│   │   └── final.json
│   ├── Subdomains/
│   │   ├── subfinder.txt
│   │   └── amass.txt
│   └── Httpx/
│       └── httpx.json
└── targets/                # Batch scans grouped by filename
    ├── example1.com_*/
    └── example2.com_*/
```

---

## 🎨 Features Showcase

### 1. Gobuster - 5 Operational Modes

- **Dir**: Directory brute-forcing with extensions, blacklist codes, user agent
- **DNS**: Subdomain enumeration with wildcard detection
- **VHost**: Virtual host discovery with domain appending
- **Fuzz**: Advanced fuzzing with request/response filtering (FUZZ keyword)
- **S3**: AWS S3 bucket enumeration

### 2. Hashcat - GPU-Accelerated Cracking

- **180+ Hash Types**: MD5, SHA1/256/512, NTLM, bcrypt, WPA/WPA2, JWT, and more
- **4 Attack Modes**: Dictionary, Combinator, Brute-force, Hybrid
- **Workload Profiles**: Low → Nightmare (1-4)
- **Real-time Results**: Cracked passwords appear instantly in results table

### 3. Nmap - Advanced Scanning

- **Scan Types**: TCP SYN, Connect, UDP, Version detection, OS detection, Aggressive
- **NSE Scripts**: Searchable library with category filtering
- **Timing Templates**: Paranoid (0) → Insane (5)
- **Custom Arguments**: Full CLI flexibility

### 4. Automation - One-Click Pipeline

Executes 6 tools sequentially with live progress dashboard:

1. ✅ **Whois** - Domain registration info
2. ✅ **Subfinder** - Passive subdomain discovery
3. ✅ **Amass** - OSINT subdomain enumeration
4. ✅ **HTTPX** - Live subdomain probing
5. ✅ **Nmap** - Port scanning discovered hosts
6. ✅ **Report** - Professional HTML report generation

Skip/stop controls available for each step.

---

## 🔧 Configuration

### Styling Customization

Edit `ui/styles.py` to customize the color scheme:

```python
# Primary colors
COLOR_BACKGROUND = "#1E1E1E"
COLOR_TEXT_PRIMARY = "#FFFFFF"
COLOR_ACCENT = "#FF6B35"

# Modify button styles, input fields, etc.
```

### Result Directory

Change the base results directory in `core/fileops.py`:

```python
RESULT_BASE = "/tmp/Vajra-results"  # Change to your preferred location
```

---

## 📄 Documentation

- **[CODE_ANALYSIS.md](CODE_ANALYSIS.md)** - Comprehensive technical documentation
  - Architecture deep-dive
  - Tool implementation details
  - UI component breakdown
  - Core utilities reference

---

## 🤝 Contributing

Contributions are welcome! To add a new tool:

1. Create `modules/yourtool.py` following the plugin pattern
2. Inherit from `ToolBase` and implement required properties
3. Tool automatically appears in the sidebar (no registration needed!)

See existing tools for reference implementations.

---

## ⚠️ Legal Disclaimer

**VAJRA is designed for authorized security testing only.**

- ✅ Use on systems you own or have explicit permission to test
- ❌ Unauthorized access to computer systems is illegal
- ⚠️ User assumes all legal responsibility for tool usage

The developers assume no liability for misuse or damage caused by this software.

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **PySide6** - Qt for Python framework
- **Nmap, Amass, Subfinder, Gobuster, Hashcat, John, Hydra** - Excellent open-source security tools
- **OWASP** - Security community and resources

---

## 📧 Contact

For questions, issues, or feature requests:
- **GitHub Issues**: [Create an issue](https://github.com/yourusername/VAJRA/issues)
- **Email**: your.email@example.com

---

<div align="center">

**Built with ❤️ for the Security Community**

⭐ **Star this repo** if you find it useful!

</div>
