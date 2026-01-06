# =============================================================================
# modules/gobuster.py
#
# Gobuster - Directory/File/DNS/VHost/Fuzz/S3 Brute-forcing Tool
# =============================================================================

import os
import shlex
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QFileDialog
)
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from core.tgtinput import TargetInput
from core.fileops import create_target_dirs
from ui.worker import ProcessWorker
from ui.styles import (
    # Widgets
    RunButton, StopButton, CopyButton, BrowseButton,
    StyledLineEdit, StyledSpinBox, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, CommandDisplay, OutputView,
    StyledGroupBox, ToolSplitter, ConfigTabs, StyledTextEdit,
    # Behaviors
    SafeStop, OutputHelper,
    # Constants
    TOOL_VIEW_STYLE, COLOR_BACKGROUND_SECONDARY
)


class GobusterTool(ToolBase):
    """Gobuster web brute-forcing tool plugin."""

    @property
    def name(self) -> str:
        return "Gobuster"

    @property
    def description(self) -> str:
        return "High-speed directory, file, and DNS brute-forcing tool."

    @property
    def category(self):
        return ToolCategory.WEB_SCANNING

    @property
    def icon(self) -> str:
        return "👻"

    def get_widget(self, main_window: QWidget) -> QWidget:
        return GobusterView("Gobuster", ToolCategory.WEB_SCANNING, main_window)


class GobusterView(QWidget, SafeStop, OutputHelper):
    """Gobuster directory/DNS/VHost/Fuzz/S3 brute-forcing interface."""
    
    tool_name = "Gobuster"
    tool_category = "WEB_SCANNING"
    
    def __init__(self, name, category, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_safe_stop()
        
        # State
        self.log_file = None
        self.raw_output = ""
        
        # Build UI
        self._build_ui()
        self.update_command()

    def _build_ui(self):
        """Build the complete UI."""
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
        
        # ==================== WORDLIST GROUP ====================
        wordlist_group = StyledGroupBox("🔤 Wordlist & Performance")
        wordlist_layout = QVBoxLayout(wordlist_group)
        wordlist_layout.setSpacing(8)
        
        wl_row = QHBoxLayout()
        wl_label = StyledLabel("Wordlist:")
        self.dict_input = StyledLineEdit("Select wordlist file...")
        self.dict_input.textChanged.connect(self.update_command)
        
        self.dict_browse_btn = BrowseButton()
        self.dict_browse_btn.clicked.connect(self._browse_dict)
        
        threads_label = StyledLabel("Threads:")
        self.threads_spin = StyledSpinBox()
        self.threads_spin.setRange(1, 100)
        self.threads_spin.setValue(10)
        self.threads_spin.valueChanged.connect(self.update_command)
        
        wl_row.addWidget(wl_label)
        wl_row.addWidget(self.dict_input, 1)
        wl_row.addWidget(self.dict_browse_btn)
        wl_row.addWidget(threads_label)
        wl_row.addWidget(self.threads_spin)
        wordlist_layout.addLayout(wl_row)
        control_layout.addWidget(wordlist_group)
        
        # ==================== MODE CONFIGURATION ====================
        config_group = StyledGroupBox("⚙️ Mode Configuration")
        config_layout = QVBoxLayout(config_group)
        config_layout.setContentsMargins(5, 15, 5, 5)
        config_layout.setSpacing(0)
        
        self.mode_tabs = ConfigTabs()
        
        # 1. Directory Tab
        dir_tab = QWidget()
        dir_layout = QGridLayout(dir_tab)
        dir_layout.setContentsMargins(10, 10, 10, 10)
        dir_layout.setSpacing(10)
        
        ext_label = StyledLabel("Ext (-x):")
        ext_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.dir_ext_input = StyledLineEdit("php,txt,html,jsp,asp")
        self.dir_ext_input.textChanged.connect(self.update_command)
        
        blacklist_label = StyledLabel("Blacklist (-b):")
        blacklist_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.dir_blacklist_input = StyledLineEdit("404,400-404")
        self.dir_blacklist_input.textChanged.connect(self.update_command)
        
        xl_label = StyledLabel("Excl Len (--xl):")
        xl_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.dir_xl_input = StyledLineEdit("e.g. 0 or 100-200")
        self.dir_xl_input.textChanged.connect(self.update_command)
        
        ua_label = StyledLabel("UA (-a):")
        ua_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.dir_ua_input = StyledLineEdit("User Agent")
        self.dir_ua_input.textChanged.connect(self.update_command)
        
        dir_layout.addWidget(ext_label, 0, 0)
        dir_layout.addWidget(self.dir_ext_input, 0, 1)
        dir_layout.addWidget(blacklist_label, 0, 2)
        dir_layout.addWidget(self.dir_blacklist_input, 0, 3)
        dir_layout.addWidget(xl_label, 1, 0)
        dir_layout.addWidget(self.dir_xl_input, 1, 1)
        dir_layout.addWidget(ua_label, 1, 2)
        dir_layout.addWidget(self.dir_ua_input, 1, 3)
        
        # Checkboxes
        hbox_checks = QHBoxLayout()
        self.dir_expanded_check = StyledCheckBox("Expanded (-e)")
        self.dir_expanded_check.stateChanged.connect(self.update_command)
        self.dir_k_check = StyledCheckBox("Skip TLS")
        self.dir_k_check.stateChanged.connect(self.update_command)
        self.dir_r_check = StyledCheckBox("Redirects")
        self.dir_r_check.stateChanged.connect(self.update_command)
        self.dir_f_check = StyledCheckBox("Add /")
        self.dir_f_check.stateChanged.connect(self.update_command)
        
        hbox_checks.addWidget(self.dir_expanded_check)
        hbox_checks.addWidget(self.dir_k_check)
        hbox_checks.addWidget(self.dir_r_check)
        hbox_checks.addWidget(self.dir_f_check)
        hbox_checks.addStretch()
        
        dir_layout.addLayout(hbox_checks, 2, 0, 1, 4)
        dir_layout.setColumnStretch(1, 3)
        dir_layout.setColumnStretch(3, 2)
        
        self.mode_tabs.addTab(dir_tab, "Dir")
        
        # 2. DNS Tab
        dns_tab = QWidget()
        dns_layout = QHBoxLayout(dns_tab)
        self.dns_show_ip_check = StyledCheckBox("Show IPs (-i)")
        self.dns_show_ip_check.stateChanged.connect(self.update_command)
        self.dns_wildcard_check = StyledCheckBox("Wildcard Force")
        self.dns_wildcard_check.stateChanged.connect(self.update_command)
        dns_layout.addWidget(self.dns_show_ip_check)
        dns_layout.addWidget(self.dns_wildcard_check)
        dns_layout.addStretch()
        self.mode_tabs.addTab(dns_tab, "DNS")
        
        # 3. VHost Tab
        vhost_tab = QWidget()
        vhost_layout = QHBoxLayout(vhost_tab)
        self.vhost_append_check = StyledCheckBox("Append Domain")
        self.vhost_append_check.stateChanged.connect(self.update_command)
        vhost_layout.addWidget(self.vhost_append_check)
        vhost_layout.addStretch()
        self.mode_tabs.addTab(vhost_tab, "VHost")
        
        # 4. Fuzz Tab
        fuzz_tab = QWidget()
        fuzz_main_layout = QVBoxLayout(fuzz_tab)
        fuzz_main_layout.setContentsMargins(10, 10, 10, 10)
        fuzz_main_layout.setSpacing(8)
        
        target_info = QLabel("⚠️ Target URL must contain 'FUZZ' keyword")
        target_info.setStyleSheet("""
            color: #FFA500;
            background-color: rgba(255, 165, 0, 0.1);
            border-left: 3px solid #FFA500;
            padding: 8px;
            border-radius: 4px;
        """)
        fuzz_main_layout.addWidget(target_info)
        
        fuzz_grid = QGridLayout()
        fuzz_grid.setSpacing(10)
        
        method_label = StyledLabel("HTTP Method:")
        method_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.fuzz_method_combo = StyledComboBox()
        self.fuzz_method_combo.addItems(["GET", "POST", "PUT", "PATCH", "DELETE"])
        self.fuzz_method_combo.currentTextChanged.connect(self.update_command)
        
        offset_label = StyledLabel("Offset:")
        offset_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.fuzz_wordlist_offset = StyledLineEdit("0")
        self.fuzz_wordlist_offset.textChanged.connect(self.update_command)
        
        fuzz_grid.addWidget(method_label, 0, 0)
        fuzz_grid.addWidget(self.fuzz_method_combo, 0, 1)
        fuzz_grid.addWidget(offset_label, 0, 2)
        fuzz_grid.addWidget(self.fuzz_wordlist_offset, 0, 3, 1, 3)
        
        body_label = StyledLabel("Request Body (-B):")
        self.fuzz_request_body = StyledTextEdit('{"user": "FUZZ"}')
        self.fuzz_request_body.setMaximumHeight(45)
        self.fuzz_request_body.textChanged.connect(self.update_command)
        
        fuzz_grid.addWidget(body_label, 1, 0, 1, 6)
        fuzz_grid.addWidget(self.fuzz_request_body, 2, 0, 1, 6)
        
        cookies_label = StyledLabel("Cookies:")
        cookies_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.fuzz_cookies_input = StyledLineEdit("session=FUZZ")
        self.fuzz_cookies_input.textChanged.connect(self.update_command)
        
        headers_label = StyledLabel("Header:")
        headers_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.fuzz_headers_text = StyledLineEdit("Authorization: Bearer FUZZ")
        self.fuzz_headers_text.textChanged.connect(self.update_command)
        
        proxy_label = StyledLabel("Proxy:")
        proxy_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.fuzz_proxy_input = StyledLineEdit("http://127.0.0.1:8080")
        self.fuzz_proxy_input.textChanged.connect(self.update_command)
        
        fuzz_grid.addWidget(cookies_label, 3, 0)
        fuzz_grid.addWidget(self.fuzz_cookies_input, 3, 1)
        fuzz_grid.addWidget(headers_label, 3, 2)
        fuzz_grid.addWidget(self.fuzz_headers_text, 3, 3)
        fuzz_grid.addWidget(proxy_label, 3, 4)
        fuzz_grid.addWidget(self.fuzz_proxy_input, 3, 5)
        
        status_label = StyledLabel("Exclude Status (-b):")
        status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.fuzz_exclude_status = StyledLineEdit("404,400-404")
        self.fuzz_exclude_status.textChanged.connect(self.update_command)
        
        length_label = StyledLabel("Exclude Length:")
        length_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.fuzz_exclude_length = StyledLineEdit("0,100-200")
        self.fuzz_exclude_length.textChanged.connect(self.update_command)
        
        fuzz_grid.addWidget(status_label, 4, 0)
        fuzz_grid.addWidget(self.fuzz_exclude_status, 4, 1, 1, 2)
        fuzz_grid.addWidget(length_label, 4, 3)
        fuzz_grid.addWidget(self.fuzz_exclude_length, 4, 4, 1, 2)
        
        fuzz_main_layout.addLayout(fuzz_grid)
        
        options_row = QHBoxLayout()
        delay_label = StyledLabel("Delay (ms):")
        self.fuzz_delay_spin = StyledSpinBox()
        self.fuzz_delay_spin.setRange(0, 5000)
        self.fuzz_delay_spin.setValue(0)
        self.fuzz_delay_spin.setSingleStep(50)
        self.fuzz_delay_spin.setSuffix(" ms")
        self.fuzz_delay_spin.valueChanged.connect(self.update_command)
        
        self.fuzz_skip_tls = StyledCheckBox("Skip TLS (-k)")
        self.fuzz_skip_tls.stateChanged.connect(self.update_command)
        
        self.fuzz_retry_check = StyledCheckBox("Retry")
        self.fuzz_retry_check.stateChanged.connect(self._on_fuzz_retry_toggle)
        
        retry_count_label = StyledLabel("Count:")
        self.fuzz_retry_count = StyledSpinBox()
        self.fuzz_retry_count.setRange(1, 10)
        self.fuzz_retry_count.setValue(3)
        self.fuzz_retry_count.setEnabled(False)
        self.fuzz_retry_count.valueChanged.connect(self.update_command)
        
        options_row.addWidget(delay_label)
        options_row.addWidget(self.fuzz_delay_spin)
        options_row.addWidget(self.fuzz_skip_tls)
        options_row.addWidget(self.fuzz_retry_check)
        options_row.addWidget(retry_count_label)
        options_row.addWidget(self.fuzz_retry_count)
        options_row.addStretch()
        
        fuzz_main_layout.addLayout(options_row)
        fuzz_main_layout.addStretch()
        
        self.mode_tabs.addTab(fuzz_tab, "Fuzz")
        
        # 5. S3 Tab
        s3_tab = QWidget()
        s3_layout = QVBoxLayout(s3_tab)
        s3_layout.setContentsMargins(10, 10, 10, 10)
        s3_layout.setSpacing(10)
        
        s3_info = StyledLabel("🪣 AWS S3 Bucket Enumeration")
        s3_layout.addWidget(s3_info)
        
        s3_options = QHBoxLayout()
        s3_maxfiles_label = StyledLabel("Max Files (-m):")
        self.s3_maxfiles_spin = StyledSpinBox()
        self.s3_maxfiles_spin.setRange(1, 100)
        self.s3_maxfiles_spin.setValue(5)
        self.s3_maxfiles_spin.valueChanged.connect(self.update_command)
        
        self.s3_k_check = StyledCheckBox("Skip TLS (-k)")
        self.s3_k_check.stateChanged.connect(self.update_command)
        
        s3_options.addWidget(s3_maxfiles_label)
        s3_options.addWidget(self.s3_maxfiles_spin)
        s3_options.addWidget(self.s3_k_check)
        s3_options.addStretch()
        
        s3_layout.addLayout(s3_options)
        s3_layout.addStretch()
        
        self.mode_tabs.addTab(s3_tab, "S3")
        
        self.mode_tabs.currentChanged.connect(self.update_command)
        config_layout.addWidget(self.mode_tabs)
        control_layout.addWidget(config_group)
        
        # Command Display
        self.command_input = CommandDisplay()
        control_layout.addWidget(self.command_input)
        
        control_layout.addStretch()
        splitter.addWidget(control_panel)
        
        # ==================== OUTPUT AREA ====================
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("Gobuster results will appear here...")
        
        self.copy_button = CopyButton(self.output.output_text, self.main_window)
        self.copy_button.setParent(self.output.output_text)
        self.copy_button.raise_()
        self.output.output_text.installEventFilter(self)
        
        splitter.addWidget(self.output)
        splitter.setSizes([450, 350])
        
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
    
    def _browse_dict(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Wordlist", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.dict_input.setText(file_path)
    
    def _on_fuzz_retry_toggle(self, state):
        self.fuzz_retry_count.setEnabled(state == 2)
        self.update_command()
    
    def _get_active_mode(self):
        idx = self.mode_tabs.currentIndex()
        modes = ["dir", "dns", "vhost", "fuzz", "s3"]
        return modes[idx] if idx < len(modes) else "dir"
    
    def update_command(self):
        target = self.target_input.get_target().strip()
        if not target:
            target = "<target>"
        
        mode = self._get_active_mode()
        cmd_parts = ["gobuster", mode]
        
        # Target handling
        if mode == "dns":
            cmd_parts.extend(["-d", target])
        elif mode == "s3":
            if target != "<target>":
                cmd_parts.append(target)
        elif mode == "fuzz":
            if not target.startswith("http") and target != "<target>":
                target = f"http://{target}"
            cmd_parts.extend(["-u", target])
        else:
            if not target.startswith("http") and target != "<target>":
                target = f"http://{target}"
            cmd_parts.extend(["-u", target])
        
        # Wordlist
        wordlist = self.dict_input.text().strip()
        if wordlist:
            cmd_parts.extend(["-w", wordlist])
        else:
            cmd_parts.extend(["-w", "<wordlist>"])
        
        # Threads
        threads = self.threads_spin.value()
        if threads != 10:
            cmd_parts.extend(["-t", str(threads)])
        
        # Mode Specifics
        if mode == "dir":
            exts = self.dir_ext_input.text().strip()
            if exts:
                cmd_parts.extend(["-x", exts])
            codes = self.dir_blacklist_input.text().strip()
            if codes:
                cmd_parts.extend(["-b", codes])
            ua = self.dir_ua_input.text().strip()
            if ua:
                cmd_parts.extend(["-a", shlex.quote(ua)])
            xl = self.dir_xl_input.text().strip()
            if xl:
                cmd_parts.extend(["--xl", xl])
            if self.dir_expanded_check.isChecked():
                cmd_parts.append("-e")
            if self.dir_k_check.isChecked():
                cmd_parts.append("-k")
            if self.dir_r_check.isChecked():
                cmd_parts.append("-r")
            if self.dir_f_check.isChecked():
                cmd_parts.append("-f")
        
        elif mode == "dns":
            if self.dns_show_ip_check.isChecked():
                cmd_parts.append("-i")
            if self.dns_wildcard_check.isChecked():
                cmd_parts.append("--wildcard")
        
        elif mode == "vhost":
            if self.vhost_append_check.isChecked():
                cmd_parts.append("--append-domain")
        
        elif mode == "fuzz":
            offset = self.fuzz_wordlist_offset.text().strip()
            if offset and offset != "0":
                cmd_parts.extend(["--offset", offset])
            body = self.fuzz_request_body.toPlainText().strip()
            if body:
                cmd_parts.extend(["-B", shlex.quote(body)])
            cookies = self.fuzz_cookies_input.text().strip()
            if cookies:
                cmd_parts.extend(["-c", shlex.quote(cookies)])
            header = self.fuzz_headers_text.text().strip()
            if header:
                cmd_parts.extend(["-H", shlex.quote(header)])
            proxy = self.fuzz_proxy_input.text().strip()
            if proxy:
                cmd_parts.extend(["--proxy", proxy])
            status_codes = self.fuzz_exclude_status.text().strip()
            if status_codes:
                cmd_parts.extend(["-b", status_codes])
            length = self.fuzz_exclude_length.text().strip()
            if length:
                cmd_parts.extend(["--exclude-length", length])
            delay = self.fuzz_delay_spin.value()
            if delay > 0:
                cmd_parts.extend(["--delay", f"{delay}ms"])
            if self.fuzz_skip_tls.isChecked():
                cmd_parts.append("-k")
            if self.fuzz_retry_check.isChecked():
                retry_count = self.fuzz_retry_count.value()
                cmd_parts.extend(["--retry", str(retry_count)])
        
        elif mode == "s3":
            maxfiles = self.s3_maxfiles_spin.value()
            if maxfiles != 5:
                cmd_parts.extend(["-m", str(maxfiles)])
            if self.s3_k_check.isChecked():
                cmd_parts.append("-k")
        
        self.command_input.setText(" ".join(cmd_parts))
    
    def run_scan(self):
        cmd_text = self.command_input.text().strip()
        if not cmd_text:
            return
        
        target = self.target_input.get_target().strip()
        if not target or "<target>" in cmd_text or "<wordlist>" in cmd_text:
            self._notify("Please provide a Target and Wordlist.")
            return
        
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.output.clear()
        self.raw_output = ""
        
        mode = self._get_active_mode()
        
        self._info(f"Running Gobuster ({mode.upper()}) for: {target}")
        self.output.appendPlainText("")
        self._section(f"GOBUSTER {mode.upper()}: {target}")
        
        try:
            base_dir = create_target_dirs(target, group_name=None)
            self.log_file = os.path.join(base_dir, "Logs", f"gobuster_{mode}.txt")
        except Exception as e:
            self._error(f"Failed to create log directories: {e}")
            self.log_file = None
        
        try:
            cmd_list = shlex.split(cmd_text)
        except ValueError:
            cmd_list = cmd_text.split()
        
        self.worker = ProcessWorker(cmd_list)
        self.worker.output_ready.connect(self._handle_output)
        self.worker.finished.connect(self._on_scan_completed)
        self.worker.start()
        
        if self.main_window:
            self.main_window.active_process = self.worker
    
    def _handle_output(self, text):
        self.output.appendPlainText(text)
        self.raw_output += text
    
    def _on_scan_completed(self):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        self.output.appendPlainText("\n✨ Scan Complete.")
        
        if self.log_file:
            try:
                with open(self.log_file, "w", encoding="utf-8") as f:
                    f.write(self.raw_output)
                if self.main_window:
                    self.main_window.notification_manager.notify(
                        f"Results saved to {os.path.basename(self.log_file)}"
                    )
            except Exception as e:
                self._error(f"Failed to write results to file: {e}")
        
        self.worker = None
        if self.main_window:
            self.main_window.active_process = None
