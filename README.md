# Watermark Remover Tool

A Python tool for removing watermarks from videos using OpenCV tracking and inpainting algorithms.

## Features

- **Interactive Selection**: Draw a rectangle around the watermark on the first frame using your mouse
- **Accurate Tracking**: Uses CSRT (Continuous Convolution Operators Trained Correlators) tracker for precise watermark tracking throughout the video
- **Smart Inpainting**: Removes watermarks using OpenCV's TELEA or Navier-Stokes inpainting methods
- **Subtitle Protection**: Protect specific regions (like subtitles) from being inpainted
- **Multiple Watermarks**: Support for removing multiple watermarks in a single video
- **Real-time Preview**: Optional side-by-side preview of original vs. cleaned frames
- **Debug Mode**: Save debug frames showing tracking boxes and protected zones
- **Audio Preservation**: Automatically merges audio from the original video
- **Format Support**: Works with MP4, MOV, AVI, and MKV files
- **Progress Tracking**: Real-time progress bar with frame count

## System Requirements

- Python 3.10 or higher
- ffmpeg (for audio processing)
- OpenCV with CSRT tracker support

### Installing ffmpeg

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html or use:
```bash
choco install ffmpeg
```

## Installation

1. Clone or download this repository:
```bash
git clone <repository-url>
cd watermark_removewr
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Verify installation:
```bash
python remove_watermark.py --help
```

## Usage

### Basic Usage

```bash
python remove_watermark.py input.mp4 output.mp4
```

### With Protected Bottom Area (for subtitles)

By default, the bottom 25% of the video is protected from inpainting to preserve subtitles:

```bash
python remove_watermark.py input.mp4 output.mp4 --protect-bottom 30
```

### Custom Protected Region

Protect a specific area (useful if subtitles are at the top or in a specific location):

```bash
python remove_watermark.py input.mp4 output.mp4 --protect-region 0,0,1920,100
```

The format is `x,y,width,height` where:
- `x`: Left coordinate
- `y`: Top coordinate
- `width`: Width of the region
- `height`: Height of the region

### Preview Mode

See real-time side-by-side comparison of original vs. cleaned frames:

```bash
python remove_watermark.py input.mp4 output.mp4 --preview
```

Press `Q` to skip preview if needed.

### Debug Mode

Save debug frames showing tracking boxes and protected zones:

```bash
python remove_watermark.py input.mp4 output.mp4 --debug
```

Debug frames will be saved in a temporary directory and the path will be printed.

### Multiple Watermarks

Remove multiple watermarks from the same video:

```bash
python remove_watermark.py input.mp4 output.mp4 --multi
```

You'll be prompted to select multiple watermarks interactively.

### Inpainting Methods

Choose the inpainting algorithm:

```bash
# TELEA method (default, faster)
python remove_watermark.py input.mp4 output.mp4 --method telea

# Navier-Stokes method (slower, potentially better quality)
python remove_watermark.py input.mp4 output.mp4 --method ns
```

## Advanced Examples

### Remove watermark with subtitle protection and preview

```bash
python remove_watermark.py video.mp4 cleaned.mp4 --protect-bottom 20 --preview
```

### Debug mode with custom protected region

```bash
python remove_watermark.py video.mp4 cleaned.mp4 --protect-region 100,50,800,100 --debug
```

### Multiple watermarks with Navier-Stokes inpainting

```bash
python remove_watermark.py video.mp4 cleaned.mp4 --multi --method ns
```

### Full feature combination

```bash
python remove_watermark.py input.mp4 output.mp4 \
  --protect-bottom 25 \
  --protect-region 0,0,1920,100 \
  --method telea \
  --preview \
  --debug \
  --multi
```

## Workflow

1. **Run the tool** with your input and output filenames
2. **Select the watermark** by drawing a rectangle on the first frame
   - Use mouse to draw a rectangle around the watermark
   - Press Enter or double-click to confirm
3. **Watch the progress** as the tool processes all frames
4. **Review the output** in the generated video file

## Watermark Selection Tips

- **Start early**: Begin drawing slightly before the watermark area
- **End late**: Continue drawing slightly after the watermark area
- **Be generous**: It's better to include a bit of extra space than to miss part of the watermark
- **Watch for movement**: Keep in mind that the watermark may move or change size - the tracker will follow it automatically

## Protected Zones

Protected zones are areas that will NOT be inpainted (useful for subtitles):

- **Default**: Bottom 25% of the video
- **Customize**: Use `--protect-bottom` to change the percentage
- **Custom region**: Use `--protect-region x,y,w,h` to define a specific area

If a tracked watermark overlaps with a protected zone, those frames will be skipped with a warning.

## Output Quality

- **FPS**: Preserved from input video
- **Resolution**: Preserved from input video
- **Codec**: H.264 (mp4v)
- **Audio**: Copied from input video using AAC codec

## Troubleshooting

### Error: "Cannot open video file"
- Ensure the file exists and the path is correct
- Verify the video format is supported (MP4, MOV, AVI, MKV)
- Check file permissions

### Error: "Cannot create output video file"
- Ensure the output directory is writable
- Check that there's enough disk space
- Verify you have write permissions

### Audio not merged
- Install ffmpeg (see Installation section)
- Verify the original video has an audio track
- Check that ffmpeg-python is installed correctly

### Poor inpainting quality
- Try the Navier-Stokes method (`--method ns`)
- Ensure the watermark selection is accurate
- Reduce the protect-bottom value if the watermark is large

### Tracker loses the watermark
- The tool will attempt to recover using template matching
- If it fails on many frames, try re-selecting the watermark more precisely
- Ensure the watermark is clearly visible in the first frame

## Performance Notes

- **Processing speed**: Depends on video resolution and length
  - 1080p video: ~0.5-1 frame per second
  - 4K video: ~0.1-0.3 frame per second
- **Memory usage**: Relatively low (typically < 500MB)
- **Disk space**: Output video size similar to input size

## Limitations

- Works best with static or slowly moving watermarks
- May struggle with semi-transparent watermarks
- Protected zones cannot contain the watermark
- Audio will be re-encoded (may affect audio quality)

## Advanced Features

### Template Matching Fallback

If the tracker confidence drops, the tool automatically attempts to find the watermark using template matching from the last successful frame. This helps maintain tracking when the watermark temporarily becomes hard to detect.

### Debug Visualization

Debug frames show:
- Red rectangles: Tracking boxes
- Green rectangles: Protected zones

This helps identify tracking issues and verify protection settings.

## License

MIT License - Feel free to use and modify for your needs.

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Try the `--debug` flag to inspect what's happening
3. Use `--preview` to see the results in real-time
4. Verify your input video format is supported

## Examples Directory

Here are some example commands for different scenarios:

### Scenario: Logo watermark in corner
```bash
python remove_watermark.py video.mp4 cleaned.mp4 --protect-bottom 20
```

### Scenario: Multiple watermarks
```bash
python remove_watermark.py video.mp4 cleaned.mp4 --multi --protect-bottom 15
```

### Scenario: Moving watermark with subtitles
```bash
python remove_watermark.py video.mp4 cleaned.mp4 --protect-bottom 30 --preview
```

### Scenario: Custom subtitle area at top
```bash
python remove_watermark.py video.mp4 cleaned.mp4 --protect-region 0,0,1920,100
```

Enjoy your watermark-free videos! 🎬
