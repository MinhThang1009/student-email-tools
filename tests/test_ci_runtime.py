import json

import pytest

from scripts.ci_runtime import build_outputs, load_policy


def test_build_outputs_creates_matrix_and_canary() -> None:
    matrix, canary = build_outputs({"supported": ["3.10", "3.11"], "canary": "3.x"})

    assert json.loads(matrix) == {"python-version": ["3.10", "3.11"]}
    assert canary == "3.x"


def test_repository_policy_includes_python_314() -> None:
    matrix, _ = build_outputs(load_policy())

    assert "3.14" in json.loads(matrix)["python-version"]


def test_build_outputs_rejects_duplicate_supported_versions() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        build_outputs({"supported": ["3.12", "3.12"], "canary": "3.x"})
