"""Format text files into fixed-size blocks separated by blank lines."""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Sequence
from pathlib import Path

DEFAULT_LINES_PER_BLOCK = 500
DEFAULT_GAP_LINES = 10
OUTPUT_SUFFIX = "_output"


def format_lines(
    lines: Iterable[str],
    *,
    lines_per_block: int = DEFAULT_LINES_PER_BLOCK,
    gap_lines: int = DEFAULT_GAP_LINES,
) -> list[str]:
    """Return lines grouped with blank lines between, but not after, blocks."""
    if lines_per_block <= 0:
        raise ValueError("lines_per_block phải lớn hơn 0")
    if gap_lines < 0:
        raise ValueError("gap_lines không được âm")

    source_lines = list(lines)
    formatted: list[str] = []
    for start in range(0, len(source_lines), lines_per_block):
        end = min(start + lines_per_block, len(source_lines))
        formatted.extend(source_lines[start:end])
        if end < len(source_lines):
            formatted.extend([""] * gap_lines)
    return formatted


def output_path_for(input_path: Path) -> Path:
    """Return the conventional output path for a text input file."""
    return input_path.with_name(f"{input_path.stem}{OUTPUT_SUFFIX}{input_path.suffix}")


def process_text_file(
    input_path: Path | str,
    output_path: Path | str | None = None,
    *,
    lines_per_block: int = DEFAULT_LINES_PER_BLOCK,
    gap_lines: int = DEFAULT_GAP_LINES,
) -> Path:
    """Format one text file and return the generated output path."""
    source = Path(input_path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Không tìm thấy file TXT: {source}")

    destination = (
        Path(output_path).expanduser().resolve()
        if output_path is not None
        else output_path_for(source)
    )
    if destination == source:
        raise ValueError("File đầu ra phải khác file đầu vào")

    lines = source.read_text(encoding="utf-8").splitlines()
    formatted = format_lines(
        lines, lines_per_block=lines_per_block, gap_lines=gap_lines
    )
    content = "\n".join(formatted)
    if formatted:
        content += "\n"
    destination.write_text(content, encoding="utf-8", newline="")
    return destination


def find_text_files(folder_path: Path | str) -> list[Path]:
    """Find source TXT files without reprocessing generated outputs."""
    folder = Path(folder_path)
    return sorted(
        (
            path
            for path in folder.iterdir()
            if path.is_file()
            and path.suffix.casefold() == ".txt"
            and not path.name.startswith("~$")
            and not path.stem.casefold().endswith(OUTPUT_SUFFIX.casefold())
        ),
        key=lambda path: path.name.casefold(),
    )


def process_folder(
    folder_path: Path | str,
    *,
    lines_per_block: int = DEFAULT_LINES_PER_BLOCK,
    gap_lines: int = DEFAULT_GAP_LINES,
) -> list[Path]:
    """Format every source TXT file in a folder."""
    folder = Path(folder_path).expanduser().resolve()
    if not folder.is_dir():
        raise FileNotFoundError(f"Không tìm thấy thư mục: {folder}")

    text_files = find_text_files(folder)
    if not text_files:
        raise FileNotFoundError(f"Không tìm thấy file TXT trong thư mục: {folder}")

    outputs = [
        process_text_file(
            path,
            lines_per_block=lines_per_block,
            gap_lines=gap_lines,
        )
        for path in text_files
    ]
    for source, destination in zip(text_files, outputs):
        print(f"Đã xử lý {source.name}, lưu tại {destination.name}")
    return outputs


def parse_args(
    argv: Sequence[str] | None = None, *, default_folder: Path | None = None
) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Chia file TXT thành các khối dòng có khoảng cách."
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=default_folder or Path.cwd(),
        help="File TXT hoặc thư mục chứa file TXT.",
    )
    parser.add_argument(
        "--lines-per-block",
        type=int,
        default=DEFAULT_LINES_PER_BLOCK,
        help=f"Số dòng mỗi khối (mặc định: {DEFAULT_LINES_PER_BLOCK}).",
    )
    parser.add_argument(
        "--gap-lines",
        type=int,
        default=DEFAULT_GAP_LINES,
        help=f"Số dòng trống giữa các khối (mặc định: {DEFAULT_GAP_LINES}).",
    )
    return parser.parse_args(argv)


def main(
    argv: Sequence[str] | None = None, *, default_folder: Path | None = None
) -> int:
    """Run the text-block formatting command."""
    args = parse_args(argv, default_folder=default_folder)
    if args.path.is_file():
        destination = process_text_file(
            args.path,
            lines_per_block=args.lines_per_block,
            gap_lines=args.gap_lines,
        )
        print(f"Đã xử lý {args.path.name}, lưu tại {destination.name}")
    else:
        process_folder(
            args.path,
            lines_per_block=args.lines_per_block,
            gap_lines=args.gap_lines,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
