# =============================================================================
# modules/ffuf.py
#
# Professional FFUF (Fuzz Faster U Fool) Web Fuzzer GUI
# Comprehensive web fuzzing tool with all major FFUF features
# =============================================================================

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QSpinBox, QCheckBox, QComboBox,
    QFileDialog, QTextEdit, QGridLayout, QSplitter, QTabWidget
)
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from ui.worker import ProcessWorker
from core.fileops import create_target_dirs
from ui.styles import (
    COLOR_BACKGROUND_INPUT, COLOR_BACKGROUND_PRIMARY, COLOR_TEXT_PRIMARY, COLOR_BORDER,
    COLOR_BORDER_INPUT_FOCUSED, LABEL_STYLE, StyledSpinBox,
    TOOL_HEADER_STYLE, TOOL_VIEW_STYLE, RUN_BUTTON_STYLE, STOP_BUTTON_STYLE, CopyButton, CommandDisplay
)


class FFUFTool(ToolBase):
    """Professional FFUF web fuzzer tool."""

    @property
    def name(self) -> str:
        return "FFUF"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WEB_SCANNING

    def get_widget(self, main_window):
        return FFUFToolView(main_window=main_window)


class FFUFToolView(QWidget):
    """Professional GUI for FFUF web fuzzer with comprehensive features."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.worker = None
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
        header = QLabel("WEB_SCANNING › FFUF")
        header.setStyleSheet(TOOL_HEADER_STYLE)
        control_layout.addWidget(header)

        # Target URL
        target_label = QLabel("Target URL (use FUZZ keyword)")
        target_label.setStyleSheet(LABEL_STYLE)
        control_layout.addWidget(target_label)

        target_row = QHBoxLayout()
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("http://example.com/FUZZ")
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

        # Command display (Centralized)
        self.command_display_widget = CommandDisplay()
        self.command_input = self.command_display_widget.input
        control_layout.addWidget(self.command_display_widget)

        # ==================== WORDLIST SECTION ====================
        wordlist_group = QGroupBox("🔤 Wordlist Configuration")
        wordlist_group.setStyleSheet(f"""
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
        wordlist_layout = QVBoxLayout(wordlist_group)
        wordlist_layout.setSpacing(8)

        wl_row = QHBoxLayout()
        wl_label = QLabel("Wordlist:")
        wl_label.setStyleSheet(LABEL_STYLE)
        wl_label.setFixedWidth(100)

        self.wordlist_input = QLineEdit()
        self.wordlist_input.setPlaceholderText("Select wordlist file...")
        self.wordlist_input.setStyleSheet(self.target_input.styleSheet())
        self.wordlist_input.textChanged.connect(self.update_command)

        wl_browse = QPushButton("📁 Browse")
        wl_browse.setFixedWidth(100)
        wl_browse.setCursor(Qt.PointingHandCursor)
        wl_browse.clicked.connect(self._browse_wordlist)
        wl_browse.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #4A4A4A; }}
        """)

        wl_row.addWidget(wl_label)
        wl_row.addWidget(self.wordlist_input)
        wl_row.addWidget(wl_browse)
        wordlist_layout.addLayout(wl_row)

        fuzz_info = QLabel("💡 Use FUZZ keyword in URL where you want to inject wordlist values")
        fuzz_info.setStyleSheet(f"color: #60A5FA; font-style: italic; font-size: 13px;")
        wordlist_layout.addWidget(fuzz_info)

        control_layout.addWidget(wordlist_group)

        # ==================== TABBED CONFIGURATION ====================
        config_group = QGroupBox("⚙️ Configuration")
        config_group.setStyleSheet(wordlist_group.styleSheet())
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

        # ===== TAB 1: HTTP REQUEST =====
        request_tab = QWidget()
        request_layout = QGridLayout(request_tab)
        request_layout.setContentsMargins(10, 10, 10, 10)
        request_layout.setSpacing(10)
        request_layout.setColumnStretch(1, 1)
        request_layout.setColumnStretch(3, 1)

        # Method
        method_label = QLabel("Method:")
        method_label.setStyleSheet(LABEL_STYLE)
        method_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.method_combo = QComboBox()
        self.method_combo.addItems(["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
        self.method_combo.setCurrentText("GET")
        self.method_combo.currentTextChanged.connect(self.update_command)
        self.method_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
                min-height: 20px;
            }}
        """)

        # Checkboxes row
        self.follow_redirects = QCheckBox("Follow Redirects")
        self.follow_redirects.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px;")
        self.follow_redirects.stateChanged.connect(self.update_command)

        self.auto_calibrate = QCheckBox("Auto-Calibrate")
        self.auto_calibrate.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px;")
        self.auto_calibrate.setChecked(True)
        self.auto_calibrate.stateChanged.connect(self.update_command)

        # Headers
        headers_label = QLabel("Headers:")
        headers_label.setStyleSheet(LABEL_STYLE)
        headers_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.headers_input = QLineEdit()
        self.headers_input.setPlaceholderText('"User-Agent: CustomUA"')
        self.headers_input.setStyleSheet(self.target_input.styleSheet())
        self.headers_input.textChanged.connect(self.update_command)

        # Cookies
        cookies_label = QLabel("Cookies:")
        cookies_label.setStyleSheet(LABEL_STYLE)
        cookies_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.cookies_input = QLineEdit()
        self.cookies_input.setPlaceholderText("session=abc123; token=xyz789")
        self.cookies_input.setStyleSheet(self.target_input.styleSheet())
        self.cookies_input.textChanged.connect(self.update_command)

        # POST Data
        data_label = QLabel("POST Data:")
        data_label.setStyleSheet(LABEL_STYLE)
        data_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.data_input = QLineEdit()
        self.data_input.setPlaceholderText("username=admin&password=FUZZ")
        self.data_input.setStyleSheet(self.target_input.styleSheet())
        self.data_input.textChanged.connect(self.update_command)

        # Add to grid
        request_layout.addWidget(method_label, 0, 0)
        request_layout.addWidget(self.method_combo, 0, 1)
        request_layout.addWidget(self.follow_redirects, 0, 2)
        request_layout.addWidget(self.auto_calibrate, 0, 3)
        request_layout.addWidget(headers_label, 1, 0)
        request_layout.addWidget(self.headers_input, 1, 1, 1, 3)
        request_layout.addWidget(cookies_label, 2, 0)
        request_layout.addWidget(self.cookies_input, 2, 1, 1, 3)
        request_layout.addWidget(data_label, 3, 0)
        request_layout.addWidget(self.data_input, 3, 1, 1, 3)
        request_layout.setRowStretch(4, 1)

        self.config_tabs.addTab(request_tab, "HTTP Request")

        # ===== TAB 2: FILTERING & MATCHING =====
        filter_tab = QWidget()
        filter_layout = QGridLayout(filter_tab)
        filter_layout.setContentsMargins(10, 10, 10, 10)
        filter_layout.setSpacing(10)
        filter_layout.setColumnStretch(1, 1)
        filter_layout.setColumnStretch(3, 1)

        # Status codes
        filter_sc_label = QLabel("Filter Status:")
        filter_sc_label.setStyleSheet(LABEL_STYLE)
        filter_sc_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.filter_status = QLineEdit()
        self.filter_status.setPlaceholderText("404,403")
        self.filter_status.setStyleSheet(self.target_input.styleSheet())
        self.filter_status.textChanged.connect(self.update_command)

        match_sc_label = QLabel("Match Status:")
        match_sc_label.setStyleSheet(LABEL_STYLE)
        match_sc_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.match_status = QLineEdit()
        self.match_status.setPlaceholderText("200,301")
        self.match_status.setStyleSheet(self.target_input.styleSheet())
        self.match_status.textChanged.connect(self.update_command)

        # Size
        filter_size_label = QLabel("Filter Size:")
        filter_size_label.setStyleSheet(LABEL_STYLE)
        filter_size_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.filter_size = QLineEdit()
        self.filter_size.setPlaceholderText("bytes")
        self.filter_size.setStyleSheet(self.target_input.styleSheet())
        self.filter_size.textChanged.connect(self.update_command)

        match_size_label = QLabel("Match Size:")
        match_size_label.setStyleSheet(LABEL_STYLE)
        match_size_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.match_size = QLineEdit()
        self.match_size.setPlaceholderText("bytes")
        self.match_size.setStyleSheet(self.target_input.styleSheet())
        self.match_size.textChanged.connect(self.update_command)

        # Words
        filter_words_label = QLabel("Filter Words:")
        filter_words_label.setStyleSheet(LABEL_STYLE)
        filter_words_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.filter_words = QLineEdit()
        self.filter_words.setPlaceholderText("word count")
        self.filter_words.setStyleSheet(self.target_input.styleSheet())
        self.filter_words.textChanged.connect(self.update_command)

        match_words_label = QLabel("Match Words:")
        match_words_label.setStyleSheet(LABEL_STYLE)
        match_words_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.match_words = QLineEdit()
        self.match_words.setPlaceholderText("word count")
        self.match_words.setStyleSheet(self.target_input.styleSheet())
        self.match_words.textChanged.connect(self.update_command)

        # Lines
        filter_lines_label = QLabel("Filter Lines:")
        filter_lines_label.setStyleSheet(LABEL_STYLE)
        filter_lines_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.filter_lines = QLineEdit()
        self.filter_lines.setPlaceholderText("line count")
        self.filter_lines.setStyleSheet(self.target_input.styleSheet())
        self.filter_lines.textChanged.connect(self.update_command)

        # Match Regex
        match_regex_label = QLabel("Match Regex:")
        match_regex_label.setStyleSheet(LABEL_STYLE)
        match_regex_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.match_regex = QLineEdit()
        self.match_regex.setPlaceholderText('"admin.*panel"')
        self.match_regex.setStyleSheet(self.target_input.styleSheet())
        self.match_regex.textChanged.connect(self.update_command)

        # Filter Regex
        filter_regex_label = QLabel("Filter Regex:")
        filter_regex_label.setStyleSheet(LABEL_STYLE)
        filter_regex_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.filter_regex = QLineEdit()
        self.filter_regex.setPlaceholderText('"error.*"')
        self.filter_regex.setStyleSheet(self.target_input.styleSheet())
        self.filter_regex.textChanged.connect(self.update_command)

        # Filter/Match Mode
        filter_mode_label = QLabel("Filter Mode:")
        filter_mode_label.setStyleSheet(LABEL_STYLE)
        filter_mode_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.filter_mode_combo = QComboBox()
        self.filter_mode_combo.addItems(["or", "and"])
        self.filter_mode_combo.setStyleSheet(self.method_combo.styleSheet())
        self.filter_mode_combo.currentTextChanged.connect(self.update_command)

        match_mode_label = QLabel("Match Mode:")
        match_mode_label.setStyleSheet(LABEL_STYLE)
        match_mode_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.match_mode_combo = QComboBox()
        self.match_mode_combo.addItems(["or", "and"])
        self.match_mode_combo.setStyleSheet(self.method_combo.styleSheet())
        self.match_mode_combo.currentTextChanged.connect(self.update_command)

        # Add to grid
        filter_layout.addWidget(filter_sc_label, 0, 0)
        filter_layout.addWidget(self.filter_status, 0, 1)
        filter_layout.addWidget(match_sc_label, 0, 2)
        filter_layout.addWidget(self.match_status, 0, 3)
        filter_layout.addWidget(filter_size_label, 1, 0)
        filter_layout.addWidget(self.filter_size, 1, 1)
        filter_layout.addWidget(match_size_label, 1, 2)
        filter_layout.addWidget(self.match_size, 1, 3)
        filter_layout.addWidget(filter_words_label, 2, 0)
        filter_layout.addWidget(self.filter_words, 2, 1)
        filter_layout.addWidget(match_words_label, 2, 2)
        filter_layout.addWidget(self.match_words, 2, 3)
        filter_layout.addWidget(filter_lines_label, 3, 0)
        filter_layout.addWidget(self.filter_lines, 3, 1)
        filter_layout.addWidget(match_regex_label, 3, 2)
        filter_layout.addWidget(self.match_regex, 3, 3)
        filter_layout.addWidget(filter_regex_label, 4, 0)
        filter_layout.addWidget(self.filter_regex, 4, 1)
        filter_layout.addWidget(filter_mode_label, 4, 2)
        filter_layout.addWidget(self.filter_mode_combo, 4, 3)
        filter_layout.addWidget(match_mode_label, 5, 0)
        filter_layout.addWidget(self.match_mode_combo, 5, 1)
        filter_layout.setRowStretch(6, 1)

        self.config_tabs.addTab(filter_tab, "Filters & Matching")

        # ===== TAB 3: ADVANCED =====
        advanced_tab = QWidget()
        advanced_layout = QGridLayout(advanced_tab)
        advanced_layout.setContentsMargins(10, 10, 10, 10)
        advanced_layout.setSpacing(10)
        advanced_layout.setColumnStretch(1, 1)
        advanced_layout.setColumnStretch(3, 1)

        # Threads
        threads_label = QLabel("Threads:")
        threads_label.setStyleSheet(LABEL_STYLE)
        threads_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.threads_spin = StyledSpinBox()
        self.threads_spin.setRange(1, 100)
        self.threads_spin.setValue(40)
        self.threads_spin.valueChanged.connect(self.update_command)

        # Delay
        delay_label = QLabel("Delay (ms):")
        delay_label.setStyleSheet(LABEL_STYLE)
        delay_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.delay_spin = StyledSpinBox()
        self.delay_spin.setRange(0, 5000)
        self.delay_spin.setValue(0)
        self.delay_spin.setSuffix(" ms")
        self.delay_spin.valueChanged.connect(self.update_command)

        # Rate limit
        rate_label = QLabel("Rate Limit:")
        rate_label.setStyleSheet(LABEL_STYLE)
        rate_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.rate_spin = StyledSpinBox()
        self.rate_spin.setRange(0, 10000)
        self.rate_spin.setValue(0)
        self.rate_spin.setSpecialValueText("Unlimited")
        self.rate_spin.setSuffix(" req/s")
        self.rate_spin.valueChanged.connect(self.update_command)

        # Timeout
        timeout_label = QLabel("Timeout (s):")
        timeout_label.setStyleSheet(LABEL_STYLE)
        timeout_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.timeout_spin = StyledSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(10)
        self.timeout_spin.setSuffix(" s")
        self.timeout_spin.valueChanged.connect(self.update_command)

        # Recursion
        self.recursion_check = QCheckBox("Recursive Fuzzing")
        self.recursion_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px;")
        self.recursion_check.stateChanged.connect(self.update_command)

        recursion_depth_label = QLabel("Depth:")
        recursion_depth_label.setStyleSheet(LABEL_STYLE)
        recursion_depth_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.recursion_depth = StyledSpinBox()
        self.recursion_depth.setRange(1, 10)
        self.recursion_depth.setValue(1)
        self.recursion_depth.setEnabled(False)
        self.recursion_depth.valueChanged.connect(self.update_command)
        self.recursion_check.stateChanged.connect(
            lambda: self.recursion_depth.setEnabled(self.recursion_check.isChecked())
        )

        # Extensions
        ext_label = QLabel("Extensions:")
        ext_label.setStyleSheet(LABEL_STYLE)
        ext_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.extensions_input = QLineEdit()
        self.extensions_input.setPlaceholderText(".php,.html,.js")
        self.extensions_input.setStyleSheet(self.target_input.styleSheet())
        self.extensions_input.textChanged.connect(self.update_command)

        # Add to grid
        advanced_layout.addWidget(threads_label, 0, 0)
        advanced_layout.addWidget(self.threads_spin, 0, 1)
        advanced_layout.addWidget(delay_label, 0, 2)
        advanced_layout.addWidget(self.delay_spin, 0, 3)
        advanced_layout.addWidget(rate_label, 1, 0)
        advanced_layout.addWidget(self.rate_spin, 1, 1)
        advanced_layout.addWidget(timeout_label, 1, 2)
        advanced_layout.addWidget(self.timeout_spin, 1, 3)
        advanced_layout.addWidget(self.recursion_check, 2, 0, 1, 2)
        advanced_layout.addWidget(recursion_depth_label, 2, 2)
        advanced_layout.addWidget(self.recursion_depth, 2, 3)
        advanced_layout.addWidget(ext_label, 3, 0)
        advanced_layout.addWidget(self.extensions_input, 3, 1, 1, 3)
        advanced_layout.setRowStretch(4, 1)

        self.config_tabs.addTab(advanced_tab, "Advanced")

        config_layout.addWidget(self.config_tabs)
        control_layout.addWidget(config_group)
        control_layout.addStretch()

        # ==================== OUTPUT AREA ====================
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("FFUF results will appear here...")
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

        # Output Container
        output_widget = QWidget()
        output_layout = QGridLayout(output_widget)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(0)
        output_layout.addWidget(self.output, 0, 0)

        self.copy_button = CopyButton(self.output, self.main_window)
        output_layout.addWidget(self.copy_button, 0, 0, Qt.AlignTop | Qt.AlignRight)

        splitter.addWidget(control_panel)
        splitter.addWidget(output_widget)
        splitter.setSizes([400, 400])

        # Initialize command
        self.update_command()

    def _browse_wordlist(self):
        """Open file dialog to select wordlist."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Wordlist",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.wordlist_input.setText(file_path)

    def update_command(self):
        """Generate FFUF command based on UI inputs."""
        target = self.target_input.text().strip()
        if not target:
            target = "http://<target>/FUZZ"
        elif "FUZZ" not in target:
            if not target.startswith("http"):
                target = f"http://{target}"
            if not target.endswith("/"):
                target += "/"
            target += "FUZZ"
        elif not target.startswith("http"):
            target = f"http://{target}"

        wordlist = self.wordlist_input.text().strip()
        if not wordlist:
            wordlist = "<wordlist>"

        cmd_parts = ["ffuf"]
        cmd_parts.extend(["-u", target])
        cmd_parts.extend(["-w", wordlist])

        # Method
        if self.method_combo.currentText() != "GET":
            cmd_parts.extend(["-X", self.method_combo.currentText()])

        # Headers
        headers = self.headers_input.text().strip()
        if headers:
            for header in headers.split('"'):
                header = header.strip()
                if header and ":" in header:
                    cmd_parts.extend(["-H", f'"{header}"'])

        # Cookies
        cookies = self.cookies_input.text().strip()
        if cookies:
            cmd_parts.extend(["-b", f'"{cookies}"'])

        # POST data
        data = self.data_input.text().strip()
        if data:
            cmd_parts.extend(["-d", f'"{data}"'])

        # Redirects and calibration
        if self.follow_redirects.isChecked():
            cmd_parts.append("-r")
        if self.auto_calibrate.isChecked():
            cmd_parts.append("-ac")

        # Filters
        if self.filter_status.text().strip():
            cmd_parts.extend(["-fc", self.filter_status.text().strip()])
        if self.match_status.text().strip():
            cmd_parts.extend(["-mc", self.match_status.text().strip()])
        if self.filter_size.text().strip():
            cmd_parts.extend(["-fs", self.filter_size.text().strip()])
        if self.match_size.text().strip():
            cmd_parts.extend(["-ms", self.match_size.text().strip()])
        if self.filter_words.text().strip():
            cmd_parts.extend(["-fw", self.filter_words.text().strip()])
        if self.match_words.text().strip():
            cmd_parts.extend(["-mw", self.match_words.text().strip()])
        if self.filter_lines.text().strip():
            cmd_parts.extend(["-fl", self.filter_lines.text().strip()])
        if self.match_regex.text().strip():
            cmd_parts.extend(["-mr", f'"{self.match_regex.text().strip()}"'])
        if self.filter_regex.text().strip():
            cmd_parts.extend(["-fr", f'"{self.filter_regex.text().strip()}"'])
        if self.filter_mode_combo.currentText() != "or":
            cmd_parts.extend(["-fmode", self.filter_mode_combo.currentText()])
        if self.match_mode_combo.currentText() != "or":
            cmd_parts.extend(["-mmode", self.match_mode_combo.currentText()])

        # Performance
        if self.threads_spin.value() != 40:
            cmd_parts.extend(["-t", str(self.threads_spin.value())])
        if self.delay_spin.value() > 0:
            cmd_parts.extend(["-p", f"{self.delay_spin.value()/1000:.3f}"])
        if self.rate_spin.value() > 0:
            cmd_parts.extend(["-rate", str(self.rate_spin.value())])
        if self.timeout_spin.value() != 10:
            cmd_parts.extend(["-timeout", str(self.timeout_spin.value())])

        # Recursion
        if self.recursion_check.isChecked():
            cmd_parts.append("-recursion")
            cmd_parts.extend(["-recursion-depth", str(self.recursion_depth.value())])

        # Extensions
        if self.extensions_input.text().strip():
            cmd_parts.extend(["-e", self.extensions_input.text().strip()])

        # Colored output
        cmd_parts.append("-c")

        self.command_input.setText(" ".join(cmd_parts))

    def run_scan(self):
        """Execute FFUF scan."""
        target = self.target_input.text().strip()
        if not target:
            self._notify("Please enter a target URL with FUZZ keyword")
            return

        if "FUZZ" not in target:
            self._notify("Target must contain FUZZ keyword for fuzzing")
            return

        wordlist = self.wordlist_input.text().strip()
        if not wordlist or not os.path.exists(wordlist):
            self._notify("Please select a valid wordlist file")
            return

        self.output.clear()
        self._info(f"Starting FFUF scan on: {target}")
        self._info(f"Wordlist: {wordlist}")
        self._info(f"Method: {self.method_combo.currentText()}")
        self._section("FFUF OUTPUT")

        # Extract target name from URL (domain/IP) - remove FUZZ and path
        try:
            # Remove protocol
            temp = target
            if "://" in temp:
                temp = temp.split("://", 1)[1]
            
            # Get domain/IP (everything before first /)
            target_name = temp.split("/")[0]
            
            # Remove port if present
            if ":" in target_name:
                target_name = target_name.split(":")[0]
            
            # Remove any remaining FUZZ or invalid chars
            target_name = target_name.replace("FUZZ", "").replace("<", "").replace(">", "")
            target_name = target_name.strip()
            
            # If empty after cleaning, use "target"
            if not target_name:
                target_name = "target"
        except:
            target_name = "target"
        
        self.base_dir = create_target_dirs(target_name, None)
        
        # FFUF will save its own JSON output
        json_output = os.path.join(self.base_dir, "Logs", "ffuf.json")

        command = self.command_input.text().split()
        command.extend(["-o", json_output, "-of", "json"])

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
            output_file = os.path.join(self.base_dir, "Logs", "ffuf.txt")
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(self.output.toPlainText())
                self._info(f"Results saved to: {output_file}")
            except Exception as e:
                self._error(f"Failed to save results: {e}")
        
        self.worker = None
        if self.main_window:
            self.main_window.active_process = None
        self._info("Scan completed")
        self._notify("FFUF scan completed.")

    def _on_output(self, line):
        """Handle real-time output - filter progress lines."""
        import re
        
        # Strip all ANSI escape codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        line = ansi_escape.sub('', line)
        
        # Skip pure progress lines (no actual results)
        if ":: Progress:" in line and "[Status:" not in line:
            return
        
        # Skip empty lines from filtering
        if not line.strip():
            return
        
        # Show everything else (header, results, etc.)
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
