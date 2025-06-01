# =============================================================================
# config.py - 環境設定ラッパー＆接続チェック
# -----------------------------------------------------------------------------
# このモジュールは、Streamlit secrets または環境変数から
# 各種キー・エンドポイントを取得するラッパー関数を提供します。
#
# また、Azure AI Search への接続確認を行う関数も含みます。
#
# 提供機能：
# - get_secret()         : Streamlit secrets / 環境変数から取得
# - check_ai_search_connection() : Azure AI Search 接続確認
# - secret               : get_secret のエイリアス（使用簡略化用）
# =============================================================================

import os
import streamlit as st
import requests

def get_secret(key: str, default: str | None = None) -> str | None:
    """
    Streamlit secrets または環境変数から指定キーを取得

    Args:
        key (str): 取得したいキー名（例: "AZURE_OPENAI_ENDPOINT"）
        default (str|None): 見つからなかった場合のデフォルト値

    Returns:
        str | None: シークレット値（存在すれば）
    """
    return st.secrets.get(key) or os.getenv(key) or default


def check_ai_search_connection() -> bool:
    """
    Azure AI Search の接続確認（インデックス一覧を取得）

    Returns:
        bool: 成功なら True、失敗なら False
    """
    endpoint = get_secret("AZURE_SEARCH_ENDPOINT")
    key = get_secret("AZURE_SEARCH_API_KEY")

    if not endpoint or not key:
        st.warning("⚠ Azure AI Search の接続設定が見つかりません。secrets.toml を確認してください。")
        return False

    try:
        rsp = requests.get(
            url=f"{endpoint}/indexes?api-version=2023-07-01-preview",
            headers={"api-key": key}
        )
        if rsp.status_code == 200:
            return True
        else:
            st.warning(f"Azure AI Search に接続できません（ステータス: {rsp.status_code}）")
            return False
    except Exception as e:
        st.error(f"Azure AI Search 接続エラー: {e}")
        return False

#  利便性のためのエイリアス（openai_sql などから使用される）
secret = get_secret


