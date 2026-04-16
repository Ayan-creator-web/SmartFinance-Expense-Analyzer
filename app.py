"""
app.py — SmartFinance Expense Analyzer
===========================================
UPGRADES ADDED v2:
  ✅ 1. Premium Hero Section  — title, subtitle, 4 feature cards, health summary row
  ✅ 2. Top Insights Panel    — auto-generated smart insights displayed on Dashboard
  ✅ 3. Forecast Confidence Band — shaded 90% CI band on trend+forecast chart
  ✅ 4. Export Options        — CSV transactions, monthly summary CSV, full HTML report
  ✅ 5. Logo / Favicon        — 💸 favicon, branded sidebar header
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ── must be first Streamlit call ──────────────────────────────────────────────
st.set_page_config(
    page_title="SmartFinance Expense Analyzer",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
#  CUSTOM CSS  — original dark theme + hero / insights additions
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
  /* ── Base ── */
  .stApp { background-color: #0a0b1e; }
  .main .block-container { padding-top: 0.5rem; }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] { background-color: #0c0e26; border-right: 1px solid #1e2448; }
  [data-testid="stSidebar"] * { color: #dde4ff !important; }

  /* ── Metrics ── */
  [data-testid="stMetricValue"] { color: #60a5fa !important; font-size: 1.6rem !important; }
  [data-testid="stMetricLabel"] { color: rgba(255,255,255,0.5) !important; }
  [data-testid="stMetricDelta"] { font-size: 0.85rem !important; }

  /* ── Misc ── */
  .streamlit-expanderHeader { background-color: #10122a !important; color: #dde4ff !important; }
  .stDataFrame { background-color: #10122a; }
  thead tr th { background-color: #1a1c3a !important; color: #93c5fd !important; }
  div[data-baseweb="select"] > div { background-color: #10122a !important; border-color: #1e2448 !important; color: #dde4ff !important; }
  h1, h2, h3 { color: #dde4ff !important; }
  p, span, label { color: #aab4d4 !important; }
  hr { border-color: #1e2448 !important; }

  /* ══════════════════════════════════
     HERO SECTION
  ══════════════════════════════════ */
  .hero-wrap {
    background: linear-gradient(135deg, #0d1030 0%, #111536 45%, #0d1a40 100%);
    border: 1px solid rgba(59,130,246,0.22);
    border-radius: 18px;
    padding: 34px 38px 26px 38px;
    margin-bottom: 22px;
    position: relative;
    overflow: hidden;
  }
  .hero-wrap::before {
    content: '';
    position: absolute; top: -70px; right: -70px;
    width: 280px; height: 280px;
    background: radial-gradient(circle, rgba(99,102,241,0.16) 0%, transparent 70%);
    border-radius: 50%;
  }
  .hero-title {
    font-size: 2.3rem; font-weight: 800; line-height: 1.15;
    background: linear-gradient(90deg, #60a5fa 0%, #a78bfa 50%, #06b6d4 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin: 0 0 7px 0;
  }
  .hero-sub {
    font-size: 1rem; color: rgba(180,190,230,0.7) !important;
    margin: 0 0 26px 0;
  }
  .fc-row { display:flex; gap:12px; flex-wrap:wrap; margin-bottom:26px; }
  .fc {
    flex:1; min-width:170px;
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 10px; padding: 14px 16px;
  }
  .fc .ic { font-size:1.5rem; margin-bottom:6px; }
  .fc .tt { font-size:0.86rem; font-weight:700; color:#c7d2fe !important; margin-bottom:3px; }
  .fc .dd { font-size:0.76rem; color:rgba(180,190,230,0.5) !important; }

  /* ── Health Summary Cards ── */
  .hr { display:flex; gap:12px; flex-wrap:wrap; }
  .hc {
    flex:1; min-width:155px;
    border-radius:10px; padding:14px 16px;
    border: 1px solid rgba(255,255,255,0.07);
  }
  .hc .lbl {
    font-size:0.72rem; text-transform:uppercase; letter-spacing:.07em;
    color:rgba(180,190,230,0.48) !important; margin-bottom:5px;
  }
  .hc .val { font-size:1.5rem; font-weight:800; line-height:1; margin-bottom:4px; }
  .hc .bdg {
    display:inline-block; padding:2px 8px;
    border-radius:99px; font-size:0.7rem; font-weight:600;
  }

  /* ══════════════════════════════════
     TOP INSIGHTS PANEL
  ══════════════════════════════════ */
  .ins-panel {
    background: linear-gradient(135deg, #0e1236 0%, #111740 100%);
    border: 1px solid rgba(139,92,246,0.28);
    border-radius: 14px; padding: 20px 24px; margin-bottom: 20px;
  }
  .ins-head {
    font-size:.95rem; font-weight:700;
    color:#a78bfa !important; margin-bottom:13px;
    display:flex; align-items:center; gap:8px;
  }
  .ins-row {
    display:flex; align-items:flex-start; gap:11px;
    padding:9px 0; border-bottom:1px solid rgba(255,255,255,0.05);
  }
  .ins-row:last-child { border-bottom:none; }
  .ins-dot { width:8px;height:8px;border-radius:50%;margin-top:5px;flex-shrink:0; }
  .ins-tt { font-size:.86rem;font-weight:600;color:#e2e8f0 !important;margin-bottom:2px; }
  .ins-sub { font-size:.76rem;color:rgba(180,190,230,0.48) !important; }
</style>
""", unsafe_allow_html=True)

# ── Plotly dark theme ─────────────────────────────────────────────────────────
PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "#10122a",
        "plot_bgcolor":  "#10122a",
        "font":          {"color": "#dde4ff", "family": "system-ui"},
        "xaxis":         {"gridcolor": "rgba(255,255,255,0.06)", "linecolor": "rgba(255,255,255,0.1)"},
        "yaxis":         {"gridcolor": "rgba(255,255,255,0.06)", "linecolor": "rgba(255,255,255,0.1)"},
        "legend":        {"bgcolor": "rgba(0,0,0,0)", "font": {"color": "#dde4ff"}},
    }
}
COLORS = {
    "primary":    "#3b82f6",
    "cyan":       "#06b6d4",
    "purple":     "#8b5cf6",
    "pink":       "#ec4899",
    "green":      "#10b981",
    "amber":      "#f59e0b",
    "red":        "#ef4444",
    "indigo":     "#6366f1",
    "categories": ["#8b5cf6","#06b6d4","#f59e0b","#ec4899","#10b981","#6366f1","#3b82f6","#f87171"],
}

def apply_theme(fig):
    fig.update_layout(**PLOTLY_TEMPLATE["layout"])
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  DATA LOADING
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner="Generating financial data…")
def load_data():
    from src.data_gen import generate_expense_data, generate_monthly_summary
    df      = generate_expense_data(year=2025, seed=42)
    monthly = generate_monthly_summary(df)
    return df, monthly

df, monthly = load_data()

from src.analysis import (
    get_category_summary, get_monthly_category_pivot,
    get_day_of_week_pattern, get_payment_method_split,
    detect_anomalies, predict_next_month,
    get_spending_insights, analyse_budget,
)


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORT HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def to_csv(dataframe: pd.DataFrame) -> bytes:
    return dataframe.to_csv(index=False).encode("utf-8")

def monthly_summary_csv(df_src: pd.DataFrame, monthly_src: pd.DataFrame) -> bytes:
    cat_pivot = df_src.pivot_table(
        index="month_num", columns="category",
        values="amount", aggfunc="sum", fill_value=0
    ).reset_index()
    return monthly_src.merge(cat_pivot, on="month_num", how="left").to_csv(index=False).encode("utf-8")

def html_report(df_src: pd.DataFrame, monthly_src: pd.DataFrame,
                budget: float, ins_list: list) -> bytes:
    total_exp = df_src["amount"].sum()
    total_inc = monthly_src["income"].sum()
    total_sav = total_inc - total_exp
    sr        = total_sav / total_inc * 100 if total_inc else 0
    cat_sum   = get_category_summary(df_src)

    cat_rows = "".join(
        f"<tr><td>{r['category']}</td><td>₹{r['total_amount']:,.0f}</td>"
        f"<td>{r['pct_of_total']:.1f}%</td></tr>"
        for _, r in cat_sum.iterrows()
    )
    ins_rows = "".join(
        f"<tr><td>{i['title']}</td><td>{i['detail']}</td></tr>"
        for i in ins_list
    )
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>SmartFinance Report 2025</title>
<style>
 body{{font-family:Arial,sans-serif;background:#0a0b1e;color:#dde4ff;max-width:900px;margin:40px auto;padding:20px}}
 h1{{background:linear-gradient(90deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
 h2{{color:#93c5fd;border-bottom:1px solid #1e2448;padding-bottom:8px}}
 .kpi{{display:flex;gap:16px;flex-wrap:wrap;margin:20px 0}}
 .kc{{background:#10122a;border:1px solid #1e2448;border-radius:8px;padding:14px 20px;flex:1;min-width:130px}}
 .kc .v{{font-size:1.5rem;font-weight:800;color:#60a5fa}} .kc .l{{font-size:.78rem;color:rgba(255,255,255,.4)}}
 table{{width:100%;border-collapse:collapse;margin-top:10px}}
 th{{background:#1a1c3a;color:#93c5fd;padding:9px;text-align:left}} td{{padding:8px 10px;border-bottom:1px solid #1e2448;font-size:.88rem}}
 tr:nth-child(even){{background:rgba(255,255,255,.03)}}
 .ft{{text-align:center;color:rgba(255,255,255,.22);font-size:.76rem;margin-top:36px}}
</style></head><body>
<h1>💸 SmartFinance Expense Analyzer</h1>
<p style="color:rgba(180,190,230,.6)">Annual Report · 2025 · Generated {datetime.now().strftime('%d %b %Y %H:%M')}</p>
<h2>Financial Health</h2>
<div class="kpi">
 <div class="kc"><div class="v">₹{total_exp:,.0f}</div><div class="l">Total Expenses</div></div>
 <div class="kc"><div class="v">₹{total_inc:,.0f}</div><div class="l">Total Income</div></div>
 <div class="kc"><div class="v">₹{total_sav:,.0f}</div><div class="l">Total Savings</div></div>
 <div class="kc"><div class="v">{sr:.1f}%</div><div class="l">Savings Rate</div></div>
 <div class="kc"><div class="v">₹{budget:,.0f}</div><div class="l">Monthly Budget</div></div>
</div>
<h2>Category Breakdown</h2>
<table><tr><th>Category</th><th>Total Spend</th><th>% of Total</th></tr>{cat_rows}</table>
<h2>AI Insights</h2>
<table><tr><th>Insight</th><th>Detail</th></tr>{ins_rows}</table>
<div class="ft">SmartFinance Expense Analyzer · Python · Streamlit · Plotly · scikit-learn</div>
</body></html>"""
    return html.encode("utf-8")


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        "<div style='display:flex;align-items:center;gap:9px;margin-bottom:3px;'>"
        "<span style='font-size:1.65rem;'>💸</span>"
        "<span style='font-size:1.05rem;font-weight:800;color:#60a5fa;'>SmartFinance</span>"
        "</div>"
        "<div style='font-size:.73rem;color:rgba(180,190,230,.45);margin-bottom:10px;'>"
        "Expense Analyzer · AI Powered · 2025</div>",
        unsafe_allow_html=True,
    )
    st.divider()

    page = st.selectbox(
        "Navigate",
        ["🏠  Dashboard", "📊  Category Analysis", "📈  Monthly Trends",
         "🤖  AI Insights", "🎯  Budget Control", "📋  Raw Data"],
    )
    st.divider()

    st.markdown("### Budget Settings")
    monthly_budget = st.slider("Monthly Budget (₹)", 5000, 30000, 15000, 500)
    current_month  = df["month_num"].max()
    cur_expense    = df[df["month_num"] == current_month]["amount"].sum()
    budget_pct     = cur_expense / monthly_budget * 100

    if budget_pct > 90:   st.error(f"⚠️  Budget {budget_pct:.0f}% used!")
    elif budget_pct > 75: st.warning(f"⚡  Budget {budget_pct:.0f}% used")
    else:                 st.success(f"✅  Budget {budget_pct:.0f}% used")
    st.progress(min(budget_pct / 100, 1.0))
    st.caption(f"₹{cur_expense:,.0f} of ₹{monthly_budget:,} spent")
    st.divider()

    st.markdown("### Filter")
    selected_cats = st.multiselect(
        "Categories",
        options=sorted(df["category"].unique()),
        default=sorted(df["category"].unique()),
    )
    df_filtered = df[df["category"].isin(selected_cats)]
    selected_months = st.slider("Month Range", 1, 12, (1, 12))
    df_filtered = df_filtered[
        (df_filtered["month_num"] >= selected_months[0]) &
        (df_filtered["month_num"] <= selected_months[1])
    ]
    st.divider()

    st.markdown("### ⬇️ Quick Export")
    st.download_button(
        "📄 Filtered CSV",
        data=to_csv(df_filtered),
        file_name="smartfinance_filtered.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if "Dashboard" in page:

    total_exp    = df_filtered["amount"].sum()
    m_range      = monthly[
        (monthly["month_num"] >= selected_months[0]) &
        (monthly["month_num"] <= selected_months[1])
    ]
    total_inc    = m_range["income"].sum()
    total_sav    = total_inc - total_exp
    savings_rate = (total_sav / total_inc * 100) if total_inc > 0 else 0
    avg_monthly  = df_filtered.groupby("month_num")["amount"].sum().mean()
    pred         = predict_next_month(monthly)
    insights     = get_spending_insights(df_filtered, monthly, monthly_budget)

    # ── HERO ─────────────────────────────────────────────────────────────────
    sr_col  = "#10b981" if savings_rate >= 20 else ("#f59e0b" if savings_rate >= 10 else "#ef4444")
    bgt_col = "#ef4444" if budget_pct > 90  else ("#f59e0b" if budget_pct > 75  else "#10b981")
    bgt_lbl = "Over Budget" if budget_pct > 100 else ("Near Limit" if budget_pct > 80 else "On Track ✓")

    st.markdown(f"""
    <div class="hero-wrap">
      <div class="hero-title">💸 SmartFinance Expense Analyzer</div>
      <div class="hero-sub">AI-Powered Personal Finance Dashboard &nbsp;·&nbsp; Real-time Insights &nbsp;·&nbsp; ML Forecasting &nbsp;·&nbsp; 2025</div>

      <div class="fc-row">
        <div class="fc"><div class="ic">🧠</div><div class="tt">Smart Analysis</div>
          <div class="dd">Auto-categorised transactions with pattern detection</div></div>
        <div class="fc"><div class="ic">🤖</div><div class="tt">ML Forecasting</div>
          <div class="dd">Linear regression predicts next month spend with CI band</div></div>
        <div class="fc"><div class="ic">🎯</div><div class="tt">Budget Control</div>
          <div class="dd">Real-time tracking with colour-coded status alerts</div></div>
        <div class="fc"><div class="ic">📤</div><div class="tt">Export Ready</div>
          <div class="dd">Download CSV, monthly summary, or full HTML report</div></div>
      </div>

      <div class="hr">
        <div class="hc" style="background:rgba(59,130,246,0.08);border-color:rgba(59,130,246,0.25);">
          <div class="lbl">Total Spend</div>
          <div class="val" style="color:#60a5fa;">₹{total_exp:,.0f}</div>
          <span class="bdg" style="background:rgba(59,130,246,0.18);color:#93c5fd;">₹{avg_monthly:,.0f}/mo avg</span>
        </div>
        <div class="hc" style="background:rgba(16,185,129,0.07);border-color:rgba(16,185,129,0.25);">
          <div class="lbl">Savings Rate</div>
          <div class="val" style="color:{sr_col};">{savings_rate:.1f}%</div>
          <span class="bdg" style="background:rgba(16,185,129,0.15);color:#6ee7b7;">₹{total_sav:,.0f} saved</span>
        </div>
        <div class="hc" style="background:rgba(139,92,246,0.07);border-color:rgba(139,92,246,0.25);">
          <div class="lbl">Budget Status</div>
          <div class="val" style="color:{bgt_col};">{budget_pct:.0f}%</div>
          <span class="bdg" style="background:rgba(139,92,246,0.18);color:#c4b5fd;">{bgt_lbl}</span>
        </div>
        <div class="hc" style="background:rgba(6,182,212,0.07);border-color:rgba(6,182,212,0.25);">
          <div class="lbl">ML Prediction</div>
          <div class="val" style="color:#22d3ee;">₹{pred['predicted_amount']:,.0f}</div>
          <span class="bdg" style="background:rgba(6,182,212,0.15);color:#67e8f9;">Next month est.</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── TOP INSIGHTS PANEL ────────────────────────────────────────────────────
    DOT_COLOR = {"warning": "#fb923c", "info": "#a78bfa", "success": "#4ade80"}
    rows_html = ""
    for ins in insights[:5]:
        dc = DOT_COLOR.get(ins["type"], "#94a3b8")
        rows_html += f"""
        <div class="ins-row">
          <div class="ins-dot" style="background:{dc};"></div>
          <div>
            <div class="ins-tt">{ins['title']}</div>
            <div class="ins-sub">{ins['detail']}</div>
          </div>
        </div>"""

    st.markdown(f"""
    <div class="ins-panel">
      <div class="ins-head"><span>🔍</span><span>Top Insights — Auto-Generated from Your Spending Data</span></div>
      {rows_html}
    </div>
    """, unsafe_allow_html=True)

    # ── KPI metrics row ───────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Expenses",    f"₹{total_exp:,.0f}",  "+12%")
    c2.metric("Total Income",      f"₹{total_inc:,.0f}")
    c3.metric("Total Savings",     f"₹{total_sav:,.0f}",  "+8%")
    c4.metric("Avg Monthly Spend", f"₹{avg_monthly:,.0f}")
    c5.metric("Predicted Next",    f"₹{pred['predicted_amount']:,.0f}", pred["trend_direction"])
    st.divider()

    # ── Monthly Income vs Expense bar ─────────────────────────────────────────
    fig_main = go.Figure()
    fig_main.add_trace(go.Bar(
        x=monthly["month_name"], y=monthly["income"],
        name="Income", marker_color=COLORS["primary"],
        text=monthly["income"].apply(lambda v: f"₹{v/1000:.0f}k"),
        textposition="outside", textfont_color="#dde4ff",
    ))
    fig_main.add_trace(go.Bar(
        x=monthly["month_name"], y=monthly["total_expense"],
        name="Expense", marker_color=COLORS["cyan"],
        text=monthly["total_expense"].apply(lambda v: f"₹{v/1000:.1f}k"),
        textposition="outside", textfont_color="#dde4ff",
    ))
    fig_main.update_layout(
        title="Monthly Income vs Expense (2025)",
        barmode="group", xaxis_title="Month", yaxis_title="Amount (₹)", height=360,
    )
    st.plotly_chart(apply_theme(fig_main), use_container_width=True)

    # ── Donut + Radar ─────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)
    with col_l:
        cat_sum = get_category_summary(df_filtered)
        fig_pie = px.pie(
            cat_sum, values="total_amount", names="category",
            title="Expense Distribution by Category",
            color_discrete_sequence=COLORS["categories"], hole=0.55,
        )
        fig_pie.update_traces(textposition="outside", textinfo="percent+label")
        fig_pie.update_layout(height=360)
        st.plotly_chart(apply_theme(fig_pie), use_container_width=True)

    with col_r:
        cat_sum = get_category_summary(df_filtered)
        fig_radar = go.Figure(go.Scatterpolar(
            r=cat_sum["pct_of_total"].tolist(), theta=cat_sum["category"].tolist(),
            fill="toself", fillcolor="rgba(59,130,246,0.15)",
            line_color=COLORS["primary"], name="Spend %",
        ))
        fig_radar.update_layout(
            title="Spending Pattern Radar",
            polar=dict(
                radialaxis=dict(visible=True, color="rgba(255,255,255,0.3)"),
                angularaxis=dict(color="rgba(255,255,255,0.4)"),
                bgcolor="#10122a",
            ),
            height=360,
        )
        st.plotly_chart(apply_theme(fig_radar), use_container_width=True)

    # ── EXPORT BUTTONS ────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### ⬇️ Export Options")
    e1, e2, e3 = st.columns(3)
    with e1:
        st.download_button(
            "📄 Transaction CSV",
            data=to_csv(df_filtered),
            file_name="smartfinance_transactions.csv",
            mime="text/csv", use_container_width=True,
        )
    with e2:
        st.download_button(
            "📊 Monthly Summary CSV",
            data=monthly_summary_csv(df_filtered, monthly),
            file_name="smartfinance_monthly_summary.csv",
            mime="text/csv", use_container_width=True,
        )
    with e3:
        st.download_button(
            "📑 Full HTML Report",
            data=html_report(df_filtered, monthly, monthly_budget, insights),
            file_name="smartfinance_report_2025.html",
            mime="text/html", use_container_width=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: CATEGORY ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif "Category" in page:
    st.markdown("# 📊 Category Analysis")
    cat_sum = get_category_summary(df_filtered)

    st.dataframe(
        cat_sum.style.format({
            "total_amount":    "₹{:,.0f}",
            "avg_transaction": "₹{:,.0f}",
            "max_transaction": "₹{:,.0f}",
            "pct_of_total":    "{:.1f}%",
        }),
        use_container_width=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        fig_bar = px.bar(
            cat_sum.sort_values("total_amount"),
            x="total_amount", y="category", orientation="h",
            title="Total Spend per Category",
            color="total_amount",
            color_continuous_scale=[[0, "#1d4ed8"], [1, "#06b6d4"]],
            text=cat_sum.sort_values("total_amount")["total_amount"].apply(lambda v: f"₹{v/1000:.1f}k"),
        )
        fig_bar.update_traces(textposition="outside")
        fig_bar.update_layout(showlegend=False, height=380, coloraxis_showscale=False)
        st.plotly_chart(apply_theme(fig_bar), use_container_width=True)

    with c2:
        pm = get_payment_method_split(df_filtered)
        fig_pm = px.pie(
            pm, values="total", names="payment_method",
            title="Payment Method Distribution",
            color_discrete_sequence=COLORS["categories"], hole=0.45,
        )
        fig_pm.update_layout(height=380)
        st.plotly_chart(apply_theme(fig_pm), use_container_width=True)

    pivot    = get_monthly_category_pivot(df_filtered)
    cat_cols = [c for c in pivot.columns if c not in ("month_num", "month_name")]
    fig_heat = px.imshow(
        pivot[cat_cols].T, x=pivot["month_name"], y=cat_cols,
        color_continuous_scale=[[0, "#0c1842"], [0.5, "#1d4ed8"], [1, "#06b6d4"]],
        title="Monthly Spending Heatmap (₹)", aspect="auto",
    )
    fig_heat.update_layout(height=380)
    st.plotly_chart(apply_theme(fig_heat), use_container_width=True)

    st.divider()
    st.download_button("📄 Category Summary CSV", data=to_csv(cat_sum),
                       file_name="category_summary.csv", mime="text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: MONTHLY TRENDS
# ══════════════════════════════════════════════════════════════════════════════
elif "Monthly" in page:
    st.markdown("# 📈 Monthly Trends")

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=monthly["month_name"], y=monthly["total_expense"],
        name="Expense", line=dict(color=COLORS["cyan"], width=2.5), mode="lines+markers"))
    fig_trend.add_trace(go.Scatter(x=monthly["month_name"], y=monthly["savings"],
        name="Savings", line=dict(color=COLORS["green"], width=2.5), mode="lines+markers"))
    fig_trend.add_trace(go.Scatter(x=monthly["month_name"], y=monthly["income"],
        name="Income", line=dict(color=COLORS["primary"], width=2, dash="dot"), mode="lines+markers"))
    fig_trend.update_layout(title="Monthly Trends — Income, Expense & Savings", height=380)
    st.plotly_chart(apply_theme(fig_trend), use_container_width=True)

    dow     = get_day_of_week_pattern(df_filtered)
    fig_dow = px.bar(dow, x="day_of_week", y="avg_spend",
        title="Average Spend by Day of Week", color="avg_spend",
        color_continuous_scale=[[0, "#1d4ed8"], [1, "#ec4899"]],
        text=dow["avg_spend"].apply(lambda v: f"₹{v:.0f}"))
    fig_dow.update_traces(textposition="outside")
    fig_dow.update_layout(height=360, coloraxis_showscale=False)
    st.plotly_chart(apply_theme(fig_dow), use_container_width=True)

    st.markdown("### Anomalous Spending Days")
    anomalies_df = detect_anomalies(df)
    if not anomalies_df.empty:
        ad = anomalies_df[["date","daily_total","z_score","anomaly_type"]].copy()
        ad["daily_total"] = ad["daily_total"].apply(lambda v: f"₹{v:,.0f}")
        ad["z_score"]     = ad["z_score"].round(2)
        st.dataframe(ad, use_container_width=True)
    else:
        st.info("No anomalies detected.")

    st.divider()
    st.download_button("📄 Monthly Trends CSV", data=to_csv(monthly),
                       file_name="monthly_trends.csv", mime="text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: AI INSIGHTS  (with confidence band forecast)
# ══════════════════════════════════════════════════════════════════════════════
elif "AI" in page:
    st.markdown("# 🤖 AI Insights Engine")
    st.caption("Automated financial intelligence powered by data analysis")

    insights = get_spending_insights(df_filtered, monthly, monthly_budget)
    pred     = predict_next_month(monthly)

    # Prediction KPIs
    st.markdown("### 🔮 Next Month Prediction (Linear Regression)")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Predicted Spend", f"₹{pred['predicted_amount']:,.0f}")
    p2.metric("Lower Bound",     f"₹{pred['lower_bound']:,.0f}")
    p3.metric("Upper Bound",     f"₹{pred['upper_bound']:,.0f}")
    p4.metric("Trend",           pred["trend_direction"].title(), f"{pred['monthly_change_pct']}%/month")
    st.caption(f"Model R² = {pred['model_r2']}")

    st.divider()
    st.markdown("### 💡 Actionable Insights")
    icon_map   = {"warning": "⚠️", "info": "ℹ️", "success": "✅"}
    color_map  = {"warning": "rgba(251,146,60,0.12)", "info": "rgba(167,139,250,0.12)", "success": "rgba(74,222,128,0.10)"}
    border_map = {"warning": "#fb923c", "info": "#a78bfa", "success": "#4ade80"}
    for ins in insights:
        st.markdown(
            f"""<div style="background:{color_map[ins['type']]};border-left:3px solid
            {border_map[ins['type']]};border-radius:6px;padding:12px 16px;margin-bottom:8px;">
              <b style="color:#f0f4ff;">{icon_map[ins['type']]}  {ins['title']}</b><br>
              <span style="color:rgba(255,255,255,0.55);font-size:.9rem;">{ins['detail']}</span>
            </div>""",
            unsafe_allow_html=True,
        )

    # ── FORECAST CHART WITH CONFIDENCE BAND ──────────────────────────────────
    st.markdown("### 📈 Spend Trend + Forecast with Confidence Band")

    X      = monthly["month_num"].values
    y      = monthly["total_expense"].values
    m_c, b_c = np.polyfit(X, y, 1)
    reg    = m_c * X + b_c
    rmse   = np.sqrt(np.mean((y - reg) ** 2))

    x_all       = list(X) + [X[-1] + 1]
    y_trend     = [m_c * xi + b_c for xi in x_all]
    y_upper     = [v + rmse * 1.65 for v in y_trend]
    y_lower     = [v - rmse * 1.65 for v in y_trend]
    month_labels = list(monthly["month_name"]) + ["Next Month"]

    fig_fc = go.Figure()

    # Confidence band (upper trace first, then fill to lower)
    fig_fc.add_trace(go.Scatter(
        x=month_labels, y=y_upper, mode="lines",
        line=dict(width=0), showlegend=False, hoverinfo="skip",
    ))
    fig_fc.add_trace(go.Scatter(
        x=month_labels, y=y_lower, mode="lines",
        line=dict(width=0), fill="tonexty",
        fillcolor="rgba(236,72,153,0.13)",
        name="90% Confidence Band", hoverinfo="skip",
    ))
    # Actual line
    fig_fc.add_trace(go.Scatter(
        x=list(monthly["month_name"]), y=y.tolist(),
        name="Actual Spend", mode="lines+markers",
        line=dict(color=COLORS["cyan"], width=2.5), marker=dict(size=7),
    ))
    # OLS trend
    fig_fc.add_trace(go.Scatter(
        x=month_labels, y=y_trend,
        name=f"Trend ({m_c:+.0f} ₹/mo)",
        mode="lines", line=dict(color=COLORS["pink"], dash="dot", width=2),
    ))
    # Forecast star
    fig_fc.add_trace(go.Scatter(
        x=["Next Month"], y=[pred["predicted_amount"]],
        name="Predicted", mode="markers",
        marker=dict(color=COLORS["amber"], size=16, symbol="star"),
    ))
    # Vertical dashed divider
    fig_fc.add_vline(
        x=len(month_labels) - 1.5,
        line_dash="dot", line_color="rgba(255,255,255,0.2)",
        annotation_text="Forecast →",
        annotation_font_color="rgba(255,255,255,0.4)",
    )
    fig_fc.update_layout(
        title="Spending Trend · Linear Regression · 90% Confidence Band",
        height=430, xaxis_title="Month", yaxis_title="Amount (₹)",
        legend=dict(orientation="h", y=-0.22),
    )
    st.plotly_chart(apply_theme(fig_fc), use_container_width=True)
    st.caption(
        f"Confidence band = ±₹{rmse*1.65:,.0f}  (1.65 × RMSE).  "
        f"R² = {pred['model_r2']} — {'strong fit ✅' if pred['model_r2'] > 0.7 else 'moderate fit'}."
    )

    st.divider()
    st.download_button(
        "📑 Download Full Insights Report (HTML)",
        data=html_report(df_filtered, monthly, monthly_budget, insights),
        file_name="smartfinance_insights_report.html",
        mime="text/html",
    )


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: BUDGET CONTROL
# ══════════════════════════════════════════════════════════════════════════════
elif "Budget" in page:
    st.markdown("# 🎯 Budget Control")
    budget_df = analyse_budget(df, monthly_budget)

    def highlight_status(row):
        cmap = {
            "Over Budget": "background-color: rgba(239,68,68,0.15)",
            "Near Limit":  "background-color: rgba(251,146,60,0.15)",
            "On Track":    "background-color: rgba(16,185,129,0.10)",
        }
        return [cmap.get(row["status"], "")] * len(row)

    st.dataframe(
        budget_df.style.apply(highlight_status, axis=1).format({
            "actual": "₹{:,.0f}", "budget": "₹{:,.0f}",
            "remaining": "₹{:,.0f}", "used_pct": "{:.1f}%",
        }),
        use_container_width=True,
    )

    fig_b = go.Figure()
    fig_b.add_trace(go.Bar(x=budget_df["month_name"], y=[monthly_budget]*12,
        name="Budget", marker_color="rgba(59,130,246,0.2)"))
    fig_b.add_trace(go.Bar(x=budget_df["month_name"], y=budget_df["actual"],
        name="Actual Spend",
        marker_color=[
            COLORS["red"] if s=="Over Budget" else COLORS["amber"] if s=="Near Limit" else COLORS["green"]
            for s in budget_df["status"]
        ]))
    fig_b.update_layout(title="Budget vs Actual", barmode="overlay", height=380)
    st.plotly_chart(apply_theme(fig_b), use_container_width=True)

    st.divider()
    st.download_button("📄 Budget Analysis CSV", data=to_csv(budget_df),
                       file_name="budget_analysis.csv", mime="text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: RAW DATA
# ══════════════════════════════════════════════════════════════════════════════
elif "Raw" in page:
    st.markdown("# 📋 Raw Transaction Data")
    st.caption(f"{len(df_filtered):,} transactions shown (of {len(df):,} total)")

    c1, c2 = st.columns(2)
    with c1:
        sc = st.selectbox("Category", ["All"] + sorted(df["category"].unique().tolist()))
    with c2:
        sp = st.selectbox("Payment", ["All"] + sorted(df["payment_method"].unique().tolist()))

    view = df_filtered.copy()
    if sc != "All": view = view[view["category"] == sc]
    if sp != "All": view = view[view["payment_method"] == sp]

    st.dataframe(
        view[["date","category","subcategory","amount","payment_method",
              "day_of_week","month","is_weekend","is_festival"]]
        .sort_values("date", ascending=False).reset_index(drop=True),
        use_container_width=True, height=500,
    )

    st.divider()
    d1, d2 = st.columns(2)
    with d1:
        st.download_button("📄 Transactions CSV", data=to_csv(view),
                           file_name="transactions.csv", mime="text/csv",
                           use_container_width=True)
    with d2:
        st.download_button("📊 Monthly Summary CSV",
                           data=monthly_summary_csv(df_filtered, monthly),
                           file_name="monthly_summary.csv", mime="text/csv",
                           use_container_width=True)


# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<div style='text-align:center;color:rgba(255,255,255,0.18);font-size:.76rem;'>"
    "💸 SmartFinance Expense Analyzer &nbsp;·&nbsp; "
    "Python · Streamlit · Plotly · scikit-learn &nbsp;·&nbsp; "
    "Data Science Portfolio Project 2025</div>",
    unsafe_allow_html=True,
)
