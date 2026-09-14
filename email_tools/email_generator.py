"""Generate university email addresses from participant Excel files."""

from __future__ import annotations

import argparse
import re
import unicodedata
from collections.abc import Iterable, Sequence
from pathlib import Path

import pandas as pd

EMAIL_DOMAIN = "vanlanguni.vn"
EXCEL_SUFFIXES = {".xls", ".xlsx"}
LONG_FIRST_PREFIX_LENGTH = 14
EMAILS_PER_BLOCK = 500
BLANK_LINES_PER_BLOCK = 5

PREFIX_SEPARATOR = re.compile(r"\s*-\s*")
INVALID_LOCAL_PART_CHARS = re.compile(r"[^a-z0-9]")
NUMBER_AFTER_DOT = re.compile(r"^[a-z0-9]+\.([0-9]+)[a-z0-9]*@[^@]+$")


def extract_component(
    value: object, *, leading_hyphen_uses_last_word: bool = False
) -> str | None:
    """Extract a usable component from a value with an optional hyphen."""
    if value is None or pd.isna(value):
        return None

    text = str(value).strip()
    if "-" not in text:
        return text or None

    parts = PREFIX_SEPARATOR.split(text, maxsplit=1)
    prefix = parts[0].strip()
    if prefix:
        return prefix

    if not leading_hyphen_uses_last_word or len(parts) == 1:
        return None

    suffix = parts[1].strip()
    # A leading-hyphen value containing digits is a class/code value (for
    # example, "- 71K31DUOC01"), not a person's name.
    if not suffix or any(character.isdigit() for character in suffix):
        return None
    return suffix.split()[-1]


def extract_suffix(value: object) -> str | None:
    """Return the trimmed text after the first hyphen, when present."""
    if value is None or pd.isna(value):
        return None

    text = str(value).strip()
    parts = PREFIX_SEPARATOR.split(text, maxsplit=1)
    if len(parts) == 1:
        return None
    suffix = parts[1].strip()
    return suffix or None


def extract_name_part(value: object) -> str | None:
    """Return the name portion after an identifier and before class data."""
    suffix = extract_suffix(value)
    if suffix is None:
        return None

    name_part = PREFIX_SEPARATOR.split(suffix, maxsplit=1)[0].strip()
    return name_part or None


def has_hyphen(value: object) -> bool:
    """Return whether a non-empty source value contains a hyphen."""
    if value is None or pd.isna(value):
        return False
    return "-" in str(value)


def extract_last_component(value: object) -> str | None:
    """Extract the last-name component, including fallback name formats."""
    return extract_component(value, leading_hyphen_uses_last_word=True)


def extract_last_component_from_row(
    first_name: object, last_name: object
) -> str | None:
    """Resolve the last-name component across the source's mixed formats."""
    last_component = extract_last_component(last_name)
    if last_component is not None:
        return last_component

    if (
        last_name is None
        or pd.isna(last_name)
        or not str(last_name).strip().startswith("-")
    ):
        return None

    full_name = extract_suffix(first_name)
    if full_name is None:
        return None

    # A second separator may carry a class code in the First name column.
    name_part = PREFIX_SEPARATOR.split(full_name, maxsplit=1)[0].strip()
    if not name_part or any(character.isdigit() for character in name_part):
        return None
    return name_part.split()[-1]


def normalize_local_part(prefix: object) -> str | None:
    """Convert a name or identifier prefix to a safe ASCII email component."""
    if prefix is None or pd.isna(prefix):
        return None

    # NFKD handles Vietnamese combining marks. Đ/đ do not decompose, so map
    # them explicitly before converting the remaining text to ASCII.
    transliterated = str(prefix).replace("Đ", "D").replace("đ", "d")
    transliterated = unicodedata.normalize("NFKD", transliterated)
    ascii_text = transliterated.encode("ascii", "ignore").decode("ascii").lower()
    component = INVALID_LOCAL_PART_CHARS.sub("", ascii_text)
    return component or None


def extract_number_after_dot(email: str) -> int | None:
    """Return the leading number after the local-part dot, when present."""
    match = NUMBER_AFTER_DOT.fullmatch(email)
    return int(match.group(1)) if match else None


def email_sort_key(email: str) -> tuple[int, int, str]:
    """Sort numbered local parts first and emails without one last."""
    number = extract_number_after_dot(email)
    if number is None:
        return (1, 0, email)
    return (0, number, email)


def normalize_required_columns(
    dataframe: pd.DataFrame, source_name: str
) -> pd.DataFrame:
    """Rename required columns while tolerating header whitespace and case."""
    required = ("first name", "last name")
    matches: dict[str, list[object]] = {column: [] for column in required}

    for column in dataframe.columns:
        normalized = str(column).strip().casefold()
        if normalized in matches:
            matches[normalized].append(column)

    missing = sorted(column for column, values in matches.items() if not values)
    if missing:
        raise ValueError(f"File Excel {source_name} không chứa các cột sau: {missing}")

    duplicates = sorted(column for column, values in matches.items() if len(values) > 1)
    if duplicates:
        raise ValueError(f"File Excel {source_name} chứa cột bị trùng: {duplicates}")

    rename_map = {matches[normalized][0]: normalized for normalized in required}
    return dataframe.rename(columns=rename_map).copy()


def generate_emails(dataframe: pd.DataFrame, source_name: str = "<data>") -> list[str]:
    """Generate and sort valid email addresses from a participant dataframe."""
    dataframe = normalize_required_columns(dataframe, source_name)

    dataframe["first_prefix"] = dataframe["first name"].map(extract_component)
    dataframe["first_name_part"] = dataframe["first name"].map(extract_name_part)
    dataframe["last_prefix"] = [
        extract_last_component_from_row(first_name, last_name)
        for first_name, last_name in zip(
            dataframe["first name"], dataframe["last name"]
        )
    ]
    dataframe["first_part"] = dataframe["first_prefix"].map(normalize_local_part)
    dataframe["last_part"] = dataframe["last_prefix"].map(normalize_local_part)

    valid_rows = dataframe["first_part"].notna() & dataframe["last_part"].notna()
    dataframe = dataframe.loc[valid_rows].copy()

    emails: list[str] = []
    for first_prefix, first_name_part, first_part, last_part, last_name in zip(
        dataframe["first_prefix"],
        dataframe["first_name_part"],
        dataframe["first_part"],
        dataframe["last_part"],
        dataframe["last name"],
    ):
        short_name_without_class = (
            isinstance(first_name_part, str)
            and len(first_name_part.split()) == 1
            and not has_hyphen(last_name)
        )
        if len(first_prefix) >= LONG_FIRST_PREFIX_LENGTH or short_name_without_class:
            emails.append(f"{first_part}@{EMAIL_DOMAIN}")
        else:
            emails.append(f"{last_part}.{first_part}@{EMAIL_DOMAIN}")

    return sorted(emails, key=email_sort_key)


def find_excel_files(folder_path: Path | str) -> list[Path]:
    """Find Excel files in a folder in deterministic, case-insensitive order."""
    folder = Path(folder_path)
    return sorted(
        (
            path
            for path in folder.iterdir()
            if path.is_file()
            and path.suffix.casefold() in EXCEL_SUFFIXES
            and not path.name.startswith("~$")
        ),
        key=lambda path: path.name.casefold(),
    )


def write_emails(
    emails: Iterable[str], output_path: Path, *, block_size: int = EMAILS_PER_BLOCK
) -> None:
    """Write one email per line with the requested block spacing."""
    if block_size <= 0:
        raise ValueError("block_size phải lớn hơn 0")

    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        for index, email in enumerate(emails, start=1):
            output_file.write(f"{email}\n")
            if index % block_size == 0:
                output_file.write("\n" * BLANK_LINES_PER_BLOCK)


def process_folder(folder_path: Path | str) -> list[Path]:
    """Process every Excel file in ``folder_path`` and return output paths."""
    folder = Path(folder_path).expanduser().resolve()
    if not folder.is_dir():
        raise FileNotFoundError(f"Không tìm thấy thư mục: {folder}")

    excel_files = find_excel_files(folder)
    if not excel_files:
        raise FileNotFoundError(f"Không tìm thấy file Excel trong thư mục: {folder}")

    output_paths: list[Path] = []
    seen_outputs: set[str] = set()
    for file_path in excel_files:
        output_path = folder / f"{file_path.stem}.txt"
        output_key = str(output_path).casefold()
        if output_key in seen_outputs:
            raise ValueError(f"Nhiều file Excel có cùng tên đầu ra: {output_path.name}")
        seen_outputs.add(output_key)

        dataframe = pd.read_excel(file_path, dtype=str)
        emails = generate_emails(dataframe, file_path.name)
        write_emails(emails, output_path)
        output_paths.append(output_path)
        skipped_rows = len(dataframe) - len(emails)
        print(
            f"Đã lưu {len(emails)} email từ file {file_path.name} "
            f"(bỏ qua {skipped_rows} dòng không đủ dữ liệu)"
        )

    return output_paths


def parse_args(
    argv: Sequence[str] | None = None, *, default_folder: Path | None = None
) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Tạo danh sách email từ các file Excel người tham gia."
    )
    parser.add_argument(
        "folder",
        nargs="?",
        type=Path,
        default=default_folder or Path.cwd(),
        help="Thư mục chứa file Excel.",
    )
    return parser.parse_args(argv)


def main(
    argv: Sequence[str] | None = None, *, default_folder: Path | None = None
) -> int:
    """Run the email generation command."""
    args = parse_args(argv, default_folder=default_folder)
    process_folder(args.folder)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
