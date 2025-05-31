# core/ai_search.py

import requests
from core.config import get_secret

def search_faq_from_query(user_input: str, top_k: int = 3) -> list[str]:
    """
    Azure AI Search を使って FAQ などの補足情報を検索する
    """
    endpoint = get_secret("AZURE_SEARCH_ENDPOINT")
    key = get_secret("AZURE_SEARCH_API_KEY")
    index_name = "faq-index"  # インデックス名（変更可）

    if not endpoint or not key:
        return []

    url = f"{endpoint}/indexes/{index_name}/docs/search?api-version=2023-07-01-preview"

    headers = {
        "Content-Type": "application/json",
        "api-key": key
    }

    body = {
        "search": user_input,
        "top": top_k
    }

    try:
        rsp = requests.post(url, headers=headers, json=body)
        results = rsp.json().get("value", [])
        return [doc.get("content") for doc in results]
    except Exception as e:
        return [f"FAQ検索に失敗しました: {e}"]
