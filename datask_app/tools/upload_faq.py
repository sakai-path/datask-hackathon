# =============================================================================
# upload_faq.py - FAQデータを Azure AI Search にアップロード
# -----------------------------------------------------------------------------
# このモジュールは Streamlit アプリまたはローカルから呼び出して、
# faq-index に簡易的な質問文を登録するために使用します。
# -----------------------------------------------------------------------------
# 依存: core/config.py にある get_secret() を使用して
# AZURE_SEARCH_ENDPOINT / AZURE_SEARCH_API_KEY を取得します。
# =============================================================================

import os
import requests
import json
from core.config import get_secret

def upload_faq():
    """FAQデータを Azure AI Search にアップロードする"""
    endpoint = get_secret("AZURE_SEARCH_ENDPOINT")
    api_key = get_secret("AZURE_SEARCH_API_KEY")
    index_name = "faq-index"

    docs = [
        { "id": "1", "content": "現在空いている席は？" },
        { "id": "2", "content": "固定席とフリー席の違いは？" },
        { "id": "3", "content": "利用状況を確認したい" },
        { "id": "4", "content": "過去の座席利用履歴を見せて" },
        { "id": "5", "content": "一番利用されていない席を教えて" }
    ]

    url = f"{endpoint}/indexes/{index_name}/docs/index?api-version=2023-07-01-Preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    payload = {
        "value": [{"@search.action": "upload", **doc} for doc in docs]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            return True, "FAQデータをアップロードしました"
        else:
            return False, f"エラー: {response.status_code}\n{response.text}"
    except Exception as e:
        return False, f"アップロード中に例外が発生しました: {e}"

# テスト実行用（単独実行）
if __name__ == "__main__":
    success, message = upload_faq()
    print("✅ 成功" if success else "❌ 失敗")
    print(message)
