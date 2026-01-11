#!/bin/bash

# =============================================================================
# VAJRA - Linux Build Script (PyInstaller)
# Creates a single-file executable using PyInstaller
# Version: 2.0.0 - Updated 2026-01-11
# =============================================================================

set -e

# Get directories
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/venv"

# Define Venv Binaries
PYTHON_BIN="$VENV_DIR/bin/python3"
PIP_BIN="$VENV_DIR/bin/pip"
PYINSTALLER_BIN="$VENV_DIR/bin/pyinstaller"

echo "🔨 Starting Vajra Build Process (PyInstaller)..."
echo "   Version: 2.0.0"
cd "$PROJECT_ROOT"

# 1. Setup Virtual Environment
echo "📦 Setting up environment..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 could not be found."
    exit 1
fi

# Check if venv exists and is valid for this project
NEED_NEW_VENV=false
if [ ! -d "$VENV_DIR" ]; then
    NEED_NEW_VENV=true
elif [ -f "$VENV_DIR/pyvenv.cfg" ]; then
    if ! grep -q "$PROJECT_ROOT" "$VENV_DIR/pyvenv.cfg" 2>/dev/null; then
        echo "   ⚠️  Venv was created for a different project, recreating..."
        rm -rf "$VENV_DIR"
        NEED_NEW_VENV=true
    fi
fi

if [ "$NEED_NEW_VENV" = true ]; then
    echo "   Creating venv..."
    python3 -m venv "$VENV_DIR" || {
        echo "❌ Error creating virtual environment."
        echo "   Try running: sudo apt install python3-venv"
        exit 1
    }
fi

# 2. Install Dependencies
echo "⬇️  Installing dependencies..."
"$PIP_BIN" install --upgrade pip
"$PIP_BIN" install PySide6>=6.7.0
"$PIP_BIN" install pyinstaller

# Verify pyinstaller is installed
if ! "$PYTHON_BIN" -c "import PyInstaller" 2>/dev/null; then
    echo "   📦 Reinstalling PyInstaller..."
    "$PIP_BIN" install --force-reinstall pyinstaller
fi

# 3. Clean previous builds
echo "🧹 Cleaning up old builds..."
rm -rf build dist vajra.spec

# 4. Run PyInstaller
echo "🚀 Building executable..."
if [ -f "$PYINSTALLER_BIN" ]; then
    BUILD_CMD="$PYINSTALLER_BIN"
else
    BUILD_CMD="$PYTHON_BIN -m PyInstaller"
fi

$BUILD_CMD --noconfirm --onefile --windowed --clean \
    --name "vajra" \
    --additional-hooks-dir="$SCRIPT_DIR" \
    --hidden-import "PySide6" \
    --collect-all "PySide6" \
    --collect-submodules "modules" \
    --collect-submodules "core" \
    --exclude-module "*.md" \
    --exclude-module "*.txt" \
    --hidden-import "modules" \
    --hidden-import "modules.amass" \
    --hidden-import "modules.automation" \
    --hidden-import "modules.bases" \
    --hidden-import "modules.dencoder" \
    --hidden-import "modules.dig" \
    --hidden-import "modules.dnsrecon" \
    --hidden-import "modules.eyewitness" \
    --hidden-import "modules.ffuf" \
    --hidden-import "modules.gobuster" \
    --hidden-import "modules.hashcat" \
    --hidden-import "modules.hashcat_data" \
    --hidden-import "modules.hashfinder" \
    --hidden-import "modules.httpx" \
    --hidden-import "modules.hydra" \
    --hidden-import "modules.john" \
    --hidden-import "modules.msfvenom" \
    --hidden-import "modules.nikto" \
    --hidden-import "modules.nmap" \
    --hidden-import "modules.nuclei" \
    --hidden-import "modules.portscanner" \
    --hidden-import "modules.searchsploit" \
    --hidden-import "modules.shellforge" \
    --hidden-import "modules.strings" \
    --hidden-import "modules.subfinder" \
    --hidden-import "modules.wafw00f" \
    --hidden-import "modules.whois" \
    --hidden-import "core" \
    --hidden-import "core.config" \
    --hidden-import "core.fileops" \
    --hidden-import "core.jsonparser" \
    --hidden-import "core.privileges" \
    --hidden-import "core.reportgen" \
    --hidden-import "core.tgtinput" \
    main.py

# 5. Clean up build artifacts
echo "🧹 Cleaning up build artifacts..."
rm -rf build vajra.spec

# 6. Finalize
echo ""
echo "✅ Build Complete!"
echo "   Executable: dist/vajra"
echo "   Version: 2.0.0"
echo ""
echo "To run it:"
echo "   ./dist/vajra"
