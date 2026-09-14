from pathlib import Path
from types import SimpleNamespace

import pytest

from email_tools.path_safety import ensure_safe_output_path, is_link_or_reparse


def test_safe_output_path_allows_regular_nested_paths(tmp_path) -> None:
    output = tmp_path / "nested" / "out.txt"

    ensure_safe_output_path(output)

    assert is_link_or_reparse(output) is False


def test_output_path_rejects_symbolic_links(tmp_path, monkeypatch) -> None:
    output = tmp_path / "out.txt"
    output.touch()
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == output)

    with pytest.raises(ValueError, match="symbolic link"):
        ensure_safe_output_path(output)


def test_output_path_rejects_reparse_points(tmp_path, monkeypatch) -> None:
    output = tmp_path / "out.txt"
    output.touch()
    metadata = SimpleNamespace(st_mode=0, st_file_attributes=0x400)
    monkeypatch.setattr(Path, "is_symlink", lambda _path: False)
    monkeypatch.setattr(Path, "lstat", lambda _path: metadata)

    with pytest.raises(ValueError, match="symbolic link"):
        ensure_safe_output_path(output)


def test_missing_path_is_not_link_like(tmp_path) -> None:
    assert is_link_or_reparse(tmp_path / "missing.txt") is False


def test_output_path_rejects_parent_traversal(tmp_path) -> None:
    with pytest.raises(ValueError, match="parent traversal"):
        ensure_safe_output_path(tmp_path / ".." / "out.txt")
