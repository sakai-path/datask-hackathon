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
