from app.api.routes.sync import router as sync_router
from app.core.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Audio AI Editor",
    description="AI-powered audio editing API with stem separation, transcription, sync, and effects processing",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sync_router)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "version": "0.1.0"}
