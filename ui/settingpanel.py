"""
VAJRA Settings Panel
Application settings and preferences
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QComboBox, QFrame, QLineEdit, QScrollArea,
    QTabWidget, QFileDialog, QMessageBox, QProgressBar
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

        # TAB 4: Tool Installer
        self.tab_installer = QWidget()
        self._build_installer_tab()
        self.tabs.addTab(self.tab_installer, "Tool Installer")

        # TAB 5: User Guide
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

    def _build_installer_tab(self):
        from core.tool_installer import ToolInstaller
        
        layout = QVBoxLayout(self.tab_installer)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Title
        title = QLabel("Security Tools Manager")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #58A6FF;")
        layout.addWidget(title)

        # Status
        self.installer = ToolInstaller()
        self._refresh_status()
        
        layout.addStretch()

    def _refresh_status(self):
        """Refresh the entire status display."""
        # Get fresh status
        stats = self.installer.get_installation_stats()
        installed_pct = int((stats["installed"] / stats["total"]) * 100) if stats["total"] > 0 else 0
        
        # Status text
        from ui.styles import (
            COLOR_SUCCESS, COLOR_WARNING, COLOR_CRITICAL, COLOR_TEXT_PRIMARY,
            COLOR_BG_INPUT, COLOR_BORDER_DEFAULT, COLOR_ACCENT_PRIMARY
        )
        
        # Status text colors
        if installed_pct == 100:
            status_text = "All Tools Installed"
            status_color = COLOR_SUCCESS
        elif installed_pct >= 50:
            status_text = "Some Tools Missing"
            status_color = "#f59e0b" # Custom Amber
        else:
            status_text = "Most Tools Missing"
            status_color = COLOR_CRITICAL
        
        # Update or create status label
        if not hasattr(self, 'stats_label'):
            self.stats_label = QLabel()
            self.tab_installer.layout().addWidget(self.stats_label)
        
        self.stats_label.setText(
            f"<div style='font-size: 16px; color: {status_color}; font-weight: bold;'>{status_text}</div>"
            f"<div style='font-size: 24px; color: white; font-weight: bold; margin: 10px 0;'>{stats['installed']}/{stats['total']} Tools</div>"
        )
        
        # Update or create progress bar
        if not hasattr(self, 'install_progress'):
            self.install_progress = QProgressBar()
            self.install_progress.setTextVisible(True)
            self.install_progress.setFixedHeight(25)
            self.install_progress.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid {COLOR_BORDER_DEFAULT};
                    border-radius: 4px;
                    background: {COLOR_BG_INPUT};
                    color: white;
                    text-align: center;
                }}
                QProgressBar::chunk {{
                    background: {COLOR_SUCCESS};
                    border-radius: 3px;
                }}
            """)
            self.tab_installer.layout().addWidget(self.install_progress)
        
        self.install_progress.setValue(installed_pct)
        self.install_progress.setFormat(f"{installed_pct}%")
        
        # Add spacing (once)
        if not hasattr(self, '_spacing_added'):
            self.tab_installer.layout().addSpacing(20)
            self._spacing_added = True
        
        # Get tool lists
        tool_status = self.installer.get_tool_status()
        installed_tools = [t["name"] for t in tool_status if t["installed"]]
        missing_tools = [t["name"] for t in tool_status if not t["installed"]]
        
        # Update or create installed section
        if installed_tools:
            if not hasattr(self, 'installed_label'):
                self.installed_label = QLabel()
                self.installed_label.setStyleSheet("color: #10b981; font-size: 14px;")
                self.tab_installer.layout().addWidget(self.installed_label)
            self.installed_label.setText(f"<b>[+] Installed ({len(installed_tools)}):</b>")
            self.installed_label.setVisible(True)
            
            if not hasattr(self, 'installed_list'):
                self.installed_list = QLabel()
                self.installed_list.setWordWrap(True)
                self.installed_list.setStyleSheet("color: #ccc; font-size: 13px; padding: 10px; background: #1a1a1a; border-radius: 4px;")
                self.tab_installer.layout().addWidget(self.installed_list)
            self.installed_list.setText(", ".join(installed_tools))
            self.installed_list.setVisible(True)
            
            # Add spacing after installed (once)
            if not hasattr(self, '_installed_spacing'):
                self.tab_installer.layout().addSpacing(15)
                self._installed_spacing = True
        elif hasattr(self, 'installed_label'):
            self.installed_label.setVisible(False)
            self.installed_list.setVisible(False)
        
        # Update or create missing section
        if missing_tools:
            if not hasattr(self, 'missing_label'):
                self.missing_label = QLabel()
                self.missing_label.setStyleSheet("color: #f87171; font-size: 14px;")
                self.tab_installer.layout().addWidget(self.missing_label)
            self.missing_label.setText(f"<b>[-] Missing ({len(missing_tools)}):</b>")
            self.missing_label.setVisible(True)
            
            if not hasattr(self, 'missing_list'):
                self.missing_list = QLabel()
                self.missing_list.setWordWrap(True)
                self.missing_list.setStyleSheet("color: #ccc; font-size: 13px; padding: 10px; background: #1a1a1a; border-radius: 4px;")
                self.tab_installer.layout().addWidget(self.missing_list)
            self.missing_list.setText(", ".join(missing_tools))
            self.missing_list.setVisible(True)
            
            # Add spacing after missing (once)
            if not hasattr(self, '_missing_spacing'):
                self.tab_installer.layout().addSpacing(20)
                self._missing_spacing = True
        elif hasattr(self, 'missing_label'):
            self.missing_label.setVisible(False)
            self.missing_list.setVisible(False)
        
        # Update or create install button
        if not hasattr(self, 'btn_install'):
            self.btn_install = QPushButton()
            self.btn_install.clicked.connect(self._install_tools_simplified)
            self.tab_installer.layout().addWidget(self.btn_install)
        
        if stats['missing'] > 0:
            self.btn_install.setText(f"Install Missing Tools ({stats['missing']})")
            self.btn_install.setEnabled(True)
            self.btn_install.setStyleSheet("""
                QPushButton {
                    background: #238636;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #2ea043;
                }
            """)
        else:
            self.btn_install.setText("All Tools Installed")
            self.btn_install.setEnabled(False)
            self.btn_install.setStyleSheet("""
                QPushButton {
                    background: #2a2a2a;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    color: #666;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)
    
    
    def _install_tools_simplified(self):
        """Install missing tools with simplified progress dialog."""
        from core.tool_installer import ToolInstaller
        from PySide6.QtWidgets import QProgressDialog
        from PySide6.QtCore import Qt
        
        installer = ToolInstaller()
        missing_tools = installer.get_missing_tools()
        
        if not missing_tools:
            QMessageBox.information(self, "✅ All Set", "All security tools are already installed!")
            return
        
        # Create progress dialog
        progress = QProgressDialog("Preparing installation...", "Cancel", 0, len(missing_tools) + 2, self)
        progress.setWindowTitle("Installing Security Tools")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        
        # Update package manager
        progress.setLabelText("Updating package manager...")
        progress.setValue(1)
        installer.update_package_manager()
        
        if progress.wasCanceled():
            return
        
        # Install tools
        installed_count = 0
        failed_tools = []
        
        for i, tool in enumerate(missing_tools, 2):
            if progress.wasCanceled():
                break
            
            progress.setLabelText(f"Installing {tool.name}...")
            progress.setValue(i)
            
            success, msg = installer.install_tool(tool)
            
            if success:
                installed_count += 1
            else:
                # Try Go fallback
                method = tool.get_install_method(installer.os_type)
                if method.value == "pkg" and tool.go_package:
                    success, msg = installer._install_via_go(tool.go_package, tool.name)
                    if success:
                        installed_count += 1
                    else:
                        failed_tools.append(tool.name)
                else:
                    failed_tools.append(tool.name)
        
        progress.setValue(len(missing_tools) + 2)
        progress.close()
        
        # Show result dialog
        if installed_count == len(missing_tools):
            QMessageBox.information(
                self,
                "✅ Installation Complete",
                f"Successfully installed all {installed_count} tools!"
            )
        elif installed_count > 0:
            QMessageBox.warning(
                self,
                "⚠️ Partial Success",
                f"Installed {installed_count}/{len(missing_tools)} tools.\n\n"
                f"Failed: {', '.join(failed_tools)}"
            )
        else:
            QMessageBox.critical(
                self,
                "❌ Installation Failed",
                f"Could not install tools. Please check:\n"
                f"• Internet connection\n"
                f"• Package manager configuration\n"
                f"• Sudo/root privileges"
            )
        
        # Refresh UI
        self._refresh_status()
    
    def _refresh_tool_status_simple(self):
        """Legacy method - now just calls _refresh_status."""
        self._refresh_status()

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

        **3. Security Tools Installation**
        If security tools are missing, use the **Tool Installer** tab to install them automatically.
        The installer supports: nmap, nuclei, subfinder, gobuster, hashcat, and 20+ more tools.
        Requires sudo/root privileges for installation.

        **4. Notifications**
        You will be notified when a long-running scan completes.

        **5. Stopping Tools**
        Use the Stop button to gracefully terminate a running tool.
        
        **6. Keyboard Shortcuts**
        - Ctrl+R: Run active tool
        - Ctrl+Q: Stop active tool
        - Ctrl+L: Clear output
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
