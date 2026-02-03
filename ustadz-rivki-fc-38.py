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
    # Existing tables
    c.execute('''CREATE TABLE IF NOT EXISTS agenda_content (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    status TEXT,
                    price TEXT,
                    event_date TEXT
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
    try: c.execute("ALTER TABLE news_content ADD COLUMN details TEXT")
    except: pass
    try: c.execute("ALTER TABLE agenda_content ADD COLUMN event_date TEXT")
    except: pass
    try: c.execute("ALTER TABLE agenda_content ADD COLUMN details TEXT")
    except: pass
    try: c.execute("ALTER TABLE agenda_content ADD COLUMN image_path TEXT")
    except: pass

    # Sponsors
    c.execute('''CREATE TABLE IF NOT EXISTS sponsors (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    image_path TEXT,
                    size INTEGER DEFAULT 80
                )''')
    try: c.execute("ALTER TABLE sponsors ADD COLUMN size INTEGER DEFAULT 80")
    except: pass
    
    # Site Settings
    c.execute('''CREATE TABLE IF NOT EXISTS site_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )''')

    # --- ACADEMY TABLES ---
    # Candidates
    c.execute('''CREATE TABLE IF NOT EXISTS candidates (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    dob TEXT,
                    category TEXT,
                    position TEXT,
                    guardian TEXT,
                    guardian_wa TEXT,
                    photo_path TEXT,
                    status TEXT DEFAULT 'pending',
                    username TEXT,
                    password_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    try: c.execute("ALTER TABLE candidates ADD COLUMN username TEXT")
    except: pass
    try: c.execute("ALTER TABLE candidates ADD COLUMN password_hash TEXT")
    except: pass

    # Academy Students
    c.execute('''CREATE TABLE IF NOT EXISTS academy_students (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    dob TEXT,
                    category TEXT,
                    position TEXT,
                    guardian TEXT,
                    guardian_wa TEXT,
                    photo_path TEXT,
                    user_id TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    # Academy Users
    c.execute('''CREATE TABLE IF NOT EXISTS academy_users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT,
                    role TEXT,
                    related_id TEXT
                )''')
    
    # Finance Bills
    c.execute('''CREATE TABLE IF NOT EXISTS finance_bills (
                    id TEXT PRIMARY KEY,
                    student_id TEXT,
                    month TEXT,
                    amount INTEGER,
                    status TEXT DEFAULT 'unpaid',
                    proof_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    # Attendance
    c.execute('''CREATE TABLE IF NOT EXISTS academy_attendance (
                    id TEXT PRIMARY KEY,
                    date TEXT,
                    student_id TEXT,
                    status TEXT,
                    coach_id TEXT
                )''')

    # Evaluations
    c.execute('''CREATE TABLE IF NOT EXISTS academy_evaluations (
                    id TEXT PRIMARY KEY,
                    month TEXT,
                    student_id TEXT,
                    coach_id TEXT,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    
    # Seed Coach
    c.execute("INSERT OR IGNORE INTO academy_users (username, password_hash, role, related_id) VALUES ('coach', ?, 'coach', 'coach_1')", (generate_password_hash('c04ch'),))
    c.execute("UPDATE academy_users SET password_hash = ? WHERE username = 'coach'", (generate_password_hash('tahkilfc'),))

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
# get_db_connection is now defined above init_db

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

def generate_monthly_bills():
    conn = get_db_connection()
    c = conn.cursor()
    
    start_date = datetime.date(2026, 2, 1)
    now = datetime.date.today()
    
    if now < start_date:
        start_date = datetime.date(now.year, now.month, 1)
        
    current = start_date
    while current <= now:
        months_id = {1:'Januari', 2:'Februari', 3:'Maret', 4:'April', 5:'Mei', 6:'Juni', 7:'Juli', 8:'Agustus', 9:'September', 10:'Oktober', 11:'November', 12:'Desember'}
        month_name = f"{months_id[current.month]} {current.year}"
        
        c.execute("SELECT id FROM academy_students")
        students = c.fetchall()
        for s in students:
            c.execute("SELECT 1 FROM finance_bills WHERE student_id=? AND month=?", (s['id'], month_name))
            if not c.fetchone():
                bid = f"bill_{s['id']}_{current.strftime('%Y%m')}"
                c.execute("INSERT INTO finance_bills (id, student_id, month, amount, status) VALUES (?,?,?,?, 'unpaid')", 
                          (bid, s['id'], month_name, 150000))
        
        if current.month == 12:
            current = datetime.date(current.year + 1, 1, 1)
        else:
            current = datetime.date(current.year, current.month + 1, 1)
            
    conn.commit()
    conn.close()

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

    # Determine Countdown Target
    now_str = datetime.datetime.now().isoformat()
    target_countdown_time = data['settings'].get('next_match_time', now_str)
    
    # Filter for future agenda items
    future_agendas = []
    for item in agenda_latihan:
        ed = item.get('event_date')
        if ed and ed > now_str:
            future_agendas.append(ed)
    
    if future_agendas:
        future_agendas.sort()
        target_countdown_time = future_agendas[0]

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
    
    return render_page(HTML_UR_FC, 
                       data=data, 
                       agenda_latihan=agenda_latihan, 
                       turnamen=turnamen,
                       target_countdown_time=target_countdown_time,
                       admin=session.get('admin', False))

@app.route('/login', methods=['POST'])
def login():
    uid = request.form.get('userid')
    pwd = request.form.get('password')
    if uid == 'adminwebsite' and check_password_hash(ADMIN_PASSWORD_HASH, pwd):
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
        try:
            img = Image.open(file)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            
            # Resize
            max_width = 1024
            if img.width > max_width:
                ratio = max_width / float(img.width)
                new_height = int((float(img.height) * float(ratio)))
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Save as JPEG
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
            print(f"Error processing image: {e}")
            return "Error processing image", 500
        
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
    allowed_fields = ['title', 'subtitle', 'category', 'name', 'position', 'role', 'status', 'price', 'value', 'nationality', 'joined', 'matches', 'goals', 'event_date', 'details', 'size']

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

@app.route('/api/delete-item', methods=['POST'])
def api_delete_item():
    if not session.get('admin'): return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    table = data.get('table')
    id = data.get('id')
    
    if table not in ['personnel', 'sponsors', 'agenda_content', 'agenda_list']:
        return jsonify({'error': 'Invalid table'}), 400
        
    conn = get_db_connection()
    c = conn.cursor()
    
    if table == 'agenda_content':
        # Also delete from list
        c.execute("DELETE FROM agenda_list WHERE id = ?", (id,))
        c.execute("DELETE FROM agenda_content WHERE id = ?", (id,))
    else:
        c.execute(f"DELETE FROM {table} WHERE id = ?", (id,))
        
    conn.commit()
    conn.close()
    return jsonify({'success': True})

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
        font-weight: 600;
        transition: 0.2s;
        margin-left: 150px;
    }
    
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
        z-index: 1040;
    }
    .nav-item-custom {
        color: #333; text-transform: uppercase; font-weight: 700; text-decoration: none; font-size: 0.9rem; position: relative;
    }
    .nav-item-custom:after {
        content: ''; position: absolute; width: 0; height: 3px; bottom: -5px; left: 0; background-color: #FFD700; transition: width 0.3s;
    }
    .nav-item-custom:hover:after { width: 100%; }
    
    .nav-split-container {
        display: flex;
        width: 100%;
        height: 100%;
    }
    .nav-box-left {
        width: 50%;
        display: flex;
        align-items: center;
        border-bottom: 3px solid #2ecc71;
        padding-left: 5%;
        position: relative;
    }
    .nav-box-right {
        width: 50%;
        display: flex;
        align-items: center;
        border-bottom: 3px solid #FFD700;
        padding-left: 20px;
        position: relative;
    }
    .nav-box-links {
        display: flex;
        gap: 20px;
        margin-left: 30px;
    }
    .navbar-logo-desktop {
        height: 85px; margin-top: -15px; transition: 0.3s; filter: drop-shadow(0 2px 5px rgba(0,0,0,0.2)); cursor: pointer; z-index: 2000; position: relative;
    }
    .mobile-separator {
        height: 1px; background-color: #ddd; margin: 15px 0; width: 100%;
    }

    @media (max-width: 992px) {
        .top-bar { display: none; }
        .main-navbar { justify-content: space-between; padding: 0 20px; }
        .navbar-logo-img { height: 50px; }
    }
</style>

<div class="top-bar">
    <div class="top-bar-left">
        <div class="next-match-mini" {% if admin %}style="cursor: pointer;" onclick="openNextMatchModal()"{% else %}style="cursor: default;"{% endif %}>
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

<div class="main-navbar p-0 d-none d-lg-flex">
    <div class="nav-split-container">
        <!-- Left Box (Green) -->
        <div class="nav-box-left">
            <div onclick="toggleLogoPopup()">
                <a href="javascript:void(0)">
                    <img src="{{ url_for('static', filename='logo-tahkil-fc.png') }}" class="navbar-logo-desktop" alt="TAHKIL FC">
                </a>
            </div>
            <div class="nav-box-links">
                <a href="{{ url_for('index') }}#hero" class="nav-item-custom">Home</a>
                <a href="{{ url_for('index') }}#players" class="nav-item-custom">Pemain</a>
                <a href="{{ url_for('index') }}#coaches" class="nav-item-custom">Pelatih</a>
                <a href="{{ url_for('index') }}#mvp" class="nav-item-custom">MVP</a>
                <a href="{{ url_for('index') }}#agenda-latihan" class="nav-item-custom">Agenda</a>
                <a href="{{ url_for('index') }}#main-partners" class="nav-item-custom">Sponsors</a>
            </div>
        </div>
        <!-- Right Box (Yellow) -->
        <div class="nav-box-right">
             <div class="nav-box-links">
                <a href="{{ url_for('list_players') }}" class="nav-item-custom">DAFTAR</a>
                <a href="{{ url_for('list_bills') }}" class="nav-item-custom">KEUANGAN</a>
                <a href="{{ url_for('list_reports') }}" class="nav-item-custom">RAPOR</a>
             </div>
        </div>
    </div>
</div>

<!-- Mobile Header -->
<div class="main-navbar d-lg-none justify-content-between px-3">
    <div class="navbar-logo-container" onclick="toggleLogoPopup()" style="position:static; transform:none;">
        <img src="{{ url_for('static', filename='logo-tahkil-fc.png') }}" class="navbar-logo-img" style="height:50px;">
    </div>
    <div class="fw-bold fs-4 position-absolute start-50 translate-middle-x" style="white-space: nowrap;">TAHFIZH KILAT FC</div>
    <button class="btn border-0" onclick="toggleMobileMenu()"><i class="fas fa-bars fa-2x"></i></button>
</div>

<div id="mobile-menu" class="mobile-menu-container">
    <div class="mobile-next-match">{{ data['settings'].get('next_match_text', 'Next Match: TAHKIL FC (Jan 2026)') }}</div>
    <a href="#hero" class="mobile-nav-link">Home</a>
    <a href="#players" class="mobile-nav-link">Pemain</a>
    <a href="#coaches" class="mobile-nav-link">Pelatih</a>
    <a href="#mvp" class="mobile-nav-link">MVP</a>
    <a href="#agenda-latihan" class="mobile-nav-link">Agenda</a>
    <a href="#main-partners" class="mobile-nav-link">Sponsors</a>
    
    <div class="mobile-separator"></div>
    <a href="{{ url_for('list_players') }}" class="mobile-nav-link">DAFTAR</a>
    <a href="{{ url_for('list_bills') }}" class="mobile-nav-link">KEUANGAN</a>
    <a href="{{ url_for('list_reports') }}" class="mobile-nav-link">RAPOR</a>
    
    <div class="mt-auto d-flex flex-column gap-3">
        <div class="history-btn justify-content-center d-lg-none" onclick="toggleFullScreen()" style="background: #111; color: #FFD700;">
            <i class="fas fa-expand"></i>
            Layar Penuh
        </div>
        <div class="history-btn justify-content-center" onclick="openHistoryModal()">
            <img src="{{ url_for('static', filename='logo-tahkil-fc.png') }}" class="monochrome-icon">
            Lihat Sejarah
        </div>
        {% if not admin %}
        <button onclick="document.getElementById('login-modal').style.display='flex'" class="btn btn-outline-dark w-100">Admin Login</button>
        {% else %}
        <a href="/logout" class="btn btn-danger w-100">Logout</a>
        {% endif %}
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

<!-- SHARED ASSETS INJECTED VIA NAVBAR -->
<!-- HISTORY MODAL -->
<div id="history-modal" class="modal-overlay" onclick="closeHistoryModal()">
    <div class="modal-content-custom" onclick="event.stopPropagation()">
        <h2 style="color:var(--gold);">Sejarah TAHKIL FC</h2>
        <div style="width:100%; aspect-ratio:16/9; background:#eee; margin-bottom:20px; position:relative; overflow:hidden;">
            {% set history_img = data['settings'].get('history_image') %}
            <img id="history-main-img" src="{{ '/uploads/' + history_img if history_img else url_for('static', filename='logo-tahkil-fc.png') }}" style="width:100%; height:100%; object-fit:cover;">
            {% if admin %}
            <form action="/upload/history/main" method="post" enctype="multipart/form-data" class="position-absolute bottom-0 end-0 p-2">
                <input type="file" name="image" onchange="this.form.submit()" style="display:none;" id="history-upload">
                <label for="history-upload" class="btn btn-sm btn-warning"><i class="fas fa-camera"></i> Change Image</label>
            </form>
            {% endif %}
        </div>
        {% if admin %}
        <textarea id="history-text-input" class="form-control mb-3" rows="10"></textarea>
        <div>
            <button class="modal-btn btn-cancel" onclick="closeHistoryModal()">Cancel</button>
            <button class="modal-btn btn-save" onclick="saveHistory()">Save</button>
        </div>
        {% else %}
        <div id="history-text-view" style="white-space: pre-wrap;">{{ data['settings'].get('history_text', '') }}</div>
        {% endif %}
    </div>
</div>

<!-- LOGO POPUP -->
<div id="logo-popup" class="logo-popup-overlay" onclick="toggleLogoPopup()">
    <img src="{{ url_for('static', filename='logo-tahkil-fc.png') }}" class="logo-popup-img">
</div>

<script>
    // SHARED SCRIPTS
    function toggleMobileMenu() { 
        document.getElementById('mobile-menu').classList.toggle('active');
        document.body.classList.toggle('no-scroll');
    }
    function toggleLogoPopup() {
        const popup = document.getElementById('logo-popup');
        popup.style.display = (popup.style.display === 'flex') ? 'none' : 'flex';
    }
    function toggleFullScreen() {
        var doc = window.document;
        var docEl = doc.documentElement;
        var requestFullScreen = docEl.requestFullscreen || docEl.mozRequestFullScreen || docEl.webkitRequestFullScreen || docEl.msRequestFullscreen;
        var cancelFullScreen = doc.exitFullscreen || doc.mozCancelFullScreen || doc.webkitExitFullscreen || doc.msExitFullscreen;
        if(!doc.fullscreenElement && !doc.mozFullScreenElement && !doc.webkitFullscreenElement && !doc.msFullscreenElement) {
            requestFullScreen.call(docEl);
        } else {
            cancelFullScreen.call(doc);
        }
    }
    
    // History
    function openHistoryModal() {
        document.getElementById('history-modal').style.display = 'flex';
            const val = `{{ data['settings'].get('history_text', '') | safe }}`;
            if (document.getElementById('history-text-input')) {
            document.getElementById('history-text-input').value = val;
        } 
    }
    function closeHistoryModal() { document.getElementById('history-modal').style.display = 'none'; }
    function saveHistory() {
            const val = document.getElementById('history-text-input').value;
            saveText('site_settings', 'history_text', 'value', {value: val});
    }

    // Save Text Helper
    function saveText(table, id, field, el_or_obj) {
        let value;
        if (el_or_obj.value !== undefined) value = el_or_obj.value;
        else value = el_or_obj.innerText;
        
        fetch('/api/update-text', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ table, id, field, value })
        }).then(() => {
            if(table === 'site_settings' && id === 'next_match_time') location.reload();
            else if(table === 'site_settings' && id === 'history_text') location.reload();
        });
    }
</script>
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
        scrollbar-width: thin;
        scrollbar-color: var(--green) rgba(0,0,0,0.1);
    }
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(0,0,0,0.1); 
    }
    ::-webkit-scrollbar-thumb {
        background: var(--green); 
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #004d40; 
    }
    .scroll-btn {
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        background: var(--green);
        color: white;
        border: none;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        z-index: 10;
        opacity: 0.9;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .scroll-btn:hover {
        background: #ffd700;
        color: black;
        transform: translateY(-50%) scale(1.1);
    }
    .scroll-left { left: 10px; }
    .scroll-right { right: 10px; }
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
        position: relative;
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
        max-width: 800px; width: 90%; text-align: center; position: relative;
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
        width: 100%; margin: 0; position: relative; overflow: hidden;
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
        padding: 20px; padding-bottom: 100px; display: flex; flex-direction: column; gap: 15px; overflow-y: auto;
    }
    .mobile-menu-container.active { right: 0; }
    .mobile-nav-link {
        font-size: 1.1rem; font-weight: 700; color: #333; text-decoration: none; padding: 10px 0; border-bottom: 1px solid #eee;
    }
    .mobile-next-match {
        background: var(--green); color: white; padding: 10px; border-radius: 5px; font-weight: 600; text-align: center;
    }
    
    .sponsor-logo-small {
        /* Default size, but overridden by inline styles */
        width: 80px; height: 80px; 
        object-fit: contain; border-radius: 50%;
        background: white; padding: 5px; margin: 5px; transition: 0.3s; filter: grayscale(100%);
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
    
    .no-scroll { overflow: hidden; }

    /* History Modal specific fixes */
    #history-text-view {
        text-align: justify;
        text-indent: 2em;
        font-size: 0.9rem;
        line-height: 1.6;
        word-wrap: break-word;
    }
    #history-modal .modal-content-custom {
        max-height: 80vh;
        overflow-y: auto;
    }
    
    .trash-btn {
        background: red; color: white; border: none; border-radius: 50%; width: 25px; height: 25px;
        display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 0.8rem;
    }
    .trash-btn:hover { background: darkred; }
    
    .time-box-wrapper {
        display: flex; flex-direction: column; gap: 8px; width: 100%; margin-bottom: 20px;
    }
    .time-box {
        background: #f8f9fa; border-left: 5px solid var(--gold); padding: 10px 15px;
        font-weight: 700; color: #333; text-transform: uppercase;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); font-size: 0.9rem;
    }
    .time-box-mini {
        background: white; padding: 4px 8px; border-radius: 4px; margin: 0 2px; 
        border: 1px solid #ddd; display: inline-block;
    }
    .agenda-modal-map-overlay {
        position: absolute; top: 10px; left: 10px; z-index: 10;
        background: rgba(255, 255, 255, 0.9); padding: 8px 15px; border-radius: 30px;
        display: flex; align-items: center; gap: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        font-weight: 700; font-size: 0.8rem; cursor: pointer; text-decoration: none; color: black;
        transition: 0.3s;
    }
    .agenda-modal-map-overlay:hover { background: var(--gold); transform: scale(1.05); }
    
    .custom-range-slider::-webkit-slider-runnable-track {
        background: #e0f7fa; 
        box-shadow: 0 0 8px rgba(135, 206, 250, 0.8);
        border-radius: 5px;
        height: 6px;
    }
    .custom-range-slider::-webkit-slider-thumb {
        margin-top: -5px; /* Adjust thumb position */
    }
    
    /* Agenda Desktop Fix & Camera Button */
    @media (min-width: 992px) {
        #agenda-modal-img {
            max-height: 55vh !important;
            width: auto !important;
            max-width: 100% !important;
            display: block;
            margin: 0 auto;
        }
    }
    .camera-btn {
        position: absolute; bottom: 10px; right: 10px;
        background: rgba(255, 215, 0, 0.9); color: black;
        border: none; border-radius: 50%; width: 40px; height: 40px;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; transition: 0.3s; z-index: 20;
    }
    .camera-btn:hover { transform: scale(1.1); background: #fff; }
    
    /* ACADEMY STYLES */
    .mode-toggle-btn {
        width: 100%;
        background-color: #FFD700;
        color: black;
        border: none;
        padding: 4px 0;
        font-size: 0.8rem;
        font-weight: 700;
        margin-top: 5px;
        margin-bottom: 15px;
        border-radius: 4px;
        cursor: pointer;
        transition: 0.2s;
        text-transform: uppercase;
    }
    .mode-toggle-btn:hover {
        background-color: #e6c200;
        transform: translateY(-1px);
    }

    .bottom-nav {
        position: fixed; bottom: 0; left: 0; width: 100%; height: 75px;
        background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-top: 1px solid rgba(255, 215, 0, 0.3);
        display: flex; justify-content: space-around; align-items: center;
        z-index: 9999; padding-bottom: 10px;
        box-shadow: 0 -5px 20px rgba(0,0,0,0.1);
    }
    .bottom-nav-item {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        text-decoration: none; color: #555; transition: 0.3s;
        font-size: 0.7rem; font-weight: 700; flex: 1; height: 100%;
        position: relative;
    }
    .bottom-nav-item i { 
        font-size: 1.5rem; margin-bottom: 5px; color: #333; 
        background: #f8f9fa; padding: 10px; border-radius: 50%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1); transition: 0.3s;
    }
    .bottom-nav-item:hover i { background: var(--gold); color: black; transform: translateY(-5px); }
    
    /* Academy Tab Active State */
    .tab-btn { padding: 10px 20px; border: none; background: #eee; font-weight: 600; border-radius: 20px; margin-right: 5px; }
    .tab-btn.active { background: var(--green); color: white; }
    
    .status-badge { padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; }
    .status-paid { background: #d1e7dd; color: #0f5132; }
    .status-unpaid { background: #f8d7da; color: #842029; }
    .status-pending { background: #fff3cd; color: #664d03; }
    
    /* LOADER OVERLAY */
    .loader-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(255, 255, 255, 0.95); z-index: 10000;
        display: none; flex-direction: column; justify-content: center; align-items: center;
    }
    .sketch-ball {
        font-size: 80px; color: #FFD700;
        animation: spin 3s linear infinite;
        filter: drop-shadow(2px 2px 0px #000);
    }
    @keyframes spin { 100% { transform: rotate(360deg); } }
    
    .check-mark-container {
        display: none;
        position: relative;
        width: 100px; height: 100px;
        border: 5px solid #FFD700;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        animation: scaleUp 0.5s ease-out;
    }
    .check-icon {
        font-size: 50px; color: #FFD700;
    }
    @keyframes scaleUp { 0% { transform: scale(0); } 100% { transform: scale(1); } }
    
    .loading-text {
        margin-top: 20px; font-weight: bold; color: #333; font-size: 1.2rem;
    }
    
    /* NEW UI UPDATES */
    .hard-card-bg {
        background: radial-gradient(circle at 10% 20%, #004d40 0%, #111 90%),
                    repeating-linear-gradient(45deg, rgba(255,215,0,0.05) 0px, rgba(255,215,0,0.05) 2px, transparent 2px, transparent 10px);
        border: 2px solid #FFD700;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        color: white;
        border-radius: 15px;
        padding: 20px;
        position: relative;
        overflow: hidden;
    }
    .hard-card-bg::before {
        content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-image: radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px);
        background-size: 20px 20px;
        opacity: 0.3; pointer-events: none;
    }
    .coach-notebook-bg {
        background-color: #fdfbf7;
        background-image: linear-gradient(#e1e1e1 1px, transparent 1px);
        background-size: 100% 1.5em;
        padding: 30px;
        border: 1px solid #d3d3d3;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.1);
        font-family: 'Patrick Hand', cursive;
        color: #333;
        border-radius: 5px;
        position: relative;
    }
    .coach-notebook-bg::before {
        content: ''; position: absolute; top: 0; left: 20px; bottom: 0; width: 2px; background: #ff9999;
    }
    .font-sketch { font-family: 'Patrick Hand', cursive; }
    .btn-thin-red {
        width: 100%;
        background-color: #d32f2f;
        color: white;
        padding: 4px 0;
        font-size: 0.8rem;
        font-weight: 700;
        border: none;
        border-radius: 4px;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: 0.3s;
    }
    .btn-thin-red:hover { background-color: #b71c1c; color: white; }
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
    <link href="https://fonts.googleapis.com/css2?family=Patrick+Hand&display=swap" rel="stylesheet">
    {{ styles|safe }}
    {% if admin %}
    <style>
        #news-modal-details {
            text-align: justify !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
            white-space: pre-wrap;
        }
        #news-modal .modal-content-custom {
            max-height: 90vh !important;
            overflow-y: auto !important;
            display: flex;
            flex-direction: column;
        }
    </style>
    {% endif %}
    {% if not admin %}
    <style>
        #news-modal-details {
            text-align: justify !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
            white-space: pre-wrap;
        }
        #news-modal .modal-content-custom {
            max-height: 80vh !important;
            overflow-y: auto !important;
        }
    </style>
    {% endif %}
</head>
<body>
    {{ navbar|safe }}

    <!-- LOADER -->
    <div id="loader-overlay" class="loader-overlay">
        <div id="loader-ball" class="sketch-ball"><i class="fas fa-futbol"></i></div>
        <div id="loader-success" style="display:none;" class="check-mark-container">
            <i class="fas fa-check check-icon"></i>
        </div>
        <div id="loader-text" class="loading-text">Memproses Data...</div>
    </div>
    
    <!-- HERO SECTION -->
    <div class="container-fluid p-0 mb-4" id="hero">
         {% set hero = data['news']['hero'] %}
         <div class="hero-full-width-container">
             <div class="hero-main-img-wrapper">
                 <img src="{{ '/uploads/' + hero.image_path if hero.image_path else url_for('static', filename='logo-tahkil-fc.png') }}" class="hero-main-img">
                 <div class="hero-overlay-gradient"></div>
                 
                 <div class="position-absolute bottom-0 start-0 w-100 p-5 d-flex flex-column align-items-center justify-content-end text-center">
                    <span class="badge bg-warning text-dark mb-2">FIRST TEAM</span>
                    <h1 class="text-white fw-bold fst-italic hover-underline display-4" 
                        style="text-shadow: 2px 2px 4px rgba(0,0,0,0.8);"
                        onclick="openNewsModal('hero', 'hero')">
                        {{ hero.title }}
                    </h1>
                    <p class="text-white h5" style="text-shadow: 1px 1px 3px rgba(0,0,0,0.8);">{{ hero.subtitle }}</p>
                 </div>
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
                     onclick="openNewsModal('news_{{ i }}', 'sub')">
                    
                    <div style="width: 100%; height: 150px; background: #333; position: relative;">
                        <img src="{{ '/uploads/' + news_item.image_path if news_item.image_path else '' }}" style="width:100%; height:100%; object-fit:cover;">
                    </div>
                    <div class="p-3 flex-grow-1">
                        <span class="text-success fw-bold d-block mb-1" style="font-size: 1rem; line-height: 1.2;">
                              {{ news_item.title }}
                        </span> 
                        
                        <small class="text-muted d-block fw-normal">
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
        <div class="d-flex flex-column flex-md-row align-items-center justify-content-center mt-5" id="sponsors">
            <div class="d-flex align-items-center mb-3 mb-md-0 me-md-4">
                <span class="fw-bold text-uppercase me-3" style="font-size: 1.1rem; letter-spacing: 1px;">Main Partners</span>
                <span class="fs-4 text-muted">|</span>
            </div>
            <div class="d-flex flex-wrap justify-content-center align-items-center gap-4">
                {% for sponsor in data['sponsors'] %}
                <div class="position-relative d-flex align-items-center flex-column">
                    {% set size = sponsor.size if sponsor.size else 80 %}
                    <img id="sp-img-{{ sponsor.id }}" src="{{ '/uploads/' + sponsor.image_path if sponsor.image_path else 'https://via.placeholder.com/100x100?text=SPONSOR' }}?t={{ timestamp }}" 
                         class="sponsor-logo-small" style="width: {{ size }}px; height: {{ size }}px;">
                    {% if admin %}
                    <div class="position-absolute top-0 start-50 translate-middle-x d-flex gap-1" style="z-index: 10;">
                        <button class="trash-btn" onclick="deleteItem('sponsors', '{{ sponsor.id }}')"><i class="fas fa-trash"></i></button>
                        <form action="/upload/sponsor/{{ sponsor.id }}" method="post" enctype="multipart/form-data">
                            <input type="file" name="image" onchange="this.form.submit()" style="display:none;" id="upload-sponsor-{{ sponsor.id }}">
                            <label for="upload-sponsor-{{ sponsor.id }}" class="trash-btn" style="background: #007bff;"><i class="fas fa-camera"></i></label>
                        </form>
                    </div>
                    <div class="mt-2">
                        <input type="range" class="form-range custom-range-slider" min="40" max="200" step="5" value="{{ size }}" style="width: 100px;" 
                               oninput="previewResize('{{ sponsor.id }}', this.value)"
                               onchange="saveText('sponsors', '{{ sponsor.id }}', 'size', this)">
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
                {% if admin %}
                <div>
                    <button class="btn btn-outline-warning btn-sm" onclick="addCard('sponsor')">+</button>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    
    <!-- PLAYERS SECTION -->
    <div class="container-fluid py-5 bg-light" id="players">
        <div class="container position-relative">
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
                    <div class="position-absolute top-0 end-0 p-2 d-flex gap-2" onclick="event.stopPropagation()">
                        <button class="btn btn-sm btn-danger" onclick="deleteItem('personnel', '{{ player.id }}')"><i class="fas fa-trash"></i></button>
                    </div>
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
        <div class="container position-relative">
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
                    <div class="position-absolute top-0 end-0 p-2 d-flex gap-2" onclick="event.stopPropagation()" style="z-index: 10;">
                        <button class="btn btn-sm btn-danger" onclick="deleteItem('personnel', '{{ coach.id }}')"><i class="fas fa-trash"></i></button>
                    </div>
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
        <div class="container position-relative">
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
                    <div class="position-absolute top-0 end-0 p-2 d-flex gap-2" onclick="event.stopPropagation()">
                        <button class="btn btn-sm btn-danger" onclick="deleteItem('personnel', '{{ mvp.id }}')"><i class="fas fa-trash"></i></button>
                    </div>
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
                <h2 class="section-title" style="white-space: nowrap; font-size: calc(1.3rem + .6vw);">Agenda Latihan & Turnamen</h2>
                <div class="calendar-container">
                    <div class="text-center mb-4">
                        <h4 class="text-uppercase fw-bold">Next Match Countdown</h4>
                        <div class="countdown-timer" id="countdown">0h 0j 0m 0d</div>
                        {% if admin %}
                        <p class="text-muted small">Auto-targets first agenda with future date. Fallback:</p>
                        <div class="d-flex justify-content-center align-items-center gap-2">
                            <input type="datetime-local" class="form-control w-25" id="countdown-picker" value="{{ data['settings']['next_match_time'] }}">
                            <button class="btn btn-success" onclick="saveText('site_settings', 'next_match_time', 'value', document.getElementById('countdown-picker'))">Mulai Count Down</button>
                        </div>
                        {% endif %}
                    </div>
                    
                    <div class="row">
                        {% for item in agenda_latihan %}
                        <div class="col-md-4">
                            <div class="agenda-card-barca cursor-pointer" onclick="openAgendaModal('{{ item.id }}', '{{ item.title }}', '{{ item.event_date }}', '{{ item.price }}', '{{ item.image_path if item.image_path else '' }}')">
                                <div class="agenda-img" style="position:relative;">
                                    <img src="{{ '/uploads/' + item.image_path if item.image_path else url_for('static', filename='logo-tahkil-fc.png') }}?t={{ timestamp }}" onerror="this.src='{{ url_for('static', filename='logo-tahkil-fc.png') }}'" style="width:100%; height:100%; object-fit:cover;">
                                </div>
                                <div class="agenda-details">
                                    <div class="agenda-date">{{ item.event_date | replace('T', ' ') if item.event_date else 'Date TBD' }}</div>
                                    <div class="agenda-title">{{ item.title }}</div>
                                    <small class="text-muted">{{ item.price }}</small>
                                </div>
                                {% if admin %}
                                <button class="position-absolute top-0 end-0 btn btn-sm btn-danger m-1" style="z-index:5;" onclick="deleteItem('agenda_content', '{{ item.id }}'); event.stopPropagation();"><i class="fas fa-trash"></i></button>
                                {% endif %}
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
    
    <!-- MAIN PARTNERS (Was TURNAMEN) -->
    <div class="container py-5" id="main-partners">
        <h2 class="section-title">Main Partners</h2>
        <div class="row">
             {% for item in turnamen %}
            <div class="col-md-4">
                <div class="agenda-card-barca cursor-pointer" onclick="openPartnerModal('{{ loop.index0 }}', '{{ item.id }}', '{{ item.title }}', '{{ item.details if item.details else '' }}', '{{ item.image_path if item.image_path else '' }}', '{{ item.price if item.price else '' }}')">
                    <div class="agenda-img" style="position:relative;">
                         <img src="{{ '/uploads/' + item.image_path if item.image_path else url_for('static', filename='logo-tahkil-fc.png') }}?t={{ timestamp }}" onerror="this.src='{{ url_for('static', filename='logo-tahkil-fc.png') }}'" style="width:100%; height:100%; object-fit:cover;">
                    </div>
                    <div class="agenda-details">
                        <div class="agenda-date">{{ item.price }}</div>
                        <div class="agenda-title">{{ item.title }}</div>
                    </div>
                    {% if admin %}
                    <button class="position-absolute top-0 end-0 btn btn-sm btn-danger m-1" style="z-index:5;" onclick="deleteItem('agenda_content', '{{ item.id }}'); event.stopPropagation();"><i class="fas fa-trash"></i></button>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
         {% if admin %}
        <button class="btn btn-outline-success mt-3" onclick="addCard('agenda', 2)">+ Add Partner Card</button>
        {% endif %}
    </div>

    <!-- MODALS -->

    <!-- PERSON MODAL -->
    <div id="person-modal" class="modal-overlay" onclick="closePersonModal()">
        <div class="modal-content-custom" onclick="event.stopPropagation()">
            <div class="row">
                <!-- Image Column (Right on desktop, Top on mobile) -->
                <div class="col-md-5 order-md-2 mb-3 mb-md-0 d-flex justify-content-center align-items-center position-relative">
                    <img id="pm-img" src="" style="width:100%; height:300px; object-fit:cover; border-radius:10px; box-shadow:0 5px 15px rgba(0,0,0,0.2);">
                </div>
                
                <!-- Info Column (Left on desktop, Bottom on mobile) -->
                <div class="col-md-7 order-md-1 text-start d-flex flex-column justify-content-center">
                     {% if admin %}
                    <form id="pm-upload-form" method="post" enctype="multipart/form-data" class="mb-3">
                        <label>Update Photo:</label>
                        <div class="input-group">
                            <input type="file" name="image" class="form-control" required>
                            <button class="btn btn-primary" type="submit">Upload</button>
                        </div>
                    </form>
                    <div class="mb-3">
                        <label>Name:</label>
                        <input type="text" id="pm-name-input" class="form-control fw-bold">
                    </div>
                    <div class="mb-3">
                        <label>Position:</label>
                        <input type="text" id="pm-pos-input" class="form-control text-muted">
                    </div>
                    <div class="row text-start mt-2">
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
                    <img src="{{ url_for('static', filename='logo-tahkil-fc.png') }}" style="width:60px; margin-bottom:15px;">
                    <h2 id="pm-name" class="fw-bold text-uppercase">Name</h2>
                    <h4 id="pm-role" class="text-muted mb-4">Position</h4>
                    
                    <div class="row g-3">
                        <div class="col-6">
                            <small class="text-muted d-block text-uppercase">Nationality</small>
                            <span id="pm-nat" class="fw-bold">Indonesia</span>
                        </div>
                        <div class="col-6">
                            <small class="text-muted d-block text-uppercase">Joined</small>
                            <span id="pm-join" class="fw-bold">2024</span>
                        </div>
                        <div class="col-6">
                            <small class="text-muted d-block text-uppercase">Matches</small>
                            <span id="pm-match" class="fw-bold">10</span>
                        </div>
                        <div class="col-6">
                            <small class="text-muted d-block text-uppercase">Goals</small>
                            <span id="pm-goal" class="fw-bold">5</span>
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>
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

    <!-- PARTNER MODAL -->
    <div id="partner-modal" class="modal-overlay" onclick="document.getElementById('partner-modal').style.display='none'">
        <div class="modal-content-custom" onclick="event.stopPropagation()" style="max-width:600px;">
            <div style="position:relative; margin-bottom:15px;" id="partner-img-wrapper">
                <img id="partner-modal-img" src="" style="width:100%; height:auto; max-height:70vh; object-fit:contain; border-radius:10px;">
                {% if admin %}
                <form id="partner-upload-form" method="post" enctype="multipart/form-data" class="mt-2">
                    <div class="input-group">
                        <input type="file" name="image" class="form-control" required>
                        <button class="btn btn-primary" type="submit">Upload</button>
                    </div>
                </form>
                {% endif %}
            </div>
            
            <div id="partner-modal-body">
                <!-- Dynamic Content Here -->
            </div>
        </div>
    </div>

    <!-- AGENDA MODAL -->
    <div id="agenda-modal" class="modal-overlay" onclick="document.getElementById('agenda-modal').style.display='none'">
        <div class="modal-content-custom" onclick="event.stopPropagation()" style="max-width:800px; padding:20px;">
            <div id="agenda-img-container" style="position:relative; width:100%; margin-bottom:20px;">
                <img id="agenda-modal-img" src="" style="width:100%; height:auto; max-height:60vh; object-fit:contain; border-radius:10px; box-shadow:0 5px 15px rgba(0,0,0,0.2);">
                <a href="https://maps.app.goo.gl/pKfSE3Ewm1RPCDiy9" target="_blank" class="agenda-modal-map-overlay" id="agenda-map-link">
                    klik ini untuk ke lokasi latihan <i class="fas fa-arrow-right"></i> <i class="fas fa-map-marker-alt fa-lg text-danger"></i>
                </a>
                {% if admin %}
                <form id="agenda-upload-form" method="post" enctype="multipart/form-data" class="mt-2">
                    <div class="input-group">
                        <input type="file" name="image" class="form-control" required>
                        <button class="btn btn-primary" type="submit">Upload New Image</button>
                    </div>
                </form>
                {% endif %}
            </div>
            
            <div class="time-box-wrapper" id="agenda-time-wrapper">
                <!-- Injected via JS -->
            </div>
        </div>
    </div>

    <!-- NEWS DETAIL MODAL -->
    <div id="news-modal" class="modal-overlay" onclick="document.getElementById('news-modal').style.display='none'">
        <div class="modal-content-custom" onclick="event.stopPropagation()" style="text-align:left; max-width:900px;">
            <div id="news-modal-date" class="text-uppercase text-muted fw-bold mb-2" style="font-size:0.8rem;"></div>
            
            <div style="position:relative;">
                <img id="news-modal-img" src="" style="width:100%; height:300px; object-fit:cover; border-radius:8px; margin-bottom:15px;">
            </div>

            {% if admin %}
            <form id="news-upload-form" method="post" enctype="multipart/form-data" class="mb-3">
                <label>Update Headline Image:</label>
                <div class="input-group">
                    <input type="file" name="image" class="form-control" required>
                    <button class="btn btn-primary" type="submit">Upload</button>
                </div>
            </form>
            <div class="mb-2">
                <label>Title:</label>
                <input type="text" id="news-modal-title-input" class="form-control fw-bold">
            </div>
            <div class="mb-2">
                <label>Subtitle (Ringkasan):</label>
                <textarea id="news-modal-subtitle-input" class="form-control" rows="2"></textarea>
            </div>
            <div class="mb-2">
                <label>Full Content:</label>
                <textarea id="news-modal-details-input" class="form-control" rows="5"></textarea>
            </div>
            <div class="text-end mt-3">
                <button class="btn btn-danger me-2" onclick="document.getElementById('news-modal').style.display='none'">Cancel</button>
                <button class="btn btn-success" onclick="saveNewsModal()">Save</button>
            </div>
            {% else %}
            <h3 id="news-modal-title" class="fw-bold mt-2 text-uppercase" style="color:var(--green)"></h3>
            <p id="news-modal-subtitle" class="lead text-muted"></p>
            <hr>
            <div id="news-modal-details" class="text-muted small" style="white-space: pre-wrap;"></div>
            <div class="text-center mt-3">
                <button class="btn btn-secondary" onclick="document.getElementById('news-modal').style.display='none'">Close</button>
            </div>
            {% endif %}
        </div>
    </div>
    
    <footer class="bg-black text-white py-5 text-center mt-5">
        <div class="container">
            <h3 class="fw-bold mb-3">TAHFIZH <span class="text-warning">KILAT FC</span></h3>
            <p contenteditable="{{ 'true' if admin else 'false' }}" onblur="saveText('site_settings', 'footer_text', 'value', this)">
                {{ data['settings'].get('footer_text', '© 2026 TAHKIL FC. All rights reserved.') }}
            </p>
            <div class="d-lg-none d-flex justify-content-center gap-4 mt-3">
                <a href="https://wa.me/6281528455350" class="social-icon-link" target="_blank"><i class="fab fa-whatsapp"></i></a>
                <a href="https://maps.app.goo.gl/4deg1ha8WaxWKdPC9" class="social-icon-link" target="_blank"><i class="fas fa-map-marker-alt"></i></a>
                <a href="https://www.instagram.com/rivkycahyahakikiori/" class="social-icon-link" target="_blank"><i class="fab fa-instagram"></i></a>
            </div>
        </div>
    </footer>

    <!-- STICKY BOTTOM NAV -->
    <div class="bottom-nav">
        <a href="javascript:void(0)" onclick="openAcademyModal('register')" class="bottom-nav-item">
            <i class="fas fa-user-plus"></i>
            <span>DAFTAR</span>
        </a>
        <a href="javascript:void(0)" onclick="openAcademyModal('finance')" class="bottom-nav-item">
            <i class="fas fa-wallet"></i>
            <span>KEUANGAN</span>
        </a>
        <a href="javascript:void(0)" onclick="openAcademyModal('report')" class="bottom-nav-item">
            <i class="fas fa-chart-line"></i>
            <span>RAPOR</span>
        </a>
    </div>

    <!-- ACADEMY MODALS -->
    
    <!-- REGISTER -->
    <div id="register-modal" class="modal-overlay" onclick="closeAcademyModals()">
        <div class="modal-content-custom" onclick="event.stopPropagation()">
            <div class="d-flex align-items-center justify-content-center gap-3 mb-2">
                <h3 class="section-title m-0">PENDAFTARAN SISWA BARU</h3>
            </div>
            
            <!-- User View -->
            <div id="reg-user-view">
                <p class="text-muted">Isi formulir untuk bergabung dengan Akademi TAHKIL FC</p>
                <button onclick="toggleRegAdmin()" class="mode-toggle-btn">Admin Mode</button>
                <form id="reg-form" onsubmit="event.preventDefault(); submitRegistration();" class="text-start">
                    <div class="mb-2">
                        <label>Nama Lengkap:</label>
                        <input type="text" name="name" class="form-control" required>
                    </div>
                    <div class="row">
                        <div class="col-6 mb-2">
                            <label>Tanggal Lahir:</label>
                            <input type="date" name="dob" class="form-control" required>
                        </div>
                        <div class="col-6 mb-2">
                            <label>Posisi:</label>
                            <select name="position" class="form-control">
                                <option value="GK">GK - Kiper</option>
                                <option value="CB">CB - Bek Tengah</option>
                                <option value="RB">RB - Bek Kanan</option>
                                <option value="LB">LB - Bek Kiri</option>
                                <option value="DMF">DMF - Gelandang Bertahan</option>
                                <option value="CMF">CMF - Gelandang Tengah</option>
                                <option value="AMF">AMF - Gelandang Serang</option>
                                <option value="RWF">RWF - Sayap Kanan</option>
                                <option value="LWF">LWF - Sayap Kiri</option>
                                <option value="SS">SS - Second Striker</option>
                                <option value="CF">CF - Center Forward</option>
                            </select>
                        </div>
                    </div>
                    <div class="mb-2">
                        <label>Nama Wali:</label>
                        <input type="text" name="guardian" class="form-control" required>
                    </div>
                    <div class="mb-2">
                        <label>No WA Wali:</label>
                        <input type="text" name="guardian_wa" class="form-control" placeholder="08..." required>
                    </div>
                    <div class="row">
                        <div class="col-6 mb-2">
                            <label>Username (untuk Login):</label>
                            <input type="text" name="username" class="form-control" required>
                        </div>
                        <div class="col-6 mb-2">
                            <label>Password:</label>
                            <input type="password" name="password" class="form-control" required>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label>Foto Diri:</label>
                        <input type="file" name="photo" class="form-control" required>
                    </div>
                    <div class="alert alert-warning small">Status Pending: Saat "Daftar" ditekan, data masuk ke antrean verifikasi admin.</div>
                    <button type="submit" class="btn btn-success w-100 fw-bold py-2">DAFTAR (Kirim ke Admin)</button>
                </form>
            </div>

            <!-- Admin View -->
            <div id="reg-admin-view" style="display:none;" class="text-start">
                <h5 class="fw-bold text-danger mb-3 text-center">Verifikasi Calon Siswa</h5>
                <button onclick="toggleRegAdmin()" class="mode-toggle-btn">Admin Mode</button>
                <div id="candidates-list" style="max-height:400px; overflow-y:auto;">
                    <div class="alert alert-info">Memuat data...</div>
                </div>
            </div>
        </div>
    </div>

    <!-- FINANCE -->
    <div id="finance-modal" class="modal-overlay" onclick="closeAcademyModals()">
        <div class="modal-content-custom" onclick="event.stopPropagation()">
            <div class="d-flex align-items-center justify-content-center gap-3 mb-2">
                <h3 class="section-title m-0">MANAJEMEN KEUANGAN & SPP</h3>
            </div>
            
            <!-- User Login View -->
            <div id="finance-login-view">
                <p>Silakan login siswa untuk cek tagihan.</p>
                <button onclick="toggleFinAdmin()" class="mode-toggle-btn">Admin Mode</button>
                <input type="text" id="login-user" class="form-control mb-2" placeholder="Username">
                <input type="password" id="login-pass" class="form-control mb-3" placeholder="Password">
                <button onclick="loginAcademy('finance')" class="btn btn-primary w-100">LOGIN SISWA</button>
            </div>

            <!-- User Dashboard View -->
            <div id="finance-dashboard-view" style="display:none;">
                <button onclick="logoutAcademy()" class="btn-thin-red">Logout</button>
                <h5 id="fin-student-name" class="fw-bold text-center mb-3"></h5>
                <div id="finance-bills-list" class="text-start" style="max-height: 400px; overflow-y: auto;">
                    <div class="alert alert-info">Memuat data tagihan...</div>
                </div>
            </div>

            <!-- Admin View -->
            <div id="finance-admin-view" style="display:none;" class="text-start">
                <h5 class="fw-bold text-success mb-3 text-center">Verifikasi Pembayaran</h5>
                <button onclick="toggleFinAdmin()" class="mode-toggle-btn">Admin Mode</button>
                <div id="finance-admin-list" style="max-height:400px; overflow-y:auto;">
                    <div class="alert alert-info">Memuat data...</div>
                </div>
            </div>
        </div>
    </div>

    <!-- REPORT -->
    <div id="report-modal" class="modal-overlay" onclick="closeAcademyModals()">
        <div class="modal-content-custom" onclick="event.stopPropagation()">
            <div class="d-flex align-items-center justify-content-center gap-3 mb-2">
                <h3 class="section-title m-0">RAPOR & ABSENSI DIGITAL</h3>
            </div>
             
            <!-- Student Login View -->
            <div id="report-login-view">
                <p>Silakan login untuk melihat rapor perkembangan.</p>
                <button onclick="toggleCoachMode()" class="mode-toggle-btn">Coach Mode</button>
                <input type="text" id="report-user" class="form-control mb-2" placeholder="Username">
                <input type="password" id="report-pass" class="form-control mb-3" placeholder="Password">
                <button onclick="loginAcademy('report')" class="btn btn-primary w-100">LOGIN</button>
            </div>

            <!-- Student Dashboard View -->
            <div id="report-dashboard-view" style="display:none;">
                <button onclick="logoutAcademy()" class="btn-thin-red">Logout</button>
                <h5 id="rep-student-name" class="fw-bold text-center text-success mb-3"></h5>
                
                <div class="hard-card-bg">
                    <div class="row mb-3">
                        <div class="col-6">
                            <div class="text-center">
                                <small class="text-white-50">Kehadiran</small>
                                <h2 class="fw-bold text-warning" id="att-percentage">--%</h2>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="text-center">
                                <small class="text-white-50">Skor Rata-rata</small>
                                <h2 class="fw-bold text-warning" id="avg-score">--</h2>
                            </div>
                        </div>
                    </div>
                    <div class="text-start">
                        <h6 class="fw-bold text-white mb-2">Grafik Perkembangan</h6>
                        <div id="score-bars" class="d-flex flex-column gap-2">
                            <!-- Bars injected via JS -->
                        </div>
                    </div>
                </div>
            </div>

            <!-- Coach Login View -->
            <div id="coach-login-view" style="display:none;">
                <h5 class="fw-bold text-primary mb-3">Coach Login</h5>
                <button onclick="toggleCoachMode()" class="mode-toggle-btn">Coach Mode</button>
                <input type="text" id="coach-user" class="form-control mb-2" placeholder="Coach ID">
                <input type="password" id="coach-pass" class="form-control mb-3" placeholder="Password">
                <button onclick="loginCoach()" class="btn btn-primary w-100">LOGIN COACH</button>
            </div>

            <!-- Coach Dashboard View -->
            <div id="coach-dashboard-view" style="display:none;" class="text-start">
                <button onclick="logoutCoach()" class="btn-thin-red">Logout</button>
                <h5 class="fw-bold text-primary text-center mb-3">Coach Dashboard</h5>
                
                <div class="coach-notebook-bg font-sketch">
                    <ul class="nav nav-tabs mb-3 border-bottom border-dark">
                        <li class="nav-item"><a class="nav-link active fw-bold text-dark" data-bs-toggle="tab" href="#tab-absensi">Absensi</a></li>
                        <li class="nav-item"><a class="nav-link fw-bold text-dark" data-bs-toggle="tab" href="#tab-evaluasi">Evaluasi</a></li>
                    </ul>

                    <div class="tab-content">
                    <div class="tab-pane fade show active" id="tab-absensi">
                        <div class="mb-2">
                            <label>Tanggal Latihan:</label>
                            <input type="date" id="att-date" class="form-control">
                        </div>
                        <div id="att-student-list" style="max-height:300px; overflow-y:auto;" class="mb-2"></div>
                        <button onclick="saveAttendance()" class="btn btn-success w-100">SIMPAN ABSENSI</button>
                    </div>
                    <div class="tab-pane fade" id="tab-evaluasi">
                        <div class="mb-2">
                            <label>Bulan Evaluasi:</label>
                            <input type="month" id="eval-month" class="form-control">
                        </div>
                        <div class="mb-2">
                            <label>Pilih Siswa:</label>
                            <select id="eval-student-select" class="form-control"></select>
                        </div>
                        <div class="row">
                            <div class="col-6 mb-2"><label>Passing:</label><input type="number" class="form-control eval-score" data-cat="passing"></div>
                            <div class="col-6 mb-2"><label>Shooting:</label><input type="number" class="form-control eval-score" data-cat="shooting"></div>
                            <div class="col-6 mb-2"><label>Stamina:</label><input type="number" class="form-control eval-score" data-cat="stamina"></div>
                            <div class="col-6 mb-2"><label>Attitude:</label><input type="number" class="form-control eval-score" data-cat="attitude"></div>
                            <div class="col-6 mb-2"><label>Teamwork:</label><input type="number" class="form-control eval-score" data-cat="teamwork"></div>
                            <div class="col-6 mb-2"><label>Discipline:</label><input type="number" class="form-control eval-score" data-cat="discipline"></div>
                        </div>
                        <button onclick="saveEvaluation()" class="btn btn-primary w-100 mt-2">SIMPAN NILAI</button>
                    </div>
                </div>
                </div>
            </div>
        </div>
    </div>

    <!-- DATA INJECTION FOR JS -->
    <script>
        // ACADEMY JS
        let currentUser = null;

        function openAcademyModal(type) {
            closeAcademyModals();
            document.getElementById(type + '-modal').style.display = 'flex';
            if(type === 'finance' || type === 'report') {
                if(currentUser) {
                    showDashboard(type);
                }
            }
        }

        function closeAcademyModals() {
            document.getElementById('register-modal').style.display = 'none';
            document.getElementById('finance-modal').style.display = 'none';
            document.getElementById('report-modal').style.display = 'none';
        }

        function submitRegistration() {
            const form = document.getElementById('reg-form');
            const formData = new FormData(form);
            
            // Show Loader
            const loader = document.getElementById('loader-overlay');
            const ball = document.getElementById('loader-ball');
            const success = document.getElementById('loader-success');
            const text = document.getElementById('loader-text');
            
            loader.style.display = 'flex';
            ball.style.display = 'block';
            success.style.display = 'none';
            text.innerText = "Mengupload Data Siswa...";
            
            fetch('/api/academy/register', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    // Animation Transformation
                    ball.style.display = 'none';
                    success.style.display = 'flex'; 
                    text.innerText = "Upload Berhasil!";
                    
                    setTimeout(() => {
                        loader.style.display = 'none';
                        alert("Pendaftaran Berhasil! Data Anda sedang diverifikasi admin.");
                        closeAcademyModals();
                        form.reset();
                    }, 2000);
                } else {
                    loader.style.display = 'none';
                    alert("Gagal: " + data.error);
                }
            })
            .catch(err => {
                loader.style.display = 'none';
                alert("Error: " + err);
            });
        }

        function toggleRegAdmin() {
            if(!isAdmin) {
                alert("Akses Ditolak. Silakan login sebagai Admin Website terlebih dahulu.");
                return;
            }
            const userView = document.getElementById('reg-user-view');
            const adminView = document.getElementById('reg-admin-view');
            if(adminView.style.display === 'none') {
                userView.style.display = 'none';
                adminView.style.display = 'block';
                loadCandidates();
            } else {
                userView.style.display = 'block';
                adminView.style.display = 'none';
            }
        }

        function loadCandidates() {
            fetch('/api/academy/admin/candidates')
            .then(res => res.json())
            .then(data => {
                const list = document.getElementById('candidates-list');
                list.innerHTML = '';
                if(data.candidates.length === 0) {
                    list.innerHTML = '<div class="alert alert-info">Tidak ada calon siswa pending.</div>';
                    return;
                }
                data.candidates.forEach(c => {
                   list.innerHTML += `
                        <div class="card mb-2 p-2 shadow-sm">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h6 class="fw-bold m-0">${c.name} (${c.position})</h6>
                                    <small class="text-muted">Lahir: ${c.dob} | Wali: ${c.guardian}</small><br>
                                    <small class="text-primary">User: ${c.username}</small>
                                </div>
                                <div class="d-flex flex-column gap-2">
                                    <button onclick="approveCandidate('${c.id}')" class="btn btn-sm btn-success w-100"><i class="fas fa-check"></i> Terima</button>
                                    <button onclick="rejectCandidate('${c.id}')" class="btn btn-sm btn-danger w-100"><i class="fas fa-times"></i> Tolak</button>
                                </div>
                            </div>
                        </div>
                   `; 
                });
            });
        }

        function approveCandidate(id) {
            if(!confirm("Approve siswa ini? Data akan masuk ke daftar resmi.")) return;
            fetch('/api/academy/approve', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ id: id })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    alert("Siswa berhasil di-approve! Otomatis masuk daftar resmi.");
                    loadCandidates();
                } else {
                    alert("Error: " + data.error);
                }
            });
        }

        function rejectCandidate(id) {
            if(!confirm("Tolak calon siswa ini? Data akan dihapus permanen.")) return;
            fetch('/api/academy/reject', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ id: id })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    alert("Siswa ditolak dan data dihapus.");
                    loadCandidates();
                } else {
                    alert("Error: " + data.error);
                }
            });
        }

        function toggleFinAdmin() {
            if(!isAdmin) {
                alert("Akses Ditolak. Silakan login sebagai Admin Website terlebih dahulu.");
                return;
            }
            // Hide other views
            document.getElementById('finance-login-view').style.display = 'none';
            document.getElementById('finance-dashboard-view').style.display = 'none';
            
            const adminView = document.getElementById('finance-admin-view');
            if(adminView.style.display === 'none') {
                adminView.style.display = 'block';
                loadFinAdminData();
            } else {
                adminView.style.display = 'none';
                document.getElementById('finance-login-view').style.display = 'block';
            }
        }
        
        function loadFinAdminData() {
            fetch('/api/academy/admin/finance')
            .then(res => res.json())
            .then(data => {
                const list = document.getElementById('finance-admin-list');
                list.innerHTML = '';
                if(data.bills.length === 0) {
                     list.innerHTML = '<div class="alert alert-info">Tidak ada tagihan perlu verifikasi.</div>';
                     return;
                }
                data.bills.forEach(b => {
                    let btn = '';
                    let proof = '';
                    if(b.status === 'pending') {
                         btn = `<button onclick="verifyPayment('${b.id}')" class="btn btn-sm btn-success mt-2">Validasi Lunas</button>`;
                         if(b.proof_path) proof = `<a href="/uploads/${b.proof_path}" target="_blank"><img src="/uploads/${b.proof_path}" style="height:50px; border:1px solid #ddd;"></a>`;
                         else proof = '<span class="text-danger">Belum upload bukti</span>';
                    } else if (b.status === 'paid') {
                        btn = `<span class="badge bg-success">LUNAS</span>`;
                        proof = `<span class="text-muted small">Verified</span>`;
                    }
                    
                    list.innerHTML += `
                        <div class="card mb-2 p-2 shadow-sm ${b.status === 'pending' ? 'border-warning' : ''}">
                             <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h6 class="fw-bold m-0">${b.student_name}</h6>
                                    <small class="text-muted">SPP ${b.month} - Rp ${b.amount.toLocaleString()}</small>
                                    <div class="mt-1">${proof}</div>
                                </div>
                                <div>${btn}</div>
                            </div>
                        </div>
                    `;
                });
            });
        }
        
        function verifyPayment(id) {
             if(!confirm("Validasi pembayaran ini sebagai Lunas?")) return;
             fetch('/api/academy/finance/verify', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ id: id })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    loadFinAdminData();
                }
            });
        }

        let currentCoach = null;
        
        function toggleCoachMode() {
            // Hide student views
            document.getElementById('report-login-view').style.display = 'none';
            document.getElementById('report-dashboard-view').style.display = 'none';
            
            if(currentCoach) {
                document.getElementById('coach-dashboard-view').style.display = 'block';
                document.getElementById('coach-login-view').style.display = 'none';
                loadCoachStudents();
            } else {
                document.getElementById('coach-dashboard-view').style.display = 'none';
                const loginView = document.getElementById('coach-login-view');
                if(loginView.style.display === 'none') {
                    loginView.style.display = 'block';
                } else {
                    loginView.style.display = 'none';
                    document.getElementById('report-login-view').style.display = 'block';
                }
            }
        }
        
        function loginCoach() {
            const u = document.getElementById('coach-user').value;
            const p = document.getElementById('coach-pass').value;
            fetch('/academy/login', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ username: u, password: p })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success && data.user.role === 'coach') {
                    currentCoach = data.user;
                    toggleCoachMode();
                } else {
                    alert("Login Gagal atau bukan akun Coach.");
                }
            });
        }
        
        function logoutCoach() {
            currentCoach = null;
            toggleCoachMode();
        }
        
        function loadCoachStudents() {
            fetch('/api/academy/coach/students')
            .then(res => res.json())
            .then(data => {
                const list = document.getElementById('att-student-list');
                const sel = document.getElementById('eval-student-select');
                list.innerHTML = '';
                sel.innerHTML = '<option value="">-- Pilih Siswa --</option>';
                
                if(data.students) {
                    data.students.forEach(s => {
                        // Attendance List
                        list.innerHTML += `
                            <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                                <span>${s.name}</span>
                                <div class="btn-group" role="group">
                                    <input type="radio" class="btn-check" name="att_${s.id}" id="att_${s.id}_p" value="present" checked>
                                    <label class="btn btn-outline-success btn-sm" for="att_${s.id}_p">Hadir</label>
                                    
                                    <input type="radio" class="btn-check" name="att_${s.id}" id="att_${s.id}_s" value="sick">
                                    <label class="btn btn-outline-warning btn-sm" for="att_${s.id}_s">Sakit</label>
                                    
                                    <input type="radio" class="btn-check" name="att_${s.id}" id="att_${s.id}_a" value="alpha">
                                    <label class="btn btn-outline-danger btn-sm" for="att_${s.id}_a">Alpha</label>
                                </div>
                            </div>
                        `;
                        // Eval Select
                        sel.innerHTML += `<option value="${s.id}">${s.name}</option>`;
                    });
                }
            });
        }
        
        function saveAttendance() {
            const date = document.getElementById('att-date').value;
            if(!date) { alert("Pilih tanggal latihan!"); return; }
            
            const list = [];
            document.querySelectorAll('[name^="att_"]:checked').forEach(radio => {
                const sid = radio.name.replace('att_', '');
                list.push({ student_id: sid, status: radio.value });
            });
            
            fetch('/api/academy/coach/attendance', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ date: date, list: list })
            })
            .then(res => res.json())
            .then(d => { if(d.success) alert("Absensi tersimpan!"); });
        }
        
        function saveEvaluation() {
            const month = document.getElementById('eval-month').value;
            const sid = document.getElementById('eval-student-select').value;
            if(!month || !sid) { alert("Pilih bulan dan siswa!"); return; }
            
            const scores = {};
            document.querySelectorAll('.eval-score').forEach(inp => {
                scores[inp.dataset.cat] = inp.value;
            });
            
            fetch('/api/academy/coach/evaluation', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ month: month, student_id: sid, scores: scores })
            })
            .then(res => res.json())
            .then(d => { if(d.success) alert("Evaluasi tersimpan!"); });
        }

        function loginAcademy(context) {
            const u = context === 'finance' ? document.getElementById('login-user').value : document.getElementById('report-user').value;
            const p = context === 'finance' ? document.getElementById('login-pass').value : document.getElementById('report-pass').value;
            
            fetch('/academy/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ username: u, password: p })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    currentUser = data.user;
                    showDashboard(context);
                } else {
                    alert("Login Gagal: " + data.error);
                }
            });
        }
        
        function logoutAcademy() {
            currentUser = null;
            document.getElementById('finance-login-view').style.display = 'block';
            document.getElementById('finance-dashboard-view').style.display = 'none';
            document.getElementById('report-login-view').style.display = 'block';
            document.getElementById('report-dashboard-view').style.display = 'none';
        }

        function showDashboard(type) {
            if(type === 'finance') {
                document.getElementById('finance-login-view').style.display = 'none';
                document.getElementById('finance-dashboard-view').style.display = 'block';
                document.getElementById('fin-student-name').innerText = currentUser.name;
                loadBills();
            } else if (type === 'report') {
                document.getElementById('report-login-view').style.display = 'none';
                document.getElementById('report-dashboard-view').style.display = 'block';
                document.getElementById('rep-student-name').innerText = currentUser.name;
                loadReport();
            }
        }

        function loadBills() {
            fetch('/api/academy/data?type=bills')
            .then(res => res.json())
            .then(data => {
                const list = document.getElementById('finance-bills-list');
                list.innerHTML = '';
                
                if(data.bills.length > 0) {
                     list.innerHTML += '<h6 class="fw-bold text-muted mb-3"><i class="fas fa-file-invoice-dollar"></i> KARTU TAGIHAN SPP</h6>';
                }

                if(data.bills.length === 0) {
                    list.innerHTML = '<div class="alert alert-success">Tidak ada tagihan aktif.</div>';
                    return;
                }
                
                data.bills.forEach(bill => {
                    const statusClass = bill.status === 'paid' ? 'status-paid' : (bill.status === 'pending' ? 'status-pending' : 'status-unpaid');
                    const statusText = bill.status === 'paid' ? 'LUNAS' : (bill.status === 'pending' ? 'VERIFIKASI' : 'BELUM BAYAR');
                    
                    let actionArea = '';
                    
                    if(bill.status === 'unpaid') {
                        actionArea = `
                            <div class="mt-3 border-top pt-2">
                                <small class="text-danger d-block mb-2"><i class="fas fa-exclamation-circle"></i> Silakan transfer dan upload bukti.</small>
                                <button class="btn btn-primary w-100" onclick="triggerUpload('${bill.id}')">
                                    <i class="fas fa-upload"></i> Upload Bukti Transfer
                                </button>
                                <form id="upload-form-${bill.id}" style="display:none">
                                    <input type="file" id="file-${bill.id}" accept="image/*" onchange="uploadProof('${bill.id}')">
                                </form>
                            </div>
                        `;
                    } else if (bill.status === 'paid') {
                         actionArea = `
                            <div class="mt-3 border-top pt-2">
                                <a href="/print-receipt/${bill.id}" target="_blank" class="btn btn-outline-success w-100">
                                    <i class="fas fa-print"></i> Cetak Kwitansi
                                </a>
                            </div>
                        `;
                    } else if (bill.status === 'pending') {
                         actionArea = `
                            <div class="mt-3 border-top pt-2 text-center text-muted">
                                <small><i class="fas fa-clock"></i> Menunggu Verifikasi Admin</small>
                            </div>
                         `;
                    }

                    const html = `
                        <div class="hard-card-bg mb-3">
                            <div class="d-flex justify-content-between align-items-center mb-2 border-bottom border-warning pb-2">
                                <span class="fw-bold text-warning">SPP ${bill.month}</span>
                                <span class="status-badge ${statusClass}">${statusText}</span>
                            </div>
                            <div class="text-center my-3">
                                <h2 class="fw-bold m-0" style="color:#fff;">Rp ${bill.amount.toLocaleString()}</h2>
                                <small class="text-white-50">ID: ${bill.id}</small>
                            </div>
                            ${actionArea}
                        </div>
                    `;
                    list.innerHTML += html;
                });
            });
        }
        
        function triggerUpload(id) {
            document.getElementById('file-'+id).click();
        }
        
        function uploadProof(billId) {
            const fileInput = document.getElementById('file-'+billId);
            const formData = new FormData();
            formData.append('proof', fileInput.files[0]);
            formData.append('bill_id', billId);
            
            fetch('/api/academy/finance/upload', { method: 'POST', body: formData })
            .then(res => res.json())
            .then(data => {
                if(data.success) { alert("Bukti terupload!"); loadBills(); }
            });
        }

        function loadReport() {
            fetch('/api/academy/data?type=report')
            .then(res => res.json())
            .then(data => {
                document.getElementById('att-percentage').innerText = data.attendance + "%";
                document.getElementById('avg-score').innerText = data.avg_score;
                
                const bars = document.getElementById('score-bars');
                bars.innerHTML = '';
                // Example categories
                const categories = { 'Passing': data.scores.passing, 'Shooting': data.scores.shooting, 'Stamina': data.scores.stamina, 'Attitude': data.scores.attitude };
                for (const [key, val] of Object.entries(categories)) {
                    bars.innerHTML += `
                        <div>
                            <div class="d-flex justify-content-between small"><span>${key}</span><span>${val || 0}</span></div>
                            <div class="progress" style="height: 8px;">
                                <div class="progress-bar bg-warning" style="width: ${val || 0}%"></div>
                            </div>
                        </div>
                    `;
                }
            });
        }

        const newsData = {{ data['news'] | tojson }};
        const isAdmin = {{ 'true' if admin else 'false' }};
    </script>

    <script>
        // --- MAIN PARTNERS (Was Turnamen) ---
        function openPartnerModal(index, id, title, details, imagePath, price) {
            index = parseInt(index);
            const modal = document.getElementById('partner-modal');
            const img = document.getElementById('partner-modal-img');
            const body = document.getElementById('partner-modal-body');
            const imgWrapper = document.getElementById('partner-img-wrapper');
            
            // Set Image
            const imgSrc = imagePath ? '/uploads/' + imagePath : '{{ url_for("static", filename="logo-tahkil-fc.png") }}';
            img.src = imgSrc + '?t=' + new Date().getTime();
            
            // Reset Layout
            body.innerHTML = '';
            
            // Remove any injected buttons in wrapper (from previous opens)
            const oldBtns = imgWrapper.querySelectorAll('.camera-btn, .agenda-modal-map-overlay');
            oldBtns.forEach(b => b.remove());

            if (isAdmin) {
                // --- ADMIN EDIT MODE ---
                document.getElementById('partner-upload-form').action = '/upload/agenda/' + id;
                
                // Build Form
                const formHtml = `
                    <div class="mb-2 mt-3">
                        <label>Nomor Partner:</label>
                        <input type="text" id="pm-price-input" class="form-control" value="${price || ''}">
                    </div>
                    <div class="mb-2">
                        <label>Judul Partner:</label>
                        <input type="text" id="pm-title-input" class="form-control" value="${title}">
                    </div>
                    <div class="mb-2">
                        <label>Deskripsi/Detail:</label>
                        <textarea id="pm-details-input" class="form-control" rows="3">${details || ''}</textarea>
                    </div>
                    
                    <div class="d-flex gap-2 justify-content-end mt-3">
                        <button class="btn btn-danger" onclick="document.getElementById('partner-modal').style.display='none'">Cancel</button>
                        <button class="btn btn-success" onclick="savePartnerFull('${id}')">Save</button>
                    </div>
                `;
                body.innerHTML = formHtml;
                
            } else {
                // --- VIEW MODE ---
                
                // 1. Social Links Overlay (Logic from previous, but cleaner)
                let linksHTML = '';
                if (index === 0) { 
                    linksHTML = `
                        <a href="instagram://user?username=tahfidzkilatsamarinda" class="agenda-modal-map-overlay" target="_blank" style="text-decoration:none;">
                            klik ini untuk ke sosmednya <i class="fas fa-arrow-right"></i> <i class="fab fa-instagram fa-lg text-danger"></i>
                        </a>`;
                } else if (index === 1) { 
                    linksHTML = `
                        <div class="agenda-modal-map-overlay" style="cursor:default;">
                            klik ini untuk ke sosmednya <i class="fas fa-arrow-right"></i> 
                            <a href="instagram://user?username=dapurarabiansmd"><i class="fab fa-instagram fa-lg text-danger ms-2"></i></a>
                            <a href="whatsapp://send?phone=6281528455350"><i class="fab fa-whatsapp fa-lg text-success ms-2"></i></a>
                        </div>
                    `;
                } else if (index === 2) { 
                    linksHTML = `
                        <a href="instagram://user?username=daycareqa" class="agenda-modal-map-overlay" target="_blank" style="text-decoration:none;">
                            klik ini untuk ke sosmednya <i class="fas fa-arrow-right"></i> <i class="fab fa-instagram fa-lg text-danger"></i>
                        </a>`;
                }
                
                // Inject overlay into wrapper
                if(linksHTML) {
                    const temp = document.createElement('div');
                    temp.innerHTML = linksHTML;
                    // append just the first child (the link or div)
                    imgWrapper.appendChild(temp.firstElementChild);
                }

                // 2. Details Text
                const detailsDiv = document.createElement('div');
                detailsDiv.className = 'mb-3 text-muted';
                detailsDiv.style.textAlign = 'justify';
                detailsDiv.innerText = details || "Keterangan...";
                body.appendChild(detailsDiv);
            }
            
            modal.style.display = 'flex';
        }
        
        function savePartnerFull(id) {
            const title = document.getElementById('pm-title-input').value;
            const details = document.getElementById('pm-details-input').value;
            const price = document.getElementById('pm-price-input').value;

            Promise.all([
                fetch('/api/update-text', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ table: 'agenda_content', id: id, field: 'title', value: title }) }),
                fetch('/api/update-text', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ table: 'agenda_content', id: id, field: 'details', value: details }) }),
                fetch('/api/update-text', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ table: 'agenda_content', id: id, field: 'price', value: price }) })
            ]).then(() => {
                location.reload();
            });
        }

        // --- AGENDA MODAL & COUNTDOWN ---
        let agendaInterval = null;
        let realTimeInterval = null;
        
        function openAgendaModal(id, title, eventDate, price, imagePath) {
            const modal = document.getElementById('agenda-modal');
            const img = document.getElementById('agenda-modal-img');
            const wrapper = document.getElementById('agenda-time-wrapper');
            const imgContainer = document.getElementById('agenda-img-container');
            
            // Set Image
            const imgSrc = imagePath ? '/uploads/' + imagePath : '{{ url_for("static", filename="logo-tahkil-fc.png") }}';
            img.src = imgSrc + '?t=' + new Date().getTime();
            
            // Reset Wrapper
            wrapper.innerHTML = ''; 
            
            // Remove old camera button if exists
            const oldCam = imgContainer.querySelector('.camera-btn');
            if(oldCam) oldCam.remove();

            if (isAdmin) {
                // --- ADMIN MODE ---
                document.getElementById('agenda-upload-form').action = '/upload/agenda/' + id;
                
                // Build Form Inputs
                const formHtml = `
                    <div class="mb-3">
                        <label>Judul Agenda:</label>
                        <input type="text" id="ag-title-input" class="form-control" value="${title}">
                    </div>
                    <div class="mb-3">
                        <label>Waktu Acara:</label>
                        <input type="datetime-local" id="ag-date-input" class="form-control" value="${eventDate || ''}">
                    </div>
                    <div class="mb-3">
                        <label>Keterangan/Tempat (Subtitle):</label>
                        <input type="text" id="ag-price-input" class="form-control" value="${price || ''}">
                    </div>
                    
                    <div class="d-flex gap-2 justify-content-end">
                        <button class="btn btn-danger" onclick="document.getElementById('agenda-modal').style.display='none'">Cancel</button>
                        <button class="btn btn-success" onclick="saveAgendaFull('${id}')">Save</button>
                    </div>
                `;
                wrapper.innerHTML = formHtml;
                
            } else {
                // --- VIEW MODE ---
                
                // 1. Real-time Clock (Top)
                const boxNow = document.createElement('div');
                boxNow.className = 'time-box';
                boxNow.innerHTML = `<span>HARI INI:</span> <span id="am-realtime">Loading...</span>`;
                wrapper.appendChild(boxNow);

                if(realTimeInterval) clearInterval(realTimeInterval);
                const updateRealTime = () => {
                    const now = new Date();
                    const datePart = now.toLocaleDateString('id-ID', {day: 'numeric', month: 'long', year: 'numeric'});
                    const timePart = now.toLocaleTimeString('id-ID', {hour: '2-digit', minute: '2-digit', second: '2-digit'}).replace(/\\./g, ':');
                    document.getElementById('am-realtime').innerText = `${datePart}, ${timePart} WITA`;
                };
                updateRealTime();
                realTimeInterval = setInterval(updateRealTime, 1000);

                // 2. Countdown (Middle)
                const boxCount = document.createElement('div');
                boxCount.className = 'time-box';
                boxCount.style.background = '#e8f5e9'; 
                boxCount.innerHTML = `<span>MENUJU ACARA:</span> <span id="am-countdown">--</span>`;
                wrapper.appendChild(boxCount);

                // 3. Event Date (Bottom)
                const boxEvent = document.createElement('div');
                boxEvent.className = 'time-box';
                boxEvent.style.background = '#fff3cd'; 
                
                if (eventDate) {
                    const eDate = new Date(eventDate);
                    const dateStr = eDate.toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric' });
                    const timeStr = eDate.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }).replace(/\\./g, ':');
                    
                    const fullStr = `${dateStr}, ${timeStr} WITA`;
                    const words = fullStr.split(' ');
                    let html = '';
                    words.forEach(w => {
                        html += `<span class="time-box-mini">${w}</span>`;
                    });
                    boxEvent.innerHTML = `<span>WAKTU ACARA:</span> <div>${html}</div>`;
                    wrapper.appendChild(boxEvent);

                    if(agendaInterval) clearInterval(agendaInterval);
                    const updateCountdown = () => {
                        const diff = eDate - new Date();
                        if (diff < 0) {
                            const cdEl = document.getElementById('am-countdown');
                            if(cdEl) cdEl.innerText = "EVENT STARTED";
                            return;
                        }
                        const d = Math.floor(diff / (1000 * 60 * 60 * 24));
                        const h = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                        const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                        const s = Math.floor((diff % (1000 * 60)) / 1000);
                        
                        const parts = [`${d}h`, `${h}j`, `${m}m`, `${s}d`];
                        let cdHtml = '';
                        parts.forEach(p => {
                             cdHtml += `<span class="time-box-mini" style="color:red; border-color:red;">${p}</span>`;
                        });
                        const cdEl = document.getElementById('am-countdown');
                        if(cdEl) cdEl.innerHTML = cdHtml;
                    };
                    updateCountdown();
                    agendaInterval = setInterval(updateCountdown, 1000);
                } else {
                    boxEvent.innerHTML = `<span>WAKTU ACARA:</span> <span>TBD</span>`;
                    wrapper.appendChild(boxEvent);
                    document.getElementById('am-countdown').innerText = "--";
                }
            }
            
            modal.style.display = 'flex';
        }

        function saveAgendaFull(id) {
            const title = document.getElementById('ag-title-input').value;
            const date = document.getElementById('ag-date-input').value;
            const price = document.getElementById('ag-price-input').value;

            // Save text
            Promise.all([
                fetch('/api/update-text', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ table: 'agenda_content', id: id, field: 'title', value: title }) }),
                fetch('/api/update-text', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ table: 'agenda_content', id: id, field: 'event_date', value: date }) }),
                fetch('/api/update-text', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ table: 'agenda_content', id: id, field: 'price', value: price }) })
            ]).then(() => {
                location.reload();
            });
        }

        function previewResize(id, size) {
            const img = document.getElementById('sp-img-' + id);
            if(img) {
                img.style.width = size + 'px';
                img.style.height = size + 'px';
            }
        }

        // --- UI UTILS ---
        function scrollHorizontally(btn, dir) {
            const container = btn.parentElement.querySelector('.horizontal-scroll-container');
            const scrollAmount = 300;
            container.scrollBy({ left: dir * scrollAmount, behavior: 'smooth' });
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

        function deleteItem(table, id) {
            if(!confirm("Are you sure you want to delete this item?")) return;
            fetch('/api/delete-item', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ table, id })
            }).then(() => location.reload());
        }

        // --- MODALS ---
        let currentPersonId = null;

        function openPersonModal(id, name, position, img, nat, joined, matches, goals) {
            currentPersonId = id;
            document.getElementById('pm-img').src = img || '{{ url_for("static", filename="logo-tahkil-fc.png") }}';
            document.getElementById('person-modal').style.display = 'flex';
            
            if (document.getElementById('pm-name-input')) { // Admin
                document.getElementById('pm-upload-form').action = '/upload/personnel/' + id;
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
                let suffix = (field === 'name' || field === 'position') ? '-input' : '-input'; 
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

        // News Modal
        let currentNewsId = null;
        function openNewsModal(newsId, type) {
            currentNewsId = newsId;
            const item = newsData[newsId];
            const imgPath = item.image_path ? '/uploads/' + item.image_path : '';
            
            document.getElementById('news-modal-img').src = imgPath || '{{ url_for("static", filename="logo-tahkil-fc.png") }}';
            
            // Date Formatting
            if (item.updated_at && item.updated_at !== 'None') {
                const date = new Date(item.updated_at.replace(" ", "T") + "Z"); // Assume UTC
                // Format: 12 Januari 2026, 10:43 WITA
                const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Makassar' };
                const dateStr = date.toLocaleString('id-ID', options);
                document.getElementById('news-modal-date').innerText = `BERITA DIUPDATE TERAKHIR : ${dateStr} WITA`;
            } else {
                document.getElementById('news-modal-date').innerText = "";
            }

            if (document.getElementById('news-modal-title-input')) { // Admin Mode
                document.getElementById('news-upload-form').action = '/upload/news/' + newsId;
                document.getElementById('news-modal-title-input').value = item.title;
                document.getElementById('news-modal-subtitle-input').value = item.subtitle;
                document.getElementById('news-modal-details-input').value = item.details || '';
            } else { // View Mode
                document.getElementById('news-modal-title').innerText = item.title;
                document.getElementById('news-modal-subtitle').innerText = item.subtitle;
                document.getElementById('news-modal-details').innerText = item.details || "Full news content...";
            }

            document.getElementById('news-modal').style.display = 'flex';
        }

        function saveNewsModal() {
            if(!currentNewsId) return;
            const title = document.getElementById('news-modal-title-input').value;
            const subtitle = document.getElementById('news-modal-subtitle-input').value;
            const details = document.getElementById('news-modal-details-input').value;
            
            // Chain promises for updates
            Promise.all([
                fetch('/api/update-text', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ table: 'news_content', id: currentNewsId, field: 'title', value: title }) }),
                fetch('/api/update-text', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ table: 'news_content', id: currentNewsId, field: 'subtitle', value: subtitle }) }),
                fetch('/api/update-text', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ table: 'news_content', id: currentNewsId, field: 'details', value: details }) })
            ]).then(() => location.reload());
        }

        // Countdown
        // Logic: Python passes target_countdown_time (ISO string)
        const targetStr = "{{ target_countdown_time }}";
        const targetDate = new Date(targetStr).getTime();
        
        setInterval(() => {
            const now = new Date().getTime();
            const distance = targetDate - now;
            if (distance < 0) {
                document.getElementById("countdown").innerHTML = "MATCH DAY / EVENT STARTED!";
                return;
            }
            const days = Math.floor(distance / (1000 * 60 * 60 * 24));
            const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);
            
            // Format: (angka)h (angka)j (angka)m (angka)d
            // h=Hari, j=Jam, m=Menit, d=Detik
            document.getElementById("countdown").innerHTML = days + "h " + hours + "j " + minutes + "m " + seconds + "d ";
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

# --- ACADEMY ROUTES ---

@app.route('/api/academy/register', methods=['POST'])
def academy_register():
    try:
        name = request.form.get('name')
        dob = request.form.get('dob')
        pos = request.form.get('position')
        guard = request.form.get('guardian')
        wa = request.form.get('guardian_wa')
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and Password required'})
            
        photo_path = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"cand_{int(time.time())}.jpg")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo_path = filename
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check username availability
        if c.execute("SELECT 1 FROM academy_users WHERE username=?", (username,)).fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Username already taken'})
            
        cid = f"cand_{int(time.time())}"
        # Simple Age Category Logic
        cat = 'U-12' 
        pwd_hash = generate_password_hash(password)
        
        c.execute("INSERT INTO candidates (id, name, dob, category, position, guardian, guardian_wa, photo_path, username, password_hash) VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (cid, name, dob, cat, pos, guard, wa, photo_path, username, pwd_hash))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/academy/admin/candidates', methods=['GET'])
def academy_admin_candidates():
    if not session.get('admin'): return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM candidates WHERE status='pending' ORDER BY created_at DESC")
    candidates = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify({'candidates': candidates})

@app.route('/academy/login', methods=['POST'])
def academy_login():
    data = request.json
    u = data.get('username')
    p = data.get('password')
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM academy_users WHERE username = ?", (u,))
    user = c.fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], p):
        # Set session
        session['academy_user'] = {'username': u, 'role': user['role'], 'related_id': user['related_id']}
        # Get name if student
        name = u
        if user['role'] == 'student':
            conn = get_db_connection()
            s = conn.execute("SELECT name FROM academy_students WHERE id=?", (user['related_id'],)).fetchone()
            conn.close()
            if s: name = s['name']
            
        return jsonify({'success': True, 'user': {'name': name, 'role': user['role']}})
    return jsonify({'success': False, 'error': 'Invalid credentials'})

@app.route('/api/academy/data', methods=['GET'])
def academy_data():
    if 'academy_user' not in session: return jsonify({'error': 'Unauthorized'}), 403
    type = request.args.get('type')
    user = session['academy_user']
    
    conn = get_db_connection()
    c = conn.cursor()
    data = {}
    
    if type == 'bills' and user['role'] == 'student':
        generate_monthly_bills()
        c.execute("SELECT * FROM finance_bills WHERE student_id = ? ORDER BY created_at DESC", (user['related_id'],))
        bills = [dict(row) for row in c.fetchall()]
        data['bills'] = bills
        
    elif type == 'report' and user['role'] == 'student':
        c.execute("SELECT * FROM academy_attendance WHERE student_id = ?", (user['related_id'],))
        att = c.fetchall()
        total = len(att)
        present = len([x for x in att if x['status'] == 'present'])
        pct = int((present / total * 100)) if total > 0 else 0
        
        c.execute("SELECT * FROM academy_evaluations WHERE student_id = ? ORDER BY created_at DESC LIMIT 1", (user['related_id'],))
        last_eval = c.fetchone()
        scores = {}
        if last_eval and last_eval['data']:
             try: scores = json.loads(last_eval['data'])
             except: pass
        
        avg = 0
        if scores:
            vals = [int(v) for v in scores.values() if str(v).isdigit()]
            if vals: avg = sum(vals) // len(vals)
            
        data['attendance'] = pct
        data['avg_score'] = avg
        data['scores'] = scores
        
    conn.close()
    return jsonify(data)

@app.route('/api/academy/finance/upload', methods=['POST'])
def academy_upload_proof():
    if 'academy_user' not in session: return jsonify({'error': 'Unauthorized'}), 403
    bill_id = request.form.get('bill_id')
    file = request.files.get('proof')
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"proof_{bill_id}.jpg")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        conn = get_db_connection()
        conn.execute("UPDATE finance_bills SET status='pending', proof_path=? WHERE id=?", (filename, bill_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/academy/approve', methods=['POST'])
def academy_approve():
    if not session.get('admin'): return jsonify({'error': 'Unauthorized'}), 403
    cand_id = request.json.get('id')
    
    conn = get_db_connection()
    c = conn.cursor()
    cand = c.execute("SELECT * FROM candidates WHERE id=?", (cand_id,)).fetchone()
    if cand:
        # Move to students
        sid = f"stu_{int(time.time())}"
        
        # Use existing credentials
        username = cand['username']
        pwd_hash = cand['password_hash']
        
        # Fallback if old data
        if not username:
             username = cand['name'].replace(' ', '').lower() + str(int(time.time())%1000)
             pwd_hash = generate_password_hash("123456")
        
        try:
            c.execute("INSERT INTO academy_users (username, password_hash, role, related_id) VALUES (?,?,?,?)", 
                      (username, pwd_hash, 'student', sid))
            
            c.execute("INSERT INTO academy_students (id, name, dob, category, position, guardian, guardian_wa, photo_path, user_id) VALUES (?,?,?,?,?,?,?,?,?)",
                      (sid, cand['name'], cand['dob'], cand['category'], cand['position'], cand['guardian'], cand['guardian_wa'], cand['photo_path'], username))
            
            c.execute("DELETE FROM candidates WHERE id=?", (cand_id,))
            conn.commit()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            conn.close()
            return jsonify({'success': False, 'error': str(e)})
    
    conn.close()
    return jsonify({'success': False, 'error': 'Candidate not found'})

@app.route('/api/academy/reject', methods=['POST'])
def academy_reject():
    if not session.get('admin'): return jsonify({'error': 'Unauthorized'}), 403
    cand_id = request.json.get('id')
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM candidates WHERE id=?", (cand_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/academy/student/delete', methods=['POST'])
def academy_student_delete():
    if not session.get('admin'): return jsonify({'error': 'Unauthorized'}), 403
    id = request.json.get('id')
    conn = get_db_connection()
    row = conn.execute("SELECT user_id FROM academy_students WHERE id=?", (id,)).fetchone()
    if row:
        conn.execute("DELETE FROM academy_users WHERE username=?", (row['user_id'],))
    conn.execute("DELETE FROM academy_students WHERE id=?", (id,))
    conn.execute("DELETE FROM finance_bills WHERE student_id=?", (id,))
    conn.execute("DELETE FROM academy_attendance WHERE student_id=?", (id,))
    conn.execute("DELETE FROM academy_evaluations WHERE student_id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/academy/admin/finance', methods=['GET'])
def academy_admin_finance():
    if not session.get('admin'): return jsonify({'error': 'Unauthorized'}), 403
    generate_monthly_bills()
    conn = get_db_connection()
    c = conn.cursor()
    # Get pending bills with student info
    c.execute('''SELECT f.*, s.name as student_name 
                 FROM finance_bills f 
                 JOIN academy_students s ON f.student_id = s.id 
                 WHERE f.status != 'unpaid' 
                 ORDER BY f.created_at DESC''')
    bills = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify({'bills': bills})

@app.route('/api/academy/finance/verify', methods=['POST'])
def academy_verify_payment():
    if not session.get('admin'): return jsonify({'error': 'Unauthorized'}), 403
    bill_id = request.json.get('id')
    
    conn = get_db_connection()
    conn.execute("UPDATE finance_bills SET status='paid' WHERE id=?", (bill_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/academy/coach/students', methods=['GET'])
def academy_coach_students():
    user = session.get('academy_user')
    if not user or user['role'] != 'coach': return jsonify({'error': 'Unauthorized'}), 403
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, name FROM academy_students ORDER BY name ASC")
    students = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify({'students': students})

@app.route('/api/academy/coach/attendance', methods=['POST'])
def academy_coach_attendance():
    user = session.get('academy_user')
    if not user or user['role'] != 'coach': return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    date = data.get('date')
    attendance_list = data.get('list') # [{student_id, status}, ...]
    
    conn = get_db_connection()
    c = conn.cursor()
    for item in attendance_list:
        aid = f"att_{date}_{item['student_id']}"
        c.execute("INSERT OR REPLACE INTO academy_attendance (id, date, student_id, status, coach_id) VALUES (?,?,?,?,?)",
                  (aid, date, item['student_id'], item['status'], user['related_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/academy/coach/evaluation', methods=['POST'])
def academy_coach_evaluation():
    user = session.get('academy_user')
    if not user or user['role'] != 'coach': return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    month = data.get('month')
    student_id = data.get('student_id')
    scores = json.dumps(data.get('scores')) # JSON string
    
    conn = get_db_connection()
    c = conn.cursor()
    eid = f"eval_{month}_{student_id}"
    c.execute("INSERT OR REPLACE INTO academy_evaluations (id, month, student_id, coach_id, data) VALUES (?,?,?,?,?)",
              (eid, month, student_id, user['related_id'], scores))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/print-receipt/<bill_id>')
def print_receipt(bill_id):
    conn = get_db_connection()
    bill = conn.execute("SELECT * FROM finance_bills WHERE id=?", (bill_id,)).fetchone()
    conn.close()
    if not bill or bill['status'] != 'paid': return "Receipt Not Available"
    
    return f"""
    <div style="text-align:center; font-family:monospace; padding:20px; border:1px solid #000; width:300px; margin:20px auto;">
        <h2>TAHKIL FC ACADEMY</h2>
        <p>OFFICIAL RECEIPT</p>
        <hr>
        <p align="left">ID: {bill['id']}</p>
        <p align="left">Month: {bill['month']}</p>
        <p align="left">Amount: Rp {bill['amount']:,}</p>
        <p align="left">Status: PAID</p>
        <hr>
        <p>Thank you for your payment.</p>
        <button onclick="window.print()">Print</button>
    </div>
    """

# --- NEW TEMPLATES ---

HTML_PLAYER_LIST = """
<!DOCTYPE html>
<html>
<head>
    <title>Daftar Resmi Pemain - TAHKIL FC</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    {{ styles|safe }}
    <style>
        .list-header { background: #111; color: #FFD700; padding: 40px 0; text-align: center; border-bottom: 5px solid #2ecc71; margin-bottom:30px; }
        .list-table thead { background: #111; color: white; }
        .list-table th { border: none; padding: 15px; }
        .list-table td { vertical-align: middle; padding: 15px; }
        .list-container { max-width: 1000px; margin: 0 auto; padding: 0 20px; }
    </style>
</head>
<body>
    {{ navbar|safe }}
    <div class="list-header">
        <h1 class="fw-bold">DAFTAR RESMI PEMAIN</h1>
        <p class="lead">DAFTAR RESMI PEMAIN TAHKIL FC yang telah dibuat dan disetujui oleh admin website TAHKIL FC</p>
    </div>
    <div class="list-container mb-5">
        <div class="card shadow border-0">
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-striped table-hover m-0 list-table">
                        <thead>
                            <tr>
                                <th>No</th>
                                <th>Foto</th>
                                <th>Nama Lengkap</th>
                                <th>Posisi</th>
                                <th>Kategori</th>
                                {% if admin %}<th>Aksi</th>{% endif %}
                            </tr>
                        </thead>
                        <tbody>
                            {% for s in students %}
                            <tr>
                                <td>{{ loop.index }}</td>
                                <td>
                                    <img src="{{ '/uploads/' + s.photo_path if s.photo_path else 'https://via.placeholder.com/50' }}" 
                                         style="width:50px; height:50px; object-fit:cover; border-radius:50%; border:2px solid #2ecc71;">
                                </td>
                                <td class="fw-bold">{{ s.name }}</td>
                                <td><span class="badge bg-dark text-warning">{{ s.position }}</span></td>
                                <td>{{ s.category }}</td>
                                {% if admin %}
                                <td>
                                    <button class="btn btn-danger btn-sm" onclick="deleteStudent('{{ s.id }}')"><i class="fas fa-trash"></i> Hapus</button>
                                </td>
                                {% endif %}
                            </tr>
                            {% else %}
                            <tr><td colspan="{% if admin %}6{% else %}5{% endif %}" class="text-center py-4">Belum ada data pemain resmi.</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function deleteStudent(id) {
            if(!confirm("Yakin ingin menghapus pemain ini dari daftar resmi? Data user & tagihan juga akan terhapus.")) return;
            fetch('/api/academy/student/delete', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ id: id })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    alert("Pemain berhasil dihapus.");
                    location.reload();
                } else {
                    alert("Gagal menghapus: " + data.error);
                }
            });
        }
    </script>
</body>
</html>
"""

HTML_BILL_LIST = """
<!DOCTYPE html>
<html>
<head>
    <title>Daftar Tagihan - TAHKIL FC</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    {{ styles|safe }}
    <style>
        .list-header { background: #111; color: #FFD700; padding: 40px 0; text-align: center; border-bottom: 5px solid #2ecc71; margin-bottom:30px; }
        .list-table thead { background: #111; color: white; }
        .list-table th { border: none; padding: 15px; }
        .list-table td { vertical-align: middle; padding: 15px; }
        .list-container { max-width: 1000px; margin: 0 auto; padding: 0 20px; }
    </style>
</head>
<body>
    {{ navbar|safe }}
    <div class="list-header">
        <h1 class="fw-bold">DAFTAR TAGIHAN PEMAIN</h1>
        <p class="lead">DAFTAR TAGIHAN PEMAIN TAHKIL FC yang telah diisi dan dibuat oleh admin website TAHKIL FC</p>
    </div>
    <div class="list-container mb-5">
        <div class="card shadow border-0">
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-striped table-hover m-0 list-table">
                        <thead>
                            <tr>
                                <th>No</th>
                                <th>Nama Pemain</th>
                                <th>Bulan Tagihan</th>
                                <th>Jumlah (Rp)</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for b in bills %}
                            <tr>
                                <td>{{ loop.index }}</td>
                                <td class="fw-bold">{{ b.student_name }}</td>
                                <td>{{ b.month }}</td>
                                <td>{{ "{:,}".format(b.amount) }}</td>
                                <td>
                                    {% if b.status == 'paid' %}
                                    <span class="badge bg-success">LUNAS</span>
                                    {% elif b.status == 'pending' %}
                                    <span class="badge bg-warning text-dark">VERIFIKASI</span>
                                    {% else %}
                                    <span class="badge bg-danger">BELUM BAYAR</span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% else %}
                            <tr><td colspan="5" class="text-center py-4">Belum ada data tagihan.</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

HTML_REPORT_LIST = """
<!DOCTYPE html>
<html>
<head>
    <title>Daftar Rapor - TAHKIL FC</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    {{ styles|safe }}
    <style>
        .list-header { background: #111; color: #FFD700; padding: 40px 0; text-align: center; border-bottom: 5px solid #2ecc71; margin-bottom:30px; }
        .list-table thead { background: #111; color: white; }
        .list-table th { border: none; padding: 15px; }
        .list-table td { vertical-align: middle; padding: 15px; }
        .list-container { max-width: 1000px; margin: 0 auto; padding: 0 20px; }
    </style>
</head>
<body>
    {{ navbar|safe }}
    <div class="list-header">
        <h1 class="fw-bold">DAFTAR RAPOR PEMAIN</h1>
        <p class="lead">DAFTAR RAPOR PEMAIN TAHKIL FC yang telah diisi oleh coach pelatih TAHKIL FC</p>
    </div>
    <div class="list-container mb-5">
        <div class="card shadow border-0">
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-striped table-hover m-0 list-table">
                        <thead>
                            <tr>
                                <th>No</th>
                                <th>Nama Pemain</th>
                                <th>Kehadiran Total</th>
                                <th>Skor Rata-Rata (Terakhir)</th>
                                <th>Keterangan</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for r in reports %}
                            <tr>
                                <td>{{ loop.index }}</td>
                                <td class="fw-bold">{{ r.name }}</td>
                                <td>
                                    <div class="progress" style="height: 20px;">
                                        <div class="progress-bar bg-success" role="progressbar" style="width: {{ r.attendance }}%">{{ r.attendance }}%</div>
                                    </div>
                                </td>
                                <td>
                                    <span class="fw-bold fs-5 {{ 'text-success' if r.score >= 80 else ('text-warning' if r.score >= 60 else 'text-danger') }}">
                                        {{ r.score }}
                                    </span>
                                </td>
                                <td>
                                    {% if r.score >= 80 %}Sangat Baik{% elif r.score >= 60 %}Cukup{% else %}Perlu Latihan{% endif %}
                                </td>
                            </tr>
                            {% else %}
                            <tr><td colspan="5" class="text-center py-4">Belum ada data rapor.</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# --- NEW ROUTES ---

@app.route('/daftar-resmi-pemain')
def list_players():
    data = get_all_data()
    conn = get_db_connection()
    students = conn.execute("SELECT * FROM academy_students ORDER BY name ASC").fetchall()
    conn.close()
    return render_page(HTML_PLAYER_LIST, data=data, students=students, admin=session.get('admin', False))

@app.route('/daftar-tagihan-pemain')
def list_bills():
    if not session.get('admin'): return redirect(url_for('index'))
    data = get_all_data()
    conn = get_db_connection()
    # Join to get student names
    bills = conn.execute("SELECT f.*, s.name as student_name FROM finance_bills f JOIN academy_students s ON f.student_id = s.id ORDER BY f.created_at DESC").fetchall()
    conn.close()
    return render_page(HTML_BILL_LIST, data=data, bills=bills, admin=session.get('admin', False))

@app.route('/daftar-rapor-pemain')
def list_reports():
    data = get_all_data()
    conn = get_db_connection()
    students = conn.execute("SELECT id, name FROM academy_students ORDER BY name ASC").fetchall()
    
    # Calculate stats for each student (simplified for list view)
    report_data = []
    for s in students:
        att = conn.execute("SELECT status FROM academy_attendance WHERE student_id=?", (s['id'],)).fetchall()
        total = len(att)
        present = len([x for x in att if x['status'] == 'present'])
        pct = int((present / total * 100)) if total > 0 else 0
        
        # Get latest eval
        eval = conn.execute("SELECT data FROM academy_evaluations WHERE student_id=? ORDER BY created_at DESC LIMIT 1", (s['id'],)).fetchone()
        avg = 0
        if eval and eval['data']:
            try:
                scores = json.loads(eval['data'])
                vals = [int(v) for v in scores.values() if str(v).isdigit()]
                if vals: avg = sum(vals) // len(vals)
            except: pass
        
        report_data.append({'name': s['name'], 'attendance': pct, 'score': avg})
        
    conn.close()
    return render_page(HTML_REPORT_LIST, data=data, reports=report_data, admin=session.get('admin', False))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
