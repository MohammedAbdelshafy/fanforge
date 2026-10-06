"""Gallery builder: emits GALLERY.md + assets/ for a finished job dir."""

from datetime import datetime, timezone
from pathlib import Path

from .jobs import ASSETS_DIR, load_jobs


def _md_escape(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def build_gallery(job_dir, project=""):
    """Write GALLERY.md into *job_dir*. Returns the Path of GALLERY.md."""
    job_dir = Path(job_dir)
    assets_dir = job_dir / ASSETS_DIR
    assets_dir.mkdir(parents=True, exist_ok=True)

    jobs = load_jobs(job_dir)
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")

    done = sum(1 for j in jobs if j.get("status") == "done")
    failed = sum(1 for j in jobs if j.get("status") == "failed")
    backends = sorted({j.get("backend") for j in jobs if j.get("backend")})

    lines = [
        f"# FanForge Gallery{f' — {project}' if project else ''}",
        "",
        f"Generated: {generated} (UTC)",
        f"Jobs: {len(jobs)} total, {done} done, {failed} failed",
        f"Backend(s): {', '.join(backends) if backends else '(none ran yet)'}",
        "",
        "> Assets below are the output of the backend(s) listed above. "
        "The built-in `mock` backend produces deterministic placeholder SVGs — "
        "not AI-generated imagery.",
        "",
        "| Item | Kind | Prompt | Asset | Status |",
        "| ---- | ---- | ------ | ----- | ------ |",
    ]
    for job in jobs:
        asset = job.get("asset")
        if asset:
            asset_ref = f"./{asset}"
            asset_cell = f"![{job['item_id']}]({asset_ref})"
        else:
            asset_cell = "—"
        lines.append(
            f"| {_md_escape(job['item_id'])} "
            f"| {_md_escape(job['kind'])} "
            f"| {_md_escape(job['prompt'])} "
            f"| {asset_cell} "
            f"| {_md_escape(job['status'])} |"
        )
    lines.append("")

    gallery_path = job_dir / "GALLERY.md"
    gallery_path.write_text("\n".join(lines), encoding="utf-8")
    return gallery_path
