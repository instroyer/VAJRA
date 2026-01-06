import os
import re
from datetime import datetime
from typing import Optional, Set, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QLineEdit, QGroupBox, QMessageBox, QSplitter,
    QFileDialog, QProgressBar, QTextEdit, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QRadioButton, QButtonGroup, QCheckBox
)

from modules.bases import ToolBase, ToolCategory
from ui.worker import ProcessWorker
from core.fileops import create_target_dirs
from ui.styles import (
    COLOR_BACKGROUND_INPUT, COLOR_BACKGROUND_PRIMARY, COLOR_BACKGROUND_SECONDARY,
    COLOR_TEXT_PRIMARY, COLOR_BORDER, COLOR_BORDER_FOCUSED, StyledComboBox,
    GROUPBOX_STYLE, SPINBOX_STYLE, CommandDisplay, RunButton, StopButton, SafeStop, OutputView, HeaderLabel
)


class HydraTool(ToolBase):
    """Hydra brute force attack tool."""

    @property
    def name(self) -> str:
        return "Hydra"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CRACKER

    def get_widget(self, main_window: QWidget) -> QWidget:
        """Create the tool view widget."""
        return HydraToolView(main_window=main_window)


class HydraToolView(QWidget, SafeStop):
    """Hydra brute force attack interface."""
    
    def __init__(self, main_window):
        super().__init__()
        self.init_safe_stop()
        self.main_window = main_window
        self._is_stopping = False
        self._discovered_creds: Set[Tuple[str, str, str]] = set()
        self._logs_dir: Optional[str] = None

        self.service_mappings = {
            "FTP": "ftp",
            "SSH": "ssh",
            "Telnet": "telnet",
            "SMTP": "smtp",
            "SMTPS": "smtps",
            "POP3": "pop3",
            "POP3S": "pop3s",
            "IMAP": "imap",
            "IMAPS": "imaps",
            "HTTP GET": "http-get",
            "HTTP POST": "http-post",
            "HTTPS GET": "https-get",
            "HTTPS POST": "https-post",
            "HTTP HEAD": "http-head",
            "SMB": "smb",
            "SMB NT": "smbnt",
            "LDAP": "ldap",
            "LDAP SSL": "ldaps",
            "MySQL": "mysql",
            "MSSQL": "mssql",
            "Oracle": "oracle",
            "PostgreSQL": "postgres",
            "RDP": "rdp",
            "VNC": "vnc",
            "SNMP": "snmp",
            "Cisco": "cisco",
            "Cisco Enable": "cisco-enable"
        }

        self._build_ui()

    def _build_ui(self):
        """Build the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create splitter
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

        # Control panel
        control_panel = QWidget()
        control_panel.setStyleSheet(f"background-color: {COLOR_BACKGROUND_SECONDARY};")
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        # Header
        header = HeaderLabel("CRACKER", "Hydra")
        control_layout.addWidget(header)

        # ==================== TARGET SECTION ====================
        target_group = QGroupBox("🎯 Target Configuration")
        target_group.setStyleSheet(GROUPBOX_STYLE)
        target_layout = QVBoxLayout(target_group)

        # Host row
        host_row = QHBoxLayout()
        host_label = QLabel("Target Host/IP:")
        host_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("e.g., 192.168.1.100 or example.com")
        self.host_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 8px;
            }}
        """)
        self.host_input.textChanged.connect(self.update_command)
        host_row.addWidget(host_label)
        host_row.addWidget(self.host_input, 1)
        target_layout.addLayout(host_row)

        # Port and Service row
        port_row = QHBoxLayout()
        port_label = QLabel("Port:")
        port_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.port_spin = QSpinBox()
        self.port_spin.setStyleSheet(SPINBOX_STYLE)
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(22)
        self.port_spin.valueChanged.connect(self.update_command)

        service_label = QLabel("Service:")
        service_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.service_combo = QComboBox()
        self.service_combo.addItems([
            "ssh", "ftp", "http-get", "http-post-form", "mysql", "postgres",
            "smb", "rdp", "vnc", "telnet", "pop3", "imap", "smtp"
        ])
        self.service_combo.currentTextChanged.connect(self.update_command)

        port_row.addWidget(port_label)
        port_row.addWidget(self.port_spin)
        port_row.addSpacing(20)
        port_row.addWidget(service_label)
        port_row.addWidget(self.service_combo, 1)
        target_layout.addLayout(port_row)

        control_layout.addWidget(target_group)

        # ==================== CREDENTIALS SECTION ====================
        creds_group = QGroupBox("🔐 Credentials")
        creds_group.setStyleSheet(GROUPBOX_STYLE)
        creds_layout = QVBoxLayout(creds_group)

        # Username row
        user_row = QHBoxLayout()
        user_label = QLabel("Username:")
        user_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")

        self.single_user_radio = QRadioButton("Single")
        self.single_user_radio.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.userlist_radio = QRadioButton("List")
        self.userlist_radio.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.userlist_radio.setChecked(True)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setEnabled(False)
        self.username_input.setStyleSheet(self.host_input.styleSheet())
        self.username_input.textChanged.connect(self.update_command)

        self.userlist_input = QLineEdit()
        self.userlist_input.setPlaceholderText("Select user list file...")
        self.userlist_input.setStyleSheet(self.host_input.styleSheet())
        self.userlist_input.textChanged.connect(self.update_command)

        self.userlist_browse = QPushButton("📁")
        self.userlist_browse.clicked.connect(self._browse_userlist)

        self.single_user_radio.toggled.connect(self._on_user_mode_change)

        user_row.addWidget(user_label)
        user_row.addWidget(self.single_user_radio)
        user_row.addWidget(self.userlist_radio)
        user_row.addWidget(self.username_input, 1)
        user_row.addWidget(self.userlist_input, 1)
        user_row.addWidget(self.userlist_browse)
        creds_layout.addLayout(user_row)

        # Password row
        pass_row = QHBoxLayout()
        pass_label = QLabel("Password:")
        pass_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")

        self.single_pass_radio = QRadioButton("Single")
        self.single_pass_radio.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.passlist_radio = QRadioButton("List")
        self.passlist_radio.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.passlist_radio.setChecked(True)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEnabled(False)
        self.password_input.setStyleSheet(self.host_input.styleSheet())
        self.password_input.textChanged.connect(self.update_command)

        self.passlist_input = QLineEdit()
        self.passlist_input.setPlaceholderText("Select password list file...")
        self.passlist_input.setStyleSheet(self.host_input.styleSheet())
        self.passlist_input.textChanged.connect(self.update_command)

        self.passlist_browse = QPushButton("📁")
        self.passlist_browse.clicked.connect(self._browse_passlist)

        self.single_pass_radio.toggled.connect(self._on_pass_mode_change)

        pass_row.addWidget(pass_label)
        pass_row.addWidget(self.single_pass_radio)
        pass_row.addWidget(self.passlist_radio)
        pass_row.addWidget(self.password_input, 1)
        pass_row.addWidget(self.passlist_input, 1)
        pass_row.addWidget(self.passlist_browse)
        creds_layout.addLayout(pass_row)

        control_layout.addWidget(creds_group)

        # ==================== ADVANCED SECTION ====================
        advanced_group = QGroupBox("⚙️ Advanced Options")
        advanced_group.setStyleSheet(GROUPBOX_STYLE)
        advanced_layout = QVBoxLayout(advanced_group)

        # Options row
        options_row = QHBoxLayout()

        tasks_label = QLabel("Tasks:")
        tasks_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.tasks_spin = QSpinBox()
        self.tasks_spin.setStyleSheet(SPINBOX_STYLE)
        self.tasks_spin.setRange(1, 64)
        self.tasks_spin.setValue(4)
        self.tasks_spin.valueChanged.connect(self.update_command)

        wait_label = QLabel("Wait:")
        wait_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.wait_spin = QSpinBox()
        self.wait_spin.setStyleSheet(SPINBOX_STYLE)
        self.wait_spin.setRange(0, 100)
        self.wait_spin.setValue(0)
        self.wait_spin.setSuffix(" ms")
        self.wait_spin.valueChanged.connect(self.update_command)

        self.verbose_check = QCheckBox("Verbose")
        self.verbose_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.verbose_check.stateChanged.connect(self.update_command)

        self.exit_first_check = QCheckBox("Exit on First")
        self.exit_first_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.exit_first_check.stateChanged.connect(self.update_command)

        options_row.addWidget(tasks_label)
        options_row.addWidget(self.tasks_spin)
        options_row.addSpacing(15)
        options_row.addWidget(wait_label)
        options_row.addWidget(self.wait_spin)
        options_row.addSpacing(15)
        options_row.addWidget(self.verbose_check)
        options_row.addWidget(self.exit_first_check)
        options_row.addStretch()

        advanced_layout.addLayout(options_row)
        control_layout.addWidget(advanced_group)

        # Command display (Centralized)
        self.command_display_widget = CommandDisplay()
        self.command_display = self.command_display_widget.input
        self.command_display.setPlaceholderText("Configure options to generate command...")
        control_layout.addWidget(self.command_display_widget)

        # Run/Stop buttons
        btn_row = QHBoxLayout()
        self.run_button = RunButton()
        self.run_button.clicked.connect(self.run_scan)

        self.stop_button = StopButton()
        self.stop_button.clicked.connect(self.stop_scan)

        btn_row.addWidget(self.run_button)
        btn_row.addWidget(self.stop_button)
        btn_row.addStretch()
        control_layout.addLayout(btn_row)

        control_layout.addStretch()
        splitter.addWidget(control_panel)

        # Output panel
        self.output = OutputView(self.main_window, show_copy_button=False)
        self.output.setPlaceholderText("Hydra results will appear here...")
        splitter.addWidget(self.output)
        splitter.setSizes([400, 350])

        # Update command initially
        self.update_command()

    def run_scan(self):
        """Execute the scan."""
        self._run_attack()

    def stop_scan(self):
        """Stop the scan."""
        self.safe_stop()

    def _on_user_mode_change(self, is_single):
        """Handle username mode change."""
        self.username_input.setEnabled(is_single)
        self.username_input.setVisible(is_single)
        self.userlist_input.setEnabled(not is_single)
        self.userlist_input.setVisible(not is_single)
        self.userlist_browse.setEnabled(not is_single)
        self.userlist_browse.setVisible(not is_single)
        self.update_command()

    def _on_pass_mode_change(self, is_single):
        """Handle password mode change."""
        self.password_input.setEnabled(is_single)
        self.password_input.setVisible(is_single)
        self.passlist_input.setEnabled(not is_single)
        self.passlist_input.setVisible(not is_single)
        self.passlist_browse.setEnabled(not is_single)
        self.passlist_browse.setVisible(not is_single)
        self.update_command()

    def _connect_signals(self):
        """Connect all signals."""
        # Text fields
        self.host_input.textChanged.connect(self._update_command_display)
        self.username_input.textChanged.connect(self._update_command_display)
        self.userlist_input.textChanged.connect(self._update_command_display)
        self.password_input.textChanged.connect(self._update_command_display)
        self.passlist_input.textChanged.connect(self._update_command_display)
        
        # Combos
        self.service_input.currentTextChanged.connect(self._update_command_display)
        self.service_input.currentTextChanged.connect(self._on_service_changed)
        self.custom_port_input.textChanged.connect(self._update_command_display)
        
        # Spinboxes
        self.tasks_spin.valueChanged.connect(self._update_command_display)
        self.wait_spin.valueChanged.connect(self._update_command_display)
        
        # Checkboxes
        self.exit_on_first_check.stateChanged.connect(self._update_command_display)
        self.use_ssl_check.stateChanged.connect(self._update_command_display)
        self.use_proxy_check.stateChanged.connect(self._update_command_display)
        self.proxy_input.textChanged.connect(self._update_command_display)
        
        # HTTP form fields
        self.http_form_path.textChanged.connect(self._update_command_display)
        self.http_user_param.textChanged.connect(self._update_command_display)
        self.http_pass_param.textChanged.connect(self._update_command_display)
        self.http_fail_string.textChanged.connect(self._update_command_display)

    def _on_service_changed(self):
        """Show/hide HTTP form options based on service."""
        service = self.service_input.currentText().lower()
        is_http = 'http' in service
        self.http_form_group.setVisible(is_http)

    def _on_ssl_changed(self):
        """Handle SSL/TLS toggle."""
        self._update_command_display()

    def _on_proxy_changed(self):
        """Handle proxy checkbox change."""
        is_checked = self.use_proxy_check.isChecked()
        self.proxy_input.setEnabled(is_checked)
        self._update_command_display()

    def _on_custom_port_changed(self):
        """Handle custom port checkbox change."""
        is_checked = self.custom_port_check.isChecked()
        self.custom_port_input.setEnabled(is_checked)
        self._update_command_display()

    def _on_user_mode_changed(self):
        """Handle username mode change."""
        is_single = self.single_user_radio.isChecked()
        self.username_input.setEnabled(is_single)
        self.userlist_input.setEnabled(not is_single)
        self.userlist_browse.setEnabled(not is_single)
        self._update_command_display()

    def _on_pass_mode_changed(self):
        """Handle password mode change."""
        is_single = self.single_pass_radio.isChecked()
        self.password_input.setEnabled(is_single)
        self.passlist_input.setEnabled(not is_single)
        self.passlist_browse.setEnabled(not is_single)
        self._update_command_display()

    def _browse_userlist(self):
        """Browse for username wordlist."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Username Wordlist", "",
            "All Files (*);;Text Files (*.txt);;Wordlist Files (*.lst *.dict)"
        )
        if file_path:
            self.userlist_input.setText(file_path)

    def _browse_passlist(self):
        """Browse for password wordlist."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Password Wordlist", "",
            "All Files (*);;Text Files (*.txt);;Wordlist Files (*.lst *.dict)"
        )
        if file_path:
            self.passlist_input.setText(file_path)

    def update_command(self):
        """Update the command display field."""
        self._update_command_display()

    def _update_command_display(self):
        """Update the command display field."""
        try:
            cmd = self._build_hydra_command()
            # Replace placeholders for empty fields in display
            display_cmd = []
            for token in cmd:
                if token == "":
                    continue
                display_cmd.append(token)
            
            # Add placeholders if fields are empty (for display only)
            if not self.host_input.text().strip():
                # Show generic target placeholder if empty
                service = self.service_combo.currentText()
                display_cmd[-1] = f"{service}://<target>"
            
            self.command_display.setText(" ".join(display_cmd))
        except Exception:
            # Prevent crashes during UI updates if partial state
            pass

    def _build_hydra_command(self) -> list:
        """Build the actual hydra command for execution."""
        cmd = ["hydra"]
        
        # Username
        if self.single_user_radio.isChecked():
            user = self.username_input.text().strip()
            if user:
                cmd.extend(["-l", user])
        else:
            ulist = self.userlist_input.text().strip()
            if ulist:
                cmd.extend(["-L", ulist])
        
        # Password
        if self.single_pass_radio.isChecked():
            pwd = self.password_input.text().strip()
            if pwd:
                cmd.extend(["-p", pwd])
        else:
            plist = self.passlist_input.text().strip()
            if plist:
                cmd.extend(["-P", plist])
        
        # Exit on first success
        if self.exit_first_check.isChecked():
            cmd.append("-f")
            
        if self.verbose_check.isChecked():
            cmd.append("-V")
            
        tasks = self.tasks_spin.value()
        if tasks != 16:
            cmd.extend(["-t", str(tasks)])
            
        wait_time = self.wait_spin.value()
        if wait_time > 0:
            cmd.extend(["-w", str(wait_time)])
            
        # Port
        port = self.port_spin.value()
        cmd.extend(["-s", str(port)])
        
        # Target
        host = self.host_input.text().strip()
        service = self.service_combo.currentText().strip()
        
        if host:
            cmd.append(f"{service}://{host}")
        else:
            cmd.append("") # Placeholder
            
        # Output file
        if hasattr(self, '_logs_dir') and self._logs_dir:
            output_file = os.path.join(self._logs_dir, "hydra_results.txt")
            cmd.extend(["-o", output_file])
            
        return cmd


    def _run_attack(self):
        """Start the brute force attack."""
        # Validate inputs
        host = self.host_input.text().strip()
        if not host:
            QMessageBox.warning(self, "No Target", "Please enter a target host/IP.")
            return

        # Check username
        if self.single_user_radio.isChecked():
            if not self.username_input.text().strip():
                QMessageBox.warning(self, "No Username", "Please enter a username.")
                return
        else:
            userlist = self.userlist_input.text().strip()
            if not userlist:
                QMessageBox.warning(self, "No Username List", "Please select a username wordlist.")
                return
            if not os.path.exists(userlist):
                QMessageBox.warning(self, "File Not Found", f"Username list not found: {userlist}")
                return

        # Check password
        if self.single_pass_radio.isChecked():
            if not self.password_input.text().strip():
                QMessageBox.warning(self, "No Password", "Please enter a password.")
                return
        else:
            passlist = self.passlist_input.text().strip()
            if not passlist:
                QMessageBox.warning(self, "No Password List", "Please select a password wordlist.")
                return
            if not os.path.exists(passlist):
                QMessageBox.warning(self, "File Not Found", f"Password list not found: {passlist}")
                return

        # Clear outputs
        self.output.clear()
        self.results_table.setRowCount(0)
        self._discovered_creds = set()
        self._is_stopping = False

        try:
            # Create directories
            base_dir = create_target_dirs(f"hydra_{host}")
            self._logs_dir = os.path.join(base_dir, "Logs")
            os.makedirs(self._logs_dir, exist_ok=True)

            self._info(f"Starting Hydra brute force attack")
            self._info(f"Target: {host}")
            self._info(f"Service: {self.service_combo.currentText()}")
            
            # Build command
            cmd = self._build_hydra_command()
            self._info(f"Command: {' '.join(cmd)}")
            self.output.append("")

            # Start worker (using inline import to avoid circular dependency if any)
            from ui.worker import ProcessWorker
            self.worker = ProcessWorker(cmd)
            self.register_worker(self.worker)
            
            self.worker.output_ready.connect(self._on_output)
            self.worker.finished.connect(self._on_finished)
            self.worker.error.connect(self._error)

            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)

            self.worker.start()

        except Exception as e:
            self._error(f"Failed to start attack: {str(e)}")

    def _on_output(self, line):
        self.output.append(line)
        # Parse logic could go here
        
    def _on_finished(self):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.worker = None
        self._info("Attack finished.")
        
    def _error(self, msg):
        self.output.append(f"ERROR: {msg}")
        self._on_finished()

    def _info(self, msg):
        self.output.append(f"[*] {msg}")

    def stop_all_workers(self):
        """Stop all workers - called when tab is closed."""
        self._stop_attack()

    def closeEvent(self, event):
        """Clean up workers when widget is closed."""
        self.stop_all_workers()
        super().closeEvent(event)

    def _on_output(self, line: str):
        """Process output line."""
        self.output.append(line)
        
        # Parse credentials
        # Hydra format: [22][ssh] host: 192.168.1.1   login: admin   password: password123
        if 'login:' in line and 'password:' in line:
            try:
                login_match = re.search(r'login:\s*(\S+)', line)
                pass_match = re.search(r'password:\s*(.+?)(?:\s*$)', line)
                
                if login_match and pass_match:
                    username = login_match.group(1).strip()
                    password = pass_match.group(1).strip()
                    host = self.host_input.text().strip()
                    
                    self._add_credential(host, username, password)
            except Exception:
                pass

    def _add_credential(self, host: str, username: str, password: str):
        """Add credential to results table (with duplicate check)."""
        cred_key = (host, username, password)
        
        if cred_key in self._discovered_creds:
            return  # Skip duplicate
        
        self._discovered_creds.add(cred_key)
        
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        self.results_table.setItem(row, 0, QTableWidgetItem(host))
        self.results_table.setItem(row, 1, QTableWidgetItem(username))
        self.results_table.setItem(row, 2, QTableWidgetItem(password))
        
        # Switch to results tab
        self.tab_widget.setCurrentIndex(1)

    def _on_finished(self):
        """Handle attack completion."""
        self.progress_bar.setVisible(False)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        if self._is_stopping:
            return

        # Save results
        try:
            if self._logs_dir and self.results_table.rowCount() > 0:
                results_file = os.path.join(self._logs_dir, "cracked_credentials.txt")
                with open(results_file, 'w') as f:
                    f.write("Hydra Brute Force Results\n")
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Target: {self.host_input.text().strip()}\n")
                    f.write(f"Service: {self.service_input.currentText()}\n")
                    if self.custom_port_check.isChecked():
                        f.write(f"Custom Port: {self.custom_port_input.text().strip()}\n")
                    f.write("\n")
                    f.write("Cracked Credentials:\n")
                    f.write("-" * 80 + "\n")
                    
                    for row in range(self.results_table.rowCount()):
                        host = self.results_table.item(row, 0).text()
                        user = self.results_table.item(row, 1).text()
                        pwd = self.results_table.item(row, 2).text()
                        f.write(f"Host: {host}\n")
                        f.write(f"Username: {user}\n")
                        f.write(f"Password: {pwd}\n")
                        f.write("-" * 40 + "\n")
                
                self._info(f"Results saved to: {results_file}")
        except Exception as e:
            self._error(f"Failed to save results: {str(e)}")

        self.output.append("")
        self._info("Attack completed.")
        
    def _save_credentials(self):
        """Save credentials to file."""
        if self.results_table.rowCount() == 0:
            QMessageBox.information(self, "No Credentials", "No credentials to save.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Credentials", "", "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write("Hydra Brute Force Results\n")
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Target: {self.host_input.text().strip()}\n")
                    f.write(f"Service: {self.service_input.currentText()}\n")
                    if self.custom_port_check.isChecked():
                        f.write(f"Custom Port: {self.custom_port_input.text().strip()}\n")
                    f.write("\n")
                    f.write("Cracked Credentials:\n")
                    f.write("-" * 80 + "\n")
                    
                    for row in range(self.results_table.rowCount()):
                        host = self.results_table.item(row, 0).text()
                        user = self.results_table.item(row, 1).text()
                        pwd = self.results_table.item(row, 2).text()
                        f.write(f"Host: {host}\n")
                        f.write(f"Username: {user}\n")
                        f.write(f"Password: {pwd}\n")
                        f.write("-" * 40 + "\n")
                
                self._info(f"Credentials saved to: {file_path}")
                QMessageBox.information(self, "Saved", f"Credentials saved successfully!\n{file_path}")
            except Exception as e:
                self._error(f"Failed to save: {str(e)}")

    def _info(self, message: str):
        """Add info message."""
        self.output.append(f"[INFO] {message}")

    def _error(self, message: str):
        """Add error message."""
        self.output.append(f"[ERROR] {message}")
