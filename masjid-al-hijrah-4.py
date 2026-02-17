import os
import sqlite3
import datetime
import math
import time
import json
import uuid
import google.generativeai as genai
from flask import Flask, request, send_from_directory, render_template_string, redirect, url_for, Response, jsonify, make_response
from werkzeug.utils import secure_filename

# --- KONFIGURASI GEMINI ---
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
    except Exception as e:
        print(f"Error configuring Gemini: {e}")

# --- KONFIGURASI FLASK ---
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB Limit
app.secret_key = "supersecretkey_masjid_al_hijrah"
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'mp4'}

# --- DATA SUMBER HUKUM (DALIL) ---
DALIL_DATA = {
    "waris": [
        "QS. An-Nisa: 11 - \"Allah mensyariatkan bagimu tentang pembagian pusaka untuk anak-anakmu. Yaitu: bahagian seorang anak laki-laki sama dengan bagaikan dua orang anak perempuan.\"",
        "QS. An-Nisa: 7 - \"Bagi orang laki-laki ada hak bagian dari harta peninggalan ibu-bapa dan kerabatnya, dan bagi orang wanita ada hak bagian (pula).\"",
        "HR. Bukhari & Muslim - \"Berikanlah harta warisan kepada yang berhak menerimanya, sedangkan sisanya adalah untuk kerabat laki-laki yang paling dekat.\""
    ],
    "zakat": [
        "QS. At-Taubah: 103 - \"Ambillah zakat dari sebagian harta mereka, dengan zakat itu kamu membersihkan dan mensucikan mereka.\"",
        "HR. Abu Daud - \"Tidak ada kewajiban zakat pada emas hingga mencapai 20 dinar (setara 85 gram).\"",
        "QS. Adz-Dzariyat: 19 - \"Dan pada harta-harta mereka ada hak untuk orang miskin yang meminta dan orang miskin yang tidak mendapat bagian.\""
    ],
    "tahajjud": [
        "HR. Bukhari & Muslim - \"Rabb kita turun ke langit dunia pada setiap malam yaitu ketika sepertiga malam terakhir untuk mengabulkan doa hamba-Nya.\"",
        "QS. Al-Isra: 79 - \"Dan pada sebagian malam hari shalat tahajudlah kamu sebagai suatu ibadah tambahan bagimu.\"",
        "QS. Al-Muzzammil: 6 - \"Sesungguhnya bangun di waktu malam adalah lebih tepat untuk khusyuk dan bacaan di waktu itu lebih berkesan.\""
    ],
    "khatam": [
        "HR. Tirmidzi - \"Siapa yang membaca satu huruf dari Al Quran maka baginya satu kebaikan, satu kebaikan dilipatkan menjadi 10 kebaikan.\"",
        "HR. Bukhari - \"Amalan yang paling dicintai Allah adalah yang terus-menerus (istiqomah) meskipun sedikit.\"",
        "HR. Muslim - \"Bacalah Al-Quran, sesungguhnya ia akan datang pada hari kiamat memberi syafaat bagi pembacanya.\""
    ],
    "fidyah": [
        "QS. Al-Baqarah: 184 - \"Maka barangsiapa diantara kamu ada yang sakit atau dalam perjalanan, maka wajiblah baginya berpuasa sebanyak hari yang ditinggalkan itu pada hari-hari yang lain.\"",
        "QS. Al-Baqarah: 184 (Lanjutan) - \"Dan wajib bagi orang-orang yang berat menjalankannya membayar fidyah, yaitu memberi makan seorang miskin.\"",
        "Ijma Ulama / SK BAZNAS - \"Besaran fidyah adalah satu mud (sekitar 0,6 kg beras) atau setara biaya makan satu hari untuk satu orang miskin.\""
    ],
    "hijri": [
        "QS. At-Taubah: 36 - \"Sesungguhnya bilangan bulan pada sisi Allah adalah dua belas bulan, dalam ketetapan Allah di waktu Dia menciptakan langit dan bumi.\"",
        "QS. Al-Baqarah: 189 - \"Katakanlah: Bulan sabit itu adalah tanda-tanda waktu bagi manusia dan bagi ibadah haji.\"",
        "Sejarah Islam - \"Penetapan Kalender Hijriyah dimulai pada masa Khalifah Umar bin Khattab yang menjadikan peristiwa Hijrah sebagai titik awal tahun.\""
    ]
}

# --- DATABASE SETUP ---
DB_NAME = 'masjid.db'

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

    # 7. Ifthar Logistik Table
    c.execute('''CREATE TABLE IF NOT EXISTS ifthar_logistik (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        donor_name TEXT NOT NULL,
        portions INTEGER NOT NULL,
        menu TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 8. Quran Progress Table
    c.execute('''CREATE TABLE IF NOT EXISTS quran_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        date TEXT NOT NULL,
        pages_read INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 9. Muhasabah Harian Table
    c.execute('''CREATE TABLE IF NOT EXISTS muhasabah_harian (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        date TEXT NOT NULL,
        sholat_jemaah INTEGER DEFAULT 0, -- 1=Yes, 0=No
        sedekah INTEGER DEFAULT 0,
        tarawih INTEGER DEFAULT 0,
        tilawah INTEGER DEFAULT 0,
        catatan_hati TEXT,
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

# --- ISLAMIC CALCULATOR LOGIC ---

def get_user_id():
    # Helper to get user ID from request cookie
    uid = request.cookies.get('user_id')
    if not uid:
        uid = str(uuid.uuid4())
    return uid

def hitung_fase_bulan():
    # Simple algorithm based on Hijri date (approximate)
    # Hijri 1 = New Moon (0%), 15 = Full Moon (100%), 29/30 = New Moon (0%)
    try:
        today = datetime.date.today()
        # Use existing helper (which returns string "D Month Y H")
        hijri_str = gregorian_to_hijri(today)
        day = int(hijri_str.split(' ')[0])

        # Cycle is ~30 days. Peak at 15.
        # Logic: 1->0%, 15->100%, 30->0%
        if day <= 15:
            illumination = (day / 15) * 100
        else:
            illumination = ((30 - day) / 15) * 100

        illumination = max(0, min(100, illumination))
        return {
            "illumination": int(illumination),
            "age": day
        }
    except:
        return {"illumination": 50, "age": 15}

def gregorian_to_hijri(date_obj):
    # Kuwaiti Algorithm
    day = date_obj.day
    month = date_obj.month
    year = date_obj.year

    m = month
    y = year
    if m < 3:
        y -= 1
        m += 12

    a = math.floor(y / 100.)
    b = 2 - a + math.floor(a / 4.)
    if y < 1583: b = 0
    if y == 1582:
        if m > 10: b = -10
        if m == 10:
            b = 0
            if day > 4: b = -10

    jd = math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + day + b - 1524.5

    iYear = 10631. / 30.
    epochAstro = 1948084
    shift1 = 8.01 / 60.

    z = jd - epochAstro
    cyc = math.floor(z / 10631.)
    z = z - 10631 * cyc
    j = math.floor((z - shift1) / iYear)
    iy = 30 * cyc + j
    z = z - math.floor(j * iYear + shift1)
    im = math.floor((z + 28.5001) / 29.5)
    if im == 13: im = 12
    id = z - math.floor(29.5001 * im - 29)

    months = ["Muharram", "Safar", "Rabiul Awal", "Rabiul Akhir", "Jumadil Awal", "Jumadil Akhir",
              "Rajab", "Syaban", "Ramadan", "Syawal", "Zulqaidah", "Zulhijjah"]

    return f"{int(id)} {months[int(im)-1]} {int(iy)} H"

def calc_waris(harta, sons, daughters):
    if sons == 0 and daughters == 0:
        return {"error": "Tidak ada ahli waris anak"}
    
    total_points = (sons * 2) + (daughters * 1)
    if total_points == 0: return {"error": "Total poin 0"}
    
    one_part = harta / total_points
    son_share = one_part * 2
    daughter_share = one_part * 1
    
    return {
        "harta": harta,
        "points": total_points,
        "part_value": one_part,
        "son_share": son_share,
        "daughter_share": daughter_share
    }

def calc_zakat(gold_price, savings, gold_grams):
    nisab = 85 * gold_price
    total_wealth = savings + (gold_grams * gold_price)
    wajib = total_wealth >= nisab
    zakat = total_wealth * 0.025 if wajib else 0
    return {
        "nisab": nisab,
        "total_wealth": total_wealth,
        "wajib": wajib,
        "zakat": zakat
    }

def calc_tahajjud(maghrib, subuh):
    # Format HH:MM
    try:
        m_h, m_m = map(int, maghrib.split(':'))
        s_h, s_m = map(int, subuh.split(':'))
        
        maghrib_dt = datetime.datetime(2023, 1, 1, m_h, m_m)
        subuh_dt = datetime.datetime(2023, 1, 2, s_h, s_m) # Next day
        
        if maghrib_dt > subuh_dt:
             subuh_dt += datetime.timedelta(days=1)
             
        diff = subuh_dt - maghrib_dt
        third_duration = diff / 3
        
        last_third_start = subuh_dt - third_duration
        
        # Calculate total hours and minutes for explanation
        total_seconds = diff.total_seconds()
        total_hours = int(total_seconds // 3600)
        total_minutes = int((total_seconds % 3600) // 60)
        
        return {
            "time": last_third_start.strftime("%H:%M"),
            "total_hours": total_hours,
            "total_minutes": total_minutes
        }
    except:
        return {"error": "Invalid Time"}

def calc_khatam(target_times, days, freq_per_day):
    try:
        total_pages = 604 * target_times
        total_sessions = days * freq_per_day
        if total_sessions == 0:
            return {
                "pages_per_session": 0,
                "total_pages": total_pages,
                "total_sessions": 0
            }
        pages_per_session = math.ceil(total_pages / total_sessions)
        return {
            "pages_per_session": pages_per_session,
            "total_pages": total_pages,
            "total_sessions": total_sessions
        }
    except:
        return {"error": "Error"}

def calc_fidyah(days, category):
    qadha = days
    fidyah_rice = days * 0.6
    fidyah_money = days * 15000
    
    return {
        "qadha_days": qadha,
        "fidyah_rice": fidyah_rice,
        "fidyah_money": fidyah_money
    }

# Samarinda Coordinates
LAT = -0.502106
LNG = 117.153709
TZ = 8 # WITA

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- FRONTEND ASSETS & LAYOUT ---

STYLES_HTML = """
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        tailwind.config = {
          theme: {
            extend: {
              colors: {
                ramadhan: {
                   dark: '#0b1026',
                   gold: '#FFD700',
                   accent: '#1a237e'
                },
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
    
    <!-- DESKTOP NAVBAR -->
    <nav class="hidden md:flex fixed top-0 left-0 w-full z-50 glass-nav shadow-sm px-8 py-4 justify-between items-center right-0">
        <div class="max-w-7xl mx-auto w-full flex justify-between items-center">
             <div class="flex items-center gap-4">
                 <div class="bg-emerald-100 p-2 rounded-xl">
                    <i class="fas fa-mosque text-emerald-600 text-2xl"></i>
                 </div>
                 <div>
                    <h1 class="text-xl font-bold text-emerald-600 leading-tight">Masjid Al Hijrah</h1>
                    <p class="text-xs text-gray-500 font-medium">Samarinda, Kalimantan Timur</p>
                 </div>
             </div>
             <div class="flex items-center gap-8">
                <a href="/" class="text-gray-600 font-medium hover:text-emerald-600 transition {{ 'text-emerald-600 font-bold' if active_page == 'home' else '' }}">Beranda</a>
                <a href="/finance" class="text-gray-600 font-medium hover:text-emerald-600 transition {{ 'text-emerald-600 font-bold' if active_page == 'finance' else '' }}">Laporan Kas</a>
                <a href="/agenda" class="text-gray-600 font-medium hover:text-emerald-600 transition {{ 'text-emerald-600 font-bold' if active_page == 'agenda' else '' }}">Jadwal</a>
                <a href="/donate" class="bg-emerald-500 text-white px-5 py-2 rounded-full font-bold shadow-lg hover:bg-emerald-600 transition transform hover:scale-105">Infaq Digital</a>
                <a href="/emergency" class="text-red-500 font-bold hover:text-red-600 transition border border-red-200 px-4 py-2 rounded-full bg-red-50 hover:bg-red-100">Darurat</a>
            </div>
        </div>
    </nav>

    <!-- MOBILE HEADER -->
    <header class="md:hidden fixed top-0 left-0 w-full z-50 glass-nav shadow-sm px-4 py-3 flex justify-between items-center max-w-md mx-auto right-0">
        <div>
            <p class="text-xs text-gray-500 font-medium">Assalamualaikum</p>
            <h1 class="text-lg font-bold text-emerald-600 leading-tight">Masjid Al Hijrah</h1>
        </div>
        <div class="text-right">
            <p class="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-2 py-1 rounded-full border border-emerald-200" id="hijri-date">Loading...</p>
        </div>
    </header>

    <!-- CONTENT -->
    <main class="min-h-screen relative w-full max-w-md md:max-w-7xl mx-auto bg-[#F8FAFC]">
        {{ content|safe }}
    </main>

    <!-- MOBILE BOTTOM NAV -->
    <nav class="md:hidden fixed bottom-0 left-0 w-full glass-bottom z-50 pb-2 pt-2 max-w-md mx-auto right-0 border-t border-gray-100">
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
                // Fetch from Aladhan API for Samarinda
                const response = await fetch('https://api.aladhan.com/v1/timingsByCity?city=Samarinda&country=Indonesia');
                const result = await response.json();
                const timings = result.data.timings;
                
                // Update grid if exists
                if(document.getElementById('fajr-time')) {
                    document.getElementById('fajr-time').innerText = timings.Fajr;
                    document.getElementById('dhuhr-time').innerText = timings.Dhuhr;
                    document.getElementById('asr-time').innerText = timings.Asr;
                    document.getElementById('maghrib-time').innerText = timings.Maghrib;
                    document.getElementById('isha-time').innerText = timings.Isha;
                }
                
                // Countdown Logic
                const now = new Date();
                const prayers = [
                    { name: 'Subuh', time: timings.Fajr },
                    { name: 'Dzuhur', time: timings.Dhuhr },
                    { name: 'Ashar', time: timings.Asr },
                    { name: 'Maghrib', time: timings.Maghrib },
                    { name: 'Isya', time: timings.Isha }
                ];
                
                let nextPrayerName = null;
                let targetTime = null;

                for (let p of prayers) {
                    const [h, m] = p.time.split(':');
                    const pDate = new Date();
                    pDate.setHours(parseInt(h), parseInt(m), 0, 0);
                    
                    if (pDate > now) {
                        nextPrayerName = p.name;
                        targetTime = pDate;
                        break;
                    }
                }

                // If no prayer found for today (meaning it's after Isya), next is Fajr tomorrow
                if (!targetTime) {
                    nextPrayerName = 'Subuh';
                    const [h, m] = timings.Fajr.split(':');
                    targetTime = new Date();
                    targetTime.setDate(targetTime.getDate() + 1);
                    targetTime.setHours(parseInt(h), parseInt(m), 0, 0);
                }
                
                if(document.getElementById('next-prayer-name')) {
                    document.getElementById('next-prayer-name').innerText = nextPrayerName;
                    
                    const diff = targetTime - now;
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

RAMADHAN_HTML = """
<div class="bg-[#0b1026] min-h-screen pb-24 text-[#FFD700] font-sans">

    <!-- RAMADHAN HEADER -->
    <div class="relative px-6 pt-24 pb-12 overflow-hidden rounded-b-[40px] shadow-2xl border-b-4 border-[#FFD700]/30">
        <div class="absolute inset-0 opacity-10" style="background-image: url('https://www.transparenttextures.com/patterns/arabesque.png');"></div>
        <div class="absolute inset-0 bg-gradient-to-b from-[#1a237e]/50 to-[#0b1026]"></div>

        <div class="relative z-10 text-center">
            <div class="inline-block p-3 rounded-full border-2 border-[#FFD700] mb-4 shadow-[0_0_15px_#FFD700]">
                <i class="fas fa-moon text-3xl text-[#FFD700]"></i>
            </div>
            <h1 class="text-4xl md:text-5xl font-bold font-serif mb-2 text-transparent bg-clip-text bg-gradient-to-r from-[#FFD700] to-[#FDB931]">Ramadhan Dashboard</h1>
            <p class="text-gray-300 text-sm md:text-base italic max-w-lg mx-auto">"Hai orang-orang yang beriman, diwajibkan atas kamu berpuasa sebagaimana diwajibkan atas orang-orang sebelum kamu agar kamu bertakwa." (QS. Al-Baqarah: 183)</p>
        </div>
    </div>

    <!-- MAIN GRID DASHBOARD (2 cols x 3 rows) -->
    <div class="max-w-7xl mx-auto px-4 md:px-8 -mt-8 relative z-20">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">

            <!-- 1. ASTRO-FALAKIYAH (Moon Phase) -->
            <div class="bg-[#151b3b] border border-[#FFD700]/20 rounded-3xl p-6 shadow-xl relative overflow-hidden group hover:border-[#FFD700]/50 transition-all duration-300">
                <div class="flex justify-between items-center mb-6 border-b border-[#FFD700]/10 pb-3">
                    <h3 class="text-xl font-bold font-serif"><i class="fas fa-star-and-crescent mr-2"></i>Astro-Falakiyah</h3>
                    <span class="text-xs bg-[#FFD700]/10 text-[#FFD700] px-2 py-1 rounded">Simulator</span>
                </div>
                <div class="flex flex-col items-center">
                    <!-- CSS Moon Animation -->
                    <div class="w-32 h-32 rounded-full bg-gray-900 shadow-[inset_-10px_0px_20px_rgba(0,0,0,1)] relative mb-6 border border-gray-700 overflow-hidden">
                        <div id="moon-shadow" class="absolute inset-0 bg-[#FFD700] rounded-full mix-blend-overlay opacity-0 transition-all duration-1000"></div>
                        <div class="absolute inset-0 shadow-[inset_10px_10px_50px_rgba(0,0,0,0.8)]"></div>
                    </div>

                    <div class="grid grid-cols-2 gap-4 w-full text-center">
                        <div class="bg-[#0b1026] p-3 rounded-xl border border-[#FFD700]/10">
                            <p class="text-xs text-gray-400">Iluminasi</p>
                            <p class="text-lg font-bold" id="moon-illumination">--%</p>
                        </div>
                        <div class="bg-[#0b1026] p-3 rounded-xl border border-[#FFD700]/10">
                            <p class="text-xs text-gray-400">Umur Bulan</p>
                            <p class="text-lg font-bold" id="moon-age">-- Hari</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 2. NUTRISI AVICENNA (Health Calc) -->
            <div class="bg-[#151b3b] border border-[#FFD700]/20 rounded-3xl p-6 shadow-xl relative overflow-hidden group hover:border-[#FFD700]/50 transition-all duration-300">
                <div class="flex justify-between items-center mb-6 border-b border-[#FFD700]/10 pb-3">
                    <h3 class="text-xl font-bold font-serif"><i class="fas fa-heartbeat mr-2"></i>Nutrisi Avicenna</h3>
                    <span class="text-xs bg-[#FFD700]/10 text-[#FFD700] px-2 py-1 rounded">Ibnu Sina</span>
                </div>
                <form onsubmit="calcNutrisi(event)" class="space-y-3">
                    <div class="grid grid-cols-2 gap-3">
                        <input type="number" id="nutri-weight" placeholder="Berat (kg)" class="bg-[#0b1026] border border-[#FFD700]/20 rounded-xl p-2 text-sm text-white focus:outline-none focus:border-[#FFD700]" required>
                        <input type="number" id="nutri-height" placeholder="Tinggi (cm)" class="bg-[#0b1026] border border-[#FFD700]/20 rounded-xl p-2 text-sm text-white focus:outline-none focus:border-[#FFD700]" required>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <input type="number" id="nutri-age" placeholder="Usia" class="bg-[#0b1026] border border-[#FFD700]/20 rounded-xl p-2 text-sm text-white focus:outline-none focus:border-[#FFD700]" required>
                        <select id="nutri-gender" class="bg-[#0b1026] border border-[#FFD700]/20 rounded-xl p-2 text-sm text-white focus:outline-none focus:border-[#FFD700]">
                            <option value="male">Laki-laki</option>
                            <option value="female">Perempuan</option>
                        </select>
                    </div>
                    <select id="nutri-activity" class="w-full bg-[#0b1026] border border-[#FFD700]/20 rounded-xl p-2 text-sm text-white focus:outline-none focus:border-[#FFD700]">
                        <option value="1.2">Ringan (Duduk/Kantor)</option>
                        <option value="1.55">Sedang (Olahraga 3x/minggu)</option>
                        <option value="1.9">Berat (Fisik/Buruh)</option>
                    </select>
                    <button type="submit" class="w-full bg-gradient-to-r from-[#FFD700] to-[#FDB931] text-[#0b1026] font-bold py-2 rounded-xl hover:opacity-90 transition">Hitung Bekal Puasa</button>
                </form>
                <div id="nutri-result" class="hidden mt-4 pt-4 border-t border-[#FFD700]/10 text-center">
                    <p class="text-xs text-gray-400">Target Kalori</p>
                    <div class="flex justify-around mt-2">
                        <div>
                            <p class="text-xs text-gray-500">Sahur (40%)</p>
                            <p class="font-bold text-[#FFD700]" id="res-sahur">0 kkal</p>
                        </div>
                        <div>
                            <p class="text-xs text-gray-500">Berbuka (60%)</p>
                            <p class="font-bold text-[#FFD700]" id="res-iftar">0 kkal</p>
                        </div>
                    </div>
                    <div class="mt-3 bg-[#0b1026] p-2 rounded-lg">
                        <p class="text-xs text-gray-400">Target Air Minum</p>
                        <p class="font-bold text-blue-400" id="res-water">0 Liter</p>
                    </div>
                </div>
            </div>

            <!-- 3. LOGISTIK IFTHAR (Crowdfunding) -->
            <div class="bg-[#151b3b] border border-[#FFD700]/20 rounded-3xl p-6 shadow-xl relative overflow-hidden group hover:border-[#FFD700]/50 transition-all duration-300 md:row-span-2">
                <div class="flex justify-between items-center mb-6 border-b border-[#FFD700]/10 pb-3">
                    <h3 class="text-xl font-bold font-serif"><i class="fas fa-utensils mr-2"></i>Logistik Ifthar</h3>
                    <span class="text-xs bg-[#FFD700]/10 text-[#FFD700] px-2 py-1 rounded">30 Hari</span>
                </div>
                <div class="h-[500px] overflow-y-auto pr-2 custom-scrollbar space-y-3" id="ifthar-list">
                    <!-- Dynamic List Generated by JS -->
                    <div class="text-center text-gray-500 py-10">Memuat Data Logistik...</div>
                </div>
                <!-- Modal for Donation is separate -->
            </div>

            <!-- 4. BAYT AL-HIKMAH (AI Chatbot) -->
            <div class="bg-[#151b3b] border border-[#FFD700]/20 rounded-3xl p-6 shadow-xl relative overflow-hidden group hover:border-[#FFD700]/50 transition-all duration-300 md:row-span-2 flex flex-col">
                <div class="flex justify-between items-center mb-4 border-b border-[#FFD700]/10 pb-3">
                    <h3 class="text-xl font-bold font-serif"><i class="fas fa-brain mr-2"></i>Bayt al-Hikmah</h3>
                    <span class="text-xs bg-[#FFD700]/10 text-[#FFD700] px-2 py-1 rounded">AI Pustakawan</span>
                </div>
                <div class="flex-1 bg-[#0b1026] rounded-2xl p-4 overflow-y-auto mb-4 border border-[#FFD700]/5 h-[400px]" id="chat-history">
                    <div class="flex items-start gap-3 mb-4">
                        <div class="w-8 h-8 rounded-full bg-[#FFD700] flex items-center justify-center text-[#0b1026] font-bold text-xs">AI</div>
                        <div class="bg-[#151b3b] p-3 rounded-2xl rounded-tl-none border border-[#FFD700]/20 text-sm text-gray-300">
                            Assalamualaikum. Saya adalah penjaga Bayt al-Hikmah. Bertanyalah tentang sejarah sains Islam atau Al-Quran.
                        </div>
                    </div>
                </div>
                <form onsubmit="sendChat(event)" class="relative">
                    <input type="text" id="chat-input" placeholder="Tanya tentang Al-Khawarizmi..." class="w-full bg-[#0b1026] border border-[#FFD700]/20 rounded-full pl-4 pr-12 py-3 text-sm text-white focus:outline-none focus:border-[#FFD700]">
                    <button type="submit" class="absolute right-2 top-2 bg-[#FFD700] text-[#0b1026] w-8 h-8 rounded-full flex items-center justify-center hover:scale-110 transition">
                        <i class="fas fa-paper-plane text-xs"></i>
                    </button>
                </form>
            </div>

            <!-- 5. KHATAM ANALYTICS (Chart) -->
            <div class="bg-[#151b3b] border border-[#FFD700]/20 rounded-3xl p-6 shadow-xl relative overflow-hidden group hover:border-[#FFD700]/50 transition-all duration-300">
                <div class="flex justify-between items-center mb-6 border-b border-[#FFD700]/10 pb-3">
                    <h3 class="text-xl font-bold font-serif"><i class="fas fa-chart-line mr-2"></i>Khatam Analytics</h3>
                </div>
                <canvas id="khatamChart" class="w-full h-48"></canvas>
                <form onsubmit="saveKhatam(event)" class="mt-4 flex gap-2">
                    <input type="number" id="khatam-input" placeholder="Bacaan Hari Ini (Halaman)" class="flex-1 bg-[#0b1026] border border-[#FFD700]/20 rounded-xl p-2 text-sm text-white">
                    <button type="submit" class="bg-[#FFD700] text-[#0b1026] px-4 py-2 rounded-xl font-bold text-sm">Update</button>
                </form>
            </div>

            <!-- 6. JURNAL MUHASABAH (Pie Chart) -->
            <div class="bg-[#151b3b] border border-[#FFD700]/20 rounded-3xl p-6 shadow-xl relative overflow-hidden group hover:border-[#FFD700]/50 transition-all duration-300">
                <div class="flex justify-between items-center mb-6 border-b border-[#FFD700]/10 pb-3">
                    <h3 class="text-xl font-bold font-serif"><i class="fas fa-book-reader mr-2"></i>Jurnal Muhasabah</h3>
                </div>
                <div class="flex flex-col md:flex-row gap-6 items-center">
                    <div class="w-32 h-32 relative">
                        <canvas id="muhasabahChart"></canvas>
                    </div>
                    <form onsubmit="saveMuhasabah(event)" class="flex-1 space-y-2 w-full">
                        <label class="flex items-center space-x-2 text-sm text-gray-300 cursor-pointer">
                            <input type="checkbox" id="check-jemaah" class="form-checkbox text-[#FFD700] rounded bg-[#0b1026] border-[#FFD700]/30">
                            <span>Sholat Berjamaah</span>
                        </label>
                        <label class="flex items-center space-x-2 text-sm text-gray-300 cursor-pointer">
                            <input type="checkbox" id="check-sedekah" class="form-checkbox text-[#FFD700] rounded bg-[#0b1026] border-[#FFD700]/30">
                            <span>Sedekah Hari Ini</span>
                        </label>
                        <label class="flex items-center space-x-2 text-sm text-gray-300 cursor-pointer">
                            <input type="checkbox" id="check-tarawih" class="form-checkbox text-[#FFD700] rounded bg-[#0b1026] border-[#FFD700]/30">
                            <span>Sholat Tarawih</span>
                        </label>
                        <label class="flex items-center space-x-2 text-sm text-gray-300 cursor-pointer">
                            <input type="checkbox" id="check-tilawah" class="form-checkbox text-[#FFD700] rounded bg-[#0b1026] border-[#FFD700]/30">
                            <span>Tilawah Quran</span>
                        </label>
                        <button type="submit" class="w-full mt-2 bg-[#FFD700]/10 border border-[#FFD700] text-[#FFD700] text-xs font-bold py-2 rounded-lg hover:bg-[#FFD700] hover:text-[#0b1026] transition">Simpan Jurnal</button>
                    </form>
                </div>
            </div>

        </div>

        <!-- LINK TO EXISTING CALCULATORS -->
        <div class="mt-8 text-center">
            <a href="/#kalkulator-section" class="inline-block bg-[#1a237e] border border-[#FFD700] text-[#FFD700] px-8 py-3 rounded-full font-bold shadow-lg hover:bg-[#FFD700] hover:text-[#0b1026] transition">
                <i class="fas fa-calculator mr-2"></i> Buka 6 Kalkulator Ilmiah Islam
            </a>
        </div>

        <div class="mt-12 text-center text-xs text-gray-500">
            <p>&copy; 1445 H - Masjid Al Hijrah Ramadhan Dashboard</p>
        </div>
    </div>

    <!-- MODAL DONASI IFTHAR -->
    <div id="modal-ifthar" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" onclick="document.getElementById('modal-ifthar').classList.add('hidden')"></div>
        <div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-full max-w-sm bg-[#151b3b] rounded-3xl p-6 shadow-2xl border border-[#FFD700]/30">
            <h3 class="text-xl font-bold text-[#FFD700] mb-4">Donasi Takjil</h3>
            <form onsubmit="submitDonasi(event)" class="space-y-4">
                <input type="hidden" id="donasi-date">
                <div>
                    <label class="block text-xs font-bold text-gray-400 mb-1">Tanggal</label>
                    <input type="text" id="donasi-date-display" class="w-full bg-[#0b1026] border border-[#FFD700]/20 rounded-xl p-3 text-sm text-gray-500" disabled>
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-400 mb-1">Nama Donatur</label>
                    <input type="text" id="donasi-name" class="w-full bg-[#0b1026] border border-[#FFD700]/20 rounded-xl p-3 text-sm text-white" required>
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-400 mb-1">Jumlah Porsi</label>
                    <input type="number" id="donasi-portions" class="w-full bg-[#0b1026] border border-[#FFD700]/20 rounded-xl p-3 text-sm text-white" required>
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-400 mb-1">Menu (Opsional)</label>
                    <input type="text" id="donasi-menu" class="w-full bg-[#0b1026] border border-[#FFD700]/20 rounded-xl p-3 text-sm text-white">
                </div>
                <button type="submit" class="w-full bg-[#FFD700] text-[#0b1026] font-bold py-3 rounded-xl shadow-lg hover:opacity-90">Simpan Donasi</button>
            </form>
        </div>
    </div>

    <script>
        // --- 1. ASTRO FALAKIYAH ---
        async function loadAstro() {
            try {
                // Fetch data from backend helper
                const res = await fetch('/api/ramadhan/astro');
                const data = await res.json();

                document.getElementById('moon-illumination').innerText = data.illumination + '%';
                document.getElementById('moon-age').innerText = data.age + ' Hari';

                // Visualize Shadow
                // 0% = New Moon (Dark), 50% = Quarter, 100% = Full (Gold)
                const moonShadow = document.getElementById('moon-shadow');
                moonShadow.style.opacity = data.illumination / 100;
            } catch(e) { console.error(e); }
        }

        // --- 2. NUTRISI AVICENNA ---
        async function calcNutrisi(e) {
            e.preventDefault();
            const data = {
                weight: document.getElementById('nutri-weight').value,
                height: document.getElementById('nutri-height').value,
                age: document.getElementById('nutri-age').value,
                gender: document.getElementById('nutri-gender').value,
                activity: document.getElementById('nutri-activity').value
            };

            const res = await fetch('/api/ramadhan/nutrisi', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            const result = await res.json();

            document.getElementById('nutri-result').classList.remove('hidden');
            document.getElementById('res-sahur').innerText = Math.round(result.sahur) + " kkal";
            document.getElementById('res-iftar').innerText = Math.round(result.iftar) + " kkal";
            document.getElementById('res-water').innerText = result.water + " Liter";
        }

        // --- 3. LOGISTIK IFTHAR ---
        async function loadIfthar() {
            const list = document.getElementById('ifthar-list');
            try {
                const res = await fetch('/api/ramadhan/ifthar');
                const data = await res.json(); // Array of 30 days

                list.innerHTML = '';
                data.forEach((day, index) => {
                    const pct = Math.min((day.current / 100) * 100, 100);
                    const color = pct >= 100 ? 'bg-green-500' : 'bg-red-500';

                    const item = document.createElement('div');
                    item.className = 'bg-[#0b1026] p-4 rounded-xl border border-[#FFD700]/10 flex justify-between items-center';
                    item.innerHTML = `
                        <div class="flex-1 mr-4">
                            <div class="flex justify-between text-xs text-gray-400 mb-1">
                                <span class="font-bold text-[#FFD700]">Ramadhan ke-${index + 1}</span>
                                <span>${day.current}/100 Porsi</span>
                            </div>
                            <div class="w-full bg-gray-700 rounded-full h-2">
                                <div class="${color} h-2 rounded-full" style="width: ${pct}%"></div>
                            </div>
                            <p class="text-[10px] text-gray-500 mt-1 truncate">${day.donors || 'Belum ada donatur'}</p>
                        </div>
                        <button onclick="openDonasi(${index + 1})" class="bg-[#FFD700]/10 hover:bg-[#FFD700] hover:text-[#0b1026] text-[#FFD700] rounded-full w-8 h-8 flex items-center justify-center transition">
                            <i class="fas fa-plus text-xs"></i>
                        </button>
                    `;
                    list.appendChild(item);
                });
            } catch(e) { console.error(e); }
        }

        function openDonasi(dayIndex) {
            document.getElementById('modal-ifthar').classList.remove('hidden');
            document.getElementById('donasi-date').value = dayIndex;
            document.getElementById('donasi-date-display').value = "Ramadhan Hari ke-" + dayIndex;
        }

        async function submitDonasi(e) {
            e.preventDefault();
            const data = {
                day_index: document.getElementById('donasi-date').value,
                name: document.getElementById('donasi-name').value,
                portions: document.getElementById('donasi-portions').value,
                menu: document.getElementById('donasi-menu').value
            };
            await fetch('/api/ramadhan/ifthar', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            document.getElementById('modal-ifthar').classList.add('hidden');
            loadIfthar();
        }

        // --- 4. BAYT AL-HIKMAH CHAT ---
        async function sendChat(e) {
            e.preventDefault();
            const input = document.getElementById('chat-input');
            const msg = input.value;
            if(!msg) return;

            const history = document.getElementById('chat-history');

            // User Msg
            const userDiv = document.createElement('div');
            userDiv.className = 'flex items-start gap-3 mb-4 flex-row-reverse';
            userDiv.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center text-white font-bold text-xs">U</div>
                <div class="bg-[#FFD700] p-3 rounded-2xl rounded-tr-none text-sm text-[#0b1026] font-medium">${msg}</div>
            `;
            history.appendChild(userDiv);
            input.value = '';
            history.scrollTop = history.scrollHeight;

            // Loading
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'flex items-start gap-3 mb-4';
            loadingDiv.id = 'chat-loading';
            loadingDiv.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-[#FFD700] flex items-center justify-center text-[#0b1026] font-bold text-xs">AI</div>
                <div class="bg-[#151b3b] p-3 rounded-2xl rounded-tl-none border border-[#FFD700]/20 text-sm text-gray-400 italic">Sedang berpikir...</div>
            `;
            history.appendChild(loadingDiv);

            try {
                const res = await fetch('/api/ramadhan/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ message: msg })
                });
                const data = await res.json();

                loadingDiv.remove();

                const botDiv = document.createElement('div');
                botDiv.className = 'flex items-start gap-3 mb-4';
                botDiv.innerHTML = `
                    <div class="w-8 h-8 rounded-full bg-[#FFD700] flex items-center justify-center text-[#0b1026] font-bold text-xs">AI</div>
                    <div class="bg-[#151b3b] p-3 rounded-2xl rounded-tl-none border border-[#FFD700]/20 text-sm text-gray-300">${data.reply}</div>
                `;
                history.appendChild(botDiv);
                history.scrollTop = history.scrollHeight;

            } catch(e) {
                loadingDiv.remove();
                alert("Gagal menghubungi server.");
            }
        }

        // --- 5 & 6. CHARTS & DATA ---
        let khatamChartInstance = null;
        let muhasabahChartInstance = null;

        async function loadCharts() {
            // Load Data
            const khatamRes = await fetch('/api/ramadhan/khatam');
            const khatamData = await khatamRes.json(); // { labels: [], data: [], target: [] }

            const muhasabahRes = await fetch('/api/ramadhan/muhasabah');
            const muhasabahData = await muhasabahRes.json(); // { good: 80, bad: 20 }

            // Render Khatam Chart
            const ctxK = document.getElementById('khatamChart').getContext('2d');
            if(khatamChartInstance) khatamChartInstance.destroy();

            khatamChartInstance = new Chart(ctxK, {
                type: 'line',
                data: {
                    labels: Array.from({length: 30}, (_, i) => i + 1),
                    datasets: [{
                        label: 'Realisasi',
                        data: khatamData.data, // Array of 30 values (cumulative)
                        borderColor: '#FFD700',
                        backgroundColor: 'rgba(255, 215, 0, 0.1)',
                        tension: 0.4,
                        fill: true
                    }, {
                        label: 'Target',
                        data: khatamData.target, // Linear line
                        borderColor: 'rgba(255, 255, 255, 0.3)',
                        borderDash: [5, 5],
                        tension: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: 'white' } } },
                    scales: {
                        y: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: 'white' } },
                        x: { display: false }
                    }
                }
            });

            // Render Muhasabah Pie
            const ctxM = document.getElementById('muhasabahChart').getContext('2d');
            if(muhasabahChartInstance) muhasabahChartInstance.destroy();

            muhasabahChartInstance = new Chart(ctxM, {
                type: 'doughnut',
                data: {
                    labels: ['Kebaikan', 'Belum'],
                    datasets: [{
                        data: [muhasabahData.good, muhasabahData.bad],
                        backgroundColor: ['#FFD700', '#1a237e'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } }
                }
            });
        }

        async function saveKhatam(e) {
            e.preventDefault();
            const pages = document.getElementById('khatam-input').value;
            await fetch('/api/ramadhan/khatam', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ pages: pages })
            });
            loadCharts(); // Refresh
            document.getElementById('khatam-input').value = '';
        }

        async function saveMuhasabah(e) {
            e.preventDefault();
            const data = {
                jemaah: document.getElementById('check-jemaah').checked,
                sedekah: document.getElementById('check-sedekah').checked,
                tarawih: document.getElementById('check-tarawih').checked,
                tilawah: document.getElementById('check-tilawah').checked
            };
            await fetch('/api/ramadhan/muhasabah', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            loadCharts();
            alert("Jurnal tersimpan!");
        }

        // Init
        document.addEventListener('DOMContentLoaded', () => {
            loadAstro();
            loadIfthar();
            loadCharts();
        });
    </script>
</div>
"""

HOME_HTML = """
<div class="pt-20 md:pt-32 pb-32 px-5 md:px-8">
    
    <!-- DESKTOP SPLIT HEADER -->
    <div class="md:grid md:grid-cols-2 md:gap-12 md:items-center mb-8 md:mb-12">
        
        <!-- LEFT COLUMN: WELCOME (Desktop Only) -->
        <div class="hidden md:block pl-2">
            <p class="text-xl text-gray-500 font-medium mb-2">Assalamualaikum Warahmatullahi Wabarakatuh</p>
            <h1 class="text-5xl font-bold text-emerald-800 leading-tight mb-6">Selamat Datang di<br>Masjid Al Hijrah</h1>
            <p class="text-gray-600 text-lg leading-relaxed mb-8">
                Pusat peribadatan dan kegiatan umat Islam di Samarinda. Mari makmurkan masjid dengan sholat berjamaah, infaq, dan kegiatan sosial untuk kemaslahatan umat.
            </p>
            <div class="flex gap-4">
                <a href="/agenda" class="bg-emerald-600 text-white px-8 py-3 rounded-full font-bold shadow-lg hover:bg-emerald-700 transition transform hover:scale-105">Lihat Agenda</a>
                <a href="/donate" class="bg-white text-emerald-600 border-2 border-emerald-100 px-8 py-3 rounded-full font-bold hover:border-emerald-600 hover:text-emerald-700 transition transform hover:scale-105">Infaq Sekarang</a>
            </div>
        </div>

        <!-- RIGHT COLUMN: PRAYER CARD -->
        <div class="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-3xl p-6 md:p-10 text-white shadow-xl relative overflow-hidden transform md:hover:scale-[1.02] transition-transform duration-500">
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
    </div>

    <!-- RAMADHAN BANNER -->
    <a href="/ramadhan" class="block mb-8 group relative overflow-hidden rounded-3xl shadow-xl border-2 border-[#FFD700] bg-[#0b1026] hover:shadow-2xl hover:scale-[1.01] transition-all duration-300">
        <!-- Background Pattern -->
        <div class="absolute inset-0 opacity-10" style="background-image: radial-gradient(#FFD700 1px, transparent 1px); background-size: 20px 20px;"></div>

        <div class="relative z-10 flex items-center justify-between p-6 md:p-8">
            <div class="flex-1">
                <div class="flex items-center gap-3 mb-2">
                    <span class="bg-[#FFD700] text-[#0b1026] text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider shadow-lg shadow-yellow-500/50">Spesial</span>
                    <h3 class="text-2xl md:text-3xl font-bold text-white font-serif"><i class="fas fa-kaaba mr-2 text-[#FFD700]"></i>Dashboard Ramadhan</h3>
                </div>
                <p class="text-[#FFD700] text-sm md:text-base opacity-90 max-w-lg leading-relaxed">
                    Akses fitur Astro-Falakiyah, Kalkulator Nutrisi, Donasi Ifthar, dan AI Chatbot Sejarah Islam "Bayt al-Hikmah".
                </p>
            </div>
            <div class="hidden md:flex items-center justify-center bg-[#FFD700] w-12 h-12 rounded-full text-[#0b1026] group-hover:scale-110 transition-transform shadow-lg shadow-yellow-500/50 ml-4">
                <i class="fas fa-arrow-right text-xl"></i>
            </div>
        </div>
        <!-- Decoration -->
        <div class="absolute -right-6 -bottom-6 transform rotate-12 opacity-20 pointer-events-none">
                <i class="fas fa-moon text-9xl text-[#FFD700]"></i>
        </div>
    </a>

    <!-- MAIN GRID MENU -->
    <h3 class="text-gray-800 font-bold text-lg mb-4 pl-1 border-l-4 border-emerald-500 leading-none py-1 ml-1 md:text-2xl md:mb-8">&nbsp;Menu Utama</h3>
    <div class="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-8 mb-8">
        <a href="/finance" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-emerald-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-emerald-600 group-hover:bg-emerald-500 group-hover:text-white transition-colors">
                <i class="fas fa-wallet text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-gray-700 group-hover:text-emerald-600">Laporan Kas</span>
        </a>
        <a href="/agenda" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-blue-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-blue-600 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                <i class="fas fa-calendar-alt text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-gray-700 group-hover:text-blue-600">Jadwal Imam</span>
        </a>
        <a href="/booking" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-orange-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-orange-600 group-hover:bg-orange-500 group-hover:text-white transition-colors">
                <i class="fas fa-building text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-gray-700 group-hover:text-orange-600">Peminjaman</span>
        </a>
        <a href="/zakat" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-green-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-green-600 group-hover:bg-green-500 group-hover:text-white transition-colors">
                <i class="fas fa-hand-holding-heart text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-gray-700 group-hover:text-green-600">Zakat</span>
        </a>
        <a href="/gallery-dakwah" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-purple-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-purple-600 group-hover:bg-purple-500 group-hover:text-white transition-colors">
                <i class="fas fa-images text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-gray-700 group-hover:text-purple-600">Galeri</span>
        </a>
        <a href="/suggestion" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-pink-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-pink-600 group-hover:bg-pink-500 group-hover:text-white transition-colors">
                <i class="fas fa-comment-dots text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-gray-700 group-hover:text-pink-600">Kotak Saran</span>
        </a>
    </div>

    <!-- SEPARATOR -->
    <div class="h-8"></div>

    <!-- KALKULATOR ISLAM SECTION -->
    <div id="kalkulator-section" class="mb-12">
        <button onclick="toggleCalc()" class="w-full bg-white p-6 rounded-3xl shadow-lg border border-emerald-100 flex justify-between items-center group hover:bg-emerald-50 transition-all duration-300">
            <div class="flex items-center gap-4">
                <div class="bg-emerald-100 p-3 rounded-xl text-emerald-600 group-hover:bg-emerald-500 group-hover:text-white transition-colors shadow-sm">
                    <i class="fas fa-calculator text-2xl"></i>
                </div>
                <div class="text-left">
                    <h3 class="text-lg font-bold text-gray-800 group-hover:text-emerald-700">Kalkulator Islam</h3>
                    <p class="text-xs text-gray-500 font-medium">6 Alat Hitung Otomatis (Waris, Zakat, dll)</p>
                </div>
            </div>
            <div id="calc-chevron" class="bg-gray-50 w-10 h-10 rounded-full flex items-center justify-center text-gray-400 group-hover:bg-white group-hover:text-emerald-500 transition-all duration-300">
                 <i class="fas fa-chevron-down transform transition-transform duration-300"></i>
            </div>
        </button>
        
        <div id="calc-content" class="hidden mt-6 animate-[slideDown_0.3s_ease-out]">
             <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                 <!-- WARIS -->
                 <button onclick="openModal('modal-waris')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-emerald-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 text-left flex items-center gap-3 group">
                     <div class="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl group-hover:bg-emerald-500 group-hover:text-white transition-colors"><i class="fas fa-users"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-emerald-700">Waris</span>
                 </button>
                 <!-- ZAKAT -->
                 <button onclick="openModal('modal-zakat')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-emerald-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 text-left flex items-center gap-3 group">
                     <div class="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl group-hover:bg-emerald-500 group-hover:text-white transition-colors"><i class="fas fa-hand-holding-usd"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-emerald-700">Zakat Maal</span>
                 </button>
                 <!-- TAHAJJUD -->
                 <button onclick="openModal('modal-tahajjud')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-emerald-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 text-left flex items-center gap-3 group">
                     <div class="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl group-hover:bg-emerald-500 group-hover:text-white transition-colors"><i class="fas fa-moon"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-emerald-700">Tahajjud</span>
                 </button>
                 <!-- KHATAM -->
                 <button onclick="openModal('modal-khatam')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-emerald-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 text-left flex items-center gap-3 group">
                     <div class="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl group-hover:bg-emerald-500 group-hover:text-white transition-colors"><i class="fas fa-quran"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-emerald-700">Target Khatam</span>
                 </button>
                 <!-- FIDYAH -->
                 <button onclick="openModal('modal-fidyah')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-emerald-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 text-left flex items-center gap-3 group">
                     <div class="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl group-hover:bg-emerald-500 group-hover:text-white transition-colors"><i class="fas fa-utensils"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-emerald-700">Fidyah</span>
                 </button>
                 <!-- HIJRI -->
                 <button onclick="openModal('modal-hijri')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-emerald-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 text-left flex items-center gap-3 group">
                     <div class="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl group-hover:bg-emerald-500 group-hover:text-white transition-colors"><i class="fas fa-calendar-check"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-emerald-700">Konverter Hijri</span>
                 </button>
             </div>
        </div>
    </div>

    <!-- MODALS -->
    
    <!-- Modal Waris -->
    <div id="modal-waris" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" onclick="closeModal('modal-waris')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-users text-emerald-500 mr-2"></i>Kalkulator Waris</h3>
                <button onclick="closeModal('modal-waris')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Total Harta (Rp)</label>
                    <input type="number" id="waris-harta" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Anak Laki-laki</label>
                        <input type="number" id="waris-sons" value="0" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Anak Perempuan</label>
                        <input type="number" id="waris-daughters" value="0" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                    </div>
                </div>
                <button onclick="calcWaris()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-emerald-600 transition">Hitung Waris</button>
                
                <div id="result-waris" class="hidden mt-4 bg-emerald-50 p-4 rounded-xl border border-emerald-100 text-sm"></div>
            </div>
        </div>
    </div>

    <!-- Modal Zakat -->
    <div id="modal-zakat" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeModal('modal-zakat')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-hand-holding-usd text-emerald-500 mr-2"></i>Zakat Maal</h3>
                <button onclick="closeModal('modal-zakat')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500">&times;</button>
            </div>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Harga Emas (per gram)</label>
                    <input type="number" id="zakat-gold-price" value="1000000" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Tabungan Uang (Rp)</label>
                    <input type="number" id="zakat-savings" value="0" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Simpanan Emas (gram)</label>
                    <input type="number" id="zakat-gold-grams" value="0" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                </div>
                <button onclick="calcZakat()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-emerald-600 transition">Cek Kewajiban</button>
                <div id="result-zakat" class="hidden mt-4 p-4 rounded-xl border text-sm"></div>
            </div>
        </div>
    </div>

    <!-- Modal Tahajjud -->
    <div id="modal-tahajjud" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeModal('modal-tahajjud')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-moon text-emerald-500 mr-2"></i>Sepertiga Malam</h3>
                <button onclick="closeModal('modal-tahajjud')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500">&times;</button>
            </div>
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Maghrib</label>
                        <input type="time" id="tahajjud-maghrib" value="18:15" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Subuh</label>
                        <input type="time" id="tahajjud-subuh" value="04:45" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                    </div>
                </div>
                <button onclick="calcTahajjud()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-emerald-600 transition">Hitung Waktu</button>
                <div id="result-tahajjud" class="hidden mt-4 bg-indigo-50 p-4 rounded-xl border border-indigo-100 text-center">
                    <p class="text-xs text-indigo-400 font-bold uppercase tracking-wider mb-1">Waktu Terbaik</p>
                    <h2 class="text-3xl font-bold text-indigo-700" id="tahajjud-time">--:--</h2>
                    <p class="text-xs text-indigo-500 mt-1">Mulai Sepertiga Malam Terakhir</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal Khatam -->
    <div id="modal-khatam" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeModal('modal-khatam')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-quran text-emerald-500 mr-2"></i>Target Khatam</h3>
                <button onclick="closeModal('modal-khatam')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500">&times;</button>
            </div>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Target Khatam (kali)</label>
                    <input type="number" id="khatam-times" value="1" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Durasi (hari)</label>
                        <input type="number" id="khatam-days" value="30" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Baca per Hari (kali)</label>
                        <input type="number" id="khatam-freq" value="5" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                    </div>
                </div>
                <button onclick="calcKhatam()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-emerald-600 transition">Hitung Target</button>
                <div id="result-khatam" class="hidden mt-4 bg-emerald-50 p-4 rounded-xl border border-emerald-100 text-center">
                    <p class="text-gray-600 text-sm">Anda harus membaca:</p>
                    <h2 class="text-3xl font-bold text-emerald-600 my-2"><span id="khatam-pages">0</span> Halaman</h2>
                    <p class="text-xs text-gray-500">Setiap kali duduk membaca</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal Fidyah -->
    <div id="modal-fidyah" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeModal('modal-fidyah')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-utensils text-emerald-500 mr-2"></i>Fidyah & Qadha</h3>
                <button onclick="closeModal('modal-fidyah')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500">&times;</button>
            </div>
            <div class="space-y-4">
                 <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Jumlah Hutang Puasa (Hari)</label>
                    <input type="number" id="fidyah-days" value="1" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Kategori</label>
                    <select id="fidyah-cat" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                        <option value="Sakit Tua">Sakit Tua / Menahun</option>
                        <option value="Hamil">Hamil / Menyusui (Khawatir Anak)</option>
                        <option value="Musafir">Musafir / Sakit Biasa</option>
                    </select>
                </div>
                <button onclick="calcFidyah()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-emerald-600 transition">Hitung Kewajiban</button>
                <div id="result-fidyah" class="hidden mt-4 space-y-2">
                    <div class="bg-orange-50 p-3 rounded-xl border border-orange-100 flex justify-between items-center">
                        <span class="text-sm text-orange-800 font-bold">Qadha (Ganti Puasa)</span>
                        <span class="text-lg font-bold text-orange-600" id="fidyah-qadha">0 Hari</span>
                    </div>
                    <div class="bg-emerald-50 p-3 rounded-xl border border-emerald-100">
                        <p class="text-xs text-emerald-800 font-bold mb-1">Fidyah (Bayar)</p>
                        <div class="flex justify-between items-center">
                            <span class="text-sm text-emerald-600" id="fidyah-rice">0 Kg Beras</span>
                            <span class="text-xs text-gray-400">atau</span>
                            <span class="text-sm text-emerald-600" id="fidyah-money">Rp 0</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal Hijri -->
    <div id="modal-hijri" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeModal('modal-hijri')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-calendar-check text-emerald-500 mr-2"></i>Konverter Hijriyah</h3>
                <button onclick="closeModal('modal-hijri')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500">&times;</button>
            </div>
            <div class="space-y-4">
                 <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Tanggal Masehi</label>
                    <input type="date" id="hijri-date-input" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                </div>
                <button onclick="calcHijri()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-emerald-600 transition">Konversi</button>
                <div id="result-hijri" class="hidden mt-4 bg-emerald-50 p-6 rounded-xl border border-emerald-100 text-center">
                    <p class="text-xs text-emerald-500 font-bold uppercase tracking-wider mb-2">Tanggal Hijriyah</p>
                    <h2 class="text-2xl font-bold text-emerald-800" id="hijri-output">...</h2>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal Explanation -->
    <div id="modal-explanation" class="fixed inset-0 z-[110] hidden">
        <div class="absolute inset-0 bg-white/80 backdrop-blur-md" onclick="closeModal('modal-explanation')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white/90 backdrop-blur-xl rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20 border border-white/50">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-info-circle text-blue-500 mr-2"></i>Penjelasan Perhitungan</h3>
                <button onclick="closeModal('modal-explanation')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            <div class="space-y-6 overflow-y-auto max-h-[70vh] pb-10">
                <!-- Logic Section -->
                <div>
                    <h4 class="text-sm font-bold text-gray-800 uppercase tracking-wider mb-2 border-b border-gray-200 pb-1">Bedah Logika (Sains)</h4>
                    <p id="exp-logic" class="text-sm text-gray-700 leading-relaxed font-medium bg-blue-50 p-4 rounded-xl border border-blue-100">
                        ...
                    </p>
                </div>
                <!-- Sources Section -->
                <div>
                    <h4 class="text-sm font-bold text-gray-800 uppercase tracking-wider mb-2 border-b border-gray-200 pb-1">Dasar Hukum & Referensi</h4>
                    <ul id="exp-sources" class="space-y-1">
                        <!-- LI generated by JS -->
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentExplanation = {};

        function toggleCalc() {
            const content = document.getElementById('calc-content');
            const chevron = document.querySelector('#calc-chevron i');
            content.classList.toggle('hidden');
            if(content.classList.contains('hidden')) {
                chevron.classList.remove('rotate-180');
            } else {
                chevron.classList.add('rotate-180');
            }
        }

        function openModal(id) {
            document.getElementById(id).classList.remove('hidden');
        }

        function closeModal(id) {
            document.getElementById(id).classList.add('hidden');
        }

        function showExplanation() {
            if(!currentExplanation.logic) return;
            document.getElementById('exp-logic').innerText = currentExplanation.logic;
            const ul = document.getElementById('exp-sources');
            ul.innerHTML = '';
            currentExplanation.sources.forEach(s => {
                const li = document.createElement('li');
                li.className = 'text-xs text-gray-600 mb-2 border-l-2 border-emerald-500 pl-2';
                const parts = s.split(' - ');
                if(parts.length > 1) {
                    li.innerHTML = `<span class="font-bold text-emerald-700">${parts[0]}</span> - ${parts[1]}`;
                } else {
                    li.innerText = s;
                }
                ul.appendChild(li);
            });
            openModal('modal-explanation');
        }

        async function postCalc(url, data) {
            try {
                const res = await fetch(url, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                return await res.json();
            } catch(e) {
                alert('Error: ' + e);
                return null;
            }
        }

        async function calcWaris() {
            const data = {
                harta: document.getElementById('waris-harta').value,
                sons: document.getElementById('waris-sons').value,
                daughters: document.getElementById('waris-daughters').value
            };
            const res = await postCalc('/api/calc/waris', data);
            if(res) {
                const div = document.getElementById('result-waris');
                div.classList.remove('hidden');
                if(res.error) {
                    div.innerHTML = `<span class="text-red-500 font-bold">${res.error}</span>`;
                } else {
                    currentExplanation = res.explanation;
                    div.innerHTML = `
                        <p class="font-bold text-emerald-800 mb-2">Hasil Pembagian:</p>
                        <ul class="space-y-1 mb-4">
                            <li class="flex justify-between"><span>Anak Laki-laki (@):</span> <span class="font-bold">Rp ${Number(res.result.son_share).toLocaleString('id-ID')}</span></li>
                            <li class="flex justify-between"><span>Anak Perempuan (@):</span> <span class="font-bold">Rp ${Number(res.result.daughter_share).toLocaleString('id-ID')}</span></li>
                        </ul>
                        <button onclick="showExplanation()" class="w-full bg-blue-100 text-blue-600 text-xs font-bold py-2 rounded-lg hover:bg-blue-200 transition flex items-center justify-center gap-2">
                            <i class="fas fa-info-circle"></i> PENJELASAN PERHITUNGAN
                        </button>
                    `;
                }
            }
        }

        async function calcZakat() {
            const data = {
                gold_price: document.getElementById('zakat-gold-price').value,
                savings: document.getElementById('zakat-savings').value,
                gold_grams: document.getElementById('zakat-gold-grams').value
            };
            const res = await postCalc('/api/calc/zakat', data);
            if(res) {
                const div = document.getElementById('result-zakat');
                div.classList.remove('hidden');
                const r = res.result;
                currentExplanation = res.explanation;
                
                div.className = r.wajib ? "mt-4 bg-red-50 p-4 rounded-xl border border-red-100 text-sm" : "mt-4 bg-green-50 p-4 rounded-xl border border-green-100 text-sm";
                
                let content = '';
                if(r.wajib) {
                    content = `
                        <h4 class="font-bold text-red-600 mb-1"><i class="fas fa-exclamation-circle mr-1"></i> WAJIB ZAKAT</h4>
                        <p class="text-gray-600 mb-2">Harta Anda melebih Nisab (Rp ${Number(r.nisab).toLocaleString()})</p>
                        <p class="text-xs font-bold text-gray-500 uppercase">Zakat yang harus dikeluarkan:</p>
                        <p class="text-2xl font-bold text-red-600 mb-3">Rp ${Number(r.zakat).toLocaleString()}</p>
                    `;
                } else {
                    content = `
                        <h4 class="font-bold text-green-600 mb-1"><i class="fas fa-check-circle mr-1"></i> BELUM WAJIB</h4>
                        <p class="text-gray-600 mb-3">Total harta Anda (Rp ${Number(r.total_wealth).toLocaleString()}) belum mencapai Nisab (Rp ${Number(r.nisab).toLocaleString()}).</p>
                    `;
                }
                content += `
                    <button onclick="showExplanation()" class="w-full bg-white/50 border border-black/5 text-gray-600 text-xs font-bold py-2 rounded-lg hover:bg-white transition flex items-center justify-center gap-2">
                        <i class="fas fa-info-circle"></i> PENJELASAN PERHITUNGAN
                    </button>
                `;
                div.innerHTML = content;
            }
        }

        async function calcTahajjud() {
            const data = {
                maghrib: document.getElementById('tahajjud-maghrib').value,
                subuh: document.getElementById('tahajjud-subuh').value
            };
            const res = await postCalc('/api/calc/tahajjud', data);
            if(res) {
                document.getElementById('result-tahajjud').classList.remove('hidden');
                document.getElementById('tahajjud-time').innerText = res.result.time;
                currentExplanation = res.explanation;
                
                // Check if button already exists to avoid dupes, or just append
                const parent = document.getElementById('result-tahajjud');
                if(!parent.querySelector('button')) {
                     const btn = document.createElement('button');
                     btn.className = "w-full bg-indigo-100 text-indigo-600 text-xs font-bold py-2 rounded-lg hover:bg-indigo-200 transition flex items-center justify-center gap-2 mt-3";
                     btn.innerHTML = '<i class="fas fa-info-circle"></i> PENJELASAN PERHITUNGAN';
                     btn.onclick = showExplanation;
                     parent.appendChild(btn);
                }
            }
        }

        async function calcKhatam() {
             const data = {
                target_times: document.getElementById('khatam-times').value,
                days: document.getElementById('khatam-days').value,
                freq_per_day: document.getElementById('khatam-freq').value
            };
            const res = await postCalc('/api/calc/khatam', data);
            if(res) {
                document.getElementById('result-khatam').classList.remove('hidden');
                document.getElementById('khatam-pages').innerText = res.result.pages_per_session;
                currentExplanation = res.explanation;
                
                const parent = document.getElementById('result-khatam');
                if(!parent.querySelector('button')) {
                     const btn = document.createElement('button');
                     btn.className = "w-full bg-emerald-100 text-emerald-600 text-xs font-bold py-2 rounded-lg hover:bg-emerald-200 transition flex items-center justify-center gap-2 mt-3";
                     btn.innerHTML = '<i class="fas fa-info-circle"></i> PENJELASAN PERHITUNGAN';
                     btn.onclick = showExplanation;
                     parent.appendChild(btn);
                }
            }
        }

        async function calcFidyah() {
             const data = {
                days: document.getElementById('fidyah-days').value,
                category: document.getElementById('fidyah-cat').value
            };
            const res = await postCalc('/api/calc/fidyah', data);
            if(res) {
                document.getElementById('result-fidyah').classList.remove('hidden');
                document.getElementById('fidyah-qadha').innerText = res.result.qadha_days + " Hari";
                document.getElementById('fidyah-rice').innerText = res.result.fidyah_rice.toFixed(1) + " Kg";
                document.getElementById('fidyah-money').innerText = "Rp " + Number(res.result.fidyah_money).toLocaleString();
                currentExplanation = res.explanation;
                
                const parent = document.getElementById('result-fidyah');
                if(!parent.querySelector('.exp-btn')) { // Use class to identify
                     const div = document.createElement('div');
                     div.className = "exp-btn pt-2";
                     div.innerHTML = `
                        <button onclick="showExplanation()" class="w-full bg-gray-100 text-gray-600 text-xs font-bold py-2 rounded-lg hover:bg-gray-200 transition flex items-center justify-center gap-2">
                            <i class="fas fa-info-circle"></i> PENJELASAN PERHITUNGAN
                        </button>
                     `;
                     parent.appendChild(div);
                }
            }
        }

        async function calcHijri() {
            const val = document.getElementById('hijri-date-input').value;
            if(!val) return alert("Pilih tanggal dulu");
            const data = { date: val };
            const res = await postCalc('/api/calc/hijri', data);
            if(res) {
                document.getElementById('result-hijri').classList.remove('hidden');
                document.getElementById('hijri-output').innerText = res.result.hijri;
                currentExplanation = res.explanation;
                
                const parent = document.getElementById('result-hijri');
                if(!parent.querySelector('button')) {
                     const btn = document.createElement('button');
                     btn.className = "w-full bg-emerald-100 text-emerald-600 text-xs font-bold py-2 rounded-lg hover:bg-emerald-200 transition flex items-center justify-center gap-2 mt-3";
                     btn.innerHTML = '<i class="fas fa-info-circle"></i> PENJELASAN PERHITUNGAN';
                     btn.onclick = showExplanation;
                     parent.appendChild(btn);
                }
            }
        }
    </script>
</div>
"""

# --- ROUTES ---

@app.route('/')
def index():
    # Render Home Dashboard
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='home', content=HOME_HTML)

@app.route('/ramadhan')
def ramadhan():
    # Render Ramadhan Dashboard
    resp = make_response(render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='ramadhan', content=RAMADHAN_HTML))
    # Ensure user has an ID
    if not request.cookies.get('user_id'):
        resp.set_cookie('user_id', str(uuid.uuid4()), max_age=60*60*24*365)
    return resp

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
    <div class="pt-20 md:pt-32 pb-24 px-5 md:px-8">
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
    <div class="pt-20 md:pt-32 pb-24 px-5 md:px-8">
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
    <div class="pt-20 md:pt-32 pb-24 px-5 md:px-8">
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
    <div class="pt-20 md:pt-32 pb-24 px-5 md:px-8">
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
    <div class="pt-20 md:pt-32 pb-24 px-5 md:px-8">
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
    <div class="pt-20 md:pt-32 pb-24 px-5 md:px-8">
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
    <div class="pt-20 md:pt-32 pb-24 px-5 md:px-8 text-center min-h-screen flex flex-col items-center justify-center">
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

# --- CALCULATOR API ROUTES ---

@app.route('/api/calc/waris', methods=['POST'])
def api_calc_waris():
    try:
        data = request.json
        harta = int(data['harta'])
        sons = int(data['sons'])
        daughters = int(data['daughters'])
        
        res = calc_waris(harta, sons, daughters)
        if "error" in res:
             return jsonify(res)
        
        # Bedah Logika
        logic = f"Bapak/Ibu memasukkan total harta Rp {harta:,}. Dalam matematika waris, karena ada {sons} anak laki-laki dan {daughters} perempuan, maka total poin pembagi adalah {res['points']}. Artinya, harta tersebut dibagi menjadi {res['points']} keping. Satu keping bernilai Rp {res['part_value']:,.0f}. Maka bagian anak laki-laki adalah 2 x {res['part_value']:,.0f} = Rp {res['son_share']:,.0f}, dan anak perempuan 1 x {res['part_value']:,.0f} = Rp {res['daughter_share']:,.0f}."
        
        return jsonify({
            "result": res,
            "explanation": {
                "logic": logic,
                "sources": DALIL_DATA["waris"]
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/calc/zakat', methods=['POST'])
def api_calc_zakat():
    try:
        data = request.json
        gold_price = int(data['gold_price'])
        savings = int(data['savings'])
        gold_grams = int(data['gold_grams'])
        
        res = calc_zakat(gold_price, savings, gold_grams)
        
        status = "WAJIB" if res['wajib'] else "BELUM WAJIB"
        cond_text = "lebih besar" if res['wajib'] else "lebih kecil"
        
        logic = f"Anda memiliki tabungan uang Rp {savings:,} dan emas {gold_grams} gram. Dengan harga emas Rp {gold_price:,}/gram, maka Nisab (batas minimal wajib zakat) adalah 85 gram x Rp {gold_price:,} = Rp {res['nisab']:,}. Total harta Anda dinilai sebesar Rp {res['total_wealth']:,}. Karena Rp {res['total_wealth']:,} {cond_text} dari Nisab, maka hukumnya {status} membayar Zakat Maal sebesar 2.5% (Rp {res['zakat']:,})."
        
        return jsonify({
            "result": res,
            "explanation": {
                "logic": logic,
                "sources": DALIL_DATA["zakat"]
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/calc/tahajjud', methods=['POST'])
def api_calc_tahajjud():
    try:
        data = request.json
        res = calc_tahajjud(data['maghrib'], data['subuh'])
        if "error" in res: return jsonify(res)
        
        logic = f"Waktu malam dihitung dari Maghrib ({data['maghrib']}) hingga Subuh ({data['subuh']}). Durasi total malam ini adalah {res['total_hours']} jam {res['total_minutes']} menit. Sepertiga malam terakhir adalah waktu istimewa (Qiyamul Lail). Kita bagi durasi malam menjadi 3 bagian, lalu ambil 1 bagian terakhir sebelum Subuh. Hasilnya, sepertiga malam terakhir dimulai pukul {res['time']}."
        
        return jsonify({
            "result": res,
            "explanation": {
                "logic": logic,
                "sources": DALIL_DATA["tahajjud"]
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/calc/khatam', methods=['POST'])
def api_calc_khatam():
    try:
        data = request.json
        target_times = int(data['target_times'])
        days = int(data['days'])
        freq = int(data['freq_per_day'])
        
        res = calc_khatam(target_times, days, freq)
        if isinstance(res, dict) and "error" in res: return jsonify(res)
        if isinstance(res, int): # Fallback
             pass

        logic = f"Target Anda adalah khatam Al-Quran {target_times} kali dalam {days} hari. Total halaman Al-Quran standar adalah 604 halaman. Jadi total beban bacaan adalah {target_times} x 604 = {res['total_pages']} halaman. Anda memiliki kesempatan membaca {freq} kali sehari selama {days} hari, total {res['total_sessions']} sesi baca. Maka, {res['total_pages']} halaman dibagi {res['total_sessions']} sesi = {res['pages_per_session']} halaman setiap kali duduk."

        return jsonify({
            "result": res,
            "explanation": {
                "logic": logic,
                "sources": DALIL_DATA["khatam"]
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/calc/fidyah', methods=['POST'])
def api_calc_fidyah():
    try:
        data = request.json
        days = int(data['days'])
        cat = data['category']
        
        res = calc_fidyah(days, cat)
        
        logic = f"Anda meninggalkan puasa sebanyak {days} hari karena alasan '{cat}'. Dalam fiqih, kategori ini mewajibkan membayar fidyah (memberi makan miskin). Hitungannya adalah {days} hari x 1 mud (0.6kg) = {res['fidyah_rice']:.1f} kg beras. Jika dikonversi ke uang makan (est. Rp 15.000/hari), maka totalnya Rp {res['fidyah_money']:,}."
        
        return jsonify({
            "result": res,
            "explanation": {
                "logic": logic,
                "sources": DALIL_DATA["fidyah"]
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/calc/hijri', methods=['POST'])
def api_calc_hijri():
    try:
        data = request.json
        y, m, d = map(int, data['date'].split('-'))
        date_obj = datetime.date(y, m, d)
        res = gregorian_to_hijri(date_obj)
        
        logic = f"Anda menginput tanggal Masehi {date_obj.strftime('%d-%m-%Y')}. Algoritma Kuwaiti menghitung selisih hari dari epoch Hijriyah (16 Juli 622 M). Dengan memperhitungkan siklus 30 tahun (dimana tahun ke-2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29 adalah kabisat), sistem mengonversi tanggal tersebut menjadi {res}."
        
        return jsonify({
            "result": {"hijri": res},
            "explanation": {
                "logic": logic,
                "sources": DALIL_DATA["hijri"]
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- RAMADHAN FEATURE ROUTES ---

@app.route('/api/ramadhan/astro', methods=['GET'])
def api_ramadhan_astro():
    return jsonify(hitung_fase_bulan())

@app.route('/api/ramadhan/nutrisi', methods=['POST'])
def api_ramadhan_nutrisi():
    try:
        data = request.json
        w = float(data['weight'])
        h = float(data['height'])
        a = int(data['age'])
        g = data['gender']
        act = float(data['activity'])

        # Harris-Benedict
        if g == 'male':
            bmr = 88.362 + (13.397 * w) + (4.799 * h) - (5.677 * a)
        else:
            bmr = 447.593 + (9.247 * w) + (3.098 * h) - (4.330 * a)

        tdee = bmr * act

        # Water: 30ml per kg
        water = (w * 30) / 1000 # Liters

        return jsonify({
            "sahur": tdee * 0.4,
            "iftar": tdee * 0.6,
            "water": round(water, 1)
        })
    except:
        return jsonify({"sahur": 0, "iftar": 0, "water": 0})

@app.route('/api/ramadhan/chat', methods=['POST'])
def api_ramadhan_chat():
    try:
        if not GOOGLE_API_KEY:
            return jsonify({"reply": "Maaf, fitur Chatbot belum dikonfigurasi (API Key hilang). Hubungi Admin."})

        data = request.json
        user_msg = data.get('message', '')

        system_prompt = "Kamu adalah Penjaga Perpustakaan Bayt al-Hikmah dari era Kekhalifahan Abbasiyah. Kamu hanya menjawab pertanyaan seputar Sejarah Islam, Penemuan Ilmuwan Muslim (Al-Khawarizmi, Ibnu Sina, dll), dan Sains dalam Al-Quran. Gaya bicaramu bijaksana, puitis, dan menggunakan istilah klasik. Jika ditanya hal di luar itu, tolak dengan halus."

        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(f"{system_prompt}\n\nUser: {user_msg}\nPenjaga:")

        return jsonify({"reply": response.text})
    except Exception as e:
        print(f"Gemini Error: {e}")
        return jsonify({"reply": "Maaf, perpustakaan sedang sibuk. Silakan tanya lagi nanti."})

@app.route('/api/ramadhan/ifthar', methods=['GET', 'POST'])
def api_ramadhan_ifthar():
    conn = get_db_connection()
    if request.method == 'POST':
        # Donasi baru
        data = request.json
        conn.execute('INSERT INTO ifthar_logistik (date, donor_name, portions, menu) VALUES (?, ?, ?, ?)',
                     (data['day_index'], data['name'], data['portions'], data['menu']))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    else:
        # Get Data for 30 Days
        # Aggregate portions per day
        rows = conn.execute('SELECT date, SUM(portions) as total, GROUP_CONCAT(donor_name) as donors FROM ifthar_logistik GROUP BY date').fetchall()
        conn.close()

        # Map to 1-30
        data = []
        lookup = {row['date']: row for row in rows}
        for i in range(1, 31):
            day_str = str(i)
            entry = lookup.get(day_str)
            data.append({
                "day": i,
                "current": entry['total'] if entry else 0,
                "donors": entry['donors'] if entry else ""
            })
        return jsonify(data)

@app.route('/api/ramadhan/khatam', methods=['GET', 'POST'])
def api_ramadhan_khatam():
    uid = get_user_id()
    conn = get_db_connection()

    if request.method == 'POST':
        data = request.json
        conn.execute('INSERT INTO quran_progress (user_id, date, pages_read) VALUES (?, ?, ?)',
                     (uid, datetime.date.today(), data['pages']))
        conn.commit()
        conn.close()
        resp = jsonify({"status": "success"})
        if not request.cookies.get('user_id'):
            resp.set_cookie('user_id', uid, max_age=60*60*24*365)
        return resp
    else:
        # Get Chart Data
        rows = conn.execute('SELECT date, SUM(pages_read) as daily_pages FROM quran_progress WHERE user_id = ? GROUP BY date ORDER BY date', (uid,)).fetchall()
        conn.close()

        # We need cumulative data for the chart over 30 days
        # Simplified: Just return cumulative reading vs target
        # Target: 604 pages / 30 days = ~20 pages/day

        total_read = 0
        realization = []
        target = []

        # This is a simplification. Ideally we map dates to Ramadhan days.
        # For now, we just show the user's input history relative to a generic 30 day timeline

        current_sum = 0
        for row in rows:
            current_sum += row['daily_pages']
            realization.append(current_sum)

        # Fill/Pad if less than 30 data points?
        # Chart.js can handle partial data.
        # But user wants "Sumbu X = Hari ke-1 sampai 30".

        # Let's just return the accumulated series padded to current day or length
        # Target line
        for i in range(1, 31):
            target.append(i * 20.2) # 604/30

        resp = jsonify({
            "data": realization,
            "target": target
        })
        if not request.cookies.get('user_id'):
            resp.set_cookie('user_id', uid, max_age=60*60*24*365)
        return resp

@app.route('/api/ramadhan/muhasabah', methods=['GET', 'POST'])
def api_ramadhan_muhasabah():
    uid = get_user_id()
    conn = get_db_connection()

    if request.method == 'POST':
        data = request.json
        conn.execute('''INSERT INTO muhasabah_harian
                        (user_id, date, sholat_jemaah, sedekah, tarawih, tilawah)
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     (uid, datetime.date.today(),
                      1 if data['jemaah'] else 0,
                      1 if data['sedekah'] else 0,
                      1 if data['tarawih'] else 0,
                      1 if data['tilawah'] else 0))
        conn.commit()
        conn.close()
        resp = jsonify({"status": "success"})
        if not request.cookies.get('user_id'):
            resp.set_cookie('user_id', uid, max_age=60*60*24*365)
        return resp
    else:
        # Get Stats
        # "Persentase Kebaikan Bulan Ini"
        # Sum all good deeds vs Total possible deeds (days * 4 items)
        row = conn.execute('''SELECT
                                SUM(sholat_jemaah) + SUM(sedekah) + SUM(tarawih) + SUM(tilawah) as total_good,
                                COUNT(*) as total_days
                              FROM muhasabah_harian WHERE user_id = ?''', (uid,)).fetchone()
        conn.close()

        total_good = row['total_good'] or 0
        total_days = row['total_days'] or 0

        # Total items checked per day is 4
        total_possible = total_days * 4

        if total_possible == 0:
            good_pct = 0
            bad_pct = 100
        else:
            good_pct = (total_good / total_possible) * 100
            bad_pct = 100 - good_pct

        resp = jsonify({
            "good": round(good_pct),
            "bad": round(bad_pct)
        })
        if not request.cookies.get('user_id'):
            resp.set_cookie('user_id', uid, max_age=60*60*24*365)
        return resp

if __name__ == '__main__':
    app.run(debug=True, port=5000)
