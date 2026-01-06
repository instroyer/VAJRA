# =============================================================================
# modules/wafw00f.py
#
# WAFW00F - Web Application Firewall Detection Tool
# =============================================================================

import os
import re
import random
import socket
import ssl
import http.client
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
)
from PySide6.QtCore import Qt, QThread, Signal

from modules.bases import ToolBase, ToolCategory
from core.fileops import create_target_dirs
from ui.styles import (
    RunButton, StopButton, CopyButton,
    StyledLineEdit, StyledSpinBox, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, CommandDisplay, OutputView,
    StyledGroupBox, ToolSplitter,
    SafeStop, OutputHelper,
    TOOL_VIEW_STYLE, COLOR_BACKGROUND_SECONDARY
)


# =============================================================================
# Smart WAF Detection Engine (Used by PortScanner and standalone)
# =============================================================================

def _random_user_agent():
    """Return a random, plausible User-Agent string."""
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"
    ]
    return random.choice(agents)

def _random_ip():
    """Generate a random public IPv4 address for X-Forwarded-For."""
    while True:
        ip = "{}.{}.{}.{}".format(*[random.randint(1, 254) for _ in range(4)])
        if not (ip.startswith('10.') or ip.startswith('192.168.') or ip.startswith('172.')):
            return ip


class SmartWAFDetector:
    """Smart WAF detection engine with stealth features."""
    
    SIGNATURES = {
        "Cloudflare": ["cf-ray", "cf-cache-status", "server: cloudflare", "__cfduid", "cf_clearance"],
        "Akamai": ["akamai", "akamai-edge", "x-akamai-request-id", "akamaighost"],
        "Imperva/Incapsula": ["incapsula", "x-iinfo", "x-cdn", "incap_ses", "visid_incap"],
        "AWS WAF/CloudFront": ["x-amzn-requestid", "x-amz-cf-id", "x-amz-cf-pop", "awselb"],
        "F5 BIG-IP": ["bigip", "x-f5-traffic", "bigipserver", "x-wa-info"],
        "Sucuri": ["sucuri", "x-sucuri-id", "x-sucuri-cache"],
        "ModSecurity": ["mod_security", "modsec", "x-modsec"],
        "Barracuda": ["barracuda", "x-barracuda"],
        "Fortinet/FortiWeb": ["fortigate", "fortiweb", "fgd_"],
        "Citrix NetScaler": ["citrix", "ns_af", "netscaler"],
        "DDoS-Guard": ["ddos-guard", "ddos_guard"],
        "Wordfence": ["wordfence"],
        "StackPath": ["stackpath", "x-sp-"],
        "Fastly": ["fastly", "x-served-by", "x-cache"],
    }
    
    PAYLOADS = [
        "/?id=<script>alert(1)</script>",
        "/?q=<svg/onload=alert(1)>",
        "/?cmd=cat+/etc/passwd",
        "/?file=../../etc/passwd",
        "/?id=1'+OR+'1'='1",
        "/wp-admin/admin-ajax.php?action=revslider_show_image&img=../wp-config.php",
        "/?__import__('os').system('id')",
    ]

    def __init__(self, host, port=None, timeout=5.0):
        self.host = host.strip()
        self.port = port
        self.timeout = timeout
        self.ip = None
        
    def resolve(self):
        try:
            self.ip = socket.gethostbyname(self.host)
            return self.ip
        except socket.gaierror:
            return None
    
    def _make_request(self, path, use_https):
        headers = {
            "Host": self.host,
            "User-Agent": _random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "X-Forwarded-For": _random_ip(),
            "X-Real-IP": _random_ip(),
            "Referer": f"https://www.google.com/search?q={self.host}",
            "Connection": "close",
        }
        try:
            target = self.ip or self.host
            if use_https:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                conn = http.client.HTTPSConnection(target, self.port, timeout=self.timeout, context=ctx)
            else:
                conn = http.client.HTTPConnection(target, self.port, timeout=self.timeout)
            
            conn.request("GET", path, headers=headers)
            resp = conn.getresponse()
            body = resp.read().decode(errors="ignore")
            headers_dict = {k.lower(): v.lower() for k, v in resp.getheaders()}
            conn.close()
            return resp.status, headers_dict, body
        except Exception as e:
            return None, {}, str(e)
    
    def _analyze(self, status, headers, body):
        detected = []
        details = []
        
        for waf_name, patterns in self.SIGNATURES.items():
            for pat in patterns:
                pat_lower = pat.lower()
                for k, v in headers.items():
                    if pat_lower in k or pat_lower in v:
                        if waf_name not in detected:
                            detected.append(waf_name)
                            details.append(f"Header match: {pat}")
                        break
        
        cookies = headers.get("set-cookie", "")
        cookie_signatures = {
            "incap_ses": "Imperva/Incapsula",
            "visid_incap": "Imperva/Incapsula", 
            "__cfduid": "Cloudflare",
            "cf_clearance": "Cloudflare",
            "awselb": "AWS ELB",
        }
        for sig, waf in cookie_signatures.items():
            if sig in cookies:
                if waf not in detected:
                    detected.append(waf)
                    details.append(f"Cookie: {sig}")
        
        if status in (403, 406, 429, 503):
            block_indicators = [
                "access denied", "forbidden", "blocked", "security check",
                "captcha", "challenge", "verify you are human", "ray id",
                "incident id", "request blocked", "web application firewall"
            ]
            body_lower = body.lower()
            for indicator in block_indicators:
                if indicator in body_lower:
                    if "Generic WAF" not in detected:
                        detected.append("Generic WAF (Block Page)")
                        details.append(f"Block indicator: {indicator}")
                    break
            else:
                if status == 403 and not detected:
                    detected.append("Possible WAF (403 Forbidden)")
                    details.append("403 response to payload")
        
        body_patterns = {
            "cf-ray": "Cloudflare",
            "cloudflare": "Cloudflare",
            "incapsula": "Imperva/Incapsula",
            "akamai": "Akamai",
            "sucuri": "Sucuri",
            "wordfence": "Wordfence",
        }
        body_lower = body.lower()
        for pat, waf in body_patterns.items():
            if pat in body_lower:
                if waf not in detected:
                    detected.append(waf)
                    details.append(f"Body content: {pat}")
        
        return detected, details
    
    def detect(self, use_payloads=True):
        if not self.resolve():
            return {"error": f"Could not resolve {self.host}", "waf": None}
        
        if self.port is None:
            self.port = 443
        use_https = self.port in (443, 8443, 4443, 10443)
        
        all_detected = set()
        all_details = []
        last_status = None
        
        status, headers, body = self._make_request("/", use_https)
        if status:
            last_status = status
            detected, details = self._analyze(status, headers, body)
            all_detected.update(detected)
            all_details.extend(details)
        
        if use_payloads:
            for payload in self.PAYLOADS:
                time.sleep(random.uniform(0.1, 0.3))
                status, headers, body = self._make_request(payload, use_https)
                if status:
                    last_status = status
                    detected, details = self._analyze(status, headers, body)
                    all_detected.update(detected)
                    all_details.extend(details)
                    
                    specific = [w for w in all_detected if "Generic" not in w and "Possible" not in w]
                    if specific:
                        break
        
        waf_name = None
        if all_detected:
            specific = [w for w in all_detected if "Generic" not in w and "Possible" not in w]
            waf_name = specific[0] if specific else list(all_detected)[0]
        
        return {
            "host": self.host,
            "ip": self.ip,
            "port": self.port,
            "waf": waf_name,
            "all_detected": list(all_detected),
            "details": list(set(all_details)),
            "status": last_status
        }


# =============================================================================
# GUI Tool Definition
# =============================================================================

class WAFW00FTool(ToolBase):
    """WAFW00F WAF detection tool plugin."""

    @property
    def name(self) -> str:
        return "WAFW00F"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.INFO_GATHERING

    def get_widget(self, main_window):
        return WAFW00FToolView(main_window=main_window)


class WAFW00FWorker(QThread):
    """Background worker for WAF detection."""
    output_ready = Signal(str)
    finished_signal = Signal()
    error = Signal(str)
    
    def __init__(self, command):
        super().__init__()
        self.command = command
        self.process = None
        self.is_running = True
    
    def run(self):
        import subprocess
        try:
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in iter(self.process.stdout.readline, ''):
                if not self.is_running:
                    break
                if line:
                    self.output_ready.emit(line.rstrip())
            
            self.process.wait()
        except FileNotFoundError:
            self.error.emit("wafw00f not found. Install with: pip install wafw00f")
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished_signal.emit()
    
    def stop(self):
        self.is_running = False
        if self.process:
            self.process.terminate()


class WAFW00FToolView(QWidget, SafeStop, OutputHelper):
    """WAFW00F WAF detection interface."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_safe_stop()
        
        # State
        self.base_dir = None
        self.output_file = None
        
        # Build UI
        self._build_ui()
        self.update_command()

    def _build_ui(self):
        """Build complete UI."""
        self.setStyleSheet(TOOL_VIEW_STYLE)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = ToolSplitter()

        # ==================== CONTROL PANEL ====================
        control_panel = QWidget()
        control_panel.setStyleSheet(f"background-color: {COLOR_BACKGROUND_SECONDARY};")
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        # Header
        header = HeaderLabel("INFO_GATHERING", "WAFW00F")
        control_layout.addWidget(header)

        # Target Row
        target_label = StyledLabel("Target")
        control_layout.addWidget(target_label)

        target_row = QHBoxLayout()
        self.target_input = StyledLineEdit("example.com or https://example.com")
        self.target_input.textChanged.connect(self.update_command)
        
        self.run_button = RunButton()
        self.run_button.clicked.connect(self.run_scan)
        self.stop_button = StopButton()
        self.stop_button.clicked.connect(self.stop_scan)
        
        target_row.addWidget(self.target_input)
        target_row.addWidget(self.run_button)
        target_row.addWidget(self.stop_button)
        control_layout.addLayout(target_row)

        # Command Display
        self.command_display = CommandDisplay()
        self.command_input = self.command_display.input
        control_layout.addWidget(self.command_display)

        # ==================== OPTIONS GROUP ====================
        options_group = StyledGroupBox("⚙️ Scan Options")
        options_layout = QGridLayout(options_group)
        options_layout.setContentsMargins(10, 15, 10, 10)
        options_layout.setSpacing(10)

        # Mode
        mode_label = StyledLabel("Mode:")
        self.mode_combo = StyledComboBox()
        self.mode_combo.addItems(["Standard", "Aggressive (-a)", "Fingerprint All (-f)"])
        self.mode_combo.currentTextChanged.connect(self.update_command)
        
        # Proxy
        proxy_label = StyledLabel("Proxy:")
        self.proxy_input = StyledLineEdit("http://127.0.0.1:8080")
        self.proxy_input.textChanged.connect(self.update_command)

        # Timeout
        timeout_label = StyledLabel("Timeout:")
        self.timeout_spin = StyledSpinBox()
        self.timeout_spin.setRange(1, 60)
        self.timeout_spin.setValue(10)
        self.timeout_spin.setSuffix(" s")
        self.timeout_spin.valueChanged.connect(self.update_command)

        # Checkboxes
        self.list_wafs_check = StyledCheckBox("List WAFs (-l)")
        self.list_wafs_check.stateChanged.connect(self.update_command)

        self.no_redirect_check = StyledCheckBox("No Redirects (-r)")
        self.no_redirect_check.stateChanged.connect(self.update_command)

        # Layout
        options_layout.addWidget(mode_label, 0, 0)
        options_layout.addWidget(self.mode_combo, 0, 1)
        options_layout.addWidget(proxy_label, 0, 2)
        options_layout.addWidget(self.proxy_input, 0, 3)
        options_layout.addWidget(timeout_label, 0, 4)
        options_layout.addWidget(self.timeout_spin, 0, 5)
        options_layout.addWidget(self.list_wafs_check, 1, 0, 1, 2)
        options_layout.addWidget(self.no_redirect_check, 1, 2, 1, 2)
        options_layout.setColumnStretch(1, 1)
        options_layout.setColumnStretch(3, 1)

        control_layout.addWidget(options_group)
        control_layout.addStretch()

        splitter.addWidget(control_panel)

        # ==================== OUTPUT AREA ====================
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("WAFW00F results will appear here...")

        self.copy_button = CopyButton(self.output.output_text, self.main_window)
        self.copy_button.setParent(self.output.output_text)
        self.copy_button.raise_()
        self.output.output_text.installEventFilter(self)

        splitter.addWidget(self.output)
        splitter.setSizes([300, 400])

        main_layout.addWidget(splitter)

    def eventFilter(self, obj, event):
        """Position copy button on resize."""
        from PySide6.QtCore import QEvent
        if obj == self.output.output_text and event.type() == QEvent.Resize:
            self.copy_button.move(
                self.output.output_text.width() - self.copy_button.sizeHint().width() - 10,
                10
            )
        return super().eventFilter(obj, event)

    def update_command(self):
        target = self.target_input.text().strip()
        if not target:
            target = "<target>"

        cmd_parts = ["wafw00f", target]

        mode = self.mode_combo.currentText()
        if "Aggressive" in mode:
            cmd_parts.append("-a")
        elif "Fingerprint" in mode:
            cmd_parts.append("-f")

        proxy = self.proxy_input.text().strip()
        if proxy:
            cmd_parts.extend(["-p", proxy])

        if self.timeout_spin.value() != 10:
            cmd_parts.extend(["-t", str(self.timeout_spin.value())])

        if self.list_wafs_check.isChecked():
            cmd_parts.append("-l")

        if self.no_redirect_check.isChecked():
            cmd_parts.append("-r")

        self.command_input.setText(" ".join(cmd_parts))

    def run_scan(self):
        target = self.target_input.text().strip()
        
        if self.list_wafs_check.isChecked():
            self.output.clear()
            self._info("Listing all known WAFs...")
            command = ["wafw00f", "-l"]
            self._execute_command(command)
            return
            
        if not target:
            self._notify("Please enter a target")
            return

        self.output.clear()
        self._info(f"Starting WAFW00F scan on: {target}")
        self._section("WAF DETECTION")

        try:
            temp = target
            if "://" in temp:
                temp = temp.split("://", 1)[1]
            target_name = temp.split("/")[0].split(":")[0]
        except:
            target_name = "target"

        self.base_dir = create_target_dirs(target_name, None)
        self.output_file = os.path.join(self.base_dir, "Logs", "wafw00f.txt")

        command = ["wafw00f"]
        
        mode = self.mode_combo.currentText()
        if "Aggressive" in mode:
            command.append("-a")
        elif "Fingerprint" in mode:
            command.append("-f")
        
        proxy = self.proxy_input.text().strip()
        if proxy:
            command.extend(["-p", proxy])
        
        if self.timeout_spin.value() != 10:
            command.extend(["-t", str(self.timeout_spin.value())])
        
        if self.no_redirect_check.isChecked():
            command.append("-r")
        
        command.append(target)
        
        self._execute_command(command)

    def _execute_command(self, command):
        self.worker = WAFW00FWorker(command)
        self.worker.output_ready.connect(self._on_output)
        self.worker.finished_signal.connect(self._on_scan_completed)
        self.worker.error.connect(lambda err: self._error(f"Error: {err}"))

        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        if self.main_window:
            self.main_window.active_process = self.worker

        self.worker.start()

    def _on_scan_completed(self):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        if hasattr(self, 'output_file') and self.output_file:
            try:
                with open(self.output_file, 'w') as f:
                    f.write(self.output.toPlainText())
                self._info(f"Results saved to: {self.output_file}")
            except Exception as e:
                self._error(f"Failed to save results: {e}")

        self.worker = None
        if self.main_window:
            self.main_window.active_process = None
        self._info("Scan completed")
        self._notify("WAFW00F scan completed.")

    def _on_output(self, line):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        line = ansi_escape.sub('', line)

        if not line.strip():
            return

        line_lower = line.lower()

        if "is behind" in line_lower or "waf detected" in line_lower:
            self.output.append(f'<span style="color:#10B981;font-weight:bold;">{line}</span>')
        elif "no waf" in line_lower or "not behind" in line_lower:
            self.output.append(f'<span style="color:#FACC15;">{line}</span>')
        elif "error" in line_lower or "failed" in line_lower:
            self.output.append(f'<span style="color:#F87171;">{line}</span>')
        elif line.startswith("[*]") or "checking" in line_lower:
            self.output.append(f'<span style="color:#60A5FA;">{line}</span>')
        else:
            self.output.append(line)
