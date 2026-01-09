# =============================================================================
# modules/eyewitness.py
#
# Eyewitness - Web Screenshot Capture Tool
# =============================================================================

import os
import shlex
import shutil
import html
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog
)

from modules.bases import ToolBase, ToolCategory
from core.tgtinput import TargetInput
from core.fileops import create_target_dirs, RESULT_BASE
from ui.worker import ToolExecutionMixin
from ui.styles import (
    # Widgets
    RunButton, StopButton, BrowseButton,
    StyledLineEdit, StyledSpinBox, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView,
    ToolSplitter, ConfigTabs, CopyButton, StyledToolView
)


class EyewitnessTool(ToolBase):
    """Eyewitness tool plugin."""
    
    name = "Eyewitness"
    category = ToolCategory.WEB_SCREENSHOTS

    @property
    def icon(self) -> str:
        return "📸"

    def get_widget(self, main_window):
        return EyewitnessView(main_window=main_window)


class EyewitnessView(StyledToolView, ToolExecutionMixin):
    """Eyewitness web screenshot tool interface."""
    
    tool_name = "Eyewitness"
    tool_category = "WEB_SCREENSHOTS"
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.output_dir = None
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
        # Removed legacy background style
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
        self.threads_spin.setValue(50)
        self.threads_spin.valueChanged.connect(self.update_command)
        
        self.timeout_spin = StyledSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" s")
        self.timeout_spin.valueChanged.connect(self.update_command)
        
        self.delay_spin = StyledSpinBox()
        self.delay_spin.setRange(0, 60)
        self.delay_spin.setValue(0)
        self.delay_spin.setSuffix(" s")
        self.delay_spin.valueChanged.connect(self.update_command)
        
        config_layout.addWidget(StyledLabel("Threads:"), 0, 0)
        config_layout.addWidget(self.threads_spin, 0, 1)
        config_layout.addWidget(StyledLabel("Timeout:"), 0, 2)
        config_layout.addWidget(self.timeout_spin, 0, 3)
        config_layout.addWidget(StyledLabel("Delay:"), 1, 0)
        config_layout.addWidget(self.delay_spin, 1, 1)
        
        control_layout.addWidget(config_group)
        
        # Options
        options_group = StyledGroupBox("🚀 Options")
        options_layout = QGridLayout(options_group)
        
        self.prepend_https_check = StyledCheckBox("Prepend HTTPS")
        self.prepend_https_check.stateChanged.connect(self.update_command)
        
        self.no_dns_check = StyledCheckBox("No DNS")
        self.no_dns_check.stateChanged.connect(self.update_command)
        
        self.ua_input = StyledLineEdit()
        self.ua_input.setPlaceholderText("User Agent (optional)...")
        self.ua_input.textChanged.connect(self.update_command)
        
        self.proxy_input = StyledLineEdit()
        self.proxy_input.setPlaceholderText("ip:port")
        self.proxy_input.textChanged.connect(self.update_command)
        
        options_layout.addWidget(self.prepend_https_check, 0, 0)
        options_layout.addWidget(self.no_dns_check, 0, 1)
        options_layout.addWidget(StyledLabel("User Agent:"), 1, 0)
        options_layout.addWidget(self.ua_input, 1, 1)
        options_layout.addWidget(StyledLabel("Proxy (IP:Port):"), 2, 0)
        options_layout.addWidget(self.proxy_input, 2, 1)
        
        control_layout.addWidget(options_group)

        # Command Preview
        self.command_input = StyledLineEdit()
        self.command_input.setReadOnly(True)
        self.command_input.setPlaceholderText("Command preview...")
        control_layout.addWidget(self.command_input)

        # Buttons
        btn_layout = QHBoxLayout()
        self.run_button = RunButton("CAPTURE")
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
        self.output.setPlaceholderText("Eyewitness logs will appear here...")
        
        splitter.addWidget(self.output)
        splitter.setSizes([450, 450])
        
        main_layout.addWidget(splitter)
        
    # -------------------------------------------------------------------------
    # Command Builder
    # -------------------------------------------------------------------------

    def build_command(self, preview: bool = False) -> str:
        cmd = ["eyewitness", "--web"]
        
        target = self.target_input.get_target().strip()
        if target:
            if os.path.isfile(target):
                cmd.extend(["-f", target])
            else:
                 # Standardize single target
                 clean_target = target
                 if "://" not in clean_target and not self.prepend_https_check.isChecked() and not preview:
                      clean_target = f"https://{clean_target}" # Eyewitness usually likes protocol or prepend flag
                 cmd.extend(["--single", clean_target])
        elif preview:
             cmd.extend(["--single", "<target>"])
        else:
             raise ValueError("Target required")
             
        if self.threads_spin.value() != 50:
            cmd.extend(["--threads", str(self.threads_spin.value())])
            
        if self.timeout_spin.value() != 30:
            cmd.extend(["--timeout", str(self.timeout_spin.value())])
            
        if self.delay_spin.value() > 0:
            cmd.extend(["--delay", str(self.delay_spin.value())])
            
        if self.prepend_https_check.isChecked(): cmd.append("--prepend-https")
        if self.no_dns_check.isChecked(): cmd.append("--no-dns")
        
        ua = self.ua_input.text().strip()
        if ua:
            cmd.extend(["--user-agent", ua])
            
        proxy = self.proxy_input.text().strip()
        if proxy and ":" in proxy:
            parts = proxy.split(":")
            if len(parts) == 2:
                cmd.extend(["--proxy-ip", parts[0], "--proxy-port", parts[1]])
        
        cmd.append("--no-prompt")
        
        # Output dir handled in run_scan
        if preview:
            cmd.extend(["-d", "<output_dir>"])
            
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
                raise ValueError("Target required")
            
            # Determine directory name
            if os.path.isfile(target):
                base_name = os.path.splitext(os.path.basename(target))[0]
            else:
                base_name = target.replace('https://', '').replace('http://', '').replace('/', '_')

            timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
            self.output_dir = os.path.join(RESULT_BASE, f"eyewitness_{base_name}_{timestamp}")
            
            # Cleanup previous if exists (unlikely with timestamp)
            if os.path.exists(self.output_dir):
                shutil.rmtree(self.output_dir)
            
            # Eyewitness creates the directory itself, but safe to make base
            os.makedirs(RESULT_BASE, exist_ok=True)
            
            cmd_str = self.build_command(preview=False)
            cmd_str += f" -d {shlex.quote(self.output_dir)}"
            
            # Remove old geckodriver.log
            if os.path.exists("geckodriver.log"):
                try: os.remove("geckodriver.log")
                except: pass
            
            self._info(f"Results will be saved to: {self.output_dir}")
            self.start_execution(cmd_str, output_path=self.output_dir)
            
        except Exception as e:
            self._error(str(e))

    def on_execution_finished(self):
        super().on_execution_finished()
        
        if self.output_dir and os.path.exists(self.output_dir):
             self._info(f"Report available in: {self.output_dir}")
             self._notify("Eyewitness capture complete.")
             
        # Cleanup log again
        if os.path.exists("geckodriver.log"):
            try: os.remove("geckodriver.log")
            except: pass

    def on_new_output(self, line):
        clean = line.strip()
        if not clean: return
        self._raw(html.escape(clean))

