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
    QFrame,
    QLineEdit,
    QScrollArea
)
from PySide6.QtCore import Qt, QDateTime
import os
import platform


# =============================================================================
# Privilege Manager - Handles privilege escalation for tools requiring root
# =============================================================================

class PrivilegeManager:
    """
    Manages privilege escalation for security tools requiring root access.
    
    Supports three modes:
    - none: No privilege escalation
    - sudo: Use sudo with stored password (Linux/Unix)
    - pkexec: Use PolicyKit GUI prompt (Linux)
    """
    
    def __init__(self):
        self.mode = "none"  # "none", "sudo", "pkexec"
        self.sudo_password = None
        self._is_windows = platform.system() == "Windows"
    
    def set_mode(self, mode: str):
        """Set privilege escalation mode"""
        if mode not in ["none", "sudo", "pkexec"]:
            raise ValueError(f"Invalid mode: {mode}")
        self.mode = mode
    
    def set_sudo_password(self, password: str):
        """Store sudo password (kept in memory only)"""
        self.sudo_password = password
    
    def clear_password(self):
        """Clear stored password from memory"""
        self.sudo_password = None
    
    def needs_privilege_escalation(self) -> bool:
        """Check if privilege escalation is enabled"""
        return self.mode != "none"
    
    def wrap_command(self, command: list) -> list:
        """
        Wrap command with privilege escalation wrapper if needed.
        
        Args:
            command: Original command as list (e.g., ['nmap', '-sS', 'target'])
        
        Returns:
            Wrapped command list
        """
        if self._is_windows:
            # Windows doesn't support sudo/pkexec
            return command
        
        if self.mode == "sudo":
            # Use sudo -S to read password from stdin
            return ['sudo', '-S'] + command
        elif self.mode == "pkexec":
            # Use PolicyKit for GUI password prompt
            return ['pkexec'] + command
        else:
            # No escalation
            return command
    
    def get_stdin_data(self) -> str:
        """
        Get password data for stdin injection.
        
        Returns:
            Password string with newline for sudo -S
        """
        if self.mode == "sudo" and self.sudo_password:
            return f"{self.sudo_password}\n"
        return ""
    
    def check_if_root(self) -> bool:
        """
        Check if currently running as root/admin.
        
        Returns:
            True if running with elevated privileges
        """
        if self._is_windows:
            # Windows admin check would require ctypes
            return False
        else:
            # Unix-like systems
            return os.geteuid() == 0
    
    def get_status_message(self) -> str:
        """Get human-readable status message"""
        if self.mode == "none":
            return "Privilege escalation disabled"
        elif self.mode == "sudo":
            has_password = "configured" if self.sudo_password else "not configured"
            return f"Using sudo (password {has_password})"
        elif self.mode == "pkexec":
            return "Using PolicyKit (GUI prompts)"
        return "Unknown mode"


# Global privilege manager instance
privilege_manager = PrivilegeManager()


class SettingsPanel(QWidget):
    """
    Settings panel for VAJRA application (opens as a tab).
    - Privilege escalation settings
    - Output directory settings
    - Tool configurations
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1C1C1C;
                color: white;
            }
            QLabel {
                font-size: 13px;
            }
            QCheckBox {
                color: white;
                spacing: 8px;
                font-size: 13px;
            }
            QSpinBox {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #333333;
                padding: 6px;
                border-radius: 4px;
                font-size: 13px;
            }
            QComboBox {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #333333;
                padding: 6px;
                border-radius: 4px;
                font-size: 13px;
            }
            QLineEdit {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #333333;
                padding: 8px;
                border-radius: 4px;
                font-size: 13px;
            }
        """)

        # Main scroll area for all settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header
        header = QLabel("⚙️ Settings")
        header.setStyleSheet("font-size: 24px; font-weight: 600; color: #58A6FF;")
        layout.addWidget(header)
        
        layout.addWidget(self._divider())

        # ===== PRIVILEGE ESCALATION =====
        privilege_section = QLabel("🔐 Privilege Escalation")
        privilege_section.setStyleSheet("font-size: 18px; font-weight: 600; color: #58A6FF;")
        layout.addWidget(privilege_section)

        # Checkbox and password field on one line
        sudo_layout = QHBoxLayout()
        sudo_layout.setSpacing(15)
        
        self.enable_sudo_check = QCheckBox("Enable sudo:")
        self.enable_sudo_check.setStyleSheet("font-size: 14px; font-weight: 500;")
        sudo_layout.addWidget(self.enable_sudo_check)
        
        self.sudo_password_input = QLineEdit()
        self.sudo_password_input.setEchoMode(QLineEdit.Password)
        self.sudo_password_input.setPlaceholderText("Enter your login password (for sudo)")
        self.sudo_password_input.setEnabled(False)
        self.sudo_password_input.setFixedWidth(300)
        sudo_layout.addWidget(self.sudo_password_input)
        
        sudo_layout.addStretch()
        layout.addLayout(sudo_layout)

        # Connect checkbox to enable/disable password field
        self.enable_sudo_check.toggled.connect(self._on_sudo_toggled)
        
        layout.addWidget(self._divider())
        
        # ===== CONSOLIDATED TIPS & INFO BOX =====
        info_section = QLabel("ℹ️ Tips & Information")
        info_section.setStyleSheet("font-size: 18px; font-weight: 600; color: #58A6FF;")
        layout.addWidget(info_section)
        
        tips_box = QFrame()
        tips_box.setStyleSheet("""
            QFrame {
                background-color: #21262D;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        tips_box_layout = QVBoxLayout(tips_box)
        tips_box_layout.setContentsMargins(14, 12, 14, 12)
        tips_box_layout.setSpacing(10)
        
        # All tips in one box
        tips = [
            "� <b>Output Directory:</b> /tmp/Vajra-results",
            "💡 <b>Sudo:</b> On Kali Linux, most nmap scans work without sudo. Only enable if you get permission errors.",
            "⚠️ <b>Password:</b> Stored in memory only. Cleared when app closes. Enter here or during scan.",
        ]
        
        for tip in tips:
            tip_label = QLabel(tip)
            tip_label.setStyleSheet("color: #8B949E; font-size: 12px; background: transparent; border: none;")
            tip_label.setWordWrap(True)
            tip_label.setTextFormat(Qt.RichText)
            tips_box_layout.addWidget(tip_label)
        
        layout.addWidget(tips_box)

        layout.addStretch()

        # Save button
        save_btn = QPushButton("💾 Save Settings")
        save_btn.setFixedHeight(45)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: white;
                border-radius: 6px;
                padding: 10px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2EA043;
            }
            QPushButton:pressed {
                background-color: #1A7F37;
            }
        """)
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

        scroll.setWidget(scroll_widget)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #21262D; min-height: 1px; max-height: 1px;")
        return line
    
    def _on_sudo_toggled(self, checked):
        """Enable/disable password field based on checkbox"""
        self.sudo_password_input.setEnabled(checked)
        if not checked:
            self.sudo_password_input.clear()
    
    def _save_settings(self):
        """Save all settings and apply privilege escalation configuration"""
        global privilege_manager
        
        # Apply privilege escalation settings
        if self.enable_sudo_check.isChecked():
            privilege_manager.set_mode("sudo")
            password = self.sudo_password_input.text()
            if password:
                # User entered a new password in settings
                privilege_manager.set_sudo_password(password)
            # If password field is empty, DON'T clear any existing password
            # (it may have been entered via popup during a scan)
        else:
            # Only clear password when sudo is disabled
            privilege_manager.set_mode("none")
            privilege_manager.clear_password()
        
        # Show confirmation with detailed status
        from PySide6.QtWidgets import QMessageBox
        status = privilege_manager.get_status_message()
        QMessageBox.information(
            self,
            "Settings Saved",
            f"Settings saved successfully!\n\nPrivilege Status: {status}"
        )
    
    def showEvent(self, event):
        """Update UI when settings panel is shown."""
        super().showEvent(event)
        # Sync checkbox with current mode
        is_sudo_enabled = privilege_manager.mode == "sudo"
        self.enable_sudo_check.setChecked(is_sudo_enabled)
        self.sudo_password_input.setEnabled(is_sudo_enabled)
        
        # Show password status as placeholder
        if privilege_manager.sudo_password:
            self.sudo_password_input.setPlaceholderText("Password configured ✓ (leave blank to keep)")
        else:
            self.sudo_password_input.setPlaceholderText("Enter your login password (for sudo)")

