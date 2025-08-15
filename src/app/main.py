from fastapi import FastAPI

from .config import settings

app = FastAPI(title="IELTS Scoring PoC", version="0.1.0")


@app.get("/healthz")
def health() -> dict[str, str]:
	return {"status": "ok", "env": settings.app_env}


@app.get("/readyz")
def ready() -> dict[str, str]:
	# Phase 0: trivial readiness
	return {"status": "ready"}
