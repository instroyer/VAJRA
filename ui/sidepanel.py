
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QScrollArea
from PySide6.QtCore import Qt, Signal, QEasingCurve, QPropertyAnimation
from collections import defaultdict

from modules.bases import ToolCategory
from ui.styles import (
    COLOR_BACKGROUND_SECONDARY, COLOR_BORDER, COLOR_TEXT_SECONDARY, 
    COLOR_TEXT_PRIMARY, FONT_FAMILY_UI, SIDE_PANEL_STYLE, SIDE_PANEL_BUTTON_STYLE
)


class Sidepanel(QWidget):
    """Collapsible sidepanel for tool navigation."""
    tool_clicked = Signal(object)
    settings_clicked = Signal()

    def __init__(self, tools, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)
        self.tools = tools
        self.active_button = None

        self._build_ui()

    def _build_ui(self):
        # Apply the new SIDE_PANEL_STYLE
        self.setStyleSheet(SIDE_PANEL_STYLE)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- Header (Logo/Title and Toggle Button) ---
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 15, 10, 10)
        header_layout.setSpacing(10)

        title = QLabel("VAJRA")
        title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 20px; font-weight: 700;")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)

        self.main_layout.addWidget(header_widget)

        # --- Scroll Area for Tools ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")
        self.main_layout.addWidget(scroll_area)
        
        self.scroll_widget = QWidget()
        scroll_area.setWidget(self.scroll_widget)

        self.tools_layout = QVBoxLayout(self.scroll_widget)
        self.tools_layout.setContentsMargins(10, 0, 10, 10)
        self.tools_layout.setSpacing(5)
        self.tools_layout.setAlignment(Qt.AlignTop)

        self._populate_tools()

        # --- Footer (Settings Button) ---
        footer_widget = QWidget()
        footer_layout = QVBoxLayout(footer_widget)
        footer_layout.setContentsMargins(10, 10, 10, 10)
        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        # Apply the new SIDE_PANEL_BUTTON_STYLE
        self.settings_btn.setStyleSheet(SIDE_PANEL_BUTTON_STYLE)
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        footer_layout.addWidget(self.settings_btn)
        self.main_layout.addWidget(footer_widget)

    def _populate_tools(self):
        categorized_tools = defaultdict(list)
        for tool in self.tools.values():
            categorized_tools[tool.category].append(tool)

        order_of_categories = list(ToolCategory)
        sorted_categories = sorted(categorized_tools.keys(), key=lambda x: order_of_categories.index(x))

        for category in sorted_categories:
            category_name = category.name.replace("_", " ").upper()
            
            toggle = QPushButton(f"{category_name}  ▾")
            toggle.setCursor(Qt.PointingHandCursor)
            toggle.setStyleSheet(self._get_category_toggle_style())
            self.tools_layout.addWidget(toggle)

            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(15, 0, 0, 5) # Indent
            container_layout.setSpacing(4)

            sorted_tools = sorted(categorized_tools[category], key=lambda x: x.name)
            for tool in sorted_tools:
                # Apply the new SIDE_PANEL_BUTTON_STYLE
                button = self._add_tool_button(tool, container_layout)
                button.clicked.connect(lambda checked, t=tool, b=button: self._activate_button(b, t))

            container.setVisible(True) # Start expanded
            self.tools_layout.addWidget(container)

            toggle.clicked.connect(
                lambda checked, c=container, t=toggle, name=category_name: self._toggle_category(c, t, name)
            )

    def _toggle_category(self, container, toggle, name):
        is_visible = container.isVisible()
        container.setVisible(not is_visible)
        arrow = "▾" if not is_visible else "▸"
        toggle.setText(f"{name}  {arrow}")

    def _activate_button(self, button, tool):
        if self.active_button:
            # Use setChecked(False) to unapply the checked style
            self.active_button.setChecked(False)

        # Use setChecked(True) to apply the checked style
        button.setChecked(True)
        self.active_button = button

        self.tool_clicked.emit(tool)

    def _get_category_toggle_style(self):
        return f'''
            QPushButton {{
                color: {COLOR_TEXT_SECONDARY};
                font-size: 12px;
                font-weight: 700;
                text-align: left;
                border: none;
                padding: 8px 5px;
            }}
            QPushButton:hover {{
                color: {COLOR_TEXT_PRIMARY};
            }}
        '''

    # Removed _get_tool_button_style as it's now replaced by SIDE_PANEL_BUTTON_STYLE

    def _add_tool_button(self, tool, layout):
        btn = QPushButton(tool.name)
        btn.setCheckable(True) # Make buttons checkable for the :checked style
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(SIDE_PANEL_BUTTON_STYLE) # Use the imported style
        layout.addWidget(btn)
        return btn
