
from enum import Enum
from PySide6.QtWidgets import QWidget

class ToolCategory(Enum):
    """Enumeration for tool categories."""
    AUTOMATION = "Automation"
    INFO_GATHERING = "Info Gathering"
    SUBDOMAIN_ENUMERATION = "Subdomain Enumeration"
    LIVE_SUBDOMAINS = "Live Subdomains"
    PORT_SCANNING = "Port Scanning"
    WEB_SCREENSHOTS = "Web Screenshots"
    WEB_SCANNING = "Web Scanning"
    CRACKER = "Cracker"
    FILE_ANALYSIS = "File Analysis"

class ToolBase:
    """
    Base class for a tool plugin.

    This class defines the "contract" that every tool must follow
    to be discovered and loaded by the main application.
    """

    @property
    def name(self) -> str:
        """
        The display name of the tool.
        This will be shown in the sidebar.
        """
        raise NotImplementedError

    @property
    def category(self) -> ToolCategory:
        """
        The category this tool belongs to.
        This determines its grouping in the sidebar.
        """
        raise NotImplementedError

    def get_widget(self, main_window: QWidget) -> QWidget:
        """
        Returns the main UI widget for the tool.

        Args:
            main_window: A reference to the main window instance.

        Returns:
            An instance of the tool's QWidget.
        """
        raise NotImplementedError
