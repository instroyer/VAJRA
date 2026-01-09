# VAJRA HTML Report Generator - Enhanced Version
# Now includes: Whois, Dig, Subdomains, Services, Nmap, Nuclei, Nikto, EyeWitness

import os
import json
from core.jsonparser import FinalJsonGenerator

class ReportGenerator:
    """
    Generates an HTML report from a final.json data file.
    Enhanced with Nuclei, Nikto, Dig, and EyeWitness sections.
    """
    def __init__(self, target, target_dir, module_choices):
        self.target = target
        self.target_dir = target_dir
        # Accept both numeric codes AND tool names
        if isinstance(module_choices, str):
            self.module_choices = set(module_choices.lower().split())
        else:
            self.module_choices = set(str(module_choices).split())
        
        self.json_file = os.path.join(self.target_dir, "JSON", "final.json")
        self.report_dir = os.path.join(self.target_dir, "Reports")
        self.data = {}

    def load_data(self):
        """Loads the data from final.json."""
        if not os.path.exists(self.json_file):
            return False
        try:
            with open(self.json_file, 'r') as f:
                self.data = json.load(f)
            return True
        except (json.JSONDecodeError, IOError) as e:
            return False

    def generate_html(self):
        """Builds the complete HTML string for the report."""
        if not self.data:
            return None

        body_sections = []
        
        # Whois
        if 'whois' in self.data:
            body_sections.append(self._generate_whois_section())
        
        # Dig (DNS)
        if 'dig' in self.data:
            body_sections.append(self._generate_dig_section())
        
        # Subdomains
        if 'subdomains' in self.data:
            body_sections.append(self._generate_subdomain_section())
        
        # Services
        if 'services' in self.data:
            body_sections.append(self._generate_service_section())
        
        # Nmap
        if 'nmap' in self.data:
            body_sections.append(self._generate_nmap_section())
        
        # Nuclei Vulnerabilities
        if 'nuclei' in self.data:
            body_sections.append(self._generate_nuclei_section())
        
        # Nikto Findings
        if 'nikto' in self.data:
            body_sections.append(self._generate_nikto_section())
        
        # EyeWitness Screenshots
        if 'eyewitness' in self.data:
            body_sections.append(self._generate_eyewitness_section())
        
        # Recommendations (always include if we have findings)
        if len(body_sections) > 0:
            body_sections.append(self._generate_recommendations_section())

        html_content = self._get_embedded_template(
            header=self._generate_header(),
            executive_summary=self._generate_executive_summary(),
            body="".join(body_sections),
            footer=self._generate_footer()
        )
        return html_content

    def save_report(self, html_content):
        """Saves the generated HTML to a file."""
        if not html_content:
            return False
        
        try:
            os.makedirs(self.report_dir, exist_ok=True)
            clean_target = "".join(c for c in self.target if c.isalnum() or c in ['.', '-', '_'])
            report_filename = f"report_{clean_target}.html"
            report_path = os.path.join(self.report_dir, report_filename)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
        except IOError as e:
            return False

    # --- SECTION GENERATORS ---
    
    def _generate_header(self):
        scan_info = self.data.get('scan_info', {})
        target_name = scan_info.get('target', 'N/A')
        scan_date = scan_info.get('scan_date', 'N/A')
        risk_level = scan_info.get('risk_level', 'Medium')
        
        # Color code risk level
        risk_colors = {
            'Critical': '#DC2626',
            'High': '#F59E0B',
            'Medium': '#3B82F6',
            'Low': '#10B981',
            'Info': '#6B7280'
        }
        risk_color = risk_colors.get(risk_level, '#3B82F6')
        
        return f"""
        <div class="header">
            <div class="header-top">
                <div>
                    <div class="vajra-title">VAJRA</div>
                    <div class="vajra-subtitle">Offensive Security Platform</div>
                </div>
            </div>
            <div class="report-title">Comprehensive Security Assessment Report</div>
            <div class="scan-info">
                <div class="info-item target" onclick="copyToClipboard('{target_name}')">
                    <span class="copy-badge"><i class="fas fa-copy"></i></span>
                    <h3><i class="fas fa-bullseye"></i> Target</h3>
                    <p>{target_name}</p>
                </div>
                <div class="info-item date">
                    <h3><i class="fas fa-calendar-alt"></i> Scan Date</h3>
                    <p>{scan_date}</p>
                </div>
                <div class="info-item risk" style="background: linear-gradient(135deg, {risk_color} 0%, {risk_color}CC 100%);">
                    <h3><i class="fas fa-shield-alt"></i> Risk Level</h3>
                    <p style="font-size: 1.3em; font-weight: 800;">{risk_level}</p>
                </div>
            </div>
        </div>
        """

    def _generate_executive_summary(self):
        scan_info = self.data.get('scan_info', {})
        subdomains = self.data.get('subdomains', {})
        nuclei = self.data.get('nuclei', {})
        nikto = self.data.get('nikto', {})
        nmap = self.data.get('nmap', {})
        
        summary_points = []
        
        if subdomains:
            total_discovered = subdomains.get('total_discovered', 0)
            total_alive = subdomains.get('total_alive', 0)
            summary_points.append(f"• Discovered {total_discovered} subdomains, {total_alive} are live") 
    
        if nmap:
            total_ports = nmap.get('scan_summary', {}).get('total_open_ports', 0)
            summary_points.append(f"• Found {total_ports} open ports across scanned hosts")
        
        if nuclei:
            total_vulns = nuclei.get('total_findings', 0)
            severity = nuclei.get('severity_breakdown', {})
            critical = severity.get('critical', 0)
            high = severity.get('high', 0)
            summary_points.append(f"• Nuclei identified {total_vulns} vulnerabilities ({critical} critical, {high} high)")
        
        if nikto:
            total_nikto = nikto.get('total_findings', 0)
            summary_points.append(f"• Nikto found {total_nikto} potential web server issues")
        
        summary_text = "<br>".join(summary_points) if summary_points else "This report summarizes the findings from the reconnaissance scan performed by the VAJRA framework."
        
        return f"""
        <div class="section executive" id="executive-summary">
            <h2 class="section-header">
                <div><i class="fas fa-chart-line"></i> Executive Summary</div>
                <button class="toggle-btn" onclick="toggleSection(this)"><i class="fas fa-chevron-up"></i></button>
            </h2>
            <div class="section-content">
                <div class="summary-box">
                    {summary_text}
                </div>
            </div>
        </div>
        """

    def _generate_whois_section(self):
        whois = self.data.get('whois', {})
        name_servers_html = ''.join(f'<li>{ns}</li>' for ns in whois.get('name_servers', []))
        
        return f"""
        <div class="section domain" id="domain-analysis">
            <h2 class="section-header">
                <div><i class="fas fa-globe"></i> Domain Registration Analysis</div>
                <button class="toggle-btn" onclick="toggleSection(this)"><i class="fas fa-chevron-up"></i></button>
            </h2>
            <div class="section-content">
                <div style="position: relative;">
                    <button class="table-copy" onclick="copyTable(this)">Copy Table</button>
                    <table class="compact-table">
                        <tr><td><strong>Domain Name</strong></td><td>{whois.get('domain_name', 'N/A')}</td></tr>
                        <tr><td><strong>Registrar</strong></td><td>{whois.get('registrar', 'N/A')}</td></tr>
                        <tr><td><strong>Creation Date</strong></td><td>{whois.get('creation_date', 'N/A')}</td></tr>
                        <tr><td><strong>Expiration Date</strong></td><td>{whois.get('expiration_date', 'N/A')}</td></tr>
                        <tr><td><strong>Last Updated</strong></td><td>{whois.get('updated_date', 'N/A')}</td></tr>
                        <tr><td><strong>Name Servers</strong></td><td><ul>{name_servers_html}</ul></td></tr>
                        <tr><td><strong>DNSSEC Status</strong></td><td>{whois.get('dnssec_status', 'N/A')}</td></tr>
                        <tr><td><strong>Registrant Org</strong></td><td>{whois.get('registrant_organization', 'N/A')}</td></tr>
                        <tr><td><strong>Registrant Country</strong></td><td>{whois.get('registrant_country', 'N/A')}</td></tr>
                    </table>
                </div>
            </div>
        </div>
        """
    
    def _generate_dig_section(self):
        dig = self.data.get('dig', {})
        
        # A Records
        a_records_html = ""
        for record in dig.get('a_records', []):
            a_records_html += f"<tr><td>{record.get('name', 'N/A')}</td><td>{record.get('ip', 'N/A')}</td></tr>"
        
        # MX Records
        mx_records_html = ""
        for record in dig.get('mx_records', []):
            mx_records_html += f"<tr><td>{record.get('priority', 'N/A')}</td><td>{record.get('server', 'N/A')}</td></tr>"
        
        # NS Records
        ns_records_html = ""
        for record in dig.get('ns_records', []):
            ns_records_html += f"<tr><td>{record.get('nameserver', 'N/A')}</td></tr>"
        
        # TXT Records
        txt_records_html = ""
        for record in dig.get('txt_records', []):
            txt_records_html += f"<tr><td>{record.get('text', 'N/A')}</td></tr>"
        
        return f"""
        <div class="section dns" id="dns-analysis">
            <h2 class="section-header">
                <div><i class="fas fa-server"></i> DNS Records Analysis</div>
                <button class="toggle-btn" onclick="toggleSection(this)"><i class="fas fa-chevron-up"></i></button>
            </h2>
            <div class="section-content">
                <div class="dns-grid">
                    <div class="dns-card">
                        <h3><i class="fas fa-map-marker-alt"></i> A Records (IPv4)</h3>
                        <table class="compact-table">
                            <thead><tr><th>Hostname</th><th>IP Address</th></tr></thead>
                            <tbody>{a_records_html or '<tr><td colspan="2">No A records found</td></tr>'}</tbody>
                        </table>
                    </div>
                    
                    <div class="dns-card">
                        <h3><i class="fas fa-envelope"></i> MX Records (Mail)</h3>
                        <table class="compact-table">
                            <thead><tr><th>Priority</th><th>Mail Server</th></tr></thead>
                            <tbody>{mx_records_html or '<tr><td colspan="2">No MX records found</td></tr>'}</tbody>
                        </table>
                    </div>
                    
                    <div class="dns-card">
                        <h3><i class="fas fa-database"></i> NS Records (Nameservers)</h3>
                        <table class="compact-table">
                            <thead><tr><th>Nameserver</th></tr></thead>
                            <tbody>{ns_records_html or '<tr><td>No NS records found</td></tr>'}</tbody>
                        </table>
                    </div>
                    
                    <div class="dns-card">
                        <h3><i class="fas fa-file-alt"></i> TXT Records</h3>
                        <table class="compact-table">
                            <thead><tr><th>Text Data</th></tr></thead>
                            <tbody>{txt_records_html or '<tr><td>No TXT records found</td></tr>'}</tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        """

    def _generate_subdomain_section(self):
        subdomains_data = self.data.get('subdomains', {})
        total_discovered = subdomains_data.get('total_discovered', 0)
        total_alive = subdomains_data.get('total_alive', 0)
        subdomains_list = subdomains_data.get('subdomains', [])
        
        # Show first 200, note if there are more
        display_limit = 200
        subdomains_list_html = ''.join(f'<tr><td>{sub}</td></tr>' for sub in subdomains_list[:display_limit])
        
        more_note = ""
        if len(subdomains_list) > display_limit:
            more_note = f'<p style="color: #F59E0B; margin-top: 10px;"><i class="fas fa-info-circle"></i> Showing first {display_limit} of {len(subdomains_list)} live subdomains</p>'
        
        return f"""
        <div class="section subdomain" id="subdomain-mapping">
            <h2 class="section-header">
                <div><i class="fas fa-sitemap"></i> Subdomain Infrastructure Mapping</div>
                <button class="toggle-btn" onclick="toggleSection(this)"><i class="fas fa-chevron-up"></i></button>
            </h2>
            <div class="section-content">
                <div class="stats-box">
                    <div class="stat-item">
                        <div class="stat-value">{total_discovered}</div>
                        <div class="stat-label">Total Discovered</div>
                    </div>
                    <div class="stat-item success">
                        <div class="stat-value">{total_alive}</div>
                        <div class="stat-label">Live Subdomains</div>
                    </div>
                </div>
                {more_note}
                <div style="position: relative; margin-top: 15px;">
                    <button class="table-copy" onclick="copyTable(this)">Copy Table</button>
                    <table class="compact-table">
                        <thead><tr><th>Live Subdomains</th></tr></thead>
                        <tbody>{subdomains_list_html}</tbody>
                    </table>
                </div>
            </div>
        </div>
        """

    def _generate_service_section(self):
        services = self.data.get('services', [])
        rows_html = ""
        for s in services[:100]:  # Limit to 100
            rows_html += f"""
            <tr>
                <td><a href="{s.get('url', '#')}" target="_blank">{s.get('url', 'N/A')}</a></td>
                <td>{s.get('host', 'N/A')}</td>
                <td>{s.get('port', 'N/A')}</td>
                <td>{s.get('webserver', 'N/A')}</td>
            </tr>
            """
        
        return f"""
        <div class="section service" id="service-discovery">
            <h2 class="section-header">
                <div><i class="fas fa-heartbeat"></i> Service Discovery & Availability</div>
                <button class="toggle-btn" onclick="toggleSection(this)"><i class="fas fa-chevron-up"></i></button>
            </h2>
            <div class="section-content">
                <div style="position: relative;">
                    <button class="table-copy" onclick="copyTable(this)">Copy Table</button>
                    <table class="compact-table">
                        <thead><tr><th>URL</th><th>Host</th><th>Port</th><th>Web Server</th></tr></thead>
                        <tbody>{rows_html}</tbody>
                    </table>
                </div>
            </div>
        </div>
        """

    def _generate_nmap_section(self):
        nmap = self.data.get('nmap', {})
        summary = nmap.get('scan_summary', {})
        hosts = nmap.get('hosts', [])
        
        # Build host cards with proper port tables
        hosts_html = ""
        for host in hosts:
            hostname = host.get('hostname', 'Unknown')
            ip = host.get('ip_address', 'N/A')
            ports = host.get('open_ports', [])
            
            # Build port table rows
            port_rows = ""
            for port in ports:
                port_id = port.get('port_id', 'N/A')
                protocol = port.get('protocol', 'tcp')
                service = port.get('service_name', 'unknown').upper()
                version = port.get('service_version', 'N/A')
                recommendation = port.get('recommendation', '')
                
                # Service color based on type
                service_colors = {
                    'SSH': '#10B981', 'HTTP': '#3B82F6', 'HTTPS': '#3B82F6',
                    'FTP': '#F59E0B', 'TELNET': '#DC2626', 'SMTP': '#8B5CF6',
                    'DNS': '#06B6D4', 'MYSQL': '#F97316', 'RDP': '#EF4444'
                }
                svc_color = service_colors.get(service, '#6B7280')
                
                port_rows += f"""
                <tr style="border-bottom: 1px solid #e5e7eb;">
                    <td style="padding: 12px; font-weight: 600; color: #1f2937;">{port_id}/{protocol}</td>
                    <td style="padding: 12px;"><span style="background: {svc_color}; color: white; padding: 4px 10px; border-radius: 4px; font-weight: 600; font-size: 0.85em;">{service}</span></td>
                    <td style="padding: 12px; color: #4b5563;">{version}</td>
                    <td style="padding: 12px; color: #6b7280; font-size: 0.9em;">{recommendation}</td>
                </tr>"""
            
            hosts_html += f"""
            <div class="host-card" style="background: white; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden;">
                <div style="background: linear-gradient(135deg, #1e3a5f, #3B82F6); padding: 15px 20px; color: white;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 1.2em; font-weight: 700;"><i class="fas fa-server"></i> {hostname}</div>
                            <div style="opacity: 0.8; font-size: 0.9em;">{ip}</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; font-weight: 600;">
                            {len(ports)} Open Ports
                        </div>
                    </div>
                </div>
                <div style="padding: 0;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #f8fafc;">
                                <th style="padding: 12px; text-align: left; color: #64748b; font-weight: 600; width: 100px;">Port</th>
                                <th style="padding: 12px; text-align: left; color: #64748b; font-weight: 600; width: 120px;">Service</th>
                                <th style="padding: 12px; text-align: left; color: #64748b; font-weight: 600;">Version</th>
                                <th style="padding: 12px; text-align: left; color: #64748b; font-weight: 600;">Security Note</th>
                            </tr>
                        </thead>
                        <tbody>{port_rows}</tbody>
                    </table>
                </div>
            </div>"""

        # Summary stats
        total_hosts = len(hosts)
        total_ports = summary.get('total_open_ports', 0)
        scan_type = summary.get('scan_type', 'SYN')

        return f"""
        <div class="section network" id="network-analysis">
            <h2 class="section-header">
                <div><i class="fas fa-network-wired"></i> Network Infrastructure Analysis</div>
                <button class="toggle-btn" onclick="toggleSection(this)"><i class="fas fa-chevron-up"></i></button>
            </h2>
            <div class="section-content">
                <div class="stats-box">
                    <div class="stat-item">
                        <div class="stat-value">{scan_type}</div>
                        <div class="stat-label">Scan Type</div>
                    </div>
                    <div class="stat-item info">
                        <div class="stat-value">{total_hosts}</div>
                        <div class="stat-label">Hosts Scanned</div>
                    </div>
                    <div class="stat-item danger">
                        <div class="stat-value">{total_ports}</div>
                        <div class="stat-label">Total Open Ports</div>
                    </div>
                </div>
                <h3 style="margin: 25px 0 15px 0; color: var(--primary);"><i class="fas fa-server"></i> Host Details</h3>
                {hosts_html if hosts_html else '<p style="color: #6B7280; padding: 20px; text-align: center;">No hosts found during scan.</p>'}
            </div>
        </div>
        """
    
    def _generate_nuclei_section(self):
        nuclei = self.data.get('nuclei', {})
        total_findings = nuclei.get('total_findings', 0)
        severity = nuclei.get('severity_breakdown', {})
        vulnerabilities = nuclei.get('vulnerabilities', [])
        
        # Severity stats
        severity_html = f"""
        <div class="severity-grid">
            <div class="severity-card critical">
                <div class="severity-count">{severity.get('critical', 0)}</div>
                <div class="severity-label">Critical</div>
            </div>
            <div class="severity-card high">
                <div class="severity-count">{severity.get('high', 0)}</div>
                <div class="severity-label">High</div>
            </div>
            <div class="severity-card medium">
                <div class="severity-count">{severity.get('medium', 0)}</div>
                <div class="severity-label">Medium</div>
            </div>
            <div class="severity-card low">
                <div class="severity-count">{severity.get('low', 0)}</div>
                <div class="severity-label">Low</div>
            </div>
            <div class="severity-card info">
                <div class="severity-count">{severity.get('info', 0)}</div>
                <div class="severity-label">Info</div>
            </div>
        </div>
        """
        
        # Vulnerability list
        vulns_html = ""
        for vuln in vulnerabilities[:50]:  # Show first 50
            severity_class = vuln.get('severity', 'medium')
            vulns_html += f"""
            <div class="vuln-item {severity_class}">
                <div class="vuln-header">
                    <span class="vuln-severity"><i class="fas fa-shield-alt"></i> {vuln.get('severity', 'N/A').upper()}</span>
                    <span class="vuln-title">{vuln.get('title', 'Unknown')}</span>
                </div>
                <div class="vuln-url"><i class="fas fa-link"></i> {vuln.get('url', 'N/A')}</div>
                <div class="vuln-description">{vuln.get('description', 'N/A')}</div>
            </div>
            """
        
        return f"""
        <div class="section vulnerability" id="nuclei-scan">
            <h2 class="section-header">
                <div><i class="fas fa-bug"></i> Nuclei Vulnerability Scan</div>
                <button class="toggle-btn" onclick="toggleSection(this)"><i class="fas fa-chevron-up"></i></button>
            </h2>
            <div class="section-content">
                <div class="alert-box critical">
                    <i class="fas fa-exclamation-triangle"></i> 
                    <strong>Total Vulnerabilities Found: {total_findings}</strong>
                </div>
                {severity_html}
                <h3 style="margin-top: 20px; color: var(--primary);">Vulnerability Details:</h3>
                <div class="vuln-list">
                    {vulns_html}
                </div>
            </div>
        </div>
        """
    
    def _generate_nikto_section(self):
        nikto = self.data.get('nikto', {})
        total_findings = nikto.get('total_findings', 0)
        targets_scanned = nikto.get('targets_scanned', [])
        findings = nikto.get('findings', [])
        
        # Count by severity
        high_count = len([f for f in findings if f.get('severity') == 'high'])
        medium_count = len([f for f in findings if f.get('severity') == 'medium'])
        info_count = len([f for f in findings if f.get('severity') == 'info'])
        
        targets_html = ", ".join(targets_scanned) if targets_scanned else "N/A"
        
        # Severity stats grid (like Nuclei)
        severity_html = f"""
        <div class="severity-grid">
            <div class="severity-card high">
                <div class="severity-count">{high_count}</div>
                <div class="severity-label">High</div>
            </div>
            <div class="severity-card medium">
                <div class="severity-count">{medium_count}</div>
                <div class="severity-label">Medium</div>
            </div>
            <div class="severity-card info">
                <div class="severity-count">{info_count}</div>
                <div class="severity-label">Info</div>
            </div>
        </div>
        """
        
        # Findings list with severity badges
        findings_html = ""
        for finding in findings[:100]:  # Show first 100
            severity = finding.get('severity', 'info')
            severity_colors = {
                'high': '#DC2626',
                'medium': '#F59E0B',
                'info': '#3B82F6'
            }
            color = severity_colors.get(severity, '#6B7280')
            host = finding.get('host', 'N/A')
            description = finding.get('finding', finding.get('description', 'N/A'))
            
            findings_html += f"""
            <div class="vuln-item {severity}">
                <div class="vuln-header">
                    <span class="vuln-severity" style="background: {color};"><i class="fas fa-shield-alt"></i> {severity.upper()}</span>
                    <span class="vuln-title">{host}</span>
                </div>
                <div class="vuln-description">{description}</div>
            </div>
            """
        
        return f"""
        <div class="section webscan" id="nikto-scan">
            <h2 class="section-header">
                <div><i class="fas fa-search"></i> Nikto Web Server Scan</div>
                <button class="toggle-btn" onclick="toggleSection(this)"><i class="fas fa-chevron-up"></i></button>
            </h2>
            <div class="section-content">
                <div class="alert-box info">
                    <i class="fas fa-server"></i> 
                    <strong>Targets Scanned:</strong> {targets_html} | <strong>Total Findings: {total_findings}</strong>
                </div>
                {severity_html}
                <h3 style="margin-top: 20px; color: var(--primary);">Findings Details:</h3>
                <div class="vuln-list">
                    {findings_html if findings_html else '<p style="color: #6B7280; padding: 20px;">No significant findings detected.</p>'}
                </div>
            </div>
        </div>
        """
    
    def _generate_eyewitness_section(self):
        eyewitness = self.data.get('eyewitness', {})
        screenshot_count = eyewitness.get('screenshot_count', 0)
        report_path = eyewitness.get('report_path', None)
        directory = eyewitness.get('directory', 'N/A')
        
        report_link = ""
        if report_path and os.path.exists(report_path):
            rel_path = os.path.relpath(report_path, self.report_dir)
            report_link = f'<p><a href="{rel_path}" target="_blank" class="btn-primary"><i class="fas fa-external-link-alt"></i> Open EyeWitness Report</a></p>'
        
        return f"""
        <div class="section screenshots" id="eyewitness-screenshots">
            <h2 class="section-header">
                <div><i class="fas fa-camera"></i> EyeWitness Screenshots</div>
                <button class="toggle-btn" onclick="toggleSection(this)"><i class="fas fa-chevron-up"></i></button>
            </h2>
            <div class="section-content">
                <div class="stats-box">
                    <div class="stat-item success">
                        <div class="stat-value">{screenshot_count}</div>
                        <div class="stat-label">Screenshots Captured</div>
                    </div>
                </div>
                <div class="info-box">
                    <p><strong>Screenshot Directory:</strong> {directory}</p>
                    {report_link}
                </div>
            </div>
        </div>
        """

    def _generate_recommendations_section(self):
        nuclei = self.data.get('nuclei', {})
        nmap = self.data.get('nmap', {})
        
        recommendations = []
        
        # Check for critical vulnerabilities
        if nuclei:
            severity = nuclei.get('severity_breakdown', {})
            if severity.get('critical', 0) > 0:
                recommendations.append({
                    'priority': 'Critical',
                    'recommendation': f"Address {severity['critical']} critical vulnerabilities from Nuclei scan immediately.",
                    'timeline': 'Immediate (24-48 hours)'
                })
            if severity.get('high', 0) > 0:
                recommendations.append({
                    'priority': 'High',
                    'recommendation': f"Remediate {severity['high']} high-severity vulnerabilities within one week.",
                    'timeline': '1 Week'
                })
        
        # Check for open ports
        if nmap:
            total_ports = nmap.get('scan_summary', {}).get('total_open_ports', 0)
            if total_ports > 10:
                recommendations.append({
                    'priority': 'High',
                    'recommendation': f"Review and close unnecessary ports. {total_ports} open ports detected - minimize attack surface.",
                    'timeline': '1-2 Weeks'
                })
        
        # Default recommendations
        if not recommendations:
            recommendations = [
                {
                    'priority': 'Medium',
                    'recommendation': 'Review web service configurations for security headers (HSTS, CSP) and updated software versions.',
                    'timeline': '1-2 Weeks'
                },
                {
                    'priority': 'Low',
                    'recommendation': 'Regularly review domain registration details for accuracy and ensure DNSSEC is enabled.',
                    'timeline': 'Ongoing'
                }
            ]
        
        rows_html = ""
        priority_colors = {
            'Critical': 'var(--danger)',
            'High': 'var(--accent)',
            'Medium': 'var(--warning)',
            'Low': 'var(--success)'
        }
        
        for rec in recommendations:
            color = priority_colors.get(rec['priority'], 'var(--primary)')
            rows_html += f"""
            <tr>
                <td><span style="color: {color}; font-weight: 700;">{rec['priority']}</span></td>
                <td>{rec['recommendation']}</td>
                <td>{rec['timeline']}</td>
            </tr>
            """
        
        return f"""
        <div class="section security" id="security-recommendations">
            <h2 class="section-header">
                <div><i class="fas fa-clipboard-check"></i> Security Recommendations</div>
                <button class="toggle-btn" onclick="toggleSection(this)"><i class="fas fa-chevron-up"></i></button>
            </h2>
            <div class="section-content">
                <div class="alert-box warning">
                    <i class="fas fa-info-circle"></i>
                    <strong>Priority Actions:</strong> Review all findings and prioritize remediation based on risk and business impact.
                </div>
                <div style="position: relative; margin-top: 15px;">
                    <button class="table-copy" onclick="copyTable(this)">Copy Table</button>
                    <table class="compact-table">
                        <thead><tr><th>Priority</th><th>Recommendation</th><th>Timeline</th></tr></thead>
                        <tbody>{rows_html}</tbody>
                    </table>
                </div>
            </div>
        </div>
        """
        
    def _generate_footer(self):
        return """
        <div class="footer">
            <p><strong>Generated by VAJRA Framework - Multi-layered Red Team Reconnaissance Framework</strong></p>
            <p>Owner: Yash Javiya | Penetration Tester</p>
            <div class="contact-info">
                <a href="mailto:yashjaviya1111@gmail.com" class="contact-link"><i class="fas fa-envelope"></i> Email</a>
                <a href="tel:+919999999999" class="contact-link"><i class="fas fa-phone"></i> Contact</a>
                <a href="https://github.com/instroyer" class="contact-link" target="_blank"><i class="fab fa-github"></i> GitHub</a>
                <a href="https://www.linkedin.com/in/yash--javiya/" class="contact-link" target="_blank"><i class="fab fa-linkedin"></i> LinkedIn</a>
            </div>
        </div>
        """

    def _get_embedded_template(self, header, executive_summary, body, footer):
        # Full HTML template with enhanced CSS for new sections
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VAJRA Security Report - {self.target}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {{
            --primary: #2c3e50; --secondary: #3B82F6; --accent: #DC2626; --success: #10B981;
            --warning: #F59E0B; --danger: #DC2626; --light: #ecf0f1; --dark: #1a1a2e;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Montserrat', sans-serif; line-height: 1.6; background: linear-gradient(135deg, #0f0f0f, #1a2a6c, #b21f1f); color: #333; min-height: 100vh; }}
        
        /* Print Styles - Hide sidebar and fixed header for PDF */
        @media print {{
            .fixed-header, .sidebar, #backToTop, .menu-toggle {{ display: none !important; }}
            .container {{ margin-top: 0 !important; padding: 10px !important; }}
            body {{ background: white !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            .section {{ page-break-inside: avoid; break-inside: avoid; margin-bottom: 15px; }}
            .header {{ margin-top: 0 !important; }}
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .header {{ background: rgba(255,255,255,0.98); padding: 30px; border-radius: 20px; box-shadow: 0 15px 40px rgba(0,0,0,0.1); margin: 20px 0 30px 0; text-align: center; }}
        .vajra-title {{ background: linear-gradient(45deg, #ff6b6b, #ee5a24, #f39c12, #27ae60, #3B82F6, #9b59b6, #ff6b6b); background-size: 400% 400%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3.5em; font-weight: 800; animation: rainbow 8s ease-in-out infinite; }}
        @keyframes rainbow {{ 0%{{background-position:0% 50%}} 50%{{background-position:100% 50%}} 100%{{background-position:0% 50%}} }}
        .vajra-subtitle {{ color: var(--primary); font-size: 1.2em; font-weight: 600; margin-top: 5px; }}
        .report-title {{ color: var(--secondary); font-size: 2.2em; margin: 10px 0 15px 0; padding-top: 15px; border-top: 3px solid var(--accent); font-weight: 700; }}
        .scan-info {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; margin-top: 20px; }}
        .info-item {{ padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.1); color: #fff; cursor: pointer; transition: transform 0.3s; }}
        .info-item:hover {{ transform: scale(1.05); }}
        .info-item.target {{ background: linear-gradient(135deg, #3B82F6 0%, #2c3e50 100%); }}
        .info-item.date {{ background: linear-gradient(135deg, #DC2626 0%, #b21f1f 100%); }}
        .info-item.risk {{ background: linear-gradient(135deg, #F59E0B 0%, #e67e22 100%); }}
        .section {{ background: rgba(255,255,255,0.97); padding: 25px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); margin-bottom: 25px; border-left: 5px solid; }}
        .section.executive {{ border-left-color: #ffc107; }}
        .section.domain {{ border-left-color: #28a745; }}
        .section.dns {{ border-left-color: #17a2b8; }}
        .section.subdomain {{ border-left-color: #007bff; }}
        .section.service {{ border-left-color: #17a2b8; }}
        .section.network {{ border-left-color: #dc3545; }}
        .section.vulnerability {{ border-left-color: #DC2626; background: linear-gradient(135deg, #fee 0%, #fdd 100%); }}
        .section.webscan {{ border-left-color: #F59E0B; }}
        .section.screenshots {{ border-left-color: #9b59b6; }}
        .section.security {{ border-left-color: #6c757d; }}
        .section-header {{ display: flex; align-items: center; justify-content: space-between; font-size: 1.8em; font-weight: 600; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 2px solid var(--accent); color: var(--primary); }}
        .toggle-btn {{ background: none; border: none; color: var(--dark); font-size: 1rem; cursor: pointer; transition: transform 0.3s; }}
        .section.collapsed .section-content {{ display: none; }}
        .compact-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; background: white; border-radius: 8px; overflow: hidden; }}
        .compact-table th {{ background: linear-gradient(135deg, var(--secondary) 0%, #2980b9 100%); color: white; padding: 12px; text-align: left; font-weight: 600; }}
        .compact-table td {{ padding: 10px 12px; border-bottom: 1px solid #dee2e6; }}
        .table-copy {{ position: absolute; top: -10px; right: 10px; background: var(--secondary); color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 0.8em; }}
        
        /* Stats boxes */
        .stats-box {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 15px 0; }}
        .stat-item {{ background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%); padding: 20px; border-radius: 10px; text-align: center; color: white; }}
        .stat-item.success {{ background: linear-gradient(135deg, #10B981 0%, #059669 100%); }}
        .stat-item.danger {{ background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%); }}
        .stat-value {{ font-size: 2.5em; font-weight: 800; }}
        .stat-label {{ font-size: 0.9em; opacity: 0.9; margin-top: 5px; }}
        
        /* DNS Grid */
        .dns-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }}
        .dns-card {{ background: white; border: 2px solid #e5e7eb; border-radius: 10px; padding: 15px; }}
        .dns-card h3 {{ color: var(--secondary); margin-bottom: 10px; font-size: 1.1em; }}
        
        /* Severity grid */
        .severity-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin: 15px 0; }}
        .severity-card {{ padding: 15px; border-radius: 8px; text-align: center; color: white; }}
        .severity-card.critical {{ background: linear-gradient(135deg, #DC2626 0%, #991B1B 100%); }}
        .severity-card.high {{ background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); }}
        .severity-card.medium {{ background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%); }}
        .severity-card.low {{ background: linear-gradient(135deg, #10B981 0%, #059669 100%); }}
        .severity-card.info {{ background: linear-gradient(135deg, #6B7280 0%, #4B5563 100%); }}
        .severity-count {{ font-size: 2em; font-weight: 800; }}
        .severity-label {{ font-size: 0.9em; opacity: 0.9; }}
        
        /* Vulnerability items */
        .vuln-list {{ margin-top: 15px; }}
        .vuln-item {{ background: white; border-left: 4px solid var(--warning); padding: 15px; margin-bottom: 10px; border-radius: 8px; }}
        .vuln-item.critical {{ border-left-color: var(--danger); }}
        .vuln-item.high {{ border-left-color: #F59E0B; }}
        .vuln-item.medium {{ border-left-color: var(--secondary); }}
        .vuln-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
        .vuln-severity {{ font-weight: 700; font-size: 0.85em; padding: 4px 8px; background: #f3f4f6; border-radius: 4px; }}
        .vuln-title {{ font-weight: 600; color: var(--primary); }}
        .vuln-url {{ color: #6b7280; font-size: 0.9em; margin-bottom: 5px; }}
        .vuln-description {{ font-size: 0.9em; color: #4b5563; }}
        
        /* Nikto findings */
        .nikto-list {{ margin-top: 15px; }}
        .nikto-finding {{ background: white; padding: 12px; margin-bottom: 8px; border-radius: 6px; display: flex; gap: 10px; align-items: center; }}
        .nikto-severity {{ padding: 4px 8px; border-radius: 4px; color: white; font-weight: 700; font-size: 0.8em; }}
        .nikto-description {{ flex: 1; color: var(--dark); }}
        
        /* Alert boxes */
        .alert-box {{ padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .alert-box.critical {{ background: #fee; border: 2px solid var(--danger); color: var(--danger); }}
        .alert-box.warning {{ background: #fef3c7; border: 2px solid var(--warning); color: #92400e; }}
        .info-box {{ background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .summary-box {{ background: #f9fafb; padding: 20px; border-radius: 10px; border-left: 4px solid var(--secondary); font-size: 1.05em; line-height: 1.8; }}
        
        /* Buttons */
        .btn-primary {{ display: inline-block; background: var(--secondary); color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-weight: 600; transition: all 0.3s; }}
        .btn-primary:hover {{ background: #2563EB; transform: translateY(-2px); }}
        
        .footer {{ text-align: center; margin-top: 40px; color: white; padding: 25px; background: rgba(0,0,0,0.3); border-radius: 15px; }}
        .contact-info {{ display: flex; justify-content: center; flex-wrap: wrap; gap: 15px; margin-top: 15px; }}
        .contact-link {{ color: #fff; text-decoration: none; padding: 8px 16px; background: rgba(255,255,255,0.2); border-radius: 20px; display: flex; align-items: center; gap: 6px; transition: all 0.3s; }}
        /* Sidebar and Header */
        .fixed-header {{ position: fixed; top: 0; left: 0; right: 0; background: linear-gradient(135deg, #3B82F6, #8B5CF6); padding: 15px 20px; z-index: 1000; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }}
        .fixed-vajra {{ color: white; font-size: 1.5em; font-weight: 800; letter-spacing: 2px; }}
        .menu-toggle {{ background: none; border: none; color: white; font-size: 1.5em; cursor: pointer; padding: 5px; }}
        .sidebar {{ position: fixed; top: 0; left: -300px; width: 300px; height: 100vh; background: linear-gradient(135deg, rgba(26,42,108,0.98) 0%, rgba(178,31,31,0.98) 100%); z-index: 1001; padding: 80px 20px 20px 20px; transition: all 0.3s ease; overflow-y: auto; }}
        .sidebar.open {{ left: 0; box-shadow: 5px 0 25px rgba(0,0,0,0.5); }}
        .close-sidebar {{ position: absolute; top: 15px; left: 15px; background: none; border: none; color: white; font-size: 1.5em; cursor: pointer; }}
        .nav-item {{ display: flex; align-items: center; gap: 15px; padding: 15px; color: white; text-decoration: none; border-radius: 8px; margin-bottom: 10px; transition: all 0.3s ease; cursor: pointer; }}
        .nav-item:hover {{ background: rgba(255,255,255,0.2); transform: translateX(5px); }}
        #backToTop {{ position: fixed; bottom: 20px; right: 20px; width: 50px; height: 50px; background: var(--primary); color: white; border: none; border-radius: 50%; font-size: 22px; cursor: pointer; display: none; z-index: 1100; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }}
        #backToTop.show {{ display: flex; align-items: center; justify-content: center; }}
        .contact-link:hover {{ transform: scale(1.1); background: rgba(255,255,255,0.3); }}
    </style>
</head>
<body>
    <div class="fixed-header" id="fixedHeader">
        <button class="menu-toggle" id="menuToggle"><i class="fas fa-bars"></i></button>
        <div class="fixed-vajra">Automation Report</div>
        <div></div>
    </div>
    
    <div class="sidebar" id="sidebar">
        <button class="close-sidebar" id="closeSidebar"><i class="fas fa-times"></i></button>
        <div class="nav-item" onclick="scrollToSection('executive-summary')"><i class="fas fa-chart-line"></i> Executive Summary</div>
        <div class="nav-item" onclick="scrollToSection('domain-analysis')"><i class="fas fa-globe"></i> Domain Analysis</div>
        <div class="nav-item" onclick="scrollToSection('dns-analysis')"><i class="fas fa-server"></i> DNS Analysis</div>
        <div class="nav-item" onclick="scrollToSection('subdomain-mapping')"><i class="fas fa-sitemap"></i> Subdomain Mapping</div>
        <div class="nav-item" onclick="scrollToSection('service-discovery')"><i class="fas fa-heartbeat"></i> Service Discovery</div>
        <div class="nav-item" onclick="scrollToSection('network-analysis')"><i class="fas fa-network-wired"></i> Network Analysis</div>
        <div class="nav-item" onclick="scrollToSection('nuclei-scan')"><i class="fas fa-bug"></i> Nuclei Scan</div>
        <div class="nav-item" onclick="scrollToSection('nikto-scan')"><i class="fas fa-search"></i> Nikto Scan</div>
        <div class="nav-item" onclick="scrollToSection('eyewitness-screenshots')"><i class="fas fa-camera"></i> Screenshots</div>
        <div class="nav-item" onclick="scrollToSection('security-recommendations')"><i class="fas fa-clipboard-check"></i> Recommendations</div>
        <div class="nav-item" onclick="window.print()"><i class="fas fa-file-pdf"></i> Download PDF</div>
    </div>
    
    <div class="container" style="margin-top: 80px;">
        {header}
        {executive_summary}
        {body}
        {footer}
    </div>
    
    <button id="backToTop" title="Go to top"><i class="fas fa-arrow-up"></i></button>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const menuToggle = document.getElementById('menuToggle');
            const sidebar = document.getElementById('sidebar');
            const closeSidebar = document.getElementById('closeSidebar');
            const backToTopBtn = document.getElementById('backToTop');
            
            menuToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
            closeSidebar.addEventListener('click', () => sidebar.classList.remove('open'));
            
            window.addEventListener('scroll', () => {{
                if (window.scrollY > 200) {{
                    backToTopBtn.classList.add('show');
                }} else {{
                    backToTopBtn.classList.remove('show');
                }}
            }});
            
            backToTopBtn.addEventListener('click', () => {{
                window.scrollTo({{ top: 0, behavior: 'smooth' }});
            }});
        }});
        
        function scrollToSection(sectionId) {{
            const el = document.getElementById(sectionId);
            if (el) {{
                el.scrollIntoView({{ behavior: 'smooth' }});
                document.getElementById('sidebar').classList.remove('open');
            }}
        }}
        
        function toggleSection(btn) {{ btn.closest('.section').classList.toggle('collapsed'); }}
        function copyToClipboard(text) {{ navigator.clipboard.writeText(text).then(() => alert('Copied: ' + text)); }}
        function copyTable(btn) {{
            const table = btn.nextElementSibling;
            let text = '';
            for (const row of table.rows) {{
                let rowText = [];
                for(const cell of row.cells) {{ rowText.push(cell.textContent); }}
                text += rowText.join('\\t') + '\\n';
            }}
            copyToClipboard(text);
        }}
    </script>
</body>
</html>
        """

def generate_report(target, target_dir, module_choices):
    """
    Entry point function to generate the HTML report.
    Accepts both numeric codes AND tool names.
    """
    json_gen = FinalJsonGenerator(target, target_dir)
    if not json_gen.generate():
        return False
        
    report_gen = ReportGenerator(target, target_dir, module_choices)
    if report_gen.load_data():
        html_content = report_gen.generate_html()
        if html_content:
            return report_gen.save_report(html_content)
    return False
