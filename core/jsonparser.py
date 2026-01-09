# VAJRA JSON Parser & Generator
# Enhanced version with Nuclei, Nikto, Dig, and EyeWitness support

import os
import json
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from datetime import datetime

class FinalJsonGenerator:
    """
    Parses various log files from a VAJRA scan and creates a consolidated JSON output.
    Now supports: Whois, Dig, Subdomains, Services, Nmap, Nuclei, Nikto, EyeWitness
    """
    def __init__(self, target, target_dir):
        self.target = target
        self.target_dir = target_dir
        self.log_dir = os.path.join(self.target_dir, "Logs")
        self.json_dir = os.path.join(self.target_dir, "JSON")
        self.screenshots_dir = os.path.join(self.target_dir, "Screenshots")
        self.final_data = {
            "scan_info": {
                "target": self.target,
                "scan_date": "N/A",
                "risk_level": "Medium",
                "scan_duration": "N/A"
            }
        }

    def parse_whois(self):
        """Parses the whois.txt log file."""
        whois_file = os.path.join(self.log_dir, "whois.txt")
        if not os.path.exists(whois_file):
            return None

        try:
            with open(whois_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            data = {
                'domain_name': self._search(r"Domain Name:\s*(.*)", content),
                'registrar': self._search(r"Registrar:\s*(.*)", content),
                'registrar_url': self._search(r"Registrar URL:\s*(.*)", content),
                'creation_date': self._search(r"Creation Date:\s*(.*)", content),
                'updated_date': self._search(r"Updated Date:\s*(.*)", content),
                'expiration_date': self._search(r"Registry Expiry Date:\s*(.*)|Registrar Registration Expiration Date:\s*(.*)", content),
                'name_servers': re.findall(r"Name Server:\s*(.*)", content) or ["N/A"],
                'dnssec_status': self._search(r"DNSSEC:\s*(.*)", content),
                'registrant_organization': self._search(r"Registrant Organization:\s*(.*)", content),
                'registrant_country': self._search(r"Registrant Country:\s*(.*)", content),
                'registrant_email': self._search(r"Registrant Email:\s*(.*)", content),
                'admin_email': self._search(r"Admin Email:\s*(.*)", content),
                'tech_email': self._search(r"Tech Email:\s*(.*)", content),
            }
            return data
        except Exception as e:
            return None
    
    def parse_dig(self):
        """Parses the dig.txt log file for DNS records."""
        dig_file = os.path.join(self.log_dir, "dig.txt")
        if not os.path.exists(dig_file):
            return None
        
        try:
            with open(dig_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            data = {
                'a_records': [],
                'aaaa_records': [],
                'mx_records': [],
                'ns_records': [],
                'txt_records': [],
                'cname_records': [],
                'soa_record': None
            }
            
            # Parse A records
            a_matches = re.findall(r"(\S+)\s+\d+\s+IN\s+A\s+(\S+)", content)
            data['a_records'] = [{'name': m[0], 'ip': m[1]} for m in a_matches]
            
            # Parse AAAA records (IPv6)
            aaaa_matches = re.findall(r"(\S+)\s+\d+\s+IN\s+AAAA\s+(\S+)", content)
            data['aaaa_records'] = [{'name': m[0], 'ip': m[1]} for m in aaaa_matches]
            
            # Parse MX records
            mx_matches = re.findall(r"(\S+)\s+\d+\s+IN\s+MX\s+(\d+)\s+(\S+)", content)
            data['mx_records'] = [{'domain': m[0], 'priority': m[1], 'server': m[2]} for m in mx_matches]
            
            # Parse NS records
            ns_matches = re.findall(r"(\S+)\s+\d+\s+IN\s+NS\s+(\S+)", content)
            data['ns_records'] = [{'domain': m[0], 'nameserver': m[1]} for m in ns_matches]
            
            # Parse TXT records
            txt_matches = re.findall(r'(\S+)\s+\d+\s+IN\s+TXT\s+"([^"]+)"', content)
            data['txt_records'] = [{'domain': m[0], 'text': m[1]} for m in txt_matches]
            
            # Parse CNAME records
            cname_matches = re.findall(r"(\S+)\s+\d+\s+IN\s+CNAME\s+(\S+)", content)
            data['cname_records'] = [{'alias': m[0], 'canonical': m[1]} for m in cname_matches]
            
            # Parse SOA record
            soa_match = re.search(r"(\S+)\s+\d+\s+IN\s+SOA\s+(\S+)\s+(\S+)\s+\(", content)
            if soa_match:
                data['soa_record'] = {
                    'domain': soa_match.group(1),
                    'primary_ns': soa_match.group(2),
                    'admin_email': soa_match.group(3)
                }
            
            # Only return if we found something
            if any([data['a_records'], data['mx_records'], data['ns_records'], data['txt_records']]):
                return data
            return None
            
        except Exception as e:
            return None

    def parse_subdomains(self):
        """Parses alive.txt for a list of live subdomains."""
        subdomain_file = os.path.join(self.log_dir, "alive.txt")
        if not os.path.exists(subdomain_file):
            return None
        
        try:
            with open(subdomain_file, 'r') as f:
                subdomains = [line.strip() for line in f if line.strip()]
            
            # Also get total discovered (before filtering)
            all_subdomains_file = os.path.join(self.log_dir, "subdomains.txt")
            total_discovered = 0
            if os.path.exists(all_subdomains_file):
                with open(all_subdomains_file, 'r') as f:
                    total_discovered = len([line.strip() for line in f if line.strip()])
            
            summary = {
                "total_discovered": total_discovered,
                "total_alive": len(subdomains),
                "subdomains": subdomains[:500] if subdomains else ["N/A"]  # Limit to 500 for report
            }
            return summary
        except Exception as e:
            return None

    def parse_services(self):
        """Parses alive.txt for basic service info (fallback if no alive.json)."""
        alive_file = os.path.join(self.log_dir, "alive.txt")
        if not os.path.exists(alive_file):
            return None
        
        try:
            services_data = []
            with open(alive_file, 'r') as f:
                for line in f:
                    url = line.strip()
                    if not url:
                        continue
                    
                    try:
                        parsed = urlparse(url)
                        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
                        
                        services_data.append({
                            "url": url,
                            "host": parsed.hostname or "N/A",
                            "port": port,
                            "webserver": "N/A"
                        })
                    except:
                        continue
            
            return services_data if services_data else None
        except Exception as e:
            return None

    def parse_nmap(self):
        """Parses an Nmap XML file."""
        nmap_file = self._find_nmap_xml()
        if not nmap_file:
            return None

        try:
            tree = ET.parse(nmap_file)
            root = tree.getroot()
            
            nmap_data = {
                "scan_summary": {
                    "scan_type": root.find('scaninfo').get('type').upper() if root.find('scaninfo') is not None else "N/A",
                    "duration": root.find('runstats/finished').get('timestr') if root.find('runstats/finished') is not None else "N/A",
                    "total_open_ports": 0
                },
                "hosts": []
            }

            total_open_ports = 0
            for host in root.findall('host'):
                host_info = {
                    "hostname": self._get_hostname(host),
                    "ip_address": host.find('address').get('addr') if host.find('address') is not None else "N/A",
                    "open_ports": []
                }
                
                ports = host.find('ports')
                if ports:
                    for port in ports.findall('port'):
                        state = port.find('state')
                        if state is not None and state.get('state') == 'open':
                            total_open_ports += 1
                            service = port.find('service')
                            port_info = {
                                "port_id": port.get('portid'),
                                "protocol": port.get('protocol'),
                                "service_name": service.get('name', 'N/A') if service is not None else 'N/A',
                                "service_version": self._get_service_version(service),
                                "recommendation": self._get_recommendation(port.get('portid'), service.get('name', 'N/A') if service is not None else 'N/A')
                            }
                            host_info["open_ports"].append(port_info)
                
                if host_info["open_ports"]:
                    nmap_data["hosts"].append(host_info)

            nmap_data["scan_summary"]["total_open_ports"] = total_open_ports
            return nmap_data if nmap_data["hosts"] else None
        except Exception as e:
            return None
    
    def parse_nuclei(self):
        """Parses Nuclei vulnerability scan results."""
        nuclei_file = os.path.join(self.log_dir, "nuclei.txt")
        if not os.path.exists(nuclei_file) or os.path.getsize(nuclei_file) == 0:
            return None
        
        try:
            vulnerabilities = []
            severity_count = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
            
            with open(nuclei_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse Nuclei output format: [severity] [template-id] url
                    parts = line.split()
                    if len(parts) >= 3:
                        severity = 'medium'  # default
                        
                        # Try to extract severity
                        for part in parts:
                            part_lower = part.lower().strip('[]')
                            if part_lower in ['critical', 'high', 'medium', 'low', 'info']:
                                severity = part_lower
                                severity_count[severity] += 1
                                break
                        
                        vuln = {
                            'severity': severity,
                            'title': parts[1] if len(parts) > 1 else 'Unknown',
                            'url': parts[-1] if len(parts) > 0 else 'N/A',
                            'description': line
                        }
                        vulnerabilities.append(vuln)
            
            if not vulnerabilities:
                return None
            
            return {
                'total_findings': len(vulnerabilities),
                'severity_breakdown': severity_count,
                'vulnerabilities': vulnerabilities[:100]  # Limit to 100 for report
            }
        except Exception as e:
            return None
    
    def parse_nikto(self):
        """Parses Nikto web server scan results."""
        nikto_file = os.path.join(self.log_dir, "nikto.txt")
        if not os.path.exists(nikto_file) or os.path.getsize(nikto_file) == 0:
            return None
        
        try:
            findings = []
            targets_scanned = []
            
            with open(nikto_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract target hosts
            target_matches = re.findall(r"- Nikto v.*? - Target IP:\s+(\S+)", content)
            targets_scanned = list(set(target_matches))
            
            # Extract findings (lines starting with +)
            finding_lines = re.findall(r"^\+\s+(.+)$", content, re.MULTILINE)
            
            for finding in finding_lines[:100]:  # Limit to 100
                finding = finding.strip()
                if finding and len(finding) > 10:  # Filter out noise
                    # Categorize severity
                    severity = 'info'
                    if any(word in finding.lower() for word in ['vulnerability', 'exploit', 'backdoor', 'shell']):
                        severity = 'high'
                    elif any(word in finding.lower() for word in ['disclosure', 'exposure', 'misconfiguration']):
                        severity = 'medium'
                    
                    findings.append({
                        'severity': severity,
                        'description': finding
                    })
            
            if not findings:
                return None
            
            return {
                'targets_scanned': targets_scanned,
                'total_findings': len(findings),
                'findings': findings
            }
        except Exception as e:
            return None
    
    def parse_eyewitness(self):
        """Check if EyeWitness screenshots exist."""
        if not os.path.exists(self.screenshots_dir):
            return None
        
        try:
            # Count images
            image_files = [f for f in os.listdir(self.screenshots_dir) 
                          if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            # Look for report.html
            report_html = os.path.join(self.screenshots_dir, "report.html")
            has_report = os.path.exists(report_html)
            
            if image_files or has_report:
                return {
                    'screenshot_count': len(image_files),
                    'report_path': report_html if has_report else None,
                    'directory': self.screenshots_dir
                }
            return None
        except Exception as e:
            return None

    def generate(self):
        """
        Orchestrates the parsing of all log files and writes the final JSON.
        """
        
        # Parse all available data
        whois_data = self.parse_whois()
        if whois_data:
            self.final_data['whois'] = whois_data

        dig_data = self.parse_dig()
        if dig_data:
            self.final_data['dig'] = dig_data

        subdomain_data = self.parse_subdomains()
        if subdomain_data:
            self.final_data['subdomains'] = subdomain_data

        service_data = self.parse_services()
        if service_data:
            self.final_data['services'] = service_data

        nmap_data = self.parse_nmap()
        if nmap_data:
            self.final_data['nmap'] = nmap_data
        
        nuclei_data = self.parse_nuclei()
        if nuclei_data:
            self.final_data['nuclei'] = nuclei_data
        
        nikto_data = self.parse_nikto()
        if nikto_data:
            self.final_data['nikto'] = nikto_data
        
        eyewitness_data = self.parse_eyewitness()
        if eyewitness_data:
            self.final_data['eyewitness'] = eyewitness_data
        
        # Update scan date and risk level
        self.final_data["scan_info"]["scan_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate risk level based on vulnerabilities
        if nuclei_data:
            severity = nuclei_data.get('severity_breakdown', {})
            if severity.get('critical', 0) > 0:
                self.final_data["scan_info"]["risk_level"] = "Critical"
            elif severity.get('high', 0) > 0:
                self.final_data["scan_info"]["risk_level"] = "High"
            elif severity.get('medium', 0) > 0:
                self.final_data["scan_info"]["risk_level"] = "Medium"
        
        # Save the final JSON file
        try:
            os.makedirs(self.json_dir, exist_ok=True)
            output_path = os.path.join(self.json_dir, "final.json")
            with open(output_path, 'w') as f:
                json.dump(self.final_data, f, indent=4)
            return True
        except Exception as e:
            return False

    # --- Helper Methods ---
    
    def _search(self, pattern, text, default="N/A"):
        """Utility to search for a regex pattern and return the first group or a default."""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return next((g for g in match.groups() if g is not None), default).strip()
        return default

    def _find_nmap_xml(self):
        """Finds the first Nmap XML file in the logs directory."""
        if not os.path.exists(self.log_dir):
            return None
        for filename in os.listdir(self.log_dir):
            if filename.endswith(".xml") and ("nmap" in filename.lower() or filename.startswith("nmap")):
                return os.path.join(self.log_dir, filename)
        return None
        
    def _get_hostname(self, host_element):
        """Extracts the most likely hostname from an Nmap host element."""
        hostname_elem = host_element.find("hostnames/hostname")
        if hostname_elem is not None and hostname_elem.get('name'):
            return hostname_elem.get('name')
        return self.target

    def _get_service_version(self, service_element):
        """Constructs a full service version string from Nmap data."""
        if service_element is None:
            return "N/A"
        parts = [
            service_element.get('product', ''),
            service_element.get('version', ''),
            service_element.get('extrainfo', '')
        ]
        full_version = ' '.join(p for p in parts if p).strip()
        return full_version if full_version else "N/A"
        
    def _get_recommendation(self, port, service_name):
        """Generates a basic recommendation based on port/service."""
        if port == "80" and "http" in service_name.lower():
            return "Unencrypted traffic. Redirect all HTTP traffic to HTTPS."
        if service_name == "ssh":
            return "Ensure strong password policies and disable root login."
        if "telnet" in service_name.lower():
            return "Telnet is insecure. Disable and use SSH instead."
        if port == "3389":
            return "RDP exposed. Ensure strong authentication and consider VPN access only."
        if port in ["139", "445"]:
            return "SMB exposed. Ensure latest patches and restrict access."
        return "Review service configuration for security best practices."

def create_final_json(target, target_dir):
    """
    Entry point function to be called by other parts of the VAJRA engine.
    """
    generator = FinalJsonGenerator(target, target_dir)
    return generator.generate()
