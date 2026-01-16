# Tool_Installation.sh - Simple Guide

## 📦 What It Does

**Tool_Installation.sh** automatically checks for missing security tools and installs them on your system.

---

## 🚀 Usage

```bash
# Make executable
chmod +x Tool_Installation.sh

# Run (requires sudo on Linux)
sudo ./Tool_Installation.sh
```

**That's it!** The script handles everything automatically.

---

## ✨ Features

- ✅ Auto-detects your OS (Debian/Ubuntu/Kali, Arch, macOS)
- ✅ Checks which tools are missing
- ✅ Installs missing tools automatically
- ✅ Shows colored progress indicators
- ✅ Displays installation summary

---

## 🎨 What You'll See

### New Banner:
```
    ██╗   ██╗ █████╗      ██╗██████╗  █████╗ 
    ██║   ██║██╔══██╗     ██║██╔══██╗██╔══██╗
    ██║   ██║███████║     ██║██████╔╝███████║
    ╚██╗ ██╔╝██╔══██║██   ██║██╔══██╗██╔══██║
     ╚████╔╝ ██║  ██║╚█████╔╝██║  ██║██║  ██║
      ╚═══╝  ╚═╝  ╚═╝ ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝

        Offensive Security Platform
        Tool Auto-Installer
```

### Installation Progress:
```
ℹ Detected: debian (apt)

[1/6] Information Gathering Tools
  ✓ Whois
  ➜ Installing DNSRecon...
  ✓ DNSRecon installed
  ...

[6/6] Password Cracking & Payload Tools
  ✓ Hashcat
  ✓ John the Ripper
  ✓ Hydra
  ✓ MSFVenom

Installation Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ● Installed Tools: 18/18

✓ All tools ready! VAJRA is good to go.

→ Start VAJRA: python main.py
```

---

## 📋 Tools Installed (18 Total)

### Information Gathering
- Whois, Dig, DNSRecon, WAFW00F, SearchSploit

### Subdomain Enumeration
- Subfinder, Amass

### Live Host Detection & Port Scanning
- HTTPX, Nmap

### Web Scanning
- Gobuster, FFUF, EyeWitness

### Vulnerability Assessment
- Nuclei, Nikto

### Password Cracking & Payloads
- Hashcat, John the Ripper, Hydra, MSFVenom

---

## 🖥️ Supported Platforms

- ✅ Debian / Ubuntu / Kali Linux
- ✅ Arch Linux
- ✅ macOS (with Homebrew)

---

## ⚙️ How It Works

1. **Detects OS** - Identifies your operating system
2. **Updates packages** - Refreshes package manager
3. **Checks tools** - Scans for missing tools
4 **Installs tools** - Downloads and installs missing tools
5. **Verifies installation** - Confirms tools are working
6. **Shows summary** - Displays final status

---

## 💡 Example Run

```bash
$ sudo ./Tool_Installation.sh

    ██╗   ██╗ █████╗      ██╗██████╗  █████╗ 
    ██║   ██║██╔══██╗     ██║██╔══██╗██╔══██╗
    ██║   ██║███████║     ██║██████╔╝███████║
    ╚██╗ ██╔╝██╔══██║██   ██║██╔══██╗██╔══██║
     ╚████╔╝ ██║  ██║╚█████╔╝██║  ██║██║  ██║
      ╚═══╝  ╚═╝  ╚═╝ ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝

        Offensive Security Platform
        Tool Auto-Installer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ Detected: debian (apt)

➜ Updating package manager...
✓ Package manager updated

[1/6] Information Gathering Tools
  ✓ Whois
  ✓ Dig
  ➜ Installing DNSRecon...
  ✓ DNSRecon installed
  ➜ Installing WAFW00F...
  ✓ WAFW00F installed
  ✓ SearchSploit

[2/6] Subdomain Enumeration
  ✓ Subfinder
  ✓ Amass

[3/6] Live Host Detection & Port Scanning
  ✓ HTTPX
  ✓ Nmap

[4/6] Web Scanning Tools
  ✓ Gobuster
  ✓ FFUF
  ✓ EyeWitness

[5/6] Vulnerability Assessment
  ✓ Nuclei
  ✓ Nikto

[6/6] Password Cracking & Payload Tools
  ✓ Hashcat
  ✓ John the Ripper
  ✓ Hydra
  ✓ MSFVenom

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Installation Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ● Installed Tools: 18/18

✓ All tools ready! VAJRA is good to go.

→ Start VAJRA: python main.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🔧 Troubleshooting

### "Please run with sudo"
```bash
sudo ./Tool_Installation.sh
```

### Some tools fail to install
The script will show which tools failed. You can install them manually:
```bash
# Debian/Ubuntu/Kali
sudo apt install <tool-name>

# Arch
sudo pacman -S <tool-name>

# macOS
brew install <tool-name>
```

---

## 📦 Complete Installation Workflow

```bash
# Step 1: Clone VAJRA
git clone https://github.com/yourorg/VAJRA-OSP.git
cd VAJRA-OSP

# Step 2: Install security tools
sudo ./Tool_Installation.sh

# Step 3: Install Python dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Step 4: Run VAJRA
python main.py
```

---

**Simple, automated, and ready to go!** 🚀
