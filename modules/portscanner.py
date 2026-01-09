# =============================================================================
# modules/portscanner.py
#
# Custom Port Scanner - Stealth & Features
# =============================================================================

import os
import socket
import random
import time
import threading
import platform
import subprocess
import ssl
import http.client
import html
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Qt imports moved to class level to follow Golden Rules (no Qt imports in module level)

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QProgressBar

from ui.worker import ToolExecutionMixin
from modules.bases import ToolBase, ToolCategory
from core.tgtinput import TargetInput, parse_targets, parse_port_range
from core.fileops import create_target_dirs, get_cache_key, get_cached_result, set_cached_result
from ui.styles import (
    StyledComboBox, StyledCheckBox, StyledSpinBox, StyledLabel, StyledLineEdit,
    HeaderLabel, CommandDisplay, OutputView, RunButton, StopButton,
    StyledGroupBox, SafeStop, OutputHelper, ToolSplitter, StyledToolView,
    COLOR_TEXT_PRIMARY
)


# ==============================
# Port Scanner Tool
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
                 stealth_mode=False, randomize_ports=False, delay=0,
                 check_os=False, check_waf=False, check_tls=False, grab_banners=False):
        self.target = target
        self.ports = ports
        self.scan_type = scan_type
        self.timeout = timeout
        self.threads = threads
        self.stealth_mode = stealth_mode
        self.randomize_ports = randomize_ports
        self.delay = delay
        self.check_os = check_os
        self.check_waf = check_waf
        self.check_tls = check_tls
        self.grab_banners = grab_banners
        
        self.open_ports = []
        self.results = []
        self.os_info = None
        self.lock = threading.Lock()
        
    def resolve_target(self):
        """Resolve hostname to IP address with caching."""
        if not self.target:
            return None

        # Check cache first
        cache_key = get_cache_key(f"dns_{self.target}")
        cached = get_cached_result(cache_key, max_age_hours=1)  # Cache for 1 hour
        if cached:
            return cached.get('ip')

        # Perform DNS resolution
        try:
            ip = socket.gethostbyname(self.target)
            # Cache the result
            set_cached_result(cache_key, {'ip': ip})
            return ip
        except socket.gaierror:
            # Cache negative result too
            set_cached_result(cache_key, {'ip': None})
            return None
    
    def get_service_name(self, port):
        """Get service name for common ports."""
        return self.SERVICE_PORTS.get(port, 'Unknown')

    def detect_os(self, ip):
        """Detect OS based on Ping TTL with caching."""
        if not ip:
            return "Invalid IP"

        # Check cache first
        cache_key = get_cache_key(f"os_detect_{ip}")
        cached = get_cached_result(cache_key, max_age_hours=24)  # Cache for 24 hours
        if cached:
            return cached.get('os', "Unknown")

        # Perform OS detection
        try:
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            # Send 1 ping - reduce timeout for better performance
            cmd = ['ping', param, '1', '-W', '2', ip] if platform.system().lower() != 'windows' else ['ping', param, '1', ip]

            # Run ping command with timeout
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                stdout, stderr = proc.communicate(timeout=5)  # 5 second timeout
                output = stdout.decode('utf-8', errors='ignore').lower()
            except subprocess.TimeoutExpired:
                proc.kill()
                return "Detection Timeout"

            if "ttl=" in output:
                # Extract TTL approximately
                # Windows usually 128, Linux 64, Solaris 255
                val = 0
                for part in output.split():
                    if part.startswith("ttl="):
                        val = int(part.split("=")[1])
                        break

                if val:
                    os_result = ""
                    if val <= 64:
                        os_result = f"Linux/Unix (TTL={val})"
                    elif val <= 128:
                        os_result = f"Windows (TTL={val})"
                    else:
                        os_result = f"Solaris/AIX (TTL={val})"

                    # Cache the result
                    set_cached_result(cache_key, {'os': os_result})
                    return os_result

            os_result = "Unknown (No TTL)"
            set_cached_result(cache_key, {'os': os_result})
            return os_result

        except Exception as e:
            os_result = "Detection Failed"
            set_cached_result(cache_key, {'os': os_result})
            return os_result

    def get_tls_info(self, ip, port):
        """Get TLS/SSL Certificate Information."""
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((ip, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=self.target) as ssock:
                    cert = ssock.getpeercert()
                    if not cert:
                        return "No Cert"
                    
                    # Extract basic info
                    subject = dict(x[0] for x in cert['subject'])
                    issuer = dict(x[0] for x in cert['issuer'])
                    
                    cn = subject.get('commonName', 'Unknown')
                    org = subject.get('organizationName', '')
                    issuer_cn = issuer.get('commonName', 'Unknown')
                    
                    info = f"CN={cn}"
                    if org: info += f", Org={org}"
                    info += f" | Issuer={issuer_cn}"
                    
                    return info
        except Exception:
            return None

    def detect_waf(self, ip, port):
        """Smart WAF Fingerprinting with stealth features."""
        # WAF Signatures
        signatures = {
            "Cloudflare": ["cf-ray", "cf-cache-status", "cloudflare", "__cfduid"],
            "Akamai": ["akamai", "akamai-edge", "x-akamai-request-id"],
            "Imperva/Incapsula": ["incapsula", "x-iinfo", "x-cdn", "incap_ses"],
            "AWS WAF/CloudFront": ["x-amzn-requestid", "x-amz-cf-id", "x-amz-cf-pop"],
            "F5 BIG-IP": ["bigip", "x-f5-traffic", "bigipserver"],
            "Sucuri": ["sucuri", "x-sucuri-id"],
            "ModSecurity": ["mod_security", "modsec", "x-modsec"],
            "Barracuda": ["barracuda", "x-barracuda"],
            "Fortinet": ["fortigate", "fortiweb"],
            "Wordfence": ["wordfence"],
            "DDoS-Guard": ["ddos-guard"],
        }
        
        # Random User-Agents for stealth
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        ]
        
        # Generate fake IP for X-Forwarded-For
        def fake_ip():
            return f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
        
        # Payloads that trigger WAF blocks
        payloads = [
            "/?id=<script>alert(1)</script>",
            "/?q=<svg/onload=alert(1)>",
            "/?cmd=cat+/etc/passwd",
            "/?id=1'+OR+'1'='1",
        ]
        
        try:
            is_https = port in [443, 8443, 10443, 4443]
            detected = set()
            
            for payload in payloads[:2]:  # Use first 2 payloads for speed
                try:
                    headers = {
                        "Host": self.target,
                        "User-Agent": random.choice(user_agents),
                        "Accept": "text/html,*/*",
                        "X-Forwarded-For": fake_ip(),
                        "X-Real-IP": fake_ip(),
                        "Connection": "close",
                    }
                    
                    if is_https:
                        context = ssl.create_default_context()
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        conn = http.client.HTTPSConnection(ip, port, timeout=self.timeout, context=context)
                    else:
                        conn = http.client.HTTPConnection(ip, port, timeout=self.timeout)
                    
                    conn.request("GET", payload, headers=headers)
                    resp = conn.getresponse()
                    body = resp.read().decode(errors="ignore").lower()
                    resp_headers = {k.lower(): v.lower() for k, v in resp.getheaders()}
                    conn.close()
                    
                    # 1. Check headers for signatures
                    for waf_name, patterns in signatures.items():
                        for pat in patterns:
                            for k, v in resp_headers.items():
                                if pat in k or pat in v:
                                    detected.add(waf_name)
                                    break
                    
                    # 2. Check cookies
                    cookies = resp_headers.get("set-cookie", "")
                    if "incap_ses" in cookies or "visid_incap" in cookies:
                        detected.add("Imperva/Incapsula")
                    if "__cfduid" in cookies or "cf_clearance" in cookies:
                        detected.add("Cloudflare")
                    
                    # 3. Check body for WAF indicators
                    body_patterns = {
                        "cloudflare": "Cloudflare",
                        "cf-ray": "Cloudflare",
                        "incapsula": "Imperva/Incapsula",
                        "sucuri": "Sucuri",
                        "wordfence": "Wordfence",
                        "access denied": "Generic WAF",
                        "blocked": "Generic WAF",
                        "web application firewall": "Generic WAF",
                    }
                    for pat, waf in body_patterns.items():
                        if pat in body:
                            detected.add(waf)
                    
                    # 4. Status code heuristic
                    if resp.status in (403, 406, 429, 503) and not detected:
                        detected.add("Possible WAF (Block)")
                    
                    # If we found a specific WAF, return early
                    if any(w for w in detected if "Possible" not in w and "Generic" not in w):
                        break
                        
                except Exception:
                    continue
            
            if detected:
                # Prefer specific WAFs over generic
                specific = [w for w in detected if "Possible" not in w and "Generic" not in w]
                return specific[0] if specific else list(detected)[0]
            return None
            
        except Exception:
            return None

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
            tls_info = None
            waf_info = None

            # Common web ports for broader checking
            web_ports = [80, 81, 443, 3000, 5000, 8000, 8008, 8080, 8081, 8443, 8888, 9000, 9090, 10443]
            common_banner_ports = [21, 22, 23, 25, 110, 143] + web_ports
            
            # Try to grab banner for common ports (only if enabled)
            if self.grab_banners and port in common_banner_ports:
                try:
                    res_banner = self.grab_banner(ip, port)
                    if res_banner: banner = res_banner
                except:
                    banner = None

            # TLS Check
            if self.check_tls and port in [443, 4443, 8443, 465, 993, 10443]:
                tls_info = self.get_tls_info(ip, port)

            # WAF Check (HTTP/HTTPS ports)
            if self.check_waf and port in web_ports:
                waf_info = self.detect_waf(ip, port)
            
            result = {
                'port': port,
                'state': 'open',
                'service': service,
                'banner': banner if banner else None,
                'tls_info': tls_info,
                'waf_info': waf_info
            }
            
            with self.lock:
                if port not in self.open_ports:
                    self.open_ports.append(port)
                    self.results.append(result)
            
            return result
        return None
    
    def scan(self, progress_callback=None, should_stop=None):
        """Perform the port scan."""
        ip = self.resolve_target()
        if not ip:
            return {'error': f'Could not resolve {self.target}'}
        
        # Reset results
        self.open_ports = []
        self.results = []
        self.os_info = None
        
        # Perform OS Detection if enabled (one-off)
        if self.check_os:
            self.os_info = self.detect_os(ip)
        
        # Randomize port order if requested (stealth technique)
        ports_to_scan = self.ports.copy()
        if self.randomize_ports:
            random.shuffle(ports_to_scan)
        
        total_ports = len(ports_to_scan)
        scanned = 0
        
        try:
            # Limit threads to prevent system overload (max 200 threads)
            max_threads = min(self.threads, 200)
            with ThreadPoolExecutor(max_workers=max_threads, thread_name_prefix="portscan") as executor:
                futures = {executor.submit(self.scan_port, ip, port): port
                          for port in ports_to_scan}

                # Process results as they complete for better memory efficiency
                completed_count = 0
                for future in as_completed(futures):
                    # Check for stop signal
                    if should_stop and should_stop():
                        # Cancel remaining futures
                        for f in futures:
                            if not f.done():
                                f.cancel()
                        break

                    completed_count += 1
                    if progress_callback and completed_count % 10 == 0:  # Update progress every 10 ports
                        progress_callback(completed_count, total_ports)
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
            'os_info': self.os_info,
            'open_ports': self.open_ports,
            'results': self.results,
            'total_scanned': total_ports,
            'open_count': len(self.open_ports)
        }


# ==============================
# Scanner Worker Thread
# ==============================

# ScannerWorker moved inside PortScannerView to follow Golden Rules


# ==============================
# GUI Tool
# ==============================

class PortScanner(ToolBase):
    """Custom Port Scanner Tool"""

    name = "Port Scanner"
    category = ToolCategory.PORT_SCANNING

    @property
    def icon(self) -> str:
        return "🔌"

    def get_widget(self, main_window):
        return PortScannerView(main_window=main_window)

class PortScannerView(StyledToolView, ToolExecutionMixin, SafeStop, OutputHelper):
    """Port Scanner tool view with custom scanning engine."""
    
    tool_name = "Port Scanner"
    tool_category = "PORT_SCANNING"

    class ScannerWorker(QThread):
        """Worker thread for port scanning."""
        from PySide6.QtCore import Signal

        progress = Signal(int, int)  # scanned, total
        result = Signal(dict)  # port result
        finished_signal = Signal(dict)  # final results
        error = Signal(str)

        def __init__(self, target, ports, scan_type, timeout, threads,
                     stealth_mode, randomize_ports, delay,
                     check_os, check_waf, check_tls, grab_banners):
            super().__init__()
            self.target = target
            self.ports = ports
            self.scan_type = scan_type
            self.timeout = timeout
            self.threads = threads
            self.stealth_mode = stealth_mode
            self.randomize_ports = randomize_ports
            self.delay = delay
            self.check_os = check_os
            self.check_waf = check_waf
            self.check_tls = check_tls
            self.grab_banners = grab_banners
            self.is_running = True

        def run(self):
            try:
                scanner = PortScannerEngine(
                    self.target, self.ports, self.scan_type, self.timeout,
                    self.threads, self.stealth_mode, self.randomize_ports, self.delay,
                    self.check_os, self.check_waf, self.check_tls, self.grab_banners
                )

                def progress_cb(scanned, total):
                    if self.is_running:
                        self.progress.emit(scanned, total)

                results = scanner.scan(progress_callback=progress_cb, should_stop=lambda: not self.is_running)

                if self.is_running:
                    self.finished_signal.emit(results)
            except Exception as e:
                if self.is_running:
                    self.error.emit(str(e))

        def stop(self):
            self.is_running = False

    def __init__(self, main_window):
        super().__init__()
        self.init_safe_stop()
        self.main_window = main_window
        self.worker = None
        self._is_stopping = False
        self._scan_complete_added = False
        # Multi-target scanning state
        self._current_target_index = 0
        self._all_targets = []
        self._all_ports = []
        self._all_results = []
        self._build_ui()
        self.update_command()
    
    def _build_ui(self):
        """Build the complete UI."""
        # setStyleSheet handled by StyledToolView
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = ToolSplitter()
        main_layout.addWidget(splitter)
        
        # ==================== CONTROL PANEL ====================
        control_panel = QWidget()
        # Removed legacy style
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        # Header
        header = HeaderLabel(self.tool_category, self.tool_name)
        control_layout.addWidget(header)
        
        # Target input row
        target_group = StyledGroupBox("🎯 Target")
        target_layout = QHBoxLayout(target_group)
        self.target_input = TargetInput()
        target_layout.addWidget(self.target_input)
        control_layout.addWidget(target_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.run_button = RunButton("START SCAN")
        self.run_button.clicked.connect(self.run_scan)
        btn_layout.addWidget(self.run_button)
        
        self.stop_button = StopButton()
        self.stop_button.clicked.connect(self.stop_scan)
        btn_layout.addWidget(self.stop_button)
        control_layout.addLayout(btn_layout)
        
        # Command display
        self.command_display = CommandDisplay()
        self.command_input = self.command_display.input
        control_layout.addWidget(self.command_display)
        
        # Port input
        target_group = StyledGroupBox("⚙️ Config")
        config_layout = QVBoxLayout(target_group)
        
        port_layout = QHBoxLayout()
        port_label = StyledLabel("Ports:")
        self.port_input = StyledLineEdit()
        self.port_input.setPlaceholderText("e.g. 80,443,1-1000 or common,top1000")
        self.port_input.textChanged.connect(self.update_command)
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_input, 1)
        config_layout.addLayout(port_layout)
        
        # Scan type
        scan_type_layout = QHBoxLayout()
        scan_type_label = StyledLabel("Scan Type:")
        self.scan_type = StyledComboBox()
        self.scan_type.addItems(['connect', 'syn', 'udp'])
        self.scan_type.currentTextChanged.connect(self.update_command)
        scan_type_layout.addWidget(scan_type_label)
        scan_type_layout.addWidget(self.scan_type, 1)
        config_layout.addLayout(scan_type_layout)

        control_layout.addWidget(target_group)
        
        # Advanced options group
        advanced_group = StyledGroupBox("🔧 Advanced")
        advanced_layout = QVBoxLayout(advanced_group)
        
        row1 = QHBoxLayout()
        self.stealth_check = StyledCheckBox("Stealth Mode")
        self.stealth_check.stateChanged.connect(self.update_command)
        self.randomize_check = StyledCheckBox("Randomize Order")
        self.randomize_check.stateChanged.connect(self.update_command)
        self.banner_check = StyledCheckBox("Grab Banners")
        self.banner_check.stateChanged.connect(self.update_command)
        row1.addWidget(self.stealth_check)
        row1.addWidget(self.randomize_check)
        row1.addWidget(self.banner_check)
        
        row2 = QHBoxLayout()
        self.os_check = StyledCheckBox("OS Detect")
        self.os_check.setToolTip("Detect OS via Ping TTL")
        self.os_check.stateChanged.connect(self.update_command)
        self.waf_check = StyledCheckBox("WAF Detect")
        self.waf_check.setToolTip("Fingerprint WAF (Cloudflare, Akamai, etc.)")
        self.waf_check.stateChanged.connect(self.update_command)
        self.tls_check = StyledCheckBox("TLS Info")
        self.tls_check.setToolTip("Extract SSL Certificate details")
        self.tls_check.stateChanged.connect(self.update_command)
        row2.addWidget(self.os_check)
        row2.addWidget(self.waf_check)
        row2.addWidget(self.tls_check)
        
        advanced_layout.addLayout(row1)
        advanced_layout.addLayout(row2)
        control_layout.addWidget(advanced_group)
        
        # Performance settings
        perf_layout = QHBoxLayout()
        threads_label = StyledLabel("Threads:")
        self.threads_spin = StyledSpinBox()
        self.threads_spin.setRange(1, 500)
        self.threads_spin.setValue(100)
        self.threads_spin.valueChanged.connect(self.update_command)
        
        timeout_label = StyledLabel("Timeout:")
        self.timeout_spin = StyledSpinBox()
        self.timeout_spin.setRange(1, 10)
        self.timeout_spin.setValue(1)
        self.timeout_spin.valueChanged.connect(self.update_command)
        
        delay_label = StyledLabel("Delay:")
        self.delay_spin = StyledSpinBox()
        self.delay_spin.setRange(0, 5)
        self.delay_spin.setValue(0)
        self.delay_spin.valueChanged.connect(self.update_command)
        
        perf_layout.addWidget(threads_label)
        perf_layout.addWidget(self.threads_spin)
        perf_layout.addWidget(timeout_label)
        perf_layout.addWidget(self.timeout_spin)
        perf_layout.addWidget(delay_label)
        perf_layout.addWidget(self.delay_spin)
        perf_layout.addStretch()
        control_layout.addLayout(perf_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #2A2A3E;
                border: 1px solid #3d3d5c;
                border-radius: 4px;
                text-align: center;
                color: {COLOR_TEXT_PRIMARY};
            }}
            QProgressBar::chunk {{
                background-color: #f97316;
                border-radius: 3px;
            }}
        """)
        control_layout.addWidget(self.progress_bar)
        control_layout.addStretch()
        
        # ==================== OUTPUT AREA ====================
        output_container = QWidget()
        output_layout = QVBoxLayout(output_container)
        output_layout.setContentsMargins(0, 0, 0, 0)
        
        self.output = OutputView(self.main_window)
        output_layout.addWidget(self.output)
        
        # Add to splitter
        splitter.addWidget(control_panel)
        splitter.addWidget(output_container)
        splitter.setSizes([450, 450])

        # Initialize progress tracking
        self.init_progress_tracking()
     
    
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
        if not port_input:
             return self._get_top_1000_ports()
        
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
            
            # Build features string
            features = []
            if self.os_check.isChecked(): features.append("OS")
            if self.waf_check.isChecked(): features.append("WAF")
            if self.tls_check.isChecked(): features.append("TLS")
            feat_str = f" | Features: {','.join(features)}" if features else ""

            cmd = f"Custom Port Scanner: {target_count} target(s) | Ports: {ports} | Type: {scan_type} | Threads: {threads} | Timeout: {timeout}s{feat_str}"
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
            self._notify("No valid targets specified.")
            return

        port_input = self.port_input.text().strip()
        ports = self._parse_port_input(port_input)
        
        # If WAF detection is enabled, ensure essential web ports are included
        if self.waf_check.isChecked():
            waf_ports = [80, 443, 8080, 8443, 3000, 5000, 8000]
            for wp in waf_ports:
                if wp not in ports:
                    ports.append(wp)
            ports = sorted(list(set(ports)))
        
        if not ports:
            self._notify("No valid ports specified.")
            return

        if len(ports) > 10000:
            from PySide6.QtWidgets import QMessageBox
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
            
            if self.os_check.isChecked() or self.waf_check.isChecked() or self.tls_check.isChecked():
                self._info("Advanced Features Enabled: " + 
                          ", ".join(filter(None, [
                              "OS Detect" if self.os_check.isChecked() else "",
                              "WAF Detect" if self.waf_check.isChecked() else "",
                              "TLS Info" if self.tls_check.isChecked() else ""
                          ])))

            self._raw("<br>")

            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(len(ports) * len(targets))
            self.progress_bar.setValue(0)

            # Scan targets sequentially
            self._current_target_index = 0
            self._all_targets = targets
            self._all_ports = ports
            self._all_results = []
            
            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)

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
                # Note: delay division by 1000 because thread used sec but here it might be ms? 
                # Original code: self.delay_spin.value() / 1000.0 if not explicit.
                # But UI says "Delay: x", assumes seconds in other tools, but usually delay between ports is small.
                # Checked original: self.delay_spin.value() / 1000.0.
                1.0 if not self.timeout_spin else self.timeout_spin.value(),
                100 if not self.threads_spin else self.threads_spin.value(),
                self.stealth_check.isChecked(),
                self.randomize_check.isChecked(),
                self.delay_spin.value() / 1000.0,
                self.os_check.isChecked(),
                self.waf_check.isChecked(),
                self.tls_check.isChecked(),
                self.banner_check.isChecked()
            )

            self.worker.progress.connect(self._on_progress)
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
        total_targets = len(self._all_targets)
        if total_targets > 1:
            base_progress = self._current_target_index * len(self._all_ports)
            total_progress = total_targets * len(self._all_ports)
            current_progress = base_progress + scanned
            self.update_progress(current_progress, total_progress,
                               f"Target {self._current_target_index + 1}/{total_targets}")
        else:
            self.update_progress(scanned, total, "Scanning ports")

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
        self._scan_complete() # Reset buttons via SafeStop helper if available or manual

        if self._is_stopping:
            return

        # Display results for all targets
        self._section("Scan Results")
        
        output_lines = []

        total_targets = len(self._all_results)
        total_ports_scanned = 0
        total_open_ports = 0

        for i, results in enumerate(self._all_results):
            if 'error' in results:
                continue

            # Add separator between targets (but not before first)
            if i > 0:
                output_lines.append("="*50)

            target = results['target']
            ip = results['ip']
            ports_scanned = results['total_scanned']
            open_count = results['open_count']
            os_info = results.get('os_info')

            total_ports_scanned += ports_scanned
            total_open_ports += open_count

            header = f"Target: {target} ({ip})"
            if os_info:
                header += f" | OS Guess: {os_info}"
            output_lines.append(header)
            
            output_lines.append(f"Total Ports Scanned: {ports_scanned}")
            output_lines.append(f"Open Ports Found: {open_count}")

            if results['open_ports'] and results['results']:
                output_lines.append("")
                output_lines.append("OPEN PORTS:")
                output_lines.append("-" * 100)
                output_lines.append(f"{'Port':<8} {'State':<10} {'Service':<15} {'Banner/TLS':<65}")
                output_lines.append("-" * 100)

                for result in results['results']:
                    port = result['port']
                    state = result['state']
                    service = result.get('service', 'Unknown')
                    
                    # Construct info string (Banner + TLS only)
                    extras = []
                    banner = result.get('banner')
                    if banner:
                        # Truncate banner if too long
                        banner_display = banner[:60] + "..." if len(banner) > 60 else banner
                        extras.append(f"Banner: {banner_display}")
                    
                    tls = result.get('tls_info')
                    if tls:
                        tls_display = tls[:50] + "..." if len(tls) > 50 else tls
                        extras.append(f"TLS: {tls_display}")
                    
                    info_str = " | ".join(extras) if extras else "N/A"
                    
                    # Truncate if extremely long
                    if len(info_str) > 65:
                        info_str = info_str[:62] + "..."

                    output_lines.append(f"{port:<8} {state:<10} {service:<15} {info_str:<65}")
                    
                    # Show WAF on separate line if detected
                    waf = result.get('waf_info')
                    if waf:
                        output_lines.append(f"         └── 🛡️ WAF Detected: {waf}")

                output_lines.append("-" * 100)

        # Summary
        output_lines.append("")
        output_lines.append(f"Summary: Scanned {total_targets} targets, {total_ports_scanned} total ports, {total_open_ports} open ports found")

        # Output to view
        if output_lines:
             self._raw('<pre>' + html.escape('\n'.join(output_lines)) + '</pre>')

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
                        if results.get('os_info'):
                            f.write(f"OS Guess: {results['os_info']}\n")
                        f.write(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"Total Ports Scanned: {results['total_scanned']}\n")
                        f.write(f"Open Ports: {results['open_count']}\n\n")
                        f.write("OPEN PORTS:\n")
                        f.write("-" * 80 + "\n")
                        for result in results['results']:
                            line = f"Port {result['port']}: {result['state']} - {result['service']}"
                            if result.get('banner'):
                                line += f" | Banner: {result['banner'][:60]}"
                            if result.get('tls_info'):
                                line += f" | TLS: {result['tls_info'][:50]}"
                            f.write(line + "\n")
                            # WAF on separate line
                            if result.get('waf_info'):
                                f.write(f"    └── WAF Detected: {result['waf_info']}\n")

                    self._info(f"Results for {results['target']} saved to: {log_file}")
        except Exception as e:
            self._error(f"Failed to save results: {str(e)}")

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
        
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self._scan_complete() # Reset via SafeStop
        self.progress_bar.setVisible(False)

        # Reset multi-target scanning state
        self._current_target_index = 0
        self._all_targets = []
        self._all_results = []
    
    def _scan_complete(self):
        # Override if needed or just use default SafeStop method if implemented
        # SafeStop usually implements stop_scan but here we override it.
        # It's better to just ensure UI state is reset.
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.worker = None
        if self.main_window:
            self.main_window.active_process = None
