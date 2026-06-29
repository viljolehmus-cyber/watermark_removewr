#!/bin/bash

# Watermark Remover - Web Version Launcher
# This script starts the Flask web server for the watermark removal tool

set -e

echo "🎬 Watermark Remover - Web Version"
echo "=================================="
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found"
echo ""

# Check if required packages are installed
echo "Checking dependencies..."

python3 << 'EOF'
import sys

required_packages = {
    'cv2': 'opencv-contrib-python',
    'numpy': 'numpy',
    'flask': 'Flask',
    'ffmpeg': 'ffmpeg-python (optional)'
}

missing_packages = []

for package, pip_name in required_packages.items():
    try:
        if package == 'ffmpeg':
            __import__('ffmpeg')
        else:
            __import__(package)
        print(f"  ✓ {package}")
    except ImportError:
        if package == 'ffmpeg':
            print(f"  ⚠ {package} (optional, audio will not be merged)")
        else:
            print(f"  ✗ {package} - MISSING")
            missing_packages.append(pip_name)

if missing_packages:
    print("\nMissing packages! Install with:")
    print(f"  pip install {' '.join(missing_packages)}")
    sys.exit(1)

print("\n✓ All required dependencies found")
EOF

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""
echo "Starting Flask server..."
echo ""
echo "🌐 Open your browser and go to: http://localhost:5000"
echo "📝 Press Ctrl+C to stop the server"
echo ""

# Start Flask app
python3 app.py
