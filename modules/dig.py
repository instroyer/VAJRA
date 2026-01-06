# =============================================================================
# modules/dig.py
#
# Dig - DNS Information Gathering Tool
# =============================================================================

import os
import shlex
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
)
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from core.tgtinput import TargetInput
from core.fileops import create_target_dirs
from ui.worker import ProcessWorker
from ui.styles import (
    RunButton, StopButton, CopyButton,
    StyledLineEdit, StyledCheckBox,
    StyledLabel, HeaderLabel, CommandDisplay, OutputView,
    StyledGroupBox, ToolSplitter,
    SafeStop, OutputHelper,
    TOOL_VIEW_STYLE, COLOR_BACKGROUND_SECONDARY, COLOR_BORDER
)


class DigTool(ToolBase):
    """Dig DNS gathering tool plugin."""

    @property
    def name(self) -> str:
        return "Dig"

    @property
    def description(self) -> str:
        return "Perform DNS lookups and information gathering (A, MX, NS, AXFR, etc.)"

    @property
    def category(self):
        return ToolCategory.INFO_GATHERING

    @property
    def icon(self) -> str:
        return "🌐"

    def get_widget(self, main_window: QWidget) -> QWidget:
        return DigToolView("Dig", ToolCategory.INFO_GATHERING, main_window)


class DigToolView(QWidget, SafeStop, OutputHelper):
    """Dig DNS information gathering interface."""
    
    tool_name = "Dig"
    tool_category = "INFO_GATHERING"
    
    def __init__(self, name, category, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_safe_stop()
        
        # State
        self.type_checks = {}
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
        
        # ==================== QUERY CONFIGURATION ====================
        config_group = StyledGroupBox("Query Configuration")
        config_layout_inner = QHBoxLayout(config_group)
        
        # Query Types
        types_layout = QGridLayout()
        types_layout.setHorizontalSpacing(15)
        types_layout.setVerticalSpacing(8)
        
        query_types = [
            ("A (IPv4)", "A", 0, 0),
            ("AAAA (IPv6)", "AAAA", 0, 1),
            ("MX (Mail)", "MX", 0, 2),
            ("NS (NameServer)", "NS", 0, 3),
            ("TXT (Text/SPF)", "TXT", 1, 0),
            ("CNAME (Alias)", "CNAME", 1, 1),
            ("SOA (Auth)", "SOA", 1, 2),
            ("PTR (Reverse)", "PTR", 1, 3),
            ("ANY (All)", "ANY", 2, 0),
            ("AXFR (Zone)", "AXFR", 2, 1),
        ]
        
        for label, flag, row, col in query_types:
            cb = StyledCheckBox(label)
            if flag == "A":
                cb.setChecked(True)
            cb.stateChanged.connect(self.update_command)
            self.type_checks[flag] = cb
            types_layout.addWidget(cb, row, col)
        
        # Extra options
        self.trace_check = StyledCheckBox("Trace (+trace)")
        self.trace_check.stateChanged.connect(self.update_command)
        types_layout.addWidget(self.trace_check, 2, 2)
        
        self.short_check = StyledCheckBox("Short (+short)")
        self.short_check.stateChanged.connect(self.update_command)
        types_layout.addWidget(self.short_check, 2, 3)
        
        config_layout_inner.addLayout(types_layout, stretch=2)
        
        # Separator
        line = QWidget()
        line.setFixedWidth(1)
        line.setStyleSheet(f"background-color: {COLOR_BORDER};")
        config_layout_inner.addWidget(line)
        
        # Nameserver
        options_layout = QVBoxLayout()
        options_layout.setSpacing(5)
        
        ns_label = StyledLabel("Nameserver (@):")
        self.ns_input = StyledLineEdit("e.g. 8.8.8.8")
        self.ns_input.textChanged.connect(self.update_command)
        
        options_layout.addWidget(ns_label)
        options_layout.addWidget(self.ns_input)
        options_layout.addStretch()
        
        config_layout_inner.addLayout(options_layout, stretch=1)
        control_layout.addWidget(config_group)
        
        # Command Display
        self.command_input = CommandDisplay()
        control_layout.addWidget(self.command_input)
        
        control_layout.addStretch()
        splitter.addWidget(control_panel)
        
        # ==================== OUTPUT AREA ====================
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("Dig results will appear here...")
        
        self.copy_button = CopyButton(self.output.output_text, self.main_window)
        self.copy_button.setParent(self.output.output_text)
        self.copy_button.raise_()
        self.output.output_text.installEventFilter(self)
        
        splitter.addWidget(self.output)
        splitter.setSizes([350, 400])
        
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
        
        cmd_parts = ["dig"]
        
        ns = self.ns_input.text().strip()
        if ns:
            cmd_parts.append(f"@{ns}")
        
        cmd_parts.append(target)
        
        for flag, cb in self.type_checks.items():
            if cb.isChecked():
                cmd_parts.append(flag)
        
        if self.trace_check.isChecked():
            cmd_parts.append("+trace")
        if self.short_check.isChecked():
            cmd_parts.append("+short")
        
        self.command_input.setText(" ".join(cmd_parts))
    
    def run_scan(self):
        cmd_text = self.command_input.text().strip()
        if not cmd_text:
            self._notify("Command is empty.")
            return
        
        target = self.target_input.get_target().strip()
        if not target or "<target>" in cmd_text:
            self._notify("Please enter a valid target domain.")
            return
        
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.output.clear()
        self.raw_output = ""
        
        self._info(f"Running Dig for: {target}")
        self.output.appendPlainText("")
        self._section(f"DIG: {target}")
        
        try:
            base_dir = create_target_dirs(target, group_name=None)
            self.log_file = os.path.join(base_dir, "Logs", "dig.txt")
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
