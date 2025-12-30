# =============================================================================
# ui/widgets.py
#
# Centralized reusable widget classes for the application.
# =============================================================================

from PySide6.QtWidgets import (
    QWidget, QGridLayout, QPushButton, QPlainTextEdit,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSplitter, QApplication
)
from PySide6.QtCore import Qt

from ui.styles import (
    OUTPUT_TEXT_EDIT_STYLE, TOOL_VIEW_STYLE, TOOL_HEADER_STYLE,
    LABEL_STYLE, TARGET_INPUT_STYLE, RUN_BUTTON_STYLE, STOP_BUTTON_STYLE
)


class OutputView(QWidget):
    """A widget for displaying tool output with a copy button."""

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Tool results will appear here...")
        self.output_text.setStyleSheet(OUTPUT_TEXT_EDIT_STYLE)

        self.copy_button = QPushButton("📋")
        self.copy_button.setStyleSheet('''
            QPushButton {
                font-size: 24px;
                background-color: transparent;
                border: none;
                padding: 10px;
            }
        ''')
        self.copy_button.setCursor(Qt.PointingHandCursor)
        self.copy_button.setToolTip("Copy output to clipboard")
        self.copy_button.clicked.connect(self.copy_to_clipboard)

        layout.addWidget(self.output_text, 0, 0)
        layout.addWidget(self.copy_button, 0, 0, Qt.AlignTop | Qt.AlignRight)

    def appendPlainText(self, text):
        self.output_text.appendPlainText(text)

    def appendHtml(self, html):
        self.output_text.appendHtml(html)

    def toPlainText(self):
        return self.output_text.toPlainText()

    def clear(self):
        self.output_text.clear()

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.toPlainText())
        if self.parent() and hasattr(self.parent(), '_notify'):
            self.parent()._notify("Results copied to clipboard.")


class BaseToolView(QWidget):
    """A base view for tools, providing a consistent UI structure."""

    def __init__(self, name, category, main_window=None):
        super().__init__()
        self.name = name
        self.category = category
        self.main_window = main_window
        self.worker = None
        self._build_base_ui()

    def _build_base_ui(self):
        from core.tgtinput import TargetInput
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

        # --- Control Panel ---
        control_panel = QWidget()
        control_panel.setStyleSheet(TOOL_VIEW_STYLE)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        header = QLabel(f"{self.category.name.replace('_', ' ')}  ›  {self.name}")
        header.setStyleSheet(TOOL_HEADER_STYLE)

        target_label = QLabel("Target")
        target_label.setStyleSheet(LABEL_STYLE)

        # --- Target Input and Action Buttons ---
        target_line_layout = QHBoxLayout()
        self.target_input = TargetInput()
        self.target_input.setStyleSheet(TARGET_INPUT_STYLE)
        self.target_input.input_box.textChanged.connect(self.update_command)

        self.run_button = QPushButton("RUN")
        self.run_button.setStyleSheet(RUN_BUTTON_STYLE)
        self.run_button.clicked.connect(self.run_scan)
        self.stop_button = QPushButton("■")
        self.stop_button.setStyleSheet(STOP_BUTTON_STYLE)
        self.stop_button.clicked.connect(self.stop_scan)
        self.stop_button.setEnabled(False)

        target_line_layout.addWidget(self.target_input)
        target_line_layout.addWidget(self.run_button)
        target_line_layout.addWidget(self.stop_button)

        # --- Command Display ---
        command_label = QLabel("Command")
        command_label.setStyleSheet(LABEL_STYLE)
        self.command_input = QLineEdit()
        self.command_input.setStyleSheet(TARGET_INPUT_STYLE)

        control_layout.addWidget(header)
        control_layout.addWidget(target_label)
        control_layout.addLayout(target_line_layout)
        control_layout.addWidget(command_label)
        control_layout.addWidget(self.command_input)
        control_layout.addStretch()

        # --- Output Area ---
        self.output = OutputView()

        splitter.addWidget(control_panel)
        splitter.addWidget(self.output)
        splitter.setSizes([250, 500])

        self.update_command()

    def update_command(self):
        raise NotImplementedError("Subclasses must implement update_command.")

    def run_scan(self):
        raise NotImplementedError("Subclasses must implement run_scan.")

    def stop_scan(self):
        if self.worker:
            self.worker.stop()

    def _on_scan_completed(self):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.worker = None
        if self.main_window:
            self.main_window.active_process = None

    def _notify(self, message):
        if self.main_window:
            self.main_window.notification_manager.notify(message)

    def _info(self, message):
        self.output.appendHtml(f'<span style="color:#60A5FA;">[INFO]</span> {message}')

    def _error(self, message):
        self.output.appendHtml(f'<span style="color:#F87171;">[ERROR]</span> {message}')

    def _section(self, title):
        self.output.appendHtml(f'<br><span style="color:#FACC15;font-weight:700;">===== {title} =====</span><br>')
