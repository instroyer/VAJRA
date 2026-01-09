# =============================================================================
# modules/john.py
#
# John the Ripper Tool Module
# =============================================================================

import os
import shlex
import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog
)

from modules.bases import ToolBase, ToolCategory
from ui.worker import ToolExecutionMixin
from ui.styles import (
    # Widgets
    RunButton, StopButton, BrowseButton,
    StyledLineEdit, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView,
    ToolSplitter, StyledToolView
)


class JohnTool(ToolBase):
    """John the Ripper password cracker integration."""
    
    name = "John The Ripper"
    category = ToolCategory.CRACKER

    @property
    def description(self) -> str:
        return "Fast password cracker, currently available for many flavors of Unix, Windows, DOS, and OpenVMS."
    
    @property
    def icon(self) -> str:
        return "🕵️"
    
    def get_widget(self, main_window):
        return JohnToolView(main_window=main_window)


class JohnToolView(StyledToolView, ToolExecutionMixin):
    """John the Ripper password cracker interface."""
    
    tool_name = "John The Ripper"
    tool_category = "CRACKER"

    HASH_FORMATS = {
        "Auto-Detect": "",
        "MD5": "raw-md5",
        "MD5 (Double)": "raw-md5u",
        "MD4": "raw-md4",
        "SHA1": "raw-sha1",
        "SHA-256": "raw-sha256",
        "SHA-384": "raw-sha384",
        "SHA-512": "raw-sha512",
        "SHA3-256": "dynamic_60",
        "SHA3-512": "dynamic_61",
        "RIPEMD-160": "ripemd-160",
        "Whirlpool": "whirlpool",
        "Tiger": "tiger",
        "GOST": "gost",
        "Haval-256": "haval-256-3",
        "LM": "lm",
        "NTLM": "nt",
        "NetNTLMv2": "netntlmv2",
        "DES (Unix)": "descrypt",
        "MD5 (Unix)": "md5crypt",
        "SHA-256 (Unix)": "sha256crypt",
        "SHA-512 (Unix)": "sha512crypt",
        "Blowfish (bcrypt)": "bcrypt",
        "Sun MD5": "sunmd5",
        "macOS 10.4 (SSHA)": "xsha",
        "macOS 10.7+ (PBKDF2)": "xsha512",
        "MSCASH": "mscash",
        "MSCASH2": "mscash2",
        "Net-LM": "netlm",
        "Net-NTLMv1": "netntlm",
        "MySQL (old)": "mysql",
        "MySQL (SHA1)": "mysql-sha1",
        "PostgreSQL MD5": "postgres",
        "MS SQL 2000": "mssql",
        "MS SQL 2005": "mssql05",
        "MS SQL 2012": "mssql12",
        "Oracle 10": "oracle",
        "Oracle 11": "oracle11",
        "Oracle 12": "oracle12c",
        "Sybase ASE": "sybasease",
        "Django (PBKDF2)": "django",
        "WordPress": "phpass",
        "PHPass (Drupal/WordPress)": "phpass",
        "phpBB3": "phpass",
        "Joomla": "md5crypt",
        "vBulletin": "md5crypt",
        "Mediawiki": "mediawiki",
        "LDAP (SSHA)": "ssha",
        "LDAP (SHA)": "sha",
        "LDAP (MD5)": "ldap-md5",
        "ZIP": "zip",
        "RAR": "rar",
        "RAR5": "rar5",
        "7-Zip": "7z",
        "PDF": "pdf",
        "MS Office": "office",
        "MS Office 2007": "office2007",
        "MS Office 2010": "office2010",
        "MS Office 2013": "office2013",
        "OpenDocument (ODF)": "odf",
        "TrueCrypt": "truecrypt",
        "VeraCrypt": "veracrypt",
        "LUKS": "luks",
        "BitLocker": "bitlocker",
        "WPA-PSK": "wpapsk",
        "IPMI 2.0": "ipmi2",
        "Kerberos 5": "krb5",
        "Kerberos 5 (TGS-REP)": "krb5tgs",
        "SSH (RSA/DSA)": "ssh",
        "OpenSSL (PEM)": "ssh",
        "KeePass": "keepass",
        "1Password": "1password",
        "LastPass": "lastpass",
        "HMAC-MD5": "hmac-md5",
        "HMAC-SHA1": "hmac-sha1",
        "HMAC-SHA256": "hmac-sha256",
        "PBKDF2-HMAC-SHA1": "pbkdf2-hmac-sha1",
        "PBKDF2-HMAC-SHA256": "pbkdf2-hmac-sha256",
        "Argon2": "argon2",
        "scrypt": "scrypt"
    }
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_safe_stop()
        self._build_ui()
        self.update_command()
        
    def _build_ui(self):
        """Build the UI."""
        # setStyleSheet handled by StyledToolView
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = ToolSplitter()
        
        # ==================== CONTROL PANEL ====================
        control_panel = QWidget()
        # Removed legacy style
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)
        
        # Header
        header = HeaderLabel(self.tool_category, self.tool_name)
        control_layout.addWidget(header)
        
        # Hash Input Section
        input_group = StyledGroupBox("📂 Input")
        input_layout = QVBoxLayout(input_group)
        
        input_row = QHBoxLayout()
        input_label = StyledLabel("Hash File:")
        self.hash_input = StyledLineEdit()
        self.hash_input.setPlaceholderText("Select hash file...")
        self.hash_input.textChanged.connect(self.update_command)
        
        browse_btn = BrowseButton()
        browse_btn.clicked.connect(self._browse_hash)
        
        input_row.addWidget(input_label)
        input_row.addWidget(self.hash_input)
        input_row.addWidget(browse_btn)
        input_layout.addLayout(input_row)
        
        control_layout.addWidget(input_group)
        
        # Configuration Section
        config_group = StyledGroupBox("⚙️ Configuration")
        config_layout = QGridLayout(config_group)
        config_layout.setSpacing(10)
        
        # Format
        fmt_label = StyledLabel("Format:")
        self.format_combo = StyledComboBox()
        self.format_combo.addItems(sorted(self.HASH_FORMATS.keys()))
        self.format_combo.setCurrentText("Auto-Detect")
        self.format_combo.currentTextChanged.connect(self.update_command)
        
        # Mode
        mode_label = StyledLabel("Attack Mode:")
        self.mode_combo = StyledComboBox()
        self.mode_combo.addItems([
            "Wordlist",
            "Single Crack",
            "Incremental",
            "External"
        ])
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        
        config_layout.addWidget(fmt_label, 0, 0)
        config_layout.addWidget(self.format_combo, 0, 1)
        config_layout.addWidget(mode_label, 1, 0)
        config_layout.addWidget(self.mode_combo, 1, 1)
        
        # Wordlist row (only for Wordlist mode)
        self.wordlist_label = StyledLabel("Wordlist:")
        self.wordlist_input = StyledLineEdit()
        self.wordlist_input.setPlaceholderText("Select wordlist...")
        self.wordlist_input.textChanged.connect(self.update_command)
        
        self.wl_browse = BrowseButton()
        self.wl_browse.clicked.connect(self._browse_wordlist)
        
        self.wl_container = QWidget()
        wl_layout = QHBoxLayout(self.wl_container)
        wl_layout.setContentsMargins(0, 0, 0, 0)
        wl_layout.addWidget(self.wordlist_label)
        wl_layout.addWidget(self.wordlist_input)
        wl_layout.addWidget(self.wl_browse)
        
        config_layout.addWidget(self.wl_container, 2, 0, 1, 2)
        
        # Rules checkbox
        self.rules_check = StyledCheckBox("Use Rules (--rules)")
        self.rules_check.stateChanged.connect(self.update_command)
        config_layout.addWidget(self.rules_check, 3, 0, 1, 2)
        
        control_layout.addWidget(config_group)
        
        # Advanced Section
        adv_group = StyledGroupBox("🚀 Advanced")
        adv_layout = QGridLayout(adv_group)
        
        show_check = StyledCheckBox("Show Cracked (--show)")
        show_check.stateChanged.connect(self.update_command)
        self.show_check = show_check  # Store reference
        
        self.session_input = StyledLineEdit()
        self.session_input.setPlaceholderText("Session Name (optional)")
        self.session_input.textChanged.connect(self.update_command)
        
        adv_layout.addWidget(show_check, 0, 0)
        adv_layout.addWidget(StyledLabel("Session:"), 0, 1)
        adv_layout.addWidget(self.session_input, 0, 2)
        
        control_layout.addWidget(adv_group)

        # Command Preview
        self.command_input = StyledLineEdit()
        self.command_input.setReadOnly(True)
        self.command_input.setPlaceholderText("Command preview...")
        control_layout.addWidget(self.command_input)

        # Buttons
        btn_layout = QHBoxLayout()
        self.run_button = RunButton("RUN JOHN")
        self.run_button.clicked.connect(self.run_scan)
        self.stop_button = StopButton()
        self.stop_button.clicked.connect(self.stop_scan)
        
        btn_layout.addWidget(self.run_button)
        btn_layout.addWidget(self.stop_button)
        control_layout.addLayout(btn_layout)
        
        control_layout.addStretch()
        splitter.addWidget(control_panel)

        # Output
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("John the Ripper results will appear here...")
        
        splitter.addWidget(self.output)
        splitter.setSizes([450, 350])
        
        main_layout.addWidget(splitter)
        
        # Init
        self._on_mode_changed(self.mode_combo.currentText())

    def _browse_hash(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Hash File")
        if f: self.hash_input.setText(f)

    def _browse_wordlist(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Wordlist")
        if f: self.wordlist_input.setText(f)

    def _on_mode_changed(self, mode):
        is_wordlist = (mode == "Wordlist")
        self.wl_container.setVisible(is_wordlist)
        self.rules_check.setVisible(is_wordlist)
        self.update_command()

    # -------------------------------------------------------------------------
    # Command Builder
    # -------------------------------------------------------------------------

    def build_command(self, preview: bool = False) -> str:
        cmd = ["john"]
        
        # Format
        fmt = self.HASH_FORMATS.get(self.format_combo.currentText(), "")
        if fmt:
            cmd.append(f"--format={fmt}")
            
        # Mode
        mode = self.mode_combo.currentText()
        if mode == "Wordlist":
            wordlist = self.wordlist_input.text().strip()
            if wordlist:
                cmd.append(f"--wordlist={wordlist}")
                if self.rules_check.isChecked():
                    cmd.append("--rules")
            elif not preview:
                 raise ValueError("Wordlist required for Wordlist mode")
            else:
                 cmd.append("--wordlist=<wordlist>")
        elif mode == "Single Crack":
            cmd.append("--single")
        elif mode == "Incremental":
            cmd.append("--incremental")
        elif mode == "External":
            cmd.append("--external:Double") # Default or let user specify? Simplified for now.
            
        # Session
        session = self.session_input.text().strip()
        if session:
            cmd.append(f"--session={session}")
            
        # Show mode?
        if self.show_check and self.show_check.isChecked():
            cmd.append("--show")
            
        # Hash File
        hash_file = self.hash_input.text().strip()
        if not hash_file:
            if preview:
                hash_file = "<hash_file>"
            else:
                raise ValueError("Hash file required")
        
        cmd.append(hash_file)
        
        return " ".join(shlex.quote(x) for x in cmd)

    def update_command(self):
        try:
            cmd_str = self.build_command(preview=True)
            self.command_input.setText(cmd_str)
        except Exception:
            self.command_input.setText("")

    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------

    def run_scan(self):
        try:
            cmd_str = self.build_command(preview=False)
            
            self._info(f"Starting John the Ripper...")
            self._section("JOHN THE RIPPER")
            self._section("Command")
            self._raw(html.escape(cmd_str))
            
            self.start_execution(cmd_str)
            
        except Exception as e:
            self._error(str(e))

    def on_execution_finished(self):
        super().on_execution_finished()
        self._section("Completed")

    def on_new_output(self, line):
        clean = line.strip()
        if clean:
             clean = self.strip_ansi(clean)
             self._raw(html.escape(clean))
