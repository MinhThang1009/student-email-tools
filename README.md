<div align="center">

# student-email-tools

Python tools for generating and formatting student email lists from local files.

[![CI](https://github.com/MinhThang1009/student-email-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/MinhThang1009/student-email-tools/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## Table of Contents

- [1. Overview](#1-overview)
- [2. Requirements](#2-requirements)
- [3. Installation](#3-installation)
- [4. Usage](#4-usage)
  - [4.1 Generate emails from Excel](#41-generate-emails-from-excel)
  - [4.2 Format TXT files](#42-format-txt-files)
  - [4.3 Recommended local data layout](#43-recommended-local-data-layout)
- [5. Development](#5-development)
- [6. Contributing and support](#6-contributing-and-support)
- [7. Releases](#7-releases)
- [8. License](#8-license)

## 1. Overview

This project provides two commands:

- Generate email addresses from the `First name` and `Last name` columns in an
  Excel file.
- Split a TXT file into spaced line blocks that are easy to copy and send.

Excel files, email lists, virtual environments, and caches are local data; they
do not belong in this repository.

## 2. Requirements

- Python 3.10 or newer.
- `pandas` and `openpyxl` for `.xlsx` files.
- Install the `xls` extra when `.xls` support is needed.

## 3. Installation

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -e ".[dev]"
```

For `.xls` support:

```powershell
./.venv/Scripts/python.exe -m pip install -e ".[xls]"
```

## 4. Usage

### 4.1 Generate emails from Excel

Place Excel files in `data/input/excel/` and run:

```powershell
python emails.py "data/input/excel" `
  --output-dir "data/output/emails" `
  --report "data/reports/email-quality.json"
```

Or use the entry point after installing the package:

```powershell
generate-emails "data/input/excel" `
  --output-dir "data/output/emails" `
  --report "data/reports/email-quality.json"
```

Generated email files contain 499 addresses per block, followed by 10 blank
lines.

Each Excel file produces a TXT file with the same basename. The parser handles
mixed code/name formats, Vietnamese diacritics, and invalid local-part
characters. If an `Email`, `Email address`, or custom email column is present,
valid values are used as row-level overrides. Duplicate output addresses are
reported and emitted once; ambiguous combinations of multiple email columns
are rejected. Numeric identifiers with at least 13 digits are
emitted as `identifier@domain`; shorter or alphanumeric prefixes use the
name-based rule.

For a quality report and safer output handling:

```powershell
generate-emails "data/input/excel" `
  --output-dir "data/output/emails" `
  --report "data/reports/email-quality.json" `
  --domain "vanlanguni.vn" `
  --no-overwrite
```

Use `--dry-run` to inspect the result without writing files. The report records
the Excel row numbers skipped or warned about, plus duplicate addresses. The
default domain remains `vanlanguni.vn` and the default behavior still writes
next to each input file, replacing an existing output unless `--no-overwrite`
is supplied.

### 4.2 Format TXT files

```powershell
python 10lines.py "data/output/emails/participants.txt" `
  --output-dir "data/output/formatted"
```

The command creates an `_output.txt` file, with 499 lines per block and 10 blank
lines between blocks by default. Customize the layout with:

```powershell
format-email-blocks "D:/data/emails.txt" --lines-per-block 100 --gap-lines 2
```

`format-email-blocks` also supports `--output-dir`, `--dry-run`, and
`--no-overwrite`.

### 4.3 Recommended local data layout

Keep private or generated files in the local data pipeline rather than beside
the source code:

```text
data/
├── input/
│   ├── excel/       # source .xlsx/.xls files
│   └── text/        # source .txt files for format-email-blocks
├── output/
│   ├── emails/      # generated email lists
│   └── formatted/   # block-formatted TXT files
└── reports/         # JSON quality reports
```

The data directories are intentionally ignored by Git. The checked-in
`.gitkeep` files preserve the layout without publishing participant data.

## 5. Development

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

## 6. Contributing and support

Read [CONTRIBUTING.md](CONTRIBUTING.md), [SUPPORT.md](SUPPORT.md), and
[SECURITY.md](SECURITY.md). Do not commit real student data or email lists.

## 7. Releases

Release Please creates the release pull request and GitHub Release. The release
workflow also builds source and wheel distributions and publishes them to PyPI
using Trusted Publishing.

Before the first package release, configure a PyPI Trusted Publisher with:

- Owner: `MinhThang1009`
- Repository: `student-email-tools`
- Workflow: `.github/workflows/release.yml`
- GitHub environment: `pypi`

See the [PyPI Trusted Publishers guide](https://docs.pypi.org/trusted-publishers/).

## 8. License

This project is released under the [MIT License](LICENSE).
