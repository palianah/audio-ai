"""Audio sync engine: place original audio at lip positions, trim or pad with silence."""

import logging
from dataclasses import dataclass

import numpy as np
import soundfile as sf

from app.services.sync_engine import SegmentMap, SyncNote

logger = logging.getLogger(__name__)


@dataclass
class SyncedAudio:
    """Result of syncing an audio stem to video."""

    audio: np.ndarray
    sample_rate: int
    notes: list[SyncNote]


class TimeStretchEngine:
    """Places original audio segments at lip-matched positions.

    NO time-stretching — audio is never pitched or warped.
    - Audio longer than lip slot → trimmed (cut at end)
    - Audio shorter than lip slot → placed as-is, rest is silence
    - Segments with no lip match → dropped (silence)
    """

    def apply_sync(
        self,
        audio_path: str,
        segment_maps: list[SegmentMap],
        total_duration_s: float,
    ) -> SyncedAudio:
        """Place audio segments at their lip-matched positions.

        Args:
            audio_path: Path to the original audio stem
            segment_maps: List of SegmentMap from the sync engine
            total_duration_s: Target total duration (video length)

        Returns:
            SyncedAudio with segments placed at correct positions
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
            audio_dur = seg_map.audio_end_s - seg_map.audio_start_s
            lip_dur = seg_map.lip_end_s - seg_map.lip_start_s

            dst_start = int(seg_map.lip_start_s * sr)
            lip_samples = int(lip_dur * sr)

            if dst_start < 0 or dst_start >= target_samples:
                continue

            if len(segment_audio) > lip_samples:
                # Audio longer than lip slot → trim
                placed = segment_audio[:lip_samples]
                notes.append(
                    SyncNote(
                        timestamp_s=seg_map.lip_start_s,
                        duration_s=lip_dur,
                        level="info",
                        message=(
                            f"Audio trimmed at {seg_map.lip_start_s:.1f}s: "
                            f"{audio_dur:.2f}s → {lip_dur:.2f}s "
                            f"(cut {audio_dur - lip_dur:.2f}s)"
                        ),
                    )
                )
            else:
                # Audio shorter or equal → place as-is (rest stays silent)
                placed = segment_audio
                if lip_dur - audio_dur > 0.1:
                    notes.append(
                        SyncNote(
                            timestamp_s=seg_map.lip_start_s,
                            duration_s=lip_dur,
                            level="info",
                            message=(
                                f"Audio shorter than lip at "
                                f"{seg_map.lip_start_s:.1f}s: "
                                f"{audio_dur:.2f}s < {lip_dur:.2f}s "
                                f"({lip_dur - audio_dur:.2f}s silence)"
                            ),
                        )
                    )

            # Clamp to output bounds
            dst_end = dst_start + len(placed)
            if dst_end > target_samples:
                placed = placed[: target_samples - dst_start]
                dst_end = target_samples

            length = min(len(placed), dst_end - dst_start)
            if length > 0:
                # Crossfade edges (5ms)
                fade_samples = min(int(0.005 * sr), length // 4)
                if fade_samples > 1:
                    placed[:fade_samples] *= np.linspace(
                        0, 1, fade_samples, dtype=np.float32
                    )
                    placed[-fade_samples:] *= np.linspace(
                        1, 0, fade_samples, dtype=np.float32
                    )

                output[dst_start : dst_start + length] += placed[:length]

        return SyncedAudio(audio=output, sample_rate=sr, notes=notes)

    @staticmethod
    def save(synced: SyncedAudio, output_path: str) -> str:
        """Save synced audio to WAV file."""
        sf.write(
            output_path,
            synced.audio,
            synced.sample_rate,
            subtype="PCM_16",
        )
        return output_path
