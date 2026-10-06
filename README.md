# FanForge

Media-generation **orchestration pipeline**: turn a brief into queued generation
jobs, execute them through a pluggable backend, and emit an asset gallery.

FanForge does not generate imagery by itself. It is the wiring between your
brief, whatever generator you plug in, and the finished gallery. The built-in
`mock` backend produces deterministic placeholder SVGs so the pipeline can be
run end-to-end without API keys; mock output is labeled as mock and is **not**
AI-generated imagery.

## Install

Python 3.9+ with only the standard library. No dependencies.

```bash
git clone https://github.com/MohammedAbdelshafy/fanforge.git
cd fanforge
pip install .          # installs the `fanforge` command
# or run without installing:
python -m fanforge --help
```

## Usage

1. **Queue** — validate a brief and expand it into queued jobs:

```bash
fanforge queue --brief samples/brief.json --out ./job1/
```

This writes `job1/jobs.jsonl` (one job per brief item, `status=queued`).

A brief is a JSON object with `project` (non-empty string) and `items`
(a non-empty list). Each item needs `id`, `prompt`, and `kind`
(`image` | `video` | `audio`); `aspect` (e.g. `16:9`) and `notes` are optional.
Invalid briefs are rejected with an error message.

2. **Run** — execute queued jobs through a backend:

```bash
fanforge run --dir ./job1/ --backend mock
```

Job statuses move `queued → running → done` (or `failed`). Only queued jobs
run; already-finished jobs are left untouched.

3. **Gallery** — emit the gallery index and asset directory:

```bash
fanforge gallery --dir ./job1/ --project "my-project"
```

This writes `job1/GALLERY.md` (per item: id, kind, prompt, asset, status)
and ensures `job1/assets/` exists.

Run the sample end-to-end:

```bash
fanforge queue --brief samples/brief.json --out ./demo/
fanforge run --dir ./demo/
fanforge gallery --dir ./demo/ --project "fanforge-sample-launch"
```

## Backend interface

Backends live in `fanforge/backends/`. A backend is a `GeneratorBackend`
subclass (`fanforge/backends/base.py`):

```python
from fanforge.backends.base import GeneratorBackend

class MyBackend(GeneratorBackend):
    name = "mybackend"                       # used as: --backend mybackend
    description = "wraps the X image API"

    def generate(self, job, assets_dir):
        # job: dict with job_id, item_id, prompt, kind, aspect, notes
        # assets_dir: pathlib.Path (already exists)
        # ... call your generator, save the file into assets_dir ...
        return str(assets_dir / "output.png")  # raise on failure
```

Then register it in `fanforge/backends/registry.py`:

```python
from . import mybackend
register(mybackend.MyBackend.name, mybackend.MyBackend)
```

A backend that raises marks its job `failed` (with the error recorded) and the
run continues with the rest of the queue.

## The `mock` backend

Deterministic placeholder SVG assets derived from a hash of each job's prompt.
Every file is visibly labeled "MOCK PLACEHOLDER — not AI-generated". It exists
only so the queue → run → gallery flow can be tested with no credentials.
Do not present mock output as AI-generated work.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Limits

- The `mock` backend produces placeholders, not real generated media.
- No real generator backends ship with this repo; plug in your own per above.
- Jobs are stored as plain `jobs.jsonl` files — fine for batches, not built
  for concurrent or distributed execution.
- Video/audio jobs run through the same interface; with the mock backend they
  get a placeholder card like any other item.

## License

MIT — see [LICENSE](LICENSE).
