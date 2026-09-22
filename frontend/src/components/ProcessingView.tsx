"use client";

import React from "react";
import { Download, Music, FileText, Sparkles, UserCheck, Video, Loader2, AlertCircle } from "lucide-react";
import { JobStatus } from "@/types";

interface ProcessingViewProps {
  job: JobStatus;
}

export const ProcessingView: React.FC<ProcessingViewProps> = ({ job }) => {
  const stages = [
    { key: "download", label: "Downloading video", icon: Download, info: job.stages.download },
    { key: "audio", label: "Extracting audio", icon: Music, info: job.stages.audio },
    { key: "transcribe", label: "Transcribing speech", icon: FileText, info: job.stages.transcribe },
    { key: "highlights", label: "Finding highlights", icon: Sparkles, info: job.stages.highlights },
    { key: "subjects", label: "Analyzing subjects", icon: UserCheck, info: job.stages.subjects },
    { key: "render", label: "Rendering clips", icon: Video, info: job.stages.render },
  ];

  return (
    <div className="w-full max-w-3xl mx-auto my-8 glass-panel rounded-2xl p-6 sm:p-8 border border-surface-border shadow-2xl space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-surface-border">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <Loader2 className="w-5 h-5 text-primary animate-spin" />
            <span>Processing Your Video</span>
          </h2>
          <p className="text-xs text-zinc-400 mt-1">
            Running local AI pipeline (CUDA / NVENC accelerated)
          </p>
        </div>
        <div className="text-right">
          <span className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent-cyan font-mono">
            {Math.round(job.progress_percent)}%
          </span>
          <span className="text-[10px] text-zinc-500 uppercase block font-semibold">Overall</span>
        </div>
      </div>

      {/* Granular Stage Progress Bars */}
      <div className="space-y-4">
        {stages.map((stg) => {
          const Icon = stg.icon;
          const pct = Math.min(100, Math.max(0, stg.info.percent));
          const isDone = pct >= 100 || stg.info.status === "completed";
          const isActive = !isDone && pct > 0;

          return (
            <div key={stg.key} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2">
                  <Icon
                    className={`w-4 h-4 ${
                      isDone
                        ? "text-emerald-400"
                        : isActive
                        ? "text-primary animate-pulse"
                        : "text-zinc-600"
                    }`}
                  />
                  <span className={`font-medium ${isDone ? "text-zinc-200" : isActive ? "text-white font-semibold" : "text-zinc-500"}`}>
                    {stg.label}
                  </span>
                </div>
                <div className="flex items-center space-x-2 font-mono">
                  <span className="text-zinc-400 text-[11px] truncate max-w-[200px] hidden sm:inline">
                    {stg.info.message}
                  </span>
                  <span className={`text-xs ${isDone ? "text-emerald-400 font-bold" : isActive ? "text-primary font-bold" : "text-zinc-600"}`}>
                    {Math.round(pct)}%
                  </span>
                </div>
              </div>

              {/* Progress track */}
              <div className="w-full h-2 rounded-full bg-surface-border overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    isDone
                      ? "bg-emerald-500"
                      : isActive
                      ? "bg-gradient-to-r from-primary to-accent-cyan"
                      : "bg-transparent"
                  }`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Live Log Message */}
      <div className="p-3.5 rounded-xl bg-background/90 border border-surface-border text-xs flex items-center justify-between">
        <span className="text-zinc-400 truncate mr-2">
          Current Activity: <span className="text-zinc-200 font-mono">{job.current_message}</span>
        </span>
        <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-primary/20 text-primary border border-primary/30 flex-shrink-0">
          Stage: {job.stage}
        </span>
      </div>

      {job.error_message && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{job.error_message}</span>
        </div>
      )}
    </div>
  );
};
