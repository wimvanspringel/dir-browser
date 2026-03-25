#!/bin/bash

# Directory Browser Server Startup Script

echo "🚀 Starting Directory Browser Server..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Start the server
echo "🌐 Starting server on http://localhost:5000"
echo "📁 Root directory: configured via config.ini [Media] media_dir (default /mnt/nasdata)"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 directory_server.py 