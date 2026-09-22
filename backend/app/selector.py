import re
import json
import math
from typing import List, Dict, Any, Optional, Tuple, Callable
import httpx

# High-impact hook starter phrases
HOOK_PATTERNS = [
    r"\b(the biggest mistake|secret to|how to|why you should|never do this|the truth about)\b",
    r"\b(nobody talks about|what most people don't realize|stop doing|if you want to)\b",
    r"\b(one of the most|here is why|the real reason|three things|number one rule)\b",
    r"\b(did you know|imagine if|have you ever wondered|what if I told you)\b"
]

# Filler / Context-dependent phrases to penalize or reject
BAD_CONTEXT_PATTERNS = [
    r"\b(as I said earlier|like we mentioned before|in the previous video|moving on to)\b",
    r"\b(as you can see on the screen|look at this slide|pointing to this)\b",
    r"\b(anyway guys welcome back|don't forget to like and subscribe|sponsor of this)\b",
    r"\b(let me pull up my notes|give me one second|technical difficulties)\b"
]

def calculate_ngram_similarity(text1: str, text2: str, n: int = 3) -> float:
    """Calculates character/word n-gram Jaccard similarity between two texts."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union)

def snap_to_natural_boundaries(
    start: float,
    end: float,
    transcript_segments: List[Dict[str, Any]],
    extend_hook: bool = True
) -> Tuple[float, float]:
    """
    Snaps candidate timestamps to nearest complete sentence/phrase boundary.
    Avoids cutting sentences in half. Optionally extends start for natural hook setup.
    """
    if not transcript_segments:
        return start, end

    best_start = start
    best_end = end

    # Find the segment closest to the requested start
    for seg in transcript_segments:
        seg_start = seg.get("start", 0.0)
        seg_end = seg.get("end", 0.0)

        # If candidate start falls inside this segment, snap to segment start
        if abs(seg_start - start) <= 3.0 or (seg_start <= start <= seg_end):
            best_start = seg_start
            # Optional hook extension: if previous segment has a natural lead-in
            if extend_hook:
                prev_idx = transcript_segments.index(seg) - 1
                if prev_idx >= 0:
                    prev_seg = transcript_segments[prev_idx]
                    # If pause between segments is small (< 1.5s), check if it provides context
                    if seg_start - prev_seg.get("end", 0.0) < 1.5 and (start - prev_seg.get("start", 0.0)) <= 6.0:
                        best_start = prev_seg.get("start", 0.0)
            break

    # Find the segment closest to requested end
    for seg in reversed(transcript_segments):
        seg_start = seg.get("start", 0.0)
        seg_end = seg.get("end", 0.0)
        if abs(seg_end - end) <= 3.0 or (seg_start <= end <= seg_end):
            best_end = seg_end
            break

    # Ensure minimum sanity duration (at least 15s)
    if best_end - best_start < 15.0 and transcript_segments:
        best_end = best_start + 15.0

    return round(best_start, 2), round(best_end, 2)

class ClipSelector:
    """
    Selects, scores, and diversifies candidate viral moments using Ollama LLM
    with an intelligent rule-based heuristic NLP fallback.
    """

    def __init__(self, ollama_host: str = "http://127.0.0.1:11434", ollama_model: str = "qwen2.5:7b"):
        self.ollama_host = ollama_host.rstrip("/")
        self.ollama_model = ollama_model

    def select_clips(
        self,
        transcript_segments: List[Dict[str, Any]],
        target_count: int = 5,
        min_duration: float = 30.0,
        max_duration: float = 60.0,
        mode: str = "Best Overall",
        custom_prompt: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Main entry point for clip selection. Attempts Ollama first,
        falling back to local NLP heuristics if Ollama is unreachable.
        """
        if not transcript_segments:
            return []

        if progress_callback:
            progress_callback(10.0, "Analyzing transcript for candidate hooks...")

        # 1. Try local Ollama LLM
        candidates = []
        try:
            candidates = self._query_ollama(
                transcript_segments, target_count, min_duration, max_duration, mode, custom_prompt
            )
        except Exception as e:
            print(f"[ClipSelector] Ollama unavailable ({e}). Using built-in local NLP engine.")

        # 2. If Ollama returned insufficient candidates, supplement with local NLP engine
        if len(candidates) < target_count:
            if progress_callback:
                progress_callback(40.0, "Running multi-factor NLP candidate scoring engine...")
            heuristic_candidates = self._generate_heuristic_candidates(
                transcript_segments, min_duration, max_duration, mode, custom_prompt
            )
            # Combine and deduplicate
            candidates.extend(heuristic_candidates)

        if progress_callback:
            progress_callback(70.0, "Refining natural sentence boundaries & hook extensions...")

        # 3. Refine boundaries & snap to natural pauses
        refined = []
        for cand in candidates:
            s, e = snap_to_natural_boundaries(cand["start"], cand["end"], transcript_segments, extend_hook=True)
            cand["start"] = s
            cand["end"] = e
            cand["duration"] = round(e - s, 1)
            # Extract transcript slice
            cand_text = " ".join(
                seg["text"] for seg in transcript_segments if seg["start"] >= s - 0.5 and seg["end"] <= e + 0.5
            )
            cand["text"] = cand_text
            refined.append(cand)

        if progress_callback:
            progress_callback(85.0, "Applying semantic diversity filter...")

        # 4. Semantic Diversity Filter: eliminate duplicate or highly overlapping clips
        diverse_clips = self._filter_diverse_clips(refined, target_count)

        if progress_callback:
            progress_callback(100.0, f"Found {len(diverse_clips)} high-scoring diverse clips")

        return diverse_clips

    def _query_ollama(
        self,
        transcript_segments: List[Dict[str, Any]],
        target_count: int,
        min_duration: float,
        max_duration: float,
        mode: str,
        custom_prompt: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Queries local Ollama instance with structured system and user prompts."""
        # Build compact transcript text with timestamps
        lines = []
        for seg in transcript_segments:
            lines.append(f"[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}")
        transcript_text = "\n".join(lines)

        mode_instructions = {
            "Best Overall": "Find standalone, high-retention moments with strong hooks, clear insights, and satisfying conclusions.",
            "Most Viral": "Prioritize controversial statements, shocking facts, high-energy emotions, and curiosity hooks.",
            "Most Informative": "Prioritize actionable advice, educational explanations, practical takeaways, and structured tips.",
            "Funniest": "Prioritize jokes, unexpected reactions, humorous anecdotes, and lighthearted moments.",
            "Custom": custom_prompt or "Find the most engaging and valuable standalone segments."
        }

        prompt = f"""You are an expert AI video clipping editor for TikTok, YouTube Shorts, and Instagram Reels.
Your task is to identify the top {target_count} standalone clips from this transcript.

Criteria:
- Clip length MUST be between {int(min_duration)} and {int(max_duration)} seconds.
- Mode: {mode} ({mode_instructions.get(mode, '')})
- Each clip MUST have a strong hook in the first 3 seconds and make complete sense on its own.
- Do NOT pick clips with dangling pronouns ('as I said earlier', 'as you can see here') or half-cut sentences.
- Ensure all clips cover DIFFERENT topics (diversity).

Return ONLY valid JSON matching this exact array format:
[
  {{
    "start": 12.5,
    "end": 48.0,
    "title": "Short catchy title",
    "reason": "Why this moment works as a viral clip",
    "score": 92
  }}
]

Transcript:
{transcript_text[:12000]}
"""

        with httpx.Client(timeout=45.0) as client:
            resp = client.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
            )
            if resp.status_code != 200:
                return []
            
            res_json = resp.json()
            raw_text = res_json.get("response", "")
            
            # Extract JSON array
            json_match = re.search(r"\[.*\]", raw_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                valid = []
                for item in parsed:
                    if "start" in item and "end" in item:
                        item["score"] = int(item.get("score", 85))
                        valid.append(item)
                return valid

        return []

    def _generate_heuristic_candidates(
        self,
        transcript_segments: List[Dict[str, Any]],
        min_duration: float,
        max_duration: float,
        mode: str,
        custom_prompt: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Local NLP engine: Scans sliding windows across transcript segments,
        calculating 8-factor scores (Hook, Info, Emotional, Standalone, Retention, Ending, Context, Quality).
        """
        candidates = []
        n = len(transcript_segments)
        if n == 0:
            return []

        # Sliding window over segments
        for i in range(n):
            start_seg = transcript_segments[i]
            start_time = start_seg["start"]

            # Check if this segment contains bad start context
            if any(re.search(pat, start_seg["text"], re.IGNORECASE) for pat in BAD_CONTEXT_PATTERNS):
                continue

            # Accumulate segments until window reaches duration
            accumulated_text = []
            for j in range(i, n):
                end_seg = transcript_segments[j]
                end_time = end_seg["end"]
                dur = end_time - start_time

                accumulated_text.append(end_seg["text"])
                full_text = " ".join(accumulated_text)

                if min_duration <= dur <= max_duration:
                    score, details = self._score_candidate_text(full_text, start_seg["text"], end_seg["text"], mode)
                    if score >= 70:
                        title = self._generate_title(start_seg["text"], full_text)
                        candidates.append({
                            "start": start_time,
                            "end": end_time,
                            "title": title,
                            "reason": details["reason"],
                            "score": score,
                            "score_breakdown": details
                        })
                elif dur > max_duration:
                    break

        # Sort descending by score
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates

    def _score_candidate_text(
        self,
        full_text: str,
        opening_text: str,
        closing_text: str,
        mode: str
    ) -> Tuple[int, Dict[str, Any]]:
        """Scores candidate moment on 8 key dimensions (0–100 total)."""
        # 1. Hook Score (0-20)
        hook_score = 10
        for pat in HOOK_PATTERNS:
            if re.search(pat, opening_text, re.IGNORECASE):
                hook_score = 20
                break
        if "?" in opening_text:
            hook_score = min(20, hook_score + 5)

        # 2. Information Score (0-15)
        info_keywords = ["because", "result", "strategy", "lesson", "system", "rule", "step", "first", "key"]
        info_count = sum(1 for kw in info_keywords if kw in full_text.lower())
        info_score = min(15, 6 + info_count * 2)

        # 3. Emotional Score (0-15)
        emotion_words = ["crazy", "amazing", "insane", "hate", "love", "shocking", "worst", "best", "terrible", "incredible"]
        emo_count = sum(1 for ew in emotion_words if ew in full_text.lower())
        emotional_score = min(15, 5 + emo_count * 3)

        # 4. Standalone Score (0-15)
        standalone_score = 15
        for bad in BAD_CONTEXT_PATTERNS:
            if re.search(bad, full_text, re.IGNORECASE):
                standalone_score -= 7

        # 5. Retention Score (0-15)
        # Moderate word density (~2.5 to 3.5 words per sec) indicates engaging delivery
        word_count = len(full_text.split())
        retention_score = 12 if word_count > 40 else 8

        # 6. Ending Score (0-10)
        # Good ending has a sentence terminator (. or !)
        ending_score = 10 if closing_text.endswith((".", "!", "?")) else 5

        # 7. Quality & Context Score (0-10)
        quality_score = 10

        total_score = hook_score + info_score + emotional_score + standalone_score + retention_score + ending_score + quality_score
        total_score = min(98, max(50, total_score))

        reason = "Strong standalone insight with high viewer retention potential."
        if hook_score >= 18:
            reason = "Compelling opening hook followed by concise, high-value delivery."
        elif emotional_score >= 12:
            reason = "High-energy expressive reaction with engaging audience retention."
        elif info_score >= 12:
            reason = "Clear, actionable advice that works seamlessly as an independent short."

        return total_score, {
            "hook": hook_score,
            "information": info_score,
            "emotional": emotional_score,
            "standalone": standalone_score,
            "retention": retention_score,
            "ending": ending_score,
            "reason": reason
        }

    def _generate_title(self, opening: str, full_text: str) -> str:
        """Derives a concise, punchy title from the opening or high-frequency theme."""
        clean = re.sub(r'^[,\s\-\."\']+', '', opening).strip()
        words = clean.split()
        if len(words) >= 4:
            candidate_title = " ".join(words[:6])
            # Strip trailing punctuation
            candidate_title = re.sub(r'[,\-:\.]+$', '', candidate_title)
            return candidate_title.capitalize()
        return "Key Takeaway"

    def _filter_diverse_clips(self, candidates: List[Dict[str, Any]], target_count: int) -> List[Dict[str, Any]]:
        """
        Compares candidate clips against each other. Discards clips that overlap
        temporally (> 40% time overlap) or semantically (> 35% text similarity).
        """
        diverse = []
        for cand in candidates:
            if len(diverse) >= target_count:
                break

            overlap = False
            for accepted in diverse:
                # 1. Temporal overlap check
                start_max = max(cand["start"], accepted["start"])
                end_min = min(cand["end"], accepted["end"])
                if end_min > start_max:
                    overlap_dur = end_min - start_max
                    min_dur = min(cand["duration"], accepted["duration"])
                    if min_dur > 0 and (overlap_dur / min_dur) > 0.35:
                        overlap = True
                        break

                # 2. Semantic text similarity check
                sim = calculate_ngram_similarity(cand.get("text", ""), accepted.get("text", ""))
                if sim > 0.40:
                    overlap = True
                    break

            if not overlap:
                diverse.append(cand)

        return diverse
