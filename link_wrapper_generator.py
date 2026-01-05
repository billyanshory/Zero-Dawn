import sqlite3
import string
import random
import os
from flask import Flask, request, render_template_string, redirect, url_for

app = Flask(__name__)
app.secret_key = "unique_generator_secret"
DB_NAME = "links.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alias TEXT UNIQUE NOT NULL,
                    original_url TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def generate_random_alias(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# --- HTML TEMPLATES ---

HTML_INDEX = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unique Text Generator | Link Wrapper</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --text-color: #c9d1d9;
            --accent-color: #58a6ff;
            --border-color: #30363d;
            --success-color: #2ea043;
        }
        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'JetBrains Mono', monospace;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .container {
            background-color: var(--card-bg);
            padding: 2rem;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            width: 100%;
            max-width: 600px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        h1 {
            color: var(--accent-color);
            margin-top: 0;
            text-align: center;
            font-size: 1.5rem;
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1rem;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: bold;
            color: var(--text-color);
        }
        input[type="text"], input[type="url"] {
            width: 100%;
            padding: 12px;
            background-color: #0d1117;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: #fff;
            font-family: inherit;
            box-sizing: border-box;
            transition: border-color 0.2s;
        }
        input:focus {
            outline: none;
            border-color: var(--accent-color);
        }
        .btn {
            display: block;
            width: 100%;
            padding: 12px;
            background-color: var(--success-color);
            color: white;
            border: none;
            border-radius: 6px;
            font-family: inherit;
            font-weight: bold;
            cursor: pointer;
            transition: background-color 0.2s;
            font-size: 1rem;
        }
        .btn:hover {
            background-color: #2c974b;
        }
        .result-box {
            margin-top: 2rem;
            padding: 1rem;
            background-color: rgba(46, 160, 67, 0.1);
            border: 1px solid var(--success-color);
            border-radius: 6px;
            text-align: center;
        }
        .result-link {
            color: var(--accent-color);
            font-size: 1.2rem;
            word-break: break-all;
            text-decoration: none;
            display: block;
            margin: 10px 0;
            padding: 10px;
            background: #0d1117;
            border-radius: 4px;
        }
        .copy-hint {
            font-size: 0.8rem;
            color: #8b949e;
        }
        .error {
            color: #ff7b72;
            margin-bottom: 1rem;
            text-align: center;
        }
        .footer {
            margin-top: 2rem;
            text-align: center;
            font-size: 0.8rem;
            color: #8b949e;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>LINK WRAPPER GENERATOR</h1>

        {% if error %}
        <div class="error">>> ERROR: {{ error }}</div>
        {% endif %}

        {% if generated_link %}
        <div class="result-box">
            <div>>> LINK GENERATED SUCCESSFULLY <<</div>
            <a href="{{ generated_link }}" class="result-link" target="_blank">{{ generated_link }}</a>
            <div class="copy-hint">Copy this unique text link and share it anywhere.</div>
            <br>
            <a href="/" style="color: var(--text-color); font-size: 0.9rem;">[ Generate Another ]</a>
        </div>
        {% else %}
        <form action="/generate" method="post">
            <div class="form-group">
                <label for="original_url">>> TARGET URL (LINK ASLI)</label>
                <input type="url" id="original_url" name="original_url" placeholder="https://example.com/very-long-link..." required>
            </div>

            <div class="form-group">
                <label for="alias">>> UNIQUE TEXT (TEKS KHUSUS)</label>
                <input type="text" id="alias" name="alias" placeholder="e.g. Helena.com (Optional)">
                <div style="font-size: 0.8rem; color: #8b949e; margin-top: 5px;">* Leave empty for auto-generated code</div>
            </div>

            <button type="submit" class="btn">:: WRAP LINK ::</button>
        </form>
        {% endif %}

        <div class="footer">
            SYSTEM STATUS: ONLINE<br>
            SECURE LINK WRAPPER PROTOCOL V1.0
        </div>
    </div>
</body>
</html>
"""

# --- ROUTES ---

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_INDEX)

@app.route('/generate', methods=['POST'])
def generate():
    original_url = request.form.get('original_url')
    alias = request.form.get('alias').strip()

    if not original_url:
        return render_template_string(HTML_INDEX, error="URL is required")

    # If alias is empty, generate one
    if not alias:
        alias = generate_random_alias()

    # Ensure URL has schema
    if not original_url.startswith(('http://', 'https://')):
        original_url = 'https://' + original_url

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO links (alias, original_url) VALUES (?, ?)', (alias, original_url))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return render_template_string(HTML_INDEX, error=f"The alias '{alias}' is already taken. Please choose another.")

    conn.close()

    # Generate the full link to display
    # Uses request.host_url to get http://localhost:5000/ or similar
    generated_link = request.host_url + alias

    return render_template_string(HTML_INDEX, generated_link=generated_link)

@app.route('/<path:alias>')
def redirect_to_url(alias):
    conn = get_db_connection()
    link = conn.execute('SELECT original_url FROM links WHERE alias = ?', (alias,)).fetchone()
    conn.close()

    if link:
        return redirect(link['original_url'])
    else:
        return render_template_string(HTML_INDEX, error="404: Link not found in the database.")

if __name__ == '__main__':
    # Running on port 5001 to avoid conflict with main app if running
    app.run(debug=True, port=5001)
