
import os
import shlex
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QCheckBox, QGroupBox,
    QGridLayout, QSplitter, QFileDialog, QTabWidget,
    QSpinBox, QComboBox, QTextEdit,  QScrollArea, QToolButton
)
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from ui.widgets import BaseToolView
from ui.worker import ProcessWorker
from core.fileops import create_target_dirs
from ui.styles import (
    COLOR_BACKGROUND_INPUT, COLOR_TEXT_PRIMARY, COLOR_BORDER, 
    COLOR_BORDER_INPUT_FOCUSED
)

# ==============================
# Gobuster Tool
# ==============================

class GobusterTool(ToolBase):
    """Web and DNS Brute-forcing tool."""

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
        return GobusterToolView("Gobuster", ToolCategory.WEB_SCANNING, main_window)


class GobusterToolView(BaseToolView):
    def __init__(self, name, category, main_window):
        # Initialize attributes
        self.mode_tabs = None
        self.dict_input = None
        self.dict_browse_btn = None
        self.threads_spin = None
        
        # Directory Mode Widgets
        self.dir_ext_input = None
        self.dir_blacklist_input = None
        self.dir_expanded_check = None
        self.dir_ua_input = None
        self.dir_xl_input = None
        self.dir_k_check = None
        self.dir_r_check = None
        self.dir_f_check = None
        
        # DNS Mode Widgets
        self.dns_wildcard_check = None
        self.dns_show_ip_check = None
        
        # VHost Mode Widgets
        self.vhost_append_check = None

        # Fuzz Mode Widgets (Compact)
        # Request Definition
        self.fuzz_method_combo = None
        self.fuzz_wordlist_offset = None
        self.fuzz_request_body = None
        
        # Headers & Auth
        self.fuzz_cookies_input = None
        self.fuzz_headers_text = None
        self.fuzz_proxy_input = None
        
        # Filters
        self.fuzz_exclude_status = None
        self.fuzz_exclude_length = None
        
        # Performance
        self.fuzz_delay_spin = None
        self.fuzz_skip_tls = None
        self.fuzz_retry_check = None
        self.fuzz_retry_count = None

        # S3 Mode Widgets
        self.s3_maxfiles_spin = None
        self.s3_k_check = None

        self.timeout_input = None
        
        super().__init__(name, category, main_window)
        
        # Custom UI
        self._build_custom_ui()
        self.update_command()

    def _get_active_mode(self):
        idx = self.mode_tabs.currentIndex()
        if idx == 0: return "dir"
        if idx == 1: return "dns"
        if idx == 2: return "vhost"
        if idx == 3: return "fuzz"
        if idx == 4: return "s3"
        return "dir"

    def _build_custom_ui(self):
        splitter = self.findChild(QSplitter)
        control_panel = splitter.widget(0)
        control_layout = control_panel.layout()
        
        insertion_index = 3

        # ==================== WORDLIST & GLOBAL OPTIONS ====================
        wordlist_group = QGroupBox("🔤 Wordlist & Performance")
        wordlist_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLOR_TEXT_PRIMARY};
                border: 2px solid {COLOR_BORDER};
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
        wordlist_layout = QVBoxLayout(wordlist_group)
        wordlist_layout.setSpacing(8)

        # Wordlist row
        wl_row = QHBoxLayout()
        wl_label = QLabel("Wordlist:")
        wl_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        wl_label.setFixedWidth(70)

        self.dict_input = QLineEdit()
        self.dict_input.setPlaceholderText("Select wordlist file...")
        self.dict_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
                min-height: 20px;
            }}
            QLineEdit:focus {{ border: 1px solid {COLOR_BORDER_INPUT_FOCUSED}; }}
        """)
        self.dict_input.textChanged.connect(self.update_command)
        
        self.dict_browse_btn = QPushButton("📁 Browse")
        self.dict_browse_btn.setFixedWidth(100)
        self.dict_browse_btn.setCursor(Qt.PointingHandCursor)
        self.dict_browse_btn.clicked.connect(self._browse_dict)
        self.dict_browse_btn.setStyleSheet(f"""
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
        wl_row.addWidget(self.dict_input)
        wl_row.addWidget(self.dict_browse_btn)
        wordlist_layout.addLayout(wl_row)

        # Performance row (Threads & Timeout)
        perf_row = QHBoxLayout()
        
        thread_label = QLabel("Threads:")
        thread_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        thread_label.setFixedWidth(70)
        
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 500)
        self.threads_spin.setValue(10)
        self.threads_spin.setFixedWidth(80)
        self.threads_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        self.threads_spin.valueChanged.connect(self.update_command)

        timeout_label = QLabel("Timeout:")
        timeout_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        timeout_label.setFixedWidth(70)
        
        self.timeout_input = QLineEdit()
        self.timeout_input.setPlaceholderText("10s")
        self.timeout_input.setFixedWidth(80)
        self.timeout_input.setStyleSheet(self.dict_input.styleSheet())
        self.timeout_input.textChanged.connect(self.update_command)

        perf_row.addWidget(thread_label)
        perf_row.addWidget(self.threads_spin)
        perf_row.addSpacing(20)
        perf_row.addWidget(timeout_label)
        perf_row.addWidget(self.timeout_input)
        perf_row.addStretch()
        wordlist_layout.addLayout(perf_row)

        control_layout.insertWidget(insertion_index, wordlist_group)
        insertion_index += 1

        # ==================== CONFIGURATION TABS ====================
        config_group = QGroupBox("⚙️ Scan Configuration")
        config_group.setStyleSheet(wordlist_group.styleSheet())
        config_layout = QVBoxLayout(config_group)
        config_layout.setContentsMargins(5, 15, 5, 5)
        config_layout.setSpacing(0)

        # --- Tabs for Modes ---
        self.mode_tabs = QTabWidget()
        self.mode_tabs.setStyleSheet(f"""
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
        
        config_layout.addWidget(self.mode_tabs)
        control_layout.insertWidget(insertion_index, config_group)
        
        # 1. Directory Tab
        dir_tab = QWidget()
        dir_layout = QGridLayout(dir_tab)
        dir_layout.setContentsMargins(10, 10, 10, 10)
        dir_layout.setSpacing(10)
        
        self.dir_ext_input = QLineEdit()
        self.dir_ext_input.setPlaceholderText("php,txt,html,jsp,asp,aspx,js")
        self.dir_ext_input.setStyleSheet(self.dict_input.styleSheet())
        self.dir_ext_input.textChanged.connect(self.update_command)
        
        self.dir_blacklist_input = QLineEdit()
        self.dir_blacklist_input.setPlaceholderText("404,400-404")
        self.dir_blacklist_input.setStyleSheet(self.dict_input.styleSheet())
        self.dir_blacklist_input.textChanged.connect(self.update_command)
        
        self.dir_xl_input = QLineEdit()
        self.dir_xl_input.setPlaceholderText("e.g. 0 or 100-200")
        self.dir_xl_input.setStyleSheet(self.dict_input.styleSheet())
        self.dir_xl_input.textChanged.connect(self.update_command)

        self.dir_ua_input = QLineEdit()
        self.dir_ua_input.setPlaceholderText("User Agent")
        self.dir_ua_input.setStyleSheet(self.dict_input.styleSheet())
        self.dir_ua_input.textChanged.connect(self.update_command)

        # Row 0: Ext | Blacklist
        ext_label = QLabel("Ext (-x):")
        ext_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        ext_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        dir_layout.addWidget(ext_label, 0, 0)
        dir_layout.addWidget(self.dir_ext_input, 0, 1)
        
        blacklist_label = QLabel("Blacklist (-b):")
        blacklist_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        blacklist_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        dir_layout.addWidget(blacklist_label, 0, 2)
        dir_layout.addWidget(self.dir_blacklist_input, 0, 3)

        # Row 1: Exclude Length | User Agent
        xl_label = QLabel("Excl Len (--xl):")
        xl_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        xl_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        dir_layout.addWidget(xl_label, 1, 0)
        dir_layout.addWidget(self.dir_xl_input, 1, 1)
        
        ua_label = QLabel("UA (-a):")
        ua_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        ua_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        dir_layout.addWidget(ua_label, 1, 2)
        dir_layout.addWidget(self.dir_ua_input, 1, 3)

        # Row 2: Checkboxes (Spanning 4 cols)
        hbox_checks = QHBoxLayout()
        
        self.dir_expanded_check = QCheckBox("Expanded (-e)")
        self.dir_expanded_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.dir_expanded_check.stateChanged.connect(self.update_command)
        
        self.dir_k_check = QCheckBox("Skip TLS")
        self.dir_k_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.dir_k_check.stateChanged.connect(self.update_command)
        
        self.dir_r_check = QCheckBox("Redirects")
        self.dir_r_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.dir_r_check.stateChanged.connect(self.update_command)

        self.dir_f_check = QCheckBox("Add /")
        self.dir_f_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.dir_f_check.stateChanged.connect(self.update_command)

        hbox_checks.addWidget(self.dir_expanded_check)
        hbox_checks.addWidget(self.dir_k_check)
        hbox_checks.addWidget(self.dir_r_check)
        hbox_checks.addWidget(self.dir_f_check)
        hbox_checks.addStretch()

        dir_layout.addLayout(hbox_checks, 2, 0, 1, 4)

        # Minimum column widths to prevent crushing
        dir_layout.setColumnMinimumWidth(1, 150)
        dir_layout.setColumnMinimumWidth(3, 120)
        
        # Balanced column stretches for professional look
        dir_layout.setColumnStretch(1, 3)  # Ext/Excl Len column
        dir_layout.setColumnStretch(3, 2)  # Blacklist/UA column

        self.mode_tabs.addTab(dir_tab, "Dir")

        # 2. DNS Tab
        dns_tab = QWidget()
        dns_layout = QHBoxLayout(dns_tab)
        self.dns_show_ip_check = QCheckBox("Show IPs (-i)")
        self.dns_show_ip_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.dns_show_ip_check.stateChanged.connect(self.update_command)
        self.dns_wildcard_check = QCheckBox("Wildcard Force")
        self.dns_wildcard_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.dns_wildcard_check.stateChanged.connect(self.update_command)
        dns_layout.addWidget(self.dns_show_ip_check)
        dns_layout.addWidget(self.dns_wildcard_check)
        dns_layout.addStretch()
        self.mode_tabs.addTab(dns_tab, "DNS")

        # 3. VHost Tab
        vhost_tab = QWidget()
        vhost_layout = QHBoxLayout(vhost_tab)
        self.vhost_append_check = QCheckBox("Append Domain")
        self.vhost_append_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.vhost_append_check.stateChanged.connect(self.update_command)
        vhost_layout.addWidget(self.vhost_append_check)
        vhost_layout.addStretch()
        self.mode_tabs.addTab(vhost_tab, "VHost")


        # 4. FUZZ Tab - Grid Layout with Dynamic Sizing
        fuzz_tab = QWidget()
        fuzz_main_layout = QVBoxLayout(fuzz_tab)
        fuzz_main_layout.setContentsMargins(10, 10, 10, 10)
        fuzz_main_layout.setSpacing(8)
        
        # Prominent Warning
        target_info = QLabel("⚠️ Target URL must contain 'FUZZ' keyword (e.g., https://target.com/api/FUZZ)")
        target_info.setStyleSheet(f"""
            color: #FFA500;
            background-color: rgba(255, 165, 0, 0.1);
            border-left: 3px solid #FFA500;
            padding: 8px;
            border-radius: 4px;
            font-style: italic;
        """)
        target_info.setWordWrap(True)
        fuzz_main_layout.addWidget(target_info)
        
        # Grid for inputs (6 columns for more flexibility)
        fuzz_grid = QGridLayout()
        fuzz_grid.setSpacing(10)
        
        # Row 0: HTTP Method | Offset
        method_label = QLabel("HTTP Method:")
        method_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        method_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.fuzz_method_combo = QComboBox()
        self.fuzz_method_combo.addItems(["GET", "POST", "PUT", "PATCH", "DELETE"])
        self.fuzz_method_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        self.fuzz_method_combo.currentTextChanged.connect(self.update_command)
        
        offset_label = QLabel("Offset:")
        offset_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        offset_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.fuzz_wordlist_offset = QLineEdit()
        self.fuzz_wordlist_offset.setPlaceholderText("0")
        self.fuzz_wordlist_offset.setStyleSheet(self.dict_input.styleSheet())
        self.fuzz_wordlist_offset.textChanged.connect(self.update_command)
        
        fuzz_grid.addWidget(method_label, 0, 0)
        fuzz_grid.addWidget(self.fuzz_method_combo, 0, 1)
        fuzz_grid.addWidget(offset_label, 0, 2)
        fuzz_grid.addWidget(self.fuzz_wordlist_offset, 0, 3, 1, 3)
        
        # Row 1: Request Body (full width) - 2 lines only
        body_label = QLabel("Request Body (-B):")
        body_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.fuzz_request_body = QTextEdit()
        self.fuzz_request_body.setPlaceholderText('{{"user": "FUZZ"}}')
        self.fuzz_request_body.setMaximumHeight(45)  # 2 lines only
        self.fuzz_request_body.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                font-family: monospace;
            }}
        """)
        self.fuzz_request_body.textChanged.connect(self.update_command)
        
        fuzz_grid.addWidget(body_label, 1, 0, 1, 6)
        fuzz_grid.addWidget(self.fuzz_request_body, 2, 0, 1, 6)
        
        # Row 3: Cookies | Header | Proxy (ALL in one row)
        cookies_label = QLabel("Cookies:")
        cookies_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        cookies_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.fuzz_cookies_input = QLineEdit()
        self.fuzz_cookies_input.setPlaceholderText("session=FUZZ")
        self.fuzz_cookies_input.setStyleSheet(self.dict_input.styleSheet())
        self.fuzz_cookies_input.textChanged.connect(self.update_command)
        
        headers_label = QLabel("Header:")
        headers_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        headers_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.fuzz_headers_text = QLineEdit()
        self.fuzz_headers_text.setPlaceholderText("Authorization: Bearer FUZZ")
        self.fuzz_headers_text.setStyleSheet(self.dict_input.styleSheet())
        self.fuzz_headers_text.textChanged.connect(self.update_command)
        
        proxy_label = QLabel("Proxy:")
        proxy_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        proxy_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.fuzz_proxy_input = QLineEdit()
        self.fuzz_proxy_input.setPlaceholderText("http://127.0.0.1:8080")
        self.fuzz_proxy_input.setStyleSheet(self.dict_input.styleSheet())
        self.fuzz_proxy_input.textChanged.connect(self.update_command)
        
        fuzz_grid.addWidget(cookies_label, 3, 0)
        fuzz_grid.addWidget(self.fuzz_cookies_input, 3, 1)
        fuzz_grid.addWidget(headers_label, 3, 2)
        fuzz_grid.addWidget(self.fuzz_headers_text, 3, 3)
        fuzz_grid.addWidget(proxy_label, 3, 4)
        fuzz_grid.addWidget(self.fuzz_proxy_input, 3, 5)
        
        # Row 4: Exclude Status | Exclude Length
        status_label = QLabel("Exclude Status (-b):")
        status_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.fuzz_exclude_status = QLineEdit()
        self.fuzz_exclude_status.setPlaceholderText("404,400-404")
        self.fuzz_exclude_status.setStyleSheet(self.dict_input.styleSheet())
        self.fuzz_exclude_status.textChanged.connect(self.update_command)
        
        length_label = QLabel("Exclude Length:")
        length_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        length_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.fuzz_exclude_length = QLineEdit()
        self.fuzz_exclude_length.setPlaceholderText("0,100-200")
        self.fuzz_exclude_length.setStyleSheet(self.dict_input.styleSheet())
        self.fuzz_exclude_length.textChanged.connect(self.update_command)
        
        fuzz_grid.addWidget(status_label, 4, 0)
        fuzz_grid.addWidget(self.fuzz_exclude_status, 4, 1, 1, 2)
        fuzz_grid.addWidget(length_label, 4, 3)
        fuzz_grid.addWidget(self.fuzz_exclude_length, 4, 4, 1, 2)
        
        # Minimum column widths to prevent crushing
        fuzz_grid.setColumnMinimumWidth(1, 120)
        fuzz_grid.setColumnMinimumWidth(3, 120)
        fuzz_grid.setColumnMinimumWidth(5, 120)
        
        # Set column stretches for dynamic sizing
        fuzz_grid.setColumnStretch(1, 2)  # Cookies/Status column
        fuzz_grid.setColumnStretch(3, 2)  # Header column
        fuzz_grid.setColumnStretch(5, 1)  # Proxy/Length column
        
        fuzz_main_layout.addLayout(fuzz_grid)
        
        # Row 6: Options (HBox for checkboxes/spinboxes)
        options_row = QHBoxLayout()
        
        delay_label = QLabel("Delay (ms):")
        delay_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.fuzz_delay_spin = QSpinBox()
        self.fuzz_delay_spin.setRange(0, 5000)
        self.fuzz_delay_spin.setValue(0)
        self.fuzz_delay_spin.setSingleStep(50)
        self.fuzz_delay_spin.setFixedWidth(80)
        self.fuzz_delay_spin.setSuffix(" ms")
        self.fuzz_delay_spin.setStyleSheet(self.threads_spin.styleSheet())
        self.fuzz_delay_spin.valueChanged.connect(self.update_command)
        
        self.fuzz_skip_tls = QCheckBox("Skip TLS (-k)")
        self.fuzz_skip_tls.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.fuzz_skip_tls.stateChanged.connect(self.update_command)
        
        self.fuzz_retry_check = QCheckBox("Retry")
        self.fuzz_retry_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.fuzz_retry_check.stateChanged.connect(self._on_fuzz_retry_toggle)
        
        retry_count_label = QLabel("Count:")
        retry_count_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.fuzz_retry_count = QSpinBox()
        self.fuzz_retry_count.setRange(1, 10)
        self.fuzz_retry_count.setValue(3)
        self.fuzz_retry_count.setFixedWidth(60)
        self.fuzz_retry_count.setStyleSheet(self.threads_spin.styleSheet())
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
        
        s3_info = QLabel("🪣 AWS S3 Bucket Enumeration - Target should be bucket name or keyword")
        s3_info.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-style: italic;")
        s3_layout.addWidget(s3_info)
        
        s3_options = QHBoxLayout()
        
        s3_maxfiles_label = QLabel("Max Files (-m):")
        s3_maxfiles_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.s3_maxfiles_spin = QSpinBox()
        self.s3_maxfiles_spin.setRange(1, 100)
        self.s3_maxfiles_spin.setValue(5)
        self.s3_maxfiles_spin.setFixedWidth(60)
        self.s3_maxfiles_spin.setStyleSheet(self.threads_spin.styleSheet())
        self.s3_maxfiles_spin.valueChanged.connect(self.update_command)
        
        self.s3_k_check = QCheckBox("Skip TLS (-k)")
        self.s3_k_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.s3_k_check.stateChanged.connect(self.update_command)
        
        s3_options.addWidget(s3_maxfiles_label)
        s3_options.addWidget(self.s3_maxfiles_spin)
        s3_options.addWidget(self.s3_k_check)
        s3_options.addStretch()
        
        s3_layout.addLayout(s3_options)
        s3_layout.addStretch()
        
        self.mode_tabs.addTab(s3_tab, "S3")


        # Connect Tab Change
        self.mode_tabs.currentChanged.connect(self.update_command)

        config_layout.addWidget(self.mode_tabs)
        control_layout.insertWidget(insertion_index, config_group)


    def _browse_dict(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Wordlist", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            self.dict_input.setText(file_path)

    # ═══════════════════════════════════════════════════════════
    # FUZZ MODE HELPER METHODS
    # ═══════════════════════════════════════════════════════════
    
    def _on_fuzz_retry_toggle(self, state):
        """Toggle retry count spinner"""
        self.fuzz_retry_count.setEnabled(state == 2)  # 2 = Checked
        self.update_command()

    def _get_active_mode(self):
        idx = self.mode_tabs.currentIndex()
        if idx == 0: return "dir"
        if idx == 1: return "dns"
        if idx == 2: return "vhost"
        return "dir"

    def update_command(self):
        # Safety check: if called before custom UI is built (e.g. by BaseToolView.__init__)
        if self.mode_tabs is None:
            return

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
            # Dir and VHost need URL
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

        # Timeout
        if self.timeout_input:
             to_val = self.timeout_input.text().strip()
             if to_val:
                 cmd_parts.extend(["--timeout", to_val])

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
            # Wordlist Offset
            offset = self.fuzz_wordlist_offset.text().strip()
            if offset and offset != "0":
                cmd_parts.extend(["--offset", offset])
            
            # Request Body
            body = self.fuzz_request_body.toPlainText().strip()
            if body:
                cmd_parts.extend(["-B", shlex.quote(body)])
            
            # Cookies
            cookies = self.fuzz_cookies_input.text().strip()
            if cookies:
                cmd_parts.extend(["-c", shlex.quote(cookies)])
            
            # Header (single line)
            header = self.fuzz_headers_text.text().strip()
            if header:
                cmd_parts.extend(["-H", shlex.quote(header)])
            
            # Proxy
            proxy = self.fuzz_proxy_input.text().strip()
            if proxy:
                cmd_parts.extend(["--proxy", proxy])
            
            # Filters
            status_codes = self.fuzz_exclude_status.text().strip()
            if status_codes:
                cmd_parts.extend(["-b", status_codes])
            
            length = self.fuzz_exclude_length.text().strip()
            if length:
                cmd_parts.extend(["--exclude-length", length])
            
            # Performance
            delay = self.fuzz_delay_spin.value()
            if delay > 0:
                cmd_parts.extend(["--delay", f"{delay}ms"])
            
            # TLS
            if self.fuzz_skip_tls.isChecked():
                cmd_parts.append("-k")
            
            # Retry
            if self.fuzz_retry_check.isChecked():
                retry_count = self.fuzz_retry_count.value()
                cmd_parts.extend(["--retry", str(retry_count)])

        elif mode == "s3":
            # Max files
            maxfiles = self.s3_maxfiles_spin.value()
            if maxfiles != 5:
                cmd_parts.extend(["-m", str(maxfiles)])
            
            # Skip TLS
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
        
        # UI Header
        self._info(f"Running Gobuster ({mode.upper()}) for: {target}")
        self.output.appendPlainText("") 
        self._section(f"GOBUSTER {mode.upper()}: {target}")

        # Setup File Saving
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
        super()._on_scan_completed()
        
        self.output.appendPlainText("\n✨ Scan Complete.")
        
        if self.log_file:
            try:
                with open(self.log_file, "w", encoding="utf-8") as f:
                    # Clean ANSI codes if desired, but raw output might be preferred
                    # Gobuster output is simple enough to save as is usually
                    f.write(self.raw_output)
                if self.main_window:
                    self.main_window.notification_manager.notify(f"Results saved to {os.path.basename(self.log_file)}")
            except Exception as e:
                self._error(f"Failed to write results to file: {e}")
