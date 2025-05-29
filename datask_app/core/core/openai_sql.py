# =============================================================================
# 🤖 openai_sql.py - 自然言語からSQL文を生成（Azure OpenAI利用）
# -----------------------------------------------------------------------------
# ユーザーの日本語の質問文を受け取り、Azure OpenAI のfunction calling機能を使って
# 読み取り専用のT-SQL（SELECT文）を生成するモジュールです。
#
# 使用例：
#   sql = generate_sql("昨日空いていた席は？")
#
# 注意：
# - SELECT文のみを生成（更新・削除・追加は禁止）
# - モデルのデプロイ名は AZURE_OPENAI_DEPLOYMENT に設定されていること
# =============================================================================

import json
from openai import AzureOpenAI
from config import secret
from core.schema import SCHEMA_HINT

client = AzureOpenAI(
    api_version="2024-05-01-preview",
    azure_endpoint=secret("AZURE_OPENAI_ENDPOINT"),
    api_key=secret("AZURE_OPENAI_API_KEY"),
)
deployment = secret("AZURE_OPENAI_DEPLOYMENT")

def generate_sql(nl: str) -> str:
    system = (
        "You are an assistant that converts Japanese questions into a single "
        "read-only T-SQL SELECT statement for Azure SQL. "
        "Use ONLY the tables listed below. Never generate INSERT/UPDATE/DELETE."
    )
    messages = [
        {"role": "system", "content": system + SCHEMA_HINT},
        {"role": "user", "content": nl},
    ]
    functions = [{
        "name": "to_sql",
        "description": "Generate T-SQL SELECT",
        "parameters": {
            "type": "object",
            "properties": {"sql": {"type": "string"}},
            "required": ["sql"],
        },
    }]
    rsp = client.chat.completions.create(
        model=deployment,
        messages=messages,
        functions=functions,
        function_call={"name": "to_sql"},
        temperature=0,
    )
    return json.loads(rsp.choices[0].message.function_call.arguments)["sql"]
