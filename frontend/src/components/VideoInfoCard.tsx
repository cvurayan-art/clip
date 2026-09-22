"use client";

import React from "react";
import { Clock, Monitor, Film, User, CheckCircle2 } from "lucide-react";
import { VideoMetadata } from "@/types";

interface VideoInfoCardProps {
  metadata: VideoMetadata;
  onChangeVideo: () => void;
}

export const VideoInfoCard: React.FC<VideoInfoCardProps> = ({ metadata, onChangeVideo }) => {
  return (
    <div className="w-full glass-panel rounded-2xl p-5 border border-surface-border shadow-xl mb-6">
      <div className="flex flex-col md:flex-row gap-5 items-start md:items-center">
        {/* Thumbnail Preview */}
        <div className="relative w-full md:w-56 h-32 rounded-xl overflow-hidden bg-black/60 flex-shrink-0 border border-surface-border">
          {metadata.thumbnail ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={metadata.thumbnail}
              alt={metadata.title}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-zinc-600">
              <Film className="w-8 h-8" />
            </div>
          )}
          <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-black/80 backdrop-blur-sm text-[11px] font-mono text-white">
            {metadata.duration_str}
          </div>
        </div>

        {/* Video Details */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Video Verified & Ready</span>
          </div>

          <h3 className="text-lg font-bold text-white line-clamp-2 mb-2" title={metadata.title}>
            {metadata.title}
          </h3>

          <div className="flex flex-wrap gap-3 text-xs text-zinc-400">
            {metadata.channel && (
              <div className="flex items-center space-x-1.5 bg-surface/80 px-2.5 py-1 rounded-md border border-surface-border">
                <User className="w-3.5 h-3.5 text-zinc-400" />
                <span className="truncate max-w-[140px]">{metadata.channel}</span>
              </div>
            )}
            <div className="flex items-center space-x-1.5 bg-surface/80 px-2.5 py-1 rounded-md border border-surface-border">
              <Clock className="w-3.5 h-3.5 text-zinc-400" />
              <span>{metadata.duration_str}</span>
            </div>
            <div className="flex items-center space-x-1.5 bg-surface/80 px-2.5 py-1 rounded-md border border-surface-border">
              <Monitor className="w-3.5 h-3.5 text-accent-cyan" />
              <span>{metadata.resolution}</span>
            </div>
            <div className="flex items-center space-x-1.5 bg-surface/80 px-2.5 py-1 rounded-md border border-surface-border">
              <Film className="w-3.5 h-3.5 text-accent-violet" />
              <span>{metadata.fps} FPS</span>
            </div>
          </div>
        </div>

        {/* Switch / Reset Action */}
        <div className="flex-shrink-0 self-end md:self-center">
          <button
            onClick={onChangeVideo}
            className="text-xs text-zinc-400 hover:text-white px-3 py-1.5 rounded-lg border border-surface-border hover:bg-surface-hover transition-colors"
          >
            Change Video
          </button>
        </div>
      </div>
    </div>
  );
};
