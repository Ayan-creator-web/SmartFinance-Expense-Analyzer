"""
analysis.py — Core Analysis, ML Prediction & AI Insights Engine
SmartFinance AI Expense Analyzer
Author: Your Name
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple
import warnings

warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────
# 1. DESCRIPTIVE ANALYSIS
# ─────────────────────────────────────────────

def get_category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Category-wise total spend, percentage, and average transaction."""
    summary = (
        df.groupby("category")
        .agg(
            total_amount   = ("amount", "sum"),
            num_transactions = ("amount", "count"),
            avg_transaction= ("amount", "mean"),
            max_transaction= ("amount", "max"),
        )
        .reset_index()
    )
    summary["pct_of_total"] = (
        summary["total_amount"] / summary["total_amount"].sum() * 100
    ).round(2)
    summary = summary.sort_values("total_amount", ascending=False).reset_index(drop=True)
    return summary


def get_monthly_category_pivot(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot table: rows = months, columns = categories, values = total spend.
    Useful for heatmaps and monthly comparison charts.
    """
    pivot = (
        df.pivot_table(
            index="month_num",
            columns="category",
            values="amount",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )
    MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    pivot["month_name"] = pivot["month_num"].apply(lambda x: MONTH_NAMES[x - 1])
    return pivot


def get_day_of_week_pattern(df: pd.DataFrame) -> pd.DataFrame:
    """Average spend per day of week (Mon–Sun)."""
    ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday"]
    dow = (
        df.groupby("day_of_week")["amount"]
        .mean()
        .reindex(ORDER)
        .reset_index()
        .rename(columns={"amount": "avg_spend"})
    )
    dow["avg_spend"] = dow["avg_spend"].round(2)
    return dow


def get_payment_method_split(df: pd.DataFrame) -> pd.DataFrame:
    """Payment method usage share."""
    pm = (
        df.groupby("payment_method")["amount"]
        .agg(["sum", "count"])
        .reset_index()
        .rename(columns={"sum": "total", "count": "transactions"})
    )
    pm["pct"] = (pm["total"] / pm["total"].sum() * 100).round(1)
    return pm.sort_values("total", ascending=False)


# ─────────────────────────────────────────────
# 2. ANOMALY DETECTION
# ─────────────────────────────────────────────

def detect_anomalies(df: pd.DataFrame, z_threshold: float = 2.5) -> pd.DataFrame:
    """
    Flag daily totals that deviate more than z_threshold standard deviations
    from the rolling 30-day mean. Returns only the anomalous days.
    """
    daily = df.groupby("date")["amount"].sum().reset_index(name="daily_total")
    daily = daily.sort_values("date")

    rolling_mean = daily["daily_total"].rolling(window=30, min_periods=5).mean()
    rolling_std  = daily["daily_total"].rolling(window=30, min_periods=5).std()

    daily["z_score"] = (daily["daily_total"] - rolling_mean) / rolling_std.replace(0, 1)
    daily["is_anomaly"] = daily["z_score"].abs() > z_threshold
    daily["anomaly_type"] = np.where(
        daily["z_score"] > z_threshold, "Overspending",
        np.where(daily["z_score"] < -z_threshold, "Unusually Low", "Normal"),
    )
    anomalies = daily[daily["is_anomaly"]].copy()
    return anomalies


# ─────────────────────────────────────────────
# 3. ML: NEXT-MONTH SPEND PREDICTION
# ─────────────────────────────────────────────

def predict_next_month(monthly_df: pd.DataFrame) -> Dict:
    """
    Train a simple Linear Regression model on monthly totals and
    predict the next month's expense.

    Returns a dict with:
        predicted_amount, confidence_interval, trend_direction, model_r2
    """
    X = monthly_df["month_num"].values.reshape(-1, 1)
    y = monthly_df["total_expense"].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LinearRegression()
    model.fit(X_scaled, y)

    # Predict month 13 (next year's January equivalent for trend)
    next_month_num = monthly_df["month_num"].max() + 1
    X_next = scaler.transform([[next_month_num]])
    prediction = model.predict(X_next)[0]

    # Simple confidence interval (±1 RMSE)
    y_pred_all = model.predict(X_scaled)
    rmse = np.sqrt(np.mean((y - y_pred_all) ** 2))

    r2 = model.score(X_scaled, y)

    trend = "increasing" if model.coef_[0] > 0 else "decreasing"
    monthly_change_pct = abs(model.coef_[0]) / y.mean() * 100

    return {
        "predicted_amount":    round(prediction, 0),
        "lower_bound":         round(prediction - rmse, 0),
        "upper_bound":         round(prediction + rmse, 0),
        "trend_direction":     trend,
        "monthly_change_pct":  round(monthly_change_pct, 1),
        "model_r2":            round(r2, 3),
    }


# ─────────────────────────────────────────────
# 4. AI INSIGHTS GENERATOR
# ─────────────────────────────────────────────

def get_spending_insights(
    df: pd.DataFrame,
    monthly_df: pd.DataFrame,
    budget: float = 15000.0,
) -> List[Dict]:
    """
    Generate a list of human-readable, actionable financial insights.

    Each insight is a dict:
        { type: 'warning' | 'info' | 'success', title, detail, icon }
    """
    insights = []
    cat_summary = get_category_summary(df)

    # ---- Top category check ----
    top_cat = cat_summary.iloc[0]
    if top_cat["pct_of_total"] > 35:
        insights.append({
            "type":   "warning",
            "title":  f"{top_cat['category']} is {top_cat['pct_of_total']:.0f}% of total spend",
            "detail": f"Above the healthy benchmark of 30%. Consider reducing {top_cat['category']} expenses.",
            "icon":   "(!)",
        })

    # ---- Month-over-month change ----
    if len(monthly_df) >= 2:
        last  = monthly_df.iloc[-1]["total_expense"]
        prev  = monthly_df.iloc[-2]["total_expense"]
        mom_pct = (last - prev) / prev * 100
        if mom_pct > 15:
            insights.append({
                "type":   "warning",
                "title":  f"Spending jumped {mom_pct:.0f}% vs last month",
                "detail": f"This month: ₹{last:,.0f} vs last month: ₹{prev:,.0f}",
                "icon":   "(!)",
            })
        elif mom_pct < -10:
            insights.append({
                "type":   "success",
                "title":  f"Spending dropped {abs(mom_pct):.0f}% — great discipline!",
                "detail": f"You saved ₹{prev - last:,.0f} more than last month.",
                "icon":   "(+)",
            })

    # ---- Budget alert ----
    current_month_expense = df[df["month_num"] == df["month_num"].max()]["amount"].sum()
    budget_pct = current_month_expense / budget * 100
    if budget_pct > 90:
        insights.append({
            "type":   "warning",
            "title":  f"Budget almost exhausted — {budget_pct:.0f}% used",
            "detail": f"Only ₹{budget - current_month_expense:,.0f} left for the month.",
            "icon":   "(!)",
        })
    elif budget_pct > 75:
        insights.append({
            "type":   "info",
            "title":  f"{budget_pct:.0f}% of monthly budget used",
            "detail": "You're on track but watch your discretionary spending.",
            "icon":   "(i)",
        })

    # ---- Weekend vs weekday spending ----
    weekend_avg = df[df["is_weekend"]]["amount"].mean()
    weekday_avg = df[~df["is_weekend"]]["amount"].mean()
    if weekend_avg > weekday_avg * 1.4:
        insights.append({
            "type":   "info",
            "title":  f"Weekend spend is {(weekend_avg/weekday_avg - 1)*100:.0f}% higher",
            "detail": "You spend significantly more on weekends. Plan weekend budgets.",
            "icon":   "(i)",
        })

    # ---- Savings check ----
    avg_savings = monthly_df["savings"].mean()
    if avg_savings > 0:
        savings_rate = avg_savings / monthly_df["income"].mean() * 100
        insights.append({
            "type":   "success",
            "title":  f"Average savings rate: {savings_rate:.0f}% per month",
            "detail": f"You save ₹{avg_savings:,.0f}/month on average. Strong financial habit!",
            "icon":   "(+)",
        })

    # ---- UPI dominance ----
    upi_pct = len(df[df["payment_method"] == "UPI"]) / len(df) * 100
    if upi_pct > 50:
        insights.append({
            "type":   "info",
            "title":  f"{upi_pct:.0f}% of payments via UPI",
            "detail": "Good digital payment hygiene — keeps transactions trackable.",
            "icon":   "(i)",
        })

    return insights


# ─────────────────────────────────────────────
# 5. BUDGET ANALYSIS
# ─────────────────────────────────────────────

def analyse_budget(
    df: pd.DataFrame,
    monthly_budget: float = 15000.0,
) -> pd.DataFrame:
    """
    Month-wise budget vs actual vs remaining.
    """
    monthly = df.groupby("month_num")["amount"].sum().reset_index(name="actual")
    MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly["month_name"] = monthly["month_num"].apply(lambda x: MONTH_NAMES[x - 1])
    monthly["budget"]     = monthly_budget
    monthly["remaining"]  = monthly["budget"] - monthly["actual"]
    monthly["used_pct"]   = (monthly["actual"] / monthly["budget"] * 100).round(1)
    monthly["status"]     = monthly["used_pct"].apply(
        lambda p: "Over Budget" if p > 100 else ("Near Limit" if p > 80 else "On Track")
    )
    return monthly


if __name__ == "__main__":
    from data_gen import generate_expense_data, generate_monthly_summary
    df = generate_expense_data()
    monthly = generate_monthly_summary(df)

    print("=== Category Summary ===")
    print(get_category_summary(df).to_string(index=False))

    print("\n=== Prediction ===")
    pred = predict_next_month(monthly)
    for k, v in pred.items():
        print(f"  {k}: {v}")

    print("\n=== AI Insights ===")
    for ins in get_spending_insights(df, monthly):
        print(f"  {ins['icon']}  {ins['title']}")
        print(f"     {ins['detail']}")
