import os
import json
from pathlib import Path
from typing import Any, Dict

# Base project directory is the parent of 'backend' -> 'ai-clipper'
BASE_DIR = Path(__file__).resolve().parent.parent.parent

CONFIG_FILE = BASE_DIR / "config" / "settings.json"
DOWNLOADS_DIR = BASE_DIR / "downloads"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"
MODELS_DIR = BASE_DIR / "models"

# Ensure all essential directories exist
for folder in [DOWNLOADS_DIR, OUTPUT_DIR, TEMP_DIR, MODELS_DIR, BASE_DIR / "config"]:
    folder.mkdir(parents=True, exist_ok=True)

DEFAULT_SETTINGS: Dict[str, Any] = {
    "storage": {
        "downloads_dir": str(DOWNLOADS_DIR),
        "output_dir": str(OUTPUT_DIR),
        "temp_dir": str(TEMP_DIR),
        "models_dir": str(MODELS_DIR),
    },
    "hardware": {
        "prefer_cuda": True,
        "prefer_nvenc": True,
        "max_concurrent_renders": 1,
    },
    "ai": {
        "prefer_youtube_captions": True,
        "whisper_model": "small",
        "whisper_device": "auto",
        "ollama_host": "http://127.0.0.1:11434",
        "ollama_model": "qwen2.5:7b",
    },
    "video": {
        "default_format": "9:16",
        "output_resolution": "1080x1920",
        "output_quality": "High",
        "codec": "auto",
        "captions_default": False,
        "captions_font_size": 24,
        "captions_font_color": "&H00FFFFFF",
        "captions_highlight_color": "&H0000FFFF",
    },
    "clips": {
        "default_count": 5,
        "default_min_duration": 30,
        "default_max_duration": 60,
        "default_style": "Best Overall",
    },
}

def load_settings() -> Dict[str, Any]:
    """Loads configuration settings from disk or creates default if missing."""
    if not CONFIG_FILE.exists():
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Merge with default settings to ensure all keys exist
            merged = DEFAULT_SETTINGS.copy()
            for section, values in data.items():
                if isinstance(values, dict) and section in merged:
                    merged[section].update(values)
                else:
                    merged[section] = values
            return merged
    except Exception as e:
        print(f"Warning: Failed to parse settings.json ({e}). Using defaults.")
        return DEFAULT_SETTINGS.copy()

def save_settings(settings: Dict[str, Any]) -> bool:
    """Saves settings dictionary to JSON file."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False
