# =============================================================================
# ui/styles.py
#
# Centralized stylesheet and custom styled widgets for the application.
# =============================================================================

from PySide6.QtWidgets import (
    QPlainTextEdit, QComboBox, QSpinBox, QPushButton, QApplication,
    QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSplitter
)
from PySide6.QtGui import QFont, QPainter, QPen, QBrush, QPolygon
from PySide6.QtCore import Qt, QRect, QPoint

# --- Color Palette (VS Code Dark+ Theme inspired) ---
COLOR_BACKGROUND_PRIMARY = "#1E1E1E"      # Editor background
COLOR_BACKGROUND_SECONDARY = "#1C1C1C"    # Side bar background
COLOR_BACKGROUND_INPUT = "#3C3C3C"        # Input field background
COLOR_BACKGROUND_BUTTON = "#D97706"       # Primary button background (Amber 600)
COLOR_BACKGROUND_BUTTON_HOVER = "#F59E0B"   # Button background on hover (Amber 500)
COLOR_BACKGROUND_BUTTON_DANGER = "#C93633"
COLOR_BACKGROUND_BUTTON_DANGER_HOVER = "#DA3633"

COLOR_BACKGROUND_SIDEPANEL_DARK = "#121212" # Even darker for sidepanel

COLOR_BORDER = "#333333"
COLOR_BORDER_INPUT_FOCUSED = "#F59E0B" # (Amber 500)

COLOR_TEXT_PRIMARY = "#FFFFFF"            # Primary text color
COLOR_TEXT_SECONDARY = "#8B8B8B"          # Lighter text for placeholders/labels
COLOR_TEXT_BUTTON = "#FFFFFF"

# --- Semantic Colors ---
COLOR_SUCCESS = "#28A745"
COLOR_WARNING = "#FFC107"
COLOR_ERROR = "#DC3545"
COLOR_INFO = "#FACC15" # (Yellow 400)

# --- Cracker Category Colors ---
COLOR_CRACKER_HASHCAT = "#FF6B35"       # Orange for Hashcat
COLOR_CRACKER_HYDRA = "#DC3545"         # Red for Hydra
COLOR_CRACKER_JOHN = "#28A745"          # Green for John The Ripper
COLOR_CRACKER_GROUPBOX = "#2A2A2A"      # Dark gray for groupbox backgrounds

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

# --- Side Panel ---
SIDE_PANEL_STYLE = f"""
    QWidget {{
        background-color: {COLOR_BACKGROUND_SIDEPANEL_DARK};
        border-right: 1px solid {COLOR_BORDER};
    }}
"""

SIDE_PANEL_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLOR_BACKGROUND_SIDEPANEL_DARK};
        color: {COLOR_TEXT_SECONDARY};
        border: none;
        padding: 10px 15px;
        text-align: left;
        font-size: 14px;
    }}
    QPushButton:hover {{
        background-color: {COLOR_BACKGROUND_SECONDARY}; /* Lighter on hover */
        color: {COLOR_TEXT_PRIMARY};
    }}
    QPushButton:checked {{
        background-color: {COLOR_BACKGROUND_BUTTON}; /* Highlight when checked/selected */
        color: {COLOR_TEXT_BUTTON};
        font-weight: bold;
    }}
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
        border-top: 2px solid transparent; /* Add transparent border for alignment */
    }}
    QTabBar::tab:selected {{
        background: {COLOR_BACKGROUND_SECONDARY};
        color: {COLOR_TEXT_PRIMARY};
        border-top: 2px solid {COLOR_BORDER_INPUT_FOCUSED}; /* Add golden highlight */
    }}
    QTabBar::tab:hover {{
        color: {COLOR_TEXT_PRIMARY};
        background: {COLOR_BACKGROUND_SECONDARY};
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
# ============================================================================="""


# =============================================================================
# PLAIN TEXT OUTPUT WIDGET
# =============================================================================

class PlainTextOutput(QPlainTextEdit):
    """A styled, read-only text area for displaying logs and output."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont(FONT_FAMILY_MONO, 10))
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 10px;
            }}
        """)

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


# =============================================================================
# REUSABLE STYLED WIDGET CLASSES
# =============================================================================

class StyledComboBox(QComboBox):
    """
    Custom ComboBox with visible arrow, 15px font, and consistent styling.
    
    Usage:
        from ui.styles import StyledComboBox
        combo = StyledComboBox()
        combo.addItems(["Option 1", "Option 2"])
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(self._get_style())

    def _get_style(self):
        return f"""
            QComboBox {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 8px;
                padding-right: 20px;
                font-size: 15px;
            }}
            QComboBox:focus {{
                border: 1px solid {COLOR_BORDER_INPUT_FOCUSED};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid {COLOR_BORDER};
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-color: {COLOR_BACKGROUND_INPUT};
            }}
            QComboBox::drop-down:hover {{
                background-color: #4A4A4A;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLOR_BACKGROUND_INPUT};
                border: 1px solid {COLOR_BORDER};
                color: {COLOR_TEXT_PRIMARY};
                selection-background-color: {COLOR_BORDER_INPUT_FOCUSED};
                selection-color: {COLOR_TEXT_PRIMARY};
                outline: none;
                font-size: 15px;
                padding: 4px;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 8px 12px;
                min-height: 28px;
            }}
        """

    def paintEvent(self, event):
        """Custom paint event to draw arrow."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate drop-down button area (right side, 20px wide)
        width = self.width()
        height = self.height()
        drop_down_width = 20
        drop_down_x = width - drop_down_width
        drop_down_rect = QRect(drop_down_x, 0, drop_down_width, height)

        # Draw arrow triangle in center of drop-down area
        arrow_size = 6
        center_x = drop_down_rect.center().x()
        center_y = drop_down_rect.center().y()

        painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(QBrush(COLOR_TEXT_PRIMARY))

        # Draw downward triangle
        arrow = QPolygon([
            QPoint(center_x - arrow_size//2, center_y - arrow_size//3),
            QPoint(center_x + arrow_size//2, center_y - arrow_size//3),
            QPoint(center_x, center_y + arrow_size//2)
        ])
        painter.drawPolygon(arrow)


class StyledSpinBox(QSpinBox):
    """
    Custom SpinBox with visible white arrow triangles and 15px font.
    
    Usage:
        from ui.styles import StyledSpinBox
        spin = StyledSpinBox()
        spin.setRange(0, 100)
        spin.setValue(10)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(self._get_style())

    def _get_style(self):
        return f"""
            QSpinBox {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 6px;
                padding-right: 20px;
                font-size: 15px;
            }}
            QSpinBox:focus {{
                border: 1px solid {COLOR_BORDER_INPUT_FOCUSED};
            }}
            QSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 18px;
                border: none;
                background: transparent;
            }}
            QSpinBox::up-button:hover {{
                background-color: rgba(100, 100, 100, 0.5);
            }}
            QSpinBox::up-arrow {{
                width: 0;
                height: 0;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-bottom: 7px solid #FFFFFF;
            }}
            QSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 18px;
                border: none;
                background: transparent;
            }}
            QSpinBox::down-button:hover {{
                background-color: rgba(100, 100, 100, 0.5);
            }}
            QSpinBox::down-arrow {{
                width: 0;
                height: 0;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 7px solid #FFFFFF;
            }}
        """


# =============================================================================
# STYLE CONSTANTS FOR DIRECT APPLICATION
# =============================================================================

# SpinBox style as a constant (for setStyleSheet)
SPINBOX_STYLE = f"""
    QSpinBox {{
        background-color: {COLOR_BACKGROUND_INPUT};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        padding: 6px;
        padding-right: 20px;
        font-size: 15px;
    }}
    QSpinBox:focus {{
        border: 1px solid {COLOR_BORDER_INPUT_FOCUSED};
    }}
    QSpinBox::up-button {{
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: 18px;
        border: none;
        background: transparent;
    }}
    QSpinBox::up-button:hover {{
        background-color: rgba(100, 100, 100, 0.5);
    }}
    QSpinBox::up-arrow {{
        width: 0;
        height: 0;
        border-left: 6px solid transparent;
        border-right: 6px solid transparent;
        border-bottom: 7px solid #FFFFFF;
    }}
    QSpinBox::down-button {{
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: 18px;
        border: none;
        background: transparent;
    }}
    QSpinBox::down-button:hover {{
        background-color: rgba(100, 100, 100, 0.5);
    }}
    QSpinBox::down-arrow {{
        width: 0;
        height: 0;
        border-left: 6px solid transparent;
        border-right: 6px solid transparent;
        border-top: 7px solid #FFFFFF;
    }}
"""

# Label styles with 15px font
LABEL_STYLE_15PX = f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 500;"
LABEL_TITLE_STYLE_15PX = f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 600;"
CHECKBOX_STYLE_15PX = f"font-size: 15px; color: {COLOR_TEXT_PRIMARY};"

# =============================================================================
# COPY BUTTON - Centralized copy button style and widget
# =============================================================================

COPY_BUTTON_STYLE = '''
    QPushButton {
        font-size: 24px;
        background-color: transparent;
        border: none;
        padding: 10px;
    }
    QPushButton:hover {
        background-color: rgba(23, 119, 209, 0.2);
        border-radius: 8px;
    }
'''


class CopyButton(QPushButton):
    """
    Centralized copy button widget for copying text from output widgets.
    
    Usage:
        self.copy_button = CopyButton(self.output, self.main_window)
        self.copy_button.setParent(self.output)
    """
    
    def __init__(self, target_widget, main_window=None):
        super().__init__("📋")
        self.target_widget = target_widget
        self.main_window = main_window
        self.setStyleSheet(COPY_BUTTON_STYLE)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._copy_to_clipboard)
    
    def _copy_to_clipboard(self):
        """Copy target widget text to clipboard and show toast popup."""
        text = self.target_widget.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            if self.main_window and hasattr(self.main_window, 'notification_manager'):
                # Show only toast popup, not in notification menu
                self.main_window.notification_manager.show_toast("Results copied to clipboard.")


class OutputView(QWidget):
    """
    A widget for displaying tool output.
    Simple output view without copy button - tools should add CopyButton separately.
    
    Usage:
        self.output = OutputView()
    """

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._build_ui()

    def _build_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Tool results will appear here...")
        self.output_text.setStyleSheet(OUTPUT_TEXT_EDIT_STYLE)

        layout.addWidget(self.output_text, 0, 0)

    def appendPlainText(self, text):
        self.output_text.appendPlainText(text)

    def appendHtml(self, html):
        self.output_text.appendHtml(html)

    def toPlainText(self):
        return self.output_text.toPlainText()

    def clear(self):
        self.output_text.clear()


class CommandDisplay(QWidget):
    """
    Centralized command line display widget.
    Features a label and an editable text input for command preview.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # Zero margins to fit in layouts
        layout.setSpacing(5)

        label = QLabel("Command")
        label.setStyleSheet(LABEL_STYLE)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Command will appear here...")
        self.input.setStyleSheet(TARGET_INPUT_STYLE)
        
        # User requested editable command line
        self.input.setReadOnly(False) 

        layout.addWidget(label)
        layout.addWidget(self.input)

    def setText(self, text):
        self.input.setText(text)

    def text(self):
        return self.input.text()



class BaseToolView(QWidget):
    """
    A base view for tools, providing a consistent UI structure.
    All tools inherit from this to get a uniform look.
    
    Features:
    - Automatic process cleanup on stop (via StoppableToolMixin)
    - Graceful termination of subprocesses
    - Cleanup on widget close
    
    Usage:
        class MyToolView(BaseToolView):
            def __init__(self, main_window=None):
                super().__init__("MyTool", ToolCategory.CATEGORY, main_window)
    """

    def __init__(self, name, category, main_window=None):
        super().__init__()
        self.name = name
        self.category = category
        self.main_window = main_window
        # Initialize stop functionality from StoppableToolMixin
        self.worker = None
        self._active_workers = []
        self._build_base_ui()

    def _build_base_ui(self):
        from core.tgtinput import TargetInput
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

        # --- Control Panel ---
        control_panel = QWidget()
        control_panel.setStyleSheet(TOOL_VIEW_STYLE)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        header = QLabel(f"{self.category.name.replace('_', ' ')}  ›  {self.name}")
        header.setStyleSheet(TOOL_HEADER_STYLE)
        control_layout.addWidget(header)

        target_label = QLabel("Target")
        target_label.setStyleSheet(LABEL_STYLE)
        control_layout.addWidget(target_label)

        # --- Target Input and Action Buttons ---
        target_line_layout = QHBoxLayout()
        self.target_input = TargetInput()
        self.target_input.setStyleSheet(TARGET_INPUT_STYLE)
        self.target_input.input_box.textChanged.connect(self.update_command)

        self.run_button = QPushButton("RUN")
        self.run_button.setStyleSheet(RUN_BUTTON_STYLE)
        self.run_button.clicked.connect(self.run_scan)
        self.stop_button = QPushButton("■")
        self.stop_button.setStyleSheet(STOP_BUTTON_STYLE)
        self.stop_button.clicked.connect(self.stop_scan)
        self.stop_button.setEnabled(False)

        target_line_layout.addWidget(self.target_input)
        target_line_layout.addWidget(self.run_button)
        target_line_layout.addWidget(self.stop_button)

        control_layout.addLayout(target_line_layout)

        # --- Options Container (Placeholder for tools to add options) ---
        # Tools should add their widgets/layouts to self.options_container
        # instead of inserting into control_layout manually.
        self.options_container = QVBoxLayout()
        self.options_container.setSpacing(10)
        control_layout.addLayout(self.options_container)

        # --- Command Display ---
        self.command_display = CommandDisplay()
        # Create legacy alias for tools that assume self.command_input exists
        self.command_input = self.command_display.input 
        
        control_layout.addWidget(self.command_display)
        control_layout.addStretch()

        # --- Output Area ---
        self.output = OutputView(self.main_window)

        splitter.addWidget(control_panel)
        splitter.addWidget(self.output)
        splitter.setSizes([250, 500])

        self.update_command()

    def update_command(self):
        raise NotImplementedError("Subclasses must implement update_command.")

    def run_scan(self):
        raise NotImplementedError("Subclasses must implement run_scan.")

    # ==================== STOP FUNCTIONALITY (Centralized) ====================
    # These methods use the same pattern as StoppableToolMixin
    
    def stop_scan(self):
        """
        Safely stop the current scan.
        Uses centralized stop logic from StoppableToolMixin pattern.
        """
        try:
            if self.worker and self.worker.isRunning():
                self.worker.stop()
                self.worker.wait(1000)  # Wait up to 1 second
        except Exception:
            pass
        finally:
            self._on_scan_completed()

    def register_worker(self, worker):
        """Register a worker for automatic cleanup."""
        self._active_workers.append(worker)
        worker.finished.connect(lambda: self._unregister_worker(worker))
    
    def _unregister_worker(self, worker):
        """Remove worker from tracking list."""
        if worker in self._active_workers:
            self._active_workers.remove(worker)

    def stop_all_workers(self):
        """Stop all active workers - called on widget destruction."""
        for worker in list(self._active_workers):
            try:
                if worker.isRunning():
                    worker.stop()
                    worker.wait(1000)
            except Exception:
                pass
        self._active_workers.clear()
        self.worker = None

    def closeEvent(self, event):
        """Clean up workers when the widget is closed."""
        self.stop_all_workers()
        super().closeEvent(event)

    def _on_scan_completed(self):
        """Reset UI state after scan completes or stops."""
        try:
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
        except Exception:
            pass
        self.worker = None
        if self.main_window:
            self.main_window.active_process = None

    # ==================== UTILITY METHODS ====================

    def _notify(self, message):
        if self.main_window:
            self.main_window.notification_manager.notify(message)

    def _info(self, message):
        self.output.appendHtml(f'<span style="color:#60A5FA;">[INFO]</span> {message}')

    def _error(self, message):
        self.output.appendHtml(f'<span style="color:#F87171;">[ERROR]</span> {message}')

    def _section(self, title):
        self.output.appendHtml(f'<br><span style="color:#FACC15;font-weight:700;">===== {title} =====</span><br>')

