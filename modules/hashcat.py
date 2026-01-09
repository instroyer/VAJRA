# =============================================================================
# modules/hashcat.py
#
# Hashcat Tool - Advanced Password Recovery
# =============================================================================

import os
import shlex
import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog
)
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from ui.worker import ToolExecutionMixin
from ui.styles import (
    # Widgets
    RunButton, StopButton, BrowseButton,
    StyledLineEdit, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView,
    ToolSplitter, StyledToolView
)


from modules.hashcat_data import HASH_MODES

class HashcatTool(ToolBase):
    name = "Hashcat"
    category = ToolCategory.CRACKER

    @property
    def description(self) -> str:
        return "World's fastest and most advanced password recovery utility."
    
    @property
    def icon(self) -> str:
        return "🐱"

    def get_widget(self, main_window):
        return HashcatToolView(main_window=main_window)


class HashcatToolView(StyledToolView, ToolExecutionMixin):
    """Hashcat password cracker interface."""
    
    tool_name = "Hashcat"
    tool_category = "CRACKER"

    # HASH_MODES loaded from external file for manageability
    HASH_MODES = HASH_MODES
    
    ATTACK_MODES = {
        "0: Straight (Wordlist)": "0",
        "1: Combination": "1",
        "3: Brute-Force (Mask)": "3",
        "6: Hybrid Wordlist+Mask": "6",
        "7: Hybrid Mask+Wordlist": "7"
    }

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._build_ui()
        self.update_command()

    def _build_ui(self):
        """Build UI."""
        # setStyleSheet handled by StyledToolView
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = ToolSplitter()
        
        # ==================== CONTROL PANEL ====================
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)
        
        # Header
        header = HeaderLabel(self.tool_category, self.tool_name)
        control_layout.addWidget(header)
        
        # Hash Input
        input_group = StyledGroupBox("📂 Hash Input")
        input_layout = QVBoxLayout(input_group)
        
        input_row = QHBoxLayout()
        self.hash_input = StyledLineEdit()
        self.hash_input.setPlaceholderText("Select hash file...")
        self.hash_input.textChanged.connect(self.update_command)
        
        browse_btn = BrowseButton()
        browse_btn.clicked.connect(self._browse_hash)
        
        input_row.addWidget(StyledLabel("Hash File:"))
        input_row.addWidget(self.hash_input)
        input_row.addWidget(browse_btn)
        input_layout.addLayout(input_row)
        
        control_layout.addWidget(input_group)
        
        # Configuration
        config_group = StyledGroupBox("⚙️ Configuration")
        config_layout = QGridLayout(config_group)
        config_layout.setSpacing(10)
        
        # Hash Type
        self.hash_type_combo = StyledComboBox()
        self.hash_type_combo.addItems(sorted(self.HASH_MODES.keys()))
        self.hash_type_combo.setCurrentText("MD5")
        self.hash_type_combo.currentTextChanged.connect(self.update_command)
        
        # Attack Mode
        self.attack_mode_combo = StyledComboBox()
        self.attack_mode_combo.addItems(sorted(self.ATTACK_MODES.keys()))
        self.attack_mode_combo.setCurrentText("0: Straight (Wordlist)")
        self.attack_mode_combo.currentTextChanged.connect(self._on_mode_changed)
        
        config_layout.addWidget(StyledLabel("Hash Type (-m):"), 0, 0)
        config_layout.addWidget(self.hash_type_combo, 0, 1)
        config_layout.addWidget(StyledLabel("Attack Mode (-a):"), 1, 0)
        config_layout.addWidget(self.attack_mode_combo, 1, 1)
        
        # Wordlist
        self.wl_row = QWidget()
        wl_layout = QHBoxLayout(self.wl_row)
        wl_layout.setContentsMargins(0, 0, 0, 0)
        
        self.wordlist_input = StyledLineEdit()
        self.wordlist_input.setPlaceholderText("Select wordlist...")
        self.wordlist_input.textChanged.connect(self.update_command)
        
        self.wl_browse = BrowseButton()
        self.wl_browse.clicked.connect(self._browse_wordlist)
        
        wl_layout.addWidget(StyledLabel("Wordlist:"))
        wl_layout.addWidget(self.wordlist_input)
        wl_layout.addWidget(self.wl_browse)
        
        config_layout.addWidget(self.wl_row, 2, 0, 1, 2)
        
        control_layout.addWidget(config_group)
        
        # Advanced
        adv_group = StyledGroupBox("🚀 Advanced")
        adv_layout = QGridLayout(adv_group)
        
        self.workload_combo = StyledComboBox()
        self.workload_combo.addItems(["1 (Low)", "2 (Default)", "3 (High)", "4 (Nightmare)"])
        self.workload_combo.setCurrentIndex(1)
        self.workload_combo.currentTextChanged.connect(self.update_command)
        
        self.device_combo = StyledComboBox()
        self.device_combo.addItems(["Auto", "CPU", "GPU"])
        self.device_combo.currentTextChanged.connect(self.update_command)
        
        self.force_check = StyledCheckBox("Force (--force)")
        self.force_check.stateChanged.connect(self.update_command)
        
        self.show_check = StyledCheckBox("Show Cracked (--show)")
        self.show_check.stateChanged.connect(self.update_command)
        
        adv_layout.addWidget(StyledLabel("Workload (-w):"), 0, 0)
        adv_layout.addWidget(self.workload_combo, 0, 1)
        adv_layout.addWidget(StyledLabel("Device (-D):"), 1, 0)
        adv_layout.addWidget(self.device_combo, 1, 1)
        adv_layout.addWidget(self.force_check, 2, 0)
        adv_layout.addWidget(self.show_check, 2, 1)
        
        control_layout.addWidget(adv_group)

        # Command Preview
        self.command_input = StyledLineEdit()
        self.command_input.setReadOnly(True)
        self.command_input.setPlaceholderText("Command preview...")
        control_layout.addWidget(self.command_input)

        # Buttons
        btn_layout = QHBoxLayout()
        self.run_button = RunButton("RUN HASHCAT")
        self.run_button.clicked.connect(self.run_scan)
        self.stop_button = StopButton()
        self.stop_button.clicked.connect(self.stop_scan)
        
        btn_layout.addWidget(self.run_button)
        btn_layout.addWidget(self.stop_button)
        control_layout.addLayout(btn_layout)
        
        control_layout.addStretch()
        splitter.addWidget(control_panel)

        # Output
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("Hashcat results will appear here...")
        
        splitter.addWidget(self.output)
        splitter.setSizes([450, 450])
        
        main_layout.addWidget(splitter)
        
        # Init
        self._on_mode_changed(self.attack_mode_combo.currentText())

    def _browse_hash(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Hash File")
        if f: self.hash_input.setText(f)

    def _browse_wordlist(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Wordlist")
        if f: self.wordlist_input.setText(f)

    def _on_mode_changed(self, mode):
        # Show wordlist only for modes 0, 6, 7 (roughly)
        mode_id = self.ATTACK_MODES.get(mode, "0")
        is_wl = mode_id in ["0", "6", "7"]
        self.wl_row.setVisible(is_wl)
        self.update_command()

    # -------------------------------------------------------------------------
    # Command Builder
    # -------------------------------------------------------------------------

    def build_command(self, preview: bool = False) -> str:
        cmd = ["hashcat"]
        
        # Hash Mode
        m_txt = self.hash_type_combo.currentText()
        m_id = self.HASH_MODES.get(m_txt, "0")
        cmd.extend(["-m", m_id])
        
        # Attack Mode
        a_txt = self.attack_mode_combo.currentText()
        a_id = self.ATTACK_MODES.get(a_txt, "0")
        cmd.extend(["-a", a_id])
        
        # Workload
        w_txt = self.workload_combo.currentText()
        w_id = w_txt.split(" ")[0]
        cmd.extend(["-w", w_id])
        
        # Device
        d_txt = self.device_combo.currentText()
        if d_txt == "CPU":
            cmd.extend(["-D", "2"])
        elif d_txt == "GPU":
            cmd.extend(["-D", "1"])
            
        # Force
        if self.force_check.isChecked():
            cmd.append("--force")
            
        # Show
        if self.show_check and self.show_check.isChecked():
            cmd.append("--show")

        # Files
        # Hash File
        hash_file = self.hash_input.text().strip()
        if not hash_file:
            if preview:
                hash_file = "<hash_file>"
            else:
                raise ValueError("Hash file required")
        
        cmd.append(hash_file)
        
        # Wordlist (if applicable)
        if a_id in ["0", "6", "7"]:
            wl = self.wordlist_input.text().strip()
            if wl:
                cmd.append(wl)
            elif not preview:
                 raise ValueError("Wordlist required")
            else:
                 cmd.append("<wordlist>")
                 
        return " ".join(shlex.quote(x) for x in cmd)

    def update_command(self):
        try:
            cmd_str = self.build_command(preview=True)
            self.command_input.setText(cmd_str)
        except Exception:
            self.command_input.setText("")

    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------

    def run_scan(self):
        try:
            cmd_str = self.build_command(preview=False)
            
            self._info("Starting Hashcat...")
            self._section("HASHCAT")
            self._section("Command")
            self._raw(html.escape(cmd_str))
            
            # Disable buffering for real-time status updates
            self.start_execution(cmd_str, buffer_output=False)
            
        except Exception as e:
            self._error(str(e))

    def on_execution_finished(self):
        super().on_execution_finished()
        self._section("Completed")

    def on_new_output(self, line):
        clean = line.rstrip() # rstrip to preserve indentation
        
        clean = self.strip_ansi(clean) # ANSI stripped
        safe = html.escape(clean)
        
        # Terminal look
        base = "white-space: pre-wrap; font-family: monospace; display: block;"
        
        if not safe:
            self._raw("<br>")
            return

        # Hashcat output parsing for status lines
        if clean.startswith("Session.") or clean.startswith("Status.") or clean.startswith("Speed."):
             self._raw(f'<span style="{base} color:#9CA3AF;">{safe}</span>')
        elif "Cracked" in clean or "Recovered" in clean:
             self._raw(f'<span style="{base} color:#10B981; font-weight:bold;">{safe}</span>')
        else:
             self._raw(f'<span style="{base}">{safe}</span>')
