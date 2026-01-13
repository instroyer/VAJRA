# =============================================================================
# modules/WebScanner/crawler.py
#
# Advanced Web Crawler - BurpSuite-like Spidering & Site Mapping
# Features: Robots.txt bypass, Scope control, Deep link extraction
# =============================================================================

import re
import time
from urllib.parse import urlparse, urljoin
from collections import deque
from concurrent.futures import ThreadPoolExecutor

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    pass # Should be installed by environment
    
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QTreeWidget, QTreeWidgetItem, QPushButton, QLabel
)
from PySide6.QtCore import Qt, Signal, QObject, QThread

from modules.bases import ToolBase, ToolCategory
from ui.worker import ToolExecutionMixin
from ui.styles import (
    RunButton, StopButton, StyledLineEdit, StyledSpinBox, StyledCheckBox,
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView,
    ToolSplitter, StyledToolView, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING,
    COLOR_TEXT_PRIMARY
)

class CrawlerTool(ToolBase):
    name = "Web Crawler"
    category = ToolCategory.WEB_INJECTION
    
    @property
    def icon(self) -> str:
        return "🕷️"
    
    def get_widget(self, main_window):
        return CrawlerView(main_window=main_window)



class CrawlerWorker(QObject):
    log = Signal(str)
    new_url = Signal(str, int, str) # url, status, type
    finished = Signal()
    progress = Signal(int, int) # discovered, visited

    def __init__(self, start_url, max_depth, concurrency, extensions_ignore, headers):
        super().__init__()
        self.start_url = start_url
        self.domain = urlparse(start_url).netloc
        self.max_depth = max_depth
        self.concurrency = concurrency
        self.extensions_ignore = extensions_ignore
        self.headers = headers
        
        self.is_running = True
        self.visited = set()
        self.queue = deque([(start_url, 0)])
        self.discovered_count = 0
        self.session = requests.Session()
        self.session.headers.update(headers)
        
        # We purposely ignore robots.txt in this design (as requested)

    def run(self):
        self.log.emit(f"[*] Starting Crawl on: {self.start_url}")
        self.log.emit(f"[*] Scope: {self.domain} | Depth: {self.max_depth}")
        self.log.emit(f"[*] Ignoring Robots.txt: ENABLED")
        
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            while self.queue and self.is_running:
                # Get batch of URLs to process
                # Simple implementation: Process manually to manage depth correctly
                # For robust BFS with threads, we need a lock on visited, 
                # but for simplicity in this GUI tool, we'll fetch one, parse, add to queue
                
                # In a real heavy crawler, we'd use a shared queue with workers.
                # Here we used ThreadPool to process the *requests* primarily.
                
                if not self.is_running: break
                
                current_batch = []
                while self.queue and len(current_batch) < self.concurrency:
                    url, depth = self.queue.popleft()
                    if url not in self.visited:
                        self.visited.add(url)
                        current_batch.append((url, depth))

                if not current_batch:
                    break

                futures = [executor.submit(self._process_url, u, d) for u, d in current_batch]
                
                for future in futures:
                    if not self.is_running: break
                    try:
                        new_links = future.result()
                        if new_links:
                            for link, depth in new_links:
                                if link not in self.visited:
                                    self.queue.append((link, depth))
                    except Exception as e:
                        pass
                
                self.progress.emit(len(self.queue), len(self.visited))
                time.sleep(0.1) # Small breathe

        self.log.emit("[*] Crawl Completed.")
        self.finished.emit()

    def _process_url(self, url, depth):
        if not self.is_running: return []
        
        try:
            # Head request first to check content type? 
            # Nah, just GET.
            resp = self.session.get(url, timeout=10, verify=False, stream=True)
            
            # Identify content type
            c_type = resp.headers.get('Content-Type', '').lower()
            size = len(resp.content) # This reads fully? No stream=True without reading.
            
            # Read content if text/html
            body = b""
            if 'text' in c_type or 'javascript' in c_type or 'json' in c_type:
                 body = resp.content # Read it now
            
            self.new_url.emit(url, resp.status_code, c_type)
            
            if depth >= self.max_depth:
                return []
                
            if 'text/html' not in c_type:
                return []

            # Extract Links using BS4
            soup = BeautifulSoup(body, 'html.parser')
            tags = {
                'a': 'href', 'link': 'href', 'script': 'src', 'form': 'action',
                'img': 'src', 'iframe': 'src'
            }
            
            found_urls = []
            
            for tag, attr in tags.items():
                for element in soup.find_all(tag):
                    val = element.get(attr)
                    if val:
                        absolute_url = urljoin(url, val)
                        parsed = urlparse(absolute_url)
                        
                        # Scope Check: Same Domain Only
                        if parsed.netloc == self.domain:
                            absolute_url = absolute_url.split('#')[0]
                            ext = absolute_url.split('.')[-1].lower() if '.' in absolute_url else ''
                            if ext not in self.extensions_ignore:
                                found_urls.append((absolute_url, depth + 1))

            # --- FORM PARSING FOR PARAMETERS ---
            for form in soup.find_all('form'):
                action = form.get('action')
                if action:
                    form_url = urljoin(url, action)
                    inputs = form.find_all('input')
                    
                    # Construct query string for GET forms (or just to map params)
                    params = []
                    for inp in inputs:
                        name = inp.get('name')
                        if name:
                            params.append(f"{name}=")
                    
                    if params:
                        if '?' in form_url:
                            form_url += '&' + '&'.join(params)
                        else:
                            form_url += '?' + '&'.join(params)
                    
                    parsed = urlparse(form_url)
                    if parsed.netloc == self.domain:
                         found_urls.append((form_url, depth + 1))
                                
            return found_urls

        except Exception as e:
            self.log.emit(f"<span style='color:{COLOR_ERROR}'>[-] Error {url}: {e}</span>")
            return []

    def stop(self):
        self.is_running = False


class CrawlerView(StyledToolView, ToolExecutionMixin):
    tool_name = "Web Crawler"
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
        
        # === Left Panel: Config ===
        control_panel = QWidget()
        layout = QVBoxLayout(control_panel)
        layout.addWidget(HeaderLabel(self.tool_category, self.tool_name))
        
        # Target
        target_group = StyledGroupBox("🎯 Target")
        t_layout = QGridLayout(target_group)
        self.url_input = StyledLineEdit()
        self.url_input.setPlaceholderText("http://example.com")
        t_layout.addWidget(StyledLabel("Seed URL:"), 0, 0)
        t_layout.addWidget(self.url_input, 0, 1)
        layout.addWidget(target_group)
        
        # Settings
        conf_group = StyledGroupBox("⚙️ Config")
        c_layout = QGridLayout(conf_group)
        
        self.depth_spin = StyledSpinBox()
        self.depth_spin.setRange(1, 10)
        self.depth_spin.setValue(3)
        
        self.threads_spin = StyledSpinBox()
        self.threads_spin.setRange(1, 20)
        self.threads_spin.setValue(5)
        
        self.ignore_ext = StyledLineEdit("jpg,jpeg,png,gif,css,pdf,svg")
        
        c_layout.addWidget(StyledLabel("Max Depth:"), 0, 0)
        c_layout.addWidget(self.depth_spin, 0, 1)
        c_layout.addWidget(StyledLabel("Threads:"), 1, 0)
        c_layout.addWidget(self.threads_spin, 1, 1)
        c_layout.addWidget(StyledLabel("Ignore Ext:"), 2, 0)
        c_layout.addWidget(self.ignore_ext, 2, 1)
        layout.addWidget(conf_group)
        
        # Buttons
        btns = QHBoxLayout()
        self.run_btn = RunButton("Start Crawl")
        self.run_btn.clicked.connect(self.run_scan)
        self.stop_btn = StopButton()
        self.stop_btn.clicked.connect(self.stop_scan)
        btns.addWidget(self.run_btn)
        btns.addWidget(self.stop_btn)
        layout.addLayout(btns)
        
        layout.addStretch()
        splitter.addWidget(control_panel)
        
        # === Right Panel: Site Map ===
        res_panel = QWidget()
        r_layout = QVBoxLayout(res_panel)
        
        # Search Bar
        self.search_input = StyledLineEdit()
        self.search_input.setPlaceholderText("Find in site map (e.g. /admin, .xml)...")
        self.search_input.textChanged.connect(self.filter_tree)
        r_layout.addWidget(self.search_input)
        
        # Tree View for Site Map
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Path", "Status", "Type"])
        self.tree.setColumnWidth(0, 400)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: #111;
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid #333;
                font-family: 'Consolas', monospace;
            }}
            QHeaderView::section {{
                background-color: #222;
                color: {COLOR_TEXT_PRIMARY};
                padding: 4px;
                border: 1px solid #333;
            }}
        """)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        r_layout.addWidget(self.tree, 1)
        splitter.addWidget(res_panel)
        
        main_layout.addWidget(splitter)
        splitter.setSizes([350, 650])

    def run_scan(self):
        url = self.url_input.text().strip()
        if not url:
            self._error("Seed URL required")
            return
            
        self.tree.clear()
        self.run_btn.set_loading(True)
        self.stop_btn.setEnabled(True)
        
        # Initialize Root Node
        domain = urlparse(url).netloc
        self.root_item = QTreeWidgetItem(self.tree)
        self.root_item.setText(0, domain)
        self.root_item.setExpanded(True)
        self.tree_nodes = {domain: self.root_item} # Map paths to items
        
        exts = [e.strip() for e in self.ignore_ext.text().split(',')]
        
        from PySide6.QtCore import QThread
        self.thread = QThread()
        self.worker = CrawlerWorker(
            url, 
            self.depth_spin.value(),
            self.threads_spin.value(),
            exts,
            {'User-Agent': 'VAJRA-Crawler/1.0'}
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.new_url.connect(self.add_node)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.on_scan_finished)
        self.thread.start()

    def stop_scan(self):
        if hasattr(self, 'worker'):
            self.worker.stop()
            self._error("Stopping crawler...")

    def add_node(self, url, status, ctype):
        parsed = urlparse(url)
        path = parsed.path
        if parsed.query:
            path += "?" + parsed.query
            
        if not path: path = "/"
        
        # Simple flat list under domain for now (Tree logic for full hierarchy is complex)
        # We'll just show full URLs for clarity or group by directory if time permits
        
        item = QTreeWidgetItem(self.root_item)
        item.setText(0, path)
        item.setText(1, str(status))
        item.setText(2, ctype)
        item.setData(0, Qt.UserRole, url)
        
        # Color coding
        if 200 <= status < 300:
            item.setForeground(1, Qt.green)
        elif 300 <= status < 400:
            item.setForeground(1, Qt.cyan)
        else:
            item.setForeground(1, Qt.red)

    def on_scan_finished(self):
        self.run_btn.set_loading(False)
        self.stop_btn.setEnabled(False)
        self._success("Crawl finished.")

    def show_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item: return

        # Use data set in add_node (we will modify add_node next to store full URL)
        full_url = item.data(0, Qt.UserRole)


        
        if not full_url: return

        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction, QGuiApplication
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        menu = QMenu(self)
        
        copy_act = QAction("Copy URL", self)
        copy_act.triggered.connect(lambda: QGuiApplication.clipboard().setText(full_url))
        menu.addAction(copy_act)
        
        open_act = QAction("Open in Browser", self)
        open_act.triggered.connect(lambda: self._open_browser(full_url))
        menu.addAction(open_act)
        
        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _open_browser(self, url):
        import sys, subprocess
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl

        if sys.platform.startswith('linux'):
            try:
                # Suppress "Opening in existing browser session" noise
                subprocess.Popen(['xdg-open', url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except Exception:
                pass
        
        # Fallback for other OS or if subprocess fails
        QDesktopServices.openUrl(QUrl(url))
    def filter_tree(self, text):
        if not hasattr(self, 'root_item') or not self.root_item:
            return
            
        text = text.lower().strip()
        
        # Iterate over all children of the root item (Paths)
        for i in range(self.root_item.childCount()):
            item = self.root_item.child(i)
            # Check path (col 0)
            path_val = item.text(0).lower()
            if text in path_val:
                item.setHidden(False)
            else:
                item.setHidden(True)

    def on_item_double_clicked(self, item, column):
        full_url = item.data(0, Qt.UserRole)
        if full_url:
            self._open_browser(full_url)
