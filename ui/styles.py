
# =============================================================================
# ui/styles.py
#
# Centralized stylesheet and custom styled widgets for the application.
# =============================================================================

from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtGui import QFont

# --- Color Palette (VS Code Dark+ Theme inspired) ---
COLOR_BACKGROUND_PRIMARY = "#1E1E1E"      # Editor background
COLOR_BACKGROUND_SECONDARY = "#1C1C1C"    # Side bar background
COLOR_BACKGROUND_INPUT = "#3C3C3C"        # Input field background
COLOR_BACKGROUND_BUTTON = "#0E639C"       # Primary button background
COLOR_BACKGROUND_BUTTON_HOVER = "#007ACC"   # Button background on hover
COLOR_BACKGROUND_BUTTON_DANGER = "#C93633"
COLOR_BACKGROUND_BUTTON_DANGER_HOVER = "#DA3633"

COLOR_BORDER = "#333333"
COLOR_BORDER_INPUT_FOCUSED = "#007ACC"

COLOR_TEXT_PRIMARY = "#D4D4D4"            # Primary text color
COLOR_TEXT_SECONDARY = "#8B8B8B"          # Lighter text for placeholders/labels
COLOR_TEXT_BUTTON = "#FFFFFF"

# --- Semantic Colors ---
COLOR_SUCCESS = "#28A745"
COLOR_WARNING = "#FFC107"
COLOR_ERROR = "#DC3545"
COLOR_INFO = "#17A2B8"

# --- Font ---
FONT_FAMILY_UI = "Segoe UI, Arial, sans-serif"
FONT_FAMILY_MONO = "Consolas, 'Courier New', monospace"


# =============================================================================
# STYLESHEET DEFINITIONS
# =============================================================================

# --- Main Application Window ---
MAIN_WINDOW_STYLE = f"""
    background-color: {COLOR_BACKGROUND_PRIMARY};
"""

# --- Tool View Container ---
TOOL_VIEW_STYLE = f"""
    background-color: {COLOR_BACKGROUND_SECONDARY};
    border-right: 1px solid {COLOR_BORDER};
"""

# --- General Widget Styles ---
TOOL_HEADER_STYLE = f"""
    font-size: 15px;
    font-weight: 600;
    color: {COLOR_TEXT_PRIMARY};
    padding: 10px;
    background-color: {COLOR_BACKGROUND_SECONDARY};
    border-bottom: 1px solid {COLOR_BORDER};
"""

LABEL_STYLE = f"""
    color: {COLOR_TEXT_SECONDARY};
    font-size: 13px;
    font-weight: 600;
"""

# --- Input Fields ---
TARGET_INPUT_STYLE = f"""
    QLineEdit {{
        background-color: {COLOR_BACKGROUND_INPUT};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        padding: 8px;
        font-size: 14px;
        font-family: {FONT_FAMILY_MONO};
    }}
    QLineEdit:focus {{
        border: 1px solid {COLOR_BORDER_INPUT_FOCUSED};
    }}
"""

# --- Buttons ---
RUN_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLOR_BACKGROUND_BUTTON};
        color: {COLOR_TEXT_BUTTON};
        font-weight: 600;
        border-radius: 4px;
        padding: 10px 16px;
        border: none;
    }}
    QPushButton:hover {{
        background-color: {COLOR_BACKGROUND_BUTTON_HOVER};
    }}
    QPushButton:disabled {{
        background-color: {COLOR_BACKGROUND_INPUT};
        color: {COLOR_TEXT_SECONDARY};
    }}
"""

STOP_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLOR_BACKGROUND_BUTTON_DANGER};
        color: {COLOR_TEXT_BUTTON};
        font-size: 16px;
        font-weight: 900;
        border-radius: 4px;
        padding: 8px 12px;
        border: none;
    }}
    QPushButton:hover {{
        background-color: {COLOR_BACKGROUND_BUTTON_DANGER_HOVER};
    }}
    QPushButton:disabled {{
        background-color: {COLOR_BACKGROUND_INPUT};
        color: {COLOR_TEXT_SECONDARY};
    }}
"""

# --- Output Area ---
OUTPUT_TEXT_EDIT_STYLE = f"""
    QPlainTextEdit {{
        background-color: {COLOR_BACKGROUND_PRIMARY};
        color: {COLOR_TEXT_PRIMARY};
        border: none;
        padding: 12px;
        font-family: {FONT_FAMILY_MONO};
        font-size: 13px;
    }}
"""

# --- Other Widgets ---
COMBO_BOX_STYLE = f"""
    QComboBox {{
        background-color: {COLOR_BACKGROUND_INPUT};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        padding: 8px;
    }}
    QComboBox::drop-down {{
        border: none;
    }}
    QComboBox::down-arrow {{
        image: url(assets/icons/chevron-down.svg); 
        width: 16px;
        height: 16px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {COLOR_BACKGROUND_INPUT};
        border: 1px solid {COLOR_BORDER};
        color: {COLOR_TEXT_PRIMARY};
    }}
"""

DIVIDER_STYLE = f"border-bottom: 1px solid {COLOR_BORDER};"

# --- Main Window Top Bar / Tabs ---
TAB_WIDGET_STYLE = f"""
    QTabWidget::pane {{
        border: none;
        background-color: {COLOR_BACKGROUND_PRIMARY};
    }}
    QTabBar::tab {{
        background: {COLOR_BACKGROUND_PRIMARY};
        color: {COLOR_TEXT_SECONDARY};
        padding: 8px 20px;
        border: 1px solid {COLOR_BORDER};
        border-bottom: none; 
    }}
    QTabBar::tab:selected {{
        background: {COLOR_BACKGROUND_SECONDARY};
        color: {COLOR_TEXT_PRIMARY};
    }}
    QTabBar::tab:hover {{
        color: {COLOR_TEXT_PRIMARY};
    }}
    QTabBar::close-button {{
        padding: 2px;
    }}
    QTabBar::close-button:hover {{
        background-color: #333;
    }}
"""


# =============================================================================
# STYLED WIDGETS
# =============================================================================

class PlainTextOutput(QPlainTextEdit):
    """A styled, read-only text area for displaying logs and output."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont(FONT_FAMILY_MONO, 10))
        self.setStyleSheet(f'''
            QPlainTextEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 10px;
            }}
        ''')

    def append_text(self, text: str):
        """Appends plain text to the output, ensuring it scrolls to the end."""
        self.appendPlainText(text)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def append_html(self, html: str):
        """Appends HTML formatted text to the output, ensuring it scrolls to the end."""
        self.appendHtml(html)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def clear_output(self):
        """Clears the entire text area."""
        self.clear()
