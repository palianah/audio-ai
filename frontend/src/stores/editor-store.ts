import { create } from "zustand";

export interface Track {
  id: string;
  name: string;
  stemType: "vocals" | "drums" | "bass" | "other" | "original";
  fileUrl: string;
  volume: number;
  pan: number;
  muted: boolean;
  soloed: boolean;
  color: string;
}

export interface EditorState {
  tracks: Track[];
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  zoom: number;
  selectedTrackId: string | null;

  addTrack: (track: Track) => void;
  removeTrack: (id: string) => void;
  updateTrack: (id: string, updates: Partial<Track>) => void;
  setPlaying: (playing: boolean) => void;
  setCurrentTime: (time: number) => void;
  setDuration: (duration: number) => void;
  setZoom: (zoom: number) => void;
  selectTrack: (id: string | null) => void;
  toggleMute: (id: string) => void;
  toggleSolo: (id: string) => void;
}

export const useEditorStore = create<EditorState>((set) => ({
  tracks: [],
  isPlaying: false,
  currentTime: 0,
  duration: 0,
  zoom: 1,
  selectedTrackId: null,

  addTrack: (track) =>
    set((state) => ({ tracks: [...state.tracks, track] })),

  removeTrack: (id) =>
    set((state) => ({ tracks: state.tracks.filter((t) => t.id !== id) })),

  updateTrack: (id, updates) =>
    set((state) => ({
      tracks: state.tracks.map((t) => (t.id === id ? { ...t, ...updates } : t)),
    })),

  setPlaying: (playing) => set({ isPlaying: playing }),
  setCurrentTime: (time) => set({ currentTime: time }),
  setDuration: (duration) => set({ duration }),
  setZoom: (zoom) => set({ zoom }),
  selectTrack: (id) => set({ selectedTrackId: id }),

  toggleMute: (id) =>
    set((state) => ({
      tracks: state.tracks.map((t) =>
        t.id === id ? { ...t, muted: !t.muted } : t
      ),
    })),

  toggleSolo: (id) =>
    set((state) => ({
      tracks: state.tracks.map((t) =>
        t.id === id ? { ...t, soloed: !t.soloed } : t
      ),
    })),
}));
