"""Command-line interface: fanforge queue | run | gallery."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .backends import registry
from .brief import BriefValidationError, load_brief
from .gallery import build_gallery
from .jobs import load_jobs, queue_jobs, run_queued_jobs


def _existing_job_count(out_dir):
    """Return the number of jobs already queued in *out_dir*, or 0."""
    try:
        return len(load_jobs(out_dir))
    except (FileNotFoundError, ValueError, OSError):
        return 0


def _cmd_queue(args):
    try:
        brief = load_brief(args.brief)
    except BriefValidationError as exc:
        print(f"error: invalid brief: {exc}", file=sys.stderr)
        return 2
    existing = _existing_job_count(args.out)
    if existing:
        print(
            f"note: overwriting {existing} existing job(s) in {args.out}",
            file=sys.stderr,
        )
    try:
        jobs = queue_jobs(brief, args.out)
    except OSError as exc:
        print(f"error: cannot create job directory {args.out!r}: {exc}", file=sys.stderr)
        return 2
    print(f"queued {len(jobs)} job(s) for project {brief['project']!r} in {args.out}")
    for job in jobs:
        print(f"  {job['job_id']}  item={job['item_id']}  kind={job['kind']}")
    return 0


def _cmd_run(args):
    try:
        backend_cls = registry.get(args.backend)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    backend = backend_cls()
    try:
        done, failed = run_queued_jobs(args.dir, backend)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"run complete with backend '{backend.name}': {done} done, {failed} failed")
    if getattr(backend, "mock_output", False):
        print(
            "note: 'mock' backend wrote placeholder SVG assets "
            "(NOT AI-generated imagery) to "
            f"{Path(args.dir) / 'assets'}/",
            file=sys.stderr,
        )
    if failed:
        return 1
    return 0


def _cmd_gallery(args):
    try:
        path = build_gallery(args.dir, project=args.project or "")
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {path}")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="fanforge",
        description="Media-generation orchestration pipeline: brief -> queued jobs -> gallery.",
    )
    parser.add_argument("--version", action="version", version=f"fanforge {__version__}")

    sub = parser.add_subparsers(dest="command", required=True)

    q = sub.add_parser("queue", help="validate a brief and expand it into queued jobs")
    q.add_argument("--brief", required=True, help="path to the brief JSON file")
    q.add_argument("--out", required=True, help="job directory to create (jobs.jsonl)")
    q.set_defaults(func=_cmd_queue)

    r = sub.add_parser("run", help="execute queued jobs through a backend")
    r.add_argument("--dir", required=True, help="job directory created by 'queue'")
    r.add_argument(
        "--backend",
        default="mock",
        help="registered backend name (default: mock; available: "
        + ", ".join(sorted(registry.available())) + ")",
    )
    r.set_defaults(func=_cmd_run)

    g = sub.add_parser("gallery", help="emit GALLERY.md + assets/ for a job directory")
    g.add_argument("--dir", required=True, help="job directory")
    g.add_argument("--project", default="", help="project name shown in the gallery header")
    g.set_defaults(func=_cmd_gallery)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
