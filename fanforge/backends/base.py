"""Backend plugin interface.

A backend is a class with:

- ``name``: a short unique string used on the CLI (``--backend name``)
- ``description``: one-line human description
- ``generate(job, assets_dir) -> str``: produce the asset for *job* inside
  *assets_dir* (a pathlib.Path) and return the asset's path (absolute or
  relative to the job dir). Raise an exception on failure; FanForge marks
  the job ``failed`` and continues with the rest of the queue.

To add a real generator:

1. Create ``fanforge/backends/mybackend.py`` with a ``MyBackend(GeneratorBackend)``
   subclass implementing ``generate()``.
2. Register it in ``fanforge/backends/registry.py``::

       from . import mybackend
       register(mybackend.MyBackend.name, mybackend.MyBackend)

3. Run with ``fanforge run --dir ./job1 --backend mybackend``.

The built-in ``mock`` backend is deterministic and produces placeholder SVG
files only. Mock output is NOT AI-generated imagery — never present it as such.
"""

from pathlib import Path


class GeneratorBackend:
    """Base class for generation backends."""

    name = "base"
    description = "base backend interface (not usable directly)"

    def generate(self, job, assets_dir):
        """Generate the asset for *job* into *assets_dir*.

        *job* is a dict with keys: job_id, item_id, prompt, kind, aspect, notes.
        *assets_dir* is a pathlib.Path that already exists.

        Return the asset path (str or Path). Raise on failure.
        """
        raise NotImplementedError("subclasses must implement generate()")


__all__ = ["GeneratorBackend", "Path"]
