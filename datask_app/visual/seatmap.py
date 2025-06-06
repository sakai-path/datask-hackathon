# =============================================================================
# seatmap.py - 座席マップ描画モジュール（Datask アプリ用）
# -----------------------------------------------------------------------------
# ・Seat.Label を使用して座席を4列ごとに配置し、円で可視化
# ・空席は薄いブルー、使用中は薄いピンクで描画
# ・使用中の席には社員名を表示、空席には席番号を表示
# -----------------------------------------------------------------------------
# 主な関数：
# - get_seat_labels()：全席のラベルを昇順取得
# - get_used_labels()：使用中の席ラベルを取得（従来版）
# - get_used_label_name_dict()：使用中の席ラベル→社員名マッピング
# - draw_auto_seat_map()：ラベルのみのマップ描画
# - draw_auto_seat_map_with_names()：名前付きのマップ描画
# =============================================================================

import matplotlib.pyplot as plt
import pandas as pd
import sqlalchemy as sa
import streamlit as st
from matplotlib.font_manager import FontProperties
import os
from matplotlib.font_manager import FontProperties

# フォントファイルへの絶対パスを取得
font_path = os.path.join(os.path.dirname(__file__), "..", "fonts", "ipaexg.ttf")
font_path = os.path.abspath(font_path)

if os.path.exists(font_path):
    jp_font = FontProperties(fname=font_path)
else:
    jp_font = None
    
def get_seat_labels(engine) -> list[str]:
    """すべての Seat.Label を昇順に取得"""
    sql = "SELECT Label FROM Seat ORDER BY Label"
    df = pd.read_sql(sa.text(sql), engine)
    return df["Label"].tolist()


def get_used_labels(engine) -> list[str]:
    """現在使用中（CheckOut が NULL）の Seat.Label を取得"""
    sql = """
    SELECT S.Label
    FROM SeatLog L
    JOIN Seat S ON S.SeatId = L.SeatId
    WHERE L.CheckIn <= GETDATE() AND L.CheckOut IS NULL
    """
    df = pd.read_sql(sa.text(sql), engine)
    return df["Label"].tolist()


def get_used_label_name_dict(engine) -> dict[str, str]:
    """
    使用中の席に座っている社員の名前を取得（Label → Name の辞書）
    """
    sql = """
    SELECT S.Label, E.Name
    FROM SeatLog L
    JOIN Seat S ON S.SeatId = L.SeatId
    JOIN Employee E ON E.EmpCode = L.EmpCode
    WHERE L.CheckIn <= GETDATE() AND L.CheckOut IS NULL
    """
    df = pd.read_sql(sa.text(sql), engine)
    return dict(zip(df["Label"], df["Name"]))


def group_labels(labels: list[str], columns: int = 4) -> list[list[str]]:
    """ラベルを列数ごとに分割（2次元リスト）"""
    return [labels[i:i + columns] for i in range(0, len(labels), columns)]


def draw_auto_seat_map(labels: list[str], used: list[str], columns: int = 4):
    """
    使用中かどうかに応じて色分けして座席マップを描画（ラベル表示）
    """
    layout = group_labels(labels, columns)
    fig, ax = plt.subplots(figsize=(columns + 1, len(layout)))

    for y, row in enumerate(layout):
    for x, label in enumerate(row):
        color = "lightpink" if label in used else "lightblue"
        circle = plt.Circle((x, -y), 0.3, color=color)
        ax.add_patch(circle)
        display_text = label  # ← これを追加
        if jp_font:
            ax.text(x, -y, display_text, ha="center", va="center", fontsize=9, color="black", fontproperties=jp_font)
        else:
            ax.text(x, -y, display_text, ha="center", va="center", fontsize=9, color="black")
    
    ax.set_xlim(-0.5, columns)
    ax.set_ylim(-len(layout), 0.5)
    ax.set_aspect("equal")
    ax.axis("off")
    st.pyplot(fig)


def draw_auto_seat_map_with_names(labels: list[str], used_label_to_name: dict[str, str], columns: int = 4):
    """
    使用中：社員名、空席：席番号を表示した座席マップを描画
    """
    layout = group_labels(labels, columns)
    fig, ax = plt.subplots(figsize=(columns + 1, len(layout)))

    for y, row in enumerate(layout):
        for x, label in enumerate(row):
            is_used = label in used_label_to_name
            color = "lightpink" if is_used else "lightblue"
            text = used_label_to_name[label] if is_used else label
            circle = plt.Circle((x, -y), 0.3, color=color)
            ax.add_patch(circle)
            if jp_font:
                ax.text(x, -y, text, ha="center", va="center", fontsize=9, color="black", fontproperties=jp_font)
            else:
                ax.text(x, -y, text, ha="center", va="center", fontsize=9, color="black")
    
    ax.set_xlim(-0.5, columns)
    ax.set_ylim(-len(layout), 0.5)
    ax.set_aspect("equal")
    ax.axis("off")
    st.pyplot(fig)
