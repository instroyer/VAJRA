# =============================================================================
# modules/nikto.py
#
# Professional Nikto Vulnerability Scanner GUI
# Comprehensive web vulnerability scanning with all major Nikto features
# =============================================================================

import os
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QCheckBox, QComboBox,
    QTextEdit, QGridLayout, QSplitter, QTabWidget, QMessageBox
)
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from ui.worker import ProcessWorker, StoppableToolMixin
from core.fileops import create_target_dirs
from ui.styles import (
    COLOR_BACKGROUND_INPUT, COLOR_BACKGROUND_PRIMARY, COLOR_TEXT_PRIMARY, COLOR_BORDER,
    COLOR_BORDER_INPUT_FOCUSED, LABEL_STYLE, StyledSpinBox,
    TOOL_HEADER_STYLE, TOOL_VIEW_STYLE, RUN_BUTTON_STYLE, STOP_BUTTON_STYLE,
    CopyButton
)


class NiktoTool(ToolBase):
    """Professional Nikto vulnerability scanner tool."""

    @property
    def name(self) -> str:
        return "Nikto"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.VULNERABILITY_SCANNER

    def get_widget(self, main_window):
        return NiktoToolView(main_window=main_window)


class NiktoToolView(QWidget, StoppableToolMixin):
    """Nikto vulnerability scanner interface."""

    def __init__(self, main_window=None):
        super().__init__()
        self.init_stoppable()
        self.main_window = main_window
        self.base_dir = None
        self._build_ui()

    def _build_ui(self):
        """Build complete custom UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

        # ==================== CONTROL PANEL ====================
        control_panel = QWidget()
        control_panel.setStyleSheet(TOOL_VIEW_STYLE)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        # Header
        header = QLabel("VULNERABILITY_SCANNER › Nikto")
        header.setStyleSheet(TOOL_HEADER_STYLE)
        control_layout.addWidget(header)

        # Target URL
        target_label = QLabel("Target URL")
        target_label.setStyleSheet(LABEL_STYLE)
        control_layout.addWidget(target_label)

        target_row = QHBoxLayout()
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("http://example.com")
        self.target_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                min-height: 22px;
            }}
            QLineEdit:focus {{ border: 1px solid {COLOR_BORDER_INPUT_FOCUSED}; }}
        """)
        self.target_input.textChanged.connect(self.update_command)

        self.run_button = QPushButton("RUN")
        self.run_button.setStyleSheet(RUN_BUTTON_STYLE)
        self.run_button.clicked.connect(self.run_scan)
        self.run_button.setCursor(Qt.PointingHandCursor)

        self.stop_button = QPushButton("■")
        self.stop_button.setStyleSheet(STOP_BUTTON_STYLE)
        self.stop_button.clicked.connect(self.stop_scan)
        self.stop_button.setEnabled(False)
        self.stop_button.setCursor(Qt.PointingHandCursor)

        target_row.addWidget(self.target_input)
        target_row.addWidget(self.run_button)
        target_row.addWidget(self.stop_button)
        control_layout.addLayout(target_row)

        # Command preview
        command_label = QLabel("Command")
        command_label.setStyleSheet(LABEL_STYLE)
        control_layout.addWidget(command_label)

        self.command_input = QLineEdit()
        self.command_input.setStyleSheet(self.target_input.styleSheet())
        control_layout.addWidget(self.command_input)

        # ==================== TABBED CONFIGURATION ====================
        config_group = QGroupBox("⚙️ Scan Configuration")
        config_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLOR_BORDER};
                border-radius: 5px;
                margin-top: 1ex;
                color: {COLOR_TEXT_PRIMARY};
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
        config_layout = QVBoxLayout(config_group)
        config_layout.setContentsMargins(5, 15, 5, 5)
        config_layout.setSpacing(0)

        self.config_tabs = QTabWidget()
        self.config_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                background-color: {COLOR_BACKGROUND_INPUT};
            }}
            QTabBar::tab {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background-color: #1777d1;
                color: white;
                font-weight: bold;
            }}
            QTabBar::tab:hover {{
                background-color: #4A4A4A;
            }}
        """)

        # ===== TAB 1: BASIC SCAN =====
        basic_tab = QWidget()
        basic_layout = QGridLayout(basic_tab)
        basic_layout.setContentsMargins(10, 10, 10, 10)
        basic_layout.setSpacing(10)
        basic_layout.setColumnStretch(1, 1)
        basic_layout.setColumnStretch(3, 1)

        # Port
        port_label = QLabel("Port:")
        port_label.setStyleSheet(LABEL_STYLE)
        port_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("80 or 443")
        self.port_input.setStyleSheet(self.target_input.styleSheet())
        self.port_input.textChanged.connect(self.update_command)

        # SSL/HTTPS
        self.ssl_check = QCheckBox("Force SSL")
        self.ssl_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px;")
        self.ssl_check.stateChanged.connect(self.update_command)

        self.followredirects_check = QCheckBox("Follow Redirects")
        self.followredirects_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px;")
        self.followredirects_check.stateChanged.connect(self.update_command)

        # Virtual Host
        vhost_label = QLabel("Virtual Host:")
        vhost_label.setStyleSheet(LABEL_STYLE)
        vhost_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.vhost_input = QLineEdit()
        self.vhost_input.setPlaceholderText("Custom Host header")
        self.vhost_input.setStyleSheet(self.target_input.styleSheet())
        self.vhost_input.textChanged.connect(self.update_command)

        # Timeout
        timeout_label = QLabel("Timeout (s):")
        timeout_label.setStyleSheet(LABEL_STYLE)
        timeout_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.timeout_spin = StyledSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(10)
        self.timeout_spin.setSuffix(" s")
        self.timeout_spin.valueChanged.connect(self.update_command)

        # Max Time
        maxtime_label = QLabel("Max Time:")
        maxtime_label.setStyleSheet(LABEL_STYLE)
        maxtime_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.maxtime_input = QLineEdit()
        self.maxtime_input.setPlaceholderText("e.g., 1h, 60m, 3600s")
        self.maxtime_input.setStyleSheet(self.target_input.styleSheet())
        self.maxtime_input.textChanged.connect(self.update_command)

        # Display Options
        display_label = QLabel("Display:")
        display_label.setStyleSheet(LABEL_STYLE)
        display_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        display_layout = QHBoxLayout()
        self.display_verbose = QCheckBox("Verbose")
        self.display_verbose.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
        self.display_verbose.stateChanged.connect(self.update_command)
        
        self.display_debug = QCheckBox("Debug")
        self.display_debug.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
        self.display_debug.stateChanged.connect(self.update_command)

        display_layout.addWidget(self.display_verbose)
        display_layout.addWidget(self.display_debug)
        display_layout.addStretch()

        # Add to grid
        basic_layout.addWidget(port_label, 0, 0)
        basic_layout.addWidget(self.port_input, 0, 1)
        basic_layout.addWidget(self.ssl_check, 0, 2)
        basic_layout.addWidget(self.followredirects_check, 0, 3)
        basic_layout.addWidget(vhost_label, 1, 0)
        basic_layout.addWidget(self.vhost_input, 1, 1, 1, 3)
        basic_layout.addWidget(timeout_label, 2, 0)
        basic_layout.addWidget(self.timeout_spin, 2, 1)
        basic_layout.addWidget(maxtime_label, 2, 2)
        basic_layout.addWidget(self.maxtime_input, 2, 3)
        basic_layout.addWidget(display_label, 3, 0)
        basic_layout.addLayout(display_layout, 3, 1, 1, 3)
        basic_layout.setRowStretch(4, 1)

        self.config_tabs.addTab(basic_tab, "Basic")

        # ===== TAB 2: SCAN OPTIONS =====
        scan_tab = QWidget()
        scan_layout = QVBoxLayout(scan_tab)
        scan_layout.setContentsMargins(10, 10, 10, 10)
        scan_layout.setSpacing(10)

        # Tuning options (checkboxes)
        tuning_label = QLabel("Scan Tuning (select tests to run):")
        tuning_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: bold; font-size: 14px;")
        scan_layout.addWidget(tuning_label)

        # Create tuning checkboxes in grid
        tuning_grid = QGridLayout()
        tuning_grid.setSpacing(8)

        self.tuning_checks = {}
        tuning_options = [
            ("1", "Interesting File / Seen in logs"),
            ("2", "Misconfiguration / Default File"),
            ("3", "Information Disclosure"),
            ("4", "Injection (XSS/Script/HTML)"),
            ("5", "Remote File Retrieval - Inside Web Root"),
            ("6", "Denial of Service"),
            ("7", "Remote File Retrieval - Server Wide"),
            ("8", "Command Execution / Remote Shell"),
            ("9", "SQL Injection"),
            ("0", "File Upload"),
            ("a", "Authentication Bypass"),
            ("b", "Software Identification"),
            ("c", "Remote Source Inclusion"),
            ("d", "WebService"),
            ("e", "Administrative Console"),
        ]

        row, col = 0, 0
        for code, label in tuning_options:
            check = QCheckBox(f"{code} - {label}")
            check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
            check.stateChanged.connect(self.update_command)
            self.tuning_checks[code] = check
            tuning_grid.addWidget(check, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

        scan_layout.addLayout(tuning_grid)

        # Additional scan options
        scan_options_grid = QGridLayout()
        scan_options_grid.setSpacing(10)

        self.no404_check = QCheckBox("No 404 Detection")
        self.no404_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px;")
        self.no404_check.stateChanged.connect(self.update_command)

        self.usecookies_check = QCheckBox("Use Cookies")
        self.usecookies_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px;")
        self.usecookies_check.stateChanged.connect(self.update_command)

        pause_label = QLabel("Pause (s):")
        pause_label.setStyleSheet(LABEL_STYLE)

        self.pause_spin = StyledSpinBox()
        self.pause_spin.setRange(0, 60)
        self.pause_spin.setValue(0)
        self.pause_spin.setSuffix(" s")
        self.pause_spin.valueChanged.connect(self.update_command)

        scan_options_grid.addWidget(self.no404_check, 0, 0)
        scan_options_grid.addWidget(self.usecookies_check, 0, 1)
        scan_options_grid.addWidget(pause_label, 0, 2)
        scan_options_grid.addWidget(self.pause_spin, 0, 3)
        scan_options_grid.setColumnStretch(4, 1)

        scan_layout.addLayout(scan_options_grid)
        scan_layout.addStretch()

        self.config_tabs.addTab(scan_tab, "Scan Options")

        # ===== TAB 3: ADVANCED =====
        advanced_tab = QWidget()
        advanced_layout = QGridLayout(advanced_tab)
        advanced_layout.setContentsMargins(10, 10, 10, 10)
        advanced_layout.setSpacing(10)
        advanced_layout.setColumnStretch(1, 1)
        advanced_layout.setColumnStretch(3, 1)

        # User-Agent
        ua_label = QLabel("User-Agent:")
        ua_label.setStyleSheet(LABEL_STYLE)
        ua_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.ua_input = QLineEdit()
        self.ua_input.setPlaceholderText("Custom User-Agent")
        self.ua_input.setStyleSheet(self.target_input.styleSheet())
        self.ua_input.textChanged.connect(self.update_command)

        # Proxy
        proxy_label = QLabel("Proxy:")
        proxy_label.setStyleSheet(LABEL_STYLE)
        proxy_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("http://proxy:port")
        self.proxy_input.setStyleSheet(self.target_input.styleSheet())
        self.proxy_input.textChanged.connect(self.update_command)

        # Authentication
        auth_label = QLabel("Auth (id:pass):")
        auth_label.setStyleSheet(LABEL_STYLE)
        auth_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.auth_input = QLineEdit()
        self.auth_input.setPlaceholderText("username:password")
        self.auth_input.setStyleSheet(self.target_input.styleSheet())
        self.auth_input.textChanged.connect(self.update_command)

        # Evasion
        evasion_label = QLabel("Evasion:")
        evasion_label.setStyleSheet(LABEL_STYLE)
        evasion_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.evasion_input = QLineEdit()
        self.evasion_input.setPlaceholderText("e.g., 1234AB")
        self.evasion_input.setStyleSheet(self.target_input.styleSheet())
        self.evasion_input.textChanged.connect(self.update_command)

        # CGI Dirs
        cgidirs_label = QLabel("CGI Dirs:")
        cgidirs_label.setStyleSheet(LABEL_STYLE)
        cgidirs_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.cgidirs_input = QLineEdit()
        self.cgidirs_input.setPlaceholderText("/cgi-bin/ /scripts/")
        self.cgidirs_input.setStyleSheet(self.target_input.styleSheet())
        self.cgidirs_input.textChanged.connect(self.update_command)

        # Root prepend
        root_label = QLabel("Root Prepend:")
        root_label.setStyleSheet(LABEL_STYLE)
        root_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.root_input = QLineEdit()
        self.root_input.setPlaceholderText("/directory")
        self.root_input.setStyleSheet(self.target_input.styleSheet())
        self.root_input.textChanged.connect(self.update_command)

        # Checkboxes
        self.nolookup_check = QCheckBox("No DNS Lookup")
        self.nolookup_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px;")
        self.nolookup_check.stateChanged.connect(self.update_command)

        self.nossl_check = QCheckBox("Disable SSL")
        self.nossl_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px;")
        self.nossl_check.stateChanged.connect(self.update_command)

        # Add to grid
        advanced_layout.addWidget(ua_label, 0, 0)
        advanced_layout.addWidget(self.ua_input, 0, 1, 1, 3)
        advanced_layout.addWidget(proxy_label, 1, 0)
        advanced_layout.addWidget(self.proxy_input, 1, 1, 1, 3)
        advanced_layout.addWidget(auth_label, 2, 0)
        advanced_layout.addWidget(self.auth_input, 2, 1)
        advanced_layout.addWidget(evasion_label, 2, 2)
        advanced_layout.addWidget(self.evasion_input, 2, 3)
        advanced_layout.addWidget(cgidirs_label, 3, 0)
        advanced_layout.addWidget(self.cgidirs_input, 3, 1)
        advanced_layout.addWidget(root_label, 3, 2)
        advanced_layout.addWidget(self.root_input, 3, 3)
        advanced_layout.addWidget(self.nolookup_check, 4, 0, 1, 2)
        advanced_layout.addWidget(self.nossl_check, 4, 2, 1, 2)
        advanced_layout.setRowStretch(5, 1)

        self.config_tabs.addTab(advanced_tab, "Advanced")

        config_layout.addWidget(self.config_tabs)
        control_layout.addWidget(config_group)
        control_layout.addStretch()

        # ==================== OUTPUT AREA ====================
        output_container = QWidget()
        output_layout = QVBoxLayout(output_container)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(0)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Nikto scan results will appear here...")
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
        output_layout.addWidget(self.output)

        # Use centralized CopyButton
        self.copy_button = CopyButton(self.output, self.main_window)
        self.copy_button.setParent(self.output)
        self.copy_button.raise_()
        
        # Severity legend button
        self.legend_button = QPushButton("⚠️")
        self.legend_button.setStyleSheet('''
            QPushButton {
                font-size: 24px;
                background-color: transparent;
                border: none;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: rgba(23, 119, 209, 0.2);
                border-radius: 8px;
            }
        ''')
        self.legend_button.setCursor(Qt.PointingHandCursor)
        
        # Create rich HTML tooltip for severity legend
        legend_tooltip = (
            '<div style="font-family: Arial; font-size: 12px; line-height: 1.5; color: #FFFFFF;">'
            '<b style="font-size: 14px; color: #FFFFFF;">⚠️ Color Severity Legend</b><br><br>'
            '<span style="color: #F87171; font-weight: bold;">🔴 RED (Bold)</span> - <span style="color: #FFFFFF;">Critical Vulnerabilities</span><br>'
            '&nbsp;&nbsp;&nbsp;<span style="color: #E5E7EB;">SQL Injection, RCE, File Upload, Auth Bypass</span><br><br>'
            '<span style="color: #FB923C; font-weight: bold;">🟠 ORANGE</span> - <span style="color: #FFFFFF;">High Severity</span><br>'
            '&nbsp;&nbsp;&nbsp;<span style="color: #E5E7EB;">XSS, Info Disclosure, Misconfiguration</span><br><br>'
            '<span style="color: #FACC15; font-weight: bold;">🟡 YELLOW</span> - <span style="color: #FFFFFF;">Medium Severity</span><br>'
            '&nbsp;&nbsp;&nbsp;<span style="color: #E5E7EB;">Warnings, Deprecated, Missing Headers</span><br><br>'
            '<span style="color: #60A5FA; font-weight: bold;">🔵 BLUE</span> - <span style="color: #FFFFFF;">Information</span><br>'
            '&nbsp;&nbsp;&nbsp;<span style="color: #E5E7EB;">Target Info, Server Details, Timestamps</span><br><br>'
            '<span style="color: #10B981; font-weight: bold;">🟢 GREEN</span> - <span style="color: #FFFFFF;">Low/Informational</span><br>'
            '&nbsp;&nbsp;&nbsp;<span style="color: #E5E7EB;">General Findings</span>'
            '</div>'
        )
        self.legend_button.setToolTip(legend_tooltip)
        self.legend_button.clicked.connect(self._show_severity_legend)
        self.legend_button.setParent(self.output)
        self.legend_button.raise_()
        
        # Position buttons at top-right
        self.output.installEventFilter(self)

        splitter.addWidget(control_panel)
        splitter.addWidget(output_container)
        splitter.setSizes([400, 400])

        # Initialize command
        self.update_command()

    def eventFilter(self, obj, event):
        """Handle events to position floating buttons."""
        from PySide6.QtCore import QEvent
        if obj == self.output and event.type() == QEvent.Resize:
            # Position buttons at top-right corner with 10px margin and spacing
            button_spacing = 5
            
            # Copy button (rightmost)
            self.copy_button.move(
                self.output.width() - self.copy_button.sizeHint().width() - 10,
                10
            )
            
            # Legend button (to the left of copy button)
            self.legend_button.move(
                self.output.width() - self.copy_button.sizeHint().width() - 
                self.legend_button.sizeHint().width() - 10 - button_spacing,
                10
            )
        return super().eventFilter(obj, event)

    def update_command(self):
        """Generate Nikto command based on UI inputs."""
        target = self.target_input.text().strip()
        if not target:
            target = "<target>"
        elif not target.startswith("http"):
            target = f"http://{target}"

        cmd_parts = ["nikto", "-h", target]

        # Port
        port = self.port_input.text().strip()
        if port:
            cmd_parts.extend(["-port", port])

        # SSL
        if self.ssl_check.isChecked():
            cmd_parts.append("-ssl")

        # Follow redirects
        if self.followredirects_check.isChecked():
            cmd_parts.append("-followredirects")

        # Virtual Host
        vhost = self.vhost_input.text().strip()
        if vhost:
            cmd_parts.extend(["-vhost", vhost])

        # Timeout
        if self.timeout_spin.value() != 10:
            cmd_parts.extend(["-timeout", str(self.timeout_spin.value())])

        # Max time
        maxtime = self.maxtime_input.text().strip()
        if maxtime:
            cmd_parts.extend(["-maxtime", maxtime])

        # Display options
        display_opts = []
        if self.display_verbose.isChecked():
            display_opts.append("V")
        if self.display_debug.isChecked():
            display_opts.append("D")
        if display_opts:
            cmd_parts.extend(["-Display", "".join(display_opts)])

        # Tuning
        tuning_codes = [code for code, check in self.tuning_checks.items() if check.isChecked()]
        if tuning_codes:
            cmd_parts.extend(["-Tuning", "".join(tuning_codes)])

        # No 404
        if self.no404_check.isChecked():
            cmd_parts.append("-no404")

        # Use cookies
        if self.usecookies_check.isChecked():
            cmd_parts.append("-usecookies")

        # Pause
        if self.pause_spin.value() > 0:
            cmd_parts.extend(["-Pause", str(self.pause_spin.value())])

        # User-Agent
        ua = self.ua_input.text().strip()
        if ua:
            cmd_parts.extend(["-useragent", f'"{ua}"'])

        # Proxy
        proxy = self.proxy_input.text().strip()
        if proxy:
            cmd_parts.extend(["-useproxy", proxy])

        # Authentication
        auth = self.auth_input.text().strip()
        if auth:
            cmd_parts.extend(["-id", auth])

        # Evasion
        evasion = self.evasion_input.text().strip()
        if evasion:
            cmd_parts.extend(["-evasion", evasion])

        # CGI Dirs
        cgidirs = self.cgidirs_input.text().strip()
        if cgidirs:
            cmd_parts.extend(["-Cgidirs", f'"{cgidirs}"'])

        # Root
        root = self.root_input.text().strip()
        if root:
            cmd_parts.extend(["-root", root])

        # No lookup
        if self.nolookup_check.isChecked():
            cmd_parts.append("-nolookup")

        # No SSL
        if self.nossl_check.isChecked():
            cmd_parts.append("-nossl")

        self.command_input.setText(" ".join(cmd_parts))

    def run_scan(self):
        """Execute Nikto scan."""
        target = self.target_input.text().strip()
        if not target:
            self._notify("Please enter a target URL")
            return

        self.output.clear()
        self._info(f"Starting Nikto scan on: {target}")
        self._section("NIKTO SCAN OUTPUT")

        # Extract target name from URL - remove protocol and path
        try:
            temp = target
            if "://" in temp:
                temp = temp.split("://", 1)[1]
            target_name = temp.split("/")[0].split(":")[0]
        except:
            target_name = "target"

        self.base_dir = create_target_dirs(target_name, None)
        output_file = os.path.join(self.base_dir, "Logs", "nikto.txt")

        # Build command
        command = self.command_input.text().split()
        command.extend(["-output", output_file, "-Format", "txt"])

        self.worker = ProcessWorker(command)
        self.worker.output_ready.connect(self._on_output)
        self.worker.finished.connect(self._on_scan_completed)
        self.worker.error.connect(lambda err: self._error(f"Error: {err}"))

        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        if self.main_window:
            self.main_window.active_process = self.worker

        self.worker.start()

    def stop_scan(self):
        """Stop the running scan."""
        if self.worker:
            self.worker.stop()

    def _on_scan_completed(self):
        """Handle scan completion."""
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        # Save the GUI output to text file
        if self.base_dir:
            output_file = os.path.join(self.base_dir, "Logs", "nikto.txt")
            self._info(f"Results saved to: {output_file}")

        self.worker = None
        if self.main_window:
            self.main_window.active_process = None
        self._info("Scan completed")
        self._notify("Nikto scan completed.")

    def _on_output(self, line):
        """
        Handle real-time output with intelligent severity-based color coding.
        
        🎨 INTELLIGENT SEVERITY-BASED COLORING SYSTEM:
        
        🔴 RED (Bold) - Critical Vulnerabilities:
           - SQL injection, Command execution, Remote shell
           - File upload, Authentication bypass
           - "Allows attackers", Credentials, Exploits, RCE
           - Keywords: sql injection, command execution, remote shell, file upload,
                       allows attackers, arbitrary code, authentication bypass,
                       credentials, password, exploit, vulnerable version, rce, backdoor
        
        🟠 ORANGE - High Severity:
           - XSS, Cross-site scripting, Information disclosure
           - Directory listing, Misconfigurations, CGI issues, Path traversal
           - Keywords: xss, cross-site, script, injection, information disclosure,
                       directory listing, indexing, misconfigur, default file,
                       sensitive data, allows remote, cgi, traversal, path disclosure
        
        🟡 YELLOW - Medium Severity:
           - Warnings, Deprecated features
           - Missing headers, Cookie issues, Clickjacking
           - Keywords: warning, deprecated, outdated, missing header,
                       clickjacking, iframe, cookie, header not set
        
        🔵 BLUE - Information:
           - Target IP, Hostname, Server info
           - Scan start/end times, Nikto version
           - Keywords: + target ip:, + target hostname:, + start time:, + server:,
                       + end time:, nikto v, scanning
        
        🟢 GREEN - Low/Informational:
           - General findings that don't match above categories
           - Any line starting with "+ " not categorized as critical/high/medium
        """
        # Strip ANSI codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        line = ansi_escape.sub('', line)

        # Skip empty lines
        if not line.strip():
            return

        line_lower = line.lower()
        
        # High severity (RED) - critical vulnerabilities
        if any(keyword in line_lower for keyword in [
            "sql injection", "command execution", "remote shell", "file upload",
            "allows attackers", "arbitrary code", "authentication bypass",
            "credentials", "password", "exploit", "vulnerable version",
            "remote code execution", "rce", "shell", "backdoor"
        ]):
            self.output.append(f'<span style="color:#F87171;font-weight:bold;">{line}</span>')  # Red Bold
        
        # Medium-High severity (ORANGE) - XSS, information disclosure, misconfigurations
        elif any(keyword in line_lower for keyword in [
            "xss", "cross-site", "script", "injection",
            "information disclosure", "directory listing", "indexing",
            "misconfigur", "default file", "sensitivem   data",
            "allows remote", "cgi", "traversal", "path disclosure"
        ]):
            self.output.append(f'<span style="color:#FB923C;">{line}</span>')  # Orange
        
        # Medium severity (YELLOW) - warnings and less critical issues
        elif any(keyword in line_lower for keyword in [
            "warning", "deprecated", "outdated", "missing header",
            "clickjacking", "iframe", "cookie", "header not set"
        ]):
            self.output.append(f'<span style="color:#FACC15;">{line}</span>')  # Yellow
        
        # Info headers (BLUE)
        elif any(keyword in line_lower for keyword in [
            "+ target ip:", "+ target hostname:", "+ start time:", "+ server:",
            "+ end time:", "nikto v", "scanning"
        ]):
            self.output.append(f'<span style="color:#60A5FA;">{line}</span>')  # Blue
        
        # Low severity / informational findings (GREEN) - anything else starting with +
        elif line.startswith("+ "):
            self.output.append(f'<span style="color:#10B981;">{line}</span>')  # Green
        
        # Everything else (default color)
        else:
            self.output.append(line)

    def _notify(self, message):
        """Show notification."""
        if self.main_window and hasattr(self.main_window, 'notification_manager'):
            self.main_window.notification_manager.notify(message)

    def _info(self, message):
        """Add info message."""
        self.output.append(f'<span style="color:#60A5FA;">[INFO]</span> {message}')

    def _error(self, message):
        """Add error message."""
        self.output.append(f'<span style="color:#F87171;">[ERROR]</span> {message}')

    def _section(self, title):
        """Add section header."""
        self.output.append(f'<br><span style="color:#FACC15;font-weight:700;">===== {title} =====</span><br>')

    def _show_severity_legend(self):
        """Show severity legend in a message box."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("⚠️ Nikto Color Severity Legend")
        
        # Build the message with rich text formatting
        legend_text = (
            '<div style="font-family: Arial; font-size: 13px; line-height: 1.8;">'
            '<b style="font-size: 15px;">⚠️ Color Severity Legend</b><br><br>'
            
            '<span style="color: #F87171; font-weight: bold; font-size: 14px;">🔴 RED (Bold)</span> - '
            '<span style="font-weight: bold;">Critical Vulnerabilities</span><br>'
            '&nbsp;&nbsp;&nbsp;&nbsp;SQL Injection, Remote Code Execution (RCE)<br>'
            '&nbsp;&nbsp;&nbsp;&nbsp;File Upload, Authentication Bypass<br><br>'
            
            '<span style="color: #FB923C; font-weight: bold; font-size: 14px;">🟠 ORANGE</span> - '
            '<span style="font-weight: bold;">High Severity</span><br>'
            '&nbsp;&nbsp;&nbsp;&nbsp;XSS, Information Disclosure<br>'
            '&nbsp;&nbsp;&nbsp;&nbsp;Misconfiguration, CGI Issues<br><br>'
            
            '<span style="color: #FACC15; font-weight: bold; font-size: 14px;">🟡 YELLOW</span> - '
            '<span style="font-weight: bold;">Medium Severity</span><br>'
            '&nbsp;&nbsp;&nbsp;&nbsp;Warnings, Deprecated Features<br>'
            '&nbsp;&nbsp;&nbsp;&nbsp;Missing Headers, Cookie Issues<br><br>'
            
            '<span style="color: #60A5FA; font-weight: bold; font-size: 14px;">🔵 BLUE</span> - '
            '<span style="font-weight: bold;">Information</span><br>'
            '&nbsp;&nbsp;&nbsp;&nbsp;Target Info, Server Details, Timestamps<br><br>'
            
            '<span style="color: #10B981; font-weight: bold; font-size: 14px;">🟢 GREEN</span> - '
            '<span style="font-weight: bold;">Low/Informational</span><br>'
            '&nbsp;&nbsp;&nbsp;&nbsp;General Findings<br>'
            '</div>'
        )
        
        msg_box.setText(legend_text)
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setIcon(QMessageBox.Information)
        
        # Style the message box with dark theme
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
            }}
            QMessageBox QLabel {{
                color: {COLOR_TEXT_PRIMARY};
                min-width: 450px;
            }}
            QPushButton {{
                background-color: #1777d1;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: #1565c0;
            }}
        """)
        
        msg_box.exec()
