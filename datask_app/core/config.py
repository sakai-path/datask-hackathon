# core/config.py

import os
import streamlit as st
import requests

def get_secret(key: str, default: str | None = None) -> str | None:
    """
    Streamlit secrets または環境変数から指定キーを取得
    """
    return st.secrets.get(key) or os.getenv(key) or default


def check_ai_search_connection() -> bool:
    """
    Azure AI Search の接続確認（インデックス一覧を取得してみる）
    成功：True、失敗：False
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

secret = get_secret

