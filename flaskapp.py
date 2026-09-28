import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB_NAME = os.path.join(app.root_path, 'users.db')

def init_db():
    """Initialize SQLite database and create users table if it does not exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL,
            email TEXT NOT NULL,
            address TEXT NOT NULL,
            filename TEXT,
            word_count INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return redirect(url_for('register_page'))

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        address = request.form['address']

        filename = None
        word_count = 0

        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        word_count = len(content.split())
                except Exception:
                    word_count = 0

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO users (username, password, firstname, lastname, email, address, filename, word_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, password, firstname, lastname, email, address, filename, word_count))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Username already exists. Please try registering with a different username.", 400
        conn.close()

        return redirect(url_for('profile', username=username))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Re-login route to authenticate stored users."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            return redirect(url_for('profile', username=username))
        else:
            return render_template('login.html', error="Invalid username or password.")

    return render_template('login.html')

@app.route('/profile/<username>')
def profile(username):
    """Display user profile details, file word count, and download link."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()

    if not user:
        return "User not found", 404

    user_data = {
        'id': user[0],
        'username': user[1],
        'password': user[2],
        'firstname': user[3],
        'lastname': user[4],
        'email': user[5],
        'address': user[6],
        'filename': user[7],
        'word_count': user[8]
    }

    return render_template('profile.html', user=user_data)

@app.route('/download/<filename>')
def download_file(filename):
    """Serve the uploaded file for download."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
