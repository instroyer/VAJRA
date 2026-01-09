# =============================================================================
# modules/hydra.py
#
# Hydra - Network Logon Cracker
# =============================================================================

import os
import shlex
import re
import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from ui.worker import ToolExecutionMixin
from core.fileops import create_target_dirs
from ui.styles import (
    # Widgets
    RunButton, StopButton, BrowseButton,
    StyledLineEdit, StyledSpinBox, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView,
    ToolSplitter, ConfigTabs, StyledToolView,
    # Behaviors
)


class HydraTool(ToolBase):
    """Hydra brute force attack tool."""

    name = "Hydra"
    category = ToolCategory.CRACKER

    @property
    def description(self) -> str:
        return "Parallelized login cracker which supports numerous protocols."

    @property
    def icon(self) -> str:
        return "🐉"

    def get_widget(self, main_window):
        return HydraToolView(main_window=main_window)


class HydraToolView(StyledToolView, ToolExecutionMixin):
    """Hydra brute force attack interface."""
    
    tool_name = "Hydra"
    tool_category = "CRACKER"

    def __init__(self, main_window=None):
        super().__init__()
        self.init_safe_stop()
        self.main_window = main_window
        self.base_dir = None
        
        self.service_ports = {
            "ssh": 22, "ftp": 21, "telnet": 23, "smtp": 25, "pop3": 110,
            "imap": 143, "smb": 445, "rdp": 3389, "vnc": 5900, "mysql": 3306,
            "postgresql": 5432, "http-get": 80, "http-post-form": 80, "https-get": 443
        }
        
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
        control_layout.setContentsMargins(15, 15, 15, 15)
        control_layout.setSpacing(15)

        # Header
        header = HeaderLabel(self.tool_category, self.tool_name)
        control_layout.addWidget(header)

        # --- Target Section ---
        target_group = StyledGroupBox("🎯 Target")
        target_layout = QGridLayout(target_group)
        target_layout.setVerticalSpacing(10)
        target_layout.setHorizontalSpacing(10)
        
        # Row 1: Host
        target_layout.addWidget(StyledLabel("Target IP/Host:"), 0, 0)
        self.host_input = StyledLineEdit()
        self.host_input.setPlaceholderText("192.168.1.10")
        self.host_input.textChanged.connect(self.update_command)
        target_layout.addWidget(self.host_input, 0, 1, 1, 3) # Span 3 cols
        
        # Row 2: Service & Port
        target_layout.addWidget(StyledLabel("Service:"), 1, 0)
        self.service_combo = StyledComboBox()
        self.service_combo.addItems(sorted(self.service_ports.keys()))
        self.service_combo.setCurrentText("ssh")
        self.service_combo.currentTextChanged.connect(self._on_service_change)
        target_layout.addWidget(self.service_combo, 1, 1)
        
        target_layout.addWidget(StyledLabel("Port (-s):"), 1, 2)
        self.port_spin = StyledSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(22)
        self.port_spin.valueChanged.connect(self.update_command)
        target_layout.addWidget(self.port_spin, 1, 3)
        
        # Column stretch
        target_layout.setColumnStretch(1, 1)
        target_layout.setColumnStretch(3, 1)
        
        control_layout.addWidget(target_group)

        # --- Credentials Section ---
        creds_group = StyledGroupBox("🔐 Credentials")
        creds_layout = QGridLayout(creds_group)
        creds_layout.setVerticalSpacing(10)
        creds_layout.setHorizontalSpacing(10)
        
        # Row 1: Username
        creds_layout.addWidget(StyledLabel("Username:"), 0, 0)
        
        # Radio buttons container
        user_radio_layout = QHBoxLayout()
        self.user_single_radio = QRadioButton("Single")
        self.user_list_radio = QRadioButton("List")
        self.user_list_radio.setChecked(True)
        self.user_single_radio.toggled.connect(self._toggle_user_mode)
        
        self.user_groups = QButtonGroup(self)
        self.user_groups.addButton(self.user_single_radio)
        self.user_groups.addButton(self.user_list_radio)
        
        user_radio_layout.addWidget(self.user_single_radio)
        user_radio_layout.addWidget(self.user_list_radio)
        user_radio_layout.addStretch()
        
        creds_layout.addLayout(user_radio_layout, 0, 1)
        
        # Input row
        self.username_input = StyledLineEdit() 
        self.username_input.setPlaceholderText("Select username list...")
        self.username_input.textChanged.connect(self.update_command)
        creds_layout.addWidget(self.username_input, 0, 2)
        
        self.user_browse = BrowseButton()
        self.user_browse.clicked.connect(self._browse_user)
        creds_layout.addWidget(self.user_browse, 0, 3)

        # Row 2: Password
        creds_layout.addWidget(StyledLabel("Password:"), 1, 0)
        
        pass_radio_layout = QHBoxLayout()
        self.pass_single_radio = QRadioButton("Single")
        self.pass_list_radio = QRadioButton("List")
        self.pass_list_radio.setChecked(True)
        self.pass_single_radio.toggled.connect(self._toggle_pass_mode)
        
        self.pass_groups = QButtonGroup(self)
        self.pass_groups.addButton(self.pass_single_radio)
        self.pass_groups.addButton(self.pass_list_radio)
        
        pass_radio_layout.addWidget(self.pass_single_radio)
        pass_radio_layout.addWidget(self.pass_list_radio)
        pass_radio_layout.addStretch()
        
        creds_layout.addLayout(pass_radio_layout, 1, 1)
        
        self.password_input = StyledLineEdit()
        self.password_input.setPlaceholderText("Select password list...")
        self.password_input.textChanged.connect(self.update_command)
        creds_layout.addWidget(self.password_input, 1, 2)
        
        self.pass_browse = BrowseButton()
        self.pass_browse.clicked.connect(self._browse_pass)
        creds_layout.addWidget(self.pass_browse, 1, 3)
        
        # Stretch factors
        creds_layout.setColumnStretch(2, 1)

        control_layout.addWidget(creds_group)

        # --- Options Section ---
        options_group = StyledGroupBox("⚙️ Options")
        options_layout = QGridLayout(options_group)
        options_layout.setVerticalSpacing(10)
        options_layout.setHorizontalSpacing(15)
        
        options_layout.addWidget(StyledLabel("Tasks (-t):"), 0, 0)
        self.tasks_spin = StyledSpinBox()
        self.tasks_spin.setRange(1, 64)
        self.tasks_spin.setValue(16)
        self.tasks_spin.valueChanged.connect(self.update_command)
        options_layout.addWidget(self.tasks_spin, 0, 1)
        
        options_layout.addWidget(StyledLabel("Wait (-w):"), 0, 2)
        self.wait_spin = StyledSpinBox()
        self.wait_spin.setRange(0, 300)
        self.wait_spin.setValue(0)
        self.wait_spin.setSuffix(" s")
        self.wait_spin.valueChanged.connect(self.update_command)
        options_layout.addWidget(self.wait_spin, 0, 3)
        
        # Checkboxes
        self.exit_check = StyledCheckBox("Exit on Found (-f)")
        self.exit_check.setChecked(True)
        self.exit_check.stateChanged.connect(self.update_command)
        
        self.verbose_check = StyledCheckBox("Verbose (-V)")
        self.verbose_check.stateChanged.connect(self.update_command)
        
        self.ssl_check = StyledCheckBox("Use SSL (-S)")
        self.ssl_check.stateChanged.connect(self.update_command)
        
        options_layout.addWidget(self.exit_check, 1, 0, 1, 2)
        options_layout.addWidget(self.verbose_check, 1, 2)
        options_layout.addWidget(self.ssl_check, 1, 3)
        
        options_layout.setColumnStretch(1, 1)
        options_layout.setColumnStretch(3, 1)
        
        control_layout.addWidget(options_group)

        # Buttons
        btn_layout = QHBoxLayout()
        self.run_button = RunButton("RUN HYDRA")
        self.run_button.clicked.connect(self.run_scan)
        self.stop_button = StopButton()
        self.stop_button.clicked.connect(self.stop_scan)
        
        btn_layout.addWidget(self.run_button)
        btn_layout.addWidget(self.stop_button)
        control_layout.addLayout(btn_layout)

        # Command Preview
        self.command_input = StyledLineEdit()
        self.command_input.setReadOnly(True)
        self.command_input.setPlaceholderText("Command preview...")
        control_layout.addWidget(self.command_input)

        control_layout.addStretch()
        splitter.addWidget(control_panel)

        # ==================== OUTPUT AREA ====================
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("Hydra results will appear here...")
        splitter.addWidget(self.output)
        splitter.setSizes([500, 300])

        main_layout.addWidget(splitter)
        
        # Initial State
        self._toggle_user_mode()
        self._toggle_pass_mode()

    def _on_service_change(self, service: str):
        if service in self.service_ports:
            self.port_spin.setValue(self.service_ports[service])
        self.update_command()

    def _toggle_user_mode(self):
        is_single = self.user_single_radio.isChecked()
        self.username_input.setPlaceholderText("Enter username..." if is_single else "Select username list...")
        self.user_browse.setVisible(not is_single)
        self.update_command()

    def _toggle_pass_mode(self):
        is_single = self.pass_single_radio.isChecked()
        self.password_input.setPlaceholderText("Enter password..." if is_single else "Select password list...")
        self.pass_browse.setVisible(not is_single)
        self.update_command()

    def _browse_user(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Username List")
        if f: self.username_input.setText(f)

    def _browse_pass(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Password List")
        if f: self.password_input.setText(f)

    # -------------------------------------------------------------------------
    # Command Builder
    # -------------------------------------------------------------------------

    def build_command(self, preview: bool = False) -> str:
        cmd = ["hydra"]
        
        # Target Login
        if self.user_single_radio.isChecked():
            user = self.username_input.text().strip()
            if user:
                cmd.extend(["-l", user])
            elif not preview:
                 raise ValueError("Username required")
            else:
                 cmd.extend(["-l", "<user>"])
        else:
            user_list = self.username_input.text().strip()
            if user_list:
                cmd.extend(["-L", user_list])
            elif not preview:
                 raise ValueError("Username list required")
            else:
                 cmd.extend(["-L", "<user_list>"])
                 
        # Target Pass
        if self.pass_single_radio.isChecked():
            pwd = self.password_input.text().strip()
            if pwd:
                cmd.extend(["-p", pwd])
            elif not preview:
                 # Password can be empty? usually not recommended but possible. 
                 # Hydra requires -p or -P.
                 raise ValueError("Password required")
            else:
                 cmd.extend(["-p", "<pass>"])
        else:
            pass_list = self.password_input.text().strip()
            if pass_list:
                cmd.extend(["-P", pass_list])
            elif not preview:
                 raise ValueError("Password list required")
            else:
                 cmd.extend(["-P", "<pass_list>"])

        # Options
        if self.exit_check.isChecked():
            cmd.append("-f")
        if self.verbose_check.isChecked():
            cmd.append("-V")
        if self.ssl_check.isChecked():
            cmd.append("-S")
            
        tasks = self.tasks_spin.value()
        if tasks != 16:
            cmd.extend(["-t", str(tasks)])
            
        wait = self.wait_spin.value()
        if wait > 0:
            cmd.extend(["-w", str(wait)])
            
        port = self.port_spin.value()
        cmd.extend(["-s", str(port)])
        
        # Target Service
        target = self.host_input.text().strip()
        if not target:
            if preview:
                target = "<target>"
            else:
                raise ValueError("Target required")
        
        service = self.service_combo.currentText()
        cmd.append(f"{service}://{target}")
        
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
            target = self.host_input.text().strip()
            
            self.base_dir = create_target_dirs(target, None)
            output_file = os.path.join(self.base_dir, "Logs", "hydra.txt")
            
            # Hydra output to file
            cmd_str_exec = f"{cmd_str} -o {shlex.quote(output_file)}"
            
            # Start Execution (Mixin)
            self.start_execution(cmd_str_exec, output_file)
            
            self._info(f"Starting Hydra attack on {target}")
            self._section("HYDRA ATTACK")
            

            
        except Exception as e:
            self._error(str(e))

    def on_execution_finished(self):
        super().on_execution_finished()
        self.worker = None
        if self.main_window:
             self.main_window.active_process = None

    def on_new_output(self, line):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_line = ansi_escape.sub('', line).strip()
        
        if not clean_line:
            return

        # Escape HTML chars for safety since we are manually building HTML
        safe_line = html.escape(clean_line)

        # Hydra specific highlighting
        if "login:" in clean_line and "password:" in clean_line:
            # Found creds, usually in green or bold
            self._raw(f'<span style="color:#10B981; font-weight:bold;">{safe_line}</span>')
            # Maybe notify user?
            # self.main_window.notification_manager.notify("Hydra found credentials!")
        elif "[ERROR]" in clean_line:
            self._raw(f'<span style="color:#EF4444;">{safe_line}</span>')
        elif "[WARNING]" in clean_line:
            self._raw(f'<span style="color:#F59E0B;">{safe_line}</span>')
        elif "[DATA]" in clean_line or "[VERBOSE]" in clean_line:
            self._raw(f'<span style="color:#6B7280;">{safe_line}</span>')
        else:
            self._raw(safe_line)
