
import inspect
import importlib
import pkgutil
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QTabWidget, QTabBar, QPushButton, QStatusBar, QSplitter, 
    QLineEdit, QApplication, QGridLayout, QPlainTextEdit
)
from PySide6.QtCore import Qt

from ui.sidepanel import Sidepanel
from modules.bases import ToolBase
from ui.notification import NotificationManager
from ui.styles import (
    MAIN_WINDOW_STYLE, TAB_WIDGET_STYLE, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_BACKGROUND_SECONDARY, COLOR_BORDER,
    COLOR_BACKGROUND_PRIMARY, TOOL_HEADER_STYLE, LABEL_STYLE, 
    TARGET_INPUT_STYLE, RUN_BUTTON_STYLE, STOP_BUTTON_STYLE, 
    OUTPUT_TEXT_EDIT_STYLE, TOOL_VIEW_STYLE
)
from core.tgtinput import TargetInput

class WelcomeWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        title = QLabel("Welcome to VAJRA - Offensive Security Platform")
        title.setStyleSheet(f"font-size: 28px; font-weight: 300; color: {COLOR_TEXT_PRIMARY};")

        subtitle = QLabel("Select a tool from the sidepanel to begin.")
        subtitle.setStyleSheet(f"font-size: 16px; color: {COLOR_TEXT_SECONDARY};")
        
        layout.addWidget(title, alignment=Qt.AlignCenter)
        layout.addWidget(subtitle, alignment=Qt.AlignCenter)
        self.setStyleSheet("background-color: transparent;")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VAJRA - Offensive Security Platform")
        self.setMinimumSize(1200, 720)
        self.setStyleSheet(MAIN_WINDOW_STYLE)

        self.active_process = None
        self.open_tool_widgets = {}
        self.tools = self._discover_tools()
        self._build_ui()

    def _discover_tools(self):
        tools = {}
        module_path = "modules"
        try:
            package = importlib.import_module(module_path)
            for _, name, is_pkg in pkgutil.walk_packages(package.__path__):
                if not is_pkg:
                    try:
                        module = importlib.import_module(f'{module_path}.{name}')
                        for _, obj in inspect.getmembers(module, inspect.isclass):
                            if issubclass(obj, ToolBase) and obj is not ToolBase:
                                tool_instance = obj()
                                tools[tool_instance.name] = tool_instance
                    except ImportError as e:
                        print(f"Could not import module '{name}': {e}")
        except (ImportError, AttributeError) as e:
            print(f"Error discovering tools: {e}")
        return tools

    def _build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0,0,0,0)
        root_layout.setSpacing(0)

        # --- Title Bar ---
        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet(f"background-color: {COLOR_BACKGROUND_PRIMARY}; border-bottom: 1px solid {COLOR_BORDER};")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)
        title_layout.setSpacing(10)

        self.sidepanel_toggle_btn = QPushButton("☰")
        self.sidepanel_toggle_btn.setFixedSize(32, 32)
        self.sidepanel_toggle_btn.setStyleSheet(f'''
            QPushButton {{
                border: none;
                background-color: transparent;
                color: {COLOR_TEXT_PRIMARY};
                font-size: 20px;
            }}
            QPushButton:hover {{
                background-color: #334155;
            }}
        ''')
        self.sidepanel_toggle_btn.setCursor(Qt.PointingHandCursor)
        title_layout.addWidget(self.sidepanel_toggle_btn)
        
        title_label = QLabel("VAJRA - Offensive Security Platform")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 16px; font-weight: 600; border: none;")
        title_layout.addWidget(title_label, 1)

        self.notification_btn = QPushButton("🔔")
        self.notification_btn.setFixedSize(32, 32)
        self.notification_btn.setToolTip("Notifications")
        self.notification_btn.setCursor(Qt.PointingHandCursor)
        self.notification_btn.setStyleSheet(self.sidepanel_toggle_btn.styleSheet())
        title_layout.addWidget(self.notification_btn)

        root_layout.addWidget(title_bar)

        main_content_layout = QHBoxLayout()
        main_content_layout.setSpacing(0)

        self.sidepanel = Sidepanel(self.tools)
        main_content_layout.addWidget(self.sidepanel)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.setStyleSheet(TAB_WIDGET_STYLE)
        main_content_layout.addWidget(self.tab_widget)
        
        root_layout.addLayout(main_content_layout)

        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"""QStatusBar {{
                background-color: {COLOR_BACKGROUND_SECONDARY};
                border-top: 1px solid {COLOR_BORDER};
                color: {COLOR_TEXT_SECONDARY};
                padding: 0 10px;
            }}
        """)
        self.setStatusBar(self.status_bar)

        # --- Managers ---
        self.notification_manager = NotificationManager(self)

        # --- Connections ---
        self.sidepanel.tool_clicked.connect(self.open_tool_tab)
        self.sidepanel_toggle_btn.clicked.connect(self.toggle_sidepanel)
        self.notification_btn.clicked.connect(self.notification_manager.toggle_panel)

        # --- Initial State ---
        self.show_welcome_tab()
        self.sidepanel.setVisible(True) # Ensure sidepanel is visible by default

    def show_welcome_tab(self):
        if self.tab_widget.count() == 0:
            welcome_widget = WelcomeWidget()
            index = self.tab_widget.addTab(welcome_widget, "Welcome")
            self.tab_widget.tabBar().setTabButton(index, QTabBar.RightSide, None)
            self.tab_widget.setCurrentIndex(index)

    def open_tool_tab(self, tool: ToolBase):
        if tool.name in self.open_tool_widgets:
            widget = self.open_tool_widgets[tool.name]
            self.tab_widget.setCurrentWidget(widget)
            return

        if self.tab_widget.count() == 1 and self.tab_widget.tabText(0) == "Welcome":
            self.tab_widget.removeTab(0)

        tool_widget = tool.get_widget(main_window=self)
        index = self.tab_widget.addTab(tool_widget, tool.name)
        self.tab_widget.setCurrentIndex(index)
        self.open_tool_widgets[tool.name] = tool_widget

    def close_tab(self, index):
        widget = self.tab_widget.widget(index)
        if widget:
            tool_name_to_remove = None
            for name, w in self.open_tool_widgets.items():
                if w == widget:
                    tool_name_to_remove = name
                    break
            
            if tool_name_to_remove in self.open_tool_widgets:
                del self.open_tool_widgets[tool_name_to_remove]
            
            self.tab_widget.removeTab(index)
            widget.deleteLater()
            
        if self.tab_widget.count() == 0:
            self.show_welcome_tab()

    def stop_active_process(self):
        if self.active_process and self.active_process.poll() is None:
            self.active_process.kill()
            self.notification_manager.notify("Process terminated.")

    def toggle_sidepanel(self):
        is_visible = self.sidepanel.isVisible()
        self.sidepanel.setVisible(not is_visible)
        self.sidepanel_toggle_btn.setText("☰" if is_visible else "🗧")

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
        self.copy_button.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                background-color: transparent;
                border: none;
                padding: 10px;
            }
        """)
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
