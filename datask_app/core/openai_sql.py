# =============================================================================
# openai_sql.py - 自然言語からSQL文やグラフ表示指示を生成（Azure OpenAI利用）
# -----------------------------------------------------------------------------
# ユーザーの日本語の質問文を受け取り、Azure OpenAI の Function Calling 機能を使って
# 以下のいずれかを実現します：
# - 読み取り専用の T-SQL（SELECT 文）を生成
# - 社員の利用履歴グラフ表示を指示する関数呼び出し
#
# 使用例：
#   result = generate_semantic_sql("昨日空いていた席は？")
#   result = generate_semantic_sql("田中さんのグラフを見せて")
#
# 戻り値は以下の形式：
#   {"type": "sql", "sql": "SELECT ..."}
#   {"type": "chart", "emp_code": "E10001", "name": "田中一郎"}
# =============================================================================

import json
from openai import AzureOpenAI
from core.config import secret
from core.schema import SCHEMA_HINT
from core.db import find_empcode_by_name  # ← 追加

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
            "description": "自然言語から読み取り専用のT-SQL SELECT文を生成します。",
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
            "description": "特定の社員の月別利用グラフを表示する指示を生成します。",
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


def generate_semantic_sql(nl: str) -> dict:
    """
    日本語の質問を Function Calling により SQL または グラフ表示指示に変換。

    Returns:
        dict:
            - {"type": "sql", "sql": "..."}
            - {"type": "chart", "emp_code": "...", "name": "..."}
            - {"type": "error", "message": "..."} （失敗時）
    """
    system = (
        "You are an assistant that converts Japanese questions into either:\n"
        "- a read-only T-SQL SELECT statement for Azure SQL\n"
        "- OR a function call to 'show_emp_usage_chart' for employee usage graphs.\n\n"
        "Use ONLY the tables and fields listed below. Never generate INSERT/UPDATE/DELETE.\n"
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

        if message.function_call:
            func_name = message.function_call.name
            args = json.loads(message.function_call.arguments)

            if func_name == "to_sql":
                return {"type": "sql", "sql": args["sql"]}

            elif func_name == "show_emp_usage_chart":
                emp_code = args.get("emp_code")
                name = args.get("name", "")

                # 補完処理：emp_code がない場合は名前から検索
                if not emp_code and name:
                    found = find_empcode_by_name(name)
                    if found:
                        emp_code, name = found
                    else:
                        return {
                            "type": "error",
                            "message": f"該当する社員が見つかりませんでした（氏名: {name}）"
                        }

                if emp_code:
                    return {"type": "chart", "emp_code": emp_code, "name": name}
                else:
                    return {"type": "error", "message": "社員コードが取得できませんでした。"}

        return {"type": "error", "message": "ちょっと意味がわかりませんでした。"}

    except Exception as e:
        return {"type": "error", "message": str(e)}



