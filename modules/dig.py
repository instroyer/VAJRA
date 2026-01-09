# =============================================================================
# modules/dig.py
#
# Dig - DNS Information Gathering Tool
# =============================================================================

import os
import shlex
import html
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout, QWidget
)

from modules.bases import ToolBase, ToolCategory
from core.tgtinput import parse_targets, TargetInput
from core.fileops import create_target_dirs
from ui.worker import ToolExecutionMixin
from ui.styles import (
    # Widgets
    RunButton, StopButton,
    StyledLineEdit, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView,
    ToolSplitter, StyledToolView,
    COLOR_BORDER_DEFAULT
)


class DigTool(ToolBase):
    """Dig DNS gathering tool plugin."""

    name = "Dig"
    category = ToolCategory.INFO_GATHERING

    @property
    def description(self) -> str:
        return "Perform DNS lookups and information gathering (A, MX, NS, AXFR, etc.)"

    @property
    def icon(self) -> str:
        return "🌐"

    def get_widget(self, main_window: QWidget) -> QWidget:
        return DigToolView(main_window=main_window)


class DigToolView(StyledToolView, ToolExecutionMixin):
    """Dig DNS information gathering interface."""
    
    tool_name = "Dig"
    tool_category = "INFO_GATHERING"
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_safe_stop()
        
        # State
        self.type_checks = {}
        self.log_file = None
        
        # Build UI
        self._build_ui()
        self.update_command()
    
    def _build_ui(self):
        """Build the complete UI."""
        # Note: setStyleSheet handled by StyledToolView
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = ToolSplitter()
        
        # ==================== CONTROL PANEL ====================
        control_panel = QWidget()
        
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)
        
        # Header
        header = HeaderLabel(self.tool_category, self.tool_name)
        control_layout.addWidget(header)
        
        # Target Row
        target_label = StyledLabel("Target")
        control_layout.addWidget(target_label)
        
        target_row = QHBoxLayout()
        self.target_input = TargetInput()
        self.target_input.input_box.textChanged.connect(self.update_command)
        target_row.addWidget(self.target_input, 1)
        
        self.run_button = RunButton("RUN DIG")
        self.run_button.clicked.connect(self.run_scan)
        self.stop_button = StopButton()
        self.stop_button.clicked.connect(self.stop_scan)
        
        target_row.addWidget(self.run_button)
        target_row.addWidget(self.stop_button)
        control_layout.addLayout(target_row)
        
        # ==================== QUERY CONFIGURATION ====================
        config_group = StyledGroupBox("Query Configuration")
        config_layout_inner = QHBoxLayout(config_group)
        
        # Query Types
        types_layout = QGridLayout()
        types_layout.setHorizontalSpacing(15)
        types_layout.setVerticalSpacing(8)
        
        query_types = [
            ("A (IPv4)", "A", 0, 0),
            ("AAAA (IPv6)", "AAAA", 0, 1),
            ("MX (Mail)", "MX", 0, 2),
            ("NS (NameServer)", "NS", 0, 3),
            ("TXT (Text/SPF)", "TXT", 1, 0),
            ("CNAME (Alias)", "CNAME", 1, 1),
            ("SOA (Auth)", "SOA", 1, 2),
            ("PTR (Reverse)", "PTR", 1, 3),
            ("ANY (All)", "ANY", 2, 0),
            ("AXFR (Zone)", "AXFR", 2, 1),
        ]
        
        for label, flag, row, col in query_types:
            cb = StyledCheckBox(label)
            if flag == "A":
                cb.setChecked(True)
            cb.stateChanged.connect(self.update_command)
            self.type_checks[flag] = cb
            types_layout.addWidget(cb, row, col)
        
        # Extra options
        self.trace_check = StyledCheckBox("Trace (+trace)")
        self.trace_check.stateChanged.connect(self.update_command)
        types_layout.addWidget(self.trace_check, 2, 2)
        
        self.short_check = StyledCheckBox("Short (+short)")
        self.short_check.stateChanged.connect(self.update_command)
        types_layout.addWidget(self.short_check, 2, 3)
        
        config_layout_inner.addLayout(types_layout, stretch=2)
        
        # Separator
        line = QWidget()
        line.setFixedWidth(1)
        line.setStyleSheet(f"background-color: {COLOR_BORDER_DEFAULT};")
        config_layout_inner.addWidget(line)
        
        # Nameserver
        options_layout = QVBoxLayout()
        options_layout.setSpacing(5)
        
        ns_label = StyledLabel("Nameserver (@):")
        self.ns_input = StyledLineEdit()
        self.ns_input.setPlaceholderText("e.g. 8.8.8.8")
        self.ns_input.textChanged.connect(self.update_command)
        
        options_layout.addWidget(ns_label)
        options_layout.addWidget(self.ns_input)
        options_layout.addStretch()
        
        config_layout_inner.addLayout(options_layout, stretch=1)
        control_layout.addWidget(config_group)
        
        # Command Display
        self.command_input = StyledLineEdit()
        self.command_input.setReadOnly(True)
        self.command_input.setPlaceholderText("Command preview...")
        control_layout.addWidget(self.command_input)
        
        control_layout.addStretch()
        splitter.addWidget(control_panel)
        
        # ==================== OUTPUT AREA ====================
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("Dig results will appear here...")
        
        splitter.addWidget(self.output)
        splitter.setSizes([350, 400])
        
        main_layout.addWidget(splitter)
    
    # -------------------------------------------------------------------------
    # Command Builder
    # -------------------------------------------------------------------------

    def build_command(self, preview: bool = False) -> str:
        """
        Builds the Dig command string.
        """
        cmd = ["dig"]
        
        # Target logic
        if hasattr(self, '_current_target_override') and self._current_target_override and not preview:
            target = self._current_target_override
        else:
            target = self.target_input.get_target().strip()
            if not target:
                if preview:
                    target = "<target>"
                else:
                    raise ValueError("Target is required")
        
        # Nameserver
        ns = self.ns_input.text().strip()
        if ns:
            cmd.append(f"@{ns}")
        
        cmd.append(target)
        
        # Types
        for flag, cb in self.type_checks.items():
            if cb.isChecked():
                cmd.append(flag)
        
        # Flags
        if self.trace_check.isChecked():
            cmd.append("+trace")
        if self.short_check.isChecked():
            cmd.append("+short")
            
        return " ".join(shlex.quote(x) for x in cmd)

    def update_command(self):
        try:
            cmd_str = self.build_command(preview=True)
            self.command_input.setText(cmd_str)
        except Exception:
            self.command_input.setText("")

    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------
    
    def run_scan(self):
        raw_input = self.target_input.get_target().strip()
        if not raw_input:
            self._notify("Please enter a target domain.")
            return
        
        try:
            targets, source = parse_targets(raw_input)
            if not targets:
                raise ValueError("No valid targets found")
            
            # Start Batch Execution (Mixin)
            # We don't have a single output file for batch, so we pass
            self.output.clear()
            self._info("Starting Batch Dig Scan...")
            self.targets_queue = list(targets)
            self._process_next_target()
            
        except Exception as e:
            self._error(str(e))

    def _process_next_target(self):
        if not self.targets_queue:
            return

        target = self.targets_queue.pop(0)
        self._info(f"Running Dig for: {target}")
        self._section(f"DIG: {target}")
        
        try:
            self._current_target_override = target
            
            # Setup logging
            base_dir = create_target_dirs(target, group_name=None)
            logs_dir = os.path.join(base_dir, "Logs")
            os.makedirs(logs_dir, exist_ok=True)
            self.log_file = os.path.join(logs_dir, "dig.txt")
            
            # Use 'tee' to save output to file while streaming to UI
            cmd_str = self.build_command(preview=False)
            cmd_str += f" | tee {shlex.quote(self.log_file)}"
            
            # Use Mixin's start_execution. 
            # We set output_path=None because we handle logging via tee (Dig specific pref).
            # Important: clear_output=False so we don't wipe previous targets.
            self.start_execution(cmd_str, output_path=None, clear_output=False, buffer_output=False)
            
        except Exception as e:
            self._error(f"Error starting scan: {e}")
            # Try next target
            self.on_execution_finished()

    def on_new_output(self, line):
        """Handle new output from the worker."""
        # Clean up line
        clean = line.rstrip()
        
        # Remove ANSI codes (OutputHelper)
        clean_text = self.strip_ansi(clean)
        
        # Escape HTML
        safe_line = html.escape(clean_text)
        
        # Preserve whitespace for terminal-like look
        style = "white-space: pre-wrap; font-family: monospace; display: block;"
        
        if not safe_line:
            self._raw("<br>")
        else:
            self._raw(f'<span style="{style}">{safe_line}</span>')

    def on_execution_finished(self):
        self._raw("<br>")
        self._current_target_override = None # Reset
        
        if self.targets_queue:
            self._process_next_target()
        else:
            super().on_execution_finished()
