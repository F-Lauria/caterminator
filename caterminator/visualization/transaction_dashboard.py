import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

# Initialize the Dash app
app = dash.Dash(__name__, title="Personal Finance Dashboard")


# Load and prepare data
def load_data():
    df = pd.read_csv(
        "/Users/francescolauria/Documents/repos/caterminator/data/categorized_transactions/mistralai.csv"
    )
    df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y")
    df["Month"] = df["Date"].dt.strftime("%Y-%m")
    df["Amount"] = np.where(
        df["Type"] == "debit", -df["Debit"].astype(float), df["Credit"].astype(float)
    )
    return df


# Layout of the dashboard
app.layout = html.Div(
    [
        html.H1("Personal Finance Dashboard"),
        html.Div(
            [
                html.Div(
                    [
                        html.H3("Select Date Range:"),
                        dcc.DatePickerRange(
                            id="date-picker-range",
                            min_date_allowed=datetime(2025, 5, 1),
                            max_date_allowed=datetime(2025, 7, 31),
                            start_date=datetime(2025, 5, 1),
                            end_date=datetime(2025, 6, 30),
                        ),
                    ],
                    style={"width": "48%", "display": "inline-block"},
                ),
                html.Div(
                    [
                        html.H3("Select Bank:"),
                        dcc.Dropdown(
                            id="bank-selector",
                            options=[
                                {"label": "All Banks", "value": "all"},
                                {"label": "ABN", "value": "ABN"},
                                {"label": "ING", "value": "ING"},
                            ],
                            value="all",
                        ),
                    ],
                    style={"width": "48%", "display": "inline-block"},
                ),
            ]
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H3("Monthly Income vs Expenses"),
                        dcc.Graph(id="income-expenses-graph"),
                    ],
                    style={"width": "100%"},
                ),
            ],
            style={"margin-top": "20px"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H3("Category Distribution"),
                        dcc.Graph(id="category-pie"),
                    ],
                    style={"width": "48%", "display": "inline-block"},
                ),
                html.Div(
                    [
                        html.H3("Top Spending Categories"),
                        dcc.Graph(id="top-categories-bar"),
                    ],
                    style={"width": "48%", "display": "inline-block"},
                ),
            ],
            style={"margin-top": "20px"},
        ),
        html.Div(
            [
                html.H3("Transaction Timeline"),
                dcc.Graph(id="transaction-timeline"),
            ],
            style={"margin-top": "20px"},
        ),
        html.Div(
            [
                html.H3("Bank Comparison"),
                dcc.Graph(id="bank-comparison"),
            ],
            style={"margin-top": "20px"},
        ),
    ],
    style={"padding": "20px"},
)


# Callbacks for interactive elements
@app.callback(
    [
        Output("income-expenses-graph", "figure"),
        Output("category-pie", "figure"),
        Output("top-categories-bar", "figure"),
        Output("transaction-timeline", "figure"),
        Output("bank-comparison", "figure"),
    ],
    [
        Input("date-picker-range", "start_date"),
        Input("date-picker-range", "end_date"),
        Input("bank-selector", "value"),
    ],
)
def update_graphs(start_date, end_date, selected_bank):
    df = load_data()

    # Filter by date range
    filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

    # Filter by bank if specified
    if selected_bank != "all":
        filtered_df = filtered_df[filtered_df["Bank"] == selected_bank]

    # Income vs Expenses Graph
    monthly_flow = filtered_df.groupby(["Month", "Type"])["Amount"].sum().reset_index()
    income_expenses = px.bar(
        monthly_flow,
        x="Month",
        y="Amount",
        color="Type",
        title="Monthly Income vs Expenses",
        labels={"Amount": "Amount (€)", "Month": "Month"},
    )

    # Category Distribution Pie Chart
    expense_categories = (
        filtered_df[filtered_df["Type"] == "debit"]
        .groupby("Category")["Amount"]
        .sum()
        .abs()
    )
    category_pie = px.pie(
        values=expense_categories,
        names=expense_categories.index,
        title="Expense Distribution by Category",
    )

    # Top Categories Bar Chart
    top_categories = (
        filtered_df[filtered_df["Type"] == "debit"]
        .groupby("Category")["Amount"]
        .sum()
        .abs()
    )
    top_categories = top_categories.sort_values(ascending=False).head(10)
    top_cat_bar = px.bar(
        y=top_categories.index,
        x=top_categories.values,
        title="Top Expense Categories",
        labels={"x": "Amount (€)", "y": "Category"},
        orientation="h",
    )

    # Transaction Timeline
    timeline = px.scatter(
        filtered_df,
        x="Date",
        y="Amount",
        color="Type",
        hover_data=["Description", "Category"],
        title="Transaction Timeline",
    )

    # Bank Comparison (if 'all' is selected)
    if selected_bank == "all":
        bank_comparison = px.box(
            filtered_df[filtered_df["Type"] == "debit"],
            x="Bank",
            y="Amount",
            color="Bank",
            title="Transaction Amount Distribution by Bank",
        )
    else:
        # Alternative chart when a specific bank is selected
        daily_amounts = filtered_df.groupby(filtered_df["Date"].dt.date)["Amount"].sum()
        bank_comparison = px.line(
            x=daily_amounts.index,
            y=daily_amounts.values,
            title=f"Daily Net Cash Flow - {selected_bank}",
            labels={"x": "Date", "y": "Net Amount (€)"},
        )

    return income_expenses, category_pie, top_cat_bar, timeline, bank_comparison


if __name__ == "__main__":
    app.run_server(debug=True)
