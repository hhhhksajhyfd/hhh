
from flask import Flask, render_template, request, redirect, url_for, session
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'secret-key'
app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

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
        row = c.fetchone()
        conn.close()
        if row and check_password_hash(row[0], password):
            session['user'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='로그인 실패!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

def init_db():
    if os.path.exists("employees.db"):
        os.remove("employees.db")
    conn = sqlite3.connect("employees.db")
    c = conn.cursor()
    c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)")
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("황은영", generate_password_hash("871015")))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    print("▶▶▶ __main__ 블록 실행됨")
    init_db()
    print("✅ 사용자 등록 완료 후 서버 시작")
    app.run(host="0.0.0.0", port=10000)
