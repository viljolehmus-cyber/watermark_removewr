#!/usr/bin/env python3
"""
Flask web application for watermark removal from videos.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Tuple
import tempfile
import shutil

from flask import Flask, render_template, request, jsonify, send_file, url_for
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from tqdm import tqdm

try:
    import ffmpeg
except ImportError:
    ffmpeg = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 2000 * 1024 * 1024  # 2GB max file size
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp(prefix='watermark_uploads_')
app.config['OUTPUT_FOLDER'] = tempfile.mkdtemp(prefix='watermark_output_')

ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm', 'flv', 'm4v'}
SUPPORTED_FORMATS = {'mp4', 'mov', 'avi', 'mkv'}


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_video_properties(video_path: str) -> Optional[dict]:
    """Get video properties."""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None

        props = {
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS)
        }
        cap.release()
        return props
    except Exception as e:
        logger.error(f"Error getting video properties: {e}")
        return None


def extract_first_frame(video_path: str, output_path: str, max_width: int = 640) -> bool:
    """Extract first frame as JPEG thumbnail."""
    try:
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()

        if ret:
            # Resize if too large
            height, width = frame.shape[:2]
            if width > max_width:
                scale = max_width / width
                new_height = int(height * scale)
                frame = cv2.resize(frame, (max_width, new_height))

            cv2.imwrite(output_path, frame)
            return True
    except Exception as e:
        logger.error(f"Error extracting first frame: {e}")

    return False


def is_in_protected_zone(
    roi: Tuple[int, int, int, int],
    height: int,
    protect_bottom: float = 25.0,
    protect_region: Optional[Tuple[int, int, int, int]] = None
) -> bool:
    """Check if ROI overlaps with protected zone."""
    x, y, w, h = roi

    if protect_region:
        px, py, pw, ph = protect_region
        if not (x + w < px or x > px + pw or y + h < py or y > py + ph):
            return True

    if protect_bottom > 0:
        protect_y = int(height * (100 - protect_bottom) / 100)
        if y + h > protect_y:
            return True

    return False


def inpaint_frame(frame: np.ndarray, mask: np.ndarray, method: str = "telea") -> np.ndarray:
    """Inpaint the watermark region in a frame."""
    if method == "ns":
        return cv2.inpaint(frame, mask, 3, cv2.INPAINT_NS)
    else:
        return cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA)


def process_watermark(
    input_path: str,
    output_path: str,
    rois: list,
    protect_bottom: float = 25.0,
    protect_region: Optional[Tuple[int, int, int, int]] = None,
    method: str = "telea",
    progress_callback=None
) -> bool:
    """
    Process video to remove watermarks.

    Args:
        input_path: Input video path
        output_path: Output video path
        rois: List of ROI tuples (x, y, w, h)
        protect_bottom: Percentage of bottom area to protect
        protect_region: Custom protected region
        method: Inpainting method
        progress_callback: Callback function for progress updates

    Returns:
        True if successful
    """
    cap = cv2.VideoCapture(input_path)

    if not cap.isOpened():
        logger.error("Cannot open input video")
        return False

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if fps <= 0:
        fps = 30.0

    # Initialize trackers
    trackers = []
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    ret, frame = cap.read()

    if not ret:
        logger.error("Cannot read first frame")
        cap.release()
        return False

    for roi in rois:
        tracker = cv2.TrackerCSRT_create()
        try:
            tracker.init(frame, tuple(roi))
            trackers.append(tracker)
        except Exception as e:
            logger.error(f"Failed to initialize tracker: {e}")
            cap.release()
            return False

    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    if not out.isOpened():
        logger.error("Cannot create output video")
        cap.release()
        return False

    # Process frames
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Track and inpaint
        for tracker in trackers:
            success, roi = tracker.update(frame)
            if success:
                x, y, w, h = [int(v) for v in roi]

                if not is_in_protected_zone((x, y, w, h), height, protect_bottom, protect_region):
                    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
                    cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
                    frame = inpaint_frame(frame, mask, method)

        out.write(frame)
        frame_count += 1

        if progress_callback:
            progress_callback(frame_count, total_frames)

    cap.release()
    out.release()

    # Merge audio
    try:
        if ffmpeg:
            temp_output = output_path + ".temp.mp4"
            stream = ffmpeg.input(input_path)
            audio = stream["a"] if "a" in stream else None

            if audio:
                video = ffmpeg.input(output_path)["v"]
                output = ffmpeg.output(video, audio, temp_output, vcodec="copy", acodec="aac", shortest=None)
                ffmpeg.run(output, capture_stdout=True, capture_stderr=True, quiet=True)
                os.replace(temp_output, output_path)
    except Exception as e:
        logger.warning(f"Failed to merge audio: {e}")

    return True


@app.route('/')
def index():
    """Render main page."""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_video():
    """Handle video upload."""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file'}), 400

    file = request.files['video']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    try:
        filename = secure_filename(file.filename)
        # Add timestamp to avoid collisions
        import time
        filename = f"{int(time.time())}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        file.save(filepath)

        # Get video properties
        props = get_video_properties(filepath)
        if not props:
            os.remove(filepath)
            return jsonify({'error': 'Invalid video file'}), 400

        # Extract first frame
        frame_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{filename}_frame.jpg")
        extract_first_frame(filepath, frame_path)

        session_id = filename.split('_')[0]

        return jsonify({
            'success': True,
            'sessionId': session_id,
            'filePath': filepath,
            'frameUrl': url_for('get_frame', session_id=session_id),
            'properties': props
        })

    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/get-frame/<session_id>')
def get_frame(session_id: str):
    """Get first frame image."""
    try:
        # Find the frame file
        for file in os.listdir(app.config['OUTPUT_FOLDER']):
            if file.startswith(session_id) and file.endswith('_frame.jpg'):
                frame_path = os.path.join(app.config['OUTPUT_FOLDER'], file)
                return send_file(frame_path, mimetype='image/jpeg')
    except Exception as e:
        logger.error(f"Error getting frame: {e}")

    return jsonify({'error': 'Frame not found'}), 404


@app.route('/api/process', methods=['POST'])
def process():
    """Process video with watermark removal."""
    try:
        data = request.get_json()
        session_id = data.get('sessionId')
        rois = data.get('rois', [])
        protect_bottom = float(data.get('protectBottom', 25.0))
        method = data.get('method', 'telea')

        # Find input file
        input_path = None
        for file in os.listdir(app.config['UPLOAD_FOLDER']):
            if file.startswith(session_id):
                input_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
                break

        if not input_path:
            return jsonify({'error': 'Video file not found'}), 404

        if not rois or len(rois) == 0:
            return jsonify({'error': 'No watermark selected'}), 400

        # Get output path
        original_name = os.path.basename(input_path).split('_', 1)[1]
        base_name = original_name.rsplit('.', 1)[0]
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_cleaned.mp4")

        # Process video
        logger.info(f"Processing video: {input_path}")
        logger.info(f"ROIs: {rois}")

        success = process_watermark(
            input_path,
            output_path,
            rois,
            protect_bottom=protect_bottom,
            method=method
        )

        if not success:
            return jsonify({'error': 'Failed to process video'}), 500

        logger.info(f"Video processed: {output_path}")

        return jsonify({
            'success': True,
            'downloadUrl': url_for('download_video', session_id=session_id)
        })

    except Exception as e:
        logger.error(f"Processing error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<session_id>')
def download_video(session_id: str):
    """Download processed video."""
    try:
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_cleaned.mp4")

        if not os.path.exists(output_path):
            return jsonify({'error': 'Video not found'}), 404

        return send_file(
            output_path,
            mimetype='video/mp4',
            as_attachment=True,
            download_name=f"cleaned_{session_id}.mp4"
        )

    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/status/<session_id>')
def status(session_id: str):
    """Get processing status."""
    try:
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_cleaned.mp4")

        if os.path.exists(output_path):
            size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            return jsonify({
                'status': 'complete',
                'size': f"{size:.1f} MB"
            })
        else:
            return jsonify({
                'status': 'processing'
            })

    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    return jsonify({'error': 'File too large (max 2GB)'}), 413


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
