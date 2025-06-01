# =============================================================================
# Datask - Streamlitアプリ起動用メインファイル
# =============================================================================

import streamlit as st
from core.db import list_tables, load_table, run_query, engine
from core.openai_sql import generate_sql
from visual.seatmap import get_seat_labels, get_used_labels, draw_auto_seat_map
from visual.charts import (
    get_seat_usage_counts,
    draw_usage_bar_chart,
    get_monthly_usage_by_employee,
    draw_monthly_usage_chart,
)
from core.config import check_ai_search_connection
from testdata.seatlog_dummy import create_test_logs
from tools.upload_faq import upload_faq

# ─────────────────────────────────────────────
# ページ初期設定
# ─────────────────────────────────────────────
st.set_page_config(page_title="おしゃべりデータ", page_icon="◆", layout="centered")
st.title("おしゃべりデータ – フリー席検索")

# ─────────────────────────────────────────────
# 質問 → SQL → 実行
# ─────────────────────────────────────────────
st.markdown("### 🔍 質問を入力してください")
query = st.text_input("例: “現在空いている席は？”")
col1, col2 = st.columns(2)

if col1.button("SQL 生成"):
    if not query.strip():
        st.warning("質問を入力してください")
    else:
        try:
            sql = generate_sql(query)
            st.session_state["sql"] = sql
            st.code(sql, language="sql")
        except Exception:
            st.warning("ちょっと意味がわかりません")

if col2.button("SQL 実行"):
    sql = st.session_state.get("sql")
    if not sql:
        st.warning("先に SQL を生成してください")
    elif not sql.strip().lower().startswith("select"):
        st.error("SELECT 以外のSQLは実行できません")
    else:
        try:
            df = run_query(sql)
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"実行失敗: {e}")

# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("### ✅ 接続状況確認")
if check_ai_search_connection():
    st.success("✅ Azure AI Search 接続 OK")
else:
    st.error("❌ Azure AI Search 未接続")

# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📄 テーブル表示")
table = st.selectbox("テーブルを選択", list_tables())
limit = st.slider("行数を選択", 10, 500, 100, 10)
if st.button("テーブルを読み込む"):
    st.dataframe(load_table(table, limit), use_container_width=True)

# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🗺️ 座席マップ（4列）")
if st.button("座席マップを表示"):
    all_labels = get_seat_labels(engine)
    used_labels = get_used_labels(engine)
    draw_auto_seat_map(all_labels, used_labels, columns=5)

# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📊 座席ごとの利用回数グラフ")
if st.button("利用回数グラフを表示"):
    df = get_seat_usage_counts(engine)
    draw_usage_bar_chart(df)

# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("### 👤 社員別・月別の利用回数")
emp_code = st.text_input("社員コードを入力（例: E10005）")
if st.button("社員の利用履歴を表示"):
    df = get_monthly_usage_by_employee(engine, emp_code)
    draw_monthly_usage_chart(df, emp_code)

# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🧪 ダミーデータ登録（初回のみ）")
if st.button("SeatLog ダミーデータ登録"):
    create_test_logs()
    st.success("SeatLog ダミーデータを登録しました")

# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📚 FAQデータ登録（Azure AI Search）")
if st.button("FAQデータ登録"):
    with st.spinner("アップロード中..."):
        success, msg = upload_faq()
        st.success(msg) if success else st.error(msg)


