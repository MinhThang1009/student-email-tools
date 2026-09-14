"""Format text files into fixed-size blocks separated by blank lines."""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Sequence
from pathlib import Path

from email_tools.path_safety import absolute_safe_output_path

DEFAULT_LINES_PER_BLOCK = 499
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
        raise ValueError("lines_per_block must be greater than 0")
    if gap_lines < 0:
        raise ValueError("gap_lines must not be negative")

    source_lines = list(lines)
    formatted: list[str] = []
    for start in range(0, len(source_lines), lines_per_block):
        end = min(start + lines_per_block, len(source_lines))
        formatted.extend(source_lines[start:end])
        if end < len(source_lines):
            formatted.extend([""] * gap_lines)
    return formatted


def output_path_for(input_path: Path, output_dir: Path | str | None = None) -> Path:
    """Return the conventional output path for a text input file."""
    output_name = f"{input_path.stem}{OUTPUT_SUFFIX}{input_path.suffix}"
    if output_dir is None:
        destination = input_path.with_name(output_name)
    else:
        destination = Path(output_dir).expanduser() / output_name
    return absolute_safe_output_path(destination)


def process_text_file(
    input_path: Path | str,
    output_path: Path | str | None = None,
    *,
    output_dir: Path | str | None = None,
    lines_per_block: int = DEFAULT_LINES_PER_BLOCK,
    gap_lines: int = DEFAULT_GAP_LINES,
    overwrite: bool = True,
    dry_run: bool = False,
) -> Path:
    """Format one text file and return the generated output path."""
    source = Path(input_path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"TXT file not found: {source}")

    if output_path is not None and output_dir is not None:
        raise ValueError("output_path and output_dir cannot be used together")

    destination = (
        Path(output_path).expanduser()
        if output_path is not None
        else output_path_for(source, output_dir)
    )
    destination = absolute_safe_output_path(destination)
    if destination == source:
        raise ValueError("Output file must differ from the input file")
    if destination.exists() and not overwrite:
        raise FileExistsError(f"Output file already exists: {destination}")

    if dry_run:
        return destination

    lines = source.read_text(encoding="utf-8").splitlines()
    formatted = format_lines(
        lines, lines_per_block=lines_per_block, gap_lines=gap_lines
    )
    content = "\n".join(formatted)
    if formatted:
        content += "\n"
    destination.parent.mkdir(parents=True, exist_ok=True)
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
        key=lambda path: (path.name.casefold(), path.name),
    )


def process_folder(
    folder_path: Path | str,
    *,
    output_dir: Path | str | None = None,
    lines_per_block: int = DEFAULT_LINES_PER_BLOCK,
    gap_lines: int = DEFAULT_GAP_LINES,
    overwrite: bool = True,
    dry_run: bool = False,
) -> list[Path]:
    """Format every source TXT file in a folder."""
    folder = Path(folder_path).expanduser().resolve()
    if not folder.is_dir():
        raise FileNotFoundError(f"Directory not found: {folder}")

    text_files = find_text_files(folder)
    if not text_files:
        raise FileNotFoundError(f"No TXT files found in directory: {folder}")

    destinations = [output_path_for(path, output_dir) for path in text_files]
    seen_destinations: set[str] = set()
    for destination in destinations:
        destination_key = str(destination).casefold()
        if destination_key in seen_destinations:
            raise ValueError(
                f"Multiple TXT files map to the same output: {destination.name}"
            )
        seen_destinations.add(destination_key)
    if not overwrite:
        conflicting_outputs = [path for path in destinations if path.exists()]
        if conflicting_outputs:
            raise FileExistsError(
                f"Output file already exists: {conflicting_outputs[0]}"
            )

    outputs = []
    for source, destination in zip(text_files, destinations):
        outputs.append(
            process_text_file(
                source,
                destination,
                lines_per_block=lines_per_block,
                gap_lines=gap_lines,
                overwrite=overwrite,
                dry_run=dry_run,
            )
        )
        status = "Would process" if dry_run else "Processed"
        print(f"{status} {source.name}, saved to {destination.name}")
    return outputs


def parse_args(
    argv: Sequence[str] | None = None, *, default_folder: Path | None = None
) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Format TXT files into fixed-size blocks."
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=default_folder or Path.cwd(),
        help="TXT file or directory containing TXT files.",
    )
    parser.add_argument(
        "--lines-per-block",
        type=int,
        default=DEFAULT_LINES_PER_BLOCK,
        help=f"Lines per block (default: {DEFAULT_LINES_PER_BLOCK}).",
    )
    parser.add_argument(
        "--gap-lines",
        type=int,
        default=DEFAULT_GAP_LINES,
        help=f"Blank lines between blocks (default: {DEFAULT_GAP_LINES}).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory for formatted TXT files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check and display results without writing files.",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Fail if an output file already exists.",
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
            output_dir=args.output_dir,
            lines_per_block=args.lines_per_block,
            gap_lines=args.gap_lines,
            overwrite=not args.no_overwrite,
            dry_run=args.dry_run,
        )
        status = "Would process" if args.dry_run else "Processed"
        print(f"{status} {args.path.name}, saved to {destination.name}")
    else:
        process_folder(
            args.path,
            output_dir=args.output_dir,
            lines_per_block=args.lines_per_block,
            gap_lines=args.gap_lines,
            overwrite=not args.no_overwrite,
            dry_run=args.dry_run,
        )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI bootstrap
    raise SystemExit(main())
