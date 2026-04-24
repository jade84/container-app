# ===== IMPORT =====
from flask import Flask, render_template, request, redirect, send_file
from datetime import date
import json
from flask import session
import os

from dotenv import load_dotenv
load_dotenv()

# services
from services.container_service import (
    get_container_list,
    get_shipping_lines,
    find_container,
    export_container,
    create_container,
    get_container_history
)

from db import query_one, query_all, execute

# ===== APP =====
app = Flask(__name__)
app.secret_key = "supersecretkey"
# ===== FILTER =====
@app.template_filter('from_json')
def from_json(value):
    return json.loads(value)

# ===== HOME =====
@app.route('/')
def home():
    return redirect('/list')

# ===== LOGIN =====
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = query_one(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (request.form['username'], request.form['password'])
        )

        if user:
            session['user'] = user['username']
            return redirect('/list')

        return render_template('login.html', error="Sai tài khoản!")

    return render_template('login.html')

# ===== LOGOUT =====
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ===== Check login =====
@app.before_request
def check_login():
    if request.endpoint in ['login', 'static']:
        return

    if 'user' not in session:
        return redirect('/login')
    
# ===== IN =====
@app.route('/in', methods=['GET', 'POST'])
def container_in():
    lines = query_all("SELECT * FROM shipping_lines ORDER BY code")

    if request.method == 'POST':
        result = create_container(
            request.form['container_no'],
            request.form['shipping_line'],
            request.form['size'],
            request.form['status'],
            request.form['date_in']
        )

        if 'error' in result:
            return render_template('in.html',
                error=result['error'],
                form=request.form,
                today=date.today().strftime('%Y-%m-%d'),
                lines=lines
            )

        return redirect('/list')

    return render_template('in.html',
        form={},
        today=date.today().strftime('%Y-%m-%d'),
        lines=lines
    )

# ===== LIST =====
@app.route('/list')
def container_list():
    query = request.args.get('q')
    line = request.args.get('line')

    data = get_container_list(query, line)
    lines = get_shipping_lines()

    return render_template('list.html',
        title="Tồn bãi",
        date_column='Date In',
        containers=data,
        q=query,
        line=line,
        lines=lines
    )

# ===== OUT =====
@app.route('/out', methods=['GET', 'POST'])
def container_out():
    data = None

    if request.method == 'POST':
        container_no = request.form['container_no'].upper()

        if 'booking_no' in request.form:
            result = export_container(
                container_no,
                request.form['booking_no'],
                request.form['customer_name']
            )

            if 'error' in result:
                return render_template('out.html', error=result['error'])

            return render_template('out.html', success=result['success'])

        data = find_container(container_no)

    return render_template('out.html', data=data)

# ===== HISTORY =====
@app.route('/history')
def container_history():
    data = get_container_history()

    return render_template('list.html',
        containers=data,
        title="Xuất bãi",
        date_column='Date Out',
        q=None,
        line=None,
        lines=[]
    )

# ===== HISTORY =====
@app.route('/logs')
def view_logs():
    logs = query_all("""
        SELECT 
            l.*, c.container_no
        FROM container_logs l
        LEFT JOIN containers c ON l.container_id = c.id
        ORDER BY l.created_at DESC
    """)

    return render_template('logs.html', logs=logs)