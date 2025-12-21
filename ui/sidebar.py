from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal


class Sidebar(QWidget):
    automation_clicked = Signal()
    whois_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedWidth(260)
        self.active_button = None
        self._build_ui()

    def _build_ui(self):
        # 🔴 DIFFERENT METHOD: darker bg + border separation
        self.setStyleSheet("""
            QWidget {
                background-color: #02040A;
                border-right: 1px solid #1F2937;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(8)

        # ===== TOOLS =====
        tools_label = QLabel("TOOLS")
        tools_label.setStyleSheet(
            "color:#60A5FA;font-size:20px;font-weight:900;"
        )
        layout.addWidget(tools_label)

        self.btn_automation = self._tool_button("Automation")
        self.btn_automation.clicked.connect(
            lambda: self._activate(self.btn_automation, self.automation_clicked)
        )
        layout.addWidget(self.btn_automation)

        # ===== RECON =====
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

        # ===== RECON CONTAINER =====
        self.recon_container = QWidget()
        recon_layout = QVBoxLayout(self.recon_container)
        recon_layout.setContentsMargins(20, 4, 0, 4)
        recon_layout.setSpacing(6)

        self.btn_whois = self._sub_tool_button("Whois")
        self.btn_whois.clicked.connect(
            lambda: self._activate(self.btn_whois, self.whois_clicked)
        )
        recon_layout.addWidget(self.btn_whois)

        recon_layout.addWidget(self._sub_tool_button("Dnsenum"))
        recon_layout.addWidget(self._sub_tool_button("Subfinder"))

        self.recon_container.setVisible(True)
        layout.addWidget(self.recon_container)

        layout.addStretch()

    # =========================
    # TOGGLE
    # =========================
    def _toggle_recon(self):
        visible = self.recon_container.isVisible()
        self.recon_container.setVisible(not visible)
        self.recon_toggle.setText("RECON  ▸" if visible else "RECON  ▾")

    # =========================
    # ACTIVE STATE
    # =========================
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

    # =========================
    # BUTTON STYLES
    # =========================
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
