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
import html
from PySide6.QtCore import Qt, QSize, QRect, QPoint, QEvent, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPolygon, QTextBlockFormat, QTextCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QSplitter, QSizePolicy, QSpinBox,
    QComboBox, QTextEdit, QApplication, QCheckBox, QGroupBox,
    QTabWidget, QRadioButton, QToolButton, QProgressBar
)




# =============================================================================
# SECTION 1: CORE CONSTANTS
# =============================================================================

# Fonts
FONT_FAMILY_UI = "Segoe UI, Arial, sans-serif"
FONT_FAMILY_MONO = "Consolas, 'Courier New', monospace"
FONT_SIZE = "15px"

# Base Colors
COLOR_BG_PRIMARY   = "#0f0f0f"
COLOR_BG_SECONDARY = "#18181b"
COLOR_BG_INPUT     = "#252525"
COLOR_BG_ELEVATED  = "#2a2a2a"

# Text Colors
COLOR_TEXT_PRIMARY   = "#ffffff"
COLOR_TEXT_SECONDARY = "#9ca3af"
COLOR_TEXT_MUTED     = "#6b7280"

# Accents
COLOR_ACCENT_PRIMARY = "#f97316"
COLOR_ACCENT_HOVER   = "#fb923c"
COLOR_ACCENT_BLUE    = "#3b82f6"

# Semantic Output
COLOR_INFO     = "#60a5fa"
COLOR_SUCCESS  = "#10b981"
COLOR_WARNING  = "#facc15"
COLOR_ERROR    = "#f87171"
COLOR_CRITICAL = "#ef4444"

# Borders
COLOR_BORDER_DEFAULT = "#27272a"
COLOR_BORDER_FOCUS   = "transparent" 




# =============================================================================
# SECTION 2: LEGACY STYLE STRINGS (for backward compatibility)
# These will be slowly phased out as tools migrate to widget classes
# =============================================================================

# Keep these for any tools that still need them during transition
TOOL_VIEW_STYLE = f"""
    QWidget {{
        background-color: {COLOR_BG_PRIMARY};
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
    background-color: {COLOR_BG_SECONDARY};
    border-bottom: 1px solid {COLOR_BORDER_DEFAULT};
"""

# Legacy style strings - keep for compatibility
RUN_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLOR_ACCENT_PRIMARY};
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
        background-color: {COLOR_BG_INPUT};
        color: {COLOR_TEXT_SECONDARY};
    }}
"""

STOP_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLOR_CRITICAL};
        color: {COLOR_TEXT_PRIMARY};
        font-size: 16px;
        font-weight: 900;
        border-radius: 4px;
        padding: 8px 12px;
        border: none;
    }}
    QPushButton:hover {{
        background-color: {COLOR_ERROR};
    }}
    QPushButton:disabled {{
        background-color: {COLOR_BG_INPUT};
        color: {COLOR_TEXT_SECONDARY};
    }}
"""

COPY_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLOR_BG_SECONDARY};
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE};
        border: 1px solid {COLOR_BORDER_DEFAULT};
        border-radius: 4px;
        padding: 6px;
    }}
    QPushButton:hover {{
        background-color: {COLOR_BG_INPUT};
        border: 1px solid {COLOR_ACCENT_PRIMARY};
    }}
"""

GROUPBOX_STYLE = f"""
    QGroupBox {{
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE};
        font-family: {FONT_FAMILY_UI};
        font-weight: bold;
        border: 1px solid {COLOR_BORDER_DEFAULT};
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
        background-color: {COLOR_BG_INPUT};
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE};
        font-family: {FONT_FAMILY_UI};
        border: 1px solid {COLOR_BORDER_DEFAULT};
        border-radius: 4px;
        padding: 4px 24px 4px 8px;
        min-width: 50px;
    }}
    QSpinBox:focus {{
        border: 1px solid {COLOR_TEXT_MUTED};
    }}
    QSpinBox::up-button {{
        subcontrol-origin: border;
        subcontrol-position: center right;
        width: 12px;
        height: 100%;
        right: 0px;
        border: none;
        border-left: 1px solid {COLOR_BORDER_DEFAULT};
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
        border-left: 1px solid {COLOR_BORDER_DEFAULT};
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
        background-color: {COLOR_BG_INPUT};
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE};
        font-family: {FONT_FAMILY_UI};
        border: 1px solid {COLOR_BORDER_DEFAULT};
        border-radius: 4px;
        padding: 6px;
        padding-right: 20px;
    }}
    QComboBox:focus {{
        border-color: {COLOR_TEXT_MUTED};
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
        border: 1px solid {COLOR_BORDER_DEFAULT};
        border-radius: 3px;
        background-color: {COLOR_BG_INPUT};
    }}
    QCheckBox::indicator:checked {{
        background-color: {COLOR_ACCENT_PRIMARY};
        border: 1px solid {COLOR_ACCENT_PRIMARY};
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
        border: 2px solid {COLOR_BORDER_DEFAULT};
        border-radius: 9px;
        background-color: {COLOR_BG_INPUT};
    }}
    QRadioButton::indicator:checked {{
        background-color: {COLOR_ACCENT_PRIMARY};
        border: 2px solid {COLOR_ACCENT_PRIMARY};
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
        background-color: {COLOR_BG_INPUT};
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE};
        font-family: {FONT_FAMILY_MONO};
        border: 1px solid {COLOR_BORDER_DEFAULT};
        border-radius: 4px;
        padding: 8px;
    }}
    QLineEdit:focus {{
        border: 1px solid {COLOR_TEXT_MUTED};
    }}
"""

OUTPUT_TEXT_EDIT_STYLE = f"""
    QTextEdit {{
        background-color: {COLOR_BG_PRIMARY};
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
        background-color: {COLOR_BORDER_DEFAULT};
    }}
"""

# Side Panel Styles (for main window)
SIDE_PANEL_STYLE = f"""
    QWidget {{
        background-color: #0a0a0a;
        border-right: 1px solid {COLOR_BORDER_DEFAULT};
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
        outline: none;
    }}
    QPushButton:focus {{
        border: none;
        outline: none;
    }}
    QPushButton:hover {{
        background-color: rgba(249, 115, 22, 0.08);
        color: {COLOR_TEXT_PRIMARY};
        border-left: 3px solid rgba(249, 115, 22, 0.5);
    }}
    QPushButton:checked {{
        background-color: rgba(249, 115, 22, 0.15);
        color: {COLOR_ACCENT_PRIMARY};
        border-left: 3px solid {COLOR_ACCENT_PRIMARY};
        font-weight: 600;
    }}
"""

SIDE_PANEL_CATEGORY_STYLE = f"""
    QPushButton {{
        color: {COLOR_ACCENT_PRIMARY};
        font-size: {FONT_SIZE};
        font-weight: 700;
        text-align: left;
        border: none;
        border-bottom: 1px solid #2d2d4d;
        padding: 12px 5px 8px 5px;
        text-transform: uppercase;
        letter-spacing: 1px;
        background: transparent;
        outline: none;
    }}
    QPushButton:focus {{
        outline: none;
        border: none;
        border-bottom: 1px solid #2d2d4d;
    }}
"""

SIDE_PANEL_HEADER_STYLE = f"""
    QWidget {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1a1a2e, stop:1 #0a0a0a);
        border-bottom: 1px solid {COLOR_BORDER_DEFAULT};
    }}
"""

TAB_WIDGET_STYLE = f"""
    QTabWidget::pane {{
        border: none;
        background-color: {COLOR_BG_PRIMARY};
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
        outline: none;
    }}
    QTabBar::tab:selected {{
        background: {COLOR_BG_PRIMARY};
        color: {COLOR_ACCENT_PRIMARY};
        border: 1px solid {COLOR_BORDER_DEFAULT};
        border-bottom: 2px solid {COLOR_ACCENT_PRIMARY};
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

# Tooltip styling
TOOLTIP_STYLE = f"""
    QToolTip {{
        color: {COLOR_TEXT_PRIMARY};
        background-color: {COLOR_BG_ELEVATED};
        border: 1px solid {COLOR_BORDER_DEFAULT};
        font-family: {FONT_FAMILY_UI};
        padding: 5px;
    }}
"""

# Main window combined style - removes default focus rectangle generally
MAIN_WINDOW_STYLE = CHECKBOX_STYLE + RADIO_BUTTON_STYLE + SPINBOX_STYLE + GLOBAL_SCROLLBAR_STYLE + TOOLTIP_STYLE + """
    QWidget {
        outline: none;
    }
"""



# =============================================================================
# SECTION 3: WIDGET CLASSES - BUTTONS
# =============================================================================

class RunButton(QPushButton):
    """Amber run button with embedded styling and spinner."""
    
    def __init__(self, text="RUN", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(RUN_BUTTON_STYLE)
        
        self.is_loading = False
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate_spinner)
        
        self._original_text = text
        
    def set_loading(self, loading: bool):
        """Set loading state with spinner."""
        self.is_loading = loading
        self.setEnabled(not loading)
        
        if loading:
            self._original_text = self.text()
            self.setText("") # Hide text while loading
            self.timer.start(50) # Approx 20 FPS
        else:
            self.setText(self._original_text)
            self.timer.stop()
        self.update() # Trigger repaint
        
    def rotate_spinner(self):
        self.angle = (self.angle + 30) % 360
        self.update()
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
        if self.is_loading:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Center of button
            center_x = self.width() / 2
            center_y = self.height() / 2
            
            # Simple spinner geometry
            painter.translate(center_x, center_y)
            painter.rotate(self.angle)
            
            pen = QPen(QColor(COLOR_TEXT_PRIMARY))
            pen.setWidth(2)
            painter.setPen(pen)
            
            # Draw an arc
            radius = 8
            painter.drawArc(-radius, -radius, radius*2, radius*2, 0, 270 * 16)
            painter.end()


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
                background-color: {COLOR_BG_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                font-size: {FONT_SIZE};
                border: 1px solid {COLOR_BORDER_DEFAULT};
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
    """Text input with embedded styling, search icon, and Esc handling."""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        # Add padding-left for the icon
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_BG_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                font-size: {FONT_SIZE};
                font-family: {FONT_FAMILY_UI};
                border: 1px solid {COLOR_BORDER_DEFAULT};
                border-radius: 4px;
                padding: 8px;
                padding-left: 28px; 
            }}
            QLineEdit:focus {{
                border: 1px solid {COLOR_TEXT_MUTED};
            }}
        """)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
        # Draw search icon if empty
        if not self.text():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            icon_color = QColor(COLOR_TEXT_MUTED)
            icon_color.setAlpha(150) # 60% approx
            
            pen = QPen(icon_color)
            pen.setWidth(2)
            painter.setPen(pen)
            
            # Magnifier Geometry
            # Center of the left padding area (28px width)
            # x center = 14, y center = height/2
            cx = 12
            cy = self.height() / 2 - 2
            r = 5
            
            painter.drawEllipse(QPoint(cx, cy), r, r)
            painter.drawLine(cx + 3, cy + 3, cx + 7, cy + 7)
            
            painter.end()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.text():
                self.clear()
            else:
                # Consume event to prevent bubbling to parent (global stop)
                event.accept()
        else:
            super().keyPressEvent(event)


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
                background-color: {COLOR_BG_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                font-size: {FONT_SIZE};
                font-family: {FONT_FAMILY_UI};
                border: 1px solid {COLOR_BORDER_DEFAULT};
                border-radius: 4px;
                padding: 6px;
                padding-right: 20px;
            }}
            QComboBox:focus {{
                border: 1px solid {COLOR_TEXT_MUTED};
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
                background-color: {COLOR_BG_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                selection-background-color: {COLOR_ACCENT_PRIMARY};
                border: 1px solid {COLOR_BORDER_DEFAULT};
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
                background-color: {COLOR_BG_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                font-size: {FONT_SIZE};
                font-family: {FONT_FAMILY_MONO};
                border: 1px solid {COLOR_BORDER_DEFAULT};
                border-radius: 4px;
                padding: 8px;
                outline: none;
            }}
            QTextEdit:focus {{
                border: 1px solid {COLOR_TEXT_MUTED};
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
                border: 1px solid {self.TERMINAL_TEXT};
            }}
        """)
        layout.addWidget(self.input)

    def setText(self, text):
        self.input.setText(text)
    
    def text(self):
        return self.input.text()


class OutputView(QWidget):
    """Output display widget with embedded styling and auto-scroll."""
    
    def __init__(self, main_window=None, parent=None, show_copy_button=True):
        super().__init__(parent)
        self.main_window = main_window
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Output Text Area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet(OUTPUT_TEXT_EDIT_STYLE)
        
        # Overlay Layout for sticky buttons
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.output_text)

        layout.addWidget(container)
        
        # Tools Overlay
        self.tools_overlay = QWidget(self.output_text)
        self.tools_overlay.setStyleSheet("background: transparent;")
        tools_layout = QHBoxLayout(self.tools_overlay)
        tools_layout.setContentsMargins(0, 5, 20, 0) # Top right padding
        tools_layout.addStretch()
        
        # Auto Scroll Toggle Removed


        if show_copy_button:
            copy_btn = CopyButton(self.output_text, main_window)
            # Retain copy button style but make it smaller/icon only if needed
            copy_btn.setFixedSize(30,30) # Compact
            # Overwrite default copy style for compactness
            copy_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_BG_SECONDARY};
                    color: {COLOR_TEXT_PRIMARY};
                    border: 1px solid {COLOR_BORDER_DEFAULT};
                    border-radius: 4px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    border: 1px solid {COLOR_ACCENT_PRIMARY};
                }}
            """)
            tools_layout.addWidget(copy_btn)

        self.tools_overlay.show()
        # Ensure overlay stays on top and resizing
        self.output_text.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.output_text and event.type() == QEvent.Resize:
            self.tools_overlay.resize(self.output_text.width(), 40) # Fixed height strip
        return super().eventFilter(obj, event)

    def _toggle_scroll(self, checked):
        ConfigManager.set_auto_scroll(checked)
        if checked:
            self.output_text.moveCursor(QTextCursor.MoveOperation.End)

    def appendHtml(self, html):
        self.output_text.append(html)

    def append(self, text):
        """Compatibility alias."""
        self.appendPlainText(text)
        
    def appendPlainText(self, text):
        self.output_text.append(text)

        
    def setText(self, text):
        self.output_text.setText(text)
        
    def clear(self):
        self.output_text.clear()
        
    def toPlainText(self):
        return self.output_text.toPlainText()
    
    def setPlaceholderText(self, text):
        self.output_text.setPlaceholderText(text)

    def scrollToTop(self):
        self.output_text.moveCursor(QTextCursor.Start)

    def scrollToBottom(self):
        self.output_text.moveCursor(QTextCursor.End)
    
    def setReadOnly(self, ro):
        self.output_text.setReadOnly(ro)


class OutputHelper:
    """Mixin for tools to log styled messages to self.output widget."""
    
    def _raw(self, message):
         """Do NOT use directly unless necessary. Semantics preferred."""
         if hasattr(self, 'output'):
             self.output.appendHtml(message)

    def _section(self, title):
        if hasattr(self, 'output'):
            # Use block formatting logic or <br>
            # Creating a styled div
            style = f"border-left: 3px solid {COLOR_ACCENT_PRIMARY}; padding-left: 8px; margin: 10px 0; font-weight: bold; color: {COLOR_TEXT_PRIMARY};"
            html_content = f'<div style="{style}">=== {title} ===</div>'
            self.output.appendHtml(html_content)

    def _info(self, message):
        if hasattr(self, 'output'):
            style = f"border-left: 3px solid {COLOR_INFO}; padding-left: 8px; margin: 2px 0; color: {COLOR_TEXT_PRIMARY};"
            self.output.appendHtml(f'<div style="{style}">{message}</div>')

    def _success(self, message):
        if hasattr(self, 'output'):
            style = f"border-left: 3px solid {COLOR_SUCCESS}; padding-left: 8px; margin: 2px 0; color: {COLOR_TEXT_PRIMARY};"
            self.output.appendHtml(f'<div style="{style}">{message}</div>')

    def _warning(self, message):
        if hasattr(self, 'output'):
            style = f"border-left: 3px solid {COLOR_WARNING}; padding-left: 8px; margin: 2px 0; color: {COLOR_TEXT_PRIMARY};"
            self.output.appendHtml(f'<div style="{style}">{message}</div>')

    def _error(self, message):
        if hasattr(self, 'output'):
            style = f"border-left: 3px solid {COLOR_ERROR}; padding-left: 8px; margin: 2px 0; color: {COLOR_ERROR};"
            self.output.appendHtml(f'<div style="{style}">{message}</div>')
    
    def _critical(self, message):
        if hasattr(self, 'output'):
            style = f"border-left: 3px solid {COLOR_CRITICAL}; padding-left: 8px; margin: 2px 0; color: {COLOR_CRITICAL}; font-weight: bold;"
            self.output.appendHtml(f'<div style="{style}">{message}</div>')
            
    def _notify(self, message):
        """Send a notification toast."""
        if hasattr(self, 'main_window') and self.main_window:
            if hasattr(self.main_window, 'notification_manager'):
                self.main_window.notification_manager.notify(message)

    def strip_ansi(self, text):
        """Strip ANSI escape sequences from text."""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)


class SafeStop:
    """Mixin for safely stopping processes."""
    
    def init_safe_stop(self):
        self.worker = None
        self.workers = [] # Track multiple workers

    def register_worker(self, worker):
        """Register a worker to be cleaned up on stop."""
        self.worker = worker # Backward compatibility for single worker

        # Auto-init list if missing (Robustness fix)
        if not hasattr(self, 'workers'):
            self.workers = []

        if worker not in self.workers:
            self.workers.append(worker)
            # Auto-cleanup when done - Fix lambda closure bug
            worker.finished.connect(self._make_cleanup_callback(worker))

    def _make_cleanup_callback(self, worker):
        """Create a proper closure callback for worker cleanup."""
        return lambda: self._cleanup_worker(worker)

    def _cleanup_worker(self, worker):
        """Safely cleanup a finished worker."""
        if worker in self.workers:
            # Validate worker is actually finished before removing
            if hasattr(worker, 'isRunning') and not worker.isRunning():
                self.workers.remove(worker)
            elif hasattr(worker, 'isFinished') and worker.isFinished():
                self.workers.remove(worker)
            # If worker is still running, don't remove it yet

        
    def stop_scan(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self._error("Process terminated by user.")
            if hasattr(self, 'run_button'): self.run_button.setEnabled(True)
            if hasattr(self, 'stop_button'): self.stop_button.setEnabled(False)
            if hasattr(self, 'run_button') and hasattr(self.run_button, 'set_loading'):
                self.run_button.set_loading(False)
    
    def stop_all_workers(self):
        """Stop all registered workers."""
        self.stop_scan() # Stop main worker
        # Stop any other tracked workers
        for w in list(self.workers):
            if w.isRunning():
                w.stop()
        self.workers.clear()


class ToolSplitter(QSplitter):
    """Pre-styled splitter."""
    
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setHandleWidth(1)
        self.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {COLOR_BORDER_DEFAULT};
            }}
        """)


class StyledGroupBox(QGroupBox):
    """Unified GroupBox style."""
    
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setStyleSheet(GROUPBOX_STYLE)


class ConfigTabs(QTabWidget):
    """Pre-styled tab widget for tools."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(TAB_WIDGET_STYLE)


class StyledProgressBar(QProgressBar):
    """Styled progress bar for long-running operations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {COLOR_BORDER_DEFAULT};
                border-radius: 3px;
                text-align: center;
                background-color: {COLOR_BG_SECONDARY};
                color: {COLOR_TEXT_PRIMARY};
                font-size: 11px;
            }}

            QProgressBar::chunk {{
                background-color: {COLOR_ACCENT_PRIMARY};
                border-radius: 2px;
            }}
        """)
        self.setFixedHeight(25)
        self.setRange(0, 100)
        self.setVisible(False)  # Hidden by default


class StyledToolView(QWidget):
    """Base class for all tool views to ensure consistent styling."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(TOOL_VIEW_STYLE)
