"""In-memory tracking for background `build` runs kicked off from the web
UI. A single local user, single process — no persistence beyond the log
file on disk needed."""

import threading
import uuid
from pathlib import Path

from .. import executor

_LOG_TAIL_BYTES = 200_000

_jobs = {}


def start_build(dream, target_dir, permission_mode="acceptEdits"):
    target_dir = Path(target_dir)
    job_id = uuid.uuid4().hex[:8]
    log_path = target_dir / ".dream_builder_build.log"
    _jobs[job_id] = {
        "status": "running",
        "log_path": log_path,
        "target_dir": target_dir,
        "error": None,
    }

    def run():
        try:
            executor.build_with_claude_code(
                dream, target_dir, permission_mode=permission_mode, log_path=log_path
            )
            _jobs[job_id]["status"] = "done"
        except executor.ClaudeCodeError as e:
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"] = str(e)

    threading.Thread(target=run, daemon=True).start()
    return job_id


def get_job(job_id):
    job = _jobs.get(job_id)
    if job is None:
        return None
    log = ""
    if job["log_path"].exists():
        data = job["log_path"].read_bytes()[-_LOG_TAIL_BYTES:]
        log = data.decode("utf-8", errors="replace")
    return {
        "status": job["status"],
        "log": log,
        "error": job["error"],
        "target_dir": str(job["target_dir"]),
    }
