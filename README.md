<div align="center">

# student-email-tools

Công cụ Python tạo và định dạng danh sách email sinh viên từ file cục bộ.

[![CI](https://github.com/MinhThang1009/student-email-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/MinhThang1009/student-email-tools/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## 1. Tổng quan

Project cung cấp hai lệnh:

- Tạo email từ các cột `First name` và `Last name` trong file Excel.
- Chia file TXT thành các block dòng có khoảng cách để dễ sao chép và gửi.

File Excel, danh sách email, virtualenv và cache chỉ là dữ liệu local; chúng
không thuộc repository.

## 2. Yêu cầu

- Python 3.10 trở lên.
- `pandas` và `openpyxl` cho file `.xlsx`.
- Cài thêm extra `xls` nếu cần đọc file `.xls`.

## 3. Cài đặt

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Để đọc định dạng `.xls`:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[xls]"
```

## 4. Sử dụng

### 4.1 Tạo email từ Excel

Đặt file Excel trong một thư mục riêng rồi chạy:

```powershell
python emails.py "D:\du-lieu\course"
```

Hoặc dùng entry point sau khi cài package:

```powershell
generate-emails "D:\du-lieu\course"
```

Mỗi file Excel tạo một file TXT cùng tên. Parser xử lý các dạng mã/tên hỗn
hợp, loại dấu tiếng Việt và loại ký tự không hợp lệ trong local part.

### 4.2 Định dạng file TXT

```powershell
python 10lines.py "D:\du-lieu\emails.txt"
```

Lệnh tạo file hậu tố `_output.txt`, mặc định 500 dòng mỗi block và 10 dòng
trống giữa các block. Có thể thay đổi:

```powershell
format-email-blocks "D:\du-lieu\emails.txt" --lines-per-block 100 --gap-lines 2
```

## 5. Phát triển

```powershell
python -m pytest -q
python -m ruff check email_tools emails.py 10lines.py tests
python -m ruff format --check email_tools emails.py 10lines.py tests
python -m mypy --ignore-missing-imports email_tools emails.py 10lines.py
```

## 6. Đóng góp và hỗ trợ

Đọc [CONTRIBUTING.md](CONTRIBUTING.md), [SUPPORT.md](SUPPORT.md) và
[SECURITY.md](SECURITY.md). Không commit dữ liệu người học hoặc danh sách
email thật.

## 7. License

Project phát hành theo [MIT License](LICENSE).
