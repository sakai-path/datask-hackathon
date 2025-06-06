# =============================================================================
# openai_sql.py - 自然言語からSQL文・グラフ・座席マップ指示を生成（Azure OpenAI Function Calling対応）
# -----------------------------------------------------------------------------
# Azure OpenAIのFunction Calling機能を用いて、以下のタイプを返します：
# - 読み取り専用のT-SQL SELECT文（type: 'sql'）
# - 社員利用グラフの表示（type: 'chart'）
# - 座席マップの表示（type: 'seatmap' または seatmap with_names）
# -----------------------------------------------------------------------------
# 戻り値の形式例：
# {"type": "sql", "sql": "..."}
# {"type": "chart", "emp_code": "E10001", "name": "田中一郎"}
# {"type": "seatmap"} または {"type": "seatmap", "detail": "with_names"}
# {"type": "error", "message": "..."} （エラー時）
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

# Function Calling 定義
def get_functions():
    return [
        {
            "name": "to_sql",
            "description": "自然言語からSELECT文を生成します。UPDATE/DELETEは禁止。",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string"}
                },
                "required": ["sql"]
            },
        },
        {
            "name": "show_emp_usage_chart",
            "description": "特定社員の月別利用状況を表示するグラフの指示を生成します。",
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
            "description": "現在の座席使用状況マップを表示する指示を生成します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "detail": {
                        "type": "string",
                        "enum": ["with_names"],
                        "description": "使用中の席に社員名を表示したい場合は 'with_names'"
                    }
                },
                "required": []
            }
        }
    ]

# メイン関数
def generate_semantic_sql(nl: str) -> dict:
    """
    日本語自然文をFunction Callingにより構造化判定し、SQLまたは描画命令を返す。
    """
    system = (
        "あなたは社内データアシスタントです。\n"
        "ユーザーの質問に対して、以下のいずれかの関数呼び出し形式で返答してください：\n"
        "- SQL取得 → to_sql\n"
        "- 社員の月別グラフ → show_emp_usage_chart\n"
        "- 現在の座席マップ → show_seatmap\n"
        "それ以外は一切返さず、常にfunction_call形式の応答を行ってください。"
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

            # SELECT文
            if func_name == "to_sql":
                sql = args.get("sql", "")
                if not sql.strip().lower().startswith("select"):
                    return {"type": "error", "message": "SELECT文以外の出力がありました。"}
                return {"type": "sql", "sql": sql}

            # グラフ描画
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

            # 座席マップ
            elif func_name == "show_seatmap":
                detail = args.get("detail")
                if detail == "with_names":
                    return {"type": "seatmap", "detail": "with_names"}
                return {"type": "seatmap"}

        return {"type": "error", "message": "AIが適切な関数呼び出しを生成できませんでした。"}

    except Exception as e:
        return {"type": "error", "message": str(e)}
