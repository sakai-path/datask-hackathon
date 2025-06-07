# =============================================================================
# app.py - Datask Streamlit アプリ（自然言語 → Function Calling対応）
# -----------------------------------------------------------------------------
# よくある質問ボタン（即実行）＋ テキスト入力（Enterキー or ボタン送信）
# Function Calling でマップ・グラフ・SQL表示・雑談対応
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
# UI初期設定
# ─────────────────────────────────────
st.set_page_config(page_title="フリーアドレス検索", layout="centered")
st.title("フリーアドレス検索")

if "query" not in st.session_state:
    st.session_state.query = ""
if "run" not in st.session_state:
    st.session_state.run = False

# ─────────────────────────────────────
# よくある質問（常時表示）＆即実行
# ─────────────────────────────────────
# よくある質問：等間隔で横並びに配置
cols = st.columns([1, 1, 1])

buttons = [
    ("現在空いている席は？", "現在空いている席は？"),
    ("なにが聞ける？", "なにが聞ける？"),
    ("田中さんの５月利用状況", "田中さんの５月利用状況")
]

for col, (label, query_text) in zip(cols, buttons):
    with col:
        if st.button(label):
            st.session_state.query = query_text
            st.session_state.run = True

# ─────────────────────────────────────
# 質問入力欄（Enterまたは送信ボタンで実行）
# ─────────────────────────────────────
with st.form("query_form", clear_on_submit=False):
    query = st.text_input("質問を入力してください", value=st.session_state.query)
    submitted = st.form_submit_button("送信")
    if submitted:
        st.session_state.query = query
        st.session_state.run = True

show_sql = st.checkbox("生成されたSQLを表示")
sql_container = st.empty()

# ─────────────────────────────────────
# メイン処理：Function Calling による出力種別分岐
# ─────────────────────────────────────
if st.session_state.run and st.session_state.query.strip():
    st.session_state.run = False
    query = st.session_state.query
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
            sql_container.code("-- AI判定: 座席マップ呼び出し", language="sql")

    elif result["type"] == "chart":
        df = get_monthly_usage_by_employee(engine, result["emp_code"])
        draw_monthly_usage_chart(df, name=result.get("name", ""))
        st.success(f"✅ {result.get('name', '')} さんのグラフを表示しました。")

    elif result["type"] == "sql":
        try:
            df = run_query(result["sql"])
            st.dataframe(df, use_container_width=True)
            if show_sql:
                sql_container.code(result["sql"], language="sql")
        except Exception as e:
            st.error(f"SQL実行エラー: {e}")

    elif result["type"] == "chat":
        st.markdown("### 📝 AIの応答")
        st.write(result["message"])

    elif result["type"] == "error":
        st.warning(result["message"])

# ─────────────────────────────────────
# サイドバー：データベースブラウズ
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
