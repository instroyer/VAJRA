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
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
)
from PySide6.QtCore import Qt, Slot, Signal, QObject

from modules.bases import ToolBase, ToolCategory
from ui.worker import ToolExecutionMixin
from ui.styles import (
    RunButton, StopButton, StyledLineEdit, StyledSpinBox, StyledComboBox,
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView,
    ToolSplitter, StyledToolView, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING
)


# =============================================================================
# Infrastructure Classes
# =============================================================================

class AuthHandler:
    """Manage authentication for API testing"""
    
    AUTH_NONE = "None"
    AUTH_BEARER = "Bearer Token"
    AUTH_BASIC = "Basic Auth"
    AUTH_API_KEY = "API Key"
    
    def __init__(self, auth_type=AUTH_NONE, token="", username="", password="", header_name="X-API-Key"):
        self.auth_type = auth_type
        self.token = token
        self.username = username
        self.password = password
        self.header_name = header_name
    
    def apply_to_session(self, session):
        """Apply authentication to requests session"""
        if self.auth_type == self.AUTH_BEARER and self.token:
            session.headers['Authorization'] = f'Bearer {self.token}'
        elif self.auth_type == self.AUTH_BASIC and self.username:
            from requests.auth import HTTPBasicAuth
            session.auth = HTTPBasicAuth(self.username, self.password)
        elif self.auth_type == self.AUTH_API_KEY and self.token:
            session.headers[self.header_name] = self.token


class HTTPLogger:
    """Log HTTP requests and responses for analysis"""
    
    def __init__(self):
        self.requests = []
        self.responses = []
    
    def log_request(self, method, url, headers, body=None):
        self.requests.append({
            'method': method,
            'url': url,
            'headers': dict(headers),
            'body': body,
            'timestamp': time.time()
        })
    
    def log_response(self, status, headers, body, elapsed):
        self.responses.append({
            'status': status,
            'headers': dict(headers),
            'body': body[:1000] if body else "",  # Truncate large responses
            'elapsed': elapsed
        })
    
    def get_curl_command(self, index=0):
        """Generate curl command for request reproduction"""
        if index >= len(self.requests):
            return ""
        
        req = self.requests[index]
        cmd = f"curl -X {req['method']} '{req['url']}'"
        
        for k, v in req['headers'].items():
            cmd += f" \\\n  -H '{k}: {v}'"
        
        if req['body']:
            cmd += f" \\\n  -d '{req['body']}'"
        
        return cmd


class ScanThrottler:
    """Prevent aggressive scanning that triggers WAF/IDS"""
    
    def __init__(self, requests_per_second=2):
        self.rps = requests_per_second
        self.last_request = 0
    
    def wait_if_needed(self):
        """Throttle requests to configured rate"""
        elapsed = time.time() - self.last_request
        if elapsed < (1.0 / self.rps):
            time.sleep((1.0 / self.rps) - elapsed)
        self.last_request = time.time()


class ReportExporter:
    """Export scan results in multiple formats"""
    
    @staticmethod
    def export_json(results, filepath):
        """Export as JSON"""
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
    
    @staticmethod
    def export_html(results, filepath, target):
        """Generate HTML report"""
        html = f"""<!DOCTYPE html>
<html><head><title>API Security Audit - {target}</title>
<style>
body {{ font-family: Arial; margin: 20px; background: #1a1a2e; color: #eee; }}
.header {{ background: #e94560; padding: 20px; border-radius: 8px; }}
.finding {{ background: #16213e; margin: 10px 0; padding: 15px; border-radius: 5px; border-left: 4px solid; }}
.high {{ border-color: #e74c3c; }}
.medium {{ border-color: #f39c12; }}
.low {{ border-color: #3498db; }}
.severity {{ font-weight: bold; padding: 5px 10px; border-radius: 3px; }}
pre {{ background: #0f0f0f; padding: 10px; border-radius: 3px; overflow-x: auto; }}
</style></head><body>
<div class="header"><h1>API Security Audit Report</h1>
<p>Target: {target} | Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}</p></div>
<h2>Findings ({len(results)} total)</h2>"""
        
        for r in results:
            sev_class = r['severity'].lower()
            html += f"""
<div class="finding {sev_class}">
<h3>{html.escape(r['check'])}</h3>
<p><span class="severity">{r['severity']}</span></p>
<p><strong>Issue:</strong> {html.escape(r['issue'])}</p>
<pre>{html.escape(r['poc'])}</pre>
</div>"""
        
        html += "</body></html>"
        
        with open(filepath, 'w') as f:
            f.write(html)
    
    @staticmethod
    def export_csv(results, filepath):
        """Export as CSV"""
        import csv
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['check', 'issue', 'severity', 'poc'])
            writer.writeheader()
            writer.writerows(results)


# =============================================================================
# Main Classes
# =============================================================================

class APITesterTool(ToolBase):
    name = "API Tester"
    category = ToolCategory.WEB_INJECTION
    
    @property
    def icon(self) -> str:
        return "🏹"
    
    def get_widget(self, main_window):
        return APITesterView(main_window=main_window)


class AuditWorker(QObject):
    """Comprehensive OWASP API Security Scanner Logic"""
    log = Signal(str)
    result = Signal(dict)
    finished = Signal()
    progress = Signal(int, int)

    def __init__(self, target, method, concurrency, auth_handler=None):
        super().__init__()
        self.target = target
        self.method = method
        self.concurrency = concurrency
        self.is_running = True
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'VAJRA-OSP/Audit'})
        
        # Apply authentication
        if auth_handler:
            auth_handler.apply_to_session(self.session)
        
        # Infrastructure
        self.http_logger = HTTPLogger()
        self.throttler = ScanThrottler(requests_per_second=2)
        self.findings = []

    def run(self):
        try:
            self.log.emit(f"<span style='color:{COLOR_SUCCESS}'>[*] Starting OWASP API Security Top 10 Audit</span>")
            self.log.emit(f"[*] Target: {self.target}")
            
            checks = [
                ("API1:2023", "Broken Object Level Authorization (BOLA)", self.check_api1_bola),
                ("API2:2023", "Broken Authentication", self.check_api2_auth),
                ("API3:2023", "Broken Object Property Level Authorization", self.check_api3_property_auth),
                ("API3:2023", "Excessive Data Exposure", self.check_data_exposure),
                ("API4:2023", "Unrestricted Resource Consumption", self.check_api4_resource_consumption),
                ("API5:2023", "Broken Function Level Authorization (BFLA)", self.check_api5_bfla),
                ("API6:2023", "Unrestricted Access to Sensitive Business Flows", self.check_api6_business_flows),
                ("API7:2023", "Security Misconfiguration", self.check_api7_misconfig),
                ("API7:2023", "Server Side Request Forgery (SSRF)", self.check_api7_ssrf),
                ("API8:2023", "Security Misconfiguration - Injection", self.check_api8_injection),
                ("API8:2023", "Security Misconfiguration (Legacy)", self.check_api8_legacy_misconfig),
                ("API9:2023", "Improper Inventory Management", self.check_api9_inventory),
                ("API10:2023", "Unsafe Consumption of APIs", self.check_api10_unsafe_consumption)
            ]
            
            total = len(checks)
            for i, (code, name, check_func) in enumerate(checks):
                if not self.is_running:
                    break
                
                self.log.emit(f"<span style='color:{COLOR_WARNING}'>[{i+1}/{total}] Checking {code}: {name}...</span>")
                try:
                    check_func()
                except Exception as e:
                    self.log.emit(f"<span style='color:{COLOR_ERROR}'>[-] Check failed: {str(e)}</span>")
                
                self.progress.emit(i+1, total)
                time.sleep(0.5)  # Brief pause between checks
            
            self.log.emit(f"<span style='color:{COLOR_SUCCESS}'>[+] Audit Complete! Found {len(self.findings)} potential issues</span>")
            self.finished.emit()

        except Exception as e:
            self.log.emit(f"<span style='color:{COLOR_ERROR}'>[-] Critical Error: {str(e)}</span>")
            self.finished.emit()


    # =========================================================================
    # OWASP API Security Top 10 (2023) - Comprehensive Checks
    # =========================================================================
    
    def check_api7_misconfig(self):
        """API7:2023 - Security Misconfiguration (Enhanced)"""
        self.throttler.wait_if_needed()
        try:
            r = self.session.get(self.target, timeout=10, verify=False)
            self.http_logger.log_request('GET', self.target, self.session.headers)
            self.http_logger.log_response(r.status_code, r.headers, r.text, r.elapsed.total_seconds())
            
            missing_headers = []
            if 'Strict-Transport-Security' not in r.headers: missing_headers.append("HSTS")
            if 'Content-Security-Policy' not in r.headers: missing_headers.append("CSP")
            if 'X-Frame-Options' not in r.headers: missing_headers.append("X-Frame-Options")
            if 'X-Content-Type-Options' not in r.headers: missing_headers.append("X-Content-Type-Options")
            
            if missing_headers:
                poc = f"curl -I '{self.target}'\n\nMissing security headers:\n" + "\n".join(f"- {h}" for h in missing_headers)
                self.report("API7: Missing Security Headers", f"Headers: {', '.join(missing_headers)}", "LOW", poc)
            
            # CORS misconfiguration
            cors_test = self.session.get(self.target, headers={'Origin': 'https://evil.com'}, timeout=10)
            if 'Access-Control-Allow-Origin' in cors_test.headers:
                acao = cors_test.headers['Access-Control-Allow-Origin']
                if acao == '*' or 'evil.com' in acao:
                    poc = f"curl '{self.target}' -H 'Origin: https://evil.com' -v\n\nResponse: Access-Control-Allow-Origin: {acao}"
                    self.report("API7: CORS Misconfiguration", f"Allows origin: {acao}", "HIGH", poc)
            
            # Information disclosure
            if 'Server' in r.headers or 'X-Powered-By' in r.headers:
                leaked = []
                if 'Server' in r.headers: leaked.append(f"Server: {r.headers['Server']}")
                if 'X-Powered-By' in r.headers: leaked.append(f"X-Powered-By: {r.headers['X-Powered-By']}")
                poc = "\n".join(leaked) + f"\n\ncurl -I '{self.target}'"
                self.report("API7: Information Disclosure", "Server version exposed", "LOW", poc)
                
        except Exception as e:
            self.log.emit(f"[-] Check failed: {e}")
    
    def check_api8_legacy_misconfig(self):
        """API8:2023 - Legacy misconfiguration checks"""
        self.throttler.wait_if_needed()
        try:
            # Verbose error messages
            error_test = self.session.get(self.target + '/nonexistent123xyz', timeout=10)
            if error_test.status_code in [500, 501, 502, 503]:
                if any(keyword in error_test.text.lower() for keyword in ['stack trace', 'exception', 'error', 'sql', 'database']):
                    self.report("API8: Verbose Errors", "Detailed error messages exposed", "MEDIUM", 
                               f"GET {self.target}/nonexistent123xyz returned {error_test.status_code} with debug info")
            
            # Unnecessary HTTP methods
            for method in ['TRACE', 'TRACK', 'OPTIONS']:
                r = requests.request(method, self.target, timeout=5)
                if r.status_code == 200:
                    self.report("API8: Unnecessary Methods", f"{method} method enabled", "LOW",
                               f"curl -X {method} '{self.target}'")
                    
        except Exception:
            pass
    
    def check_api1_bola(self):
        """API1:2023 - Broken Object Level Authorization (Enhanced)"""
        self.throttler.wait_if_needed()
        
        # Test numeric IDs
        match = re.search(r'/(\d+)', self.target)
        if match:
            original_id = match.group(1)
            test_ids = [str(int(original_id) + 1), str(int(original_id) - 1), '999999', '1']
            
            try:
                r_orig = self.session.get(self.target, timeout=10)
                orig_len = len(r_orig.text)
                
                for test_id in test_ids:
                    fuzzed_url = self.target.replace(f"/{original_id}", f"/{test_id}")
                    r_fuzz = self.session.get(fuzzed_url, timeout=10)
                    
                    if r_fuzz.status_code == 200 and abs(len(r_fuzz.text) - orig_len) > 50:
                        poc = f"""curl '{fuzzed_url}' \\
  -H 'Authorization: {self.session.headers.get("Authorization", "YOUR_TOKEN")}'

Original ID: {original_id} -> Test ID: {test_id}
Status: {r_fuzz.status_code}
Response length: {len(r_fuzz.text)} (orig: {orig_len})

This suggests unauthorized access to other users' data."""
                        self.report("API1: BOLA", f"Unauthorized access via ID {test_id}", "HIGH", poc)
                        break
            except:
                pass
        
        # Test UUID patterns
        uuid_match = re.search(r'/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', self.target, re.I)
        if uuid_match:
            self.log.emit("[*] UUID detected - BOLA testing limited without second user account")
    
    def check_api2_auth(self):
        """API2:2023 - Broken Authentication (Enhanced)"""
        self.throttler.wait_if_needed()
        
        # Test unauthenticated access
        temp_session = requests.Session()
        try:
            r = temp_session.get(self.target, timeout=10)
            if r.status_code == 200:
                poc = f"curl '{self.target}'\n\nNo authentication required! Endpoint accessible without credentials."
                self.report("API2: No Authentication", "Endpoint accessible without auth", "HIGH", poc)
        except:
            pass
        
        # JWT testing (if Bearer token present)
        auth_header = self.session.headers.get('Authorization', '')
        if 'Bearer' in auth_header:
            token = auth_header.replace('Bearer ', '').strip()
            
            # Test expired/invalid token
            invalid_tokens = [
                token[:-5] + 'xxxxx',  # Modified signature
                'eyJhbGciOiJub25lIn0.eyJzdWIiOiIxMjM0NTY3ODkwIn0.',  # Algorithm:none
            ]
            
            for invalid_token in invalid_tokens:
                try:
                    r = self.session.get(self.target, headers={'Authorization': f'Bearer {invalid_token}'}, timeout=10)
                    if r.status_code == 200:
                        self.report("API2: JWT Weakness", "Invalid/tampered JWT accepted", "CRITICAL",
                                   f"Modified token accepted: {invalid_token[:20]}...")
                        break
                except:
                    pass
    
    def check_api3_property_auth(self):
        """API3:2023 - Broken Object Property Level Authorization"""
        self.throttler.wait_if_needed()
        
        # Mass assignment test
        admin_fields = [
            {"isAdmin": True, "role": "admin"},
            {"is_admin": 1, "admin": True},
            {"role": "administrator", "permissions": ["*"]},
            {"user_role": "admin", "access_level": 999},
            {"is_superuser": True, "is_staff": True}
        ]
        
        for payload in admin_fields:
            try:
                r = self.session.post(self.target, json=payload, timeout=10)
                if r.status_code in [200, 201] and any(k in r.text.lower() for k in ['admin', 'true', 'success']):
                    poc = f"""curl -X POST '{self.target}' \\
  -H 'Content-Type: application/json' \\
  -d '{json.dumps(payload)}'

Response ({r.status_code}): Accepted admin fields!"""
                    self.report("API3: Mass Assignment", f"Admin field injection: {list(payload.keys())}", "HIGH", poc)
                    break
            except:
                pass
    
    def check_data_exposure(self):
        """API3:2023 - Excessive Data Exposure"""
        self.throttler.wait_if_needed()
        try:
            r = self.session.get(self.target, timeout=10)
            
            # Check for sensitive patterns
            sensitive_patterns = [
                (r'(?i)(password|passwd|pwd)"?\s*:\s*"?[^\s,}]+', 'Password'),
                (r'(?i)(secret|api_key|apikey)"?\s*:\s*"?[^\s,}]+', 'Secret/API Key'),
                (r'(?i)(token|auth_token)"?\s*:\s*"?[^\s,}]+', 'Token'),
                (r'\b\d{3}-\d{2}-\d{4}\b', 'SSN'),
                (r'\b\d{16}\b', 'Credit Card'),
            ]
            
            for pattern, name in sensitive_patterns:
                match = re.search(pattern, r.text)
                if match:
                    hit = match.group(0)[:50]
                    self.report("API3: Data Exposure", f"Sensitive data leaked: {name}", "HIGH", 
                               f"Response contains: {hit}...")
                    break
        except:
            pass
    
    def check_api4_resource_consumption(self):
        """API4:2023 - Unrestricted Resource Consumption"""
        self.throttler.wait_if_needed()
        
        # Rate limiting test
        start_time = time.time()
        statuses = []
        
        for i in range(10):
            try:
                r = self.session.get(self.target, timeout=5)
                statuses.append(r.status_code)
                if r.status_code == 429:  # Rate limited
                    self.log.emit(f"<span style='color:{COLOR_SUCCESS}'>[+] Rate limiting detected (429)</span>")
                    return
            except:
                pass
        
        elapsed = time.time() - start_time
        
        if 429 not in statuses:
            poc = f"""# No rate limiting detected after 10 rapid requests in {elapsed:.2f}s

for i in {{1..100}}; do
  curl '{self.target}' &
done
wait

This could lead to DoS attacks."""
            self.report("API4: No Rate Limiting", "No 429 status after rapid requests", "MEDIUM", poc)
    
    def check_api5_bfla(self):
        """API5:2023 - Broken Function Level Authorization (Enhanced)"""
        self.throttler.wait_if_needed()
        
        # HTTP method fuzzing
        dangerous_methods = ['PUT', 'DELETE', 'PATCH', 'POST']
        for method in dangerous_methods:
            try:
                r = requests.request(method, self.target, timeout=5)
                if r.status_code not in [405, 404, 501, 403]:
                    poc = f"curl -X {method} '{self.target}'\n\nStatus: {r.status_code}\nExpected: 405 (Method Not Allowed)"
                    self.report("API5: Unrestricted Method", f"{method} returned {r.status_code}", "MEDIUM", poc)
            except:
                pass
        
        # Admin endpoint discovery
        base_url = '/'.join(self.target.split('/')[:3])
        admin_paths = ['/admin', '/api/admin', '/api/v1/admin', '/admin/users', '/administrator']
        
        for path in admin_paths:
            try:
                admin_url = base_url + path
                r = self.session.get(admin_url, timeout=5)
                if r.status_code == 200:
                    self.report("API5: Admin Endpoint", f"Admin path accessible: {path}", "HIGH",
                               f"curl '{admin_url}'\n\nStatus: 200 OK")
            except:
                pass
    
    def check_api6_business_flows(self):
        """API6:2023 - Unrestricted Access to Sensitive Business Flows"""
        self.throttler.wait_if_needed()
        
        # Simulate multiple rapid transactions
        if any(keyword in self.target.lower() for keyword in ['purchase', 'order', 'payment', 'transaction']):
            try:
                responses = []
                for i in range(5):
                    r = self.session.post(self.target, json={"amount": 1, "item": "test"}, timeout=5)
                    responses.append(r.status_code)
                
                if responses.count(200) >= 4:
                    self.report("API6: No Transaction Limit", "Multiple rapid transactions allowed", "MEDIUM",
                               "Submitted 5 rapid transactions - all succeeded. No velocity check detected.")
            except:
                pass
    
    def check_api7_ssrf(self):
        """API7:2023 - Server-Side Request Forgery (Enhanced)"""
        self.throttler.wait_if_needed()
        
        ssrf_payloads = [
            ('url', 'http://127.0.0.1'),
            ('url', 'http://localhost'),
            ('url', 'http://169.254.169.254/latest/meta-data/'),  # AWS metadata
            ('redirect', 'http://internal.local'),
            ('webhook', 'http://127.0.0.1:8080'),
            ('api_url', 'file:///etc/passwd'),
        ]
        
        for param, value in ssrf_payloads:
            try:
                r = self.session.get(self.target, params={param: value}, timeout=10)
                if any(indicator in r.text.lower() for indicator in ['localhost', '127.0.0.1', 'ami-id', 'root:', 'metadata']):
                    poc = f"""curl '{self.target}?{param}={value}'

Response contained: {value} reflection or sensitive data
This indicates SSRF vulnerability."""
                    self.report("API7: SSRF", f"SSRF via ?{param}= parameter", "CRITICAL", poc)
                    break
            except:
                pass
    
    def check_api8_injection(self):
        """API8:2023 - Security Misconfiguration - Injection Attacks"""
        self.throttler.wait_if_needed()
        
        # SQL Injection
        sql_payloads = ["' OR '1'='1", "1' OR '1'='1' --", "admin'--", "1 UNION SELECT NULL--"]
        for payload in sql_payloads:
            try:
                r = self.session.get(self.target, params={'id': payload}, timeout=10)
                if any(err in r.text.lower() for err in ['sql syntax', 'mysql', 'postgresql', 'ora-', 'sqlite']):
                    poc = f"curl '{self.target}?id={payload}'\n\nSQL error in response - injection point detected!"
                    self.report("API8: SQL Injection", "SQL error messages detected", "CRITICAL", poc)
                    break
            except:
                pass
        
        # NoSQL Injection
        nosql_payloads = [{"$ne": None}, {"$gt": ""}, {"$regex": ".*"}]
        for payload in nosql_payloads:
            try:
                r = self.session.post(self.target, json={"username": payload}, timeout=10)
                if r.status_code == 200 and len(r.text) > 100:
                    self.report("API8: NoSQL Injection", f"NoSQL operator accepted: {payload}", "HIGH",
                               f"POST {self.target} with body: {json.dumps({'username': payload})}")
                    break
            except:
                pass
        
        # Command Injection
        cmd_payloads = ["; ls", "| whoami", "&& cat /etc/passwd"]
        for payload in cmd_payloads:
            try:
                r = self.session.get(self.target, params={'cmd': payload}, timeout=10)
                if any(indicator in r.text for indicator in ['root:', 'bin/bash', 'usr/bin']):
                    self.report("API8: Command Injection", "Command execution detected", "CRITICAL",
                               f"curl '{self.target}?cmd={payload}'")
                    break
            except:
                pass
    
    def check_api9_inventory(self):
        """API9:2023 - Improper Inventory Management"""
        self.throttler.wait_if_needed()
        
        base_url = '/'.join(self.target.split('/')[:3])
        
        # API version discovery
        versions = ['/v1/', '/v2/', '/api/v1/', '/api/v2/', '/api/beta/', '/api/deprecated/']
        for version in versions:
            try:
                test_url = base_url + version + 'users'
                r = self.session.get(test_url, timeout=5)
                if r.status_code == 200:
                    self.report("API9: Old API Version", f"Version path accessible: {version}", "MEDIUM",
                               f"curl '{test_url}'\n\nOld API versions may have unpatched vulnerabilities")
            except:
                pass
        
        # Documentation exposure
        doc_paths = ['/swagger.json', '/openapi.json', '/api-docs', '/docs', '/swagger-ui', '/api/swagger.json']
        for path in doc_paths:
            try:
                doc_url = base_url + path
                r = self.session.get(doc_url, timeout=5)
                if r.status_code == 200 and ('swagger' in r.text.lower() or 'openapi' in r.text.lower()):
                    self.report("API9: Documentation Exposed", f"API docs public: {path}", "LOW",
                               f"curl '{doc_url}'\n\nAPI documentation publicly accessible")
            except:
                pass
    
    def check_api10_unsafe_consumption(self):
        """API10:2023 - Unsafe Consumption of APIs"""
        self.throttler.wait_if_needed()
        
        # XML External Entity (XXE)
        xxe_payload = """<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<root><data>&xxe;</data></root>"""
        
        try:
            r = self.session.post(self.target, data=xxe_payload, 
                                 headers={'Content-Type': 'application/xml'}, timeout=10)
            if 'root:' in r.text or '/bin/bash' in r.text:
                self.report("API10: XXE Vulnerability", "XML External Entity processed", "CRITICAL",
                           f"POST with XXE payload exposed /etc/passwd")
        except:
            pass

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
        
        # Use plain QLineEdit to avoid cursor jumping issue from StyledLineEdit
        from PySide6.QtWidgets import QLineEdit
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/api/users/1 (Use specific endpoint, not homepage!)")
        self.url_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #1e1e1e;
                color: #e0e0e0;
                font-size: 14px;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
            }}
            QLineEdit:focus {{
                border: 1px solid #888;
            }}
        """)
        
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
        
        # Authentication
        auth_group = StyledGroupBox("🔐 Authentication")
        auth_layout = QGridLayout(auth_group)
        
        from PySide6.QtWidgets import QLineEdit
        
        self.auth_type_combo = StyledComboBox()
        self.auth_type_combo.addItems([
            AuthHandler.AUTH_NONE,
            AuthHandler.AUTH_BEARER,
            AuthHandler.AUTH_BASIC,
            AuthHandler.AUTH_API_KEY
        ])
        self.auth_type_combo.currentTextChanged.connect(self.on_auth_type_changed)
        
        self.auth_token_input = StyledLineEdit()
        self.auth_token_input.setPlaceholderText("Enter Bearer token or API key")
        self.auth_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.auth_username_input = StyledLineEdit()
        self.auth_username_input.setPlaceholderText("Username")
        
        self.auth_password_input = StyledLineEdit()
        self.auth_password_input.setPlaceholderText("Password")
        self.auth_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        auth_layout.addWidget(StyledLabel("Type:"), 0, 0)
        auth_layout.addWidget(self.auth_type_combo, 0, 1)
        auth_layout.addWidget(StyledLabel("Token/Key:"), 1, 0)
        auth_layout.addWidget(self.auth_token_input, 1, 1)
        auth_layout.addWidget(StyledLabel("Username:"), 2, 0)
        auth_layout.addWidget(self.auth_username_input, 2, 1)
        auth_layout.addWidget(StyledLabel("Password:"), 3, 0)
        auth_layout.addWidget(self.auth_password_input, 3, 1)
        
        control_layout.addWidget(auth_group)
        
        # Initially hide auth fields (show based on type)
        self.auth_token_input.setVisible(False)
        self.auth_username_input.setVisible(False)
        self.auth_password_input.setVisible(False)
        
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
        
        self.export_button = QPushButton("📥 Export")
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:disabled {
                background-color: #64748b;
            }
        """)
        self.export_button.clicked.connect(self.export_results)
        self.export_button.setEnabled(False)  # Enable after scan
        
        btn_layout.addWidget(self.run_button)
        btn_layout.addWidget(self.stop_button)
        btn_layout.addWidget(self.export_button)
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

    def on_auth_type_changed(self, auth_type):
        """Handle authentication type selection"""
        # Hide all auth fields first
        self.auth_token_input.setVisible(False)
        self.auth_username_input.setVisible(False)
        self.auth_password_input.setVisible(False)
        
        # Show relevant fields based on type
        if auth_type == AuthHandler.AUTH_BEARER:
            self.auth_token_input.setVisible(True)
            self.auth_token_input.setPlaceholderText("Enter Bearer token (JWT)")
        elif auth_type == AuthHandler.AUTH_BASIC:
            self.auth_username_input.setVisible(True)
            self.auth_password_input.setVisible(True)
        elif auth_type == AuthHandler.AUTH_API_KEY:
            self.auth_token_input.setVisible(True)
            self.auth_token_input.setPlaceholderText("Enter API key")
    
    def run_scan(self):
        target = self.url_input.text().strip()
        if not target:
            self._error("Target URL required")
            return
        
        # Build auth handler
        auth_type = self.auth_type_combo.currentText()
        auth_handler = None
        
        if auth_type == AuthHandler.AUTH_BEARER:
            token = self.auth_token_input.text().strip()
            if token:
                auth_handler = AuthHandler(auth_type=AuthHandler.AUTH_BEARER, token=token)
        elif auth_type == AuthHandler.AUTH_BASIC:
            username = self.auth_username_input.text().strip()
            password = self.auth_password_input.text().strip()
            if username:
                auth_handler = AuthHandler(auth_type=AuthHandler.AUTH_BASIC, username=username, password=password)
        elif auth_type == AuthHandler.AUTH_API_KEY:
            api_key = self.auth_token_input.text().strip()
            if api_key:
                auth_handler = AuthHandler(auth_type=AuthHandler.AUTH_API_KEY, token=api_key)
            
        self.output.clear()
        self.results_table.setRowCount(0)
        self.run_button.set_loading(True)
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.export_button.setEnabled(False)
        
        # Start Worker Thread
        from PySide6.QtCore import QThread
        self.thread = QThread()
        
        self.worker = AuditWorker(target, "GET", 1, auth_handler=auth_handler)

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

    def export_results(self):
        """Export scan results to multiple formats"""
        if self.results_table.rowCount() == 0:
            self._error("No results to export")
            return

        # Collect all results
        results = []
        for row in range(self.results_table.rowCount()):
            results.append({
                'check': self.results_table.item(row, 0).text(),
                'issue': self.results_table.item(row, 1).text(),
                'severity': self.results_table.item(row, 2).text(),
                'poc': "See PoC button for details"
            })
        
        # Export to multiple formats
        target = self.url_input.text().strip()
        target_name = target.replace('https://', '').replace('http://', '').replace('/', '_').replace(':', '_')
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        base_path = f"/tmp/Vajra-results/api_audit_{target_name}_{timestamp}"
        
        import os
        os.makedirs(base_path, exist_ok=True)
        
        # Export JSON
        json_file = f"{base_path}/results.json"
        ReportExporter.export_json(results, json_file)
        
        # Export HTML
        html_file = f"{base_path}/report.html"
        ReportExporter.export_html(results, html_file, target)
        
        # Export CSV
        csv_file = f"{base_path}/results.csv"
        ReportExporter.export_csv(results, csv_file)
        
        self._success(f"✅ Exported to: {base_path}/")
        self.output.append(f"<span style='color:{COLOR_SUCCESS}'>[+] Results exported:</span>")
        self.output.append(f"  📄 JSON: {json_file}")
        self.output.append(f"  🌐 HTML: {html_file}")
        self.output.append(f"  📊 CSV: {csv_file}")
    
    def on_execution_finished(self):
        self.run_button.set_loading(False)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        # Enable export if there are results
        if self.results_table.rowCount() > 0:
            self.export_button.setEnabled(True)
