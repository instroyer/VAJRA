import os
import subprocess

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QFrame,
    QComboBox
)

from core.tgtinput import TargetInput
from ui.worker import ProcessWorker
from core.tgtinput import parse_targets
from core.fileops import create_target_dirs, get_group_name_from_file


SCAN_TYPES = {
    "quick": {
        "name": "Quick Scan (Top 1000 ports)",
        "args": ["-T4", "--top-ports", "1000", "-sS", "-sV", "-O"],
        "files": ("nmap_top1000.txt", "nmap_top1000.xml")
    },
    "full": {
        "name": "Full Port Scan (1-65535)",
        "args": ["-T4", "-p-", "-sS", "-sV", "-O"],
        "files": ("nmap_full.txt", "nmap_full.xml")
    },
    "fast": {
        "name": "Fast Scan (-A)",
        "args": ["-T4", "-A"],
        "files": ("nmap_fastA.txt", "nmap_fastA.xml")
    },
    "udp": {
        "name": "UDP Scan (Top 100 UDP ports)",
        "args": ["-T4", "-sU", "--top-ports", "100"],
        "files": ("nmap_udp.txt", "nmap_udp.xml")
    }
}


def run_nmap(target: str, output_dir: str, scan_type: str = "quick") -> str:
    """
    Run nmap scan on the target.
    Returns the output as string.
    """
    if not target:
        raise ValueError("Target is empty")

    if scan_type not in SCAN_TYPES:
        scan_type = "quick"

    try:
        logs_dir = os.path.join(output_dir, "Logs")
        os.makedirs(logs_dir, exist_ok=True)

        scan_config = SCAN_TYPES[scan_type]
        txt_file, xml_file = scan_config["files"]
        txt_path = os.path.join(logs_dir, txt_file)
        xml_path = os.path.join(logs_dir, xml_file)

        cmd = ["nmap", target] + scan_config["args"] + ["-oN", txt_path, "-oX", xml_path]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and os.path.exists(txt_path):
            with open(txt_path, 'r') as f:
                return f.read()
        else:
            raise RuntimeError(f"Nmap failed: {result.stderr}")
    except Exception as e:
        raise RuntimeError(str(e))


class NmapView(QWidget):
    """
    Port scanning via Nmap.
    """

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.worker = None
        self.log_file = None
        self.all_output = []
        self.current_process = None
        self._build_ui()

    # ================= UI =================
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        header = QLabel("RECON  ›  Nmap")
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
        layout.addWidget(self.target_input)

        # Scan type selector (below target)
        scan_type_layout = QHBoxLayout()
        scan_type_label = QLabel("Scan Type:")
        scan_type_label.setStyleSheet("color: #E5E7EB; font-weight: 600;")
        
        self.scan_type_combo = QComboBox()
        self.scan_type_combo.addItems([
            SCAN_TYPES["quick"]["name"],
            SCAN_TYPES["full"]["name"],
            SCAN_TYPES["fast"]["name"],
            SCAN_TYPES["udp"]["name"]
        ])
        self.scan_type_combo.setStyleSheet("""
            QComboBox {
                background-color: #020617;
                color: #E5E7EB;
                border: 1px solid #1E293B;
                padding: 8px;
                border-radius: 6px;
                font-size: 13px;
            }
        """)
        self.scan_type_combo.setMaximumWidth(350)
        
        scan_type_layout.addWidget(scan_type_label)
        scan_type_layout.addWidget(self.scan_type_combo)
        scan_type_layout.addStretch()
        layout.addLayout(scan_type_layout)

        # Control buttons
        controls_buttons = QHBoxLayout()
        controls_buttons.setSpacing(10)

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
        self.stop_button.setToolTip("Stop Nmap execution")
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

        controls_buttons.addWidget(self.run_button)
        controls_buttons.addWidget(self.stop_button)
        controls_buttons.addStretch()
        layout.addLayout(controls_buttons)

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
        self.output.setPlaceholderText("Nmap results will appear here...")
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

        # Get selected scan type
        scan_type_idx = self.scan_type_combo.currentIndex()
        scan_type_map = ["quick", "full", "fast", "udp"]
        scan_type = scan_type_map[scan_type_idx]

        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.targets_queue = list(targets)
        self.group_name = group_name
        self.scan_type = scan_type
        self._process_next_target()

    def _process_next_target(self):
        """Process targets one by one"""
        if not self.targets_queue:
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self._notify("Nmap scan completed")
            return

        target = self.targets_queue.pop(0)
        self._info(f"Running Nmap ({self.scan_type}) for: {target}")
        self._section(f"NMAP: {target}")

        base_dir = create_target_dirs(target, group_name=self.group_name)
        logs_dir = os.path.join(base_dir, "Logs")
        os.makedirs(logs_dir, exist_ok=True)

        scan_config = SCAN_TYPES[self.scan_type]
        txt_file, xml_file = scan_config["files"]
        txt_path = os.path.join(logs_dir, txt_file)
        xml_path = os.path.join(logs_dir, xml_file)

        self.all_output = []
        self.last_base_dir = base_dir

        cmd = ["nmap", target] + scan_config["args"] + ["-oN", txt_path, "-oX", xml_path]

        # Create and start worker thread
        self.worker = ProcessWorker(cmd)
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
        self.output.appendPlainText("\n")

        # Process next target
        if self.targets_queue:
            self._process_next_target()
        else:
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            if hasattr(self, 'last_base_dir'):
                self._notify(f"Nmap results saved under:\n{os.path.dirname(self.last_base_dir)}")

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
        self._notify("Nmap scan stopped")

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
