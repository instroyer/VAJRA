# =============================================================================
# modules/searchsploit.py
#
# SearchSploit - Exploit Database Search Tool
# =============================================================================

import shlex
import html
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
)
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from ui.worker import ProcessWorker
from ui.styles import (
    RunButton, StopButton, CopyButton,
    StyledLineEdit, StyledCheckBox,
    StyledLabel, HeaderLabel, CommandDisplay, OutputView,
    StyledGroupBox, ToolSplitter, StyledToolView,
    SafeStop, OutputHelper
)


class SearchSploitTool(ToolBase):
    """SearchSploit exploit search tool plugin."""

    name = "SearchSploit"
    category = ToolCategory.INFO_GATHERING

    @property
    def description(self) -> str:
        return "Search for exploits in Exploit-DB."

    @property
    def icon(self) -> str:
        return "🔍"

    def get_widget(self, main_window):
        return SearchSploitToolView(main_window=main_window)


class SearchSploitToolView(StyledToolView, SafeStop, OutputHelper):
    """SearchSploit exploit search interface."""

    tool_name = "SearchSploit"
    tool_category = "INFO_GATHERING"

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_safe_stop()
        self._build_ui()
        self.update_command()

    def _build_ui(self):
        """Build UI."""
        # setStyleSheet handled by StyledToolView
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = ToolSplitter()
        
        # ==================== CONTROL PANEL ====================
        control_panel = QWidget()
        # Removed legacy style
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)
        
        # Header
        header = HeaderLabel(self.tool_category, self.tool_name)
        control_layout.addWidget(header)
        
        # Search Input
        search_group = StyledGroupBox("Search")
        search_layout = QVBoxLayout(search_group)
        
        search_row = QHBoxLayout()
        self.search_input = StyledLineEdit(show_icon=True)
        self.search_input.setPlaceholderText("e.g. apache 2.4, wordpress, ssh")
        self.search_input.textChanged.connect(self.update_command)
        self.search_input.returnPressed.connect(self.run_scan)
        
        search_row.addWidget(self.search_input)
        search_layout.addLayout(search_row)
        
        filter_row = QHBoxLayout()
        self.filter_input = StyledLineEdit()
        self.filter_input.setPlaceholderText("Grep Filter (optional)...")
        self.filter_input.textChanged.connect(self.update_command)
        self.filter_input.returnPressed.connect(self.run_scan)
        
        filter_row.addWidget(StyledLabel("Grep:"))
        filter_row.addWidget(self.filter_input)
        search_layout.addLayout(filter_row)
        
        control_layout.addWidget(search_group)
        
        # Options
        options_group = StyledGroupBox("⚙️ Options")
        options_layout = QGridLayout(options_group)
        
        self.case_check = StyledCheckBox("Case Sensitive (-c)")
        self.case_check.stateChanged.connect(self.update_command)
        
        self.exact_check = StyledCheckBox("Exact Match (-e)")
        self.exact_check.stateChanged.connect(self.update_command)
        
        self.strict_check = StyledCheckBox("Strict Match (-s)")
        self.strict_check.stateChanged.connect(self.update_command)
        
        self.title_check = StyledCheckBox("Title Only (-t)")
        self.title_check.stateChanged.connect(self.update_command)
        
        self.path_check = StyledCheckBox("Show Path (-p)")
        self.path_check.stateChanged.connect(self.update_command)
        
        self.www_check = StyledCheckBox("Show URLs (-w)")
        self.www_check.stateChanged.connect(self.update_command)
        
        self.json_check = StyledCheckBox("JSON Output (-j)")
        self.json_check.stateChanged.connect(self.update_command)
        
        self.overflow_check = StyledCheckBox("Overflow (-o)")
        self.overflow_check.stateChanged.connect(self.update_command)
        
        options_layout.addWidget(self.case_check, 0, 0)
        options_layout.addWidget(self.exact_check, 0, 1)
        options_layout.addWidget(self.strict_check, 0, 2)
        options_layout.addWidget(self.title_check, 0, 3)
        options_layout.addWidget(self.path_check, 1, 0)
        options_layout.addWidget(self.www_check, 1, 1)
        options_layout.addWidget(self.json_check, 1, 2)
        options_layout.addWidget(self.overflow_check, 1, 3)
        
        control_layout.addWidget(options_group)

        # Command Preview
        self.command_input = StyledLineEdit()
        self.command_input.setReadOnly(True)
        self.command_input.setPlaceholderText("Command preview...")
        control_layout.addWidget(self.command_input)

        # Buttons
        btn_layout = QHBoxLayout()
        self.run_button = RunButton("SEARCH")
        self.run_button.clicked.connect(self.run_scan)
        self.stop_button = StopButton()
        self.stop_button.clicked.connect(self.stop_scan)
        
        btn_layout.addWidget(self.run_button)
        btn_layout.addWidget(self.stop_button)
        control_layout.addLayout(btn_layout)

        control_layout.addStretch()
        splitter.addWidget(control_panel)

        # Output
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("Search results will appear here...")
        
        splitter.addWidget(self.output)
        splitter.setSizes([450, 400])
        
        main_layout.addWidget(splitter)
        
    # -------------------------------------------------------------------------
    # Command Builder
    # -------------------------------------------------------------------------

    def build_command(self, preview: bool = False) -> str:
        cmd = ["searchsploit"]
        
        if self.case_check.isChecked(): cmd.append("-c")
        if self.exact_check.isChecked(): cmd.append("-e")
        if self.strict_check.isChecked(): cmd.append("-s")
        if self.title_check.isChecked(): cmd.append("-t")
        if self.json_check.isChecked(): cmd.append("-j")
        if self.overflow_check.isChecked(): cmd.append("-o")
        if self.path_check.isChecked(): cmd.append("-p")
        if self.www_check.isChecked(): cmd.append("-w")
        
        term = self.search_input.text().strip()
        if term:
            # searchsploit allows multiple terms space-separated
            cmd.extend(term.split())
        elif preview:
            cmd.append("<search_term>")
        else:
            raise ValueError("Search term required")
            
        # Grep filter
        # We handle this by piping. ProcessWorker supports piped commands if shell=True is used
        grep = self.filter_input.text().strip()
        
        base_cmd = " ".join(shlex.quote(x) for x in cmd)
        
        if grep:
            base_cmd += f" | grep -i {shlex.quote(grep)}"
            
        return base_cmd

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
        try:
            cmd_str = self.build_command(preview=False)

            self.output.clear()
            self._info(f"Searching Exploit-DB...")
            self._section("SEARCHSPLOIT RESULTS")
            self._section("Command")
            self._raw(html.escape(cmd_str))

            self.worker = ProcessWorker(cmd_str, shell=True)
            self.worker.output_ready.connect(self._on_output)
            self.worker.finished.connect(self._on_scan_completed)
            self.worker.error.connect(lambda e: self._error(str(e)))

            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)

            if self.main_window:
                self.main_window.active_process = self.worker

            self.worker.start()

        except Exception as e:
            self._error(str(e))

    def _on_scan_completed(self):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.worker = None
        if self.main_window:
             self.main_window.active_process = None
        self._section("Search Completed")

    def _on_output(self, line):
        # ANSI escape codes regex
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

        # ProcessWorker might send multiple lines at once
        raw_lines = line.split('\n')
        
        for raw_line in raw_lines:
            # Clean up line
            clean = raw_line.rstrip()
            # if not clean: continue # Don't skip empty lines, need them for spacing

            # Remove ANSI codes
            clean_text = ansi_escape.sub('', clean)
            
            # Escape HTML
            safe_line = html.escape(clean_text)
            
            # If line is empty after cleaning, just print a break (or empty div)
            if not safe_line:
                self._raw("<br>")
                continue

            lower_line = clean_text.lower()
            
            # Use pre-wrap to preserve spaces for table alignment
            style_base = "white-space: pre-wrap; font-family: monospace; display: block;"

            # Single color output (Default)
            self._raw(f'<span style="{style_base}">{safe_line}</span>')
