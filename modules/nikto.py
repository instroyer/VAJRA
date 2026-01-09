# =============================================================================
# modules/nikto.py
#
# Nikto - Web Server Vulnerability Scanner
# =============================================================================

import os
import re
import shlex
import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from ui.worker import ToolExecutionMixin
from core.fileops import create_target_dirs
from ui.styles import (
    # Widgets
    RunButton, StopButton, CopyButton,
    StyledLineEdit, StyledSpinBox, StyledCheckBox,
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView,
    ToolSplitter, ConfigTabs, StyledToolView,
    # Constants
    COLOR_BG_INPUT, COLOR_TEXT_PRIMARY
)


class NiktoTool(ToolBase):
    """Nikto vulnerability scanner tool plugin."""

    name = "Nikto"
    category = ToolCategory.VULNERABILITY_SCANNER

    @property
    def description(self) -> str:
        return "Web server scanner which performs comprehensive tests against web servers."

    @property
    def icon(self) -> str:
        return "🛡️"

    def get_widget(self, main_window):
        return NiktoView(main_window=main_window)


class NiktoView(StyledToolView, ToolExecutionMixin):
    """Nikto web vulnerability scanner interface."""
    
    tool_name = "Nikto"
    tool_category = "VULNERABILITY_SCANNER"

    def __init__(self, main_window=None):
        super().__init__()
        self.init_safe_stop()
        self.main_window = main_window
        self.base_dir = None
        self._build_ui()
        self.update_command()

    def _build_ui(self):
        """Build complete custom UI."""
        # setStyleSheet handled by StyledToolView
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = ToolSplitter()

        # ==================== CONTROL PANEL ====================
        control_panel = QWidget()
        # Removed legacy style
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        # Header
        header = HeaderLabel(self.tool_category, self.tool_name)
        control_layout.addWidget(header)

        # Target URL
        target_label = StyledLabel("Target URL")
        control_layout.addWidget(target_label)

        target_row = QHBoxLayout()
        self.target_input = StyledLineEdit()
        self.target_input.setPlaceholderText("http://example.com")
        self.target_input.textChanged.connect(self.update_command)
        target_row.addWidget(self.target_input)

        self.run_button = RunButton("RUN NIKTO")
        self.run_button.clicked.connect(self.run_scan)
        self.stop_button = StopButton()
        self.stop_button.clicked.connect(self.stop_scan)

        target_row.addWidget(self.run_button)
        target_row.addWidget(self.stop_button)
        control_layout.addLayout(target_row)
        
        # Legend Button
        self.legend_button = QPushButton("⚠️ View Severity Legend")
        self.legend_button.setCursor(Qt.PointingHandCursor)
        self.legend_button.setStyleSheet(f"""
            QPushButton {{
                color: {COLOR_TEXT_PRIMARY};
                background-color: transparent;
                border: 1px solid #3b82f6;
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: rgba(59, 130, 246, 0.2);
            }}
        """)
        self.legend_button.clicked.connect(self._show_severity_legend)
        control_layout.addWidget(self.legend_button)

        # Command display
        self.command_input = StyledLineEdit()
        self.command_input.setReadOnly(True)
        self.command_input.setPlaceholderText("Command preview...")
        control_layout.addWidget(self.command_input)

        # Configuration Group
        config_group = StyledGroupBox("⚙️ Scan Configuration")
        config_layout = QVBoxLayout(config_group)
        config_layout.setContentsMargins(5, 15, 5, 5)
        config_layout.setSpacing(0)

        self.config_tabs = ConfigTabs()

        # ===== TAB 1: BASIC SCAN =====
        basic_tab = QWidget()
        basic_layout = QGridLayout(basic_tab)
        basic_layout.setContentsMargins(10, 10, 10, 10)
        basic_layout.setSpacing(10)
        basic_layout.setColumnStretch(1, 1)
        basic_layout.setColumnStretch(3, 1)

        # Port
        port_label = StyledLabel("Port (-port):")
        port_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.port_input = StyledLineEdit()
        self.port_input.setPlaceholderText("80,443")
        self.port_input.textChanged.connect(self.update_command)

        # SSL/HTTPS
        self.ssl_check = StyledCheckBox("Force SSL (-ssl)")
        self.ssl_check.stateChanged.connect(self.update_command)

        self.followredirects_check = StyledCheckBox("Follow Redirects")
        self.followredirects_check.stateChanged.connect(self.update_command)

        # Virtual Host
        vhost_label = StyledLabel("VHost (-vhost):")
        vhost_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.vhost_input = StyledLineEdit()
        self.vhost_input.setPlaceholderText("Custom Host header")
        self.vhost_input.textChanged.connect(self.update_command)

        # Timeout
        timeout_label = StyledLabel("Timeout (s):")
        timeout_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.timeout_spin = StyledSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(10)
        self.timeout_spin.setSuffix(" s")
        self.timeout_spin.valueChanged.connect(self.update_command)

        # Max Time
        maxtime_label = StyledLabel("Max Time:")
        maxtime_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.maxtime_input = StyledLineEdit()
        self.maxtime_input.setPlaceholderText("e.g., 1h, 60m")
        self.maxtime_input.textChanged.connect(self.update_command)

        # Display Options
        display_label = StyledLabel("Display:")
        display_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        display_layout = QHBoxLayout()
        self.display_verbose = StyledCheckBox("Verbose (V)")
        self.display_verbose.stateChanged.connect(self.update_command)
        self.display_debug = StyledCheckBox("Debug (D)")
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

        tuning_label = StyledLabel("Scan Tuning (-Tuning):")
        scan_layout.addWidget(tuning_label)

        tuning_grid = QGridLayout()
        tuning_grid.setSpacing(8)

        self.tuning_checks = {}
        tuning_options = [
            ("1", "Interesting File / Seen in logs"),
            ("2", "Misconfiguration / Default File"),
            ("3", "Information Disclosure"),
            ("4", "Injection (XSS/Script/HTML)"),
            ("5", "Remote File Retrieval - Web Root"),
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
            check = StyledCheckBox(f"{code} - {label}")
            check.stateChanged.connect(self.update_command)
            self.tuning_checks[code] = check
            tuning_grid.addWidget(check, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

        scan_layout.addLayout(tuning_grid)

        scan_options_grid = QGridLayout()
        scan_options_grid.setSpacing(10)

        self.no404_check = StyledCheckBox("No 404 Detection")
        self.no404_check.stateChanged.connect(self.update_command)

        self.usecookies_check = StyledCheckBox("Use Cookies")
        self.usecookies_check.stateChanged.connect(self.update_command)

        pause_label = StyledLabel("Pause (s):")
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
        ua_label = StyledLabel("User-Agent:")
        ua_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.ua_input = StyledLineEdit()
        self.ua_input.setPlaceholderText("Custom User-Agent")
        self.ua_input.textChanged.connect(self.update_command)

        # Proxy
        proxy_label = StyledLabel("Proxy:")
        proxy_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.proxy_input = StyledLineEdit()
        self.proxy_input.setPlaceholderText("http://proxy:port")
        self.proxy_input.textChanged.connect(self.update_command)

        # Authentication
        auth_label = StyledLabel("Auth (id:pass):")
        auth_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.auth_input = StyledLineEdit()
        self.auth_input.setPlaceholderText("username:password")
        self.auth_input.textChanged.connect(self.update_command)

        # Evasion
        evasion_label = StyledLabel("Evasion:")
        evasion_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.evasion_input = StyledLineEdit()
        self.evasion_input.setPlaceholderText("e.g., 1234AB")
        self.evasion_input.textChanged.connect(self.update_command)

        # CGI Dirs
        cgidirs_label = StyledLabel("CGI Dirs:")
        cgidirs_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.cgidirs_input = StyledLineEdit()
        self.cgidirs_input.setPlaceholderText("/cgi-bin/ /scripts/")
        self.cgidirs_input.textChanged.connect(self.update_command)

        # Root prepend
        root_label = StyledLabel("Root Prepend:")
        root_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.root_input = StyledLineEdit()
        self.root_input.setPlaceholderText("/directory")
        self.root_input.textChanged.connect(self.update_command)

        # Checkboxes
        self.nolookup_check = StyledCheckBox("No DNS Lookup")
        self.nolookup_check.stateChanged.connect(self.update_command)

        self.nossl_check = StyledCheckBox("Disable SSL")
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

        splitter.addWidget(control_panel)

        # ==================== OUTPUT AREA ====================
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("Nikto results will appear here...")
        
        splitter.addWidget(self.output)
        splitter.setSizes([450, 350])

        main_layout.addWidget(splitter)

    # -------------------------------------------------------------------------
    # Command Builder
    # -------------------------------------------------------------------------

    def build_command(self, preview: bool = False) -> str:
        """
        Generate Nikto command string.
        """
        cmd = ["nikto"]
        
        target = self.target_input.text().strip()
        if not target:
            if preview:
                target = "<target>"
            else:
                raise ValueError("Target required")
        elif not target.startswith("http") and not preview:
             target = f"http://{target}"

        cmd.extend(["-h", target])

        # Port
        port = self.port_input.text().strip()
        if port:
            cmd.extend(["-port", port])

        # SSL
        if self.ssl_check.isChecked():
            cmd.append("-ssl")

        # Follow redirects
        if self.followredirects_check.isChecked():
            cmd.append("-followredirects")

        # Virtual Host
        vhost = self.vhost_input.text().strip()
        if vhost:
            cmd.extend(["-vhost", vhost])

        # Timeout
        if self.timeout_spin.value() != 10:
            cmd.extend(["-timeout", str(self.timeout_spin.value())])

        # Max time
        maxtime = self.maxtime_input.text().strip()
        if maxtime:
            cmd.extend(["-maxtime", maxtime])

        # Display options
        display_opts = []
        if self.display_verbose.isChecked():
            display_opts.append("V")
        if self.display_debug.isChecked():
            display_opts.append("D")
        if display_opts:
            cmd.extend(["-Display", "".join(display_opts)])

        # Tuning
        tuning_codes = [code for code, check in self.tuning_checks.items() if check.isChecked()]
        if tuning_codes:
            cmd.extend(["-Tuning", "".join(tuning_codes)])

        # No 404
        if self.no404_check.isChecked():
            cmd.append("-no404")

        # Use cookies
        if self.usecookies_check.isChecked():
            cmd.append("-usecookies")

        # Pause
        if self.pause_spin.value() > 0:
            cmd.extend(["-Pause", str(self.pause_spin.value())])

        # User-Agent
        ua = self.ua_input.text().strip()
        if ua:
            cmd.extend(["-useragent", ua])

        # Proxy
        proxy = self.proxy_input.text().strip()
        if proxy:
            cmd.extend(["-useproxy", proxy])

        # Authentication
        auth = self.auth_input.text().strip()
        if auth:
            cmd.extend(["-id", auth])

        # Evasion
        evasion = self.evasion_input.text().strip()
        if evasion:
            cmd.extend(["-evasion", evasion])

        # CGI Dirs
        cgidirs = self.cgidirs_input.text().strip()
        if cgidirs:
            cmd.extend(["-Cgidirs", cgidirs])

        # Root
        root = self.root_input.text().strip()
        if root:
            cmd.extend(["-root", root])

        # No lookup
        if self.nolookup_check.isChecked():
            cmd.append("-nolookup")

        # No SSL
        if self.nossl_check.isChecked():
            cmd.append("-nossl")

        # No interactive
        cmd.extend(["-ask", "no"])

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
        """Execute Nikto scan."""
        try:
            target = self.target_input.text().strip()
            # Validate via build
            cmd_str = self.build_command(preview=False)
            
            # Extract target name from URL
            try:
                temp = target
                if "://" in temp:
                    temp = temp.split("://", 1)[1]
                target_name = temp.split("/")[0].split(":")[0]
            except:
                target_name = "target"

            self.base_dir = create_target_dirs(target_name, None)
            output_file = os.path.join(self.base_dir, "Logs", "nikto.txt")
            
            # Append output options to command string
            cmd_str += f" -output {shlex.quote(output_file)} -Format txt"

            # Start Execution (Mixin) - Use real-time output for formatted display
            self.start_execution(cmd_str, output_file, buffer_output=False)

            self._info(f"Starting Nikto scan on: {target}")
            self._section("NIKTO SCAN OUTPUT")


        
        except Exception as e:
            self._error(str(e))

    def on_execution_finished(self):
        """Handle scan completion."""
        super().on_execution_finished()
        self.worker = None
        if self.main_window:
            self.main_window.active_process = None
        
        if self.base_dir:
             pass # Mixin handles notification

    def on_new_output(self, line):
        """Handle real-time output with severity-based color coding."""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_line = ansi_escape.sub('', line)

        if not clean_line.strip():
            return

        safe_line = html.escape(clean_line)
        line_lower = clean_line.lower()

        # Critical (RED)
        if any(keyword in line_lower for keyword in [
            "sql injection", "command execution", "remote shell", "file upload",
            "allows attackers", "arbitrary code", "authentication bypass",
            "credentials", "password", "exploit", "vulnerable version",
            "remote code execution", "rce", "shell", "backdoor"
        ]):
            self._raw(f'<span style="color:#F87171;font-weight:bold;">{safe_line}</span>')

        # High (ORANGE)
        elif any(keyword in line_lower for keyword in [
            "xss", "cross-site", "script", "injection",
            "information disclosure", "directory listing", "indexing",
            "misconfigur", "default file", "sensitive data",
            "allows remote", "cgi", "traversal", "path disclosure"
        ]):
            self._raw(f'<span style="color:#FB923C;">{safe_line}</span>')

        # Medium (YELLOW)
        elif any(keyword in line_lower for keyword in [
            "warning", "deprecated", "outdated", "missing header",
            "clickjacking", "iframe", "cookie", "header not set"
        ]):
            self._raw(f'<span style="color:#FACC15;">{safe_line}</span>')

        # Info (BLUE)
        elif any(keyword in line_lower for keyword in [
            "+ target ip:", "+ target hostname:", "+ start time:", "+ server:",
            "+ end time:", "nikto v", "scanning"
        ]):
            self._raw(f'<span style="color:#60A5FA;">{safe_line}</span>')

        # Low (GREEN)
        elif clean_line.startswith("+ "):
            self._raw(f'<span style="color:#10B981;">{safe_line}</span>')

        # Default
        else:
            self._raw(safe_line)

    def _show_severity_legend(self):
        """Show severity legend in a message box."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("⚠️ Nikto Color Severity Legend")

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

        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {COLOR_BG_INPUT};
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
