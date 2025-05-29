# =============================================================================
# seatmap.py - 座席マップ（円で空席/使用中を表示）
# -----------------------------------------------------------------------------
# このモジュールでは、固定レイアウトの座席一覧を丸で表示します。
# 使用中の席は赤、空席は緑で描画されます。
# =============================================================================

import matplotlib.pyplot as plt
import pandas as pd
import sqlalchemy as sa
import streamlit as st

# 固定レイアウト（必要に応じて並び変更）
SEAT_LAYOUT = [
    ["A-01", "A-02", "A-03", "A-04", "A-05"],
    ["A-06", "A-07", "A-08", "A-09", "A-10"]
]

def get_used_seats(engine) -> list[str]:
    """現在使用中の席のLabelを取得"""
    sql = """
    SELECT DISTINCT Seat.Label
    FROM SeatLog
    JOIN Seat ON Seat.SeatId = SeatLog.SeatId
    WHERE CheckIn <= GETDATE() AND CheckOut IS NULL
    """
    df = pd.read_sql(sa.text(sql), engine)
    return df["Label"].tolist()

def draw_seat_map(used_labels: list[str]):
    """固定レイアウトに沿って座席を円で描画"""
    fig, ax = plt.subplots(figsize=(6, 3))

    for y, row in enumerate(SEAT_LAYOUT):
        for x, label in enumerate(row):
            is_used = label in used_labels
            color = "red" if is_used else "green"
            circle = plt.Circle((x, -y), 0.4, color=color, ec="black")
            ax.add_patch(circle)
            ax.text(x, -y, label, ha="center", va="center", color="white", fontsize=9)

    ax.set_xlim(-0.5, len(SEAT_LAYOUT[0]))
    ax.set_ylim(-len(SEAT_LAYOUT), 0.5)
    ax.set_aspect("equal")
    ax.axis("off")
    st.pyplot(fig)
