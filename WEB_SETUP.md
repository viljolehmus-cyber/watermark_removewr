# Watermark Remover - Web Version Setup Guide

The easiest way to remove watermarks from your videos using a web browser!

## Features

✨ **No Command Line Needed** - Just open your browser  
📤 **Drag & Drop Upload** - Simply drag your video onto the page  
🎯 **Visual Selection** - Click and drag to select watermarks  
⚙️ **Easy Configuration** - Simple sliders and dropdowns  
💾 **One-Click Download** - Get your cleaned video instantly  
🌐 **Works Everywhere** - Chrome, Firefox, Safari, Edge  

## Prerequisites

Before you start, make sure you have:

- **Python 3.10 or higher** - [Download here](https://www.python.org/downloads/)
- **ffmpeg** (optional, but recommended for audio)
  - Linux: `sudo apt-get install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: [Download here](https://ffmpeg.org/download.html)

## Installation

### Step 1: Clone or Download the Repository

```bash
git clone https://github.com/viljolehmus-cyber/watermark_removewr.git
cd watermark_removewr
```

Or [download the ZIP](https://github.com/viljolehmus-cyber/watermark_removewr/archive/refs/heads/main.zip) and extract it.

### Step 2: Install Python Dependencies

Open a terminal/command prompt in the project directory and run:

```bash
pip install -r requirements.txt
```

**On Linux/macOS**, you might need:
```bash
pip3 install -r requirements.txt
```

**On Windows**, if you get permission errors, try:
```bash
pip install --user -r requirements.txt
```

### Step 3: Verify Installation

Check that everything is installed correctly:

```bash
python3 -c "from app import app; print('✓ All good!')"
```

You should see: `✓ All good!`

## Running the Web App

### Option 1: Using the Launch Script (Recommended)

**On Linux/macOS:**
```bash
chmod +x run_web.sh
./run_web.sh
```

**On Windows:**
```bash
run_web.bat
```

### Option 2: Manual Start

```bash
python3 app.py
```

Or on Windows:
```bash
python app.py
```

### Step 4: Open in Browser

Once the script starts, you'll see:
```
 * Running on http://127.0.0.1:5000
```

Open your browser and go to: **http://localhost:5000**

## How to Use

### Step 1: Upload Video
- Click the upload area or drag and drop your video
- Supported formats: MP4, MOV, AVI, MKV, WebM, FLV, M4V
- Maximum file size: 2GB

### Step 2: Select Watermark
- The first frame of your video will appear
- Click and drag to draw a rectangle around the watermark
- You can select multiple watermarks by drawing multiple rectangles
- Green rectangles show your selections
- Click "Undo Last" to remove the last selection

### Step 3: Configure Settings
- **Protect Bottom Area (%)**: How much of the bottom to protect from removal
  - Set higher values to protect subtitles
  - Default: 25%
- **Inpainting Method**: How to fill the watermark area
  - TELEA: Faster, good quality
  - Navier-Stokes: Slower, potentially better quality

### Step 4: Process
- The tool will process your video
- Processing time depends on video length and resolution
- You'll see a progress indicator
- This typically takes a few minutes for 1-2 minute videos

### Step 5: Download
- Once complete, click "Download Video" to save your cleaned video
- The file will be saved as `cleaned_[timestamp].mp4`

## Troubleshooting

### "Flask is not installed"
```bash
pip install Flask
```

### "No module named 'cv2'"
```bash
pip install opencv-contrib-python
```

### "Module 'ffmpeg' not found"
This is optional. Audio won't be merged but video will still be processed:
```bash
pip install ffmpeg-python
```

### Port 5000 already in use
The app will try the next available port. Check the terminal output for the correct URL.

### Upload fails
- Check file size (max 2GB)
- Verify it's a valid video file
- Try a different browser
- Check your internet connection

### Processing never completes
- Try a shorter video
- Check available disk space
- Restart the web server
- Try processing again

### Downloaded video has no audio
Make sure ffmpeg is installed and working:
```bash
ffmpeg -version
```

## Advanced Configuration

### Running on a Different Port
Edit `app.py` at the bottom:
```python
app.run(debug=True, host='0.0.0.0', port=8080)  # Change 5000 to 8080
```

### Allowing Remote Access
In `app.py`, change `localhost` to `0.0.0.0`:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

Then access from another computer using your IP:
```
http://YOUR_IP:5000
```

### Changing Upload Limits
In `app.py`, modify the MAX_CONTENT_LENGTH:
```python
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 * 1024  # 5GB
```

## Tips for Best Results

1. **Clear Watermarks**: Works best with visible, non-blended watermarks
2. **Steady Content**: Stationary backgrounds help the tracker follow the watermark
3. **Good First Frame**: Make sure the watermark is visible in the first frame
4. **Protect Subtitles**: Always enable bottom protection if you have subtitles

## Performance Notes

- **Resolution Impact**: Larger videos take longer to process
  - 720p: ~1-2 minutes per minute of video
  - 1080p: ~2-5 minutes per minute of video
  - 4K: ~10-20 minutes per minute of video

- **Memory Usage**: ~500MB - 2GB depending on video size

- **Disk Space**: Need free space at least 2x the video size

## File Locations

- **Uploaded videos**: Temporary folder (auto-cleaned)
- **Processed videos**: Temporary folder (auto-cleaned)
- **Browser cache**: Normally in your Downloads folder

## Security Notes

- This tool runs locally on your computer
- No videos are uploaded to external servers
- All processing happens on your machine
- Temporary files are automatically cleaned up

## Advanced: Using Docker

For easier deployment, you can run this in Docker:

```bash
docker build -t watermark-remover .
docker run -p 5000:5000 watermark-remover
```

(Requires `Dockerfile` in the repository)

## Getting Help

If you encounter issues:

1. Check the browser console for errors (F12 → Console tab)
2. Check the terminal for error messages
3. Try restarting the web server
4. Make sure all dependencies are installed
5. Verify ffmpeg is installed: `ffmpeg -version`

## Performance Optimization

For faster processing on slower computers:

1. Use smaller videos
2. Choose TELEA method (faster)
3. Use lower resolution videos
4. Close other applications

## Limitations

- Works best with static or slowly moving watermarks
- May struggle with semi-transparent watermarks
- Cannot protect and remove watermarks in the same area
- Audio will be re-encoded (may affect quality slightly)

## Feedback

Found a bug or have a suggestion? Please let us know!

---

Enjoy removing watermarks! 🎬✨
