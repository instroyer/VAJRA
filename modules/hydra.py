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
from ui.worker import ProcessWorker, StoppableToolMixin
from core.fileops import create_target_dirs
from ui.styles import (
    TARGET_INPUT_STYLE, COMBO_BOX_STYLE,
    COLOR_BACKGROUND_INPUT, COLOR_BACKGROUND_PRIMARY, COLOR_TEXT_PRIMARY, COLOR_BORDER, COLOR_BORDER_INPUT_FOCUSED,
    StyledComboBox, RUN_BUTTON_STYLE, STOP_BUTTON_STYLE,
    TOOL_HEADER_STYLE, TOOL_VIEW_STYLE, CommandDisplay
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


class HydraToolView(QWidget, StoppableToolMixin):
    """Hydra brute force attack interface."""
    
    def __init__(self, main_window):
        super().__init__()
        self.init_stoppable()
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
        control_panel.setStyleSheet(TOOL_VIEW_STYLE)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        # Header
        header = QLabel("Cracker › Hydra")
        header.setStyleSheet(TOOL_HEADER_STYLE)
        control_layout.addWidget(header)

        # Target Configuration
        target_group = self._create_target_section()
        control_layout.addWidget(target_group)

        # Credentials Configuration
        creds_group = self._create_credentials_section()
        control_layout.addWidget(creds_group)

        # Advanced Options
        advanced_group = self._create_advanced_section()
        control_layout.addWidget(advanced_group)

        # Command display (Centralized)
        self.command_display_widget = CommandDisplay()
        self.command_display = self.command_display_widget.input
        self.command_display.setPlaceholderText("Configure options to generate command...")
        
        control_layout.addWidget(self.command_display_widget)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                text-align: center;
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: #DC3545;
            }}
        """)
        control_layout.addWidget(self.progress_bar)
        control_layout.addStretch()

        # Output area with tabs
        self.tab_widget = QTabWidget()

        # Output tab
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_BACKGROUND_PRIMARY};
                color: {COLOR_TEXT_PRIMARY};
                border: none;
                padding: 12px;
                font-family: 'Courier New', monospace;
                font-size: 13px;
            }}
        """)

        # Results table (no buttons here anymore)
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Host", "Username", "Password"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                gridline-color: {COLOR_BORDER};
            }}
            QHeaderView::section {{
                background-color: #2A2A2A;
                color: {COLOR_TEXT_PRIMARY};
                padding: 8px;
                border: 1px solid {COLOR_BORDER};
                font-weight: bold;
            }}
        """)

        self.tab_widget.addTab(self.output, "Output")
        self.tab_widget.addTab(self.results_table, "Cracked Credentials")

        splitter.addWidget(control_panel)
        splitter.addWidget(self.tab_widget)
        splitter.setSizes([500, 400])

        # Connect signals
        self._connect_signals()
        
        # Initial command update
        self._update_command_display()

    def _create_target_section(self) -> QGroupBox:
        """Create target configuration section."""
        target_group = QGroupBox("Target Configuration")
        target_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLOR_BORDER};
                border-radius: 5px;
                margin-top: 1ex;
                color: {COLOR_TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)

        target_layout = QVBoxLayout(target_group)

        # Host row with buttons
        host_row = QHBoxLayout()
        
        host_label = QLabel("Target Host/IP:")
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("e.g., 192.168.1.100 or example.com")
        self.host_input.setMinimumHeight(36)
        self.host_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 6px;
                font-size: 14px;
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLOR_BORDER_INPUT_FOCUSED};
            }}
        """)

        # Run/Stop buttons
        self.run_button = QPushButton("RUN")
        self.run_button.setCursor(Qt.PointingHandCursor)
        self.run_button.setToolTip("Start Brute Force")
        self.run_button.setStyleSheet(RUN_BUTTON_STYLE)
        self.run_button.clicked.connect(self._run_attack)

        self.stop_button = QPushButton("■")
        self.stop_button.setCursor(Qt.PointingHandCursor)
        self.stop_button.setToolTip("Stop Brute Force")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet(STOP_BUTTON_STYLE)
        self.stop_button.clicked.connect(self._stop_attack)

        # Save button
        self.save_creds_button = QPushButton("💾")
        self.save_creds_button.setFixedSize(36, 36)
        self.save_creds_button.setStyleSheet(f'''
            QPushButton {{
                font-size: 16px;
                background-color: {COLOR_BACKGROUND_INPUT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #28A745;
            }}
        ''')
        self.save_creds_button.setCursor(Qt.PointingHandCursor)
        self.save_creds_button.setToolTip("Save credentials")
        self.save_creds_button.clicked.connect(self._save_credentials)

        host_row.addWidget(host_label)
        host_row.addWidget(self.host_input, 2)
        host_row.addWidget(self.run_button)
        host_row.addWidget(self.stop_button)
        host_row.addWidget(self.save_creds_button)
        target_layout.addLayout(host_row)

        # Service and custom port row
        service_row = QHBoxLayout()
        service_label = QLabel("Service:")
        
        # Editable service combo
        self.service_input = StyledComboBox()
        self.service_input.setEditable(True)
        self.service_input.addItems(sorted(self.service_mappings.values()))  # Add actual service names
        self.service_input.setCurrentText("ssh")
        self.service_input.setMinimumHeight(36)
        
        # Custom port checkbox and input
        self.custom_port_check = QCheckBox("Custom Port:")
        self.custom_port_check.stateChanged.connect(self._on_custom_port_changed)
        
        self.custom_port_input = QLineEdit()
        self.custom_port_input.setPlaceholderText("Port")
        self.custom_port_input.setEnabled(False)
        self.custom_port_input.setMinimumHeight(36)
        self.custom_port_input.setMaximumWidth(80)
        self.custom_port_input.setStyleSheet(self.host_input.styleSheet())
        
        service_row.addWidget(service_label)
        service_row.addWidget(self.service_input, 2)
        service_row.addSpacing(20)
        service_row.addWidget(self.custom_port_check)
        service_row.addWidget(self.custom_port_input)
        target_layout.addLayout(service_row)

        return target_group

    def _create_credentials_section(self) -> QGroupBox:
        """Create credentials configuration section."""
        creds_group = QGroupBox("Credentials Configuration")
        creds_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLOR_BORDER};
                border-radius: 5px;
                margin-top: 1ex;
                color: {COLOR_TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)

        creds_layout = QVBoxLayout(creds_group)

        # Username row
        user_row = QHBoxLayout()
        user_label = QLabel("Username:")
        user_label.setMinimumWidth(80)
        
        self.single_user_radio = QRadioButton("Single")
        self.userlist_radio = QRadioButton("List")
        self.userlist_radio.setChecked(True)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setEnabled(False)
        self.username_input.setMinimumHeight(36)
        self.username_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 6px;
                font-size: 14px;
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLOR_BORDER_INPUT_FOCUSED};
            }}
        """)
        
        self.userlist_input = QLineEdit()
        self.userlist_input.setPlaceholderText("Select username wordlist...")
        self.userlist_input.setMinimumHeight(36)
        self.userlist_input.setStyleSheet(self.username_input.styleSheet())
        
        self.userlist_browse = QPushButton("📁")
        self.userlist_browse.setFixedSize(36, 36)
        self.userlist_browse.setCursor(Qt.PointingHandCursor)
        self.userlist_browse.clicked.connect(self._browse_userlist)
        self.userlist_browse.setStyleSheet(f"""
            QPushButton {{
                font-size: 16px;
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #4A4A4A;
            }}
        """)

        user_row.addWidget(user_label)
        user_row.addWidget(self.single_user_radio)
        user_row.addWidget(self.username_input, 1)
        user_row.addSpacing(10)
        user_row.addWidget(self.userlist_radio)
        user_row.addWidget(self.userlist_input, 1)
        user_row.addWidget(self.userlist_browse)
        creds_layout.addLayout(user_row)

        # Password row
        pass_row = QHBoxLayout()
        pass_label = QLabel("Password:")
        pass_label.setMinimumWidth(80)
        
        self.single_pass_radio = QRadioButton("Single")
        self.passlist_radio = QRadioButton("List")
        self.passlist_radio.setChecked(True)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEnabled(False)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(36)
        self.password_input.setStyleSheet(self.username_input.styleSheet())
        
        self.passlist_input = QLineEdit()
        self.passlist_input.setPlaceholderText("Select password wordlist...")
        self.passlist_input.setMinimumHeight(36)
        self.passlist_input.setStyleSheet(self.username_input.styleSheet())
        
        self.passlist_browse = QPushButton("📁")
        self.passlist_browse.setFixedSize(36, 36)
        self.passlist_browse.setCursor(Qt.PointingHandCursor)
        self.passlist_browse.clicked.connect(self._browse_passlist)
        self.passlist_browse.setStyleSheet(self.userlist_browse.styleSheet())

        pass_row.addWidget(pass_label)
        pass_row.addWidget(self.single_pass_radio)
        pass_row.addWidget(self.password_input, 1)
        pass_row.addSpacing(10)
        pass_row.addWidget(self.passlist_radio)
        pass_row.addWidget(self.passlist_input, 1)
        pass_row.addWidget(self.passlist_browse)
        creds_layout.addLayout(pass_row)

        # Radio button groups
        self.user_group = QButtonGroup()
        self.user_group.addButton(self.single_user_radio, 1)
        self.user_group.addButton(self.userlist_radio, 2)
        self.user_group.buttonClicked.connect(self._on_user_mode_changed)

        self.pass_group = QButtonGroup()
        self.pass_group.addButton(self.single_pass_radio, 1)
        self.pass_group.addButton(self.passlist_radio, 2)
        self.pass_group.buttonClicked.connect(self._on_pass_mode_changed)

        return creds_group

    def _create_advanced_section(self) -> QGroupBox:
        """Create advanced options section."""
        advanced_group = QGroupBox("Advanced Options")
        advanced_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLOR_BORDER};
                border-radius: 5px;
                margin-top: 1ex;
                color: {COLOR_TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)

        advanced_layout = QVBoxLayout(advanced_group)

        # Single row: Tasks, Wait, and all checkboxes
        options_row = QHBoxLayout()
        
        tasks_label = QLabel("Tasks:")
        self.tasks_spin = QSpinBox()
        self.tasks_spin.setRange(1, 64)
        self.tasks_spin.setValue(4)
        self.tasks_spin.setSuffix(" parallel")

        wait_label = QLabel("Wait:")
        self.wait_spin = QSpinBox()
        self.wait_spin.setRange(0, 100)
        self.wait_spin.setValue(0)
        self.wait_spin.setSuffix(" ms")

        options_row.addWidget(tasks_label)
        options_row.addWidget(self.tasks_spin)
        options_row.addSpacing(15)
        options_row.addWidget(wait_label)
        options_row.addWidget(self.wait_spin)
        options_row.addSpacing(20)
        
        # Checkboxes
        self.exit_on_first_check = QCheckBox("Stop after success")
        self.exit_on_first_check.setStyleSheet(f"font-size: 14px; color: {COLOR_TEXT_PRIMARY};")
        options_row.addWidget(self.exit_on_first_check)
        options_row.addSpacing(15)
        
        self.use_ssl_check = QCheckBox("Use SSL/TLS")
        self.use_ssl_check.setStyleSheet(f"font-size: 14px; color: {COLOR_TEXT_PRIMARY};")
        self.use_ssl_check.stateChanged.connect(self._on_ssl_changed)
        options_row.addWidget(self.use_ssl_check)
        options_row.addSpacing(15)
        
        self.use_proxy_check = QCheckBox("Use Proxy:")
        self.use_proxy_check.setStyleSheet(f"font-size: 14px; color: {COLOR_TEXT_PRIMARY};")
        self.use_proxy_check.stateChanged.connect(self._on_proxy_changed)
        options_row.addWidget(self.use_proxy_check)
        
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("http://127.0.0.1:8080")
        self.proxy_input.setEnabled(False)
        self.proxy_input.setMinimumHeight(32)
        self.proxy_input.setMaximumWidth(200)
        self.proxy_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 6px;
                font-size: 14px;
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
        """)
        options_row.addWidget(self.proxy_input)
        options_row.addStretch()
        advanced_layout.addLayout(options_row)

        # HTTP Form Options (conditional)
        self.http_form_group = self._create_http_form_section()
        self.http_form_group.hide()
        advanced_layout.addWidget(self.http_form_group)

        return advanced_group

    def _create_http_form_section(self) -> QGroupBox:
        """Create HTTP form options section."""
        http_group = QGroupBox("HTTP Form Options")
        http_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLOR_BORDER};
                border-radius: 5px;
                margin-top: 1ex;
                color: {COLOR_TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
        
        layout = QVBoxLayout(http_group)
        
        # Form path
        path_row = QHBoxLayout()
        path_label = QLabel("Form Path:")
        path_label.setMinimumWidth(100)
        self.http_form_path = QLineEdit()
        self.http_form_path.setPlaceholderText("/login.php")
        self.http_form_path.setMinimumHeight(32)
        path_row.addWidget(path_label)
        path_row.addWidget(self.http_form_path)
        layout.addLayout(path_row)
        
        # Username param
        user_row = QHBoxLayout()
        user_label = QLabel("Username Param:")
        user_label.setMinimumWidth(100)
        self.http_user_param = QLineEdit()
        self.http_user_param.setPlaceholderText("username=^USER^")
        self.http_user_param.setMinimumHeight(32)
        user_row.addWidget(user_label)
        user_row.addWidget(self.http_user_param)
        layout.addLayout(user_row)
        
        # Password param
        pass_row = QHBoxLayout()
        pass_label = QLabel("Password Param:")
        pass_label.setMinimumWidth(100)
        self.http_pass_param = QLineEdit()
        self.http_pass_param.setPlaceholderText("password=^PASS^")
        self.http_pass_param.setMinimumHeight(32)
        pass_row.addWidget(pass_label)
        pass_row.addWidget(self.http_pass_param)
        layout.addLayout(pass_row)
        
        # Failure string
        fail_row = QHBoxLayout()
        fail_label = QLabel("Failure String:")
        fail_label.setMinimumWidth(100)
        self.http_fail_string = QLineEdit()
        self.http_fail_string.setPlaceholderText("Login Failed")
        self.http_fail_string.setMinimumHeight(32)
        fail_row.addWidget(fail_label)
        fail_row.addWidget(self.http_fail_string)
        layout.addLayout(fail_row)
        
        return http_group

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

    def _update_command_display(self):
        """Update the command display field."""
        try:
            cmd_parts = ["hydra"]
            
            # Username
            if self.single_user_radio.isChecked():
                username = self.username_input.text().strip()
                cmd_parts.extend(["-l", username if username else "<username>"])
            else:
                userlist = self.userlist_input.text().strip()
                cmd_parts.extend(["-L", userlist if userlist else "<userlist>"])
            
            # Password
            if self.single_pass_radio.isChecked():
                password = self.password_input.text().strip()
                cmd_parts.extend(["-p", password if password else "<password>"])
            else:
                passlist = self.passlist_input.text().strip()
                cmd_parts.extend(["-P", passlist if passlist else "<passlist>"])
            
            # Exit on first success
            if self.exit_on_first_check.isChecked():
                cmd_parts.append("-f")
            
            # Custom port
            if self.custom_port_check.isChecked():
                custom_port = self.custom_port_input.text().strip()
                if custom_port:
                    cmd_parts.extend(["-s", custom_port])
            
            # Proxy
            if self.use_proxy_check.isChecked():
                # Proxy is handled via env var usually, but can be shown here for clarity
                # Hydra doesn't have a direct CLI arg for proxy URL in all versions, 
                # usually uses HYDRA_PROXY_HTTP env var.
                # However, we'll just show it as an env var export hint or ignore in display if not supported directly.
                # Let's not clutter command display with env vars, just keep it internal logic or show comment.
                pass

            # Target & Service logic
            host = self.host_input.text().strip()
            service = self.service_input.currentText().strip()
            
            # Check for HTTP form options
            http_module_opt = ""
            if 'http' in service.lower() and self.http_form_path.text().strip():
                # Construct form string
                path = self.http_form_path.text().strip()
                user_p = self.http_user_param.text().strip()
                pass_p = self.http_pass_param.text().strip()
                fail_s = self.http_fail_string.text().strip()
                
                # Format: "url:userparam:passparam:failstring"
                # Hydra expects: http-post-form "/login.php:user=^USER^:pass=^PASS^:F=incorrect"
                http_module_opt = f'"{path}:{user_p}:{pass_p}:{fail_s}"'
                
                # Update service name to form-based variant
                if 'post' in service.lower():
                    service = 'http-post-form'
                elif 'get' in service.lower():
                    service = 'http-get-form'
            
            # SSL/TLS toggle
            if self.use_ssl_check.isChecked() and service:
                if service == "http":
                    service = "https"
                elif service == "ftp":
                    service = "ftps"
                elif "http" in service and not service.startswith("https"):
                     service = service.replace("http", "https")
            
            target = f"{service if service else '<service>'}://{host if host else '<host>'}"
            cmd_parts.append(target)
            
            if http_module_opt:
                cmd_parts.append(http_module_opt)
            
            # Tasks
            cmd_parts.extend(["-t", str(self.tasks_spin.value())])
            
            # Wait
            if self.wait_spin.value() > 0:
                cmd_parts.extend(["-w", str(self.wait_spin.value())])
            
            self.command_display.setText(" ".join(cmd_parts))
        except Exception:
            pass

    def _build_hydra_command(self) -> list:
        """Build the actual hydra command for execution."""
        cmd = ["hydra"]
        
        # Username
        if self.single_user_radio.isChecked():
            cmd.extend(["-l", self.username_input.text().strip()])
        else:
            cmd.extend(["-L", self.userlist_input.text().strip()])
        
        # Password
        if self.single_pass_radio.isChecked():
            cmd.extend(["-p", self.password_input.text().strip()])
        else:
            cmd.extend(["-P", self.passlist_input.text().strip()])
        
        # Exit on first success
        if self.exit_on_first_check.isChecked():
            cmd.append("-f")
        
        # Custom port
        if self.custom_port_check.isChecked():
            custom_port = self.custom_port_input.text().strip()
            if custom_port:
                cmd.extend(["-s", custom_port])
        
        # Target logic
        host = self.host_input.text().strip()
        service = self.service_input.currentText().strip()
        
        # Check for HTTP form options
        http_module_opt = ""
        if 'http' in service.lower() and self.http_form_path.text().strip():
            # Construct form string
            path = self.http_form_path.text().strip()
            user_p = self.http_user_param.text().strip()
            pass_p = self.http_pass_param.text().strip()
            fail_s = self.http_fail_string.text().strip()
            
            # Hydra expects: http-post-form "/login.php:user=^USER^:pass=^PASS^:F=incorrect"
            http_module_opt = f'"{path}:{user_p}:{pass_p}:{fail_s}"'
            
            # Update service name
            if 'post' in service.lower():
                service = 'http-post-form'
            elif 'get' in service.lower():
                service = 'http-get-form'
        
        # SSL/TLS
        if self.use_ssl_check.isChecked():
            if service == "http":
                service = "https"
            elif service == "ftp":
                service = "ftps"
            elif "http" in service and not service.startswith("https"):
                service = service.replace("http", "https")
        
        cmd.append(f"{service}://{host}")
        
        if http_module_opt:
            cmd.append(http_module_opt)
        
        # Tasks
        cmd.extend(["-t", str(self.tasks_spin.value())])
        
        # Wait
        if self.wait_spin.value() > 0:
            cmd.extend(["-w", str(self.wait_spin.value())])
        
        # Use proxy if enabled (set via environment variable, not arg, but we can try setting it prior if using subprocess env)
        # Note: Hydra uses HYDRA_PROXY_HTTP or HYDRA_PROXY_CONNECT.
        # Since we use QProcess/subprocess, we should set this in the environment of the worker.
        # However, _build_hydra_command returns a list of args.
        # We'll need to handle the env var in the execution method.
        
        # Output file
        if self._logs_dir:
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
        self._discovered_creds.clear()
        self._is_stopping = False

        try:
            # Create directories
            base_dir = create_target_dirs(f"hydra_{host}")
            self._logs_dir = os.path.join(base_dir, "Logs")
            os.makedirs(self._logs_dir, exist_ok=True)

            self._info(f"Starting Hydra brute force attack")
            self._info(f"Target: {host}")
            self._info(f"Service: {self.service_input.currentText()}")
            if self.custom_port_check.isChecked():
                self._info(f"Custom Port: {self.custom_port_input.text().strip()}")
            self.output.append("")

            # Build command
            cmd = self._build_hydra_command()
            self._info(f"Command: {' '.join(cmd)}")
            self.output.append("")

            # Start worker
            self.worker = ProcessWorker(cmd)
            
            # Set proxy environment variable if enabled
            if self.use_proxy_check.isChecked():
                proxy_url = self.proxy_input.text().strip()
                if proxy_url:
                    env = os.environ.copy()
                    env["HYDRA_PROXY_HTTP"] = proxy_url
                    # Also set connect proxy just in case, though usually one is sufficient depending on mode
                    env["HYDRA_PROXY_CONNECT"] = proxy_url
                    self.worker.process.setProcessEnvironment(env)
            
            self.worker.output_ready.connect(self._on_output)
            self.worker.finished.connect(self._on_finished)
            self.worker.error.connect(self._error)

            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate

            self.worker.start()

        except Exception as e:
            self._error(f"Failed to start attack: {str(e)}")

    def _stop_attack(self):
        """Stop the attack safely."""
        try:
            if self.worker and self.worker.isRunning():
                self._is_stopping = True
                self.worker.stop()
                self.worker.wait(1000)  # Wait up to 1 second
                self._info("Attack stopped by user.")
        except Exception:
            pass
        finally:
            try:
                self.run_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.progress_bar.setVisible(False)
            except Exception:
                pass
            self.worker = None

    def stop_scan(self):
        """Alias for _stop_attack for consistency with other tools."""
        self._stop_attack()

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
