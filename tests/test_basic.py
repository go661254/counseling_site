import sys, os, sqlite3
import pytest

# プロジェクトのルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db import get_connection, add_reservation, delete_reservation_by_id
from db import find_reservations_by_date  # ← 検索関数がある前提
from db import update_reservation         # ← 更新関数がある前提

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """テスト前後にDBを初期化"""
    conn = get_connection()
    conn.execute("DELETE FROM reservations")
    conn.commit()
    conn.close()
    yield
    conn = get_connection()
    conn.execute("DELETE FROM reservations")
    conn.commit()
    conn.close()


def test_add_and_find_reservation():
    add_reservation("テスト太郎", "2030-01-01", "10:00")
    results = find_reservations_by_date("2030-01-01")
    assert len(results) == 1
    assert results[0]["name"] == "テスト太郎"


def test_update_reservation():
    # 追加
    add_reservation("修正前", "2030-01-02", "11:00")

    conn = get_connection()
    row = conn.execute("SELECT * FROM reservations WHERE date='2030-01-02'").fetchone()
    conn.close()

    # 更新
    update_reservation(row["id"], "修正後", "2030-01-02", "12:00")

    conn = get_connection()
    updated = conn.execute("SELECT * FROM reservations WHERE id=?", (row["id"],)).fetchone()
    conn.close()

    assert updated["name"] == "修正後"
    assert updated["time"] == "12:00"


def test_delete_reservation():
    add_reservation("削除対象", "2030-01-03", "13:00")

    conn = get_connection()
    row = conn.execute("SELECT * FROM reservations WHERE name='削除対象'").fetchone()
    conn.close()

    delete_reservation_by_id(row["id"])

    conn = get_connection()
    deleted = conn.execute("SELECT * FROM reservations WHERE id=?", (row["id"],)).fetchone()
    conn.close()

    assert deleted is None
