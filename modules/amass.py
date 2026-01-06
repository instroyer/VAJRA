# =============================================================================
# modules/amass.py
#
# Amass - In-depth Attack Surface Mapping and Asset Discovery
# =============================================================================

import os
import subprocess
import shlex
import re
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QLineEdit, QInputDialog
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from core.tgtinput import parse_targets, TargetInput
from core.fileops import create_target_dirs, get_group_name_from_file
from ui.worker import ProcessWorker
from ui.styles import (
    # Widgets
    RunButton, StopButton, BrowseButton,
    StyledLineEdit, StyledSpinBox, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, CommandDisplay, OutputView,
    StyledGroupBox, ToolSplitter, CopyButton,
    # Behaviors
    SafeStop, OutputHelper,
    # Constants
    TOOL_VIEW_STYLE, COLOR_BACKGROUND_SECONDARY
)


class AmassView(QWidget, SafeStop, OutputHelper):
    """Amass attack surface mapping tool interface."""
    
    tool_name = "Amass"
    tool_category = "SUBDOMAIN_ENUMERATION"
    
    def __init__(self, name, category, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_safe_stop()
        
        # State
        self.targets_queue = []
        self.group_name = None
        self.log_file = None
        
        # Build UI
        self._build_ui()
        self.update_command()
    
    def _build_ui(self):
        """Build the complete UI."""
        self.setStyleSheet(TOOL_VIEW_STYLE)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Splitter for control/output
        splitter = ToolSplitter()
        
        # ==================== CONTROL PANEL ====================
        control_panel = QWidget()
        control_panel.setStyleSheet(f"background-color: {COLOR_BACKGROUND_SECONDARY};")
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)
        
        # Header
        header = HeaderLabel(self.tool_category, self.tool_name)
        control_layout.addWidget(header)
        
        # Target Row
        target_label = StyledLabel("Target")
        control_layout.addWidget(target_label)
        
        target_row = QHBoxLayout()
        self.target_input = TargetInput()
        self.target_input.input_box.textChanged.connect(self.update_command)
        target_row.addWidget(self.target_input, 1)
        
        self.run_button = RunButton()
        self.run_button.clicked.connect(self.run_scan)
        self.stop_button = StopButton()
        self.stop_button.clicked.connect(self.stop_scan)
        
        target_row.addWidget(self.run_button)
        target_row.addWidget(self.stop_button)
        control_layout.addLayout(target_row)
        
        # ==================== CONFIGURATION GROUP ====================
        config_group = StyledGroupBox("⚙️ Advanced Configuration")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(10)
        
        # Row 1: Mode & Timeout
        row1 = QHBoxLayout()
        
        # Mode
        mode_label = StyledLabel("Mode:")
        self.mode_combo = StyledComboBox()
        self.mode_combo.addItems(["enum", "intel"])
        self.mode_combo.currentTextChanged.connect(self.update_command)
        
        row1.addWidget(mode_label)
        row1.addWidget(self.mode_combo)
        row1.addSpacing(20)
        
        # Timeout
        timeout_label = StyledLabel("Timeout (min):")
        self.timeout_spin = StyledSpinBox()
        self.timeout_spin.setRange(0, 1440)
        self.timeout_spin.setValue(0)
        self.timeout_spin.setToolTip("Timeout in minutes (0 = default)")
        self.timeout_spin.valueChanged.connect(self.update_command)
        
        row1.addWidget(timeout_label)
        row1.addWidget(self.timeout_spin)
        row1.addStretch()
        
        config_layout.addLayout(row1)
        
        # Row 2: Checkboxes & Config
        row2 = QHBoxLayout()
        
        # Checkboxes
        self.passive_check = StyledCheckBox("Passive")
        self.passive_check.setToolTip("Enable passive mode (-passive)")
        self.passive_check.stateChanged.connect(self.update_command)
        
        self.active_check = StyledCheckBox("Active")
        self.active_check.setToolTip("Enable active mode (-active)")
        self.active_check.stateChanged.connect(self.update_command)
        
        self.brute_check = StyledCheckBox("Brute")
        self.brute_check.setToolTip("Enable brute force (-brute)")
        self.brute_check.stateChanged.connect(self.update_command)
        
        self.ips_check = StyledCheckBox("IPs")
        self.ips_check.setToolTip("Show IP addresses (-ip)")
        self.ips_check.stateChanged.connect(self.update_command)
        
        self.sources_check = StyledCheckBox("Src")
        self.sources_check.setToolTip("Show data sources (-src)")
        self.sources_check.stateChanged.connect(self.update_command)
        
        row2.addWidget(self.passive_check)
        row2.addWidget(self.active_check)
        row2.addWidget(self.brute_check)
        row2.addWidget(self.ips_check)
        row2.addWidget(self.sources_check)
        row2.addSpacing(20)
        
        # Config Section
        config_label = StyledLabel("Config:")
        self.config_input = StyledLineEdit("Config file...")
        self.config_input.setToolTip("Path to config.ini or config.yaml")
        self.config_input.textChanged.connect(self.update_command)
        
        config_browse = BrowseButton()
        config_browse.clicked.connect(self._browse_config)
        
        row2.addWidget(config_label)
        row2.addWidget(self.config_input)
        row2.addWidget(config_browse)
        
        config_layout.addLayout(row2)
        control_layout.addWidget(config_group)
        
        # Command Display
        self.command_input = CommandDisplay()
        control_layout.addWidget(self.command_input)
        
        control_layout.addStretch()
        splitter.addWidget(control_panel)
        
        # ==================== OUTPUT AREA ====================
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("Amass results will appear here...")
        
        # Copy button
        self.copy_button = CopyButton(self.output.output_text, self.main_window)
        self.copy_button.setParent(self.output.output_text)
        self.copy_button.raise_()
        self.output.output_text.installEventFilter(self)
        
        splitter.addWidget(self.output)
        splitter.setSizes([350, 400])
        
        main_layout.addWidget(splitter)
    
    def eventFilter(self, obj, event):
        """Position copy button on resize."""
        from PySide6.QtCore import QEvent
        if obj == self.output.output_text and event.type() == QEvent.Resize:
            self.copy_button.move(
                self.output.output_text.width() - self.copy_button.sizeHint().width() - 10,
                10
            )
        return super().eventFilter(obj, event)
    
    def _browse_config(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Config File", "", "All Files (*)"
        )
        if file_path:
            self.config_input.setText(file_path)
    
    def update_command(self):
        target = self.target_input.get_target().strip()
        if not target:
            target = "<target>"
        
        mode = self.mode_combo.currentText()
        cmd_parts = ["amass", mode, "-d", target]
        
        if self.passive_check.isChecked():
            cmd_parts.append("-passive")
        if self.active_check.isChecked():
            cmd_parts.append("-active")
        if self.brute_check.isChecked():
            cmd_parts.append("-brute")
        if self.ips_check.isChecked():
            cmd_parts.append("-ip")
        if self.sources_check.isChecked():
            cmd_parts.append("-src")
        
        if self.timeout_spin.value() > 0:
            cmd_parts.extend(["-timeout", str(self.timeout_spin.value())])
        
        if self.config_input.text().strip():
            cmd_parts.extend(["-config", self.config_input.text().strip()])
        
        self.command_input.setText(" ".join(cmd_parts))
    
    def run_scan(self):
        raw_input = self.target_input.get_target()
        if not raw_input:
            self._notify("Please enter a target domain.")
            return
        
        targets, source = parse_targets(raw_input)
        if not targets:
            self._notify("No valid targets found.")
            return
        
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.output.clear()
        
        self.targets_queue = list(targets)
        self.group_name = get_group_name_from_file(raw_input) if source == "file" else None
        self._process_next_target()
    
    def _process_next_target(self):
        if not self.targets_queue:
            self._on_scan_completed()
            self._notify("Amass scan finished.")
            return
        
        target = self.targets_queue.pop(0)
        self._info(f"Running command: {self.command_input.text()}")
        self._section(f"AMASS: {target}")
        
        base_dir = create_target_dirs(target, self.group_name)
        self.log_file = os.path.join(base_dir, "Subdomains", "amass.txt")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        try:
            command = shlex.split(self.command_input.text())
        except ValueError:
            command = self.command_input.text().split()
        
        command = command + ["-o", self.log_file]
        
        # Privilege escalation check
        from ui.settingpanel import privilege_manager
        
        stdin_data = None
        
        if privilege_manager.mode == "sudo":
            if not privilege_manager.sudo_password:
                pwd, ok = QInputDialog.getText(
                    self,
                    "Sudo Password Required",
                    "Amass scan is configured to use sudo.\n\nPlease enter your sudo password:",
                    QLineEdit.Password
                )
                if ok and pwd.strip():
                    privilege_manager.set_sudo_password(pwd.strip())
                else:
                    self._error("Scan cancelled: Password is required.")
                    return
            
            command = privilege_manager.wrap_command(command)
            stdin_data = privilege_manager.get_stdin_data()
            self._info("Running with sudo")
        
        self.worker = ProcessWorker(command, stdin_data=stdin_data)
        self.worker.output_ready.connect(self._on_output)
        self.worker.finished.connect(self._on_process_finished)
        self.worker.error.connect(self._on_process_error)
        self.worker.start()
        
        if self.main_window:
            self.main_window.active_process = self.worker
    
    def _on_output(self, line):
        # Strip ANSI codes
        clean_line = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', line)
        
        # Filter noisy library errors
        if "address_parser" in clean_line or "libpostal" in clean_line:
            return
        if "dir=(null)" in clean_line:
            return
        if "Could not find parser model file" in clean_line:
            return
        
        # Filter progress bars
        if "%" in clean_line and "p/s" in clean_line:
            return
        
        self.output.appendPlainText(clean_line)
    
    def _on_process_finished(self):
        self.output.appendPlainText("\n")
        
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    self.output.appendPlainText(f.read())
            except IOError as e:
                self._error(f"Could not read log file: {e}")
        
        if self.targets_queue:
            self._process_next_target()
        else:
            self._on_scan_completed()
            self._notify("Amass scan finished.")
    
    def _on_process_error(self, error):
        self._error(f"Process error: {error}")
        self._on_scan_completed()
    
    def stop_scan(self):
        """Forcefully stop the scan and kill all amass processes."""
        self.targets_queue = []
        
        # Call parent stop
        if hasattr(self, 'worker') and self.worker:
            self.worker.stop()
            self.worker = None
        
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self._info("Process stopped by user.")
        
        # Force kill lingering amass processes
        try:
            if os.name == 'nt':
                subprocess.run(
                    ["taskkill", "/F", "/IM", "amass.exe"],
                    stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                subprocess.run(
                    ["pkill", "-9", "amass"],
                    stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
                )
        except Exception as e:
            self._error(f"Failed to force kill Amass: {e}")
    
    def _on_scan_completed(self):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.worker = None
        if self.main_window:
            self.main_window.active_process = None


class AmassTool(ToolBase):
    """Amass tool plugin."""
    
    @property
    def name(self) -> str:
        return "Amass"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SUBDOMAIN_ENUMERATION
    
    def get_widget(self, main_window):
        return AmassView(self.name, self.category, main_window=main_window)
