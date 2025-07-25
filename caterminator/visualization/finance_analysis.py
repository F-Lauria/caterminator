import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import matplotlib.dates as mdates
import os
import sys

# Set up project path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Set the style for all visualizations
plt.style.use("ggplot")
sns.set_palette("colorblind")


def load_transaction_data(filepath):
    """Load transaction data from CSV file"""
    df = pd.read_csv(filepath)
    # Convert date strings to datetime objects
    df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y")
    # Convert amounts to float and make debits negative
    df["Amount"] = np.where(
        df["Type"] == "debit", -df["Debit"].astype(float), df["Credit"].astype(float)
    )
    return df


def plot_monthly_expenses_by_category(df, output_dir):
    """Create a bar chart of monthly expenses by category"""
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
    pivot_data.plot(kind="bar", stacked=True, figsize=(15, 8))
    plt.title("Monthly Expenses by Category", fontsize=16)
    plt.xlabel("Month", fontsize=14)
    plt.ylabel("Amount (€)", fontsize=14)
    plt.legend(title="Category", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/monthly_expenses_by_category.png")
    plt.close()


def plot_bank_comparison(df, output_dir):
    """Compare spending between different banks"""
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
    plt.savefig(f"{output_dir}/bank_category_comparison.png")
    plt.close()


def plot_income_vs_expenses(df, output_dir):
    """Plot income vs expenses over time"""
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
    plt.savefig(f"{output_dir}/income_vs_expenses.png")
    plt.close()


def plot_savings_trends(df, output_dir):
    """Plot savings trends over time"""
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
    plt.savefig(f"{output_dir}/savings_trends.png")
    plt.close()


def plot_category_distribution_by_bank(df, output_dir):
    """Create pie charts showing category distribution for each bank"""
    banks = df["Bank"].unique()

    fig, axes = plt.subplots(1, len(banks), figsize=(7 * len(banks), 7))
    if len(banks) == 1:
        axes = [axes]

    for i, bank in enumerate(banks):
        bank_data = df[(df["Bank"] == bank) & (df["Type"] == "debit")]
        category_totals = bank_data.groupby("Category")["Amount"].sum().abs()

        # Plot pie chart for this bank
        axes[i].pie(
            category_totals,
            labels=category_totals.index,
            autopct="%1.1f%%",
            startangle=90,
        )
        axes[i].set_title(f"{bank} Expense Distribution")

    plt.tight_layout()
    plt.savefig(f"{output_dir}/category_distribution_by_bank.png")
    plt.close()


def plot_daily_spending_patterns(df, output_dir):
    """Plot spending patterns by day of week"""
    # Add day of week to the dataframe
    expenses = df[df["Type"] == "debit"].copy()
    expenses["DayOfWeek"] = expenses["Date"].dt.day_name()

    # Order days correctly
    day_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    expenses["DayOfWeek"] = pd.Categorical(
        expenses["DayOfWeek"], categories=day_order, ordered=True
    )

    # Plot
    plt.figure(figsize=(14, 8))
    sns.boxplot(x="DayOfWeek", y="Amount", data=expenses, showfliers=False)
    plt.title("Daily Spending Patterns", fontsize=16)
    plt.xlabel("Day of Week", fontsize=14)
    plt.ylabel("Amount Spent (€)", fontsize=14)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/daily_spending_patterns.png")
    plt.close()


def plot_top_merchants(df, output_dir, n=15):
    """Plot top merchants by total spending"""
    merchants = (
        df[df["Type"] == "debit"]
        .groupby("Description")["Amount"]
        .sum()
        .abs()
        .sort_values(ascending=False)
        .head(n)
    )

    plt.figure(figsize=(15, 8))
    merchants.plot(kind="barh")
    plt.title(f"Top {n} Merchants by Total Spending", fontsize=16)
    plt.xlabel("Total Amount (€)", fontsize=14)
    plt.ylabel("Merchant", fontsize=14)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/top_merchants.png")
    plt.close()


def create_essential_vs_nonessential_comparison(df, output_dir):
    """Compare essential vs non-essential spending"""
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
    plt.savefig(f"{output_dir}/essential_vs_nonessential.png")
    plt.close()


def main():
    # Create output directory if it doesn't exist
    output_dir = os.path.join(PROJECT_ROOT, "docs/plots")
    os.makedirs(output_dir, exist_ok=True)

    # Load data from CSV
    file_path = os.path.join(
        PROJECT_ROOT, "data/categorized_transactions/mistralai.csv"
    )
    transactions = load_transaction_data(file_path)

    # Generate all plots
    plot_monthly_expenses_by_category(transactions, output_dir)
    plot_bank_comparison(transactions, output_dir)
    plot_income_vs_expenses(transactions, output_dir)
    plot_savings_trends(transactions, output_dir)
    plot_category_distribution_by_bank(transactions, output_dir)
    plot_daily_spending_patterns(transactions, output_dir)
    plot_top_merchants(transactions, output_dir)
    create_essential_vs_nonessential_comparison(transactions, output_dir)

    print(f"All plots have been generated and saved to {output_dir}")


if __name__ == "__main__":
    main()
