# =============================================================================
# seatlog_dummy.py - SeatLog テストデータ生成＆挿入
# -----------------------------------------------------------------------------
# このモジュールは初期データ確認用にのみ使用します。
# 2025年1月〜5月の範囲で、全日ランダムに社員が席に着いたログを生成します。
# 各日最低10件（最大20件）を挿入します。
# =============================================================================

import random
from datetime import datetime, timedelta
import pandas as pd
import sqlalchemy as sa
from core.db import engine


def generate_dummy_seatlog() -> pd.DataFrame:
    """
    2025年1月〜5月の各日に最低10件のSeatLogを生成（最大20件）
    ・SeatId：1〜20
    ・EmpCode：E10001〜E10050
    ・CheckIn：9:00〜10:00の間
    ・CheckOut：6〜9時間後
    """
    seat_ids = list(range(1, 21))  # SeatId: 1〜20
    emp_codes = [f"E{10000 + i:03}" for i in range(1, 51)]  # E10001〜E10050
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 5, 31)

    data = []
    current_day = start_date

    while current_day <= end_date:
        entries_today = random.randint(10, 20)  # 1日あたり10〜20件
        for _ in range(entries_today):
            seat_id = random.choice(seat_ids)
            emp_code = random.choice(emp_codes)

            # CheckIn は 9:00〜10:00 の範囲でランダム
            check_in = datetime.combine(current_day, datetime.min.time()) + timedelta(hours=9, minutes=random.randint(0, 60))
            check_out = check_in + timedelta(hours=random.randint(6, 9), minutes=random.randint(0, 59))

            data.append({
                "SeatId": seat_id,
                "EmpCode": emp_code,
                "CheckIn": check_in,
                "CheckOut": check_out
            })

        current_day += timedelta(days=1)

    return pd.DataFrame(data)


def insert_seatlog(df: pd.DataFrame):
    """
    DataFrameからSeatLogに一括INSERT
    """
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(sa.text("""
                INSERT INTO SeatLog (SeatId, EmpCode, CheckIn, CheckOut)
                VALUES (:seat, :emp, :cin, :cout)
            """), {
                "seat": row.SeatId,
                "emp": row.EmpCode,
                "cin": row.CheckIn,
                "cout": row.CheckOut
            })


def create_test_logs():
    """
    ダミーデータ生成＆挿入をまとめて実行する関数
    Streamlitのボタンから呼び出し可能
    """
    df = generate_dummy_seatlog()
    insert_seatlog(df)
