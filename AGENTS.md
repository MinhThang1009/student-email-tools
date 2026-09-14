# Agent Instructions

This file is the shared instruction entry point for coding agents that support
`AGENTS.md`.

## Working agreement

- Follow the user's request and the repository's applicable instructions.
- Read the relevant files before making a change and preserve project-specific
  conventions.
- Keep changes focused, validate them with the project's relevant checks, and
  report any verification that could not run.
- Do not commit, push, create pull requests, or change remote settings unless
  the user explicitly requests that action.

## Checks

- `python -m coverage run -m pytest -q`
- `python -m coverage report --fail-under=100`
- `python -m ruff check email_tools emails.py 10lines.py scripts/ci_runtime.py tests`
- `python -m ruff format --check email_tools emails.py 10lines.py scripts/ci_runtime.py tests`
- `python -m mypy --ignore-missing-imports email_tools emails.py 10lines.py scripts/ci_runtime.py`
- `python -m ruff check scripts --ignore E501`
- `python -m ruff format --check scripts`
- `python -m mypy --ignore-missing-imports scripts`
- `python -m compileall -q scripts`

## Pull requests

Before creating or updating a pull request, run
`python scripts/pr_template_preflight.py --title "<title>"`.

## Language

Use English for user-facing and contributor-facing documentation. Keep command
names, package names, protocol literals, and Conventional Commit prefixes in
their standard English form.
