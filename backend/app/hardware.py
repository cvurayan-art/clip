import os
import shutil
import subprocess
from typing import Dict, Any, Optional

try:
    import psutil
except ImportError:
    psutil = None

def check_nvenc_support() -> bool:
    """Checks whether FFmpeg supports the h264_nvenc encoder on this system."""
    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
    try:
        res = subprocess.run(
            [ffmpeg_bin, "-hide_banner", "-encoders"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        return "h264_nvenc" in res.stdout
    except Exception:
        return False

def get_system_ram_gb() -> float:
    """Returns total system physical memory in GB."""
    if psutil:
        try:
            return round(psutil.virtual_memory().total / (1024 ** 3), 1)
        except Exception:
            pass
    # Windows fallback via wmic or systeminfo
    try:
        res = subprocess.run(
            ["wmic", "computersystem", "get", "totalphysicalmemory"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=3
        )
        lines = [line.strip() for line in res.stdout.splitlines() if line.strip() and line.strip().isdigit()]
        if lines:
            return round(int(lines[0]) / (1024 ** 3), 1)
    except Exception:
        pass
    return 16.0  # Reasonable default

def detect_nvidia_gpu() -> Dict[str, Any]:
    """Detects NVIDIA GPU presence, model name, VRAM, and CUDA status."""
    info = {
        "gpu_name": "None",
        "vram_gb": 0.0,
        "cuda_available": False,
        "nvenc_available": False,
    }

    # 1. Try PyTorch CUDA if installed
    try:
        import torch
        if torch.cuda.is_available():
            info["cuda_available"] = True
            info["gpu_name"] = torch.cuda.get_device_name(0)
            total_bytes = torch.cuda.get_device_properties(0).total_memory
            info["vram_gb"] = round(total_bytes / (1024 ** 3), 1)
            info["nvenc_available"] = check_nvenc_support()
            return info
    except Exception:
        pass

    # 2. Try nvidia-smi command
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if res.returncode == 0 and res.stdout.strip():
            parts = res.stdout.strip().split("\n")[0].split(",")
            if len(parts) >= 2:
                info["gpu_name"] = parts[0].strip()
                vram_mb = float(parts[1].strip())
                info["vram_gb"] = round(vram_mb / 1024.0, 1)
                info["cuda_available"] = True
                info["nvenc_available"] = check_nvenc_support()
                return info
    except Exception:
        pass

    # 3. Fallback: Query Windows WMI for Video Controllers
    try:
        res = subprocess.run(
            ["wmic", "path", "win32_VideoController", "get", "name,adapterram"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=4
        )
        if res.returncode == 0:
            lines = [l.strip() for l in res.stdout.splitlines() if l.strip()]
            for line in lines[1:]:
                if "nvidia" in line.lower():
                    parts = line.rsplit(None, 1)
                    info["gpu_name"] = parts[0] if parts else "NVIDIA GPU"
                    info["cuda_available"] = True
                    if len(parts) > 1 and parts[1].isdigit():
                        info["vram_gb"] = round(int(parts[1]) / (1024 ** 3), 1)
                    break
                elif "intel" in line.lower() and info["gpu_name"] == "None":
                    info["gpu_name"] = line
    except Exception:
        pass

    info["nvenc_available"] = check_nvenc_support()
    return info

def get_hardware_status() -> Dict[str, Any]:
    """Returns comprehensive hardware status dictionary for settings and UI."""
    gpu_data = detect_nvidia_gpu()
    ram_gb = get_system_ram_gb()
    
    # Recommended video encoder
    if gpu_data["nvenc_available"]:
        recommended_encoder = "h264_nvenc"
    else:
        recommended_encoder = "libx264"

    # Recommended whisper device
    whisper_device = "cuda" if gpu_data["cuda_available"] else "cpu"
    whisper_compute = "float16" if gpu_data["cuda_available"] else "int8"

    return {
        "gpu": gpu_data["gpu_name"],
        "vram_gb": gpu_data["vram_gb"],
        "cuda_available": gpu_data["cuda_available"],
        "nvenc_available": gpu_data["nvenc_available"],
        "ram_gb": ram_gb,
        "recommended_video_encoder": recommended_encoder,
        "recommended_whisper_device": whisper_device,
        "recommended_whisper_compute": whisper_compute,
    }
