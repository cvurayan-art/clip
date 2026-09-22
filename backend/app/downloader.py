import os
import re
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from .config import DOWNLOADS_DIR

def is_valid_youtube_url(url: str) -> bool:
    """Validates whether a string is a valid YouTube video URL (including youtu.be, shorts, ?si=, etc.)."""
    if not url or not isinstance(url, str):
        return False
    pattern = r"(?:https?://)?(?:www\.|m\.)?(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|live/|embed/)|youtu\.be/)([a-zA-Z0-9_-]{11})"
    return bool(re.search(pattern, url.strip()))

def sanitize_filename(name: str) -> str:
    """Removes special characters to produce safe Windows filename."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def get_video_metadata(url: str) -> Dict[str, Any]:
    """
    Fetches video metadata (title, duration, resolution, fps, thumbnail)
    without downloading the video stream.
    """
    if not is_valid_youtube_url(url):
        raise ValueError("Invalid YouTube URL. Please provide a standard YouTube video link.")

    yt_dlp_bin = shutil.which("yt-dlp") or "yt-dlp"
    cmd = [
        yt_dlp_bin,
        "--skip-download",
        "--dump-single-json",
        "--no-playlist",
        url.strip()
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        if res.returncode != 0:
            err = res.stderr.strip() or "Failed to retrieve video metadata"
            raise RuntimeError(f"yt-dlp error: {err}")
        
        data = json.loads(res.stdout)
        
        # Extract best resolution and FPS
        width = data.get("width") or 1920
        height = data.get("height") or 1080
        fps = round(data.get("fps") or 30.0, 2)
        duration = int(data.get("duration") or 0)
        
        # Format duration HH:MM:SS
        hours = duration // 3600
        mins = (duration % 3600) // 60
        secs = duration % 60
        if hours > 0:
            duration_str = f"{hours:02d}:{mins:02d}:{secs:02d}"
        else:
            duration_str = f"{mins:02d}:{secs:02d}"

        return {
            "id": data.get("id"),
            "title": data.get("title", "Untitled Video"),
            "duration": duration,
            "duration_str": duration_str,
            "width": width,
            "height": height,
            "resolution": f"{width}x{height}",
            "fps": fps,
            "thumbnail": data.get("thumbnail", ""),
            "channel": data.get("uploader", ""),
            "url": url.strip(),
        }
    except subprocess.TimeoutExpired:
        raise TimeoutError("Timed out while contacting YouTube. Please check network connectivity.")
    except Exception as e:
        raise RuntimeError(f"Could not analyze video: {str(e)}")

def download_source_video(
    url: str,
    video_id: str,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Path:
    """
    Downloads the highest quality video and audio stream merged into an MP4 file.
    Does NOT reduce quality.
    """
    yt_dlp_bin = shutil.which("yt-dlp") or "yt-dlp"
    output_template = str(DOWNLOADS_DIR / f"{video_id}.%(ext)s")
    final_mp4 = DOWNLOADS_DIR / f"{video_id}.mp4"

    # If already downloaded, return it directly
    if final_mp4.exists() and final_mp4.stat().st_size > 100000:
        if progress_callback:
            progress_callback(100.0, "Source video already cached locally")
        return final_mp4

    cmd = [
        yt_dlp_bin,
        "-f", "bv*+ba/b",
        "--merge-output-format", "mp4",
        "-o", output_template,
        "--no-playlist",
        "--newline",
        url.strip()
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    percent_regex = re.compile(r"\[download\]\s+(\d+\.?\d*)%")

    if process.stdout:
        for line in process.stdout:
            match = percent_regex.search(line)
            if match and progress_callback:
                pct = float(match.group(1))
                progress_callback(pct, f"Downloading video: {pct:.1f}%")

    process.wait()
    if process.returncode != 0:
        raise RuntimeError("yt-dlp failed to download the video.")

    # Locate the downloaded file
    candidates = list(DOWNLOADS_DIR.glob(f"{video_id}.*"))
    for cand in candidates:
        if cand.suffix.lower() in [".mp4", ".mkv", ".webm"]:
            return cand

    raise FileNotFoundError(f"Downloaded video for {video_id} was not found on disk.")
