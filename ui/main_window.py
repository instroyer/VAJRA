from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTabBar
)
from PySide6.QtCore import Qt

from ui.sidebar import Sidebar
from modules.automation import AutomationView
from modules.whois import WhoisView
from modules.amass import AmassView
from modules.subfinder import SubfinderView
from modules.httpx import HttpxView
from modules.nmap import NmapView
from modules.screenshot import ScreenshotView
from ui.notification import NotificationPanel, NotificationManager
from ui.settingpanel import SettingsPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VAJRA – Offensive Security Platform")
        self.setMinimumSize(1200, 720)

        self.active_process = None
        self.active_process_type = None
        self.open_tabs = {}

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        central.setStyleSheet("background-color: #0B1220;")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

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
                color: #E5E7EB; background: transparent; border: none; font-size: 18px;
            }
            QPushButton:hover { color: #93C5FD; }
        """)

        title = QLabel("VAJRA")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 40px; font-weight: 800; letter-spacing: 2px; color: #FFFFFF;")

        subtitle = QLabel("Offensive Security Platform")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 13px; color: #9CA3AF;")

        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        self.notification_btn = QPushButton("🔔")
        self.notification_btn.setFixedSize(32, 32)
        self.notification_btn.setStyleSheet("""
            QPushButton { color: #FACC15; background: transparent; border: none; font-size: 18px; }
            QPushButton:hover { color: #FDE047; }
        """)

        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.setStyleSheet("""
            QPushButton { color: #9CA3AF; background: transparent; border: none; font-size: 18px; }
            QPushButton:hover { color: #E5E7EB; }
        """)

        top_layout.addWidget(toggle_btn)
        top_layout.addStretch()
        top_layout.addWidget(title_container)
        top_layout.addStretch()
        top_layout.addWidget(self.settings_btn)
        top_layout.addWidget(self.notification_btn)

        root_layout.addWidget(top_bar)

        content = QWidget()
        content.setStyleSheet("background-color: #0B1220;")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.sidebar = Sidebar()
        content_layout.addWidget(self.sidebar)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab {
                background: #0F172A; color: #9CA3AF; padding: 10px 20px;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
                border: 1px solid #1E293B; border-bottom: none; margin-right: 2px;
            }
            QTabBar::tab:selected { background: #0B1220; color: #E5E7EB; }
            QTabBar::tab:hover { background: #1E293B; }
        """)

        content_layout.addWidget(self.tabs)
        root_layout.addWidget(content)

        self.notification_panel = NotificationPanel(self)
        self.notification_manager = NotificationManager(self)
        self.notification_btn.clicked.connect(
            lambda: self.notification_panel.show_below(self.notification_btn)
        )

        self.settings_panel = SettingsPanel(self)
        self.settings_btn.clicked.connect(
            lambda: self.settings_panel.show_below(self.settings_btn)
        )

        self.load_automation()

        toggle_btn.clicked.connect(self.sidebar.toggle)
        self.sidebar.automation_clicked.connect(self.load_automation)
        self.sidebar.whois_clicked.connect(self.load_whois)
        self.sidebar.amass_clicked.connect(self.load_amass)
        self.sidebar.subfinder_clicked.connect(self.load_subfinder)
        self.sidebar.httpx_clicked.connect(self.load_httpx)
        self.sidebar.nmap_clicked.connect(self.load_nmap)
        self.sidebar.screenshot_clicked.connect(self.load_screenshot)

    def stop_active_process(self):
        if self.active_process and self.active_process.poll() is None:
            self.active_process.kill()
            self.active_process = None
            self.active_process_type = None
            self.notification_manager.notify("Execution stopped")

    def close_tab_for_widget(self, widget):
        index = self.tabs.indexOf(widget)
        if index != -1:
            self._close_tab(index)

    def _open_tab(self, name, widget_class):
        if name in self.open_tabs:
            self.tabs.setCurrentWidget(self.open_tabs[name])
        else:
            widget = widget_class(main_window=self)
            index = self.tabs.addTab(widget, name)
            self.tabs.setCurrentIndex(index)
            self.open_tabs[name] = widget

            close_button = QPushButton("×")
            close_button.setFixedSize(24, 24)
            close_button.setStyleSheet("""
                QPushButton {
                    color: #eaeaea;
                    background: transparent;
                    border: none;
                    font-size: 20px;
                    font-weight: bold;
                }
                QPushButton:hover { color: #DC2626; }
                QPushButton:pressed { color: #B91C1C; }
            """)
            close_button.setCursor(Qt.PointingHandCursor)
            self.tabs.tabBar().setTabButton(index, QTabBar.RightSide, close_button)
            close_button.clicked.connect(lambda: self.close_tab_for_widget(widget))

    def _close_tab(self, index):
        widget = self.tabs.widget(index)
        if widget:
            for name, w in self.open_tabs.items():
                if w == widget:
                    del self.open_tabs[name]
                    break
            widget.deleteLater()
        self.tabs.removeTab(index)

    def load_automation(self):
        self._open_tab("Automation", AutomationView)

    def load_whois(self):
        self._open_tab("Whois", WhoisView)

    def load_amass(self):
        self._open_tab("Amass", AmassView)

    def load_subfinder(self):
        self._open_tab("Subfinder", SubfinderView)

    def load_httpx(self):
        self._open_tab("Httpx", HttpxView)

    def load_nmap(self):
        self._open_tab("Nmap", NmapView)

    def load_screenshot(self):
        self._open_tab("Screenshot", ScreenshotView)
