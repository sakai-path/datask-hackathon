# =============================================================================
# app.py - おしゃべりデータ：自然言語からSQL→実行→結果を出し分け
# -----------------------------------------------------------------------------
# このアプリでは、自然言語の質問を入力するだけで、
# - Azure OpenAI の Function Calling を使って SQL を生成
# - 実行して表／文章／グラフなどを自動で表示
# -----------------------------------------------------------------------------
# 入力：質問文（例：「田中さんの利用状況は？」）
# 出力：質問に応じた可視化（表、文章、グラフ）
# =============================================================================

import streamlit as st
from core.db import run_query, engine
from core.openai_sql import generate_sql
from visual.charts import (
    get_monthly_usage_by_employee,
    draw_monthly_usage_chart,
    get_seat_usage_counts,
    draw_usage_bar_chart,
)

st.set_page_config(page_title="おしゃべりデータ", layout="centered")
st.title("🧠 おしゃべりデータ")

# ─────────────────────────────────────────────
# 入力欄：質問テキストを受け付ける（自然言語のみ）
# ─────────────────────────────────────────────
st.markdown("#### 質問を入力してください（例：『田中さんの月別利用状況は？』など）")

query = st.text_input("例：「現在空いている席は？」", placeholder="ここに質問を入力...")

# SQL表示のトグル用
show_sql = st.checkbox("生成されたSQLを表示", value=False)

# ─────────────────────────────────────────────
# 入力された質問があればSQL生成→実行
# ─────────────────────────────────────────────
if query:
    with st.spinner("AIが質問を解析中..."):
        sql = generate_sql(query)

    if not sql or not sql.strip().lower().startswith("select"):
        st.error("SQL生成に失敗しました")
    else:
        if show_sql:
            st.code(sql, language="sql")

        try:
            df = run_query(sql)
        except Exception as e:
            st.error(f"SQL実行エラー: {e}")
            df = None

        if df is not None:
            # ─────────────────────────────────────
            # 出し分け処理：データ内容に応じて表示形式を判断
            # ─────────────────────────────────────

            # 1. 氏名＋月＋利用回数 → グラフ
            if set(df.columns) >= {"Month", "UsageCount"} and len(df) <= 24:
                draw_monthly_usage_chart(df)

            # 2. 席ラベル＋利用回数 → 座席集計グラフ
            elif set(df.columns) >= {"Label", "UsageCount"} and len(df) <= 100:
                draw_usage_bar_chart(df)

            # 3. 結果行数が少ない → テーブルではなくテキスト的に出力
            elif len(df) == 1 and df.shape[1] == 1:
                st.success(f"回答：{df.iloc[0, 0]}")

            # 4. 通常の表表示
            else:
                st.dataframe(df, use_container_width=True)



