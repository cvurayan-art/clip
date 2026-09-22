import os
import uuid
import time
import shutil
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional

from .config import OUTPUT_DIR, TEMP_DIR, load_settings
from .downloader import download_source_video
from .transcriber import VideoTranscriber
from .selector import ClipSelector
from .cropper import SmartCropper
from .captions import generate_ass_subtitles
from .renderer import render_clip

class JobManager:
    """
    Manages asynchronous video clipping jobs with real stage-by-stage progress tracking.
    """

    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

    def create_job(self, video_info: Dict[str, Any], settings: Dict[str, Any]) -> str:
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        with self.lock:
            self.jobs[job_id] = {
                "id": job_id,
                "status": "queued",
                "stage": "queued",
                "progress_percent": 0.0,
                "current_message": "Job queued for processing...",
                "stages": {
                    "download": {"percent": 0.0, "status": "pending", "message": "Waiting to download..."},
                    "audio": {"percent": 0.0, "status": "pending", "message": "Pending audio extraction..."},
                    "transcribe": {"percent": 0.0, "status": "pending", "message": "Pending transcription..."},
                    "highlights": {"percent": 0.0, "status": "pending", "message": "Pending highlight selection..."},
                    "subjects": {"percent": 0.0, "status": "pending", "message": "Pending subject tracking..."},
                    "render": {"percent": 0.0, "status": "pending", "message": "Pending clip render..."},
                },
                "video_info": video_info,
                "settings": settings,
                "clips": [],
                "error_message": None,
                "created_at": time.time(),
            }
        return job_id

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            return self.jobs.get(job_id)

    def update_stage(self, job_id: str, stage_key: str, percent: float, message: str, stage_status: str = "in_progress"):
        with self.lock:
            if job_id not in self.jobs:
                return
            job = self.jobs[job_id]
            job["stage"] = stage_key
            job["current_message"] = message
            if stage_key in job["stages"]:
                job["stages"][stage_key]["percent"] = round(percent, 1)
                job["stages"][stage_key]["message"] = message
                job["stages"][stage_key]["status"] = stage_status

            # Calculate weighted overall progress
            # Weights: download (15%), audio (5%), transcribe (35%), highlights (15%), subjects (10%), render (20%)
            weights = {
                "download": 0.15,
                "audio": 0.05,
                "transcribe": 0.35,
                "highlights": 0.15,
                "subjects": 0.10,
                "render": 0.20
            }
            overall = 0.0
            for k, w in weights.items():
                overall += (job["stages"][k]["percent"] / 100.0) * w * 100.0
            job["progress_percent"] = min(99.0, round(overall, 1))

    def run_job_async(self, job_id: str):
        thread = threading.Thread(target=self._execute_job, args=(job_id,), daemon=True)
        thread.start()

    def _execute_job(self, job_id: str):
        job = self.get_job(job_id)
        if not job:
            return

        with self.lock:
            self.jobs[job_id]["status"] = "processing"

        cfg = load_settings()
        video_info = job["video_info"]
        req_settings = job["settings"]

        url = video_info["url"]
        video_id = video_info["id"]
        total_duration = video_info.get("duration", 0)

        # Job configuration options
        num_clips = req_settings.get("num_clips", 5)
        min_dur = req_settings.get("min_duration", 30.0)
        max_dur = req_settings.get("max_duration", 60.0)
        selection_mode = req_settings.get("selection_mode", "Best Overall")
        custom_prompt = req_settings.get("custom_prompt")
        output_format = req_settings.get("output_format", "9:16")
        captions_enabled = req_settings.get("captions_enabled", False)

        try:
            # STAGE 1: Download highest quality video
            self.update_stage(job_id, "download", 5.0, "Starting source download...")
            
            def download_cb(pct, msg):
                self.update_stage(job_id, "download", pct, msg)

            source_path = download_source_video(url, video_id, progress_callback=download_cb)
            self.update_stage(job_id, "download", 100.0, "Source video downloaded", stage_status="completed")

            # STAGE 2 & 3: Audio extraction & faster-whisper transcription
            self.update_stage(job_id, "audio", 100.0, "Extracting audio for speech analysis...", stage_status="completed")
            self.update_stage(job_id, "transcribe", 0.0, "Loading Whisper speech model...")

            whisper_model_name = cfg.get("ai", {}).get("whisper_model", "small")
            transcriber = VideoTranscriber(model_size=whisper_model_name)

            def transcribe_cb(pct, msg):
                self.update_stage(job_id, "transcribe", pct, msg)

            segments = transcriber.transcribe(source_path, total_duration, progress_callback=transcribe_cb)
            self.update_stage(job_id, "transcribe", 100.0, "Speech transcription complete", stage_status="completed")

            # STAGE 4: AI Highlights & Clip Selection
            self.update_stage(job_id, "highlights", 0.0, "Analyzing transcript moments...")
            ollama_host = cfg.get("ai", {}).get("ollama_host", "http://127.0.0.1:11434")
            ollama_model = cfg.get("ai", {}).get("ollama_model", "qwen2.5:7b")
            selector = ClipSelector(ollama_host=ollama_host, ollama_model=ollama_model)

            def highlights_cb(pct, msg):
                self.update_stage(job_id, "highlights", pct, msg)

            candidate_clips = selector.select_clips(
                transcript_segments=segments,
                target_count=num_clips,
                min_duration=min_dur,
                max_duration=max_dur,
                mode=selection_mode,
                custom_prompt=custom_prompt,
                progress_callback=highlights_cb
            )
            self.update_stage(job_id, "highlights", 100.0, f"Selected {len(candidate_clips)} moments", stage_status="completed")

            if not candidate_clips:
                raise RuntimeError("No suitable standalone moments found matching duration and context criteria.")

            # STAGE 5 & 6: Smart Crop & Sequential Rendering
            cropper = SmartCropper(smoothing_factor=0.15, deadband_px=25)
            rendered_clips = []
            total_clips_to_render = len(candidate_clips)

            for i, cand in enumerate(candidate_clips, start=1):
                clip_id = f"clip_{i:02d}"
                clip_filename = f"{video_id}_{clip_id}.mp4"
                output_clip_path = OUTPUT_DIR / clip_filename

                # 5. Subject Tracking
                self.update_stage(
                    job_id, "subjects",
                    round((i - 1) / total_clips_to_render * 100.0, 1),
                    f"Tracking subject for Clip {i}/{total_clips_to_render}..."
                )
                
                crop_info = cropper.calculate_crop_trajectory(
                    video_path=source_path,
                    start_time=cand["start"],
                    end_time=cand["end"],
                    source_width=video_info["width"],
                    source_height=video_info["height"],
                    target_aspect_ratio=9.0 / 16.0 if output_format == "9:16" else 1.0
                )

                # Optional captions
                subtitles_path = None
                if captions_enabled:
                    subtitles_path = TEMP_DIR / f"{video_id}_{clip_id}.ass"
                    generate_ass_subtitles(
                        segments=segments,
                        clip_start=cand["start"],
                        clip_end=cand["end"],
                        output_ass_path=subtitles_path
                    )

                # 6. Render Clip
                self.update_stage(
                    job_id, "render",
                    round((i - 1) / total_clips_to_render * 100.0, 1),
                    f"Rendering Clip {i}/{total_clips_to_render}: '{cand['title']}'..."
                )

                def render_cb(pct, msg):
                    base_pct = ((i - 1) / total_clips_to_render) * 100.0
                    current_clip_pct = (pct / total_clips_to_render)
                    self.update_stage(job_id, "render", base_pct + current_clip_pct, msg)

                prefer_nvenc = cfg.get("hardware", {}).get("prefer_nvenc", True)

                render_clip(
                    source_video_path=source_path,
                    output_clip_path=output_clip_path,
                    start_time=cand["start"],
                    end_time=cand["end"],
                    crop_info=crop_info,
                    source_fps=video_info["fps"],
                    source_width=video_info["width"],
                    source_height=video_info["height"],
                    output_format=output_format,
                    subtitles_ass_path=subtitles_path,
                    prefer_nvenc=prefer_nvenc,
                    progress_callback=render_cb
                )

                # Cleanup temp subtitle file
                if subtitles_path and subtitles_path.exists():
                    try:
                        subtitles_path.unlink()
                    except Exception:
                        pass

                clip_data = {
                    "id": clip_id,
                    "filename": clip_filename,
                    "title": cand["title"],
                    "reason": cand["reason"],
                    "score": cand["score"],
                    "duration": cand["duration"],
                    "start": cand["start"],
                    "end": cand["end"],
                    "format": output_format,
                    "file_path": str(output_clip_path),
                    "file_size_mb": round(output_clip_path.stat().st_size / (1024 * 1024), 2)
                }
                rendered_clips.append(clip_data)

                with self.lock:
                    self.jobs[job_id]["clips"] = list(rendered_clips)

            self.update_stage(job_id, "subjects", 100.0, "Subject tracking complete", stage_status="completed")
            self.update_stage(job_id, "render", 100.0, "All clips successfully rendered", stage_status="completed")

            with self.lock:
                self.jobs[job_id]["status"] = "completed"
                self.jobs[job_id]["stage"] = "done"
                self.jobs[job_id]["progress_percent"] = 100.0
                self.jobs[job_id]["current_message"] = f"Finished! {len(rendered_clips)} clips ready."

        except Exception as e:
            print(f"[JobManager] Job {job_id} failed: {e}")
            with self.lock:
                self.jobs[job_id]["status"] = "failed"
                self.jobs[job_id]["error_message"] = str(e)
                self.jobs[job_id]["current_message"] = f"Error: {str(e)}"
