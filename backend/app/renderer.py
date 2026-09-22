import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from .config import TEMP_DIR
from .hardware import check_nvenc_support

def render_clip(
    source_video_path: Path,
    output_clip_path: Path,
    start_time: float,
    end_time: float,
    crop_info: Dict[str, Any],
    source_fps: float = 30.0,
    source_width: int = 1920,
    source_height: int = 1080,
    output_format: str = "9:16",
    subtitles_ass_path: Optional[Path] = None,
    prefer_nvenc: bool = True,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Path:
    """
    Renders high-quality clip in a SINGLE FFmpeg encoding pass.
    Preserves FPS, preserves high-fidelity audio, applies smart crop & optional captions.
    """
    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
    duration = end_time - start_time
    if duration <= 0:
        raise ValueError(f"Invalid duration: start={start_time}, end={end_time}")

    # Ensure output directory exists
    output_clip_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Determine Target Dimensions based on Format
    crop_w = crop_info.get("crop_width", int(source_height * 9 / 16))
    crop_h = crop_info.get("crop_height", source_height)
    crop_x = crop_info.get("crop_x", (source_width - crop_w) // 2)
    crop_y = crop_info.get("crop_y", 0)

    # Output scale mapping
    if output_format == "9:16":
        # Target 1080x1920 if source is at least 1080p, else proportional
        out_w = 1080 if source_height >= 1080 else ((int(source_height * 9 / 16) // 2) * 2)
        out_h = 1920 if source_height >= 1080 else ((source_height // 2) * 2)
    elif output_format == "1:1":
        out_w = 1080
        out_h = 1080
        crop_w = min(source_width, source_height)
        crop_h = crop_w
        crop_x = max(0, (source_width - crop_w) // 2)
    elif output_format == "4:5":
        out_w = 1080
        out_h = 1350
        crop_w = int(source_height * 4 / 5)
        crop_h = source_height
        crop_x = max(0, (source_width - crop_w) // 2)
    elif output_format == "16:9":
        # Original landscape format
        out_w = source_width
        out_h = source_height
        crop_w = source_width
        crop_h = source_height
        crop_x = 0
        crop_y = 0
    else:
        out_w = 1080
        out_h = 1920

    # Ensure even dimensions
    out_w = (out_w // 2) * 2
    out_h = (out_h // 2) * 2
    crop_w = (crop_w // 2) * 2
    crop_h = (crop_h // 2) * 2
    crop_x = (crop_x // 2) * 2
    crop_y = (crop_y // 2) * 2

    # 2. Build Filtergraph
    filter_chains = []
    
    # Crop filter (skip if 16:9 full frame)
    if output_format != "16:9":
        filter_chains.append(f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}")
    
    # Scale filter
    filter_chains.append(f"scale={out_w}:{out_h}:flags=lanczos")

    # Optional Subtitle Burn-In
    if subtitles_ass_path and subtitles_ass_path.exists():
        # FFmpeg requires escaping colon and backslashes in Windows file paths for subtitles filter
        escaped_sub = str(subtitles_ass_path).replace("\\", "/").replace(":", r"\:")
        filter_chains.append(f"subtitles='{escaped_sub}'")

    vf_string = ",".join(filter_chains)

    # 3. Choose Hardware (NVENC) vs CPU Encoder
    use_nvenc = prefer_nvenc and check_nvenc_support()

    if use_nvenc:
        vcodec = "h264_nvenc"
        video_params = [
            "-c:v", vcodec,
            "-preset", "p5",       # High quality preset
            "-tune", "hq",
            "-rc", "vbr",
            "-cq", "19",          # Quality-focused constant quantization
            "-b:v", "0",
            "-spatial_aq", "1",
            "-temporal_aq", "1"
        ]
    else:
        vcodec = "libx264"
        video_params = [
            "-c:v", vcodec,
            "-preset", "slow",     # Quality-focused
            "-crf", "18"           # Visually lossless
        ]

    # Preserve exact FPS
    fps_val = str(source_fps) if source_fps > 0 else "30"

    cmd = [
        ffmpeg_bin,
        "-y",
        "-ss", str(start_time),
        "-to", str(end_time),
        "-i", str(source_video_path),
        "-vf", vf_string,
        "-r", fps_val,
    ] + video_params + [
        "-c:a", "aac",
        "-ar", "48000",            # 48 kHz AAC audio
        "-b:a", "320k",           # High audio bitrate
        "-movflags", "+faststart", # Enable instant web streaming preview
        str(output_clip_path)
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        universal_newlines=True
    )

    # Track render progress via stderr
    time_regex = re.compile(r"time=(\d+):(\d+):(\d+\.?\d*)")

    if process.stderr:
        for line in process.stderr:
            match = time_regex.search(line)
            if match and progress_callback and duration > 0:
                hours = int(match.group(1))
                mins = int(match.group(2))
                secs = float(match.group(3))
                current_rendered_sec = hours * 3600 + mins * 60 + secs
                pct = min(100.0, (current_rendered_sec / duration) * 100.0)
                progress_callback(pct, f"Rendering video ({vcodec}): {pct:.1f}%")

    process.wait()

    if process.returncode != 0:
        err = process.stderr.read() if process.stderr else "Unknown FFmpeg error"
        raise RuntimeError(f"FFmpeg render failed: {err}")

    if not output_clip_path.exists() or output_clip_path.stat().st_size == 0:
        raise RuntimeError(f"Rendered clip file not found or empty: {output_clip_path}")

    return output_clip_path
