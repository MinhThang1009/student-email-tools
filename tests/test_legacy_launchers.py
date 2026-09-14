import importlib
from pathlib import Path


def test_email_launcher_preserves_legacy_exports() -> None:
    launcher = importlib.import_module("emails")

    assert launcher.EMAIL_DOMAIN == "vanlanguni.vn"
    assert launcher.EMAILS_PER_BLOCK == 499
    assert launcher.BLANK_LINES_PER_BLOCK == 10
    assert launcher.generate_emails is not None
    assert launcher.process_folder is not None


def test_package_version_matches_source_manifest() -> None:
    package = importlib.import_module("email_tools")
    project_file = Path(__file__).resolve().parents[1] / "pyproject.toml"
    project_version = next(
        line.split("=", maxsplit=1)[1].strip().strip('"')
        for line in project_file.read_text(encoding="utf-8").splitlines()
        if line.startswith("version =")
    )

    assert package.__version__ == project_version


def test_package_version_source_lookup_handles_unreadable_manifest(monkeypatch) -> None:
    package = importlib.import_module("email_tools")
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("unreadable")),
    )

    assert package._source_project_version() is None


def test_text_launcher_preserves_legacy_exports() -> None:
    launcher = importlib.import_module("10lines")

    assert launcher.DEFAULT_LINES_PER_BLOCK == 499
    assert launcher.DEFAULT_GAP_LINES == 10
    assert launcher.format_lines(["a"]) == ["a"]
    assert launcher.process_text_file is not None
