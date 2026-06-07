#!/bin/bash
echo "=========================================="
echo "  MedAI - Clinical Intelligence Platform"
echo "=========================================="

echo "[1/4] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "[2/4] Installing dependencies..."
pip install -r requirements.txt

echo "[3/4] Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "** IMPORTANT: Edit .env and add your ANTHROPIC_API_KEY **"
    echo "Open .env in your editor and replace the placeholder with your key."
    echo ""
fi

echo "[4/4] Starting MedAI on http://localhost:5000"
python run.py
