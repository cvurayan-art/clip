import os
from pathlib import Path
from typing import List, Dict, Any

def format_ass_timestamp(seconds: float) -> str:
    """Formats seconds into ASS timestamp format: H:MM:SS.cc"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"

def generate_ass_subtitles(
    segments: List[Dict[str, Any]],
    clip_start: float,
    clip_end: float,
    output_ass_path: Path,
    font_name: str = "Arial",
    font_size: int = 22,
    primary_color: str = "&H00FFFFFF",      # White
    highlight_color: str = "&H0000D4FF",    # Amber/Gold
    outline_color: str = "&H00000000",      # Black outline
    outline_width: int = 3
) -> Path:
    """
    Generates modern, high-retention styled ASS subtitles for vertical video.
    Aligns text relative to clip_start (00:00:00.00).
    """
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary_color},{highlight_color},{outline_color},&H64000000,-1,0,0,0,100,100,0,0,1,{outline_width},2,2,40,40,240,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    dialogue_lines = []

    for seg in segments:
        seg_start = seg.get("start", 0.0)
        seg_end = seg.get("end", 0.0)

        # Check overlap with clip
        if seg_end <= clip_start or seg_start >= clip_end:
            continue

        rel_start = max(0.0, seg_start - clip_start)
        rel_end = max(rel_start + 0.5, min(clip_end - clip_start, seg_end - clip_start))

        start_str = format_ass_timestamp(rel_start)
        end_str = format_ass_timestamp(rel_end)

        # Clean text
        raw_text = seg.get("text", "").strip().upper()
        if not raw_text:
            continue

        # Break text into short, punchy 3-5 word lines for vertical video
        words = raw_text.split()
        chunks = []
        for i in range(0, len(words), 4):
            chunks.append(" ".join(words[i:i + 4]))
        formatted_text = r"\N".join(chunks)

        dialogue_lines.append(
            f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{formatted_text}"
        )

    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(dialogue_lines) + "\n")

    return output_ass_path
