
# =============================================================================
# app.py - Datask Streamlit アプリ（Function Calling + UI改善）
# -----------------------------------------------------------------------------
# 自然言語からAIによってSQL生成・座席マップ表示・利用グラフ表示・雑談応答を切り替え。
# よくある質問ボタンや「なにが聞けますか？」ボタンもUIに統合。
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
st.set_page_config(page_title="Datask", layout="centered", page_icon="❄️")
st.title("❄️フリーアドレス検索")

if "query" not in st.session_state:
    st.session_state.query = ""
if "run" not in st.session_state:
    st.session_state.run = False

# ─────────────────────────────────────
# よくある質問（上部ボタン）
# ─────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("座席マップを見せて"):
        st.session_state.query = "今の座席マップを見せて"
        st.session_state.run = True
with col2:
    if st.button("田中さんの利用状況"):
        st.session_state.query = "田中さんの5月利用状況"
        st.session_state.run = True
with col3:
    if st.button("なにが聞けますか"):
        st.session_state.query = "なにが聞けますか"
        st.session_state.run = True

# ─────────────────────────────────────
# テキスト入力欄と送信ボタン
# ─────────────────────────────────────
if st.button("送信"):
    st.session_state.run = True
    
show_sql = st.checkbox("生成されたSQLを表示")
sql_container = st.empty()

# ─────────────────────────────────────
# メイン処理
# ─────────────────────────────────────
if st.session_state.run and query.strip():
    st.session_state.run = False
    result = generate_semantic_sql(query)

    if result["type"] == "seatmap":
        labels = get_seat_labels(engine)
        if result.get("detail") == "with_names":
            used_dict = get_used_label_name_dict(engine)
            draw_auto_seat_map_with_names(labels, used_dict)
        else:
            used = get_used_labels(engine)
            draw_auto_seat_map(labels, used)

        st.success("🪑 座席マップを表示しました。")
        if show_sql:
            with sql_container.expander("🔍 AIによる判定内容"):
                st.code("-- AI判定: 座席マップ呼び出し", language="sql")

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
        if df.empty:
            st.warning("データがありません。")
        else:
            draw_monthly_usage_chart(df, name=result.get("name", ""))
            st.success(f"📊 {result.get('name', '')}さんのグラフを表示しました。")

    elif result["type"] == "chat":
        st.markdown("### 💬 AIの応答")
        st.info(result["message"])

    elif result["type"] == "error":
        st.warning(result["message"])

# ─────────────────────────────────────
# サイドバー：DB参照とCSV出力
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
