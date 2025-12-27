import os
import subprocess
from datetime import datetime

from PySide6.QtCore import QObject, Signal, Qt, QRect, QThread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QLineEdit, QGroupBox, QMessageBox, QSplitter, QCompleter, QApplication, QCheckBox,
    QFileDialog, QProgressBar, QTextEdit, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QRadioButton, QButtonGroup
)

from modules.bases import ToolBase, ToolCategory
from ui.main_window import BaseToolView
from ui.worker import ProcessWorker
from core.tgtinput import parse_targets
from core.fileops import create_target_dirs
from ui.styles import TARGET_INPUT_STYLE, COMBO_BOX_STYLE, COLOR_BACKGROUND_INPUT, COLOR_TEXT_PRIMARY, COLOR_BORDER, COLOR_BORDER_INPUT_FOCUSED
from PySide6.QtGui import QPainter, QPen, QBrush, QPolygon
from PySide6.QtCore import QPoint


# ==============================
# Custom Styled ComboBox
# ==============================

class StyledComboBox(QComboBox):
    """Custom ComboBox with visible arrow and consistent background."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(self._get_style())

    def _get_style(self):
        return f"""
            QComboBox {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 8px;
                padding-right: 20px;
            }}
            QComboBox:focus {{
                border: 1px solid {COLOR_BORDER_INPUT_FOCUSED};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid {COLOR_BORDER};
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-color: {COLOR_BACKGROUND_INPUT};
            }}
            QComboBox::drop-down:hover {{
                background-color: #4A4A4A;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLOR_BACKGROUND_INPUT};
                border: 1px solid {COLOR_BORDER};
                color: {COLOR_TEXT_PRIMARY};
                selection-background-color: {COLOR_BORDER_INPUT_FOCUSED};
                selection-color: {COLOR_TEXT_PRIMARY};
                outline: none;
            }}
        """

    def paintEvent(self, event):
        """Custom paint event to draw arrow."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate drop-down button area (right side, 20px wide)
        width = self.width()
        height = self.height()
        drop_down_width = 20
        drop_down_x = width - drop_down_width
        drop_down_rect = QRect(drop_down_x, 0, drop_down_width, height)

        # Draw arrow triangle in center of drop-down area
        arrow_size = 6
        center_x = drop_down_rect.center().x()
        center_y = drop_down_rect.center().y()

        painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(QBrush(COLOR_TEXT_PRIMARY))

        # Draw downward triangle
        arrow = QPolygon([
            QPoint(center_x - arrow_size//2, center_y - arrow_size//3),
            QPoint(center_x + arrow_size//2, center_y - arrow_size//3),
            QPoint(center_x, center_y + arrow_size//2)
        ])
        painter.drawPolygon(arrow)

# ==============================
# Hashcat Tool
# ==============================

class HashcatTool(ToolBase):
    @property
    def name(self) -> str:
        return "Hashcat"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CRACKER

    def get_widget(self, main_window: QWidget) -> QWidget:
        return HashcatToolView(main_window=main_window)

class HashcatToolView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._is_stopping = False
        self._scan_complete_added = False

        # Hashcat hash modes dictionary
        self.hash_modes = {
            "MD5": "0",
            "MD4": "1",
            "SHA1": "100",
            "SHA256": "1400",
            "SHA512": "1700",
            "NTLM": "1000",
            "LM": "3000",
            "NetNTLMv1": "5500",
            "NetNTLMv2": "5600",
            "Kerberos 5 TGS-REP": "13100",
            "Kerberos 5 TGT": "13100",
            "WPA2": "2500",
            "WPA2 PMKID": "16800",
            "MySQL": "200",
            "PostgreSQL": "12",
            "Oracle": "112",
            "MSSQL": "132",
            "MD5(Unix)": "500",
            "SHA256(Unix)": "7400",
            "SHA512(Unix)": "1800",
            "Blowfish": "3200",
            "DES(Unix)": "1500",
            "MD5(APR)": "1600",
            "SHA256(APR)": "7401",
            "SHA512(APR)": "7402"
        }

        self._build_custom_ui()
        self.update_command()

    def _build_custom_ui(self):
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create splitter
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

        # Create control panel
        control_panel = QWidget()
        control_panel.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_BACKGROUND_INPUT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
        """)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        # Header
        header = QLabel("Cracker › Hashcat")
        header.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        control_layout.addWidget(header)

        # Hash file selection
        hash_label = QLabel("Hash File / Input")
        hash_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        control_layout.addWidget(hash_label)

        # Hash input layout
        hash_layout = QHBoxLayout()
        self.hash_input = QLineEdit()
        self.hash_input.setPlaceholderText("Select hash file or enter hash directly...")
        self.hash_input.setMinimumHeight(36)
        self.hash_input.setStyleSheet(f"""
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

        # Hash file picker button
        self.hash_browse_button = QPushButton("📁")
        self.hash_browse_button.setFixedSize(36, 36)
        self.hash_browse_button.setCursor(Qt.PointingHandCursor)
        self.hash_browse_button.clicked.connect(self._browse_hash_file)
        self.hash_browse_button.setStyleSheet(f"""
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

        hash_layout.addWidget(self.hash_input)
        hash_layout.addWidget(self.hash_browse_button)
        control_layout.addLayout(hash_layout)

        # Hash type selection
        hash_type_label = QLabel("Hash Type")
        hash_type_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        control_layout.addWidget(hash_type_label)

        self.hash_type_combo = StyledComboBox()
        self.hash_type_combo.addItems(sorted(self.hash_modes.keys()))
        control_layout.addWidget(self.hash_type_combo)

        # Attack mode selection
        attack_mode_label = QLabel("Attack Mode")
        attack_mode_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        control_layout.addWidget(attack_mode_label)

        self.attack_mode_combo = StyledComboBox()
        self.attack_mode_combo.addItems([
            "0: Straight (wordlist)",
            "1: Combination",
            "3: Brute-force",
            "6: Hybrid Wordlist + Mask",
            "7: Hybrid Mask + Wordlist"
        ])
        self.attack_mode_combo.setCurrentText("0: Straight (wordlist)")
        control_layout.addWidget(self.attack_mode_combo)

        # Wordlist selection
        wordlist_label = QLabel("Wordlist")
        wordlist_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        control_layout.addWidget(wordlist_label)

        wordlist_layout = QHBoxLayout()
        self.wordlist_input = QLineEdit()
        self.wordlist_input.setPlaceholderText("Select password wordlist...")
        self.wordlist_input.setMinimumHeight(36)
        self.wordlist_input.setStyleSheet(f"""
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

        self.wordlist_browse_button = QPushButton("📁")
        self.wordlist_browse_button.setFixedSize(36, 36)
        self.wordlist_browse_button.setCursor(Qt.PointingHandCursor)
        self.wordlist_browse_button.clicked.connect(self._browse_wordlist)
        self.wordlist_browse_button.setStyleSheet(f"""
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

        wordlist_layout.addWidget(self.wordlist_input)
        wordlist_layout.addWidget(self.wordlist_browse_button)
        control_layout.addLayout(wordlist_layout)

        # Advanced options
        advanced_label = QLabel("Advanced Options")
        advanced_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        control_layout.addWidget(advanced_label)

        advanced_layout = QHBoxLayout()

        # Workload profile
        workload_label = QLabel("Workload:")
        self.workload_combo = StyledComboBox()
        self.workload_combo.addItems([
            "1: Low",
            "2: Default",
            "3: High",
            "4: Nightmare"
        ])
        self.workload_combo.setCurrentText("2: Default")

        # GPU/CPU selection
        device_label = QLabel("Device:")
        self.device_combo = StyledComboBox()
        self.device_combo.addItems([
            "Auto",
            "GPU only",
            "CPU only"
        ])

        # Rules file
        self.rules_check = QCheckBox("Use Rules")
        self.rules_input = QLineEdit()
        self.rules_input.setPlaceholderText("Rules file...")
        self.rules_input.setEnabled(False)
        self.rules_check.stateChanged.connect(lambda: self.rules_input.setEnabled(self.rules_check.isChecked()))

        advanced_layout.addWidget(workload_label)
        advanced_layout.addWidget(self.workload_combo)
        advanced_layout.addSpacing(20)
        advanced_layout.addWidget(device_label)
        advanced_layout.addWidget(self.device_combo)
        advanced_layout.addSpacing(20)
        advanced_layout.addWidget(self.rules_check)
        advanced_layout.addWidget(self.rules_input)
        advanced_layout.addStretch()

        control_layout.addLayout(advanced_layout)

        # Command display
        command_label = QLabel("Command")
        command_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        self.command_input = QLineEdit()
        self.command_input.setReadOnly(True)
        self.command_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 6px;
                font-size: 14px;
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
        """)

        control_layout.addWidget(command_label)
        control_layout.addWidget(self.command_input)

        # Control buttons
        buttons_layout = QHBoxLayout()

        self.run_button = QPushButton("START CRACKING")
        self.run_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #FF6B35;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #E55A2B;
            }}
            QPushButton:pressed {{
                background-color: #CC4F26;
            }}
        """)
        self.run_button.clicked.connect(self.run_scan)

        self.stop_button = QPushButton("STOP")
        self.stop_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #DC3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #C82333;
            }}
            QPushButton:pressed {{
                background-color: #BD2130;
            }}
        """)
        self.stop_button.clicked.connect(self.stop_scan)
        self.stop_button.setEnabled(False)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.run_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addStretch()

        control_layout.addLayout(buttons_layout)

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
                background-color: #FF6B35;
            }}
        """)

        control_layout.addWidget(self.progress_bar)
        control_layout.addStretch()

        # Output area with tabs
        self.tab_widget = QTabWidget()

        # Main output tab
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 5px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }}
        """)

        # Results table tab
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Hash", "Password", "Time"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                gridline-color: {COLOR_BORDER};
            }}
            QHeaderView::section {{
                background-color: #2A2A2A;
                color: {COLOR_TEXT_PRIMARY};
                padding: 8px;
                border: 1px solid {COLOR_BORDER};
                font-weight: bold;
            }}
        """)

        self.tab_widget.addTab(self.output, "Output")
        self.tab_widget.addTab(self.results_table, "Cracked Hashes")

        splitter.addWidget(control_panel)
        splitter.addWidget(self.tab_widget)
        splitter.setSizes([500, 400])

        # Connect signals
        for widget in [self.hash_input, self.hash_type_combo, self.attack_mode_combo,
                      self.wordlist_input, self.workload_combo, self.device_combo,
                      self.rules_check, self.rules_input]:
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(self.update_command)
            elif isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(self.update_command)
            elif isinstance(widget, QCheckBox):
                widget.stateChanged.connect(self.update_command)

    def _browse_hash_file(self):
        """Browse for hash file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Hash File", "",
            "All Files (*);;Text Files (*.txt);;Hash Files (*.hash)"
        )
        if file_path:
            self.hash_input.setText(file_path)
            self.update_command()

    def _browse_wordlist(self):
        """Browse for wordlist file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Wordlist", "",
            "All Files (*);;Text Files (*.txt);;Wordlist Files (*.lst *.dict)"
        )
        if file_path:
            self.wordlist_input.setText(file_path)
            self.update_command()

    def update_command(self):
        try:
            hash_input = self.hash_input.text().strip() or "<hash_file>"
            hash_mode = self.hash_modes.get(self.hash_type_combo.currentText(), "0")
            attack_mode = self.attack_mode_combo.currentText().split(":")[0]
            wordlist = self.wordlist_input.text().strip() or "<wordlist>"

            cmd_parts = ["hashcat"]

            # Hash mode
            cmd_parts.extend(["-m", hash_mode])

            # Attack mode
            cmd_parts.extend(["-a", attack_mode])

            # Wordlist
            if attack_mode == "0":
                cmd_parts.append(wordlist)

            # Hash file
            cmd_parts.append(hash_input)

            # Workload profile
            workload = self.workload_combo.currentText().split(":")[0]
            cmd_parts.extend(["-w", workload])

            # Device selection
            if self.device_combo.currentText() == "GPU only":
                cmd_parts.append("-D 1")
            elif self.device_combo.currentText() == "CPU only":
                cmd_parts.append("-D 2")

            # Rules
            if self.rules_check.isChecked() and self.rules_input.text().strip():
                cmd_parts.extend(["-r", self.rules_input.text().strip()])

            cmd = " ".join(cmd_parts)
            if hasattr(self, 'command_input'):
                self.command_input.setText(cmd)
        except AttributeError:
            pass

    def run_scan(self):
        """Start hash cracking."""
        hash_input = self.hash_input.text().strip()
        if not hash_input:
            QMessageBox.warning(self, "No Hash Input", "Please select a hash file or enter a hash.")
            return

        wordlist = self.wordlist_input.text().strip()
        if not wordlist and self.attack_mode_combo.currentText().startswith("0:"):
            QMessageBox.warning(self, "No Wordlist", "Please select a wordlist for dictionary attack.")
            return

        if not os.path.exists(hash_input):
            QMessageBox.warning(self, "Hash File Not Found", f"Hash file does not exist: {hash_input}")
            return

        if wordlist and not os.path.exists(wordlist):
            QMessageBox.warning(self, "Wordlist Not Found", f"Wordlist file does not exist: {wordlist}")
            return

        self.output.clear()
        self.results_table.setRowCount(0)
        self._is_stopping = False
        self._scan_complete_added = False

        try:
            # Create target directory
            hash_name = os.path.basename(hash_input)
            if "." in hash_name:
                hash_name = hash_name.rsplit(".", 1)[0]
            base_dir = create_target_dirs(f"hashcat_{hash_name}")
            logs_dir = os.path.join(base_dir, "Logs")
            os.makedirs(logs_dir, exist_ok=True)

            self._info(f"Starting Hashcat cracking session")
            self._info(f"Hash file: {hash_input}")
            self._info(f"Hash type: {self.hash_type_combo.currentText()}")
            self._info(f"Attack mode: {self.attack_mode_combo.currentText()}")
            if wordlist:
                self._info(f"Wordlist: {wordlist}")
            self.output.appendPlainText("")

            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress

            # Build hashcat command
            cmd = ["hashcat"]
            hash_mode = self.hash_modes.get(self.hash_type_combo.currentText(), "0")
            attack_mode = self.attack_mode_combo.currentText().split(":")[0]

            cmd.extend(["-m", hash_mode])
            cmd.extend(["-a", attack_mode])

            if attack_mode == "0" and wordlist:
                cmd.append(wordlist)

            cmd.append(hash_input)

            # Workload profile
            workload = self.workload_combo.currentText().split(":")[0]
            cmd.extend(["-w", workload])

            # Device selection
            if self.device_combo.currentText() == "GPU only":
                cmd.extend(["-D", "1"])
            elif self.device_combo.currentText() == "CPU only":
                cmd.extend(["-D", "2"])

            # Rules
            if self.rules_check.isChecked() and self.rules_input.text().strip():
                cmd.extend(["-r", self.rules_input.text().strip()])

            # Output file
            potfile = os.path.join(logs_dir, "cracked_hashes.txt")
            cmd.extend(["--potfile-path", potfile])

            self._info(f"Command: {' '.join(cmd)}")
            self.output.appendPlainText("")

            self.worker = ProcessWorker(cmd)
            self.worker.output_ready.connect(self._on_output)
            self.worker.finished.connect(self._on_finished)
            self.worker.error.connect(self._error)

            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.worker.start()

        except Exception as e:
            self._error(f"Failed to start cracking: {str(e)}")

    def _on_output(self, line):
        """Process hashcat output."""
        self.output.appendPlainText(line)

        # Parse cracked hashes and add to table
        if ":" in line and len(line.split(":")) >= 2:
            parts = line.split(":", 1)
            if len(parts) == 2:
                hash_value, password = parts
                # Add to results table
                row_count = self.results_table.rowCount()
                self.results_table.insertRow(row_count)
                self.results_table.setItem(row_count, 0, QTableWidgetItem(hash_value.strip()))
                self.results_table.setItem(row_count, 1, QTableWidgetItem(password.strip()))
                self.results_table.setItem(row_count, 2, QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))

    def _on_finished(self):
        """Handle cracking completion."""
        self.progress_bar.setVisible(False)
        self._on_scan_completed()

        if self._is_stopping:
            return

        # Save results
        try:
            hash_name = os.path.basename(self.hash_input.text().strip())
            if "." in hash_name:
                hash_name = hash_name.rsplit(".", 1)[0]
            base_dir = create_target_dirs(f"hashcat_{hash_name}")
            logs_dir = os.path.join(base_dir, "Logs")

            # Save results table to file
            results_file = os.path.join(logs_dir, "cracked_results.txt")
            with open(results_file, 'w') as f:
                f.write("Hashcat Cracking Results\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Hash Type: {self.hash_type_combo.currentText()}\n")
                f.write(f"Attack Mode: {self.attack_mode_combo.currentText()}\n\n")

                f.write("Cracked Hashes:\n")
                f.write("-" * 80 + "\n")
                for row in range(self.results_table.rowCount()):
                    hash_item = self.results_table.item(row, 0)
                    pass_item = self.results_table.item(row, 1)
                    time_item = self.results_table.item(row, 2)
                    if hash_item and pass_item and time_item:
                        f.write(f"{hash_item.text()}:{pass_item.text()} (cracked at {time_item.text()})\n")

            self._info(f"Results saved to: {results_file}")

        except Exception as e:
            self._error(f"Failed to save results: {str(e)}")

        if not self._scan_complete_added:
            self._section("Cracking Complete")
            self._scan_complete_added = True

    def stop_scan(self):
        """Stop the cracking process."""
        if self.worker and self.worker.is_running:
            self._is_stopping = True
            self.worker.stop()
            self._info("Cracking stopped.")
        self._on_scan_completed()
        self.progress_bar.setVisible(False)

    def copy_results_to_clipboard(self):
        """Copy cracking results to clipboard."""
        results_text = self.output.toPlainText()
        if results_text.strip():
            QApplication.clipboard().setText(results_text)
            self._notify("Results copied to clipboard.")
        else:
            self._notify("No results to copy.")

    def _info(self, message):
        """Add info message to output."""
        self.output.appendPlainText(f"[INFO] {message}")

    def _error(self, message):
        """Add error message to output."""
        self.output.appendPlainText(f"[ERROR] {message}")

    def _section(self, title):
        """Add section header to output."""
        self.output.appendPlainText(f"\n===== {title} =====")

    def _notify(self, message):
        """Show notification (placeholder for now)."""
        self._info(f"Notification: {message}")

    def _on_scan_completed(self):
        """Handle scan completion."""
        pass