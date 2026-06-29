# Quick Start Guide - Watermark Remover

Two ways to remove watermarks: **Browser** (easiest) or **Command Line** (most control)

## 🌐 WEB VERSION (Recommended for Most Users)

### Install & Run (3 steps)

**Step 1: Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 2: Start the web server**

Linux/macOS:
```bash
./run_web.sh
```

Windows:
```bash
run_web.bat
```

Or manually:
```bash
python app.py
```

**Step 3: Open browser**
```
http://localhost:5000
```

### How to Use
1. 📤 **Upload** - Drag your video onto the page
2. 🎯 **Select** - Draw rectangles around watermarks
3. ⚙️ **Configure** - Set protection zones and options
4. ▶️ **Process** - Click process and wait
5. 💾 **Download** - Save your cleaned video

✨ **That's it!** No command line needed.

📖 Full guide: See [WEB_SETUP.md](WEB_SETUP.md)

---

## 💻 COMMAND LINE VERSION

### Install & Run

**Step 1: Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 2: Run the tool**
```bash
python remove_watermark.py input.mp4 output.mp4
```

### Basic Usage Examples

**Simple removal (use defaults)**
```bash
python remove_watermark.py video.mp4 cleaned.mp4
```

**Protect bottom 30% (for subtitles)**
```bash
python remove_watermark.py video.mp4 cleaned.mp4 --protect-bottom 30
```

**Remove multiple watermarks**
```bash
python remove_watermark.py video.mp4 cleaned.mp4 --multi
```

**Better quality (slower)**
```bash
python remove_watermark.py video.mp4 cleaned.mp4 --method ns
```

**See all options**
```bash
python remove_watermark.py --help
```

📖 Full guide: See [README.md](README.md)

---

## Comparison

| Feature | Web | CLI |
|---------|-----|-----|
| Ease of Use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| No Terminal Needed | ✓ | ✗ |
| Visual Interface | ✓ | ✗ |
| Automation Scripts | ✗ | ✓ |
| Batch Processing | ✗ | ✓ |
| Advanced Options | Partial | Full |

---

## System Requirements

- Python 3.10+
- ffmpeg (optional but recommended for audio)

### Install ffmpeg

**Linux:**
```bash
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html

---

## Troubleshooting

### Issue: Module not found
```bash
pip install -r requirements.txt
```

### Issue: Port 5000 already in use
Change the port in `app.py` line at the bottom:
```python
app.run(debug=True, host='0.0.0.0', port=8080)
```

### Issue: Slow processing
- Use shorter videos
- Use TELEA method (faster)
- Reduce video resolution first

### Issue: No audio in output
Install ffmpeg - it's optional but needed for audio

---

## File Structure

```
watermark_removewr/
├── app.py                    # Web server
├── remove_watermark.py       # CLI tool
├── requirements.txt          # Python packages
├── templates/
│   └── index.html           # Web interface
├── static/
│   ├── css/style.css        # Styling
│   └── js/script.js         # Frontend logic
├── run_web.sh               # Launch script (Linux/macOS)
├── run_web.bat              # Launch script (Windows)
├── README.md                # Full documentation
├── WEB_SETUP.md            # Web version guide
└── QUICKSTART.md           # This file
```

---

## Features

### Core Features
- ✅ CSRT tracking (most accurate)
- ✅ TELEA & Navier-Stokes inpainting
- ✅ Multiple watermark support
- ✅ Subtitle protection zones
- ✅ Audio preservation
- ✅ MP4, MOV, AVI, MKV support
- ✅ Real-time progress tracking

### Web-Only Features
- ✅ Drag & drop upload
- ✅ Visual watermark selection
- ✅ Live preview

### CLI-Only Features
- ✅ Batch processing
- ✅ Preview mode
- ✅ Debug frames
- ✅ Template matching fallback

---

## Common Scenarios

### Scenario 1: Channel Logo in Corner
```bash
# Web: Upload, draw box around logo, process
# CLI:
python remove_watermark.py video.mp4 cleaned.mp4 --protect-bottom 20
```

### Scenario 2: Multiple Watermarks
```bash
# Web: Upload, draw multiple boxes, process
# CLI:
python remove_watermark.py video.mp4 cleaned.mp4 --multi
```

### Scenario 3: Video with Subtitles
```bash
# Web: Upload, draw watermark, set protect-bottom to 30, process
# CLI:
python remove_watermark.py video.mp4 cleaned.mp4 --protect-bottom 30
```

### Scenario 4: High Quality (Slower)
```bash
# Web: Upload, draw box, select "Navier-Stokes" method, process
# CLI:
python remove_watermark.py video.mp4 cleaned.mp4 --method ns
```

---

## Performance Notes

**Processing Speed by Resolution:**
- 720p: ~1-2 min per minute of video
- 1080p: ~2-5 min per minute of video
- 4K: ~10-20 min per minute of video

**Memory Usage:** ~500MB - 2GB

**Disk Space Needed:** 2x your video size

---

## Tips for Best Results

1. **Visible First Frame** - Watermark should be clearly visible in frame 1
2. **Steady Background** - Stationary backgrounds work best
3. **Accurate Selection** - Be precise when drawing the watermark box
4. **Protect Subtitles** - Always enable bottom protection if needed
5. **Choose Method** - TELEA is faster, NS is better quality

---

## Getting Started Now

### I want the easiest way:
```bash
./run_web.sh
# Then open http://localhost:5000
```

### I want command line control:
```bash
python remove_watermark.py input.mp4 output.mp4
```

### I want to see all options:
```bash
python remove_watermark.py --help
```

---

## Next Steps

- **Web Users**: Open [WEB_SETUP.md](WEB_SETUP.md) for detailed help
- **CLI Users**: Open [README.md](README.md) for all options
- **Developers**: Check the code structure and modify as needed

---

Happy watermark removing! 🎬✨
