import { useCallback, useRef } from "react";
import { useEditorStore } from "@/stores/editor-store";

export function useAudioPlayer() {
  const audioContextRef = useRef<AudioContext | null>(null);
  const { isPlaying, setPlaying, setCurrentTime } = useEditorStore();

  const getAudioContext = useCallback(() => {
    if (!audioContextRef.current) {
      audioContextRef.current = new AudioContext();
    }
    return audioContextRef.current;
  }, []);

  const play = useCallback(() => {
    const ctx = getAudioContext();
    if (ctx.state === "suspended") {
      ctx.resume();
    }
    setPlaying(true);
  }, [getAudioContext, setPlaying]);

  const pause = useCallback(() => {
    setPlaying(false);
  }, [setPlaying]);

  const seek = useCallback(
    (time: number) => {
      setCurrentTime(time);
    },
    [setCurrentTime]
  );

  return { isPlaying, play, pause, seek, getAudioContext };
}
