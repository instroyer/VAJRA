# =============================================================================
# modules/sublist3r.py
#
# Sublist3r - Fast Subdomain Enumeration
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
    ToolSplitter, StyledSpinBox, StyledToolView
)


class Sublist3rTool(ToolBase):
    """
    Sublist3r is a python tool designed to enumerate subdomains of websites using OSINT.
    """
    
    name = "Sublist3r"
    category = ToolCategory.SUBDOMAIN_ENUMERATION
    
    @property
    def icon(self) -> str:
        return "📜"
    
    def get_widget(self, main_window):
        return Sublist3rView(main_window=main_window)


class Sublist3rView(StyledToolView, ToolExecutionMixin):
    """Sublist3r tool interface."""
    
    tool_name = "Sublist3r"
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
        
        # Configuration
        config_group = StyledGroupBox("⚙️ Configuration")
        config_layout = QGridLayout(config_group)
        
        # Threads
        self.threads_spin = StyledSpinBox()
        self.threads_spin.setRange(1, 100)
        self.threads_spin.setValue(30)
        self.threads_spin.valueChanged.connect(self.update_command)
        
        # Engines Input (User Request: "Box if he wants to use another")
        self.engines_input = StyledLineEdit()
        self.engines_input.setPlaceholderText("Engines (e.g. google,bing). Leave empty for ALL.")
        self.engines_input.textChanged.connect(self.update_command)
        
        # Ports
        self.ports_input = StyledLineEdit()
        self.ports_input.setPlaceholderText("Specific ports (e.g. 80,443)")
        self.ports_input.textChanged.connect(self.update_command)
        
        config_layout.addWidget(StyledLabel("Threads (-t):"), 0, 0)
        config_layout.addWidget(self.threads_spin, 0, 1)
        config_layout.addWidget(StyledLabel("Engines (-e):"), 1, 0)
        config_layout.addWidget(self.engines_input, 1, 1)
        config_layout.addWidget(StyledLabel("Ports (-p):"), 2, 0)
        config_layout.addWidget(self.ports_input, 2, 1)
        
        control_layout.addWidget(config_group)
        
        # Options
        options_group = StyledGroupBox("🚀 Options")
        options_layout = QHBoxLayout(options_group)
        
        # Verbose removed as per user request for cleaner output
        self.bruteforce_check = StyledCheckBox("Enable Bruteforce")
        self.bruteforce_check.setToolTip("Enable Subbrute module")
        self.bruteforce_check.stateChanged.connect(self.update_command)
        
        options_layout.addWidget(self.bruteforce_check)
        
        control_layout.addWidget(options_group)
        
        # Command Preview
        self.command_input = StyledLineEdit()
        self.command_input.setReadOnly(True)
        self.command_input.setPlaceholderText("Command preview...")
        control_layout.addWidget(self.command_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.run_button = RunButton("RUN SUBLIST3R")
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
        self.output.setPlaceholderText("Sublist3r results will appear here...")
        splitter.addWidget(self.output)
        splitter.setSizes([400, 450])
        
        main_layout.addWidget(splitter)
        
    def build_command(self, preview: bool = False) -> str:
        # Sublist3r is typically run as 'sublist3r' or 'python sublist3r.py'
        # Assuming 'sublist3r' is in PATH or alias
        cmd = ["sublist3r"]
        
        target = self.target_input.get_target().strip()
        if target:
            cmd.extend(["-d", target])
        elif preview:
            cmd.extend(["-d", "<domain>"])
        else:
            raise ValueError("Target domain required")
            
        if self.threads_spin.value() != 30: # Only add if changed from default
            cmd.extend(["-t", str(self.threads_spin.value())])
            
        engines = self.engines_input.text().strip()
        if engines:
            cmd.extend(["-e", engines])
            
        ports = self.ports_input.text().strip()
        if ports:
            cmd.extend(["-p", ports])
            
        # Verbose flag removed to clean up output (user request)
        if self.bruteforce_check.isChecked(): cmd.append("-b")
        
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
            self.log_file = os.path.join(base_dir, "sublist3r_results.txt")
            
            # Suppress the default "Results saved to..." message from worker
            self._suppress_result_msg = True
            
            cmd_str = self.build_command(preview=False)
            cmd_str += f" -o {shlex.quote(self.log_file)}"
            
            self._info(f"Starting Sublist3r for {target}...")
            self._section("SUBLIST3R SCAN")
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
