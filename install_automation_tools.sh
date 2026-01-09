#!/bin/bash
# VAJRA Automation - Tool Installation Script (Updated)
# Install all required tools for bug bounty automation

echo "🚀 Installing VAJRA Automation Dependencies..."
echo ""

# Update system
echo "📦 Updating package lists..."
sudo apt update

# Install basic tools
echo ""
echo "🔧 Installing core tools..."
sudo apt install -y whois nmap git python3-pip golang-go

# Setup Go environment
echo ""
echo "🐹 Configuring Go environment..."
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin
echo 'export GOPATH=$HOME/go' >> ~/.bashrc
echo 'export PATH=$PATH:$GOPATH/bin' >> ~/.bashrc

# Install ProjectDiscovery tools
echo ""
echo "🛠️  Installing ProjectDiscovery tools..."
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/chaos-client/cmd/chaos@latest
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# Rename httpx to httpx-toolkit if needed
if [ -f "$GOPATH/bin/httpx" ]; then
    echo "🔗 Creating httpx-toolkit alias..."
    sudo ln -sf $GOPATH/bin/httpx /usr/local/bin/httpx-toolkit
fi

# Install Python tools
echo ""
echo "🐍 Installing Python tools..."
pip3 install theHarvester
pip3 install sublist3r

# Install EyeWitness
echo ""
echo "📸 Installing EyeWitness..."
cd /opt
sudo git clone https://github.com/FortyNorthSecurity/EyeWitness.git
cd EyeWitness/Python/setup
sudo ./setup.sh
sudo ln -sf /opt/EyeWitness/Python/EyeWitness.py /usr/local/bin/eyewitness

# Install Nikto
echo ""
echo "🔧 Installing Nikto..."
sudo apt install -y nikto

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Installed tools:"
echo "  ✓ whois"
echo "  ✓ nmap"
echo "  ✓ subfinder"
echo "  ✓ httpx-toolkit"
echo "  ✓ chaos"
echo "  ✓ theHarvester"
echo "  ✓ sublist3r"
echo "  ✓ eyewitness"
echo "  ✓ nuclei"
echo "  ✓ nikto"
echo ""
echo "🔍 Verifying installations..."
for tool in whois nmap subfinder httpx-toolkit theHarvester sublist3r eyewitness nuclei nikto; do
    if command -v $tool &> /dev/null; then
        echo "  ✅ $tool - $(which $tool)"
    else
        echo "  ❌ $tool - NOT FOUND"
    fi
done

echo ""
echo "🎉 Setup complete! You can now use VAJRA Automation."
echo ""
echo "⚡ Quick start:"
echo "  1. Open VAJRA application"
echo "  2. Go to Automation tool"
echo "  3. Enter target domain"
echo "  4. Select Nmap preset and options"
echo "  5. Click START AUTOMATION"
echo ""
