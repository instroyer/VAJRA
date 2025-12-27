import os
import subprocess
from datetime import datetime

from PySide6.QtCore import QObject, Signal, Qt, QRect, QThread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QLineEdit, QGroupBox, QMessageBox, QSplitter, QCompleter, QApplication, QCheckBox,
    QFileDialog, QProgressBar, QTextEdit, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QRadioButton, QButtonGroup, QGroupBox
)

from modules.bases import ToolBase, ToolCategory
from ui.main_window import BaseToolView
from ui.worker import ProcessWorker
from core.tgtinput import parse_targets
from core.fileops import create_target_dirs
from ui.styles import (
    TARGET_INPUT_STYLE, COMBO_BOX_STYLE,
    COLOR_BACKGROUND_INPUT, COLOR_TEXT_PRIMARY, COLOR_BORDER, COLOR_BORDER_INPUT_FOCUSED,
    StyledComboBox  # Import from centralized styles
)


# ==============================
# Hydra Tool
# ==============================

class HydraTool(ToolBase):
    @property
    def name(self) -> str:
        return "Hydra"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CRACKER

    def get_widget(self, main_window: QWidget) -> QWidget:
        return HydraToolView(main_window=main_window)

class HydraToolView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._is_stopping = False
        self._scan_complete_added = False

        # Hydra service mappings
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
            "Cisco Enable": "cisco-enable",
            "CVS": "cvs",
            "SVN": "svn",
            "Firebird": "firebird",
            "AFP": "afp",
            "ICQ": "icq",
            "IRC": "irc",
            "SAP R/3": "sapr3",
            "Teamspeak": "teamspeak",
            "PCAnywhere": "pcanywhere"
        }

        self._build_custom_ui()

    def _build_custom_ui(self):
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create splitter
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

        # Create control panel
        control_panel = QWidget()
        control_panel.setStyleSheet(f"""
            QWidget {{
                background-color: #1C1C1C;
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
        """)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        # Header
        header = QLabel("Cracker › Hydra")
        header.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        control_layout.addWidget(header)

        # Command display (like nmap)
        command_label = QLabel("Command:")
        command_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 500;")
        self.command_display = QLineEdit()
        self.command_display.setReadOnly(True)
        self.command_display.setStyleSheet(TARGET_INPUT_STYLE)
        self.command_display.setPlaceholderText("Configure options to generate command...")
        
        command_layout = QVBoxLayout()
        command_layout.addWidget(command_label)
        command_layout.addWidget(self.command_display)
        control_layout.addLayout(command_layout)

        # Target configuration with Start/Stop buttons
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

        # Target host with buttons
        host_layout = QHBoxLayout()
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

        # Port with dropdown and input
        port_label = QLabel("Port:")
        self.port_combo = StyledComboBox()
        self.port_combo.addItems(["22", "80", "443", "3306", "5432", "3389", "445", "21"])
        self.port_combo.setEditable(True)
        self.port_combo.setCurrentText("22")
        self.port_combo.setMinimumHeight(36)
        self.port_combo.setMaximumWidth(100)

        # Start button (icon only)
        self.run_button = QPushButton("▶")
        self.run_button.setFixedSize(36, 36)
        self.run_button.setCursor(Qt.PointingHandCursor)
        self.run_button.setToolTip("Start Brute Force")
        self.run_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #FF6B35;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #E55A2B;
            }}
            QPushButton:pressed {{
                background-color: #CC4F26;
            }}
            QPushButton:disabled {{
                background-color: #555555;
                color: #999999;
            }}
        """)
        self.run_button.clicked.connect(self.run_scan)

        # Stop button (icon only)
        self.stop_button = QPushButton("⏹")
        self.stop_button.setFixedSize(36, 36)
        self.stop_button.setCursor(Qt.PointingHandCursor)
        self.stop_button.setToolTip("Stop Brute Force")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #DC3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #C82333;
            }}
            QPushButton:pressed {{
                background-color: #BD2130;
            }}
            QPushButton:disabled {{
                background-color: #555555;
                color: #999999;
            }}
        """)
        self.stop_button.clicked.connect(self.stop_scan)

        host_layout.addWidget(host_label)
        host_layout.addWidget(self.host_input, 2)
        host_layout.addSpacing(10)
        host_layout.addWidget(port_label)
        host_layout.addWidget(self.port_combo)
        host_layout.addWidget(self.run_button)
        host_layout.addWidget(self.stop_button)
        target_layout.addLayout(host_layout)

        control_layout.addWidget(target_group)

        # Service configuration
        service_group = QGroupBox("Service Configuration")
        service_group.setStyleSheet(f"""
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

        service_layout = QVBoxLayout(service_group)

        # Service selection
        service_sel_layout = QHBoxLayout()
        service_label = QLabel("Service:")
        self.service_combo = StyledComboBox()
        self.service_combo.addItems(sorted(self.service_mappings.keys()))
        self.service_combo.setCurrentText("SSH")
        self.service_combo.currentTextChanged.connect(self._on_service_changed)

        service_sel_layout.addWidget(service_label)
        service_sel_layout.addWidget(self.service_combo)
        service_layout.addLayout(service_sel_layout)

        # Service-specific options
        self.service_options_layout = QVBoxLayout()

        # HTTP options (initially hidden)
        self.http_options_widget = QWidget()
        http_layout = QVBoxLayout(self.http_options_widget)
        http_layout.setContentsMargins(0, 0, 0, 0)

        http_url_layout = QHBoxLayout()
        http_url_label = QLabel("URL Path:")
        self.http_url_input = QLineEdit()
        self.http_url_input.setPlaceholderText("/login.php")
        self.http_url_input.setText("/")
        http_url_layout.addWidget(http_url_label)
        http_url_layout.addWidget(self.http_url_input)

        http_method_layout = QHBoxLayout()
        http_method_label = QLabel("HTTP Method:")
        self.http_method_combo = StyledComboBox()
        self.http_method_combo.addItems(["GET", "POST"])
        self.http_method_combo.setCurrentText("POST")
        http_method_layout.addWidget(http_method_label)
        http_method_layout.addWidget(self.http_method_combo)

        http_layout.addLayout(http_url_layout)
        http_layout.addLayout(http_method_layout)
        self.http_options_widget.hide()

        self.service_options_layout.addWidget(self.http_options_widget)
        service_layout.addLayout(self.service_options_layout)



        # Credentials configuration
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

        # Username and Password options on one line
        cred_options_layout = QHBoxLayout()

        # Username options
        user_group = QGroupBox("Username Options")
        user_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #555; border-radius: 3px; margin-top: 0.5ex; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        user_layout = QVBoxLayout(user_group)
        user_layout.setSpacing(15)  # Increased spacing between elements
        user_layout.setContentsMargins(10, 20, 10, 10)  # Increased top margin for more spacing from title

        # Username input type
        user_type_layout = QHBoxLayout()
        user_type_layout.setSpacing(20)  # Add spacing between radio buttons
        self.single_user_radio = QRadioButton("Single Username:")
        self.userlist_radio = QRadioButton("Username List:")
        self.userlist_radio.setChecked(True)

        user_type_layout.addWidget(self.single_user_radio)
        user_type_layout.addWidget(self.userlist_radio)
        user_type_layout.addStretch()
        user_layout.addLayout(user_type_layout)

        # Username input
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter single username")
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
        user_layout.addWidget(self.username_input)

        # Username list file
        userlist_layout = QHBoxLayout()
        self.userlist_input = QLineEdit()
        self.userlist_input.setPlaceholderText("Select username wordlist...")
        self.userlist_input.setMinimumHeight(36)
        self.userlist_input.setStyleSheet(f"""
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

        self.userlist_browse_button = QPushButton("📁")
        self.userlist_browse_button.setFixedSize(36, 36)
        self.userlist_browse_button.setCursor(Qt.PointingHandCursor)
        self.userlist_browse_button.clicked.connect(self._browse_userlist)
        self.userlist_browse_button.setStyleSheet(f"""
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
            QPushButton:pressed {{
                background-color: #2A2A2A;
            }}
        """)

        userlist_layout.addWidget(self.userlist_input)
        userlist_layout.addWidget(self.userlist_browse_button)
        user_layout.addLayout(userlist_layout)

        cred_options_layout.addWidget(user_group, 1)
        cred_options_layout.addSpacing(20)  # Add gap between Username and Password boxes

        # Password options
        pass_group = QGroupBox("Password Options")
        pass_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #555; border-radius: 3px; margin-top: 0.5ex; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        pass_layout = QVBoxLayout(pass_group)
        pass_layout.setSpacing(15)  # Increased spacing between elements
        pass_layout.setContentsMargins(10, 20, 10, 10)  # Increased top margin for more spacing from title

        # Password input type
        pass_type_layout = QHBoxLayout()
        pass_type_layout.setSpacing(20)  # Add spacing between radio buttons
        self.single_pass_radio = QRadioButton("Single Password:")
        self.passlist_radio = QRadioButton("Password List:")
        self.passlist_radio.setChecked(True)

        pass_type_layout.addWidget(self.single_pass_radio)
        pass_type_layout.addWidget(self.passlist_radio)
        pass_type_layout.addStretch()
        pass_layout.addLayout(pass_type_layout)

        # Password input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter single password")
        self.password_input.setEnabled(False)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(36)
        self.password_input.setStyleSheet(f"""
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
        pass_layout.addWidget(self.password_input)

        # Password list file
        passlist_layout = QHBoxLayout()
        self.passlist_input = QLineEdit()
        self.passlist_input.setPlaceholderText("Select password wordlist...")
        self.passlist_input.setMinimumHeight(36)
        self.passlist_input.setStyleSheet(f"""
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

        self.passlist_browse_button = QPushButton("📁")
        self.passlist_browse_button.setFixedSize(36, 36)
        self.passlist_browse_button.setCursor(Qt.PointingHandCursor)
        self.passlist_browse_button.clicked.connect(self._browse_passlist)
        self.passlist_browse_button.setStyleSheet(f"""
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
            QPushButton:pressed {{
                background-color: #2A2A2A;
            }}
        """)

        passlist_layout.addWidget(self.passlist_input)
        passlist_layout.addWidget(self.passlist_browse_button)
        pass_layout.addLayout(passlist_layout)

        cred_options_layout.addWidget(pass_group, 1)
        creds_layout.addLayout(cred_options_layout)

        control_layout.addWidget(creds_group)

        # Advanced options
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

        advanced_layout = QHBoxLayout(advanced_group)

        # Tasks/threads
        tasks_label = QLabel("Tasks:")
        self.tasks_spin = QSpinBox()
        self.tasks_spin.setRange(1, 64)
        self.tasks_spin.setValue(4)
        self.tasks_spin.setSuffix(" parallel")

        # Timeout
        timeout_label = QLabel("Timeout:")
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" sec")

        # Wait between attempts
        wait_label = QLabel("Wait:")
        self.wait_spin = QSpinBox()
        self.wait_spin.setRange(0, 100)
        self.wait_spin.setValue(0)
        self.wait_spin.setSuffix(" ms")

        advanced_layout.addWidget(tasks_label)
        advanced_layout.addWidget(self.tasks_spin)
        advanced_layout.addSpacing(20)
        advanced_layout.addWidget(timeout_label)
        advanced_layout.addWidget(self.timeout_spin)
        advanced_layout.addSpacing(20)
        advanced_layout.addWidget(wait_label)
        advanced_layout.addWidget(self.wait_spin)
        advanced_layout.addStretch()

        control_layout.addWidget(advanced_group)

        # Command display
        command_label = QLabel("Command")
        command_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        self.command_input = QLineEdit()
        self.command_input.setReadOnly(False)
        self.command_input.setStyleSheet(f"""
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

        control_layout.addWidget(command_label)
        control_layout.addWidget(self.command_input)



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

        # Main output tab
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 5px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }}
        """)

        # Results table tab
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

        # Radio button groups
        self.user_radio_group = QButtonGroup()
        self.user_radio_group.addButton(self.single_user_radio, 1)
        self.user_radio_group.addButton(self.userlist_radio, 2)
        self.user_radio_group.buttonClicked.connect(self._on_user_radio_changed)

        self.pass_radio_group = QButtonGroup()
        self.pass_radio_group.addButton(self.single_pass_radio, 1)
        self.pass_radio_group.addButton(self.passlist_radio, 2)
        self.pass_radio_group.buttonClicked.connect(self._on_pass_radio_changed)

        # Connect signals
        for widget in [self.host_input, self.port_combo, self.service_combo, self.username_input,
                      self.userlist_input, self.password_input, self.passlist_input,
                      self.tasks_spin, self.timeout_spin, self.wait_spin,
                      self.http_url_input, self.http_method_combo]:
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(self.update_command)
            elif isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(self.update_command)
            elif isinstance(widget, QSpinBox):
                widget.valueChanged.connect(self.update_command)

    def _info(self, message):
        """Add info message to output."""
        self.output.appendPlainText(f"[INFO] {message}")

    def _error(self, message):
        """Add error message to output."""
        self.output.appendPlainText(f"[ERROR] {message}")

    def _section(self, title):
        """Add section header to output."""
        self.output.appendPlainText(f"\n===== {title} =====")

    def _notify(self, message):
        """Show notification (placeholder for now)."""
        self._info(f"Notification: {message}")

    def _on_scan_completed(self):
        """Handle scan completion."""
        pass

    def _on_service_changed(self):
        """Handle service selection change."""
        service = self.service_combo.currentText()
        is_http = "HTTP" in service

        self.http_options_widget.setVisible(is_http)
        if is_http:
            # Set default port based on HTTP/HTTPS
            if "HTTPS" in service:
                self.port_combo.setCurrentText("443")
            else:
                self.port_combo.setCurrentText("80")
        else:
            # Set default ports for other services
            default_ports = {
                "SSH": "22", "FTP": "21", "Telnet": "23", "SMTP": "25", "POP3": "110",
                "IMAP": "143", "SMB": "445", "LDAP": "389", "MySQL": "3306", "RDP": "3389"
            }
            self.port_combo.setCurrentText(str(default_ports.get(service, "22")))

        self.update_command()

    def _on_user_radio_changed(self):
        """Handle username radio button change."""
        is_single = self.single_user_radio.isChecked()
        self.username_input.setEnabled(is_single)
        self.userlist_input.setEnabled(not is_single)
        self.userlist_browse_button.setEnabled(not is_single)
        self.update_command()

    def _on_pass_radio_changed(self):
        """Handle password radio button change."""
        is_single = self.single_pass_radio.isChecked()
        self.password_input.setEnabled(is_single)
        self.passlist_input.setEnabled(not is_single)
        self.passlist_browse_button.setEnabled(not is_single)
        self.update_command()

    def _browse_userlist(self):
        """Browse for username wordlist."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Username Wordlist", "",
            "All Files (*);;Text Files (*.txt);;Wordlist Files (*.lst *.dict)"
        )
        if file_path:
            self.userlist_input.setText(file_path)
            self.update_command()

    def _browse_passlist(self):
        """Browse for password wordlist."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Password Wordlist", "",
            "All Files (*);;Text Files (*.txt);;Wordlist Files (*.lst *.dict)"
        )
        if file_path:
            self.passlist_input.setText(file_path)
            self.update_command()

    def update_command(self):
        try:
            host = self.host_input.text().strip() or "<host>"
            port = self.port_combo.currentText().strip() or "22"
            service = self.service_mappings.get(self.service_combo.currentText(), "ssh")

            cmd_parts = ["hydra"]

            # Username configuration
            if self.single_user_radio.isChecked():
                username = self.username_input.text().strip()
                if username:
                    cmd_parts.extend(["-l", username])
                else:
                    cmd_parts.extend(["-l", "<username>"])
            else:
                userlist = self.userlist_input.text().strip()
                if userlist:
                    cmd_parts.extend(["-L", userlist])
                else:
                    cmd_parts.extend(["-L", "<userlist>"])

            # Password configuration
            if self.single_pass_radio.isChecked():
                password = self.password_input.text().strip()
                if password:
                    cmd_parts.extend(["-p", password])
                else:
                    cmd_parts.extend(["-p", "<password>"])
            else:
                passlist = self.passlist_input.text().strip()
                if passlist:
                    cmd_parts.extend(["-P", passlist])
                else:
                    cmd_parts.extend(["-P", "<passlist>"])

            # Service and target
            cmd_parts.append(service + "://" + host + ":" + port)

            # Tasks
            cmd_parts.extend(["-t", str(self.tasks_spin.value())])

            # Timeout
            cmd_parts.extend(["-T", str(self.timeout_spin.value())])

            # Wait
            if self.wait_spin.value() > 0:
                cmd_parts.extend(["-w", str(self.wait_spin.value())])

            # HTTP specific options
            if "http" in service:
                method = self.http_method_combo.currentText().lower()
                url_path = self.http_url_input.text().strip()
                if url_path:
                    cmd_parts.extend([method + "-form", url_path])

            cmd = " ".join(cmd_parts)
            if hasattr(self, 'command_display'):
                self.command_display.setText(cmd)
        except AttributeError:
            pass

    def run_scan(self):
        """Start Hydra brute force attack."""
        host = self.host_input.text().strip()
        if not host:
            QMessageBox.warning(self, "No Target", "Please enter a target host/IP.")
            return

        # Check username configuration
        if self.single_user_radio.isChecked():
            if not self.username_input.text().strip():
                QMessageBox.warning(self, "No Username", "Please enter a username.")
                return
        else:
            if not self.userlist_input.text().strip():
                QMessageBox.warning(self, "No Username List", "Please select a username wordlist.")
                return
            if not os.path.exists(self.userlist_input.text().strip()):
                QMessageBox.warning(self, "Username List Not Found", f"Username list file does not exist: {self.userlist_input.text().strip()}")
                return

        # Check password configuration
        if self.single_pass_radio.isChecked():
            if not self.password_input.text().strip():
                QMessageBox.warning(self, "No Password", "Please enter a password.")
                return
        else:
            if not self.passlist_input.text().strip():
                QMessageBox.warning(self, "No Password List", "Please select a password wordlist.")
                return
            if not os.path.exists(self.passlist_input.text().strip()):
                QMessageBox.warning(self, "Password List Not Found", f"Password list file does not exist: {self.passlist_input.text().strip()}")
                return

        self.output.clear()
        self.results_table.setRowCount(0)
        self._is_stopping = False
        self._scan_complete_added = False

        try:
            # Create target directory
            base_dir = create_target_dirs(f"hydra_{host}")
            logs_dir = os.path.join(base_dir, "Logs")
            os.makedirs(logs_dir, exist_ok=True)

            self._info(f"Starting Hydra brute force attack")
            self._info(f"Target: {host}:{self.port_combo.currentText()}")
            self._info(f"Service: {self.service_combo.currentText()}")
            self.output.appendPlainText("")

            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress

            # Build hydra command
            cmd = ["hydra"]

            # Username configuration
            if self.single_user_radio.isChecked():
                cmd.extend(["-l", self.username_input.text().strip()])
            else:
                cmd.extend(["-L", self.userlist_input.text().strip()])

            # Password configuration
            if self.single_pass_radio.isChecked():
                cmd.extend(["-p", self.password_input.text().strip()])
            else:
                cmd.extend(["-P", self.passlist_input.text().strip()])

            # Service and target
            service = self.service_mappings.get(self.service_combo.currentText(), "ssh")
            target = f"{service}://{host}:{self.port_combo.currentText()}"
            cmd.append(target)

            # Tasks
            cmd.extend(["-t", str(self.tasks_spin.value())])

            # Timeout
            cmd.extend(["-T", str(self.timeout_spin.value())])

            # Wait
            if self.wait_spin.value() > 0:
                cmd.extend(["-w", str(self.wait_spin.value())])

            # HTTP specific options
            if "http" in service:
                method = self.http_method_combo.currentText().lower()
                url_path = self.http_url_input.text().strip()
                if url_path:
                    cmd.extend([f"{method}-form", url_path])

            # Output file
            output_file = os.path.join(logs_dir, "hydra_results.txt")
            cmd.extend(["-o", output_file])

            self._info(f"Command: {' '.join(cmd)}")
            self.output.appendPlainText("")

            self.worker = ProcessWorker(cmd)
            self.worker.output_ready.connect(self._on_output)
            self.worker.finished.connect(self._on_finished)
            self.worker.error.connect(self._error)

            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.worker.start()

        except Exception as e:
            self._error(f"Failed to start brute force: {str(e)}")

    def _on_output(self, line):
        """Process Hydra output."""
        self.output.appendPlainText(line)

        # Parse successful logins and add to table
        # Hydra outputs successful logins like: [port][service] host:port LOGIN - PASSWORD
        if "LOGIN -" in line and "PASSWORD" in line:
            try:
                # Extract login info from Hydra output
                parts = line.split("LOGIN - ")
                if len(parts) == 2:
                    host_info = parts[0].strip()
                    password = parts[1].split()[0].strip()  # Get password before other text

                    # Extract username from the line (usually after host:port)
                    host_parts = host_info.split()
                    if len(host_parts) >= 2:
                        username = host_parts[-1]  # Usually the last part before LOGIN

                        # Add to results table
                        row_count = self.results_table.rowCount()
                        self.results_table.insertRow(row_count)
                        self.results_table.setItem(row_count, 0, QTableWidgetItem(self.host_input.text().strip()))
                        self.results_table.setItem(row_count, 1, QTableWidgetItem(username))
                        self.results_table.setItem(row_count, 2, QTableWidgetItem(password))
            except:
                pass

    def _on_finished(self):
        """Handle brute force completion."""
        self.progress_bar.setVisible(False)
        self._on_scan_completed()

        if self._is_stopping:
            return

        # Save results
        try:
            host = self.host_input.text().strip()
            base_dir = create_target_dirs(f"hydra_{host}")
            logs_dir = os.path.join(base_dir, "Logs")

            # Save results table to file
            results_file = os.path.join(logs_dir, "cracked_credentials.txt")
            with open(results_file, 'w') as f:
                f.write("Hydra Brute Force Results\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Target: {host}:{self.port_combo.currentText()}\n")
                f.write(f"Service: {self.service_combo.currentText()}\n\n")

                f.write("Cracked Credentials:\n")
                f.write("-" * 80 + "\n")
                for row in range(self.results_table.rowCount()):
                    host_item = self.results_table.item(row, 0)
                    user_item = self.results_table.item(row, 1)
                    pass_item = self.results_table.item(row, 2)
                    if host_item and user_item and pass_item:
                        f.write(f"Host: {host_item.text()}\n")
                        f.write(f"Username: {user_item.text()}\n")
                        f.write(f"Password: {pass_item.text()}\n")
                        f.write("-" * 40 + "\n")

            self._info(f"Results saved to: {results_file}")

        except Exception as e:
            self._error(f"Failed to save results: {str(e)}")

        if not self._scan_complete_added:
            self._section("Brute Force Complete")
            self._scan_complete_added = True

    def stop_scan(self):
        """Stop the brute force attack."""
        if self.worker and self.worker.is_running:
            self._is_stopping = True
            self.worker.stop()
            self._info("Brute force stopped.")
        self._on_scan_completed()
        self.progress_bar.setVisible(False)

    def copy_results_to_clipboard(self):
        """Copy brute force results to clipboard."""
        results_text = self.output.toPlainText()
        if results_text.strip():
            QApplication.clipboard().setText(results_text)
            self._notify("Results copied to clipboard.")
        else:
            self._notify("No results to copy.")
