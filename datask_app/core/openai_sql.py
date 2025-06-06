# =============================================================================
# openai_sql.py - 自然言語からSQL文を生成するAIモジュール（Function Calling 不使用）
# -----------------------------------------------------------------------------
# ユーザーの日本語質問に対し、Azure OpenAI を使って SELECT文を直接生成。
# 必ずT-SQLのSELECT文のみを返し、INSERT/UPDATE/DELETEは禁止。
# =============================================================================

import json
from openai import AzureOpenAI
from core.config import secret
from core.schema import SCHEMA_HINT

# OpenAI クライアント設定
client = AzureOpenAI(
    api_version="2024-05-01-preview",
    azure_endpoint=secret("AZURE_OPENAI_ENDPOINT"),
    api_key=secret("AZURE_OPENAI_API_KEY"),
)
deployment = secret("AZURE_OPENAI_DEPLOYMENT")


def generate_semantic_sql(nl: str) -> dict:
    """
    日本語の自然言語を SELECT文に変換。

    Returns:
        dict: { "type": "sql", "sql": "SELECT ..." } または
              { "type": "error", "message": "..." }
    """
    system_prompt = (
        "あなたは社内データベース専用のAIアシスタントです。"
        "ユーザーからの日本語の質問に対して、T-SQL形式のSELECT文だけを出力してください。"
        "絶対にINSERT, UPDATE, DELETE, DROP, CREATE, ALTERは出さないでください。"
        "コメントや補足も不要です。"
        "以下のスキーマ定義を参考に、正確なクエリを生成してください。"
    )

    messages = [
        {"role": "system", "content": system_prompt + "\n\n" + SCHEMA_HINT},
        {"role": "user", "content": nl}
    ]

    try:
        rsp = client.chat.completions.create(
            model=deployment,
            messages=messages,
            temperature=0,
        )
        sql = rsp.choices[0].message.content.strip()

        if not sql.lower().startswith("select"):
            return {"type": "error", "message": "SELECT文以外の出力がありました。"}

        return {"type": "sql", "sql": sql}

    except Exception as e:
        return {"type": "error", "message": str(e)}
