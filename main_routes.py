from flask import Blueprint, request, render_template, redirect, url_for, Response, session
from datetime import date, datetime
from functools import wraps
from db import get_connection, delete_reservation_by_id, add_reservation, is_reservation_conflict

main_routes = Blueprint('main_routes', __name__, template_folder='templates')

# ログイン必須のデコレータ
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:  # ログインしていない場合
            return redirect(url_for("main_routes.login"))
        return f(*args, **kwargs)
    return decorated_function


# パスワードのハッシュ化用
from werkzeug.security import generate_password_hash, check_password_hash

# テスト用ユーザー（初期は1ユーザー）
# "admin" のパスワードは "password123" になります（学習用）。本番ではDBに移行してください。
USERS = {
    "admin": generate_password_hash("password123")
}

# --- 共通関数 ---
def get_db_connection():
    conn = get_connection()
    conn.row_factory = None  # row_factoryはNoneか適宜設定してください
    return conn

def validate_reservation_input(name, reserve_date, reserve_time, allow_past=False):
    if not name or not reserve_date or not reserve_time:
        return "すべての項目を入力してください。"
    if name.strip() == "":
        return "お名前に空白のみは使用できません。"
    if len(name) > 50:
        return "お名前は50文字以内で入力してください。"
    try:
        reserve_datetime = datetime.strptime(f"{reserve_date} {reserve_time}", "%Y-%m-%d %H:%M")
        if not allow_past and reserve_datetime < datetime.now():
            return "過去の日時には予約できません。"
    except ValueError:
        return "日付または時間の形式が正しくありません。"
    return None

# --- ルーティング ---
@main_routes.route('/')
def index():
    return render_template('index.html', min_date=date.today().isoformat())

@main_routes.route('/confirm', methods=['POST'])
def confirm():
    name = request.form.get('name')
    reserve_date = request.form.get('date')
    reserve_time = request.form.get('time')

    error = validate_reservation_input(name, reserve_date, reserve_time)
    if error:
        return render_template('index.html', name=name, reserve_date=reserve_date,
                               reserve_time=reserve_time, error=error,
                               min_date=date.today().isoformat())

    return render_template('confirm.html', name=name, reserve_date=reserve_date, reserve_time=reserve_time)

@main_routes.route('/complete', methods=['POST'])
def complete():
    name = request.form.get('name')
    reserve_date = request.form.get('date')
    reserve_time = request.form.get('time')

    # 重複チェック
    if is_reservation_conflict(reserve_date, reserve_time):
        return render_template('confirm.html', name=name,
                               reserve_date=reserve_date,
                               reserve_time=reserve_time,
                               error='すでに同じ日時に予約があります。')

    # 予約登録処理
    conn = get_db_connection()
    conn.execute('INSERT INTO reservations (name, date, time) VALUES (?, ?, ?)',
                 (name, reserve_date, reserve_time))
    conn.commit()
    conn.close()

    return render_template('complete.html', name=name,
                           reserve_date=reserve_date,
                           reserve_time=reserve_time)

@main_routes.route('/list')
def reservation_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reservations ORDER BY date, time')
    rows = cursor.fetchall()
    conn.close()

    reservations = []
    for r in rows:
        reservations.append({
            'id': r[0],
            'name': r[1],
            'date': r[2],
            'time': r[3]
        })

    return render_template('list.html', reservations=reservations)

@main_routes.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = get_db_connection()

    if request.method == 'POST':
        name = request.form['name']
        reserve_date = request.form['date']
        reserve_time = request.form['time']

        # 入力バリデーション（過去の日時も不可）
        error = validate_reservation_input(name, reserve_date, reserve_time)
        if error:
            conn.close()
            return render_template(
                'edit.html',
                reservation_id=id,
                name=name,
                reserve_date=reserve_date,
                reserve_time=reserve_time,
                error=error,
                min_date=date.today().isoformat()
            )

        # 重複チェック（自分自身以外）
        conflict = conn.execute(
            'SELECT id FROM reservations WHERE date = ? AND time = ? AND id != ?',
            (reserve_date, reserve_time, id)
        ).fetchone()
        if conflict:
            conn.close()
            return render_template(
                'edit.html',
                reservation_id=id,
                name=name,
                reserve_date=reserve_date,
                reserve_time=reserve_time,
                error='同じ日時に他の予約があります。',
                min_date=date.today().isoformat()
            )

        # 更新処理
        conn.execute(
            'UPDATE reservations SET name = ?, date = ?, time = ? WHERE id = ?',
            (name, reserve_date, reserve_time, id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('main_routes.reservation_list'))

    # GETの場合（フォーム表示）
    reservation = conn.execute(
        'SELECT name, date, time FROM reservations WHERE id = ?',
        (id,)
    ).fetchone()
    conn.close()

    if reservation:
        return render_template(
            'edit.html',
            reservation_id=id,
            name=reservation[0],
            reserve_date=reservation[1],
            reserve_time=reservation[2],
            min_date=date.today().isoformat()
        )
    else:
        return '予約が見つかりませんでした。', 404

@main_routes.route('/delete/<int:reservation_id>', methods=['GET'])
def delete_reservation(reservation_id):
    delete_reservation_by_id(reservation_id)
    return redirect(url_for('main_routes.reservation_list'))

@main_routes.route('/search_by_date')
def search_by_date():
    search_date = request.args.get('search_date')
    if not search_date:
        return redirect(url_for('main_routes.reservation_list'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM reservations WHERE date = ? ORDER BY time',
        (search_date,)
    )
    rows = cursor.fetchall()
    conn.close()

    reservations = []
    for r in rows:
        reservations.append({
            'id': r[0],
            'name': r[1],
            'date': r[2],
            'time': r[3]
        })

    return render_template('list.html', reservations=reservations)


@main_routes.route('/search_name')
def search_by_name():
    search_name = request.args.get('search_name')
    if not search_name:
        return redirect(url_for('main_routes.reservation_list'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM reservations WHERE name LIKE ? ORDER BY date, time",
        (f'%{search_name}%',)
    )
    rows = cursor.fetchall()
    conn.close()

    # 辞書型に変換（必要に応じて）
    reservations = []
    for r in rows:
        reservations.append({
            'id': r[0],
            'name': r[1],
            'date': r[2],
            'time': r[3]
        })

    return render_template('list.html', reservations=reservations)

@main_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # ユーザー存在チェック
        if username in USERS and check_password_hash(USERS[username], password):
            session['user'] = username  # ログイン状態にする
            return redirect(url_for('main_routes.index'))
        else:
            return render_template('login.html', error='ユーザー名またはパスワードが違います')

    return render_template('login.html')

@main_routes.route('/logout')
def logout():
    session.pop("user", None)  # セッションから削除
    return redirect(url_for("main_routes.login"))
