# =============================================================================
# modules/httpx.py
#
# Httpx - Fast HTTP Toolkit
# =============================================================================

import os
import shlex
import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog
)

from modules.bases import ToolBase, ToolCategory
from core.tgtinput import TargetInput
from core.fileops import create_target_dirs
from ui.worker import ToolExecutionMixin
from ui.styles import (
    # Widgets
    RunButton, StopButton, BrowseButton,
    StyledLineEdit, StyledSpinBox, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView,
    ToolSplitter, ConfigTabs, CopyButton, StyledToolView
)


class HttpxTool(ToolBase):
    """Httpx tool plugin."""
    
    name = "Httpx"
    category = ToolCategory.LIVE_SUBDOMAINS
    
    @property
    def icon(self) -> str:
        return "⚡"
    
    def get_widget(self, main_window):
        return HttpxView(main_window=main_window)


class HttpxView(StyledToolView, ToolExecutionMixin):
    """Httpx HTTP probing tool interface."""
    
    tool_name = "Httpx"
    tool_category = "LIVE_SUBDOMAINS"
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.log_file = None
        self._build_ui()
        self.update_command()
    
    def _build_ui(self):
        """Build the complete UI."""
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
        
        # Target Input
        target_group = StyledGroupBox("🎯 Target")
        target_layout = QHBoxLayout(target_group)
        
        self.target_input = TargetInput()
        self.target_input.input_box.textChanged.connect(self.update_command)
        target_layout.addWidget(self.target_input)
        
        control_layout.addWidget(target_group)
        
        # Options
        options_group = StyledGroupBox("⚙️ Options")
        options_layout = QGridLayout(options_group)
        
        self.threads_spin = StyledSpinBox()
        self.threads_spin.setRange(1, 1000)
        self.threads_spin.setValue(50)
        self.threads_spin.valueChanged.connect(self.update_command)
        
        self.title_check = StyledCheckBox("Title (-title)")
        self.title_check.stateChanged.connect(self.update_command)
        
        self.status_check = StyledCheckBox("Status Code (-status-code)")
        self.status_check.stateChanged.connect(self.update_command)
        
        self.tech_check = StyledCheckBox("Tech Detect (-tech-detect)")
        self.tech_check.stateChanged.connect(self.update_command)
        
        self.follow_redirects = StyledCheckBox("Follow Redirects (-follow-redirects)")
        self.follow_redirects.stateChanged.connect(self.update_command)
        
        options_layout.addWidget(StyledLabel("Threads (-threads):"), 0, 0)
        options_layout.addWidget(self.threads_spin, 0, 1)
        options_layout.addWidget(self.title_check, 1, 0)
        options_layout.addWidget(self.status_check, 1, 1)
        options_layout.addWidget(self.tech_check, 2, 0)
        options_layout.addWidget(self.follow_redirects, 2, 1)
        
        control_layout.addWidget(options_group)

        # Command Preview
        self.command_input = StyledLineEdit()
        self.command_input.setReadOnly(True)
        self.command_input.setPlaceholderText("Command preview...")
        control_layout.addWidget(self.command_input)

        # Buttons
        btn_layout = QHBoxLayout()
        self.run_button = RunButton("RUN HTTPX")
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
        self.output.setPlaceholderText("Httpx probing results will appear here...")
        
        splitter.addWidget(self.output)
        splitter.setSizes([400, 450])
        
        main_layout.addWidget(splitter)
        
    # -------------------------------------------------------------------------
    # Command Builder
    # -------------------------------------------------------------------------

    def build_command(self, preview: bool = False, is_file: bool = None) -> str:
        # User specified httpx-toolkit
        cmd = ["httpx-toolkit"]
        
        target = self.target_input.get_target().strip()
        # Use cached is_file if provided, otherwise check
        target_is_file = is_file if is_file is not None else (target and os.path.isfile(target))
        if target_is_file:
            cmd.extend(["-l", target])
        
        # If target is NOT a file, we provide it via stdin, so no argument added here.
             
        if self.threads_spin.value() != 50:
            cmd.extend(["-threads", str(self.threads_spin.value())])
            
        if self.title_check.isChecked(): cmd.append("-title")
        if self.status_check.isChecked(): cmd.append("-status-code")
        if self.tech_check.isChecked(): cmd.append("-tech-detect")
        if self.follow_redirects.isChecked(): cmd.append("-follow-redirects")
        
        cmd.append("-silent") # Less noise in output
        
        # Output file handled in run_scan
        if preview:
            cmd.extend(["-json", "-o", "<output_file>"])
            
        return " ".join(shlex.quote(x) for x in cmd)

    def update_command(self):
        try:
            target = self.target_input.get_target().strip()
            # Cache the file check
            is_file = target and os.path.isfile(target)
            cmd_str = self.build_command(preview=True, is_file=is_file)
            
            # If single target (not file), show it piped
            if target and not is_file:
                cmd_str = f"echo {shlex.quote(target)} | {cmd_str}"
            elif not target:
                cmd_str = f"echo <target> | {cmd_str}"
                
            self.command_input.setText(cmd_str)
        except Exception:
            self.command_input.setText("")

    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------

    def run_scan(self):
        try:
            # Prepare output directory
            target = self.target_input.get_target().strip()
            if not target:
                raise ValueError("Target required")
            
            # Cache file system check
            is_file = os.path.isfile(target)
            
            # Determine directory name
            if is_file:
                base_name = "target_list"
                cmd_prefix = ""
            else:
                temp = target
                if "://" in temp: temp = temp.split("://", 1)[1]
                base_name = temp.split("/")[0].split(":")[0]
                cmd_prefix = f"echo {shlex.quote(target)} | "

            base_dir = create_target_dirs(base_name)
            
            # Ensure tool specific directory exists
            tool_dir = os.path.join(base_dir, "Httpx")
            os.makedirs(tool_dir, exist_ok=True)
            
            self.log_file = os.path.join(tool_dir, "httpx.json")
            
            cmd_str = self.build_command(preview=False, is_file=is_file)
            cmd_str += f" -json -o {shlex.quote(self.log_file)}"
            
            # Construct display string with prefix if needed
            display_cmd = f"{cmd_prefix}{cmd_str}"
            
            self._info(f"Starting Httpx...")
            self._section("HTTPX SCAN")
            self._section("Command")
            self._raw(html.escape(display_cmd))
            self._raw("<br>")
            
            self.start_execution(display_cmd, output_path=self.log_file)
            
        except Exception as e:
            self._error(str(e))

    def on_execution_finished(self):
        super().on_execution_finished()
        self._section("Scan Completed")


    def on_new_output(self, line):
        clean = line.strip()
        if not clean: return
        clean = self.strip_ansi(clean)
        self._raw(html.escape(clean))
