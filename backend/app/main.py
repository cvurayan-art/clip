import os
import zipfile
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from .config import load_settings, save_settings, OUTPUT_DIR, DOWNLOADS_DIR
from .hardware import get_hardware_status
from .downloader import get_video_metadata, is_valid_youtube_url
from .jobs import JobManager

app = FastAPI(
    title="Local AI Video Clipper API",
    description="Crayo/OpusClip-style personal AI video clipper backend",
    version="1.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

job_manager = JobManager()

# Request Models
class AnalyzeRequest(BaseModel):
    url: str = Field(..., description="YouTube video URL to analyze")

class GenerateRequest(BaseModel):
    video_info: Dict[str, Any]
    num_clips: int = Field(5, ge=1, le=20)
    min_duration: float = Field(30.0, ge=10.0, le=120.0)
    max_duration: float = Field(60.0, ge=15.0, le=180.0)
    selection_mode: str = Field("Best Overall")
    custom_prompt: Optional[str] = None
    output_format: str = Field("9:16")
    captions_enabled: bool = Field(False)

class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, Any]

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": "Local AI Video Clipper",
        "version": "1.0.0"
    }

@app.get("/api/hardware")
def get_hardware():
    """Returns detected GPU, VRAM, CUDA, NVENC, and RAM metrics."""
    return get_hardware_status()

@app.get("/api/settings")
def get_settings():
    """Returns current application settings."""
    return load_settings()

@app.post("/api/settings")
def update_settings(payload: SettingsUpdateRequest):
    """Updates settings on disk."""
    success = save_settings(payload.settings)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save settings.")
    return {"status": "success", "settings": load_settings()}

@app.post("/api/analyze")
def analyze_video(req: AnalyzeRequest):
    """
    Validates YouTube URL and retrieves metadata (title, duration, resolution, fps).
    """
    if not is_valid_youtube_url(req.url):
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL. Please enter a valid link (e.g., https://www.youtube.com/watch?v=...)"
        )
    try:
        metadata = get_video_metadata(req.url)
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate")
def start_generation(req: GenerateRequest):
    """
    Initiates asynchronous clipping workflow and returns job ID.
    """
    settings_dict = {
        "num_clips": req.num_clips,
        "min_duration": req.min_duration,
        "max_duration": req.max_duration,
        "selection_mode": req.selection_mode,
        "custom_prompt": req.custom_prompt,
        "output_format": req.output_format,
        "captions_enabled": req.captions_enabled
    }

    job_id = job_manager.create_job(video_info=req.video_info, settings=settings_dict)
    job_manager.run_job_async(job_id)

    return {
        "job_id": job_id,
        "status": "queued",
        "message": f"Clip generation job {job_id} started."
    }

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    """Returns real-time status, stage progress, and generated clips for a job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
    return job

@app.delete("/api/jobs/{job_id}")
def cancel_job(job_id: str):
    """Cancels or deletes a job."""
    with job_manager.lock:
        if job_id in job_manager.jobs:
            del job_manager.jobs[job_id]
            return {"status": "deleted", "job_id": job_id}
    raise HTTPException(status_code=404, detail="Job not found.")

@app.get("/api/clips/{filename}/file")
def stream_clip_file(filename: str):
    """Streams MP4 video for instant in-browser preview."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Clip file {filename} not found.")
    return FileResponse(path=str(file_path), media_type="video/mp4", filename=filename)

@app.get("/api/clips/{filename}/download")
def download_clip_file(filename: str):
    """Directly downloads individual MP4 clip file."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Clip file {filename} not found.")
    return FileResponse(
        path=str(file_path),
        media_type="application/octet-stream",
        filename=filename
    )

@app.get("/api/jobs/{job_id}/download-all")
def download_all_clips(job_id: str):
    """Packages all clips for a job into a ZIP archive for one-click download."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    clips = job.get("clips", [])
    if not clips:
        raise HTTPException(status_code=400, detail="No clips available to download.")

    zip_filename = f"{job_id}_all_clips.zip"
    zip_path = OUTPUT_DIR / zip_filename

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for clip in clips:
            clip_path = Path(clip["file_path"])
            if clip_path.exists():
                zipf.write(clip_path, arcname=clip["filename"])

    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=zip_filename
    )

@app.post("/api/open-folder")
def open_output_folder():
    """Opens the output directory in Windows File Explorer."""
    try:
        subprocess.run(["explorer.exe", str(OUTPUT_DIR)], check=False)
        return {"status": "opened", "path": str(OUTPUT_DIR)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open explorer: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
