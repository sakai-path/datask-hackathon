# =============================================================================
# app.py - Datask Streamlit アプリ
# -----------------------------------------------------------------------------
# 自然言語質問から SQL 実行・グラフ描画・座席マップ表示を行う。
# サイドバーでは任意テーブルをCSV出力付きで閲覧可能。
# =============================================================================

import streamlit as st
import pandas as pd
from core.db import run_query, engine, load_table
from core.openai_sql import generate_semantic_sql
from visual.charts import get_monthly_usage_by_employee, draw_monthly_usage_chart
from visual.seatmap import get_seat_labels, get_used_labels, draw_auto_seat_map

# ─────────────────────────────────────
# UI 初期設定
# ─────────────────────────────────────
st.set_page_config(page_title="おしゃべりデータ", layout="centered")
st.title("💬 おしゃべりデータ")

st.markdown("### 質問を入力してください（例：『田中さんの月別利用状況は？』など）")
st.caption("例：『現在空いている席は？』")

# ─────────────────────────────────────
# 入力欄の吹き出し風スタイル設定
# ─────────────────────────────────────
st.markdown("""
<style>
.chat-input-box {
    background-color: #fff9db;  /* 淡いイエロー */
    padding: 1rem;
    border-radius: 1rem;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    margin-bottom: 1rem;
}
.stTextInput > div > input {
    background-color: transparent !important;
    border: none !important;
    font-size: 1.1rem !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────
# 質問入力欄（吹き出し風デザイン）
# ─────────────────────────────────────
with st.container():
    st.markdown('<div class="chat-input-box">', unsafe_allow_html=True)
    query = st.text_input("質問", placeholder="田中さんの利用状況をグラフで見せて", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

show_sql = st.checkbox("生成されたSQLを表示")
sql_container = st.empty()

# ─────────────────────────────────────
# メイン処理：自然言語質問の判定と表示分岐
# ─────────────────────────────────────
if query.strip():
    lower = query.lower()

    # 座席マップのキーワードによる判定
    if "空いている席" in lower or "使用状況" in lower or "空席" in lower or "今の席" in lower:
        labels = get_seat_labels(engine)
        used = get_used_labels(engine)
        draw_auto_seat_map(labels, used)
        st.info("現在の座席利用状況を表示しました。")

    else:
        # 通常のSQL/グラフ/エラー処理
        result = generate_semantic_sql(query)

        if result["type"] == "sql":
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
# サイドバー：テーブル表示＆CSV出力（初期は折りたたみ）
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
