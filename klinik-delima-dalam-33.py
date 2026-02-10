import os
import sqlite3
import time
import datetime
import json
import io
import re
import base64
import qrcode
from functools import wraps
from PIL import Image
from flask import Flask, request, send_from_directory, redirect, url_for, render_template_string, jsonify, session
from werkzeug.utils import secure_filename

# --- FLASK CONFIGURATION ---
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB Limit
app.secret_key = "supersecretkey"

# Load Symptom Data
try:
    with open('symptom_data.json', 'r') as f:
        SYMPTOM_RULES = json.load(f)
except Exception as e:
    print(f"Error loading symptom data: {e}")
    SYMPTOM_RULES = []

@app.context_processor
def inject_rbac():
    return dict(role=session.get('role', 'patient'), menu_items=MENU_ITEMS)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff', 'ico', 'svg', 'mp3', 'wav', 'ogg', 'mp4', 'm4a', 'flac', 'srt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_wita_now():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=8)

def format_date_indo(date_str):
    if not date_str: return ""
    try:
        # Handle if date_str contains time or not
        if 'T' in date_str: date_str = date_str.replace('T', ' ')
        
        if ' ' in date_str:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        else:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            
        months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        return f"{dt.day} {months[dt.month - 1]} {dt.year}"
    except:
        return date_str

# --- RBAC CONFIGURATION ---
MENU_ITEMS = [
    {'route': '/antrean', 'label': 'Antrean', 'icon': 'fas fa-users', 'roles': ['patient', 'admin', 'doctor']},
    {'route': '/symptom-checker', 'label': 'Cek Gejala', 'icon': 'fas fa-user-md', 'roles': ['patient', 'doctor']},
    {'route': '/booking', 'label': 'Booking', 'icon': 'fas fa-calendar-check', 'roles': ['patient', 'doctor']},
    {'route': '/profil-klinik', 'label': 'Profil Klinik', 'icon': 'fas fa-hospital-user', 'roles': ['patient', 'admin', 'doctor']},
    {'route': '/booking-list', 'label': 'Daftar Janji', 'icon': 'fas fa-calendar-alt', 'roles': ['admin', 'doctor']},
    {'route': '/rekam-medis', 'label': 'Rekam Medis', 'icon': 'fas fa-notes-medical', 'roles': ['doctor']},
    {'route': '/stok-obat', 'label': 'Stok Obat', 'icon': 'fas fa-capsules', 'roles': ['admin', 'doctor']},
    {'route': '/surat-sakit', 'label': 'Surat Sakit', 'icon': 'fas fa-file-medical', 'roles': ['doctor']},
    {'route': '/kasir', 'label': 'Kasir & Laporan', 'icon': 'fas fa-cash-register', 'roles': ['admin', 'doctor']},
    {'route': '/database-pasien', 'label': 'Data Pasien', 'icon': 'fas fa-database', 'roles': ['admin', 'doctor']},
    {'route': '/pencarian-pasien', 'label': 'Cari Pasien', 'icon': 'fas fa-search', 'roles': ['admin', 'doctor']},
    {'route': '/statistik', 'label': 'Statistik', 'icon': 'fas fa-chart-pie', 'roles': ['doctor']},
    {'route': '/download-data', 'label': 'Unduh Data', 'icon': 'fas fa-file-pdf', 'roles': ['admin', 'doctor']},
    {'route': '/financial-dashboard', 'label': 'Keuangan', 'icon': 'fas fa-chart-line', 'roles': ['doctor']},
    {'route': '/expiry-tracker', 'label': 'Expiry Alert', 'icon': 'fas fa-exclamation-triangle', 'roles': ['admin', 'doctor']},
    {'route': '/receipt-list', 'label': 'Cetak Struk', 'icon': 'fas fa-receipt', 'roles': ['admin', 'doctor']},
    {'route': '/wa-reminder', 'label': 'WA Reminder', 'icon': 'fab fa-whatsapp', 'roles': ['admin', 'doctor']},
    {'route': '/qr-pasien', 'label': 'Pasien QR', 'icon': 'fas fa-qrcode', 'roles': ['admin', 'doctor']},
    {'route': '/peta-sebaran', 'label': 'Peta Penyakit', 'icon': 'fas fa-map-marked-alt', 'roles': ['doctor']},
    {'route': '/prediksi-stok', 'label': 'Prediksi Stok', 'icon': 'fas fa-chart-line', 'roles': ['doctor']},
    {'route': '/lab-results', 'label': 'Hasil Lab', 'icon': 'fas fa-vial', 'roles': ['admin', 'doctor']},
    {'route': '/audit-log', 'label': 'Audit Log', 'icon': 'fas fa-history', 'roles': ['doctor']},
    {'route': '/backup-db', 'label': 'Backup DB', 'icon': 'fas fa-shield-alt', 'roles': ['doctor']},
]

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_role = session.get('role', 'patient')
            if current_role not in allowed_roles:
                return render_template_string("<h1>403 Unauthorized</h1><p>Anda tidak memiliki akses ke halaman ini.</p><a href='/'>Kembali</a>"), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

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
                    medical_action TEXT,
                    cancellation_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    try: c.execute("ALTER TABLE queue ADD COLUMN medical_action TEXT")
    except: pass
    try: c.execute("ALTER TABLE queue ADD COLUMN cancellation_reason TEXT")
    except: pass
    try: c.execute("ALTER TABLE queue ADD COLUMN fee_doctor INTEGER DEFAULT 0")
    except: pass
    try: c.execute("ALTER TABLE queue ADD COLUMN fee_medicine INTEGER DEFAULT 0")
    except: pass
    try: c.execute("ALTER TABLE queue ADD COLUMN finished_at TEXT")
    except: pass
    try: c.execute("ALTER TABLE queue ADD COLUMN address TEXT")
    except: pass
    
    # Audit Logs
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT,
                    action TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    
    # Lab Results
    c.execute('''CREATE TABLE IF NOT EXISTS lab_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER,
                    description TEXT,
                    file_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    # Medicine Stock
    c.execute('''CREATE TABLE IF NOT EXISTS medicine_stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    stock INTEGER DEFAULT 0,
                    unit TEXT DEFAULT 'pcs',
                    expiry_date TEXT
                )''')
    try: c.execute("ALTER TABLE medicine_stock ADD COLUMN expiry_date TEXT")
    except: pass

    # Appointments
    c.execute('''CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT,
                    date TEXT,
                    time TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

# --- AUDIT LOG HELPERS ---
def log_audit(action, details, user="Admin"):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO audit_logs (user, action, details) VALUES (?, ?, ?)", (user, action, details))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Audit Log Error: {e}")

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
    # Render Queue (Antrean) as Home
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_title }}', 'ANTREAN')
    return render_template_string(HTML_QUEUE.replace('{{ navbar|safe }}', navbar))

@app.route('/antrean')
def antrean_page():
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fas fa-users').replace('{{ page_title }}', 'ANTREAN')
    return render_template_string(HTML_QUEUE.replace('{{ navbar|safe }}', navbar))

@app.route('/rekam-medis')
@role_required(['doctor'])
def rekam_medis_page():
    # Admin check removed for development
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fas fa-notes-medical').replace('{{ page_title }}', 'REKAM MEDIS')
    return render_template_string(HTML_DOCTOR_REKAM.replace('{{ navbar|safe }}', navbar))

@app.route('/stok-obat')
@role_required(['admin', 'doctor'])
def stok_obat_page():
    # Admin check removed for development
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fas fa-capsules').replace('{{ page_title }}', 'STOK OBAT')
    return render_template_string(HTML_DOCTOR_STOCK.replace('{{ navbar|safe }}', navbar))

@app.route('/surat-sakit')
@role_required(['doctor'])
def surat_sakit_list():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM queue WHERE status='done' ORDER BY created_at DESC LIMIT 50")
    patients = [dict(r) for r in c.fetchall()]
    conn.close()
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fas fa-file-medical').replace('{{ page_title }}', 'SURAT SAKIT')
    return render_template_string(HTML_SICK_LIST.replace('{{ navbar|safe }}', navbar), patients=patients)

@app.route('/surat-sakit/print/<int:id>')
@role_required(['doctor'])
def surat_sakit_print(id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM queue WHERE id=?", (id,))
    row = c.fetchone()
    conn.close()
    if not row: return "Pasien tidak ditemukan", 404
    
    p = dict(row)
    days = request.args.get('days', '3')
    
    # Simple number to text (very basic, can extend)
    days_map = {'1':'Satu', '2':'Dua', '3':'Tiga', '4':'Empat', '5':'Lima', '7':'Tujuh'}
    days_text = days_map.get(str(days), str(days))
    
    # Use finished_at if available, else created_at, else now
    raw_date = p.get('finished_at') or p.get('created_at')
    if raw_date:
        date_str = format_date_indo(raw_date)
    else:
        date_str = format_date_indo(get_wita_now().strftime("%Y-%m-%d"))
    
    return render_template_string(HTML_SICK_PRINT, p=p, days=days, days_text=days_text, date=date_str)

@app.route('/kasir')
@role_required(['admin', 'doctor'])
def kasir_page():
    conn = get_db_connection()
    c = conn.cursor()
    today = datetime.date.today().isoformat()
    c.execute("SELECT * FROM queue WHERE status='done' AND created_at LIKE ? ORDER BY created_at DESC", (f"{today}%",))
    patients = [dict(r) for r in c.fetchall()]
    conn.close()
    
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fas fa-cash-register').replace('{{ page_title }}', 'KASIR & LAPORAN')
    return render_template_string(HTML_CASHIER.replace('{{ navbar|safe }}', navbar), patients=patients)

@app.route('/api/kasir/update', methods=['POST'])
@role_required(['admin', 'doctor'])
def api_kasir_update():
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE queue SET fee_doctor=?, fee_medicine=? WHERE id=?", (data.get('fee_doctor'), data.get('fee_medicine'), data.get('id')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/database-pasien')
@role_required(['admin', 'doctor'])
def database_pasien_page():
    q = request.args.get('q', '')
    conn = get_db_connection()
    c = conn.cursor()
    if q:
        c.execute("SELECT * FROM queue WHERE status='done' AND (name LIKE ? OR phone LIKE ?) ORDER BY created_at DESC LIMIT 50", (f"%{q}%", f"%{q}%"))
    else:
        c.execute("SELECT * FROM queue WHERE status='done' ORDER BY created_at DESC LIMIT 20")
    patients = [dict(r) for r in c.fetchall()]
    conn.close()
    
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fas fa-database').replace('{{ page_title }}', 'DATABASE PASIEN')
    return render_template_string(HTML_PATIENT_DB.replace('{{ navbar|safe }}', navbar), patients=patients)

@app.route('/pencarian-pasien')
@role_required(['admin', 'doctor'])
def pencarian_pasien_page():
    q = request.args.get('q', '')
    patients = []
    if q:
        conn = get_db_connection()
        c = conn.cursor()
        # Group by phone to get unique patients (approx)
        c.execute("SELECT * FROM queue WHERE name LIKE ? OR phone LIKE ? GROUP BY phone LIMIT 20", (f"%{q}%", f"%{q}%"))
        patients = [dict(r) for r in c.fetchall()]
        conn.close()
    
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fas fa-search').replace('{{ page_title }}', 'CARI PASIEN')
    return render_template_string(HTML_SEARCH.replace('{{ navbar|safe }}', navbar), patients=patients)

@app.route('/statistik')
@role_required(['doctor'])
def statistik_page():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT diagnosis, COUNT(*) as cnt FROM queue WHERE status='done' AND diagnosis IS NOT NULL AND diagnosis != '' GROUP BY diagnosis ORDER BY cnt DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    
    chart_data = {
        'labels': [r['diagnosis'] for r in rows],
        'values': [r['cnt'] for r in rows]
    }
    
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fas fa-chart-pie').replace('{{ page_title }}', 'STATISTIK')
    return render_template_string(HTML_STATS.replace('{{ navbar|safe }}', navbar), chart_data=chart_data)

@app.route('/download-data')
@role_required(['admin', 'doctor'])
def download_data_page():
    return render_template_string(HTML_DOWNLOAD_PDF)

@app.route('/api/export-data')
@role_required(['admin', 'doctor'])
def api_export_data():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Queue Stats (Daily Count)
    # SQLite date function
    c.execute("SELECT date(created_at) as d, COUNT(*) as c FROM queue GROUP BY d ORDER BY d DESC")
    queue_stats = [dict(r) for r in c.fetchall()]
    
    # History
    c.execute("SELECT * FROM queue ORDER BY created_at DESC")
    history = [dict(r) for r in c.fetchall()]
    
    # Cashier
    c.execute("SELECT * FROM queue WHERE status='done' ORDER BY created_at DESC")
    cashier = [dict(r) for r in c.fetchall()]
    
    conn.close()
    return jsonify({
        'queue_stats': queue_stats,
        'history': history,
        'cashier': cashier
    })

# --- CLINIC API ---

@app.route('/api/clinic/status', methods=['GET', 'POST'])
def api_clinic_status():
    conn = get_db_connection()
    c = conn.cursor()
    
    if request.method == 'POST':
        # if not session.get('admin'): return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.json or {}
        if 'set_status' in data:
            new_val = '1' if data['set_status'] else '0'
        else:
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
    address = data.get('address', '')
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get daily number
    today = datetime.date.today().isoformat()
    c.execute("SELECT MAX(number) as max_num FROM queue WHERE created_at LIKE ?", (f"{today}%",))
    row = c.fetchone()
    next_num = (row['max_num'] or 0) + 1
    
    c.execute("INSERT INTO queue (name, phone, complaint, number, status, address) VALUES (?, ?, ?, ?, 'waiting', ?)", 
              (name, phone, complaint, next_num, address))
    conn.commit()
    conn.close()
    
    log_audit('QUEUE_ADD', f"Added patient {name} (#{next_num})")
    
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
        if session.get('role') not in ['admin', 'doctor']:
            conn.close()
            return jsonify({'error': 'Unauthorized'}), 403

        c.execute("SELECT * FROM queue WHERE status='waiting' ORDER BY created_at ASC")
        waiting_list = [dict(r) for r in c.fetchall()]
        
        today = datetime.date.today().isoformat()
        c.execute("SELECT * FROM queue WHERE status='done' AND created_at LIKE ? ORDER BY created_at ASC", (f"{today}%",))
        history_list = [dict(r) for r in c.fetchall()]

        c.execute("SELECT * FROM queue WHERE status='cancelled' AND created_at LIKE ? ORDER BY created_at DESC", (f"{today}%",))
        cancelled_list = [dict(r) for r in c.fetchall()]
        
        conn.close()
        return jsonify({
            'current': current_data,
            'waiting_count': waiting_count,
            'waiting': waiting_list,
            'history': history_list,
            'cancelled': cancelled_list
        })
        
    conn.close()
    return jsonify({
        'current_number': current_data['number'] if current_data else None,
        'current_name': current_data['name'] if current_data else None,
        'waiting_count': waiting_count
    })

@app.route('/api/queue/archive')
@role_required(['admin', 'doctor'])
def api_queue_archive():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM queue WHERE status IN ('done', 'cancelled') ORDER BY created_at DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    
    grouped = {}
    for r in rows:
        # Use finished_at for date grouping if available, else created_at
        time_source = r.get('finished_at') or r['created_at']
        date_str = time_source.split(' ')[0] if time_source else 'Unknown'
        if date_str not in grouped:
            grouped[date_str] = []
        grouped[date_str].append(r)
        
    return jsonify(grouped)

@app.route('/api/patient/my-card', methods=['POST'])
def api_patient_card():
    data = request.json
    phone = data.get('phone', '')
    if not phone:
        return jsonify({'error': 'No phone number provided'}), 400
    
    conn = get_db_connection()
    c = conn.cursor()
    # Get the latest visit
    c.execute("SELECT * FROM queue WHERE phone = ? ORDER BY created_at DESC LIMIT 1", (phone,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'error': 'Patient not found'}), 404
        
    return jsonify(dict(row))

@app.route('/api/patient/my-lab', methods=['POST'])
def api_patient_lab():
    data = request.json
    phone = data.get('phone', '')
    if not phone:
        return jsonify({'error': 'No phone number provided'}), 400
    
    conn = get_db_connection()
    c = conn.cursor()
    # Get all patient IDs for this phone
    c.execute("SELECT id FROM queue WHERE phone = ?", (phone,))
    patient_ids = [r['id'] for r in c.fetchall()]
    
    if not patient_ids:
        conn.close()
        return jsonify([])
        
    # Get lab results
    placeholders = ','.join('?' * len(patient_ids))
    c.execute(f"SELECT * FROM lab_results WHERE patient_id IN ({placeholders}) ORDER BY created_at DESC", patient_ids)
    results = [dict(r) for r in c.fetchall()]
    conn.close()
    
    return jsonify(results)

@app.route('/api/queue/action', methods=['POST'])
@role_required(['admin', 'doctor'])
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
        med_action = data.get('medical_action')
        now_wita = get_wita_now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE queue SET status='done', diagnosis=?, prescription=?, medical_action=?, finished_at=? WHERE id=?", (diag, presc, med_action, now_wita, id))
        log_audit('QUEUE_FINISH', f"Finished patient ID {id}")
        
    elif action == 'cancel':
        reason = data.get('reason')
        c.execute("UPDATE queue SET status='cancelled', cancellation_reason=? WHERE id=?", (reason, id))
        log_audit('QUEUE_CANCEL', f"Cancelled patient ID {id}: {reason}")

    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/stock/list')
@role_required(['admin', 'doctor'])
def api_stock_list():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM medicine_stock ORDER BY name ASC")
    items = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(items)

@app.route('/api/stock/update', methods=['POST'])
@role_required(['admin', 'doctor'])
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
    log_audit('STOCK_UPDATE', f"Action: {action}, Data: {str(data)}")
    return jsonify({'success': True})

@app.route('/api/dental/settings', methods=['GET', 'POST'])
def api_dental_settings():
    conn = get_db_connection()
    c = conn.cursor()
    
    if request.method == 'POST':
        # Need developer auth effectively, but we trust the frontend gate for now or check session if implemented
        # The user requested 'developer mode' access via frontend ID/Pass, but saving should probably be open if in dev mode
        # or we can rely on standard RBAC if logged in as admin. 
        # For this specific "game dev" request, we allow saving freely as per "real time universal" requirement
        data = request.json
        config_str = json.dumps(data)
        c.execute("INSERT OR REPLACE INTO site_settings (key, value) VALUES ('dental_game_config', ?)", (config_str,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
        
    c.execute("SELECT value FROM site_settings WHERE key='dental_game_config'")
    row = c.fetchone()
    conn.close()
    
    if row and row['value']:
        return jsonify(json.loads(row['value']))
    else:
        return jsonify({})

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
                       admin=session.get('admin', False))

@app.route('/login', methods=['POST'])
def login():
    uid = request.form.get('userid')
    pwd = request.form.get('password')
    
    if uid == 'dokter' and pwd == 'dokter123':
        session['role'] = 'doctor'
        return redirect(url_for('landing_page'))
    elif uid == 'admin' and pwd == 'admin123':
        session['role'] = 'admin'
        return redirect(url_for('landing_page'))
    elif uid == 'adminwebsite' and pwd == '4dm1nw3bs1t3':
        session['role'] = 'admin'
        return redirect(url_for('landing_page'))
        
    return redirect(url_for('landing_page'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing_page'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload/<type>/<id>', methods=['POST'])
@role_required(['admin', 'doctor'])
def upload_image(type, id):
    # if not session.get('admin'): return "Unauthorized", 403
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
@role_required(['admin', 'doctor'])
def api_update_text():
    # if not session.get('admin'): return jsonify({'error': 'Unauthorized'}), 403
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
@role_required(['admin', 'doctor'])
def api_add_card():
    # if not session.get('admin'): return jsonify({'error': 'Unauthorized'}), 403
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
@role_required(['admin', 'doctor'])
def api_delete_item():
    # if not session.get('admin'): return jsonify({'error': 'Unauthorized'}), 403
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

# --- NEW ENTERPRISE ROUTES ---

@app.route('/booking')
def booking_page():
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fas fa-calendar-check').replace('{{ page_title }}', 'BOOKING JANJI TEMU')
    return render_template_string(HTML_BOOKING.replace('{{ navbar|safe }}', navbar))

@app.route('/api/booking/add', methods=['POST'])
def api_booking_add():
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO appointments (name, phone, date, time) VALUES (?, ?, ?, ?)", 
              (data.get('name'), data.get('phone'), data.get('date'), data.get('time')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/financial-dashboard')
@role_required(['doctor'])
def financial_dashboard():
    # if not session.get('admin'): return "Unauthorized", 403
    conn = get_db_connection()
    c = conn.cursor()
    # Monthly Revenue
    c.execute("SELECT strftime('%Y-%m', created_at) as m, SUM(fee_doctor + fee_medicine) as total FROM queue WHERE status='done' GROUP BY m ORDER BY m ASC LIMIT 12")
    rows = c.fetchall()
    conn.close()
    
    chart_data = {
        'labels': [r['m'] for r in rows],
        'values': [r['total'] for r in rows]
    }
    
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fas fa-chart-line').replace('{{ page_title }}', 'DASHBOARD KEUANGAN')
    return render_template_string(HTML_FINANCE.replace('{{ navbar|safe }}', navbar), chart_data=chart_data)

@app.route('/expiry-tracker')
@role_required(['admin', 'doctor'])
def expiry_tracker():
    # if not session.get('admin'): return "Unauthorized", 403
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM medicine_stock ORDER BY expiry_date ASC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    
    medicines = []
    today = datetime.date.today()
    for r in rows:
        is_expiring = False
        if r['expiry_date']:
            try:
                exp = datetime.datetime.strptime(r['expiry_date'], '%Y-%m-%d').date()
                if (exp - today).days < 30:
                    is_expiring = True
            except: pass
        r['is_expiring'] = is_expiring
        medicines.append(r)
        
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fas fa-exclamation-triangle').replace('{{ page_title }}', 'ALERT KEDALUWARSA')
    return render_template_string(HTML_EXPIRY.replace('{{ navbar|safe }}', navbar), medicines=medicines)

@app.route('/api/stock/update-expiry', methods=['POST'])
@role_required(['admin', 'doctor'])
def api_stock_update_expiry():
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE medicine_stock SET expiry_date=? WHERE id=?", (data.get('date'), data.get('id')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/receipt-list')
@role_required(['admin', 'doctor'])
def receipt_list():
    # if not session.get('admin'): return "Unauthorized", 403
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM queue WHERE status='done' ORDER BY created_at DESC LIMIT 50")
    patients = [dict(r) for r in c.fetchall()]
    conn.close()
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fas fa-receipt').replace('{{ page_title }}', 'CETAK STRUK')
    return render_template_string(HTML_RECEIPT_LIST.replace('{{ navbar|safe }}', navbar), patients=patients)

@app.route('/print-receipt/<int:id>')
@role_required(['admin', 'doctor'])
def print_receipt(id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM queue WHERE id=?", (id,))
    row = c.fetchone()
    conn.close()
    if not row: return "Not Found", 404
    p = dict(row)
    
    total = (p['fee_doctor'] or 0) + (p['fee_medicine'] or 0)
    total_fmt = "{:,.0f}".format(total).replace(',', '.')
    date_str = (p['finished_at'] or p['created_at']).split(' ')[0]
    
    return render_template_string(HTML_RECEIPT_PRINT, p=p, total=total_fmt, date=date_str)

@app.route('/wa-reminder')
@role_required(['admin', 'doctor'])
def wa_reminder_page():
    # if not session.get('admin'): return "Unauthorized", 403
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM queue WHERE status='waiting' ORDER BY number ASC")
    patients = [dict(r) for r in c.fetchall()]
    conn.close()
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fab fa-whatsapp').replace('{{ page_title }}', 'WA REMINDER')
    return render_template_string(HTML_WA_REMINDER.replace('{{ navbar|safe }}', navbar), patients=patients)

@app.route('/booking-list')
@role_required(['admin', 'doctor'])
def booking_list_page():
    # if not session.get('admin'): return "Unauthorized", 403
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM appointments ORDER BY date DESC, time ASC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fas fa-calendar-alt').replace('{{ page_title }}', 'DAFTAR JANJI TEMU')
    return render_template_string(HTML_BOOKING_LIST.replace('{{ navbar|safe }}', navbar), appointments=rows)

@app.route('/backup-db')
@role_required(['doctor'])
def backup_db():
    # if not session.get('admin'): return "Unauthorized", 403
    return send_from_directory('.', 'data.db', as_attachment=True)

@app.route('/audit-log')
@role_required(['doctor'])
def audit_log_page():
    # if not session.get('admin'): return "Unauthorized", 403
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 100")
    logs = [dict(r) for r in c.fetchall()]
    conn.close()
    
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fas fa-history').replace('{{ page_title }}', 'AUDIT TRAIL')
    return render_template_string(HTML_AUDIT.replace('{{ navbar|safe }}', navbar), logs=logs)

@app.route('/qr-pasien')
@role_required(['admin', 'doctor'])
def qr_pasien_page():
    # Simple search interface
    q = request.args.get('q', '')
    patients = []
    if q:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM queue WHERE name LIKE ? OR phone LIKE ? GROUP BY phone LIMIT 20", (f"%{q}%", f"%{q}%"))
        patients = [dict(r) for r in c.fetchall()]
        conn.close()
    
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fas fa-qrcode').replace('{{ page_title }}', 'KARTU PASIEN QR')
    return render_template_string(HTML_QR_PAGE.replace('{{ navbar|safe }}', navbar), patients=patients)

@app.route('/api/qr/generate', methods=['POST'])
@role_required(['admin', 'doctor'])
def api_qr_generate():
    data = request.json
    # Content of QR: JSON string with ID, Name, Phone
    qr_content = json.dumps({
        'id': data.get('id'),
        'name': data.get('name'),
        'phone': data.get('phone')
    })
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = io.BytesIO()
    img.save(buf)
    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return jsonify({'image': img_b64})

@app.route('/symptom-checker')
def symptom_checker_page():
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fas fa-user-md').replace('{{ page_title }}', 'SYMPTOM CHECKER')
    return render_template_string(HTML_SYMPTOM.replace('{{ navbar|safe }}', navbar))

@app.route('/api/symptom/check', methods=['POST'])
def api_symptom_check():
    text = request.json.get('text', '').lower()
    
    best_match = None
    max_score = 0
    
    for rule in SYMPTOM_RULES:
        matches = 0
        total_keywords = len(rule['keywords'])
        
        if total_keywords == 0: continue
            
        for kw in rule['keywords']:
            if kw in text:
                matches += 1
        
        score = matches # Use raw match count to favor diseases with more matching details
        if score > max_score:
            max_score = score
            best_match = rule
                
    if best_match and max_score >= 1: # At least 1 keyword match
        disease = f"{best_match['name']} ({best_match['code']})" if best_match['code'] else best_match['name']
        advice = f"Gejala terdeteksi mirip dengan: {best_match['raw_symptoms']}. Segera konsultasi dokter untuk diagnosa pasti."
        confidence = "Tinggi" if max_score >= 3 else "Sedang"
    else:
        disease = "Tidak Spesifik / Belum Dikenali"
        advice = "Gejala tidak cocok dengan database 99 penyakit kami. Perbanyak istirahat dan hubungi dokter jika berlanjut."
        confidence = "Rendah"
        
    return jsonify({'disease': disease, 'advice': advice, 'confidence': confidence})

@app.route('/peta-sebaran')
@role_required(['doctor'])
def peta_sebaran_page():
    # Aggregate data
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT address, diagnosis FROM queue WHERE status='done' AND diagnosis IS NOT NULL")
    rows = c.fetchall()
    conn.close()
    
    # Process data
    data = {}
    for r in rows:
        addr = r['address'] if r['address'] else 'Blok A' # Defaulting to Blok A for demo if empty
        diag = r['diagnosis']
        if addr not in data: data[addr] = {}
        if diag not in data[addr]: data[addr][diag] = 0
        data[addr][diag] += 1
        
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fas fa-map-marked-alt').replace('{{ page_title }}', 'PETA SEBARAN PENYAKIT')
    return render_template_string(HTML_MAP.replace('{{ navbar|safe }}', navbar), map_data=data)

@app.route('/prediksi-stok')
@role_required(['doctor'])
def prediksi_stok_page():
    # Simple Moving Average Logic (Mocked for Demo as requested "Algorithms")
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM medicine_stock")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    
    predictions = []
    import random
    
    for r in rows:
        # Simulate analyzing last 7 days of usage
        # In real app, we would query: SELECT count(*) FROM queue WHERE prescription LIKE '%name%' AND date > 7_days_ago
        avg_usage = random.randint(1, 5) # 1-5 units per day
        days_left = r['stock'] // avg_usage if avg_usage > 0 else 999
        
        status = "Aman"
        css = "success"
        if days_left < 3:
            status = "KRITIS (Habis < 3 Hari)"
            css = "danger"
        elif days_left < 7:
            status = "Waspada (Habis < 1 Minggu)"
            css = "warning"
            
        predictions.append({
            'name': r['name'],
            'stock': r['stock'],
            'unit': r['unit'],
            'avg_usage': avg_usage,
            'days_left': days_left,
            'status': status,
            'css': css
        })
        
    predictions.sort(key=lambda x: x['days_left'])
    
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fas fa-chart-line').replace('{{ page_title }}', 'PREDIKSI STOK (AI)')
    return render_template_string(HTML_STOCK_PRED.replace('{{ navbar|safe }}', navbar), predictions=predictions)

@app.route('/lab-results')
@role_required(['admin', 'doctor'])
def lab_results_page():
    q = request.args.get('q', '')
    conn = get_db_connection()
    c = conn.cursor()
    if q:
        c.execute("SELECT * FROM queue WHERE name LIKE ? ORDER BY created_at DESC", (f"%{q}%",))
    else:
        c.execute("SELECT * FROM queue ORDER BY created_at DESC LIMIT 50")
    patients = [dict(r) for r in c.fetchall()]
    
    # Attach lab results
    for p in patients:
        c.execute("SELECT * FROM lab_results WHERE patient_id=? ORDER BY created_at DESC", (p['id'],))
        p['results'] = [dict(r) for r in c.fetchall()]
        
    conn.close()
    
    navbar = MEDICAL_NAVBAR_TEMPLATE.replace('{{ page_icon }}', 'fas fa-vial').replace('{{ page_title }}', 'HASIL LAB DIGITAL')
    return render_template_string(HTML_LAB.replace('{{ navbar|safe }}', navbar), patients=patients)

@app.route('/upload/lab', methods=['POST'])
@role_required(['admin', 'doctor'])
def upload_lab():
    if 'file' not in request.files: return "No file", 400
    file = request.files['file']
    patient_id = request.form.get('patient_id')
    desc = request.form.get('description')
    
    if file and file.filename != '' and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"lab_{patient_id}_{int(time.time())}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        conn = get_db_connection()
        c = conn.cursor()
        now_wita = get_wita_now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO lab_results (patient_id, description, file_path, created_at) VALUES (?, ?, ?, ?)", 
                  (patient_id, desc, filename, now_wita))
        conn.commit()
        conn.close()
        log_audit('LAB_UPLOAD', f"Uploaded {filename} for patient {patient_id}")
        
    return redirect('/lab-results')

# --- FRONTEND ASSETS ---

MEDICAL_FOOTER_TEMPLATE = """
<footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
    <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
    <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
</footer>
"""

MEDICAL_NAVBAR_TEMPLATE = """
<style>
    :root {
        --green: #2ecc71;
        --gold: #FFD700;
        --black: #111;
        --white: #fff;
        --blue: #3498db;
    }
    .medical-top-bar {
        {% if role == 'doctor' %}
        background: var(--gold);
        {% elif role == 'admin' %}
        background: var(--blue);
        {% else %}
        background: rgba(255, 255, 255, 0.9);
        {% endif %}
        
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        height: 70px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 20px;
        position: sticky;
        top: 0;
        z-index: 1050;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        transition: background 0.3s;
    }
    .medical-split-border {
        position: absolute; bottom: 0; left: 0; width: 100%; height: 3px;
        background: linear-gradient(90deg, var(--green) 50%, var(--gold) 50%);
    }
    .medical-logo-area { display: flex; align-items: center; gap: 15px; cursor: pointer; transition: transform 0.2s; }
    .medical-logo-area:hover { transform: scale(1.05); }
    .medical-logo-icon { font-size: 2rem; color: {% if role in ['admin', 'doctor'] %}white{% else %}var(--green){% endif %}; }
    .medical-title { 
        font-weight: 800; font-size: 1.5rem; text-transform: uppercase; 
        color: {% if role in ['admin', 'doctor'] %}white{% else %}#333{% endif %}; 
        letter-spacing: 1px;
    }
    
    /* Horizontal Menu */
    .medical-horizontal-menu {
        display: flex;
        overflow-x: auto;
        padding: 10px 15px;
        gap: 10px;
        background: rgba(255, 255, 255, 0.95);
        border-bottom: 1px solid rgba(0,0,0,0.05);
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none; /* Firefox */
        position: sticky;
        top: 70px; /* Adjust based on navbar height */
        z-index: 1040;
    }
    .medical-horizontal-menu::-webkit-scrollbar { display: none; } /* Chrome/Safari */
    
    .feature-btn {
        display: inline-flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-width: 90px;
        height: 85px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 3px 6px rgba(0,0,0,0.08);
        text-decoration: none;
        color: #555;
        padding: 8px;
        flex-shrink: 0;
        transition: transform 0.2s, box-shadow 0.2s;
        border: 1px solid rgba(0,0,0,0.02);
    }
    .feature-btn:hover, .feature-btn.active {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(46, 204, 113, 0.2);
        color: var(--green);
        border-color: var(--green);
    }
    .feature-btn i {
        font-size: 1.6rem;
        margin-bottom: 6px;
        color: var(--green);
    }
    .feature-btn span {
        font-size: 0.7rem;
        font-weight: 700;
        text-align: center;
        line-height: 1.1;
        text-transform: uppercase;
    }

    /* Role Switcher Buttons */
    .role-btn-group {
        display: flex;
        gap: 8px;
        align-items: center;
    }
    .role-btn {
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        cursor: pointer;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        transition: transform 0.2s;
    }
    .role-btn:hover { transform: scale(1.05); }
    .role-btn-pasien { background: white; color: #333; }
    .role-btn-admin { background: var(--blue); color: white; }
    .role-btn-dokter { background: var(--gold); color: black; }

    /* Dark Mode Styles - Enhanced */
    body.dark-mode {
        background: #121212 !important;
        color: #e0e0e0 !important;
    }
    body.dark-mode .medical-top-bar,
    body.dark-mode .medical-horizontal-menu {
        background: #1e1e1e !important;
        border-bottom-color: #333;
    }
    body.dark-mode .feature-btn {
        background: #2d2d2d;
        color: #bbb;
        border-color: #444;
    }
    body.dark-mode .feature-btn:hover {
        background: #333;
        color: var(--green);
    }
    
    /* Container & Card Backgrounds */
    body.dark-mode .card, 
    body.dark-mode .glass-panel,
    body.dark-mode .glass-panel-custom,
    body.dark-mode .modal-content,
    body.dark-mode .modal-card,
    body.dark-mode .login-modal-box,
    body.dark-mode .list-group-item,
    body.dark-mode .bg-white,
    body.dark-mode .bottom-nav {
        background-color: #1e1e1e !important;
        color: #e0e0e0 !important;
        border-color: #444 !important;
    }
    
    body.dark-mode #theme-menu-dropdown {
        background-color: #1e1e1e !important;
        border-color: #444 !important;
    }
    body.dark-mode #theme-menu-dropdown button {
        background-color: #1e1e1e !important;
        color: #e0e0e0 !important;
        border-bottom-color: #444 !important;
    }
    body.dark-mode #theme-menu-dropdown button:hover {
        background-color: #333 !important;
    }

    /* Headers & Titles */
    body.dark-mode .medical-title,
    body.dark-mode h1, body.dark-mode h2, body.dark-mode h3, 
    body.dark-mode h4, body.dark-mode h5, body.dark-mode h6,
    body.dark-mode .card-header,
    body.dark-mode .modal-header {
        color: #fff !important;
    }
    body.dark-mode .card-header,
    body.dark-mode .modal-header {
        background-color: #252525 !important;
        border-bottom-color: #444 !important;
    }
    
    /* Footer */
    body.dark-mode footer {
        background: #1e1e1e !important;
        border-top-color: #333 !important;
        color: #bbb !important;
    }
    body.dark-mode footer h5 {
        color: #fff !important;
    }
    body.dark-mode footer small {
        color: #888 !important;
    }
    
    /* Text Colors */
    body.dark-mode .text-dark { color: #ddd !important; }
    body.dark-mode .text-muted { color: #aaa !important; }
    body.dark-mode .text-primary { color: #64b5f6 !important; }
    body.dark-mode .text-success { color: #81c784 !important; }
    body.dark-mode .text-danger { color: #e57373 !important; }
    body.dark-mode label { color: #ddd !important; }
    
    /* Tables */
    body.dark-mode .table {
        color: #e0e0e0 !important;
        border-color: #444;
    }
    /* Ensure all cells have dark bg */
    body.dark-mode .table th,
    body.dark-mode .table td {
        background-color: #1e1e1e !important;
        color: #e0e0e0 !important;
        border-color: #444 !important;
    }
    /* Headers lighter */
    body.dark-mode .table thead th {
        background-color: #2d2d2d !important;
        color: #fff !important;
    }
    /* Table light overrides */
    body.dark-mode .table-light,
    body.dark-mode .table-light th,
    body.dark-mode .table-light td {
        background-color: #2d2d2d !important;
        color: #fff !important;
    }
    /* Table success overrides */
    body.dark-mode .table-success, 
    body.dark-mode .table-success th,
    body.dark-mode .table-success td {
        background-color: #1b5e20 !important;
        color: #e8f5e9 !important;
        border-color: #2e7d32 !important;
    }
    /* Hover - must target td to override the specific td rule above */
    body.dark-mode .table-hover tbody tr:hover,
    body.dark-mode .table-hover tbody tr:hover td,
    body.dark-mode .table-hover tbody tr:hover th {
        background-color: #333 !important;
        color: #fff !important;
    }
    
    /* Forms & Inputs */
    body.dark-mode .form-control,
    body.dark-mode .form-select,
    body.dark-mode input,
    body.dark-mode select,
    body.dark-mode textarea {
        background-color: #2d2d2d !important;
        border-color: #444 !important;
        color: #fff !important;
    }
    body.dark-mode .form-control::placeholder { color: #888; }
    body.dark-mode .input-group-text {
        background-color: #333 !important;
        border-color: #444;
        color: #eee !important;
    }
    
    /* Buttons & Misc */
    body.dark-mode .close-btn, 
    body.dark-mode .btn-close {
        filter: invert(1) grayscale(100%) brightness(200%);
    }
    body.dark-mode #map-container {
        background-color: #2d2d2d !important;
    }

    /* Clean Mode - Dark Minimalist Aesthetic */
    body.clean-mode {
        background: #000000 !important;
        background-image: none !important;
        color: #ffffff !important;
    }
    body.clean-mode .medical-top-bar {
        background: #000000 !important;
        border-bottom: 2px solid #333 !important;
        box-shadow: none !important;
    }
    body.clean-mode .medical-logo-icon,
    body.clean-mode .medical-title,
    body.clean-mode .feature-btn i,
    body.clean-mode h1, body.clean-mode h2, body.clean-mode h3, 
    body.clean-mode h4, body.clean-mode h5, body.clean-mode h6,
    body.clean-mode .text-dark,
    body.clean-mode .text-muted,
    body.clean-mode .nav-item {
        color: #ffffff !important;
    }
    body.clean-mode .feature-btn {
        background: #000000 !important;
        border: 2px solid #ffffff !important;
        color: #ffffff !important;
        box-shadow: none !important;
        border-radius: 8px !important;
    }
    body.clean-mode .feature-btn:hover,
    body.clean-mode .feature-btn.active {
        border-color: #FF6D00 !important;
        color: #FF6D00 !important;
    }
    body.clean-mode .feature-btn:hover i,
    body.clean-mode .feature-btn.active i {
        color: #FF6D00 !important;
    }
    body.clean-mode .card,
    body.clean-mode .glass-panel,
    body.clean-mode .glass-panel-custom,
    body.clean-mode .modal-content,
    body.clean-mode .modal-card,
    body.clean-mode .list-group-item,
    body.clean-mode .bg-white,
    body.clean-mode .bottom-nav,
    body.clean-mode .card-header,
    body.clean-mode .modal-header,
    body.clean-mode footer,
    body.clean-mode .table th, 
    body.clean-mode .table td,
    body.clean-mode .input-group-text,
    body.clean-mode #iconGalleryModal .login-modal-box {
        background-color: #000000 !important;
        color: #ffffff !important;
        border-color: #ffffff !important;
        box-shadow: none !important;
    }
    body.clean-mode .table-light,
    body.clean-mode .table-hover tbody tr:hover {
        background-color: #111 !important;
    }
    body.clean-mode .form-control,
    body.clean-mode .form-select,
    body.clean-mode input,
    body.clean-mode select,
    body.clean-mode textarea {
        background-color: #000000 !important;
        border: 1px solid #ffffff !important;
        color: #ffffff !important;
    }
    body.clean-mode .form-control:focus {
        border-color: #FF6D00 !important;
    }
    body.clean-mode .btn-primary {
        border-color: #FF6D00 !important;
        color: #FF6D00 !important;
        background: #000 !important;
    }
    body.clean-mode .btn-primary:hover {
        background-color: #FF6D00 !important;
        color: #000000 !important;
    }
    body.clean-mode .bottom-nav { border-top: 1px solid #ffffff !important; }

    /* Login Modal */
    .login-modal-overlay {
        display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.6); z-index: 9999; justify-content: center; align-items: center;
        backdrop-filter: blur(5px);
    }
    .login-modal-box {
        background: white; padding: 30px; border-radius: 15px; width: 320px;
        box-shadow: 0 15px 40px rgba(0,0,0,0.3); position: relative;
        animation: slideIn 0.3s ease-out;
    }
    @keyframes slideIn { from { transform: translateY(-20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

    @media (max-width: 768px) {
        .medical-title { font-size: 1.0rem; }
        .medical-logo-icon { font-size: 1.5rem; }
        .role-btn span { display: none; } /* Hide text on small screens */
        .role-btn { padding: 8px; border-radius: 50%; width: 35px; height: 35px; justify-content: center; }
        .role-btn i { margin: 0; }
    }
    
    /* Fixes for Queue/Symptom/Booking in Dark Mode */
    body.dark-mode #ticket-view { background-color: #2d2d2d !important; color: white !important; border: 1px solid #444; padding: 20px; border-radius: 15px; }
    body.dark-mode #result-box { background-color: #2d2d2d !important; color: white !important; border-color: #444 !important; }
    body.dark-mode input[type="date"]::-webkit-calendar-picker-indicator,
    body.dark-mode input[type="time"]::-webkit-calendar-picker-indicator { filter: invert(1); }
    
    body.clean-mode #ticket-view { background-color: #000 !important; color: white !important; border: 1px solid white; padding: 20px; border-radius: 15px; }
    body.clean-mode #result-box { background-color: #000 !important; color: white !important; border: 1px solid white !important; }
    body.clean-mode input[type="date"]::-webkit-calendar-picker-indicator,
    body.clean-mode input[type="time"]::-webkit-calendar-picker-indicator { filter: invert(1); }

    /* Login Password Icon */
    body.dark-mode #login-eye-icon { color: white !important; }

    /* Close Button Visibility Fix */
    body.dark-mode .login-modal-box > button,
    body.clean-mode .login-modal-box > button { color: white !important; }

    body.dark-mode .btn-close,
    body.clean-mode .btn-close { filter: invert(1) grayscale(100%) brightness(200%); }
</style>

<div class="medical-top-bar">
    <div class="medical-logo-area" {% if role == 'doctor' %}onclick="openIconGallery()"{% endif %} title="Lihat Semua Fitur" style="cursor: {% if role == 'doctor' %}pointer{% else %}default{% endif %};">
        <i class="fas fa-clinic-medical medical-logo-icon"></i>
    </div>
    
    <div class="medical-title">{{ page_title }}</div>
    
    <div class="role-btn-group">
        <div class="theme-switch-wrapper" style="position:relative; display:inline-block;">
            <button onclick="toggleThemeMenu()" class="role-btn" style="background: #34495e; color: white;" title="Ganti Tema">
                <i id="theme-main-icon" class="fas fa-palette"></i> <span id="theme-text">Tema</span>
            </button>
            <div id="theme-menu-dropdown" style="display:none; position:absolute; top:110%; left:50%; transform:translateX(-50%); background:white; border-radius:10px; box-shadow:0 5px 15px rgba(0,0,0,0.2); overflow:hidden; z-index:2000; min-width:120px; border:1px solid #eee;">
                <button onclick="setTheme('light')" style="width:100%; text-align:left; padding:10px 15px; border:none; background:white; cursor:pointer; display:flex; align-items:center; gap:10px; color:#333; font-weight:bold; font-size:0.8rem; border-bottom:1px solid #f0f0f0;">
                    <i class="fas fa-sun text-warning" style="width:20px; text-align:center;"></i> Light
                </button>
                <button onclick="setTheme('dark')" style="width:100%; text-align:left; padding:10px 15px; border:none; background:white; cursor:pointer; display:flex; align-items:center; gap:10px; color:#333; font-weight:bold; font-size:0.8rem; border-bottom:1px solid #f0f0f0;">
                    <i class="fas fa-moon text-dark" style="width:20px; text-align:center;"></i> Dark
                </button>
                <button onclick="setTheme('clean')" style="width:100%; text-align:left; padding:10px 15px; border:none; background:white; cursor:pointer; display:flex; align-items:center; gap:10px; color:#333; font-weight:bold; font-size:0.8rem;">
                    <i class="fas fa-sparkles" style="color:#FF6D00; width:20px; text-align:center;"></i> Clean
                </button>
            </div>
        </div>
        <a href="/logout" class="role-btn role-btn-pasien" title="Mode Pasien">
            <i class="fas fa-user"></i> <span>Pasien</span>
        </a>
        <button onclick="openLogin('admin')" class="role-btn role-btn-admin" title="Login Admin">
            <i class="fas fa-user-cog"></i> <span>Admin</span>
        </button>
        <button onclick="openLogin('dokter')" class="role-btn role-btn-dokter" title="Login Dokter">
            <i class="fas fa-user-md"></i> <span>Dokter</span>
        </button>
    </div>
    
    <div class="medical-split-border"></div>
</div>

<div class="medical-horizontal-menu">
    {% for item in menu_items %}
        {% if role in item.roles %}
            {% if item.route == '/profil-klinik' %}
            <a href="javascript:void(0)" onclick="document.getElementById('devInfoModal').style.display='flex'; return false;" class="feature-btn">
                <i class="{{ item.icon }}"></i>
                <span>{{ item.label }}</span>
            </a>
            {% else %}
            <a href="{{ item.route }}" class="feature-btn">
                <i class="{{ item.icon }}"></i>
                <span>{{ item.label }}</span>
            </a>
            {% endif %}
        {% endif %}
    {% endfor %}
</div>

<!-- Login Modal -->
<div id="loginModal" class="login-modal-overlay">
    <div class="login-modal-box">
        <button type="button" onclick="closeLogin()" style="position:absolute; top:10px; right:15px; border:none; background:none; font-size:1.2rem; cursor:pointer;">&times;</button>
        <h4 id="loginTitle" class="text-center mb-4 fw-bold">Login</h4>
        <form action="/login" method="POST">
            <div class="mb-3">
                <div class="input-group">
                    <span class="input-group-text bg-light"><i class="fas fa-user"></i></span>
                    <input type="text" name="userid" id="loginUser" class="form-control" placeholder="Username" required>
                </div>
            </div>
            <div class="mb-4">
                 <div class="input-group">
                    <span class="input-group-text bg-light"><i class="fas fa-lock"></i></span>
                    <input type="password" name="password" id="loginPass" class="form-control" placeholder="Password" required>
                    <button class="btn btn-outline-secondary" type="button" onclick="toggleLoginPass()">
                        <i class="fas fa-eye" id="login-eye-icon"></i>
                    </button>
                </div>
            </div>
            <button type="submit" class="btn btn-primary w-100 fw-bold py-2 rounded-pill">MASUK SISTEM</button>
        </form>
    </div>
</div>

<!-- Icon Gallery Modal -->
<div id="iconGalleryModal" class="login-modal-overlay" style="display:none; z-index: 11000;">
    <div class="login-modal-box" style="width: 95%; max-width: 900px; padding: 30px; max-height: 90vh; overflow-y: auto;">
        <button type="button" onclick="document.getElementById('iconGalleryModal').style.display='none'" style="position:absolute; top:15px; right:20px; border:none; background:none; font-size:1.5rem; cursor:pointer;">&times;</button>
        <h4 class="text-center mb-4 fw-bold text-dark" style="letter-spacing: 1px;">SEMUA FITUR & LAYANAN</h4>
        
        <style>
            .gallery-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; }
            @media(max-width: 500px) { .gallery-grid { gap: 8px; } }
        </style>
        
        <div class="gallery-grid">
            {% for item in menu_items %}
            <a href="{{ item.route }}" class="feature-btn" style="width: 100%; height: auto; min-height: 100px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border: 1px solid #eee;">
                <i class="{{ item.icon }}" style="font-size: 2rem; margin-bottom: 10px;"></i>
                <span style="font-size: 0.75rem;">{{ item.label }}</span>
            </a>
            {% endfor %}
        </div>
        
        <div class="text-center mt-4">
            <button class="btn btn-secondary btn-sm rounded-pill px-4" onclick="document.getElementById('iconGalleryModal').style.display='none'">Tutup Jendela</button>
        </div>
    </div>
</div>

<script>
function openIconGallery() {
    document.getElementById('iconGalleryModal').style.display = 'flex';
}

function toggleThemeMenu() {
    const menu = document.getElementById('theme-menu-dropdown');
    menu.style.display = (menu.style.display === 'block') ? 'none' : 'block';
}

window.addEventListener('click', function(e) {
    const wrapper = document.querySelector('.theme-switch-wrapper');
    if (wrapper && !wrapper.contains(e.target)) {
        document.getElementById('theme-menu-dropdown').style.display = 'none';
    }
});

function setTheme(mode) {
    const body = document.body;
    body.classList.remove('dark-mode', 'clean-mode');
    
    if (mode === 'dark') {
        body.classList.add('dark-mode');
    } else if (mode === 'clean') {
        body.classList.add('clean-mode');
    }
    
    localStorage.setItem('theme', mode);
    document.getElementById('theme-menu-dropdown').style.display = 'none';
}

function toggleLoginPass() {
    const x = document.getElementById("loginPass");
    const icon = document.getElementById("login-eye-icon");
    if (x.type === "password") {
        x.type = "text";
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
    } else {
        x.type = "password";
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
    }
}

document.addEventListener("DOMContentLoaded", function() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
});
</script>

<!-- Bottom Navigation for Patients -->
{% if role == 'patient' %}
<style>
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-top: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 -5px 20px rgba(0,0,0,0.1);
        display: flex;
        justify-content: space-around;
        padding: 10px 0;
        z-index: 9999;
        padding-bottom: max(10px, env(safe-area-inset-bottom));
    }
    .nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        color: #7f8c8d;
        text-decoration: none;
        font-size: 0.75rem;
        font-weight: 700;
        transition: 0.3s;
        cursor: pointer;
        width: 33%;
    }
    .nav-item i {
        font-size: 1.4rem;
        margin-bottom: 4px;
        transition: 0.3s;
    }
    .nav-item:hover, .nav-item:active {
        color: #2ecc71;
        transform: translateY(-2px);
    }
    .nav-item:hover i {
        transform: scale(1.1);
    }
    
    /* Hard Card Style */
    .hard-card-wrapper {
        background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
        border-radius: 15px;
        padding: 20px;
        color: white;
        box-shadow: 0 10px 25px rgba(46, 204, 113, 0.4);
        position: relative;
        overflow: hidden;
        min-height: 200px;
    }
    .hard-card-wrapper::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.2) 0%, transparent 60%);
        transform: rotate(30deg);
        pointer-events: none;
    }
    .hc-chip {
        width: 40px; height: 30px;
        background: linear-gradient(135deg, #f1c40f 0%, #f39c12 100%);
        border-radius: 5px;
        margin-bottom: 15px;
        position: relative;
        overflow: hidden;
    }
    .hc-chip::after {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        border: 1px solid rgba(0,0,0,0.2);
        border-radius: 5px;
        background: repeating-linear-gradient(90deg, transparent, transparent 5px, rgba(0,0,0,0.1) 5px, rgba(0,0,0,0.1) 6px);
    }
    
    /* Game Canvas */
    #gameCanvas {
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        cursor: pointer;
        touch-action: none;
    }
</style>

<div class="bottom-nav">
    <div class="nav-item" onclick="openMyCard()">
        <i class="fas fa-id-card"></i>
        <span>KARTU SAYA</span>
    </div>
    <div class="nav-item" onclick="openMyLab()">
        <i class="fas fa-file-medical-alt"></i>
        <span>HASIL LAB</span>
    </div>
    <div class="nav-item" onclick="openGame()">
        <i class="fas fa-gamepad"></i>
        <span>GAME</span>
    </div>
</div>

<!-- My Card Modal -->
<div id="myCardModal" class="login-modal-overlay">
    <div class="login-modal-box" style="width: 95%; max-width: 450px; max-height: 85vh; overflow-y: auto;">
        <button type="button" onclick="document.getElementById('myCardModal').style.display='none'" style="position:sticky; top:0; right:0; float:right; border:none; background:none; font-size:1.5rem; cursor:pointer; z-index: 100;">&times;</button>
        <h4 class="text-center mb-4 fw-bold text-success" style="margin-top:10px;">Kartu Pasien Digital</h4>
        
        <div id="card-login-step">
            <p class="text-center text-muted small mb-3">Masukkan No. WhatsApp untuk melihat kartu Anda.</p>
            <div class="input-group mb-3">
                <span class="input-group-text bg-white"><i class="fab fa-whatsapp text-success"></i></span>
                <input type="tel" id="card-phone" class="form-control" placeholder="08..." onkeypress="if(event.keyCode==13) fetchMyCard()">
            </div>
            <button class="btn btn-success w-100 fw-bold rounded-pill" onclick="fetchMyCard()">LIHAT KARTU</button>
        </div>
        
        <div id="card-display-step" style="display:none;">
            <div class="hard-card-wrapper">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="hc-chip"></div>
                    <i class="fas fa-hospital-alt fa-2x rgba-white-5"></i>
                </div>
                <h5 class="fw-bold mb-0 text-uppercase" id="hc-name">NAMA PASIEN</h5>
                <p class="small mb-3 opacity-75" id="hc-phone">08xxx</p>
                
                <div class="row g-2 small">
                    <div class="col-6">
                        <span class="d-block opacity-75" style="font-size:0.6rem">STATUS</span>
                        <strong id="hc-status">DONE</strong>
                    </div>
                    <div class="col-6 text-end">
                        <span class="d-block opacity-75" style="font-size:0.6rem">TANGGAL</span>
                        <strong id="hc-date">27 JAN</strong>
                    </div>
                </div>
            </div>
            
            <div class="mt-3">
                <ul class="list-group list-group-flush small bg-transparent">
                    <li class="list-group-item bg-transparent d-flex justify-content-between px-0">
                        <span class="text-muted">Nama:</span> <strong id="d-name">...</strong>
                    </li>
                    <li class="list-group-item bg-transparent d-flex justify-content-between px-0">
                        <span class="text-muted">HP:</span> <strong id="d-phone">...</strong>
                    </li>
                    <li class="list-group-item bg-transparent d-flex justify-content-between px-0">
                        <span class="text-muted">STATUS:</span> <span class="badge bg-success" id="d-status">...</span>
                    </li>
                    <li class="list-group-item bg-transparent px-0">
                         <div class="d-flex justify-content-between mb-1">
                             <span class="text-muted">Masuk (In):</span> <strong id="d-in">...</strong>
                         </div>
                         <div class="d-flex justify-content-between">
                             <span class="text-muted">Keluar (Out):</span> <strong id="d-out">...</strong>
                         </div>
                    </li>
                    <li class="list-group-item bg-transparent px-0">
                        <strong class="d-block text-warning mb-1"><i class="fas fa-comment-medical me-2"></i>Keluhan:</strong>
                        <div id="d-complaint" class="fw-bold text-dark">...</div>
                    </li>
                    <li class="list-group-item bg-transparent px-0">
                        <strong class="d-block text-info mb-1"><i class="fas fa-stethoscope me-2"></i>Diagnosa:</strong>
                        <div id="d-diag" class="fw-bold text-dark">...</div>
                    </li>
                    <li class="list-group-item bg-transparent px-0">
                        <strong class="d-block text-danger mb-1"><i class="fas fa-pills me-2"></i>Resep Obat:</strong>
                        <div id="d-presc" class="fw-bold text-dark">...</div>
                    </li>
                     <li class="list-group-item bg-transparent px-0">
                        <strong class="d-block text-success mb-1"><i class="fas fa-user-md me-2"></i>Tindakan:</strong>
                        <div id="d-action" class="fw-bold text-dark">...</div>
                    </li>
                </ul>
            </div>
            
            <button class="btn btn-outline-secondary btn-sm w-100 mt-3" onclick="resetCardView()">Cari Nomor Lain</button>
        </div>
    </div>
</div>

<!-- My Lab Modal -->
<div id="myLabModal" class="login-modal-overlay">
    <div class="login-modal-box" style="width: 350px;">
        <button type="button" onclick="document.getElementById('myLabModal').style.display='none'" style="position:absolute; top:10px; right:15px; border:none; background:none; font-size:1.2rem; cursor:pointer;">&times;</button>
        <h4 class="text-center mb-4 fw-bold text-primary">Hasil Lab Digital</h4>
        
        <div id="lab-login-step">
            <div class="input-group mb-3">
                <span class="input-group-text bg-white"><i class="fab fa-whatsapp text-primary"></i></span>
                <input type="tel" id="lab-phone" class="form-control" placeholder="No. WhatsApp..." onkeypress="if(event.keyCode==13) fetchMyLab()">
            </div>
            <button class="btn btn-primary w-100 fw-bold rounded-pill" onclick="fetchMyLab()">CARI HASIL</button>
        </div>
        
        <div id="lab-list-step" style="display:none;">
            <div id="lab-results-container" style="max-height: 300px; overflow-y: auto;"></div>
            <button class="btn btn-outline-secondary btn-sm w-100 mt-3" onclick="resetLabView()">Kembali</button>
        </div>
    </div>
</div>

<!-- Game Menu Modal -->
<div id="gameMenuModal" class="login-modal-overlay" style="display:none; z-index: 10000;">
    <div class="login-modal-box" style="width: 350px; text-align: center; background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(15px);">
        <button type="button" onclick="document.getElementById('gameMenuModal').style.display='none'" style="position:absolute; top:10px; right:15px; border:none; background:none; font-size:1.2rem; cursor:pointer;">&times;</button>
        <h4 class="mb-4 fw-bold text-success" style="letter-spacing: 1px;">PILIH PERMAINAN</h4>
        
        <div class="d-grid gap-3">
            <button onclick="openPuzzleGame()" class="btn btn-outline-success btn-lg fw-bold py-3 rounded-pill shadow-sm" style="display:flex; align-items:center; justify-content:center; gap:10px;">
                <i class="fas fa-puzzle-piece fa-lg"></i> Puzzle Gambar
            </button>
            <button onclick="openDevPopup()" class="btn btn-outline-info btn-lg fw-bold py-3 rounded-pill shadow-sm" style="display:flex; align-items:center; justify-content:center; gap:10px;">
                <i class="fas fa-tooth fa-lg"></i> Perawatan Gigi
            </button>
        </div>
    </div>
</div>

<!-- Development Info Modal -->
<div id="devInfoModal" class="login-modal-overlay" style="display:none; z-index: 12000;">
    <div style="background: rgba(255, 255, 255, 0.65); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 2px solid rgba(255, 255, 255, 0.8); box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37); border-radius: 25px; padding: 40px 30px; text-align: center; max-width: 400px; width: 85%; animation: slideIn 0.4s ease-out;">
        <div class="mb-3" style="font-size: 3.5rem; color: #ffb703; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));">
            <i class="fas fa-tools"></i>
        </div>
        <h3 class="fw-bold mb-3" style="color: #2c3e50; letter-spacing: 0.5px;">TAHAP PENGEMBANGAN</h3>
        <p class="mb-4 fw-bold" style="font-size: 1.1rem; line-height: 1.6; color: #444;">
            Mohon maaf, fitur ini <strong>Masih dalam Tahap Pengembangan</strong>.<br>Kami sedang menyiapkannya agar lebih sempurna untuk Anda.
        </p>
        <button onclick="closeDevPopup()" class="btn btn-dark rounded-pill px-5 py-2 fw-bold shadow-lg" style="transition: all 0.3s; letter-spacing: 1px;">
            OKE, MENGERTI
        </button>
    </div>
</div>

<!-- Dental Game Modal -->
<div id="dentalModal" class="login-modal-overlay" style="display:none; z-index: 10001;">
    <style>
        .hard-card-glass-enhanced {
            background: rgba(255, 255, 255, 0.25);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border: 2px solid rgba(255, 255, 255, 0.5);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.25);
            border-radius: 25px;
            padding: 25px;
            width: 95%; max-width: 1200px; /* Wider for desktop split */
            height: auto; max-height: 95vh;
            overflow-y: auto;
            display: flex; flex-direction: column;
            position: relative;
        }
        
        /* Layout Container */
        .dental-layout {
            display: flex;
            flex-direction: column; /* Mobile Default */
            gap: 20px;
            flex: 1;
        }
        
        .game-area {
            flex: 1;
            display: flex; flex-direction: column; align-items: center;
        }
        
        #dentalContainer {
            position: relative;
            width: 100%;
            max-width: 500px; /* Keep game size controlled */
            aspect-ratio: 1 / 1; 
            border-radius: 15px; 
            overflow: hidden;
            margin-bottom: 20px;
            background: #fff;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            cursor: default; 
            border: 4px solid rgba(255,255,255,0.8);
        }
        
        #dentalContainer img {
            width: 100%; height: 100%; object-fit: cover;
            position: absolute; top: 0; left: 0; z-index: 1;
            border-radius: 15px; 
        }
        #dentalCanvas {
            position: absolute; top: 0; left: 0; z-index: 2;
            width: 100%; height: 100%;
            touch-action: none;
            border-radius: 15px; 
        }
        
        .tool-btn {
            background: rgba(255, 255, 255, 0.9); 
            border: 1px solid rgba(0,0,0,0.05);
            padding: 12px 25px; border-radius: 50px;
            font-weight: 800; color: #444; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: 0.3s; cursor: pointer; display: flex; align-items: center; gap: 10px;
            backdrop-filter: blur(5px);
        }
        .tool-btn:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.15); }
        .tool-btn.active-tool {
            background: #3498db; color: white; transform: scale(1.05);
            box-shadow: 0 0 20px rgba(52, 152, 219, 0.6);
            border-color: #3498db;
        }
        
        /* Custom Brush Cursor */
        #customBrushCursor {
            position: fixed;
            width: 50px; 
            height: auto;
            pointer-events: none;
            z-index: 9999;
            display: none;
            transform: translate(0, 0); 
        }
        
        /* Dev Panel Styling */
        #devPanel {
            display: none; /* Hidden by default */
            background: rgba(0, 0, 0, 0.85); 
            color: white;
            padding: 20px; 
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.2);
            flex-direction: column;
            gap: 15px;
        }
        .dev-active .dental-layout {
            /* Applied when dev mode is active */
        }
        
        /* Responsive Desktop */
        @media (min-width: 992px) {
            .dev-active .dental-layout {
                flex-direction: row; /* Side by side on Desktop */
                align-items: flex-start;
            }
            .dev-active #devPanel {
                width: 350px;
                display: flex;
            }
        }
        @media (max-width: 991px) {
             /* Mobile: Column remains default */
             .dev-active #devPanel {
                 width: 100%;
                 display: flex;
             }
        }

        .dev-row { display: flex; gap: 10px; align-items: center; justify-content: space-between; flex-wrap: wrap; }
        .dev-input { width: 60px; padding: 5px; border-radius: 5px; border:none; text-align: center; font-weight: bold; }
        
        .dev-transparent { opacity: 0.5; filter: blur(2px); }
        
        .resize-handle {
            position: absolute; width: 15px; height: 15px; background: #FFD700;
            border: 2px solid white; z-index: 50; display: none; border-radius: 50%; box-shadow: 0 0 5px black;
        }
        /* Handle Positions */
        .handle-nw { top: -7px; left: -7px; cursor: nw-resize; }
        .handle-n { top: -7px; left: 50%; transform: translateX(-50%); cursor: n-resize; }
        .handle-ne { top: -7px; right: -7px; cursor: ne-resize; }
        .handle-e { top: 50%; right: -7px; transform: translateY(-50%); cursor: e-resize; }
        .handle-se { bottom: -7px; right: -7px; cursor: se-resize; }
        .handle-s { bottom: -7px; left: 50%; transform: translateX(-50%); cursor: s-resize; }
        .handle-sw { bottom: -7px; left: -7px; cursor: sw-resize; }
        .handle-w { top: 50%; left: -7px; transform: translateY(-50%); cursor: w-resize; }
        
        #calibrationOverlay {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            display: none; justify-content: center; align-items: center;
            z-index: 60; pointer-events: none;
        }
        #fakeCursor {
            width: 30px; height: 30px; border: 3px solid #e74c3c; border-radius: 50%;
            background: rgba(231, 76, 60, 0.2); position: absolute; pointer-events: none;
        }
        #fakeCursor::after {
            content: '+'; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #e74c3c; font-weight: 900; font-size: 20px;
        }
    </style>

    <div class="hard-card-glass-enhanced" id="dentalMainWrapper">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h3 class="fw-bold mb-0 text-white" style="letter-spacing: 1px;"><i class="fas fa-tooth me-2"></i> PERAWATAN GIGI</h3>
            <div>
                <button class="btn btn-dark rounded-pill me-2 fw-bold px-3 shadow-sm" onclick="enableDevMode()" id="devToggleBtn">
                    <i class="fas fa-cog me-2"></i> DEV MODE
                </button>
                <button onclick="document.getElementById('dentalModal').style.display='none'" class="close-btn" style="color:white; font-size: 2rem;">&times;</button>
            </div>
        </div>
        
        <div class="dental-layout">
            <div class="game-area">
                <div id="dentalContainer" onmousemove="moveCustomCursor(event)" onmouseleave="hideCustomCursor()">
                    <img src="{{ url_for('static', filename='gigibersih.png') }}" id="dentalCleanImg" onerror="this.style.background='#eee'">
                    <canvas id="dentalCanvas"></canvas>
                    
                    <div id="resizeHandles">
                        <div class="resize-handle handle-nw" onmousedown="startResize(event, 'nw')"></div>
                        <div class="resize-handle handle-n" onmousedown="startResize(event, 'n')"></div>
                        <div class="resize-handle handle-ne" onmousedown="startResize(event, 'ne')"></div>
                        <div class="resize-handle handle-e" onmousedown="startResize(event, 'e')"></div>
                        <div class="resize-handle handle-se" onmousedown="startResize(event, 'se')"></div>
                        <div class="resize-handle handle-s" onmousedown="startResize(event, 's')"></div>
                        <div class="resize-handle handle-sw" onmousedown="startResize(event, 'sw')"></div>
                        <div class="resize-handle handle-w" onmousedown="startResize(event, 'w')"></div>
                    </div>
                    
                    <div id="calibrationOverlay">
                        <div id="fakeCursor"></div>
                    </div>
                    
                    <img src="{{ url_for('static', filename='sikatgigi.png') }}" id="customBrushCursor">
                </div>
                
                <div class="d-flex justify-content-center gap-3 w-100">
                    <button class="tool-btn" id="btn-brush" onclick="toggleBrush()">
                        <i class="fas fa-magic text-info"></i> Sikat Gigi (Busa)
                    </button>
                    <button class="tool-btn" onclick="resetDentalGame()">
                        <i class="fas fa-redo text-danger"></i> Reset
                    </button>
                </div>
            </div>
            
            <!-- Dev Panel -->
            <div id="devPanel">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="text-warning fw-bold mb-0">DEVELOPER PANEL</h5>
                    <button class="btn btn-sm btn-outline-light rounded-pill px-3" onclick="closeDevMode()">EXIT DEV</button>
                </div>
                
                <div class="p-3 rounded bg-dark border border-secondary mb-2">
                    <h6 class="text-white-50 text-uppercase small fw-bold mb-3">1. Select Layer to Resize</h6>
                    <div class="btn-group w-100" role="group">
                        <input type="radio" class="btn-check" name="targetLayer" id="selClean" autocomplete="off" checked onchange="selectLayer('dentalCleanImg')">
                        <label class="btn btn-outline-light fw-bold" for="selClean">CLEAN IMAGE</label>
                        <input type="radio" class="btn-check" name="targetLayer" id="selDirty" autocomplete="off" onchange="selectLayer('dentalCanvas')">
                        <label class="btn btn-outline-light fw-bold" for="selDirty">DIRTY CANVAS</label>
                    </div>
                </div>
                
                <div id="resizeInputs">
                    <div class="p-3 rounded bg-dark border border-secondary mb-2">
                        <h6 class="text-white-50 text-uppercase small fw-bold mb-3">2. Manual Dimensions (%)</h6>
                        <div class="dev-row mb-2">
                            <span>WIDTH</span> <input type="number" id="inp-w" class="dev-input" onchange="manualResize('width', this.value)">
                            <span>HEIGHT</span> <input type="number" id="inp-h" class="dev-input" onchange="manualResize('height', this.value)">
                        </div>
                        <div class="dev-row">
                            <span>LEFT (X)</span> <input type="number" id="inp-x" class="dev-input" onchange="manualResize('left', this.value)">
                            <span>TOP (Y)</span> <input type="number" id="inp-y" class="dev-input" onchange="manualResize('top', this.value)">
                        </div>
                    </div>
                </div>
                
                <div id="calibrationControls" style="display:none;" class="p-3 rounded bg-dark border border-warning mb-2 text-center">
                    <h6 class="text-warning fw-bold mb-2">CALIBRATION MODE</h6>
                    <p class="small text-light mb-3">Drag the toothbrush image to match the red target point.</p>
                    <button class="btn btn-success fw-bold w-100 py-2 rounded-pill" onclick="fixCalibration()">FIX & SAVE POSITION</button>
                </div>
                
                <div class="d-grid gap-2 mt-2">
                    <button class="btn btn-outline-warning fw-bold py-2" onclick="toggleCalibration()" id="calibBtn">
                        <i class="fas fa-crosshairs me-2"></i> CALIBRATE CURSOR
                    </button>
                    <button class="btn btn-primary fw-bold py-3 shadow" onclick="saveSettings()">
                        <i class="fas fa-save me-2"></i> SAVE CHANGES PERMANENTLY
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Puzzle Game Modal -->
<div id="gameModal" class="login-modal-overlay" style="display:none; z-index: 10001;">
    <style>
        .hard-card-glass {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.4);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            border-radius: 20px;
            padding: 20px;
            width: 95%; max-width: 450px;
            height: 85vh;
            display: flex; flex-direction: column;
            position: relative;
            overflow: hidden;
            transition: all 0.5s;
        }
        .game-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; color: #333; }
        .game-title { margin: 0; font-weight: 800; font-size: 1.2rem; text-shadow: 0 1px 2px rgba(255,255,255,0.5); color: #fff; }
        .close-btn { background: none; border: none; color: #fff; font-size: 2rem; cursor: pointer; line-height: 1;}

        .game-controls { margin-bottom: 10px; display: flex; flex-direction: column; gap: 8px; }
        .level-buttons { display: flex; gap: 5px; justify-content: center; }
        .btn-level { flex: 1; padding: 8px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.5); background: rgba(255,255,255,0.2); color: white; font-weight: bold; cursor: pointer; transition: 0.3s; font-size: 0.8rem; }
        .btn-level:hover, .btn-level.active { background: #FFD700; color: black; border-color: #FFD700; box-shadow: 0 0 10px rgba(255, 215, 0, 0.5); }

        .image-controls { display: flex; gap: 5px; justify-content: center; }
        .btn-control { padding: 6px 12px; border-radius: 15px; border: none; background: white; color: #333; font-weight: bold; cursor: pointer; font-size: 0.75rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .btn-control:hover { transform: translateY(-2px); }

        .puzzle-board {
            flex: 1;
            background: rgba(0,0,0,0.2);
            border-radius: 15px;
            position: relative;
            overflow: hidden;
            margin: 0 auto;
            width: 100%;
            display: grid;
            gap: 1px;
            border: 2px solid rgba(255,255,255,0.3);
        }

        .puzzle-piece {
            background-repeat: no-repeat;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            position: relative;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .puzzle-piece.selected {
            z-index: 10;
            box-shadow: 0 0 15px #FFD700;
            transform: scale(0.92);
            border: 2px solid #FFD700;
        }

        .win-overlay {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(135deg, rgba(255,215,0,0.6), rgba(255,255,255,0.6));
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            z-index: 20;
            animation: fadeIn 0.5s;
            backdrop-filter: blur(5px);
        }
        .win-message {
            font-size: 2rem; font-weight: 900; color: white; 
            text-shadow: 0 4px 10px rgba(0,0,0,0.5);
            background: rgba(0,0,0,0.5); padding: 20px; border-radius: 15px;
            margin-bottom: 20px;
        }
        
        .shiny-win {
            box-shadow: 0 0 50px 20px rgba(255, 255, 255, 0.8), inset 0 0 50px 20px rgba(255, 215, 0, 0.5);
            border: 2px solid rgba(255,255,255,0.9);
        }
    </style>

    <div class="hard-card-glass" id="gameContainer">
        <div class="game-header">
            <h3 class="game-title">PUZZLE GAME</h3>
            <button onclick="document.getElementById('gameModal').style.display='none'" class="close-btn">&times;</button>
        </div>
        
        <div class="game-controls">
            <div class="level-buttons">
                <button onclick="initPuzzle(1)" class="btn-level" id="btn-lvl-1">LVL 1 (3x2)</button>
                <button onclick="initPuzzle(2)" class="btn-level" id="btn-lvl-2">LVL 2 (6x2)</button>
                <button onclick="initPuzzle(3)" class="btn-level" id="btn-lvl-3">LVL 3 (9x2)</button>
            </div>
            <div class="image-controls">
                <input type="file" id="uploadGameImg" accept="image/*" onchange="handleGameImageUpload(this)" hidden>
                <button onclick="document.getElementById('uploadGameImg').click()" class="btn-control"><i class="fas fa-camera text-primary"></i> Upload Foto</button>
                <button onclick="resetGameImage()" class="btn-control"><i class="fas fa-undo text-danger"></i> Reset Default</button>
            </div>
        </div>

        <div id="puzzleBoard" class="puzzle-board"></div>
        
        <div id="winOverlay" class="win-overlay" style="display:none;">
            <div class="win-message">SELESAI! 🎉</div>
            <button onclick="initPuzzle(currentLevel)" class="btn btn-light fw-bold rounded-pill shadow">Main Lagi</button>
        </div>
    </div>
</div>

<script>
    let currentLevel = 1;
    let puzzleImage = "{{ url_for('static', filename='monalisa.png') }}";
    let gridState = []; // Array of piece IDs
    let selectedPiece = null;
    let rows = 3, cols = 2;

    function openGame() {
        document.getElementById('gameMenuModal').style.display = 'flex';
    }

    function openPuzzleGame() {
        document.getElementById('gameMenuModal').style.display = 'none';
        document.getElementById('gameModal').style.display = 'flex';
        initPuzzle(currentLevel);
    }

    function openDevPopup() {
        document.getElementById('gameMenuModal').style.display = 'none';
        document.getElementById('devInfoModal').style.display = 'flex';
    }
    
    function closeDevPopup() {
        document.getElementById('devInfoModal').style.display = 'none';
        document.getElementById('gameMenuModal').style.display = 'flex';
    }

    // --- DENTAL GAME JS ---
    let dentalCanvas, dentalCtx;
    let isDrawing = false;
    let isBrushActive = false;
    let cursorOffsetX = -25; // Default center adjustment (50px width / 2)
    let cursorOffsetY = -25; 
    let isDevMode = false;
    
    // Resize Vars
    let selectedLayerId = 'dentalCleanImg';
    let isResizing = false;
    let resizeDir = '';
    let startX, startY, startW, startH, startTop, startLeft;
    
    // Calibration Vars
    let isCalibrating = false;
    let isDraggingBrush = false;
    
    function openDentalGame() {
        document.getElementById('gameMenuModal').style.display = 'none';
        document.getElementById('dentalModal').style.display = 'flex';
        
        // Reset state
        isBrushActive = false;
        document.getElementById('btn-brush').classList.remove('active-tool');
        document.getElementById('customBrushCursor').style.display = 'none';
        document.getElementById('dentalCanvas').style.cursor = 'default';
        
        setTimeout(initDentalGame, 100); 
    }

    function initDentalGame() {
        dentalCanvas = document.getElementById('dentalCanvas');
        dentalCtx = dentalCanvas.getContext('2d');
        const container = document.getElementById('dentalContainer');
        const imgDirty = new Image();
        
        // Match container
        dentalCanvas.width = container.clientWidth;
        dentalCanvas.height = container.clientHeight;
        
        imgDirty.onload = function() {
            dentalCtx.drawImage(imgDirty, 0, 0, dentalCanvas.width, dentalCanvas.height);
        };
        imgDirty.src = "{{ url_for('static', filename='gigikotor.png') }}";
        
        // Events
        dentalCanvas.onmousedown = startDraw;
        dentalCanvas.onmousemove = draw;
        dentalCanvas.onmouseup = stopDraw;
        dentalCanvas.onmouseleave = stopDraw;
        
        dentalCanvas.addEventListener('touchstart', startDraw, {passive: false});
        dentalCanvas.addEventListener('touchmove', draw, {passive: false});
        dentalCanvas.addEventListener('touchend', stopDraw);
        
        // Global mouseup for resize stop
        window.addEventListener('mouseup', stopResize);
    }
    
    function toggleBrush() {
        if(isDevMode && isCalibrating) return; // Disable in calib mode
        isBrushActive = !isBrushActive;
        const btn = document.getElementById('btn-brush');
        const cursor = document.getElementById('customBrushCursor');
        const canvas = document.getElementById('dentalCanvas');
        
        if (isBrushActive) {
            btn.classList.add('active-tool');
            cursor.style.display = 'block';
            canvas.style.cursor = 'none'; 
        } else {
            btn.classList.remove('active-tool');
            cursor.style.display = 'none';
            canvas.style.cursor = 'default';
        }
    }
    
    function moveCustomCursor(e) {
        // Normal Gameplay
        if (isBrushActive && !isCalibrating) {
            const cursor = document.getElementById('customBrushCursor');
            let clientX = e.clientX;
            let clientY = e.clientY;
            if(e.type.includes('touch') && e.touches[0]) {
                clientX = e.touches[0].clientX;
                clientY = e.touches[0].clientY;
            }
            cursor.style.left = (clientX + cursorOffsetX) + 'px';
            cursor.style.top = (clientY + cursorOffsetY) + 'px';
        }
    }
    
    function hideCustomCursor() {
        if (!isBrushActive) return;
    }

    function getPos(e) {
        const rect = dentalCanvas.getBoundingClientRect();
        let clientX = e.clientX;
        let clientY = e.clientY;
        if(e.touches && e.touches.length > 0) {
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        }
        
        const scaleX = dentalCanvas.width / rect.width;
        const scaleY = dentalCanvas.height / rect.height;
        
        return {
            x: (clientX - rect.left) * scaleX,
            y: (clientY - rect.top) * scaleY
        };
    }
    
    function startDraw(e) {
        if (!isBrushActive || isResizing || isCalibrating) return;
        if(e.type === 'touchstart') e.preventDefault();
        isDrawing = true;
        draw(e);
    }
    
    function draw(e) {
        moveCustomCursor(e); 
        if(!isDrawing || !isBrushActive || isResizing) return;
        if(e.type === 'touchmove') e.preventDefault();
        
        const pos = getPos(e);
        const radius = 30; 
        
        dentalCtx.globalCompositeOperation = 'destination-out';
        dentalCtx.beginPath();
        dentalCtx.arc(pos.x, pos.y, radius, 0, Math.PI * 2, false);
        dentalCtx.fill();
    }
    
    function stopDraw() {
        isDrawing = false;
    }
    
    function resetDentalGame() {
        initDentalGame();
    }
    
    // --- DEVELOPER MODE & RESIZING ---
    function enableDevMode() {
        const id = prompt("Masukkan Developer ID:");
        if (id === 'developer') {
            const pw = prompt("Masukkan Password:");
            if (pw === 'd3v3l0p3r') {
                isDevMode = true;
                document.getElementById('devPanel').style.display = 'flex'; // Use flex for panel
                document.getElementById('dentalMainWrapper').classList.add('dev-active'); // Trigger layout change
                document.getElementById('devToggleBtn').style.display = 'none'; // Hide entry button
                document.getElementById('dentalCanvas').classList.add('dev-transparent');
                selectLayer(selectedLayerId); // Init handles
            } else {
                alert("Password Salah.");
            }
        } else {
            alert("ID Tidak Dikenal.");
        }
    }
    
    function closeDevMode() {
        isDevMode = false;
        document.getElementById('devPanel').style.display = 'none';
        document.getElementById('dentalMainWrapper').classList.remove('dev-active');
        document.getElementById('devToggleBtn').style.display = 'inline-block';
        document.getElementById('dentalCanvas').classList.remove('dev-transparent');
        document.getElementById('resizeHandles').style.display = 'none';
        if(isCalibrating) toggleCalibration(); // Ensure calibration mode is off
    }
    
    function saveSettings() {
        const clean = document.getElementById('dentalCleanImg');
        const canvas = document.getElementById('dentalCanvas');
        
        const config = {
            clean: {
                width: clean.style.width,
                height: clean.style.height,
                top: clean.style.top,
                left: clean.style.left
            },
            dirty: {
                width: canvas.style.width,
                height: canvas.style.height,
                top: canvas.style.top,
                left: canvas.style.left
            },
            cursor: {
                x: cursorOffsetX,
                y: cursorOffsetY
            }
        };
        
        fetch('/api/dental/settings', {
            method: 'POST', 
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(config)
        }).then(r => r.json()).then(res => {
            if(res.success) alert("Settings Saved Permanently!");
        });
    }
    
    function loadSettings() {
        fetch('/api/dental/settings').then(r => r.json()).then(config => {
            if(!config.clean) return; // No config saved yet
            
            const clean = document.getElementById('dentalCleanImg');
            const canvas = document.getElementById('dentalCanvas');
            
            if(config.clean) {
                clean.style.width = config.clean.width;
                clean.style.height = config.clean.height;
                clean.style.top = config.clean.top;
                clean.style.left = config.clean.left;
            }
            if(config.dirty) {
                canvas.style.width = config.dirty.width;
                canvas.style.height = config.dirty.height;
                canvas.style.top = config.dirty.top;
                canvas.style.left = config.dirty.left;
            }
            if(config.cursor) {
                cursorOffsetX = config.cursor.x;
                cursorOffsetY = config.cursor.y;
            }
            // Re-init handles if dev mode open? No, standard load
        });
    }
    
    function selectLayer(id) {
        selectedLayerId = id;
        if(!isDevMode) return;
        
        const el = document.getElementById(id);
        const handles = document.getElementById('resizeHandles');
        
        // Show handles
        handles.style.display = 'block';
        
        // Sync inputs
        document.getElementById('inp-w').value = parseFloat(el.style.width) || 100;
        document.getElementById('inp-h').value = parseFloat(el.style.height) || 100;
        document.getElementById('inp-x').value = parseFloat(el.style.left) || 0;
        document.getElementById('inp-y').value = parseFloat(el.style.top) || 0;
        
        // Update handles position to match target
        // Since targets are 100% of container by default, handles just fill container unless modified
        // Actually, handles are absolute in container. We should set them to match element logic?
        // Since we are resizing top/left/width/height percentages of element, 
        // the handles are hardcoded to container corners in CSS. 
        // NOTE: User asked to "drag points on image box". 
        // If images are same size as container, handles on container works.
        // If images are resized smaller, handles should follow.
        // Simplification: We rely on CSS handles on container for now, as images are usually fit.
        // If precise mapping needed, we'd move handles div. 
        // Given constraint, we'll keep handles on container edges but update logic.
    }
    
    function manualResize(prop, val) {
        const el = document.getElementById(selectedLayerId);
        el.style[prop] = val + '%';
    }
    
    function updateLayer(elementId, property, value) {
        // Legacy support
        const el = document.getElementById(elementId);
        if (el) el.style[property] = value;
    }

    function startResize(e, dir) {
        if(!isDevMode) return;
        e.preventDefault();
        isResizing = true;
        resizeDir = dir;
        
        const el = document.getElementById(selectedLayerId);
        const container = document.getElementById('dentalContainer');
        const cRect = container.getBoundingClientRect();
        
        // Get current values (in px relative to container)
        // If % is used, convert.
        startW = el.offsetWidth;
        startH = el.offsetHeight;
        startTop = el.offsetTop;
        startLeft = el.offsetLeft;
        startX = e.clientX;
        startY = e.clientY;
        
        window.addEventListener('mousemove', resizing);
    }
    
    function resizing(e) {
        if(!isResizing) return;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        const el = document.getElementById(selectedLayerId);
        const container = document.getElementById('dentalContainer');
        
        let newW = startW, newH = startH, newL = startLeft, newT = startTop;
        
        if (resizeDir.includes('e')) newW = startW + dx;
        if (resizeDir.includes('s')) newH = startH + dy;
        if (resizeDir.includes('w')) { newW = startW - dx; newL = startLeft + dx; }
        if (resizeDir.includes('n')) { newH = startH - dy; newT = startTop + dy; }
        
        // Convert to % for consistency
        const perW = (newW / container.offsetWidth) * 100;
        const perH = (newH / container.offsetHeight) * 100;
        const perL = (newL / container.offsetWidth) * 100;
        const perT = (newT / container.offsetHeight) * 100;
        
        el.style.width = perW + '%';
        el.style.height = perH + '%';
        el.style.left = perL + '%';
        el.style.top = perT + '%';
        
        // Update inputs
        document.getElementById('inp-w').value = Math.round(perW);
        document.getElementById('inp-h').value = Math.round(perH);
        document.getElementById('inp-x').value = Math.round(perL);
        document.getElementById('inp-y').value = Math.round(perT);
    }
    
    function stopResize() {
        if(isResizing) {
            isResizing = false;
            window.removeEventListener('mousemove', resizing);
        }
    }
    
    // --- CURSOR CALIBRATION ---
    function toggleCalibration() {
        isCalibrating = !isCalibrating;
        const overlay = document.getElementById('calibrationOverlay');
        const cursor = document.getElementById('customBrushCursor');
        const controls = document.getElementById('calibrationControls');
        const resizeInputs = document.getElementById('resizeInputs');
        
        if(isCalibrating) {
            overlay.style.display = 'flex'; // Center fake cursor
            controls.style.display = 'flex';
            resizeInputs.style.display = 'none';
            
            // Show brush, center it initially
            cursor.style.display = 'block';
            cursor.style.pointerEvents = 'auto'; // Enable dragging
            cursor.style.cursor = 'grab';
            
            // Center brush visually (reset transform to none to allow simple left/top)
            const rect = document.getElementById('dentalContainer').getBoundingClientRect();
            cursor.style.left = (rect.width/2) + 'px';
            cursor.style.top = (rect.height/2) + 'px';
            cursor.style.transform = 'translate(0, 0)';
            
            // Add drag listeners to cursor
            cursor.onmousedown = startDragBrush;
            window.addEventListener('mousemove', dragBrush);
            window.addEventListener('mouseup', stopDragBrush);
            
        } else {
            overlay.style.display = 'none';
            controls.style.display = 'none';
            resizeInputs.style.display = 'flex';
            
            // Reset brush
            cursor.style.display = 'none';
            cursor.style.pointerEvents = 'none';
            cursor.onmousedown = null;
            window.removeEventListener('mousemove', dragBrush);
            window.removeEventListener('mouseup', stopDragBrush);
        }
    }
    
    let brushDragStartX, brushDragStartY, brushStartLeft, brushStartTop;
    
    function startDragBrush(e) {
        e.preventDefault();
        isDraggingBrush = true;
        brushDragStartX = e.clientX;
        brushDragStartY = e.clientY;
        const cursor = document.getElementById('customBrushCursor');
        brushStartLeft = cursor.offsetLeft;
        brushStartTop = cursor.offsetTop;
    }
    
    function dragBrush(e) {
        if(!isDraggingBrush) return;
        const dx = e.clientX - brushDragStartX;
        const dy = e.clientY - brushDragStartY;
        const cursor = document.getElementById('customBrushCursor');
        cursor.style.left = (brushStartLeft + dx) + 'px';
        cursor.style.top = (brushStartTop + dy) + 'px';
    }
    
    function stopDragBrush() {
        isDraggingBrush = false;
    }
    
    function fixCalibration() {
        // Calculate offset
        // Fake cursor is at center of container
        const container = document.getElementById('dentalContainer');
        const cRect = container.getBoundingClientRect();
        const centerX = cRect.width / 2;
        const centerY = cRect.height / 2;
        
        const cursor = document.getElementById('customBrushCursor');
        const brushX = cursor.offsetLeft;
        const brushY = cursor.offsetTop;
        
        // Offset = BrushPos - CenterPos
        // When user mouse (clientX) is at pos, we want brush to be at clientX + offset
        // In calibration, Mouse is irrelevant, we aligned visual brush to visual center.
        // So offset is difference.
        cursorOffsetX = brushX - centerX;
        cursorOffsetY = brushY - centerY;
        
        alert(`Offset Saved: X=${cursorOffsetX}, Y=${cursorOffsetY}`);
        toggleCalibration(); // Exit calib mode
    }

    function initPuzzle(lvl) {
        currentLevel = lvl;
        
        // Reset UI
        document.querySelectorAll('.btn-level').forEach(b => b.classList.remove('active'));
        document.getElementById('btn-lvl-' + lvl).classList.add('active');
        document.getElementById('winOverlay').style.display = 'none';
        document.getElementById('gameContainer').classList.remove('shiny-win');
        
        // Config
        cols = 2;
        if (lvl === 1) rows = 3;
        else if (lvl === 2) rows = 6;
        else if (lvl === 3) rows = 9;
        
        // Generate Pieces
        const total = rows * cols;
        gridState = Array.from({length: total}, (_, i) => i);
        
        // Shuffle (Fisher-Yates)
        for (let i = gridState.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [gridState[i], gridState[j]] = [gridState[j], gridState[i]];
        }
        
        renderBoard();
    }

    function renderBoard() {
        const board = document.getElementById('puzzleBoard');
        board.innerHTML = '';
        board.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
        board.style.gridTemplateRows = `repeat(${rows}, 1fr)`;
        
        const bgWidth = cols * 100;
        const bgHeight = rows * 100;
        
        gridState.forEach((pieceId, index) => {
            const div = document.createElement('div');
            div.className = 'puzzle-piece';
            div.style.backgroundImage = `url('${puzzleImage}')`;
            div.style.backgroundSize = `${bgWidth}% ${bgHeight}%`;
            
            const correctRow = Math.floor(pieceId / cols);
            const correctCol = pieceId % cols;
            
            const xPct = cols > 1 ? (correctCol / (cols - 1)) * 100 : 0;
            const yPct = rows > 1 ? (correctRow / (rows - 1)) * 100 : 0;
            
            div.style.backgroundPosition = `${xPct}% ${yPct}%`;
            div.onclick = () => handlePieceClick(index);
            
            if (selectedPiece === index) div.classList.add('selected');
            
            board.appendChild(div);
        });
    }

    function handlePieceClick(index) {
        if (selectedPiece === null) {
            selectedPiece = index;
            renderBoard();
        } else {
            if (selectedPiece !== index) {
                // Swap
                [gridState[selectedPiece], gridState[index]] = [gridState[index], gridState[selectedPiece]];
                selectedPiece = null;
                renderBoard();
                checkWin();
            } else {
                selectedPiece = null;
                renderBoard();
            }
        }
    }

    function checkWin() {
        let won = true;
        for (let i = 0; i < gridState.length; i++) {
            if (gridState[i] !== i) {
                won = false;
                break;
            }
        }
        
        if (won) {
            document.getElementById('winOverlay').style.display = 'flex';
            document.getElementById('gameContainer').classList.add('shiny-win');
        }
    }

    function handleGameImageUpload(input) {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                puzzleImage = e.target.result;
                initPuzzle(currentLevel);
            };
            reader.readAsDataURL(input.files[0]);
        }
    }

    function resetGameImage() {
        puzzleImage = "{{ url_for('static', filename='monalisa.png') }}";
        initPuzzle(currentLevel);
    }
</script>

{% endif %}

<script>
    // Highlight active menu
    document.addEventListener("DOMContentLoaded", function() {
        const path = window.location.pathname;
        const buttons = document.querySelectorAll('.feature-btn');
        buttons.forEach(btn => {
            if(btn.getAttribute('href') === path || (path === '/' && btn.getAttribute('href') === '/antrean')) {
                btn.classList.add('active');
                // Scroll to active
                btn.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
            }
        });
    });

    function openLogin(role) {
        document.getElementById('loginModal').style.display = 'flex';
        const title = document.getElementById('loginTitle');
        const user = document.getElementById('loginUser');
        const pass = document.getElementById('loginPass');
        
        if(role === 'admin') {
            title.innerText = 'Login Admin';
            title.style.color = '#3498db';
            user.value = 'admin'; 
            pass.value = ''; 
        } else {
            title.innerText = 'Login Dokter';
            title.style.color = '#d35400';
            user.value = 'dokter';
            pass.value = ''; 
        }
        pass.focus();
    }
    
    function closeLogin() {
        document.getElementById('loginModal').style.display = 'none';
    }
    
    // Close modal on outside click
    window.onclick = function(event) {
        const modal = document.getElementById('loginModal');
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }

    // --- PATIENT FEATURES ---
    function openMyCard() {
        document.getElementById('myCardModal').style.display = 'flex';
        // Auto-focus
        setTimeout(() => document.getElementById('card-phone').focus(), 100);
    }
    
    function fetchMyCard() {
        const phone = document.getElementById('card-phone').value;
        if(!phone) return;
        
        fetch('/api/patient/my-card', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({phone: phone})
        }).then(r => r.json()).then(data => {
            if(data.error) {
                alert('Data tidak ditemukan. Pastikan nomor WhatsApp sesuai pendaftaran.');
            } else {
                document.getElementById('card-login-step').style.display = 'none';
                document.getElementById('card-display-step').style.display = 'block';
                
                // Hard Card
                document.getElementById('hc-name').innerText = data.name;
                document.getElementById('hc-phone').innerText = data.phone;
                document.getElementById('hc-status').innerText = (data.status || 'waiting').toUpperCase();
                
                const fmtDate = (s) => {
                    if(!s) return '-';
                    try {
                        const d = new Date(s.replace(' ', 'T'));
                        const m = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];
                        const min = d.getMinutes().toString().padStart(2, '0');
                        return `${d.getDate()} ${m[d.getMonth()]} ${d.getHours()}:${min}`;
                    } catch(e) { return s; }
                };

                // Date for Hard Card
                let dateStr = data.created_at;
                try {
                    const d = new Date(dateStr.replace(' ', 'T'));
                    const m = ["JAN", "FEB", "MAR", "APR", "MEI", "JUN", "JUL", "AGU", "SEP", "OKT", "NOV", "DES"];
                    document.getElementById('hc-date').innerText = d.getDate() + ' ' + m[d.getMonth()];
                } catch(e) {
                     document.getElementById('hc-date').innerText = '-';
                }

                // Details List
                document.getElementById('d-name').innerText = data.name;
                document.getElementById('d-phone').innerText = data.phone;
                document.getElementById('d-status').innerText = (data.status || 'waiting').toUpperCase();
                document.getElementById('d-in').innerText = fmtDate(data.created_at);
                document.getElementById('d-out').innerText = fmtDate(data.finished_at);
                
                document.getElementById('d-complaint').innerText = data.complaint || '-';
                document.getElementById('d-diag').innerText = data.diagnosis || '-';
                document.getElementById('d-presc').innerText = data.prescription || '-';
                document.getElementById('d-action').innerText = data.medical_action || '-';
            }
        });
    }
    
    function resetCardView() {
        document.getElementById('card-login-step').style.display = 'block';
        document.getElementById('card-display-step').style.display = 'none';
        document.getElementById('card-phone').value = '';
    }

    function openMyLab() {
        document.getElementById('myLabModal').style.display = 'flex';
        const cardPhone = document.getElementById('card-phone').value;
        if(cardPhone) {
            document.getElementById('lab-phone').value = cardPhone;
            fetchMyLab(); // Auto fetch if phone known
        }
    }
    
    function fetchMyLab() {
        const phone = document.getElementById('lab-phone').value;
        if(!phone) return;
        
        fetch('/api/patient/my-lab', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({phone: phone})
        }).then(r => r.json()).then(data => {
            document.getElementById('lab-login-step').style.display = 'none';
            document.getElementById('lab-list-step').style.display = 'block';
            const cont = document.getElementById('lab-results-container');
            cont.innerHTML = '';
            
            if(data.length === 0) {
                cont.innerHTML = '<div class="text-center text-muted py-3">Tidak ada hasil lab ditemukan.</div>';
            } else {
                data.forEach(item => {
                    cont.innerHTML += `
                        <div class="d-flex align-items-center justify-content-between p-2 border-bottom">
                            <div>
                                <div class="fw-bold small">${item.description || 'Dokumen Lab'}</div>
                                <div class="text-muted" style="font-size:0.7rem;">${item.created_at}</div>
                            </div>
                            <a href="/uploads/${item.file_path}" target="_blank" class="btn btn-sm btn-primary rounded-pill"><i class="fas fa-eye"></i></a>
                        </div>
                    `;
                });
            }
        });
    }
    
    function resetLabView() {
        document.getElementById('lab-login-step').style.display = 'block';
        document.getElementById('lab-list-step').style.display = 'none';
    }

</script>
"""

HTML_LANDING = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Klinik Kesehatan</title>
    <link rel="icon" href="{{ url_for('static', filename='favicon.svg') }}">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
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
            margin: auto;
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
            padding: 15px 40px;
            border-radius: 50px;
            margin-bottom: 20px;
            display: inline-block;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            position: relative;
            overflow: hidden;
        }
        .status-badge:hover { transform: scale(1.05); box-shadow: 0 8px 25px rgba(0,0,0,0.15); }
        .status-open { background: #2ecc71; color: white; border: 2px solid #27ae60; }
        .status-closed { background: #e74c3c; color: white; border: 2px solid #c0392b; }
        
        .status-options-hidden {
            max-height: 0;
            opacity: 0;
            overflow: hidden;
            transition: all 0.5s cubic-bezier(0.68, -0.55, 0.27, 1.55);
            transform: translateY(-20px) scale(0.9);
        }
        .status-options-visible {
            max-height: 300px;
            opacity: 1;
            transform: translateY(0) scale(1);
            margin-bottom: 20px;
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .status-option-btn {
            border: none;
            border-radius: 15px;
            padding: 15px 25px;
            font-weight: bold;
            color: white;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-width: 140px;
            transition: 0.3s;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            position: relative;
            overflow: hidden;
        }
        .status-option-btn::before {
            content: '';
            position: absolute;
            top: 0; left: -100%;
            width: 100%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
            transition: 0.5s;
        }
        .status-option-btn:hover::before { left: 100%; }
        .status-option-btn:hover { transform: translateY(-5px); box-shadow: 0 8px 20px rgba(0,0,0,0.2); }
        .btn-open { background: linear-gradient(135deg, #2ecc71, #27ae60); }
        .btn-close { background: linear-gradient(135deg, #e74c3c, #c0392b); }
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
    </style>
</head>
<body>
    {{ navbar|safe }}
    <div class="glass-panel">
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

            <a href="/surat-sakit" class="main-btn">
                <i class="fas fa-file-medical"></i>
                SURAT SAKIT
            </a>

            <a href="/kasir" class="main-btn">
                <i class="fas fa-cash-register"></i>
                KASIR & LAPORAN
            </a>

            <a href="/database-pasien" class="main-btn">
                <i class="fas fa-database"></i>
                DATABASE PASIEN
            </a>

            <a href="/pencarian-pasien" class="main-btn">
                <i class="fas fa-search"></i>
                CARI PASIEN
            </a>

            <a href="/statistik" class="main-btn">
                <i class="fas fa-chart-pie"></i>
                DASHBOARD STATISTIK
            </a>
        </div>
    </div>
    
    <a href="https://wa.me/6281241865310?text=Halo%20Dokter,%20saya%20ingin%20konsultasi%20darurat." class="wa-float" target="_blank">
        <i class="fab fa-whatsapp"></i>
    </a>

    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
</body>
</html>
"""

HTML_LAB = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hasil Lab Digital</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>body{background:#f4f7f6; font-family:'Segoe UI',sans-serif;}</style>
</head>
<body>
    {{ navbar|safe }}
    <div class="container py-5">
        <h2 class="mb-4 fw-bold text-center text-primary"><i class="fas fa-microscope me-2"></i> Hasil Laboratorium & Rontgen</h2>
        
        <div class="card shadow border-0 rounded-4">
             <div class="card-header bg-white py-3 border-0">
                <form method="get" class="d-flex gap-2">
                    <input type="text" name="q" class="form-control" placeholder="Cari Pasien..." value="{{ request.args.get('q', '') }}">
                    <button class="btn btn-primary"><i class="fas fa-search"></i></button>
                </form>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Nama Pasien</th>
                                <th>Hasil Lab Tersimpan</th>
                                <th>Upload Baru</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for p in patients %}
                            <tr>
                                <td class="fw-bold">{{ p.name }}<br><small class="text-muted">{{ p.phone }}</small></td>
                                <td>
                                    {% if p.results %}
                                        <div class="d-flex flex-wrap gap-2">
                                        {% for res in p.results %}
                                            <a href="/uploads/{{ res.file_path }}" target="_blank" class="btn btn-sm btn-outline-primary" title="{{ res.description }}">
                                                <i class="fas fa-file-alt me-1"></i> {{ res.description or 'Dokumen' }}
                                            </a>
                                        {% endfor %}
                                        </div>
                                    {% else %}
                                        <span class="text-muted small">- Belum ada file -</span>
                                    {% endif %}
                                </td>
                                <td>
                                    <button class="btn btn-sm btn-success" onclick="openUploadModal({{ p.id }}, '{{ p.name }}')">
                                        <i class="fas fa-upload me-1"></i> Upload
                                    </button>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Upload Modal -->
    <div class="modal fade" id="uploadModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header bg-success text-white">
                    <h5 class="modal-title">Upload Hasil Lab</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>Pasien: <strong id="up-name"></strong></p>
                    <form action="/upload/lab" method="post" enctype="multipart/form-data">
                        <input type="hidden" name="patient_id" id="up-id">
                        <div class="mb-3">
                            <label class="form-label">Deskripsi File</label>
                            <input type="text" name="description" class="form-control" placeholder="Contoh: Rontgen Thorax, Darah Lengkap" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Pilih File (JPG, PNG, PDF)</label>
                            <input type="file" name="file" class="form-control" required>
                        </div>
                        <button class="btn btn-success w-100">Simpan</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function openUploadModal(id, name) {
            document.getElementById('up-id').value = id;
            document.getElementById('up-name').innerText = name;
            new bootstrap.Modal(document.getElementById('uploadModal')).show();
        }

        // --- Client-Side Image Compression ---
        document.addEventListener('DOMContentLoaded', () => {
            const fileInput = document.querySelector('input[name="file"]');
            if(fileInput) {
                fileInput.addEventListener('change', async function(e) {
                    const file = e.target.files[0];
                    if (!file || !file.type.startsWith('image/')) return;

                    // Visual Feedback
                    const parent = e.target.parentNode;
                    let feedback = parent.querySelector('.compress-feedback');
                    if(!feedback) {
                        feedback = document.createElement('div');
                        feedback.className = 'compress-feedback text-warning small mt-1';
                        parent.appendChild(feedback);
                    }
                    feedback.innerText = 'Compressing...';

                    try {
                        const compressedBlob = await compressImage(file);

                        // Create new File object
                        const newFile = new File([compressedBlob], file.name, {
                            type: 'image/jpeg',
                            lastModified: Date.now()
                        });

                        // Update Input
                        const dataTransfer = new DataTransfer();
                        dataTransfer.items.add(newFile);
                        fileInput.files = dataTransfer.files;

                        feedback.innerText = 'Compression Complete (' + (compressedBlob.size/1024).toFixed(1) + 'KB)';
                        feedback.classList.remove('text-warning');
                        feedback.classList.add('text-success');

                    } catch (err) {
                        console.error(err);
                        feedback.innerText = 'Compression Failed. Using original.';
                        feedback.classList.remove('text-warning');
                        feedback.classList.add('text-danger');
                    }
                });
            }
        });

        function compressImage(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onload = (event) => {
                    const img = new Image();
                    img.src = event.target.result;
                    img.onload = () => {
                        const canvas = document.createElement('canvas');
                        const ctx = canvas.getContext('2d');

                        // Max dimensions
                        const MAX_WIDTH = 1024;
                        const MAX_HEIGHT = 1024;
                        let width = img.width;
                        let height = img.height;

                        if (width > height) {
                            if (width > MAX_WIDTH) {
                                height *= MAX_WIDTH / width;
                                width = MAX_WIDTH;
                            }
                        } else {
                            if (height > MAX_HEIGHT) {
                                width *= MAX_HEIGHT / height;
                                height = MAX_HEIGHT;
                            }
                        }

                        canvas.width = width;
                        canvas.height = height;
                        ctx.drawImage(img, 0, 0, width, height);

                        // Compress to JPEG 0.7
                        canvas.toBlob((blob) => {
                            if(blob) resolve(blob);
                            else reject(new Error('Canvas to Blob failed'));
                        }, 'image/jpeg', 0.7);
                    };
                    img.onerror = (err) => reject(err);
                };
                reader.onerror = (err) => reject(err);
            });
        }
    </script>
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
</body>
</html>
"""

HTML_STOCK_PRED = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prediksi Stok Obat</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>body{background:#f4f7f6; font-family:'Segoe UI',sans-serif;}</style>
</head>
<body>
    {{ navbar|safe }}
    <div class="container py-5">
        <h2 class="mb-4 fw-bold text-center text-primary"><i class="fas fa-chart-line me-2"></i> Prediksi Stok Obat (Inventory Forecasting)</h2>
        
        <div class="card shadow border-0 rounded-4">
            <div class="card-body p-4">
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i> Sistem menggunakan algoritma <strong>Moving Average</strong> berdasarkan data pemakaian 7 hari terakhir.
                </div>
                
                <div class="table-responsive">
                    <table class="table table-hover align-middle">
                        <thead class="table-light">
                            <tr>
                                <th>Nama Obat</th>
                                <th>Sisa Stok</th>
                                <th>Rata-rata Pakai/Hari</th>
                                <th>Estimasi Habis</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for p in predictions %}
                            <tr class="table-{{ 'danger' if p.days_left < 3 else '' }}">
                                <td class="fw-bold">{{ p.name }}</td>
                                <td>{{ p.stock }} {{ p.unit }}</td>
                                <td>~{{ p.avg_usage }} {{ p.unit }}</td>
                                <td class="fw-bold">{{ p.days_left }} Hari Lagi</td>
                                <td><span class="badge bg-{{ p.css }}">{{ p.status }}</span></td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    {% if not predictions %}
                    <div class="text-center py-5 text-muted">Belum ada data stok obat.</div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
</body>
</html>
"""

HTML_MAP = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Peta Sebaran Penyakit</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>body{background:#f4f7f6; font-family:'Segoe UI',sans-serif;}</style>
</head>
<body>
    {{ navbar|safe }}
    <div class="container py-5">
        <h2 class="mb-4 fw-bold text-center text-primary"><i class="fas fa-map-marked-alt me-2"></i> Peta Sebaran Penyakit (GIS Sederhana)</h2>
        
        <div class="row">
            <div class="col-lg-8">
                <div class="card shadow border-0 rounded-4 mb-4">
                    <div class="card-body p-4 position-relative" style="min-height: 400px; background: #e9ecef; overflow: hidden;">
                        <h5 class="fw-bold mb-3">Visualisasi Wilayah</h5>
                        <!-- Simple Grid Map -->
                        <div class="d-flex flex-wrap gap-3 justify-content-center align-items-center h-100" id="map-container">
                            <!-- Blocks will be rendered here -->
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-lg-4">
                <div class="card shadow border-0 rounded-4">
                    <div class="card-body p-4">
                        <h5 class="fw-bold mb-3">Detail Wilayah</h5>
                        <div id="detail-list" class="list-group">
                            <div class="text-center text-muted">Klik wilayah di peta untuk melihat detail.</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const mapData = {{ map_data | tojson }};
        
        // Mock Layout if data is empty or sparse, ensures we have some blocks to show
        const blocks = ['Blok A', 'Blok B', 'Blok C', 'Blok D', 'Blok E'];
        
        const container = document.getElementById('map-container');
        
        blocks.forEach(block => {
            let totalCases = 0;
            let diseases = {};
            if(mapData[block]) {
                diseases = mapData[block];
                totalCases = Object.values(diseases).reduce((a,b) => a+b, 0);
            }
            
            // Color intensity
            let opacity = 0.2 + (Math.min(totalCases, 50) / 50) * 0.8;
            let color = `rgba(231, 76, 60, ${opacity})`; // Red base
            if (totalCases === 0) color = '#bdc3c7'; // Grey
            
            const el = document.createElement('div');
            el.style.width = '120px';
            el.style.height = '120px';
            el.style.backgroundColor = color;
            el.style.borderRadius = '10px';
            el.style.display = 'flex';
            el.style.flexDirection = 'column';
            el.style.alignItems = 'center';
            el.style.justifyContent = 'center';
            el.style.cursor = 'pointer';
            el.style.border = '2px solid #fff';
            el.style.boxShadow = '0 5px 15px rgba(0,0,0,0.1)';
            el.style.transition = '0.3s';
            
            el.innerHTML = `<h4 class="fw-bold text-white mb-0">${block}</h4><span class="text-white small">${totalCases} Kasus</span>`;
            
            el.onclick = () => showDetail(block, diseases);
            el.onmouseenter = () => el.style.transform = 'scale(1.05)';
            el.onmouseleave = () => el.style.transform = 'scale(1)';
            
            container.appendChild(el);
        });
        
        function showDetail(block, diseases) {
            const list = document.getElementById('detail-list');
            list.innerHTML = `<h5 class="mb-3 text-primary fw-bold">${block}</h5>`;
            
            if(Object.keys(diseases).length === 0) {
                list.innerHTML += '<div class="alert alert-info">Tidak ada data penyakit tercatat.</div>';
                return;
            }
            
            for (const [d, count] of Object.entries(diseases)) {
                list.innerHTML += `
                    <div class="list-group-item d-flex justify-content-between align-items-center">
                        ${d}
                        <span class="badge bg-danger rounded-pill">${count}</span>
                    </div>`;
            }
            
            // Suggestion
            list.innerHTML += `<div class="mt-3 p-3 bg-light rounded small"><strong>Saran Tindakan:</strong><br>Lakukan fogging atau penyuluhan kesehatan di wilayah ini.</div>`;
        }
    </script>
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
</body>
</html>
"""

HTML_SYMPTOM = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Symptom Checker</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>body{background:#f4f7f6; font-family:'Segoe UI',sans-serif;}</style>
</head>
<body>
    {{ navbar|safe }}
    <div class="container py-5">
        <h2 class="mb-4 fw-bold text-center text-primary"><i class="fas fa-clipboard-check me-2"></i> Symptom Checker (Deteksi Dini)</h2>
        
        <div class="card shadow border-0 rounded-4" style="max-width: 700px; margin: auto;">
            <div class="card-body p-5">
                <p class="text-muted text-center mb-4">Masukkan keluhan utama pasien (contoh: "badan panas, ada bintik merah")</p>
                
                <div class="mb-3">
                    <textarea id="symptoms" class="form-control form-control-lg" rows="3" placeholder="Ketik keluhan di sini..."></textarea>
                </div>
                <button class="btn btn-primary w-100 btn-lg rounded-pill fw-bold" onclick="checkSymptom()"><i class="fas fa-stethoscope me-2"></i> ANALISIS GEJALA</button>
                
                <div id="result-box" class="mt-4 p-4 bg-light rounded border" style="display:none; border-left: 5px solid #2ecc71 !important;">
                    <h4 class="fw-bold mb-2">Hasil Analisis Data Medis:</h4>
                    <div class="mb-2"><strong>Suspek Penyakit:</strong> <span id="res-disease" class="text-danger fw-bold">-</span></div>
                    <div class="mb-2"><strong>Saran:</strong> <span id="res-advice">-</span></div>
                    <div><strong>Tingkat Keyakinan:</strong> <span id="res-conf" class="badge bg-secondary">-</span></div>
                    <small class="text-muted d-block mt-3">*Hasil ini hanya prediksi awal, bukan diagnosa medis pasti.</small>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function checkSymptom() {
            const text = document.getElementById('symptoms').value;
            if(!text) return;
            
            document.getElementById('result-box').style.display = 'none';
            
            fetch('/api/symptom/check', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: text})
            }).then(r => r.json()).then(data => {
                document.getElementById('res-disease').innerText = data.disease;
                document.getElementById('res-advice').innerText = data.advice;
                document.getElementById('res-conf').innerText = data.confidence;
                
                const badge = document.getElementById('res-conf');
                badge.className = 'badge ' + (data.confidence === 'Tinggi' ? 'bg-success' : 'bg-warning');
                
                document.getElementById('result-box').style.display = 'block';
            });
        }
    </script>
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
</body>
</html>
"""

HTML_QR_PAGE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kartu Pasien QR</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>body{background:#f4f7f6; font-family:'Segoe UI',sans-serif; min-height: 100vh; display: flex; flex-direction: column;}</style>
</head>
<body>
    {{ navbar|safe }}
    <div class="container py-5">
        <h2 class="mb-4 fw-bold text-center text-dark"><i class="fas fa-qrcode me-2"></i> Kartu Pasien Digital QR Code</h2>
        
        <div class="card shadow border-0 rounded-4 mb-4">
            <div class="card-body p-5 text-center">
                <form method="get" class="mb-4">
                    <div class="input-group input-group-lg">
                        <input type="text" name="q" class="form-control" placeholder="Cari Nama / No HP Pasien..." value="{{ request.args.get('q', '') }}">
                        <button class="btn btn-primary px-4"><i class="fas fa-search"></i> CARI</button>
                    </div>
                </form>
                
                {% if patients %}
                <div class="list-group text-start">
                    {% for p in patients %}
                    <div class="list-group-item list-group-item-action d-flex justify-content-between align-items-center p-3" 
                         onclick='openQRModal({{ p | tojson | safe }})' style="cursor: pointer;">
                        <div>
                            <h5 class="mb-1 fw-bold">{{ p.name }}</h5>
                            <small class="text-muted"><i class="fas fa-phone me-1"></i> {{ p.phone }}</small>
                        </div>
                        <button class="btn btn-dark rounded-pill px-4"><i class="fas fa-qrcode me-2"></i> GENERATE QR</button>
                    </div>
                    {% endfor %}
                </div>
                {% elif request.args.get('q') %}
                <div class="alert alert-warning">Pasien tidak ditemukan.</div>
                {% endif %}
            </div>
        </div>
    </div>

    <!-- QR Modal -->
    <div class="modal fade" id="qrModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header bg-dark text-white">
                    <h5 class="modal-title"><i class="fas fa-qrcode me-2"></i> Kartu Pasien Digital</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body text-center p-5">
                    <h3 class="fw-bold mb-1" id="qr-name">Nama Pasien</h3>
                    <p class="text-muted mb-4" id="qr-phone">08xxx</p>
                    
                    <div id="qr-loading" class="spinner-border text-primary" role="status" style="display:none;"></div>
                    <img id="qr-image" src="" style="width: 250px; height: 250px; display:none;" class="img-thumbnail shadow">
                    
                    <div class="mt-4">
                        <small class="text-muted d-block">Tunjukkan QR Code ini kepada petugas saat pendaftaran ulang.</small>
                    </div>
                </div>
                <div class="modal-footer justify-content-center">
                    <button class="btn btn-outline-dark w-100" onclick="printQR()">Cetak / Simpan Gambar</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function openQRModal(p) {
            document.getElementById('qr-name').innerText = p.name;
            document.getElementById('qr-phone').innerText = p.phone;
            
            const img = document.getElementById('qr-image');
            const load = document.getElementById('qr-loading');
            img.style.display = 'none';
            load.style.display = 'inline-block';
            
            new bootstrap.Modal(document.getElementById('qrModal')).show();
            
            fetch('/api/qr/generate', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id: p.id, name: p.name, phone: p.phone})
            }).then(r => r.json()).then(data => {
                img.src = "data:image/png;base64," + data.image;
                load.style.display = 'none';
                img.style.display = 'inline-block';
            });
        }
        
        function printQR() {
            const win = window.open('');
            const img = document.getElementById('qr-image').src;
            const name = document.getElementById('qr-name').innerText;
            win.document.write(`<div style="text-align:center; padding:50px; font-family:sans-serif;"><h2>${name}</h2><img src="${img}" width="300"><br><br>KLINIK KESEHATAN</div>`);
            win.print();
        }
    </script>
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
</body>
</html>
"""

HTML_AUDIT = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audit Trail System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>body{background:#f4f7f6; font-family:'Segoe UI',sans-serif;}</style>
</head>
<body>
    {{ navbar|safe }}
    <div class="container py-5">
        <h2 class="mb-4 fw-bold text-center text-dark"><i class="fas fa-history me-2"></i> Audit Trail (Kotak Hitam Digital)</h2>
        <div class="card shadow border-0 rounded-4">
            <div class="card-header bg-dark text-white">
                <h5 class="mb-0">Log Aktivitas Sistem</h5>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover table-striped mb-0">
                        <thead class="table-dark">
                            <tr>
                                <th>Timestamp</th>
                                <th>User</th>
                                <th>Action</th>
                                <th>Details</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for log in logs %}
                            <tr>
                                <td style="white-space:nowrap;">{{ log.timestamp }}</td>
                                <td class="fw-bold">{{ log.user }}</td>
                                <td><span class="badge bg-secondary">{{ log.action }}</span></td>
                                <td>{{ log.details }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    {% if not logs %}
                    <div class="text-center py-5 text-muted">Belum ada log aktivitas.</div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
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
    <link rel="icon" href="{{ url_for('static', filename='favicon.svg') }}">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { 
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
            font-family: 'Segoe UI', sans-serif; 
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .glass-panel-custom {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
            border: 1px solid rgba(255, 255, 255, 0.5);
        }
        .big-number { font-size: 6rem; font-weight: 800; color: #2ecc71; line-height: 1; }
        .section-label { font-size: 0.9rem; font-weight: 700; text-transform: uppercase; color: #999; letter-spacing: 1px; margin-bottom: 15px; }
        .ticket {
            border: 2px dashed #2ecc71; background: #e8f5e9; padding: 20px; border-radius: 10px;
            text-align: center; margin-top: 20px; display: none;
        }
    </style>
</head>
<body>
    {{ navbar|safe }}
    
    <div class="container py-5">
        <div class="row g-4">
            <div class="col-lg-6">
                <div class="glass-panel-custom h-100 text-center d-flex flex-column justify-content-center">
                    <div class="section-label">Sedang Diperiksa</div>
                    <div class="big-number mb-3" id="current-num">--</div>
                    <h3 class="fw-bold mb-0" id="current-name">Menunggu Dokter...</h3>
                </div>
            </div>
            
            <div class="col-lg-3 col-6">
                <div class="glass-panel-custom h-100 text-center">
                    <div class="section-label">Antrean Menunggu</div>
                    <div class="display-1 fw-bold text-muted" id="waiting-count">0</div>
                    <small class="text-muted">PASIEN</small>
                </div>
            </div>
            
            <div class="col-lg-3 col-6">
                <div class="glass-panel-custom h-100 text-center d-flex align-items-center justify-content-center bg-white">
                    <div>
                        <div class="section-label">Estimasi Waktu</div>
                        <div class="fs-2 fw-bold text-warning">~15</div>
                        <small class="text-muted">Menit/Pasien</small>
                    </div>
                </div>
            </div>
            
            <div class="col-lg-12">
                 <div class="glass-panel-custom">
                    <h4 class="mb-4 fw-bold"><i class="fas fa-ticket-alt me-2 text-success"></i> Ambil Nomor Antrean</h4>
                    <div class="row">
                        <div class="col-md-6">
                            <form id="queue-form" onsubmit="submitQueue(event)">
                                <div class="mb-3">
                                    <label class="fw-bold mb-1">Nama Pasien</label>
                                    <input type="text" id="q-name" class="form-control form-control-lg" placeholder="Masukkan Nama Lengkap" required>
                                </div>
                                <div class="mb-3">
                                    <label class="fw-bold mb-1">Nomor WhatsApp</label>
                                    <input type="tel" id="q-phone" class="form-control form-control-lg" placeholder="08..." required>
                                </div>
                                <div class="mb-3">
                                    <label class="fw-bold mb-1">Alamat / Blok (Opsional)</label>
                                    <input type="text" id="q-address" class="form-control" placeholder="Contoh: Blok A No. 12">
                                </div>
                                <div class="mb-3">
                                    <label class="fw-bold mb-1">Keluhan Utama</label>
                                    <textarea id="q-complaint" class="form-control" rows="3" placeholder="Contoh: Demam, Batuk, Pusing..." required></textarea>
                                </div>
                                <button type="submit" class="btn btn-success w-100 py-3 fw-bold rounded-pill shadow-sm">AMBIL NOMOR SEKARANG</button>
                            </form>
                        </div>
                        <div class="col-md-6 d-flex align-items-center justify-content-center">
                            <div id="ticket-view" class="ticket w-100">
                                <h4 class="text-uppercase text-muted mb-4">Nomor Antrean Anda</h4>
                                <div class="display-1 fw-bold text-success mb-3" id="my-number">0</div>
                                <p class="mb-4">Mohon menunggu panggilan dari perawat kami.</p>
                                <button class="btn btn-outline-success rounded-pill px-4" onclick="location.reload()">Selesai / Ambil Baru</button>
                            </div>
                            <div id="ticket-placeholder" class="text-center text-muted opacity-50">
                                <i class="fas fa-print fa-5x mb-3"></i>
                                <p>Tiket akan muncul di sini setelah Anda mendaftar.</p>
                            </div>
                        </div>
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
                address: document.getElementById('q-address').value,
                complaint: document.getElementById('q-complaint').value
            };
            
            fetch('/api/queue/add', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            }).then(r => r.json()).then(res => {
                if(res.ticket) {
                    document.getElementById('queue-form').reset();
                    document.getElementById('ticket-placeholder').style.display = 'none';
                    document.getElementById('ticket-view').style.display = 'block';
                    document.getElementById('my-number').innerText = res.ticket;
                }
            });
        }
        
        setInterval(refreshStatus, 3000);
        refreshStatus();

        // Auto-fill from URL params
        window.onload = function() {
            const params = new URLSearchParams(window.location.search);
            if(params.has('name')) document.getElementById('q-name').value = params.get('name');
            if(params.has('phone')) document.getElementById('q-phone').value = params.get('phone');
        }
    </script>
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
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
    <link rel="icon" href="{{ url_for('static', filename='favicon.svg') }}">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { 
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
            font-family: 'Segoe UI', sans-serif; 
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .glass-panel-custom {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            border: 1px solid rgba(255,255,255,0.5);
            transition: all 0.3s ease;
        }
        .section-label { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: #7f8c8d; margin-bottom: 15px; letter-spacing: 1px; }
        .queue-card { 
            background: white; border-left: 5px solid #2ecc71; padding: 15px; margin-bottom: 10px; 
            border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); transition: 0.2s; cursor: pointer;
        }
        .queue-card:hover { transform: translateX(5px); }
        .active-patient-box {
            background: #fffbe6; border: 2px solid #f1c40f; border-radius: 15px; padding: 30px; text-align: center;
        }
        /* Custom Scrollbar for Table */
        .custom-scrollbar::-webkit-scrollbar {
            height: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
            background: #f1f1f1; 
            border-radius: 5px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
            background: #2ecc71; 
            border-radius: 5px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
            background: #27ae60; 
        }
    </style>
</head>
<body>
    {{ navbar|safe }}

    <div class="container-fluid py-4 px-lg-5">
        <div class="row g-4">
            <!-- CENTER/TOP: CURRENT PATIENT -->
            <div class="col-lg-12">
                <div class="glass-panel-custom">
                    <div class="section-label"><i class="fas fa-stethoscope me-2"></i> Sedang Diperiksa</div>
                    <div id="current-patient-panel">
                        <!-- Loaded via JS -->
                        <div class="text-center text-muted py-5">Belum ada pasien dipanggil</div>
                    </div>
                </div>
            </div>
            
            <!-- LEFT: WAITING LIST -->
            <div class="col-lg-5">
                <div class="glass-panel-custom h-100">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div class="section-label mb-0"><i class="fas fa-user-clock me-2"></i> Antrean Menunggu</div>
                        <span class="badge bg-primary rounded-pill" id="waiting-count-badge">0</span>
                    </div>
                    <div id="queue-list" style="max-height: 500px; overflow-y: auto; padding-right: 5px;">
                        <!-- JS Loaded -->
                    </div>
                </div>
            </div>

            <!-- RIGHT: HISTORY -->
            <div class="col-lg-7">
                <div class="glass-panel-custom mb-4">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div class="section-label mb-0"><i class="fas fa-history me-2"></i> Riwayat Pemeriksaan (Hari Ini)</div>
                        <button class="btn btn-sm btn-outline-success fw-bold" onclick="openArchive()"><i class="fas fa-database me-2"></i> Database</button>
                    </div>
                    <div class="table-responsive custom-scrollbar">
                        <table class="table table-hover align-middle" style="min-width: 600px;">
                            <thead class="table-light">
                                <tr>
                                    <th>No</th>
                                    <th style="white-space:nowrap">Nama Pasien</th>
                                    <th>Keluhan</th>
                                    <th>Diagnosa</th>
                                    <th>Resep Obat</th>
                                    <th>Tindakan</th>
                                    <th>Aksi</th>
                                </tr>
                            </thead>
                            <tbody id="history-table"></tbody>
                        </table>
                    </div>
                </div>

                <!-- DELETED PATIENTS -->
                <div class="glass-panel-custom bg-light border-danger">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div class="section-label text-danger mb-0"><i class="fas fa-trash-alt me-2"></i> DATA PASIEN YANG DIHAPUS</div>
                        <button class="btn btn-sm btn-outline-danger fw-bold" onclick="openArchive()"><i class="fas fa-database me-2"></i> Database</button>
                    </div>
                    <div class="table-responsive custom-scrollbar" style="max-height: 200px;">
                        <table class="table table-sm table-hover align-middle">
                            <thead class="table-danger">
                                <tr>
                                    <th>No</th>
                                    <th>Nama Pasien</th>
                                    <th>Alasan Batal</th>
                                </tr>
                            </thead>
                            <tbody id="deleted-table"></tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Finish Modal (Same as before) -->
    <div class="modal fade" id="finishModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header bg-success text-white">
                    <h5 class="modal-title">Selesaikan Pemeriksaan & Rekam Medis</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <input type="hidden" id="finish-id">
                    <div class="mb-3">
                        <label class="fw-bold">Diagnosa Dokter</label>
                        <textarea id="diag-input" class="form-control" rows="3" placeholder="Masukkan hasil diagnosa..."></textarea>
                    </div>
                    <div class="mb-3">
                        <label class="fw-bold">Resep Obat</label>
                        <textarea id="presc-input" class="form-control" rows="3" placeholder="Daftar obat..."></textarea>
                    </div>
                    <div class="mb-3">
                        <label class="fw-bold">Tindakan</label>
                        <textarea id="action-input" class="form-control" rows="3" placeholder="Tindakan medis yang dilakukan..."></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Batal</button>
                    <button type="button" class="btn btn-primary" onclick="submitFinish()"><i class="fas fa-save me-2"></i> Simpan & Selesai</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // JS Logic (Same as before, just slight UI tweaks in rendering)
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
            fetch('/api/queue/status?full=1').then(r => r.json()).then(data => {
                // Queue List
                const list = document.getElementById('queue-list');
                list.innerHTML = '';
                document.getElementById('waiting-count-badge').innerText = data.waiting.length;
                
                data.waiting.forEach(p => {
                    list.innerHTML += `
                        <div class="queue-card d-flex justify-content-between align-items-center">
                            <div>
                                <h5 class="mb-1 fw-bold">#${p.number} ${escapeHtml(p.name)}</h5>
                                <small class="text-muted"><i class="fas fa-comment-medical me-1"></i> ${escapeHtml(p.complaint)}</small>
                            </div>
                            <button class="btn btn-sm btn-outline-primary fw-bold" onclick="callPatient(${p.id})">
                                <i class="fas fa-bullhorn me-1"></i> Panggil
                            </button>
                        </div>
                    `;
                });
                if(data.waiting.length === 0) list.innerHTML = '<div class="text-center text-muted py-4">Tidak ada antrean menunggu.</div>';
                
                // Current Patient
                const panel = document.getElementById('current-patient-panel');
                if (data.current) {
                    panel.innerHTML = `
                        <div class="active-patient-box">
                            <div class="row align-items-center">
                                <div class="col-md-8 text-md-start mb-3 mb-md-0">
                                    <h6 class="text-warning text-uppercase fw-bold mb-1">Pasien Saat Ini</h6>
                                    <h1 class="fw-bold display-5 mb-2">#${data.current.number} ${escapeHtml(data.current.name)}</h1>
                                    <p class="lead mb-0 text-muted"><i class="fas fa-notes-medical me-2"></i> Keluhan: ${escapeHtml(data.current.complaint)}</p>
                                </div>
                                <div class="col-md-4 text-md-end">
                                    <button class="btn btn-success btn-lg w-100 py-3 shadow" onclick="openFinishModal(${data.current.id})">
                                        <i class="fas fa-check-circle me-2"></i> Selesai Periksa
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    panel.innerHTML = '<div class="text-center text-muted py-5 border rounded bg-light"><h5><i class="fas fa-user-slash fa-2x mb-3 d-block"></i>Belum ada pasien yang dipanggil</h5><p>Silakan panggil pasien dari daftar antrean.</p></div>';
                }
                
                // History
                const hist = document.getElementById('history-table');
                hist.innerHTML = '';
                data.history.forEach(p => {
                    hist.innerHTML += `
                        <tr>
                            <td class="fw-bold text-center">${p.number}</td>
                            <td style="white-space:nowrap">${escapeHtml(p.name)}</td>
                            <td>${escapeHtml(p.complaint)}</td>
                            <td>${escapeHtml(p.diagnosis)}</td>
                            <td>${escapeHtml(p.prescription)}</td>
                            <td>${escapeHtml(p.medical_action)}</td>
                            <td>
                                <button class="btn btn-sm btn-danger rounded-circle" onclick="deletePatient(${p.id})">
                                    <i class="fas fa-trash-alt"></i>
                                </button>
                            </td>
                        </tr>`;
                });

                // Deleted
                const del = document.getElementById('deleted-table');
                if(del) {
                    del.innerHTML = '';
                    if(data.cancelled) {
                        data.cancelled.forEach(p => {
                            del.innerHTML += `
                                <tr>
                                    <td class="fw-bold text-center">${p.number}</td>
                                    <td class="fw-bold">${escapeHtml(p.name)}</td>
                                    <td class="text-danger">${escapeHtml(p.cancellation_reason)}</td>
                                </tr>`;
                        });
                    }
                }
            });
        }
        
        function deletePatient(id) {
            const reason = prompt("Masukkan Alasan Pembatalan/Penghapusan:");
            if (reason) {
                fetch('/api/queue/action', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ action: 'cancel', id: id, reason: reason })
                }).then(() => loadData());
            }
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
            document.getElementById('action-input').value = '';
            new bootstrap.Modal(document.getElementById('finishModal')).show();
        }
        
        function submitFinish() {
            const id = document.getElementById('finish-id').value;
            const diag = document.getElementById('diag-input').value;
            const presc = document.getElementById('presc-input').value;
            const act = document.getElementById('action-input').value;
            
            fetch('/api/queue/action', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ action: 'finish', id: id, diagnosis: diag, prescription: presc, medical_action: act })
            }).then(() => {
                const modal = bootstrap.Modal.getInstance(document.getElementById('finishModal'));
                modal.hide();
                loadData(); 
            });
        }
        
        setInterval(loadData, 5000);
        loadData();
    </script>

    <style>
    .archive-modal {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: white; z-index: 9999;
        transform-origin: left;
        transform: perspective(2000px) rotateY(-90deg);
        opacity: 0; pointer-events: none;
        transition: all 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .archive-modal.archive-visible {
        transform: perspective(2000px) rotateY(0deg);
        opacity: 1; pointer-events: auto;
    }
    .date-header {
        background: #e8f5e9; padding: 15px; border-left: 5px solid #2ecc71;
        margin-bottom: 10px; cursor: pointer; font-weight: bold; font-size: 1.1rem;
        display: flex; justify-content: space-between; align-items: center;
        border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .date-header:hover { background: #d0e9d4; }
    .date-content { display: none; padding: 15px; border: 1px solid #eee; margin-bottom: 20px; animation: slideDown 0.3s; border-radius: 5px; }
    .date-content.show { display: block; }
    @keyframes slideDown { from { opacity:0; transform:translateY(-10px); } to { opacity:1; transform:translateY(0); } }
    </style>

    <div id="archive-modal" class="archive-modal">
        <div class="container-fluid h-100 p-0">
            <div class="row h-100 g-0">
                <div class="col-12 h-100">
                    <div class="glass-panel-custom h-100 m-0" style="border-radius:0; overflow-y:auto; border:none;">
                        <div class="d-flex justify-content-between align-items-center mb-4 sticky-top bg-white p-3 shadow-sm">
                            <h3 class="fw-bold text-success m-0"><i class="fas fa-database me-2"></i> Arsip Data Pasien</h3>
                            <div class="d-flex gap-2">
                                <button class="btn btn-outline-primary btn-sm" onclick="setSort('desc')">Terbaru - Terlama</button>
                                <button class="btn btn-outline-primary btn-sm" onclick="setSort('asc')">Terlama - Terbaru</button>
                                <button class="btn btn-danger rounded-circle shadow-sm" onclick="closeArchive()"><i class="fas fa-times"></i></button>
                            </div>
                        </div>
                        <div id="archive-content" class="container py-3">
                            <div class="text-center text-muted"><i class="fas fa-circle-notch fa-spin fa-2x"></i><br>Loading Database...</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
    let archiveData = {};
    let sortOrder = 'desc';

    function openArchive() {
        document.getElementById('archive-modal').classList.add('archive-visible');
        fetch('/api/queue/archive').then(r=>r.json()).then(data => {
            archiveData = data;
            renderArchive();
        });
    }

    function setSort(order) {
        sortOrder = order;
        renderArchive();
    }

    function renderArchive() {
        const container = document.getElementById('archive-content');
        container.innerHTML = '';
        let dates = Object.keys(archiveData);
        if(sortOrder === 'asc') dates.sort();
        else dates.sort().reverse();
        
        if(dates.length === 0) {
            container.innerHTML = '<div class="text-center text-muted mt-5"><h5>Belum ada data arsip.</h5></div>';
            return;
        }

        const months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"];

        dates.forEach(date => {
            const rows = archiveData[date];
            
            // Format Date Indo
            let dateFormatted = date;
            try {
                const d = new Date(date);
                if(!isNaN(d)) dateFormatted = `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
            } catch(e) {}

            let html = `<div class="date-header" onclick="toggleDate('${date}')">
                            <span><i class="far fa-calendar-alt me-2"></i> ${dateFormatted}</span>
                            <span class="badge bg-success rounded-pill">${rows.length} Pasien</span>
                        </div>
                        <div id="date-${date}" class="date-content">
                            <div class="table-responsive">
                                <table class="table table-bordered table-hover align-middle">
                                    <thead class="table-success">
                                        <tr>
                                            <th>No</th>
                                            <th>Nama</th>
                                            <th>Status</th>
                                            <th>Keluhan</th>
                                            <th>Diagnosa</th>
                                            <th>Resep</th>
                                            <th>Tindakan</th>
                                            <th>Waktu</th>
                                        </tr>
                                    </thead>
                                    <tbody>`;
            rows.forEach(r => {
                const badge = r.status==='done' ? '<span class="badge bg-primary">Selesai</span>' : '<span class="badge bg-danger">Batal</span>';
                
                // Time Logic
                let time = '-';
                if (r.finished_at) time = r.finished_at.split(' ')[1];
                else if (r.created_at) time = r.created_at.split(' ')[1];

                html += `<tr>
                            <td class="text-center fw-bold">${r.number}</td>
                            <td>${escapeHtml(r.name)}</td>
                            <td>${badge}</td>
                            <td>${escapeHtml(r.complaint || '-')}</td>
                            <td>${escapeHtml(r.diagnosis || '-')}</td>
                            <td>${escapeHtml(r.prescription || '-')}</td>
                            <td>${escapeHtml(r.medical_action || '-')}</td>
                            <td class="text-center">${time} WITA</td>
                         </tr>`;
            });
            html += `</tbody></table></div></div>`;
            container.innerHTML += html;
        });
    }
    function closeArchive() {
        document.getElementById('archive-modal').classList.remove('archive-visible');
    }
    function toggleDate(id) {
        const el = document.getElementById('date-'+id);
        el.classList.toggle('show');
    }
    </script>
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
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
    <link rel="icon" href="{{ url_for('static', filename='favicon.svg') }}">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { 
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
            font-family: 'Segoe UI', sans-serif; 
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .glass-panel-custom {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            border: 1px solid rgba(255,255,255,0.5);
        }
        .section-label { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: #7f8c8d; margin-bottom: 20px; letter-spacing: 1px; }
    </style>
</head>
<body>
    {{ navbar|safe }}

    <div class="container py-5">
        <div class="row g-4">
            <div class="col-md-12">
                <div class="glass-panel-custom">
                    <div class="section-label"><i class="fas fa-plus-circle me-2"></i> Tambah / Update Stok Obat</div>
                    <form id="add-stock-form" class="row g-3 align-items-end" onsubmit="addStock(event)">
                        <div class="col-md-5">
                            <label class="form-label fw-bold small">Nama Obat</label>
                            <input type="text" class="form-control" id="new-name" placeholder="Contoh: Paracetamol 500mg" required>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label fw-bold small">Jumlah Awal</label>
                            <input type="number" class="form-control" id="new-stock" placeholder="0" required>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label fw-bold small">Satuan</label>
                            <select class="form-select" id="new-unit">
                                <option value="pcs">Pcs</option>
                                <option value="strip">Strip</option>
                                <option value="botol">Botol</option>
                                <option value="box">Box</option>
                            </select>
                        </div>
                        <div class="col-md-2">
                            <button type="submit" class="btn btn-primary w-100 fw-bold"><i class="fas fa-save me-1"></i> Simpan</button>
                        </div>
                    </form>
                </div>
            </div>
            
            <div class="col-md-12">
                <div class="glass-panel-custom">
                    <div class="section-label"><i class="fas fa-list-alt me-2"></i> Daftar Stok Obat</div>
                    <div class="table-responsive">
                        <table class="table table-hover align-middle">
                            <thead class="table-light">
                                <tr>
                                    <th>Nama Obat</th>
                                    <th class="text-center">Stok</th>
                                    <th class="text-center">Satuan</th>
                                    <th class="text-end">Aksi</th>
                                </tr>
                            </thead>
                            <tbody id="stock-table">
                                <!-- JS Loaded -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
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
                if(data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" class="text-center py-4 text-muted">Belum ada data obat.</td></tr>';
                    return;
                }
                data.forEach(item => {
                    const row = `
                        <tr>
                            <td class="fw-bold text-dark">${escapeHtml(item.name)}</td>
                            <td class="text-center">
                                <span class="badge ${item.stock < 10 ? 'bg-danger' : 'bg-success'} fs-6 rounded-pill px-3">
                                    ${item.stock}
                                </span>
                            </td>
                            <td class="text-center text-muted text-uppercase small fw-bold">${escapeHtml(item.unit)}</td>
        <td class="text-end" style="white-space: nowrap;">
            <div class="d-flex justify-content-end align-items-center gap-2">
                <div class="btn-group" role="group">
                    <button class="btn btn-sm btn-outline-danger" onclick="updateStock(${item.id}, -1)"><i class="fas fa-minus"></i></button>
                    <button class="btn btn-sm btn-outline-success" onclick="updateStock(${item.id}, 1)"><i class="fas fa-plus"></i></button>
                </div>
                <button class="btn btn-sm btn-light text-danger" onclick="deleteStock(${item.id})" title="Hapus"><i class="fas fa-trash-alt"></i></button>
                                </div>
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
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
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
            <a href="https://wa.me/6281241865310" class="social-icon-link" target="_blank"><i class="fab fa-whatsapp"></i></a>
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

<script>
document.addEventListener("DOMContentLoaded", function() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
    }
});
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

    /* Dark Mode Styles */
    body.dark-mode {
        background: #121212 !important;
        color: #e0e0e0 !important;
    }
    body.dark-mode .card, 
    body.dark-mode .modal-content-custom,
    body.dark-mode .glass-panel,
    body.dark-mode .person-card {
        background-color: #1e1e1e !important;
        color: #e0e0e0 !important;
        border-color: #444 !important;
    }
    body.dark-mode .text-muted {
        color: #bbb !important;
    }
    body.dark-mode .form-control {
        background-color: #2d2d2d;
        border-color: #444;
        color: #fff;
    }
    body.dark-mode .main-navbar {
        background-color: #1e1e1e !important;
        border-bottom: 1px solid #444;
    }
    body.dark-mode .nav-item-custom {
        color: #ddd;
    }
    body.dark-mode footer {
        background-color: #000 !important;
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
                <a href="https://wa.me/6281241865310" class="social-icon-link" target="_blank"><i class="fab fa-whatsapp"></i></a>
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
                            <a href="whatsapp://send?phone=6281241865310"><i class="fab fa-whatsapp fa-lg text-success ms-2"></i></a>
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

        // Full Screen Toggle
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
    </script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

HTML_SICK_LIST = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generator Surat Sakit</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>body{background:#f4f7f6; font-family:'Segoe UI',sans-serif;}</style>
</head>
<body>
    {{ navbar|safe }}
    <div class="container py-5">
        <div class="card shadow border-0 rounded-4">
            <div class="card-header bg-white py-3 border-0">
                <h4 class="fw-bold mb-0 text-success"><i class="fas fa-file-medical me-2"></i> Generator Surat Sakit</h4>
            </div>
            <div class="card-body p-4">
                <div class="table-responsive">
                    <table class="table table-hover align-middle">
                        <thead class="table-light">
                            <tr>
                                <th>Tanggal</th>
                                <th>Nama Pasien</th>
                                <th>Diagnosa</th>
                                <th>Aksi</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for p in patients %}
                            <tr>
                                <td>{{ (p.finished_at or p.created_at).split(' ')[1] }} WITA</td>
                                <td class="fw-bold">{{ p.name }}</td>
                                <td>{{ p.diagnosis }}</td>
                                <td>
                                    <form action="/surat-sakit/print/{{ p.id }}" method="get" target="_blank" class="d-flex gap-2">
                                        <input type="number" name="days" class="form-control form-control-sm" style="width:70px" value="3" placeholder="Hari">
                                        <button type="submit" class="btn btn-sm btn-success"><i class="fas fa-print me-1"></i> Print</button>
                                    </form>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
</body>
</html>
"""

HTML_SICK_PRINT = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Surat Keterangan Sakit</title>
    <style>
        body { font-family: 'Times New Roman', serif; padding: 40px; max-width: 800px; margin: auto; }
        .header { text-align: center; border-bottom: 3px double black; padding-bottom: 20px; margin-bottom: 30px; }
        .header h2 { margin: 0; text-transform: uppercase; letter-spacing: 2px; }
        .header p { margin: 5px 0; }
        .content { line-height: 1.6; font-size: 1.1rem; }
        .signature { margin-top: 50px; text-align: right; }
        .signature div { margin-top: 70px; font-weight: bold; text-decoration: underline; }
        @media print { .no-print { display: none; } }
    </style>
</head>
<body onload="window.print()">
    <div class="no-print" style="position:fixed; top:20px; right:20px;">
        <button onclick="window.print()" style="padding:10px 20px; font-size:1.2rem; cursor:pointer;">Cetak PDF</button>
    </div>

    <div class="header">
        <h2>KLINIK KESEHATAN</h2>
        <p>Jl. Contoh No. 123, Kota Samarinda</p>
        <p>Telp: 0812-4186-5310</p>
    </div>

    <div class="content">
        <h3 style="text-align:center; text-decoration:underline; margin-bottom:30px;">SURAT KETERANGAN SAKIT</h3>
        
        <p>Yang bertanda tangan di bawah ini, Dokter Pemeriksa Klinik Kesehatan menerangkan bahwa:</p>
        
        <table style="margin-left: 20px;">
            <tr><td style="width:150px;">Nama</td><td>: <strong>{{ p.name }}</strong></td></tr>
            <tr><td>Umur/Tgl. Lahir</td><td>: -</td></tr>
            <tr><td>Alamat</td><td>: -</td></tr>
            <tr><td>Diagnosa</td><td>: {{ p.diagnosis }}</td></tr>
        </table>
        
        <p>Berdasarkan hasil pemeriksaan medis, pasien tersebut membutuhkan istirahat karena sakit selama <strong>{{ days }} ({{ days_text }})</strong> hari.</p>
        
        <p>Demikian surat keterangan ini dibuat untuk dapat dipergunakan sebagaimana mestinya.</p>
    </div>

    <div class="signature">
        <p>Samarinda, {{ date }}</p>
        <div>dr. Pemeriksa</div>
    </div>
</body>
</html>
"""

HTML_CASHIER = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kasir & Laporan</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>body{background:#f4f7f6; font-family:'Segoe UI',sans-serif;}</style>
</head>
<body>
    {{ navbar|safe }}
    <div class="container py-5">
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card bg-success text-white shadow">
                    <div class="card-body">
                        <h5 class="card-title">Total Pendapatan Hari Ini</h5>
                        <h2 class="display-4 fw-bold" id="grand-total">Rp 0</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card bg-white shadow">
                    <div class="card-body text-center">
                        <h5 class="text-muted">Total Pasien Selesai</h5>
                        <h2 class="display-4 fw-bold text-dark">{{ patients|length }}</h2>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card shadow border-0 rounded-4">
            <div class="card-header bg-white py-3 border-0">
                <h4 class="fw-bold mb-0 text-dark"><i class="fas fa-cash-register me-2"></i> Transaksi Hari Ini</h4>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead class="table-light">
                            <tr>
                                <th class="ps-4">Nama Pasien</th>
                                <th>Layanan</th>
                                <th>Biaya Jasa (Rp)</th>
                                <th>Biaya Obat (Rp)</th>
                                <th>Subtotal</th>
                                <th>Aksi</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for p in patients %}
                            <tr id="row-{{ p.id }}">
                                <td class="ps-4 fw-bold">{{ p.name }}<br><small class="text-muted">{% if p.finished_at %}{{ p.finished_at.split(' ')[1] }} WITA{% else %}{{ p.created_at.split(' ')[1] }}{% endif %}</small></td>
                                <td>{{ p.medical_action }}</td>
                                <td><input type="number" id="fee-doc-{{ p.id }}" class="form-control" value="{{ p.fee_doctor }}" onchange="calcTotal({{ p.id }})"></td>
                                <td><input type="number" id="fee-med-{{ p.id }}" class="form-control" value="{{ p.fee_medicine }}" onchange="calcTotal({{ p.id }})"></td>
                                <td class="fw-bold text-success" id="sub-{{ p.id }}">Rp 0</td>
                                <td>
                                    <button class="btn btn-sm btn-primary" onclick="saveFee({{ p.id }})"><i class="fas fa-save"></i></button>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    <script>
        function formatRp(num) { return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR' }).format(num); }
        
        function calcTotal(id) {
            let doc = parseInt(document.getElementById('fee-doc-'+id).value) || 0;
            let med = parseInt(document.getElementById('fee-med-'+id).value) || 0;
            document.getElementById('sub-'+id).innerText = formatRp(doc + med);
            updateGrandTotal();
        }
        
        function updateGrandTotal() {
            let sum = 0;
            {% for p in patients %}
            sum += (parseInt(document.getElementById('fee-doc-{{ p.id }}').value)||0) + (parseInt(document.getElementById('fee-med-{{ p.id }}').value)||0);
            {% endfor %}
            document.getElementById('grand-total').innerText = formatRp(sum);
        }

        function saveFee(id) {
            let doc = document.getElementById('fee-doc-'+id).value;
            let med = document.getElementById('fee-med-'+id).value;
            fetch('/api/kasir/update', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id: id, fee_doctor: doc, fee_medicine: med})
            }).then(r=>r.json()).then(d => {
                alert('Tersimpan!');
            });
        }
        
        // Init
        {% for p in patients %}
        calcTotal({{ p.id }});
        {% endfor %}
    </script>
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
</body>
</html>
"""

HTML_PATIENT_DB = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Database Pasien</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>body{background:#f4f7f6; font-family:'Segoe UI',sans-serif;}</style>
</head>
<body>
    {{ navbar|safe }}
    <div class="container py-5">
        <div class="card shadow border-0 rounded-4">
            <div class="card-header bg-white py-4 border-0 text-center">
                <h3 class="fw-bold text-primary"><i class="fas fa-database me-2"></i> Database Riwayat Pasien</h3>
                <div class="col-md-6 mx-auto mt-3">
                    <form method="get" class="d-flex gap-2">
                        <input type="text" name="q" class="form-control form-control-lg" placeholder="Cari Nama / No HP..." value="{{ request.args.get('q', '') }}">
                        <button class="btn btn-primary btn-lg"><i class="fas fa-search"></i></button>
                    </form>
                </div>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Tanggal</th>
                                <th>Nama</th>
                                <th>Keluhan</th>
                                <th>Diagnosa</th>
                                <th>Resep</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for p in patients %}
                            <tr>
                                <td>{{ p.created_at.split(' ')[0] }}</td>
                                <td class="fw-bold">{{ p.name }}<br><small class="text-muted">{{ p.phone }}</small></td>
                                <td>{{ p.complaint }}</td>
                                <td><span class="badge bg-info text-dark">{{ p.diagnosis }}</span></td>
                                <td class="small">{{ p.prescription }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    {% if not patients %}
                    <div class="text-center py-5 text-muted">Data tidak ditemukan.</div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
</body>
</html>
"""

HTML_SEARCH = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cari Pasien Lama</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body{background:#f4f7f6; font-family:'Segoe UI',sans-serif; min-height: 100vh; display: flex; flex-direction: column;}
        .modal-overlay {
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.6); backdrop-filter: blur(5px); z-index: 9999;
            justify-content: center; align-items: center;
        }
        .modal-card {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.5);
            border-radius: 20px;
            padding: 30px;
            width: 90%;
            max-width: 400px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            animation: popUp 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        @keyframes popUp { from { transform: scale(0.8); opacity: 0; } to { transform: scale(1); opacity: 1; } }
    </style>
</head>
<body>
    {{ navbar|safe }}
    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card shadow border-0 rounded-4">
                    <div class="card-body p-5 text-center">
                        <h2 class="fw-bold mb-4 text-primary">Pencarian Pasien Lama</h2>
                        <form method="get" class="mb-5">
                            <div class="input-group input-group-lg">
                                <input type="text" name="q" class="form-control" placeholder="Masukkan Nama atau No HP..." value="{{ request.args.get('q', '') }}">
                                <button class="btn btn-primary px-4"><i class="fas fa-search me-2"></i> CARI</button>
                            </div>
                        </form>
                        
                        {% if patients %}
                        <div class="list-group text-start">
                            {% for p in patients %}
                            <div class="list-group-item list-group-item-action d-flex justify-content-between align-items-center p-3" style="cursor: pointer;" 
                             onclick='showPlayerCard({{ p | tojson | safe }})'>
                                <div>
                                    <h5 class="mb-1 fw-bold">{{ p.name }}</h5>
                                    <small class="text-muted"><i class="fas fa-phone me-1"></i> {{ p.phone }}</small>
                                </div>
                                <button class="btn btn-success rounded-pill px-4 fw-bold">PILIH <i class="fas fa-arrow-right ms-2"></i></button>
                            </div>
                            {% endfor %}
                        </div>
                        {% elif request.args.get('q') %}
                        <div class="alert alert-warning">Pasien tidak ditemukan.</div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- PLAYER CARD MODAL -->
    <div id="player-card-modal" class="modal-overlay" onclick="closePlayerCard()">
        <div class="modal-card" onclick="event.stopPropagation()" style="max-width: 500px; max-height: 90vh; overflow-y: auto;">
            <div class="text-end">
                <button class="btn btn-sm btn-danger rounded-circle" onclick="closePlayerCard()"><i class="fas fa-times"></i></button>
            </div>
            
            <div class="text-center mb-3">
                <div class="bg-gradient bg-success text-white rounded-circle d-flex align-items-center justify-content-center mx-auto shadow-lg" style="width: 80px; height: 80px; font-size: 2.5rem;">
                    <i class="fas fa-user"></i>
                </div>
                <h4 class="fw-bold text-uppercase mt-2 mb-0" id="pc-name" style="letter-spacing: 1px;">Nama Pasien</h4>
                <small class="text-muted font-monospace" id="pc-phone">08xxxx</small>
            </div>
            
            <div class="row g-2 text-start mb-4">
                 <!-- Status -->
                 <div class="col-6">
                     <div class="p-2 bg-light rounded border h-100">
                         <small class="text-muted d-block fw-bold" style="font-size:0.7rem;"><i class="fas fa-info-circle text-info me-1"></i> STATUS</small>
                         <span id="pc-status" class="fw-bold text-dark small">-</span>
                     </div>
                 </div>
                 <!-- Times -->
                 <div class="col-6">
                     <div class="p-2 bg-light rounded border h-100">
                         <small class="text-muted d-block fw-bold" style="font-size:0.7rem;"><i class="fas fa-clock text-warning me-1"></i> MASUK/KELUAR</small>
                         <div style="font-size:0.75rem;">
                             In: <span id="pc-created" class="fw-bold">-</span><br>
                             Out: <span id="pc-finished" class="fw-bold">-</span>
                         </div>
                     </div>
                 </div>
                 
                 <!-- Details -->
                 <div class="col-12">
                     <div class="p-2 bg-white rounded border shadow-sm mt-2">
                        <small class="text-success fw-bold text-uppercase" style="font-size:0.7rem;"><i class="fas fa-comment-medical me-1"></i> Keluhan</small>
                        <div id="pc-complaint" class="text-dark small fw-bold ms-3">-</div>
                     </div>
                 </div>
                 <div class="col-12">
                     <div class="p-2 bg-white rounded border shadow-sm">
                        <small class="text-primary fw-bold text-uppercase" style="font-size:0.7rem;"><i class="fas fa-stethoscope me-1"></i> Diagnosa</small>
                        <div id="pc-diagnosis" class="text-dark small fw-bold ms-3">-</div>
                     </div>
                 </div>
                 <div class="col-12">
                     <div class="p-2 bg-white rounded border shadow-sm">
                        <small class="text-danger fw-bold text-uppercase" style="font-size:0.7rem;"><i class="fas fa-pills me-1"></i> Resep Obat</small>
                        <div id="pc-prescription" class="text-dark small fw-bold ms-3">-</div>
                     </div>
                 </div>
                 <div class="col-12">
                     <div class="p-2 bg-white rounded border shadow-sm">
                        <small class="text-dark fw-bold text-uppercase" style="font-size:0.7rem;"><i class="fas fa-user-md me-1"></i> Tindakan</small>
                        <div id="pc-action" class="text-dark small fw-bold ms-3">-</div>
                     </div>
                 </div>
            </div>
            
            <button class="btn btn-success w-100 py-3 fw-bold shadow rounded-pill" id="pc-select-btn">
                <i class="fas fa-check-circle me-2"></i> PILIH PASIEN INI
            </button>
        </div>
    </div>

    <script>
        function showPlayerCard(p) {
            document.getElementById('pc-name').innerText = p.name;
            document.getElementById('pc-phone').innerText = p.phone;
            
            const statusMap = {'waiting': 'Menunggu', 'examining': 'Sedang Diperiksa', 'done': 'Selesai', 'cancelled': 'Dibatalkan'};
            document.getElementById('pc-status').innerText = statusMap[p.status] || p.status;
            
            const fmt = (s) => {
                if(!s) return '-';
                try {
                    // split 'YYYY-MM-DD HH:MM:SS'
                    const parts = s.split(' ');
                    if(parts.length < 2) return s;
                    // Format: DD/MM HH:MM
                    const d = new Date(s.replace(' ', 'T'));
                    return d.toLocaleDateString('id-ID', {day:'numeric', month:'short'}) + ' ' + parts[1].substring(0, 5);
                } catch(e) { return s; }
            };
            
            document.getElementById('pc-created').innerText = fmt(p.created_at);
            document.getElementById('pc-finished').innerText = fmt(p.finished_at);
            
            document.getElementById('pc-complaint').innerText = p.complaint || '-';
            document.getElementById('pc-diagnosis').innerText = p.diagnosis || '-';
            document.getElementById('pc-prescription').innerText = p.prescription || '-';
            document.getElementById('pc-action').innerText = p.medical_action || '-';
            
            const btn = document.getElementById('pc-select-btn');
            btn.onclick = function() {
                window.location.href = '/antrean?name=' + encodeURIComponent(p.name) + '&phone=' + encodeURIComponent(p.phone);
            };
            
            document.getElementById('player-card-modal').style.display = 'flex';
        }
        
        function closePlayerCard() {
            document.getElementById('player-card-modal').style.display = 'none';
        }
    </script>
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
</body>
</html>
"""

HTML_STATS = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Statistik Penyakit</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>body{background:#f4f7f6; font-family:'Segoe UI',sans-serif;}</style>
</head>
<body>
    {{ navbar|safe }}
    <div class="container py-5">
        <h2 class="mb-4 fw-bold text-center"><i class="fas fa-chart-pie me-2 text-primary"></i> Statistik Penyakit Terbanyak</h2>
        
        <div class="card shadow border-0 rounded-4 mb-4">
            <div class="card-body p-4">
                <canvas id="diseaseChart" style="max-height: 500px;"></canvas>
            </div>
        </div>
    </div>
    
    <script>
        const ctx = document.getElementById('diseaseChart').getContext('2d');
        const data = {{ chart_data | tojson }};
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Jumlah Pasien',
                    data: data.values,
                    backgroundColor: 'rgba(46, 204, 113, 0.6)',
                    borderColor: 'rgba(46, 204, 113, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    </script>
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
</body>
</html>
"""

HTML_DOWNLOAD_PDF = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Downloading Data...</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js"></script>
    <style>body{font-family:sans-serif; text-align:center; padding-top:50px; background:#f4f7f6;}</style>
</head>
<body>
    <h3>Sedang memproses data PDF...</h3>
    <p>Mohon tunggu sebentar, unduhan akan dimulai otomatis.</p>
    <div id="status">Mengambil data...</div>
    
    <script>
        async function generate() {
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();
            
            try {
                const response = await fetch('/api/export-data');
                const data = await response.json();
                
                document.getElementById('status').innerText = 'Membuat PDF...';
                
                // HEADER
                doc.setFontSize(18);
                doc.text("DATA KLINIK KESEHATAN", 105, 15, null, null, "center");
                doc.setFontSize(10);
                doc.text(`Generated: ${new Date().toLocaleString()}`, 105, 22, null, null, "center");
                
                let y = 30;
                
                // 1. ANTREAN STATS
                doc.setFontSize(14);
                doc.text("1. Statistik Antrean Harian", 14, y);
                y += 5;
                doc.autoTable({
                    startY: y,
                    head: [['Tanggal', 'Jumlah Pasien']],
                    body: data.queue_stats.map(r => [r.d, r.c]),
                    theme: 'grid',
                    headStyles: {fillColor: [46, 204, 113]}
                });
                
                // 2. RIWAYAT PEMERIKSAAN
                doc.addPage();
                doc.text("2. Riwayat Pemeriksaan", 14, 15);
                
                const historyBody = data.history.map(r => [
                    r.created_at.split(' ')[0],
                    r.name,
                    r.status,
                    r.complaint || '-',
                    r.diagnosis || '-',
                    r.prescription || '-',
                    r.medical_action || '-',
                    (r.created_at || '').split(' ')[1] || '-',
                    (r.finished_at || '').split(' ')[1] || '-'
                ]);
                
                doc.autoTable({
                    startY: 20,
                    head: [['Tgl', 'Nama', 'Status', 'Keluhan', 'Diag', 'Resep', 'Tindakan', 'Masuk', 'Selesai']],
                    body: historyBody,
                    theme: 'grid',
                    styles: {fontSize: 8},
                    headStyles: {fillColor: [46, 204, 113]},
                    columnStyles: {
                        0: {cellWidth: 18},
                        1: {cellWidth: 25},
                        3: {cellWidth: 20},
                        4: {cellWidth: 20},
                        5: {cellWidth: 20},
                        6: {cellWidth: 20}
                    }
                });
                
                // 3. KASIR
                doc.addPage();
                doc.text("3. Laporan Kasir (Pendapatan)", 14, 15);
                
                let grandTotal = 0;
                let dailyRevenue = {};
                
                const cashierBody = data.cashier.map(r => {
                    const sub = (r.fee_doctor || 0) + (r.fee_medicine || 0);
                    grandTotal += sub;
                    
                    const date = r.created_at.split(' ')[0];
                    if(!dailyRevenue[date]) dailyRevenue[date] = 0;
                    dailyRevenue[date] += sub;
                    
                    return [
                        date,
                        r.name,
                        r.medical_action || '-',
                        r.fee_doctor || 0,
                        r.fee_medicine || 0,
                        sub
                    ];
                });
                
                doc.autoTable({
                    startY: 20,
                    head: [['Tgl', 'Nama', 'Layanan', 'Jasa (Rp)', 'Obat (Rp)', 'Subtotal (Rp)']],
                    body: cashierBody,
                    theme: 'grid',
                    styles: {fontSize: 9},
                    headStyles: {fillColor: [46, 204, 113]}
                });
                
                // Daily Totals
                let finalY = doc.lastAutoTable.finalY + 10;
                
                if (finalY > 250) { doc.addPage(); finalY = 20; }
                
                doc.text("Total Pendapatan Per Tanggal:", 14, finalY);
                finalY += 5;
                
                const dailyBody = Object.keys(dailyRevenue).map(d => [d, dailyRevenue[d].toLocaleString('id-ID')]);
                
                doc.autoTable({
                    startY: finalY,
                    head: [['Tanggal', 'Total Pendapatan (Rp)']],
                    body: dailyBody,
                    theme: 'striped',
                    headStyles: {fillColor: [255, 215, 0], textColor: [0,0,0]}
                });
                
                finalY = doc.lastAutoTable.finalY + 10;
                doc.setFontSize(12);
                doc.text(`Total Pendapatan Keseluruhan: Rp ${grandTotal.toLocaleString('id-ID')}`, 14, finalY);
                
                document.getElementById('status').innerText = 'Selesai! Mengunduh...';
                doc.save('Data_Klinik_Delima.pdf');
                
                setTimeout(() => {
                    document.body.innerHTML = "<h3>Unduhan Selesai!</h3><button style='padding:10px 20px; font-size:16px; cursor:pointer;' onclick='window.history.back()'>Kembali</button>";
                }, 1000);
                
            } catch(e) {
                console.error(e);
                document.getElementById('status').innerText = 'Error: ' + e.message;
            }
        }
        
        window.onload = generate;
    </script>
</body>
</html>
"""

HTML_BOOKING = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Booking Janji Temu</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>body{background:#f4f7f6; font-family:'Segoe UI',sans-serif;}</style>
</head>
<body>
    {{ navbar|safe }}
    <div class="container py-5">
        <div class="card shadow border-0 rounded-4" style="max-width: 600px; margin: auto;">
            <div class="card-body p-5">
                <h3 class="fw-bold text-center mb-4 text-primary"><i class="fas fa-calendar-check me-2"></i> Booking Janji Temu</h3>
                <form id="booking-form" onsubmit="submitBooking(event)">
                    <div class="mb-3">
                        <label class="fw-bold mb-1">Nama Pasien</label>
                        <input type="text" id="b-name" class="form-control form-control-lg" required>
                    </div>
                    <div class="mb-3">
                        <label class="fw-bold mb-1">Nomor WhatsApp</label>
                        <input type="tel" id="b-phone" class="form-control form-control-lg" required>
                    </div>
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="fw-bold mb-1">Tanggal Kunjungan</label>
                            <input type="date" id="b-date" class="form-control form-control-lg" required>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="fw-bold mb-1">Jam (Estimasi)</label>
                            <input type="time" id="b-time" class="form-control form-control-lg" required>
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary w-100 btn-lg rounded-pill mt-3">Kirim Booking</button>
                </form>
                <div id="success-msg" class="alert alert-success mt-3" style="display:none;">
                    Booking Berhasil! Silakan datang sesuai jadwal.
                </div>
                <div class="text-center mt-3"><a href="/booking-list" class="text-muted small text-decoration-none">Admin: Lihat Daftar</a></div>
            </div>
        </div>
    </div>
    <script>
        function submitBooking(e) {
            e.preventDefault();
            const data = {
                name: document.getElementById('b-name').value,
                phone: document.getElementById('b-phone').value,
                date: document.getElementById('b-date').value,
                time: document.getElementById('b-time').value
            };
            fetch('/api/booking/add', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            }).then(r => r.json()).then(res => {
                if(res.success) {
                    document.getElementById('booking-form').reset();
                    document.getElementById('success-msg').style.display = 'block';
                }
            });
        }
    </script>
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
</body>
</html>
"""

HTML_FINANCE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Keuangan</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>body{background:#f4f7f6; font-family:'Segoe UI',sans-serif;}</style>
</head>
<body>
    {{ navbar|safe }}
    <div class="container py-5">
        <h2 class="mb-4 fw-bold text-center"><i class="fas fa-chart-line me-2 text-success"></i> Dashboard Keuangan & Tren</h2>
        
        <div class="card shadow border-0 rounded-4 mb-4">
            <div class="card-body p-4">
                <canvas id="financeChart" style="max-height: 500px;"></canvas>
            </div>
        </div>
    </div>
    
    <script>
        const ctx = document.getElementById('financeChart').getContext('2d');
        const data = {{ chart_data | tojson }};
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Pendapatan Bulanan (Rp)',
                    data: data.values,
                    backgroundColor: 'rgba(46, 204, 113, 0.2)',
                    borderColor: 'rgba(46, 204, 113, 1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                scales: {
                    y: { beginAtZero: true }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR' }).format(context.parsed.y);
                                }
                                return label;
                            }
                        }
                    }
                }
            }
        });
    </script>
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
</body>
</html>
"""

HTML_EXPIRY = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alert Kedaluwarsa Obat</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>body{background:#f4f7f6; font-family:'Segoe UI',sans-serif;}</style>
</head>
<body>
    {{ navbar|safe }}
    <div class="container py-5">
        <h2 class="mb-4 fw-bold text-danger text-center"><i class="fas fa-exclamation-triangle me-2"></i> Tracker Kedaluwarsa Obat</h2>
        <div class="card shadow border-0 rounded-4">
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Nama Obat</th>
                                <th>Stok</th>
                                <th>Tgl Kedaluwarsa</th>
                                <th>Status</th>
                                <th>Aksi</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for m in medicines %}
                            <tr class="{{ 'table-danger' if m.is_expiring else '' }}">
                                <td class="fw-bold">{{ m.name }}</td>
                                <td>{{ m.stock }} {{ m.unit }}</td>
                                <td>
                                    {% if m.expiry_date %}
                                        {{ m.expiry_date }}
                                    {% else %}
                                        <span class="text-muted fst-italic">Belum diatur</span>
                                    {% endif %}
                                </td>
                                <td>
                                    {% if m.is_expiring %}
                                        <span class="badge bg-danger">KEDALUWARSA &lt; 30 HARI</span>
                                    {% else %}
                                        <span class="badge bg-success">Aman</span>
                                    {% endif %}
                                </td>
                                <td>
                                    <form class="d-flex gap-2" onsubmit="updateExpiry(event, {{ m.id }})">
                                        <input type="date" id="date-{{ m.id }}" class="form-control form-control-sm" value="{{ m.expiry_date }}">
                                        <button class="btn btn-sm btn-primary">Update</button>
                                    </form>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    <script>
        function updateExpiry(e, id) {
            e.preventDefault();
            const date = document.getElementById('date-' + id).value;
            fetch('/api/stock/update-expiry', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id: id, date: date})
            }).then(() => location.reload());
        }
    </script>
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
</body>
</html>
"""

HTML_RECEIPT_LIST = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cetak Struk</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>body{background:#f4f7f6; font-family:'Segoe UI',sans-serif;}</style>
</head>
<body>
    {{ navbar|safe }}
    <div class="container py-5">
        <h2 class="mb-4 fw-bold text-center text-dark"><i class="fas fa-receipt me-2"></i> Cetak Struk Pembayaran</h2>
        <div class="card shadow border-0 rounded-4">
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Tanggal</th>
                                <th>Nama Pasien</th>
                                <th>Total Biaya</th>
                                <th>Aksi</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for p in patients %}
                            <tr>
                                <td>{{ (p.finished_at or p.created_at).split(' ')[0] }}</td>
                                <td class="fw-bold">{{ p.name }}</td>
                                <td class="fw-bold text-success">Rp {{ "{:,.0f}".format((p.fee_doctor or 0) + (p.fee_medicine or 0)).replace(',','.') }}</td>
                                <td>
                                    <a href="/print-receipt/{{ p.id }}" target="_blank" class="btn btn-sm btn-dark"><i class="fas fa-print me-1"></i> Cetak Struk</a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
</body>
</html>
"""

HTML_RECEIPT_PRINT = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Struk Pembayaran</title>
    <style>
        body { font-family: 'Courier New', monospace; font-size: 12px; width: 58mm; margin: 0; padding: 10px; color: #000; }
        .text-center { text-align: center; }
        .fw-bold { font-weight: bold; }
        .line { border-bottom: 1px dashed #000; margin: 5px 0; }
        .flex { display: flex; justify-content: space-between; }
        @media print { .no-print { display: none; } }
    </style>
</head>
<body onload="window.print()">
    <div class="no-print">
        <button onclick="window.print()">PRINT</button>
    </div>
    <div class="text-center fw-bold" style="font-size: 14px;">KLINIK KESEHATAN</div>
    <div class="text-center">Jl. Contoh No. 123</div>
    <div class="text-center">Samarinda</div>
    <div class="line"></div>
    <div class="flex"><span>Tgl:</span> <span>{{ date }}</span></div>
    <div class="flex"><span>Pasien:</span> <span>{{ p.name }}</span></div>
    <div class="line"></div>
    <div class="flex"><span>Jasa Dokter</span> <span>{{ p.fee_doctor }}</span></div>
    <div class="flex"><span>Obat</span> <span>{{ p.fee_medicine }}</span></div>
    <div class="line"></div>
    <div class="flex fw-bold" style="font-size: 14px;"><span>TOTAL</span> <span>Rp {{ total }}</span></div>
    <div class="line"></div>
    <div class="text-center" style="margin-top: 10px;">Terima Kasih</div>
    <div class="text-center">Semoga Lekas Sembuh</div>
</body>
</html>
"""

HTML_WA_REMINDER = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp Reminder</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>body{background:#f4f7f6; font-family:'Segoe UI',sans-serif;}</style>
</head>
<body>
    {{ navbar|safe }}
    <div class="container py-5">
        <h2 class="mb-4 fw-bold text-center text-success"><i class="fab fa-whatsapp me-2"></i> WhatsApp Reminder Pasien</h2>
        <div class="card shadow border-0 rounded-4">
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>No Antrean</th>
                                <th>Nama Pasien</th>
                                <th>No WhatsApp</th>
                                <th>Aksi Reminder</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for p in patients %}
                            <tr>
                                <td class="fw-bold fs-5 text-center">{{ p.number }}</td>
                                <td class="fw-bold">{{ p.name }}</td>
                                <td>{{ p.phone }}</td>
                                <td>
                                    <a href="https://wa.me/{{ p.phone|replace('0', '62', 1) if p.phone.startswith('0') else p.phone }}?text=Halo%20{{ p.name }},%20giliran%20Anda%203%20nomor%20lagi.%20Harap%20bersiap%20di%20ruang%20tunggu.%20Terima%20kasih." 
                                       target="_blank" class="btn btn-success text-white fw-bold">
                                        <i class="fab fa-whatsapp me-1"></i> Ingatkan
                                    </a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    {% if not patients %}
                    <div class="text-center py-5 text-muted">Tidak ada antrean menunggu.</div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
</body>
</html>
"""

HTML_BOOKING_LIST = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daftar Janji Temu</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>body{background:#f4f7f6; font-family:'Segoe UI',sans-serif; min-height: 100vh; display: flex; flex-direction: column;}</style>
</head>
<body>
    {{ navbar|safe }}
    <div class="container py-5">
        <h2 class="mb-4 fw-bold text-center text-primary"><i class="fas fa-calendar-alt me-2"></i> Daftar Janji Temu</h2>
        <div class="card shadow border-0 rounded-4">
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Tanggal</th>
                                <th>Jam</th>
                                <th>Nama Pasien</th>
                                <th>No WhatsApp</th>
                                <th>Dibuat</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for a in appointments %}
                            <tr>
                                <td class="fw-bold">{{ a.date }}</td>
                                <td><span class="badge bg-info text-dark">{{ a.time }}</span></td>
                                <td class="fw-bold">{{ a.name }}</td>
                                <td>
                                    <a href="https://wa.me/{{ a.phone|replace('0', '62', 1) if a.phone.startswith('0') else a.phone }}" target="_blank" class="text-decoration-none">
                                        <i class="fab fa-whatsapp text-success"></i> {{ a.phone }}
                                    </a>
                                </td>
                                <td class="text-muted small">{{ a.created_at }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    {% if not appointments %}
                    <div class="text-center py-5 text-muted">Belum ada janji temu.</div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <footer class="text-center py-4 mt-auto" style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid rgba(0,0,0,0.1);">
        <h5 class="fw-bold mb-1" style="color: #333; letter-spacing: 1px;">KLINIK KESEHATAN</h5>
        <small class="text-muted fw-bold" style="font-size: 0.8rem;">© 2026 KLINIK KESEHATAN. All Rights Reserved.</small>
    </footer>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=False, port=5000)
