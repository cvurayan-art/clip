import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

from .config import TEMP_DIR, MODELS_DIR
from .hardware import detect_nvidia_gpu

def extract_audio_for_whisper(video_path: Path, output_wav: Path) -> Path:
    """Extracts 16kHz mono WAV audio required for optimal Whisper transcription."""
    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(output_wav)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {res.stderr}")
    return output_wav

class VideoTranscriber:
    """Transcribes video audio using faster-whisper with automatic CUDA/CPU detection."""

    def __init__(self, model_size: str = "small", device: str = "auto"):
        self.model_size = model_size
        self.device = device
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return self._model

        from faster_whisper import WhisperModel

        hw = detect_nvidia_gpu()
        if self.device == "auto":
            device = "cuda" if hw["cuda_available"] else "cpu"
        else:
            device = self.device

        # If on CUDA with 8GB VRAM, float16 is fast and accurate
        compute_type = "float16" if device == "cuda" else "int8"

        print(f"[Transcriber] Loading faster-whisper model '{self.model_size}' on device '{device}' ({compute_type})...")
        try:
            self._model = WhisperModel(
                self.model_size,
                device=device,
                compute_type=compute_type,
                download_root=str(MODELS_DIR)
            )
        except Exception as e:
            # Fall back to CPU int8 if CUDA fails
            print(f"[Transcriber] Device '{device}' failed ({e}). Falling back to CPU int8.")
            self._model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",
                download_root=str(MODELS_DIR)
            )

        return self._model

    def transcribe(
        self,
        video_path: Path,
        total_duration: float,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Transcribes audio from video file with word-level timestamps.
        Yields real progress updates based on timestamp processed.
        """
        model = self._load_model()
        temp_wav = TEMP_DIR / f"temp_{os.getpid()}_{video_path.stem}.wav"

        try:
            if progress_callback:
                progress_callback(5.0, "Extracting audio for speech analysis...")
            extract_audio_for_whisper(video_path, temp_wav)

            if progress_callback:
                progress_callback(10.0, f"Transcribing audio with Whisper ({self.model_size})...")

            segments, info = model.transcribe(
                str(temp_wav),
                beam_size=5,
                word_timestamps=True,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )

            result_segments = []
            dur = total_duration if total_duration > 0 else (info.duration or 60.0)

            for segment in segments:
                words_list = []
                if segment.words:
                    for w in segment.words:
                        words_list.append({
                            "word": w.word.strip(),
                            "start": round(w.start, 2),
                            "end": round(w.end, 2),
                            "probability": round(w.probability, 2)
                        })

                seg_data = {
                    "id": segment.id,
                    "start": round(segment.start, 2),
                    "end": round(segment.end, 2),
                    "text": segment.text.strip(),
                    "words": words_list
                }
                result_segments.append(seg_data)

                # Real progress update
                if progress_callback and dur > 0:
                    pct = min(99.0, 10.0 + (segment.end / dur) * 85.0)
                    progress_callback(round(pct, 1), f"Transcribing: {segment.end:.1f}s / {dur:.1f}s")

            if progress_callback:
                progress_callback(100.0, "Transcription completed successfully")

            return result_segments

        finally:
            if temp_wav.exists():
                try:
                    temp_wav.unlink()
                except Exception:
                    pass
