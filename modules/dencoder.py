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
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QComboBox, QSplitter, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from modules.bases import ToolBase, ToolCategory
from ui.styles import (
    TARGET_INPUT_STYLE, COMBO_BOX_STYLE, COLOR_BACKGROUND_INPUT,
    COLOR_TEXT_PRIMARY, COLOR_BORDER, COLOR_BORDER_INPUT_FOCUSED,
    COLOR_SUCCESS, COLOR_ERROR
)


class DencoderTool(ToolBase):
    """Decoder/Encoder tool for various encoding schemes."""

    def __init__(self):
        super().__init__()
        self.name = "Dencoder"
        self.description = "Encode/decode data in various formats (Base64, URL, Hex, HTML, etc.)"
        self.category = ToolCategory.CRACKER
        self.icon = "🔐"  # Lock icon

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

        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Create control panel
        control_panel = QWidget()
        control_panel.setStyleSheet(f"""
            QWidget {{
                background-color: #2A2A2A;
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
        """)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        # Header
        header = QLabel("Cracker › Dencoder")
        header.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        control_layout.addWidget(header)

        # Encoding type selection
        type_group = QGroupBox("Encoding Type")
        type_group.setStyleSheet(f"""
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
        type_layout = QVBoxLayout(type_group)

        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems([
            "Base64 Encode",
            "Base64 Decode",
            "URL Encode",
            "URL Decode",
            "Hex Encode",
            "Hex Decode",
            "HTML Encode",
            "HTML Decode",
            "ROT13 Encode",
            "ROT13 Decode",
            "Binary to Text",
            "Text to Binary"
        ])
        self.encoding_combo.setStyleSheet(COMBO_BOX_STYLE)
        self.encoding_combo.setMinimumHeight(36)
        type_layout.addWidget(self.encoding_combo)

        # Buttons
        button_layout = QHBoxLayout()
        self.encode_button = QPushButton("Process")
        self.encode_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #FF6B35;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: #E55A2B;
            }}
            QPushButton:pressed {{
                background-color: #CC4F26;
            }}
        """)
        self.encode_button.clicked.connect(self._process_text)

        self.clear_button = QPushButton("Clear")
        self.clear_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #DC3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: #C82333;
            }}
            QPushButton:pressed {{
                background-color: #BD2130;
            }}
        """)
        self.clear_button.clicked.connect(self._clear_text)

        button_layout.addWidget(self.encode_button)
        button_layout.addWidget(self.clear_button)
        type_layout.addLayout(button_layout)

        control_layout.addWidget(type_group)

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
        io_layout.addWidget(self.input_text)

        # Output area
        output_label = QLabel("Output:")
        output_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 500;")
        io_layout.addWidget(output_label)

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
        io_layout.addWidget(self.output_text)

        control_layout.addWidget(io_group)

        # Add control panel to splitter
        splitter.addWidget(control_panel)

        # Create output panel (right side)
        output_panel = QWidget()
        output_panel.setStyleSheet(f"background-color: #1E1E1E;")
        output_layout = QVBoxLayout(output_panel)
        output_layout.setContentsMargins(10, 10, 10, 10)

        # Output header
        output_header = QLabel("Processing Log")
        output_header.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px; font-weight: bold;")
        output_layout.addWidget(output_header)

        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 8px;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 11px;
            }}
        """)
        output_layout.addWidget(self.log_output)

        # Add output panel to splitter
        splitter.addWidget(output_panel)

        # Set splitter proportions
        splitter.setSizes([400, 400])

    def _process_text(self):
        """Process the input text based on selected encoding type."""
        input_text = self.input_text.toPlainText().strip()
        if not input_text:
            self._show_error("Please enter some text to process.")
            return

        encoding_type = self.encoding_combo.currentText()

        try:
            result = self._perform_encoding(input_text, encoding_type)
            self.output_text.setPlainText(result)
            self._log_message(f"Successfully processed text using {encoding_type}", "success")
        except Exception as e:
            self._show_error(f"Error processing text: {str(e)}")
            self._log_message(f"Error: {str(e)}", "error")

    def _perform_encoding(self, text, encoding_type):
        """Perform the actual encoding/decoding operation."""
        if encoding_type == "Base64 Encode":
            return base64.b64encode(text.encode('utf-8')).decode('utf-8')
        elif encoding_type == "Base64 Decode":
            return base64.b64decode(text).decode('utf-8')
        elif encoding_type == "URL Encode":
            return urllib.parse.quote(text)
        elif encoding_type == "URL Decode":
            return urllib.parse.unquote(text)
        elif encoding_type == "Hex Encode":
            return binascii.hexlify(text.encode('utf-8')).decode('utf-8')
        elif encoding_type == "Hex Decode":
            return binascii.unhexlify(text).decode('utf-8')
        elif encoding_type == "HTML Encode":
            return html.escape(text)
        elif encoding_type == "HTML Decode":
            return html.unescape(text)
        elif encoding_type == "ROT13 Encode":
            return self._rot13(text)
        elif encoding_type == "ROT13 Decode":
            return self._rot13(text)  # ROT13 is symmetric
        elif encoding_type == "Binary to Text":
            return self._binary_to_text(text)
        elif encoding_type == "Text to Binary":
            return self._text_to_binary(text)
        else:
            raise ValueError(f"Unknown encoding type: {encoding_type}")

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
            # Remove spaces and split into 8-bit chunks
            binary = ''.join(binary.split())
            if len(binary) % 8 != 0:
                raise ValueError("Binary string length must be multiple of 8")
            bytes_data = [binary[i:i+8] for i in range(0, len(binary), 8)]
            text = ''.join(chr(int(b, 2)) for b in bytes_data)
            return text
        except ValueError as e:
            raise ValueError(f"Invalid binary format: {e}")

    def _text_to_binary(self, text):
        """Convert text to binary string."""
        return ' '.join(format(ord(char), '08b') for char in text)

    def _clear_text(self):
        """Clear all input and output fields."""
        self.input_text.clear()
        self.output_text.clear()
        self.log_output.clear()

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

    def _log_message(self, message, msg_type="info"):
        """Log a message to the output panel."""
        color = {
            "success": COLOR_SUCCESS,
            "error": COLOR_ERROR,
            "info": COLOR_TEXT_SECONDARY
        }.get(msg_type, COLOR_TEXT_SECONDARY)

        timestamp = "00:00:00"  # Could add actual timestamp
        log_entry = f"[{timestamp}] {message}"
        self.log_output.append(f'<span style="color: {color};">{log_entry}</span>')</content>
<parameter name="filePath">c:\Users\Legend\Documents\Github\VAJRA---Offensive-Security-Platform\modules\dencoder.py