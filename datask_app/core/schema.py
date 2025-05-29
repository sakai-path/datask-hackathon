# =============================================================================
# schema.py - モデルに渡すスキーマヒント（テーブル構造の定義）
# -----------------------------------------------------------------------------
# OpenAIに渡すシステムメッセージの一部として使われる、利用可能なテーブルとそのカラムの説明を記述します。
#
# この情報を使って、AIが適切なSQL文を生成できるようにします。
# 他のテーブルは使用できないように注意喚起しています。
# =============================================================================

SCHEMA_HINT = """
Available tables (only these 3):
  dbo.Seat(SeatId int PK, Label nvarchar, Area nvarchar, SeatType nvarchar)
  dbo.Employee(EmpCode varchar PK, Name nvarchar, Dept nvarchar)
  dbo.SeatLog(LogId int PK, SeatId int FK, EmpCode varchar FK,
              CheckIn datetime2, CheckOut datetime2)
"""
