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
    
    # Drop old tables if they exist (Clean Slate for this demo)
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
            return 0 # Handle polar regions if needed
        return noon - d / 15.0 if g > 90 else noon + d / 15.0

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

# --- FRONTEND ASSETS & LAYOUT ---

STYLES_HTML = """
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
          theme: {
            extend: {
              colors: {
                emerald: {
                  50: '#ecfdf5',
                  100: '#d1fae5',
                  400: '#34d399',
                  500: '#10b981',
                  600: '#059669',
                },
                amber: {
                  300: '#fcd34d',
                  400: '#fbbf24',
                }
              },
              fontFamily: {
                sans: ['Poppins', 'sans-serif'],
              },
              borderRadius: {
                '3xl': '1.5rem',
              }
            }
          }
        }
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
        body { background-color: #F8FAFC; }
        .glass-nav {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(0,0,0,0.05);
        }
        .glass-bottom {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border-top: 1px solid rgba(0,0,0,0.05);
        }
        .card-hover { transition: all 0.3s ease; }
        .card-hover:active { transform: scale(0.98); }
        .pb-safe { padding-bottom: env(safe-area-inset-bottom, 20px); }
    </style>
"""

BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Masjid Al Hijrah</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    {{ styles|safe }}
</head>
<body class="text-gray-800 antialiased">
    
    <!-- HEADER -->
    <header class="fixed top-0 left-0 w-full z-50 glass-nav shadow-sm px-4 py-3 flex justify-between items-center max-w-md mx-auto right-0">
        <div>
            <p class="text-xs text-gray-500 font-medium">Assalamualaikum</p>
            <h1 class="text-lg font-bold text-emerald-600 leading-tight">Masjid Al Hijrah</h1>
        </div>
        <div class="text-right">
            <p class="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-2 py-1 rounded-full border border-emerald-200" id="hijri-date">Loading...</p>
        </div>
    </header>

    <!-- CONTENT -->
    <main class="min-h-screen relative w-full max-w-md mx-auto bg-[#F8FAFC]">
        {{ content|safe }}
    </main>

    <!-- BOTTOM NAV -->
    <nav class="fixed bottom-0 left-0 w-full glass-bottom z-50 pb-2 pt-2 max-w-md mx-auto right-0 border-t border-gray-100">
        <div class="flex justify-around items-end h-14 px-2">
            <a href="/" class="flex flex-col items-center justify-center text-gray-400 hover:text-emerald-600 w-16 mb-1 transition-colors {{ 'text-emerald-600' if active_page == 'home' else '' }}">
                <i class="fas fa-home text-xl mb-1"></i>
                <span class="text-[10px] font-medium">Beranda</span>
            </a>
            <a href="/donate" class="flex flex-col items-center justify-center text-gray-400 hover:text-emerald-600 w-16 mb-6 relative z-10">
                <div class="bg-emerald-500 text-white w-14 h-14 rounded-full flex items-center justify-center shadow-lg border-4 border-white transform hover:scale-105 transition-transform">
                    <i class="fas fa-qrcode text-2xl"></i>
                </div>
                <span class="text-[10px] font-bold mt-1 text-emerald-600">Infaq</span>
            </a>
            <a href="/emergency" class="flex flex-col items-center justify-center text-gray-400 hover:text-red-500 w-16 mb-1 transition-colors">
                <i class="fas fa-phone-alt text-xl mb-1"></i>
                <span class="text-[10px] font-medium">Darurat</span>
            </a>
        </div>
    </nav>

    <script>
        // HIJRI DATE
        async function fetchHijri() {
            try {
                const today = new Date();
                const dd = String(today.getDate()).padStart(2, '0');
                const mm = String(today.getMonth() + 1).padStart(2, '0');
                const yyyy = today.getFullYear();
                const dateStr = dd + '-' + mm + '-' + yyyy;

                const response = await fetch('https://api.aladhan.com/v1/gToH?date=' + dateStr);
                const data = await response.json();
                const h = data.data.hijri;
                document.getElementById('hijri-date').innerText = `${h.day} ${h.month.en} ${h.year}H`;
            } catch(e) {
                console.error(e);
                document.getElementById('hijri-date').innerText = "1 Muharram 1445H";
            }
        }

        // PRAYER TIMES & COUNTDOWN
        async function fetchPrayerTimes() {
            try {
                const response = await fetch('/prayer-times');
                const data = await response.json();

                // Update grid if exists
                if(document.getElementById('fajr-time')) {
                    document.getElementById('fajr-time').innerText = data.Fajr;
                    document.getElementById('dhuhr-time').innerText = data.Dhuhr;
                    document.getElementById('asr-time').innerText = data.Asr;
                    document.getElementById('maghrib-time').innerText = data.Maghrib;
                    document.getElementById('isha-time').innerText = data.Isha;
                }

                // Countdown Logic
                const now = new Date();
                const currentTimeStr = now.toTimeString().slice(0, 5);
                const prayers = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'];
                let nextPrayer = null;
                let nextTimeStr = null;

                for (let p of prayers) {
                    if (data[p] > currentTimeStr) {
                        nextPrayer = p;
                        nextTimeStr = data[p];
                        break;
                    }
                }

                if (!nextPrayer) {
                    // Next is Fajr tomorrow
                    nextPrayer = 'Fajr';
                    nextTimeStr = data['Fajr'];
                    // Note: Logic needs date adjustment for accurate countdown across midnight, simplified here
                }

                if(document.getElementById('next-prayer-name')) {
                    document.getElementById('next-prayer-name').innerText = nextPrayer;

                    // Simple countdown visualization (hh:mm:ss)
                    // Parsing time
                    const [h, m] = nextTimeStr.split(':');
                    const target = new Date();
                    target.setHours(h, m, 0);
                    if(target < now) target.setDate(target.getDate() + 1);

                    const diff = target - now;
                    const hours = Math.floor(diff / 3600000);
                    const minutes = Math.floor((diff % 3600000) / 60000);
                    const seconds = Math.floor((diff % 60000) / 1000);

                    document.getElementById('countdown-timer').innerText =
                        `${hours.toString().padStart(2,'0')}:${minutes.toString().padStart(2,'0')}:${seconds.toString().padStart(2,'0')}`;
                }

            } catch(e) { console.error(e); }
        }

        document.addEventListener('DOMContentLoaded', () => {
            fetchHijri();
            fetchPrayerTimes();
            setInterval(fetchPrayerTimes, 1000);
        });
    </script>
</body>
</html>
"""

HOME_HTML = """
<div class="pt-20 pb-32 px-5">
    <!-- HERO CARD -->
    <div class="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-3xl p-6 text-white shadow-xl mb-8 relative overflow-hidden">
        <div class="absolute top-0 right-0 opacity-10 transform translate-x-4 -translate-y-4">
            <i class="fas fa-mosque text-9xl"></i>
        </div>
        <div class="relative z-10">
            <p class="text-xs font-medium opacity-80 mb-1 tracking-wide uppercase">Waktu Sholat Berikutnya</p>
            <h2 class="text-4xl font-bold mb-3" id="next-prayer-name">--:--</h2>
            <div class="bg-white/20 backdrop-blur-md rounded-xl px-4 py-2 inline-block mb-6 border border-white/10">
                <span class="font-mono text-2xl font-bold tracking-wider" id="countdown-timer">--:--:--</span>
            </div>

            <div class="grid grid-cols-5 gap-1 text-center text-xs opacity-90 border-t border-white/20 pt-4">
                <div>
                    <div class="font-semibold mb-1">Subuh</div>
                    <div id="fajr-time" class="font-mono">--:--</div>
                </div>
                <div>
                    <div class="font-semibold mb-1">Dzuhur</div>
                    <div id="dhuhr-time" class="font-mono">--:--</div>
                </div>
                <div>
                    <div class="font-semibold mb-1">Ashar</div>
                    <div id="asr-time" class="font-mono">--:--</div>
                </div>
                <div>
                    <div class="font-semibold mb-1">Maghrib</div>
                    <div id="maghrib-time" class="font-mono">--:--</div>
                </div>
                <div>
                    <div class="font-semibold mb-1">Isya</div>
                    <div id="isha-time" class="font-mono">--:--</div>
                </div>
            </div>
        </div>
    </div>

    <!-- MAIN GRID MENU -->
    <h3 class="text-gray-800 font-bold text-lg mb-4 pl-1 border-l-4 border-emerald-500 leading-none py-1 ml-1">&nbsp;Menu Utama</h3>
    <div class="grid grid-cols-2 gap-4 mb-8">
        <a href="/finance" class="bg-white p-5 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 border border-gray-50 group">
            <div class="bg-emerald-50 w-14 h-14 rounded-full flex items-center justify-center mb-3 text-emerald-600 group-hover:bg-emerald-500 group-hover:text-white transition-colors">
                <i class="fas fa-wallet text-2xl"></i>
            </div>
            <span class="text-sm font-semibold text-gray-700 group-hover:text-emerald-600">Laporan Kas</span>
        </a>
        <a href="/agenda" class="bg-white p-5 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 border border-gray-50 group">
            <div class="bg-blue-50 w-14 h-14 rounded-full flex items-center justify-center mb-3 text-blue-600 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                <i class="fas fa-calendar-alt text-2xl"></i>
            </div>
            <span class="text-sm font-semibold text-gray-700 group-hover:text-blue-600">Jadwal Imam</span>
        </a>
        <a href="/booking" class="bg-white p-5 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 border border-gray-50 group">
            <div class="bg-orange-50 w-14 h-14 rounded-full flex items-center justify-center mb-3 text-orange-600 group-hover:bg-orange-500 group-hover:text-white transition-colors">
                <i class="fas fa-building text-2xl"></i>
            </div>
            <span class="text-sm font-semibold text-gray-700 group-hover:text-orange-600">Peminjaman</span>
        </a>
        <a href="/zakat" class="bg-white p-5 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 border border-gray-50 group">
            <div class="bg-green-50 w-14 h-14 rounded-full flex items-center justify-center mb-3 text-green-600 group-hover:bg-green-500 group-hover:text-white transition-colors">
                <i class="fas fa-hand-holding-heart text-2xl"></i>
            </div>
            <span class="text-sm font-semibold text-gray-700 group-hover:text-green-600">Zakat</span>
        </a>
        <a href="/gallery-dakwah" class="bg-white p-5 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 border border-gray-50 group">
            <div class="bg-purple-50 w-14 h-14 rounded-full flex items-center justify-center mb-3 text-purple-600 group-hover:bg-purple-500 group-hover:text-white transition-colors">
                <i class="fas fa-images text-2xl"></i>
            </div>
            <span class="text-sm font-semibold text-gray-700 group-hover:text-purple-600">Galeri</span>
        </a>
        <a href="/suggestion" class="bg-white p-5 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 border border-gray-50 group">
            <div class="bg-pink-50 w-14 h-14 rounded-full flex items-center justify-center mb-3 text-pink-600 group-hover:bg-pink-500 group-hover:text-white transition-colors">
                <i class="fas fa-comment-dots text-2xl"></i>
            </div>
            <span class="text-sm font-semibold text-gray-700 group-hover:text-pink-600">Kotak Saran</span>
        </a>
    </div>
</div>
"""

# --- ROUTES ---

@app.route('/')
def index():
    # Render Home Dashboard
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='home', content=HOME_HTML)

@app.route('/finance', methods=['GET', 'POST'])
def finance():
    conn = get_db_connection()
    if request.method == 'POST':
        if 'delete_id' in request.form:
            conn.execute('DELETE FROM finance WHERE id = ?', (request.form['delete_id'],))
        else:
            conn.execute('INSERT INTO finance (date, type, category, description, amount) VALUES (?, ?, ?, ?, ?)',
                         (request.form['date'], request.form['type'], request.form['category'], 
                          request.form['description'], request.form['amount']))
        conn.commit()
        return redirect(url_for('finance'))
    
    items = conn.execute('SELECT * FROM finance ORDER BY date DESC').fetchall()
    
    total_in = conn.execute("SELECT SUM(amount) FROM finance WHERE type='Pemasukan'").fetchone()[0] or 0
    total_out = conn.execute("SELECT SUM(amount) FROM finance WHERE type='Pengeluaran'").fetchone()[0] or 0
    balance = total_in - total_out
    conn.close()
    
    content = """
    <div class="pt-20 pb-24 px-5">
        <div class="flex justify-between items-center mb-6">
            <h3 class="text-xl font-bold text-gray-800">Laporan Kas</h3>
            <button onclick="document.getElementById('modal-add').classList.remove('hidden')" class="bg-emerald-500 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-md hover:bg-emerald-600 transition">+ Input</button>
        </div>

        <div class="grid grid-cols-1 gap-4 mb-6">
            <div class="bg-white p-5 rounded-3xl shadow-sm border border-emerald-100 relative overflow-hidden">
                <div class="absolute right-0 top-0 p-4 opacity-10"><i class="fas fa-wallet text-6xl text-emerald-500"></i></div>
                <p class="text-sm text-gray-500 font-medium mb-1">Saldo Akhir</p>
                <h2 class="text-3xl font-bold text-emerald-600">Rp {{ "{:,.0f}".format(balance) }}</h2>
            </div>
            <div class="grid grid-cols-2 gap-4">
                <div class="bg-white p-4 rounded-3xl shadow-sm border border-gray-100">
                    <p class="text-xs text-gray-400 mb-1">Pemasukan</p>
                    <h3 class="text-lg font-bold text-green-500">Rp {{ "{:,.0f}".format(total_in) }}</h3>
                </div>
                <div class="bg-white p-4 rounded-3xl shadow-sm border border-gray-100">
                    <p class="text-xs text-gray-400 mb-1">Pengeluaran</p>
                    <h3 class="text-lg font-bold text-red-500">Rp {{ "{:,.0f}".format(total_out) }}</h3>
                </div>
            </div>
        </div>

        <div class="bg-white rounded-3xl shadow-lg border border-gray-100 overflow-hidden">
            <div class="bg-gray-50 px-5 py-3 border-b border-gray-100">
                <h4 class="font-bold text-gray-700 text-sm">Riwayat Transaksi</h4>
            </div>
            <div class="divide-y divide-gray-100">
                {% for item in items %}
                <div class="p-4 flex justify-between items-start hover:bg-gray-50 transition">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="text-[10px] font-bold px-2 py-0.5 rounded-full {{ 'bg-green-100 text-green-600' if item['type'] == 'Pemasukan' else 'bg-red-100 text-red-600' }}">{{ item['category'] }}</span>
                            <span class="text-xs text-gray-400">{{ item['date'] }}</span>
                        </div>
                        <p class="text-sm font-medium text-gray-800">{{ item['description'] }}</p>
                    </div>
                    <div class="text-right">
                        <p class="text-sm font-bold {{ 'text-green-600' if item['type'] == 'Pemasukan' else 'text-red-500' }}">
                            {{ "+" if item['type'] == 'Pemasukan' else "-" }} {{ "{:,.0f}".format(item['amount']) }}
                        </p>
                        <form method="POST" class="inline-block mt-1">
                            <input type="hidden" name="delete_id" value="{{ item['id'] }}">
                            <button class="text-gray-300 hover:text-red-500 text-xs" onclick="return confirm('Hapus?')"><i class="fas fa-trash"></i></button>
                        </form>
                    </div>
                </div>
                {% else %}
                <div class="p-8 text-center text-gray-400 text-sm">Belum ada data transaksi.</div>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- Modal -->
    <div id="modal-add" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="document.getElementById('modal-add').classList.add('hidden')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold">Input Kas Baru</h3>
                <button onclick="document.getElementById('modal-add').classList.add('hidden')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500">&times;</button>
            </div>
            <form method="POST">
                <div class="space-y-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Tanggal</label>
                        <input type="date" name="date" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" required>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-xs font-bold text-gray-500 mb-1">Jenis</label>
                            <select name="type" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" required>
                                <option value="Pemasukan">Pemasukan</option>
                                <option value="Pengeluaran">Pengeluaran</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-gray-500 mb-1">Kategori</label>
                            <select name="category" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" required>
                                <option value="Infaq Jumat">Infaq Jumat</option>
                                <option value="Operasional">Operasional</option>
                                <option value="Pembangunan">Pembangunan</option>
                                <option value="Sosial">Sosial</option>
                            </select>
                        </div>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Keterangan</label>
                        <input type="text" name="description" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="Contoh: Bayar Listrik" required>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Nominal (Rp)</label>
                        <input type="number" name="amount" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" required>
                    </div>
                    <button type="submit" class="w-full bg-emerald-500 text-white font-bold py-4 rounded-xl shadow-lg hover:bg-emerald-600 transition mt-4">Simpan Data</button>
                </div>
            </form>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='finance', content=render_template_string(content, items=items, total_in=total_in, total_out=total_out, balance=balance))

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
    <div class="pt-20 pb-24 px-5">
        <div class="flex justify-between items-center mb-6">
            <h3 class="text-xl font-bold text-gray-800">Jadwal Imam & Kajian</h3>
            <button onclick="document.getElementById('modal-agenda').classList.remove('hidden')" class="bg-blue-500 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-md hover:bg-blue-600 transition">+ Tambah</button>
        </div>

        <div class="space-y-4">
            {% for item in items %}
            <div class="bg-white p-5 rounded-3xl shadow-sm border border-gray-100 flex gap-4 relative">
                <form method="POST" class="absolute top-2 right-2">
                    <input type="hidden" name="delete_id" value="{{ item['id'] }}">
                    <button class="text-gray-300 hover:text-red-500" onclick="return confirm('Hapus?')">&times;</button>
                </form>
                <div class="flex-shrink-0 flex flex-col items-center justify-center bg-blue-50 w-16 h-16 rounded-2xl text-blue-600">
                    <span class="text-xs font-bold uppercase">{{ item['date'][5:7] }}/{{ item['date'][8:] }}</span>
                    <span class="text-xs">{{ item['time'] }}</span>
                </div>
                <div>
                    <span class="text-[10px] font-bold px-2 py-0.5 rounded-full {{ 'bg-amber-100 text-amber-700' if item['type'] == 'Jumat' else 'bg-blue-100 text-blue-700' }} mb-1 inline-block">{{ item['type'] }}</span>
                    <h4 class="font-bold text-gray-800 leading-tight mb-1">{{ item['title'] }}</h4>
                    <p class="text-xs text-gray-500"><i class="fas fa-user-circle mr-1"></i> {{ item['speaker'] }}</p>
                </div>
            </div>
            {% else %}
            <div class="text-center py-10 text-gray-400">Belum ada agenda terjadwal.</div>
            {% endfor %}
        </div>
    </div>

    <!-- Modal -->
    <div id="modal-agenda" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="document.getElementById('modal-agenda').classList.add('hidden')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out]">
            <h3 class="text-lg font-bold mb-6">Tambah Agenda</h3>
            <form method="POST">
                <div class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-xs font-bold text-gray-500 mb-1">Tanggal</label>
                            <input type="date" name="date" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm" required>
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-gray-500 mb-1">Jam</label>
                            <input type="time" name="time" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm" required>
                        </div>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Jenis</label>
                        <select name="type" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm" required>
                            <option value="Jumat">Sholat Jumat</option>
                            <option value="Kajian">Kajian Rutin</option>
                            <option value="PHBI">PHBI</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Judul / Tema</label>
                        <input type="text" name="title" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm" required>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Ustadz / Imam</label>
                        <input type="text" name="speaker" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm" required>
                    </div>
                    <button type="submit" class="w-full bg-blue-500 text-white font-bold py-4 rounded-xl shadow-lg mt-4">Simpan</button>
                </div>
            </form>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='agenda', content=render_template_string(content, items=items))

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
    <div class="pt-20 pb-24 px-5">
        <h3 class="text-xl font-bold text-gray-800 mb-2">Peminjaman Fasilitas</h3>
        <p class="text-sm text-gray-500 mb-6">Ajukan peminjaman ambulan atau area masjid.</p>

        <form method="POST" class="bg-white p-6 rounded-3xl shadow-lg border border-gray-100 mb-8">
            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Nama Peminjam</label>
                    <input type="text" name="name" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm" required>
                </div>
                <div>
                     <label class="block text-xs font-bold text-gray-500 mb-1">No. HP / WA</label>
                    <input type="text" name="contact" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm" required>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Tanggal</label>
                        <input type="date" name="date" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm" required>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Fasilitas</label>
                        <select name="type" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm" required>
                            <option value="Ambulan">Ambulan</option>
                            <option value="Area Masjid">Area Masjid</option>
                            <option value="Peralatan">Peralatan</option>
                        </select>
                    </div>
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Keperluan</label>
                    <textarea name="purpose" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm" rows="2" required></textarea>
                </div>
                <button type="submit" class="w-full bg-orange-500 text-white font-bold py-3 rounded-xl shadow-md hover:bg-orange-600 transition">Ajukan</button>
            </div>
        </form>

        <h4 class="font-bold text-gray-800 mb-4 border-l-4 border-orange-500 pl-2">Status Pengajuan</h4>
        <div class="space-y-3">
            {% for item in items %}
            <div class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50">
                <div class="flex justify-between items-start mb-2">
                    <h5 class="font-bold text-gray-800">{{ item['name'] }}</h5>
                    <span class="text-[10px] font-bold px-2 py-1 rounded-lg {{ 'bg-yellow-100 text-yellow-700' if item['status'] == 'Pending' else ('bg-green-100 text-green-700' if item['status'] == 'Approved' else 'bg-red-100 text-red-700') }}">
                        {{ item['status'] }}
                    </span>
                </div>
                <p class="text-xs text-gray-500 mb-1"><i class="fas fa-tag mr-1 text-orange-400"></i> {{ item['type'] }} • {{ item['date'] }}</p>
                <p class="text-xs text-gray-600 italic">"{{ item['purpose'] }}"</p>

                {% if item['status'] == 'Pending' %}
                <div class="flex gap-2 mt-3 pt-3 border-t border-gray-100">
                     <form method="POST" class="flex-1">
                        <input type="hidden" name="status_update" value="1">
                        <input type="hidden" name="booking_id" value="{{ item['id'] }}">
                        <input type="hidden" name="status" value="Approved">
                        <button class="w-full bg-green-50 text-green-600 text-xs font-bold py-2 rounded-lg hover:bg-green-100">Setujui</button>
                    </form>
                    <form method="POST" class="flex-1">
                        <input type="hidden" name="status_update" value="1">
                        <input type="hidden" name="booking_id" value="{{ item['id'] }}">
                        <input type="hidden" name="status" value="Rejected">
                        <button class="w-full bg-red-50 text-red-600 text-xs font-bold py-2 rounded-lg hover:bg-red-100">Tolak</button>
                    </form>
                </div>
                {% endif %}
            </div>
            {% else %}
            <p class="text-center text-gray-400 text-sm">Belum ada pengajuan.</p>
            {% endfor %}
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='booking', content=render_template_string(content, items=items))

@app.route('/zakat', methods=['GET', 'POST'])
def zakat():
    conn = get_db_connection()
    if request.method == 'POST':
         conn.execute('INSERT INTO zakat (donor_name, type, amount, notes) VALUES (?, ?, ?, ?)',
                     (request.form['donor_name'], request.form['type'], request.form['amount'], request.form['notes']))
         conn.commit()
         return redirect(url_for('zakat'))
    
    items = conn.execute('SELECT * FROM zakat ORDER BY created_at DESC LIMIT 50').fetchall()
    total_zakat_fitrah = conn.execute("SELECT SUM(amount) FROM zakat WHERE type='Zakat Fitrah'").fetchone()[0] or 0
    total_sapi = conn.execute("SELECT COUNT(*) FROM zakat WHERE type='Qurban Sapi'").fetchone()[0] or 0
    total_kambing = conn.execute("SELECT COUNT(*) FROM zakat WHERE type='Qurban Kambing'").fetchone()[0] or 0
    conn.close()

    content = """
    <div class="pt-20 pb-24 px-5">
        <div class="flex justify-between items-center mb-6">
            <h3 class="text-xl font-bold text-gray-800">Zakat & Qurban</h3>
            <button onclick="document.getElementById('modal-zakat').classList.remove('hidden')" class="bg-green-500 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-md hover:bg-green-600 transition">+ Input</button>
        </div>

        <div class="grid grid-cols-2 gap-4 mb-8">
            <div class="bg-white p-4 rounded-3xl shadow-sm border border-green-50 text-center">
                <p class="text-xs text-gray-400 mb-1">Zakat Fitrah</p>
                <h3 class="text-lg font-bold text-green-600">Rp {{ "{:,.0f}".format(total_zakat_fitrah) }}</h3>
            </div>
            <div class="bg-white p-4 rounded-3xl shadow-sm border border-green-50 text-center">
                <p class="text-xs text-gray-400 mb-1">Hewan Qurban</p>
                <h3 class="text-sm font-bold text-gray-800">{{ total_sapi }} Sapi <br> {{ total_kambing }} Kambing</h3>
            </div>
        </div>

        <h4 class="font-bold text-gray-800 mb-4 pl-2 border-l-4 border-green-500">Data Terbaru</h4>
        <div class="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
            <div class="divide-y divide-gray-100">
                {% for item in items %}
                <div class="p-4 flex justify-between items-center">
                    <div>
                        <h5 class="font-bold text-gray-800 text-sm">{{ item['donor_name'] }}</h5>
                        <p class="text-xs text-gray-500">{{ item['type'] }} • {{ item['notes'] }}</p>
                    </div>
                    <div class="font-bold text-green-600 text-sm">
                        {{ "Rp {:,.0f}".format(item['amount']|int) if item['amount'].isdigit() else item['amount'] }}
                    </div>
                </div>
                {% else %}
                <div class="p-6 text-center text-gray-400">Belum ada data.</div>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- Modal -->
    <div id="modal-zakat" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="document.getElementById('modal-zakat').classList.add('hidden')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out]">
            <h3 class="text-lg font-bold mb-6">Input Data</h3>
            <form method="POST">
                <div class="space-y-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Nama</label>
                        <input type="text" name="donor_name" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm" required>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Jenis</label>
                        <select name="type" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm" required>
                            <option value="Zakat Fitrah">Zakat Fitrah</option>
                            <option value="Zakat Mal">Zakat Mal</option>
                            <option value="Qurban Sapi">Qurban Sapi</option>
                            <option value="Qurban Kambing">Qurban Kambing</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Jumlah / Nominal</label>
                        <input type="text" name="amount" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm" placeholder="Ex: 50000 atau 1 Ekor" required>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Catatan</label>
                        <input type="text" name="notes" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm" placeholder="Ex: Hamba Allah">
                    </div>
                    <button type="submit" class="w-full bg-green-500 text-white font-bold py-4 rounded-xl shadow-lg mt-4">Simpan</button>
                </div>
            </form>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='zakat', content=render_template_string(content, items=items, total_zakat_fitrah=total_zakat_fitrah, total_sapi=total_sapi, total_kambing=total_kambing))

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
    <div class="pt-20 pb-24 px-5">
        <div class="flex justify-between items-center mb-6">
            <h3 class="text-xl font-bold text-gray-800">Galeri Dakwah</h3>
            <button onclick="document.getElementById('modal-upload').classList.remove('hidden')" class="bg-purple-500 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-md hover:bg-purple-600 transition">+ Foto</button>
        </div>

        <div class="grid grid-cols-2 gap-4">
            {% for item in items %}
            <div class="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden relative group">
                <div class="aspect-square bg-gray-200 relative">
                    <img src="/uploads/{{ item['image'] }}" class="w-full h-full object-cover" alt="{{ item['title'] }}">
                    <div class="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent flex items-end p-3">
                        <p class="text-white text-xs font-bold leading-tight line-clamp-2">{{ item['title'] }}</p>
                    </div>
                </div>
                <form method="POST" class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <input type="hidden" name="delete_id" value="{{ item['id'] }}">
                    <button class="bg-red-500 text-white w-6 h-6 rounded-full text-xs shadow-md" onclick="return confirm('Hapus?')">&times;</button>
                </form>
            </div>
            {% else %}
            <div class="col-span-2 text-center py-10 text-gray-400">Belum ada dokumentasi.</div>
            {% endfor %}
        </div>
    </div>

    <!-- Modal -->
    <div id="modal-upload" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="document.getElementById('modal-upload').classList.add('hidden')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out]">
            <h3 class="text-lg font-bold mb-6">Upload Foto</h3>
            <form method="POST" enctype="multipart/form-data">
                <div class="space-y-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Judul</label>
                        <input type="text" name="title" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm" required>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Deskripsi</label>
                        <input type="text" name="description" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Foto</label>
                        <input type="file" name="image" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm" required>
                    </div>
                    <button type="submit" class="w-full bg-purple-500 text-white font-bold py-4 rounded-xl shadow-lg mt-4">Upload</button>
                </div>
            </form>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='gallery', content=render_template_string(content, items=items))

@app.route('/suggestion', methods=['GET', 'POST'])
def suggestion():
    conn = get_db_connection()
    if request.method == 'POST':
         conn.execute('INSERT INTO suggestions (content, date) VALUES (?, ?)',
                     (request.form['content'], datetime.date.today()))
         conn.commit()
         return redirect(url_for('suggestion'))
    
    items = conn.execute('SELECT * FROM suggestions ORDER BY created_at DESC LIMIT 10').fetchall()
    conn.close()

    content = """
    <div class="pt-20 pb-24 px-5">
        <h3 class="text-xl font-bold text-gray-800 mb-4">Kotak Saran Digital</h3>
        
        <form method="POST" class="bg-white p-6 rounded-3xl shadow-lg border border-pink-50 mb-8">
            <div class="mb-4">
                <label class="block text-xs font-bold text-gray-500 mb-2">Kritik & Saran Anda</label>
                <textarea name="content" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm min-h-[120px]" placeholder="Silakan tulis masukan Anda..." required></textarea>
            </div>
            <button type="submit" class="w-full bg-pink-500 text-white font-bold py-3 rounded-xl shadow-md hover:bg-pink-600 transition">Kirim</button>
        </form>
        
        <h6 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">Laporan Masuk (Admin)</h6>
        <div class="space-y-3">
            {% for item in items %}
            <div class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50">
                <div class="flex justify-between items-center mb-2">
                    <span class="text-[10px] text-gray-400">{{ item['date'] }}</span>
                    <span class="bg-gray-100 text-gray-500 text-[10px] px-2 py-0.5 rounded-full">{{ item['status'] }}</span>
                </div>
                <p class="text-sm text-gray-700">{{ item['content'] }}</p>
            </div>
            {% else %}
            <p class="text-center text-gray-400 text-sm">Belum ada saran.</p>
            {% endfor %}
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='suggestion', content=render_template_string(content, items=items))

@app.route('/prayer-times')
def prayer_times_api():
    now = datetime.datetime.now()
    pt = PrayTimes()
    times = pt.get_prayer_times(now.year, now.month, now.day, LAT, LNG, TZ)
    return jsonify(times)

@app.route('/donate')
def donate():
    content = """
    <div class="pt-20 pb-24 px-5 text-center min-h-screen flex flex-col items-center justify-center">
        <div class="bg-white p-8 rounded-[40px] shadow-2xl border border-emerald-50 max-w-sm w-full relative overflow-hidden">
             <div class="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-emerald-400 to-emerald-600"></div>
             <h2 class="text-2xl font-bold text-gray-800 mb-2">Infaq Digital</h2>
             <p class="text-sm text-gray-500 mb-6">Scan QRIS menggunakan E-Wallet apa saja</p>

             <div class="bg-white p-4 rounded-2xl shadow-inner border border-gray-100 inline-block mb-6">
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=MasjidAlHijrahInfaq" alt="QRIS" class="w-48 h-48 mx-auto">
             </div>

             <div class="flex justify-center gap-3 opacity-60 grayscale hover:grayscale-0 transition-all">
                <i class="fas fa-wallet text-2xl"></i>
                <i class="fas fa-university text-2xl"></i>
                <i class="fas fa-mobile-alt text-2xl"></i>
             </div>
        </div>
        <br>
        <a href="/" class="text-gray-400 text-sm font-medium hover:text-emerald-500 transition">Kembali ke Beranda</a>
    </div>
    """
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='donate', content=content)

@app.route('/emergency')
def emergency():
    return redirect("https://wa.me/6281241865310?text=Halo%20Takmir%20Masjid,%20Ada%20Keadaan%20Darurat!")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
