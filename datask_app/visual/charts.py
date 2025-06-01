# =============================================================================
# charts.py - 座席利用状況の棒グラフ表示
# -----------------------------------------------------------------------------
# このモジュールでは、SeatLogを集計し、座席ごとの利用回数を
# matplotlib で棒グラフとして表示する機能を提供します。
# =============================================================================

import pandas as pd
import sqlalchemy as sa
import matplotlib.pyplot as plt
import streamlit as st

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

def show_usage_chart_by_emp(emp_code: str, engine: sa.Engine):
    """社員別の月別利用回数を棒グラフで表示"""
    query = """
        SELECT
            EmpCode,
            FORMAT(CheckIn, 'yyyy-MM') AS Month,
            COUNT(*) AS Count
        FROM SeatLog
        WHERE EmpCode = :emp
        GROUP BY EmpCode, FORMAT(CheckIn, 'yyyy-MM')
        ORDER BY Month
    """
    df = pd.read_sql(sa.text(query), engine, params={"emp": emp_code})

    if df.empty:
        st.warning(f"{emp_code} の利用履歴が見つかりませんでした。")
        return

    plt.figure(figsize=(6, 4))
    plt.bar(df["Month"], df["Count"], color="green", edgecolor="black")
    plt.title(f"{emp_code} の月別利用回数")
    plt.xlabel("月")
    plt.ylabel("回数")
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(plt)
