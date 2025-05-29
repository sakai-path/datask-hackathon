# =============================================================================
# seatlog_dummy.py - SeatLog テストデータ生成＆挿入
# -----------------------------------------------------------------------------
# このモジュールは初期データ確認用にのみ使用します。
# 2025年1月〜5月の範囲で、ランダムに社員が席に着いたログを生成します。
# =============================================================================

import random
from datetime import datetime, timedelta
import pandas as pd
import sqlalchemy as sa
from core.db import engine

def generate_dummy_seatlog(num_entries=300) -> pd.DataFrame:
    """ランダムな着席データ（CheckIn/Out）を生成"""
    seat_ids = list(range(1, 21))  # SeatId 1〜20
    emp_codes = [f"E{10000 + i:03}" for i in range(1, 51)]  # E10001〜E10050
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 5, 31)

    data = []
    for _ in range(num_entries):
        seat_id = random.choice(seat_ids)
        emp_code = random.choice(emp_codes)

        # ランダム日付・時間
        day = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
        check_in = datetime.combine(day.date(), datetime.strptime("09:00", "%H:%M").time()) + timedelta(minutes=random.randint(0, 60))
        check_out = check_in + timedelta(hours=random.randint(6, 9), minutes=random.randint(0, 59))

        data.append({
            "SeatId": seat_id,
            "EmpCode": emp_code,
            "CheckIn": check_in,
            "CheckOut": check_out
        })

    return pd.DataFrame(data)

def insert_seatlog(df: pd.DataFrame):
    """DataFrameからSeatLogにINSERT"""
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
    """ダミーデータ生成＆挿入をまとめて実行"""
    df = generate_dummy_seatlog(500)
    insert_seatlog(df)
