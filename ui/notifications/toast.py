from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout
)
from PySide6.QtCore import Qt, QTimer


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
