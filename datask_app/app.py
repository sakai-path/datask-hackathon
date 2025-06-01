# =============================================================================
# app.py - Datask スタイリッシュ質問 UI メイン
# -----------------------------------------------------------------------------
# - 自然言語の質問を入力すると、自動でSQL生成・実行・表示
# - 回答は表形式またはグラフ表示（Function Calling による指示）
# - 実行されたSQLは「▼ SQLを表示」で確認可能
# =============================================================================

import streamlit as st
from core.db import run_query, engine
from core.openai_sql import generate_sql
from visual.charts import get_monthly_usage_by_employee, draw_monthly_usage_chart
from core.employee import get_empcode_by_name

from visual.charts import (
    get_monthly_usage_by_employee,
    draw_monthly_usage_chart
)

# -------------------------------
# ページ設定 & スタイル
# -------------------------------
st.set_page_config(page_title="おしゃべりデータ", page_icon="🔍", layout="centered")

st.markdown("""
    <style>
    .big-input > div > input {
        font-size: 1.1rem !important;
        padding: 0.75em;
        border-radius: 0.5em;
        background-color: #f8f9fa;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# タイトル・入力エリア
# -------------------------------
st.markdown("## 🔍 質問を入力してください")
user_input = st.text_input(
    "例: “E10001 の利用履歴をグラフで見せて”",
    placeholder="自然な言葉で質問できます",
    label_visibility="collapsed",
    key="query_input",
    help="座席や利用履歴など、自由に質問できます",
)

# -------------------------------
# SQL生成 & 実行
# -------------------------------
if user_input.strip():
    sql = generate_sql(user_input)
    st.session_state["last_sql"] = sql

    # ▼ Function Calling 成果物としてのプレースホルダ判定
    if sql.startswith("#CHART:"):
        emp_code = sql.removeprefix("#CHART:").strip()
        df = get_monthly_usage_by_employee(engine, emp_code)
        draw_monthly_usage_chart(df, name=emp_code)
    elif sql.lower().startswith("select"):
        df = run_query(sql)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("ちょっと意味がわかりませんでした。")

# ─────────────────────────────────────────────
# 氏名から社員の月別利用回数グラフを表示
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("### 氏名から社員の月別利用回数を表示")

name_input = st.text_input("社員名を入力（例：田中）")

if st.button("利用回数グラフを表示"):
    if not name_input.strip():
        st.warning("氏名を入力してください。")
    else:
        emp_code = get_empcode_by_name(name_input)
        if emp_code:
            df = get_monthly_usage_by_employee(engine, emp_code)
            draw_monthly_usage_chart(df, name_input)
        else:
            st.error("該当する社員が見つかりませんでした。")

# -------------------------------
# SQL確認（折りたたみ）
# -------------------------------
if "last_sql" in st.session_state:
    with st.expander("▼ SQLを表示"):
        st.code(st.session_state["last_sql"], language="sql")


