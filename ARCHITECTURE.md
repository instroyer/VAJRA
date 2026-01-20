# VAJRA-OSP Architecture

This document describes the architectural design decisions, module relationships, and patterns used in VAJRA.

---

## 📋 Table of Contents

1. [High-Level Architecture](#-high-level-architecture)
2. [Directory Structure](#-directory-structure)
3. [Plugin Discovery System](#-plugin-discovery-system)
4. [Module Relationships](#-module-relationships)
5. [Design Patterns](#-design-patterns)
6. [Data Flow](#-data-flow)
7. [Styling Architecture](#-styling-architecture)
8. [Process Management](#-process-management)
9. [Report Generation Pipeline](#-report-generation-pipeline)
10. [Design Decisions](#-design-decisions)

---

## 🏗️ High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                              VAJRA-OSP                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────────────────────────────────────────┐  │
│  │   main.py    │───▶│               MainWindow                          │  │
│  │  (Entry)     │    │  ┌──────────┐  ┌───────────────┐  ┌───────────┐  │  │
│  └──────────────┘    │  │Sidepanel │  │  QTabWidget   │  │Notification│  │  │
│                      │  │(Nav)     │  │  (Tool Tabs)  │  │  Manager   │  │  │
│                      │  └────┬─────┘  └───────┬───────┘  └───────────┘  │  │
│                      └───────┼────────────────┼─────────────────────────┘  │
│                              │                │                             │
│                              ▼                ▼                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                         modules/                                       │ │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │ │
│  │  │ToolBase │◀─│NmapTool │  │HashcatT.│  │NucleiT. │  │  ...    │    │ │
│  │  │(bases.py│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘    │ │
│  │  └─────────┘       │            │            │            │          │ │
│  │                    ▼            ▼            ▼            ▼          │ │
│  │              ┌──────────────────────────────────────────────────┐    │ │
│  │              │              Tool Views (UI Widgets)              │    │ │
│  │              │  Inherits: StyledToolView + SafeStop + OutputHelper│   │ │
│  │              └──────────────────────────────────────────────────┘    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                              │                                              │
│                              ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                           ui/                                          │ │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────┐  │ │
│  │  │ styles.py │  │ worker.py │  │sidepanel. │  │  notification.py  │  │ │
│  │  │(Widgets,  │  │(Process   │  │   py      │  │  (Toast system)   │  │ │
│  │  │ Themes)   │  │ Execution)│  │           │  │                   │  │ │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                              │                                              │
│                              ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                          core/                                         │ │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────┐  │ │
│  │  │ fileops.py│  │jsonparser.│  │reportgen. │  │    config.py      │  │ │
│  │  │(Dirs,     │  │   py      │  │   py      │  │  (Settings)       │  │ │
│  │  │ Caching)  │  │(JSON agg) │  │(HTML/PDF) │  │                   │  │ │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────────────┘  │ │
│  │                                                                        │ │
│  │  ⚠️ NO Qt IMPORTS ALLOWED IN core/                                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Directory Structure

```text
VAJRA-OSP/
│
├── main.py                 # Application entry point
│                           # - Initializes QApplication
│                           # - Sets global font styling
│                           # - Creates MainWindow
│
├── core/                   # Core utilities (Qt-free zone)
│   ├── __init__.py
│   ├── config.py           # ConfigManager - output paths, settings
│   ├── fileops.py          # create_target_dirs(), caching system
│   ├── jsonparser.py       # FinalJsonGenerator - aggregates scan data
│   ├── privileges.py       # Privilege checking for root operations
│   ├── reportgen.py        # ReportGenerator - HTML/PDF reports
│   ├── tgtinput.py         # Target parsing and normalization
│   └── tool_installer.py   # Dynamic tool installer
│
├── ui/                     # User interface layer
│   ├── __init__.py
│   ├── main_window.py      # MainWindow - plugin discovery, tab management
│   ├── sidepanel.py        # Sidepanel - category navigation
│   ├── styles.py           # SINGLE SOURCE OF TRUTH for all styling
│   ├── worker.py           # ProcessWorker, ToolExecutionMixin, SafeStop
│   ├── notification.py     # NotificationManager - toast system
│   └── settingpanel.py     # Settings UI panel
│
├── modules/                # Tool plugins (auto-discovered)
│   ├── __init__.py
│   ├── bases.py            # ToolBase, ToolCategory (contracts)
│   └── <tool>.py           # Individual tool implementations
│
├── builder/                # Build system
│   └── build_nuitka.sh     # Nuitka compilation script
│
└── docs/                   # Documentation
    ├── ARCHITECTURE.md     # This file
    ├── CONTRIBUTING.md     # Contributor guide
    ├── DEVELOPMENT.md      # Developer setup
    └── SECURITY.md         # Security policy
```

---

## 🔌 Plugin Discovery System

VAJRA uses dynamic plugin discovery to automatically find and load tools at runtime.

### How It Works

```python
# ui/main_window.py - MainWindow._discover_tools()

def _discover_tools(self):
    """
    Hybrid tool discovery mechanism.
    
    The discovery process:
    1. Check if running as frozen executable (PyInstaller)
    2. If frozen: Use hardcoded fallback list (pkgutil doesn't work)
    3. If development: Auto-discover using pkgutil.iter_modules()
    4. Import each module and find ToolBase subclasses
    5. Store class references (not instances) for lazy loading
    
    Returns:
        Dict[str, Type[ToolBase]]: Mapping of tool names to classes.
    """
    tools = {}
    
    # Development mode: auto-discover
    import modules
    known_modules = [
        name for _, name, _ in pkgutil.iter_modules(modules.__path__)
        if name != "bases"
    ]
    
    # Load each module
    for name in known_modules:
        module = importlib.import_module(f'modules.{name}')
        
        # Find all ToolBase subclasses
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, ToolBase) and obj is not ToolBase:
                tool_name = getattr(obj, 'name', None)
                if tool_name:
                    tools[tool_name] = obj  # Store CLASS, not instance
    
    return tools
```

### Discovery Flow

```
Application Start
       │
       ▼
MainWindow.__init__()
       │
       ▼
_discover_tools()
       │
       ├─── Is Frozen (PyInstaller)? ───▶ Use fallback module list
       │              │
       │              ▼
       │         importlib.import_module()
       │              │
       ▼              ▼
pkgutil.iter_modules() ──▶ Get module names
       │
       ▼
For each module:
  ├── Import module
  ├── inspect.getmembers(isclass)
  ├── Filter: issubclass(obj, ToolBase)
  └── Store: tools[name] = class_reference
       │
       ▼
Return tools dict to Sidepanel
       │
       ▼
Sidepanel groups by ToolCategory
       │
       ▼
User clicks tool → MainWindow.open_tool_tab()
       │
       ▼
Instantiate tool class → tool.get_widget()
```

### Adding a New Tool

Simply create a file in `modules/` with a class that:
1. Inherits from `ToolBase`
2. Has a `name` class attribute
3. Has a `category` class attribute
4. Implements `get_widget(main_window)`

The tool will be automatically discovered on the next application launch.

---

## 🔗 Module Relationships

### Dependency Graph

```text
                    ┌─────────────┐
                    │   main.py   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
              ┌─────│ MainWindow  │─────┐
              │     └──────┬──────┘     │
              │            │            │
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────────┐
        │Sidepanel │ │QTabWidget│ │Notification  │
        └────┬─────┘ └────┬─────┘ │   Manager    │
             │            │       └──────────────┘
             │            │
             ▼            ▼
        ┌──────────────────────┐
        │   modules/bases.py   │
        │  ┌────────────────┐  │
        │  │   ToolBase     │  │◀─── All tools inherit
        │  │   ToolCategory │  │
        │  └────────────────┘  │
        └──────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │   modules/<tool>.py  │
        │  ┌────────────────┐  │
        │  │   *Tool class  │  │─── Implements ToolBase
        │  │   *View class  │──┼───▶ Uses ui/styles.py components
        │  └────────────────┘  │
        └──────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │    ui/styles.py      │
        │  ┌────────────────┐  │
        │  │ StyledToolView │  │
        │  │ SafeStop       │  │◀─── Mixins for tools
        │  │ OutputHelper   │  │
        │  │ RunButton, etc │  │◀─── Reusable widgets
        │  └────────────────┘  │
        └──────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │    ui/worker.py      │
        │  ┌────────────────┐  │
        │  │ ProcessWorker  │  │◀─── QThread subprocess
        │  │ToolExecMixin   │  │◀─── Execution lifecycle
        │  └────────────────┘  │
        └──────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │      core/*          │
        │  (Qt-free utilities) │
        │  fileops, jsonparser │
        │  reportgen, config   │
        └──────────────────────┘
```

### Import Rules

| From | Can Import | Cannot Import |
| :--- | :--- | :--- |
| `main.py` | `ui/*`, `modules/*` | - |
| `ui/*` | `ui/*`, `modules/bases.py`, `core/*` | - |
| `modules/*` | `ui/styles.py`, `ui/worker.py`, `core/*`, `modules/bases.py` | `ui/main_window.py` |
| `core/*` | `core/*` | **Any Qt (`PySide6`)** |

---

## 🎨 Design Patterns

### 1. Plugin Pattern

Tools are plugins that implement the `ToolBase` contract:

```python
class ToolBase:
    name = None          # Required: Display name
    category = None      # Required: ToolCategory enum
    
    def get_widget(self, main_window) -> QWidget:
        raise NotImplementedError
```

### 2. Mixin Pattern

Tool views combine multiple mixins for functionality:

```python
class MyToolView(StyledToolView, SafeStop, OutputHelper):
    # StyledToolView: Base styling and layout
    # SafeStop: Process termination (stop_scan, worker management)
    # OutputHelper: _info(), _error(), _success(), _section()
```

### 3. Singleton Tab Pattern

Each tool can only have one open tab:

```python
def open_tool_tab(self, tool_class):
    if tool.name in self.open_tool_widgets:
        # Focus existing tab instead of creating new
        self.tab_widget.setCurrentWidget(self.open_tool_widgets[tool.name])
        return
    
    # Create new tab
    tool_widget = tool.get_widget(main_window=self)
    self.open_tool_widgets[tool.name] = tool_widget
```

### 4. Command Builder Pattern

All tools implement `build_command()` for testable command generation:

```python
def build_command(self, preview: bool = False) -> str:
    """Build command from UI state."""
    cmd_parts = ["nmap"]
    cmd_parts.append(f"-p {self.ports_input.text()}")
    cmd_parts.append(shlex.quote(self.target_input.text()))
    return " ".join(cmd_parts)
```

### 5. Worker Thread Pattern

Non-blocking execution using `ProcessWorker`:

```python
# ui/worker.py
class ProcessWorker(QThread):
    output_ready = Signal(str)  # Line-by-line output
    finished = Signal()         # Completion
    error = Signal(str)         # Errors
    
    def run(self):
        process = subprocess.Popen(...)
        for line in process.stdout:
            self.output_ready.emit(line)
```

---

## 📊 Data Flow

### Scan Execution Flow

```text
User Input (UI)
       │
       ▼
build_command() ──────▶ Command String
       │
       ▼
start_execution() ────▶ ProcessWorker (QThread)
       │                      │
       │                      ▼
       │               subprocess.Popen()
       │                      │
       │                      ▼
       │               stdout readline loop
       │                      │
       ▼                      ▼
Button States        output_ready.emit(line)
(disabled)                    │
       │                      ▼
       │               on_new_output(line)
       │                      │
       │                      ▼
       │               OutputView.append()
       │                      │
       ▼                      ▼
Process Ends ◀────────── finished.emit()
       │
       ▼
on_execution_finished()
       │
       ▼
Button States (enabled)
```

### Report Generation Flow

```text
Automation Pipeline Completes
            │
            ▼
    FinalJsonGenerator(target, target_dir)
            │
            ▼
    ┌───────┴───────┐
    │  Parse Files  │
    ├───────────────┤
    │ whois.txt     │
    │ dig.txt       │
    │ alive.txt     │
    │ nmap*.xml     │
    │ nuclei.json   │
    │ nikto*.csv    │
    └───────┬───────┘
            │
            ▼
    Generate final.json
            │
            ▼
    ReportGenerator(target, dir, modules)
            │
            ▼
    ┌───────┴───────┐
    │ Build HTML    │
    ├───────────────┤
    │ Header        │
    │ Exec Summary  │
    │ Whois Section │
    │ DNS Section   │
    │ ... sections  │
    │ Footer        │
    └───────┬───────┘
            │
            ▼
    Save final_report.html
```

---

## 🎨 Styling Architecture

### Single Source of Truth: `ui/styles.py`

```text
ui/styles.py
├── Color Constants
│   ├── COLOR_BG_PRIMARY, COLOR_BG_SECONDARY
│   ├── COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY
│   ├── COLOR_ACCENT_PRIMARY (orange)
│   ├── COLOR_INFO, COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR
│   └── COLOR_BORDER_DEFAULT, COLOR_BORDER_FOCUS
│
├── Font Constants
│   ├── FONT_FAMILY_UI = "Segoe UI"
│   ├── FONT_FAMILY_MONO = "Consolas"
│   └── FONT_SIZE = "14px"
│
├── Style Strings (QSS)
│   ├── RUN_BUTTON_STYLE, STOP_BUTTON_STYLE
│   ├── COMBO_BOX_STYLE, SPINBOX_STYLE
│   ├── OUTPUT_TEXT_EDIT_STYLE
│   └── TAB_WIDGET_STYLE, SIDE_PANEL_STYLE
│
├── Styled Widgets (Classes)
│   ├── RunButton, StopButton, BrowseButton, CopyButton
│   ├── StyledLineEdit, StyledComboBox, StyledSpinBox
│   ├── StyledCheckBox, StyledLabel, HeaderLabel
│   ├── StyledGroupBox, CommandDisplay
│   ├── OutputView, ToolSplitter, ConfigTabs
│   └── StyledToolView (base for all tool views)
│
└── Mixins
    ├── SafeStop - Process termination
    └── OutputHelper - Colored output methods
```

### Why Centralized Styling?

1. **Consistency**: All tools look identical
2. **Maintainability**: Change once, apply everywhere
3. **Theme Support**: Easy to add light mode
4. **Reduced Bugs**: No ad-hoc color values

---

## ⚙️ Process Management

### ProcessWorker Lifecycle

```text
                    ┌─────────────────────┐
                    │   ProcessWorker     │
                    │      created        │
                    └──────────┬──────────┘
                               │
                          start()
                               │
                               ▼
                    ┌─────────────────────┐
                    │     run() begins    │
                    │  subprocess.Popen() │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
        Normal Output    Error Output      stop() called
              │                │                │
              ▼                ▼                ▼
      output_ready.emit() error.emit()   SIGTERM → wait → SIGKILL
              │                │                │
              │                │                ▼
              └────────────────┴────────stopped.emit()
                               │
                               ▼
                        finished.emit()
```

### SafeStop Mixin

```python
class SafeStop:
    """Mixin providing graceful process termination."""
    
    def init_safe_stop(self):
        self.worker = None
        self._stopping = False
    
    def stop_scan(self):
        if self.worker and not self._stopping:
            self._stopping = True
            self.worker.stop()  # SIGTERM then SIGKILL
```

---

## 📈 Design Decisions

### 1. Qt-Free Core

**Decision**: `core/` modules cannot import PySide6.

**Rationale**:

- Enables CLI tools using core functionality
- Easier unit testing without Qt event loop
- Clear separation of concerns
- Potential for headless automation

### 2. Lazy Tool Loading

**Decision**: Store class references, instantiate on tab open.

**Rationale**:

- Faster startup (24 tools × ~50ms = 1.2s saved)
- Lower memory footprint
- Tools only loaded when needed

### 3. Single Styling File

**Decision**: All styles in `ui/styles.py`.

**Rationale**:

- Single source of truth
- Prevents style drift
- Easy theme switching
- Consistent component sizing

### 4. Mixin-Based Tool Views

**Decision**: Use mixins (`SafeStop`, `OutputHelper`) instead of deep inheritance.

**Rationale**:

- Composition over inheritance
- Pick only needed functionality
- Easier testing of individual mixins
- Avoids diamond inheritance issues

### 5. Command Builder Pattern

**Decision**: All tools implement `build_command(preview=False)`.

**Rationale**:

- Testable command generation
- Preview mode for display
- Consistent pattern across tools
- Enables command editing before execution

### 6. Plugin Auto-Discovery

**Decision**: Dynamic discovery via `pkgutil` + `inspect`.

**Rationale**:

- Zero configuration for new tools
- Just create file → tool appears
- No manual registration
- Supports both dev and frozen modes

---

## 🛠️ Build System

VAJRA-OSP uses **Nuitka** to compile the Python application into a standalone native executable.

### Compilation Process (`builder/build_nuitka.sh`)

1. **Environment Setup**: Creates a fresh virtual environment.
2. **Dependency Install**: Installs PySide6 and Nuitka.
3. **Compilation**:
    - `--standalone`: Bundles Python and dependencies.
    - `--onefile`: Creates a single binary.
    - `--enable-plugin=pyside6`: Handles Qt plugins.
    - Includes `modules`, `core`, `ui` packages.
    - Embeds `db` directory.
4. **Security**: The resulting binary is harder to reverse-engineer than raw Python bytecode.

---

## 🔮 Future Considerations

1. **Plugin Manifest**: Optional `tool.json` for metadata
2. **Hot Reload**: Reload tools without restart
3. **Tool Dependencies**: Declare external tool requirements
4. **Async Execution**: Migrate from QThread to asyncio
5. **Remote Execution**: Run tools on remote hosts
6. **Result Database**: SQLite for scan history
