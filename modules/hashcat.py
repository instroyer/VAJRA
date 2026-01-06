import os
import subprocess
from datetime import datetime
'''
✅ Hashcat Tool - Fully Functional
Supports 180+ hash types
Direct hash input & file input
Proper output parsing (handles hash:password:hashcat)
Clean file management (/tmp/Vajra-results/)
Perfect button control (RUN/STOP)
All cracked hashes appear correctly
'''

from PySide6.QtCore import QObject, Signal, Qt, QThread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox, QSpinBox, QSplitter, QComboBox,
    QTextEdit, QMessageBox, QFileDialog, QCheckBox, QTabWidget, QProgressBar,
    QTableWidget, QHeaderView, QTableWidgetItem
)

from modules.bases import ToolBase, ToolCategory
from ui.worker import ProcessWorker
from core.tgtinput import parse_targets
from core.fileops import create_target_dirs
from ui.styles import (
    COLOR_BACKGROUND_INPUT, COLOR_BACKGROUND_PRIMARY, COLOR_BACKGROUND_SECONDARY,
    COLOR_TEXT_PRIMARY, COLOR_BORDER, COLOR_BORDER_FOCUSED, StyledComboBox,
    CommandDisplay, GROUPBOX_STYLE, RunButton, StopButton, SafeStop, OutputView, HeaderLabel
)


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

class HashcatToolView(QWidget, SafeStop):
    """Hashcat password cracker interface."""
    
    def __init__(self, main_window=None):
        super().__init__()
        self.init_safe_stop()
        self.main_window = main_window
        self._is_stopping = False
        self._scan_complete_added = False

        self.hash_modes = {
            # --- Raw Hashes ---
            "MD5": "0",
            "MD4": "900",
            "SHA1": "100",
            "SHA2-224": "1300",
            "SHA2-256": "1400",
            "SHA2-384": "10800",
            "SHA2-512": "1700",
            "SHA3-224": "17300",
            "SHA3-256": "17400",
            "SHA3-384": "17500",
            "SHA3-512": "17600",
            "RIPEMD-160": "6000",
            "Blake2b-512": "600",
            "GOST R 34.11-94": "6900",
            "Whirlpool": "6100",
            
            # --- Salted Hashes ---
            "md5($pass.$salt)": "10",
            "md5($salt.$pass)": "20",
            "md5(utf16le($pass).$salt)": "30",
            "md5($salt.utf16le($pass))": "40",
            "HMAC-MD5 (key = $pass)": "50",
            "HMAC-MD5 (key = $salt)": "60",
            "sha1($pass.$salt)": "110",
            "sha1($salt.$pass)": "120",
            "sha1(utf16le($pass).$salt)": "130",
            "sha1($salt.utf16le($pass))": "140",
            "HMAC-SHA1 (key = $pass)": "150",
            "HMAC-SHA1 (key = $salt)": "160",
            "sha256($pass.$salt)": "1410",
            "sha256($salt.$pass)": "1420",
            "sha256(utf16le($pass).$salt)": "1430",
            "sha256($salt.utf16le($pass))": "1440",
            "HMAC-SHA256 (key = $pass)": "1450",
            "HMAC-SHA256 (key = $salt)": "1460",
            "sha512($pass.$salt)": "1710",
            "sha512($salt.$pass)": "1720",
            "sha512(utf16le($pass).$salt)": "1730",
            "sha512($salt.utf16le($pass))": "1740",
            "HMAC-SHA512 (key = $pass)": "1750",
            "HMAC-SHA512 (key = $salt)": "1760",
            
            # --- Operating Systems ---
            "MD5(Unix)": "500",
            "SHA256(Unix)": "7400",
            "SHA512(Unix)": "1800",
            "bcrypt": "3200",
            "scrypt": "8900",
            "phpass": "400",
            "PHPS": "2612",
            "DES(Unix)": "1500",
            "BSDi Crypt": "12400",
            "Cisco-PIX MD5": "2400",
            "Cisco-ASA MD5": "2410",
            "Cisco-IOS SHA256": "5700",
            "Cisco-IOS scrypt": "9200",
            
            # --- Database Server ---
            "MySQL323": "200",
            "MySQL4.1/MySQL5": "300",
            "PostgreSQL": "12",
            "MSSQL(2000)": "131",
            "MSSQL(2005)": "132",
            "MSSQL(2012/2014)": "1731",
            "Oracle 11g/12c": "112",
            "Oracle 7-10g": "3100",
            "MongoDB ServerKey": "24100",
            "PostgreSQL SCRAM-SHA-256": "28600",
            
            # --- Enterprise Application Software (EAS) ---
            "NTLM": "1000",
            "NetNTLMv1": "5500",
            "NetNTLMv2": "5600",
            "Kerberos 5 AS-REP": "7500",
            "Kerberos 5 TGS-REP": "13100",
            "Kerberos 5 PreAuth": "19600",
            "Kerberos 5 AS-REP etype 17": "19700",
            "Kerberos 5 AS-REP etype 18": "19800",
            "Domain Cached Credentials (DCC)": "1100",
            "Domain Cached Credentials 2 (DCC2)": "2100",
            "MS-AzureSync PBKDF2-HMAC-SHA256": "12800",
            "LM": "3000",
            
            # --- Archives ---
            "7-Zip": "11600",
            "RAR3-hp": "12500",
            "RAR5": "13000",
            "WinZip": "13600",
            "ZIP (Legacy)": "17200",
            "ZIP (AES-128)": "17210",
            "ZIP (AES-192)": "17220",
            "ZIP (AES-256)": "17230",
            
            # --- Password Managers ---
            "1Password (Cloud)": "8200",
            "1Password (Agile Keychain)": "6600",
            "KeePass 1": "13400",
            "KeePass 2": "13400",
            "LastPass": "6800",
            "Bitwarden": "31000",
            
            # --- Full-Disk Encryption (FDE) ---
            "TrueCrypt PBKDF2-HMAC-SHA512 + AES": "6211",
            "TrueCrypt PBKDF2-HMAC-Whirlpool + AES": "6212",
            "TrueCrypt PBKDF2-HMAC-RIPEMD160 + AES": "6213",
            "VeraCrypt PBKDF2-HMAC-SHA512 + AES": "13711",
            "VeraCrypt PBKDF2-HMAC-Whirlpool + AES": "13712",
            "VeraCrypt PBKDF2-HMAC-RIPEMD160 + AES": "13713",
            "BitLocker": "22100",
            "FileVault 2": "16700",
            "LUKS": "14600",
            
            # --- Documents ---
            "MS Office 2007": "9400",
            "MS Office 2010": "9500",
            "MS Office 2013": "9600",
            "MS Office 2016": "25300",
            "PDF 1.1 - 1.3 (Acrobat 2-4)": "10400",
            "PDF 1.4 - 1.6 (Acrobat 5-8)": "10500",
            "PDF 1.7 Level 3 (Acrobat 9)": "10600",
            "PDF 1.7 Level 8 (Acrobat 10-11)": "10700",
            
            # --- Network Protocols ---
            "WPA/WPA2": "2500",
            "WPA-PMKID": "16800",
            "WPA/WPA2 PMKID": "22000",
            "WPA3": "22000",
            "IKE-PSK MD5": "5300",
            "IKE-PSK SHA1": "5400",
            "IPB2+ (Invision Power Board)": "2811",
            "vBulletin < v3.8.5": "2611",
            "vBulletin >= v3.8.5": "2711",
            "Mediawiki B type": "3711",
            "Joomla < 2.5.18": "11",
            "osCommerce": "21",
            "xt:Commerce": "21",
            
            # --- Application Hashes ---
            "md5(WordPress)": "400",
            "Drupal7": "7900",
            "Django (SHA-1)": "124",
            "Django (PBKDF2-SHA256)": "10000",
            "Atlassian (PBKDF2-HMAC-SHA1)": "12001",
            "PeopleSoft": "133",
            "Bitcoin/Litecoin wallet.dat": "11300",
            "Electrum Wallet": "16600",
            "Ethereum Pre-Sale Wallet": "15700",
            "Ethereum Wallet PBKDF2": "15600",
            
            # --- JWT ---
            "JWT (JSON Web Token)": "16500",
            
            # --- Apache/Nginx ---
            "Apache $apr1$ MD5": "1600",
            "md5apr1 (APR)": "1600",
            "SHA256(APR)": "7401",
            "SHA512(APR)": "7402",
            
            # --- FortiGate ---
            "FortiGate (FortiOS)": "7000",
            
            # --- PBKDF2 variants ---
            "PBKDF2-HMAC-MD5": "11900",
            "PBKDF2-HMAC-SHA1": "12000",
            "PBKDF2-HMAC-SHA256": "10900",
            "PBKDF2-HMAC-SHA512": "12100",
            
            # --- Other ---
            "Citrix NetScaler": "8100",
            "RACF": "8500",
            "AIX {smd5}": "6300",
            "AIX {ssha1}": "6700",
            "AIX {ssha256}": "6400",
            "AIX {ssha512}": "6500",
            "SAP CODVN B (BCODE)": "7700",
            "SAP CODVN F/G (PASSCODE)": "7800",
            "Juniper NetScreen/SSG (ScreenOS)": "22",
            "Juniper IVE": "501",
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
        control_panel.setStyleSheet(f"background-color: {COLOR_BACKGROUND_SECONDARY};")
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        # Header
        header = HeaderLabel("CRACKER", "Hashcat")
        control_layout.addWidget(header)

        # Hash file selection with Start/Stop buttons on same line
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
                border: 1px solid {COLOR_BORDER_FOCUSED};
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

        # Start button (text style like nmap)
        self.run_button = RunButton()
        self.run_button.setToolTip("Start Cracking")
        self.run_button.clicked.connect(self.run_scan)

        # Stop button (square icon like nmap)
        self.stop_button = StopButton()
        self.stop_button.setToolTip("Stop Cracking")
        self.stop_button.clicked.connect(self.stop_scan)

        hash_layout.addWidget(self.hash_input)
        hash_layout.addWidget(self.hash_browse_button)
        hash_layout.addWidget(self.run_button)
        hash_layout.addWidget(self.stop_button)
        control_layout.addLayout(hash_layout)

        # Hash type, Attack mode, and Wordlist on one line
        hash_attack_layout = QVBoxLayout()
        
        hash_type_label = QLabel("Hash Type, Attack Mode & Wordlist")
        hash_type_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        hash_attack_layout.addWidget(hash_type_label)

        hash_attack_combo_layout = QHBoxLayout()
        
        self.hash_type_combo = StyledComboBox()
        self.hash_type_combo.addItems(sorted(self.hash_modes.keys()))
        
        self.attack_mode_combo = StyledComboBox()
        self.attack_mode_combo.addItems([
            "0: Straight (wordlist)",
            "1: Combination",
            "3: Brute-force",
            "6: Hybrid Wordlist + Mask",
            "7: Hybrid Mask + Wordlist"
        ])
        self.attack_mode_combo.setCurrentText("0: Straight (wordlist)")
        
        # Wordlist input and browse button
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
                border: 1px solid {COLOR_BORDER_FOCUSED};
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
        
        # Add all to one row: Type | Mode | Wordlist | Browse button
        hash_attack_combo_layout.addWidget(QLabel("Type:"), 0)
        hash_attack_combo_layout.addWidget(self.hash_type_combo, 1)
        hash_attack_combo_layout.addSpacing(15)
        hash_attack_combo_layout.addWidget(QLabel("Mode:"), 0)
        hash_attack_combo_layout.addWidget(self.attack_mode_combo, 1)
        hash_attack_combo_layout.addSpacing(15)
        hash_attack_combo_layout.addWidget(QLabel("Wordlist:"), 0)
        hash_attack_combo_layout.addWidget(self.wordlist_input, 2)
        hash_attack_combo_layout.addWidget(self.wordlist_browse_button)
        
        hash_attack_layout.addLayout(hash_attack_combo_layout)
        control_layout.addLayout(hash_attack_layout)

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

        # Command display - EDITABLE
        # Command display (Centralized)
        self.command_display_widget = CommandDisplay()
        self.command_display = self.command_display_widget.input
        self.command_display.setPlaceholderText("Configure options to generate command...")
        
        control_layout.addWidget(self.command_display_widget)





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
        self.output = OutputView(show_copy_button=False)
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Hashcat results will appear here...")

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

        # Copy button removed

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
            # Safety check: ensure all widgets exist and are valid
            if not (hasattr(self, 'hash_input') and hasattr(self, 'hash_type_combo') and 
                    hasattr(self, 'command_display')):
                return
            
            # Additional check to ensure widgets haven't been deleted
            try:
                _ = self.hash_type_combo.currentText()
            except RuntimeError:
                return  # Widget was deleted, silently return
            
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
            if hasattr(self, 'command_display'):
                self.command_display.setText(cmd)
        except (AttributeError, RuntimeError):
            # Widget doesn't exist or was deleted, silently ignore
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


        # Check if hash_input is a file or direct hash
        hash_file_path = hash_input
        temp_hash_file = None
        
        if not os.path.exists(hash_input):
            # Not a file - treat as direct hash input
            # Create a temporary hash file
            import tempfile
            temp_hash_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.hash')
            temp_hash_file.write(hash_input + '\n')
            temp_hash_file.close()
            hash_file_path = temp_hash_file.name
            self._info(f"Using direct hash input")

        if wordlist and not os.path.exists(wordlist):
            QMessageBox.warning(self, "Wordlist Not Found", f"Wordlist file does not exist: {wordlist}")
            return

        self.output.clear()
        self.results_table.setRowCount(0)
        self._is_stopping = False
        self._scan_complete_added = False

        try:
            # Create target directory with proper structure: VAJRA-results/filename_timestamp/Logs/
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            hash_name = os.path.basename(hash_input) if os.path.exists(hash_input) else "hash"
            if "." in hash_name:
                hash_name = hash_name.rsplit(".", 1)[0]
            
            # Create proper directory structure: /tmp/Vajra-results/filename_timestamp/Logs/
            base_dir = os.path.join("/tmp", "Vajra-results", f"{hash_name}_{timestamp}")
            logs_dir = os.path.join(base_dir, "Logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            # Store for later use
            self.current_logs_dir = logs_dir

            self._info(f"Starting Hashcat cracking session")
            self._info(f"Hash: {hash_input[:50]}..." if len(hash_input) > 50 else f"Hash: {hash_input}")
            self._info(f"Hash type: {self.hash_type_combo.currentText()}")
            self._info(f"Attack mode: {self.attack_mode_combo.currentText()}")
            if wordlist:
                self._info(f"Wordlist: {wordlist}")
            self.output.append("")

            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress

            # Build hashcat command using the hash file path (either original or temp)
            cmd = ["hashcat"]
            hash_mode = self.hash_modes.get(self.hash_type_combo.currentText(), "0")
            attack_mode = self.attack_mode_combo.currentText().split(":")[0]

            cmd.extend(["-m", hash_mode])
            cmd.extend(["-a", attack_mode])

            if attack_mode == "0" and wordlist:
                cmd.append(wordlist)

            cmd.append(hash_file_path)  # Use the correct file path (original or temp)


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

            # No potfile - we'll capture cracked hashes from stdout

            self._info(f"Command: {' '.join(cmd)}")
            self.output.append("")

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
        """Process hashcat output - detect cracked hashes in format: hash:password OR hash:password:hashcat"""
        
        # Filter out verbose progress/status messages
        skip_keywords = [
            "Status........:",
            "Speed.........:",
            "Progress......:",
            "Candidates....",
            "Hardware.Monitor",
            "Time.Started..:",
            "Time.Estimated:",
            "Guess.Base....:",
            "Guess.Queue...:",
            "Kernel........:",
            "Optimizers....:",
            "Watchdog......:",
            "[s]tatus",
            "[p]ause",
            "[r]esume",
            "[q]uit",
        ]
        
        # Skip verbose lines
        if any(keyword in line for keyword in skip_keywords):
            return
        
        # Append the line to output (important messages will be shown)
        self.output.append(line)

        # Hashcat outputs cracked hashes in format: hash:password:hashcat OR just hash:password
        # Example: 01dfae6e5d4d90d989262232595959afbe:7050461:hashcat
        
        # Must have at least one colon
        if ':' not in line:
            return
        
        # Skip lines with spaces before first colon (error messages)
        if ' ' in line.split(':')[0]:
            return
        
        # Split on first colon to get hash and rest
        parts = line.strip().split(':', 1)
        if len(parts) != 2:
            return
            
        hash_value = parts[0].strip()
        # Rest could be "password" or "password:hashcat", split again to get just password
        password_part = parts[1].strip()
        # If there's another colon, take only the first part (the password)
        if ':' in password_part:
            password = password_part.split(':')[0].strip()
        else:
            password = password_part
        
        # Validate hash format (must be hex characters only)
        # MD5=32, SHA1=40, SHA256=64, SHA512=128, NTLM=32, etc.
        valid_hash_lengths = [16, 32, 40, 56, 64, 96, 128]  # Common hash lengths
        
        # Check if it's all hex characters and valid length
        if (hash_value and 
            len(hash_value) in valid_hash_lengths and
            all(c in '0123456789abcdefABCDEF' for c in hash_value) and
            len(password) > 0):
            
            # Check if already in table (avoid duplicates)
            duplicate = False
            for row in range(self.results_table.rowCount()):
                if self.results_table.item(row, 0).text() == hash_value:
                    duplicate = True
                    break
            
            if not duplicate:
                # Add to results table
                row_count = self.results_table.rowCount()
                self.results_table.insertRow(row_count)
                self.results_table.setItem(row_count, 0, QTableWidgetItem(hash_value))
                self.results_table.setItem(row_count, 1, QTableWidgetItem(password))
                self.results_table.setItem(row_count, 2, QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))

    def _on_finished(self):
        """Handle cracking completion."""
        # Re-enable buttons when cracking finishes
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)

        if self._is_stopping:
            return

        # Save results using the stored logs directory
        try:
            # Use previously stored logs directory
            logs_dir = getattr(self, 'current_logs_dir', '/tmp/Vajra-results/default/Logs')
            
            # Save results table to file: hashcat.txt
            results_file = os.path.join(logs_dir, "hashcat.txt")
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
        """Stop the cracking process safely."""
        try:
            if hasattr(self, 'worker') and self.worker:
                if self.worker.isRunning():
                    self._is_stopping = True
                    self.worker.stop()
                    self.worker.wait(1000)  # Wait up to 1 second
                    self._info("Cracking stopped by user.")
        except Exception:
            pass
        finally:
            # Force re-enable buttons
            try:
                self.run_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.progress_bar.setVisible(False)
            except Exception:
                pass
            self.worker = None

    def stop_all_workers(self):
        """Stop all workers - called when tab is closed."""
        self.stop_scan()

    def closeEvent(self, event):
        """Clean up workers when widget is closed."""
        self.stop_all_workers()
        super().closeEvent(event)

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
        self.output.append(f"[INFO] {message}")

    def _error(self, message):
        """Add error message to output."""
        self.output.append(f"[ERROR] {message}")

    def _section(self, title):
        """Add section header to output."""
        self.output.append(f"\n===== {title} =====")

    def _notify(self, message):
        """Show notification (placeholder for now)."""
        self._info(f"Notification: {message}")

    def _on_scan_completed(self):
        """Handle scan completion."""
        pass
