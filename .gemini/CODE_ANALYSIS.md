# VAJRA Offensive Security Platform - Comprehensive Tool Analysis

## 📋 Overview
VAJRA is a **PySide6-based offensive security platform** with a modular plugin architecture providing 17 penetration testing tools organized in categorized sidepanels. Each tool is dynamically discovered and loaded at runtime, supporting batch operations, automated workflows, and comprehensive result tracking.

---

## 🏗️ Architecture Overview

### **Application Flow:**
```
main.py → MainWindow → Sidepanel + Tabs
           ↓
       Tool Discovery (modules/*.py)
           ↓
       Dynamic Tool Loading
           ↓
       Tool Widgets in Tabs
```

### **Core Components:**

1. **`main.py`**: Entry point with global font scaling (+2px for all elements)
2. **`core/`**: Utilities for file operations, JSON parsing, target input validation, and report generation
3. **`modules/`**: 17 self-contained tool plugins implementing `ToolBase`
4. **`ui/`**: Reusable UI components, styling system, background workers, notifications

---

## 📁 Project Structure

```
VAJRA---Offensive-Security-Platform/
├── main.py                    # Application entry point with global font scaling
├── core/                      # Core utilities
│   ├── fileops.py            # File operations & target directory structure
│   ├── jsonparser.py         # JSON parsing utilities
│   ├── reportgen.py          # HTML/PDF report generation
│   └── tgtinput.py           # Target input widget with validation
├── modules/                   # Tool modules (17 plugins)
│   ├── bases.py              # Base classes (ToolBase, ToolCategory enum)
│   ├── amass.py              # Subdomain enumeration (OWASP Amass)
│   ├── automation.py         # 6-step automated pipeline
│   ├── dencoder.py           # Decoder/Encoder (50+ operations)
│   ├── dig.py                # DNS lookup (10 query types)
│   ├── dnsrecon.py           # Advanced DNS recon (8 scan modes)
│   ├── eyewitness.py         # Web screenshot capture
│   ├── gobuster.py           # Web/DNS brute-forcing (5 modes)
│   ├── hashcat.py            # Password cracking (180+ hash types)
│   ├── httpx.py              # HTTP probing & live host detection
│   ├── hydra.py              # Credential brute-forcing (multi-service)
│   ├── john.py               # John the Ripper (4 attack modes)
│   ├── nmap.py               # Port scanning (comprehensive)
│   ├── portscanner.py        # Custom Python port scanner (3 scan types)
│   ├── strings.py            # [DUPLICATE] Same as dencoder.py
│   ├── subfinder.py          # Subdomain finder (passive enumeration)
│   └── whois.py              # WHOIS domain information lookup
└── ui/                        # User interface components
    ├── main_window.py         # Main application window with tab system
    ├── sidepanel.py           # Collapsible navigation sidebar
    ├── notification.py        # Toast notification system
    ├── settingpanel.py        # Application settings panel
    ├── styles.py              # Centralized styling (dark theme, colors, fonts)
    ├── widgets.py             # Reusable UI components (BaseToolView, OutputView)
    └── worker.py              # Background subprocess worker threads
```

---

## 🧰 Core Utilities Documentation

### **1. File Operations (`core/fileops.py`)**

**Purpose**: Manages all file system operations and directory structure creation.

**Key Functions:**

#### **`create_target_dirs(target, group_name=None)`**
Creates organized directory structure for scan results:

**Single Target Mode:**
```
/tmp/Vajra-results/
└── example.com_01012026_114521/
    ├── Logs/
    ├── Reports/
    └── JSON/
```

**Batch/Group Mode** (from file input):
```
/tmp/Vajra-results/
└── targets/              # Group name from file
    └── example.com_01012026_114521/
        ├── Logs/
        ├── Reports/
        └── JSON/
```

**Features:**
- Timestamp-based naming (format: `DDMMYYYY_HHMMSS`)
- Automatic subdirectory creation
- Group-based organization for batch scans
- Returns base directory path for tools to use

#### **`get_group_name_from_file(file_path)`**
Extracts filename without extension to use as group name.
- Example: `targets.txt` → `targets`

#### **`get_timestamp()`**
Returns current timestamp string in format: `DDMMYYYY_HHMMSS`

**Global Constant:**
- `RESULT_BASE = "/tmp/Vajra-results"` - Base directory for all results

---

### **2. Target Input (`core/tgtinput.py`)**

**Purpose**: Handles target input parsing, validation, and normalization.

**Key Components:**

#### **`TargetInput` Widget**
Reusable Qt widget providing:
- Text input field for domain/IP/file path
- File picker button (📁) for selecting target files
- Placeholder text: "Enter target (domain / IP / CIDR) or select file"
- Minimum height: 36px
- Auto-completion support

**Methods:**
- `get_target()`: Returns current input value
- `open_file_dialog()`: Opens file picker dialog

#### **`parse_targets(input_value)`**
Intelligent parsing of single or multi-target input:

**Returns:** `(targets_list, source_type)`
- `source_type`: "single" or "file"

**Behavior:**
1. Checks if input is a file path
2. If file: Reads all non-empty lines, normalizes each
3. If single: Returns normalized target in list

#### **`normalize_target(target)`**
Cleans target by removing protocol while preserving path:
- `https://example.com/api` → `example.com/api`
- `http://192.168.1.1:8080` → `192.168.1.1:8080`

---

### **3. Report Generation (`core/reportgen.py`)**

**Purpose**: Generates professional HTML reports from scan data.

**Key Components:**

#### **`ReportGenerator` Class**

**Constructor:**
```python
ReportGenerator(target, target_dir, module_choices)
```
- `target`: Scanned target domain/IP
- `target_dir`: Base directory containing scan results
- `module_choices`: String of modules run (e.g., "whois subfinder amass httpx nmap")

**Report Sections:**
1. **Header**: Target name, scan date, VAJRA branding
2. **Executive Summary**: High-level overview, total subdomains/services found
3. **WHOIS Section**: Domain registration details (if whois was run)
4. **Subdomain Section**: Table of discovered subdomains (from Amass/Subfinder)
5. **Service Section**: Live services table (from HTTPX)
6. **Nmap Section**: Port scan results with service detection
7. **Recommendations**: Auto-generated security recommendations
8. **Footer**: Timestamp, disclaimer

**Features:**
- Embedded CSS styling (professional dark theme)
- Responsive tables with hover effects
- Color-coded status indicators
- Collapsible sections
- Copy-to-clipboard buttons
- Export-ready HTML (no external dependencies)

**Data Source:**
- Reads from `final.json` (generated by `FinalJsonGenerator`)
- JSON structure contains aggregated results from all modules

**Output:**
- Saves to `{target_dir}/Reports/final_report.html`
- ~500 lines of styled HTML per report

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
Uses Python introspection to auto-discover tool plugins:
```python
def _discover_tools(self):
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

**Benefits:**
- No manual tool registration needed
- New tools automatically available on restart
- Supports hot-reloading during development

#### **Layout Structure**
```
MainWindow
├── Sidepanel (260px fixed width)
│   └── Tool navigation
└── Content Area (flexible)
    └── QTabWidget
        ├── Welcome Tab (default)
        ├── Tool Tabs (dynamically added)
        └── Settings Tab
```

#### **Tab Management**

**`open_tool_tab(tool)`** - Singleton pattern:
1. Check if tool already open → focus existing tab
2. Remove welcome tab if present
3. Call `tool.get_widget(main_window=self)` to create UI
4. Add custom close button (✕) to tab
5. Store reference in `self.open_tool_widgets`

**`close_tab(index)`** - Cleanup:
1. Remove widget reference
2. Stop any active processes
3. Remove tab from QTabWidget
4. Show welcome tab if no tabs remain

#### **Process Management**
- `active_process`: Tracks currently running worker thread
- `stop_active_process()`: Kills active subprocess
- Ensures only one tool runs at a time

#### **Notification System**
- `notification_manager`: Toast-style notifications
- Tools call `main_window.notification_manager.notify(message)`

---

### **2. Sidepanel (`ui/sidepanel.py`)**

**Purpose**: Collapsible navigation sidebar with categorized tool listing.

**Signals:**
- `tool_clicked = Signal(object)`: Emitted when tool button clicked
- `settings_clicked = Signal()`: Emitted when settings button clicked

**Layout:**
```
Sidepanel (260px × full height)
├── Header
│   └── "VAJRA" title (centered, bold, 20px)
├── Scroll Area (expandable)
│   ├── Category: AUTOMATION ▾
│   │   └── Automation (button)
│   ├── Category: INFO GATHERING ▾
│   │   ├── Dig (button)
│   │   ├── DNSRecon (button)
│   │   └── Whois (button)
│   └── ... (8 categories total)
└── Footer
    └── ⚙️ Settings (button)
```

**Category Behavior:**
- Collapsible with ▾/▸ arrow indicators
- Click category header to toggle visibility
- All categories start expanded by default
- Tools sorted alphabetically within category

**Button States:**
- **Default**: Dark background, gray text
- **Hover**: Lighter background, white text
- **Active (`:checked`)**: Amber background, white bold text
- Uses `setCheckable(True)` for state persistence

**Tool Organization:**
1. Groups tools by `ToolCategory` enum
2. Sorts categories by enum order
3. Sorts tools alphabetically within category
4. Creates indented buttons (15px left margin)

---

### **3. Widgets (`ui/widgets.py`)**

**Purpose**: Reusable UI components for consistent tool interfaces.

#### **`OutputView` Widget**

**Features:**
- Wraps `QPlainTextEdit` for consistent styling
- Read-only output display
- Copy button (📋) overlay (top-right corner)
- Placeholder: "Tool results will appear here..."

**Methods:**
- `appendPlainText(text)`: Add plain text line
- `appendHtml(html)`: Add HTML-formatted text
- `toPlainText()`: Get all text content
- `clear()`: Clear all output
- `copy_to_clipboard()`: Copy output to system clipboard

**Usage:**
```python
self.output = OutputView()
self.output.appendHtml('<span style="color:#60A5FA;">[INFO]</span> Scan started')
```

#### **`BaseToolView` Class**

**Purpose**: Standard layout for tool UIs (used by 11 tools).

**Structure:**
```
BaseToolView
├── Control Panel (top, 250px)
│   ├── Header: "Category › Tool Name"
│   ├── Target Label + TargetInput + RUN/STOP buttons
│   ├── Command Label + Command Input (editable)
│   └── [Custom UI injected here by subclasses]
└── Output Area (bottom, 500px)
    └── OutputView widget
```

**Initialization:**
```python
class MyToolView(BaseToolView):
    def __init__(self, name, category, main_window):
        super().__init__(name, category, main_window)
        # Custom UI is auto-built
        self.update_command()  # Initial command generation
```

**Required Overrides:**
- `update_command(self)`: Build command string from UI state
- `run_scan(self)`: Execute the tool command

**Helper Methods:**
- `_notify(message)`: Show toast notification
- `_info(message)`: Add blue [INFO] message to output
- `_error(message)`: Add red [ERROR] message to output
- `_section(title)`: Add yellow section header
- `_on_scan_completed()`: Re-enable buttons, cleanup worker

**Automatic Features:**
- Target input with file picker
- Command preview (editable before run)
- Run/Stop button management
- Output area with copy button
- Process lifecycle management

---

### **4. Worker Threads (`ui/worker.py`)**

**Purpose**: Non-blocking subprocess execution with real-time output streaming.

#### **`ProcessWorker` Class**

Extends `QThread` for background process execution.

**Constructor:**
```python
ProcessWorker(command, shell=False, stdin_data=None)
```
- `command`: List of strings (e.g., `["nmap", "-sV", "192.168.1.1"]`) or string if shell=True
- `shell`: Enable shell mode for complex commands
- `stdin_data`: For sudo password injection (`sudo -S`)

**Signals:**
- `output_ready = Signal(str)`: Emitted for each line of output
- `error = Signal(str)`: Emitted on exception

**Features:**

1. **Auto-Shell Detection**: Converts to shell mode if command too long (>50 args or >5000 chars)
2. **Line-by-Line Streaming**: Emits output immediately as process generates it
3. **Sudo Support**: Injects password via stdin for `sudo -S` commands
4. **Graceful Termination**: `stop()` method kills process cleanly

**Usage Pattern:**
```python
self.worker = ProcessWorker(["gobuster", "dir", "-u", url, "-w", wordlist])
self.worker.output_ready.connect(self.output.appendPlainText)
self.worker.finished.connect(self._on_scan_completed)
self.worker.error.connect(self._error)
self.worker.start()

# Later, to stop:
self.worker.stop()
```

**Benefits:**
- UI remains responsive during long scans
- Real-time output feedback
- Clean separation of UI and process logic
- Reusable across all tools

---

## 🛠️ Comprehensive Tool Documentation

### **1. Automation (`automation.py`)**

**Category**: AUTOMATION  
**Description**: Automated penetration testing pipeline executing 6 sequential steps with live status tracking.

**Features:**
- **6-Step Pipeline**:
  1. **Whois**: Domain registration information
  2. **Subfinder**: Passive subdomain enumeration
  3. **Amass**: Active subdomain enumeration
  4. **HTTPX**: Live host detection & probing
  5. **Nmap**: Port scanning on live hosts
  6. **Report Generation**: Automated HTML report creation

- **Live Execution Dashboard**: Real-time status for each module (Pending → Running → Completed/Error/Skipped)
- **Skip/Stop Controls**: Skip current module or terminate entire pipeline
- **Automated File Management**: Creates organized directory structure per target
- **Result Aggregation**: Merges subdomain results before HTTPX probing

**UI/UX:**
- Color-coded status labels (Gray: Pending, Blue: Running, Green: Completed, Amber: Skipped, Red: Error)
- Live output stream in HTML-formatted console
- Skip button enabled during execution
- Stop button for emergency termination

**Command Generation:**  
Executes predefined commands for each module using `subprocess.Popen` with real-time output streaming.

---

### **2. Gobuster (`gobuster.py`)**

**Category**: WEB_SCANNING  
**Description**: High-speed directory, file, DNS, and fuzzing brute-force tool with 5 operational modes.

**Features:**

#### **5 Operational Modes:**

1. **Directory Mode (Dir)**:
   - Extensions (`-x`): Multi-extension support (php,txt,html,jsp,asp,aspx,js)
   - Blacklist Status Codes (`-b`): Filter unwanted responses (404,400-404)
   - Exclude Length (`--xl`): Filter responses by size (0 or 100-200)
   - User Agent (`-a`): Custom UA string
   - Expanded Mode (`-e`): Show full URLs
   - Skip TLS (`-k`), Follow Redirects (`-r`), Add Slash (`-f`)

2. **DNS Mode**:
   - Show IPs (`-i`): Display resolved IP addresses
   - Wildcard Force: Bypass wildcard DNS detection

3. **VHost Mode**:
   - Append Domain: Automatically append base domain to wordlist entries

4. **Fuzz Mode** (Advanced):
   - HTTP Methods: GET/POST/PUT/PATCH/DELETE
   - Wordlist Offset: Start fuzzing from specific position
   - Request Body (`-B`): JSON/form data with FUZZ keyword
   - Cookies, Headers, Proxy support
   - Filters: Exclude by status code or content length
   - Delay Configuration: Rate limiting (ms)
   - Retry Logic: Configurable retry count
   - **⚠️ Prominent Warning**: Target URL must contain 'FUZZ' keyword

5. **S3 Mode**:
   - AWS S3 bucket enumeration
   - Max Files (`-m`): Limit file listing
   - Skip TLS verification

**UI/UX:**
- Tabbed interface for mode selection
- Grid layout with dynamic column sizing
- Right-aligned labels for professional appearance
- Minimum column widths prevent UI crushing
- FUZZ mode has highlighted warning banner
- 2-line Request Body input for compactness

**Command Generation:**  
Dynamic command builder based on active mode, intelligently adds `-u` for URL-based modes or `-d` for DNS, handles target URL prefixing (auto-adds `http://`), and quotes special characters using `shlex.quote()`.

---

### **3. Dig (`dig.py`)**

**Category**: INFO_GATHERING  
**Description**: DNS query tool supporting 10 record types with multiple query options.

**Features:**

#### **10 Query Types** (Multi-select):
- **A (IPv4)**: Standard address records (default selected)
- **AAAA (IPv6)**: IPv6 address records
- **MX (Mail)**: Mail exchanger records
- **NS (NameServer)**: Authoritative nameservers
- **TXT (Text/SPF)**: Text records & SPF policies
- **CNAME (Alias)**: Canonical name records
- **SOA (Auth)**: Start of authority
- **PTR (Reverse)**: Reverse DNS lookup
- **ANY (All)**: All available records
- **AXFR (Zone)**: Zone transfer attempt

**Additional Options:**
- **Custom Nameserver** (`@8.8.8.8`): Query specific DNS server
- **Trace** (`+trace`): Trace delegation path
- **Short** (`+short`): Concise output

**UI/UX:**
- Checkbox grid (3 rows × 4 columns) for query types
- Custom nameserver input field
- Radio button styling (circular indicators)
- Results saved to `Logs/dig.txt`

**Command Generation:**  
Builds `dig @nameserver target TYPE1 TYPE2 +options` format, supports multiple simultaneous query types.

---

### **4 . DNSRecon (`dnsrecon.py`)**

**Category**: INFO_GATHERING  
**Description**: Advanced DNS enumeration with 8 specialized scan modes.

**Features:**

#### **8 Scan Modes** (Single selection):
1. **Standard (STD)**: Default comprehensive DNS scan (selected by default)
2. **Zone Transfer (AXFR)**: Attempt zone transfer
3. **Reverse Lookup (PTR)**: Reverse DNS on IP range
4. **Google Enumeration (GOO)**: Google dorking for subdomains
5. **Bing Enumeration (BING)**: Bing search enumeration
6. **Cache Snooping (SNOOP)**: DNS cache inspection
7. **Dictionary Brute Force (BRT)**: Wordlist-based subdomain brute-forcing
8. **Zone Walk (WALK)**: DNSSEC zone walking

**UI/UX:**
- Radio button grid for exclusive mode selection
- **Conditional Wordlist**: Only visible when "BRT" mode selected
- Browse button for wordlist file selection
- Blue highlight for selected mode

**Command Generation:**  
Generates `dnsrecon -d target -t mode` with special handling for BRT mode (`-D wordlist`) and reverse lookup (`-r` flag for IP ranges).

---

### **5. Eyewitness (`eyewitness.py`)**

**Category**: WEB_SCREENSHOTS  
**Description**: Automated web application screenshot capture tool.

**Features:**
- **Timeout Configuration**: Adjustable page load timeout (seconds)
- **Thread Control**: Parallel screenshot capture (1-50 threads)
- **HTTPS Prepending**: Auto-prepend https:// to URLs
- **Timestamped Output**: Results saved with timestamp for versioning
- **Batch Processing**: Processes multiple URLs from file or list

**UI/UX:**
- Spinbox controls for timeout and threads
- Checkbox for HTTPS prepending
- Creates timestamped directories: `Eyewitness/eyewitness_YYYYMMDD_HHMMSS/`

**Command Generation:**  
`eyewitness --web -f target_file --timeout X --threads Y --prepend-https`

---

### **6. Hashcat (`hashcat.py`)**

**Category**: CRACKER  
**Description**: GPU-accelerated password cracking supporting 180+ hash algorithms.

**Features:**

#### **180+ Hash Types** including:
- **Standard Hashes**: MD5, SHA1, SHA256, SHA512, BLAKE2b
- **Salted Hashes**: bcrypt, Argon2, PBKDF2-HMAC-SHA256
- **Application Hashes**: WordPress, Joomla, phpBB, Django
- **Database Hashes**: MySQL, PostgreSQL, MSSQL, Oracle
- **Operating System**: NTLM, LM, DCC/DCC2, macOS
- **Network Protocols**: WPA/WPA2/WPA3, IKE-PSK, Kerberos
- **Enterprise**: LDAP, SAP, Lotus Notes
- **Encrypted Archives**: ZIP, RAR, 7-Zip, KeePass, TrueCrypt

**Attack Modes:**
- **Dictionary** (`-a 0`): Wordlist-based
- **Combinator** (`-a 1`): Combine two wordlists
- **Brute Force** (`-a 3`): Mask-based attack
- **Hybrid** (`-a 6/7`): Wordlist + mask

**UI/UX:**
- Searchable hash type dropdown (type to filter 180+ options)
- Direct hash input or file upload
- Workload profile selector (Low/Default/High/Nightmare)
- Real-time cracked password display in table
- Auto-saves results to `/tmp/Vajra-results/{timestamp}/hashcat.txt`
- Copy results to clipboard button

**Command Generation:**  
`hashcat -m {mode} -a {attack_mode} {hash_file} {wordlist} -w {workload} --potfile-disable --outfile-format=2`

---

### **7. Httpx (`httpx.py`)**

**Category**: LIVE_SUBDOMAINS  
**Description**: Fast HTTP toolkit for probing live web services and extracting metadata.

**Features:**
- **Batch Processing**: Processes multiple targets from file
- **JSON Output**: Structured output with metadata
- **Silent Mode**: Clean output for automation
- **File/URL Detection**: Intelligently uses `-l` for files or `-u` for single URLs

**UI/UX:**
- Minimal configuration (leverages httpx-toolkit defaults)
- Saves results to `Httpx/httpx.json`
- Queue-based processing for multiple targets

**Command Generation:**  
`httpx -l {file} -json -o {output} -silent` or `httpx -u {url} -json -o {output} -silent`

---

### **8. Hydra (`hydra.py`)**

**Category**: CRACKER  
**Description**: Network authentication brute-forcing tool supporting 50+ protocols.

**Features:**

#### **50+ Supported Services** including:
- **Web**: HTTP/HTTPS (GET/POST forms), HTTP Proxy
- **Remote Access**: SSH, Telnet, RDP, VNC
- **File Transfer**: FTP, FTPS, SFTP, SMB/CIFS
- **Email**: POP3, IMAP, SMTP
- **Databases**: MySQL, PostgreSQL, MSSQL, MongoDB, Oracle, Redis
- **Authentication**: LDAP, Kerberos, RADIUS, SNMP
- **Network Services**: Cisco AAA, Cisco Enable, Socks5

**Credential Modes:**
1. **Single Username + Wordlist**: Brute-force single account
2. **Username List + Single Password**: Password spraying
3. **Username List + Password List**: Full matrix attack
4. **Colon-List** (`user:pass`): Pre-paired credentials

**Advanced Options:**
- **Custom Port**: Override default service port
- **SSL/TLS Toggle**: Enable encrypted connections
- **Proxy Support**: Route through HTTP/SOCKS proxy
- **Parallel Tasks** (`-t`): Concurrent connection count (default: 16)
- **Timeout**: Connection timeout in seconds

**HTTP Form-Specific:**
- **Login Path**: `/login.php`
- **POST Parameters**: `user=^USER^&pass=^PASS^`
- **Failure String**: "Invalid credentials"

**UI/UX:**
- Service dropdown with 50+ options
- Conditional UI (HTTP form options appear only for http/https-post-form)
- Real-time credential table display
- Duplicate credential filtering
- Results table columns: Host | Username | Password
- Auto-saves to `/tmp/Vajra-results/{timestamp}/hydra_credentials.txt`

**Command Generation:**  
Complex builder handling username/password modes, SSL prefix (`-S`), proxy (`-m CONNECT:proxy:port`), HTTP form data encoding.

---

### **9. John the Ripper (`john.py`)**

**Category**: CRACKER  
**Description**: CPU-based password cracker with 4 attack modes supporting 100+ hash formats.

**Features:**

#### **4 Attack Modes:**
1. **Wordlist**: Dictionary attack with wordlist file
2. **Incremental**: Brute-force (all character combinations)
3. **Mask**: Pattern-based attack (`?l?l?l?d?d?d` = 3 letters + 3 digits)
4. **Single**: Uses username/GECOS fields as password candidates

#### **100+ Hash Formats** including:
- **Raw Hashes**: MD5, SHA1, SHA256, SHA512, BLAKE2
- **Crypt Formats**: bcrypt, SHA512crypt, MD5crypt
- **Application**: Django, phpBB, WordPress, Drupal, Joomla
- **Operating System**: NTLM, LM, Kerberos, macOS passwords
- **Database**: MySQL, PostgreSQL, Oracle, MSSQL
- **Network**: WPA/WPA2, IKE, NetNTLM, VNC
- **Archives**: ZIP, RAR, 7-Zip, KeePass, PDF, Office documents
- **SSH/PGP**: SSH private keys, OpenPGP/GnuPG keys

**Advanced Options:**
- **Fork**: Parallel processing (multi-core utilization)
- **Session Name**: Save/restore cracking sessions

**UI/UX:**
- Tabbed output (Console | Results table)
- Hash input: Direct text or file upload
- Mask input field (appears only in Mask mode)
- Results display columns: Hash | Username | Password
- Auto-extracts cracked passwords using `john --show`
- Saves to `/tmp/Vajra-results/{timestamp}/john.txt`
- Copy results button

**Command Generation:**  
`john --format={format} --wordlist={wordlist} {hash_file} --fork={N}` (varies by attack mode)

---

### **10. Nmap (`nmap.py`)**

**Category**: PORT_SCANNING  
**Description**: Industry-standard network scanner with comprehensive port scanning and service detection.

**Features:**

#### **Scan Types:**
- **TCP SYN Scan** (`-sS`): Stealth half-open scan (requires root)
- **TCP Connect** (`-sT`): Full TCP connection scan
- **UDP Scan** (`-sU`): UDP port scanning (slow)
- **Service/Version Detection** (`-sV`): Banner grabbing & version detection
- **OS Detection** (`-O`): Operating system fingerprinting
- **Aggressive** (`-A`): Combines -sV, -O, traceroute, -sC

#### **Host Discovery:**
- **Normal Discovery**: Standard ping before scanning
- **Skip Ping** (`-Pn`): Treat all hosts as online
- **ARP Ping**: Local network discovery

#### **Timing Templates** (`-T`):
- Paranoid (0), Sneaky (1), Polite (2), Normal (3), Aggressive (4), Insane (5)

#### **NSE Scripts:**
- **Searchable Dropdown**: Dynamic list from Nmap script directory
- **Multiple Script Selection**: Comma-separated script names
- **Script Categories**: Default, vuln, exploit, discovery, auth, brute, malware

**Advanced Options:**
- **Port Range**: Custom port specification (1-1000, 80,443,8080, etc.)
- **Exclude Hosts**: Skip specific IPs/subnets
- **Output Formats**: XML, Normal, Grepable (auto-saves all 3)

**UI/UX:**
- Dropdown for scan type, host discovery, and timing
- Script selector with autocomplete
- Results saved to `Scans/nmap_{timestamp}.{xml,nmap,gnmap}`

**Command Generation:**  
`nmap {scan_type} {host_discovery} {timing} -p {ports} --script {scripts} -oA {output_prefix} {target}`

---

### **11. Port Scanner (`portscanner.py`)**

**Category**: PORT_SCANNING  
**Description**: Custom Python-based port scanner with stealth capabilities.

**Features:**

#### **3 Scan Types:**
1. **TCP Connect**: Full three-way handshake (reliable, detectable)
2. **SYN Scan**: Half-open scan (stealth, requires root/raw sockets)
3. **UDP Scan**: Connectionless protocol scanning (slow, unreliable)

#### **Port Range Options:**
- **Common Ports**: 50 most common ports (21, 22, 23, 25, 80, 443, etc.)
- **Top 1000**: Nmap's top 1000 most commonly open ports
- **All Ports**: Full range 1-65535 (very slow)
- **Custom Range**: User-defined (e.g., 1-1024, 80,443,8080)

**Advanced Features:**
- **Banner Grabbing**: Attempts to retrieve service banners
- **Service Identification**: Maps ports to known services (FTP:21, SSH:22, etc.)
- **Stealth Mode**: Adds randomization and delays to avoid IDS detection
- **Thread Control**: 1-500 concurrent threads (default: 100)
- **Randomize Port Order**: Evade sequential scanning detection
- **Inter-Scan Delay**: Millisecond delay between port probes

**UI/UX:**
- Live progress bar (scanned/total ports)
- Real-time results table: Port | State | Service | Banner
- Tabbed output (Console | Results table)
- Results saved to `Scans/portscan_{timestamp}.txt`
- Copy results to clipboard

**Command Generation:**  
Pure Python implementation using `socket` module, `ThreadPoolExecutor` for concurrency, and raw socket support for SYN scans.

---

### **12. Amass (`amass.py`)**

**Category**: SUBDOMAIN_ENUMERATION  
**Description**: OWASP Amass - Advanced subdomain enumeration using OSINT techniques.

**Features:**
- **Passive Enumeration**: API queries to public sources (no direct contact with target)
- **Active Enumeration**: DNS brute-forcing and zone walking
- **Output File**: Saves to `Subdomains/amass.txt`
- **Batch Processing**: Queue-based processing for multiple domains

**UI/UX:**
- Minimal configuration (leverages Amass defaults)
- Real-time output streaming
- Appends file results to console after completion

**Command Generation:**  
`amass enum -d {domain} -o {output_file}`

---

### **13. Subfinder (`subfinder.py`)**

**Category**: SUBDOMAIN_ENUMERATION  
**Description**: Fast passive subdomain discovery tool using public sources.

**Features:**
- **Passive-Only**: No active DNS queries (stealthy)
- **Silent Mode**: Clean output for automation
- **Multi-Source**: Queries 40+ sources (Censys, Shodan, VirusTotal, etc.)
- **Batch Processing**: Queue-based multi-domain support

**UI/UX:**
- Minimal interface
- Saves to `Subdomains/subfinder.txt`
- Real-time subdomain display

**Command Generation:**  
`subfinder -d {domain} -silent -o {output_file}`

---

### **14. Whois (`whois.py`)**

**Category**: INFO_GATHERING  
**Description**: Domain registration and ownership information lookup.

**Features:**
- **Domain Registrar**: Registrar name and WHOIS server
- **Registration Dates**: Created, updated, expires
- **Nameservers**: Authoritative DNS servers
- **Registrant Contact**: Organization, location (if not redacted)
- **Batch Processing**: Multi-domain queue support

**UI/UX:**
- Single target input
- Saves to `Logs/whois.txt`
- Plain text output display

**Command Generation:**  
`whois {domain}`

---

### **15. Dencoder (`dencoder.py`)**

**Category**: CRACKER  
**Description**: Multi-purpose encoding/decoding tool with 50+ operations.

**Features:**

#### **50+ Operations** including:
- **Base Encodings**: Base16, Base32, Base64, Base85, ASCII85
- **URL Encoding**: Encode/decode, double encode
- **HTML Entity**: Encode/decode
- **Hashing**: MD5, SHA1, SHA2-256/384/512, BLAKE2
- **JWT**: Header decode, payload decode
- **Security Payloads**:
  - XSS Basic/Advanced/Tag-based
  - SQL Hex Encode, CHAR() encode
  - Path Traversal (../, URL-encoded)
  - Command Injection, CRLF Injection
  - XXE (XML External Entity)
  - SSTI (Server-Side Template Injection)
- **Character Conversion**: Binary, Decimal, Octal, Hex, Morse Code
- **Case Conversion**: Uppercase, lowercase, titlecase, swapcase
- **ROT Ciphers**: ROT13, ROT47
- **Unicode**: Punycode encode/decode, Unicode escape

**UI/UX:**
- **Searchable Dropdown**: Type to filter 50+ operations instantly
- **Input/Output Panels**: Side-by-side text areas
- **Copy Buttons**: Quick clipboard copy for input/output
- **Process/Clear**: Execute operation or clear all fields
- **Error Handling**: User-friendly error messages for invalid input

**Command Generation:**  
Pure Python implementation using `base64`, `urllib.parse`, `html`, `hashlib`, `json`, and custom transformation logic.

---

### **16. Gobuster (Already documented above)**

---

## 📊 Tool Statistics Summary

| Tool | Category | Features | LOC |
|------|----------|----------|-----|
| **Automation** | AUTOMATION | 6-step pipeline, skip/stop controls | 335 |
| **Gobuster** | WEB_SCANNING | 5 modes (Dir/DNS/VHost/Fuzz/S3) | 829 |
| **Dig** | INFO_GATHERING | 10 DNS query types, multi-select | 342 |
| **DNSRecon** | INFO_GATHERING | 8 scan modes, conditional wordlist | 295 |
| **Eyewitness** | WEB_SCREENSHOTS | Screenshot capture, batch processing | 271 |
| **Hashcat** | CRACKER | 180+ hash types, 4 attack modes | 867 |
| **Httpx** | LIVE_SUBDOMAINS | Live host detection, JSON output | 108 |
| **Hydra** | CRACKER | 50+ services, 4 credential modes | 1077 |
| **John** | CRACKER | 100+ formats, 4 attack modes | 1195 |
| **Nmap** | PORT_SCANNING | Comprehensive scanning, NSE scripts | 503 |
| **PortScanner** | PORT_SCANNING | 3 scan types, stealth mode | 796 |
| **Amass** | SUBDOMAIN_ENUMERATION | OSINT subdomain enumeration | 101 |
| **Subfinder** | SUBDOMAIN_ENUMERATION | Passive subdomain discovery | 101 |
| **Whois** | INFO_GATHERING | Domain registration info | 97 |
| **Dencoder** | CRACKER | 50+ encode/decode operations | 48,310 |
| **Strings** | FILE_ANALYSIS | **[DUPLICATE]** Identical to Dencoder | 48,310 |

**Total**: 17 tools (16 unique + 1 duplicate) | ~104,000+ lines of code

---

## 🎨 Common UI/UX Patterns

### **1. BaseToolView Architecture**

All tools (except Automation, Hashcat, Hydra, John, PortScanner) inherit from `BaseToolView`, providing:
- **Standard Layout**: Target input → Configuration → Command preview → Run/Stop buttons → Output panel
- **Target Input** (`TargetInput`): Validates URLs, domains, IPs, file paths
- **Command Preview**: Live-updating editable command line
- **Output View**: Syntax-highlighted console with colored status messages
- **File Management**: Auto-creates organized directory structure: `{target}/Logs/`, `{target}/Subdomains/`, etc.

### **2. Real-Time Output Streaming**

Tools use `ProcessWorker` (QThread) for non-blocking subprocess execution:
```python
self.worker = ProcessWorker(command_list)
self.worker.output_ready.connect(self._handle_output)  # Line-by-line output
self.worker.finished.connect(self._on_scan_completed)  # Cleanup
self.worker.error.connect(self._error)  # Error handling
self.worker.start()
```

###  **3. Batch Processing Queue**

Tools like Amass, Subfinder, Whois, Httpx implement queue-based processing:
```python
self.targets_queue = list(targets)
self.group_name = get_group_name_from_file(file) if source == "file" else None

def _process_next_target(self):
    if not self.targets_queue:
        self._on_scan_completed()
        return
    target = self.targets_queue.pop(0)
    # Execute scan for target
```

### **4. Dynamic Command Generation**

All tools implement `update_command()` connected to UI element change signals:
```python
self.target_input.textChanged.connect(self.update_command)
self.mode_combo.currentIndexChanged.connect(self.update_command)
self.threads_spin.valueChanged.connect(self.update_command)
```

### **5. Status Message Color Coding**

Consistent message formatting across all tools:
- **Info** (`_info()`): `[INFO]` in blue
- **Success** (`_success()`): `[SUCCESS]` in green
- **Warning** (`_warning()`): `[WARNING]` in amber
- **Error** (`_error()`): `[ERROR]` in red
- **Section** (`_section()`): `=== SECTION ===` in bold

---

## 🔄 Plugin Discovery & Loading

### **Step 1: Dynamic Tool Discovery**

`main_window.py` automatically discovers tools using Python introspection:
```python
def _discover_tools(self):
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

### **Step 2: Sidepanel Categorization**

`sidepanel.py` groups tools by `ToolCategory` enum:
```python
categorized_tools = defaultdict(list)
for tool in self.tools.values():
    categorized_tools[tool.category].append(tool)

# Sort categories by enum order
sorted_categories = sorted(categorized_tools.keys(), 
                           key=lambda x: list(ToolCategory).index(x))

# Create collapsible UI for each category
for category in sorted_categories:
    sorted_tools = sorted(categorized_tools[category], key=lambda x: x.name)
    for tool in sorted_tools:
        button = self._add_tool_button(tool)
        button.clicked.connect(lambda t=tool: self.open_tool_tab(t))
```

### **Step 3: Tab Management**

`main_window.py` implements singleton tab pattern:
```python
def open_tool_tab(self, tool: ToolBase):
    # Reuse existing tab if already open
    if tool.name in self.open_tool_widgets:
        self.tab_widget.setCurrentWidget(self.open_tool_widgets[tool.name])
        return
    
    # Create new tab
    tool_widget = tool.get_widget(main_window=self)
    index = self.tab_widget.addTab(tool_widget, tool.name)
    
    # Add close button
    close_btn = QPushButton("✕")
    close_btn.clicked.connect(lambda: self.close_tab(index))
    self.tab_widget.tabBar().setTabButton(index, QTabBar.RightSide, close_btn)
    
    self.open_tool_widgets[tool.name] = tool_widget
```

---

## 🎨 Centralized Styling System (`ui/styles.py`)

### **Dark Theme Colors:**
```python
COLOR_BACKGROUND_PRIMARY = "#1E1E1E"         # Main editor background
COLOR_BACKGROUND_SECONDARY = "#1C1C1C"        # Sidebar/panels
COLOR_BACKGROUND_INPUT = "#3C3C3C"            # Input fields
COLOR_BACKGROUND_SIDEPANEL_DARK = "#121212"   # Darker sidepanel

COLOR_TEXT_PRIMARY = "#FFFFFF"                # Main text
COLOR_TEXT_SECONDARY = "#8B8B8B"              # Secondary/placeholder

COLOR_BORDER = "#333333"
COLOR_BORDER_INPUT_FOCUSED = "#F59E0B"        # Amber highlight on focus

COLOR_SUCCESS = "#28A745"                     # Green
COLOR_WARNING = "#FFC107"                      # Amber
COLOR_ERROR = "#DC3545"                       # Red
COLOR_INFO = "#17A2B8"                        # Cyan
```

### **Reusable Styled Components:**
- **StyledComboBox**: Dropdown with dark theme styling
- **StyledSpinBox**: Number input with custom arrows
- **TargetInput**: Auto-completing input for domains/IPs/files
- **OutputView**: Syntax-highlighted console output
- **RUN_BUTTON_STYLE**: Amber button with hover/active states
- **STOP_BUTTON_STYLE**: Red stop button

---

## 📁 File Management & Directory Structure

Tools automatically create organized directories using `core/fileops.py`:

```
{RESULT_BASE}/
└── {target}/
    ├── Logs/              # whois.txt, dig.txt, dnsrecon.txt
    ├── Subdomains/        # amass.txt, subfinder.txt, merged_subdomains.txt
    ├── Probed/            # httpx_probed.txt
    ├── Scans/             # nmap_scan.xml, portscan.txt
    ├── Httpx/             # httpx.json
    ├── Eyewitness/        # eyewitness_{timestamp}/
    └── Reports/           # final_report.html
```

Groups (for batch scans from file):
```
{RESULT_BASE}/
└── {group_name}/
    └── {target1}/
        ├── Logs/
        └── ...
    └── {target2}/
        ├── Logs/
        └── ...
```

---

## 🚨 Identified Issues and Recommendations

### **1. Duplicate File: `modules/strings.py` ❌**
**Issue**: The `modules/strings.py` file is an exact duplicate of `modules/dencoder.py`.
**Status**: Both files contain identical code, classes, and functionality.
**Impact**: Causes redundancy and confusion - both appear as separate tools in the UI.
**Recommendation**: 
- **CORRECTED**: Both files serve different purposes:
  - **`strings.py`**: Binary file analysis tool (FILE_ANALYSIS category) - extracts readable strings from executables, memory dumps
  - **`dencoder.py`**: Encoder/decoder tool (CRACKER category) - converts between text encoding formats
- No action needed - both are valid, distinct tools.

### **2. Gobuster Dead Code: GCS/TFTP Modes ✅**
**Status**: **FIXED** - Dead code has been removed.
**What was removed**:
- Removed `idx == 5` (gcs) and `idx == 6` (tftp) from `_get_active_mode()`
- Removed TFTP target handling: `elif mode == "tftp": cmd_parts.extend(["-s", target])`
- Removed GCS from S3 mode check: `elif mode in ["s3", "gcs"]:` → `elif mode == "s3":`

### **3. Inconsistent Base Class Usage**
- **Tools Using BaseToolView**: Amass, Subfinder, Whois, Httpx, Dig, DNSRecon, Gobuster, Eyewitness
- **Custom Implementations**: Automation, Hashcat, Hydra, John, PortScanner, Dencoder
- **Recommendation**: Standardize on `BaseToolView` for consistency

---

## 🎯 How to Add a New Tool

```python
# 1. Create modules/mytool.py

from modules.bases import ToolBase, ToolCategory
from ui.widgets import BaseToolView
from ui.worker import ProcessWorker

class MyTool(ToolBase):
    @property
    def name(self) -> str:
        return "My Custom Tool"
    
    @property
    def category(self):
        return ToolCategory.INFO_GATHERING
    
    def get_widget(self, main_window):
        return MyToolView("My Custom Tool", self.category, main_window)

class MyToolView(BaseToolView):
    def __init__(self, name, category, main_window):
        super().__init__(name, category, main_window)
        # Custom UI initialization here
    
    def update_command(self):
        target = self.target_input.get_target().strip()
        self.command_input.setText(f"mytool --scan {target}")
    
    def run_scan(self):
        command = self.command_input.text().split()
        self.worker = ProcessWorker(command)
        self.worker.output_ready.connect(self.output.appendPlainText)
        self.worker.finished.connect(self._on_scan_completed)
        self.worker.start()
```

**Result**: Tool automatically appears in "INFO GATHERING" category, inherits standard layout, output handling, and file management.

---

## 📊 Visual Hierarchy

```
MAIN WINDOW (1200x800)
│
├── SIDEPANEL (260px wide, dark #121212)
│   ├── [Header] "VAJRA" (centered, bold)
│   ├── [Scroll Area]
│   │   ├── ▾ AUTOMATION
│   │   │   └── Automation
│   │   ├── ▾ INFO GATHERING
│   │   │   ├── Dig
│   │   │   ├── DNSRecon
│   │   │   └── Whois
│   │   ├── ▾ SUBDOMAIN ENUMERATION
│   │   │   ├── Amass
│   │   │   └── Subfinder
│   │   ├── ▾ LIVE SUBDOMAINS
│   │   │   └── Httpx
│   │   ├── ▾ PORT SCANNING
│   │   │   ├── Nmap
│   │   │   └── Port Scanner
│   │   ├──  ▾ WEB SCANNING
│   │   │   └── Gobuster
│   │   ├── ▾ WEB SCREENSHOTS
│   │   │   └── Eyewitness
│   │   └── ▾ CRACKER
│   │       ├── Dencoder
│   │       ├── Hashcat
│   │       ├── Hydra
│   │       └── John
│   └── [Footer] ⚙️ Settings
│
└── CONTENT AREA (flex, dark gray #1E1E1E)
    └── TAB WIDGET
        ├── [Tab 1: Automation] (with ✕ close button)
        ├── [Tab 2: Gobuster] (with ✕ close button)
        └── ...
```

**Sidepanel Button States:**
- **Default**: Dark background (#121212), gray text (#8B8B8B)
- **Hover**: Lighter background (#1C1C1C), white text
- **Active**: Amber background (#F59E0B), white bold text

---

## 🚀 Conclusion

VAJRA is a **comprehensive, professional-grade offensive security platform** with:

✅ **17 Specialized Tools** covering reconnaissance, enumeration, scanning, and exploitation  
✅ **Plugin Architecture** for easy extensibility  
✅ **Automated Workflows** with 6-step pipeline  
✅ **Batch Processing** for multi-target engagements  
✅ **Consistent UI/UX** with dark theme and intuitive navigation  
✅ **Real-Time Output** streaming and progress tracking  
✅ **Organized File Management** with auto-generated directory structures  
✅ **Advanced Features**: Stealth scanning, GPU acceleration, 180+ hash types, 50+ services  

⚠️ **Known Issues**:
- Duplicate `strings.py` file (should be deleted)
- Gobuster dead code for GCS/TFTP modes

**Total Project**: ~104,000 lines of Python code, 17 tools, 8 categories, fully integrated Qt-based UI.
