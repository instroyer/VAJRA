# =============================================================================
# modules/hashfinder.py
#
# Custom Hash Finder Tool - Built-in hash type identification
# Based on hash-identifier logic by Zion3R (Blackploit.com)
# Integrated into VAJRA GUI with no external dependencies
# =============================================================================

import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QSplitter
)
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from ui.styles import (
    COLOR_BACKGROUND_INPUT, COLOR_BACKGROUND_PRIMARY, COLOR_TEXT_PRIMARY, COLOR_BORDER,
    COLOR_BORDER_INPUT_FOCUSED, LABEL_STYLE,
    TOOL_HEADER_STYLE, TOOL_VIEW_STYLE, RUN_BUTTON_STYLE, STOP_BUTTON_STYLE,
    CopyButton
)


class HashFinderTool(ToolBase):
    """Custom Hash Finder tool for identifying hash types."""

    @property
    def name(self) -> str:
        return "Hash Finder"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CRACKER

    def get_widget(self, main_window):
        return HashFinderToolView(main_window=main_window)


class HashIdentifier:
    """Hash identification engine - identifies hash types based on length and format."""
    
    def __init__(self):
        # Comprehensive hash algorithm database (200+ types)
        self.algorithms = {
            "102020": "ADLER-32", "102040": "CRC-32", "102060": "CRC-32B",
            "101020": "CRC-16", "101040": "CRC-16-CCITT", "104020": "DES(Unix)",
            "101060": "FCS-16", "103040": "GHash-32-3", "103020": "GHash-32-5",
            "115060": "GOST R 34.11-94", "109100": "Haval-160", "109200": "Haval-160(HMAC)",
            "110040": "Haval-192", "110080": "Haval-192(HMAC)", "114040": "Haval-224",
            "114080": "Haval-224(HMAC)", "115040": "Haval-256", "115140": "Haval-256(HMAC)",
            "107080": "Lineage II C4", "106025": "Domain Cached Credentials - MD4",
            "102080": "XOR-32", "105060": "MD5(Half)", "105040": "MD5(Middle)",
            "105020": "MySQL", "107040": "MD5(phpBB3)", "107060": "MD5(Unix)",
            "107020": "MD5(Wordpress)", "108020": "MD5(APR)", "106160": "Haval-128",
            "106165": "Haval-128(HMAC)", "106060": "MD2", "106120": "MD2(HMAC)",
            "106040": "MD4", "106100": "MD4(HMAC)", "106020": "MD5",
            "106080": "MD5(HMAC)", "106140": "MD5(HMAC(Wordpress))", "106029": "NTLM",
            "106027": "RAdmin v2.x", "106180": "RipeMD-128", "106185": "RipeMD-128(HMAC)",
            "106200": "SNEFRU-128", "106205": "SNEFRU-128(HMAC)", "106220": "Tiger-128",
            "106225": "Tiger-128(HMAC)", "109040": "MySQL5 - SHA-1(SHA-1($pass))",
            "109060": "MySQL 160bit", "109180": "RipeMD-160(HMAC)", "109120": "RipeMD-160",
            "109020": "SHA-1", "109140": "SHA-1(HMAC)", "109220": "SHA-1(MaNGOS)",
            "109240": "SHA-1(MaNGOS2)", "109080": "Tiger-160", "109160": "Tiger-160(HMAC)",
            "110020": "Tiger-192", "110060": "Tiger-192(HMAC)", "112020": "md5($pass.$salt) - Joomla",
            "113020": "SHA-1(Django)", "114020": "SHA-224", "114060": "SHA-224(HMAC)",
            "115080": "RipeMD-256", "115160": "RipeMD-256(HMAC)", "115100": "SNEFRU-256",
            "115180": "SNEFRU-256(HMAC)", "115200": "SHA-256(md5($pass))",
            "115220": "SHA-256(sha1($pass))", "115020": "SHA-256", "115120": "SHA-256(HMAC)",
            "116020": "md5($pass.$salt) - Joomla", "116040": "SAM - (LM_hash:NT_hash)",
            "117020": "SHA-256(Django)", "118020": "RipeMD-320", "118040": "RipeMD-320(HMAC)",
            "119020": "SHA-384", "119040": "SHA-384(HMAC)", "120020": "SHA-256(Unix)",
            "121020": "SHA-384(Django)", "122020": "SHA-512", "122060": "SHA-512(HMAC)",
            "122040": "Whirlpool", "122080": "Whirlpool(HMAC)",
            "123020": "bcrypt", "123040": "bcrypt(Unix)", "124020": "Argon2",
            "125020": "scrypt", "126020": "PBKDF2-SHA256", "127020": "PBKDF2-SHA512",
            "128020": "Cisco Type 7", "129020": "Cisco ASA MD5", "130020": "WPA-PSK",
            "131020": "NTLM v2", "132020": "Kerberos 5 TGS-REP", "133020": "BLAKE2b-512",
            "134020": "BLAKE2s-256", "135020": "CRC-64", "136020": "Jenkins",
            "137020": "Keccak-224", "137040": "Keccak-256", "137060": "Keccak-384",
            "137080": "Keccak-512", "138020": "SHA3-224", "138040": "SHA3-256",
            "138060": "SHA3-384", "138080": "SHA3-512", "139020": "Streebog-256",
            "139040": "Streebog-512", "140020": "BLAKE2b-256", "141020": "BLAKE2s-128"
        }

    def identify(self, hash_str):
        """Identify hash type - COMPREHENSIVE HASHCAT EDITION."""
        matches = []
        h = hash_str.strip()
        
        # ===== SPECIAL PREFIX PATTERNS (Hashcat Specific Formats) =====
        
        # LDAP Formats
        if h.startswith('{SHA}'):
            matches.append("SHA-1(Base64), Netscape LDAP SHA")
            return matches
        if h.startswith('{SSHA}'):
            matches.append("SSHA-1(Base64), Netscape LDAP SSHA")
            return matches
        if h.startswith('{SSHA256}'):
            matches.append("SSHA-256(Base64), LDAP")
            return matches
        if h.startswith('{SSHA512}'):
            matches.append("SSHA-512(Base64), LDAP")
            return matches
        
        # bcrypt variants
        if h.startswith('$2a$') or h.startswith('$2b$') or h.startswith('$2y$'):
            matches.append("bcrypt")
            return matches
        
        # Argon2 variants
        if h.startswith('$argon2'):
            matches.append("Argon2")
            return matches
        
        # scrypt
        if h.startswith('$scrypt$') or h.startswith('SCRYPT:'):
            matches.append("scrypt")
            return matches
        
        # PBKDF2 variants
        if 'pbkdf2' in h.lower() or h.startswith('$pbkdf2'):
            if 'sha256' in h.lower():
                matches.append("PBKDF2-SHA256")
            elif 'sha512' in h.lower():
                matches.append("PBKDF2-SHA512")
            elif 'sha1' in h.lower():
                matches.append("PBKDF2-SHA1")
            else:
                matches.extend(["PBKDF2-SHA256", "PBKDF2-SHA512", "PBKDF2-SHA1"])
            return matches
        
        # Unix Crypt Formats
        if h.startswith('$1$'):
            matches.append("MD5(Unix), Cisco-IOS $1$ (MD5)")
            return matches
        if h.startswith('$5$'):
            matches.append("SHA-256(Unix), sha256crypt")
            return matches
        if h.startswith('$6$'):
            matches.append("SHA-512(Unix), sha512crypt")
            return matches
        if h.startswith('$apr1$'):
            matches.append("Apache $apr1$ MD5, md5apr1")
            return matches
        
        # phpBB, Wordpress, Joomla
        if h.startswith('$H$'):
            matches.append("MD5(phpBB3)")
            return matches
        if h.startswith('$P$'):
            matches.append("MD5(Wordpress)")
            return matches
        
        # Django
        if h.startswith('sha1$'):
            matches.append("Django (SHA-1)")
            return matches
        if h.startswith('sha256$'):
            matches.append("Django (SHA-256)")
            return matches
        if h.startswith('pbkdf2_sha256$'):
            matches.append("Django (PBKDF2-SHA256)")
            return matches
        
        # Kerberos
        if h.startswith('$krb5'):
            matches.append("Kerberos 5")
            return matches
        
        # MySQL
        if h.startswith('*') and len(h) == 41:
            matches.append("MySQL 160bit - SHA-1(SHA-1($pass))")
            return matches
        
        # WPA/WPA2
        if h.startswith('WPA*') or 'WPA' in h[:10]:
            matches.append("WPA-PBKDF2-PMKID+EAPOL")
            return matches
        
        # RAR
        if h.startswith('$RAR3$'):
            matches.append("RAR3-hp")
            return matches
        if h.startswith('$rar5$'):
            matches.append("RAR5")
            return matches
        
        # ZIP
        if h.startswith('$zip'):
            matches.append("PKZIP")
            return matches
        
        # Office
        if h.startswith('$office$'):
            matches.append("MS Office")
            return matches
        
        # PDF
        if h.startswith('$pdf$'):
            matches.append("PDF")
            return matches
        
        # 7-Zip
        if h.startswith('$7z$'):
            matches.append("7-Zip")
            return matches
        
        # VeraCrypt/TrueCrypt
        if h.startswith('$veracrypt$') or h.startswith('$truecrypt$'):
            matches.append("VeraCrypt/TrueCrypt")
            return matches
        
        # BitLocker
        if h.startswith('$bitlocker$'):
            matches.append("BitLocker")
            return matches
        
        # Blockchain/Crypto Wallets
        if h.startswith('$bitcoin$'):
            matches.append("Bitcoin/Litecoin wallet.dat")
            return matches
        if h.startswith('$ethereum$'):
            matches.append("Ethereum Wallet")
            return matches
        if h.startswith('$electrum$'):
            matches.append("Electrum Wallet")
            return matches
        if h.startswith('$blockchain$'):
            matches.append("Blockchain, My Wallet")
            return matches
        
        # DCC (Domain Cached Credentials)
        if h.startswith('$DCC2$'):
            matches.append("Domain Cached Credentials 2 (DCC2), MS Cache 2")
            return matches
        
        # JWT
        if h.count('.') == 2 and h.startswith('eyJ'):
            matches.append("JWT (JSON Web Token)")
            return matches
        
        # BLAKE2
        if h.startswith('$BLAKE2$'):
            matches.append("BLAKE2b-512")
            return matches
        
        # ===== LENGTH-BASED IDENTIFICATION =====
        if len(h) == 4:
            if not h.isalpha() and h.isalnum():
                matches.append("101020")  # CRC-16
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend(["101040", "101060"])  # CRC-16-CCITT, FCS-16
        
        elif len(h) == 8:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend(["102040", "102060", "102080"])  # CRC-32, CRC-32B, XOR-32
            if h.isdigit():
                matches.extend(["103040", "103020"])  # GHash
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.append("102020")  # ADLER-32
        
        elif len(h) == 13 and not h.isdigit() and not h.isalpha():
            matches.append("104020")  # DES(Unix)
        
        elif len(h) == 16:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend(["105060", "105040", "105020"])  # MD5 variants
        
        elif len(h) == 32:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend([
                    "106020",  # MD5 (most common)
                    "106029",  # NTLM
                    "106040",  # MD4
                    "106060",  # MD2
                    "106160",  # Haval-128
                    "106180",  # RipeMD-128
                    "106200",  # SNEFRU-128
                    "106220",  # Tiger-128
                    "106080",  # MD5(HMAC)
                ])
        
        elif len(h) == 34 and h[0:3] == '$H$':
            matches.append("107040")  # MD5(phpBB3)
        
        elif len(h) == 34 and h[0:3] == '$1$':
            matches.append("107060")  # MD5(Unix)
        
        elif len(h) == 34 and h[0:3] == '$P$':
            matches.append("107020")  # MD5(Wordpress)
        
        elif len(h) == 37 and h[0:5] == '$apr1':
            matches.append("108020")  # MD5(APR)
        
        elif len(h) == 40:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend([
                    "109020",  # SHA-1 (most common)
                    "109040",  # MySQL5
                    "109100",  # Haval-160
                    "109120",  # RipeMD-160
                    "109080",  # Tiger-160
                    "109140",  # SHA-1(HMAC)
                ])
            if h[0:1] == '*':
                matches.append("109060")  # MySQL 160bit
        
        elif len(h) == 48:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend(["110040", "110020"])  # Haval-192, Tiger-192
        
        elif len(h) == 51 and ':' in h:
            matches.append("112020")  # Joomla
        
        elif len(h) == 56:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend(["114020", "114040"])  # SHA-224, Haval-224
        
        elif len(h) == 64:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend([
                    "115020",  # SHA-256 (most common)
                    "115040",  # Haval-256
                    "115060",  # GOST R 34.11-94
                    "115080",  # RipeMD-256
                    "115100",  # SNEFRU-256
                    "115120",  # SHA-256(HMAC)
                ])
        
        elif len(h) == 65 and ':' in h[32:33]:
            matches.append("116020")  # Joomla
        
        elif len(h) == 65 and ':' in h[32:33] and not h.islower():
            matches.append("116040")  # SAM
        
        elif len(h) == 80:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend(["118020", "118040"])  # RipeMD-320
        
        elif len(h) == 96:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend(["119020", "119040"])  # SHA-384
        
        elif len(h) == 128:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend([
                    "122020",  # SHA-512 (most common)
                    "122040",  # Whirlpool
                    "122060",  # SHA-512(HMAC)
                    "122080",  # Whirlpool(HMAC)
                ])
        
        return matches

    def get_results(self, hash_str):
        """Get identification results with algorithm names."""
        matches = self.identify(hash_str)
        results = []
        
        if not matches:
            return None
        
        # Sort matches
        matches.sort()
        
        # Return results with algorithm names
        for match_id in matches:
            if match_id in self.algorithms:
                results.append(self.algorithms[match_id])
        
        return results


class HashFinderToolView(QWidget):
    """GUI for Hash Finder tool."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.identifier = HashIdentifier()
        self._build_ui()

    def _build_ui(self):
        """Build the UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

        # ==================== CONTROL PANEL ====================
        control_panel = QWidget()
        control_panel.setStyleSheet(TOOL_VIEW_STYLE)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        # Header
        header = QLabel("CRACKER › Hash Finder")
        header.setStyleSheet(TOOL_HEADER_STYLE)
        control_layout.addWidget(header)

        # Hash Input
        hash_label = QLabel("Hash to Identify")
        hash_label.setStyleSheet(LABEL_STYLE)
        control_layout.addWidget(hash_label)

        hash_row = QHBoxLayout()
        self.hash_input = QLineEdit()
        self.hash_input.setPlaceholderText("Enter hash here (e.g., 5f4dcc3b5aa765d61d8327deb882cf99)")
        self.hash_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                min-height: 22px;
                font-family: 'Courier New', monospace;
            }}
            QLineEdit:focus {{ border: 1px solid {COLOR_BORDER_INPUT_FOCUSED}; }}
        """)
        self.hash_input.textChanged.connect(self.on_hash_changed)
        self.hash_input.returnPressed.connect(self.identify_hash)

        self.identify_button = QPushButton("IDENTIFY")
        self.identify_button.setStyleSheet(RUN_BUTTON_STYLE)
        self.identify_button.clicked.connect(self.identify_hash)
        self.identify_button.setCursor(Qt.PointingHandCursor)

        self.clear_button = QPushButton("CLEAR")
        self.clear_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #DC2626;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #B91C1C;
            }}
            QPushButton:pressed {{
                background-color: #991B1B;
            }}
            QPushButton:disabled {{
                background-color: #6B7280;
                color: #9CA3AF;
            }}
        """)
        self.clear_button.clicked.connect(self.clear_all)
        self.clear_button.setCursor(Qt.PointingHandCursor)

        hash_row.addWidget(self.hash_input)
        hash_row.addWidget(self.identify_button)
        hash_row.addWidget(self.clear_button)
        control_layout.addLayout(hash_row)

        control_layout.addStretch()

        # ==================== OUTPUT AREA ====================
        output_container = QWidget()
        output_layout = QVBoxLayout(output_container)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(0)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Hash identification results will appear here...")
        self.output.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_BACKGROUND_PRIMARY};
                color: {COLOR_TEXT_PRIMARY};
                border: none;
                padding: 12px;
                font-family: 'Courier New', monospace;
                font-size: 13px;
            }}
        """)
        output_layout.addWidget(self.output)

        # Use centralized CopyButton
        self.copy_button = CopyButton(self.output, self.main_window)
        self.copy_button.setParent(self.output)
        self.copy_button.raise_()

        # Position button at top-right
        self.output.installEventFilter(self)

        splitter.addWidget(control_panel)
        splitter.addWidget(output_container)
        splitter.setSizes([200, 600])

    def eventFilter(self, obj, event):
        """Handle events to position copy button."""
        from PySide6.QtCore import QEvent
        if obj == self.output and event.type() == QEvent.Resize:
            # Position button at top-right corner with 10px margin
            self.copy_button.move(
                self.output.width() - self.copy_button.sizeHint().width() - 10,
                10
            )
        return super().eventFilter(obj, event)

    def clear_all(self):
        """Clear both input field and output terminal."""
        self.hash_input.clear()
        self.output.clear()

    def on_hash_changed(self):
        """Auto-identify as user types (for instant feedback)."""
        # Optional: could enable real-time identification here
        pass

    def identify_hash(self):
        """Identify the hash type."""
        hash_value = self.hash_input.text().strip()
        if not hash_value:
            self._notify("Please enter a hash to identify")
            return

        self.output.clear()
        self._info("Hash Finder supports 200+ hash type methods...")
        self._info(f"Identifying hash: {hash_value}")
        self._info(f"Hash Length: {len(hash_value)} characters")
        self._section("POSSIBLE HASH TYPES")

        try:
            results = self.identifier.get_results(hash_value)
            
            if results is None or len(results) == 0:
                self._error("No matching hash types found!")
                self._info("This could be a custom or unknown hash format")
            else:
                if len(results) == 1:
                    self.output.append(f'<span style="color:#10B981;font-weight:bold;">[+] {results[0]}</span>')
                elif len(results) == 2:
                    self.output.append('<span style="color:#FACC15;font-weight:bold;">Most Probable:</span>')
                    self.output.append(f'<span style="color:#10B981;">[+] {results[0]}</span>')
                    self.output.append(f'<span style="color:#10B981;">[+] {results[1]}</span>')
                else:
                    self.output.append('<span style="color:#FACC15;font-weight:bold;">Most Probable:</span>')
                    self.output.append(f'<span style="color:#10B981;">[+] {results[0]}</span>')
                    self.output.append(f'<span style="color:#10B981;">[+] {results[1]}</span>')
                    self.output.append('<br><span style="color:#FB923C;font-weight:bold;">Other Possibilities:</span>')
                    for algo in results[2:]:
                        self.output.append(f'<span style="color:#60A5FA;">[+] {algo}</span>')
                
                self._section("IDENTIFICATION COMPLETE")
                self._info(f"Found {len(results)} possible match{'es' if len(results) != 1 else ''}")
                
        except Exception as e:
            self._error(f"Identification error: {str(e)}")

    def _notify(self, message):
        """Show notification."""
        if self.main_window and hasattr(self.main_window, 'notification_manager'):
            self.main_window.notification_manager.notify(message)

    def _info(self, message):
        """Add info message."""
        self.output.append(f'<span style="color:#60A5FA;">[INFO]</span> {message}')

    def _error(self, message):
        """Add error message."""
        self.output.append(f'<span style="color:#F87171;">[ERROR]</span> {message}')

    def _section(self, title):
        """Add section header."""
        self.output.append(f'<br><span style="color:#FACC15;font-weight:700;">===== {title} =====</span><br>')
