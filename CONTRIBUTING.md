# Contributing to student-email-tools

Thanks for your interest in contributing! This project processes student lists
and email data, so do not include real data in commits, issues, pull requests,
or test fixtures.

## Workflow

1. Create a branch from `main`, for example `feat/improve-parser`.
2. Commit using [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
3. Run the full test, lint, format, and mypy checks.
4. Push the branch and open a pull request.

## Local checks

```powershell
python -m coverage run -m pytest -q
python -m coverage report --fail-under=100
python -m ruff check email_tools emails.py 10lines.py scripts/ci_runtime.py tests
python -m ruff format --check email_tools emails.py 10lines.py scripts/ci_runtime.py tests
python -m mypy --ignore-missing-imports email_tools emails.py 10lines.py scripts/ci_runtime.py
python -m ruff check scripts --ignore E501
python -m ruff format --check scripts
python -m mypy --ignore-missing-imports scripts
python -m compileall -q scripts
```

The 100% coverage gate covers the runtime package, legacy launchers, and the CI
runtime policy. Other maintenance scripts are validated separately with Ruff,
mypy, bytecode compilation, and their scheduled or documentation workflows.

The maintenance-script lint intentionally ignores `E501` for long parser and
report-format definitions; import, correctness, type, format, and bytecode checks
remain enforced.

## Code expectations

- Keep processing logic in the `email_tools` package; root launchers exist for
  compatibility with the legacy commands.
- Add a regression test for every behavior change.
- Use `pathlib`, type hints, and actionable error messages.
- Do not add a dependency unless it is necessary.

## Reporting issues

For ordinary bugs, open an [Issue](https://github.com/MinhThang1009/student-email-tools/issues)
with minimal reproduction steps and anonymized data. For security issues, see
[SECURITY.md](SECURITY.md).

All interactions must follow the [Code of Conduct](CODE_OF_CONDUCT.md).
