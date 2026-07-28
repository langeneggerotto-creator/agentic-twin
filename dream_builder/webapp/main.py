"""Local web UI for Dream Builder — a thin FastAPI layer over the existing
store/planner/resources/reflector/executor modules. No auth: this is a
single local user's personal tool. Stays local-first per CLAUDE.md — the
only network calls this makes are the same ones the CLI already makes
(Ollama via llm_client, web search via web_lookup, and the opt-in Claude
Code `build` step)."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .. import service, store
from ..executor import ClaudeCodeError
from ..llm_client import OllamaError
from ..projections import project_dream
from ..reflector import reflect
from ..resources import find_resources
from ..scaling import plan_scaling
from ..util import slugify
from . import jobs

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Dream Builder")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.exception_handler(OllamaError)
def _ollama_error_handler(request, exc):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=503, content={"error": str(exc)})


@app.exception_handler(ClaudeCodeError)
def _claude_error_handler(request, exc):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=503, content={"error": str(exc)})


class DreamCreate(BaseModel):
    title: str
    description: str


class StepUpdate(BaseModel):
    done: bool


class BuildRequest(BaseModel):
    dir: str | None = None
    permission_mode: str = "acceptEdits"


def _require_dream(dream_id):
    dream = store.get_dream(dream_id)
    if dream is None:
        raise HTTPException(status_code=404, detail=f"No dream with id '{dream_id}'.")
    return dream


def _summarize(dream):
    plan = dream.get("plan") or []
    return {
        "id": dream["id"],
        "title": dream["title"],
        "status": dream["status"],
        "created_at": dream["created_at"],
        "steps_done": sum(1 for s in plan if s["done"]),
        "steps_total": len(plan),
    }


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/dreams")
def list_dreams():
    return [_summarize(d) for d in store.load_dreams()]


@app.post("/api/dreams")
def create_dream(body: DreamCreate):
    return service.create_dream_with_hints(body.title, body.description)


@app.get("/api/dreams/{dream_id}")
def get_dream(dream_id: str):
    return _require_dream(dream_id)


@app.post("/api/dreams/{dream_id}/plan")
def plan_dream(dream_id: str):
    dream = _require_dream(dream_id)
    return service.plan_dream(dream)


@app.post("/api/dreams/{dream_id}/resources")
def resources_for_dream(dream_id: str):
    dream = _require_dream(dream_id)
    return {"resources": find_resources(dream)}


@app.patch("/api/dreams/{dream_id}/steps/{step}")
def update_step(dream_id: str, step: int, body: StepUpdate):
    dream = _require_dream(dream_id)
    idx = step - 1
    if idx < 0 or idx >= len(dream["plan"]):
        raise HTTPException(status_code=400, detail="Step out of range.")
    dream["plan"][idx]["done"] = body.done
    if dream["plan"] and all(s["done"] for s in dream["plan"]):
        dream["status"] = "done"
    elif dream["status"] == "done":
        dream["status"] = "in_progress"
    store.update_dream(dream)
    return dream


@app.post("/api/dreams/{dream_id}/reflect")
def reflect_on_dream(dream_id: str):
    dream = _require_dream(dream_id)
    text = reflect(dream)
    return {"text": text, "dream": dream}


@app.post("/api/dreams/{dream_id}/projection")
def project_dream_endpoint(dream_id: str):
    dream = _require_dream(dream_id)
    return {"projection": project_dream(dream)}


@app.post("/api/dreams/{dream_id}/scaling")
def plan_scaling_endpoint(dream_id: str):
    dream = _require_dream(dream_id)
    return {"scaling": plan_scaling(dream)}


@app.post("/api/dreams/{dream_id}/build", status_code=202)
def build_dream(dream_id: str, body: BuildRequest | None = None):
    body = body or BuildRequest()
    dream = _require_dream(dream_id)
    target_dir = Path(body.dir) if body.dir else Path("builds") / f"{dream['id']}-{slugify(dream['title'])}"
    job_id = jobs.start_build(dream, target_dir, permission_mode=body.permission_mode)
    return {"job_id": job_id, "target_dir": str(target_dir), "status": "running"}


@app.get("/api/builds/{job_id}")
def get_build(job_id: str):
    job = jobs.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"No build job with id '{job_id}'.")
    return job
