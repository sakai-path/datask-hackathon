# =============================================================================
# openai_sql.py - 自然言語からSQL文・グラフ指示・座席マップ指示・雑談応答を生成
# -----------------------------------------------------------------------------
# Azure OpenAI Function Calling 機能を活用して、以下を出力します：
# - SELECT文による読み取り専用SQL（type: 'sql'）
# - 社員コードを含む利用状況グラフ（type: 'chart'）
# - 座席マップ表示（type: 'seatmap' または seatmap with_names）
# - その他の質問には自然な雑談応答（type: 'chat'）を返します。
# =============================================================================

import json
from openai import AzureOpenAI
from core.config import secret
from core.schema import SCHEMA_HINT
from core.db import find_empcode_by_name

client = AzureOpenAI(
    api_version="2024-05-01-preview",
    azure_endpoint=secret("AZURE_OPENAI_ENDPOINT"),
    api_key=secret("AZURE_OPENAI_API_KEY"),
)
deployment = secret("AZURE_OPENAI_DEPLOYMENT")

def get_functions():
    return [
        {
            "name": "to_sql",
            "description": "自然言語からT-SQL SELECT文を生成します。",
            "parameters": {
                "type": "object",
                "properties": {"sql": {"type": "string"}},
                "required": ["sql"]
            },
        },
        {
            "name": "show_emp_usage_chart",
            "description": "社員の月別利用グラフを表示します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "emp_code": {"type": "string"},
                    "name": {"type": "string"}
                },
                "required": ["emp_code"]
            },
        },
        {
            "name": "show_seatmap",
            "description": "現在の座席マップを表示します。社員名表示あり/なしを選べます。",
            "parameters": {
                "type": "object",
                "properties": {
                    "detail": {
                        "type": "string",
                        "enum": ["with_names"],
                        "description": "社員名を表示する場合は 'with_names' を指定"
                    }
                },
                "required": []
            }
        }
    ]

def generate_semantic_sql(nl: str) -> dict:
    """
    日本語の自然文を Function Calling により目的別に変換。
    戻り値は type: sql/chart/seatmap/chat/error を含む dict。
    """
    system = (
        "あなたは社内のデータベースに対するアシスタントです。\n"
        "質問に応じて、以下のいずれかの関数呼び出しを使ってください：\n"
        "- 社員の利用状況グラフ → show_emp_usage_chart\n"
        "- 現在の座席マップ → show_seatmap\n"
        "- SQLでテーブルのデータ取得 → to_sql\n"
        "直接的な回答や一般的な雑談はせず、必ず関数形式で返してください。"
    )

    messages = [
        {"role": "system", "content": system + "\n\n" + SCHEMA_HINT},
        {"role": "user", "content": nl},
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
                if not emp_code and name:
                    found = find_empcode_by_name(name)
                    if found:
                        emp_code, name = found
                    else:
                        return {"type": "error", "message": f"該当する社員が見つかりません（{name}）"}
                return {"type": "chart", "emp_code": emp_code, "name": name}

            elif func_name == "show_seatmap":
                detail = args.get("detail")
                if detail == "with_names":
                    return {"type": "seatmap", "detail": "with_names"}
                return {"type": "seatmap"}

        return {"type": "error", "message": "AIが適切な応答を返せませんでした。"}

    except Exception as e:
        return {"type": "error", "message": str(e)}





