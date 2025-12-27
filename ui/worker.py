import subprocess
from PySide6.QtCore import QThread, Signal


class ProcessWorker(QThread):
    """
    Worker thread for running subprocess commands without blocking the UI.
    Emits signals for output updates and completion.
    """
    output_ready = Signal(str)  # Emitted for each line of output
    finished = Signal()  # Emitted when process completes
    error = Signal(str)  # Emitted if an error occurs

    def __init__(self, command, shell=False, stdin_data=None):
        super().__init__()
        self.command = command
        self.shell = shell
        self.stdin_data = stdin_data  # For sudo password injection
        self.process = None
        self.is_running = True

        # Auto-detect if command is too long for execvp
        if not shell and isinstance(command, list):
            command_str = ' '.join(command)
            if len(command) > 50 or len(command_str) > 5000:
                # Convert to shell command to avoid argument list limits
                self.command = ['sh', '-c', command_str]
                self.shell = True

    def run(self):
        """Run the subprocess in a separate thread"""
        try:
            self.process = subprocess.Popen(
                self.command,
                shell=self.shell,
                stdin=subprocess.PIPE if self.stdin_data else None,  # Enable stdin if password provided
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Write password to stdin if provided (for sudo -S)
            if self.stdin_data:
                self.process.stdin.write(self.stdin_data)
                self.process.stdin.flush()
                self.process.stdin.close()

            # Read output line by line
            while self.is_running and self.process.poll() is None:
                line = self.process.stdout.readline()
                if line:
                    self.output_ready.emit(line.rstrip())

            # Capture any remaining output
            remaining = self.process.stdout.read()
            if remaining:
                for line in remaining.split('\n'):
                    if line.strip():
                        self.output_ready.emit(line.rstrip())

            self.process.wait()
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit()

    def stop(self):
        """Stop the process"""
        self.is_running = False
        if self.process and self.process.poll() is None:
            self.process.kill()
            self.process.wait()
