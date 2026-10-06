"""Backend registry: maps --backend names to GeneratorBackend classes."""

from . import mock
from .base import GeneratorBackend

_BACKENDS = {}


def register(name, backend_cls):
    """Register a backend class under *name*."""
    if not (isinstance(backend_cls, type) and issubclass(backend_cls, GeneratorBackend)):
        raise TypeError("backend must be a GeneratorBackend subclass")
    _BACKENDS[name] = backend_cls


def get(name):
    """Return the backend class registered as *name*, or raise KeyError."""
    try:
        return _BACKENDS[name]
    except KeyError:
        known = ", ".join(sorted(_BACKENDS)) or "(none)"
        raise KeyError(f"unknown backend {name!r}; available: {known}") from None


def available():
    """Return {name: backend_cls} for all registered backends."""
    return dict(_BACKENDS)


register(mock.MockBackend.name, mock.MockBackend)

__all__ = ["register", "get", "available", "GeneratorBackend"]
