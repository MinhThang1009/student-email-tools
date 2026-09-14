"""Load the reviewed Python runtime policy for GitHub Actions."""

from __future__ import annotations

import json
from pathlib import Path

POLICY_PATH = Path(__file__).resolve().parents[1] / ".github" / "python-versions.json"


def load_policy(path: Path = POLICY_PATH) -> dict[str, object]:
    """Load and validate the runtime policy JSON object."""
    with path.open(encoding="utf-8") as policy_file:
        policy = json.load(policy_file)
    if not isinstance(policy, dict):
        raise ValueError("Runtime policy must be a JSON object")
    return policy


def build_outputs(policy: dict[str, object]) -> tuple[str, str]:
    """Build GitHub Actions outputs from a runtime policy."""
    supported = policy.get("supported")
    canary = policy.get("canary")
    if (
        not isinstance(supported, list)
        or not supported
        or not all(isinstance(version, str) and version for version in supported)
    ):
        raise ValueError("Runtime policy must contain non-empty supported versions")
    if len(set(supported)) != len(supported):
        raise ValueError("Runtime policy contains duplicate supported versions")
    if not isinstance(canary, str) or not canary:
        raise ValueError("Runtime policy must contain a canary version")

    matrix = json.dumps({"python-version": supported}, separators=(",", ":"))
    return matrix, canary


def main() -> int:
    """Print GitHub Actions output assignments."""
    matrix, canary = build_outputs(load_policy())
    print(f"matrix={matrix}")
    print(f"canary={canary}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CI bootstrap
    raise SystemExit(main())
