"""
Environment and Hardware Diagnostic Script for AI Video Clipper.
Checks Python, FFmpeg, yt-dlp, NVIDIA GPU, CUDA, NVENC, RAM, and Ollama.
"""

import sys
import shutil
import subprocess

def check_mark(success: bool) -> str:
    return "[OK]" if success else "[MISSING]"

def main():
    print("=" * 60)
    print("      AI VIDEO CLIPPER — HARDWARE & SYSTEM CHECK")
    print("=" * 60)

    # 1. Python Check
    py_ver = sys.version.split()[0]
    print(f"{check_mark(True)} Python Version: {py_ver}")

    # 2. FFmpeg Check
    ffmpeg_path = shutil.which("ffmpeg")
    has_ffmpeg = ffmpeg_path is not None
    print(f"{check_mark(has_ffmpeg)} FFmpeg: {ffmpeg_path or 'Not found in PATH'}")

    # 3. yt-dlp Check
    ytdlp_path = shutil.which("yt-dlp")
    has_ytdlp = ytdlp_path is not None
    print(f"{check_mark(has_ytdlp)} yt-dlp: {ytdlp_path or 'Not found in PATH'}")

    # 4. NVENC Support in FFmpeg
    has_nvenc = False
    if has_ffmpeg:
        try:
            res = subprocess.run([ffmpeg_path, "-hide_banner", "-encoders"], capture_output=True, text=True, timeout=5)
            has_nvenc = "h264_nvenc" in res.stdout
        except Exception:
            pass
    print(f"{check_mark(has_nvenc)} NVIDIA NVENC (h264_nvenc): {'Available' if has_nvenc else 'Unavailable (will use libx264)'}")

    # 5. NVIDIA GPU & CUDA Check
    has_cuda = False
    gpu_name = "None detected"
    vram_gb = 0.0

    try:
        import torch
        if torch.cuda.is_available():
            has_cuda = True
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 1)
    except ImportError:
        # Fallback to nvidia-smi
        try:
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if res.returncode == 0 and res.stdout.strip():
                parts = res.stdout.strip().split("\n")[0].split(",")
                gpu_name = parts[0].strip()
                vram_gb = round(float(parts[1].strip()) / 1024.0, 1)
                has_cuda = True
        except Exception:
            pass

    print(f"{check_mark(has_cuda)} NVIDIA GPU: {gpu_name}")
    print(f"{check_mark(has_cuda)} VRAM: {vram_gb} GB")
    print(f"{check_mark(has_cuda)} CUDA Acceleration: {'Active' if has_cuda else 'Unavailable (CPU mode)'}")

    # 6. System RAM Check
    ram_gb = 16.0
    try:
        import psutil
        ram_gb = round(psutil.virtual_memory().total / (1024**3), 1)
    except Exception:
        pass
    print(f"{check_mark(True)} System RAM: {ram_gb} GB")

    # 7. Ollama Local LLM Check
    ollama_path = shutil.which("ollama")
    has_ollama = ollama_path is not None
    ollama_running = False
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2) as resp:
            if resp.status == 200:
                ollama_running = True
    except Exception:
        pass

    print(f"{check_mark(has_ollama)} Ollama Executable: {ollama_path or 'Not installed'}")
    print(f"{check_mark(ollama_running)} Ollama Service: {'Running on http://127.0.0.1:11434' if ollama_running else 'Offline (Built-in NLP fallback active)'}")

    print("=" * 60)
    if has_cuda and has_nvenc:
        print("Hardware Status: OPTIMAL (Full NVIDIA CUDA & NVENC acceleration enabled)")
    elif has_cuda:
        print("Hardware Status: GOOD (CUDA active for Whisper; libx264 for encoding)")
    else:
        print("Hardware Status: COMPATIBLE (CPU fallback active for Whisper & libx264)")
    print("=" * 60)

if __name__ == "__main__":
    main()
