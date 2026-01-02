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


class StoppableToolMixin:
    """
    Mixin for tools with stop button functionality.
    
    Usage:
        class MyTool(QWidget, StoppableToolMixin):
            def __init__(self):
                super().__init__()
                self.init_stoppable()
    """
    
    def init_stoppable(self):
        """Initialize stop functionality. Call in __init__()."""
        self._active_workers = []
        self.worker = None
    
    def register_worker(self, worker):
        """Register a worker for cleanup tracking."""
        if not hasattr(self, '_active_workers'):
            self._active_workers = []
        self._active_workers.append(worker)
        worker.finished.connect(lambda: self._unregister_worker(worker))
    
    def _unregister_worker(self, worker):
        if hasattr(self, '_active_workers') and worker in self._active_workers:
            self._active_workers.remove(worker)
    
    def safe_stop(self):
        """Safely stop the current worker."""
        try:
            if hasattr(self, 'worker') and self.worker:
                if self.worker.isRunning():
                    self.worker.stop()
                    self.worker.wait(1000)
                self.worker = None
        except Exception:
            pass
        self._update_button_states(running=False)
    
    def _update_button_states(self, running=False):
        try:
            if hasattr(self, 'run_button'):
                self.run_button.setEnabled(not running)
            if hasattr(self, 'stop_button'):
                self.stop_button.setEnabled(running)
            if hasattr(self, 'progress_bar'):
                self.progress_bar.setVisible(running)
        except Exception:
            pass
    
    def stop_all_workers(self):
        """Stop all active workers."""
        if not hasattr(self, '_active_workers'):
            return
        for worker in list(self._active_workers):
            try:
                if worker.isRunning():
                    worker.stop()
                    worker.wait(1000)
            except Exception:
                pass
        self._active_workers.clear()
        self.worker = None
    
    def closeEvent(self, event):
        """Clean up on widget close."""
        self.stop_all_workers()
        if hasattr(super(), 'closeEvent'):
            super().closeEvent(event)
        else:
            event.accept()


StoppableMixin = StoppableToolMixin
