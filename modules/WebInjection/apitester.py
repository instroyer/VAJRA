# =============================================================================
# modules/apitester.py
#
# API Tester - OWASP API Security Audit Tool
# =============================================================================

import os
import shlex
import html
import time
import json
import re
from concurrent.futures import ThreadPoolExecutor

try:
    import requests
except ImportError:
    pass

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Slot, Signal, QObject

from modules.bases import ToolBase, ToolCategory
from ui.worker import ToolExecutionMixin
from ui.styles import (
    RunButton, StopButton, StyledLineEdit, StyledSpinBox, StyledComboBox,
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView,
    ToolSplitter, StyledToolView, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING
)


class APITesterTool(ToolBase):
    name = "API Tester"
    category = ToolCategory.WEB_INJECTION
    
    @property
    def icon(self) -> str:
        return "🏹"
    
    def get_widget(self, main_window):
        return APITesterView(main_window=main_window)


class AuditWorker(QObject):
    """OWASP API Security Scanner Logic."""
    log = Signal(str)
    result = Signal(dict)
    finished = Signal()
    progress = Signal(int, int)

    def __init__(self, target, method, concurrency):
        super().__init__()
        self.target = target
        self.method = method
        self.concurrency = concurrency
        self.is_running = True
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'VAJRA-OSP/Audit'})

    def run(self):
        try:
            self.log.emit(f"[*] Starting OWASP API Audit on: {self.target}")
            
            checks = [
                self.check_api8_misconfig,
                self.check_api1_bola,
                self.check_api2_auth,
                self.check_api3_mass_assignment,
                self.check_api5_bfla,
                self.check_api7_ssrf,
                self.check_data_exposure
            ]
            
            total = len(checks)
            for i, check in enumerate(checks):
                if not self.is_running: break
                check()
                self.progress.emit(i+1, total)
            
            self.finished.emit()

        except Exception as e:
            self.log.emit(f"[-] Critical Error: {str(e)}")
            self.finished.emit()

    def check_api8_misconfig(self):
        self.log.emit("[*] Checking API8: Security Misconfiguration (Headers)...")
        try:
            r = self.session.get(self.target, timeout=10)
            missing = []
            if 'Strict-Transport-Security' not in r.headers: missing.append("HSTS")
            if 'Content-Security-Policy' not in r.headers: missing.append("CSP")
            if 'X-Frame-Options' not in r.headers: missing.append("X-Frame-Options")
            
            if missing:
                self.report("API8: Misconfigure", f"Missing Headers: {', '.join(missing)}", "LOW", poc=f"Response headers missing: {missing}")
            else:
                self.log.emit(f"<span style='color:{COLOR_SUCCESS}'>[+] Security Headers OK</span>")
                
            if 'Server' in r.headers:
                 self.report("API8: Info Leak", f"Server Header Leaked: {r.headers['Server']}", "LOW", poc=f"Header found: Server: {r.headers['Server']}")

        except Exception as e:
            self.log.emit(f"[-] Failed to optimize check: {e}")

    def check_api1_bola(self):
        """Simple heuristic for BOLA: Fuzz integer IDs in URL."""
        self.log.emit("[*] Checking API1: Broken Object Level Authorization (ID Fuzzing)...")
        # Regex to find integers in URL path
        # e.g. /users/105/profile
        match = re.search(r'/(\d+)', self.target)
        if match:
            original_id = match.group(1)
            fuzzed_id = str(int(original_id) + 1)
            fuzzed_url = self.target.replace(f"/{original_id}", f"/{fuzzed_id}")
            
            output = f"Fuzzing ID {original_id} -> {fuzzed_id}"
            self.log.emit(f"[*] {output}")
            
            try:
                r_orig = self.session.get(self.target)
                r_fuzz = self.session.get(fuzzed_url)
                
                if r_fuzz.status_code == 200 and len(r_fuzz.text) != len(r_orig.text):
                     self.report("API1: BOLA", f"Access succeeded for tweaked ID: {fuzzed_url}", "HIGH", poc=f"Try accessing: {fuzzed_url} (Different response length)")
                elif r_fuzz.status_code == 401 or r_fuzz.status_code == 403:
                     self.log.emit(f"[+] BOLA Check Passed (Access Denied for {fuzzed_id})")
                else:
                     self.log.emit(f"[-] No obvious BOLA (Status {r_fuzz.status_code})")
            except Exception:
                pass
        else:
            self.log.emit("[-] No numeric ID found in URL to test for BOLA.")

    def check_api2_auth(self):
        self.log.emit("[*] Checking API2: Broken Authentication...")
        # Check if we can access without auth (assuming no auth headers provided yet)
        try:
            r = self.session.get(self.target)
            if r.status_code == 200:
                self.report("API2: No Auth", "Endpoint accessible without credentials", "MEDIUM", poc=f"GET {self.target} returned 200 OK without Auth headers")
        except: pass

    def check_api3_mass_assignment(self):
        self.log.emit("[*] Checking API3: Mass Assignment (Injecting admin fields)...")
        payloads = [
            {"isAdmin": True},
            {"role": "admin"},
            {"is_admin": 1}
        ]
        for p in payloads:
            try:
                r = self.session.post(self.target, json=p)
                if r.status_code == 200 and ("admin" in r.text or "true" in r.text):
                    self.report("API3: Mass Assign", f"Endpoint accepted {p} with 200 OK", "HIGH", poc=f"POST {self.target} Body: {json.dumps(p)}")
            except: pass

    def check_api5_bfla(self):
        self.log.emit("[*] Checking API5: Broken Function Level Auth (Method Fuzzing)...")
        danger_methods = ['PUT', 'DELETE', 'PATCH']
        for m in danger_methods:
            try:
                r = requests.request(m, self.target, timeout=5)
                if r.status_code not in [405, 404, 501]:
                     self.report("API5: Method Allowed", f"Method {m} returned {r.status_code}", "MEDIUM", poc=f"{m} {self.target} -> {r.status_code}")
            except: pass

    def check_api7_ssrf(self):
        self.log.emit("[*] Checking API7: SSRF...")
        ssrf_params = {'url': 'http://127.0.0.1', 'redirect': '127.0.0.1', 'link': 'localhost'}
        try:
            r = self.session.get(self.target, params=ssrf_params)
            if "localhost" in r.text or "127.0.0.1" in r.text:
                 self.report("API7: SSRF", "Possible SSRF reflection detected", "HIGH", poc=f"GET {self.target}?url=http://127.0.0.1 -> Response contained 'localhost'/'127.0.0.1'")
        except: pass

    def check_data_exposure(self):
         self.log.emit("[*] Checking API3: Sensitive Data Exposure...")
         try:
             r = self.session.get(self.target)
             if "password" in r.text or "secret" in r.text or "key" in r.text:
                  match = re.search(r'(?i)(password|secret|key)"?\s*:\s*"?([a-z0-9_]+)', r.text)
                  hit = match.group(0) if match else "Found sensitive keywords"
                  self.report("Data Exposure", f"Sensitive data pattern found: {hit}", "HIGH", poc=f"Response body match regex: {hit[:50]}...")
         except: pass

    def report(self, check, issue, severity, poc="Details in logs"):
        color = COLOR_ERROR if severity == "HIGH" else (COLOR_WARNING if severity == "MEDIUM" else COLOR_SUCCESS)
        self.log.emit(f"<span style='color:{color}'>[!] {check}: {issue}</span>")
        self.result.emit({"check": check, "issue": issue, "severity": severity, "poc": poc})

    def stop(self):
        self.is_running = False


class APITesterView(StyledToolView, ToolExecutionMixin):
    tool_name = "API Tester"
    tool_category = "WEB_INJECTION"

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.workers = set()
        self.scanner_thread = None
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = ToolSplitter()
        
        # === Left Panel: Controls ===
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        
        header = HeaderLabel(self.tool_category, self.tool_name)
        control_layout.addWidget(header)
        
        # Target
        target_group = StyledGroupBox("🎯 Target")
        target_layout = QGridLayout(target_group)
        self.url_input = StyledLineEdit()
        self.url_input.setPlaceholderText("http://example.com/api/v1/user/101")
        
        target_layout.addWidget(StyledLabel("URL:"), 0, 0)
        target_layout.addWidget(self.url_input, 0, 1)
        control_layout.addWidget(target_group)

        # Config
        self.opts_group = StyledGroupBox("⚙️ Config")
        opts_layout = QGridLayout(self.opts_group)
        self.threads_spin = StyledSpinBox()
        self.threads_spin.setRange(1, 10)
        self.threads_spin.setValue(1) # Audits are usually lighter on concurrency to avoid WAF
        opts_layout.addWidget(StyledLabel("Threads:"), 0, 0)
        opts_layout.addWidget(self.threads_spin, 0, 1)
        control_layout.addWidget(self.opts_group)
        
        # Note
        note = StyledLabel("ℹ️ Checks for OWASP API Top 10 vulnerabilities.\nIncludes BOLA, Broken Auth, Mass Assignment, etc.")
        note.setStyleSheet("color: #aaa; font-size: 13px; font-style: italic;")
        control_layout.addWidget(note)

        # Buttons
        btn_layout = QHBoxLayout()
        self.run_button = RunButton("AUDIT API")
        self.run_button.clicked.connect(self.run_scan)
        self.stop_button = StopButton()
        self.stop_button.clicked.connect(self.stop_scan)
        btn_layout.addWidget(self.run_button)
        btn_layout.addWidget(self.stop_button)
        control_layout.addLayout(btn_layout)
        
        control_layout.addStretch()
        splitter.addWidget(control_panel)
        
        # === Right Panel: Output & Results ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Check", "Issue", "Severity", "PoC"])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.results_table.setStyleSheet("background-color: #111; color: #0f0; gridline-color: #333;")
        
        self.output = OutputView(self.main_window)
        
        right_layout.addWidget(self.results_table, 1)
        right_layout.addWidget(self.output, 2)
        splitter.addWidget(right_panel)
        
        main_layout.addWidget(splitter)
        splitter.setSizes([350, 650])

    def run_scan(self):
        target = self.url_input.text().strip()
        if not target:
            self._error("Target URL required")
            return
            
        self.output.clear()
        self.results_table.setRowCount(0)
        self.run_button.set_loading(True)
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # Start Worker Thread
        from PySide6.QtCore import QThread
        self.thread = QThread()
        
        self.worker = AuditWorker(target, "GET", 1)

        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.log.connect(self.on_new_output)
        self.worker.result.connect(self.add_result)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.on_execution_finished)
        
        self.thread.start()

    def stop_scan(self):
        if hasattr(self, 'worker'):
            self.worker.stop()
            self._error("Stopping scan...")

    def on_new_output(self, msg):
        self._raw(msg + "<br>")

    def add_result(self, data):
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        self.results_table.setItem(row, 0, QTableWidgetItem(data.get('check', 'Param')))
        self.results_table.setItem(row, 1, QTableWidgetItem(data.get('issue', 'Type')))
        self.results_table.setItem(row, 2, QTableWidgetItem(data.get('severity', 'INFO')))
        
        # Add PoC Button
        poc_data = data.get('poc', 'No PoC available')
        from PySide6.QtWidgets import QPushButton, QDialog, QTextEdit, QApplication
        
        btn = QPushButton("Show PoC")
        btn.setStyleSheet("background-color: #3b82f6; color: white; border-radius: 4px; padding: 2px;")
        btn.setCursor(Qt.PointingHandCursor)
        
        class PoCDialog(QDialog):
            def __init__(self, title, content, parent=None):
                super().__init__(parent)
                self.setWindowTitle(title)
                self.resize(600, 400)
                layout = QVBoxLayout(self)
                
                # Header
                header = StyledLabel(f"<h3>{title}</h3>")
                layout.addWidget(header)
                
                # Content (Code Block style)
                self.text_area = QTextEdit()
                self.text_area.setPlainText(content)
                self.text_area.setReadOnly(True)
                self.text_area.setStyleSheet("""
                    QTextEdit {
                        background-color: #1e1e1e;
                        color: #d4d4d4;
                        font-family: 'Consolas', 'Monospace';
                        font-size: 13px;
                        border: 1px solid #333;
                        border-radius: 4px;
                        padding: 10px;
                    }
                """)
                layout.addWidget(self.text_area)
                
                # Buttons
                btn_layout = QHBoxLayout()
                copy_btn = QPushButton("Copy to Clipboard")
                copy_btn.setStyleSheet("background-color: #4b5563; color: white; padding: 8px; border-radius: 4px;")
                copy_btn.clicked.connect(self.copy_to_clipboard)
                
                close_btn = QPushButton("Close")
                close_btn.setStyleSheet("background-color: #ef4444; color: white; padding: 8px; border-radius: 4px;")
                close_btn.clicked.connect(self.accept)
                
                btn_layout.addWidget(copy_btn)
                btn_layout.addStretch()
                btn_layout.addWidget(close_btn)
                layout.addLayout(btn_layout)
                
                # Apply Dialog Style
                self.setStyleSheet("""
                    QDialog { background-color: #2d2d2d; }
                    QLabel { color: #fff; }
                """)

            def copy_to_clipboard(self):
                clipboard = QApplication.clipboard()
                clipboard.setText(self.text_area.toPlainText())
                self.text_area.setStyleSheet("background-color: #064e3b; color: #fff;") # Flash green
                QApplication.processEvents()
                time.sleep(0.2)
                self.text_area.setStyleSheet("""
                    QTextEdit {
                        background-color: #1e1e1e;
                        color: #d4d4d4;
                        font-family: 'Consolas', 'Monospace';
                        font-size: 13px;
                        border: 1px solid #333;
                        border-radius: 4px;
                        padding: 10px;
                    }
                """)

        def show_poc():
            dlg = PoCDialog("Vulnerability PoC", poc_data, self)
            dlg.exec()
            
        btn.clicked.connect(show_poc)
        self.results_table.setCellWidget(row, 3, btn)

    def on_execution_finished(self):
        self.run_button.set_loading(False)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
