#!/bin/bash

# =============================================================================
# VAJRA - Nuitka Build Script
# Compiles Python to native C++ for better protection and performance
# =============================================================================

set -e

# Get directories
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/venv"

# Define Venv Binaries
PYTHON_BIN="$VENV_DIR/bin/python3"
PIP_BIN="$VENV_DIR/bin/pip"

echo "🔨 Starting Vajra Build Process (Nuitka)..."
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
"$PIP_BIN" install nuitka ordered-set

# 3. Check for required tools
echo "🔍 Checking for required tools..."
MISSING_DEPS=""

if ! command -v gcc &> /dev/null; then
    MISSING_DEPS="$MISSING_DEPS build-essential"
fi

if ! command -v patchelf &> /dev/null; then
    MISSING_DEPS="$MISSING_DEPS patchelf"
fi

if [ ! -z "$MISSING_DEPS" ]; then
    echo "⚠️  Installing missing dependencies:$MISSING_DEPS"
    sudo apt-get update && sudo apt-get install -y $MISSING_DEPS
fi

# 4. Clean previous builds
echo "🧹 Cleaning up old builds..."
rm -rf main.dist main.build main.onefile-build dist

# 5. Run Nuitka
echo "🚀 Compiling with Nuitka (this will take several minutes)..."
"$PYTHON_BIN" -m nuitka \
    --standalone \
    --onefile \
    --enable-plugin=pyside6 \
    --include-package=modules \
    --include-package=core \
    --include-package=ui \
    --output-dir=dist \
    --output-filename=vajra \
    --assume-yes-for-downloads \
    --remove-output \
    main.py

# 6. Clean up build artifacts
echo "🧹 Cleaning up build artifacts..."
rm -rf main.build main.onefile-build

# 7. Finalize
echo ""
echo "✅ Build Complete!"
echo "   Executable: dist/vajra"
echo ""
echo "To run it:"
echo "   ./dist/vajra"
echo ""
echo "🛡️  This binary is compiled to native C++ and is much harder to reverse-engineer."
