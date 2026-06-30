"""Pydantic schemas for video and sync API endpoints."""

from pydantic import BaseModel, Field


class VideoUploadResponse(BaseModel):
    video_id: str
    filename: str
    duration_s: float
    fps: float
    width: int
    height: int
    has_audio: bool


class SyncRequest(BaseModel):
    video_id: str
    stem_ids: list[str] = Field(description="List of uploaded audio stem IDs to sync")


class SyncNoteSchema(BaseModel):
    timestamp_s: float
    duration_s: float
    level: str = Field(description="info, warning, or error")
    message: str


class SegmentMapSchema(BaseModel):
    audio_start_s: float
    audio_end_s: float
    lip_start_s: float
    lip_end_s: float
    stretch_ratio: float
    confidence: float


class StemSyncResult(BaseModel):
    stem_id: str
    offset_ms: int
    matched_face_id: int
    overall_confidence: float
    segment_maps: list[SegmentMapSchema] = Field(default_factory=list)
    notes: list[SyncNoteSchema] = Field(default_factory=list)


class SyncAnalysisResponse(BaseModel):
    task_id: str
    status: str = Field(
        default="pending",
        description="pending, processing, completed, failed",
    )
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    results: list[StemSyncResult] = Field(default_factory=list)


class SyncApplyRequest(BaseModel):
    video_id: str
    stem_results: list[StemSyncResult] = Field(
        description="Sync results (possibly user-adjusted) to apply"
    )


class SyncApplyResponse(BaseModel):
    output_files: dict[str, str] = Field(
        description="Mapping of stem_id to processed audio URL"
    )
    notes: list[SyncNoteSchema] = Field(default_factory=list)
