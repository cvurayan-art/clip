# Local AI Video Clipper — Crayo-Style Personal App

A high-performance, fully local AI video clipping platform engineered for Windows with NVIDIA GPU acceleration. Inspired by the workflow of modern clipping apps like Crayo and OpusClip, but runs 100% locally on your machine with **zero paid APIs, zero monthly subscriptions, and zero watermarks**.

---

## Hardware Optimization

Designed and optimized specifically for personal workstations:
- **NVIDIA GPU**: 8 GB VRAM
- **System Memory**: 16 GB RAM
- **Operating System**: Windows 10 / 11 (64-bit)

### Acceleration Highlights
- **NVIDIA CUDA**: Automatically powers `faster-whisper` speech transcription.
- **NVIDIA NVENC (`h264_nvenc`)**: Quality-focused hardware video encoding (`-preset p5 -cq 19`).
- **Smart Resource Management**: Processes renders sequentially to ensure VRAM stays well within 8 GB limits.
- **Graceful Fallbacks**: If running on a machine without an NVIDIA GPU, seamlessly transitions to CPU (`libx264` + CPU Whisper).

---

## Core Features

1. **Highest-Quality Download**: Leverages `yt-dlp` to fetch the highest compatible video and audio stream (`bv*+ba/b`). Never artificially degrades or repeatedly re-encodes source files.
2. **AI Speech Transcription**: Word-level and segment-level timestamps powered locally by `faster-whisper` (`small` or `medium` model).
3. **Local AI Highlight Detection**:
   - Integrates with local **Ollama** (`qwen2.5:7b` / `llama3.1:8b`).
   - Includes a built-in **8-factor NLP scoring engine** (Hook, Information, Emotion, Standalone, Retention, Ending, Context, Quality) that operates offline even if Ollama is not installed.
4. **Smart 9:16 Subject Tracking**:
   - Never blindly crops the center of videos.
   - Detects speaker faces and active motion using OpenCV.
   - Uses an **Exponential Moving Average (EMA) and deadband filter** to deliver smooth, cinematic camera panning without jitter.
5. **Semantic Diversity Filtering**:
   - Compares candidate moments with Jaccard n-gram and temporal overlap checks.
   - Prevents duplicate or redundant clips when generating 5, 10, or 20 clips.
6. **Natural Timestamp Snapping**:
   - Expands or shrinks boundaries around sentence pauses so speech never cuts off mid-word.
   - Features optional hook lead-in context extensions.
7. **Optional Styled Captions**:
   - **Default: OFF** (strictly no text burned in unless requested).
   - When enabled, burns clean, modern vertical video subtitles (ASS format).
8. **Real Stage Progress**:
   - Real-time progress tracking across all 6 pipeline stages (Download, Audio, Transcribe, Highlights, Tracking, Render).
9. **Zero Watermarks**: Clean, pristine MP4 exports saved directly to `/output/`.

---

## Directory Structure

```
ai-clipper/
│
├── frontend/             # Next.js 14 + TypeScript + Tailwind CSS
├── backend/              # Python FastAPI Application
│   ├── app/
│   │   ├── main.py       # API endpoints, streaming & jobs
│   │   ├── config.py     # Configuration & storage paths
│   │   ├── hardware.py   # GPU, VRAM, CUDA, NVENC, RAM diagnostics
│   │   ├── downloader.py # yt-dlp metadata & highest-quality download
│   │   ├── transcriber.py# faster-whisper CUDA transcription
│   │   ├── selector.py   # Ollama / Qwen & 8-factor scoring engine
│   │   ├── cropper.py    # OpenCV face & smooth 9:16 camera tracking
│   │   ├── renderer.py   # Single-pass NVENC / CPU FFmpeg renderer
│   │   ├── captions.py   # Optional ASS styled subtitles
│   │   └── jobs.py       # Background queue & stage progress manager
│   └── requirements.txt  # Python backend dependencies
├── models/               # Local AI model weights cache
├── downloads/            # Downloaded original source videos
├── temp/                 # Temporary working files (auto-cleaned)
├── output/               # Rendered final MP4 clips
├── scripts/              # Environment verification & diagnostic utilities
├── config/               # Configuration settings (settings.json)
├── install.bat           # Automated one-click installer
├── start.bat             # One-click dual-server launcher
└── README.md             # Documentation
```

---

## Prerequisites & Installation

### 1. Prerequisites Checklist
Make sure the following tools are installed on your Windows PC:

| Software | Recommended Version | Download Link / Command |
|---|---|---|
| **Python** | 3.10 or 3.11 | [python.org/downloads](https://www.python.org/downloads/) *(Check "Add to PATH")* |
| **Node.js** | 18 LTS or 20 LTS | [nodejs.org](https://nodejs.org/) |
| **FFmpeg** | Latest Build | `winget install Gyan.FFmpeg` or [gyan.dev/ffmpeg](https://www.gyan.dev/ffmpeg/builds/) |
| **Ollama** *(Optional)* | Latest | [ollama.ai](https://ollama.ai/) *(Run: `ollama pull qwen2.5:7b`)* |

### 2. Automated Installation
Simply double-click:
```bat
install.bat
```
This script will:
- Check for Python, Node.js, and FFmpeg.
- Create a Python virtual environment (`.venv`).
- Install all backend dependencies (`fastapi`, `faster-whisper`, `yt-dlp`, `opencv-python-headless`, etc.).
- Install Next.js frontend dependencies (`npm install`).

---

## Running the Application

Double-click:
```bat
start.bat
```
This will:
1. Activate the Python virtual environment.
2. Launch the FastAPI backend server on `http://127.0.0.1:8000`.
3. Launch the Next.js frontend server on `http://localhost:3000`.
4. Automatically open your browser to `http://localhost:3000`.

---

## End-to-End User Workflow

1. **Input**: Paste a public YouTube video URL (e.g. `https://www.youtube.com/watch?v=...`) and click **Analyze Video**.
2. **Review Video Metadata**: View confirmed title, source duration, resolution (e.g. `1920x1080`), and FPS (`30 FPS` or `60 FPS`).
3. **Configure Clips**:
   - **Clips Count**: `1`, `3`, `5`, `10`, `15`, `20`, or Custom.
   - **Duration**: `15–30s`, `30–45s`, `30–60s`, `60–90s`, or Custom min/max.
   - **Selection Mode**: `Best Overall`, `Most Viral`, `Most Informative`, `Funniest`, or `Custom`.
   - **Format**: `9:16 Vertical` (Default), `16:9`, `1:1`, `4:5`.
   - **Captions**: `OFF` (Default) or `Automatic Captions`.
4. **Click GENERATE CLIPS**:
   - Watch live progress bars for Download, Audio, Transcription, Highlights, Subject Tracking, and Rendering.
5. **Results & Export**:
   - Preview generated clips instantly in the integrated vertical video player.
   - Inspect AI viral score badges (e.g., `94/100`) and reasoning summaries.
   - Click **Download MP4** for individual clips, or **Download All (ZIP)**.
   - Click **Open Folder** to view exported files directly in Windows File Explorer.

---

## Verifying Environment & Running Tests

To verify your hardware and pipeline without launching the UI:

```powershell
# Check hardware, CUDA, NVENC, and RAM
python scripts/check_env.py

# Run complete automated integration tests
python scripts/test_pipeline.py
```

---

## License

This software is an independent implementation created for personal use. It does not contain proprietary code, assets, or algorithms from commercial platforms.
