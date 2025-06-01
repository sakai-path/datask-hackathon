# =============================================================================
# openai_sql.py - 自然言語からSQL文を生成（Azure OpenAI利用）
# -----------------------------------------------------------------------------
# ユーザーの日本語の質問文を受け取り、Azure OpenAI の function calling 機能を使って
# 読み取り専用の T-SQL（SELECT 文）またはグラフ表示用の関数呼び出しに変換します。
#
# 使用例：
#   sql = generate_sql("昨日空いていた席は？")
#   （または）
#   sql = generate_sql("田中さんの月別利用グラフを見せて")
#
# 注意：
# - SELECT 文のみを生成（INSERT/UPDATE/DELETEは禁止）
# - モデルのデプロイ名は AZURE_OPENAI_DEPLOYMENT に設定されていること
# - Function Calling 経由でグラフ表示関数を呼び出すこともあります
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


def get_functions():
    """Function Calling で登録する関数スキーマを定義"""
    return [
        {
            "name": "to_sql",
            "description": "Convert natural language to T-SQL SELECT",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string"}
                },
                "required": ["sql"]
            }
        },
        {
            "name": "show_emp_usage_chart",
            "description": "特定の社員の月別利用グラフを表示する",
            "parameters": {
                "type": "object",
                "properties": {
                    "emp_code": {
                        "type": "string",
                        "description": "社員コード（例：E10001）"
                    },
                    "name": {
                        "type": "string",
                        "description": "社員の氏名（例：田中一郎）"
                    }
                },
                "required": ["emp_code"]
            }
        }
    ]


def generate_sql(nl: str) -> str:
    """日本語の質問を Function Calling により SQL または関数呼び出しに変換"""
    system = (
        "You are an assistant that converts Japanese questions into either:\n"
        "- a single read-only T-SQL SELECT statement for Azure SQL\n"
        "- OR call a function like 'show_emp_usage_chart' for graphs\n\n"
        "Use ONLY the tables listed below. Never generate INSERT/UPDATE/DELETE.\n"
    )

    messages = [
        {"role": "system", "content": system + SCHEMA_HINT},
        {"role": "user", "content": nl}
    ]

    try:
        rsp = client.chat.completions.create(
            model=deployment,
            messages=messages,
            functions=get_functions(),
            function_call="auto",
            temperature=0,
        )
        message = rsp.choices[0].message

        # Function Calling の場合（SQL or グラフ）
        if message.function_call:
            func_name = message.function_call.name
            args = json.loads(message.function_call.arguments)

            if func_name == "to_sql":
                return args["sql"]

            elif func_name == "show_emp_usage_chart":
                # 特殊なトークンとして戻す（後段の処理側で判定）
                emp_code = args.get("emp_code")
                name = args.get("name", "")
                return f"#CHART:{emp_code}:{name}"

        return "-- ちょっと意味がわかりませんでした。"

    except Exception:
        return "-- ちょっと意味がわかりませんでした。"

def is_chart_request(nl: str) -> str | None:
    """
    特定の社員別グラフ表示を求める質問かどうかを判定
    （例:「E10001 の利用履歴をグラフで見せて」など）

    Returns:
        対象の社員コードが含まれていればそのコードを返す。なければ None。
    """
    import re
    m = re.search(r"(E\d{5})", nl)
    if m and "グラフ" in nl or "傾向" in nl or "回数" in nl:
        return m.group(1)
    return None

