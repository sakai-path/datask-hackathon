# =============================================================================
# openai_sql.py - 自然言語からSQL文・グラフ指示・座席マップ指示を生成（Azure OpenAI対応）
# -----------------------------------------------------------------------------
# ユーザーの日本語の質問を受け取り、Azure OpenAI の Function Calling 機能を使って
# 以下のいずれかを判定・出力します：
# - 読み取り専用の T-SQL（SELECT 文）を生成
# - 社員の月別利用グラフの表示指示を生成
# - 現在の座席マップ表示指示を生成（社員名表示も対応）
#
# 使用例：
#   result = generate_semantic_sql("昨日空いていた席は？")
#   result = generate_semantic_sql("田中さんのグラフを見せて")
#   result = generate_semantic_sql("今誰がどこに座ってる？")
#
# 戻り値の例：
#   {"type": "sql", "sql": "SELECT ..."}
#   {"type": "chart", "emp_code": "E10001", "name": "田中一郎"}
#   {"type": "seatmap"} または {"type": "seatmap", "detail": "with_names"}
# =============================================================================

import json
from openai import AzureOpenAI
from core.config import secret
from core.schema import SCHEMA_HINT
from core.db import find_empcode_by_name

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
    日本語の質問を Function Calling により SQL / グラフ / 座席マップ指示に変換。

    Returns:
        dict:
            - {"type": "sql", "sql": "..."}
            - {"type": "chart", "emp_code": "...", "name": "..."}
            - {"type": "seatmap"} または {"type": "seatmap", "detail": "with_names"}
            - {"type": "error", "message": "..."} （失敗時）
    """
    system = (
        "あなたは社内座席・勤務データに関するAIアシスタントです。\n"
        "以下の分類に従って、質問の種類を判定してください：\n\n"
        "- 質問が座席の空き状況や誰がどこに座っているかに関する場合 → 'type': 'seatmap' を返してください。\n"
        "  ・もし社員名を表示する方が適切な場合（例：誰が座ってる？） → 'detail': 'with_names' を含めてください。\n"
        "- 質問が社員の利用傾向（例：〇〇さんの利用状況）に関する場合 → 'type': 'chart' と社員情報を返してください。\n"
        "- それ以外（データの一覧表示など） → 'type': 'sql' とSQL文を返してください。\n"
        "- 判別できない場合 → 'type': 'error' と 'message' を返してください。"
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
                        return {
                            "type": "error",
                            "message": f"該当する社員が見つかりませんでした（氏名: {name}）"
                        }

                if emp_code:
                    return {"type": "chart", "emp_code": emp_code, "name": name}
                else:
                    return {"type": "error", "message": "社員コードが取得できませんでした。"}

        # fallback: 明示的にseatmapを検出
        lower = nl.lower()
        if any(x in lower for x in ["空いている席", "空席", "誰が座って", "使用状況", "今の席"]):
            if any(x in lower for x in ["誰", "名前", "誰が", "座ってる"]):
                return {"type": "seatmap", "detail": "with_names"}
            else:
                return {"type": "seatmap"}

        return {"type": "error", "message": "ちょっと意味がわかりませんでした。"}

    except Exception as e:
        return {"type": "error", "message": str(e)}


