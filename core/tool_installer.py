"""
VAJRA Tool Installer
Automated installation of security tools (Python version)
Qt-free module for core functionality - Smart dynamic installer
"""

import subprocess
import platform
import shutil
import os
from typing import List, Tuple, Dict, Optional
from enum import Enum


class InstallMethod(Enum):
    """Installation method for a tool."""
    PACKAGE_MANAGER = "pkg"
    GO_INSTALL = "go"
    MANUAL = "manual"


class ToolDefinition:
    """Defines a security tool and its install methods."""
    
    def __init__(self, name: str, command: str, 
                 pkg_debian: Optional[str] = None,
                 pkg_arch: Optional[str] = None,
                 pkg_fedora: Optional[str] = None,
                 pkg_macos: Optional[str] = None,
                 go_package: Optional[str] = None,
                 install_url: Optional[str] = None):
        self.name = name
        self.command = command  # Command to check if installed
        self.pkg_debian = pkg_debian
        self.pkg_arch = pkg_arch
        self.pkg_fedora = pkg_fedora
        self.pkg_macos = pkg_macos
        self.go_package = go_package
        self.install_url = install_url
    
    def get_package_name(self, os_type: str) -> Optional[str]:
        """Get package name for specific OS."""
        mapping = {
            "debian": self.pkg_debian,
            "arch": self.pkg_arch,
            "fedora": self.pkg_fedora,
            "macos": self.pkg_macos,
        }
        return mapping.get(os_type)
    
    def get_install_method(self, os_type: str) -> InstallMethod:
        """Determine best install method for this OS."""
        # Prefer package manager if available
        if self.get_package_name(os_type):
            return InstallMethod.PACKAGE_MANAGER
        # Fallback to Go if available
        elif self.go_package:
            return InstallMethod.GO_INSTALL
        # Manual/URL-based install
        else:
            return InstallMethod.MANUAL


class ToolInstaller:
    """Manages installation of security tools across different platforms."""
    
    # Complete tool registry - dynamic and extensible
    TOOLS = [
        # Core Network Tools
        ToolDefinition("Whois", "whois",
                      pkg_debian="whois", pkg_arch="whois", 
                      pkg_fedora="whois", pkg_macos="whois"),
        
        ToolDefinition("Dig", "dig",
                      pkg_debian="dnsutils", pkg_arch="bind", 
                      pkg_fedora="bind-utils", pkg_macos="bind"),
        
        ToolDefinition("Nmap", "nmap",
                      pkg_debian="nmap", pkg_arch="nmap",
                      pkg_fedora="nmap", pkg_macos="nmap"),
        
        # DNS/Subdomain Tools
        ToolDefinition("DNSRecon", "dnsrecon",
                      pkg_debian="dnsrecon", pkg_arch="dnsrecon",
                      pkg_fedora="dnsrecon", pkg_macos="dnsrecon"),
        
        ToolDefinition("Subfinder", "subfinder",
                      pkg_debian="subfinder", pkg_arch="subfinder",  # Try pkg first!
                      pkg_macos="subfinder",
                      go_package="github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"),
        
        ToolDefinition("Amass", "amass",
                      pkg_debian="amass", pkg_arch="amass",
                      pkg_macos="amass",
                      go_package="github.com/owasp-amass/amass/v4/...@master"),
        
        ToolDefinition("HTTPX", "httpx",
                      pkg_debian="httpx-toolkit", pkg_arch="httpx",
                      pkg_macos="httpx",
                      go_package="github.com/projectdiscovery/httpx/cmd/httpx@latest"),
        
        ToolDefinition("Chaos", "chaos",
                      go_package="github.com/projectdiscovery/chaos-client/cmd/chaos@latest"),
        
        # OSINT Tools
        ToolDefinition("theHarvester", "theHarvester",
                      pkg_debian="theharvester", pkg_arch="theharvester",
                      pkg_fedora="theharvester", pkg_macos="theharvester"),
        
        ToolDefinition("Sublist3r", "sublist3r",
                      pkg_debian="sublist3r", pkg_arch="sublist3r"),
        
        # Web Scanners
        ToolDefinition("Gobuster", "gobuster",
                      pkg_debian="gobuster", pkg_arch="gobuster",
                      pkg_fedora="gobuster", pkg_macos="gobuster"),
        
        ToolDefinition("FFUF", "ffuf",
                      pkg_debian="ffuf", pkg_arch="ffuf",
                      pkg_fedora="ffuf", pkg_macos="ffuf"),
        
        ToolDefinition("Nikto", "nikto",
                      pkg_debian="nikto", pkg_arch="nikto",
                      pkg_fedora="nikto", pkg_macos="nikto"),
        
        ToolDefinition("WAFW00F", "wafw00f",
                      pkg_debian="wafw00f", pkg_arch="wafw00f",
                      pkg_fedora="wafw00f", pkg_macos="wafw00f"),
        
        # Vulnerability Scanners
        ToolDefinition("Nuclei", "nuclei",
                      pkg_debian="nuclei", pkg_arch="nuclei",  # Try pkg first!
                      pkg_macos="nuclei",
                      go_package="github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"),
        
        # Screenshot Tools
        ToolDefinition("EyeWitness", "eyewitness",
                      pkg_debian="eyewitness", pkg_arch="eyewitness",
                      pkg_macos="eyewitness"),
        
        # Password Crackers
        ToolDefinition("Hashcat", "hashcat",
                      pkg_debian="hashcat", pkg_arch="hashcat",
                      pkg_fedora="hashcat", pkg_macos="hashcat"),
        
        ToolDefinition("John the Ripper", "john",
                      pkg_debian="john", pkg_arch="john",
                      pkg_fedora="john", pkg_macos="john"),
        
        ToolDefinition("Hydra", "hydra",
                      pkg_debian="hydra", pkg_arch="hydra",
                      pkg_fedora="hydra", pkg_macos="hydra"),
        
        # Exploitation Tools
        ToolDefinition("Metasploit", "msfvenom",
                      pkg_debian="metasploit-framework", pkg_arch="metasploit",
                      pkg_fedora="metasploit", pkg_macos="metasploit"),
        
        ToolDefinition("SearchSploit", "searchsploit",
                      pkg_debian="exploitdb", pkg_arch="exploitdb",
                      pkg_fedora="exploitdb", pkg_macos="exploitdb"),
    ]
    
    def __init__(self):
        self.os_type = self._detect_os()
        self.pkg_manager = self._get_package_manager()
        
    def _detect_os(self) -> str:
        """Detect operating system type."""
        system = platform.system().lower()
        if system == "linux":
            # Check distro
            if os.path.exists("/etc/debian_version") or os.path.exists("/etc/lsb-release"):
                return "debian"
            elif os.path.exists("/etc/arch-release"):
                return "arch"
            elif os.path.exists("/etc/fedora-release") or os.path.exists("/etc/redhat-release"):
                return "fedora"
            return "debian"  # Default to debian-based
        elif system == "darwin":
            return "macos"
        return "unknown"
    
    def _get_package_manager(self) -> Tuple[str, List[str], List[str]]:
        """Get package manager commands for the OS."""
        if self.os_type == "debian":
            return ("apt", ["apt", "update", "-qq"], ["apt", "install", "-y", "-qq"])
        elif self.os_type == "arch":
            return ("pacman", ["pacman", "-Sy", "--noconfirm"], ["pacman", "-S", "--noconfirm", "--needed"])
        elif self.os_type == "fedora":
            return ("dnf", ["dnf", "check-update", "-q"], ["dnf", "install", "-y", "-q"])
        elif self.os_type == "macos":
            return ("brew", ["brew", "update"], ["brew", "install"])
        return ("unknown", [], [])
    
    def check_tool_installed(self, command_name: str) -> bool:
        """Check if a tool is installed."""
        return shutil.which(command_name) is not None
    
    def get_tool_status(self) -> List[Dict]:
        """Get detailed status of all tools."""
        status = []
        
        for tool in self.TOOLS:
            is_installed = self.check_tool_installed(tool.command)
            install_method = tool.get_install_method(self.os_type)
            pkg_name = tool.get_package_name(self.os_type)
            
            status.append({
                "name": tool.name,
                "command": tool.command,
                "installed": is_installed,
                "method": install_method.value,
                "package": pkg_name or tool.go_package or "manual",
                "available": pkg_name is not None or tool.go_package is not None
            })
        
        return status
    
    def get_missing_tools(self) -> List[ToolDefinition]:
        """Get list of missing tools."""
        missing = []
        for tool in self.TOOLS:
            if not self.check_tool_installed(tool.command):
                missing.append(tool)
        return missing
    
    def install_tool(self, tool: ToolDefinition) -> Tuple[bool, str]:
        """Install a tool using the best available method."""
        install_method = tool.get_install_method(self.os_type)
        
        if install_method == InstallMethod.PACKAGE_MANAGER:
            pkg_name = tool.get_package_name(self.os_type)
            if pkg_name:
                return self._install_via_package_manager(pkg_name, tool.name)
        
        elif install_method == InstallMethod.GO_INSTALL:
            if tool.go_package:
                return self._install_via_go(tool.go_package, tool.name)
        
        return False, f"{tool.name}: No installation method available for {self.os_type}"
    
    def _install_via_package_manager(self, package_name: str, tool_name: str) -> Tuple[bool, str]:
        """Install a tool using the system package manager."""
        pkg_name, update_cmd, install_cmd = self.pkg_manager
        
        if pkg_name == "unknown":
            return False, f"{tool_name}: Unsupported operating system"
        
        try:
            # Run install command
            cmd = install_cmd + [package_name]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                return True, f"{tool_name}: Installed via {pkg_name}"
            else:
                # If package manager fails, try Go fallback if available
                return False, f"{tool_name}: Package install failed"
        
        except subprocess.TimeoutExpired:
            return False, f"{tool_name}: Installation timeout"
        except Exception as e:
            return False, f"{tool_name}: Error - {str(e)}"
    
    def _install_via_go(self, package_url: str, tool_name: str) -> Tuple[bool, str]:
        """Install a Go-based tool."""
        # Check if Go is installed
        if not self.check_tool_installed("go"):
            # Try to install Go first
            go_success, go_msg = self.install_go()
            if not go_success:
                return False, f"{tool_name}: Go not available"
        
        try:
            result = subprocess.run(
                ["go", "install", "-v", package_url],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                # Check if tool is in PATH
                gopath = subprocess.run(
                    ["go", "env", "GOPATH"],
                    capture_output=True,
                    text=True
                ).stdout.strip()
                
                gobin = os.path.join(gopath, "bin")
                return True, f"{tool_name}: Installed via Go to {gobin}"
            else:
                return False, f"{tool_name}: Go install failed"
        
        except subprocess.TimeoutExpired:
            return False, f"{tool_name}: Installation timeout"
        except Exception as e:
            return False, f"{tool_name}: Error - {str(e)}"
    
    def update_package_manager(self) -> Tuple[bool, str]:
        """Update package manager repositories."""
        pkg_name, update_cmd, _ = self.pkg_manager
        
        if pkg_name == "unknown":
            return False, "Unsupported operating system"
        
        try:
            result = subprocess.run(
                update_cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0 or result.returncode == 100:  # dnf returns 100 if no updates
                return True, "Package manager updated"
            else:
                return False, f"Update failed: {result.stderr[:100]}"
        
        except subprocess.TimeoutExpired:
            return False, "Update timeout"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def install_go(self) -> Tuple[bool, str]:
        """Install Go programming language."""
        if self.check_tool_installed("go"):
            return True, "Go is already installed"
        
        # Try package manager install
        pkg_names = {
            "debian": "golang-go",
            "arch": "go",
            "fedora": "golang",
            "macos": "go"
        }
        
        pkg_name = pkg_names.get(self.os_type, "golang")
        success, msg = self._install_via_package_manager(pkg_name, "Go")
        
        return success, msg
    
    def get_go_path_warning(self) -> str:
        """Get warning message about Go PATH if needed."""
        if not self.check_tool_installed("go"):
            return ""
        
        try:
            gopath = subprocess.run(
                ["go", "env", "GOPATH"],
                capture_output=True,
                text=True
            ).stdout.strip()
            
            gobin = os.path.join(gopath, "bin")
            
            # Check if Go bin is in PATH
            path_env = os.environ.get("PATH", "")
            if gobin not in path_env:
                return f"⚠️ Add Go tools to PATH:\nexport PATH=$PATH:{gobin}\nAdd this to ~/.bashrc or ~/.zshrc"
        
        except Exception:
            pass
        
        return ""
    
    def get_installation_stats(self) -> Dict[str, int]:
        """Get statistics about installed tools."""
        total_tools = len(self.TOOLS)
        installed = sum(1 for tool in self.TOOLS if self.check_tool_installed(tool.command))
        
        return {
            "total": total_tools,
            "installed": installed,
            "missing": total_tools - installed
        }
