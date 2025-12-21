# VAJRA/Engine/finaljson.py
# Description: Parses raw tool outputs and assembles them into a structured final.json file.

import os
import json
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse  # added to parse host from URL

class FinalJsonGenerator:
    """
    Parses various log files from a VAJRA scan and creates a consolidated JSON output.
    """
    def __init__(self, target, target_dir):
        self.target = target
        self.target_dir = target_dir
        self.log_dir = os.path.join(self.target_dir, "Logs")
        self.json_dir = os.path.join(self.target_dir, "JSON")
        self.final_data = {
            "scan_info": {
                "target": self.target,
                "scan_date": "N/A", # This will be updated upon generation
                "risk_level": "N/A" # Placeholder for future logic
            }
        }

    def parse_whois(self):
        """Parses the whois.txt log file."""
        whois_file = os.path.join(self.log_dir, "whois.txt")
        if not os.path.exists(whois_file):
            return None

        info("Parsing Whois data...")
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
                'registrant_phone': self._search(r"Registrant Phone:\s*(.*)", content),
                'registrar_abuse_email': self._search(r"Registrar Abuse Contact Email:\s*(.*)", content),
                'registrar_abuse_phone': self._search(r"Registrar Abuse Contact Phone:\s*(.*)", content),
            }
            return data
        except Exception as e:
            error(f"Could not parse whois.txt: {e}")
            return None

    def parse_subdomains(self):
        """Parses alive.txt for a list of live subdomains."""
        subdomain_file = os.path.join(self.log_dir, "alive.txt")
        if not os.path.exists(subdomain_file):
            return None
        
        info("Parsing live subdomain data...")
        try:
            with open(subdomain_file, 'r') as f:
                subdomains = [line.strip() for line in f if line.strip()]
            
            summary = {
                "total_alive": len(subdomains),
                "subdomains": subdomains or ["N/A"]
            }
            return summary
        except Exception as e:
            error(f"Could not parse alive.txt: {e}")
            return None

    def parse_services(self):
        """Parses alive.json for web service details.

        Modified to extract only: url, host, port, webserver.
        """
        services_file = os.path.join(self.log_dir, "alive.json")
        if not os.path.exists(services_file):
            return None

        info("Parsing HTTPX service data...")
        services_data = []
        try:
            with open(services_file, 'r') as f:
                for line in f:
                    try:
                        service = json.loads(line)

                        # Raw values
                        url = service.get('url', 'N/A')
                        port = service.get('port', 'N/A')

                        # Host: prefer explicit 'host' key, otherwise parse from URL
                        host = service.get('host')
                        if not host or host == "":
                            try:
                                parsed = urlparse(url)
                                host = parsed.hostname if parsed and parsed.hostname else "N/A"
                            except Exception:
                                host = "N/A"

                        # Webserver: prefer well-known keys, otherwise try to infer from 'tech' list
                        webserver = service.get('server') or service.get('webserver') or None
                        if not webserver:
                            tech_list = service.get('tech', []) or []
                            # Common server names to look for in tech list
                            common_servers = ["nginx", "apache", "iis", "caddy", "gunicorn", "uvicorn", "tomcat", "jetty"]
                            inferred = next((t for t in tech_list if any(s in t.lower() for s in common_servers)), None)
                            webserver = inferred if inferred else "N/A"

                        services_data.append({
                            "url": url,
                            "host": host,
                            "port": port,
                            "webserver": webserver
                        })
                    except json.JSONDecodeError:
                        # Skip malformed lines
                        continue
            return services_data if services_data else None
        except Exception as e:
            error(f"Could not parse alive.json: {e}")
            return None

    def parse_nmap(self):
        """Parses an Nmap XML file (e.g., nmap_top1000.xml)."""
        nmap_file = self._find_nmap_xml()
        if not nmap_file:
            return None

        info(f"Parsing Nmap data from {os.path.basename(nmap_file)}...")
        try:
            tree = ET.parse(nmap_file)
            root = tree.getroot()
            
            nmap_data = {
                "scan_summary": {
                    "scan_type": root.find('scaninfo').get('type').upper() if root.find('scaninfo') is not None else "N/A",
                    "duration": root.find('runstats/finished').get('timestr') if root.find('runstats/finished') is not None else "N/A",
                    "total_open_ports": 0 # Will be calculated
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
                        if port.find('state').get('state') == 'open':
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
        except ET.ParseError as e:
            error(f"Could not parse Nmap XML file: {e}")
            return None

    def generate(self):
        """
        Orchestrates the parsing of all log files and writes the final JSON.
        """
        info("Assembling final JSON report...")
        
        whois_data = self.parse_whois()
        if whois_data:
            self.final_data['whois'] = whois_data

        subdomain_data = self.parse_subdomains()
        if subdomain_data:
            self.final_data['subdomains'] = subdomain_data

        service_data = self.parse_services()
        if service_data:
            self.final_data['services'] = service_data

        nmap_data = self.parse_nmap()
        if nmap_data:
            self.final_data['nmap'] = nmap_data
        
        # Update scan date
        from datetime import datetime
        self.final_data["scan_info"]["scan_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save the final JSON file
        try:
            os.makedirs(self.json_dir, exist_ok=True)
            output_path = os.path.join(self.json_dir, "final.json")
            with open(output_path, 'w') as f:
                json.dump(self.final_data, f, indent=4)
            info(f"Final JSON report saved to: {output_path}")
            return True
        except Exception as e:
            error(f"Failed to write final.json: {e}")
            return False

    # --- Helper Methods ---
    
    def _search(self, pattern, text, default="N/A"):
        """Utility to search for a regex pattern and return the first group or a default."""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # For patterns with multiple capture groups (like expiration date)
            return next((g for g in match.groups() if g is not None), default).strip()
        return default

    def _find_nmap_xml(self):
        """Finds the first Nmap XML file in the logs directory."""
        for filename in os.listdir(self.log_dir):
            if filename.startswith("nmap_") and filename.endswith(".xml"):
                return os.path.join(self.log_dir, filename)
        return None
        
    def _get_hostname(self, host_element):
        """Extracts the most likely hostname from an Nmap host element."""
        hostname_elem = host_element.find("hostnames/hostname")
        if hostname_elem is not None and hostname_elem.get('name'):
            return hostname_elem.get('name')
        # Fallback to the main target if no specific hostname is found
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
        return "Review service configuration for security best practices."

def create_final_json(target, target_dir):
    """
    Entry point function to be called by other parts of the VAJRA engine.
    """
    generator = FinalJsonGenerator(target, target_dir)
    return generator.generate()
