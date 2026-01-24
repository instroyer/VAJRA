"""
VAJRA Worker Module - Subprocess execution and stop functionality.
"""

import subprocess
import signal
import os
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QWidget
from core.config import ConfigManager
from ui.styles import SafeStop, OutputHelper


class ProcessWorker(QThread):
    """Worker thread for running subprocess commands."""
    
    output_ready = Signal(str)
    error = Signal(str)
    stopped = Signal()

    def __init__(self, command, shell=False, stdin_data=None, buffer_output=True):
        super().__init__()
        self.command = command
        self.shell = shell
        self.stdin_data = stdin_data
        self.process = None
        self.is_running = True
        self._was_stopped = False
        self._buffer_output = buffer_output
        self._output_buffer = []  # Buffer for batched output updates
        self._buffer_timer = None

        # Handle long commands
        if not shell and isinstance(command, list):
            command_str = ' '.join(str(c) for c in command)
            if len(command) > 50 or len(command_str) > 5000:
                self.command = ['sh', '-c', command_str]

    def run(self):
        try:
            # Platform-specific "death pact" to ensure child dies with parent
            def _set_pdeathsig():
                import ctypes
                import signal
                try:
                    # PR_SET_PDEATHSIG = 1, SIGTERM = 15
                    libc = ctypes.CDLL("libc.so.6")
                    libc.prctl(1, 15, 0, 0, 0)
                except Exception:
                    pass

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
                # Only use preexec_fn on Linux for safety
                if os.name == 'posix' and os.uname().sysname == 'Linux':
                    popen_kwargs['preexec_fn'] = _set_pdeathsig
            
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

            if self._buffer_output:
                # Buffered output mode (better for high-frequency output)
                while self.is_running and self.process.poll() is None:
                    try:
                        line = self.process.stdout.readline()
                        if line:
                            # Preserve newlines for proper formatting
                            self._output_buffer.append(line.rstrip('\n'))  # Only strip trailing newline, preserve spaces
                            self._flush_buffer_if_needed()
                    except (ValueError, OSError):
                        break

                if not self._was_stopped and self.process.stdout:
                    try:
                        remaining = self.process.stdout.read()
                        if remaining:
                            # Split on newlines but preserve empty lines that might be intentional formatting
                            lines = remaining.split('\n')
                            for i, line in enumerate(lines):
                                if line or i < len(lines) - 1:  # Keep empty lines that aren't the last one
                                    self._output_buffer.append(line)
                    except (ValueError, OSError):
                        pass

                # Flush any remaining buffered output
                self._flush_buffer(force=True)
            else:
                # Real-time output mode (better for formatted tools like Nikto)
                while self.is_running and self.process.poll() is None:
                    try:
                        line = self.process.stdout.readline()
                        if line:
                            # Emit line immediately without buffering
                            self.output_ready.emit(line.rstrip('\n'))
                    except (ValueError, OSError):
                        break

                if not self._was_stopped and self.process.stdout:
                    try:
                        remaining = self.process.stdout.read()
                        if remaining:
                            # Process remaining output line by line
                            for line in remaining.split('\n'):
                                if line.strip():  # Only emit non-empty lines
                                    self.output_ready.emit(line)
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

    def _flush_buffer_if_needed(self):
        """Flush buffer if it exceeds threshold."""
        if len(self._output_buffer) >= 50:  # Flush every 50 lines
            self._flush_buffer()

    def _flush_buffer(self, force=False):
        """Flush buffered output to UI."""
        if self._output_buffer:
            if len(self._output_buffer) == 1:
                # Single line, emit directly
                self.output_ready.emit(self._output_buffer[0])
            else:
                # Multiple lines, emit as combined batch
                combined_output = '\n'.join(self._output_buffer)
                self.output_ready.emit(combined_output)
            self._output_buffer.clear()

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

class ToolExecutionMixin(SafeStop, OutputHelper):
    """
    Optimized mixin to enforce unified tool execution lifecycle.

    Required attributes (for performance):
    - run_button: RunButton instance
    - stop_button: StopButton instance
    - output: OutputView instance
    - main_window: MainWindow reference (optional)

    Required methods:
    - on_execution_finished(success: bool = True)

    Optional methods:
    - on_new_output(line: str) [preferred]
    - _on_output(line: str) [fallback]
    - on_output(line: str) [legacy fallback]
    - _error(message: str)

    This mixin manages:
    - Button states (Run/Stop)
    - Spinner animation
    - Progress tracking
    - Notifications
    - Final output message
    """

    def init_progress_tracking(self):
        """Initialize progress tracking for long-running operations."""
        if not hasattr(self, 'progress_bar'):
            from ui.styles import StyledProgressBar
            self.progress_bar = StyledProgressBar()
            # Find the output view and add progress bar above it
            if hasattr(self, 'output') and hasattr(self.output, 'parent'):
                parent_layout = self.output.parent().layout()
                if parent_layout:
                    output_index = parent_layout.indexOf(self.output)
                    if output_index >= 0:
                        parent_layout.insertWidget(output_index, self.progress_bar)

    def update_progress(self, current, total, status_text=""):
        """Update progress bar with current/total values."""
        if hasattr(self, 'progress_bar'):
            if total > 0:
                percentage = int((current / total) * 100)
                self.progress_bar.setValue(percentage)
                if status_text:
                    self.progress_bar.setFormat(f"{status_text} ({current}/{total})")
                else:
                    self.progress_bar.setFormat(f"{current}/{total} ({percentage}%)")
                self.progress_bar.setVisible(True)
            else:
                self.progress_bar.setVisible(False)

    def hide_progress(self):
        """Hide the progress bar."""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(False)
    
    def start_execution(self, command: str, output_path: str | None = None, shell: bool = True, clear_output: bool = True, buffer_output: bool = True, skip_ui_updates: bool = False):
        """
        Optimized start execution with reduced overhead.

        Args:
            command: Command string to execute
            output_path: Path for output file
            shell: Use shell execution
            clear_output: Clear output area before starting
            buffer_output: Use buffered output mode
            skip_ui_updates: Skip button state updates for performance
        """

        # 1. UI State (skip if requested for performance)
        if not skip_ui_updates:
            # Assume run_button and stop_button exist (required by interface)
            self.run_button.set_loading(True)
            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)

        # 2. Store output path for completion
        self._execution_output_path = output_path

        # 3. Log Command (assume output exists)
        if clear_output:
            self.output.clear()
        self._section("Command")
        self._raw(command)

        # 4. Create and Start Worker
        try:
            self.worker = ProcessWorker(command, shell=shell, buffer_output=buffer_output)
            self.register_worker(self.worker)

            # Connect Signals - Optimized: prefer on_new_output, fallback to legacy
            if hasattr(self, 'on_new_output'):
                self.worker.output_ready.connect(self.on_new_output)
            elif hasattr(self, '_on_output'):
                self.worker.output_ready.connect(self._on_output)
            elif hasattr(self, 'on_output'):
                self.worker.output_ready.connect(self.on_output)

            # Finished handling (required method)
            self.worker.finished.connect(self.on_execution_finished)

            # Error handling (optional)
            if hasattr(self, '_error'):
                self.worker.error.connect(self._error)

            self.worker.start()

            # Main window tracking (optional)
            if hasattr(self, 'main_window') and self.main_window:
                self.main_window.active_process = self.worker

        except Exception as e:
            if hasattr(self, '_error'):
                self._error(f"Failed to start execution: {e}")

            # Handle cleanup safely
            try:
                self.on_execution_finished(success=False)
            except (TypeError, Exception):
                self.on_execution_finished()
        
    def on_execution_finished(self, success: bool = True):
        """
        Optimized handler for when tool execution finishes.
        MUST be connected to the worker's finished signal.
        """
        # 1. Reset UI State (assume buttons exist)
        self.run_button.set_loading(False)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        # 2. Final Output Message
        path = getattr(self, '_execution_output_path', None)
        suppress = getattr(self, '_suppress_result_msg', False)
        if path and not suppress:
            self._raw("") # Newline
            self._info(f"Results saved to:<br><b>{path}</b>")

        # 3. Notification (check config once, not on every call)
        if ConfigManager.get_notifications_enabled():
            msg = "Tool execution completed"
            if hasattr(self, 'tool_name'):
                msg = f"{self.tool_name} finished"
            self._notify(msg)

        # 4. Clean up worker (SafeStop handles this via register_worker)
