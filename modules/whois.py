import os
import subprocess
from subprocess import CalledProcessError

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


def run_whois_lookup(target: str) -> str:
    """
    Run a whois lookup and return the output as string.
    This mirrors the previous `modules/whois.py` behaviour so callers
    can use a simple function-based API.
    """
    if not target:
        raise ValueError("Target is empty")

    try:
        result = subprocess.check_output([
            "whois",
            target
        ], stderr=subprocess.STDOUT, text=True)
        return result
    except CalledProcessError as e:
        # Propagate output in exception to keep behaviour consistent
        raise RuntimeError(e.output)


class WhoisView(QWidget):
    """
    Recon → Whois Tool UI
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

        # Header
        header = QLabel("RECON  ›  Whois")
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

        # Controls
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
        self.run_button.clicked.connect(self.run_whois)

        self.stop_button = QPushButton("■")
        self.stop_button.setFixedSize(44, 36)
        self.stop_button.setToolTip("Stop Whois execution")
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
        self.stop_button.clicked.connect(self.stop_whois)

        controls.addWidget(self.target_input)
        controls.addWidget(self.run_button)
        controls.addWidget(self.stop_button)
        layout.addLayout(controls)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #1E293B;")
        layout.addWidget(divider)

        # Output
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
        self.output.setPlaceholderText("Whois results will appear here...")
        layout.addWidget(self.output)

    # ================= LOGIC =================
    def run_whois(self):
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
            self._info(
                f"Loaded {len(targets)} targets from file: {group_name}.txt"
            )
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
            self._notify("Whois scan completed")
            return

        target = self.targets_queue.pop(0)
        self._info(f"Running Whois for: {target}")
        self._section(f"WHOIS: {target}")

        base_dir = create_target_dirs(target, group_name=self.group_name)
        self.log_file = os.path.join(base_dir, "Logs", "whois.txt")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        self.all_output = []
        self.last_base_dir = base_dir

        # Create and start worker thread
        self.worker = ProcessWorker(["whois", target])
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
                self._notify(f"Whois results saved under:\n{os.path.dirname(self.last_base_dir)}")

    def _on_process_error(self, error):
        """Handle process error"""
        self._error(f"Process error: {error}")
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def stop_whois(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self._notify("Whois scan stopped")

    # ================= HELPERS =================
    def _info(self, message: str):
        self.output.appendHtml(
            f'<span style="color:#60A5FA;">[INFO]</span> {message}'
        )

    def _error(self, message: str):
        self.output.appendHtml(
            f'<span style="color:#F87171;">[ERROR]</span> {message}'
        )

    def _section(self, title: str):
        self.output.appendHtml(
            f'<br><span style="color:#FACC15;font-weight:700;">'
            f'===== {title} =====</span><br>'
        )

    def _notify(self, message: str):
        if self.main_window:
            self.main_window.notification_manager.notify(message)
