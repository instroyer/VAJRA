import os
from PySide6.QtWidgets import QLabel, QSpinBox, QHBoxLayout, QCheckBox, QVBoxLayout, QGroupBox, QLineEdit, QGridLayout
from core.tgtinput import parse_targets
from core.fileops import RESULT_BASE
from modules.bases import ToolBase, ToolCategory
from ui.styles import (
    BaseToolView, CopyButton, COLOR_TEXT_PRIMARY, COLOR_BORDER, 
    COLOR_BACKGROUND_INPUT, COLOR_BORDER_INPUT_FOCUSED
)
from ui.worker import ProcessWorker
from PySide6.QtCore import Qt


class EyewitnessView(BaseToolView):
    def _build_base_ui(self):
        super()._build_base_ui()
        self.copy_button = CopyButton(self.output.output_text, self.main_window)
        self.output.layout().addWidget(self.copy_button, 0, 0, Qt.AlignTop | Qt.AlignRight)

    def __init__(self, name, category, main_window=None):
        # Initialize attributes before calling super().__init__()
        self.timeout_spin = None
        self.threads_spin = None
        self.prepend_https_check = None
        self.no_dns_check = None
        self.user_agent_input = None
        self.delay_spin = None
        self.proxy_input = None

        super().__init__(name, category, main_window)
        # UI is built in super().__init__ which calls _build_ui, but we need to append our custom UI
        self._build_screenshot_ui()
        self.update_command()

    def _build_screenshot_ui(self):
        """Build the custom screenshot UI for eyewitness using standardized layout."""
        # Use centralized options container provided by BaseToolView
        
        # ==================== CONFIGURATION GROUP ====================
        config_group = QGroupBox("⚙️ Scan Configuration")
        config_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(10)

        # --- Row 1: Basic Options (Timeout, Threads, Delay) ---
        row1 = QHBoxLayout()
        
        # Timeout
        timeout_container = QHBoxLayout()
        timeout_label = QLabel("Timeout:")
        timeout_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix("s")
        self.timeout_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        timeout_container.addWidget(timeout_label)
        timeout_container.addWidget(self.timeout_spin)
        row1.addLayout(timeout_container)
        
        row1.addSpacing(20)

        # Threads
        threads_container = QHBoxLayout()
        threads_label = QLabel("Threads:")
        threads_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 1000)
        self.threads_spin.setValue(50)  # Default 50
        self.threads_spin.setStyleSheet(self.timeout_spin.styleSheet())
        threads_container.addWidget(threads_label)
        threads_container.addWidget(self.threads_spin)
        row1.addLayout(threads_container)
        
        row1.addSpacing(20)
        
        # Delay
        delay_container = QHBoxLayout()
        delay_label = QLabel("Delay:")
        delay_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 60)
        self.delay_spin.setValue(0)
        self.delay_spin.setSuffix("s")
        self.delay_spin.setStyleSheet(self.timeout_spin.styleSheet())
        delay_container.addWidget(delay_label)
        delay_container.addWidget(self.delay_spin)
        row1.addLayout(delay_container)
        
        row1.addStretch()
        config_layout.addLayout(row1)

        # --- Row 2: Advanced Options (User Agent, Proxy) ---
        row2 = QHBoxLayout()
        
        # User Agent
        ua_label = QLabel("User Agent:")
        ua_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.user_agent_input = QLineEdit()
        self.user_agent_input.setPlaceholderText("Default User Agent...")
        self.user_agent_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 4px;
            }}
            QLineEdit:focus {{ border: 1px solid {COLOR_BORDER_INPUT_FOCUSED}; }}
        """)
        self.user_agent_input.textChanged.connect(self.update_command)
        
        row2.addWidget(ua_label)
        row2.addWidget(self.user_agent_input, 1) # Stretch 1
        
        # Proxy
        row2.addSpacing(15)
        proxy_label = QLabel("Proxy:")
        proxy_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("http://127.0.0.1:8080")
        self.proxy_input.setStyleSheet(self.user_agent_input.styleSheet())
        self.proxy_input.textChanged.connect(self.update_command)
        
        row2.addWidget(proxy_label)
        row2.addWidget(self.proxy_input, 1) # Stretch 1
        
        config_layout.addLayout(row2)
        
        # --- Row 3: Checkboxes ---
        row3 = QHBoxLayout()
        self.prepend_https_check = QCheckBox("Prepend HTTPS")
        self.prepend_https_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        
        self.no_dns_check = QCheckBox("No DNS")
        self.no_dns_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        
        row3.addWidget(self.prepend_https_check)
        row3.addSpacing(15)
        row3.addWidget(self.no_dns_check)
        row3.addStretch()
        
        config_layout.addLayout(row3)

        # Add to centralized container
        self.options_container.addWidget(config_group)

        # Connect signals
        # Connect signals
        self.timeout_spin.valueChanged.connect(self.update_command)
        self.threads_spin.valueChanged.connect(self.update_command)
        self.prepend_https_check.stateChanged.connect(self.update_command)
        self.no_dns_check.stateChanged.connect(self.update_command)
        self.delay_spin.valueChanged.connect(self.update_command)

    def update_command(self):
        # Handle case when UI elements haven't been created yet
        if not hasattr(self, 'timeout_spin') or not self.timeout_spin:
            return

        # Build command with dynamic settings
        try:
            cmd_parts = ["eyewitness", "--web"]
            
            # Basic Options
            cmd_parts.extend(["--timeout", str(self.timeout_spin.value())])
            cmd_parts.extend(["--threads", str(self.threads_spin.value())])
            
            if self.delay_spin.value() > 0:
                cmd_parts.extend(["--delay", str(self.delay_spin.value())])

            # Checkboxes
            if self.prepend_https_check.isChecked():
                cmd_parts.append("--prepend-https")

            if self.no_dns_check.isChecked():
                cmd_parts.append("--no-dns")
                
            # Advanced Options
            if self.user_agent_input.text().strip():
                cmd_parts.extend(["--user-agent", self.user_agent_input.text().strip()])
                
            proxy_val = self.proxy_input.text().strip()
            if proxy_val and ":" in proxy_val:
                try:
                    ip, port = proxy_val.split(":", 1)
                    cmd_parts.extend(["--proxy-ip", ip, "--proxy-port", port])
                except ValueError:
                    pass # Invalid format

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
        
        # Cleanup geckodriver.log if exists
        if os.path.exists("geckodriver.log"):
            try:
                os.remove("geckodriver.log")
            except:
                pass

        # Determine if input is a file (starts with @ or implies path) or single target
        target_args = []
        
        # Check for @file syntax first
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
        
        # Check if direct file path provided without @
        elif os.path.exists(raw_input.strip()):
            # File input
            targets, source = parse_targets(raw_input)
            if not targets:
                self._notify("No valid targets found in file.")
                return

            base_name = os.path.splitext(os.path.basename(raw_input))[0]
            target_args = ["-f", raw_input]
        else:
            # Single target input
            single_target = raw_input.strip()
            if not single_target:
                self._notify("Please enter a valid target.")
                return

            # Force HTTPS if no protocol specified
            if '://' not in single_target:
                single_target = f"https://{single_target}"

            target_args = ["--single", single_target]
            base_name = single_target.replace('https://', '').replace('http://', '').replace('/', '_')

        # Create eyewitness directory directly under VAJRA results
        eyewitness_output_dir = os.path.join(RESULT_BASE, f"eyewitness_{base_name}_{self._get_timestamp()}")

        # Clean directory if it exists to avoid conflicts
        if os.path.exists(eyewitness_output_dir):
            import shutil
            shutil.rmtree(eyewitness_output_dir)
        
        # Ensure parent directory exists
        os.makedirs(RESULT_BASE, exist_ok=True)
        
        # Note: Do NOT create the eyewitness_output_dir here. 
        # EyeWitness requires the directory to NOT exist, otherwise it prompts for overwrite.
        self._info(f"Target output directory: {eyewitness_output_dir}")

        # Build eyewitness command using the command_input base command
        cmd = self.command_input.text().split()
        cmd.extend(target_args)
        cmd.extend(["-d", eyewitness_output_dir, "--no-prompt"])

        # Show start info in output
        self._info(f"Starting Eyewitness scan")
        self._info(f"Output directory: {eyewitness_output_dir}")

        # Clear any preview text from command input and show actual command
        actual_cmd = ' '.join(cmd)
        self.command_input.setText(actual_cmd)

        try:
            # Use shell=True to mimic terminal execution closely
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
        # Show ALL eyewitness output in the UI for debugging
        line = line.strip()
        if line:  # Show all non-empty output lines
            self._info(line)

    def _on_error(self, error):
        self._error(f"Eyewitness error: {error}")

    def _on_scan_completed(self):
        # Prevent double execution of completion logic
        if not self.stop_button.isEnabled():
            return

        # Cleanup geckodriver.log if exists
        if os.path.exists("geckodriver.log"):
            try:
                os.remove("geckodriver.log")
            except:
                pass
                
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self._notify("Eyewitness screenshot scan completed!")

    def stop_scan(self):
        if hasattr(self, 'worker') and self.worker and self.worker.is_running:
            self.worker.stop()
            self._notify("Eyewitness scan stopped.")
        self._on_scan_completed()

    def _get_timestamp(self):
        """Get current timestamp for directory naming."""
        from datetime import datetime
        return datetime.now().strftime("%d%m%Y_%H%M%S")


class EyewitnessTool(ToolBase):
    @property
    def name(self) -> str:
        return "Eyewitness"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WEB_SCREENSHOTS

    def get_widget(self, main_window):
        return EyewitnessView(self.name, self.category, main_window=main_window)
