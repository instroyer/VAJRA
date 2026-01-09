# =============================================================================
# modules/whois.py
#
# Whois - Domain Registration Lookup
# =============================================================================

import os
import shlex
import html
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from modules.bases import ToolBase, ToolCategory
from core.tgtinput import parse_targets, TargetInput
from core.fileops import create_target_dirs, get_group_name_from_file
from ui.worker import ToolExecutionMixin
from ui.styles import (
    # Widgets
    RunButton, StopButton,
    StyledLabel, HeaderLabel, StyledLineEdit, OutputView,
    ToolSplitter, StyledToolView, StyledGroupBox
)


class WhoisTool(ToolBase):
    """Whois tool plugin."""
    
    name = "Whois"
    category = ToolCategory.INFO_GATHERING
    
    @property
    def icon(self) -> str:
        return "ℹ️"
    
    def get_widget(self, main_window):
        return WhoisView(main_window=main_window)


class WhoisView(StyledToolView, ToolExecutionMixin):
    """Whois domain lookup tool interface."""
    
    tool_name = "Whois"
    tool_category = "INFO_GATHERING"
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_safe_stop()
        
        # State
        self.targets_queue = []
        self.group_name = None
        self.current_target = None
        self.scanning = False
        
        # Build UI
        self._build_ui()
        self.update_command()
    
    def _build_ui(self):
        """Build the complete UI."""
        # setStyleSheet handled by StyledToolView
        
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
        
        # Target Section
        target_group = StyledGroupBox("🎯 Target")
        target_layout = QVBoxLayout(target_group)
        
        target_row = QHBoxLayout()
        self.target_input = TargetInput()
        self.target_input.input_box.textChanged.connect(self.update_command)
        target_row.addWidget(self.target_input, 1)
        target_layout.addLayout(target_row)
        
        control_layout.addWidget(target_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.run_button = RunButton("RUN WHOIS")
        self.run_button.clicked.connect(self.run_scan)
        self.stop_button = StopButton()
        self.stop_button.clicked.connect(self.stop_scan)
        
        btn_layout.addWidget(self.run_button)
        btn_layout.addWidget(self.stop_button)
        control_layout.addLayout(btn_layout)
        
        # Command Display
        self.command_input = StyledLineEdit()
        self.command_input.setReadOnly(True)
        self.command_input.setPlaceholderText("Command preview...")
        control_layout.addWidget(self.command_input)
        
        control_layout.addStretch()
        splitter.addWidget(control_panel)
        
        # ==================== OUTPUT AREA ====================
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("Whois results will appear here...")
        
        splitter.addWidget(self.output)
        splitter.setSizes([200, 500])
        
        main_layout.addWidget(splitter)

    # -------------------------------------------------------------------------
    # Command Builder
    # -------------------------------------------------------------------------

    def build_command(self, preview: bool = False) -> str:
        cmd = ["whois"]

        # Target
        # If previewing, allow current input. If running, use self.current_target from queue
        target = ""
        if preview:
            target = self.target_input.get_target().strip()
            if not target:
                target = "<target>"
        else:
            target = self.current_target
            if not target:
                raise ValueError("No target specified")
        
        cmd.append(target)
        
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
        if self.scanning:
            self._notify("Scan already in progress. Please wait or stop current scan.")
            return

        raw_input = self.target_input.get_target().strip()
        if not raw_input:
            self._notify("Please enter a target domain.")
            return

        try:
            targets, source = parse_targets(raw_input)
            if not targets:
                raise ValueError("No valid targets found")

            self.scanning = True
            self.output.clear()
            self._info("Starting Batch Whois Scan...")

            self.targets_queue = list(targets)
            self.group_name = get_group_name_from_file(raw_input) if source == "file" else None
            self._process_next_target()

        except Exception as e:
            self.scanning = False
            self._error(str(e))

    def _process_next_target(self):
        if not self.targets_queue:
            return
        
        self.current_target = self.targets_queue.pop(0)
        self._info(f"Running Whois for: {self.current_target}")
        self._section(f"WHOIS: {self.current_target}")
        
        try:
            # Setup logging
            base_dir = create_target_dirs(self.current_target, self.group_name)
            logs_dir = os.path.join(base_dir, "Logs")
            os.makedirs(logs_dir, exist_ok=True)
            output_file = os.path.join(logs_dir, "whois.txt")
            
            # Build command
            cmd_str = self.build_command(preview=False)
            cmd_str += f" | tee {shlex.quote(output_file)}"
            
            # Execute via Mixin
            self.start_execution(cmd_str, output_path=None, clear_output=False)
            
        except Exception as e:
            self._error(f"Error starting scan: {e}")
            self.on_execution_finished()

    def on_execution_finished(self):
        self._raw("<br>")
        if self.targets_queue:
            self._process_next_target()
        else:
            self.scanning = False
            super().on_execution_finished()

    def stop_scan(self):
        """Override to reset scanning state."""
        super().stop_scan()
        self.scanning = False
        self.targets_queue = []
        self.current_target = None

    def on_new_output(self, line):
        clean = line.strip()
        if clean:
             self._raw(html.escape(clean))
