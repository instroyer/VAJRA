# VAJRA - Functional Specification Document

**Document Version:** 1.0  
**Date:** January 2026  
**Product:** VAJRA (Versatile Automated Jailbreak and Reconnaissance Arsenal)  
**Platform:** Linux (Primary), Cross-platform compatible

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Overview](#2-product-overview)
3. [User Personas](#3-user-personas)
4. [System Requirements](#4-system-requirements)
5. [Functional Requirements](#5-functional-requirements)
6. [User Interface Specification](#6-user-interface-specification)
7. [Tool Functional Specifications](#7-tool-functional-specifications)
8. [Input/Output Specifications](#8-inputoutput-specifications)
9. [Use Cases](#9-use-cases)
10. [Error Handling](#10-error-handling)
11. [Security Considerations](#11-security-considerations)

---

## 1. Executive Summary

VAJRA is a professional-grade offensive security platform that consolidates 22+ penetration testing tools into a unified graphical user interface. The platform enables security professionals to perform comprehensive reconnaissance, vulnerability scanning, web application testing, and password cracking through an intuitive, modern interface.

### Key Value Propositions

- **Unified Interface**: Single platform for multiple security tools
- **Real-time Feedback**: Live output streaming with color-coded results
- **Organized Results**: Automatic directory structure for scan outputs
- **Automated Workflows**: Sequential tool pipelines with report generation
- **Professional Reporting**: Styled HTML reports with export capabilities

---

## 2. Product Overview

### 2.1 Product Name

**VAJRA** - Versatile Automated Jailbreak and Reconnaissance Arsenal

### 2.2 Product Description

A desktop GUI application that provides:

- Graphical interfaces for command-line security tools
- Real-time output visualization with severity-based coloring
- Batch processing capabilities for multiple targets
- Automated scan pipelines with HTML report generation
- Built-in utilities (hash identification, encoding/decoding, string extraction)

### 2.3 Target Platform

- **Primary**: Linux (Kali Linux, Parrot OS, Ubuntu)
- **Secondary**: Windows, macOS (with tool dependencies)

### 2.4 Technology Stack

- **GUI Framework**: PySide6 (Qt for Python)
- **Language**: Python 3.8+
- **Distribution**: Standalone executable (PyInstaller/Nuitka)

---

## 3. User Personas

### 3.1 Penetration Tester

- **Role**: Professional security consultant
- **Needs**: Quick access to multiple tools, organized outputs, professional reports
- **Usage**: Client engagements, vulnerability assessments

### 3.2 Security Researcher

- **Role**: Vulnerability researcher, bug bounty hunter
- **Needs**: Efficient reconnaissance, subdomain enumeration, web fuzzing
- **Usage**: Bug bounty programs, security research

### 3.3 IT Security Administrator

- **Role**: Internal security team member
- **Needs**: Network scanning, password auditing, infrastructure assessment
- **Usage**: Internal security assessments, compliance testing

### 3.4 Security Student

- **Role**: Learning cybersecurity
- **Needs**: Accessible tools, visual feedback, learning environment
- **Usage**: CTF competitions, learning exercises

---

## 4. System Requirements

### 4.1 Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Storage | 500 MB | 2+ GB |
| Display | 1280x720 | 1920x1080+ |

### 4.2 Software Requirements

| Requirement | Specification |
|-------------|---------------|
| Operating System | Linux (Kali/Ubuntu 20.04+), Windows 10+, macOS 10.15+ |
| Python | 3.8 or higher |
| PySide6 | 6.7.0 or higher |

### 4.3 External Tool Dependencies

VAJRA requires the following tools to be installed for full functionality:

| Category | Tools |
|----------|-------|
| DNS/Recon | whois, dig, dnsrecon, subfinder, amass |
| Network | nmap, httpx |
| Web Scanning | gobuster, ffuf, nikto, nuclei, wafw00f |
| Screenshots | eyewitness |
| Crackers | hashcat, john, hydra, searchsploit |

---

## 5. Functional Requirements

### 5.1 Core Platform Functions

#### FR-001: Tool Discovery

- **Description**: System shall automatically discover and load all tool modules from the `modules/` directory
- **Priority**: High
- **Acceptance**: All valid tool modules appear in sidepanel on startup

#### FR-002: Tab-based Tool Management

- **Description**: Each tool shall open in its own tab within the main window
- **Priority**: High
- **Acceptance**: Multiple tools can run simultaneously in separate tabs

#### FR-003: Real-time Output Streaming

- **Description**: Tool output shall stream to the UI in real-time without blocking
- **Priority**: High
- **Acceptance**: Output appears within 100ms of generation

#### FR-004: Process Control

- **Description**: User shall be able to start and stop any running tool
- **Priority**: High
- **Acceptance**: Stop button terminates process within 5 seconds

#### FR-005: Result Organization

- **Description**: All scan results shall be saved in organized directory structure
- **Priority**: Medium
- **Acceptance**: Results saved to `/tmp/Vajra-results/<target>_<timestamp>/`

#### FR-006: Notification System

- **Description**: System shall provide toast notifications for important events
- **Priority**: Medium
- **Acceptance**: Notifications appear for scan start, completion, and errors

#### FR-007: Privilege Escalation

- **Description**: System shall handle sudo/pkexec for tools requiring root
- **Priority**: Medium
- **Acceptance**: User can enable sudo mode and provide password

### 5.2 Tool Category Functions

#### FR-100: Information Gathering

- Whois domain lookup
- DNS record queries (A, MX, NS, AXFR, +trace)
- DNS reconnaissance and enumeration
- Subdomain discovery
- WAF detection

#### FR-200: Network Scanning

- Port scanning (TCP connect, SYN, UDP)
- Service detection
- OS fingerprinting
- HTTP/HTTPS probing

#### FR-300: Web Scanning

- Directory brute-forcing
- Virtual host discovery
- Web fuzzing with filters
- Vulnerability template scanning
- Web server vulnerability assessment

#### FR-400: Password Cracking

- Hash cracking (GPU/CPU)
- Network service brute-forcing
- Hash type identification
- Encoding/decoding utilities

#### FR-500: File Analysis

- Binary string extraction
- Pattern detection (URLs, IPs, emails)

#### FR-600: Automation

- Sequential scan pipelines
- Automatic report generation
- Pipeline step skip/stop controls

---

## 6. User Interface Specification

### 6.1 Main Window Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  VAJRA - Offensive Security Platform               [─] [□] [×] │
├───────────┬─────────────────────────────────────────────────────┤
│           │  [Tab 1] [Tab 2] [Tab 3]                        [+] │
│   Side    ├─────────────────────────────────────────────────────┤
│   Panel   │                                                     │
│           │              Tool Content Area                      │
│  ┌─────┐  │                                                     │
│  │Tools│  │  ┌─────────────────────────────────────────────┐   │
│  └─────┘  │  │ Target Input                          [RUN] │   │
│           │  ├─────────────────────────────────────────────┤   │
│  Info     │  │ Options Panel                               │   │
│  Gathering│  ├─────────────────────────────────────────────┤   │
│           │  │ Command Preview                             │   │
│  Web      │  ├─────────────────────────────────────────────┤   │
│  Scanning │  │                                             │   │
│           │  │           Output Area                       │   │
│  Crackers │  │                                             │   │
│           │  │                                             │   │
│  Settings │  └─────────────────────────────────────────────┘   │
│           │                                                     │
├───────────┴─────────────────────────────────────────────────────┤
│  Status Bar                                   [Notifications] 🔔│
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Sidepanel Specification

| Element | Description |
|---------|-------------|
| Tool Categories | Collapsible sections grouping related tools |
| Tool Buttons | Clickable buttons to open each tool |
| Settings Button | Access to application settings |
| Collapse Toggle | Expand/collapse entire sidepanel |

### 6.3 Tool View Layout

All tools follow a consistent layout pattern:

| Section | Components |
|---------|------------|
| Header | Category › Tool Name |
| Target Input | Text field + File browser + RUN/STOP buttons |
| Options Panel | Tool-specific configuration options |
| Command Preview | Read-only display of generated command |
| Output Area | Real-time tool output with copy button |

### 6.4 Color Scheme

| Element | Color Code | Usage |
|---------|------------|-------|
| Background (Primary) | #1E1E1E | Main window background |
| Background (Input) | #252526 | Input fields, panels |
| Text (Primary) | #D4D4D4 | Main text |
| Accent (Blue) | #58A6FF | Success, info messages |
| Accent (Green) | #10B981 | Positive results |
| Accent (Orange) | #FF6B35 | Warnings, buttons |
| Accent (Red) | #EF4444 | Errors, critical |
| Accent (Yellow) | #FACC15 | Important notices |
| Border | #3E3E42 | Element borders |

---

## 7. Tool Functional Specifications

### 7.1 Information Gathering Tools

#### 7.1.1 Whois

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | Domain registration information lookup |
| **Input** | Domain name or IP address |
| **Output** | Registration details, contacts, dates |
| **Batch Support** | Yes (file input) |
| **Output File** | `Logs/whois.txt` |

#### 7.1.2 Dig

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | DNS record queries |
| **Input** | Domain name |
| **Query Types** | A, AAAA, MX, NS, TXT, SOA, PTR, AXFR, ANY |
| **Options** | +trace, +short, custom nameserver |
| **Output File** | `Logs/dig.txt` |

#### 7.1.3 DNSRecon

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | Advanced DNS enumeration |
| **Input** | Domain name |
| **Scan Modes** | STD, AXFR, RVL, GOO, BING, SNOOP, BRT, ZWALK |
| **Options** | Wordlist for brute-force |
| **Output File** | `Logs/dnsrecon.txt` |

#### 7.1.4 Subfinder

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | Subdomain discovery |
| **Input** | Domain name or file |
| **Options** | Threads, recursive, all sources, config file |
| **Batch Support** | Yes |
| **Output File** | `Subdomains/subfinder.txt` |

#### 7.1.5 Amass

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | Subdomain enumeration |
| **Input** | Domain name |
| **Modes** | Enumeration, Intel |
| **Options** | Passive/Active, brute force, timeout, config |
| **Requires Root** | Optional (for active mode) |
| **Output File** | `Subdomains/amass.txt` |

#### 7.1.6 WAFW00F

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | Web Application Firewall detection |
| **Input** | URL or domain |
| **Modes** | Standard, Aggressive, Fingerprint All |
| **Options** | Proxy, timeout, no redirects |
| **Detection** | 14+ known WAF signatures |
| **Output File** | `Logs/wafw00f.txt` |

### 7.2 Network Scanning Tools

#### 7.2.1 Nmap

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | Network discovery and security auditing |
| **Input** | IP, CIDR, hostname, or file |
| **Scan Types** | SYN, TCP, UDP, ACK, Window, Maimon |
| **Host Discovery** | List, Ping, No Ping |
| **Options** | Ports, scripts, aggressive, timing, OS detection |
| **Requires Root** | Yes (for SYN scan) |
| **Output Formats** | Normal, XML, Grepable, All |
| **Output File** | `Logs/nmap.*` |

#### 7.2.2 Port Scanner (Built-in)

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | Custom Python port scanner |
| **Input** | IP or hostname |
| **Scan Types** | Connect, SYN, UDP |
| **Options** | Threads, timeout, delay, stealth mode |
| **Features** | OS detection, WAF detection, TLS info, banner grabbing |
| **Output File** | `Logs/portscan.txt` |

#### 7.2.3 HTTPX

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | HTTP/HTTPS probing |
| **Input** | URL, domain, or file |
| **Features** | Status codes, titles, technologies |
| **Batch Support** | Yes |
| **Output Format** | JSON |
| **Output File** | `Httpx/httpx.json` |

### 7.3 Web Scanning Tools

#### 7.3.1 Gobuster

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | Directory and DNS brute-forcing |
| **Modes** | Dir, DNS, VHost, Fuzz, S3 |
| **Input** | URL (Dir), Domain (DNS), or bucket name (S3) |
| **Options** | Wordlist, threads, timeout, extensions, user-agent |
| **Output File** | `Logs/gobuster_<mode>.txt` |

#### 7.3.2 FFUF

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | Web fuzzing |
| **Input** | URL with FUZZ keyword |
| **Features** | Status/size/word/line filtering, regex matching |
| **Options** | Headers, cookies, POST data, recursion |
| **Output Formats** | JSON, text |
| **Output File** | `Logs/ffuf.json`, `Logs/ffuf.txt` |

#### 7.3.3 Nikto

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | Web server vulnerability scanning |
| **Input** | URL or host |
| **Options** | Port, SSL, tuning, evasion, auth |
| **Features** | 6,700+ vulnerability tests |
| **Output File** | `Logs/nikto.txt` |

#### 7.3.4 Nuclei

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | Template-based vulnerability scanning |
| **Input** | URL or file |
| **Options** | Templates, severity filter, tags, rate limit |
| **Features** | 3,000+ community templates |
| **Output Formats** | Text, JSON, JSONL, Markdown |
| **Output File** | `Logs/nuclei.txt` |

#### 7.3.5 SearchSploit

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | Exploit-DB search |
| **Input** | Search term |
| **Options** | Case sensitive, exact match, title only, JSON output |
| **Features** | Grep filter for results |
| **Color Coding** | Remote (red), Local (orange), WebApps (cyan) |

### 7.4 Web Screenshot Tools

#### 7.4.1 Eyewitness

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | Website screenshot capture |
| **Input** | URL, domain, or file |
| **Options** | Threads, timeout, delay, user-agent, proxy |
| **Output** | HTML report with screenshots |
| **Output Directory** | `/tmp/Vajra-results/eyewitness_<target>_<timestamp>/` |

### 7.5 Password Cracking Tools

#### 7.5.1 Hashcat

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | GPU/CPU hash cracking |
| **Input** | Hash file or direct hash |
| **Hash Types** | 180+ supported |
| **Attack Modes** | Straight, Combination, Brute-force, Hybrid |
| **Options** | Wordlist, rules, workload profile, device selection |
| **Output File** | `Logs/hashcat.txt` |

#### 7.5.2 John The Ripper

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | Password cracking |
| **Input** | Hash file or direct hash |
| **Hash Formats** | 200+ supported |
| **Attack Modes** | Wordlist, Incremental, Single, Mask, External |
| **Options** | Format, wordlist, rules, mask |
| **Output File** | `Logs/john.txt` |

#### 7.5.3 Hydra

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | Network service brute-forcing |
| **Input** | Target host/IP |
| **Services** | 25+ (SSH, FTP, HTTP, SMB, RDP, etc.) |
| **Options** | Username/list, password/list, tasks, SSL, proxy |
| **Features** | HTTP form attack support |
| **Output File** | `Logs/hydra.txt` |

#### 7.5.4 Hash Finder (Built-in)

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | Hash type identification |
| **Input** | Hash string |
| **Detection** | 200+ hash types |
| **Features** | Prefix matching, length-based detection |
| **Output** | Most probable hash types ranked |

#### 7.5.5 Dencoder (Built-in)

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | Encoding/decoding utility |
| **Operations** | 60+ (Base64, URL, Hex, HTML, JWT, hashes, etc.) |
| **Features** | Auto-detect encoding, live processing |
| **Shortcuts** | Ctrl+D for auto-detect |

### 7.6 File Analysis Tools

#### 7.6.1 Strings (Built-in)

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | Binary string extraction |
| **Input** | Any file (binary, executable) |
| **Encodings** | ASCII, UTF-16LE, UTF-16BE, UTF-8 |
| **Options** | Minimum length, hex offsets, context view |
| **Pattern Detection** | URLs, IPs, emails, paths, registry keys, Base64, crypto keywords |
| **Features** | Search/filter, statistics dashboard |

### 7.7 Automation Tools

#### 7.7.1 Automation Pipeline

| Attribute | Specification |
|-----------|---------------|
| **Purpose** | Automated reconnaissance workflow |
| **Input** | Domain name |
| **Pipeline Steps** | Whois → Subfinder → Amass → Httpx → Nmap → Report |
| **Controls** | Skip step, Stop pipeline |
| **Output** | HTML report with all findings |

---

## 8. Input/Output Specifications

### 8.1 Target Input Formats

| Format | Example | Supported Tools |
|--------|---------|-----------------|
| Single Domain | example.com | All |
| Single IP | 192.168.1.1 | Nmap, Port Scanner, Hydra |
| CIDR Range | 10.0.0.0/24 | Nmap |
| URL | <https://example.com> | FFUF, Nikto, Nuclei |
| File (line-separated) | /path/to/targets.txt | Whois, Subfinder, HTTPX |

### 8.2 Output Directory Structure

```
/tmp/Vajra-results/
└── <target>_<DDMMYYYY_HHMMSS>/
    ├── Logs/
    │   ├── whois.txt
    │   ├── dig.txt
    │   ├── dnsrecon.txt
    │   ├── nmap.xml
    │   ├── nmap.txt
    │   ├── gobuster_dir.txt
    │   ├── ffuf.json
    │   ├── nikto.txt
    │   ├── nuclei.txt
    │   ├── wafw00f.txt
    │   ├── hashcat.txt
    │   ├── john.txt
    │   ├── hydra.txt
    │   └── portscan.txt
    ├── Subdomains/
    │   ├── subfinder.txt
    │   └── amass.txt
    ├── Httpx/
    │   └── httpx.json
    ├── Reports/
    │   └── final_report.html
    └── JSON/
        └── final.json
```

### 8.3 Report Output Format

The HTML report contains:

- Executive summary
- Whois information
- Discovered subdomains
- HTTP probing results
- Open ports and services
- Identified vulnerabilities
- Recommendations

---

## 9. Use Cases

### UC-001: Domain Reconnaissance

| Attribute | Description |
|-----------|-------------|
| **Actor** | Penetration Tester |
| **Goal** | Gather intelligence on target domain |
| **Preconditions** | VAJRA running, target domain known |
| **Steps** | 1. Open Automation tool<br>2. Enter target domain<br>3. Click RUN<br>4. Wait for pipeline completion<br>5. Review HTML report |
| **Postconditions** | Complete reconnaissance data in organized directory |

### UC-002: Web Application Fuzzing

| Attribute | Description |
|-----------|-------------|
| **Actor** | Security Researcher |
| **Goal** | Discover hidden endpoints and parameters |
| **Preconditions** | Target URL known, wordlist available |
| **Steps** | 1. Open FFUF tool<br>2. Enter URL with FUZZ keyword<br>3. Configure filters<br>4. Specify wordlist<br>5. Click RUN<br>6. Analyze results |
| **Postconditions** | List of discovered endpoints |

### UC-003: Password Hash Cracking

| Attribute | Description |
|-----------|-------------|
| **Actor** | IT Administrator |
| **Goal** | Audit password strength |
| **Preconditions** | Hash file obtained, wordlist available |
| **Steps** | 1. Open Hash Finder<br>2. Identify hash type<br>3. Open Hashcat<br>4. Select hash type and wordlist<br>5. Click RUN<br>6. Review cracked passwords |
| **Postconditions** | Weak passwords identified |

### UC-004: Network Vulnerability Scan

| Attribute | Description |
|-----------|-------------|
| **Actor** | Security Administrator |
| **Goal** | Identify network vulnerabilities |
| **Preconditions** | Target IP range authorized |
| **Steps** | 1. Open Nmap<br>2. Enter target CIDR<br>3. Enable scripts and service detection<br>4. Click RUN<br>5. Open Nuclei<br>6. Scan discovered hosts<br>7. Review findings |
| **Postconditions** | Vulnerability report generated |

---

## 10. Error Handling

### 10.1 Error Categories

| Category | Handling |
|----------|----------|
| Tool Not Found | Display error message with installation instructions |
| Permission Denied | Prompt for sudo/privilege escalation |
| Network Error | Display connection failure message |
| Invalid Input | Highlight field, show validation message |
| Process Timeout | Allow user to stop or wait |
| File Access Error | Display path and permission information |

### 10.2 Error Display

- **Toast Notifications**: Brief errors (3-5 seconds visibility)
- **Output Area**: Detailed error messages with color coding (red)
- **Dialog Boxes**: Critical errors requiring user action

---

## 11. Security Considerations

### 11.1 Ethical Use

- Tool is intended for authorized security testing only
- Users are responsible for obtaining proper authorization
- Output may contain sensitive information

### 11.2 Credential Handling

- Sudo passwords stored in memory only (not persisted)
- Passwords cleared on application close
- No credential caching to disk

### 11.3 Output Security

- Results stored in `/tmp/` (cleared on reboot)
- Users should secure or delete sensitive outputs
- Reports may contain confidential target information

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 2026 | VAJRA Team | Initial specification |

---

*This document provides a functional specification for VAJRA and should be maintained alongside software updates.*
