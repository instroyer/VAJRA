"""
VAJRA Target Input Widget & Parser
Target input component and parsing utilities
"""

import os
import re
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QFileDialog
)
from PySide6.QtCore import Qt


def normalize_target(target: str) -> str:
    """
    Normalize target by removing protocol only.
    Path is preserved.
    """
    target = target.strip()
    # Remove protocol (keep path)
    target = re.sub(r"^https?://", "", target, flags=re.IGNORECASE)
    return target


def parse_targets(input_value: str):
    """
    Parse single target or file containing targets.

    Returns:
        targets (list[str])
        source_type (str): "single" | "file"
    """
    if not input_value:
        raise ValueError("Empty target input")

    targets = []

    if os.path.isfile(input_value):
        with open(input_value, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                normalized = normalize_target(line)
                if normalized:
                    targets.append(normalized)
        return targets, "file"

    # Single target
    return [normalize_target(input_value)], "single"


def parse_port_range(port_str: str) -> list[int]:
    """
    Parse a port range string (e.g. "80,443,1000-1010") into a list of integers.
    """
    ports = set()
    parts = port_str.split(',')
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                ports.update(range(start, end + 1))
            except ValueError:
                continue
        else:
            try:
                ports.add(int(part))
            except ValueError:
                continue
    return sorted(list(ports))


class TargetInput(QWidget):
    """
    Common target input widget used across all modules.
    Provides:
    - Text input
    - File picker button
    - Target parsing and normalization
    """

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Target text box
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText(
            "Enter target (domain / IP / CIDR) or select file"
        )
        self.input_box.setMinimumHeight(36)

        # File picker button
        self.file_button = QPushButton("📁")
        self.file_button.setFixedSize(36, 36)
        self.file_button.setCursor(Qt.PointingHandCursor)

        self.file_button.clicked.connect(self.open_file_dialog)

        layout.addWidget(self.input_box)
        layout.addWidget(self.file_button)

        self.setStyleSheet(
            """
            QLineEdit {
                padding: 6px;
                font-size: 14px;
            }
            QPushButton {
                font-size: 16px;
            }
            """
        )

    def open_file_dialog(self):
        """
        Opens file dialog and sets selected file path
        into the target input box.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Target File",
            "",
            "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            self.input_box.setText(file_path)

    def get_target(self):
        """
        Returns the current value of the target input.
        """
        return self.input_box.text().strip()
