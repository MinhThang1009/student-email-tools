import importlib


def test_email_launcher_preserves_legacy_exports() -> None:
    launcher = importlib.import_module("emails")

    assert launcher.EMAIL_DOMAIN == "vanlanguni.vn"
    assert launcher.generate_emails is not None
    assert launcher.process_folder is not None


def test_text_launcher_preserves_legacy_exports() -> None:
    launcher = importlib.import_module("10lines")

    assert launcher.DEFAULT_LINES_PER_BLOCK == 500
    assert launcher.format_lines(["a"]) == ["a"]
    assert launcher.process_text_file is not None
