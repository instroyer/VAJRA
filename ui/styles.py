# =============================================================================
# ui/styles.py
#
# VAJRA-OSP Unified Style System
# Single source of truth for all UI components and styles
#
# USAGE: Import needed widgets directly
#   from ui.styles import RunButton, StyledLineEdit, SafeStop, OutputHelper
#
# =============================================================================

import os
from PySide6.QtCore import Qt, QSize, QRect, QPoint, QEvent
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPolygon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QSplitter, QSizePolicy, QSpinBox,
    QComboBox, QTextEdit, QApplication, QCheckBox, QGroupBox,
    QTabWidget, QRadioButton
)


# =============================================================================
# SECTION 1: CORE CONSTANTS
# =============================================================================

# Fonts
FONT_FAMILY_UI = "Segoe UI, Arial, sans-serif"
FONT_FAMILY_MONO = "Consolas, 'Courier New', monospace"
FONT_SIZE = "15px"

# Base Colors
COLOR_BACKGROUND_PRIMARY = "#0f0f0f"
COLOR_BACKGROUND_SECONDARY = "#18181b"
COLOR_BACKGROUND_INPUT = "#252525"

# Text Colors
COLOR_TEXT_PRIMARY = "#FFFFFF"
COLOR_TEXT_SECONDARY = "#9ca3af"

# Border Colors
COLOR_BORDER = "#27272a"
COLOR_BORDER_FOCUSED = "transparent"  # Removed orange color - no focus borders!

# Accent Colors
COLOR_ACCENT = "#f97316"
COLOR_ACCENT_HOVER = "#fb923c"

# Button Colors
COLOR_BUTTON_DANGER = "#ef4444"
COLOR_BUTTON_DANGER_HOVER = "#f87171"
COLOR_BTN_PRIMARY = "#3b82f6"
COLOR_BTN_PRIMARY_HOVER = "#2563eb"

# Semantic Colors (for output messages)
COLOR_SUCCESS = "#10B981"
COLOR_WARNING = "#FACC15"
COLOR_ERROR = "#F87171"
COLOR_INFO = "#60A5FA"


# =============================================================================
# SECTION 2: LEGACY STYLE STRINGS (for backward compatibility)
# These will be slowly phased out as tools migrate to widget classes
# =============================================================================

# Keep these for any tools that still need them during transition
TOOL_VIEW_STYLE = f"""
    QWidget {{
        background-color: {COLOR_BACKGROUND_PRIMARY};
        outline: none;
    }}
    QWidget:focus {{
        outline: none;
    }}
"""

TOOL_HEADER_STYLE = f"""
    font-size: 20px;
    font-weight: bold;
    font-family: {FONT_FAMILY_UI};
    color: {COLOR_TEXT_PRIMARY};
    padding: 10px;
    background-color: {COLOR_BACKGROUND_SECONDARY};
    border-bottom: 1px solid {COLOR_BORDER};
"""

# Legacy style strings - keep for compatibility
RUN_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE};
        font-weight: 600;
        font-family: {FONT_FAMILY_UI};
        border-radius: 4px;
        padding: 10px 16px;
        border: none;
    }}
    QPushButton:hover {{
        background-color: {COLOR_ACCENT_HOVER};
    }}
    QPushButton:disabled {{
        background-color: {COLOR_BACKGROUND_INPUT};
        color: {COLOR_TEXT_SECONDARY};
    }}
"""

STOP_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLOR_BUTTON_DANGER};
        color: {COLOR_TEXT_PRIMARY};
        font-size: 16px;
        font-weight: 900;
        border-radius: 4px;
        padding: 8px 12px;
        border: none;
    }}
    QPushButton:hover {{
        background-color: {COLOR_BUTTON_DANGER_HOVER};
    }}
    QPushButton:disabled {{
        background-color: {COLOR_BACKGROUND_INPUT};
        color: {COLOR_TEXT_SECONDARY};
    }}
"""

COPY_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLOR_BACKGROUND_SECONDARY};
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE};
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        padding: 6px;
    }}
    QPushButton:hover {{
        background-color: {COLOR_BACKGROUND_INPUT};
        border: 1px solid {COLOR_ACCENT};
    }}
"""

GROUPBOX_STYLE = f"""
    QGroupBox {{
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE};
        font-family: {FONT_FAMILY_UI};
        font-weight: bold;
        border: 1px solid {COLOR_BORDER};
        border-radius: 6px;
        margin-top: 10px;
        padding-top: 10px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        left: 10px;
    }}
"""

SPINBOX_STYLE = f"""
    QSpinBox {{
        background-color: {COLOR_BACKGROUND_INPUT};
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE};
        font-family: {FONT_FAMILY_UI};
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        padding: 4px 24px 4px 8px;
        min-width: 50px;
    }}
    QSpinBox:focus {{
        border: 1px solid {COLOR_BORDER_FOCUSED};
    }}
    QSpinBox::up-button {{
        subcontrol-origin: border;
        subcontrol-position: center right;
        width: 12px;
        height: 100%;
        right: 0px;
        border: none;
        border-left: 1px solid {COLOR_BORDER};
        background: transparent;
    }}
    QSpinBox::up-button:hover {{
        background-color: rgba(255, 255, 255, 0.08);
    }}
    QSpinBox::up-arrow {{
        width: 0; height: 0;
        border-top: 4px solid transparent;
        border-bottom: 4px solid transparent;
        border-left: 5px solid {COLOR_TEXT_SECONDARY};
    }}
    QSpinBox::up-arrow:hover {{
        border-left: 5px solid {COLOR_TEXT_PRIMARY};
    }}
    QSpinBox::down-button {{
        subcontrol-origin: border;
        subcontrol-position: center right;
        width: 12px;
        height: 100%;
        right: 12px;
        border: none;
        border-left: 1px solid {COLOR_BORDER};
        background: transparent;
    }}
    QSpinBox::down-button:hover {{
        background-color: rgba(255, 255, 255, 0.08);
    }}
    QSpinBox::down-arrow {{
        width: 0; height: 0;
        border-top: 4px solid transparent;
        border-bottom: 4px solid transparent;
        border-right: 5px solid {COLOR_TEXT_SECONDARY};
    }}
    QSpinBox::down-arrow:hover {{
        border-right: 5px solid {COLOR_TEXT_PRIMARY};
    }}
"""



COMBO_BOX_STYLE = f"""
    QComboBox {{
        background-color: {COLOR_BACKGROUND_INPUT};
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE};
        font-family: {FONT_FAMILY_UI};
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        padding: 6px;
        padding-right: 20px;
    }}
    QComboBox:focus {{
        border-color: {COLOR_BORDER_FOCUSED};
    }}
    QComboBox::drop-down {{
        border: none;
    }}
"""

CHECKBOX_STYLE = f"""
    QCheckBox {{
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE};
        font-family: {FONT_FAMILY_UI};
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {COLOR_BORDER};
        border-radius: 3px;
        background-color: {COLOR_BACKGROUND_INPUT};
    }}
    QCheckBox::indicator:checked {{
        background-color: {COLOR_ACCENT};
        border: 1px solid {COLOR_ACCENT};
    }}
"""

RADIO_BUTTON_STYLE = f"""
    QRadioButton {{
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE};
        font-family: {FONT_FAMILY_UI};
        outline: none;
        border: none;
    }}
    QRadioButton:focus {{
        outline: none;
        border: none;
    }}
    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {COLOR_BORDER};
        border-radius: 9px;
        background-color: {COLOR_BACKGROUND_INPUT};
    }}
    QRadioButton::indicator:checked {{
        background-color: {COLOR_ACCENT};
        border: 2px solid {COLOR_ACCENT};
    }}
"""

LABEL_STYLE = f"""
    color: {COLOR_TEXT_PRIMARY};
    font-size: {FONT_SIZE};
    font-weight: 500;
    font-family: {FONT_FAMILY_UI};
"""

TARGET_INPUT_STYLE = f"""
    QLineEdit {{
        background-color: {COLOR_BACKGROUND_INPUT};
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE};
        font-family: {FONT_FAMILY_MONO};
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        padding: 8px;
    }}
    QLineEdit:focus {{
        border: 1px solid {COLOR_BORDER_FOCUSED};
    }}
"""

OUTPUT_TEXT_EDIT_STYLE = f"""
    QTextEdit {{
        background-color: {COLOR_BACKGROUND_PRIMARY};
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE};
        font-family: {FONT_FAMILY_MONO};
        border: none;
        padding: 12px;
        outline: none;
    }}
    QTextEdit:focus {{
        outline: none;
        border: none;
    }}
    QTextEdit QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0;
    }}
    QTextEdit QScrollBar::handle:vertical {{
        background: rgba(255, 255, 255, 0.15);
        border-radius: 4px;
        min-height: 30px;
    }}
    QTextEdit QScrollBar::handle:vertical:hover {{
        background: rgba(255, 255, 255, 0.25);
    }}
    QTextEdit QScrollBar::add-line:vertical,
    QTextEdit QScrollBar::sub-line:vertical {{
        height: 0;
        background: none;
    }}
    QTextEdit QScrollBar::add-page:vertical,
    QTextEdit QScrollBar::sub-page:vertical {{
        background: none;
    }}
"""


DIVIDER_STYLE = f"""
    QFrame {{
        background-color: {COLOR_BORDER};
    }}
"""

# Side Panel Styles (for main window)
SIDE_PANEL_STYLE = f"""
    QWidget {{
        background-color: #0a0a0a;
        border-right: 1px solid {COLOR_BORDER};
    }}
"""

SIDE_PANEL_BUTTON_STYLE = f"""
    QPushButton {{
        background: transparent;
        color: {COLOR_TEXT_SECONDARY};
        border: none;
        border-left: 3px solid transparent;
        padding: 12px 18px;
        text-align: left;
        font-family: {FONT_FAMILY_UI};
        font-size: {FONT_SIZE};
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: rgba(249, 115, 22, 0.08);
        color: {COLOR_TEXT_PRIMARY};
        border-left: 3px solid rgba(249, 115, 22, 0.5);
    }}
    QPushButton:checked {{
        background-color: rgba(249, 115, 22, 0.15);
        color: {COLOR_ACCENT};
        border-left: 3px solid {COLOR_ACCENT};
        font-weight: 600;
    }}
"""

SIDE_PANEL_CATEGORY_STYLE = f"""
    QPushButton {{
        color: {COLOR_ACCENT};
        font-size: {FONT_SIZE};
        font-weight: 700;
        text-align: left;
        border: none;
        border-bottom: 1px solid #2d2d4d;
        padding: 12px 5px 8px 5px;
        text-transform: uppercase;
        letter-spacing: 1px;
        background: transparent;
    }}
"""

SIDE_PANEL_HEADER_STYLE = f"""
    QWidget {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1a1a2e, stop:1 #0a0a0a);
        border-bottom: 1px solid {COLOR_BORDER};
    }}
"""

TAB_WIDGET_STYLE = f"""
    QTabWidget::pane {{
        border: none;
        background-color: {COLOR_BACKGROUND_PRIMARY};
        border-radius: 6px;
        top: -1px;
    }}
    QTabBar {{
        background-color: transparent;
        qproperty-drawBase: 0;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {COLOR_TEXT_SECONDARY};
        padding: 10px 24px;
        margin-right: 4px;
        border: 1px solid transparent;
        border-bottom: none;
        font-weight: 600;
        font-size: {FONT_SIZE};
        min-width: 90px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
    }}
    QTabBar::tab:selected {{
        background: {COLOR_BACKGROUND_PRIMARY};
        color: {COLOR_ACCENT};
        border: 1px solid {COLOR_BORDER};
        border-bottom: 2px solid {COLOR_ACCENT};
    }}
    QTabBar::tab:hover:!selected {{
        color: {COLOR_TEXT_PRIMARY};
        background-color: rgba(255, 255, 255, 0.03);
    }}
    QTabBar::close-button {{
        image: none;
        background: transparent;
        padding: 2px;
        border-radius: 2px;
    }}
    QTabBar::close-button:hover {{
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }}
"""

# Global scrollbar styling (thin, subtle)
GLOBAL_SCROLLBAR_STYLE = f"""
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(255, 255, 255, 0.15);
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: rgba(255, 255, 255, 0.25);
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
        background: none;
    }}
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{
        background: none;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background: rgba(255, 255, 255, 0.15);
        border-radius: 4px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: rgba(255, 255, 255, 0.25);
    }}
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0;
        background: none;
    }}
    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {{
        background: none;
    }}
"""

# Main window combined style
MAIN_WINDOW_STYLE = CHECKBOX_STYLE + RADIO_BUTTON_STYLE + SPINBOX_STYLE + GLOBAL_SCROLLBAR_STYLE



# =============================================================================
# SECTION 3: WIDGET CLASSES - BUTTONS
# =============================================================================

class RunButton(QPushButton):
    """Amber run button with embedded styling."""
    
    def __init__(self, text="RUN", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(RUN_BUTTON_STYLE)


class StopButton(QPushButton):
    """Red stop button with embedded styling."""
    
    def __init__(self, text="■", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setEnabled(False)
        self.setStyleSheet(STOP_BUTTON_STYLE)


class CopyButton(QPushButton):
    """Clipboard copy button with embedded styling."""
    
    def __init__(self, target_widget, main_window=None, parent=None):
        super().__init__("📋", parent)
        self.target_widget = target_widget
        self.main_window = main_window
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._copy_to_clipboard)
        self.setStyleSheet(COPY_BUTTON_STYLE)
    
    def _copy_to_clipboard(self):
        text = self.target_widget.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            if self.main_window and hasattr(self.main_window, 'notification_manager'):
                self.main_window.notification_manager.notify("Copied to clipboard")


class BrowseButton(QPushButton):
    """File/folder browse button with embedded styling."""
    
    def __init__(self, text="📁", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedWidth(40)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                font-size: {FONT_SIZE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 6px 10px;
            }}
            QPushButton:hover {{
                background-color: #4A4A4A;
            }}
        """)


# =============================================================================
# SECTION 4: WIDGET CLASSES - INPUTS
# =============================================================================

class StyledLineEdit(QLineEdit):
    """Text input with embedded styling."""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                font-size: {FONT_SIZE};
                font-family: {FONT_FAMILY_UI};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 8px;
            }}
            QLineEdit:focus {{
                border-color: {COLOR_BORDER_FOCUSED};
            }}
        """)


class StyledSpinBox(QSpinBox):
    """Number input with embedded styling."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(SPINBOX_STYLE)


class StyledComboBox(QComboBox):
    """Dropdown with embedded styling and custom arrow."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                font-size: {FONT_SIZE};
                font-family: {FONT_FAMILY_UI};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 6px;
                padding-right: 20px;
            }}
            QComboBox:focus {{
                border-color: {COLOR_BORDER_FOCUSED};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                width: 0; height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {COLOR_TEXT_PRIMARY};
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                selection-background-color: {COLOR_ACCENT};
                border: 1px solid {COLOR_BORDER};
            }}
        """)

    def paintEvent(self, event):
        """Custom paint for arrow."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        drop_down_rect = QRect(width - 20, 0, 20, height)
        center = drop_down_rect.center()

        painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(QBrush(QColor(COLOR_TEXT_PRIMARY)))

        arrow = QPolygon([
            QPoint(center.x() - 3, center.y() - 2),
            QPoint(center.x() + 3, center.y() - 2),
            QPoint(center.x(), center.y() + 3)
        ])
        painter.drawPolygon(arrow)


class StyledCheckBox(QCheckBox):
    """Checkbox with embedded styling."""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(CHECKBOX_STYLE)


class StyledRadioButton(QRadioButton):
    """Radio button with embedded styling."""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(RADIO_BUTTON_STYLE)


class StyledTextEdit(QTextEdit):
    """Multi-line text input with embedded styling."""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                font-size: {FONT_SIZE};
                font-family: {FONT_FAMILY_MONO};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 8px;
                outline: none;
            }}
            QTextEdit:focus {{
                border-color: {COLOR_BORDER_FOCUSED};
                outline: none;
            }}
        """)


# =============================================================================
# SECTION 5: WIDGET CLASSES - DISPLAY
# =============================================================================

class StyledLabel(QLabel):
    """Label with embedded styling (15px, normal weight)."""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(LABEL_STYLE)


class HeaderLabel(QLabel):
    """Tool header label (larger font for titles only)."""
    
    def __init__(self, category, tool_name, parent=None):
        # Replace underscores with spaces for display
        display_category = category.replace("_", " ")
        super().__init__(f"{display_category} › {tool_name}", parent)
        self.setStyleSheet(TOOL_HEADER_STYLE)



class CommandDisplay(QWidget):
    """Terminal-style command preview with embedded styling."""
    
    TERMINAL_BG = "#0D1117"
    TERMINAL_TEXT = "#58A6FF"
    TERMINAL_BORDER = "#30363D"
    
    def __init__(self, parent=None, title="Command", read_only=True):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        label = QLabel(title)
        label.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TEXT_PRIMARY};
                font-size: {FONT_SIZE};
                font-weight: normal;
                font-family: {FONT_FAMILY_UI};
            }}
        """)
        layout.addWidget(label)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Command will appear here...")
        self.input.setReadOnly(read_only)
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.TERMINAL_BG};
                color: {self.TERMINAL_TEXT};
                font-size: {FONT_SIZE};
                font-family: {FONT_FAMILY_MONO};
                border: 1px solid {self.TERMINAL_BORDER};
                border-radius: 6px;
                padding: 12px;
            }}
            QLineEdit:focus {{
                border-color: {self.TERMINAL_TEXT};
            }}
        """)
        layout.addWidget(self.input)

    def setText(self, text):
        self.input.setText(text)
    
    def text(self):
        return self.input.text()


class OutputView(QWidget):
    """Output display widget with embedded styling."""
    
    def __init__(self, main_window=None, parent=None, show_copy_button=True):
        super().__init__(parent)
        self.main_window = main_window
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Results will appear here...")
        self.output_text.setStyleSheet(OUTPUT_TEXT_EDIT_STYLE)
        layout.addWidget(self.output_text)
        
        # Add copy button directly on top of output_text if enabled
        if show_copy_button:
            self.copy_button = CopyButton(self.output_text, main_window, self.output_text)
            self.copy_button.setParent(self.output_text)
            self.copy_button.raise_()
            # Position at top-right, will be updated on resize
            self.output_text.resizeEvent = self._on_output_resize

    # Core methods
    def appendPlainText(self, text):
        self.output_text.append(text)

    def appendHtml(self, html):
        self.output_text.append(html)
    
    def appendHTML(self, html):
        """Alias for appendHtml."""
        self.output_text.append(html)
    
    def append(self, text):
        """Compatibility alias."""
        self.output_text.append(text)

    def setPlaceholderText(self, text):
        self.output_text.setPlaceholderText(text)

    def setReadOnly(self, state):
        self.output_text.setReadOnly(state)

    def toPlainText(self):
        return self.output_text.toPlainText()

    def clear(self):
        self.output_text.clear()
    
    def moveCursor(self, cursor_operation):
        """Move cursor in the text edit."""
        self.output_text.moveCursor(cursor_operation)
    
    def scrollToTop(self):
        """Scroll to the top of the output."""
        from PySide6.QtGui import QTextCursor
        self.output_text.moveCursor(QTextCursor.Start)

    # Rich text helper methods (built into OutputView)
    def info(self, message):
        self.output_text.append(f'<span style="color:{COLOR_INFO};">[INFO]</span> {message}')

    def success(self, message):
        self.output_text.append(f'<span style="color:{COLOR_SUCCESS};">[SUCCESS]</span> {message}')

    def warning(self, message):
        self.output_text.append(f'<span style="color:{COLOR_WARNING};">[WARNING]</span> {message}')

    def error(self, message):
        self.output_text.append(f'<span style="color:{COLOR_ERROR};">[ERROR]</span> {message}')

    def critical(self, message):
        self.output_text.append(f'<span style="color:{COLOR_ERROR};font-weight:bold;">[CRITICAL] {message}</span>')

    def section(self, title):
        self.output_text.append(f'<br><span style="color:{COLOR_WARNING};font-weight:700;">===== {title} =====</span><br>')
    
    def _on_output_resize(self, event):
        """Reposition copy button when output text area is resized."""
        if hasattr(self, 'copy_button'):
            self.copy_button.move(
                self.output_text.width() - self.copy_button.width() - 10,
                10
            )
        # Call the original resize event
        QTextEdit.resizeEvent(self.output_text, event)
    
    # Backward compatibility - old method name
    def _update_copy_button_position(self, event, container):
        """Legacy method for compatibility."""
        return self._on_output_resize(event)


# =============================================================================
# SECTION 6: WIDGET CLASSES - CONTAINERS
# =============================================================================

class ConfigTabs(QTabWidget):
    """Tab widget for tool configuration with embedded styling."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                background-color: {COLOR_BACKGROUND_INPUT};
            }}
            QTabBar::tab {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                font-size: {FONT_SIZE};
                font-family: {FONT_FAMILY_UI};
                border: 1px solid {COLOR_BORDER};
                padding: 8px 16px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background-color: #1777d1;
                color: white;
                font-weight: bold;
            }}
            QTabBar::tab:hover {{
                background-color: #4A4A4A;
            }}
        """)


class StyledGroupBox(QGroupBox):
    """Group box with embedded styling."""
    
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setStyleSheet(GROUPBOX_STYLE)


class ToolSplitter(QSplitter):
    """Vertical splitter with embedded styling."""
    
    def __init__(self, parent=None):
        super().__init__(Qt.Vertical, parent)
        self.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {COLOR_BORDER};
                height: 3px;
            }}
            QSplitter::handle:hover {{
                background-color: {COLOR_ACCENT};
            }}
        """)


# =============================================================================
# SECTION 7: BEHAVIOR CLASSES
# =============================================================================

class SafeStop:
    """Provides safe worker stopping logic.
    
    Usage:
        class MyTool(QWidget, SafeStop):
            def __init__(self):
                super().__init__()
                self.init_safe_stop()
    """
    
    def init_safe_stop(self):
        """Initialize safe stop state. Call in __init__."""
        self.worker = None
    
    def register_worker(self, worker):
        """Register a worker for safe stopping."""
        self.worker = worker
    
    def stop_scan(self):
        """Safely stop the current worker/process."""
        if hasattr(self, 'worker') and self.worker:
            self.worker.stop()
            self.worker = None
        if hasattr(self, 'run_button'):
            self.run_button.setEnabled(True)
        if hasattr(self, 'stop_button'):
            self.stop_button.setEnabled(False)
        if hasattr(self, '_info'):
            self._info("Process stopped by user.")


class OutputHelper:
    """Provides standard output helper methods.
    
    Usage:
        class MyTool(QWidget, OutputHelper):
            def __init__(self):
                self.output = OutputView()
                self.main_window = main_window
    
    Requires:
        - self.output (OutputView or QTextEdit-like widget)
        - self.main_window (optional, for notifications)
    """
    
    def _notify(self, message):
        """Show notification via main window."""
        if hasattr(self, 'main_window') and self.main_window:
            if hasattr(self.main_window, 'notification_manager'):
                self.main_window.notification_manager.notify(message)
    
    def _info(self, message):
        """Add info message to output."""
        if hasattr(self, 'output'):
            self.output.appendHtml(f'<span style="color:{COLOR_INFO};">[INFO]</span> {message}')
    
    def _error(self, message):
        """Add error message to output."""
        if hasattr(self, 'output'):
            self.output.appendHtml(f'<span style="color:{COLOR_ERROR};">[ERROR]</span> {message}')
    
    def _warning(self, message):
        """Add warning message to output."""
        if hasattr(self, 'output'):
            self.output.appendHtml(f'<span style="color:{COLOR_WARNING};">[WARNING]</span> {message}')
    
    def _success(self, message):
        """Add success message to output."""
        if hasattr(self, 'output'):
            self.output.appendHtml(f'<span style="color:{COLOR_SUCCESS};">[SUCCESS]</span> {message}')
    
    def _section(self, title):
        """Add section header to output."""
        if hasattr(self, 'output'):
            self.output.appendHtml(f'<br><span style="color:{COLOR_WARNING};font-weight:700;">===== {title} =====</span><br>')

