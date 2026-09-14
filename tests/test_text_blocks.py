from pathlib import Path

import pytest

from email_tools.text_blocks import (
    find_text_files,
    format_lines,
    main,
    output_path_for,
    parse_args,
    process_folder,
    process_text_file,
)


def test_format_lines_adds_gaps_only_between_blocks() -> None:
    assert format_lines(["a", "b", "c"], lines_per_block=2, gap_lines=2) == [
        "a",
        "b",
        "",
        "",
        "c",
    ]


def test_format_lines_uses_499_line_blocks_and_10_blank_lines_by_default() -> None:
    formatted = format_lines([str(index) for index in range(500)])

    assert formatted[498] == "498"
    assert formatted[499:509] == [""] * 10
    assert formatted[509] == "499"


def test_process_folder_does_not_reprocess_generated_outputs(tmp_path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("a\nb\nc\n", encoding="utf-8")

    outputs = process_folder(tmp_path, lines_per_block=2, gap_lines=1)
    output = tmp_path / "source_output.txt"

    assert outputs == [output.resolve()]
    assert output.read_text(encoding="utf-8") == "a\nb\n\nc\n"
    assert find_text_files(tmp_path) == [source]

    process_text_file(source, lines_per_block=2, gap_lines=1)
    assert not (tmp_path / "source_output_output.txt").exists()


def test_format_lines_validates_arguments() -> None:
    with pytest.raises(ValueError, match="lines_per_block"):
        format_lines(["a"], lines_per_block=0)
    with pytest.raises(ValueError, match="gap_lines"):
        format_lines(["a"], gap_lines=-1)
    assert format_lines([]) == []


def test_output_path_and_process_text_file_safety(tmp_path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("a\nb\n", encoding="utf-8")
    output_dir = tmp_path / "nested"

    with pytest.raises(FileNotFoundError, match="TXT file not found"):
        process_text_file(tmp_path / "missing.txt")

    assert output_path_for(source) == tmp_path / "source_output.txt"
    assert (
        output_path_for(source, output_dir)
        == output_dir.resolve() / "source_output.txt"
    )

    with pytest.raises(ValueError, match="cannot be used together"):
        process_text_file(
            source, output_dir=output_dir, output_path=tmp_path / "out.txt"
        )
    with pytest.raises(ValueError, match="must differ"):
        process_text_file(source, output_path=source)

    dry_run_output = output_dir / "dry.txt"
    assert (
        process_text_file(source, output_path=dry_run_output, dry_run=True)
        == dry_run_output.resolve()
    )
    assert not dry_run_output.exists()

    output = process_text_file(source, output_dir=output_dir)
    assert output.read_text(encoding="utf-8") == "a\nb\n"
    with pytest.raises(FileExistsError, match="already exists"):
        process_text_file(source, output_path=output, overwrite=False)


def test_process_text_file_preserves_empty_input(tmp_path) -> None:
    source = tmp_path / "empty.txt"
    source.write_text("", encoding="utf-8")

    output = process_text_file(source)

    assert output.read_text(encoding="utf-8") == ""


def test_find_text_files_filters_generated_and_lock_files(tmp_path) -> None:
    first = tmp_path / "b.TXT"
    second = tmp_path / "a.txt"
    first.write_text("b", encoding="utf-8")
    second.write_text("a", encoding="utf-8")
    (tmp_path / "a_output.txt").write_text("generated", encoding="utf-8")
    (tmp_path / "~$locked.txt").write_text("locked", encoding="utf-8")
    (tmp_path / "notes.csv").write_text("ignored", encoding="utf-8")

    assert find_text_files(tmp_path) == [second, first]


def test_find_text_files_breaks_casefold_ties_deterministically(monkeypatch) -> None:
    candidates = [Path("z.txt"), Path("a.txt"), Path("A.txt")]
    monkeypatch.setattr(Path, "iterdir", lambda _path: iter(candidates))
    monkeypatch.setattr(Path, "is_file", lambda _path: True)

    assert [path.name for path in find_text_files(Path("input"))] == [
        "A.txt",
        "a.txt",
        "z.txt",
    ]


def test_process_folder_validates_and_supports_output_controls(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="Directory not found"):
        process_folder(tmp_path / "missing")
    with pytest.raises(FileNotFoundError, match="No TXT files found"):
        process_folder(tmp_path)

    source = tmp_path / "source.txt"
    source.write_text("a\nb\nc\n", encoding="utf-8")
    output_dir = tmp_path / "output"
    outputs = process_folder(
        tmp_path,
        output_dir=output_dir,
        lines_per_block=2,
        gap_lines=1,
    )
    assert outputs == [output_dir.resolve() / "source_output.txt"]
    assert outputs[0].read_text(encoding="utf-8") == "a\nb\n\nc\n"

    with pytest.raises(FileExistsError, match="already exists"):
        process_folder(tmp_path, output_dir=output_dir, overwrite=False)

    dry_output_dir = tmp_path / "dry"
    dry_outputs = process_folder(tmp_path, output_dir=dry_output_dir, dry_run=True)
    assert dry_outputs == [dry_output_dir.resolve() / "source_output.txt"]
    assert not dry_output_dir.exists()

    no_overwrite_dir = tmp_path / "fresh"
    no_overwrite_outputs = process_folder(
        tmp_path,
        output_dir=no_overwrite_dir,
        overwrite=False,
    )
    assert no_overwrite_outputs == [no_overwrite_dir.resolve() / "source_output.txt"]


def test_process_folder_rejects_casefolded_output_collisions(
    tmp_path, monkeypatch
) -> None:
    first = tmp_path / "a.txt"
    second = tmp_path / "a.TXT"
    monkeypatch.setattr(
        "email_tools.text_blocks.find_text_files",
        lambda folder: [first, second],
    )

    with pytest.raises(ValueError, match="same output"):
        process_folder(tmp_path)


def test_parse_args_and_main_cover_file_and_folder_paths(tmp_path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("a\nb\n", encoding="utf-8")
    args = parse_args(
        [
            str(source),
            "--lines-per-block",
            "1",
            "--gap-lines",
            "0",
            "--output-dir",
            "out",
            "--dry-run",
            "--no-overwrite",
        ]
    )
    assert args.lines_per_block == 1
    assert args.gap_lines == 0
    assert args.output_dir.name == "out"
    assert args.dry_run is True
    assert args.no_overwrite is True

    assert main([str(source), "--dry-run"]) == 0
    assert main([str(tmp_path), "--dry-run"]) == 0
