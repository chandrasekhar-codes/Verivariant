from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import DISCLAIMER, get_settings
from app.jobs import purge_expired
from app.routes import analysis, health, upload

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    purge_expired(settings)
    yield
    purge_expired(settings)


app = FastAPI(
    title="GENESIS",
    description=(
        "GENESIS — Multi-Agent Genomic Intelligence. "
        "Analyze genomic variants with evidence retrieval, AI reasoning, and claim-level verification. "
        + DISCLAIMER
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "GENESIS",
        "subtitle": "Multi-Agent Genomic Intelligence",
        "tagline": "From genomic variants to evidence-backed insights.",
        "status": "online",
        "disclaimer": DISCLAIMER,
    }
