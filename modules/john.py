"""
John the Ripper Tool Module
============================
Complete redesign with robust password extraction, clean architecture,
and comprehensive results tracking.

Author: VAJRA Offensive Security Platform
"""

import os
import subprocess
import tempfile
from datetime import datetime
from typing import Optional, Dict, List, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QSplitter, QApplication,
    QFileDialog, QProgressBar, QTextEdit, QTabWidget, QTableWidget, 
    QTableWidgetItem, QSpinBox, QCheckBox
)

from modules.bases import ToolBase, ToolCategory
from ui.worker import ProcessWorker
from ui.styles import (
    COLOR_BACKGROUND_INPUT, COLOR_TEXT_PRIMARY, COLOR_BORDER, 
    COLOR_BORDER_INPUT_FOCUSED, StyledComboBox,
    RUN_BUTTON_STYLE, STOP_BUTTON_STYLE,
    TOOL_HEADER_STYLE, TOOL_VIEW_STYLE
)


# ==============================
# John the Ripper Tool
# ==============================

class JohnTool(ToolBase):
    """John the Ripper password cracker integration."""
    
    @property
    def name(self) -> str:
        return "John The Ripper"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CRACKER
    
    def get_widget(self, main_window: QWidget) -> QWidget:
        return JohnToolView(main_window=main_window)


class JohnToolView(QWidget):
    """
    John the Ripper UI and functionality.
    
    This class provides a complete interface for password cracking with:
    - Multiple attack modes (wordlist, incremental, mask, single)
    - Comprehensive hash format support
    - Robust password extraction using 'john --show'
    - Results tracking with hash, username, and password
    - Automatic file storage in organized directory structure
    """
    
    FORMAT_MAPPINGS: Dict[str, str] = {
        "Automatic Detection": "auto",
        "7z": "7z",
        "AFS": "AFS",
        "AndroidBackup": "AndroidBackup",
        "Ansible Vault": "ansible",
        "AxCrypt": "AxCrypt",
        "AzureAD": "AzureAD",
        "adxcrypt": "adxcrypt",
        "agilekeychain": "agilekeychain",
        "aix-ssha1": "aix-ssha1",
        "aix-ssha256": "aix-ssha256",
        "aix-ssha512": "aix-ssha512",
        "andOTP": "andOTP",
        "argon2": "argon2",
        "as400-des": "as400-des",
        "as400-ssha1": "as400-ssha1",
        "asa-md5": "asa-md5",
        "BKS": "BKS",
        "BestCrypt": "BestCrypt",
        "BestCryptVE4": "BestCryptVE4",
        "Bitcoin": "Bitcoin",
        "BitLocker": "BitLocker",
        "Bitwarden": "Bitwarden",
        "Blackberry-ES10": "Blackberry-ES10",
        "Blockchain": "Blockchain",
        "bcrypt": "bcrypt",
        "bfegg": "bfegg",
        "bitshares": "bitshares",
        "bsdicrypt": "bsdicrypt",
        "CRC32": "CRC32",
        "Cisco ASA MD5": "pix-md5",
        "Cisco IOS MD5": "md5",
        "Cisco IOS SHA256": "sha256crypt",
        "Cisco VPN (PCF)": "pcf",
        "Citrix_NS10": "Citrix_NS10",
        "Clipperz": "Clipperz",
        "chap": "chap",
        "cloudkeychain": "cloudkeychain",
        "cq": "cq",
        "crypt": "crypt",
        "cryptoSafe": "cryptoSafe",
        "DPAPImk": "DPAPImk",
        "Django": "Django",
        "Drupal7": "Drupal7",
        "dahua": "dahua",
        "dashlane": "dashlane",
        "descrypt": "descrypt",
        "diskcryptor": "diskcryptor",
        "django-scrypt": "django-scrypt",
        "dmd5": "dmd5",
        "dmg": "dmg",
        "dominosec": "dominosec",
        "dominosec8": "dominosec8",
        "dragonfly3-32": "dragonfly3-32",
        "dragonfly3-64": "dragonfly3-64",
        "dragonfly4-32": "dragonfly4-32",
        "dragonfly4-64": "dragonfly4-64",
        "dummy": "dummy",
        "dynamic_n": "dynamic_n",
        "EPI": "EPI",
        "EPiServer": "EPiServer",
        "EncFS": "EncFS",
        "eCryptfs": "eCryptfs",
        "eigrp": "eigrp",
        "electrum": "electrum",
        "enpass": "enpass",
        "ethereum": "ethereum",
        "FVDE": "FVDE",
        "FormSpring": "FormSpring",
        "Fortigate": "Fortigate",
        "Fortigate256": "Fortigate256",
        "fde": "fde",
        "HAVAL-128-4": "HAVAL-128-4",
        "HAVAL-256-3": "HAVAL-256-3",
        "HMAC-MD5": "HMAC-MD5",
        "HMAC-SHA1": "HMAC-SHA1",
        "HMAC-SHA224": "HMAC-SHA224",
        "HMAC-SHA256": "HMAC-SHA256",
        "HMAC-SHA384": "HMAC-SHA384",
        "HMAC-SHA512": "HMAC-SHA512",
        "geli": "geli",
        "gost": "gost",
        "gpg": "gpg",
        "IKE": "IKE",
        "hMailServer": "hMailServer",
        "has-160": "has-160",
        "hdaa": "hdaa",
        "hsrp": "hsrp",
        "ipb2": "ipb2",
        "itunes-backup": "itunes-backup",
        "iwork": "iwork",
        "jwt": "jwt",
        "KeePass": "KeePass",
        "keychain": "keychain",
        "keyring": "keyring",
        "keystore": "keystore",
        "known_hosts": "known_hosts",
        "krb4": "krb4",
        "krb5": "krb5",
        "krb5-17": "krb5-17",
        "krb5-18": "krb5-18",
        "krb5-3": "krb5-3",
        "krb5asrep": "krb5asrep",
        "krb5pa-md5": "krb5pa-md5",
        "krb5pa-sha1": "krb5pa-sha1",
        "krb5tgs": "krb5tgs",
        "kwallet": "kwallet",
        "LM": "LM",
        "LUKS": "LUKS",
        "LastPass": "LastPass",
        "Lotus Notes/Domino 5": "lotus5",
        "Lotus Notes/Domino 6": "lotus6",
        "Lotus Notes/Domino 8": "lotus8",
        "leet": "leet",
        "lotus85": "lotus85",
        "lp": "lp",
        "lpcli": "lpcli",
        "MD2": "MD2",
        "MD5 (Apache)": "md5crypt-long",
        "MD5 (Unix)": "md5crypt",
        "MongoDB": "mongodb",
        "MS Cache (DCC)": "mscash",
        "MS Cache2 (DCC2)": "mscash2",
        "MS Office 2007": "office2007",
        "MS Office 2010": "office2010",
        "MS Office 2013": "office2013",
        "MS Office 2016/2019": "office",
        "MSCHAPv2": "MSCHAPv2",
        "MSSQL": "mssql",
        "MSSQL05": "mssql05",
        "MSSQL12": "mssql12",
        "MediaWiki": "MediaWiki",
        "Mozilla": "Mozilla",
        "MySQL": "mysql-sha1",
        "MySQL (Pre-4.1)": "mysql",
        "md5crypt": "md5crypt",
        "md5crypt-long": "md5crypt-long",
        "md5ns": "md5ns",
        "mdc2": "mdc2",
        "monero": "monero",
        "money": "money",
        "mscash": "mscash",
        "mscash2": "mscash2",
        "mschapv2-naive": "mschapv2-naive",
        "multibit": "multibit",
        "mysqlna": "mysqlna",
        "NTLM": "nt",
        "NetNTLMv2": "netntlmv2",
        "net-ah": "net-ah",
        "net-md5": "net-md5",
        "net-sha1": "net-sha1",
        "nethalflm": "nethalflm",
        "netlm": "netlm",
        "netlmv2": "netlmv2",
        "netntlm": "netntlm",
        "netntlm-naive": "netntlm-naive",
        "netntlmv2": "netntlmv2",
        "nk": "nk",
        "notes": "notes",
        "nsec3": "nsec3",
        "ODF": "ODF",
        "Office": "Office",
        "OpenBSD-SoftRAID": "OpenBSD-SoftRAID",
        "OpenVPN": "openvpn",
        "OpenVMS": "OpenVMS",
        "Oracle 10/11": "oracle",
        "Oracle 11g/12c": "oracle11",
        "Oracle 12c/18c": "oracle12c",
        "Oracle12C": "Oracle12C",
        "o10glogon": "o10glogon",
        "o3logon": "o3logon",
        "o5logon": "o5logon",
        "oldoffice": "oldoffice",
        "openssl-enc": "openssl-enc",
        "osc": "osc",
        "ospf": "ospf",
        "PBKDF2-HMAC-MD4": "PBKDF2-HMAC-MD4",
        "PBKDF2-HMAC-MD5": "pbkdf2-hmac-md5",
        "PBKDF2-HMAC-SHA1": "pbkdf2-hmac-sha1",
        "PBKDF2-HMAC-SHA256": "pbkdf2-hmac-sha256",
        "PBKDF2-HMAC-SHA512": "pbkdf2-hmac-sha512",
        "PDF": "PDF",
        "PEM": "PEM",
        "PHPS": "PHPS",
        "PHPS2": "PHPS2",
        "PKZIP": "PKZIP",
        "PST": "PST",
        "Padlock": "Padlock",
        "Palshop": "Palshop",
        "Panama": "Panama",
        "Password Safe": "pwsafe",
        "PeopleSoft": "peoplesoft",
        "Postgres": "postgres",
        "PuTTY": "PuTTY",
        "pfx": "pfx",
        "pgpdisk": "pgpdisk",
        "pgpsda": "pgpsda",
        "pgpwde": "pgpwde",
        "phpass": "phpass",
        "plaintext": "plaintext",
        "po": "po",
        "RACF": "RACF",
        "RACF-KDFAES": "RACF-KDFAES",
        "RAdmin": "RAdmin",
        "RAKP": "RAKP",
        "RAR": "rar",
        "RAR5": "RAR5",
        "RVARY": "RVARY",
        "Raw-Blake2": "Raw-Blake2",
        "Raw-Keccak": "Raw-Keccak",
        "Raw-Keccak-256": "Raw-Keccak-256",
        "Raw-MD4": "Raw-MD4",
        "Raw-MD5": "Raw-MD5",
        "Raw-MD5u": "Raw-MD5u",
        "Raw-SHA1": "Raw-SHA1",
        "Raw-SHA1-AxCrypt": "Raw-SHA1-AxCrypt",
        "Raw-SHA1-Linkedin": "Raw-SHA1-Linkedin",
        "Raw-SHA224": "Raw-SHA224",
        "Raw-SHA256": "Raw-SHA256",
        "Raw-SHA3": "Raw-SHA3",
        "Raw-SHA384": "Raw-SHA384",
        "Raw-SHA512": "Raw-SHA512",
        "qnx": "qnx",
        "radius": "radius",
        "restic": "restic",
        "ripemd-128": "ripemd-128",
        "ripemd-160": "ripemd-160",
        "rsvp": "rsvp",
        "SAP CODVN B (BCODE)": "sapb",
        "SAP CODVN G (PASSCODE)": "sapg",
        "SAP CODVN H (PWDSALTEDHASH)": "saph",
        "SIP": "SIP",
        "SL3": "SL3",
        "SNMP": "SNMP",
        "SSH": "SSH",
        "SSH Private Key": "SSH",
        "SSHA512": "SSHA512",
        "Salted-SHA1": "Salted-SHA1",
        "Siemens-S7": "Siemens-S7",
        "Signal": "Signal",
        "Snefru-128": "Snefru-128",
        "Snefru-256": "Snefru-256",
        "Stribog-256": "Stribog-256",
        "Stribog-512": "Stribog-512",
        "STRIP": "STRIP",
        "SunMD5": "SunMD5",
        "Sybase ASE": "sybasease",
        "Sybase-PROP": "Sybase-PROP",
        "SybaseASE": "SybaseASE",
        "sapb": "sapb",
        "sapg": "sapg",
        "saph": "saph",
        "sappse": "sappse",
        "scram": "scram",
        "scrypt": "scrypt",
        "securezip": "securezip",
        "sha1crypt": "sha1crypt",
        "sha256crypt": "sha256crypt",
        "sha512crypt": "sha512crypt",
        "skein-256": "skein-256",
        "skein-512": "skein-512",
        "skey": "skey",
        "solarwinds": "solarwinds",
        "sspr": "sspr",
        "Tiger": "Tiger",
        "tacacs-plus": "tacacs-plus",
        "tc_aes_xts": "tc_aes_xts",
        "tc_ripemd160": "tc_ripemd160",
        "tc_ripemd160boot": "tc_ripemd160boot",
        "tc_sha512": "tc_sha512",
        "tc_whirlpool": "tc_whirlpool",
        "tcp-md5": "tcp-md5",
        "telegram": "telegram",
        "tezos": "tezos",
        "tripcode": "tripcode",
        "VNC": "VNC",
        "vdi": "vdi",
        "vmx": "vmx",
        "vtp": "vtp",
        "WoWSRP": "WoWSRP",
        "WPA-PSK PMK": "wpapsk-pmk",
        "WPA/WPA2": "wpapsk",
        "WordPress": "phpass",
        "wbb3": "wbb3",
        "whirlpool": "whirlpool",
        "whirlpool0": "whirlpool0",
        "whirlpool1": "whirlpool1",
        "xmpp-scram": "xmpp-scram",
        "xsha": "xsha",
        "xsha512": "xsha512",
        "ZIP": "pkzip",
        "ZipMonster": "ZipMonster",
        "zed": "zed"
    }
    
    def __init__(self, main_window: QWidget):
        """Initialize the John the Ripper tool view."""
        super().__init__()
        self.main_window = main_window
        
        # State variables
        self._is_stopping = False
        self._temp_hash_file: Optional[str] = None
        self._hash_file_path: Optional[str] = None
        self._logs_dir: Optional[str] = None
        self._original_hashes: Dict[str, str] = {}  # Map username to original hash
        
        # Build UI
        self._build_ui()
        
    def _build_ui(self):
        """Construct the main user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)
        
        # Control panel
        control_panel = self._create_control_panel()
        splitter.addWidget(control_panel)
        
        # Output panel with tabs
        output_panel = self._create_output_panel()
        splitter.addWidget(output_panel)
        
        # Set initial sizes
        splitter.setSizes([500, 400])
        
    def _create_control_panel(self) -> QWidget:
        """Create the control panel with all input widgets."""
        panel = QWidget()
        panel.setStyleSheet(TOOL_VIEW_STYLE)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("Cracker › John The Ripper")
        header.setStyleSheet(TOOL_HEADER_STYLE)
        layout.addWidget(header)
        
        # Hash input section
        layout.addWidget(self._create_hash_input_section())
        
        # Configuration section
        layout.addWidget(self._create_config_section())
        
        # Mask input (for mask attack)
        layout.addWidget(self._create_mask_section())
        
        # Advanced options
        layout.addWidget(self._create_advanced_section())
        
        # Command display
        layout.addWidget(self._create_command_section())
        
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
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        return panel
        
    def _create_hash_input_section(self) -> QWidget:
        """Create hash file input section with browse and action buttons."""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(5)
        
        # Label
        label = QLabel("Hash File / Input")
        label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        section_layout.addWidget(label)
        
        # Input row with buttons
        input_row = QHBoxLayout()
        
        # Hash input field
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
        self.hash_input.textChanged.connect(self._update_command)
        
        # Browse button
        browse_btn = QPushButton("📁")
        browse_btn.setFixedSize(36, 36)
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.setToolTip("Browse for hash file")
        browse_btn.clicked.connect(self._browse_hash_file)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 16px;
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: #4A4A4A; }}
            QPushButton:pressed {{ background-color: #2A2A2A; }}
        """)
        
        # Run button
        self.run_button = QPushButton("RUN")
        self.run_button.setCursor(Qt.PointingHandCursor)
        self.run_button.setToolTip("Start cracking")
        self.run_button.setStyleSheet(RUN_BUTTON_STYLE)
        self.run_button.clicked.connect(self._run_crack)
        
        # Stop button
        self.stop_button = QPushButton("■")
        self.stop_button.setCursor(Qt.PointingHandCursor)
        self.stop_button.setToolTip("Stop cracking")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet(STOP_BUTTON_STYLE)
        self.stop_button.clicked.connect(self._stop_crack)
        
        input_row.addWidget(self.hash_input)
        input_row.addWidget(browse_btn)
        input_row.addWidget(self.run_button)
        input_row.addWidget(self.stop_button)
        
        section_layout.addLayout(input_row)
        return section
        
    def _create_config_section(self) -> QWidget:
        """Create configuration section with format, mode, and wordlist."""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(5)
        
        # Label
        label = QLabel("Cracking Configuration")
        label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        section_layout.addWidget(label)
        
        # Config row
        config_row = QHBoxLayout()
        
        # Format
        config_row.addWidget(QLabel("Format:"))
        self.format_combo = StyledComboBox()
        self.format_combo.addItems(sorted(self.FORMAT_MAPPINGS.keys()))
        self.format_combo.setCurrentText("Automatic Detection")
        self.format_combo.currentTextChanged.connect(self._update_command)
        config_row.addWidget(self.format_combo, 1)
        
        config_row.addSpacing(15)
        
        # Attack mode
        config_row.addWidget(QLabel("Mode:"))
        self.attack_mode_combo = StyledComboBox()
        self.attack_mode_combo.addItems([
            "Wordlist (Dictionary)",
            "Incremental (Brute-force)",
            "Single Crack",
            "Mask Attack",
            "External (Custom modes)"
        ])
        self.attack_mode_combo.currentTextChanged.connect(self._update_command)
        config_row.addWidget(self.attack_mode_combo, 1)
        
        config_row.addSpacing(15)
        
        # Wordlist
        config_row.addWidget(QLabel("Dictionary:"))
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
        self.wordlist_input.textChanged.connect(self._update_command)
        config_row.addWidget(self.wordlist_input, 2)
        
        # Wordlist browse button
        wordlist_browse = QPushButton("📁")
        wordlist_browse.setFixedSize(36, 36)
        wordlist_browse.setCursor(Qt.PointingHandCursor)
        wordlist_browse.setToolTip("Browse for wordlist")
        wordlist_browse.clicked.connect(self._browse_wordlist)
        wordlist_browse.setStyleSheet(f"""
            QPushButton {{
                font-size: 16px;
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: #4A4A4A; }}
            QPushButton:pressed {{ background-color: #2A2A2A; }}
        """)
        config_row.addWidget(wordlist_browse)
        
        section_layout.addLayout(config_row)
        return section
        
    def _create_mask_section(self) -> QWidget:
        """Create mask input section for mask attacks."""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(5)
        
        label = QLabel("Mask (for Mask Attack)")
        label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        section_layout.addWidget(label)
        
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
        self.mask_input.textChanged.connect(self._update_command)
        section_layout.addWidget(self.mask_input)
        
        return section
        
    def _create_advanced_section(self) -> QWidget:
        """Create advanced options section."""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(5)
        
        label = QLabel("Advanced Options")
        label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        section_layout.addWidget(label)
        
        options_row = QHBoxLayout()
        

        
        # Rules
        self.rules_check = QCheckBox("Use Rules")
        self.rules_check.stateChanged.connect(self._update_command)
        options_row.addWidget(self.rules_check)
        
        self.rules_input = QLineEdit()
        self.rules_input.setPlaceholderText("Rules file...")
        self.rules_input.setEnabled(False)
        self.rules_input.textChanged.connect(self._update_command)
        self.rules_check.stateChanged.connect(
            lambda: self.rules_input.setEnabled(self.rules_check.isChecked())
        )
        options_row.addWidget(self.rules_input)
        
        options_row.addSpacing(20)
        

        
        options_row.addStretch()
        
        section_layout.addLayout(options_row)
        return section
        
    def _create_command_section(self) -> QWidget:
        """Create command display section."""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(5)
        
        label = QLabel("Command")
        label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        section_layout.addWidget(label)
        
        self.command_display = QLineEdit()
        self.command_display.setReadOnly(False)  # Editable
        self.command_display.setStyleSheet(f"""
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
        section_layout.addWidget(self.command_display)
        
        # Initialize command
        self._update_command()
        
        return section
        
    def _create_output_panel(self) -> QWidget:
        """Create output panel with tabs for console and results."""
        self.tab_widget = QTabWidget()
        
        # Console output tab
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
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Hash", "Username", "Password", "Time"])
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
        
        return self.tab_widget
        
    # ==================== Event Handlers ====================
    
    def _browse_hash_file(self):
        """Browse for hash file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Hash File", "",
            "All Files (*);;Text Files (*.txt);;Hash Files (*.hash)"
        )
        if file_path:
            self.hash_input.setText(file_path)
            
    def _browse_wordlist(self):
        """Browse for wordlist file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Wordlist", "",
            "All Files (*);;Text Files (*.txt);;Wordlist Files (*.lst *.dict)"
        )
        if file_path:
            self.wordlist_input.setText(file_path)
            
    def _update_command(self):
        """Update the command display based on current settings."""
        try:
            hash_input = self.hash_input.text().strip() or "<hash_file>"
            format_name = self.FORMAT_MAPPINGS.get(self.format_combo.currentText(), "auto")
            attack_mode = self.attack_mode_combo.currentText()
            
            cmd_parts = ["john"]
            
            # Format
            if format_name != "auto":
                cmd_parts.append(f"--format={format_name}")
                
            # Attack mode
            if attack_mode == "Wordlist (Dictionary)" and self.wordlist_input.text().strip():
                cmd_parts.append(f"--wordlist={self.wordlist_input.text().strip()}")
            elif attack_mode == "Incremental (Brute-force)":
                cmd_parts.append("--incremental")
            elif attack_mode == "Mask Attack" and self.mask_input.text().strip():
                cmd_parts.append(f"--mask={self.mask_input.text().strip()}")
            elif attack_mode == "Single Crack":
                cmd_parts.append("--single")
            elif attack_mode == "External (Custom modes)":
                cmd_parts.append("--external")
                
            # Rules
            if self.rules_check.isChecked() and self.rules_input.text().strip():
                cmd_parts.append(f"--rules={self.rules_input.text().strip()}")
                

                
            # Hash file
            cmd_parts.append(hash_input)
            
            self.command_display.setText(" ".join(cmd_parts))
            
        except (AttributeError, RuntimeError):
            # Widget doesn't exist or was deleted
            pass
            
    # ==================== Core Functionality ====================
    
    def _run_crack(self):
        """Start the password cracking process."""
        # Validate inputs
        hash_input = self.hash_input.text().strip()
        if not hash_input:
            QMessageBox.warning(self, "No Hash Input", "Please select a hash file or enter a hash.")
            return
            
        attack_mode = self.attack_mode_combo.currentText()
        
        # Validate attack mode requirements
        if attack_mode == "Wordlist (Dictionary)" and not self.wordlist_input.text().strip():
            QMessageBox.warning(self, "No Wordlist", "Please select a wordlist for dictionary attack.")
            return
            
        if attack_mode == "Mask Attack" and not self.mask_input.text().strip():
            QMessageBox.warning(self, "No Mask", "Please specify a mask for mask attack.")
            return
            
        # Handle hash input - file or direct hash
        hash_file_path = self._prepare_hash_file(hash_input)
        if not hash_file_path:
            return
            
        # Validate wordlist exists
        if self.wordlist_input.text().strip() and not os.path.exists(self.wordlist_input.text().strip()):
            QMessageBox.warning(self, "Wordlist Not Found", 
                              f"Wordlist file does not exist: {self.wordlist_input.text().strip()}")
            return
            
        # Clear previous results
        self.output.clear()
        self.results_table.setRowCount(0)
        self._is_stopping = False
        self._original_hashes.clear()
        
        # Create output directory
        self._create_output_directory(hash_input)
        
        # Load hash file to store original hashes
        self._load_original_hashes(hash_file_path)
        
        # Build and execute command
        cmd = self._build_john_command(hash_file_path, attack_mode)
        self._execute_john(cmd, hash_file_path)
        
    def _prepare_hash_file(self, hash_input: str) -> Optional[str]:
        """
        Prepare hash file from input.
        If input is a file path, use it directly.
        If input is a hash string, create temporary file.
        
        Returns:
            Path to hash file, or None on error
        """
        if os.path.exists(hash_input):
            # It's a file
            self._hash_file_path = hash_input
            return hash_input
        else:
            # It's a direct hash - create temp file
            try:
                temp_file = tempfile.NamedTemporaryFile(
                    mode='w', delete=False, suffix='.hash', prefix='john_'
                )
                temp_file.write(hash_input + '\n')
                temp_file.close()
                
                self._temp_hash_file = temp_file.name
                self._hash_file_path = temp_file.name
                
                self._log_info("Created temporary hash file for direct input")
                return temp_file.name
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create temporary hash file: {str(e)}")
                return None
                
    def _create_output_directory(self, hash_input: str):
        """Create organized output directory structure."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get base name
        if os.path.exists(hash_input):
            hash_name = os.path.splitext(os.path.basename(hash_input))[0]
        else:
            hash_name = "hash"
            
        # Create directory: /tmp/Vajra-results/{hash_name}_{timestamp}/Logs/
        base_dir = os.path.join("/tmp", "Vajra-results", f"{hash_name}_{timestamp}")
        self._logs_dir = os.path.join(base_dir, "Logs")
        os.makedirs(self._logs_dir, exist_ok=True)
        
        self._log_info(f"Output directory: {self._logs_dir}")
        
    def _load_original_hashes(self, hash_file_path: str):
        """Load original hashes from file for later display."""
        try:
            with open(hash_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                        
                    # Parse hash format: username:hash or just hash
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) >= 2:
                            username = parts[0]
                            hash_value = line  # Store full line
                            self._original_hashes[username] = hash_value
                    else:
                        # Raw hash without username
                        self._original_hashes['?'] = line
                        
        except Exception as e:
            self._log_error(f"Error loading hashes: {str(e)}")
            
    def _build_john_command(self, hash_file_path: str, attack_mode: str) -> List[str]:
        """Build John the Ripper command based on settings."""
        cmd = ["john"]
        
        # Format
        format_name = self.FORMAT_MAPPINGS.get(self.format_combo.currentText(), "auto")
        if format_name != "auto":
            cmd.append(f"--format={format_name}")
            
        # Attack mode
        if attack_mode == "Wordlist (Dictionary)" and self.wordlist_input.text().strip():
            cmd.append(f"--wordlist={self.wordlist_input.text().strip()}")
        elif attack_mode == "Incremental (Brute-force)":
            cmd.append("--incremental")
        elif attack_mode == "Mask Attack" and self.mask_input.text().strip():
            cmd.append(f"--mask={self.mask_input.text().strip()}")
        elif attack_mode == "Single Crack":
            cmd.append("--single")
        elif attack_mode == "External (Custom modes)":
            cmd.append("--external")
            
        # Rules
        if self.rules_check.isChecked() and self.rules_input.text().strip():
            cmd.append(f"--rules={self.rules_input.text().strip()}")
            
        # Session - Force to logs directory to avoid polluting user folder
        if self._logs_dir:
            session_path = os.path.join(self._logs_dir, "john_session")
            cmd.append(f"--session={session_path}")
        
        # Hash file
        cmd.append(hash_file_path)
        
        return cmd
        
    def _execute_john(self, cmd: List[str], hash_file_path: str):
        """Execute John the Ripper command."""
        self._log_section("Starting John The Ripper")
        self._log_info(f"Hash file: {hash_file_path}")
        self._log_info(f"Format: {self.format_combo.currentText()}")
        self._log_info(f"Attack mode: {self.attack_mode_combo.currentText()}")
        self._log_info(f"Command: {' '.join(cmd)}")
        self.output.append("")
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        # Create worker
        self.worker = ProcessWorker(cmd)
        self.worker.output_ready.connect(self._on_output)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._log_error)
        
        # Update UI state
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # Start
        self.worker.start()
        
    def _on_output(self, line: str):
        """Handle output from John the Ripper process."""
        self.output.append(line)
        
        # Note: We don't parse passwords from live output anymore.
        # We'll use 'john --show' after completion for reliable extraction.
        
    def _on_finished(self):
        """Handle process completion and extract cracked passwords."""
        # Reset UI
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if self._is_stopping:
            self._log_info("Cracking stopped by user")
            return
            
        # Extract passwords using 'john --show'
        self._extract_cracked_passwords()
        
        # Save results
        self._save_results()
        
        # Cleanup temp file if created
        if self._temp_hash_file and os.path.exists(self._temp_hash_file):
            try:
                os.unlink(self._temp_hash_file)
                self._temp_hash_file = None
            except Exception:
                pass
                
        self._log_section("Cracking Complete")
        
    def _extract_cracked_passwords(self):
        """
        Extract cracked passwords using 'john --show' command.
        This is the most reliable method to get results.
        """
        if not self._hash_file_path or not os.path.exists(self._hash_file_path):
            self._log_error("Hash file not found - cannot extract results")
            return
            
        self._log_info("Extracting cracked passwords with 'john --show'...")
        
        try:
            # Build john --show command
            show_cmd = ["john", "--show"]
            
            # Add format if specified
            format_name = self.FORMAT_MAPPINGS.get(self.format_combo.currentText(), "auto")
            if format_name != "auto":
                show_cmd.append(f"--format={format_name}")
                
            show_cmd.append(self._hash_file_path)
            
            # Execute
            result = subprocess.run(
                show_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse output
            cracked_count = 0
            for line in result.stdout.splitlines():
                line = line.strip()
                
                # Skip empty lines and summary lines
                if not line or "password hash" in line.lower():
                    continue
                    
                # Parse: username:password or ?:password
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        username = parts[0].strip()
                        password = parts[1].strip()
                        
                        # Get original hash
                        original_hash = self._original_hashes.get(username, line)
                        
                        # Add to results table
                        self._add_result(
                            original_hash,
                            username if username != '?' else 'N/A',
                            password
                        )
                        cracked_count += 1
                        
            if cracked_count > 0:
                self._log_info(f"Successfully extracted {cracked_count} cracked password(s)")
            else:
                self._log_info("No passwords cracked")
                
        except subprocess.TimeoutExpired:
            self._log_error("Timeout while extracting passwords")
        except Exception as e:
            self._log_error(f"Error extracting passwords: {str(e)}")
            
    def _add_result(self, hash_value: str, username: str, password: str):
        """Add a cracked password to the results table."""
        # Check for duplicates
        for row in range(self.results_table.rowCount()):
            existing_user = self.results_table.item(row, 1)
            existing_pass = self.results_table.item(row, 2)
            
            if (existing_user and existing_pass and
                existing_user.text() == username and
                existing_pass.text() == password):
                return  # Duplicate
                
        # Add new result
        row_count = self.results_table.rowCount()
        self.results_table.insertRow(row_count)
        
        self.results_table.setItem(row_count, 0, QTableWidgetItem(hash_value))
        self.results_table.setItem(row_count, 1, QTableWidgetItem(username))
        self.results_table.setItem(row_count, 2, QTableWidgetItem(password))
        self.results_table.setItem(row_count, 3, 
                                   QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))
        
    def _save_results(self):
        """Save cracked passwords to john.txt file."""
        if not self._logs_dir:
            self._log_error("No output directory - cannot save results")
            return
            
        try:
            results_file = os.path.join(self._logs_dir, "john.txt")
            
            with open(results_file, 'w', encoding='utf-8') as f:
                # Header
                f.write("=" * 80 + "\n")
                f.write("John The Ripper - Cracking Results\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Hash Format: {self.format_combo.currentText()}\n")
                f.write(f"Attack Mode: {self.attack_mode_combo.currentText()}\n")
                
                if self.wordlist_input.text().strip():
                    f.write(f"Wordlist: {self.wordlist_input.text().strip()}\n")
                    
                f.write("\n" + "=" * 80 + "\n")
                f.write("Cracked Accounts\n")
                f.write("=" * 80 + "\n\n")
                
                # Results
                if self.results_table.rowCount() == 0:
                    f.write("No passwords cracked.\n")
                else:
                    for row in range(self.results_table.rowCount()):
                        hash_item = self.results_table.item(row, 0)
                        user_item = self.results_table.item(row, 1)
                        pass_item = self.results_table.item(row, 2)
                        time_item = self.results_table.item(row, 3)
                        
                        if hash_item and user_item and pass_item:
                            f.write(f"Hash:     {hash_item.text()}\n")
                            f.write(f"Username: {user_item.text()}\n")
                            f.write(f"Password: {pass_item.text()}\n")
                            if time_item:
                                f.write(f"Time:     {time_item.text()}\n")
                            f.write("-" * 40 + "\n\n")
                            
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"Total Cracked: {self.results_table.rowCount()}\n")
                f.write("=" * 80 + "\n")
                
            self._log_info(f"Results saved to: {results_file}")
            
        except Exception as e:
            self._log_error(f"Failed to save results: {str(e)}")
            
    def _stop_crack(self):
        """Stop the cracking process."""
        if hasattr(self, 'worker') and self.worker and self.worker.is_running:
            self._is_stopping = True
            self.worker.stop()
            self._log_info("Stopping cracking process...")
            
        # Reset UI
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
    # ==================== Logging Helpers ====================
    
    def _log_info(self, message: str):
        """Log info message to output."""
        self.output.append(f"[INFO] {message}")
        
    def _log_error(self, message: str):
        """Log error message to output."""
        self.output.append(f"[ERROR] {message}")
        
    def _log_section(self, title: str):
        """Log section header to output."""
        self.output.append(f"\n{'=' * 5} {title} {'=' * 5}")
