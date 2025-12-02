#!/bin/bash

# WhatsApp Bot Quick Start Script
# This script helps you start the server and ngrok for WhatsApp bot testing

echo "🚀 Starting Google Ads Research WhatsApp Bot..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.example to .env and add your credentials:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ Error: ngrok is not installed!"
    echo ""
    echo "Install ngrok:"
    echo "  macOS: brew install ngrok"
    echo "  Or download from: https://ngrok.com/download"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Virtual environment not activated"
    echo "Activating venv..."
    source venv/bin/activate
fi

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  NEXT STEPS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  Keep this terminal open and run:"
echo "    python main.py"
echo ""
echo "2️⃣  Open a NEW terminal and run:"
echo "    ngrok http 3002"
echo ""
echo "3️⃣  Copy the ngrok HTTPS URL (e.g., https://abc123.ngrok-free.app)"
echo ""
echo "4️⃣  Go to Meta Developer Console and set webhook URL to:"
echo "    https://YOUR-NGROK-URL/webhook"
echo ""
echo "5️⃣  Send 'help' to your WhatsApp Business number to test!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📖 Full setup guide: WHATSAPP_SETUP.md"
echo ""

# Ask if user wants to start the server now
read -p "Start the server now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Starting server on http://0.0.0.0:3002..."
    echo "📝 Press Ctrl+C to stop"
    echo ""
    python main.py
fi
