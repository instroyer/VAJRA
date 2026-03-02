<div align="center">

<img src="Resources/logo.png" alt="VAJRA Logo" width="150"/>

# VAJRA — Official Documentation
### Complete User Guide v1.0.0

[![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg)](#)
[![Platform](https://img.shields.io/badge/Platform-Linux-1c7ed6.svg?logo=linux&logoColor=white)](#)

[← Back to README](README.md)

</div>

---

## 📑 Table of Contents

- [Introduction](#-introduction)
- [Getting Started](#-getting-started)
- [The GUI — Complete Interface Guide](#-the-gui--complete-interface-guide)
  - [Main Window Layout](#main-window-layout)
  - [Sidebar Navigation](#sidebar-navigation)
  - [Tab System](#tab-system)
  - [Status Bar](#status-bar)
  - [Dashboard](#dashboard)
  - [Command Palette](#command-palette)
  - [Integrated Terminal](#integrated-terminal)
  - [Notification System](#notification-system)
  - [Session Management](#session-management)
  - [Welcome Screen](#welcome-screen)
- [Tool Interface — Anatomy of a Tool](#-tool-interface--anatomy-of-a-tool)
- [Tool Arsenal & Features](#-tool-arsenal--features)
  - [Automation](#-automation)
  - [Info Gathering](#-info-gathering)
  - [Subdomain Enumeration](#-subdomain-enumeration)
  - [Live Subdomains](#-live-subdomains)
  - [Port Scanning](#-port-scanning)
  - [Web Screenshots](#-web-screenshots)
  - [Web Scanning](#-web-scanning)
  - [Web Injection](#-web-injection)
  - [Vulnerability Scanner](#-vulnerability-scanner)
  - [Cracker](#-cracker)
  - [Payload Generator](#-payload-generator)
  - [File Analysis](#-file-analysis)
  - [OSINT](#-osint)
- [Output Structure](#-output-structure)
- [Keyboard Shortcuts Reference](#-keyboard-shortcuts-reference)
- [Settings & Configuration](#-settings--configuration)
- [Sample Reports](#-sample-reports)

---

## 🧭 Introduction

VAJRA is a professional, GUI-based offensive security platform designed for penetration testers, bug bounty hunters, and red teamers. Rather than juggling 20 open terminal windows, VAJRA brings every tool into one clean, tabbed interface — with real-time output streaming, automatic result organization, and keyboard shortcuts for every action.

The platform is built around three principles:

**Transparency** — You always see the exact CLI command that will run before you press RUN. There are no hidden flags or unexpected behaviours.

**Organization** — Every scan result is automatically saved to a timestamped folder (`~/Vajra-results/<target>_<timestamp>/Logs|Reports|JSON`). You never lose a result.

**Speed** — The Command Palette (`Ctrl+K`), per-tool keyboard shortcuts (`Ctrl+R` to run, `Ctrl+Q` to stop), and the tab system let you navigate entirely by keyboard. A full recon chain that would take 45 minutes of manual setup runs in minutes with the Automation Pipeline.

---

## 🚀 Getting Started

### Running VAJRA

```bash
chmod +x vajra
./vajra
```

For tools that require raw socket access (e.g., Nmap SYN scans, OS detection):

```bash
sudo ./vajra
```

### Installing External Tools

VAJRA's **Tool Installer** handles all dependency management automatically:

1. Open VAJRA.
2. Go to **Settings → Tool Installer** tab.
3. Click **"Check Dependencies"**.
4. VAJRA detects your Linux package manager (`apt`, `pacman`, `dnf`) and installs all missing tools in one click.

---

## 🖥️ The GUI — Complete Interface Guide

### Main Window Layout

The VAJRA interface is organized into four zones that are always present:

```
┌─────────────────────────────────────────────────┐
│   ☰  VAJRA — Offensive Security Platform    🔔  │  ← Title Bar
├──────────┬──────────────────────────────────────┤
│          │                                      │
│ SIDEBAR  │        TAB AREA (Tool Views)         │
│ (260px)  │                                      │
│          │                                      │
├──────────┴──────────────────────────────────────┤
│          TERMINAL DRAWER (hidden by default)    │  ← Toggle: Ctrl+`
├─────────────────────────────────────────────────┤
│  📊  Dashboard         🖥 Terminal   💾 Session  │  ← Status Bar
└─────────────────────────────────────────────────┘
```

Every divider between zones is a draggable splitter handle, so you can resize the sidebar and terminal drawer freely. The title bar's **☰** button shows/hides the sidebar, and the **🔔** button opens/closes the notification panel.

---

### Sidebar Navigation

The sidebar is your primary tool launcher. It is 260px wide and organized into collapsible category groups. Each category has a ▶/▼ chevron button — click it to collapse or expand that category's tool list. Tools within each category are listed alphabetically.

Click any tool name to open it in a new tab. The tool button stays highlighted while its tab is open, giving you an instant visual of what is running. The **⚙ Settings** button at the very bottom of the sidebar opens the Settings tab.

If you prefer the keyboard, press `Ctrl+K` to open the Command Palette and type any tool name — it is faster than scrolling the sidebar for tools you use frequently.

**Full Category Map:**

| # | Category | Tools |
|---|---|---|
| 1 | 🤖 Automation | Automation |
| 2 | 📡 Info Gathering | Whois, Dig, DNSRecon, WAFW00F, SearchSploit |
| 3 | 🌐 Subdomain Enumeration | Subfinder, Amass, theHarvester, Sublist3r, Chaos |
| 4 | 🟢 Live Subdomains | Httpx |
| 5 | 🔍 Port Scanning | Nmap, Port Scanner |
| 6 | 📸 Web Screenshots | Eyewitness |
| 7 | 🕸️ Web Scanning | FFUF, Gobuster |
| 8 | 💉 Web Injection | SQLi Hunter, Web Fuzzer, API Tester, Crawler |
| 9 | 🔓 Vulnerability Scanner | Nuclei, Nikto |
| 10 | 🔐 Cracker | Hashcat, John, Hydra, Hash Finder, Dencoder |
| 11 | 🚀 Payload Generator | MSFVenom, ShellForge |
| 12 | 📄 File Analysis | Strings |
| 13 | 🔎 OSINT | HTTrack |

---

### Tab System

Every tool, the Dashboard, and Settings open as independent tabs. You can have as many tools open at the same time as you need — they run in parallel, each managing its own process.

Tabs are **moveable** by dragging. They are **closeable** by clicking the `✕` on each tab. When a tab is closed, any still-running process in that tab is stopped cleanly before the tab is removed. Tabs are **deduplicated** — if you click a tool that is already open, VAJRA switches to its existing tab rather than opening a duplicate.

When all tabs are closed, the Welcome Screen appears automatically so you are never left with a blank window.

---

### Status Bar

The thin bar at the bottom of the window has three elements:

| Element | Action |
|---|---|
| **📊 Dashboard** (left) | Opens or switches to the Dashboard tab |
| **🖥 Terminal** (right) | Shows or hides the terminal drawer. Icon turns accent-colored when the terminal is open |
| **💾 Session** (right) | Opens a menu with Save Session and Load Session options |

---

### Dashboard

The Dashboard is the home screen you see when VAJRA first opens. Open it any time by clicking the **📊** button in the status bar.

**Live System Gauges** — Two circular arc charts update every 2 seconds:
- **CPU Usage** — current processor load percentage
- **RAM Usage** — current memory usage percentage

**Status Cards** — Click any card value to copy it to your clipboard instantly:
- **Active Processes** — how many tool tabs are currently open
- **Local IP Address** — your machine's outbound IP, auto-detected via the default route

**Quick Action:**
- **Manage Tools** → Opens Settings at the Tool Installer tab

---

### Command Palette

**Shortcut:** `Ctrl+K`

The Command Palette is a Spotlight-style search overlay that appears centered on your screen. It is the fastest way to navigate VAJRA — faster than the sidebar for tools you use regularly.

Type any of the following to trigger an action and press Enter:

| What to type | Result |
|---|---|
| Tool name (`nmap`, `hydra`, `nuclei`, etc.) | Opens that tool in a new tab |
| `dashboard` | Switches to the Dashboard tab |
| `settings` | Opens the Settings tab |
| `terminal` | Toggles the terminal drawer |
| `sidebar` | Shows or hides the sidebar |
| Theme name (`dark`, `light`, `orange`, `one dark`) | Switches to that theme instantly |
| `quit` | Closes VAJRA |

Press **Escape** or click anywhere outside the palette to dismiss it without taking action.

---

### Integrated Terminal

**Shortcut:** `Ctrl+`` ` or the **🖥** button in the status bar.

The terminal drawer slides up from the bottom of the window. Drag the splitter handle between the terminal and the tab area to resize it. The terminal runs a real shell session (`bash`) with full support for pipes, redirects, aliases, and environment variables.

**Features:**

| Feature | Description |
|---|---|
| **`cd` command** | Changes the terminal's working directory, tracked between commands |
| **`clear` command** | Clears all output from the terminal screen |
| **Command history** | Press `↑` and `↓` to cycle through previous commands |
| **Live output** | Output streams as it is produced — the interface never freezes |
| **Colored prompt** | Displays `user@hostname:~/current/path$` |
| **Kill button** | Stops the currently running command immediately |

Only one command can run at a time. If you type while a command is running, the terminal shows a warning asking you to wait or stop the current command first.

---

### Notification System

The **🔔 bell button** in the top-right corner opens the notification panel. Notifications appear as toast-style popups for events like scan completion, value copied to clipboard, and scan errors. You can disable notifications entirely in **Settings → General → Notifications**.

---

### Session Management

The **💾 Session** button in the status bar opens a menu with two options:

**Save Session (`Ctrl+S`)** — Exports the current workspace state to a JSON file, including:
- Names of all open tool tabs
- The currently active tab
- Current theme selection
- Whether the terminal drawer is open or closed
- Whether the sidebar is visible

**Load Session (`Ctrl+O`)** — Opens a file picker to restore a saved session. VAJRA reopens all saved tool tabs and restores your theme and layout exactly as they were.

**Autosave** — When you close VAJRA, it automatically saves your workspace to `~/.vajra/sessions/autosave.json` so you never fully lose your state.

---

### Welcome Screen

The Welcome Screen appears on first launch and whenever all open tabs are closed. It provides quick-start buttons to navigate to the Dashboard or open the sidebar and start picking tools.

---

## 🔬 Tool Interface — Anatomy of a Tool

Every tool in VAJRA is laid out as a horizontal two-panel split:

```
┌─────────────────────────────┬──────────────────────────────┐
│  CATEGORY  ·  TOOL NAME     │                              │
│  ─────────────────────────  │                              │
│  Target Input      [📁]     │   OUTPUT PANEL               │
│                             │                              │
│  ┌── Configuration Group ─┐ │   Live HTML output streams   │
│  │  Options, dropdowns,   │ │   here as the tool runs.     │
│  │  checkboxes, spinboxes │ │                              │
│  └───────────────────────┘ │   Color-coded:               │
│                             │   🔵 Info  ⚪ Raw output     │
│  [  RUN ▶  ]  [  STOP ■  ] │   🟥 Errors  🟩 Saved path  │
│                             │                              │
│  Command preview: nmap ...  │                              │
└─────────────────────────────┴──────────────────────────────┘
                              ↑ Drag splitter to resize
```

**Elements explained:**

| Element | Description |
|---|---|
| **Category · Tool Name** | Two-line header at the top of the input panel |
| **Target Input + 📁** | Type a target or click 📁 to select a `.txt` file for batch mode |
| **RUN button** | Starts the tool. Shows a loading spinner while running |
| **STOP button** | Stops the currently running process (disabled when idle) |
| **Command Preview** | Read-only field. Shows the exact CLI command that will run. Updates live as you change any option |
| **Output Panel** | Styled HTML output area — scroll to review results |
| **Splitter** | Drag the divider to give more space to what you need |

**What the Target Input accepts:**

| Format | Example |
|---|---|
| Domain | `example.com` |
| IP Address | `192.168.1.1` |
| CIDR Range | `10.0.0.0/24` |
| File path | `/home/user/targets.txt` → enables batch mode |

---

## 🛠️ Tool Arsenal & Features

---

### 🤖 Automation

#### Automation Pipeline

The Automation Pipeline is the most powerful feature in VAJRA. It is designed for bug bounty hunters and penetration testers who want a complete reconnaissance chain executed automatically, from a single domain all the way to a structured vulnerability report — with zero manual intervention between steps.

The pipeline typically completes a full recon chain in **30–60 minutes** for a medium-sized target, a process that would take several hours if done manually across separate terminal sessions. It handles deduplication, cross-tool data passing, and report generation automatically.

**Workflow Stages:**

1. **Intelligence Gathering** — Runs `whois`, `dig`, and `wafw00f` to collect registration data, DNS records, and WAF information.
2. **Subdomain Discovery** — Runs `subfinder`, `theHarvester`, `chaos`, and `sublist3r` in parallel. Results are merged and deduplicated.
3. **Live Host Probing** — Passes the merged subdomain list to `httpx` to filter down to live hosts only.
4. **Port & Service Scanning** — Runs `nmap` on the live host list to discover open ports and running services.
5. **Vulnerability Scanning** — Passes the services and URLs to `nuclei` for template-based CVE/misconfiguration detection.
6. **Report Generation** — Generates a consolidated HTML report in the `Reports/` directory with all findings organized by severity.

**Pros:**
- Saves hours of manual tool chaining and copy-pasting between tools.
- Automatic deduplication means no duplicate subdomains or URLs polluting your results.
- End-to-end pipeline in a single click — ideal for initial recon on new bug bounty targets.
- The generated HTML report is professional-grade and shareable with clients or teams.

**Cons:**
- Less flexible than running individual tools manually if you need specific flags per tool.
- A very broad target may produce thousands of results that require manual triage after the pipeline completes.

---

### 📡 Info Gathering

#### Whois

Whois lookups are the first thing a penetration tester does on a new target. In 30 seconds, you get the domain's registrar, registration date, expiry date, registrant contact details, and nameservers — information that can reveal the hosting provider, technology stack hints, and the organization's internal structure.

VAJRA's Whois tool supports **batch mode**: supply a `.txt` file of targets and it processes each one sequentially, saving individual output files per target in the standard result directory.

**GUI Options:**

| Option | Description |
|---|---|
| **Target Input** | Enter a domain name or IP address, or select a `.txt` file for batch processing |

**Output:** Saved to `~/Vajra-results/<target>_<timestamp>/whois.txt`

---

#### Dig

Dig is the go-to tool for DNS analysis. VAJRA wraps the full DNS record enumeration capability of `dig` in a clean dropdown interface, eliminating the need to remember record type flags.

**GUI Options:**

| Option | Description |
|---|---|
| **Target** | Domain name to query |
| **Record Type** | A, AAAA, MX, NS, SOA, TXT, CNAME, PTR, ANY |
| **DNS Server** | Optional custom DNS server (e.g., `8.8.8.8`) |

**Pros:** Instant, precise DNS record retrieval. Useful for verifying zone configuration, discovering mail servers, and finding TXT records for SPF/DKIM analysis.

---

#### DNSRecon

DNSRecon goes deeper than Dig. It supports zone transfers, reverse lookups, brute-force enumeration, and search-engine scraping — all from one tool. VAJRA exposes every scan mode as a radio button selection.

**GUI Options:**

| Option | Description |
|---|---|
| **Target** | Domain name or IP/CIDR for reverse lookups |
| **Standard (STD)** | Default DNS enumeration |
| **Zone Transfer (AXFR)** | Attempts a DNS zone transfer — reveals all records if misconfigured |
| **Reverse Lookup (PTR)** | Reverse DNS for an IP or range |
| **Google Enumeration (GOO)** | Scrapes Google for subdomain information |
| **Bing Enumeration (BING)** | Scrapes Bing for subdomains |
| **Cache Snooping (SNOOP)** | DNS cache snooping attack |
| **Dictionary Brute Force (BRT)** | Subdomain brute-force using a wordlist |
| **Zone Walk (WALK)** | DNSSEC zone walking |
| **Wordlist** | Required when BRT is selected |

**Pros:** Zone transfers against misconfigured DNS servers can expose your entire subdomain list instantly. The brute-force mode complements passive tools like Subfinder.

---

#### WAFW00F

Before testing a web application, you need to know if a WAF is protecting it. Sending SQLi or XSS payloads into a Cloudflare-protected site without knowing will just get your IP rate-limited. WAFW00F fingerprints the WAF type so you can adjust your testing strategy.

**GUI Options:**

| Option | Description |
|---|---|
| **Target** | Domain or URL to probe |

**What it detects:** Cloudflare, AWS WAF, Akamai, Imperva, Sucuri, Incapsula, F5 BIG-IP, ModSecurity, Barracuda, and 85+ more WAF signatures.

---

#### SearchSploit

SearchSploit queries your local offline copy of the Exploit-DB database. After service discovery (e.g., "Apache 2.4.49"), you search here first to find known public exploits before even trying manual testing.

**GUI Options:**

| Option | Description |
|---|---|
| **Search Term** | Software name, version, CVE number, or keyword |

**Pros:** Fully offline — no internet required. Results include local file paths so you can immediately read exploit code. **Cons:** Only covers exploits that have been submitted to Exploit-DB.

---

### 🌐 Subdomain Enumeration

#### Subfinder

Subfinder is the fastest passive subdomain discovery tool available. It queries 40+ data sources simultaneously — including certificate transparency logs, DNS passive databases, VirusTotal, Shodan, and more — and aggregates unique subdomains within seconds.

For a medium-sized company, Subfinder often discovers **200–800 subdomains** in under 2 minutes, a task that would take hours manually querying each source.

**GUI Options:**

| Option | Flag | Description |
|---|---|---|
| **Target** | `-d` | Domain to enumerate |
| **Threads** | `-t` | Concurrent goroutines (default: 10, max: 1000) |
| **Recursive** | `-recursive` | Recursively enumerate discovered subdomains |
| **All Sources** | `-all` | Use all available sources including paid ones |
| **Silent** | `-silent` | Output only discovered subdomains (no info messages) |
| **Config File** | `-config` | Path to a custom Subfinder configuration file with API keys |

**Pros:** Extremely fast, highly comprehensive, and API key-configurable for even deeper coverage with paid sources.
**Cons:** Passive only — will not discover subdomains that have never appeared in public data.

**Output:** Saved to `~/Vajra-results/<target>_<timestamp>/subfinder_results.txt`

---

#### Amass

Amass is a deeper, slower, and more exhaustive attack surface mapping tool. Unlike Subfinder's pure passive approach, Amass can perform active DNS brute-forcing, ASN enumeration, certificate transparency crawling, and graph-based relationship mapping.

**GUI Options:**

| Option | Flag | Description |
|---|---|---|
| **Target** | `-d` | Domain |
| **Mode** | — | `enum` (subdomain enumeration) or `intel` (intelligence gathering) |
| **Timeout** | `-timeout` | Max run time in minutes (0 = no limit) |
| **Config File** | `-config` | Path to Amass config with API keys |
| **Passive** | `-passive` | Only passive data collection |
| **Active** | `-active` | Active DNS enumeration techniques |
| **Brute Force** | `-brute` | DNS brute-force subdomain discovery |
| **Show IPs** | `-ip` | Include IP addresses in output |
| **Show Sources** | `-src` | Show data source for each result |

**Pros:** The most thorough subdomain discovery tool available. Produces a graph of how assets relate to each other.
**Cons:** Slow — full runs on large targets can take 30+ minutes. Configure API keys for best results.

**Output:** Saved to `~/Vajra-results/<target>_<timestamp>/amass_results.txt`

---

#### theHarvester

theHarvester collects publicly available intelligence about a target from search engines, LinkedIn, PGP servers, and security databases simultaneously. It is especially powerful for gathering **email addresses** — a critical asset for phishing simulations and social engineering assessments.

**GUI Options:**

| Option | Flag | Description |
|---|---|---|
| **Target** | `-d` | Domain or company name |
| **Data Source** | `-b` | Source to query: `all`, `google`, `bing`, `linkedin`, `crtsh`, `virustotal`, `shodan`, `netlas`, `duckduckgo`, `hunter`, `securitytrails`, and more. Also editable — type custom sources. |
| **Limit Results** | `-l` | Max results to retrieve (default: 500, max: 10000) |
| **DNS Brute Force** | `-c` | Perform DNS brute-force on discovered subdomains |
| **DNS Resolve** | `-r` | Resolve discovered subdomains to IPs |
| **Take Screenshots** | `--screenshot` | Capture screenshots of discovered live hosts |

> **Note:** Some sources (Shodan, Hunter.io, SecurityTrails) require API keys configured in `~/.theHarvester/api-keys.yaml` to return results.

**Pros:** Gathers emails, subdomains, hosts, and IPs from a single run. Excellent for OSINT and pre-engagement intelligence.
**Cons:** Results vary significantly between sources. Free sources return fewer results than API-authenticated ones.

---

#### Sublist3r

Sublist3r enumerates subdomains using traditional search engine scraping — Google, Bing, Yahoo, Baidu, Ask, Netcraft, DNSdumpster, and Virustotal. It completes quickly and serves as a good complement to Subfinder.

**GUI Options:**

| Option | Description |
|---|---|
| **Target** | Domain to enumerate |

**Pros:** Fast, simple, no API keys required.
**Cons:** Search engine scraping is increasingly limited by rate limits and bot detection.

---

#### Chaos

Chaos queries ProjectDiscovery's publicly available internet-wide dataset — a massive database of subdomains collected from continuous scans of the internet. For targets that participate in bug bounty programs, the results are often the most comprehensive available.

**GUI Options:**

| Option | Flag | Description |
|---|---|---|
| **Target** | `-d` | Domain to query |
| **PDCP API Key** | `-key` | Your ProjectDiscovery API key (free registration) |
| **Silent Mode** | `-silent` | Output only subdomains, suppress info messages |
| **JSON Output** | `-json` | Output results in JSON format |
| **Count Only** | `-count` | Return only the count of subdomains, not the list |
| **New Subdomains** | `-new` | Show only newly discovered subdomains since last query |

**Pros:** One of the fastest and most comprehensive sources for bug bounty targets. The `-new` flag is unique — shows only what has changed since your last scan.
**Cons:** Requires a free PDCP API key. Coverage depends on whether ProjectDiscovery has scanned the target.

---

### 🟢 Live Subdomains

#### Httpx

After subdomain enumeration, you typically have hundreds to thousands of discovered subdomains — but most will be dead, parked, or inactive. Httpx probes each one rapidly to identify which ones actually respond to HTTP/HTTPS, reducing your attack surface to only what matters.

Running Httpx on a list of 1,000 subdomains takes about 30 seconds and immediately tells you which ones are alive, their status codes, page titles, server types, and technologies — replacing hours of manual checking.

**GUI Options:**

| Option | Flag | Description |
|---|---|---|
| **Target** | `-l` | Domain, IP, or path to a `.txt` file (subdomain list) |
| **Threads** | `-threads` | Number of concurrent connections (default: 50, max: 1000) |
| **Title** | `-title` | Include page title in output |
| **Status Code** | `-status-code` | Include HTTP status code in output |
| **Tech Detect** | `-tech-detect` | Detect web technologies (frameworks, CMS, CDN) |
| **Follow Redirects** | `-follow-redirects` | Follow HTTP redirects and show final destination |

**Output:** Saved as JSON to `~/Vajra-results/<target>_<timestamp>/Httpx/httpx.json`

---

### 🔍 Port Scanning

#### Nmap

Nmap is the industry standard for network scanning and host discovery. VAJRA's Nmap integration exposes every major option through a structured GUI — scan types, scripts, timing, output format — while showing you the exact command before you run it.

For a penetration tester, Nmap is the first active scan run after subdomain enumeration. It reveals open ports, running services, versions, and operating system details — the foundation for all further exploitation.

**GUI Options:**

**Scan Type:**

| Option | Flag | Description |
|---|---|---|
| SYN Scan | `-sS` | Fast, stealthy (requires root) |
| TCP Connect | `-sT` | Full 3-way handshake (no root required) |
| UDP Scan | `-sU` | Scans UDP ports (slow, requires root) |
| ACK Scan | `-sA` | Maps firewall rules |
| FIN Scan | `-sF` | Stealthy, bypasses some firewalls |

**Host Discovery:**

| Option | Flag | Description |
|---|---|---|
| Default | — | Standard ping + port probing |
| No Ping | `-Pn` | Skip discovery, treat all hosts as up |
| Ping Scan Only | `-sn` | Only discover hosts, skip port scanning |
| List Scan | `-sL` | Only list targets without scanning |

**Detection Options:**

| Option | Flag | Description |
|---|---|---|
| Service Version | `-sV` | Detect service names and version numbers |
| OS Detection | `-O` | Guess operating system (requires root) |
| Aggressive Scan | `-A` | Enables -sV, -O, traceroute, and default scripts |
| Traceroute | `--traceroute` | Map network route to target |

**Port Ranges:** Enter any combination — `80,443`, `1-1024`, `22,80,8080-8090`. Large port ranges are handled automatically.

**NSE Scripts:**

| Option | Description |
|---|---|
| **Script dropdown** | Searchable list loaded from `/usr/share/nmap/scripts/` |
| Common choices | `default`, `vuln`, `auth`, `http-title`, `ssl-heartbleed` |

**Performance Controls:**

| Option | Description |
|---|---|
| **Timing Template** | T1 (stealthiest) to T5 (fastest) — T3 is balanced default |
| **Max Retries** | Number of probe retransmissions |
| **Host Timeout** | Give up on a host after this duration |
| **Max Rate** | Maximum packet rate (packets/second) |
| **Scan Delay** | Minimum delay between probes |

**Output Formats:**

| Option | Description |
|---|---|
| Normal | Human-readable text (`.txt`) |
| Grepable | Machine-parseable format (`.gnmap`) |
| XML | Structured XML for importers (`.xml`) |
| All | Outputs all three formats simultaneously (`-oA`) |
| Terminal Only | No file saved, only displayed in output panel |

---

#### Port Scanner (Custom Engine)

VAJRA's built-in Port Scanner is a native Python async TCP scanning engine. It requires no external installation and is extremely fast due to multi-threaded design. It also provides unique capabilities beyond raw port scanning.

**GUI Options:**

| Option | Description |
|---|---|
| **Target** | Domain, IP, or CIDR range |
| **Ports** | Port ranges to scan (e.g., `1-65535`, `80,443,8080`) |
| **Threads** | Up to 200 concurrent threads |
| **Stealth Mode** | Randomizes port scan order and adds inter-probe delays |
| **Banner Grabbing** | Connects to open ports to retrieve service banners |
| **OS Fingerprinting** | Estimates OS from TTL values (Windows / Linux / Network Device) |
| **WAF Detection** | Sends probe payloads and checks response headers for WAF signatures |

---

### 📸 Web Screenshots

#### Eyewitness

After Httpx reveals which hosts are alive, you still face a list of hundreds of URLs you need to assess. Eyewitness solves this by automatically visiting each URL and saving a screenshot, along with the page title, server headers, and response codes, into a local HTML report.

Scrolling through an Eyewitness report for 500 hosts takes 10 minutes — the equivalent of manually checking each URL in a browser, which would take hours.

**GUI Options:**

| Option | Description |
|---|---|
| **Target** | Single URL or path to a `.txt` file of URLs |
| **Threads** | Concurrent screenshot workers (default: 50) |
| **Timeout** | Per-request timeout in seconds (default: 30s) |
| **Delay** | Wait time before taking screenshot after page load (default: 0s) |
| **Prepend HTTPS** | Automatically add `https://` if no protocol specified |
| **No DNS** | Skip DNS resolution checks |
| **User Agent** | Set a custom browser User-Agent string |
| **Proxy** | Route traffic through a proxy (`ip:port` format) |

**Output:** HTML report with screenshots, headers, and response data, saved in `~/Vajra-results/` with a timestamped folder.

---

### 🕸️ Web Scanning

#### FFUF

FFUF (Fuzz Faster U Fool) is the fastest web fuzzer available. It is used for directory brute-forcing, parameter discovery, virtual host enumeration, and input field fuzzing. The `FUZZ` keyword in the target URL or request body marks the position where wordlist payloads are injected.

FFUF can test a 10,000-word wordlist against a target in under 60 seconds, the same task that would take 30+ minutes with older tools like DirBuster.

**GUI Options — Wordlist & Target:**

| Option | Description |
|---|---|
| **Target URL** | Must contain the `FUZZ` keyword (e.g., `http://example.com/FUZZ`) |
| **Wordlist** | Path to a wordlist file (use the 📁 picker or type the path) |

**Tab 1 — HTTP Request:**

| Option | Flag | Description |
|---|---|---|
| **Method** | `-X` | GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS |
| **Follow Redirects** | `-r` | Automatically follow HTTP redirects |
| **Auto-Calibrate** | `-ac` | Auto-detect and filter baseline responses |
| **Headers** | `-H` | Custom request headers (e.g., `"Authorization: Bearer token"`) |
| **Cookies** | `-b` | Session cookies |
| **POST Data** | `-d` | POST body payload (use `FUZZ` keyword here too) |

**Tab 2 — Filters & Matching:**

| Option | Flag | Description |
|---|---|---|
| **Filter Status** | `-fc` | Exclude responses by HTTP status code (e.g., `404,403`) |
| **Match Status** | `-mc` | Only show responses matching these codes (e.g., `200,301`) |
| **Filter Size** | `-fs` | Exclude responses of this byte size |
| **Match Size** | `-ms` | Only show responses of this byte size |
| **Filter Words** | `-fw` | Exclude responses with this word count |
| **Match Words** | `-mw` | Only show responses with this word count |
| **Filter Lines** | `-fl` | Exclude responses with this line count |
| **Match Regex** | `-mr` | Only show responses matching this regex |
| **Filter Regex** | `-fr` | Exclude responses matching this regex |
| **Filter Mode** | `-fmode` | `or` (any filter matches) or `and` (all filters must match) |
| **Match Mode** | `-mmode` | `or` or `and` matching logic |

**Tab 3 — Advanced:**

| Option | Flag | Description |
|---|---|---|
| **Threads** | `-t` | Concurrent requests (default: 40, max: 200) |
| **Delay** | `-p` | Milliseconds between requests (rate limiting) |
| **Rate Limit** | `-rate` | Max requests per second |
| **Timeout** | `-timeout` | Per-request timeout in seconds (default: 10s) |
| **Recursive Fuzzing** | `-recursion` | Automatically fuzz discovered directories |
| **Recursion Depth** | `-recursion-depth` | How deep to recurse (enabled when Recursive is checked) |
| **Extensions** | `-e` | File extensions to append to each wordlist entry (e.g., `.php,.html,.js`) |

---

#### Gobuster

Gobuster is specialized for web directory brute-forcing, DNS subdomain enumeration, virtual host discovery, and AWS S3 bucket enumeration. It is faster than many alternatives because it is written in Go and uses a highly concurrent design.

VAJRA's Gobuster integration provides **5 distinct mode tabs**, each with its own specific options.

**Common Options (all modes):**

| Option | Description |
|---|---|
| **Target** | URL for Dir/VHost/Fuzz modes, domain for DNS, bucket name for S3 |
| **Wordlist** | Path to wordlist file |
| **Threads** | Concurrent connections (default: 10, max: 200) |

**Tab 1 — Dir** (Directory/File brute-forcing):

| Option | Flag | Description |
|---|---|---|
| **Extensions** | `-x` | File extensions to test (e.g., `php,txt,html,jsp`) |
| **Status Blacklist** | `-b` | HTTP status codes to ignore (e.g., `404,403`) |
| **Exclude Length** | `--xl` | Exclude responses of this content length |
| **User Agent** | `-a` | Custom User-Agent string |
| **Expanded** | `-e` | Show full URLs in output |
| **Skip TLS** | `-k` | Skip TLS certificate verification |
| **Follow Redirects** | `-r` | Follow HTTP redirects |
| **Add Slash** | `-f` | Append a slash to each request |

**Tab 2 — DNS** (Subdomain enumeration):

| Option | Flag | Description |
|---|---|---|
| **Show IPs** | `-i` | Include resolved IP addresses in output |
| **Wildcard Force** | `--wildcard` | Force enumeration even if wildcard DNS is detected |

**Tab 3 — VHost** (Virtual host discovery):

| Option | Description |
|---|---|
| **Append Domain** | Append the target domain to each wordlist entry |

**Tab 4 — Fuzz** (Parameter/URL fuzzing with `FUZZ` keyword):

| Option | Description |
|---|---|
| **HTTP Method** | GET, POST, PUT, PATCH, DELETE |
| **Request Body** | Body payload for POST/PUT requests |
| **Cookies** | Session cookies |
| **Header** | Custom HTTP header |
| **Proxy** | Route through proxy (`http://127.0.0.1:8080`) |
| **Exclude Status** | HTTP status codes to hide |
| **Exclude Length** | Response lengths to hide |
| **Delay** | Milliseconds between requests |
| **Skip TLS** | Ignore TLS certificate errors |
| **Retry** | Retry failed requests (configurable count) |

**Tab 5 — S3** (AWS S3 bucket enumeration):

| Option | Description |
|---|---|
| **Max Files** | Maximum files to list per bucket (default: 5) |
| **Skip TLS** | Skip certificate verification |

---

### 💉 Web Injection

#### SQLi Hunter

SQLi Hunter is VAJRA's **native Python SQL injection engine** — it does not require SQLMap or any external dependency. It uses error-based and boolean-blind injection techniques to test whether input fields are vulnerable to SQL injection.

Using a curated payload database (`db/sqlipayload.txt`, 1000+ payloads) and an intelligent testing loop, it can identify vulnerable parameters in minutes rather than the hours a manual approach requires.

**GUI Options:**

| Option | Description |
|---|---|
| **Target URL** | The URL to test (include parameter, e.g., `?id=1`) |
| **HTTP Method** | GET or POST |
| **Custom Payload List** | Optional: use your own payload file instead of the built-in database |
| **Cookie / Session** | Include session cookies for authenticated testing |
| **Headers** | Custom headers (e.g., `Authorization`) |
| **Threads** | Concurrent injection workers |
| **Timeout** | Per-request timeout |

**Pros:** No external dependency, fast, silent operation with clear findings. Great for quick vulnerability confirmation.
**Cons:** Does not perform extraction or dumping — use SQLMap for that after SQLi Hunter confirms a vulnerable parameter.

---

#### Web Fuzzer

The Web Fuzzer is a high-performance payload delivery engine for testing input fields, endpoints, and parameters against large wordlists. Unlike FFUF which is primarily for directory discovery, the Web Fuzzer focuses on payload-based injection testing.

**GUI Options:**

| Option | Description |
|---|---|
| **Target URL** | URL with parameter to fuzz |
| **Wordlist** | Built-in `db/webfuzzers.txt` or browse for custom file (tested with 150k+ line lists) |
| **Threads** | Concurrent request workers |
| **Rate Limit** | Maximum requests per second |
| **Timeout** | Per-request timeout |
| **HTTP Method** | GET or POST |
| **Headers** | Custom request headers |
| **Cookie** | Session cookies for authenticated testing |

---

#### API Tester

The API Tester is built for security auditing of REST and GraphQL APIs. It supports all HTTP methods with structured body payloads and custom headers, making it easy to test every endpoint of a modern web application.

**GUI Options:**

| Option | Description |
|---|---|
| **Target URL** | API endpoint (e.g., `https://api.example.com/v1/user`) |
| **Method** | GET, POST, PUT, DELETE, PATCH |
| **Headers** | Any header key:value pair (Authorization, Content-Type, etc.) |
| **Request Body** | JSON or form-encoded payload |
| **Auth Token** | Bearer token or API key entry |
| **Follow Redirects** | Follow HTTP 301/302 responses |
| **SSL Verification** | Toggle TLS certificate verification |

---

#### Crawler

The Crawler spiders a web application recursively to build a complete site map. It discovers links, forms, JavaScript files, API endpoints, and hidden paths that are not visible from the homepage alone.

**GUI Options:**

| Option | Description |
|---|---|
| **Start URL** | Entry point for the crawl |
| **Depth** | Maximum recursion depth |
| **Threads** | Concurrent crawling workers |
| **Scope** | Restrict to same domain or allow external links |
| **Include** | File extensions or patterns to include |
| **Exclude** | Paths or file types to skip |

---

### 🔓 Vulnerability Scanner

#### Nuclei

Nuclei is the most powerful template-based vulnerability scanner available. It runs thousands of community-maintained YAML templates against your targets, each designed to detect a specific CVE, misconfiguration, exposed panel, or security weakness. The ProjectDiscovery template library covers everything from Log4Shell and Spring4Shell to exposed Git repositories and default credentials.

A full Nuclei scan against a set of live hosts often takes 5–15 minutes and can surface critical vulnerabilities that would take manual researchers days to find.

**GUI Options — 4 Configuration Tabs:**

**Tab 1 — Templates:**

| Option | Flag | Description |
|---|---|---|
| **Template Path** | `-t` | Path to a specific template, a directory of templates, or multiple `.yaml` files (comma-separated). Use the 📁 picker to choose a file or directory. |
| **Auto-Scan** | `-as` | Automatically apply recommended templates based on detected technologies |
| **New Templates** | `-nt` | Run only templates added in the latest Nuclei update |

**Tab 2 — Filters:**

| Option | Flag | Description |
|---|---|---|
| **Severity Checkboxes** | `-s` | Filter to specific severities: Info, Low, Medium, High, Critical |
| **Tags** | `-tags` | Run only templates with these tags (e.g., `cve,rce,xss`) |
| **Exclude Tags** | `-etags` | Skip templates with these tags (e.g., `dos,fuzz`) |

**Tab 3 — Performance:**

| Option | Flag | Default | Description |
|---|---|---|---|
| **Concurrency** | `-c` | 25 | Parallel template executions |
| **Rate Limit** | `-rl` | 150 | Max requests per second |
| **Timeout** | `-to` | 10s | Per-request timeout |

**Tab 4 — Advanced:**

| Option | Flag | Description |
|---|---|---|
| **Proxy** | `-proxy` | Route requests through a proxy (e.g., `http://127.0.0.1:8080`) |
| **Headless** | `-headless` | Enable headless browser for JavaScript-heavy targets |
| **Verbose** | `-v` | Show verbose output including template matches |

**Output Color Coding:**
- 🔵 `[info]` — Informational findings
- 🟡 `[medium]` — Medium severity issues
- 🟠 `[high]` — High severity issues
- 🔴 `[critical]` — Critical vulnerabilities
- 🟢 `[INF]` — Scanner status messages

---

#### Nikto

Nikto is a comprehensive web server scanner that checks for over 6,700 known dangerous files, CGI scripts, outdated server software, and common misconfigurations. It is the most thorough automated web server assessment tool available.

VAJRA's Nikto integration is unique in that it uses **real-time output streaming** (no buffering) for accurate display, and color-codes findings by severity automatically.

**Severity Legend (click the "View Severity Legend" button in the tool):**

| Color | Severity | Examples |
|---|---|---|
| 🔴 Red (Bold) | Critical | SQL Injection, RCE, File Upload, Auth Bypass |
| 🟠 Orange | High | XSS, Information Disclosure, CGI Issues, Directory Traversal |
| 🟡 Yellow | Medium | Missing Headers, Deprecated Features, Cookie Issues |
| 🔵 Blue | Info | Target IP, Server Details, Scan Timestamps |
| 🟢 Green | Low | General findings starting with `+` |

**GUI Options — 3 Configuration Tabs:**

**Tab 1 — Basic:**

| Option | Flag | Description |
|---|---|---|
| **Target URL** | `-h` | URL to scan (e.g., `http://example.com`) |
| **Port** | `-port` | Custom port(s) to scan (e.g., `80,443`) |
| **Force SSL** | `-ssl` | Force SSL for all requests |
| **Follow Redirects** | `-followredirects` | Automatically follow HTTP redirects |
| **VHost** | `-vhost` | Override the Host header (virtual hosting) |
| **Timeout** | — | Per-request timeout in seconds (default: 10s) |
| **Max Time** | `-maxtime` | Stop scan after this duration (e.g., `1h`, `60m`) |
| **Verbose** | `-Display V` | Show verbose scan output |
| **Debug** | `-Display D` | Show debug-level output |

**Tab 2 — Scan Options (Tuning):**

Select which test types to run. If none are selected, all are run by default.

| Code | Test Category |
|---|---|
| 1 | Interesting File / Seen in logs |
| 2 | Misconfiguration / Default File |
| 3 | Information Disclosure |
| 4 | Injection (XSS/Script/HTML) |
| 5 | Remote File Retrieval — Web Root |
| 6 | Denial of Service |
| 7 | Remote File Retrieval — Server Wide |
| 8 | Command Execution / Remote Shell |
| 9 | SQL Injection |
| 0 | File Upload |
| a | Authentication Bypass |
| b | Software Identification |
| c | Remote Source Inclusion |
| d | WebService |
| e | Administrative Console |

Additional options: **No 404 Detection**, **Use Cookies**, **Pause** (seconds between requests).

**Tab 3 — Advanced:**

| Option | Flag | Description |
|---|---|---|
| **User-Agent** | `-useragent` | Custom browser User-Agent string |
| **Proxy** | `-useproxy` | Route through proxy (e.g., `http://proxy:port`) |
| **Auth** | `-id` | HTTP Basic Auth credentials (`username:password`) |
| **Evasion** | `-evasion` | IDS evasion techniques — combine codes (e.g., `1234AB`) |
| **CGI Dirs** | `-Cgidirs` | Custom CGI directories to check (e.g., `/cgi-bin/ /scripts/`) |
| **Root Prepend** | `-root` | Prepend this path to all requests |
| **No DNS Lookup** | `-nolookup` | Skip DNS resolution |
| **Disable SSL** | `-nossl` | Disable SSL entirely |

---

### 🔐 Cracker

#### Hashcat

Hashcat is the world's fastest GPU-accelerated password recovery tool. When you have captured a password hash — from a database dump, an Active Directory extraction, or a network capture — Hashcat is how you crack it.

**GUI Options:**

| Option | Description |
|---|---|
| **Hash Input** | Paste the hash directly or select a hash file |
| **Hash Type** | Select the algorithm from a searchable dropdown (MD5, SHA1, bcrypt, NTLM, WPA2, etc.) |
| **Wordlist / Mask** | Path to wordlist for dictionary attacks, or mask pattern for brute-force |
| **Attack Mode** | Dictionary (0), Brute-Force/Mask (3), Rule-based (0 + rules), Combination (1) |
| **Rules** | Path to a Hashcat rules file |
| **Output File** | Where to save cracked credentials |

**Pros:** GPU acceleration makes Hashcat orders of magnitude faster than CPU-based tools for most hash types. Supports 300+ hash algorithms.

---

#### John (John the Ripper)

John the Ripper is the classic CPU-based password auditor. It automatically identifies hash types and supports wordlist, brute-force, and incremental attack modes. It remains the go-to for slower algorithms where GPU advantages are less significant.

**GUI Options:**

| Option | Description |
|---|---|
| **Hash File** | Path to a hash file |
| **Wordlist** | Path to a wordlist for dictionary attack |
| **Format** | Force a specific hash format (optional — auto-detected if left blank) |
| **Attack Mode** | Wordlist, Incremental, or Single crack |
| **Rules** | Apply Mangling rules to wordlist |

---

#### Hydra

Hydra is the fastest and most flexible network login brute-forcer. It supports over 50 protocols and is essential for testing authentication services across services like SSH, FTP, HTTP login forms, and databases.

**GUI Options:**

| Option | Description |
|---|---|
| **Target** | IP address or hostname |
| **Protocol** | SSH, FTP, HTTP-Form-POST, HTTPS, SMB, RDP, MySQL, PostgreSQL, Telnet, VNC, and 50+ more |
| **Username** | Single username or path to usernames file |
| **Password** | Single password or path to passwords file |
| **Port** | Custom port (auto-selected for most protocols) |
| **Threads** | Concurrent connection workers |
| **Login Form** | For HTTP-Form attacks: URL, form fields, failure string |
| **Stop on First** | Stop after first valid credential found |

---

#### Hash Finder

Hash Finder is a fast, offline hash type identification engine. When you recover a hash from a database dump or system file, you need to know its algorithm before you can crack it. Hash Finder analyzes the hash's length, character set, and structural signatures to identify it.

**GUI Options:**

| Option | Description |
|---|---|
| **Hash Input** | Paste any hash directly into the text field |
| **Identify Button** | Run the identification engine |

**Identification Logic:**
- Analyzes hash length and character composition
- Checks known structural signatures (e.g., `$2y$` = bcrypt, `$1$` = MD5-crypt, `sha1$` = Django SHA1)
- Returns **Most Probable** match and a ranked **Possibilities** list
- Supports **200+ algorithm signatures** including MD5, SHA1, SHA256, SHA512, bcrypt, Argon2, NTLM, LM, JWT, WPA2, BitLocker, PBKDF2, and more

---

#### Dencoder

Dencoder is a universal encoding, decoding, and hashing utility. It is invaluable during web application testing, where you constantly need to encode payloads, decode obfuscated data, and verify hash values.

**GUI Options:**

| Option | Description |
|---|---|
| **Input Text** | Paste any text to encode or decode |
| **Operation** | Select from the operations below |

**Supported Operations:**

| Operation | Description |
|---|---|
| Base64 Encode | Convert text to Base64 |
| Base64 Decode | Decode Base64 back to plaintext |
| Hex Encode | Convert to hexadecimal representation |
| Hex Decode | Convert hex back to text |
| URL Encode | Percent-encode special characters |
| URL Decode | Decode percent-encoded strings |
| HTML Encode | Encode HTML entities (`<`, `>`, `&`) |
| HTML Decode | Decode HTML entities back to characters |
| ROT13 | Caesar cipher with 13-position shift |
| JWT Decode | Inspect JWT header and payload (no key required) |
| MD5 Hash | Generate MD5 hash of input |
| SHA1 Hash | Generate SHA1 hash of input |
| SHA256 Hash | Generate SHA256 hash of input |

Output updates instantly as you type. Click the copy button next to the output to copy to clipboard.

---

### 🚀 Payload Generator

#### MSFVenom

MSFVenom is Metasploit's payload generator. It creates shellcode, binaries, and scripts that establish reverse connections back to your listener. VAJRA's GUI wrapper makes it easy to configure the many options without memorizing the complex flag syntax.

**GUI Options:**

| Option | Flag | Description |
|---|---|---|
| **Payload** | `-p` | Select from a full dropdown of payload types (reverse_tcp, meterpreter, etc.) |
| **Platform** | — | Windows, Linux, Android, macOS, PHP, JSP, Python, Ruby, Java, ASP |
| **Architecture** | — | x86, x64, arm, mips |
| **LHOST** | — | Your listener IP — auto-detected from local network interface |
| **LPORT** | — | Your listener port (default: 4444) |
| **Format** | `-f` | Output format: exe, elf, apk, raw, py, jsp, war, dll, and more |
| **Encoder** | `-e` | Encoder to apply (e.g., `x86/shikata_ga_nai`) |
| **Iterations** | `-i` | How many times to apply the encoder |
| **Template** | `-x` | Inject payload into this legitimate executable |
| **Keep Template Running** | `-k` | Keep the original executable's functionality intact |
| **Output File** | `-o` | Where to save the generated payload |

**Pros:** The most versatile payload generator for standard engagements. Auto-detected LHOST saves time. Encoder support helps bypass basic AV signatures.

---

#### ShellForge

ShellForge is an offline database of over 100 reverse shell and bind shell one-liners. Rather than searching the internet or memorizing syntax, you configure your IP and port once and instantly generate ready-to-use reverse shell commands for any language or environment.

**GUI Options:**

| Option | Description |
|---|---|
| **LHOST** | Your listener IP address |
| **LPORT** | Your listener port number |
| **Shell Type** | Select from the category list: Bash, Python 2/3, Perl, Ruby, PHP, Netcat, Socat, PowerShell, Awk, Java, Lua, HoaxShell (HTTP-based) |
| **Encode: URL** | URL-encode the generated shell for web-based delivery |
| **Encode: Base64** | Base64-encode the shell |
| **Copy** | Copy the generated shell to clipboard |
| **Listener Command** | Displays the exact `nc -lvnp` or `msfconsole` command to run on your machine to catch the shell |

**Pros:** Invaluable during exploitation when you need a specific shell type quickly. The Listener Buddy feature eliminates the need to remember listener syntax. HoaxShell support is great for bypassing firewalls that block standard reverse shells.

---

### 📄 File Analysis

#### Strings

Strings extracts printable character sequences from binary files. When analyzing malware samples, firmware images, or unknown binaries, `strings` is the first step — it reveals embedded URLs, filenames, error messages, API calls, and configuration values that expose the binary's purpose and targets.

**GUI Options:**

| Option | Description |
|---|---|
| **Target File** | Path to the binary file to analyze |
| **Minimum Length** | Minimum character sequence length to extract (default: 4) |
| **Encoding** | String encoding to look for (ASCII, Unicode) |
| **Output** | Results displayed in output panel and saved to `Logs/` |

---

### 🔎 OSINT

#### HTTrack

HTTrack is a website copier that downloads a complete website to your local machine, preserving the directory structure and all links. During security assessments, it is used to study application logic offline, find hidden paths and source code references, and analyze frontend code without triggering server-side rate limits.

**GUI Options:**

| Option | Description |
|---|---|
| **Target URL** | Website to mirror |
| **Depth** | Maximum crawl depth (number of link levels to follow) |
| **Max Connections** | Concurrent download connections |
| **Max Rate** | Bandwidth limit in bytes/second |
| **Include** | Only mirror paths matching this pattern |
| **Exclude** | Skip paths matching this pattern |
| **User Agent** | Custom browser User-Agent for the download |
| **No External** | Only download content from the target domain |

---

## 📁 Output Structure

Every tool in VAJRA follows the same organized output structure. When you run a scan, VAJRA automatically creates a timestamped target directory:

```
~/Vajra-results/
└── example.com_01032026_191500/          ← <target>_<DDMMYYYY_HHMMSS>
    ├── Logs/                              ← Raw tool output files
    │   ├── nmap.txt
    │   ├── subfinder_results.txt
    │   ├── nuclei_results.txt
    │   └── ffuf.json
    ├── JSON/                              ← Structured findings
    │   └── final.json
    ├── Reports/                           ← Generated HTML reports
    │   └── report.html
    └── Screenshots/                       ← Eyewitness captures
```

**For batch/file-input scans** (supply a `.txt` file of targets):
```
~/Vajra-results/
└── targets/                              ← Group name from filename
    ├── example.com_01032026_191500/
    └── target2.com_01032026_191502/
```

> The output root directory is configurable in **Settings → Paths**. Changes are session-only and reset on next launch.

---

## ⌨️ Keyboard Shortcuts Reference

| Action | Shortcut |
|--------|---------|
| **Command Palette** | `Ctrl+K` |
| **Toggle Terminal** | `Ctrl+`` ` |
| **Run Active Tool** | `Ctrl+R` |
| **Stop Active Tool** | `Ctrl+Q` |
| **Clear Output** | `Ctrl+L` |
| **Focus Target Input** | `Ctrl+I` |
| **Save Session** | `Ctrl+S` |
| **Load Session** | `Ctrl+O` |

---

## ⚙️ Settings & Configuration

Open Settings from the sidebar footer **⚙** button or via `Ctrl+K` → "Go to Settings". The panel has four tabs.

### Tab 1 — General

**Notifications** — Toggle scan-completion toast notifications on or off globally. When enabled, a popup appears on the screen whenever a scan completes, even if VAJRA is in the background.

**Theme** — Switch between four built-in themes. The selected theme applies instantly to every element of the interface without requiring a restart.

| Theme | Style |
|---|---|
| **Github Dark** *(default)* | Deep navy backgrounds, electric blue accents, high-contrast text |
| **Github Light** | Clean white backgrounds, red/dark accents — ideal for presentations |
| **One Dark** | Atom-editor-style dark theme with sky blue highlights |
| **Orange Dark** | High-contrast black backgrounds with bold orange fire accents |

### Tab 2 — Paths

**Output Directory** — Set the root folder where all scan results are saved. Defaults to `~/Vajra-results`. This setting is session-only: it resets to the default each time VAJRA is launched.

### Tab 3 — Privileges

Shows your current user privilege level: **User** or **Root**. Root access is required for:
- Nmap SYN scan (`-sS`), UDP scan (`-sU`), and OS detection (`-O`)
- Raw socket operations in the custom Port Scanner

### Tab 4 — Tool Installer

A visual dependency management panel:
- Shows a ✅/❌ status for every external tool VAJRA supports
- **Check Dependencies** scans your system for installed tools
- **Install** auto-installs missing tools using the detected package manager:
  - Debian/Ubuntu: `apt`
  - Arch Linux: `pacman`
  - Fedora/RHEL: `dnf`
  - Go tools: `go install`
  - Python tools: `pip`

**Persistent config stored at:** `~/.vajra/config.json`
**Session files stored at:** `~/.vajra/sessions/`

---

## 📊 Sample Reports

VAJRA's Automation Pipeline generates professional-grade HTML reports:

* 📄 **[Summary Report (PDF)](Sample_Report/Vajra_Summary_Sample_Report.pdf)** — Executive-level overview of findings, organized by severity.
* 📑 **[Full Report (PDF)](Sample_Report/Vajra_Full_Sample_Report.pdf)** — Full technical breakdown with tool outputs, evidence, and recommendations.

---

<div align="center">

**VAJRA v1.0 — Built for security professionals, by Yash Javiya**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue.svg?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/yash--javiya/)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support-FF5E5B.svg?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/yashjaviya)

[← Back to README](README.md)

</div>
