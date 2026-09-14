<div align="center">

# student-email-tools

Python tools for generating and formatting student email lists from local files.

[![CI](https://github.com/MinhThang1009/student-email-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/MinhThang1009/student-email-tools/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

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

Place Excel files in a dedicated directory and run:

```powershell
python emails.py "D:/data/course"
```

Or use the entry point after installing the package:

```powershell
generate-emails "D:/data/course"
```

Each Excel file produces a TXT file with the same basename. The parser handles
mixed code/name formats, Vietnamese diacritics, and invalid local-part
characters.

### 4.2 Format TXT files

```powershell
python 10lines.py "D:/data/emails.txt"
```

The command creates an `_output.txt` file, with 500 lines per block and 10 blank
lines between blocks by default. Customize the layout with:

```powershell
format-email-blocks "D:/data/emails.txt" --lines-per-block 100 --gap-lines 2
```

## 5. Development

```powershell
python -m pytest -q
python -m ruff check email_tools emails.py 10lines.py scripts/ci_runtime.py tests
python -m ruff format --check email_tools emails.py 10lines.py scripts/ci_runtime.py tests
python -m mypy --ignore-missing-imports email_tools emails.py 10lines.py scripts/ci_runtime.py
```

## 6. Contributing and support

Read [CONTRIBUTING.md](CONTRIBUTING.md), [SUPPORT.md](SUPPORT.md), and
[SECURITY.md](SECURITY.md). Do not commit real student data or email lists.

## 7. License

This project is released under the [MIT License](LICENSE).
