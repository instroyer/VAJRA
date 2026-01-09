# =============================================================================
# modules/subfinder.py
#
# Subfinder - Subdomain Discovery Tool
# =============================================================================

import os
import shlex
import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog
)

from modules.bases import ToolBase, ToolCategory
from core.tgtinput import TargetInput
from core.fileops import create_target_dirs
from ui.worker import ToolExecutionMixin
from ui.styles import (
    # Widgets
    RunButton, StopButton, BrowseButton,
    StyledLineEdit, StyledSpinBox, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView,
    ToolSplitter, ConfigTabs, CopyButton, StyledToolView
)


class SubfinderTool(ToolBase):
    """Subfinder tool plugin."""
    
    name = "Subfinder"
    category = ToolCategory.SUBDOMAIN_ENUMERATION
    
    @property
    def icon(self) -> str:
        return "🔍"
    
    def get_widget(self, main_window):
        return SubfinderView(main_window=main_window)


class SubfinderView(StyledToolView, ToolExecutionMixin):
    """Subfinder subdomain discovery tool interface."""
    
    tool_name = "Subfinder"
    tool_category = "SUBDOMAIN_ENUMERATION"
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.log_file = None
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
        # Removed legacy background
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
        
        self.threads_spin = StyledSpinBox()
        self.threads_spin.setRange(1, 1000)
        self.threads_spin.setValue(10)
        self.threads_spin.valueChanged.connect(self.update_command)
        
        self.config_input = StyledLineEdit()
        self.config_input.setPlaceholderText("Config file (optional)...")
        self.config_input.textChanged.connect(self.update_command)
        
        browse_config = BrowseButton()
        browse_config.clicked.connect(self._browse_config)
        
        config_layout.addWidget(StyledLabel("Threads (-t):"), 0, 0)
        config_layout.addWidget(self.threads_spin, 0, 1)
        config_layout.addWidget(StyledLabel("Config:"), 1, 0)
        config_layout.addWidget(self.config_input, 1, 1, 1, 2)
        config_layout.addWidget(browse_config, 1, 3)
        
        control_layout.addWidget(config_group)
        
        # Options
        options_group = StyledGroupBox("🚀 Options")
        options_layout = QHBoxLayout(options_group)
        
        self.recursive_check = StyledCheckBox("Recursive (-recursive)")
        self.recursive_check.stateChanged.connect(self.update_command)
        
        self.all_check = StyledCheckBox("All Sources (-all)")
        self.all_check.stateChanged.connect(self.update_command)
        
        self.silent_check = StyledCheckBox("Silent (-silent)")
        self.silent_check.stateChanged.connect(self.update_command)
        
        options_layout.addWidget(self.recursive_check)
        options_layout.addWidget(self.all_check)
        options_layout.addWidget(self.silent_check)
        
        control_layout.addWidget(options_group)

        # Command Preview
        self.command_input = StyledLineEdit()
        self.command_input.setReadOnly(True)
        self.command_input.setPlaceholderText("Command preview...")
        control_layout.addWidget(self.command_input)

        # Buttons
        btn_layout = QHBoxLayout()
        self.run_button = RunButton("RUN SUBFINDER")
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
        self.output.setPlaceholderText("Subdomain discovery results will appear here...")
        
        splitter.addWidget(self.output)
        splitter.setSizes([400, 450])
        
        main_layout.addWidget(splitter)
        
    def _browse_config(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Config File")
        if f: self.config_input.setText(f)
        
    # -------------------------------------------------------------------------
    # Command Builder
    # -------------------------------------------------------------------------

    def build_command(self, preview: bool = False) -> str:
        cmd = ["subfinder"]
        
        target = self.target_input.get_target().strip()
        if target:
            cmd.extend(["-d", target])
        elif preview:
             cmd.extend(["-d", "<domain>"])
        else:
             raise ValueError("Target domain required")
             
        if self.threads_spin.value() != 10:
            cmd.extend(["-t", str(self.threads_spin.value())])
            
        if self.recursive_check.isChecked(): cmd.append("-recursive")
        if self.all_check.isChecked(): cmd.append("-all")
        if self.silent_check.isChecked(): cmd.append("-silent")

        cfg = self.config_input.text().strip()
        if cfg:
             cmd.extend(["-config", cfg])
             
        # Output file handled in run_scan
        if preview:
            cmd.extend(["-o", "<output_file>"])
            
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
        try:
            # Prepare output directory
            target = self.target_input.get_target().strip()
            if not target:
                raise ValueError("Target domain required")
                
            base_dir = create_target_dirs(target)
            self.log_file = os.path.join(base_dir, "subfinder_results.txt")
            
            cmd_str = self.build_command(preview=False)
            cmd_str += f" -o {shlex.quote(self.log_file)}"
            
            self._info(f"Starting Subfinder...")
            self._section("SUBFINDER SCAN")
            self._section("Command")
            self._raw(html.escape(cmd_str))
            self._raw("")
            
            self.start_execution(cmd_str, output_path=self.log_file)
            
        except Exception as e:
            self._error(str(e))

    def on_execution_finished(self):
        super().on_execution_finished()
        self._section("Scan Completed")


    def on_new_output(self, line):
        clean = line.strip()
        if not clean: return
        clean = self.strip_ansi(clean)
        self._raw(html.escape(clean))
