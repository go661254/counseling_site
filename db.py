import sqlite3

DB_PATH = "database.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def add_reservation(name, date, time):
    conn = get_connection()
    conn.execute(
        "INSERT INTO reservations (name, date, time) VALUES (?, ?, ?)",
        (name, date, time)
    )
    conn.commit()
    conn.close()


def find_reservations_by_date(date):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reservations WHERE date=? ORDER BY time",
        (date,)
    ).fetchall()
    conn.close()
    return rows


def update_reservation(reservation_id, name, date, time):
    conn = get_connection()
    conn.execute(
        "UPDATE reservations SET name=?, date=?, time=? WHERE id=?",
        (name, date, time, reservation_id)
    )
    conn.commit()
    conn.close()


def delete_reservation_by_id(reservation_id):
    conn = get_connection()
    conn.execute("DELETE FROM reservations WHERE id=?", (reservation_id,))
    conn.commit()
    conn.close()

def is_reservation_conflict(date, time):
    """同じ日時の予約が存在するかを確認する"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM reservations WHERE date=? AND time=?",
        (date, time)
    )
    conflict = cursor.fetchone()
    conn.close()
    return conflict is not None
