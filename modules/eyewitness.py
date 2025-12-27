import os
from PySide6.QtWidgets import QLabel, QSpinBox, QHBoxLayout, QCheckBox, QSplitter
from core.tgtinput import parse_targets
from core.fileops import RESULT_BASE
from modules.bases import ToolBase, ToolCategory
from ui.main_window import BaseToolView
from ui.worker import ProcessWorker


class EyewitnessView(BaseToolView):
    def __init__(self, name, category, main_window=None):
        # Initialize attributes before calling super().__init__()
        self.timeout_spin = None
        self.threads_spin = None
        self.prepend_https_check = None
        self.no_dns_check = None

        super().__init__(name, category, main_window)
        # UI is built in super().__init__ which calls _build_ui, but we need to append our custom UI
        self._build_screenshot_ui()
        self.update_command()

    def _build_screenshot_ui(self):
        """Build the custom screenshot UI for eyewitness."""
        # Get the splitter and modify the layout
        splitter = self.findChild(QSplitter)
        if not splitter:
            return

        control_panel = splitter.widget(0)
        control_layout = control_panel.layout()

        # Remove existing stretch from control layout
        for i in range(control_layout.count()):
            item = control_layout.itemAt(i)
            if item and item.spacerItem():
                control_layout.removeItem(item)
                break

        # Single line configuration layout
        config_layout = QHBoxLayout()

        # Timeout setting
        timeout_label = QLabel("Timeout:")
        timeout_label.setStyleSheet("color: #FFFFFF; font-weight: 500;")
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix("s")
        self.timeout_spin.setStyleSheet("""
            QSpinBox {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 5px;
                min-width: 70px;
            }
        """)

        # Threads setting
        threads_label = QLabel("Threads:")
        threads_label.setStyleSheet("color: #FFFFFF; font-weight: 500; margin-left: 10px;")
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 1000)
        self.threads_spin.setValue(500)
        self.threads_spin.setStyleSheet("""
            QSpinBox {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 5px;
                min-width: 70px;
            }
        """)

        # Options checkboxes
        self.prepend_https_check = QCheckBox("Prepend HTTPS")
        self.prepend_https_check.setChecked(False)
        self.prepend_https_check.setStyleSheet("color: #FFFFFF; margin-left: 10px;")

        self.no_dns_check = QCheckBox("No DNS")
        self.no_dns_check.setStyleSheet("color: #FFFFFF; margin-left: 10px;")

        # Add all to single layout
        config_layout.addWidget(timeout_label)
        config_layout.addWidget(self.timeout_spin)
        config_layout.addWidget(threads_label)
        config_layout.addWidget(self.threads_spin)
        config_layout.addWidget(self.prepend_https_check)
        config_layout.addWidget(self.no_dns_check)
        config_layout.addStretch()
        
        control_layout.addLayout(config_layout)

        # Connect signals
        self.timeout_spin.valueChanged.connect(self.update_command)
        self.threads_spin.valueChanged.connect(self.update_command)
        self.prepend_https_check.stateChanged.connect(self.update_command)
        self.no_dns_check.stateChanged.connect(self.update_command)

    def update_command(self):
        # Handle case when UI elements haven't been created yet
        if hasattr(self, 'timeout_spin') and self.timeout_spin:
            # Build command with dynamic settings
            timeout = self.timeout_spin.value()
            threads = self.threads_spin.value()

            cmd_parts = ["eyewitness", "--web", "--timeout", str(timeout), "--threads", str(threads)]

            if self.prepend_https_check.isChecked():
                cmd_parts.append("--prepend-https")

            if self.no_dns_check.isChecked():
                cmd_parts.append("--no-dns")

            self.command_input.setText(" ".join(cmd_parts))
        else:
            self.command_input.setText("eyewitness --web --timeout 30 --threads 500")

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
