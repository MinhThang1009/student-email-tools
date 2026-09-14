"""Generate university email addresses from participant Excel files."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from email_tools.path_safety import absolute_safe_output_path

EMAIL_DOMAIN = "vanlanguni.vn"
EXCEL_SUFFIXES = {".xls", ".xlsx"}
LONG_FIRST_PREFIX_LENGTH = 14
NUMERIC_IDENTIFIER_MIN_LENGTH = 13
EMAILS_PER_BLOCK = 499
BLANK_LINES_PER_BLOCK = 10
EMAIL_COLUMN_ALIASES = {"email", "email address", "e-mail", "e-mail address"}

PREFIX_SEPARATOR = re.compile(r"\s*-\s*")
INVALID_LOCAL_PART_CHARS = re.compile(r"[^a-z0-9]")
INTEGRAL_NUMERIC_TEXT_PATTERN = re.compile(r"^(?P<integer>[0-9]+)\.0+$")
PANDAS_MANGLED_COLUMN_PATTERN = re.compile(r"^(?P<base>.+?)\s*\.[1-9]\d*$")
NUMBER_AFTER_DOT = re.compile(r"^[a-z0-9]+\.([0-9]+)[a-z0-9]*@[^@]+$")
DOMAIN_PATTERN = re.compile(
    r"(?=.{1,253}\Z)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}\Z",
    re.IGNORECASE,
)
EMAIL_PATTERN = re.compile(
    r"^[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$",
    re.IGNORECASE,
)
ESCAPED_AT = re.compile(r"\\+@")


def normalize_integral_numeric_text(text: str) -> str:
    """Remove a spreadsheet-style zero fraction from an integer value."""
    match = INTEGRAL_NUMERIC_TEXT_PATTERN.fullmatch(text)
    return match.group("integer") if match else text


@dataclass(frozen=True)
class SkippedRow:
    """Describe a source row that could not produce an email address."""

    row_number: int
    reason: str


@dataclass(frozen=True)
class DuplicateEmail:
    """Describe an email generated for more than one source row."""

    email: str
    row_numbers: tuple[int, ...]


@dataclass(frozen=True)
class EmailGenerationReport:
    """Summarize generated emails and source-data quality issues."""

    total_rows: int
    emails: list[str]
    skipped_rows: list[SkippedRow]
    warnings: list[SkippedRow]
    duplicate_emails: list[DuplicateEmail]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation of the report."""
        return {
            "total_rows": self.total_rows,
            "generated_emails": len(self.emails),
            "skipped_rows": [asdict(row) for row in self.skipped_rows],
            "warnings": [asdict(row) for row in self.warnings],
            "duplicate_emails": [
                {"email": item.email, "row_numbers": list(item.row_numbers)}
                for item in self.duplicate_emails
            ],
        }


def extract_component(
    value: object, *, leading_hyphen_uses_last_word: bool = False
) -> str | None:
    """Extract a usable component from a value with an optional hyphen."""
    if value is None or pd.isna(value):
        return None

    text = str(value).strip()
    if "-" not in text:
        normalized = normalize_integral_numeric_text(text)
        return normalized or None

    parts = PREFIX_SEPARATOR.split(text, maxsplit=1)
    prefix = normalize_integral_numeric_text(parts[0].strip())
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


def normalize_email_domain(email_domain: str) -> str:
    """Validate and normalize the domain used for generated addresses."""
    domain = str(email_domain).strip()
    if domain.startswith("@"):
        domain = domain[1:]
    domain = domain.casefold()
    if not DOMAIN_PATTERN.fullmatch(domain):
        raise ValueError(f"Invalid email domain: {email_domain!r}")
    return domain


def normalize_email_override(value: object) -> str | None:
    """Normalize an optional source email, including escaped ``@`` values."""
    if value is None or pd.isna(value):
        return None

    email = ESCAPED_AT.sub("@", str(value).strip()).casefold()
    if not EMAIL_PATTERN.fullmatch(email):
        return None
    local_part = email.rsplit("@", maxsplit=1)[0]
    if local_part.startswith(".") or local_part.endswith(".") or ".." in local_part:
        return None
    return email


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
    dataframe: pd.DataFrame,
    source_name: str,
    *,
    email_column: str | None = None,
) -> pd.DataFrame:
    """Rename required and optional email columns safely."""
    required = ("first name", "last name")
    matches: dict[str, list[object]] = {column: [] for column in required}
    normalized_columns = {
        str(column).strip().casefold() for column in dataframe.columns
    }

    def pandas_mangled_base(normalized: str) -> str | None:
        match = PANDAS_MANGLED_COLUMN_PATTERN.fullmatch(normalized)
        if match is None or match.group("base") not in normalized_columns:
            return None
        return match.group("base")

    for column in dataframe.columns:
        normalized = str(column).strip().casefold()
        if normalized in matches:
            matches[normalized].append(column)
            continue
        mangled_base = pandas_mangled_base(normalized)
        if mangled_base in matches:
            matches[mangled_base].append(column)

    missing = sorted(column for column, values in matches.items() if not values)
    if missing:
        raise ValueError(f"Excel file {source_name} is missing columns: {missing}")

    duplicates = sorted(column for column, values in matches.items() if len(values) > 1)
    if duplicates:
        raise ValueError(
            f"Excel file {source_name} has duplicate columns: {duplicates}"
        )

    rename_map = {matches[normalized][0]: normalized for normalized in required}
    if email_column is not None:
        requested_email_column = str(email_column).strip().casefold()
        if not requested_email_column:
            raise ValueError("email_column must not be empty")
        if requested_email_column in required:
            raise ValueError("email_column must differ from required columns")
        email_matches = [
            column
            for column in dataframe.columns
            if (
                str(column).strip().casefold() == requested_email_column
                or pandas_mangled_base(str(column).strip().casefold())
                == requested_email_column
            )
        ]
        if not email_matches:
            raise ValueError(
                f"Excel file {source_name} is missing email column: {email_column!r}"
            )
        email_alias_matches = [
            column
            for column in dataframe.columns
            if (
                str(column).strip().casefold() in EMAIL_COLUMN_ALIASES
                or pandas_mangled_base(str(column).strip().casefold())
                in EMAIL_COLUMN_ALIASES
            )
        ]
        if any(column not in email_matches for column in email_alias_matches):
            raise ValueError(f"Excel file {source_name} has duplicate email columns")
    else:
        email_matches = [
            column
            for column in dataframe.columns
            if (
                str(column).strip().casefold() in EMAIL_COLUMN_ALIASES
                or pandas_mangled_base(str(column).strip().casefold())
                in EMAIL_COLUMN_ALIASES
            )
        ]

    if len(email_matches) > 1:
        raise ValueError(f"Excel file {source_name} has duplicate email columns")
    if email_matches:
        rename_map[email_matches[0]] = "email"

    return dataframe.rename(columns=rename_map).copy()


def generate_email_report(
    dataframe: pd.DataFrame,
    source_name: str = "<data>",
    *,
    email_domain: str = EMAIL_DOMAIN,
    email_column: str | None = None,
) -> EmailGenerationReport:
    """Generate emails and report skipped rows, warnings, and duplicates."""
    domain = normalize_email_domain(email_domain)
    dataframe = normalize_required_columns(
        dataframe, source_name, email_column=email_column
    )
    has_email_column = "email" in dataframe.columns
    skipped_rows: list[SkippedRow] = []
    warnings: list[SkippedRow] = []
    emails_by_row: dict[int, str] = {}

    for row_number, (_, row) in enumerate(dataframe.iterrows(), start=2):
        override_value = row["email"] if has_email_column else None
        override_present = (
            override_value is not None
            and not pd.isna(override_value)
            and bool(str(override_value).strip())
        )
        email = normalize_email_override(override_value)

        if email is None:
            first_name = row["first name"]
            last_name = row["last name"]
            first_prefix = extract_component(first_name)
            first_name_part = extract_name_part(first_name)
            last_prefix = extract_last_component_from_row(first_name, last_name)
            first_part = normalize_local_part(first_prefix)
            last_part = normalize_local_part(last_prefix)

            if first_part is None or last_part is None or first_prefix is None:
                reason = "unusable name data"
                if override_present:
                    reason = "invalid email override and unusable name data"
                skipped_rows.append(SkippedRow(row_number, reason))
                continue

            short_name_without_class = (
                isinstance(first_name_part, str)
                and len(first_name_part.split()) == 1
                and not has_hyphen(last_name)
            )
            if (
                (
                    first_prefix.isdigit()
                    and len(first_prefix) >= NUMERIC_IDENTIFIER_MIN_LENGTH
                )
                or (
                    first_prefix.isdigit()
                    and len(first_prefix) >= LONG_FIRST_PREFIX_LENGTH
                )
                or short_name_without_class
            ):
                email = f"{first_part}@{domain}"
            else:
                email = f"{last_part}.{first_part}@{domain}"

            if override_present:
                warnings.append(
                    SkippedRow(
                        row_number, "invalid email override; generated from names"
                    )
                )

        emails_by_row[row_number] = email

    rows_by_email: dict[str, list[int]] = {}
    for row_number, email in emails_by_row.items():
        rows_by_email.setdefault(email, []).append(row_number)

    emails = sorted(rows_by_email, key=email_sort_key)
    duplicate_emails = [
        DuplicateEmail(email, tuple(row_numbers))
        for email, row_numbers in sorted(
            rows_by_email.items(), key=lambda item: email_sort_key(item[0])
        )
        if len(row_numbers) > 1
    ]
    return EmailGenerationReport(
        total_rows=len(dataframe),
        emails=emails,
        skipped_rows=skipped_rows,
        warnings=warnings,
        duplicate_emails=duplicate_emails,
    )


def generate_emails(
    dataframe: pd.DataFrame,
    source_name: str = "<data>",
    *,
    email_domain: str = EMAIL_DOMAIN,
    email_column: str | None = None,
) -> list[str]:
    """Generate unique, sorted email addresses from a participant dataframe."""
    return generate_email_report(
        dataframe,
        source_name,
        email_domain=email_domain,
        email_column=email_column,
    ).emails


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
    emails: Iterable[str],
    output_path: Path,
    *,
    block_size: int = EMAILS_PER_BLOCK,
    overwrite: bool = True,
    dry_run: bool = False,
) -> None:
    """Write one email per line with the requested block spacing."""
    if block_size <= 0:
        raise ValueError("block_size must be greater than 0")
    output_path = absolute_safe_output_path(output_path)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output file already exists: {output_path}")
    if dry_run:
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        for index, email in enumerate(emails, start=1):
            output_file.write(f"{email}\n")
            if index % block_size == 0:
                output_file.write("\n" * BLANK_LINES_PER_BLOCK)


def write_generation_report(
    reports: dict[str, EmailGenerationReport],
    output_path: Path,
    *,
    email_domain: str,
    overwrite: bool = True,
    dry_run: bool = False,
) -> None:
    """Write source-data quality reports as UTF-8 JSON."""
    output_path = absolute_safe_output_path(output_path)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Report file already exists: {output_path}")
    if dry_run:
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "email_domain": email_domain,
        "files": {name: report.to_dict() for name, report in reports.items()},
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def process_folder(
    folder_path: Path | str,
    *,
    output_dir: Path | str | None = None,
    report_path: Path | str | None = None,
    email_domain: str = EMAIL_DOMAIN,
    email_column: str | None = None,
    overwrite: bool = True,
    dry_run: bool = False,
) -> list[Path]:
    """Process every Excel file in ``folder_path`` and return output paths."""
    folder = Path(folder_path).expanduser().resolve()
    if not folder.is_dir():
        raise FileNotFoundError(f"Directory not found: {folder}")

    excel_files = find_excel_files(folder)
    if not excel_files:
        raise FileNotFoundError(f"No Excel files found in directory: {folder}")

    domain = normalize_email_domain(email_domain)
    destination_dir = (
        folder if output_dir is None else absolute_safe_output_path(Path(output_dir))
    )
    output_paths: list[Path] = []
    seen_outputs: set[str] = set()
    reports: dict[str, EmailGenerationReport] = {}
    jobs: list[tuple[Path, Path, EmailGenerationReport]] = []
    report_destination = (
        None if report_path is None else absolute_safe_output_path(Path(report_path))
    )
    for file_path in excel_files:
        output_path = destination_dir / f"{file_path.stem}.txt"
        output_key = str(output_path).casefold()
        if output_key in seen_outputs:
            raise ValueError(
                f"Multiple Excel files map to the same output: {output_path.name}"
            )
        seen_outputs.add(output_key)

        dataframe = pd.read_excel(file_path, dtype=str)
        report = generate_email_report(
            dataframe,
            file_path.name,
            email_domain=domain,
            email_column=email_column,
        )
        reports[file_path.name] = report
        jobs.append((file_path, output_path, report))
        output_paths.append(output_path)
        status = "Would save" if dry_run else "Saved"
        print(
            f"{status} {len(report.emails)} emails from {file_path.name} "
            f"(skipped {len(report.skipped_rows)} rows, "
            f"warnings {len(report.warnings)}, "
            f"duplicates {len(report.duplicate_emails)})"
        )

    if not overwrite:
        conflicting_outputs = [path for _, path, _ in jobs if path.exists()]
        if conflicting_outputs:
            raise FileExistsError(
                f"Output file already exists: {conflicting_outputs[0]}"
            )
        if report_destination is not None and report_destination.exists():
            raise FileExistsError(f"Report file already exists: {report_destination}")

    if report_destination is not None:
        report_key = str(report_destination).casefold()
        source_keys = {str(path).casefold() for path in excel_files}
        if report_key in seen_outputs:
            raise ValueError("Report path must differ from output files")
        if report_key in source_keys:
            raise ValueError("Report path must not overwrite an input file")

    for _, output_path, report in jobs:
        write_emails(
            report.emails,
            output_path,
            overwrite=overwrite,
            dry_run=dry_run,
        )

    if report_destination is not None:
        write_generation_report(
            reports,
            report_destination,
            email_domain=domain,
            overwrite=overwrite,
            dry_run=dry_run,
        )
        if dry_run:
            print(f"Would save report to {report_destination}")
        else:
            print(f"Saved report to {report_destination}")

    return output_paths


def parse_args(
    argv: Sequence[str] | None = None, *, default_folder: Path | None = None
) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate email addresses from participant Excel files."
    )
    parser.add_argument(
        "folder",
        nargs="?",
        type=Path,
        default=default_folder or Path.cwd(),
        help="Directory containing Excel files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory for generated TXT files.",
    )
    parser.add_argument(
        "--report",
        dest="report_path",
        type=Path,
        help="Path for the JSON data-quality report.",
    )
    parser.add_argument(
        "--domain",
        default=EMAIL_DOMAIN,
        help=f"Email domain for generated addresses (default: {EMAIL_DOMAIN}).",
    )
    parser.add_argument(
        "--email-column",
        help="Custom email column to use as a row-level override.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze and display results without writing files.",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Fail if an output or report file already exists.",
    )
    return parser.parse_args(argv)


def main(
    argv: Sequence[str] | None = None, *, default_folder: Path | None = None
) -> int:
    """Run the email generation command."""
    args = parse_args(argv, default_folder=default_folder)
    process_folder(
        args.folder,
        output_dir=args.output_dir,
        report_path=args.report_path,
        email_domain=args.domain,
        email_column=args.email_column,
        overwrite=not args.no_overwrite,
        dry_run=args.dry_run,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI bootstrap
    raise SystemExit(main())
