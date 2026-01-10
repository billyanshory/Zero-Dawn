import os
import sqlite3
import time
import datetime
from flask import Flask, request, send_from_directory, redirect, url_for, render_template_string, jsonify, session
from werkzeug.utils import secure_filename

# --- KONFIGURASI FLASK ---
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB Limit
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff', 'ico', 'svg', 'mp3', 'wav', 'ogg', 'mp4', 'm4a', 'flac', 'srt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    # Existing tables
    c.execute('''CREATE TABLE IF NOT EXISTS agenda_content (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    status TEXT,
                    price TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS agenda_list (
                    id TEXT PRIMARY KEY,
                    section INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    
    # New Tables for Barca-style Layout
    # News/Hero Content
    c.execute('''CREATE TABLE IF NOT EXISTS news_content (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    subtitle TEXT,
                    category TEXT, -- 'First Team', etc.
                    timestamp TEXT,
                    image_path TEXT,
                    type TEXT -- 'hero', 'sub_1', 'sub_2', 'sub_3', 'sub_4'
                )''')
    
    # Personnel (Players, Coaches, MVP)
    c.execute('''CREATE TABLE IF NOT EXISTS personnel (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    role TEXT, -- 'player', 'coach', 'mvp'
                    position TEXT, -- e.g. 'Forward', 'Head Coach'
                    details TEXT, -- JSON or text blob
                    image_path TEXT
                )''')
    
    # Sponsors
    c.execute('''CREATE TABLE IF NOT EXISTS sponsors (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    image_path TEXT
                )''')
    
    # General Site Settings (Next Match Time, etc)
    c.execute('''CREATE TABLE IF NOT EXISTS site_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )''')

    # Seed Initial Data if empty
    # Hero
    c.execute("INSERT OR IGNORE INTO news_content (id, title, subtitle, category, type) VALUES ('hero', 'VICTORY IN THE DERBY', 'A stunning performance secures the win', 'FIRST TEAM', 'hero')")
    for i in range(1, 5):
        c.execute(f"INSERT OR IGNORE INTO news_content (id, title, category, type) VALUES ('news_{i}', 'Breaking News Headline {i}', 'CLUB', 'sub_{i}')")
    
    # Next Match Default
    c.execute("INSERT OR IGNORE INTO site_settings (key, value) VALUES ('next_match_time', '2026-02-01T20:00:00')")
    c.execute("INSERT OR IGNORE INTO site_settings (key, value) VALUES ('history_text', 'Sejarah TAHKIL FC bermula pada tahun...')")

    conn.commit()
    conn.close()

init_db()

# --- DATA HELPER ---
def get_db_connection():
    conn = sqlite3.connect('data.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_all_data():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Agenda Data (Existing)
    c.execute("SELECT * FROM agenda_content")
    agenda_content = {row['id']: dict(row) for row in c.fetchall()}
    c.execute("SELECT * FROM agenda_list ORDER BY created_at ASC")
    agenda_list = [dict(row) for row in c.fetchall()]
    
    # News Data
    c.execute("SELECT * FROM news_content")
    news_data = {row['id']: dict(row) for row in c.fetchall()}
    
    # Personnel
    c.execute("SELECT * FROM personnel")
    personnel_rows = [dict(row) for row in c.fetchall()]
    personnel = {'player': [], 'coach': [], 'mvp': []}
    for p in personnel_rows:
        personnel[p['role']].append(p)
    
    # Sponsors
    c.execute("SELECT * FROM sponsors")
    sponsors = [dict(row) for row in c.fetchall()]
    
    # Settings
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
    return render_template_string(content, **kwargs)

@app.route('/')
def index():
    data = get_all_data()
    
    # Construct Agenda Lists
    # Combine static (agenda1..3) and dynamic for the "Calendar" view
    # Limit to 3 for display as per request, but load all
    
    # Process Agenda Items for display
    def process_agenda(id_prefix, dynamic_section_id):
        items = []
        # Check static slots (limiting to 3 for the new layout initial view)
        for i in range(1, 4): 
            id = f"{id_prefix}{i}"
            content = data['agenda_content'].get(id, {'title': 'Judul Agenda', 'status': 'Tersedia', 'price': 'Waktu/Tempat'})
            items.append({**content, 'id': id, 'is_dynamic': False})
            
        # Add dynamic
        for item in data['agenda_list']:
            if item['section'] == dynamic_section_id:
                content = data['agenda_content'].get(item['id'], {'title': 'New Agenda', 'status': 'Tersedia', 'price': 'Rp 0'})
                items.append({**content, 'id': item['id'], 'is_dynamic': True})
        return items

    agenda_latihan = process_agenda("agenda", 1)
    turnamen = process_agenda("turnamen", 2) # Renamed from Next Agenda

    # Ensure Personnel lists have at least some placeholders if empty
    if not data['personnel']['player']:
        for i in range(11):
            data['personnel']['player'].append({'id': f'player_placeholder_{i}', 'name': 'Nama Pemain', 'position': 'Posisi', 'role': 'player', 'image_path': None})
    if not data['personnel']['coach']:
        for i in range(3):
            data['personnel']['coach'].append({'id': f'coach_placeholder_{i}', 'name': 'Nama Pelatih', 'position': 'Head Coach', 'role': 'coach', 'image_path': None})
    if not data['personnel']['mvp']:
        for i in range(3):
            data['personnel']['mvp'].append({'id': f'mvp_placeholder_{i}', 'name': 'Nama MVP', 'position': 'Tournament X', 'role': 'mvp', 'image_path': None})

    # Ensure Sponsors
    if not data['sponsors']:
        for i in range(4):
            data['sponsors'].append({'id': f'sponsor_{i}', 'name': 'Sponsor', 'image_path': None})

    return render_page(HTML_UR_FC, 
                       data=data, 
                       agenda_latihan=agenda_latihan, 
                       turnamen=turnamen, 
                       admin=session.get('admin', False))

@app.route('/login', methods=['POST'])
def login():
    uid = request.form.get('userid')
    pwd = request.form.get('password')
    if uid == 'adminwebsite' and pwd == '4dm1nw3bs1t3':
        session['admin'] = True
        return redirect(url_for('index'))
    return redirect(url_for('index')) # Silent fail or redirect back

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- UPLOAD & API HANDLERS ---

@app.route('/upload/<type>/<id>', methods=['POST'])
def upload_image(type, id):
    if not session.get('admin'): return "Unauthorized", 403
    if 'image' not in request.files: return "No file", 400
    
    file = request.files['image']
    if file and file.filename != '' and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{type}_{id}_{int(time.time())}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        conn = get_db_connection()
        c = conn.cursor()
        
        if type == 'news':
            c.execute("INSERT OR IGNORE INTO news_content (id) VALUES (?)", (id,))
            c.execute("UPDATE news_content SET image_path = ? WHERE id = ?", (filename, id))
        elif type == 'personnel':
            # Check if exists, if not create (for dynamic adds)
            c.execute("SELECT id FROM personnel WHERE id = ?", (id,))
            if not c.fetchone():
                c.execute("INSERT INTO personnel (id, role, name) VALUES (?, ?, ?)", (id, request.form.get('role', 'player'), 'New Person'))
            c.execute("UPDATE personnel SET image_path = ? WHERE id = ?", (filename, id))
        elif type == 'agenda':
            # agenda logic handled separately usually but can unify
            pass 
        elif type == 'sponsor':
            c.execute("INSERT OR IGNORE INTO sponsors (id) VALUES (?)", (id,))
            c.execute("UPDATE sponsors SET image_path = ? WHERE id = ?", (filename, id))
            
        conn.commit()
        conn.close()
        
    return redirect(url_for('index'))

@app.route('/api/update-text', methods=['POST'])
def api_update_text():
    if not session.get('admin'): return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    table = data.get('table') 
    id = data.get('id')
    field = data.get('field')
    value = data.get('value')

    # Security: Whitelist allowed tables and fields to prevent SQL Injection
    allowed_tables = ['news_content', 'personnel', 'agenda_content', 'sponsors', 'site_settings']
    allowed_fields = ['title', 'subtitle', 'category', 'name', 'position', 'role', 'status', 'price', 'value']

    if table not in allowed_tables:
        return jsonify({'error': 'Invalid table'}), 400
    
    if table != 'site_settings' and field not in allowed_fields:
        return jsonify({'error': 'Invalid field'}), 400
    
    conn = get_db_connection()
    c = conn.cursor()
    
    if table == 'site_settings':
        c.execute("INSERT OR REPLACE INTO site_settings (key, value) VALUES (?, ?)", (id, value))
    else:
        # Ensure row exists
        c.execute(f"SELECT id FROM {table} WHERE id = ?", (id,))
        if not c.fetchone():
            # Minimal insert if missing
            if table == 'personnel':
                c.execute(f"INSERT INTO {table} (id, role) VALUES (?, ?)", (id, data.get('role', 'player')))
            else:
                c.execute(f"INSERT INTO {table} (id) VALUES (?)", (id,))
        
        # Use formatting for column name (safe because validated against whitelist)
        c.execute(f"UPDATE {table} SET {field} = ? WHERE id = ?", (value, id))
        
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/add-card', methods=['POST'])
def api_add_card():
    if not session.get('admin'): return jsonify({'error': 'Unauthorized'}), 403
    type = request.json.get('type') # personnel, agenda
    
    conn = get_db_connection()
    c = conn.cursor()
    new_id = f"{type}_{int(time.time()*1000)}"
    
    if type == 'personnel':
        role = request.json.get('role', 'player')
        c.execute("INSERT INTO personnel (id, role, name, position) VALUES (?, ?, ?, ?)", (new_id, role, 'New Name', 'Position'))
    elif type == 'agenda':
        section = request.json.get('section', 1)
        c.execute("INSERT INTO agenda_list (id, section) VALUES (?, ?)", (new_id, section))
        c.execute("INSERT INTO agenda_content (id, title, status, price) VALUES (?, ?, ?, ?)", (new_id, "New Agenda", "Available", "Location"))
        
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'id': new_id})


# --- FRONTEND ---

NAVBAR_HTML = """
<style>
    /* Top Bar */
    .top-bar {
        background-color: #2ecc71; /* Green */
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 5%;
        font-size: 0.9rem;
        position: relative;
        z-index: 1030;
    }
    .top-bar-left {
        display: flex;
        align-items: center;
    }
    .next-match-mini {
        background: rgba(0,0,0,0.2);
        color: white;
        padding: 5px 15px;
        border-radius: 4px;
        cursor: pointer;
        font-weight: 600;
        transition: 0.2s;
    }
    .next-match-mini:hover { background: rgba(0,0,0,0.4); }
    
    .top-bar-right {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    
    /* Login Button */
    .admin-login-btn {
        background: transparent;
        border: 1px solid white;
        color: white;
        padding: 2px 10px;
        font-size: 0.8rem;
        border-radius: 4px;
        text-transform: uppercase;
        text-decoration: none;
    }
    
    /* History Button */
    .history-btn {
        background: #FFD700; /* Gold */
        color: black;
        border-radius: 20px 4px 20px 4px; /* Tumpul style */
        padding: 5px 15px;
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 700;
        text-decoration: none;
        transition: 0.3s;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .history-btn img { height: 20px; filter: brightness(0) invert(1); } /* White sketch style */
    .history-btn:hover { transform: translateY(-2px); box-shadow: 0 5px 10px rgba(0,0,0,0.2); color: black; }
    
    /* WA Button */
    .wa-btn-circle {
        background: #25D366;
        color: white;
        width: 35px;
        height: 35px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        text-decoration: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        transition: 0.3s;
    }
    .wa-btn-circle:hover { transform: scale(1.1); color: white; }

    /* Main Navbar (Bottom) */
    .main-navbar {
        background-color: white;
        height: 70px;
        display: flex;
        align-items: center;
        padding: 0 5%;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        position: sticky;
        top: 0;
        z-index: 1020;
    }
    .navbar-logo-container {
        position: absolute;
        left: 5%;
        top: -15px; /* Overlap upwards */
        z-index: 1031;
    }
    .navbar-logo-img {
        height: 85px;
        transition: 0.3s;
        filter: drop-shadow(0 2px 5px rgba(0,0,0,0.2));
    }
    .navbar-links {
        margin-left: 120px; /* Space for logo */
        display: flex;
        gap: 30px;
    }
    .nav-item-custom {
        color: #333;
        text-transform: uppercase;
        font-weight: 700;
        text-decoration: none;
        font-size: 0.9rem;
        position: relative;
    }
    .nav-item-custom:after {
        content: '';
        position: absolute;
        width: 0;
        height: 3px;
        bottom: -24px; /* Align with bottom of navbar */
        left: 0;
        background-color: #FFD700;
        transition: width 0.3s;
    }
    .nav-item-custom:hover:after { width: 100%; }
    
    /* Mobile Responsive */
    @media (max-width: 992px) {
        .top-bar { display: none; } /* Simplify for mobile or adjust */
        .main-navbar { justify-content: space-between; padding: 0 20px; }
        .navbar-logo-container { position: static; transform: none; }
        .navbar-logo-img { height: 50px; }
        .navbar-links { display: none; } /* Hide for now or hamburger */
    }
</style>

<!-- Top Bar -->
<div class="top-bar">
    <div class="top-bar-left">
        <div class="next-match-mini" onclick="togglePopup('next-match-popup')">
            Next Match: TAHKIL FC (Jan 2026)
        </div>
    </div>
    <div class="top-bar-right">
        {% if not admin %}
        <button onclick="document.getElementById('login-modal').style.display='flex'" class="admin-login-btn">Admin Login</button>
        {% else %}
        <a href="/logout" class="admin-login-btn" style="background:red; border:none;">Logout</a>
        {% endif %}
        
        <a href="#" class="history-btn" onclick="openHistoryModal()">
            <img src="{{ url_for('static', filename='logo-tahkil-fc.png') }}">
            Lihat Sejarah
        </a>
        <a href="https://chat.whatsapp.com/invite/placeholder" class="wa-btn-circle" target="_blank">
            <i class="fab fa-whatsapp"></i>
        </a>
    </div>
</div>

<!-- Main Navbar -->
<div class="main-navbar">
    <div class="navbar-logo-container">
        <a href="/">
            <img src="{{ url_for('static', filename='logo-tahkil-fc.png') }}" class="navbar-logo-img" alt="TAHKIL FC">
        </a>
    </div>
    <div class="navbar-links d-none d-lg-flex">
        <a href="#hero" class="nav-item-custom">Home</a>
        <a href="#agenda-latihan" class="nav-item-custom">Agenda Latihan</a>
        <a href="#turnamen" class="nav-item-custom">Turnamen</a>
        <a href="#players" class="nav-item-custom">Pemain</a>
        <a href="#coaches" class="nav-item-custom">Pelatih</a>
        <a href="#sponsors" class="nav-item-custom">Sponsors</a>
    </div>
    <!-- Mobile Toggler -->
    <button class="d-lg-none btn border-0" onclick="alert('Mobile menu coming soon')"><i class="fas fa-bars fa-2x"></i></button>
</div>

<!-- Login Modal -->
<div id="login-modal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:9999; justify-content:center; align-items:center;">
    <div style="background:white; padding:30px; border-radius:10px; width:300px;">
        <h3 class="text-center mb-3">Admin Login</h3>
        <form action="/login" method="POST">
            <input type="text" name="userid" placeholder="User ID" class="form-control mb-2" required>
            <input type="password" name="password" placeholder="Password" class="form-control mb-3" required>
            <button type="submit" class="btn btn-success w-100">Login</button>
        </form>
        <button onclick="document.getElementById('login-modal').style.display='none'" class="btn btn-link w-100 mt-2">Cancel</button>
    </div>
</div>

<!-- History Modal -->
<div id="history-modal" class="modal-overlay" onclick="this.style.display='none'">
    <div class="modal-content-custom" onclick="event.stopPropagation()">
        <h2 style="color:var(--gold);">Sejarah TAHKIL FC</h2>
        <img src="{{ url_for('static', filename='logo-tahkil-fc.png') }}" style="width:150px; display:block; margin:20px auto;">
        <p id="history-text" contenteditable="{{ 'true' if admin else 'false' }}" onblur="saveText('site_settings', 'history_text', 'value', this)">
            {{ history_text_placeholder }}
        </p>
    </div>
</div>
"""

STYLES_HTML = """
<style>
    :root {
        --green: #2ecc71;
        --gold: #FFD700;
        --black: #111;
        --white: #fff;
        --acrylic-dark: rgba(20, 20, 20, 0.85);
        --acrylic-light: rgba(255, 255, 255, 0.1);
    }
    body {
        font-family: 'Inter', sans-serif;
        background-color: var(--white);
        color: var(--black);
        margin: 0;
        padding: 0;
        overflow-x: hidden;
    }
    
    /* Utility */
    .section-title {
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 20px;
        position: relative;
        display: inline-block;
        border-bottom: 3px solid var(--gold);
        padding-bottom: 5px;
    }
    
    /* Horizontal Scroll Sections */
    .horizontal-scroll-container {
        display: flex;
        overflow-x: auto;
        gap: 20px;
        padding: 20px 0;
        scroll-snap-type: x mandatory;
        -webkit-overflow-scrolling: touch;
    }
    .horizontal-scroll-container::-webkit-scrollbar {
        height: 8px;
    }
    .horizontal-scroll-container::-webkit-scrollbar-thumb {
        background: var(--green);
        border-radius: 4px;
    }
    
    .person-card {
        min-width: 250px;
        height: 350px;
        background: var(--black);
        color: white;
        border-radius: 10px;
        overflow: hidden;
        scroll-snap-align: center;
        position: relative;
        transition: transform 0.3s;
        cursor: pointer;
    }
    .person-card:hover {
        transform: translateY(-10px);
    }
    .person-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        opacity: 0.8;
        transition: 0.3s;
    }
    .person-card:hover .person-img { opacity: 1; }
    
    .person-info {
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        background: linear-gradient(transparent, black);
        padding: 20px;
    }
    .person-name { font-weight: 700; font-size: 1.2rem; text-transform: uppercase; color: var(--gold); }
    .person-role { font-size: 0.9rem; color: #ccc; }
    
    /* Calendar / Agenda Style */
    .calendar-container {
        background: var(--bg-light);
        padding: 40px;
        border-radius: 8px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .countdown-timer {
        font-size: 3rem;
        font-weight: 800;
        color: var(--green);
        text-align: center;
        margin: 20px 0;
        font-family: monospace;
    }
    
    .agenda-card-barca {
        display: flex;
        background: white;
        border: 1px solid #eee;
        margin-bottom: 15px;
        transition: 0.3s;
    }
    .agenda-card-barca:hover { transform: translateX(10px); border-left: 5px solid var(--gold); }
    .agenda-img { width: 100px; height: 100px; object-fit: cover; background: #333; }
    .agenda-details { padding: 15px; flex: 1; display: flex; flex-direction: column; justify-content: center; }
    .agenda-date { color: var(--green); font-weight: 700; font-size: 0.8rem; text-transform: uppercase; }
    .agenda-title { font-weight: 800; font-size: 1.2rem; }
    
    /* Modal Overlay */
    .modal-overlay {
        display: none;
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.8);
        backdrop-filter: blur(10px);
        z-index: 9999;
        justify-content: center;
        align-items: center;
    }
    .modal-content-custom {
        background: white;
        padding: 40px;
        border-radius: 10px;
        max-width: 600px;
        width: 90%;
        text-align: center;
        position: relative;
    }
    
    /* Admin UI */
    .edit-btn {
        position: absolute;
        top: 10px; right: 10px;
        background: var(--gold);
        border: none;
        border-radius: 4px;
        padding: 5px 10px;
        cursor: pointer;
        z-index: 10;
    }
</style>
"""

HTML_UR_FC = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TAHFIZH KILAT FC - Official Site</title>
    <link rel="shortcut icon" href="{{ url_for('static', filename='logo-tahkil-fc.png') }}">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    {{ styles|safe }}
</head>
<body>
    {{ navbar|safe }}
    
    <!-- HERO SECTION -->
    <div class="container py-5" id="hero">
        <div class="row">
            <!-- Main News (Left/Top) -->
            <div class="col-lg-8 mb-4 position-relative">
                <div class="position-relative" style="height: 500px; overflow: hidden; border-radius: 10px; background: black;">
                    {% set hero = data['news']['hero'] %}
                    <img src="{{ '/uploads/' + hero.image_path if hero.image_path else url_for('static', filename='logo-tahkil-fc.png') }}" 
                         style="width: 100%; height: 100%; object-fit: cover; opacity: 0.7;">
                    
                    {% if admin %}
                    <form action="/upload/news/hero" method="post" enctype="multipart/form-data" class="position-absolute top-0 start-0 p-2">
                        <input type="file" name="image" onchange="this.form.submit()" style="display:none;" id="hero-upload">
                        <label for="hero-upload" class="btn btn-sm btn-warning"><i class="fas fa-camera"></i></label>
                    </form>
                    {% endif %}

                    <div class="position-absolute bottom-0 start-0 w-100 p-4" style="background: linear-gradient(transparent, black);">
                        <span class="badge bg-warning text-dark mb-2">FIRST TEAM</span>
                        <h1 class="text-white fw-bold fst-italic text-decoration-underline" 
                            contenteditable="{{ 'true' if admin else 'false' }}"
                            onblur="saveText('news_content', 'hero', 'title', this)">
                            {{ hero.title }}
                        </h1>
                        <p class="text-white-50" 
                           contenteditable="{{ 'true' if admin else 'false' }}"
                           onblur="saveText('news_content', 'hero', 'subtitle', this)">
                           {{ hero.subtitle }}
                        </p>
                        <div class="text-warning small"><i class="far fa-clock"></i> <span id="last-updated">2 Hours Ago</span></div>
                    </div>
                </div>
            </div>
            
            <!-- Sub News (Right/Side) -->
            <div class="col-lg-4">
                <div class="row">
                    {% for i in range(1, 5) %}
                    {% set news_item = data['news']['news_' ~ i] %}
                    <div class="col-6 col-lg-12 mb-3">
                        <div class="d-flex align-items-center bg-light rounded p-2 shadow-sm sub-news-card" style="transition:0.3s;">
                            <div style="width: 80px; height: 60px; background: #333; border-radius: 5px; overflow: hidden; flex-shrink: 0; position: relative;">
                                <img src="{{ '/uploads/' + news_item.image_path if news_item.image_path else '' }}" style="width:100%; height:100%; object-fit:cover;">
                                {% if admin %}
                                <form action="/upload/news/news_{{ i }}" method="post" enctype="multipart/form-data" class="position-absolute top-0 start-0">
                                    <input type="file" name="image" onchange="this.form.submit()" style="display:none;" id="news-up-{{ i }}">
                                    <label for="news-up-{{ i }}" class="badge bg-warning" style="cursor:pointer;">+</label>
                                </form>
                                {% endif %}
                            </div>
                            <div class="ms-3 flex-grow-1">
                                <small class="text-success fw-bold">FIRST TEAM</small>
                                <h6 class="mb-0 fw-bold" style="font-size: 0.9rem;"
                                    contenteditable="{{ 'true' if admin else 'false' }}"
                                    onblur="saveText('news_content', 'news_{{ i }}', 'title', this)">
                                    {{ news_item.title }}
                                </h6>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        
        <!-- Sponsors -->
        <div class="row mt-4 justify-content-center text-center" id="sponsors">
            {% for sponsor in data['sponsors'] %}
            <div class="col-3 col-md-2 position-relative">
                <img src="{{ '/uploads/' + sponsor.image_path if sponsor.image_path else 'https://via.placeholder.com/150x50?text=SPONSOR' }}" 
                     class="img-fluid" style="filter: grayscale(100%); opacity: 0.6; transition: 0.3s;" onmouseover="this.style.filter='none'; this.style.opacity='1'" onmouseout="this.style.filter='grayscale(100%)'; this.style.opacity='0.6'">
                {% if admin %}
                <form action="/upload/sponsor/{{ sponsor.id }}" method="post" enctype="multipart/form-data" class="position-absolute top-0 start-50">
                    <input type="file" name="image" onchange="this.form.submit()" style="display:none;" id="sp-{{ sponsor.id }}">
                    <label for="sp-{{ sponsor.id }}" class="badge bg-secondary"><i class="fas fa-edit"></i></label>
                </form>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </div>
    
    <!-- PLAYERS SECTION -->
    <div class="container-fluid py-5 bg-light" id="players">
        <div class="container">
            <h2 class="section-title">Pemain TAHKIL FC</h2>
            <div class="horizontal-scroll-container">
                {% for player in data['personnel']['player'] %}
                <div class="person-card" onclick="openPersonModal('{{ player.id }}', '{{ player.name }}', '{{ player.position }}', '{{ '/uploads/' + player.image_path if player.image_path else '' }}')">
                    {% if player.image_path %}
                        <img src="/uploads/{{ player.image_path }}" class="person-img">
                    {% else %}
                        <div class="person-img d-flex align-items-center justify-content-center bg-secondary"><i class="fas fa-user fa-3x text-white-50"></i></div>
                    {% endif %}
                    
                    <div class="person-info">
                        <div class="person-name">{{ player.name }}</div>
                        <div class="person-role">{{ player.position }}</div>
                    </div>
                    
                    {% if admin %}
                    <form action="/upload/personnel/{{ player.id }}" method="post" enctype="multipart/form-data" class="edit-btn" onclick="event.stopPropagation()">
                         <input type="file" name="image" onchange="this.form.submit()" style="display:none;" id="pl-{{ player.id }}">
                         <input type="hidden" name="role" value="player">
                         <label for="pl-{{ player.id }}"><i class="fas fa-camera"></i></label>
                    </form>
                    {% endif %}
                </div>
                {% endfor %}
                {% if admin %}
                <div class="person-card d-flex align-items-center justify-content-center" onclick="addPerson('player')">
                    <i class="fas fa-plus fa-3x text-success"></i>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    
    <!-- COACHES SECTION -->
    <div class="container-fluid py-5" id="coaches">
        <div class="container">
            <h2 class="section-title">Pelatih TAHKIL FC</h2>
            <div class="horizontal-scroll-container">
                {% for coach in data['personnel']['coach'] %}
                <div class="person-card" onclick="openPersonModal('{{ coach.id }}', '{{ coach.name }}', '{{ coach.position }}', '{{ '/uploads/' + coach.image_path if coach.image_path else '' }}')">
                    <img src="{{ '/uploads/' + coach.image_path if coach.image_path else '' }}" class="person-img" style="background:#333">
                    <div class="person-info">
                        <div class="person-name">{{ coach.name }}</div>
                        <div class="person-role">{{ coach.position }}</div>
                    </div>
                     {% if admin %}
                    <form action="/upload/personnel/{{ coach.id }}" method="post" enctype="multipart/form-data" class="edit-btn" onclick="event.stopPropagation()">
                         <input type="file" name="image" onchange="this.form.submit()" style="display:none;" id="co-{{ coach.id }}">
                         <input type="hidden" name="role" value="coach">
                         <label for="co-{{ coach.id }}"><i class="fas fa-camera"></i></label>
                    </form>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- MVP SECTION -->
    <div class="container-fluid py-5 bg-light" id="mvp">
        <div class="container">
            <h2 class="section-title">Pemain MVP TAHKIL FC</h2>
            <div class="horizontal-scroll-container">
                {% for mvp in data['personnel']['mvp'] %}
                <div class="person-card" onclick="openPersonModal('{{ mvp.id }}', '{{ mvp.name }}', '{{ mvp.position }}', '{{ '/uploads/' + mvp.image_path if mvp.image_path else '' }}')">
                    <img src="{{ '/uploads/' + mvp.image_path if mvp.image_path else '' }}" class="person-img" style="background:#333">
                    <div class="person-info">
                        <div class="person-name">{{ mvp.name }}</div>
                        <div class="person-role">{{ mvp.position }}</div>
                    </div>
                     {% if admin %}
                    <form action="/upload/personnel/{{ mvp.id }}" method="post" enctype="multipart/form-data" class="edit-btn" onclick="event.stopPropagation()">
                         <input type="file" name="image" onchange="this.form.submit()" style="display:none;" id="mv-{{ mvp.id }}">
                         <input type="hidden" name="role" value="mvp">
                         <label for="mv-{{ mvp.id }}"><i class="fas fa-camera"></i></label>
                    </form>
                    {% endif %}
                </div>
                {% endfor %}
                 {% if admin %}
                <div class="person-card d-flex align-items-center justify-content-center" onclick="addPerson('mvp')">
                    <i class="fas fa-plus fa-3x text-warning"></i>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    
    <!-- AGENDA LATIHAN (CALENDAR STYLE) -->
    <div class="container py-5" id="agenda-latihan">
        <div class="row">
            <div class="col-lg-12">
                <h2 class="section-title">Agenda Latihan TAHKIL FC</h2>
                <div class="calendar-container">
                    <div class="text-center mb-4">
                        <h4 class="text-uppercase fw-bold">Next Match Countdown</h4>
                        <div class="countdown-timer" id="countdown">00:00:00:00</div>
                        {% if admin %}
                        <input type="datetime-local" class="form-control w-25 mx-auto" onchange="saveText('site_settings', 'next_match_time', 'value', this)" value="{{ data['settings']['next_match_time'] }}">
                        {% endif %}
                    </div>
                    
                    <div class="row">
                        {% for item in agenda_latihan %}
                        <div class="col-md-4">
                            <div class="agenda-card-barca">
                                <div class="agenda-img" style="position:relative;">
                                    <!-- Use existing upload mechanism for agenda images via JS logic if needed, or simple placeholder -->
                                    <img src="{{ '/uploads/' + item.id + '.jpg' }}" onerror="this.src='{{ url_for('static', filename='logo-tahkil-fc.png') }}'" style="width:100%; height:100%; object-fit:cover;">
                                </div>
                                <div class="agenda-details">
                                    <div class="agenda-date" contenteditable="{{ 'true' if admin else 'false' }}" onblur="saveText('agenda_content', '{{ item.id }}', 'price', this)">{{ item.price }}</div>
                                    <div class="agenda-title" contenteditable="{{ 'true' if admin else 'false' }}" onblur="saveText('agenda_content', '{{ item.id }}', 'title', this)">{{ item.title }}</div>
                                    <small class="text-muted" contenteditable="{{ 'true' if admin else 'false' }}" onblur="saveText('agenda_content', '{{ item.id }}', 'status', this)">{{ item.status }}</small>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                     {% if admin %}
                    <button class="btn btn-outline-success mt-3" onclick="addCard('agenda', 1)">+ Add Agenda Item</button>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    
    <!-- TURNAMEN (NEXT AGENDA) -->
    <div class="container py-5" id="turnamen">
        <h2 class="section-title">Turnamen</h2>
        <div class="row">
             {% for item in turnamen %}
            <div class="col-md-4">
                <div class="agenda-card-barca">
                    <div class="agenda-img">
                         <img src="{{ '/uploads/' + item.id + '.jpg' }}" onerror="this.src='{{ url_for('static', filename='logo-tahkil-fc.png') }}'" style="width:100%; height:100%; object-fit:cover;">
                    </div>
                    <div class="agenda-details">
                        <div class="agenda-date" contenteditable="{{ 'true' if admin else 'false' }}" onblur="saveText('agenda_content', '{{ item.id }}', 'price', this)">{{ item.price }}</div>
                        <div class="agenda-title" contenteditable="{{ 'true' if admin else 'false' }}" onblur="saveText('agenda_content', '{{ item.id }}', 'title', this)">{{ item.title }}</div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
         {% if admin %}
        <button class="btn btn-outline-success mt-3" onclick="addCard('agenda', 2)">+ Add Tournament Item</button>
        {% endif %}
    </div>

    <!-- PERSON MODAL -->
    <div id="person-modal" class="modal-overlay" onclick="this.style.display='none'">
        <div class="modal-content-custom" onclick="event.stopPropagation()">
            <img id="pm-img" src="" style="width:150px; height:150px; border-radius:50%; object-fit:cover; margin-bottom:20px;">
            <h2 id="pm-name" contenteditable="{{ 'true' if admin else 'false' }}" onblur="updatePersonDetail('name')">Name</h2>
            <h4 id="pm-role" class="text-muted" contenteditable="{{ 'true' if admin else 'false' }}" onblur="updatePersonDetail('position')">Position</h4>
            <div class="mt-4 text-start">
                <p><strong>Nationality:</strong> Indonesia</p>
                <p><strong>Joined:</strong> 2024</p>
                <p><strong>Matches:</strong> 10</p>
                <p><strong>Goals:</strong> 5</p>
            </div>
        </div>
    </div>
    
    <footer class="bg-black text-white py-5 text-center mt-5">
        <div class="container">
            <h3 class="fw-bold mb-3">TAHFIZH <span class="text-warning">KILAT FC</span></h3>
            <p>&copy; 2026 TAHKIL FC. All rights reserved.</p>
        </div>
    </footer>

    <script>
        // API Interactions
        function saveText(table, id, field, el) {
            let value = el.innerText || el.value;
            fetch('/api/update-text', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ table, id, field, value })
            });
        }
        
        function addPerson(role) {
            fetch('/api/add-card', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ type: 'personnel', role })
            }).then(() => location.reload());
        }
        
        function addCard(type, section) {
             fetch('/api/add-card', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ type, section })
            }).then(() => location.reload());
        }

        // Modals
        let currentPersonId = null;
        function openPersonModal(id, name, role, img) {
            currentPersonId = id;
            document.getElementById('pm-name').innerText = name;
            document.getElementById('pm-role').innerText = role;
            document.getElementById('pm-img').src = img || '{{ url_for("static", filename="logo-tahkil-fc.png") }}';
            document.getElementById('person-modal').style.display = 'flex';
        }
        
        function updatePersonDetail(field) {
            if(!currentPersonId) return;
            const el = field === 'name' ? document.getElementById('pm-name') : document.getElementById('pm-role');
            saveText('personnel', currentPersonId, field, el);
        }
        
        function openHistoryModal() {
            document.getElementById('history-modal').style.display = 'flex';
            // Here you would fetch specific history text if needed
            document.getElementById('history-text').innerText = "{{ data['settings']['history_text'] }}";
        }

        // Countdown Logic
        const targetDate = new Date("{{ data['settings']['next_match_time'] }}").getTime();
        
        setInterval(() => {
            const now = new Date().getTime();
            const distance = targetDate - now;
            
            if (distance < 0) {
                document.getElementById("countdown").innerHTML = "MATCH DAY!";
                return;
            }
            
            const days = Math.floor(distance / (1000 * 60 * 60 * 24));
            const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);
            
            document.getElementById("countdown").innerHTML = days + "d " + hours + "h " + minutes + "m " + seconds + "s ";
        }, 1000);
        
        // Hover effects for news cards (Animation)
        document.querySelectorAll('.sub-news-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'scale(1.05)';
                card.style.zIndex = '10';
            });
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'scale(1)';
                card.style.zIndex = '1';
            });
        });
    </script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)
