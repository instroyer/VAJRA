"""
VAJRA Worker Module - Subprocess execution and stop functionality.
"""

import subprocess
import signal
import os
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QWidget


class ProcessWorker(QThread):
    """Worker thread for running subprocess commands."""
    
    output_ready = Signal(str)
    error = Signal(str)
    stopped = Signal()

    def __init__(self, command, shell=False, stdin_data=None):
        super().__init__()
        self.command = command
        self.shell = shell
        self.stdin_data = stdin_data
        self.process = None
        self.is_running = True
        self._was_stopped = False

        # Handle long commands
        if not shell and isinstance(command, list):
            command_str = ' '.join(str(c) for c in command)
            if len(command) > 50 or len(command_str) > 5000:
                self.command = ['sh', '-c', command_str]

    def run(self):
        try:
            popen_kwargs = {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.STDOUT,
                'text': True,
                'bufsize': 1,
            }
            
            if self.stdin_data:
                popen_kwargs['stdin'] = subprocess.PIPE
            
            if os.name != 'nt':
                popen_kwargs['start_new_session'] = True
            
            self.process = subprocess.Popen(
                self.command,
                shell=self.shell,
                **popen_kwargs
            )

            if self.stdin_data and self.process.stdin:
                try:
                    self.process.stdin.write(self.stdin_data)
                    self.process.stdin.flush()
                    self.process.stdin.close()
                except (BrokenPipeError, OSError):
                    pass

            while self.is_running and self.process.poll() is None:
                try:
                    line = self.process.stdout.readline()
                    if line:
                        self.output_ready.emit(line.rstrip())
                except (ValueError, OSError):
                    break

            if not self._was_stopped and self.process.stdout:
                try:
                    remaining = self.process.stdout.read()
                    if remaining:
                        for line in remaining.split('\n'):
                            if line.strip():
                                self.output_ready.emit(line.rstrip())
                except (ValueError, OSError):
                    pass

            if self.process:
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self._force_kill()

        except Exception as e:
            if not self._was_stopped:
                self.error.emit(str(e))

    def stop(self):
        """Stop the process gracefully (SIGTERM then SIGKILL)."""
        self._was_stopped = True
        self.is_running = False
        
        if not self.process or self.process.poll() is not None:
            return
        
        try:
            if os.name != 'nt':
                try:
                    pgid = os.getpgid(self.process.pid)
                    os.killpg(pgid, signal.SIGTERM)
                except (ProcessLookupError, OSError):
                    pass
                
                try:
                    self.process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self._force_kill()
            else:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()
        except Exception:
            self._force_kill()
        
        self.stopped.emit()
    
    def _force_kill(self):
        """Force kill the process."""
        if not self.process:
            return
        try:
            if os.name != 'nt':
                try:
                    pgid = os.getpgid(self.process.pid)
                    os.killpg(pgid, signal.SIGKILL)
                except (ProcessLookupError, OSError):
                    pass
            else:
                self.process.kill()
            self.process.wait(timeout=1)
        except Exception:
            pass
