"""Video ingestion and frame extraction service."""

import os
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.core.config import settings


@dataclass
class VideoInfo:
    """Metadata about an ingested video file."""

    video_id: str
    filename: str
    duration_s: float
    fps: float
    width: int
    height: int
    has_audio: bool
    frames_dir: str
    audio_path: str | None


class VideoProcessor:
    """Handles video upload, frame extraction, and audio demuxing."""

    def __init__(self, extraction_fps: float = 10.0) -> None:
        self.extraction_fps = extraction_fps

    def ingest(self, video_path: str, output_dir: str | None = None) -> VideoInfo:
        """Ingest a video file: extract metadata, frames, and audio.

        Args:
            video_path: Path to the video file (MP4, MOV, MKV, etc.)
            output_dir: Base output directory. Defaults to settings.output_dir.

        Returns:
            VideoInfo with paths to extracted assets
        """
        video_id = uuid.uuid4().hex[:12]
        base_dir = output_dir or settings.output_dir
        work_dir = os.path.join(base_dir, "video", video_id)
        frames_dir = os.path.join(work_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)

        info = self._probe_video(video_path)
        duration_s = info["duration"]
        fps = info["fps"]
        width = info["width"]
        height = info["height"]
        has_audio = info["has_audio"]

        self._extract_frames(video_path, frames_dir)

        audio_path = None
        if has_audio:
            audio_path = os.path.join(work_dir, "guide_audio.wav")
            self._extract_audio(video_path, audio_path)

        return VideoInfo(
            video_id=video_id,
            filename=Path(video_path).name,
            duration_s=duration_s,
            fps=fps,
            width=width,
            height=height,
            has_audio=has_audio,
            frames_dir=frames_dir,
            audio_path=audio_path,
        )

    def _probe_video(self, video_path: str) -> dict:
        """Extract video metadata using ffprobe."""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path,
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True
        )

        import json

        probe = json.loads(result.stdout)

        video_stream = None
        has_audio = False
        for stream in probe.get("streams", []):
            if stream["codec_type"] == "video" and video_stream is None:
                video_stream = stream
            if stream["codec_type"] == "audio":
                has_audio = True

        if video_stream is None:
            raise ValueError(f"No video stream found in {video_path}")

        fps_parts = video_stream.get("r_frame_rate", "30/1").split("/")
        fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0

        duration = float(
            probe.get("format", {}).get(
                "duration",
                video_stream.get("duration", "0"),
            )
        )

        return {
            "duration": duration,
            "fps": fps,
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "has_audio": has_audio,
        }

    def _extract_frames(self, video_path: str, frames_dir: str) -> int:
        """Extract frames at self.extraction_fps using OpenCV.

        Returns the number of frames extracted.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        native_fps = cap.get(cv2.CAP_PROP_FPS)
        if native_fps <= 0:
            native_fps = 30.0

        frame_interval = max(1, int(round(native_fps / self.extraction_fps)))
        frame_idx = 0
        saved = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_interval == 0:
                filename = os.path.join(
                    frames_dir, f"frame_{saved:06d}.jpg"
                )
                cv2.imwrite(filename, frame)
                saved += 1

            frame_idx += 1

        cap.release()
        return saved

    def _extract_audio(self, video_path: str, output_path: str) -> None:
        """Extract audio track from video as 16kHz mono WAV."""
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            output_path,
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    @staticmethod
    def load_frames(frames_dir: str) -> list[np.ndarray]:
        """Load extracted frames as numpy arrays (BGR)."""
        frame_files = sorted(
            f
            for f in os.listdir(frames_dir)
            if f.endswith(".jpg")
        )
        frames = []
        for fname in frame_files:
            img = cv2.imread(os.path.join(frames_dir, fname))
            if img is not None:
                frames.append(img)
        return frames

    @staticmethod
    def frame_index_to_time(
        frame_index: int, extraction_fps: float
    ) -> float:
        """Convert frame index to timestamp in seconds."""
        return frame_index / extraction_fps
