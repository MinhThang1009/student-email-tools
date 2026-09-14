# Đóng góp cho student-email-tools

Cảm ơn bạn đã quan tâm đóng góp! Project này xử lý danh sách người học và dữ
liệu email, vì vậy không được đưa dữ liệu thật lên commit, issue, pull request
hoặc test fixture.

## Quy trình

1. Tạo branch từ `main`, ví dụ `feat/improve-parser`.
2. Commit theo [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
3. Chạy toàn bộ test, lint, format check và mypy.
4. Push branch và mở pull request.

## Kiểm tra local

```powershell
python -m pytest -q
python -m ruff check email_tools emails.py 10lines.py tests
python -m ruff format --check email_tools emails.py 10lines.py tests
python -m mypy --ignore-missing-imports email_tools emails.py 10lines.py
```

## Kỳ vọng về mã nguồn

- Giữ logic xử lý trong package `email_tools`, launcher gốc chỉ dùng để tương
  thích với cách chạy cũ.
- Thêm regression test cho mọi thay đổi hành vi.
- Dùng `pathlib`, type hints và thông báo lỗi có thể hành động.
- Không thêm dependency nếu chưa cần thiết.

## Báo cáo vấn đề

Với lỗi thông thường, mở [Issue](https://github.com/MinhThang1009/student-email-tools/issues) kèm bước tái hiện tối thiểu và
dữ liệu đã được ẩn danh. Với vấn đề bảo mật, xem [SECURITY.md](SECURITY.md).

Mọi tương tác phải tuân theo [Code of Conduct](CODE_OF_CONDUCT.md).
