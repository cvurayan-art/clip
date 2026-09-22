"use client";

import React, { useState } from "react";
import { Youtube, Search, AlertCircle, Loader2 } from "lucide-react";

interface UrlInputProps {
  onAnalyze: (url: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export const UrlInput: React.FC<UrlInputProps> = ({ onAnalyze, isLoading, error }) => {
  const [url, setUrl] = useState("");
  const [localValidationErr, setLocalValidationErr] = useState<string | null>(null);

  const isValidYoutubeUrl = (testUrl: string): boolean => {
    const pattern = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)[a-zA-Z0-9_-]{11}(&.*)?$/;
    return pattern.test(testUrl.trim());
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLocalValidationErr(null);

    const cleanUrl = url.trim();
    if (!cleanUrl) {
      setLocalValidationErr("Please enter a YouTube video URL.");
      return;
    }

    if (!isValidYoutubeUrl(cleanUrl)) {
      setLocalValidationErr("Please enter a valid YouTube video URL (e.g. https://www.youtube.com/watch?v=...)");
      return;
    }

    onAnalyze(cleanUrl);
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setUrl(text);
        setLocalValidationErr(null);
      }
    } catch {
      // Clipboard read blocked
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto my-12 px-4">
      <div className="text-center mb-8">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white mb-3">
          Turn Any Video Into Viral Shorts
        </h1>
        <p className="text-base sm:text-lg text-zinc-400 max-w-xl mx-auto">
          Local Crayo-style AI clipper. Powered by local Whisper and Qwen models with smart 9:16 subject tracking.
        </p>
      </div>

      <div className="glass-panel p-6 sm:p-8 rounded-2xl shadow-2xl relative overflow-hidden">
        {/* Subtle accent glow in background */}
        <div className="absolute -top-24 -left-24 w-48 h-48 bg-primary/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-accent-cyan/20 rounded-full blur-3xl pointer-events-none" />

        <form onSubmit={handleSubmit} className="space-y-4 relative z-10">
          <div>
            <label htmlFor="yt-url-input" className="block text-sm font-semibold text-zinc-200 mb-2">
              Paste YouTube URL
            </label>
            <div className="relative flex items-center">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                <Youtube className="h-5 w-5 text-red-500" />
              </div>
              <input
                id="yt-url-input"
                type="text"
                value={url}
                onChange={(e) => {
                  setUrl(e.target.value);
                  if (localValidationErr) setLocalValidationErr(null);
                }}
                placeholder="https://www.youtube.com/watch?v=XXXXXXXXXXX"
                disabled={isLoading}
                className="block w-full pl-11 pr-24 py-3.5 bg-background/80 border border-surface-border rounded-xl text-white placeholder-zinc-500 text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
              />
              <button
                type="button"
                onClick={handlePaste}
                className="absolute right-2 px-3 py-1.5 text-xs font-medium text-zinc-400 hover:text-white bg-surface hover:bg-surface-hover rounded-lg border border-surface-border transition-colors"
              >
                Paste
              </button>
            </div>
          </div>

          {(localValidationErr || error) && (
            <div className="flex items-center space-x-2 text-rose-400 text-xs py-2 px-3 bg-rose-500/10 border border-rose-500/20 rounded-lg">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{localValidationErr || error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading || !url.trim()}
            className="w-full flex items-center justify-center space-x-2 py-3.5 px-6 rounded-xl font-semibold text-white bg-gradient-to-r from-primary to-accent-violet hover:from-primary-hover hover:to-primary disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-primary/25 transition-all duration-200"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Analyzing Video Stream & Metadata...</span>
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                <span>Analyze Video</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
