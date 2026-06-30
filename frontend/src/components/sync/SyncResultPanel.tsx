import { useCallback, useRef, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  Download,
  Info,
  Pause,
  Play,
  Wand2,
} from "lucide-react";

import { useSyncStore } from "@/stores/sync-store";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const CONFIDENCE_COLORS = {
  high: "bg-green-500/20 text-green-400 border-green-500/30",
  medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  low: "bg-red-500/20 text-red-400 border-red-500/30",
} as const;

function getConfidenceLevel(c: number): keyof typeof CONFIDENCE_COLORS {
  if (c >= 0.7) return "high";
  if (c >= 0.4) return "medium";
  return "low";
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

const NOTE_ICONS = {
  info: Info,
  warning: AlertTriangle,
  error: AlertCircle,
} as const;

export function SyncResultPanel() {
  const {
    syncResults,
    syncNotes,
    syncStatus,
    updateStemOffset,
    videoInfo,
    setAppliedStemUrls,
  } = useSyncStore();
  const [applying, setApplying] = useState(false);
  const [appliedStems, setAppliedStems] = useState<Set<string>>(new Set());
  const [playingStem, setPlayingStem] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handleApply = useCallback(async () => {
    if (!videoInfo) return;
    setApplying(true);
    try {
      const res = await fetch(`${API_BASE}/api/sync/apply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_id: videoInfo.video_id,
          stem_results: syncResults,
        }),
      });
      if (!res.ok) throw new Error("Apply failed");

      const data = await res.json();
      const stemIds = Object.keys(data.output_files);
      setAppliedStems(new Set<string>(stemIds));

      const urls: Record<string, string> = {};
      for (const sid of stemIds) {
        urls[sid] = `${API_BASE}/api/sync/download/${sid}?video_id=${videoInfo.video_id}`;
      }
      setAppliedStemUrls(urls);
    } finally {
      setApplying(false);
    }
  }, [videoInfo, syncResults, setAppliedStemUrls]);

  const handlePlay = useCallback(
    (stemId: string) => {
      if (!videoInfo) return;

      if (playingStem === stemId && audioRef.current) {
        audioRef.current.pause();
        setPlayingStem(null);
        return;
      }

      if (audioRef.current) {
        audioRef.current.pause();
      }

      const url = `${API_BASE}/api/sync/download/${stemId}?video_id=${videoInfo.video_id}`;
      const audio = new Audio(url);
      audio.onended = () => setPlayingStem(null);
      audio.play();
      audioRef.current = audio;
      setPlayingStem(stemId);
    },
    [videoInfo, playingStem]
  );

  const handleDownload = useCallback(
    (stemId: string) => {
      if (!videoInfo) return;
      const url = `${API_BASE}/api/sync/download/${stemId}?video_id=${videoInfo.video_id}`;
      const a = document.createElement("a");
      a.href = url;
      a.download = `${stemId}_synced.wav`;
      a.click();
    },
    [videoInfo]
  );

  if (syncStatus !== "completed" || syncResults.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3 border-t border-editor-surface p-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Sync Results</h3>
        <button
          onClick={handleApply}
          disabled={applying}
          className="flex items-center gap-1 rounded bg-editor-waveform/20 px-2 py-1 text-[11px] font-medium text-editor-waveform transition hover:bg-editor-waveform/30 disabled:opacity-40"
        >
          {applying ? (
            <Wand2 size={12} className="animate-spin" />
          ) : (
            <Wand2 size={12} />
          )}
          {applying ? "Processing..." : appliedStems.size > 0 ? "Re-apply" : "Apply Sync"}
        </button>
      </div>

      {/* Per-stem results */}
      {syncResults.map((result) => {
        const level = getConfidenceLevel(result.overall_confidence);
        const colors = CONFIDENCE_COLORS[level];

        return (
          <div
            key={result.stem_id}
            className={`rounded-lg border p-3 ${colors}`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle size={14} />
                <span className="text-sm font-medium">
                  Stem {result.stem_id.slice(0, 6)}
                </span>
              </div>
              <span className="text-xs">
                {(result.overall_confidence * 100).toFixed(0)}% confidence
              </span>
            </div>

            <div className="mt-2 flex items-center gap-3 text-xs">
              <span>
                Offset:{" "}
                <strong>{result.offset_ms > 0 ? "+" : ""}
                  {result.offset_ms}ms
                </strong>
              </span>
              <span>
                Segments: <strong>{result.segment_maps.length}</strong>
              </span>
              {result.matched_face_id >= 0 && (
                <span>
                  Face: <strong>#{result.matched_face_id}</strong>
                </span>
              )}
            </div>

            {/* Offset adjustment */}
            <div className="mt-2">
              <label className="text-xs text-editor-muted">
                Adjust offset (ms):
              </label>
              <input
                type="range"
                min={-5000}
                max={5000}
                step={10}
                value={result.offset_ms}
                onChange={(e) =>
                  updateStemOffset(result.stem_id, Number(e.target.value))
                }
                className="mt-1 w-full accent-editor-accent"
              />
            </div>

            {/* Play / Download buttons */}
            {appliedStems.has(result.stem_id) && (
              <div className="mt-2 flex gap-2">
                <button
                  onClick={() => handlePlay(result.stem_id)}
                  className="flex flex-1 items-center justify-center gap-1 rounded bg-black/20 py-1.5 text-[11px] font-medium transition hover:bg-black/30"
                >
                  {playingStem === result.stem_id ? (
                    <><Pause size={12} /> Stop</>
                  ) : (
                    <><Play size={12} /> Preview</>
                  )}
                </button>
                <button
                  onClick={() => handleDownload(result.stem_id)}
                  className="flex flex-1 items-center justify-center gap-1 rounded bg-black/20 py-1.5 text-[11px] font-medium transition hover:bg-black/30"
                >
                  <Download size={12} /> Download
                </button>
              </div>
            )}

            {/* Segment map preview */}
            {result.segment_maps.length > 0 && (
              <div className="mt-2 space-y-0.5">
                {result.segment_maps.slice(0, 5).map((seg, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 text-[10px] opacity-70"
                  >
                    <span>
                      🎵 {formatTime(seg.audio_start_s)}–
                      {formatTime(seg.audio_end_s)}
                    </span>
                    <span>→</span>
                    <span>
                      👄 {formatTime(seg.lip_start_s)}–
                      {formatTime(seg.lip_end_s)}
                    </span>
                    <span className="rounded bg-black/20 px-1">
                      {seg.stretch_ratio.toFixed(2)}x
                    </span>
                  </div>
                ))}
                {result.segment_maps.length > 5 && (
                  <p className="text-[10px] opacity-50">
                    +{result.segment_maps.length - 5} more segments
                  </p>
                )}
              </div>
            )}
          </div>
        );
      })}

      {/* Notes */}
      {syncNotes.length > 0 && (
        <div className="space-y-1">
          <h4 className="text-xs font-semibold text-editor-muted">Notes</h4>
          {syncNotes.map((note, i) => {
            const Icon = NOTE_ICONS[note.level as keyof typeof NOTE_ICONS] || Info;
            return (
              <div
                key={i}
                className="flex items-start gap-2 rounded bg-editor-bg p-2 text-xs"
              >
                <Icon
                  size={12}
                  className={
                    note.level === "error"
                      ? "mt-0.5 text-red-400"
                      : note.level === "warning"
                        ? "mt-0.5 text-yellow-400"
                        : "mt-0.5 text-blue-400"
                  }
                />
                <div>
                  <span className="text-editor-muted">
                    [{formatTime(note.timestamp_s)}]
                  </span>{" "}
                  {note.message}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
