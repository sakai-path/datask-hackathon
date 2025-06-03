# =============================================================================
# charts.py - 座席利用状況 & 社員の月別利用回数の棒グラフ表示
# -----------------------------------------------------------------------------
# このモジュールでは、SeatLogを集計し、以下を matplotlib で描画：
# - 座席ごとの利用回数
# - 社員ごとの月別利用回数
# =============================================================================

import pandas as pd
import sqlalchemy as sa
import matplotlib.pyplot as plt
import streamlit as st
import platform
import matplotlib

# -------------------------------
# 1. 座席ごとの利用回数
# -------------------------------
def get_seat_usage_counts(engine) -> pd.DataFrame:
    """Seatごとの利用回数を取得"""
    sql = """
    SELECT S.Label, COUNT(*) AS UsageCount
    FROM SeatLog L
    JOIN Seat S ON S.SeatId = L.SeatId
    GROUP BY S.Label
    ORDER BY S.Label
    """
    return pd.read_sql(sa.text(sql), engine)

def draw_usage_bar_chart(df: pd.DataFrame):
    """座席ごとの利用回数を棒グラフで描画"""
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(df["Label"], df["UsageCount"], color="skyblue", edgecolor="black")
    ax.set_title("座席ごとの利用回数")
    ax.set_xlabel("Seat")
    ax.set_ylabel("利用回数")
    ax.set_xticklabels(df["Label"], rotation=45, ha="right")
    st.pyplot(fig)

# -------------------------------
# 2. 社員ごとの月別利用回数
# -------------------------------
def get_monthly_usage_by_employee(engine, emp_code: str) -> pd.DataFrame:
    """指定された社員の月別利用回数を取得"""
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
    """月別利用回数を棒グラフで描画"""
    if df.empty:
        st.warning("データがありません。")
        return
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(df["Month"], df["UsageCount"], color="salmon", edgecolor="black")
    ax.set_title(f"{name} の月別利用回数" if name else "月別利用回数")
    ax.set_xlabel("月")
    ax.set_ylabel("利用回数")
    ax.set_xticks(range(len(df["Month"])))
    ax.set_xticklabels(df["Month"], rotation=45, ha="right")
    st.pyplot(fig)

# ▼ OSごとに日本語フォントを設定
if platform.system() == "Windows":
    matplotlib.rc("font", family="Yu Gothic")
elif platform.system() == "Darwin":  # macOS
    matplotlib.rc("font", family="Hiragino Maru Gothic Pro")
else:
    matplotlib.rc("font", family="IPAPGothic")  # Linux向け (IPAフォントなど)

matplotlib.rcParams["axes.unicode_minus"] = False  # マイナス記号対策
