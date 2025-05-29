# =============================================================================
# Datask - Streamlitアプリ起動用メインファイル
# -----------------------------------------------------------------------------
# このファイルはStreamlitアプリのエントリーポイントです。
# ユーザーインターフェース（UI）を構築し、他のモジュールの機能を呼び出します。
#
# 主な機能：
# - テーブルのデータ表示
# - 日本語質問からSQL文の生成（Azure OpenAI）
# - 生成されたSQL文の実行と結果表示
# - 座席マップの表示（Label順 × 4列）
# =============================================================================

import streamlit as st
from core.db import list_tables, load_table, run_query, engine
from core.openai_sql import generate_sql
from visual.seatmap import get_seat_labels, get_used_labels, draw_auto_seat_map

st.set_page_config(page_title="Seat DB Viewer", page_icon="◆", layout="centered")
st.title("おしゃべりデータ – フリー席検索")

# テーブル表示
with st.expander("テーブル表示", expanded=True):
    tbl = st.selectbox("テーブル", list_tables())
    lim = st.slider("行数", 10, 500, 100, 10)
    if st.button("読み込み"):
        st.dataframe(load_table(tbl, lim), use_container_width=True)

# 自然言語 → SQL
with st.expander("自然言語 ➜ SQL 生成・実行", expanded=True):
    q = st.text_input("質問を入力（例: “現在空いている席は？”）")
    col_gen, col_exec = st.columns(2)

    if col_gen.button("SQL 生成", use_container_width=True):
        sql = generate_sql(q)
        st.session_state["sql"] = sql
        st.code(sql, language="sql")

    if col_exec.button("SQL 実行", use_container_width=True):
        sql = st.session_state.get("sql")
        if sql and sql.strip().lower().startswith("select"):
            st.dataframe(run_query(sql), use_container_width=True)

# 座席マップ表示（4列固定）
st.subheader("座席マップの表示（4列固定）")
if st.button("座席マップを表示"):
    all_labels = get_seat_labels(engine)
    used_labels = get_used_labels(engine)
    draw_auto_seat_map(all_labels, used_labels, columns=5)

from visual.charts import get_seat_usage_counts, draw_usage_bar_chart

st.subheader("座席ごとの利用回数（棒グラフ）")
if st.button("利用回数グラフを表示"):
    df = get_seat_usage_counts(engine)
    draw_usage_bar_chart(df)
