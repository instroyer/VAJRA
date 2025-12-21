"""
VAJRA Notification System
Consolidated notification components: Toast, Manager, and Panel
"""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QFrame
)
from PySide6.QtCore import Qt, QTimer, QEvent, QDateTime


# =====================================================
# TOAST NOTIFICATION
# =====================================================
class ToastNotification(QWidget):
    """
    Small auto-hide notification popup.
    - Auto closes after 2 seconds
    - Manual close (✕)
    - UI-only
    """

    def __init__(self, message: str, parent=None, duration_ms=2000):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._build_ui(message)

        # Auto-close timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close)
        self.timer.start(duration_ms)

    def _build_ui(self, message: str):
        container = QWidget(self)
        container.setStyleSheet(
            """
            QWidget {
                background-color: #1F2933;
                border-radius: 8px;
            }
            """
        )

        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        label = QLabel(message)
        label.setStyleSheet(
            """
            QLabel {
                color: white;
                font-size: 14px;
            }
            """
        )

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet(
            """
            QPushButton {
                border: none;
                color: #9CA3AF;
                font-size: 14px;
            }
            QPushButton:hover {
                color: white;
            }
            """
        )
        close_btn.clicked.connect(self.close)

        layout.addWidget(label)
        layout.addWidget(close_btn)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(container)

        self.adjustSize()

    def show_at_bottom_right(self):
        """
        Positions the toast at bottom-right of the parent window.
        """
        if not self.parent():
            return

        parent_geom = self.parent().geometry()
        x = parent_geom.x() + parent_geom.width() - self.width() - 20
        y = parent_geom.y() + parent_geom.height() - self.height() - 20

        self.move(x, y)
        self.show()


# =====================================================
# NOTIFICATION PANEL
# =====================================================
class NotificationPanel(QWidget):
    """
    Notification history panel.
    - Opens from 🔔 icon
    - Lists notifications
    - Each item removable
    - Auto-hides on focus loss
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setFixedWidth(320)

        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(
            """
            QWidget {
                background-color: #161B22;
                color: white;
            }
            QLabel {
                font-size: 14px;
            }
            QPushButton {
                border: none;
                background: transparent;
                color: #9CA3AF;
            }
            QPushButton:hover {
                color: white;
            }
            """
        )

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)

        header = QLabel("Notifications")
        header.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: 600;
            }
            """
        )

        self.layout.addWidget(header)
        self.layout.addWidget(self._divider())

        self.list_container = QVBoxLayout()
        self.list_container.setSpacing(6)

        self.layout.addLayout(self.list_container)

        self.layout.addStretch()

    def _divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #2A2F36;")
        return line

    def add_notification(self, message: str):
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")

        item = QWidget()
        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(6, 4, 6, 4)
        item_layout.setSpacing(6)

        text = QLabel(f"{message}\n{timestamp}")
        text.setStyleSheet("font-size: 13px;")

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(16, 16)
        close_btn.clicked.connect(item.deleteLater)

        item_layout.addWidget(text)
        item_layout.addStretch()
        item_layout.addWidget(close_btn)

        self.list_container.addWidget(item)

    def show_below(self, anchor_widget):
        """
        Shows panel below the given widget (🔔 icon).
        """
        global_pos = anchor_widget.mapToGlobal(anchor_widget.rect().bottomLeft())
        self.move(global_pos.x() - self.width() + anchor_widget.width(), global_pos.y())
        self.show()

    def focusOutEvent(self, event):
        self.hide()
        super().focusOutEvent(event)


# =====================================================
# NOTIFICATION MANAGER
# =====================================================
class NotificationManager:
    """
    Central notification manager.
    - Shows toast notifications
    - Adds entries to notification panel
    - UI-only (no engine dependency)
    """

    def __init__(self, main_window):
        self.main_window = main_window
        self.panel = main_window.notification_panel

    def notify(self, message: str):
        """
        Send a notification:
        - Show toast (2 sec)
        - Add to notification panel
        """

        # Add to panel (history)
        self.panel.add_notification(message)

        # Show toast
        toast = ToastNotification(message, parent=self.main_window)
        toast.show_at_bottom_right()
