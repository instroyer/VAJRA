from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal


class Sidebar(QWidget):
    automation_clicked = Signal()
    whois_clicked = Signal()
    amass_clicked = Signal()
    subfinder_clicked = Signal()
    httpx_clicked = Signal()
    nmap_clicked = Signal()
    screenshot_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedWidth(260)
        self.active_button = None
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #02040A;
                border-right: 1px solid #1F2937;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(8)

        tools_label = QLabel("TOOLS")
        tools_label.setStyleSheet(
            "color:#60A5FA;font-size:20px;font-weight:900;"
        )
        layout.addWidget(tools_label)

        self.btn_automation = self._tool_button("Automation")
        self.btn_automation.clicked.connect(self.automation_clicked.emit)
        layout.addWidget(self.btn_automation)

        self.recon_toggle = QPushButton("RECON  ▾")
        self.recon_toggle.setCursor(Qt.PointingHandCursor)
        self.recon_toggle.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                color: #FACC15;
                font-size: 20px;
                font-weight: 900;
                text-align: left;
                border: none;
                padding: 6px 0;
            }
            QPushButton:hover {
                color: #FDE047;
            }
            """
        )
        self.recon_toggle.clicked.connect(self._toggle_recon)
        layout.addWidget(self.recon_toggle)

        self.recon_container = QWidget()
        recon_layout = QVBoxLayout(self.recon_container)
        recon_layout.setContentsMargins(20, 4, 0, 4)
        recon_layout.setSpacing(6)

        self.btn_whois = self._sub_tool_button("Whois")
        self.btn_whois.clicked.connect(self.whois_clicked.emit)
        recon_layout.addWidget(self.btn_whois)

        self.recon_container.setVisible(True)
        layout.addWidget(self.recon_container)

        self.subdomain_toggle = QPushButton("SUBDOMAIN ENUMERATION  ▾")
        self.subdomain_toggle.setCursor(Qt.PointingHandCursor)
        self.subdomain_toggle.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                color: #FACC15;
                font-size: 20px;
                font-weight: 900;
                text-align: left;
                border: none;
                padding: 6px 0;
            }
            QPushButton:hover {
                color: #FDE047;
            }
            """
        )
        self.subdomain_toggle.clicked.connect(self._toggle_subdomain)
        layout.addWidget(self.subdomain_toggle)

        self.subdomain_container = QWidget()
        subdomain_layout = QVBoxLayout(self.subdomain_container)
        subdomain_layout.setContentsMargins(20, 4, 0, 4)
        subdomain_layout.setSpacing(6)

        self.btn_amass = self._sub_tool_button("Amass")
        self.btn_amass.clicked.connect(self.amass_clicked.emit)
        subdomain_layout.addWidget(self.btn_amass)

        self.btn_subfinder = self._sub_tool_button("Subfinder")
        self.btn_subfinder.clicked.connect(self.subfinder_clicked.emit)
        subdomain_layout.addWidget(self.btn_subfinder)

        self.live_enum_toggle = QPushButton("Live Enumeration  ▾")
        self.live_enum_toggle.setCursor(Qt.PointingHandCursor)
        self.live_enum_toggle.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                color: #60A5FA;
                font-size: 14px;
                font-weight: 700;
                text-align: left;
                border: none;
                padding: 6px 0;
                margin-top: 6px;
            }
            QPushButton:hover {
                color: #93C5FD;
            }
            """
        )
        self.live_enum_toggle.clicked.connect(self._toggle_live_enum)
        subdomain_layout.addWidget(self.live_enum_toggle)

        self.live_enum_container = QWidget()
        live_enum_layout = QVBoxLayout(self.live_enum_container)
        live_enum_layout.setContentsMargins(30, 4, 0, 4)
        live_enum_layout.setSpacing(6)

        self.btn_httpx = self._sub_tool_button("HTTPX")
        self.btn_httpx.clicked.connect(self.httpx_clicked.emit)
        live_enum_layout.addWidget(self.btn_httpx)

        self.live_enum_container.setVisible(True)
        subdomain_layout.addWidget(self.live_enum_container)

        self.subdomain_container.setVisible(True)
        layout.addWidget(self.subdomain_container)

        self.scan_toggle = QPushButton("SCAN  ▾")
        self.scan_toggle.setCursor(Qt.PointingHandCursor)
        self.scan_toggle.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                color: #FACC15;
                font-size: 20px;
                font-weight: 900;
                text-align: left;
                border: none;
                padding: 6px 0;
            }
            QPushButton:hover {
                color: #FDE047;
            }
            """
        )
        self.scan_toggle.clicked.connect(self._toggle_scan)
        layout.addWidget(self.scan_toggle)

        self.scan_container = QWidget()
        scan_layout = QVBoxLayout(self.scan_container)
        scan_layout.setContentsMargins(20, 4, 0, 4)
        scan_layout.setSpacing(6)

        self.btn_nmap = self._sub_tool_button("Nmap")
        self.btn_nmap.clicked.connect(self.nmap_clicked.emit)
        scan_layout.addWidget(self.btn_nmap)

        self.scan_container.setVisible(True)
        layout.addWidget(self.scan_container)

        self.screenshot_toggle = QPushButton("SCREENSHOT  ▾")
        self.screenshot_toggle.setCursor(Qt.PointingHandCursor)
        self.screenshot_toggle.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                color: #FACC15;
                font-size: 20px;
                font-weight: 900;
                text-align: left;
                border: none;
                padding: 6px 0;
            }
            QPushButton:hover {
                color: #FDE047;
            }
            """
        )
        self.screenshot_toggle.clicked.connect(self._toggle_screenshot)
        layout.addWidget(self.screenshot_toggle)

        self.screenshot_container = QWidget()
        screenshot_layout = QVBoxLayout(self.screenshot_container)
        screenshot_layout.setContentsMargins(20, 4, 0, 4)
        screenshot_layout.setSpacing(6)

        self.btn_screenshot = self._sub_tool_button("Screenshot")
        self.btn_screenshot.clicked.connect(self.screenshot_clicked.emit)
        screenshot_layout.addWidget(self.btn_screenshot)

        self.screenshot_container.setVisible(True)
        layout.addWidget(self.screenshot_container)

        layout.addStretch()

    def _toggle_recon(self):
        visible = self.recon_container.isVisible()
        self.recon_container.setVisible(not visible)
        self.recon_toggle.setText("RECON  ▸" if visible else "RECON  ▾")

    def _toggle_subdomain(self):
        visible = self.subdomain_container.isVisible()
        self.subdomain_container.setVisible(not visible)
        self.subdomain_toggle.setText("SUBDOMAIN ENUMERATION  ▸" if visible else "SUBDOMAIN ENUMERATION  ▾")

    def _toggle_live_enum(self):
        visible = self.live_enum_container.isVisible()
        self.live_enum_container.setVisible(not visible)
        self.live_enum_toggle.setText("Live Enumeration  ▸" if visible else "Live Enumeration  ▾")

    def _toggle_scan(self):
        visible = self.scan_container.isVisible()
        self.scan_container.setVisible(not visible)
        self.scan_toggle.setText("SCAN  ▸" if visible else "SCAN  ▾")

    def _toggle_screenshot(self):
        visible = self.screenshot_container.isVisible()
        self.screenshot_container.setVisible(not visible)
        self.screenshot_toggle.setText("SCREENSHOT  ▸" if visible else "SCREENSHOT  ▾")

    def _tool_button(self, text):
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                color: #E5E7EB;
                font-size: 15px;
                padding: 8px 10px;
                border-radius: 6px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #1E293B;
            }
            QPushButton[active="true"] {
                background-color: #2563EB;
                color: white;
            }
            """
        )
        return btn

    def _sub_tool_button(self, text):
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                color: #CBD5E1;
                font-size: 14px;
                padding: 6px 8px;
                border-radius: 6px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #1E293B;
            }
            QPushButton[active="true"] {
                background-color: #2563EB;
                color: white;
            }
            """
        )
        return btn

    def toggle(self):
        self.setVisible(not self.isVisible())

    def _activate(self, button, signal):
        if self.active_button:
            self.active_button.setProperty("active", False)
            self.active_button.style().unpolish(self.active_button)
            self.active_button.style().polish(self.active_button)

        self.active_button = button
        button.setProperty("active", True)
        button.style().unpolish(button)
        button.style().polish(button)

        signal.emit()
