
import os
import subprocess
import threading
from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QFrame,
    QGroupBox,
)
from modules.bases import ToolBase, ToolCategory
from core.tgtinput import TargetInput, parse_targets
from core.fileops import create_target_dirs, get_group_name_from_file
from core import reportgen as report
from ui.styles import (
    OUTPUT_TEXT_EDIT_STYLE,
    RUN_BUTTON_STYLE,
    STOP_BUTTON_STYLE,
    DIVIDER_STYLE,
    COLOR_SUCCESS,
    COLOR_WARNING,
    COLOR_ERROR,
    COLOR_INFO,
)


class Status:
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    SKIPPED = "Skipped"
    ERROR = "Error"
    TERMINATED = "Terminated"


class AutomationWorker(QObject):
    status_update = Signal(str, str)
    output = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, target, base_dir, main_window):
        super().__init__()
        self.target = target
        self.base_dir = base_dir
        self.main_window = main_window
        self.current_process = None
        self.is_running = True
        self.is_skipping = False

    def run(self):
        """Executes the entire, sequential pipeline."""
        pipeline = [
            {"key": "whois", "name": "Whois", "func": self._run_whois},
            {"key": "subfinder", "name": "Subfinder", "func": self._run_subfinder},
            {"key": "amass", "name": "Amass", "func": self._run_amass},
            {"key": "httpx", "name": "HTTPX", "func": self._run_httpx},
            {"key": "nmap", "name": "Nmap", "func": self._run_nmap},
            {"key": "report", "name": "Report Generation", "func": self._run_reportgen},
        ]

        modules_run_for_report = []

        for step in pipeline:
            if not self.is_running:
                break

            self.is_skipping = False
            self.status_update.emit(step["key"], Status.RUNNING)

            success = step["func"]()

            if self.is_skipping:
                self.status_update.emit(step["key"], Status.SKIPPED)
                self.output.emit(f'<span style="color:#F59E0B;">[SKIP]</span> {step["name"]} was skipped.<br>')
            elif not self.is_running:
                self.status_update.emit(step["key"], Status.TERMINATED)
                self.output.emit(f'<span style="color:{COLOR_ERROR}; font-weight:700;">[TERMINATED]</span> {step["name"]} was terminated.<br>')
                break
            elif success:
                self.status_update.emit(step["key"], Status.COMPLETED)
                modules_run_for_report.append(step["key"])
            else:
                self.status_update.emit(step["key"], Status.ERROR)

        if "report" in modules_run_for_report:
            report.generate_report(self.target, self.base_dir, " ".join(m for m in modules_run_for_report if m != 'report'))

        self.finished.emit()

    def stop(self):
        self.is_running = False
        if self.current_process and self.current_process.poll() is None:
            self.current_process.kill()

    def skip(self):
        self.is_skipping = True
        if self.current_process and self.current_process.poll() is None:
            self.current_process.kill()

    def _execute_command(self, cmd, log_file, shell=False):
        log_path = os.path.join(self.base_dir, "Logs", log_file)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        try:
            self.current_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=shell, bufsize=1, universal_newlines=True
            )
            with open(log_path, "w") as f:
                for line in iter(self.current_process.stdout.readline, ""):
                    if not self.is_running or self.is_skipping:
                        break
                    self.output.emit(line)
                    f.write(line)
            self.current_process.wait()
            return self.current_process.returncode == 0
        except FileNotFoundError:
            self.error.emit(f"Command not found: {cmd[0]}. Is it in your PATH?")
            return False
        except Exception as e:
            self.error.emit(f"Error executing {' '.join(cmd)}: {e}")
            return False
        finally:
            self.current_process = None

    def _run_whois(self):
        return self._execute_command(["whois", self.target], "whois.txt")

    def _run_subfinder(self):
        sub_log = os.path.join(self.base_dir, "Subdomains", "subfinder.txt")
        return self._execute_command(["subfinder", "-d", self.target, "-o", sub_log, "-silent"], "subfinder.out")

    def _run_amass(self):
        amass_log = os.path.join(self.base_dir, "Subdomains", "amass.txt")
        return self._execute_command(["amass", "enum", "-d", self.target, "-o", amass_log], "amass.out")

    def _run_httpx(self):
        self.output.emit(f'<span style="color:{COLOR_INFO};">[INFO]</span> Merging subdomains for HTTPX scan...<br>')
        sub_dir = os.path.join(self.base_dir, "Subdomains")
        all_subs = set()
        for f in os.listdir(sub_dir):
            if f.endswith(".txt"):
                with open(os.path.join(sub_dir, f), 'r') as reader:
                    all_subs.update(line.strip() for line in reader)

        merged_file = os.path.join(sub_dir, "merged_subdomains.txt")
        with open(merged_file, 'w') as writer:
            for sub in sorted(list(all_subs)):
                writer.write(f"{sub}\n")

        self.output.emit(f'<span style="color:{COLOR_INFO};">[INFO]</span> Found {len(all_subs)} unique subdomains.<br>')

        httpx_out = os.path.join(self.base_dir, "Probed", "httpx_probed.txt")
        return self._execute_command(["httpx-toolkit", "-l", merged_file, "-o", httpx_out, "-silent"], "httpx.out")

    def _run_nmap(self):
        probed_file = os.path.join(self.base_dir, "Probed", "httpx_probed.txt")
        if not os.path.exists(probed_file) or os.path.getsize(probed_file) == 0:
            self.error.emit("Cannot run Nmap, no live hosts from HTTPX.")
            return False

        nmap_out = os.path.join(self.base_dir, "Scans", "nmap_scan.xml")
        return self._execute_command(["nmap", "-iL", probed_file, "-T4", "-A", "-oX", nmap_out], "nmap.out")

    def _run_reportgen(self):
        self.output.emit(f'<span style="color:{COLOR_INFO};">[INFO]</span> Final report will be generated shortly...<br>')
        return True

class Automation(ToolBase):
    @property
    def name(self) -> str: return "Automation"
    @property
    def category(self) -> ToolCategory: return ToolCategory.AUTOMATION
    def get_widget(self, main_window: QWidget) -> QWidget:
        return AutomationView(main_window=main_window)

class AutomationView(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.worker = None
        self.worker_thread = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        controls = QHBoxLayout()
        self.target_input = TargetInput()
        controls.addWidget(self.target_input)

        self.run_button = QPushButton("RUN")
        self.run_button.setStyleSheet(RUN_BUTTON_STYLE)
        self.run_button.setFixedSize(90, 36)
        self.run_button.clicked.connect(self.run_pipeline)
        controls.addWidget(self.run_button)

        self.skip_button = QPushButton("SKIP")
        self.skip_button.setEnabled(False)
        self.skip_button.setFixedSize(70, 36)
        self.skip_button.setStyleSheet('''
            QPushButton {
                background-color: #F59E0B; color: black; font-weight: 700; border-radius: 6px;
            }
            QPushButton:disabled {
                background-color: #374151; color: #9CA3AF;
            }
        ''')
        self.skip_button.clicked.connect(self.skip_step)
        controls.addWidget(self.skip_button)

        self.stop_button = QPushButton("■")
        self.stop_button.setStyleSheet(STOP_BUTTON_STYLE)
        self.stop_button.setFixedSize(44, 36)
        self.stop_button.clicked.connect(self.stop_pipeline)
        self.stop_button.setEnabled(False)
        controls.addWidget(self.stop_button)

        layout.addLayout(controls)

        status_group = QGroupBox("Live Execution Status")
        status_layout = QVBoxLayout(); status_layout.setSpacing(8)
        self.status_labels = {}
        modules = [("whois", "Whois"), ("subfinder", "Subfinder"), ("amass", "Amass"), ("httpx", "HTTPX"), ("nmap", "Nmap"), ("report", "Report Generation")]
        for key, name in modules:
            row = QHBoxLayout()
            name_label = QLabel(f"{name}:"); name_label.setFixedWidth(150)
            status_label = QLabel(Status.PENDING)
            self.status_labels[key] = status_label
            row.addWidget(name_label); row.addWidget(status_label); row.addStretch()
            status_layout.addLayout(row)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        divider = QFrame(); divider.setFrameShape(QFrame.HLine); divider.setStyleSheet(DIVIDER_STYLE)
        layout.addWidget(divider)

        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUTPUT_TEXT_EDIT_STYLE)
        self.output.setPlaceholderText("Pipeline output will appear here...")
        results_layout.addWidget(self.output)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

    def run_pipeline(self):
        raw_input = self.target_input.get_target()
        targets, source = parse_targets(raw_input)
        if not targets: self._notify("No valid target specified."); return

        self.output.clear()
        for key in self.status_labels: self.update_status(key, Status.PENDING)

        self.run_button.setEnabled(False); self.skip_button.setEnabled(True); self.stop_button.setEnabled(True)

        target = targets[0]
        group_name = get_group_name_from_file(raw_input) if source == "file" else None
        base_dir = create_target_dirs(target, group_name)

        self.worker = AutomationWorker(target, base_dir, self.main_window)
        self.worker_thread = threading.Thread(target=self.worker.run)
        self.worker.status_update.connect(self.update_status)
        self.worker.output.connect(self.append_output)
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.on_pipeline_finished)
        self.worker_thread.start()

    def skip_step(self):
        if self.worker: self.worker.skip()

    def stop_pipeline(self):
        self.run_button.setEnabled(True); self.skip_button.setEnabled(False); self.stop_button.setEnabled(False)
        if self.worker: self.worker.stop()
        self._notify("Pipeline stop requested.")

    def on_pipeline_finished(self):
        self.run_button.setEnabled(True); self.skip_button.setEnabled(False); self.stop_button.setEnabled(False)
        self.worker_thread = None; self.worker = None
        self._notify("Automation pipeline has finished.")

    def update_status(self, key, status):
        label = self.status_labels.get(key)
        if not label: return
        label.setText(status)
        color = {
            Status.PENDING: "#9CA3AF",
            Status.RUNNING: "#3B82F6",
            Status.COMPLETED: COLOR_SUCCESS,
            Status.SKIPPED: COLOR_WARNING,
            Status.ERROR: COLOR_ERROR,
            Status.TERMINATED: COLOR_ERROR
        }.get(status, "#E5E7EB")
        label.setStyleSheet(f"color: {color}; font-weight: 700;")

    def append_output(self, text):
        self.output.appendHtml(text.strip().replace("\n", "<br>"))
        self.output.verticalScrollBar().setValue(self.output.verticalScrollBar().maximum())

    def show_error(self, msg):
        self.output.appendHtml(f'<span style="color:{COLOR_ERROR}; font-weight:700;">[ERROR]</span> {msg}<br>')

    def _notify(self, msg):
        if self.main_window: self.main_window.notification_manager.notify(msg)
