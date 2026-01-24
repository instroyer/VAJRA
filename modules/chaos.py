# =============================================================================
# modules/chaos.py
#
# Chaos - ProjectDiscovery Subdomain Enumeration
# =============================================================================

import os
import shlex
import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
)

from modules.bases import ToolBase, ToolCategory
from core.tgtinput import TargetInput
from core.fileops import create_target_dirs
from ui.worker import ToolExecutionMixin
from ui.styles import (
    RunButton, StopButton, StyledLineEdit, StyledCheckBox, 
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView,
    ToolSplitter, StyledToolView
)


class ChaosTool(ToolBase):
    """
    Chaos is a tool that communicates with Chaos dataset API 
    to list subdomains of a given domain.
    """
    
    name = "Chaos"
    category = ToolCategory.SUBDOMAIN_ENUMERATION
    
    @property
    def icon(self) -> str:
        return "🌪️"
    
    def get_widget(self, main_window):
        return ChaosView(main_window=main_window)


class ChaosView(StyledToolView, ToolExecutionMixin):
    """Chaos tool interface."""
    
    tool_name = "Chaos"
    tool_category = "SUBDOMAIN_ENUMERATION"
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.log_file = None
        self._build_ui()
        self.update_command()
    
    def _build_ui(self):
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
        
        # Target Input
        target_group = StyledGroupBox("🎯 Target")
        target_layout = QHBoxLayout(target_group)
        self.target_input = TargetInput()
        self.target_input.input_box.textChanged.connect(self.update_command)
        target_layout.addWidget(self.target_input)
        control_layout.addWidget(target_group)
        
        # API Configuration
        api_group = StyledGroupBox("🔑 Authentication")
        api_layout = QVBoxLayout(api_group)
        
        key_layout = QHBoxLayout()
        key_label = StyledLabel("PDCP API Key:")
        self.key_input = StyledLineEdit()
        self.key_input.setPlaceholderText("Enter Chaos/PDCP API Key (optional)")
        self.key_input.setEchoMode(StyledLineEdit.Password)
        self.key_input.textChanged.connect(self.update_command)
        
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_input)
        api_layout.addLayout(key_layout)
        
        control_layout.addWidget(api_group)
        
        # Options
        options_group = StyledGroupBox("🚀 Options")
        options_layout = QGridLayout(options_group)
        
        self.silent_check = StyledCheckBox("Silent Mode (-silent)")
        self.silent_check.setChecked(True) # Default to silent for cleaner output parsing
        self.silent_check.stateChanged.connect(self.update_command)
        
        self.json_check = StyledCheckBox("JSON Output (-json)")
        self.json_check.stateChanged.connect(self.update_command)
        
        self.count_check = StyledCheckBox("Count Only (-count)")
        self.count_check.stateChanged.connect(self.update_command)
        
        self.new_check = StyledCheckBox("New Subdomains Only (-new)")
        self.new_check.setToolTip("Only show new subdomains found")
        self.new_check.stateChanged.connect(self.update_command)
        
        options_layout.addWidget(self.silent_check, 0, 0)
        options_layout.addWidget(self.json_check, 0, 1)
        options_layout.addWidget(self.count_check, 1, 0)
        options_layout.addWidget(self.new_check, 1, 1)
        
        control_layout.addWidget(options_group)
        
        # Command Preview
        self.command_input = StyledLineEdit()
        self.command_input.setReadOnly(True)
        self.command_input.setPlaceholderText("Command preview...")
        control_layout.addWidget(self.command_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.run_button = RunButton("RUN CHAOS")
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
        self.output.setPlaceholderText("Chaos results will appear here...")
        splitter.addWidget(self.output)
        splitter.setSizes([400, 450])
        
        main_layout.addWidget(splitter)
        
    def build_command(self, preview: bool = False) -> str:
        cmd = ["chaos"]
        
        target = self.target_input.get_target().strip()
        if target:
            cmd.extend(["-d", target])
        elif preview:
            cmd.extend(["-d", "<domain>"])
        else:
            raise ValueError("Target domain required")
            
        key = self.key_input.text().strip()
        if key:
            cmd.extend(["-key", key])
        elif preview:
            # show placeholder in preview if user hasn't typed one
            pass # cmd.extend(["-key", "<api_key>"]) - user prefers clean preview?
            
        if self.silent_check.isChecked(): cmd.append("-silent")
        if self.json_check.isChecked(): cmd.append("-json")
        if self.count_check.isChecked(): cmd.append("-count")
        if self.new_check.isChecked(): cmd.append("-new")
        
        # Output file handled in execution
        if preview:
            cmd.extend(["-o", "<output_file>"])
            
        return " ".join(shlex.quote(x) for x in cmd)
    
    def update_command(self):
        try:
            cmd_str = self.build_command(preview=True)
            self.command_input.setText(cmd_str)
        except Exception:
            self.command_input.setText("")
            
    def run_scan(self):
        try:
            target = self.target_input.get_target().strip()
            if not target:
                raise ValueError("Target domain required")
                
            base_dir = create_target_dirs(target)
            self.log_file = os.path.join(base_dir, "chaos_results.txt")
            
            # Suppress the default "Results saved to..." message from worker
            self._suppress_result_msg = True
            
            cmd_str = self.build_command(preview=False)
            cmd_str += f" -o {shlex.quote(self.log_file)}"
            
            self._info(f"Starting Chaos for {target}...")
            self._section("CHAOS SCAN")
            self._raw(html.escape(cmd_str))
            
            # Use buffer_output=False to see progress in real-time
            self.start_execution(cmd_str, output_path=self.log_file, buffer_output=False)
            
        except Exception as e:
            self._error(str(e))
            
    def on_execution_finished(self):
        super().on_execution_finished()
        self._section("Scan Completed")
        
        # Read and display results inline
        if self.log_file and os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read().strip()
                
                if content:
                    self._section("Found Subdomains")
                    self._raw(f"<pre>{html.escape(content)}</pre>")
                else:
                    self._info("No subdomains found in output file.")
            except Exception as e:
                self._error(f"Failed to read results file: {e}")
