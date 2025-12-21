import os
import subprocess

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QFrame
)

from core.tgtinput import TargetInput
from ui.worker import ProcessWorker
from core.tgtinput import parse_targets
from core.fileops import create_target_dirs, get_group_name_from_file


def run_subfinder(target: str, output_dir: str) -> str:
    """
    Run subfinder tool on the target.
    Returns the output as string.
    """
    if not target:
        raise ValueError("Target is empty")

    try:
        log_file = os.path.join(output_dir, "Logs", "subfinder.txt")
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        command = f"subfinder -d {target} -silent -o {log_file}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            with open(log_file, 'r') as f:
                return f.read()
        else:
            raise RuntimeError(f"Subfinder failed: {result.stderr}")
    except Exception as e:
        raise RuntimeError(str(e))


class SubfinderView(QWidget):
    """
    Subdomain finder via Subfinder.
    """

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.worker = None
        self.log_file = None
        self.all_output = []
        self._build_ui()

    # ================= UI =================
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        header = QLabel("RECON  ›  Subfinder")
        header.setStyleSheet("""
            QLabel {
                background-color: #0F172A;
                color: #93C5FD;
                font-size: 18px;
                font-weight: 700;
                padding: 12px;
                border-radius: 8px;
            }
        """)
        layout.addWidget(header)

        controls = QHBoxLayout()
        controls.setSpacing(10)

        self.target_input = TargetInput()
        self.target_input.setStyleSheet("""
            QLineEdit {
                background-color: #020617;
                color: #E5E7EB;
                border: 1px solid #1E293B;
                padding: 10px;
                border-radius: 6px;
                font-size: 14px;
            }
        """)

        self.run_button = QPushButton("RUN")
        self.run_button.setFixedSize(90, 36)
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                font-weight: 600;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)
        self.run_button.clicked.connect(self.run_scan)

        self.stop_button = QPushButton("■")
        self.stop_button.setFixedSize(44, 36)
        self.stop_button.setToolTip("Stop Subfinder execution")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #DC2626;
                color: white;
                font-size: 16px;
                font-weight: 900;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #B91C1C;
            }
        """)
        self.stop_button.clicked.connect(self.stop_scan)

        controls.addWidget(self.target_input)
        controls.addWidget(self.run_button)
        controls.addWidget(self.stop_button)
        layout.addLayout(controls)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #1E293B;")
        layout.addWidget(divider)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(420)
        self.output.setStyleSheet("""
            QPlainTextEdit {
                background-color: #020617;
                color: #E5E7EB;
                border: 1px solid #1E293B;
                border-radius: 8px;
                padding: 12px;
                font-family: Consolas, monospace;
                font-size: 13px;
            }
        """)
        self.output.setPlaceholderText("Subfinder results will appear here...")
        layout.addWidget(self.output)

    # ================= LOGIC =================
    def run_scan(self):
        raw_input = self.target_input.get_target()

        if not raw_input:
            self._notify("Please enter a target or select a file")
            return

        targets, source = parse_targets(raw_input)

        if not targets:
            self._notify("No valid targets found")
            return

        group_name = None
        if source == "file":
            group_name = get_group_name_from_file(raw_input)
            self._info(f"Loaded {len(targets)} targets from file: {group_name}.txt")
        else:
            self._info(f"Target loaded: {targets[0]}")

        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.targets_queue = list(targets)
        self.group_name = group_name
        self._process_next_target()

    def _process_next_target(self):
        """Process targets one by one"""
        if not self.targets_queue:
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self._notify("Subfinder scan completed")
            return

        target = self.targets_queue.pop(0)
        self._info(f"Running Subfinder for: {target}")
        self._section(f"SUBFINDER: {target}")

        base_dir = create_target_dirs(target, group_name=self.group_name)
        self.log_file = os.path.join(base_dir, "Logs", "subfinder.txt")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        self.all_output = []
        self.last_base_dir = base_dir

        # Create and start worker thread
        self.worker = ProcessWorker(["subfinder", "-d", target, "-silent"])
        self.worker.output_ready.connect(self._on_output)
        self.worker.finished.connect(self._on_process_finished)
        self.worker.error.connect(self._on_process_error)
        self.worker.start()

        if self.main_window:
            self.main_window.active_process = self.worker

    def _on_output(self, line):
        """Handle output from worker thread"""
        self.all_output.append(line + "\n")
        self.output.appendPlainText(line)

    def _on_process_finished(self):
        """Handle process completion"""
        if self.log_file:
            with open(self.log_file, "w") as f:
                f.writelines(self.all_output)

        self.output.appendPlainText("\n")

        # Process next target
        if self.targets_queue:
            self._process_next_target()
        else:
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            if hasattr(self, 'last_base_dir'):
                self._notify(f"Subfinder results saved under:\n{os.path.dirname(self.last_base_dir)}")

    def _on_process_error(self, error):
        """Handle process error"""
        self._error(f"Process error: {error}")
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def stop_scan(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self._notify("Subfinder scan stopped")

    # ================= HELPERS =================
    def _info(self, message: str):
        self.output.appendHtml(f'<span style="color:#60A5FA;">[INFO]</span> {message}')

    def _error(self, message: str):
        self.output.appendHtml(f'<span style="color:#F87171;">[ERROR]</span> {message}')

    def _section(self, title: str):
        self.output.appendHtml(
            f'<br><span style="color:#FACC15;font-weight:700;">'
            f'===== {title} =====</span><br>'
        )

    def _notify(self, message: str):
        if self.main_window:
            self.main_window.notification_manager.notify(message)
