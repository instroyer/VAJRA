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

from ui.widgets.target_input import TargetInput
from core.target_parser import parse_targets
from core.file_ops import create_target_dirs, get_group_name_from_file


def run_screenshot(target: str, output_dir: str) -> str:
    """
    Run eyewitness tool on the target.
    Returns the output as string.
    """
    if not target:
        raise ValueError("Target is empty")

    try:
        screenshot_dir = os.path.join(output_dir, "Screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)

        if target.startswith('@'):
            input_file = target[1:]
            if not os.path.isfile(input_file):
                raise RuntimeError(f"File not found: {input_file}")
            command = f"eyewitness --web --timeout 30 --threads 500 --prepend-https -f {input_file} -d {screenshot_dir} --no-prompt"
        else:
            if not target.startswith(('http://', 'https://')):
                target_url = f"https://{target}"
            else:
                target_url = target
            command = f"eyewitness --web --timeout 30 --threads 500 --prepend-https --single {target_url} -d {screenshot_dir} --no-prompt"

        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            return f"Screenshots saved to: {screenshot_dir}"
        else:
            raise RuntimeError(f"Eyewitness failed: {result.stderr}")
    except Exception as e:
        raise RuntimeError(str(e))


class ScreenshotView(QWidget):
    """
    Web screenshot capture via Eyewitness.
    """

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._build_ui()

    # ================= UI =================
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        header = QLabel("RECON  ›  Screenshot")
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
        self.stop_button.setToolTip("Stop Screenshot execution")
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
        self.output.setPlaceholderText("Screenshot results will appear here...")
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

        last_base_dir = None

        for target in targets:
            self._info(f"Capturing screenshots for: {target}")
            self._section(f"SCREENSHOT: {target}")

            base_dir = create_target_dirs(target, group_name=group_name)
            last_base_dir = base_dir

            try:
                output = run_screenshot(target, base_dir)
                self.output.appendPlainText(output + "\n")
            except RuntimeError as e:
                self._error(str(e))

        if last_base_dir:
            self._notify(f"Screenshots saved under:\n{os.path.dirname(last_base_dir)}")

    def stop_scan(self):
        if self.main_window:
            self.main_window.stop_active_process()

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
