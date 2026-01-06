# =============================================================================
# modules/ffuf.py
#
# FFUF - Web Fuzzing Tool
# =============================================================================

import os
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog
)
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from core.fileops import create_target_dirs
from ui.worker import ProcessWorker
from ui.styles import (
    RunButton, StopButton, CopyButton, BrowseButton,
    StyledLineEdit, StyledSpinBox, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, CommandDisplay, OutputView,
    StyledGroupBox, ToolSplitter, ConfigTabs,
    SafeStop, OutputHelper,
    TOOL_VIEW_STYLE, COLOR_BACKGROUND_SECONDARY
)


class FFUFTool(ToolBase):
    """FFUF web fuzzing tool plugin."""

    @property
    def name(self) -> str:
        return "FFUF"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WEB_SCANNING

    def get_widget(self, main_window):
        return FfufView(name=self.name, category=self.category, main_window=main_window)


class FfufView(QWidget, SafeStop, OutputHelper):
    """FFUF web fuzzing interface."""
    
    tool_name = "FFUF"
    tool_category = "WEB_SCANNING"

    def __init__(self, name, category, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_safe_stop()
        
        # State
        self.base_dir = None
        
        # Build UI
        self._build_ui()
        self.update_command()

    def _build_ui(self):
        """Build complete UI."""
        self.setStyleSheet(TOOL_VIEW_STYLE)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

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
        target_label = StyledLabel("Target URL (use FUZZ keyword)")
        control_layout.addWidget(target_label)

        target_row = QHBoxLayout()
        self.target_input = StyledLineEdit("http://example.com/FUZZ")
        self.target_input.textChanged.connect(self.update_command)
        target_row.addWidget(self.target_input)
        
        self.run_button = RunButton()
        self.run_button.clicked.connect(self.run_scan)
        self.stop_button = StopButton()
        self.stop_button.clicked.connect(self.stop_scan)

        target_row.addWidget(self.run_button)
        target_row.addWidget(self.stop_button)
        control_layout.addLayout(target_row)

        # Wordlist Group
        wordlist_group = StyledGroupBox("📚 Wordlist")
        wordlist_layout = QHBoxLayout(wordlist_group)
        
        wl_label = StyledLabel("Wordlist:")
        wl_label.setFixedWidth(100)

        self.wordlist_input = StyledLineEdit("Select wordlist file...")
        self.wordlist_input.textChanged.connect(self.update_command)

        wl_browse = BrowseButton()
        wl_browse.clicked.connect(self._browse_wordlist)
        
        wordlist_layout.addWidget(wl_label)
        wordlist_layout.addWidget(self.wordlist_input)
        wordlist_layout.addWidget(wl_browse)
        control_layout.addWidget(wordlist_group)

        # Command Display
        self.command_input = CommandDisplay()
        control_layout.addWidget(self.command_input)

        # Configuration Tabs
        config_group = StyledGroupBox("⚙️ Configuration")
        config_layout = QVBoxLayout(config_group)
        config_layout.setContentsMargins(5, 15, 5, 5)
        config_layout.setSpacing(0)

        self.config_tabs = ConfigTabs()

        # ===== TAB 1: HTTP REQUEST =====
        request_tab = QWidget()
        request_layout = QGridLayout(request_tab)
        request_layout.setContentsMargins(10, 10, 10, 10)
        request_layout.setSpacing(10)
        request_layout.setColumnStretch(1, 1)
        request_layout.setColumnStretch(3, 1)

        method_label = StyledLabel("Method:")
        method_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.method_combo = StyledComboBox()
        self.method_combo.addItems(["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
        self.method_combo.currentTextChanged.connect(self.update_command)

        self.follow_redirects = StyledCheckBox("Follow Redirects")
        self.follow_redirects.stateChanged.connect(self.update_command)

        self.auto_calibrate = StyledCheckBox("Auto-Calibrate")
        self.auto_calibrate.setChecked(True)
        self.auto_calibrate.stateChanged.connect(self.update_command)

        headers_label = StyledLabel("Headers:")
        headers_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.headers_input = StyledLineEdit('"User-Agent: CustomUA"')
        self.headers_input.textChanged.connect(self.update_command)

        cookies_label = StyledLabel("Cookies:")
        cookies_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.cookies_input = StyledLineEdit("session=abc123; token=xyz789")
        self.cookies_input.textChanged.connect(self.update_command)

        data_label = StyledLabel("POST Data:")
        data_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.data_input = StyledLineEdit("username=admin&password=FUZZ")
        self.data_input.textChanged.connect(self.update_command)

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

        # ===== TAB 2: FILTERING =====
        filter_tab = QWidget()
        filter_layout = QGridLayout(filter_tab)
        filter_layout.setContentsMargins(10, 10, 10, 10)
        filter_layout.setSpacing(10)
        filter_layout.setColumnStretch(1, 1)
        filter_layout.setColumnStretch(3, 1)

        filter_sc_label = StyledLabel("Filter Status:")
        filter_sc_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.filter_status = StyledLineEdit("404,403")
        self.filter_status.textChanged.connect(self.update_command)

        match_sc_label = StyledLabel("Match Status:")
        match_sc_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.match_status = StyledLineEdit("200,301")
        self.match_status.textChanged.connect(self.update_command)

        filter_size_label = StyledLabel("Filter Size:")
        filter_size_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.filter_size = StyledLineEdit("bytes")
        self.filter_size.textChanged.connect(self.update_command)

        match_size_label = StyledLabel("Match Size:")
        match_size_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.match_size = StyledLineEdit("bytes")
        self.match_size.textChanged.connect(self.update_command)

        filter_words_label = StyledLabel("Filter Words:")
        filter_words_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.filter_words = StyledLineEdit("word count")
        self.filter_words.textChanged.connect(self.update_command)

        match_words_label = StyledLabel("Match Words:")
        match_words_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.match_words = StyledLineEdit("word count")
        self.match_words.textChanged.connect(self.update_command)

        filter_lines_label = StyledLabel("Filter Lines:")
        filter_lines_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.filter_lines = StyledLineEdit("line count")
        self.filter_lines.textChanged.connect(self.update_command)

        match_regex_label = StyledLabel("Match Regex:")
        match_regex_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.match_regex = StyledLineEdit('"admin.*panel"')
        self.match_regex.textChanged.connect(self.update_command)

        filter_regex_label = StyledLabel("Filter Regex:")
        filter_regex_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.filter_regex = StyledLineEdit('"error.*"')
        self.filter_regex.textChanged.connect(self.update_command)

        filter_mode_label = StyledLabel("Filter Mode:")
        filter_mode_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.filter_mode_combo = StyledComboBox()
        self.filter_mode_combo.addItems(["or", "and"])
        self.filter_mode_combo.currentTextChanged.connect(self.update_command)

        match_mode_label = StyledLabel("Match Mode:")
        match_mode_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.match_mode_combo = StyledComboBox()
        self.match_mode_combo.addItems(["or", "and"])
        self.match_mode_combo.currentTextChanged.connect(self.update_command)

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

        threads_label = StyledLabel("Threads:")
        threads_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.threads_spin = StyledSpinBox()
        self.threads_spin.setRange(1, 100)
        self.threads_spin.setValue(40)
        self.threads_spin.valueChanged.connect(self.update_command)

        delay_label = StyledLabel("Delay (ms):")
        delay_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.delay_spin = StyledSpinBox()
        self.delay_spin.setRange(0, 5000)
        self.delay_spin.setValue(0)
        self.delay_spin.setSuffix(" ms")
        self.delay_spin.valueChanged.connect(self.update_command)

        rate_label = StyledLabel("Rate Limit:")
        rate_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.rate_spin = StyledSpinBox()
        self.rate_spin.setRange(0, 10000)
        self.rate_spin.setValue(0)
        self.rate_spin.setSpecialValueText("Unlimited")
        self.rate_spin.setSuffix(" req/s")
        self.rate_spin.valueChanged.connect(self.update_command)

        timeout_label = StyledLabel("Timeout (s):")
        timeout_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.timeout_spin = StyledSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(10)
        self.timeout_spin.setSuffix(" s")
        self.timeout_spin.valueChanged.connect(self.update_command)

        self.recursion_check = StyledCheckBox("Recursive Fuzzing")
        self.recursion_check.stateChanged.connect(self.update_command)

        recursion_depth_label = StyledLabel("Depth:")
        recursion_depth_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.recursion_depth = StyledSpinBox()
        self.recursion_depth.setRange(1, 10)
        self.recursion_depth.setValue(1)
        self.recursion_depth.setEnabled(False)
        self.recursion_depth.valueChanged.connect(self.update_command)
        self.recursion_check.stateChanged.connect(
            lambda: self.recursion_depth.setEnabled(self.recursion_check.isChecked())
        )

        ext_label = StyledLabel("Extensions:")
        ext_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.extensions_input = StyledLineEdit(".php,.html,.js")
        self.extensions_input.textChanged.connect(self.update_command)

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

        splitter.addWidget(control_panel)

        # ==================== OUTPUT AREA ====================
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("FFUF results will appear here...")

        self.copy_button = CopyButton(self.output.output_text, self.main_window)
        self.copy_button.setParent(self.output.output_text)
        self.copy_button.raise_()
        self.output.output_text.installEventFilter(self)

        splitter.addWidget(self.output)
        splitter.setSizes([400, 400])

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

    def _browse_wordlist(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Wordlist", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.wordlist_input.setText(file_path)

    def update_command(self):
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

        if self.method_combo.currentText() != "GET":
            cmd_parts.extend(["-X", self.method_combo.currentText()])

        headers = self.headers_input.text().strip()
        if headers:
            for header in headers.split('"'):
                header = header.strip()
                if header and ":" in header:
                    cmd_parts.extend(["-H", f'"{header}"'])

        cookies = self.cookies_input.text().strip()
        if cookies:
            cmd_parts.extend(["-b", f'"{cookies}"'])

        data = self.data_input.text().strip()
        if data:
            cmd_parts.extend(["-d", f'"{data}"'])

        if self.follow_redirects.isChecked():
            cmd_parts.append("-r")
        if self.auto_calibrate.isChecked():
            cmd_parts.append("-ac")

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

        if self.threads_spin.value() != 40:
            cmd_parts.extend(["-t", str(self.threads_spin.value())])
        if self.delay_spin.value() > 0:
            cmd_parts.extend(["-p", f"{self.delay_spin.value()/1000:.3f}"])
        if self.rate_spin.value() > 0:
            cmd_parts.extend(["-rate", str(self.rate_spin.value())])
        if self.timeout_spin.value() != 10:
            cmd_parts.extend(["-timeout", str(self.timeout_spin.value())])

        if self.recursion_check.isChecked():
            cmd_parts.append("-recursion")
            cmd_parts.extend(["-recursion-depth", str(self.recursion_depth.value())])

        if self.extensions_input.text().strip():
            cmd_parts.extend(["-e", self.extensions_input.text().strip()])

        cmd_parts.append("-c")

        self.command_input.setText(" ".join(cmd_parts))

    def run_scan(self):
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

        try:
            temp = target
            if "://" in temp:
                temp = temp.split("://", 1)[1]
            target_name = temp.split("/")[0]
            if ":" in target_name:
                target_name = target_name.split(":")[0]
            target_name = target_name.replace("FUZZ", "").replace("<", "").replace(">", "").strip()
            if not target_name:
                target_name = "target"
        except:
            target_name = "target"
        
        self.base_dir = create_target_dirs(target_name, None)
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

    def _on_scan_completed(self):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
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
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        line = ansi_escape.sub('', line)
        
        if ":: Progress:" in line and "[Status:" not in line:
            return
        
        if not line.strip():
            return
        
        self.output.append(line)
