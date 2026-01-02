# =============================================================================
# modules/nuclei.py
#
# Professional Nuclei Vulnerability Scanner GUI
# Comprehensive template-based vulnerability scanning with all advanced options
# =============================================================================

import os
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QCheckBox, QComboBox, QFileDialog,
    QTextEdit, QGridLayout, QSplitter, QTabWidget, QMessageBox,
    QListWidget, QListWidgetItem, QAbstractItemView
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


class NucleiTool(ToolBase):
    """Professional Nuclei vulnerability scanner tool."""

    @property
    def name(self) -> str:
        return "Nuclei"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.VULNERABILITY_SCANNER

    def get_widget(self, main_window):
        return NucleiToolView(main_window=main_window)


class NucleiToolView(QWidget, StoppableToolMixin):
    """Nuclei vulnerability scanner interface."""

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
        header = QLabel("VULNERABILITY_SCANNER › Nuclei")
        header.setStyleSheet(TOOL_HEADER_STYLE)
        control_layout.addWidget(header)

        # Target input row
        target_label = QLabel("Target")
        target_label.setStyleSheet(LABEL_STYLE)
        control_layout.addWidget(target_label)

        target_row = QHBoxLayout()
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("http://example.com or IP address")
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

        self.target_list_btn = QPushButton("📁")
        self.target_list_btn.setToolTip("Load targets from file")
        self.target_list_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_BACKGROUND_INPUT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 16px;
            }}
            QPushButton:hover {{ background-color: #4A4A4A; }}
        """)
        self.target_list_btn.clicked.connect(self._browse_target_list)
        self.target_list_btn.setCursor(Qt.PointingHandCursor)

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
        target_row.addWidget(self.target_list_btn)
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
                padding: 8px 12px;
                font-size: 12px;
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

        # Build all tabs
        self._build_templates_tab()
        self._build_filters_tab()
        self._build_rate_tab()
        self._build_network_tab()
        self._build_output_tab()
        self._build_advanced_tab()

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
        self.output.setPlaceholderText("Nuclei scan results will appear here...")
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
        self.output.installEventFilter(self)

        splitter.addWidget(control_panel)
        splitter.addWidget(output_container)
        splitter.setSizes([450, 350])

        self.update_command()

    def _build_templates_tab(self):
        """Build Templates tab with file/folder selection."""
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Template file/folder selection
        tmpl_label = QLabel("Templates:")
        tmpl_label.setStyleSheet(LABEL_STYLE)
        tmpl_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.template_input = QLineEdit()
        self.template_input.setPlaceholderText("Template path or directory")
        self.template_input.setStyleSheet(self.target_input.styleSheet())
        self.template_input.textChanged.connect(self.update_command)

        self.tmpl_file_btn = QPushButton("📄 File")
        self.tmpl_file_btn.setToolTip("Select template file(s)")
        self.tmpl_file_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_BACKGROUND_INPUT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 6px 10px;
                color: {COLOR_TEXT_PRIMARY};
            }}
            QPushButton:hover {{ background-color: #4A4A4A; }}
        """)
        self.tmpl_file_btn.clicked.connect(self._browse_template_file)
        self.tmpl_file_btn.setCursor(Qt.PointingHandCursor)

        self.tmpl_folder_btn = QPushButton("📁 Folder")
        self.tmpl_folder_btn.setToolTip("Select template folder")
        self.tmpl_folder_btn.setStyleSheet(self.tmpl_file_btn.styleSheet())
        self.tmpl_folder_btn.clicked.connect(self._browse_template_folder)
        self.tmpl_folder_btn.setCursor(Qt.PointingHandCursor)

        tmpl_btn_row = QHBoxLayout()
        tmpl_btn_row.addWidget(self.template_input)
        tmpl_btn_row.addWidget(self.tmpl_file_btn)
        tmpl_btn_row.addWidget(self.tmpl_folder_btn)

        # Workflow file
        wf_label = QLabel("Workflow:")
        wf_label.setStyleSheet(LABEL_STYLE)
        wf_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.workflow_input = QLineEdit()
        self.workflow_input.setPlaceholderText("Workflow file path")
        self.workflow_input.setStyleSheet(self.target_input.styleSheet())
        self.workflow_input.textChanged.connect(self.update_command)

        self.wf_btn = QPushButton("📄")
        self.wf_btn.setStyleSheet(self.tmpl_file_btn.styleSheet())
        self.wf_btn.clicked.connect(self._browse_workflow)
        self.wf_btn.setCursor(Qt.PointingHandCursor)

        # Exclude templates
        excl_label = QLabel("Exclude:")
        excl_label.setStyleSheet(LABEL_STYLE)
        excl_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.exclude_tmpl_input = QLineEdit()
        self.exclude_tmpl_input.setPlaceholderText("Templates to exclude")
        self.exclude_tmpl_input.setStyleSheet(self.target_input.styleSheet())
        self.exclude_tmpl_input.textChanged.connect(self.update_command)

        # Template list option
        self.auto_scan_check = QCheckBox("Auto-Scan (detect tech)")
        self.auto_scan_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
        self.auto_scan_check.stateChanged.connect(self.update_command)

        self.new_templates_check = QCheckBox("New Templates Only")
        self.new_templates_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
        self.new_templates_check.stateChanged.connect(self.update_command)

        # Layout
        layout.addWidget(tmpl_label, 0, 0)
        layout.addLayout(tmpl_btn_row, 0, 1, 1, 3)
        layout.addWidget(wf_label, 1, 0)
        layout.addWidget(self.workflow_input, 1, 1, 1, 2)
        layout.addWidget(self.wf_btn, 1, 3)
        layout.addWidget(excl_label, 2, 0)
        layout.addWidget(self.exclude_tmpl_input, 2, 1, 1, 3)
        layout.addWidget(self.auto_scan_check, 3, 1)
        layout.addWidget(self.new_templates_check, 3, 2)
        layout.setRowStretch(4, 1)
        layout.setColumnStretch(1, 1)

        self.config_tabs.addTab(tab, "Templates")

    def _build_filters_tab(self):
        """Build Filters tab for severity, tags, authors."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Severity selection
        sev_label = QLabel("Severity (select one or more):")
        sev_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: bold;")
        layout.addWidget(sev_label)

        sev_row = QHBoxLayout()
        self.severity_checks = {}
        for sev in ["info", "low", "medium", "high", "critical"]:
            check = QCheckBox(sev.capitalize())
            check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
            check.stateChanged.connect(self.update_command)
            self.severity_checks[sev] = check
            sev_row.addWidget(check)
        sev_row.addStretch()
        layout.addLayout(sev_row)

        # Tags
        grid = QGridLayout()
        grid.setSpacing(10)

        tags_label = QLabel("Tags:")
        tags_label.setStyleSheet(LABEL_STYLE)
        tags_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("cve,rce,xss (comma-separated)")
        self.tags_input.setStyleSheet(self.target_input.styleSheet())
        self.tags_input.textChanged.connect(self.update_command)

        # Exclude tags
        excl_tags_label = QLabel("Exclude Tags:")
        excl_tags_label.setStyleSheet(LABEL_STYLE)
        excl_tags_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.exclude_tags_input = QLineEdit()
        self.exclude_tags_input.setPlaceholderText("dos,fuzz")
        self.exclude_tags_input.setStyleSheet(self.target_input.styleSheet())
        self.exclude_tags_input.textChanged.connect(self.update_command)

        # Authors
        author_label = QLabel("Authors:")
        author_label.setStyleSheet(LABEL_STYLE)
        author_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.authors_input = QLineEdit()
        self.authors_input.setPlaceholderText("pdteam,geeknik")
        self.authors_input.setStyleSheet(self.target_input.styleSheet())
        self.authors_input.textChanged.connect(self.update_command)

        # Template condition
        tc_label = QLabel("Condition:")
        tc_label.setStyleSheet(LABEL_STYLE)
        tc_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.template_condition_input = QLineEdit()
        self.template_condition_input.setPlaceholderText("contains(id,'xss')")
        self.template_condition_input.setStyleSheet(self.target_input.styleSheet())
        self.template_condition_input.textChanged.connect(self.update_command)

        grid.addWidget(tags_label, 0, 0)
        grid.addWidget(self.tags_input, 0, 1)
        grid.addWidget(excl_tags_label, 0, 2)
        grid.addWidget(self.exclude_tags_input, 0, 3)
        grid.addWidget(author_label, 1, 0)
        grid.addWidget(self.authors_input, 1, 1)
        grid.addWidget(tc_label, 1, 2)
        grid.addWidget(self.template_condition_input, 1, 3)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        layout.addLayout(grid)
        layout.addStretch()

        self.config_tabs.addTab(tab, "Filters")

    def _build_rate_tab(self):
        """Build Rate Limiting tab."""
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Concurrency
        conc_label = QLabel("Concurrency:")
        conc_label.setStyleSheet(LABEL_STYLE)
        conc_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.concurrency_spin = StyledSpinBox()
        self.concurrency_spin.setRange(1, 500)
        self.concurrency_spin.setValue(25)
        self.concurrency_spin.valueChanged.connect(self.update_command)

        # Rate limit
        rate_label = QLabel("Rate Limit:")
        rate_label.setStyleSheet(LABEL_STYLE)
        rate_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.rate_limit_spin = StyledSpinBox()
        self.rate_limit_spin.setRange(0, 10000)
        self.rate_limit_spin.setValue(150)
        self.rate_limit_spin.setSuffix(" req/s")
        self.rate_limit_spin.valueChanged.connect(self.update_command)

        # Bulk size
        bulk_label = QLabel("Bulk Size:")
        bulk_label.setStyleSheet(LABEL_STYLE)
        bulk_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.bulk_size_spin = StyledSpinBox()
        self.bulk_size_spin.setRange(1, 500)
        self.bulk_size_spin.setValue(25)
        self.bulk_size_spin.valueChanged.connect(self.update_command)

        # Retries
        retry_label = QLabel("Retries:")
        retry_label.setStyleSheet(LABEL_STYLE)
        retry_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.retries_spin = StyledSpinBox()
        self.retries_spin.setRange(0, 10)
        self.retries_spin.setValue(1)
        self.retries_spin.valueChanged.connect(self.update_command)

        # Timeout
        timeout_label = QLabel("Timeout:")
        timeout_label.setStyleSheet(LABEL_STYLE)
        timeout_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.timeout_spin = StyledSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(10)
        self.timeout_spin.setSuffix(" s")
        self.timeout_spin.valueChanged.connect(self.update_command)

        layout.addWidget(conc_label, 0, 0)
        layout.addWidget(self.concurrency_spin, 0, 1)
        layout.addWidget(rate_label, 0, 2)
        layout.addWidget(self.rate_limit_spin, 0, 3)
        layout.addWidget(bulk_label, 1, 0)
        layout.addWidget(self.bulk_size_spin, 1, 1)
        layout.addWidget(retry_label, 1, 2)
        layout.addWidget(self.retries_spin, 1, 3)
        layout.addWidget(timeout_label, 2, 0)
        layout.addWidget(self.timeout_spin, 2, 1)
        layout.setRowStretch(3, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        self.config_tabs.addTab(tab, "Rate Limit")

    def _build_network_tab(self):
        """Build Network tab for proxy, headers."""
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Proxy
        proxy_label = QLabel("Proxy:")
        proxy_label.setStyleSheet(LABEL_STYLE)
        proxy_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("http://127.0.0.1:8080 or socks5://...")
        self.proxy_input.setStyleSheet(self.target_input.styleSheet())
        self.proxy_input.textChanged.connect(self.update_command)

        # Headers
        header_label = QLabel("Headers:")
        header_label.setStyleSheet(LABEL_STYLE)
        header_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.headers_input = QLineEdit()
        self.headers_input.setPlaceholderText("Authorization: Bearer token")
        self.headers_input.setStyleSheet(self.target_input.styleSheet())
        self.headers_input.textChanged.connect(self.update_command)

        # Input mode
        mode_label = QLabel("Input Mode:")
        mode_label.setStyleSheet(LABEL_STYLE)
        mode_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.input_mode_combo = QComboBox()
        self.input_mode_combo.addItems(["list", "burp", "jsonl", "yaml", "openapi", "swagger"])
        self.input_mode_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 6px;
            }}
        """)
        self.input_mode_combo.currentTextChanged.connect(self.update_command)

        # System resolver
        self.system_resolvers_check = QCheckBox("System DNS Resolvers")
        self.system_resolvers_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
        self.system_resolvers_check.stateChanged.connect(self.update_command)

        layout.addWidget(proxy_label, 0, 0)
        layout.addWidget(self.proxy_input, 0, 1, 1, 3)
        layout.addWidget(header_label, 1, 0)
        layout.addWidget(self.headers_input, 1, 1, 1, 3)
        layout.addWidget(mode_label, 2, 0)
        layout.addWidget(self.input_mode_combo, 2, 1)
        layout.addWidget(self.system_resolvers_check, 2, 2, 1, 2)
        layout.setRowStretch(3, 1)
        layout.setColumnStretch(1, 1)

        self.config_tabs.addTab(tab, "Network")

    def _build_output_tab(self):
        """Build Output tab."""
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Output file
        out_label = QLabel("Output File:")
        out_label.setStyleSheet(LABEL_STYLE)
        out_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.output_file_input = QLineEdit()
        self.output_file_input.setPlaceholderText("Custom output path (auto-generated if empty)")
        self.output_file_input.setStyleSheet(self.target_input.styleSheet())
        self.output_file_input.textChanged.connect(self.update_command)

        # JSON output - enabled by default
        self.json_output_check = QCheckBox("JSON Output")
        self.json_output_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
        self.json_output_check.setChecked(True)
        self.json_output_check.stateChanged.connect(self.update_command)

        self.jsonl_output_check = QCheckBox("JSONL Output")
        self.jsonl_output_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
        self.jsonl_output_check.stateChanged.connect(self.update_command)

        self.markdown_output_check = QCheckBox("Markdown Export")
        self.markdown_output_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
        self.markdown_output_check.stateChanged.connect(self.update_command)

        # Display options
        self.verbose_check = QCheckBox("Verbose")
        self.verbose_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
        self.verbose_check.stateChanged.connect(self.update_command)

        self.debug_check = QCheckBox("Debug")
        self.debug_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
        self.debug_check.stateChanged.connect(self.update_command)

        self.silent_check = QCheckBox("Silent")
        self.silent_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
        self.silent_check.stateChanged.connect(self.update_command)

        self.no_color_check = QCheckBox("No Color")
        self.no_color_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
        self.no_color_check.stateChanged.connect(self.update_command)

        layout.addWidget(out_label, 0, 0)
        layout.addWidget(self.output_file_input, 0, 1, 1, 3)
        layout.addWidget(self.json_output_check, 1, 0)
        layout.addWidget(self.jsonl_output_check, 1, 1)
        layout.addWidget(self.markdown_output_check, 1, 2)
        layout.addWidget(self.verbose_check, 2, 0)
        layout.addWidget(self.debug_check, 2, 1)
        layout.addWidget(self.silent_check, 2, 2)
        layout.addWidget(self.no_color_check, 2, 3)
        layout.setRowStretch(3, 1)
        layout.setColumnStretch(1, 1)

        self.config_tabs.addTab(tab, "Output")

    def _build_advanced_tab(self):
        """Build Advanced tab."""
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Config file
        cfg_label = QLabel("Config File:")
        cfg_label.setStyleSheet(LABEL_STYLE)
        cfg_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.config_file_input = QLineEdit()
        self.config_file_input.setPlaceholderText("Custom config YAML file")
        self.config_file_input.setStyleSheet(self.target_input.styleSheet())
        self.config_file_input.textChanged.connect(self.update_command)

        self.cfg_btn = QPushButton("📄")
        self.cfg_btn.setStyleSheet(self.tmpl_file_btn.styleSheet())
        self.cfg_btn.clicked.connect(self._browse_config)
        self.cfg_btn.setCursor(Qt.PointingHandCursor)

        # Interactsh server
        interact_label = QLabel("Interactsh:")
        interact_label.setStyleSheet(LABEL_STYLE)
        interact_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.interactsh_input = QLineEdit()
        self.interactsh_input.setPlaceholderText("Custom Interactsh server URL")
        self.interactsh_input.setStyleSheet(self.target_input.styleSheet())
        self.interactsh_input.textChanged.connect(self.update_command)

        # Checkboxes
        self.headless_check = QCheckBox("Headless Browser")
        self.headless_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
        self.headless_check.stateChanged.connect(self.update_command)

        self.update_templates_check = QCheckBox("Update Templates")
        self.update_templates_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
        self.update_templates_check.stateChanged.connect(self.update_command)

        self.validate_check = QCheckBox("Validate Templates")
        self.validate_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
        self.validate_check.stateChanged.connect(self.update_command)

        self.stop_at_first_check = QCheckBox("Stop at First Match")
        self.stop_at_first_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
        self.stop_at_first_check.stateChanged.connect(self.update_command)

        self.no_interactsh_check = QCheckBox("Disable Interactsh")
        self.no_interactsh_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
        self.no_interactsh_check.stateChanged.connect(self.update_command)

        layout.addWidget(cfg_label, 0, 0)
        layout.addWidget(self.config_file_input, 0, 1, 1, 2)
        layout.addWidget(self.cfg_btn, 0, 3)
        layout.addWidget(interact_label, 1, 0)
        layout.addWidget(self.interactsh_input, 1, 1, 1, 3)
        layout.addWidget(self.headless_check, 2, 0)
        layout.addWidget(self.update_templates_check, 2, 1)
        layout.addWidget(self.validate_check, 2, 2)
        layout.addWidget(self.stop_at_first_check, 3, 0)
        layout.addWidget(self.no_interactsh_check, 3, 1)
        layout.setRowStretch(4, 1)
        layout.setColumnStretch(1, 1)

        self.config_tabs.addTab(tab, "Advanced")

    # ==================== FILE BROWSERS ====================

    def _browse_target_list(self):
        """Browse for target list file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Target List", "",
            "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.target_input.setText(file_path)

    def _browse_template_file(self):
        """Browse for template file(s)."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Template Files", "",
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if files:
            self.template_input.setText(",".join(files))

    def _browse_template_folder(self):
        """Browse for template folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Template Folder"
        )
        if folder:
            self.template_input.setText(folder)

    def _browse_workflow(self):
        """Browse for workflow file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Workflow File", "",
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if file_path:
            self.workflow_input.setText(file_path)

    def _browse_config(self):
        """Browse for config file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Config File", "",
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if file_path:
            self.config_file_input.setText(file_path)

    # ==================== COMMAND BUILDER ====================

    def eventFilter(self, obj, event):
        """Handle events to position floating buttons."""
        from PySide6.QtCore import QEvent
        if obj == self.output and event.type() == QEvent.Resize:
            self.copy_button.move(
                self.output.width() - self.copy_button.sizeHint().width() - 10,
                10
            )
        return super().eventFilter(obj, event)

    def update_command(self):
        """Generate Nuclei command based on UI inputs."""
        target = self.target_input.text().strip()
        if not target:
            target = "<target>"

        cmd_parts = ["nuclei"]

        # Target - check if file or single target
        if os.path.isfile(target):
            cmd_parts.extend(["-l", target])
        else:
            cmd_parts.extend(["-u", target])

        # Templates
        tmpl = self.template_input.text().strip()
        if tmpl:
            cmd_parts.extend(["-t", tmpl])

        # Workflow
        wf = self.workflow_input.text().strip()
        if wf:
            cmd_parts.extend(["-w", wf])

        # Exclude templates
        excl = self.exclude_tmpl_input.text().strip()
        if excl:
            cmd_parts.extend(["-exclude-templates", excl])

        # Auto-scan
        if self.auto_scan_check.isChecked():
            cmd_parts.append("-as")

        # New templates
        if self.new_templates_check.isChecked():
            cmd_parts.append("-nt")

        # Severity
        severities = [s for s, c in self.severity_checks.items() if c.isChecked()]
        if severities:
            cmd_parts.extend(["-severity", ",".join(severities)])

        # Tags
        tags = self.tags_input.text().strip()
        if tags:
            cmd_parts.extend(["-tags", tags])

        # Exclude tags
        excl_tags = self.exclude_tags_input.text().strip()
        if excl_tags:
            cmd_parts.extend(["-exclude-tags", excl_tags])

        # Authors
        authors = self.authors_input.text().strip()
        if authors:
            cmd_parts.extend(["-author", authors])

        # Template condition
        tc = self.template_condition_input.text().strip()
        if tc:
            cmd_parts.extend(["-tc", f'"{tc}"'])

        # Rate limiting
        if self.concurrency_spin.value() != 25:
            cmd_parts.extend(["-c", str(self.concurrency_spin.value())])

        if self.rate_limit_spin.value() != 150:
            cmd_parts.extend(["-rl", str(self.rate_limit_spin.value())])

        if self.bulk_size_spin.value() != 25:
            cmd_parts.extend(["-bs", str(self.bulk_size_spin.value())])

        if self.retries_spin.value() != 1:
            cmd_parts.extend(["-retries", str(self.retries_spin.value())])

        if self.timeout_spin.value() != 10:
            cmd_parts.extend(["-timeout", str(self.timeout_spin.value())])

        # Network
        proxy = self.proxy_input.text().strip()
        if proxy:
            cmd_parts.extend(["-proxy", proxy])

        headers = self.headers_input.text().strip()
        if headers:
            cmd_parts.extend(["-H", f'"{headers}"'])

        if self.input_mode_combo.currentText() != "list":
            cmd_parts.extend(["-im", self.input_mode_combo.currentText()])

        if self.system_resolvers_check.isChecked():
            cmd_parts.append("-system-resolvers")

        # Output
        if self.json_output_check.isChecked():
            cmd_parts.append("-json")

        if self.jsonl_output_check.isChecked():
            cmd_parts.append("-jsonl")

        if self.markdown_output_check.isChecked():
            cmd_parts.append("-me")

        if self.verbose_check.isChecked():
            cmd_parts.append("-v")

        if self.debug_check.isChecked():
            cmd_parts.append("-debug")

        if self.silent_check.isChecked():
            cmd_parts.append("-silent")

        if self.no_color_check.isChecked():
            cmd_parts.append("-nc")

        # Advanced
        cfg = self.config_file_input.text().strip()
        if cfg:
            cmd_parts.extend(["-config", cfg])

        interact = self.interactsh_input.text().strip()
        if interact:
            cmd_parts.extend(["-iserver", interact])

        if self.headless_check.isChecked():
            cmd_parts.append("-headless")

        if self.update_templates_check.isChecked():
            cmd_parts.append("-update-templates")

        if self.validate_check.isChecked():
            cmd_parts.append("-validate")

        if self.stop_at_first_check.isChecked():
            cmd_parts.append("-stop-at-first-match")

        if self.no_interactsh_check.isChecked():
            cmd_parts.append("-no-interactsh")

        self.command_input.setText(" ".join(cmd_parts))

    # ==================== SCAN EXECUTION ====================

    def run_scan(self):
        """Execute Nuclei scan."""
        target = self.target_input.text().strip()
        if not target:
            self._notify("Please enter a target URL or select a target list file")
            return

        self.output.clear()
        self._info(f"Starting Nuclei scan on: {target}")
        self._section("NUCLEI SCAN OUTPUT")

        # Extract target name
        try:
            temp = target
            if os.path.isfile(temp):
                target_name = os.path.splitext(os.path.basename(temp))[0]
            else:
                if "://" in temp:
                    temp = temp.split("://", 1)[1]
                target_name = temp.split("/")[0].split(":")[0]
        except:
            target_name = "target"

        self.base_dir = create_target_dirs(target_name, None)
        output_file = os.path.join(self.base_dir, "Logs", "nuclei.txt")

        # Build command
        cmd_text = self.command_input.text()
        command = cmd_text.split()

        # Add output file if not already specified
        custom_out = self.output_file_input.text().strip()
        if custom_out:
            command.extend(["-o", custom_out])
        else:
            command.extend(["-o", output_file])

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

        if self.base_dir:
            output_file = os.path.join(self.base_dir, "Logs", "nuclei.txt")
            self._info(f"Results saved to: {output_file}")

        self.worker = None
        if self.main_window:
            self.main_window.active_process = None
        self._info("Scan completed")
        self._notify("Nuclei scan completed.")

    def _on_output(self, line):
        """Handle real-time output with severity-based coloring."""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        line = ansi_escape.sub('', line)

        if not line.strip():
            return

        line_lower = line.lower()

        # Critical (RED) - critical severity findings
        if "[critical]" in line_lower or "critical" in line_lower:
            self.output.append(f'<span style="color:#F87171;font-weight:bold;">{line}</span>')

        # High (ORANGE)
        elif "[high]" in line_lower:
            self.output.append(f'<span style="color:#FB923C;">{line}</span>')

        # Medium (YELLOW)
        elif "[medium]" in line_lower:
            self.output.append(f'<span style="color:#FACC15;">{line}</span>')

        # Low (GREEN)
        elif "[low]" in line_lower:
            self.output.append(f'<span style="color:#10B981;">{line}</span>')

        # Info (BLUE)
        elif "[info]" in line_lower or "inf]" in line_lower:
            self.output.append(f'<span style="color:#60A5FA;">{line}</span>')

        # Error messages
        elif "error" in line_lower or "failed" in line_lower:
            self.output.append(f'<span style="color:#F87171;">{line}</span>')

        # Default
        else:
            self.output.append(line)

    # ==================== HELPERS ====================

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
