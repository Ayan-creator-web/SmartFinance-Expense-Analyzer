"""
data_gen.py — Synthetic Expense Data Generator
SmartFinance AI Expense Analyzer
Author: Your Name
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os


def generate_expense_data(year: int = 2025, seed: int = 42) -> pd.DataFrame:
    """
    Generate realistic synthetic expense data for a student / young professional.

    Parameters
    ----------
    year : int   — year to simulate (default 2025)
    seed : int   — random seed for reproducibility

    Returns
    -------
    pd.DataFrame with columns:
        date, category, subcategory, amount, payment_method,
        day_of_week, month, month_num, week, is_weekend, is_festival
    """
    np.random.seed(seed)
    random.seed(seed)

    # ---- Category config: (mean_per_transaction, std) ----
    CATEGORIES = {
        "Rent":          (5000, 0),        # fixed monthly
        "Food":          (280,  140),
        "Travel":        (320,  200),
        "Entertainment": (450,  250),
        "Education":     (600,  300),
        "Health":        (350,  180),
        "Utilities":     (280,  50),
        "Shopping":      (750,  400),
    }

    SUBCATEGORIES = {
        "Rent":          ["Apartment Rent"],
        "Food":          ["Zomato", "Swiggy", "Grocery", "Restaurant", "Cafe"],
        "Travel":        ["Uber", "Ola", "Metro", "Train", "Bus", "Flight"],
        "Entertainment": ["Netflix", "Amazon Prime", "Cinema", "Gaming", "Pub"],
        "Education":     ["Udemy", "Books", "Course Fees", "Stationery"],
        "Health":        ["Pharmacy", "Gym", "Doctor", "Lab Test"],
        "Utilities":     ["Electricity", "Internet", "Mobile Recharge"],
        "Shopping":      ["Clothes", "Electronics", "Amazon", "Flipkart"],
    }

    PAYMENT_METHODS = ["UPI", "Cash", "Credit Card", "Debit Card", "Net Banking"]
    PAYMENT_WEIGHTS  = [0.45,  0.18,  0.17,          0.12,          0.08]

    # Rent is paid once a month, everything else is daily
    # Category sampling weights (not for Rent — handled separately)
    CAT_DAILY = ["Food", "Travel", "Entertainment", "Education",
                 "Health", "Utilities", "Shopping"]
    CAT_WEIGHTS = [0.38, 0.22, 0.14, 0.10, 0.06, 0.05, 0.05]

    # Festival months (Diwali, Durga Puja, Christmas)
    FESTIVAL_MONTHS = {10, 11, 12}

    records = []
    start_date = datetime(year, 1, 1)
    end_date   = datetime(year, 12, 31)
    current    = start_date

    while current <= end_date:
        is_weekend = current.weekday() >= 5
        is_festival = current.month in FESTIVAL_MONTHS and current.day <= 20

        # --- Monthly fixed: Rent on the 1st ---
        if current.day == 1:
            records.append({
                "date":           current.date(),
                "category":       "Rent",
                "subcategory":    "Apartment Rent",
                "amount":         5000.0,
                "payment_method": "Net Banking",
                "day_of_week":    current.strftime("%A"),
                "month":          current.strftime("%B"),
                "month_num":      current.month,
                "week":           current.isocalendar()[1],
                "is_weekend":     is_weekend,
                "is_festival":    is_festival,
            })

        # --- Variable daily transactions ---
        base_txn = 3 if is_weekend else 2
        n_txn = np.random.poisson(base_txn + (1 if is_festival else 0))

        for _ in range(max(1, n_txn)):
            cat = np.random.choice(CAT_DAILY, p=CAT_WEIGHTS)
            mean, std = CATEGORIES[cat]

            amount = max(30, np.random.normal(mean, std))
            if is_festival and cat in ("Shopping", "Entertainment", "Food"):
                amount *= np.random.uniform(1.3, 1.8)
            if is_weekend and cat in ("Entertainment", "Food", "Travel"):
                amount *= np.random.uniform(1.1, 1.4)

            subcategory = random.choice(SUBCATEGORIES[cat])
            payment = random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS)[0]

            records.append({
                "date":           current.date(),
                "category":       cat,
                "subcategory":    subcategory,
                "amount":         round(amount, 2),
                "payment_method": payment,
                "day_of_week":    current.strftime("%A"),
                "month":          current.strftime("%B"),
                "month_num":      current.month,
                "week":           current.isocalendar()[1],
                "is_weekend":     is_weekend,
                "is_festival":    is_festival,
            })

        current += timedelta(days=1)

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def generate_monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a month-level summary with income, expense, and savings columns.
    Income is simulated (base stipend + occasional bonuses).
    """
    INCOME_MAP = {
        1: 18000, 2: 18000, 3: 18000, 4: 18000,
        5: 22000, 6: 18000, 7: 18000, 8: 18000,
        9: 18000, 10: 20000, 11: 18000, 12: 25000,
    }
    MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    monthly = (
        df.groupby("month_num", as_index=False)["amount"]
        .sum()
        .rename(columns={"amount": "total_expense"})
    )
    monthly["income"]     = monthly["month_num"].map(INCOME_MAP)
    monthly["savings"]    = monthly["income"] - monthly["total_expense"]
    monthly["month_name"] = monthly["month_num"].apply(lambda x: MONTH_NAMES[x - 1])
    monthly["savings_pct"] = (monthly["savings"] / monthly["income"] * 100).round(1)
    return monthly


def save_data(df: pd.DataFrame, path: str = "data/expenses_2025.csv") -> None:
    """Save the dataset to CSV."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"[OK] Dataset saved to {path}  ({len(df):,} rows)")


if __name__ == "__main__":
    df = generate_expense_data()
    monthly = generate_monthly_summary(df)
    save_data(df)
    print(df.head(10).to_string())
    print(f"\nTotal annual expense: ₹{df['amount'].sum():,.0f}")
    print(f"Transactions generated: {len(df):,}")
