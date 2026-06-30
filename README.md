# 🎵 Audio AI Editor

AI-powered audio editing platform with automatic stem separation, multi-track editing, and professional DAW-like interface.

## Features

- **AI Stem Separation** — Split any audio into vocals, drums, bass, and other instruments using Demucs v4
- **Multi-Track Editor** — Professional DAW-like UI with individual track waveforms, solo/mute, volume control
- **AI Transcription** — Automatic speech-to-text with Whisper
- **Audio Effects** — EQ, compression, reverb, noise reduction, normalization
- **Non-Destructive Editing** — All edits are operations; originals are never modified
- **Format Support** — WAV, MP3, FLAC, OGG, AAC input/output
- **Real-Time Preview** — Web Audio API powered real-time effect preview

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript, Vite, TailwindCSS, shadcn/ui |
| Audio UI | WaveSurfer.js (multitrack), Web Audio API |
| State | Zustand |
| Backend | Python 3.11+, FastAPI |
| AI Models | Demucs v4 (stem separation), Whisper (transcription) |
| Audio | FFmpeg, librosa, pydub, soundfile, noisereduce |
| Task Queue | Celery + Redis |
| Infra | Docker, GitHub Actions |

## Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- FFmpeg
- Docker & Docker Compose (optional)

### Development Setup

```bash
# Clone
git clone https://github.com/palianah/audio-ai.git
cd audio-ai

# Frontend
cd frontend
npm install
npm run dev

# Backend (new terminal)
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Or use Docker
docker compose up --build
```

### Environment Variables
Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

## Project Structure

```
audio-ai/
├── frontend/          # React + TypeScript DAW UI
├── backend/           # FastAPI + AI/ML processing
├── CLAUDE.md          # AI agent project context
├── AGENTS.md          # Agent roles & protocols
├── docker-compose.yml # Full stack orchestration
└── .github/           # CI/CD workflows
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Frontend (React)                │
│  ┌───────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ WaveSurfer│  │  Toolbar  │  │  Track Panel │  │
│  │ Multitrack│  │  Controls │  │  Solo/Mute   │  │
│  └─────┬─────┘  └────┬─────┘  └──────┬───────┘  │
│        │              │               │          │
│        └──────────────┼───────────────┘          │
│                       │ Web Audio API            │
│                       ▼                          │
│              ┌────────────────┐                  │
│              │  Zustand Store │                  │
│              └───────┬────────┘                  │
└──────────────────────┼───────────────────────────┘
                       │ REST / WebSocket
┌──────────────────────┼───────────────────────────┐
│                      ▼                           │
│              ┌────────────────┐                  │
│              │  FastAPI       │  Backend         │
│              │  Endpoints     │                  │
│              └───────┬────────┘                  │
│        ┌─────────────┼─────────────┐             │
│        ▼             ▼             ▼             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Demucs  │  │  Whisper │  │  Effects │       │
│  │  Stems   │  │  STT     │  │  Chain   │       │
│  └──────────┘  └──────────┘  └──────────┘       │
│                       │                          │
│              ┌────────┴────────┐                 │
│              │  Celery + Redis │                 │
│              └─────────────────┘                 │
└──────────────────────────────────────────────────┘
```

## License

MIT
