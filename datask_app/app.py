
# =============================================================================
# Datask - シンプルQA専用アプリ画面
# -----------------------------------------------------------------------------
# 質問入力欄 → 自動でSQL生成 → 実行し回答を表示（SQLは任意表示）
# =============================================================================

import streamlit as st
from core.db import run_query, engine
from core.openai_sql import generate_sql
from visual.charts import show_usage_chart_by_emp

st.set_page_config(page_title="おしゃべりデータ - QA", page_icon="🤖", layout="centered")

st.markdown("""
<style>
    .main {
        background-color: #f9f9f9;
    }
    input {
        background-color: #ffffff !important;
        border-radius: 10px !important;
        padding: 10px;
        border: 1px solid #ddd !important;
    }
    .stTextInput>div>div>input {
        color: #333 !important;
    }
    .stButton>button {
        border-radius: 10px;
        padding: 0.5em 1.5em;
        background-color: #4a90e2;
        color: white;
        border: none;
    }
    .stButton>button:hover {
        background-color: #3c7dc3;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔍 質問を入力してください")

query = st.text_input("例: “現在空いている席は？”", key="query_input")

if query:
    sql = generate_sql(query)
    if sql.startswith("#CHART:"):
        emp_code = sql.split(":", 1)[1].strip().rstrip(":")
        if emp_code:
            show_usage_chart_by_emp(emp_code, engine)
        else:
            st.warning("社員コードが見つかりませんでした。")
    elif not sql.strip().lower().startswith("select"):
        st.warning("ちょっと意味がわかりません")
    else:
        try:
            df = run_query(sql)
            if df.empty:
                st.info("該当データは見つかりませんでした。")
            else:
                st.dataframe(df, use_container_width=True)

            with st.expander("📄 実行されたSQLを表示"):
                st.code(sql, language="sql")
        except Exception as e:
            st.error(f"SQL実行エラー: {e}")
