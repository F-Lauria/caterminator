# Caterminator

## Introduction

Caterminator is a comprehensive financial analysis tool that combines transaction categorization with data visualization. It leverages the LM Studio SDK to automatically classify bank transactions into predefined categories using generative AI technology, and then generates insightful visualizations to help users understand their financial patterns and spending habits.

The tool currently supports **ABN AMRO** and **ING** bank statement formats, each using specialized parsing approaches optimized for their respective PDF structures.

## Project Structure

```
caterminator/
├── caterminator/             # Main package
│   ├── main.py               # Entry point for the application
│   ├── functions/            # Core functionality modules
│   │   ├── parser.py         # Bank statement parsing (ABN & ING)
│   │   └── categorizer.py    # AI-powered transaction categorization
│   ├── visualization/        # Financial data visualization
│   │   └── finance_analysis.py # Plot generation and analysis
│   └── utils/                # Utility modules
│       └── logging_config.py # Logging configuration
├── config/                   # Configuration files
│   ├── categories.json       # Predefined transaction categories
│   └── paths.json            # File path configurations
├── data/                     # Data storage directory
│   ├── bank_statements/      # Raw bank statement PDFs
│   ├── categorized_transactions/ # Final categorized transactions
│   └── clean_transactions/   # Intermediate cleaned transaction data
├── docs/                     # Documentation and generated content
│   └── plots/                # Generated visualization plots
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

### Visualization Features
After categorizing transactions, Caterminator automatically generates comprehensive financial analysis plots including:

- **Monthly Expenses by Category**: Stacked bar charts showing spending patterns over time by category
- **Bank Comparison**: Compare spending habits across different banks (ABN AMRO vs ING)
- **Income vs Expenses**: Track monthly cash flow with income, expenses, and net flow trends
- **Savings Trends**: Monitor savings patterns with both individual transactions and cumulative totals
- **Essential vs Non-essential Spending**: Categorize expenses into essential (groceries, housing, utilities) and discretionary spending
- **Category and Bank Analysis**: Detailed breakdown of spending by category across different bank accounts

All plots are generated using matplotlib and seaborn, styled with a consistent color-blind friendly palette and saved as high-quality PNG images in the `docs/plots/` directory.

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
3. **LM Studio** installed and running with a loaded model (for categorization)
4. **Bank statement PDFs** in supported formats (ABN AMRO or ING)

**Note**: Visualization features work independently of LM Studio and can be used with any properly formatted categorized transaction data.

## Installation

To set up the project, clone the repository and install the required dependencies:

```bash
poetry install
```

## Usage

### Configuration Setup
1. **Configure Categories**: Edit `config/categories.json` to define your transaction categories and keywords

   The categories configuration file defines how transactions should be automatically categorized by the AI model. Each category contains:
   - **Keywords**: Words or phrases that help the model identify transactions belonging to this category
   - **Type**: Either `"debit"` (money going out) or `"credit"` (money coming in)

   Example configuration:
   ```json
   {
       "Groceries": {
           "keywords": ["supermarket", "grocery", "albert heijn", "jumbo", "lidl", "aldi"],
           "type": "debit"
       },
       "Salary": {
           "keywords": ["salary", "wage", "payroll", "employer name"],
           "type": "credit"
       },
       "Restaurants": {
           "keywords": ["restaurant", "cafe", "takeaway", "uber eats", "deliveroo"],
           "type": "debit"
       }
   }
   ```

   **Tips for effective categorization**:
   - Add specific merchant names, chain names, or transaction descriptions you commonly see
   - Include both Dutch and English terms if applicable
   - Use lowercase keywords for better matching
   - The AI model uses these keywords along with transaction descriptions to make categorization decisions

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

### Generating Visualizations

After processing and categorizing your transactions, you can generate financial analysis plots:

1. **Ensure Categorized Data Exists**: Make sure you have run the main processing pipeline first
2. **Run Visualization Module**:
   ```bash
   python caterminator/visualization/finance_analysis.py
   ```

The visualization module will:
- Load your categorized transaction data
- Generate multiple types of financial analysis plots
- Save all plots as PNG images in `docs/plots/`
- Display completion message with the output directory path

**Generated Plot Types**:
- `monthly_expenses_by_category.png` - Monthly spending breakdown by category
- `bank_category_comparison.png` - Spending comparison across banks
- `income_vs_expenses.png` - Monthly cash flow analysis
- `savings_trends.png` - Savings patterns over time
- `essential_vs_nonessential.png` - Essential vs discretionary spending
- `monthly_expenses_by_category_and_bank.png` - Detailed category and bank analysis

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

3. **Visualization Phase** (Optional):
   - Loads categorized transaction data
   - Generates comprehensive financial analysis plots
   - Creates multiple chart types for different insights
   - Saves all visualizations to `docs/plots/` directory

### Output Files

- **Clean Transactions**: `data/clean_transactions/` - Parsed and cleaned transaction data
- **Categorized Transactions**: `data/categorized_transactions/` - Final results with AI-assigned categories
- **Visualization Plots**: `docs/plots/` - Generated financial analysis charts and graphs
- **Logs**: Application logs are created in the `logs/` directory (created automatically)

### Notes

- **Duplicate Handling**: The system automatically prevents duplicate transactions when processing multiple files or running multiple times
- **Confidence Threshold**: Transactions below the confidence threshold are marked as "to categorize" for manual review
- **Transaction Types**: The system distinguishes between debit and credit transactions for accurate categorization
- **Error Handling**: Failed categorizations are logged but don't stop the overall process

For detailed logs and troubleshooting information, check the generated log files.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.