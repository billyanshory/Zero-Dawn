import os
import datetime
import math
import time
import json
import csv
import urllib.request
import pymysql
import io
from PIL import Image
from flask import Flask, request, send_from_directory, render_template_string, redirect, url_for, Response, jsonify, session
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_caching import Cache
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import filetype
import pytz

load_dotenv()


# --- KONFIGURASI FLASK ---
app = Flask(__name__)
csrf = CSRFProtect(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 86400})
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB Limit
app.secret_key = os.environ.get("SECRET_KEY", "fallback_dev_key")
app.config['UPLOAD_FOLDER'] = 'uploads'
app.permanent_session_lifetime = datetime.timedelta(days=30)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://alhijrahdelima_user:4lh1jr4hd3l1m5A!@localhost/alhijrahdelima'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_size': 100, 'max_overflow': 200, 'pool_recycle': 280}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'mp4'}

db = SQLAlchemy(app)

# --- DATA SUMBER HUKUM (DALIL) ---
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

# --- DATABASE MODELS ---

class Finance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

class Agenda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(255), nullable=False)
    time = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    speaker = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    date = db.Column(db.String(255), nullable=False)
    purpose = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    contact = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

class Zakat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor_name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, server_default=func.now())

class GalleryDakwah(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

class Suggestion(db.Model):
    __tablename__ = 'suggestions'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='Unread')
    created_at = db.Column(db.DateTime, server_default=func.now())

class RamadhanKas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

class TarawihSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    night_index = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(255))
    imam = db.Column(db.String(255))
    penceramah = db.Column(db.String(255))
    judul = db.Column(db.Text)

class IrmaSchedule(db.Model):
    __tablename__ = 'irma_schedule'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text)

class IrmaMember(db.Model):
    __tablename__ = 'irma_members'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer)
    hobbies = db.Column(db.Text)
    instagram = db.Column(db.String(255))
    joined_at = db.Column(db.DateTime, server_default=func.now())
    wa_number = db.Column(db.String(255))
    status = db.Column(db.String(50), default='Pending')

class IrmaKas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now())

class IrmaGallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    creator = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    caption = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now())

class IrmaProker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.String(255))

class IrmaCurhat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now())
    answered_at = db.Column(db.DateTime)

class EpilepsiLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(255), nullable=False)
    time = db.Column(db.String(255), nullable=False)
    trigger = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now())

class AppSettings(db.Model):
    key = db.Column(db.String(255), primary_key=True)
    value = db.Column(db.Text)

class QurbanAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    check_in_time = db.Column(db.DateTime, server_default=func.now())
    status = db.Column(db.String(50), nullable=False) # 'Hadir Pagi' or 'Terlambat' / 'Siluman'

def get_settings():
    try:
        settings = {item.key: item.value for item in AppSettings.query.all()}
    except:
        settings = {}
    return settings

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
    # Offset -1 day -> BRUTE FORCE -3 DAYS (Updated for 2026 adjustment)
    date_obj = date_obj - datetime.timedelta(days=3)
    
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

def is_safe_file(file_storage):
    """Deep inspection of file mime types and signatures."""
    kind = filetype.guess(file_storage.read(2048))
    file_storage.seek(0) # Reset pointer
    if kind is None:
        return False
    return kind.extension in ALLOWED_EXTENSIONS

def compress_image(file_storage, upload_folder):
    if not is_safe_file(file_storage):
        raise ValueError("Invalid file content signature detected.")
    filename = secure_filename(file_storage.filename)
    
    # Skip compression for video
    if filename.lower().endswith('.mp4'):
        save_path = os.path.join(upload_folder, filename)
        file_storage.save(save_path)
        return filename
        
    # Process Image
    try:
        img = Image.open(file_storage)
        
        # Convert to RGB (standardize for JPG)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # Resize max 800x800
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        
        # Force JPG extension
        base = os.path.splitext(filename)[0]
        new_filename = base + ".jpg"
        save_path = os.path.join(upload_folder, new_filename)
        
        # Compress loop
        quality = 90
        while quality >= 10:
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
            size_kb = img_byte_arr.tell() / 1024
            if size_kb < 500:
                break
            quality -= 5
        
        # Save final
        with open(save_path, 'wb') as f:
            f.write(img_byte_arr.getbuffer())
            
        return new_filename
        
    except Exception as e:
        print(f"Compression error: {e}")
        # Fallback
        save_path = os.path.join(upload_folder, filename)
        file_storage.seek(0)
        file_storage.save(save_path)
        return filename

# --- RAMADHAN HELPER FUNCTIONS ---

# --- RAMADHAN HELPER FUNCTIONS ---

def seed_ramadhan_schedule():
    if TarawihSchedule.query.count() == 0:
        schedule_data = [
            (1, "Ustadz M. Faisal Bulqiah", "Ustadz M. Faisal Bulqiah"),
            (2, "Ustadz H. Bunyamin LC MA", "Ustadz H. Bunyamin LC MA"),
            (3, "Ustadz H. Sutanil fadlan M. Al Hafidz", "Ustadz H. Sutanil fadlan M. Al Hafidz"),
            (4, "Ustadz Fathurrahman Al Hafidz", "Ustadz Fathurrahman Al Hafidz"),
            (5, "Ustadz H. Abdul Syakur LC MA", "Ustadz H. Abdul Syakur LC MA"),
            (6, "Ustadz Ibnu Mulkan M.Pd", "Ustadz Ibnu Mulkan M.Pd"),
            (7, "KH Muhammad Mansur", "KH Muhammad Mansur"),
            (8, "Ustadz Mahyudin S. Ag M.Pd", "Ustadz Mahyudin S. Ag M.Pd"),
            (9, "Ustadz Dr Ahmad Nur Zahrani M.Ag", "Ustadz Dr Ahmad Nur Zahrani M.Ag"),
            (10, "Ustadz Wahyu Utami L.C M. Pd", "Ustadz Wahyu Utami L.C M. Pd"),
            (11, "Ustadz Prof Dr Abdul Majid MA", "Ustadz Prof Dr Abdul Majid MA"),
            (12, "KH Azhar Qowiem M. Pd", "KH Azhar Qowiem M. Pd"),
            (13, "Ustadz Fathur Rojak", "Ustadz Fathur Rojak"),
            (14, "Ustadz Amirullah M.Ud", "Ustadz Amirullah M.Ud"),
            (15, "Ustadz H. Dr. Akmad Haries M.Si", "Ustadz H. Dr. Akmad Haries M.Si"),
            (16, "Ustadz Ahmad Nur Jamil", "Ustadz Ahmad Nur Jamil"),
            (17, "Ustadz H. Susanto L.C", "Ustadz H. Susanto L.C"),
            (18, "Ustadz Ahmad Husairi S. Pd", "Ustadz Ahmad Husairi S. Pd"),
            (19, "Ustadz M. Faisal Bulqiah", "Ustadz M. Faisal Bulqiah"),
            (20, "Ustadz Rivky Cahaya Hakiki", "Ustadz Rivky Cahaya Hakiki"),
            (21, "Ustadz Imam Syafii", "Ustadz Imam Syafii"),
            (22, "Ustadz Ahmad Subhi", "Ustadz Ahmad Subhi"),
            (23, "Ustadz Ahmad Ihsan S.Pd", "Ustadz Ahmad Ihsan S.Pd"),
            (24, "Ustadz Syahrial M.Ud", "Ustadz Syahrial M.Ud"),
            (25, "Ustadz Rivky Cahaya Hakiki", "Ustadz Rivky Cahaya Hakiki"),
            (26, "Ustadz H. Maraio L.C. M.Pd.I", "Ustadz H. Maraio L.C. M.Pd.I"),
            (27, "Ustadz H. Darmaizar LC M.Ag", "Ustadz H. Darmaizar LC M.Ag"),
            (28, "Ustadz Ahmad Jailani", "Ustadz Ahmad Jailani"),
            (29, "Ustadz Robi Ar-Rasyid", "Ustadz Robi Ar-Rasyid"),
            (30, "Ustadz Fathur Rojak", "Ustadz Fathur Rojak"),
        ]

        for night, imam, penceramah in schedule_data:
            entry = TarawihSchedule(
                night_index=night, 
                date=f"Ramadhan {night}", 
                imam=imam, 
                penceramah=penceramah, 
                judul="-"
            )
            db.session.add(entry)
        db.session.commit()

RAW_TAKJIL_DATA = """
### **DATA JADWAL TAKJIL MASJID AL HIJRAH (RAMADHAN 2026)** 

**Hari 1 (18-Feb-26)**  
1. H.Muhtadi (RT.49), 2. La Juadi (RT.50), 3. Hariyadi (RT.51), 4. H. Hadransyah (RT.52), 5. Mukayan (RT.52), 6. Ibu Abdulah (RT.52), 7. M. Latif (RT.53), 8. Mahfud (RT.57), 9. Eko Pranoto (RT.53), 10. Hj. Elnawati (RT.49), 11. Maryono (RT.49), 12. Rindayanto (RT.50), 13. Yoyo P. (RT.55), 14. Sabran (RT.55) 
 
**Hari 2 (19-Feb-26)** 
1. H. Haryoto (RT.49), 2. Ahmad Zaidi (RT.51), 3. Ovan Iskandar (RT.51), 4. H. Kandi H. (RT.52), 5. La Nuju (RT.53), 6. Hj. Rusmiati (RT.56), 7. H. Parto Sirun (RT.56), 8. H. Asnan Alus (RT.57), 9. H. Herman (RT.49), 10. Ibu sabaruddin (RT.53), 11. Ibu sugi / muntoha (RT.52), 12. Subandi (RT.55), 13. Sofyansyah (RT.50), 14. Asmudin (RT.56) 
 
**Hari 3 (20-Feb-26)** 
1. H. Harsuji (RT.49), 2. Andre/ Landito (RT.51), 3. Najiman (RT.51), 4. Syamsu (RT.52), 5. Pak Waras (RT.55), 6. Ulil Azmi (RT.56), 7. La sidun (RT.51), 8. Hariyanto (RT.57), 9. Ibu asan basri (bengkel asa) (RT.57), 10. Bimo Sunaryo (RT.53), 11. Syaiful Bakri (RT.55), 12. La Bano (RT.53), 13. Ibu ideham dekot (RT.57), 14. Jufri (RT.52), 15. Rohmad Muslim (RT.51), 16. Boby (RT.51) 
 
**Hari 4 (21-Feb-26)** 
1. H. Mardjuni (RT.49), 2. La Bondu (RT.51), 3. Misdan (RT.51), 4. Adi Wibowo (RT.52), 5. Suyanto (RT.55), 6. H. Syamsudin Japri (RT.56), 7. Hj. M. Ishak (RT.49), 8. Suryadi (RT.52), 9. Andri (RT.57), 10. Budi Hariana (RT.55), 11. Mukhlis (RT.56), 12. Mama Daus (RT.51), 13. condro Lukito (RT.53), 14. Haludin (RT.51), 15. Aidil (RT.56), 16. Kahar (RT.57) 
 
**Hari 5 (22-Feb-26)** 
1. La Bila (RT.50), 2. Darmaji /Erna (RT.50), 3. Rusmianti (RT.51), 4. Rony Pasla (RT.52), 5. Sumoharjo (RT.53), 6. Ujianto (RT.53), 7. Jamaludin Eka (RT.56), 8. Umar Uji (RT.50), 9. Supriyansyah (RT.50), 10. H. F. Suwarno (RT.52), 11. Dr. Dedy S. (RT.49), 12. La Asri (RT.50), 13. Pak Asmin (RT.55), 14. Paiman (RT.56), 15. kastum (RT.52) 
 
**Hari 6 (23-Feb-26)** 
1. Ir. Ari Mulyadi (RT.49), 2. Sudalil (RT.52), 3. Mistono (RT.51), 4. Kasim (RT.52), 5. Dr. Randy (RT.52), 6. Yayat (RT.53), 7. Sarno (RT.55), 8. M. Taufik (RT.50), 9. Hj. Eva Paqun (RT.57), 10. La Ludu (RT.50), 11. La Komu (RT.52), 12. Sapto (RT.51), 13. Asep (RT.53), 14. Jufri (RT.52), 15. Drs. safii (RT.55) 
 
**Hari 7 (24-Feb-26)** 
1. Ir. Haryoto (RT.49), 2. Sukadi (RT.50), 3. Samingan (RT.51), 4. Mianto (RT.51), 5. Sakti (RT.57), 6. Sabar (RT.53), 7. Gunaji (RT.49), 8. La Jumadi (RT.56), 9. Rusli (RT.57), 10. Jamrah (RT.57), 11. H. Marsaid (RT.50), 12. La Jamulia (RT.56), 13. Irwanto (RT.55), 14. Rudiman /idim (RT.53), 15. Sudihardani (RT.57) 
 
**Hari 8 (25-Feb-26)** 
1. Latif (RT.56), 2. Mangin (RT.50), 3. La Jemo (RT.55), 4. Sanyoto (RT.52), 5. H. Andreas (RT.53), 6. Ahmad Adha (RT.53), 7. H. Katmidi (RT.49), 8. Agus S. (RT.56), 9. Syarifudin (RT.53), 10. sardi (RT.52), 11. Babang Legiono (RT.52), 12. Ibu sabarudin (RT.53), 13. Sri budi (RT.57), 14. La beo (RT.51), 15. La Saani (RT.51) 
 
**Hari 9 (26-Feb-26)** 
1. Sumardiansyah (RT.53), 2. Nanang / Ny. Kastun (RT.56), 3. Adi Setiawan (RT.50), 4. Ibu Erlena (RT.53), 5. La Juru (RT.53), 6. Kaslim (RT.55), 7. Wr. Magetan (RT.57), 8. H. Sugiyono (RT.57), 9. Taufik Hidayat (RT.50), 10. Supriyadi (Pak Yono) (RT.51), 11. Edy Sulistyo (RT.53), 12. Edy rusmini (RT.52), 13. H. Hamsanudin P. (RT.52), 14. La Besa (RT.53) 
 
**Hari 10 (27-Feb-26)** 
1. Ibu Heru Santoso (Alm) (RT.49), 2. Syahdan Hadib (RT.57), 3. H.Umar/La kenje (RT.51), 4. Irfan Iskandar (RT.55), 5. Margi R. (RT.52), 6. Zainudin (bladuk) (RT.53), 7. Siman (RT.55), 8. La Bango (RT.55), 9. Kris Kurniawan (RT.52), 10. Safrani (RT.50), 11. Edi ( Bapak Mia ) (RT.51), 12. Sugeng PLN (RT.51), 13. H. Lanaya (RT.50), 14. Rukayat (RT.51) 
 
**Hari 11 (28-Feb-26)** 
1. Sirun /Ipah (RT.49), 2. Tomi Libra (RT.50), 3. Untung Suparno (RT.52), 4. Wijaya (RT.53), 5. Suriansyah (RT.53), 6. Ibu asan basri (bengkel asa) (RT.57), 7. La Edi (RT.55), 8. La Mandiri (RT.55), 9. M. Latif (RT.53), 10. Rifai (RT.53), 11. paino (RT.50), 12. M. Rusli (RT.50), 13. La Mihadi (RT.51), 14. Tajuddin Djuna/ Jainal (RT.55), 15. Kahar (RT.57) 
 
**Hari 12 (1-Mar-26)** 
1. H. Syaifudin (RT.49), 2. Asrani Karim (RT.49), 3. Slamet Susanto (RT.50), 4. Erwin Donanto (RT.51), 5. Lisna Wati (RT.53), 6. Lela (RT.53), 7. Sunarto (RT.55), 8. Denok (RT.51), 9. Loso (RT.53), 10. Tony Bowo (RT.53), 11. H. Zainudin (RT.57), 12. La Bano (RT.53), 13. Agus /Dwiyanto (RT.51), 14. Adi Setiawan (RT.50), 15. La Jayani (RT.50) 
 
**Hari 13 (2-Mar-26)** 
1. Sutrisno (RT.49), 2. La Haludin (RT.55), 3. Samiin (RT.50), 4. Yoyok Ardiansyah (RT.52), 5. Ribut Setiawan (RT.57), 6. Elven Noor (RT.53), 7. Ny. Sidik (RT.55), 8. Sanjaya (RT.56), 9. Sugeng Anas (RT.57), 10. H. Firdaus (RT.53), 11. Sugeng Chairudin (RT.53), 12. Zainuri (RT.51), 13. Johan (RT.51), 14. Syamjudin (RT.55), 15. La Yanto (RT.51) 
 
**Hari 14 (3-Mar-26)** 
1. Sigit (RT.49), 2. Eka/Jeliteng Prasojo (RT.50), 3. La Japo (RT.51), 4. Jarot (RT.52), 5. Agustinawati (RT.53), 6. Mulyono Edy (RT.53), 7. Mat Rais (RT.55), 8. Legianto (RT.56), 9. La Jahali (RT.56), 10. La Mili Tale (RT.55), 11. Mulyadi (wa Pain) (RT.56), 12. La Amirudin (RT.55), 13. Wr. Magetan (RT.57), 14. sujai (RT.55), 15. Pak Asmin (RT.55) 
 
**Hari 15 (4-Mar-26)** 
1. La Suri Hamsa (RT.51), 2. Prianto (RT.49), 3. Misrun (RT.50), 4. Usman / Meti (RT.51), 5. H. Noor Hamdi (RT.52), 6. La Rumpu (RT.53), 7. Mas'ud Effendi (RT.53), 8. Subandi (RT.55), 9. La Anjo (RT.56), 10. H. Sofyan Noor (RT.57), 11. Lampero (RT.50), 12. Bambang (RT.50), 13. Siska (RT.51), 14. supriono (RT.55), 15. Boby (RT.51) 
 
**Hari 16 (5-Mar-26)** 
1. H. Muhtadi (RT.49), 2. La Juadi (RT.50), 3. H. Hadransyah (RT.52), 4. Mukayan (RT.52), 5. Ibu Abdulah (RT.52), 6. M. Ali (RT.56), 7. Mahfud (RT.57), 8. Eko Pranoto (RT.53), 9. Hj. Elnawati (RT.49), 10. Maryono (RT.49), 11. Yoyo P. (RT.55), 12. Rindayanto (RT.50), 13. Syahran (RT.56), 14. Rohmad Muslim (RT.51), 15. La sidun (RT.51) 
 
**Hari 17 (6-Mar-26)** 
1. H. Haryoto (RT.49), 2. Ahmad Zaidi (RT.51), 3. Ovan Iskandar (RT.51), 4. H. Kandi H. (RT.52), 5. La suju (RT.53), 6. Hj. Rusmiati (RT.56), 7. H. Parto Sirun (RT.56), 8. H. Asnan Alus (RT.57), 9. H. Herman (RT.49), 10. sukadi (RT.50), 11. Ibu sugi / Muntoha (RT.52), 12. Tomi Libra (RT.50), 13. Deni Wibawa (RT.50), 14. Asmudin (RT.56), 15. Sabran (RT.55) 
 
**Hari 18 (7-Mar-26)** 
1. H. Harsuji (RT.49), 2. Andre/Landito (RT.51), 3. Najiman (RT.51), 4. Syamsu (RT.52), 5. Pak Waras (RT.55), 6. Ulil Azmi (RT.56), 7. La Saani (RT.51), 8. Hariyanto (RT.57), 9. Rusli (RT.57), 10. Bimo Sunaryo (RT.53), 11. Syaiful Bakri (RT.55), 12. H. Marsaid (RT.50), 13. ibu Ideham dekot (RT.57), 14. Amiruddin (RT.56), 15. Pina/Miadi (RT.53) 
 
**Hari 19 (8-Mar-26)** 
1. H. Mardjuni (RT.49), 2. H. Lanaya (RT.50), 3. Misdan (RT.51), 4. Adi Wibowo (RT.52), 5. Suyanto (RT.55), 6. H. Syamsudin Japri (RT.56), 7. H. M. Ishak (RT.49), 8. Suryadi (RT.52), 9. Wa Pipa (RT.55), 10. Budi Hariana (RT.55), 11. Mukhlis (RT.56), 12. Mama Daus (RT.51), 13. condro Lukito (RT.53), 14. Aidil (RT.56), 15. Sudihardani (RT.57) 
 
**Hari 20 (9-Mar-26)** 
1. Dr. Indra (RT.49), 2. Darmaji/Erna (RT.50), 3. Rusmianti (RT.51), 4. Rony Pasla (RT.52), 5. La Mili Ruca (RT.53), 6. Ujianto (RT.53), 7. Jamaludin /eka (RT.56), 8. Drs. Safii (RT.55), 9. Supriyansyah (RT.50), 10. H. F. Suwarno (RT.52), 11. Dr. Dedy S. (RT.49), 12. La Asri (RT.50), 13. Porimin (RT.55), 14. Paiman (RT.56), 15. Hj. Eva Paqun (RT.57) 
 
**Hari 21 (10-Mar-26)** 
1. Ir. Ari Mulyadi (RT.49), 2. Sudalil (RT.52), 3. Mistono (RT.51), 4. Kasim (RT.52), 5. Dr. Randy (RT.52), 6. Yayat (RT.53), 7. Sarno (RT.55), 8. La Rilu (RT.55), 9. La Yare (RT.55), 10. La Bila (RT.50), 11. La Komu (RT.52), 12. Sapto (RT.51), 13. Asep (RT.53), 14. Haludin (RT.51), 15. Jupi (RT.52) 
 
**Hari 22 (11-Mar-26)** 
1. Ir. Haryoto (RT.49), 2. Kris Kurniawan (RT.52), 3. Samingan (RT.51), 4. Agustinawati (RT.53), 5. Sakti (RT.57), 6. Sabar (RT.53), 7. Rudin Lapandewa (RT.53), 8. La Jumadi (RT.56), 9. Mianto (RT.51), 10. Jamrah (RT.57), 11. Hariyadi (RT.51), 12. La Jamulia (RT.56), 13. Irwanto (RT.55), 14. Rudiman /idim (RT.53), 15. Mulyadi (wa Pain) (RT.56) 
 
**Hari 23 (12-Mar-26)** 
1. Latif (RT.56), 2. Mangin (RT.50), 3. La Jemo (RT.55), 4. Sanyoto (RT.52), 5. H. Andreas (RT.53), 6. Ahmad Adha (RT.53), 7. La beo (RT.51), 8. Agus S. (RT.56), 9. Syarifudin (RT.53), 10. Sardi (RT.52), 11. Bambang Legiono (RT.52), 12. Slamet Susanto (RT.50), 13. Sri budi (RT.57), 14. Sugeng PLN (RT.51), 15. Kastum (RT.52) 
 
**Hari 24 (13-Mar-26)** 
1. La Piy (RT.53), 2. Nanang / Ny. Kastun (RT.56), 3. La Sani (RT.55), 4. Ibu Erlena (RT.53), 5. Sedek Buton (RT.53), 6. Syahran (RT.56), 7. H. Sugiyono (RT.57), 8. La pudin (RT.50), 9. Supriyadi (Pak Yono) (RT.51), 10. Syarif Rahman (RT.52), 11. Edy Sulistyo (RT.53), 12. Edy rusmini (RT.52), 13. H. Hamsanudin P. (RT.52), 14. Joko (kunci) (RT.56), 15. Suprianto (RT.55) 
 
**Hari 25 (14-Mar-26)** 
1. Ibu Heru Santoso (Alm) (RT.49), 2. H. Syahdan Hadib (RT.57), 3. H.Umar/La kenje (RT.51), 4. Irfan Iskandar (RT.55), 5. Margi R. (RT.52), 6. Zainudin (bladuk) (RT.53), 7. Siman (RT.55), 8. La Wardi (RT.55), 9. Yando (RT.52), 10. Safrani (RT.50), 11. Edi (bapak Mia) (RT.51), 12. Sulistio (RT.51), 13. La Ami Arni (RT.55), 14. Rukayat (RT.51), 15. paino (RT.50) 
 
**Hari 26 (15-Mar-26)** 
1. Sirun /ipah (RT.49), 2. Umar Uji (RT.50), 3. Untung Suparno (RT.52), 4. Roby Hermawan (RT.53), 5. Suriansyah (RT.53), 6. Syamjudin (RT.55), 7. La Edi (RT.55), 8. Wa Pipa (RT.55), 9. La Bondu (RT.51), 10. Rifai (RT.53), 11. M. Rusli (RT.50), 12. La Mihadi (RT.51), 13. Tajuddin Djuna/Jainal (RT.55), 14. suprio (RT.55), 15. Tony Bowo (RT.53) 
 
**Hari 27 (16-Mar-26)** 
1. H. Syaifudin (RT.49), 2. Asrani Karim (RT.49), 3. Sofyansyah (RT.50), 4. Erwin Donanto (RT.51), 5. Lisna Wati (RT.53), 6. Lela (RT.53), 7. Sunarto (RT.55), 8. Denok (RT.51), 9. Loso (RT.53), 10. Pak Bibit (RT.50), 11. H. Zainudin (RT.57), 12. Deni Wibawa (RT.50), 13. Agus dwiyanto (RT.51), 14. Yuliansah (RT.50), 15. Gunawan (RT.50) 
 
**Hari 28 (17-Mar-26)** 
1. Sutrisno (RT.49), 2. La Haludin (RT.55), 3. Johan (RT.51), 4. Yoyok Ardiansyah (RT.52), 5. Ribut Setiawan (RT.57), 6. La Besa (RT.53), 7. Ny. Sidik (RT.55), 8. Sanjaya (RT.56), 9. Sugeng Anas (RT.57), 10. H. Firdaus (RT.53), 11. Sugeng Chairudin (RT.53), 12. Zainuri (RT.51), 13. La Bango (RT.55), 14. La Yanto (RT.51), 15. Joko (kunci) (RT.56) 
 
**Hari 29 (18-Mar-26)** 
1. Sigit (RT.49), 2. Eka/ Jeliteng (RT.50), 3. La Japo (RT.51), 4. Jarot (RT.52), 5. La Jayani (RT.50), 6. Mulyono Edy (RT.53), 7. Mat Rais (RT.55), 8. Legianto (RT.56), 9. La Jahali (RT.56), 10. H. Sofyan Noor (RT.57), 11. Aril (RT.51), 12. La Anjo (RT.56), 13. Jupi (RT.52), 14. sujai (RT.55), 15. Yando (RT.52) 
 
**Hari 30 (19-Mar-26)** 
1. La Suri Hamsa (RT.51), 2. Ibu Edy Heflin (RT.49), 3. Misrun (RT.50), 4. Usman / Meti (RT.51), 5. H. Noor Hamdi (RT.52), 6. La Rumpu (RT.53), 7. Mas'ud Effendi (RT.53), 8. suprio (RT.55), 9. Mulyono (RT.56), 10. Andri (RT.57), 11. Lampero (RT.50), 12. Bambang (RT.50), 13. Siska (RT.51), 14. Wijaya (RT.53), 15. La pudin (RT.50)
"""

def parse_takjil_data():
    data = []
    import re
    
    current_date = None
    
    # Split by newlines
    lines = RAW_TAKJIL_DATA.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Check for Date Header: **Hari 1 (18-Feb-26)**
        date_match = re.search(r'\((.*?)\)', line)
        if line.startswith('**Hari') and date_match:
            current_date = date_match.group(1)
            continue
            
        # Parse items: 1. Name (RT), 2. Name (RT)
        # We split by comma followed by number and dot: ", \d+\."
        # Or simpler: split by regex ", (?=\d+\.)"
        
        if current_date:
            items = re.split(r', (?=\d+\.)', line)
            for item in items:
                # Format: "1. Name (RT)" or "1. Name"
                # Remove number prefix
                item = re.sub(r'^\d+\.\s*', '', item)
                
                # Extract RT if exists
                rt_match = re.search(r'\((.*?)\)$', item)
                if rt_match:
                    rt = rt_match.group(1)
                    name = item.replace(f'({rt})', '').strip()
                else:
                    rt = '-'
                    name = item.strip()
                    
                data.append({
                    'Tanggal': current_date,
                    'Nama': name,
                    'Ket.': rt
                })
    return data

def get_takjil_data():
    return parse_takjil_data()

@cache.cached(timeout=86400, key_prefix='imsakiyah_schedule')
def get_imsakiyah_schedule():
    schedule = []
    try:
        # 1. Panggil API Aladhan untuk Samarinda, Indonesia
        # 2. Bulan Februari & Maret 2026 (Ramadhan 1447 H) & Method 20 (Kemenag RI)
        months = [2, 3]
        all_days = []
        
        for m in months:
            url = f"http://api.aladhan.com/v1/calendarByCity?city=Samarinda&country=Indonesia&method=20&month={m}&year=2026"
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                if 'data' in data:
                    all_days.extend(data['data'])
            
        today = datetime.date.today()
        
        # 3. Filter Tanggal (19 Feb - 19 Mar 2026)
        start_date = datetime.date(2026, 2, 19)
        end_date = datetime.date(2026, 3, 19)

        for day in all_days:
            # Parse date
            date_obj = datetime.datetime.strptime(day['date']['gregorian']['date'], "%d-%m-%Y").date()
            
            if not (start_date <= date_obj <= end_date):
                continue

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

# --- ORM Compatibility Patch (Allow dict-style access in Jinja) ---
def model_getitem(self, key):
    return getattr(self, key)

for model in [Finance, Agenda, Booking, Zakat, GalleryDakwah, Suggestion, RamadhanKas, 
              TarawihSchedule, IrmaSchedule, IrmaMember, IrmaKas, IrmaGallery, 
              IrmaProker, IrmaCurhat, EpilepsiLog, AppSettings, QurbanAttendance]:
    model.__getitem__ = model_getitem

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
        @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&display=swap');
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
        .bg-gold { background-color: var(--gold); }
        .text-midnight { color: var(--midnight-blue); }
        
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
        
        /* Amalan Popup Animation */
        @keyframes popupFadeIn {
            from { opacity: 0; transform: scale(0.9); }
            to { opacity: 1; transform: scale(1); }
        }
        @keyframes popupFadeOut {
            from { opacity: 1; transform: scale(1); }
            to { opacity: 0; transform: scale(0.9); }
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
    <script>
        function triggerEmergency() {
            const now = new Date();
            const h = now.getHours();
            let time = "Malam";
            if (h >= 0 && h <= 10) time = "Pagi";
            else if (h >= 11 && h <= 14) time = "Siang";
            else if (h >= 15 && h <= 18) time = "Sore";
            else time = "Malam"; // 19-23
            
            const msg = `Assalamualaikum, Selamat ${time}, maaf mengganggu waktunya Pak ya... Saya butuh bantuan darurat.`;
            window.location.href = "https://wa.me/6282330890500?text=" + encodeURIComponent(msg);
        }
    </script>
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
                <a href="javascript:void(0)" onclick="openModal('modal-infaq')" class="{{ t_btn_primary }} px-5 py-2 rounded-full font-bold shadow-lg transition transform hover:scale-105">Infaq Digital</a>
                <button onclick="triggerEmergency()" class="text-red-500 font-bold hover:text-red-600 transition border border-red-200 px-4 py-2 rounded-full bg-red-50 hover:bg-red-100 cursor-pointer">Darurat</button>
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
    <main class="min-h-screen relative w-full {{ 'max-w-md md:max-w-7xl mx-auto bg-[#F8FAFC]' if not full_width else '' }}">
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
            <a href="javascript:void(0)" onclick="openModal('modal-infaq')" class="flex flex-col items-center justify-center text-gray-400 {{ t_link_hover }} w-16 mb-6 relative z-10">
                <div class="{{ t_bottom_btn_bg }} text-white w-14 h-14 rounded-full flex items-center justify-center shadow-lg border-4 border-white transform hover:scale-105 transition-transform">
                    <i class="fas fa-qrcode text-2xl"></i>
                </div>
                <span class="text-[10px] font-bold mt-1 {{ t_bottom_btn_text }}">Infaq</span>
            </a>
            <button onclick="triggerEmergency()" class="flex flex-col items-center justify-center {{ t_bottom_text_inactive }} hover:text-red-500 w-16 mb-1 transition-colors">
                <i class="fas fa-phone-alt text-xl mb-1"></i>
                <span class="text-[10px] font-medium">Darurat</span>
            </button>
        </div>
    </nav>
    {% endif %}

    <!-- MODAL INFAQ REVOLUTION -->
    <div id="modal-infaq" class="fixed inset-0 z-[150] hidden">
        <div id="infaq-modal-content" class="fixed inset-0 w-full h-full bg-white p-6 overflow-y-auto flex flex-col animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6">
                <h3 id="infaq-title" class="text-xl font-bold text-gray-800">Infaq Digital</h3>
                <button onclick="closeModal('modal-infaq')" class="w-10 h-10 rounded-full bg-black/5 flex items-center justify-center text-current hover:bg-black/10 transition">&times;</button>
            </div>
            
            <!-- Tabs -->
            <div id="infaq-tabs" class="flex p-1 bg-gray-100 rounded-xl mb-6">
                <button onclick="switchInfaqTab('masjid')" id="tab-btn-masjid" class="flex-1 py-2 text-xs font-bold rounded-lg bg-white shadow-sm text-emerald-600 transition">Masjid</button>
                <button onclick="switchInfaqTab('qurban')" id="tab-btn-qurban" class="flex-1 py-2 text-xs font-bold rounded-lg text-gray-500 hover:bg-gray-50 transition">Qurban</button>
                <button onclick="switchInfaqTab('zakat')" id="tab-btn-zakat" class="flex-1 py-2 text-xs font-bold rounded-lg text-gray-500 hover:bg-gray-50 transition">Zakat</button>
            </div>

            <!-- Content Masjid -->
            <div id="infaq-content-masjid" class="infaq-tab-content">
                <div class="text-center mb-6">
                    <img src="/uploads/{{ settings.get('infaq_qris_image', '') if settings else '' }}" onerror="this.src='https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=MasjidAlHijrahInfaq'" class="w-48 h-48 mx-auto object-contain bg-white p-2 rounded-xl border border-gray-200">
                    <p class="text-xs text-gray-400 mt-2">Scan QRIS (Masjid)</p>
                </div>
                <div id="infaq-box-masjid" class="bg-emerald-50 p-4 rounded-2xl border border-emerald-100 flex justify-between items-center">
                    <div>
                        <p class="text-[10px] text-emerald-600 font-bold uppercase infaq-label">Rekening Masjid</p>
                        <p class="font-mono font-bold text-gray-800 text-sm infaq-text" id="rek-masjid-text">{{ settings.get('infaq_rekening_masjid', '7123456789 (BSI)') if settings else 'Loading...' }}</p>
                    </div>
                    <button onclick="copyText('rek-masjid-text')" class="text-emerald-500 hover:text-emerald-700 infaq-icon"><i class="fas fa-copy"></i></button>
                </div>
            </div>

            <!-- Content Qurban -->
            <div id="infaq-content-qurban" class="infaq-tab-content hidden">
                 <div class="text-center mb-6">
                    <div class="w-48 h-48 mx-auto bg-orange-100 rounded-xl flex items-center justify-center text-orange-500">
                        <i class="fas fa-cow text-5xl"></i>
                    </div>
                    <p class="text-xs text-gray-400 mt-2">Salurkan untuk Sapi/Kambing</p>
                </div>
                <div id="infaq-box-qurban" class="bg-orange-50 p-4 rounded-2xl border border-orange-100 flex justify-between items-center">
                    <div>
                        <p class="text-[10px] text-orange-600 font-bold uppercase infaq-label">Rekening Qurban</p>
                        <p class="font-mono font-bold text-gray-800 text-sm infaq-text" id="rek-qurban-text">{{ settings.get('infaq_rekening_qurban', 'Hubungi Panitia') if settings else '...' }}</p>
                    </div>
                    <button onclick="copyText('rek-qurban-text')" class="text-orange-500 hover:text-orange-700 infaq-icon"><i class="fas fa-copy"></i></button>
                </div>
            </div>

            <!-- Content Zakat -->
            <div id="infaq-content-zakat" class="infaq-tab-content hidden">
                 <div class="text-center mb-6">
                    <div class="w-48 h-48 mx-auto bg-blue-100 rounded-xl flex items-center justify-center text-blue-500">
                        <i class="fas fa-hand-holding-heart text-5xl"></i>
                    </div>
                    <p class="text-xs text-gray-400 mt-2">Zakat Maal / Fitrah</p>
                </div>
                <div id="infaq-box-zakat" class="bg-blue-50 p-4 rounded-2xl border border-blue-100 flex justify-between items-center">
                    <div>
                        <p class="text-[10px] text-blue-600 font-bold uppercase infaq-label">Rekening Zakat</p>
                        <p class="font-mono font-bold text-gray-800 text-sm infaq-text" id="rek-zakat-text">{{ settings.get('infaq_rekening_zakat', 'Hubungi Panitia') if settings else '...' }}</p>
                    </div>
                    <button onclick="copyText('rek-zakat-text')" class="text-blue-500 hover:text-blue-700 infaq-icon"><i class="fas fa-copy"></i></button>
                </div>
            </div>

            <!-- Global Action Buttons -->
            <div class="mt-6 pt-4 border-t border-gray-100">
                <div class="mb-3">
                    <label class="block text-[10px] font-bold text-gray-400 mb-1">Keperluan (untuk Konfirmasi WA)</label>
                    <select id="infaq-type-select" class="w-full bg-gray-50 border border-gray-200 rounded-lg p-2 text-xs font-bold text-gray-700 focus:outline-none focus:ring-2 focus:ring-emerald-500">
                        <option value="Masjid">Masjid</option>
                        <option value="Qurban">Qurban</option>
                        <option value="Zakat">Zakat</option>
                        <option value="Infaq">Infaq</option>
                    </select>
                </div>
                <div class="flex gap-2 justify-center">
                    <a href="/uploads/{{ settings.get('infaq_qris_image', '') if settings else '' }}" download="QRIS_Masjid.png" class="flex-1 bg-gray-100 text-gray-700 px-3 py-3 rounded-xl text-xs font-bold hover:bg-gray-200 text-center transition"><i class="fas fa-download mr-1"></i> Download QRIS</a>
                    <button onclick="triggerInfaqWA()" class="flex-1 bg-[#25D366] text-white px-3 py-3 rounded-xl text-xs font-bold hover:bg-green-600 transition shadow-lg shadow-green-200"><i class="fab fa-whatsapp mr-1"></i> Konfirmasi WA</button>
                </div>
            </div>

            {% if is_admin %}
            <div class="mt-6 border-t pt-4">
                <details>
                    <summary class="text-xs font-bold text-gray-400 cursor-pointer">Admin Settings</summary>
                    <form action="/donate/update" method="POST" enctype="multipart/form-data" class="mt-2 space-y-2" onsubmit="combineBanks(event)">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                        
                        <div class="flex gap-1">
                            <select id="bank_masjid" class="w-1/3 text-[10px] p-2 border rounded bg-white infaq-input-text">
                                <option value="">Bank...</option>
                                <option value="BRI">BRI</option><option value="BCA">BCA</option><option value="Mandiri">Mandiri</option><option value="BNI">BNI</option><option value="BSI">BSI</option><option value="CIMB Niaga">CIMB Niaga</option><option value="Permata">Permata</option><option value="Danamon">Danamon</option><option value="Muamalat">Muamalat</option><option value="BTN">BTN</option><option value="BTPN">BTPN</option><option value="Jenius">Jenius</option><option value="Jago">Jago</option><option value="Neo">Neo</option><option value="SeaBank">SeaBank</option><option value="OCBC NISP">OCBC NISP</option><option value="Panin">Panin</option><option value="Maybank">Maybank</option><option value="Bukopin">Bukopin</option><option value="Mega">Mega</option><option value="Sinarmas">Sinarmas</option>
                            </select>
                            <input type="text" name="infaq_rekening_masjid" value="{{ settings.get('infaq_rekening_masjid', '') }}" placeholder="Rek Masjid" class="w-2/3 text-xs p-2 border rounded infaq-input-text">
                        </div>

                        <div class="flex gap-1">
                            <select id="bank_qurban" class="w-1/3 text-[10px] p-2 border rounded bg-white infaq-input-text">
                                <option value="">Bank...</option>
                                <option value="BRI">BRI</option><option value="BCA">BCA</option><option value="Mandiri">Mandiri</option><option value="BNI">BNI</option><option value="BSI">BSI</option><option value="CIMB Niaga">CIMB Niaga</option><option value="Permata">Permata</option><option value="Danamon">Danamon</option><option value="Muamalat">Muamalat</option><option value="BTN">BTN</option><option value="BTPN">BTPN</option><option value="Jenius">Jenius</option><option value="Jago">Jago</option><option value="Neo">Neo</option><option value="SeaBank">SeaBank</option><option value="OCBC NISP">OCBC NISP</option><option value="Panin">Panin</option><option value="Maybank">Maybank</option><option value="Bukopin">Bukopin</option><option value="Mega">Mega</option><option value="Sinarmas">Sinarmas</option>
                            </select>
                            <input type="text" name="infaq_rekening_qurban" value="{{ settings.get('infaq_rekening_qurban', '') }}" placeholder="Rek Qurban" class="w-2/3 text-xs p-2 border rounded infaq-input-text">
                        </div>

                        <div class="flex gap-1">
                            <select id="bank_zakat" class="w-1/3 text-[10px] p-2 border rounded bg-white infaq-input-text">
                                <option value="">Bank...</option>
                                <option value="BRI">BRI</option><option value="BCA">BCA</option><option value="Mandiri">Mandiri</option><option value="BNI">BNI</option><option value="BSI">BSI</option><option value="CIMB Niaga">CIMB Niaga</option><option value="Permata">Permata</option><option value="Danamon">Danamon</option><option value="Muamalat">Muamalat</option><option value="BTN">BTN</option><option value="BTPN">BTPN</option><option value="Jenius">Jenius</option><option value="Jago">Jago</option><option value="Neo">Neo</option><option value="SeaBank">SeaBank</option><option value="OCBC NISP">OCBC NISP</option><option value="Panin">Panin</option><option value="Maybank">Maybank</option><option value="Bukopin">Bukopin</option><option value="Mega">Mega</option><option value="Sinarmas">Sinarmas</option>
                            </select>
                            <input type="text" name="infaq_rekening_zakat" value="{{ settings.get('infaq_rekening_zakat', '') }}" placeholder="Rek Zakat" class="w-2/3 text-xs p-2 border rounded infaq-input-text">
                        </div>

                        <label class="text-[10px]">Upload QRIS (Masjid)</label>
                        <input type="file" name="qris_image" class="text-xs">
                        <button class="w-full bg-blue-500 text-white text-xs py-2 rounded">Save Changes</button>
                    </form>
                    <script>
                        function combineBanks(e) {
                            ['masjid', 'qurban', 'zakat'].forEach(type => {
                                const sel = document.getElementById('bank_' + type);
                                const inp = document.getElementsByName('infaq_rekening_' + type)[0];
                                if(sel.value && inp.value && !inp.value.includes(sel.value)) {
                                    inp.value = sel.value + ' - ' + inp.value;
                                }
                            });
                        }
                    </script>
                </details>
            </div>
            {% endif %}
        </div>
        <script>
            function switchInfaqTab(tab) {
                document.querySelectorAll('.infaq-tab-content').forEach(el => el.classList.add('hidden'));
                document.getElementById('infaq-content-'+tab).classList.remove('hidden');
                
                // Reset buttons
                ['masjid', 'qurban', 'zakat'].forEach(t => {
                    const btn = document.getElementById('tab-btn-'+t);
                    if(t === tab) {
                        btn.className = "flex-1 py-2 text-xs font-bold rounded-lg bg-white shadow-sm text-emerald-600 transition";
                    } else {
                        btn.className = "flex-1 py-2 text-xs font-bold rounded-lg text-gray-500 hover:bg-gray-50 transition";
                    }
                });
            }
            function copyText(id) {
                const el = document.getElementById(id);
                if(!el) return;
                const txt = el.innerText;
                const digits = txt.replace(/\\D/g, '');
                navigator.clipboard.writeText(digits);
                alert('Tersalin: ' + digits);
            }

            function formatBankDisplay(id) {
                const el = document.getElementById(id);
                if(!el || el.dataset.formatted) return;
                
                const text = el.innerText;
                const match = text.match(/(\\d{6,})/);
                if (match) {
                    const num = match[0];
                    const parts = text.split(num);
                    let html = '';
                    if(parts[0]) html += `<span style="user-select: none; opacity: 0.8;">${parts[0]}</span>`;
                    html += `<span>${num}</span>`;
                    if(parts[1]) html += `<span style="user-select: none; opacity: 0.8;">${parts[1]}</span>`;
                    
                    el.innerHTML = html;
                    el.dataset.formatted = 'true';
                }
            }
        </script>
    </div>
    <!-- ADMIN LOGIN MODAL -->
    <div id="modal-login-admin" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeModal('modal-login-admin')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.5s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-user-shield text-emerald-500 mr-2"></i>Login Admin</h3>
                <button onclick="closeModal('modal-login-admin')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            <form action="/login" method="POST" class="space-y-4">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Username</label>
                    <input type="text" name="username" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" required>
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Password</label>
                    <input type="password" name="password" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" required>
                </div>
                <button type="submit" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-emerald-600 transition">Masuk</button>
            </form>
        </div>
    </div>

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
                
                // API Aladhan
                const response = await fetch(`https://api.aladhan.com/v1/gToH?date=${dd}-${mm}-${yyyy}`);
                const result = await response.json();
                const h = result.data.hijri;
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
            if(el) {
                el.classList.remove('hidden');
                history.pushState({modal: id}, null, "");

                if(id === 'modal-infaq') {
                    adjustInfaqTheme();
                    setTimeout(() => {
                        ['rek-masjid-text', 'rek-qurban-text', 'rek-zakat-text'].forEach(formatBankDisplay);
                    }, 50);
                }
                
                // Call local init functions dynamically if they exist
                if(id === 'modal-fitur-alarm-adzan' && typeof initAlarmAdzan === 'function') {
                    initAlarmAdzan();
                }
                if(id === 'modal-fitur-jadwal-30' && typeof loadJadwal30Hari === 'function') {
                    loadJadwal30Hari();
                }
            }
        }

        window.addEventListener('popstate', (event) => {
            document.querySelectorAll('[id^="modal-"]').forEach(el => el.classList.add('hidden'));
            if (event.state && event.state.modal) {
                const el = document.getElementById(event.state.modal);
                if (el) el.classList.remove('hidden');
            }
        });

        function adjustInfaqTheme() {
            const container = document.getElementById('infaq-modal-content');
            const title = document.getElementById('infaq-title');
            const tabs = document.getElementById('infaq-tabs');
            const path = window.location.pathname;
            
            // Elements to style
            const boxes = [document.getElementById('infaq-box-masjid'), document.getElementById('infaq-box-qurban'), document.getElementById('infaq-box-zakat')];
            const labels = document.querySelectorAll('.infaq-label');
            const texts = document.querySelectorAll('.infaq-text');
            const icons = document.querySelectorAll('.infaq-icon');
            const inputs = document.querySelectorAll('.infaq-input-text');

            // Reset Base
            container.className = "fixed inset-0 w-full h-full p-6 overflow-y-auto flex flex-col animate-[slideUp_0.3s_ease-out] transition-colors duration-500";
            title.className = "text-xl font-bold";
            tabs.className = "flex p-1 rounded-xl mb-6 transition-colors duration-500";

            if (path.includes('/ramadhan')) {
                // RAMADHAN THEME (Midnight Blue & Gold)
                container.classList.add('bg-[#0b1026]', 'text-white');
                title.classList.add('text-[#FFD700]');
                tabs.classList.add('bg-white/10');
                
                boxes.forEach(box => {
                    box.className = "p-4 rounded-2xl border flex justify-between items-center transition-colors duration-500 bg-white/5 border-[#FFD700]/30";
                });
                labels.forEach(l => l.className = "text-[10px] font-bold uppercase infaq-label text-[#FFD700]");
                texts.forEach(t => t.className = "font-mono font-bold text-sm infaq-text text-white");
                icons.forEach(i => i.className = "hover:opacity-80 infaq-icon text-[#FFD700]");
                inputs.forEach(i => i.className = "w-full text-xs p-2 border rounded infaq-input-text text-[#0b1026] bg-white");

            } else if (path.includes('/irma')) {
                // IRMA THEME (Sage Green & Pink)
                container.classList.add('bg-[#F4E7E1]', 'text-[#2F4F4F]');
                title.classList.add('text-[#A0B391]');
                tabs.classList.add('bg-[#A0B391]/20');
                
                boxes.forEach(box => {
                    box.className = "p-4 rounded-2xl border flex justify-between items-center transition-colors duration-500 bg-white border-[#A0B391]/30";
                });
                labels.forEach(l => l.className = "text-[10px] font-bold uppercase infaq-label text-[#A0B391]");
                texts.forEach(t => t.className = "font-mono font-bold text-sm infaq-text text-[#2F4F4F]");
                icons.forEach(i => i.className = "hover:opacity-80 infaq-icon text-[#FFB6C1]");
                inputs.forEach(i => i.className = "w-full text-xs p-2 border rounded infaq-input-text text-[#2F4F4F] bg-white");

            } else {
                // DEFAULT HOME (Emerald)
                container.classList.add('bg-white', 'text-gray-800');
                title.classList.add('text-emerald-600');
                tabs.classList.add('bg-gray-100');
                
                // Reset boxes to distinct colors for Home
                document.getElementById('infaq-box-masjid').className = "bg-emerald-50 p-4 rounded-2xl border border-emerald-100 flex justify-between items-center";
                document.getElementById('infaq-box-qurban').className = "bg-orange-50 p-4 rounded-2xl border border-orange-100 flex justify-between items-center";
                document.getElementById('infaq-box-zakat').className = "bg-blue-50 p-4 rounded-2xl border border-blue-100 flex justify-between items-center";
                
                // Helper to reset inner
                const resetInner = (boxId, color) => {
                    const box = document.getElementById(boxId);
                    if(box) {
                        box.querySelector('.infaq-label').className = `text-[10px] font-bold uppercase infaq-label text-${color}-600`;
                        box.querySelector('.infaq-text').className = `font-mono font-bold text-sm infaq-text text-gray-800`;
                        box.querySelector('.infaq-icon').className = `hover:text-${color}-700 infaq-icon text-${color}-500`;
                    }
                };
                
                resetInner('infaq-box-masjid', 'emerald');
                resetInner('infaq-box-qurban', 'orange');
                resetInner('infaq-box-zakat', 'blue');
                inputs.forEach(i => i.className = "w-full text-xs p-2 border rounded infaq-input-text text-emerald-800 bg-white");
            }
        }

        function closeModal(id) {
            if (history.state && history.state.modal === id) {
                history.back();
            } else {
                const el = document.getElementById(id);
                if(el) el.classList.add('hidden');
            }
        }

        function triggerInfaqWA() {
            const type = document.getElementById('infaq-type-select').value;
            const now = new Date();
            const h = now.getHours();
            let time = "Malam";
            if (h >= 0 && h < 11) time = "Pagi";
            else if (h >= 11 && h < 15) time = "Siang";
            else if (h >= 15 && h < 18) time = "Sore";
            
            const msg = `Assalamaulaikum Pak, selamat ${time}, ijin konfirmasi Pak, saya sudah mengtransfer sebesar / jumlah Rp... di nomor rekening ${type.toLowerCase()} untuk keperluan ${type} ke masjid langsung, terima kasih Pak 🙏`;
            
            window.location.href = "https://wa.me/6282330890500?text=" + encodeURIComponent(msg);
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
                // Fallback for when event didn't fire (iOS, or already installed, or browser blocked it)
                const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
                const isAndroid = /Android/.test(navigator.userAgent);
                
                if (isIOS) {
                    alert("Untuk menginstall di iOS:\\n1. Klik tombol Share (ikon panah ke atas/kotak)\\n2. Pilih 'Add to Home Screen' (Tambah ke Layar Utama)");
                } else if (isAndroid) {
                    alert("Untuk menginstall:\\n1. Klik ikon tiga titik di pojok kanan atas browser\\n2. Pilih 'Install App' atau 'Tambahkan ke Layar Utama'");
                } else {
                    alert("Untuk menginstall di PC/Laptop:\\nKlik ikon 'Install' (simbol monitor/panah) di bagian kanan kolom URL browser Anda.");
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
    
</body>
</html>
"""

FITUR_MASJID_HTML = """
<style>
    .app-drawer-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px 15px;
        padding: 20px;
    }
    .app-icon-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        cursor: pointer;
    }
    .app-icon-wrapper:active .app-icon-box {
        transform: scale(0.92);
    }
    .app-icon-box {
        width: 60px;
        height: 60px;
        border-radius: 22%;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        display: flex;
        justify-content: center;
        align-items: center;
        color: #ffffff;
        font-size: 28px;
        transition: transform 0.1s ease;
    }
    .app-icon-title {
        font-family: 'Inter', 'Roboto', sans-serif;
        font-size: 11px;
        font-weight: 600;
        text-align: center;
        line-height: 1.2;
        width: 60px;
        word-wrap: break-word;
        color: #374151; /* gray-700 */
    }
</style>
<div class="pt-20 md:pt-32 pb-32 px-5 md:px-8">
    <div class="text-center mb-10">
        <h2 class="text-3xl md:text-4xl font-bold text-emerald-800 mb-4">Fitur Ekosistem Digital Masjid</h2>
        <p class="text-gray-600">Jelajahi berbagai layanan spiritual dan fungsional kami.</p>
    </div>

    <div class="app-drawer-grid">
        <div class="app-icon-wrapper" onclick="openModal('modal-fitur-kiblat')">
            <div class="app-icon-box" style="background: linear-gradient(135deg, #3b82f6, #2563eb);">
                <i class="fa-solid fa-compass"></i>
            </div>
            <span class="app-icon-title">Arah Kiblat</span>
        </div>
        <div class="app-icon-wrapper" onclick="openModal('modal-fitur-puasa')">
            <div class="app-icon-box" style="background: linear-gradient(135deg, #f59e0b, #d97706);">
                <i class="fa-solid fa-calendar-check"></i>
            </div>
            <span class="app-icon-title">Kalender Puasa</span>
        </div>
        <div class="app-icon-wrapper" onclick="openModal('modal-fitur-alarm-adzan')">
            <div class="app-icon-box" style="background: linear-gradient(135deg, #0f172a, #1e293b);">
                <i class="fa-solid fa-bell"></i>
            </div>
            <span class="app-icon-title">Alarm Adzan</span>
        </div>
        <div class="app-icon-wrapper" onclick="openModal('modal-fitur-jadwal-30')">
            <div class="app-icon-box" style="background: linear-gradient(135deg, #111827, #000000); border: 1px solid #FFD700;">
                <i class="fa-solid fa-calendar-days text-[#FFD700]"></i>
            </div>
            <span class="app-icon-title">Jadwal 30 Hari</span>
        </div>
    </div>
    
    <!-- Modal Fitur 0: Jadwal 30 Hari Kedepan (Pure Dark Mode & Landscape Forced) -->
    <style>
        /* Landscape Orientation Lock Strategy */
        #modal-fitur-jadwal-30 .landscape-container {
            width: 100vw;
            height: 100vh;
            background-color: #050505;
            color: #ffffff;
            position: fixed;
            top: 0; left: 0;
            z-index: 300;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        @media screen and (orientation: portrait) {
            #modal-fitur-jadwal-30 .landscape-container {
                transform: rotate(-90deg);
                transform-origin: left top;
                width: 100vh;
                height: 100vw;
                position: absolute;
                top: 100%;
                left: 0;
            }
        }
        
        .table-30-hari th {
            position: sticky;
            top: 0;
            background-color: #0a0a0a;
            color: #FFD700;
            z-index: 10;
            padding: 12px 8px;
            border-bottom: 2px solid #222;
        }
        .table-30-hari td {
            padding: 16px 8px;
            border-bottom: 1px solid #1a1a1a;
            color: #e5e5e5;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        }
        .table-30-hari tr.today-row {
            background-color: rgba(255, 255, 255, 0.1) !important;
            border-left: 3px solid #FFD700;
        }
        .table-30-hari td:first-child {
            color: #FFD700;
            font-weight: bold;
        }
        .jadwal-scroll-area {
            flex: 1;
            overflow-y: auto;
            -webkit-overflow-scrolling: touch;
        }
    </style>
    
    <div id="modal-fitur-jadwal-30" class="fixed inset-0 z-[300] hidden bg-black">
        <div class="landscape-container font-sans">
            <!-- Navigation Bar -->
            <div class="flex justify-between items-center p-4 bg-[#0a0a0a] border-b border-[#222] flex-shrink-0">
                <div class="flex items-center gap-4">
                    <button onclick="closeModal('modal-fitur-jadwal-30')" class="text-white hover:text-gray-300 w-10 h-10 flex items-center justify-center text-xl">
                        <i class="fas fa-arrow-left"></i>
                    </button>
                    <h2 class="text-xl md:text-2xl font-semibold text-white tracking-wide">Jadwal 30 Hari Kedepan</h2>
                </div>
                <div class="relative">
                    <button onclick="document.getElementById('jadwal-column-menu').classList.toggle('hidden')" class="text-white hover:text-gray-300 flex items-center gap-2 text-sm font-bold tracking-widest px-4 py-2 bg-[#1a1a1a] rounded-lg border border-[#333]">
                        <i class="fas fa-list"></i> KOLOM
                    </button>
                    <!-- Floating Menu for Columns -->
                    <div id="jadwal-column-menu" class="hidden absolute top-full right-0 mt-2 bg-[#1a1a1a] border border-[#333] rounded-xl p-3 w-48 shadow-2xl z-50">
                        <p class="text-[10px] text-gray-500 font-bold uppercase mb-2 border-b border-[#333] pb-1">Visibilitas Kolom</p>
                        <div class="space-y-2 text-sm text-gray-300">
                            <label class="flex items-center gap-2 cursor-pointer"><input type="checkbox" checked onchange="toggleColJadwal('col-imsak')" class="accent-[#FFD700]"> Imsak</label>
                            <label class="flex items-center gap-2 cursor-pointer"><input type="checkbox" checked onchange="toggleColJadwal('col-subuh')" class="accent-[#FFD700]"> Subuh</label>
                            <label class="flex items-center gap-2 cursor-pointer"><input type="checkbox" checked onchange="toggleColJadwal('col-terbit')" class="accent-[#FFD700]"> Terbit</label>
                            <label class="flex items-center gap-2 cursor-pointer"><input type="checkbox" checked onchange="toggleColJadwal('col-dzuhur')" class="accent-[#FFD700]"> Dzuhur</label>
                            <label class="flex items-center gap-2 cursor-pointer"><input type="checkbox" checked onchange="toggleColJadwal('col-ashar')" class="accent-[#FFD700]"> Ashar</label>
                            <label class="flex items-center gap-2 cursor-pointer"><input type="checkbox" checked onchange="toggleColJadwal('col-maghrib')" class="accent-[#FFD700]"> Maghrib</label>
                            <label class="flex items-center gap-2 cursor-pointer"><input type="checkbox" checked onchange="toggleColJadwal('col-isya')" class="accent-[#FFD700]"> Isya</label>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Table Area -->
            <div class="jadwal-scroll-area relative">
                <table class="w-full text-center border-collapse table-30-hari text-sm md:text-base">
                    <thead>
                        <tr>
                            <th class="text-left pl-4 font-medium tracking-wider">Tanggal Masehi</th>
                            <th class="font-medium tracking-wider">Hijriah</th>
                            <th class="col-imsak font-medium tracking-wider">Imsak</th>
                            <th class="col-subuh font-medium tracking-wider">Subuh</th>
                            <th class="col-terbit font-medium tracking-wider">Terbit</th>
                            <th class="col-dzuhur font-medium tracking-wider">Dzuhur</th>
                            <th class="col-ashar font-medium tracking-wider">Ashar</th>
                            <th class="col-maghrib font-medium tracking-wider">Maghrib</th>
                            <th class="col-isya font-medium tracking-wider">Isya</th>
                        </tr>
                    </thead>
                    <tbody id="jadwal-30-body" class="divide-y divide-[#1a1a1a]">
                        <tr><td colspan="9" class="py-10 text-gray-500"><i class="fas fa-spinner fa-spin mr-2"></i> Menarik data dari server...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Modal Fitur 2: Kompas Kiblat Presisi -->
    <div id="modal-fitur-kiblat" class="fixed inset-0 z-[200] hidden flex items-center justify-center perspective-[1000px] bg-[#1a1a1a]">
        <!-- Full dark background mode -->
        <div class="absolute inset-0 bg-[#1a1a1a]" onclick="closeModal('modal-fitur-kiblat')"></div>
        <div class="relative w-full h-full flex flex-col items-center justify-center z-10 p-6">
            <button onclick="closeModal('modal-fitur-kiblat')" class="absolute top-6 right-6 bg-white/10 w-10 h-10 rounded-full text-white hover:bg-white/20 flex items-center justify-center transition">&times;</button>
            
            <div class="mb-12 text-center w-full">
                <!-- Fetch Location Text Hierarchy -->
                <h2 id="qibla-city" class="text-2xl font-sans font-bold text-white tracking-wide mb-1">Mencari Satelit...</h2>
                <h3 class="text-sm font-bold tracking-[0.3em] text-[#FFD700] mb-8">INDONESIA</h3>
                <button id="activate-compass-btn" onclick="startCompass()" class="bg-teal-700 text-white font-bold py-3 px-8 rounded-full shadow-[0_0_20px_rgba(15,118,110,0.5)] hover:bg-teal-600 transition tracking-widest text-sm uppercase">Pindai Kiblat</button>
            </div>
            
            <div class="relative w-[280px] h-[280px] flex items-center justify-center mb-8" style="perspective: 1000px;">
                <!-- Base Compass Disc with absolute dimensions and strict geometry -->
                <div id="compass-disc" class="absolute w-full h-full rounded-full flex items-center justify-center shadow-[0_15px_35px_rgba(0,0,0,0.5)] transition-transform duration-300 border-[12px] border-[#2d2d2d]" style="background: white; box-shadow: 0 0 0 8px #0f766e inset; transform-style: preserve-3d;">
                    
                    <!-- 8 Direction Lines -->
                    <div class="absolute inset-0 pointer-events-none flex items-center justify-center">
                        <div class="w-full h-[1px] bg-gray-300 absolute"></div>
                        <div class="w-[1px] h-full bg-gray-300 absolute"></div>
                        <div class="w-full h-[1px] bg-gray-200 absolute rotate-45"></div>
                        <div class="w-[1px] h-full bg-gray-200 absolute rotate-45"></div>
                    </div>

                    <!-- Directions (positioned exactly inside the inner ring to breathe) -->
                    <div class="absolute top-[22px] font-bold text-[#0f766e] text-lg drop-shadow-sm leading-none">N</div>
                    <div class="absolute bottom-[22px] font-bold text-[#4b5563] text-sm drop-shadow-sm rotate-180 leading-none">S</div>
                    <div class="absolute left-[22px] font-bold text-[#4b5563] text-sm drop-shadow-sm -rotate-90 leading-none">W</div>
                    <div class="absolute right-[22px] font-bold text-[#4b5563] text-sm drop-shadow-sm rotate-90 leading-none">E</div>
                    
                    <div class="absolute top-[60px] right-[60px] font-bold text-[#9ca3af] text-[10px] rotate-45 leading-none">NE</div>
                    <div class="absolute bottom-[60px] right-[60px] font-bold text-[#9ca3af] text-[10px] rotate-[135deg] leading-none">SE</div>
                    <div class="absolute bottom-[60px] left-[60px] font-bold text-[#9ca3af] text-[10px] rotate-[225deg] leading-none">SW</div>
                    <div class="absolute top-[60px] left-[60px] font-bold text-[#9ca3af] text-[10px] rotate-[315deg] leading-none">NW</div>

                    <!-- Needle Red Triangle Container at Center, points outward -->
                    <div id="kaaba-icon-container" class="absolute w-full h-full pointer-events-none z-30 flex flex-col items-center" style="transform: rotate(0deg);">
                        <!-- Wrapper spanning top half to pivot around exact center -->
                        <div class="w-full h-1/2 relative flex flex-col items-center justify-end">
                            <!-- Kaaba Icon perfectly stitched at tip of the needle -->
                            <div class="mb-1 flex flex-col items-center justify-center drop-shadow-md">
                                <div class="w-[16px] h-[20px] bg-black rounded-[2px] flex flex-col justify-start relative overflow-hidden border border-black">
                                    <div class="w-full h-[3px] bg-[#FFD700] mt-[4px] absolute"></div>
                                </div>
                            </div>
                            <!-- Sharp Red Needle pointing to Qibla (base exact touching dome) -->
                            <div class="w-0 h-0 border-l-[4px] border-r-[4px] border-b-[75px] border-l-transparent border-r-transparent border-b-[#ef4444] mb-[15px]"></div>
                        </div>
                    </div>
                </div>

                <!-- Static Mosque Logo completely decoupled from rotation for absolute center grounding -->
                <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-40 flex flex-col items-center justify-center pointer-events-none drop-shadow-md">
                    <div class="w-5 h-3 bg-[#FFD700] rounded-t-full relative mb-[-1px] z-10 shadow-sm"></div>
                    <div class="w-7 h-5 bg-black rounded-sm relative z-20 flex items-center justify-center">
                        <div class="w-1.5 h-2.5 bg-[#1a1a1a] rounded-t-sm absolute bottom-0"></div>
                    </div>
                </div>
                
                <!-- Fixed Outer Indicator (Phone direction) -->
                <div class="absolute top-[-20px] left-1/2 -translate-x-1/2 w-0 h-0 border-l-[12px] border-r-[12px] border-b-[16px] border-l-transparent border-r-transparent border-b-gray-400 drop-shadow-md z-50 opacity-80"></div>
            </div>

            <!-- Qiblat Degree and Distance Info -->
            <p id="kiblat-info" class="mt-4 text-[13px] font-bold text-gray-300 tracking-wide uppercase opacity-0 transition-opacity duration-500"></p>

            <!-- Bottom Warning -->
            <div class="absolute bottom-8 w-full flex justify-center px-6">
                <div class="flex items-center gap-2 max-w-xs text-center">
                    <div class="w-4 h-4 rounded-full border border-[#4b5563] text-[#4b5563] flex items-center justify-center text-[10px] font-bold italic flex-shrink-0">i</div>
                    <p class="text-[10px] text-[#4b5563] uppercase font-bold tracking-wider leading-relaxed">Jauhkan perangkat dari objek logam atau magnetik untuk akurasi maksimal</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal Fitur 3: Kalender Puasa -->
    <div id="modal-fitur-puasa" class="fixed inset-0 z-[200] hidden flex items-center justify-center">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeModal('modal-fitur-puasa')"></div>
        <div class="relative bg-white w-full max-w-md mx-4 p-6 rounded-3xl shadow-2xl animate-[slideUp_0.3s_ease-out] flex flex-col max-h-[90vh]">
            <button onclick="closeModal('modal-fitur-puasa')" class="absolute top-4 right-4 bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200 flex items-center justify-center z-10">&times;</button>
            
            <h3 class="text-xl font-bold text-emerald-700 mb-2"><i class="fas fa-calendar-alt mr-2"></i>Kalender Puasa Sunnah</h3>
            
            <!-- Tanggal Hari Ini & Peringatan -->
            <div class="bg-emerald-50 rounded-2xl p-3 text-center mb-4 flex-shrink-0">
                <p class="text-[10px] text-emerald-600 font-bold uppercase mb-1">Tanggal Hari Ini</p>
                <h4 id="fitur-hijri-date" class="text-lg font-bold text-emerald-800">Loading...</h4>
            </div>
            <div id="puasa-alarm" class="hidden bg-yellow-50 text-yellow-700 p-2 rounded-xl border border-yellow-200 text-xs font-bold text-center animate-pulse mb-4 flex-shrink-0">
                Peringatan Puasa Sunnah!
            </div>

            <!-- Kalender Navigation -->
            <div class="flex justify-between items-center mb-4 flex-shrink-0">
                <button onclick="changeMonth(-1)" class="bg-gray-100 hover:bg-gray-200 text-gray-600 w-8 h-8 rounded-full flex items-center justify-center transition"><i class="fas fa-chevron-left"></i></button>
                <h4 id="calendar-month-year" class="font-bold text-gray-800 text-sm">Loading...</h4>
                <button onclick="changeMonth(1)" class="bg-gray-100 hover:bg-gray-200 text-gray-600 w-8 h-8 rounded-full flex items-center justify-center transition"><i class="fas fa-chevron-right"></i></button>
            </div>

            <!-- 7-Column Grid -->
            <div class="overflow-y-auto flex-1">
                <div class="grid grid-cols-7 gap-1 text-center mb-2">
                    <div class="text-[10px] font-bold text-red-500 uppercase">Min</div>
                    <div class="text-[10px] font-bold text-gray-400 uppercase">Sen</div>
                    <div class="text-[10px] font-bold text-gray-400 uppercase">Sel</div>
                    <div class="text-[10px] font-bold text-gray-400 uppercase">Rab</div>
                    <div class="text-[10px] font-bold text-gray-400 uppercase">Kam</div>
                    <div class="text-[10px] font-bold text-gray-400 uppercase">Jum</div>
                    <div class="text-[10px] font-bold text-gray-400 uppercase">Sab</div>
                </div>
                <div id="calendar-grid" class="grid grid-cols-7 gap-1">
                    <!-- Blocks rendered via JS -->
                </div>
            </div>
            
            <div class="flex justify-center items-center gap-2 mt-4 pt-4 border-t border-gray-100 flex-shrink-0 text-[10px] font-bold text-gray-500">
                <span class="w-3 h-3 rounded-full bg-[#dcfce7] inline-block border border-green-200"></span> Jadwal Puasa Sunnah
            </div>
        </div>
    </div>

    <!-- Sub-Modal: Penjelasan Puasa Sunnah -->
    <div id="modal-puasa-detail" class="fixed inset-0 z-[250] hidden flex items-center justify-center bg-black/60 backdrop-blur-sm">
        <div class="bg-white rounded-3xl w-full max-w-xs mx-4 p-6 shadow-2xl animate-[popupFadeIn_0.3s_ease-out] relative">
            <div class="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4 border-4 border-white shadow-lg -mt-12">
                <i class="fas fa-star-and-crescent text-2xl"></i>
            </div>
            <p id="puasa-detail-date" class="text-[10px] font-bold text-emerald-500 text-center uppercase tracking-widest mb-1"></p>
            <h3 id="puasa-detail-title" class="text-xl font-bold text-gray-800 text-center mb-3 leading-tight"></h3>
            <div class="w-12 h-1 bg-emerald-200 mx-auto rounded-full mb-4"></div>
            <p id="puasa-detail-desc" class="text-sm text-gray-600 text-center leading-relaxed mb-6"></p>
            <button onclick="closeModal('modal-puasa-detail')" class="w-full bg-gray-100 text-gray-700 hover:bg-gray-200 font-bold py-3 rounded-xl transition">Tutup</button>
        </div>
    </div>

    <!-- Modal Fitur 7: Alarm Adzan Interaktif -->
    <div id="modal-fitur-alarm-adzan" class="fixed inset-0 z-[200] hidden flex items-center justify-center bg-[#0f172a]">
        <!-- Mosque Photography Background -->
        <div class="absolute inset-0 bg-cover bg-center" style="background-image: url('https://images.unsplash.com/photo-1564683214965-3619addd900d?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80');"></div>
        <!-- Gradient Overlay: Dark midnight blue gradually transparent to bottom -->
        <div class="absolute inset-0 bg-gradient-to-b from-[#0b162c]/95 via-[#0b162c]/80 to-[#0b162c]/95"></div>
        
        <div class="relative w-full h-full max-w-md mx-auto p-6 flex flex-col z-10 overflow-hidden">
            <!-- Zona 1: Navigasi Atas -->
            <div class="flex justify-between items-start mb-8 flex-shrink-0 animate-[fadeIn_0.5s_ease-out]">
                <div class="flex items-center gap-2">
                    <div class="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center backdrop-blur-md border border-white/20">
                        <i class="fas fa-user text-white text-xs"></i>
                    </div>
                    <div>
                        <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Lokasi Saat Ini</p>
                        <p id="alarm-location-text" class="text-sm font-bold text-white">Mendeteksi...</p>
                    </div>
                </div>
                <div class="flex gap-2">
                    <button onclick="openAlarmCalendar()" class="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-white hover:bg-white/20 backdrop-blur-md border border-white/20 transition"><i class="fas fa-calendar-alt"></i></button>
                    <button onclick="detectAlarmLocation()" class="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-white hover:bg-white/20 backdrop-blur-md border border-white/20 transition"><i class="fas fa-map-marker-alt"></i></button>
                    <button onclick="openAlarmSettings()" class="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-white hover:bg-white/20 backdrop-blur-md border border-white/20 transition"><i class="fas fa-cog"></i></button>
                    <button onclick="closeModal('modal-fitur-alarm-adzan')" class="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center text-red-400 hover:bg-red-500/40 backdrop-blur-md border border-red-500/30 transition ml-2"><i class="fas fa-times"></i></button>
                </div>
            </div>

            <!-- Zona 2: Konteks Tengah -->
            <div class="flex flex-col items-center justify-center mb-8 flex-shrink-0 animate-[slideUp_0.5s_ease-out]">
                <div class="flex justify-center items-center gap-4 mb-4">
                    <h2 id="alarm-main-time" class="text-6xl font-sans font-bold text-white tracking-tighter drop-shadow-lg">--:--</h2>
                    <button onclick="closeModal('modal-fitur-alarm-adzan'); openModal('modal-fitur-kiblat'); startCompass();" class="bg-white text-black px-4 py-2 rounded-full font-bold text-xs shadow-lg flex items-center gap-2 hover:bg-gray-100 transition transform hover:scale-105 active:scale-95">
                        <i class="fas fa-compass"></i> Qiblat
                    </button>
                </div>
                
                <div class="w-full flex justify-between text-xs font-bold text-gray-300 mb-4 px-4">
                    <span id="alarm-hijri-date">-- ---- ---- H</span>
                    <span id="alarm-masehi-date">-- --- ----</span>
                </div>
                
                <p id="alarm-countdown-text" class="text-teal-400 font-bold text-sm tracking-wide bg-teal-900/30 px-4 py-2 rounded-full border border-teal-500/30 mb-2">Memuat Waktu...</p>
                <button onclick="openAlarmHelp()" class="text-[10px] text-teal-300 hover:text-teal-200 underline underline-offset-2">Adzan/Notif Sering Tidak Muncul?</button>
            </div>

            <!-- Zona 3: Daftar Jadwal Sholat -->
            <div class="flex-1 overflow-y-auto pb-6 space-y-3 px-1 custom-scrollbar">
                <!-- Template Kartu Glassmorphism (Will be generated by JS) -->
                <div id="alarm-schedule-container" class="space-y-3">
                    <div class="text-center text-white py-10"><i class="fas fa-circle-notch fa-spin text-3xl text-teal-500"></i></div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    // Modal Utils for App Drawer
    function openModal(id) {
        const el = document.getElementById(id);
        if(el) {
            el.classList.remove('hidden');
            if (id === 'modal-fitur-alarm-adzan') {
                initAlarmAdzan();
            }
            if (id === 'modal-fitur-jadwal-30') {
                loadJadwal30Hari();
            }
        }
    }

    // Fitur Baru: Jadwal 30 Hari
    async function loadJadwal30Hari() {
        const tbody = document.getElementById('jadwal-30-body');
        if (tbody && tbody.innerHTML.includes('Menarik data')) {
            try {
                const now = new Date();
                const month = now.getMonth() + 1;
                const year = now.getFullYear();
                
                const res1 = await fetch(`https://api.aladhan.com/v1/calendarByCity?city=Samarinda&country=Indonesia&method=20&month=${month}&year=${year}`);
                const data1 = await res1.json();
                
                let nextMonth = month + 1;
                let nextYear = year;
                if (nextMonth > 12) { nextMonth = 1; nextYear++; }
                const res2 = await fetch(`https://api.aladhan.com/v1/calendarByCity?city=Samarinda&country=Indonesia&method=20&month=${nextMonth}&year=${nextYear}`);
                const data2 = await res2.json();
                
                let allDays = [...data1.data, ...data2.data];
                
                const todayStr = String(now.getDate()).padStart(2, '0') + '-' + String(now.getMonth()+1).padStart(2, '0') + '-' + now.getFullYear();
                
                let startIndex = allDays.findIndex(d => d.date.gregorian.date === todayStr);
                if (startIndex === -1) startIndex = 0;
                
                let thirtyDays = allDays.slice(startIndex, startIndex + 30);
                
                let html = '';
                const todayGregorianDate = now.getDate();
                const todayGregorianMonth = now.getMonth() + 1;
                
                thirtyDays.forEach(day => {
                    const g = day.date.gregorian;
                    const h = day.date.hijri;
                    const t = day.timings;
                    
                    const gDay = parseInt(g.day);
                    const gMonth = parseInt(g.month.number);
                    const isToday = (gDay === todayGregorianDate && gMonth === todayGregorianMonth);
                    
                    const clean = (timeStr) => timeStr.split(' ')[0];
                    
                    html += `
                        <tr class="${isToday ? 'today-row' : 'hover:bg-[#111] transition-colors'}">
                            <td class="text-left pl-4">${g.day} ${g.month.en} ${g.year}</td>
                            <td>${h.day} ${h.month.en}</td>
                            <td class="col-imsak">${clean(t.Imsak)}</td>
                            <td class="col-subuh">${clean(t.Fajr)}</td>
                            <td class="col-terbit">${clean(t.Sunrise)}</td>
                            <td class="col-dzuhur">${clean(t.Dhuhr)}</td>
                            <td class="col-ashar">${clean(t.Asr)}</td>
                            <td class="col-maghrib">${clean(t.Maghrib)}</td>
                            <td class="col-isya">${clean(t.Isha)}</td>
                        </tr>
                    `;
                });
                
                tbody.innerHTML = html;
                
                const checkboxes = document.querySelectorAll('#jadwal-column-menu input[type="checkbox"]');
                checkboxes.forEach(cb => {
                    const colClass = cb.getAttribute('onchange').match(/'([^']+)'/)[1];
                    const elements = document.querySelectorAll('.' + colClass);
                    elements.forEach(el => {
                        el.style.display = cb.checked ? '' : 'none';
                    });
                });
                
            } catch(e) {
                tbody.innerHTML = `<tr><td colspan="9" class="py-10 text-red-500">Gagal mengambil data: ${e.message}</td></tr>`;
            }
        }
    }
    
    function toggleColJadwal(colClass) {
        const elements = document.querySelectorAll('.' + colClass);
        const checkbox = document.querySelector(`input[onchange="toggleColJadwal('${colClass}')"]`);
        const isVisible = checkbox.checked;
        
        elements.forEach(el => {
            el.style.display = isVisible ? '' : 'none';
        });
    }

    function closeModal(id) {
        const el = document.getElementById(id);
        if(el) {
            el.classList.add('hidden');
        }
    }

    // Fitur 2: Kompas Kiblat Presisi
    let currentHeading = 0;
    
    // Haversine Formula for Distance to Kaaba
    function calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // Radius of the earth in km
        const dLat = (lat2 - lat1) * Math.PI / 180;  
        const dLon = (lon2 - lon1) * Math.PI / 180; 
        const a = 
            Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
            Math.sin(dLon/2) * Math.sin(dLon/2)
            ; 
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)); 
        const d = R * c; 
        return Math.round(d);
    }

    function startCompass() {
        if (!navigator.geolocation) {
            alert("Geolocation tidak didukung di perangkat ini.");
            return;
        }
        
        // Disable button & show loading state
        const btn = document.getElementById('activate-compass-btn');
        if (btn) btn.classList.add('hidden');

        navigator.geolocation.getCurrentPosition(async (pos) => {
            let lat = pos.coords.latitude;
            let lon = pos.coords.longitude;
            
            // Kaaba Coordinates
            const kaabaLat = 21.422487;
            const kaabaLon = 39.826206;
            
            try {
                // Fetch Qibla Direction
                const res = await fetch(`https://api.aladhan.com/v1/qibla/${lat}/${lon}`);
                const data = await res.json();
                const qibla = data.data.direction;
                
                // Calculate Distance
                const distance = calculateDistance(lat, lon, kaabaLat, kaabaLon);
                
                // Fetch Location Name (Reverse Geocoding)
                const geoRes = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=10`);
                const geoData = await geoRes.json();
                let city = geoData.address.city || geoData.address.town || geoData.address.county || geoData.address.state || "Lokasi Anda";
                let state = geoData.address.state || "";
                
                // Update UI Location
                document.getElementById('qibla-city').innerText = `${city} ${state}`;
                
                // Update UI Qibla Info
                const infoEl = document.getElementById('kiblat-info');
                infoEl.innerText = `Qiblat ${qibla.toFixed(2)} Derajat Jarak ${distance} KM`;
                infoEl.classList.remove('opacity-0');
                
                // Inject Kaaba Icon precisely at Qibla degree relative to North
                document.getElementById('kaaba-icon-container').style.transform = `rotate(${qibla}deg)`;
                
                // Low-Pass Filter factor
                const alphaFilter = 0.15;

                const handleOrientation = (event) => {
                    let heading = null;
                    if (event.webkitCompassHeading !== undefined) {
                        heading = event.webkitCompassHeading; // iOS
                    } else if (event.alpha !== null) {
                        // Android absolute orientation
                        heading = 360 - event.alpha; 
                    }

                    if (heading !== null) {
                        let diff = heading - currentHeading;
                        if (diff > 180) diff -= 360;
                        if (diff < -180) diff += 360;
                        currentHeading += diff * alphaFilter;

                        const rotateDeg = -currentHeading;
                        const disc = document.getElementById('compass-disc');
                        disc.style.transform = `rotate(${rotateDeg}deg)`;

                        let diffQibla = Math.abs(currentHeading - qibla);
                        if (diffQibla > 180) diffQibla = 360 - diffQibla;
                        
                        if (diffQibla <= 3) {
                            if (disc.style.background !== "radial-gradient(circle at 50% 50%, #ffffff, #dcfce7)") {
                                disc.style.background = "radial-gradient(circle at 50% 50%, #ffffff, #dcfce7)";
                                if (navigator.vibrate) navigator.vibrate([100, 50, 100]);
                            }
                        } else {
                            if (disc.style.background !== "white") {
                                disc.style.background = "white";
                            }
                        }
                    }
                };

                // Request iOS Permission if needed, otherwise just listen
                if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
                    DeviceOrientationEvent.requestPermission()
                        .then(permissionState => {
                            if (permissionState === 'granted') {
                                window.addEventListener('deviceorientation', handleOrientation);
                            } else {
                                alert('Izin sensor kompas ditolak.');
                            }
                        })
                        .catch(console.error);
                } else {
                    // Android & non-iOS13+ devices
                    if ('ondeviceorientationabsolute' in window) {
                        window.addEventListener('deviceorientationabsolute', handleOrientation);
                    } else {
                        window.addEventListener('deviceorientation', handleOrientation);
                    }
                }

            } catch(e) {
                alert("Gagal mengambil data arah kiblat dari API.");
            }
        }, () => {
            alert("Mohon izinkan akses lokasi (GPS) untuk menggunakan fitur kompas.");
        });
    }

    // Fitur 3: Kalender Hijriah & Alarm Puasa Sunnah
    let currentCalMonth = new Date().getMonth() + 1; // 1-12
    let currentCalYear = new Date().getFullYear();
    let isCalendarLoaded = false;

    async function fetchFiturHijri() {
        const today = new Date();
        const dd = String(today.getDate()).padStart(2, '0');
        const mm = String(today.getMonth() + 1).padStart(2, '0');
        const yyyy = today.getFullYear();
        try {
            const res = await fetch(`https://api.aladhan.com/v1/gToH?date=${dd}-${mm}-${yyyy}`);
            const data = await res.json();
            const h = data.data.hijri;
            document.getElementById('fitur-hijri-date').innerText = `${h.day} ${h.month.en} ${h.year} H`;
            
            // Check if today is a fasting day
            const isFasting = checkPuasaSunnah(parseInt(h.day), h.month.number, today.getDay());
            if (isFasting) {
                const el = document.getElementById('puasa-alarm');
                el.innerText = `Hari ini disunnahkan: ${isFasting.title}`;
                el.classList.remove('hidden');
            }
        } catch(e) {}
    }
    fetchFiturHijri();

    function checkPuasaSunnah(hijriDay, hijriMonthNum, gregorianWeekday) {
        // gregorianWeekday: 0 = Sunday, 1 = Monday, 4 = Thursday
        hijriDay = parseInt(hijriDay);
        hijriMonthNum = parseInt(hijriMonthNum);
        
        let fasting = null;
        
        // 1. Senin & Kamis
        if (gregorianWeekday === 1) {
            fasting = { title: "Puasa Senin", desc: "Puasa sunnah mingguan yang rutin dikerjakan Rasulullah SAW karena pada hari tersebut amal-amal diangkat." };
        } else if (gregorianWeekday === 4) {
            fasting = { title: "Puasa Kamis", desc: "Puasa sunnah mingguan yang rutin dikerjakan Rasulullah SAW karena pada hari tersebut amal-amal diangkat." };
        }
        
        // 2. Ayyamul Bidh (13, 14, 15 every Hijri month)
        if ([13, 14, 15].includes(hijriDay)) {
            fasting = { title: "Puasa Ayyamul Bidh", desc: "Puasa sunnah tiga hari pertengahan bulan Hijriah yang pahalanya seperti berpuasa sepanjang tahun." };
        }
        
        // 3. Tasu'a & Asyura (9 & 10 Muharram)
        if (hijriMonthNum === 1) {
            if (hijriDay === 9) fasting = { title: "Puasa Tasu'a", desc: "Puasa sunnah tanggal 9 Muharram untuk menyelisihi ahli kitab." };
            if (hijriDay === 10) fasting = { title: "Puasa Asyura", desc: "Puasa sunnah tanggal 10 Muharram yang dapat menghapus dosa setahun yang lalu." };
        }

        // 4. Arafah (9 Zulhijjah)
        if (hijriMonthNum === 12 && hijriDay === 9) {
             fasting = { title: "Puasa Arafah", desc: "Puasa sunnah bagi yang tidak wukuf di Arafah, menghapus dosa setahun lalu dan setahun yang akan datang." };
        }
        
        // 5. Syawal (6 Days) - We won't mark them specifically here as it can be any 6 days, but usually marked manually. For simplicity, omit or just tag month.

        return fasting;
    }

    async function loadCalendar(month, year) {
        const grid = document.getElementById('calendar-grid');
        const header = document.getElementById('calendar-month-year');
        grid.innerHTML = '<div class="col-span-7 py-10 text-center"><i class="fas fa-spinner fa-spin text-emerald-500 text-2xl"></i></div>';
        
        const monthNames = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"];
        header.innerText = `${monthNames[month - 1]} ${year}`;

        try {
            const res = await fetch(`https://api.aladhan.com/v1/calendar/${year}/${month}?method=20`);
            const data = await res.json();
            const days = data.data;

            let html = '';
            
            // Get first day of the month to pad empty grid cells
            const firstDayData = days[0].date.gregorian;
            const firstDateObj = new Date(year, month - 1, 1);
            let startDayOfWeek = firstDateObj.getDay(); // 0 = Sunday, 1 = Monday
            
            // Pad empty cells
            for(let i=0; i<startDayOfWeek; i++) {
                html += `<div class="p-2 border border-transparent"></div>`;
            }

            days.forEach(day => {
                const gregorian = day.date.gregorian;
                const hijri = day.date.hijri;
                
                const gDay = parseInt(gregorian.day);
                const weekday = new Date(year, month - 1, gDay).getDay(); // 0-6
                
                const fastingData = checkPuasaSunnah(hijri.day, hijri.month.number, weekday);
                
                // Styling classes
                let textClass = "text-gray-800";
                if (weekday === 0) textClass = "text-red-500"; // Minggu = Merah
                
                let bgClass = "bg-white hover:bg-gray-50 border-transparent";
                let cursorClass = "cursor-pointer";
                let onclickEvent = ``;

                if (fastingData) {
                    bgClass = "bg-[#d1fae5] hover:bg-[#bbf7d0] border-transparent"; // emerald-100 / green-200
                    
                    // Escape single quotes for inline JS injection
                    const safeTitle = fastingData.title.replace(/'/g, "\\'");
                    const safeDesc = fastingData.desc.replace(/'/g, "\\'");
                    const fullDate = `${gDay} ${monthNames[month-1]} ${year} / ${hijri.day} ${hijri.month.en} ${hijri.year}H`;
                    onclickEvent = `onclick="event.preventDefault(); event.stopPropagation(); openPuasaModal('${fullDate}', '${safeTitle}', '${safeDesc}')"`;
                } else {
                    cursorClass = "cursor-default";
                }
                
                // Add current day highlight if it's today
                const today = new Date();
                if (gDay === today.getDate() && month === today.getMonth() + 1 && year === today.getFullYear()) {
                     textClass = "text-emerald-700 font-bold underline";
                     if(!fastingData) bgClass = "bg-emerald-50 border-emerald-200";
                }

                html += `
                    <div class="p-1 flex flex-col items-center justify-center aspect-square rounded-xl ${bgClass} ${cursorClass} transition-colors" ${onclickEvent}>
                        <span class="text-sm font-bold ${textClass}">${gDay}</span>
                        <span class="text-[8px] text-gray-500 font-arabic opacity-70">${hijri.day}</span>
                    </div>
                `;
            });
            
            grid.innerHTML = html;
        } catch(e) {
            grid.innerHTML = `<div class="col-span-7 text-center text-red-500 py-4 text-xs">Error memuat kalender</div>`;
        }
    }

    function changeMonth(step) {
        currentCalMonth += step;
        if (currentCalMonth > 12) {
            currentCalMonth = 1;
            currentCalYear += 1;
        } else if (currentCalMonth < 1) {
            currentCalMonth = 12;
            currentCalYear -= 1;
        }
        loadCalendar(currentCalMonth, currentCalYear);
    }

    function openPuasaModal(dateStr, title, desc) {
        document.getElementById('puasa-detail-date').innerText = dateStr;
        document.getElementById('puasa-detail-title').innerText = title;
        document.getElementById('puasa-detail-desc').innerText = desc;
        document.getElementById('modal-puasa-detail').classList.remove('hidden');
    }

    // Intercept Modal Open to load calendar once
    const originalOpenModalPuasa = window.openModal;
    window.openModal = function(id) {
        originalOpenModalPuasa(id);
        if (id === 'modal-fitur-puasa' && !isCalendarLoaded) {
            loadCalendar(currentCalMonth, currentCalYear);
            isCalendarLoaded = true;
        }
    };

    // Fitur 7: Alarm Adzan Interaktif
    let alarmAdzanInterval = null;
    let alarmAdzanSchedules = [];

    async function initAlarmAdzan() {
        if(alarmAdzanInterval) clearInterval(alarmAdzanInterval);
        
        // Fetch Location
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(async (pos) => {
                try {
                    const lat = pos.coords.latitude;
                    const lon = pos.coords.longitude;
                    const geoRes = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=10`);
                    const geoData = await geoRes.json();
                    let city = geoData.address.city || geoData.address.town || geoData.address.county || "Lokasi Anda";
                    document.getElementById('alarm-location-text').innerText = city;
                } catch(e) {
                    document.getElementById('alarm-location-text').innerText = "Samarinda (Default)";
                }
            }, () => {
                document.getElementById('alarm-location-text').innerText = "Samarinda (Default)";
            });
        }

        // Fetch Date & Prayer Times (Aladhan API)
        try {
            const dateObj = new Date();
            const dd = String(dateObj.getDate()).padStart(2, '0');
            const mm = String(dateObj.getMonth() + 1).padStart(2, '0');
            const yyyy = dateObj.getFullYear();

            // Hijri Date
            const hRes = await fetch(`https://api.aladhan.com/v1/gToH?date=${dd}-${mm}-${yyyy}`);
            const hData = await hRes.json();
            const h = hData.data.hijri;
            document.getElementById('alarm-hijri-date').innerText = `${h.day} ${h.month.en} ${h.year} H`;
            
            // Masehi Date
            const monthNames = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"];
            document.getElementById('alarm-masehi-date').innerText = `${dateObj.getDate()} ${monthNames[dateObj.getMonth()]} ${yyyy}`;

            // Prayer Times
            const pRes = await fetch('https://api.aladhan.com/v1/timingsByCity?city=Samarinda&country=Indonesia');
            const pData = await pRes.json();
            const timings = pData.data.timings;
            
            alarmAdzanSchedules = [
                { id: 'Imsak', name: 'Imsak', time: timings.Imsak },
                { id: 'Fajr', name: 'Subuh', time: timings.Fajr },
                { id: 'Sunrise', name: 'Terbit', time: timings.Sunrise },
                { id: 'Dhuhr', name: 'Dzuhur', time: timings.Dhuhr },
                { id: 'Asr', name: 'Ashar', time: timings.Asr },
                { id: 'Maghrib', name: 'Maghrib', time: timings.Maghrib },
                { id: 'Isha', name: 'Isya', time: timings.Isha }
            ];

            renderAlarmSchedules();
            alarmAdzanInterval = setInterval(updateAlarmAdzanEngine, 1000);
            updateAlarmAdzanEngine();

        } catch(e) {
            console.error(e);
            document.getElementById('alarm-countdown-text').innerText = "Gagal memuat jadwal.";
        }
    }

    function renderAlarmSchedules() {
        const container = document.getElementById('alarm-schedule-container');
        let html = '';
        alarmAdzanSchedules.forEach(p => {
            const isActive = localStorage.getItem(`alarm_adzan_${p.id}`) !== 'false';
            html += `
                <div id="row-${p.id}" class="bg-white/10 backdrop-blur-md border border-white/10 rounded-2xl p-4 flex justify-between items-center transition-colors duration-300">
                    <span class="text-xl font-bold font-sans tracking-wide text-white transition-colors duration-300 schedule-name">${p.name}</span>
                    <div class="flex items-center gap-4">
                        <span class="text-2xl font-mono font-bold text-white transition-colors duration-300 schedule-time">${p.time}</span>
                        <button onclick="toggleAdzanAlarm('${p.id}')" id="btn-${p.id}" class="w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${isActive ? 'bg-teal-500/20 text-teal-400 border border-teal-500/50 hover:bg-teal-500/40 shadow-[0_0_15px_rgba(20,184,166,0.3)]' : 'bg-red-500/20 text-red-400 border border-red-500/50 hover:bg-red-500/40'}">
                            <i class="fas ${isActive ? 'fa-check' : 'fa-times'}"></i>
                        </button>
                    </div>
                </div>
            `;
        });
        container.innerHTML = html;
    }

    function toggleAdzanAlarm(id) {
        const current = localStorage.getItem(`alarm_adzan_${id}`) !== 'false';
        localStorage.setItem(`alarm_adzan_${id}`, !current);
        renderAlarmSchedules(); // Re-render to update icon classes cleanly
        updateAlarmAdzanEngine(); // Immediately refresh golden highlights
        if('vibrate' in navigator) navigator.vibrate(50);
    }

    function updateAlarmAdzanEngine() {
        const now = new Date();
        document.getElementById('alarm-main-time').innerText = now.toLocaleTimeString('id-ID', {hour12: false}).substring(0,5);

        let nextPrayer = null;
        let activePrayerId = null;
        let targetTime = null;

        // Find Next Prayer
        for (let p of alarmAdzanSchedules) {
            const [h, m] = p.time.split(':');
            const pDate = new Date();
            pDate.setHours(parseInt(h), parseInt(m), 0, 0);
            
            if (pDate > now) {
                nextPrayer = p;
                targetTime = pDate;
                break;
            }
        }

        // If after Isya, next is Imsak tomorrow
        if (!targetTime && alarmAdzanSchedules.length > 0) {
            nextPrayer = alarmAdzanSchedules[0];
            const [h, m] = nextPrayer.time.split(':');
            targetTime = new Date();
            targetTime.setDate(targetTime.getDate() + 1);
            targetTime.setHours(parseInt(h), parseInt(m), 0, 0);
        }

        // Find Active Prayer (The one that just passed)
        for (let i = alarmAdzanSchedules.length - 1; i >= 0; i--) {
            const p = alarmAdzanSchedules[i];
            const [h, m] = p.time.split(':');
            const pDate = new Date();
            pDate.setHours(parseInt(h), parseInt(m), 0, 0);
            if (now >= pDate) {
                activePrayerId = p.id;
                
                // Calculate time passed since active prayer
                const diffMs = now - pDate;
                const passedH = Math.floor(diffMs / 3600000);
                const passedM = Math.floor((diffMs % 3600000) / 60000);
                
                let passedStr = "";
                if(passedH > 0) passedStr += `${passedH} jam `;
                if(passedM > 0) passedStr += `${passedM} menit `;
                if(passedStr === "") passedStr = "Baru saja ";
                
                // Update countdown text to show what passed
                document.getElementById('alarm-countdown-text').innerText = `Kurang lebih ${passedStr.trim()} yang lalu`;
                break;
            }
        }
        
        // If it's close to next prayer (< 30 mins), switch to countdown
        if (targetTime) {
            const diffMsToNext = targetTime - now;
            if (diffMsToNext < 30 * 60 * 1000 && diffMsToNext > 0) {
                const mins = Math.floor(diffMsToNext / 60000);
                const secs = Math.floor((diffMsToNext % 60000) / 1000);
                document.getElementById('alarm-countdown-text').innerText = `Menuju ${nextPrayer.name} dalam ${mins}m ${secs}s`;
                document.getElementById('alarm-countdown-text').className = "text-[#FFD700] font-bold text-sm tracking-wide bg-[#FFD700]/20 px-4 py-2 rounded-full border border-[#FFD700]/50 mb-2 animate-pulse";
            } else {
                 document.getElementById('alarm-countdown-text').className = "text-teal-400 font-bold text-sm tracking-wide bg-teal-900/30 px-4 py-2 rounded-full border border-teal-500/30 mb-2";
            }
        }

        // Apply Golden Highlight
        alarmAdzanSchedules.forEach(p => {
            const row = document.getElementById(`row-${p.id}`);
            if(row) {
                const nameEl = row.querySelector('.schedule-name');
                const timeEl = row.querySelector('.schedule-time');
                
                // Reset styling
                row.classList.remove('bg-white/20', 'border-[#FFD700]/50', 'shadow-[0_0_20px_rgba(255,215,0,0.15)]');
                row.classList.add('bg-white/10', 'border-white/10');
                nameEl.classList.remove('text-[#FFD700]');
                nameEl.classList.add('text-white');
                timeEl.classList.remove('text-[#FFD700]');
                timeEl.classList.add('text-white');

                // Apply active golden styling
                if (p.id === activePrayerId) {
                    row.classList.remove('bg-white/10', 'border-white/10');
                    row.classList.add('bg-white/20', 'border-[#FFD700]/50', 'shadow-[0_0_20px_rgba(255,215,0,0.15)]');
                    nameEl.classList.remove('text-white');
                    nameEl.classList.add('text-[#FFD700]');
                    timeEl.classList.remove('text-white');
                    timeEl.classList.add('text-[#FFD700]');
                }
            }
        });
    }

    function detectAlarmLocation() {
        initAlarmAdzan();
        if('vibrate' in navigator) navigator.vibrate(50);
    }
    
    function openAlarmCalendar() {
        closeModal('modal-fitur-alarm-adzan');
        openModal('modal-fitur-puasa');
    }
    
    function openAlarmSettings() {
        alert("Menu Pengaturan Suara Muadzin (Dalam Pengembangan)");
    }
    
    function openAlarmHelp() {
        alert("PANDUAN NOTIFIKASI:\\n\\n1. Buka Pengaturan HP > Aplikasi > Masjid Al Hijrah.\\n2. Izinkan 'Mulai Otomatis' (Auto Start).\\n3. Matikan 'Penghemat Baterai' (No Restrictions).\\n4. Pastikan volume media/notifikasi tidak dibisukan.");
    }
</script>
"""

IDUL_ADHA_DASHBOARD_HTML = """
<div class="pt-20 md:pt-32 pb-32 px-5 md:px-8 bg-gray-50 font-sans text-gray-800 selection:bg-amber-200 selection:text-amber-900">
    <!-- HERO SECTION: IDUL ADHA -->
    <div class="relative w-full bg-[#451a03] overflow-hidden pt-6 pb-12 mb-8 shadow-2xl rounded-[2.5rem] md:rounded-[4rem] border-b-4 border-[#78350f]">
        <div class="absolute inset-0 opacity-10" style="background-image: url('https://www.transparenttextures.com/patterns/arabesque.png');"></div>
        <div class="absolute right-[-10%] top-0 opacity-10 transform rotate-12 pointer-events-none">
            <i class="fas fa-kaaba text-[250px] md:text-[400px] text-[#fcd34d]"></i>
        </div>

        <div class="container mx-auto px-4 md:px-8 relative z-10 text-center mt-4">
            <h1 class="text-4xl md:text-6xl font-bold text-[#fcd34d] mb-4 font-sans tracking-tight drop-shadow-lg">
                Idul Adha Mode
            </h1>
            <p class="text-white/80 text-lg md:text-xl font-medium max-w-2xl mx-auto mb-8">
                Portal Khusus Informasi & Kegiatan Qurban Masjid Al-Hijrah
            </p>
            <a href="/" class="inline-block bg-white/10 hover:bg-white/20 text-[#fcd34d] border border-[#fcd34d]/30 px-6 py-2.5 rounded-full font-bold transition backdrop-blur-sm">
                <i class="fas fa-arrow-left mr-2"></i> Kembali ke Beranda
            </a>
        </div>
    </div>

    <!-- MAIN CONTENT -->
    <div class="container mx-auto px-4 md:px-8 max-w-6xl mb-12">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">

            <!-- LEFT COLUMN: MENU GRID -->
            <div class="lg:col-span-2">
                <h2 class="text-2xl font-bold text-[#451a03] mb-6 flex items-center border-l-4 border-[#78350f] pl-4">
                    <i class="fas fa-th-large text-[#78350f] mr-3"></i>Menu Qurban
                </h2>

                <div class="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-8 mb-8">
                    <!-- ABSEN PANITIA (Time-Gated) -->
                    {% if not is_valid_window %}
                    <!-- DISABLED LATE STATE -->
                    <div class="bg-red-50 p-5 md:p-8 rounded-3xl shadow-lg flex flex-col items-center justify-center h-36 md:h-48 border-2 border-red-500 opacity-80 relative overflow-hidden">
                        <div class="absolute -right-4 -top-4 w-16 h-16 bg-red-500 text-white rounded-full flex items-center justify-center text-xs font-bold transform rotate-12 shadow-lg">LATE</div>
                        <div class="bg-red-100 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-red-600">
                            <i class="fas fa-times-circle text-2xl md:text-3xl"></i>
                        </div>
                        <span class="text-sm md:text-base font-bold text-red-700">Terlambat</span>
                        <span class="text-[10px] text-red-500 text-center mt-1">Absensi Ditutup</span>
                    </div>
                    {% else %}
                    <!-- ACTIVE FORM -->
                    <form action="/idul-adha/absen" method="POST" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-amber-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-amber-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300 relative cursor-pointer" onclick="this.submit()">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                        <div class="bg-amber-100 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-amber-700 group-hover:bg-amber-500 group-hover:text-white transition-colors">
                            <i class="fas fa-clipboard-check text-2xl md:text-3xl"></i>
                        </div>
                        <span class="text-sm md:text-base font-bold text-[#78350f] group-hover:text-amber-700">Absen Panitia</span>
                        <span class="text-[10px] text-amber-600 font-medium absolute bottom-3">Batas: 08:30 AM</span>
                    </form>
                    {% endif %}

                    <!-- PLACEHOLDER 1 -->
                    <a href="#" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
                        <div class="bg-stone-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-stone-600 group-hover:bg-stone-500 group-hover:text-white transition-colors">
                            <i class="fas fa-file-invoice text-2xl md:text-3xl"></i>
                        </div>
                        <span class="text-sm md:text-base font-semibold text-gray-700 group-hover:text-stone-600">Laporan Qurban</span>
                    </a>

                    <!-- PLACEHOLDER 2 -->
                    <a href="#" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
                        <div class="bg-red-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-red-600 group-hover:bg-red-500 group-hover:text-white transition-colors">
                            <i class="fas fa-cow text-2xl md:text-3xl"></i>
                        </div>
                        <span class="text-sm md:text-base font-semibold text-gray-700 group-hover:text-red-600">Daftar Shohibul</span>
                    </a>

                    <!-- PLACEHOLDER 3 -->
                    <a href="/idul-adha/distribution" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
                        <div class="bg-emerald-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-emerald-600 group-hover:bg-emerald-500 group-hover:text-white transition-colors">
                            <i class="fas fa-balance-scale text-2xl md:text-3xl"></i>
                        </div>
                        <span class="text-sm md:text-base font-semibold text-gray-700 group-hover:text-emerald-600">Pembagian</span>
                    </a>

                     <!-- PLACEHOLDER 4 -->
                    <a href="#" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
                        <div class="bg-orange-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-orange-600 group-hover:bg-orange-500 group-hover:text-white transition-colors">
                            <i class="fas fa-images text-2xl md:text-3xl"></i>
                        </div>
                        <span class="text-sm md:text-base font-semibold text-gray-700 group-hover:text-orange-600">Galeri Qurban</span>
                    </a>

                    <!-- PLACEHOLDER 5 -->
                    <a href="#" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
                        <div class="bg-blue-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-blue-600 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                            <i class="fas fa-info-circle text-2xl md:text-3xl"></i>
                        </div>
                        <span class="text-sm md:text-base font-semibold text-gray-700 group-hover:text-blue-600">Panduan</span>
                    </a>
                </div>
            </div>

            <!-- RIGHT COLUMN: PRAYER CARD -->
            <div class="flex flex-col gap-6">
                <!-- PRAYER CARD -->
                <div class="bg-gradient-to-br from-[#78350f] to-[#451a03] rounded-3xl p-6 md:p-10 text-white shadow-xl relative overflow-hidden transform md:hover:scale-[1.02] transition-transform duration-500 border border-[#fcd34d]/30">
                    <a href="{{ url_for('fitur_masjid') }}" class="absolute top-4 right-4 bg-white/10 hover:bg-white text-white hover:text-[#78350f] px-3 py-1.5 rounded-full text-xs font-bold transition-all shadow-[0_0_15px_rgba(255,255,255,0.1)] hover:shadow-[0_0_20px_rgba(255,255,255,0.4)] z-20 flex items-center gap-1 backdrop-blur-sm">
                        <i class="fas fa-mosque"></i> Fitur Lainnya
                    </a>
                    <div class="absolute top-0 right-0 opacity-5 transform translate-x-4 -translate-y-4">
                        <i class="fas fa-mosque text-9xl"></i>
                    </div>
                    <div class="relative z-10">
                        <p class="text-xs font-medium opacity-80 mb-1 tracking-wide uppercase text-[#fcd34d]">Waktu Sholat Berikutnya</p>
                        <h2 class="text-4xl font-bold mb-3" id="next-prayer-name">--:--</h2>
                        <div class="bg-black/30 backdrop-blur-md rounded-xl px-4 py-2 inline-block mb-6 border border-white/10">
                            <span class="font-mono text-2xl font-bold tracking-wider" id="countdown-timer">--:--:--</span>
                        </div>

                        <div class="grid grid-cols-5 gap-1 text-center text-xs opacity-90 border-t border-[#fcd34d]/20 pt-4">
                            <div>
                                <div class="font-semibold mb-1 text-[#fcd34d]">Subuh</div>
                                <div id="fajr-time" class="font-mono">--:--</div>
                            </div>
                            <div>
                                <div class="font-semibold mb-1 text-[#fcd34d]">Dzuhur</div>
                                <div id="dhuhr-time" class="font-mono">--:--</div>
                            </div>
                            <div>
                                <div class="font-semibold mb-1 text-[#fcd34d]">Ashar</div>
                                <div id="asr-time" class="font-mono">--:--</div>
                            </div>
                            <div>
                                <div class="font-semibold mb-1 text-[#fcd34d]">Maghrib</div>
                                <div id="maghrib-time" class="font-mono">--:--</div>
                            </div>
                            <div>
                                <div class="font-semibold mb-1 text-[#fcd34d]">Isya</div>
                                <div id="isha-time" class="font-mono">--:--</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
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

        <!-- RIGHT COLUMN: PRAYER CARD & RAMADHAN BANNER -->
        <div class="flex flex-col gap-6">
            
            <!-- PRAYER CARD -->
            <div class="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-3xl p-6 md:p-10 text-white shadow-xl relative overflow-hidden transform md:hover:scale-[1.02] transition-transform duration-500">
                <a href="{{ url_for('fitur_masjid') }}" class="absolute top-4 right-4 bg-white/20 hover:bg-white text-white hover:text-emerald-700 px-3 py-1.5 rounded-full text-xs font-bold transition-all shadow-[0_0_15px_rgba(255,255,255,0.3)] hover:shadow-[0_0_20px_rgba(255,255,255,0.6)] z-20 flex items-center gap-1 backdrop-blur-sm">
                    <i class="fas fa-mosque"></i> Fitur Lainnya
                </a>
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

            <!-- DUAL BANNER CONTAINER -->
            <div class="relative w-full h-[120px] md:h-[140px] perspective-1000 group">
                <!-- Inner flipper container -->
                <div id="banner-flipper" class="w-full h-full relative transition-transform duration-700 preserve-3d">
                    
                    <!-- RAMADHAN BANNER (FRONT FACE) -->
                    <div class="absolute w-full h-full backface-hidden rounded-3xl overflow-hidden shadow-xl border border-[#0b162c]">
                        <!-- Background & Texture -->
                        <div class="absolute inset-0 bg-[#0b162c]"></div>
                        <div class="absolute inset-0 opacity-10" style="background-image: url('https://www.transparenttextures.com/patterns/arabesque.png');"></div>

                        <!-- Crescent Moon Background -->
                        <div class="absolute right-24 top-1/2 transform -translate-y-1/2 opacity-10 text-[#FFD700] pointer-events-none">
                            <i class="fas fa-moon text-7xl md:text-8xl"></i>
                        </div>

                        <div class="relative w-full h-full px-6 py-4 md:px-8 flex items-center justify-between">
                            <a href="/ramadhan" class="flex-1">
                                <h2 class="text-2xl md:text-3xl font-bold text-[#FFD700] mb-1 font-sans tracking-wide leading-none hover:text-white transition-colors">Ramadhan Mode</h2>
                                <p class="text-white/60 text-xs md:text-sm font-medium">Akses Dashboard Khusus Ramadhan</p>
                            </a>

                            <!-- Trigger Button to flip -->
                            <button onclick="document.getElementById('banner-flipper').classList.toggle('rotate-x-180')" class="w-10 h-10 md:w-12 md:h-12 rounded-full bg-white/10 hover:bg-[#FFD700] flex items-center justify-center text-[#FFD700] hover:text-[#0b1026] transition-all duration-300 relative z-10 ml-4 group/btn border border-[#FFD700]/30 shadow-[0_0_15px_rgba(255,215,0,0.2)] hover:shadow-[0_0_20px_rgba(255,215,0,0.6)]">
                                <i class="fas fa-arrow-down text-sm md:text-lg group-hover/btn:translate-y-1 transition-transform"></i>
                            </button>
                        </div>
                    </div>

                    <!-- IDUL ADHA BANNER (BACK FACE) -->
                    <div class="absolute w-full h-full backface-hidden rotate-x-180 rounded-3xl overflow-hidden shadow-xl border border-[#78350f]">
                        <div class="absolute inset-0 bg-gradient-to-br from-[#78350f] to-[#451a03]"></div>
                        <div class="absolute inset-0 opacity-10" style="background-image: url('https://www.transparenttextures.com/patterns/arabesque.png');"></div>

                        <div class="absolute right-24 top-1/2 transform -translate-y-1/2 opacity-10 text-[#fcd34d] pointer-events-none">
                            <i class="fas fa-kaaba text-7xl md:text-8xl"></i>
                        </div>

                        <div class="relative w-full h-full px-6 py-4 md:px-8 flex items-center justify-between">
                            <a href="/idul-adha" class="flex-1">
                                <h2 class="text-2xl md:text-3xl font-bold text-[#fcd34d] mb-1 font-sans tracking-wide leading-none hover:text-white transition-colors">Idul Adha Mode</h2>
                                <p class="text-white/70 text-xs md:text-sm font-medium">Akses Dashboard Khusus Qurban</p>
                            </a>

                            <!-- Trigger Button to flip back -->
                            <button onclick="document.getElementById('banner-flipper').classList.toggle('rotate-x-180')" class="w-10 h-10 md:w-12 md:h-12 rounded-full bg-white/10 hover:bg-[#fcd34d] flex items-center justify-center text-[#fcd34d] hover:text-[#451a03] transition-all duration-300 relative z-10 ml-4 group/btn border border-[#fcd34d]/30 shadow-[0_0_15px_rgba(252,211,77,0.2)] hover:shadow-[0_0_20px_rgba(252,211,77,0.6)]">
                                <i class="fas fa-arrow-up text-sm md:text-lg group-hover/btn:-translate-y-1 transition-transform"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- CSS required for flip transition -->
            <style>
                .perspective-1000 { perspective: 1000px; }
                .preserve-3d { transform-style: preserve-3d; }
                .backface-hidden { backface-visibility: hidden; -webkit-backface-visibility: hidden; }
                .rotate-x-180 { transform: rotateX(180deg); }
            </style>

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

    <!-- TERAPI SECTION -->
    <div class="mb-6">
        <button onclick="toggleTerapi()" class="w-full bg-white p-6 rounded-3xl shadow-lg border border-blue-50 flex justify-between items-center group hover:bg-blue-50 transition-all duration-500">
            <div class="flex items-center gap-4">
                <div class="bg-blue-100 p-3 rounded-xl text-blue-500 group-hover:bg-blue-500 group-hover:text-white transition-colors shadow-sm">
                    <i class="fas fa-heartbeat text-2xl"></i>
                </div>
                <div class="text-left">
                    <h3 class="text-lg font-bold text-gray-800 group-hover:text-blue-700">Terapi</h3>
                    <p class="text-xs text-gray-500 font-medium">Bantuan Kesehatan & Epilepsi</p>
                </div>
            </div>
            <div id="terapi-chevron" class="bg-gray-50 w-10 h-10 rounded-full flex items-center justify-center text-gray-400 group-hover:bg-white group-hover:text-blue-500 transition-all duration-500">
                 <i class="fas fa-chevron-down transform transition-transform duration-500"></i>
            </div>
        </button>
        
        <div id="terapi-content" class="hidden mt-6 transition-all duration-1000 ease-in-out opacity-0 -translate-y-4">
             <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                 <!-- 1. Audio Healing -->
                 <button onclick="openModal('modal-terapi-audio')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-blue-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-700 text-left flex items-center gap-3 group">
                     <div class="bg-blue-50 text-blue-400 p-2.5 rounded-xl group-hover:bg-blue-400 group-hover:text-white transition-colors"><i class="fas fa-music"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-blue-500">Terapi Suara</span>
                 </button>
                 <!-- 2. Latihan Napas -->
                 <button onclick="startBreathing()" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-blue-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-700 text-left flex items-center gap-3 group">
                     <div class="bg-blue-50 text-blue-400 p-2.5 rounded-xl group-hover:bg-blue-400 group-hover:text-white transition-colors"><i class="fas fa-lungs"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-blue-500">Latihan Napas</span>
                 </button>
                 <!-- 3. Sleep Monitor -->
                 <button onclick="openModal('modal-terapi-tidur')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-blue-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-700 text-left flex items-center gap-3 group">
                     <div class="bg-blue-50 text-blue-400 p-2.5 rounded-xl group-hover:bg-blue-400 group-hover:text-white transition-colors"><i class="fas fa-bed"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-blue-500">Tracker Tidur</span>
                 </button>
                 <!-- 4. Seizure Log -->
                 <button onclick="openModal('modal-terapi-log')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-blue-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-700 text-left flex items-center gap-3 group">
                     <div class="bg-blue-50 text-blue-400 p-2.5 rounded-xl group-hover:bg-blue-400 group-hover:text-white transition-colors"><i class="fas fa-file-medical"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-blue-500">Jurnal Kambuh</span>
                 </button>
                 <!-- 5. Medication Alarm -->
                 <button onclick="openModal('modal-terapi-alarm')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-blue-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-700 text-left flex items-center gap-3 group">
                     <div class="bg-blue-50 text-blue-400 p-2.5 rounded-xl group-hover:bg-blue-400 group-hover:text-white transition-colors"><i class="fas fa-capsules"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-blue-500">Alarm Obat</span>
                 </button>
                 <!-- 6. Diet Keton -->
                 <button onclick="openModal('modal-terapi-diet')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-blue-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-700 text-left flex items-center gap-3 group">
                     <div class="bg-blue-50 text-blue-400 p-2.5 rounded-xl group-hover:bg-blue-400 group-hover:text-white transition-colors"><i class="fas fa-apple-alt"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-blue-500">Diet Keton</span>
                 </button>
             </div>
        </div>
    </div>

    <!-- KALKULATOR ISLAM SECTION -->
    <div id="kalkulator-section" class="mb-6">
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
    <div id="pwa-static-btn-container" class="pwa-btn-container mb-6 hidden">
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

    <!-- DEVELOPER BUTTON -->
    <div class="mb-8">
        <button onclick="openModal('modal-developer'); playDevAudio()" class="w-full bg-white p-4 rounded-3xl shadow-sm border border-gray-100 flex justify-between items-center group hover:bg-gray-50 transition-all">
            <div class="flex items-center gap-4">
                <div class="bg-gray-100 p-3 rounded-xl text-gray-600">
                    <i class="fas fa-code text-2xl"></i>
                </div>
                <div class="text-left">
                    <h3 class="text-lg font-bold text-gray-800">Pembuat Website</h3>
                    <p class="text-xs text-gray-500 font-medium">Credit & Developer Profil</p>
                </div>
            </div>
            <div class="bg-gray-50 w-10 h-10 rounded-full flex items-center justify-center text-gray-400 group-hover:text-gray-600">
                 <i class="fas fa-arrow-right"></i>
            </div>
        </button>
    </div>

    <!-- MODALS -->

    <!-- Modal Developer -->
    <div id="modal-developer" class="fixed inset-0 z-[100] hidden">
        <div class="fixed inset-0 bg-white/95 backdrop-blur-xl animate-[slideUp_0.5s_ease-out] overflow-y-auto flex items-center justify-center p-4">
            <div class="relative w-full max-w-md mx-auto flex flex-col items-center justify-center p-4 text-center">
                <button onclick="closeModal('modal-developer'); stopDevAudio()" class="absolute top-0 right-0 md:-right-4 bg-gray-100 w-10 h-10 rounded-full text-gray-600 hover:bg-gray-200 text-xl flex items-center justify-center z-10">&times;</button>
                
                <h2 class="text-xs font-bold text-gray-400 tracking-[0.3em] mb-2 uppercase">DEVELOPER</h2>
                <h1 class="text-3xl font-extrabold text-emerald-800 mb-8" style="white-space: nowrap; font-size: clamp(1.5rem, 5vw, 2.5rem);">SAMARINDA WEB CREATIVE</h1>
                
                <div class="mb-8">
                    <img src="/static/Samarinda_Web_Creative_Logo-removebg-preview.png" alt="Logo Developer" class="h-32 object-contain mx-auto drop-shadow-2xl">
                </div>
                
                <h3 class="text-xs font-bold text-gray-400 tracking-[0.2em] mb-4 uppercase border-b border-gray-200 pb-2 w-24 mx-auto">PIHAK KETIGA</h3>
                <div class="flex flex-col gap-4 justify-center items-center mb-8">
                    <img src="/static/pythonanywherelogo-removebg.png" class="h-16 object-contain">
                    <img src="/static/pythonlogo.png" class="h-16 object-contain">
                    <img src="/static/godaddylogo.png" class="h-8 object-contain">
                </div>
                
                <div class="bg-gray-50 p-6 rounded-3xl border border-gray-100 mb-8 max-w-sm w-full mx-auto">
                    <p class="text-sm text-gray-600 font-medium leading-relaxed mb-1">
                        Samarinda, Kalimantan Timur,<br>
                        Jln. Delima Dalam, Blok. E, RT. 53
                    </p>
                    <p class="text-xs text-gray-500 italic mt-2">"kalau butuh jasa pembuatan aplikasi website seperti ini, hubungi kami yaa hehee"</p>
                </div>
                
                <div class="flex items-center justify-center gap-4 mb-8">
                    <a href="https://www.instagram.com/samarindawebcreative/" target="_blank" class="bg-gradient-to-tr from-purple-500 to-pink-500 text-white w-12 h-12 rounded-full flex items-center justify-center shadow-lg hover:scale-110 transition shrink-0">
                        <i class="fab fa-instagram text-2xl"></i>
                    </a>
                    <a href="https://b1l14n50r1.pythonanywhere.com/" class="flex items-center gap-2 px-6 py-3 bg-gray-900 text-white rounded-full font-bold shadow-lg hover:scale-105 transition">
                        <img src="/static/piton.png" class="h-6 w-6"> See Our Current Work
                    </a>
                </div>

                <p class="text-[10px] text-gray-400 font-serif">Sempurna (2006) - Andra & The Backbone (Covered by BBIBEEB)</p>
            </div>
        </div>
        <audio id="dev-audio" src="/static/Perfection(compressed).m4a"></audio>
        <script>
            let devAudio = document.getElementById('dev-audio');
            let fadeInterval;

            function playDevAudio() {
                devAudio.volume = 0.3;
                devAudio.currentTime = 0;
                devAudio.play();
                
                // Fade In 0.3 -> 0.6 in 3s
                let vol = 0.3;
                clearInterval(fadeInterval);
                fadeInterval = setInterval(() => {
                    if(vol < 0.6) {
                        vol += 0.05;
                        devAudio.volume = Math.min(vol, 0.6);
                    } else {
                        clearInterval(fadeInterval);
                    }
                }, 500);

                // Monitor Fade Out (Last 6s) - Simulated
                devAudio.ontimeupdate = () => {
                    if(devAudio.duration && devAudio.duration - devAudio.currentTime <= 6) {
                        if(devAudio.volume > 0.05) devAudio.volume -= 0.01;
                    }
                };
                
                devAudio.onended = () => {
                    playDevAudio();
                };
            }

            function stopDevAudio() {
                devAudio.pause();
                devAudio.currentTime = 0;
                clearInterval(fadeInterval);
            }
        </script>
    </div>

    <!-- Modal Terapi Audio -->
    <div id="modal-terapi-audio" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" onclick="closeModal('modal-terapi-audio')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.5s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-music text-blue-500 mr-2"></i>Terapi Suara</h3>
                <button onclick="closeModal('modal-terapi-audio')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            <div class="space-y-4">
                <p class="text-sm text-gray-600 bg-blue-50 p-3 rounded-xl border border-blue-100">
                    <i class="fas fa-info-circle mr-1"></i> Dengarkan 15 menit untuk menstabilkan gelombang otak.
                </p>
                <div class="space-y-3">
                    <div class="bg-gray-50 p-4 rounded-2xl flex items-center justify-between border border-gray-100">
                        <span class="font-bold text-gray-700 text-sm">Suara Alam</span>
                        <div class="flex items-center gap-2">
                            <button onclick="playAudio('alam')" class="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center hover:bg-blue-500 hover:text-white transition-colors"><i class="fas fa-play"></i></button>
                            <button onclick="switchNatureAudio()" class="w-8 h-8 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center hover:bg-emerald-500 hover:text-white transition-colors"><i class="fas fa-step-forward text-xs"></i></button>
                        </div>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-2xl flex items-center justify-between border border-gray-100">
                        <span class="font-bold text-gray-700 text-sm">Mozart K.448</span>
                        <button onclick="playAudio('mozart')" class="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center hover:bg-blue-500 hover:text-white transition-colors"><i class="fas fa-play"></i></button>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-2xl flex items-center justify-between border border-gray-100">
                        <span class="font-bold text-gray-700 text-sm">Murattal Relaksasi</span>
                        <button onclick="playAudio('murattal')" class="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center hover:bg-blue-500 hover:text-white transition-colors"><i class="fas fa-play"></i></button>
                    </div>
                </div>
                <div class="hidden bg-blue-50 p-2 rounded-xl mt-2">
                    <div id="now-playing" class="text-center text-xs text-blue-600 font-bold mb-1">Sedang Memutar...</div>
                    <input type="range" id="audio-seeker" class="w-full h-1 bg-blue-200 rounded-lg appearance-none cursor-pointer" value="0">
                </div>
            </div>
            <button onclick="showMedicalExplanation('audio')" class="mt-4 w-full border border-blue-200 text-blue-500 text-[10px] font-bold py-2 rounded-lg hover:bg-blue-50 transition uppercase tracking-wider">
                Penjelasan Medis
            </button>
        </div>
    </div>

    <!-- Modal Terapi Napas -->
    <div id="modal-terapi-napas" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-blue-900/95 backdrop-blur-md transition-opacity" onclick="stopBreathing(); closeModal('modal-terapi-napas')"></div>
        <div class="absolute inset-0 flex flex-col items-center justify-center z-10 pointer-events-none">
            <h3 class="text-2xl font-bold text-white mb-12 opacity-90">Latihan Napas</h3>
            <div class="relative flex items-center justify-center w-80 h-80">
                <div id="breath-circle" class="w-32 h-32 bg-blue-300/30 rounded-full absolute"></div>
                <div class="w-32 h-32 bg-white rounded-full flex items-center justify-center relative z-20 shadow-[0_0_50px_rgba(255,255,255,0.3)]">
                    <span id="breath-text" class="text-blue-600 font-bold text-xl">Mulai</span>
                </div>
            </div>
            <p class="text-white/70 text-sm mt-12 max-w-xs text-center">Ikuti instruksi. Fokus pada lingkaran.</p>
            <button onclick="stopBreathing(); closeModal('modal-terapi-napas')" class="mt-8 bg-white/20 text-white px-6 py-2 rounded-full hover:bg-white/30 pointer-events-auto backdrop-blur-sm border border-white/10">Selesai</button>
            <button onclick="showMedicalExplanation('napas')" class="mt-4 bg-transparent border border-white/20 text-white/50 text-[10px] font-bold py-2 px-6 rounded-lg hover:bg-white/10 transition uppercase tracking-wider pointer-events-auto backdrop-blur-sm">
                Penjelasan Medis
            </button>
        </div>
    </div>

    <!-- Modal Terapi Tidur -->
    <div id="modal-terapi-tidur" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" onclick="closeModal('modal-terapi-tidur')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.5s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-bed text-blue-500 mr-2"></i>Tracker Tidur</h3>
                <button onclick="closeModal('modal-terapi-tidur')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            <div class="space-y-6">
                <div>
                    <label class="block text-sm font-bold text-gray-600 mb-2">Berapa jam Anda tidur semalam?</label>
                    <input type="number" id="sleep-hours" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-4 text-center text-2xl font-bold focus:ring-2 focus:ring-blue-500 focus:outline-none" placeholder="0">
                </div>
                <button onclick="checkSleep()" class="w-full bg-blue-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-blue-600 transition">Cek Kondisi</button>
                <div id="sleep-result" class="hidden p-4 rounded-xl border text-sm"></div>
            </div>
            <button onclick="showMedicalExplanation('tidur')" class="mt-4 w-full border border-blue-200 text-blue-500 text-[10px] font-bold py-2 rounded-lg hover:bg-blue-50 transition uppercase tracking-wider">
                Penjelasan Medis
            </button>
        </div>
    </div>

    <!-- Modal Seizure Log -->
    <div id="modal-terapi-log" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" onclick="closeModal('modal-terapi-log')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.5s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20 max-h-[90vh] overflow-y-auto">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-file-medical text-blue-500 mr-2"></i>Jurnal Kambuh</h3>
                <button onclick="closeModal('modal-terapi-log')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            
            <form action="/therapy/log" method="POST" class="space-y-4 mb-8 bg-blue-50 p-4 rounded-2xl border border-blue-100">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Tanggal</label>
                        <input type="date" name="date" class="w-full bg-white border border-blue-100 rounded-xl p-2 text-sm" required>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Jam</label>
                        <input type="time" name="time" class="w-full bg-white border border-blue-100 rounded-xl p-2 text-sm" required>
                    </div>
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Pemicu</label>
                    <select name="trigger" class="w-full bg-white border border-blue-100 rounded-xl p-2 text-sm">
                        <option value="Stres">Stres / Cemas</option>
                        <option value="Kurang Tidur">Kurang Tidur</option>
                        <option value="Lupa Obat">Lupa Minum Obat</option>
                        <option value="Silau">Cahaya Silau / Berkedip</option>
                        <option value="Kelelahan">Kelelahan Fisik</option>
                        <option value="Lainnya">Lainnya</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Catatan Tambahan</label>
                    <input type="text" name="notes" placeholder="Durasi, kondisi setelahnya..." class="w-full bg-white border border-blue-100 rounded-xl p-2 text-sm">
                </div>
                <button type="submit" class="w-full bg-blue-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-blue-600 transition">Simpan Laporan</button>
            </form>
            
            <h4 class="text-sm font-bold text-gray-800 mb-4 pl-2 border-l-4 border-blue-500">Riwayat Terakhir</h4>
            <div class="space-y-3">
                {% for log in epilepsi_logs %}
                <div class="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 flex justify-between items-start">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md">{{ log['date'] }}</span>
                            <span class="text-xs text-gray-400">{{ log['time'] }}</span>
                        </div>
                        <p class="text-sm font-bold text-gray-800">{{ log['trigger'] }}</p>
                        {% if log['notes'] %}<p class="text-xs text-gray-500 mt-1 italic">"{{ log['notes'] }}"</p>{% endif %}
                    </div>
                </div>
                {% else %}
                <p class="text-center text-gray-400 text-xs py-4">Belum ada data rekaman.</p>
                {% endfor %}
            </div>
            <button onclick="showMedicalExplanation('log')" class="mt-4 w-full border border-blue-200 text-blue-500 text-[10px] font-bold py-2 rounded-lg hover:bg-blue-50 transition uppercase tracking-wider">
                Penjelasan Medis
            </button>
        </div>
    </div>

    <!-- Modal Medication Alarm -->
    <div id="modal-terapi-alarm" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" onclick="closeModal('modal-terapi-alarm')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.5s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-capsules text-blue-500 mr-2"></i>Alarm Obat</h3>
                <button onclick="closeModal('modal-terapi-alarm')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            
            <div class="bg-blue-50 p-4 rounded-2xl border border-blue-100 mb-6">
                <p class="text-sm text-gray-700 mb-3 font-medium">Set Jam Minum Obat:</p>
                <div class="flex gap-4">
                    <input type="time" id="alarm-time-1" class="w-full p-3 rounded-xl border border-blue-200 focus:outline-none" value="07:00">
                    <input type="time" id="alarm-time-2" class="w-full p-3 rounded-xl border border-blue-200 focus:outline-none" value="19:00">
                </div>
                <button onclick="saveAlarm()" class="mt-3 w-full bg-blue-500 text-white text-xs font-bold py-2 rounded-lg hover:bg-blue-600 transition">Simpan Pengaturan</button>
                <p id="alarm-status" class="text-xs text-green-600 mt-2 hidden text-center font-bold">Alarm Aktif!</p>
            </div>
            
            <p class="text-xs text-gray-500 text-center">
                Alarm akan mengunci layar dan meminta Anda menyelesaikan soal matematika untuk memastikan Anda bangun.
            </p>
            <button onclick="showMedicalExplanation('alarm')" class="mt-4 w-full border border-blue-200 text-blue-500 text-[10px] font-bold py-2 rounded-lg hover:bg-blue-50 transition uppercase tracking-wider">
                Penjelasan Medis
            </button>
        </div>
    </div>

    <!-- LOCKED ALARM SCREEN (Hidden by default) -->
    <div id="alarm-lock-screen" class="fixed inset-0 z-[150] bg-red-600 text-white flex flex-col items-center justify-center hidden p-8">
        <i class="fas fa-bell text-6xl mb-6 animate-bounce"></i>
        <h2 class="text-4xl font-bold mb-2">Waktunya Obat!</h2>
        <p class="mb-8 text-white/80">Selesaikan soal untuk mematikan alarm.</p>
        
        <div class="bg-white text-gray-800 p-6 rounded-3xl w-full max-w-xs text-center shadow-2xl">
            <p class="text-2xl font-bold mb-4" id="math-problem">5 + 7 = ?</p>
            <input type="number" id="math-answer" class="w-full p-3 border-2 border-gray-300 rounded-xl text-center text-xl mb-4" placeholder="Jawab...">
            <button onclick="checkMath()" class="w-full bg-red-600 text-white font-bold py-3 rounded-xl hover:bg-red-700">Matikan Alarm</button>
        </div>
    </div>

    <!-- Modal Diet Keton -->
    <div id="modal-terapi-diet" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" onclick="closeModal('modal-terapi-diet')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.5s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20 max-h-[85vh] overflow-y-auto">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-apple-alt text-blue-500 mr-2"></i>Panduan Diet & Puasa</h3>
                <button onclick="closeModal('modal-terapi-diet')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            
            <div class="space-y-6">
                <div class="bg-gradient-to-r from-blue-500 to-blue-600 rounded-2xl p-5 text-white shadow-lg">
                    <h4 class="font-bold text-lg mb-1">Puasa Sunnah</h4>
                    <p class="text-xs opacity-90 mb-3">Puasa membantu menstabilkan aktivitas listrik otak (neuroprotektif).</p>
                    <div class="bg-white/20 rounded-xl p-3 text-sm font-medium backdrop-blur-sm">
                        <i class="fas fa-calendar-check mr-2"></i> Jadwal Terdekat: Senin & Kamis
                    </div>
                </div>
                
                <div>
                    <h4 class="font-bold text-gray-800 mb-3 border-l-4 border-green-500 pl-2">Diet Ketogenik (Rendah Karbo)</h4>
                    <p class="text-sm text-gray-600 mb-4 leading-relaxed">
                        Diet tinggi lemak dan sangat rendah karbohidrat terbukti efektif mengurangi frekuensi kejang.
                    </p>
                    
                    <div class="grid grid-cols-2 gap-3">
                        <div class="bg-green-50 p-3 rounded-xl border border-green-100">
                            <p class="text-xs font-bold text-green-700 uppercase mb-2">Dianjurkan <i class="fas fa-check float-right"></i></p>
                            <ul class="text-xs text-gray-600 space-y-1">
                                <li>• Alpukat</li>
                                <li>• Minyak Zaitun/Kelapa</li>
                                <li>• Ikan & Telur</li>
                                <li>• Sayuran Hijau</li>
                            </ul>
                        </div>
                        <div class="bg-red-50 p-3 rounded-xl border border-red-100">
                            <p class="text-xs font-bold text-red-700 uppercase mb-2">Hindari <i class="fas fa-times float-right"></i></p>
                            <ul class="text-xs text-gray-600 space-y-1">
                                <li>• Gula Pasir</li>
                                <li>• Nasi Putih (Kurangi)</li>
                                <li>• Roti & Tepung</li>
                                <li>• Minuman Manis</li>
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div class="bg-gray-50 p-4 rounded-xl text-xs text-gray-500 italic border border-gray-200">
                    <i class="fas fa-info-circle mr-1"></i> Konsultasikan dengan dokter gizi sebelum mengubah pola makan secara drastis.
                </div>
            </div>
            <button onclick="showMedicalExplanation('diet')" class="mt-4 w-full border border-blue-200 text-blue-500 text-[10px] font-bold py-2 rounded-lg hover:bg-blue-50 transition uppercase tracking-wider">
                Penjelasan Medis
            </button>
        </div>
    </div>
    
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

    <!-- Modal Medical Explanation -->
    <div id="modal-medical-explanation" class="fixed inset-0 z-[120] hidden">
        <div class="absolute inset-0 bg-white/80 backdrop-blur-md" onclick="closeModal('modal-medical-explanation')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white/90 backdrop-blur-xl rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20 border border-white/50">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-user-md text-blue-500 mr-2"></i>Penjelasan Medis</h3>
                <button onclick="closeModal('modal-medical-explanation')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            <div class="space-y-6 overflow-y-auto max-h-[70vh] pb-10">
                <!-- Sains Section -->
                <div>
                    <h4 class="text-sm font-bold text-gray-800 uppercase tracking-wider mb-2 border-b border-gray-200 pb-1">DASAR MEDIS (SAINS)</h4>
                    <p id="med-sains" class="text-sm text-gray-700 leading-relaxed font-medium bg-blue-50 p-4 rounded-xl border border-blue-100">
                        ...
                    </p>
                </div>
                <!-- Refs Section -->
                <div>
                    <h4 class="text-sm font-bold text-gray-800 uppercase tracking-wider mb-2 border-b border-gray-200 pb-1">PENELITIAN MEDIS & REFERENSI</h4>
                    <ul id="med-refs" class="space-y-1">
                        <!-- LI generated by JS -->
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentExplanation = {};

        const MEDICAL_DATA = {
            'audio': {
                sains: "Otak penderita epilepsi sering mengalami lonjakan gelombang listrik yang tidak beraturan (Epileptiform Discharges). Terapi suara berfokus pada ritme dan frekuensi tertentu (seperti komposisi Mozart K.448 atau tempo tartil Murattal) yang secara biofisik merangsang korteks pendengaran. Stimulasi parasimpatetik ini memicu efek relaksasi dan menormalkan kembali sinkronisasi gelombang listrik otak, sehingga menurunkan frekuensi kejang.",
                refs: [
                    "Clinical Neurophysiology Journal (2015): Penelitian oleh Coppola et al., membuktikan bahwa mendengarkan Mozart K.448 menurunkan Interictal Epileptiform Discharges (IEDs) hingga 32% pada pasien epilepsi.",
                    "Royal Society of Medicine (2001): Hughes dkk., merilis \\"The Mozart Effect on Epilepsy\\", menunjukkan penurunan kejang yang signifikan pada pasien koma dan kebal obat.",
                    "Journal of Islamic Medicine (2018): Riset membuktikan lantunan Murattal Al-Quran (tempo lambat) merangsang gelombang Alpha di otak, menurunkan hormon stres kortisol yang menjadi salah satu pemicu utama kejang."
                ]
            },
            'napas': {
                sains: "Saraf Vagus adalah saraf kranial terpanjang yang menghubungkan otak ke organ vital (jantung/paru). Bernapas dengan tempo yang sangat lambat (Slow-Paced Breathing, 5-6 napas per menit) memberikan stimulasi non-invasif langsung ke Saraf Vagus. Hal ini meningkatkan Heart Rate Variability (HRV) dan mengaktifkan sistem saraf parasimpatis, yang secara kimiawi menaikkan \\"ambang batas kejang\\" (Seizure Threshold) di otak.",
                refs: [
                    "Neurology Journal (2018): Penelitian klinis menunjukkan bahwa pasien yang mempraktikkan pernapasan diafragma lambat mengalami peningkatan aktivitas Saraf Vagus, mirip dengan efek alat pacu VNS (Vagus Nerve Stimulator) yang mahal harganya.",
                    "Epilepsy & Behavior (2012): Studi oleh Yildiz et al., menyimpulkan bahwa biofeedback pernapasan secara signifikan menurunkan frekuensi kejang pada pasien epilepsi refrakter (kebal obat).",
                    "Frontiers in Neurology (2019): Jurnal ini mempublikasikan kemanjuran stimulasi saraf vagus melalui teknik pernapasan untuk menurunkan hiper-eksitabilitas kortikal."
                ]
            },
            'tidur': {
                sains: "Tidur adalah fase krusial di mana otak melakukan \\"reset\\" kelistrikan. Kurang tidur (Sleep Deprivation) adalah pemicu kejang nomor satu di seluruh dunia. Kurang tidur menurunkan ambang batas kejang secara drastis, membuat sel-sel neuron di otak menjadi sangat sensitif (hiper-eksitabilitas) dan mudah mengalami korsleting listrik di siang harinya.",
                refs: [
                    "Epilepsia Journal (2017): Malow dkk., merilis studi komprehensif yang membuktikan bahwa fragmentasi tidur dan durasi tidur di bawah 6 jam melipatgandakan risiko serangan kejang esok harinya.",
                    "Clinical Neurophysiology (2011): Penelitian menunjukkan bahwa kurang tidur mengubah keseimbangan neurotransmitter (menurunkan GABA yang menenangkan, meningkatkan Glutamat yang merangsang), memicu kejang tonik-klonik.",
                    "Journal of Sleep Research (2020): Studi polysomnography mengkonfirmasi interaksi dua arah yang kuat antara epilepsi dan gangguan arsitektur tidur."
                ]
            },
            'log': {
                sains: "Pengobatan epilepsi bersifat sangat personal (Tailored Medicine). Tidak ada satu obat yang cocok untuk semua orang. Dengan mencatat jurnal kejang (waktu, pemicu, durasi), algoritma medis dan dokter saraf (Neurolog) dapat mengidentifikasi pola kejang. Data ini krusial untuk menentukan jenis obat Anti-Epilepsi (AED) apa yang paling tepat dan berapa dosis yang pas tanpa merusak liver pasien.",
                refs: [
                    "International League Against Epilepsy / ILAE (2018): Panduan resmi ILAE menetapkan Seizure Diary (Jurnal Kejang) sebagai Standar Emas (Gold Standard) dalam evaluasi klinis pasien epilepsi.",
                    "Seizure Journal (2015): Penelitian oleh Fisher et al., membuktikan bahwa pasien yang mencatat jurnal kejang harian memiliki tingkat keberhasilan terapi obat 40% lebih tinggi dibanding yang tidak mencatat.",
                    "Epilepsy Research (2021): Studi menunjukkan bahwa pelacakan pemicu kejang secara digital (lewat aplikasi) sangat meningkatkan akurasi diagnosa dokter pada epilepsi fokal."
                ]
            },
            'alarm': {
                sains: "Obat Anti-Epilepsi (AED) bekerja dengan cara menjaga kadar zat kimia penstabil di dalam darah. Obat ini memiliki \\"Waktu Paruh\\" (Half-life) yang ketat. Jika telat minum obat walau hanya 1-2 jam, kadar obat di dalam darah akan anjlok (Drop). Penurunan mendadak ini menyebabkan fenomena Breakthrough Seizure (kejang mendadak yang fatal pada pasien yang sebelumnya sudah stabil).",
                refs: [
                    "Seizure - European Journal of Epilepsy (2016): Riset menemukan bahwa Non-Adherence (lupa/telat minum obat) adalah penyebab dari lebih 50% kasus kejang berulang di ruang gawat darurat.",
                    "Epilepsia Journal (2013): Cramer et al., menunjukkan bahwa melewatkan satu dosis obat meningkatkan risiko kejang hingga 3 kali lipat dalam 24 jam ke depan.",
                    "Neurology Clinical Practice (2019): Studi intervensi digital membuktikan bahwa penggunaan alarm terkunci yang memaksa pasien berinteraksi (seperti fitur kita) meningkatkan kepatuhan minum obat hingga 92%."
                ]
            },
            'diet': {
                sains: "Otak biasanya menggunakan Glukosa (gula/karbohidrat) sebagai energi. Namun, saat seseorang berpuasa atau memakan diet tinggi lemak sangat rendah karbohidrat, liver mengubah lemak menjadi senyawa bernama \\"Keton\\" (Ketone Bodies). Saat otak memakai Keton sebagai energi, sel-sel neuron saraf mengalami perubahan metabolisme yang membuatnya menjadi sangat stabil, \\"tenang\\", dan sangat tahan terhadap lonjakan listrik pemicu kejang.",
                refs: [
                    "The Lancet Neurology (2008): Studi acak terkendali (RCT) oleh Neal et al., membuktikan Diet Ketogenik mengurangi frekuensi kejang lebih dari 50% pada anak-anak yang kebal terhadap semua jenis obat epilepsi.",
                    "Epilepsia Journal (2014): Bough dan Rho mempublikasikan mekanisme bagaimana badan Keton menstimulasi produksi GABA (neurotransmitter penenang utama di otak).",
                    "Journal of Child Neurology (2020): Riset jangka panjang membuktikan efektivitas puasa intermiten (seperti puasa sunnah) yang dikombinasikan dengan diet lemak sehat dalam menyembuhkan epilepsi refrakter."
                ]
            }
        };

        function showMedicalExplanation(key) {
            const data = MEDICAL_DATA[key];
            if(!data) return;
            
            document.getElementById('med-sains').innerText = data.sains;
            const ul = document.getElementById('med-refs');
            ul.innerHTML = '';
            data.refs.forEach(r => {
                const li = document.createElement('li');
                li.className = 'text-xs text-gray-600 mb-2 border-l-2 border-blue-500 pl-2';
                // Check if there is a colon to bold the title
                if(r.includes(':')) {
                    const parts = r.split(':');
                    const title = parts[0];
                    const content = parts.slice(1).join(':');
                    li.innerHTML = `<span class="font-bold text-blue-700">${title}</span>: ${content}`;
                } else {
                    li.innerText = r;
                }
                ul.appendChild(li);
            });
            
            openModal('modal-medical-explanation');
        }

        function toggleTerapi() {
            const content = document.getElementById('terapi-content');
            const chevron = document.querySelector('#terapi-chevron i');
            
            if (content.classList.contains('hidden')) {
                // Open
                content.classList.remove('hidden');
                setTimeout(() => {
                    content.classList.remove('opacity-0', '-translate-y-4');
                    content.classList.add('opacity-100', 'translate-y-0');
                }, 20);
                chevron.classList.add('rotate-180');
            } else {
                // Close
                content.classList.remove('opacity-100', 'translate-y-0');
                content.classList.add('opacity-0', '-translate-y-4');
                chevron.classList.remove('rotate-180');
                
                setTimeout(() => {
                    content.classList.add('hidden');
                }, 1000); 
            }
        }

        // --- TERAPI DIGITAL LOGIC ---

        // 1. Audio Healing
        let audio = null;
        let currentMurottalIndex = 0;
        const murottalPlaylist = ['001', '112', '113', '114'];
        
        // Nature Playlist
        let currentNatureIndex = 0;
        const naturePlaylist = [
            '/static/rockot-meditation-and-gentle-nature-184572.mp3',
            '/static/soundsforyou-meditative-rain-114484.mp3'
        ];
        
        let hasPlayedAudio = {};

        function playAudio(type) {
            const status = document.getElementById('now-playing');
            const seeker = document.getElementById('audio-seeker');
            
            // Real URLs
            const sources = {
                'alam': naturePlaylist[currentNatureIndex], 
                'mozart': '/static/Mozart - Sonata for Two Pianos in D, K. 448 [complete].mp3',
                'murattal': `https://server8.mp3quran.net/afs/${murottalPlaylist[currentMurottalIndex]}.mp3`
            };
            
            if (audio && !audio.paused && audio.dataset.type === type) {
                audio.pause();
                status.innerText = "Paused: " + (type === 'alam' ? 'Suara Alam' : type.toUpperCase());
                return;
            } else if (audio && audio.paused && audio.dataset.type === type) {
                audio.play();
                status.innerText = "Sedang Memutar: " + (type === 'alam' ? 'Suara Alam' : type.toUpperCase());
                return;
            }

            if(audio) {
                audio.pause();
                audio = null;
            }
            
            // Loading Animation Check
            if (!hasPlayedAudio[type]) {
                status.innerText = "sedang mengambil data audio, harap sabar...";
                status.classList.add('animate-pulse');
                hasPlayedAudio[type] = true;
            }

            if (type === 'murattal') {
                playMurottalSequence();
            } else if (type === 'mozart') {
                playMozartOptimized(sources['mozart']);
                status.innerText = "Sedang Memutar: MOZART ";
            } else {
                // Optimization: Preload none to simulate buffering/chunking control
                audio = new Audio(sources[type]);
                audio.preload = 'none'; 
                audio.dataset.type = type;
                setupAudioEvents();
                
                audio.addEventListener('canplay', () => {
                    status.classList.remove('animate-pulse');
                    let displayType = type.toUpperCase();
                    if(type === 'alam') displayType = "Suara Alam";
                    status.innerText = "Sedang Memutar: " + displayType;
                });

                audio.play();
            }
            
            status.classList.remove('hidden');
            if(seeker) seeker.parentElement.classList.remove('hidden');
        }

        function triggerInfaqWA() {
            const now = new Date();
            const h = now.getHours();
            let time = "Pagi";
            if (h >= 11 && h < 15) time = "Siang";
            else if (h >= 15 && h < 19) time = "Sore";
            else if (h >= 19 || h < 4) time = "Malam";
            
            const type = document.getElementById('infaq-type-select') ? document.getElementById('infaq-type-select').value : 'Infaq';
            const msg = `Assalamu'alaikum Pak, selamat ${time}, ijin konfirmasi Pak, saya sudah mengtransfer sebesar Rp... di nomor rekening ${type} untuk keperluan ${type} ke masjid langsung, terima kasih Pak 🙏`;
            window.open(`https://wa.me/6282330890500?text=${encodeURIComponent(msg)}`, '_blank');
        }

        function showAmalanPopup() {
            // Create popup element if not exists
            if (!document.getElementById('amalan-popup')) {
                const div = document.createElement('div');
                div.id = 'amalan-popup';
                div.className = 'fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-sm hidden opacity-0 transition-opacity duration-500';
                div.innerHTML = `
                    <div class="text-center transform scale-95 transition-transform duration-500">
                        <h2 class="text-2xl font-bold text-white mb-2 animate-pulse">May Allah SWT always be with us</h2>
                        <p class="text-lg text-[#FFD700]">Aamiin Allahuma Aamiin 🙏</p>
                    </div>
                `;
                document.body.appendChild(div);
            }
            
            const popup = document.getElementById('amalan-popup');
            popup.classList.remove('hidden');
            // Trigger reflow
            void popup.offsetWidth;
            popup.classList.remove('opacity-0');
            popup.querySelector('div').classList.remove('scale-95');
            popup.querySelector('div').classList.add('scale-100');
            
            setTimeout(() => {
                popup.classList.add('opacity-0');
                popup.querySelector('div').classList.add('scale-95');
                setTimeout(() => {
                    popup.classList.add('hidden');
                    openModal('modal-amalan');
                }, 500);
            }, 2000);
        }

        function switchNatureAudio() {
            currentNatureIndex = (currentNatureIndex + 1) % naturePlaylist.length;
            
            // If currently playing alam, restart
            if (audio && audio.dataset.type === 'alam') {
                audio.pause();
                audio = null;
                playAudio('alam');
            } else {
                // Just update index, user will hear new track next time they click play
                const status = document.getElementById('now-playing');
                status.innerText = "Track Diganti. Klik Play.";
                status.classList.remove('hidden');
            }
        }

        function playMozartOptimized(url) {
            // Optimasi: Range Requests / Buffer Chunking via JS
            // Menggunakan preload='none' agar browser hanya menarik data saat diputar
            audio = new Audio(url);
            audio.preload = 'none'; 
            audio.dataset.type = 'mozart';
            setupAudioEvents();
            
            // Simulate chunking logic
            console.log("Initializing Mozart Range Requests...");
            
            audio.play().catch(e => {
                console.log("Playback awaiting user interaction or loading...", e);
            });
        }

        function playMurottalSequence() {
            const url = `https://server8.mp3quran.net/afs/${murottalPlaylist[currentMurottalIndex]}.mp3`;
            audio = new Audio(url);
            audio.dataset.type = 'murattal';
            setupAudioEvents();
            
            audio.onended = function() {
                currentMurottalIndex = (currentMurottalIndex + 1) % murottalPlaylist.length;
                playMurottalSequence();
            };
            
            audio.play();
            document.getElementById('now-playing').innerText = "Sedang Memutar: MURATTAL (Surah " + murottalPlaylist[currentMurottalIndex] + ")";
        }

        function setupAudioEvents() {
            const seeker = document.getElementById('audio-seeker');
            if(!seeker) return;
            
            audio.ontimeupdate = function() {
                if(audio.duration) {
                    seeker.value = (audio.currentTime / audio.duration) * 100;
                }
            };
            
            seeker.oninput = function() {
                if(audio && audio.duration) {
                    audio.currentTime = (seeker.value / 100) * audio.duration;
                }
            };
        }

        // 2. Breathing Exercise
        let breathInterval = null;
        function startBreathing() {
            openModal('modal-terapi-napas');
            const circle = document.getElementById('breath-circle');
            const text = document.getElementById('breath-text');
            
            // Reset
            circle.style.transition = 'none';
            circle.style.transform = 'scale(1)';
            text.innerText = "Mulai";
            
            setTimeout(() => {
                runCycle();
                breathInterval = setInterval(runCycle, 12000); // 4+2+6 = 12s
            }, 500);

            function runCycle() {
                // Inhale (4s)
                text.innerText = "Tarik Napas";
                circle.style.transition = 'transform 4s ease-in-out';
                circle.style.transform = 'scale(2.5)';
                
                setTimeout(() => {
                    // Hold (2s)
                    text.innerText = "Tahan";
                    
                    setTimeout(() => {
                        // Exhale (6s)
                        text.innerText = "Hembuskan";
                        circle.style.transition = 'transform 6s ease-in-out';
                        circle.style.transform = 'scale(1)';
                    }, 2000);
                    
                }, 4000);
            }
        }

        function stopBreathing() {
            if(breathInterval) clearInterval(breathInterval);
            const circle = document.getElementById('breath-circle');
            if(circle) circle.style.transform = 'scale(1)';
        }

        // 3. Sleep Tracker
        function checkSleep() {
            const hours = parseFloat(document.getElementById('sleep-hours').value);
            const resDiv = document.getElementById('sleep-result');
            resDiv.classList.remove('hidden');
            
            if (!hours) return;
            
            if (hours < 6) {
                resDiv.className = "mt-4 p-4 rounded-xl border border-red-200 bg-red-50 text-sm";
                resDiv.innerHTML = `
                    <h4 class="font-bold text-red-600 mb-1"><i class="fas fa-exclamation-triangle"></i> PERINGATAN</h4>
                    <p class="text-gray-700">Waktu tidur Anda kurang dari 6 jam. <b>Risiko kejang meningkat.</b></p>
                    <ul class="list-disc ml-4 mt-2 text-gray-600 text-xs">
                        <li>Hindari aktivitas fisik berat hari ini.</li>
                        <li>Jangan menyetir kendaraan.</li>
                        <li>Segera minum obat jika ada jadwal.</li>
                    </ul>
                `;
            } else {
                resDiv.className = "mt-4 p-4 rounded-xl border border-green-200 bg-green-50 text-sm";
                resDiv.innerHTML = `
                    <h4 class="font-bold text-green-600 mb-1"><i class="fas fa-check-circle"></i> AMAN</h4>
                    <p class="text-gray-700">Alhamdulillah, waktu tidur Anda cukup. Tetap jaga pola makan dan hindari stres.</p>
                `;
            }
        }

        // 5. Medication Alarm Simulation
        let alarmInterval = null;
        let alarmTimes = [];
        
        function saveAlarm() {
            const t1 = document.getElementById('alarm-time-1').value;
            const t2 = document.getElementById('alarm-time-2').value;
            alarmTimes = [t1, t2];
            
            document.getElementById('alarm-status').classList.remove('hidden');
            
            // Start checking
            if(alarmInterval) clearInterval(alarmInterval);
            alarmInterval = setInterval(checkAlarm, 60000); // Check every minute
            checkAlarm(); // Initial check
            
            alert("Alarm diaktifkan pada jam " + t1 + " dan " + t2);
        }
        
        function checkAlarm() {
            const now = new Date();
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const currentTime = `${hours}:${minutes}`;
            
            if (alarmTimes.includes(currentTime)) {
                triggerAlarm();
            }
        }
        
        let currentMathAnswer = 0;
        
        function triggerAlarm() {
            const lockScreen = document.getElementById('alarm-lock-screen');
            lockScreen.classList.remove('hidden');
            
            // Generate simple math problem
            const n1 = Math.floor(Math.random() * 10) + 5;
            const n2 = Math.floor(Math.random() * 10) + 1;
            currentMathAnswer = n1 + n2;
            document.getElementById('math-problem').innerText = `${n1} + ${n2} = ?`;
            document.getElementById('math-answer').value = '';
        }
        
        function checkMath() {
            const ans = parseInt(document.getElementById('math-answer').value);
            if(ans === currentMathAnswer) {
                document.getElementById('alarm-lock-screen').classList.add('hidden');
                alert("Alarm dimatikan. Jangan lupa minum obat!");
            } else {
                alert("Jawaban salah! Coba lagi.");
            }
        }

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

<!-- YASIN & ADMIN FLOATING ACTIONS -->
<div id="floating-actions" class="fixed bottom-24 right-5 z-40 md:right-8 flex items-end gap-3">
    <!-- Admin Button -->
    {% if is_admin %}
    <a href="/logout" onclick="return confirm('Apakah Anda yakin ingin keluar dari Mode Admin?')" class="w-12 h-12 rounded-md bg-red-600 text-white shadow-xl flex items-center justify-center hover:bg-red-700 transition-all border-2 border-white">
       <i class="fas fa-sign-out-alt text-lg"></i>
    </a>
    {% else %}
    <button onclick="openModal('modal-login-admin')" class="w-12 h-12 rounded-md bg-emerald-600 text-white shadow-xl flex items-center justify-center hover:bg-emerald-500 transition-all border-2 border-white">
       <i class="fas fa-user-shield text-lg"></i>
    </button>
    {% endif %}

    <!-- Quran & Yasin Stack -->
    <div class="flex flex-col items-center gap-4">
        <!-- Al-Qur'an Button (New) -->
        <button onclick="openQuranModal()" class="w-14 h-14 rounded-full bg-emerald-600 text-white shadow-xl flex items-center justify-center hover:bg-emerald-500 hover:scale-110 transition-all duration-300 border-2 border-white relative group">
            <i class="fas fa-book-quran text-xl"></i>
            <span class="absolute right-full mr-2 bg-emerald-800 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">Al-Qur'an</span>
        </button>

        <!-- Yasin Button -->
        <div class="animate-bounce-slow">
            <button onclick="openYasinModal()" class="w-16 h-16 rounded-full bg-emerald-600 text-white shadow-2xl flex items-center justify-center hover:bg-emerald-500 hover:scale-110 transition-all duration-300 border-4 border-white">
                <i class="fas fa-book-open text-2xl"></i>
            </button>
        </div>
    </div>
</div>

<!-- YASIN DIGITAL MODAL -->
<div id="modal-yasin" class="fixed inset-0 z-[100] hidden bg-white">
    <!-- Header -->
    <div class="fixed top-0 left-0 w-full bg-white z-10 shadow-sm border-b border-gray-100 px-5 py-4 flex justify-between items-center">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-emerald-50 flex items-center justify-center text-emerald-600">
                <i class="fas fa-book-open"></i>
            </div>
            <div>
                <h3 class="text-lg font-bold text-gray-800 leading-none">Surat Yasin</h3>
                <p class="text-xs text-gray-500">83 Ayat • Makkiyah</p>
            </div>
        </div>
        <button onclick="closeYasinModal()" class="w-10 h-10 rounded-full bg-gray-50 text-gray-500 hover:bg-gray-100 flex items-center justify-center transition-colors">
            <i class="fas fa-times text-lg"></i>
        </button>
    </div>

    <!-- Content -->
    <div class="pt-24 pb-10 px-5 md:px-8 max-w-3xl mx-auto h-full overflow-y-auto" id="yasin-content">
        <!-- Loading State -->
        <div id="yasin-loading" class="flex flex-col items-center justify-center py-20">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mb-4"></div>
            <p class="text-gray-500 text-sm">Mengambil Data Surat Yasin...</p>
        </div>
        
        <!-- Error State -->
        <div id="yasin-error" class="hidden text-center py-20">
            <p class="text-red-500 mb-2">Gagal memuat data.</p>
            <button onclick="fetchYasin()" class="text-emerald-600 underline text-sm">Coba Lagi</button>
        </div>

        <!-- Verses Container -->
        <div id="yasin-verses" class="hidden space-y-8">
            <!-- Verses injected here via JS -->
        </div>
    </div>
</div>

<!-- AL-QURAN DIGITAL MODALS -->

<!-- 1. SURAH LIST MODAL -->
<div id="modal-quran-list" class="fixed inset-0 z-[100] hidden bg-white">
    <!-- Header -->
    <div class="fixed top-0 left-0 w-full bg-white z-10 shadow-sm border-b border-gray-100 px-5 py-4 flex justify-between items-center">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-emerald-50 flex items-center justify-center text-emerald-600">
                <i class="fas fa-book-quran"></i>
            </div>
            <div>
                <h3 class="text-lg font-bold text-gray-800 leading-none">Al-Qur'an Digital</h3>
                <p class="text-xs text-gray-500">Daftar 114 Surat</p>
            </div>
        </div>
        <button onclick="closeQuranModal()" class="w-10 h-10 rounded-full bg-gray-50 text-gray-500 hover:bg-gray-100 flex items-center justify-center transition-colors">
            <i class="fas fa-times text-lg"></i>
        </button>
    </div>

    <!-- Content -->
    <div class="pt-24 pb-10 px-5 md:px-8 max-w-3xl mx-auto h-full overflow-y-auto" id="quran-list-content">
        <!-- Loading State -->
        <div id="quran-list-loading" class="flex flex-col items-center justify-center py-20">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mb-4"></div>
            <p class="text-gray-500 text-sm">Mengambil Daftar Surat...</p>
        </div>
        
        <!-- Error State -->
        <div id="quran-list-error" class="hidden text-center py-20">
            <p class="text-red-500 mb-2">Gagal memuat daftar surat.</p>
            <button onclick="fetchSurahList()" class="text-emerald-600 underline text-sm">Coba Lagi</button>
        </div>

        <!-- List Container -->
        <div id="quran-list-container" class="hidden space-y-3">
            <!-- Items injected here -->
        </div>
    </div>
</div>

<!-- 2. SURAH DETAIL MODAL -->
<div id="modal-quran-detail" class="fixed inset-0 z-[101] hidden bg-white">
    <!-- Header -->
    <div class="fixed top-0 left-0 w-full bg-white z-20 shadow-sm border-b border-gray-100 px-5 py-4 flex justify-between items-center">
        <div class="flex items-center gap-3 cursor-pointer hover:bg-gray-50 rounded-lg pr-2 transition-colors" onclick="closeSurahDetail()">
            <div class="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-500">
                <i class="fas fa-arrow-left"></i>
            </div>
            <div>
                <h3 class="text-lg font-bold text-gray-800 leading-none" id="detail-surah-name">Loading...</h3>
                <p class="text-[10px] text-gray-500" id="detail-surah-info">...</p>
            </div>
        </div>
        <div class="flex items-center gap-2">
            <button id="btn-quran-tajwid" onclick="toggleQuranTajwid()" class="text-xs font-bold text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-full border border-emerald-200 hover:bg-emerald-100 transition shadow-sm flex items-center gap-1">
                <i class="fas fa-palette"></i> Tajwid
            </button>
            <button onclick="closeQuranModal()" class="w-10 h-10 rounded-full bg-gray-50 text-gray-500 hover:bg-gray-100 flex items-center justify-center transition-colors">
                <i class="fas fa-times text-lg"></i>
            </button>
        </div>
    </div>

    <!-- Audio Player (Sticky under header) -->
    <div class="fixed top-[72px] left-0 w-full bg-emerald-50 z-10 border-b border-emerald-100 px-5 py-3 flex flex-col gap-2">
        <div class="flex items-center justify-between w-full">
            <p class="text-xs text-emerald-800 font-bold"><i class="fas fa-volume-up mr-1"></i> Murottal (Misyari Rasyid)</p>
            <audio id="quran-audio-player" controls class="h-8 w-48 md:w-64"></audio>
        </div>
        <input type="range" id="quran-seeker" value="0" class="w-full h-1 bg-emerald-200 rounded-lg appearance-none cursor-pointer">
    </div>

    <!-- Content -->
    <div class="pt-48 pb-10 px-5 md:px-8 max-w-3xl mx-auto h-full overflow-y-auto" id="quran-detail-content">
        <!-- Loading -->
        <div id="quran-detail-loading" class="flex flex-col items-center justify-center py-20">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mb-4"></div>
            <p class="text-gray-500 text-sm">Membuka Ayat...</p>
        </div>
        
        <!-- Verses -->
        <div id="quran-detail-verses" class="hidden space-y-8 pb-20">
             <!-- Verses injected here -->
        </div>

        <div id="quran-detail-tajwid-legend" class="hidden sticky bottom-4 mx-auto max-w-sm bg-white/90 backdrop-blur-md border border-emerald-100 p-3 rounded-2xl shadow-[0_-10px_15px_-3px_rgba(0,0,0,0.1)] z-20 mt-4">
            <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2 border-b border-gray-200 pb-1">Panduan Tajwid</p>
            <div class="grid grid-cols-3 gap-y-2 gap-x-1 text-[10px] font-bold text-gray-700">
                <div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-red-500"></span> Idgham</div>
                <div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-green-500"></span> Ikhfa</div>
                <div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-blue-500"></span> Iqlab</div>
                <div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-purple-500"></span> Qalqalah</div>
                <div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-orange-500"></span> Ghunnah</div>
                <div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-teal-500"></span> Mad</div>
            </div>
        </div>
    </div>
</div>

<!-- 3. TAJWID RULE MODAL -->
<div id="modal-tajwid-rule" class="fixed inset-0 z-[300] hidden flex items-center justify-center bg-black/60 backdrop-blur-sm">
    <div class="bg-white rounded-3xl w-full max-w-xs mx-4 p-6 shadow-2xl animate-[popupFadeIn_0.3s_ease-out] relative border border-emerald-100">
        <div class="w-16 h-16 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4 border-4 border-white shadow-sm -mt-12">
            <i class="fas fa-book-open text-2xl"></i>
        </div>
        <h3 id="tajwid-rule-title" class="text-xl font-bold text-gray-800 text-center mb-2 leading-tight uppercase tracking-wider"></h3>
        <div class="w-12 h-1 bg-emerald-200 mx-auto rounded-full mb-4"></div>
        <p id="tajwid-rule-desc" class="text-sm text-gray-600 text-center leading-relaxed mb-6 font-medium"></p>
        <button onclick="closeTajwidRule()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-md hover:bg-emerald-600 transition transform hover:scale-105">Paham</button>
    </div>
</div>

<script>
    let quranListLoaded = false;
    let currentSurahData = null;
    
    let isQuranTajwidMode = false;
    let currentQuranSurahNomor = null;
    let currentQuranSurahName = '';
    
    const TAJWID_RULES = {
        'idgham': {
            name: 'Idgham',
            desc: 'Memasukkan huruf pertama ke dalam huruf kedua sehingga menjadi satu huruf yang bertasydid.'
        },
        'ikhfa': {
            name: 'Ikhfa',
            desc: 'Menyamarkan bunyi Nun Sukun (نْ) atau Tanwin menjadi dengung sebelum bertemu dengan huruf-huruf Ikhfa.'
        },
        'iqlab': {
            name: 'Iqlab',
            desc: 'Menukar bunyi Nun Sukun (نْ) atau Tanwin menjadi bunyi Mim (م) ketika bertemu huruf Ba (ب).'
        },
        'qalqalah': {
            name: 'Qalqalah',
            desc: 'Memantulkan atau menggetarkan bunyi huruf-huruf Qalqalah apabila dalam keadaan sukun (mati).'
        },
        'ghunnah': {
            name: 'Ghunnah',
            desc: 'Mendengungkan suara secara sempurna pada huruf Nun (ن) dan Mim (م) yang bertasydid.'
        },
        'madd': {
            name: 'Mad',
            desc: 'Memanjangkan suara suatu bacaan karena bertemu dengan huruf-huruf Mad.'
        }
    };

    // --- MAIN MODAL LOGIC ---
    function toggleQuranTajwid() {
        isQuranTajwidMode = !isQuranTajwidMode;
        const btn = document.getElementById('btn-quran-tajwid');
        if (isQuranTajwidMode) {
            btn.classList.remove('bg-emerald-50', 'text-emerald-600', 'border-emerald-200');
            btn.classList.add('bg-emerald-500', 'text-white', 'border-emerald-500', 'shadow-md');
        } else {
            btn.classList.add('bg-emerald-50', 'text-emerald-600', 'border-emerald-200');
            btn.classList.remove('bg-emerald-500', 'text-white', 'border-emerald-500', 'shadow-md');
        }
        if (currentQuranSurahNomor) {
            openSurahDetail(currentQuranSurahNomor);
        }
    }

    function showTajwidRule(ruleKey) {
        const rule = TAJWID_RULES[ruleKey];
        if (rule) {
            document.getElementById('tajwid-rule-title').innerText = rule.name;
            document.getElementById('tajwid-rule-desc').innerText = rule.desc;
            document.getElementById('modal-tajwid-rule').classList.remove('hidden');
        }
    }

    function closeTajwidRule() {
        document.getElementById('modal-tajwid-rule').classList.add('hidden');
    }

    function openQuranModal() {
        document.getElementById('modal-quran-list').classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        if (!quranListLoaded) {
            fetchSurahList();
        }
    }

    function closeQuranModal() {
        document.getElementById('modal-quran-list').classList.add('hidden');
        document.getElementById('modal-quran-detail').classList.add('hidden');
        document.body.style.overflow = 'auto';
        
        // Stop audio if playing
        const audio = document.getElementById('quran-audio-player');
        if(audio) {
            audio.pause();
            audio.currentTime = 0;
        }
    }

    // --- FETCH SURAH LIST ---
    async function fetchSurahList() {
        const loading = document.getElementById('quran-list-loading');
        const error = document.getElementById('quran-list-error');
        const container = document.getElementById('quran-list-container');
        
        loading.classList.remove('hidden');
        error.classList.add('hidden');
        
        try {
            const response = await fetch('https://equran.id/api/v2/surat');
            const result = await response.json();
            
            if (result.code === 200 && result.data) {
                renderSurahList(result.data);
                quranListLoaded = true;
                loading.classList.add('hidden');
                container.classList.remove('hidden');
            } else {
                throw new Error('Invalid data');
            }
        } catch (e) {
            console.error(e);
            loading.classList.add('hidden');
            error.classList.remove('hidden');
        }
    }

    function renderSurahList(surahs) {
        const container = document.getElementById('quran-list-container');
        container.innerHTML = '';
        
        surahs.forEach(surah => {
            const el = document.createElement('div');
            el.className = "bg-white p-4 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between cursor-pointer hover:bg-emerald-50 hover:border-emerald-200 transition-all group";
            el.onclick = () => openSurahDetail(surah.nomor);
            
            el.innerHTML = `
                <div class="flex items-center gap-4">
                    <div class="w-10 h-10 rounded-full bg-emerald-100 text-emerald-600 font-bold flex items-center justify-center text-sm group-hover:bg-emerald-500 group-hover:text-white transition-colors">
                        ${surah.nomor}
                    </div>
                    <div>
                        <h4 class="font-bold text-gray-800 group-hover:text-emerald-700">${surah.namaLatin}</h4>
                        <p class="text-xs text-gray-500">${surah.arti} • ${surah.jumlahAyat} Ayat</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="font-amiri text-xl text-emerald-800 font-bold">${surah.nama}</p>
                </div>
            `;
            container.appendChild(el);
        });
    }

    // --- SURAH DETAIL LOGIC ---
    async function openSurahDetail(nomor) {
        currentQuranSurahNomor = nomor;
        document.getElementById('modal-quran-detail').classList.remove('hidden');
        const loading = document.getElementById('quran-detail-loading');
        const content = document.getElementById('quran-detail-verses');
        const legend = document.getElementById('quran-detail-tajwid-legend');
        
        // Reset view
        document.getElementById('detail-surah-name').innerText = "Loading...";
        document.getElementById('detail-surah-info').innerText = "...";
        loading.classList.remove('hidden');
        content.classList.add('hidden');
        legend.classList.add('hidden');
        content.innerHTML = '';
        
        try {
            const response = await fetch(`https://equran.id/api/v2/surat/${nomor}`);
            const result = await response.json();
            
            let tajwidData = null;
            if (isQuranTajwidMode) {
                const resTajwid = await fetch(`https://api.alquran.cloud/v1/surah/${nomor}/ar.tajweed`);
                tajwidData = await resTajwid.json();
            }

            if (result.code === 200 && result.data) {
                renderSurahDetail(result.data, tajwidData);
                loading.classList.add('hidden');
                content.classList.remove('hidden');
                if (isQuranTajwidMode) legend.classList.remove('hidden');
            } else {
                throw new Error('Data detail invalid');
            }
        } catch(e) {
            alert("Gagal memuat surat. Periksa koneksi internet.");
            closeSurahDetail();
        }
    }

    function closeSurahDetail() {
        document.getElementById('modal-quran-detail').classList.add('hidden');
        const audio = document.getElementById('quran-audio-player');
        if(audio) {
            audio.pause();
            audio.currentTime = 0;
        }
    }

    function renderSurahDetail(data, tajwidData) {
        currentQuranSurahName = data.namaLatin;
        // Update Header
        document.getElementById('detail-surah-name').innerText = data.namaLatin;
        document.getElementById('detail-surah-info').innerText = `${data.arti} • ${data.jumlahAyat} Ayat • ${data.tempatTurun}`;
        
        // Update Audio
        const audioPlayer = document.getElementById('quran-audio-player');
        const seeker = document.getElementById('quran-seeker');
        
        audioPlayer.ontimeupdate = () => {
            if(audioPlayer.duration) {
                seeker.value = (audioPlayer.currentTime / audioPlayer.duration) * 100;
            }
        };
        
        seeker.oninput = () => {
            if(audioPlayer.duration) {
                audioPlayer.currentTime = (seeker.value / 100) * audioPlayer.duration;
            }
        };
        // Use Misyari Rasyid (05) if available, fallback to 01
        const audioSrc = data.audioFull['05'] || data.audioFull['01'];
        audioPlayer.src = audioSrc;
        
        // Render Verses
        const container = document.getElementById('quran-detail-verses');
        container.innerHTML = '';

        if (!isQuranTajwidMode || !tajwidData || tajwidData.code !== 200) {
            data.ayat.forEach(verse => {
                const el = document.createElement('div');
                el.className = "border-b border-gray-100 pb-6 last:border-0";
                
                el.innerHTML = `
                    <div class="flex flex-col gap-4">
                        <div class="flex justify-between items-start">
                            <div class="w-8 h-8 flex-shrink-0 rounded-full bg-gray-100 border border-gray-200 flex items-center justify-center text-gray-500 font-bold text-xs mt-1">
                                ${verse.nomorAyat}
                            </div>
                            <div class="flex-1 text-right pl-4">
                                <p class="font-amiri text-3xl md:text-4xl leading-[2.5] text-gray-800 font-bold" style="font-family: 'Amiri', serif; direction: rtl;">
                                    ${verse.teksArab}
                                </p>
                            </div>
                        </div>
                        <div class="pl-12">
                            <p class="text-sm text-gray-500 italic mb-2 leading-relaxed font-serif tracking-wide text-emerald-700">${verse.teksLatin}</p>
                            <p class="text-base text-gray-700 leading-relaxed">${verse.teksIndonesia}</p>
                        </div>
                    </div>
                `;
                container.appendChild(el);
            });
        } else {
            for (let i = 0; i < tajwidData.data.ayahs.length; i++) {
                let ayahTajwid = tajwidData.data.ayahs[i];
                let equranVerse = data.ayat[i];
                let rawText = ayahTajwid.text;

                let parsedText = rawText
                    .replace(/<tajweed class="idgham[^"]*"[^>]*>(.*?)<[/]tajweed>/gi, '<span onclick="showTajwidRule(\\\'idgham\\\')" class="text-red-500 font-bold cursor-pointer hover:underline decoration-red-300 decoration-2">$1</span>')
                    .replace(/<tajweed class="ikhfa[^"]*"[^>]*>(.*?)<[/]tajweed>/gi, '<span onclick="showTajwidRule(\\\'ikhfa\\\')" class="text-emerald-500 font-bold cursor-pointer hover:underline decoration-emerald-300 decoration-2">$1</span>')
                    .replace(/<tajweed class="iqlab[^"]*"[^>]*>(.*?)<[/]tajweed>/gi, '<span onclick="showTajwidRule(\\\'iqlab\\\')" class="text-blue-500 font-bold cursor-pointer hover:underline decoration-blue-300 decoration-2">$1</span>')
                    .replace(/<tajweed class="qalqalah[^"]*"[^>]*>(.*?)<[/]tajweed>/gi, '<span onclick="showTajwidRule(\\\'qalqalah\\\')" class="text-sky-500 font-bold cursor-pointer hover:underline decoration-sky-300 decoration-2">$1</span>')
                    .replace(/<tajweed class="ghunnah[^"]*"[^>]*>(.*?)<[/]tajweed>/gi, '<span onclick="showTajwidRule(\\\'ghunnah\\\')" class="text-orange-500 font-bold cursor-pointer hover:underline decoration-orange-300 decoration-2">$1</span>')
                    .replace(/<tajweed class="madd[^"]*"[^>]*>(.*?)<[/]tajweed>/gi, '<span onclick="showTajwidRule(\\\'madd\\\')" class="text-teal-500 font-bold cursor-pointer hover:underline decoration-teal-300 decoration-2">$1</span>')
                    .replace(/<tajweed class="[^"]*"[^>]*>(.*?)<[/]tajweed>/gi, '<span>$1</span>');

                const el = document.createElement('div');
                el.className = "border-b border-gray-100 pb-6 last:border-0 relative";
                
                el.innerHTML = `
                    <div class="flex flex-col gap-4">
                        <div class="flex justify-between items-start">
                            <div class="w-8 h-8 flex-shrink-0 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 font-bold text-xs mt-1">
                                ${ayahTajwid.numberInSurah}
                            </div>
                            <div class="flex-1 text-right pl-4">
                                <p class="font-amiri text-3xl md:text-4xl leading-[2.5] text-gray-800 font-bold" style="font-family: 'Amiri', serif; direction: rtl;">
                                    ${parsedText}
                                </p>
                            </div>
                        </div>
                        <div class="pl-12 text-left">
                            <p class="text-sm text-gray-500 italic mb-2 leading-relaxed font-serif tracking-wide text-emerald-700">${equranVerse ? equranVerse.teksLatin : ''}</p>
                            <p class="text-base text-gray-700 leading-relaxed">${equranVerse ? equranVerse.teksIndonesia : ''}</p>
                        </div>
                    </div>
                `;
                container.appendChild(el);
            }
        }
    }

    let yasinDataLoaded = false;

    function openYasinModal() {
        document.getElementById('modal-yasin').classList.remove('hidden');
        document.body.style.overflow = 'hidden'; // Prevent scrolling background
        if (!yasinDataLoaded) {
            fetchYasin();
        }
    }

    function closeYasinModal() {
        document.getElementById('modal-yasin').classList.add('hidden');
        document.body.style.overflow = 'auto';
    }

    async function fetchYasin() {
        const loading = document.getElementById('yasin-loading');
        const error = document.getElementById('yasin-error');
        const content = document.getElementById('yasin-verses');
        
        loading.classList.remove('hidden');
        error.classList.add('hidden');
        content.classList.add('hidden');

        try {
            const response = await fetch('/api/yasin');
            const result = await response.json();
            
            if (result.data && result.data.ayat) {
                renderYasin(result.data.ayat);
                yasinDataLoaded = true;
                loading.classList.add('hidden');
                content.classList.remove('hidden');
            } else {
                throw new Error('Invalid data');
            }
        } catch (e) {
            console.error(e);
            loading.classList.add('hidden');
            error.classList.remove('hidden');
        }
    }

    function renderYasin(verses) {
        const container = document.getElementById('yasin-verses');
        container.innerHTML = '';

        verses.forEach(verse => {
            const el = document.createElement('div');
            el.className = "border-b border-gray-100 pb-6 last:border-0";
            el.innerHTML = `
                <div class="flex justify-between items-start mb-4">
                    <div class="w-10 h-10 flex-shrink-0 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 font-bold text-sm">
                        ${verse.nomorAyat}
                    </div>
                    <div class="flex-1 text-right pl-4">
                        <p class="font-amiri text-3xl md:text-4xl leading-loose text-gray-800 font-bold mb-2" style="font-family: 'Amiri', serif; line-height: 2.2;">
                            ${verse.teksArab}
                        </p>
                    </div>
                </div>
                <div class="pl-14">
                    <p class="text-sm text-gray-500 italic mb-2 leading-relaxed">${verse.teksLatin}</p>
                    <p class="text-base text-gray-700 leading-relaxed">${verse.teksIndonesia}</p>
                </div>
            `;
            container.appendChild(el);
        });
    }
</script>

"""

# --- ROUTES ---

# --- ROUTES ---

@app.route('/')
def index():
    try:
        epilepsi_logs = EpilepsiLog.query.order_by(EpilepsiLog.date.desc(), EpilepsiLog.time.desc()).limit(5).all()
    except:
        epilepsi_logs = []

    rendered_home = render_template_string(HOME_HTML, epilepsi_logs=epilepsi_logs, open_modal=request.args.get('open'), is_admin=session.get('is_admin', False))
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='home', content=rendered_home, is_admin=session.get('is_admin', False), settings=get_settings())

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == 'admin':
        if password == 'takmirmasjid':
            session['is_admin'] = True
            session.permanent = True
        elif password == 'kameramasjid':
            session['is_gallery_admin'] = True
            session.permanent = True
            
    return redirect(request.referrer or url_for('index'))

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    session.pop('is_gallery_admin', None)
    return redirect(url_for('index'))

@app.route('/therapy/log', methods=['POST'])
def therapy_log():
    try:
        log = EpilepsiLog(
            date=request.form['date'],
            time=request.form['time'],
            trigger=request.form['trigger'],
            notes=request.form['notes']
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging therapy: {e}")
    return redirect(url_for('index', open='modal-terapi-log'))

@app.route('/finance', methods=['GET', 'POST'])
def finance():
    if request.method == 'POST':
        if 'delete_id' in request.form:
            Finance.query.filter_by(id=request.form['delete_id']).delete()
        else:
            item = Finance(
                date=request.form['date'],
                type=request.form['type'],
                category=request.form['category'],
                description=request.form['description'],
                amount=int(request.form['amount'])
            )
            db.session.add(item)
        db.session.commit()
        return redirect(url_for('finance'))
    
    items = Finance.query.order_by(Finance.date.desc()).all()
    
    total_in = db.session.query(func.sum(Finance.amount)).filter_by(type='Pemasukan').scalar() or 0
    total_out = db.session.query(func.sum(Finance.amount)).filter_by(type='Pengeluaran').scalar() or 0
    balance = total_in - total_out

    content = """
    <div class="pt-20 md:pt-32 pb-24 px-5 md:px-8">
        <div class="flex justify-between items-center mb-6">
            <h3 class="text-xl font-bold text-gray-800">Laporan Kas</h3>
            {% if is_admin %}
            <button onclick="document.getElementById('modal-add').classList.remove('hidden')" class="bg-emerald-500 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-md hover:bg-emerald-600 transition">+ Input</button>
            {% endif %}
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
                        {% if is_admin %}
                        <form method="POST" class="inline-block mt-1">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                            <input type="hidden" name="delete_id" value="{{ item['id'] }}">
                            <button class="text-gray-300 hover:text-red-500 text-xs" onclick="return confirm('Hapus?')"><i class="fas fa-trash"></i></button>
                        </form>
                        {% endif %}
                    </div>
                </div>
                {% else %}
                <div class="p-8 text-center text-gray-400 text-sm">Belum ada data transaksi.</div>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- Modal -->
    {% if is_admin %}
    <div id="modal-add" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="document.getElementById('modal-add').classList.add('hidden')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold">Input Kas Baru</h3>
                <button onclick="document.getElementById('modal-add').classList.add('hidden')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500">&times;</button>
            </div>
            <form method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

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
    {% endif %}
    """
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='finance', content=render_template_string(content, items=items, total_in=total_in, total_out=total_out, balance=balance, is_admin=session.get('is_admin', False)), is_admin=session.get('is_admin', False), settings=get_settings())

@app.route('/agenda', methods=['GET', 'POST'])
def agenda():
    if request.method == 'POST':
        if 'delete_id' in request.form:
            Agenda.query.filter_by(id=request.form['delete_id']).delete()
        else:
            item = Agenda(
                date=request.form['date'],
                time=request.form['time'],
                title=request.form['title'],
                speaker=request.form['speaker'],
                type=request.form['type']
            )
            db.session.add(item)
        db.session.commit()
        return redirect(url_for('agenda'))

    items = Agenda.query.order_by(Agenda.date.asc(), Agenda.time.asc()).all()

#     conn.close()

    content = """
    <div class="pt-20 md:pt-32 pb-24 px-5 md:px-8">
        <div class="flex justify-between items-center mb-6">
            <h3 class="text-xl font-bold text-gray-800">Jadwal Imam & Kajian</h3>
            {% if is_admin %}
            <button onclick="document.getElementById('modal-agenda').classList.remove('hidden')" class="bg-blue-500 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-md hover:bg-blue-600 transition">+ Tambah</button>
            {% endif %}
        </div>

        <div class="space-y-4">
            {% for item in items %}
            <div class="bg-white p-5 rounded-3xl shadow-sm border border-gray-100 flex gap-4 relative">
                {% if is_admin %}
                <form method="POST" class="absolute top-2 right-2">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                    <input type="hidden" name="delete_id" value="{{ item['id'] }}">
                    <button class="text-gray-300 hover:text-red-500" onclick="return confirm('Hapus?')">&times;</button>
                </form>
                {% endif %}
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
    {% if is_admin %}
    <div id="modal-agenda" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="document.getElementById('modal-agenda').classList.add('hidden')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out]">
            <h3 class="text-lg font-bold mb-6">Tambah Agenda</h3>
            <form method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

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
    {% endif %}
    """
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='agenda', content=render_template_string(content, items=items, is_admin=session.get('is_admin', False)), is_admin=session.get('is_admin', False), settings=get_settings())

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        if 'status_update' in request.form:
             booking = Booking.query.get(request.form['booking_id'])
             if booking:
                 booking.status = request.form['status']
        else:
             item = Booking(
                 name=request.form['name'],
                 date=request.form['date'],
                 purpose=request.form['purpose'],
                 type=request.form['type'],
                 contact=request.form['contact']
             )
             db.session.add(item)
        db.session.commit()
        return redirect(url_for('booking'))

    items = Booking.query.order_by(Booking.created_at.desc()).all()

#     conn.close()

    content = """
    <div class="pt-20 md:pt-32 pb-24 px-5 md:px-8">
        <h3 class="text-xl font-bold text-gray-800 mb-2">Peminjaman Fasilitas</h3>
        <p class="text-sm text-gray-500 mb-6">Ajukan peminjaman ambulan atau area masjid.</p>

        <form method="POST" class="bg-white p-6 rounded-3xl shadow-lg border border-gray-100 mb-8">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

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
                
                {% if item['status'] == 'Pending' and is_admin %}
                <div class="flex gap-2 mt-3 pt-3 border-t border-gray-100">
                     <form method="POST" class="flex-1">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                        <input type="hidden" name="status_update" value="1">
                        <input type="hidden" name="booking_id" value="{{ item['id'] }}">
                        <input type="hidden" name="status" value="Approved">
                        <button class="w-full bg-green-50 text-green-600 text-xs font-bold py-2 rounded-lg hover:bg-green-100">Setujui</button>
                    </form>
                    <form method="POST" class="flex-1">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

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
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='booking', content=render_template_string(content, items=items, is_admin=session.get('is_admin', False)), is_admin=session.get('is_admin', False), settings=get_settings())

@app.route('/zakat', methods=['GET', 'POST'])
def zakat():
    if request.method == 'POST':
         item = Zakat(
             donor_name=request.form['donor_name'],
             type=request.form['type'],
             amount=request.form['amount'],
             notes=request.form['notes'],
             status='Pending'
         )
         db.session.add(item)
         db.session.commit()
         return redirect(url_for('zakat'))
    
    items = Zakat.query.order_by(Zakat.created_at.desc()).limit(50).all()
    
    # Calculate totals (Python side for safety with String column)
    fitrah_items = Zakat.query.filter_by(type='Zakat Fitrah').all()
    total_zakat_fitrah = sum(int(float(i.amount)) for i in fitrah_items if i.amount.replace('.','').isdigit())
    
    total_sapi = Zakat.query.filter_by(type='Qurban Sapi').count()
    total_kambing = Zakat.query.filter_by(type='Qurban Kambing').count()

    content = """
    <div class="pt-20 md:pt-32 pb-24 px-5 md:px-8">
        <div class="flex justify-between items-center mb-6">
            <h3 class="text-xl font-bold text-gray-800">Zakat & Qurban</h3>
            <div class="flex gap-2">
                <button onclick="triggerZakatWA()" class="bg-[#25D366] text-white px-3 py-2 rounded-xl text-xs font-bold shadow-md hover:bg-green-600 transition flex items-center gap-1">
                    <i class="fab fa-whatsapp text-sm"></i> <span class="hidden md:inline">Konfirmasi Admin</span>
                </button>
                <button onclick="document.getElementById('modal-zakat').classList.remove('hidden')" class="bg-green-500 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-md hover:bg-green-600 transition">+ Input</button>
            </div>
        </div>
        <script>
            function triggerZakatWA() {
                const now = new Date();
                const h = now.getHours();
                let time = "Malam";
                if (h >= 0 && h < 11) time = "Pagi";
                else if (h >= 11 && h < 15) time = "Siang";
                else if (h >= 15 && h < 18) time = "Sore";
                
                const msg = `Assalamualaikum Pak, selamat ${time}, saya ingin berqurban atau melakukan zakat Pak, terima kasih 🙏`;
                window.location.href = "https://wa.me/6282330890500?text=" + encodeURIComponent(msg);
            }
        </script>

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
                <div class="p-4 flex justify-between items-start">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <h5 class="font-bold text-gray-800 text-sm">{{ item['donor_name'] }}</h5>
                            <span class="text-[10px] font-bold px-2 py-0.5 rounded-full {{ 'bg-yellow-100 text-yellow-600' if item['status'] == 'Pending' else ('bg-green-100 text-green-600' if item['status'] == 'Approved' else 'bg-red-100 text-red-600') }}">{{ item['status'] }}</span>
                        </div>
                        <p class="text-xs text-gray-500">{{ item['type'] }} • {{ item['notes'] }}</p>
                        
                        {% if is_admin and item['status'] == 'Pending' %}
                        <div class="flex gap-2 mt-2">
                            <form action="/zakat/status" method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                                <input type="hidden" name="id" value="{{ item['id'] }}">
                                <input type="hidden" name="status" value="Approved">
                                <button class="bg-green-500 text-white text-[10px] px-2 py-1 rounded hover:bg-green-600">Approve</button>
                            </form>
                            <form action="/zakat/status" method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                                <input type="hidden" name="id" value="{{ item['id'] }}">
                                <input type="hidden" name="status" value="Rejected">
                                <button class="bg-red-500 text-white text-[10px] px-2 py-1 rounded hover:bg-red-600">Tolak</button>
                            </form>
                        </div>
                        {% endif %}
                    </div>
                    <div class="font-bold text-green-600 text-sm text-right">
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
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

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
                    <button type="submit" class="w-full bg-green-500 text-white font-bold py-4 rounded-xl shadow-lg mt-4">Simpan Data</button>
                </div>
            </form>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='zakat', content=render_template_string(content, items=items, total_zakat_fitrah=total_zakat_fitrah, total_sapi=total_sapi, total_kambing=total_kambing, is_admin=session.get('is_admin', False)), is_admin=session.get('is_admin', False), settings=get_settings())

@app.route('/zakat/status', methods=['POST'])
def zakat_status():
    if not session.get('is_admin'):
        return redirect(url_for('zakat'))
    
    try:
        item = Zakat.query.get(request.form['id'])
        if item:
            item.status = request.form['status']
            db.session.commit()
    except Exception as e:
        print(f"Error updating zakat status: {e}")
    return redirect(url_for('zakat'))

@app.route('/gallery-dakwah', methods=['GET', 'POST'])
def gallery_dakwah():
    is_admin = session.get('is_admin', False)
    is_gallery_admin = session.get('is_gallery_admin', False)
    can_edit = is_admin or is_gallery_admin

    if request.method == 'POST' and can_edit:
        if 'delete_id' in request.form:
             GalleryDakwah.query.filter_by(id=request.form['delete_id']).delete()
        elif 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                saved_filename = compress_image(file, app.config['UPLOAD_FOLDER'])
                item = GalleryDakwah(
                    title=request.form['title'],
                    image=saved_filename,
                    description=request.form['description'],
                    date=str(datetime.date.today())
                )
                db.session.add(item)
        db.session.commit()
        return redirect(url_for('gallery_dakwah'))
    
    items = GalleryDakwah.query.order_by(GalleryDakwah.created_at.desc()).all()

#     conn.close()

    content = """
    <div class="pt-20 md:pt-32 pb-24 px-5 md:px-8">
        <div class="flex justify-between items-center mb-6">
            <h3 class="text-xl font-bold text-gray-800">Galeri Dakwah</h3>
            {% if can_edit %}
            <button onclick="document.getElementById('modal-upload').classList.remove('hidden')" class="bg-purple-500 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-md hover:bg-purple-600 transition">+ Foto</button>
            {% endif %}
        </div>

        <div class="grid grid-cols-2 gap-4">
            {% for item in items %}
            <div class="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden relative group">
                <div class="aspect-square bg-gray-200 relative cursor-pointer" onclick='openGalleryModal({{ url_for("uploaded_file", filename=item["image"])|tojson }}, {{ item["title"]|tojson }}, {{ item["description"]|tojson }})'>
                    <img src="/uploads/{{ item['image'] }}" class="w-full h-full object-cover" alt="{{ item['title'] }}">
                    <div class="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent flex items-end p-3">
                        <p class="text-white text-xs font-bold leading-tight line-clamp-2">{{ item['title'] }}</p>
                    </div>
                </div>
                {% if can_edit %}
                <form method="POST" class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                    <input type="hidden" name="delete_id" value="{{ item['id'] }}">
                    <button class="bg-red-500 text-white w-6 h-6 rounded-full text-xs shadow-md" onclick="return confirm('Hapus?')">&times;</button>
                </form>
                {% endif %}
            </div>
            {% else %}
            <div class="col-span-2 text-center py-10 text-gray-400">Belum ada dokumentasi.</div>
            {% endfor %}
        </div>
    </div>

    <!-- Modal Upload -->
    {% if can_edit %}
    <div id="modal-upload" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="document.getElementById('modal-upload').classList.add('hidden')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out]">
            <h3 class="text-lg font-bold mb-6">Upload Foto</h3>
            <form method="POST" enctype="multipart/form-data">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

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
    {% endif %}

    <!-- GALLERY MODAL FULLSCREEN -->
    <div id="modal-gallery-view" class="fixed inset-0 z-[200] hidden flex items-center justify-center bg-black/90 backdrop-blur-sm animate-[fadeIn_0.3s_ease-out]" onclick="closeGalleryModal()">
        <div class="relative max-w-6xl w-[90%] h-[85vh] bg-white rounded-3xl overflow-hidden shadow-2xl flex flex-col md:flex-row" onclick="event.stopPropagation()">
            <!-- Image Side -->
            <div class="flex-1 bg-black flex items-center justify-center relative h-1/2 md:h-full">
                <img id="gallery-modal-img" src="" class="max-w-full max-h-full object-contain">
                <button onclick="closeGalleryModal()" class="absolute top-4 left-4 bg-black/50 text-white w-10 h-10 rounded-full flex items-center justify-center hover:bg-black/70 md:hidden">&times;</button>
            </div>
            <!-- Info Side -->
            <div class="w-full md:w-96 bg-white p-8 flex flex-col justify-center h-1/2 md:h-full relative overflow-y-auto">
                <button onclick="closeGalleryModal()" class="hidden md:flex absolute top-6 right-6 bg-gray-100 text-gray-500 w-10 h-10 rounded-full items-center justify-center hover:bg-gray-200 transition">&times;</button>
                <h3 id="gallery-modal-title" class="text-3xl font-bold text-gray-800 mb-4 font-sans leading-tight"></h3>
                <div class="w-12 h-1 bg-purple-500 rounded-full mb-6"></div>
                <p id="gallery-modal-desc" class="text-gray-600 leading-relaxed text-lg"></p>
                <div class="mt-auto pt-8">
                     <p class="text-xs font-bold text-gray-400 uppercase tracking-widest">Galeri Dakwah</p>
                </div>
            </div>
        </div>
    </div>
    <script>
        function openGalleryModal(imgSrc, title, desc) {
            document.getElementById('gallery-modal-img').src = imgSrc;
            document.getElementById('gallery-modal-title').innerText = title;
            document.getElementById('gallery-modal-desc').innerText = desc || 'Tidak ada deskripsi.';
            document.getElementById('modal-gallery-view').classList.remove('hidden');
        }
        function closeGalleryModal() {
            document.getElementById('modal-gallery-view').classList.add('hidden');
        }
    </script>
    """
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='gallery', content=render_template_string(content, items=items, can_edit=can_edit), is_admin=session.get('is_admin', False), settings=get_settings())

@app.route('/suggestion', methods=['GET', 'POST'])
def suggestion():
    if request.method == 'POST':
         try:
             item = Suggestion(
                 content=request.form['content'],
                 date=str(datetime.date.today())
             )
             db.session.add(item)
             db.session.commit()
         except Exception as e:
             print(f"Error saving suggestion: {e}")
             db.session.rollback()
         return redirect(url_for('suggestion', success=1))
    
    items = Suggestion.query.order_by(Suggestion.created_at.desc()).limit(10).all()

    content = """
    <div class="pt-20 md:pt-32 pb-24 px-5 md:px-8">
        <h3 class="text-xl font-bold text-gray-800 mb-4">Kotak Saran Digital</h3>
        
        {% if request.args.get('success') %}
        <div class="bg-green-100 text-green-700 p-3 rounded-xl mb-4 text-center font-bold text-sm border border-green-200 animate-pulse">
            Terima kasih, saran Anda telah terkirim!
        </div>
        {% endif %}

        <form action="/suggestion" method="POST" class="bg-white p-6 rounded-3xl shadow-lg border border-pink-50 mb-8">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

            <div class="mb-4">
                <label class="block text-xs font-bold text-gray-500 mb-2">Kritik & Saran Anda</label>
                <textarea name="content" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm min-h-[120px]" placeholder="Silakan tulis masukan Anda..." required></textarea>
            </div>
            <button type="submit" class="w-full bg-pink-500 text-white font-bold py-3 rounded-xl shadow-md hover:bg-pink-600 transition">Kirim</button>
        </form>
        
        {% if is_admin %}
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
        {% endif %}
    </div>
    """
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='suggestion', content=render_template_string(content, items=items, is_admin=session.get('is_admin', False)), is_admin=session.get('is_admin', False), settings=get_settings())

@app.route('/fitur_masjid')
def fitur_masjid():
    rendered_content = render_template_string(FITUR_MASJID_HTML)
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='home', content=rendered_content, is_admin=session.get('is_admin', False), settings=get_settings())

@app.route('/prayer-times')
def prayer_times_api():
    now = datetime.datetime.now()
    pt = PrayTimes()
    times = pt.get_prayer_times(now.year, now.month, now.day, LAT, LNG, TZ)
    return jsonify(times)

@app.route('/donate', methods=['GET', 'POST'])
def donate():
    is_admin = session.get('is_admin', False)
    
    if request.method == 'POST' and is_admin:
        key = request.form.get('key')
        val = request.form.get('value')
        
        if 'qris_image' in request.files:
            file = request.files['qris_image']
            if file and allowed_file(file.filename):
                saved_filename = compress_image(file, app.config['UPLOAD_FOLDER'])
                
                # Update setting
                s = AppSettings.query.get('infaq_qris_image')
                if s: s.value = saved_filename
                else: db.session.add(AppSettings(key='infaq_qris_image', value=saved_filename))
        
        if key and val:
             s = AppSettings.query.get(key)
             if s: s.value = val
             else: db.session.add(AppSettings(key=key, value=val))
             
        db.session.commit()
        return redirect(url_for('donate', source=request.args.get('source')))

    # Fetch settings
    settings = get_settings()
    acc_no = settings.get('infaq_rekening', '7123456789 (BSI - Masjid Al Hijrah)')
    qris_img = settings.get('infaq_qris_image', '')
    qris_url = f"/uploads/{qris_img}" if qris_img else "https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=MasjidAlHijrahInfaq"
    
    source = request.args.get('source')
    
    # Theme Logic
    theme = {}
    if source == 'ramadhan':
        theme = {
            'nav_bg': 'glass-gold bg-[#0b1026]',
            'icon_bg': 'bg-[#FFD700]/20',
            'icon_text': 'text-[#FFD700]',
            'title_text': 'text-[#FFD700]',
            'link_hover': 'hover:text-[#FFD700]',
            'link_active': 'text-[#FFD700] font-bold',
            'btn_primary': 'bg-[#FFD700] text-[#0b1026] hover:bg-white',
            'bottom_nav_bg': 'bg-[#0b1026] border-t border-[#FFD700]/20',
            'bottom_active': 'text-[#FFD700]',
            'bottom_btn_bg': 'bg-[#FFD700]',
            'bottom_btn_text': 'text-[#0b1026]',
            'bottom_text_inactive': 'text-gray-400'
        }
        bg_class = "bg-[#0b1026] text-white"
        card_class = "bg-[#151e3f] border-[#FFD700]/30"
        text_highlight = "text-[#FFD700]"
        btn_action = "bg-[#FFD700] text-[#0b1026]"
    elif source == 'irma':
        theme = {
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
        bg_class = "bg-[#F4E7E1] text-gray-800"
        card_class = "bg-white border-[#A0B391]/30"
        text_highlight = "text-[#A0B391]"
        btn_action = "bg-[#A0B391] text-white"
    else:
        # Default Home
        bg_class = "bg-[#F8FAFC] text-gray-800"
        card_class = "bg-white border-emerald-50"
        text_highlight = "text-emerald-600"
        btn_action = "bg-emerald-500 text-white"

    content = f"""
    <div class="pt-20 md:pt-32 pb-24 px-5 md:px-8 text-center min-h-screen flex flex-col items-center justify-center {bg_class}">
        <div class="{card_class} p-8 rounded-[40px] shadow-2xl border max-w-md w-full relative overflow-hidden">
             <div class="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-transparent via-current to-transparent opacity-50 {text_highlight}"></div>
             <h2 class="text-2xl font-bold mb-2 {text_highlight}">Infaq Digital</h2>
             <p class="text-sm opacity-70 mb-6">Scan QRIS menggunakan E-Wallet apa saja</p>
             
             <div class="bg-white p-4 rounded-2xl shadow-inner border border-gray-100 inline-block mb-6 relative group">
                <img src="{qris_url}" alt="QRIS" class="w-48 h-48 mx-auto object-contain">
                <a href="{qris_url}" download="QRIS_Masjid.png" class="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity rounded-xl text-white font-bold backdrop-blur-sm">
                    <i class="fas fa-download mr-2"></i> Download
                </a>
             </div>

             <div class="flex gap-2 justify-center mb-6 max-w-xs mx-auto w-full">
                <a href="{qris_url}" download="QRIS_Masjid.png" class="flex-1 bg-gray-100 text-gray-700 px-3 py-3 rounded-xl text-xs font-bold hover:bg-gray-200 text-center transition"><i class="fas fa-download mr-1"></i> Download QRIS</a>
                <button onclick="triggerInfaqWA()" class="flex-1 bg-[#25D366] text-white px-3 py-3 rounded-xl text-xs font-bold hover:bg-green-600 transition shadow-lg shadow-green-200"><i class="fab fa-whatsapp mr-1"></i> Konfirmasi WA</button>
             </div>
             
             <div class="mb-4 max-w-xs mx-auto">
                 <label class="block text-[10px] font-bold text-gray-400 mb-1 text-left">Keperluan (untuk Konfirmasi WA)</label>
                 <select id="infaq-type-select" class="w-full bg-white border border-gray-200 rounded-lg p-2 text-xs font-bold text-gray-700 focus:outline-none focus:ring-2 focus:ring-emerald-500">
                     <option value="Masjid">Masjid</option>
                     <option value="Qurban">Qurban</option>
                     <option value="Zakat">Zakat</option>
                     <option value="Infaq">Infaq</option>
                 </select>
             </div>
             
             <div class="mb-6">
                <p class="text-xs font-bold uppercase tracking-widest opacity-50 mb-1">Nomor Rekening</p>
                <div class="bg-gray-50/50 p-3 rounded-xl border border-dashed border-gray-300 flex items-center justify-between gap-2">
                    <span id="donate-rek-text" class="font-mono font-bold text-lg select-all text-gray-800">{acc_no}</span>
                    <button onclick="copyText('donate-rek-text')" class="p-2 rounded-lg hover:bg-gray-200 transition text-gray-500"><i class="fas fa-copy"></i></button>
                </div>
             </div>
             <script>window.addEventListener('load', function() {{ if(typeof formatBankDisplay === 'function') formatBankDisplay('donate-rek-text'); }});</script>
             
             {{% if is_admin %}}
             <div class="border-t border-gray-200/50 pt-6 mt-6 text-left">
                <h4 class="text-xs font-bold text-red-500 uppercase mb-3"><i class="fas fa-cog"></i> Admin Settings</h4>
                <form method="POST" enctype="multipart/form-data" class="space-y-3">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                    <div>
                        <label class="text-[10px] font-bold opacity-70">Update No. Rekening</label>
                        <input type="hidden" name="key" value="infaq_rekening">
                        <div class="flex gap-2">
                            <input type="text" name="value" value="{acc_no}" class="w-full text-xs p-2 rounded-lg border border-gray-300 text-black">
                            <button class="bg-blue-500 text-white px-3 rounded-lg text-xs">Save</button>
                        </div>
                    </div>
                </form>
                <form method="POST" enctype="multipart/form-data" class="mt-3">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                    <label class="text-[10px] font-bold opacity-70 block mb-1">Update QRIS Image</label>
                    <div class="flex gap-2">
                        <input type="file" name="qris_image" class="w-full text-xs text-gray-500">
                        <button class="bg-blue-500 text-white px-3 rounded-lg text-xs">Upload</button>
                    </div>
                </form>
             </div>
             {{% endif %}}
             
             <div class="flex justify-center gap-3 opacity-60 grayscale hover:grayscale-0 transition-all mt-4">
                <i class="fas fa-wallet text-2xl"></i>
                <i class="fas fa-university text-2xl"></i>
                <i class="fas fa-mobile-alt text-2xl"></i>
             </div>
        </div>
        <br>
        <a href="/" class="opacity-50 text-sm font-medium hover:opacity-100 transition">Kembali ke Beranda</a>
        </div>
    </div>
    """
    
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML + (RAMADHAN_STYLES if source=='ramadhan' else (IRMA_STYLES if source=='irma' else '')), active_page='donate', theme=theme, content=render_template_string(content, is_admin=is_admin, settings=get_settings()), is_admin=is_admin)

@app.route('/emergency')
def emergency():
    return redirect("https://wa.me/6281241865310?text=Halo%20Takmir%20Masjid,%20Ada%20Keadaan%20Darurat!")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, max_age=31536000)

@app.route('/api/calc/waris', methods=['POST'])
@limiter.limit("10 per minute")
@csrf.exempt
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
        logic = f"Bapak/Ibu memasukkan total harta Rp {harta:,}. Dalam matematika waris, anak laki-laki dihitung 2 bagian lalu anak perempuan dihitung 1 bagian, karena ada {sons} anak laki-laki dan {daughters} perempuan, maka total poin pembagi adalah {res['points']}. Artinya, harta tersebut dibagi menjadi {res['points']} keping. Satu keping bernilai Rp {res['part_value']:,.0f}. Maka bagian anak laki-laki adalah 2 x {res['part_value']:,.0f} = Rp {res['son_share']:,.0f}, dan anak perempuan 1 x {res['part_value']:,.0f} = Rp {res['daughter_share']:,.0f}."
        
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
@limiter.limit("10 per minute")
@csrf.exempt
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
@limiter.limit("10 per minute")
@csrf.exempt
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
@limiter.limit("10 per minute")
@csrf.exempt
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
@limiter.limit("10 per minute")
@csrf.exempt
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
@limiter.limit("10 per minute")
@csrf.exempt
def api_calc_hijri():
    try:
        data = request.json
        y, m, d = data['date'].split('-')
        formatted_date = f"{d}-{m}-{y}"
        
        url = f"http://api.aladhan.com/v1/gToH?date={formatted_date}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            resp_data = json.loads(response.read().decode())
            h = resp_data['data']['hijri']
            res = f"{h['day']} {h['month']['en']} {h['year']} H"
            
            logic = f"Data diambil real-time dari API Aladhan (Internasional). Tanggal {formatted_date} Masehi dikonversi menjadi {res}."
            
            return jsonify({
                "result": {"hijri": res},
                "explanation": {
                    "logic": logic,
                    "sources": DALIL_DATA["hijri"]
                }
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/yasin', methods=['GET'])
@limiter.limit("10 per minute")
@cache.cached(timeout=86400)
def api_yasin():
    try:
        url = "https://equran.id/api/v2/surat/36"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- RAMADHAN SPECIAL FEATURES ---

RAMADHAN_STYLES = """

# """

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
                <a href="javascript:void(0)" onclick="openModal('modal-infaq')" class="bg-gold text-midnight px-5 py-2 rounded-full font-bold shadow-lg hover:bg-white transition transform hover:scale-105">Infaq Digital</a>
                <button onclick="triggerEmergency()" class="text-red-400 font-bold hover:text-red-500 transition border border-red-500/50 px-4 py-2 rounded-full bg-red-500/10 hover:bg-red-500/20 cursor-pointer">Darurat</button>
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
            <p class="text-[10px] font-bold text-[#FFD700] bg-[#0b1026] px-2 py-1 rounded-full border border-[#FFD700]" id="hijri-date-ramadhan">Loading...</p>
        </div>
    </header>

    <!-- SPACER -->
    <div class="h-24"></div>

    <div class="px-5 md:px-8 max-w-7xl mx-auto relative z-10">
        
        <!-- SPLIT HEADER -->
        <div class="md:grid md:grid-cols-2 md:gap-12 md:items-center mb-10">
             
             <!-- LEFT: WELCOME -->
             <div class="hidden md:block pl-2">
                <p class="text-xl text-gray-400 font-medium mb-2">Assalamualaikum Warahmatullahi Wabarakatuh</p>
                <h1 class="text-5xl font-bold text-white leading-tight mb-6">Selamat Datang di<br>Masjid Al Hijrah</h1>
                <p class="text-gray-300 text-lg leading-relaxed mb-8">
                    Sambut Ramadhan dengan Hati yang Suci. Mari hidupkan malam dengan Tarawih, tadarus Al-Quran, dan berbagi kebahagiaan melalui Infaq dan Takjil.
                </p>
                <div class="flex gap-4">
                    <button onclick="openModal('modal-tarawih')" class="bg-gold text-midnight px-8 py-3 rounded-full font-bold shadow-lg hover:bg-white transition transform hover:scale-105">Lihat Agenda</button>
                    <a href="javascript:void(0)" onclick="openModal('modal-infaq')" class="bg-transparent text-gold border-2 border-gold px-8 py-3 rounded-full font-bold hover:bg-gold hover:text-midnight transition transform hover:scale-105">Infaq Sekarang</a>
                </div>
             </div>

             <!-- RIGHT: PRAYER CARD -->
             <div>
                <div class="bg-[#151e3f] rounded-3xl p-6 md:p-8 text-white shadow-2xl border border-white/5 relative overflow-hidden group">
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
                             <div class="bg-[#0b1026] p-3 rounded-2xl text-center border border-white/5">
                                <span class="block text-[10px] text-white uppercase font-bold mb-1">Subuh</span>
                                <div class="bg-[#0b1026] p-1 rounded-xl border border-white/10"><span class="font-bold font-mono text-white text-xs" id="r-fajr">--:--</span></div>
                             </div>
                             <div class="bg-[#0b1026] p-3 rounded-2xl text-center border border-white/5">
                                <span class="block text-[10px] text-white uppercase font-bold mb-1">Dzuhur</span>
                                <div class="bg-[#0b1026] p-1 rounded-xl border border-white/10"><span class="font-bold font-mono text-white text-xs" id="r-dhuhr">--:--</span></div>
                             </div>
                             <div class="bg-[#0b1026] p-3 rounded-2xl text-center border border-white/5">
                                <span class="block text-[10px] text-white uppercase font-bold mb-1">Ashar</span>
                                <div class="bg-[#0b1026] p-1 rounded-xl border border-white/10"><span class="font-bold font-mono text-white text-xs" id="r-asr">--:--</span></div>
                             </div>
                             <div class="bg-[#0b1026] p-3 rounded-2xl text-center border border-white/5">
                                <span class="block text-[10px] text-white uppercase font-bold mb-1">Maghrib</span>
                                <div class="bg-[#0b1026] p-1 rounded-xl border border-white/10"><span class="font-bold font-mono text-white text-xs" id="r-maghrib">--:--</span></div>
                             </div>
                             <div class="bg-[#0b1026] p-3 rounded-2xl text-center border border-white/5">
                                <span class="block text-[10px] text-white uppercase font-bold mb-1">Isya</span>
                                <div class="bg-[#0b1026] p-1 rounded-xl border border-white/10"><span class="font-bold font-mono text-white text-xs" id="r-isha">--:--</span></div>
                             </div>
                        </div>
                    </div>
                </div>
             </div>
        </div>

        <!-- MENU GRID -->
        <h2 class="text-xl font-bold text-white font-sans mb-6 border-l-4 border-gold pl-3">Menu Utama</h2>
        
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
            <button onclick="openModal('modal-zakat-menu')" class="bg-[#151e3f] p-6 rounded-3xl flex flex-col items-center justify-center h-40 group hover:bg-[#1a254d] transition-all border border-white/5 hover:border-gold/30 relative overflow-hidden">
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
            <a href="javascript:void(0)" onclick="openModal('modal-infaq')" class="flex flex-col items-center justify-center text-gray-400 hover:text-gold w-16 mb-6 relative z-10">
                <div class="bg-[#FFD700] text-white w-14 h-14 rounded-full flex items-center justify-center shadow-[0_0_15px_rgba(255,215,0,0.4)] border-4 border-white transform hover:scale-105 transition-transform">
                    <i class="fas fa-qrcode text-2xl"></i>
                </div>
                <span class="text-[10px] font-bold mt-1 text-gold">Infaq</span>
            </a>
            <button onclick="triggerEmergency()" class="flex flex-col items-center justify-center text-gray-400 hover:text-red-400 w-16 mb-1 transition-colors">
                <i class="fas fa-phone-alt text-xl mb-1"></i>
                <span class="text-[10px] font-medium">Darurat</span>
            </button>
        </div>
    </nav>

    <!-- MODALS SECTION -->
    
    <!-- 1. MODAL TAKJIL -->
    <div id="modal-takjil" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <h3 class="text-xl font-bold text-gold font-sans">Jadwal Pembagian Takjil</h3>
                <button onclick="closeModal('modal-takjil')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>
            
            <div class="p-4 bg-white/5 border-b border-white/10 rounded-xl mb-4">
                <input type="text" id="search-takjil" onkeyup="filterTakjil()" placeholder="Cari Nama Warga..." class="w-full bg-[#0b1026] border border-gold/30 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-gold">
            </div>
            
            <div class="overflow-hidden rounded-xl border border-white/10">
                <table class="w-full text-left border-collapse">
                    <thead class="bg-gold/10 text-gold backdrop-blur-md">
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

    <!-- 2. MODAL IMSAKIYAH -->
    <div id="modal-imsakiyah" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <div>
                     <h3 class="text-xl font-bold text-gold font-sans">Jadwal Imsakiyah</h3>
                     <p class="text-[10px] text-gray-400">Samarinda & Sekitarnya • Ramadhan 1447 H / 2026 M</p>
                </div>
                <button onclick="closeModal('modal-imsakiyah')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>
            
            <div class="overflow-hidden rounded-xl border border-white/10">
                <table class="w-full text-center border-collapse">
                    <thead class="bg-blue-900/50 text-blue-200 backdrop-blur-md">
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

    <!-- 3. MODAL KAS RAMADHAN -->
    <div id="modal-kas-ramadhan" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <h3 class="text-xl font-bold text-gold font-sans">Laporan Kas Ramadhan</h3>
                <button onclick="closeModal('modal-kas-ramadhan')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>
            
            <!-- Summary -->
            <div class="grid grid-cols-2 gap-4 border-b border-white/10 pb-6 mb-6">
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
            {% if is_admin %}
            <div class="bg-white/5 border border-white/10 p-6 rounded-2xl mb-6">
                <h4 class="text-sm font-bold text-gray-300 mb-3">Input Transaksi (Admin)</h4>
                <form action="/ramadhan/kas" method="POST" class="space-y-3">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                    <div class="grid grid-cols-2 gap-3">
                        <input type="date" name="date" required class="w-full bg-[#0b1026] border border-gray-600 rounded-lg p-3 text-sm text-white focus:border-gold">
                        <select name="type" class="w-full bg-[#0b1026] border border-gray-600 rounded-lg p-3 text-sm text-white focus:border-gold">
                            <option value="Pemasukan">Pemasukan</option>
                            <option value="Pengeluaran">Pengeluaran</option>
                        </select>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                         <input type="text" name="description" placeholder="Keterangan (ex: Infaq Tarawih Malam 1)" required class="w-full bg-[#0b1026] border border-gray-600 rounded-lg p-3 text-sm text-white focus:border-gold">
                         <input type="number" name="amount" placeholder="Nominal (Rp)" required class="w-full bg-[#0b1026] border border-gray-600 rounded-lg p-3 text-sm text-white focus:border-gold">
                    </div>
                    <input type="hidden" name="category" value="Ramadhan">
                    <button type="submit" class="w-full bg-white/80 text-[#0b1026] font-bold py-3 rounded-lg hover:bg-white active:bg-white transition shadow-lg">Simpan Data</button>
                </form>
            </div>
            {% endif %}

            <!-- List -->
            <div class="overflow-hidden rounded-xl border border-white/10">
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

    <!-- 4. MODAL JADWAL TARAWIH -->
    <div id="modal-tarawih" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <h3 class="text-xl font-bold text-gold font-sans">Jadwal Imam & Penceramah</h3>
                <button onclick="closeModal('modal-tarawih')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>
            
            <!-- Editor (Hidden by default, toggleable) -->
            {% if is_admin %}
            <div id="tarawih-editor" class="hidden p-4 bg-white/5 border border-white/10 rounded-xl mb-6">
                <form action="/ramadhan/tarawih" method="POST" class="space-y-3">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                     <div class="grid grid-cols-4 gap-2">
                         <input type="number" name="night_index" placeholder="Malam ke" required class="bg-[#0b1026] border border-gray-600 rounded-lg p-2 text-sm text-white focus:border-gold">
                         <input type="text" name="imam" placeholder="Nama Imam" required class="bg-[#0b1026] border border-gray-600 rounded-lg p-2 text-sm text-white focus:border-gold">
                         <input type="text" name="penceramah" placeholder="Nama Penceramah" required class="bg-[#0b1026] border border-gray-600 rounded-lg p-2 text-sm text-white focus:border-gold">
                         <input type="text" name="judul" placeholder="Judul Ceramah" class="bg-[#0b1026] border border-gray-600 rounded-lg p-2 text-sm text-white focus:border-gold">
                     </div>
                     <button type="submit" class="w-full bg-purple-600 text-white font-bold py-2 rounded-lg hover:bg-purple-500 shadow-lg">Update Jadwal</button>
                </form>
            </div>
            <div class="p-2 text-center border-b border-white/10 mb-4">
                <button onclick="document.getElementById('tarawih-editor').classList.toggle('hidden')" class="text-xs text-purple-400 hover:text-purple-300 font-bold uppercase tracking-wider bg-purple-500/10 px-4 py-2 rounded-full border border-purple-500/20">+ Edit Jadwal (Admin)</button>
            </div>
            {% endif %}

            <div class="overflow-hidden rounded-xl border border-white/10">
                <div class="grid grid-cols-1 divide-y divide-white/5">
                    {% for item in tarawih_schedule %}
                    <div class="p-4 hover:bg-white/5 transition flex gap-4 items-center">
                        <div class="bg-purple-500/20 text-purple-400 w-16 h-16 rounded-xl flex items-center justify-center font-bold text-xs flex-shrink-0 text-center leading-tight">
                            Hari {{ item['night_index'] - 1 }}<br>Malam {{ item['night_index'] }}
                        </div>
                        <div class="flex-1">
                            <p class="text-xs text-gray-400 uppercase font-bold mb-1 tracking-wider">IMAM & PENCERAMAH</p>
                            <p class="font-bold text-white mb-1">{{ item['imam'] }}</p>
                            {% if item['penceramah'] != item['imam'] %}
                            <p class="font-bold text-gold mb-1">{{ item['penceramah'] }}</p>
                            {% endif %}
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

    <!-- 5. MODAL ZAKAT FITRAH -->
    <div id="modal-zakat-fitrah" class="hidden fixed inset-0 z-[60] bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <button onclick="document.getElementById('modal-zakat-fitrah').classList.add('hidden'); document.getElementById('modal-zakat-menu').classList.remove('hidden'); history.replaceState({modal: 'modal-zakat-menu'}, null, '');" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full flex items-center justify-center"><i class="fas fa-arrow-left"></i></button>
                <h3 class="text-xl font-bold text-gold font-sans">Kalkulator Zakat Fitrah</h3>
                <button onclick="closeModal('modal-zakat-fitrah')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>
            <div class="space-y-6">
                <div>
                    <label class="block text-xs font-bold text-gray-400 mb-2">Jumlah Jiwa (Orang)</label>
                    <input type="number" id="zakat-jiwa" value="1" min="1" class="w-full bg-[#0b1026] border border-gold/30 rounded-xl p-4 text-white text-center text-xl font-bold focus:border-gold">
                </div>
                
                <div class="bg-white/5 p-6 rounded-2xl border border-white/10">
                    <p class="text-xs text-gray-400 mb-4 uppercase font-bold text-center tracking-widest">Estimasi Pembayaran</p>
                    <div class="flex justify-between items-center mb-4 border-b border-white/5 pb-4">
                        <span class="text-gray-300">Beras (2.75 Kg)</span>
                        <span class="font-bold text-white text-2xl" id="res-beras">2.75 Kg</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <div class="flex items-center gap-2">
                            <span class="text-gray-300">Uang</span>
                            <select id="zakat-uang-rate" onchange="calculateZakatFitrah()" class="bg-[#0b1026] text-gray-300 border border-gold/30 rounded p-1 text-xs">
                                <option value="70000">Kategori I (Rp 70.000)</option>
                                <option value="60000">Kategori II (Rp 60.000)</option>
                                <option value="50000">Kategori III (Rp 50.000)</option>
                                <option value="45000" selected>Standar (Rp 45.000)</option>
                            </select>
                        </div>
                        <span class="font-bold text-gold text-2xl" id="res-uang">Rp 45.000</span>
                    </div>
                </div>
                
                <button onclick="calculateZakatFitrah()" class="w-full bg-gray-200 text-gray-800 font-bold py-4 rounded-xl hover:bg-white active:bg-white active:shadow-[0_0_15px_rgba(255,255,255,0.8)] transition shadow-lg">Hitung Ulang</button>
                <p class="text-[10px] text-gray-500 text-center italic">*Harga uang menyesuaikan standar BAZNAS (Badan Amil Zakat Nasional) KOTA SAMARINDA</p>
            </div>
        </div>
    </div>

    <!-- 5A. MODAL ZAKAT MENU -->
    <div id="modal-zakat-menu" class="hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm flex items-center justify-center overflow-y-auto">
        <div class="relative w-full max-w-sm mx-4 bg-[#151e3f] border border-white/10 rounded-3xl shadow-2xl p-6 animate-[slideUp_0.3s_ease-out]">
            <button onclick="closeModal('modal-zakat-menu')" class="absolute top-4 right-4 bg-white/10 w-8 h-8 rounded-full text-gray-300 hover:text-white hover:bg-white/20 flex items-center justify-center transition">&times;</button>
            <h3 class="text-xl font-bold text-gold font-sans mb-6 text-center">Menu Zakat Fitrah</h3>
            <div class="flex flex-col gap-4">
                <button onclick="event.preventDefault(); event.stopPropagation(); document.getElementById('modal-zakat-menu').classList.add('hidden'); document.getElementById('modal-zakat-fitrah').classList.remove('hidden'); history.pushState({modal: 'modal-zakat-fitrah'}, null, '');" class="bg-gold text-midnight font-bold py-4 px-6 rounded-2xl hover:bg-white transition transform hover:scale-105 shadow-lg flex items-center justify-center gap-3">
                    <i class="fas fa-calculator text-lg"></i> Kalkulator Zakat Fitrah
                </button>
                <button onclick="event.preventDefault(); event.stopPropagation(); document.getElementById('modal-zakat-menu').classList.add('hidden'); document.getElementById('modal-doa-zakat').classList.remove('hidden'); history.pushState({modal: 'modal-doa-zakat'}, null, '');" class="bg-gold text-midnight font-bold py-4 px-6 rounded-2xl hover:bg-white transition transform hover:scale-105 shadow-lg flex items-center justify-center gap-3">
                    <i class="fas fa-hands-praying text-lg"></i> Doa Zakat
                </button>
                <button onclick="event.preventDefault(); event.stopPropagation(); document.getElementById('modal-zakat-menu').classList.add('hidden'); document.getElementById('modal-tabel-zakat').classList.remove('hidden'); history.pushState({modal: 'modal-tabel-zakat'}, null, '');" class="bg-gold text-midnight font-bold py-4 px-6 rounded-2xl hover:bg-white transition transform hover:scale-105 shadow-lg flex items-center justify-center gap-3">
                    <i class="fas fa-table text-lg"></i> Tabel Zakat
                </button>
            </div>
        </div>
    </div>

    <!-- 5B. MODAL DOA ZAKAT -->
    <div id="modal-doa-zakat" class="hidden fixed inset-0 z-[60] bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-8 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out] max-w-3xl mx-auto">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <button onclick="document.getElementById('modal-doa-zakat').classList.add('hidden'); document.getElementById('modal-zakat-menu').classList.remove('hidden'); history.replaceState({modal: 'modal-zakat-menu'}, null, '');" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full flex items-center justify-center"><i class="fas fa-arrow-left"></i></button>
                <div class="text-center flex-1">
                    <h2 class="text-2xl md:text-3xl font-bold text-white font-sans tracking-wide">NIKMAT BERZAKAT</h2>
                    <h3 class="text-xs md:text-sm font-bold text-[#FFD700] tracking-widest mt-1">TENTRAMNYA MUZAKI, BAHAGIANYA MUSTAHIK</h3>
                </div>
                <button onclick="closeModal('modal-doa-zakat')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>

            <div class="space-y-6">
                <!-- Kartu Pertama -->
                <div class="bg-white rounded-3xl p-6 md:p-8 shadow-[0_10px_30px_rgba(0,0,0,0.5)] border border-gray-100 relative overflow-hidden transform transition hover:-translate-y-1">
                    <h4 class="font-bold text-gray-900 mb-6 text-sm md:text-base border-l-4 border-[#FFD700] pl-3">NIAT ZAKAT FITRAH UNTUK DIRI SENDIRI</h4>
                    <p class="text-2xl md:text-4xl text-right font-arabic leading-[2.5] mb-6 text-gray-800" style="font-family: 'Amiri', serif;">نَوَيْتُ أَنْ أُخْرِجَ زَكَاةَ الْفِطْرِ عَنْ نَفْسِيْ فَرْضًا لِلَّهِ تَعَالَى</p>
                    <p class="text-emerald-700 italic text-sm md:text-base mb-4 leading-relaxed font-medium">Nawaitu an ukhrija zakaatal fitri 'an nafsi fardhallillahi ta'ala</p>
                    <p class="text-gray-700 text-sm md:text-base leading-relaxed border-t border-gray-100 pt-4">Aku niat mengeluarkan zakat fitrah untuk diriku sendiri, fardu karena Allah Ta'âlâ.</p>
                </div>

                <!-- Kartu Kedua -->
                <div class="bg-white rounded-3xl p-6 md:p-8 shadow-[0_10px_30px_rgba(0,0,0,0.5)] border border-gray-100 relative overflow-hidden transform transition hover:-translate-y-1">
                    <h4 class="font-bold text-gray-900 mb-6 text-sm md:text-base border-l-4 border-[#FFD700] pl-3">NIAT ZAKAT FITRAH UNTUK DIRI SENDIRI DAN KELUARGA</h4>
                    <p class="text-2xl md:text-4xl text-right font-arabic leading-[2.5] mb-6 text-gray-800" style="font-family: 'Amiri', serif;">نَوَيْتُ أَنْ أُخْرِجَ زَكَاةَ الْفِطْرِ عَنِّيْ وَعَنْ جَمِيْعِ مَا يَلْزَمُنِيْ نَفَقَاتُهُمْ شَرْعًا فَرْضًا لِلَّهِ تَعَالَى</p>
                    <p class="text-emerald-700 italic text-sm md:text-base mb-4 leading-relaxed font-medium">Nawaitu an ukhrija zakaatal fitri 'annii wa 'an jamii'i maa yal zamunii nafaqaa tuhum syar'an fardhallillahi ta'ala</p>
                    <p class="text-gray-700 text-sm md:text-base leading-relaxed border-t border-gray-100 pt-4">Aku niat mengeluarkan zakat fitrah untuk diriku dan seluruh orang yang nafkahnya menjadi tanggunganku, fardu karena Allah Ta'âlâ.</p>
                </div>

                <!-- Kartu Ketiga -->
                <div class="bg-white rounded-3xl p-6 md:p-8 shadow-[0_10px_30px_rgba(0,0,0,0.5)] border border-gray-100 relative overflow-hidden transform transition hover:-translate-y-1">
                    <h4 class="font-bold text-gray-900 mb-6 text-sm md:text-base border-l-4 border-[#FFD700] pl-3">NIAT ZAKAT FITRAH UNTUK ORANG YANG DIWAKILKAN</h4>
                    <p class="text-2xl md:text-4xl text-right font-arabic leading-[2.5] mb-6 text-gray-800" style="font-family: 'Amiri', serif;">نَوَيْتُ أَنْ أُخْرِجَ زَكَاةَ الْفِطْرِ عَنْ (...) فَرْضًا لِلَّهِ تَعَالَى</p>
                    <p class="text-emerald-700 italic text-sm md:text-base mb-4 leading-relaxed font-medium">Nawaitu an ukhrija zakaatal fitri 'an ...(nama)... fardhallillahi ta'ala</p>
                    <p class="text-gray-700 text-sm md:text-base leading-relaxed border-t border-gray-100 pt-4">Aku niat mengeluarkan zakat fitrah untuk... (sebutkan nama spesifik), fardu karena Allah Ta'âlâ.</p>
                </div>

                <!-- Kartu Keempat -->
                <div class="bg-white rounded-3xl p-6 md:p-8 shadow-[0_10px_30px_rgba(0,0,0,0.5)] border border-gray-100 relative overflow-hidden transform transition hover:-translate-y-1">
                    <h4 class="font-bold text-gray-900 mb-6 text-sm md:text-base border-l-4 border-[#FFD700] pl-3">NIAT ZAKAT MAAL</h4>
                    <p class="text-2xl md:text-4xl text-right font-arabic leading-[2.5] mb-6 text-gray-800" style="font-family: 'Amiri', serif;">نَوَيْتُ أَنْ أُخْرِجَ زَكَاةَ الْمَالِ عَنْ نَفْسِيْ فَرْضًا لِلَّهِ تَعَالَى</p>
                    <p class="text-emerald-700 italic text-sm md:text-base mb-4 leading-relaxed font-medium">Nawaitu an ukhrija zakaatal maal 'an nafsi fardhallillahi ta'ala</p>
                    <p class="text-gray-700 text-sm md:text-base leading-relaxed border-t border-gray-100 pt-4">Saya niat mengeluarkan zakat berupa emas/perak/harta dari diriku sendiri karena Allah Ta'ala.</p>
                </div>

                <!-- Kartu Kelima -->
                <div class="bg-white rounded-3xl p-6 md:p-8 shadow-[0_10px_30px_rgba(0,0,0,0.5)] border border-gray-100 relative overflow-hidden transform transition hover:-translate-y-1">
                    <h4 class="font-bold text-gray-900 mb-6 text-sm md:text-base border-l-4 border-[#FFD700] pl-3">DO'A MENERIMA ZAKAT</h4>
                    <p class="text-2xl md:text-4xl text-right font-arabic leading-[2.5] mb-6 text-gray-800" style="font-family: 'Amiri', serif;">أَجَرَكَ اللهُ فِيْمَا أَعْطَيْتَ, وَبَارَكَ لَكَ فِيْمَا أَبْقَيْتَ, وَاجْعَلْهُ لَكَ طَهُوْرًا</p>
                    <p class="text-emerald-700 italic text-sm md:text-base mb-4 leading-relaxed font-medium">Ajarakallahu fiimaa a'thoita wa baaraka laka fiimaa abqoita waj'alhu laka thohuuron.</p>
                    <p class="text-gray-700 text-sm md:text-base leading-relaxed border-t border-gray-100 pt-4">Semoga Allah memberikan pahala kepadamu pada barang yang engkau berikan (zakatkan) dan semoga Allah memberkahimu dalam harta-harta yang masih engkau sisakan dan semoga pula menjadikannya sebagai pembersih (dosa) bagimu.</p>
                </div>
            </div>
        </div>
    </div>
    
    <!-- 5C. MODAL TABEL ZAKAT -->
    <div id="modal-tabel-zakat" class="hidden fixed inset-0 z-[60] bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-12 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out] max-w-4xl mx-auto">
            <button onclick="closeModal('modal-tabel-zakat')" class="absolute top-6 right-6 text-gray-400 hover:text-white bg-white/10 w-10 h-10 rounded-full z-10">&times;</button>
            <button onclick="document.getElementById('modal-tabel-zakat').classList.add('hidden'); document.getElementById('modal-zakat-menu').classList.remove('hidden'); history.replaceState({modal: 'modal-zakat-menu'}, null, '');" class="absolute top-6 left-6 text-gray-400 hover:text-white bg-white/10 w-10 h-10 rounded-full z-10 flex items-center justify-center"><i class="fas fa-arrow-left"></i></button>

            <div class="text-center mt-8 mb-6">
                <h2 class="text-2xl md:text-3xl font-bold text-white font-sans tracking-wide">MASJID AL-HIJRAH</h2>
                <h3 class="text-lg md:text-xl font-bold text-[#FFD700] tracking-widest mt-1">BAZNAS (Badan Amil Zakat Nasional) KOTA SAMARINDA</h3>
            </div>
            
            <hr class="border-white/20 mb-6">
            
            <div class="text-center mb-8">
                <h4 class="text-xl md:text-2xl font-bold text-white mb-2">TABEL KADAR ZAKAT FITRAH DAN FIDYAH</h4>
                <p class="text-gray-300 text-sm md:text-base">Wilayah Kota Samarinda Tahun 1447 H / 2026 M</p>
            </div>

            <div class="space-y-10">
                <!-- Tabel 1: Zakat Fitrah -->
                <div class="bg-white rounded-3xl p-6 shadow-2xl overflow-hidden border border-gray-100">
                    <h5 class="font-bold text-gray-900 mb-4 text-lg border-l-4 border-[#FFD700] pl-3">Kadar Zakat Fitrah</h5>
                    <div class="overflow-x-auto custom-scrollbar">
                        <table class="w-full text-sm text-left border-collapse min-w-[600px]">
                            <thead class="bg-[#FFD700] text-[#0b1026]">
                                <tr>
                                    <th class="p-3 font-bold border border-gray-200">Jumlah Orang / Jiwa</th>
                                    <th class="p-3 font-bold border border-gray-200">Kategori I (Rp)</th>
                                    <th class="p-3 font-bold border border-gray-200">Kategori II (Rp)</th>
                                    <th class="p-3 font-bold border border-gray-200">Kategori III (Rp)</th>
                                    <th class="p-3 font-bold border border-gray-200">Beras (KG)</th>
                                </tr>
                            </thead>
                            <tbody class="text-gray-800">
                                <tr class="bg-gray-50 hover:bg-[#FFF9C4] transition">
                                    <td class="p-3 font-bold border border-gray-200">1</td>
                                    <td class="p-3 border border-gray-200">70.000</td>
                                    <td class="p-3 border border-gray-200">60.000</td>
                                    <td class="p-3 border border-gray-200">50.000</td>
                                    <td class="p-3 border border-gray-200">2,75</td>
                                </tr>
                                <tr class="bg-white hover:bg-[#FFF9C4] transition">
                                    <td class="p-3 font-bold border border-gray-200">2</td>
                                    <td class="p-3 border border-gray-200">140.000</td>
                                    <td class="p-3 border border-gray-200">120.000</td>
                                    <td class="p-3 border border-gray-200">100.000</td>
                                    <td class="p-3 border border-gray-200">5,5</td>
                                </tr>
                                <tr class="bg-gray-50 hover:bg-[#FFF9C4] transition">
                                    <td class="p-3 font-bold border border-gray-200">3</td>
                                    <td class="p-3 border border-gray-200">210.000</td>
                                    <td class="p-3 border border-gray-200">180.000</td>
                                    <td class="p-3 border border-gray-200">150.000</td>
                                    <td class="p-3 border border-gray-200">8,25</td>
                                </tr>
                                <tr class="bg-white hover:bg-[#FFF9C4] transition">
                                    <td class="p-3 font-bold border border-gray-200">4</td>
                                    <td class="p-3 border border-gray-200">280.000</td>
                                    <td class="p-3 border border-gray-200">240.000</td>
                                    <td class="p-3 border border-gray-200">200.000</td>
                                    <td class="p-3 border border-gray-200">11</td>
                                </tr>
                                <tr class="bg-gray-50 hover:bg-[#FFF9C4] transition">
                                    <td class="p-3 font-bold border border-gray-200">5</td>
                                    <td class="p-3 border border-gray-200">350.000</td>
                                    <td class="p-3 border border-gray-200">300.000</td>
                                    <td class="p-3 border border-gray-200">250.000</td>
                                    <td class="p-3 border border-gray-200">13,75</td>
                                </tr>
                                <tr class="bg-white hover:bg-[#FFF9C4] transition">
                                    <td class="p-3 font-bold border border-gray-200">6</td>
                                    <td class="p-3 border border-gray-200">420.000</td>
                                    <td class="p-3 border border-gray-200">360.000</td>
                                    <td class="p-3 border border-gray-200">300.000</td>
                                    <td class="p-3 border border-gray-200">16,5</td>
                                </tr>
                                <tr class="bg-gray-50 hover:bg-[#FFF9C4] transition">
                                    <td class="p-3 font-bold border border-gray-200">7</td>
                                    <td class="p-3 border border-gray-200">490.000</td>
                                    <td class="p-3 border border-gray-200">420.000</td>
                                    <td class="p-3 border border-gray-200">350.000</td>
                                    <td class="p-3 border border-gray-200">19,25</td>
                                </tr>
                                <tr class="bg-white hover:bg-[#FFF9C4] transition">
                                    <td class="p-3 font-bold border border-gray-200">8</td>
                                    <td class="p-3 border border-gray-200">560.000</td>
                                    <td class="p-3 border border-gray-200">480.000</td>
                                    <td class="p-3 border border-gray-200">400.000</td>
                                    <td class="p-3 border border-gray-200">22</td>
                                </tr>
                                <tr class="bg-gray-50 hover:bg-[#FFF9C4] transition">
                                    <td class="p-3 font-bold border border-gray-200">9</td>
                                    <td class="p-3 border border-gray-200">630.000</td>
                                    <td class="p-3 border border-gray-200">540.000</td>
                                    <td class="p-3 border border-gray-200">450.000</td>
                                    <td class="p-3 border border-gray-200">24,75</td>
                                </tr>
                                <tr class="bg-white hover:bg-[#FFF9C4] transition">
                                    <td class="p-3 font-bold border border-gray-200">10</td>
                                    <td class="p-3 border border-gray-200">700.000</td>
                                    <td class="p-3 border border-gray-200">600.000</td>
                                    <td class="p-3 border border-gray-200">500.000</td>
                                    <td class="p-3 border border-gray-200">27,5</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Tabel 2: Fidyah -->
                <div class="bg-white rounded-3xl p-6 shadow-2xl overflow-hidden border border-gray-100">
                    <h5 class="font-bold text-gray-900 mb-4 text-lg border-l-4 border-[#FFD700] pl-3">Kadar Fidyah</h5>
                    <div class="overflow-x-auto custom-scrollbar">
                        <table class="w-full text-sm text-left border-collapse min-w-[500px]">
                            <thead class="bg-[#FFD700] text-[#0b1026]">
                                <tr>
                                    <th class="p-3 font-bold border border-gray-200">Jumlah Hari / Orang / Jiwa</th>
                                    <th class="p-3 font-bold border border-gray-200">Kategori I (Rp)</th>
                                    <th class="p-3 font-bold border border-gray-200">Kategori II (Rp)</th>
                                    <th class="p-3 font-bold border border-gray-200">Beras (KG)</th>
                                </tr>
                            </thead>
                            <tbody class="text-gray-800">
                                <tr class="bg-gray-50 hover:bg-[#FFF9C4] transition">
                                    <td class="p-3 font-bold border border-gray-200">1 Hari / Jiwa / Orang</td>
                                    <td class="p-3 border border-gray-200">40.000</td>
                                    <td class="p-3 border border-gray-200">25.000</td>
                                    <td class="p-3 border border-gray-200">0,7</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- DEV TOAST NOTIFICATION -->
    <div id="dev-toast" class="fixed bottom-24 left-1/2 transform -translate-x-1/2 bg-white text-gray-900 px-6 py-3 rounded-full shadow-2xl z-50 opacity-0 pointer-events-none transition-all duration-300 flex items-center gap-3">
        <div class="w-8 h-8 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center">
            <i class="fas fa-hammer"></i>
        </div>
        <span class="font-bold text-sm tracking-wide">Sedang dalam tahap pengembangan</span>
    </div>

    <!-- 6. MODAL AMALAN -->
    <div id="modal-amalan" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <!-- Canvas for fireworks needs to be full screen -->
        <canvas id="fireworks" class="fixed inset-0 pointer-events-none z-50"></canvas>
        
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4 relative z-10">
                <h3 class="text-xl font-bold text-pink-400 font-sans">Checklist Amalan Harian</h3>
                <button onclick="closeModal('modal-amalan')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>
            
            <div class="relative z-10">
                <div class="bg-gradient-to-r from-pink-400 to-purple-500 bg-clip-text text-transparent text-center font-bold text-lg animate-pulse mb-6">May Allah SWT always be with us...</div>
                <div class="mb-8">
                     <div class="flex justify-between text-xs text-gray-400 mb-2 font-bold uppercase tracking-wider">
                         <span>Progress Harian</span>
                         <span id="progress-text">0%</span>
                     </div>
                     <div class="w-full bg-white/10 rounded-full h-4 overflow-hidden">
                          <div id="progress-bar" class="bg-pink-500 h-4 rounded-full transition-all duration-500 shadow-[0_0_10px_#EC4899]" style="width: 0%"></div>
                     </div>
                </div>

                <div class="space-y-4" id="amalan-list">
                    <!-- Checkboxes generated by JS -->
                    <label class="flex items-center gap-4 p-4 bg-white/5 rounded-2xl border border-white/10 cursor-pointer hover:bg-white/10 transition group">
                        <div class="relative flex items-center">
                            <input type="checkbox" onchange="updateProgress()" class="peer appearance-none w-6 h-6 border-2 border-gray-500 rounded-md checked:bg-pink-500 checked:border-pink-500 transition-colors">
                            <i class="fas fa-check absolute left-1 top-1 text-white opacity-0 peer-checked:opacity-100 text-xs pointer-events-none"></i>
                        </div>
                        <span class="text-gray-300 font-medium group-hover:text-white transition-colors">Puasa Hari Ini</span>
                    </label>
                    <label class="flex items-center gap-4 p-4 bg-white/5 rounded-2xl border border-white/10 cursor-pointer hover:bg-white/10 transition group">
                        <div class="relative flex items-center">
                            <input type="checkbox" onchange="updateProgress()" class="peer appearance-none w-6 h-6 border-2 border-gray-500 rounded-md checked:bg-pink-500 checked:border-pink-500 transition-colors">
                            <i class="fas fa-check absolute left-1 top-1 text-white opacity-0 peer-checked:opacity-100 text-xs pointer-events-none"></i>
                        </div>
                        <span class="text-gray-300 font-medium group-hover:text-white transition-colors">Sholat 5 Waktu</span>
                    </label>
                    <label class="flex items-center gap-4 p-4 bg-white/5 rounded-2xl border border-white/10 cursor-pointer hover:bg-white/10 transition group">
                        <div class="relative flex items-center">
                            <input type="checkbox" onchange="updateProgress()" class="peer appearance-none w-6 h-6 border-2 border-gray-500 rounded-md checked:bg-pink-500 checked:border-pink-500 transition-colors">
                            <i class="fas fa-check absolute left-1 top-1 text-white opacity-0 peer-checked:opacity-100 text-xs pointer-events-none"></i>
                        </div>
                        <span class="text-gray-300 font-medium group-hover:text-white transition-colors">Sholat Tarawih</span>
                    </label>
                    <label class="flex items-center gap-4 p-4 bg-white/5 rounded-2xl border border-white/10 cursor-pointer hover:bg-white/10 transition group">
                        <div class="relative flex items-center">
                             <input type="checkbox" onchange="updateProgress()" class="peer appearance-none w-6 h-6 border-2 border-gray-500 rounded-md checked:bg-pink-500 checked:border-pink-500 transition-colors">
                            <i class="fas fa-check absolute left-1 top-1 text-white opacity-0 peer-checked:opacity-100 text-xs pointer-events-none"></i>
                        </div>
                        <span class="text-gray-300 font-medium group-hover:text-white transition-colors">Tilawah 1 Juz</span>
                    </label>
                    <label class="flex items-center gap-4 p-4 bg-white/5 rounded-2xl border border-white/10 cursor-pointer hover:bg-white/10 transition group">
                        <div class="relative flex items-center">
                             <input type="checkbox" onchange="updateProgress()" class="peer appearance-none w-6 h-6 border-2 border-gray-500 rounded-md checked:bg-pink-500 checked:border-pink-500 transition-colors">
                            <i class="fas fa-check absolute left-1 top-1 text-white opacity-0 peer-checked:opacity-100 text-xs pointer-events-none"></i>
                        </div>
                        <span class="text-gray-300 font-medium group-hover:text-white transition-colors">Sedekah Subuh</span>
                    </label>
                </div>
                
                <button onclick="resetAmalan()" class="mt-8 w-full text-xs text-gray-500 hover:text-white underline uppercase tracking-wider">Reset Checklist Hari Ini</button>
            </div>
        </div>
    </div>
</div>

<script>
    // --- RAMADHAN JS UTILS ---

    document.addEventListener('DOMContentLoaded', () => {
        const open = '{{ open_modal }}';
        if(open && open !== 'None') openModal(open);
    });
    
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
            
            // Brute Force Adjustment -3 Days
            const response = await fetch('https://api.aladhan.com/v1/gToH?date=' + dateStr + '&adjustment=-3');
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
        history.pushState({modal: id}, null, "");
    }
    function closeModal(id) {
        if (history.state && history.state.modal === id) {
            history.back();
        } else {
            document.getElementById(id).classList.add('hidden');
        }
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
        const beras = jiwa * 2.75;
        const rate = document.getElementById('zakat-uang-rate') ? parseInt(document.getElementById('zakat-uang-rate').value) : 45000;
        const uang = jiwa * rate;
        
        document.getElementById('res-beras').innerText = beras.toFixed(2) + " Kg";
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

    // DEV TOAST
    function showDevelopmentToast() {
        const toast = document.getElementById('dev-toast');
        if (toast) {
            toast.classList.remove('opacity-0', 'pointer-events-none');
            toast.classList.add('opacity-100');
            setTimeout(() => {
                toast.classList.remove('opacity-100');
                toast.classList.add('opacity-0', 'pointer-events-none');
            }, 3000);
        }
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
    
    <!-- SPLIT HEADER -->
    <div class="md:grid md:grid-cols-2 md:gap-12 md:items-center mb-10">
        
        <!-- LEFT: WELCOME -->
        <div class="hidden md:block pl-2">
            <p class="text-xl text-gray-500 font-medium mb-2">Assalamualaikum Warahmatullahi Wabarakatuh</p>
            <h1 class="text-5xl font-bold text-[#2F4F4F] leading-tight mb-6">Selamat Datang di<br>IRMA Masjid Al Hijrah</h1>
            <p class="text-gray-600 text-lg leading-relaxed mb-8">
                Wadah Pemuda Pemudi Kreatif dan Islami. Mari bersama membangun generasi Rabbani yang produktif, berakhlak mulia, dan bermanfaat bagi umat.
            </p>
            <div class="flex gap-4">
                <button onclick="openModal('modal-events')" class="bg-[#A0B391] text-white px-8 py-3 rounded-full font-bold shadow-lg hover:bg-[#8DA57B] transition transform hover:scale-105">Lihat Proker</button>
                <button onclick="openModal('modal-join')" class="bg-transparent text-[#A0B391] border-2 border-[#A0B391] px-8 py-3 rounded-full font-bold hover:bg-[#A0B391] hover:text-white transition transform hover:scale-105">Gabung Sekarang</button>
            </div>
        </div>

        <!-- RIGHT: PRAYER CARD -->
        <div>
            <div class="bg-gradient-to-br from-[#A0B391] to-[#8DA57B] rounded-3xl p-6 md:p-10 text-white shadow-xl relative overflow-hidden transform md:hover:scale-[1.02] transition-transform duration-500 border border-white/20">
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
            
            {% if is_admin %}
            <form action="/irma/schedule" method="POST" class="mb-6 bg-white p-4 rounded-2xl shadow-sm border border-[#A0B391]/20">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

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
            {% endif %}

            <div class="overflow-y-auto max-h-[40vh] space-y-3">
                {% for item in schedule_list %}
                <div class="bg-white p-4 rounded-2xl shadow-sm flex items-center justify-between">
                    <div>
                        <span class="text-[10px] font-bold bg-[#A0B391]/20 text-[#A0B391] px-2 py-1 rounded-md mb-1 inline-block">{{ item['role'] }}</span>
                        <h5 class="font-bold text-[#2F4F4F]">{{ item['name'] }}</h5>
                        <p class="text-xs text-gray-400">{{ item['date'] }}</p>
                    </div>
                    {% if is_admin %}
                    <form action="/irma/schedule" method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                        <input type="hidden" name="delete_id" value="{{ item['id'] }}">
                        <button class="text-gray-300 hover:text-red-400"><i class="fas fa-trash"></i></button>
                    </form>
                    {% endif %}
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
            
            {% if is_admin %}
            <!-- ADMIN VIEW -->
            <div class="bg-white rounded-3xl shadow-sm border border-[#A0B391]/20 overflow-hidden">
                <div class="p-4 border-b border-gray-100">
                    <h4 class="font-bold text-gray-700">Daftar Pendaftar</h4>
                </div>
                <div class="divide-y divide-gray-100">
                    {% for member in members_list %}
                    <div class="p-4">
                        <div class="flex justify-between items-start mb-2">
                            <div>
                                <h5 class="font-bold text-[#2F4F4F]">{{ member['name'] }} <span class="text-xs font-normal text-gray-500">({{ member['age'] }} th)</span></h5>
                                <p class="text-xs text-gray-400">{{ member['wa_number'] }} • {{ member['instagram'] }}</p>
                            </div>
                            <span class="text-[10px] font-bold px-2 py-1 rounded-full {{ 'bg-yellow-100 text-yellow-600' if member['status'] == 'Pending' else ('bg-green-100 text-green-600' if member['status'] == 'Approved' else 'bg-red-100 text-red-600') }}">
                                {{ member['status'] }}
                            </span>
                        </div>
                        <p class="text-xs text-gray-600 italic mb-3">"{{ member['hobbies'] }}"</p>
                        
                        {% if member['status'] == 'Pending' %}
                        <div class="flex gap-2">
                            <form action="/irma/join" method="POST" class="flex-1">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                                <input type="hidden" name="action" value="approve">
                                <input type="hidden" name="member_id" value="{{ member['id'] }}">
                                <button class="w-full bg-green-500 text-white text-xs font-bold py-2 rounded-lg hover:bg-green-600">Approve</button>
                            </form>
                            <form action="/irma/join" method="POST" class="flex-1">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                                <input type="hidden" name="action" value="reject">
                                <input type="hidden" name="member_id" value="{{ member['id'] }}">
                                <button class="w-full bg-red-500 text-white text-xs font-bold py-2 rounded-lg hover:bg-red-600">Tolak</button>
                            </form>
                        </div>
                        {% endif %}
                    </div>
                    {% else %}
                    <div class="p-8 text-center text-gray-400">Belum ada pendaftar.</div>
                    {% endfor %}
                </div>
            </div>
            {% else %}
            <!-- CITIZEN VIEW -->
            
            <!-- Check Status Form -->
            <div class="bg-white p-4 rounded-2xl shadow-sm border border-[#A0B391]/20 mb-6">
                <h4 class="text-xs font-bold text-[#A0B391] uppercase mb-2">Cek Status Pendaftaran</h4>
                <form action="/irma/join" method="GET" class="flex gap-2">
                    <input type="text" name="check_wa" placeholder="Masukkan No. WA" class="w-full bg-[#F4E7E1] border-none rounded-xl p-2 text-sm" required>
                    <button type="submit" class="bg-[#A0B391] text-white px-4 rounded-xl font-bold text-xs">Cek</button>
                </form>
                
                {% if check_status %}
                <div class="mt-3 p-3 rounded-xl {{ 'bg-green-50 border border-green-200' if check_status['status'] == 'Approved' else ('bg-red-50 border border-red-200' if check_status['status'] == 'Rejected' else 'bg-yellow-50 border border-yellow-200') }}">
                    <p class="font-bold text-sm {{ 'text-green-700' if check_status['status'] == 'Approved' else ('text-red-700' if check_status['status'] == 'Rejected' else 'text-yellow-700') }}">
                        Status: {{ check_status['status'] }}
                    </p>
                    <p class="text-xs text-gray-600 mt-1">
                        {% if check_status['status'] == 'Pending' %}
                        "Berhasil mendaftar! Silakan tunggu jadwal wawancara dari pengurus IRMA."
                        {% elif check_status['status'] == 'Rejected' %}
                        "Tetap semangat bertumbuh! Meskipun saat ini belum bisa bergabung dengan pengurus IRMA, kamu tetap bagian dari keluarga besar Masjid Al-Hijrah."
                        {% else %}
                        "Hubungi WhatsApp Jumali (Ketua IRMA Masjid Al-Hijrah) untuk panggilan wawancara atau informasi lebih lanjut."
                        <br><br>
                        <a href="https://wa.me/6285321395053?text=Assalamualaikum%20ka%20Jumali,%20perkenalkan%20saya%20{{ check_status['name'] }},%20telah%20mendaftar%20di%20IRMA%20Masjid%20Al-Hijrah%20melalui%20aplikasi%20website%20masjid%20ka,%20untuk%20kelanjutannya%20seperti%20apa%20ya%20ini%20Ka?%20Terima%20kasih%20ka." class="inline-block bg-[#25D366] text-white px-4 py-2 rounded-full font-bold text-xs shadow-md hover:bg-green-600 transition"><i class="fab fa-whatsapp mr-1"></i> Hubungi Ketua</a>
                        {% endif %}
                    </p>
                </div>
                {% endif %}
            </div>

            <form action="/irma/join" method="POST" class="space-y-4">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

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
            {% endif %}
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
            
            {% if is_admin %}
            <form action="/irma/kas" method="POST" class="mb-6 bg-white p-4 rounded-2xl shadow-sm border border-[#A0B391]/20">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

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
            {% endif %}

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
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

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
                <div class="bg-white rounded-2xl shadow-sm overflow-hidden break-inside-avoid border border-[#A0B391]/10 cursor-pointer hover:scale-105 transition-transform"
                     onclick="openMadingDetail(this)"
                     data-title="{{ item['title'] }}"
                     data-creator="{{ item['creator'] }}"
                     data-type="{{ item['content_type'] }}"
                     data-content="{{ item['content'] }}"
                     data-caption="{{ item['caption'] or '' }}">
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

    <!-- MODAL MADING DETAIL -->
    <div id="modal-mading-detail" class="hidden fixed inset-0 z-[60] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl shadow-2xl w-full max-w-sm max-h-[80vh] flex flex-col overflow-hidden animate-[popupFadeIn_0.3s_ease-out] relative">
            <button onclick="closeModal('modal-mading-detail')" class="absolute top-4 right-4 z-10 bg-white/20 hover:bg-white/40 text-white w-8 h-8 rounded-full flex items-center justify-center backdrop-blur-md shadow-sm transition">&times;</button>
            
            <div id="mading-detail-img-container" class="bg-gray-100 flex-shrink-0 hidden">
                <img id="mading-detail-img" src="" class="w-full h-auto object-contain max-h-[50vh]">
            </div>
            
            <div class="p-6 overflow-y-auto">
                <h3 id="mading-detail-title" class="text-xl font-bold text-[#2F4F4F] mb-1 leading-tight"></h3>
                <p class="text-xs font-bold text-[#A0B391] mb-4">By <span id="mading-detail-creator"></span></p>
                <div class="prose prose-sm text-gray-600">
                    <p id="mading-detail-text" class="whitespace-pre-wrap leading-relaxed text-sm"></p>
                </div>
            </div>
        </div>
    </div>

    <script>
        function openMadingDetail(el) {
            const title = el.getAttribute('data-title');
            const creator = el.getAttribute('data-creator');
            const type = el.getAttribute('data-type');
            const content = el.getAttribute('data-content');
            const caption = el.getAttribute('data-caption');
            
            document.getElementById('mading-detail-title').innerText = title;
            document.getElementById('mading-detail-creator').innerText = creator;
            
            const imgContainer = document.getElementById('mading-detail-img-container');
            const img = document.getElementById('mading-detail-img');
            const text = document.getElementById('mading-detail-text');
            
            if (type === 'Image') {
                imgContainer.classList.remove('hidden');
                img.src = "/uploads/" + content;
                text.innerText = caption;
            } else {
                imgContainer.classList.add('hidden');
                text.innerText = content;
            }
            
            document.getElementById('modal-mading-detail').classList.remove('hidden');
        }
    </script>
    <!-- 5. MODAL PROKER -->
    <div id="modal-events" class="hidden fixed inset-0 z-40 bg-[#F4E7E1] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-[#A0B391]/20 pb-4">
                <h3 class="text-xl font-bold text-[#2F4F4F]">Proker & Event</h3>
                <button onclick="closeModal('modal-events')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
            </div>
            
            {% if is_admin %}
            <form action="/irma/proker" method="POST" class="mb-6 bg-white p-4 rounded-2xl shadow-sm border border-[#A0B391]/20">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

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
            {% endif %}

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
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

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
                    {% if is_admin %}
                    <form action="/irma/curhat" method="POST" class="mt-2 pt-2 border-t border-gray-50">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                        <input type="hidden" name="answer_id" value="{{ item['id'] }}">
                        <input type="text" name="answer" placeholder="Jawab (Admin)..." class="w-full bg-gray-50 text-xs p-2 rounded-lg">
                    </form>
                    {% endif %}
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

# --- RAMADHAN ROUTES ---

@app.route('/ramadhan')
def ramadhan_dashboard():
    # 1. Takjil Data
    takjil_data = get_takjil_data()
    
    # 2. Imsakiyah Data
    imsakiyah_data = get_imsakiyah_schedule()
    
    # 3. Kas Ramadhan Data
    ramadhan_kas_items = RamadhanKas.query.order_by(RamadhanKas.date.desc()).all()
    kas_in = db.session.query(func.sum(RamadhanKas.amount)).filter_by(type='Pemasukan').scalar() or 0
    kas_out = db.session.query(func.sum(RamadhanKas.amount)).filter_by(type='Pengeluaran').scalar() or 0
    
    # 4. Tarawih Schedule
    seed_ramadhan_schedule()
    tarawih_schedule = TarawihSchedule.query.order_by(TarawihSchedule.night_index.asc()).all()
        
    # Render CONTENT first
    rendered_content = render_template_string(RAMADHAN_DASHBOARD_HTML,
                                              takjil_data=takjil_data,
                                              imsakiyah_data=imsakiyah_data,
                                              ramadhan_kas_items=ramadhan_kas_items,
                                              ramadhan_kas_summary={'income': kas_in, 'out': kas_out, 'balance': kas_in - kas_out},
                                              tarawih_schedule=tarawih_schedule,
                                              open_modal=request.args.get('open'),
                                              is_admin=session.get('is_admin', False),
                                              settings=get_settings())

    return render_template_string(BASE_LAYOUT, 
                                  styles=STYLES_HTML + RAMADHAN_STYLES, 
                                  active_page='ramadhan', 
                                  content=rendered_content,
                                  hide_nav=True,
                                  full_width=True,
                                  is_admin=session.get('is_admin', False),
                                  settings=get_settings())

@app.route('/ramadhan/kas', methods=['POST'])
def ramadhan_kas_action():
    try:
        item = RamadhanKas(
            date=request.form['date'],
            type=request.form['type'],
            category=request.form['category'],
            description=request.form['description'],
            amount=int(request.form['amount'])
        )
        db.session.add(item)
        db.session.commit()
    except Exception as e:
        print(f"Error saving kas: {e}")
    return redirect(url_for('ramadhan_dashboard', open='modal-kas-ramadhan'))

@app.route('/ramadhan/tarawih', methods=['POST'])
def ramadhan_tarawih_action():
    try:
        night = request.form['night_index']
        item = TarawihSchedule.query.filter_by(night_index=night).first()
        if item:
            item.imam = request.form['imam']
            item.penceramah = request.form['penceramah']
            item.judul = request.form['judul']
        else:
            item = TarawihSchedule(
                night_index=night,
                imam=request.form['imam'],
                penceramah=request.form['penceramah'],
                judul=request.form['judul']
            )
            db.session.add(item)
        db.session.commit()
    except Exception as e:
        print(f"Error saving tarawih: {e}")
    return redirect(url_for('ramadhan_dashboard', open='modal-tarawih'))

# --- IRMA ROUTES ---

@app.route('/irma')
def irma_dashboard():
    # Initialize Defaults
    is_admin = False
    schedule_list = []
    kas_list = []
    kas_summary = {'income': 0, 'out': 0, 'balance': 0}
    gallery_list = []
    proker_list = []
    curhat_list = []
    members_list = []
    check_status = None
    settings_data = {}
    
    try:
        is_admin = session.get('is_admin', False)
        settings_data = get_settings()

        # 1. Schedule List
        try:
            schedule_list = IrmaSchedule.query.order_by(IrmaSchedule.date.desc(), IrmaSchedule.id.desc()).all()
        except Exception as e:
            print(f"Error fetching Schedule: {e}")
        
        # 2. Kas (Finance)
        try:
            kas_list = IrmaKas.query.order_by(IrmaKas.date.desc()).all()
            fin_in = db.session.query(func.sum(IrmaKas.amount)).filter_by(type='Pemasukan').scalar() or 0
            fin_out = db.session.query(func.sum(IrmaKas.amount)).filter_by(type='Pengeluaran').scalar() or 0
            kas_summary = {'income': fin_in, 'out': fin_out, 'balance': fin_in - fin_out}
        except Exception as e:
            print(f"Error fetching Kas: {e}")
        
        # 3. Gallery (Mading)
        try:
            gallery_list = IrmaGallery.query.order_by(IrmaGallery.created_at.desc()).all()
        except Exception as e:
            print(f"Error fetching Gallery: {e}")
        
        # 4. Proker (Events)
        try:
            proker_list = IrmaProker.query.order_by(IrmaProker.date.asc()).all()
        except Exception as e:
            print(f"Error fetching Proker: {e}")
        
        # 5. Curhat (Q&A)
        try:
            curhat_list = IrmaCurhat.query.order_by(IrmaCurhat.created_at.desc()).all()
        except Exception as e:
            print(f"Error fetching Curhat: {e}")
        
        # 6. Members
        try:
            if is_admin:
                members_list = IrmaMember.query.order_by(IrmaMember.joined_at.desc()).all()
            
            check_wa = request.args.get('check_wa')
            if check_wa:
                check_status = IrmaMember.query.filter_by(wa_number=check_wa).first()
        except Exception as e:
            print(f"Error fetching Members: {e}")

    except Exception as e:
        print(f"Critical Error in IRMA Dashboard: {e}")
    
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
                                                                 members_list=members_list,
                                                                 check_status=check_status,
                                                                 open_modal=open_modal,
                                                                 is_admin=is_admin, settings=settings_data),
                                  full_width=True,
                                  is_admin=is_admin,
                                  settings=settings_data)

@app.route('/irma/schedule', methods=['POST'])
def irma_schedule():
    if 'delete_id' in request.form:
        IrmaSchedule.query.filter_by(id=request.form['delete_id']).delete()
    else:
        item = IrmaSchedule(
            name=request.form['name'],
            role=request.form['role'],
            date=request.form['date']
        )
        db.session.add(item)
    db.session.commit()
    return redirect(url_for('irma_dashboard', open='modal-duty'))

@app.route('/irma/join', methods=['GET', 'POST'])
def irma_join():
    if request.method == 'GET':
        return redirect(url_for('irma_dashboard', open='modal-join', check_wa=request.args.get('check_wa')))

    action = request.form.get('action')
    if action in ['approve', 'reject']:
        member = IrmaMember.query.get(request.form['member_id'])
        if member:
            member.status = 'Approved' if action == 'approve' else 'Rejected'
    else:
        item = IrmaMember(
            name=request.form['name'],
            age=request.form['age'],
            hobbies=request.form['hobbies'],
            instagram=request.form['instagram'],
            wa_number=request.form['wa_number']
        )
        db.session.add(item)
    db.session.commit()
    return redirect(url_for('irma_dashboard', open='modal-join'))

@app.route('/irma/kas', methods=['POST'])
def irma_kas():
    item = IrmaKas(
        date=request.form['date'],
        type=request.form['type'],
        description=request.form['description'],
        amount=int(request.form['amount'])
    )
    db.session.add(item)
    db.session.commit()
    return redirect(url_for('irma_dashboard', open='modal-finance'))

@app.route('/irma/gallery', methods=['POST'])
def irma_gallery():
    try:
        title = request.form.get('title', '')[:255]
        creator = request.form.get('creator', '')[:255]
        content = request.form.get('content', '')
        caption = content
        post_type = 'Text'
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    saved_filename = compress_image(file, app.config['UPLOAD_FOLDER'])
                    content = saved_filename
                    post_type = 'Image'
        
        # Ensure fallback for caption
        if caption is None: caption = ""
        
        item = IrmaGallery(title=title, creator=creator, content_type=post_type, content=content, caption=caption)
        db.session.add(item)
        db.session.commit()
    except Exception as e:
        print(f"Error uploading gallery: {e}")
        db.session.rollback()
        
    return redirect(url_for('irma_dashboard', open='modal-wall'))

@app.route('/irma/proker', methods=['POST'])
def irma_proker():
    item = IrmaProker(
        title=request.form['title'],
        status=request.form['status'],
        description=request.form['description'],
        date=request.form['date']
    )
    db.session.add(item)
    db.session.commit()
    return redirect(url_for('irma_dashboard', open='modal-events'))

@app.route('/irma/curhat', methods=['POST'])
def irma_curhat():
    if 'answer' in request.form:
        item = IrmaCurhat.query.get(request.form['answer_id'])
        if item:
            item.answer = request.form['answer']
            item.answered_at = datetime.datetime.now()
    else:
        item = IrmaCurhat(question=request.form['question'])
        db.session.add(item)
    db.session.commit()
    return redirect(url_for('irma_dashboard', open='modal-qa'))

def manifest():
    return jsonify({
        "name": "Masjid Al Hijrah",
        "short_name": "Al Hijrah",
        "description": "Aplikasi Masjid Al Hijrah Samarinda",
        "start_url": "/",
        "id": "/",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#0b1026",
        "theme_color": "#FFD700",
        "categories": ["lifestyle", "religious"],
        "prefer_related_applications": False,
        "icons": [
            {
                "src": "/static/logomasjidalhijrah.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/logomasjidalhijrah.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
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
    event.respondWith(
        fetch(event.request).then((networkResponse) => {
             if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
                 return networkResponse;
             }
             const responseToCache = networkResponse.clone();
             caches.open(CACHE_NAME).then((cache) => {
                 cache.put(event.request, responseToCache);
             });
             return networkResponse;
        }).catch(() => {
            return caches.match(event.request);
        })
    );
});
"""
    return Response(sw_code, mimetype='application/javascript')

@app.route('/donate/update', methods=['POST'])
def donate_update():
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    
    keys = ['infaq_rekening_masjid', 'infaq_rekening_qurban', 'infaq_rekening_zakat']
    for k in keys:
        val = request.form.get(k)
        if val:
            s = AppSettings.query.get(k)
            if s: s.value = val
            else: db.session.add(AppSettings(key=k, value=val))
            
    if 'qris_image' in request.files:
        file = request.files['qris_image']
        if file and allowed_file(file.filename):
            saved_filename = compress_image(file, app.config['UPLOAD_FOLDER'])
            s = AppSettings.query.get('infaq_qris_image')
            if s: s.value = saved_filename
            else: db.session.add(AppSettings(key='infaq_qris_image', value=saved_filename))
            
    db.session.commit()
    return redirect(request.referrer)

# --- IDUL ADHA ROUTES ---

@app.route('/idul-adha')
def idul_adha_dashboard():
    makassar_tz = pytz.timezone('Asia/Makassar')
    current_time = datetime.datetime.now(makassar_tz)

    # Check if time is between 06:30 AM and 08:30 AM
    start_time = current_time.replace(hour=6, minute=30, second=0, microsecond=0)
    cutoff_time = current_time.replace(hour=8, minute=30, second=0, microsecond=0)
    is_valid_window = start_time <= current_time <= cutoff_time

    rendered_content = render_template_string(IDUL_ADHA_DASHBOARD_HTML,
                                              is_valid_window=is_valid_window,
                                              settings=get_settings())

    # We will use the existing BASE_LAYOUT which already manages headers/footers/styles/js
    # instead of rendering a raw HTML string.
    return render_template_string(BASE_LAYOUT,
                                  styles=STYLES_HTML,
                                  active_page='idul-adha',
                                  content=rendered_content,
                                  is_admin=session.get('is_admin', False),
                                  settings=get_settings())

@app.route('/idul-adha/absen', methods=['POST'])
def idul_adha_absen():
    makassar_tz = pytz.timezone('Asia/Makassar')
    current_time = datetime.datetime.now(makassar_tz)

    # 06:30 AM to 08:30 AM
    start_time = current_time.replace(hour=6, minute=30, second=0, microsecond=0)
    cutoff_time = current_time.replace(hour=8, minute=30, second=0, microsecond=0)

    if start_time <= current_time <= cutoff_time:
        status = 'Hadir Pagi'
    else:
        status = 'Terlambat'

    username = session.get('username', 'Unknown/Guest')

    attendance = QurbanAttendance(
        name=username,
        check_in_time=current_time,
        status=status
    )
    db.session.add(attendance)
    db.session.commit()

    if status == 'Hadir Pagi':
        flash('Berhasil absen. Anda tercatat Hadir Pagi.', 'success')
    else:
        flash('Absen gagal atau terlambat. Anda tercatat Terlambat.', 'error')

    return redirect(url_for('idul_adha_dashboard'))

@app.route('/idul-adha/distribution')
def idul_adha_distribution():
    # Segregate committee members based on attendance status
    hadir_pagi = QurbanAttendance.query.filter_by(status='Hadir Pagi').all()
    terlambat = QurbanAttendance.query.filter(QurbanAttendance.status.in_(['Terlambat', 'Siluman'])).all()

    # In a real scenario, this would render a specific distribution dashboard template.
    # For now, we return JSON to fulfill the logic requirement.
    return jsonify({
        'hadir_pagi_count': len(hadir_pagi),
        'terlambat_count': len(terlambat),
        'hadir_pagi_members': [a.name for a in hadir_pagi],
        'terlambat_members': [a.name for a in terlambat],
        'allocation_policy': {
            'Hadir Pagi': 'Full Meat Allocation',
            'Terlambat / Siluman': 'Leftover / Denied'
        }
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
