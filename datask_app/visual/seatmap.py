# =============================================================================
# seatmap.py - Label順に座席を4列ごとに並べて描画（色調整済み）
# -----------------------------------------------------------------------------
# 空席は薄いブルー、使用中は薄いピンク、枠線なし。
# =============================================================================

import matplotlib.pyplot as plt
import pandas as pd
import sqlalchemy as sa
import streamlit as st

def get_seat_labels(engine) -> list[str]:
    """すべての Seat.Label を昇順に取得"""
    sql = "SELECT Label FROM Seat ORDER BY Label"
    df = pd.read_sql(sa.text(sql), engine)
    return df["Label"].tolist()

def get_used_labels(engine) -> list[str]:
    """現在使用中（CheckOut が NULL）の Seat.Label を取得"""
    sql = """
    SELECT S.Label FROM SeatLog L
    JOIN Seat S ON S.SeatId = L.SeatId
    WHERE L.CheckIn <= GETDATE() AND L.CheckOut IS NULL
    """
    df = pd.read_sql(sa.text(sql), engine)
    return df["Label"].tolist()

def group_labels(labels: list[str], columns: int = 4) -> list[list[str]]:
    """4列ごとに分割（2次元リストに変換）"""
    return [labels[i:i + columns] for i in range(0, len(labels), columns)]

def draw_auto_seat_map(labels: list[str], used: list[str], columns: int = 4):
    """固定列でラベル順に並べて座席を描画（色調整済み）"""
    layout = group_labels(labels, columns)
    fig, ax = plt.subplots(figsize=(columns + 1, len(layout)))

    for y, row in enumerate(layout):
        for x, label in enumerate(row):
            color = "lightpink" if label in used else "lightblue"
            circle = plt.Circle((x, -y), 0.3, color=color)  # 枠線なし
            ax.add_patch(circle)
            ax.text(x, -y, label, ha="center", va="center", color="black", fontsize=9)

    ax.set_xlim(-0.5, columns)
    ax.set_ylim(-len(layout), 0.5)
    ax.set_aspect("equal")
    ax.axis("off")
    st.pyplot(fig)
