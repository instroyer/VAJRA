# =============================================================================
# modules/amass.py
#
# Amass - In-depth Attack Surface Mapping and Asset Discovery
# =============================================================================

import os
import shlex
import html
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog, QWidget
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
    ToolSplitter, StyledToolView
)


class AmassTool(ToolBase):
    """Amass tool plugin."""
    
    name = "Amass"
    category = ToolCategory.SUBDOMAIN_ENUMERATION
    
    @property
    def icon(self) -> str:
        return "🌐"
    
    def get_widget(self, main_window):
        return AmassView(main_window=main_window)


class AmassView(StyledToolView, ToolExecutionMixin):
    """Amass attack surface mapping tool interface."""
    
    tool_name = "Amass"
    tool_category = "SUBDOMAIN_ENUMERATION"
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_safe_stop()
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
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)
        
        # Header
        header = HeaderLabel(self.tool_category, self.tool_name)
        control_layout.addWidget(header)
        
        # Target Input
        target_group = StyledGroupBox("Target")
        target_layout = QHBoxLayout(target_group)
        
        self.target_input = TargetInput()
        self.target_input.input_box.textChanged.connect(self.update_command)
        target_layout.addWidget(self.target_input)
        
        control_layout.addWidget(target_group)
        
        # Configuration
        config_group = StyledGroupBox("⚙️ Configuration")
        config_layout = QGridLayout(config_group)
        
        self.mode_combo = StyledComboBox()
        self.mode_combo.addItems(["enum", "intel"])
        self.mode_combo.setCurrentText("enum")
        self.mode_combo.currentTextChanged.connect(self.update_command)
        
        self.timeout_spin = StyledSpinBox()
        self.timeout_spin.setRange(0, 1440)
        self.timeout_spin.setValue(0)
        self.timeout_spin.setSuffix(" min")
        self.timeout_spin.valueChanged.connect(self.update_command)
        
        self.config_input = StyledLineEdit()
        self.config_input.setPlaceholderText("Config file (optional)...")
        self.config_input.textChanged.connect(self.update_command)
        
        browse_config = BrowseButton()
        browse_config.clicked.connect(self._browse_config)
        
        config_layout.addWidget(StyledLabel("Mode:"), 0, 0)
        config_layout.addWidget(self.mode_combo, 0, 1)
        config_layout.addWidget(StyledLabel("Timeout:"), 0, 2)
        config_layout.addWidget(self.timeout_spin, 0, 3)
        config_layout.addWidget(StyledLabel("Config:"), 1, 0)
        config_layout.addWidget(self.config_input, 1, 1, 1, 2)
        config_layout.addWidget(browse_config, 1, 3)
        
        control_layout.addWidget(config_group)
        
        # Options
        options_group = StyledGroupBox("🚀 Options")
        options_layout = QGridLayout(options_group)
        
        self.passive_check = StyledCheckBox("Passive (-passive)")
        self.passive_check.stateChanged.connect(self.update_command)
        
        self.active_check = StyledCheckBox("Active (-active)")
        self.active_check.stateChanged.connect(self.update_command)
        
        self.brute_check = StyledCheckBox("Brute Force (-brute)")
        self.brute_check.stateChanged.connect(self.update_command)
        
        self.ips_check = StyledCheckBox("Show IPs (-ip)")
        self.ips_check.stateChanged.connect(self.update_command)
        
        self.src_check = StyledCheckBox("Show Sources (-src)")
        self.src_check.stateChanged.connect(self.update_command)
        
        options_layout.addWidget(self.passive_check, 0, 0)
        options_layout.addWidget(self.active_check, 0, 1)
        options_layout.addWidget(self.brute_check, 0, 2)
        options_layout.addWidget(self.ips_check, 1, 0)
        options_layout.addWidget(self.src_check, 1, 1)
        
        control_layout.addWidget(options_group)

        # Command Preview
        self.command_input = StyledLineEdit()
        self.command_input.setReadOnly(True)
        self.command_input.setPlaceholderText("Command preview...")
        control_layout.addWidget(self.command_input)

        # Buttons
        btn_layout = QHBoxLayout()
        self.run_button = RunButton("RUN AMASS")
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
        self.output.setPlaceholderText("Amass discovery results will appear here...")
        
        splitter.addWidget(self.output)
        splitter.setSizes([450, 450])
        
        main_layout.addWidget(splitter)
        
    def _browse_config(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Config File")
        if f: self.config_input.setText(f)
        


    # -------------------------------------------------------------------------
    # Command Builder
    # -------------------------------------------------------------------------

    def build_command(self, preview: bool = False) -> str:
        mode = self.mode_combo.currentText()
        cmd = ["amass", mode]
        
        target = self.target_input.get_target().strip()
        if target:
            cmd.extend(["-d", target])
        elif preview:
             cmd.extend(["-d", "<domain>"])
        else:
             raise ValueError("Target domain required")
             
        if self.passive_check.isChecked(): cmd.append("-passive")
        if self.active_check.isChecked(): cmd.append("-active")
        if self.brute_check.isChecked(): cmd.append("-brute")
        if self.ips_check.isChecked(): cmd.append("-ip")
        if self.src_check.isChecked(): cmd.append("-src")
        
        if self.timeout_spin.value() > 0:
            cmd.extend(["-timeout", str(self.timeout_spin.value())])
            
        cfg = self.config_input.text().strip()
        if cfg:
             cmd.extend(["-config", cfg])
             
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
            target = self.target_input.get_target().strip()
            if not target:
                raise ValueError("Target domain required")
                
            base_dir = create_target_dirs(target)
            self.log_file = os.path.join(base_dir, "amass_results.txt")
            
            cmd_str = self.build_command(preview=False)
            cmd_str += f" -o {shlex.quote(self.log_file)}"
            
            # Start Execution (Mixin)
            self.start_execution(cmd_str, self.log_file)
            
            self._info(f"Starting Amass ({self.mode_combo.currentText()})...")
            self._section("AMASS SCAN")
            
        except Exception as e:
            self._error(str(e))

    def on_execution_finished(self):
        super().on_execution_finished()
        self.worker = None
        if self.main_window:
             self.main_window.active_process = None
        
        # Additional result verification could go here
        if self.log_file and os.path.exists(self.log_file):
             pass

    def on_new_output(self, line):
        clean = line.strip()
        if not clean: return
        
        # Filter noise
        if "address_parser" in clean or "libpostal" in clean: return
        if "dir=(null)" in clean: return
        if "Could not find parser model" in clean: return
        
        self._raw(html.escape(clean))
