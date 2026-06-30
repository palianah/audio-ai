"""API routes for video-audio sync operations."""

import os
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile

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

    _video_store[video_id] = {
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
    lip_segments = lip_detector.analyze_frames(
        frames, fps=10.0
    )

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

        from app.api.schemas.video import (
            SegmentMapSchema,
            StemSyncResult,
        )

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

    output_dir = os.path.join(
        settings.output_dir, "synced", request.video_id
    )
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

        out_path = os.path.join(
            output_dir, f"{stem_result.stem_id}_synced.wav"
        )
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

    return SyncApplyResponse(
        output_files=output_files, notes=all_notes
    )
