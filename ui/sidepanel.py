
import functools
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QScrollArea, QFrame
from PySide6.QtCore import Qt, Signal, QEasingCurve, QPropertyAnimation
from collections import defaultdict

from modules.bases import ToolCategory
from ui.styles import (
    COLOR_BG_SECONDARY, COLOR_BORDER_DEFAULT, COLOR_TEXT_SECONDARY, 
    COLOR_TEXT_PRIMARY, FONT_FAMILY_UI, SIDE_PANEL_STYLE, SIDE_PANEL_BUTTON_STYLE,
    SIDE_PANEL_CATEGORY_STYLE, SIDE_PANEL_HEADER_STYLE, COLOR_ACCENT_PRIMARY
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

        # --- Header with gradient ---
        header_widget = QWidget()
        header_widget.setStyleSheet(SIDE_PANEL_HEADER_STYLE)
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 18, 15, 15)
        header_layout.setSpacing(5)

        title = QLabel("⚡ VAJRA")
        title.setStyleSheet(f"color: {COLOR_ACCENT_PRIMARY}; font-size: 22px; font-weight: 800; background: transparent; border: none; font-family: {FONT_FAMILY_UI};")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        
        subtitle = QLabel("Offensive Security Platform")
        subtitle.setStyleSheet(f"color: #6b7280; font-size: 10px; font-weight: 500; background: transparent; border: none; font-family: {FONT_FAMILY_UI};")
        subtitle.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle)

        self.main_layout.addWidget(header_widget)

        # --- Scroll Area for Tools ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background: transparent; border: none;")
        self.main_layout.addWidget(scroll_area)
        
        self.scroll_widget = QWidget()
        self.scroll_widget.setStyleSheet("background: transparent;")
        scroll_area.setWidget(self.scroll_widget)

        self.tools_layout = QVBoxLayout(self.scroll_widget)
        self.tools_layout.setContentsMargins(12, 10, 12, 10)
        self.tools_layout.setSpacing(3)
        self.tools_layout.setAlignment(Qt.AlignTop)

        self._populate_tools()

        # --- Footer (Settings Button) ---
        footer_widget = QWidget()
        footer_widget.setStyleSheet("background: transparent;") # Removed border-top
        footer_layout = QVBoxLayout(footer_widget)
        footer_layout.setContentsMargins(12, 12, 12, 12)
        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a1a1a, stop:1 #2d1f1f);
                color: #9ca3af;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                padding: 10px 15px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2d1f1f, stop:1 #3d2f2f);
                color: #e5e7eb;
                border-color: {COLOR_ACCENT_PRIMARY};
            }
        """)
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        footer_layout.addWidget(self.settings_btn)
        self.main_layout.addWidget(footer_widget)

    def _populate_tools(self):
        categorized_tools = defaultdict(list)
        for tool_class in self.tools.values():
            # Access class attributes without instantiation
            tool_category = getattr(tool_class, 'category', None)
            if tool_category:
                categorized_tools[tool_category].append(tool_class)

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

            sorted_tools = sorted(categorized_tools[category], key=lambda x: getattr(x, 'name', x.__name__))
            for tool in sorted_tools:
                # Apply the new SIDE_PANEL_BUTTON_STYLE
                button = self._add_tool_button(tool, container_layout)
                button.clicked.connect(functools.partial(self._activate_button, button, tool))

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
                color: #f97316;
                font-size: 14px;
                font-weight: 700;
                text-align: left;
                border: none;
                border-bottom: 1px solid #2d2d4d;
                padding: 12px 5px 8px 5px;
                text-transform: uppercase;
                letter-spacing: 1px;
                background: transparent;
            }}
            QPushButton:hover {{
                color: #fb923c;
                background: transparent;
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
