import os
from core.fileops import create_target_dirs, get_group_name_from_file
from core.tgtinput import parse_targets
from modules.bases import ToolBase, ToolCategory
from ui.main_window import BaseToolView
from ui.worker import ProcessWorker


class AmassView(BaseToolView):
    def __init__(self, name, category, main_window=None):
        super().__init__(name, category, main_window)
        self.targets_queue = []
        self.group_name = None
        self.log_file = None

    def update_command(self):
        target = self.target_input.get_target().strip()
        if not target:
            target = "<target>"
        self.command_input.setText(f"amass enum -d {target}")

    def run_scan(self):
        raw_input = self.target_input.get_target()
        if not raw_input:
            self._notify("Please enter a target domain.")
            return

        targets, source = parse_targets(raw_input)
        if not targets:
            self._notify("No valid targets found.")
            return

        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.output.clear()

        self.targets_queue = list(targets)
        self.group_name = get_group_name_from_file(raw_input) if source == "file" else None
        self._process_next_target()

    def _process_next_target(self):
        if not self.targets_queue:
            self._on_scan_completed()
            self._notify("Amass scan finished.")
            return

        target = self.targets_queue.pop(0)
        self._info(f"Running command: {self.command_input.text()}")
        self._section(f"AMASS: {target}")

        base_dir = create_target_dirs(target, self.group_name)
        self.log_file = os.path.join(base_dir, "Subdomains", "amass.txt")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

        command = self.command_input.text().split() + ["-o", self.log_file]

        self.worker = ProcessWorker(command)
        self.worker.output_ready.connect(self._on_output)
        self.worker.finished.connect(self._on_process_finished)
        self.worker.error.connect(self._on_process_error)
        self.worker.start()

        if self.main_window:
            self.main_window.active_process = self.worker

    def _on_output(self, line):
        self.output.appendPlainText(line)

    def _on_process_finished(self):
        self.output.appendPlainText("\n")

        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    self.output.appendPlainText(f.read())
            except IOError as e:
                self._error(f"Could not read log file: {e}")

        if self.targets_queue:
            self._process_next_target()
        else:
            self._on_scan_completed()
            self._notify("Amass scan finished.")

    def _on_process_error(self, error):
        self._error(f"Process error: {error}")
        self._on_scan_completed()


class AmassTool(ToolBase):
    @property
    def name(self) -> str:
        return "Amass"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SUBDOMAIN_ENUMERATION

    def get_widget(self, main_window):
        return AmassView(self.name, self.category, main_window=main_window)
