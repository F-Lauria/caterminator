import os
import csv
from unittest.mock import patch
from caterminator.functions.parser import (
    clean_amount,
    clean_description,
    extract_transactions_to_csv,
    parse_ing_text_lines,
    compute_row_hash,
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

    extract_transactions_to_csv([pdf_path], csv_path)

    assert os.path.exists(csv_path)

    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert len(rows) == 4
    assert rows[0] == [
        "Date",
        "Description",
        "Debit",
        "Credit",
        "Bank",
        "Hash",
    ]
    assert rows[1][0] == "01-01-2023"
    assert rows[1][2] == "45.67"  # Debit amount
    assert rows[2][3] == "2000.00"  # Credit amount

    hashes = [row[5] for row in rows[1:]]
    assert all(len(h) == 64 for h in hashes)
    assert len(hashes) == len(set(hashes))


@patch("pdfplumber.open")
def test_extract_transactions_to_csv_ing(
    mock_pdf_open, temp_dir, mock_pdf_content_ing_text
):
    """
    Test ING input file parsing using text fallback.
    """
    mock_pdf_open.return_value = mock_pdf_content_ing_text

    pdf_path = "dummy_ing.pdf"
    csv_path = os.path.join(temp_dir, "output_ing.csv")

    extract_transactions_to_csv([pdf_path], csv_path)

    assert os.path.exists(csv_path)

    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert len(rows) == 4
    assert rows[0] == [
        "Date",
        "Description",
        "Debit",
        "Credit",
        "Bank",
        "Hash",
    ]
    assert rows[1][0] == "01/02/2023"
    assert rows[1][2] == "12.34"  # Debit amount
    assert rows[2][3] == "1500.00"  # Credit amount
    assert rows[3][2] == "3.50"

    hashes = [row[5] for row in rows[1:]]
    assert all(len(h) == 64 for h in hashes)
    assert len(hashes) == len(set(hashes))


@patch("pdfplumber.open")
def test_duplicate_prevention(mock_pdf_open, mock_pdf_content, temp_dir):
    """
    Test that the function prevents duplicate entries when
    processing the same PDF multiple times.
    """
    mock_pdf_open.return_value = mock_pdf_content
    pdf_path = "dummy.pdf"
    csv_path = os.path.join(temp_dir, "output_dedupe.csv")

    extract_transactions_to_csv([pdf_path], csv_path)

    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        rows_first_run = list(reader)

    extract_transactions_to_csv([pdf_path], csv_path)

    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        rows_second_run = list(reader)

    assert len(rows_first_run) == len(rows_second_run)

    for i in range(len(rows_first_run)):
        assert rows_first_run[i] == rows_second_run[i]


def test_compute_row_hash():
    """Test that the hash function produces consistent and unique results."""
    row1 = ["01-01-2023", "Test Transaction", "100.00", "0", "TEST"]
    row2 = ["01-01-2023", "Test Transaction", "100.00", "0", "TEST"]
    row3 = ["02-01-2023", "Test Transaction", "100.00", "0", "TEST"]

    assert compute_row_hash(row1) == compute_row_hash(row2)

    assert compute_row_hash(row1) != compute_row_hash(row3)


def test_parse_ing_text_lines():
    ing_text = """
    Statement Zakelijke Rekening
    Date Name / Description / Notification Type Amount
    01/02/2023 Albert Heijn groceries - 12,34
    02/02/2023 Salaris betaling + 1500,00
    03/02/2023 Coffee Shop - 3,50
    """
    rows = parse_ing_text_lines(ing_text)
    assert len(rows) == 3
    assert rows[0][0] == "01/02/2023"
    assert rows[0][1].startswith("Albert Heijn")
    assert rows[0][2] == "12.34"  # Debit
    assert rows[0][3] == "0"  # Credit
    assert rows[0][4] == "ING"
    assert rows[1][0] == "02/02/2023"
    assert rows[1][2] == "0"
    assert rows[1][3] == "1500.00"
    assert rows[2][0] == "03/02/2023"
    assert rows[2][2] == "3.50"
    assert rows[2][3] == "0"
