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
from ui.styles import (
    TARGET_INPUT_STYLE, COMBO_BOX_STYLE,
    COLOR_BACKGROUND_INPUT, COLOR_TEXT_PRIMARY, COLOR_BORDER, COLOR_BORDER_INPUT_FOCUSED,
    StyledComboBox  # Import from centralized styles
)


# ==============================
# John the Ripper Tool
# ==============================

class JohnTool(ToolBase):
    @property
    def name(self) -> str:
        return "John The Ripper"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CRACKER

    def get_widget(self, main_window: QWidget) -> QWidget:
        return JohnToolView(main_window=main_window)

class JohnToolView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._is_stopping = False
        self._scan_complete_added = False

        # John format mappings
        self.format_mappings = {
            "Automatic Detection": "auto",
            "DES": "des",
            "MD5": "md5",
            "Blowfish": "bf",
            "SHA256": "sha256crypt",
            "SHA512": "sha512crypt",
            "NTLM": "nt",
            "LM": "lm",
            "NetNTLM": "netntlm",
            "Kerberos": "krb5",
            "WPA2": "wpapsk",
            "MySQL": "mysql",
            "MSSQL": "mssql",
            "Oracle": "oracle",
            "PostgreSQL": "postgres",
            "Raw MD5": "raw-md5",
            "Raw SHA1": "raw-sha1",
            "Raw SHA256": "raw-sha256",
            "Raw SHA512": "raw-sha512"
        }

        self._build_custom_ui()

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
                background-color: #1C1C1C;
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
        """)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        # Header
        header = QLabel("Cracker › John The Ripper")
        header.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        control_layout.addWidget(header)

        # Command display (like nmap and hydra)
        command_label = QLabel("Command:")
        command_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 500;")
        self.command_display = QLineEdit()
        self.command_display.setReadOnly(True)
        self.command_display.setStyleSheet(TARGET_INPUT_STYLE)
        self.command_display.setPlaceholderText("Configure options to generate command...")
        
        command_layout = QVBoxLayout()
        command_layout.addWidget(command_label)
        command_layout.addWidget(self.command_display)
        control_layout.addLayout(command_layout)

        # Hash file selection with Start/Stop buttons
        hash_label = QLabel("Hash File / Input")
        hash_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        control_layout.addWidget(hash_label)

        # Hash input layout with buttons
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

        # Start button (icon only)
        self.run_button = QPushButton("▶")
        self.run_button.setFixedSize(36, 36)
        self.run_button.setCursor(Qt.PointingHandCursor)
        self.run_button.setToolTip("Start Cracking")
        self.run_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #FF6B35;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #E55A2B;
            }}
            QPushButton:pressed {{
                background-color: #CC4F26;
            }}
            QPushButton:disabled {{
                background-color: #555555;
                color: #999999;
            }}
        """)
        self.run_button.clicked.connect(self.run_scan)

        # Stop button (icon only)
        self.stop_button = QPushButton("⏹")
        self.stop_button.setFixedSize(36, 36)
        self.stop_button.setCursor(Qt.PointingHandCursor)
        self.stop_button.setToolTip("Stop Cracking")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #DC3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #C82333;
            }}
            QPushButton:pressed {{
                background-color: #BD2130;
            }}
            QPushButton:disabled {{
                background-color: #555555;
                color: #999999;
            }}
        """)
        self.stop_button.clicked.connect(self.stop_scan)

        hash_layout.addWidget(self.hash_input)
        hash_layout.addWidget(self.hash_browse_button)
        hash_layout.addWidget(self.run_button)
        hash_layout.addWidget(self.stop_button)
        control_layout.addLayout(hash_layout)

        # Hash Format, Attack Mode & Dictionary on one line
        config_layout = QVBoxLayout()

        config_label = QLabel("Cracking Configuration")
        config_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        config_layout.addWidget(config_label)

        # Consolidated line layout
        config_line_layout = QHBoxLayout()

        # Format
        format_label = QLabel("Format:")
        self.format_combo = StyledComboBox()
        self.format_combo.addItems(sorted(self.format_mappings.keys()))
        self.format_combo.setCurrentText("Automatic Detection")

        # Attack mode
        attack_label = QLabel("Mode:")
        self.attack_mode_combo = StyledComboBox()
        self.attack_mode_combo.addItems([
            "Wordlist (Dictionary)",
            "Incremental (Brute-force)",
            "External (Custom modes)",
            "Single Crack",
            "Mask Attack"
        ])
        self.attack_mode_combo.setCurrentText("Wordlist (Dictionary)")

        # Wordlist (for dictionary mode)
        wordlist_label = QLabel("Dictionary:")
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

        config_line_layout.addWidget(format_label, 0)
        config_line_layout.addWidget(self.format_combo, 1)
        config_line_layout.addSpacing(15)
        config_line_layout.addWidget(attack_label, 0)
        config_line_layout.addWidget(self.attack_mode_combo, 1)
        config_line_layout.addSpacing(15)
        config_line_layout.addWidget(wordlist_label, 0)
        config_line_layout.addWidget(self.wordlist_input, 2)
        config_line_layout.addWidget(self.wordlist_browse_button, 0)

        config_layout.addLayout(config_line_layout)
        control_layout.addLayout(config_layout)

        # Mask input (for mask attack)
        mask_label = QLabel("Mask (for Mask Attack)")
        mask_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        control_layout.addWidget(mask_label)

        self.mask_input = QLineEdit()
        self.mask_input.setPlaceholderText("e.g., ?l?l?l?l?d?d (4 lowercase + 2 digits)")
        self.mask_input.setMinimumHeight(36)
        self.mask_input.setStyleSheet(f"""
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
        control_layout.addWidget(self.mask_input)

        # Advanced options
        advanced_label = QLabel("Advanced Options")
        advanced_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        control_layout.addWidget(advanced_label)

        advanced_layout = QHBoxLayout()

        # Fork processes
        fork_label = QLabel("Processes:")
        self.fork_spin = QSpinBox()
        self.fork_spin.setRange(1, 8)
        self.fork_spin.setValue(1)
        self.fork_spin.setSuffix(" CPU cores")

        # Rules file
        self.rules_check = QCheckBox("Use Rules")
        self.rules_input = QLineEdit()
        self.rules_input.setPlaceholderText("Rules file...")
        self.rules_input.setEnabled(False)
        self.rules_check.stateChanged.connect(lambda: self.rules_input.setEnabled(self.rules_check.isChecked()))

        # Session name
        session_label = QLabel("Session:")
        self.session_input = QLineEdit()
        self.session_input.setPlaceholderText("session name")
        self.session_input.setText("john_session")

        advanced_layout.addWidget(fork_label)
        advanced_layout.addWidget(self.fork_spin)
        advanced_layout.addSpacing(20)
        advanced_layout.addWidget(self.rules_check)
        advanced_layout.addWidget(self.rules_input)
        advanced_layout.addSpacing(20)
        advanced_layout.addWidget(session_label)
        advanced_layout.addWidget(self.session_input)
        advanced_layout.addStretch()

        control_layout.addLayout(advanced_layout)

        # Command display
        command_label = QLabel("Command")
        command_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        self.command_input = QLineEdit()
        self.command_input.setReadOnly(False)
        self.command_input.setStyleSheet(f"""
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
        control_layout.addWidget(command_label)
        control_layout.addWidget(self.command_input)

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
                background-color: #28A745;
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
        self.results_table.setHorizontalHeaderLabels(["Username", "Password", "Hash"])
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
        self.tab_widget.addTab(self.results_table, "Cracked Accounts")

        splitter.addWidget(control_panel)
        splitter.addWidget(self.tab_widget)
        splitter.setSizes([500, 400])

        # Connect signals
        for widget in [self.hash_input, self.format_combo, self.attack_mode_combo,
                    self.wordlist_input, self.mask_input, self.fork_spin,
                    self.rules_check, self.rules_input, self.session_input]:
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(self.update_command)
            elif isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(self.update_command)
            elif isinstance(widget, QSpinBox):
                widget.valueChanged.connect(self.update_command)
            elif isinstance(widget, QCheckBox):
                widget.stateChanged.connect(self.update_command)

    def _info(self, message):
        """Add info message to output."""
        self.output.appendPlainText(f"[INFO] {message}")

    def _error(self, message):
        """Add error message to output."""
        self.output.appendPlainText(f"[ERROR] {message}")

    def _section(self, title):
        """Add section header to output."""
        self.output.appendPlainText(f"\n===== {title} =====")

    def _on_scan_completed(self):
        """Handle scan completion."""
        pass

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
            format_name = self.format_mappings.get(self.format_combo.currentText(), "auto")
            attack_mode = self.attack_mode_combo.currentText()

            cmd_parts = ["john"]

            # Format specification
            if format_name != "auto":
                cmd_parts.extend(["--format=" + format_name])

            # Attack mode specific options
            if attack_mode == "Wordlist (Dictionary)" and self.wordlist_input.text().strip():
                cmd_parts.extend(["--wordlist=" + self.wordlist_input.text().strip()])
            elif attack_mode == "Incremental (Brute-force)":
                cmd_parts.append("--incremental")
            elif attack_mode == "Mask Attack" and self.mask_input.text().strip():
                cmd_parts.extend(["--mask=" + self.mask_input.text().strip()])
            elif attack_mode == "Single Crack":
                cmd_parts.append("--single")

            # Rules
            if self.rules_check.isChecked() and self.rules_input.text().strip():
                cmd_parts.extend(["--rules=" + self.rules_input.text().strip()])

            # Fork processes
            if self.fork_spin.value() > 1:
                cmd_parts.extend(["--fork=" + str(self.fork_spin.value())])

            # Session name
            if self.session_input.text().strip():
                cmd_parts.extend(["--session=" + self.session_input.text().strip()])

            # Hash file
            cmd_parts.append(hash_input)

            cmd = " ".join(cmd_parts)
            if hasattr(self, 'command_display'):
                self.command_display.setText(cmd)
        except AttributeError:
            pass

    def run_scan(self):
        """Start hash cracking with John."""
        hash_input = self.hash_input.text().strip()
        if not hash_input:
            QMessageBox.warning(self, "No Hash Input", "Please select a hash file or enter a hash.")
            return

        attack_mode = self.attack_mode_combo.currentText()
        if attack_mode == "Wordlist (Dictionary)" and not self.wordlist_input.text().strip():
            QMessageBox.warning(self, "No Wordlist", "Please select a wordlist for dictionary attack.")
            return

        if attack_mode == "Mask Attack" and not self.mask_input.text().strip():
            QMessageBox.warning(self, "No Mask", "Please specify a mask for mask attack.")
            return

        if not os.path.exists(hash_input):
            QMessageBox.warning(self, "Hash File Not Found", f"Hash file does not exist: {hash_input}")
            return

        if self.wordlist_input.text().strip() and not os.path.exists(self.wordlist_input.text().strip()):
            QMessageBox.warning(self, "Wordlist Not Found", f"Wordlist file does not exist: {self.wordlist_input.text().strip()}")
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
            base_dir = create_target_dirs(f"john_{hash_name}")
            logs_dir = os.path.join(base_dir, "Logs")
            os.makedirs(logs_dir, exist_ok=True)

            self._info(f"Starting John The Ripper cracking session")
            self._info(f"Hash file: {hash_input}")
            self._info(f"Format: {self.format_combo.currentText()}")
            self._info(f"Attack mode: {attack_mode}")
            self.output.appendPlainText("")

            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress

            # Build john command
            cmd = ["john"]

            format_name = self.format_mappings.get(self.format_combo.currentText(), "auto")
            if format_name != "auto":
                cmd.append(f"--format={format_name}")

            # Attack mode specific options
            if attack_mode == "Wordlist (Dictionary)" and self.wordlist_input.text().strip():
                cmd.append(f"--wordlist={self.wordlist_input.text().strip()}")
            elif attack_mode == "Incremental (Brute-force)":
                cmd.append("--incremental")
            elif attack_mode == "Mask Attack" and self.mask_input.text().strip():
                cmd.append(f"--mask={self.mask_input.text().strip()}")
            elif attack_mode == "Single Crack":
                cmd.append("--single")

            # Rules
            if self.rules_check.isChecked() and self.rules_input.text().strip():
                cmd.append(f"--rules={self.rules_input.text().strip()}")

            # Fork processes
            if self.fork_spin.value() > 1:
                cmd.append(f"--fork={self.fork_spin.value()}")

            # Session name
            session_name = self.session_input.text().strip() or "john_session"
            cmd.append(f"--session={session_name}")

            # Hash file
            cmd.append(hash_input)

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
        """Process John output."""
        self.output.appendPlainText(line)

        # Parse cracked accounts and add to table
        # John typically outputs in format: username (hash_type:password)
        if "(" in line and ")" in line and ":" in line:
            try:
                # Extract username and password from John's output
                parts = line.split("(")
                if len(parts) >= 2:
                    username = parts[0].strip()
                    rest = parts[1].split(":")
                    if len(rest) >= 2:
                        password = rest[1].split(")")[0].strip()
                        # Add to results table
                        row_count = self.results_table.rowCount()
                        self.results_table.insertRow(row_count)
                        self.results_table.setItem(row_count, 0, QTableWidgetItem(username))
                        self.results_table.setItem(row_count, 1, QTableWidgetItem(password))
                        self.results_table.setItem(row_count, 2, QTableWidgetItem(line.strip()))
            except:
                pass

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
            base_dir = create_target_dirs(f"john_{hash_name}")
            logs_dir = os.path.join(base_dir, "Logs")

            # Save results table to file
            results_file = os.path.join(logs_dir, "cracked_accounts.txt")
            with open(results_file, 'w') as f:
                f.write("John The Ripper Cracking Results\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Hash Format: {self.format_combo.currentText()}\n")
                f.write(f"Attack Mode: {self.attack_mode_combo.currentText()}\n\n")

                f.write("Cracked Accounts:\n")
                f.write("-" * 80 + "\n")
                for row in range(self.results_table.rowCount()):
                    user_item = self.results_table.item(row, 0)
                    pass_item = self.results_table.item(row, 1)
                    hash_item = self.results_table.item(row, 2)
                    if user_item and pass_item and hash_item:
                        f.write(f"Username: {user_item.text()}\n")
                        f.write(f"Password: {pass_item.text()}\n")
                        f.write(f"Hash: {hash_item.text()}\n")
                        f.write("-" * 40 + "\n")

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

    def _notify(self, message):
        """Show notification (placeholder for now)."""
        self._info(f"Notification: {message}")
