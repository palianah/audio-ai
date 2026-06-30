"""Sync matching engine: aligns audio stems to video lip movements."""

from dataclasses import dataclass, field

import numpy as np
from app.services.vad import SpeechSegment


@dataclass
class SegmentMap:
    """Maps an audio speech segment to a lip speech segment."""

    audio_start_s: float
    audio_end_s: float
    lip_start_s: float
    lip_end_s: float
    stretch_ratio: float
    confidence: float

    @property
    def audio_duration(self) -> float:
        return self.audio_end_s - self.audio_start_s

    @property
    def lip_duration(self) -> float:
        return self.lip_end_s - self.lip_start_s


@dataclass
class SyncNote:
    """Warning or info note about sync quality."""

    timestamp_s: float
    duration_s: float
    level: str  # "info", "warning", "error"
    message: str


@dataclass
class SyncResult:
    """Result of syncing one audio stem to video."""

    stem_id: str
    offset_ms: int
    matched_face_id: int
    overall_confidence: float
    segment_maps: list[SegmentMap] = field(default_factory=list)
    notes: list[SyncNote] = field(default_factory=list)


class SyncEngine:
    """Matches audio speech segments to video lip segments.

    Uses cross-correlation of activity timelines to find the best
    global offset, then maps individual segments for time-stretching.
    """

    def __init__(
        self,
        resolution_ms: int = 50,
        max_offset_s: float = 30.0,
    ) -> None:
        self.resolution_ms = resolution_ms
        self.max_offset_s = max_offset_s

    def sync_stem(
        self,
        stem_id: str,
        audio_segments: list[SpeechSegment],
        lip_segments_by_face: dict[int, list[SpeechSegment]],
        total_duration_s: float,
        guide_segments: list[SpeechSegment] | None = None,
    ) -> SyncResult:
        """Find the best alignment for one audio stem.

        Args:
            stem_id: Identifier for this audio stem
            audio_segments: VAD segments from the audio stem
            lip_segments_by_face: Lip segments per face_id from video
            total_duration_s: Total video duration
            guide_segments: Optional VAD from video's guide audio

        Returns:
            SyncResult with offset, segment maps, and notes
        """
        if not audio_segments:
            return SyncResult(
                stem_id=stem_id,
                offset_ms=0,
                matched_face_id=-1,
                overall_confidence=0.0,
                notes=[
                    SyncNote(
                        timestamp_s=0,
                        duration_s=total_duration_s,
                        level="error",
                        message="No speech detected in audio stem",
                    )
                ],
            )

        audio_timeline = self._segments_to_timeline(audio_segments, total_duration_s)

        best_face_id = -1
        best_offset = 0
        best_score = -1.0

        for face_id, lip_segs in lip_segments_by_face.items():
            lip_timeline = self._segments_to_timeline(lip_segs, total_duration_s)
            offset, score = self._cross_correlate(audio_timeline, lip_timeline)
            if score > best_score:
                best_score = score
                best_offset = offset
                best_face_id = face_id

        if guide_segments and best_score < 0.3:
            guide_timeline = self._segments_to_timeline(
                guide_segments, total_duration_s
            )
            offset, score = self._cross_correlate(audio_timeline, guide_timeline)
            if score > best_score:
                best_score = score
                best_offset = offset
                best_face_id = -1

        offset_ms = int(best_offset * self.resolution_ms)
        confidence = min(1.0, max(0.0, best_score))

        segment_maps, notes = self._build_segment_maps(
            audio_segments,
            lip_segments_by_face.get(best_face_id, []),
            offset_ms / 1000.0,
        )

        if best_face_id == -1 and lip_segments_by_face:
            notes.append(
                SyncNote(
                    timestamp_s=0,
                    duration_s=total_duration_s,
                    level="warning",
                    message="Could not match stem to any face; "
                    "used guide audio for alignment",
                )
            )

        if confidence < 0.3:
            notes.append(
                SyncNote(
                    timestamp_s=0,
                    duration_s=total_duration_s,
                    level="warning",
                    message=f"Low sync confidence ({confidence:.2f}); "
                    "manual review recommended",
                )
            )

        return SyncResult(
            stem_id=stem_id,
            offset_ms=offset_ms,
            matched_face_id=best_face_id,
            overall_confidence=round(confidence, 3),
            segment_maps=segment_maps,
            notes=notes,
        )

    def _segments_to_timeline(
        self,
        segments: list[SpeechSegment],
        duration_s: float,
    ) -> np.ndarray:
        """Convert segments to binary activity timeline."""
        n_bins = int(duration_s * 1000 / self.resolution_ms) + 1
        timeline = np.zeros(n_bins, dtype=np.float32)

        for seg in segments:
            start_bin = int(seg.start_s * 1000 / self.resolution_ms)
            end_bin = int(seg.end_s * 1000 / self.resolution_ms)
            start_bin = max(0, min(start_bin, n_bins - 1))
            end_bin = max(0, min(end_bin, n_bins))
            timeline[start_bin:end_bin] = seg.confidence

        return timeline

    def _cross_correlate(
        self,
        audio_tl: np.ndarray,
        lip_tl: np.ndarray,
    ) -> tuple[int, float]:
        """Cross-correlate two timelines, return best offset and score.

        Returns:
            (offset_bins, normalized_score)
        """
        max_shift = int(self.max_offset_s * 1000 / self.resolution_ms)
        n = max(len(audio_tl), len(lip_tl))

        a_pad = np.zeros(n, dtype=np.float32)
        l_pad = np.zeros(n, dtype=np.float32)
        a_pad[: len(audio_tl)] = audio_tl
        l_pad[: len(lip_tl)] = lip_tl

        a_norm = np.sum(a_pad**2)
        l_norm = np.sum(l_pad**2)
        if a_norm < 1e-6 or l_norm < 1e-6:
            return 0, 0.0

        best_offset = 0
        best_score = -1.0

        for shift in range(-max_shift, max_shift + 1):
            if shift >= 0:
                shifted = np.zeros_like(a_pad)
                if shift < n:
                    shifted[shift:] = a_pad[: n - shift]
            else:
                shifted = np.zeros_like(a_pad)
                if -shift < n:
                    shifted[: n + shift] = a_pad[-shift:]

            score = float(np.dot(shifted, l_pad))
            score /= np.sqrt(a_norm * l_norm)

            if score > best_score:
                best_score = score
                best_offset = shift

        return best_offset, best_score

    def _build_segment_maps(
        self,
        audio_segments: list[SpeechSegment],
        lip_segments: list[SpeechSegment],
        offset_s: float,
    ) -> tuple[list[SegmentMap], list[SyncNote]]:
        """Map audio segments to lip segments with time-stretch ratios."""
        maps: list[SegmentMap] = []
        notes: list[SyncNote] = []

        shifted_audio = [
            SpeechSegment(
                start_s=s.start_s + offset_s,
                end_s=s.end_s + offset_s,
                confidence=s.confidence,
            )
            for s in audio_segments
        ]

        used_lip: set[int] = set()

        for audio_seg in shifted_audio:
            best_lip_idx = -1
            best_overlap = 0.0

            for i, lip_seg in enumerate(lip_segments):
                if i in used_lip:
                    continue
                overlap = self._overlap(audio_seg, lip_seg)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_lip_idx = i

            if best_lip_idx >= 0:
                lip_seg = lip_segments[best_lip_idx]
                used_lip.add(best_lip_idx)

                audio_dur = audio_seg.duration_s
                lip_dur = lip_seg.duration_s
                ratio = lip_dur / audio_dur if audio_dur > 0.01 else 1.0

                seg_map = SegmentMap(
                    audio_start_s=round(audio_seg.start_s - offset_s, 3),
                    audio_end_s=round(audio_seg.end_s - offset_s, 3),
                    lip_start_s=round(lip_seg.start_s, 3),
                    lip_end_s=round(lip_seg.end_s, 3),
                    stretch_ratio=round(ratio, 4),
                    confidence=round(
                        min(audio_seg.confidence, lip_seg.confidence),
                        3,
                    ),
                )
                maps.append(seg_map)

                if ratio > 2.0 or ratio < 0.5:
                    notes.append(
                        SyncNote(
                            timestamp_s=lip_seg.start_s,
                            duration_s=lip_seg.duration_s,
                            level="warning",
                            message=(
                                f"Extreme time-stretch ({ratio:.2f}x) "
                                f"at {lip_seg.start_s:.1f}s; "
                                "audio quality may degrade"
                            ),
                        )
                    )
            else:
                notes.append(
                    SyncNote(
                        timestamp_s=audio_seg.start_s,
                        duration_s=audio_seg.duration_s,
                        level="info",
                        message=(
                            f"No matching lip segment found for "
                            f"audio at {audio_seg.start_s:.1f}s–"
                            f"{audio_seg.end_s:.1f}s"
                        ),
                    )
                )

        return maps, notes

    @staticmethod
    def _overlap(a: SpeechSegment, b: SpeechSegment) -> float:
        """Calculate overlap duration between two segments."""
        start = max(a.start_s, b.start_s)
        end = min(a.end_s, b.end_s)
        return max(0.0, end - start)
