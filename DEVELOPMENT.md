# VAJRA Development Guide

**Comprehensive guide for developers contributing to VAJRA-OSP**

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Project Structure](#project-structure)
4. [Development Workflow](#development-workflow)
5. [Adding New Tools](#adding-new-tools)
6. [Code Style](#code-style)
7. [Building for Distribution](#building-for-distribution)
8. [Debugging](#debugging)
9. [Common Tasks](#common-tasks)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

```bash
# Python 3.10+ (3.11+ recommended)
python3 --version

# Pip package manager
pip --version

# Git version control
git --version

# Optional: Virtual environment
python3 -m venv --help
```

### Recommended Tools

- **IDE**: VS Code, PyCharm, or any Python IDE
- **Terminal**: For running commands and viewing logs
- **Security tools**: Install the ones you plan to work with

---

## Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd VAJRA-OSP
```

### 2. Create Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Verify PySide6 installation
python -c "from PySide6.QtWidgets import QApplication; print('PySide6 OK')"
```

### 4. Install Security Tools (Optional)

```bash
# Debian/Ubuntu/Kali
sudo apt update
sudo apt install -y nmap nuclei subfinder httpx-toolkit gobuster \
    nikto ffuf amass dnsutils hashcat john hydra

# Or use VAJRA's built-in installer:
# python main.py → Settings → Tool Installer
```

### 5. Run VAJRA

```bash
python main.py
```

---

## Project Structure

```
VAJRA-OSP/
├── main.py                 # Entry point - starts the Qt application
│
├── core/                   # Qt-free business logic
│   ├── config.py          # Settings persistence (QSettings)
│   ├── fileops.py         # File operations, directory creation
│   ├── privileges.py      # Privilege detection (root/admin)
│   ├── tgtinput.py        # Target parsing and validation
│   ├── jsonparser.py      # Tool output aggregation
│   ├── tool_installer.py  # Automated tool installation
│   └── reportgen.py       # HTML/PDF report generation
│
├── ui/                     # PySide6 UI components
│   ├── main_window.py     # Main application window
│   ├── sidepanel.py       # Tool navigation sidebar
│   ├── settingpanel.py    # Settings interface
│   ├── notification.py    # Notification system
│   ├── worker.py          # Background worker threads
│   ├── styles.py          # Centralized stylesheets
│   └── bases.py           # Shared UI mixins
│
├── modules/                # Tool plugins (31 tools)
│   ├── bases.py           # ToolBase, ToolCategory, Mixins
│   ├── automation.py      # Automated reconnaissance pipeline
│   ├── nmap.py           # Nmap integration
│   ├── nuclei.py         # Nuclei vulnerability scanner
│   ├── subfinder.py      # Subfinder subdomain enum
│   ├── httpx.py          # HTTPX probing
│   ├── gobuster.py       # Gobuster brute-forcing
│   ├── nikto.py          # Nikto web scanner
│   ├── portscanner.py    # Native Python port scanner
│   ├── shellforge.py     # Reverse shell generator
│   ├── hashcat.py        # Hashcat password cracking
│   ├── WebInjection/     # Web security testing tools
│   │   ├── sqli.py      # SQL injection detection
│   │   ├── crawler.py   # Web spider
│   │   ├── apitester.py # API security testing
│   │   └── fuzzer.py    # Web fuzzer
│   └── [other tools...]
│
├── builder/               # Build scripts
│   └── compile.sh        # Nuitka compilation
│
└── db/                    # Static resources
    ├── wordlists/        # Fuzzing wordlists
    └── payloads/         # Injection templates
```

### Key Directories

| Directory | Purpose | Contains |
|-----------|---------|----------|
| `core/` | Business logic | Qt-free modules, utilities |
| `ui/` | User interface | PySide6 widgets, styling |
| `modules/` | Tool plugins | All 31 tool implementations |
| `db/` | Resources | Wordlists, payloads |
| `builder/` | Compilation | Nuitka scripts |

---

## Development Workflow

### Typical Development Cycle

1. **Make changes** to code
2. **Test locally** with `python main.py`
3. **Verify functionality** of modified tool/feature
4. **Commit changes** with clear message
5. **Push** to your branch
6. **Create PR** for review

### Running Locally

```bash
# Activate virtual environment
source venv/bin/activate

# Run VAJRA
python main.py

# Run with verbose output (if implemented)
python main.py --verbose

# Run specific tool test (manual testing)
# Navigate to: Tool Category → Your Tool → Test with sample target
```

### Code Organization

**Where to put new code:**

| Task | Location | Example |
|------|----------|---------|
| New tool | `modules/` | `modules/mytool.py` |
| Core utility | `core/` | `core/myutil.py` |
| UI component | `ui/` | `ui/mywidget.py` |
| Styling | `ui/styles.py` | Add to existing file |
| Resource | `db/` | `db/wordlists/mylist.txt` |

---

## Adding New Tools

### Step-by-Step Guide

#### 1. Create Plugin File

```bash
touch modules/mytool.py
```

#### 2. Define Tool Class

```python
# modules/mytool.py
from modules.bases import ToolBase, ToolCategory, IOMixin, RunMixin
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class MyTool(ToolBase):
    """My custom security tool"""
    
    name = "My Tool"
    category = ToolCategory.INFO_GATHERING  # Choose appropriate category
    
    def get_widget(self, main_window):
        return MyToolWidget(main_window)
```

#### 3. Implement Widget

```python
class MyToolWidget(QWidget, IOMixin, RunMixin):
    """UI for MyTool"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Add title
        title = QLabel(f"<h2>{MyTool.name}</h2>")
        layout.addWidget(title)
        
        # IOMixin provides: self.setup_io()
        # - self.target_input (TargetInput widget)
        # - self.output_area (QTextEdit)
        self.setup_io(layout)
        
        # RunMixin provides: self.setup_run_controls()
        # - self.run_button (QPushButton)
        # - self.stop_button (QPushButton)
        # - self.clear_button (QPushButton)
        self.setup_run_controls(layout)
        
        self.setLayout(layout)
    
    def build_command(self):
        """Build command to execute"""
        target = self.target_input.get_targets()
        if not target:
            return None
        
        # Example: ["mytool", "--scan", "target"]
        return ["mytool", "--scan", target[0]]
    
    def run_scan(self):
        """Called when RUN button is clicked"""
        command = self.build_command()
        if not command:
            self.show_error("Please enter a target")
            return
        
        # RunMixin provides: self.start_worker(command)
        self.start_worker(command, tool_name="mytool")
```

#### 4. Test Your Tool

```bash
python main.py
# Navigate to your tool's category
# Click on "My Tool"
# Enter target and click RUN
```

#### 5. Done!

Your tool is now integrated. It will:
- Appear in the sidebar automatically
- Follow UI conventions
- Save output to `/tmp/Vajra-results/`

---

### Tool Categories

Choose the appropriate category:

```python
class ToolCategory:
    AUTOMATION = "Automation"
    INFO_GATHERING = "Information Gathering"
    SUBDOMAIN_ENUM = "Subdomain Enumeration"
    LIVE_HOST_DETECTION = "Live Host Detection"
    PORT_SCANNING = "Port Scanning"
    WEB_SCANNING = "Web Scanning"
    WEB_INJECTION = "Web Injection"
    VULN_SCANNING = "Vulnerability Scanning"
    PASSWORD_CRACKING = "Password Cracking"
    PAYLOAD_GENERATION = "Payload Generation"
    FILE_ANALYSIS = "File Analysis"
```

---

### Using Mixins

Mixins provide reusable functionality:

#### **IOMixin** - Input/Output Widgets

```python
class MyTool(QWidget, IOMixin):
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setup_io(layout)  # Adds target input + output area
        
        # Access widgets
        targets = self.target_input.get_targets()
        self.output_area.append("Output text")
```

**Provides:**
- `self.target_input` - Target input widget
- `self.output_area` - Output text area
- `self.log_file` - Path to log file

#### **RunMixin** - Execution Controls

```python
class MyTool(QWidget, RunMixin):
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setup_run_controls(layout)  # Adds RUN/STOP/CLEAR buttons
    
    def run_scan(self):
        self.start_worker(["mytool", "arg"], tool_name="mytool")
```

**Provides:**
- `self.run_button` - RUN button
- `self.stop_button` - STOP button
- `self.clear_button` - CLEAR button
- `self.start_worker(command, tool_name)` - Worker management
- `self.stop_scan()` - Stop running worker

---

### Advanced: Custom Command Building

For complex tools with many options:

```python
def build_command(self):
    cmd = ["nmap"]
    
    # Add scan type
    if self.syn_scan.isChecked():
        cmd.append("-sS")
    elif self.tcp_scan.isChecked():
        cmd.append("-sT")
    
    # Add timing
    timing = self.timing_combo.currentText()
    cmd.extend(["-T", timing])
    
    # Add target
    targets = self.target_input.get_targets()
    cmd.extend(targets)
    
    return cmd
```

---

## Code Style

### Python Style Guide

Follow **PEP 8** with these conventions:

```python
# Classes: PascalCase
class MyTool(ToolBase):
    pass

# Functions/Methods: snake_case
def build_command():
    pass

# Constants: UPPER_SNAKE_CASE
DEFAULT_TIMEOUT = 30

# Private methods: _leading_underscore
def _internal_helper():
    pass
```

### Documentation

Use docstrings:

```python
def parse_targets(input_text: str) -> list[str]:
    """
    Parse target input from user.
    
    Args:
        input_text: Raw input (single target or file path)
    
    Returns:
        List of target strings
    
    Example:
        >>> parse_targets("example.com")
        ['example.com']
    """
    pass
```

### Import Organization

```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal, Slot

# Local
from core.config import ConfigManager
from modules.bases import ToolBase
```

---

## Building for Distribution

### Using Nuitka

Compile VAJRA to a standalone executable:

```bash
# Ensure you're in the VAJRA-OSP directory
cd /path/to/VAJRA-OSP

# Run build script
chmod +x builder/compile.sh
./builder/compile.sh
```

### Build Script (`builder/compile.sh`)

```bash
#!/bin/bash
python -m nuitka \
    --standalone \
    --onefile \
    --enable-plugin=pyside6 \
    --include-data-dir=db=db \
    --linux-icon=icon.png \
    --output-filename=VAJRA \
    main.py
```

### Build Output

```
VAJRA-OSP/
└── VAJRA  (standalone executable)
```

### Build Requirements

```bash
# Install Nuitka
pip install nuitka

# Install compiler (Debian/Ubuntu)
sudo apt install build-essential

# Install compiler (Fedora)
sudo dnf install gcc-c++

# Install compiler (macOS)
xcode-select --install
```

---

## Debugging

### Print Debugging

```python
# Simple output
print(f"Target: {target}")

# Rich debugging
import sys
print(f"[DEBUG] Command: {command}", file=sys.stderr)
```

### Qt Debugging

```python
# Signal connections
@Slot()
def my_slot(self):
    print("Signal received!")

# Widget hierarchy
def print_widget_tree(widget, indent=0):
    print("  " * indent + widget.__class__.__name__)
    for child in widget.children():
        print_widget_tree(child, indent + 1)
```

### Worker Debugging

```python
class MyWorker(QThread):
    def run(self):
        try:
            # Your code
            pass
        except Exception as e:
            print(f"[ERROR] Worker failed: {e}")
            import traceback
            traceback.print_exc()
```

### Log Files

Check output logs:

```bash
# Navigate to scan output
cd /tmp/Vajra-results/

# List scans
ls -lh

# View specific log
cat example.com_*/Logs/nmap.log
```

---

## Common Tasks

### Task 1: Add a New Option to Existing Tool

```python
# modules/nmap.py

def setup_ui(self):
    # ... existing code ...
    
    # Add new checkbox
    self.aggressive_scan = QCheckBox("Aggressive Scan (-A)")
    layout.addWidget(self.aggressive_scan)

def build_command(self):
    cmd = ["nmap"]
    
    # Add new option
    if self.aggressive_scan.isChecked():
        cmd.append("-A")
    
    # ... rest of command building ...
    return cmd
```

### Task 2: Add Color-Coding to Output

```python
from ui.styles import SUCCESS, ERROR, WARNING

def colorize_output(self, line):
    if "VULNERABLE" in line:
        return f'<span style="color: {ERROR};">{line}</span>'
    elif "open" in line.lower():
        return f'<span style="color: {SUCCESS};">{line}</span>'
    elif "filtered" in line.lower():
        return f'<span style="color: {WARNING};">{line}</span>'
    return line

def handle_output(self, line):
    colored_line = self.colorize_output(line)
    self.output_area.append(colored_line)
```

### Task 3: Add Notifications

```python
def run_scan(self):
    # Start scan
    self.start_worker(command, tool_name="mytool")
    
    # Show notification
    self.main_window.notification_manager.show_toast(
        "Scan started",
        "info"
    )

@Slot(int)
def handle_scan_finished(self, exit_code):
    if exit_code == 0:
        self.main_window.notification_manager.show_toast(
            "Scan completed successfully",
            "success"
        )
    else:
        self.main_window.notification_manager.show_toast(
            "Scan failed",
            "error"
        )
```

### Task 4: Parse Tool Output

```python
# core/jsonparser.py

def parse_mytool_output(self, log_file):
    """Parse MyTool output from log file"""
    if not os.path.exists(log_file):
        return {}
    
    findings = []
    with open(log_file, 'r') as f:
        for line in f:
            if "FINDING:" in line:
                findings.append(line.strip())
    
    return {
        "tool": "mytool",
        "findings": findings,
        "count": len(findings)
    }

# In generate_final_json()
mytool_data = self.parse_mytool_output(
    os.path.join(log_dir, "mytool.log")
)
data["tools"]["mytool"] = mytool_data
```

---

## Troubleshooting

### Issue: PySide6 Import Error

```bash
# Symptom
ModuleNotFoundError: No module named 'PySide6'

# Solution
pip install PySide6
# or
pip install -r requirements.txt
```

### Issue: Tool Not Appearing in Sidebar

**Checklist:**
1. ✅ Class inherits from `ToolBase`
2. ✅ `name` and `category` are set
3. ✅ `get_widget()` is implemented
4. ✅ File is in `modules/` directory
5. ✅ No syntax errors (check console)

```python
# Verify your class looks like:
class MyTool(ToolBase):
    name = "My Tool"  # Required!
    category = ToolCategory.INFO_GATHERING  # Required!
    
    def get_widget(self, main_window):  # Required!
        return MyToolWidget(main_window)
```

### Issue: Worker Not Starting

```python
# Check command validity
def run_scan(self):
    command = self.build_command()
    
    # Debug: Print command
    print(f"Command: {command}")
    
    # Check if command is valid
    if not command:
        print("ERROR: Command is None")
        return
    
    if not isinstance(command, list):
        print("ERROR: Command must be a list")
        return
    
    self.start_worker(command, tool_name="mytool")
```

### Issue: Output Not Displaying

```python
# Ensure signal is connected
@Slot(str)
def handle_output(self, line):
    print(f"Received: {line}")  # Debug
    self.output_area.append(line)

# In start_worker()
self.worker.output_ready.connect(self.handle_output)  # Required!
```

### Issue: Build Fails

```bash
# Check Nuitka installation
python -m nuitka --version

# Check compiler
gcc --version  # Linux
clang --version  # macOS

# Try building with verbose output
python -m nuitka --show-progress --standalone main.py
```

---

## Best Practices

### 1. **Always Use List-Based Commands**

```python
# ✅ GOOD (prevents injection)
command = ["nmap", "-p", ports, target]

# ❌ BAD (vulnerable to injection)
command = f"nmap -p {ports} {target}"
```

### 2. **Handle Empty Input**

```python
def run_scan(self):
    targets = self.target_input.get_targets()
    if not targets:
        self.main_window.notification_manager.show_toast(
            "Please enter a target", "warning"
        )
        return
```

### 3. **Provide User Feedback**

```python
# Show progress
self.main_window.notification_manager.show_toast(
    "Scan starting...", "info"
)

# Show completion
@Slot(int)
def handle_scan_finished(self, exit_code):
    if exit_code == 0:
        self.main_window.notification_manager.show_toast(
            "Scan completed successfully", "success"
        )
```

### 4. **Clean Up Resources**

```python
def closeEvent(self, event):
    """Clean up when widget is closed"""
    if hasattr(self, 'worker') and self.worker:
        self.worker.terminate()
        self.worker.wait()
    event.accept()
```

### 5. **Use Existing Utilities**

```python
# Use target parsing
from core.tgtinput import parse_targets, normalize_target

# Use file operations
from core.fileops import create_target_directory, get_timestamp

# Use styling
from ui.styles import get_button_style, ACCENT, SUCCESS
```

---

## Getting Help

### Resources

- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)
- **Code Examples**: Check existing tools in `modules/`

### Common Questions

**Q: How do I add a new tool category?**
A: Edit `modules/bases.py` and add to `ToolCategory` class.

**Q: Can I make tools depend on each other?**
A: Avoid dependencies. Tools should be independent for modularity.

**Q: How do I test without running the full GUI?**
A: Core utilities in `core/` can be tested independently:
```bash
python -c "from core.tgtinput import parse_targets; print(parse_targets('example.com'))"
```

**Q: Where are settings stored?**
A: `~/.config/VAJRA/` (managed by Qt's QSettings)

---

## Next Steps

1. **Explore codebase**: Browse `modules/` for examples
2. **Read architecture**: Understand patterns in [ARCHITECTURE.md](ARCHITECTURE.md)
3. **Build a tool**: Follow [Adding New Tools](#adding-new-tools)
4. **Submit PR**: See [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Happy coding! 🚀**

**Last Updated:** 2026-01-22
