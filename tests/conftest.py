import pytest
import tempfile
from unittest.mock import Mock


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield td


@pytest.fixture
def mock_pdf_content():
    mock_tables = [
        [
            ["", "Date", "Description", "", "Debit", "Credit"],
            ["", "01-01-2023", "SUPERMARKET GROCERY", "", "45.67", ""],
            ["", "05-01-2023", "SALARY PAYMENT", "", "", "2000.00"],
            ["", "10-01-2023", "INTERNET PROVIDER", "", "29.99", ""],
        ]
    ]

    mock_page = Mock()
    mock_page.extract_tables.return_value = mock_tables

    mock_pdf = Mock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = Mock(return_value=mock_pdf)
    mock_pdf.__exit__ = Mock(return_value=None)

    return mock_pdf
