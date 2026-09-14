import json

import pytest

from scripts.ci_runtime import build_outputs, load_policy, main


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


@pytest.mark.parametrize(
    "policy",
    [
        {},
        {"supported": [], "canary": "3.x"},
        {"supported": ["3.12", 3.13], "canary": "3.x"},
    ],
)
def test_build_outputs_rejects_invalid_supported_versions(policy) -> None:
    with pytest.raises(ValueError, match="supported versions"):
        build_outputs(policy)


@pytest.mark.parametrize(
    "policy",
    [
        {"supported": ["3.12"], "canary": ""},
        {"supported": ["3.12"], "canary": 3.13},
    ],
)
def test_build_outputs_rejects_invalid_canary(policy) -> None:
    with pytest.raises(ValueError, match="canary version"):
        build_outputs(policy)


def test_load_policy_rejects_non_object_json(tmp_path) -> None:
    policy_path = tmp_path / "policy.json"
    policy_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="JSON object"):
        load_policy(policy_path)


def test_ci_runtime_main_emits_github_outputs(capsys) -> None:
    assert main() == 0
    output = capsys.readouterr().out
    assert "matrix=" in output
    assert "canary=3.x" in output
