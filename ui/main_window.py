from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton
)
from PySide6.QtCore import Qt

from ui.sidebar import Sidebar
from ui.automation_view import AutomationView
from ui.toolui.whois_view import WhoisView
from ui.notifications.panel import NotificationPanel
from ui.notifications.manager import NotificationManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VAJRA – Offensive Security Platform")
        self.setMinimumSize(1200, 720)

        # Global execution tracking (logic unchanged)
        self.active_process = None
        self.active_process_type = None

        self._build_ui()

    def _build_ui(self):
        # ===== ROOT =====
        central = QWidget()
        central.setStyleSheet("background-color: #0B1220;")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ===== TOP BAR =====
        top_bar = QWidget()
        top_bar.setFixedHeight(58)
        top_bar.setStyleSheet("""
            background-color: #0F172A;
            border-bottom: 1px solid #1E293B;
        """)

        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 0, 16, 0)

        toggle_btn = QPushButton("☰")
        toggle_btn.setFixedSize(36, 36)
        toggle_btn.setStyleSheet("""
            QPushButton {
                color: #E5E7EB;
                background: transparent;
                border: none;
                font-size: 18px;
            }
            QPushButton:hover {
                color: #93C5FD;
            }
        """)

        title = QLabel("VAJRA")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 40px;
                font-weight: 800;
                letter-spacing: 2px;
                color: #FFFFFF;
            }
        """)

        subtitle = QLabel("Offensive Security Platform")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #9CA3AF;
            }
        """)

        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        self.notification_btn = QPushButton("🔔")
        self.notification_btn.setFixedSize(32, 32)
        self.notification_btn.setStyleSheet("""
            QPushButton {
                color: #FACC15;
                background: transparent;
                border: none;
                font-size: 18px;
            }
            QPushButton:hover {
                color: #FDE047;
            }
        """)

        top_layout.addWidget(toggle_btn)
        top_layout.addStretch()
        top_layout.addWidget(title_container)
        top_layout.addStretch()
        top_layout.addWidget(self.notification_btn)

        root_layout.addWidget(top_bar)

        # ===== MAIN CONTENT =====
        content = QWidget()
        content.setStyleSheet("background-color: #0B1220;")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # ===== SIDEBAR =====
        self.sidebar = Sidebar()
        self.sidebar.setStyleSheet("""
            background-color: #020617;
            border-right: 1px solid #1E293B;
        """)
        content_layout.addWidget(self.sidebar)

        # ===== WORKSPACE =====
        self.workspace_container = QWidget()
        self.workspace_container.setStyleSheet("""
            background-color: #0B1220;
        """)
        self.workspace_layout = QVBoxLayout(self.workspace_container)
        self.workspace_layout.setContentsMargins(0, 0, 0, 0)
        self.workspace_layout.setSpacing(0)

        content_layout.addWidget(self.workspace_container)
        root_layout.addWidget(content)

        # ===== NOTIFICATIONS =====
        self.notification_panel = NotificationPanel(self)
        self.notification_manager = NotificationManager(self)

        self.notification_btn.clicked.connect(
            lambda: self.notification_panel.show_below(self.notification_btn)
        )

        # ===== INITIAL VIEW =====
        self.load_automation()

        # ===== SIGNALS =====
        toggle_btn.clicked.connect(self.sidebar.toggle)
        self.sidebar.automation_clicked.connect(self.load_automation)
        self.sidebar.whois_clicked.connect(self.load_whois)

    # ==================================================
    # GLOBAL STOP (LOGIC UNCHANGED)
    # ==================================================
    def stop_active_process(self):
        if self.active_process and self.active_process.poll() is None:
            self.active_process.kill()
            self.active_process = None
            self.active_process_type = None
            self.notification_manager.notify("Execution stopped")

    # ==================================================
    # VIEW LOADERS
    # ==================================================
    def _clear_workspace(self):
        while self.workspace_layout.count():
            item = self.workspace_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def load_automation(self):
        self._clear_workspace()
        self.workspace_layout.addWidget(
            AutomationView(main_window=self)
        )

    def load_whois(self):
        self._clear_workspace()
        self.workspace_layout.addWidget(
            WhoisView(main_window=self)
        )
