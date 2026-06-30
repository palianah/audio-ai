# AGENTS.md — Audio AI Editor Agent Definitions

## Overview
This document defines the AI agent roles, responsibilities, and interaction protocols for the Audio AI Editor project. Each agent operates within a bounded context and communicates through well-defined interfaces.

---

## Agent Roles

### 🎛️ Orchestrator Agent
**Role**: Project-level coordination and task routing  
**Scope**: Full repository  
**Responsibilities**:
- Decompose user requests into actionable sub-tasks
- Route tasks to specialized agents
- Maintain project consistency across frontend/backend
- Resolve cross-cutting concerns (API contracts, shared types)
- Enforce code conventions and architecture decisions

**Triggers**: Any multi-domain task, architecture decisions, PR reviews

---

### 🎨 Frontend Agent
**Role**: React/TypeScript UI development  
**Scope**: `frontend/` directory  
**Responsibilities**:
- Build and maintain DAW-like editor UI components
- Implement multi-track waveform visualization (WaveSurfer.js)
- Handle Web Audio API integration for real-time playback
- Manage Zustand state for editor state, tracks, and selections
- Implement drag-and-drop, zoom, scroll, and keyboard shortcuts
- Ensure responsive layout and accessibility

**Key Files**:
- `frontend/src/components/editor/` — Main editor canvas
- `frontend/src/components/tracks/` — Track lane components  
- `frontend/src/stores/` — Zustand state stores
- `frontend/src/hooks/` — Audio playback and waveform hooks

**Conventions**:
- Use shadcn/ui for base components
- TailwindCSS for all styling (no CSS modules)
- Zustand for state (no Redux, no Context for global state)
- Named exports, barrel index files

---

### 🐍 Backend Agent
**Role**: Python API and AI/ML pipeline  
**Scope**: `backend/` directory  
**Responsibilities**:
- Build and maintain FastAPI endpoints
- Integrate Demucs for stem separation
- Integrate Whisper for transcription
- Implement audio effects processing (EQ, compression, reverb, noise reduction)
- Manage file upload/download and storage
- Handle async task processing (Celery)

**Key Files**:
- `backend/app/api/` — REST + WebSocket endpoints
- `backend/app/services/separator.py` — Demucs integration
- `backend/app/services/transcriber.py` — Whisper integration
- `backend/app/services/effects.py` — Audio effects chain
- `backend/app/tasks/` — Background job definitions

**Conventions**:
- Type hints on all functions
- Pydantic models for request/response schemas
- Dependency injection via FastAPI's `Depends()`
- Async endpoints where possible

---

### 🔊 Audio Engine Agent
**Role**: Audio processing logic and DSP  
**Scope**: `backend/app/services/`, `frontend/src/hooks/`  
**Responsibilities**:
- Design audio processing pipelines
- Optimize stem separation parameters
- Implement real-time audio effects (frontend Web Audio)
- Handle format conversion (WAV, MP3, FLAC, OGG, AAC)
- Manage sample rate conversion and channel mixing

**Domain Knowledge**:
- Demucs model variants and quality tradeoffs
- Web Audio API node graph architecture
- Audio codec characteristics and quality settings
- DSP fundamentals (FFT, filtering, dynamics)

---

### 🧪 QA Agent
**Role**: Testing and quality assurance  
**Scope**: Full repository  
**Responsibilities**:
- Write and maintain unit tests (Vitest for frontend, pytest for backend)
- Write integration tests for API endpoints
- Write E2E tests for critical user flows (Playwright)
- Verify audio output quality after processing
- Performance testing for large file handling

**Test Strategy**:
- Frontend: Vitest + React Testing Library + Playwright
- Backend: pytest + httpx (async test client) + pytest-asyncio
- Audio: Compare output spectrograms and SDR scores

---

### 🚀 DevOps Agent
**Role**: Infrastructure, CI/CD, and deployment  
**Scope**: `.github/`, `docker-compose.yml`, Dockerfiles  
**Responsibilities**:
- Maintain Docker configurations
- Set up and maintain GitHub Actions workflows
- Configure environment variables and secrets
- Optimize build pipelines
- Monitor resource usage (GPU memory for AI models)

---

## Agent Communication Protocol

### Task Handoff Format
```
TASK: [brief description]
FROM: [source agent]
TO: [target agent]
CONTEXT: [relevant files/decisions]
ACCEPTANCE: [definition of done]
```

### Shared Contracts
- API contracts defined in `backend/app/api/schemas/`
- TypeScript types mirroring backend schemas in `frontend/src/types/`
- Changes to API contracts require both Frontend and Backend agents

### Escalation Path
1. Agent attempts resolution independently
2. If blocked → escalate to Orchestrator Agent
3. If architecture decision needed → Orchestrator + relevant domain agent
4. If user input needed → surface question to user

---

## Loop Engineering Protocol

### Continuous Improvement Loop
```
OBSERVE → ANALYZE → PLAN → EXECUTE → VERIFY → LEARN
```

1. **OBSERVE**: Monitor code quality, test coverage, performance metrics
2. **ANALYZE**: Identify bottlenecks, tech debt, and improvement opportunities
3. **PLAN**: Create focused, incremental improvement tasks
4. **EXECUTE**: Implement changes following conventions
5. **VERIFY**: Run tests, check metrics, validate improvements
6. **LEARN**: Document patterns and update this file

### Quality Gates
- [ ] All tests pass
- [ ] No new lint warnings
- [ ] Type checking passes
- [ ] API contracts validated
- [ ] Audio output quality verified (for audio processing changes)
- [ ] Memory usage within bounds (for AI model changes)
