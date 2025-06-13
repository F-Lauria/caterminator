import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(log_file=None):
    """
    Configure and set up logging for the application.

    :param log_file: Path to the log file (absolute or relative)
    :type log_file: str
    :return: Configured logger
    :rtype: logging.Logger
    """
    # Default log file path if none provided
    if log_file is None:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        log_file = os.path.join(project_root, "logs/app.log")

    # Ensure the logs directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger("transaction_categorizer")

    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1048576,
        backupCount=5,  # 1MB file size, keep 5 backups
    )
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_format)

    console_handler = logging.StreamHandler()
    console_format = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
