# CLAUDE.md — Audio AI Editor

## Project Overview
**Audio AI** is an AI-powered audio editing platform that automatically processes, separates, and edits audio files and recordings. It provides a professional DAW-like UI/UX for multi-track editing with AI-assisted automation.

## Tech Stack

### Frontend
- **Framework**: React 18+ with TypeScript
- **Package Manager**: pnpm 11
- **Build Tool**: Vite
- **Styling**: TailwindCSS + shadcn/ui
- **Audio Visualization**: WaveSurfer.js (multitrack plugin) for waveform rendering
- **State Management**: Zustand
- **Icons**: Lucide React
- **Audio Engine**: Web Audio API for real-time processing

### Backend
- **Framework**: Python 3.11+ with FastAPI
- **AI/ML**: 
  - Demucs v4 (HTDemucs) — stem separation (vocals, drums, bass, other)
  - OpenAI Whisper — speech-to-text / transcription
  - librosa — audio analysis & feature extraction
  - noisereduce — AI noise reduction
- **Audio Processing**: FFmpeg, pydub, soundfile
- **Task Queue**: Celery + Redis (for async heavy processing)
- **API**: REST + WebSocket (real-time progress updates)

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Storage**: Local filesystem + S3-compatible (optional)
- **CI/CD**: GitHub Actions

## Project Structure
```
audio-ai/
├── CLAUDE.md                    # This file — AI context
├── AGENTS.md                    # Agent roles & responsibilities
├── README.md                    # Project documentation
├── .github/                     # GitHub Actions workflows
│   └── workflows/
├── frontend/                    # React + TypeScript app
│   ├── src/
│   │   ├── components/          # UI components
│   │   │   ├── editor/          # DAW editor components
│   │   │   ├── tracks/          # Multi-track components
│   │   │   ├── toolbar/         # Editing toolbar
│   │   │   └── ui/              # shadcn/ui components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── stores/              # Zustand stores
│   │   ├── services/            # API service layer
│   │   ├── types/               # TypeScript types
│   │   └── utils/               # Utility functions
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── backend/                     # Python FastAPI server
│   ├── app/
│   │   ├── api/                 # API endpoints
│   │   ├── core/                # Core config & settings
│   │   ├── models/              # Data models
│   │   ├── services/            # Business logic
│   │   │   ├── separator.py     # Demucs stem separation
│   │   │   ├── editor.py        # Audio editing operations
│   │   │   ├── transcriber.py   # Whisper transcription
│   │   │   └── effects.py       # Audio effects processing
│   │   └── tasks/               # Celery async tasks
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Key Architecture Decisions
1. **Stem Separation**: Use Demucs HTDemucs fine-tuned model (`htdemucs_ft`) for highest quality 4-stem separation
2. **Waveform Rendering**: WaveSurfer.js with multitrack plugin — each separated stem gets its own waveform track
3. **Real-time Processing**: WebSocket for progress updates during heavy AI processing
4. **Non-destructive Editing**: All edits are stored as operations; original files are never modified
5. **Chunked Processing**: Large files are processed in segments to manage memory

## Code Conventions
- **Frontend**: ESLint 9 flat config + typescript-eslint, named exports, barrel files for components
- **Backend**: Black + isort + mypy, type hints everywhere, docstrings on public functions
- **Git**: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)
- **Branch Strategy**: `main` (stable) → `develop` → feature branches (`feat/xxx`)

## AI Agent Guidelines
- Always read this file before making changes
- Follow existing code patterns and conventions
- Run tests before committing
- Keep the frontend and backend loosely coupled via API contracts
- Prefer small, focused PRs over large monolithic changes
