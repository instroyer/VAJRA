# =============================================================================
# modules/nmap.py
#
# Nmap - Network Mapper Port Scanner (STABLE REFACTOR)
# =============================================================================

import os
import shlex
import tempfile
import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QMessageBox, QInputDialog, QLineEdit
)

from modules.bases import ToolBase, ToolCategory
from core.tgtinput import parse_targets, TargetInput, parse_port_range
from core.fileops import create_target_dirs
from ui.worker import ToolExecutionMixin
from ui.styles import (
    # Widgets
    RunButton, StopButton, CopyButton,
    StyledLineEdit, StyledSpinBox, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, OutputView,
    StyledGroupBox, ToolSplitter, StyledToolView, ConfigTabs
)

# =============================================================================
# Tool Registration (MANDATORY FOR SIDEBAR)
# =============================================================================

class NmapScanner(ToolBase):

    name = "Nmap"
    category = ToolCategory.PORT_SCANNING

    def get_widget(self, main_window: QWidget) -> QWidget:
        return NmapScannerView(main_window)


# =============================================================================
# Tool View
# =============================================================================

class NmapScannerView(StyledToolView, ToolExecutionMixin):

    tool_name = "Nmap"
    tool_category = "PORT_SCANNING"

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_safe_stop()

        self._temp_ports_file = None
        self.nmap_scripts = self._get_nmap_scripts()

        self._build_ui()
        self.update_command()

    # -------------------------------------------------------------------------
    # Command Builder (SINGLE SOURCE OF TRUTH)
    # -------------------------------------------------------------------------

    def build_command(self, preview: bool = False) -> str:
        """
        Builds the Nmap command string.
        
        Args:
            preview: If True, uses placeholders for missing/dynamic values.
                     If False, strict validation is applied.
        
        Returns:
            The fully quoted command string safe for execution.
        """
        cmd = ["nmap"]

        # Target
        target = self.target_input.get_target().strip()
        if not target:
            if preview:
                target = "<target>"
            else:
                raise ValueError("Target is required")
        
        # Speed
        cmd.append(self._get_speed_flag())

        # Host Scan
        host_scan = self._get_host_scan_flag()
        if host_scan:
            cmd.append(host_scan)

        # Scan Type & Ports
        if host_scan not in ("-sL", "-sn"):
            ports = self.port_input.text().strip() or "1-1000"
            scan_flag = self._get_nmap_scan_flag()

            if len(ports) <= 1000:
                cmd.extend([scan_flag, "-p", ports])
            else:
                if preview:
                    cmd.extend([scan_flag, "-p", "<ports-file>"])
                else:
                    self._temp_ports_file = self._create_ports_file(ports)
                    cmd.extend([scan_flag, "-iL", self._temp_ports_file])

        # Feature Flags
        if self.aggressive_scan_check.isChecked():
            cmd.append("-A")
        if self.traceroute_check.isChecked():
            cmd.append("--traceroute")
        if self.service_version_check.isChecked():
            cmd.append("-sV")
        if self.os_detection_check.isChecked():
            cmd.append("-O")

        # Scripts
        script = self.script_input.currentText().strip()
        if script and script != "(None)":
            cmd.extend(["--script", script])

        # Timing & Rate
        if self.retries.value() > 0:
            cmd.extend(["--max-retries", str(self.retries.value())])
        if self.timeout.value() > 0:
            cmd.extend(["--host-timeout", f"{self.timeout.value()}s"])
        if self.max_rps.value() > 0:
            cmd.extend(["--max-rate", str(self.max_rps.value())])
        if self.delay.value() > 0:
            cmd.extend(["--scan-delay", f"{self.delay.value()}ms"])

        # Output Flags (Runtime only)
        if not preview and self._current_output_flag and self._current_log_base:
            cmd.append(self._current_output_flag)
            if self._current_output_flag == "-oA":
                cmd.append(self._current_log_base)
            else:
                # Append extension based on the flag type
                ext = ""
                if self._current_output_flag == "-oN": ext = ".txt"
                elif self._current_output_flag == "-oG": ext = ".gnmap"
                elif self._current_output_flag == "-oX": ext = ".xml"
                cmd.append(f"{self._current_log_base}{ext}")

        # Target (Last)
        cmd.append(target)

        return " ".join(shlex.quote(x) for x in cmd)

    # -------------------------------------------------------------------------
    # UI Helpers
    # -------------------------------------------------------------------------

    def update_command(self):
        try:
            cmd_str = self.build_command(preview=True)
            self.command_input.setText(cmd_str)
        except ValueError:
            self.command_input.setText("")  # Clear if invalid
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------

    def run_scan(self):
        # Parse target first
        target_str = self.target_input.get_target().strip()
        if not target_str:
            QMessageBox.warning(self, "Warning", "No valid targets specified.")
            return

        try:
            # 1. Setup Environment & Output Paths
            targets = parse_targets(target_str)[0]
            if not targets:
                raise ValueError("No valid targets found")

            base_dir = create_target_dirs(targets[0])
            logs_dir = os.path.join(base_dir, "Logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            # Set state for build_command
            self._current_output_flag, _ = self._get_output_args()
            self._current_log_base = os.path.join(logs_dir, "nmap")

            # 2. Build Command
            cmd_str = self.build_command(preview=False)

            # 3. Start Execution (Mixin handles UI state)
            # Pass output path to mixin for final reporting
            output_display_path = self._current_log_base if self._current_output_flag else None
            self.start_execution(cmd_str, output_display_path, buffer_output=False)



        except Exception as e:
            self._error(str(e))
            self._cleanup()
    
    def on_new_output(self, text):
        clean = text.strip()
        if clean:
            self._raw(html.escape(clean))

    def on_finished(self):
        self._cleanup()
        self.on_execution_finished(success=True)

    
    def _cleanup(self):
        # Reset state
        self._current_output_flag = None
        self._current_log_base = None

        if self._temp_ports_file:
            try:
                os.unlink(self._temp_ports_file)
            except Exception:
                pass
            self._temp_ports_file = None

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    def _create_ports_file(self, ports):
        ports_list = sorted(parse_port_range(ports))
        # Use mkstemp for secure temporary file creation
        fd, temp_path = tempfile.mkstemp(prefix="nmap_ports_", suffix=".txt", text=True)
        try:
            with os.fdopen(fd, 'w') as f:
                f.write("\n".join(map(str, ports_list)))
            return temp_path
        except Exception:
            # fd is already closed by os.fdopen context manager, so no need to close here
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    def _get_nmap_scripts(self):
        """Retrieve list of nmap scripts."""
        scripts = ["(None)", "vuln", "default", "banner", "http-enum", "http-title"]
        # Basic check for common location
        script_dir = "/usr/share/nmap/scripts"
        if os.path.exists(script_dir):
            try:
                found = sorted([f for f in os.listdir(script_dir) if f.endswith(".nse")])
                scripts.extend(found)
            except Exception:
                pass
        return scripts

    def _get_speed_flag(self):
        # Placeholder T3 until UI is added or linked to retries logic properly
        return "-T3"

    def _get_host_scan_flag(self):
        if self.host_scan_combo.currentText() == "No Ping (-Pn)":
            return "-Pn"
        elif self.host_scan_combo.currentText() == "Ping Scan (-sn)":
            return "-sn"
        elif self.host_scan_combo.currentText() == "List Scan (-sL)":
            return "-sL"
        return ""

    def _get_nmap_scan_flag(self):
        scan_map = {
            "SYN Scan (-sS)": "-sS",
            "TCP Connect (-sT)": "-sT",
            "UDP Scan (-sU)": "-sU",
            "ACK Scan (-sA)": "-sA"
        }
        return scan_map.get(self.scan_type_combo.currentText(), "-sS")

    def _get_output_args(self):
        flags = {
            "Terminal Only": "", # Added for the new combo box
            "Normal (-oN)": "-oN",
            "Grepable (-oG)": "-oG",
            "XML (-oX)": "-oX",
            "All (-oA)": "-oA"
        }
        flag = flags.get(self.output_format_combo.currentText(), "")
        ext = ""
        if flag == "-oN": ext = ".txt"
        elif flag == "-oG": ext = ".gnmap"
        elif flag == "-oX": ext = ".xml"
        return flag, ext

    # -------------------------------------------------------------------------
    # UI Builder
    # -------------------------------------------------------------------------

    def _build_ui(self):
        """Construct the UI using centralized styles."""
        # setStyleSheet handled by StyledToolView
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter
        splitter = ToolSplitter()
        main_layout.addWidget(splitter)

        # === Input Panel ===
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_layout.setContentsMargins(20, 20, 20, 20)
        input_layout.setSpacing(20) # Increased spacing between groups

        # Header
        input_layout.addWidget(HeaderLabel("PORT SCANNING", "Nmap"))

        # --- 1. Scan Configuration Group ---
        scan_group = StyledGroupBox("Scan Configuration")
        scan_layout = QGridLayout(scan_group)
        scan_layout.setVerticalSpacing(10)
        scan_layout.setHorizontalSpacing(15)

        # Target (Full Width)
        scan_layout.addWidget(StyledLabel("Target:"), 0, 0)
        self.target_input = TargetInput()
        self.target_input.input_box.textChanged.connect(self.update_command)
        scan_layout.addWidget(self.target_input, 0, 1, 1, 3) # Span 3 columns

        # Row 2: Scan Type & Host Discovery
        scan_layout.addWidget(StyledLabel("Scan Type:"), 1, 0)
        self.scan_type_combo = StyledComboBox()
        self.scan_type_combo.addItems(["SYN Scan (-sS)", "TCP Connect (-sT)", "UDP Scan (-sU)", "ACK Scan (-sA)"])
        self.scan_type_combo.currentTextChanged.connect(self.update_command)
        scan_layout.addWidget(self.scan_type_combo, 1, 1)

        scan_layout.addWidget(StyledLabel("Host Discovery:"), 1, 2)
        self.host_scan_combo = StyledComboBox()
        self.host_scan_combo.addItem("Default Host Discovery")
        self.host_scan_combo.addItems(["No Ping (-Pn)", "Ping Scan (-sn)", "List Scan (-sL)"])
        self.host_scan_combo.currentTextChanged.connect(self.update_command)
        scan_layout.addWidget(self.host_scan_combo, 1, 3)

        # Row 3: Ports & Scripts
        scan_layout.addWidget(StyledLabel("Ports:"), 2, 0)
        self.port_input = StyledLineEdit("1-1000")
        self.port_input.textChanged.connect(self.update_command)
        scan_layout.addWidget(self.port_input, 2, 1)

        scan_layout.addWidget(StyledLabel("Script:"), 2, 2)
        self.script_input = StyledComboBox()
        self.script_input.setEditable(True) # Allow typing script names
        self.script_input.addItems(self.nmap_scripts)
        self.script_input.currentTextChanged.connect(self.update_command)
        scan_layout.addWidget(self.script_input, 2, 3)
        
        # Column stretch
        scan_layout.setColumnStretch(1, 1)
        scan_layout.setColumnStretch(3, 1)

        input_layout.addWidget(scan_group)

        # --- 2. Options Group ---
        options_group = StyledGroupBox("Options")
        options_layout = QGridLayout(options_group)
        options_layout.setVerticalSpacing(10)
        options_layout.setHorizontalSpacing(20)

        self.service_version_check = StyledCheckBox("Service Version (-sV)")
        self.os_detection_check = StyledCheckBox("OS Detection (-O)")
        self.aggressive_scan_check = StyledCheckBox("Aggressive (-A)")
        self.traceroute_check = StyledCheckBox("Traceroute")
        
        for chk in [self.service_version_check, self.os_detection_check, 
                   self.aggressive_scan_check, self.traceroute_check]:
            chk.stateChanged.connect(self.update_command)

        options_layout.addWidget(self.service_version_check, 0, 0)
        options_layout.addWidget(self.os_detection_check, 0, 1)
        options_layout.addWidget(self.aggressive_scan_check, 1, 0)
        options_layout.addWidget(self.traceroute_check, 1, 1)
        
        # Add a stretch or ensure columns are even
        options_layout.setColumnStretch(0, 1)
        options_layout.setColumnStretch(1, 1)

        input_layout.addWidget(options_group)

        # --- 3. Performance & Timing Group ---
        perf_group = StyledGroupBox("Performance & Timing")
        perf_layout = QGridLayout(perf_group)
        perf_layout.setVerticalSpacing(10)
        perf_layout.setHorizontalSpacing(15)

        # Row 1: Retries & Timeout
        perf_layout.addWidget(StyledLabel("Max Retries:"), 0, 0)
        self.retries = StyledSpinBox()
        self.retries.setRange(0, 10)
        self.retries.setValue(0)
        self.retries.valueChanged.connect(self.update_command)
        perf_layout.addWidget(self.retries, 0, 1)

        perf_layout.addWidget(StyledLabel("Timeout (s):"), 0, 2)
        self.timeout = StyledSpinBox()
        self.timeout.setRange(0, 9999)
        self.timeout.setValue(0)
        self.timeout.valueChanged.connect(self.update_command)
        perf_layout.addWidget(self.timeout, 0, 3)

        # Row 2: Rate & Delay
        perf_layout.addWidget(StyledLabel("Max Rate:"), 1, 0)
        self.max_rps = StyledSpinBox()
        self.max_rps.setRange(0, 50000)
        self.max_rps.setValue(0)
        self.max_rps.valueChanged.connect(self.update_command)
        perf_layout.addWidget(self.max_rps, 1, 1)
        
        perf_layout.addWidget(StyledLabel("Delay (ms):"), 1, 2)
        self.delay = StyledSpinBox()
        self.delay.setRange(0, 5000)
        self.delay.setValue(0)
        self.delay.valueChanged.connect(self.update_command)
        perf_layout.addWidget(self.delay, 1, 3)
        
        # Column stretch
        perf_layout.setColumnStretch(1, 1)
        perf_layout.setColumnStretch(3, 1)

        input_layout.addWidget(perf_group)

        # --- 4. Control & Output ---
        control_row = QHBoxLayout()
        control_row.setSpacing(10)
        
        control_row.addWidget(StyledLabel("Output Format:"))
        self.output_format_combo = StyledComboBox()
        self.output_format_combo.addItems(["Terminal Only", "Normal (-oN)", "Grepable (-oG)", "XML (-oX)", "All (-oA)"])
        self.output_format_combo.setCurrentIndex(1) # Default to Normal (-oN)
        control_row.addWidget(self.output_format_combo)
        
        control_row.addStretch()
        
        self.run_button = RunButton("RUN SCAN")
        self.run_button.clicked.connect(self.run_scan)
        
        self.stop_button = StopButton()
        self.stop_button.clicked.connect(self.stop_scan)

        control_row.addWidget(self.run_button)
        control_row.addWidget(self.stop_button)
        
        input_layout.addLayout(control_row)

        # Command Preview
        self.command_input = StyledLineEdit()
        self.command_input.setReadOnly(True)
        self.command_input.setPlaceholderText("Command preview...")
        input_layout.addWidget(self.command_input)

        # Spacer to push everything up
        input_layout.addStretch()

        splitter.addWidget(input_widget)

        # === Output Panel ===
        self.output = OutputView(self.main_window)
        splitter.addWidget(self.output)
        
        # Initial Sizes
        splitter.setSizes([550, 250])
