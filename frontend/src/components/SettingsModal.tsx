"use client";

import React, { useState } from "react";
import { X, Cpu, HardDrive, Sparkles, Sliders, CheckCircle2, Globe } from "lucide-react";
import { HardwareStatus } from "@/types";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  hardware: HardwareStatus | null;
  settings: any;
  apiUrl?: string;
  onSaveSettings: (newSettings: any, newApiUrl?: string) => Promise<void>;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  hardware,
  settings,
  apiUrl = "http://127.0.0.1:8000",
  onSaveSettings,
}) => {
  const [formData, setFormData] = useState(settings || {});
  const [customApiUrl, setCustomApiUrl] = useState(apiUrl);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSave = async () => {
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      await onSaveSettings(formData, customApiUrl.trim());
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch {
      // Handled in parent
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-2xl glass-panel bg-surface/95 border border-surface-border rounded-2xl shadow-2xl p-6 sm:p-8 space-y-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between pb-4 border-b border-surface-border">
          <div className="flex items-center space-x-2.5">
            <Sliders className="w-5 h-5 text-primary" />
            <h3 className="text-lg font-bold text-white">System & AI Settings</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-surface-hover transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 1. Remote Server / Vercel Tunnel Connection */}
        <div className="space-y-2 p-4 rounded-xl bg-background/80 border border-surface-border">
          <label className="text-xs font-bold uppercase tracking-wider text-accent-cyan flex items-center space-x-1.5">
            <Globe className="w-4 h-4" />
            <span>AI Backend Server URL (Local / Vercel / Cloudflare Tunnel)</span>
          </label>
          <p className="text-[11px] text-zinc-400">
            When deployed to Vercel, paste your Cloudflare Tunnel / Ngrok URL here to connect directly to your home GPU.
          </p>
          <input
            type="text"
            value={customApiUrl}
            onChange={(e) => setCustomApiUrl(e.target.value)}
            placeholder="http://127.0.0.1:8000 or https://your-tunnel.trycloudflare.com"
            className="w-full px-3 py-2 bg-surface border border-surface-border rounded-xl text-white text-xs font-mono focus:ring-1 focus:ring-primary"
          />
        </div>

        {/* 2. Hardware Inspection Card */}
        <div className="space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-zinc-400 block">
            Detected Hardware Acceleration
          </span>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl bg-background border border-surface-border space-y-1">
              <span className="text-[10px] text-zinc-500 uppercase font-semibold block">GPU</span>
              <span className="text-xs font-bold text-white truncate block" title={hardware?.gpu || "None"}>
                {hardware?.gpu || "Integrated"}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-background border border-surface-border space-y-1">
              <span className="text-[10px] text-zinc-500 uppercase font-semibold block">VRAM</span>
              <span className="text-xs font-bold text-accent-cyan block">
                {hardware?.vram_gb ? `${hardware.vram_gb} GB` : "Shared"}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-background border border-surface-border space-y-1">
              <span className="text-[10px] text-zinc-500 uppercase font-semibold block">CUDA</span>
              <span className={`text-xs font-bold block ${hardware?.cuda_available ? "text-emerald-400" : "text-zinc-500"}`}>
                {hardware?.cuda_available ? "Available" : "Unavailable"}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-background border border-surface-border space-y-1">
              <span className="text-[10px] text-zinc-500 uppercase font-semibold block">NVENC</span>
              <span className={`text-xs font-bold block ${hardware?.nvenc_available ? "text-accent-cyan" : "text-zinc-500"}`}>
                {hardware?.nvenc_available ? "Available" : "Unavailable (x264)"}
              </span>
            </div>
          </div>
          <div className="text-[11px] text-zinc-400 flex items-center justify-between px-1">
            <span>System RAM: <strong className="text-white">{hardware?.ram_gb || 16} GB</strong></span>
            <span>Video Encoder: <strong className="text-primary">{hardware?.recommended_video_encoder}</strong></span>
          </div>
        </div>

        {/* 3. AI Model Preferences */}
        <div className="space-y-4 pt-4 border-t border-surface-border">
          <span className="text-xs font-bold uppercase tracking-wider text-zinc-400 block">
            AI Transcription & Models
          </span>

          {/* Instant YouTube Captions Toggle (Optimal for Laptop) */}
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-background/80 border border-surface-border">
            <div>
              <span className="text-xs font-bold text-white block">
                Instant YouTube Captions (1-Sec Laptop Mode)
              </span>
              <span className="text-[11px] text-zinc-400">
                Instantly downloads existing video transcripts in 1 second. Zero CPU/GPU load.
              </span>
            </div>
            <button
              type="button"
              onClick={() =>
                setFormData({
                  ...formData,
                  ai: {
                    ...formData.ai,
                    prefer_youtube_captions: formData.ai?.prefer_youtube_captions === false ? true : false,
                  },
                })
              }
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                formData.ai?.prefer_youtube_captions !== false ? "bg-primary" : "bg-surface-border"
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  formData.ai?.prefer_youtube_captions !== false ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-zinc-300 block mb-1.5">
                faster-whisper Model Size
              </label>
              <select
                value={formData.ai?.whisper_model || "small"}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    ai: { ...formData.ai, whisper_model: e.target.value },
                  })
                }
                className="w-full px-3 py-2 bg-background border border-surface-border rounded-xl text-white text-xs focus:ring-1 focus:ring-primary"
              >
                <option value="tiny">tiny (Fastest, low VRAM)</option>
                <option value="base">base (Balanced)</option>
                <option value="small">small (Recommended for 8GB GPU)</option>
                <option value="medium">medium (High accuracy)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-zinc-300 block mb-1.5">
                Ollama LLM Model
              </label>
              <input
                type="text"
                value={formData.ai?.ollama_model || "qwen2.5:7b"}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    ai: { ...formData.ai, ollama_model: e.target.value },
                  })
                }
                placeholder="qwen2.5:7b"
                className="w-full px-3 py-2 bg-background border border-surface-border rounded-xl text-white text-xs"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-zinc-300 block mb-1.5">
              Ollama Host Endpoint
            </label>
            <input
              type="text"
              value={formData.ai?.ollama_host || "http://127.0.0.1:11434"}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  ai: { ...formData.ai, ollama_host: e.target.value },
                })
              }
              placeholder="http://127.0.0.1:11434"
              className="w-full px-3 py-2 bg-background border border-surface-border rounded-xl text-white text-xs"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-surface-border flex items-center justify-between">
          <div>
            {saveSuccess && (
              <span className="text-xs text-emerald-400 flex items-center space-x-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Settings saved!</span>
              </span>
            )}
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-zinc-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-primary hover:bg-primary-hover shadow-lg shadow-primary/20 transition-all"
            >
              {isSaving ? "Saving..." : "Save Settings"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
