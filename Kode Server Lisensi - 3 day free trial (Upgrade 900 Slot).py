from flask import Flask, request, jsonify, render_template_string
import sqlite3
import random
import string
import os
from datetime import datetime, timedelta

app = Flask(__name__)
DB_FILE = "licenses.db"

# --- HTML TEMPLATES ---

# Template Admin Utama (Standard Lifetime Keys)
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>License Manager - Lifetime</title>
    <style>
        body { font-family: monospace; background: #1a1a1a; color: #0f0; padding: 20px; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #333; padding: 8px; text-align: left; }
        th { background: #333; }
        tr:nth-child(even) { background: #222; }
        .used { color: #f00; font-weight: bold; }
        .active { color: #0f0; }
        .expired { color: #888; text-decoration: line-through; }
        .nav { margin-bottom: 20px; border-bottom: 1px solid #444; padding-bottom: 10px; }
        a { color: #0ff; text-decoration: none; margin-right: 15px; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="nav">
        <strong>MODE: LIFETIME LICENSES</strong> | 
        <i><u><a href="/admin/trials">serial key free trial for 3 day</a></u></i>
    </div>
    
    <h1>BANK SERIAL NUMBER (LIFETIME)</h1>
    <p>
        Total: {{ total }} | 
        <span style="color:#f00">Used: {{ used_count }}</span> | 
        <span style="color:#0f0">Available: {{ available }}</span>
    </p>
    
    <table>
        <tr>
            <th>ID</th>
            <th>Serial Key</th>
            <th>Type</th>
            <th>Status</th>
            <th>Hardware ID (Locked To)</th>
        </tr>
        {% for lic in licenses %}
        <tr>
            <td>{{ lic['id'] }}</td>
            <td>{{ lic['serial_key'] }}</td>
            <td style="color: #ffff00;">{{ lic['type']|upper }}</td>
            <td class="{{ lic['status'] }}">{{ lic['status']|upper }}</td>
            <td>{{ lic['hwid'] if lic['hwid'] else '-' }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

# Template Admin Trial (3 Days)
ADMIN_TRIAL_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>License Manager - Free Trial</title>
    <style>
        body { font-family: monospace; background: #0f0f1a; color: #0ff; padding: 20px; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #333; padding: 8px; text-align: left; }
        th { background: #223; }
        tr:nth-child(even) { background: #1a1a2e; }
        .used { color: #ffaa00; font-weight: bold; } /* Orange for running trial */
        .active { color: #0f0; }
        .expired { color: #f00; font-weight: bold; }
        .nav { margin-bottom: 20px; border-bottom: 1px solid #444; padding-bottom: 10px; }
        a { color: #0f0; text-decoration: none; margin-right: 15px; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="nav">
        <a href="/admin"> < Back to Lifetime Licenses</a> | 
        <strong>MODE: FREE TRIAL (3 DAYS)</strong>
    </div>
    
    <h1>BANK SERIAL NUMBER (TRIAL 3 DAYS)</h1>
    <p>
        Total Trial Keys: {{ total }} | 
        Running: {{ used_count }} | 
        Expired: {{ expired_count }} |
        Available: {{ available }}
    </p>
    
    <table>
        <tr>
            <th>ID</th>
            <th>Serial Key</th>
            <th>Status</th>
            <th>Activation Date</th>
            <th>Expires At</th>
            <th>Hardware ID</th>
        </tr>
        {% for lic in licenses %}
        <tr>
            <td>{{ lic['id'] }}</td>
            <td>{{ lic['serial_key'] }}</td>
            <td class="{{ lic['status'] }}">{{ lic['status']|upper }}</td>
            <td>{{ format_indo(lic['activated_at']) if lic['activated_at'] else '-' }}</td>
            <td>
                {% if lic['activated_at'] and lic['status'] == 'used' %}
                    {{ format_indo(lic['activated_at']|to_datetime + timedelta(days=3)) }}
                {% elif lic['status'] == 'expired' %}
                    EXPIRED
                {% else %}
                    -
                {% endif %}
            </td>
            <td>{{ lic['hwid'] if lic['hwid'] else '-' }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

# --- DATABASE FUNCTIONS ---

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def init_or_migrate_db():
    """
    Fungsi pintar untuk inisialisasi atau UPGRADE database lama
    tanpa menghapus data yang sudah ada (2 user existing aman).
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Buat tabel jika belum ada (Schema Lama)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_key TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'active',
            hwid TEXT
        )
    ''')
    
    # 2. Cek apakah kolom baru 'type' dan 'activated_at' sudah ada? (Schema Baru)
    cur.execute("PRAGMA table_info(licenses)")
    columns = [info[1] for info in cur.fetchall()]
    
    if 'type' not in columns:
        print("Migrating DB: Adding 'type' column...")
        cur.execute("ALTER TABLE licenses ADD COLUMN type TEXT DEFAULT 'standard'")
        
    if 'activated_at' not in columns:
        print("Migrating DB: Adding 'activated_at' column...")
        cur.execute("ALTER TABLE licenses ADD COLUMN activated_at TIMESTAMP")
        
    conn.commit()
    conn.close()

def generate_serial(prefix="SOLAR"):
    # Format: PREFIX-XXXX-XXXX-XXXX
    parts = [prefix]
    for _ in range(3):
        part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        parts.append(part)
    return '-'.join(parts)

def update_expired_trials():
    """Cek semua lisensi trial yang sedang berjalan, hanguskan jika > 3 hari."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    now = datetime.now()
    cutoff_date = now - timedelta(days=3)
    
    # Update status ke 'expired' jika type='trial', status='used', dan aktivasi < 3 hari lalu
    cur.execute('''
        UPDATE licenses 
        SET status = 'expired' 
        WHERE type = 'trial' AND status = 'used' AND activated_at < ?
    ''', (cutoff_date,))
    
    conn.commit()
    conn.close()

# --- ROUTES ---

@app.route('/')
def index():
    return "Solar System License Server Online v2.0"

@app.route('/setup')
def setup():
    """
    SETUP STANDARD: Menambah kunci Lifetime sampai 900 slot.
    """
    init_or_migrate_db()
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Hitung kunci STANDARD yang ada
    cur.execute("SELECT count(*) FROM licenses WHERE type = 'standard'")
    count = cur.fetchone()[0]
    
    TARGET_COUNT = 900
    
    if count >= TARGET_COUNT:
        conn.close()
        return f"Standard Keys already at target ({count}). No action taken."
    
    needed = TARGET_COUNT - count
    keys = []
    for _ in range(needed):
        keys.append((generate_serial("SOLAR"), 'active', 'standard'))
    
    try:
        cur.executemany("INSERT INTO licenses (serial_key, status, type) VALUES (?, ?, ?)", keys)
        conn.commit()
        msg = f"SUCCESS: Added {needed} NEW Standard keys. Total Standard: {TARGET_COUNT}."
    except Exception as e:
        msg = f"Error: {str(e)}"
    finally:
        conn.close()
        
    return msg

@app.route('/setup_trials')
def setup_trials():
    """
    SETUP BARU: Menambah kunci TRIAL 3 HARI hingga 900 slot.
    (Menambahkan 800 lagi jika sebelumnya sudah ada 100).
    Akses url ini sekali untuk generate kunci trial.
    """
    init_or_migrate_db()
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Hitung kunci TRIAL yang ada
    cur.execute("SELECT count(*) FROM licenses WHERE type = 'trial'")
    count = cur.fetchone()[0]
    
    TARGET_TRIAL = 900 # TARGET BARU: 900 SLOT TRIAL (agar genap)
    
    if count >= TARGET_TRIAL:
        conn.close()
        return f"Trial Keys already at target ({count}). No action taken."
    
    needed = TARGET_TRIAL - count
    keys = []
    for _ in range(needed):
        # Format kunci trial: TRIAL-XXXX...
        keys.append((generate_serial("TRIAL"), 'active', 'trial'))
    
    try:
        cur.executemany("INSERT INTO licenses (serial_key, status, type) VALUES (?, ?, ?)", keys)
        conn.commit()
        msg = f"SUCCESS: Added {needed} NEW Trial keys. Total Trial: {TARGET_TRIAL}."
    except Exception as e:
        msg = f"Error: {str(e)}"
    finally:
        conn.close()
        
    return msg

@app.route('/activate', methods=['POST'])
def activate():
    # Pastikan data expired diupdate sebelum validasi
    update_expired_trials()
    
    data = request.json
    if not data or 'key' not in data or 'hwid' not in data:
        return jsonify({'status': 'error', 'message': 'Invalid request'}), 400
    
    serial_key = data['key'].strip().upper()
    hwid = data['hwid']
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Ambil info lisensi
    cur.execute("SELECT * FROM licenses WHERE serial_key = ?", (serial_key,))
    license_row = cur.fetchone()
    
    if not license_row:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Invalid Serial Key'}), 404
        
    status = license_row['status']
    registered_hwid = license_row['hwid']
    lic_type = license_row['type']
    
    # --- LOGIKA AKTIVASI ---
    
    if status == 'expired':
        conn.close()
        return jsonify({'status': 'error', 'message': 'This Trial Key has EXPIRED.'}), 403

    if status == 'active':
        # Aktivasi Baru (Baik Standard maupun Trial)
        now = datetime.now()
        cur.execute("""
            UPDATE licenses 
            SET status = 'used', hwid = ?, activated_at = ? 
            WHERE serial_key = ?
        """, (hwid, now, serial_key))
        conn.commit()
        conn.close()
        
        msg = "Activation Successful."
        if lic_type == 'trial':
            msg += " Trial Active for 3 Days."
        else:
            msg += " Lifetime License Locked."
            
        return jsonify({'status': 'success', 'message': msg})
        
    elif status == 'used':
        # Re-aktivasi / Cek Validitas
        if registered_hwid == hwid:
            # Jika Trial, cek lagi apakah waktu habis (double check)
            if lic_type == 'trial':
                activated_at = license_row['activated_at']
                if not activated_at: activated_at = datetime.now() # Fallback safety
                
                if datetime.now() > activated_at + timedelta(days=3):
                    # Ups, ternyata barusan habis
                    cur.execute("UPDATE licenses SET status = 'expired' WHERE serial_key = ?", (serial_key,))
                    conn.commit()
                    conn.close()
                    return jsonify({'status': 'error', 'message': 'Trial Period Ended.'}), 403
            
            conn.close()
            return jsonify({'status': 'success', 'message': 'License Valid.'})
        else:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Key already used on another machine (HWID Mismatch).'}), 403
            
    conn.close()
    return jsonify({'status': 'error', 'message': 'Unknown error'}), 500

@app.route('/admin')
def admin():
    # Halaman Default: Menampilkan Standard Lifetime Keys
    # Update expired trials dulu biar data konsisten
    update_expired_trials()
    
    conn = get_db_connection()
    # Hanya ambil yang standard
    licenses = conn.execute("SELECT * FROM licenses WHERE type = 'standard' OR type IS NULL").fetchall()
    conn.close()
    
    total = len(licenses)
    used = sum(1 for l in licenses if l['status'] == 'used')
    
    return render_template_string(ADMIN_HTML, licenses=licenses, total=total, used_count=used, available=total-used)

@app.route('/admin/trials')
def admin_trials():
    # Halaman Khusus: Menampilkan Trial Keys
    update_expired_trials()
    
    conn = get_db_connection()
    licenses = conn.execute("SELECT * FROM licenses WHERE type = 'trial'").fetchall()
    conn.close()
    
    total = len(licenses)
    used = sum(1 for l in licenses if l['status'] == 'used')
    expired = sum(1 for l in licenses if l['status'] == 'expired')
    available = sum(1 for l in licenses if l['status'] == 'active')
    
    # Helper untuk template (convert string date ke object datetime jika perlu)
    def to_datetime(val):
        if isinstance(val, str):
            return datetime.strptime(val, "%Y-%m-%d %H:%M:%S.%f")
        return val

    # Helper Format Tanggal Indonesia
    def format_indo(dt):
        if not dt: return "-"
        # Mapping nama bulan
        months = {
            "January": "Januari", "February": "Februari", "March": "Maret",
            "April": "April", "May": "Mei", "June": "Juni",
            "July": "Juli", "August": "Agustus", "September": "September",
            "October": "Oktober", "November": "November", "December": "Desember"
        }
        # Format dasar: 21 December 2025, 10:54 PM
        date_str = dt.strftime("%d %B %Y, %I:%M %p")
        # Ganti nama bulan Inggris ke Indonesia
        for eng, indo in months.items():
            date_str = date_str.replace(eng, indo)
        return date_str

    return render_template_string(
        ADMIN_TRIAL_HTML, 
        licenses=licenses, 
        total=total, 
        used_count=used, 
        expired_count=expired,
        available=available,
        timedelta=timedelta,
        to_datetime=to_datetime,
        format_indo=format_indo
    )

if __name__ == '__main__':
    if not os.path.exists(DB_FILE):
        init_or_migrate_db()
    app.run(debug=True)
