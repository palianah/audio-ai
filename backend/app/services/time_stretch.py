"""Pitch-preserving time-stretch engine for dubbing alignment."""

import logging
from dataclasses import dataclass

import numpy as np
import soundfile as sf
from app.services.sync_engine import SegmentMap, SyncNote

logger = logging.getLogger(__name__)


@dataclass
class StretchedAudio:
    """Result of time-stretching an audio stem."""

    audio: np.ndarray
    sample_rate: int
    notes: list[SyncNote]


class TimeStretchEngine:
    """Applies pitch-preserving time-stretch to align audio to lip timing.

    Uses pyrubberband (Rubber Band Library) for high-quality stretching.
    Falls back to librosa if pyrubberband is unavailable.
    """

    def __init__(self, max_ratio: float = 3.0) -> None:
        self.max_ratio = max_ratio
        self._backend = self._detect_backend()

    @staticmethod
    def _detect_backend() -> str:
        """Check which time-stretch backend is available."""
        try:
            import pyrubberband  # noqa: F401

            return "rubberband"
        except ImportError:
            logger.warning("pyrubberband not available, falling back to librosa")
            return "librosa"

    def stretch_segment(
        self,
        audio: np.ndarray,
        sr: int,
        ratio: float,
    ) -> np.ndarray:
        """Time-stretch an audio segment by the given ratio.

        Args:
            audio: Audio samples (mono float32)
            sr: Sample rate
            ratio: Stretch ratio (>1 = longer, <1 = shorter)

        Returns:
            Stretched audio samples
        """
        if abs(ratio - 1.0) < 0.01:
            return audio

        ratio = max(1.0 / self.max_ratio, min(self.max_ratio, ratio))

        if self._backend == "rubberband":
            return self._stretch_rubberband(audio, sr, ratio)
        else:
            return self._stretch_librosa(audio, sr, ratio)

    @staticmethod
    def _stretch_rubberband(audio: np.ndarray, sr: int, ratio: float) -> np.ndarray:
        """Stretch using pyrubberband (highest quality)."""
        import pyrubberband as pyrb

        stretched = pyrb.time_stretch(audio, sr, ratio)
        return stretched.astype(np.float32)

    @staticmethod
    def _stretch_librosa(audio: np.ndarray, sr: int, ratio: float) -> np.ndarray:
        """Stretch using librosa (fallback)."""
        import librosa

        rate = 1.0 / ratio
        stretched = librosa.effects.time_stretch(audio, rate=rate)
        return stretched.astype(np.float32)

    def apply_sync(
        self,
        audio_path: str,
        segment_maps: list[SegmentMap],
        total_duration_s: float,
    ) -> StretchedAudio:
        """Apply time-stretch to an entire audio stem based on segment maps.

        Args:
            audio_path: Path to the original audio stem
            segment_maps: List of SegmentMap from the sync engine
            total_duration_s: Target total duration (video length)

        Returns:
            StretchedAudio with the processed audio
        """
        audio, sr = sf.read(audio_path, dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        target_samples = int(total_duration_s * sr)
        output = np.zeros(target_samples, dtype=np.float32)
        notes: list[SyncNote] = []

        sorted_maps = sorted(segment_maps, key=lambda m: m.lip_start_s)

        for seg_map in sorted_maps:
            src_start = int(seg_map.audio_start_s * sr)
            src_end = int(seg_map.audio_end_s * sr)
            src_start = max(0, min(src_start, len(audio)))
            src_end = max(0, min(src_end, len(audio)))

            if src_end <= src_start:
                continue

            segment_audio = audio[src_start:src_end]
            ratio = seg_map.stretch_ratio

            if abs(ratio - 1.0) < 0.01:
                stretched = segment_audio
            elif ratio > self.max_ratio or ratio < 1.0 / self.max_ratio:
                notes.append(
                    SyncNote(
                        timestamp_s=seg_map.lip_start_s,
                        duration_s=seg_map.lip_duration,
                        level="error",
                        message=(
                            f"Stretch ratio {ratio:.2f}x exceeds "
                            f"max {self.max_ratio}x; segment skipped"
                        ),
                    )
                )
                stretched = segment_audio
                ratio = 1.0
            else:
                try:
                    stretched = self.stretch_segment(segment_audio, sr, ratio)
                except Exception as e:
                    logger.error(
                        "Time-stretch failed at %.1fs: %s",
                        seg_map.lip_start_s,
                        e,
                    )
                    notes.append(
                        SyncNote(
                            timestamp_s=seg_map.lip_start_s,
                            duration_s=seg_map.lip_duration,
                            level="error",
                            message=f"Time-stretch failed: {e}",
                        )
                    )
                    stretched = segment_audio

            dst_start = int(seg_map.lip_start_s * sr)
            dst_end = dst_start + len(stretched)

            if dst_start < 0:
                stretched = stretched[-dst_start:]
                dst_start = 0
            if dst_end > target_samples:
                stretched = stretched[: target_samples - dst_start]
                dst_end = target_samples

            length = min(len(stretched), dst_end - dst_start)
            if length > 0:
                fade_samples = min(int(0.005 * sr), length // 4)
                if fade_samples > 0:
                    fade_in = np.linspace(0, 1, fade_samples)
                    fade_out = np.linspace(1, 0, fade_samples)
                    stretched[:fade_samples] *= fade_in
                    stretched[-fade_samples:] *= fade_out

                output[dst_start : dst_start + length] += stretched[:length]

        return StretchedAudio(audio=output, sample_rate=sr, notes=notes)

    @staticmethod
    def save(stretched: StretchedAudio, output_path: str) -> str:
        """Save stretched audio to WAV file."""
        sf.write(
            output_path,
            stretched.audio,
            stretched.sample_rate,
            subtype="PCM_16",
        )
        return output_path
