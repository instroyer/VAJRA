# =============================================================================
# modules/web_fuzzer.py
#
# Web Fuzzer - Multi-threaded Fuzzing Tool (FFUF Equivalent in Pure Python)
# =============================================================================

import os
try:
    import requests
except ImportError:
    pass
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog
)
from PySide6.QtCore import QObject, Signal, QThread

from modules.bases import ToolBase, ToolCategory
from ui.worker import ToolExecutionMixin
from ui.styles import (
    RunButton, StopButton, BrowseButton,
    StyledLineEdit, StyledSpinBox, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView,
    ToolSplitter, StyledToolView, COLOR_SUCCESS, COLOR_WARNING
)

# Small default list for testing
DEFAULT_WORDLIST = ["admin", "login", "dashboard", "api", "v1", "backup", "config", "shell", "db", "jenkins"]

class WebFuzzerTool(ToolBase):
    name = "Web Fuzzer"
    category = ToolCategory.WEB_INJECTION
    
    @property
    def icon(self) -> str:
        return "💣"
    
    def get_widget(self, main_window):
        return WebFuzzerView(main_window=main_window)


class FuzzerWorker(QObject):
    log = Signal(str)
    result = Signal(dict)
    finished = Signal()
    progress = Signal(int, int)

    def __init__(self, target, method, wordlist, concurrency, filters, matchers):
        super().__init__()
        self.target = target
        self.method = method
        self.wordlist = wordlist
        self.concurrency = concurrency
        self.filters = filters # dict of codes, size
        self.matchers = matchers
        self.is_running = True

    def run(self):
        total = len(self.wordlist)
        completed = 0
        
        self.log.emit(f"[*] Starting fuzzing on {total} payloads...")
        
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = []
            for word in self.wordlist:
                if not self.is_running: break
                future = executor.submit(self._fuzz, word)
                futures.append(future)

            # Monitor progress
            for future in futures:
                if not self.is_running: break
                try:
                    res = future.result()
                    if res:
                        self.result.emit(res)
                except Exception as e:
                    pass
                
                completed += 1
                if completed % 10 == 0:
                    self.progress.emit(completed, total)
        
        self.finished.emit()

    def _fuzz(self, word):
        url = self.target.replace("FUZZ", word)
        
        try:
            # Basic request
            if self.method == "GET":
                resp = requests.get(url, timeout=5, allow_redirects=False)
            else:
                resp = requests.post(url, timeout=5, allow_redirects=False)
            
            # Filtering Logic (Exclude)
            if self.filters.get('codes') and resp.status_code in self.filters['codes']:
                return None
            
            # Matcher Logic (Include) - If matchers are set, ONLY include matches
            if self.matchers.get('codes'):
                if resp.status_code not in self.matchers['codes']:
                    return None
            
            # Return result
            return {
                "word": word,
                "code": resp.status_code,
                "size": len(resp.content),
                "words": len(resp.text.split()),
                "url": url
            }
        except Exception:
            return None

    def stop(self):
        self.is_running = False


class WebFuzzerView(StyledToolView, ToolExecutionMixin):
    tool_name = "Web Fuzzer"
    tool_category = "WEB_INJECTION"

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.workers = set()
        self.wordlist_data = []
        
        # Load powerful common wordlist by default
        common_path = os.path.join(os.getcwd(), 'db', 'webfuzzers.txt')
        if os.path.exists(common_path):
            try:
                with open(common_path, 'r', encoding='latin-1') as f:
                    self.wordlist_data = [l.strip() for l in f if l.strip()]
            except Exception:
                pass
        
        # Fallback to a minimal list only if file missing
        if not self.wordlist_data:
            self.wordlist_data = ["admin", "login", "dashboard", "api", "config", "shell", "db"]
            
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        splitter = ToolSplitter()
        
        # === Controls ===
        control_panel = QWidget()
        layout = QVBoxLayout(control_panel)
        
        layout.addWidget(HeaderLabel(self.tool_category, self.tool_name))
        
        # Target
        target_group = StyledGroupBox("🎯 Target (Use 'FUZZ' keyword)")
        t_layout = QGridLayout(target_group)
        self.url_input = StyledLineEdit()
        self.url_input.setPlaceholderText("http://target.com/content/FUZZ.html")
        self.method_combo = StyledComboBox()
        self.method_combo.addItems(["GET", "POST", "PUT", "DELETE"])
        
        t_layout.addWidget(StyledLabel("URL:"), 0, 0)
        t_layout.addWidget(self.url_input, 0, 1)
        t_layout.addWidget(self.method_combo, 0, 2)
        layout.addWidget(target_group)
        
        # Wordlist
        wl_group = StyledGroupBox("📚 Wordlist")
        wl_layout = QHBoxLayout(wl_group)
        self.wl_path = StyledLineEdit("Default List")
        self.wl_path.setReadOnly(True)
        self.browse_btn = BrowseButton()
        self.browse_btn.clicked.connect(self._browse)
        wl_layout.addWidget(self.wl_path)
        wl_layout.addWidget(self.browse_btn)
        layout.addWidget(wl_group)
        
        # Filters / Matchers
        fm_group = StyledGroupBox("🔍 Filters & Matchers")
        fm_layout = QGridLayout(fm_group)
        
        self.match_codes = StyledLineEdit("200,204,301,302,307,401,403")
        self.filter_codes = StyledLineEdit("404")
        self.threads = StyledSpinBox()
        self.threads.setValue(20)
        self.threads.setRange(1, 100)
        
        fm_layout.addWidget(StyledLabel("Match Codes:"), 0, 0)
        fm_layout.addWidget(self.match_codes, 0, 1)
        fm_layout.addWidget(StyledLabel("Filter Codes:"), 1, 0)
        fm_layout.addWidget(self.filter_codes, 1, 1)
        fm_layout.addWidget(StyledLabel("Threads:"), 2, 0)
        fm_layout.addWidget(self.threads, 2, 1)
        layout.addWidget(fm_group)
        
        # Buttons
        btns = QHBoxLayout()
        self.run_btn = RunButton("Start Fuzzing")
        self.run_btn.clicked.connect(self.run_scan)
        self.stop_btn = StopButton()
        self.stop_btn.clicked.connect(self.stop_scan)
        btns.addWidget(self.run_btn)
        btns.addWidget(self.stop_btn)
        layout.addLayout(btns)
        
        layout.addStretch()
        splitter.addWidget(control_panel)
        
        # === Results ===
        res_panel = QWidget()
        r_layout = QVBoxLayout(res_panel)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Payload", "Status", "Size", "URL"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Dark theme table
        self.table.setStyleSheet("gridline-color: #333; color: #ddd;")
        
        self.log_box = OutputView(self.main_window)
        # self.log_box.setMaximumHeight(150) # Removed to allow proper resizing
        
        r_layout.addWidget(self.table)
        r_layout.addWidget(self.log_box)
        splitter.addWidget(res_panel)
        
        main_layout.addWidget(splitter)
        splitter.setSizes([400, 600])

    def _browse(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Load Wordlist", "", "txt (*.txt);;All (*)")
        if fname:
            self.wl_path.setText(fname)
            try:
                with open(fname, 'r', encoding='latin-1') as f:
                    self.wordlist_data = [l.strip() for l in f if l.strip()]
                self._info(f"Loaded {len(self.wordlist_data)} words")
            except Exception as e:
                self._error(f"Error: {e}")

    def run_scan(self):
        url = self.url_input.text().strip()
        if "FUZZ" not in url:
            self._error("URL must contain 'FUZZ' keyword")
            return
            
        self.table.setRowCount(0)
        self.log_box.clear()
        
        self.run_btn.set_loading(True)
        self.stop_btn.setEnabled(True)
        
        # Parse filters
        try:
            mc = [int(x) for x in self.match_codes.text().split(",") if x.strip()]
            fc = [int(x) for x in self.filter_codes.text().split(",") if x.strip()]
        except:
            self._error("Invalid status codes")
            return
            
        filters = {'codes': fc}
        matchers = {'codes': mc}
        
        self.thread = QThread()
        self.worker = FuzzerWorker(
            url, self.method_combo.currentText(), 
            self.wordlist_data, self.threads.value(),
            filters, matchers
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.result.connect(self.add_row)
        self.worker.log.connect(self._info)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.on_finished)
        
        self.thread.start()

    def stop_scan(self):
        if hasattr(self, 'worker'):
            self.worker.stop()

    def add_row(self, res):
        r = self.table.rowCount()
        self.table.insertRow(r)
        
        # Payload
        self.table.setItem(r, 0, QTableWidgetItem(res['word']))
        
        # Status (Color coded)
        code_item = QTableWidgetItem(str(res['code']))
        if 200 <= res['code'] < 300:
            code_item.setForeground(Qt.green)
        elif 300 <= res['code'] < 400:
             code_item.setForeground(Qt.yellow)
        else:
             code_item.setForeground(Qt.red)
        self.table.setItem(r, 1, code_item)
        
        self.table.setItem(r, 2, QTableWidgetItem(str(res['size'])))
        self.table.setItem(r, 3, QTableWidgetItem(res['url']))

    def on_finished(self):
        self.run_btn.set_loading(False)
        self.stop_btn.setEnabled(False)
        self._success("Fuzzing completed")
