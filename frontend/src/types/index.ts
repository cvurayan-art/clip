export interface VideoMetadata {
  id: string;
  title: string;
  duration: number;
  duration_str: string;
  width: number;
  height: number;
  resolution: string;
  fps: number;
  thumbnail: string;
  channel: string;
  url: string;
}

export interface HardwareStatus {
  gpu: string;
  vram_gb: number;
  cuda_available: boolean;
  nvenc_available: boolean;
  ram_gb: number;
  recommended_video_encoder: string;
  recommended_whisper_device: string;
}

export interface ClipSettingsState {
  num_clips: number;
  min_duration: number;
  max_duration: number;
  selection_mode: "Best Overall" | "Most Viral" | "Most Informative" | "Funniest" | "Custom";
  custom_prompt?: string;
  output_format: "9:16" | "16:9" | "1:1" | "4:5";
  captions_enabled: boolean;
}

export interface ClipResult {
  id: string;
  filename: string;
  title: string;
  reason: string;
  score: number;
  duration: number;
  start: number;
  end: number;
  format: string;
  file_path: string;
  file_size_mb: number;
}

export interface StageInfo {
  percent: number;
  status: "pending" | "in_progress" | "completed";
  message: string;
}

export interface JobStatus {
  id: string;
  status: "queued" | "processing" | "completed" | "failed";
  stage: string;
  progress_percent: number;
  current_message: string;
  stages: {
    download: StageInfo;
    audio: StageInfo;
    transcribe: StageInfo;
    highlights: StageInfo;
    subjects: StageInfo;
    render: StageInfo;
  };
  clips: ClipResult[];
  error_message?: string;
}
