# =============================================================================
# app.py - Datask Streamlit アプリ（座席マップ優先表示＋よくある質問）
# -----------------------------------------------------------------------------
# 自然言語の質問をAIで判定し、SQL実行・グラフ描画・座席マップ表示を自動選択。
# UI上部にマップ・グラフ・表それぞれの例となる「よくある質問」ボタンを追加。
# =============================================================================

import streamlit as st
import pandas as pd
from core.db import run_query, engine, load_table
from core.openai_sql import generate_semantic_sql
from visual.seatmap import (
    get_seat_labels,
    get_used_labels,
    get_used_label_name_dict,
    draw_auto_seat_map,
    draw_auto_seat_map_with_names,
)

# ─────────────────────────────────────
# UI 初期設定
# ─────────────────────────────────────
st.set_page_config(page_title="Dataks", layout="centered")
st.title("フリーアドレス検索")

if "query" not in st.session_state:
    st.session_state.query = ""
if "run" not in st.session_state:
    st.session_state.run = False

# ─────────────────────────────────────
# よくある質問（マップ・グラフ・表）
# ─────────────────────────────────────
with st.expander("💡 よくある質問（クリックで自動入力）", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("現在空いている席は？"):
            st.session_state.query = "現在空いている席は？"
            st.session_state.run = True
    with col2:
        if st.button("田中さんの月別利用状況は？"):
            st.session_state.query = "田中さんの月別利用状況は？"
            st.session_state.run = True
    with col3:
        if st.button("昨日の使用状況を教えて"):
            st.session_state.query = "昨日の使用状況を教えて"
            st.session_state.run = True

# ─────────────────────────────────────
# 入力フォーム
# ─────────────────────────────────────
col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input("質問", value=st.session_state.query, placeholder="例：現在空いている席は？", label_visibility="collapsed")
    st.session_state.query = query
with col2:
    if st.button("送信"):
        st.session_state.run = True

show_sql = st.checkbox("生成されたSQLを表示")
sql_container = st.empty()

# ─────────────────────────────────────
# メイン処理：マップ表示優先で処理確認
# ─────────────────────────────────────
if st.session_state.run and query.strip():
    st.session_state.run = False
    result = generate_semantic_sql(query)
    st.json(result)  # ← デバッグ表示を一時有効化

    if result["type"] == "seatmap":
        labels = get_seat_labels(engine)
        if result.get("detail") == "with_names":
            used_dict = get_used_label_name_dict(engine)
            draw_auto_seat_map_with_names(labels, used_dict)
        else:
            used = get_used_labels(engine)
            draw_auto_seat_map(labels, used)
        st.success("✅ 座席マップを表示しました。")

    elif result["type"] == "error":
        st.warning(result["message"])

# ─────────────────────────────────────
# サイドバー：DBテーブル閲覧とCSV出力
# ─────────────────────────────────────
with st.sidebar.expander("◆データベース参照（Seat / Employee / SeatLog）", expanded=False):
    table = st.selectbox("表示するテーブルを選択", ["Seat", "Employee", "SeatLog"])
    limit = st.slider("表示件数", 10, 5000, 100, 10)

    if st.button("読み込み"):
        df = load_table(table, limit)
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label=f"{table} をCSVで保存",
            data=csv,
            file_name=f"{table}.csv",
            mime="text/csv"
        )
