# =============================================================================
# modules/hashfinder.py
#
# Hash Finder Tool - Hash Type Identification
# =============================================================================

import html
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from ui.styles import (
    RunButton, StopButton, CopyButton,
    StyledLineEdit, StyledLabel, HeaderLabel, OutputView,
    ToolSplitter, OutputHelper, StyledToolView,
    StyledGroupBox
)


class HashFinderTool(ToolBase):
    """Hash Finder tool plugin for identifying hash types."""

    name = "Hash Finder"
    category = ToolCategory.CRACKER

    @property
    def icon(self) -> str:
        return "🔍"

    def get_widget(self, main_window):
        return HashFinderToolView(main_window=main_window)


class HashIdentifier:
    """Hash identification engine - identifies hash types based on length and format."""
    
    def __init__(self):
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
        """Identify hash type."""
        matches = []
        h = hash_str.strip()
        
        # Special prefix patterns
        if h.startswith('{SHA}'):
            return ["SHA-1(Base64), Netscape LDAP SHA"]
        if h.startswith('{SSHA}'):
            return ["SSHA-1(Base64), Netscape LDAP SSHA"]
        if h.startswith('{SSHA256}'):
            return ["SSHA-256(Base64), LDAP"]
        if h.startswith('{SSHA512}'):
            return ["SSHA-512(Base64), LDAP"]
        if h.startswith('$2a$') or h.startswith('$2b$') or h.startswith('$2y$'):
            return ["bcrypt"]
        if h.startswith('$argon2'):
            return ["Argon2"]
        if h.startswith('$scrypt$') or h.startswith('SCRYPT:'):
            return ["scrypt"]
        if 'pbkdf2' in h.lower() or h.startswith('$pbkdf2'):
            if 'sha256' in h.lower():
                return ["PBKDF2-SHA256"]
            elif 'sha512' in h.lower():
                return ["PBKDF2-SHA512"]
            elif 'sha1' in h.lower():
                return ["PBKDF2-SHA1"]
            return ["PBKDF2-SHA256", "PBKDF2-SHA512", "PBKDF2-SHA1"]
        if h.startswith('$1$'):
            return ["MD5(Unix), Cisco-IOS $1$ (MD5)"]
        if h.startswith('$5$'):
            return ["SHA-256(Unix), sha256crypt"]
        if h.startswith('$6$'):
            return ["SHA-512(Unix), sha512crypt"]
        if h.startswith('$apr1$'):
            return ["Apache $apr1$ MD5, md5apr1"]
        if h.startswith('$H$'):
            return ["MD5(phpBB3)"]
        if h.startswith('$P$'):
            return ["MD5(Wordpress)"]
        if h.startswith('sha1$'):
            return ["Django (SHA-1)"]
        if h.startswith('sha256$'):
            return ["Django (SHA-256)"]
        if h.startswith('pbkdf2_sha256$'):
            return ["Django (PBKDF2-SHA256)"]
        if h.startswith('$krb5'):
            return ["Kerberos 5"]
        if h.startswith('*') and len(h) == 41:
            return ["MySQL 160bit - SHA-1(SHA-1($pass))"]
        if h.startswith('WPA*') or 'WPA' in h[:10]:
            return ["WPA-PBKDF2-PMKID+EAPOL"]
        if h.startswith('$RAR3$'):
            return ["RAR3-hp"]
        if h.startswith('$rar5$'):
            return ["RAR5"]
        if h.startswith('$zip'):
            return ["PKZIP"]
        if h.startswith('$office$'):
            return ["MS Office"]
        if h.startswith('$pdf$'):
            return ["PDF"]
        if h.startswith('$7z$'):
            return ["7-Zip"]
        if h.startswith('$veracrypt$') or h.startswith('$truecrypt$'):
            return ["VeraCrypt/TrueCrypt"]
        if h.startswith('$bitlocker$'):
            return ["BitLocker"]
        if h.startswith('$bitcoin$'):
            return ["Bitcoin/Litecoin wallet.dat"]
        if h.startswith('$ethereum$'):
            return ["Ethereum Wallet"]
        if h.startswith('$electrum$'):
            return ["Electrum Wallet"]
        if h.startswith('$blockchain$'):
            return ["Blockchain, My Wallet"]
        if h.startswith('$DCC2$'):
            return ["Domain Cached Credentials 2 (DCC2), MS Cache 2"]
        if h.count('.') == 2 and h.startswith('eyJ'):
            return ["JWT (JSON Web Token)"]
        if h.startswith('$BLAKE2$'):
            return ["BLAKE2b-512"]
        
        # Length-based identification
        if len(h) == 4:
            if not h.isalpha() and h.isalnum():
                matches.append("101020")
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend(["101040", "101060"])
        elif len(h) == 8:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend(["102040", "102060", "102080"])
            if h.isdigit():
                matches.extend(["103040", "103020"])
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.append("102020")
        elif len(h) == 13 and not h.isdigit() and not h.isalpha():
            matches.append("104020")
        elif len(h) == 16:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend(["105060", "105040", "105020"])
        elif len(h) == 32:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend([
                    "106020", "106029", "106040", "106060",
                    "106160", "106180", "106200", "106220", "106080",
                ])
        elif len(h) == 40:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend([
                    "109020", "109040", "109100", "109120", "109080", "109140",
                ])
        elif len(h) == 48:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend(["110040", "110020"])
        elif len(h) == 56:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend(["114020", "114040"])
        elif len(h) == 64:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend([
                    "115020", "115040", "115060", "115080", "115100", "115120",
                ])
        elif len(h) == 80:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend(["118020", "118040"])
        elif len(h) == 96:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend(["119020", "119040"])
        elif len(h) == 128:
            if not h.isdigit() and not h.isalpha() and h.isalnum():
                matches.extend(["122020", "122040", "122060", "122080"])
        
        return matches

    def get_results(self, hash_str):
        """Get identification results with algorithm names."""
        matches = self.identify(hash_str)
        results = []
        
        if not matches:
            return None
        
        matches.sort()
        
        for match_id in matches:
            if match_id in self.algorithms:
                results.append(self.algorithms[match_id])
        
        return results


class HashFinderToolView(StyledToolView, OutputHelper):
    """Hash Finder tool interface."""
    
    tool_name = "Hash Finder"
    tool_category = "CRACKER"

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.identifier = HashIdentifier()
        self._build_ui()

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
        header = HeaderLabel("CRACKER", "Hash Finder")
        control_layout.addWidget(header)

        # Hash Input
        input_group = StyledGroupBox("Hash Input")
        input_layout = QVBoxLayout(input_group)
        
        input_row = QHBoxLayout()
        self.hash_input = StyledLineEdit()
        self.hash_input.setPlaceholderText("Enter hash here (e.g., 5f4dcc3b5aa765d61d8327deb882cf99)")
        self.hash_input.returnPressed.connect(self.identify_hash)

        self.identify_button = RunButton("IDENTIFY")
        self.identify_button.clicked.connect(self.identify_hash)

        self.clear_button = StopButton("CLEAR")
        self.clear_button.setEnabled(True)
        self.clear_button.clicked.connect(self.clear_all)

        input_row.addWidget(self.hash_input, 1) # Expand input
        input_row.addWidget(self.identify_button)
        input_row.addWidget(self.clear_button)
        
        input_layout.addLayout(input_row)
        control_layout.addWidget(input_group)

        control_layout.addStretch()
        splitter.addWidget(control_panel)

        # ==================== OUTPUT AREA ====================
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("Hash Finder results will appear here...")

        splitter.addWidget(self.output)
        splitter.setSizes([200, 600])

        main_layout.addWidget(splitter)

    def clear_all(self):
        self.hash_input.clear()
        self.output.clear()

    def identify_hash(self):
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
                    self._raw(f'<span style="color:#10B981;font-weight:bold;">[+] {html.escape(results[0])}</span>')
                elif len(results) == 2:
                    self._raw('<span style="color:#FACC15;font-weight:bold;">Most Probable:</span>')
                    self._raw(f'<span style="color:#10B981;">[+] {html.escape(results[0])}</span>')
                    self._raw(f'<span style="color:#10B981;">[+] {html.escape(results[1])}</span>')
                else:
                    self._raw('<span style="color:#FACC15;font-weight:bold;">Most Probable:</span>')
                    self._raw(f'<span style="color:#10B981;">[+] {html.escape(results[0])}</span>')
                    self._raw(f'<span style="color:#10B981;">[+] {html.escape(results[1])}</span>')
                    self._raw('<br><span style="color:#FB923C;font-weight:bold;">Other Possibilities:</span>')
                    for algo in results[2:]:
                        self._raw(f'<span style="color:#60A5FA;">[+] {html.escape(algo)}</span>')
                
                self._section("IDENTIFICATION COMPLETE")
                self._info(f"Found {len(results)} possible match{'es' if len(results) != 1 else ''}")
                
        except Exception as e:
            self._error(f"Identification error: {str(e)}")
