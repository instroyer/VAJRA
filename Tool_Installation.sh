#!/bin/bash

# ============================================================================
# VAJRA-OSP Tool Installation Script
# Automated installation of security tools
# ============================================================================

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
ORANGE='\033[38;5;208m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Symbols
CHECK="${GREEN}✓${NC}"
CROSS="${RED}✗${NC}"
ARROW="${CYAN}➜${NC}"
WARN="${YELLOW}⚠${NC}"
INFO="${BLUE}ℹ${NC}"

# Counters
INSTALLED_COUNT=0
MISSING_COUNT=0
TOTAL_TOOLS=18

# ============================================================================
# Functions
# ============================================================================

print_banner() {
    clear
    echo -e "${ORANGE}"
    cat << "EOF"
    ██╗   ██╗ █████╗      ██╗██████╗  █████╗ 
    ██║   ██║██╔══██╗     ██║██╔══██╗██╔══██╗
    ██║   ██║███████║     ██║██████╔╝███████║
    ╚██╗ ██╔╝██╔══██║██   ██║██╔══██╗██╔══██║
     ╚████╔╝ ██║  ██║╚█████╔╝██║  ██║██║  ██║
      ╚═══╝  ╚═╝  ╚═╝ ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
EOF
    echo -e "${NC}"
    echo -e "${BOLD}${CYAN}        Offensive Security Platform${NC}"
    echo -e "${CYAN}           Tool Auto-Installer${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_info() {
    echo -e "${INFO} ${WHITE}$1${NC}"
}

print_success() {
    echo -e "${CHECK} ${GREEN}$1${NC}"
}

print_error() {
    echo -e "${CROSS} ${RED}$1${NC}"
}

print_installing() {
    echo -e "${ARROW} ${CYAN}$1${NC}"
}

# Detect OS and package manager
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            OS="debian"
            PKG_MANAGER="apt"
            PKG_UPDATE="apt update -qq"
            PKG_INSTALL="apt install -y -qq"
        elif [ -f /etc/arch-release ]; then
            OS="arch"
            PKG_MANAGER="pacman"
            PKG_UPDATE="pacman -Sy --noconfirm"
            PKG_INSTALL="pacman -S --noconfirm"
        elif [ -f /etc/fedora-release ]; then
            OS="fedora"
            PKG_MANAGER="dnf"
            PKG_UPDATE="dnf check-update -q"
            PKG_INSTALL="dnf install -y -q"
        else
            OS="linux"
            PKG_MANAGER="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PKG_MANAGER="brew"
        PKG_UPDATE="brew update"
        PKG_INSTALL="brew install"
    else
        OS="unknown"
        PKG_MANAGER="unknown"
    fi
}

# Check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check and install tool
check_install_tool() {
    local tool_name=$1
    local package_name=$2
    local command_name=${3:-$1}
    
    if command_exists "$command_name"; then
        echo -e "  ${CHECK} ${tool_name}"
        ((INSTALLED_COUNT++))
        return 0
    else
        ((MISSING_COUNT++))
        print_installing "Installing $tool_name..."
        
        case $OS in
            debian)
                sudo $PKG_INSTALL "$package_name" >/dev/null 2>&1
                ;;
            arch)
                sudo $PKG_INSTALL "$package_name" >/dev/null 2>&1
                ;;
            macos)
                $PKG_INSTALL "$package_name" >/dev/null 2>&1
                ;;
        esac
        
        if command_exists "$command_name"; then
            print_success "$tool_name installed"
            ((INSTALLED_COUNT++))
            return 0
        else
            print_error "Failed to install $tool_name"
            return 1
        fi
    fi
}

# Install all tools
install_tools() {
    echo -e "${BOLD}${PURPLE}[1/6] Information Gathering Tools${NC}"
    check_install_tool "Whois" "whois" "whois"
    
    if [ "$OS" = "debian" ]; then
        check_install_tool "Dig" "dnsutils" "dig"
    elif [ "$OS" = "arch" ]; then
        check_install_tool "Dig" "bind" "dig"
    elif [ "$OS" = "macos" ]; then
        check_install_tool "Dig" "bind" "dig"
    fi
    
    check_install_tool "DNSRecon" "dnsrecon" "dnsrecon"
    check_install_tool "WAFW00F" "wafw00f" "wafw00f"
    
    if [ "$OS" = "debian" ]; then
        check_install_tool "SearchSploit" "exploitdb" "searchsploit"
    fi
    
    echo ""
    echo -e "${BOLD}${PURPLE}[2/6] Subdomain Enumeration${NC}"
    check_install_tool "Subfinder" "subfinder" "subfinder"
    check_install_tool "Amass" "amass" "amass"
    
    echo ""
    echo -e "${BOLD}${PURPLE}[3/6] Live Host Detection & Port Scanning${NC}"
    if [ "$OS" = "debian" ]; then
        check_install_tool "HTTPX" "httpx-toolkit" "httpx"
    else
        check_install_tool "HTTPX" "httpx" "httpx"
    fi
    check_install_tool "Nmap" "nmap" "nmap"
    
    echo ""
    echo -e "${BOLD}${PURPLE}[4/6] Web Scanning Tools${NC}"
    check_install_tool "Gobuster" "gobuster" "gobuster"
    check_install_tool "FFUF" "ffuf" "ffuf"
    
    if [ "$OS" = "debian" ]; then
        check_install_tool "EyeWitness" "eyewitness" "eyewitness"
    fi
    
    echo ""
    echo -e "${BOLD}${PURPLE}[5/6] Vulnerability Assessment${NC}"
    check_install_tool "Nuclei" "nuclei" "nuclei"
    check_install_tool "Nikto" "nikto" "nikto"
    
    echo ""
    echo -e "${BOLD}${PURPLE}[6/6] Password Cracking & Payload Tools${NC}"
    check_install_tool "Hashcat" "hashcat" "hashcat"
    check_install_tool "John the Ripper" "john" "john"
    check_install_tool "Hydra" "hydra" "hydra"
    
    if [ "$OS" = "debian" ]; then
        check_install_tool "MSFVenom" "metasploit-framework" "msfvenom"
    fi
    
    echo ""
}

# Print summary
print_summary() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${WHITE}Installation Complete!${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  ${GREEN}●${NC} Installed Tools: ${BOLD}${GREEN}${INSTALLED_COUNT}/${TOTAL_TOOLS}${NC}"
    
    if [ $INSTALLED_COUNT -eq $TOTAL_TOOLS ]; then
        echo ""
        print_success "All tools ready! VAJRA is good to go."
        echo ""
        echo -e "${BOLD}${ORANGE}→${NC} ${CYAN}Start VAJRA:${NC} ${WHITE}python main.py${NC}"
    else
        local missing=$((TOTAL_TOOLS - INSTALLED_COUNT))
        echo -e "  ${RED}●${NC} Missing Tools: ${BOLD}${RED}${missing}${NC}"
        echo ""
        echo -e "${WARN} ${YELLOW}Some tools failed to install. You may need to install them manually.${NC}"
    fi
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Install Go tools if needed
install_go_tools() {
    if ! command_exists subfinder || ! command_exists httpx || ! command_exists nuclei; then
        if ! command_exists go; then
            print_installing "Installing Go programming language..."
            case $OS in
                debian)
                    sudo apt install -y -qq golang-go >/dev/null 2>&1
                    ;;
                arch)
                    sudo pacman -S --noconfirm go >/dev/null 2>&1
                    ;;
                macos)
                    brew install go >/dev/null 2>&1
                    ;;
            esac
        fi
        
        if command_exists go; then
            GOPATH=$(go env GOPATH)
            echo -e "  ${INFO} Go tools will be installed to: ${WHITE}${GOPATH}/bin${NC}"
            
            if ! command_exists subfinder; then
                print_installing "Installing Subfinder via Go..."
                go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest >/dev/null 2>&1
                print_success "Subfinder installed via Go"
            fi
            
            if ! command_exists httpx; then
                print_installing "Installing HTTPX via Go..."
                go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest >/dev/null 2>&1
                print_success "HTTPX installed via Go"
            fi
            
            if ! command_exists nuclei; then
                print_installing "Installing Nuclei via Go..."
                go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest >/dev/null 2>&1
                print_success "Nuclei installed via Go"
            fi
            
            # Check if GOPATH/bin is in PATH
            if [[ ":$PATH:" != *":$GOPATH/bin:"* ]]; then
                echo ""
                echo -e "  ${WARN} ${YELLOW}Add Go tools to PATH:${NC} ${WHITE}export PATH=\$PATH:$GOPATH/bin${NC}"
                echo -e "  ${INFO} Add this to your ${WHITE}~/.bashrc${NC} or ${WHITE}~/.zshrc${NC}"
            fi
        fi
    fi
}

# ============================================================================
# Main Script
# ============================================================================

main() {
    # Print banner
    print_banner
    
    # Detect OS
    detect_os
    print_info "Detected: ${BOLD}$OS${NC} (${PKG_MANAGER})"
    echo ""
    
    if [ "$PKG_MANAGER" = "unknown" ]; then
        print_error "Unsupported operating system"
        exit 1
    fi
    
    # Check root for Linux
    if [ "$OS" != "macos" ] && [ "$EUID" -ne 0 ]; then
        print_error "Please run with sudo: ${BOLD}sudo ./Tool_Installation.sh${NC}"
        exit 1
    fi
    
    # Update package manager
    print_installing "Updating package manager..."
    case $OS in
        debian)
            sudo apt update -qq >/dev/null 2>&1
            ;;
        arch)
            sudo pacman -Sy --noconfirm >/dev/null 2>&1
            ;;
        macos)
            brew update >/dev/null 2>&1
            ;;
    esac
    print_success "Package manager updated"
    
    # Info about installation locations
    case $OS in
        debian|arch)
            echo -e "  ${INFO} Tools will be installed to: ${WHITE}/usr/bin${NC} and ${WHITE}/usr/local/bin${NC}"
            ;;
        macos)
            echo -e "  ${INFO} Tools will be installed to: ${WHITE}/usr/local/bin${NC}"
            ;;
    esac
    echo ""
    
    # Install tools
    install_tools
    
    # Install Go tools if needed
    install_go_tools
    
    # Print summary
    print_summary
}

# Run main function
main "$@"
