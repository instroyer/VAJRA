import os
import re
from datetime import datetime

from PySide6.QtCore import QObject, Signal, Qt, QRect, QThread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QLineEdit, QGroupBox, QMessageBox, QSplitter, QCompleter, QApplication, QCheckBox,
    QFileDialog, QProgressBar, QTextEdit
)

from modules.bases import ToolBase, ToolCategory
from ui.main_window import BaseToolView
from ui.worker import ProcessWorker
from core.tgtinput import parse_targets
from core.fileops import create_target_dirs
from ui.styles import (
    TARGET_INPUT_STYLE, COMBO_BOX_STYLE,
    COLOR_BACKGROUND_INPUT, COLOR_TEXT_PRIMARY, COLOR_BORDER, COLOR_BORDER_INPUT_FOCUSED,
    StyledComboBox  # Import from centralized styles
)
from PySide6.QtGui import QPainter, QPen, QBrush, QPolygon
from PySide6.QtCore import QPoint


# ==============================
# Strings Analysis Tool
# ==============================

class StringsAnalyzer(ToolBase):
    @property
    def name(self) -> str:
        return "Strings"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.FILE_ANALYSIS

    def get_widget(self, main_window: QWidget) -> QWidget:
        return StringsAnalyzerView(main_window=main_window)

class StringsAnalyzerView(BaseToolView):
    def __init__(self, main_window):
        super().__init__("Strings", ToolCategory.FILE_ANALYSIS, main_window)
        self._is_stopping = False
        self._scan_complete_added = False
        self._build_custom_ui()
        self.update_command()

    def _build_custom_ui(self):
        # Create a completely custom UI for the Strings tool
        splitter = self.findChild(QSplitter)
        if not splitter:
            # Create the basic splitter structure if it doesn't exist
            splitter = QSplitter(Qt.Vertical)
            self.layout().addWidget(splitter)

        # Create control panel
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        # Header
        header = QLabel(f"{self.category.name.replace('_', ' ')}  ›  {self.name}")
        header.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        control_layout.addWidget(header)

        # File selection
        file_label = QLabel("File to Analyze")
        file_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        control_layout.addWidget(file_label)

        # File input layout
        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select a file to analyze for strings...")
        self.file_path_input.setMinimumHeight(36)
        self.file_path_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 6px;
                font-size: 14px;
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLOR_BORDER_INPUT_FOCUSED};
            }}
        """)

        # File picker button (icon style)
        self.browse_button = QPushButton("📁")
        self.browse_button.setFixedSize(36, 36)
        self.browse_button.setCursor(Qt.PointingHandCursor)
        self.browse_button.clicked.connect(self._browse_file)
        self.browse_button.setStyleSheet(f"""
            QPushButton {{
                font-size: 16px;
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #4A4A4A;
            }}
            QPushButton:pressed {{
                background-color: #2A2A2A;
            }}
        """)

        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(self.browse_button)
        control_layout.addLayout(file_layout)

        # Run button
        self.run_button = QPushButton("ANALYZE STRINGS")
        self.run_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #17A2B8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #138496;
            }}
            QPushButton:pressed {{
                background-color: #117A8B;
            }}
        """)
        self.run_button.clicked.connect(self.run_scan)
        control_layout.addWidget(self.run_button, alignment=Qt.AlignCenter)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                text-align: center;
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: #17A2B8;
            }}
        """)

        control_layout.addWidget(self.progress_bar)
        control_layout.addStretch()

        # Output area
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 5px;
            }}
        """)

        splitter.addWidget(control_panel)
        splitter.addWidget(self.output)
        splitter.setSizes([200, 400])

        # Connect signals
        self.file_path_input.textChanged.connect(self.update_command)

    def _browse_file(self):
        """Browse for file to analyze."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File to Analyze", "",
            "All Files (*);;Binary Files (*.exe *.dll *.bin);;Text Files (*.txt *.log)"
        )
        if file_path:
            self.file_path_input.setText(file_path)
            self.update_command()

    def update_command(self):
        try:
            file_path = self.file_path_input.text().strip() or "<file>"
            cmd = f"strings {file_path}"
            # No command input in simplified UI
        except AttributeError:
            pass

    def run_scan(self):
        """Start strings analysis."""
        file_path = self.file_path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "No File Selected", "Please select a file to analyze.")
            return

        if not os.path.exists(file_path):
            QMessageBox.warning(self, "File Not Found", f"File does not exist: {file_path}")
            return

        self.output.clear()
        self._is_stopping = False
        self._scan_complete_added = False

        try:
            # Create target directory based on file name
            file_name = os.path.basename(file_path)
            base_dir = create_target_dirs(file_name)
            logs_dir = os.path.join(base_dir, "Logs")
            os.makedirs(logs_dir, exist_ok=True)

            self._info(f"Starting strings analysis on: {file_name}")
            self._info(f"File: {file_path}")
            self.output.appendPlainText("")

            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress

            # Start analysis with default settings
            self.worker = StringsAnalyzerWorker(
                file_path,
                4,  # min_length
                True,  # printable_only
                True,  # include_paths
                True,  # include_urls
                True,  # include_emails
                False,  # include_api_keys
                False   # include_ips
            )

            self.worker.progress.connect(self._on_progress)
            self.worker.finished_signal.connect(self._on_analysis_finished)
            self.worker.error.connect(self._error)

            self.run_button.setEnabled(False)
            self.worker.start()

        except Exception as e:
            self._error(f"Failed to start analysis: {str(e)}")

    def _on_progress(self, message):
        """Update progress message."""
        self._info(message)

    def _on_analysis_finished(self, results):
        """Handle analysis completion."""
        self.progress_bar.setVisible(False)
        self._on_scan_completed()

        if self._is_stopping:
            return

        if 'error' in results:
            self._error(results['error'])
            return

        # Display results
        file_name = results['file_name']
        total_strings = results['total_strings']
        strings_found = results['strings_found']

        self.output.appendPlainText("")
        self._section("Strings Analysis Results")
        self.output.appendPlainText(f"File: {file_name}")
        self.output.appendPlainText(f"Total strings found: {total_strings}")

        if strings_found:
            # Group strings by category
            categories = {
                'emails': [],
                'urls': [],
                'paths': [],
                'api_keys': [],
                'ips': [],
                'other': []
            }

            for string_info in strings_found:
                string_text = string_info['string']
                category = self._categorize_string(string_text)
                categories[category].append(string_info)

            # Display categorized results
            for category, strings in categories.items():
                if strings:
                    self.output.appendPlainText("")
                    category_name = category.replace('_', ' ').upper()
                    self.output.appendPlainText(f"{category_name} STRINGS ({len(strings)}):")
                    self.output.appendPlainText("-" * 60)

                    for string_info in strings[:50]:  # Limit display to 50 per category
                        offset = string_info['offset']
                        string_text = string_info['string']
                        self.output.appendPlainText(f"0x{offset:08X}: {string_text}")

                    if len(strings) > 50:
                        self.output.appendPlainText(f"... and {len(strings) - 50} more")

        # Save results to file
        try:
            base_dir = create_target_dirs(file_name)
            logs_dir = os.path.join(base_dir, "Logs")
            os.makedirs(logs_dir, exist_ok=True)

            strings_file = os.path.join(logs_dir, "strings.txt")
            with open(strings_file, 'w', encoding='utf-8') as f:
                f.write(f"Strings Analysis Results\n")
                f.write(f"File: {results['file_path']}\n")
                f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total strings found: {total_strings}\n")
                f.write(f"Minimum length: {results['min_length']}\n\n")

                if strings_found:
                    for category in ['emails', 'urls', 'paths', 'api_keys', 'ips', 'other']:
                        category_strings = [s for s in strings_found if self._categorize_string(s['string']) == category]
                        if category_strings:
                            category_name = category.replace('_', ' ').upper()
                            f.write(f"\n{category_name} STRINGS ({len(category_strings)}):\n")
                            f.write("-" * 60 + "\n")
                            for string_info in category_strings:
                                f.write(f"0x{string_info['offset']:08X}: {string_info['string']}\n")

            self._info(f"Results saved to: {strings_file}")

        except Exception as e:
            self._error(f"Failed to save results: {str(e)}")

        if not self._scan_complete_added:
            self._section("Analysis Complete")
            self._scan_complete_added = True

    def _categorize_string(self, string):
        """Categorize a string based on its content."""
        string = string.strip()

        # Email pattern
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', string):
            return 'emails'

        # URL pattern (more comprehensive)
        if re.match(r'^https?://', string) or re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', string):
            # Additional check for common TLDs
            if any(tld in string.lower() for tld in ['.com', '.org', '.net', '.edu', '.gov', '.mil', '.info', '.biz', '.io', '.dev']):
                return 'urls'

        # IP address pattern (IPv4)
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', string):
            parts = string.split('.')
            if all(0 <= int(part) <= 255 for part in parts):
                return 'ips'

        # API key patterns (common API key formats)
        string_lower = string.lower()
        if any(pattern in string_lower for pattern in [
            'api_key', 'apikey', 'api-key', 'secret', 'token', 'bearer',
            'sk-', 'pk-', 'xoxp-', 'xoxb-', 'ghp_', 'glpat'
        ]):
            return 'api_keys'

        # Check for API key-like patterns (long alphanumeric strings)
        if re.match(r'^[a-zA-Z0-9_-]{20,}$', string) and not any(char.isdigit() for char in string[-5:]):
            # Additional heuristics for API keys
            if len(string) >= 20 and any(c in string for c in ['_', '-', 'sk', 'pk', 'xox']):
                return 'api_keys'

        # Path pattern (Windows or Unix) - enhanced
        if '\\' in string or '/' in string:
            # Check for file extensions or path indicators
            if any(ext in string.lower() for ext in [
                '.exe', '.dll', '.so', '.dylib', '.txt', '.log', '.ini', '.cfg', '.conf',
                '.xml', '.json', '.yaml', '.yml', '.py', '.js', '.php', '.java', '.c', '.cpp',
                '.h', '.hpp', '.bat', '.sh', '.ps1', '.sql', '.db', '.sqlite'
            ]) or ':\\' in string or string.startswith('/') or '../' in string or './' in string:
                return 'paths'

        return 'other'

    def copy_results_to_clipboard(self):
        """Copy analysis results to clipboard."""
        results_text = self.output.toPlainText()
        if results_text.strip():
            QApplication.clipboard().setText(results_text)
            self._notify("Results copied to clipboard.")
        else:
            self._notify("No results to copy.")


# ==============================
# Strings Analysis Worker
# ==============================

class StringsAnalyzerWorker(QThread):
    """Worker thread for strings analysis."""
    progress = Signal(str)
    finished_signal = Signal(dict)
    error = Signal(str)

    def __init__(self, file_path, min_length, printable_only, include_paths, include_urls, include_emails, include_api_keys, include_ips):
        super().__init__()
        self.file_path = file_path
        self.min_length = min_length
        self.printable_only = printable_only
        self.include_paths = include_paths
        self.include_urls = include_urls
        self.include_emails = include_emails
        self.include_api_keys = include_api_keys
        self.include_ips = include_ips
        self.is_running = True

    def run(self):
        """Run the strings analysis."""
        try:
            self.progress.emit("Reading file...")

            # Read file in binary mode
            with open(self.file_path, 'rb') as f:
                data = f.read()

            file_size = len(data)
            self.progress.emit(f"Analyzing {file_size:,} bytes...")

            strings_found = []
            current_string = b''
            start_offset = 0

            # Scan through the binary data
            for i, byte in enumerate(data):
                if self.is_running:
                    # Check progress every 100KB
                    if i % 100000 == 0:
                        progress_percent = (i / file_size) * 100
                        self.progress.emit(f"Scanning... {progress_percent:.1f}% complete")

                    if self._is_printable(byte):
                        if not current_string:
                            start_offset = i
                        current_string += bytes([byte])
                    else:
                        if current_string and len(current_string) >= self.min_length:
                            try:
                                string_text = current_string.decode('utf-8', errors='ignore')
                                if len(string_text) >= self.min_length:
                                    if self._should_include_string(string_text):
                                        strings_found.append({
                                            'offset': start_offset,
                                            'string': string_text
                                        })
                            except:
                                pass
                        current_string = b''
                else:
                    break

            # Handle the last string
            if current_string and len(current_string) >= self.min_length and self.is_running:
                try:
                    string_text = current_string.decode('utf-8', errors='ignore')
                    if len(string_text) >= self.min_length and self._should_include_string(string_text):
                        strings_found.append({
                            'offset': start_offset,
                            'string': string_text
                        })
                except:
                    pass

            if self.is_running:
                result = {
                    'file_path': self.file_path,
                    'file_name': os.path.basename(self.file_path),
                    'total_strings': len(strings_found),
                    'strings_found': strings_found,
                    'min_length': self.min_length
                }
                self.finished_signal.emit(result)
            else:
                self.finished_signal.emit({'error': 'Analysis cancelled'})

        except Exception as e:
            self.error.emit(f"Analysis failed: {str(e)}")

    def _is_printable(self, byte):
        """Check if a byte represents a printable character."""
        if self.printable_only:
            return 32 <= byte <= 126  # Printable ASCII range
        else:
            return byte >= 32  # All printable characters including extended ASCII

    def _should_include_string(self, string):
        """Check if a string should be included based on filters."""
        # Always include if no filters are set
        if not (self.include_paths or self.include_urls or self.include_emails or self.include_api_keys or self.include_ips):
            return True

        # Check for specific types
        if self.include_emails and '@' in string and '.' in string:
            return True

        if self.include_urls and ('http' in string.lower() or 'www' in string.lower()):
            return True

        if self.include_paths and ('\\' in string or '/' in string):
            return True

        if self.include_api_keys:
            # API key patterns
            string_lower = string.lower()
            if any(pattern in string_lower for pattern in [
                'api_key', 'apikey', 'api-key', 'secret', 'token', 'bearer',
                'sk-', 'pk-', 'xoxp-', 'xoxb-', 'ghp_', 'glpat'
            ]) or (len(string) >= 20 and re.match(r'^[a-zA-Z0-9_-]+$', string)):
                return True

        if self.include_ips and re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', string):
            parts = string.split('.')
            if all(0 <= int(part) <= 255 for part in parts):
                return True

        return False
