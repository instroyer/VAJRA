# Contributing to VAJRA-OSP

Thank you for your interest in contributing to VAJRA! This guide will help you understand how to add new tools and contribute effectively to the project.

---

## 📋 Table of Contents

1. [Who This Is For](#who-this-is-for)
2. [Core Principles](#core-principles)
3. [Project Structure](#project-structure)
4. [Adding a New Tool](#adding-a-new-tool)
5. [Golden Tool Template](#golden-tool-template)
6. [Contribution Workflow](#contribution-workflow)
7. [Code Style Guidelines](#code-style-guidelines)
8. [Pull Request Process](#pull-request-process)

---

## 👥 Who This Is For

- **Core developers** maintaining the platform
- **Contributors** adding new tools or features
- **Reviewers** evaluating pull requests
- **Automated agents** (LLMs) generating code

---

## 🎯 Core Principles

VAJRA is a **platform**, not a collection of scripts. All contributions must preserve:

### ✅ You MUST

- Follow the plugin architecture (`ToolBase` inheritance)
- Use centralized styles from `ui/styles.py`
- Use `OutputHelper` for all output formatting
- Use `SafeStop` mixin for process management
- Use `build_command()` pattern for command generation
- Keep UI, output, and logic centralized
- Add Google-style docstrings to public methods

### ❌ You MUST NOT

- Add inline styles inside tools (use `ui/styles.py`)
- Use raw shell command strings without `shlex.quote()`
- Add duplicate output formatting
- Add new colors outside the theme palette
- Touch core architecture without discussion
- Embed `sudo` directly in commands
- Manage notifications directly in tools
- Manage output paths manually (use `core/fileops.py`)
- Implement custom execution lifecycles (use `ToolExecutionMixin`)

---

## 📁 Project Structure

```
VAJRA-OSP/
├── core/              # Core utilities (NO Qt imports allowed)
│   ├── config.py      # Configuration management
│   ├── fileops.py     # File operations, directory creation
│   ├── jsonparser.py  # JSON parsing and aggregation
│   ├── reportgen.py   # HTML/PDF report generation
│   └── tgtinput.py    # Target input parsing
│
├── ui/                # User interface (Qt widgets, styles)
│   ├── styles.py      # ALL styles and reusable widgets
│   ├── worker.py      # ProcessWorker, ToolExecutionMixin
│   ├── main_window.py # Main window with plugin discovery
│   └── sidepanel.py   # Navigation sidebar
│
├── modules/           # Tool plugins (one file per tool)
│   ├── bases.py       # ToolBase, ToolCategory (DO NOT MODIFY)
│   └── <tool>.py      # Individual tool implementations
│
└── main.py            # Application entry point
```

---

## 🔧 Adding a New Tool

### Step 1: Choose a Category

Select the appropriate `ToolCategory` from `modules/bases.py`:

| Category | Use Case |
|----------|----------|
| `AUTOMATION` | Multi-step pipelines |
| `INFO_GATHERING` | WHOIS, DNS, OSINT |
| `SUBDOMAIN_ENUMERATION` | Subdomain discovery |
| `LIVE_SUBDOMAINS` | Live host detection |
| `PORT_SCANNING` | Port/service scanning |
| `WEB_SCANNING` | Directory brute-forcing, fuzzing |
| `WEB_SCREENSHOTS` | Screenshot capture |
| `VULNERABILITY_SCANNER` | Vuln scanning |
| `CRACKER` | Password cracking, hashing |
| `PAYLOAD_GENERATOR` | Payload/shell generation |
| `FILE_ANALYSIS` | Binary/file analysis |

### Step 2: Create the Tool File

Create `modules/<tool_name>.py` using the template below.

### Step 3: Test Locally

```bash
python main.py
```

Your tool should automatically appear in the sidebar under its category.

---

## 📝 Golden Tool Template

Copy this template for new tools:

```python
# =============================================================================
# modules/<tool_name>.py
#
# <Tool Name> - <Brief Description>
# =============================================================================

import os
import shlex

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from ui.styles import (
    # Widgets - import only what you need
    RunButton, StopButton, BrowseButton, CopyButton,
    StyledLineEdit, StyledSpinBox, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView, CommandDisplay,
    ToolSplitter, ConfigTabs, StyledToolView,
    # Mixins
    SafeStop, OutputHelper,
    # Constants (if needed)
    COLOR_INFO, COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR
)


class MyTool(ToolBase):
    """
    <Tool Name> tool plugin for VAJRA.
    
    This tool provides <brief description of what the tool does>.
    
    Attributes:
        name: Display name shown in sidebar.
        category: ToolCategory enum for sidebar grouping.
    """
    
    name = "My Tool"
    category = ToolCategory.INFO_GATHERING  # Change as appropriate
    
    @property
    def description(self) -> str:
        """Return a brief description of the tool."""
        return "Brief description for tooltips"
    
    @property
    def icon(self) -> str:
        """Return an emoji icon for the tool."""
        return "🔧"
    
    def get_widget(self, main_window: QWidget) -> QWidget:
        """
        Create and return the tool's UI widget.
        
        Args:
            main_window: Reference to the MainWindow instance.
            
        Returns:
            The tool's view widget instance.
        """
        return MyToolView(main_window)


class MyToolView(StyledToolView, SafeStop, OutputHelper):
    """
    UI view for <Tool Name>.
    
    This class implements the complete user interface for the tool,
    including configuration options, command building, and execution.
    
    Attributes:
        tool_name: Name used for logging and display.
        tool_category: Category string for header breadcrumb.
    """
    
    tool_name = "My Tool"
    tool_category = "INFO_GATHERING"
    
    def __init__(self, main_window: QWidget = None):
        """
        Initialize the tool view.
        
        Args:
            main_window: Reference to the MainWindow for notifications.
        """
        super().__init__()
        self.main_window = main_window
        self.init_safe_stop()  # Initialize stop functionality
        self._build_ui()
        self.update_command()
    
    def _build_ui(self) -> None:
        """Build the complete tool UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # === Header ===
        header = HeaderLabel(f"{self.tool_category} › {self.tool_name}")
        layout.addWidget(header)
        
        # === Configuration Section ===
        config_group = StyledGroupBox("Configuration")
        config_layout = QGridLayout(config_group)
        config_layout.setSpacing(10)
        
        # Target input
        config_layout.addWidget(StyledLabel("Target:"), 0, 0)
        self.target_input = StyledLineEdit()
        self.target_input.setPlaceholderText("Enter target (domain / IP / CIDR)")
        self.target_input.textChanged.connect(self.update_command)
        config_layout.addWidget(self.target_input, 0, 1)
        
        # Add more configuration options here...
        # Example: checkbox option
        self.verbose_check = StyledCheckBox("Verbose output")
        self.verbose_check.stateChanged.connect(self.update_command)
        config_layout.addWidget(self.verbose_check, 1, 0, 1, 2)
        
        layout.addWidget(config_group)
        
        # === Command Preview ===
        cmd_group = StyledGroupBox("Command")
        cmd_layout = QHBoxLayout(cmd_group)
        self.command_display = CommandDisplay()
        cmd_layout.addWidget(self.command_display)
        layout.addWidget(cmd_group)
        
        # === Action Buttons ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.run_button = RunButton("Run")
        self.run_button.clicked.connect(self.run_scan)
        btn_layout.addWidget(self.run_button)
        
        self.stop_button = StopButton("Stop")
        self.stop_button.clicked.connect(self.stop_scan)
        self.stop_button.setEnabled(False)
        btn_layout.addWidget(self.stop_button)
        
        layout.addLayout(btn_layout)
        
        # === Output Section ===
        self.output = OutputView()
        layout.addWidget(self.output, 1)  # Stretch factor 1
    
    def build_command(self, preview: bool = False) -> str:
        """
        Build the command string from current UI state.
        
        Args:
            preview: If True, format for display only (no file paths).
            
        Returns:
            The complete command string ready for execution.
        """
        target = self.target_input.text().strip()
        if not target:
            return "mytool --help"
        
        cmd_parts = ["mytool"]
        
        # Add target
        cmd_parts.append(shlex.quote(target))
        
        # Add options based on UI state
        if self.verbose_check.isChecked():
            cmd_parts.append("-v")
        
        return " ".join(cmd_parts)
    
    def update_command(self) -> None:
        """Update the command preview display."""
        cmd = self.build_command(preview=True)
        self.command_display.setText(cmd)
    
    def run_scan(self) -> None:
        """Execute the tool with current configuration."""
        target = self.target_input.text().strip()
        if not target:
            self._error("Please enter a target")
            return
        
        # Build command
        command = self.build_command()
        
        # Clear output and show info
        self.output.clear()
        self._info(f"Starting scan on {target}")
        self._section("COMMAND")
        self.output.appendPlainText(command)
        self._section("OUTPUT")
        
        # Execute using mixin (handles button states, worker lifecycle)
        self.start_execution(command, shell=True)
    
    def on_execution_finished(self) -> None:
        """Handle scan completion."""
        self._success("Scan completed")
    
    def on_new_output(self, line: str) -> None:
        """
        Process each line of output from the tool.
        
        Override this to add custom output formatting/parsing.
        
        Args:
            line: A single line of output from the subprocess.
        """
        self.output.appendPlainText(line)
```

---

## 🔄 Contribution Workflow

1. **Fork** the repository
2. **Create a feature branch**: `git checkout -b feature/my-new-tool`
3. **Read** this guide and `ARCHITECTURE.md`
4. **Implement** using the Golden Tool Template
5. **Test locally**: `python main.py`
6. **Commit**: `git commit -m "Add MyTool for X functionality"`
7. **Push**: `git push origin feature/my-new-tool`
8. **Open Pull Request** using the template below

---

## 📏 Code Style Guidelines

### Python Style

- **PEP 8** compliance (use `black` formatter recommended)
- **Google-style docstrings** for all public methods
- **Type hints** for function parameters and returns
- **Max line length**: 100 characters (soft limit)

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Tool class | `PascalCase` + `Tool` suffix | `NmapTool` |
| View class | `PascalCase` + `View` suffix | `NmapView` |
| Methods | `snake_case` | `build_command()` |
| Constants | `UPPER_SNAKE` | `COLOR_SUCCESS` |
| Private methods | `_snake_case` | `_build_ui()` |

### Import Order

```python
# 1. Standard library
import os
import shlex

# 2. Third-party (PySide6)
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt

# 3. Local modules
from modules.bases import ToolBase, ToolCategory
from ui.styles import RunButton, StopButton
```

---

## 📬 Pull Request Template

When opening a PR, include:

```markdown
## Summary
Brief description of what this PR does.

## Type
- [ ] New Tool
- [ ] Bug Fix
- [ ] Refactor
- [ ] Documentation

## Checklist

### Architecture Compliance
- [ ] Inherits from `ToolBase`
- [ ] Uses `StyledToolView`, `SafeStop`, `OutputHelper`
- [ ] No Qt imports in `core/`
- [ ] No inline styles (all from `ui/styles.py`)

### Code Quality
- [ ] Google-style docstrings on public methods
- [ ] Type hints on function signatures
- [ ] `shlex.quote()` used for shell arguments
- [ ] `build_command()` pattern implemented

### Testing
- [ ] Application launches without errors
- [ ] Tool appears in correct sidebar category
- [ ] Tool executes correctly
- [ ] Output displays properly
- [ ] Stop button terminates process

## Screenshots (if applicable)
```

---

## 🆘 Getting Help

- **Issues**: Open a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Code Review**: Tag maintainers for architecture questions

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.
