# =============================================================================
# modules/wafw00f.py
#
# WAFW00F - Web Application Firewall Detection Tool
# =============================================================================

import os
import shlex
import random
import socket
import http.client
import time
import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
)
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from core.fileops import create_target_dirs
from ui.worker import ToolExecutionMixin
from ui.styles import (
    # Widgets
    RunButton, StopButton,
    StyledLineEdit, StyledSpinBox, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView,
    ToolSplitter, StyledToolView
)

# =============================================================================
# Smart WAF Detection Engine (Preserved for compatibility)
# =============================================================================

class SmartWAFDetector:
    """Smart WAF detection engine stub."""
    def __init__(self, host, port=None, timeout=5.0):
        self.host = host.strip()
        self.port = port
        self.timeout = timeout
        self.ip = None

    def resolve(self):
        try:
            self.ip = socket.gethostbyname(self.host)
            return self.ip
        except socket.gaierror:
            return None
            
    def detect(self, use_payloads=True):
        return {"error": "Use the GUI tool for detection", "waf": None}


# =============================================================================
# GUI Tool Definition
# =============================================================================

class WAFW00FTool(ToolBase):
    """WAFW00F WAF detection tool plugin."""

    name = "WAFW00F"
    category = ToolCategory.INFO_GATHERING
    
    @property
    def icon(self) -> str:
        return "🛡️"

    def get_widget(self, main_window):
        return WAFW00FToolView(main_window=main_window)


class WAFW00FToolView(StyledToolView, ToolExecutionMixin):
    """WAFW00F WAF detection interface."""
    
    tool_name = "WAFW00F"
    tool_category = "INFO_GATHERING"

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.log_file = None
        self._build_ui()
        self.update_command()

    def _build_ui(self):
        """Build complete UI."""
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

        # Target Row
        target_group = StyledGroupBox("🎯 Target")
        target_layout = QHBoxLayout(target_group)
        
        self.target_input = StyledLineEdit()
        self.target_input.setPlaceholderText("https://example.com")
        self.target_input.textChanged.connect(self.update_command)
        
        target_layout.addWidget(self.target_input)
        control_layout.addWidget(target_group)
        
        # Options
        options_group = StyledGroupBox("⚙️ Options")
        options_layout = QGridLayout(options_group)
        
        self.mode_combo = StyledComboBox()
        self.mode_combo.addItems(["Standard", "Aggressive (-a)", "Fingerprint All (-f)"])
        self.mode_combo.currentTextChanged.connect(self.update_command)
        
        self.proxy_input = StyledLineEdit()
        self.proxy_input.setPlaceholderText("http://localhost:8080")
        self.proxy_input.textChanged.connect(self.update_command)
        
        self.timeout_spin = StyledSpinBox()
        self.timeout_spin.setRange(1, 60)
        self.timeout_spin.setValue(10)
        self.timeout_spin.setSuffix(" s")
        self.timeout_spin.valueChanged.connect(self.update_command)
        
        self.list_wafs_check = StyledCheckBox("List WAFs (-l)")
        self.list_wafs_check.stateChanged.connect(self.update_command)
        
        self.no_redirect_check = StyledCheckBox("No Redirects (-r)")
        self.no_redirect_check.stateChanged.connect(self.update_command)
        
        options_layout.addWidget(StyledLabel("Mode:"), 0, 0)
        options_layout.addWidget(self.mode_combo, 0, 1)
        options_layout.addWidget(StyledLabel("Proxy:"), 1, 0)
        options_layout.addWidget(self.proxy_input, 1, 1)
        options_layout.addWidget(StyledLabel("Timeout:"), 2, 0)
        options_layout.addWidget(self.timeout_spin, 2, 1)
        options_layout.addWidget(self.list_wafs_check, 3, 0)
        options_layout.addWidget(self.no_redirect_check, 3, 1)
        
        control_layout.addWidget(options_group)

        # Command Preview
        self.command_input = StyledLineEdit()
        self.command_input.setReadOnly(True)
        self.command_input.setPlaceholderText("Command preview...")
        control_layout.addWidget(self.command_input)

        # Buttons
        btn_layout = QHBoxLayout()
        self.run_button = RunButton("DETECT WAF")
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
        self.output.setPlaceholderText("Detection results will appear here...")
        
        splitter.addWidget(self.output)
        splitter.setSizes([400, 450])
        
        main_layout.addWidget(splitter)
        
    # -------------------------------------------------------------------------
    # Command Builder
    # -------------------------------------------------------------------------

    def build_command(self, preview: bool = False) -> str:
        cmd = ["wafw00f"]
        
        if self.list_wafs_check.isChecked():
            cmd.append("-l")
            return " ".join(cmd)
            
        mode = self.mode_combo.currentText()
        if "Aggressive" in mode:
            cmd.append("-a")
        elif "Fingerprint" in mode:
            cmd.append("-f")
            
        proxy = self.proxy_input.text().strip()
        if proxy:
            cmd.extend(["-p", proxy])
            
        if self.timeout_spin.value() != 10:
            cmd.extend(["-t", str(self.timeout_spin.value())])
            
        if self.no_redirect_check.isChecked(): cmd.append("-r")
        
        target = self.target_input.text().strip()
        if target:
            cmd.append(target)
        elif preview:
             cmd.append("<target>")
        else:
             raise ValueError("Target URL required")
             
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
            cmd_str = self.build_command(preview=False)
            
            # Prepare logging if there is a target
            target = self.target_input.text().strip()
            if target and not self.list_wafs_check.isChecked():
                try:
                    temp = target
                    if "://" in temp: temp = temp.split("://", 1)[1]
                    target_name = temp.split("/")[0].split(":")[0]
                    base_dir = create_target_dirs(target_name, None)
                    self.log_file = os.path.join(base_dir, "Logs", f"wafw00f_{int(time.time())}.txt")
                    cmd_str += f" -o {shlex.quote(self.log_file)}"
                except:
                    pass
            
            self._info(f"Starting WAFW00F...")
            self._section("WAF DETECTION")
            self._section("Command")
            self._raw(html.escape(cmd_str))
            self._raw("")
            
            self.start_execution(cmd_str, output_path=self.log_file, buffer_output=False)
            
        except Exception as e:
            self._error(str(e))

    def on_execution_finished(self):
        super().on_execution_finished()
        self._section("Scan Completed")


    def on_new_output(self, line):
        # We use rstrip to preserve leading whitespace (indentation) but remove newline
        clean = line.rstrip()
        
        clean = self.strip_ansi(clean)
        safe_line = html.escape(clean)
        
        # Base style for terminal emulation
        base_style = "white-space: pre-wrap; font-family: monospace; display: block;"
        
        if not safe_line:
            self._raw("<br>")
            return
            
        lower = clean.lower()
        
        if "is behind" in lower or "waf detected" in lower:
             self._raw(f'<span style="{base_style} color:#10B981; font-weight:bold;">{safe_line}</span>')
        elif "no waf" in lower or "not behind" in lower:
             self._raw(f'<span style="{base_style} color:#FACC15;">{safe_line}</span>')
        else:
             self._raw(f'<span style="{base_style}">{safe_line}</span>')
