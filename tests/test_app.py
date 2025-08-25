import pytest
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # プロジェクトルートを追加

from main_routes import is_reservation_conflict
from db import add_reservation, get_connection   # ← ここで必要な関数をimport


def test_add_reservation():
    name = "テスト太郎"
    date = "2030-01-01"
    time = "10:00"

    # まず重複していないことを確認
    assert not is_reservation_conflict(date, time)

    # 予約を追加
    add_reservation(name, date, time)

    # 重複チェックでTrueになること
    assert is_reservation_conflict(date, time)

    # 後片付け
    conn = get_connection()
    conn.execute("DELETE FROM reservations WHERE name=?", (name,))
    conn.commit()
    conn.close()


def test_edit_reservation_conflict():
    # テスト用データ作成
    add_reservation("A", "2030-01-02", "11:00")
    add_reservation("B", "2030-01-02", "12:00")

    # BのIDを取得
    conn = get_connection()
    b_id = conn.execute("SELECT id FROM reservations WHERE name='B'").fetchone()["id"]
    conn.close()

    # 重複日時をチェック
    conn = get_connection()   # 新しい接続を開く
    conflict = conn.execute(
        "SELECT id FROM reservations WHERE date=? AND time=? AND id!=?",
        ("2030-01-02", "11:00", b_id)
    ).fetchone()
    conn.close()

    assert conflict is not None

    # 後片付け
    conn = get_connection()
    conn.execute("DELETE FROM reservations WHERE date='2030-01-02'")
    conn.commit()
    conn.close()
