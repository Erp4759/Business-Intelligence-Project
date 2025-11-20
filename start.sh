#!/bin/bash
# Quick start script for VAESTA

echo "🚀 Starting VAESTA - Your Fashion Companion"
echo ""

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python -m venv .venv"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if dependencies are installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Using mock weather data."
    echo "💡 To use real weather data:"
    echo "   1. Get free API key from https://openweathermap.org/api"
    echo "   2. Copy .env.example to .env"
    echo "   3. Add your API key to .env"
    echo ""
fi

# Run the app
echo "🎨 Launching VAESTA..."
echo "🌐 Open http://localhost:8501 in your browser"
echo ""
streamlit run app.py
