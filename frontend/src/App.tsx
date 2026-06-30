import { useState } from "react";
import { FolderOpen, Play, Pause, SkipBack } from "lucide-react";

import { VideoPlayer } from "@/components/editor/VideoPlayer";
import { ImportDialog } from "@/components/import/ImportDialog";
import { SyncResultPanel } from "@/components/sync/SyncResultPanel";
import { useEditorStore } from "@/stores/editor-store";
import { useSyncStore } from "@/stores/sync-store";

function formatTimecode(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 100);
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}.${ms.toString().padStart(2, "0")}`;
}

export function App() {
  const [showImport, setShowImport] = useState(false);
  const { isPlaying, currentTime, duration, setPlaying, setCurrentTime } =
    useEditorStore();
  const { syncStatus, syncProgress, videoInfo } = useSyncStore();

  return (
    <div className="flex h-screen flex-col bg-editor-bg text-editor-text">
      {/* Header */}
      <header className="flex h-12 items-center justify-between border-b border-editor-surface px-4">
        <h1 className="text-lg font-bold tracking-tight">
          Audio AI Editor
        </h1>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowImport(true)}
            className="flex items-center gap-1.5 rounded-md bg-editor-accent px-3 py-1.5 text-xs font-medium text-white transition hover:bg-editor-accent/80"
          >
            <FolderOpen size={14} />
            Import
          </button>
          <span className="text-xs text-editor-muted">v0.1.0</span>
        </div>
      </header>

      {/* Main content */}
      <main className="flex flex-1 overflow-hidden">
        {/* Left: Video + Sync Results */}
        <div className="flex w-80 flex-col border-r border-editor-surface">
          <div className="aspect-video w-full bg-black">
            <VideoPlayer />
          </div>
          <div className="flex-1 overflow-y-auto">
            <SyncResultPanel />
          </div>
        </div>

        {/* Right: Timeline area */}
        <div className="flex flex-1 flex-col">
          {/* Transport controls */}
          <div className="flex h-10 items-center gap-2 border-b border-editor-surface px-4">
            <button
              onClick={() => setCurrentTime(0)}
              className="rounded p-1 hover:bg-editor-surface"
            >
              <SkipBack size={16} />
            </button>
            <button
              onClick={() => setPlaying(!isPlaying)}
              className="rounded bg-editor-accent p-1.5 text-white hover:bg-editor-accent/80"
            >
              {isPlaying ? <Pause size={16} /> : <Play size={16} />}
            </button>
            <span className="ml-2 font-mono text-xs text-editor-muted">
              {formatTimecode(currentTime)} / {formatTimecode(duration)}
            </span>

            {syncStatus === "analyzing" && (
              <div className="ml-auto flex items-center gap-2">
                <div className="h-1.5 w-32 rounded-full bg-editor-surface">
                  <div
                    className="h-full rounded-full bg-editor-accent transition-all"
                    style={{ width: `${syncProgress * 100}%` }}
                  />
                </div>
                <span className="text-xs text-editor-muted">
                  Analyzing...
                </span>
              </div>
            )}
          </div>

          {/* Timeline placeholder */}
          <div className="flex flex-1 items-center justify-center">
            {videoInfo ? (
              <p className="text-sm text-editor-muted">
                Timeline — {videoInfo.filename} ({videoInfo.duration_s.toFixed(1)}s)
              </p>
            ) : (
              <p className="text-editor-muted">
                Click <strong>Import</strong> to load video + audio stems
              </p>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="flex h-8 items-center justify-between border-t border-editor-surface px-4">
        <span className="text-xs text-editor-muted">
          {syncStatus === "completed"
            ? "Sync complete"
            : syncStatus === "analyzing"
              ? "Analyzing..."
              : "Ready"}
        </span>
        {videoInfo && (
          <span className="text-xs text-editor-muted">
            {videoInfo.width}×{videoInfo.height} · {videoInfo.fps.toFixed(1)}fps
          </span>
        )}
      </footer>

      {/* Import Dialog */}
      {showImport && <ImportDialog onClose={() => setShowImport(false)} />}
    </div>
  );
}
