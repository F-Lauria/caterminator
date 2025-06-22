import pdfplumber
import csv
import re
import logging
import os

logging.getLogger("pdfminer").setLevel(logging.ERROR)
logger = logging.getLogger("transaction_categorizer")


def clean_amount(amount_str):
    """
    Cleans and formats a string representing a monetary amount.

    :param amount_str: The string representing the amount.
    :type amount_str: str
    :return: The cleaned and formatted amount string.
    :rtype: str
    """
    # Remove spaces
    amount_str = amount_str.replace(" ", "")
    # If both '.' and ',' are present, assume European format (e.g., '2.000,00')
    if "." in amount_str and "," in amount_str:
        amount_str = amount_str.replace(".", "")
        amount_str = amount_str.replace(",", ".")
    # If only ',' is present, assume European decimal (e.g., '1234,56')
    elif "," in amount_str:
        amount_str = amount_str.replace(",", ".")
    # If only '.' is present, assume US/UK decimal (do nothing)
    # If neither, do nothing
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
    Fallback ING parser: parses lines of text if no tables are found.
    Returns a list of [date, description, debit, credit, bank] rows.
    """
    transactions = []
    lines = text.splitlines()
    header_found = False
    current = None

    ignore_patterns = [
        "this product is covered by the deposit guarantee scheme",
        "more information? go to ing.nl/dgs",
        "page",  # e.g., page1 of2
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
        "value date",  # ignore value date lines
        "iban:",  # ignore IBAN lines
        "date/time:",  # ignore Date/time: lines
    ]

    def should_ignore_line(line):
        l = line.lower()
        return any(pat in l for pat in ignore_patterns)

    for line in lines:
        line = line.strip()
        # Detect header
        if (
            not header_found
            and "date name / description / notification type amount"
            in line.lower().replace("(", "").replace(")", "")
        ):
            header_found = True
            continue
        if not header_found:
            continue
        # Detect transaction start (date at beginning)
        m = re.match(r"(\d{1,2}/\d{2}/\d{4})\s+(.+)", line)
        if m:
            # Save previous transaction if any
            if current:
                current[1] = clean_description(current[1].strip())
                transactions.append(current)
            date = m.group(1)
            rest = m.group(2)
            # Extract amount from end of line (e.g., "+ 15.00" or "- 131.20")
            amt_match = re.search(r"([+-]\s*\d+[.,]?\d*)\s*$", rest)
            if amt_match:
                amount = amt_match.group(1).replace(" ", "")
                amount = clean_amount(amount)
                rest = rest[: amt_match.start()].strip()
            else:
                amount = "0"
            if amount.startswith("-"):
                debit = amount.lstrip("-")
                credit = "0"
            else:
                debit = "0"
                credit = amount.lstrip("+")
            current = [date, rest, debit, credit, "ING"]
            continue
        # If we are in a transaction, collect all lines as description until next date
        if current:
            if should_ignore_line(line):
                continue
            if current[1]:
                current[1] += " " + line
            else:
                current[1] = line
    # Save last transaction
    if current:
        current[1] = clean_description(current[1].strip())
        transactions.append(current)
    return transactions


def extract_transactions_to_csv(pdf_path, csv_path):
    """
    Extracts transactions from a PDF file and writes them to a CSV file.

    :param pdf_path: The path to the input PDF file.
    :type pdf_path: str
    :param csv_path: The path to the output CSV file.
    :type csv_path: str
    :return: None
    :rtype: None
    """
    transactions = []
    header_found = False
    bank_type = None

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if not tables or all(len(table) == 0 for table in tables):
                text = page.extract_text()
                print(text)
                if text:
                    ing_rows = parse_ing_text_lines(text)
                    if ing_rows:
                        if not transactions:
                            transactions.append(
                                ["Date", "Description", "Debit", "Credit", "Bank"]
                            )
                        transactions.extend(ing_rows)
                continue
            for table in tables:
                print(f"Processing table with {len(table)} rows")
                for row in table:
                    row = [cell.strip() if cell else "" for cell in row]

                    # Detect header and bank type
                    if not header_found:
                        if abn_is_header_row(row, header_found):
                            transactions.append(
                                ["Date", "Description", "Debit", "Credit", "Bank"]
                            )
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
                                transactions.append(
                                    [date, description, debit, credit, "ABN"]
                                )

    # Write or append to CSV
    file_exists = os.path.isfile(csv_path)
    write_header = not file_exists or os.stat(csv_path).st_size == 0

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for i, row in enumerate(transactions):
            if i == 0 and not write_header:
                continue  # Skip header if already present
            writer.writerow(row)

    logger.info(f"Extracted {len(transactions) - 1} transactions to {csv_path}")
