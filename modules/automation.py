"""
VAJRA Automation - Professional Bug Bounty Reconnaissance Pipeline
Complete automated workflow with proper error handling and reporting
"""

import os
import json
import shutil
import subprocess
import threading
import time
import html
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PySide6.QtCore import Signal, QObject, Qt, QThread
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QGroupBox, QWidget, QProgressBar, QScrollArea, QSplitter
)

from modules.bases import ToolBase, ToolCategory
from core.tgtinput import TargetInput, parse_targets
from core.fileops import create_target_dirs, get_group_name_from_file
from core import reportgen as report
from ui.styles import (
    COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR, COLOR_INFO,
    RunButton, StopButton, SafeStop, OutputView, StyledToolView,
    OutputHelper, StyledCheckBox, StyledSpinBox, ToolSplitter,
    StyledLabel, HeaderLabel, StyledGroupBox, StyledComboBox
)


class Status:
    """Pipeline step statuses with emoji indicators"""
    PENDING = "⏳ Pending"
    RUNNING = "🔄 Running"
    COMPLETED = "✅ Completed"
    SKIPPED = "⏭️ Skipped"
    ERROR = "❌ Error"
    TERMINATED = "⛔ Stopped"


class AutomationConfig:
    """Configuration for all automation tools"""
    def __init__(self):
        # Subdomain enumeration
        self.subfinder_enabled = True
        self.subfinder_timeout = 30
        
        self.theharvester_enabled = True
        self.theharvester_sources = "baidu,bing,duckduckgo,google"
        self.theharvester_limit = 500
        
        self.chaos_enabled = True
        self.sublist3r_enabled = True
        
        # HTTPX Configuration
        self.httpx_threads = 50
        self.httpx_timeout = 10
        
        # Nmap Configuration
        self.nmap_preset = "default"
        
        # Additional Tools
        self.eyewitness_enabled = True
        self.nuclei_enabled = True
        self.nuclei_severity = "critical,high,medium"
        self.nikto_enabled = False  # Disabled by default (slow)
        
        # General
        self.parallel_subdomain = True
        self.max_workers = 3


class AutomationWorker(QThread):
    """Worker thread for executing the automation pipeline"""
    
    status_update = Signal(str, str)  # step_key, status
    output = Signal(str)  # output text
    progress = Signal(int, str)  # percentage, message
    finished = Signal()
    error = Signal(str)
    stats_update = Signal(dict)  # statistics
    tool_result = Signal(str, dict)  # tool_name, results
    
    def __init__(self, targets, base_dirs, config, main_window):
        super().__init__()
        self.targets = targets
        self.base_dirs = base_dirs
        self.config = config
        self.main_window = main_window
        
        self.current_process = None
        self.is_running = True
        self.is_skipping = False
        
        self.stats = defaultdict(dict)
        self.start_time = None
        self.current_step = None
        
        # Results storage
        self.results = defaultdict(dict)
    
    def run(self):
        """Execute the complete bug bounty pipeline"""
        self.start_time = time.time()
        
        for target_idx, (target, base_dir) in enumerate(zip(self.targets, self.base_dirs)):
            if not self.is_running:
                break
            
            self.output.emit(f'\n<h2 style="color:#3B82F6; border-bottom:2px solid #3B82F6; padding:10px;">🎯 TARGET {target_idx + 1}/{len(self.targets)}: {target}</h2><br>')
            
            # Pipeline steps
            pipeline = [
                {"key": "whois", "name": "Whois Lookup", "func": lambda: self._run_whois(target, base_dir), "enabled": True},
                {"key": "dig", "name": "DNS Records", "func": lambda: self._run_dig(target, base_dir), "enabled": True},
                {"key": "subdomain", "name": "Subdomain Enumeration", "func": lambda: self._run_subdomain_enumeration(target, base_dir), "enabled": True},
                {"key": "httpx", "name": "HTTP Probing", "func": lambda: self._run_httpx(target, base_dir), "enabled": True},
                {"key": "nmap", "name": "Port Scanning", "func": lambda: self._run_nmap(target, base_dir), "enabled": True},
                {"key": "eyewitness", "name": "Screenshots", "func": lambda: self._run_eyewitness(target, base_dir), "enabled": self.config.eyewitness_enabled},
                {"key": "nuclei", "name": "Nuclei Scan", "func": lambda: self._run_nuclei(target, base_dir), "enabled": self.config.nuclei_enabled},
                {"key": "nikto", "name": "Nikto Scan", "func": lambda: self._run_nikto(target, base_dir), "enabled": self.config.nikto_enabled},
                {"key": "report", "name": "Report Generation", "func": lambda: self._run_reportgen(target, base_dir), "enabled": True},
            ]
            
            for step_idx, step in enumerate(pipeline):
                if not self.is_running:
                    self.output.emit(f'<br><span style="color:{COLOR_ERROR}; font-size:16px; font-weight:bold;">⛔ Pipeline stopped by user</span><br>')
                    break
                
                # Skip disabled steps
                if not step["enabled"]:
                    self.status_update.emit(step["key"], Status.SKIPPED)
                    continue
                
                self.current_step = step["key"]
                progress_pct = int((step_idx / len(pipeline)) * 100)
                self.progress.emit(progress_pct, f"{step['name']}...")
                
                # Handle skip request
                if self.is_skipping:
                    self.status_update.emit(step["key"], Status.SKIPPED)
                    self.output.emit(f'<span style="color:{COLOR_WARNING}; font-weight:bold;">⏭️ {step["name"]} skipped by user</span><br>')
                    self.is_skipping = False
                    continue
                
                # Execute step
                self.status_update.emit(step["key"], Status.RUNNING)
                self.output.emit(f'<br><div style="background:#1a1a2e; padding:10px; border-left:4px solid #3B82F6; margin:5px 0;"><b>▶️ {step["name"]}</b></div>')
                
                step_start = time.time()
                
                try:
                    success = step["func"]()
                except Exception as e:
                    self.output.emit(f'<span style="color:{COLOR_ERROR};">💥 Exception: {str(e)}</span><br>')
                    success = False
                
                elapsed = time.time() - step_start
                
                # Update status
                if success is None:
                    self.status_update.emit(step["key"], Status.SKIPPED)
                elif not self.is_running:
                    self.status_update.emit(step["key"], Status.TERMINATED)
                    break
                elif success:
                    self.status_update.emit(step["key"], Status.COMPLETED)
                    self.output.emit(f'<span style="color:{COLOR_SUCCESS}; font-size:14px; font-weight:bold;">✅ {step["name"]} completed in {elapsed:.1f}s</span><br>')
                else:
                    self.status_update.emit(step["key"], Status.ERROR)
                    self.output.emit(f'<span style="color:{COLOR_ERROR}; font-size:14px; font-weight:bold;">❌ {step["name"]} failed</span><br>')
            
            # Export results
            self._export_results_json(target, base_dir)
            
            # Show summary in results section
            self._show_results_summary(target, base_dir)
        
        total_time = time.time() - self.start_time
        self.progress.emit(100, f"Completed in {int(total_time//60)}m {int(total_time%60)}s")
        
        # Send notification
        # Send notification code removed per user request
        
        self.finished.emit()
    
    def stop(self):
        """Stop the pipeline gracefully"""
        self.is_running = False
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=3)
            except:
                try:
                    self.current_process.kill()
                except:
                    pass
        self.output.emit(f'<br><span style="color:{COLOR_WARNING}; font-size:16px; font-weight:bold;">⛔ Stopping automation...</span><br>')
    
    def skip(self):
        """Skip current step"""
        self.is_skipping = True
        if self.current_process:
            try:
                self.current_process.terminate()
            except:
                pass
        self.output.emit(f'<span style="color:{COLOR_WARNING}; font-weight:bold;">⏭️ Skipping {self.current_step}...</span><br>')
    
    def _execute_command(self, cmd, log_path, tool_name="", shell=False):
        """Execute command with proper error handling"""
        if not self.is_running or self.is_skipping:
            return None
        
        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            
            self.current_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, shell=shell, bufsize=1
            )
            
            output_lines = []
            with open(log_path, "w") as f:
                for line in iter(self.current_process.stdout.readline, ""):
                    if not self.is_running:
                        self.current_process.terminate()
                        return None
                    if self.is_skipping:
                        self.current_process.terminate()
                        return None
                    
                    # Show important lines only
                    if any(keyword in line.lower() for keyword in ['error', 'warning', 'found', 'discovered', 'detected', 'vulnerability']):
                        self.output.emit(f'<span style="color:#9CA3AF; font-family:monospace; font-size:12px;">{html.escape(line.rstrip())}</span><br>')
                    
                    output_lines.append(line)
                    f.write(line)
            
            self.current_process.wait()
            
            if not self.is_running or self.is_skipping:
                return None
            
            self.current_process = None
            return self.current_process.returncode == 0 if self.current_process else True
            
        except FileNotFoundError:
            self.error.emit(f"❌ {tool_name or cmd[0]} not found in PATH")
            return False
        except Exception as e:
            self.error.emit(f"❌ Error: {str(e)}")
            return False
        finally:
            self.current_process = None
    
    def _run_whois(self, target, base_dir):
        """Run whois lookup"""
        self.output.emit(f'<span style="color:{COLOR_INFO};">📋 Querying WHOIS database...</span><br>')
        log_file = os.path.join(base_dir, "Logs", "whois.txt")
        result = self._execute_command(["whois", target], log_file, "whois")
        
        if result and os.path.exists(log_file):
            size = os.path.getsize(log_file)
            self.output.emit(f'<span style="color:{COLOR_SUCCESS};">✓ Saved {size} bytes to whois.txt</span><br>')
        
        return result
    
    def _run_dig(self, target, base_dir):
        """Run comprehensive DNS lookup"""
        self.output.emit(f'<span style="color:{COLOR_INFO}; font-weight:bold;">🌐 Performing comprehensive DNS lookup...</span><br>')
        log_file = os.path.join(base_dir, "Logs", "dig.txt")
        
        # Run dig for common record types
        record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']
        
        all_success = True
        with open(log_file, 'w') as f:
            for record_type in record_types:
                if not self.is_running:
                    return None
                
                self.output.emit(f'<span style="color:#60A5FA;">  ▶️ Querying {record_type} records...</span><br>')
                
                try:
                    proc = subprocess.Popen(
                        ['dig', target, record_type, '+noall', '+answer'],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
                    )
                    
                    output, _ = proc.communicate(timeout=10)
                    f.write(f"\n=== {record_type} RECORDS ===\n")
                    f.write(output)
                    f.write("\n")
                    
                    # Count results
                    result_count = len([line for line in output.split('\n') if line.strip() and not line.startswith(';')])
                    if result_count > 0:
                        self.output.emit(f'<span style="color:{COLOR_SUCCESS};">    ✓ Found {result_count} {record_type} record(s)</span><br>')
                    
                except subprocess.TimeoutExpired:
                    proc.kill()
                    all_success = False
                except Exception as e:
                    all_success = False
        
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            self.output.emit(f'<span style="color:{COLOR_SUCCESS}; font-weight:bold;">✓ DNS lookup complete, saved to dig.txt ({size} bytes)</span><br>')
        
        return all_success
    
    def _run_subdomain_enumeration(self, target, base_dir):
        self.output.emit(f'<span style="color:{COLOR_INFO}; font-size:14px; font-weight:bold;">🌐 Running Subdomain Enumeration Tools in Parallel...</span><br>')
        
        logs_dir = os.path.join(base_dir, "Logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        tools = []
        
        # Build tool list based on config
        if self.config.subfinder_enabled:
            tools.append({
                'name': 'Subfinder',
                'cmd': ["subfinder", "-d", target, "-o", os.path.join(logs_dir, "subfinder.txt"), "-silent"],
                'log': os.path.join(logs_dir, "subfinder.txt"),
                'icon': '🔍'
            })
        
        if self.config.theharvester_enabled:
            tools.append({
                'name': 'theHarvester',
                'cmd': ["theHarvester", "-d", target, "-b", self.config.theharvester_sources, 
                       "-l", str(self.config.theharvester_limit), "-f", os.path.join(logs_dir, "theharvester")],
                'log': os.path.join(logs_dir, "theharvester.txt"),
                'icon': '🌾'
            })
        
        if self.config.chaos_enabled:
            tools.append({
                'name': 'Chaos',
                'cmd': ["chaos", "-d", target, "-o", os.path.join(logs_dir, "chaos.txt"), "-silent"],
                'log': os.path.join(logs_dir, "chaos.txt"),
                'icon': '⚡'
            })
        
        if self.config.sublist3r_enabled:
            tools.append({
                'name': 'Sublist3r',
                'cmd': ["sublist3r", "-d", target, "-o", os.path.join(logs_dir, "sublist3r.txt")],
                'log': os.path.join(logs_dir, "sublist3r.txt"),
                'icon': '📝'
            })
        
        if not tools:
            self.error.emit("No subdomain enumeration tools enabled!")
            return False
        
        # Show which tools are running
        tool_names = ", ".join([f"{t['icon']} {t['name']}" for t in tools])
        self.output.emit(f'<div style="background:#0f3460; padding:8px; border-radius:4px; margin:5px 0;">Running {len(tools)} tools: {tool_names}</div>')
        
        # Execute in parallel
        results = []
        tool_results = {}
        
        if self.config.parallel_subdomain:
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = {}
                for tool in tools:
                    self.output.emit(f'<span style="color:#60A5FA;">{tool["icon"]} Starting {tool["name"]}...</span><br>')
                    future = executor.submit(self._execute_command, tool['cmd'], tool['log'], tool['name'])
                    futures[future] = tool
                
                for future in as_completed(futures):
                    tool = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                        
                        # Count results
                        count = 0
                        if result and os.path.exists(tool['log']):
                            try:
                                with open(tool['log'], 'r') as f:
                                    count = len([line for line in f if line.strip() and not line.startswith('#')])
                            except:
                                pass
                        
                        tool_results[tool['name']] = count
                        
                        if result:
                            self.output.emit(f'<span style="color:{COLOR_SUCCESS}; font-weight:bold;">{tool["icon"]} ✓ {tool["name"]}: {count} subdomains</span><br>')
                        else:
                            self.output.emit(f'<span style="color:{COLOR_WARNING};">{tool["icon"]} ⚠ {tool["name"]}: Failed</span><br>')
                    except Exception as e:
                        self.output.emit(f'<span style="color:{COLOR_ERROR};">{tool["icon"]} ✗ {tool["name"]}: {str(e)}</span><br>')
                        results.append(False)
        else:
            # Sequential execution
            for tool in tools:
                if not self.is_running:
                    break
                self.output.emit(f'<span style="color:#60A5FA;">{tool["icon"]} Running {tool["name"]}...</span><br>')
                result = self._execute_command(tool['cmd'], tool['log'], tool['name'])
                results.append(result)
        
        # Merge subdomains
        merged_file = self._merge_subdomains(logs_dir, target)
        
        # Count results
        subdomain_count = 0
        if os.path.exists(merged_file):
            with open(merged_file, 'r') as f:
                subdomain_count = len(f.readlines())
        
        self.stats[target]['subdomains_found'] = subdomain_count
        self.stats[target]['subdomain_tools'] = tool_results
        self.stats_update.emit(self.stats)
        
        # Show detailed results - combine into single HTML string
        tool_rows = "".join([f'<tr><td style="padding:5px;"><b>{tool_name}:</b></td><td style="color:#3B82F6; font-weight:bold;">{count} domains</td></tr>' for tool_name, count in tool_results.items()])
        
        subdomain_html = f'''
<br><div style="background:#16213e; padding:15px; border-radius:8px; border:2px solid #3B82F6;">
<h3 style="color:#3B82F6; margin:0;">📊 Subdomain Enumeration Results</h3>
<table style="width:100%; margin-top:10px; color:#E5E7EB;">
{tool_rows}
<tr style="border-top:2px solid #3B82F6;"><td style="padding:5px; padding-top:10px;"><b>Total Unique:</b></td><td style="color:#10B981; font-weight:bold; font-size:18px; padding-top:10px;">{subdomain_count}</td></tr>
</table>
</div>'''
        self.output.emit(subdomain_html)
        
        return subdomain_count > 0 or any(results)
    
    def _merge_subdomains(self, logs_dir, target):
        """Merge and deduplicate all subdomain files"""
        self.output.emit(f'<span style="color:{COLOR_INFO};">🔗 Merging and deduplicating subdomains...</span><br>')
        
        all_subdomains = set()
        
        for filename in os.listdir(logs_dir):
            if filename.endswith('.txt') and filename not in ['subdomains.txt', 'whois.txt', 'alive.txt', 'httpx.txt', 'nmap.txt']:
                filepath = os.path.join(logs_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        for line in f:
                            subdomain = line.strip()
                            if subdomain and '.' in subdomain and not subdomain.startswith('#'):
                                all_subdomains.add(subdomain.lower())
                except:
                    pass
        
        # Always include the target itself (handles IPs and main domain)
        if target:
            all_subdomains.add(target.lower())
        
        merged_file = os.path.join(logs_dir, "subdomains.txt")
        with open(merged_file, 'w') as f:
            for subdomain in sorted(all_subdomains):
                f.write(f"{subdomain}\n")
        
        return merged_file
    
    def _run_httpx(self, target, base_dir):
        """Run HTTPX to probe live subdomains"""
        subdomain_file = os.path.join(base_dir, "Logs", "subdomains.txt")
        
        if not os.path.exists(subdomain_file):
            self.error.emit("❌ No subdomains.txt file found")
            return False
        
        # Count total subdomains
        with open(subdomain_file, 'r') as f:
            total = len(f.readlines())
        
        if total == 0:
            self.error.emit("❌ No subdomains to probe")
            return False
        
        self.output.emit(f'<span style="color:{COLOR_INFO}; font-weight:bold;">🌐 Probing {total} subdomains with HTTPX...</span><br>')
        
        alive_file = os.path.join(base_dir, "Logs", "alive.txt")
        log_file = os.path.join(base_dir, "Logs", "httpx.txt")
        
        cmd = [
            "httpx-toolkit", "-l", subdomain_file,
            "-o", alive_file,
            "-threads", str(self.config.httpx_threads),
            "-timeout", str(self.config.httpx_timeout),
            "-silent", "-no-color"
        ]
        
        result = self._execute_command(cmd, log_file, "HTTPX")
        
        # Count live hosts
        live_count = 0
        if os.path.exists(alive_file):
            with open(alive_file, 'r') as f:
                live_count = len(f.readlines())
        
        self.stats[target]['live_hosts'] = live_count
        self.stats[target]['total_subdomains'] = total
        self.stats_update.emit(self.stats)
        
        percentage = (live_count / total * 100) if total > 0 else 0
        
        http_html = f'''
<br><div style="background:#16213e; padding:15px; border-radius:8px; border:2px solid #10B981;">
<h3 style="color:#10B981; margin:0;">🎯 HTTP Probing Results</h3>
<p style="font-size:18px; color:#E5E7EB; margin:10px 0;"><b>Live Hosts:</b> <span style="color:#10B981; font-size:24px; font-weight:bold;">{live_count}</span> / {total} ({percentage:.1f}%)</p>
<p style="color:#9CA3AF; margin:5px 0;">Saved to: <code>Logs/alive.txt</code></p>
</div>'''
        self.output.emit(http_html)
        
        return result
    
    def _run_nmap(self, target, base_dir):
        """Run Nmap port scanning"""
        alive_file = os.path.join(base_dir, "Logs", "alive.txt")
        
        if not os.path.exists(alive_file) or os.path.getsize(alive_file) == 0:
            # Fallback to subdomains.txt which definitely contains the target now
            sub_file = os.path.join(base_dir, "Logs", "subdomains.txt")
            if os.path.exists(sub_file) and os.path.getsize(sub_file) > 0:
                self.output.emit(f'<span style="color:{COLOR_INFO};">ℹ️ No web-alive hosts found. Falling back to target list for Nmap...</span><br>')
                alive_file = sub_file
            else:
                self.output.emit(f'<span style="color:{COLOR_WARNING};">⚠ No hosts to scan - Skipped</span><br>')
                return None  # Skipped
        
        with open(alive_file, 'r') as f:
            host_count = len(f.readlines())
        
        if host_count == 0:
            self.output.emit(f'<span style="color:{COLOR_WARNING};">⚠ No live hosts to scan - Skipped</span><br>')
            return None  # Skipped
        
        # Nmap presets
        presets = {
            "default": {"name": "Top 1000 TCP Ports", "args": ["-sS", "-T4", "--top-ports=1000"]},
            "fast": {"name": "Top 100 TCP Ports (Fast)", "args": ["-sS", "-T5", "--top-ports=100", "-Pn"]},
            "full": {"name": "Full TCP Scan (All 65535 ports)", "args": ["-sS", "-T4", "-p-"]},
            "udp_default": {"name": "Top 1000 UDP Ports", "args": ["-sU", "-T4", "--top-ports=1000"]},
            "udp_fast": {"name": "Top 100 UDP Ports", "args": ["-sU", "-T5", "--top-ports=100", "-Pn"]},
            "udp_full": {"name": "UDP + TCP Full Scan", "args": ["-sS", "-sU", "-T4", "--top-ports=1000"]}
        }
        
        preset = presets.get(self.config.nmap_preset, presets["default"])
        
        self.output.emit(f'<span style="color:{COLOR_INFO}; font-weight:bold;">🔍 Running Nmap: {preset["name"]}</span><br>')
        self.output.emit(f'<span style="color:#9CA3AF;">Scanning {host_count} live hosts...</span><br>')
        
        nmap_out = os.path.join(base_dir, "Logs", "nmap")
        log_file = os.path.join(base_dir, "Logs", "nmap.txt")
        
        # Create clean hosts file for nmap (extract hostnames from URLs)
        nmap_hosts_file = os.path.join(base_dir, "Logs", "nmap_hosts.txt")
        with open(alive_file, 'r') as f_in, open(nmap_hosts_file, 'w') as f_out:
            for line in f_in:
                url = line.strip()
                if url:
                    # Extract hostname from URL (remove protocol and port)
                    host = url.replace('http://', '').replace('https://', '').split(':')[0].split('/')[0]
                    if host:
                        f_out.write(f"{host}\n")
        
        cmd = ["nmap", "-iL", nmap_hosts_file] + preset["args"] + ["-oA", nmap_out]
        
        result = self._execute_command(cmd, log_file, "Nmap")
        
        if result and os.path.exists(nmap_out + ".xml"):
            size = os.path.getsize(nmap_out + ".xml")
            self.output.emit(f'<span style="color:{COLOR_SUCCESS};">✓ Scan complete, results saved to Logs/nmap.* ({size} bytes)</span><br>')
        
        return result
    
    def _run_eyewitness(self, target, base_dir):
        """Run EyeWitness for screenshots"""
        if not self.config.eyewitness_enabled:
            return None
        
        alive_file = os.path.join(base_dir, "Logs", "alive.txt")
        
        if not os.path.exists(alive_file) or os.path.getsize(alive_file) == 0:
            self.output.emit(f'<span style="color:{COLOR_WARNING};">⚠ No live hosts for screenshots - Skipped</span><br>')
            return None  # Skipped
        
        with open(alive_file, 'r') as f:
            count = len(f.readlines())
        
        self.output.emit(f'<span style="color:{COLOR_INFO}; font-weight:bold;">📸 Capturing screenshots of {count} hosts...</span><br>')
        
        screenshots_dir = os.path.join(base_dir, "Screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        
        log_file = os.path.join(base_dir, "Logs", "eyewitness.txt")
        
        cmd = ["eyewitness", "-f", alive_file, "-d", screenshots_dir, "--no-prompt", "--web"]
        
        result = self._execute_command(cmd, log_file, "EyeWitness")
        
        if result:
            self.output.emit(f'<span style="color:{COLOR_SUCCESS};">✓ Screenshots saved to Screenshots/</span><br>')
        
        return result
    
    def _run_nuclei(self, target, base_dir):
        """Run Nuclei vulnerability scanner"""
        if not self.config.nuclei_enabled:
            return None
        
        alive_file = os.path.join(base_dir, "Logs", "alive.txt")
        
        if not os.path.exists(alive_file) or os.path.getsize(alive_file) == 0:
            self.output.emit(f'<span style="color:{COLOR_WARNING};">⚠ No live hosts for vulnerability scanning - Skipped</span><br>')
            return None  # Return None to show as "Skipped" not "Error"
        
        with open(alive_file, 'r') as f:
            count = len(f.readlines())
        
        self.output.emit(f'<span style="color:{COLOR_INFO}; font-weight:bold;">⚠️ Scanning {count} hosts with Nuclei ({self.config.nuclei_severity})...</span><br>')
        
        nuclei_output = os.path.join(base_dir, "Logs", "nuclei.txt")
        
        cmd = [
            "nuclei", "-l", alive_file,
            "-severity", self.config.nuclei_severity,
            "-o", nuclei_output,
            "-silent", "-no-color"
        ]
        
        result = self._execute_command(cmd, nuclei_output, "Nuclei")
        
        # Parse findings with severity breakdown
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        nuclei_details = []
        
        if os.path.exists(nuclei_output):
            with open(nuclei_output, 'r') as f:
                for line in f:
                    line_lower = line.lower()
                    finding = {'line': line.strip(), 'severity': 'info'}
                    
                    # Parse severity from nuclei output format: [severity] or [critical] etc
                    if '[critical]' in line_lower:
                        severity_counts['critical'] += 1
                        finding['severity'] = 'critical'
                    elif '[high]' in line_lower:
                        severity_counts['high'] += 1
                        finding['severity'] = 'high'
                    elif '[medium]' in line_lower:
                        severity_counts['medium'] += 1
                        finding['severity'] = 'medium'
                    elif '[low]' in line_lower:
                        severity_counts['low'] += 1
                        finding['severity'] = 'low'
                    else:
                        severity_counts['info'] += 1
                    
                    nuclei_details.append(finding)
        
        total_findings = sum(severity_counts.values())
        
        # Store in stats for report
        self.stats[target]['nuclei_findings'] = total_findings
        self.stats[target]['nuclei_severity'] = severity_counts
        self.stats[target]['nuclei_details'] = nuclei_details
        self.stats_update.emit(self.stats)
        
        # CVSS-based colors
        # Critical (9.0-10.0): #7f1d1d bg, #DC2626 text
        # High (7.0-8.9): #991b1b bg, #EF4444 text  
        # Medium (4.0-6.9): #78350f bg, #F59E0B text
        # Low (0.1-3.9): #1e3a5f bg, #3B82F6 text
        # Info (0.0): #1f2937 bg, #6B7280 text
        
        if total_findings > 0:
            nuclei_html = f'''
<div style="background:#7f1d1d; padding:15px; border-radius:8px; border:2px solid #DC2626; margin:10px 0;">
<h3 style="color:#DC2626; margin:0;">⚠️ Nuclei Vulnerability Scan Results</h3>
<table style="margin-top:10px;"><tr>
<td style="background:#450a0a; padding:10px 20px; border-radius:6px; text-align:center;"><div style="color:#DC2626; font-size:24px; font-weight:bold;">{severity_counts['critical']}</div><div style="color:#FCA5A5;">Critical</div><div style="color:#9CA3AF; font-size:10px;">CVSS 9.0-10.0</div></td>
<td style="background:#7f1d1d; padding:10px 20px; border-radius:6px; text-align:center;"><div style="color:#EF4444; font-size:24px; font-weight:bold;">{severity_counts['high']}</div><div style="color:#FCA5A5;">High</div><div style="color:#9CA3AF; font-size:10px;">CVSS 7.0-8.9</div></td>
<td style="background:#78350f; padding:10px 20px; border-radius:6px; text-align:center;"><div style="color:#F59E0B; font-size:24px; font-weight:bold;">{severity_counts['medium']}</div><div style="color:#FCD34D;">Medium</div><div style="color:#9CA3AF; font-size:10px;">CVSS 4.0-6.9</div></td>
<td style="background:#1e3a5f; padding:10px 20px; border-radius:6px; text-align:center;"><div style="color:#3B82F6; font-size:24px; font-weight:bold;">{severity_counts['low']}</div><div style="color:#93C5FD;">Low</div><div style="color:#9CA3AF; font-size:10px;">CVSS 0.1-3.9</div></td>
<td style="background:#1f2937; padding:10px 20px; border-radius:6px; text-align:center; border:1px solid #374151;"><div style="color:#6B7280; font-size:24px; font-weight:bold;">{severity_counts['info']}</div><div style="color:#9CA3AF;">Info</div><div style="color:#6B7280; font-size:10px;">CVSS 0.0</div></td>
</tr></table>
<p style="color:#9CA3AF; margin:10px 0 0 0;">Total: <b style="color:#E5E7EB;">{total_findings}</b> vulnerabilities saved to <code>Logs/nuclei.txt</code></p>
</div>'''
            self.output.emit(nuclei_html)
        else:
            self.output.emit(f'<span style="color:{COLOR_SUCCESS};">✓ No vulnerabilities found</span><br>')
        
        return result
    
    def _run_nikto(self, target, base_dir):
        """Run Nikto web server scanner"""
        if not self.config.nikto_enabled:
            return None
        
        alive_file = os.path.join(base_dir, "Logs", "alive.txt")
        
        if not os.path.exists(alive_file) or os.path.getsize(alive_file) == 0:
            self.output.emit(f'<span style="color:{COLOR_WARNING};">⚠ No live hosts for Nikto scan - Skipped</span><br>')
            return None  # Skipped, not Error
        
        self.output.emit(f'<span style="color:{COLOR_INFO}; font-weight:bold;">🔧 Running Nikto (first 3 hosts, slow)...</span><br>')
        
        nikto_output = os.path.join(base_dir, "Logs", "nikto.txt")
        
        hosts = []
        with open(alive_file, 'r') as f:
            hosts = [line.strip() for line in f.readlines()[:3]]
        
        if not hosts:
            self.output.emit(f'<span style="color:{COLOR_WARNING};">⚠ No hosts available for Nikto - Skipped</span><br>')
            return None  # Skipped
        
        all_success = True
        nikto_findings = []
        
        with open(nikto_output, 'w') as out_file:
            for idx, host in enumerate(hosts, 1):
                if not self.is_running:
                    break
                
                self.output.emit(f'<span style="color:#60A5FA;">📍 Nikto scan {idx}/{len(hosts)}: {host}</span><br>')
                
                try:
                    proc = subprocess.Popen(
                        ["nikto", "-h", host],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
                    )
                    
                    for line in iter(proc.stdout.readline, ""):
                        if not self.is_running:
                            proc.terminate()
                            break
                        out_file.write(line)
                        
                        # Parse findings
                        if "+ " in line and "OSVDB" in line:
                            nikto_findings.append({'host': host, 'finding': line.strip(), 'severity': 'medium'})
                        elif "+ " in line and any(kw in line.lower() for kw in ['vulnerability', 'outdated', 'error', 'xss', 'sql']):
                            nikto_findings.append({'host': host, 'finding': line.strip(), 'severity': 'high'})
                        elif "+ " in line:
                            nikto_findings.append({'host': host, 'finding': line.strip(), 'severity': 'info'})
                    
                    proc.wait()
                except Exception as e:
                    self.output.emit(f'<span style="color:{COLOR_ERROR};">✗ {host}: {str(e)}</span><br>')
                    all_success = False
        
        # Store findings for report with severity breakdown
        high_count = len([f for f in nikto_findings if f['severity'] == 'high'])
        medium_count = len([f for f in nikto_findings if f['severity'] == 'medium'])
        info_count = len([f for f in nikto_findings if f['severity'] == 'info'])
        
        self.stats[target]['nikto_findings'] = len(nikto_findings)
        self.stats[target]['nikto_severity'] = {'high': high_count, 'medium': medium_count, 'info': info_count}
        self.stats[target]['nikto_details'] = nikto_findings
        self.stats_update.emit(self.stats)
        
        # Display styled summary with CVSS labels (like Nuclei)
        if nikto_findings:
            nikto_html = f'''
<div style="background:#1e3a5f; padding:15px; border-radius:8px; border:2px solid #3B82F6; margin:10px 0;">
<h3 style="color:#3B82F6; margin:0;">🔧 Nikto Web Server Scan Results</h3>
<table style="margin-top:10px;"><tr>
<td style="background:#7f1d1d; padding:10px 20px; border-radius:6px; text-align:center;"><div style="color:#EF4444; font-size:24px; font-weight:bold;">{high_count}</div><div style="color:#FCA5A5;">High</div><div style="color:#9CA3AF; font-size:10px;">CVSS 7.0-8.9</div></td>
<td style="background:#78350f; padding:10px 20px; border-radius:6px; text-align:center;"><div style="color:#F59E0B; font-size:24px; font-weight:bold;">{medium_count}</div><div style="color:#FCD34D;">Medium</div><div style="color:#9CA3AF; font-size:10px;">CVSS 4.0-6.9</div></td>
<td style="background:#1f2937; padding:10px 20px; border-radius:6px; text-align:center; border:1px solid #374151;"><div style="color:#6B7280; font-size:24px; font-weight:bold;">{info_count}</div><div style="color:#9CA3AF;">Info</div><div style="color:#6B7280; font-size:10px;">CVSS 0.0</div></td>
</tr></table>
<p style="color:#9CA3AF; margin:10px 0 0 0;">Total: <b style="color:#E5E7EB;">{len(nikto_findings)}</b> findings saved to <code>Logs/nikto.txt</code></p>
</div>'''
            self.output.emit(nikto_html)
        else:
            self.output.emit(f'<span style="color:{COLOR_SUCCESS};">✓ Nikto scan complete - No significant findings</span><br>')
        
        return all_success
    
    def _run_reportgen(self, target, base_dir):
        """Generate final HTML report"""
        self.output.emit(f'<span style="color:{COLOR_INFO}; font-weight:bold;">📝 Generating HTML report...</span><br>')
        
        try:
            # Build module list based on what ran
            modules_run = ["whois"]
            
            if any(k in self.stats.get(target, {}) for k in ['subdomains_found']):
                modules_run.extend(["subfinder", "theharvester", "chaos", "sublist3r"])
            
            if 'live_hosts' in self.stats.get(target, {}):
                modules_run.append("httpx")
            
            # Check if nmap files exist
            nmap_xml = os.path.join(base_dir, "Logs", "nmap.xml")
            if os.path.exists(nmap_xml):
                modules_run.append("nmap")
            
            if self.config.eyewitness_enabled:
                modules_run.append("eyewitness")
            
            if self.config.nuclei_enabled:
                modules_run.append("nuclei")
            
            if self.config.nikto_enabled:
                modules_run.append("nikto")
            
            modules_str = " ".join(modules_run)
            
            # Call report generator
            report.generate_report(target, base_dir, modules_str)
            
            # Find the generated report
            reports_dir = os.path.join(base_dir, "Reports")
            if os.path.exists(reports_dir):
                reports = [f for f in os.listdir(reports_dir) if f.endswith('.html')]
                if reports:
                    report_path = os.path.join(reports_dir, reports[0])
                    report_html = f'''
<br><div style="background:#16213e; padding:15px; border-radius:8px; border:2px solid #10B981;">
<h3 style="color:#10B981; margin:0;">📝 Report Generated Successfully</h3>
<p style="color:#E5E7EB; margin:10px 0;">Location: <code>{report_path}</code></p>
</div>'''
                    self.output.emit(report_html)
                    return True
            
            self.output.emit(f'<span style="color:{COLOR_SUCCESS};">✓ Report generation completed</span><br>')
            return True
            
        except Exception as e:
            self.error.emit(f"Report generation failed: {str(e)}")
            self.output.emit(f'<span style="color:{COLOR_ERROR};">✗ Report generation failed: {str(e)}</span><br>')
            return False
    
    def _export_results_json(self, target, base_dir):
        """Export results to JSON"""
        results = {
            'target': target,
            'scan_date': datetime.now().isoformat(),
            'scan_duration': time.time() - self.start_time if self.start_time else 0,
            'configuration': {
                'nmap_preset': self.config.nmap_preset,
                'parallel_subdomain': self.config.parallel_subdomain,
                'tools_enabled': {
                    'subfinder': self.config.subfinder_enabled,
                    'theharvester': self.config.theharvester_enabled,
                    'chaos': self.config.chaos_enabled,
                    'sublist3r': self.config.sublist3r_enabled,
                    'eyewitness': self.config.eyewitness_enabled,
                    'nuclei': self.config.nuclei_enabled,
                    'nikto': self.config.nikto_enabled
                }
            },
            'statistics': dict(self.stats.get(target, {})),
            'files': {
                'subdomains': os.path.join(base_dir, "Logs", "subdomains.txt"),
                'alive_hosts': os.path.join(base_dir, "Logs", "alive.txt"),
                'nmap_scan': os.path.join(base_dir, "Logs", "nmap.xml"),
                'nuclei_results': os.path.join(base_dir, "Logs", "nuclei.txt"),
                'screenshots': os.path.join(base_dir, "Screenshots")
            }
        }
        
        json_file = os.path.join(base_dir, "automation_results.json")
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.output.emit(f'<span style="color:#9CA3AF;">💾 Results JSON: {json_file}</span><br>')
    
    def _show_results_summary(self, target, base_dir):
        """Show final summary in output"""
        stats = self.stats.get(target, {})
        
        # Check for HTML report
        report_path = ""
        reports_dir = os.path.join(base_dir, "Reports")
        if os.path.exists(reports_dir):
            reports = [f for f in os.listdir(reports_dir) if f.endswith('.html')]
            if reports:
                report_path = f"Reports/{reports[0]}"
        
        # Build nikto line if enabled
        nikto_line = ""
        if self.config.nikto_enabled:
            nikto_line = f'<tr><td style="padding:8px;"><b>🔧 Nikto Findings:</b></td><td style="color:#F59E0B; font-weight:bold; font-size:18px;">{stats.get("nikto_findings", 0)}</td></tr>'
        
        # Build Nmap line
        nmap_line = ""
        nmap_file = os.path.join(base_dir, "Logs", "nmap.xml")
        if os.path.exists(nmap_file):
            nmap_line = f'<tr><td style="padding:8px;"><b>🔍 Nmap Ports:</b></td><td style="color:#3B82F6; font-weight:bold; font-size:18px;">Scan Complete</td></tr>'
        
        # Single combined HTML output
        summary_html = f'''
<div style="background:#0f172a; padding:20px; border-radius:10px; border:3px solid #3B82F6; margin:20px 0;">
<h2 style="color:#3B82F6; margin:0 0 15px 0; font-size:18px;">📊 AUTOMATION SUMMARY</h2>
<div style="background: linear-gradient(135deg, #3B82F6, #8B5CF6); padding: 12px; border-radius: 8px; margin-bottom: 15px;">
<span style="color: white; font-size: 14px; font-weight: bold;">🎯 Target: {html.escape(target)}</span>
</div>
<table style="width:100%; color:#E5E7EB; font-size:14px;">
<tr><td style="padding:8px;"><b>🌐 Subdomains Found:</b></td><td style="color:#10B981; font-weight:bold; font-size:18px;">{stats.get("subdomains_found", 0)}</td></tr>
<tr><td style="padding:8px;"><b>📡 Live Hosts:</b></td><td style="color:#10B981; font-weight:bold; font-size:18px;">{stats.get("live_hosts", 0)}</td></tr>
<tr><td style="padding:8px;"><b>⚠️ Nuclei Vulnerabilities:</b></td><td style="color:#DC2626; font-weight:bold; font-size:18px;">{stats.get("nuclei_findings", 0)}</td></tr>
{nikto_line}
{nmap_line}
</table>
<hr style="border: 1px solid #334155; margin: 15px 0;">
<div style="color:#9CA3AF; font-size:13px;">
<div style="padding:5px;"><b>📁 Base Directory:</b> <span style="color:#60A5FA;">{html.escape(base_dir)}</span></div>
<div style="padding:5px;">• Subdomains: Logs/subdomains.txt</div>
<div style="padding:5px;">• Live Hosts: Logs/alive.txt</div>
<div style="padding:5px;">• Nmap Results: Logs/nmap.*</div>
<div style="padding:5px;">• Nuclei Results: Logs/nuclei.txt</div>
{f'<div style="padding:5px;">• Nikto Scan: Logs/nikto.txt</div>' if self.config.nikto_enabled else ''}
{f'<div style="padding:5px; color:#10B981;"><b>• HTML Report: {report_path}</b></div>' if report_path else ''}
</div>
</div>'''
        
        self.output.emit(summary_html)


class Automation(ToolBase):
    name = "Automation"
    category = ToolCategory.AUTOMATION
    
    def get_widget(self, main_window):
        return AutomationView(main_window=main_window)


class AutomationView(StyledToolView, SafeStop, OutputHelper):
    """Bug Bounty Automation UI"""
    
    def __init__(self, main_window=None):
        super().__init__()
        self.init_safe_stop()
        self.main_window = main_window
        self.worker = None
        self.worker_thread = None
        self.config = AutomationConfig()
        self._build_ui()
    
    def _build_ui(self):
        """Build the complete UI - Same layout as Whois."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = ToolSplitter()
        
        # ==================== CONTROL PANEL (Left Side) ====================
        control_panel = QWidget()
        control_scroll = QScrollArea()
        control_scroll.setWidgetResizable(True)
        control_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        control_content = QWidget()
        control_layout = QVBoxLayout(control_content)
        control_layout.setContentsMargins(15, 15, 15, 15)
        control_layout.setSpacing(12)
        
        # Header
        header = HeaderLabel("AUTOMATION", "Bug Bounty Pipeline")
        control_layout.addWidget(header)
        
        # Target Input
        target_group = StyledGroupBox("🎯 Target")
        target_layout = QVBoxLayout(target_group)
        self.target_input = TargetInput()
        self.target_input.input_box.setPlaceholderText("example.com or /path/to/targets.txt")
        target_layout.addWidget(self.target_input)
        control_layout.addWidget(target_group)
        
        # Tool Configuration
        config_group = StyledGroupBox("⚙️ Configuration")
        config_layout = QGridLayout(config_group)
        config_layout.setSpacing(8)
        
        # Subdomain tools row
        self.subfinder_check = StyledCheckBox("Subfinder")
        self.subfinder_check.setChecked(True)
        self.theharvester_check = StyledCheckBox("theHarvester")
        self.chaos_check = StyledCheckBox("Chaos")
        self.sublist3r_check = StyledCheckBox("Sublist3r")
        self.parallel_check = StyledCheckBox("Parallel")
        self.parallel_check.setChecked(True)
        
        config_layout.addWidget(self.subfinder_check, 0, 0)
        config_layout.addWidget(self.theharvester_check, 0, 1)
        config_layout.addWidget(self.chaos_check, 0, 2)
        config_layout.addWidget(self.sublist3r_check, 1, 0)
        config_layout.addWidget(self.parallel_check, 1, 1)
        
        # HTTPX threads
        httpx_label = QLabel("HTTPX Threads:")
        httpx_label.setStyleSheet("color: #E5E7EB; font-weight: 600;")
        self.httpx_threads = StyledSpinBox()
        self.httpx_threads.setRange(10, 200)
        self.httpx_threads.setValue(50)
        config_layout.addWidget(httpx_label, 2, 0)
        config_layout.addWidget(self.httpx_threads, 2, 1)
        
        # Nmap preset
        nmap_label = QLabel("Nmap Preset:")
        nmap_label.setStyleSheet("color: #E5E7EB; font-weight: 600;")
        self.nmap_preset = StyledComboBox()
        self.nmap_preset.addItems([
            "Default (Top 1000 TCP)", "Fast (Top 100 TCP)", "Full TCP Scan",
            "UDP Default (Top 1000)", "UDP Fast (Top 100)", "UDP + TCP Full"
        ])
        config_layout.addWidget(nmap_label, 3, 0)
        config_layout.addWidget(self.nmap_preset, 3, 1, 1, 2)
        
        control_layout.addWidget(config_group)
        
        # Additional Tools
        tools_group = StyledGroupBox("🔧 Additional Tools")
        tools_layout = QGridLayout(tools_group)
        
        self.eyewitness_check = StyledCheckBox("📸 EyeWitness")
        self.nuclei_check = StyledCheckBox("⚠️ Nuclei")
        self.nikto_check = StyledCheckBox("🔧 Nikto")
        
        tools_layout.addWidget(self.eyewitness_check, 0, 0)
        tools_layout.addWidget(self.nuclei_check, 0, 1)
        tools_layout.addWidget(self.nikto_check, 0, 2)
        
        control_layout.addWidget(tools_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.run_button = RunButton("🚀 START")
        self.run_button.clicked.connect(self.run_pipeline)
        self.skip_button = StopButton("⏭️ SKIP")
        self.skip_button.clicked.connect(self.skip_step)
        self.skip_button.setEnabled(False)
        self.stop_button = StopButton("⛔ STOP")
        self.stop_button.clicked.connect(self.stop_pipeline)
        self.stop_button.setEnabled(False)
        
        btn_layout.addWidget(self.run_button)
        btn_layout.addWidget(self.skip_button)
        btn_layout.addWidget(self.stop_button)
        control_layout.addLayout(btn_layout)
        
        # Progress
        progress_group = StyledGroupBox("📊 Progress")
        progress_layout = QVBoxLayout(progress_group)
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar { background: #1a1a2e; border: 2px solid #3B82F6; border-radius: 8px; height: 25px; text-align: center; color: white; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #10B981); border-radius: 6px; }
        """)
        self.progress_label = QLabel("Ready to start")
        self.progress_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        control_layout.addWidget(progress_group)
        
        # Pipeline Status
        status_group = StyledGroupBox("📋 Status")
        status_layout = QGridLayout(status_group)
        status_layout.setSpacing(5)
        
        self.status_labels = {}
        modules = [
            ("whois", "Whois"), ("dig", "DNS"), ("subdomain", "Subdomains"),
            ("httpx", "HTTPX"), ("nmap", "Nmap"), ("eyewitness", "Screenshots"),
            ("nuclei", "Nuclei"), ("nikto", "Nikto"), ("report", "Report")
        ]
        
        for idx, (key, name) in enumerate(modules):
            row, col = divmod(idx, 3)
            label = QLabel(f"{name}: ")
            label.setStyleSheet("color: #9CA3AF; font-size: 11px;")
            status = QLabel(Status.PENDING)
            status.setStyleSheet("color: #6B7280; font-size: 11px;")
            self.status_labels[key] = status
            status_layout.addWidget(label, row, col * 2)
            status_layout.addWidget(status, row, col * 2 + 1)
        
        control_layout.addWidget(status_group)
        
        # Statistics
        stats_group = StyledGroupBox("📈 Statistics")
        stats_layout = QGridLayout(stats_group)
        
        self.stats_labels = {
            'targets': QLabel("0"), 'subdomains': QLabel("0"),
            'live_hosts': QLabel("0"), 'vulns': QLabel("0")
        }
        
        stats_layout.addWidget(QLabel("Targets:"), 0, 0)
        stats_layout.addWidget(self.stats_labels['targets'], 0, 1)
        stats_layout.addWidget(QLabel("Subdomains:"), 0, 2)
        stats_layout.addWidget(self.stats_labels['subdomains'], 0, 3)
        stats_layout.addWidget(QLabel("Live:"), 1, 0)
        stats_layout.addWidget(self.stats_labels['live_hosts'], 1, 1)
        stats_layout.addWidget(QLabel("Vulns:"), 1, 2)
        stats_layout.addWidget(self.stats_labels['vulns'], 1, 3)
        
        for lbl in self.stats_labels.values():
            lbl.setStyleSheet("color: #3B82F6; font-weight: 700; font-size: 16px;")
        
        control_layout.addWidget(stats_group)
        control_layout.addStretch()
        
        control_scroll.setWidget(control_content)
        
        # Create wrapper for scroll
        scroll_wrapper = QWidget()
        wrapper_layout = QVBoxLayout(scroll_wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(control_scroll)
        
        splitter.addWidget(scroll_wrapper)
        
        # ==================== OUTPUT AREA (Right Side) ====================
        self.output = OutputView(self.main_window)
        self.output.setPlaceholderText("🚀 Automation output will appear here...\n\n1. Enter target domain or file\n2. Configure tools\n3. Click START")
        
        splitter.addWidget(self.output)
        splitter.setSizes([350, 650])
        
        main_layout.addWidget(splitter)
    
    def run_pipeline(self):
        """Start automation pipeline"""
        raw_input = self.target_input.get_target().strip()
        if not raw_input:
            self._notify("Please enter a target")
            return
        
        # Dependency check
        if not self._check_dependencies():
            return
        
        # Parse targets
        targets, source = parse_targets(raw_input)
        if not targets:
            self._notify("No valid targets found")
            return
        
        # Update config from UI
        self.config.subfinder_enabled = self.subfinder_check.isChecked()
        self.config.theharvester_enabled = self.theharvester_check.isChecked()
        self.config.chaos_enabled = self.chaos_check.isChecked()
        self.config.sublist3r_enabled = self.sublist3r_check.isChecked()
        self.config.parallel_subdomain = self.parallel_check.isChecked()
        self.config.httpx_threads = self.httpx_threads.value()
        self.config.eyewitness_enabled = self.eyewitness_check.isChecked()
        self.config.nuclei_enabled = self.nuclei_check.isChecked()
        self.config.nikto_enabled = self.nikto_check.isChecked()
        
        # Nmap preset
        preset_map = {
            "Default (Top 1000 TCP)": "default",
            "Fast (Top 100 TCP)": "fast",
            "Full TCP Scan": "full",
            "UDP Default (Top 1000)": "udp_default",
            "UDP Fast (Top 100)": "udp_fast",
            "UDP + TCP Full": "udp_full"
        }
        self.config.nmap_preset = preset_map.get(self.nmap_preset.currentText(), "default")
        
        # Create dirs
        base_dirs = []
        group_name = get_group_name_from_file(raw_input) if source == "file" else None
        
        for target in targets:
            base_dir = create_target_dirs(target, group_name)
            base_dirs.append(base_dir)
        
        # Reset UI
        self.output.clear()
        for key in self.status_labels:
            self.update_status(key, Status.PENDING)
        
        self.progress_bar.setValue(0)
        self.stats_labels['targets'].setText(str(len(targets)))
        self.stats_labels['subdomains'].setText("0")
        self.stats_labels['live_hosts'].setText("0")
        self.stats_labels['vulns'].setText("0")
        
        # Buttons
        self.run_button.setEnabled(False)
        self.skip_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        
        # Start worker
        self.worker = AutomationWorker(targets, base_dirs, self.config, self.main_window)
        
        self.worker.status_update.connect(self.update_status)
        self.worker.output.connect(self.append_output)
        self.worker.error.connect(self.show_error)
        self.worker.progress.connect(self.update_progress)
        self.worker.stats_update.connect(self.update_stats)
        self.worker.tool_result.connect(self.update_results)
        self.worker.finished.connect(self.on_pipeline_finished)
        
        self.worker.start()
        
        self._info("🚀 Automation pipeline started!")
    
    def _check_dependencies(self):
        """Check required tools"""
        required = ['whois', 'httpx-toolkit', 'nmap']
        
        if self.config.subfinder_enabled:
            required.append('subfinder')
        if self.config.theharvester_enabled:
            required.append('theHarvester')
        if self.config.chaos_enabled:
            required.append('chaos')
        if self.config.sublist3r_enabled:
            required.append('sublist3r')
        if self.config.eyewitness_enabled:
            required.append('eyewitness')
        if self.config.nuclei_enabled:
            required.append('nuclei')
        if self.config.nikto_enabled:
            required.append('nikto')
        
        missing = [t for t in required if not shutil.which(t)]
        
        if missing:
            self._error(f"❌ Missing tools: {', '.join(missing)}")
            self._raw("<br><b>Please install missing tools before running automation.</b>")
            self._raw(f"<br>Run: <code>./install_automation_tools.sh</code>")
            return False
        
        return True
    
    def skip_step(self):
        """Skip current step"""
        if self.worker and self.worker.isRunning():
            self.worker.skip()
            self._notify("⏭️ Skipping current step...")
    
    def stop_pipeline(self):
        """Stop pipeline"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(3000)  # Wait up to 3 seconds
            if self.worker.isRunning():
                self.worker.terminate()
            self._notify("⛔ Stopping pipeline...")
        
        self.run_button.setEnabled(True)
        self.skip_button.setEnabled(False)
        self.stop_button.setEnabled(False)
    
    def on_pipeline_finished(self):
        """Handle completion"""
        self.run_button.setEnabled(True)
        self.skip_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        
        self.worker = None
        
        self._info("✅ Automation pipeline finished!")
    
    def update_status(self, key, status):
        """Update step status"""
        label = self.status_labels.get(key)
        if not label:
            return
        
        label.setText(status)
        
        color_map = {
            Status.PENDING: "#9CA3AF",
            Status.RUNNING: "#3B82F6",
            Status.COMPLETED: COLOR_SUCCESS,
            Status.SKIPPED: COLOR_WARNING,
            Status.ERROR: COLOR_ERROR,
            Status.TERMINATED: COLOR_ERROR
        }
        
        color = color_map.get(status, "#E5E7EB")
        label.setStyleSheet(f"color: {color}; font-weight: 700; font-size: 12px;")
    
    def update_progress(self, percentage, message):
        """Update progress bar"""
        self.progress_bar.setValue(percentage)
        self.progress_label.setText(message)
    
    def update_stats(self, stats):
        """Update statistics"""
        total_subdomains = sum(s.get('subdomains_found', 0) for s in stats.values())
        total_live = sum(s.get('live_hosts', 0) for s in stats.values())
        total_vulns = sum(s.get('nuclei_findings', 0) for s in stats.values())
        
        self.stats_labels['subdomains'].setText(str(total_subdomains))
        self.stats_labels['live_hosts'].setText(str(total_live))
        self.stats_labels['vulns'].setText(str(total_vulns))
    
    def update_results(self, target_name, result_data):
        """Handle results signal - summary is already shown by _show_results_summary"""
        # This method receives the signal but doesn't need to display anything
        # as _show_results_summary already handles the output display
        pass
    
    def append_output(self, text):
        """Append output"""
        if text.strip():
            self._raw(text)
    
    def show_error(self, msg):
        """Show error"""
        self._error(msg)
    
    def stop_scan(self):
        """Override from SafeStop mixin"""
        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(2000)
