# Contributing to VAJRA-OSP

Thank you for your interest in contributing to VAJRA! This document provides guidelines and instructions for contributing.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How Can I Contribute?](#how-can-i-contribute)
3. [Development Setup](#development-setup)
4. [Contribution Workflow](#contribution-workflow)
5. [Adding New Tools](#adding-new-tools)
6. [Code Style Guidelines](#code-style-guidelines)
7. [Pull Request Process](#pull-request-process)
8. [Recognition](#recognition)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful in all interactions.

### Expected Behavior

- ✅ Use welcoming and inclusive language
- ✅ Be respectful of differing viewpoints
- ✅ Accept constructive criticism gracefully
- ✅ Focus on what's best for the community
- ✅ Show empathy towards others

### Unacceptable Behavior

- ❌ Harassment or discriminatory language
- ❌ Trolling or insulting comments
- ❌ Personal or political attacks
- ❌ Publishing others' private information
- ❌ Unprofessional conduct

---

## How Can I Contribute?

### 🐛 Reporting Bugs

**Before submitting:**
1. Check existing issues to avoid duplicates
2. Collect information about your environment
3. Gather reproduction steps

**Bug Report Template:**

```markdown
### Description
Clear description of the bug

### Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. See error

### Expected Behavior
What should happen

### Actual Behavior
What actually happens

### Environment
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11.2]
- VAJRA Version: [e.g., commit hash]

### Additional Context
Any other relevant information
```

### 💡 Suggesting Enhancements

**Enhancement Request Template:**

```markdown
### Feature Description
Clear description of the proposed feature

### Use Case
Why is this feature needed?

### Proposed Solution
How should it work?

### Alternatives Considered
Other approaches you've thought about

### Additional Context
Screenshots, mockups, examples
```

### 🔧 Contributing Code

We welcome:
- **New tools** - Add security tool integrations
- **Bug fixes** - Fix reported issues
- **Improvements** - Enhance existing features
- **Documentation** - Improve docs and examples
- **Tests** - Add test coverage (when testing framework exists)

---

## Development Setup

### Prerequisites

```bash
# Required
- Python 3.10+ (3.11+ recommended)
- Git
- pip

# Optional
- Virtual environment tool (venv/virtualenv)
```

### Setup Steps

```bash
# 1. Fork the repository on GitHub

# 2. Clone YOUR fork
git clone https://github.com/YOUR_USERNAME/VAJRA-OSP.git
cd VAJRA-OSP

# 3. Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/VAJRA-OSP.git

# 4. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 5. Install dependencies
pip install -r requirements.txt

# 6. Verify installation
python main.py
```

---

## Contribution Workflow

### 1. Create a Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/my-new-tool
# or
git checkout -b fix/issue-123
```

**Branch naming conventions:**
- `feature/` - New features or tools
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring

### 2. Make Changes

- Write clean, readable code
- Follow existing patterns
- Add comments for complex logic
- Test your changes locally

### 3. Commit Changes

```bash
# Stage changes
git add modules/mytool.py

# Commit with clear message
git commit -m "Add MyTool integration for XYZ scanning"
```

**Commit message format:**
```
<type>: <short summary>

<optional detailed description>

<optional footer>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Code style (formatting)
- `refactor:` - Code restructuring
- `perf:` - Performance improvement
- `test:` - Adding tests

**Examples:**
```bash
git commit -m "feat: Add Nuclei vulnerability scanner integration"
git commit -m "fix: Resolve port parsing issue in Nmap module"
git commit -m "docs: Update CONTRIBUTING.md with new guidelines"
```

### 4. Push to Your Fork

```bash
git push origin feature/my-new-tool
```

### 5. Create Pull Request

1. Go to your fork on GitHub
2. Click "Pull Request"
3. Select `base: main` ← `compare: feature/my-new-tool`
4. Fill out PR template
5. Submit!

---

## Adding New Tools

### Quick Start Template

Create `modules/mytool.py`:

```python
"""
MyTool - Short description
"""

from modules.bases import ToolBase, ToolCategory, IOMixin, RunMixin
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox
from PySide6.QtCore import Slot
from ui.styles import get_button_style, SUCCESS, ERROR


class MyTool(ToolBase):
    """MyTool implementation"""
    
    name = "My Tool"
    category = ToolCategory.INFO_GATHERING
    
    def get_widget(self, main_window):
        return MyToolWidget(main_window)


class MyToolWidget(QWidget, IOMixin, RunMixin):
    """UI for MyTool"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel(f"<h2>{MyTool.name}</h2>")
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Brief description of what this tool does")
        layout.addWidget(desc)
        
        # Target input + output area (from IOMixin)
        self.setup_io(layout)
        
        # Optional: Add custom options
        self.verbose_option = QCheckBox("Verbose Output")
        layout.addWidget(self.verbose_option)
        
        # Run controls (from RunMixin)
        self.setup_run_controls(layout)
        
        self.setLayout(layout)
    
    def build_command(self):
        """Build the command to execute"""
        # Get targets
        targets = self.target_input.get_targets()
        if not targets:
            return None
        
        # Build command
        cmd = ["mytool"]  # Replace with actual tool command
        
        # Add options
        if self.verbose_option.isChecked():
            cmd.append("-v")
        
        # Add target
        cmd.append(targets[0])
        
        return cmd
    
    def run_scan(self):
        """Execute the scan"""
        command = self.build_command()
        
        if not command:
            self.main_window.notification_manager.show_toast(
                "Please enter a target", "warning"
            )
            return
        
        # Notify user
        self.main_window.notification_manager.show_toast(
            "Starting scan...", "info"
        )
        
        # Start worker (from RunMixin)
        self.start_worker(command, tool_name="mytool")
    
    @Slot(str)
    def handle_output(self, line):
        """Handle output from worker"""
        # Optional: Colorize output
        colored_line = self.colorize_line(line)
        self.output_area.append(colored_line)
    
    def colorize_line(self, line):
        """Add color coding to output"""
        if "error" in line.lower() or "failed" in line.lower():
            return f'<span style="color: {ERROR};">{line}</span>'
        elif "success" in line.lower() or "found" in line.lower():
            return f'<span style="color: {SUCCESS};">{line}</span>'
        return line
    
    @Slot(int)
    def handle_scan_finished(self, exit_code):
        """Handle scan completion"""
        if exit_code == 0:
            self.main_window.notification_manager.show_toast(
                "Scan completed successfully", "success"
            )
        else:
            self.main_window.notification_manager.show_toast(
                f"Scan failed with exit code {exit_code}", "error"
            )
```

### Tool Checklist

Before submitting a new tool:

- [ ] Tool class inherits from `ToolBase`
- [ ] `name` attribute is set
- [ ] `category` attribute is set (valid `ToolCategory`)
- [ ] `get_widget()` method is implemented
- [ ] Widget uses `IOMixin` for input/output
- [ ] Widget uses `RunMixin` for execution controls
- [ ] `build_command()` returns a list (not string)
- [ ] Empty input is handled gracefully
- [ ] Tool provides user feedback (notifications)
- [ ] Output is saved to log file automatically (via RunMixin)
- [ ] Code follows style guidelines
- [ ] Tool tested locally with real targets
- [ ] Documentation added (docstrings)

---

## Code Style Guidelines

### Python Style (PEP 8)

```python
# Naming conventions
class MyClass:           # PascalCase for classes
    CONSTANT = 42        # UPPER_CASE for constants
    
    def my_method(self):     # snake_case for functions/methods
        my_variable = 10     # snake_case for variables
        _private_var = 20    # _leading underscore for private

# Line length: 88 characters (Black style)
# Use 4 spaces for indentation (not tabs)
```

### Imports

```python
# Order: standard library → third-party → local
import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal, Slot

from core.config import ConfigManager
from modules.bases import ToolBase
```

### Documentation

```python
def parse_targets(input_text: str) -> list[str]:
    """
    Parse target input from user.
    
    Handles both single targets and file paths containing
    multiple targets (one per line).
    
    Args:
        input_text: Raw input string from user
    
    Returns:
        List of parsed target strings
    
    Example:
        >>> parse_targets("example.com")
        ['example.com']
        >>> parse_targets("/path/to/targets.txt")
        ['example.com', 'test.com']
    """
    pass
```

### Type Hints

Use type hints where beneficial:

```python
from typing import Optional, List, Dict

def create_directory(path: str) -> bool:
    """Create directory if it doesn't exist"""
    pass

def get_config(key: str) -> Optional[str]:
    """Get configuration value"""
    pass

def parse_output(file_path: str) -> Dict[str, List[str]]:
    """Parse tool output"""
    pass
```

### Error Handling

```python
# Be specific with exceptions
try:
    result = parse_file(path)
except FileNotFoundError:
    logger.error(f"File not found: {path}")
    return None
except PermissionError:
    logger.error(f"Permission denied: {path}")
    return None

# Avoid bare except
# ❌ BAD
try:
    risky_operation()
except:
    pass

# ✅ GOOD
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
```

### Security

```python
# Always use list-based commands
# ✅ GOOD (safe from injection)
subprocess.run(["nmap", "-p", ports, target])

# ❌ BAD (vulnerable to injection)
subprocess.run(f"nmap -p {ports} {target}", shell=True)

# Validate user input
def validate_port(port: str) -> bool:
    """Validate port number"""
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except ValueError:
        return False

# Sanitize file paths
from pathlib import Path

def safe_path(user_path: str) -> Path:
    """Ensure path is within allowed directory"""
    base_dir = Path("/tmp/Vajra-results")
    full_path = (base_dir / user_path).resolve()
    
    if not str(full_path).startswith(str(base_dir)):
        raise ValueError("Invalid path")
    
    return full_path
```

---

## Pull Request Process

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature (tool)
- [ ] Enhancement (existing feature)
- [ ] Documentation update
- [ ] Code refactoring

## Changes Made
- Added MyTool integration
- Fixed XYZ bug in ABC module
- Updated documentation for DEF

## Testing
- [ ] Tested locally
- [ ] Tested with real targets
- [ ] No errors in console

## Screenshots (if applicable)
Attach screenshots of new UI features

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings introduced
```

### Review Process

1. **Automated checks** (if configured)
   - Linting
   - Style checking

2. **Code review** by maintainers
   - Functionality
   - Code quality
   - Security
   - Documentation

3. **Feedback**
   - Address review comments
   - Push updates to same branch
   - PR updates automatically

4. **Approval & Merge**
   - Maintainer approves
   - PR is merged to main
   - Branch can be deleted

### After Your PR is Merged

```bash
# Update your local repo
git checkout main
git pull upstream main

# Delete feature branch
git branch -d feature/my-new-tool

# Update your fork
git push origin main
```

---

## Common Contribution Scenarios

### Scenario 1: Fix a Bug

```bash
# 1. Create fix branch
git checkout -b fix/port-parsing-issue

# 2. Make changes
# Edit modules/nmap.py

# 3. Test fix
python main.py
# Verify the bug is fixed

# 4. Commit
git add modules/nmap.py
git commit -m "fix: Resolve port range parsing in Nmap module"

# 5. Push and create PR
git push origin fix/port-parsing-issue
```

### Scenario 2: Add New Tool

```bash
# 1. Create feature branch
git checkout -b feature/add-masscan

# 2. Create tool file
touch modules/masscan.py

# 3. Implement tool (use template above)

# 4. Test thoroughly
python main.py
# Navigate to tool and test with real target

# 5. Commit
git add modules/masscan.py
git commit -m "feat: Add Masscan port scanner integration

- Implements Masscan as a new port scanning tool
- Supports rate limiting and port range options
- Includes color-coded output parsing"

# 6. Push and create PR
git push origin feature/add-masscan
```

### Scenario 3: Update Documentation

```bash
# 1. Create docs branch
git checkout -b docs/improve-readme

# 2. Edit documentation
# Edit README.md, DEVELOPMENT.md, etc.

# 3. Commit
git add README.md
git commit -m "docs: Improve installation instructions in README"

# 4. Push and create PR
git push origin docs/improve-readme
```

---

## Recognition

### Contributors

All contributors will be:
- Listed in project acknowledgments
- Credited in release notes
- Recognized in the community

### Contribution Types

We value all contributions:
- 💻 **Code** - Tools, features, fixes
- 📖 **Documentation** - Guides, examples, tutorials
- 🐛 **Bug Reports** - Detailed issue reports
- 💡 **Ideas** - Feature suggestions, improvements
- 🎨 **Design** - UI/UX enhancements
- 🧪 **Testing** - Finding and reporting bugs

---

## Questions?

### Getting Help

- **Documentation**: Check [DEVELOPMENT.md](DEVELOPMENT.md) and [ARCHITECTURE.md](ARCHITECTURE.md)
- **Issues**: Browse existing issues for similar questions
- **Code Examples**: Look at existing tools in `modules/`

### Contact

- Open an issue for questions
- Tag with `question` label
- Be specific and provide context

---

## Final Notes

### Do's ✅

- Write clean, readable code
- Test thoroughly before submitting
- Follow existing patterns and conventions
- Be respectful and professional
- Ask questions when unclear

### Don'ts ❌

- Don't commit sensitive data (API keys, passwords)
- Don't include large binary files
- Don't break existing functionality
- Don't ignore code review feedback
- Don't submit untested code

---

**Thank you for contributing to VAJRA! 🙏**

Your contributions make this project better for everyone.

---

**Last Updated:** 2026-01-22
