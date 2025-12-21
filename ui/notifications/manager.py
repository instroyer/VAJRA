from ui.notifications.toast import ToastNotification


class NotificationManager:
    """
    Central notification manager.
    - Shows toast notifications
    - Adds entries to notification panel
    - UI-only (no engine dependency)
    """

    def __init__(self, main_window):
        self.main_window = main_window
        self.panel = main_window.notification_panel

    def notify(self, message: str):
        """
        Send a notification:
        - Show toast (2 sec)
        - Add to notification panel
        """

        # Add to panel (history)
        self.panel.add_notification(message)

        # Show toast
        toast = ToastNotification(message, parent=self.main_window)
        toast.show_at_bottom_right()
