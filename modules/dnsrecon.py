
import os
import shlex
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QRadioButton, QGroupBox,
    QGridLayout, QSplitter, QButtonGroup, QFileDialog, QSpinBox,
    QCheckBox
)
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from ui.widgets import BaseToolView
from ui.worker import ProcessWorker
from core.fileops import create_target_dirs
from ui.styles import (
    COLOR_BACKGROUND_INPUT, COLOR_TEXT_PRIMARY, COLOR_BORDER, 
    COLOR_BORDER_INPUT_FOCUSED, COLOR_TEXT_SECONDARY
)

# ==============================
# DNSRecon Tool
# ==============================

class DnsReconTool(ToolBase):
    """Advanced DNS Enumeration tool."""

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
        return DnsReconToolView("DNSRecon", ToolCategory.INFO_GATHERING, main_window)


class DnsReconToolView(BaseToolView):
    def __init__(self, name, category, main_window):
        # Initialize attributes
        self.scan_mode_group = None
        self.modes = {}
        self.dict_input = None
        self.dict_browse_btn = None
        self.dict_container = None
        self.log_file = None
        
        super().__init__(name, category, main_window)
        
        # Insert custom UI
        self._build_custom_ui()
        
        # Initial update
        self.update_command()

    def _build_custom_ui(self):
        splitter = self.findChild(QSplitter)
        control_panel = splitter.widget(0)
        control_layout = control_panel.layout()
        
        # Insert after Target row (index 3)
        insertion_index = 3

        # --- Configuration Group ---
        config_group = QGroupBox("Scan Configuration")
        config_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                margin-top: 10px;
                margin-bottom: 10px;
                padding-top: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                padding: 0 5px;
                left: 10px;
            }}
        """)
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(15)

        # 1. Scan Types Grid (Radio Buttons - Single Selection)
        types_layout = QGridLayout()
        types_layout.setHorizontalSpacing(15)
        types_layout.setVerticalSpacing(10)

        self.scan_mode_group = QButtonGroup(self)
        self.scan_mode_group.setExclusive(True)

        # Mode definitions: (Label, Flag, Row, Col)
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

        self.modes = {}
        for label, mode_id, row, col in scan_modes:
            rb = QRadioButton(label)
            rb.setStyleSheet(f"""
                QRadioButton {{
                    color: {COLOR_TEXT_PRIMARY};
                    spacing: 8px;
                }}
                QRadioButton::indicator {{
                    width: 16px;
                    height: 16px;
                    border: 1px solid {COLOR_BORDER};
                    border-radius: 8px; /* Circle */
                    background-color: {COLOR_BACKGROUND_INPUT};
                }}
                QRadioButton::indicator:checked {{
                    background-color: #007ACC;
                    border: 1px solid #007ACC;
                }}
            """)
            if mode_id == "std":
                rb.setChecked(True)
            
            rb.toggled.connect(self.update_command)
            rb.toggled.connect(self._on_mode_changed)
            
            self.scan_mode_group.addButton(rb)
            self.modes[mode_id] = rb
            types_layout.addWidget(rb, row, col)

        config_layout.addLayout(types_layout)

        # 2. Dictionary Selection (Conditional)
        self.dict_container = QWidget()
        dict_layout = QHBoxLayout(self.dict_container)
        dict_layout.setContentsMargins(0, 0, 0, 0)
        
        dict_label = QLabel("Wordlist:")
        dict_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        
        self.dict_input = QLineEdit()
        self.dict_input.setPlaceholderText("/path/to/wordlist.txt")
        self.dict_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        self.dict_input.textChanged.connect(self.update_command)
        
        self.dict_browse_btn = QPushButton("📂")
        self.dict_browse_btn.setFixedSize(30, 30)
        self.dict_browse_btn.clicked.connect(self._browse_dict)
        self.dict_browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_BACKGROUND_INPUT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                color: {COLOR_TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                border: 1px solid {COLOR_BORDER_INPUT_FOCUSED};
            }}
        """)
        
        dict_layout.addWidget(dict_label)
        dict_layout.addWidget(self.dict_input)
        dict_layout.addWidget(self.dict_browse_btn)
        
        self.dict_container.setVisible(False) # Hidden by default
        config_layout.addWidget(self.dict_container)

        control_layout.insertWidget(insertion_index, config_group)

    def _on_mode_changed(self):
        # Show dictionary input only if Brute Force (BRT) is selected
        if "brt" in self.modes:
            is_brute = self.modes["brt"].isChecked()
            self.dict_container.setVisible(is_brute)

    def _browse_dict(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Wordlist", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            self.dict_input.setText(file_path)

    def update_command(self):
        target = self.target_input.get_target().strip()
        if not target:
            target = "<target>"
            
        if not self.modes:
            return

        cmd_parts = ["dnsrecon", "-d", target]

        # Determine mode logic (Single Selection)
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
             # Reverse lookup usually wants ip range but supports -d
             cmd_parts = ["dnsrecon", "-r", target] if "/" in target or target[0].isdigit() else ["dnsrecon", "-d", target, "-t", "rvl"]
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
        self.raw_output = "" # Init raw output buffer
        
        # UI Header (matching Whois style)
        self._info(f"Running DNSRecon for: {target}")
        self.output.appendPlainText("") # Blank line
        self._section(f"DNSRECON: {target}")

        # Setup File Saving
        try:
            base_dir = create_target_dirs(target, group_name=None)
            self.log_file = os.path.join(base_dir, "Logs", "dnsrecon.txt")
        except Exception as e:
            self._error(f"Failed to create log directories: {e}")
            self.log_file = None

        # self._info(f"Running: {cmd_text}")

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
        self.raw_output += text # Accumulate only raw output

    def _on_scan_completed(self):
        super()._on_scan_completed()
        
        self.output.appendPlainText("\n✨ Scan Complete.")
        
        if self.log_file:
            try:
                with open(self.log_file, "w", encoding="utf-8") as f:
                    f.write(self.raw_output)
                if self.main_window:
                    self.main_window.notification_manager.notify(f"Results saved to {os.path.basename(self.log_file)}")
            except Exception as e:
                self._error(f"Failed to write results to file: {e}")
