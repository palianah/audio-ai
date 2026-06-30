import { useCallback, useEffect, useRef } from "react";

import { useEditorStore } from "@/stores/editor-store";
import { useSyncStore } from "@/stores/sync-store";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function VideoPlayer() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const { currentTime, isPlaying, setCurrentTime, setDuration, setPlaying } =
    useEditorStore();
  const { videoUrl, videoInfo, appliedStemUrls, applyTimestamp } =
    useSyncStore();

  const hasApplied = Object.keys(appliedStemUrls).length > 0;
  const previewUrl =
    hasApplied && videoInfo
      ? `${API_BASE}/api/sync/preview/${videoInfo.video_id}?t=${applyTimestamp}`
      : null;

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const onLoaded = () => setDuration(video.duration);
    const onEnded = () => setPlaying(false);
    video.addEventListener("loadedmetadata", onLoaded);
    video.addEventListener("ended", onEnded);
    return () => {
      video.removeEventListener("loadedmetadata", onLoaded);
      video.removeEventListener("ended", onEnded);
    };
  }, [setDuration, setPlaying]);

  useEffect(() => {
    const video = videoRef.current;
    const audio = audioRef.current;
    if (!video) return;

    if (isPlaying) {
      const t = video.currentTime;
      video.play().catch(() => {});
      if (audio && previewUrl) {
        audio.currentTime = t;
        audio.play().catch(() => {});
      }
    } else {
      video.pause();
      if (audio) audio.pause();
    }
  }, [isPlaying, previewUrl]);

  useEffect(() => {
    const video = videoRef.current;
    const audio = audioRef.current;
    if (!video) return;

    if (Math.abs(video.currentTime - currentTime) > 0.2) {
      video.currentTime = currentTime;
      if (audio) audio.currentTime = currentTime;
    }
  }, [currentTime]);

  const handleTimeUpdate = useCallback(() => {
    const video = videoRef.current;
    if (video && isPlaying) {
      setCurrentTime(video.currentTime);
    }
  }, [isPlaying, setCurrentTime]);

  const handleVideoClick = useCallback(() => {
    setPlaying(!isPlaying);
  }, [isPlaying, setPlaying]);

  if (!videoUrl) {
    return (
      <div className="flex h-full items-center justify-center rounded-lg border border-dashed border-editor-muted/30 bg-editor-surface/50">
        <p className="text-sm text-editor-muted">No video loaded</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      <div className="relative overflow-hidden rounded-t-lg bg-black">
        <video
          ref={videoRef}
          src={videoUrl}
          className="h-full w-full cursor-pointer object-contain"
          onTimeUpdate={handleTimeUpdate}
          onClick={handleVideoClick}
          preload="auto"
        />
        {hasApplied && (
          <div className="absolute bottom-1 right-1 rounded bg-editor-waveform/80 px-1.5 py-0.5 text-[9px] font-medium text-black">
            🔊 Synced
          </div>
        )}
      </div>
      {previewUrl && (
        <div className="rounded-b-lg bg-editor-surface/80 px-2 py-1">
          <p className="mb-1 text-[10px] text-editor-muted">Synced Audio</p>
          <audio
            ref={audioRef}
            src={previewUrl}
            controls
            preload="auto"
            className="h-7 w-full"
          />
        </div>
      )}
    </div>
  );
}
