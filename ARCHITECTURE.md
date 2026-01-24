# VAJRA Architecture

**Technical Architecture Overview**

This document describes the internal architecture, design patterns, and technical implementation of VAJRA-OSP.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architectural Principles](#architectural-principles)
3. [Directory Structure](#directory-structure)
4. [Core Components](#core-components)
5. [UI Layer](#ui-layer)
6. [Plugin System](#plugin-system)
7. [Process Management](#process-management)
8. [Data Flow](#data-flow)
9. [Styling System](#styling-system)
10. [Build System](#build-system)
11. [Security Considerations](#security-considerations)

---

## System Overview

VAJRA is architected as a **layered Qt application** with a strict separation between business logic and UI:

```
┌─────────────────────────────────────┐
│        Application Layer            │
│         (main.py)                   │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│         UI Layer (ui/)              │
│  - Main Window                      │
│  - Sidepanel (Navigation)           │
│  - Settings Panel                   │
│  - Notification System              │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│      Plugin Layer (modules/)        │
│  - 31 Tool Implementations          │
│  - ToolBase Interface               │
│  - Auto-discovery System            │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│       Core Layer (core/)            │
│  - Configuration                    │
│  - File Operations                  │
│  - Privilege Management             │
│  - Target Parsing                   │
│  - JSON Aggregation                 │
│  - Tool Installation                │
└─────────────────────────────────────┘
```

---

## Architectural Principles

### 1. **Qt-Free Core**
All business logic in `core/` is framework-agnostic Python. This enables:
- Unit testing without Qt runtime
- CLI integration potential
- Cross-platform compatibility
- Minimal dependencies for core logic

### 2. **Plugin Architecture**
Tools are self-contained modules that conform to `ToolBase`:
- **Auto-discovery**: New tools are automatically detected
- **Loose coupling**: Tools don't depend on each other
- **Easy extension**: Add tools without modifying core code

### 3. **Worker-Based Concurrency**
Long-running operations use `QThread` workers:
- Non-blocking UI during scans
- Clean process lifecycle management
- Signal-based communication for thread safety

### 4. **Centralized Styling**
All UI styling lives in `ui/styles.py`:
- Single source of truth for colors and fonts
- Consistent look across components
- Easy theming support

### 5. **Dependency Injection**
Tools receive `main_window` reference for:
- Access to shared services (config, notifications)
- Controlled coupling to UI layer
- Testability

---

## Directory Structure

```
VAJRA-OSP/
├── main.py                     # Application entry point
│
├── core/                       # Qt-free business logic
│   ├── config.py              # Settings persistence (QSettings wrapper)
│   ├── fileops.py             # File I/O, directory creation, caching
│   ├── privileges.py          # Root/admin privilege detection
│   ├── tgtinput.py            # Target parsing and validation
│   ├── jsonparser.py          # Tool output aggregation
│   ├── tool_installer.py      # Cross-platform tool installation
│   └── reportgen.py           # HTML/PDF report generation
│
├── ui/                        # PySide6 UI components
│   ├── main_window.py         # Main application window
│   ├── sidepanel.py           # Tool navigation sidebar
│   ├── settingpanel.py        # Settings interface
│   ├── notification.py        # Toast and panel notifications
│   ├── worker.py              # Generic worker thread base
│   ├── styles.py              # Unified stylesheet definitions
│   └── bases.py               # Shared UI mixins
│
├── modules/                   # Tool plugins (auto-discovered)
│   ├── bases.py              # ToolBase, ToolCategory definitions
│   ├── nmap.py               # Nmap scanner
│   ├── nuclei.py             # Nuclei vulnerability scanner
│   ├── automation.py         # 8-step recon pipeline
│   ├── subfinder.py          # Subdomain enumeration
│   ├── httpx.py              # HTTP probing
│   ├── gobuster.py           # Web brute-forcing
│   ├── nikto.py              # Web server scanning
│   ├── portscanner.py        # Native Python port scanner
│   ├── shellforge.py         # Reverse shell generator
│   ├── hashcat.py            # GPU hash cracking
│   ├── WebInjection/         # Web security testing
│   │   ├── sqli.py          # SQL injection detection
│   │   ├── crawler.py       # Web spider
│   │   ├── apitester.py     # API security auditing
│   │   └── fuzzer.py        # Endpoint fuzzing
│   └── [25 more tools...]
│
├── builder/                   # Nuitka build scripts
│   └── compile.sh            # Linux compilation
│
└── db/                        # Static resources
    ├── wordlists/            # Fuzzing/brute-force lists
    └── payloads/             # Injection templates
```

---

## Core Components

### ConfigManager (`core/config.py`)

Manages application settings using Qt's `QSettings`:

```python
# Persistent settings (stored in ~/.config/VAJRA/)
- notifications_enabled: bool
- output_directory: str
- privilege_mode: str

# Session-only settings
- current_output_dir: str (per-target directory)
```

**Key Methods:**
- `get_notifications_enabled()` / `set_notifications_enabled()`
- `get_output_dir()` / `set_output_dir()`

### FileOps (`core/fileops.py`)

Handles file I/O and directory structure:

```python
DEFAULT_OUTPUT_DIR = "/tmp/Vajra-results/"

# Creates: /tmp/Vajra-results/{target}_{timestamp}/
create_target_directory(target: str) -> str
    ├── Logs/
    ├── JSON/
    ├── Reports/
    └── Screenshots/
```

**Caching System:**
- Simple pickle-based cache for tool state
- `save_cache(tool_name, data)` / `load_cache(tool_name)`

### PrivilegeManager (`core/privileges.py`)

Cross-platform privilege detection:

```python
is_running_as_root() -> bool  # Unix: uid == 0, Windows: admin check
```

Used to warn users when tools require elevated privileges.

### Target Input (`core/tgtinput.py`)

Target parsing utilities:

```python
normalize_target(target: str) -> str
    # Cleans URLs: https://example.com/path → example.com

parse_targets(input_text: str) -> list[str]
    # Handles single targets or file paths
    # Returns: ["target1", "target2", ...]

parse_port_range(port_str: str) -> list[int]
    # "80,443,8000-8010" → [80, 443, 8000, 8001, ..., 8010]
```

### FinalJsonGenerator (`core/jsonparser.py`)

Aggregates tool outputs into `final.json`:

**Supported Parsers:**
- `parse_whois_output()`
- `parse_dig_output()`
- `parse_nmap_output()`
- `parse_nuclei_output()`
- `parse_nikto_output()`
- `parse_eyewitness_output()`

**Output Format:**
```json
{
  "target": "example.com",
  "scan_time": "2026-01-22 17:00:00",
  "risk_level": "HIGH",
  "tools": {
    "nmap": { "open_ports": [...], "services": [...] },
    "nuclei": { "vulnerabilities": [...] },
    ...
  }
}
```

### ToolInstaller (`core/tool_installer.py`)

Automated security tool installation:

**Supported Package Managers:**
- Debian/Ubuntu/Kali: `apt`
- Arch Linux: `pacman`
- Fedora/RHEL: `dnf`
- macOS: `brew`
- Go tools: `go install`

**Tool Definitions:**
```python
ToolDefinition(
    name="nmap",
    command="nmap",
    package_name={"debian": "nmap", "arch": "nmap", ...},
    install_method=InstallMethod.PACKAGE_MANAGER
)
```

### ReportGen (`core/reportgen.py`)

HTML/PDF report generation:
- Aggregates findings from `final.json`
- Generates styled HTML reports
- Optional PDF conversion (requires wkhtmltopdf)

---

## UI Layer

### MainWindow (`ui/main_window.py`)

Central application controller:

**Responsibilities:**
- Window initialization and layout
- Tool switching logic
- Shared service coordination (config, notifications)
- Keyboard shortcut handling

**Layout:**
```
┌──────────────────────────────────────┐
│  Title Bar                           │
├─────────┬────────────────────────────┤
│         │                            │
│ Side    │   Tool Content Area        │
│ Panel   │   (Dynamic)                │
│         │                            │
│ (Tools) │                            │
│         │                            │
├─────────┴────────────────────────────┤
│  Notification Panel (collapsible)    │
└──────────────────────────────────────┘
```

### Sidepanel (`ui/sidepanel.py`)

Dynamic tool navigation:

**Auto-population:**
1. Imports all modules from `modules/`
2. Finds classes inheriting from `ToolBase`
3. Groups by `ToolCategory`
4. Creates buttons dynamically

**Categories:**
- AUTOMATION
- INFO_GATHERING
- SUBDOMAIN_ENUM
- LIVE_HOST_DETECTION
- PORT_SCANNING
- WEB_SCANNING
- WEB_INJECTION
- VULN_SCANNING
- PASSWORD_CRACKING
- PAYLOAD_GENERATION
- FILE_ANALYSIS

### NotificationManager (`ui/notification.py`)

Dual notification system:

**Toast Notifications:**
- Auto-hide popups (3-4s)
- Positioned at top-right
- Color-coded by type (success/error/warning/info)

**Notification Panel:**
- Persistent notification list
- Expandable/collapsible
- Timestamp tracking
- Clear all functionality

### Worker (`ui/worker.py`)

Generic background worker:

```python
class GenericWorker(QThread):
    output_ready = Signal(str)
    scan_finished = Signal(int)
    error_occurred = Signal(str)
    
    def run(self):
        # Execute command
        # Emit output line-by-line
        # Handle errors
```

**Benefits:**
- Non-blocking UI
- Real-time output streaming
- Clean process termination

---

## Plugin System

### ToolBase Interface

All tools inherit from `ToolBase`:

```python
class ToolBase:
    name: str                  # Display name
    category: ToolCategory     # Sidebar grouping
    
    def get_widget(self, main_window) -> QWidget:
        """Return the tool's UI widget"""
        pass
```

### Auto-Discovery

Tools are discovered at runtime:

```python
# In Sidepanel.__init__()
import modules
for name in dir(modules):
    cls = getattr(modules, name)
    if isinstance(cls, type) and issubclass(cls, ToolBase):
        # Found a tool! Create button and register it
```

**To add a new tool:**
1. Create `modules/newtool.py`
2. Subclass `ToolBase`
3. Set `name` and `category`
4. Implement `get_widget()`
5. Tool appears automatically in sidebar

### Tool Implementation Pattern

**Mixin Composition:**
```python
class MyTool(ToolBase, IOMixin, RunMixin):
    """ToolBase provides interface"""
    """IOMixin provides input/output widgets"""
    """RunMixin provides run button and worker management"""
    
    def get_widget(self, main_window):
        widget = QWidget()
        # Build UI
        return widget
```

**Common Mixins:**
- `IOMixin` - Input field, output text area
- `RunMixin` - Run/stop buttons, worker lifecycle
- `CommandBuilderMixin` - Command construction helpers

---

## Process Management

### Worker Lifecycle

```
User clicks RUN
    ↓
Create GenericWorker(command)
    ↓
worker.start()  [New thread]
    ↓
worker.output_ready → Update UI
worker.scan_finished → Cleanup
    ↓
User clicks STOP (optional)
    ↓
worker.terminate()
worker.wait()
```

### Command Execution

Tools use `subprocess.Popen` with:
- `stdout=PIPE` for line-by-line streaming
- `stderr=STDOUT` to merge error output
- `text=True` for string handling
- `bufsize=1` for unbuffered output

### Signal-Slot Communication

Thread-safe UI updates:

```python
# In worker thread
self.output_ready.emit(line)

# In main thread (auto-queued)
@Slot(str)
def handle_output(self, line):
    self.output_area.append(line)
```

---

## Data Flow

### Typical Scan Workflow

```
1. User Input
   └→ Target entered in TargetInput widget

2. Validation
   └→ normalize_target() / parse_targets()

3. Directory Creation
   └→ create_target_directory(target)
      Creates: /tmp/Vajra-results/target_timestamp/

4. Command Building
   └→ Tool builds command string
      Example: ["nmap", "-sV", "-p-", "target"]

5. Execution
   └→ GenericWorker spawns subprocess
      Streams output to UI in real-time

6. Output Logging
   └→ Write to Logs/tool_name.log

7. JSON Parsing (optional)
   └→ FinalJsonGenerator.parse_tool_output()
      Creates: JSON/final.json

8. Report Generation (automation only)
   └→ ReportGen.generate_report()
      Creates: Reports/report.html
```

### Configuration Flow

```
Application Start
    ↓
ConfigManager loads QSettings
    ├→ notifications_enabled
    ├→ output_directory
    └→ [other persistent settings]
    ↓
User modifies settings via SettingsPanel
    ↓
ConfigManager.set_*() persists changes
    ↓
Changes take effect immediately
```

---

## Styling System

### Centralized Design (`ui/styles.py`)

**Color Palette:**
```python
BG_DARK = "#1a1a2e"
BG_CARD = "#16213e"
BG_HOVER = "#0f3460"
ACCENT = "#e94560"
TEXT_PRIMARY = "#eee"
TEXT_SECONDARY = "#aaa"
SUCCESS = "#2ecc71"
WARNING = "#f39c12"
ERROR = "#e74c3c"
```

**QSS Stylesheets:**
- `get_main_window_style()` - Window background and layout
- `get_sidepanel_style()` - Navigation buttons
- `get_textbox_style()` - Input fields
- `get_output_area_style()` - Output console
- `get_button_style()` - Action buttons
- `get_settings_style()` - Settings panel
- `get_notification_style()` - Toast notifications

**Usage:**
```python
from ui.styles import get_button_style, ACCENT

button = QPushButton("RUN")
button.setStyleSheet(get_button_style())
```

### Color-Coded Output

Tools colorize output for readability:

```python
def colorize_line(line: str) -> str:
    if "CRITICAL" in line or "FAIL" in line:
        return f'<span style="color: {ERROR};">{line}</span>'
    elif "open" in line.lower():
        return f'<span style="color: {SUCCESS};">{line}</span>'
    # ... more patterns
```

---

## Build System

### Nuitka Compilation (`builder/compile.sh`)

**Build Process:**
```bash
python -m nuitka \
    --standalone \
    --onefile \
    --enable-plugin=pyside6 \
    --include-data-dir=db=db \
    --linux-icon=icon.png \
    --output-filename=VAJRA \
    main.py
```

**Output:**
- Single executable: `VAJRA`
- Bundled dependencies (PySide6, etc.)
- Embedded resources (`db/` folder)

**Build Requirements:**
- Python 3.10+
- Nuitka
- PySide6
- gcc/clang compiler

---

## Security Considerations

### Privilege Escalation

**Design Decision:** VAJRA runs as normal user by default.

**Tools requiring root:**
- Nmap (SYN scans)
- Port Scanner (raw sockets)

**Approach:**
1. Check privileges: `PrivilegeManager.is_running_as_root()`
2. Warn user if insufficient
3. Let user decide: run with `sudo` or use limited features

### Command Injection Prevention

**Input Sanitization:**
```python
# ❌ UNSAFE
command = f"nmap {user_input}"

# ✅ SAFE
command = ["nmap", user_input]  # List form prevents shell injection
```

All tools use **list-based commands**, not shell strings.

### Output Directory Isolation

Each scan gets an isolated directory:
```
/tmp/Vajra-results/
├── example.com_22012026_170000/
└── test.com_22012026_180000/
```

Prevents:
- Output collision between scans
- Accidental file overwrites

---

## Performance Optimizations

### 1. **Lazy Loading**
Tools are imported only when accessed:
```python
# Sidebar imports all, but widgets created on-demand
def switch_tool(self, tool_name):
    widget = tool_class.get_widget(main_window)  # Created here
```

### 2. **Threaded Execution**
Long-running scans don't block UI:
- Worker threads for subprocess execution
- Signal-based asynchronous communication

### 3. **Smart Caching**
Avoid redundant computations:
```python
# Cache wordlist contents
cached_wordlists = load_cache("wordlists")
if not cached_wordlists:
    cached_wordlists = load_wordlists_from_db()
    save_cache("wordlists", cached_wordlists)
```

### 4. **Incremental Output**
Stream output line-by-line instead of buffering:
```python
for line in process.stdout:
    self.output_ready.emit(line)  # Immediate display
```

---

## Extension Points

### Adding a New Tool

1. **Create plugin file:**
```python
# modules/mytool.py
from modules.bases import ToolBase, ToolCategory

class MyTool(ToolBase):
    name = "My Tool"
    category = ToolCategory.INFO_GATHERING
    
    def get_widget(self, main_window):
        return MyToolWidget(main_window)
```

2. **Implement widget:**
```python
class MyToolWidget(QWidget, IOMixin, RunMixin):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()
    
    def build_command(self):
        return ["mytool", "--target", self.target]
```

3. **Done!** Tool appears in sidebar automatically.

### Adding a New Category

Edit `modules/bases.py`:
```python
class ToolCategory:
    MY_NEW_CATEGORY = "My Category"
```

### Custom Output Parsers

Add to `core/jsonparser.py`:
```python
def parse_mytool_output(self, log_file):
    # Parse tool-specific output
    # Return structured dict
    return {"findings": [...]}
```

---

## Design Patterns

### 1. **Plugin Pattern**
- Tools as self-contained plugins
- Auto-discovery via reflection
- Loose coupling

### 2. **Observer Pattern**
- Qt Signals/Slots for event handling
- Worker → UI communication
- Settings changes propagation

### 3. **Factory Pattern**
- Dynamic widget creation
- Tool instantiation on-demand

### 4. **Singleton Pattern**
- `ConfigManager` - Single settings instance
- `NotificationManager` - Centralized notifications

### 5. **Mixin Pattern**
- `IOMixin`, `RunMixin` for code reuse
- Composition over inheritance

---

## Related Documentation

- **[README.md](README.md)** - User-facing overview and quick start
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development workflow and practices
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

---

**Last Updated:** 2026-01-22
