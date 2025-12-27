import os
from core.fileops import create_target_dirs, get_group_name_from_file
from core.tgtinput import parse_targets
from modules.bases import ToolBase, ToolCategory
from ui.main_window import BaseToolView
from ui.worker import ProcessWorker


class WhoisView(BaseToolView):
    def __init__(self, name, category, main_window=None):
        super().__init__(name, category, main_window)
        self.targets_queue = []
        self.group_name = None
        self.log_file = None

    def update_command(self):
        target = self.target_input.get_target().strip()
        if not target:
            target = "<target>"
        self.command_input.setText(f"whois {target}")

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
            self._notify("Whois scan finished.")
            return

        target = self.targets_queue.pop(0)
        self._info(f"Running Whois for: {target}")
        self._section(f"WHOIS: {target}")

        base_dir = create_target_dirs(target, self.group_name)
        self.log_file = os.path.join(base_dir, "Logs", "whois.txt")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        command = self.command_input.text().split()

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

        with open(self.log_file, "w") as f:
            f.write(self.output.toPlainText())

        if self.targets_queue:
            self._process_next_target()
        else:
            self._on_scan_completed()
            self._notify("Whois scan finished.")

    def _on_process_error(self, error):
        self._error(f"Process error: {error}")
        self._on_scan_completed()


class WhoisTool(ToolBase):
    @property
    def name(self) -> str:
        return "Whois"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.INFO_GATHERING

    def get_widget(self, main_window):
        return WhoisView(self.name, self.category, main_window=main_window)
