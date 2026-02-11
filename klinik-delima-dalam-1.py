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
    
    # Clinic Queue
    c.execute('''CREATE TABLE IF NOT EXISTS queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT,
                    complaint TEXT,
                    status TEXT DEFAULT 'waiting',
                    number INTEGER,
                    diagnosis TEXT,
                    prescription TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    
    # Medicine Stock
    c.execute('''CREATE TABLE IF NOT EXISTS medicine_stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    stock INTEGER DEFAULT 0,
                    unit TEXT DEFAULT 'pcs'
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

# --- CLINIC ROUTES ---

@app.route('/')
def landing_page():
    # Check Clinic Status
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM site_settings WHERE key='clinic_open'")
    row = c.fetchone()
    is_open = row['value'] == '1' if row else False
    conn.close()
    
    # Render
    return render_template_string(HTML_LANDING, admin=session.get('admin', False), spa_script=JS_SPA_ROUTER)

@app.route('/antrean')
def antrean_page():
    navbar = render_template_string(HTML_INTERNAL_NAVBAR, title='ANTREAN')
    return render_template_string(HTML_QUEUE, internal_navbar=navbar, spa_script=JS_SPA_ROUTER)

@app.route('/rekam-medis')
def rekam_medis_page():
    navbar = render_template_string(HTML_INTERNAL_NAVBAR, title='REKAM MEDIS')
    return render_template_string(HTML_DOCTOR_REKAM, internal_navbar=navbar, spa_script=JS_SPA_ROUTER)

@app.route('/stok-obat')
def stok_obat_page():
    navbar = render_template_string(HTML_INTERNAL_NAVBAR, title='STOK OBAT')
    return render_template_string(HTML_DOCTOR_STOCK, internal_navbar=navbar, spa_script=JS_SPA_ROUTER)

# --- CLINIC API ---

@app.route('/api/clinic/status', methods=['GET', 'POST'])
def api_clinic_status():
    conn = get_db_connection()
    c = conn.cursor()
    
    if request.method == 'POST':
        if not session.get('admin'): return jsonify({'error': 'Unauthorized'}), 403
        c.execute("SELECT value FROM site_settings WHERE key='clinic_open'")
        row = c.fetchone()
        curr = row['value'] if row else '0'
        new_val = '0' if curr == '1' else '1'
        c.execute("INSERT OR REPLACE INTO site_settings (key, value) VALUES ('clinic_open', ?)", (new_val,))
        conn.commit()
        conn.close()
        return jsonify({'open': new_val == '1'})
    
    c.execute("SELECT value FROM site_settings WHERE key='clinic_open'")
    row = c.fetchone()
    is_open = row['value'] == '1' if row else False
    conn.close()
    return jsonify({'open': is_open})

@app.route('/api/queue/add', methods=['POST'])
def api_queue_add():
    data = request.json
    name = data.get('name')
    phone = data.get('phone')
    complaint = data.get('complaint')
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get daily number
    today = datetime.date.today().isoformat()
    c.execute("SELECT MAX(number) as max_num FROM queue WHERE created_at LIKE ?", (f"{today}%",))
    row = c.fetchone()
    next_num = (row['max_num'] or 0) + 1
    
    c.execute("INSERT INTO queue (name, phone, complaint, number, status) VALUES (?, ?, ?, ?, 'waiting')", 
              (name, phone, complaint, next_num))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'ticket': next_num})

@app.route('/api/queue/status')
def api_queue_status():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Current
    c.execute("SELECT * FROM queue WHERE status='examining' ORDER BY created_at DESC LIMIT 1")
    curr = c.fetchone()
    current_data = dict(curr) if curr else None
    
    # Waiting Count
    c.execute("SELECT COUNT(*) as cnt FROM queue WHERE status='waiting'")
    waiting_count = c.fetchone()['cnt']
    
    # Full data for Admin
    if request.args.get('full'):
        c.execute("SELECT * FROM queue WHERE status='waiting' ORDER BY created_at ASC")
        waiting_list = [dict(r) for r in c.fetchall()]
        
        today = datetime.date.today().isoformat()
        c.execute("SELECT * FROM queue WHERE status='done' AND created_at LIKE ? ORDER BY created_at DESC", (f"{today}%",))
        history_list = [dict(r) for r in c.fetchall()]
        
        conn.close()
        return jsonify({
            'current': current_data,
            'waiting_count': waiting_count,
            'waiting': waiting_list,
            'history': history_list
        })
        
    conn.close()
    return jsonify({
        'current_number': current_data['number'] if current_data else None,
        'current_name': current_data['name'] if current_data else None,
        'waiting_count': waiting_count
    })

@app.route('/api/queue/action', methods=['POST'])
def api_queue_action():
    # if not session.get('admin'): return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    action = data.get('action')
    id = data.get('id')
    
    conn = get_db_connection()
    c = conn.cursor()
    
    if action == 'call':
        # Finish any currently examining
        c.execute("UPDATE queue SET status='done' WHERE status='examining'") 
        # Update target
        c.execute("UPDATE queue SET status='examining' WHERE id=?", (id,))
        
    elif action == 'finish':
        diag = data.get('diagnosis')
        presc = data.get('prescription')
        c.execute("UPDATE queue SET status='done', diagnosis=?, prescription=? WHERE id=?", (diag, presc, id))
        
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/stock/list')
def api_stock_list():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM medicine_stock ORDER BY name ASC")
    items = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(items)

@app.route('/api/stock/update', methods=['POST'])
def api_stock_update():
    # if not session.get('admin'): return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    action = data.get('action')
    
    conn = get_db_connection()
    c = conn.cursor()
    
    if action == 'create':
        c.execute("INSERT INTO medicine_stock (name, stock, unit) VALUES (?, ?, ?)", 
                  (data.get('name'), data.get('stock'), data.get('unit')))
    elif action == 'update':
        id = data.get('id')
        change = int(data.get('change'))
        c.execute("UPDATE medicine_stock SET stock = stock + ? WHERE id=?", (change, id))
    elif action == 'delete':
        c.execute("DELETE FROM medicine_stock WHERE id=?", (data.get('id'),))
        
    conn.commit()
    conn.close()
    return jsonify({'success': True})

def render_page(content, **kwargs):
    content = content.replace('{{ styles|safe }}', STYLES_HTML)
    content = content.replace('{{ navbar|safe }}', NAVBAR_HTML)
    if 'timestamp' not in kwargs:
        kwargs['timestamp'] = int(time.time())
    return render_template_string(content, **kwargs)

@app.route('/profil-klinik')
def profil_klinik():
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
                       admin=session.get('admin', False),
                       spa_script=JS_SPA_ROUTER)

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
        
        if type == 'history':
            c.execute("INSERT OR REPLACE INTO site_settings (key, value) VALUES (?, ?)", ('history_image', filename))
        elif type == 'news':
            c.execute("UPDATE news_content SET image_path = ? WHERE id = ?", (filename, id))
        elif type == 'personnel':
            c.execute("UPDATE personnel SET image_path = ? WHERE id = ?", (filename, id))
        elif type == 'sponsor':
            c.execute("UPDATE sponsors SET image_path = ? WHERE id = ?", (filename, id))
        elif type == 'agenda':
            c.execute("UPDATE agenda_content SET image_path = ? WHERE id = ?", (filename, id))
            
        conn.commit()
        conn.close()
        
    return redirect(url_for('profil_klinik'))

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

HTML_INTERNAL_NAVBAR = """
<nav class="navbar fixed-top bg-white shadow-sm p-0" style="height: 60px; z-index: 1030;">
    <div class="container-fluid h-100 d-flex justify-content-between align-items-center position-relative">
        <a class="navbar-brand d-flex align-items-center" href="/">
            <img src="{{ url_for('static', filename='logo-tahkil-fc.png') }}" height="40" alt="Logo">
        </a>
        <div class="position-absolute top-50 start-50 translate-middle fw-bold fs-5 text-uppercase">
            {{ title }}
        </div>
        <button class="btn border-0" type="button" data-bs-toggle="offcanvas" data-bs-target="#internalMenu">
            <i class="fas fa-bars fa-lg"></i>
        </button>
        <div style="position: absolute; bottom: 0; left: 0; width: 100%; height: 3px; background: linear-gradient(90deg, #2ecc71 50%, #FFD700 50%);"></div>
    </div>
</nav>
<div class="offcanvas offcanvas-end" tabindex="-1" id="internalMenu" style="width: 250px;">
    <div class="offcanvas-header bg-light">
        <h5 class="offcanvas-title">Menu</h5>
        <button type="button" class="btn-close" data-bs-dismiss="offcanvas"></button>
    </div>
    <div class="offcanvas-body d-flex flex-column gap-3">
        <a href="/" class="btn btn-outline-dark text-start border-0"><i class="fas fa-home me-2"></i> Home</a>
        <a href="/rekam-medis" class="btn btn-outline-success text-start border-0"><i class="fas fa-notes-medical me-2"></i> Rekam Medis</a>
        <a href="/stok-obat" class="btn btn-outline-secondary text-start border-0"><i class="fas fa-capsules me-2"></i> Stok Obat</a>
        <a href="/antrean" class="btn btn-outline-primary text-start border-0"><i class="fas fa-users me-2"></i> Antrean</a>
    </div>
</div>
<div style="height: 70px;"></div>
"""

JS_SPA_ROUTER = """
<script>
    // Interval Management
    window.activeIntervals = [];
    const originalSetInterval = window.setInterval;
    window.setInterval = function(func, delay) {
        const id = originalSetInterval(func, delay);
        window.activeIntervals.push(id);
        return id;
    };
    window.clearIntervalAll = function() {
        window.activeIntervals.forEach(id => clearInterval(id));
        window.activeIntervals = [];
    };

    document.addEventListener('DOMContentLoaded', () => {
        const isLocked = sessionStorage.getItem('lockScreen') === 'true';
        if (isLocked) {
             if (!document.fullscreenElement) {
                 document.addEventListener('click', () => {
                     if(sessionStorage.getItem('lockScreen') === 'true' && !document.fullscreenElement) {
                         document.documentElement.requestFullscreen().catch(e=>{});
                     }
                 }, {once:true});
             }
        }
        document.body.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (link) {
                const href = link.getAttribute('href');
                if (href && href.startsWith('/') && !href.startsWith('//') && !href.includes('.') && href !== '#') {
                    e.preventDefault();
                    navigateTo(href);
                }
            }
        });
        window.addEventListener('popstate', () => {
            loadContent(location.pathname);
        });
    });
    async function navigateTo(url) {
        history.pushState(null, '', url);
        await loadContent(url);
    }
    async function loadContent(url) {
        window.clearIntervalAll();
        try {
            const res = await fetch(url);
            const text = await res.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(text, 'text/html');
            document.body.innerHTML = doc.body.innerHTML;
            document.title = doc.title;
            const scripts = document.body.querySelectorAll('script');
            scripts.forEach(oldScript => {
                const newScript = document.createElement('script');
                Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
                newScript.appendChild(document.createTextNode(oldScript.innerHTML));
                oldScript.parentNode.replaceChild(newScript, oldScript);
            });
        } catch (e) {
            window.location.href = url;
        }
    }
    window.toggleFullScreen = function() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().then(() => {
                sessionStorage.setItem('lockScreen', 'true');
            }).catch(e => {
                alert("Fullscreen blocked: " + e.message);
            });
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
                sessionStorage.setItem('lockScreen', 'false');
            }
        }
    };
</script>
"""

HTML_LANDING = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Klinik Tahfizh Kilat</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Segoe UI', sans-serif;
        }
        .glass-panel {
            background: rgba(255, 255, 255, 0.25);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            backdrop-filter: blur(4px);
            -webkit-backdrop-filter: blur(4px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.18);
            padding: 40px;
            text-align: center;
            max-width: 1000px;
            width: 90%;
        }
        .main-btn {
            background: rgba(255, 255, 255, 0.8);
            border: none;
            border-radius: 15px;
            padding: 20px;
            margin: 10px;
            width: 200px;
            height: 200px;
            display: inline-flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            transition: 0.3s;
            text-decoration: none;
            color: #333;
            font-weight: bold;
            font-size: 1.1rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .main-btn:hover {
            transform: translateY(-5px);
            background: #fff;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            color: #2ecc71;
        }
        .main-btn i {
            font-size: 4rem;
            margin-bottom: 15px;
            color: #2ecc71;
        }
        .status-badge {
            font-size: 1.5rem;
            font-weight: bold;
            padding: 10px 30px;
            border-radius: 50px;
            margin-bottom: 30px;
            display: inline-block;
        }
        .status-open { background: #2ecc71; color: white; }
        .status-closed { background: #e74c3c; color: white; }
        .wa-float {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #25D366;
            color: white;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            text-decoration: none;
            transition: 0.3s;
            z-index: 9999;
        }
        .wa-float:hover { transform: scale(1.1); color: white; }
        .lock-screen-btn {
            position: fixed;
            bottom: 30px;
            left: 30px;
            background: rgba(255, 255, 255, 0.9);
            border: none;
            border-radius: 15px;
            width: 70px;
            height: 70px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            z-index: 9999;
            color: #333;
            text-decoration: none;
            transition: 0.3s;
        }
        .lock-screen-btn i { font-size: 1.5rem; margin-bottom: 5px; color: #333; }
        .lock-screen-btn span { font-size: 0.65rem; font-weight: bold; line-height: 1; color: #333; }
        @media (min-width: 992px) { .lock-screen-btn { display: none; } }
    </style>
</head>
<body>
    <div class="glass-panel">
        <h1 class="mb-4 fw-bold">KLINIK TAHFIZH KILAT</h1>
        
        <div id="status-container">
            <!-- Loaded via JS -->
            <span class="status-badge status-open">LOADING...</span>
        </div>
        
        {% if admin %}
        <div class="mb-4">
            <button class="btn btn-warning" onclick="toggleClinicStatus()">
                <i class="fas fa-power-off"></i> SAKLAR BUKA/TUTUP
            </button>
        </div>
        {% endif %}
        
        <div class="d-flex flex-wrap justify-content-center">
            <a href="/antrean" class="main-btn">
                <i class="fas fa-users"></i>
                ANTREAN
            </a>
            
            <a href="/rekam-medis" class="main-btn">
                <i class="fas fa-notes-medical"></i>
                REKAM MEDIS
            </a>
            
            <a href="/stok-obat" class="main-btn">
                <i class="fas fa-capsules"></i>
                STOK OBAT
            </a>

            <a href="/profil-klinik" class="main-btn">
                <i class="fas fa-hospital-user"></i>
                PROFIL KLINIK
            </a>
        </div>
    </div>
    
    <a href="https://wa.me/6281528455350?text=Halo%20Dokter,%20saya%20ingin%20konsultasi%20darurat." class="wa-float" target="_blank">
        <i class="fab fa-whatsapp"></i>
    </a>

    <button onclick="toggleFullScreen()" class="lock-screen-btn">
        <i class="fas fa-expand"></i>
        <span>Layar Penuh</span>
    </button>

    <script>
        function updateStatus() {
            fetch('/api/clinic/status').then(r => r.json()).then(data => {
                const el = document.getElementById('status-container');
                if(data.open) {
                    el.innerHTML = '<span class="status-badge status-open">KLINIK BUKA</span>';
                } else {
                    el.innerHTML = '<span class="status-badge status-closed">KLINIK TUTUP</span>';
                }
            });
        }
        
        function toggleClinicStatus() {
            fetch('/api/clinic/status', { method: 'POST' }).then(() => updateStatus());
        }
        
        updateStatus();
    </script>
    {{ spa_script|safe }}
</body>
</html>
"""

HTML_QUEUE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Antrean Klinik</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background: #f0f2f5; font-family: 'Segoe UI', sans-serif; padding-top: 80px; }
        .monitor-box {
            background: white; border-radius: 15px; padding: 30px; text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1); margin-bottom: 20px;
        }
        .big-number { font-size: 6rem; font-weight: 800; color: #2ecc71; line-height: 1; }
        .form-box { background: white; border-radius: 15px; padding: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .ticket {
            border: 2px dashed #2ecc71; background: #e8f5e9; padding: 20px; border-radius: 10px;
            text-align: center; margin-top: 20px; display: none;
        }
    </style>
</head>
<body>
    {{ internal_navbar|safe }}
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-5">
                <div class="monitor-box">
                    <h4 class="text-muted text-uppercase">Sedang Diperiksa</h4>
                    <div class="big-number" id="current-num">--</div>
                    <p class="mb-0" id="current-name">Menunggu Dokter...</p>
                </div>
                
                <div class="monitor-box mt-3">
                    <h5>Antrean Menunggu</h5>
                    <div class="fs-4 fw-bold" id="waiting-count">0</div>
                    <small class="text-muted">Orang</small>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="form-box">
                    <h4 class="mb-3 border-bottom pb-2">Ambil Nomor Antrean</h4>
                    <form id="queue-form" onsubmit="submitQueue(event)">
                        <div class="mb-3">
                            <label>Nama Pasien</label>
                            <input type="text" id="q-name" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label>Nomor HP (WhatsApp)</label>
                            <input type="tel" id="q-phone" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label>Keluhan Utama</label>
                            <textarea id="q-complaint" class="form-control" rows="2" required></textarea>
                        </div>
                        <button type="submit" class="btn btn-success w-100 py-2 fw-bold">AMBIL NOMOR</button>
                    </form>
                    
                    <div id="ticket-view" class="ticket">
                        <h4>TIKET ANTREAN ANDA</h4>
                        <div class="display-1 fw-bold text-success" id="my-number">0</div>
                        <p>Silakan menunggu panggilan.</p>
                        <button class="btn btn-sm btn-outline-success" onclick="location.reload()">Selesai</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function refreshStatus() {
            fetch('/api/queue/status').then(r => r.json()).then(data => {
                document.getElementById('current-num').innerText = data.current_number || '--';
                document.getElementById('current-name').innerText = data.current_name || 'Tidak ada pasien';
                document.getElementById('waiting-count').innerText = data.waiting_count;
            });
        }
        
        function submitQueue(e) {
            e.preventDefault();
            const data = {
                name: document.getElementById('q-name').value,
                phone: document.getElementById('q-phone').value,
                complaint: document.getElementById('q-complaint').value
            };
            
            fetch('/api/queue/add', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            }).then(r => r.json()).then(res => {
                if(res.ticket) {
                    document.getElementById('queue-form').style.display = 'none';
                    document.getElementById('ticket-view').style.display = 'block';
                    document.getElementById('my-number').innerText = res.ticket;
                }
            });
        }
        
        setInterval(refreshStatus, 3000);
        refreshStatus();
    </script>
    {{ spa_script|safe }}
</body>
</html>
"""

HTML_DOCTOR_REKAM = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dokter - Rekam Medis</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background: #e9ecef; padding-top: 70px; }
        .queue-card { background: white; border-left: 5px solid #2ecc71; padding: 15px; margin-bottom: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); cursor:pointer; }
        .queue-card:hover { transform: translateX(5px); transition:0.2s; }
        .queue-card.active { border-left-color: #f1c40f; background: #fffbe6; }
        .section-title { font-weight:700; color:#555; margin-bottom:15px; border-bottom:2px solid #ddd; padding-bottom:5px; }
    </style>
</head>
<body>
    {{ internal_navbar|safe }}
    
    <div class="container-fluid px-4 py-3">
        <div class="row g-4">
            <!-- Mobile: Order 2. Desktop: Order 1 (Left) -->
            <div class="col-lg-3 order-2 order-lg-1">
                <div class="bg-white p-3 rounded shadow-sm h-100">
                    <h5 class="section-title"><i class="fas fa-users text-primary"></i> Antrean Menunggu</h5>
                    <div id="queue-list" style="max-height: 70vh; overflow-y: auto;">
                        <!-- JS Loaded -->
                    </div>
                </div>
            </div>
            
            <!-- Mobile: Order 1. Desktop: Order 2 (Center/Main) -->
            <div class="col-lg-6 order-1 order-lg-2">
                <div class="bg-white p-4 rounded shadow-sm mb-4">
                    <h5 class="section-title"><i class="fas fa-stethoscope text-success"></i> Sedang Diperiksa</h5>
                    <div id="current-patient-panel">
                        <div class="text-center text-muted py-5">
                            <i class="fas fa-user-md fa-3x mb-3 text-secondary"></i><br>
                            Belum ada pasien dipanggil
                        </div>
                    </div>
                </div>
            </div>

            <!-- Mobile: Order 3. Desktop: Order 3 (Right) -->
            <div class="col-lg-3 order-3 order-lg-3">
                 <div class="bg-white p-3 rounded shadow-sm h-100">
                    <h5 class="section-title"><i class="fas fa-history text-warning"></i> Riwayat Hari Ini</h5>
                    <div style="max-height: 70vh; overflow-y: auto;">
                        <table class="table table-sm table-hover">
                            <thead><tr><th>No</th><th>Nama</th><th>Diagnosa</th></tr></thead>
                            <tbody id="history-table"></tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Finish Modal -->
    <div class="modal fade" id="finishModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header bg-success text-white">
                    <h5 class="modal-title">Selesaikan Pemeriksaan</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <input type="hidden" id="finish-id">
                    <div class="mb-3">
                        <label>Diagnosa</label>
                        <textarea id="diag-input" class="form-control" rows="2"></textarea>
                    </div>
                    <div class="mb-3">
                        <label>Resep Obat</label>
                        <textarea id="presc-input" class="form-control" rows="3"></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-primary" onclick="submitFinish()">Simpan & Selesai</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function escapeHtml(text) {
            if (!text) return "";
            return text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        function loadData() {
            if(!document.getElementById('queue-list')) return; // Exit if element missing (SPA nav)

            fetch('/api/queue/status?full=1').then(r => r.json()).then(data => {
                // Queue List
                const list = document.getElementById('queue-list');
                if(!list) return;
                list.innerHTML = '';
                data.waiting.forEach(p => {
                    list.innerHTML += `
                        <div class="queue-card" onclick="callPatient(${p.id})">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <span class="badge bg-secondary mb-1">#${p.number}</span>
                                    <div class="fw-bold">${escapeHtml(p.name)}</div>
                                    <small class="text-muted text-truncate" style="max-width: 150px; display:block;">${escapeHtml(p.complaint)}</small>
                                </div>
                                <button class="btn btn-sm btn-primary"><i class="fas fa-bullhorn"></i></button>
                            </div>
                        </div>
                    `;
                });
                if(data.waiting.length === 0) list.innerHTML = '<p class="text-muted text-center py-4">Tidak ada antrean.</p>';
                
                // Current Patient
                const panel = document.getElementById('current-patient-panel');
                if (data.current) {
                    panel.innerHTML = `
                        <div class="alert alert-warning border-warning">
                            <div class="d-flex justify-content-between">
                                <span class="badge bg-warning text-dark fs-5">#${data.current.number}</span>
                                <span class="text-muted small">${data.current.created_at || ''}</span>
                            </div>
                            <h2 class="fw-bold my-3">${escapeHtml(data.current.name)}</h2>
                            <div class="p-3 bg-white rounded mb-3 border">
                                <strong>Keluhan:</strong><br>
                                ${escapeHtml(data.current.complaint)}
                            </div>
                            <hr>
                            <button class="btn btn-success btn-lg w-100 shadow" onclick="openFinishModal(${data.current.id})">
                                <i class="fas fa-check-circle"></i> Selesai & Rekam Medis
                            </button>
                        </div>
                    `;
                } else {
                    panel.innerHTML = '<div class="text-center text-muted py-5"><i class="fas fa-user-md fa-3x mb-3 text-secondary"></i><br>Belum ada pasien dipanggil</div>';
                }
                
                // History
                const hist = document.getElementById('history-table');
                hist.innerHTML = '';
                data.history.forEach(p => {
                    hist.innerHTML += `<tr><td>${p.number}</td><td>${escapeHtml(p.name)}</td><td><small>${escapeHtml(p.diagnosis)}</small></td></tr>`;
                });
            });
        }
        
        function callPatient(id) {
            fetch('/api/queue/action', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ action: 'call', id: id })
            }).then(() => loadData());
        }
        
        function openFinishModal(id) {
            document.getElementById('finish-id').value = id;
            document.getElementById('diag-input').value = '';
            document.getElementById('presc-input').value = '';
            new bootstrap.Modal(document.getElementById('finishModal')).show();
        }
        
        function submitFinish() {
            const id = document.getElementById('finish-id').value;
            const diag = document.getElementById('diag-input').value;
            const presc = document.getElementById('presc-input').value;
            
            fetch('/api/queue/action', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ action: 'finish', id: id, diagnosis: diag, prescription: presc })
            }).then(() => {
                // With SPA, we might want to just reload data or nav
                loadData();
                document.querySelector('.btn-close').click(); // close modal
            });
        }
        
        // Start Poll
        loadData();
        // Since SPA re-executes this script every time, we get a new interval.
        // We should clear old one? hard to access.
        // But the check at start of loadData will prevent errors.
        setInterval(loadData, 5000);
    </script>
    {{ spa_script|safe }}
</body>
</html>
"""

HTML_DOCTOR_STOCK = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stok Obat</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-light" style="padding-top: 80px;">
    {{ internal_navbar|safe }}
    <div class="container py-3">
        <div class="card shadow-sm mb-4">
            <div class="card-body">
                <form id="add-stock-form" class="row g-3" onsubmit="addStock(event)">
                    <div class="col-md-4">
                        <input type="text" class="form-control" id="new-name" placeholder="Nama Obat" required>
                    </div>
                    <div class="col-md-3">
                        <input type="number" class="form-control" id="new-stock" placeholder="Jumlah" required>
                    </div>
                    <div class="col-md-3">
                        <input type="text" class="form-control" id="new-unit" placeholder="Satuan (Strip/Botol)" value="pcs" required>
                    </div>
                    <div class="col-md-2">
                        <button type="submit" class="btn btn-primary w-100">+ Tambah</button>
                    </div>
                </form>
            </div>
        </div>
        
        <div class="bg-white rounded shadow-sm p-4">
            <table class="table table-hover align-middle">
                <thead>
                    <tr>
                        <th>Nama Obat</th>
                        <th>Stok</th>
                        <th>Satuan</th>
                        <th>Aksi</th>
                    </tr>
                </thead>
                <tbody id="stock-table">
                    <!-- JS Loaded -->
                </tbody>
            </table>
        </div>
    </div>

    <script>
        function escapeHtml(text) {
            if (!text) return "";
            return text.toString()
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        function loadStock() {
            fetch('/api/stock/list').then(r => r.json()).then(data => {
                const tbody = document.getElementById('stock-table');
                tbody.innerHTML = '';
                data.forEach(item => {
                    const row = `
                        <tr>
                            <td>${escapeHtml(item.name)}</td>
                            <td class="${item.stock < 10 ? 'text-danger fw-bold' : ''}">${item.stock}</td>
                            <td>${escapeHtml(item.unit)}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-danger" onclick="updateStock(${item.id}, -1)">-1</button>
                                <button class="btn btn-sm btn-outline-success" onclick="updateStock(${item.id}, 1)">+1</button>
                                <button class="btn btn-sm btn-danger ms-2" onclick="deleteStock(${item.id})"><i class="fas fa-trash"></i></button>
                            </td>
                        </tr>
                    `;
                    tbody.innerHTML += row;
                });
            });
        }
        
        function addStock(e) {
            e.preventDefault();
            const name = document.getElementById('new-name').value;
            const stock = document.getElementById('new-stock').value;
            const unit = document.getElementById('new-unit').value;
            
            fetch('/api/stock/update', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ action: 'create', name, stock, unit })
            }).then(() => {
                document.getElementById('add-stock-form').reset();
                loadStock();
            });
        }
        
        function updateStock(id, change) {
            fetch('/api/stock/update', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ action: 'update', id, change })
            }).then(() => loadStock());
        }
        
        function deleteStock(id) {
            if(!confirm('Hapus obat ini?')) return;
            fetch('/api/stock/update', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ action: 'delete', id })
            }).then(() => loadStock());
        }
        
        loadStock();
    </script>
    {{ spa_script|safe }}
</body>
</html>
"""

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

<div class="main-navbar">
    <div class="navbar-logo-container" onclick="toggleLogoPopup()">
        <a href="javascript:void(0)">
            <img src="{{ url_for('static', filename='logo-tahkil-fc.png') }}" class="navbar-logo-img" alt="TAHKIL FC">
        </a>
    </div>
    <div class="d-lg-none fw-bold fs-4 position-absolute start-50 translate-middle-x" style="white-space: nowrap;">TAHFIZH KILAT FC</div>
    <div class="navbar-links d-none d-lg-flex">
        <a href="#hero" class="nav-item-custom">Home</a>
        <a href="#players" class="nav-item-custom">Pemain</a>
        <a href="#coaches" class="nav-item-custom">Pelatih</a>
        <a href="#mvp" class="nav-item-custom">MVP</a>
        <a href="#agenda-latihan" class="nav-item-custom">Agenda</a>
        <a href="#main-partners" class="nav-item-custom">Sponsors</a>
    </div>
    <button class="d-lg-none btn border-0" onclick="toggleMobileMenu()"><i class="fas fa-bars fa-2x"></i></button>
    <div class="navbar-split-border"></div>
</div>

<div id="mobile-menu" class="mobile-menu-container">
    <div class="mobile-next-match">{{ data['settings'].get('next_match_text', 'Next Match: TAHKIL FC (Jan 2026)') }}</div>
    <a href="#hero" class="mobile-nav-link">Home</a>
    <a href="#players" class="mobile-nav-link">Pemain</a>
    <a href="#coaches" class="mobile-nav-link">Pelatih</a>
    <a href="#mvp" class="mobile-nav-link">MVP</a>
    <a href="#agenda-latihan" class="mobile-nav-link">Agenda</a>
    <a href="#main-partners" class="mobile-nav-link">Sponsors</a>
    
    <div class="mt-auto d-flex flex-column gap-3">
        <div class="history-btn justify-content-center d-lg-none" onclick="toggleFullScreen()" style="background: #111; color: #FFD700;">
            <i class="fas fa-expand"></i>
            Layar Penuh
        </div>
        <div class="history-btn justify-content-center" onclick="openHistoryModal()">
            <img src="{{ url_for('static', filename='logo-tahkil-fc.png') }}" class="monochrome-icon">
            Lihat Sejarah
        </div>
        <button onclick="document.getElementById('login-modal').style.display='flex'" class="btn btn-outline-dark w-100">Admin Login</button>
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
                    </div>
                    <form action="/upload/sponsor/{{ sponsor.id }}" method="post" enctype="multipart/form-data" class="position-absolute bottom-0 end-0">
                        <input type="file" name="image" onchange="this.form.submit()" style="display:none;" id="sp-upload-{{ sponsor.id }}">
                        <label for="sp-upload-{{ sponsor.id }}" class="btn btn-sm btn-light border rounded-circle p-1" style="width:30px;height:30px;display:flex;align-items:center;justify-content:center;cursor:pointer;"><i class="fas fa-camera text-primary"></i></label>
                    </form>
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
                    {% if admin %}
                    <form id="pm-upload-form" method="post" enctype="multipart/form-data" class="position-absolute bottom-0 end-0 m-3">
                         <input type="file" name="image" onchange="this.form.submit()" style="display:none;" id="pm-upload">
                         <label for="pm-upload" class="btn btn-warning shadow"><i class="fas fa-camera"></i></label>
                    </form>
                    {% endif %}
                </div>
                
                <!-- Info Column (Left on desktop, Bottom on mobile) -->
                <div class="col-md-7 order-md-1 text-start d-flex flex-column justify-content-center">
                     {% if admin %}
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
            </div>
            
            <div class="time-box-wrapper" id="agenda-time-wrapper">
                <!-- Injected via JS -->
            </div>
        </div>
    </div>

    <!-- HISTORY MODAL -->
    <div id="history-modal" class="modal-overlay" onclick="closeHistoryModal()">
        <div class="modal-content-custom" onclick="event.stopPropagation()">
            <h2 style="color:var(--gold);">Sejarah TAHKIL FC</h2>
            
            <!-- History Image Container 16:9 -->
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

    <!-- NEWS DETAIL MODAL -->
    <div id="news-modal" class="modal-overlay" onclick="document.getElementById('news-modal').style.display='none'">
        <div class="modal-content-custom" onclick="event.stopPropagation()" style="text-align:left; max-width:900px;">
            <div id="news-modal-date" class="text-uppercase text-muted fw-bold mb-2" style="font-size:0.8rem;"></div>
            
            <div style="position:relative;">
                <img id="news-modal-img" src="" style="width:100%; height:300px; object-fit:cover; border-radius:8px; margin-bottom:15px;">
                {% if admin %}
                <form id="news-upload-form" method="post" enctype="multipart/form-data" class="position-absolute bottom-0 end-0 m-3">
                     <input type="file" name="image" onchange="this.form.submit()" style="display:none;" id="news-upload">
                     <label for="news-upload" class="btn btn-warning shadow"><i class="fas fa-camera"></i></label>
                </form>
                {% endif %}
            </div>

            {% if admin %}
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
            <div class="d-lg-none d-flex justify-content-center gap-4 mt-3">
                <a href="https://wa.me/6281528455350" class="social-icon-link" target="_blank"><i class="fab fa-whatsapp"></i></a>
                <a href="https://maps.app.goo.gl/4deg1ha8WaxWKdPC9" class="social-icon-link" target="_blank"><i class="fas fa-map-marker-alt"></i></a>
                <a href="https://www.instagram.com/rivkycahyahakikiori/" class="social-icon-link" target="_blank"><i class="fab fa-instagram"></i></a>
            </div>
        </div>
    </footer>

    <!-- DATA INJECTION FOR JS -->
    <script>
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
                
                // Inject Upload Button
                const uploadBtn = document.createElement('div');
                uploadBtn.className = 'camera-btn';
                uploadBtn.innerHTML = `<form action="/upload/agenda/${id}" method="post" enctype="multipart/form-data"><label for="p-up-${id}" style="cursor:pointer;width:100%;height:100%;display:flex;align-items:center;justify-content:center;"><i class="fas fa-camera"></i></label><input type="file" id="p-up-${id}" name="image" style="display:none;" onchange="this.form.submit()"></form>`;
                imgWrapper.appendChild(uploadBtn);
                
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
                
                // Inject Upload Button
                const uploadBtn = document.createElement('div');
                uploadBtn.className = 'camera-btn';
                uploadBtn.innerHTML = `<form action="/upload/agenda/${id}" method="post" enctype="multipart/form-data"><label for="ag-up-${id}" style="cursor:pointer;width:100%;height:100%;display:flex;align-items:center;justify-content:center;"><i class="fas fa-camera"></i></label><input type="file" id="ag-up-${id}" name="image" style="display:none;" onchange="this.form.submit()"></form>`;
                imgContainer.appendChild(uploadBtn);
                
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
        function toggleMobileMenu() { 
            document.getElementById('mobile-menu').classList.toggle('active');
            document.body.classList.toggle('no-scroll');
        }
        function toggleLogoPopup() {
            const popup = document.getElementById('logo-popup');
            popup.style.display = (popup.style.display === 'flex') ? 'none' : 'flex';
        }
        
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
             fetch('/api/update-text', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ table: 'site_settings', id: 'history_text', value: val })
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
    {{ spa_script|safe }}
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)
