import os
import csv
from unittest.mock import patch
from caterminator.functions.parser import (
    clean_amount,
    clean_description,
    extract_transactions_to_csv,
)


def test_clean_amount():
    assert clean_amount("1 234,56") == "1234.56"
    assert clean_amount("45.67") == "45.67"
    assert clean_amount("2.000,00") == "2000.00"


def test_clean_description():
    desc = (
        "PAS123 NR:456789 /TRTP/ Payment for NL12ABCD1234567890 services from AABBCCDD"
    )
    cleaned = clean_description(desc)
    assert "NL12ABCD1234567890" not in cleaned
    assert "/TRTP/" not in cleaned
    assert "PAS123 NR:456789" not in cleaned
    assert "AABBCCDD" not in cleaned
    assert "Payment for services from" in cleaned


@patch("pdfplumber.open")
def test_extract_transactions_to_csv(mock_pdf_open, mock_pdf_content, temp_dir):
    mock_pdf_open.return_value = mock_pdf_content

    pdf_path = "dummy.pdf"
    csv_path = os.path.join(temp_dir, "output.csv")

    extract_transactions_to_csv(pdf_path, csv_path)

    assert os.path.exists(csv_path)

    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert len(rows) == 4  # Header + 3 transactions
    assert rows[0] == ["Date", "Description", "Debit", "Credit"]
    assert rows[1][0] == "01-01-2023"
    assert rows[1][2] == "45.67"  # Debit amount
    assert rows[2][3] == "2000.00"  # Credit amount
