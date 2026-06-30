import { useCallback, useEffect, useRef, useState } from "react";

import { useEditorStore } from "@/stores/editor-store";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const TRACK_COLORS = [
  "#53d769",
  "#5ac8fa",
  "#ff9500",
  "#ff2d55",
  "#af52de",
  "#ffcc00",
];

interface WaveformTrackProps {
  stemId: string;
  label: string;
  index: number;
  synced?: boolean;
  videoId?: string;
}

interface PeakData {
  duration_s: number;
  peaks: [number, number][];
}

export function WaveformTrack({
  stemId,
  label,
  index,
  synced = false,
  videoId = "",
}: WaveformTrackProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [peaks, setPeaks] = useState<PeakData | null>(null);
  const { currentTime, duration } = useEditorStore();
  const color = TRACK_COLORS[index % TRACK_COLORS.length];

  useEffect(() => {
    const params = new URLSearchParams({ points: "1000" });
    if (synced && videoId) {
      params.set("synced", "true");
      params.set("video_id", videoId);
    }

    fetch(`${API_BASE}/api/waveform/${stemId}?${params}`)
      .then((r) => r.json())
      .then((data: PeakData) => setPeaks(data))
      .catch(() => setPeaks(null));
  }, [stemId, synced, videoId]);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !peaks) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    const mid = h / 2;

    ctx.clearRect(0, 0, w, h);

    ctx.fillStyle = "#16213e";
    ctx.fillRect(0, 0, w, h);

    const pointWidth = w / peaks.peaks.length;

    peaks.peaks.forEach(([min, max], i) => {
      const x = i * pointWidth;
      const top = mid + min * mid * 0.9;
      const bottom = mid + max * mid * 0.9;

      ctx.fillStyle = color;
      ctx.globalAlpha = 0.8;
      ctx.fillRect(x, top, Math.max(pointWidth - 0.5, 1), bottom - top);
    });

    ctx.globalAlpha = 1;

    if (duration > 0) {
      const playX = (currentTime / duration) * w;
      ctx.strokeStyle = "#e94560";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(playX, 0);
      ctx.lineTo(playX, h);
      ctx.stroke();
    }
  }, [peaks, currentTime, duration, color]);

  useEffect(() => {
    draw();
  }, [draw]);

  useEffect(() => {
    const observer = new ResizeObserver(() => draw());
    if (canvasRef.current) observer.observe(canvasRef.current);
    return () => observer.disconnect();
  }, [draw]);

  return (
    <div className="flex border-b border-editor-surface">
      {/* Track header */}
      <div className="flex w-32 flex-shrink-0 flex-col justify-center border-r border-editor-surface px-2 py-1">
        <div className="flex items-center gap-1.5">
          <div
            className="h-2.5 w-2.5 rounded-full"
            style={{ backgroundColor: color }}
          />
          <span className="truncate text-xs font-medium">{label}</span>
        </div>
        {peaks && (
          <span className="mt-0.5 text-[10px] text-editor-muted">
            {peaks.duration_s.toFixed(1)}s
          </span>
        )}
      </div>

      {/* Waveform canvas */}
      <div className="flex-1">
        <canvas
          ref={canvasRef}
          className="h-16 w-full cursor-crosshair"
        />
      </div>
    </div>
  );
}
