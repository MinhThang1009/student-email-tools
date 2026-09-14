"""Utilities for generating and formatting participant email lists."""

from importlib.metadata import PackageNotFoundError, version

__all__ = ["__version__"]

try:
    __version__ = version("student-email-tools")
except PackageNotFoundError:  # pragma: no cover - exercised by clean installs
    # Source checkouts can be imported before the editable package is installed.
    __version__ = "0.2.0"
