# =============================================================================
# modules/dnsrecon.py
#
# DNSRecon - Advanced DNS Enumeration Tool
# =============================================================================

import os
import shlex
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QButtonGroup, QFileDialog
)
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from core.tgtinput import TargetInput
from core.fileops import create_target_dirs
from ui.worker import ProcessWorker
from ui.styles import (
    RunButton, StopButton, CopyButton, BrowseButton,
    StyledLineEdit, StyledRadioButton,
    StyledLabel, HeaderLabel, CommandDisplay, OutputView,
    StyledGroupBox, ToolSplitter,
    SafeStop, OutputHelper,
    TOOL_VIEW_STYLE, COLOR_BACKGROUND_SECONDARY
)


class DnsReconTool(ToolBase):
    """DNSRecon enumeration tool plugin."""

    @property
    def name(self) -> str:
        return "DNSRecon"

    @property
    def description(self) -> str:
        return "Advanced DNS enumeration (Zone Transfer, Google/Bing Scraping, Brute Force, etc.)"

    @property
    def category(self):
        return ToolCategory.INFO_GATHERING

    @property
    def icon(self) -> str:
        return "🔍"

    def get_widget(self, main_window: QWidget) -> QWidget:
        return DnsReconView("DNSRecon", ToolCategory.INFO_GATHERING, main_window)


class DnsReconView(QWidget, SafeStop, OutputHelper):
    """DNSRecon advanced DNS enumeration interface."""
    
    tool_name = "DNSRecon"
    tool_category = "INFO_GATHERING"
    
    def __init__(self, name, category, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_safe_stop()
        
        # State
        self.modes = {}
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
        
        # ==================== CONFIGURATION GROUP ====================
        config_group = StyledGroupBox("Scan Configuration")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(15)
        
        # Scan Types Grid
        types_layout = QGridLayout()
        types_layout.setHorizontalSpacing(15)
        types_layout.setVerticalSpacing(10)
        
        self.scan_mode_group = QButtonGroup(self)
        self.scan_mode_group.setExclusive(True)
        
        scan_modes = [
            ("Standard (STD)", "std", 0, 0),
            ("Zone Transfer (AXFR)", "axfr", 0, 1),
            ("Reverse Lookup (PTR)", "rvl", 0, 2),
            ("Google Enumeration (GOO)", "goo", 1, 0),
            ("Bing Enumeration (BING)", "bing", 1, 1),
            ("Cache Snooping (SNOOP)", "snoop", 1, 2),
            ("Dictionary Brute Force (BRT)", "brt", 2, 0),
            ("Zone Walk (WALK)", "zonewalk", 2, 1),
        ]
        
        for label, mode_id, row, col in scan_modes:
            rb = StyledRadioButton(label)
            if mode_id == "std":
                rb.setChecked(True)
            rb.toggled.connect(self.update_command)
            rb.toggled.connect(self._on_mode_changed)
            self.scan_mode_group.addButton(rb)
            self.modes[mode_id] = rb
            types_layout.addWidget(rb, row, col)
        
        config_layout.addLayout(types_layout)
        
        # Dictionary Selection (conditional)
        self.dict_container = QWidget()
        dict_layout = QHBoxLayout(self.dict_container)
        dict_layout.setContentsMargins(0, 0, 0, 0)
        
        dict_label = StyledLabel("Wordlist:")
        self.dict_input = StyledLineEdit("/path/to/wordlist.txt")
        self.dict_input.textChanged.connect(self.update_command)
        
        self.dict_browse_btn = BrowseButton()
        self.dict_browse_btn.clicked.connect(self._browse_dict)
        
        dict_layout.addWidget(dict_label)
        dict_layout.addWidget(self.dict_input)
        dict_layout.addWidget(self.dict_browse_btn)
        
        self.dict_container.setVisible(False)
        config_layout.addWidget(self.dict_container)
        
        control_layout.addWidget(config_group)
        
        # Command Display
        self.command_input = CommandDisplay()
        control_layout.addWidget(self.command_input)
        
        control_layout.addStretch()
        splitter.addWidget(control_panel)
        
        # ==================== OUTPUT AREA ====================
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("DNSRecon results will appear here...")
        
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
    
    def _on_mode_changed(self):
        if "brt" in self.modes:
            is_brute = self.modes["brt"].isChecked()
            self.dict_container.setVisible(is_brute)
    
    def _browse_dict(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Wordlist", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.dict_input.setText(file_path)
    
    def update_command(self):
        target = self.target_input.get_target().strip()
        if not target:
            target = "<target>"
        
        if not self.modes:
            return
        
        cmd_parts = ["dnsrecon", "-d", target]
        
        selected_mode = "std"
        for mode_id, rb in self.modes.items():
            if rb.isChecked():
                selected_mode = mode_id
                break
        
        if selected_mode == "brt":
            cmd_parts.extend(["-t", "brt"])
            dict_path = self.dict_input.text().strip()
            if dict_path:
                cmd_parts.extend(["-D", dict_path])
            else:
                cmd_parts.extend(["-D", "<wordlist>"])
        elif selected_mode == "rvl":
            if "/" in target or (target and target[0].isdigit()):
                cmd_parts = ["dnsrecon", "-r", target]
            else:
                cmd_parts = ["dnsrecon", "-d", target, "-t", "rvl"]
        else:
            cmd_parts.extend(["-t", selected_mode])
        
        self.command_input.setText(" ".join(cmd_parts))
    
    def run_scan(self):
        cmd_text = self.command_input.text().strip()
        if not cmd_text:
            return
        
        target = self.target_input.get_target().strip()
        if not target or "<target>" in cmd_text or "<wordlist>" in cmd_text:
            self._notify("Please ensure Target and required Options are valid.")
            return
        
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.output.clear()
        self.raw_output = ""
        
        self._info(f"Running DNSRecon for: {target}")
        self.output.appendPlainText("")
        self._section(f"DNSRECON: {target}")
        
        try:
            base_dir = create_target_dirs(target, group_name=None)
            self.log_file = os.path.join(base_dir, "Logs", "dnsrecon.txt")
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
