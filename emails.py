"""Backward-compatible launcher for the email generation command."""

from pathlib import Path

from email_tools.email_generator import (
    BLANK_LINES_PER_BLOCK,
    EMAIL_DOMAIN,
    EMAILS_PER_BLOCK,
    EXCEL_SUFFIXES,
    LONG_FIRST_PREFIX_LENGTH,
    NUMERIC_IDENTIFIER_MIN_LENGTH,
    DuplicateEmail,
    EmailGenerationReport,
    SkippedRow,
    email_sort_key,
    extract_component,
    extract_last_component_from_row,
    extract_name_part,
    extract_number_after_dot,
    extract_suffix,
    generate_email_report,
    generate_emails,
    has_hyphen,
    main,
    normalize_email_domain,
    normalize_email_override,
    normalize_local_part,
    normalize_required_columns,
    process_folder,
    write_emails,
    write_generation_report,
)

__all__ = [
    "BLANK_LINES_PER_BLOCK",
    "DuplicateEmail",
    "EMAIL_DOMAIN",
    "EMAILS_PER_BLOCK",
    "EmailGenerationReport",
    "EXCEL_SUFFIXES",
    "LONG_FIRST_PREFIX_LENGTH",
    "NUMERIC_IDENTIFIER_MIN_LENGTH",
    "SkippedRow",
    "email_sort_key",
    "extract_component",
    "extract_last_component_from_row",
    "extract_name_part",
    "extract_number_after_dot",
    "extract_suffix",
    "generate_email_report",
    "generate_emails",
    "has_hyphen",
    "normalize_local_part",
    "normalize_email_domain",
    "normalize_email_override",
    "normalize_required_columns",
    "process_folder",
    "write_generation_report",
    "write_emails",
]


if __name__ == "__main__":  # pragma: no cover - CLI bootstrap
    raise SystemExit(main(default_folder=Path(__file__).resolve().parent))
