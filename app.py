
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, openpyxl, os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.jinja_env.auto_reload = True
app.jinja_env.cache = {}
app.config['TEMPLATES_AUTO_RELOAD'] = True

def get_employee_info_from_excel(username):
    try:
        wb = openpyxl.load_workbook("라온 연차대장 (25년4월1).xlsx", data_only=True)
        ws = wb.active
        for row in ws.iter_rows(min_row=2):
            if row[0].value and str(row[0].value).strip() == username.strip():
                return {
                    "입사일": row[4].value,
                    "총부여": row[6].value,
                    "총사용": row[7].value,
                    "잔여": row[8].value
                }
    except Exception as e:
        print("엑셀 읽기 오류:", e)
    return None

def get_worklog_from_excel(username):
    try:
        wb = openpyxl.load_workbook("라온 연차대장 (25년4월1).xlsx", data_only=True)
        ws = wb.active
        for row in ws.iter_rows(min_row=2):
            if row[0].value and str(row[0].value).strip() == username.strip():
                return {
                    "출근일수": row[10].value,
                    "지각": row[11].value,
                    "결근": row[12].value,
                    "외출": row[13].value,
                    "조퇴": row[14].value
                }
    except Exception as e:
        print("근로내역 엑셀 읽기 오류:", e)
    return None

def get_colored_leave_notes(username):
    try:
        wb = openpyxl.load_workbook("라온 연차대장 (25년4월1).xlsx")
        ws = wb.active
        notes = []
        for row in ws.iter_rows(min_row=2):
            if row[0].value and str(row[0].value).strip() == username.strip():
                for cell in row:
                    fill = cell.fill
                    if fill.patternType == 'solid' and fill.start_color.rgb == 'FFFFFF00' and cell.value:
                        notes.append(str(cell.value))
                break
        return notes
    except Exception as e:
        print("색상 필터 연차 추출 오류:", e)
    return []

def init_db():
    if os.path.exists("employees.db"):
        os.remove("employees.db")
    conn = sqlite3.connect("employees.db")
    c = conn.cursor()
    c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)")
    conn.commit()
    conn.close()

def create_users_from_excel():
    wb = openpyxl.load_workbook("직원명부.xlsx", data_only=True)
    ws = wb["Sheet1"]
    conn = sqlite3.connect("employees.db")
    c = conn.cursor()
    for row in ws.iter_rows(min_row=2):
        name = row[0].value
        birth = row[1].value
        if name and birth:
            password = str(int(birth)).zfill(6) if isinstance(birth, (int, float)) else str(birth).strip()
            try:
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (name, generate_password_hash(password)))
            except sqlite3.IntegrityError:
                continue
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['user'])

@app.route('/연차')
def leave():
    if 'user' not in session:
        return redirect(url_for('login'))
    info = get_employee_info_from_excel(session['user'])
    notes = get_colored_leave_notes(session['user'])
    return render_template('leave.html', username=session['user'], info=info, notes=notes)

@app.route('/근로내역')
def worklog():
    if 'user' not in session:
        return redirect(url_for('login'))
    worklog_info = get_worklog_from_excel(session['user'])
    return render_template('worklog.html', username=session['user'], worklog=worklog_info)

@app.route('/명세표')
def payslip():
    if 'user' not in session:
        return redirect(url_for('login'))
    return f"{session['user']}님의 급여명세표 확인 페이지 (추후 구현)"

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username, password = request.form['username'], request.form['password']
        conn = sqlite3.connect("employees.db")
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username=?", (username,))
        result = c.fetchone()
        conn.close()
        if result and check_password_hash(result[0], password):
            session['user'] = username
            return redirect(url_for('index'))
        else:
            return render_template("login.html", error="로그인 실패!")
    return render_template("login.html", error=None)

if __name__ == "__main__":
    init_db()
    create_users_from_excel()
    app.run()
