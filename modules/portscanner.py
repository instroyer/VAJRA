import os
import socket
import struct
import random
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue

from PySide6.QtCore import QObject, Signal, Qt, QRect, QThread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QLineEdit, QGroupBox, QMessageBox, QSplitter, QApplication, QCheckBox, QProgressBar
)

from modules.bases import ToolBase, ToolCategory
from ui.main_window import BaseToolView
from core.tgtinput import parse_targets
from core.fileops import create_target_dirs
from ui.styles import TARGET_INPUT_STYLE, COLOR_BACKGROUND_INPUT, COLOR_TEXT_PRIMARY, COLOR_BORDER, COLOR_BORDER_INPUT_FOCUSED
from PySide6.QtGui import QPainter, QPen, QBrush, QPolygon
from PySide6.QtCore import QPoint


# ==============================
# Custom Styled ComboBox
# ==============================

class StyledComboBox(QComboBox):
    """Custom ComboBox with visible arrow and consistent background."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(self._get_style())
    
    def _get_style(self):
        return f"""
            QComboBox {{
                background-color: {COLOR_BACKGROUND_INPUT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 8px;
                padding-right: 20px;
            }}
            QComboBox:focus {{
                border: 1px solid {COLOR_BORDER_INPUT_FOCUSED};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid {COLOR_BORDER};
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-color: {COLOR_BACKGROUND_INPUT};
            }}
            QComboBox::drop-down:hover {{
                background-color: #4A4A4A;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLOR_BACKGROUND_INPUT};
                border: 1px solid {COLOR_BORDER};
                color: {COLOR_TEXT_PRIMARY};
                selection-background-color: {COLOR_BORDER_INPUT_FOCUSED};
                selection-color: {COLOR_TEXT_PRIMARY};
                outline: none;
            }}
        """
    
    def paintEvent(self, event):
        """Custom paint event to draw arrow."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        drop_down_width = 20
        drop_down_x = width - drop_down_width
        drop_down_rect = QRect(drop_down_x, 0, drop_down_width, height)
        
        arrow_size = 6
        center_x = drop_down_rect.center().x()
        center_y = drop_down_rect.center().y()
        
        painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(QBrush(COLOR_TEXT_PRIMARY))
        
        arrow = QPolygon([
            QPoint(center_x - arrow_size//2, center_y - arrow_size//3),
            QPoint(center_x + arrow_size//2, center_y - arrow_size//3),
            QPoint(center_x, center_y + arrow_size//2)
        ])
        painter.drawPolygon(arrow)


# ==============================
# Custom Port Scanner Engine
# ==============================

class PortScannerEngine:
    """Advanced custom port scanner with stealth capabilities."""
    
    # Common service ports and their names
    SERVICE_PORTS = {
        21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS',
        80: 'HTTP', 110: 'POP3', 111: 'RPC', 135: 'MSRPC', 139: 'NetBIOS',
        143: 'IMAP', 443: 'HTTPS', 445: 'SMB', 993: 'IMAPS', 995: 'POP3S',
        1433: 'MSSQL', 3306: 'MySQL', 3389: 'RDP', 5432: 'PostgreSQL',
        5900: 'VNC', 8080: 'HTTP-Proxy', 8443: 'HTTPS-Alt'
    }
    
    def __init__(self, target, ports, scan_type='connect', timeout=1.0, threads=100, 
                 stealth_mode=False, randomize_ports=False, delay=0):
        self.target = target
        self.ports = ports
        self.scan_type = scan_type
        self.timeout = timeout
        self.threads = threads
        self.stealth_mode = stealth_mode
        self.randomize_ports = randomize_ports
        self.delay = delay
        self.open_ports = []
        self.results = []
        self.lock = threading.Lock()
        
    def resolve_target(self):
        """Resolve hostname to IP address."""
        try:
            ip = socket.gethostbyname(self.target)
            return ip
        except socket.gaierror:
            return None
    
    def get_service_name(self, port):
        """Get service name for common ports."""
        return self.SERVICE_PORTS.get(port, 'Unknown')
    
    def grab_banner(self, ip, port, timeout=2):
        """Attempt to grab service banner."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            
            if result == 0:
                # Connection successful, try to receive banner
                try:
                    # For HTTP/HTTPS, send a simple request
                    if port in [80, 8080]:
                        sock.send(b'HEAD / HTTP/1.1\r\nHost: ' + ip.encode() + b'\r\n\r\n')
                    elif port in [443, 8443]:
                        # HTTPS requires SSL, skip for now
                        sock.close()
                        return None
                    
                    sock.settimeout(1)
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                    if banner:
                        # Clean up banner
                        banner = ' '.join(banner.split()[:10])  # Limit to first 10 words
                        return banner[:100]  # Limit banner length
                except socket.timeout:
                    pass
                except Exception:
                    pass
            
            sock.close()
        except Exception:
            pass
        return None
    
    def scan_port_connect(self, ip, port):
        """TCP Connect scan (most reliable but detectable)."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                return True
        except:
            pass
        return False
    
    def scan_port_syn(self, ip, port):
        """TCP SYN scan (stealth scan - requires raw sockets/root)."""
        # Note: True SYN scanning requires raw sockets which need root privileges
        # This is a simulated version that uses connect but with shorter timeout
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout * 0.5)  # Shorter timeout for stealth
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                return True
        except:
            pass
        return False
    
    def scan_port_udp(self, ip, port):
        """UDP scan (slower, less reliable)."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout * 2)  # UDP needs longer timeout
            
            # Send empty UDP packet
            sock.sendto(b'', (ip, port))
            
            try:
                data, addr = sock.recvfrom(1024)
                sock.close()
                return True
            except socket.timeout:
                # No response might mean port is open (UDP is connectionless)
                sock.close()
                return 'open|filtered'
        except:
            pass
        return False
    
    def scan_port(self, ip, port):
        """Scan a single port based on scan type."""
        if self.stealth_mode and self.delay > 0:
            time.sleep(random.uniform(0, self.delay))
        
        is_open = False
        if self.scan_type == 'connect':
            is_open = self.scan_port_connect(ip, port)
        elif self.scan_type == 'syn':
            is_open = self.scan_port_syn(ip, port)
        elif self.scan_type == 'udp':
            result_udp = self.scan_port_udp(ip, port)
            if result_udp == True:
                is_open = True
            elif result_udp == 'open|filtered':
                # For UDP, open|filtered is still considered open
                is_open = True
        else:
            is_open = self.scan_port_connect(ip, port)
        
        if is_open:
            service = self.get_service_name(port)
            banner = None
            
            # Try to grab banner for common ports
            if port in [21, 22, 23, 25, 80, 110, 143, 443, 8080, 8443]:
                try:
                    banner = self.grab_banner(ip, port)
                except:
                    banner = None
            
            result = {
                'port': port,
                'state': 'open',
                'service': service,
                'banner': banner if banner else None
            }
            
            with self.lock:
                if port not in self.open_ports:
                    self.open_ports.append(port)
                    self.results.append(result)
            
            return result
        return None
    
    def scan(self, progress_callback=None):
        """Perform the port scan."""
        ip = self.resolve_target()
        if not ip:
            return {'error': f'Could not resolve {self.target}'}
        
        # Reset results
        self.open_ports = []
        self.results = []
        
        # Randomize port order if requested (stealth technique)
        ports_to_scan = self.ports.copy()
        if self.randomize_ports:
            random.shuffle(ports_to_scan)
        
        total_ports = len(ports_to_scan)
        scanned = 0
        
        try:
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                futures = {executor.submit(self.scan_port, ip, port): port 
                          for port in ports_to_scan}
                
                for future in as_completed(futures):
                    scanned += 1
                    if progress_callback:
                        progress_callback(scanned, total_ports)
                    try:
                        future.result()
                    except Exception as e:
                        pass
        except Exception as e:
            return {'error': f'Scan error: {str(e)}'}
        
        # Ensure results are properly sorted and deduplicated
        seen_ports = set()
        unique_results = []
        for result in self.results:
            if result['port'] not in seen_ports:
                seen_ports.add(result['port'])
                unique_results.append(result)
        
        self.results = sorted(unique_results, key=lambda x: x['port'])
        self.open_ports = sorted(list(seen_ports))
        
        return {
            'target': self.target,
            'ip': ip,
            'open_ports': self.open_ports,
            'results': self.results,
            'total_scanned': total_ports,
            'open_count': len(self.open_ports)
        }


# ==============================
# Scanner Worker Thread
# ==============================

class ScannerWorker(QThread):
    """Worker thread for port scanning."""
    progress = Signal(int, int)  # scanned, total
    result = Signal(dict)  # port result
    finished_signal = Signal(dict)  # final results
    error = Signal(str)
    
    def __init__(self, target, ports, scan_type, timeout, threads, 
                 stealth_mode, randomize_ports, delay):
        super().__init__()
        self.target = target
        self.ports = ports
        self.scan_type = scan_type
        self.timeout = timeout
        self.threads = threads
        self.stealth_mode = stealth_mode
        self.randomize_ports = randomize_ports
        self.delay = delay
        self.is_running = True
    
    def run(self):
        try:
            scanner = PortScannerEngine(
                self.target, self.ports, self.scan_type, self.timeout,
                self.threads, self.stealth_mode, self.randomize_ports, self.delay
            )
            
            def progress_cb(scanned, total):
                if self.is_running:
                    self.progress.emit(scanned, total)
            
            results = scanner.scan(progress_callback=progress_cb)
            
            if self.is_running:
                self.finished_signal.emit(results)
        except Exception as e:
            if self.is_running:
                self.error.emit(str(e))
    
    def stop(self):
        self.is_running = False


# ==============================
# Utility Functions
# ==============================

def parse_port_range(port_input: str):
    """Parse port range string into list of ports."""
    ports = set()
    if not port_input:
        return []
    
    for part in port_input.split(','):
        part = part.strip()
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                if 1 <= start <= end <= 65535:
                    ports.update(range(start, end + 1))
            except ValueError:
                continue
        else:
            try:
                port = int(part)
                if 1 <= port <= 65535:
                    ports.add(port)
            except ValueError:
                continue
    
    return sorted(list(ports))


# ==============================
# GUI Tool
# ==============================

class PortScanner(ToolBase):
    @property
    def name(self) -> str:
        return "Port Scanner"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.PORT_SCANNING

    def get_widget(self, main_window: QWidget) -> QWidget:
        return PortScannerView(main_window=main_window)

class PortScannerView(BaseToolView):
    def __init__(self, main_window):
        super().__init__("Port Scanner", ToolCategory.PORT_SCANNING, main_window)
        self.worker = None
        self._is_stopping = False
        self._scan_complete_added = False
        # Multi-target scanning state
        self._current_target_index = 0
        self._all_targets = []
        self._all_ports = []
        self._all_results = []
        self._build_custom_ui()
        self.update_command()
    
    def _build_custom_ui(self):
        splitter = self.findChild(QSplitter)
        control_panel = splitter.widget(0)
        control_layout = control_panel.layout()
        
        # Disconnect default copy button and connect custom handler
        try:
            self.output.copy_button.clicked.disconnect()
        except:
            pass
        self.output.copy_button.clicked.connect(self.copy_results_to_clipboard)
        
        # Port input
        port_layout = QHBoxLayout()
        port_label = QLabel("Ports:")
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("e.g. 80,443,1-1000 or common,top1000")
        self.port_input.setStyleSheet(TARGET_INPUT_STYLE)
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_input, 1)
        
        # Scan type
        scan_type_layout = QHBoxLayout()
        scan_type_label = QLabel("Scan Type:")
        self.scan_type = StyledComboBox()
        self.scan_type.addItems(['connect', 'syn', 'udp'])
        scan_type_layout.addWidget(scan_type_label)
        scan_type_layout.addWidget(self.scan_type, 1)
        
        # Advanced options
        advanced_layout = QHBoxLayout()
        self.stealth_check = QCheckBox("Stealth Mode")
        self.randomize_check = QCheckBox("Randomize Ports")
        self.banner_check = QCheckBox("Grab Banners")
        advanced_layout.addWidget(self.stealth_check)
        advanced_layout.addWidget(self.randomize_check)
        advanced_layout.addWidget(self.banner_check)
        
        # Performance settings
        perf_layout = QHBoxLayout()
        threads_label = QLabel("Threads:")
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 500)
        self.threads_spin.setValue(100)
        self.threads_spin.setSuffix(" threads")
        
        timeout_label = QLabel("Timeout:")
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 10)
        self.timeout_spin.setValue(1)
        self.timeout_spin.setSuffix(" s")
        
        delay_label = QLabel("Delay:")
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 5)
        self.delay_spin.setValue(0)
        self.delay_spin.setSuffix(" ms")
        
        perf_layout.addWidget(threads_label)
        perf_layout.addWidget(self.threads_spin)
        perf_layout.addWidget(timeout_label)
        perf_layout.addWidget(self.timeout_spin)
        perf_layout.addWidget(delay_label)
        perf_layout.addWidget(self.delay_spin)
        perf_layout.addStretch()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        insertion_index = 5
        control_layout.insertLayout(insertion_index, port_layout)
        control_layout.insertLayout(insertion_index + 1, scan_type_layout)
        control_layout.insertLayout(insertion_index + 2, advanced_layout)
        control_layout.insertLayout(insertion_index + 3, perf_layout)
        control_layout.insertWidget(insertion_index + 4, self.progress_bar)
        
        # Connect signals
        for widget in [self.port_input, self.scan_type, self.threads_spin, 
                      self.timeout_spin, self.delay_spin, self.stealth_check,
                      self.randomize_check, self.banner_check]:
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(self.update_command)
            elif isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(self.update_command)
            elif isinstance(widget, QSpinBox):
                widget.valueChanged.connect(self.update_command)
            elif isinstance(widget, QCheckBox):
                widget.stateChanged.connect(self.update_command)
    
    def _get_common_ports(self):
        """Get list of common ports."""
        return [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445,
                993, 995, 1433, 3306, 3389, 5432, 5900, 8080, 8443]
    
    def _get_top_1000_ports(self):
        """Get top 1000 most common ports."""
        # Common ports based on nmap's top ports
        return list(range(1, 1001))  # Simplified - in real implementation, use actual top 1000
    
    def _parse_port_input(self, port_input: str):
        """Parse port input including special keywords."""
        port_input = port_input.strip().lower()
        
        if port_input == 'common':
            return self._get_common_ports()
        elif port_input == 'top1000':
            return self._get_top_1000_ports()
        else:
            return parse_port_range(port_input)
    
    def update_command(self):
        try:
            target = self.target_input.get_target().strip() or "<target>"
            ports = self.port_input.text().strip() or "1-1000"
            scan_type = self.scan_type.currentText()
            threads = self.threads_spin.value()
            timeout = self.timeout_spin.value()

            # Count targets for display
            targets_info = parse_targets(target)[0]
            target_count = len(targets_info) if targets_info else 1

            cmd = f"Custom Port Scanner: {target_count} target(s) | Ports: {ports} | Type: {scan_type} | Threads: {threads} | Timeout: {timeout}s"
            self.command_input.setText(cmd)
        except AttributeError:
            pass
    
    def run_scan(self):
        self.output.clear()
        self._is_stopping = False
        self._scan_complete_added = False

        target_str = self.target_input.get_target()
        targets = parse_targets(target_str)[0]
        if not targets:
            return QMessageBox.warning(self, "Warning", "No valid targets specified.")

        port_input = self.port_input.text().strip()
        if not port_input:
            port_input = "1-1000"

        ports = self._parse_port_input(port_input)
        if not ports:
            return QMessageBox.warning(self, "Warning", "No valid ports specified.")

        if len(ports) > 10000:
            reply = QMessageBox.question(
                self, "Large Scan",
                f"Scanning {len(ports)} ports may take a long time. Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        try:
            # Create directories for the first target (for logs)
            base_dir = create_target_dirs(targets[0])
            logs_dir = os.path.join(base_dir, "Logs")
            os.makedirs(logs_dir, exist_ok=True)

            self._info(f"Starting custom port scan on {len(targets)} target(s)")
            self._info(f"Scanning {len(ports)} ports using {self.scan_type.currentText()} scan")
            self._info(f"Threads: {self.threads_spin.value()}, Timeout: {self.timeout_spin.value()}s")
            self.output.appendPlainText("")

            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(len(ports) * len(targets))
            self.progress_bar.setValue(0)

            # Scan targets sequentially
            self._current_target_index = 0
            self._all_targets = targets
            self._all_ports = ports
            self._all_results = []

            self._scan_next_target()

        except Exception as e:
            self._error(f"Failed to start scan: {str(e)}")

    def _scan_next_target(self):
        """Scan the next target in the list."""
        if self._current_target_index >= len(self._all_targets) or self._is_stopping:
            # All targets scanned, show final results
            self._show_final_results()
            return

        current_target = self._all_targets[self._current_target_index]
        self._info(f"Scanning target: {current_target}")

        try:
            self.worker = ScannerWorker(
                current_target,
                self._all_ports,
                self.scan_type.currentText(),
                self.timeout_spin.value(),
                self.threads_spin.value(),
                self.stealth_check.isChecked(),
                self.randomize_check.isChecked(),
                self.delay_spin.value() / 1000.0  # Convert ms to seconds
            )

            self.worker.progress.connect(self._on_progress)
            self.worker.result.connect(self._on_port_result)
            self.worker.finished_signal.connect(self._on_target_finished)
            self.worker.error.connect(self._error)

            self.worker.start()

        except Exception as e:
            self._error(f"Failed to scan {current_target}: {str(e)}")
            self._current_target_index += 1
            self._scan_next_target()
    
    def _on_progress(self, scanned, total):
        """Update progress bar."""
        # Account for multiple targets
        base_progress = self._current_target_index * len(self._all_ports)
        self.progress_bar.setValue(base_progress + scanned)
    
    def _on_port_result(self, result):
        """Handle individual port result."""
        pass  # Results are handled in finished signal

    def _on_target_finished(self, results):
        """Handle completion of scanning one target."""
        if 'error' in results:
            self._error(f"Error scanning {results.get('target', 'unknown')}: {results['error']}")
        else:
            # Store results for this target
            self._all_results.append(results)

        # Move to next target
        self._current_target_index += 1
        self._scan_next_target()

    def _show_final_results(self):
        """Show final results for all scanned targets."""
        self.progress_bar.setVisible(False)
        self._on_scan_completed()

        if self._is_stopping:
            return

        # Display results for all targets
        self._section("Scan Results")

        total_targets = len(self._all_results)
        total_ports_scanned = 0
        total_open_ports = 0

        for i, results in enumerate(self._all_results):
            if 'error' in results:
                continue

            # Add separator between targets (but not before first)
            if i > 0:
                self.output.appendPlainText("")

            target = results['target']
            ip = results['ip']
            ports_scanned = results['total_scanned']
            open_count = results['open_count']

            total_ports_scanned += ports_scanned
            total_open_ports += open_count

            self.output.appendPlainText(f"Target: {target} ({ip})")
            self.output.appendPlainText(f"Total Ports Scanned: {ports_scanned}")
            self.output.appendPlainText(f"Open Ports Found: {open_count}")

            if results['open_ports'] and results['results']:
                self.output.appendPlainText("")
                self.output.appendPlainText("OPEN PORTS:")
                self.output.appendPlainText("-" * 80)
                self.output.appendPlainText(f"{'Port':<10} {'State':<10} {'Service':<20} {'Banner':<40}")
                self.output.appendPlainText("-" * 80)

                for result in results['results']:
                    port = result['port']
                    state = result['state']
                    service = result.get('service', 'Unknown')
                    banner = result.get('banner', None)

                    # Format banner display
                    if banner:
                        banner_str = banner.strip() if isinstance(banner, str) else str(banner)
                        if len(banner_str) > 40:
                            banner_str = banner_str[:37] + "..."
                    else:
                        banner_str = 'N/A'

                    self.output.appendPlainText(f"{port:<10} {state:<10} {service:<20} {banner_str:<40}")

                self.output.appendPlainText("-" * 80)

        # Summary
        self.output.appendPlainText("")
        self.output.appendPlainText(f"Summary: Scanned {total_targets} targets, {total_ports_scanned} total ports, {total_open_ports} open ports found")

        # Save results for each target
        try:
            for results in self._all_results:
                if 'error' not in results:
                    base_dir = create_target_dirs(results['target'])
                    logs_dir = os.path.join(base_dir, "Logs")
                    os.makedirs(logs_dir, exist_ok=True)

                    log_file = os.path.join(logs_dir, "portscan.txt")
                    with open(log_file, 'w') as f:
                        f.write(f"Custom Port Scan Results\n")
                        f.write(f"Target: {results['target']} ({results['ip']})\n")
                        f.write(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"Total Ports Scanned: {results['total_scanned']}\n")
                        f.write(f"Open Ports: {results['open_count']}\n\n")
                        f.write("OPEN PORTS:\n")
                        f.write("-" * 80 + "\n")
                        for result in results['results']:
                            f.write(f"Port {result['port']}: {result['state']} - {result['service']}")
                            if result.get('banner'):
                                f.write(f" - {result['banner']}")
                            f.write("\n")

                    self._info(f"Results for {results['target']} saved to: {log_file}")
        except Exception as e:
            self._error(f"Failed to save results: {str(e)}")

        if not self._scan_complete_added:
            self._section("Scan Complete")
            self._scan_complete_added = True
    
    def _on_scan_finished(self, results):
        """Handle scan completion."""
        self.progress_bar.setVisible(False)
        self._on_scan_completed()
        
        if self._is_stopping:
            return
        
        if 'error' in results:
            self._error(results['error'])
            return
        
        # Display results
        self.output.appendPlainText("")
        self._section("Scan Results")
        self.output.appendPlainText(f"Target: {results['target']} ({results['ip']})")
        self.output.appendPlainText(f"Total Ports Scanned: {results['total_scanned']}")
        self.output.appendPlainText(f"Open Ports Found: {results['open_count']}")
        self.output.appendPlainText("")
        
        if results['open_ports']:
            self.output.appendPlainText("OPEN PORTS:")
            self.output.appendPlainText("-" * 80)
            self.output.appendPlainText(f"{'Port':<10} {'State':<10} {'Service':<20} {'Banner':<40}")
            self.output.appendPlainText("-" * 80)
            
            for result in results['results']:
                port = result['port']
                state = result['state']
                service = result.get('service', 'Unknown')
                banner = result.get('banner', None)
                
                # Format banner display
                if banner:
                    banner_str = banner.strip() if isinstance(banner, str) else str(banner)
                    if len(banner_str) > 40:
                        banner_str = banner_str[:37] + "..."
                else:
                    banner_str = 'N/A'
                
                self.output.appendPlainText(f"{port:<10} {state:<10} {service:<20} {banner_str:<40}")
            
            self.output.appendPlainText("-" * 80)
            
            # Save results to file
            try:
                base_dir = create_target_dirs(results['target'])
                logs_dir = os.path.join(base_dir, "Logs")
                os.makedirs(logs_dir, exist_ok=True)
                
                log_file = os.path.join(logs_dir, "portscan.txt")
                with open(log_file, 'w') as f:
                    f.write(f"Custom Port Scan Results\n")
                    f.write(f"Target: {results['target']} ({results['ip']})\n")
                    f.write(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Total Ports Scanned: {results['total_scanned']}\n")
                    f.write(f"Open Ports: {results['open_count']}\n\n")
                    f.write("OPEN PORTS:\n")
                    f.write("-" * 80 + "\n")
                    for result in results['results']:
                        f.write(f"Port {result['port']}: {result['state']} - {result['service']}")
                        if result.get('banner'):
                            f.write(f" - {result['banner']}")
                        f.write("\n")
                
                self._info(f"Results saved to: {log_file}")
            except Exception as e:
                self._error(f"Failed to save results: {str(e)}")
        else:
            self.output.appendPlainText("No open ports found.")
        
        if not self._scan_complete_added:
            self._section("Scan Complete")
            self._scan_complete_added = True
    
    def stop_scan(self):
        if self.worker and self.worker.isRunning():
            self._is_stopping = True
            self.worker.stop()
            self.worker.terminate()
            self.worker.wait()
            self._info("Scan stopped.")
        self._on_scan_completed()
        self.progress_bar.setVisible(False)

        # Reset multi-target scanning state
        self._current_target_index = 0
        self._all_targets = []
        self._all_results = []
    
    def copy_results_to_clipboard(self):
        """Copy scan results to clipboard."""
        results_text = self.output.toPlainText()
        if results_text.strip():
            QApplication.clipboard().setText(results_text)
            self._notify("Results copied to clipboard.")
        else:
            self._notify("No results to copy.")

