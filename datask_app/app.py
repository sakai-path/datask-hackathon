# =============================================================================
# app.py - Datask Streamlit アプリ（SQL生成中心構成）
# -----------------------------------------------------------------------------
# 自然言語での質問に対して、AIがSELECT文を出力し、SQLを実行・表示します。
# グラフや座席マップの判定はSQLの構造に応じて処理を分岐させます（準備中）。
# =============================================================================

import streamlit as st
import pandas as pd
from core.db import run_query, engine, load_table
from core.openai_sql import generate_semantic_sql

# ─────────────────────────────────────
# UI 初期設定
# ─────────────────────────────────────
st.set_page_config(page_title="Datask", layout="centered")
st.title("フリーアドレス検索（SQL AI）")

# よくある質問を先頭に
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

# 入力欄
if "query" not in st.session_state:
    st.session_state.query = ""
if "run" not in st.session_state:
    st.session_state.run = False

col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input("質問", value=st.session_state.query, placeholder="例：現在空いている席は？", label_visibility="collapsed")
    st.session_state.query = query
with col2:
    if st.button("送信"):
        st.session_state.run = True

show_sql = st.checkbox("生成されたSQLを表示")
sql_container = st.empty()

result = generate_semantic_sql(query)

# デバッグ出力（常時表示でも可）
st.markdown("### 🔍 AIの出力デバッグ表示")
st.json(result)

# SQLがあれば表示（形式的なSELECT文でなくても）
if "sql" in result:
    st.markdown("### 🔍 AIの返した SQL 部分（そのまま表示）")
    st.code(result["sql"], language="sql")

# ─────────────────────────────────────
# メイン処理：AIでSQLを生成し、実行または通知
# ─────────────────────────────────────
if st.session_state.run and query.strip():
    st.session_state.run = False
    result = generate_semantic_sql(query)

    if result["type"] == "sql":
        try:
            df = run_query(result["sql"])
            st.dataframe(df, use_container_width=True)
            if show_sql:
                with sql_container:
                    st.code(result["sql"], language="sql")
        except Exception as e:
            st.error(f"SQL実行エラー: {e}")
    else:
        st.warning(result.get("message", "AIが理解できませんでした。"))

# ─────────────────────────────────────
# サイドバー：テーブル参照とCSV出力
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
