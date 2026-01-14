import os
import sqlite3
import time
import datetime
import json
from flask import Flask, request, send_from_directory, redirect, url_for, render_template_string, jsonify, session
from werkzeug.utils import secure_filename

# --- FLASK CONFIGURATION ---
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
    
    # News/Hero Content
    c.execute('''CREATE TABLE IF NOT EXISTS news_content (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    subtitle TEXT,
                    category TEXT,
                    timestamp TEXT,
                    image_path TEXT,
                    type TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    
    # Personnel
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
    
    # Migrations
    try: c.execute("ALTER TABLE personnel ADD COLUMN nationality TEXT DEFAULT 'Indonesia'")
    except: pass
    try: c.execute("ALTER TABLE personnel ADD COLUMN joined TEXT DEFAULT '2024'")
    except: pass
    try: c.execute("ALTER TABLE personnel ADD COLUMN matches TEXT DEFAULT '0'")
    except: pass
    try: c.execute("ALTER TABLE personnel ADD COLUMN goals TEXT DEFAULT '0'")
    except: pass
    try: c.execute("ALTER TABLE news_content ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except: pass

    # Sponsors
    c.execute('''CREATE TABLE IF NOT EXISTS sponsors (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    image_path TEXT
                )''')
    
    # Site Settings
    c.execute('''CREATE TABLE IF NOT EXISTS site_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )''')

    # Seed Data
    c.execute("INSERT OR IGNORE INTO news_content (id, title, subtitle, category, type) VALUES ('hero', 'VICTORY IN THE DERBY', 'A stunning performance secures the win', 'FIRST TEAM', 'hero')")
    for i in range(1, 5):
        c.execute(f"INSERT OR IGNORE INTO news_content (id, title, subtitle, category, type) VALUES ('news_{i}', 'Headlines {i}', 'Breaking News Headline 2', 'FIRST TEAM', 'sub_{i}')")
    
    c.execute("INSERT OR IGNORE INTO site_settings (key, value) VALUES ('next_match_time', '2026-02-01T20:00:00')")
    c.execute("INSERT OR IGNORE INTO site_settings (key, value) VALUES ('history_text', 'Sejarah TAHKIL FC bermula pada tahun...')")
    c.execute("INSERT OR IGNORE INTO site_settings (key, value) VALUES ('footer_text', '© 2026 TAHKIL FC. All rights reserved.')")

    conn.commit()
    conn.close()

init_db()

# --- DATA HELPERS ---
def get_db_connection():
    conn = sqlite3.connect('data.db')
    conn.row_factory = sqlite3.Row
    return conn

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
        personnel[p['role']].append(p)
    
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
    return render_template_string(content, **kwargs)

@app.route('/')
def index():
    data = get_all_data()
    
    def process_agenda(id_prefix, dynamic_section_id):
        items = []
        for i in range(1, 4): 
            id = f"{id_prefix}{i}"
            content = data['agenda_content'].get(id, {'title': 'Judul Agenda', 'status': 'Tersedia', 'price': 'Waktu/Tempat'})
            items.append({**content, 'id': id, 'is_dynamic': False})
        for item in data['agenda_list']:
            if item['section'] == dynamic_section_id:
                content = data['agenda_content'].get(item['id'], {'title': 'New Agenda', 'status': 'Tersedia', 'price': 'Rp 0'})
                items.append({**content, 'id': item['id'], 'is_dynamic': True})
        return items

    agenda_latihan = process_agenda("agenda", 1)
    turnamen = process_agenda("turnamen", 2)

    # Placeholders
    if not data['personnel']['player']:
        for i in range(11):
            data['personnel']['player'].append({'id': f'player_placeholder_{i}', 'name': 'Nama Pemain', 'position': 'Posisi', 'role': 'player', 'nationality':'Indonesia', 'joined':'2024', 'matches':'0', 'goals':'0', 'image_path': None})
    if not data['personnel']['coach']:
        for i in range(3):
            data['personnel']['coach'].append({'id': f'coach_placeholder_{i}', 'name': 'Nama Pelatih', 'position': 'Head Coach', 'role': 'coach', 'nationality':'Indonesia', 'joined':'2024', 'matches':'0', 'goals':'0', 'image_path': None})
    if not data['personnel']['mvp']:
        for i in range(3):
            data['personnel']['mvp'].append({'id': f'mvp_placeholder_{i}', 'name': 'Nama MVP', 'position': 'Tournament X', 'role': 'mvp', 'nationality':'Indonesia', 'joined':'2024', 'matches':'0', 'goals':'0', 'image_path': None})

    # Sponsors (Allow dynamic, but show at least some placeholders if totally empty and no DB entries)
    if not data['sponsors'] and not session.get('admin'):
        pass # If empty, stays empty or seeds handled in init_db

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
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

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
            c.execute("UPDATE news_content SET image_path = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (filename, id))
        elif type == 'personnel':
            c.execute("SELECT id FROM personnel WHERE id = ?", (id,))
            if not c.fetchone():
                c.execute("INSERT INTO personnel (id, role, name) VALUES (?, ?, ?)", (id, request.form.get('role', 'player'), 'New Person'))
            c.execute("UPDATE personnel SET image_path = ? WHERE id = ?", (filename, id))
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

    allowed_tables = ['news_content', 'personnel', 'agenda_content', 'sponsors', 'site_settings']
    allowed_fields = ['title', 'subtitle', 'category', 'name', 'position', 'role', 'status', 'price', 'value', 'nationality', 'joined', 'matches', 'goals']

    if table not in allowed_tables:
        return jsonify({'error': 'Invalid table'}), 400
    if table != 'site_settings' and field not in allowed_fields:
        return jsonify({'error': 'Invalid field'}), 400
    
    conn = get_db_connection()
    c = conn.cursor()
    
    if table == 'site_settings':
        c.execute("INSERT OR REPLACE INTO site_settings (key, value) VALUES (?, ?)", (id, value))
    else:
        c.execute(f"SELECT id FROM {table} WHERE id = ?", (id,))
        if not c.fetchone():
            if table == 'personnel':
                c.execute(f"INSERT INTO {table} (id, role) VALUES (?, ?)", (id, data.get('role', 'player')))
            else:
                c.execute(f"INSERT INTO {table} (id) VALUES (?)", (id,))
        
        c.execute(f"UPDATE {table} SET {field} = ? WHERE id = ?", (value, id))
        
        # Update timestamp for news
        if table == 'news_content':
            c.execute("UPDATE news_content SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (id,))

    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/add-card', methods=['POST'])
def api_add_card():
    if not session.get('admin'): return jsonify({'error': 'Unauthorized'}), 403
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

# --- FRONTEND ASSETS ---

NAVBAR_HTML = """
<style>
    .top-bar {
        background-color: #2ecc71;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 5%;
        font-size: 0.9rem;
        position: relative;
        z-index: 1030;
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
    
    .history-btn {
        background: #FFD700;
        color: black;
        border-radius: 20px 4px 20px 4px;
        padding: 5px 15px;
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 700;
        text-decoration: none;
        transition: 0.3s;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        cursor: pointer;
    }
    .history-btn img { height: 20px; filter: brightness(0) invert(1); }
    .history-btn:hover { transform: translateY(-2px); box-shadow: 0 5px 10px rgba(0,0,0,0.2); color: black; }
    
    .social-icon-link { color: white; font-size: 1.2rem; transition: 0.2s; }
    .social-icon-link:hover { color: var(--gold); }

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
    .navbar-logo-container { position: absolute; left: 5%; top: -15px; z-index: 2000; }
    .navbar-logo-img { height: 85px; transition: 0.3s; filter: drop-shadow(0 2px 5px rgba(0,0,0,0.2)); cursor: pointer; }
    .navbar-links { margin-left: 120px; display: flex; gap: 30px; }
    .nav-item-custom {
        color: #333; text-transform: uppercase; font-weight: 700; text-decoration: none; font-size: 0.9rem; position: relative;
    }
    .nav-item-custom:after {
        content: ''; position: absolute; width: 0; height: 3px; bottom: -24px; left: 0; background-color: #FFD700; transition: width 0.3s;
    }
    .nav-item-custom:hover:after { width: 100%; }
    
    @media (max-width: 992px) {
        .top-bar { display: none; }
        .main-navbar { justify-content: space-between; padding: 0 20px; }
        .navbar-logo-container { position: static; transform: none; }
        .navbar-logo-img { height: 50px; }
        .navbar-links { display: none; }
    }
</style>

<div class="top-bar">
    <div class="top-bar-left">
        <div class="next-match-mini" onclick="openNextMatchModal()">
            <span id="next-match-display">{{ data['settings'].get('next_match_text', 'Next Match: TAHKIL FC (Jan 2026)') }}</span>
        </div>
    </div>
    <div class="top-bar-right d-flex align-items-center gap-3">
        {% if not admin %}
        <button onclick="document.getElementById('login-modal').style.display='flex'" class="btn btn-outline-light btn-sm">Admin Login</button>
        {% else %}
        <a href="/logout" class="btn btn-danger btn-sm">Logout</a>
        {% endif %}
        
        <div class="history-btn" onclick="openHistoryModal()">
            <img src="{{ url_for('static', filename='logo-tahkil-fc.png') }}" class="monochrome-icon">
            Lihat Sejarah
        </div>
        <div class="d-none d-lg-flex gap-3 align-items-center">
            <a href="https://wa.me/6281528455350" class="social-icon-link" target="_blank"><i class="fab fa-whatsapp"></i></a>
            <a href="https://maps.app.goo.gl/4deg1ha8WaxWKdPC9" class="social-icon-link" target="_blank"><i class="fas fa-map-marker-alt"></i></a>
            <a href="https://www.instagram.com/rivkycahyahakikiori/" class="social-icon-link" target="_blank"><i class="fab fa-instagram"></i></a>
        </div>
    </div>
</div>

<div class="main-navbar">
    <div class="navbar-logo-container" onclick="toggleLogoPopup()">
        <a href="javascript:void(0)">
            <img src="{{ url_for('static', filename='logo-tahkil-fc.png') }}" class="navbar-logo-img" alt="TAHKIL FC">
        </a>
    </div>
    <div class="navbar-links d-none d-lg-flex">
        <a href="#hero" class="nav-item-custom">Home</a>
        <a href="#players" class="nav-item-custom">Pemain</a>
        <a href="#coaches" class="nav-item-custom">Pelatih</a>
        <a href="#mvp" class="nav-item-custom">MVP</a>
        <a href="#agenda-latihan" class="nav-item-custom">Agenda Latihan</a>
        <a href="#turnamen" class="nav-item-custom">Turnamen</a>
        <a href="#sponsors" class="nav-item-custom">Sponsors</a>
    </div>
    <button class="d-lg-none btn border-0" onclick="toggleMobileMenu()"><i class="fas fa-bars fa-2x"></i></button>
    <div class="navbar-split-border"></div>
</div>

<div id="mobile-menu" class="mobile-menu-container">
    <div class="mobile-next-match">{{ data['settings'].get('next_match_text', 'Next Match: TAHKIL FC (Jan 2026)') }}</div>
    <a href="#hero" class="mobile-nav-link" onclick="toggleMobileMenu()">Home</a>
    <a href="#players" class="mobile-nav-link" onclick="toggleMobileMenu()">Pemain</a>
    <a href="#coaches" class="mobile-nav-link" onclick="toggleMobileMenu()">Pelatih</a>
    <a href="#mvp" class="mobile-nav-link" onclick="toggleMobileMenu()">MVP</a>
    <a href="#agenda-latihan" class="mobile-nav-link" onclick="toggleMobileMenu()">Agenda Latihan</a>
    <a href="#turnamen" class="mobile-nav-link" onclick="toggleMobileMenu()">Turnamen</a>
    <a href="#sponsors" class="mobile-nav-link" onclick="toggleMobileMenu()">Sponsors</a>
    
    <div class="mt-auto d-flex flex-column gap-3">
        <div class="history-btn justify-content-center" onclick="openHistoryModal(); toggleMobileMenu();">
            <img src="{{ url_for('static', filename='logo-tahkil-fc.png') }}" class="monochrome-icon">
            Lihat Sejarah
        </div>
        <button onclick="document.getElementById('login-modal').style.display='flex'; toggleMobileMenu();" class="btn btn-outline-dark w-100">Admin Login</button>
        <div class="d-flex justify-content-center gap-4 mt-2">
            <a href="https://wa.me/6281528455350" class="text-dark h4"><i class="fab fa-whatsapp"></i></a>
            <a href="https://maps.app.goo.gl/4deg1ha8WaxWKdPC9" class="text-dark h4"><i class="fas fa-map-marker-alt"></i></a>
            <a href="https://www.instagram.com/rivkycahyahakikiori/" class="text-dark h4"><i class="fab fa-instagram"></i></a>
        </div>
    </div>
</div>

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
"""

STYLES_HTML = """
<style>
    :root {
        --green: #2ecc71;
        --gold: #FFD700;
        --black: #111;
        --white: #fff;
    }
    body {
        font-family: 'Inter', sans-serif;
        background-color: var(--white);
        color: var(--black);
        margin: 0;
        padding: 0;
        overflow-x: hidden;
    }
    .section-title {
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 20px;
        position: relative;
        display: inline-block;
        border-bottom: 3px solid var(--gold);
        padding-bottom: 5px;
    }
    .horizontal-scroll-container {
        display: flex;
        overflow-x: auto;
        gap: 20px;
        padding: 20px 0;
        scroll-snap-type: x mandatory;
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
    .person-card:hover { transform: translateY(-10px); }
    .person-img { width: 100%; height: 100%; object-fit: cover; opacity: 0.8; transition: 0.3s; }
    .person-card:hover .person-img { opacity: 1; }
    .person-info {
        position: absolute; bottom: 0; left: 0; width: 100%;
        background: linear-gradient(transparent, black); padding: 20px;
    }
    .person-name { font-weight: 700; font-size: 1.2rem; text-transform: uppercase; color: var(--gold); }
    .person-role { font-size: 0.9rem; color: #ccc; }
    
    .calendar-container {
        background: #f8f9fa; padding: 40px; border-radius: 8px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .countdown-timer {
        font-size: 3rem; font-weight: 800; color: var(--green);
        text-align: center; margin: 20px 0; font-family: monospace;
    }
    .agenda-card-barca {
        display: flex; background: white; border: 1px solid #eee; margin-bottom: 15px; transition: 0.3s;
    }
    .agenda-card-barca:hover { transform: translateX(10px); border-left: 5px solid var(--gold); }
    .agenda-img { width: 100px; height: 100px; object-fit: cover; background: #333; }
    .agenda-details { padding: 15px; flex: 1; display: flex; flex-direction: column; justify-content: center; }
    .agenda-date { color: var(--green); font-weight: 700; font-size: 0.8rem; text-transform: uppercase; }
    .agenda-title { font-weight: 800; font-size: 1.2rem; }
    
    .modal-overlay {
        display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.8); backdrop-filter: blur(10px); z-index: 9999;
        justify-content: center; align-items: center;
    }
    .modal-content-custom {
        background: white; padding: 40px; border-radius: 10px;
        max-width: 600px; width: 90%; text-align: center; position: relative;
    }
    .modal-btn {
        padding: 8px 20px; border: none; border-radius: 5px; font-weight: 700; cursor: pointer; margin: 5px;
    }
    .btn-save { background: var(--green); color: white; }
    .btn-cancel { background: #e74c3c; color: white; }
    
    .navbar-split-border {
        position: absolute; bottom: 0; left: 0; width: 100%; height: 3px;
        background: linear-gradient(90deg, #2ecc71 50%, #FFD700 50%); z-index: 1025;
    }
    .monochrome-icon { filter: grayscale(100%) contrast(1.2); }
    
    .hero-full-width-container {
        width: 100vw; margin-left: calc(-50vw + 50%); position: relative; overflow: hidden;
    }
    .hero-main-img-wrapper { position: relative; width: 100%; height: 60vh; }
    .hero-main-img { width: 100%; height: 100%; object-fit: cover; }
    .hero-overlay-gradient {
        position: absolute; bottom: 0; left: 0; width: 100%; height: 50%;
        background: linear-gradient(to bottom, transparent, #000); pointer-events: none;
    }
    
    .logo-popup-overlay {
        display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(20, 20, 20, 0.6); backdrop-filter: blur(20px);
        z-index: 99999; justify-content: center; align-items: center; cursor: pointer;
    }
    .logo-popup-img {
        max-width: 80%; max-height: 80%; filter: drop-shadow(0 10px 30px rgba(0,0,0,0.5));
        transition: transform 0.3s;
    }
    .logo-popup-img:hover { transform: scale(1.05); }
    
    .mobile-menu-container {
        position: fixed; top: 70px; right: -100%; width: 80%; max-width: 300px;
        height: calc(100vh - 70px); background: white; z-index: 1040;
        transition: right 0.3s ease-in-out; box-shadow: -5px 0 15px rgba(0,0,0,0.1);
        padding: 20px; display: flex; flex-direction: column; gap: 15px; overflow-y: auto;
    }
    .mobile-menu-container.active { right: 0; }
    .mobile-nav-link {
        font-size: 1.1rem; font-weight: 700; color: #333; text-decoration: none; padding: 10px 0; border-bottom: 1px solid #eee;
    }
    .mobile-next-match {
        background: var(--green); color: white; padding: 10px; border-radius: 5px; font-weight: 600; text-align: center;
    }
    
    .sponsor-logo-small {
        width: 100px; height: 100px; object-fit: contain; border-radius: 50%;
        background: white; padding: 10px; margin: 10px; transition: 0.3s; filter: grayscale(100%);
    }
    .sponsor-logo-small:hover { filter: none; transform: scale(1.1); }
    
    /* Hover Underline & Center Hero */
    .hover-underline {
        text-decoration: none !important;
        position: relative;
        cursor: pointer;
    }
    .hover-underline:after {
        content: ''; position: absolute; width: 0; height: 3px; bottom: 0; left: 50%;
        background: var(--white); transition: all 0.3s; transform: translateX(-50%);
    }
    .hover-underline:hover:after { width: 100%; }
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
    <div class="container-fluid p-0 mb-4" id="hero">
         {% set hero = data['news']['hero'] %}
         <div class="hero-full-width-container">
             <div class="hero-main-img-wrapper">
                 <img src="{{ '/uploads/' + hero.image_path if hero.image_path else url_for('static', filename='logo-tahkil-fc.png') }}" class="hero-main-img">
                 <div class="hero-overlay-gradient"></div>
                 
                 <div class="position-absolute bottom-0 start-0 w-100 p-5 container text-center">
                    <span class="badge bg-warning text-dark mb-2">FIRST TEAM</span>
                    <h1 class="text-white fw-bold fst-italic hover-underline display-4"
                        style="text-shadow: 2px 2px 4px rgba(0,0,0,0.8);"
                        onclick="openNewsModal('{{ hero.title }}', '{{ hero.subtitle }}', '{{ '/uploads/' + hero.image_path if hero.image_path else '' }}')">
                        {{ hero.title }}
                    </h1>
                    {% if admin %}
                    <div contenteditable="true" onblur="saveText('news_content', 'hero', 'title', this)" class="text-white bg-dark d-inline-block px-2">Edit Title</div>
                    <div contenteditable="true" onblur="saveText('news_content', 'hero', 'subtitle', this)" class="text-white bg-dark d-inline-block px-2">Edit Subtitle</div>
                    {% else %}
                    <p class="text-white h5" style="text-shadow: 1px 1px 3px rgba(0,0,0,0.8);">{{ hero.subtitle }}</p>
                    {% endif %}
                 </div>
                 
                 {% if admin %}
                 <form action="/upload/news/hero" method="post" enctype="multipart/form-data" class="position-absolute top-0 start-0 p-2">
                     <input type="file" name="image" onchange="this.form.submit()" style="display:none;" id="hero-upload">
                     <label for="hero-upload" class="btn btn-sm btn-warning"><i class="fas fa-camera"></i> Change Hero Image</label>
                 </form>
                 {% endif %}
             </div>
         </div>
    </div>
    
    <div class="container mb-5">
        <!-- Sub News Row -->
        <div class="row">
            {% for i in range(1, 5) %}
            {% set news_item = data['news']['news_' ~ i] %}
            <div class="col-md-3 col-6 mb-3">
                <div class="d-flex flex-column bg-light rounded shadow-sm sub-news-card h-100"
                     style="transition:0.3s; overflow:hidden; cursor:pointer;"
                     onclick="openNewsModal('{{ news_item.title }}', '{{ news_item.subtitle }}', '{{ '/uploads/' + news_item.image_path if news_item.image_path else '' }}')">

                    <div style="width: 100%; height: 150px; background: #333; position: relative;">
                        <img src="{{ '/uploads/' + news_item.image_path if news_item.image_path else '' }}" style="width:100%; height:100%; object-fit:cover;">
                        {% if admin %}
                        <form action="/upload/news/news_{{ i }}" method="post" enctype="multipart/form-data" class="position-absolute top-0 start-0 p-1" onclick="event.stopPropagation()">
                            <input type="file" name="image" onchange="this.form.submit()" style="display:none;" id="news-up-{{ i }}">
                            <label for="news-up-{{ i }}" class="badge bg-warning" style="cursor:pointer;">+</label>
                        </form>
                        {% endif %}
                    </div>
                    <div class="p-3 flex-grow-1">
                        <span class="text-success fw-bold d-block mb-1 fs-5"
                              contenteditable="{{ 'true' if admin else 'false' }}"
                              onclick="event.stopPropagation()"
                              onblur="saveText('news_content', 'news_{{ i }}', 'title', this)">
                              {{ news_item.title }}
                        </span> <!-- Title as Category/First Team -->

                        <small class="text-muted d-block fw-normal"
                               contenteditable="{{ 'true' if admin else 'false' }}"
                               onclick="event.stopPropagation()"
                               onblur="saveText('news_content', 'news_{{ i }}', 'subtitle', this)">
                               {{ news_item.subtitle }}
                        </small>

                        <div class="mt-2 text-end text-muted" style="font-size:0.7rem;" data-updated="{{ news_item.updated_at }}">
                            <!-- Time ago loaded via JS -->
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <!-- Sponsors -->
        <div class="row mt-5 justify-content-center text-center align-items-center" id="sponsors">
            {% for sponsor in data['sponsors'] %}
            <div class="col-6 col-md-3 position-relative">
                <img src="{{ '/uploads/' + sponsor.image_path if sponsor.image_path else 'https://via.placeholder.com/100x100?text=SPONSOR' }}" 
                     class="sponsor-logo-small">
                {% if admin %}
                <form action="/upload/sponsor/{{ sponsor.id }}" method="post" enctype="multipart/form-data" class="position-absolute top-0 start-50">
                    <input type="file" name="image" onchange="this.form.submit()" style="display:none;" id="sp-{{ sponsor.id }}">
                    <label for="sp-{{ sponsor.id }}" class="badge bg-secondary"><i class="fas fa-edit"></i></label>
                </form>
                {% endif %}
            </div>
            {% endfor %}
            {% if admin %}
            <div class="col-6 col-md-3 d-flex justify-content-center align-items-center">
                <button class="btn btn-outline-warning" onclick="addCard('sponsor')">+ Add Sponsor</button>
            </div>
            {% endif %}
        </div>
    </div>
    
    <!-- PLAYERS SECTION -->
    <div class="container-fluid py-5 bg-light" id="players">
        <div class="container">
            <h2 class="section-title">Pemain TAHKIL FC</h2>
            <div class="horizontal-scroll-container">
                {% for player in data['personnel']['player'] %}
                <div class="person-card" onclick="openPersonModal('{{ player.id }}', '{{ player.name }}', '{{ player.position }}', '{{ '/uploads/' + player.image_path if player.image_path else '' }}', '{{ player.nationality }}', '{{ player.joined }}', '{{ player.matches }}', '{{ player.goals }}')">
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
                <div class="person-card d-flex align-items-center justify-content-center" onclick="addCard('personnel', 'player')">
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
                <div class="person-card" onclick="openPersonModal('{{ coach.id }}', '{{ coach.name }}', '{{ coach.position }}', '{{ '/uploads/' + coach.image_path if coach.image_path else '' }}', '{{ coach.nationality }}', '{{ coach.joined }}', '{{ coach.matches }}', '{{ coach.goals }}')">
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
                {% if admin %}
                <div class="person-card d-flex align-items-center justify-content-center" onclick="addCard('personnel', 'coach')">
                    <i class="fas fa-plus fa-3x text-success"></i>
                </div>
                {% endif %}
            </div>
        </div>
    </div>

    <!-- MVP SECTION -->
    <div class="container-fluid py-5 bg-light" id="mvp">
        <div class="container">
            <h2 class="section-title">Pemain MVP TAHKIL FC</h2>
            <div class="horizontal-scroll-container">
                {% for mvp in data['personnel']['mvp'] %}
                <div class="person-card" onclick="openPersonModal('{{ mvp.id }}', '{{ mvp.name }}', '{{ mvp.position }}', '{{ '/uploads/' + mvp.image_path if mvp.image_path else '' }}', '{{ mvp.nationality }}', '{{ mvp.joined }}', '{{ mvp.matches }}', '{{ mvp.goals }}')">
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
                <div class="person-card d-flex align-items-center justify-content-center" onclick="addCard('personnel', 'mvp')">
                    <i class="fas fa-plus fa-3x text-warning"></i>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    
    <!-- AGENDA -->
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
    
    <!-- TURNAMEN -->
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

    <!-- MODALS -->

    <!-- PERSON MODAL -->
    <div id="person-modal" class="modal-overlay" onclick="closePersonModal()">
        <div class="modal-content-custom" onclick="event.stopPropagation()">
            <img id="pm-img" src="" style="width:150px; height:150px; border-radius:50%; object-fit:cover; margin-bottom:20px;">
            
            {% if admin %}
            <div class="mb-3">
                <label>Name:</label>
                <input type="text" id="pm-name-input" class="form-control text-center fw-bold">
            </div>
            <div class="mb-3">
                <label>Position:</label>
                <input type="text" id="pm-pos-input" class="form-control text-center text-muted">
            </div>
            <div class="row text-start mt-4">
                <div class="col-6 mb-2"><strong>Nationality:</strong> <input type="text" id="pm-nat-input" class="form-control form-control-sm"></div>
                <div class="col-6 mb-2"><strong>Joined:</strong> <input type="text" id="pm-join-input" class="form-control form-control-sm"></div>
                <div class="col-6 mb-2"><strong>Matches:</strong> <input type="text" id="pm-match-input" class="form-control form-control-sm"></div>
                <div class="col-6 mb-2"><strong>Goals:</strong> <input type="text" id="pm-goal-input" class="form-control form-control-sm"></div>
            </div>
            <div class="mt-4">
                <button class="modal-btn btn-cancel" onclick="closePersonModal()">Cancel</button>
                <button class="modal-btn btn-save" onclick="savePersonFull()">Save</button>
            </div>
            {% else %}
            <h2 id="pm-name">Name</h2>
            <h4 id="pm-role" class="text-muted">Position</h4>
            <div class="mt-4 text-start">
                <p><strong>Nationality:</strong> <span id="pm-nat">Indonesia</span></p>
                <p><strong>Joined:</strong> <span id="pm-join">2024</span></p>
                <p><strong>Matches:</strong> <span id="pm-match">10</span></p>
                <p><strong>Goals:</strong> <span id="pm-goal">5</span></p>
            </div>
            {% endif %}
        </div>
    </div>

    <!-- NEXT MATCH MODAL -->
    <div id="next-match-modal" class="modal-overlay" onclick="closeNextMatchModal()">
        <div class="modal-content-custom" onclick="event.stopPropagation()">
            <h3 class="section-title">Edit Next Match Info</h3>
            {% if admin %}
            <textarea id="next-match-input" class="form-control mb-3" rows="4"></textarea>
            <div>
                <button class="modal-btn btn-cancel" onclick="closeNextMatchModal()">Cancel</button>
                <button class="modal-btn btn-save" onclick="saveNextMatch()">Save</button>
            </div>
            {% else %}
            <p id="next-match-view" class="fs-4 fw-bold"></p>
            {% endif %}
        </div>
    </div>

    <!-- HISTORY MODAL -->
    <div id="history-modal" class="modal-overlay" onclick="closeHistoryModal()">
        <div class="modal-content-custom" onclick="event.stopPropagation()">
            <h2 style="color:var(--gold);">Sejarah TAHKIL FC</h2>
            <img src="{{ url_for('static', filename='logo-tahkil-fc.png') }}" style="width:150px; display:block; margin:20px auto;">

            {% if admin %}
            <textarea id="history-text-input" class="form-control mb-3" rows="6"></textarea>
            <div>
                <button class="modal-btn btn-cancel" onclick="closeHistoryModal()">Cancel</button>
                <button class="modal-btn btn-save" onclick="saveHistory()">Save</button>
            </div>
            {% else %}
            <p id="history-text-view" style="white-space: pre-line;">{{ data['settings'].get('history_text', '') }}</p>
            {% endif %}
        </div>
    </div>

    <!-- NEWS DETAIL MODAL -->
    <div id="news-modal" class="modal-overlay" onclick="document.getElementById('news-modal').style.display='none'">
        <div class="modal-content-custom" onclick="event.stopPropagation()" style="text-align:left;">
            <img id="news-modal-img" src="" style="width:100%; height:250px; object-fit:cover; border-radius:8px; mb-3;">
            <h3 id="news-modal-title" class="fw-bold mt-3 text-uppercase" style="color:var(--green)"></h3>
            <p id="news-modal-subtitle" class="lead text-muted"></p>
            <hr>
            <p class="text-muted small">Full news content would go here...</p>
            <div class="text-center mt-3">
                <button class="btn btn-secondary" onclick="document.getElementById('news-modal').style.display='none'">Close</button>
            </div>
        </div>
    </div>
    
    <!-- LOGO POPUP -->
    <div id="logo-popup" class="logo-popup-overlay" onclick="toggleLogoPopup()">
        <img src="{{ url_for('static', filename='logo-tahkil-fc.png') }}" class="logo-popup-img">
    </div>
    
    <footer class="bg-black text-white py-5 text-center mt-5">
        <div class="container">
            <h3 class="fw-bold mb-3">TAHFIZH <span class="text-warning">KILAT FC</span></h3>
            <p contenteditable="{{ 'true' if admin else 'false' }}" onblur="saveText('site_settings', 'footer_text', 'value', this)">
                {{ data['settings'].get('footer_text', '© 2026 TAHKIL FC. All rights reserved.') }}
            </p>
        </div>
    </footer>

    <script>
        // --- UI UTILS ---
        function toggleMobileMenu() { document.getElementById('mobile-menu').classList.toggle('active'); }
        function toggleLogoPopup() {
            const popup = document.getElementById('logo-popup');
            popup.style.display = (popup.style.display === 'flex') ? 'none' : 'flex';
        }

        // --- TIME AGO LOGIC ---
        function timeAgo(dateString) {
            if (!dateString) return "";
            const date = new Date(dateString + "Z"); // Assume UTC if not specified
            const now = new Date();
            const seconds = Math.floor((now - date) / 1000);

            let interval = seconds / 31536000;
            if (interval > 1) return Math.floor(interval) + " tahun lalu";
            interval = seconds / 2592000;
            if (interval > 1) return Math.floor(interval) + " bulan lalu";
            interval = seconds / 86400;
            if (interval > 3) return date.toLocaleDateString(); // > 3 days, show date
            if (interval > 1) return Math.floor(interval) + " hari lalu";
            interval = seconds / 3600;
            if (interval > 1) return Math.floor(interval) + " jam lalu";
            interval = seconds / 60;
            if (interval > 1) return Math.floor(interval) + " menit lalu";
            return "Baru saja";
        }

        // Apply Time Ago
        document.querySelectorAll('[data-updated]').forEach(el => {
            const ts = el.getAttribute('data-updated');
            if(ts && ts != 'None') el.innerText = timeAgo(ts.replace(" ", "T"));
        });

        // --- API & SAVING ---
        function saveText(table, id, field, el_or_obj) {
            let value;
            if (el_or_obj.value !== undefined) value = el_or_obj.value;
            else value = el_or_obj.innerText;

            fetch('/api/update-text', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ table, id, field, value })
            });
        }
        
        function addCard(type, sectionOrRole) {
             let body = { type };
             if (type === 'agenda') body.section = sectionOrRole;
             else if (type === 'personnel') body.role = sectionOrRole;

             fetch('/api/add-card', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(body)
            }).then(() => location.reload());
        }

        // --- MODALS ---
        let currentPersonId = null;

        function openPersonModal(id, name, position, img, nat, joined, matches, goals) {
            currentPersonId = id;
            document.getElementById('pm-img').src = img || '{{ url_for("static", filename="logo-tahkil-fc.png") }}';
            document.getElementById('person-modal').style.display = 'flex';
            
            if (document.getElementById('pm-name-input')) { // Admin
                document.getElementById('pm-name-input').value = name;
                document.getElementById('pm-pos-input').value = position;
                document.getElementById('pm-nat-input').value = nat || 'Indonesia';
                document.getElementById('pm-join-input').value = joined || '2024';
                document.getElementById('pm-match-input').value = matches || '0';
                document.getElementById('pm-goal-input').value = goals || '0';
            } else { // View
                document.getElementById('pm-name').innerText = name;
                document.getElementById('pm-role').innerText = position;
                document.getElementById('pm-nat').innerText = nat || 'Indonesia';
                document.getElementById('pm-join').innerText = joined || '2024';
                document.getElementById('pm-match').innerText = matches || '0';
                document.getElementById('pm-goal').innerText = goals || '0';
            }
        }
        function closePersonModal() { document.getElementById('person-modal').style.display = 'none'; }

        function savePersonFull() {
            if(!currentPersonId) return;
            // Simple sequential saves
            ['name', 'position', 'nationality', 'joined', 'matches', 'goals'].forEach(field => {
                let suffix = (field === 'name' || field === 'position') ? '-input' : '-input'; // correction: IDs use short codes
                let idMap = {'name':'pm-name-input', 'position':'pm-pos-input', 'nationality':'pm-nat-input', 'joined':'pm-join-input', 'matches':'pm-match-input', 'goals':'pm-goal-input'};
                let val = document.getElementById(idMap[field]).value;
                saveText('personnel', currentPersonId, field, {value: val});
            });
            setTimeout(() => location.reload(), 500);
        }

        // Next Match
        function openNextMatchModal() {
            const currentText = document.getElementById('next-match-display').innerText;
            document.getElementById('next-match-modal').style.display = 'flex';
            if (document.getElementById('next-match-input')) {
                document.getElementById('next-match-input').value = currentText;
            } else {
                document.getElementById('next-match-view').innerText = currentText;
            }
        }
        function closeNextMatchModal() { document.getElementById('next-match-modal').style.display = 'none'; }
        function saveNextMatch() {
            const val = document.getElementById('next-match-input').value;
            fetch('/api/update-text', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ table: 'site_settings', id: 'next_match_text', value: val })
            }).then(() => location.reload());
        }

        // History
        function openHistoryModal() {
            document.getElementById('history-modal').style.display = 'flex';
            // Value is pre-rendered in hidden variable or pulled from DOM?
            // Better to pull from settings object exposed to JS
            // But we can just use the rendered view text if not admin

            // For admin, we want the raw value.
            // A simple hack: we use the value passed in JS or render it into a hidden div.
            // Let's grab it from a JS variable injection.
             const val = `{{ data['settings'].get('history_text', '') | safe }}`;
             if (document.getElementById('history-text-input')) {
                document.getElementById('history-text-input').value = val;
            } 
        }
        function closeHistoryModal() { document.getElementById('history-modal').style.display = 'none'; }
        function saveHistory() {
             const val = document.getElementById('history-text-input').value;
             fetch('/api/update-text', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ table: 'site_settings', id: 'history_text', value: val })
            }).then(() => location.reload());
        }

        // News Modal
        function openNewsModal(title, subtitle, img) {
            document.getElementById('news-modal-title').innerText = title;
            document.getElementById('news-modal-subtitle').innerText = subtitle;
            document.getElementById('news-modal-img').src = img || '{{ url_for("static", filename="logo-tahkil-fc.png") }}';
            document.getElementById('news-modal').style.display = 'flex';
        }

        // Countdown
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

        // Hover Animation
        document.querySelectorAll('.sub-news-card').forEach(card => {
            card.addEventListener('mouseenter', () => { card.style.transform = 'scale(1.05)'; card.style.zIndex = '10'; });
            card.addEventListener('mouseleave', () => { card.style.transform = 'scale(1)'; card.style.zIndex = '1'; });
        });
    </script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)
