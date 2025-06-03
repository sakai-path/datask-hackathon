# =============================================================================
# db.py - データベース接続と操作
# -----------------------------------------------------------------------------
# SQL Server（Azure SQL）への接続を行い、データの取得やクエリ実行を行う関数をまとめたモジュールです。
#
# 主な機能：
# - SQLAlchemyを使用してDBエンジンを構築
# - Seat / Employee / SeatLog テーブルの一覧取得
# - 任意のテーブルデータ取得
# - 任意のSQL文を実行し結果をDataFrameで返す
# - 氏名から社員コードを検索（← NEW）
#
# 使用例：
#   df = load_table("Seat", 100)
#   result = run_query("SELECT * FROM Employee")
#   code = find_empcode_by_name("田中")
# =============================================================================

import os
import streamlit as st
import pandas as pd
import sqlalchemy as sa
from urllib.parse import quote_plus
from config import secret

def build_engine() -> sa.Engine:
    srv, db = secret("AZURE_SQL_SERVER"), secret("AZURE_SQL_DB")
    usr, pwd = secret("AZURE_SQL_USER"), secret("AZURE_SQL_PASSWORD")
    driver = secret("AZURE_SQL_DRIVER", "ODBC Driver 17 for SQL Server")
    conn = f"mssql+pyodbc://{usr}:{quote_plus(pwd)}@{srv}/{db}?driver={driver.replace(' ', '+')}"
    return sa.create_engine(conn, fast_executemany=True)

engine = build_engine()

@st.cache_data(ttl=60)
def list_tables():
    sql = """
    SELECT TABLE_SCHEMA + '.' + TABLE_NAME AS FullName
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_NAME IN ('Seat','Employee','SeatLog')
    ORDER BY FullName
    """
    with engine.connect() as c:
        return [r[0] for r in c.execute(sa.text(sql))]

@st.cache_data(ttl=60)
def load_table(tbl: str, limit: int = 100) -> pd.DataFrame:
    with engine.connect() as c:
        return pd.read_sql(sa.text(f"SELECT TOP {limit} * FROM {tbl}"), c)

def run_query(sql: str) -> pd.DataFrame:
    with engine.connect() as c:
        return pd.read_sql(sa.text(sql), c)

# NEW: 氏名から社員コードを検索する関数
def find_empcode_by_name(name: str) -> tuple[str, str] | None:
    """
    氏名の一部（姓など）から該当する社員コードと氏名を返す。
    完全一致・前方一致・部分一致の順で検索。

    Returns:
        (EmpCode, Name) または None
    """
    with engine.connect() as c:
        # 完全一致 → 前方一致 → 部分一致
        patterns = [name, f"{name}%", f"%{name}%"]
        for pat in patterns:
            sql = sa.text("SELECT TOP 1 EmpCode, Name FROM Employee WHERE Name LIKE :pat")
            row = c.execute(sql, {"pat": pat}).fetchone()
            if row:
                return row[0], row[1]
    return None
