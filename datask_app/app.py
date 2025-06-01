# =============================================================================
# app.py - Datask Streamlit アプリ（自然言語から動的表示）
# -----------------------------------------------------------------------------
# このアプリは、ユーザーの自然言語の質問から、Azure OpenAI を通じて
# SQL 実行またはグラフ描画などを自動判定・表示します。
# 質問入力欄は1つだけ。表示形式は AI が判断します。
# =============================================================================

import streamlit as st
from core.db import run_query, engine
from core.openai_sql import generate_semantic_sql
from visual.charts import get_monthly_usage_by_employee, draw_monthly_usage_chart

# UIの設定
st.set_page_config(page_title="おしゃべりデータ", layout="centered")
st.title("💬 おしゃべりデータ")

# シンプルなテキスト入力欄（スタイル調整）
query = st.text_input("知りたいことを聞いてください", placeholder="例：田中さんのグラフを見せて")

# SQL 表示用の展開領域（後で中身を詰める）
sql_container = st.empty()

if query.strip():
    result = generate_semantic_sql(query)

    if result["type"] == "sql":
        try:
            df = run_query(result["sql"])
            st.dataframe(df, use_container_width=True)
            with sql_container.expander("🔍 生成されたSQLを見る"):
                st.code(result["sql"], language="sql")
        except Exception as e:
            st.error(f"SQL実行エラー: {e}")

    elif result["type"] == "chart":
        df = get_monthly_usage_by_employee(engine, result["emp_code"])
        draw_monthly_usage_chart(df, name=result.get("name", ""))

    elif result["type"] == "error":
        st.warning(result["message"])
