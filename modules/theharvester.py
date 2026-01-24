# =============================================================================
# modules/theharvester.py
#
# theHarvester - OSINT Intelligence Gathering
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
    ToolSplitter, StyledSpinBox, StyledComboBox, StyledToolView
)


class TheHarvesterTool(ToolBase):
    """
    theHarvester is a simple to use, yet powerful tool designed to be used in the early 
    stages of a penetration test or red team engagement.
    """
    
    name = "theHarvester"
    category = ToolCategory.SUBDOMAIN_ENUMERATION
    
    @property
    def icon(self) -> str:
        return "🌾"
    
    def get_widget(self, main_window):
        return TheHarvesterView(main_window=main_window)


class TheHarvesterView(StyledToolView, ToolExecutionMixin):
    """theHarvester tool interface."""
    
    tool_name = "theHarvester"
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
        
        # Source Selection (User Request: "Box if he wants to use another")
        # We use a ComboBox that is editable, pre-filled with common options but allows typing
        self.source_combo = StyledComboBox()
        self.source_combo.setEditable(True) 
        self.source_combo.addItems([
            "all", "google", "bing", "yahoo", "linkedin", "twitter", 
            "crtsh", "virustotal", "shodan", "netlas", "duckduckgo",
            "baidu", "dnsdumpster", "hunter", "securitytrails"
        ])
        self.source_combo.setCurrentText("all")
        self.source_combo.currentTextChanged.connect(self.update_command)
        self.source_combo.setToolTip("Select or type data sources (comma separated)")
        
        # Limit
        self.limit_spin = StyledSpinBox()
        self.limit_spin.setRange(10, 10000)
        self.limit_spin.setValue(500)
        self.limit_spin.valueChanged.connect(self.update_command)
        
        config_layout.addWidget(StyledLabel("Data Source (-b):"), 0, 0)
        config_layout.addWidget(self.source_combo, 0, 1)
        config_layout.addWidget(StyledLabel("Limit Results (-l):"), 1, 0)
        config_layout.addWidget(self.limit_spin, 1, 1)
        
        control_layout.addWidget(config_group)
        
        # Active Recon
        active_group = StyledGroupBox("🔥 Active Recon")
        active_layout = QVBoxLayout(active_group)
        
        self.dns_brute = StyledCheckBox("DNS Brute Force (-c)")
        self.dns_brute.setToolTip("Perform DNS brute force on domain")
        self.dns_brute.stateChanged.connect(self.update_command)
        
        self.dns_resolve = StyledCheckBox("DNS Resolve (-r)")
        self.dns_resolve.setToolTip("Perform DNS resolution on subdomains")
        self.dns_resolve.stateChanged.connect(self.update_command)
        
        self.screenshot = StyledCheckBox("Take Screenshots (--screenshot)")
        self.screenshot.stateChanged.connect(self.update_command)
        
        # Checkbox Row
        row1 = QHBoxLayout()
        row1.addWidget(self.dns_brute)
        row1.addWidget(self.dns_resolve)
        active_layout.addLayout(row1)
        active_layout.addWidget(self.screenshot)
        
        control_layout.addWidget(active_group)
         
        # Options
        options_group = StyledGroupBox("🚀 Options")
        options_layout = QHBoxLayout(options_group)
        
        options_layout.addWidget(StyledLabel("(Requires API keys configured in ~/.theHarvester/api-keys.yaml for some sources)"))
        
        control_layout.addWidget(options_group)

        # Command Preview
        self.command_input = StyledLineEdit()
        self.command_input.setReadOnly(True)
        self.command_input.setPlaceholderText("Command preview...")
        control_layout.addWidget(self.command_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.run_button = RunButton("RUN THEHARVESTER")
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
        self.output.setPlaceholderText("theHarvester results will appear here...")
        splitter.addWidget(self.output)
        splitter.setSizes([450, 450])
        
        main_layout.addWidget(splitter)
        
    def build_command(self, preview: bool = False) -> str:
        cmd = ["theHarvester"]
        
        target = self.target_input.get_target().strip()
        if target:
            cmd.extend(["-d", target])
        elif preview:
            cmd.extend(["-d", "<domain>"])
        else:
            raise ValueError("Target domain required")
            
        source = self.source_combo.currentText().strip()
        if source:
            cmd.extend(["-b", source])
            
        cmd.extend(["-l", str(self.limit_spin.value())])
            
        if self.dns_brute.isChecked(): cmd.append("-c")
        if self.dns_resolve.isChecked(): cmd.append("-r")
        if self.screenshot.isChecked(): 
            cmd.append("--screenshot")
            # Usually requires a directory, but in some versions it uses output dir.
            # We'll let it use default or handle logic if needed. 
            # If using output dir, we might need to specify it.
            # For now, flag is sufficient for command preview.
            if not preview and self.log_file:
                 pass # Screenshots usually save to CWD or specified, we run in CWD / logs
            
        # Verbose removed per user request
        
        # Output file handled in execution
        if preview:
            cmd.extend(["-f", "<output_file>"])
            
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
            # theHarvester appends extensions automatically often, but we specify base
            self.log_file = os.path.join(base_dir, "theharvester_results") 
            
            cmd_str = self.build_command(preview=False)
            cmd_str += f" -f {shlex.quote(self.log_file)}"
            
            self._info(f"Starting theHarvester for {target}...")
            self._section("THEHARVESTER SCAN")
            self._raw(html.escape(cmd_str))
            self._raw("")
            
            self.start_execution(cmd_str) # output displayed via stdout usually
            
        except Exception as e:
            self._error(str(e))
