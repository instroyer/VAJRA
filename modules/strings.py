# =============================================================================
# modules/strings.py
#
# Professional String Extraction Tool
# =============================================================================

import os
import re
import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog,
    QMessageBox
)
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from ui.styles import (
    RunButton, OutputView, HeaderLabel,
    StyledToolView, StyledGroupBox, StyledLabel, StyledCheckBox,
    StyledSpinBox, StyledLineEdit, BrowseButton, ToolSplitter,
    OutputHelper
)


class StringsTool(ToolBase):
    """Professional string extraction tool for binary file analysis."""

    name = "Strings"
    category = ToolCategory.FILE_ANALYSIS

    @property
    def description(self) -> str:
        return "Extract and analyze readable strings from binary files and executables"

    @property
    def icon(self) -> str:
        return "📝"

    def get_widget(self, main_window: QWidget) -> QWidget:
        """Create the tool view widget."""
        return StringsToolView(main_window=main_window)


class StringsToolView(StyledToolView, OutputHelper):
    """UI for the professional string extraction tool."""

    tool_name = "Strings"
    tool_category = "FILE_ANALYSIS"

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.selected_file = None
        self.all_results = []
        self._build_ui()

    def _build_ui(self):
        """Build the Strings tool UI."""
        # setStyleSheet handled by StyledToolView

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = ToolSplitter()

        # ==================== CONTROL PANEL ====================
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        # Header
        header = HeaderLabel(self.tool_category, self.tool_name)
        control_layout.addWidget(header)

        # File Selection
        file_group = StyledGroupBox("📂 File Selection")
        file_layout = QHBoxLayout(file_group)

        self.file_path_display = StyledLabel("No file selected")
        # Custom styling for path display to make it truncated/visible
        self.file_path_display.setStyleSheet("color: #FFFFFF; font-size: 13px;") 
        file_layout.addWidget(self.file_path_display, 1)

        browse_btn = BrowseButton()
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)

        self.extract_button = RunButton("EXTRACT")
        self.extract_button.setEnabled(False)
        self.extract_button.clicked.connect(self._extract_strings)
        file_layout.addWidget(self.extract_button)

        control_layout.addWidget(file_group)

        # Options Group
        options_group = StyledGroupBox("⚙️ Extraction Options")
        options_layout = QVBoxLayout(options_group)

        # First row: Length and encodings
        row1 = QHBoxLayout()

        min_len_label = StyledLabel("Min Length:")
        row1.addWidget(min_len_label)

        self.min_length_spin = StyledSpinBox()
        self.min_length_spin.setRange(1, 100)
        self.min_length_spin.setValue(4)
        self.min_length_spin.setToolTip("Minimum string length to extract")
        row1.addWidget(self.min_length_spin)

        row1.addSpacing(20)

        # Encoding checkboxes
        self.ascii_check = StyledCheckBox("ASCII")
        self.ascii_check.setChecked(True)
        row1.addWidget(self.ascii_check)

        self.unicode_le_check = StyledCheckBox("UTF-16LE")
        self.unicode_le_check.setChecked(True)
        row1.addWidget(self.unicode_le_check)

        self.unicode_be_check = StyledCheckBox("UTF-16BE")
        row1.addWidget(self.unicode_be_check)

        self.utf8_check = StyledCheckBox("UTF-8")
        row1.addWidget(self.utf8_check)

        row1.addStretch()
        options_layout.addLayout(row1)

        # Display options
        row2 = QHBoxLayout()
        self.show_offset_check = StyledCheckBox("Show Offset")
        self.show_offset_check.setChecked(True)
        row2.addWidget(self.show_offset_check)

        self.show_context_check = StyledCheckBox("Show Context")
        row2.addWidget(self.show_context_check)

        row2.addStretch()
        options_layout.addLayout(row2)
        control_layout.addWidget(options_group)

        # Filters Group
        filters_group = StyledGroupBox("🔍 Filters")
        filters_layout = QVBoxLayout(filters_group)

        # Filter checkboxes
        filter_row1 = QHBoxLayout()

        self.filter_all = StyledCheckBox("Show All")
        self.filter_all.setChecked(True)
        self.filter_all.stateChanged.connect(self._on_filter_all_changed)
        filter_row1.addWidget(self.filter_all)

        self.filter_urls = StyledCheckBox("🌐 URLs")
        filter_row1.addWidget(self.filter_urls)

        self.filter_ips = StyledCheckBox("🔴 IPs")
        filter_row1.addWidget(self.filter_ips)

        self.filter_emails = StyledCheckBox("📧 Emails")
        filter_row1.addWidget(self.filter_emails)

        self.filter_paths = StyledCheckBox("📁 Paths")
        filter_row1.addWidget(self.filter_paths)

        self.filter_registry = StyledCheckBox("🔑 Registry")
        filter_row1.addWidget(self.filter_registry)

        self.filter_base64 = StyledCheckBox("🔐 Base64")
        filter_row1.addWidget(self.filter_base64)

        self.filter_crypto = StyledCheckBox("🔒 Crypto")
        filter_row1.addWidget(self.filter_crypto)

        filter_row1.addStretch()
        filters_layout.addLayout(filter_row1)

        # Search box
        search_row = QHBoxLayout()
        search_label = StyledLabel("Search:")
        search_row.addWidget(search_label)

        self.search_box = StyledLineEdit()
        self.search_box.setPlaceholderText("Filter by text...")
        self.search_box.textChanged.connect(self._apply_filters)
        search_row.addWidget(self.search_box, 1)

        self.case_sensitive_check = StyledCheckBox("Case Sensitive")
        search_row.addWidget(self.case_sensitive_check)

        self.regex_check = StyledCheckBox("Regex")
        search_row.addWidget(self.regex_check)

        filters_layout.addLayout(search_row)
        control_layout.addWidget(filters_group)

        # Statistics Group
        stats_group = StyledGroupBox("📊 Statistics")
        stats_layout = QGridLayout(stats_group)
        stats_layout.setSpacing(10)

        # Create stat labels
        self.stat_total = self._create_stat_label("Total Strings:", "0")
        self.stat_urls = self._create_stat_label("🌐 URLs:", "0", "#3B82F6")
        self.stat_ips = self._create_stat_label("🔴 IPs:", "0", "#EF4444")
        self.stat_emails = self._create_stat_label("📧 Emails:", "0", "#10B981")
        self.stat_paths = self._create_stat_label("📁 Paths:", "0", "#F59E0B")
        self.stat_registry = self._create_stat_label("🔑 Registry:", "0", "#8B5CF6")
        self.stat_base64 = self._create_stat_label("🔐 Base64:", "0", "#EC4899")
        self.stat_crypto = self._create_stat_label("🔒 Crypto:", "0", "#14B8A6")

        # Arrange in grid
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
        
        control_layout.addStretch()
        splitter.addWidget(control_panel)

        # Output area
        self.output_text = OutputView(self.main_window)
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Strings results will appear here...")
        
        splitter.addWidget(self.output_text)
        splitter.setSizes([350, 600])

        main_layout.addWidget(splitter)

    def _create_stat_label(self, title, value, color="#FFFFFF"):
        """Create a pair of labels for statistics display."""
        title_label = StyledLabel(title)
        
        value_label = StyledLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 15px; font-weight: bold; background: transparent;")
        
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
            self._error("Please select a valid file first.")
            return

        min_length = self.min_length_spin.value()
        extract_ascii = self.ascii_check.isChecked()
        extract_unicode_le = self.unicode_le_check.isChecked()
        extract_unicode_be = self.unicode_be_check.isChecked()
        extract_utf8 = self.utf8_check.isChecked()

        if not any([extract_ascii, extract_unicode_le, extract_unicode_be, extract_utf8]):
            self._error("Please select at least one encoding type.")
            return

        try:
            self.output_text.clear()
            self._info(f"Analyzing {os.path.basename(self.selected_file)}...")
            
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
            self._error(f"Error extracting strings: {str(e)}")

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
        self.output_text.scrollToTop()
        
        # Update total displayed
        if search_text or (not show_all and active_filters):
            self.output_text.appendHtml(f"<br><b>--- Showing {displayed_count} of {len(self.all_results)} strings ---</b>")

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
            # Escape not needed for hex digits
            output_parts.append(f'<span style="color: #4B5563;">{hex_before}</span>')
        
        # Show icon and string
        escaped_string = html.escape(string)
        output_parts.append(f'{icon} <span style="color: {color}; font-weight: bold;">{escaped_string}</span>')
        
        # Show context after
        if self.show_context_check.isChecked():
            output_parts.append(f'<span style="color: #4B5563;">{hex_after}</span>')
        
        self.output_text.appendHtml(' '.join(output_parts))
