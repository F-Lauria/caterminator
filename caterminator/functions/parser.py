import pdfplumber
import csv
import re
import logging
import os
import hashlib

logging.getLogger("pdfminer").setLevel(logging.ERROR)
logger = logging.getLogger("transaction_categorizer")


def clean_amount(amount_str):
    """
    Cleans and formats a string representing a monetary amount.

    Handles different numeric formats:
    - Removes all spaces
    - For European format with both '.' and ',' (e.g., '2.000,00'), removes thousands
      separators and converts decimal comma to decimal point
    - For European decimal with only ',' (e.g., '1234,56'), converts comma to decimal point
    - For US/UK format with decimal point, leaves as is
    - If no separators present, leaves as is

    :param amount_str: The string representing the amount.
    :type amount_str: str
    :return: The cleaned and formatted amount string.
    :rtype: str
    """
    amount_str = amount_str.replace(" ", "")
    if "." in amount_str and "," in amount_str:
        amount_str = amount_str.replace(".", "")
        amount_str = amount_str.replace(",", ".")
    elif "," in amount_str:
        amount_str = amount_str.replace(",", ".")
    return amount_str


def clean_description(description):
    """
    Cleans and formats a transaction description by removing unnecessary details.

    :param description: The raw transaction description.
    :type description: str
    :return: The cleaned transaction description.
    :rtype: str
    """
    # Remove IBANs
    description = re.sub(r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{10,30}\b", "", description)
    # Remove BICs
    description = re.sub(r"\b[A-Z]{6}[A-Z0-9]{2,5}\b", "", description)
    # Remove codes like PAS112 NR:xxxxxx
    description = re.sub(r"PAS\d+\s*NR:\S+", "", description, flags=re.IGNORECASE)
    # Remove /TRTP/, /CSID/, /MARF/, /REMI/, /EREF/, /NAME/, /BIC/, /IBAN/, /AMT/, etc.
    description = re.sub(r"/[A-Z]{3,6}/", "", description)
    # Remove long digit sequences (references)
    description = re.sub(r"\b\d{6,}\b", "", description)
    # Remove payment method prefixes (robust for spaces and case)
    description = re.sub(
        r"\bBEA,?\s*Apple Pay\b[ ,:]*", "", description, flags=re.IGNORECASE
    )
    description = re.sub(
        r"\biDEAL/\s*BI\s*C/?\b[ ,:]*", "", description, flags=re.IGNORECASE
    )
    description = re.sub(
        r"\biDEAL/\s*BIC/?\b[ ,:]*", "", description, flags=re.IGNORECASE
    )
    # Remove date/time patterns like 21.05.25/13:11 or 22.05.25/19:28
    description = re.sub(r"\d{2}\.\d{2}\.\d{2}/\d{2}:\d{2}", "", description)
    # Remove patterns like a404-- -05-2025 22:17 or a404---05-2025 07:34 anywhere in the string
    description = re.sub(
        r"a\d{3,4}-*\s*-*\d{2}-\d{2}-\d{4}\s*\d{2}:\d{2}",
        "",
        description,
        flags=re.IGNORECASE,
    )
    # Remove extra spaces and commas
    description = re.sub(r"\s+", " ", description)
    description = re.sub(r",,", ",", description)

    description = description.strip(" ,")
    return description


def abn_is_header_row(row, header_found):
    """
    Determines if the given row is the header row for ABN AMRO transaction tables.

    :param row: The row from the table.
    :type row: list
    :param header_found: Whether the header has already been found.
    :type header_found: bool
    :return: True if the row is the header row, False otherwise.
    :rtype: bool
    """
    return (
        not header_found
        and len(row) > 5
        and row[1] == "Date"
        and row[2] == "Description"
    )


def abn_should_skip_row(row):
    """
    Determines if the given row should be skipped (e.g., empty or summary rows).

    :param row: The row from the table.
    :type row: list
    :return: True if the row should be skipped, False otherwise.
    :rtype: bool
    """
    return row[1] in (
        "",
        "Date",
        "Number of debit",
        "Total amount debited",
    )


def abn_is_transaction_row(row):
    """
    Determines if the given row represents a transaction row based on the date format.

    :param row: The row from the table.
    :type row: list
    :return: True if the row is a transaction row, False otherwise.
    :rtype: bool
    """
    return re.match(r"\d{2}-\d{2}-\d{4}", row[1])


def parse_ing_text_lines(text):
    """
    Fallback ING parser for PDF statements when no tables are found.

    This function parses plain text from ING bank statements by:
    1. Splitting the text into lines and identifying statement headers
    2. Finding transaction entries that start with dates in DD/MM/YYYY format
    3. Processing each transaction to extract date, description, and amount information
    4. Identifying whether amounts are debits (negative values) or credits (positive values)
    5. Cleaning transaction descriptions and merging multi-line descriptions
    6. Filtering out common statement header/footer text and irrelevant information

    Transactions are built incrementally, with multi-line descriptions being combined
    until the next transaction is found.

    :param text: Raw text extracted from an ING bank statement PDF
    :type text: str
    :return: List of transaction records, each containing [date, description, debit, credit, bank]
    :rtype: list
    """
    transactions = []
    lines = text.splitlines()
    header_found = False
    current_transaction = None

    ignore_patterns = [
        "this product is covered by the deposit guarantee scheme",
        "more information? go to ing.nl/dgs",
        "page",
        "sbettr01",
        "statement zakelijke rekening",
        "accountnumber period",
        "opening balance",
        "closing balance",
        "total in",
        "total out",
        "at ing.nl you will find the answers",
        "rather have personal contact?",
        "period",
        "address account name",
        "value date",
        "iban:",
        "date/time:",
    ]

    def should_ignore_line(line):
        lowered_line = line.lower()
        return any(pattern in lowered_line for pattern in ignore_patterns)

    for line in lines:
        line = line.strip()

        header_indicator = "date name / description / notification type amount"
        normalized_line = line.lower().replace("(", "").replace(")", "")

        if not header_found and header_indicator in normalized_line:
            header_found = True
            continue

        if not header_found:
            continue

        date_match = re.match(r"(\d{1,2}/\d{2}/\d{4})\s+(.+)", line)
        if date_match:
            if current_transaction:
                current_transaction[1] = clean_description(
                    current_transaction[1].strip()
                )
                transactions.append(current_transaction)

            date = date_match.group(1)
            remaining_text = date_match.group(2)

            amount_match = re.search(r"([+-]\s*\d+[.,]?\d*)\s*$", remaining_text)
            if amount_match:
                amount_str = amount_match.group(1).replace(" ", "")
                amount_str = clean_amount(amount_str)
                description = remaining_text[: amount_match.start()].strip()
            else:
                amount_str = "0"
                description = remaining_text

            if amount_str.startswith("-"):
                debit_amount = amount_str.lstrip("-")
                credit_amount = "0"
            else:
                debit_amount = "0"
                credit_amount = amount_str.lstrip("+")

            current_transaction = [
                date,
                description,
                debit_amount,
                credit_amount,
                "ING",
            ]
            continue

        if current_transaction:
            if should_ignore_line(line):
                continue

            if current_transaction[1]:
                current_transaction[1] += " " + line
            else:
                current_transaction[1] = line

    if current_transaction:
        current_transaction[1] = clean_description(current_transaction[1].strip())
        transactions.append(current_transaction)

    return transactions


def compute_row_hash(row):
    """
    Computes a SHA256 hash for a transaction row (excluding the hash column itself).
    """
    row_str = "|".join(str(x) for x in row)
    return hashlib.sha256(row_str.encode("utf-8")).hexdigest()


def extract_transactions_to_csv(pdf_paths, csv_path):
    """
    Extracts transactions from multiple PDF files and writes them to a single CSV file.

    This function:
    1. Processes multiple bank statement PDFs (currently supports ABN AMRO and ING formats)
    2. Extracts transaction data from tables or falls back to text-based parsing
    3. Computes unique hash values for each transaction to prevent duplicates
    4. Checks for existing transactions in the destination CSV file
    5. Appends only new transactions to avoid duplicates
    6. Creates a new CSV file with headers if the destination doesn't exist

    For structured PDFs with tables, the function extracts data directly from tables.
    For PDFs without proper table structure (like some ING statements), it falls back
    to text-based parsing via the parse_ing_text_lines function.

    Each transaction is stored with date, description, debit amount, credit amount,
    bank identifier, and a unique hash value computed from these fields.

    :param pdf_paths: List of paths to PDF files to process
    :type pdf_paths: list
    :param csv_path: Path to the output CSV file
    :type csv_path: str
    :return: None
    """
    transactions = []
    header = ["Date", "Description", "Debit", "Credit", "Bank", "Hash"]

    for pdf_path in pdf_paths:
        header_found = False
        bank_type = None
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if not tables or all(len(table) == 0 for table in tables):
                    text = page.extract_text()
                    if text:
                        ing_rows = parse_ing_text_lines(text)
                        if ing_rows:
                            for row in ing_rows:
                                row_hash = compute_row_hash(row)
                                transactions.append(row + [row_hash])
                    continue

                for table in tables:
                    for row in table:
                        row = [cell.strip() if cell else "" for cell in row]
                        if not header_found:
                            if abn_is_header_row(row, header_found):
                                header_found = True
                                bank_type = "ABN"
                                continue

                        if header_found:
                            if bank_type == "ABN":
                                if abn_should_skip_row(row):
                                    continue

                                if abn_is_transaction_row(row):
                                    date = row[1]
                                    description = clean_description(row[2])
                                    debit = clean_amount(row[4]) if row[4] else "0"
                                    credit = clean_amount(row[5]) if row[5] else "0"
                                    tx_row = [date, description, debit, credit, "ABN"]
                                    row_hash = compute_row_hash(tx_row)
                                    transactions.append(tx_row + [row_hash])

    existing_hashes = set()
    file_exists = os.path.isfile(csv_path)
    if file_exists:
        with open(csv_path, newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if "Hash" in row:
                    existing_hashes.add(row["Hash"])

    write_header = not file_exists
    with open(csv_path, "a", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        if write_header:
            writer.writerow(header)

        new_rows = 0
        for row in transactions:
            if row[-1] not in existing_hashes:
                writer.writerow(row)
                new_rows += 1

    logger.info(f"Appended {new_rows} new transactions to {csv_path}")
