import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QtMsgType, qInstallMessageHandler
from ui.main_window import MainWindow


def qt_message_handler(mode, context, message):
    """Custom Qt message handler."""
    # Suppress "Unknown property transform" warnings
    if "Unknown property" in message and "transform" in message:
        return
    
    # Suppress QBoxLayout warnings (internal Qt layout issues)
    if "QBoxLayout" in message or "out of range" in message:
        return
    
    # For other messages, use default behavior
    if mode == QtMsgType.QtDebugMsg:
        print(f"Qt Debug: {message}")
    elif mode == QtMsgType.QtInfoMsg:
        print(f"Qt Info: {message}")
    elif mode == QtMsgType.QtWarningMsg:
        print(f"Qt Warning: {message}")
    elif mode == QtMsgType.QtCriticalMsg:
        print(f"Qt Critical: {message}")
    elif mode == QtMsgType.QtFatalMsg:
        print(f"Qt Fatal: {message}")


def main():
    # Suppress unwanted Qt warnings
    qInstallMessageHandler(qt_message_handler)
    
    # Suppress other Qt warnings
    os.environ["QT_LOGGING_RULES"] = "qt.xkb.compose=false;qt.qpa.*=false"
    
    app = QApplication(sys.argv)

    # Global Font Consistency
    app.setStyleSheet("""
        QWidget {
            font-family: "Segoe UI", "Arial", sans-serif;
            font-size: 14px;
            font-weight: normal;
        }
        QLabel {
            font-family: "Segoe UI", "Arial", sans-serif;
            font-size: 14px;
            font-weight: normal;
        }
        QLineEdit {
            font-family: "Segoe UI", "Arial", sans-serif;
            font-size: 14px;
            font-weight: normal;
        }
        QPushButton {
            font-family: "Segoe UI", "Arial", sans-serif;
            font-size: 14px;
            font-weight: normal;
        }
        QComboBox {
            font-family: "Segoe UI", "Arial", sans-serif;
            font-size: 14px;
            font-weight: normal;
        }
        QTextEdit {
            font-family: "Consolas", "Monaco", "Courier New", monospace;
            font-size: 13px;
            font-weight: normal;
        }
        QPlainTextEdit {
            font-family: "Consolas", "Monaco", "Courier New", monospace;
            font-size: 13px;
            font-weight: normal;
        }
    """)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
