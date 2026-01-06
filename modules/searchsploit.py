# =============================================================================
# modules/searchsploit.py
#
# SearchSploit - Exploit Database Search Tool
# =============================================================================

import os
import re
import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
)
from PySide6.QtCore import Qt, QThread, Signal

from modules.bases import ToolBase, ToolCategory
from core.fileops import create_target_dirs
from ui.styles import (
    RunButton, StopButton, CopyButton,
    StyledLineEdit, StyledCheckBox,
    StyledLabel, HeaderLabel, CommandDisplay, OutputView,
    StyledGroupBox, ToolSplitter,
    SafeStop, OutputHelper,
    TOOL_VIEW_STYLE, COLOR_BACKGROUND_SECONDARY
)


class SearchSploitTool(ToolBase):
    """SearchSploit exploit search tool plugin."""

    @property
    def name(self) -> str:
        return "SearchSploit"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.INFO_GATHERING

    def get_widget(self, main_window):
        return SearchSploitToolView(main_window=main_window)


class SearchSploitWorker(QThread):
    """Background worker for SearchSploit with grep filter support."""
    output_ready = Signal(str)
    finished_signal = Signal()
    error = Signal(str)
    
    def __init__(self, command, grep_filter=None):
        super().__init__()
        self.command = command
        self.grep_filter = grep_filter.strip().lower() if grep_filter else None
        self.process = None
        self.is_running = True
    
    def run(self):
        import subprocess
        try:
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in iter(self.process.stdout.readline, ''):
                if not self.is_running:
                    break
                if line:
                    if self.grep_filter:
                        if self.grep_filter in line.lower():
                            self.output_ready.emit(line.rstrip())
                    else:
                        self.output_ready.emit(line.rstrip())
            
            self.process.wait()
        except FileNotFoundError:
            self.error.emit("searchsploit not found. Install exploit-db or use Kali Linux.")
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished_signal.emit()
    
    def stop(self):
        self.is_running = False
        if self.process:
            self.process.terminate()


class SearchSploitToolView(QWidget, SafeStop, OutputHelper):
    """SearchSploit exploit search interface."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_safe_stop()
        
        # State
        self.base_dir = None
        
        # Build UI
        self._build_ui()
        self.update_command()

    def _build_ui(self):
        """Build complete UI."""
        self.setStyleSheet(TOOL_VIEW_STYLE)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = ToolSplitter()

        # ==================== CONTROL PANEL ====================
        control_panel = QWidget()
        control_panel.setStyleSheet(f"background-color: {COLOR_BACKGROUND_SECONDARY};")
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        # Header
        header = HeaderLabel("INFO_GATHERING", "SearchSploit")
        control_layout.addWidget(header)

        # Search Term
        search_label = StyledLabel("Search Term")
        control_layout.addWidget(search_label)

        search_row = QHBoxLayout()
        self.search_input = StyledLineEdit("e.g., apache 2.4, wordpress, ssh")
        self.search_input.textChanged.connect(self.update_command)
        self.search_input.returnPressed.connect(self.run_scan)
        
        self.run_button = RunButton()
        self.run_button.clicked.connect(self.run_scan)
        self.stop_button = StopButton()
        self.stop_button.clicked.connect(self.stop_scan)
        
        search_row.addWidget(self.search_input)
        search_row.addWidget(self.run_button)
        search_row.addWidget(self.stop_button)
        control_layout.addLayout(search_row)

        # Grep Filter
        filter_row = QHBoxLayout()
        filter_label = StyledLabel("Filter (grep):")
        filter_label.setFixedWidth(90)
        
        self.filter_input = StyledLineEdit("Filter results (e.g., remote, RCE, privilege)")
        self.filter_input.textChanged.connect(self.update_command)
        
        filter_row.addWidget(filter_label)
        filter_row.addWidget(self.filter_input)
        control_layout.addLayout(filter_row)

        # Command Display
        self.command_display = CommandDisplay()
        self.command_input = self.command_display.input
        control_layout.addWidget(self.command_display)

        # ==================== OPTIONS GROUP ====================
        options_group = StyledGroupBox("⚙️ Search Options")
        options_layout = QGridLayout(options_group)
        options_layout.setContentsMargins(10, 15, 10, 10)
        options_layout.setSpacing(10)

        # Row 1
        self.case_check = StyledCheckBox("Case Sensitive (-c)")
        self.case_check.stateChanged.connect(self.update_command)
        
        self.exact_check = StyledCheckBox("Exact Match (-e)")
        self.exact_check.stateChanged.connect(self.update_command)

        self.strict_check = StyledCheckBox("Strict Match (-s)")
        self.strict_check.stateChanged.connect(self.update_command)

        self.title_check = StyledCheckBox("Title Only (-t)")
        self.title_check.stateChanged.connect(self.update_command)

        # Row 2
        self.json_check = StyledCheckBox("JSON Output (-j)")
        self.json_check.stateChanged.connect(self.update_command)

        self.overflow_check = StyledCheckBox("Allow Overflow (-o)")
        self.overflow_check.stateChanged.connect(self.update_command)

        self.path_check = StyledCheckBox("Show Full Path (-p)")
        self.path_check.stateChanged.connect(self.update_command)

        self.www_check = StyledCheckBox("Show URLs (-w)")
        self.www_check.stateChanged.connect(self.update_command)

        # Layout
        options_layout.addWidget(self.case_check, 0, 0)
        options_layout.addWidget(self.exact_check, 0, 1)
        options_layout.addWidget(self.strict_check, 0, 2)
        options_layout.addWidget(self.title_check, 0, 3)
        options_layout.addWidget(self.json_check, 1, 0)
        options_layout.addWidget(self.overflow_check, 1, 1)
        options_layout.addWidget(self.path_check, 1, 2)
        options_layout.addWidget(self.www_check, 1, 3)

        control_layout.addWidget(options_group)
        control_layout.addStretch()

        splitter.addWidget(control_panel)

        # ==================== OUTPUT AREA ====================
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("SearchSploit results will appear here...")

        self.copy_button = CopyButton(self.output.output_text, self.main_window)
        self.copy_button.setParent(self.output.output_text)
        self.copy_button.raise_()
        self.output.output_text.installEventFilter(self)

        splitter.addWidget(self.output)
        splitter.setSizes([350, 400])

        main_layout.addWidget(splitter)

    def eventFilter(self, obj, event):
        """Position copy button on resize."""
        from PySide6.QtCore import QEvent
        if obj == self.output.output_text and event.type() == QEvent.Resize:
            self.copy_button.move(
                self.output.output_text.width() - self.copy_button.sizeHint().width() - 10,
                10
            )
        return super().eventFilter(obj, event)

    def update_command(self):
        search_term = self.search_input.text().strip()
        if not search_term:
            search_term = "<search_term>"

        cmd_parts = ["searchsploit"]

        if self.case_check.isChecked():
            cmd_parts.append("-c")
        if self.exact_check.isChecked():
            cmd_parts.append("-e")
        if self.strict_check.isChecked():
            cmd_parts.append("-s")
        if self.title_check.isChecked():
            cmd_parts.append("-t")
        if self.json_check.isChecked():
            cmd_parts.append("-j")
        if self.overflow_check.isChecked():
            cmd_parts.append("-o")
        if self.path_check.isChecked():
            cmd_parts.append("-p")
        if self.www_check.isChecked():
            cmd_parts.append("-w")

        cmd_parts.append(search_term)

        grep_filter = self.filter_input.text().strip()
        if grep_filter:
            cmd_parts.extend(["|", "grep", "-i", f'"{grep_filter}"'])

        self.command_input.setText(" ".join(cmd_parts))

    def run_scan(self):
        search_term = self.search_input.text().strip()
        
        if not search_term:
            self._notify("Please enter a search term")
            return

        self.output.clear()
        self._info(f"Searching Exploit-DB for: {search_term}")
        
        grep_filter = self.filter_input.text().strip()
        if grep_filter:
            self._info(f"Filtering results for: {grep_filter}")
        
        self._section("SEARCHSPLOIT RESULTS")

        command = ["searchsploit"]
        
        if self.case_check.isChecked():
            command.append("-c")
        if self.exact_check.isChecked():
            command.append("-e")
        if self.strict_check.isChecked():
            command.append("-s")
        if self.title_check.isChecked():
            command.append("-t")
        if self.json_check.isChecked():
            command.append("-j")
        if self.overflow_check.isChecked():
            command.append("-o")
        if self.path_check.isChecked():
            command.append("-p")
        if self.www_check.isChecked():
            command.append("-w")
        
        command.append(search_term)

        self.worker = SearchSploitWorker(command, grep_filter)
        self.worker.output_ready.connect(self._on_output)
        self.worker.finished_signal.connect(self._on_scan_completed)
        self.worker.error.connect(lambda err: self._error(f"Error: {err}"))

        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        if self.main_window:
            self.main_window.active_process = self.worker

        self.worker.start()

    def _on_scan_completed(self):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        self.worker = None
        if self.main_window:
            self.main_window.active_process = None
        self._info("Search completed")
        self._notify("SearchSploit search completed.")

    def _on_output(self, line):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        line = ansi_escape.sub('', line)

        if not line.strip():
            return

        line_lower = line.lower()
        escaped_line = html.escape(line)
        
        grep_filter = self.filter_input.text().strip()
        if grep_filter:
            pattern = re.compile(re.escape(grep_filter), re.IGNORECASE)
            escaped_line = pattern.sub(
                f'<span style="background-color:#FACC15;color:#000;font-weight:bold;">{grep_filter}</span>',
                escaped_line
            )

        if line.startswith("-") or line.startswith("=") or "----" in line:
            self.output.append(f'<span style="color:#6B7280;">{escaped_line}</span>')
        elif "exploit title" in line_lower or "path" in line_lower and "|" in line:
            self.output.append(f'<span style="color:#FACC15;font-weight:bold;">{escaped_line}</span>')
        elif "remote" in line_lower:
            self.output.append(f'<span style="color:#EF4444;font-weight:bold;">{escaped_line}</span>')
        elif "privilege" in line_lower or "escalation" in line_lower:
            self.output.append(f'<span style="color:#EF4444;font-weight:bold;">{escaped_line}</span>')
        elif "local" in line_lower:
            self.output.append(f'<span style="color:#F97316;">{escaped_line}</span>')
        elif "dos" in line_lower or "denial" in line_lower:
            self.output.append(f'<span style="color:#EAB308;">{escaped_line}</span>')
        elif "webapps" in line_lower or "php" in line_lower:
            self.output.append(f'<span style="color:#22D3EE;">{escaped_line}</span>')
        elif "shellcode" in line_lower:
            self.output.append(f'<span style="color:#22C55E;">{escaped_line}</span>')
        elif ".rb" in line_lower or "metasploit" in line_lower:
            self.output.append(f'<span style="color:#A855F7;">{escaped_line}</span>')
        elif ".py" in line_lower or ".pl" in line_lower:
            self.output.append(f'<span style="color:#3B82F6;">{escaped_line}</span>')
        else:
            self.output.append(escaped_line)
