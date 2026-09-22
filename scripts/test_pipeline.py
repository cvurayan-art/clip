"""
Automated Pipeline Verification Test for AI Video Clipper.
Tests unit and integration flows for downloader, selector, cropper, and renderer.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.downloader import is_valid_youtube_url
from app.hardware import get_hardware_status
from app.selector import ClipSelector, calculate_ngram_similarity, snap_to_natural_boundaries
from app.cropper import SmartCropper
from app.captions import generate_ass_subtitles

def test_pipeline():
    print(">>> 1. Testing Hardware Status...")
    hw = get_hardware_status()
    print(f"    Detected GPU: {hw['gpu']}")
    print(f"    VRAM: {hw['vram_gb']} GB")
    print(f"    CUDA Available: {hw['cuda_available']}")
    print(f"    NVENC Available: {hw['nvenc_available']}")
    print(f"    System RAM: {hw['ram_gb']} GB")
    assert hw["ram_gb"] > 0, "RAM detection failed"

    print(">>> 2. Testing YouTube URL Validation...")
    valid_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtube.com/shorts/dQw4w9WgXcQ"
    ]
    invalid_urls = [
        "https://vimeo.com/12345",
        "not_a_url",
        "https://youtube.com/"
    ]
    for u in valid_urls:
        assert is_valid_youtube_url(u), f"Should be valid: {u}"
    for u in invalid_urls:
        assert not is_valid_youtube_url(u), f"Should be invalid: {u}"
    print("    URL validation passed.")

    print(">>> 3. Testing Semantic Diversity & Scoring Engine...")
    sample_segments = [
        {"id": 0, "start": 0.0, "end": 4.5, "text": "The biggest mistake people make in business is waiting too long."},
        {"id": 1, "start": 4.5, "end": 12.0, "text": "They spend six months planning an idea instead of launching in six days."},
        {"id": 2, "start": 12.0, "end": 22.0, "text": "When you launch fast, the market gives you real feedback immediately."},
        {"id": 3, "start": 22.0, "end": 35.0, "text": "That feedback is worth ten times more than your initial assumptions."},
        {"id": 4, "start": 35.0, "end": 48.0, "text": "So stop overthinking and test your hypothesis with real customers today."},
        {"id": 5, "start": 48.0, "end": 60.0, "text": "Now let's talk about completely different topic: hiring engineers."},
        {"id": 6, "start": 60.0, "end": 75.0, "text": "When hiring engineers, the number one rule is looking for curiosity."},
        {"id": 7, "start": 75.0, "end": 90.0, "text": "Curious people solve problems before they even become bottlenecks."},
        {"id": 8, "start": 90.0, "end": 105.0, "text": "That is how you build a world class team that stays resilient."},
    ]

    selector = ClipSelector()
    clips = selector.select_clips(
        transcript_segments=sample_segments,
        target_count=2,
        min_duration=20.0,
        max_duration=55.0,
        mode="Best Overall"
    )
    print(f"    Generated {len(clips)} candidate clips.")
    for i, c in enumerate(clips, 1):
        print(f"    Clip {i}: [{c['start']}s - {c['end']}s] '{c['title']}' (Score: {c['score']}/100)")
        print(f"      Reason: {c['reason']}")
    assert len(clips) >= 1, "Selector should find at least 1 clip"

    print(">>> 4. Testing Natural Boundary Snapping...")
    s, e = snap_to_natural_boundaries(2.0, 33.0, sample_segments)
    print(f"    Snapped (2.0s, 33.0s) -> ({s}s, {e}s)")
    assert s == 0.0, "Should snap to sentence start"

    print(">>> 5. Testing Smart Cropper...")
    cropper = SmartCropper()
    crop_info = cropper._default_center_crop(1920, 1080, 9.0 / 16.0)
    print(f"    9:16 Crop for 1920x1080 -> {crop_info['crop_width']}x{crop_info['crop_height']} at x={crop_info['crop_x']}")
    assert crop_info["crop_width"] == 606 or crop_info["crop_width"] == 608 or crop_info["crop_width"] == 607, "Width check"
    assert crop_info["crop_height"] == 1080, "Height check"

    print(">>> 6. Testing ASS Subtitle Generation...")
    test_ass = Path(__file__).resolve().parent.parent / "temp" / "test.ass"
    generate_ass_subtitles(
        segments=sample_segments,
        clip_start=0.0,
        clip_end=35.0,
        output_ass_path=test_ass
    )
    assert test_ass.exists() and test_ass.stat().st_size > 50, "Subtitle generation failed"
    test_ass.unlink()
    print("    ASS subtitle generated successfully.")

    print("\n" + "=" * 60)
    print("  ALL CORE PIPELINE TESTS COMPLETED AND VERIFIED!")
    print("=" * 60)

if __name__ == "__main__":
    test_pipeline()
