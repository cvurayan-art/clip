"use client";

import React, { useState } from "react";
import { Download, FolderOpen, Play, CheckCircle2, RotateCcw, Sparkles } from "lucide-react";
import { ClipResult } from "@/types";

interface ResultsGridProps {
  clips: ClipResult[];
  jobId: string;
  onReset: () => void;
  onOpenFolder: () => void;
  apiBaseUrl?: string;
}

export const ResultsGrid: React.FC<ResultsGridProps> = ({
  clips,
  jobId,
  onReset,
  onOpenFolder,
  apiBaseUrl = "http://127.0.0.1:8000",
}) => {
  const [activeClip, setActiveClip] = useState<ClipResult | null>(clips[0] || null);

  const getScoreColor = (score: number) => {
    if (score >= 90) return "text-emerald-400 bg-emerald-500/10 border-emerald-500/30";
    if (score >= 80) return "text-cyan-400 bg-cyan-500/10 border-cyan-500/30";
    return "text-amber-400 bg-amber-500/10 border-amber-500/30";
  };

  return (
    <div className="w-full max-w-7xl mx-auto my-8 px-4 space-y-8">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 glass-panel p-6 rounded-2xl border border-surface-border">
        <div>
          <div className="flex items-center space-x-2 text-emerald-400 text-xs font-bold uppercase tracking-wider mb-1">
            <CheckCircle2 className="w-4 h-4" />
            <span>Generation Complete</span>
          </div>
          <h2 className="text-2xl font-black text-white">
            {clips.length} Standalone Clips Ready
          </h2>
          <p className="text-xs text-zinc-400">
            Files rendered locally in high quality (9:16 vertical format).
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={onOpenFolder}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-surface border border-surface-border hover:border-zinc-500 text-zinc-200 transition-colors"
          >
            <FolderOpen className="w-4 h-4" />
            <span>Open Folder</span>
          </button>

          <a
            href={`${apiBaseUrl}/api/jobs/${jobId}/download-all`}
            download
            className="flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-primary to-accent-violet hover:opacity-90 text-white shadow-lg shadow-primary/25 transition-all"
          >
            <Download className="w-4 h-4" />
            <span>Download All (ZIP)</span>
          </a>

          <button
            onClick={onReset}
            className="p-2.5 rounded-xl bg-surface border border-surface-border text-zinc-400 hover:text-white transition-colors"
            title="Clip Another Video"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Grid + Video Player Spotlight */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Focused Player (sticky) */}
        {activeClip && (
          <div className="lg:col-span-5 glass-panel p-6 rounded-2xl border border-surface-border sticky top-24 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-surface-border">
              <span className="text-xs font-bold uppercase tracking-wider text-zinc-400">
                Live Player Preview
              </span>
              <span
                className={`text-xs px-2.5 py-0.5 rounded-full font-mono font-bold border ${getScoreColor(
                  activeClip.score
                )}`}
              >
                Score: {activeClip.score}/100
              </span>
            </div>

            {/* Video Container (Aspect 9:16) */}
            <div className="relative w-full max-w-[280px] mx-auto aspect-[9/16] bg-black rounded-xl overflow-hidden border border-surface-border shadow-2xl">
              <video
                key={activeClip.filename}
                src={`${apiBaseUrl}/api/clips/${activeClip.filename}/file`}
                controls
                autoPlay
                playsInline
                className="w-full h-full object-contain"
              />
            </div>

            <div>
              <h3 className="font-bold text-white text-base mb-1">{activeClip.title}</h3>
              <p className="text-xs text-zinc-300 italic mb-3 bg-surface/80 p-3 rounded-lg border border-surface-border">
                &ldquo;{activeClip.reason}&rdquo;
              </p>
              <div className="flex items-center justify-between text-xs text-zinc-400">
                <span>Duration: {activeClip.duration}s</span>
                <span>Size: {activeClip.file_size_mb} MB</span>
                <a
                  href={`${apiBaseUrl}/api/clips/${activeClip.filename}/download`}
                  download={activeClip.filename}
                  className="text-primary hover:underline font-semibold flex items-center space-x-1"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download MP4</span>
                </a>
              </div>
            </div>
          </div>
        )}

        {/* Right Column: Cards Grid */}
        <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-4">
          {clips.map((clip, index) => {
            const isSelected = activeClip?.id === clip.id;
            return (
              <div
                key={clip.id}
                onClick={() => setActiveClip(clip)}
                className={`cursor-pointer glass-panel p-5 rounded-2xl border transition-all duration-200 space-y-3 ${
                  isSelected
                    ? "border-primary ring-2 ring-primary/40 bg-surface/90 shadow-xl"
                    : "border-surface-border hover:border-zinc-600 hover:bg-surface/70"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-extrabold uppercase tracking-wider text-primary">
                    CLIP {String(index + 1).padStart(2, "0")}
                  </span>
                  <span
                    className={`text-[11px] px-2 py-0.5 rounded-full font-mono font-bold border ${getScoreColor(
                      clip.score
                    )}`}
                  >
                    {clip.score}/100
                  </span>
                </div>

                <h4 className="font-bold text-sm text-white line-clamp-1">{clip.title}</h4>

                <p className="text-xs text-zinc-400 line-clamp-2">{clip.reason}</p>

                <div className="flex items-center justify-between pt-2 border-t border-surface-border text-xs text-zinc-500">
                  <span>{clip.duration}s</span>
                  <div className="flex items-center space-x-2 text-zinc-300">
                    <span className="flex items-center space-x-1 hover:text-white">
                      <Play className="w-3 h-3 fill-current" />
                      <span>Preview</span>
                    </span>
                    <span>•</span>
                    <a
                      href={`${apiBaseUrl}/api/clips/${clip.filename}/download`}
                      download={clip.filename}
                      onClick={(e) => e.stopPropagation()}
                      className="hover:text-primary transition-colors"
                      title="Download MP4"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
