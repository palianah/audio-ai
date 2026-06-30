# Harness Engineering — Audio AI Editor

## Purpose
Define the AI agent action space, tool definitions, observation formatting, and execution patterns for higher task completion rates across the Audio AI Editor project.

---

## Agent Harness Architecture

### Action Space Definition
Each agent operates within a bounded action space to prevent scope creep and ensure focused execution.

```
┌─────────────────────────────────────────────┐
│                ORCHESTRATOR                  │
│  Actions: route, decompose, validate, merge │
├──────────┬──────────┬──────────┬────────────┤
│ FRONTEND │ BACKEND  │  AUDIO   │   DEVOPS   │
│ ui, state│ api, ml  │ dsp, fmt │ ci, docker │
│ waveform │ tasks    │ pipeline │ deploy     │
└──────────┴──────────┴──────────┴────────────┘
```

### Tool Definitions Per Agent

#### Frontend Agent Tools
| Tool | Input | Output | Side Effects |
|------|-------|--------|-------------|
| `create_component` | name, props, type | `.tsx` file | Updates barrel exports |
| `create_hook` | name, dependencies | `.ts` file | Updates hooks index |
| `update_store` | store name, slice | Updated store | Type regeneration |
| `add_route` | path, component | Router update | Nav update |

#### Backend Agent Tools
| Tool | Input | Output | Side Effects |
|------|-------|--------|-------------|
| `create_endpoint` | method, path, schema | Route handler | Schema generation |
| `create_service` | name, interface | Service class | DI registration |
| `create_task` | name, params | Celery task | Task registration |
| `add_model` | name, fields | Pydantic model | Migration needed |

#### Audio Engine Agent Tools
| Tool | Input | Output | Side Effects |
|------|-------|--------|-------------|
| `create_pipeline` | steps, config | Processing chain | None |
| `add_effect` | type, params | Effect node | Pipeline update |
| `convert_format` | input, output_fmt | Converted file | Storage |
| `analyze_audio` | file, features | Analysis JSON | None |

---

## Observation Formatting

### Structured Output Format
All agent observations follow this schema:
```json
{
  "agent": "agent_name",
  "action": "action_performed",
  "status": "success|failure|partial",
  "artifacts": ["list of created/modified files"],
  "metrics": {
    "duration_ms": 0,
    "files_changed": 0,
    "tests_affected": 0
  },
  "next_steps": ["suggested follow-up actions"],
  "blockers": ["any blocking issues"]
}
```

### Error Recovery Patterns
1. **Retry with backoff**: For transient failures (network, API rate limits)
2. **Fallback strategy**: For model loading failures (try smaller model variant)
3. **Graceful degradation**: For GPU OOM (switch to CPU processing)
4. **Escalation**: For architecture-level blockers (hand off to orchestrator)

---

## Execution Patterns

### Sequential Pipeline
```
Input → Validate → Process → Verify → Output
```
Used for: file uploads, format conversion, simple edits

### Parallel Fan-Out
```
Input → [Task A, Task B, Task C] → Merge → Output
```
Used for: multi-stem separation, batch processing

### Event-Driven Reactive
```
Event → Filter → Transform → Side Effect → Notify
```
Used for: real-time playback, waveform updates, WebSocket messages

### Iterative Refinement
```
Input → Process → Evaluate → (if quality < threshold) → Adjust → Process
```
Used for: noise reduction optimization, auto-mastering

---

## Safety Constraints
- **Memory Ceiling**: Demucs max segment size = 40s per chunk on 8GB GPU
- **File Size Limit**: Max upload 500MB per file
- **Concurrent Tasks**: Max 3 parallel stem separations per instance
- **Timeout**: AI processing tasks timeout at 10 minutes
- **Rollback**: All file operations are reversible (original never deleted)

## Performance Targets
| Operation | Target Latency | Acceptable |
|-----------|---------------|------------|
| File upload (100MB) | < 5s | < 10s |
| Stem separation (3min song) | < 60s (GPU) | < 180s (CPU) |
| Waveform render | < 500ms | < 1s |
| Effect preview | < 100ms | < 250ms |
| Transcription (3min) | < 30s | < 60s |
