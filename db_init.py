import sqlite3

# DB初期化関数
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # reservationsテーブルを作成（存在しない場合のみ）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            menu TEXT,
            note TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ database.db に 'reservations' テーブルを作成（または存在確認）しました。")

# スクリプトとして直接実行されたときだけinit_dbを呼び出す
if __name__ == "__main__":
    init_db()
