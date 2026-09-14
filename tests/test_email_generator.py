import json
from pathlib import Path

import pandas as pd
import pytest

from email_tools.email_generator import (
    DuplicateEmail,
    EmailGenerationReport,
    SkippedRow,
    email_sort_key,
    extract_component,
    extract_last_component,
    extract_last_component_from_row,
    extract_name_part,
    extract_number_after_dot,
    extract_suffix,
    find_excel_files,
    generate_email_report,
    generate_emails,
    has_hyphen,
    main,
    normalize_email_domain,
    normalize_email_override,
    normalize_integral_numeric_text,
    normalize_local_part,
    normalize_required_columns,
    parse_args,
    process_folder,
    write_emails,
    write_generation_report,
)


def test_extract_component_supports_values_with_or_without_hyphens() -> None:
    assert extract_component("  Nguyễn Văn - 71K01  ") == "Nguyễn Văn"
    assert extract_component("Nguyễn Văn") == "Nguyễn Văn"
    assert extract_component("- 71K01", leading_hyphen_uses_last_word=True) is None
    assert (
        extract_component("- Nguyễn Văn A", leading_hyphen_uses_last_word=True) == "A"
    )
    assert extract_component(None) is None


def test_leading_class_separator_uses_given_name_from_first_name() -> None:
    assert (
        extract_last_component_from_row(
            "24772020101CT - Nguyễn Lê An Như", "- 71K31DUOC01"
        )
        == "Như"
    )
    assert (
        extract_last_component_from_row("2500115423 - Hồ Nguyễn Trung Khoa", "-")
        == "Khoa"
    )


def test_normalize_local_part_handles_vietnamese_characters() -> None:
    assert normalize_local_part("Đặng Ánh") == "danganh"
    assert normalize_local_part(".,-") is None


def test_email_sort_key_requires_a_number_after_a_dot() -> None:
    numbered = "an.207tt50948@vanlanguni.vn"
    no_dot = "24042108031986@vanlanguni.vn"

    assert email_sort_key(numbered) < email_sort_key(no_dot)
    assert email_sort_key("an.207@other.example") == (0, 207, "an.207@other.example")
    assert extract_number_after_dot(f"a.{'1' * 5000}@example.com") is None


def test_generate_emails_handles_mixed_source_formats() -> None:
    dataframe = pd.DataFrame(
        {
            "First name": [
                "2500115424 - Nguyễn Văn A",
                "24042108031986 - Lê Thị Hậu",
                "24772020101CT - Nguyễn Lê An Như",
                "2500115425 - Nguyễn Văn C",
                "2500115426",
                "2673201040001 - Soles",
            ],
            "Last name": [
                "An - 71K01",
                "An - 71K01",
                "- 71K31DUOC01",
                "Ý - 71K01",
                "Bình",
                "Adam",
            ],
        }
    )

    assert generate_emails(dataframe) == [
        "an.2500115424@vanlanguni.vn",
        "y.2500115425@vanlanguni.vn",
        "binh.2500115426@vanlanguni.vn",
        "nhu.24772020101ct@vanlanguni.vn",
        "24042108031986@vanlanguni.vn",
        "2673201040001@vanlanguni.vn",
    ]


def test_thirteen_digit_numeric_identifiers_use_the_identifier_email() -> None:
    identifiers = [
        "2672103020113",
        "2672104090130",
        "2672104090133",
        "2673104011231",
        "2673201040001",
        "2673201041167",
        "2673201041551",
        "2673201041884",
        "2673201043697",
        "2673201043993",
        "2673201044204",
    ]
    dataframe = pd.DataFrame(
        {
            "First name": [f"{identifier} - Student" for identifier in identifiers],
            "Last name": ["Family - 71A"] * len(identifiers),
        }
    )

    assert generate_emails(dataframe) == [
        f"{identifier}@vanlanguni.vn" for identifier in identifiers
    ]


def test_extract_helpers_cover_empty_and_fallback_values() -> None:
    assert extract_component("") is None
    assert extract_component("-") is None
    assert extract_component("- Name", leading_hyphen_uses_last_word=False) is None
    assert extract_component("- Name", leading_hyphen_uses_last_word=True) == "Name"
    assert extract_component("- 71K01", leading_hyphen_uses_last_word=True) is None
    assert extract_suffix(None) is None
    assert extract_suffix("Name") is None
    assert extract_suffix("Name - ") is None
    assert extract_name_part("Name") is None
    assert extract_name_part("Code - Name - Group") == "Name"
    assert has_hyphen(None) is False
    assert has_hyphen("") is False
    assert has_hyphen("A-B") is True
    assert extract_last_component("- Name") == "Name"
    assert extract_last_component_from_row("No separator", "- 71K01") is None
    assert extract_last_component_from_row("Code - 123 - Group", "- 71K01") is None


def test_integral_numeric_identifiers_do_not_gain_spurious_zeroes() -> None:
    assert normalize_integral_numeric_text("2673201040001.0") == "2673201040001"
    assert normalize_integral_numeric_text("2673201040001.00") == "2673201040001"
    assert normalize_integral_numeric_text("2673201040001.5") == "2673201040001.5"

    dataframe = pd.DataFrame(
        {
            "First name": [2673201040001.0, "2673201040001.0"],
            "Last name": ["Adam", "Adam"],
        }
    )
    assert generate_emails(dataframe) == ["2673201040001@vanlanguni.vn"]


def test_long_alphanumeric_prefixes_keep_the_name_based_rule() -> None:
    dataframe = pd.DataFrame(
        {
            "First name": ["ALPHA123456789 - Given Name"],
            "Last name": ["Student - 71A"],
        }
    )

    assert generate_emails(dataframe) == ["student.alpha123456789@vanlanguni.vn"]


def test_normalize_email_values_and_domains() -> None:
    assert normalize_email_domain(" @Example.COM ") == "example.com"
    assert normalize_email_override(r"User\@Example.COM") == "user@example.com"
    assert normalize_email_override(r"User\\@Example.COM") == "user@example.com"
    assert normalize_email_override("not-an-email") is None
    assert normalize_email_override(".user@example.com") is None
    assert normalize_email_override("user.@example.com") is None
    assert normalize_email_override("user..name@example.com") is None
    assert normalize_email_override(None) is None
    assert normalize_email_override("a" * 65 + "@example.com") is None
    assert normalize_email_override("a" * 250 + "@example.com") is None
    assert normalize_email_override(pd.NA) is None

    with pytest.raises(ValueError, match="Invalid email domain"):
        normalize_email_domain("not a domain")
    with pytest.raises(ValueError, match="Invalid email domain"):
        normalize_email_domain("@@example.com")


def test_normalize_required_columns_supports_email_aliases_and_errors() -> None:
    dataframe = pd.DataFrame(
        [["Code - Name", "Last", "user@example.com"]],
        columns=[" FIRST NAME ", "Last Name", "Email Address"],
    )
    normalized = normalize_required_columns(dataframe, "input.xlsx")
    assert list(normalized.columns) == ["first name", "last name", "email"]

    custom = pd.DataFrame(
        [["Code - Name", "Last", "user@example.com"]],
        columns=["First Name", "Last Name", "Student Contact"],
    )
    assert (
        "email"
        in normalize_required_columns(
            custom, "input.xlsx", email_column="student contact"
        ).columns
    )

    with pytest.raises(ValueError, match="is missing columns"):
        normalize_required_columns(pd.DataFrame({"First name": ["A"]}), "input.xlsx")

    duplicate_required = pd.DataFrame(
        [["A", "B", "C"]], columns=["First name", "first NAME", "Last name"]
    )
    with pytest.raises(ValueError, match="has duplicate columns"):
        normalize_required_columns(duplicate_required, "input.xlsx")

    with pytest.raises(ValueError, match="must not be empty"):
        normalize_required_columns(dataframe, "input.xlsx", email_column=" ")
    with pytest.raises(ValueError, match="must differ"):
        normalize_required_columns(dataframe, "input.xlsx", email_column="First Name")
    with pytest.raises(ValueError, match="is missing email column"):
        normalize_required_columns(dataframe, "input.xlsx", email_column="other")

    duplicate_email = pd.DataFrame(
        [["A", "B", "one@example.com", "two@example.com"]],
        columns=["First name", "Last name", "Email", "E-mail"],
    )
    with pytest.raises(ValueError, match="has duplicate email columns"):
        normalize_required_columns(duplicate_email, "input.xlsx")

    explicit_email_with_alias = pd.DataFrame(
        [["A", "B", "one@example.com", "two@example.com"]],
        columns=["First name", "Last name", "email", "Student Contact"],
    )
    with pytest.raises(ValueError, match="has duplicate email columns"):
        normalize_required_columns(
            explicit_email_with_alias,
            "input.xlsx",
            email_column="Student Contact",
        )

    pandas_mangled_required = pd.DataFrame(
        [["A", "B", "C"]], columns=["First name", "First name.1", "Last name"]
    )
    with pytest.raises(ValueError, match="has duplicate columns"):
        normalize_required_columns(pandas_mangled_required, "input.xlsx")

    pandas_mangled_required_with_spacing = pd.DataFrame(
        [["A", "B", "C"]],
        columns=["First name ", "First name ", "Last name"],
    )
    with pytest.raises(ValueError, match="has duplicate columns"):
        normalize_required_columns(
            pandas_mangled_required_with_spacing,
            "input.xlsx",
        )

    pandas_mangled_email = pd.DataFrame(
        [["A", "B", "one@example.com", "two@example.com"]],
        columns=["First name", "Last name", "Email", "Email.1"],
    )
    with pytest.raises(ValueError, match="has duplicate email columns"):
        normalize_required_columns(pandas_mangled_email, "input.xlsx")

    pandas_mangled_custom_email = pd.DataFrame(
        [["A", "B", "one@example.com", "two@example.com"]],
        columns=["First name", "Last name", "Student Contact", "Student Contact.1"],
    )
    with pytest.raises(ValueError, match="has duplicate email columns"):
        normalize_required_columns(
            pandas_mangled_custom_email,
            "input.xlsx",
            email_column="Student Contact",
        )


def test_generate_email_report_handles_override_warning_skip_and_duplicates() -> None:
    dataframe = pd.DataFrame(
        {
            "First name": [
                "2500115424 - Alpha Beta",
                "2500115424 - Alpha Beta",
                None,
                "2500115424 - Alpha Beta",
            ],
            "Last name": ["Gamma - 71A", "Gamma - 71A", None, "Gamma - 71A"],
            "Email": [
                r"Manual\@Example.COM",
                "invalid",
                "invalid",
                None,
            ],
        }
    )

    report = generate_email_report(dataframe, "input.xlsx")

    assert report.total_rows == 4
    assert report.emails == [
        "gamma.2500115424@vanlanguni.vn",
        "manual@example.com",
    ]
    assert report.skipped_rows == [
        SkippedRow(4, "invalid email override and unusable name data")
    ]
    assert report.warnings == [
        SkippedRow(3, "invalid email override; generated from names")
    ]
    assert report.duplicate_emails == [
        DuplicateEmail("gamma.2500115424@vanlanguni.vn", (3, 5))
    ]
    assert report.to_dict()["generated_emails"] == 2


def test_generate_email_report_records_unusable_row_without_override() -> None:
    dataframe = pd.DataFrame({"First name": [None], "Last name": [None]})

    report = generate_email_report(dataframe, "input.xlsx")

    assert report.skipped_rows == [SkippedRow(2, "unusable name data")]
    assert report.warnings == []


def test_generate_emails_accepts_custom_domain_and_explicit_column() -> None:
    dataframe = pd.DataFrame(
        {
            "First name": ["Code - Alpha"],
            "Last name": ["Beta"],
            "Student contact": ["person@other.example"],
        }
    )

    assert generate_emails(
        dataframe,
        email_domain="@custom.example",
        email_column="Student Contact",
    ) == ["person@other.example"]


def test_find_excel_files_filters_lock_files_and_sorts(tmp_path) -> None:
    (tmp_path / "b.XLSX").touch()
    (tmp_path / "a.xls").touch()
    (tmp_path / "~$locked.xlsx").touch()
    (tmp_path / "notes.txt").touch()
    (tmp_path / "nested").mkdir()

    assert find_excel_files(tmp_path) == [tmp_path / "a.xls", tmp_path / "b.XLSX"]


def test_find_excel_files_breaks_casefold_ties_deterministically(monkeypatch) -> None:
    candidates = [Path("z.xlsx"), Path("a.xlsx"), Path("A.xlsx")]
    monkeypatch.setattr(Path, "iterdir", lambda _path: iter(candidates))
    monkeypatch.setattr(Path, "is_file", lambda _path: True)

    assert [path.name for path in find_excel_files(Path("input"))] == [
        "A.xlsx",
        "a.xlsx",
        "z.xlsx",
    ]


def test_write_emails_validates_safety_and_formats_blocks(tmp_path) -> None:
    with pytest.raises(ValueError, match="block_size"):
        write_emails(["a@example.com"], tmp_path / "out.txt", block_size=0)

    dry_run_path = tmp_path / "dry" / "out.txt"
    write_emails(["a@example.com"], dry_run_path, dry_run=True)
    assert not dry_run_path.exists()

    output = tmp_path / "nested" / "out.txt"
    write_emails(["a@example.com", "b@example.com"], output, block_size=1)
    assert (
        output.read_text(encoding="utf-8")
        == "a@example.com\n" + "\n" * 10 + "b@example.com\n" + "\n" * 10
    )

    with pytest.raises(FileExistsError, match="already exists"):
        write_emails(["c@example.com"], output, overwrite=False)


def test_writers_reject_link_like_output_paths(tmp_path, monkeypatch) -> None:
    output = tmp_path / "out.txt"
    output.write_text("existing\n", encoding="utf-8")
    source = tmp_path / "source.txt"
    source.write_text("a\n", encoding="utf-8")

    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda path: path == output,
    )

    with pytest.raises(ValueError, match="symbolic link"):
        write_emails(["a@example.com"], output)

    from email_tools.text_blocks import process_text_file

    with pytest.raises(ValueError, match="symbolic link"):
        process_text_file(source, output_path=output)


def test_write_emails_uses_499_email_blocks_and_10_blank_lines(tmp_path) -> None:
    output = tmp_path / "default-blocks.txt"
    emails = [f"student{index}@example.com" for index in range(500)]

    write_emails(emails, output)

    lines = output.read_text(encoding="utf-8").splitlines()
    assert lines[498] == "student498@example.com"
    assert lines[499:509] == [""] * 10
    assert lines[509] == "student499@example.com"


def test_write_generation_report_serializes_and_respects_flags(tmp_path) -> None:
    report = EmailGenerationReport(1, ["a@example.com"], [], [], [])
    output = tmp_path / "reports" / "report.json"
    write_generation_report({"input.xlsx": report}, output, email_domain="example.com")
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["email_domain"] == "example.com"
    assert payload["files"]["input.xlsx"]["generated_emails"] == 1

    dry_run = tmp_path / "dry" / "report.json"
    write_generation_report(
        {"input.xlsx": report}, dry_run, email_domain="example.com", dry_run=True
    )
    assert not dry_run.exists()

    with pytest.raises(FileExistsError, match="already exists"):
        write_generation_report(
            {"input.xlsx": report}, output, email_domain="example.com", overwrite=False
        )


def test_process_folder_writes_outputs_and_report(tmp_path, monkeypatch) -> None:
    source = tmp_path / "source.xlsx"
    source.touch()
    output_dir = tmp_path / "output"
    report_path = tmp_path / "reports" / "quality.json"

    def fake_read_excel(path, dtype):
        assert path == source
        assert dtype is str
        return pd.DataFrame(
            {
                "First name": ["2500115424 - Alpha"],
                "Last name": ["Beta - 71A"],
            }
        )

    monkeypatch.setattr("email_tools.email_generator.pd.read_excel", fake_read_excel)
    outputs = process_folder(
        tmp_path,
        output_dir=output_dir,
        report_path=report_path,
        email_domain="custom.example",
    )

    assert outputs == [output_dir.resolve() / "source.txt"]
    assert outputs[0].read_text(encoding="utf-8") == "beta.2500115424@custom.example\n"
    assert report_path.exists()

    with pytest.raises(ValueError, match="must not overwrite"):
        process_folder(tmp_path, output_dir=output_dir, report_path=source)

    with pytest.raises(ValueError, match="must differ"):
        process_folder(tmp_path, output_dir=output_dir, report_path=outputs[0])


def test_process_folder_supports_no_overwrite_without_report(
    tmp_path, monkeypatch
) -> None:
    source = tmp_path / "source.xlsx"
    source.touch()
    output_dir = tmp_path / "output"

    monkeypatch.setattr(
        "email_tools.email_generator.pd.read_excel",
        lambda path, dtype: pd.DataFrame(
            {"First name": ["Code - Alpha"], "Last name": ["Beta"]}
        ),
    )

    outputs = process_folder(
        tmp_path,
        output_dir=output_dir,
        overwrite=False,
    )

    assert outputs == [output_dir.resolve() / "source.txt"]
    assert outputs[0].exists()


def test_process_folder_reports_saved_only_after_writing(
    tmp_path, monkeypatch, capsys
) -> None:
    source = tmp_path / "source.xlsx"
    source.touch()
    monkeypatch.setattr(
        "email_tools.email_generator.pd.read_excel",
        lambda path, dtype: pd.DataFrame(
            {"First name": ["Code - Alpha"], "Last name": ["Beta"]}
        ),
    )

    def fail_write(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("email_tools.email_generator.write_emails", fail_write)

    with pytest.raises(OSError, match="disk full"):
        process_folder(tmp_path)

    assert "Saved" not in capsys.readouterr().out


def test_process_folder_supports_dry_run_and_rejects_conflicts(
    tmp_path, monkeypatch
) -> None:
    source = tmp_path / "source.xlsx"
    source.touch()
    output_dir = tmp_path / "output"
    report_path = tmp_path / "report.json"

    monkeypatch.setattr(
        "email_tools.email_generator.pd.read_excel",
        lambda path, dtype: pd.DataFrame(
            {"First name": ["Code - Alpha"], "Last name": ["Beta"]}
        ),
    )
    outputs = process_folder(
        tmp_path,
        output_dir=output_dir,
        report_path=report_path,
        dry_run=True,
    )
    assert outputs == [output_dir.resolve() / "source.txt"]
    assert not output_dir.exists()
    assert not report_path.exists()

    output_dir.mkdir()
    outputs[0].write_text("old\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match="already exists"):
        process_folder(tmp_path, output_dir=output_dir, overwrite=False)

    report_path.write_text("old report", encoding="utf-8")
    with pytest.raises(FileExistsError, match="Report file already exists"):
        process_folder(
            tmp_path,
            output_dir=tmp_path / "another-output",
            report_path=report_path,
            overwrite=False,
        )


def test_process_folder_validates_folder_inputs_and_output_collisions(
    tmp_path, monkeypatch
) -> None:
    with pytest.raises(FileNotFoundError, match="Directory not found"):
        process_folder(tmp_path / "missing")
    with pytest.raises(FileNotFoundError, match="No Excel files found"):
        process_folder(tmp_path)

    (tmp_path / "same.xlsx").touch()
    (tmp_path / "same.xls").touch()
    monkeypatch.setattr(
        "email_tools.email_generator.pd.read_excel",
        lambda path, dtype: pd.DataFrame(
            {"First name": ["Code - Alpha"], "Last name": ["Beta"]}
        ),
    )
    with pytest.raises(ValueError, match="same output"):
        process_folder(tmp_path)


def test_process_folder_rejects_link_like_output_directories(
    tmp_path, monkeypatch
) -> None:
    source = tmp_path / "source.xlsx"
    source.touch()
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == output_dir)

    with pytest.raises(ValueError, match="symbolic link"):
        process_folder(tmp_path, output_dir=output_dir)


def test_process_folder_rejects_duplicate_excel_headers(tmp_path) -> None:
    source = tmp_path / "duplicate-headers.xlsx"
    pd.DataFrame(
        [["2500115424 - Alpha", "2500115424 - Wrong", "Beta - 71A"]],
        columns=["First name", "First name", "Last name"],
    ).to_excel(source, index=False)

    with pytest.raises(ValueError, match="has duplicate columns"):
        process_folder(tmp_path)


def test_parse_args_and_main_forward_new_options(tmp_path, monkeypatch) -> None:
    args = parse_args(
        [
            str(tmp_path),
            "--output-dir",
            "out",
            "--report",
            "report.json",
            "--domain",
            "custom.example",
            "--email-column",
            "Contact",
            "--dry-run",
            "--no-overwrite",
        ]
    )
    assert args.output_dir == Path("out")
    assert args.report_path == Path("report.json")
    assert args.domain == "custom.example"
    assert args.email_column == "Contact"
    assert args.dry_run is True
    assert args.no_overwrite is True

    captured = {}

    def fake_process_folder(folder, **kwargs):
        captured["folder"] = folder
        captured.update(kwargs)
        return []

    monkeypatch.setattr(
        "email_tools.email_generator.process_folder", fake_process_folder
    )
    assert (
        main(
            [
                str(tmp_path),
                "--output-dir",
                "out",
                "--report",
                "report.json",
                "--domain",
                "custom.example",
                "--email-column",
                "Contact",
                "--dry-run",
                "--no-overwrite",
            ]
        )
        == 0
    )
    assert captured["folder"] == Path(tmp_path)
    assert captured["output_dir"] == Path("out")
    assert captured["report_path"] == Path("report.json")
    assert captured["email_domain"] == "custom.example"
    assert captured["email_column"] == "Contact"
    assert captured["dry_run"] is True
    assert captured["overwrite"] is False
