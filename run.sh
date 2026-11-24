#!/bin/bash
set -e

# Change directory to project root
cd "$(dirname "$0")"

# Enforce strict offline operation
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTHONPATH=.

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment .venv not found. Run ./setup.sh first."
    exit 1
fi

echo "================================================================="
echo "       OFFLINE MULTILINGUAL TRANSLATOR - STARTING SERVER         "
echo "================================================================="
echo "Supported Languages: Kannada, Hindi, Tamil, Telugu, Malayalam, English, Spanish"
echo "Engine: CTranslate2 INT8 on CPU (Zero network access required)"
echo ""
echo "🚀 Local Web App:     http://localhost:8000"
echo "🧪 Gradio Interface:  http://localhost:8000/gradio"
echo "📱 Mobile on LAN:     http://translator.local:8000"
echo "================================================================="
echo "Press Ctrl+C to stop the server."
echo ""

exec .venv/bin/python app/server.py
