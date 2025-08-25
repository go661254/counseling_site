# カウンセリング予約システム 詳細設計書

## 1. モジュール構成

### 1.1 ファイル構成
```
counseling_site/
├── app.py              # アプリケーションのエントリーポイント
├── routes.py           # ルーティング処理
├── db.py              # データベース操作
├── validators.py      # バリデーション処理
├── static/
│   └── style.css      # スタイルシート
├── templates/         # HTMLテンプレート
│   ├── index.html     # 予約フォーム
│   ├── confirm.html   # 確認画面
│   ├── complete.html  # 完了画面
│   └── list.html      # 予約一覧
└── tests/            # テストコード
    ├── test_routes.py
    └── test_validators.py
```

## 2. モジュール詳細

### 2.1 app.py
```python
from flask import Flask
from routes import routes

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # CSRF対策
app.register_blueprint(routes)

if __name__ == '__main__':
    app.run(debug=True)
```

### 2.2 db.py
```python
import sqlite3
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = 'reservations.db'):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL
                )
            ''')
            conn.commit()

    def add_reservation(self, name: str, date: str, time: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO reservations (name, date, time) VALUES (?, ?, ?)',
                (name, date, time)
            )
            conn.commit()
            return True

    def get_reservations(self) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, date, time FROM reservations ORDER BY date, time')
            rows = cursor.fetchall()
            return [
                {'id': row[0], 'name': row[1], 'date': row[2], 'time': row[3]}
                for row in rows
            ]

    def delete_reservation(self, reservation_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM reservations WHERE id = ?', (reservation_id,))
            conn.commit()
            return cursor.rowcount > 0

    def check_duplicate(self, date: str, time: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT COUNT(*) FROM reservations WHERE date = ? AND time = ?',
                (date, time)
            )
            return cursor.fetchone()[0] > 0
```

### 2.3 validators.py
```python
from datetime import datetime
from typing import Optional, Dict

class ReservationValidator:
    @staticmethod
    def validate_reservation(name: str, date: str, time: str) -> Optional[str]:
        # 必須チェック
        if not all([name, date, time]):
            return "すべての項目を入力してください。"

        # 名前のバリデーション
        if len(name.strip()) == 0:
            return "お名前に空白のみは使用できません。"
        if len(name) > 50:
            return "お名前は50文字以内で入力してください。"

        # 日時のバリデーション
        try:
            reservation_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            if reservation_datetime < datetime.now():
                return "過去の日時は予約できません。"
        except ValueError:
            return "日付または時間の形式が正しくありません。"

        return None  # バリデーションOK
```

### 2.4 routes.py
```python
from flask import Blueprint, request, render_template, redirect, url_for
from datetime import date
from db import Database
from validators import ReservationValidator

routes = Blueprint('routes', __name__)
db = Database()
validator = ReservationValidator()

@routes.route('/')
def index():
    today = date.today().isoformat()
    return render_template('index.html', min_date=today)

@routes.route('/confirm', methods=['POST'])
def confirm():
    name = request.form.get('name')
    reserve_date = request.form.get('date')
    reserve_time = request.form.get('time')

    # バリデーション
    error = validator.validate_reservation(name, reserve_date, reserve_time)
    if error:
        return render_template('index.html',
                             min_date=date.today().isoformat(),
                             name=name,
                             reserve_date=reserve_date,
                             reserve_time=reserve_time,
                             error=error)

    # 重複チェック
    if db.check_duplicate(reserve_date, reserve_time):
        return render_template('index.html',
                             min_date=date.today().isoformat(),
                             name=name,
                             reserve_date=reserve_date,
                             reserve_time=reserve_time,
                             error="その日時はすでに予約されています。")

    return render_template('confirm.html',
                         name=name,
                         reserve_date=reserve_date,
                         reserve_time=reserve_time)

@routes.route('/complete', methods=['POST'])
def complete():
    name = request.form.get('name')
    reserve_date = request.form.get('date')
    reserve_time = request.form.get('time')

    # 再度バリデーション
    error = validator.validate_reservation(name, reserve_date, reserve_time)
    if error:
        return redirect(url_for('routes.index'))

    # 予約登録
    if db.add_reservation(name, reserve_date, reserve_time):
        return render_template('complete.html',
                             name=name,
                             reserve_date=reserve_date,
                             reserve_time=reserve_time)
    else:
        return "予約登録に失敗しました。", 500

@routes.route('/list')
def reservation_list():
    reservations = db.get_reservations()
    return render_template('list.html', reservations=reservations)

@routes.route('/delete/<int:reservation_id>')
def delete_reservation(reservation_id):
    if db.delete_reservation(reservation_id):
        return redirect(url_for('routes.list'))
    else:
        return "予約の削除に失敗しました。", 500
```

## 3. テンプレート詳細

### 3.1 index.html
```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>カウンセリング予約</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="container">
        <h1>カウンセリング予約</h1>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}

        <form method="POST" action="{{ url_for('routes.confirm') }}">
            <div class="form-group">
                <label for="name">お名前:</label>
                <input type="text" id="name" name="name" required maxlength="50" 
                       value="{{ name or '' }}">
            </div>

            <div class="form-group">
                <label for="date">予約日:</label>
                <input type="date" id="date" name="date" required 
                       min="{{ min_date }}" value="{{ reserve_date or '' }}">
            </div>

            <div class="form-group">
                <label for="time">時間:</label>
                <input type="time" id="time" name="time" required 
                       value="{{ reserve_time or '' }}">
            </div>

            <button type="submit" class="btn">確認する</button>
        </form>
    </div>
</body>
</html>
```

### 3.2 list.html
```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>予約一覧</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="container">
        <h1>予約一覧</h1>
        
        {% if reservations %}
        <table class="reservation-table">
            <thead>
                <tr>
                    <th>お名前</th>
                    <th>予約日</th>
                    <th>時間</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
                {% for reservation in reservations %}
                <tr>
                    <td>{{ reservation.name }}</td>
                    <td>{{ reservation.date }}</td>
                    <td>{{ reservation.time }}</td>
                    <td>
                        <a href="{{ url_for('routes.delete_reservation', reservation_id=reservation.id) }}"
                           class="btn btn-delete"
                           onclick="return confirm('この予約をキャンセルしますか？')">
                            キャンセル
                        </a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p>予約はありません。</p>
        {% endif %}

        <a href="{{ url_for('routes.index') }}" class="btn btn-back">戻る</a>
    </div>
</body>
</html>
```

### 3.3 style.css
```css
/* 共通スタイル */
body {
    font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
}

.container {
    max-width: 800px;
    margin: 2rem auto;
    padding: 2rem;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

h1 {
    color: #333;
    margin-bottom: 2rem;
    text-align: center;
}

/* フォーム要素 */
.form-group {
    margin-bottom: 1.5rem;
}

label {
    display: block;
    margin-bottom: 0.5rem;
    color: #555;
}

input[type="text"],
input[type="date"],
input[type="time"] {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
}

/* ボタン */
.btn {
    display: inline-block;
    padding: 0.5rem 1rem;
    background-color: #007bff;
    color: #fff;
    text-decoration: none;
    border-radius: 4px;
    border: none;
    cursor: pointer;
    font-size: 1rem;
}

.btn:hover {
    background-color: #0056b3;
}

.btn-back {
    background-color: #6c757d;
}

.btn-delete {
    background-color: #dc3545;
}

/* エラーメッセージ */
.error {
    color: #dc3545;
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    padding: 0.75rem;
    margin-bottom: 1rem;
    border-radius: 4px;
}

/* テーブル */
.reservation-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 2rem;
}

.reservation-table th,
.reservation-table td {
    padding: 0.75rem;
    border: 1px solid #dee2e6;
}

.reservation-table th {
    background-color: #f8f9fa;
    font-weight: bold;
}

/* レスポンシブ対応 */
@media (max-width: 768px) {
    .container {
        margin: 1rem;
        padding: 1rem;
    }

    .reservation-table {
        display: block;
        overflow-x: auto;
    }
}
```

## 4. 例外処理

### 4.1 データベースエラー
```python
class DatabaseError(Exception):
    pass

class Database:
    def add_reservation(self, name: str, date: str, time: str) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO reservations (name, date, time) VALUES (?, ?, ?)',
                    (name, date, time)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            raise DatabaseError(f"予約の追加に失敗しました: {str(e)}")
```

## 5. ユニットテスト

### 5.1 test_validators.py
```python
import unittest
from datetime import datetime, timedelta
from validators import ReservationValidator

class TestReservationValidator(unittest.TestCase):
    def setUp(self):
        self.validator = ReservationValidator()

    def test_valid_reservation(self):
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        error = self.validator.validate_reservation(
            name="山田太郎",
            date=tomorrow,
            time="14:00"
        )
        self.assertIsNone(error)

    def test_empty_name(self):
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        error = self.validator.validate_reservation(
            name="",
            date=tomorrow,
            time="14:00"
        )
        self.assertIsNotNone(error)
        self.assertIn("すべての項目を入力", error)

    def test_past_date(self):
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        error = self.validator.validate_reservation(
            name="山田太郎",
            date=yesterday,
            time="14:00"
        )
        self.assertIsNotNone(error)
        self.assertIn("過去の日時", error)
```

## 6. セキュリティ実装

### 6.1 XSS対策
- Flaskのテンプレートエンジン（Jinja2）のエスケープ機能を使用
- HTMLの属性値はダブルクォートで囲む

### 6.2 CSRF対策
- FlaskのCSRF保護機能を使用
- フォームにCSRFトークンを埋め込む

### 6.3 SQLインジェクション対策
- プリペアドステートメントの使用
- パラメータバインディング

## 7. ロギング実装

### 7.1 ログ設定
```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    logger = logging.getLogger('counseling_site')
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=1024 * 1024,
        backupCount=5
    )
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
```

## 8. パフォーマンス最適化

### 8.1 データベースインデックス
```sql
CREATE INDEX idx_reservations_date_time ON reservations(date, time);
```

### 8.2 キャッシュ設定
- 静的ファイル（CSS, JavaScript）のキャッシュヘッダー設定
```python
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1年
```

## 9. デプロイメント手順

1. 環境設定
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. データベース初期化
```python
from db import Database
db = Database()
db.init_db()
```

3. アプリケーション起動
```bash
python app.py
```

## 10. 保守・運用

### 10.1 バックアップスクリプト
```python
import shutil
from datetime import datetime

def backup_database():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2(
        'reservations.db',
        f'backups/reservations_{timestamp}.db'
    )
```

### 10.2 監視項目
- データベース容量
- アクセスログ
- エラーログ
- レスポンス時間
