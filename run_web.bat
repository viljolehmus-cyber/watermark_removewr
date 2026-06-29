@echo off
REM Watermark Remover - Web Version Launcher (Windows)
REM This script starts the Flask web server for the watermark removal tool

title Watermark Remover - Web Version

echo.
echo  ╔════════════════════════════════════════════════════════╗
echo  ║       🎬 Watermark Remover - Web Version              ║
echo  ╚════════════════════════════════════════════════════════╝
echo.

REM Check if Python 3 is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python 3 is not installed or not in PATH
    pause
    exit /b 1
)

echo ✓ Python 3 found
echo.

REM Check dependencies
echo Checking dependencies...

python << 'EOF'
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

if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo Starting Flask server...
echo.
echo 🌐 Open your browser and go to: http://localhost:5000
echo 📝 Press Ctrl+C to stop the server
echo.

REM Start Flask app
python app.py
pause
