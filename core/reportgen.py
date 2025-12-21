# VAJRA HTML Report Generator
# Description: Generates the final, fully-styled HTML report from the structured final.json file.

import os
import json
from core.jsonparser import FinalJsonGenerator

class ReportGenerator:
    """
    Generates an HTML report from a final.json data file.
    """
    def __init__(self, target, target_dir, module_choices):
        self.target = target
        self.target_dir = target_dir
        self.module_choices = set(module_choices.split())
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
        
        # Conditionally build the report body based on selected modules
        if 'whois' in self.data and ('1' in self.module_choices or '0' in self.module_choices):
            body_sections.append(self._generate_whois_section())
        
        if 'subdomains' in self.data and ('4' in self.module_choices or '0' in self.module_choices):
            body_sections.append(self._generate_subdomain_section())
            
        if 'services' in self.data and ('4' in self.module_choices or '0' in self.module_choices):
            body_sections.append(self._generate_service_section())
        
        if 'nmap' in self.data and ('5' in self.module_choices or '0' in self.module_choices):
              body_sections.append(self._generate_nmap_section())
        
        # Add recommendations if more than just Whois was run
        if len(self.module_choices.intersection({'0', '4', '5'})) > 0:
            body_sections.append(self._generate_recommendations_section())

        # The main template is now embedded, so we pass the parts to it
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

    # --- METHODS TO GENERATE DYNAMIC HTML SECTIONS ---
    def _generate_header(self):
        scan_info = self.data.get('scan_info', {})
        target_name = scan_info.get('target', 'N/A')
        scan_date = scan_info.get('scan_date', 'N/A')
        risk_level = scan_info.get('risk_level', 'Medium')
        return f"""
        <div class="header">
            <div class="header-top">
                <div>
                    <div class="vajra-title">VAJRA</div>
                    <div class="vajra-subtitle">Multi-layered Red Team Reconnaissance Framework</div>
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
                    <p id="scanDateDisplay">{scan_date}</p>
                </div>
                <div class="info-item risk">
                    <h3><i class="fas fa-shield-alt"></i> Risk Level</h3>
                    <p>{risk_level}</p>
                </div>
            </div>
        </div>
        """

    def _generate_executive_summary(self):
        # This section is always present
        return """
        <div class="section executive" id="executive-summary">
            <h2 class="section-header">
                <div><i class="fas fa-chart-line"></i> Executive Summary</div>
                 <button class="toggle-btn" onclick="toggleSection(this)"><i class="fas fa-chevron-up"></i></button>
            </h2>
            <div class="section-content">
                <div class="code-block">
                    <button class="copy-button" onclick="copyCode(this)">Copy</button>
                    <code>This report summarizes the findings from the reconnaissance scan performed by the VAJRA framework.</code>
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
                        <tr><td><strong>Name Servers</strong></td><td><ul>{name_servers_html}</ul></td></tr>
                        <tr><td><strong>DNSSEC Status</strong></td><td>{whois.get('dnssec_status', 'N/A')}</td></tr>
                        <tr><td><strong>Registrant Org</strong></td><td>{whois.get('registrant_organization', 'N/A')}</td></tr>
                        <tr><td><strong>Registrant Country</strong></td><td>{whois.get('registrant_country', 'N/A')}</td></tr>
                    </table>
                </div>
            </div>
        </div>
        """

    def _generate_subdomain_section(self):
        subdomains_data = self.data.get('subdomains', {})
        subdomains_list_html = ''.join(f'<tr><td>{sub}</td></tr>' for sub in subdomains_data.get('subdomains', []))
        return f"""
        <div class="section subdomain" id="subdomain-mapping">
            <h2 class="section-header">
                <div><i class="fas fa-sitemap"></i> Subdomain Infrastructure Mapping</div>
                <button class="toggle-btn" onclick="toggleSection(this)"><i class="fas fa-chevron-up"></i></button>
            </h2>
            <div class="section-content">
                <div class="code-block"><button class="copy-button" onclick="copyCode(this)">Copy</button><code>Total Alive Subdomains: {subdomains_data.get('total_alive', 0)}</code></div>
                <div style="position: relative;">
                    <button class="table-copy" onclick="copyTable(this)">Copy Table</button>
                    <table class="compact-table">
                        <thead><tr><th>Alive Subdomains</th></tr></thead>
                        <tbody>{subdomains_list_html}</tbody>
                    </table>
                </div>
            </div>
        </div>
        """

    def _generate_service_section(self):
        services = self.data.get('services', [])
        rows_html = ""
        for s in services:
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
        hosts_html = ""
        for host in nmap.get('hosts', []):
            hosts_html += f"<div class='url-header'>{host.get('hostname', 'N/A')} ({host.get('ip_address', '')})</div>"
            ports_html = ""
            for port in host.get('open_ports', []):
                ports_html += f"""
                <div class="service-item">
                    <div class="service-header">
                        <span class="service-port">Port {port.get('port_id')}/{port.get('protocol')}</span>
                        <span style="color: var(--accent); font-weight: 600;">{port.get('service_name', 'N/A').upper()}</span>
                    </div>
                    <div class="service-details">{port.get('service_version', 'N/A')}</div>
                    <div class="service-recommendation"><i class="fas fa-exclamation-triangle"></i> {port.get('recommendation', 'N/A')}</div>
                </div>
                """
            hosts_html += f"<div class='service-grid'>{ports_html}</div>"

        return f"""
        <div class="section network" id="network-analysis">
            <h2 class="section-header">
                <div><i class="fas fa-network-wired"></i> Network Infrastructure Analysis</div>
                <button class="toggle-btn" onclick="toggleSection(this)"><i class="fas fa-chevron-up"></i></button>
            </h2>
            <div class="section-content">
                <div class="code-block"><button class="copy-button" onclick="copyCode(this)">Copy</button><code>Scan Type: {summary.get('scan_type', 'N/A')} | Total Open Ports: {summary.get('total_open_ports', 0)}</code></div>
                {hosts_html}
            </div>
        </div>
        """

    def _generate_recommendations_section(self):
        return """
        <div class="section security" id="security-recommendations">
            <h2 class="section-header">
                <div><i class="fas fa-clipboard-check"></i> Security Recommendations</div>
                <button class="toggle-btn" onclick="toggleSection(this)"><i class="fas fa-chevron-up"></i></button>
            </h2>
            <div class="section-content">
                <div class="code-block"><button class="copy-button" onclick="copyCode(this)">Copy</button><code>Priority Actions: Review all findings and prioritize remediation based on risk.</code></div>
                 <div style="position: relative;">
                    <button class="table-copy" onclick="copyTable(this)">Copy Table</button>
                    <table class="compact-table">
                        <thead><tr><th>Priority</th><th>Recommendation</th><th>Timeline</th></tr></thead>
                        <tbody>
                            <tr>
                                <td><span style="color: var(--accent);">High</span></td>
                                <td>Address all critical and high-risk findings from the Network Analysis section immediately.</td>
                                <td>Immediate</td>
                            </tr>
                            <tr>
                                <td><span style="color: var(--warning);">Medium</span></td>
                                <td>Review web service configurations for security headers (HSTS, CSP) and updated software versions.</td>
                                <td>1-2 Weeks</td>
                            </tr>
                            <tr>
                                <td><span style="color: var(--success);">Low</span></td>
                                <td>Regularly review domain registration details for accuracy and ensure DNSSEC is enabled.</td>
                                <td>Ongoing</td>
                            </tr>
                        </tbody>
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
        # --- CHANGE START: Added Google Font import and interactive hover styles ---
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
            --primary: #2c3e50; --secondary: #3498db; --accent: #e74c3c; --success: #27ae60;
            --warning: #f39c12; --danger: #c0392b; --light: #ecf0f1; --dark: #2c3e50;
            --header-gradient: linear-gradient(135deg, #fdbb2d, #b21f1f, #1a2a6c);
            --executive-bg: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            --domain-bg: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            --subdomain-bg: linear-gradient(135deg, #cce5ff 0%, #b8daff 100%);
            --service-bg: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
            --network-bg: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            --security-bg: linear-gradient(135deg, #d6d8d9 0%, #c6c8ca 100%);
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Montserrat', sans-serif; line-height: 1.6; background: linear-gradient(135deg, #0f0f0f, #1a2a6c, #b21f1f); color: #333; min-height: 100vh; position: relative; overflow-x: hidden; }}
        body::before {{ content: ''; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: url('https://images.unsplash.com/photo-1544890225-2f3faec4cd60?w=500&h=500&fit=crop') center/cover, url('https://images.unsplash.com/photo-1563207153-f403bf289096?w=500&h=500&fit=crop') 20% 30%/cover, url('https://images.unsplash.com/photo-1555949963-ff9fe0c870eb?w=500&h=500&fit=crop') 80% 70%/cover; background-blend-mode: overlay; opacity: 0.05; pointer-events: none; z-index: -1; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .fixed-header {{ position: fixed; top: 0; left: 0; right: 0; background: var(--header-gradient); padding: 15px 20px; z-index: 1000; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 20px rgba(0,0,0,0.3); transition: all 0.3s ease; backdrop-filter: blur(10px); }}
        .fixed-header.small {{ padding: 10px 20px; }}
        .fixed-header-title {{ display: flex; align-items: center; gap: 15px; width: 100%; justify-content: center; }}
        .fixed-vajra {{ background: linear-gradient(45deg, #ff6b6b, #ee5a24, #f39c12, #27ae60, #3498db, #9b59b6, #ff6b6b); background-size: 400% 400%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 1.8em; font-weight: 800; text-transform: uppercase; letter-spacing: 2px; animation: rainbow 8s ease-in-out infinite; }}
        .fixed-subtitle {{ color: white; font-size: 0.9em; opacity: 0.9; display: none; }}
        .fixed-header.small .fixed-subtitle {{ display: block; }}
        .menu-toggle {{ background: none; border: none; color: white; font-size: 1.5em; cursor: pointer; padding: 5px; border-radius: 5px; transition: all 0.3s ease; position: absolute; left: 20px; }}
        .sidebar {{ position: fixed; top: 0; left: -300px; width: 300px; height: 100vh; background: linear-gradient(135deg, rgba(26,42,108,0.98) 0%, rgba(178,31,31,0.98) 100%); z-index: 1001; padding: 80px 20px 20px 20px; transition: all 0.3s ease; backdrop-filter: blur(10px); overflow-y: auto; }}
        .sidebar.open {{ left: 0; box-shadow: -5px 0 25px rgba(0,0,0,0.3); }}
        .close-sidebar {{ position: absolute; top: 15px; left: 15px; background: none; border: none; color: white; font-size: 1.5em; cursor: pointer; }}
        .nav-item {{ display: flex; align-items: center; gap: 15px; padding: 15px; color: white; text-decoration: none; border-radius: 8px; margin-bottom: 10px; transition: all 0.3s ease; cursor: pointer; }}
        .nav-item:hover {{ background: rgba(255,255,255,0.2); transform: translateX(-5px) scale(1.03); }}
        .nav-item i {{ font-size: 1.2em; width: 25px; text-align: center; }}
        .header {{ background: rgba(255,255,255,0.98); padding: 30px; border-radius: 20px; box-shadow: 0 15px 40px rgba(0,0,0,0.1); margin: 80px 0 30px 0; text-align: center; border: 1px solid rgba(0,0,0,0.1); }}
        .vajra-title {{ background: linear-gradient(45deg, #ff6b6b, #ee5a24, #f39c12, #27ae60, #3498db, #9b59b6, #ff6b6b); background-size: 400% 400%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3.5em; font-weight: 800; text-transform: uppercase; animation: rainbow 8s ease-in-out infinite; }}
        @keyframes rainbow {{ 0%{{background-position:0% 50%}} 50%{{background-position:100% 50%}} 100%{{background-position:0% 50%}} }}
        .vajra-subtitle {{ color: var(--primary); font-size: 1.2em; font-weight: 600; margin-top: 5px; }}
        .report-title {{ color: var(--secondary); font-size: 2.2em; margin: 10px 0 15px 0; padding-top: 15px; border-top: 3px solid var(--accent); font-weight: 700; }}
        .scan-info {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; margin-top: 20px; }}
        .info-item {{ padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.1); color: #fff; cursor: pointer; position: relative; transition: transform 0.3s ease; }}
        .info-item:hover {{ transform: scale(1.05); }}
        .copy-badge {{ position: absolute; top: 10px; right: 10px; background: rgba(255,255,255,0.2); border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.3s; }}
        .info-item:hover .copy-badge {{ opacity: 1; }}
        .info-item.target {{ background: linear-gradient(135deg, #3498db 0%, #2c3e50 100%); }}
        .info-item.date {{ background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); }}
        .info-item.risk {{ background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%); }}
        .info-item h3 {{ margin-bottom: 8px; font-size: 1.1em; }}
        .info-item p {{ font-size: 1em; font-weight: 600; }}
        .section {{ background: rgba(255,255,255,0.97); padding: 25px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); margin-bottom: 25px; border-left: 5px solid; }}
        .section.executive {{ background: var(--executive-bg); border-left-color: #ffc107; }} .section.domain {{ background: var(--domain-bg); border-left-color: #28a745; }}
        .section.subdomain {{ background: var(--subdomain-bg); border-left-color: #007bff; }} .section.service {{ background: var(--service-bg); border-left-color: #17a2b8; }}
        .section.network {{ background: var(--network-bg); border-left-color: #dc3545; }} .section.security {{ background: var(--security-bg); border-left-color: #6c757d; }}
        .section-header {{ display: flex; align-items: center; justify-content: space-between; font-size: 1.8em; font-weight: 600; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 2px solid var(--accent); color: var(--primary); }}
        .toggle-btn {{ background: none; border: none; color: var(--dark); font-size: 1rem; cursor: pointer; transition: transform 0.3s ease; }}
        .toggle-btn i {{ transition: transform 0.3s ease; }}
        .section.collapsed .toggle-btn i {{ transform: rotate(180deg); }}
        .section.collapsed .section-content {{ display: none; }}
        .compact-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .compact-table th {{ background: linear-gradient(135deg, var(--secondary) 0%, #2980b9 100%); color: white; padding: 12px; text-align: left; font-weight: 600; }}
        .compact-table td {{ padding: 10px 12px; border-bottom: 1px solid #dee2e6; }}
        .compact-table td ul {{ padding-left: 20px; }}
        .compact-table tr:last-child td {{ border-bottom: none; }}
        .status-badge {{ padding: 4px 8px; border-radius: 12px; font-size: 0.85em; font-weight: 600; }}
        .status-200 {{ background: #d4edda; color: #155724; }} .status-302 {{ background: #fff3cd; color: #856404; }} .status-404 {{ background: #f8d7da; color: #721c24; }}
        .code-block {{ position: relative; background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 8px; margin: 15px 0; font-family: 'Courier New', monospace; overflow-x: auto; }}
        .copy-button, .table-copy {{ position: absolute; top: 10px; right: 10px; background: rgba(255,255,255,0.2); color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 0.8em; }}
        .service-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin: 15px 0; }}
        .service-item {{ background: white; padding: 15px; border-radius: 8px; border-left: 4px solid var(--secondary); box-shadow: 0 2px 6px rgba(0,0,0,0.1); transition: transform 0.3s ease; }}
        .service-item:hover {{ transform: scale(1.03); }}
        .service-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
        .service-port {{ font-weight: 700; color: var(--primary); }}
        .service-details {{ font-size: 0.9em; color: #6c757d; }}
        .service-recommendation {{ margin-top: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px; border-left: 3px solid var(--warning); font-size: 0.85em; }}
        .url-header {{ background: linear-gradient(135deg, var(--secondary) 0%, #2980b9 100%); color: white; padding: 12px; border-radius: 8px 8px 0 0; margin-top: 20px; font-weight: 600; }}
        .footer {{ text-align: center; margin-top: 40px; color: white; padding: 25px; background: rgba(0,0,0,0.3); border-radius: 15px; }}
        .contact-info {{ display: flex; justify-content: center; flex-wrap: wrap; gap: 15px; margin-top: 15px; }}
        .contact-link {{ color: #fff; text-decoration: none; padding: 8px 16px; background: rgba(255,255,255,0.2); border-radius: 20px; display: flex; align-items: center; gap: 6px; font-size: 0.9em; transition: transform 0.3s ease, background-color 0.3s ease; }}
        .contact-link:hover {{ transform: scale(1.1); background: rgba(255,255,255,0.3); }}
        #backToTop {{ position: fixed; bottom: 20px; right: 20px; width: 50px; height: 50px; background: var(--primary); color: white; border: none; border-radius: 50%; font-size: 22px; cursor: pointer; display: none; align-items: center; justify-content: center; z-index: 1100; }}
        #backToTop.show {{ display: flex; }}
        @media print {{
            @page {{ size: A4; margin: 15mm; }}
            body {{
                font-size: 10pt;
                background: #fff !important;
                color: #000 !important;
                -webkit-print-color-adjust: exact;
                color-adjust: exact;
            }}
            .fixed-header, .sidebar, #backToTop, .copy-button, .table-copy, .toggle-btn, .copy-badge {{ display: none !important; }}
            .section:not(#executive-summary) {{ page-break-before: always; }}
            .container {{ max-width: 100%; padding: 0; margin: 0; }}
            .header, .section, .footer {{
                box-shadow: none !important;
                border: 1px solid #ddd !important;
                background: #fff !important;
                padding: 15px;
                border-radius: 0 !important;
            }}
            .vajra-title {{ font-size: 2.5em; -webkit-text-fill-color: var(--primary); background: none; animation: none; }}
            .report-title {{ font-size: 1.8em; }}
            .section-header {{ font-size: 1.5em; padding-bottom: 8px; margin-bottom: 15px; }}
            .scan-info {{ grid-template-columns: repeat(3, 1fr); }}
            .info-item, .info-item.target, .info-item.date, .info-item.risk {{
                background: #f0f0f0 !important;
                border: 1px solid #ccc;
                color: #000 !important;
            }}
            .info-item h3, .info-item p {{ color: #000 !important; }}
            a {{ color: var(--secondary); text-decoration: none; }}
            .footer {{ background: none !important; color: #333 !important; border-top: 1px solid #ccc; }}
            .contact-info {{ display: flex !important; justify-content: center; }}
            .contact-link {{ background: #f0f0f0 !important; color: #333 !important; border: 1px solid #ccc; }}
        }}
    </style>
</head>
<body>
    <div class="fixed-header" id="fixedHeader">
        <div class="fixed-header-title">
            <div class="fixed-vajra">VAJRA</div>
            <div class="fixed-subtitle">Multi-layered Red Team Reconnaissance Framework</div>
        </div>
        <button class="menu-toggle" id="menuToggle"><i class="fas fa-bars"></i></button>
    </div>
    <div class="sidebar" id="sidebar">
        <button class="close-sidebar" id="closeSidebar"><i class="fas fa-times"></i></button>
        <div class="nav-item" onclick="scrollToSection('executive-summary')"><i class="fas fa-chart-line"></i> Executive Summary</div>
        <div class="nav-item" onclick="scrollToSection('domain-analysis')"><i class="fas fa-globe"></i> Domain Analysis</div>
        <div class="nav-item" onclick="scrollToSection('subdomain-mapping')"><i class="fas fa-sitemap"></i> Subdomain Mapping</div>
        <div class="nav-item" onclick="scrollToSection('service-discovery')"><i class="fas fa-heartbeat"></i> Service Discovery</div>
        <div class="nav-item" onclick="scrollToSection('network-analysis')"><i class="fas fa-network-wired"></i> Network Analysis</div>
        <div class="nav-item" onclick="scrollToSection('security-recommendations')"><i class="fas fa-clipboard-check"></i> Security Recommendations</div>
        <div class="nav-item" onclick="downloadPDF()"><i class="fas fa-file-pdf"></i> Download PDF</div>
    </div>
    <div class="container">
        {header}
        {executive_summary}
        {body}
        {footer}
    </div>
    <button id="backToTop" title="Go to top"><i class="fas fa-arrow-up"></i></button>
    <script>
        document.addEventListener('DOMContentLoaded', function () {{
            const fixedHeader = document.getElementById('fixedHeader');
            window.addEventListener('scroll', () => {{ window.scrollY > 100 ? fixedHeader.classList.add('small') : fixedHeader.classList.remove('small'); }});
            document.getElementById('menuToggle').addEventListener('click', () => document.getElementById('sidebar').classList.toggle('open'));
            document.getElementById('closeSidebar').addEventListener('click', () => document.getElementById('sidebar').classList.remove('open'));
            const backToTopBtn = document.getElementById("backToTop");
            window.addEventListener("scroll", () => {{ window.scrollY > 200 ? backToTopBtn.classList.add("show") : backToTopBtn.classList.remove("show"); }});
            backToTopBtn.addEventListener("click", () => window.scrollTo({{ top: 0, behavior: "smooth" }}));
        }});
        function scrollToSection(sectionId) {{ const el = document.getElementById(sectionId); if (el) {{ el.scrollIntoView({{ behavior: 'smooth' }}); document.getElementById('sidebar').classList.remove('open'); }} }}
        function downloadPDF() {{ window.print(); }}
        function copyToClipboard(text) {{ navigator.clipboard.writeText(text).then(() => alert('Copied: ' + text), () => alert('Failed to copy')); }}
        function copyCode(btn) {{ const code = btn.parentElement.querySelector('code').textContent; copyToClipboard(code); }}
        function copyTable(btn) {{ const table = btn.nextElementSibling; let text = ''; for (const row of table.rows) {{ let rowText = []; for(const cell of row.cells) {{ rowText.push(cell.textContent); }} text += rowText.join('\\t') + '\\n'; }} copyToClipboard(text); }}
        function toggleSection(btn) {{ const section = btn.closest('.section'); section.classList.toggle('collapsed'); }}
    </script>
</body>
</html>
        """

def generate_report(target, target_dir, module_choices):
    """
    Entry point function to generate the HTML report.
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
