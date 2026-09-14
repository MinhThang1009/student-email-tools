from email_tools.text_blocks import (
    find_text_files,
    format_lines,
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
