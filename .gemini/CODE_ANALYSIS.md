# VAJRA Offensive Security Platform - Comprehensive Code Analysis

## 📋 Overview

VAJRA (Versatile Automated Jailbreak and Reconnaissance Arsenal) is a **professional-grade offensive security platform** built with PySide6, featuring a modular plugin architecture that integrates **24 penetration testing tools** into a unified graphical interface. The platform supports automated workflows, batch operations, real-time output streaming, and comprehensive result tracking with professional HTML/PDF report generation.

---

## 🏗️ Architecture Overview

### **Application Flow:**
```
main.py → QApplication → MainWindow
                             ↓
                    _discover_tools() (Dynamic Plugin Discovery)
                             ↓
                    ┌────────┴────────┐
                    │                 │
              Sidepanel        QTabWidget
          (Tool Navigation)   (Tool Views)
                    │                 │
            ToolCategory       ToolBase.get_widget()
              Grouping              ↓
                              Tool UI (View Classes)
                                     ↓
                              ProcessWorker (QThread)
                                     ↓
                              Subprocess Execution
```

### **Core Components:**

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `main.py` | Entry point with global styling | Qt message handler, font configuration |
| `core/` | Utilities for file operations, parsing, reporting | fileops.py, jsonparser.py, reportgen.py, tgtinput.py, config.py |
| `modules/` | 24 self-contained tool plugins implementing `ToolBase` | automation.py, nmap.py, hashcat.py, etc. |
| `ui/` | Reusable UI components, themes, workers | main_window.py, sidepanel.py, styles.py, worker.py |

---

## 📁 Complete Project Structure

```
VAJRA-OSP/
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies (PySide6)
├── Golden_Rules.md              # Project guidelines
├── install_automation_tools.sh  # External tool installer
│
├── core/                        # Core utilities (7 files)
│   ├── __init__.py
│   ├── config.py               # Configuration management (output paths, settings)
│   ├── fileops.py              # File operations & directory structure creation
│   ├── jsonparser.py           # JSON parsing & final.json generation
│   ├── privileges.py           # Privilege management (sudo operations)
│   ├── reportgen.py            # HTML/PDF report generation (1083 lines)
│   └── tgtinput.py             # Target input widget with validation
│
├── modules/                     # Tool plugins (27 files, 24 unique tools)
│   ├── __init__.py
│   ├── bases.py                # Base classes (ToolBase, ToolCategory enum)
│   ├── automation.py           # 8-step automated pipeline (1326 lines)
│   ├── amass.py                # OWASP Amass subdomain enumeration
│   ├── dencoder.py             # Encoder/Decoder (50+ operations)
│   ├── dig.py                  # DNS lookup (10 query types)
│   ├── dnsrecon.py             # Advanced DNS recon (8 scan modes)
│   ├── eyewitness.py           # Web screenshot capture
│   ├── ffuf.py                 # Fast web fuzzer
│   ├── gobuster.py             # Directory/DNS brute-forcing (5 modes)
│   ├── hashcat.py              # GPU-accelerated password cracking
│   ├── hashcat_data.py         # Hashcat hash type definitions
│   ├── hashfinder.py           # Hash type identification
│   ├── httpx.py                # HTTP probing & live host detection
│   ├── hydra.py                # Network authentication brute-forcing
│   ├── john.py                 # John the Ripper password cracker
│   ├── msfvenom.py             # Metasploit payload generator
│   ├── nikto.py                # Web server vulnerability scanner
│   ├── nmap.py                 # Network scanner (port scanning, NSE)
│   ├── nuclei.py               # Template-based vulnerability scanner
│   ├── portscanner.py          # Custom Python port scanner
│   ├── searchsploit.py         # Exploit-DB local search
│   ├── shellforge.py           # Reverse shell command generator
│   ├── strings.py              # Binary file string extractor
│   ├── subfinder.py            # Passive subdomain discovery
│   ├── wafw00f.py              # Web Application Firewall detection
│   └── whois.py                # Domain registration lookup
│
├── ui/                          # User interface components (7 files)
│   ├── __init__.py
│   ├── main_window.py          # Main application window (436 lines)
│   ├── sidepanel.py            # Collapsible navigation sidebar
│   ├── styles.py               # Centralized styling system (1164 lines)
│   ├── worker.py               # Background subprocess workers
│   ├── notification.py         # Toast notification system
│   └── settingpanel.py         # Application settings panel
│
└── linux_setup/                 # Linux-specific setup files
    └── hook-vajra.py           # PyInstaller hook
```

---

## 🧰 Core Utilities Documentation

### **1. Configuration (`core/config.py`)**

**Purpose**: Centralized configuration management for the application.

**Key Features:**
- `ConfigManager` class for managing output directories
- Persistent settings storage
- Support for custom output paths

---

### **2. File Operations (`core/fileops.py`)**

**Purpose**: Manages file system operations and directory structure creation.

**Key Functions:**

#### **`create_target_dirs(target, group_name=None)`**
Creates organized directory structure for scan results:

**Single Target Mode:**
```
/tmp/Vajra-results/
└── example.com_11012026_150821/
    ├── Logs/
    ├── Reports/
    └── JSON/
```

**Batch/Group Mode** (from file input):
```
/tmp/Vajra-results/
└── targets/              # Group name from file
    └── example.com_11012026_150821/
        ├── Logs/
        ├── Reports/
        └── JSON/
```

#### **Caching System:**
- `get_cache_dir()`: Get cache directory path
- `get_cached_result()`: Retrieve cached results with age validation
- `set_cached_result()`: Store results in cache
- `clear_cache()`: Clear all cached data

---

### **3. Target Input (`core/tgtinput.py`)**

**Purpose**: Handles target input parsing, validation, and normalization.

**Key Components:**

#### **`TargetInput` Widget**
- Text input field for domain/IP/file path
- File picker button (📁) for selecting target files
- Placeholder: "Enter target (domain / IP / CIDR) or select file"
- Auto-completion support

#### **`parse_targets(input_value)`**
Returns: `(targets_list, source_type)`
- `source_type`: "single" or "file"

#### **`normalize_target(target)`**
Cleans target by removing protocol while preserving path:
- `https://example.com/api` → `example.com/api`
- `http://192.168.1.1:8080` → `192.168.1.1:8080`

---

### **4. JSON Parser (`core/jsonparser.py`)**

**Purpose**: Parses scan results and generates consolidated JSON output.

**`FinalJsonGenerator` Class:**

Parses and aggregates data from:
- **Whois**: Domain registration details
- **Dig**: DNS records (A, AAAA, MX, NS, TXT, CNAME, SOA, PTR)
- **Subdomains**: From alive.txt
- **Services**: From HTTPX alive.json
- **Nmap**: XML port scan results
- **Nuclei**: Vulnerability scan findings
- **Nikto**: Web server vulnerabilities
- **EyeWitness**: Screenshot existence check

**Output:** `{target_dir}/JSON/final.json`

---

### **5. Report Generation (`core/reportgen.py`)**

**Purpose**: Generates professional HTML reports from scan data.

**`ReportGenerator` Class:**

**Report Sections:**
1. **Header**: Target name, scan date, VAJRA branding with risk indicator
2. **Executive Summary**: High-level overview with statistics
3. **WHOIS Section**: Domain registration details
4. **Dig Section**: DNS records in categorized tables
5. **Subdomain Section**: Discovered subdomains table
6. **Service Section**: Live services from HTTPX
7. **Nmap Section**: Port scan results with CVSS-colored severity
8. **Nuclei Section**: Vulnerability findings with severity badges
9. **Nikto Section**: Web server vulnerabilities
10. **EyeWitness Section**: Screenshot count summary
11. **Recommendations**: Auto-generated security recommendations
12. **Footer**: Timestamp, disclaimer

**Features:**
- CVSS-based color coding (Critical: 9.0-10.0, High: 7.0-8.9, Medium: 4.0-6.9, Low: 0.1-3.9)
- Responsive tables with hover effects
- Collapsible sections with expand/collapse animation
- Copy-to-clipboard buttons
- Export-ready HTML (no external dependencies)
- PDF generation support

---

## 🎨 UI Components Documentation

### **1. Main Window (`ui/main_window.py`)**

**Purpose**: Primary application window managing layout, tabs, and navigation.

**Key Features:**

#### **Window Configuration**
- Title: "VAJRA - Offensive Security Platform"
- Minimum size: 1200×720px
- Dark theme styling (VS Code inspired)

#### **Tool Discovery (`_discover_tools()`)**
```python
def _discover_tools(self):
    """
    Hybrid tool discovery:
    - Development mode: Auto-discovers all modules in modules/ directory
    - Frozen mode (PyInstaller): Uses fallback list for reliability
    """
    tools = {}
    package = importlib.import_module("modules")
    
    for _, name, is_pkg in pkgutil.walk_packages(package.__path__):
        if not is_pkg:
            module = importlib.import_module(f'modules.{name}')
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, ToolBase) and obj is not ToolBase:
                    tool_instance = obj()
                    tools[tool_instance.name] = tool_instance
    return tools
```

#### **Keyboard Shortcuts**
- `Ctrl+R`: Run active tool
- `Ctrl+Q`: Stop active tool  
- `Ctrl+L`: Clear output
- `Ctrl+I`: Focus primary input

#### **Tab Management**
- Singleton pattern (one tab per tool)
- Custom close button (✕) on each tab
- Welcome tab when no tools open
- Proper cleanup on tab close

---

### **2. Sidepanel (`ui/sidepanel.py`)**

**Purpose**: Collapsible navigation sidebar with categorized tool listing.

**Layout:**
```
Sidepanel (260px × full height)
├── Header
│   └── "VAJRA" title (gradient background)
├── Scroll Area (expandable)
│   ├── Category: AUTOMATION ▾
│   │   └── Automation
│   ├── Category: INFO GATHERING ▾
│   │   ├── Dig, DNSRecon, SearchSploit, WAFW00F, Whois
│   └── ... (11 categories total)
└── Footer
    └── ⚙️ Settings
```

**Category Behavior:**
- Collapsible with ▾/▸ arrow indicators
- All categories start expanded by default
- Tools sorted alphabetically within category

---

### **3. Styles (`ui/styles.py`)**

**Purpose**: Centralized styling system - single source of truth for all UI.

**Color Palette:**
```python
# Background Colors
COLOR_BG_PRIMARY   = "#1a1a1a"   # Main editor background
COLOR_BG_SECONDARY = "#18181b"   # Sidebar/panels
COLOR_BG_INPUT     = "#252525"   # Input fields
COLOR_BG_ELEVATED  = "#2a2a2a"   # Elevated elements

# Accent Colors
COLOR_ACCENT_PRIMARY = "#f97316"  # Orange (Run buttons)
COLOR_ACCENT_HOVER   = "#fb923c"  # Orange hover
COLOR_ACCENT_BLUE    = "#3b82f6"  # Blue accent

# Semantic Colors
COLOR_INFO     = "#60a5fa"  # Blue
COLOR_SUCCESS  = "#10b981"  # Green
COLOR_WARNING  = "#facc15"  # Yellow
COLOR_ERROR    = "#f87171"  # Red
COLOR_CRITICAL = "#ef4444"  # Dark red
```

**Reusable Components:**
- `StyledComboBox`, `StyledSpinBox`, `StyledCheckBox`
- `StyledLineEdit`, `StyledLabel`, `HeaderLabel`
- `RunButton`, `StopButton`, `BrowseButton`, `CopyButton`
- `OutputView`, `OutputHelper`
- `StyledToolView`, `StyledGroupBox`, `ToolSplitter`
- `SafeStop` mixin for process termination

---

### **4. Worker Threads (`ui/worker.py`)**

**Purpose**: Non-blocking subprocess execution with real-time output streaming.

#### **`ProcessWorker` Class**
Extends `QThread` for background process execution.

**Signals:**
- `output_ready = Signal(str)`: Emitted for each line of output
- `error = Signal(str)`: Emitted on exception
- `stopped = Signal()`: Emitted when process is stopped

**Features:**
- Line-by-line streaming with optional buffering
- Graceful termination (SIGTERM → SIGKILL)
- Sudo password support via stdin
- Auto shell mode for complex commands

#### **`ToolExecutionMixin` Class**
Mixin for unified tool execution lifecycle:
- `init_progress_tracking()`: Initialize progress bar
- `start_execution()`: Start command execution
- `on_execution_finished()`: Handle completion/cleanup
- `update_progress()`: Update progress bar

---

## 🛠️ Complete Tool Documentation (24 Tools)

### **Category: AUTOMATION**

#### **1. Automation (`automation.py`)**
**Description**: Complete bug bounty reconnaissance pipeline.

**8-Step Pipeline:**
1. **Whois**: Domain registration lookup
2. **Dig**: Comprehensive DNS enumeration
3. **Subfinder**: Passive subdomain discovery
4. **TheHarvester**: OSINT subdomain enumeration (optional)
5. **HTTPX**: Live host detection & probing
6. **Nmap**: Port scanning on live hosts
7. **Nuclei**: Vulnerability scanning (optional)
8. **Nikto**: Web server scanning (optional)
9. **Report Generation**: HTML report creation

**UI Features:**
- Color-coded status indicators (⏳ Pending, 🔄 Running, ✅ Completed, ⏭️ Skipped, ❌ Error)
- Skip/Stop controls for each step
- Parallel subdomain enumeration option
- Configurable tool parameters

---

### **Category: INFO_GATHERING**

#### **2. Whois (`whois.py`)**
Domain registration and ownership lookup.

#### **3. Dig (`dig.py`)**
DNS query tool supporting 10 record types: A, AAAA, MX, NS, TXT, CNAME, SOA, PTR, ANY, AXFR.

#### **4. DNSRecon (`dnsrecon.py`)**
Advanced DNS enumeration with 8 scan modes: STD, AXFR, PTR, GOO, BING, SNOOP, BRT, WALK.

#### **5. WAFW00F (`wafw00f.py`)**
Web Application Firewall detection tool.

#### **6. SearchSploit (`searchsploit.py`)**
Exploit-DB local search with filters for CVE, platform, type.

---

### **Category: SUBDOMAIN_ENUMERATION**

#### **7. Subfinder (`subfinder.py`)**
Fast passive subdomain discovery using 40+ public sources.

#### **8. Amass (`amass.py`)**
OWASP Amass OSINT-based enumeration with active/passive modes.

---

### **Category: LIVE_SUBDOMAINS**

#### **9. HTTPX (`httpx.py`)**
Fast HTTP probing with JSON output for live host detection.

---

### **Category: PORT_SCANNING**

#### **10. Nmap (`nmap.py`)**
Industry-standard network scanner with:
- Scan types: TCP SYN, TCP Connect, UDP, Service/Version, OS Detection, Aggressive
- Host discovery: Normal, Skip Ping, ARP Ping
- Timing templates: Paranoid to Insane (T0-T5)
- NSE script support with searchable dropdown

#### **11. Port Scanner (`portscanner.py`)**
Custom Python port scanner with:
- 3 scan types: TCP Connect, SYN, UDP
- Banner grabbing and service identification
- Stealth mode with randomization
- Up to 500 concurrent threads

---

### **Category: WEB_SCANNING**

#### **12. Gobuster (`gobuster.py`)**
High-speed brute-forcing with 5 modes:
1. **Dir**: Directory enumeration (extensions, status filters)
2. **DNS**: Subdomain brute-forcing
3. **VHost**: Virtual host discovery
4. **Fuzz**: Advanced fuzzing (methods, headers, body)
5. **S3**: AWS S3 bucket enumeration

#### **13. FFUF (`ffuf.py`)**
Fast web fuzzer with:
- Multiple fuzz points (URL, headers, POST data)
- Response filters (status, size, words, lines)
- Matchers for positive results
- Recursion support
- Rate limiting

---

### **Category: WEB_SCREENSHOTS**

#### **14. EyeWitness (`eyewitness.py`)**
Automated web application screenshot capture with:
- Configurable timeout and thread count
- HTTPS prepending option
- Batch processing from file
- Timestamped output directories

---

### **Category: VULNERABILITY_SCANNER**

#### **15. Nuclei (`nuclei.py`)**
Template-based vulnerability scanner with:
- Severity filtering (critical, high, medium, low, info)
- Custom template support
- Rate limiting
- Proxy support

#### **16. Nikto (`nikto.py`)**
Web server vulnerability scanner with:
- SSL/TLS support
- Custom port and host header
- Tuning options (plugins, tests)
- CVSS-based severity color coding in output

---

### **Category: CRACKER**

#### **17. Hashcat (`hashcat.py`)**
GPU-accelerated password cracking:
- 180+ hash types
- Attack modes: Dictionary, Combinator, Brute Force, Hybrid
- Workload profiles: Low to Nightmare
- Real-time cracked password display

#### **18. John the Ripper (`john.py`)**
CPU-based password cracker:
- 100+ hash formats
- Attack modes: Wordlist, Incremental, Mask, Single
- Session save/restore
- Multi-core forking

#### **19. Hydra (`hydra.py`)**
Network authentication brute-forcing:
- 50+ protocols (SSH, FTP, HTTP, SMB, RDP, etc.)
- 4 credential modes: single user, password spray, full matrix, colon-list
- SSL/TLS, proxy support
- Custom port and timeout

#### **20. Hash Finder (`hashfinder.py`)**
Hash type identification:
- Pattern-based detection
- Length and format analysis
- 40+ algorithm support
- Confidence scoring

#### **21. Dencoder (`dencoder.py`)**
Multi-purpose encoding/decoding:
- Base encodings: Base16, Base32, Base64, Base85, ASCII85
- URL/HTML encoding
- Hashing: MD5, SHA family, BLAKE2
- JWT decode
- Security payloads: XSS, SQL, path traversal, command injection

---

### **Category: PAYLOAD_GENERATOR**

#### **22. ShellForge (`shellforge.py`)**
Reverse shell command generator:
- Categories: Reverse, Bind, MSFVenom, HoaxShell
- 20+ shell types (bash, sh, powershell, etc.)
- Auto IP detection
- Base64/URL encoding options
- Listener command generation

#### **23. MSFVenom (`msfvenom.py`)**
Metasploit payload generator:
- Platform presets: Windows, Linux, macOS, Android, PHP, Java
- Meterpreter and shell payloads
- Output formats: exe, elf, raw, war, php
- Encoder support
- Template injection

---

### **Category: FILE_ANALYSIS**

#### **24. Strings (`strings.py`)**
Binary file string extractor:
- Encoding support: ASCII, Unicode (LE/BE), UTF-8
- Pattern detection: URLs, emails, IPs, paths, hashes
- Statistics dashboard
- Filter system with category toggles
- Search within results

---

## 📊 Tool Statistics Summary

| Tool | Category | Lines of Code | Key Features |
|------|----------|---------------|--------------|
| Automation | AUTOMATION | 1,326 | 8-step pipeline, parallel execution |
| Whois | INFO_GATHERING | 280 | Domain registration lookup |
| Dig | INFO_GATHERING | 342 | 10 DNS query types |
| DNSRecon | INFO_GATHERING | 295 | 8 scan modes |
| WAFW00F | INFO_GATHERING | 281 | WAF detection |
| SearchSploit | INFO_GATHERING | 282 | Exploit-DB search |
| Subfinder | SUBDOMAIN_ENUM | 280 | 40+ passive sources |
| Amass | SUBDOMAIN_ENUM | 320 | Active/passive enumeration |
| HTTPX | LIVE_SUBDOMAINS | 300 | HTTP probing |
| Nmap | PORT_SCANNING | 503 | NSE scripts, OS detection |
| PortScanner | PORT_SCANNING | 796 | Custom Python scanner |
| Gobuster | WEB_SCANNING | 750 | 5 brute-force modes |
| FFUF | WEB_SCANNING | 579 | Advanced fuzzing |
| EyeWitness | WEB_SCREENSHOTS | 340 | Batch screenshots |
| Nuclei | VULNERABILITY | 415 | Template-based scanning |
| Nikto | VULNERABILITY | 652 | Web server scanning |
| Hashcat | CRACKER | 450 | 180+ hash types, GPU |
| John | CRACKER | 500 | 100+ formats |
| Hydra | CRACKER | 520 | 50+ protocols |
| Hash Finder | CRACKER | 341 | Hash identification |
| Dencoder | CRACKER | 650 | 50+ encode/decode ops |
| ShellForge | PAYLOAD_GEN | 394 | Shell generator |
| MSFVenom | PAYLOAD_GEN | 491 | Payload generator |
| Strings | FILE_ANALYSIS | 649 | Binary analysis |

**Total**: ~12,000+ lines of tool code across 24 unique tools

---

## 🎨 Common UI/UX Patterns

### **1. StyledToolView Base Class**
All tools inherit from `StyledToolView`, providing:
- Consistent header with tool category breadcrumb
- Target input with file picker
- Command preview (editable)
- Run/Stop button pair
- Output panel with copy button
- `SafeStop` mixin for graceful termination

### **2. Real-Time Output Streaming**
```python
self.worker = ProcessWorker(command)
self.worker.output_ready.connect(self.on_new_output)
self.worker.finished.connect(self.on_execution_finished)
self.worker.error.connect(self._on_error)
self.worker.start()
```

### **3. Color-Coded Output (OutputHelper)**
```python
_info(text)     # [INFO] Blue
_success(text)  # [SUCCESS] Green
_warning(text)  # [WARNING] Yellow/Amber
_error(text)    # [ERROR] Red
_section(title) # === SECTION === Bold
```

### **4. CVSS Severity Colors**
- **Critical (9.0-10.0)**: `#dc2626` (Dark Red)
- **High (7.0-8.9)**: `#ea580c` (Orange)
- **Medium (4.0-6.9)**: `#ca8a04` (Yellow)
- **Low (0.1-3.9)**: `#16a34a` (Green)
- **Info**: `#2563eb` (Blue)

---

## 📁 File Management & Results Structure

Tools automatically create organized directories:

```
{RESULT_BASE}/
└── {target}_{timestamp}/
    ├── Logs/              # whois.txt, dig.txt, dnsrecon.txt
    ├── Subdomains/        # amass.txt, subfinder.txt, alive.txt
    ├── Scans/             # nmap*.xml, portscan.txt
    ├── Httpx/             # httpx.json
    ├── Nuclei/            # nuclei.json
    ├── Nikto/             # nikto_*.csv
    ├── Eyewitness/        # screenshots/
    ├── JSON/              # final.json
    └── Reports/           # final_report.html, final_report.pdf
```

---

## 🔧 Plugin Architecture

### **Creating a New Tool**

```python
# modules/mytool.py

from modules.bases import ToolBase, ToolCategory
from ui.styles import (
    StyledToolView, SafeStop, OutputHelper,
    RunButton, StopButton, StyledLineEdit, OutputView
)

class MyTool(ToolBase):
    name = "My Tool"
    category = ToolCategory.INFO_GATHERING
    
    @property
    def description(self):
        return "My custom security tool"
    
    def get_widget(self, main_window):
        return MyToolView(main_window)


class MyToolView(StyledToolView, SafeStop, OutputHelper):
    tool_name = "My Tool"
    tool_category = "INFO_GATHERING"
    
    def __init__(self, main_window=None):
        super().__init__()
        self.init_safe_stop()
        self.main_window = main_window
        self._build_ui()
        self.update_command()
    
    def _build_ui(self):
        # Build custom UI here
        pass
    
    def build_command(self, preview=False):
        # Generate command string
        return f"mytool --scan {self.target_input.text()}"
    
    def update_command(self):
        self.command_display.setText(self.build_command(preview=True))
    
    def run_scan(self):
        # Execute the tool
        command = self.build_command()
        self.start_execution(command, shell=True)
    
    def on_execution_finished(self):
        self._info("Scan completed!")
```

**Result**: Tool automatically appears in "INFO GATHERING" category with full integration.

---

## 🚀 Key Technical Features

### **1. Dynamic Plugin Discovery**
- Uses Python introspection (`importlib`, `pkgutil`, `inspect`)
- No manual tool registration required
- Automatic categorization via `ToolCategory` enum

### **2. Non-Blocking Execution**
- All tools run in background `QThread`
- Real-time output streaming
- Graceful stop with SIGTERM/SIGKILL fallback

### **3. Unified Styling**
- Single source of truth in `ui/styles.py`
- Consistent dark theme across all tools
- Reusable styled components

### **4. Comprehensive Reporting**
- JSON data aggregation from all scan results
- Professional HTML reports with embedded CSS
- PDF export capability
- CVSS-based severity system

---

## ⚠️ Notes

### **Duplicate Check - RESOLVED**
Both `dencoder.py` and `strings.py` are **distinct tools**:
- **`dencoder.py`**: Encoder/decoder for text transformations (CRACKER category)
- **`strings.py`**: Binary file string extractor (FILE_ANALYSIS category)

---

## 📈 Project Totals

| Metric | Count |
|--------|-------|
| **Total Tools** | 24 unique |
| **Tool Categories** | 11 |
| **Core Utilities** | 7 files |
| **UI Components** | 7 files |
| **Total Python Files** | ~50 |
| **Lines of Code** | ~25,000+ |

---

## 🎯 Conclusion

VAJRA is a **comprehensive, professional-grade offensive security platform** featuring:

✅ **24 Specialized Tools** covering full penetration testing workflow  
✅ **Plugin Architecture** for easy extensibility  
✅ **8-Step Automated Pipeline** with parallel execution  
✅ **Batch Processing** for multi-target engagements  
✅ **Consistent UI/UX** with professional dark theme  
✅ **Real-Time Output** streaming and progress tracking  
✅ **Organized File Management** with timestamped directories  
✅ **Professional Reports** with CVSS severity system  
✅ **Advanced Features**: GPU acceleration, 180+ hash types, 50+ protocols
