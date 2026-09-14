"""Backward-compatible launcher for the text-block formatting command."""

from pathlib import Path

from email_tools.text_blocks import (
    DEFAULT_GAP_LINES,
    DEFAULT_LINES_PER_BLOCK,
    OUTPUT_SUFFIX,
    find_text_files,
    format_lines,
    main,
    output_path_for,
    process_folder,
    process_text_file,
)

__all__ = [
    "DEFAULT_GAP_LINES",
    "DEFAULT_LINES_PER_BLOCK",
    "OUTPUT_SUFFIX",
    "find_text_files",
    "format_lines",
    "output_path_for",
    "process_folder",
    "process_text_file",
]


if __name__ == "__main__":  # pragma: no cover - CLI bootstrap
    raise SystemExit(main(default_folder=Path(__file__).resolve().parent))
