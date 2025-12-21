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
from core.tgtinput import parse_targets
from core.fileops import create_target_dirs, get_group_name_from_file
from core import reportgen as report


class AutomationView(QWidget):
    """
    VAJRA Automation – Full Recon Pipeline
    Supports runtime SKIP of current module.
    """

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window

        self.current_process = None
        self.current_module = None
        self.skip_current = False

        self._build_ui()

    # ================= UI =================
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        header = QLabel("AUTOMATION  ›  Full Recon Pipeline")
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

        self.target_input = TargetInput()

        self.run_button = QPushButton("RUN")
        self.run_button.setFixedSize(90, 36)
        self.run_button.clicked.connect(self.run_pipeline)

        self.skip_button = QPushButton("SKIP")
        self.skip_button.setFixedSize(70, 36)
        self.skip_button.setEnabled(False)
        self.skip_button.setStyleSheet("""
            QPushButton {
                background-color: #F59E0B;
                color: black;
                font-weight: 700;
                border-radius: 6px;
            }
            QPushButton:disabled {
                background-color: #374151;
                color: #9CA3AF;
            }
        """)
        self.skip_button.clicked.connect(self.skip_module)

        self.stop_button = QPushButton("■")
        self.stop_button.setFixedSize(44, 36)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #DC2626;
                color: white;
                font-size: 16px;
                font-weight: 900;
                border-radius: 6px;
            }
        """)
        self.stop_button.clicked.connect(self.stop_pipeline)

        controls.addWidget(self.target_input)
        controls.addWidget(self.run_button)
        controls.addWidget(self.skip_button)
        controls.addWidget(self.stop_button)
        layout.addLayout(controls)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color:#1E293B;")
        layout.addWidget(divider)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(460)
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
        layout.addWidget(self.output)

    # ================= PIPELINE =================
    def run_pipeline(self):
        raw_input = self.target_input.get_target()
        targets, source = parse_targets(raw_input)

        if not targets:
            self._notify("No valid targets found")
            return

        self.run_button.setEnabled(False)
        self.skip_button.setEnabled(True)

        group_name = None
        if source == "file":
            group_name = get_group_name_from_file(raw_input)
            self._info(f"Loaded {len(targets)} targets from file: {group_name}.txt")
        else:
            self._info(f"Target loaded: {targets[0]}")

        for target in targets:
            base_dir = create_target_dirs(target, group_name=group_name)
            self._section(f"TARGET: {target}")

            self._run_module("Whois", ["whois", target], base_dir)
            self._run_module("Subfinder", ["subfinder", "-d", target, "-silent"], base_dir)
            self._run_module("Nmap", ["nmap", "-sV", "-T4", target], base_dir)
            self._run_module("Nikto", ["nikto", "-h", target], base_dir)

            self._info("Generating report")
            report.generate_report(target, base_dir, "whois subfinder nmap nikto")

        self.run_button.setEnabled(True)
        self.skip_button.setEnabled(False)

        self._notify("Automation completed")

    def _run_module(self, name, cmd, base_dir):
        self.skip_current = False
        self.current_module = name

        self._info(f"Running {name} for current target")
        self._section(name.upper())

        log_file = os.path.join(base_dir, "Logs", f"{name.lower()}.txt")

        self.current_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        if self.main_window:
            self.main_window.active_process = self.current_process

        output, _ = self.current_process.communicate()

        if self.skip_current:
            self._info(f"[SKIP] {name} skipped by user")
            return

        with open(log_file, "w") as f:
            f.write(output)

        self.output.appendPlainText(output + "\n")

    # ================= CONTROLS =================
    def skip_module(self):
        if self.current_process and self.current_process.poll() is None:
            self.skip_current = True
            self.current_process.kill()
            self._notify(f"{self.current_module} skipped")

    def stop_pipeline(self):
        if self.main_window:
            self.main_window.stop_active_process()
        self.run_button.setEnabled(True)
        self.skip_button.setEnabled(False)

    # ================= HELPERS =================
    def _info(self, msg):
        self.output.appendHtml(
            f'<span style="color:#60A5FA;">[INFO]</span> {msg}'
        )

    def _section(self, title):
        self.output.appendHtml(
            f'<br><span style="color:#FACC15;font-weight:700;">'
            f'===== {title} =====</span><br>'
        )

    def _notify(self, msg):
        if self.main_window:
            self.main_window.notification_manager.notify(msg)
