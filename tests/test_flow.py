import pytest
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # 1階層上を追加

from db import (
    get_connection,
    add_reservation,
    find_reservations_by_date,
    update_reservation,
    delete_reservation_by_id,
    is_reservation_conflict
)

def test_reservation_flow():
    # Step 1: 予約追加
    add_reservation("テスト太郎", "2030-01-01", "10:00")
    add_reservation("テスト花子", "2030-01-01", "11:00")

    # Step 2: 一覧取得
    rows = find_reservations_by_date("2030-01-01")
    assert len(rows) == 2
    assert rows[0]["name"] == "テスト太郎"
    assert rows[1]["name"] == "テスト花子"

    # Step 3: 更新（太郎の時間を変更）
    conn = get_connection()
    res_id = conn.execute(
        "SELECT id FROM reservations WHERE name='テスト太郎'"
    ).fetchone()["id"]
    conn.close()

    update_reservation(res_id, "テスト太郎", "2030-01-01", "12:00")
    rows = find_reservations_by_date("2030-01-01")
    assert any(r["time"] == "12:00" for r in rows)

    # Step 4: 重複チェック
    assert is_reservation_conflict("2030-01-01", "12:00")

    # Step 5: 削除
    delete_reservation_by_id(res_id)
    rows = find_reservations_by_date("2030-01-01")
    assert len(rows) == 1  # 花子だけ残る

    # Step 6: 後片付け（花子も削除）
    conn = get_connection()
    conn.execute("DELETE FROM reservations WHERE date='2030-01-01'")
    conn.commit()
    conn.close()
