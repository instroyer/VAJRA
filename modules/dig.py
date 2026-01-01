
import os
import shlex
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QCheckBox, QGroupBox,
    QGridLayout, QSplitter, QButtonGroup, QRadioButton
)
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from ui.styles import BaseToolView, CopyButton
from ui.worker import ProcessWorker
from core.fileops import create_target_dirs
from ui.styles import (
    COLOR_BACKGROUND_INPUT, COLOR_TEXT_PRIMARY, COLOR_BORDER, 
    COLOR_BORDER_INPUT_FOCUSED
)

# ==============================
# Dig Tool
# ==============================

class DigTool(ToolBase):
    """DNS Information Gathering tool using Dig."""

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


class DigToolView(BaseToolView):
    def _build_base_ui(self):
        super()._build_base_ui()
        self.copy_button = CopyButton(self.output.output_text, self.main_window)
        self.output.layout().addWidget(self.copy_button, 0, 0, Qt.AlignTop | Qt.AlignRight)

    def __init__(self, name, category, main_window):
        # Initialize state attributes BEFORE super().__init__ calls update_command
        self.type_checks = {}  # Changed from type_buttons for CheckBoxes
        self.trace_check = None
        self.short_check = None
        self.ns_input = None
        self.log_file = None
        self.raw_output = ""
        
        super().__init__(name, category, main_window)
        
        # Build custom UI elements
        self._build_custom_ui()
        
        # Initial command update now that widgets exist
        self.update_command()

    def _build_custom_ui(self):
        """Inject Dig specific widgets into the BaseToolView layout."""
        # Use centralized options container
        
        # Configuration Grid (Query Types & Options)

        # Configuration Grid (Query Types & Options)
        config_group = QGroupBox("Query Configuration")
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
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
            }}
        """)
        config_layout_inner = QHBoxLayout(config_group)

        # 1. Query Types (Checkboxes)
        types_layout = QGridLayout()
        types_layout.setHorizontalSpacing(15)
        types_layout.setVerticalSpacing(8)
        
        # Standard Types
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



        # 1. Query Types (Checkboxes for Multiple Selection)
        types_layout = QGridLayout()
        types_layout.setHorizontalSpacing(15)
        types_layout.setVerticalSpacing(8)
        
        # self.type_group = QButtonGroup(self) # Removed for multiple selection
        # self.type_group.setExclusive(False)
        
        self.type_checks = {} # Back to checks

        # Standard Types
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
            cb = QCheckBox(label)
            cb.setStyleSheet(f"""
                QCheckBox {{
                    color: {COLOR_TEXT_PRIMARY};
                    spacing: 8px;
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                    border: 1px solid {COLOR_BORDER};
                    border-radius: 4px; /* Rectangular */
                    background-color: {COLOR_BACKGROUND_INPUT};
                }}
                QCheckBox::indicator:checked {{
                    background-color: #007ACC;
                    border: 1px solid #007ACC;
                }}
            """)
            if flag == "A":
                cb.setChecked(True)
            
            cb.stateChanged.connect(self.update_command)
            
            self.type_checks[flag] = cb
            types_layout.addWidget(cb, row, col)

        # Add Trace and Short options to the grid's empty spots (Row 2, Cols 2 & 3)
        self.trace_check = QCheckBox("Trace (+trace)")
        self.short_check = QCheckBox("Short (+short)")
        
        extra_options = [
            (self.trace_check, 2, 2),
            (self.short_check, 2, 3)
        ]

        for cb, row, col in extra_options:
            cb.setStyleSheet(f"""
                QCheckBox {{
                    color: {COLOR_TEXT_PRIMARY};
                    spacing: 8px;
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                    border: 1px solid {COLOR_BORDER};
                    border-radius: 4px; /* Rectangular */
                    background-color: {COLOR_BACKGROUND_INPUT};
                }}
                QCheckBox::indicator:checked {{
                    background-color: #007ACC;
                    border: 1px solid #007ACC;
                }}
            """)
            cb.stateChanged.connect(self.update_command)
            types_layout.addWidget(cb, row, col)

        config_layout_inner.addLayout(types_layout, stretch=2)
        
        # Separator line
        line = QWidget()
        line.setFixedWidth(1)
        line.setStyleSheet(f"background-color: {COLOR_BORDER};")
        config_layout_inner.addWidget(line)

        # 2. Options (Right Side) - Now only Nameserver
        options_layout = QVBoxLayout()
        options_layout.setSpacing(5)
        
        # Custom Nameserver
        ns_label = QLabel("Nameserver (@):")
        ns_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.ns_input = QLineEdit()
        self.ns_input.setPlaceholderText("e.g. 8.8.8.8")
        self.ns_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 4px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLOR_BORDER_INPUT_FOCUSED};
            }}
        """)
        self.ns_input.textChanged.connect(self.update_command)
        
        options_layout.addWidget(ns_label)
        options_layout.addWidget(self.ns_input)
        options_layout.addStretch() # Push input to top

        config_layout_inner.addLayout(options_layout, stretch=1)

        # Add to centralized container
        self.options_container.addWidget(config_group)

    def update_command(self):
        """Rebuild the Dig command based on UI state."""
        target = self.target_input.get_target().strip()
        if not target:
            target = "<target>"

        # Start with base command
        cmd_parts = ["dig"]
        
        # Add custom nameserver
        ns = self.ns_input.text().strip() if self.ns_input else ""
        if ns:
            cmd_parts.append(f"@{ns}")
            
        # Add target
        cmd_parts.append(target)
        
        # Add query types (Multiple Selection)
        if self.type_checks:
            for flag, cb in self.type_checks.items():
                if cb.isChecked():
                    cmd_parts.append(flag)
        
        # Add valid options
        if self.trace_check and self.trace_check.isChecked():
            cmd_parts.append("+trace")
        if self.short_check and self.short_check.isChecked():
            cmd_parts.append("+short")

        # Update the command preview line
        self.command_input.setText(" ".join(cmd_parts))

    def run_scan(self):
        """Execute the command from the command input box."""
        # Get command from the editable text box to respect manual edits
        cmd_text = self.command_input.text().strip()
        
        if not cmd_text:
            self._notify("Command is empty.")
            return

        # Basic target validation
        target = self.target_input.get_target().strip()
        if not target or "<target>" in cmd_text:
             self._notify("Please enter a valid target domain.")
             return

        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.output.clear()
        self.raw_output = "" # Init raw output buffer
        
        
        # UI Header (matching Whois style)
        self._info(f"Running Dig for: {target}")
        self.output.appendPlainText("") # Blank line
        self._section(f"DIG: {target}")

        # Setup File Saving
        try:
            # We treat single manual runs as not having a specific input file group
            base_dir = create_target_dirs(target, group_name=None)
            self.log_file = os.path.join(base_dir, "Logs", "dig.txt")
        except Exception as e:
            self._error(f"Failed to create log directories: {e}")
            self.log_file = None
        
        # Split command for subclass
        import shlex
        try:
            cmd_list = shlex.split(cmd_text)
        except ValueError:
            # Fallback for simple split if quotes are unbalanced
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
        
        # Write to file if path was set (Use RAW output only)
        if self.log_file:
            try:
                with open(self.log_file, "w", encoding="utf-8") as f:
                    f.write(self.raw_output)
                if self.main_window:
                    self.main_window.notification_manager.notify(f"Results saved to {os.path.basename(self.log_file)}")
            except Exception as e:
                self._error(f"Failed to write results to file: {e}")
