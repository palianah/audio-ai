"""Voice Activity Detection service using Silero VAD."""

from dataclasses import dataclass

import numpy as np
import soundfile as sf
import torch


@dataclass
class SpeechSegment:
    """A detected speech segment with timestamps and confidence."""

    start_s: float
    end_s: float
    confidence: float = 1.0

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s


class VoiceActivityDetector:
    """Detects speech segments in audio using Silero VAD.

    Silero VAD is a lightweight, highly accurate voice activity
    detector that runs on CPU via PyTorch.
    """

    def __init__(
        self,
        threshold: float = 0.5,
        min_speech_duration_s: float = 0.1,
        min_silence_duration_s: float = 0.15,
        window_size_samples: int = 512,
        sample_rate: int = 16000,
    ) -> None:
        self.threshold = threshold
        self.min_speech_duration_s = min_speech_duration_s
        self.min_silence_duration_s = min_silence_duration_s
        self.window_size_samples = window_size_samples
        self.sample_rate = sample_rate
        self._model = None

    def _load_model(self) -> None:
        """Lazy-load the Silero VAD model from torch.hub."""
        if self._model is None:
            self._model, _ = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                force_reload=False,
                onnx=False,
            )
            self._model.eval()

    def _load_audio(self, audio_path: str) -> np.ndarray:
        """Load and resample audio to 16kHz mono."""
        audio, sr = sf.read(audio_path, dtype="float32")

        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        if sr != self.sample_rate:
            import librosa

            audio = librosa.resample(audio, orig_sr=sr, target_sr=self.sample_rate)

        return audio

    def detect(self, audio_path: str) -> list[SpeechSegment]:
        """Detect speech segments in an audio file.

        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)

        Returns:
            List of SpeechSegment with start/end timestamps
        """
        self._load_model()
        audio = self._load_audio(audio_path)
        tensor = torch.from_numpy(audio)

        speech_timestamps = self._get_speech_timestamps(tensor)

        segments = []
        for ts in speech_timestamps:
            start_s = ts["start"] / self.sample_rate
            end_s = ts["end"] / self.sample_rate
            segments.append(
                SpeechSegment(
                    start_s=round(start_s, 3),
                    end_s=round(end_s, 3),
                    confidence=ts.get("confidence", 1.0),
                )
            )

        return segments

    def _get_speech_timestamps(self, audio: torch.Tensor) -> list[dict]:
        """Run VAD on audio tensor, return raw timestamps."""
        assert self._model is not None

        min_speech_samples = int(self.min_speech_duration_s * self.sample_rate)
        min_silence_samples = int(self.min_silence_duration_s * self.sample_rate)

        speeches: list[dict] = []
        current_speech: dict | None = None
        audio_length = audio.shape[0]

        self._model.reset_states()

        for i in range(0, audio_length, self.window_size_samples):
            end = min(i + self.window_size_samples, audio_length)
            chunk = audio[i:end]

            if len(chunk) < self.window_size_samples:
                chunk = torch.nn.functional.pad(
                    chunk,
                    (0, self.window_size_samples - len(chunk)),
                )

            prob = self._model(chunk, self.sample_rate).item()

            if prob >= self.threshold:
                if current_speech is None:
                    current_speech = {"start": i, "end": end}
                else:
                    current_speech["end"] = end
            else:
                if current_speech is not None:
                    duration = current_speech["end"] - current_speech["start"]
                    if duration >= min_speech_samples:
                        speeches.append(current_speech)
                    current_speech = None

        if current_speech is not None:
            duration = current_speech["end"] - current_speech["start"]
            if duration >= min_speech_samples:
                speeches.append(current_speech)

        merged = self._merge_close_segments(speeches, min_silence_samples)
        return merged

    @staticmethod
    def _merge_close_segments(segments: list[dict], min_gap: int) -> list[dict]:
        """Merge speech segments separated by short silences."""
        if not segments:
            return []

        merged = [segments[0].copy()]
        for seg in segments[1:]:
            gap = seg["start"] - merged[-1]["end"]
            if gap < min_gap:
                merged[-1]["end"] = seg["end"]
            else:
                merged.append(seg.copy())

        return merged

    def detect_batch(self, audio_paths: list[str]) -> dict[str, list[SpeechSegment]]:
        """Detect speech in multiple audio files.

        Args:
            audio_paths: List of paths to audio files

        Returns:
            Dict mapping file path to list of SpeechSegments
        """
        results: dict[str, list[SpeechSegment]] = {}
        for path in audio_paths:
            results[path] = self.detect(path)
        return results
