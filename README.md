# Caterminator

## Introduction

Caterminator is a financial transaction categorization tool that leverages the LM Studio SDK. It automatically classifies bank transactions into predefined categories using generative AI technology through LM Studio, providing a structured approach to financial data organization.

The tool currently supports **ABN AMRO** and **ING** bank statement formats, each using specialized parsing approaches optimized for their respective PDF structures.

## Project Structure

```
caterminator/
├── caterminator/             # Main package
│   ├── main.py               # Entry point for the application
│   ├── functions/            # Core functionality modules
│   │   ├── parser.py         # Bank statement parsing (ABN & ING)
│   │   └── categorizer.py    # AI-powered transaction categorization
│   └── utils/                # Utility modules
│       └── logging_config.py # Logging configuration
├── config/                   # Configuration files
│   ├── categories.json       # Predefined transaction categories
│   └── paths.json            # File path configurations
├── data/                     # Data storage directory
│   ├── bank_statements/      # Raw bank statement PDFs
│   ├── categorized_transactions/ # Final categorized transactions
│   └── clean_transactions/   # Intermediate cleaned transaction data
├── tests/                    # Test suite
│   ├── fixtures/             # Test data and sample files
│   ├── conftest.py           # Test configuration
│   ├── test_categorizer.py   # Categorization tests
│   └── test_parser.py        # Parsing tests (ABN & ING)
├── pyproject.toml            # Project metadata and dependencies
├── poetry.lock               # Locked dependencies
└── README.md                 # This file
```

## Features

### Dual Bank Support
- **ABN AMRO**: Table-based extraction from structured PDF statements
- **ING**: Text-based parsing for PDFs with unstructured layouts
- **Automatic Bank Detection**: The system automatically identifies the bank format and applies the appropriate parsing method

### Key Capabilities
- **Duplicate Prevention**: Hash-based system prevents duplicate transactions when processing multiple files
- **AI-Powered Categorization**: Uses LM Studio with configurable confidence thresholds
- **Transaction Cleaning**: Removes bank codes, IBANs, BICs, and other unnecessary details
- **Flexible Configuration**: Customizable categories and file paths via JSON configuration

## Bank Processing Methods

### ABN AMRO Processing
The ABN AMRO parser handles **structured PDF tables** with the following approach:
- **Header Detection**: Automatically identifies table headers (`Date`, `Description`, etc.)
- **Transaction Validation**: Uses date pattern matching (`DD-MM-YYYY`) to identify valid transactions
- **Row Filtering**: Skips summary rows, totals, and empty entries
- **Amount Processing**: Handles both debit and credit columns with European number formatting

### ING Processing  
The ING parser uses **text-based extraction** for PDFs without proper table structure:
- **Text Pattern Recognition**: Identifies transactions starting with date patterns (`DD/MM/YYYY`)
- **Multi-line Description Handling**: Combines transaction descriptions that span multiple lines
- **Amount Detection**: Extracts positive/negative amounts and determines debit/credit classification
- **Content Filtering**: Removes bank-specific headers, footers, and irrelevant text patterns

Both processes output standardized CSV files with columns: `Date`, `Description`, `Debit`, `Credit`, `Bank`, `Hash`

## Prerequisites

Before using Caterminator, ensure you have:
1. **Python 3.10 or higher**
2. **Poetry** for dependency management
3. **LM Studio** installed and running with a loaded model
4. **Bank statement PDFs** in supported formats (ABN AMRO or ING)

## Installation

To set up the project, clone the repository and install the required dependencies:

```bash
poetry install
```

## Usage

### Configuration Setup
1. **Configure Categories**: Edit `config/categories.json` to define your transaction categories and keywords
2. **Set File Paths**: Update `config/paths.json` with the paths to your bank statement files:
   ```json
   {
       "bank_statement": [
           "data/bank_statements/statement1.pdf",
           "data/bank_statements/statement2.pdf"
       ],
       "clean_transactions": "data/clean_transactions/transactions.csv",
       "categorized_transactions": "data/categorized_transactions/final.csv"
   }
   ```

### Bank Statement Requirements

#### ABN AMRO Statements
- **Format**: PDF with structured tables
- **Required Headers**: Must contain `Date` and `Description` columns
- **Date Format**: Transactions must use `DD-MM-YYYY` format
- **Layout**: Standard ABN AMRO PDF export format with debit/credit columns

#### ING Statements  
- **Format**: PDF (table structure optional)
- **Header Indicator**: Must contain the text `"date name / description / notification type amount"`
- **Date Format**: Transactions must start with `DD/MM/YYYY` format  
- **Layout**: Standard ING "Zakelijke rekening" (business account) statement format

### Running the Application

1. **Start LM Studio**: Ensure LM Studio server is running with a model loaded
2. **Place Bank Statements**: Put your PDF files in the `data/bank_statements/` directory
3. **Run Processing Pipeline**:
   ```bash
   python caterminator/main.py
   ```

### Processing Workflow

The application follows this automated pipeline:

1. **Parsing Phase**:
   - Reads PDF files from configured paths
   - Auto-detects bank format (ABN AMRO vs ING)
   - Applies appropriate parsing method:
     - **ABN AMRO**: Table extraction → Row validation → Data cleaning
     - **ING**: Text parsing → Pattern matching → Multi-line consolidation
   - Generates unique hash for each transaction to prevent duplicates
   - Outputs cleaned transactions to CSV

2. **Categorization Phase**:
   - Reads cleaned transactions
   - Sends each transaction to LM Studio for AI categorization
   - Applies confidence threshold (default: 99%)
   - Assigns categories based on description, amount, and transaction type
   - Saves final categorized results

### Output Files

- **Clean Transactions**: `data/clean_transactions/` - Parsed and cleaned transaction data
- **Categorized Transactions**: `data/categorized_transactions/` - Final results with AI-assigned categories
- **Logs**: Application logs are created in the `logs/` directory (created automatically)

### Notes

- **Duplicate Handling**: The system automatically prevents duplicate transactions when processing multiple files or running multiple times
- **Confidence Threshold**: Transactions below the confidence threshold are marked as "to categorize" for manual review
- **Transaction Types**: The system distinguishes between debit and credit transactions for accurate categorization
- **Error Handling**: Failed categorizations are logged but don't stop the overall process

For detailed logs and troubleshooting information, check the generated log files.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.