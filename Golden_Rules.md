# VAJRA-OSP Contributor Package

This document consolidates **CONTRIBUTING.md**, **Tool Generator Guide**, and **Pull Request Template** into a single authoritative reference.

---

## PART 1: CONTRIBUTING.md

### Purpose

This guide defines how to contribute to **VAJRA-OSP** safely, consistently, and professionally.

VAJRA is a **platform**, not a collection of scripts. All contributions must preserve architectural discipline, UX consistency, and security-tool standards.

---

### Who This Is For

* Core developers
* Contributors
* Reviewers
* Automated LLM agents

---

### Non-Negotiable Rules

You MUST NOT:

* Change existing tool behavior
* Add inline styles inside tools
* Use raw shell command strings
* Add duplicate output formatting
* Add new colors outside the theme
* Touch architecture without approval
* Embed sudo in commands
* Manage notifications directly in tools
* Manage output paths manually
* Implement custom execution lifecycles (use ToolExecutionMixin)

You MUST:

* Follow `GOLDEN_RULES.md`
* Use the Golden Tool Template
* Keep UI, output, and logic centralized

---

### Project Structure (Enforced)

```
VAJRA/
├── core/          # No Qt imports
├── ui/            # Styles, widgets, workers
├── modules/
│       └─<tool>.py
└── GOLDEN_RULES.md
```

---

### Contribution Workflow

1. Read `GOLDEN_RULES.md`
2. Copy the Golden Tool Template
3. Implement changes
4. Run application locally
5. Open Pull Request

Any deviation must be justified explicitly.

---

## PART 2: TOOL GENERATOR SCRIPT (REFERENCE)

> This is a **template-driven guide**. It can be implemented as a script or used manually.

### Tool Creation Checklist

When creating a new tool:

1. Choose category (RECON / SCANNING / FUZZING / MISC)
2. Create file:

```
modules/tools/<category>/<tool_name>.py
```

3. Use Golden Tool Template structure

---

### Minimal Generator Pseudocode

```python
# tool_generator.py (reference)

TOOL_TEMPLATE = """
class {class_name}(QWidget, ToolBase, SafeStop, OutputHelper):
    name = "{tool_name}"
    description = "{description}"
    category = ToolCategory.{category}

    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.init_safe_stop()
        self._build_ui()
        self._connect_signals()
"""

print("Fill placeholders and save into correct directory")
```

Rules:

* Generator MUST NOT add logic
* Generator MUST NOT guess UI
* Generator MUST follow Golden Rules

---

## PART 3: PULL REQUEST TEMPLATE

> This section must be copied into `.github/pull_request_template.md` if separated.

---

### Pull Request Summary

Describe clearly what this PR does.

---

### Scope

* [ ] New Tool
* [ ] Bug Fix
* [ ] Refactor
* [ ] Documentation
* [ ] UX Improvement

---

### Golden Rules Compliance

* [ ] Followed `GOLDEN_RULES.md`
* [ ] No inline styles added
* [ ] No raw command strings used
* [ ] Used `build_command()` correctly
* [ ] Output via OutputHelper only

---

### Architecture Safety

* [ ] No Qt imports in core/
* [ ] No logic in ui/styles.py
* [ ] No per-tool UX behavior

---

### UX & Interaction

* [ ] No new colors added
* [ ] Keyboard shortcuts unaffected
* [ ] Output behavior unchanged

---

### Validation

* [ ] App launches
* [ ] Tool executes correctly
* [ ] Output renders correctly
* [ ] No Qt warnings

---

### Final Declaration

I confirm that this PR complies with VAJRA Golden Rules and introduces no architectural debt.

---

## FINAL NOTE

This document, together with `GOLDEN_RULES.md`, forms the **permanent contract** for VAJRA-OSP development.

Violations must not be merged.
