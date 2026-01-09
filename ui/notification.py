
"""
VAJRA Notification System
Consolidated notification components: Toast, Manager, and Panel
"""

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QIcon

from ui.styles import (
    COLOR_BG_INPUT, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_BORDER_DEFAULT, FONT_FAMILY_UI,
    COLOR_BG_PRIMARY, COLOR_BG_SECONDARY
)


# =====================================================
# TOAST NOTIFICATION
# =====================================================
class ToastNotification(QWidget):
    """Small auto-hide notification popup."""
    def __init__(self, message: str, parent=None, duration_ms=3000):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._build_ui(message)
        QTimer.singleShot(duration_ms, self.close)

    def _build_ui(self, message: str):
        layout = QHBoxLayout(self)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_BG_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER_DEFAULT};
                border-radius: 6px;
                font-family: {FONT_FAMILY_UI};
            }}
        """)
        
        icon_label = QLabel("🔔")
        icon_label.setStyleSheet("border: none; font-size: 16px; background: transparent;")
        layout.addWidget(icon_label)

        text_label = QLabel(message)
        text_label.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(text_label)

        close_button = QPushButton("✕")
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.setStyleSheet(f"""
            QPushButton {{ 
                font-size: 14px; 
                border: none; 
                background: transparent;
                color: {COLOR_TEXT_SECONDARY};
            }}
            QPushButton:hover {{ color: {COLOR_TEXT_PRIMARY}; }}
        """)
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

    def show_at_bottom_right(self):
        if self.parent():
            # Use global screen coordinates for correct positioning
            parent_rect = self.parent().frameGeometry()
            self.adjustSize()
            global_pos = self.parent().mapToGlobal(self.parent().rect().bottomRight())
            x = global_pos.x() - self.width() - 20
            y = global_pos.y() - self.height() - 60  # Account for status bar
            self.move(x, y)
        self.show()

# =====================================================
# NOTIFICATION PANEL
# =====================================================
class NotificationPanel(QWidget):
    """A panel to display a list of notifications."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(350)
        self.setMaximumHeight(400)
        
        self._build_ui()

    def _build_ui(self):
        self.main_frame = QFrame()
        self.main_frame.setObjectName("main_frame")
        self.main_frame.setStyleSheet(f"""
            #main_frame {{
                background-color: {COLOR_BG_PRIMARY};
                border: 1px solid {COLOR_BORDER_DEFAULT};
                border-radius: 8px;
                font-family: {FONT_FAMILY_UI};
            }}
        """)
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0,0,0,0)
        outer_layout.addWidget(self.main_frame)

        panel_layout = QVBoxLayout(self.main_frame)
        panel_layout.setContentsMargins(0,0,0,0)
        panel_layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet(f"background-color: {COLOR_BG_INPUT}; border-bottom: 1px solid {COLOR_BORDER_DEFAULT}; border-top-left-radius: 8px; border-top-right-radius: 8px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15,10,15,10)
        
        title = QLabel("Notifications")
        title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 600; border: none; background: transparent;")
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                color: {COLOR_TEXT_SECONDARY};
                font-size: 12px;
                border: none;
                background: transparent;
            }}
            QPushButton:hover {{
                text-decoration: underline;
                color: {COLOR_TEXT_PRIMARY};
            }}
        """)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.clear_btn)
        
        # Content Area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background: transparent; border: none;")
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setContentsMargins(15, 10, 15, 10)
        self.content_layout.setSpacing(8)

        scroll_area.setWidget(self.content_widget)

        panel_layout.addWidget(header)
        panel_layout.addWidget(scroll_area)

        self.add_placeholder()

    def add_placeholder(self):
        self.clear_notifications()
        placeholder = QLabel("No new notifications")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; padding: 30px; border: none; background: transparent;")
        self.content_layout.addWidget(placeholder)
        self.clear_btn.setVisible(False)

    def add_notification(self, message: str):
        if not self.clear_btn.isVisible():
            # Remove placeholder
            while self.content_layout.count():
                child = self.content_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            self.clear_btn.setVisible(True)

        notification_widget = QLabel(message)
        notification_widget.setWordWrap(True)
        notification_widget.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TEXT_PRIMARY};
                background-color: {COLOR_BG_INPUT};
                border: 1px solid {COLOR_BORDER_DEFAULT};
                border-radius: 5px;
                padding: 10px;
            }}
        """)
        self.content_layout.insertWidget(0, notification_widget)

    def clear_notifications(self):
         # Using a while loop to safely delete all widgets in the layout
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                widget = child.widget()
                # Disconnect all signals to prevent callbacks on deleted objects
                # widget.disconnect() # Removed invalid call
                # Force immediate deletion instead of async deleteLater()
                widget.setParent(None)
                widget.deleteLater()  # Keep deleteLater for thread safety

        # Force Qt to process events to ensure cleanup happens
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

# =====================================================
# NOTIFICATION MANAGER
# =====================================================
class NotificationManager:
    """
    Central notification manager.
    - Shows toast notifications
    - Manages notification panel
    """
    def __init__(self, main_window):
        self.main_window = main_window
        self.notifications = []
        self.panel = NotificationPanel(parent=main_window)
        self.panel.clear_btn.clicked.connect(self.clear_all_notifications)

    def notify(self, message: str):
        """
        Send a notification:
        - Show toast (3 sec)
        - Add to notification panel
        """
        self.notifications.insert(0, message)
        self.panel.add_notification(message)

        self.show_toast(message)

    def show_toast(self, message: str):
        """Show a temporary toast notification without adding to history."""
        toast = ToastNotification(message, parent=self.main_window)
        toast.show_at_bottom_right()

    def clear_all_notifications(self):
        self.notifications.clear()
        self.panel.add_placeholder()

    def toggle_panel(self):
        if self.panel.isVisible():
            self.panel.hide()
        else:
            button = self.main_window.notification_btn
            pos = button.mapToGlobal(QPoint(0, button.height()))
            self.panel.move(pos.x() - self.panel.width() + button.width(), pos.y() + 5)
            self.panel.show()
