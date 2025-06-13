# Caterminator

## Introduction

Caterminator is a financial transaction categorization tool that leverages the LM studio SDK. It automatically classifies bank transactions into predefined categories using generative AI technology through LM Studio, providing a structured approach to financial data organization.

## Project Structure

```
caterminator/
├── caterminator/             # Main package
│   ├── main.py               # Entry point for the application
│   ├── functions/            # Core functionality modules
│   └── utils/                # loggin set up
├── config/                   # Configuration files
│   ├── categories.json       # Predefined transaction categories
│   └── paths.json            # File path configurations to provide as input
├── data/                     # Data storage
│   ├── bank_statements/      # Raw bank statement files (PDF, CSV, etc.)
│   ├── categorized_transactions/ # Processed and categorized transactions
│   └── clean_transactions/   # Cleaned transaction data
├── logs/                     # Application logs
│   └── app.log               # Main log file
├── tests/                    # Test suite
│   ├── fixtures/             # Test fixtures
│   ├── test_categorizer.py   # Tests for categorization functionality
│   └── test_parser.py        # Tests for parsing functionality
├── pyproject.toml            # Project metadata and dependencies
└── poetry.lock               # Locked dependencies
└── README.md
```

## Installation

To set up the project, clone the repository and install the required dependencies:

```bash
poetry install
```

## Usage

1. Ensure your configuration files are set up in the config directory
    - Categories and keywork defined by you
    - paths
2. **Prepare your bank statements:**  
   The PDF files you provide as input must have the following header row:  
   `["Date", "Description", "Debit", "Credit"]`
3. Place your bank statements in the bank_statements directory
4. Run the application using:

```bash
python caterminator/main.py
```
Make sure LM studio server is running and a model is loaded

The application will:
1. Parse your bank statements
2. Clean the transaction data
3. Categorize transactions using model loaded in LM studio
4. Save categorized transactions to the categorized_transactions directory

For detailed logs, check the app.log file.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.