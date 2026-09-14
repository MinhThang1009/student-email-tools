import subprocess
import sys
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
    assert "github.event_name == 'workflow_call'" in release_engine
    assert (
        "EVENT_COMMIT: ${{ github.event.release.target_commitish }}" in release_engine
    )
    assert "The published release tag no longer resolves" in release_engine
    assert "ref: ${{ steps.release.outputs.commit_sha }}" in release_engine
    assert "publish_latest" in release_engine
    assert "gh api --paginate --slurp" in release_engine
    assert '"repos/${REPOSITORY}/releases?per_page=100" |' in release_engine
    assert "jq -r 'map(.[]) |" in release_engine
    dispatch_block = release_engine.split("  workflow_dispatch:", 1)[1].split(
        "  release:", 1
    )[0]
    assert "      tag:" not in dispatch_block
    assert "      commit_sha:" not in dispatch_block


def test_codeql_actions_use_the_current_reviewed_release_pin() -> None:
    codeql = (ROOT / ".github/workflows/codeql.yml").read_text(encoding="utf-8")
    scorecard = (ROOT / ".github/workflows/scorecard.yml").read_text(encoding="utf-8")

    expected = "b96794f015dfd88f77b49b1c93e0fa7110f94c63 # v4.38.0"
    assert codeql.count(expected) == 3
    assert expected in scorecard


def test_ci_requires_a_package_build_gate() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "package-build:" in ci
    assert "python -m build --sdist --wheel" in ci
    assert "needs: [test, package-build, maintenance-quality]" in ci
    assert "PACKAGE_BUILD_RESULT: ${{ needs.package-build.result }}" in ci


def test_action_pin_sync_defaults_to_workflows_present_in_this_repository() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from pathlib import Path; "
                "from scripts.sync_action_pins import "
                "action_repositories, workflow_paths; "
                "paths = workflow_paths(Path.cwd()); "
                "print(*(path.relative_to(Path.cwd()).as_posix() "
                "for path in paths), sep='\\n'); "
                "print(*(repository for path in paths "
                "for repository in sorted(action_repositories("
                "path, path.read_text(encoding='utf-8')))), "
                "sep='\\n')"
            ),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert ".github\\workflows" in result.stdout or ".github/workflows" in result.stdout
    assert "pypa/gh-action-pypi-publish" in result.stdout
