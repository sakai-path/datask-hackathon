# =============================================================================
# employee.py - 氏名から社員コード（EmpCode）を取得するユーティリティ
# -----------------------------------------------------------------------------
# このモジュールでは、自然言語で指定された社員の氏名（例：「田中さん」）
# から、社員コード（EmpCode）を検索して返す関数を提供します。
#
# 主な使用箇所：
# - 質問に含まれる氏名から対象の社員コードを特定し、
#   社員ごとのグラフ表示やログ抽出に活用。
# =============================================================================

import sqlalchemy as sa
import pandas as pd
from core.db import engine

def get_empcode_by_name(name: str) -> str | None:
    """
    氏名からEmpCodeを取得（部分一致、最初の1件を返す）

    Parameters:
        name (str): 氏名の一部（例: "田中"）

    Returns:
        EmpCode (str) or None
    """
    sql = "SELECT EmpCode FROM Employee WHERE Name LIKE :name"
    with engine.begin() as conn:
        df = pd.read_sql(sa.text(sql), conn, params={"name": f"%{name}%"})
    return df["EmpCode"].iloc[0] if not df.empty else None
