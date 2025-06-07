# =============================================================================
# app.py - Datask Streamlit アプリ（AIによるSQL生成＋マップ・グラフ対応）
# -----------------------------------------------------------------------------
# 質問入力に対して Function Calling 経由でマップ/グラフ/SQL/雑談を自動判定
# よくある質問ボタン付き
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

# ───────────────────────────────
# 初期化
# ───────────────────────────────
st.set_page_config(page_title="フリーアドレス検索", layout="centered")
st.title("💼 フリーアドレス検索")

if "query" not in st.session_state:
    st.session_state.query = ""
if "run" not in st.session_state:
    st.session_state.run = False

# ───────────────────────────────
# よくある質問ボタン
# ───────────────────────────────
btn_style = "margin-right: 1rem; margin-bottom: 0.5rem;"
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("座席マップを見せて", use_container_width=True):
        st.session_state.query = "座席マップを見せて"
        st.session_state.run = True
with col2:
    if st.button("田中さんの利用状況", use_container_width=True):
        st.session_state.query = "田中さんの利用状況"
        st.session_state.run = True
with col3:
    if st.button("なにが聞けますか", use_container_width=True):
        st.session_state.query = "なにが聞けますか"
        st.session_state.run = True

# ──────────────────────────────
# 入力欄と送信ボタン + 「なにが聞けますか？」ボタン
# ──────────────────────────────
q# テキスト入力欄（上部）
query = st.text_input("質問を入力してください", value=st.session_state.query, placeholder="例：現在空いている席は？")
st.session_state.query = query

# 送信ボタン + なにが聞けますか？ を近くに横並びで表示
col1, spacer, col2 = st.columns([1, 0.1, 2])

with col1:
    if st.button("送信"):
        st.session_state.run = True

with col2:
    if st.button("なにが聞ける？"):
        st.session_state.query = "なにが聞ける？"
        st.session_state.run = True

# ───────────────────────────────
# 実行処理
# ───────────────────────────────
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
        if show_sql:
            sql_container.code("-- AI判定：座席マップ呼び出し", language="sql")
        st.success("✅ 座席マップを表示しました。")

    elif result["type"] == "chart":
        df = get_monthly_usage_by_employee(engine, result["emp_code"])
        draw_monthly_usage_chart(df, name=result.get("name", ""))
        if df.empty:
            st.warning("データがありません。")
        else:
            st.success(f"✅ {result.get('name', '社員')} さんのグラフを表示しました。")

    elif result["type"] == "sql":
        try:
            df = run_query(result["sql"])
            st.dataframe(df, use_container_width=True)
            if show_sql:
                sql_container.code(result["sql"], language="sql")
        except Exception as e:
            st.error(f"SQL実行エラー: {e}")

    elif result["type"] == "chat":
        st.subheader("📝 AIの応答")
        st.markdown(result["message"])

    elif result["type"] == "error":
        st.warning(result["message"])

# ───────────────────────────────
# サイドバー：DB参照
# ───────────────────────────────
with st.sidebar.expander("◆データベース参照（Seat / Employee / SeatLog）", expanded=False):
    table = st.selectbox("表示テーブル", ["Seat", "Employee", "SeatLog"])
    limit = st.slider("表示件数", 10, 1000, 100, 10)
    if st.button("読み込み"):
        df = load_table(table, limit)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(f"{table}.csv を保存", csv, file_name=f"{table}.csv", mime="text/csv")
