"""Face mesh and lip movement detection using MediaPipe."""

from dataclasses import dataclass, field

import cv2
import numpy as np
from app.services.vad import SpeechSegment

UPPER_LIP = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291]
LOWER_LIP = [146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 61]
MOUTH_TOP = 13
MOUTH_BOTTOM = 14
MOUTH_LEFT = 78
MOUTH_RIGHT = 308


@dataclass
class FaceTrack:
    """Tracked face across frames with lip activity."""

    face_id: int
    center_x: float
    center_y: float
    mar_history: list[float] = field(default_factory=list)
    frame_indices: list[int] = field(default_factory=list)
    speaking_frames: list[bool] = field(default_factory=list)


class LipDetector:
    """Detects lip movements in video frames using MediaPipe Face Mesh.

    Calculates Mouth Aspect Ratio (MAR) per frame to determine
    speaking vs non-speaking states. Tracks faces across frames
    using spatial proximity.
    """

    def __init__(
        self,
        mar_threshold: float = 0.03,
        min_detection_confidence: float = 0.3,
        min_tracking_confidence: float = 0.3,
        face_match_distance: float = 100.0,
    ) -> None:
        self.mar_threshold = mar_threshold
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.face_match_distance = face_match_distance
        self._face_mesh = None

    def _init_face_mesh(self) -> None:
        """Lazy-init MediaPipe FaceMesh."""
        if self._face_mesh is None:
            import mediapipe as mp

            self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=5,
                refine_landmarks=True,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence,
            )

    def analyze_frames(
        self,
        frames: list[np.ndarray],
        fps: float = 10.0,
    ) -> dict[int, list[SpeechSegment]]:
        """Analyze video frames for lip movement.

        Args:
            frames: List of BGR frame arrays
            fps: Frame rate of the extracted frames

        Returns:
            Dict mapping face_id to list of SpeechSegments
        """
        self._init_face_mesh()
        assert self._face_mesh is not None

        tracks: list[FaceTrack] = []

        for frame_idx, frame in enumerate(frames):
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self._face_mesh.process(rgb)

            if not results.multi_face_landmarks:
                continue

            h, w = frame.shape[:2]

            for face_landmarks in results.multi_face_landmarks:
                mar = self._compute_mar(face_landmarks, w, h)
                cx, cy = self._face_center(face_landmarks, w, h)
                is_speaking = mar > self.mar_threshold

                matched = self._match_face(tracks, cx, cy)
                if matched is not None:
                    matched.mar_history.append(mar)
                    matched.frame_indices.append(frame_idx)
                    matched.speaking_frames.append(is_speaking)
                    matched.center_x = cx
                    matched.center_y = cy
                else:
                    new_track = FaceTrack(
                        face_id=len(tracks),
                        center_x=cx,
                        center_y=cy,
                        mar_history=[mar],
                        frame_indices=[frame_idx],
                        speaking_frames=[is_speaking],
                    )
                    tracks.append(new_track)

        return self._tracks_to_segments(tracks, fps)

    @staticmethod
    def _compute_mar(face_landmarks: object, w: int, h: int) -> float:
        """Compute Mouth Aspect Ratio from face landmarks."""
        lm = face_landmarks.landmark  # type: ignore[attr-defined]

        top = np.array([lm[MOUTH_TOP].x * w, lm[MOUTH_TOP].y * h])
        bottom = np.array([lm[MOUTH_BOTTOM].x * w, lm[MOUTH_BOTTOM].y * h])
        left = np.array([lm[MOUTH_LEFT].x * w, lm[MOUTH_LEFT].y * h])
        right = np.array([lm[MOUTH_RIGHT].x * w, lm[MOUTH_RIGHT].y * h])

        vertical = float(np.linalg.norm(top - bottom))
        horizontal = float(np.linalg.norm(left - right))

        if horizontal < 1.0:
            return 0.0
        return vertical / horizontal

    @staticmethod
    def _face_center(face_landmarks: object, w: int, h: int) -> tuple[float, float]:
        """Get approximate center of face from nose tip (landmark 1)."""
        lm = face_landmarks.landmark  # type: ignore[attr-defined]
        return lm[1].x * w, lm[1].y * h

    def _match_face(
        self, tracks: list[FaceTrack], cx: float, cy: float
    ) -> FaceTrack | None:
        """Match a detected face to existing tracks by proximity."""
        best: FaceTrack | None = None
        best_dist = self.face_match_distance

        for track in tracks:
            dist = np.sqrt((track.center_x - cx) ** 2 + (track.center_y - cy) ** 2)
            if dist < best_dist:
                best_dist = dist
                best = track

        return best

    def _tracks_to_segments(
        self, tracks: list[FaceTrack], fps: float
    ) -> dict[int, list[SpeechSegment]]:
        """Convert face tracks to speech segments per face."""
        result: dict[int, list[SpeechSegment]] = {}

        for track in tracks:
            if len(track.frame_indices) < 3:
                continue

            smoothed = self._smooth_speaking(track.speaking_frames, window=3)

            segments: list[SpeechSegment] = []
            in_speech = False
            start_frame = 0

            for i, speaking in enumerate(smoothed):
                frame_idx = track.frame_indices[i]
                if speaking and not in_speech:
                    in_speech = True
                    start_frame = frame_idx
                elif not speaking and in_speech:
                    in_speech = False
                    start_s = start_frame / fps
                    end_s = frame_idx / fps
                    if end_s - start_s >= 0.1:
                        confidence = self._segment_confidence(
                            track, i - (frame_idx - start_frame), i
                        )
                        segments.append(
                            SpeechSegment(
                                start_s=round(start_s, 3),
                                end_s=round(end_s, 3),
                                confidence=confidence,
                            )
                        )

            if in_speech:
                start_s = start_frame / fps
                end_s = track.frame_indices[-1] / fps
                if end_s - start_s >= 0.1:
                    segments.append(
                        SpeechSegment(
                            start_s=round(start_s, 3),
                            end_s=round(end_s, 3),
                            confidence=0.7,
                        )
                    )

            if segments:
                result[track.face_id] = segments

        return result

    @staticmethod
    def _smooth_speaking(speaking: list[bool], window: int = 3) -> list[bool]:
        """Smooth speaking detection to reduce flicker."""
        if len(speaking) < window:
            return speaking

        smoothed = speaking.copy()
        half = window // 2
        for i in range(half, len(speaking) - half):
            votes = sum(speaking[i - half : i + half + 1])
            smoothed[i] = votes > window // 2

        return smoothed

    @staticmethod
    def _segment_confidence(
        track: FaceTrack,
        start_idx: int,
        end_idx: int,
    ) -> float:
        """Estimate confidence for a speech segment."""
        start_idx = max(0, start_idx)
        end_idx = min(len(track.mar_history), end_idx)
        if start_idx >= end_idx:
            return 0.5

        mars = track.mar_history[start_idx:end_idx]
        avg_mar = np.mean(mars)
        mar_std = np.std(mars)

        if avg_mar > 0.08 and mar_std > 0.01:
            return min(0.95, 0.7 + avg_mar + mar_std)
        elif avg_mar > 0.04:
            return 0.6
        else:
            return 0.4
