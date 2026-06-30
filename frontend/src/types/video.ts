export interface VideoUploadResponse {
  video_id: string;
  filename: string;
  duration_s: number;
  fps: number;
  width: number;
  height: number;
  has_audio: boolean;
}

export interface SyncNote {
  timestamp_s: number;
  duration_s: number;
  level: "info" | "warning" | "error";
  message: string;
}

export interface SegmentMap {
  audio_start_s: number;
  audio_end_s: number;
  lip_start_s: number;
  lip_end_s: number;
  stretch_ratio: number;
  confidence: number;
}

export interface StemSyncResult {
  stem_id: string;
  offset_ms: number;
  matched_face_id: number;
  overall_confidence: number;
  segment_maps: SegmentMap[];
  notes: SyncNote[];
}

export interface SyncAnalysisResponse {
  task_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  progress: number;
  results: StemSyncResult[];
}
