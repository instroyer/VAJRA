import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QtMsgType, qInstallMessageHandler
from ui.main_window import MainWindow


def qt_message_handler(mode, context, message):
    """Custom Qt message handler to filter out unwanted warnings."""
    # Suppress "Unknown property transform" warnings from Qt's HTML/CSS renderer
    if "Unknown property" in message and "transform" in message:
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
    # Install custom message handler to suppress unwanted Qt warnings
    qInstallMessageHandler(qt_message_handler)
    
    # Suppress other Qt warnings
    os.environ["QT_LOGGING_RULES"] = "qt.xkb.compose=false;qt.qpa.*=false"
    
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
