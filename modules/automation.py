
import os
import subprocess
import threading
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QCheckBox
from PySide6.QtCore import Signal, QObject
from ui.main_window import BaseToolView
from core.tgtinput import parse_targets
from core.fileops import create_target_dirs, get_group_name_from_file
from core import reportgen as report
from modules.bases import ToolBase, ToolCategory
from ui.styles import (
    COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR, COLOR_INFO,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY
)

class PipelineCommunicator(QObject):
    module_started = Signal(str)
    module_finished = Signal(str, str)
    pipeline_finished = Signal(str)
    log_message = Signal(str)
    info_message = Signal(str)
    error_message = Signal(str)
    section_message = Signal(str)

class AutomationView(BaseToolView):
    def __init__(self, name, category, main_window=None):
        super().__init__(name, category, main_window)
        self.pipeline_thread = None
        self.is_running = False
        
        self.modules = {
            "Whois": {"status": "Queued"},
            "Subfinder": {"status": "Queued"},
            "Amass": {"status": "Queued"},
            "Nmap": {"status": "Queued"},
        }

        self.communicator = PipelineCommunicator()
        self._extend_ui()
        self._connect_signals()

    def _extend_ui(self):
        # Modify the base UI for this specific tool
        self.command_input.setParent(None) # Remove command input

        # Modules Status
        self.modules_group = QGroupBox("Pipeline Modules")
        self.modules_layout = QVBoxLayout(self.modules_group)
        self.modules_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        self._update_modules_display()

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        options_group.setStyleSheet("QGroupBox { font-weight: bold; } ")
        self.report_checkbox = QCheckBox("Generate HTML Report")
        self.report_checkbox.setChecked(True)
        self.report_checkbox.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}")
        options_layout.addWidget(self.report_checkbox)

        # Add new widgets to the control panel
        control_layout = self.findChild(QVBoxLayout)
        if control_layout:
            control_layout.insertWidget(4, self.modules_group)
            control_layout.insertWidget(5, options_group)

    def _connect_signals(self):
        self.run_button.clicked.connect(self.run_scan) # Base class connects this already
        self.stop_button.clicked.connect(self.stop_scan) # Base class connects this

        self.communicator.module_started.connect(lambda name: self.update_module_status(name, "Running"))
        self.communicator.module_finished.connect(self.update_module_status)
        self.communicator.pipeline_finished.connect(self.on_pipeline_finished)
        self.communicator.log_message.connect(self.output.appendPlainText)
        self.communicator.info_message.connect(self._info)
        self.communicator.error_message.connect(self._error)
        self.communicator.section_message.connect(self._section)

    def update_command(self):
        # Not needed for this tool as it runs a fixed pipeline
        pass
        
    def run_scan(self): # Overrides BaseToolView.run_scan
        raw_input = self.target_input.get_target()
        targets, source = parse_targets(raw_input)

        if not targets:
            self._notify("No valid targets found. Please enter a target.")
            return

        self.is_running = True
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.target_input.set_enabled(False)
        self.output.clear()
        self.reset_module_statuses()

        group_name = get_group_name_from_file(raw_input) if source == "file" else None
        
        self.pipeline_thread = threading.Thread(
            target=self._pipeline_worker, 
            args=(targets, group_name)
        )
        self.pipeline_thread.start()

    def stop_scan(self): # Overrides BaseToolView.stop_scan
        if self.is_running:
            self.is_running = False
            if self.main_window:
                self.main_window.stop_active_process()
            self.communicator.pipeline_finished.emit("Stopped by user.")
        super().stop_scan()

    def on_pipeline_finished(self, message):
        self.is_running = False
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.target_input.set_enabled(True)
        self._info(f"Pipeline finished: {message}")
        self._notify(f"Automation finished: {message}")

    def _pipeline_worker(self, targets, group_name):
        num_targets = len(targets)
        for i, target in enumerate(targets):
            if not self.is_running: break

            self.communicator.section_message.emit(f"STARTING TARGET {i+1}/{num_targets}: {target}")
            base_dir = create_target_dirs(target, group_name)

            self._run_module("Whois", ["whois", target], base_dir)
            self._run_module("Subfinder", ["subfinder", "-d", target, "-silent"], base_dir)
            self._run_module("Amass", ["amass", "enum", "-d", target], base_dir)
            self._run_module("Nmap", ["nmap", "-sV", "-T4", target], base_dir)

            if self.is_running and self.report_checkbox.isChecked():
                self.communicator.info_message.emit("Generating report...")
                try:
                    report.generate_report(target, base_dir, "whois subfinder amass nmap")
                    self.communicator.info_message.emit(f"Successfully generated report for {target}")
                except Exception as e:
                    self.communicator.error_message.emit(f"Report generation failed: {e}")

        if self.is_running:
            self.communicator.pipeline_finished.emit("Completed successfully.")

    def _run_module(self, name, cmd, base_dir):
        if not self.is_running: return

        self.communicator.module_started.emit(name)
        self.communicator.info_message.emit(f"Running {name}...")

        log_dir = os.path.join(base_dir, "Logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"{name.lower()}.txt")

        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, preexec_fn=os.setsid
            )
            if self.main_window: self.main_window.active_process = process
            
            with open(log_file, 'w') as f:
                for line in iter(process.stdout.readline, ''):
                    if not self.is_running:
                        # Using os.killpg and signal.SIGTERM for graceful process group termination
                        import signal
                        try:
                            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                        except ProcessLookupError:
                            pass # Process already finished
                        break
                    self.communicator.log_message.emit(line.strip())
                    f.write(line)
            
            process.wait()

            if self.is_running:
                self.communicator.module_finished.emit(name, "Completed")
            else:
                self.communicator.module_finished.emit(name, "Skipped")

        except FileNotFoundError:
            self.communicator.error_message.emit(f"{name} not found. Is it installed and in your PATH?")
            self.communicator.module_finished.emit(name, "Failed")
        except Exception as e:
            self.communicator.error_message.emit(f"An exception occurred with {name}: {e}")
            self.communicator.module_finished.emit(name, "Failed")
        finally:
            if self.main_window: self.main_window.active_process = None

    def _update_modules_display(self):
        # Clear previous labels
        while self.modules_layout.count():
            child = self.modules_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for name, data in self.modules.items():
            status = data["status"]
            status_label = QLabel(f"<b>{name}</b>: {status}")
            color = {
                "Queued": COLOR_TEXT_SECONDARY,
                "Running": COLOR_INFO,
                "Completed": COLOR_SUCCESS,
                "Skipped": COLOR_WARNING,
                "Failed": COLOR_ERROR
            }.get(status, COLOR_TEXT_PRIMARY)
            status_label.setStyleSheet(f"color: {color}; margin: 2px 0;")
            self.modules_layout.addWidget(status_label)
    
    def update_module_status(self, name, status):
        if name in self.modules:
            self.modules[name]["status"] = status
            self._update_modules_display()

    def reset_module_statuses(self):
        for name in self.modules:
            self.modules[name]["status"] = "Queued"
        self._update_modules_display()

    def closeEvent(self, event):
        self.stop_scan()
        super().closeEvent(event)

class AutomationTool(ToolBase):
    @property
    def name(self) -> str:
        return "Automation"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.AUTOMATION

    def get_widget(self, main_window: QWidget) -> QWidget:
        return AutomationView(self.name, self.category, main_window=main_window)
