"""Backward-compatible launcher for the email generation command."""

from pathlib import Path

from email_tools.email_generator import (
    BLANK_LINES_PER_BLOCK,
    EMAIL_DOMAIN,
    EMAILS_PER_BLOCK,
    EXCEL_SUFFIXES,
    LONG_FIRST_PREFIX_LENGTH,
    email_sort_key,
    extract_component,
    extract_last_component_from_row,
    extract_name_part,
    extract_number_after_dot,
    extract_suffix,
    generate_emails,
    has_hyphen,
    main,
    normalize_local_part,
    normalize_required_columns,
    process_folder,
    write_emails,
)

__all__ = [
    "BLANK_LINES_PER_BLOCK",
    "EMAIL_DOMAIN",
    "EMAILS_PER_BLOCK",
    "EXCEL_SUFFIXES",
    "LONG_FIRST_PREFIX_LENGTH",
    "email_sort_key",
    "extract_component",
    "extract_last_component_from_row",
    "extract_name_part",
    "extract_number_after_dot",
    "extract_suffix",
    "generate_emails",
    "has_hyphen",
    "normalize_local_part",
    "normalize_required_columns",
    "process_folder",
    "write_emails",
]


if __name__ == "__main__":
    raise SystemExit(main(default_folder=Path(__file__).resolve().parent))
