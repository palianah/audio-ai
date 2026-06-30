"""API routes for video-audio sync operations."""

import os
import uuid

import numpy as np
import soundfile as sf
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.api.schemas.video import (
    SyncAnalysisResponse,
    SyncApplyRequest,
    SyncApplyResponse,
    SyncNoteSchema,
    SyncRequest,
    VideoUploadResponse,
)
from app.core.config import settings

router = APIRouter(prefix="/api", tags=["sync"])

_video_store: dict[str, dict] = {}
_stem_store: dict[str, str] = {}
_task_store: dict[str, dict] = {}


@router.post("/video/upload", response_model=VideoUploadResponse)
async def upload_video(file: UploadFile = File(...)) -> VideoUploadResponse:
    """Upload a video file for sync analysis."""
    if file.filename is None:
        raise HTTPException(400, "No filename provided")

    video_id = uuid.uuid4().hex[:12]
    upload_dir = os.path.join(settings.upload_dir, "video", video_id)
    os.makedirs(upload_dir, exist_ok=True)

    video_path = os.path.join(upload_dir, file.filename)
    content = await file.read()
    with open(video_path, "wb") as f:
        f.write(content)

    from app.services.video import VideoProcessor

    processor = VideoProcessor()
    info = processor.ingest(video_path)

    _video_store[info.video_id] = {
        "info": info,
        "path": video_path,
    }

    return VideoUploadResponse(
        video_id=info.video_id,
        filename=info.filename,
        duration_s=info.duration_s,
        fps=info.fps,
        width=info.width,
        height=info.height,
        has_audio=info.has_audio,
    )


@router.post("/stems/upload")
async def upload_stem(
    file: UploadFile = File(...),
) -> dict:
    """Upload an audio stem file."""
    if file.filename is None:
        raise HTTPException(400, "No filename provided")

    stem_id = uuid.uuid4().hex[:12]
    upload_dir = os.path.join(settings.upload_dir, "stems")
    os.makedirs(upload_dir, exist_ok=True)

    stem_path = os.path.join(upload_dir, f"{stem_id}_{file.filename}")
    content = await file.read()
    with open(stem_path, "wb") as f:
        f.write(content)

    _stem_store[stem_id] = stem_path

    return {"stem_id": stem_id, "filename": file.filename}


@router.post("/sync/analyze", response_model=SyncAnalysisResponse)
async def analyze_sync(
    request: SyncRequest,
) -> SyncAnalysisResponse:
    """Start sync analysis between video and audio stems."""
    if request.video_id not in _video_store:
        raise HTTPException(404, "Video not found")

    for sid in request.stem_ids:
        if sid not in _stem_store:
            raise HTTPException(404, f"Stem {sid} not found")

    task_id = uuid.uuid4().hex[:12]

    video_data = _video_store[request.video_id]
    video_info = video_data["info"]

    from app.services.lip_detector import LipDetector
    from app.services.sync_engine import SyncEngine
    from app.services.vad import VoiceActivityDetector
    from app.services.video import VideoProcessor

    vad = VoiceActivityDetector()
    lip_detector = LipDetector()
    sync_engine = SyncEngine()

    frames = VideoProcessor.load_frames(video_info.frames_dir)
    lip_segments = lip_detector.analyze_frames(frames, fps=10.0)

    guide_segments = None
    if video_info.audio_path:
        guide_segments = vad.detect(video_info.audio_path)

    results = []
    for stem_id in request.stem_ids:
        stem_path = _stem_store[stem_id]
        audio_segments = vad.detect(stem_path)

        sync_result = sync_engine.sync_stem(
            stem_id=stem_id,
            audio_segments=audio_segments,
            lip_segments_by_face=lip_segments,
            total_duration_s=video_info.duration_s,
            guide_segments=guide_segments,
        )

        from app.api.schemas.video import SegmentMapSchema, StemSyncResult

        results.append(
            StemSyncResult(
                stem_id=sync_result.stem_id,
                offset_ms=sync_result.offset_ms,
                matched_face_id=sync_result.matched_face_id,
                overall_confidence=sync_result.overall_confidence,
                segment_maps=[
                    SegmentMapSchema(
                        audio_start_s=m.audio_start_s,
                        audio_end_s=m.audio_end_s,
                        lip_start_s=m.lip_start_s,
                        lip_end_s=m.lip_end_s,
                        stretch_ratio=m.stretch_ratio,
                        confidence=m.confidence,
                    )
                    for m in sync_result.segment_maps
                ],
                notes=[
                    SyncNoteSchema(
                        timestamp_s=n.timestamp_s,
                        duration_s=n.duration_s,
                        level=n.level,
                        message=n.message,
                    )
                    for n in sync_result.notes
                ],
            )
        )

    response = SyncAnalysisResponse(
        task_id=task_id,
        status="completed",
        progress=1.0,
        results=results,
    )
    _task_store[task_id] = response.model_dump()

    return response


@router.get(
    "/sync/result/{task_id}",
    response_model=SyncAnalysisResponse,
)
async def get_sync_result(
    task_id: str,
) -> SyncAnalysisResponse:
    """Get the result of a sync analysis task."""
    if task_id not in _task_store:
        raise HTTPException(404, "Task not found")
    return SyncAnalysisResponse(**_task_store[task_id])


@router.post("/sync/apply", response_model=SyncApplyResponse)
async def apply_sync(
    request: SyncApplyRequest,
) -> SyncApplyResponse:
    """Apply sync results with time-stretching."""
    if request.video_id not in _video_store:
        raise HTTPException(404, "Video not found")

    video_info = _video_store[request.video_id]["info"]

    from app.services.sync_engine import SegmentMap
    from app.services.time_stretch import TimeStretchEngine

    stretcher = TimeStretchEngine()
    output_files: dict[str, str] = {}
    all_notes: list[SyncNoteSchema] = []

    output_dir = os.path.join(settings.output_dir, "synced", request.video_id)
    os.makedirs(output_dir, exist_ok=True)

    for stem_result in request.stem_results:
        if stem_result.stem_id not in _stem_store:
            continue

        stem_path = _stem_store[stem_result.stem_id]

        seg_maps = [
            SegmentMap(
                audio_start_s=m.audio_start_s,
                audio_end_s=m.audio_end_s,
                lip_start_s=m.lip_start_s,
                lip_end_s=m.lip_end_s,
                stretch_ratio=m.stretch_ratio,
                confidence=m.confidence,
            )
            for m in stem_result.segment_maps
        ]

        stretched = stretcher.apply_sync(
            audio_path=stem_path,
            segment_maps=seg_maps,
            total_duration_s=video_info.duration_s,
        )

        out_path = os.path.join(output_dir, f"{stem_result.stem_id}_synced.wav")
        stretcher.save(stretched, out_path)
        output_files[stem_result.stem_id] = out_path

        for n in stretched.notes:
            all_notes.append(
                SyncNoteSchema(
                    timestamp_s=n.timestamp_s,
                    duration_s=n.duration_s,
                    level=n.level,
                    message=n.message,
                )
            )

    combined_path = os.path.join(output_dir, "_combined.wav")
    stem_paths = [
        os.path.join(output_dir, f)
        for f in sorted(os.listdir(output_dir))
        if f.endswith("_synced.wav")
    ]
    if stem_paths:
        first, sr = sf.read(stem_paths[0], dtype="float32")
        if first.ndim > 1:
            first = first.mean(axis=1)
        combined = np.zeros_like(first)

        for path in stem_paths:
            audio, _ = sf.read(path, dtype="float32")
            if audio.ndim > 1:
                audio = audio.mean(axis=1)
            length = min(len(combined), len(audio))
            for i in range(length):
                if combined[i] == 0.0:
                    combined[i] = audio[i]

        peak = np.max(np.abs(combined))
        if peak > 0.95:
            combined *= 0.95 / peak

        sf.write(combined_path, combined, sr, subtype="PCM_16")

    output_files["_combined"] = combined_path

    return SyncApplyResponse(output_files=output_files, notes=all_notes)


@router.get("/sync/download/{stem_id}")
async def download_synced_wav(stem_id: str, video_id: str) -> FileResponse:
    """Download a synced WAV file."""
    output_dir = os.path.join(settings.output_dir, "synced", video_id)
    file_path = os.path.join(output_dir, f"{stem_id}_synced.wav")

    if not os.path.exists(file_path):
        raise HTTPException(404, "Synced file not found. Run /sync/apply first.")

    return FileResponse(
        file_path,
        media_type="audio/wav",
        filename=f"{stem_id}_synced.wav",
    )


@router.get("/sync/preview/{video_id}")
async def get_preview_audio(video_id: str) -> FileResponse:
    """Get a single combined WAV of all synced stems for preview with video."""
    output_dir = os.path.join(settings.output_dir, "synced", video_id)
    combined_path = os.path.join(output_dir, "_combined.wav")

    if os.path.exists(combined_path):
        return FileResponse(combined_path, media_type="audio/wav")

    if not os.path.isdir(output_dir):
        raise HTTPException(404, "No synced files found. Run /sync/apply first.")

    stem_files = [
        os.path.join(output_dir, f)
        for f in sorted(os.listdir(output_dir))
        if f.endswith("_synced.wav")
    ]
    if not stem_files:
        raise HTTPException(404, "No synced stem files found.")

    first, sr = sf.read(stem_files[0], dtype="float32")
    if first.ndim > 1:
        first = first.mean(axis=1)
    combined = first.copy()

    for path in stem_files[1:]:
        audio, _ = sf.read(path, dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        length = min(len(combined), len(audio))
        combined[:length] += audio[:length]

    peak = np.max(np.abs(combined))
    if peak > 1.0:
        combined /= peak

    sf.write(combined_path, combined, sr, subtype="PCM_16")

    return FileResponse(combined_path, media_type="audio/wav")


@router.get("/waveform/{stem_id}")
async def get_waveform(
    stem_id: str, points: int = 800, synced: bool = False, video_id: str = ""
) -> dict:
    """Get waveform peak data for rendering.

    Args:
        stem_id: Stem identifier
        points: Number of data points (width in pixels)
        synced: If True, return waveform of synced file
        video_id: Required if synced=True
    """
    if synced and video_id:
        file_path = os.path.join(
            settings.output_dir, "synced", video_id, f"{stem_id}_synced.wav"
        )
    elif stem_id in _stem_store:
        file_path = _stem_store[stem_id]
    else:
        raise HTTPException(404, "Stem not found")

    if not os.path.exists(file_path):
        raise HTTPException(404, "Audio file not found")

    audio, sr = sf.read(file_path, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    total_samples = len(audio)
    samples_per_point = max(1, total_samples // points)

    peaks: list[list[float]] = []
    for i in range(0, total_samples, samples_per_point):
        chunk = audio[i : i + samples_per_point]
        if len(chunk) > 0:
            peaks.append(
                [round(float(np.min(chunk)), 4), round(float(np.max(chunk)), 4)]
            )

    return {
        "stem_id": stem_id,
        "sample_rate": sr,
        "duration_s": round(total_samples / sr, 3),
        "points": len(peaks),
        "peaks": peaks,
    }
