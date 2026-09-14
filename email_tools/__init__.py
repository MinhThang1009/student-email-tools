"""Utilities for generating and formatting participant email lists."""

import re
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

__all__ = ["__version__"]

PROJECT_VERSION_PATTERN = re.compile(r"(?m)^version\s*=\s*\"([^\"]+)\"")


def _source_project_version() -> str | None:
    """Read the version from the repository manifest in a source checkout."""
    project_file = Path(__file__).resolve().parents[1] / "pyproject.toml"
    try:
        project_text = project_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    match = PROJECT_VERSION_PATTERN.search(project_text)
    return match.group(1) if match else None


_source_version = _source_project_version()
if _source_version is not None:
    __version__ = _source_version
else:  # pragma: no cover - installed wheels use distribution metadata
    try:
        __version__ = version("student-email-tools")
    except PackageNotFoundError:  # pragma: no cover - uninstalled wheel
        __version__ = "0+unknown"
