import os
import sys
import platform

class PrivilegeManager:
    """
    Manages privilege checks for the application.
    Tools should use this to query status, but not to invoke sudo.
    """

    @staticmethod
    def is_root() -> bool:
        """Check if the current process is running as root/admin."""
        try:
            if platform.system() == "Windows":
                # On Windows, check if running as Administrator
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            elif hasattr(os, 'geteuid'):  # Unix-like systems
                return os.geteuid() == 0
            else:
                # Fallback for other systems - assume not root
                return False
        except Exception:
            # If privilege check fails, assume not privileged
            return False

    @staticmethod
    def require_root(tool_name: str) -> bool:
        """
        Check if root is required. 
        Returns True if satisfied (is root), False otherwise.
        This allows the UI to show a warning.
        """
        # Logic can be expanded, for now just checks is_root
        return PrivilegeManager.is_root()
