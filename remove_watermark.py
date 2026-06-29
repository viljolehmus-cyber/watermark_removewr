#!/usr/bin/env python3
"""
Watermark removal tool for videos using OpenCV tracking and inpainting.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Tuple, List
import tempfile
import shutil

import cv2
import numpy as np
from tqdm import tqdm

try:
    import ffmpeg
except ImportError:
    ffmpeg = None


class WatermarkRemover:
    """Main class for watermark removal from videos."""

    def __init__(
        self,
        input_path: str,
        output_path: str,
        protect_bottom: float = 25.0,
        protect_region: Optional[Tuple[int, int, int, int]] = None,
        method: str = "telea",
        preview: bool = False,
        debug: bool = False,
        multi: bool = False,
    ):
        """
        Initialize the watermark remover.

        Args:
            input_path: Path to input video file
            output_path: Path to output video file
            protect_bottom: Percentage of bottom area to protect from inpainting (default: 25%)
            protect_region: Custom protected region (x, y, w, h)
            method: Inpainting method: "telea", "ns", or "lama"
            preview: Show real-time preview of processing
            debug: Save debug frames showing tracking and protected zones
            multi: Support multiple watermarks
        """
        self.input_path = input_path
        self.output_path = output_path
        self.protect_bottom = protect_bottom
        self.protect_region = protect_region
        self.method = method
        self.preview = preview
        self.debug = debug
        self.multi = multi

        self.cap: Optional[cv2.VideoCapture] = None
        self.fps: float = 30.0
        self.width: int = 0
        self.height: int = 0
        self.total_frames: int = 0
        self.rois: List[Tuple[int, int, int, int]] = []
        self.trackers: List[cv2.Tracker] = []
        self.debug_dir: Optional[str] = None

        if self.debug:
            self.debug_dir = tempfile.mkdtemp(prefix="watermark_debug_")

    def validate_input(self) -> bool:
        """Validate input file exists and is readable."""
        if not os.path.exists(self.input_path):
            print(f"Error: Input file '{self.input_path}' not found")
            return False

        cap = cv2.VideoCapture(self.input_path)
        if not cap.isOpened():
            print(f"Error: Cannot open video file '{self.input_path}'")
            return False

        cap.release()
        return True

    def open_video(self) -> bool:
        """Open video file and get properties."""
        self.cap = cv2.VideoCapture(self.input_path)

        if not self.cap.isOpened():
            print(f"Error: Cannot open video file '{self.input_path}'")
            return False

        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if self.fps <= 0:
            self.fps = 30.0

        print(f"Video properties: {self.width}x{self.height} @ {self.fps} FPS ({self.total_frames} frames)")
        return True

    def select_watermark(self) -> bool:
        """
        Select watermark region by drawing on first frame.
        User draws a rectangle around the watermark.
        """
        if not self.cap:
            return False

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = self.cap.read()

        if not ret:
            print("Error: Cannot read first frame")
            return False

        print("\n=== Watermark Selection ===")
        print("Draw a rectangle around the watermark using mouse")
        print("Left-click and drag to select, then press Enter or double-click")

        roi = cv2.selectROI("Select Watermark", frame, fromCenter=False, showCrosshair=True)
        cv2.destroyAllWindows()

        if roi[2] == 0 or roi[3] == 0:
            print("Error: No region selected")
            return False

        self.rois.append(roi)
        print(f"Selected ROI: x={roi[0]}, y={roi[1]}, w={roi[2]}, h={roi[3]}")

        if self.multi:
            while True:
                response = input("Select another watermark? (y/n): ").lower().strip()
                if response == "y":
                    roi = cv2.selectROI("Select Watermark", frame, fromCenter=False, showCrosshair=True)
                    cv2.destroyAllWindows()
                    if roi[2] > 0 and roi[3] > 0:
                        self.rois.append(roi)
                        print(f"Selected ROI: x={roi[0]}, y={roi[1]}, w={roi[2]}, h={roi[3]}")
                else:
                    break

        return True

    def initialize_trackers(self) -> bool:
        """Initialize CSRT tracker for each ROI."""
        if not self.cap or not self.rois:
            return False

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = self.cap.read()

        if not ret:
            print("Error: Cannot read first frame for tracker initialization")
            return False

        for roi in self.rois:
            tracker = cv2.TrackerCSRT_create()
            x, y, w, h = roi
            success = tracker.init(frame, (x, y, w, h))

            if not success:
                print(f"Error: Failed to initialize tracker for ROI {roi}")
                return False

            self.trackers.append(tracker)

        print(f"Initialized {len(self.trackers)} tracker(s)")
        return True

    def is_in_protected_zone(self, roi: Tuple[int, int, int, int]) -> bool:
        """
        Check if ROI overlaps with protected zone.

        Args:
            roi: Region of interest (x, y, w, h)

        Returns:
            True if ROI overlaps with protected zone
        """
        x, y, w, h = roi

        if self.protect_region:
            px, py, pw, ph = self.protect_region
            if not (x + w < px or x > px + pw or y + h < py or y > py + ph):
                return True

        if self.protect_bottom > 0:
            protect_y = int(self.height * (100 - self.protect_bottom) / 100)
            if y + h > protect_y:
                return True

        return False

    def inpaint_frame(self, frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        Inpaint the watermark region in a frame.

        Args:
            frame: Input frame
            mask: Mask of regions to inpaint (white = inpaint)

        Returns:
            Inpainted frame
        """
        if self.method == "telea":
            return cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA)
        elif self.method == "ns":
            return cv2.inpaint(frame, mask, 3, cv2.INPAINT_NS)
        else:
            return cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA)

    def process_video(self) -> bool:
        """
        Process video: track watermarks and inpaint frames.

        Returns:
            True if successful
        """
        if not self.cap or not self.trackers:
            return False

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(
            self.output_path,
            fourcc,
            self.fps,
            (self.width, self.height),
        )

        if not out.isOpened():
            print(f"Error: Cannot create output video file '{self.output_path}'")
            return False

        frame_count = 0
        failed_tracks: List[int] = []
        skipped_frames: int = 0
        template_frames: List[np.ndarray] = []
        last_rois: List[Tuple[int, int, int, int]] = self.rois.copy()

        print("\n=== Processing Video ===")

        with tqdm(total=self.total_frames, desc="Processing") as pbar:
            while True:
                ret, frame = self.cap.read()

                if not ret:
                    break

                original_frame = frame.copy()
                masks: List[np.ndarray] = []
                current_rois: List[Tuple[int, int, int, int]] = []
                frame_skipped = False

                for i, tracker in enumerate(self.trackers):
                    success, roi = tracker.update(frame)
                    x, y, w, h = [int(v) for v in roi]
                    roi_tuple = (x, y, w, h)

                    if success and w > 0 and h > 0:
                        if self.is_in_protected_zone(roi_tuple):
                            if frame_count == 0:
                                print(f"Warning: Watermark {i} in protected zone, skipping frame {frame_count}")
                            skipped_frames += 1
                            frame_skipped = True
                            last_rois[i] = roi_tuple
                            continue

                        last_rois[i] = roi_tuple
                        current_rois.append(roi_tuple)

                        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
                        cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
                        masks.append(mask)

                        if self.debug:
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    else:
                        if i not in failed_tracks:
                            failed_tracks.append(i)

                if not frame_skipped:
                    for mask in masks:
                        frame = self.inpaint_frame(frame, mask)

                if self.debug and self.debug_dir:
                    if self.protect_bottom > 0:
                        protect_y = int(self.height * (100 - self.protect_bottom) / 100)
                        cv2.rectangle(frame, (0, protect_y), (self.width, self.height), (0, 255, 0), 2)

                    if self.protect_region:
                        px, py, pw, ph = self.protect_region
                        cv2.rectangle(frame, (px, py), (px + pw, py + ph), (0, 255, 0), 2)

                    debug_path = os.path.join(self.debug_dir, f"frame_{frame_count:06d}.jpg")
                    cv2.imwrite(debug_path, frame)

                if self.preview:
                    h_concat = np.hstack((original_frame, frame))
                    cv2.imshow("Original vs Cleaned", h_concat)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        self.preview = False

                out.write(frame)
                frame_count += 1
                pbar.update(1)

        out.release()
        cv2.destroyAllWindows()

        print(f"\nProcessing complete: {frame_count} frames")
        print(f"Skipped frames (protected zone): {skipped_frames}")

        if self.debug_dir:
            print(f"Debug frames saved to: {self.debug_dir}")

        return True

    def merge_audio(self) -> bool:
        """
        Merge audio from original video to output video using ffmpeg.

        Returns:
            True if successful
        """
        if ffmpeg is None:
            print("Warning: ffmpeg-python not installed, skipping audio merge")
            return True

        print("\n=== Merging Audio ===")

        try:
            temp_output = self.output_path + ".temp.mp4"

            stream = ffmpeg.input(self.input_path)
            audio = stream["a"] if "a" in stream else None

            if audio is None:
                print("No audio track found in input video")
                return True

            video = ffmpeg.input(self.output_path)["v"]

            output = ffmpeg.output(video, audio, temp_output, vcodec="copy", acodec="aac", shortest=None)
            ffmpeg.run(output, capture_stdout=True, capture_stderr=True, quiet=True)

            os.replace(temp_output, self.output_path)
            print("Audio merged successfully")
            return True

        except Exception as e:
            print(f"Warning: Failed to merge audio: {e}")
            return True

    def run(self) -> bool:
        """
        Run the complete watermark removal pipeline.

        Returns:
            True if successful
        """
        print("=== Watermark Removal Tool ===\n")

        if not self.validate_input():
            return False

        if not self.open_video():
            return False

        if not self.select_watermark():
            return False

        if not self.initialize_trackers():
            return False

        if not self.process_video():
            return False

        if not self.merge_audio():
            return False

        if self.cap:
            self.cap.release()

        print(f"\n✓ Output video saved to: {self.output_path}")
        return True


def parse_region(region_str: str) -> Tuple[int, int, int, int]:
    """
    Parse region string in format 'x,y,w,h'.

    Args:
        region_str: Region string

    Returns:
        Tuple of (x, y, w, h)
    """
    try:
        parts = [int(x.strip()) for x in region_str.split(",")]
        if len(parts) != 4:
            raise ValueError("Region must have exactly 4 values")
        return tuple(parts)  # type: ignore
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid region format: {e}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Remove watermarks from videos using OpenCV tracking and inpainting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python remove_watermark.py input.mp4 output.mp4
  python remove_watermark.py input.mp4 output.mp4 --protect-bottom 30
  python remove_watermark.py input.mp4 output.mp4 --protect-region 0,0,1920,100
  python remove_watermark.py input.mp4 output.mp4 --preview --debug
  python remove_watermark.py input.mp4 output.mp4 --method telea --multi
        """,
    )

    parser.add_argument("input", help="Input video file")
    parser.add_argument("output", help="Output video file")
    parser.add_argument(
        "--protect-bottom",
        type=float,
        default=25.0,
        help="Percentage of bottom area to protect from inpainting (default: 25%%)",
    )
    parser.add_argument(
        "--protect-region",
        type=parse_region,
        help="Custom protected region in format 'x,y,w,h' (e.g., '0,0,1920,100')",
    )
    parser.add_argument(
        "--method",
        choices=["telea", "ns"],
        default="telea",
        help="Inpainting method: telea (default) or ns (Navier-Stokes)",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Show real-time preview of processing (original vs cleaned)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Save debug frames showing tracking boxes and protected zones",
    )
    parser.add_argument(
        "--multi",
        action="store_true",
        help="Support multiple watermarks (select multiple regions)",
    )

    args = parser.parse_args()

    try:
        remover = WatermarkRemover(
            input_path=args.input,
            output_path=args.output,
            protect_bottom=args.protect_bottom,
            protect_region=args.protect_region,
            method=args.method,
            preview=args.preview,
            debug=args.debug,
            multi=args.multi,
        )

        if remover.run():
            return 0
        else:
            return 1

    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        return 130
    except Exception as e:
        print(f"\nError: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
