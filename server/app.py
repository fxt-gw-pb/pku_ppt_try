"""Minimal FastAPI backend that exposes the manuscript → deck pipeline.

Endpoints:
    POST /api/jobs                — create a new generation job
    GET  /api/jobs/{job_id}       — poll job status
    GET  /api/jobs/{job_id}/download — download the deck as .zip (when done)
    GET  /api/jobs/{job_id}/preview  — redirect to the rendered deck index.html

Static mounts:
    /decks/{job_id}/…  serves the materialized deck files (so /preview works)
    /                  serves the web/ frontend demo (textarea + Generate UI)

Job state is persisted as JSON in data/jobs/<id>.json so it survives restarts.
Decks land in outputs/<id>/, zips at outputs/<id>.zip.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse, RedirectResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from src.exporter import export_deck, zip_deck  # noqa: E402
from src.llm import generate_slide_json  # noqa: E402
from src.renderer import compile_to_pku  # noqa: E402
from src.schema import validate_slide_json  # noqa: E402

OUTPUT_DIR = (REPO_ROOT / os.environ.get("OUTPUT_DIR", "outputs")).resolve()
JOB_DIR = (REPO_ROOT / os.environ.get("JOB_DIR", "data/jobs")).resolve()
MAX_INPUT_CHARS = int(os.environ.get("MAX_INPUT_CHARS", "30000"))

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
JOB_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="PKU PPT Generator", version="0.1.0")

# CORS — only the GitHub Pages frontend and local dev are allowed to call the
# API from a browser. (curl / server-to-server traffic isn't affected; CORS is
# enforced by browsers.) Override via env CORS_ORIGINS="a,b,c" if you add a
# new frontend host.
_default_origins = [
    "https://fxt-gw-pb.github.io",
    "http://127.0.0.1:8787",
    "http://localhost:8787",
    "http://127.0.0.1:8090",
    "http://localhost:8090",
]
_env_origins = os.environ.get("CORS_ORIGINS", "").strip()
ALLOWED_ORIGINS = (
    [o.strip() for o in _env_origins.split(",") if o.strip()]
    if _env_origins
    else _default_origins
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobRequest(BaseModel):
    manuscript: str
    style: str | None = "academic"


def _job_path(job_id: str) -> Path:
    return JOB_DIR / f"{job_id}.json"


def _save_job(job: dict[str, Any]) -> None:
    _job_path(job["job_id"]).write_text(
        json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _load_job(job_id: str) -> dict[str, Any] | None:
    p = _job_path(job_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_job(job_id: str, manuscript: str) -> None:
    job = _load_job(job_id) or {"job_id": job_id}
    try:
        job["status"] = "running"
        job["started_at"] = _now()
        _save_job(job)

        generic = generate_slide_json(manuscript, {})
        errors = validate_slide_json(generic)
        if errors:
            raise RuntimeError(
                "slide_json validation failed: " + "; ".join(errors)
            )
        pku = compile_to_pku(generic)

        deck_out = OUTPUT_DIR / job_id
        export_deck(pku, deck_out, force=True)
        (deck_out / "data" / "slide.json").write_text(
            json.dumps(generic, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        zip_path = OUTPUT_DIR / f"{job_id}.zip"
        zip_deck(deck_out, zip_path)

        job["status"] = "done"
        job["finished_at"] = _now()
        job["download_url"] = f"/api/jobs/{job_id}/download"
        job["preview_url"] = f"/api/jobs/{job_id}/preview"
        job["slide_count"] = len(pku.get("slides", []))
        job["deck_path"] = str(deck_out.relative_to(REPO_ROOT))
        job["zip_path"] = str(zip_path.relative_to(REPO_ROOT))
        _save_job(job)
    except Exception as e:  # noqa: BLE001 — failure surfaces in job state
        job = _load_job(job_id) or {"job_id": job_id}
        job["status"] = "failed"
        job["finished_at"] = _now()
        job["error"] = f"{type(e).__name__}: {e}"
        job["traceback"] = traceback.format_exc()
        _save_job(job)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "provider": os.environ.get("LLM_PROVIDER", "mock"),
        "max_input_chars": MAX_INPUT_CHARS,
    }


@app.post("/api/jobs")
def create_job(req: JobRequest) -> dict[str, Any]:
    manuscript = (req.manuscript or "").strip()
    if not manuscript:
        raise HTTPException(status_code=400, detail="manuscript is empty")
    if len(manuscript) > MAX_INPUT_CHARS:
        raise HTTPException(
            status_code=413,
            detail=(
                f"manuscript exceeds MAX_INPUT_CHARS={MAX_INPUT_CHARS} "
                f"(got {len(manuscript)})"
            ),
        )

    job_id = uuid.uuid4().hex[:12]
    job = {
        "job_id": job_id,
        "status": "pending",
        "created_at": _now(),
        "style": req.style or "academic",
        "download_url": None,
        "preview_url": None,
        "error": None,
    }
    _save_job(job)

    threading.Thread(
        target=_run_job, args=(job_id, manuscript), daemon=True
    ).start()
    return job


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    job = _load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    # Hide the raw traceback from the public response (still in the on-disk file).
    return {k: v for k, v in job.items() if k != "traceback"}


@app.get("/api/jobs/{job_id}/download")
def download_job(job_id: str) -> FileResponse:
    job = _load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job.get("status") != "done":
        raise HTTPException(
            status_code=409, detail=f"job status is {job.get('status')}"
        )
    zip_rel = job.get("zip_path")
    if not zip_rel:
        raise HTTPException(status_code=500, detail="zip path missing in job state")
    zip_path = REPO_ROOT / zip_rel
    if not zip_path.is_file():
        raise HTTPException(status_code=500, detail="output zip missing on disk")
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"pku-deck-{job_id}.zip",
    )


@app.get("/api/jobs/{job_id}/preview")
def preview_job(job_id: str) -> RedirectResponse:
    """Redirect to the deck's index.html served from the /decks static mount."""
    job = _load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job.get("status") != "done":
        raise HTTPException(
            status_code=409, detail=f"job status is {job.get('status')}"
        )
    return RedirectResponse(url=f"/decks/{job_id}/index.html")


# Serve materialized decks so /preview can resolve their fetch('data/slides.json').
app.mount("/decks", StaticFiles(directory=str(OUTPUT_DIR), html=True), name="decks")

# Frontend demo. Mounting at "/" must be last so /api/* and /decks/* still win.
WEB_DIR = REPO_ROOT / "web"
if WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8787"))
    uvicorn.run(app, host=host, port=port)
