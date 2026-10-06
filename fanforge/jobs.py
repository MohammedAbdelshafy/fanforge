"""Job queue: expansion from a brief, persistence in jobs.jsonl, execution.

Each line of jobs.jsonl is one job::

    {
        "job_id": "job-001-a3f9c1d2",
        "item_id": "hero-01",
        "prompt": "...",
        "kind": "image",
        "aspect": "16:9",
        "notes": null,
        "status": "queued",        # queued -> running -> done | failed
        "backend": null,
        "asset": null,             # relative path inside the job dir once done
        "error": null,
        "created_at": "2026-10-06T10:00:00+00:00",
        "finished_at": null
    }
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

JOBS_FILE = "jobs.jsonl"
ASSETS_DIR = "assets"

STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_FAILED = "failed"


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_job_id(item_id, index, prompt):
    """Deterministic job id derived from item id, position, and prompt."""
    digest = hashlib.sha256(
        f"{item_id}|{index}|{prompt}".encode("utf-8")
    ).hexdigest()[:8]
    return f"job-{index + 1:03d}-{digest}"


def queue_jobs(brief, out_dir):
    """Expand a validated brief into queued jobs and persist jobs.jsonl.

    Returns the list of job dicts. Re-queueing overwrites any existing queue.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = []
    for index, item in enumerate(brief["items"]):
        jobs.append(
            {
                "job_id": make_job_id(item["id"], index, item["prompt"]),
                "item_id": item["id"],
                "prompt": item["prompt"],
                "kind": item["kind"],
                "aspect": item.get("aspect"),
                "notes": item.get("notes"),
                "status": STATUS_QUEUED,
                "backend": None,
                "asset": None,
                "error": None,
                "created_at": _now(),
                "finished_at": None,
            }
        )
    save_jobs(out_dir, jobs)
    return jobs


def load_jobs(job_dir):
    """Load the job queue from <job_dir>/jobs.jsonl."""
    path = Path(job_dir) / JOBS_FILE
    if not path.exists():
        raise FileNotFoundError(f"no job queue found at {path} (run 'fanforge queue' first)")
    jobs = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                jobs.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"corrupt jobs.jsonl line {line_no}: {exc}") from exc
    return jobs


def save_jobs(job_dir, jobs):
    """Persist the job queue (one job per line)."""
    path = Path(job_dir) / JOBS_FILE
    with path.open("w", encoding="utf-8") as handle:
        for job in jobs:
            handle.write(json.dumps(job, ensure_ascii=False) + "\n")


def run_queued_jobs(job_dir, backend):
    """Run every queued job through *backend*, updating statuses in place.

    Returns (done_count, failed_count). Statuses move queued -> running ->
    done (or failed). Non-queued jobs are left untouched.
    """
    job_dir = Path(job_dir)
    assets_dir = job_dir / ASSETS_DIR
    assets_dir.mkdir(parents=True, exist_ok=True)

    jobs = load_jobs(job_dir)
    done = failed = 0
    for job in jobs:
        if job.get("status") != STATUS_QUEUED:
            continue
        job["status"] = STATUS_RUNNING
        job["backend"] = backend.name
        save_jobs(job_dir, jobs)
        try:
            asset_path = backend.generate(job, assets_dir)
            job["asset"] = str(Path(asset_path).relative_to(job_dir))
            job["error"] = None
            job["status"] = STATUS_DONE
            job["finished_at"] = _now()
            done += 1
        except Exception as exc:  # a backend failure marks the job failed, not the run
            job["asset"] = None
            job["error"] = str(exc)
            job["status"] = STATUS_FAILED
            job["finished_at"] = _now()
            failed += 1
        save_jobs(job_dir, jobs)
    return done, failed
