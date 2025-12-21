"""
VAJRA Settings Panel
Application settings and preferences
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QComboBox,
    QFrame
)
from PySide6.QtCore import Qt, QDateTime


class SettingsPanel(QWidget):
    """
    Settings panel for VAJRA application.
    - Output directory settings
    - Tool timeouts
    - Display preferences
    - Auto-hides on focus loss
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setFixedWidth(380)

        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(
            """
            QWidget {
                background-color: #161B22;
                color: white;
            }
            QLabel {
                font-size: 13px;
            }
            QPushButton {
                border: none;
                background: transparent;
                color: #9CA3AF;
            }
            QPushButton:hover {
                color: white;
            }
            QCheckBox {
                color: white;
                spacing: 8px;
            }
            QSpinBox {
                background-color: #0F172A;
                color: white;
                border: 1px solid #1E293B;
                padding: 4px;
                border-radius: 4px;
            }
            QComboBox {
                background-color: #0F172A;
                color: white;
                border: 1px solid #1E293B;
                padding: 4px;
                border-radius: 4px;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Header
        header = QLabel("⚙️ Settings")
        header.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: 600;
            }
            """
        )
        layout.addWidget(header)
        layout.addWidget(self._divider())

        # ===== SCAN SETTINGS =====
        scan_label = QLabel("Scan Settings")
        scan_label.setStyleSheet("font-weight: 600; color: #60A5FA;")
        layout.addWidget(scan_label)

        # Timeout setting
        timeout_layout = QHBoxLayout()
        timeout_layout.setSpacing(10)
        timeout_layout.addWidget(QLabel("Default Timeout (seconds):"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setValue(300)
        self.timeout_spin.setMinimum(30)
        self.timeout_spin.setMaximum(3600)
        self.timeout_spin.setFixedWidth(80)
        timeout_layout.addWidget(self.timeout_spin)
        timeout_layout.addStretch()
        layout.addLayout(timeout_layout)

        # Parallel scanning
        self.parallel_check = QCheckBox("Enable Parallel Scanning")
        self.parallel_check.setChecked(False)
        layout.addWidget(self.parallel_check)

        # Thread count
        threads_layout = QHBoxLayout()
        threads_layout.setSpacing(10)
        threads_layout.addWidget(QLabel("Max Threads:"))
        self.threads_spin = QSpinBox()
        self.threads_spin.setValue(4)
        self.threads_spin.setMinimum(1)
        self.threads_spin.setMaximum(16)
        self.threads_spin.setFixedWidth(80)
        threads_layout.addWidget(self.threads_spin)
        threads_layout.addStretch()
        layout.addLayout(threads_layout)

        layout.addWidget(self._divider())

        # ===== OUTPUT SETTINGS =====
        output_label = QLabel("Output Settings")
        output_label.setStyleSheet("font-weight: 600; color: #60A5FA;")
        layout.addWidget(output_label)

        # Save reports
        self.reports_check = QCheckBox("Auto-generate HTML Reports")
        self.reports_check.setChecked(True)
        layout.addWidget(self.reports_check)

        # Create JSON files
        self.json_check = QCheckBox("Export JSON Data")
        self.json_check.setChecked(True)
        layout.addWidget(self.json_check)

        # Output directory (display only)
        output_dir_layout = QHBoxLayout()
        output_dir_layout.setSpacing(10)
        output_dir_layout.addWidget(QLabel("Output Directory:"))
        output_dir_label = QLabel("/tmp/Vajra-results")
        output_dir_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        output_dir_layout.addWidget(output_dir_label)
        output_dir_layout.addStretch()
        layout.addLayout(output_dir_layout)

        layout.addWidget(self._divider())

        # ===== UI SETTINGS =====
        ui_label = QLabel("UI Preferences")
        ui_label.setStyleSheet("font-weight: 600; color: #60A5FA;")
        layout.addWidget(ui_label)

        # Auto-scroll
        self.autoscroll_check = QCheckBox("Auto-scroll Output")
        self.autoscroll_check.setChecked(True)
        layout.addWidget(self.autoscroll_check)

        # Notifications
        self.notify_check = QCheckBox("Show Notifications")
        self.notify_check.setChecked(True)
        layout.addWidget(self.notify_check)

        # Theme
        theme_layout = QHBoxLayout()
        theme_layout.setSpacing(10)
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark (Default)", "Light"])
        self.theme_combo.setFixedWidth(150)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)

        layout.addWidget(self._divider())

        # ===== TOOL SETTINGS =====
        tools_label = QLabel("Tool Settings")
        tools_label.setStyleSheet("font-weight: 600; color: #60A5FA;")
        layout.addWidget(tools_label)

        # Nmap aggressive
        self.nmap_aggressive_check = QCheckBox("Nmap: Enable Aggressive Scan")
        self.nmap_aggressive_check.setChecked(False)
        layout.addWidget(self.nmap_aggressive_check)

        # HTTP redirects
        self.follow_redirects_check = QCheckBox("HTTPX: Follow Redirects")
        self.follow_redirects_check.setChecked(True)
        layout.addWidget(self.follow_redirects_check)

        # Screenshot threads
        screenshot_threads_layout = QHBoxLayout()
        screenshot_threads_layout.setSpacing(10)
        screenshot_threads_layout.addWidget(QLabel("Screenshot Threads:"))
        self.screenshot_threads_spin = QSpinBox()
        self.screenshot_threads_spin.setValue(5)
        self.screenshot_threads_spin.setMinimum(1)
        self.screenshot_threads_spin.setMaximum(20)
        self.screenshot_threads_spin.setFixedWidth(80)
        screenshot_threads_layout.addWidget(self.screenshot_threads_spin)
        screenshot_threads_layout.addStretch()
        layout.addLayout(screenshot_threads_layout)

        layout.addStretch()

        # Save button
        save_btn = QPushButton("💾 Save Settings")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                border-radius: 6px;
                padding: 8px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)
        layout.addWidget(save_btn)

    def _divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #2A2F36;")
        return line

    def show_below(self, anchor_widget):
        """
        Shows panel below the given widget (⚙️ icon).
        """
        global_pos = anchor_widget.mapToGlobal(anchor_widget.rect().bottomLeft())
        self.move(global_pos.x() - self.width() + anchor_widget.width(), global_pos.y())
        self.show()

    def focusOutEvent(self, event):
        self.hide()
        super().focusOutEvent(event)

