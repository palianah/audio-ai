import { create } from "zustand";

import type {
  StemSyncResult,
  SyncAnalysisResponse,
  SyncNote,
  VideoUploadResponse,
} from "@/types/video";

export interface SyncState {
  videoInfo: VideoUploadResponse | null;
  videoUrl: string | null;
  stemFiles: Array<{ stemId: string; filename: string }>;
  syncResults: StemSyncResult[];
  syncNotes: SyncNote[];
  syncStatus: "idle" | "uploading" | "analyzing" | "completed" | "failed";
  syncProgress: number;
  appliedStemUrls: Record<string, string>;
  applyTimestamp: number;

  setVideoInfo: (info: VideoUploadResponse, url: string) => void;
  addStem: (stemId: string, filename: string) => void;
  removeStem: (stemId: string) => void;
  setSyncStatus: (status: SyncState["syncStatus"]) => void;
  setSyncProgress: (progress: number) => void;
  setSyncResults: (response: SyncAnalysisResponse) => void;
  updateStemOffset: (stemId: string, offsetMs: number) => void;
  setAppliedStemUrls: (urls: Record<string, string>) => void;
  reset: () => void;
}

export const useSyncStore = create<SyncState>((set) => ({
  videoInfo: null,
  videoUrl: null,
  stemFiles: [],
  syncResults: [],
  syncNotes: [],
  syncStatus: "idle",
  syncProgress: 0,
  appliedStemUrls: {},
  applyTimestamp: 0,

  setVideoInfo: (info, url) =>
    set({ videoInfo: info, videoUrl: url }),

  addStem: (stemId, filename) =>
    set((state) => ({
      stemFiles: [...state.stemFiles, { stemId, filename }],
    })),

  removeStem: (stemId) =>
    set((state) => ({
      stemFiles: state.stemFiles.filter((s) => s.stemId !== stemId),
    })),

  setSyncStatus: (status) => set({ syncStatus: status }),

  setSyncProgress: (progress) => set({ syncProgress: progress }),

  setSyncResults: (response) => {
    const allNotes = response.results.flatMap((r) => r.notes);
    set({
      syncResults: response.results,
      syncNotes: allNotes,
      syncStatus: response.status === "completed" ? "completed" : "failed",
      syncProgress: response.progress,
    });
  },

  updateStemOffset: (stemId, offsetMs) =>
    set((state) => ({
      syncResults: state.syncResults.map((r) =>
        r.stem_id === stemId ? { ...r, offset_ms: offsetMs } : r
      ),
    })),

  setAppliedStemUrls: (urls) =>
    set({ appliedStemUrls: urls, applyTimestamp: Date.now() }),

  reset: () =>
    set({
      videoInfo: null,
      videoUrl: null,
      stemFiles: [],
      syncResults: [],
      syncNotes: [],
      syncStatus: "idle",
      syncProgress: 0,
      appliedStemUrls: {},
      applyTimestamp: 0,
    }),
}));
