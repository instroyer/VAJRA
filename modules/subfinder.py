# =============================================================================
# modules/subfinder.py
#
# Subfinder - Subdomain Discovery Tool
# =============================================================================

import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from core.tgtinput import parse_targets
from core.fileops import create_target_dirs, get_group_name_from_file
from ui.worker import ProcessWorker
from ui.styles import (
    # Widgets
    RunButton, StopButton, BrowseButton,
    StyledLineEdit, StyledSpinBox, StyledCheckBox,
    StyledLabel, HeaderLabel, CommandDisplay, OutputView,
    StyledGroupBox, ToolSplitter, CopyButton,
    # Behaviors
    SafeStop, OutputHelper,
    # Constants
    TOOL_VIEW_STYLE, COLOR_BACKGROUND_SECONDARY
)
from core.tgtinput import TargetInput


class SubfinderView(QWidget, SafeStop, OutputHelper):
    """Subfinder subdomain discovery tool interface."""
    
    tool_name = "Subfinder"
    tool_category = "SUBDOMAIN_ENUMERATION"
    
    def __init__(self, name, category, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_safe_stop()
        
        # State
        self.targets_queue = []
        self.group_name = None
        self.log_file = None
        
        # Build UI
        self._build_ui()
        self.update_command()
    
    def _build_ui(self):
        """Build the complete UI."""
        self.setStyleSheet(TOOL_VIEW_STYLE)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Splitter for control/output
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
        
        # ==================== CONFIGURATION GROUP ====================
        config_group = StyledGroupBox("⚙️ Advanced Configuration")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(10)
        
        # Row 1: Threads & Config
        row1 = QHBoxLayout()
        
        # Threads
        threads_label = StyledLabel("Threads:")
        self.threads_spin = StyledSpinBox()
        self.threads_spin.setRange(1, 200)
        self.threads_spin.setValue(10)
        self.threads_spin.setToolTip("Number of concurrent threads")
        self.threads_spin.valueChanged.connect(self.update_command)
        
        row1.addWidget(threads_label)
        row1.addWidget(self.threads_spin)
        row1.addSpacing(20)
        
        # Config File
        config_label = StyledLabel("Config:")
        self.config_input = StyledLineEdit("Path to config file...")
        self.config_input.textChanged.connect(self.update_command)
        
        config_browse = BrowseButton()
        config_browse.clicked.connect(self._browse_config)
        
        row1.addWidget(config_label)
        row1.addWidget(self.config_input)
        row1.addWidget(config_browse)
        
        config_layout.addLayout(row1)
        
        # Row 2: Checkboxes
        row2 = QHBoxLayout()
        
        self.recursive_check = StyledCheckBox("Recursive (-recursive)")
        self.recursive_check.setToolTip("Use only sources that can handle subdomains recursively")
        self.recursive_check.stateChanged.connect(self.update_command)
        
        self.all_sources_check = StyledCheckBox("All Sources (-all)")
        self.all_sources_check.setToolTip("Use all available sources for enumeration")
        self.all_sources_check.stateChanged.connect(self.update_command)
        
        row2.addWidget(self.recursive_check)
        row2.addSpacing(20)
        row2.addWidget(self.all_sources_check)
        row2.addStretch()
        
        config_layout.addLayout(row2)
        control_layout.addWidget(config_group)
        
        # Command Display
        self.command_input = CommandDisplay()
        control_layout.addWidget(self.command_input)
        
        control_layout.addStretch()
        splitter.addWidget(control_panel)
        
        # ==================== OUTPUT AREA ====================
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("Subfinder results will appear here...")
        
        # Copy button
        self.copy_button = CopyButton(self.output.output_text, self.main_window)
        self.copy_button.setParent(self.output.output_text)
        self.copy_button.raise_()
        self.output.output_text.installEventFilter(self)
        
        splitter.addWidget(self.output)
        splitter.setSizes([300, 400])
        
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
    
    def _browse_config(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Config File", "", 
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if file_path:
            self.config_input.setText(file_path)
    
    def update_command(self):
        target = self.target_input.get_target().strip()
        if not target:
            target = "<target>"
        
        cmd_parts = ["subfinder", "-d", target]
        
        if self.threads_spin.value() > 10:
            cmd_parts.extend(["-t", str(self.threads_spin.value())])
        
        if self.recursive_check.isChecked():
            cmd_parts.append("-recursive")
        
        if self.all_sources_check.isChecked():
            cmd_parts.append("-all")
        
        if self.config_input.text().strip():
            cmd_parts.extend(["-config", self.config_input.text().strip()])
        
        self.command_input.setText(" ".join(cmd_parts))
    
    def run_scan(self):
        raw_input = self.target_input.get_target()
        if not raw_input:
            self._notify("Please enter a target domain.")
            return
        
        targets, source = parse_targets(raw_input)
        if not targets:
            self._notify("No valid targets found.")
            return
        
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.output.clear()
        
        self.targets_queue = list(targets)
        self.group_name = get_group_name_from_file(raw_input) if source == "file" else None
        self._process_next_target()
    
    def _process_next_target(self):
        if not self.targets_queue:
            self._on_scan_completed()
            self._notify("Subfinder scan finished.")
            return
        
        target = self.targets_queue.pop(0)
        self._info(f"Running command: {self.command_input.text()}")
        self._section(f"SUBFINDER: {target}")
        
        base_dir = create_target_dirs(target, self.group_name)
        self.log_file = os.path.join(base_dir, "Subdomains", "subfinder.txt")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        command = self.command_input.text().split() + ["-o", self.log_file]
        
        self.worker = ProcessWorker(command)
        self.worker.output_ready.connect(self._on_output)
        self.worker.finished.connect(self._on_process_finished)
        self.worker.error.connect(self._on_process_error)
        self.worker.start()
        
        if self.main_window:
            self.main_window.active_process = self.worker
    
    def _on_output(self, line):
        self.output.appendPlainText(line)
    
    def _on_process_finished(self):
        self.output.appendPlainText("\n")
        
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    self.output.appendPlainText(f.read())
            except IOError as e:
                self._error(f"Could not read log file: {e}")
        
        if self.targets_queue:
            self._process_next_target()
        else:
            self._on_scan_completed()
            self._notify("Subfinder scan finished.")
    
    def _on_process_error(self, error):
        self._error(f"Process error: {error}")
        self._on_scan_completed()
    
    def _on_scan_completed(self):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.worker = None
        if self.main_window:
            self.main_window.active_process = None


class SubfinderTool(ToolBase):
    """Subfinder tool plugin."""
    
    @property
    def name(self) -> str:
        return "Subfinder"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SUBDOMAIN_ENUMERATION
    
    def get_widget(self, main_window):
        return SubfinderView(self.name, self.category, main_window=main_window)
