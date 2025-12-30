# =============================================================================
# modules/strings.py
#
# Professional String Extraction Tool - Extract readable strings from binary files,
# executables, memory dumps, etc. Similar to the Unix 'strings' command.
# Enhanced with pattern detection, filtering, and security analysis features.
# =============================================================================

import os
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QFileDialog, QSpinBox, QCheckBox, QGroupBox, 
    QApplication, QMessageBox, QLineEdit, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor

from modules.bases import ToolBase, ToolCategory
from ui.styles import (
    COLOR_BACKGROUND_INPUT, COLOR_TEXT_PRIMARY, COLOR_BORDER, 
    COLOR_BORDER_INPUT_FOCUSED, StyledSpinBox, LABEL_STYLE_15PX
)


class StringsTool(ToolBase):
    """Professional string extraction tool for binary file analysis."""

    @property
    def name(self) -> str:
        return "Strings"

    @property
    def description(self) -> str:
        return "Extract and analyze readable strings from binary files and executables"

    @property
    def category(self):
        return ToolCategory.FILE_ANALYSIS

    @property
    def icon(self) -> str:
        return "📝"

    def get_widget(self, main_window: QWidget) -> QWidget:
        """Create the tool view widget."""
        return StringsToolView(main_window=main_window)


class StringsToolView(QWidget):
    """UI for the professional string extraction tool."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setStyleSheet(f"background-color: #1E1E1E;")
        self.selected_file = None
        self.all_results = []  # Store all extracted strings with metadata
        self._build_ui()

    def _build_ui(self):
        """Build the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create main panel
        main_panel = QWidget()
        main_panel.setStyleSheet(f"""
            QWidget {{
                background-color: #1C1C1C;
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
        """)
        main_layout.addWidget(main_panel)

        control_layout = QVBoxLayout(main_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        # Header
        header = QLabel("File Analysis › Strings Extractor Pro")
        header.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        control_layout.addWidget(header)

        # File selection and action buttons in one row
        file_layout = QHBoxLayout()
        
        file_label = QLabel("File:")
        file_label.setStyleSheet(LABEL_STYLE_15PX)
        file_layout.addWidget(file_label)

        self.file_path_display = QLabel("No file selected")
        self.file_path_display.setStyleSheet(f"""
            QLabel {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }}
        """)
        file_layout.addWidget(self.file_path_display, 1)

        self.browse_button = QPushButton("📁 Browse...")
        self.browse_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #4A4A4A;
                border: 1px solid {COLOR_BORDER_INPUT_FOCUSED};
            }}
        """)
        self.browse_button.clicked.connect(self._browse_file)
        file_layout.addWidget(self.browse_button)

        # Action buttons in the same row
        self.extract_button = QPushButton("🚀 Extract")
        self.extract_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #FF6B35;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #E55A2B;
            }}
            QPushButton:pressed {{
                background-color: #CC4F26;
            }}
            QPushButton:disabled {{
                background-color: #555;
                color: #999;
            }}
        """)
        self.extract_button.clicked.connect(self._extract_strings)
        self.extract_button.setEnabled(False)
        file_layout.addWidget(self.extract_button)

        self.clear_button = QPushButton("🗑️ Clear")
        self.clear_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #DC3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #C82333;
            }}
            QPushButton:pressed {{
                background-color: #BD2130;
            }}
        """)
        self.clear_button.clicked.connect(self._clear_output)
        file_layout.addWidget(self.clear_button)

        self.save_button = QPushButton("💾 Save")
        self.save_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #28A745;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #218838;
            }}
            QPushButton:pressed {{
                background-color: #1E7E34;
            }}
        """)
        self.save_button.clicked.connect(self._save_results)
        file_layout.addWidget(self.save_button)

        control_layout.addLayout(file_layout)

        # Options group
        options_group = QGroupBox("Extraction Options")
        options_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLOR_BORDER};
                border-radius: 5px;
                margin-top: 1ex;
                color: {COLOR_TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
        options_layout = QVBoxLayout(options_group)

        # First row: Length and encodings
        row1 = QHBoxLayout()
        
        min_len_label = QLabel("Min Length:")
        min_len_label.setStyleSheet(LABEL_STYLE_15PX)
        row1.addWidget(min_len_label)

        self.min_length_spin = StyledSpinBox()
        self.min_length_spin.setRange(1, 100)
        self.min_length_spin.setValue(4)
        self.min_length_spin.setToolTip("Minimum string length to extract")
        row1.addWidget(self.min_length_spin)

        row1.addSpacing(20)

        # Encoding checkboxes
        self.ascii_check = QCheckBox("ASCII")
        self.ascii_check.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_PRIMARY};")
        self.ascii_check.setChecked(True)
        row1.addWidget(self.ascii_check)

        self.unicode_le_check = QCheckBox("Unicode (UTF-16LE)")
        self.unicode_le_check.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_PRIMARY};")
        self.unicode_le_check.setChecked(True)
        row1.addWidget(self.unicode_le_check)

        self.unicode_be_check = QCheckBox("UTF-16BE")
        self.unicode_be_check.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_PRIMARY};")
        row1.addWidget(self.unicode_be_check)

        self.utf8_check = QCheckBox("UTF-8")
        self.utf8_check.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_PRIMARY};")
        row1.addWidget(self.utf8_check)

        row1.addStretch()
        options_layout.addLayout(row1)

        # Second row: Context view option
        row2 = QHBoxLayout()
        
        self.show_offset_check = QCheckBox("Show Hex Offsets")
        self.show_offset_check.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_PRIMARY};")
        self.show_offset_check.setChecked(True)
        self.show_offset_check.setToolTip("Display file offset where each string was found")
        row2.addWidget(self.show_offset_check)

        self.show_context_check = QCheckBox("Show Hex Context")
        self.show_context_check.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_PRIMARY};")
        self.show_context_check.setToolTip("Show hex bytes before/after each string")
        row2.addWidget(self.show_context_check)

        row2.addStretch()
        options_layout.addLayout(row2)

        control_layout.addWidget(options_group)

        # Pattern Filters Group
        filters_group = QGroupBox("Pattern Filters (Smart Detection)")
        filters_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLOR_BORDER};
                border-radius: 5px;
                margin-top: 1ex;
                color: {COLOR_TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
        filters_layout = QVBoxLayout(filters_group)

        # Filter checkboxes in two rows
        filter_row1 = QHBoxLayout()
        
        self.filter_urls = QCheckBox("🌐 URLs")
        self.filter_urls.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_PRIMARY};")
        filter_row1.addWidget(self.filter_urls)

        self.filter_ips = QCheckBox("🔴 IP Addresses")
        self.filter_ips.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_PRIMARY};")
        filter_row1.addWidget(self.filter_ips)

        self.filter_emails = QCheckBox("📧 Emails")
        self.filter_emails.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_PRIMARY};")
        filter_row1.addWidget(self.filter_emails)

        self.filter_paths = QCheckBox("📁 File Paths")
        self.filter_paths.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_PRIMARY};")
        filter_row1.addWidget(self.filter_paths)

        filter_row1.addStretch()
        filters_layout.addLayout(filter_row1)

        filter_row2 = QHBoxLayout()

        self.filter_registry = QCheckBox("🔑 Registry Keys")
        self.filter_registry.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_PRIMARY};")
        filter_row2.addWidget(self.filter_registry)

        self.filter_base64 = QCheckBox("🔐 Base64")
        self.filter_base64.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_PRIMARY};")
        filter_row2.addWidget(self.filter_base64)

        self.filter_crypto = QCheckBox("🔒 Crypto Keywords")
        self.filter_crypto.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_PRIMARY};")
        filter_row2.addWidget(self.filter_crypto)

        self.filter_all = QCheckBox("Show All (No Filter)")
        self.filter_all.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_PRIMARY}; font-weight: bold;")
        self.filter_all.setChecked(True)
        self.filter_all.stateChanged.connect(self._on_filter_all_changed)
        filter_row2.addWidget(self.filter_all)

        filter_row2.addStretch()
        filters_layout.addLayout(filter_row2)

        control_layout.addWidget(filters_group)

        # Search/Filter box
        search_layout = QHBoxLayout()
        
        search_label = QLabel("🔍 Search:")
        search_label.setStyleSheet(LABEL_STYLE_15PX)
        search_layout.addWidget(search_label)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter results by keyword (regex supported)...")
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLOR_BORDER_INPUT_FOCUSED};
            }}
        """)
        self.search_box.textChanged.connect(self._apply_filters)
        search_layout.addWidget(self.search_box, 1)

        self.case_sensitive_check = QCheckBox("Case Sensitive")
        self.case_sensitive_check.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_PRIMARY};")
        self.case_sensitive_check.stateChanged.connect(self._apply_filters)
        search_layout.addWidget(self.case_sensitive_check)

        self.regex_check = QCheckBox("Regex")
        self.regex_check.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_PRIMARY};")
        self.regex_check.stateChanged.connect(self._apply_filters)
        search_layout.addWidget(self.regex_check)

        control_layout.addLayout(search_layout)

        # Statistics Dashboard with all pattern counts
        stats_group = QGroupBox("📊 Statistics Dashboard")
        stats_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLOR_BORDER};
                border-radius: 5px;
                margin-top: 1ex;
                color: {COLOR_TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
        stats_layout = QGridLayout(stats_group)
        stats_layout.setSpacing(10)

        # Create stat labels with proper references
        self.stat_total = self._create_stat_label("Total Strings:", "0")
        self.stat_urls = self._create_stat_label("🌐 URLs:", "0", "#3B82F6")
        self.stat_ips = self._create_stat_label("🔴 IPs:", "0", "#EF4444")
        self.stat_emails = self._create_stat_label("📧 Emails:", "0", "#10B981")
        self.stat_paths = self._create_stat_label("📁 Paths:", "0", "#F59E0B")
        self.stat_registry = self._create_stat_label("🔑 Registry:", "0", "#8B5CF6")
        self.stat_base64 = self._create_stat_label("🔐 Base64:", "0", "#EC4899")
        self.stat_crypto = self._create_stat_label("🔒 Crypto:", "0", "#14B8A6")

        # Arrange in grid - 4 columns per row
        stats_layout.addWidget(self.stat_total[0], 0, 0)
        stats_layout.addWidget(self.stat_total[1], 0, 1)
        stats_layout.addWidget(self.stat_urls[0], 0, 2)
        stats_layout.addWidget(self.stat_urls[1], 0, 3)
        stats_layout.addWidget(self.stat_ips[0], 0, 4)
        stats_layout.addWidget(self.stat_ips[1], 0, 5)
        stats_layout.addWidget(self.stat_emails[0], 0, 6)
        stats_layout.addWidget(self.stat_emails[1], 0, 7)
        
        stats_layout.addWidget(self.stat_paths[0], 1, 0)
        stats_layout.addWidget(self.stat_paths[1], 1, 1)
        stats_layout.addWidget(self.stat_registry[0], 1, 2)
        stats_layout.addWidget(self.stat_registry[1], 1, 3)
        stats_layout.addWidget(self.stat_base64[0], 1, 4)
        stats_layout.addWidget(self.stat_base64[1], 1, 5)
        stats_layout.addWidget(self.stat_crypto[0], 1, 6)
        stats_layout.addWidget(self.stat_crypto[1], 1, 7)

        control_layout.addWidget(stats_group)

        # Output area
        output_group = QGroupBox("Extracted Strings")
        output_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLOR_BORDER};
                border-radius: 5px;
                margin-top: 1ex;
                color: {COLOR_TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
        output_layout = QVBoxLayout(output_group)

        # Output text area with copy button
        output_container = QWidget()
        output_grid = QGridLayout(output_container)
        output_grid.setContentsMargins(0, 0, 0, 0)
        output_grid.setSpacing(0)

        self.output_text = QTextEdit()
        self.output_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 8px;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 12px;
            }}
            QTextEdit:focus {{
                border: 1px solid {COLOR_BORDER_INPUT_FOCUSED};
            }}
        """)
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Extracted strings will appear here with color-coded patterns...")

        # Professional icon-only copy button at top-right
        self.copy_button = QPushButton("📋")
        self.copy_button.setFixedSize(36, 36)
        self.copy_button.setStyleSheet(f'''
            QPushButton {{
                font-size: 18px;
                background-color: {COLOR_BACKGROUND_INPUT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 18px;
                padding: 0px;
                margin: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_BORDER_INPUT_FOCUSED};
                border: 1px solid {COLOR_BORDER_INPUT_FOCUSED};
                transform: scale(1.05);
            }}
            QPushButton:pressed {{
                background-color: #CC8A00;
            }}
        ''')
        self.copy_button.setCursor(Qt.PointingHandCursor)
        self.copy_button.setToolTip("Copy all results to clipboard")
        self.copy_button.clicked.connect(self._copy_to_clipboard)

        output_grid.addWidget(self.output_text, 0, 0)
        output_grid.addWidget(self.copy_button, 0, 0, Qt.AlignTop | Qt.AlignRight)
        output_layout.addWidget(output_container)

        control_layout.addWidget(output_group)

    def _create_stat_label(self, title, value, color="#FFFFFF"):
        """Create a pair of labels for statistics display."""
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 500;")
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")
        
        return (title_label, value_label)

    def _on_filter_all_changed(self, state):
        """When 'Show All' is toggled, disable other filters."""
        if state == Qt.Checked:
            self.filter_urls.setChecked(False)
            self.filter_ips.setChecked(False)
            self.filter_emails.setChecked(False)
            self.filter_paths.setChecked(False)
            self.filter_registry.setChecked(False)
            self.filter_base64.setChecked(False)
            self.filter_crypto.setChecked(False)
        self._apply_filters()

    def _browse_file(self):
        """Open file browser to select a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Extract Strings",
            "",
            "All Files (*.*)"
        )
        
        if file_path:
            self.selected_file = file_path
            filename = os.path.basename(file_path)
            self.file_path_display.setText(filename)
            self.file_path_display.setToolTip(file_path)
            self.extract_button.setEnabled(True)

    def _extract_strings(self):
        """Extract strings from the selected file."""
        if not self.selected_file or not os.path.exists(self.selected_file):
            self._show_error("Please select a valid file first.")
            return

        min_length = self.min_length_spin.value()
        extract_ascii = self.ascii_check.isChecked()
        extract_unicode_le = self.unicode_le_check.isChecked()
        extract_unicode_be = self.unicode_be_check.isChecked()
        extract_utf8 = self.utf8_check.isChecked()

        if not any([extract_ascii, extract_unicode_le, extract_unicode_be, extract_utf8]):
            self._show_error("Please select at least one encoding type.")
            return

        try:
            self.output_text.clear()
            
            # Read file as binary
            with open(self.selected_file, 'rb') as f:
                data = f.read()

            self.all_results = []

            # Extract strings with different encodings
            if extract_ascii:
                ascii_strings = self._extract_ascii_strings(data, min_length)
                self.all_results.extend(ascii_strings)

            if extract_unicode_le:
                unicode_strings = self._extract_unicode_le_strings(data, min_length)
                self.all_results.extend(unicode_strings)

            if extract_unicode_be:
                unicode_be_strings = self._extract_unicode_be_strings(data, min_length)
                self.all_results.extend(unicode_be_strings)

            if extract_utf8:
                utf8_strings = self._extract_utf8_strings(data, min_length)
                self.all_results.extend(utf8_strings)

            # Classify and deduplicate
            seen = set()
            unique_results = []
            for result in self.all_results:
                if result['string'] not in seen:
                    seen.add(result['string'])
                    result['patterns'] = self._classify_string(result['string'])
                    unique_results.append(result)

            self.all_results = unique_results

            # Update statistics
            self._update_statistics()

            # Display results
            self._apply_filters()

            self._notify(f"Extracted {len(self.all_results)} unique strings")

        except Exception as e:
            self._show_error(f"Error extracting strings: {str(e)}")

    def _extract_ascii_strings(self, data, min_length):
        """Extract ASCII printable strings from binary data."""
        results = []
        ascii_pattern = rb'[ -~]{' + str(min_length).encode() + rb',}'
        
        for match in re.finditer(ascii_pattern, data):
            results.append({
                'string': match.group().decode('ascii', errors='ignore'),
                'offset': match.start(),
                'encoding': 'ASCII',
                'context_before': data[max(0, match.start()-8):match.start()],
                'context_after': data[match.end():min(len(data), match.end()+8)]
            })
        return results

    def _extract_unicode_le_strings(self, data, min_length):
        """Extract Unicode (UTF-16LE) strings from binary data."""
        results = []
        i = 0
        while i < len(data) - 1:
            if 32 <= data[i] <= 126 and data[i + 1] == 0:
                string_bytes = bytearray()
                start_offset = i
                j = i
                while j < len(data) - 1 and 32 <= data[j] <= 126 and data[j + 1] == 0:
                    string_bytes.append(data[j])
                    j += 2
                
                if len(string_bytes) >= min_length:
                    try:
                        results.append({
                            'string': string_bytes.decode('ascii'),
                            'offset': start_offset,
                            'encoding': 'UTF-16LE',
                            'context_before': data[max(0, start_offset-8):start_offset],
                            'context_after': data[j:min(len(data), j+8)]
                        })
                    except:
                        pass
                i = j
            else:
                i += 1
        return results

    def _extract_unicode_be_strings(self, data, min_length):
        """Extract Unicode (UTF-16BE) strings from binary data."""
        results = []
        i = 0
        while i < len(data) - 1:
            if data[i] == 0 and 32 <= data[i + 1] <= 126:
                string_bytes = bytearray()
                start_offset = i
                j = i
                while j < len(data) - 1 and data[j] == 0 and 32 <= data[j + 1] <= 126:
                    string_bytes.append(data[j + 1])
                    j += 2
                
                if len(string_bytes) >= min_length:
                    try:
                        results.append({
                            'string': string_bytes.decode('ascii'),
                            'offset': start_offset,
                            'encoding': 'UTF-16BE',
                            'context_before': data[max(0, start_offset-8):start_offset],
                            'context_after': data[j:min(len(data), j+8)]
                        })
                    except:
                        pass
                i = j
            else:
                i += 1
        return results

    def _extract_utf8_strings(self, data, min_length):
        """Extract UTF-8 strings from binary data."""
        results = []
        # Simple UTF-8 extraction (ASCII compatible part)
        current_string = bytearray()
        start_offset = 0
        
        for i, byte in enumerate(data):
            if 32 <= byte <= 126:
                if not current_string:
                    start_offset = i
                current_string.append(byte)
            else:
                if len(current_string) >= min_length:
                    try:
                        results.append({
                            'string': current_string.decode('utf-8'),
                            'offset': start_offset,
                            'encoding': 'UTF-8',
                            'context_before': data[max(0, start_offset-8):start_offset],
                            'context_after': data[i:min(len(data), i+8)]
                        })
                    except:
                        pass
                current_string = bytearray()
        
        return results

    def _classify_string(self, string):
        """Classify string into pattern categories."""
        patterns = []
        
        # URL pattern
        if re.search(r'https?://|ftp://|file://', string, re.IGNORECASE):
            patterns.append('url')
        
        # IP address pattern (IPv4)
        if re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', string):
            patterns.append('ip')
        
        # Email pattern
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', string):
            patterns.append('email')
        
        # File path patterns
        if re.search(r'[A-Za-z]:\\|/usr/|/etc/|/var/|/home/|/opt/', string):
            patterns.append('path')
        
        # Registry key pattern
        if re.search(r'HKEY_|HKLM|HKCU|HKCR|HKU', string, re.IGNORECASE):
            patterns.append('registry')
        
        # Base64 pattern (at least 20 chars, ends with = or ==)
        if re.search(r'^[A-Za-z0-9+/]{20,}={0,2}$', string):
            patterns.append('base64')
        
        # Crypto keywords
        crypto_keywords = ['MD5', 'SHA', 'AES', 'RSA', 'DES', 'ECDSA', 'HMAC', 'encrypt', 'decrypt', 'cipher', 'key', 'hash']
        if any(keyword.lower() in string.lower() for keyword in crypto_keywords):
            patterns.append('crypto')
        
        return patterns

    def _update_statistics(self):
        """Update statistics dashboard with pattern counts."""
        stats = {
            'url': 0,
            'ip': 0,
            'email': 0,
            'path': 0,
            'registry': 0,
            'base64': 0,
            'crypto': 0
        }
        
        # Count patterns
        for result in self.all_results:
            for pattern in result.get('patterns', []):
                if pattern in stats:
                    stats[pattern] += 1
        
        # Update all stat labels
        self.stat_total[1].setText(str(len(self.all_results)))
        self.stat_urls[1].setText(str(stats['url']))
        self.stat_ips[1].setText(str(stats['ip']))
        self.stat_emails[1].setText(str(stats['email']))
        self.stat_paths[1].setText(str(stats['path']))
        self.stat_registry[1].setText(str(stats['registry']))
        self.stat_base64[1].setText(str(stats['base64']))
        self.stat_crypto[1].setText(str(stats['crypto']))

    def _apply_filters(self):
        """Apply pattern filters and search to display results."""
        if not self.all_results:
            return

        self.output_text.clear()
        
        # Determine which patterns to show
        show_all = self.filter_all.isChecked()
        active_filters = []
        
        if not show_all:
            if self.filter_urls.isChecked():
                active_filters.append('url')
            if self.filter_ips.isChecked():
                active_filters.append('ip')
            if self.filter_emails.isChecked():
                active_filters.append('email')
            if self.filter_paths.isChecked():
                active_filters.append('path')
            if self.filter_registry.isChecked():
                active_filters.append('registry')
            if self.filter_base64.isChecked():
                active_filters.append('base64')
            if self.filter_crypto.isChecked():
                active_filters.append('crypto')

        # Get search parameters
        search_text = self.search_box.text()
        case_sensitive = self.case_sensitive_check.isChecked()
        use_regex = self.regex_check.isChecked()

        displayed_count = 0
        
        for result in self.all_results:
            string = result['string']
            patterns = result.get('patterns', [])
            
            # Apply pattern filter
            if not show_all and active_filters:
                if not any(p in active_filters for p in patterns):
                    continue
            
            # Apply search filter
            if search_text:
                try:
                    if use_regex:
                        flags = 0 if case_sensitive else re.IGNORECASE
                        if not re.search(search_text, string, flags):
                            continue
                    else:
                        if case_sensitive:
                            if search_text not in string:
                                continue
                        else:
                            if search_text.lower() not in string.lower():
                                continue
                except re.error:
                    # Invalid regex, skip filtering
                    pass
            
            # Display the string with formatting
            self._display_string(result)
            displayed_count += 1

        # Scroll to top
        self.output_text.moveCursor(QTextCursor.Start)
        
        # Update total displayed
        if search_text or (not show_all and active_filters):
            self.output_text.append(f"\n<br><b>--- Showing {displayed_count} of {len(self.all_results)} strings ---</b>")

    def _display_string(self, result):
        """Display a single string with color coding and formatting."""
        string = result['string']
        offset = result['offset']
        encoding = result['encoding']
        patterns = result.get('patterns', [])
        
        # Determine color based on patterns
        color = "#FFFFFF"  # Default white
        icon = ""
        
        if 'url' in patterns:
            color = "#3B82F6"  # Blue
            icon = "🌐"
        elif 'ip' in patterns:
            color = "#EF4444"  # Red
            icon = "🔴"
        elif 'email' in patterns:
            color = "#10B981"  # Green
            icon = "📧"
        elif 'path' in patterns:
            color = "#F59E0B"  # Yellow
            icon = "📁"
        elif 'registry' in patterns:
            color = "#8B5CF6"  # Purple
            icon = "🔑"
        elif 'base64' in patterns:
            color = "#EC4899"  # Pink
            icon = "🔐"
        elif 'crypto' in patterns:
            color = "#14B8A6"  # Teal
            icon = "🔒"

        # Build output line
        output_parts = []
        
        # Show offset if enabled
        if self.show_offset_check.isChecked():
            output_parts.append(f'<span style="color: #6B7280;">[0x{offset:08X}]</span>')
        
        # Show encoding
        output_parts.append(f'<span style="color: #9CA3AF;">[{encoding}]</span>')
        
        # Show context if enabled
        if self.show_context_check.isChecked():
            context_before = result.get('context_before', b'')
            context_after = result.get('context_after', b'')
            hex_before = ' '.join(f'{b:02X}' for b in context_before[-4:])
            hex_after = ' '.join(f'{b:02X}' for b in context_after[:4])
            output_parts.append(f'<span style="color: #4B5563;">{hex_before}</span>')
        
        # Show icon and string
        escaped_string = string.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        output_parts.append(f'{icon} <span style="color: {color}; font-weight: bold;">{escaped_string}</span>')
        
        # Show context after
        if self.show_context_check.isChecked():
            output_parts.append(f'<span style="color: #4B5563;">{hex_after}</span>')
        
        self.output_text.append(' '.join(output_parts) + '<br>')

    def _clear_output(self):
        """Clear the output area and reset statistics."""
        self.output_text.clear()
        self.all_results = []
        # Reset all statistics
        self.stat_total[1].setText("0")
        self.stat_urls[1].setText("0")
        self.stat_ips[1].setText("0")
        self.stat_emails[1].setText("0")
        self.stat_paths[1].setText("0")
        self.stat_registry[1].setText("0")
        self.stat_base64[1].setText("0")
        self.stat_crypto[1].setText("0")

    def _copy_to_clipboard(self):
        """Copy output to clipboard."""
        text = self.output_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self._notify("Results copied to clipboard.")
        else:
            self._show_error("Nothing to copy.")

    def _save_results(self):
        """Save extracted strings to a file."""
        if not self.all_results:
            self._show_error("No results to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Extracted Strings",
            "strings_output.txt",
            "Text Files (*.txt);;JSON Files (*.json);;CSV Files (*.csv);;All Files (*.*)"
        )

        if file_path:
            try:
                if file_path.endswith('.json'):
                    self._save_as_json(file_path)
                elif file_path.endswith('.csv'):
                    self._save_as_csv(file_path)
                else:
                    self._save_as_txt(file_path)
                
                self._notify(f"Results saved to {os.path.basename(file_path)}")
            except Exception as e:
                self._show_error(f"Error saving file: {str(e)}")

    def _save_as_txt(self, file_path):
        """Save results as plain text."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Strings Extraction Report\n")
            f.write(f"File: {self.selected_file}\n")
            f.write(f"Total Strings: {len(self.all_results)}\n")
            f.write("=" * 80 + "\n\n")
            
            for result in self.all_results:
                if self.show_offset_check.isChecked():
                    f.write(f"[0x{result['offset']:08X}] ")
                f.write(f"[{result['encoding']}] ")
                if result.get('patterns'):
                    f.write(f"[{','.join(result['patterns'])}] ")
                f.write(f"{result['string']}\n")

    def _save_as_json(self, file_path):
        """Save results as JSON."""
        import json
        
        output_data = {
            'file': self.selected_file,
            'total_strings': len(self.all_results),
            'strings': []
        }
        
        for result in self.all_results:
            output_data['strings'].append({
                'offset': f"0x{result['offset']:08X}",
                'encoding': result['encoding'],
                'patterns': result.get('patterns', []),
                'string': result['string']
            })
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)

    def _save_as_csv(self, file_path):
        """Save results as CSV."""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Offset', 'Encoding', 'Patterns', 'String'])
            
            for result in self.all_results:
                writer.writerow([
                    f"0x{result['offset']:08X}",
                    result['encoding'],
                    ','.join(result.get('patterns', [])),
                    result['string']
                ])

    def _show_error(self, message):
        """Show error message."""
        QMessageBox.critical(self, "Error", message)

    def _notify(self, message):
        """Send notification to main window."""
        if self.main_window and hasattr(self.main_window, 'notification_manager'):
            self.main_window.notification_manager.notify(message)
