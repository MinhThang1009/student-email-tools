# Hướng dẫn cho agent

Tệp này là điểm vào hướng dẫn dùng chung cho các coding agent hỗ trợ
`AGENTS.md`.

## Quy ước làm việc

- Tuân theo yêu cầu của người dùng và các hướng dẫn đang áp dụng trong
  repository.
- Đọc các tệp liên quan trước khi thay đổi và giữ nguyên quy ước riêng của dự
  án.
- Giữ thay đổi tập trung, chạy các kiểm tra phù hợp của dự án và báo cáo rõ các
  kiểm tra không thể chạy.
- Không commit, push, tạo pull request hoặc thay đổi cấu hình remote nếu người
  dùng chưa yêu cầu rõ ràng.

## Lệnh kiểm tra

- `python -m pytest -q`
- `python -m ruff check email_tools emails.py 10lines.py tests`
- `python -m ruff format --check email_tools emails.py 10lines.py tests`
- `python -m mypy --ignore-missing-imports email_tools emails.py 10lines.py`

## Pull request

Trước khi tạo hoặc cập nhật pull request, chạy
`python scripts/pr_template_preflight.py --title "<title>"`.

## Ngôn ngữ

Dùng tiếng Việt cho tài liệu hướng tới người dùng và contributor. Giữ nguyên
các tên lệnh, tên package, protocol literal và Conventional Commit prefix bằng
tiếng Anh.
