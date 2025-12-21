from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QFileDialog
)
from PySide6.QtCore import Qt


class TargetInput(QWidget):
    """
    Common target input widget used across all modules.
    Provides:
    - Text input
    - File picker button
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
