# =============================================================================
# modules/dnsrecon.py
#
# DNSRecon - Advanced DNS Enumeration Tool
# =============================================================================

import os
import shlex
import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QButtonGroup, QFileDialog
)

from modules.bases import ToolBase, ToolCategory
from core.tgtinput import parse_targets, TargetInput
from core.fileops import create_target_dirs
from ui.worker import ToolExecutionMixin
from ui.styles import (
    RunButton, StopButton, BrowseButton,
    StyledLineEdit, StyledRadioButton,
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView,
    ToolSplitter, StyledToolView
)


class DnsReconTool(ToolBase):
    """DNSRecon enumeration tool plugin."""

    name = "DNSRecon"
    category = ToolCategory.INFO_GATHERING

    @property
    def description(self) -> str:
        return "Advanced DNS enumeration (Zone Transfer, Google/Bing Scraping, Brute Force, etc.)"

    @property
    def icon(self) -> str:
        return "🔍"

    def get_widget(self, main_window: QWidget) -> QWidget:
        return DnsReconView(main_window=main_window)


class DnsReconView(StyledToolView, ToolExecutionMixin):
    """DNSRecon advanced DNS enumeration interface."""
    
    tool_name = "DNSRecon"
    tool_category = "INFO_GATHERING"
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        
        # State
        self.modes = {}
        self.targets_queue = []
        self._current_target_override = None
        
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
        
        self.run_button = RunButton("RUN DNSRECON")
        self.run_button.clicked.connect(self.run_scan)
        self.stop_button = StopButton()
        self.stop_button.clicked.connect(self.stop_scan)
        
        target_row.addWidget(self.run_button)
        target_row.addWidget(self.stop_button)
        control_layout.addLayout(target_row)
        
        # ==================== CONFIGURATION GROUP ====================
        config_group = StyledGroupBox("Scan Configuration")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(15)
        
        # Scan Types Grid
        types_layout = QGridLayout()
        types_layout.setHorizontalSpacing(15)
        types_layout.setVerticalSpacing(10)
        
        self.scan_mode_group = QButtonGroup(self)
        self.scan_mode_group.setExclusive(True)
        
        scan_modes = [
            ("Standard (STD)", "std", 0, 0),
            ("Zone Transfer (AXFR)", "axfr", 0, 1),
            ("Reverse Lookup (PTR)", "rvl", 0, 2),
            ("Google Enumeration (GOO)", "goo", 1, 0),
            ("Bing Enumeration (BING)", "bing", 1, 1),
            ("Cache Snooping (SNOOP)", "snoop", 1, 2),
            ("Dictionary Brute Force (BRT)", "brt", 2, 0),
            ("Zone Walk (WALK)", "zonewalk", 2, 1),
        ]
        
        for label, mode_id, row, col in scan_modes:
            rb = StyledRadioButton(label)
            if mode_id == "std":
                rb.setChecked(True)
            rb.toggled.connect(self.update_command)
            rb.toggled.connect(self._on_mode_changed)
            self.scan_mode_group.addButton(rb)
            self.modes[mode_id] = rb
            types_layout.addWidget(rb, row, col)
        
        config_layout.addLayout(types_layout)
        
        # Dictionary Selection (conditional)
        self.dict_container = QWidget()
        dict_layout = QHBoxLayout(self.dict_container)
        dict_layout.setContentsMargins(0, 0, 0, 0)
        
        dict_label = StyledLabel("Wordlist:")
        self.dict_input = StyledLineEdit()
        self.dict_input.setPlaceholderText("/path/to/wordlist.txt")
        self.dict_input.textChanged.connect(self.update_command)
        
        self.dict_browse_btn = BrowseButton()
        self.dict_browse_btn.clicked.connect(self._browse_dict)
        
        dict_layout.addWidget(dict_label)
        dict_layout.addWidget(self.dict_input)
        dict_layout.addWidget(self.dict_browse_btn)
        
        self.dict_container.setVisible(False)
        config_layout.addWidget(self.dict_container)
        
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
        self.output.setPlaceholderText("DNSRecon results will appear here...")
        
        splitter.addWidget(self.output)
        splitter.setSizes([350, 400])
        
        main_layout.addWidget(splitter)
    
    def _on_mode_changed(self):
        if "brt" in self.modes:
            is_brute = self.modes["brt"].isChecked()
            self.dict_container.setVisible(is_brute)
            self.update_command()
    
    def _browse_dict(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Wordlist", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.dict_input.setText(file_path)

    # -------------------------------------------------------------------------
    # Command Builder
    # -------------------------------------------------------------------------

    def build_command(self, preview: bool = False) -> str:
        """
        Builds the DNSRecon command string.
        """
        cmd = ["dnsrecon"]
        
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
        
        # Mode Logic
        selected_mode = "std"
        for mode_id, rb in self.modes.items():
            if rb.isChecked():
                selected_mode = mode_id
                break
        
        if selected_mode == "brt":
            # Brute force needs domain and dict
            cmd.extend(["-d", target, "-t", "brt"])
            dict_path = self.dict_input.text().strip()
            if dict_path:
                cmd.extend(["-D", dict_path])
            else:
                if preview:
                    cmd.extend(["-D", "<wordlist>"])
                else:
                    raise ValueError("Wordlist required for Brute Force mode")
        elif selected_mode == "rvl":
            # Reverse lookup often takes IP or Range
            if "/" in target or (target and target[0].isdigit()):
                cmd.extend(["-r", target])
            else:
                 cmd.extend(["-d", target, "-t", "rvl"])
        else:
            # Standard modes
            cmd.extend(["-d", target, "-t", selected_mode])
            
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
    
    
    def run_scan(self):
        raw_input = self.target_input.get_target().strip()
        if not raw_input:
            self._notify("Please enter a target.")
            return

        try:
            targets, source = parse_targets(raw_input)
            if not targets:
                raise ValueError("No valid targets found")
            
            self.output.clear()
            self.targets_queue = list(targets)
            self._process_next_target()
            
        except Exception as e:
            self._error(str(e))

    def _process_next_target(self):
        if not self.targets_queue:
            return

        target = self.targets_queue.pop(0)
        self._current_target_override = target
        
        self._info(f"Running DNSRecon for: {target}")
        self._section(f"DNSRECON: {target}")
        
        try:
            base_dir = create_target_dirs(target, group_name=None)
            cmd_str = self.build_command(preview=False)
            
            # Using mixing's start_execution
            # We don't clear output on subsequent targets to keep history
            first_target = (target == self._current_target_override) and (len(self.targets_queue) + 1 == len(parse_targets(self.target_input.get_target())[0])) 
            # Actually, simplify: if we cleared at run_scan, we don't clear here.
            # ToolExecutionMixin `start_execution` has `clear_output` param, default True.
            
            self.start_execution(cmd_str, clear_output=False, buffer_output=False)
            
        except Exception as e:
            self._error(f"Error starting scan: {e}")
            self._process_next_target()

    def on_execution_finished(self):
        """Called when a single process execution finishes."""
        self._raw("<br>")
        self._current_target_override = None
        
        if self.targets_queue:
            self._process_next_target()
        else:
            super().on_execution_finished()
