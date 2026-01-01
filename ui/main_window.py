
import inspect
import importlib
import pkgutil
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QTabWidget, QTabBar, QPushButton, QStatusBar, QSplitter,
    QPlainTextEdit, QGridLayout, QLineEdit, QApplication, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from modules.bases import ToolBase, ToolCategory
from ui.sidepanel import Sidepanel
from ui.notification import NotificationManager
from ui.settingpanel import SettingsPanel
from ui.styles import (
    MAIN_WINDOW_STYLE, TAB_WIDGET_STYLE,
    COLOR_BACKGROUND_SECONDARY, COLOR_BORDER, COLOR_TEXT_SECONDARY, COLOR_TEXT_PRIMARY,
    COLOR_BACKGROUND_PRIMARY, TOOL_HEADER_STYLE, LABEL_STYLE,
    TARGET_INPUT_STYLE, RUN_BUTTON_STYLE, STOP_BUTTON_STYLE,
    OUTPUT_TEXT_EDIT_STYLE, TOOL_VIEW_STYLE
)
from ui.widgets import OutputView  # Only import OutputView
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
                                tool_name = tool_instance.name
                                
                                tools[tool_name] = tool_instance
                                print(f"✅ Loaded tool: {tool_name} (Category: {tool_instance.category.name})")

                                    
                    except ImportError as e:
                        print(f"❌ Could not import module '{name}': {e}")
                    except Exception as e:
                        print(f"❌ Error loading tool from '{name}': {e}")
                        
        except (ImportError, AttributeError) as e:
            print(f"❌ Error discovering tools: {e}")
        
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

        self.sidepanel_toggle_btn = QPushButton("✕")
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
        self.status_bar.setStyleSheet(f'''QStatusBar {{
                background-color: {COLOR_BACKGROUND_SECONDARY};
                border-top: 1px solid {COLOR_BORDER};
                color: {COLOR_TEXT_SECONDARY};
                padding: 0 10px;
            }}
        ''')
        self.setStatusBar(self.status_bar)

        # --- Managers ---
        self.notification_manager = NotificationManager(self)

        # --- Connections ---
        self.sidepanel.tool_clicked.connect(self.open_tool_tab)
        self.sidepanel.settings_clicked.connect(self.open_settings_tab)  # Changed to open as tab
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
    
    def open_settings_tab(self):
        """Open settings as a tab"""
        # Check if settings tab already open
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "⚙️ Settings":
                self.tab_widget.setCurrentIndex(i)
                return
        
        # Remove welcome tab if present
        if self.tab_widget.count() == 1 and self.tab_widget.tabText(0) == "Welcome":
            self.tab_widget.removeTab(0)
        
        # Create settings panel
        settings_widget = SettingsPanel(self)
        index = self.tab_widget.addTab(settings_widget, "⚙️ Settings")
        
        # Add close button
        close_btn = QPushButton("✕")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f'''
            QPushButton {{
                background: transparent;
                border: none;
                color: {COLOR_TEXT_SECONDARY};
                font-size: 14px;
                font-weight: bold;
                padding: 0px 5px;
            }}
            QPushButton:hover {{
                color: {COLOR_TEXT_PRIMARY};
                background-color: #555;
                border-radius: 3px;
            }}
        ''')
        close_btn.clicked.connect(lambda: self.close_tab(self.tab_widget.indexOf(settings_widget)))
        self.tab_widget.tabBar().setTabButton(index, QTabBar.RightSide, close_btn)
        
        self.tab_widget.setCurrentIndex(index)

    def open_tool_tab(self, tool: ToolBase):
        if tool.name in self.open_tool_widgets:
            widget = self.open_tool_widgets[tool.name]
            self.tab_widget.setCurrentWidget(widget)
            return

        if self.tab_widget.count() == 1 and self.tab_widget.tabText(0) == "Welcome":
            self.tab_widget.removeTab(0)

        try:
            tool_widget = tool.get_widget(main_window=self)
            if tool_widget is None:
                QMessageBox.critical(self, "Tool Error", f"Tool {tool.name} returned None widget")
                return
            index = self.tab_widget.addTab(tool_widget, tool.name)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            QMessageBox.critical(self, "Tool Error", f"Failed to open {tool.name}:\n{str(e)}\n\nDetails:\n{error_details}")
            return
        
        # --- Add custom close button ---
        close_btn = QPushButton("✕")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f'''
            QPushButton {{
                background: transparent;
                border: none;
                color: {COLOR_TEXT_SECONDARY};
                font-size: 14px;
                font-weight: bold;
                padding: 0px 5px;
            }}
            QPushButton:hover {{
                color: {COLOR_TEXT_PRIMARY};
                background-color: #555;
                border-radius: 3px;
            }}
        ''')
        close_btn.clicked.connect(lambda: self.close_tab(self.tab_widget.indexOf(tool_widget)))
        self.tab_widget.tabBar().setTabButton(index, QTabBar.RightSide, close_btn)

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
        self.sidepanel_toggle_btn.setText("☰" if is_visible else "✕")
