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


@pytest.fixture
def mock_pdf_content_ing():
    class MockPage:
        def extract_tables(self):
            # Return a list of tables, each table is a list of rows
            return [
                [
                    [
                        "Datum",
                        "Naam / Omschrijving",
                        "Rekening",
                        "Tegenrekening",
                        "Code",
                        "Af Bij",
                        "Bedrag (EUR)",
                        "MutatieSoort",
                        "Mededelingen",
                    ],
                    [
                        "01-02-2023",
                        "Albert Heijn",
                        "NL12INGB0001234567",
                        "NL34RABO0123456789",
                        "GM",
                        "Af",
                        "12,34",
                        "PIN",
                        "",
                    ],
                    [
                        "02-02-2023",
                        "Salaris",
                        "NL12INGB0001234567",
                        "NL56SNSB0123456789",
                        "GM",
                        "Bij",
                        "1500,00",
                        "STORT",
                        "",
                    ],
                ]
            ]

        def extract_table(self):
            # For compatibility, return the first table
            return self.extract_tables()[0]

    class MockPDF:
        pages = [MockPage()]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    return MockPDF()


@pytest.fixture
def mock_pdf_content_ing_text():
    class MockPage:
        def extract_tables(self):
            return []  # No tables found

        def extract_text(self):
            return (
                "Statement Zakelijke Rekening\n"
                "Date Name / Description / Notification Type Amount\n"
                "01/02/2023 Albert Heijn groceries - 12,34\n"
                "02/02/2023 Salaris betaling + 1500,00\n"
                "03/02/2023 Coffee Shop - 3,50\n"
            )

    class MockPDF:
        pages = [MockPage()]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    return MockPDF()
