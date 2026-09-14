import pandas as pd

from email_tools.email_generator import (
    email_sort_key,
    extract_component,
    extract_last_component_from_row,
    generate_emails,
    normalize_local_part,
)


def test_extract_component_supports_values_with_or_without_hyphens() -> None:
    assert extract_component("  Nguyễn Văn - 71K01  ") == "Nguyễn Văn"
    assert extract_component("Nguyễn Văn") == "Nguyễn Văn"
    assert extract_component("- 71K01", leading_hyphen_uses_last_word=True) is None
    assert (
        extract_component("- Nguyễn Văn A", leading_hyphen_uses_last_word=True) == "A"
    )
    assert extract_component(None) is None


def test_leading_class_separator_uses_given_name_from_first_name() -> None:
    assert (
        extract_last_component_from_row(
            "24772020101CT - Nguyễn Lê An Như", "- 71K31DUOC01"
        )
        == "Như"
    )
    assert (
        extract_last_component_from_row("2500115423 - Hồ Nguyễn Trung Khoa", "-")
        == "Khoa"
    )


def test_normalize_local_part_handles_vietnamese_characters() -> None:
    assert normalize_local_part("Đặng Ánh") == "danganh"
    assert normalize_local_part(".,-") is None


def test_email_sort_key_requires_a_number_after_a_dot() -> None:
    numbered = "an.207tt50948@vanlanguni.vn"
    no_dot = "24042108031986@vanlanguni.vn"

    assert email_sort_key(numbered) < email_sort_key(no_dot)
    assert email_sort_key("an.207@other.example") == (0, 207, "an.207@other.example")


def test_generate_emails_handles_mixed_source_formats() -> None:
    dataframe = pd.DataFrame(
        {
            "First name": [
                "2500115424 - Nguyễn Văn A",
                "24042108031986 - Lê Thị Hậu",
                "24772020101CT - Nguyễn Lê An Như",
                "2500115425 - Nguyễn Văn C",
                "2500115426",
                "2673201040001 - Soles",
            ],
            "Last name": [
                "An - 71K01",
                "An - 71K01",
                "- 71K31DUOC01",
                "Ý - 71K01",
                "Bình",
                "Adam",
            ],
        }
    )

    assert generate_emails(dataframe) == [
        "an.2500115424@vanlanguni.vn",
        "y.2500115425@vanlanguni.vn",
        "binh.2500115426@vanlanguni.vn",
        "nhu.24772020101ct@vanlanguni.vn",
        "24042108031986@vanlanguni.vn",
        "2673201040001@vanlanguni.vn",
    ]
