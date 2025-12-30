import os
import shutil
import threading
import subprocess
from datetime import datetime

from PySide6.QtCore import QObject, Signal, Qt, QRect
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QLineEdit, QGroupBox, QMessageBox, QSplitter, QCompleter, QApplication, QCheckBox
)

from modules.bases import ToolBase, ToolCategory
from ui.widgets import BaseToolView
from ui.worker import ProcessWorker
from core.tgtinput import parse_targets
from core.fileops import create_target_dirs
from ui.styles import (
    TARGET_INPUT_STYLE, COMBO_BOX_STYLE,
    COLOR_BACKGROUND_INPUT, COLOR_TEXT_PRIMARY, COLOR_BORDER, COLOR_BORDER_INPUT_FOCUSED,
    StyledComboBox, StyledSpinBox, SPINBOX_STYLE
)


# ==============================
# Nmap Tool
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
    @property
    def name(self) -> str:
        return "Nmap"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.PORT_SCANNING

    def get_widget(self, main_window: QWidget) -> QWidget:
        return NmapScannerView(main_window=main_window)

class NmapScannerView(BaseToolView):
    def __init__(self, main_window):
        super().__init__("Nmap", ToolCategory.PORT_SCANNING, main_window)
        self.nmap_scripts = self._get_nmap_scripts()
        self._is_stopping = False
        self._scan_complete_added = False  # Flag to prevent duplicate "Scan Complete"
        self._temp_ports_file = None  # For cleanup of temporary port files
        self._build_custom_ui()
        self.update_command()

    def _get_nmap_scripts(self):
        try:
            command = "find /usr/share/nmap/scripts -name '*.nse' -printf '%f\n' | sed 's/\.nse//' | sort"
            process = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
            if process.returncode == 0:
                return process.stdout.strip().split('\n')
            else:
                return []
        except Exception:
            return []

    def _build_custom_ui(self):
        splitter = self.findChild(QSplitter)
        control_panel = splitter.widget(0)
        control_layout = control_panel.layout()

        # Fix: Properly disconnect and reconnect copy button
        try:
            self.output.copy_button.clicked.disconnect()
        except:
            pass
        self.output.copy_button.clicked.connect(self.copy_results_to_clipboard)

        options_layout = QHBoxLayout()
        port_label = QLabel("Ports:")
        port_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 500;")
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("e.g. 80, 443, 1-1000")
        # Apply target input style to port input
        self.port_input.setStyleSheet(TARGET_INPUT_STYLE)
        
        scan_type_label = QLabel("Scan Type:")
        scan_type_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 500;")
        self.scan_type = StyledComboBox()
        self.scan_type.addItems(['syn', 'tcp', 'udp', 'ack', 'fin', 'null', 'xmas', 'window', 'maimon'])
        
        options_layout.addWidget(port_label)
        options_layout.addWidget(self.port_input, 1)
        options_layout.addSpacing(10)
        options_layout.addWidget(scan_type_label)
        options_layout.addWidget(self.scan_type, 1)

        script_host_layout = QHBoxLayout()
        script_label = QLabel("Scripts:")
        script_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 500;")
        self.script_input = StyledComboBox()
        self.script_input.setEditable(True)
        self.script_input.setPlaceholderText("Search or select a script...")

        common_scripts = ['(None)', 'default', 'vuln', 'banner', 'discovery', 'safe', 'intrusive', 'auth', 'brute', 'dos', 'exploit']
        self.script_input.addItems(common_scripts)
        self.script_input.insertSeparator(len(common_scripts))
        self.script_input.addItems(self.nmap_scripts)

        completer_list = common_scripts + self.nmap_scripts
        completer = QCompleter(completer_list, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.script_input.setCompleter(completer)

        host_scan_label = QLabel("Host Scan:")
        host_scan_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 500;")
        self.host_scan_type = StyledComboBox()
        self.host_scan_type.addItems(['Default', 'List Scan (-sL)', 'Ping Scan (-sn)', 'No Ping (-Pn)'])

        script_host_layout.addWidget(script_label)
        script_host_layout.addWidget(self.script_input, 1)
        script_host_layout.addSpacing(10)
        script_host_layout.addWidget(host_scan_label)
        script_host_layout.addWidget(self.host_scan_type, 1)

        # Checkbox layout (first line)
        checkbox_layout = QHBoxLayout()
        checkbox_style = f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px;"
        self.aggressive_scan_check = QCheckBox("Aggressive Scan (-A)")
        self.aggressive_scan_check.setStyleSheet(checkbox_style)
        self.traceroute_check = QCheckBox("Traceroute")
        self.traceroute_check.setStyleSheet(checkbox_style)
        self.service_version_check = QCheckBox("Service Version (-sV)")
        self.service_version_check.setStyleSheet(checkbox_style)
        self.os_detection_check = QCheckBox("OS Detection (-O)")
        self.os_detection_check.setStyleSheet(checkbox_style)
        
        checkbox_layout.addWidget(self.aggressive_scan_check)
        checkbox_layout.addWidget(self.traceroute_check)
        checkbox_layout.addWidget(self.service_version_check)
        checkbox_layout.addWidget(self.os_detection_check)
        checkbox_layout.addStretch()
        
        # Speed and Output Format layout (second line, below checkboxes)
        speed_output_layout = QHBoxLayout()
        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 500;")
        self.speed_template = StyledComboBox()
        self.speed_template.addItems(['T0 (Paranoid)', 'T1 (Sneaky)', 'T2 (Polite)', 'T3 (Normal)', 'T4 (Aggressive)', 'T5 (Insane)'])
        self.speed_template.setCurrentIndex(3)  # Default to T3 (Normal)
        
        output_format_label = QLabel("Output Format:")
        output_format_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 500;")
        self.output_format = StyledComboBox()
        self.output_format.addItems(['Normal (txt)', 'XML (.xml)', 'Grepable (.gnmap)', 'All Formats'])

        speed_output_layout.addWidget(speed_label)
        speed_output_layout.addWidget(self.speed_template, 1)
        speed_output_layout.addSpacing(10)
        speed_output_layout.addWidget(output_format_label)
        speed_output_layout.addWidget(self.output_format, 1)

        timing_title = QLabel("Timing & Rate Control")
        timing_title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 600; margin-top: 10px;")

        timing_controls_widget = QWidget()
        timing_controls_widget.setStyleSheet("background: transparent; border: none;")  # Remove dark box
        timing_layout = QHBoxLayout(timing_controls_widget)
        timing_layout.setContentsMargins(0, 0, 0, 0)
        timing_layout.setSpacing(10)

        # Host timeout
        timeout_label = QLabel("Host Timeout (ms):")
        timeout_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 500;")
        self.host_timeout_spin = QSpinBox()
        self.host_timeout_spin.setRange(0, 300000)
        self.host_timeout_spin.setValue(0)
        self.host_timeout_spin.setSuffix(" ms")
        self.host_timeout_spin.setSpecialValueText("Default")
        self.host_timeout_spin.setStyleSheet(SPINBOX_STYLE)
        timing_layout.addWidget(timeout_label)
        timing_layout.addWidget(self.host_timeout_spin)

        # Create styled spinboxes using centralized style
        self.delay = QSpinBox()
        self.delay.setSuffix(" ms delay")
        self.delay.setRange(0, 5000)
        self.delay.setValue(0)
        self.delay.setStyleSheet(SPINBOX_STYLE)

        self.max_rps = QSpinBox()
        self.max_rps.setPrefix("Max RPS: ")
        self.max_rps.setRange(0, 10000)
        self.max_rps.setValue(0)
        self.max_rps.setStyleSheet(SPINBOX_STYLE)

        self.timeout = QSpinBox()
        self.timeout.setPrefix("Timeout: ")
        self.timeout.setSuffix(" s")
        self.timeout.setRange(0, 300)
        self.timeout.setValue(0)
        self.timeout.setStyleSheet(SPINBOX_STYLE)

        self.retries = QSpinBox()
        self.retries.setPrefix("Retries: ")
        self.retries.setRange(0, 10)
        self.retries.setValue(0)
        self.retries.setStyleSheet(SPINBOX_STYLE)

        for w in (self.delay, self.max_rps, self.timeout, self.retries):
            timing_layout.addWidget(w)

        insertion_index = 5
        control_layout.insertLayout(insertion_index, options_layout)
        control_layout.insertLayout(insertion_index + 1, script_host_layout)
        control_layout.insertLayout(insertion_index + 2, checkbox_layout)
        control_layout.insertLayout(insertion_index + 3, speed_output_layout)
        control_layout.insertWidget(insertion_index + 4, timing_title)
        control_layout.insertWidget(insertion_index + 5, timing_controls_widget)

        for widget in [self.port_input, self.scan_type, self.script_input, self.host_scan_type, self.output_format, self.speed_template, self.delay, self.max_rps, self.timeout, self.retries, self.aggressive_scan_check, self.traceroute_check, self.service_version_check, self.os_detection_check]:
            if isinstance(widget, QLineEdit): 
                widget.textChanged.connect(self.update_command)
            elif isinstance(widget, QComboBox): 
                widget.currentTextChanged.connect(self.update_command)
            elif isinstance(widget, QSpinBox): 
                widget.valueChanged.connect(self.update_command)
            elif isinstance(widget, QCheckBox): 
                widget.stateChanged.connect(self.update_command)

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
            if self.retries.value() > 0: timing_args.append(f"--max-retries {self.retries.value()}")
            if self.timeout.value() > 0: timing_args.append(f"--host-timeout {self.timeout.value()}s")
            if self.max_rps.value() > 0: timing_args.append(f"--max-rate {self.max_rps.value()}")
            if self.delay.value() > 0: timing_args.append(f"--scan-delay {self.delay.value()}ms")

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
        self._scan_complete_added = False  # Reset flag when starting new scan
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
                scan_type = self.scan_type.currentText()
                if scan_type != "tcp" and not is_root():
                    QMessageBox.warning(self, "Privilege Warning", f"'{scan_type.upper()}' scan requires root privileges.")
                
                # Handle port specification to avoid argument list too long errors
                port_input = self.port_input.text().strip()
                if not port_input:
                    port_input = "1-1000"

                # Check if the input contains ranges or is very long
                if ',' not in port_input and '-' in port_input and len(port_input) <= 20:
                    # Simple range like "1-1000" - use directly
                    command.extend([self._get_nmap_scan_flag(), "-p", port_input])
                elif len(port_input) <= 1000:
                    # Short input - use as-is
                    command.extend([self._get_nmap_scan_flag(), "-p", port_input])
                else:
                    # Very long input - use file-based approach
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                        # Parse and write individual ports to file
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

            if self.retries.value() > 0: command.extend(["--max-retries", str(self.retries.value())])
            if self.timeout.value() > 0: command.extend(["--host-timeout", f"{self.timeout.value()}s"])
            if self.max_rps.value() > 0: command.extend(["--max-rate", str(self.max_rps.value())])
            if self.delay.value() > 0: command.extend(["--scan-delay", f"{self.delay.value()}ms"])
            command.extend(targets)

            # === PRIVILEGE ESCALATION CHECK ===
            from ui.settingpanel import privilege_manager
            
            # Determine if this scan requires root privileges
            scan_flag = self._get_nmap_scan_flag()
            needs_root = (
                scan_flag in ['-sS', '-sU', '-sO'] or  # SYN, UDP, IP protocol scans
                self.os_detection_check.isChecked() or   # OS detection
                self.aggressive_scan_check.isChecked()   # Aggressive includes OS detection
            )
            
            if needs_root and privilege_manager.needs_privilege_escalation():
                # Wrap command with sudo/pkexec
                command = privilege_manager.wrap_command(command)
                stdin_data = privilege_manager.get_stdin_data()
                self._info(f"Using privilege escalation: {privilege_manager.mode}")
            else:
                stdin_data = None
                if needs_root:
                    self._info("⚠️ Warning: This scan requires root privileges. Enable in Settings or run as root.")

            if output_flag == '-oA':
                self._info(f"Scan started. Output will be saved to {log_path_base}.(nmap|xml|gnmap)")
            else:
                self._info(f"Scan started. Output will be saved to: {log_path}")
            # Add blank line after info message
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
        # Clean up temporary ports file if it exists
        if hasattr(self, '_temp_ports_file') and self._temp_ports_file:
            try:
                os.unlink(self._temp_ports_file)
                self._temp_ports_file = None
            except (OSError, AttributeError):
                pass

        self._on_scan_completed()
        if self._is_stopping:
            return
        # Only add section once, prevent duplicate
        if not self._scan_complete_added:
            self._section("Scan Complete")
            self._scan_complete_added = True

    def stop_scan(self):
        # Clean up temporary ports file if it exists
        if hasattr(self, '_temp_ports_file') and self._temp_ports_file:
            try:
                os.unlink(self._temp_ports_file)
                self._temp_ports_file = None
            except (OSError, AttributeError):
                pass

        if self.worker and self.worker.is_running:
            self._is_stopping = True
            self.worker.stop()
            self._info("Scan stopped.")
        self._on_scan_completed()

    def copy_results_to_clipboard(self):
        """Copy scan results to clipboard, not script names."""
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
