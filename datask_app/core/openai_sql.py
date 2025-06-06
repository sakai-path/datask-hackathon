# =============================================================================
# openai_sql.py - 自然言語からSQL文・グラフ指示・座席マップ指示・雑談応答を生成
# -----------------------------------------------------------------------------
# Azure OpenAI Function Calling を活用して以下を判定：
# - SQL文の生成（type: 'sql'）
# - グラフ表示（type: 'chart'）
# - 座席マップ（type: 'seatmap'）
# - 雑談応答（type: 'chat'）
# =============================================================================

import json
from openai import AzureOpenAI
from core.config import secret
from core.schema import SCHEMA_HINT
from core.db import find_empcode_by_name

# OpenAIクライアント設定
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
            "description": "社員の月別利用グラフを表示する指示を生成します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "emp_code": {"type": "string"},
                    "name": {"type": "string"}
                },
                "required": ["emp_code"]
            }
        },
        {
            "name": "show_seatmap",
            "description": "座席マップの表示（社員名表示オプション付き）を指示します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "detail": {
                        "type": "string",
                        "enum": ["with_names"],
                        "description": "社員名を表示したい場合は 'with_names' を指定"
                    }
                }
            }
        }
    ]


def generate_semantic_sql(nl: str) -> dict:
    """
    自然言語の質問をFunction Callingまたは通常出力で解析し、
    SQL/グラフ/マップ/雑談のいずれかを返す。
    """
    system = (
        "あなたは社内データに関するAIアシスタントです。\n"
        "次のように処理を分類してください：\n"
        "- 座席に関する質問 → show_seatmap\n"
        "- ○○さんの利用状況 → show_emp_usage_chart\n"
        "- データ参照や集計 → to_sql\n"
        "- 雑談（天気・挨拶など） → 通常のメッセージとして返答\n"
        "SELECT以外のSQL（INSERT/UPDATE/DELETE）は絶対に生成しないでください。"
    )

    messages = [
        {"role": "system", "content": system + "\n\n" + SCHEMA_HINT},
        {"role": "user", "content": nl}
    ]

    try:
        rsp = client.chat.completions.create(
            model=deployment,
            messages=messages,
            functions=get_functions(),
            function_call="auto",
            temperature=0
        )

        message = rsp.choices[0].message

        # 関数呼び出しされた場合
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

        # 関数呼び出しが無く、通常の応答（=雑談）
        if message.content:
            return {"type": "chat", "message": message.content}

        return {"type": "error", "message": "AIが正しく応答できませんでした。"}

    except Exception as e:
        return {"type": "error", "message": str(e)}
