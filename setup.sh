#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "=== Setting up Offline Multilingual Language Translator ==="

# 1. Virtual Environment Setup
if [ ! -d ".venv" ]; then
    echo "Creating Python 3.12 virtual environment..."
    python3.12 -m venv .venv || python3 -m venv .venv
fi

# 2. Dependency Installation
echo "Installing dependencies..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt -r requirements-setup.txt

# 3. Auxiliary Assets
echo "Downloading auxiliary assets (FastText model & Noto fonts)..."
.venv/bin/python setup/download_assets.py

# 4. Model Conversion
echo "Downloading NLLB-200 and converting to CTranslate2 INT8..."
.venv/bin/python setup/convert_model.py

echo ""
echo "=== Setup Complete! ==="
echo "You can now run: ./run.sh"
