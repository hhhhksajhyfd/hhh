from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import openpyxl
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.jinja_env.auto_reload = True
app.jinja_env.cache = {}
app.config['TEMPLATES_AUTO_RELOAD'] = True

def init_db():
    if os.path.exists('employees.db'):
        os.remove('employees.db')
    conn = sqlite3.connect('employees.db')
    c = conn.cursor()
    c.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def create_users_from_excel():
    try:
        wb = openpyxl.load_workbook("직원명부.xlsx", data_only=True)
        ws = wb["Sheet1"]
        conn = sqlite3.connect('employees.db')
        c = conn.cursor()
        for row in ws.iter_rows(min_row=2):
            name = row[0].value
            birth = row[1].value
            if name and birth:
                username = str(name).strip()
                if isinstance(birth, (int, float)):
                    password = str(int(birth)).zfill(6)
                elif isinstance(birth, datetime):
                    password = birth.strftime("%y%m%d")
                else:
                    password = str(birth).strip()
                hashed_pw = generate_password_hash(password)
                try:
                    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
                except sqlite3.IntegrityError:
                    pass
        conn.commit()
        conn.close()
        wb.close()
    except Exception as e:
        raise Exception(f"엑셀 사용자 등록 오류: {e}")

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['user'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('employees.db')
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        conn.close()
        if result and check_password_hash(result[0], password):
            session['user'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='로그인 실패!')
    return render_template('login.html', error=None)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    create_users_from_excel()
    app.run(host='0.0.0.0', port=10000)
