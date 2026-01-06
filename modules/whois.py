# =============================================================================
# modules/whois.py
#
# Whois - Domain Registration Lookup
# =============================================================================

import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from modules.bases import ToolBase, ToolCategory
from core.tgtinput import parse_targets, TargetInput
from core.fileops import create_target_dirs, get_group_name_from_file
from ui.worker import ProcessWorker
from ui.styles import (
    RunButton, StopButton, CopyButton,
    StyledLabel, HeaderLabel, CommandDisplay, OutputView,
    ToolSplitter,
    SafeStop, OutputHelper,
    TOOL_VIEW_STYLE, COLOR_BACKGROUND_SECONDARY
)


class WhoisView(QWidget, SafeStop, OutputHelper):
    """Whois domain lookup tool interface."""
    
    tool_name = "Whois"
    tool_category = "INFO_GATHERING"
    
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
        
        # Command Display
        self.command_input = CommandDisplay()
        control_layout.addWidget(self.command_input)
        
        control_layout.addStretch()
        splitter.addWidget(control_panel)
        
        # ==================== OUTPUT AREA ====================
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("Whois results will appear here...")
        
        self.copy_button = CopyButton(self.output.output_text, self.main_window)
        self.copy_button.setParent(self.output.output_text)
        self.copy_button.raise_()
        self.output.output_text.installEventFilter(self)
        
        splitter.addWidget(self.output)
        splitter.setSizes([200, 500])
        
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
    
    def update_command(self):
        target = self.target_input.get_target().strip()
        if not target:
            target = "<target>"
        self.command_input.setText(f"whois {target}")
    
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
            self._notify("Whois scan finished.")
            return
        
        target = self.targets_queue.pop(0)
        self._info(f"Running Whois for: {target}")
        self._section(f"WHOIS: {target}")
        
        base_dir = create_target_dirs(target, self.group_name)
        self.log_file = os.path.join(base_dir, "Logs", "whois.txt")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        command = self.command_input.text().split()
        
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
        
        with open(self.log_file, "w") as f:
            f.write(self.output.toPlainText())
        
        if self.targets_queue:
            self._process_next_target()
        else:
            self._on_scan_completed()
            self._notify("Whois scan finished.")
    
    def _on_process_error(self, error):
        self._error(f"Process error: {error}")
        self._on_scan_completed()
    
    def _on_scan_completed(self):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.worker = None
        if self.main_window:
            self.main_window.active_process = None


class WhoisTool(ToolBase):
    """Whois tool plugin."""
    
    @property
    def name(self) -> str:
        return "Whois"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.INFO_GATHERING
    
    def get_widget(self, main_window):
        return WhoisView(self.name, self.category, main_window=main_window)
