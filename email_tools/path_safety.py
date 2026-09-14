"""Filesystem-boundary helpers for generated output paths."""

from __future__ import annotations

import os
import stat
from pathlib import Path


def is_link_or_reparse(path: Path) -> bool:
    """Return whether an existing path is a symlink or reparse point."""
    if path.is_symlink():
        return True
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    attributes = getattr(metadata, "st_file_attributes", 0)
    return stat.S_ISLNK(metadata.st_mode) or bool(attributes & reparse_flag)


def ensure_safe_output_path(path: Path) -> None:
    """Reject output paths that traverse symlinks or reparse points."""
    expanded = path.expanduser()
    if ".." in expanded.parts:
        raise ValueError(f"Output path must not contain parent traversal: {path}")
    candidate = Path(os.path.abspath(expanded))
    current = candidate
    while True:
        if os.path.lexists(current) and is_link_or_reparse(current):
            raise ValueError(
                "Output path must not traverse a symbolic link or reparse point: "
                f"{path}"
            )
        parent = current.parent
        if parent == current:
            return
        current = parent
