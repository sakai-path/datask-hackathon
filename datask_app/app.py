# =============================================================================
# app.py - Datask Streamlit アプリ（AIによる動的出力＋DBブラウズ）
# -----------------------------------------------------------------------------
# 自然言語の質問をAIで判定し、SQL実行・グラフ描画・座席マップ表示を自動選択。
# サイドバーではテーブルの任意参照やCSV出力も可能。
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
st.title("フリーアドレス")

st.markdown("""
<div style='
    background-color: #fff9db;
    padding: 0.75rem 1rem;
    border-radius: 1rem;
    margin-top: 0.5rem;
    margin-bottom: 1.5rem;
    display: inline-block;
    font-size: 0.95rem;
    color: #333;
'>
    💡 例：『現在空いている席は？』
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input("質問", placeholder="田中さんの利用状況をグラフで見せて", label_visibility="collapsed")
with col2:
    run_button = st.button("送信")

# よくある質問
with st.expander("💡 よくある質問をクリックで入力", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("現在空いている席は？"):
            query = "現在空いている席は？"
            run_button = True
    with col2:
        if st.button("田中さんの月別利用状況は？"):
            query = "田中さんの月別利用状況は？"
            run_button = True
    with col3:
        if st.button("昨日の使用状況を教えて"):
            query = "昨日の使用状況を教えて"
            run_button = True

show_sql = st.checkbox("生成されたSQLを表示")
sql_container = st.empty()

# ─────────────────────────────────────
# メイン処理：AIによる出力種別の判定と動的表示
# ─────────────────────────────────────
if run_button and query.strip():
    result = generate_semantic_sql(query)

    if result["type"] == "seatmap":
        labels = get_seat_labels(engine)
        if result.get("detail") == "with_names":
            used_dict = get_used_label_name_dict(engine)
            draw_auto_seat_map_with_names(labels, used_dict)
        else:
            used = get_used_labels(engine)
            draw_auto_seat_map(labels, used)
        st.info("現在の座席利用状況を表示しました。")

    elif result["type"] == "sql":
        try:
            df = run_query(result["sql"])
            st.dataframe(df, use_container_width=True)
            if show_sql:
                with sql_container.expander("🔍 生成されたSQL"):
                    st.code(result["sql"], language="sql")
        except Exception as e:
            st.error(f"SQL実行エラー: {e}")

    elif result["type"] == "chart":
        df = get_monthly_usage_by_employee(engine, result["emp_code"])
        draw_monthly_usage_chart(df, name=result.get("name", ""))

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

