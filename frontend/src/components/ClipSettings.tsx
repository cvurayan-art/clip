"use client";

import React, { useState } from "react";
import { Sparkles, Sliders, Type, Smartphone, Compass, Clock, Play } from "lucide-react";
import { ClipSettingsState } from "@/types";

interface ClipSettingsProps {
  settings: ClipSettingsState;
  onChange: (settings: ClipSettingsState) => void;
  onGenerate: () => void;
  isGenerating: boolean;
}

const CLIP_COUNT_OPTIONS = [1, 3, 5, 10, 15, 20];
const DURATION_PRESETS = [
  { label: "15–30 sec", min: 15, max: 30 },
  { label: "30–45 sec", min: 30, max: 45 },
  { label: "30–60 sec", min: 30, max: 60 },
  { label: "60–90 sec", min: 60, max: 90 },
];

export const ClipSettings: React.FC<ClipSettingsProps> = ({
  settings,
  onChange,
  onGenerate,
  isGenerating,
}) => {
  const [isCustomCount, setIsCustomCount] = useState(
    !CLIP_COUNT_OPTIONS.includes(settings.num_clips)
  );
  const [isCustomDuration, setIsCustomDuration] = useState(false);

  return (
    <div className="w-full glass-panel rounded-2xl p-6 sm:p-8 border border-surface-border shadow-2xl space-y-8">
      <div className="flex items-center space-x-2.5 pb-4 border-b border-surface-border">
        <Sliders className="w-5 h-5 text-primary" />
        <h2 className="text-xl font-bold text-white">Clip Generation Settings</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* 1. Number of Clips */}
        <div className="space-y-3">
          <label className="text-sm font-semibold text-zinc-200 flex items-center justify-between">
            <span>Number of Clips</span>
            <span className="text-xs font-mono text-primary font-bold">
              Generate: {settings.num_clips} {settings.num_clips === 1 ? "clip" : "clips"}
            </span>
          </label>
          <div className="flex flex-wrap gap-2">
            {CLIP_COUNT_OPTIONS.map((count) => (
              <button
                key={count}
                type="button"
                onClick={() => {
                  setIsCustomCount(false);
                  onChange({ ...settings, num_clips: count });
                }}
                className={`px-3.5 py-2 rounded-xl text-sm font-medium border transition-all ${
                  !isCustomCount && settings.num_clips === count
                    ? "bg-primary text-white border-primary shadow-lg shadow-primary/20"
                    : "bg-surface/80 border-surface-border text-zinc-300 hover:border-zinc-500"
                }`}
              >
                {count}
              </button>
            ))}
            <button
              type="button"
              onClick={() => setIsCustomCount(true)}
              className={`px-3.5 py-2 rounded-xl text-sm font-medium border transition-all ${
                isCustomCount
                  ? "bg-primary text-white border-primary shadow-lg shadow-primary/20"
                  : "bg-surface/80 border-surface-border text-zinc-300 hover:border-zinc-500"
              }`}
            >
              Custom
            </button>
          </div>
          {isCustomCount && (
            <div className="pt-2">
              <input
                type="number"
                min={1}
                max={30}
                value={settings.num_clips}
                onChange={(e) =>
                  onChange({ ...settings, num_clips: Math.max(1, parseInt(e.target.value) || 1) })
                }
                className="w-32 px-3 py-1.5 bg-background border border-surface-border rounded-lg text-white text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
          )}
        </div>

        {/* 2. Clip Duration */}
        <div className="space-y-3">
          <label className="text-sm font-semibold text-zinc-200 flex items-center justify-between">
            <span className="flex items-center space-x-1.5">
              <Clock className="w-4 h-4 text-zinc-400" />
              <span>Clip Duration</span>
            </span>
            <span className="text-xs font-mono text-zinc-400">
              {settings.min_duration}s – {settings.max_duration}s
            </span>
          </label>
          <div className="flex flex-wrap gap-2">
            {DURATION_PRESETS.map((preset) => {
              const active =
                !isCustomDuration &&
                settings.min_duration === preset.min &&
                settings.max_duration === preset.max;
              return (
                <button
                  key={preset.label}
                  type="button"
                  onClick={() => {
                    setIsCustomDuration(false);
                    onChange({
                      ...settings,
                      min_duration: preset.min,
                      max_duration: preset.max,
                    });
                  }}
                  className={`px-3 py-2 rounded-xl text-xs sm:text-sm font-medium border transition-all ${
                    active
                      ? "bg-primary text-white border-primary shadow-lg shadow-primary/20"
                      : "bg-surface/80 border-surface-border text-zinc-300 hover:border-zinc-500"
                  }`}
                >
                  {preset.label}
                </button>
              );
            })}
            <button
              type="button"
              onClick={() => setIsCustomDuration(true)}
              className={`px-3 py-2 rounded-xl text-xs sm:text-sm font-medium border transition-all ${
                isCustomDuration
                  ? "bg-primary text-white border-primary shadow-lg shadow-primary/20"
                  : "bg-surface/80 border-surface-border text-zinc-300 hover:border-zinc-500"
              }`}
            >
              Custom
            </button>
          </div>
          {isCustomDuration && (
            <div className="flex items-center space-x-3 pt-2">
              <div className="flex items-center space-x-1">
                <span className="text-xs text-zinc-400">Min:</span>
                <input
                  type="number"
                  min={10}
                  max={120}
                  value={settings.min_duration}
                  onChange={(e) =>
                    onChange({
                      ...settings,
                      min_duration: Math.max(10, parseInt(e.target.value) || 10),
                    })
                  }
                  className="w-20 px-2.5 py-1 bg-background border border-surface-border rounded-lg text-white text-xs"
                />
              </div>
              <div className="flex items-center space-x-1">
                <span className="text-xs text-zinc-400">Max:</span>
                <input
                  type="number"
                  min={15}
                  max={180}
                  value={settings.max_duration}
                  onChange={(e) =>
                    onChange({
                      ...settings,
                      max_duration: Math.max(15, parseInt(e.target.value) || 15),
                    })
                  }
                  className="w-20 px-2.5 py-1 bg-background border border-surface-border rounded-lg text-white text-xs"
                />
              </div>
            </div>
          )}
        </div>

        {/* 3. Selection Mode */}
        <div className="space-y-3">
          <label className="text-sm font-semibold text-zinc-200 flex items-center space-x-1.5">
            <Compass className="w-4 h-4 text-zinc-400" />
            <span>AI Selection Mode</span>
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {(["Best Overall", "Most Viral", "Most Informative", "Funniest", "Custom"] as const).map(
              (mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => onChange({ ...settings, selection_mode: mode })}
                  className={`px-3 py-2 rounded-xl text-xs sm:text-sm font-medium border text-center transition-all ${
                    settings.selection_mode === mode
                      ? "bg-accent-violet text-white border-accent-violet shadow-lg shadow-accent-violet/20"
                      : "bg-surface/80 border-surface-border text-zinc-300 hover:border-zinc-500"
                  }`}
                >
                  {mode}
                </button>
              )
            )}
          </div>
          {settings.selection_mode === "Custom" && (
            <div className="pt-2">
              <input
                type="text"
                value={settings.custom_prompt || ""}
                onChange={(e) => onChange({ ...settings, custom_prompt: e.target.value })}
                placeholder="E.g. Find the most useful parts where the speaker gives business advice..."
                className="w-full px-3 py-2 bg-background border border-surface-border rounded-xl text-white text-xs placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-accent-violet"
              />
            </div>
          )}
        </div>

        {/* 4. Output Format & Captions */}
        <div className="space-y-4">
          <div>
            <label className="text-sm font-semibold text-zinc-200 flex items-center space-x-1.5 mb-2">
              <Smartphone className="w-4 h-4 text-zinc-400" />
              <span>Aspect Ratio</span>
            </label>
            <div className="flex flex-wrap gap-2">
              {(
                [
                  { id: "9:16", label: "9:16 Vertical (1080×1920)" },
                  { id: "16:9", label: "16:9 Landscape" },
                  { id: "1:1", label: "1:1 Square" },
                  { id: "4:5", label: "4:5 Portrait" },
                ] as const
              ).map((fmt) => (
                <button
                  key={fmt.id}
                  type="button"
                  onClick={() => onChange({ ...settings, output_format: fmt.id })}
                  className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${
                    settings.output_format === fmt.id
                      ? "bg-primary text-white border-primary shadow-lg shadow-primary/20"
                      : "bg-surface/80 border-surface-border text-zinc-300 hover:border-zinc-500"
                  }`}
                >
                  {fmt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Captions Toggle (Default: OFF) */}
          <div className="pt-2 border-t border-surface-border flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Type className="w-4 h-4 text-zinc-400" />
              <div>
                <span className="text-sm font-semibold text-zinc-200 block">Burn Captions</span>
                <span className="text-xs text-zinc-400">
                  {settings.captions_enabled
                    ? "Burn styled vertical captions"
                    : "No text burned in (Default: OFF)"}
                </span>
              </div>
            </div>
            <button
              type="button"
              onClick={() =>
                onChange({ ...settings, captions_enabled: !settings.captions_enabled })
              }
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.captions_enabled ? "bg-primary" : "bg-surface-border"
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.captions_enabled ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* CTA Button */}
      <div className="pt-4 border-t border-surface-border flex justify-end">
        <button
          type="button"
          onClick={onGenerate}
          disabled={isGenerating}
          className="w-full sm:w-auto px-8 py-4 rounded-xl font-bold text-white text-base bg-gradient-to-r from-primary via-accent-violet to-accent-cyan hover:opacity-95 shadow-xl shadow-primary/30 flex items-center justify-center space-x-2.5 transition-all duration-200"
        >
          <Play className="w-5 h-5 fill-current" />
          <span>GENERATE CLIPS</span>
        </button>
      </div>
    </div>
  );
};
