import os
import sqlite3
import time
import datetime
import json
from flask import Flask, request, send_from_directory, redirect, url_for, render_template_string, jsonify, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image

# --- FLASK CONFIGURATION ---
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB Limit
app.secret_key = "51677061409c9ab04d7b9822cfe8e6206f0595ffbeb91de43ff3a476769963d3"
ADMIN_PASSWORD_HASH = 'scrypt:32768:8:1$wC1vDFSL04PVmWuj$30839c55608f9ceffc247121c87d882263a54c06fb067ed509bfbb8d7e838e1936a9fdf128a45f0042729585665c5c3b7547c9969bc74c01d1de5ec5de07d8e2'

app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff', 'ico', 'svg', 'mp3', 'wav', 'ogg', 'mp4', 'm4a', 'flac', 'srt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect('data.db', timeout=20, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Existing tables (Public Website)
    c.execute('''CREATE TABLE IF NOT EXISTS agenda_content (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    status TEXT,
                    price TEXT,
                    event_date TEXT,
                    details TEXT,
                    image_path TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS agenda_list (
                    id TEXT PRIMARY KEY,
                    section INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    
    # News/Hero Content
    c.execute('''CREATE TABLE IF NOT EXISTS news_content (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    subtitle TEXT,
                    category TEXT,
                    timestamp TEXT,
                    image_path TEXT,
                    type TEXT,
                    details TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    
    # Personnel (First Team Display)
    c.execute('''CREATE TABLE IF NOT EXISTS personnel (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    role TEXT, 
                    position TEXT, 
                    nationality TEXT DEFAULT 'Indonesia',
                    joined TEXT DEFAULT '2024',
                    matches TEXT DEFAULT '0',
                    goals TEXT DEFAULT '0',
                    details TEXT, 
                    image_path TEXT
                )''')
    
    # Sponsors
    c.execute('''CREATE TABLE IF NOT EXISTS sponsors (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    image_path TEXT,
                    size INTEGER DEFAULT 80
                )''')
    
    # Site Settings
    c.execute('''CREATE TABLE IF NOT EXISTS site_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )''')

    # --- ACADEMY MANAGEMENT SYSTEM TABLES (NEW) ---

    # 1. Registrations (Pending Students)
    c.execute('''CREATE TABLE IF NOT EXISTS registrations (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    dob TEXT,
                    position TEXT,
                    guardian TEXT,
                    guardian_wa TEXT,
                    photo_path TEXT,
                    desired_username TEXT,
                    desired_password TEXT,
                    status TEXT DEFAULT 'Pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    # 2. Players (Active Students & Auth)
    c.execute('''CREATE TABLE IF NOT EXISTS players (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    dob TEXT,
                    position TEXT,
                    guardian TEXT,
                    guardian_wa TEXT,
                    photo_path TEXT,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    # 3. Payments (Finance)
    c.execute('''CREATE TABLE IF NOT EXISTS payments (
                    id TEXT PRIMARY KEY,
                    player_id TEXT,
                    month TEXT,
                    year TEXT,
                    amount INTEGER,
                    proof_image TEXT,
                    status TEXT DEFAULT 'unpaid', -- unpaid, pending, paid
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    # 4. Attendance
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                    id TEXT PRIMARY KEY,
                    date TEXT,
                    player_id TEXT,
                    status TEXT, -- Hadir, Sakit, Alpha
                    coach_id TEXT
                )''')

    # 5. Performance Reviews (Rapor)
    c.execute('''CREATE TABLE IF NOT EXISTS performance_reviews (
                    id TEXT PRIMARY KEY,
                    month TEXT,
                    year TEXT,
                    player_id TEXT,
                    coach_id TEXT,
                    passing INTEGER,
                    shooting INTEGER,
                    stamina INTEGER,
                    attitude INTEGER,
                    teamwork INTEGER,
                    discipline INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    
    # Seed Data (Public)
    c.execute("INSERT OR IGNORE INTO news_content (id, title, subtitle, category, type) VALUES ('hero', 'VICTORY IN THE DERBY', 'A stunning performance secures the win', 'FIRST TEAM', 'hero')")
    for i in range(1, 5):
        c.execute(f"INSERT OR IGNORE INTO news_content (id, title, subtitle, category, type) VALUES ('news_{i}', 'Headlines {i}', 'Breaking News Headline 2', 'FIRST TEAM', 'sub_{i}')")
    
    c.execute("INSERT OR IGNORE INTO site_settings (key, value) VALUES ('next_match_time', '2026-02-01T20:00:00')")
    c.execute("INSERT OR IGNORE INTO site_settings (key, value) VALUES ('footer_text', '© 2026 TAHKIL FC. All rights reserved.')")

    conn.commit()
    conn.close()

init_db()

# --- DATA HELPERS ---

def get_all_data():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT * FROM agenda_content")
    agenda_content = {row['id']: dict(row) for row in c.fetchall()}
    c.execute("SELECT * FROM agenda_list ORDER BY created_at ASC")
    agenda_list = [dict(row) for row in c.fetchall()]
    
    c.execute("SELECT * FROM news_content")
    news_data = {row['id']: dict(row) for row in c.fetchall()}
    
    c.execute("SELECT * FROM personnel")
    personnel_rows = [dict(row) for row in c.fetchall()]
    personnel = {'player': [], 'coach': [], 'mvp': []}
    for p in personnel_rows:
        if p['role'] in personnel:
            personnel[p['role']].append(p)
        else:
            # Fallback for old data or other roles
            if 'player' not in personnel: personnel['player'] = []
            personnel['player'].append(p)
    
    c.execute("SELECT * FROM sponsors")
    sponsors = [dict(row) for row in c.fetchall()]
    
    c.execute("SELECT * FROM site_settings")
    settings = {row['key']: row['value'] for row in c.fetchall()}
    
    conn.close()
    return {
        'agenda_content': agenda_content,
        'agenda_list': agenda_list,
        'news': news_data,
        'personnel': personnel,
        'sponsors': sponsors,
        'settings': settings
    }

# --- ROUTES ---

def render_page(content, **kwargs):
    content = content.replace('{{ styles|safe }}', STYLES_HTML)
    content = content.replace('{{ navbar|safe }}', NAVBAR_HTML)
    if 'timestamp' not in kwargs:
        kwargs['timestamp'] = int(time.time())
    return render_template_string(content, **kwargs)

@app.route('/')
def index():
    data = get_all_data()
    
    # Helper to process agenda items
    def process_agenda(id_prefix, dynamic_section_id):
        items = []
        for i in range(1, 4): 
            id = f"{id_prefix}{i}"
            content = data['agenda_content'].get(id, {'title': 'Judul Agenda', 'status': 'Tersedia', 'price': 'Waktu/Tempat', 'event_date': ''})
            items.append({**content, 'id': id, 'is_dynamic': False})
        for item in data['agenda_list']:
            if item['section'] == dynamic_section_id:
                content = data['agenda_content'].get(item['id'], {'title': 'New Agenda', 'status': 'Tersedia', 'price': 'Rp 0', 'event_date': ''})
                items.append({**content, 'id': item['id'], 'is_dynamic': True})
        return items

    agenda_latihan = process_agenda("agenda", 1)
    turnamen = process_agenda("turnamen", 2)

    # Countdown Logic
    now_str = datetime.datetime.now().isoformat()
    target_countdown_time = data['settings'].get('next_match_time', now_str)
    
    # Placeholders if empty
    if not data['personnel']['player']:
        for i in range(11):
            data['personnel']['player'].append({'id': f'p_{i}', 'name': 'Nama Pemain', 'position': 'Posisi', 'role': 'player', 'image_path': None})

    return render_page(HTML_UR_FC, 
                       data=data, 
                       agenda_latihan=agenda_latihan, 
                       turnamen=turnamen,
                       target_countdown_time=target_countdown_time,
                       session=session)

# --- AUTHENTICATION ---

@app.route('/login', methods=['POST'])
def login():
    role = request.form.get('role')
    uid = request.form.get('userid')
    pwd = request.form.get('password')

    if role == 'admin':
        # Admin Login
        if check_password_hash(ADMIN_PASSWORD_HASH, pwd):
            session['role'] = 'admin'
            session['user_id'] = 'admin'
            return redirect(url_for('index'))

    elif role == 'coach':
        # Coach Login (Hardcoded)
        if uid == 'coach' and pwd == 'c04ch':
            session['role'] = 'coach'
            session['user_id'] = 'coach'
            return redirect(url_for('index'))

    elif role == 'student':
        # Student Login (From DB)
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM players WHERE username=?", (uid,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], pwd):
            session['role'] = 'student'
            session['user_id'] = user['id']
            session['name'] = user['name']
            return redirect(url_for('index'))

    return redirect(url_for('index') + '?error=LoginFailed')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- PUBLIC/ADMIN API (Website Content) ---

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload/<type>/<id>', methods=['POST'])
def upload_image(type, id):
    if session.get('role') != 'admin': return "Unauthorized", 403
    if 'image' not in request.files: return "No file", 400
    
    file = request.files['image']
    if file and allowed_file(file.filename):
        try:
            img = Image.open(file)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            
            # Resize
            max_width = 1024
            if img.width > max_width:
                ratio = max_width / float(img.width)
                new_height = int((float(img.height) * float(ratio)))
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            filename = secure_filename(f"{type}_{id}_{int(time.time())}.jpg")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            img.save(filepath, "JPEG", quality=85, optimize=True)
            
            conn = get_db_connection()
            c = conn.cursor()
            
            if type == 'history':
                c.execute("INSERT OR REPLACE INTO site_settings (key, value) VALUES (?, ?)", ('history_image', filename))
            elif type == 'news':
                c.execute("UPDATE news_content SET image_path = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (filename, id))
            elif type == 'personnel':
                c.execute("UPDATE personnel SET image_path = ? WHERE id = ?", (filename, id))
            elif type == 'agenda':
                c.execute("UPDATE agenda_content SET image_path = ? WHERE id = ?", (filename, id))
            elif type == 'sponsor':
                c.execute("UPDATE sponsors SET image_path = ? WHERE id = ?", (filename, id))
                
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error: {e}")
            return "Error processing image", 500
        
    return redirect(url_for('index'))

@app.route('/api/update-text', methods=['POST'])
def api_update_text():
    if session.get('role') != 'admin': return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    table = data.get('table') 
    id = data.get('id')
    field = data.get('field')
    value = data.get('value')
    
    conn = get_db_connection()
    c = conn.cursor()
    
    if table == 'site_settings':
        c.execute("INSERT OR REPLACE INTO site_settings (key, value) VALUES (?, ?)", (id, value))
    else:
        # Check existence
        c.execute(f"SELECT id FROM {table} WHERE id = ?", (id,))
        if not c.fetchone():
            if table == 'personnel':
                c.execute(f"INSERT INTO {table} (id, role) VALUES (?, ?)", (id, data.get('role', 'player')))
            else:
                c.execute(f"INSERT INTO {table} (id) VALUES (?)", (id,))
        
        c.execute(f"UPDATE {table} SET {field} = ? WHERE id = ?", (value, id))
        if table == 'news_content':
            c.execute("UPDATE news_content SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (id,))
            
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/add-card', methods=['POST'])
def api_add_card():
    if session.get('role') != 'admin': return jsonify({'error': 'Unauthorized'}), 403
    type = request.json.get('type')
    
    conn = get_db_connection()
    c = conn.cursor()
    new_id = f"{type}_{int(time.time()*1000)}"
    
    if type == 'personnel':
        role = request.json.get('role', 'player')
        c.execute("INSERT INTO personnel (id, role, name, position) VALUES (?, ?, ?, ?)", (new_id, role, 'New Name', 'Position'))
    elif type == 'sponsor':
        c.execute("INSERT INTO sponsors (id, name) VALUES (?, ?)", (new_id, 'New Sponsor'))
    elif type == 'agenda':
        section = request.json.get('section', 1)
        c.execute("INSERT INTO agenda_list (id, section) VALUES (?, ?)", (new_id, section))
        c.execute("INSERT INTO agenda_content (id, title, status, price) VALUES (?, ?, ?, ?)", (new_id, "New Agenda", "Available", "Location"))
        
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'id': new_id})

@app.route('/api/delete-item', methods=['POST'])
def api_delete_item():
    if session.get('role') != 'admin': return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    table = data.get('table')
    id = data.get('id')
    
    conn = get_db_connection()
    c = conn.cursor()
    if table == 'agenda_content':
        c.execute("DELETE FROM agenda_list WHERE id = ?", (id,))
        c.execute("DELETE FROM agenda_content WHERE id = ?", (id,))
    else:
        c.execute(f"DELETE FROM {table} WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# --- ACADEMY API ---

# 1. REGISTRATION (DAFTAR)
@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        name = request.form.get('name')
        dob = request.form.get('dob')
        pos = request.form.get('position')
        guard = request.form.get('guardian')
        wa = request.form.get('guardian_wa')
        uname = request.form.get('desired_username')
        upass = request.form.get('desired_password')

        photo_path = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"reg_{int(time.time())}.jpg")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo_path = filename

        conn = get_db_connection()
        rid = f"reg_{int(time.time())}"
        conn.execute("INSERT INTO registrations (id, name, dob, position, guardian, guardian_wa, photo_path, desired_username, desired_password) VALUES (?,?,?,?,?,?,?,?,?)",
                  (rid, name, dob, pos, guard, wa, photo_path, uname, upass))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/registrations', methods=['GET'])
def api_get_registrations():
    if session.get('role') != 'admin': return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db_connection()
    c = conn.execute("SELECT * FROM registrations WHERE status='Pending' ORDER BY created_at DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify({'registrations': rows})

@app.route('/api/admin/approve', methods=['POST'])
def api_approve_registration():
    if session.get('role') != 'admin': return jsonify({'error': 'Unauthorized'}), 403
    rid = request.json.get('id')

    conn = get_db_connection()
    reg = conn.execute("SELECT * FROM registrations WHERE id=?", (rid,)).fetchone()

    if reg:
        pid = f"pl_{int(time.time())}"
        pwd_hash = generate_password_hash(reg['desired_password'])

        # Move to players
        conn.execute("INSERT INTO players (id, name, dob, position, guardian, guardian_wa, photo_path, username, password_hash) VALUES (?,?,?,?,?,?,?,?,?)",
                     (pid, reg['name'], reg['dob'], reg['position'], reg['guardian'], reg['guardian_wa'], reg['photo_path'], reg['desired_username'], pwd_hash))
        
        conn.execute("DELETE FROM registrations WHERE id=?", (rid,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

    conn.close()
    return jsonify({'success': False, 'error': 'Not found'})

@app.route('/api/admin/reject', methods=['POST'])
def api_reject_registration():
    if session.get('role') != 'admin': return jsonify({'error': 'Unauthorized'}), 403
    rid = request.json.get('id')
    conn = get_db_connection()
    conn.execute("DELETE FROM registrations WHERE id=?", (rid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# 2. FINANCE (KEUANGAN)
@app.route('/api/finance/data', methods=['GET'])
def api_get_finance():
    role = session.get('role')
    user_id = session.get('user_id')

    conn = get_db_connection()
    c = conn.cursor()

    if role == 'admin':
        c.execute("SELECT p.*, pl.name as player_name FROM payments p JOIN players pl ON p.player_id = pl.id ORDER BY p.created_at DESC")
    elif role == 'student':
        c.execute("SELECT * FROM payments WHERE player_id = ? ORDER BY created_at DESC", (user_id,))
    else:
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403

    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify({'payments': rows})

@app.route('/api/student/upload_proof', methods=['POST'])
def api_upload_proof():
    if session.get('role') != 'student': return jsonify({'error': 'Unauthorized'}), 403

    month = request.form.get('month') # e.g. "Januari"
    year = request.form.get('year')   # e.g. "2026"
    amount = request.form.get('amount')

    file = request.files.get('proof')
    if file and allowed_file(file.filename):
        filename = secure_filename(f"pay_{session['user_id']}_{int(time.time())}.jpg")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = get_db_connection()
        pid = f"pay_{int(time.time())}"
        conn.execute("INSERT INTO payments (id, player_id, month, year, amount, proof_image, status) VALUES (?,?,?,?,?,?,?)",
                     (pid, session['user_id'], month, year, amount, filename, 'pending'))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'File error'})

@app.route('/api/admin/verify_payment', methods=['POST'])
def api_verify_payment():
    if session.get('role') != 'admin': return jsonify({'error': 'Unauthorized'}), 403
    pid = request.json.get('id')
    conn = get_db_connection()
    conn.execute("UPDATE payments SET status='paid' WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# 3. RAPOR (REPORT)
@app.route('/api/report/data', methods=['GET'])
def api_get_report():
    role = session.get('role')

    conn = get_db_connection()

    if role == 'student':
        pid = session['user_id']
        # Get Scores
        rev = conn.execute("SELECT * FROM performance_reviews WHERE player_id=? ORDER BY created_at DESC LIMIT 1", (pid,)).fetchone()
        # Get Attendance
        att = conn.execute("SELECT status FROM attendance WHERE player_id=?", (pid,)).fetchall()
        total = len(att)
        present = len([x for x in att if x['status'] == 'Hadir'])
        rate = int(present/total*100) if total > 0 else 0

        scores = dict(rev) if rev else {}
        conn.close()
        return jsonify({'scores': scores, 'attendance_rate': rate})

    elif role == 'coach':
        # Get list of players for dropdown
        pl = conn.execute("SELECT id, name FROM players ORDER BY name").fetchall()
        players = [dict(x) for x in pl]
        conn.close()
        return jsonify({'players': players})

    conn.close()
    return jsonify({'error': 'Unauthorized'})

@app.route('/api/coach/attendance', methods=['POST'])
def api_post_attendance():
    if session.get('role') != 'coach': return jsonify({'error': 'Unauthorized'}), 403
    data = request.json # { date: '...', items: [{player_id: '...', status: '...'}, ...] }

    conn = get_db_connection()
    date = data.get('date')
    for item in data.get('items', []):
        aid = f"att_{item['player_id']}_{date}"
        conn.execute("INSERT OR REPLACE INTO attendance (id, date, player_id, status, coach_id) VALUES (?,?,?,?,?)",
                     (aid, date, item['player_id'], item['status'], session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/coach/score', methods=['POST'])
def api_post_score():
    if session.get('role') != 'coach': return jsonify({'error': 'Unauthorized'}), 403
    d = request.json

    conn = get_db_connection()
    rid = f"rev_{d['player_id']}_{d['month']}_{d['year']}"
    conn.execute('''INSERT OR REPLACE INTO performance_reviews
                    (id, month, year, player_id, coach_id, passing, shooting, stamina, attitude, teamwork, discipline)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                 (rid, d['month'], d['year'], d['player_id'], session['user_id'],
                  d['passing'], d['shooting'], d['stamina'], d['attitude'], d['teamwork'], d['discipline']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# --- FRONTEND ASSETS ---

NAVBAR_HTML = """
<style>
    .top-bar { background-color: #2ecc71; height: 50px; display: flex; align-items: center; justify-content: space-between; padding: 0 5%; font-size: 0.9rem; position: relative; z-index: 1030; }
    .main-navbar { background-color: white; height: 70px; display: flex; align-items: center; padding: 0 5%; box-shadow: 0 4px 10px rgba(0,0,0,0.05); position: sticky; top: 0; z-index: 1040; justify-content: space-between; }
    .navbar-logo-img { height: 85px; position:absolute; top:-15px; left:5%; z-index:2000; }
    .nav-item-custom { color: #333; text-transform: uppercase; font-weight: 700; text-decoration: none; margin-left: 20px; }
    
    .login-btn {
        background: #333; color: white; border: none; padding: 5px 15px; border-radius: 4px; font-weight: bold; cursor: pointer;
    }
    .logout-btn {
        background: #e91e63; color: white; border: none; padding: 5px 15px; border-radius: 4px; font-weight: bold; text-decoration: none;
    }
    
    @media (max-width: 992px) {
        .top-bar { display: none; }
        .navbar-logo-img { height: 50px; position: static; }
        .nav-links-desktop { display: none; }
    }
</style>

<div class="top-bar">
    <div>Next Match: {{ data['settings'].get('next_match_text', 'Upcoming Match') }}</div>
    <div>
        {% if session.get('role') %}
            <span class="me-2 fw-bold text-white">{{ session.get('role').upper() }}</span>
            <a href="/logout" class="logout-btn">LOGOUT</a>
        {% else %}
            <button onclick="openLoginModal()" class="login-btn">LOGIN</button>
        {% endif %}
    </div>
</div>

<div class="main-navbar">
    <a href="/"><img src="{{ url_for('static', filename='logo-tahkil-fc.png') }}" class="navbar-logo-img"></a>
    <div class="nav-links-desktop">
        <a href="#hero" class="nav-item-custom">Home</a>
        <a href="#players" class="nav-item-custom">Pemain</a>
        <a href="#agenda-latihan" class="nav-item-custom">Agenda</a>
    </div>
    <div class="d-lg-none">
        {% if session.get('role') %}
            <a href="/logout" class="logout-btn" style="font-size:0.8rem">LOGOUT</a>
        {% else %}
            <button onclick="openLoginModal()" class="login-btn" style="font-size:0.8rem">LOGIN</button>
        {% endif %}
    </div>
</div>

<!-- LOGIN MODAL -->
<div id="login-modal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:9999; justify-content:center; align-items:center;">
    <div style="background:white; padding:30px; border-radius:10px; width:350px; text-align:center;">
        <h3 class="mb-3 fw-bold">SYSTEM LOGIN</h3>

        <div class="d-flex justify-content-center gap-2 mb-3">
            <button onclick="setLoginRole('admin')" id="btn-role-admin" class="btn btn-sm btn-outline-dark role-btn">Admin</button>
            <button onclick="setLoginRole('coach')" id="btn-role-coach" class="btn btn-sm btn-outline-dark role-btn">Coach</button>
            <button onclick="setLoginRole('student')" id="btn-role-student" class="btn btn-sm btn-outline-dark role-btn">Siswa</button>
        </div>

        <form action="/login" method="POST">
            <input type="hidden" name="role" id="login-role-input" value="student">
            <input type="text" name="userid" id="login-uid" placeholder="Username" class="form-control mb-2" required>
            <input type="password" name="password" placeholder="Password" class="form-control mb-3" required>
            <button type="submit" class="btn btn-success w-100">MASUK</button>
        </form>
        <button onclick="document.getElementById('login-modal').style.display='none'" class="btn btn-link w-100 mt-2">Batal</button>
    </div>
</div>

<script>
    function openLoginModal() {
        document.getElementById('login-modal').style.display = 'flex';
        setLoginRole('student');
    }
    function setLoginRole(role) {
        document.getElementById('login-role-input').value = role;
        document.querySelectorAll('.role-btn').forEach(b => {
            b.classList.remove('btn-dark');
            b.classList.add('btn-outline-dark');
        });
        document.getElementById('btn-role-'+role).classList.remove('btn-outline-dark');
        document.getElementById('btn-role-'+role).classList.add('btn-dark');

        const ph = document.getElementById('login-uid');
        if(role === 'student') ph.placeholder = 'Username Siswa';
        else if(role === 'coach') ph.placeholder = 'ID Pelatih';
        else ph.placeholder = 'ID Admin';
    }
</script>
"""

STYLES_HTML = """
<style>
    :root { var(--green: #2ecc71; var(--gold: #FFD700; var(--black: #111; }
    body { font-family: 'Inter', sans-serif; background-color: #fff; margin:0; padding:0; overflow-x:hidden; }
    .section-title { border-bottom: 3px solid #FFD700; display:inline-block; padding-bottom:5px; margin-bottom:20px; font-weight:800; text-transform:uppercase; }
    .modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 9999; justify-content: center; align-items: center; }
    .modal-content-custom { background: white; padding: 30px; border-radius: 10px; max-width: 800px; width: 90%; max-height:90vh; overflow-y:auto; position:relative; }
    .bottom-nav { position: fixed; bottom: 0; left: 0; width: 100%; height: 70px; background: white; border-top: 1px solid #eee; display: flex; z-index: 9000; box-shadow: 0 -2px 10px rgba(0,0,0,0.05); }
    .bottom-nav-item { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; text-decoration: none; color: #555; font-size: 0.7rem; font-weight: 700; }
    .bottom-nav-item i { font-size: 1.4rem; margin-bottom: 5px; color: #333; }
    .bottom-nav-item:hover i { color: #2ecc71; }
    
    .status-badge { padding: 3px 10px; border-radius: 15px; font-size: 0.75rem; font-weight: bold; }
    .badge-paid { background: #d1e7dd; color: #0f5132; }
    .badge-unpaid { background: #f8d7da; color: #842029; }
    .badge-pending { background: #fff3cd; color: #664d03; }
</style>
"""

HTML_UR_FC = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TAHFIZH KILAT FC</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    {{ styles|safe }}
</head>
<body>
    {{ navbar|safe }}
    
    <!-- PUBLIC CONTENT (SIMPLIFIED FOR BREVITY, ASSUMING STANDARD LAYOUT) -->
    <div class="container-fluid p-0 mb-4" id="hero">
         {% set hero = data['news']['hero'] %}
         <div style="position:relative; width:100%; height:50vh; background:#333;">
             <img src="{{ '/uploads/' + hero.image_path if hero.image_path else url_for('static', filename='logo-tahkil-fc.png') }}" style="width:100%; height:100%; object-fit:cover; opacity:0.8">
             <div class="position-absolute bottom-0 start-0 p-4 text-white">
                <h1 class="fw-bold">{{ hero.title }}</h1>
                <p>{{ hero.subtitle }}</p>
             </div>
         </div>
    </div>
    
    <div class="container mb-5" id="players">
        <h2 class="section-title">First Team</h2>
        <div class="d-flex overflow-auto gap-3 pb-3">
            {% for p in data['personnel']['player'] %}
            <div style="min-width:200px; background:#f8f9fa; border-radius:8px; overflow:hidden;">
                <img src="{{ '/uploads/' + p.image_path if p.image_path else '' }}" style="width:100%; height:200px; object-fit:cover; background:#ccc;">
                <div class="p-2 text-center fw-bold">{{ p.name }}</div>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <div class="container mb-5" id="agenda-latihan">
        <h2 class="section-title">Agenda</h2>
        <div class="row">
            {% for item in agenda_latihan %}
            <div class="col-md-4 mb-3">
                <div class="border rounded p-3">
                    <h5 class="fw-bold">{{ item.title }}</h5>
                    <div class="text-success small fw-bold">{{ item.event_date }}</div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- BOTTOM NAV -->
    <div class="bottom-nav">
        <a href="javascript:void(0)" onclick="openModule('daftar')" class="bottom-nav-item">
            <i class="fas fa-user-plus"></i> DAFTAR
        </a>
        <a href="javascript:void(0)" onclick="openModule('keuangan')" class="bottom-nav-item">
            <i class="fas fa-wallet"></i> KEUANGAN
        </a>
        <a href="javascript:void(0)" onclick="openModule('rapor')" class="bottom-nav-item">
            <i class="fas fa-chart-line"></i> RAPOR
        </a>
    </div>

    <!-- MODALS FOR MODULES -->
    <div id="module-modal" class="modal-overlay" onclick="closeModule()">
        <div class="modal-content-custom" onclick="event.stopPropagation()">
            <div id="module-content">Loading...</div>
        </div>
    </div>

    <script>
        const USER_ROLE = "{{ session.get('role', 'guest') }}";
        const USER_ID = "{{ session.get('user_id', '') }}";

        function closeModule() {
            document.getElementById('module-modal').style.display = 'none';
        }

        function openModule(type) {
            const modal = document.getElementById('module-modal');
            const content = document.getElementById('module-content');
            modal.style.display = 'flex';
            content.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin fa-3x"></i></div>';
            
            if (type === 'daftar') renderDaftar(content);
            else if (type === 'keuangan') renderKeuangan(content);
            else if (type === 'rapor') renderRapor(content);
        }

        // --- DAFTAR MODULE ---
        function renderDaftar(container) {
            if (USER_ROLE === 'guest') {
                container.innerHTML = `
                    <h3 class="fw-bold mb-3">FORMULIR PENDAFTARAN</h3>
                    <form onsubmit="submitRegistration(event)">
                        <div class="mb-2"><label>Nama Lengkap</label><input type="text" name="name" class="form-control" required></div>
                        <div class="row mb-2">
                            <div class="col-6"><label>Tanggal Lahir</label><input type="date" name="dob" class="form-control" required></div>
                            <div class="col-6"><label>Posisi</label>
                                <select name="position" class="form-control">
                                    <option>Penyerang</option><option>Gelandang</option><option>Bertahan</option><option>Kiper</option>
                                </select>
                            </div>
                        </div>
                        <div class="mb-2"><label>Nama Wali</label><input type="text" name="guardian" class="form-control" required></div>
                        <div class="mb-2"><label>No WA Wali</label><input type="text" name="guardian_wa" class="form-control" required></div>
                        <div class="mb-2"><label>Foto Diri</label><input type="file" name="photo" class="form-control" required></div>
                        <hr>
                        <h5 class="fw-bold">Akun Siswa</h5>
                        <div class="mb-2"><label>Desired Username</label><input type="text" name="desired_username" class="form-control" required></div>
                        <div class="mb-3"><label>Desired Password</label><input type="password" name="desired_password" class="form-control" required></div>
                        <button type="submit" class="btn btn-success w-100 fw-bold">DAFTAR SEKARANG</button>
                    </form>
                `;
            } else if (USER_ROLE === 'admin') {
                fetch('/api/admin/registrations').then(r=>r.json()).then(data => {
                    let html = `<h3 class="fw-bold">PENDAFTAR BARU</h3><div class="list-group">`;
                    if(data.registrations.length === 0) html += `<div class="alert alert-info">Tidak ada pendaftar baru.</div>`;
                    data.registrations.forEach(reg => {
                        html += `
                            <div class="list-group-item d-flex justify-content-between align-items-center">
                                <div>
                                    <h5 class="mb-0 fw-bold">${reg.name}</h5>
                                    <small>${reg.position} | ${reg.guardian} (${reg.guardian_wa})</small><br>
                                    <small class="text-primary">User: ${reg.desired_username}</small>
                                </div>
                                <div class="d-flex gap-2">
                                    <button onclick="approveReg('${reg.id}')" class="btn btn-sm btn-success">Approve</button>
                                    <button onclick="rejectReg('${reg.id}')" class="btn btn-sm btn-danger">Reject</button>
                                </div>
                            </div>
                        `;
                    });
                    html += `</div>`;
                    container.innerHTML = html;
                });
            } else {
                container.innerHTML = `<div class="alert alert-warning">Anda sudah terdaftar sebagai Anggota/Pelatih.</div>`;
            }
        }

        function submitRegistration(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            fetch('/api/register', { method:'POST', body:formData }).then(r=>r.json()).then(d=>{
                if(d.success) { alert("Pendaftaran Berhasil! Tunggu persetujuan Admin."); closeModule(); }
                else alert("Error: " + d.error);
            });
        }
        function approveReg(id) {
            if(!confirm("Setujui siswa ini?")) return;
            fetch('/api/admin/approve', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id})})
            .then(r=>r.json()).then(d=>{ if(d.success) openModule('daftar'); });
        }
        function rejectReg(id) {
            if(!confirm("Tolak siswa ini?")) return;
            fetch('/api/admin/reject', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id})})
            .then(r=>r.json()).then(d=>{ if(d.success) openModule('daftar'); });
        }

        // --- KEUANGAN MODULE ---
        function renderKeuangan(container) {
            if (USER_ROLE === 'student') {
                fetch('/api/finance/data').then(r=>r.json()).then(d => {
                    let html = `<h3 class="fw-bold">TAGIHAN SAYA</h3>
                        <div class="card mb-3 p-3 bg-light">
                            <h6>Upload Bukti Pembayaran</h6>
                            <form onsubmit="uploadProof(event)">
                                <div class="row g-2">
                                    <div class="col-4"><select name="month" class="form-control form-control-sm"><option>Januari</option><option>Februari</option><option>Maret</option></select></div>
                                    <div class="col-4"><input type="number" name="year" value="2026" class="form-control form-control-sm"></div>
                                    <div class="col-4"><input type="number" name="amount" placeholder="Rp" class="form-control form-control-sm"></div>
                                </div>
                                <input type="file" name="proof" class="form-control form-control-sm mt-2" required>
                                <button class="btn btn-sm btn-primary w-100 mt-2">Kirim Bukti</button>
                            </form>
                        </div>
                        <div class="list-group">`;
                    d.payments.forEach(p => {
                        let badge = p.status==='paid'?'badge-paid':(p.status==='pending'?'badge-pending':'badge-unpaid');
                        html += `<div class="list-group-item d-flex justify-content-between">
                            <div><strong>${p.month} ${p.year}</strong><br><small>Rp ${p.amount}</small></div>
                            <span class="status-badge ${badge}">${p.status.toUpperCase()}</span>
                        </div>`;
                    });
                    html += `</div>`;
                    container.innerHTML = html;
                });
            } else if (USER_ROLE === 'admin') {
                fetch('/api/finance/data').then(r=>r.json()).then(d => {
                    let html = `<h3 class="fw-bold">VERIFIKASI PEMBAYARAN</h3><div class="list-group">`;
                    d.payments.forEach(p => {
                        let btn = p.status !== 'paid' ? `<button onclick="verifyPay('${p.id}')" class="btn btn-sm btn-success ms-2">Validasi</button>` : '';
                        html += `<div class="list-group-item">
                            <div class="d-flex justify-content-between">
                                <div><strong>${p.player_name}</strong> - ${p.month} ${p.year}</div>
                                <div class="text-end">Rp ${p.amount} ${btn}</div>
                            </div>
                            ${p.proof_image ? `<a href="/uploads/${p.proof_image}" target="_blank" class="small text-primary">Lihat Bukti</a>` : ''}
                        </div>`;
                    });
                    container.innerHTML = html + `</div>`;
                });
            } else {
                container.innerHTML = `<div class="text-center p-5">Silakan Login sebagai Siswa atau Admin.</div>`;
            }
        }
        
        function uploadProof(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            fetch('/api/student/upload_proof', {method:'POST', body:formData}).then(r=>r.json()).then(d=>{
                if(d.success) openModule('keuangan');
            });
        }
        function verifyPay(id) {
            if(!confirm("Validasi Lunas?")) return;
            fetch('/api/admin/verify_payment', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id})})
            .then(r=>r.json()).then(d=>{ openModule('keuangan'); });
        }

        // --- RAPOR MODULE ---
        function renderRapor(container) {
            if (USER_ROLE === 'coach') {
                fetch('/api/report/data').then(r=>r.json()).then(d => {
                    let html = `<h3 class="fw-bold">INPUT NILAI & ABSENSI</h3>
                    <div class="mb-3">
                        <label>Pilih Siswa:</label>
                        <select id="coach-player-select" class="form-control">
                            ${d.players.map(p => `<option value="${p.id}">${p.name}</option>`).join('')}
                        </select>
                    </div>
                    <ul class="nav nav-tabs mb-3" id="raporTab">
                        <li class="nav-item"><a class="nav-link active" onclick="switchTab('absensi')">Absensi</a></li>
                        <li class="nav-item"><a class="nav-link" onclick="switchTab('nilai')">Penilaian</a></li>
                    </ul>
                    
                    <div id="tab-absensi">
                        <input type="date" id="att-date" class="form-control mb-2">
                        <select id="att-status" class="form-control mb-2">
                            <option>Hadir</option><option>Sakit</option><option>Alpha</option>
                        </select>
                        <button onclick="submitAttendance()" class="btn btn-primary w-100">Simpan Absensi</button>
                    </div>
                    
                    <div id="tab-nilai" style="display:none">
                        <div class="row g-2">
                            <div class="col-6"><label>Passing (0-100)</label><input type="number" id="sc-passing" class="form-control"></div>
                            <div class="col-6"><label>Shooting</label><input type="number" id="sc-shooting" class="form-control"></div>
                            <div class="col-6"><label>Stamina</label><input type="number" id="sc-stamina" class="form-control"></div>
                            <div class="col-6"><label>Attitude</label><input type="number" id="sc-attitude" class="form-control"></div>
                            <div class="col-6"><label>Teamwork</label><input type="number" id="sc-teamwork" class="form-control"></div>
                            <div class="col-6"><label>Discipline</label><input type="number" id="sc-discipline" class="form-control"></div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-6"><select id="sc-month" class="form-control"><option>Januari</option><option>Februari</option></select></div>
                            <div class="col-6"><input type="number" id="sc-year" value="2026" class="form-control"></div>
                        </div>
                        <button onclick="submitScore()" class="btn btn-success w-100 mt-3">Simpan Nilai</button>
                    </div>`;
                    container.innerHTML = html;
                });
            } else if (USER_ROLE === 'student') {
                fetch('/api/report/data').then(r=>r.json()).then(d => {
                    let scores = d.scores || {};
                    container.innerHTML = `
                        <h3 class="fw-bold text-center mb-4">RAPOR SAYA</h3>
                        <div class="row text-center mb-4">
                            <div class="col-6"><div class="p-3 bg-light rounded"><h5>Kehadiran</h5><h2 class="fw-bold text-primary">${d.attendance_rate}%</h2></div></div>
                            <div class="col-6"><div class="p-3 bg-light rounded"><h5>Rata-rata</h5><h2 class="fw-bold text-success">
                                ${Math.round(( (scores.passing||0)+(scores.shooting||0)+(scores.stamina||0)+(scores.attitude||0)+(scores.teamwork||0)+(scores.discipline||0) ) / 6) || 0}
                            </h2></div></div>
                        </div>
                        <canvas id="scoreChart"></canvas>
                    `;
                    setTimeout(() => {
                        new Chart(document.getElementById('scoreChart'), {
                            type: 'radar',
                            data: {
                                labels: ['Passing', 'Shooting', 'Stamina', 'Attitude', 'Teamwork', 'Discipline'],
                                datasets: [{
                                    label: 'Skill Stats',
                                    data: [scores.passing||0, scores.shooting||0, scores.stamina||0, scores.attitude||0, scores.teamwork||0, scores.discipline||0],
                                    backgroundColor: 'rgba(46, 204, 113, 0.2)',
                                    borderColor: '#2ecc71',
                                    pointBackgroundColor: '#2ecc71'
                                }]
                            },
                            options: { scales: { r: { min: 0, max: 100 } } }
                        });
                    }, 500);
                });
            } else {
                container.innerHTML = `<div class="text-center p-5">Silakan Login sebagai Coach atau Siswa.</div>`;
            }
        }

        function switchTab(tab) {
            document.getElementById('tab-absensi').style.display = tab==='absensi'?'block':'none';
            document.getElementById('tab-nilai').style.display = tab==='nilai'?'block':'none';
        }
        function submitAttendance() {
            const pid = document.getElementById('coach-player-select').value;
            const date = document.getElementById('att-date').value;
            const status = document.getElementById('att-status').value;
            if(!date) { alert("Pilih tanggal"); return; }
            
            fetch('/api/coach/attendance', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({ date, items: [{player_id: pid, status}] })
            }).then(r=>r.json()).then(d=> { if(d.success) alert("Absensi tersimpan!"); });
        }
        function submitScore() {
            const pid = document.getElementById('coach-player-select').value;
            const body = {
                player_id: pid,
                passing: document.getElementById('sc-passing').value,
                shooting: document.getElementById('sc-shooting').value,
                stamina: document.getElementById('sc-stamina').value,
                attitude: document.getElementById('sc-attitude').value,
                teamwork: document.getElementById('sc-teamwork').value,
                discipline: document.getElementById('sc-discipline').value,
                month: document.getElementById('sc-month').value,
                year: document.getElementById('sc-year').value
            };
            fetch('/api/coach/score', {
                method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)
            }).then(r=>r.json()).then(d=> { if(d.success) alert("Nilai tersimpan!"); });
        }

    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)
