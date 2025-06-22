import json
import os
import sys
from functions.parser import extract_transactions_to_csv
from functions.categorizer import run_categorizer
from utils.logging_config import setup_logger

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

log_path = os.path.join(PROJECT_ROOT, "logs/app.log")
logger = setup_logger(log_path)

if __name__ == "__main__":
    config_path = os.path.join(PROJECT_ROOT, "config/paths.json")
    with open(config_path) as f:
        paths = json.load(f)

    categories_path = os.path.join(PROJECT_ROOT, "config/categories.json")

    bank_statement = paths["bank_statement"]
    clean_transactions = paths["clean_transactions"]
    categorized_transactions = paths["categorized_transactions"]

    os.makedirs(os.path.dirname(clean_transactions), exist_ok=True)
    os.makedirs(os.path.dirname(categorized_transactions), exist_ok=True)

    logger.info("Starting transaction processing pipeline")
    logger.info(f"Using bank statement: {bank_statement}")

    logger.info("Running parser to extract transactions...")
    extract_transactions_to_csv(bank_statement, clean_transactions)

    # logger.info("Running categorizer to assign categories...")
    # run_categorizer(
    #     clean_transactions, categorized_transactions, confidence_threshold=99
    # )

    # logger.info(
    #     f"Processing pipeline complete. Final results saved to {categorized_transactions}"
    # )
