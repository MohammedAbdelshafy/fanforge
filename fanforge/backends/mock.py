"""Deterministic MOCK backend: produces placeholder SVG files, NOT AI imagery.

The mock exists so the pipeline (queue -> run -> gallery) can be exercised
end-to-end with no API keys and no network access. Every asset is derived
from a hash of the job's prompt and is plainly labeled "MOCK PLACEHOLDER".
"""

import hashlib
import random
from pathlib import Path
from xml.sax.saxutils import escape

from .base import GeneratorBackend

PALETTE = [
    ("#0f172a", "#38bdf8"),  # slate / sky
    ("#1e1b4b", "#a78bfa"),  # indigo / violet
    ("#052e16", "#4ade80"),  # deep green / green
    ("#450a0a", "#f87171"),  # maroon / red
    ("#422006", "#fbbf24"),  # brown / amber
    ("#083344", "#22d3ee"),  # teal / cyan
    ("#3b0764", "#e879f9"),  # purple / fuchsia
    ("#172554", "#93c5fd"),  # navy / blue
]


def _dims(aspect):
    width, height = 800, 800
    if aspect:
        try:
            left, right = aspect.split(":")
            ratio = int(right) / int(left)
            height = max(200, min(1600, int(800 * ratio)))
        except (ValueError, ZeroDivisionError):
            pass
    return width, height


def _seed(job):
    return int(
        hashlib.sha256(f"{job['job_id']}|{job['prompt']}".encode("utf-8")).hexdigest(),
        16,
    )


def _render_svg(job):
    rng = random.Random(_seed(job))
    width, height = _dims(job.get("aspect"))
    bg, accent = rng.choice(PALETTE)

    shapes = []
    for _ in range(rng.randint(3, 7)):
        cx, cy = rng.randint(0, width), rng.randint(0, height)
        r = rng.randint(20, min(width, height) // 3)
        opacity = round(rng.uniform(0.15, 0.55), 2)
        if rng.random() < 0.5:
            shapes.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{accent}" opacity="{opacity}"/>'
            )
        else:
            x, y = rng.randint(0, width), rng.randint(0, height)
            w, h = rng.randint(20, width // 2), rng.randint(20, height // 2)
            shapes.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                f'fill="{accent}" opacity="{opacity}" rx="8"/>'
            )
    shapes_svg = "\n    ".join(shapes)

    prompt_text = escape(job["prompt"][:90])
    item_id = escape(str(job["item_id"]))
    kind = escape(str(job["kind"]))
    job_id = escape(str(job["job_id"]))

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="{bg}"/>
    {shapes_svg}
  <rect x="0" y="{height - 190}" width="{width}" height="190" fill="#000000" opacity="0.72"/>
  <text x="28" y="{height - 148}" font-family="monospace" font-size="26" fill="#ffffff">MOCK PLACEHOLDER - not AI-generated</text>
  <text x="28" y="{height - 112}" font-family="monospace" font-size="20" fill="#cbd5e1">kind: {kind}  |  item: {item_id}</text>
  <text x="28" y="{height - 80}" font-family="monospace" font-size="20" fill="#cbd5e1">job: {job_id}</text>
  <text x="28" y="{height - 40}" font-family="monospace" font-size="18" fill="#94a3b8">prompt: {prompt_text}</text>
</svg>
"""


class MockBackend(GeneratorBackend):
    """Deterministic placeholder generator. Output is NOT AI-generated."""

    name = "mock"
    description = "deterministic mock: SVG placeholder assets (NOT AI-generated)"

    def generate(self, job, assets_dir):
        assets_dir = Path(assets_dir)
        assets_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{job['job_id']}.svg"
        path = assets_dir / filename
        path.write_text(_render_svg(job), encoding="utf-8")
        return str(path)
