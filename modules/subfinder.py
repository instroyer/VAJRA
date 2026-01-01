import os
from PySide6.QtWidgets import (
    QLabel, QSpinBox, QHBoxLayout, QCheckBox, QVBoxLayout, QGroupBox, 
    QLineEdit, QPushButton, QFileDialog
)
from core.tgtinput import parse_targets
from core.fileops import create_target_dirs, get_group_name_from_file
from modules.bases import ToolBase, ToolCategory
from ui.styles import (
    BaseToolView, CopyButton, COLOR_TEXT_PRIMARY, COLOR_BORDER, 
    COLOR_BACKGROUND_INPUT, COLOR_BORDER_INPUT_FOCUSED
)
from ui.worker import ProcessWorker
from PySide6.QtCore import Qt


class SubfinderView(BaseToolView):
    def _build_base_ui(self):
        super()._build_base_ui()
        self.copy_button = CopyButton(self.output.output_text, self.main_window)
        self.output.layout().addWidget(self.copy_button, 0, 0, Qt.AlignTop | Qt.AlignRight)

    def __init__(self, name, category, main_window=None):
        super().__init__(name, category, main_window)
        # Initialize attributes
        self.threads_spin = None
        self.recursive_check = None
        self.all_sources_check = None
        self.config_input = None
        
        # Build UI and initialize command
        self._build_custom_ui()
        self.update_command()
        
        self.targets_queue = []
        self.group_name = None
        self.log_file = None

    def _build_custom_ui(self):
        """Build advanced options for Subfinder."""
        # Use centralized options container provided by BaseToolView
        
        # ==================== CONFIGURATION GROUP ====================
        config_group = QGroupBox("⚙️ Advanced Configuration")
        config_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(10)

        # Row 1: Threads & Config
        row1 = QHBoxLayout()
        
        # Threads
        threads_container = QHBoxLayout()
        threads_label = QLabel("Threads:")
        threads_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 200)
        self.threads_spin.setValue(10)
        self.threads_spin.setToolTip("Number of concurrent threads")
        self.threads_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        self.threads_spin.valueChanged.connect(self.update_command)
        
        threads_container.addWidget(threads_label)
        threads_container.addWidget(self.threads_spin)
        row1.addLayout(threads_container)
        
        row1.addSpacing(20)
        
        # Config File
        config_container = QHBoxLayout()
        config_label = QLabel("Config:")
        config_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        
        self.config_input = QLineEdit()
        self.config_input.setPlaceholderText("Path to config file...")
        self.config_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        self.config_input.textChanged.connect(self.update_command)
        
        config_browse = QPushButton("📁")
        config_browse.setFixedSize(30, 30)
        config_browse.clicked.connect(self._browse_config)
        config_browse.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_BACKGROUND_INPUT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                color: {COLOR_TEXT_PRIMARY};
            }}
            QPushButton:hover {{ background-color: #4A4A4A; }}
        """)
        
        config_container.addWidget(config_label)
        config_container.addWidget(self.config_input)
        config_container.addWidget(config_browse)
        row1.addLayout(config_container)
        
        config_layout.addLayout(row1)
        
        # Row 2: Checkboxes
        row2 = QHBoxLayout()
        
        self.recursive_check = QCheckBox("Recursive (-recursive)")
        self.recursive_check.setToolTip("Use only sources that can handle subdomains recursively")
        self.recursive_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.recursive_check.stateChanged.connect(self.update_command)
        
        self.all_sources_check = QCheckBox("All Sources (-all)")
        self.all_sources_check.setToolTip("Use all available sources for enumeration")
        self.all_sources_check.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        self.all_sources_check.stateChanged.connect(self.update_command)
        
        row2.addWidget(self.recursive_check)
        row2.addSpacing(20)
        row2.addWidget(self.all_sources_check)
        row2.addStretch()
        
        config_layout.addLayout(row2)
        
        # Add to centralized container
        self.options_container.addWidget(config_group)

    def _browse_config(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Config File", "", "YAML Files (*.yaml *.yml);;All Files (*)")
        if file_path:
            self.config_input.setText(file_path)

    def update_command(self):
        # Handle case when UI elements haven't been created yet
        if not hasattr(self, 'threads_spin') or not self.threads_spin:
            return

        target = self.target_input.get_target().strip()
        if not target:
            target = "<target>"
            
        cmd_parts = ["subfinder", "-d", target]
        
        # Add options
        if self.threads_spin and self.threads_spin.value() > 10:
             cmd_parts.extend(["-t", str(self.threads_spin.value())])
             
        if self.recursive_check and self.recursive_check.isChecked():
            cmd_parts.append("-recursive")
            
        if self.all_sources_check and self.all_sources_check.isChecked():
            cmd_parts.append("-all")
            
        if self.config_input and self.config_input.text().strip():
            cmd_parts.extend(["-config", self.config_input.text().strip()])
            
        self.command_input.setText(" ".join(cmd_parts))

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
            self._notify("Subfinder scan finished.")
            return

        target = self.targets_queue.pop(0)
        self._info(f"Running command: {self.command_input.text()}")
        self._section(f"SUBFINDER: {target}")

        base_dir = create_target_dirs(target, self.group_name)
        self.log_file = os.path.join(base_dir, "Subdomains", "subfinder.txt")
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
            self._notify("Subfinder scan finished.")

    def _on_process_error(self, error):
        self._error(f"Process error: {error}")
        self._on_scan_completed()


class SubfinderTool(ToolBase):
    @property
    def name(self) -> str:
        return "Subfinder"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SUBDOMAIN_ENUMERATION

    def get_widget(self, main_window):
        return SubfinderView(self.name, self.category, main_window=main_window)
