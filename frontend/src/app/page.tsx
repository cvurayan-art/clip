"use client";

import React, { useState, useEffect, useRef } from "react";
import { Header } from "@/components/Header";
import { UrlInput } from "@/components/UrlInput";
import { VideoInfoCard } from "@/components/VideoInfoCard";
import { ClipSettings } from "@/components/ClipSettings";
import { ProcessingView } from "@/components/ProcessingView";
import { ResultsGrid } from "@/components/ResultsGrid";
import { SettingsModal } from "@/components/SettingsModal";
import { VideoMetadata, HardwareStatus, ClipSettingsState, JobStatus } from "@/types";

export default function Home() {
  const [apiBaseUrl, setApiBaseUrl] = useState<string>("http://127.0.0.1:8000");
  const [hardware, setHardware] = useState<HardwareStatus | null>(null);
  const [appSettings, setAppSettings] = useState<any>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Workflow states: 'input' -> 'configured' -> 'processing' -> 'results'
  const [currentStep, setCurrentStep] = useState<"input" | "configured" | "processing" | "results">("input");

  const [metadata, setMetadata] = useState<VideoMetadata | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);

  const [clipSettings, setClipSettings] = useState<ClipSettingsState>({
    num_clips: 5,
    min_duration: 30,
    max_duration: 60,
    selection_mode: "Best Overall",
    output_format: "9:16",
    captions_enabled: false,
  });

  const [currentJob, setCurrentJob] = useState<JobStatus | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // 1. Initialize API URL from env or localStorage
  useEffect(() => {
    const savedUrl = localStorage.getItem("ai_clipper_api_url");
    const initialUrl = savedUrl || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    setApiBaseUrl(initialUrl);
  }, []);

  // 2. Fetch hardware status & initial settings whenever apiBaseUrl changes
  useEffect(() => {
    if (!apiBaseUrl) return;
    const fetchSystemInfo = async () => {
      try {
        const cleanBase = apiBaseUrl.replace(/\/+$/, "");
        const [hwRes, setRes] = await Promise.all([
          fetch(`${cleanBase}/api/hardware`),
          fetch(`${cleanBase}/api/settings`),
        ]);
        if (hwRes.ok) setHardware(await hwRes.json());
        if (setRes.ok) {
          const s = await setRes.json();
          setAppSettings(s);
          if (s.clips) {
            setClipSettings((prev) => ({
              ...prev,
              num_clips: s.clips.default_count || 5,
              min_duration: s.clips.default_min_duration || 30,
              max_duration: s.clips.default_max_duration || 60,
              selection_mode: s.clips.default_style || "Best Overall",
            }));
          }
        }
      } catch {
        console.warn(`Backend API not reachable at ${apiBaseUrl}`);
      }
    };
    fetchSystemInfo();
  }, [apiBaseUrl]);

  // 3. Poll job status during processing
  useEffect(() => {
    if (currentStep === "processing" && currentJob?.id) {
      pollIntervalRef.current = setInterval(async () => {
        try {
          const cleanBase = apiBaseUrl.replace(/\/+$/, "");
          const res = await fetch(`${cleanBase}/api/jobs/${currentJob.id}`);
          if (res.ok) {
            const data: JobStatus = await res.json();
            setCurrentJob(data);

            if (data.status === "completed") {
              if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
              setCurrentStep("results");
            } else if (data.status === "failed") {
              if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
            }
          }
        } catch (err) {
          console.error("Job polling error:", err);
        }
      }, 1000);
    }

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [currentStep, currentJob?.id, apiBaseUrl]);

  // Handler: Analyze YouTube URL
  const handleAnalyze = async (url: string) => {
    setIsAnalyzing(true);
    setAnalyzeError(null);
    try {
      const cleanBase = apiBaseUrl.replace(/\/+$/, "");
      const res = await fetch(`${cleanBase}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to analyze video.");
      }
      setMetadata(data);
      setCurrentStep("configured");
    } catch (err: any) {
      setAnalyzeError(err.message || `Cannot connect to backend at ${apiBaseUrl}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Handler: Start Clip Generation
  const handleGenerateClips = async () => {
    if (!metadata) return;

    try {
      const cleanBase = apiBaseUrl.replace(/\/+$/, "");
      const res = await fetch(`${cleanBase}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_info: metadata,
          ...clipSettings,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to start clipping job.");

      setCurrentJob({
        id: data.job_id,
        status: "processing",
        stage: "download",
        progress_percent: 2.0,
        current_message: "Starting video download...",
        stages: {
          download: { percent: 5.0, status: "in_progress", message: "Starting yt-dlp download..." },
          audio: { percent: 0.0, status: "pending", message: "Pending..." },
          transcribe: { percent: 0.0, status: "pending", message: "Pending..." },
          highlights: { percent: 0.0, status: "pending", message: "Pending..." },
          subjects: { percent: 0.0, status: "pending", message: "Pending..." },
          render: { percent: 0.0, status: "pending", message: "Pending..." },
        },
        clips: [],
      });

      setCurrentStep("processing");
    } catch (err: any) {
      alert(`Error starting job: ${err.message}`);
    }
  };

  // Handler: Save settings
  const handleSaveSettings = async (newSettings: any, newApiUrl?: string) => {
    if (newApiUrl && newApiUrl !== apiBaseUrl) {
      setApiBaseUrl(newApiUrl);
      localStorage.setItem("ai_clipper_api_url", newApiUrl);
    }
    try {
      const cleanBase = (newApiUrl || apiBaseUrl).replace(/\/+$/, "");
      const res = await fetch(`${cleanBase}/api/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ settings: newSettings }),
      });
      if (res.ok) {
        setAppSettings(newSettings);
      }
    } catch {
      // Offline / URL changed
    }
  };

  // Handler: Open output folder in Windows Explorer
  const handleOpenFolder = async () => {
    try {
      const cleanBase = apiBaseUrl.replace(/\/+$/, "");
      await fetch(`${cleanBase}/api/open-folder`, { method: "POST" });
    } catch (err) {
      console.error("Open folder error:", err);
    }
  };

  // Handler: Reset to analyze another video
  const handleReset = () => {
    setCurrentStep("input");
    setMetadata(null);
    setCurrentJob(null);
    setAnalyzeError(null);
  };

  return (
    <main className="min-h-screen flex flex-col justify-between">
      <Header hardware={hardware} onOpenSettings={() => setIsSettingsOpen(true)} />

      <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Step 1: Input URL */}
        {currentStep === "input" && (
          <UrlInput
            onAnalyze={handleAnalyze}
            isLoading={isAnalyzing}
            error={analyzeError}
          />
        )}

        {/* Step 2: Configured (Metadata Card + Settings Form) */}
        {currentStep === "configured" && metadata && (
          <div className="max-w-4xl mx-auto space-y-6">
            <VideoInfoCard
              metadata={metadata}
              onChangeVideo={handleReset}
            />
            <ClipSettings
              settings={clipSettings}
              onChange={setClipSettings}
              onGenerate={handleGenerateClips}
              isGenerating={false}
            />
          </div>
        )}

        {/* Step 3: Real Stage Processing Screen */}
        {currentStep === "processing" && currentJob && (
          <ProcessingView job={currentJob} />
        )}

        {/* Step 4: Results Screen */}
        {currentStep === "results" && currentJob && (
          <ResultsGrid
            clips={currentJob.clips}
            jobId={currentJob.id}
            onReset={handleReset}
            onOpenFolder={handleOpenFolder}
            apiBaseUrl={apiBaseUrl}
          />
        )}
      </div>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        hardware={hardware}
        settings={appSettings}
        apiUrl={apiBaseUrl}
        onSaveSettings={handleSaveSettings}
      />

      {/* Footer */}
      <footer className="w-full border-t border-surface-border py-4 text-center text-xs text-zinc-500">
        <div className="flex flex-col sm:flex-row items-center justify-center gap-2">
          <span>AI Clipper • Local & Privacy-Focused • NVIDIA CUDA & NVENC</span>
          <span className="hidden sm:inline">•</span>
          <span className="font-mono text-zinc-400">Connected: {apiBaseUrl}</span>
        </div>
      </footer>
    </main>
  );
}
