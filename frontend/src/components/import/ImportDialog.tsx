import { useCallback, useRef, useState } from "react";
import { Film, Music, Upload, X } from "lucide-react";

import { useSyncStore } from "@/stores/sync-store";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function ImportDialog({ onClose }: { onClose: () => void }) {
  const {
    videoInfo,
    stemFiles,
    setVideoInfo,
    addStem,
    removeStem,
    setSyncStatus,
    setSyncProgress,
    setSyncResults,
  } = useSyncStore();

  const [uploading, setUploading] = useState(false);
  const videoInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);

  const handleVideoUpload = useCallback(
    async (file: File) => {
      setUploading(true);
      try {
        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch(`${API_BASE}/api/video/upload`, {
          method: "POST",
          body: formData,
        });

        if (!res.ok) throw new Error("Video upload failed");
        const data = await res.json();
        const url = URL.createObjectURL(file);
        setVideoInfo(data, url);
      } finally {
        setUploading(false);
      }
    },
    [setVideoInfo]
  );

  const handleStemUpload = useCallback(
    async (files: FileList) => {
      setUploading(true);
      try {
        for (const file of Array.from(files)) {
          const formData = new FormData();
          formData.append("file", file);

          const res = await fetch(`${API_BASE}/api/stems/upload`, {
            method: "POST",
            body: formData,
          });

          if (!res.ok) throw new Error(`Stem upload failed: ${file.name}`);
          const data = await res.json();
          addStem(data.stem_id, data.filename);
        }
      } finally {
        setUploading(false);
      }
    },
    [addStem]
  );

  const handleAnalyze = useCallback(async () => {
    if (!videoInfo || stemFiles.length === 0) return;

    setSyncStatus("analyzing");
    setSyncProgress(0);

    try {
      const res = await fetch(`${API_BASE}/api/sync/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_id: videoInfo.video_id,
          stem_ids: stemFiles.map((s) => s.stemId),
        }),
      });

      if (!res.ok) throw new Error("Sync analysis failed");
      const data = await res.json();
      setSyncResults(data);
    } catch {
      setSyncStatus("failed");
    }
  }, [videoInfo, stemFiles, setSyncStatus, setSyncProgress, setSyncResults]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-lg rounded-xl bg-editor-surface p-6 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Import & Sync</h2>
          <button
            onClick={onClose}
            className="rounded p-1 hover:bg-editor-bg"
          >
            <X size={18} />
          </button>
        </div>

        <div className="space-y-4">
          {/* Video Upload */}
          <div
            className="cursor-pointer rounded-lg border-2 border-dashed border-editor-muted/30 p-4 transition hover:border-editor-accent/50"
            onClick={() => videoInputRef.current?.click()}
          >
            <input
              ref={videoInputRef}
              type="file"
              accept="video/*"
              className="hidden"
              onChange={(e) => {
                if (e.target.files?.[0]) handleVideoUpload(e.target.files[0]);
              }}
            />
            <div className="flex items-center gap-3">
              <Film size={24} className="text-editor-accent" />
              <div>
                <p className="font-medium">
                  {videoInfo ? videoInfo.filename : "Upload Video"}
                </p>
                <p className="text-xs text-editor-muted">
                  {videoInfo
                    ? `${videoInfo.duration_s.toFixed(1)}s · ${videoInfo.width}×${videoInfo.height}`
                    : "MP4, MOV, MKV"}
                </p>
              </div>
            </div>
          </div>

          {/* Audio Stems Upload */}
          <div
            className="cursor-pointer rounded-lg border-2 border-dashed border-editor-muted/30 p-4 transition hover:border-editor-waveform/50"
            onClick={() => audioInputRef.current?.click()}
          >
            <input
              ref={audioInputRef}
              type="file"
              accept="audio/*"
              multiple
              className="hidden"
              onChange={(e) => {
                if (e.target.files) handleStemUpload(e.target.files);
              }}
            />
            <div className="flex items-center gap-3">
              <Music size={24} className="text-editor-waveform" />
              <div>
                <p className="font-medium">Upload Audio Stems</p>
                <p className="text-xs text-editor-muted">
                  WAV files from Pro Tools (multiple)
                </p>
              </div>
            </div>
          </div>

          {/* Stem List */}
          {stemFiles.length > 0 && (
            <div className="space-y-1">
              {stemFiles.map((stem) => (
                <div
                  key={stem.stemId}
                  className="flex items-center justify-between rounded bg-editor-bg px-3 py-1.5 text-sm"
                >
                  <span>{stem.filename}</span>
                  <button
                    onClick={() => removeStem(stem.stemId)}
                    className="text-editor-muted hover:text-editor-accent"
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Analyze Button */}
          <button
            onClick={handleAnalyze}
            disabled={!videoInfo || stemFiles.length === 0 || uploading}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-editor-accent px-4 py-2.5 font-medium text-white transition hover:bg-editor-accent/80 disabled:opacity-40"
          >
            <Upload size={18} />
            Analyze & Sync
          </button>
        </div>
      </div>
    </div>
  );
}
