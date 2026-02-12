import os
import sqlite3
import datetime
import math
import time
import json
from flask import Flask, request, send_from_directory, render_template_string, redirect, url_for, Response, jsonify
from werkzeug.utils import secure_filename

# --- KONFIGURASI FLASK ---
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB Limit
app.secret_key = "supersecretkey_masjid_al_hijrah"
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'mp4'}

# --- DATABASE SETUP ---
DB_NAME = 'bimbel.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Drop old tables if they exist (Clean Slate)
    tables = ['gallery', 'tutors', 'pricing', 'slots', 'join_requests', 'news', 
              'finance', 'agenda', 'bookings', 'zakat', 'gallery_dakwah', 'suggestions']
    for table in tables:
        c.execute(f'DROP TABLE IF EXISTS {table}')

    # 1. Finance Table
    c.execute('''CREATE TABLE IF NOT EXISTS finance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        type TEXT NOT NULL, -- 'Pemasukan' or 'Pengeluaran'
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        amount INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 2. Agenda Table
    c.execute('''CREATE TABLE IF NOT EXISTS agenda (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        title TEXT NOT NULL,
        speaker TEXT NOT NULL,
        type TEXT NOT NULL, -- 'Jumat' or 'Kajian'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 3. Bookings Table
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        date TEXT NOT NULL,
        purpose TEXT NOT NULL,
        type TEXT NOT NULL, -- 'Ambulan' or 'Fasilitas'
        status TEXT DEFAULT 'Pending', -- 'Pending', 'Approved', 'Rejected'
        contact TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 4. Zakat & Qurban Table
    c.execute('''CREATE TABLE IF NOT EXISTS zakat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        donor_name TEXT NOT NULL,
        type TEXT NOT NULL, -- 'Zakat Fitrah', 'Zakat Mal', 'Qurban Sapi', 'Qurban Kambing'
        amount TEXT NOT NULL, -- Can be money or "1 Ekor"
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 5. Gallery Dakwah Table
    c.execute('''CREATE TABLE IF NOT EXISTS gallery_dakwah (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        image TEXT NOT NULL,
        description TEXT,
        date TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 6. Suggestions Table
    c.execute('''CREATE TABLE IF NOT EXISTS suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        date TEXT NOT NULL,
        status TEXT DEFAULT 'Unread',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

# --- PRAYER TIMES CALCULATION (Samarinda) ---
class PrayTimes:
    def __init__(self, method="MWL"):
        self.method = method
        self.methods = {
            "MWL": {"fajr": 18, "isha": 17},
            "ISNA": {"fajr": 15, "isha": 15},
            "Egypt": {"fajr": 19.5, "isha": 17.5},
            "Makkah": {"fajr": 18.5, "isha": 90},  # minutes
            "Karachi": {"fajr": 18, "isha": 18},
            "Tehran": {"fajr": 17.7, "isha": 14, "maghrib": 4.5, "midnight": "Jafari"},
            "Jafari": {"fajr": 16, "isha": 14, "maghrib": 4, "midnight": "Jafari"}
        }
        self.params = self.methods[method]

    def set_calc_method(self, method):
        if method in self.methods:
            self.params = self.methods[method]

    def get_prayer_times(self, year, month, day, latitude, longitude, timezone):
        return self.compute_times(year, month, day, latitude, longitude, timezone)

    def compute_times(self, year, month, day, lat, lng, tzone):
        d = self.days_since_j2000(year, month, day) + 0.5 - tzone / 24.0
        eqt = self.equation_of_time(d)
        decl = self.sun_declination(d)
        noon = self.compute_mid_day(d - 0.5 + tzone / 24.0)

        times = {
            "Fajr": self.compute_time(180 - self.params["fajr"], decl, lat, noon),
            "Sunrise": self.compute_time(180 - 0.833, decl, lat, noon),
            "Dhuhr": noon,
            "Asr": self.compute_asr(1, decl, lat, noon), # Shafi'i
            "Sunset": self.compute_time(0.833, decl, lat, noon),
            "Maghrib": self.compute_time(0.833, decl, lat, noon) if "maghrib" not in self.params else self.compute_time(self.params["maghrib"], decl, lat, noon),
            "Isha": self.compute_time(self.params["isha"], decl, lat, noon)
        }
        
        # Adjust for timezone
        final_times = {}
        for name, t in times.items():
            final_times[name] = self.adjust_time(t, tzone)
            
        return final_times

    def days_since_j2000(self, year, month, day):
        if month <= 2:
            year -= 1
            month += 12
        a = math.floor(year / 100)
        b = 2 - a + math.floor(a / 4)
        return math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + b - 1524.5

    def equation_of_time(self, d):
        g = self.fix_angle(357.529 + 0.98560028 * d)
        q = self.fix_angle(280.459 + 0.98564736 * d)
        l = self.fix_angle(q + 1.915 * math.sin(math.radians(g)) + 0.020 * math.sin(math.radians(2 * g)))
        e = 23.439 - 0.00000036 * d
        ra = math.degrees(math.atan2(math.cos(math.radians(e)) * math.sin(math.radians(l)), math.cos(math.radians(l)))) / 15.0
        ra = self.fix_hour(ra)
        return q / 15.0 - ra

    def sun_declination(self, d):
        g = self.fix_angle(357.529 + 0.98560028 * d)
        q = self.fix_angle(280.459 + 0.98564736 * d)
        l = self.fix_angle(q + 1.915 * math.sin(math.radians(g)) + 0.020 * math.sin(math.radians(2 * g)))
        e = 23.439 - 0.00000036 * d
        return math.degrees(math.asin(math.sin(math.radians(e)) * math.sin(math.radians(l))))

    def compute_mid_day(self, t):
        t2 = self.equation_of_time(t)
        return 12 - t2

    def compute_time(self, g, decl, lat, noon):
        try:
            d = math.degrees(math.acos((math.sin(math.radians(g)) - math.sin(math.radians(decl)) * math.sin(math.radians(lat))) / (math.cos(math.radians(decl)) * math.cos(math.radians(lat)))))
        except:
            return 0 # Handle polar regions if needed, unlikely for Samarinda
        return noon - d / 15.0 if g > 90 else noon + d / 15.0 # Logic simplified for brevity

    def compute_asr(self, step, decl, lat, noon):
        try:
            d = math.degrees(math.acos((math.sin(math.atan(step + math.tan(math.radians(abs(lat - decl)))))-math.sin(math.radians(decl))*math.sin(math.radians(lat)))/(math.cos(math.radians(decl))*math.cos(math.radians(lat)))))
        except:
             return 0
        return noon + d / 15.0

    def fix_angle(self, a):
        return a - 360.0 * math.floor(a / 360.0)

    def fix_hour(self, a):
        return a - 24.0 * math.floor(a / 24.0)

    def adjust_time(self, t, tzone):
        t += tzone - 8 # Base is calculated relative to GMT, we just add timezone
        t = self.fix_hour(t)
        hours = int(t)
        minutes = int((t - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"

# Samarinda Coordinates
LAT = -0.502106
LNG = 117.153709
TZ = 8 # WITA

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- FRONTEND ASSETS ---

STYLES_HTML = """
    <style>
        :root {
            --primary-glass: rgba(255, 255, 255, 0.1);
            --secondary-glass: rgba(255, 255, 255, 0.05);
            --border-glass: rgba(255, 255, 255, 0.2);
            --blur-amount: 20px;
            --text-color: #ffffff;
            --accent-color: #00ffcc; /* Cyan/Teal Neon */
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: #1a1a1a; /* Fallback */
            background-image: url('https://images.unsplash.com/photo-1542452377-9d7f08819077?q=80&w=2070&auto=format&fit=crop'); /* Modern Mosque/Abstract Background */
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: var(--text-color);
            margin: 0;
            padding-bottom: 100px; /* Space for bottom nav */
            min-height: 100vh;
        }
        
        .overlay {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(10px);
            z-index: -1;
        }

        /* Glassmorphism Card */
        .glass-card {
            background: var(--primary-glass);
            backdrop-filter: blur(var(--blur-amount));
            -webkit-backdrop-filter: blur(var(--blur-amount));
            border: 1px solid var(--border-glass);
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
            transition: transform 0.3s ease;
        }
        
        .glass-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.15);
        }

        /* TOP NAV (Horizontal Scroll) */
        .top-nav-container {
            position: sticky;
            top: 0;
            z-index: 1000;
            background: rgba(0,0,0,0.3);
            backdrop-filter: blur(15px);
            padding: 15px 0;
            border-bottom: 1px solid var(--border-glass);
        }
        
        .top-nav-scroll {
            display: flex;
            gap: 15px;
            overflow-x: auto;
            padding: 0 15px;
            scrollbar-width: none;
            -ms-overflow-style: none;
        }
        .top-nav-scroll::-webkit-scrollbar { display: none; }
        
        .nav-item-top {
            flex: 0 0 100px;
            height: 100px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            background: var(--secondary-glass);
            border: 1px solid var(--border-glass);
            border-radius: 12px;
            color: white;
            text-decoration: none;
            transition: 0.3s;
            padding: 10px;
        }
        
        .nav-item-top:hover, .nav-item-top.active {
            background: var(--accent-color);
            color: #000;
            box-shadow: 0 0 15px var(--accent-color);
            border-color: transparent;
        }
        
        .nav-item-top i {
            font-size: 1.8rem;
            margin-bottom: 8px;
        }
        
        .nav-item-top span {
            font-size: 0.75rem;
            font-weight: 600;
            line-height: 1.2;
        }

        /* BOTTOM NAV */
        .bottom-nav {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            width: 90%;
            max-width: 500px;
            background: rgba(20, 20, 20, 0.85);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border-glass);
            border-radius: 50px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            z-index: 1000;
        }
        
        .bottom-nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            color: rgba(255,255,255,0.6);
            text-decoration: none;
            transition: 0.3s;
        }
        
        .bottom-nav-item:hover {
            color: var(--accent-color);
            transform: scale(1.1);
        }
        
        .bottom-nav-item i {
            font-size: 1.5rem;
            margin-bottom: 4px;
        }
        
        .bottom-nav-item span {
            font-size: 0.7rem;
            font-weight: 600;
        }
        
        .prayer-countdown {
            background: var(--accent-color);
            color: black;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: 800;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 5px;
            box-shadow: 0 0 15px rgba(0, 255, 204, 0.4);
        }

        /* FORMS & TABLES */
        .form-control, .form-select {
            background: rgba(255,255,255,0.1) !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
            color: white !important;
        }
        .form-control::placeholder { color: rgba(255,255,255,0.5); }
        .form-control:focus {
            background: rgba(255,255,255,0.2) !important;
            box-shadow: 0 0 10px rgba(255,255,255,0.2);
            border-color: white !important;
        }
        
        .table {
            color: white !important;
        }
        .table thead {
            background: rgba(255,255,255,0.1);
        }
        .table td, .table th {
            border-color: rgba(255,255,255,0.1) !important;
        }

        /* UTILS */
        .page-title {
            font-weight: 800;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-left: 5px solid var(--accent-color);
            padding-left: 15px;
        }
        
        .btn-custom {
            background: var(--accent-color);
            color: black;
            font-weight: bold;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            transition: 0.3s;
        }
        .btn-custom:hover {
            background: white;
            color: black;
            box-shadow: 0 0 15px rgba(255,255,255,0.5);
        }
        
        .modal-content {
            background: rgba(20, 20, 20, 0.95);
            backdrop-filter: blur(30px);
            border: 1px solid var(--border-glass);
            color: white;
        }
        .btn-close { filter: invert(1); }
    </style>
"""

NAVBAR_HTML = """
<div class="top-nav-container">
    <div class="container">
        <div class="top-nav-scroll">
            <a href="/finance" class="nav-item-top {{ 'active' if active_page == 'finance' }}">
                <i class="fas fa-coins"></i>
                <span>Laporan Kas</span>
            </a>
            <a href="/agenda" class="nav-item-top {{ 'active' if active_page == 'agenda' }}">
                <i class="fas fa-calendar-alt"></i>
                <span>Jadwal Imam</span>
            </a>
            <a href="/booking" class="nav-item-top {{ 'active' if active_page == 'booking' }}">
                <i class="fas fa-hand-holding-heart"></i>
                <span>Peminjaman</span>
            </a>
            <a href="/zakat" class="nav-item-top {{ 'active' if active_page == 'zakat' }}">
                <i class="fas fa-gift"></i>
                <span>Zakat & Qurban</span>
            </a>
            <a href="/gallery-dakwah" class="nav-item-top {{ 'active' if active_page == 'gallery' }}">
                <i class="fas fa-camera-retro"></i>
                <span>Galeri Dakwah</span>
            </a>
            <a href="/suggestion" class="nav-item-top {{ 'active' if active_page == 'suggestion' }}">
                <i class="fas fa-envelope-open-text"></i>
                <span>Kotak Saran</span>
            </a>
        </div>
    </div>
</div>
"""

BOTTOM_NAV_HTML = """
<div class="bottom-nav">
    <a href="javascript:void(0)" class="bottom-nav-item" onclick="fetchPrayerTimes()">
        <div class="prayer-countdown" id="prayer-timer">
            <i class="fas fa-clock"></i> <span id="countdown-text">Loading...</span>
        </div>
    </a>
    
    <a href="/donate" class="bottom-nav-item">
        <i class="fas fa-qrcode"></i>
        <span>Infaq QRIS</span>
    </a>
    
    <a href="/emergency" class="bottom-nav-item text-danger">
        <i class="fas fa-ambulance"></i>
        <span>Darurat</span>
    </a>
</div>

<script>
    async function updatePrayerCountdown() {
        try {
            const response = await fetch('/prayer-times');
            const data = await response.json();
            const now = new Date();
            const currentTimeStr = now.toTimeString().slice(0, 5);
            
            let nextPrayer = null;
            let nextTime = null;
            
            // Times are in format "HH:MM"
            const prayers = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'];
            
            for (let p of prayers) {
                if (data[p] > currentTimeStr) {
                    nextPrayer = p;
                    nextTime = data[p];
                    break;
                }
            }
            
            if (!nextPrayer) {
                // Next is Fajr tomorrow (simplified logic: just show message)
                document.getElementById('countdown-text').innerText = "Istirahat";
                return;
            }
            
            // Calculate diff
            const [h, m] = nextTime.split(':');
            const prayerDate = new Date();
            prayerDate.setHours(h, m, 0);
            
            const diffMs = prayerDate - now;
            const diffHrs = Math.floor((diffMs % 86400000) / 3600000);
            const diffMins = Math.round(((diffMs % 86400000) % 3600000) / 60000);
            
            document.getElementById('countdown-text').innerText = `${nextPrayer} - ${diffHrs}j ${diffMins}m`;
            
        } catch (e) {
            console.error(e);
            document.getElementById('countdown-text').innerText = "Error";
        }
    }
    
    // Update every minute
    updatePrayerCountdown();
    setInterval(updatePrayerCountdown, 60000);
</script>
"""

BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Masjid Al Hijrah - Layanan Digital</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    {{ styles|safe }}
</head>
<body>
    <div class="overlay"></div>
    
    {{ navbar|safe }}
    
    <div class="container mt-4 mb-5">
        {{ content|safe }}
    </div>

    {{ bottom_nav|safe }}

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# --- ROUTES ---

@app.route('/')
def index():
    return redirect(url_for('finance')) # Default to first tab

@app.route('/finance', methods=['GET', 'POST'])
def finance():
    conn = get_db_connection()
    if request.method == 'POST':
        # Admin Logic (Simple)
        if 'delete_id' in request.form:
            conn.execute('DELETE FROM finance WHERE id = ?', (request.form['delete_id'],))
        else:
            conn.execute('INSERT INTO finance (date, type, category, description, amount) VALUES (?, ?, ?, ?, ?)',
                         (request.form['date'], request.form['type'], request.form['category'], 
                          request.form['description'], request.form['amount']))
        conn.commit()
        return redirect(url_for('finance'))
    
    items = conn.execute('SELECT * FROM finance ORDER BY date DESC').fetchall()
    
    # Calculate Totals
    total_in = conn.execute("SELECT SUM(amount) FROM finance WHERE type='Pemasukan'").fetchone()[0] or 0
    total_out = conn.execute("SELECT SUM(amount) FROM finance WHERE type='Pengeluaran'").fetchone()[0] or 0
    balance = total_in - total_out
    
    conn.close()
    
    content = """
    <div class="row mb-4">
        <div class="col-md-4">
            <div class="glass-card text-center text-success">
                <h5 class="opacity-75">Pemasukan</h5>
                <h3 class="fw-bold">Rp {{ "{:,.0f}".format(total_in) }}</h3>
            </div>
        </div>
        <div class="col-md-4">
            <div class="glass-card text-center text-danger">
                <h5 class="opacity-75">Pengeluaran</h5>
                <h3 class="fw-bold">Rp {{ "{:,.0f}".format(total_out) }}</h3>
            </div>
        </div>
        <div class="col-md-4">
            <div class="glass-card text-center text-info">
                <h5 class="opacity-75">Saldo Akhir</h5>
                <h3 class="fw-bold">Rp {{ "{:,.0f}".format(balance) }}</h3>
            </div>
        </div>
    </div>

    <div class="glass-card">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h4 class="page-title mb-0">Laporan Kas Transparan</h4>
            <button class="btn btn-custom btn-sm" data-bs-toggle="modal" data-bs-target="#addModal"><i class="fas fa-plus"></i> Input</button>
        </div>
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Tanggal</th>
                        <th>Kategori</th>
                        <th>Keterangan</th>
                        <th class="text-end">Jumlah</th>
                        <th>Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in items %}
                    <tr>
                        <td>{{ item['date'] }}</td>
                        <td><span class="badge {{ 'bg-success' if item['type'] == 'Pemasukan' else 'bg-danger' }}">{{ item['category'] }}</span></td>
                        <td>{{ item['description'] }}</td>
                        <td class="text-end fw-bold {{ 'text-success' if item['type'] == 'Pemasukan' else 'text-danger' }}">
                            {{ "+" if item['type'] == 'Pemasukan' else "-" }} Rp {{ "{:,.0f}".format(item['amount']) }}
                        </td>
                        <td>
                            <form method="POST" style="display:inline;">
                                <input type="hidden" name="delete_id" value="{{ item['id'] }}">
                                <button class="btn btn-sm btn-outline-danger border-0" onclick="return confirm('Hapus?')"><i class="fas fa-trash"></i></button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    
    <!-- Modal -->
    <div class="modal fade" id="addModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header border-0">
                    <h5 class="modal-title">Input Data Keuangan</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <form method="POST">
                    <div class="modal-body">
                        <div class="mb-3">
                            <label>Tanggal</label>
                            <input type="date" name="date" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label>Jenis Transaksi</label>
                            <select name="type" class="form-select" required>
                                <option value="Pemasukan" class="text-dark">Pemasukan (Infaq Jumat/Donasi)</option>
                                <option value="Pengeluaran" class="text-dark">Pengeluaran (Listrik/Gaji/Perbaikan)</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label>Kategori</label>
                            <select name="category" class="form-select" required>
                                <option value="Infaq Jumat" class="text-dark">Infaq Jumat</option>
                                <option value="Operasional" class="text-dark">Operasional</option>
                                <option value="Pembangunan" class="text-dark">Pembangunan</option>
                                <option value="Sosial" class="text-dark">Sosial</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label>Keterangan</label>
                            <input type="text" name="description" class="form-control" placeholder="Contoh: Bayar Listrik Bulan Juli" required>
                        </div>
                        <div class="mb-3">
                            <label>Nominal (Rp)</label>
                            <input type="number" name="amount" class="form-control" required>
                        </div>
                    </div>
                    <div class="modal-footer border-0">
                        <button type="submit" class="btn btn-custom w-100">Simpan Data</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, navbar=render_template_string(NAVBAR_HTML, active_page='finance'), bottom_nav=BOTTOM_NAV_HTML, content=render_template_string(content, items=items, total_in=total_in, total_out=total_out, balance=balance))

@app.route('/agenda', methods=['GET', 'POST'])
def agenda():
    conn = get_db_connection()
    if request.method == 'POST':
        if 'delete_id' in request.form:
            conn.execute('DELETE FROM agenda WHERE id = ?', (request.form['delete_id'],))
        else:
            conn.execute('INSERT INTO agenda (date, time, title, speaker, type) VALUES (?, ?, ?, ?, ?)',
                         (request.form['date'], request.form['time'], request.form['title'], request.form['speaker'], request.form['type']))
        conn.commit()
        return redirect(url_for('agenda'))

    items = conn.execute('SELECT * FROM agenda ORDER BY date ASC, time ASC').fetchall()
    conn.close()

    content = """
    <div class="glass-card">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h4 class="page-title mb-0">Jadwal Imam & Kajian</h4>
            <button class="btn btn-custom btn-sm" data-bs-toggle="modal" data-bs-target="#addAgendaModal"><i class="fas fa-plus"></i> Tambah</button>
        </div>
        
        <div class="row g-3">
            {% for item in items %}
            <div class="col-md-6">
                <div class="p-3 border rounded-3 position-relative" style="background: rgba(255,255,255,0.05);">
                    <form method="POST" class="position-absolute top-0 end-0 m-2">
                        <input type="hidden" name="delete_id" value="{{ item['id'] }}">
                        <button class="btn btn-sm text-danger p-0" onclick="return confirm('Hapus?')"><i class="fas fa-times"></i></button>
                    </form>
                    
                    <div class="d-flex align-items-center mb-2">
                        <span class="badge {{ 'bg-warning text-dark' if item['type'] == 'Jumat' else 'bg-info text-dark' }} me-2">{{ item['type'] }}</span>
                        <small class="opacity-75"><i class="far fa-calendar me-1"></i> {{ item['date'] }} | <i class="far fa-clock me-1"></i> {{ item['time'] }}</small>
                    </div>
                    <h5 class="fw-bold mb-1">{{ item['title'] }}</h5>
                    <p class="mb-0 opacity-75"><i class="fas fa-user-tie me-2"></i> {{ item['speaker'] }}</p>
                </div>
            </div>
            {% else %}
            <div class="col-12 text-center py-5">
                <p class="opacity-50">Belum ada agenda.</p>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Modal -->
    <div class="modal fade" id="addAgendaModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header border-0">
                    <h5 class="modal-title">Tambah Agenda</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <form method="POST">
                    <div class="modal-body">
                        <div class="mb-3">
                            <label>Tanggal</label>
                            <input type="date" name="date" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label>Jam</label>
                            <input type="time" name="time" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label>Jenis</label>
                            <select name="type" class="form-select" required>
                                <option value="Jumat" class="text-dark">Sholat Jumat</option>
                                <option value="Kajian" class="text-dark">Kajian Rutin</option>
                                <option value="PHBI" class="text-dark">PHBI (Maulid/Isra Miraj)</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label>Judul / Tema</label>
                            <input type="text" name="title" class="form-control" placeholder="Contoh: Khutbah Jumat" required>
                        </div>
                        <div class="mb-3">
                            <label>Nama Ustadz / Imam</label>
                            <input type="text" name="speaker" class="form-control" required>
                        </div>
                    </div>
                    <div class="modal-footer border-0">
                        <button type="submit" class="btn btn-custom w-100">Simpan Agenda</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, navbar=render_template_string(NAVBAR_HTML, active_page='agenda'), bottom_nav=BOTTOM_NAV_HTML, content=render_template_string(content, items=items))

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    conn = get_db_connection()
    if request.method == 'POST':
        if 'status_update' in request.form:
             conn.execute('UPDATE bookings SET status = ? WHERE id = ?', (request.form['status'], request.form['booking_id']))
        else:
             conn.execute('INSERT INTO bookings (name, date, purpose, type, contact) VALUES (?, ?, ?, ?, ?)',
                         (request.form['name'], request.form['date'], request.form['purpose'], request.form['type'], request.form['contact']))
        conn.commit()
        return redirect(url_for('booking'))

    items = conn.execute('SELECT * FROM bookings ORDER BY created_at DESC').fetchall()
    conn.close()

    content = """
    <div class="glass-card">
        <h4 class="page-title">Peminjaman Fasilitas & Ambulan</h4>
        <p class="opacity-75 mb-4">Silakan isi formulir untuk meminjam Ambulan atau Area Masjid.</p>
        
        <form method="POST" class="mb-5 border-bottom border-secondary pb-4">
            <div class="row">
                <div class="col-md-6 mb-3">
                    <label>Nama Peminjam</label>
                    <input type="text" name="name" class="form-control" required>
                </div>
                <div class="col-md-6 mb-3">
                    <label>No. HP / WhatsApp</label>
                    <input type="text" name="contact" class="form-control" required>
                </div>
                <div class="col-md-6 mb-3">
                    <label>Tanggal Pemakaian</label>
                    <input type="date" name="date" class="form-control" required>
                </div>
                <div class="col-md-6 mb-3">
                    <label>Fasilitas</label>
                    <select name="type" class="form-select" required>
                        <option value="Ambulan" class="text-dark">Mobil Ambulan</option>
                        <option value="Area Masjid" class="text-dark">Area Masjid (Akad Nikah/TPA)</option>
                        <option value="Peralatan" class="text-dark">Peralatan (Tenda/Kursi)</option>
                    </select>
                </div>
                <div class="col-12 mb-3">
                    <label>Keperluan</label>
                    <textarea name="purpose" class="form-control" rows="2" required></textarea>
                </div>
                <div class="col-12">
                    <button type="submit" class="btn btn-custom w-100">Ajukan Peminjaman</button>
                </div>
            </div>
        </form>

        <h5 class="fw-bold mb-3"><i class="fas fa-list-ul me-2"></i>Status Pengajuan</h5>
        <div class="table-responsive">
            <table class="table align-middle">
                <tbody>
                    {% for item in items %}
                    <tr>
                        <td>
                            <div class="fw-bold">{{ item['name'] }}</div>
                            <small class="opacity-75">{{ item['type'] }} - {{ item['date'] }}</small>
                            <div class="small fst-italic">{{ item['purpose'] }}</div>
                        </td>
                        <td class="text-end">
                            <span class="badge {{ 'bg-warning text-dark' if item['status'] == 'Pending' else ('bg-success' if item['status'] == 'Approved' else 'bg-danger') }}">
                                {{ item['status'] }}
                            </span>
                            {% if item['status'] == 'Pending' %}
                            <div class="mt-2">
                                <form method="POST" class="d-inline">
                                    <input type="hidden" name="status_update" value="1">
                                    <input type="hidden" name="booking_id" value="{{ item['id'] }}">
                                    <input type="hidden" name="status" value="Approved">
                                    <button class="btn btn-sm btn-success py-0 px-2" title="Setujui"><i class="fas fa-check"></i></button>
                                </form>
                                <form method="POST" class="d-inline">
                                    <input type="hidden" name="status_update" value="1">
                                    <input type="hidden" name="booking_id" value="{{ item['id'] }}">
                                    <input type="hidden" name="status" value="Rejected">
                                    <button class="btn btn-sm btn-danger py-0 px-2" title="Tolak"><i class="fas fa-times"></i></button>
                                </form>
                            </div>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, navbar=render_template_string(NAVBAR_HTML, active_page='booking'), bottom_nav=BOTTOM_NAV_HTML, content=render_template_string(content, items=items))

@app.route('/zakat', methods=['GET', 'POST'])
def zakat():
    conn = get_db_connection()
    if request.method == 'POST':
         conn.execute('INSERT INTO zakat (donor_name, type, amount, notes) VALUES (?, ?, ?, ?)',
                     (request.form['donor_name'], request.form['type'], request.form['amount'], request.form['notes']))
         conn.commit()
         return redirect(url_for('zakat'))
    
    items = conn.execute('SELECT * FROM zakat ORDER BY created_at DESC LIMIT 50').fetchall()
    
    # Stats
    total_zakat_fitrah = conn.execute("SELECT SUM(amount) FROM zakat WHERE type='Zakat Fitrah'").fetchone()[0] or 0
    total_sapi = conn.execute("SELECT COUNT(*) FROM zakat WHERE type='Qurban Sapi'").fetchone()[0] or 0
    total_kambing = conn.execute("SELECT COUNT(*) FROM zakat WHERE type='Qurban Kambing'").fetchone()[0] or 0
    
    conn.close()

    content = """
    <div class="row mb-4">
        <div class="col-md-4">
            <div class="glass-card text-center">
                <h6 class="opacity-75">Total Zakat Fitrah</h6>
                <h3 class="fw-bold text-success">Rp {{ "{:,.0f}".format(total_zakat_fitrah) }}</h3>
            </div>
        </div>
        <div class="col-md-4">
            <div class="glass-card text-center">
                <h6 class="opacity-75">Hewan Qurban</h6>
                <h3 class="fw-bold text-warning">{{ total_sapi }} Sapi / {{ total_kambing }} Kambing</h3>
            </div>
        </div>
    </div>

    <div class="glass-card">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h4 class="page-title mb-0">Pencatatan Zakat & Qurban</h4>
            <button class="btn btn-custom btn-sm" data-bs-toggle="modal" data-bs-target="#addZakatModal"><i class="fas fa-plus"></i> Input Data</button>
        </div>
        
        <div class="table-responsive">
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>Nama Muzakki/Pequrban</th>
                        <th>Jenis</th>
                        <th>Jumlah/Nominal</th>
                        <th>Catatan</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in items %}
                    <tr>
                        <td>{{ item['donor_name'] }}</td>
                        <td>{{ item['type'] }}</td>
                        <td class="fw-bold">{{ "Rp {:,.0f}".format(item['amount']|int) if item['amount'].isdigit() else item['amount'] }}</td>
                        <td class="opacity-75 small">{{ item['notes'] }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Modal -->
    <div class="modal fade" id="addZakatModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header border-0">
                    <h5 class="modal-title">Input Zakat / Qurban</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <form method="POST">
                    <div class="modal-body">
                        <div class="mb-3">
                            <label>Nama Warga</label>
                            <input type="text" name="donor_name" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label>Jenis</label>
                            <select name="type" class="form-select" required>
                                <option value="Zakat Fitrah" class="text-dark">Zakat Fitrah</option>
                                <option value="Zakat Mal" class="text-dark">Zakat Mal</option>
                                <option value="Qurban Sapi" class="text-dark">Qurban Sapi</option>
                                <option value="Qurban Kambing" class="text-dark">Qurban Kambing</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label>Nominal (Rp) atau Jumlah Hewan</label>
                            <input type="text" name="amount" class="form-control" placeholder="Contoh: 50000 atau 1 Ekor" required>
                        </div>
                        <div class="mb-3">
                            <label>Catatan</label>
                            <input type="text" name="notes" class="form-control" placeholder="Opsional (misal: Hamba Allah)">
                        </div>
                    </div>
                    <div class="modal-footer border-0">
                        <button type="submit" class="btn btn-custom w-100">Simpan</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, navbar=render_template_string(NAVBAR_HTML, active_page='zakat'), bottom_nav=BOTTOM_NAV_HTML, content=render_template_string(content, items=items, total_zakat_fitrah=total_zakat_fitrah, total_sapi=total_sapi, total_kambing=total_kambing))

@app.route('/gallery-dakwah', methods=['GET', 'POST'])
def gallery_dakwah():
    conn = get_db_connection()
    if request.method == 'POST':
        if 'delete_id' in request.form:
             conn.execute('DELETE FROM gallery_dakwah WHERE id = ?', (request.form['delete_id'],))
        elif 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                conn.execute('INSERT INTO gallery_dakwah (title, image, description, date) VALUES (?, ?, ?, ?)',
                             (request.form['title'], filename, request.form['description'], datetime.date.today()))
        conn.commit()
        return redirect(url_for('gallery_dakwah'))
    
    items = conn.execute('SELECT * FROM gallery_dakwah ORDER BY created_at DESC').fetchall()
    conn.close()

    content = """
    <div class="glass-card">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h4 class="page-title mb-0">Galeri Dakwah & Santunan</h4>
            <button class="btn btn-custom btn-sm" data-bs-toggle="modal" data-bs-target="#uploadModal"><i class="fas fa-camera"></i> Upload</button>
        </div>
        
        <div class="row g-3">
            {% for item in items %}
            <div class="col-6 col-md-4">
                <div class="position-relative overflow-hidden rounded-3 shadow-sm" style="padding-top: 100%; background: #000;">
                    <img src="/uploads/{{ item['image'] }}" class="position-absolute top-0 start-0 w-100 h-100 object-fit-cover" alt="{{ item['title'] }}">
                    <div class="position-absolute bottom-0 start-0 w-100 p-2 text-white bg-dark bg-opacity-50">
                        <small class="fw-bold d-block text-truncate">{{ item['title'] }}</small>
                    </div>
                    <form method="POST" class="position-absolute top-0 end-0 m-2">
                        <input type="hidden" name="delete_id" value="{{ item['id'] }}">
                        <button class="btn btn-sm btn-danger rounded-circle p-1" style="width:24px; height:24px; line-height:1;" onclick="return confirm('Hapus?')">&times;</button>
                    </form>
                </div>
            </div>
            {% else %}
            <div class="col-12 text-center py-5">
                <p class="opacity-50">Belum ada dokumentasi.</p>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Modal -->
    <div class="modal fade" id="uploadModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header border-0">
                    <h5 class="modal-title">Upload Foto Kegiatan</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <form method="POST" enctype="multipart/form-data">
                    <div class="modal-body">
                        <div class="mb-3">
                            <label>Judul Kegiatan</label>
                            <input type="text" name="title" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label>Deskripsi Singkat</label>
                            <input type="text" name="description" class="form-control">
                        </div>
                        <div class="mb-3">
                            <label>File Foto</label>
                            <input type="file" name="image" class="form-control" required>
                        </div>
                    </div>
                    <div class="modal-footer border-0">
                        <button type="submit" class="btn btn-custom w-100">Upload</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, navbar=render_template_string(NAVBAR_HTML, active_page='gallery'), bottom_nav=BOTTOM_NAV_HTML, content=render_template_string(content, items=items))

@app.route('/suggestion', methods=['GET', 'POST'])
def suggestion():
    conn = get_db_connection()
    if request.method == 'POST':
         conn.execute('INSERT INTO suggestions (content, date) VALUES (?, ?)',
                     (request.form['content'], datetime.date.today()))
         conn.commit()
         return redirect(url_for('suggestion'))
    
    # Admin View (Showing last 10)
    items = conn.execute('SELECT * FROM suggestions ORDER BY created_at DESC LIMIT 10').fetchall()
    conn.close()

    content = """
    <div class="glass-card">
        <h4 class="page-title">Kotak Saran Digital</h4>
        <p class="opacity-75 mb-4">Sampaikan kritik, saran, atau laporan kerusakan fasilitas masjid. Identitas Anda dirahasiakan.</p>
        
        <form method="POST" class="mb-5">
            <div class="mb-3">
                <textarea name="content" class="form-control" rows="5" placeholder="Tulis saran Anda di sini... Contoh: 'Keran wudhu bocor', 'Suara sound system kurang jelas'" required></textarea>
            </div>
            <button type="submit" class="btn btn-custom w-100"><i class="fas fa-paper-plane me-2"></i> Kirim Laporan</button>
        </form>
        
        <hr class="border-secondary my-4">
        
        <h6 class="fw-bold mb-3 opacity-50 text-uppercase">Laporan Masuk (Admin View)</h6>
        <div class="list-group list-group-flush bg-transparent">
            {% for item in items %}
            <div class="list-group-item bg-transparent text-white border-bottom border-secondary">
                <div class="d-flex justify-content-between">
                    <small class="opacity-50">{{ item['date'] }}</small>
                    <span class="badge bg-secondary">{{ item['status'] }}</span>
                </div>
                <p class="mb-1 mt-2">{{ item['content'] }}</p>
            </div>
            {% endfor %}
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, navbar=render_template_string(NAVBAR_HTML, active_page='suggestion'), bottom_nav=BOTTOM_NAV_HTML, content=render_template_string(content, items=items))

@app.route('/prayer-times')
def prayer_times_api():
    now = datetime.datetime.now()
    pt = PrayTimes()
    times = pt.get_prayer_times(now.year, now.month, now.day, LAT, LNG, TZ)
    return jsonify(times)

@app.route('/donate')
def donate():
    # Renders a page with the QRIS modal auto-triggered or just static
    content = """
    <div class="glass-card text-center py-5">
        <h2 class="fw-bold mb-3">Infaq & Sedekah Instan</h2>
        <p class="mb-4">Scan QRIS ini menggunakan GoPay, OVO, Dana, ShopeePay, atau Mobile Banking.</p>
        
        <div class="bg-white p-3 d-inline-block rounded-3 mb-4">
             <!-- Placeholder QRIS -->
             <img src="https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=MasjidAlHijrahInfaq" alt="QRIS Code" class="img-fluid" style="width: 250px;">
        </div>
        
        <br>
        <a href="/" class="btn btn-outline-light rounded-pill px-5">Kembali</a>
    </div>
    """
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, navbar=render_template_string(NAVBAR_HTML, active_page='donate'), bottom_nav=BOTTOM_NAV_HTML, content=content)

@app.route('/emergency')
def emergency():
    # Redirect to WhatsApp
    return redirect("https://wa.me/6281241865310?text=Halo%20Takmir%20Masjid,%20Ada%20Keadaan%20Darurat!")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
