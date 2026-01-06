# =============================================================================
# modules/nmap.py
#
# Nmap - Network Mapper Port Scanner
# =============================================================================

import os
import subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCompleter, QApplication,
    QMessageBox, QInputDialog, QLineEdit
)
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from core.tgtinput import parse_targets, TargetInput
from core.fileops import create_target_dirs
from ui.worker import ProcessWorker
from ui.styles import (
    # Widgets
    RunButton, StopButton, CopyButton, BrowseButton,
    StyledLineEdit, StyledSpinBox, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, CommandDisplay, OutputView,
    StyledGroupBox, ToolSplitter,
    # Behaviors
    SafeStop, OutputHelper,
    # Constants
    TOOL_VIEW_STYLE, COLOR_BACKGROUND_SECONDARY
)


# ==============================
# Helper Functions
# ==============================

def is_root():
    return os.geteuid() == 0 if hasattr(os, "geteuid") else False


def parse_port_range(port_input: str):
    ports = set()
    if not port_input:
        return []
    for part in port_input.split(','):
        part = part.strip()
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                if 1 <= start <= end <= 65535:
                    ports.update(range(start, end + 1))
            except ValueError:
                continue
        else:
            try:
                port = int(part)
                if 1 <= port <= 65535:
                    ports.add(port)
            except ValueError:
                continue
    return sorted(list(ports))


# ==============================
# GUI Tool
# ==============================

class NmapScanner(ToolBase):
    """Nmap tool plugin."""
    
    @property
    def name(self) -> str:
        return "Nmap"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.PORT_SCANNING

    def get_widget(self, main_window: QWidget) -> QWidget:
        return NmapScannerView(main_window=main_window)


class NmapScannerView(QWidget, SafeStop, OutputHelper):
    """Nmap port scanner interface."""
    
    tool_name = "Nmap"
    tool_category = "PORT_SCANNING"
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_safe_stop()
        
        # State
        self._is_stopping = False
        self._scan_complete_added = False
        self._temp_ports_file = None
        self.nmap_scripts = self._get_nmap_scripts()
        
        # Build UI
        self._build_ui()
        self.update_command()
    
    def _get_nmap_scripts(self):
        try:
            command = r"find /usr/share/nmap/scripts -name '*.nse' -printf '%f\n' | sed 's/\.nse//' | sort"
            process = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
            if process.returncode == 0:
                return process.stdout.strip().split('\n')
            else:
                return []
        except Exception:
            return []
    
    def _build_ui(self):
        """Build the complete UI."""
        self.setStyleSheet(TOOL_VIEW_STYLE)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Splitter for control/output
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
        
        # ==================== PORT & SCAN TYPE ROW ====================
        options_layout = QHBoxLayout()
        
        port_label = StyledLabel("Ports:")
        self.port_input = StyledLineEdit("e.g. 80, 443, 1-1000")
        self.port_input.textChanged.connect(self.update_command)
        
        scan_type_label = StyledLabel("Scan Type:")
        self.scan_type = StyledComboBox()
        self.scan_type.addItems(['syn', 'tcp', 'udp', 'ack', 'fin', 'null', 'xmas', 'window', 'maimon'])
        self.scan_type.currentTextChanged.connect(self.update_command)
        
        options_layout.addWidget(port_label)
        options_layout.addWidget(self.port_input, 1)
        options_layout.addSpacing(10)
        options_layout.addWidget(scan_type_label)
        options_layout.addWidget(self.scan_type, 1)
        
        control_layout.addLayout(options_layout)
        
        # ==================== SCRIPT & HOST SCAN ROW ====================
        script_host_layout = QHBoxLayout()
        
        script_label = StyledLabel("Scripts:")
        self.script_input = StyledComboBox()
        self.script_input.setEditable(True)
        
        common_scripts = ['(None)', 'default', 'vuln', 'banner', 'discovery', 'safe', 'intrusive', 'auth', 'brute', 'dos', 'exploit']
        self.script_input.addItems(common_scripts)
        self.script_input.insertSeparator(len(common_scripts))
        self.script_input.addItems(self.nmap_scripts)
        self.script_input.currentTextChanged.connect(self.update_command)
        
        completer_list = common_scripts + self.nmap_scripts
        completer = QCompleter(completer_list, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.script_input.setCompleter(completer)
        
        host_scan_label = StyledLabel("Host Scan:")
        self.host_scan_type = StyledComboBox()
        self.host_scan_type.addItems(['Default', 'List Scan (-sL)', 'Ping Scan (-sn)', 'No Ping (-Pn)'])
        self.host_scan_type.currentTextChanged.connect(self.update_command)
        
        script_host_layout.addWidget(script_label)
        script_host_layout.addWidget(self.script_input, 1)
        script_host_layout.addSpacing(10)
        script_host_layout.addWidget(host_scan_label)
        script_host_layout.addWidget(self.host_scan_type, 1)
        
        control_layout.addLayout(script_host_layout)
        
        # ==================== CHECKBOXES ROW ====================
        checkbox_layout = QHBoxLayout()
        
        self.aggressive_scan_check = StyledCheckBox("Aggressive Scan (-A)")
        self.aggressive_scan_check.stateChanged.connect(self.update_command)
        
        self.traceroute_check = StyledCheckBox("Traceroute")
        self.traceroute_check.stateChanged.connect(self.update_command)
        
        self.service_version_check = StyledCheckBox("Service Version (-sV)")
        self.service_version_check.stateChanged.connect(self.update_command)
        
        self.os_detection_check = StyledCheckBox("OS Detection (-O)")
        self.os_detection_check.stateChanged.connect(self.update_command)
        
        checkbox_layout.addWidget(self.aggressive_scan_check)
        checkbox_layout.addWidget(self.traceroute_check)
        checkbox_layout.addWidget(self.service_version_check)
        checkbox_layout.addWidget(self.os_detection_check)
        checkbox_layout.addStretch()
        
        control_layout.addLayout(checkbox_layout)
        
        # ==================== SPEED & OUTPUT ROW ====================
        speed_output_layout = QHBoxLayout()
        
        speed_label = StyledLabel("Speed:")
        self.speed_template = StyledComboBox()
        self.speed_template.addItems(['T0 (Paranoid)', 'T1 (Sneaky)', 'T2 (Polite)', 'T3 (Normal)', 'T4 (Aggressive)', 'T5 (Insane)'])
        self.speed_template.setCurrentIndex(3)
        self.speed_template.currentTextChanged.connect(self.update_command)
        
        output_format_label = StyledLabel("Output Format:")
        self.output_format = StyledComboBox()
        self.output_format.addItems(['Normal (txt)', 'XML (.xml)', 'Grepable (.gnmap)', 'All Formats'])
        self.output_format.currentTextChanged.connect(self.update_command)
        
        speed_output_layout.addWidget(speed_label)
        speed_output_layout.addWidget(self.speed_template, 1)
        speed_output_layout.addSpacing(10)
        speed_output_layout.addWidget(output_format_label)
        speed_output_layout.addWidget(self.output_format, 1)
        
        control_layout.addLayout(speed_output_layout)
        
        # ==================== TIMING CONTROLS ====================
        timing_title = StyledLabel("Timing & Rate Control")
        control_layout.addWidget(timing_title)
        
        timing_layout = QHBoxLayout()
        
        timeout_label = StyledLabel("Host Timeout (ms):")
        self.host_timeout_spin = StyledSpinBox()
        self.host_timeout_spin.setRange(0, 300000)
        self.host_timeout_spin.setValue(0)
        self.host_timeout_spin.setSuffix(" ms")
        self.host_timeout_spin.setSpecialValueText("Default")
        self.host_timeout_spin.valueChanged.connect(self.update_command)
        
        self.delay = StyledSpinBox()
        self.delay.setSuffix(" ms delay")
        self.delay.setRange(0, 5000)
        self.delay.setValue(0)
        self.delay.valueChanged.connect(self.update_command)
        
        self.max_rps = StyledSpinBox()
        self.max_rps.setPrefix("Max RPS: ")
        self.max_rps.setRange(0, 10000)
        self.max_rps.setValue(0)
        self.max_rps.valueChanged.connect(self.update_command)
        
        self.timeout = StyledSpinBox()
        self.timeout.setPrefix("Timeout: ")
        self.timeout.setSuffix(" s")
        self.timeout.setRange(0, 300)
        self.timeout.setValue(0)
        self.timeout.valueChanged.connect(self.update_command)
        
        self.retries = StyledSpinBox()
        self.retries.setPrefix("Retries: ")
        self.retries.setRange(0, 10)
        self.retries.setValue(0)
        self.retries.valueChanged.connect(self.update_command)
        
        timing_layout.addWidget(timeout_label)
        timing_layout.addWidget(self.host_timeout_spin)
        timing_layout.addWidget(self.delay)
        timing_layout.addWidget(self.max_rps)
        timing_layout.addWidget(self.timeout)
        timing_layout.addWidget(self.retries)
        
        control_layout.addLayout(timing_layout)
        
        # Command Display
        self.command_input = CommandDisplay()
        control_layout.addWidget(self.command_input)
        
        control_layout.addStretch()
        splitter.addWidget(control_panel)
        
        # ==================== OUTPUT AREA ====================
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("Nmap results will appear here...")
        
        # Copy button
        self.copy_button = CopyButton(self.output.output_text, self.main_window)
        self.copy_button.setParent(self.output.output_text)
        self.copy_button.raise_()
        self.output.output_text.installEventFilter(self)
        
        splitter.addWidget(self.output)
        splitter.setSizes([400, 400])
        
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
        try:
            target = self.target_input.get_target().strip() or "<target>"
            host_scan_flag = self._get_host_scan_flag()
            scan_type_flag = self._get_nmap_scan_flag()
            port_arg = f"-p {self.port_input.text().strip()}" if self.port_input.text().strip() else "-p 1-1000"
            
            output_flag, _ = self._get_output_args()
            speed_flag = self._get_speed_flag()
            
            other_args = []
            if self.aggressive_scan_check.isChecked():
                other_args.append("-A")
            if self.traceroute_check.isChecked():
                other_args.append("--traceroute")
            if self.service_version_check.isChecked():
                other_args.append("-sV")
            if self.os_detection_check.isChecked():
                other_args.append("-O")
            
            script_arg = []
            selected_script = self.script_input.currentText().strip()
            if selected_script and selected_script != '(None)':
                script_arg = ["--script", selected_script]
            
            timing_args = []
            if self.retries.value() > 0:
                timing_args.append(f"--max-retries {self.retries.value()}")
            if self.timeout.value() > 0:
                timing_args.append(f"--host-timeout {self.timeout.value()}s")
            if self.max_rps.value() > 0:
                timing_args.append(f"--max-rate {self.max_rps.value()}")
            if self.delay.value() > 0:
                timing_args.append(f"--scan-delay {self.delay.value()}ms")
            
            command_parts = ["nmap"]
            if speed_flag:
                command_parts.append(speed_flag)
            if host_scan_flag:
                command_parts.append(host_scan_flag)
            
            if host_scan_flag not in ['-sL', '-sn']:
                command_parts.extend([scan_type_flag, port_arg])
            
            command_parts.extend(other_args)
            
            if output_flag:
                command_parts.extend([output_flag, "nmap"])
            
            command_parts.extend(script_arg)
            command_parts.extend(timing_args)
            command_parts.append(target)
            
            self.command_input.setText(" ".join(command_parts))
        except AttributeError:
            pass
    
    def run_scan(self):
        self.output.clear()
        self._is_stopping = False
        self._scan_complete_added = False
        
        target_str = self.target_input.get_target()
        targets = parse_targets(target_str)[0]
        if not targets:
            return QMessageBox.warning(self, "Warning", "No valid targets specified.")
        
        try:
            base_dir = create_target_dirs(targets[0])
            logs_dir = os.path.join(base_dir, "Logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            output_flag, file_ext = self._get_output_args()
            log_path_base = os.path.join(logs_dir, "nmap")
            log_path = f"{log_path_base}{file_ext}"
            
            command = ["nmap"]
            speed_flag = self._get_speed_flag()
            if speed_flag:
                command.append(speed_flag)
            
            host_scan_flag = self._get_host_scan_flag()
            if host_scan_flag:
                command.append(host_scan_flag)
            
            if host_scan_flag not in ['-sL', '-sn']:
                port_input = self.port_input.text().strip()
                if not port_input:
                    port_input = "1-1000"
                
                if ',' not in port_input and '-' in port_input and len(port_input) <= 20:
                    command.extend([self._get_nmap_scan_flag(), "-p", port_input])
                elif len(port_input) <= 1000:
                    command.extend([self._get_nmap_scan_flag(), "-p", port_input])
                else:
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                        ports_list = parse_port_range(port_input)
                        f.write('\n'.join(map(str, ports_list)))
                        ports_file = f.name
                    command.extend([self._get_nmap_scan_flag(), "-iL", ports_file])
                    self._temp_ports_file = ports_file
            
            if self.aggressive_scan_check.isChecked():
                command.append("-A")
            if self.traceroute_check.isChecked():
                command.append("--traceroute")
            if self.service_version_check.isChecked():
                command.append("-sV")
            if self.os_detection_check.isChecked():
                command.append("-O")
            
            if output_flag:
                path_for_nmap = log_path_base if output_flag == '-oA' else log_path
                command.extend([output_flag, path_for_nmap])
            
            scripts = self.script_input.currentText().strip()
            if scripts and scripts != '(None)':
                command.extend(["--script", scripts])
            
            if self.retries.value() > 0:
                command.extend(["--max-retries", str(self.retries.value())])
            if self.timeout.value() > 0:
                command.extend(["--host-timeout", f"{self.timeout.value()}s"])
            if self.max_rps.value() > 0:
                command.extend(["--max-rate", str(self.max_rps.value())])
            if self.delay.value() > 0:
                command.extend(["--scan-delay", f"{self.delay.value()}ms"])
            
            command.extend(targets)
            
            # Privilege escalation
            from ui.settingpanel import privilege_manager
            
            stdin_data = None
            
            if privilege_manager.mode == "sudo":
                if not privilege_manager.sudo_password:
                    pwd, ok = QInputDialog.getText(
                        self,
                        "Sudo Password Required",
                        "Sudo is enabled in Settings.\n\nPlease enter your password:",
                        QLineEdit.Password
                    )
                    if ok and pwd.strip():
                        privilege_manager.set_sudo_password(pwd.strip())
                    else:
                        self._error("Scan cancelled: Password is required when sudo is enabled.")
                        self._info("Tip: Disable 'Enable sudo' in Settings if you don't need it.")
                        return
                
                command = privilege_manager.wrap_command(command)
                stdin_data = privilege_manager.get_stdin_data()
                self._info("Running with sudo")
            
            if output_flag == '-oA':
                self._info(f"Scan started. Output will be saved to {log_path_base}.(nmap|xml|gnmap)")
            else:
                self._info(f"Scan started. Output will be saved to: {log_path}")
            
            self.output.appendPlainText("")
            
            self.worker = ProcessWorker(command, stdin_data=stdin_data)
            self.worker.output_ready.connect(self.output.appendPlainText)
            self.worker.finished.connect(self.on_finished)
            self.worker.error.connect(self._error)
            
            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.worker.start()
            
        except Exception as e:
            self._error(f"Failed to start scan: {str(e)}")
    
    def on_finished(self):
        if hasattr(self, '_temp_ports_file') and self._temp_ports_file:
            try:
                os.unlink(self._temp_ports_file)
                self._temp_ports_file = None
            except (OSError, AttributeError):
                pass
        
        self._on_scan_completed()
        if self._is_stopping:
            return
        
        if not self._scan_complete_added:
            self._section("Scan Complete")
            self._scan_complete_added = True
    
    def stop_scan(self):
        """Stop the scan safely."""
        if hasattr(self, '_temp_ports_file') and self._temp_ports_file:
            try:
                os.unlink(self._temp_ports_file)
                self._temp_ports_file = None
            except (OSError, AttributeError):
                pass
        
        try:
            if self.worker and self.worker.isRunning():
                self._is_stopping = True
                self.worker.stop()
                self.worker.wait(1000)
                self._info("Scan stopped.")
        except Exception:
            pass
        finally:
            self._on_scan_completed()
    
    def _on_scan_completed(self):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.worker = None
        if self.main_window:
            self.main_window.active_process = None
    
    def copy_results_to_clipboard(self):
        """Copy scan results to clipboard."""
        results_text = self.output.toPlainText()
        if results_text.strip():
            QApplication.clipboard().setText(results_text)
            self._notify("Results copied to clipboard.")
        else:
            self._notify("No results to copy.")
    
    def _get_nmap_scan_flag(self):
        return {
            "tcp": "-sT", "syn": "-sS", "udp": "-sU",
            "ack": "-sA", "fin": "-sF", "null": "-sN",
            "xmas": "-sX", "window": "-sW", "maimon": "-sM"
        }.get(self.scan_type.currentText(), "-sS")
    
    def _get_host_scan_flag(self):
        return {
            'Default': '',
            'List Scan (-sL)': '-sL',
            'Ping Scan (-sn)': '-sn',
            'No Ping (-Pn)': '-Pn'
        }.get(self.host_scan_type.currentText(), '')
    
    def _get_speed_flag(self):
        """Get Nmap timing template flag."""
        speed_map = {
            'T0 (Paranoid)': '-T0',
            'T1 (Sneaky)': '-T1',
            'T2 (Polite)': '-T2',
            'T3 (Normal)': '-T3',
            'T4 (Aggressive)': '-T4',
            'T5 (Insane)': '-T5'
        }
        return speed_map.get(self.speed_template.currentText(), '-T3')
    
    def _get_output_args(self):
        return {
            'Normal (txt)': ('-oN', '.txt'),
            'XML (.xml)': ('-oX', '.xml'),
            'Grepable (.gnmap)': ('-oG', '.gnmap'),
            'All Formats': ('-oA', '')
        }.get(self.output_format.currentText(), ('-oN', '.txt'))
