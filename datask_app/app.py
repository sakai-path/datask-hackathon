# =============================================================================
# app.py - OpenAI応答表示テスト画面（Datask用）
# -----------------------------------------------------------------------------
# 入力された自然言語をそのままOpenAIに送り、返ってきた応答を表示するだけの画面。
# =============================================================================

import streamlit as st
from openai import AzureOpenAI
from core.config import secret  # ← Azureのエンドポイント/キー取得

# OpenAIクライアントの準備
client = AzureOpenAI(
    api_key=secret("AZURE_OPENAI_API_KEY"),
    azure_endpoint=secret("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-05-01-preview"
)
deployment = secret("AZURE_OPENAI_DEPLOYMENT")

# UI設定
st.set_page_config(page_title="OpenAI 応答確認", layout="centered")
st.title("🧠 OpenAI 応答確認画面")

# 質問入力
query = st.text_input("質問を入力してください", placeholder="例：現在空いている席は？")

# 送信ボタン
if st.button("送信") and query.strip():
    try:
        with st.spinner("AIに問い合わせ中..."):
            response = client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": "あなたは親切なAIアシスタントです。"},
                    {"role": "user", "content": query}
                ],
                temperature=0.7
            )
            answer = response.choices[0].message.content
            st.markdown("### 📝 AIの応答")
            st.write(answer)
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
