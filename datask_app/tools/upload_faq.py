# =============================================================================
# upload_faq.py - Azure AI Search に FAQデータをアップロード
# -----------------------------------------------------------------------------
# このスクリプトはローカルではなく GitHub 上に配置して、
# Streamlit Cloud の Web UI や CLI から実行を想定しています。
# =============================================================================

import os
import requests
import json
from core.config import get_secret

# --- Azure AI Search 設定 ---
endpoint = get_secret("AZURE_SEARCH_ENDPOINT")
api_key = get_secret("AZURE_SEARCH_API_KEY")
index_name = "faq-index"

# --- 登録データ（必要に応じて外部JSONファイル読み込みに変更可） ---
docs = [
    { "id": "1", "content": "現在空いている席は？" },
    { "id": "2", "content": "固定席とフリー席の違いは？" },
    { "id": "3", "content": "利用状況を確認したい" }
]

# --- アップロード処理 ---
def upload_faq():
    url = f"{endpoint}/indexes/{index_name}/docs/index?api-version=2023-07-01-Preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    payload = {
        "value": [{"@search.action": "upload", **doc} for doc in docs]
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        print("✅ アップロード成功")
    else:
        print(f"❌ エラー発生: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    upload_faq()
