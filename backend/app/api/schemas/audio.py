"""Pydantic schemas for audio API endpoints."""

from enum import Enum

from pydantic import BaseModel, Field


class AudioFormat(str, Enum):
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    OGG = "ogg"
    AAC = "aac"


class StemType(str, Enum):
    VOCALS = "vocals"
    DRUMS = "drums"
    BASS = "bass"
    OTHER = "other"


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    duration_seconds: float
    sample_rate: int
    channels: int
    format: AudioFormat


class SeparationRequest(BaseModel):
    file_id: str
    stems: list[StemType] = Field(
        default=[StemType.VOCALS, StemType.DRUMS, StemType.BASS, StemType.OTHER],
        description="Which stems to extract",
    )


class SeparationResult(BaseModel):
    task_id: str
    status: str
    stems: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of stem name to download URL",
    )
    progress: float = Field(default=0.0, ge=0.0, le=1.0)


class EffectConfig(BaseModel):
    type: str = Field(
        description="Effect type: eq, compression, reverb, noise_reduction, normalize"
    )
    params: dict = Field(default_factory=dict)


class EffectsRequest(BaseModel):
    file_id: str
    effects: list[EffectConfig]


class TranscriptionResult(BaseModel):
    text: str
    language: str
    segments: list[dict] = Field(
        default_factory=list,
        description="Timestamped text segments",
    )
