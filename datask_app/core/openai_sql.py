# =============================================================================
# openai_sql.py - 自然言語からSQL文・グラフ指示・座席マップ指示・雑談応答を生成（Azure OpenAI対応）
# -----------------------------------------------------------------------------
# ユーザーの日本語の質問を受け取り、Azure OpenAI の Function Calling 機能を使って
# 以下のいずれかを判定・出力します：
# - 読み取り専用の T-SQL（SELECT 文）を生成
# - 社員の月別利用グラフの表示指示を生成
# - 現在の座席マップ表示指示を生成（社員名表示も対応）
# - 雑談などは通常チャット応答として返答
#
# 使用例：
#   result = generate_semantic_sql("昨日空いていた席は？")
#   result = generate_semantic_sql("田中さんのグラフを見せて")
#   result = generate_semantic_sql("こんにちは")
#
# 戻り値の例：
#   {"type": "sql", "sql": "SELECT ..."}
#   {"type": "chart", "emp_code": "E10001", "name": "田中一郎"}
#   {"type": "seatmap"} または {"type": "seatmap", "detail": "with_names"}
#   {"type": "chat", "message": "こんにちは！ご質問があれば何でもどうぞ。"}
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
                    "emp_code": {"type": "string"},
                    "name": {"type": "string"}
                },
                "required": ["emp_code"]
            }
        }
    ]

def generate_semantic_sql(nl: str) -> dict:
    system = (
        "あなたは社内座席・勤務データに関するAIアシスタントです。\n"
        "以下の分類に従って、質問の種類を判定してください：\n\n"
        "- 質問が座席の空き状況や誰がどこに座っているかに関する場合 → 'type': 'seatmap' を返してください。\n"
        "  ・もし社員名を表示する方が適切な場合（例：誰が座ってる？） → 'detail': 'with_names' を含めてください。\n"
        "- 質問が社員の利用傾向（例：〇〇さんの利用状況）に関する場合 → 'type': 'chart' と社員情報を返してください。\n"
        "- それ以外（データの一覧表示など） → 'type': 'sql' とSQL文を返してください。\n"
        "- 雑談・あいさつなど業務と関係のない質問には、'type': 'chat' を返し、messageに自然な応答を書いてください。"
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
                        return {"type": "error", "message": f"該当する社員が見つかりませんでした（氏名: {name}）"}
                if emp_code:
                    return {"type": "chart", "emp_code": emp_code, "name": name}
                else:
                    return {"type": "error", "message": "社員コードが取得できませんでした。"}

        # 通常の自然文メッセージとして返すようなものが含まれているかを確認
        if message.content:
            return {"type": "chat", "message": message.content.strip()}

        return {
            "type": "error",
            "message": (
                "質問の意図がうまく読み取れませんでした。\n\n"
                "以下のような質問を試してみてください：\n"
                "・『田中さんの利用状況を教えて』\n"
                "・『空いている席は？』\n"
                "・『Seat テーブルの中身を見せて』"
            )
        }

    except Exception as e:
        return {"type": "error", "message": str(e)}





