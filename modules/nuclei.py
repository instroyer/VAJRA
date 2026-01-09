# =============================================================================
# modules/nuclei.py
#
# Professional Nuclei Vulnerability Scanner GUI
# Comprehensive template-based vulnerability scanning with all advanced options
# =============================================================================

import os
import shlex
import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog, QMessageBox
)

from modules.bases import ToolBase, ToolCategory
from ui.worker import ToolExecutionMixin
from ui.styles import (
    # Widgets
    RunButton, StopButton, BrowseButton,
    StyledLineEdit, StyledSpinBox, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView,
    ToolSplitter, ConfigTabs, StyledToolView
)


class NucleiTool(ToolBase):
    """Professional Nuclei vulnerability scanner tool."""

    name = "Nuclei"
    category = ToolCategory.VULNERABILITY_SCANNER

    @property
    def icon(self) -> str:
        return "⚛️"

    def get_widget(self, main_window):
        return NucleiToolView(main_window=main_window)


class NucleiToolView(StyledToolView, ToolExecutionMixin):
    """Nuclei vulnerability scanner interface."""
    
    tool_name = "Nuclei"
    tool_category = "VULNERABILITY_SCANNER"

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.output_file = None
        self._build_ui()
        self.update_command()

    def _build_ui(self):
        """Build UI."""
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
        
        # Target
        target_group = StyledGroupBox("🎯 Target")
        target_layout = QHBoxLayout(target_group)
        
        self.target_input = StyledLineEdit()
        self.target_input.setPlaceholderText("http://example.com or list.txt")
        self.target_input.textChanged.connect(self.update_command)
        
        browse_btn = BrowseButton()
        browse_btn.clicked.connect(self._browse_target)
        
        target_layout.addWidget(self.target_input)
        target_layout.addWidget(browse_btn)
        
        control_layout.addWidget(target_group)
        
        # Configuration
        self.config_tabs = ConfigTabs()
        
        # Tab 1: Templates
        t_tab = QWidget()
        t_layout = QGridLayout(t_tab)
        
        self.template_input = StyledLineEdit()
        self.template_input.setPlaceholderText("Template path/folder or file(s) - comma separated (optional)")
        self.template_input.textChanged.connect(self.update_command)
        
        t_browse = BrowseButton()
        t_browse.clicked.connect(self._browse_template)
        
        self.auto_scan_check = StyledCheckBox("Auto-Scan (-as)")
        self.auto_scan_check.stateChanged.connect(self.update_command)
        
        self.new_tmpl_check = StyledCheckBox("New Templates (-nt)")
        self.new_tmpl_check.stateChanged.connect(self.update_command)
        
        t_layout.addWidget(StyledLabel("Templates:\n(Directory or Files)"), 0, 0)
        t_layout.addWidget(self.template_input, 0, 1)
        t_layout.addWidget(t_browse, 0, 2)
        t_layout.addWidget(self.auto_scan_check, 1, 0, 1, 2)
        t_layout.addWidget(self.new_tmpl_check, 1, 2)
        
        self.config_tabs.addTab(t_tab, "Templates")
        
        # Tab 2: Filters
        f_tab = QWidget()
        f_layout = QVBoxLayout(f_tab)
        
        sev_layout = QHBoxLayout()
        self.sev_checks = {}
        for sev in ["info", "low", "medium", "high", "critical"]:
            c = StyledCheckBox(sev.title())
            c.stateChanged.connect(self.update_command)
            self.sev_checks[sev] = c
            sev_layout.addWidget(c)
        f_layout.addLayout(sev_layout)
        
        tags_layout = QGridLayout()
        self.tags_input = StyledLineEdit()
        self.tags_input.setPlaceholderText("cve,rce,xss")
        self.tags_input.textChanged.connect(self.update_command)
        
        self.exclude_tags = StyledLineEdit()
        self.exclude_tags.setPlaceholderText("dos,fuzz")
        self.exclude_tags.textChanged.connect(self.update_command)
        
        tags_layout.addWidget(StyledLabel("Tags:"), 0, 0)
        tags_layout.addWidget(self.tags_input, 0, 1)
        tags_layout.addWidget(StyledLabel("Exclude Tags:"), 1, 0)
        tags_layout.addWidget(self.exclude_tags, 1, 1)
        
        f_layout.addLayout(tags_layout)
        self.config_tabs.addTab(f_tab, "Filters")
        
        # Tab 3: Performance
        p_tab = QWidget()
        p_layout = QGridLayout(p_tab)
        
        self.concurrency = StyledSpinBox()
        self.concurrency.setRange(1, 1000)
        self.concurrency.setValue(25)
        self.concurrency.valueChanged.connect(self.update_command)
        
        self.rate_limit = StyledSpinBox()
        self.rate_limit.setRange(1, 10000)
        self.rate_limit.setValue(150)
        self.rate_limit.valueChanged.connect(self.update_command)
        
        self.timeout = StyledSpinBox()
        self.timeout.setRange(1, 300)
        self.timeout.setValue(10)
        self.timeout.valueChanged.connect(self.update_command)
        
        p_layout.addWidget(StyledLabel("Concurrency (-c):"), 0, 0)
        p_layout.addWidget(self.concurrency, 0, 1)
        p_layout.addWidget(StyledLabel("Rate Limit (-rl):"), 1, 0)
        p_layout.addWidget(self.rate_limit, 1, 1)
        p_layout.addWidget(StyledLabel("Timeout (-to):"), 2, 0)
        p_layout.addWidget(self.timeout, 2, 1)
        
        self.config_tabs.addTab(p_tab, "Performance")
        
        # Tab 4: Advanced
        a_tab = QWidget()
        a_layout = QGridLayout(a_tab)
        
        self.proxy_input = StyledLineEdit()
        self.proxy_input.setPlaceholderText("http://127.0.0.1:8080")
        self.proxy_input.textChanged.connect(self.update_command)
        
        self.headless_check = StyledCheckBox("Headless")
        self.headless_check.stateChanged.connect(self.update_command)
        
        self.verbose_check = StyledCheckBox("Verbose")
        self.verbose_check.stateChanged.connect(self.update_command)
        
        a_layout.addWidget(StyledLabel("Proxy:"), 0, 0)
        a_layout.addWidget(self.proxy_input, 0, 1)
        a_layout.addWidget(self.headless_check, 1, 0)
        a_layout.addWidget(self.verbose_check, 1, 1)
        
        self.config_tabs.addTab(a_tab, "Advanced")
        
        control_layout.addWidget(self.config_tabs)
        
        # Command Preview
        self.command_input = StyledLineEdit()
        self.command_input.setReadOnly(True)
        self.command_input.setPlaceholderText("Command preview...")
        control_layout.addWidget(self.command_input)

        # Buttons
        btn_layout = QHBoxLayout()
        self.run_button = RunButton("RUN NUCLEI")
        self.run_button.clicked.connect(self.run_scan)
        self.stop_button = StopButton()
        self.stop_button.clicked.connect(self.stop_scan)
        
        btn_layout.addWidget(self.run_button)
        btn_layout.addWidget(self.stop_button)
        control_layout.addLayout(btn_layout)

        control_layout.addStretch()
        splitter.addWidget(control_panel)

        # Output
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("Nuclei results will appear here...")
        
        splitter.addWidget(self.output)
        splitter.setSizes([450, 450])
        
        main_layout.addWidget(splitter)
        
    def _browse_target(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Target List")
        if f: self.target_input.setText(f)

    def _browse_template(self):
        """Browse for template files or directories with user choice."""
        # Create a message box to let user choose between file and directory selection
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Select Template Type")
        msg_box.setText("What would you like to select?")
        msg_box.setIcon(QMessageBox.Question)

        # Add buttons for different selection types
        dir_button = msg_box.addButton("📁 Directory", QMessageBox.AcceptRole)
        file_button = msg_box.addButton("📄 Template File(s)", QMessageBox.AcceptRole)
        cancel_button = msg_box.addButton("Cancel", QMessageBox.RejectRole)

        msg_box.setDefaultButton(dir_button)
        msg_box.exec()

        clicked_button = msg_box.clickedButton()

        if clicked_button == dir_button:
            # Select directory
            directory = QFileDialog.getExistingDirectory(
                self,
                "Select Template Directory",
                "",
                QFileDialog.ShowDirsOnly
            )
            if directory:
                self.template_input.setText(directory)

        elif clicked_button == file_button:
            # Select one or more template files
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Template File(s)",
                "",
                "YAML files (*.yaml *.yml);;All files (*)"
            )
            if files:
                # Join multiple files with commas (nuclei supports this)
                self.template_input.setText(",".join(files))
        
    # -------------------------------------------------------------------------
    # Command Builder
    # -------------------------------------------------------------------------

    def build_command(self, preview: bool = False) -> str:
        cmd = ["nuclei"]
        
        target = self.target_input.text().strip()
        if target:
            if os.path.isfile(target):
                cmd.extend(["-l", target])
            else:
                cmd.extend(["-u", target])
        elif preview:
             cmd.extend(["-u", "<target>"])
        else:
             raise ValueError("Target required")
        
        # Templates
        tmpl = self.template_input.text().strip()
        if tmpl:
            cmd.extend(["-t", tmpl])
            
        if self.auto_scan_check.isChecked(): cmd.append("-as")
        if self.new_tmpl_check.isChecked(): cmd.append("-nt")
        
        # Filters
        sevs = [s for s, c in self.sev_checks.items() if c.isChecked()]
        if sevs:
            cmd.extend(["-s", ",".join(sevs)])
            
        tags = self.tags_input.text().strip()
        if tags:
            cmd.extend(["-tags", tags])
            
        ex_tags = self.exclude_tags.text().strip()
        if ex_tags:
            cmd.extend(["-etags", ex_tags])
            
        # Perf
        if self.concurrency.value() != 25:
            cmd.extend(["-c", str(self.concurrency.value())])
        if self.rate_limit.value() != 150:
            cmd.extend(["-rl", str(self.rate_limit.value())])
        if self.timeout.value() != 10:
            cmd.extend(["-to", str(self.timeout.value())])
            
        # Advanced
        proxy = self.proxy_input.text().strip()
        if proxy:
            cmd.extend(["-proxy", proxy])
            
        if self.headless_check.isChecked(): cmd.append("-headless")
        if self.verbose_check.isChecked(): cmd.append("-v")
        
        # Output (Always use json output for processing, or standard if user wants text)
        cmd.append("-nc") # No color
        
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
        try:
            # Prepare output directory
            target = self.target_input.text().strip()
            if not target:
                raise ValueError("Target required")
                
            from core.fileops import create_target_dirs
            
            # Create standard directory structure
            base_dir = create_target_dirs(target)
            
            # Define output file
            # Nuclei output is text by default with our -nc flag, or we could use .json if we switched to -json
            # For now keeping it simple with txt as per existing logic
            self.output_file = os.path.join(base_dir, "Logs", "nuclei_results.txt")
            
            cmd_str = self.build_command(preview=False)
            
            # Append output file arg
            cmd_str += f" -o {shlex.quote(self.output_file)}"
            
            self._info(f"Starting Nuclei Scan...")
            self._info(f"Results will be saved to: {self.output_file}")
            
            self._section("NUCLEI SCAN")
            self._section("Command")
            self._raw(html.escape(cmd_str))
            
            # Disable buffering for real-time results
            self.start_execution(cmd_str, output_path=self.output_file, buffer_output=False)
            
        except Exception as e:
            self._error(str(e))

    def on_execution_finished(self):
        super().on_execution_finished()
        self._section("Scan Completed")

    def on_new_output(self, line):
        clean = line.rstrip() # rstrip to preserve indentation
        
        clean = self.strip_ansi(clean)
        safe_line = html.escape(clean)
        
        # Terminal look
        base = "white-space: pre-wrap; font-family: monospace; display: block;"
        
        if not safe_line:
            self._raw("<br>")
            return
        
        # Colorize
        if "[info]" in clean:
            self._raw(f'<span style="{base} color:#60A5FA;">{safe_line}</span>') # Blue-400
        elif "[low]" in clean:
            self._raw(f'<span style="{base} color:#93C5FD; font-weight:bold;">{safe_line}</span>') # Blue-300
        elif "[medium]" in clean:
            self._raw(f'<span style="{base} color:#FACC15; font-weight:bold;">{safe_line}</span>') # Yellow-400
        elif "[high]" in clean:
            self._raw(f'<span style="{base} color:#F97316; font-weight:bold;">{safe_line}</span>') # Orange-500
        elif "[critical]" in clean:
            self._raw(f'<span style="{base} color:#EF4444; font-weight:bold;">{safe_line}</span>') # Red-500
        elif "[INF]" in clean:
            self._raw(f'<span style="{base} color:#34D399;">{safe_line}</span>') # Green-400
        elif "[WRN]" in clean:
            self._raw(f'<span style="{base} color:#FBBF24;">{safe_line}</span>') # Amber-400
        elif "[ERR]" in clean:
            self._raw(f'<span style="{base} color:#F87171;">{safe_line}</span>') # Red-400
        else:
            self._raw(f'<span style="{base}">{safe_line}</span>')
