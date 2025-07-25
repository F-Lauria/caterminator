import csv
import lmstudio as lms
import json
import logging
import os

logger = logging.getLogger("transaction_categorizer")

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
categories_path = os.path.join(project_root, "config/categories.json")

with open(categories_path) as f:
    categories = json.load(f)


def build_prompt(description, amount, tx_type, categories, confidence_threshold):
    """
    Builds a prompt for the language model to categorize a transaction.

    :param description: The transaction description.
    :type description: str
    :param amount: The transaction amount.
    :type amount: str
    :param tx_type: The transaction type (debit or credit).
    :type tx_type: str
    :param categories: A dictionary of categories with their types and keywords.
    :type categories: dict
    :param confidence_threshold: The confidence threshold for categorization.
    :type confidence_threshold: int
    :return: The constructed prompt for the language model.
    :rtype: str
    """
    prompt = (
        "You are a bank transaction categorizer. "
        "Given the transaction description, amount, and type (debit or credit), assign one of these categories: "
        f"{', '.join(categories.keys())}, to categorize.\n"
        "Use BOTH the transaction type and the following keywords as hints for each category:\n"
    )
    for cat, info in categories.items():
        prompt += f"- {cat} (type: {info['type']}): {', '.join(info['keywords']) if info['keywords'] else 'no specific keywords'}\n"
    prompt += (
        "\nWhen assigning a category, always consider if the transaction type (debit or credit) matches the typical type for the category. "
        "For example, do not assign a debit category to a credit transaction and vice versa.\n"
        f"If you are at least {confidence_threshold}% sure of the category, output only the category name. "
        "If you are less confident, output: to categorize.\n"
        "If the description does not contain any of the keywords, but you are still at least "
        f"{confidence_threshold}% sure of the category, you can still assign the category.\n"
        "If you find similar words (not just exact matches) in the description, use your knowledge to assign the best category.\n"
        "ALWAYS answer in English. Output ONLY the category name (one of: "
        f"{', '.join(categories.keys())}, to categorize). Do NOT explain your reasoning. Do NOT add any extra text.\n"
        f"Description: {description}\n"
        f"Amount: {amount}\n"
        f"Type: {tx_type}\n"
        "Category:"
    )
    return prompt


def extract_category(model_output, categories):
    """
    Extracts the category from the language model's output.

    :param model_output: The raw output from the language model.
    :type model_output: str
    :param categories: A dictionary of categories.
    :type categories: dict
    :return: The extracted category or "to categorize" if no match is found.
    :rtype: str
    """
    if "</think>" in model_output:
        after_think = model_output.split("</think>")[-1]
    else:
        after_think = model_output

    cleaned = after_think.strip().replace('"', "").replace("'", "").strip(",. ").lower()
    for cat in list(categories.keys()) + ["to categorize"]:
        if cleaned == cat.lower():
            return cat
    return "to categorize"


def categorize_transaction(description, amount, tx_type, confidence_threshold):
    """
    Categorizes a transaction using a language model.

    :param description: The transaction description.
    :type description: str
    :param amount: The transaction amount.
    :type amount: str
    :param tx_type: The transaction type (debit or credit).
    :type tx_type: str
    :param confidence_threshold: The confidence threshold for categorization.
    :type confidence_threshold: int
    :return: The category assigned to the transaction.
    :rtype: str
    """
    model = lms.llm()
    prompt = build_prompt(
        description, amount, tx_type, categories, confidence_threshold
    )
    result = model.respond(prompt)
    logger.debug(f"Model output for transaction: {result.content}")
    return extract_category(result.content, categories)


def run_categorizer(csv_path, output_csv_path, confidence_threshold=99):
    """
    Runs the categorizer on a CSV file of transactions and writes the results to a new CSV file.

    :param csv_path: The path to the input CSV file.
    :type csv_path: str
    :param output_csv_path: The path to the output CSV file.
    :type output_csv_path: str
    :param confidence_threshold: The confidence threshold for categorization (default is 99).
    :type confidence_threshold: int
    :return: None
    :rtype: None
    """
    logger.info(f"Starting categorization from {csv_path} to {output_csv_path}")

    row_count = 0
    categorized_count = 0

    with (
        open(csv_path, newline="", encoding="utf-8") as csvfile,
        open(output_csv_path, "w", newline="", encoding="utf-8") as outfile,
    ):
        reader = csv.DictReader(csvfile)
        fieldnames = reader.fieldnames + ["Category", "Type"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()

        for row in reader:
            row_count += 1
            description = row["Description"]
            debit = row["Debit"].strip() if row["Debit"] else ""
            credit = row["Credit"].strip() if row["Credit"] else ""
            if debit and float(debit) != 0:
                amount = debit
                tx_type = "debit"
            elif credit and float(credit) != 0:
                amount = credit
                tx_type = "credit"
            else:
                amount = "0"
                tx_type = "unknown"
            category = categorize_transaction(
                description, amount, tx_type, confidence_threshold
            )
            if category != "to categorize":
                categorized_count += 1
            row["Category"] = category
            row["Type"] = tx_type
            row["Debit"] = row["Debit"] if row["Debit"] else "0"
            row["Credit"] = row["Credit"] if row["Credit"] else "0"
            row["Description"] = (
                row["Description"].replace("\n", " ").replace("\r", " ")
            )
            writer.writerow(row)

    logger.info(
        f"Categorization complete. Processed {row_count} transactions, categorized {categorized_count}."
    )
