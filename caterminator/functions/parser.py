import pdfplumber
import csv
import re
import logging

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

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    row = [cell.strip() if cell else "" for cell in row]
                    if (
                        not header_found
                        and len(row) > 5
                        and row[1] == "Date"
                        and row[2] == "Description"
                    ):
                        transactions.append(["Date", "Description", "Debit", "Credit"])
                        header_found = True
                        continue
                    if header_found:
                        if row[1] in (
                            "",
                            "Date",
                            "Number of debit",
                            "Total amount debited",
                        ):
                            continue
                        if re.match(r"\d{2}-\d{2}-\d{4}", row[1]):
                            date = row[1]
                            description = clean_description(row[2])
                            debit = clean_amount(row[4]) if row[4] else "0"
                            credit = clean_amount(row[5]) if row[5] else "0"
                            transactions.append([date, description, debit, credit])

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in transactions:
            writer.writerow(row)

    logger.info(f"Extracted {len(transactions) - 1} transactions to {csv_path}")
