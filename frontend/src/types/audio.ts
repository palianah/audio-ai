export type AudioFormat = "wav" | "mp3" | "flac" | "ogg" | "aac";
export type StemType = "vocals" | "drums" | "bass" | "other";

export interface UploadResponse {
  file_id: string;
  filename: string;
  duration_seconds: number;
  sample_rate: number;
  channels: number;
  format: AudioFormat;
}

export interface SeparationRequest {
  file_id: string;
  stems: StemType[];
}

export interface SeparationResult {
  task_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  stems: Record<string, string>;
  progress: number;
}

export interface EffectConfig {
  type: "eq" | "compression" | "reverb" | "noise_reduction" | "normalize";
  params: Record<string, number | string | boolean>;
}

export interface TranscriptionResult {
  text: string;
  language: string;
  segments: Array<{
    start: number;
    end: number;
    text: string;
  }>;
}
