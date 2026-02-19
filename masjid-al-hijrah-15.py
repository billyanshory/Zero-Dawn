import os
import sqlite3
import datetime
import math
import time
import json
import csv
import urllib.request
from flask import Flask, request, send_from_directory, render_template_string, redirect, url_for, Response, jsonify
from werkzeug.utils import secure_filename

# --- KONFIGURASI FLASK ---
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB Limit
app.secret_key = "9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e"
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
    conn = sqlite3.connect(DB_NAME, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
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

    # 7. Ramadhan Kas Table
    c.execute('''CREATE TABLE IF NOT EXISTS ramadhan_kas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        type TEXT NOT NULL, -- 'Pemasukan' or 'Pengeluaran'
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        amount INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 8. Tarawih Schedule Table
    c.execute('''CREATE TABLE IF NOT EXISTS tarawih_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        night_index INTEGER NOT NULL,
        date TEXT,
        imam TEXT,
        penceramah TEXT,
        judul TEXT
    )''')

    # 9. IRMA Duty Roster
    c.execute('''CREATE TABLE IF NOT EXISTS irma_duty (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        date TEXT NOT NULL
    )''')

    # 10. IRMA Members
    c.execute('''CREATE TABLE IF NOT EXISTS irma_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER,
        hobbies TEXT,
        instagram TEXT,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 11. IRMA Finance
    c.execute('''CREATE TABLE IF NOT EXISTS irma_finance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        type TEXT NOT NULL,
        description TEXT NOT NULL,
        amount INTEGER NOT NULL
    )''')

    # 12. IRMA Wall (Mading)
    c.execute('''CREATE TABLE IF NOT EXISTS irma_wall (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        type TEXT NOT NULL,
        author TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 13. IRMA Events (Proker)
    c.execute('''CREATE TABLE IF NOT EXISTS irma_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        status TEXT NOT NULL,
        date TEXT
    )''')

    # 14. IRMA Curhat (Q&A)
    c.execute('''CREATE TABLE IF NOT EXISTS irma_qa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        answer TEXT,
        asked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        answered_at TIMESTAMP
    )''')

    # 15. IRMA Schedule (Jadwal Piket)
    c.execute('''CREATE TABLE IF NOT EXISTS irma_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        notes TEXT
    )''')

    # 16. IRMA Kas (Kas Remaja)
    c.execute('''CREATE TABLE IF NOT EXISTS irma_kas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        type TEXT NOT NULL,
        amount INTEGER NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 17. IRMA Gallery (Mading)
    c.execute('''CREATE TABLE IF NOT EXISTS irma_gallery (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        creator TEXT NOT NULL,
        content_type TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 18. IRMA Proker (Events)
    c.execute('''CREATE TABLE IF NOT EXISTS irma_proker (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        status TEXT NOT NULL,
        description TEXT,
        date TEXT
    )''')

    # 19. IRMA Curhat (QA)
    c.execute('''CREATE TABLE IF NOT EXISTS irma_curhat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        answer TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        answered_at TIMESTAMP
    )''')

    # Add wa_number to irma_members
    try:
        c.execute('ALTER TABLE irma_members ADD COLUMN wa_number TEXT')
    except sqlite3.OperationalError:
        pass
    
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

# --- RAMADHAN HELPER FUNCTIONS ---

def get_takjil_data():
    csv_file = "jadwal pembagian takjil masjid al-hijrah 2024.xlsx - Sheet1.csv"
    data = []
    try:
        with open(csv_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Ensure we have the needed columns, handle missing keys gracefully
                data.append({
                    'Tanggal': row.get('Tanggal', '-'),
                    'Nama': row.get('Nama', 'Hamba Allah'),
                    'Ket.': row.get('Ket.', '-')
                })
    except FileNotFoundError:
        print("CSV Takjil not found.")
    except Exception as e:
        print(f"Error reading CSV: {e}")
    return data

def get_imsakiyah_schedule():
    schedule = []
    try:
        # 1. Panggil API Aladhan untuk Samarinda, Indonesia
        # 2. Bulan Februari 2026 (Ramadhan 1447 H) & Method 20 (Kemenag RI)
        url = "http://api.aladhan.com/v1/calendarByCity?city=Samarinda&country=Indonesia&method=20&month=2&year=2026"
        
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            
            if 'data' in data:
                today = datetime.date.today()
                
                for day in data['data']:
                    # Parse date
                    date_obj = datetime.datetime.strptime(day['date']['gregorian']['date'], "%d-%m-%Y").date()
                    timings = day['timings']
                    
                    # Format HH:MM (strip seconds/timezone if any)
                    def clean_time(t): return t.split(' ')[0]

                    schedule.append({
                        'date_str': date_obj.strftime('%d/%m'),
                        'imsak': clean_time(timings['Imsak']),
                        'fajr': clean_time(timings['Fajr']),
                        'dhuhr': clean_time(timings['Dhuhr']),
                        'asr': clean_time(timings['Asr']),
                        'maghrib': clean_time(timings['Maghrib']),
                        'isha': clean_time(timings['Isha']),
                        'is_today': (date_obj == today)
                    })
    except Exception as e:
        print(f"Error fetching Imsakiyah API: {e}")
        # Fallback empty or local calculation if needed, but user requested API specifically.
        
    return schedule

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

        /* RAMADHAN MODE UTILS */
        :root {
            --midnight-blue: #0b1026;
            --gold: #FFD700;
            --light-navy: #151e3f;
        }
        .bg-midnight { background-color: var(--midnight-blue); }
        .text-gold { color: var(--gold); }
        .border-gold { border-color: var(--gold); }
        
        /* Floating Card */
        .floating-card {
            margin: 0 0.5rem;
            border-radius: 2.5rem;
            background-color: #0b162c;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.1);
        }

        /* FAB Center Button */
        .fab-center {
            position: absolute;
            bottom: 2rem;
            left: 50%;
            transform: translateX(-50%);
            width: 4.5rem;
            height: 4.5rem;
            background-color: var(--gold);
            border-radius: 9999px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
            border: 4px solid #0b1026; /* Dark Theme Border */
            z-index: 60;
        }
        
        .dark-bottom-nav {
            background-color: #0b1026;
            border-top: 1px solid rgba(255, 215, 0, 0.2);
            border-radius: 20px 20px 0 0;
        }
    </style>
"""

BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#0b1026">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <link rel="manifest" href="/manifest.json">
    <link rel="icon" type="image/png" href="/static/logomasjidalhijrah.png">
    <link rel="apple-touch-icon" href="/static/logomasjidalhijrah.png">
    <title>Masjid Al Hijrah</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    {{ styles|safe }}
</head>
<body class="text-gray-800 antialiased {{ 'ramadhan-mode' if hide_nav else '' }}">
    {% set t_nav_bg = theme.nav_bg if theme and theme.nav_bg else 'glass-nav' %}
    {% set t_icon_bg = theme.icon_bg if theme and theme.icon_bg else 'bg-emerald-100' %}
    {% set t_icon_text = theme.icon_text if theme and theme.icon_text else 'text-emerald-600' %}
    {% set t_title_text = theme.title_text if theme and theme.title_text else 'text-emerald-600' %}
    {% set t_link_hover = theme.link_hover if theme and theme.link_hover else 'hover:text-emerald-600' %}
    {% set t_link_active = theme.link_active if theme and theme.link_active else 'text-emerald-600 font-bold' %}
    {% set t_btn_primary = theme.btn_primary if theme and theme.btn_primary else 'bg-emerald-500 text-white hover:bg-emerald-600' %}
    {% set t_bottom_bg = theme.bottom_nav_bg if theme and theme.bottom_nav_bg else 'glass-bottom' %}
    {% set t_bottom_active = theme.bottom_active if theme and theme.bottom_active else 'text-emerald-600' %}
    {% set t_bottom_btn_bg = theme.bottom_btn_bg if theme and theme.bottom_btn_bg else 'bg-emerald-500' %}
    {% set t_bottom_btn_text = theme.bottom_btn_text if theme and theme.bottom_btn_text else 'text-emerald-600' %}
    {% set t_bottom_text_inactive = theme.bottom_text_inactive if theme and theme.bottom_text_inactive else 'text-gray-400' %}

    <!-- DESKTOP NAVBAR -->
    {% if not hide_nav %}
    <nav class="hidden md:flex fixed top-0 left-0 w-full z-50 {{ t_nav_bg }} shadow-sm px-8 py-4 justify-between items-center right-0">
        <div class="max-w-7xl mx-auto w-full flex justify-between items-center">
             <div class="flex items-center gap-4">
                 <div class="{{ t_icon_bg }} p-2 rounded-xl">
                    <i class="fas fa-mosque {{ t_icon_text }} text-2xl"></i>
                 </div>
                 <div>
                    <h1 class="text-xl font-bold {{ t_title_text }} leading-tight">Masjid Al Hijrah</h1>
                    <p class="text-xs text-gray-500 font-medium">Samarinda, Kalimantan Timur</p>
                 </div>
             </div>
             <div class="flex items-center gap-8">
                <a href="/" class="text-gray-600 font-medium {{ t_link_hover }} transition {{ t_link_active if active_page == 'home' else '' }}">Beranda</a>
                <a href="/finance" class="text-gray-600 font-medium {{ t_link_hover }} transition {{ t_link_active if active_page == 'finance' else '' }}">Laporan Kas</a>
                <a href="/agenda" class="text-gray-600 font-medium {{ t_link_hover }} transition {{ t_link_active if active_page == 'agenda' else '' }}">Jadwal</a>
                <a href="/donate" class="{{ t_btn_primary }} px-5 py-2 rounded-full font-bold shadow-lg transition transform hover:scale-105">Infaq Digital</a>
                <a href="/emergency" class="text-red-500 font-bold hover:text-red-600 transition border border-red-200 px-4 py-2 rounded-full bg-red-50 hover:bg-red-100">Darurat</a>
            </div>
        </div>
    </nav>

    <!-- MOBILE HEADER -->
    <header class="md:hidden fixed top-0 left-0 w-full z-50 {{ t_nav_bg }} shadow-sm px-4 py-3 flex justify-between items-center max-w-md mx-auto right-0">
        <div>
            <p class="text-xs text-gray-500 font-medium">Assalamualaikum</p>
            <h1 class="text-lg font-bold {{ t_title_text }} leading-tight">Masjid Al Hijrah</h1>
        </div>
        <div class="text-right">
            <p class="text-[10px] font-bold {{ t_icon_text }} {{ t_icon_bg }} px-2 py-1 rounded-full border border-emerald-200" id="hijri-date">Loading...</p>
        </div>
    </header>
    {% endif %}

    <!-- CONTENT -->
    <main class="min-h-screen relative w-full max-w-md md:max-w-7xl mx-auto bg-[#F8FAFC]">
        {{ content|safe }}
    </main>

    <!-- MOBILE BOTTOM NAV -->
    {% if not hide_nav %}
    <nav class="md:hidden fixed bottom-0 left-0 w-full {{ t_bottom_bg }} z-50 pb-2 pt-2 max-w-md mx-auto right-0 border-t border-gray-100">
        <div class="flex justify-around items-end h-14 px-2">
            <a href="/" class="flex flex-col items-center justify-center {{ t_bottom_text_inactive }} {{ t_link_hover }} w-16 mb-1 transition-colors {{ t_bottom_active if active_page == 'home' else '' }}">
                <i class="fas fa-home text-xl mb-1"></i>
                <span class="text-[10px] font-medium">Beranda</span>
            </a>
            <a href="/donate" class="flex flex-col items-center justify-center text-gray-400 {{ t_link_hover }} w-16 mb-6 relative z-10">
                <div class="{{ t_bottom_btn_bg }} text-white w-14 h-14 rounded-full flex items-center justify-center shadow-lg border-4 border-white transform hover:scale-105 transition-transform">
                    <i class="fas fa-qrcode text-2xl"></i>
                </div>
                <span class="text-[10px] font-bold mt-1 {{ t_bottom_btn_text }}">Infaq</span>
            </a>
            <a href="/emergency" class="flex flex-col items-center justify-center {{ t_bottom_text_inactive }} hover:text-red-500 w-16 mb-1 transition-colors">
                <i class="fas fa-phone-alt text-xl mb-1"></i>
                <span class="text-[10px] font-medium">Darurat</span>
            </a>
        </div>
    </nav>
    {% endif %}

    <script>
        // PWA SERVICE WORKER
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js').then(reg => {
                    console.log('SW registered!', reg);
                }).catch(err => {
                    console.log('SW failed!', err);
                });
            });
        }

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

        // GLOBAL MODAL UTILS
        function openModal(id) {
            const el = document.getElementById(id);
            if(el) el.classList.remove('hidden');
        }

        function closeModal(id) {
            const el = document.getElementById(id);
            if(el) el.classList.add('hidden');
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

        document.addEventListener('DOMContentLoaded', () => {
            fetchHijri();
            fetchPrayerTimes();
            setInterval(fetchPrayerTimes, 1000);
        });

        // --- PWA INSTALL LOGIC (GLOBAL) ---
        window.deferredPrompt = null;

        window.triggerInstall = async () => {
            if (window.deferredPrompt) {
                window.deferredPrompt.prompt();
                const { outcome } = await window.deferredPrompt.userChoice;
                window.deferredPrompt = null;
                // If accepted, hide prompt
                if(outcome === 'accepted') {
                     document.querySelectorAll('.pwa-btn-container').forEach(el => el.classList.add('hidden'));
                }
            } else {
                // Manual Instructions Logic
                const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
                const isAndroid = /Android/.test(navigator.userAgent);
                
                if (isIOS) {
                    alert("Untuk menginstal di iOS:\\n1. Klik tombol Share (ikon kotak panah atas)\\n2. Cari dan pilih 'Add to Home Screen' / 'Tambah ke Utama' (ikon kotak plus)");
                } else if (isAndroid) {
                    alert("Untuk menginstal:\\n1. Klik ikon tiga titik di pojok kanan atas browser\\n2. Pilih 'Install App' atau 'Tambahkan ke Layar Utama'");
                } else {
                    alert("Untuk menginstal di PC/Laptop:\\nCari ikon 'Install' atau (+) di ujung kanan kolom alamat browser (Address Bar).");
                }
            }
        };

        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            window.deferredPrompt = e;
            // Ensure buttons are visible if not standalone
            const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;
            if (!isStandalone) {
                document.querySelectorAll('.pwa-btn-container').forEach(el => el.classList.remove('hidden'));
            }
        });

        window.addEventListener('load', () => {
            const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;
            if (isStandalone) {
                 // Hide all if installed
                 document.querySelectorAll('.pwa-btn-container').forEach(el => el.classList.add('hidden'));
            } else {
                 // Show all if not installed (Buttons are hidden by default in HTML to prevent FOUC, so we remove hidden here)
                 document.querySelectorAll('.pwa-btn-container').forEach(el => el.classList.remove('hidden'));
                 
                 // Special check for iOS which doesn't fire beforeinstallprompt
                 const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
                 if(isIOS) {
                     // Customize floating banner text for iOS
                     const banner = document.getElementById('pwa-floating-banner');
                     if(banner) {
                        const textDiv = banner.querySelector('.pwa-text');
                        if(textDiv) textDiv.innerHTML = '<h3 class="text-sm font-bold text-[#FFD700] leading-tight">Install di iPhone</h3><p class="text-[10px] text-gray-300">Klik tombol Share <i class="fas fa-share-square"></i> lalu "Add to Home Screen"</p>';
                        const btnDiv = banner.querySelector('.pwa-btn');
                        if(btnDiv) btnDiv.style.display = 'none'; // Manual action only
                     }
                 }
            }
        });
    </script>
    
    <!-- FIXED BOTTOM BANNER (GLOBAL) -->
    <div id="pwa-floating-banner" class="pwa-btn-container hidden fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 z-[9999] bg-[#0b1026]/90 backdrop-blur-md border border-[#FFD700]/30 rounded-2xl shadow-2xl animate-[slideUp_0.3s_ease-out]">
        <div class="flex items-center justify-between p-4">
            <div class="flex items-center gap-3">
                <div class="bg-white/10 p-2 rounded-xl border border-[#FFD700]/20">
                    <img src="/static/logomasjidalhijrah.png" class="w-10 h-10 object-contain">
                </div>
                <div class="pwa-text">
                    <h3 class="text-sm font-bold text-[#FFD700] leading-tight">Pasang Aplikasi</h3>
                    <p class="text-[10px] text-gray-300 font-medium">Akses Cepat & Offline</p>
                </div>
            </div>
            <div class="pwa-btn">
                <button onclick="triggerInstall()" class="bg-[#FFD700] text-[#0b1026] text-xs font-bold px-4 py-2 rounded-full hover:bg-white transition shadow-lg shadow-[#FFD700]/20">
                    INSTALL
                </button>
            </div>
            <button onclick="document.getElementById('pwa-floating-banner').classList.add('hidden')" class="absolute -top-2 -right-2 bg-red-500 text-white w-6 h-6 rounded-full text-xs shadow-md border border-white flex items-center justify-center">&times;</button>
        </div>
    </div>
</body>
</html>
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

        <!-- RIGHT COLUMN: PRAYER CARD & RAMADHAN BANNER -->
        <div class="flex flex-col gap-6">
            
            <!-- PRAYER CARD -->
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

            <!-- RAMADHAN BANNER (MOVED HERE) -->
            <a href="/ramadhan" class="block relative floating-card overflow-hidden group transform hover:scale-[1.02] transition-all duration-300 rounded-3xl shadow-xl border border-[#0b162c]">
                <!-- Background & Texture -->
                <div class="absolute inset-0 bg-[#0b162c]"></div>
                <div class="absolute inset-0 opacity-10" style="background-image: url('https://www.transparenttextures.com/patterns/arabesque.png');"></div>
                
                <!-- Crescent Moon Background -->
                <div class="absolute right-12 top-1/2 transform -translate-y-1/2 opacity-10 text-[#FFD700] pointer-events-none">
                    <i class="fas fa-moon text-9xl"></i>
                </div>
                
                <div class="relative px-6 py-6 md:px-8 md:py-8 flex items-center justify-between">
                    <div>
                        <h2 class="text-2xl md:text-3xl font-bold text-[#FFD700] mb-1 font-sans tracking-wide leading-none">Ramadhan Mode</h2>
                        <p class="text-white/60 text-xs md:text-sm font-medium">Akses Dashboard Khusus Ramadhan</p>
                    </div>
                    
                    <!-- Gold Circle Button -->
                    <div class="w-12 h-12 rounded-full bg-[#FFD700] flex items-center justify-center text-[#0b1026] shadow-[0_0_15px_rgba(255,215,0,0.4)] group-hover:scale-110 transition-transform duration-300 relative z-10">
                        <i class="fas fa-arrow-right text-lg"></i>
                    </div>
                </div>
            </a>

            <!-- IRMA BANNER -->
            <a href="/irma" class="block relative floating-card overflow-hidden group transform hover:scale-[1.02] transition-all duration-300 rounded-3xl shadow-xl border border-[#A0B391] mt-4">
                <div class="absolute inset-0 bg-gradient-to-r from-[#A0B391] to-[#FFB6C1]"></div>
                <div class="absolute inset-0 opacity-10" style="background-image: url('https://www.transparenttextures.com/patterns/arabesque.png');"></div>
                
                <div class="absolute right-12 top-1/2 transform -translate-y-1/2 opacity-20 text-white pointer-events-none">
                    <i class="fas fa-user-friends text-9xl"></i>
                </div>
                
                <div class="relative px-6 py-6 md:px-8 md:py-8 flex items-center justify-between">
                    <div>
                        <h2 class="text-2xl md:text-3xl font-bold text-white mb-1 font-sans tracking-wide leading-none">IRMA Dashboard</h2>
                        <p class="text-white/80 text-xs md:text-sm font-medium">Ruang Kreatif & Kegiatan Remaja</p>
                    </div>
                    
                    <div class="w-12 h-12 rounded-full bg-white flex items-center justify-center text-[#A0B391] shadow-[0_0_15px_rgba(255,255,255,0.4)] group-hover:scale-110 transition-transform duration-300 relative z-10">
                        <i class="fas fa-arrow-right text-lg"></i>
                    </div>
                </div>
            </a>

            <!-- PWA INSTALL BANNER (Moved Here) -->
            <div id="pwa-install-banner" class="pwa-btn-container hidden relative overflow-hidden rounded-3xl shadow-xl border border-[#FFD700] mt-4 group transform hover:scale-[1.02] transition-all duration-300 cursor-pointer" onclick="triggerInstall()">
                <!-- Background -->
                <div class="absolute inset-0 bg-[#0b1026]"></div>
                <div class="absolute inset-0 opacity-10" style="background-image: url('https://www.transparenttextures.com/patterns/arabesque.png');"></div>
                
                <div class="relative px-6 py-5 flex items-center justify-between z-10">
                    <div class="flex items-center gap-4">
                        <div class="bg-white/10 p-3 rounded-full border border-[#FFD700]/30 shadow-inner">
                            <img src="/static/logomasjidalhijrah.png" class="w-8 h-8 object-contain">
                        </div>
                        <div>
                            <h3 class="text-lg font-bold text-[#FFD700] leading-tight">Install Aplikasi</h3>
                            <p class="text-xs text-gray-300 font-medium">Akses Cepat & Offline</p>
                        </div>
                    </div>
                    
                    <button class="bg-[#FFD700] text-[#0b1026] text-xs font-bold px-5 py-2.5 rounded-full hover:bg-white transition shadow-lg shadow-[#FFD700]/20 transform hover:scale-105" onclick="event.stopPropagation(); triggerInstall()">
                        Install
                    </button>
                </div>
            </div>
            
        </div>
    </div>

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

    <!-- STATIC PWA INSTALL BUTTON (NEW) -->
    <div id="pwa-static-btn-container" class="pwa-btn-container mb-12 hidden">
        <button onclick="triggerInstall()" class="w-full bg-gradient-to-r from-emerald-500 to-teal-600 text-white p-4 rounded-3xl shadow-lg border border-emerald-400 flex justify-between items-center group hover:scale-[1.02] transition-all duration-300">
            <div class="flex items-center gap-4">
                <div class="bg-white/20 p-3 rounded-xl text-white shadow-inner">
                    <i class="fas fa-download text-2xl"></i>
                </div>
                <div class="text-left">
                    <h3 class="text-lg font-bold text-white">Install Aplikasi</h3>
                    <p class="text-xs text-emerald-100 font-medium">Akses Cepat Tanpa Buka Browser</p>
                </div>
            </div>
            <div class="bg-white/20 w-10 h-10 rounded-full flex items-center justify-center text-white group-hover:bg-white group-hover:text-emerald-600 transition-all duration-300">
                 <i class="fas fa-arrow-right"></i>
            </div>
        </button>
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
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, max_age=31536000)

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

# --- RAMADHAN SPECIAL FEATURES ---

RAMADHAN_STYLES = """
    <link href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&display=swap" rel="stylesheet">
    <style>
        .ramadhan-bg {
            background-color: #0b1026;
            background-image: radial-gradient(circle at 50% 0%, #1a237e 0%, #0b1026 70%);
            color: #ecf0f1;
            font-family: 'Poppins', sans-serif;
        }
        .text-gold { color: #FFD700; }
        .bg-gold { background-color: #FFD700; }
        .border-gold { border-color: #FFD700; }
        .glass-gold {
            background: rgba(11, 16, 38, 0.8);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 215, 0, 0.15);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }
        .glass-gold:hover {
            border-color: rgba(255, 215, 0, 0.4);
            box-shadow: 0 8px 32px 0 rgba(255, 215, 0, 0.1);
        }
        .amiri-font { font-family: 'Amiri', serif; }
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #0b1026; }
        ::-webkit-scrollbar-thumb { background: #FFD700; border-radius: 4px; }
    </style>
"""

RAMADHAN_DASHBOARD_HTML = """
<div class="bg-midnight min-h-screen pb-24 relative overflow-hidden font-sans">
    <!-- BACKGROUND PATTERN -->
    <div class="fixed inset-0 opacity-5 pointer-events-none" style="background-image: url('https://www.transparenttextures.com/patterns/arabesque.png');"></div>

    <!-- CUSTOM HEADER (Adapted from BASE_LAYOUT) -->
    <nav class="hidden md:flex fixed top-0 left-0 w-full z-50 glass-gold bg-midnight shadow-sm px-8 py-4 justify-between items-center right-0 border-b border-gold/20">
        <div class="max-w-7xl mx-auto w-full flex justify-between items-center">
             <div class="flex items-center gap-4">
                 <div class="bg-white/10 p-2 rounded-xl border border-gold/20">
                    <i class="fas fa-mosque text-gold text-2xl"></i>
                 </div>
                 <div>
                    <h1 class="text-xl font-bold text-gold leading-tight font-sans">Masjid Al Hijrah</h1>
                    <p class="text-xs text-gray-400 font-medium">Samarinda, Kalimantan Timur</p>
                 </div>
             </div>
             <div class="flex items-center gap-8">
                <a href="/" class="text-gray-300 font-medium hover:text-gold transition">Beranda</a>
                <a href="/finance" class="text-gray-300 font-medium hover:text-gold transition">Laporan Kas</a>
                <a href="/agenda" class="text-gray-300 font-medium hover:text-gold transition">Jadwal</a>
                <a href="/donate" class="bg-gold text-midnight px-5 py-2 rounded-full font-bold shadow-lg hover:bg-white transition transform hover:scale-105">Infaq Digital</a>
                <a href="/emergency" class="text-red-400 font-bold hover:text-red-500 transition border border-red-500/50 px-4 py-2 rounded-full bg-red-500/10 hover:bg-red-500/20">Darurat</a>
            </div>
        </div>
    </nav>

    <!-- MOBILE HEADER (Adapted from BASE_LAYOUT) -->
    <header class="md:hidden fixed top-0 left-0 w-full z-50 glass-gold bg-midnight shadow-sm px-4 py-3 flex justify-between items-center max-w-md mx-auto right-0 border-b border-gold/20">
        <div>
            <p class="text-xs text-gray-400 font-medium">Assalamualaikum</p>
            <h1 class="text-lg font-bold text-gold leading-tight font-sans">Masjid Al Hijrah</h1>
        </div>
        <div class="text-right">
            <p class="text-[10px] font-bold text-midnight bg-gold px-2 py-1 rounded-full border border-gold/50" id="hijri-date-ramadhan">Loading...</p>
        </div>
    </header>

    <!-- SPACER -->
    <div class="h-24"></div>

    <div class="px-5 md:px-8 max-w-7xl mx-auto relative z-10">
        
        <!-- PRAYER TIMES CARD -->
        <div class="bg-[#151e3f] rounded-3xl p-6 md:p-8 text-white shadow-2xl border border-white/5 relative overflow-hidden mb-10 group">
            <div class="absolute top-0 right-0 opacity-5 transform translate-x-10 -translate-y-10 transition-transform duration-700 group-hover:scale-110">
                <i class="fas fa-kaaba text-[10rem]"></i>
            </div>
            <div class="relative z-10 flex flex-col md:flex-row justify-between items-center gap-6">
                <div class="text-center md:text-left">
                    <p class="text-gold text-xs font-bold uppercase tracking-widest mb-2">Jadwal Sholat Hari Ini</p>
                    <h2 class="text-5xl font-bold font-mono tracking-tighter text-white drop-shadow-lg" id="ramadhan-clock">--:--</h2>
                    <p class="text-sm text-gray-400 mt-2 flex items-center justify-center md:justify-start gap-2"><i class="fas fa-map-marker-alt text-gold"></i> Samarinda, Kalimantan Timur</p>
                </div>
                
                <div class="grid grid-cols-5 gap-2 md:gap-4 w-full md:w-auto">
                     <!-- Times -->
                     <div class="bg-[#0b1026] p-3 rounded-2xl text-center border border-white/5">
                        <span class="block text-[10px] text-gray-500 uppercase font-bold mb-1">Subuh</span>
                        <span class="font-bold font-mono text-gold" id="r-fajr">--:--</span>
                     </div>
                     <div class="bg-[#0b1026] p-3 rounded-2xl text-center border border-white/5">
                        <span class="block text-[10px] text-gray-500 uppercase font-bold mb-1">Dzuhur</span>
                        <span class="font-bold font-mono text-white" id="r-dhuhr">--:--</span>
                     </div>
                     <div class="bg-[#0b1026] p-3 rounded-2xl text-center border border-white/5">
                        <span class="block text-[10px] text-gray-500 uppercase font-bold mb-1">Ashar</span>
                        <span class="font-bold font-mono text-white" id="r-asr">--:--</span>
                     </div>
                     <div class="bg-gold p-3 rounded-2xl text-center shadow-lg shadow-gold/20 transform scale-110 z-10">
                        <span class="block text-[10px] text-[#0b1026] uppercase font-extrabold mb-1">Maghrib</span>
                        <span class="font-bold font-mono text-[#0b1026]" id="r-maghrib">--:--</span>
                     </div>
                     <div class="bg-[#0b1026] p-3 rounded-2xl text-center border border-white/5">
                        <span class="block text-[10px] text-gray-500 uppercase font-bold mb-1">Isya</span>
                        <span class="font-bold font-mono text-white" id="r-isha">--:--</span>
                     </div>
                </div>
            </div>
        </div>

        <!-- MENU GRID -->
        <h2 class="text-xl font-bold text-white font-sans mb-6 border-l-4 border-gold pl-3">Menu Spesial Ramadhan</h2>
        
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-6 mb-24">
            
            <!-- 1. JADWAL TAKJIL -->
            <button onclick="openModal('modal-takjil')" class="bg-[#151e3f] p-6 rounded-3xl flex flex-col items-center justify-center h-40 group hover:bg-[#1a254d] transition-all border border-white/5 hover:border-gold/30 relative overflow-hidden">
                <div class="absolute inset-0 bg-gold/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="w-14 h-14 rounded-full bg-[#0b1026] flex items-center justify-center text-gold mb-3 group-hover:scale-110 transition-transform shadow-lg border border-white/5">
                    <i class="fas fa-utensils text-2xl"></i>
                </div>
                <span class="font-bold text-sm text-gray-200 group-hover:text-gold transition-colors">Jadwal Takjil</span>
            </button>

            <!-- 2. IMSAKIYAH -->
            <button onclick="openModal('modal-imsakiyah')" class="bg-[#151e3f] p-6 rounded-3xl flex flex-col items-center justify-center h-40 group hover:bg-[#1a254d] transition-all border border-white/5 hover:border-gold/30 relative overflow-hidden">
                <div class="absolute inset-0 bg-gold/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="w-14 h-14 rounded-full bg-[#0b1026] flex items-center justify-center text-blue-400 mb-3 group-hover:scale-110 transition-transform shadow-lg border border-white/5">
                    <i class="fas fa-calendar-alt text-2xl"></i>
                </div>
                <span class="font-bold text-sm text-gray-200 group-hover:text-blue-400 transition-colors">Imsakiyah</span>
            </button>

            <!-- 3. KAS RAMADHAN -->
            <button onclick="openModal('modal-kas-ramadhan')" class="bg-[#151e3f] p-6 rounded-3xl flex flex-col items-center justify-center h-40 group hover:bg-[#1a254d] transition-all border border-white/5 hover:border-gold/30 relative overflow-hidden">
                <div class="absolute inset-0 bg-gold/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="w-14 h-14 rounded-full bg-[#0b1026] flex items-center justify-center text-green-400 mb-3 group-hover:scale-110 transition-transform shadow-lg border border-white/5">
                    <i class="fas fa-wallet text-2xl"></i>
                </div>
                <span class="font-bold text-sm text-gray-200 group-hover:text-green-400 transition-colors">Kas Ramadhan</span>
            </button>

            <!-- 4. JADWAL TARAWIH -->
            <button onclick="openModal('modal-tarawih')" class="bg-[#151e3f] p-6 rounded-3xl flex flex-col items-center justify-center h-40 group hover:bg-[#1a254d] transition-all border border-white/5 hover:border-gold/30 relative overflow-hidden">
                <div class="absolute inset-0 bg-gold/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="w-14 h-14 rounded-full bg-[#0b1026] flex items-center justify-center text-purple-400 mb-3 group-hover:scale-110 transition-transform shadow-lg border border-white/5">
                    <i class="fas fa-microphone-alt text-2xl"></i>
                </div>
                <span class="font-bold text-sm text-center text-gray-200 group-hover:text-purple-400 transition-colors">Imam & Penceramah</span>
            </button>

            <!-- 5. ZAKAT CALCULATOR -->
            <button onclick="openModal('modal-zakat-fitrah')" class="bg-[#151e3f] p-6 rounded-3xl flex flex-col items-center justify-center h-40 group hover:bg-[#1a254d] transition-all border border-white/5 hover:border-gold/30 relative overflow-hidden">
                <div class="absolute inset-0 bg-gold/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="w-14 h-14 rounded-full bg-[#0b1026] flex items-center justify-center text-orange-400 mb-3 group-hover:scale-110 transition-transform shadow-lg border border-white/5">
                    <i class="fas fa-calculator text-2xl"></i>
                </div>
                <span class="font-bold text-sm text-gray-200 group-hover:text-orange-400 transition-colors">Zakat Fitrah</span>
            </button>

            <!-- 6. AMALAN CHECKLIST -->
            <button onclick="openModal('modal-amalan')" class="bg-[#151e3f] p-6 rounded-3xl flex flex-col items-center justify-center h-40 group hover:bg-[#1a254d] transition-all border border-white/5 hover:border-gold/30 relative overflow-hidden">
                <div class="absolute inset-0 bg-gold/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="w-14 h-14 rounded-full bg-[#0b1026] flex items-center justify-center text-pink-400 mb-3 group-hover:scale-110 transition-transform shadow-lg border border-white/5">
                    <i class="fas fa-check-double text-2xl"></i>
                </div>
                <span class="font-bold text-sm text-gray-200 group-hover:text-pink-400 transition-colors">Target Amalan</span>
            </button>
        </div>
    </div>

    <!-- CUSTOM BOTTOM BAR (Adapted from BASE_LAYOUT) -->
    <nav class="md:hidden fixed bottom-0 left-0 w-full bg-midnight z-50 pb-2 pt-2 max-w-md mx-auto right-0 border-t border-gold/20 rounded-t-3xl">
        <div class="flex justify-around items-end h-14 px-2">
            <a href="/" class="flex flex-col items-center justify-center text-gray-400 hover:text-gold w-16 mb-1 transition-colors">
                <i class="fas fa-home text-xl mb-1"></i>
                <span class="text-[10px] font-medium">Beranda</span>
            </a>
            <a href="/donate" class="flex flex-col items-center justify-center text-gray-400 hover:text-gold w-16 mb-6 relative z-10">
                <div class="bg-gold text-midnight w-14 h-14 rounded-full flex items-center justify-center shadow-[0_0_15px_rgba(255,215,0,0.4)] border-4 border-midnight transform hover:scale-105 transition-transform">
                    <i class="fas fa-qrcode text-2xl"></i>
                </div>
                <span class="text-[10px] font-bold mt-1 text-gold">Infaq</span>
            </a>
            <a href="/emergency" class="flex flex-col items-center justify-center text-gray-400 hover:text-red-400 w-16 mb-1 transition-colors">
                <i class="fas fa-phone-alt text-xl mb-1"></i>
                <span class="text-[10px] font-medium">Darurat</span>
            </a>
        </div>
    </nav>

    <!-- MODALS SECTION -->
    
    <!-- 1. MODAL TAKJIL -->
    <div id="modal-takjil" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" onclick="closeModal('modal-takjil')"></div>
        <div class="absolute inset-x-0 bottom-0 md:inset-0 md:flex md:items-center md:justify-center pointer-events-none">
            <div class="bg-[#0b1026] w-full md:w-[600px] h-[80vh] md:h-auto md:max-h-[80vh] rounded-t-3xl md:rounded-3xl shadow-2xl border border-gold/30 flex flex-col pointer-events-auto overflow-hidden animate-[slideUp_0.3s_ease-out]">
                <div class="p-6 border-b border-white/10 flex justify-between items-center bg-white/5">
                    <h3 class="text-xl font-bold text-gold font-sans">Jadwal Pembagian Takjil</h3>
                    <button onclick="closeModal('modal-takjil')" class="text-gray-400 hover:text-white">&times;</button>
                </div>
                <div class="p-4 bg-white/5 border-b border-white/10">
                    <input type="text" id="search-takjil" onkeyup="filterTakjil()" placeholder="Cari Nama Warga..." class="w-full bg-[#0b1026] border border-gold/30 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-gold">
                </div>
                <div class="overflow-y-auto flex-1 p-0">
                    <table class="w-full text-left border-collapse">
                        <thead class="bg-gold/10 text-gold sticky top-0 backdrop-blur-md">
                            <tr>
                                <th class="p-4 text-xs font-bold uppercase">Tanggal</th>
                                <th class="p-4 text-xs font-bold uppercase">Nama Warga</th>
                                <th class="p-4 text-xs font-bold uppercase text-right">RT / Ket</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-white/5" id="takjil-list">
                            {% for row in takjil_data %}
                            <tr class="hover:bg-white/5 transition">
                                <td class="p-4 text-sm text-gray-300">{{ row['Tanggal'] }}</td>
                                <td class="p-4 font-bold text-white name-cell">{{ row['Nama'] }}</td>
                                <td class="p-4 text-sm text-gray-400 text-right">{{ row['Ket.'] }}</td>
                            </tr>
                            {% else %}
                            <tr><td colspan="3" class="p-6 text-center text-gray-500">Data tidak tersedia atau file CSV belum diupload.</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- 2. MODAL IMSAKIYAH -->
    <div id="modal-imsakiyah" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" onclick="closeModal('modal-imsakiyah')"></div>
        <div class="absolute inset-x-0 bottom-0 md:inset-0 md:flex md:items-center md:justify-center pointer-events-none">
            <div class="bg-[#0b1026] w-full md:w-[800px] h-[85vh] md:h-auto md:max-h-[85vh] rounded-t-3xl md:rounded-3xl shadow-2xl border border-gold/30 flex flex-col pointer-events-auto overflow-hidden animate-[slideUp_0.3s_ease-out]">
                <div class="p-6 border-b border-white/10 flex justify-between items-center bg-white/5">
                    <div>
                         <h3 class="text-xl font-bold text-gold font-sans">Jadwal Imsakiyah</h3>
                         <p class="text-[10px] text-gray-400">Samarinda & Sekitarnya • Ramadhan 1447 H / 2026 M</p>
                    </div>
                    <button onclick="closeModal('modal-imsakiyah')" class="text-gray-400 hover:text-white">&times;</button>
                </div>
                <div class="overflow-auto flex-1 p-0">
                    <table class="w-full text-center border-collapse">
                        <thead class="bg-blue-900/50 text-blue-200 sticky top-0 backdrop-blur-md z-10">
                            <tr>
                                <th class="p-3 text-xs font-bold border-b border-white/10">Tgl</th>
                                <th class="p-3 text-xs font-bold border-b border-white/10 text-gold">Imsak</th>
                                <th class="p-3 text-xs font-bold border-b border-white/10">Subuh</th>
                                <th class="p-3 text-xs font-bold border-b border-white/10 hidden md:table-cell">Dzuhur</th>
                                <th class="p-3 text-xs font-bold border-b border-white/10 hidden md:table-cell">Ashar</th>
                                <th class="p-3 text-xs font-bold border-b border-white/10 text-gold">Maghrib</th>
                                <th class="p-3 text-xs font-bold border-b border-white/10 hidden md:table-cell">Isya</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-white/5">
                            {% for day in imsakiyah_data %}
                            <tr class="hover:bg-white/5 transition {{ 'bg-gold/10 border-l-4 border-gold' if day.is_today else '' }}">
                                <td class="p-3 text-xs text-gray-300">{{ day.date_str }}</td>
                                <td class="p-3 text-sm font-bold text-gold font-mono">{{ day.imsak }}</td>
                                <td class="p-3 text-sm text-gray-300 font-mono">{{ day.fajr }}</td>
                                <td class="p-3 text-sm text-gray-400 font-mono hidden md:table-cell">{{ day.dhuhr }}</td>
                                <td class="p-3 text-sm text-gray-400 font-mono hidden md:table-cell">{{ day.asr }}</td>
                                <td class="p-3 text-sm font-bold text-gold font-mono bg-gold/5">{{ day.maghrib }}</td>
                                <td class="p-3 text-sm text-gray-400 font-mono hidden md:table-cell">{{ day.isha }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- 3. MODAL KAS RAMADHAN -->
    <div id="modal-kas-ramadhan" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" onclick="closeModal('modal-kas-ramadhan')"></div>
        <div class="absolute inset-x-0 bottom-0 md:inset-0 md:flex md:items-center md:justify-center pointer-events-none">
            <div class="bg-[#0b1026] w-full md:w-[600px] h-[80vh] md:h-auto md:max-h-[80vh] rounded-t-3xl md:rounded-3xl shadow-2xl border border-gold/30 flex flex-col pointer-events-auto overflow-hidden animate-[slideUp_0.3s_ease-out]">
                <div class="p-6 border-b border-white/10 flex justify-between items-center bg-white/5">
                    <h3 class="text-xl font-bold text-gold font-sans">Laporan Kas Ramadhan</h3>
                    <button onclick="closeModal('modal-kas-ramadhan')" class="text-gray-400 hover:text-white">&times;</button>
                </div>
                
                <!-- Summary -->
                <div class="p-6 grid grid-cols-2 gap-4 border-b border-white/10">
                    <div class="bg-green-500/10 p-4 rounded-2xl border border-green-500/20 text-center">
                        <p class="text-xs text-green-400 uppercase font-bold">Pemasukan</p>
                        <p class="text-lg font-bold text-green-400">Rp {{ "{:,.0f}".format(ramadhan_kas_summary.income) }}</p>
                    </div>
                    <div class="bg-red-500/10 p-4 rounded-2xl border border-red-500/20 text-center">
                        <p class="text-xs text-red-400 uppercase font-bold">Pengeluaran</p>
                        <p class="text-lg font-bold text-red-400">Rp {{ "{:,.0f}".format(ramadhan_kas_summary.out) }}</p>
                    </div>
                    <div class="col-span-2 bg-gold/10 p-4 rounded-2xl border border-gold/30 text-center">
                        <p class="text-xs text-gold uppercase font-bold">Saldo Akhir</p>
                        <p class="text-2xl font-bold text-white">Rp {{ "{:,.0f}".format(ramadhan_kas_summary.balance) }}</p>
                    </div>
                </div>

                <!-- Input Form -->
                <div class="p-6 bg-white/5 border-b border-white/10">
                    <h4 class="text-sm font-bold text-gray-300 mb-3">Input Transaksi (Admin)</h4>
                    <form action="/ramadhan/kas" method="POST" class="space-y-3">
                        <div class="grid grid-cols-2 gap-3">
                            <input type="date" name="date" required class="bg-[#0b1026] border border-gray-600 rounded-lg p-2 text-sm text-white focus:border-gold">
                            <select name="type" class="bg-[#0b1026] border border-gray-600 rounded-lg p-2 text-sm text-white focus:border-gold">
                                <option value="Pemasukan">Pemasukan</option>
                                <option value="Pengeluaran">Pengeluaran</option>
                            </select>
                        </div>
                        <div class="grid grid-cols-2 gap-3">
                             <input type="text" name="description" placeholder="Keterangan (ex: Infaq Tarawih Malam 1)" required class="bg-[#0b1026] border border-gray-600 rounded-lg p-2 text-sm text-white focus:border-gold">
                             <input type="number" name="amount" placeholder="Nominal (Rp)" required class="bg-[#0b1026] border border-gray-600 rounded-lg p-2 text-sm text-white focus:border-gold">
                        </div>
                        <input type="hidden" name="category" value="Ramadhan"> <!-- Default Category -->
                        <button type="submit" class="w-full bg-gold text-[#0b1026] font-bold py-2 rounded-lg hover:bg-white transition">Simpan Data</button>
                    </form>
                </div>

                <!-- List -->
                <div class="overflow-y-auto flex-1 p-0">
                    <table class="w-full text-left">
                        <tbody class="divide-y divide-white/5">
                            {% for item in ramadhan_kas_items %}
                            <tr class="hover:bg-white/5">
                                <td class="p-4">
                                    <div class="flex items-center justify-between">
                                        <div>
                                            <p class="text-sm font-bold text-white">{{ item['description'] }}</p>
                                            <p class="text-[10px] text-gray-400">{{ item['date'] }}</p>
                                        </div>
                                        <span class="font-mono font-bold {{ 'text-green-400' if item['type'] == 'Pemasukan' else 'text-red-400' }}">
                                            {{ "+" if item['type'] == 'Pemasukan' else "-" }} {{ "{:,.0f}".format(item['amount']) }}
                                        </span>
                                    </div>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- 4. MODAL JADWAL TARAWIH -->
    <div id="modal-tarawih" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" onclick="closeModal('modal-tarawih')"></div>
        <div class="absolute inset-x-0 bottom-0 md:inset-0 md:flex md:items-center md:justify-center pointer-events-none">
            <div class="bg-[#0b1026] w-full md:w-[700px] h-[80vh] md:h-auto md:max-h-[80vh] rounded-t-3xl md:rounded-3xl shadow-2xl border border-gold/30 flex flex-col pointer-events-auto overflow-hidden animate-[slideUp_0.3s_ease-out]">
                <div class="p-6 border-b border-white/10 flex justify-between items-center bg-white/5">
                    <h3 class="text-xl font-bold text-gold font-sans">Jadwal Imam & Penceramah</h3>
                    <button onclick="closeModal('modal-tarawih')" class="text-gray-400 hover:text-white">&times;</button>
                </div>
                
                <!-- Editor (Hidden by default, toggleable) -->
                <div id="tarawih-editor" class="hidden p-4 bg-white/5 border-b border-white/10">
                    <form action="/ramadhan/tarawih" method="POST" class="space-y-3">
                         <div class="grid grid-cols-4 gap-2">
                             <input type="number" name="night_index" placeholder="Malam ke" required class="bg-[#0b1026] border border-gray-600 rounded-lg p-2 text-sm text-white">
                             <input type="text" name="imam" placeholder="Nama Imam" required class="bg-[#0b1026] border border-gray-600 rounded-lg p-2 text-sm text-white">
                             <input type="text" name="penceramah" placeholder="Nama Penceramah" required class="bg-[#0b1026] border border-gray-600 rounded-lg p-2 text-sm text-white">
                             <input type="text" name="judul" placeholder="Judul Ceramah" class="bg-[#0b1026] border border-gray-600 rounded-lg p-2 text-sm text-white">
                         </div>
                         <button type="submit" class="w-full bg-purple-600 text-white font-bold py-2 rounded-lg hover:bg-purple-500">Update Jadwal</button>
                    </form>
                </div>
                <div class="p-2 text-center border-b border-white/10">
                    <button onclick="document.getElementById('tarawih-editor').classList.toggle('hidden')" class="text-xs text-purple-400 hover:text-purple-300 font-bold uppercase tracking-wider">+ Edit Jadwal (Admin)</button>
                </div>

                <div class="overflow-y-auto flex-1 p-0">
                    <div class="grid grid-cols-1 divide-y divide-white/5">
                        {% for item in tarawih_schedule %}
                        <div class="p-4 hover:bg-white/5 transition flex gap-4 items-center">
                            <div class="bg-purple-500/20 text-purple-400 w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg flex-shrink-0">
                                {{ item['night_index'] }}
                            </div>
                            <div class="flex-1">
                                <div class="flex justify-between items-start">
                                    <div>
                                        <p class="text-xs text-gray-400 uppercase">Imam</p>
                                        <p class="font-bold text-white mb-1">{{ item['imam'] }}</p>
                                    </div>
                                    <div class="text-right">
                                        <p class="text-xs text-gray-400 uppercase">Penceramah</p>
                                        <p class="font-bold text-gold mb-1">{{ item['penceramah'] }}</p>
                                    </div>
                                </div>
                                <p class="text-xs text-gray-500 italic mt-1">"{{ item['judul'] }}"</p>
                            </div>
                        </div>
                        {% else %}
                        <div class="p-8 text-center text-gray-500">Jadwal belum diisi.</div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- 5. MODAL ZAKAT FITRAH -->
    <div id="modal-zakat-fitrah" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" onclick="closeModal('modal-zakat-fitrah')"></div>
        <div class="absolute inset-x-0 bottom-0 md:inset-0 md:flex md:items-center md:justify-center pointer-events-none">
            <div class="bg-[#0b1026] w-full md:w-[400px] h-auto rounded-t-3xl md:rounded-3xl shadow-2xl border border-gold/30 flex flex-col pointer-events-auto overflow-hidden animate-[slideUp_0.3s_ease-out]">
                <div class="p-6 border-b border-white/10 flex justify-between items-center bg-white/5">
                    <h3 class="text-xl font-bold text-gold font-sans">Kalkulator Zakat Fitrah</h3>
                    <button onclick="closeModal('modal-zakat-fitrah')" class="text-gray-400 hover:text-white">&times;</button>
                </div>
                <div class="p-6 space-y-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-400 mb-2">Jumlah Jiwa (Orang)</label>
                        <input type="number" id="zakat-jiwa" value="1" min="1" class="w-full bg-[#0b1026] border border-gold/30 rounded-xl p-4 text-white text-center text-xl font-bold focus:border-gold">
                    </div>
                    
                    <div class="bg-white/5 p-4 rounded-xl border border-white/10">
                        <p class="text-xs text-gray-400 mb-2 uppercase font-bold text-center">Estimasi Pembayaran</p>
                        <div class="flex justify-between items-center mb-2">
                            <span class="text-gray-300">Beras (2.5 Kg)</span>
                            <span class="font-bold text-white text-lg" id="res-beras">2.5 Kg</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-300">Uang (Rp 45.000)</span>
                            <span class="font-bold text-gold text-lg" id="res-uang">Rp 45.000</span>
                        </div>
                    </div>
                    
                    <button onclick="calculateZakatFitrah()" class="w-full bg-gold text-[#0b1026] font-bold py-3 rounded-xl hover:bg-white transition">Hitung Ulang</button>
                    <p class="text-[10px] text-gray-500 text-center italic">*Harga uang menyesuaikan standar Samarinda (Rp 45.000/jiwa)</p>
                </div>
            </div>
        </div>
    </div>

    <!-- 6. MODAL AMALAN -->
    <div id="modal-amalan" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" onclick="closeModal('modal-amalan')"></div>
        <div class="absolute inset-x-0 bottom-0 md:inset-0 md:flex md:items-center md:justify-center pointer-events-none">
            <div class="bg-[#0b1026] w-full md:w-[400px] h-[80vh] md:h-auto rounded-t-3xl md:rounded-3xl shadow-2xl border border-gold/30 flex flex-col pointer-events-auto overflow-hidden animate-[slideUp_0.3s_ease-out] relative">
                <!-- Canvas for fireworks -->
                <canvas id="fireworks" class="absolute inset-0 pointer-events-none z-50"></canvas>
                
                <div class="p-6 border-b border-white/10 flex justify-between items-center bg-white/5 relative z-10">
                    <h3 class="text-xl font-bold text-pink-400 font-sans">Checklist Amalan Harian</h3>
                    <button onclick="closeModal('modal-amalan')" class="text-gray-400 hover:text-white">&times;</button>
                </div>
                
                <div class="p-6 flex-1 overflow-y-auto relative z-10">
                    <div class="mb-6">
                         <div class="flex justify-between text-xs text-gray-400 mb-1">
                             <span>Progress Harian</span>
                             <span id="progress-text">0%</span>
                         </div>
                         <div class="w-full bg-white/10 rounded-full h-2.5">
                              <div id="progress-bar" class="bg-pink-500 h-2.5 rounded-full transition-all duration-500" style="width: 0%"></div>
                         </div>
                    </div>

                    <div class="space-y-3" id="amalan-list">
                        <!-- Checkboxes generated by JS -->
                        <label class="flex items-center gap-3 p-3 bg-white/5 rounded-xl border border-white/10 cursor-pointer hover:bg-white/10 transition">
                            <input type="checkbox" onchange="updateProgress()" class="w-5 h-5 accent-pink-500 rounded text-pink-500 focus:ring-pink-500 bg-gray-700 border-gray-600">
                            <span class="text-gray-200 font-medium">Puasa Hari Ini</span>
                        </label>
                        <label class="flex items-center gap-3 p-3 bg-white/5 rounded-xl border border-white/10 cursor-pointer hover:bg-white/10 transition">
                            <input type="checkbox" onchange="updateProgress()" class="w-5 h-5 accent-pink-500 rounded text-pink-500 focus:ring-pink-500 bg-gray-700 border-gray-600">
                            <span class="text-gray-200 font-medium">Sholat 5 Waktu</span>
                        </label>
                        <label class="flex items-center gap-3 p-3 bg-white/5 rounded-xl border border-white/10 cursor-pointer hover:bg-white/10 transition">
                            <input type="checkbox" onchange="updateProgress()" class="w-5 h-5 accent-pink-500 rounded text-pink-500 focus:ring-pink-500 bg-gray-700 border-gray-600">
                            <span class="text-gray-200 font-medium">Sholat Tarawih</span>
                        </label>
                        <label class="flex items-center gap-3 p-3 bg-white/5 rounded-xl border border-white/10 cursor-pointer hover:bg-white/10 transition">
                            <input type="checkbox" onchange="updateProgress()" class="w-5 h-5 accent-pink-500 rounded text-pink-500 focus:ring-pink-500 bg-gray-700 border-gray-600">
                            <span class="text-gray-200 font-medium">Tilawah 1 Juz</span>
                        </label>
                        <label class="flex items-center gap-3 p-3 bg-white/5 rounded-xl border border-white/10 cursor-pointer hover:bg-white/10 transition">
                            <input type="checkbox" onchange="updateProgress()" class="w-5 h-5 accent-pink-500 rounded text-pink-500 focus:ring-pink-500 bg-gray-700 border-gray-600">
                            <span class="text-gray-200 font-medium">Sedekah Subuh</span>
                        </label>
                    </div>
                    
                    <button onclick="resetAmalan()" class="mt-6 w-full text-xs text-gray-500 hover:text-white underline">Reset Checklist Hari Ini</button>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    // --- RAMADHAN JS UTILS ---
    
    // CLOCK
    function updateRamadhanClock() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('id-ID', {hour12: false});
        if(document.getElementById('ramadhan-clock')) {
            document.getElementById('ramadhan-clock').innerText = timeStr;
        }
    }
    setInterval(updateRamadhanClock, 1000);
    updateRamadhanClock();
    
    // HIJRI DATE RAMADHAN (REUSE fetchHijri but target different ID)
    async function fetchHijriRamadhan() {
        try {
            const today = new Date();
            const dd = String(today.getDate()).padStart(2, '0');
            const mm = String(today.getMonth() + 1).padStart(2, '0');
            const yyyy = today.getFullYear();
            const dateStr = dd + '-' + mm + '-' + yyyy;
            
            const response = await fetch('https://api.aladhan.com/v1/gToH?date=' + dateStr);
            const data = await response.json();
            const h = data.data.hijri;
            if(document.getElementById('hijri-date-ramadhan')) {
                document.getElementById('hijri-date-ramadhan').innerText = `${h.day} ${h.month.en} ${h.year}H`;
            }
        } catch(e) { console.error(e); }
    }
    fetchHijriRamadhan();

    // PRAYER TIMES FOR HEADER (FETCH SAME AS HOME BUT DISPLAY HERE)
    async function fetchRamadhanPrayer() {
         try {
            // Using Aladhan for Samarinda (Current)
            const response = await fetch('https://api.aladhan.com/v1/timingsByCity?city=Samarinda&country=Indonesia');
            const result = await response.json();
            const timings = result.data.timings;
            
            if(document.getElementById('r-fajr')) {
                document.getElementById('r-fajr').innerText = timings.Fajr;
                document.getElementById('r-dhuhr').innerText = timings.Dhuhr;
                document.getElementById('r-asr').innerText = timings.Asr;
                document.getElementById('r-maghrib').innerText = timings.Maghrib;
                document.getElementById('r-isha').innerText = timings.Isha;
            }
        } catch(e) { console.error(e); }
    }
    fetchRamadhanPrayer();

    // MODAL UTILS
    function openModal(id) {
        document.getElementById(id).classList.remove('hidden');
    }
    function closeModal(id) {
        document.getElementById(id).classList.add('hidden');
    }
    
    // TAKJIL FILTER
    function filterTakjil() {
        const input = document.getElementById('search-takjil');
        const filter = input.value.toUpperCase();
        const tbody = document.getElementById('takjil-list');
        const tr = tbody.getElementsByTagName('tr');

        for (let i = 0; i < tr.length; i++) {
            const td = tr[i].getElementsByTagName("td")[1]; // Nama Column
            if (td) {
                const txtValue = td.textContent || td.innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {
                    tr[i].style.display = "";
                } else {
                    tr[i].style.display = "none";
                }
            }
        }
    }

    // ZAKAT CALCULATOR
    function calculateZakatFitrah() {
        const jiwa = document.getElementById('zakat-jiwa').value;
        const beras = jiwa * 2.5;
        const uang = jiwa * 45000;
        
        document.getElementById('res-beras').innerText = beras.toFixed(1) + " Kg";
        document.getElementById('res-uang').innerText = "Rp " + Number(uang).toLocaleString('id-ID');
    }

    // AMALAN CHECKLIST
    function updateProgress() {
        const checks = document.querySelectorAll('#amalan-list input[type="checkbox"]');
        let checkedCount = 0;
        checks.forEach(c => {
            if(c.checked) checkedCount++;
            // Save state
            localStorage.setItem('amalan_' + Array.from(checks).indexOf(c), c.checked);
        });
        
        const pct = Math.round((checkedCount / checks.length) * 100);
        document.getElementById('progress-bar').style.width = pct + "%";
        document.getElementById('progress-text').innerText = pct + "%";
        
        if(pct === 100) {
            triggerFireworks();
        }
    }
    
    function loadAmalan() {
        const checks = document.querySelectorAll('#amalan-list input[type="checkbox"]');
        checks.forEach((c, index) => {
            const saved = localStorage.getItem('amalan_' + index);
            if(saved === 'true') c.checked = true;
        });
        updateProgress();
    }
    
    function resetAmalan() {
        const checks = document.querySelectorAll('#amalan-list input[type="checkbox"]');
        checks.forEach((c, index) => {
             c.checked = false;
             localStorage.removeItem('amalan_' + index);
        });
        updateProgress();
    }

    // Init Amalan
    loadAmalan();

    // FIREWORKS
    function triggerFireworks() {
         // Simple particle explosion
         const canvas = document.getElementById('fireworks');
         const ctx = canvas.getContext('2d');
         canvas.width = canvas.parentElement.clientWidth;
         canvas.height = canvas.parentElement.clientHeight;
         
         let particles = [];
         for(let i=0; i<50; i++) {
             particles.push({
                 x: canvas.width/2,
                 y: canvas.height/2,
                 vx: (Math.random() - 0.5) * 10,
                 vy: (Math.random() - 0.5) * 10,
                 color: `hsl(${Math.random()*360}, 100%, 50%)`,
                 life: 1.0
             });
         }
         
         function animate() {
             ctx.clearRect(0,0,canvas.width,canvas.height);
             particles.forEach((p, index) => {
                 p.x += p.vx;
                 p.y += p.vy;
                 p.life -= 0.02;
                 p.vy += 0.1; // gravity
                 
                 ctx.fillStyle = p.color;
                 ctx.globalAlpha = p.life;
                 ctx.beginPath();
                 ctx.arc(p.x, p.y, 4, 0, Math.PI*2);
                 ctx.fill();
                 
                 if(p.life <= 0) particles.splice(index, 1);
             });
             
             if(particles.length > 0) requestAnimationFrame(animate);
             else ctx.clearRect(0,0,canvas.width,canvas.height);
         }
         animate();
    }
</script>
"""

# --- IRMA DASHBOARD ASSETS ---

IRMA_STYLES = """
    <style>
        .bg-sage { background-color: #A0B391; }
        .text-sage { color: #A0B391; }
        .border-sage { border-color: #A0B391; }
        
        .bg-pastel-pink { background-color: #FFB6C1; }
        .text-pastel-pink { color: #FFB6C1; }
        .border-pastel-pink { border-color: #FFB6C1; }
        
        .bg-off-white { background-color: #F4E7E1; }
        
        .text-dark-grey { color: #4A4A4A; }
        .text-forest { color: #2F4F4F; } /* Dark Forest Green for contrast */
        
        .irma-header {
            background: linear-gradient(135deg, #A0B391 0%, #8DA57B 100%);
        }
        
        .irma-card {
            background-color: white;
            border-radius: 1.5rem;
            box-shadow: 0 10px 15px -3px rgba(160, 179, 145, 0.2);
            transition: all 0.3s ease;
            border: 1px solid rgba(160, 179, 145, 0.2);
        }
        .irma-card:hover {
            transform: scale(1.02);
            box-shadow: 0 20px 25px -5px rgba(160, 179, 145, 0.3);
            border-color: #FFB6C1;
        }
        
        .btn-irma-primary {
            background-color: #A0B391;
            color: white;
            border-radius: 0.75rem;
            font-weight: bold;
            transition: all 0.3s;
        }
        .btn-irma-primary:hover {
            background-color: #FFB6C1;
            transform: translateY(-2px);
        }

        /* Fade In Animation */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
            animation: fadeIn 0.5s ease-out forwards;
        }
    </style>
"""

IRMA_DASHBOARD_HTML = """
<div class="pt-24 pb-32 px-5 md:px-8 bg-[#F4E7E1] min-h-screen">
    
    <!-- PRAYER CARD (Standard Logic, Sage Theme) -->
    <div class="bg-gradient-to-br from-[#A0B391] to-[#8DA57B] rounded-3xl p-6 md:p-10 text-white shadow-xl relative overflow-hidden transform md:hover:scale-[1.02] transition-transform duration-500 mb-8 border border-white/20">
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
                <div><div class="font-semibold mb-1">Subuh</div><div id="fajr-time" class="font-mono">--:--</div></div>
                <div><div class="font-semibold mb-1">Dzuhur</div><div id="dhuhr-time" class="font-mono">--:--</div></div>
                <div><div class="font-semibold mb-1">Ashar</div><div id="asr-time" class="font-mono">--:--</div></div>
                <div><div class="font-semibold mb-1">Maghrib</div><div id="maghrib-time" class="font-mono">--:--</div></div>
                <div><div class="font-semibold mb-1">Isya</div><div id="isha-time" class="font-mono">--:--</div></div>
            </div>
        </div>
    </div>

    <!-- MENU GRID -->
    <h3 class="text-[#2F4F4F] font-bold text-lg mb-4 pl-3 border-l-4 border-[#FFB6C1]">Menu Utama</h3>
    <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-24">
        
        <!-- 1. JADWAL PIKET -->
        <button onclick="openModal('modal-duty')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#A0B391]/20 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
             <div class="w-14 h-14 rounded-full bg-[#A0B391]/10 flex items-center justify-center text-[#A0B391] mb-3 group-hover:bg-[#FFB6C1] group-hover:text-white transition-colors">
                <i class="fas fa-clipboard-list text-2xl"></i>
             </div>
             <span class="font-bold text-sm text-gray-600 group-hover:text-[#A0B391]">Jadwal Piket</span>
        </button>

        <!-- 2. JOIN IRMA -->
        <button onclick="openModal('modal-join')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#A0B391]/20 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
             <div class="w-14 h-14 rounded-full bg-[#A0B391]/10 flex items-center justify-center text-[#A0B391] mb-3 group-hover:bg-[#FFB6C1] group-hover:text-white transition-colors">
                <i class="fas fa-user-plus text-2xl"></i>
             </div>
             <span class="font-bold text-sm text-gray-600 group-hover:text-[#A0B391]">Join IRMA</span>
        </button>

        <!-- 3. KAS REMAJA -->
        <button onclick="openModal('modal-finance')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#A0B391]/20 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
             <div class="w-14 h-14 rounded-full bg-[#A0B391]/10 flex items-center justify-center text-[#A0B391] mb-3 group-hover:bg-[#FFB6C1] group-hover:text-white transition-colors">
                <i class="fas fa-piggy-bank text-2xl"></i>
             </div>
             <span class="font-bold text-sm text-gray-600 group-hover:text-[#A0B391]">Kas Remaja</span>
        </button>

        <!-- 4. MADING KREATIF -->
        <button onclick="openModal('modal-wall')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#A0B391]/20 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
             <div class="w-14 h-14 rounded-full bg-[#A0B391]/10 flex items-center justify-center text-[#A0B391] mb-3 group-hover:bg-[#FFB6C1] group-hover:text-white transition-colors">
                <i class="fas fa-palette text-2xl"></i>
             </div>
             <span class="font-bold text-sm text-gray-600 group-hover:text-[#A0B391]">Mading Kreatif</span>
        </button>

        <!-- 5. PROKER EVENT -->
        <button onclick="openModal('modal-events')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#A0B391]/20 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
             <div class="w-14 h-14 rounded-full bg-[#A0B391]/10 flex items-center justify-center text-[#A0B391] mb-3 group-hover:bg-[#FFB6C1] group-hover:text-white transition-colors">
                <i class="fas fa-tasks text-2xl"></i>
             </div>
             <span class="font-bold text-sm text-gray-600 group-hover:text-[#A0B391]">Proker Event</span>
        </button>

        <!-- 6. CURHAT ISLAMI -->
        <button onclick="openModal('modal-qa')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#A0B391]/20 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
             <div class="w-14 h-14 rounded-full bg-[#A0B391]/10 flex items-center justify-center text-[#A0B391] mb-3 group-hover:bg-[#FFB6C1] group-hover:text-white transition-colors">
                <i class="fas fa-comments text-2xl"></i>
             </div>
             <span class="font-bold text-sm text-gray-600 group-hover:text-[#A0B391]">Curhat Islami</span>
        </button>
    </div>

    <!-- MODALS SECTION -->
    
    <!-- 1. MODAL DUTY -->
    <div id="modal-duty" class="hidden fixed inset-0 z-40 bg-[#F4E7E1] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-[#A0B391]/20 pb-4">
                <h3 class="text-xl font-bold text-[#2F4F4F]">Jadwal Piket</h3>
                <button onclick="closeModal('modal-duty')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
            </div>
            
            <form action="/irma/schedule" method="POST" class="mb-6 bg-white p-4 rounded-2xl shadow-sm border border-[#A0B391]/20">
                <h4 class="text-xs font-bold text-[#A0B391] uppercase mb-3">Input Petugas</h4>
                <div class="grid grid-cols-2 gap-3 mb-3">
                    <input type="text" name="name" placeholder="Nama" required class="w-full bg-[#F4E7E1] border-none rounded-xl p-3 text-sm">
                    <select name="role" class="w-full bg-[#F4E7E1] border-none rounded-xl p-3 text-sm">
                        <option value="MC">MC</option>
                        <option value="Adzan">Muadzin</option>
                        <option value="Bersih-bersih">Bersih-bersih</option>
                        <option value="Konsumsi">Konsumsi</option>
                    </select>
                </div>
                <input type="date" name="date" required class="w-full bg-[#F4E7E1] border-none rounded-xl p-3 text-sm mb-3">
                <button type="submit" class="w-full bg-[#A0B391] text-white font-bold py-3 rounded-xl hover:bg-[#FFB6C1] transition">Simpan</button>
            </form>

            <div class="overflow-y-auto max-h-[40vh] space-y-3">
                {% for item in schedule_list %}
                <div class="bg-white p-4 rounded-2xl shadow-sm flex items-center justify-between">
                    <div>
                        <span class="text-[10px] font-bold bg-[#A0B391]/20 text-[#A0B391] px-2 py-1 rounded-md mb-1 inline-block">{{ item['role'] }}</span>
                        <h5 class="font-bold text-[#2F4F4F]">{{ item['name'] }}</h5>
                        <p class="text-xs text-gray-400">{{ item['date'] }}</p>
                    </div>
                    <form action="/irma/schedule" method="POST">
                        <input type="hidden" name="delete_id" value="{{ item['id'] }}">
                        <button class="text-gray-300 hover:text-red-400"><i class="fas fa-trash"></i></button>
                    </form>
                </div>
                {% else %}
                <p class="text-center text-gray-400 text-sm">Belum ada jadwal.</p>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- 2. MODAL JOIN -->
    <div id="modal-join" class="hidden fixed inset-0 z-40 bg-[#F4E7E1] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-[#A0B391]/20 pb-4">
                <h3 class="text-xl font-bold text-[#2F4F4F]">Join IRMA</h3>
                <button onclick="closeModal('modal-join')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
            </div>
            
            <form action="/irma/join" method="POST" class="space-y-4">
                <div class="bg-white p-6 rounded-3xl shadow-sm border border-[#A0B391]/20">
                    <div class="mb-4 text-center">
                        <div class="w-16 h-16 bg-[#FFB6C1]/20 rounded-full flex items-center justify-center mx-auto mb-2 text-[#FFB6C1]">
                            <i class="fas fa-user-plus text-3xl"></i>
                        </div>
                        <p class="text-xs text-gray-500">Gabung Komunitas Remaja Positif</p>
                    </div>
                    
                    <div class="space-y-3">
                        <input type="text" name="name" placeholder="Nama Lengkap" required class="w-full bg-[#F4E7E1] border-none rounded-xl p-3 text-sm">
                        <div class="grid grid-cols-2 gap-3">
                            <input type="number" name="age" placeholder="Umur" required class="w-full bg-[#F4E7E1] border-none rounded-xl p-3 text-sm">
                            <input type="text" name="wa_number" placeholder="No WA (08xx)" required class="w-full bg-[#F4E7E1] border-none rounded-xl p-3 text-sm">
                        </div>
                        <input type="text" name="instagram" placeholder="@Instagram" class="w-full bg-[#F4E7E1] border-none rounded-xl p-3 text-sm">
                        <textarea name="hobbies" placeholder="Skill / Hobi (ex: Desain, Futsal)" class="w-full bg-[#F4E7E1] border-none rounded-xl p-3 text-sm h-20"></textarea>
                    </div>
                    
                    <button type="submit" class="w-full bg-[#A0B391] text-white font-bold py-3 mt-4 rounded-xl hover:bg-[#FFB6C1] transition shadow-lg">Daftar Sekarang</button>
                </div>
            </form>
        </div>
    </div>
    <!-- 3. MODAL FINANCE -->
    <div id="modal-finance" class="hidden fixed inset-0 z-40 bg-[#F4E7E1] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-[#A0B391]/20 pb-4">
                <h3 class="text-xl font-bold text-[#2F4F4F]">Kas Remaja</h3>
                <button onclick="closeModal('modal-finance')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
            </div>

            <div class="bg-gradient-to-r from-[#A0B391] to-[#8DA57B] text-white p-6 rounded-3xl shadow-lg mb-6 relative overflow-hidden">
                <div class="absolute right-0 top-0 p-4 opacity-20"><i class="fas fa-wallet text-6xl"></i></div>
                <p class="text-xs opacity-80 mb-1">Saldo Kas Saat Ini</p>
                <h2 class="text-3xl font-bold">Rp {{ "{:,.0f}".format(kas_summary.balance) }}</h2>
                <div class="flex gap-4 mt-4 text-xs font-bold">
                    <span class="bg-white/20 px-2 py-1 rounded">+ {{ "{:,.0f}".format(kas_summary.income) }}</span>
                    <span class="bg-white/20 px-2 py-1 rounded">- {{ "{:,.0f}".format(kas_summary.out) }}</span>
                </div>
            </div>
            
            <form action="/irma/kas" method="POST" class="mb-6 bg-white p-4 rounded-2xl shadow-sm border border-[#A0B391]/20">
                <div class="grid grid-cols-2 gap-3 mb-3">
                    <select name="type" class="w-full bg-[#F4E7E1] border-none rounded-xl p-3 text-sm">
                        <option value="Pemasukan">Pemasukan</option>
                        <option value="Pengeluaran">Pengeluaran</option>
                    </select>
                    <input type="number" name="amount" placeholder="Nominal" required class="w-full bg-[#F4E7E1] border-none rounded-xl p-3 text-sm">
                </div>
                <input type="text" name="description" placeholder="Keterangan (ex: Iuran)" required class="w-full bg-[#F4E7E1] border-none rounded-xl p-3 text-sm mb-3">
                <input type="date" name="date" required class="w-full bg-[#F4E7E1] border-none rounded-xl p-3 text-sm mb-3">
                <button type="submit" class="w-full bg-[#A0B391] text-white font-bold py-3 rounded-xl hover:bg-[#FFB6C1] transition">Catat Transaksi</button>
            </form>

            <div class="overflow-y-auto max-h-[30vh] space-y-2">
                 {% for item in kas_list %}
                 <div class="flex justify-between items-center p-3 bg-white rounded-xl shadow-sm">
                     <div>
                         <p class="text-xs text-gray-500">{{ item['date'] }}</p>
                         <p class="text-sm font-bold text-[#2F4F4F]">{{ item['description'] }}</p>
                     </div>
                     <span class="font-bold text-sm {{ 'text-[#A0B391]' if item['type'] == 'Pemasukan' else 'text-[#FFB6C1]' }}">
                         {{ "+" if item['type'] == 'Pemasukan' else "-" }} {{ "{:,.0f}".format(item['amount']) }}
                     </span>
                 </div>
                 {% endfor %}
            </div>
        </div>
    </div>

    <!-- 4. MODAL MADING -->
    <div id="modal-wall" class="hidden fixed inset-0 z-40 bg-[#F4E7E1] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-[#A0B391]/20 pb-4">
                <h3 class="text-xl font-bold text-[#2F4F4F]">Mading Kreatif</h3>
                <button onclick="closeModal('modal-wall')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
            </div>
            
            <div class="p-4 bg-white border border-[#A0B391]/20 rounded-2xl mb-4">
                 <form action="/irma/gallery" method="POST" enctype="multipart/form-data" class="flex flex-col gap-2">
                     <input type="text" name="title" placeholder="Judul Karya" required class="w-full bg-[#F4E7E1] border-none rounded-lg p-2 text-xs">
                     <input type="text" name="creator" placeholder="Nama Pembuat" required class="w-full bg-[#F4E7E1] border-none rounded-lg p-2 text-xs">
                     <div class="flex gap-2">
                         <input type="file" name="image" class="w-1/2 text-xs text-gray-500">
                         <button type="submit" class="w-1/2 bg-[#A0B391] text-white px-4 rounded-xl font-bold text-xs hover:bg-[#FFB6C1] h-8">Posting</button>
                     </div>
                     <textarea name="content" placeholder="Cerita / Puisi / Caption..." class="w-full bg-[#F4E7E1] border-none rounded-lg p-2 text-xs h-16"></textarea>
                 </form>
            </div>

            <div class="overflow-y-auto max-h-[50vh] p-1 grid grid-cols-2 gap-3 content-start">
                {% for item in gallery_list %}
                <div class="bg-white rounded-2xl shadow-sm overflow-hidden break-inside-avoid border border-[#A0B391]/10">
                    {% if item['content_type'] == 'Image' %}
                    <img src="/uploads/{{ item['content'] }}" class="w-full h-32 object-cover">
                    {% endif %}
                    <div class="p-3">
                        <h5 class="font-bold text-[#2F4F4F] text-xs mb-1">{{ item['title'] }}</h5>
                        <p class="text-[10px] text-[#A0B391] font-bold mb-1">By {{ item['creator'] }}</p>
                        {% if item['content_type'] == 'Text' %}
                        <p class="text-xs text-gray-600 line-clamp-4">{{ item['content'] }}</p>
                        {% endif %}
                    </div>
                </div>
                {% else %}
                <div class="col-span-2 text-center py-10 text-gray-400">Belum ada karya.</div>
                {% endfor %}
            </div>
        </div>
    </div>
    <!-- 5. MODAL PROKER -->
    <div id="modal-events" class="hidden fixed inset-0 z-40 bg-[#F4E7E1] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-[#A0B391]/20 pb-4">
                <h3 class="text-xl font-bold text-[#2F4F4F]">Proker & Event</h3>
                <button onclick="closeModal('modal-events')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
            </div>
            
            <form action="/irma/proker" method="POST" class="mb-6 bg-white p-4 rounded-2xl shadow-sm border border-[#A0B391]/20">
                <input type="text" name="title" placeholder="Nama Kegiatan" required class="w-full bg-[#F4E7E1] border-none rounded-xl p-3 text-sm mb-3">
                <div class="grid grid-cols-2 gap-3 mb-3">
                    <select name="status" class="w-full bg-[#F4E7E1] border-none rounded-xl p-3 text-sm">
                        <option value="Rencana">Rencana</option>
                        <option value="Proses">Proses</option>
                        <option value="Selesai">Selesai</option>
                    </select>
                    <input type="date" name="date" class="w-full bg-[#F4E7E1] border-none rounded-xl p-3 text-sm">
                </div>
                <textarea name="description" placeholder="Deskripsi Singkat" class="w-full bg-[#F4E7E1] border-none rounded-xl p-3 text-sm mb-3"></textarea>
                <button type="submit" class="w-full bg-[#A0B391] text-white font-bold py-3 rounded-xl hover:bg-[#FFB6C1] transition">Tambah Proker</button>
            </form>

            <div class="space-y-3 max-h-[40vh] overflow-y-auto">
                {% for item in proker_list %}
                <div class="bg-white p-4 rounded-2xl shadow-sm border-l-4 {{ 'border-gray-300' if item['status'] == 'Rencana' else ('border-yellow-400' if item['status'] == 'Proses' else 'border-green-500') }}">
                    <div class="flex justify-between items-start">
                        <div>
                            <h5 class="font-bold text-[#2F4F4F]">{{ item['title'] }}</h5>
                            <p class="text-xs text-gray-400">{{ item['date'] }}</p>
                            <p class="text-xs text-gray-500 mt-1">{{ item['description'] }}</p>
                        </div>
                        <span class="text-[10px] font-bold px-2 py-1 rounded {{ 'bg-gray-100 text-gray-600' if item['status'] == 'Rencana' else ('bg-yellow-100 text-yellow-600' if item['status'] == 'Proses' else 'bg-green-100 text-green-600') }}">
                            {{ item['status'] }}
                        </span>
                    </div>
                    
                    <div class="w-full bg-gray-100 rounded-full h-1.5 mt-3">
                        <div class="h-1.5 rounded-full {{ 'bg-gray-400 w-1/3' if item['status'] == 'Rencana' else ('bg-yellow-400 w-2/3' if item['status'] == 'Proses' else 'bg-green-500 w-full') }}"></div>
                    </div>
                </div>
                {% else %}
                <p class="text-center text-gray-400 text-sm">Belum ada proker.</p>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- 6. MODAL CURHAT -->
    <div id="modal-qa" class="hidden fixed inset-0 z-40 bg-[#F4E7E1] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-[#A0B391]/20 pb-4">
                <h3 class="text-xl font-bold text-[#2F4F4F]">Curhat Islami (Anonim)</h3>
                <button onclick="closeModal('modal-qa')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
            </div>
            
            <div class="p-4 bg-white border-b border-[#A0B391]/20">
                    <form action="/irma/curhat" method="POST" class="space-y-3">
                        <textarea name="question" placeholder="Tanya apa saja, identitasmu dirahasiakan..." required class="w-full bg-[#F4E7E1] border-none rounded-xl p-3 text-sm h-24 focus:ring-2 focus:ring-[#FFB6C1]"></textarea>
                        <button type="submit" class="w-full bg-[#A0B391] text-white font-bold py-3 rounded-xl hover:bg-[#FFB6C1] transition">Kirim Pertanyaan</button>
                    </form>
            </div>

            <div class="overflow-y-auto flex-1 p-4 space-y-4">
                {% for item in curhat_list %}
                <div class="bg-white rounded-2xl shadow-sm p-4">
                    <div class="flex gap-3 mb-2">
                        <div class="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-400"><i class="fas fa-user-secret"></i></div>
                        <div class="bg-gray-50 p-3 rounded-r-2xl rounded-bl-2xl text-sm text-gray-700 flex-1">
                            {{ item['question'] }}
                        </div>
                    </div>
                    
                    {% if item['answer'] %}
                    <div class="flex gap-3 flex-row-reverse">
                        <div class="w-8 h-8 rounded-full bg-[#A0B391] flex items-center justify-center text-white"><i class="fas fa-check"></i></div>
                        <div class="bg-[#A0B391]/10 p-3 rounded-l-2xl rounded-br-2xl text-sm text-[#2F4F4F] flex-1 border border-[#A0B391]/20">
                            <p class="font-bold text-[#A0B391] text-xs mb-1">Mentor Menjawab:</p>
                            {{ item['answer'] }}
                        </div>
                    </div>
                    {% else %}
                    <p class="text-[10px] text-gray-400 text-center italic mt-1">Menunggu jawaban mentor...</p>
                    <form action="/irma/curhat" method="POST" class="mt-2 pt-2 border-t border-gray-50">
                        <input type="hidden" name="answer_id" value="{{ item['id'] }}">
                        <input type="text" name="answer" placeholder="Jawab (Admin)..." class="w-full bg-gray-50 text-xs p-2 rounded-lg">
                    </form>
                    {% endif %}
                </div>
                {% else %}
                <p class="text-center text-gray-400 text-sm">Belum ada pertanyaan.</p>
                {% endfor %}
            </div>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const open = '{{ open_modal }}';
            if(open && open !== 'None') openModal(open);
        });
    </script>
</div>
"""

# --- RAMADHAN ROUTES ---

@app.route('/ramadhan')
def ramadhan_dashboard():
    # 1. Takjil Data
    takjil_data = get_takjil_data()
    
    # 2. Imsakiyah Data
    imsakiyah_data = get_imsakiyah_schedule()
    
    # 3. Kas Ramadhan Data
    conn = get_db_connection()
    ramadhan_kas_items = conn.execute("SELECT * FROM ramadhan_kas ORDER BY date DESC").fetchall()
    kas_in = conn.execute("SELECT SUM(amount) FROM ramadhan_kas WHERE type='Pemasukan'").fetchone()[0] or 0
    kas_out = conn.execute("SELECT SUM(amount) FROM ramadhan_kas WHERE type='Pengeluaran'").fetchone()[0] or 0
    
    # 4. Tarawih Schedule
    # Create table if not exists (double check because init_db runs on startup but we might have persistent db)
    # Actually init_db handles creation.
    
    tarawih_schedule = conn.execute("SELECT * FROM tarawih_schedule ORDER BY night_index ASC").fetchall()
    
    # Pre-populate Tarawih if empty
    if not tarawih_schedule:
        for i in range(1, 31):
             conn.execute("INSERT INTO tarawih_schedule (night_index, date, imam, penceramah, judul) VALUES (?, ?, ?, ?, ?)",
                          (i, f"Ramadhan {i}", "-", "-", "-"))
        conn.commit()
        tarawih_schedule = conn.execute("SELECT * FROM tarawih_schedule ORDER BY night_index ASC").fetchall()
        
    conn.close()
    
    # Render CONTENT first to ensure internal Jinja tags are processed
    rendered_content = render_template_string(RAMADHAN_DASHBOARD_HTML,
                                              takjil_data=takjil_data,
                                              imsakiyah_data=imsakiyah_data,
                                              ramadhan_kas_items=ramadhan_kas_items,
                                              ramadhan_kas_summary={'income': kas_in, 'out': kas_out, 'balance': kas_in - kas_out},
                                              tarawih_schedule=tarawih_schedule)

    return render_template_string(BASE_LAYOUT, 
                                  styles=STYLES_HTML + RAMADHAN_STYLES, 
                                  active_page='ramadhan', 
                                  content=rendered_content,
                                  hide_nav=True)

@app.route('/ramadhan/kas', methods=['POST'])
def ramadhan_kas_action():
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO ramadhan_kas (date, type, category, description, amount) VALUES (?, ?, ?, ?, ?)',
                     (request.form['date'], request.form['type'], request.form['category'], 
                      request.form['description'], request.form['amount']))
        conn.commit()
    except Exception as e:
        print(f"Error saving kas: {e}")
    finally:
        conn.close()
    return redirect(url_for('ramadhan_dashboard'))

@app.route('/ramadhan/tarawih', methods=['POST'])
def ramadhan_tarawih_action():
    conn = get_db_connection()
    try:
        night = request.form['night_index']
        exists = conn.execute("SELECT 1 FROM tarawih_schedule WHERE night_index = ?", (night,)).fetchone()
        if exists:
            conn.execute("UPDATE tarawih_schedule SET imam=?, penceramah=?, judul=? WHERE night_index=?",
                         (request.form['imam'], request.form['penceramah'], request.form['judul'], night))
        else:
            conn.execute("INSERT INTO tarawih_schedule (night_index, imam, penceramah, judul) VALUES (?, ?, ?, ?)",
                         (night, request.form['imam'], request.form['penceramah'], request.form['judul']))
        conn.commit()
    except Exception as e:
        print(f"Error saving tarawih: {e}")
    finally:
        conn.close()
    return redirect(url_for('ramadhan_dashboard'))

# --- IRMA ROUTES ---

@app.route('/irma')
def irma_dashboard():
    conn = get_db_connection()
    
    # 1. Schedule List
    schedule_list = conn.execute("SELECT * FROM irma_schedule ORDER BY date DESC, id DESC").fetchall()
    
    # 2. Kas (Finance)
    kas_list = conn.execute("SELECT * FROM irma_kas ORDER BY date DESC").fetchall()
    fin_in = conn.execute("SELECT SUM(amount) FROM irma_kas WHERE type='Pemasukan'").fetchone()[0] or 0
    fin_out = conn.execute("SELECT SUM(amount) FROM irma_kas WHERE type='Pengeluaran'").fetchone()[0] or 0
    kas_summary = {'income': fin_in, 'out': fin_out, 'balance': fin_in - fin_out}
    
    # 3. Gallery (Mading)
    gallery_list = conn.execute("SELECT * FROM irma_gallery ORDER BY created_at DESC").fetchall()
    
    # 4. Proker (Events)
    proker_list = conn.execute("SELECT * FROM irma_proker ORDER BY date ASC").fetchall()
    
    # 5. Curhat (Q&A)
    curhat_list = conn.execute("SELECT * FROM irma_curhat ORDER BY created_at DESC").fetchall()
    
    conn.close()
    
    # IRMA THEME
    irma_theme = {
        'nav_bg': 'bg-[#F4E7E1]/90 backdrop-blur-md border-b border-[#A0B391]/20',
        'icon_bg': 'bg-[#A0B391]/20',
        'icon_text': 'text-[#A0B391]',
        'title_text': 'text-[#A0B391]',
        'link_hover': 'hover:text-[#FFB6C1]',
        'link_active': 'text-[#FFB6C1] font-bold',
        'btn_primary': 'bg-[#A0B391] text-white hover:bg-[#FFB6C1]',
        'bottom_nav_bg': 'bg-[#A0B391]',
        'bottom_active': 'text-[#FFB6C1]',
        'bottom_btn_bg': 'bg-[#FFB6C1]',
        'bottom_btn_text': 'text-white',
        'bottom_text_inactive': 'text-[#F4E7E1]'
    }

    open_modal = request.args.get('open')

    # Render with custom styles
    return render_template_string(BASE_LAYOUT, 
                                  styles=STYLES_HTML + IRMA_STYLES, 
                                  active_page='irma', 
                                  theme=irma_theme,
                                  content=render_template_string(IRMA_DASHBOARD_HTML,
                                                                 schedule_list=schedule_list,
                                                                 kas_list=kas_list,
                                                                 kas_summary=kas_summary,
                                                                 gallery_list=gallery_list,
                                                                 proker_list=proker_list,
                                                                 curhat_list=curhat_list,
                                                                 open_modal=open_modal))

@app.route('/irma/schedule', methods=['POST'])
def irma_schedule():
    conn = get_db_connection()
    if 'delete_id' in request.form:
        conn.execute('DELETE FROM irma_schedule WHERE id = ?', (request.form['delete_id'],))
    else:
        conn.execute('INSERT INTO irma_schedule (name, role, date) VALUES (?, ?, ?)',
                     (request.form['name'], request.form['role'], request.form['date']))
    conn.commit()
    conn.close()
    return redirect(url_for('irma_dashboard', open='modal-duty'))

@app.route('/irma/join', methods=['POST'])
def irma_join():
    conn = get_db_connection()
    conn.execute('INSERT INTO irma_members (name, age, hobbies, instagram, wa_number) VALUES (?, ?, ?, ?, ?)',
                 (request.form['name'], request.form['age'], request.form['hobbies'], request.form['instagram'], request.form['wa_number']))
    conn.commit()
    conn.close()
    return redirect(url_for('irma_dashboard', open='modal-join'))

@app.route('/irma/kas', methods=['POST'])
def irma_kas():
    conn = get_db_connection()
    conn.execute('INSERT INTO irma_kas (date, type, description, amount) VALUES (?, ?, ?, ?)',
                 (request.form['date'], request.form['type'], request.form['description'], request.form['amount']))
    conn.commit()
    conn.close()
    return redirect(url_for('irma_dashboard', open='modal-finance'))

@app.route('/irma/gallery', methods=['POST'])
def irma_gallery():
    conn = get_db_connection()
    title = request.form['title']
    creator = request.form['creator']
    content = request.form.get('content', '')
    post_type = 'Text'
    
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                content = filename
                post_type = 'Image'
            
    conn.execute('INSERT INTO irma_gallery (title, creator, content_type, content) VALUES (?, ?, ?, ?)',
                 (title, creator, post_type, content))
    conn.commit()
    conn.close()
    return redirect(url_for('irma_dashboard', open='modal-wall'))

@app.route('/irma/proker', methods=['POST'])
def irma_proker():
    conn = get_db_connection()
    conn.execute('INSERT INTO irma_proker (title, status, description, date) VALUES (?, ?, ?, ?)',
                 (request.form['title'], request.form['status'], request.form['description'], request.form['date']))
    conn.commit()
    conn.close()
    return redirect(url_for('irma_dashboard', open='modal-events'))

@app.route('/irma/curhat', methods=['POST'])
def irma_curhat():
    conn = get_db_connection()
    if 'answer' in request.form:
        conn.execute('UPDATE irma_curhat SET answer = ?, answered_at = ? WHERE id = ?',
                     (request.form['answer'], datetime.datetime.now(), request.form['answer_id']))
    else:
        conn.execute('INSERT INTO irma_curhat (question) VALUES (?)', (request.form['question'],))
    conn.commit()
    conn.close()
    return redirect(url_for('irma_dashboard', open='modal-qa'))

# --- PWA ROUTES ---

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "Masjid Al Hijrah",
        "short_name": "Al Hijrah",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0b1026",
        "theme_color": "#FFD700",
        "icons": [
            {
                "src": "/static/logomasjidalhijrah.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/logomasjidalhijrah.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    })

@app.route('/sw.js')
def service_worker():
    sw_code = """
const CACHE_NAME = 'al-hijrah-v1';
const ASSETS_TO_CACHE = [
    '/',
    '/static/logomasjidalhijrah.png',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    'https://cdn.tailwindcss.com'
];

self.addEventListener('install', (event) => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    return self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    // Network First Strategy for HTML (Navigation)
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request).catch(() => {
                return caches.match(event.request);
            })
        );
        return;
    }

    // Cache First Strategy for Static Assets
    event.respondWith(
        caches.match(event.request).then((response) => {
            if (response) {
                return response;
            }
            return fetch(event.request).then((networkResponse) => {
                if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
                    return networkResponse;
                }
                const responseToCache = networkResponse.clone();
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, responseToCache);
                });
                return networkResponse;
            });
        })
    );
});
"""
    return Response(sw_code, mimetype='application/javascript')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
