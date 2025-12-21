import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # ===== Global Font Scaling (+2) =====
    # Applied once for entire application
    app.setStyleSheet("""
        QWidget {
            font-size: 15px;
        }
        QLabel {
            font-size: 15px;
        }
        QLineEdit {
            font-size: 15px;
        }
        QPushButton {
            font-size: 14px;
        }
    """)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
