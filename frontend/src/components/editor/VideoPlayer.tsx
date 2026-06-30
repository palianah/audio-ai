import { useCallback, useEffect, useRef } from "react";

import { useEditorStore } from "@/stores/editor-store";
import { useSyncStore } from "@/stores/sync-store";

export function VideoPlayer() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const { currentTime, isPlaying, setCurrentTime, setDuration } =
    useEditorStore();
  const { videoUrl } = useSyncStore();

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const onLoaded = () => {
      setDuration(video.duration);
    };
    video.addEventListener("loadedmetadata", onLoaded);
    return () => video.removeEventListener("loadedmetadata", onLoaded);
  }, [setDuration]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    if (isPlaying) {
      video.play();
    } else {
      video.pause();
    }
  }, [isPlaying]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    if (Math.abs(video.currentTime - currentTime) > 0.1) {
      video.currentTime = currentTime;
    }
  }, [currentTime]);

  const handleTimeUpdate = useCallback(() => {
    const video = videoRef.current;
    if (video && isPlaying) {
      setCurrentTime(video.currentTime);
    }
  }, [isPlaying, setCurrentTime]);

  if (!videoUrl) {
    return (
      <div className="flex h-full items-center justify-center rounded-lg border border-dashed border-editor-muted/30 bg-editor-surface/50">
        <p className="text-sm text-editor-muted">No video loaded</p>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden rounded-lg bg-black">
      <video
        ref={videoRef}
        src={videoUrl}
        className="h-full w-full object-contain"
        onTimeUpdate={handleTimeUpdate}
        preload="metadata"
      />
    </div>
  );
}
