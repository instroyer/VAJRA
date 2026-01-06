# =============================================================================
# modules/eyewitness.py
#
# Eyewitness - Web Screenshot Capture Tool
# =============================================================================

import os
from datetime import datetime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from modules.bases import ToolBase, ToolCategory
from core.tgtinput import parse_targets, TargetInput
from core.fileops import RESULT_BASE
from ui.worker import ProcessWorker
from ui.styles import (
    RunButton, StopButton, CopyButton,
    StyledLineEdit, StyledSpinBox, StyledCheckBox,
    StyledLabel, HeaderLabel, CommandDisplay, OutputView,
    StyledGroupBox, ToolSplitter,
    SafeStop, OutputHelper,
    TOOL_VIEW_STYLE, COLOR_BACKGROUND_SECONDARY
)


class EyewitnessView(QWidget, SafeStop, OutputHelper):
    """Eyewitness web screenshot tool interface."""
    
    tool_name = "Eyewitness"
    tool_category = "WEB_SCREENSHOTS"
    
    def __init__(self, name, category, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_safe_stop()
        
        # Build UI
        self._build_ui()
        self.update_command()
    
    def _build_ui(self):
        """Build the complete UI."""
        self.setStyleSheet(TOOL_VIEW_STYLE)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = ToolSplitter()
        
        # ==================== CONTROL PANEL ====================
        control_panel = QWidget()
        control_panel.setStyleSheet(f"background-color: {COLOR_BACKGROUND_SECONDARY};")
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)
        
        # Header
        header = HeaderLabel(self.tool_category, self.tool_name)
        control_layout.addWidget(header)
        
        # Target Row
        target_label = StyledLabel("Target")
        control_layout.addWidget(target_label)
        
        target_row = QHBoxLayout()
        self.target_input = TargetInput()
        self.target_input.input_box.textChanged.connect(self.update_command)
        target_row.addWidget(self.target_input, 1)
        
        self.run_button = RunButton()
        self.run_button.clicked.connect(self.run_scan)
        self.stop_button = StopButton()
        self.stop_button.clicked.connect(self.stop_scan)
        
        target_row.addWidget(self.run_button)
        target_row.addWidget(self.stop_button)
        control_layout.addLayout(target_row)
        
        # ==================== CONFIGURATION GROUP ====================
        config_group = StyledGroupBox("⚙️ Scan Configuration")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(10)
        
        # Row 1: Timeout, Threads, Delay
        row1 = QHBoxLayout()
        
        timeout_label = StyledLabel("Timeout:")
        self.timeout_spin = StyledSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix("s")
        self.timeout_spin.valueChanged.connect(self.update_command)
        
        row1.addWidget(timeout_label)
        row1.addWidget(self.timeout_spin)
        row1.addSpacing(20)
        
        threads_label = StyledLabel("Threads:")
        self.threads_spin = StyledSpinBox()
        self.threads_spin.setRange(1, 1000)
        self.threads_spin.setValue(50)
        self.threads_spin.valueChanged.connect(self.update_command)
        
        row1.addWidget(threads_label)
        row1.addWidget(self.threads_spin)
        row1.addSpacing(20)
        
        delay_label = StyledLabel("Delay:")
        self.delay_spin = StyledSpinBox()
        self.delay_spin.setRange(0, 60)
        self.delay_spin.setValue(0)
        self.delay_spin.setSuffix("s")
        self.delay_spin.valueChanged.connect(self.update_command)
        
        row1.addWidget(delay_label)
        row1.addWidget(self.delay_spin)
        row1.addStretch()
        
        config_layout.addLayout(row1)
        
        # Row 2: User Agent, Proxy
        row2 = QHBoxLayout()
        
        ua_label = StyledLabel("User Agent:")
        self.user_agent_input = StyledLineEdit("Default User Agent...")
        self.user_agent_input.textChanged.connect(self.update_command)
        
        row2.addWidget(ua_label)
        row2.addWidget(self.user_agent_input, 1)
        row2.addSpacing(15)
        
        proxy_label = StyledLabel("Proxy:")
        self.proxy_input = StyledLineEdit("http://127.0.0.1:8080")
        self.proxy_input.textChanged.connect(self.update_command)
        
        row2.addWidget(proxy_label)
        row2.addWidget(self.proxy_input, 1)
        
        config_layout.addLayout(row2)
        
        # Row 3: Checkboxes
        row3 = QHBoxLayout()
        
        self.prepend_https_check = StyledCheckBox("Prepend HTTPS")
        self.prepend_https_check.stateChanged.connect(self.update_command)
        
        self.no_dns_check = StyledCheckBox("No DNS")
        self.no_dns_check.stateChanged.connect(self.update_command)
        
        row3.addWidget(self.prepend_https_check)
        row3.addSpacing(15)
        row3.addWidget(self.no_dns_check)
        row3.addStretch()
        
        config_layout.addLayout(row3)
        
        control_layout.addWidget(config_group)
        
        # Command Display
        self.command_input = CommandDisplay()
        control_layout.addWidget(self.command_input)
        
        control_layout.addStretch()
        splitter.addWidget(control_panel)
        
        # ==================== OUTPUT AREA ====================
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("Eyewitness results will appear here...")
        
        self.copy_button = CopyButton(self.output.output_text, self.main_window)
        self.copy_button.setParent(self.output.output_text)
        self.copy_button.raise_()
        self.output.output_text.installEventFilter(self)
        
        splitter.addWidget(self.output)
        splitter.setSizes([350, 400])
        
        main_layout.addWidget(splitter)
    
    def eventFilter(self, obj, event):
        """Position copy button on resize."""
        from PySide6.QtCore import QEvent
        if obj == self.output.output_text and event.type() == QEvent.Resize:
            self.copy_button.move(
                self.output.output_text.width() - self.copy_button.sizeHint().width() - 10,
                10
            )
        return super().eventFilter(obj, event)
    
    def update_command(self):
        if not hasattr(self, 'timeout_spin') or not self.timeout_spin:
            return

        try:
            cmd_parts = ["eyewitness", "--web"]
            
            cmd_parts.extend(["--timeout", str(self.timeout_spin.value())])
            cmd_parts.extend(["--threads", str(self.threads_spin.value())])
            
            if self.delay_spin.value() > 0:
                cmd_parts.extend(["--delay", str(self.delay_spin.value())])

            if self.prepend_https_check.isChecked():
                cmd_parts.append("--prepend-https")

            if self.no_dns_check.isChecked():
                cmd_parts.append("--no-dns")
                
            if self.user_agent_input.text().strip():
                cmd_parts.extend(["--user-agent", self.user_agent_input.text().strip()])
                
            proxy_val = self.proxy_input.text().strip()
            if proxy_val and ":" in proxy_val:
                try:
                    ip, port = proxy_val.split(":", 1)
                    cmd_parts.extend(["--proxy-ip", ip, "--proxy-port", port])
                except ValueError:
                    pass

            self.command_input.setText(" ".join(cmd_parts))
            
        except AttributeError:
            pass

    def run_scan(self):
        raw_input = self.target_input.get_target()
        if not raw_input:
            self._notify("Please enter a target (domain/IP or file path).")
            return

        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.output.clear()
        
        # Cleanup geckodriver.log
        if os.path.exists("geckodriver.log"):
            try:
                os.remove("geckodriver.log")
            except:
                pass

        target_args = []
        
        if raw_input.strip().startswith('@'):
            potential_file = raw_input.strip()[1:]
            if os.path.exists(potential_file):
                targets, source = parse_targets(potential_file)
                if not targets:
                    self._notify("No valid targets found in file.")
                    return
                base_name = os.path.splitext(os.path.basename(potential_file))[0]
                target_args = ["-f", potential_file]
            else:
                self._notify(f"File not found: {potential_file}")
                return
        
        elif os.path.exists(raw_input.strip()):
            targets, source = parse_targets(raw_input)
            if not targets:
                self._notify("No valid targets found in file.")
                return

            base_name = os.path.splitext(os.path.basename(raw_input))[0]
            target_args = ["-f", raw_input]
        else:
            single_target = raw_input.strip()
            if not single_target:
                self._notify("Please enter a valid target.")
                return

            if '://' not in single_target:
                single_target = f"https://{single_target}"

            target_args = ["--single", single_target]
            base_name = single_target.replace('https://', '').replace('http://', '').replace('/', '_')

        eyewitness_output_dir = os.path.join(RESULT_BASE, f"eyewitness_{base_name}_{self._get_timestamp()}")

        if os.path.exists(eyewitness_output_dir):
            import shutil
            shutil.rmtree(eyewitness_output_dir)
        
        os.makedirs(RESULT_BASE, exist_ok=True)
        
        self._info(f"Target output directory: {eyewitness_output_dir}")

        cmd = self.command_input.text().split()
        cmd.extend(target_args)
        cmd.extend(["-d", eyewitness_output_dir, "--no-prompt"])

        self._info(f"Starting Eyewitness scan")
        self._info(f"Output directory: {eyewitness_output_dir}")

        actual_cmd = ' '.join(cmd)
        self.command_input.setText(actual_cmd)

        try:
            self.worker = ProcessWorker(actual_cmd, shell=True)
            self.worker.output_ready.connect(self._on_output)
            self.worker.finished.connect(self._on_scan_completed)
            self.worker.error.connect(self._on_error)
            self.worker.start()

            if self.main_window:
                self.main_window.active_process = self.worker
        except Exception as e:
            self._error(f"Failed to start eyewitness: {str(e)}")
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def _on_output(self, line):
        line = line.strip()
        if line:
            self._info(line)

    def _on_error(self, error):
        self._error(f"Eyewitness error: {error}")

    def _on_scan_completed(self):
        if not self.stop_button.isEnabled():
            return

        if os.path.exists("geckodriver.log"):
            try:
                os.remove("geckodriver.log")
            except:
                pass
                
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.worker = None
        if self.main_window:
            self.main_window.active_process = None
        self._notify("Eyewitness screenshot scan completed!")

    def _get_timestamp(self):
        return datetime.now().strftime("%d%m%Y_%H%M%S")


class EyewitnessTool(ToolBase):
    """Eyewitness tool plugin."""
    
    @property
    def name(self) -> str:
        return "Eyewitness"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WEB_SCREENSHOTS

    def get_widget(self, main_window):
        return EyewitnessView(self.name, self.category, main_window=main_window)
