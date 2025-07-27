import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import sys

from caterminator.utils.logging_config import setup_visualization_logger

# Set up project path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# Set the style for all visualizations
plt.style.use("ggplot")
sns.set_palette("colorblind")

# Initialize visualization logger
logger = setup_visualization_logger()


def load_transaction_data(filepath):
    """Load transaction data from CSV file"""
    logger.info(f"Loading transaction data from {filepath}")
    df = pd.read_csv(filepath)
    # Convert date strings to datetime objects
    df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y")
    # Convert amounts to float and make debits negative
    df["Amount"] = np.where(
        df["Type"] == "debit", -df["Debit"].astype(float), df["Credit"].astype(float)
    )
    logger.info(f"Successfully loaded {len(df)} transactions")
    return df


def plot_monthly_expenses_by_category(df, output_dir):
    """Create a bar chart of monthly expenses by category"""
    logger.info("Generating monthly expenses by category plot")
    # Filter for debit transactions only
    expenses = df[df["Type"] == "debit"].copy()
    # Group by month and category, summing the amounts
    monthly_cat = (
        expenses.groupby([pd.Grouper(key="Date", freq="M"), "Category"])["Amount"]
        .sum()
        .abs()
        .reset_index()
    )

    # Pivot the data for plotting
    pivot_data = monthly_cat.pivot_table(
        index="Date", columns="Category", values="Amount", fill_value=0
    )

    # Plot the stacked bar chart
    plt.figure(figsize=(15, 8))
    ax = pivot_data.plot(kind="bar", stacked=True, figsize=(15, 8))
    plt.title("Monthly Expenses by Category", fontsize=16)
    plt.xlabel("Month", fontsize=14)
    plt.ylabel("Amount (€)", fontsize=14)
    plt.legend(title="Category", bbox_to_anchor=(1.05, 1), loc="upper left")
    # Format x-tick labels as "Mon YYYY"
    ax.set_xticklabels(
        [d.strftime("%b %Y") for d in pivot_data.index], rotation=45, ha="right"
    )
    plt.tight_layout()
    output_path = f"{output_dir}/monthly_expenses_by_category.png"
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved monthly expenses by category plot to {output_path}")


def plot_bank_comparison(df, output_dir):
    """Compare spending between different banks"""
    logger.info("Generating bank comparison plot")
    # Group by bank and category
    bank_category = (
        df[df["Type"] == "debit"]
        .groupby(["Bank", "Category"])["Amount"]
        .sum()
        .abs()
        .reset_index()
    )

    # Plot the data
    plt.figure(figsize=(14, 8))
    g = sns.catplot(
        x="Category",
        y="Amount",
        hue="Bank",
        data=bank_category,
        kind="bar",
        height=6,
        aspect=2,
    )
    g.fig.suptitle("Spending by Category Across Banks", fontsize=16)
    g.set_xticklabels(rotation=45, ha="right")
    plt.tight_layout()
    output_path = f"{output_dir}/bank_category_comparison.png"
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved bank comparison plot to {output_path}")


def plot_income_vs_expenses(df, output_dir):
    """Plot income vs expenses over time"""
    logger.info("Generating income vs expenses plot")
    # Group by month and transaction type
    monthly_flow = (
        df.groupby([pd.Grouper(key="Date", freq="M"), "Type"])["Amount"]
        .sum()
        .reset_index()
    )

    # Pivot data for plotting
    flow_pivot = monthly_flow.pivot_table(
        index="Date", columns="Type", values="Amount", fill_value=0
    )

    # If columns don't exist, create them
    if "credit" not in flow_pivot.columns:
        flow_pivot["credit"] = 0
    if "debit" not in flow_pivot.columns:
        flow_pivot["debit"] = 0

    # Calculate net cash flow
    flow_pivot["net"] = flow_pivot["credit"] - flow_pivot["debit"].abs()

    # Plot
    plt.figure(figsize=(15, 8))
    plt.plot(flow_pivot.index, flow_pivot["credit"], "g-", marker="o", label="Income")
    plt.plot(
        flow_pivot.index, flow_pivot["debit"].abs(), "r-", marker="o", label="Expenses"
    )
    plt.plot(
        flow_pivot.index, flow_pivot["net"], "b--", marker="s", label="Net Cash Flow"
    )

    plt.title("Monthly Income vs. Expenses", fontsize=16)
    plt.xlabel("Month", fontsize=14)
    plt.ylabel("Amount (€)", fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    output_path = f"{output_dir}/income_vs_expenses.png"
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved income vs expenses plot to {output_path}")


def plot_savings_trends(df, output_dir):
    """Plot savings trends over time"""
    logger.info("Generating savings trends plot")
    # Filter for savings transactions
    savings = df[df["Category"] == "Savings"].copy()

    # Group by date
    savings_by_date = savings.groupby("Date")["Amount"].sum().abs().reset_index()

    # Calculate cumulative savings
    savings_by_date["Cumulative"] = savings_by_date["Amount"].cumsum()

    # Plot
    plt.figure(figsize=(15, 8))

    # Individual savings transactions
    plt.bar(
        savings_by_date["Date"],
        savings_by_date["Amount"],
        alpha=0.6,
        color="skyblue",
        label="Daily Savings",
    )

    # Cumulative savings line
    plt.plot(
        savings_by_date["Date"],
        savings_by_date["Cumulative"],
        "r-",
        linewidth=2,
        label="Cumulative Savings",
    )

    plt.title("Savings Trends Over Time", fontsize=16)
    plt.xlabel("Date", fontsize=14)
    plt.ylabel("Amount (€)", fontsize=14)
    plt.legend()
    plt.tight_layout()
    output_path = f"{output_dir}/savings_trends.png"
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved savings trends plot to {output_path}")


def create_essential_vs_nonessential_comparison(df, output_dir):
    """Compare essential vs non-essential spending"""
    logger.info("Generating essential vs non-essential comparison plot")
    # Define essential categories
    essential_categories = [
        "Groceries",
        "Housing",
        "Utilities",
        "Transport",
        "Insurances",
    ]

    # Create a new column indicating if expense is essential
    expenses = df[df["Type"] == "debit"].copy()
    expenses["Necessity"] = expenses["Category"].apply(
        lambda x: "Essential" if x in essential_categories else "Non-essential"
    )

    # Group by month and necessity
    monthly_necessity = (
        expenses.groupby([pd.Grouper(key="Date", freq="M"), "Necessity"])["Amount"]
        .sum()
        .abs()
        .reset_index()
    )

    # Pivot for plotting
    necessity_pivot = monthly_necessity.pivot_table(
        index="Date", columns="Necessity", values="Amount", fill_value=0
    )

    # Plot
    plt.figure(figsize=(15, 8))
    necessity_pivot.plot(kind="bar", figsize=(15, 8))
    plt.title("Essential vs. Non-essential Spending", fontsize=16)
    plt.xlabel("Month", fontsize=14)
    plt.ylabel("Amount (€)", fontsize=14)
    plt.legend(title="Expense Type")
    plt.tight_layout()
    output_path = f"{output_dir}/essential_vs_nonessential.png"
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved essential vs non-essential comparison plot to {output_path}")


def plot_monthly_expenses_by_category_and_bank(df, output_dir):
    """Create a single plot showing monthly expenses by category and bank"""
    logger.info("Generating monthly expenses by category and bank plot")
    # Filter for debit transactions only
    expenses = df[df["Type"] == "debit"].copy()
    # Group by month, category, and bank, summing the amounts
    monthly_cat_bank = (
        expenses.groupby([pd.Grouper(key="Date", freq="M"), "Category", "Bank"])[
            "Amount"
        ]
        .sum()
        .abs()
        .reset_index()
    )

    # Create a single facet grid plot
    plt.figure(figsize=(20, 12))
    g = sns.FacetGrid(
        monthly_cat_bank, col="Category", col_wrap=3, height=4, aspect=1.2, sharey=False
    )
    g.map_dataframe(sns.barplot, x="Date", y="Amount", hue="Bank", palette="colorblind")
    g.set_titles("{col_name}", fontsize=12)

    # Format x-axis labels
    for ax in g.axes.flatten():
        dates = monthly_cat_bank["Date"].dt.strftime("%b %Y").unique()
        ax.set_xticklabels(dates, rotation=45, ha="right")
        ax.set_xlabel("Month")
        ax.set_ylabel("Amount (€)")

    g.fig.suptitle("Monthly Expenses by Category and Bank", fontsize=16, y=1.02)
    g.add_legend(title="Bank", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    output_path = f"{output_dir}/monthly_expenses_by_category_and_bank.png"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved monthly expenses by category and bank plot to {output_path}")


def main():
    logger.info("Starting visualization generation process")
    # Create output directory if it doesn't exist
    output_dir = os.path.join(PROJECT_ROOT, "docs/plots")
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    # Load data from CSV
    file_path = os.path.join(
        PROJECT_ROOT, "data/categorized_transactions/mistralai.csv"
    )
    try:
        transactions = load_transaction_data(file_path)

        # Generate all plots
        plot_monthly_expenses_by_category(transactions, output_dir)
        plot_bank_comparison(transactions, output_dir)
        plot_income_vs_expenses(transactions, output_dir)
        plot_savings_trends(transactions, output_dir)
        create_essential_vs_nonessential_comparison(transactions, output_dir)
        plot_monthly_expenses_by_category_and_bank(transactions, output_dir)

        logger.info(f"All plots have been generated and saved to {output_dir}")
        print(f"All plots have been generated and saved to {output_dir}")
    except Exception as e:
        logger.error(f"Error during visualization generation: {str(e)}")
        raise


if __name__ == "__main__":
    main()
