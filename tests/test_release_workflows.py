from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_please_passes_pat_to_reusable_release_engine() -> None:
    release_engine = (ROOT / ".github/workflows/release.yml").read_text(
        encoding="utf-8"
    )
    release_please = (ROOT / ".github/workflows/release-please.yml").read_text(
        encoding="utf-8"
    )

    assert "RELEASE_PLEASE_TOKEN:" in release_engine
    assert "required: true" in release_engine
    assert (
        "GH_TOKEN: ${{ secrets.RELEASE_PLEASE_TOKEN || github.token }}"
        in release_engine
    )
    assert "RELEASE_PLEASE_TOKEN: ${{ secrets.RELEASE_PLEASE_TOKEN }}" in release_please
    assert "github.event_name == 'release'" in release_engine


def test_codeql_actions_use_the_current_reviewed_release_pin() -> None:
    codeql = (ROOT / ".github/workflows/codeql.yml").read_text(encoding="utf-8")
    scorecard = (ROOT / ".github/workflows/scorecard.yml").read_text(encoding="utf-8")

    expected = "b96794f015dfd88f77b49b1c93e0fa7110f94c63 # v4.38.0"
    assert codeql.count(expected) == 3
    assert expected in scorecard
