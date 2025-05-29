# =============================================================================
# 🔧 config.py - シークレット情報の取得ユーティリティ
# -----------------------------------------------------------------------------
# このモジュールでは、Streamlitの secrets または環境変数から
# 安全に接続情報やAPIキーを取得するための関数を提供します。
#
# 使用例：
#   from config import secret
#   key = secret("AZURE_OPENAI_API_KEY")
#
# 優先順位： st.secrets > 環境変数 > デフォルト値（省略可）
# =============================================================================

import os
import streamlit as st

def secret(key: str, default: str | None = None) -> str | None:
    """
    Streamlit secrets または OS環境変数から値を取得する。

    Parameters:
    - key: シークレットキーの名前（例: "AZURE_SQL_PASSWORD"）
    - default: 該当キーがなかった場合に返すデフォルト値（省略可）

    Returns:
    - 文字列（設定値）または None
    """
    return st.secrets.get(key) or os.getenv(key) or default
