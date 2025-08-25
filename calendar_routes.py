from flask import Blueprint, request, render_template
import calendar
from datetime import date
from db import get_connection

calendar_routes = Blueprint('calendar_routes', __name__)

@calendar_routes.route('/calendar')
def calendar_view():
    # クエリパラメータから年・月を取得
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    today = date.today()
    if not year or not month:
        year = today.year
        month = today.month

    # 月カレンダー（日曜始まり）
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)

    # DBから予約データを取得（日付・時間順にソート）
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT name, date, time FROM reservations ORDER BY date, time'
    )
    reservations_raw = cursor.fetchall()
    conn.close()

    # 日付ごとの予約データに整形
    reservations = {}
    for name, date_str, time_str in reservations_raw:
        if date_str not in reservations:
            reservations[date_str] = []
        reservations[date_str].append((time_str, name))

    # 前の月・次の月を計算（年またぎ対応）
    prev_month = month - 1 or 12
    prev_year = year - 1 if month == 1 else year
    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year

    return render_template(
        'calendar.html',
        year=year,
        month=month,
        month_days=month_days,
        reservations=reservations,
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month
    )
