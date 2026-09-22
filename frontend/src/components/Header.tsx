"use client";

import React from "react";
import { Sparkles, Settings, Cpu, HardDrive } from "lucide-react";
import { HardwareStatus } from "@/types";

interface HeaderProps {
  hardware: HardwareStatus | null;
  onOpenSettings: () => void;
}

export const Header: React.FC<HeaderProps> = ({ hardware, onOpenSettings }) => {
  return (
    <header className="w-full border-b border-surface-border bg-surface/50 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-primary to-accent-violet flex items-center justify-center shadow-lg shadow-primary/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-lg tracking-wider text-white">AI CLIPPER</span>
              <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-primary/20 text-primary border border-primary/30">
                Local
              </span>
            </div>
          </div>
        </div>

        {/* Hardware Status & Settings Button */}
        <div className="flex items-center space-x-3">
          {hardware && (
            <div className="hidden md:flex items-center space-x-2 text-xs bg-surface px-3 py-1.5 rounded-lg border border-surface-border">
              <Cpu className="w-3.5 h-3.5 text-accent-cyan" />
              <span className="text-zinc-300 font-medium">
                {hardware.cuda_available ? (
                  <span className="text-emerald-400">NVIDIA CUDA ({hardware.vram_gb} GB)</span>
                ) : (
                  <span className="text-zinc-400">CPU Mode</span>
                )}
              </span>
              <span className="text-zinc-600">•</span>
              <span className="text-zinc-300 font-medium">
                {hardware.nvenc_available ? (
                  <span className="text-accent-cyan">NVENC Active</span>
                ) : (
                  <span className="text-zinc-400">x264 Active</span>
                )}
              </span>
            </div>
          )}

          <button
            onClick={onOpenSettings}
            className="p-2 rounded-lg bg-surface border border-surface-border hover:border-primary/50 text-zinc-400 hover:text-white transition-all duration-200"
            title="System & AI Settings"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
