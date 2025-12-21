
import os
from ui.main_window import BaseToolView
from core.tgtinput import parse_targets
from ui.worker import ProcessWorker
from core.fileops import create_target_dirs, get_group_name_from_file
from modules.bases import ToolBase, ToolCategory

class ScreenshotView(BaseToolView):
    def __init__(self, name, category, main_window=None):
        super().__init__(name, category, main_window)
        self.targets_queue = []
        self.group_name = None
        self.log_file = None
        self.all_output = []

    def update_command(self):
        target = self.target_input.get_target().strip()
        if not target:
            target = "<target>"
        
        # The actual output directory will be determined at scan time
        self.command_input.setText(f"screenshot -l {target} -o <output_dir>")

    def run_scan(self):
        raw_input = self.target_input.get_target()
        if not raw_input:
            self._notify("Please enter a target or select a file.")
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
        self.all_output = []
        self._process_next_target()

    def _process_next_target(self):
        if not self.targets_queue:
            self._on_scan_completed()
            self._notify("Screenshot scan finished.")
            return

        target = self.targets_queue.pop(0)
        self._info(f"Running Screenshot for: {target}")
        self._section(f"SCREENSHOT: {target}")

        base_dir = create_target_dirs(target, self.group_name)
        screenshots_dir = os.path.join(base_dir, "Screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        
        self.log_file = os.path.join(base_dir, "Logs", "screenshot.txt")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # Build command dynamically
        cmd = ["screenshot", "-l", target, "-o", screenshots_dir]

        self.worker = ProcessWorker(cmd)
        self.worker.output_ready.connect(self._on_output)
        self.worker.finished.connect(self._on_process_finished)
        self.worker.error.connect(self._on_process_error)
        self.worker.start()

        if self.main_window:
            self.main_window.active_process = self.worker

    def _on_output(self, line):
        self.all_output.append(line + "\n")
        self.output.appendPlainText(line)

    def _on_process_finished(self):
        if self.log_file:
            with open(self.log_file, "w") as f:
                f.writelines(self.all_output)
        
        self.output.appendPlainText("\n")
        
        if self.targets_queue:
            self._process_next_target()
        else:
            self._on_scan_completed()
            self._notify("Screenshot scan finished.")

    def _on_process_error(self, error):
        self._error(f"Process error: {error}")
        self._on_scan_completed()

class ScreenshotTool(ToolBase):
    @property
    def name(self) -> str:
        return "Screenshot"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WEB_SCREENSHOTS

    def get_widget(self, main_window):
        return ScreenshotView(self.name, self.category, main_window=main_window)
