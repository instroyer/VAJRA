"""
VAJRA Settings Panel
Application settings and preferences
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QComboBox, QFrame, QLineEdit, QScrollArea,
    QTabWidget, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QDateTime
import os
import platform

from core.config import ConfigManager
from core.privileges import PrivilegeManager as CorePrivilegeManager


# =============================================================================
# Legacy Privilege Manager (Compat for unrefactored tools)
# =============================================================================

class LegacyPrivilegeManager:
    def __init__(self):
        self.mode = "none"
        self.sudo_password = None
    
    def set_mode(self, mode): self.mode = mode
    def set_sudo_password(self, password): self.sudo_password = password
    def clear_password(self): self.sudo_password = None
    def needs_privilege_escalation(self): return False
    def wrap_command(self, command): return command
    def wrap_command_str(self, cmd_str): return cmd_str # Added for compat
    def get_stdin_data(self): return ""
    def check_if_root(self): return CorePrivilegeManager.is_root()
    def get_status_message(self): return "Managed by Platform"

# Instance for compatibility
privilege_manager = LegacyPrivilegeManager()


# =============================================================================
# New Settings Panel
# =============================================================================

class SettingsPanel(QWidget):
    """
    Settings panel for VAJRA application (opens as a tab).
    Uses ConfigManager for persistence.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #1C1C1C; color: white; }
            QLabel { font-size: 13px; }
            QCheckBox { color: white; spacing: 8px; font-size: 13px; }
            QLineEdit { background-color: #3C3C3C; color: white; border: 1px solid #333333; padding: 8px; border-radius: 4px; }
            QPushButton { background-color: #3C3C3C; border: 1px solid #333333; padding: 6px 12px; border-radius: 4px; color: white; }
            QPushButton:hover { background-color: #4A4A4A; }
            QTabWidget::pane { border: 1px solid #333333; background: #1C1C1C; }
            QTabBar::tab { background: #2D2D2D; color: #888; padding: 8px 12px; border: 1px solid #333333; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
            QTabBar::tab:selected { background: #1C1C1C; color: white; border-bottom: 2px solid #58A6FF; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        header = QLabel("⚙️ Settings")
        header.setStyleSheet("font-size: 24px; font-weight: 600; color: #58A6FF;")
        layout.addWidget(header)
        layout.addSpacing(20)

        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # TAB 1: General
        self.tab_general = QWidget()
        self._build_general_tab()
        self.tabs.addTab(self.tab_general, "General")

        # TAB 2: Paths
        self.tab_paths = QWidget()
        self._build_paths_tab()
        self.tabs.addTab(self.tab_paths, "Paths")

        # TAB 3: Privileges
        self.tab_privileges = QWidget()
        self._build_privileges_tab()
        self.tabs.addTab(self.tab_privileges, "Privileges")

        # TAB 4: User Guide
        self.tab_guide = QWidget()
        self._build_guide_tab()
        self.tabs.addTab(self.tab_guide, "User Guide")

        # Footer Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        save_btn = QPushButton("💾 Save Settings")
        save_btn.setStyleSheet("background-color: #238636; border: none; font-weight: bold;")
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)

    def _build_general_tab(self):
        layout = QVBoxLayout(self.tab_general)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(15)

        self.chk_notify = QCheckBox("Enable Notifications")
        self.chk_notify.setToolTip("Show toast notifications when tools finish.")
        layout.addWidget(self.chk_notify)

    def _build_paths_tab(self):
        layout = QVBoxLayout(self.tab_paths)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Session Output Directory (Resets on Restart):"))
        
        row = QHBoxLayout()
        self.txt_output_dir = QLineEdit()
        self.txt_output_dir.setReadOnly(True)
        row.addWidget(self.txt_output_dir)
        
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse_output_dir)
        row.addWidget(btn_browse)
        
        layout.addLayout(row)
        layout.addWidget(QLabel("<small style='color:#f1c40f'>Note: This path resets to default <b>/tmp/Vajra-results</b> when you restart the app.</small>"))

    def _build_privileges_tab(self):
        layout = QVBoxLayout(self.tab_privileges)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(20)

        # Status
        status_box = QFrame()
        status_box.setStyleSheet("background: #252525; border-radius: 6px; padding: 15px;")
        sb_layout = QHBoxLayout(status_box)
        
        is_root = CorePrivilegeManager.is_root()
        icon = "✅" if is_root else "⚠️"
        text = "Running as Root (Privileged)" if is_root else "Running as Standard User"
        color = "#2ecc71" if is_root else "#f1c40f"
        
        lbl_status = QLabel(f"<span style='font-size:16px; font-weight:bold; color:{color}'>{icon} {text}</span>")
        sb_layout.addWidget(lbl_status)
        layout.addWidget(status_box)

        # Info
        info_text = """
        <h3>Privileges Explanation</h3>
        <p>Some tools (like Nmap SYN scan, hping3) require raw socket access, which needs <b>Root / Administrator</b> privileges.</p>
        <p><b>VAJRA does NOT use sudo internally.</b></p>
        <p>If you need to run privileged tools, please restart VAJRA with sudo:</p>
        <pre style='background:#111; padding:10px;'>sudo python3 main.py</pre>
        """
        lbl_info = QLabel(info_text)
        lbl_info.setWordWrap(True)
        lbl_info.setTextFormat(Qt.RichText)
        lbl_info.setStyleSheet("color: #ccc; font-size: 14px; line-height: 1.4;")
        layout.addWidget(lbl_info)

    def _build_guide_tab(self):
        layout = QVBoxLayout(self.tab_guide)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;")
        
        content = QWidget()
        c_layout = QVBoxLayout(content)
        
        guide_md = """
        ## How VAJRA Works
        
        **1. Tool Execution**
        Select a tool, enter targets, and click RUN. 
        VAJRA manages the process and saves results automatically.

        **2. Output Organization**
        Results are saved to your configurable Output Path.
        **Important:** The output path is **Session-Only**. It resets to `/tmp/Vajra-results` every time you restart the app.

        **3. Notifications**
        You will be notified when a long-running scan completes.

        **4. Stopping Tools**
        Use the Stop button to gracefully terminate a generic tool.
        """
        
        lbl = QLabel(guide_md)
        lbl.setWordWrap(True) # Markdown rendering is limited in QLabel but basic formatting works
        lbl.setTextFormat(Qt.MarkdownText)
        lbl.setStyleSheet("font-size: 14px; color: #ddd;")
        c_layout.addWidget(lbl)
        c_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _load_settings(self):
        self.chk_notify.setChecked(ConfigManager.get_notifications_enabled())
        self.txt_output_dir.setText(str(ConfigManager.get_output_dir()))

    def _browse_output_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.txt_output_dir.text())
        if d:
            self.txt_output_dir.setText(d)

    def _save_settings(self):
        ConfigManager.set_notifications_enabled(self.chk_notify.isChecked())
        ConfigManager.set_output_dir(self.txt_output_dir.text())
        
        QMessageBox.information(self, "Settings Saved", "Configuration updated successfully.<br>Output path set for <b>this session only</b>.")
