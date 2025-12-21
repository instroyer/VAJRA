from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QFrame
)
from PySide6.QtCore import Qt, QEvent, QDateTime


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
