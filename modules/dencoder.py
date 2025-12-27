# =============================================================================
# modules/dencoder.py
#
# Decoder/Encoder facility similar to Burp Suite's Decoder tab.
# Provides encoding/decoding for various formats commonly used in security testing.
# =============================================================================

import base64
import binascii
import html
import urllib.parse
import hashlib
import codecs
import quopri
import json
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QComboBox, QSplitter, QGroupBox, QMessageBox, QGridLayout, QApplication, QCompleter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from modules.bases import ToolBase, ToolCategory
from ui.styles import (
    TARGET_INPUT_STYLE, COMBO_BOX_STYLE, COLOR_BACKGROUND_INPUT,
    COLOR_TEXT_PRIMARY, COLOR_BORDER, COLOR_BORDER_INPUT_FOCUSED,
    COLOR_SUCCESS, COLOR_ERROR, COLOR_BACKGROUND_BUTTON, COLOR_TEXT_BUTTON,
    StyledComboBox  # Import from centralized styles
)



class DencoderTool(ToolBase):
    """Decoder/Encoder tool for various encoding schemes."""

    @property
    def name(self) -> str:
        return "Dencoder"

    @property
    def description(self) -> str:
        return "Encode/decode data in various formats (Base64, URL, Hex, HTML, etc.)"

    @property
    def category(self):
        return ToolCategory.CRACKER

    @property
    def icon(self) -> str:
        return "🔐"  # Lock icon

    def get_widget(self, main_window: QWidget) -> QWidget:
        """Create the tool view widget."""
        return DencoderToolView(main_window=main_window)


class DencoderToolView(QWidget):
    """UI for the decoder/encoder tool."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setStyleSheet(f"background-color: #1E1E1E;")
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
        header = QLabel("Cracker › Dencoder")
        header.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        control_layout.addWidget(header)

        # Operation selection with buttons all in one line
        operation_layout = QHBoxLayout()

        # Operation label
        operation_label = QLabel("Operation:")
        operation_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500; font-size: 14px;")
        operation_layout.addWidget(operation_label)

        # Single operation dropdown with custom arrow
        self.operation_combo = StyledComboBox()
        self.operation_combo.setEditable(True)
        self.operation_combo.setInsertPolicy(QComboBox.NoInsert)
        self.operation_combo.setPlaceholderText("Search or select operation...")

        operations = [
            "ASCII85 Decode",
            "ASCII85 Encode",
            "Base16 Decode",
            "Base16 Encode",
            "Base32 Decode",
            "Base32 Encode",
            "Base64 Decode",
            "Base64 Encode",
            "Base85 Decode",
            "Base85 Encode",
            "Binary to Text",
            "Caesar Cipher (-3)",
            "Caesar Cipher (+3)",
            "Command Injection Encode",
            "Decimal to Text",
            "Double HTML Decode",
            "Double HTML Encode",
            "Double URL Decode",
            "Double URL Encode",
            "File Inclusion Encode",
            "Hex Decode",
            "Hex Encode",
            "HTML Decode",
            "HTML Encode",
            "JWT Header Decode",
            "JWT Payload Decode",
            "MD5 Hash",
            "Morse Code Decode",
            "Morse Code Encode",
            "Octal to Text",
            "Path Traversal Encode",
            "Quoted Printable Decode",
            "Quoted Printable Encode",
            "ROT13 Encode/Decode",
            "SHA1 Hash",
            "SHA256 Hash",
            "SQL Char Encode",
            "SQL Hex Encode",
            "Template Injection Encode",
            "Text to Binary",
            "Text to Decimal",
            "Text to Octal",
            "Unicode Escape Decode",
            "Unicode Escape Encode",
            "URL Decode",
            "URL Encode",
            "UU Decode",
            "UU Encode",
            "XSS Basic Encode",
            "XSS Double Encode"
        ]

        self.operation_combo.addItems(operations)
        
        # Add completer for filtering search results
        completer = QCompleter(operations, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)  # Match anywhere in the string
        completer.setCompletionMode(QCompleter.PopupCompletion)  # Don't auto-complete, just filter
        
        # COMPLETELY HIDE the completer's popup (prevent small dropdown)
        completer_popup = completer.popup()
        completer_popup.setMaximumHeight(0)  # Hide it completely
        completer_popup.setStyleSheet("QListView { max-height: 0px; min-height: 0px; border: none; }")
        
        self.operation_combo.setCompleter(completer)
        
        # Keep focus in the input while showing dropdown
        self.operation_combo.setInsertPolicy(QComboBox.NoInsert)
        
        # Auto-show dropdown when typing
        def on_text_changed():
            if not self.operation_combo.view().isVisible():
                self.operation_combo.showPopup()
            # Keep focus in the line edit
            self.operation_combo.lineEdit().setFocus()
        
        self.operation_combo.lineEdit().textChanged.connect(on_text_changed)

        self.operation_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 2px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 8px 35px 8px 12px;
                font-size: 14px;
                font-weight: 500;
                min-height: 18px;
            }}
            QComboBox:focus {{
                border: 2px solid {COLOR_BORDER_INPUT_FOCUSED};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
                background: transparent;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLOR_BACKGROUND_INPUT};
                border: 2px solid {COLOR_BORDER};
                border-radius: 6px;
                color: {COLOR_TEXT_PRIMARY};
                selection-background-color: {COLOR_BORDER_INPUT_FOCUSED};
                selection-color: {COLOR_TEXT_PRIMARY};
                padding: 8px;
                font-size: 14px;
                min-width: 350px;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 4px 14px;
                border-radius: 4px;
                min-height: 26px;
                font-size: 14px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: #2D333B;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {COLOR_BORDER_INPUT_FOCUSED};
            }}
            QComboBox:editable {{
                background-color: {COLOR_BACKGROUND_INPUT};
            }}
            QComboBox QLineEdit {{
                background-color: transparent;
                color: {COLOR_TEXT_PRIMARY};
                border: none;
                padding: 0px;
                font-size: 14px;
            }}
            /* Scrollbar styling */
            QComboBox QAbstractItemView::verticalScrollBar {{
                width: 14px;
                background-color: {COLOR_BACKGROUND_INPUT};
                border-radius: 7px;
            }}
            QComboBox QAbstractItemView::verticalScrollBar::handle {{
                background-color: #4A5568;
                border-radius: 7px;
                min-height: 30px;
            }}
            QComboBox QAbstractItemView::verticalScrollBar::handle:hover {{
                background-color: #58A6FF;
            }}
            QComboBox QAbstractItemView::verticalScrollBar::add-line,
            QComboBox QAbstractItemView::verticalScrollBar::sub-line {{
                height: 0px;
            }}
            QComboBox QAbstractItemView::verticalScrollBar::add-page,
            QComboBox QAbstractItemView::verticalScrollBar::sub-page {{
                background: none;
            }}
        """)
        self.operation_combo.setMinimumHeight(38)
        self.operation_combo.setMinimumWidth(220)
        self.operation_combo.setMaxVisibleItems(15)  # Show more items in dropdown
        operation_layout.addWidget(self.operation_combo)

        # Spacer
        operation_layout.addSpacing(20)

        # Process button
        self.process_button = QPushButton("Process")
        self.process_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #FF6B35;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 16px;
                min-height: 18px;
            }}
            QPushButton:hover {{
                background-color: #E55A2B;
            }}
            QPushButton:pressed {{
                background-color: #CC4F26;
            }}
        """)
        self.process_button.clicked.connect(self._process_text)
        operation_layout.addWidget(self.process_button)

        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #DC3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 16px;
                min-height: 18px;
            }}
            QPushButton:hover {{
                background-color: #C82333;
            }}
            QPushButton:pressed {{
                background-color: #BD2130;
            }}
        """)
        self.clear_button.clicked.connect(self._clear_text)
        operation_layout.addWidget(self.clear_button)

        # Add stretch to push everything to the left
        operation_layout.addStretch()

        control_layout.addLayout(operation_layout)

        # Input/Output areas
        io_group = QGroupBox("Input/Output")
        io_group.setStyleSheet(f"""
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
        io_layout = QVBoxLayout(io_group)

        # Input area
        input_label = QLabel("Input:")
        input_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        io_layout.addWidget(input_label)

        # Input container with copy button
        input_container = QWidget()
        input_layout = QGridLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(0)

        self.input_text = QTextEdit()
        self.input_text.setStyleSheet(f"""
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
        self.input_text.setMinimumHeight(100)

        self.input_copy_button = QPushButton("📋")
        self.input_copy_button.setStyleSheet('''
            QPushButton {
                font-size: 18px;
                background-color: transparent;
                border: none;
                padding: 5px;
            }
        ''')
        self.input_copy_button.setCursor(Qt.PointingHandCursor)
        self.input_copy_button.setToolTip("Copy input to clipboard")
        self.input_copy_button.clicked.connect(self._copy_input_to_clipboard)

        input_layout.addWidget(self.input_text, 0, 0)
        input_layout.addWidget(self.input_copy_button, 0, 0, Qt.AlignTop | Qt.AlignRight)
        io_layout.addWidget(input_container)

        # Output area
        output_label = QLabel("Output:")
        output_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        io_layout.addWidget(output_label)

        # Output container with copy button
        output_container = QWidget()
        output_layout = QGridLayout(output_container)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(0)

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
        self.output_text.setMinimumHeight(100)

        self.output_copy_button = QPushButton("📋")
        self.output_copy_button.setStyleSheet('''
            QPushButton {
                font-size: 18px;
                background-color: transparent;
                border: none;
                padding: 5px;
            }
        ''')
        self.output_copy_button.setCursor(Qt.PointingHandCursor)
        self.output_copy_button.setToolTip("Copy output to clipboard")
        self.output_copy_button.clicked.connect(self._copy_output_to_clipboard)

        output_layout.addWidget(self.output_text, 0, 0)
        output_layout.addWidget(self.output_copy_button, 0, 0, Qt.AlignTop | Qt.AlignRight)
        io_layout.addWidget(output_container)

        control_layout.addWidget(io_group)

    def _process_text(self):
        """Process the input text based on selected operation."""
        input_text = self.input_text.toPlainText().strip()
        if not input_text:
            self._show_error("Please enter some text to process.")
            return

        operation_text = self.operation_combo.currentText()

        try:
            result = self._perform_operation(input_text, operation_text)
            self.output_text.setPlainText(result)
        except Exception as e:
            self._show_error(f"Error processing text: {str(e)}")

    def _perform_operation(self, text, operation_text):
        """Perform the actual encoding/decoding operation based on menu selection."""
        if operation_text == "Base64 Encode":
            return base64.b64encode(text.encode('utf-8')).decode('utf-8')
        elif operation_text == "Base64 Decode":
            try:
                return base64.b64decode(text).decode('utf-8')
            except Exception:
                # Try with padding if missing
                missing_padding = len(text) % 4
                if missing_padding:
                    text += '=' * (4 - missing_padding)
                return base64.b64decode(text).decode('utf-8')
        elif operation_text == "Base32 Encode":
            return base64.b32encode(text.encode('utf-8')).decode('utf-8')
        elif operation_text == "Base32 Decode":
            try:
                return base64.b32decode(text).decode('utf-8')
            except Exception:
                # Try with padding if missing
                missing_padding = len(text) % 8
                if missing_padding:
                    text += '=' * (8 - missing_padding)
                return base64.b32decode(text).decode('utf-8')
        elif operation_text == "Base16 Encode":
            return base64.b16encode(text.encode('utf-8')).decode('utf-8')
        elif operation_text == "Base16 Decode":
            # Remove spaces, newlines, and other non-hex characters
            clean_hex = ''.join(c for c in text if c in '0123456789abcdefABCDEF')
            return base64.b16decode(clean_hex).decode('utf-8')
        elif operation_text == "Base85 Encode":
            return base64.b85encode(text.encode('utf-8')).decode('utf-8')
        elif operation_text == "Base85 Decode":
            return base64.b85decode(text).decode('utf-8')
        elif operation_text == "ASCII85 Encode":
            return base64.a85encode(text.encode('utf-8')).decode('utf-8')
        elif operation_text == "ASCII85 Decode":
            return base64.a85decode(text).decode('utf-8')
        elif operation_text == "URL Encode":
            return urllib.parse.quote(text)
        elif operation_text == "URL Decode":
            return urllib.parse.unquote(text)
        elif operation_text == "Double URL Encode":
            return urllib.parse.quote(urllib.parse.quote(text))
        elif operation_text == "Double URL Decode":
            return urllib.parse.unquote(urllib.parse.unquote(text))
        elif operation_text == "Hex Encode":
            return binascii.hexlify(text.encode('utf-8')).decode('utf-8')
        elif operation_text == "Hex Decode":
            # Remove spaces, newlines, and other non-hex characters
            clean_hex = ''.join(c for c in text if c in '0123456789abcdefABCDEF')
            return binascii.unhexlify(clean_hex).decode('utf-8')
        elif operation_text == "HTML Encode":
            return html.escape(text)
        elif operation_text == "HTML Decode":
            return html.unescape(text)
        elif operation_text == "Double HTML Encode":
            return html.escape(html.escape(text))
        elif operation_text == "Double HTML Decode":
            return html.unescape(html.unescape(text))
        elif operation_text == "Quoted Printable Encode":
            return quopri.encodestring(text.encode('utf-8')).decode('utf-8')
        elif operation_text == "Quoted Printable Decode":
            return quopri.decodestring(text.encode('utf-8')).decode('utf-8')
        elif operation_text == "UU Encode":
            return codecs.encode(text.encode('utf-8'), 'uu').decode('utf-8')
        elif operation_text == "UU Decode":
            return codecs.decode(text.encode('utf-8'), 'uu').decode('utf-8')
        elif operation_text == "ROT13 Encode/Decode":
            return self._rot13(text)  # ROT13 is symmetric
        elif operation_text == "Caesar Cipher (+3)":
            return self._caesar_cipher(text, 3)
        elif operation_text == "Caesar Cipher (-3)":
            return self._caesar_cipher(text, -3)
        elif operation_text == "Morse Code Encode":
            return self._text_to_morse(text)
        elif operation_text == "Morse Code Decode":
            return self._morse_to_text(text)
        elif operation_text == "Text to Binary":
            return self._text_to_binary(text)
        elif operation_text == "Binary to Text":
            return self._binary_to_text(text)
        elif operation_text == "Text to Decimal":
            return self._text_to_decimal(text)
        elif operation_text == "Decimal to Text":
            return self._decimal_to_text(text)
        elif operation_text == "Text to Octal":
            return self._text_to_octal(text)
        elif operation_text == "Octal to Text":
            return self._octal_to_text(text)
        elif operation_text == "Unicode Escape Encode":
            return codecs.encode(text, 'unicode_escape').decode('utf-8')
        elif operation_text == "Unicode Escape Decode":
            return codecs.decode(text, 'unicode_escape')
        elif operation_text == "JWT Header Decode":
            return self._jwt_header_decode(text)
        elif operation_text == "JWT Payload Decode":
            return self._jwt_payload_decode(text)
        elif operation_text == "SQL Hex Encode":
            return self._sql_hex_encode(text)
        elif operation_text == "SQL Char Encode":
            return self._sql_char_encode(text)
        elif operation_text == "XSS Basic Encode":
            return self._xss_basic_encode(text)
        elif operation_text == "XSS Double Encode":
            return self._xss_double_encode(text)
        elif operation_text == "Command Injection Encode":
            return self._command_injection_encode(text)
        elif operation_text == "Path Traversal Encode":
            return self._path_traversal_encode(text)
        elif operation_text == "File Inclusion Encode":
            return self._file_inclusion_encode(text)
        elif operation_text == "Template Injection Encode":
            return self._template_injection_encode(text)
        elif operation_text == "MD5 Hash":
            return hashlib.md5(text.encode('utf-8')).hexdigest()
        elif operation_text == "SHA1 Hash":
            return hashlib.sha1(text.encode('utf-8')).hexdigest()
        elif operation_text == "SHA256 Hash":
            return hashlib.sha256(text.encode('utf-8')).hexdigest()
        else:
            raise ValueError(f"Unknown operation: {operation_text}")

    def _rot13(self, text):
        """Apply ROT13 encoding/decoding."""
        result = []
        for char in text:
            if 'a' <= char <= 'z':
                result.append(chr((ord(char) - ord('a') + 13) % 26 + ord('a')))
            elif 'A' <= char <= 'Z':
                result.append(chr((ord(char) - ord('A') + 13) % 26 + ord('A')))
            else:
                result.append(char)
        return ''.join(result)

    def _binary_to_text(self, binary):
        """Convert binary string to text."""
        try:
            # Remove spaces, newlines, and any non-binary characters
            clean_binary = ''.join(c for c in binary if c in '01')
            if len(clean_binary) % 8 != 0:
                raise ValueError("Binary string length must be multiple of 8")
            bytes_data = [clean_binary[i:i+8] for i in range(0, len(clean_binary), 8)]
            text = ''.join(chr(int(b, 2)) for b in bytes_data)
            return text
        except ValueError as e:
            raise ValueError(f"Invalid binary format: {e}")

    def _text_to_binary(self, text):
        """Convert text to binary string."""
        return ' '.join(format(ord(char), '08b') for char in text)

    def _caesar_cipher(self, text, shift):
        """Apply Caesar cipher with given shift."""
        result = []
        for char in text:
            if char.isalpha():
                # Determine the base (A or a)
                base = ord('A') if char.isupper() else ord('a')
                # Shift the character and wrap around
                result.append(chr((ord(char) - base + shift) % 26 + base))
            else:
                result.append(char)
        return ''.join(result)

    def _text_to_morse(self, text):
        """Convert text to Morse code."""
        morse_dict = {
            'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
            'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
            'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
            'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
            'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
            'Z': '--..', '0': '-----', '1': '.----', '2': '..---', '3': '...--',
            '4': '....-', '5': '.....', '6': '-....', '7': '--...', '8': '---..',
            '9': '----.', '.': '.-.-.-', ',': '--..--', '?': '..--..', "'": '.----.',
            '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-', '&': '.-...',
            ':': '---...', ';': '-.-.-.', '=': '-...-', '+': '.-.-.', '-': '-....-',
            '_': '..--.-', '"': '.-..-.', '$': '...-..-', '@': '.--.-.',
            ' ': '/'
        }

        result = []
        for char in text.upper():
            if char in morse_dict:
                result.append(morse_dict[char])
            else:
                result.append(char)  # Keep unknown characters as-is

        return ' '.join(result)

    def _morse_to_text(self, morse):
        """Convert Morse code to text."""
        morse_dict = {
            '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E',
            '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J',
            '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O',
            '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T',
            '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X', '-.--': 'Y',
            '--..': 'Z', '-----': '0', '.----': '1', '..---': '2', '...--': '3',
            '....-': '4', '.....': '5', '-....': '6', '--...': '7', '---..': '8',
            '----.': '9', '.-.-.-': '.', '--..--': ',', '..--..': '?', '.----.': "'",
            '-.-.--': '!', '-..-.': '/', '-.--.': '(', '-.--.-': ')', '.-...': '&',
            '---...': ':', '-.-.-.': ';', '-...-': '=', '.-.-.': '+', '-....-': '-',
            '..--.-': '_', '.-..-.': '"', '...-..-': '$', '.--.-.': '@'
        }

        # Split by spaces and slashes (word separators)
        words = morse.replace('/', ' / ').split()
        result = []

        for word in words:
            if word == '/':
                result.append(' ')
            else:
                letters = word.split()
                for letter in letters:
                    if letter in morse_dict:
                        result.append(morse_dict[letter])
                    else:
                        result.append('?')  # Unknown Morse code

        return ''.join(result)

    def _text_to_decimal(self, text):
        """Convert text to decimal representation."""
        return ' '.join(str(ord(char)) for char in text)

    def _decimal_to_text(self, decimal):
        """Convert decimal representation to text."""
        try:
            # Split by spaces and convert each decimal number to character
            decimals = decimal.strip().split()
            result = []
            for dec in decimals:
                if dec.isdigit():
                    result.append(chr(int(dec)))
                else:
                    result.append(dec)  # Keep non-numeric as-is
            return ''.join(result)
        except (ValueError, OverflowError):
            raise ValueError("Invalid decimal format")

    def _text_to_octal(self, text):
        """Convert text to octal representation."""
        return ' '.join(format(ord(char), '03o') for char in text)

    def _octal_to_text(self, octal):
        """Convert octal representation to text."""
        try:
            # Split by spaces and convert each octal number to character
            octals = octal.strip().split()
            result = []
            for oct_val in octals:
                if oct_val and all(c in '01234567' for c in oct_val):
                    result.append(chr(int(oct_val, 8)))
                else:
                    result.append(oct_val)  # Keep invalid octal as-is
            return ''.join(result)
        except (ValueError, OverflowError):
            raise ValueError("Invalid octal format")

    def _jwt_header_decode(self, jwt_token):
        """Decode JWT header (first part before first dot)."""
        try:
            parts = jwt_token.split('.')
            if len(parts) >= 1:
                # Add padding if needed
                header_b64 = parts[0] + '=' * (4 - len(parts[0]) % 4)
                header_json = base64.urlsafe_b64decode(header_b64)
                return json.loads(header_json.decode('utf-8'))
            else:
                raise ValueError("Invalid JWT format")
        except Exception as e:
            raise ValueError(f"JWT header decode failed: {e}")

    def _jwt_payload_decode(self, jwt_token):
        """Decode JWT payload (second part between dots)."""
        try:
            parts = jwt_token.split('.')
            if len(parts) >= 2:
                # Add padding if needed
                payload_b64 = parts[1] + '=' * (4 - len(parts[1]) % 4)
                payload_json = base64.urlsafe_b64decode(payload_b64)
                return json.loads(payload_json.decode('utf-8'))
            else:
                raise ValueError("Invalid JWT format")
        except Exception as e:
            raise ValueError(f"JWT payload decode failed: {e}")

    def _sql_hex_encode(self, text):
        """Encode text as SQL hex values (0x... format)."""
        hex_string = binascii.hexlify(text.encode('utf-8')).decode('utf-8')
        return f"0x{hex_string}"

    def _sql_char_encode(self, text):
        """Encode text as SQL CHAR() function calls."""
        chars = []
        for char in text:
            chars.append(f"CHAR({ord(char)})")
        return '+'.join(chars)

    def _xss_basic_encode(self, text):
        """Basic XSS encoding using HTML entities and JavaScript escaping."""
        # HTML encode
        encoded = html.escape(text)
        # Add JavaScript-style escaping
        encoded = encoded.replace('"', '\\"').replace("'", "\\'")
        return encoded

    def _xss_double_encode(self, text):
        """Double HTML encode for XSS bypass attempts."""
        return html.escape(html.escape(text))

    def _command_injection_encode(self, text):
        """Encode for command injection (semicolon, pipe, backtick escaping)."""
        # Escape common command injection characters
        encoded = text.replace(';', '\\;')
        encoded = encoded.replace('|', '\\|')
        encoded = encoded.replace('`', '\\`')
        encoded = encoded.replace('$', '\\$')
        encoded = encoded.replace('(', '\\(')
        encoded = encoded.replace(')', '\\)')
        return encoded

    def _path_traversal_encode(self, text):
        """Encode for path traversal attacks (../ encoding)."""
        # Encode dots and slashes
        encoded = text.replace('../', '%2e%2e%2f')
        encoded = encoded.replace('..\\', '%2e%2e%5c')
        encoded = encoded.replace('/', '%2f')
        encoded = encoded.replace('\\', '%5c')
        return encoded

    def _file_inclusion_encode(self, text):
        """Encode for file inclusion attacks (null bytes, wrappers)."""
        # Add null byte termination
        encoded = text + '\x00'
        # Base64 encode for data wrapper
        encoded = f"data:text/plain;base64,{base64.b64encode(text.encode('utf-8')).decode('utf-8')}"
        return encoded

    def _template_injection_encode(self, text):
        """Encode for template injection attacks (common template syntax)."""
        # Escape common template injection characters
        encoded = text.replace('{{', '\\{\\{')
        encoded = encoded.replace('}}', '\\}\\}')
        encoded = encoded.replace('${', '\\$\\{')
        encoded = encoded.replace('<%', '<\\%')
        encoded = encoded.replace('%>', '%\\>')
        return encoded

    def _clear_text(self):
        """Clear all input and output fields."""
        self.input_text.clear()
        self.output_text.clear()

    def _copy_input_to_clipboard(self):
        """Copy input text to clipboard."""
        input_text = self.input_text.toPlainText()
        if input_text.strip():
            QApplication.clipboard().setText(input_text)

    def _copy_output_to_clipboard(self):
        """Copy output text to clipboard."""
        output_text = self.output_text.toPlainText()
        if output_text.strip():
            QApplication.clipboard().setText(output_text)

    def _show_error(self, message):
        """Show an error message dialog."""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: #1E1E1E;
                color: {COLOR_TEXT_PRIMARY};
            }}
            QMessageBox QLabel {{
                color: {COLOR_TEXT_PRIMARY};
            }}
            QMessageBox QPushButton {{
                background-color: {COLOR_BACKGROUND_BUTTON};
                color: {COLOR_TEXT_BUTTON};
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }}
        """)
        msg_box.exec()

    def _show_info(self, message):
        """Show an info message dialog."""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("Info")
        msg_box.setText(message)
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: #1E1E1E;
                color: {COLOR_TEXT_PRIMARY};
            }}
            QMessageBox QLabel {{
                color: {COLOR_TEXT_PRIMARY};
            }}
            QMessageBox QPushButton {{
                background-color: {COLOR_BACKGROUND_BUTTON};
                color: {COLOR_TEXT_BUTTON};
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }}
        """)
        msg_box.exec()
