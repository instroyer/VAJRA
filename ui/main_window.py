
import inspect
import importlib
import pkgutil
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QTabWidget, QTabBar, QPushButton, QStatusBar, QSplitter,
    QPlainTextEdit, QGridLayout, QLineEdit, QApplication, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QShortcut, QKeySequence

from modules.bases import ToolBase, ToolCategory
from ui.sidepanel import Sidepanel
from ui.notification import NotificationManager
from ui.settingpanel import SettingsPanel
from ui.styles import (
    MAIN_WINDOW_STYLE, TAB_WIDGET_STYLE,
    COLOR_BG_SECONDARY, COLOR_BORDER_DEFAULT, COLOR_TEXT_SECONDARY, COLOR_TEXT_PRIMARY,
    COLOR_BG_PRIMARY, TOOL_HEADER_STYLE, LABEL_STYLE,
    TARGET_INPUT_STYLE, RUN_BUTTON_STYLE, STOP_BUTTON_STYLE,
    OUTPUT_TEXT_EDIT_STYLE, TOOL_VIEW_STYLE, FONT_FAMILY_UI
)
from ui.styles import OutputView  # Import OutputView from styles
from core.tgtinput import TargetInput

class WelcomeWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        title = QLabel("Welcome to VAJRA - Offensive Security Platform")
        title.setStyleSheet(f"font-size: 28px; font-weight: 300; color: {COLOR_TEXT_PRIMARY}; font-family: {FONT_FAMILY_UI};")

        subtitle = QLabel("Select a tool from the sidepanel to begin.")
        subtitle.setStyleSheet(f"font-size: 16px; color: {COLOR_TEXT_SECONDARY}; font-family: {FONT_FAMILY_UI};")
        
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
        self.current_tool_obj = {} # Helper to track ToolBase objects for focus delegation
        self.tools = self._discover_tools()
        self._build_ui()
        self._setup_shortcuts()

    def _discover_tools(self):
        """
        Hybrid tool discovery:
        - Development mode: Auto-discovers all modules in modules/ directory
        - Frozen mode (PyInstaller): Uses fallback list for reliability
        - Nuitka: Works with both (use --include-package=modules)
        """
        tools = {}
        module_path = "modules"
        
        # Check if running as frozen executable (PyInstaller)
        is_frozen = getattr(sys, 'frozen', False)
        
        if is_frozen:
            # PyInstaller: Use explicit list (dynamic discovery doesn't work)
            print("[Discovery] Running in frozen mode - using fallback list")
            known_modules = [
                "amass", "WebInjection", "automation", "dencoder", "dig", "dnsrecon", 
                "eyewitness", "ffuf", "gobuster", "hashcat", "hashfinder", 
                "httpx", "hydra", "john", "msfvenom", "nikto", "nmap", 
                "nuclei", "portscanner", "searchsploit", "strings", 
                "subfinder", "wafw00f", "whois"
            ]
        else:
            # Development/Nuitka: Auto-discover all modules dynamically
            print("[Discovery] Running in dev mode - auto-discovering modules")
            try:
                import modules
                known_modules = [
                    name for _, name, _ in pkgutil.iter_modules(modules.__path__)
                    if name != "bases"  # Skip the base class
                ]
                print(f"[Discovery] Found modules: {known_modules}")
                
                # If auto-discovery returned nothing (e.g. weird environment), use fallback
                if not known_modules:
                    print("[Discovery] Auto-discovery returned 0 modules, forcing fallback list")
                    known_modules = [
                        "amass", "WebInjection", "automation", "dencoder", "dig", "dnsrecon", 
                        "eyewitness", "ffuf", "gobuster", "hashcat", "hashfinder", 
                        "httpx", "hydra", "john", "msfvenom", "nikto", "nmap", 
                        "nuclei", "portscanner", "searchsploit", "strings", 
                        "subfinder", "wafw00f", "whois"
                    ]
            except Exception as e:
                # Fallback if auto-discovery fails
                print(f"[Discovery] Auto-discovery failed: {e}, using fallback")
                known_modules = [
                "amass", "WebInjection", "automation", "dencoder", "dig", "dnsrecon", 
                "eyewitness", "ffuf", "gobuster", "hashcat", "hashfinder", 
                "httpx", "hydra", "john", "msfvenom", "nikto", "nmap", 
                "nuclei", "portscanner", "searchsploit", "strings", 
                "subfinder", "wafw00f", "whois"
                ]
        
        
        # Load each module and find ToolBase subclasses (lazy loading)
        for name in known_modules:
            try:
                module = importlib.import_module(f'{module_path}.{name}')
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, ToolBase) and obj is not ToolBase:
                        tool_name = getattr(obj, 'name', None)
                        if tool_name:
                            tools[tool_name] = obj
            except ImportError as e:
                print(f"[Discovery] ImportError loading {name}: {e}")
            except Exception as e:
                print(f"[Discovery] Error loading {name}: {e}")
        
        print(f"[Discovery] Loaded {len(tools)} tools: {list(tools.keys())}")
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
        title_bar.setStyleSheet(f"background-color: {COLOR_BG_PRIMARY}; border-bottom: 1px solid {COLOR_BORDER_DEFAULT};")
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
        # Handle tab change to update context for shortcuts if needed, 
        # but shortcuts work on active window/widget usually.
        self.tab_widget.setStyleSheet(TAB_WIDGET_STYLE)
        main_content_layout.addWidget(self.tab_widget)
        
        root_layout.addLayout(main_content_layout)

        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f'''QStatusBar {{
                background-color: {COLOR_BG_SECONDARY};
                border-top: 1px solid {COLOR_BORDER_DEFAULT};
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

    def _setup_shortcuts(self):
        """Setup global keyboard shortcuts."""
        # Run Active Tool: Ctrl+Enter
        self.shortcut_run = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.shortcut_run.activated.connect(self._run_active_tool)
        
        # Stop Active Tool: Esc
        self.shortcut_stop = QShortcut(QKeySequence("Esc"), self)
        self.shortcut_stop.activated.connect(self._stop_active_tool)
        
        # Clear Output: Ctrl+L
        self.shortcut_clear = QShortcut(QKeySequence("Ctrl+L"), self)
        self.shortcut_clear.activated.connect(self._clear_active_output)
        
        # Focus Input: Ctrl+/ 
        self.shortcut_focus = QShortcut(QKeySequence("Ctrl+/"), self)
        self.shortcut_focus.activated.connect(self._focus_primary_input)

    def _get_active_tool_widget(self):
        return self.tab_widget.currentWidget()

    def _run_active_tool(self):
        widget = self._get_active_tool_widget()
        if widget and hasattr(widget, 'run_button') and widget.run_button.isEnabled():
            if hasattr(widget, 'run_scan'):
                widget.run_scan() # Direct call preferred or click
            else:
                widget.run_button.click()

    def _stop_active_tool(self):
        widget = self._get_active_tool_widget()
        if widget and hasattr(widget, 'stop_scan'):
            widget.stop_scan()

    def _clear_active_output(self):
        widget = self._get_active_tool_widget()
        if widget and hasattr(widget, 'output') and hasattr(widget.output, 'clear'):
            widget.output.clear()
            self.notification_manager.notify("Output cleared")

    def _focus_primary_input(self):
        widget = self._get_active_tool_widget()
        # We need the ToolBase object to delegate this properly if using the new method
        # or we try to find it on the widget if the widget implements it
        
        # Option 1: Widget implements it (if ToolView inherits correctly or manually implemented)
        if widget and hasattr(widget, 'target_input'):
             widget.target_input.setFocus()
             return
             
        # Option 2: Fallback to generic search for QLineEdit
        if widget:
             input_widget = widget.findChild(QLineEdit)
             if input_widget:
                 input_widget.setFocus()

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

    def open_tool_tab(self, tool_class):
        # Handle both class references (lazy loading) and instances
        if inspect.isclass(tool_class) and issubclass(tool_class, ToolBase):
            # It's a class, instantiate it
            tool = tool_class()
        else:
            # It's already an instance
            tool = tool_class

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

            # Store tool entry for focus delegation
            self.current_tool_obj[tool.name] = tool
            
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
        """Close a tab and clean up its worker processes."""
        widget = self.tab_widget.widget(index)
        if widget:
            # Stop any running processes in this tool
            # Check for stop_all_workers first, then fallback to stop_scan
            if hasattr(widget, 'stop_all_workers'):
                widget.stop_all_workers()
            elif hasattr(widget, 'stop_scan'):
                try:
                    widget.stop_scan()
                except Exception:
                    pass
            
            tool_name_to_remove = None
            for name, w in self.open_tool_widgets.items():
                if w == widget:
                    tool_name_to_remove = name
                    break
            
            if tool_name_to_remove in self.open_tool_widgets:
                del self.open_tool_widgets[tool_name_to_remove]
                if tool_name_to_remove in self.current_tool_obj:
                    del self.current_tool_obj[tool_name_to_remove]
            
            self.tab_widget.removeTab(index)
            widget.deleteLater()
            
        if self.tab_widget.count() == 0:
            self.show_welcome_tab()

    def stop_active_process(self):
        if self.active_process:
            # Handle ProcessWorker (QThread)
            if hasattr(self.active_process, 'stop'):
                self.active_process.stop()
                if hasattr(self.active_process, 'wait'):
                    self.active_process.wait(2000) # Optional wait
            # Handle legacy subprocess.Popen
            elif hasattr(self.active_process, 'poll') and self.active_process.poll() is None:
                if hasattr(self.active_process, 'kill'):
                    self.active_process.kill()
            
            self.notification_manager.notify("Process terminated.")

    def toggle_sidepanel(self):
        is_visible = self.sidepanel.isVisible()
        self.sidepanel.setVisible(not is_visible)
        self.sidepanel_toggle_btn.setText("☰" if is_visible else "✕")

    def closeEvent(self, event):
        """
        Clean up all running processes when the application closes.
        This ensures no zombie processes are left behind.
        """
        # Stop all workers in open tool widgets
        for tool_name, widget in list(self.open_tool_widgets.items()):
            try:
                if hasattr(widget, 'stop_all_workers'):
                    widget.stop_all_workers()
                elif hasattr(widget, 'stop_scan'):
                    widget.stop_scan()
            except Exception:
                pass
        
        # Stop active process if any
        self.stop_active_process()
        
        # Accept the close event
        event.accept()
