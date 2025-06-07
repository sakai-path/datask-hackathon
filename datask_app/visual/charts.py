# =============================================================================
# charts.py - Seat & Monthly Usage Graphs
# -----------------------------------------------------------------------------
# - Seat usage counts (draw_usage_bar_chart)
# - Monthly usage counts per employee (draw_monthly_usage_chart)
# - JP font rendering support (for Windows/macOS/Linux)
# =============================================================================

import pandas as pd
import sqlalchemy as sa
import matplotlib
import matplotlib.pyplot as plt
import streamlit as st
import platform
from matplotlib.font_manager import FontProperties

# ▼ Platform-based Japanese font configuration (only for Streamlit rendering safety)
if platform.system() == "Windows":
    jp_font = FontProperties(fname="C:/Windows/Fonts/YuGothR.ttc")
    matplotlib.rc("font", family="Yu Gothic")
elif platform.system() == "Darwin":
    jp_font = FontProperties(fname="/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc")
    matplotlib.rc("font", family="Hiragino Maru Gothic Pro")
else:
    jp_font = FontProperties(fname="/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc")
    matplotlib.rc("font", family="Noto Sans CJK JP")

matplotlib.rcParams["axes.unicode_minus"] = False

# -------------------------------
# Seat usage counts
# -------------------------------
def get_seat_usage_counts(engine) -> pd.DataFrame:
    sql = """
    SELECT S.Label, COUNT(*) AS UsageCount
    FROM SeatLog L
    JOIN Seat S ON S.SeatId = L.SeatId
    GROUP BY S.Label
    ORDER BY S.Label
    """
    return pd.read_sql(sa.text(sql), engine)

def draw_usage_bar_chart(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(df["Label"], df["UsageCount"], color="skyblue", edgecolor="black")
    ax.set_title("Usage Count per Seat")
    ax.set_xlabel("Seat")
    ax.set_ylabel("Usage Count")
    ax.set_xticklabels(df["Label"], rotation=45, ha="right")
    st.pyplot(fig)

# -------------------------------
# Monthly usage per employee
# -------------------------------
def get_monthly_usage_by_employee(engine, emp_code: str) -> pd.DataFrame:
    sql = """
    SELECT 
        FORMAT(CheckIn, 'yyyy-MM') AS Month,
        COUNT(*) AS UsageCount
    FROM SeatLog
    WHERE EmpCode = :emp
    GROUP BY FORMAT(CheckIn, 'yyyy-MM')
    ORDER BY Month
    """
    with engine.begin() as conn:
        df = pd.read_sql(sa.text(sql), conn, params={"emp": emp_code})
    return df

def draw_monthly_usage_chart(df: pd.DataFrame, name: str = ""):
    if df.empty:
        st.warning("No data available.")
        return
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(df["Month"], df["UsageCount"], color="salmon", edgecolor="black")
    ax.set_title(f"Monthly Usage")
    ax.set_xlabel("Month")
    ax.set_ylabel("Usage Count")
    ax.set_xticks(range(len(df["Month"])))
    ax.set_xticklabels(df["Month"], rotation=45, ha="right")
    st.pyplot(fig)
