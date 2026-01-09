import os
from PySide6.QtCore import QSettings

class ConfigManager:
    """
    Centralized Configuration Manager (Singleton-style).
    Handles persistent and session-only settings.
    """
    _settings = None
    _output_dir = None  # Session-only storage
    
    # Keys for QSettings (Only persist what is allowed)
    KEY_NOTIFICATIONS = "app/notifications"
    
    @staticmethod
    def _get_settings():
        if ConfigManager._settings is None:
            ConfigManager._settings = QSettings("VAJRA", "Platform")
        return ConfigManager._settings

    @classmethod
    def initialize_defaults(cls):
        """Ensure critical defaults are set on startup."""
        # Notifications default to True if not set
        s = cls._get_settings()
        if not s.contains(cls.KEY_NOTIFICATIONS):
            s.setValue(cls.KEY_NOTIFICATIONS, True)

    # =========================================================================
    # Output Directory (SESSION ONLY - Resets on Restart)
    # =========================================================================
    
    @classmethod
    def get_output_dir(cls) -> str:
        """Get the current output directory (Session scope)."""
        if cls._output_dir is None:
            # Lazy import to avoid circular dependency
            from core.fileops import DEFAULT_OUTPUT_DIR
            cls._output_dir = DEFAULT_OUTPUT_DIR
            
            # Ensure it exists
            try:
                os.makedirs(cls._output_dir, exist_ok=True)
            except OSError:
                pass
                
        return cls._output_dir

    @classmethod
    def set_output_dir(cls, path: str):
        """Set output directory for this session only."""
        cls._output_dir = str(path)
        # DO NOT PERSIST to settings

    # =========================================================================
    # Notifications (Persistent)
    # =========================================================================
    
    @classmethod
    def get_notifications_enabled(cls) -> bool:
        return cls._get_settings().value(cls.KEY_NOTIFICATIONS, True, type=bool)

    @classmethod
    def set_notifications_enabled(cls, enabled: bool):
        cls._get_settings().setValue(cls.KEY_NOTIFICATIONS, enabled)
