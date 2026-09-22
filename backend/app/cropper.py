import os
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Callable

class SmartCropper:
    """
    Intelligently analyzes video frames using OpenCV face and motion detection
    to calculate a smoothed horizontal crop center (x) for 9:16 vertical video.
    """

    def __init__(self, smoothing_factor: float = 0.15, deadband_px: int = 25):
        self.smoothing_factor = smoothing_factor  # Lower = smoother, higher = more responsive
        self.deadband_px = deadband_px            # Minimum pixel shift required to move camera
        self._cascade = None

    def _get_cascade(self):
        if self._cascade is None:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self._cascade = cv2.CascadeClassifier(cascade_path)
        return self._cascade

    def calculate_crop_trajectory(
        self,
        video_path: Path,
        start_time: float,
        end_time: float,
        source_width: int,
        source_height: int,
        target_aspect_ratio: float = 9.0 / 16.0,
        sample_fps: float = 3.0,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Samples frames across [start_time, end_time] at `sample_fps`.
        Detects primary face/speaker location and produces a smoothed horizontal crop trajectory.
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            # Fallback to center crop
            return self._default_center_crop(source_width, source_height, target_aspect_ratio)

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        duration = end_time - start_time
        target_crop_w = int(source_height * target_aspect_ratio)
        # Ensure crop width is even and does not exceed source width
        target_crop_w = min(source_width, (target_crop_w // 2) * 2)
        target_crop_h = source_height

        max_x = source_width - target_crop_w
        default_x = max(0, (source_width - target_crop_w) // 2)

        sample_step_sec = 1.0 / sample_fps
        current_t = start_time
        raw_centers_x = []
        timestamps = []

        cascade = self._get_cascade()

        total_steps = int(duration * sample_fps)
        step_count = 0

        while current_t < end_time:
            cap.set(cv2.CAP_PROP_POS_MSEC, current_t * 1000.0)
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = cascade.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=4,
                minSize=(60, 60)
            )

            if len(faces) > 0:
                # Find largest face (highest visual prominence / closest speaker)
                largest_face = max(faces, key=lambda f: f[2] * f[3])
                fx, fy, fw, fh = largest_face
                face_center_x = fx + fw // 2
                raw_centers_x.append(face_center_x)
            else:
                # Fallback to previous or default center
                last_x = raw_centers_x[-1] if raw_centers_x else (source_width // 2)
                raw_centers_x.append(last_x)

            timestamps.append(round(current_t - start_time, 2))
            current_t += sample_step_sec
            step_count += 1

            if progress_callback and total_steps > 0:
                pct = min(100.0, (step_count / total_steps) * 100.0)
                progress_callback(pct, f"Tracking subject in frame {step_count}/{total_steps}")

        cap.release()

        if not raw_centers_x:
            return self._default_center_crop(source_width, source_height, target_aspect_ratio)

        # Apply Exponential Moving Average (EMA) and deadband smoothing
        smoothed_x = []
        current_smooth = float(raw_centers_x[0])

        for raw in raw_centers_x:
            # Deadband check: only update if delta is significant
            if abs(raw - current_smooth) > self.deadband_px:
                current_smooth = (
                    self.smoothing_factor * raw + (1.0 - self.smoothing_factor) * current_smooth
                )
            
            # Compute top-left X coordinate for 9:16 crop window
            crop_x = int(current_smooth - target_crop_w / 2.0)
            crop_x = max(0, min(crop_x, max_x))
            # Ensure even number
            crop_x = (crop_x // 2) * 2
            smoothed_x.append(crop_x)

        # Average stable crop X for simple single-pass rendering, or keyframes
        median_crop_x = int(np.median(smoothed_x))
        median_crop_x = (median_crop_x // 2) * 2

        return {
            "crop_width": target_crop_w,
            "crop_height": target_crop_h,
            "crop_x": median_crop_x,
            "crop_y": 0,
            "max_x": max_x,
            "trajectory": list(zip(timestamps, smoothed_x))
        }

    def _default_center_crop(
        self,
        source_width: int,
        source_height: int,
        target_aspect_ratio: float
    ) -> Dict[str, Any]:
        """Provides balanced center crop when detection cannot read frames."""
        target_crop_w = int(source_height * target_aspect_ratio)
        target_crop_w = min(source_width, (target_crop_w // 2) * 2)
        crop_x = max(0, (source_width - target_crop_w) // 2)
        crop_x = (crop_x // 2) * 2
        return {
            "crop_width": target_crop_w,
            "crop_height": source_height,
            "crop_x": crop_x,
            "crop_y": 0,
            "max_x": source_width - target_crop_w,
            "trajectory": []
        }
