"""Start the FastAPI server — local dev and Railway/production."""
import os
import uvicorn

if __name__ == "__main__":
    port     = int(os.getenv("PORT", "8000"))
    is_prod  = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("PRODUCTION"))

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        reload=not is_prod,
        reload_dirs=(
            ["api", "agents", "engine", "providers", "models", "storage", "exports"]
            if not is_prod else None
        ),
    )
