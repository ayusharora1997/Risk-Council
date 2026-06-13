"""FastAPI application — AI Risk Council backend API."""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path so relative imports work when running
# the API from any working directory.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import sessions, providers, exports, attachments


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield  # startup / shutdown hooks go here in Phase 2


app = FastAPI(
    title="AI Risk Council",
    description="Multi-model AI governance policy generation and review platform.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # CRA / alternative
        "https://*.vercel.app",    # Vercel preview + production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(sessions.router,     prefix="/api/sessions",     tags=["Sessions"])
app.include_router(providers.router,    prefix="/api/providers",    tags=["Providers"])
app.include_router(exports.router,      prefix="/api/sessions",     tags=["Exports"])
app.include_router(attachments.router,  prefix="/api/attachments",  tags=["Attachments"])


@app.get("/api/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "AI Risk Council API", "version": "1.0.0"}
