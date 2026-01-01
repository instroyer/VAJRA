import os
import subprocess
import shlex
import re
from PySide6.QtWidgets import (
    QLabel, QSpinBox, QHBoxLayout, QCheckBox, QVBoxLayout, QGroupBox, 
    QLineEdit, QPushButton, QFileDialog, QComboBox, QInputDialog
)
from core.tgtinput import parse_targets
from core.fileops import create_target_dirs, get_group_name_from_file
from modules.bases import ToolBase, ToolCategory
from ui.styles import (
    BaseToolView, CopyButton, COLOR_TEXT_PRIMARY, COLOR_BORDER, 
    COLOR_BACKGROUND_INPUT, COLOR_BORDER_INPUT_FOCUSED, StyledComboBox
)
from ui.worker import ProcessWorker
from PySide6.QtCore import Qt


class AmassView(BaseToolView):
    def _build_base_ui(self):
        super()._build_base_ui()
        self.copy_button = CopyButton(self.output.output_text, self.main_window)
        self.output.layout().addWidget(self.copy_button, 0, 0, Qt.AlignTop | Qt.AlignRight)

    def __init__(self, name, category, main_window=None):
        super().__init__(name, category, main_window)
        # Initialize attributes
        self.mode_combo = None
        self.passive_check = None
        self.active_check = None
        self.brute_check = None
        self.ips_check = None
        self.sources_check = None
        self.timeout_spin = None
        self.config_input = None
        
        # Build UI and initialize command
        self._build_custom_ui()
        self.update_command()
        
        self.targets_queue = []
        self.group_name = None
        self.log_file = None

    def _build_custom_ui(self):
        """Build advanced options for Amass."""
        # Use centralized options container
        
        # ==================== CONFIGURATION GROUP ====================
        config_group = QGroupBox("⚙️ Advanced Configuration")
        config_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(10)

        # Row 1: Mode & Timeout
        row1 = QHBoxLayout()
        
        # Mode
        mode_label = QLabel("Mode:")
        mode_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.mode_combo = StyledComboBox()
        self.mode_combo.addItems(["enum", "intel"])
        self.mode_combo.currentTextChanged.connect(self.update_command)
        
        row1.addWidget(mode_label)
        row1.addWidget(self.mode_combo)
        
        row1.addSpacing(20)
        
        # Timeout
        timeout_label = QLabel("Timeout (min):")
        timeout_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(0, 1440) # 0 to 24 hours
        self.timeout_spin.setValue(0) # 0 = no limit (or default)
        self.timeout_spin.setToolTip("Timeout in minutes (0 = default)")
        self.timeout_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        self.timeout_spin.valueChanged.connect(self.update_command)
        
        row1.addWidget(timeout_label)
        row1.addWidget(self.timeout_spin)
        row1.addStretch()
        
        config_layout.addLayout(row1)
        
        # Row 2: Checkboxes & Config
        row2 = QHBoxLayout()
        
        # Checkboxes
        self.passive_check = QCheckBox("Passive")
        self.passive_check.setToolTip("Enable passive mode (-passive)")
        self.passive_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.passive_check.stateChanged.connect(self.update_command)
        
        self.active_check = QCheckBox("Active")
        self.active_check.setToolTip("Enable active mode (-active)")
        self.active_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.active_check.stateChanged.connect(self.update_command)
        
        self.brute_check = QCheckBox("Brute")
        self.brute_check.setToolTip("Enable brute force (-brute)")
        self.brute_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.brute_check.stateChanged.connect(self.update_command)
        
        self.ips_check = QCheckBox("IPs")
        self.ips_check.setToolTip("Show IP addresses (-ip)")
        self.ips_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.ips_check.stateChanged.connect(self.update_command)
        
        self.sources_check = QCheckBox("Src")
        self.sources_check.setToolTip("Show data sources (-src)")
        self.sources_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.sources_check.setChecked(False)
        self.sources_check.stateChanged.connect(self.update_command)
        
        row2.addWidget(self.passive_check)
        row2.addWidget(self.active_check)
        row2.addWidget(self.brute_check)
        row2.addWidget(self.ips_check)
        row2.addWidget(self.sources_check)
        
        row2.addSpacing(20) # Spacer between checkboxes and config
        
        # Config Section
        config_label = QLabel("Config:")
        config_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        
        self.config_input = QLineEdit()
        self.config_input.setPlaceholderText("Config file...")
        self.config_input.setToolTip("Path to config.ini or config.yaml")
        self.config_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        self.config_input.textChanged.connect(self.update_command)
        
        config_browse = QPushButton("📁")
        config_browse.setFixedSize(30, 30)
        config_browse.clicked.connect(self._browse_config)
        config_browse.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_BACKGROUND_INPUT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                color: {COLOR_TEXT_PRIMARY};
            }}
            QPushButton:hover {{ background-color: #4A4A4A; }}
        """)
        
        row2.addWidget(config_label)
        row2.addWidget(self.config_input)
        row2.addWidget(config_browse)
        
        config_layout.addLayout(row2)
        
        # Add to centralized container
        self.options_container.addWidget(config_group)

    def _browse_config(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Config File", "", "All Files (*)")
        if file_path:
            self.config_input.setText(file_path)

    def update_command(self):
        # Handle case when UI elements haven't been created yet
        if not hasattr(self, 'mode_combo') or not self.mode_combo:
            return

        target = self.target_input.get_target().strip()
        if not target:
            target = "<target>"
            
        mode = self.mode_combo.currentText()
        cmd_parts = ["amass", mode, "-d", target]
        
        # Add options
        if self.passive_check and self.passive_check.isChecked():
            cmd_parts.append("-passive")
        if self.active_check and self.active_check.isChecked():
            cmd_parts.append("-active")
        if self.brute_check and self.brute_check.isChecked():
            cmd_parts.append("-brute")
            
        if self.ips_check and self.ips_check.isChecked():
            cmd_parts.append("-ip")
        if self.sources_check and self.sources_check.isChecked():
            cmd_parts.append("-src")
            
        if self.timeout_spin and self.timeout_spin.value() > 0:
            cmd_parts.extend(["-timeout", str(self.timeout_spin.value())])
            
        if self.config_input and self.config_input.text().strip():
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

        # === PRIVILEGE ESCALATION CHECK ===
        from ui.settingpanel import privilege_manager
        
        # If Sudo is enabled in settings, we assume user wants Amass to use it 
        # (similar to Nmap's auto-detection, but here we honor the global toggle)
        needs_root = (privilege_manager.mode == "sudo")
        
        if needs_root:
            # Check for password
            if not privilege_manager.sudo_password:
                    pwd, ok = QInputDialog.getText(
                        self, 
                        "Sudo Password Required", 
                        "Amass scan requires root privileges (Settings Enabled).\nPlease enter your sudo password:", 
                        QLineEdit.Password
                    )
                    if ok and pwd:
                        privilege_manager.set_sudo_password(pwd)
                    else:
                        self._notify("Scan cancelled: Root password required.")
                        return

        if needs_root and privilege_manager.needs_privilege_escalation():
            command = privilege_manager.wrap_command(command)
            stdin_data = privilege_manager.get_stdin_data()
            self._info(f"Using privilege escalation on Amass: {privilege_manager.mode}")
        else:
            stdin_data = None
            
        self.worker = ProcessWorker(command, stdin_data=stdin_data)
        self.worker.output_ready.connect(self._on_output)
        self.worker.finished.connect(self._on_process_finished)
        self.worker.error.connect(self._on_process_error)
        self.worker.start()

        if self.main_window:
            self.main_window.active_process = self.worker

    def _on_output(self, line):
        # Strip ANSI codes (robust)
        clean_line = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', line)
        
        # Filter out noisy library errors from Amass binary
        if "address_parser" in clean_line or "libpostal" in clean_line:
            return
        if "dir=(null)" in clean_line:
            return
        if "Could not find parser model file" in clean_line:
            return
            
        # Filter progress bars (e.g. [==>] 10% 400 p/s)
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
        self.targets_queue = [] # Clear queue to prevent next target from starting
        super().stop_scan()
        
        # Force kill any lingering amass processes
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


class AmassTool(ToolBase):
    @property
    def name(self) -> str:
        return "Amass"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SUBDOMAIN_ENUMERATION

    def get_widget(self, main_window):
        return AmassView(self.name, self.category, main_window=main_window)
