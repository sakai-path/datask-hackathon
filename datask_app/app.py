# =============================================================================
# app.py - Datask Streamlit アプリ（Function Calling + マップ/グラフ/SQL 対応）
# -----------------------------------------------------------------------------
# 自然言語の質問を Azure OpenAI Function Calling により自動分類。
# - マップ表示（座席状況）
# - 利用状況グラフ（社員別）
# - SELECT SQL 実行
# - 雑談（type: chat）など柔軟対応
# =============================================================================

import streamlit as st
import pandas as pd
from core.db import run_query, engine, load_table
from core.openai_sql import generate_semantic_sql
from visual.charts import get_monthly_usage_by_employee, draw_monthly_usage_chart
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
st.set_page_config(page_title="おしゃべりデータ", layout="centered")
st.title("💬 おしゃべりデータ")

if "query" not in st.session_state:
    st.session_state.query = ""
if "run" not in st.session_state:
    st.session_state.run = False

# ─────────────────────────────────────
# よくある質問ボタン
# ─────────────────────────────────────
with st.expander("💡 よくある質問（クリックで自動入力）", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("現在空いている席は？"):
            st.session_state.query = "現在空いている席は？"
    with col2:
        if st.button("田中さんの月別利用状況は？"):
            st.session_state.query = "田中さんの月別利用状況は？"
    with col3:
        if st.button("昨日の使用状況を教えて"):
            st.session_state.query = "昨日の使用状況を教えて"

# ─────────────────────────────────────
# 入力欄＆送信ボタン
# ─────────────────────────────────────
col1, col2 = st.columns([5, 1])
with col1:
    query = st.text_input("質問を入力してください", value=st.session_state.query, label_visibility="collapsed")
    st.session_state.query = query
with col2:
    if st.button("送信"):
        st.session_state.run = True

show_sql = st.checkbox("生成されたSQLを表示")
sql_container = st.empty()

# ─────────────────────────────────────
# メイン処理：AI応答処理
# ─────────────────────────────────────
if st.session_state.run and query.strip():
    st.session_state.run = False
    result = generate_semantic_sql(query)

    if result["type"] == "seatmap":
        labels = get_seat_labels(engine)
        if result.get("detail") == "with_names":
            used_dict = get_used_label_name_dict(engine)
            draw_auto_seat_map_with_names(labels, used_dict)
        else:
            used = get_used_labels(engine)
            draw_auto_seat_map(labels, used)
        st.success("✅ 座席マップを表示しました。")
        if show_sql:
            with sql_container:
                st.code(result.get("sql", "-- AI判定：座席マップ表示（SQLなし）"), language="sql")

    elif result["type"] == "chart":
        df = get_monthly_usage_by_employee(engine, result["emp_code"])
        if df.empty:
            st.warning("データがありません。")
        else:
            draw_monthly_usage_chart(df, name=result.get("name", ""))

    elif result["type"] == "sql":
        try:
            df = run_query(result["sql"])
            st.dataframe(df, use_container_width=True)
            if show_sql:
                with sql_container:
                    st.code(result["sql"], language="sql")
        except Exception as e:
            st.error(f"SQL実行エラー: {e}")

    elif result["type"] == "chat":
        st.markdown("### 💬 AIの応答")
        st.write(result["message"])

    elif result["type"] == "error":
        st.warning(result["message"])

# ─────────────────────────────────────
# サイドバー：テーブル参照＆CSVエクスポート
# ─────────────────────────────────────
with st.sidebar.expander("📂 データベース参照（Seat / Employee / SeatLog）", expanded=False):
    table = st.selectbox("表示するテーブル", ["Seat", "Employee", "SeatLog"])
    limit = st.slider("表示件数", 10, 5000, 100, 10)
    if st.button("読み込み"):
        df = load_table(table, limit)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(f"{table} をCSVで保存", csv, f"{table}.csv", mime="text/csv")
