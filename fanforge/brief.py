"""Brief loading and validation.

A brief is a JSON object::

    {
        "project": "my-project",
        "items": [
            {
                "id": "hero-01",
                "prompt": "a neon city skyline at dusk",
                "kind": "image",            # one of: image | video | audio
                "aspect": "16:9",           # optional
                "notes": "use brand teal"   # optional
            }
        ]
    }
"""

import json
from pathlib import Path

VALID_KINDS = ("image", "video", "audio")


class BriefValidationError(ValueError):
    """Raised when a brief fails validation."""


def load_brief(path):
    """Read a brief JSON file from *path* and return the validated dict."""
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise BriefValidationError(f"cannot read brief file: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BriefValidationError(f"brief is not valid JSON: {exc}") from exc
    return validate_brief(data)


def validate_brief(data):
    """Validate a parsed brief dict. Returns it unchanged or raises."""
    if not isinstance(data, dict):
        raise BriefValidationError("brief must be a JSON object")
    project = data.get("project")
    if not isinstance(project, str) or not project.strip():
        raise BriefValidationError("'project' must be a non-empty string")
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise BriefValidationError("'items' must be a non-empty list")
    seen_ids = set()
    for index, item in enumerate(items):
        _validate_item(item, index, seen_ids)
    return data


def _validate_item(item, index, seen_ids):
    where = f"item[{index}]"
    if not isinstance(item, dict):
        raise BriefValidationError(f"{where} must be an object")
    item_id = item.get("id")
    if not isinstance(item_id, str) or not item_id.strip():
        raise BriefValidationError(f"{where} is missing a non-empty 'id'")
    if item_id in seen_ids:
        raise BriefValidationError(f"duplicate item id: {item_id!r}")
    seen_ids.add(item_id)

    prompt = item.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise BriefValidationError(f"{where} (id={item_id!r}) is missing a non-empty 'prompt'")

    kind = item.get("kind")
    if kind not in VALID_KINDS:
        raise BriefValidationError(
            f"{where} (id={item_id!r}) has invalid kind {kind!r}; "
            f"must be one of: {', '.join(VALID_KINDS)}"
        )

    aspect = item.get("aspect")
    if aspect is not None and (not isinstance(aspect, str) or not aspect.strip()):
        raise BriefValidationError(
            f"{where} (id={item_id!r}) 'aspect' must be a non-empty string when present"
        )

    notes = item.get("notes")
    if notes is not None and not isinstance(notes, str):
        raise BriefValidationError(
            f"{where} (id={item_id!r}) 'notes' must be a string when present"
        )
