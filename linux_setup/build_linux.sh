#!/bin/bash

# =============================================================================
# VAJRA - Linux Build Script
# Creates a single-file executable using PyInstaller
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

echo "🔨 Starting Vajra Build Process..."
cd "$PROJECT_ROOT"

# 1. Setup Virtual Environment
echo "📦 Setting up environment..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 could not be found."
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
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
"$PIP_BIN" install -r requirements.txt
"$PIP_BIN" install pyinstaller

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
    --hidden-import "modules.hashfinder" \
    --hidden-import "modules.httpx" \
    --hidden-import "modules.hydra" \
    --hidden-import "modules.john" \
    --hidden-import "modules.nikto" \
    --hidden-import "modules.nmap" \
    --hidden-import "modules.nuclei" \
    --hidden-import "modules.portscanner" \
    --hidden-import "modules.strings" \
    --hidden-import "modules.subfinder" \
    --hidden-import "modules.whois" \
    --hidden-import "core" \
    --hidden-import "core.fileops" \
    --hidden-import "core.tgtinput" \
    --hidden-import "core.jsonparser" \
    main.py

# 5. Clean up build artifacts (keep only the executable)
echo "🧹 Cleaning up build artifacts..."
rm -rf build vajra.spec

# 6. Finalize
echo ""
echo "✅ Build Complete!"
echo "   Executable: dist/vajra"
echo ""
echo "To run it:"
echo "   ./dist/vajra"
