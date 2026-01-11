# VAJRA-OSP Development Guide

This guide covers setting up a development environment, running tests, and debugging VAJRA.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Running the Application](#running-the-application)
4. [Project Structure](#project-structure)
5. [Development Workflow](#development-workflow)
6. [Testing](#testing)
7. [Debugging](#debugging)
8. [Code Quality](#code-quality)
9. [Building for Distribution](#building-for-distribution)
10. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### System Requirements

- **Python**: 3.10+ (3.11+ recommended)
- **OS**: Linux (primary), macOS, Windows (limited testing)
- **RAM**: 4GB minimum, 8GB recommended
- **Display**: 1280x720 minimum resolution

### Required Python Packages

```bash
# Core dependencies (in requirements.txt)
PySide6>=6.5.0      # Qt for Python
```

### External Security Tools

VAJRA wraps external tools. Install the ones you need:

```bash
# Debian/Ubuntu/Kali Linux
sudo apt update
sudo apt install -y \
    nmap \
    gobuster \
    subfinder \
    amass \
    httpx-toolkit \
    dnsutils \
    dnsrecon \
    hashcat \
    john \
    hydra \
    eyewitness \
    whois \
    nikto \
    ffuf \
    nuclei \
    wafw00f \
    exploitdb

# Verify installations
nmap --version
gobuster version
subfinder -version
```

---

## 🚀 Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/VAJRA-OSP.git
cd VAJRA-OSP
```

### 2. Create Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
.\venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# For development (optional)
pip install black flake8 pytest pytest-qt mypy
```

### 4. Verify Setup

```bash
# Run the application
python main.py

# You should see:
# [Discovery] Running in dev mode - auto-discovering modules
# [Discovery] Found modules: ['amass', 'automation', ...]
# [Discovery] Loaded 24 tools: [...]
```

---

## ▶️ Running the Application

### Development Mode

```bash
# Standard launch
python main.py

# With verbose Qt output
QT_DEBUG_PLUGINS=1 python main.py

# With Python warnings
python -W all main.py
```

### Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `QT_DEBUG_PLUGINS` | Debug Qt plugin loading | `1` |
| `QT_LOGGING_RULES` | Control Qt log verbosity | `qt.*=false` |
| `VAJRA_OUTPUT_DIR` | Custom output directory | `/home/user/scans` |

---

## 📁 Project Structure

```
VAJRA-OSP/
├── main.py                 # Entry point - start here
│
├── core/                   # Core utilities (NO Qt imports)
│   ├── config.py           # Settings management
│   ├── fileops.py          # Directory/file operations
│   ├── jsonparser.py       # Scan result aggregation
│   ├── privileges.py       # Root privilege checking
│   ├── reportgen.py        # HTML/PDF report generation
│   └── tgtinput.py         # Target input parsing
│
├── ui/                     # Qt UI components
│   ├── main_window.py      # Main window + plugin discovery
│   ├── sidepanel.py        # Navigation sidebar
│   ├── styles.py           # ALL styling + reusable widgets
│   ├── worker.py           # ProcessWorker + execution mixins
│   ├── notification.py     # Toast notifications
│   └── settingpanel.py     # Settings UI
│
├── modules/                # Tool plugins
│   ├── bases.py            # ToolBase, ToolCategory
│   ├── automation.py       # 8-step pipeline
│   ├── nmap.py             # Nmap integration
│   └── ...                 # 24 tools total
│
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md
│   ├── CONTRIBUTING.md
│   ├── DEVELOPMENT.md      # This file
│   └── SECURITY.md
│
└── tests/                  # Test suite (if present)
    ├── test_core/
    ├── test_modules/
    └── test_ui/
```

---

## 🔄 Development Workflow

### Adding a New Tool

1. **Create the file**:
   ```bash
   touch modules/mytool.py
   ```

2. **Use the template** from `CONTRIBUTING.md`

3. **Test discovery**:
   ```bash
   python main.py
   # Check console for: [Discovery] Loaded X tools: [..., 'My Tool', ...]
   ```

4. **Test execution**:
   - Open the tool from sidebar
   - Enter a target
   - Click Run
   - Verify output displays correctly
   - Test Stop button

### Modifying Styles

All styling is in `ui/styles.py`. To modify:

1. **Find the component** (e.g., `RunButton`)
2. **Modify the style string** (e.g., `RUN_BUTTON_STYLE`)
3. **Test visually** - restart app to see changes

**Never add inline styles in tool files!**

### Modifying Core Utilities

Files in `core/` should:
- Not import PySide6
- Be testable without Qt event loop
- Have docstrings on all public functions

---

## 🧪 Testing

### Manual Testing Checklist

Before committing, verify:

- [ ] Application launches without errors
- [ ] All 24 tools appear in sidebar
- [ ] Tool tabs open and close correctly
- [ ] Run/Stop buttons work
- [ ] Output displays in real-time
- [ ] No Qt warnings in console

### Running Unit Tests (if available)

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=. tests/

# Run specific test file
pytest tests/test_core/test_fileops.py

# Run with verbose output
pytest -v tests/
```

### Testing Tool Execution

```bash
# Test a specific tool (example: nmap)
python -c "
from modules.nmap import NmapTool
tool = NmapTool()
print(f'Name: {tool.name}')
print(f'Category: {tool.category}')
"
```

### Testing Core Modules

```bash
# Test fileops
python -c "
from core.fileops import create_target_dirs, get_timestamp
print(f'Timestamp: {get_timestamp()}')
dir_path = create_target_dirs('example.com')
print(f'Created: {dir_path}')
"
```

### Qt Testing with pytest-qt

```python
# tests/test_ui/test_main_window.py
import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

@pytest.fixture
def app(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    return window

def test_window_title(app):
    assert "VAJRA" in app.windowTitle()

def test_tool_discovery(app):
    assert len(app.tools) >= 20  # At least 20 tools
```

---

## 🐛 Debugging

### Enable Verbose Logging

Add to `main.py` temporarily:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Debug Qt Issues

```bash
# Enable Qt plugin debugging
export QT_DEBUG_PLUGINS=1
python main.py

# Check for missing libraries
ldd $(python -c "from PySide6 import QtWidgets; print(QtWidgets.__file__)")
```

### Debug Process Execution

In `ui/worker.py`, add prints:

```python
def run(self):
    print(f"[Worker] Starting: {self.command}")
    # ... existing code ...
    print(f"[Worker] Process exited with: {process.returncode}")
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Tool not appearing | Missing `name` attribute | Add `name = "Tool Name"` |
| Import error on start | Syntax error in tool | Check console, fix syntax |
| UI freeze | Long operation on main thread | Use ProcessWorker |
| Style not applied | Inline style overriding | Remove inline style |

### Using PDB

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint()
breakpoint()
```

---

## 📏 Code Quality

### Formatting with Black

```bash
# Install
pip install black

# Format single file
black modules/mytool.py

# Format entire project
black .

# Check without modifying
black --check .
```

### Linting with Flake8

```bash
# Install
pip install flake8

# Lint project
flake8 . --max-line-length=100 --exclude=venv

# Common ignores
flake8 . --ignore=E501,W503
```

### Type Checking with MyPy

```bash
# Install
pip install mypy

# Check types
mypy core/ --ignore-missing-imports
mypy modules/bases.py
```

### Pre-commit Hook (Optional)

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100]
EOF

# Install hooks
pre-commit install
```

---

## 📦 Building for Distribution

### PyInstaller (Recommended)

```bash
# Install
pip install pyinstaller

# Build single executable
pyinstaller --onefile --windowed \
    --name VAJRA \
    --add-data "modules:modules" \
    main.py

# Output in dist/VAJRA
```

### PyInstaller Spec File

Create `vajra.spec`:

```python
# vajra.spec
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('modules', 'modules')],
    hiddenimports=[
        'modules.amass', 'modules.automation', 'modules.nmap',
        # ... list all modules
    ],
    hookspath=['linux_setup'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VAJRA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
```

```bash
# Build with spec
pyinstaller vajra.spec
```

### Nuitka (Alternative)

```bash
# Install
pip install nuitka

# Build
python -m nuitka \
    --standalone \
    --include-package=modules \
    --include-package=ui \
    --include-package=core \
    --enable-plugin=pyside6 \
    main.py
```

---

## 🔧 Troubleshooting

### "No module named 'modules.xxx'"

```bash
# Ensure __init__.py exists
ls modules/__init__.py

# Check if module has syntax errors
python -c "import modules.xxx"
```

### "Qt platform plugin could not be initialized"

```bash
# Install Qt dependencies
sudo apt install -y libxcb-xinerama0 libxkbcommon-x11-0

# Set platform
export QT_QPA_PLATFORM=xcb
python main.py
```

### "Permission denied" for scans

Some tools (nmap SYN scan, etc.) require root:

```bash
# Run with sudo
sudo python main.py

# Or use polkit for specific tools
```

### Tool output not showing

1. Check if `output_ready` signal is connected
2. Verify `on_new_output()` is implemented
3. Add debug print in `ProcessWorker.run()`

### Slow startup

```bash
# Profile startup
python -m cProfile -s cumtime main.py 2>&1 | head -50

# Common causes:
# - Heavy imports in tools (lazy load instead)
# - Network calls during import
# - Large data structures in module scope
```

---

## 📚 Additional Resources

- **PySide6 Documentation**: https://doc.qt.io/qtforpython-6/
- **Qt Stylesheets Reference**: https://doc.qt.io/qt-6/stylesheet-reference.html
- **Python Packaging**: https://packaging.python.org/
- **PyInstaller Manual**: https://pyinstaller.org/en/stable/

---

## 🆘 Getting Help

1. **Check existing issues** on GitHub
2. **Search documentation** (this file + others in `docs/`)
3. **Open an issue** with:
   - Python version (`python --version`)
   - OS and version
   - Complete error traceback
   - Steps to reproduce
