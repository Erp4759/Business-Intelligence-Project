#!/bin/bash

# VAESTA Startup Script
# Quick start script for running the application

echo "🚀 Starting VAESTA - Fashion Recommendation System"
echo "=================================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source .venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found!"
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your API keys:"
    echo "   - OPENWEATHER_API_KEY (required for live weather)"
    echo "   - GEMINI_API_KEY (optional for AI wardrobe)"
    echo ""
    echo "   Get keys from:"
    echo "   🌤️  OpenWeather: https://openweathermap.org/api"
    echo "   🤖 Gemini: https://makersuite.google.com/app/apikey"
    echo ""
    read -p "Press Enter after adding your API keys..."
fi

echo ""
echo "🎨 Launching VAESTA..."
echo "📍 Application will open at: http://localhost:8501"
echo ""

# Run Streamlit
streamlit run app.py
