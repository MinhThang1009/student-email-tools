from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ci_gates_all_maintenance_scripts() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "maintenance-quality:" in ci
    assert "python -m ruff check scripts --ignore E501" in ci
    assert "python -m ruff format --check scripts" in ci
    assert "python -m mypy --ignore-missing-imports scripts" in ci
    assert "python -m compileall -q scripts" in ci
    assert "needs: [test, package-build, maintenance-quality]" in ci
    assert "MAINTENANCE_RESULT: ${{ needs.maintenance-quality.result }}" in ci
