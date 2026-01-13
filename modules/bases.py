
from enum import Enum

class ToolCategory(Enum):
    """Enumeration for tool categories."""
    AUTOMATION = "Automation"
    INFO_GATHERING = "Info Gathering"
    SUBDOMAIN_ENUMERATION = "Subdomain Enumeration"
    LIVE_SUBDOMAINS = "Live Subdomains"
    PORT_SCANNING = "Port Scanning"
    WEB_SCREENSHOTS = "Web Screenshots"
    WEB_SCANNING = "Web Scanning"
    WEB_INJECTION = "Web Injection"
    VULNERABILITY_SCANNER = "Vulnerability Scanner"
    CRACKER = "Cracker"
    PAYLOAD_GENERATOR = "Payload Generator"
    FILE_ANALYSIS = "File Analysis"

    
class ToolBase:
    """
    Base class for a tool plugin.

    This class defines the "contract" that every tool must follow
    to be discovered and loaded by the main application.
    """

    # Class attributes for discovery (to avoid instantiation)
    name = None  # Override in subclasses
    category = None  # Override in subclasses

    @property
    def display_name(self) -> str:
        """
        The display name of the tool.
        This will be shown in the sidebar.
        """
        return self.name or self.__class__.__name__

    @property
    def tool_category(self) -> ToolCategory:
        """
        The category this tool belongs to.
        This determines its grouping in the sidebar.
        """
        return self.category

    def get_widget(self, main_window) -> "QWidget":
        """
        Returns the main UI widget for the tool.

        Args:
            main_window: A reference to the main window instance.

        Returns:
            An instance of the tool's UI widget.
        """
        raise NotImplementedError

    def focus_primary_input(self):
        """
        Focuses the primary input field of the tool.
        
        This method is optional but recommended for keyboard accessibility.
        The tool implementation should find its main target input and call .setFocus().
        """
        pass
