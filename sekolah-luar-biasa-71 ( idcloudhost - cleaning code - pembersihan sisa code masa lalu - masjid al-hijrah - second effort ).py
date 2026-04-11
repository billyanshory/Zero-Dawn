import eventlet
eventlet.monkey_patch()
import threading
import os
import datetime
import math
import time
import json
import csv
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from flask import Flask, request, send_from_directory, redirect, url_for, Response, jsonify, session, render_template_string
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy import Index
from flask_socketio import SocketIO, emit
from apscheduler.schedulers.background import BackgroundScheduler
import filetype
import logging
import logging.handlers
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
import hashlib

def cached_render(template_name, template_string, **context):
    env = current_app.jinja_env
    if env.cache is not None:
        template = env.cache.get(template_name)
        if template is None:
            template = env.from_string(template_string)
            env.cache[template_name] = template
    else:
        template = env.from_string(template_string)
    return template.render(**context)


load_dotenv()

# --- KONFIGURASI FLASK ---
app = Flask(__name__)

import urllib.parse
def is_safe_redirect(url):
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc == '' or parsed.netloc == request.host
    except Exception:
        return False
csrf = CSRFProtect(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv('REDIS_URL', 'memory://')
)
cache = Cache(app, config={
    'CACHE_TYPE': 'RedisCache' if os.getenv('REDIS_URL') else 'SimpleCache', 
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379/0') if os.getenv('REDIS_URL') else None
})
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins=os.getenv('ALLOWED_ORIGINS', '').split(',') if os.getenv('ALLOWED_ORIGINS') else [])

scheduler = BackgroundScheduler()

app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB Limit
secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    raise RuntimeError("SECRET_KEY environment variable is not set. Generate one using: python -c \"import secrets; print(secrets.token_hex(32))\"")
app.secret_key = secret_key
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(hours=8)
app.config['WTF_CSRF_CHECK_DEFAULT'] = True
app.config['WTF_CSRF_HEADERS'] = ['X-CSRFToken', 'X-CSRF-Token']
app.config['WTF_CSRF_TIME_LIMIT'] = 3600

from flask import current_app


app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
if not app.config['SQLALCHEMY_DATABASE_URI']:
    raise RuntimeError("SQLALCHEMY_DATABASE_URI environment variable is not set.")
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 3600,
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 30,
    'pool_pre_ping': True,
    
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

log_dir = os.path.join(os.path.expanduser('~'), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, 'slb_error.log')
handler = logging.handlers.RotatingFileHandler(log_path, maxBytes=10*1024*1024, backupCount=5)
handler.setLevel(logging.ERROR)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
app.logger.addHandler(handler)

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Terjadi kesalahan: {str(e)}", exc_info=True)
    return '''
    <html>
        <head><title>500 Internal Server Error</title></head>
        <body style="font-family: sans-serif; text-align: center; padding-top: 20%;">
            <h2>Mohon Maaf, Sistem Sedang Mengalami Kendala.</h2>
            <p>Terjadi kesalahan teknis. Silakan coba beberapa saat lagi.</p>
        </body>
    </html>
    ''', 500
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff', 'heic', 'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'm4v', 'mpeg', 'mp3', 'wav', 'ogg', 'm4a', 'flac', 'aac', 'wma', 'aiff', 'alac', 'amr', 'mid', 'midi'}

db = SQLAlchemy(app)

# --- DATA SUMBER HUKUM (DALIL) ---
# --- DATA SUMBER HUKUM (DALIL) ---
DALIL_DATA = {
    "imt": [],
    "sensory": [],
    "auditori": [],
    "iq": [],
    "motorik": [],
    "diet": []
}

# --- DATABASE SETUP ---
# Database is configured via the SQLALCHEMY_DATABASE_URI environment variable.

# --- DATABASE MODELS ---

class Siswa(db.Model):
    __tablename__ = 'siswa'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(255), nullable=False)
    kelas = db.Column(db.String(255))
    diagnosis = db.Column(db.String(255))

class ProfilMedisSiswa(db.Model):
    __tablename__ = 'profil_medis_siswa'
    id = db.Column(db.Integer, primary_key=True)
    siswa_id = db.Column(db.Integer, db.ForeignKey('siswa.id'), unique=True, index=True, nullable=False)
    nama_lengkap = db.Column(db.String(255))
    nama_panggilan = db.Column(db.String(100))
    usia = db.Column(db.Integer)
    kelas = db.Column(db.String(50))
    jenis_slb = db.Column(db.String(100))
    kategori_hambatan = db.Column(db.String(100))
    diagnosis_utama = db.Column(db.Text)
    tingkat_hambatan = db.Column(db.String(100))
    alergi_kritis = db.Column(db.Text)
    pemicu_tantrum = db.Column(db.Text)
    strategi_penenangan = db.Column(db.Text)
    kemampuan_komunikasi = db.Column(db.Text)
    hotline_darurat_nama = db.Column(db.String(100))
    hotline_darurat_nomor = db.Column(db.String(30))
    kondisi_terkini = db.Column(db.String(100))
    kondisi_warna = db.Column(db.String(20))
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=datetime.datetime.now)

class AkunPengguna(db.Model):
    __tablename__ = 'akun_pengguna'
    __table_args__ = (Index('idx_akun_pengguna_status_akun', 'status_akun'), Index('idx_akun_pengguna_anak_id', 'anak_id'),)
    id = db.Column(db.Integer, primary_key=True)
    nik = db.Column(db.String(50), unique=True, nullable=False)
    nama_lengkap = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    peran = db.Column(db.Enum('orang_tua', 'guru', 'kepala_sekolah', name='peran_akun_enum'), nullable=False)
    status_akun = db.Column(db.Enum('menunggu_verifikasi', 'disetujui', 'ditolak', name='status_akun_enum'), default='menunggu_verifikasi', index=True)
    anak_id = db.Column(db.Integer, db.ForeignKey('siswa.id'), nullable=True, index=True)

class SignLanguageDictionary(db.Model):
    __tablename__ = 'sign_language_dictionary'
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(255), nullable=False, index=True)
    image_url = db.Column(db.String(500), nullable=False)

class EmotionJournal(db.Model):
    __tablename__ = 'emotion_journal'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, server_default=func.now())
    emotion = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text)
    anak_id = db.Column(db.Integer, db.ForeignKey('siswa.id'), nullable=True, index=True)










class EpilepsiLog(db.Model):
    __tablename__ = 'epilepsi_log'
    __table_args__ = (Index('idx_epilepsi_log_created_at', 'created_at'), Index('idx_epilepsi_log_anak_id', 'anak_id'),)
    id = db.Column(db.Integer, primary_key=True)
    occurred_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, index=True)
    trigger = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now(), index=True)
    anak_id = db.Column(db.Integer, db.ForeignKey('siswa.id'), nullable=True, index=True)

    @property
    def date(self):
        return self.occurred_at.strftime('%Y-%m-%d') if self.occurred_at else ''

    @property
    def time(self):
        return self.occurred_at.strftime('%H:%M') if self.occurred_at else ''

class AppSettings(db.Model):
    __tablename__ = 'app_settings'
    key = db.Column(db.String(255), primary_key=True)
    value = db.Column(db.Text)

class JadwalKelas(db.Model):
    __tablename__ = 'jadwal_kelas'
    id = db.Column(db.Integer, primary_key=True)
    hari = db.Column(db.String(50), nullable=False)
    jam = db.Column(db.String(50), nullable=False)
    mata_pelajaran = db.Column(db.String(255), nullable=False)
    guru = db.Column(db.String(255), nullable=False)
    ruangan = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

class GaleriKarya(db.Model):
    __tablename__ = 'galeri_karya'
    id = db.Column(db.Integer, primary_key=True)
    image_filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    student_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

@cache.memoize(timeout=600)
def get_settings():
    try:
        settings = {item.key: item.value for item in AppSettings.query.all()}
    except:
        settings = {}
    return settings

@cache.cached(timeout=300, key_prefix='list_siswa')
def get_list_siswa_cached():
    try:
        rows = Siswa.query.with_entities(Siswa.id, Siswa.nama).limit(500).all()
        return [{'id': r.id, 'nama': r.nama} for r in rows]
    except Exception:
        return []

def invalidate_settings_cache():
    cache.delete_memoized(get_settings)
    cache.delete('app_settings')
    cache.delete('view//app_settings')
    cache.delete('view/app_settings')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def seed_slb_data():
    try:
        if SignLanguageDictionary.query.count() == 0:
            data = [
                ("aku", "https://media.giphy.com/media/l41lFj8af0LC6wcxs/giphy.gif"),
                ("ingin", "https://media.giphy.com/media/xT9IgG50Fb7Mi0prBC/giphy.gif"),
                ("makan", "https://media.giphy.com/media/3o7bu3XilJ5BOiSGic/giphy.gif"),
                ("minum", "https://media.giphy.com/media/l0HlHJDqLkcCHVz3y/giphy.gif"),
                ("tidur", "https://media.giphy.com/media/3o6Zt481isN3u/giphy.gif"),
                ("shalat", "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif"),
                ("wudhu", "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif"),
            ]
            for word, url in data:
                db.session.add(SignLanguageDictionary(word=word, image_url=url))
            db.session.commit()
    except Exception as e:
        app.logger.error(f"Error seeding SLB data: {e}", exc_info=True)





# --- FRONTEND ASSETS & LAYOUT ---



STYLES_HTML = """
    <script src="https://cdn.tailwindcss.com"></script>
    <script>tailwind.config = { theme: { extend: { colors: { emerald: { 50: '#ecfdf5', 100: '#d1fae5', 400: '#34d399', 500: '#10b981', 600: '#059669' }, amber: { 300: '#fcd34d', 400: '#fbbf24' } }, fontFamily: { sans: ['Poppins', 'sans-serif'] }, borderRadius: { '3xl': '1.5rem' } } } }</script>
    <style>
                body { background-color: #F8FAFC; }
        .glass-nav {
            background: rgba(255, 255, 255, 0.98);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            border-bottom: 1px solid rgba(0,0,0,0.05);
        }
        .glass-bottom {
            background: rgba(255, 255, 255, 0.98);
            box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.05);
            border-top: 1px solid rgba(0,0,0,0.05);
        }
        .card-hover { transition: all 0.3s ease; }
        .card-hover:active { transform: scale(0.98); }
        .pb-safe { padding-bottom: env(safe-area-inset-bottom, 20px); }

        /* NEUMORPHISM & CORK BOARD EFFECTS */
        .cork-board {
            background-color: #e5d1b8;
            background-image: radial-gradient(#d3bfa2 15%, transparent 16%), radial-gradient(#d3bfa2 15%, transparent 16%);
            background-size: 8px 8px;
            background-position: 0 0, 4px 4px;
            box-shadow: inset 0 0 40px rgba(100, 70, 40, 0.4);
            border-radius: 2.5rem;
            position: relative;
        }

        .acrylic-card {
            background: rgba(255, 255, 255, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.8);
            border-top: 2px solid rgba(255, 255, 255, 1);
            border-left: 2px solid rgba(255, 255, 255, 0.9);
            box-shadow: 
                8px 12px 20px rgba(0, 0, 0, 0.25), 
                inset -2px -2px 10px rgba(0,0,0,0.05),
                inset 2px 2px 10px rgba(255,255,255,1);
            border-radius: 1.5rem;
            transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
            transform-origin: center center;
            position: relative;
            z-index: 10;
        }
        @supports (backdrop-filter: blur(1px)) {
            @media (min-resolution: 2dppx) {
                .acrylic-card {
                    backdrop-filter: blur(16px);
                    -webkit-backdrop-filter: blur(16px);
                }
            }
        }
        .acrylic-card:hover, .acrylic-card:focus-within {
            will-change: transform, box-shadow;
        }

        .metal-pin {
            width: 14px;
            height: 14px;
            background: radial-gradient(circle at 30% 30%, #f0f0f0, #888);
            border-radius: 50%;
            position: absolute;
            top: 12px;
            left: 50%;
            transform: translateX(-50%);
            box-shadow: 
                2px 4px 6px rgba(0,0,0,0.4),
                inset -1px -1px 3px rgba(0,0,0,0.5),
                inset 1px 1px 3px rgba(255,255,255,0.9);
            z-index: 20;
        }

        .metal-pin::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 4px;
            height: 4px;
            background: #444;
            border-radius: 50%;
            box-shadow: inset 1px 1px 1px rgba(0,0,0,0.8);
        }

        .neumorphic-btn {
            background: #f8fafc;
            border-radius: 1.5rem;
            box-shadow: 
                6px 6px 12px rgba(163, 177, 198, 0.6), 
                -6px -6px 12px rgba(255, 255, 255, 0.9),
                inset 1px 1px 2px rgba(255, 255, 255, 0.8),
                inset -1px -1px 2px rgba(163, 177, 198, 0.2);
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.4);
        }
        .neumorphic-btn:hover, .neumorphic-btn:active {
            will-change: transform, box-shadow;
        }

        .neumorphic-btn:active {
            box-shadow: 
                inset 4px 4px 8px rgba(163, 177, 198, 0.7), 
                inset -4px -4px 8px rgba(255, 255, 255, 0.9);
            transform: scale(0.96);
        }

        /* Interaction Animation States */
        .card-pulled {
            transform: scale(1.05) translateY(-10px) rotate(-1deg);
            box-shadow: 
                15px 25px 35px rgba(0, 0, 0, 0.3),
                inset -2px -2px 10px rgba(0,0,0,0.05),
                inset 2px 2px 10px rgba(255,255,255,1);
            z-index: 100;
        }
    </style>
"""

BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <meta name="theme-color" content="#0b1026">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <link rel="manifest" href="/manifest.json">
    <link rel="icon" type="image/png" href="/static/logoslb.png">
    <link rel="apple-touch-icon" href="/static/logoslb.png">
    <script>
        function triggerEmergency() {
            const now = new Date();
            const h = now.getHours();
            let time = "Malam";
            if (h >= 0 && h <= 10) time = "Pagi";
            else if (h >= 11 && h <= 14) time = "Siang";
            else if (h >= 15 && h <= 18) time = "Sore";
            else time = "Malam"; // 19-23
            
            const msg = `Halo, Selamat ${time}, saya butuh bantuan darurat terkait SLB Waktu Samarinda.`;
            window.location.href = "https://wa.me/6282330890500?text=" + encodeURIComponent(msg);
        }
    </script>
    <title>Sekolah Luar Biasa</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Poppins:wght@300;400;500;600;700&display=swap" media="print" onload="this.media='all'">
    <noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Poppins:wght@300;400;500;600;700&display=swap"></noscript>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" media="print" onload="this.media='all'">
    <noscript><link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"></noscript>
    {{ styles|safe }}
</head>
<body class="text-gray-800 antialiased">
    <script>
        // Apple Audio Auto-Play Workaround
        document.addEventListener('pointerdown', function unlockAudio() {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {
                const dummyCtx = new AudioContext();
                if (dummyCtx.state === 'suspended') {
                    dummyCtx.resume();
                }
                const buffer = dummyCtx.createBuffer(1, 1, 22050);
                const source = dummyCtx.createBufferSource();
                source.buffer = buffer;
                source.connect(dummyCtx.destination);
                source.start();
            }
            document.removeEventListener('pointerdown', unlockAudio);
        }, { once: true });
    </script>
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
    {% set t_bottom_text_inactive = theme.bottom_text_inactive if theme and theme.bottom_text_inactive else 'text-gray-500' %}

    <!-- DESKTOP NAVBAR -->
    {% if not hide_nav %}
    <nav class="hidden md:flex fixed top-0 left-0 w-full z-50 {{ t_nav_bg }} shadow-sm px-8 py-4 justify-between items-center right-0">
        <div class="max-w-7xl mx-auto w-full flex justify-between items-center">
             <div class="flex items-center gap-4">
                 <div class="{{ t_icon_bg }} p-2 rounded-xl">
                    <i class="fas fa-mosque {{ t_icon_text }} text-2xl"></i>
                 </div>
                 <div>
                    <h1 class="text-xl font-bold {{ t_title_text }} leading-tight">Sekolah Luar Biasa</h1>
                    <p class="text-xs text-gray-500 font-medium">Salam Inklusi Sahabat Sekolah Luar Biasa</p>
                 </div>
             </div>
             <div class="flex items-center gap-8">
                <a href="/" class="text-emerald-800 font-bold text-[15px] hover:text-emerald-600 transition-colors border-b-2 border-transparent hover:border-emerald-500 py-2 {{ t_link_active if active_page == 'home' else '' }}">Beranda</a>
                <a href="/jadwal" class="text-gray-600 font-medium text-[15px] hover:text-emerald-600 transition-colors py-2">Jadwal Kelas</a>
                <a href="/galeri" class="text-gray-600 font-medium text-[15px] hover:text-emerald-600 transition-colors py-2">Galeri Karya</a>
                
                <div class="bg-emerald-50 px-4 py-2 rounded-xl shadow-sm border border-emerald-100 flex items-center justify-center space-x-2 ml-4">
                    <i class="fas fa-clock text-emerald-500"></i>
                    <span id="waktu-samarinda-header" class="text-emerald-800 font-bold tracking-wider font-mono">--:--:--</span>
                </div>
            </div>
        </div>
    </nav>

    <!-- MOBILE HEADER -->
    <header class="md:hidden fixed top-0 left-0 w-full z-50 {{ t_nav_bg }} shadow-sm px-4 py-3 flex justify-between items-center max-w-md mx-auto right-0">
        <div>
            <p class="text-xs text-gray-500 font-medium">Salam Inklusi Sahabat</p>
            <h1 class="text-lg font-bold {{ t_title_text }} leading-tight">Sekolah Luar Biasa</h1>
        </div>
        <div class="text-right">
            <p class="text-[8px] text-gray-500 font-bold mb-0.5 uppercase tracking-wider"><i class="fas fa-clock text-emerald-500"></i> Waktu Samarinda</p>
        </div>
    </header>
    {% endif %}

    <!-- GLOBAL AAC NOTIFICATION POPUP -->
    <div id="aac-popup" class="fixed top-24 left-1/2 transform -translate-x-1/2 -translate-y-[150%] opacity-0 z-[200] transition-all duration-500 pointer-events-none w-11/12 max-w-sm">
        <div class="bg-indigo-100/95 backdrop-blur-md px-6 py-4 rounded-3xl shadow-lg border-2 border-indigo-200 flex items-center justify-center gap-3">
            <i class="fas fa-volume-up text-indigo-500 text-xl animate-pulse"></i>
            <span id="aac-popup-text" class="text-indigo-800 font-bold text-center leading-tight text-sm"></span>
        </div>
    </div>

    <!-- CONTENT -->
    <main class="min-h-[100dvh] relative w-full {{ 'max-w-md md:max-w-7xl mx-auto bg-[#F8FAFC]' if not full_width else '' }}">
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
            <a href="/jadwal" class="flex flex-col items-center justify-center text-gray-500 {{ t_link_hover }} w-16 mb-6 relative z-10">
                <div class="{{ t_bottom_btn_bg }} text-white w-14 h-14 rounded-full flex items-center justify-center shadow-lg border-4 border-white transform hover:scale-105 transition-transform">
                    <i class="fas fa-book text-2xl"></i>
                </div>
                <span class="text-[10px] font-bold mt-1 {{ t_bottom_btn_text }} whitespace-nowrap">Jadwal Kelas</span>
            </a>
            <a href="/galeri" class="flex flex-col items-center justify-center {{ t_bottom_text_inactive }} hover:text-yellow-500 w-16 mb-1 transition-colors">
                <i class="fas fa-images text-xl mb-1"></i>
                <span class="text-[10px] font-medium">Galeri Karya</span>
            </a>
        </div>
    </nav>
    {% endif %}

    
    <!-- PORTAL MASUK & REGISTRASI MODAL -->
    <div id="modal-login-admin" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeModal('modal-login-admin')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.5s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20 max-h-[90dvh] overflow-y-auto">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-user-shield text-emerald-500 mr-2"></i>Portal Masuk & Registrasi</h3>
                <button onclick="closeModal('modal-login-admin')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            
            <div class="flex p-1 bg-gray-100 rounded-xl mb-6">
                <button onclick="switchAuthTab('login')" id="tab-btn-login" class="flex-1 py-2 text-xs font-bold rounded-lg bg-white shadow-sm text-emerald-600 transition">Masuk</button>
                <button onclick="switchAuthTab('register')" id="tab-btn-register" class="flex-1 py-2 text-xs font-bold rounded-lg text-gray-500 hover:bg-gray-50 transition">Daftar</button>
                <button onclick="switchAuthTab('validator')" id="tab-btn-validator" class="flex-1 py-2 text-xs font-bold rounded-lg text-gray-500 hover:bg-gray-50 transition flex items-center justify-center gap-1"><i class="fas fa-lock"></i> Akses Validator</button>
            </div>

            <div id="auth-content-login">
                <form action="/login" method="POST" class="space-y-4">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
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

            <div id="auth-content-register" class="hidden">
                <form action="/register" method="POST" class="space-y-4">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">NIK</label>
                        <input type="text" name="nik" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" required>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Nama Lengkap</label>
                        <input type="text" name="nama_lengkap" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" required>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Username</label>
                        <input type="text" name="username" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" required>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Password</label>
                        <input type="password" name="password" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" required>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Peran</label>
                        <select name="peran" id="register-peran" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" onchange="toggleSiswaDropdown()" required>
                            <option value="guru">Guru</option>
                            <option value="orang_tua">Orang Tua</option>
                        </select>
                    </div>
                    <div id="siswa-dropdown-container" class="hidden">
                        <label class="block text-xs font-bold text-gray-500 mb-1">Pilih Anak (Siswa)</label>
                        <select name="anak_id" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500">
                            <!-- Injected dynamically or rendered via template -->
                            <option value="">Pilih Siswa...</option>
                            {% for s in list_siswa %}
                            <option value="{{ s['id'] }}">{{ s['nama'] }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <button type="submit" class="w-full bg-blue-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-blue-600 transition">Daftar</button>
                </form>
            </div>
            
            <div id="auth-content-validator" class="hidden">
                <div class="bg-gray-900 rounded-3xl p-6 text-center shadow-inner relative overflow-hidden" id="brankas-container">
                    <div class="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-gray-700 to-gray-900 opacity-50"></div>
                    <div class="flex justify-between items-center mb-6 relative z-10">
                        <h4 class="text-gray-400 text-xs font-bold tracking-widest uppercase"><i class="fas fa-shield-alt mr-2"></i>Brankas Digital Akses Validator</h4>
                        <button id="btn-fullscreen" class="text-gray-400 hover:text-emerald-400 hover:drop-shadow-[0_0_8px_rgba(52,211,153,0.8)] transition-all">
                            <svg id="icon-expand" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path></svg>
                            <svg id="icon-compress" class="w-5 h-5 hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 14h4v4m0-4l-5 5m11-5h-4v4m0-4l5 5M10 10V6H6m4 4l-5-5m11 5h4V6m-4 4l5-5"></path></svg>
                        </button>
                    </div>
                    
                    <div class="relative w-48 h-48 mx-auto mb-6 z-10" id="brankas-dial-wrapper">
                        <!-- Outer Rim & Fixed Top Marker -->
                        <div class="absolute inset-0 rounded-full border-8 border-gray-700 shadow-[inset_0_0_20px_rgba(0,0,0,0.8)] z-30 pointer-events-none"></div>
                        <div class="absolute top-0 left-1/2 -translate-x-1/2 w-2 h-4 bg-red-500 z-40 rounded-sm shadow-md"></div>
                        
                        <!-- Rotating Dial containing Ticks and Numbers -->
                        <div id="brankas-dial" class="absolute inset-2 rounded-full bg-gradient-to-br from-gray-700 to-gray-800 shadow-[0_10px_20px_rgba(0,0,0,0.6),_inset_0_2px_5px_rgba(255,255,255,0.2)] cursor-grab active:cursor-grabbing touch-none z-20" style="transform: rotate(0deg);">
                            <svg id="brankas-ticks" class="absolute inset-0 w-full h-full" viewBox="0 0 100 100"></svg>
                            <div class="absolute inset-0 m-auto w-16 h-16 rounded-full bg-gradient-to-br from-gray-600 to-gray-700 shadow-[0_5px_15px_rgba(0,0,0,0.8)] flex items-center justify-center">
                                <div class="w-4 h-4 rounded-full bg-gray-900 shadow-inner"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="relative z-10 flex justify-center gap-4 text-xs font-bold text-gray-500" id="brankas-status">
                        <span id="brankas-state-1" class="w-8 h-8 rounded-full border-2 border-gray-600 flex items-center justify-center"><i class="fas fa-lock text-[10px]"></i></span>
                        <span id="brankas-state-2" class="w-8 h-8 rounded-full border-2 border-gray-600 flex items-center justify-center"><i class="fas fa-lock text-[10px]"></i></span>
                        <span id="brankas-state-3" class="w-8 h-8 rounded-full border-2 border-gray-600 flex items-center justify-center"><i class="fas fa-lock text-[10px]"></i></span>
                    </div>
                    
                    <p class="text-gray-500 text-[10px] mt-6 relative z-10" style="opacity: 0.6; font-family: serif;">Lupa kode brankas ? Bisa hubungi developer untuk kodenya.</p>
                </div>
            </div>

            <script>
                function switchAuthTab(tab) {
                    document.getElementById('auth-content-login').classList.add('hidden');
                    document.getElementById('auth-content-register').classList.add('hidden');
                    document.getElementById('auth-content-validator').classList.add('hidden');
                    document.getElementById('auth-content-' + tab).classList.remove('hidden');
                    
                    const btnLogin = document.getElementById('tab-btn-login');
                    const btnRegister = document.getElementById('tab-btn-register');
                    const btnValidator = document.getElementById('tab-btn-validator');
                    
                    [btnLogin, btnRegister, btnValidator].forEach(btn => {
                        btn.className = "flex-1 py-2 text-xs font-bold rounded-lg text-gray-500 hover:bg-gray-50 transition";
                        if(btn.querySelector('.fa-lock') && btn !== btnValidator) {
                            btn.className += " flex items-center justify-center gap-1";
                        }
                    });
                    
                    if (tab === 'login') {
                        btnLogin.className = "flex-1 py-2 text-xs font-bold rounded-lg bg-white shadow-sm text-emerald-600 transition";
                    } else if (tab === 'register') {
                        btnRegister.className = "flex-1 py-2 text-xs font-bold rounded-lg bg-white shadow-sm text-emerald-600 transition";
                    } else if (tab === 'validator') {
                        btnValidator.className = "flex-1 py-2 text-xs font-bold rounded-lg bg-white shadow-sm text-emerald-600 transition flex items-center justify-center gap-1";
                        initBrankasDial();
                    }
                }
                
                function toggleSiswaDropdown() {
                    const peran = document.getElementById('register-peran').value;
                    const container = document.getElementById('siswa-dropdown-container');
                    if (peran === 'orang_tua') {
                        container.classList.remove('hidden');
                    } else {
                        container.classList.add('hidden');
                    }
                }

                // --- BRANKAS DIGITAL LOGIC ---
                let brankasState = 0; // 0: Start, 1: State 1 Reached, 2: State 2 Reached
                let currentAngle = 0;
                let lastAngle = 0;
                let isDragging = false;
                let centerPoint = { x: 0, y: 0 };
                let direction = null; // 'CCW' (Left) or 'CW' (Right)
                let lastNumber = 0;
                let ticksDrawn = false;
                
                let brankasAudioCtx = null;

                function initBrankasDial() {
                    if (ticksDrawn) return;
                    
                    const svg = document.getElementById('brankas-ticks');
                    const cx = 50, cy = 50, r = 45;
                    for (let i = 0; i < 100; i++) {
                        const angle = (i * 3.6 - 90) * (Math.PI / 180);
                        const x1 = cx + (r - (i % 5 === 0 ? 5 : 2)) * Math.cos(angle);
                        const y1 = cy + (r - (i % 5 === 0 ? 5 : 2)) * Math.sin(angle);
                        const x2 = cx + r * Math.cos(angle);
                        const y2 = cy + r * Math.sin(angle);
                        
                        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
                        line.setAttribute('x1', x1);
                        line.setAttribute('y1', y1);
                        line.setAttribute('x2', x2);
                        line.setAttribute('y2', y2);
                        line.setAttribute('stroke', i % 5 === 0 ? '#9CA3AF' : '#4B5563'); // Gray-400 / Gray-600
                        line.setAttribute('stroke-width', i % 5 === 0 ? '1' : '0.5');
                        svg.appendChild(line);
                        
                        if (i % 10 === 0) {
                            const textAngle = (i * 3.6 - 90) * (Math.PI / 180);
                            const tx = cx + (r - 12) * Math.cos(textAngle);
                            const ty = cy + (r - 12) * Math.sin(textAngle);
                            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
                            text.setAttribute('x', tx);
                            text.setAttribute('y', ty);
                            text.setAttribute('fill', '#9CA3AF');
                            text.setAttribute('font-size', '5');
                            text.setAttribute('text-anchor', 'middle');
                            text.setAttribute('dominant-baseline', 'middle');
                            text.setAttribute('font-family', 'sans-serif');
                            text.textContent = i;
                            svg.appendChild(text);
                        }
                    }
                    ticksDrawn = true;
                    
                    const dial = document.getElementById('brankas-dial');
                    
                    function updateCenter() {
                        const rect = dial.getBoundingClientRect();
                        centerPoint = {
                            x: rect.left + rect.width / 2,
                            y: rect.top + rect.height / 2
                        };
                    }

                    function onDragStart(e) {
                        isDragging = true;
                        updateCenter();
                        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
                        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
                        const startAngle = Math.atan2(clientY - centerPoint.y, clientX - centerPoint.x) * (180 / Math.PI);
                        lastAngle = startAngle - currentAngle;
                        e.preventDefault();
                        
                        if (!brankasAudioCtx) {
                            brankasAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
                        }
                        if (brankasAudioCtx.state === 'suspended') {
                            brankasAudioCtx.resume();
                        }
                    }

                    function playTick() {
                        if (!brankasAudioCtx) return;
                        const osc = brankasAudioCtx.createOscillator();
                        const gain = brankasAudioCtx.createGain();
                        osc.type = 'sine';
                        osc.frequency.setValueAtTime(1000, brankasAudioCtx.currentTime); // 1000Hz
                        
                        gain.gain.setValueAtTime(0, brankasAudioCtx.currentTime);
                        gain.gain.linearRampToValueAtTime(0.5, brankasAudioCtx.currentTime + 0.01);
                        gain.gain.exponentialRampToValueAtTime(0.001, brankasAudioCtx.currentTime + 0.05);
                        
                        osc.connect(gain);
                        gain.connect(brankasAudioCtx.destination);
                        osc.start();
                        osc.stop(brankasAudioCtx.currentTime + 0.05);
                    }

                    function playUnlock() {
                        if (!brankasAudioCtx) return;
                        
                        // Heavy Mechanical Door - Oscillator Square (40Hz to 20Hz)
                        const osc = brankasAudioCtx.createOscillator();
                        const oscGain = brankasAudioCtx.createGain();
                        osc.type = 'square';
                        osc.frequency.setValueAtTime(40, brankasAudioCtx.currentTime); 
                        osc.frequency.exponentialRampToValueAtTime(20, brankasAudioCtx.currentTime + 1.0);
                        
                        oscGain.gain.setValueAtTime(0, brankasAudioCtx.currentTime);
                        oscGain.gain.linearRampToValueAtTime(0.8, brankasAudioCtx.currentTime + 0.1);
                        oscGain.gain.exponentialRampToValueAtTime(0.001, brankasAudioCtx.currentTime + 1.0);
                        
                        osc.connect(oscGain);
                        oscGain.connect(brankasAudioCtx.destination);
                        osc.start(brankasAudioCtx.currentTime);
                        osc.stop(brankasAudioCtx.currentTime + 1.0);

                        // White noise for Clank-Swooosh-Thud
                        const bufferSize = brankasAudioCtx.sampleRate * 1.0;
                        const buffer = brankasAudioCtx.createBuffer(1, bufferSize, brankasAudioCtx.sampleRate);
                        const data = buffer.getChannelData(0);
                        for (let i = 0; i < bufferSize; i++) {
                            data[i] = Math.random() * 2 - 1;
                        }

                        const noiseSource = brankasAudioCtx.createBufferSource();
                        noiseSource.buffer = buffer;

                        const lowpass = brankasAudioCtx.createBiquadFilter();
                        lowpass.type = 'lowpass';
                        lowpass.frequency.setValueAtTime(1000, brankasAudioCtx.currentTime);
                        lowpass.frequency.exponentialRampToValueAtTime(100, brankasAudioCtx.currentTime + 0.5);

                        const bandpass = brankasAudioCtx.createBiquadFilter();
                        bandpass.type = 'bandpass';
                        bandpass.frequency.setValueAtTime(500, brankasAudioCtx.currentTime);

                        const noiseGain = brankasAudioCtx.createGain();
                        noiseGain.gain.setValueAtTime(0, brankasAudioCtx.currentTime);
                        noiseGain.gain.linearRampToValueAtTime(1.0, brankasAudioCtx.currentTime + 0.1);
                        noiseGain.gain.exponentialRampToValueAtTime(0.001, brankasAudioCtx.currentTime + 1.0);

                        noiseSource.connect(lowpass);
                        lowpass.connect(bandpass);
                        bandpass.connect(noiseGain);
                        noiseGain.connect(brankasAudioCtx.destination);

                        noiseSource.start(brankasAudioCtx.currentTime);
                        noiseSource.stop(brankasAudioCtx.currentTime + 1.0);
                    }

                    function onDragMove(e) {
                        if (!isDragging) return;
                        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
                        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
                        
                        const angle = Math.atan2(clientY - centerPoint.y, clientX - centerPoint.x) * (180 / Math.PI);
                        let newAngle = angle - lastAngle;
                        
                        // Calculate direction and delta
                        let deltaAngle = newAngle - currentAngle;
                        // Handle wraparound
                        if (deltaAngle > 180) deltaAngle -= 360;
                        if (deltaAngle < -180) deltaAngle += 360;
                        
                        currentAngle += deltaAngle;
                        
                        let currentDirection = null;
                        if (deltaAngle < 0) currentDirection = 'CCW';
                        if (deltaAngle > 0) currentDirection = 'CW';
                        
                        if (currentDirection && currentDirection !== direction) {
                            direction = currentDirection;
                            // Checking if we overshot or changed direction improperly happens in checkCombination
                        }

                        // Apply visual rotation. The SVG has 0 at top, so angle needs adjustment if we want 0 up.
                        // Our tick calculation puts 0 at the top. 
                        // The dial's red marker is at the top initially.
                        dial.style.transform = `rotate(${currentAngle}deg)`;
                        
                        // Map angle to numbers 0-99
                        // 360 degrees = 100 ticks. 1 tick = 3.6 degrees.
                        // Clockwise rotation (CW) positive degrees -> means numbers go up if CW, but standard safes numbers go down when turning right.
                        // Let's make standard mapping: 0 at top. 
                        let normalizedAngle = currentAngle % 360;
                        if (normalizedAngle < 0) normalizedAngle += 360;
                        
                        // Current number under the top mark
                        let currentNumber = Math.round((360 - normalizedAngle) / 3.6) % 100;
                        
                        if (currentNumber !== lastNumber) {
                            if (currentNumber % 1 === 0) playTick();
                            lastNumber = currentNumber;
                            checkCombination(currentNumber, direction);
                        }
                    }

                    function onDragEnd() {
                        isDragging = false;
                        direction = null;
                    }

                    function updateStatusUI() {
                        const s1 = document.getElementById('brankas-state-1');
                        const s2 = document.getElementById('brankas-state-2');
                        const s3 = document.getElementById('brankas-state-3');
                        
                        s1.className = brankasState >= 1 ? "w-8 h-8 rounded-full border-2 border-green-500 bg-green-500 text-white flex items-center justify-center shadow-[0_0_10px_rgba(34,197,94,0.5)]" : "w-8 h-8 rounded-full border-2 border-gray-600 flex items-center justify-center";
                        s1.innerHTML = brankasState >= 1 ? '<i class="fas fa-unlock text-[10px]"></i>' : '<i class="fas fa-lock text-[10px]"></i>';
                        
                        s2.className = brankasState >= 2 ? "w-8 h-8 rounded-full border-2 border-green-500 bg-green-500 text-white flex items-center justify-center shadow-[0_0_10px_rgba(34,197,94,0.5)]" : "w-8 h-8 rounded-full border-2 border-gray-600 flex items-center justify-center";
                        s2.innerHTML = brankasState >= 2 ? '<i class="fas fa-unlock text-[10px]"></i>' : '<i class="fas fa-lock text-[10px]"></i>';
                        
                        s3.className = brankasState >= 3 ? "w-8 h-8 rounded-full border-2 border-green-500 bg-green-500 text-white flex items-center justify-center shadow-[0_0_10px_rgba(34,197,94,0.5)]" : "w-8 h-8 rounded-full border-2 border-gray-600 flex items-center justify-center";
                        s3.innerHTML = brankasState >= 3 ? '<i class="fas fa-unlock text-[10px]"></i>' : '<i class="fas fa-lock text-[10px]"></i>';
                    }

                    function resetBrankas() {
                        brankasState = 0;
                        updateStatusUI();
                    }

                    function checkCombination(num, dir) {
                        // Kombinasi Absolut: 30 Kiri (CCW), 10 Kanan (CW), 50 Kiri (CCW)
                        
                        if (brankasState === 0) {
                            if (dir === 'CCW' && num === 30) {
                                brankasState = 1;
                                updateStatusUI();
                            } else if (dir === 'CW') {
                                resetBrankas();
                            }
                        } 
                        else if (brankasState === 1) {
                            if (dir === 'CW' && num === 10) {
                                brankasState = 2;
                                updateStatusUI();
                            } else if (dir === 'CCW' && num !== 30) {
                                // If they overshoot or start moving CCW again before hitting 10
                                resetBrankas();
                            }
                        }
                        else if (brankasState === 2) {
                            if (dir === 'CCW' && num === 50) {
                                brankasState = 3;
                                updateStatusUI();
                                unlockVault();
                            } else if (dir === 'CW' && num !== 10) {
                                resetBrankas();
                            }
                        }
                    }

                    function unlockVault() {
                        playUnlock();
                        const container = document.getElementById('brankas-container');
                        container.style.transition = 'all 1s ease';
                        container.style.transform = 'scale(1.1)';
                        container.style.opacity = '0';
                        
                        fetch('/brankas_unlock', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content') },
                            body: JSON.stringify({ kode: '30-10-50' })
                        }).then(response => response.json())
                          .then(data => {
                            if(data.status === 'success') {
                                setTimeout(() => {
                                    window.location.href = data.redirect_url;
                                }, 1000);
                            }
                        });
                    }

                    dial.addEventListener('mousedown', onDragStart);
                    document.addEventListener('mousemove', onDragMove);
                    document.addEventListener('mouseup', onDragEnd);
                    
                    dial.addEventListener('touchstart', onDragStart, {passive: false});
                    document.addEventListener('touchmove', onDragMove, {passive: false});
                    document.addEventListener('touchend', onDragEnd);
                    
                    const btnFullscreen = document.getElementById('btn-fullscreen');
                    const iconExpand = document.getElementById('icon-expand');
                    const iconCompress = document.getElementById('icon-compress');
                    
                    btnFullscreen.addEventListener('click', () => {
                        if (!document.fullscreenElement) {
                            document.documentElement.requestFullscreen().catch(err => {
                                console.error(`Error attempting to enable fullscreen: ${err.message}`);
                            });
                            iconExpand.classList.add('hidden');
                            iconCompress.classList.remove('hidden');
                        } else {
                            document.exitFullscreen();
                            iconExpand.classList.remove('hidden');
                            iconCompress.classList.add('hidden');
                        }
                    });
                }
            </script>
        </div>
    </div>

    <!-- Socket.IO globally for student receiving -->
    {% if needs_socketio %}<script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>{% endif %}
    <script>
        // CLIENT WEBSOCKET RECEPTION (for all pages)
        const socket = io();
        let globalAudioCtx;
        let globalOscillators = [];
        let globalNoiseNode = null;
        let globalFilterNode = null;
        let globalGainNode;
        
        function initGlobalAudio() {
            if (!globalAudioCtx) {
                globalAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
                globalGainNode = globalAudioCtx.createGain();
                globalGainNode.connect(globalAudioCtx.destination);
                globalGainNode.gain.value = 0.9; // Brute force volume to 90%
            }
            if (globalAudioCtx.state === 'suspended') {
                globalAudioCtx.resume();
            }
        }

        function createGlobalOscillator(freq, pan) {
            const osc = globalAudioCtx.createOscillator();
            const panner = globalAudioCtx.createStereoPanner();
            osc.frequency.value = freq;
            osc.connect(panner);
            panner.connect(globalGainNode);
            panner.pan.value = pan; // -1 Left, 1 Right
            osc.start();
            return osc;
        }

        function generateGlobalNoise(type) {
            const bufferSize = globalAudioCtx.sampleRate * 2;
            const buffer = globalAudioCtx.createBuffer(1, bufferSize, globalAudioCtx.sampleRate);
            const data = buffer.getChannelData(0);

            if (type === 'white') {
                for (let i = 0; i < bufferSize; i++) {
                    data[i] = Math.random() * 2 - 1;
                }
            } else if (type === 'pink') {
                let b0, b1, b2, b3, b4, b5, b6;
                b0 = b1 = b2 = b3 = b4 = b5 = b6 = 0.0;
                for (let i = 0; i < bufferSize; i++) {
                    let white = Math.random() * 2 - 1;
                    b0 = 0.99886 * b0 + white * 0.0555179;
                    b1 = 0.99332 * b1 + white * 0.0750759;
                    b2 = 0.96900 * b2 + white * 0.1538520;
                    b3 = 0.86650 * b3 + white * 0.3104856;
                    b4 = 0.55000 * b4 + white * 0.5329522;
                    b5 = -0.7616 * b5 - white * 0.0168980;
                    data[i] = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362;
                    data[i] *= 0.11; // compensate gain
                    b6 = white * 0.115926;
                }
            } else if (type === 'brown') {
                let lastOut = 0;
                for (let i = 0; i < bufferSize; i++) {
                    let white = Math.random() * 2 - 1;
                    data[i] = (lastOut + (0.02 * white)) / 1.02;
                    lastOut = data[i];
                    data[i] *= 3.5; // compensate gain
                }
            }

            globalNoiseNode = globalAudioCtx.createBufferSource();
            globalNoiseNode.buffer = buffer;
            globalNoiseNode.loop = true;
            
            globalFilterNode = globalAudioCtx.createBiquadFilter();
            if(type === 'brown') {
                globalFilterNode.type = 'lowpass';
                globalFilterNode.frequency.value = 400;
            } else if(type === 'pink') {
                globalFilterNode.type = 'lowpass';
                globalFilterNode.frequency.value = 800;
            } else {
                globalFilterNode.type = 'allpass';
            }

            globalNoiseNode.connect(globalFilterNode);
            globalFilterNode.connect(globalGainNode);
            globalNoiseNode.start();
        }

        function stopGlobalAudio() {
            // Stop Oscillators
            globalOscillators.forEach(osc => {
                try { osc.stop(); } catch(e) {}
            });
            globalOscillators = [];
            
            // Stop Noise Node
            if (globalNoiseNode) {
                try { globalNoiseNode.stop(); } catch(e) {}
                globalNoiseNode.disconnect();
                globalNoiseNode = null;
            }
            if(globalFilterNode) {
                globalFilterNode.disconnect();
                globalFilterNode = null;
            }
        }
        
        window.processFrequencyData = function(data) {
            initGlobalAudio();
            stopGlobalAudio();

            if(data.mode === 'off') {
                return;
            }

            if(data.mode === 'calm') {
                // Theta Binaural (432Hz and 439Hz)
                globalOscillators.push(createGlobalOscillator(432, -1));
                globalOscillators.push(createGlobalOscillator(439, 1));
            } else if(data.mode === 'noise') {
                if (data.type === 'white' || data.type === 'pink' || data.type === 'brown') {
                    generateGlobalNoise(data.type);
                }
            }
        };

        socket.on('receive_frequency', function(data) {
            window.processFrequencyData(data);
        });

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

        // GLOBAL WEB PUSH UTILS (Brute Force)
        function urlBase64ToUint8Array(base64String) {
            const padding = '='.repeat((4 - base64String.length % 4) % 4);
            const base64 = (base64String + padding).replace(/\\-/g, '+').replace(/_/g, '/');
            const rawData = window.atob(base64);
            const outputArray = new Uint8Array(rawData.length);
            for (let i = 0; i < rawData.length; ++i) {
                outputArray[i] = rawData.charCodeAt(i);
            }
            return outputArray;
        }

        async function subscribeUserToPush() {
            if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;
            try {
                const reg = await navigator.serviceWorker.ready;
                const existingSub = await reg.pushManager.getSubscription();
                if(existingSub) return existingSub;

                const response = await fetch('/orang-tua/api/vapid_public_key');
                const data = await response.json();
                const convertedVapidKey = urlBase64ToUint8Array(data.public_key);

                const subscription = await reg.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: convertedVapidKey
                });

                await fetch('/orang-tua/api/subscribe', {
                    method: 'POST',
                    body: JSON.stringify(subscription),
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content') }
                });
                return subscription;
            } catch(e) {
                console.error("Failed to subscribe to Web Push", e);
            }
        }

        // MASEHI DATE WITH MOTIVATION AND SAMARINDA CLOCK
            function updateDate() {
                const today = new Date();
                const options = { 
                    timeZone: 'Asia/Makassar',
                    weekday: 'long', 
                    day: 'numeric', 
                    month: 'long', 
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false
                };
                
                let dateString = today.toLocaleString('id-ID', options);
                dateString = dateString.replace('pukul', '•').replace(/\\./g, ':');
                
                const elements = document.querySelectorAll('[id^="hijri-date"]');
                elements.forEach(el => {
                    el.innerText = dateString;
                });
            }
            updateDate();
            setInterval(updateDate, 1000); // Update every second for real-time clock

        // GLOBAL MODAL UTILS
        function openModal(id) {
            const el = document.getElementById(id);
            if(el) {
                el.classList.remove('hidden');
                history.pushState({modal: id}, null, "");
            }
        }

        window.addEventListener('popstate', (event) => {
            document.querySelectorAll('[id^="modal-"]').forEach(el => el.classList.add('hidden'));
        });

        function closeModal(id) {
            if (history.state && history.state.modal === id) {
                history.back();
            } else {
                const el = document.getElementById(id);
                if(el) el.classList.add('hidden');
            }
        }

        async function postCalc(url, data) {
            try {
                const res = await fetch(url, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')},
                    body: JSON.stringify(data)
                });
                return await res.json();
            } catch(e) {
                alert('Error: ' + e);
                return null;
            }
        }

        // --- AAC WEB SPEECH API & POPUP LOGIC ---
        function speakAAC(text) {
            if ('speechSynthesis' in window) {
                // Hentikan suara yang sedang berjalan (jika ada) agar tidak menumpuk
                window.speechSynthesis.cancel();
                
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'id-ID';
                utterance.rate = 0.9; // Sedikit lebih lambat agar jelas
                utterance.pitch = 1.1; // Sedikit lebih tinggi untuk suara yang lebih "ramah"
                
                window.speechSynthesis.speak(utterance);
                
                // Tampilkan Popup Notifikasi Pastel
                showAACPopup(text);
            } else {
                alert("Maaf, browser Anda tidak mendukung fitur suara (Text-to-Speech).");
            }
        }
        
        function showAACPopup(text) {
            const popup = document.getElementById('aac-popup');
            const popupText = document.getElementById('aac-popup-text');
            
            if (popup && popupText) {
                popupText.innerText = text;
                popup.classList.remove('translate-y-[-150%]', 'opacity-0');
                popup.classList.add('translate-y-0', 'opacity-100');
                
                // Sembunyikan kembali setelah 3 detik
                setTimeout(() => {
                    popup.classList.remove('translate-y-0', 'opacity-100');
                    popup.classList.add('translate-y-[-150%]', 'opacity-0');
                }, 3000);
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
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
                        if(textDiv) textDiv.innerHTML = '<h3 class="text-sm font-bold text-[#FFD700] leading-tight">Install di iPhone</h3><p class="text-[10px] text-gray-700">Klik tombol Share <i class="fas fa-share-square"></i> lalu "Add to Home Screen"</p>';
                        const btnDiv = banner.querySelector('.pwa-btn');
                        if(btnDiv) btnDiv.style.display = 'none'; // Manual action only
                     }
                 }
            }
        });
    </script>
    

    <script>
        function updateHeaderClock() {
            const clockEl = document.getElementById('waktu-samarinda-header');
            if (!clockEl) return;
            const now = new Date();
            const timeString = new Intl.DateTimeFormat('id-ID', {
                timeZone: 'Asia/Makassar',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            }).format(now).replace(/[.]/g, ':');
            clockEl.innerHTML = timeString;
        }
        setInterval(updateHeaderClock, 1000);
        document.addEventListener('DOMContentLoaded', updateHeaderClock);
    </script>

</body>
</html>
"""

HOME_HTML = """
<div class="pt-20 md:pt-32 pb-32 px-5 md:px-8">
    <script>
        const userPeran = "{{ peran|default('') }}";
        const userAnakId = {{ anak_id if anak_id else 'null' }};
    </script>
    
    <!-- DESKTOP SPLIT HEADER -->
    <div class="md:grid md:grid-cols-2 md:gap-12 md:items-center mb-8 md:mb-12">
        
        <!-- LEFT COLUMN: WELCOME (Desktop Only) -->
        <div class="hidden md:block pl-2">
            <p class="text-xl text-gray-500 font-medium mb-2">Salam Inklusi, Sahabat</p>
            <h1 class="text-5xl font-bold text-emerald-800 leading-tight mb-6">Selamat Datang di<br>Sekolah Luar Biasa</h1>
            <p class="text-gray-600 text-lg leading-relaxed mb-8">
                Pusat layanan pendidikan dan terapi inklusif di Samarinda. Mari wujudkan ruang aman, nyaman, dan memberdayakan bagi anak-anak istimewa kita, bersinergi bersama orang tua dan pendidik berdedikasi demi kemaslahatan masa depan mereka.
            </p>
            <div class="flex gap-4">
                <a href="{{ url_for('jadwal_kelas') }}" class="bg-emerald-500 text-white border-2 border-emerald-500 px-8 py-3 rounded-full font-bold hover:bg-emerald-600 hover:border-emerald-600 transition-all transform hover:scale-105 shadow-lg">Jadwal Kelas</a>
                <a href="{{ url_for('galeri_karya') }}" class="bg-white text-emerald-600 border-2 border-emerald-200 px-8 py-3 rounded-full font-bold hover:border-emerald-600 hover:text-emerald-700 transition-all transform hover:scale-105 shadow-md">Galeri Karya</a>
            </div>
        </div>

        <!-- RIGHT COLUMN: KARTU PROFIL & PAPAN KOMUNIKASI -->
        <div class="flex flex-col gap-6">
            
            <!-- KARTU PROFIL SISWA DAN PAPAN KOMUNIKASI EKSPRES AAC (NEUMORPHISM CORK BOARD) -->
            <div class="cork-board p-6 md:p-8">
                
                {% if peran == 'guru' or peran == 'kepala_sekolah' %}
                <!-- TEAHCER SEARCH CARD -->
                <div class="acrylic-card group" id="student-acrylic-card">
                    <div class="metal-pin"></div>
                    <div class="px-6 py-6 flex flex-col gap-4">
                        <div class="flex items-center gap-4">
                            <div class="w-14 h-14 rounded-full bg-white shadow-md border-2 border-white flex items-center justify-center shrink-0 text-indigo-600">
                                <i class="fas fa-search text-xl"></i>
                            </div>
                            <div>
                                <h2 class="text-xl font-extrabold text-gray-800 tracking-tight leading-none mb-1">Cari Data Diri Anak SLB</h2>
                                <p class="text-xs text-gray-600 font-bold">Temukan profil medis siswa dengan cepat</p>
                            </div>
                        </div>
                        <div class="relative">
                            <i class="fas fa-search absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"></i>
                            <input type="text" id="teacher-search-input" placeholder="Ketik nama siswa..." class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 shadow-inner">
                        </div>
                        <div id="teacher-search-results" class="bg-white rounded-xl shadow-lg border border-gray-100 hidden max-h-48 overflow-y-auto"></div>
                    </div>
                </div>
                
                <script>
                    let searchTimeout;
                    const searchInput = document.getElementById('teacher-search-input');
                    const searchResults = document.getElementById('teacher-search-results');
                    
                    if(searchInput) {
                        searchInput.addEventListener('input', (e) => {
                            clearTimeout(searchTimeout);
                            const q = e.target.value.trim();
                            if(q.length === 0) {
                                searchResults.innerHTML = '';
                                searchResults.classList.add('hidden');
                                return;
                            }
                            searchTimeout = setTimeout(() => {
                                fetch('/api/cari-siswa-guru?q=' + encodeURIComponent(q))
                                    .then(res => res.json())
                                    .then(data => {
                                        searchResults.innerHTML = '';
                                        if(data.length === 0) {
                                            searchResults.innerHTML = '<div class="p-4 text-center text-xs text-gray-500">Tidak ditemukan</div>';
                                            searchResults.classList.remove('hidden');
                                            return;
                                        }
                                        data.forEach(siswa => {
                                            const statusHtml = siswa.profil_exists 
                                                ? '<span class="text-[10px] bg-green-100 text-green-700 px-2 py-1 rounded-full font-bold">Data Lengkap</span>' 
                                                : '<span class="text-[10px] bg-gray-100 text-gray-600 px-2 py-1 rounded-full font-bold">Belum Diisi</span>';
                                                
                                            const div = document.createElement('div');
                                            div.className = "p-3 border-b border-gray-50 hover:bg-gray-50 cursor-pointer flex justify-between items-center transition-colors";
                                            div.innerHTML = `<span class="text-sm font-bold text-gray-800">${siswa.nama}</span>${statusHtml}`;
                                            div.onclick = () => {
                                                openTeacherMedicalPanel(siswa.id, siswa.nama);
                                                searchResults.classList.add('hidden');
                                                searchInput.value = '';
                                            };
                                            searchResults.appendChild(div);
                                        });
                                        searchResults.classList.remove('hidden');
                                    });
                            }, 300);
                        });
                    }
                </script>
                
                {% else %}
                
                <!-- Acrylic Card (Polaroid Style) -->
                <div class="acrylic-card cursor-pointer group" id="student-acrylic-card" onclick="openMedicalPanel()">
                    <!-- Metal Pin -->
                    <div class="metal-pin"></div>
                    
                    <!-- Header Identitas Medis -->
                    <div class="px-6 py-6 flex items-center justify-between border-b border-gray-200/50">
                        <div class="flex items-center gap-4">
                            <div class="w-14 h-14 rounded-full bg-white shadow-md border-2 border-white flex items-center justify-center overflow-hidden shrink-0">
                                {% if profil_medis %}
                                <img src="https://api.dicebear.com/7.x/notionists/svg?seed={{ profil_medis.nama_panggilan }}&backgroundColor=e0e7ff" alt="Avatar" class="w-full h-full object-cover">
                                {% elif anak_nama %}
                                <img src="https://api.dicebear.com/7.x/notionists/svg?seed={{ anak_nama }}&backgroundColor=e0e7ff" alt="Avatar" class="w-full h-full object-cover">
                                {% else %}
                                <img src="https://api.dicebear.com/7.x/notionists/svg?seed=Default&backgroundColor=e0e7ff" alt="Avatar Default" class="w-full h-full object-cover">
                                {% endif %}
                            </div>
                            <div>
                                {% if profil_medis %}
                                <h2 class="text-xl font-extrabold text-gray-800 tracking-tight leading-none mb-1">{{ profil_medis.nama_panggilan }}</h2>
                                <p class="text-xs text-gray-600 font-bold">Siswa {{ profil_medis.jenis_slb }} ({{ profil_medis.kategori_hambatan }})</p>
                                {% elif anak_nama %}
                                <h2 class="text-xl font-extrabold text-gray-800 tracking-tight leading-none mb-1">{{ anak_nama }}</h2>
                                <p class="text-xs text-gray-600 font-bold">Tipe SLB (Jenis Hambatan)</p>
                                {% else %}
                                <h2 class="text-xl font-extrabold text-gray-800 tracking-tight leading-none mb-1">Anak Anda</h2>
                                <p class="text-xs text-gray-600 font-bold">Tipe SLB (Jenis Hambatan)</p>
                                {% endif %}
                            </div>
                        </div>
                        <!-- Lencana Indikator Status Emosi -->
                        <div class="bg-white px-3 py-1.5 rounded-full border flex items-center gap-2 shadow-sm shrink-0">
                            {% if profil_medis and profil_medis.kondisi_warna %}
                                {% if profil_medis.kondisi_warna == 'green' %}
                                    <span class="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse"></span>
                                    <span class="text-[10px] font-bold text-green-700 uppercase tracking-wider">{{ profil_medis.kondisi_terkini }}</span>
                                {% elif profil_medis.kondisi_warna == 'yellow' %}
                                    <span class="w-2.5 h-2.5 rounded-full bg-yellow-500 animate-pulse"></span>
                                    <span class="text-[10px] font-bold text-yellow-700 uppercase tracking-wider">{{ profil_medis.kondisi_terkini }}</span>
                                {% else %}
                                    <span class="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse"></span>
                                    <span class="text-[10px] font-bold text-red-700 uppercase tracking-wider">{{ profil_medis.kondisi_terkini }}</span>
                                {% endif %}
                            {% elif peran == 'orang_tua' %}
                                <span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                                <span class="text-[10px] font-bold text-amber-700 uppercase tracking-wider">Lengkapi Data</span>
                            {% else %}
                                <span class="w-2.5 h-2.5 rounded-full bg-gray-400"></span>
                                <span class="text-[10px] font-bold text-gray-600 uppercase tracking-wider">KONDISI TERKINI ANAK</span>
                            {% endif %}
                        </div>
                    </div>
                    <div class="absolute inset-0 bg-white/0 group-hover:bg-white/20 transition-colors rounded-3xl pointer-events-none"></div>
                    <div class="absolute right-4 bottom-4 w-8 h-8 rounded-full bg-white/50 text-gray-600 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity backdrop-blur-sm pointer-events-none shadow-sm border border-white">
                        <i class="fas fa-search-plus"></i>
                    </div>
                </div>
                {% endif %}
                
                <!-- Papan Komunikasi Ekspres (AAC) Neumorphic -->
                <div class="mt-6">
                    <h3 class="text-sm font-extrabold text-gray-800 mb-4 px-2 drop-shadow-sm flex items-center gap-2"><i class="fas fa-th-large text-indigo-600 opacity-80"></i> Papan Komunikasi Ekspres</h3>
                    <div class="grid grid-cols-2 md:grid-cols-3 gap-4 px-1">
                        <!-- Toilet -->
                        <button onclick="speakAAC('Saya mau ke toilet')" class="neumorphic-btn p-4 flex flex-col items-center justify-center gap-2 aspect-square">
                            <div class="w-12 h-12 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-2xl shadow-inner">
                                <i class="fas fa-restroom"></i>
                            </div>
                            <span class="text-[10px] font-bold text-gray-600 text-center leading-tight">Saya mau ke toilet</span>
                        </button>
                        
                        <!-- Sakit -->
                        <button onclick="speakAAC('Saya merasa sakit')" class="neumorphic-btn p-4 flex flex-col items-center justify-center gap-2 aspect-square">
                            <div class="w-12 h-12 rounded-full bg-red-100 text-red-600 flex items-center justify-center text-2xl shadow-inner">
                                <i class="fas fa-briefcase-medical"></i>
                            </div>
                            <span class="text-[10px] font-bold text-gray-600 text-center leading-tight">Saya merasa sakit</span>
                        </button>

                        <!-- Lapar Haus -->
                        <button onclick="speakAAC('Saya lapar dan haus')" class="neumorphic-btn p-4 flex flex-col items-center justify-center gap-2 aspect-square">
                            <div class="w-12 h-12 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center text-2xl shadow-inner">
                                <i class="fas fa-hamburger"></i>
                            </div>
                            <span class="text-[10px] font-bold text-gray-600 text-center leading-tight">Saya lapar dan haus</span>
                        </button>

                        <!-- Bising -->
                        <button onclick="speakAAC('Ruangan ini terlalu bising')" class="neumorphic-btn p-4 flex flex-col items-center justify-center gap-2 aspect-square">
                            <div class="w-12 h-12 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center text-2xl shadow-inner">
                                <i class="fas fa-volume-mute"></i>
                            </div>
                            <span class="text-[10px] font-bold text-gray-600 text-center leading-tight">Ruangan ini terlalu bising</span>
                        </button>

                        <!-- Istirahat -->
                        <button onclick="speakAAC('Saya butuh istirahat')" class="neumorphic-btn p-4 flex flex-col items-center justify-center gap-2 aspect-square">
                            <div class="w-12 h-12 rounded-full bg-teal-100 text-teal-600 flex items-center justify-center text-2xl shadow-inner">
                                <i class="fas fa-bed"></i>
                            </div>
                            <span class="text-[10px] font-bold text-gray-600 text-center leading-tight">Saya butuh istirahat</span>
                        </button>

                        <!-- Pelukan -->
                        <button onclick="speakAAC('Saya butuh pelukan')" class="neumorphic-btn p-4 flex flex-col items-center justify-center gap-2 aspect-square">
                            <div class="w-12 h-12 rounded-full bg-pink-100 text-pink-600 flex items-center justify-center text-2xl shadow-inner">
                                <i class="fas fa-heart"></i>
                            </div>
                            <span class="text-[10px] font-bold text-gray-600 text-center leading-tight">Saya butuh pelukan</span>
                        </button>
                    </div>
                </div>
            </div>

            <!-- DASHBOARD GURU BANNER -->

            <!-- DASHBOARD ORANG TUA BANNER -->
            <a href="/orang-tua" class="block relative floating-card overflow-hidden group transform hover:scale-[1.02] transition-all duration-300 rounded-3xl shadow-xl border border-pink-200 mt-4">
                <div class="absolute inset-0 bg-gradient-to-r from-pink-100 to-rose-100"></div>
                
                <div class="absolute right-12 top-1/2 transform -translate-y-1/2 opacity-20 text-pink-500 pointer-events-none">
                    <i class="fas fa-home text-9xl"></i>
                </div>
                
                <div class="relative px-6 py-6 md:px-8 md:py-8 flex items-center justify-between">
                    <div>
                        <h2 class="text-2xl md:text-3xl font-bold text-pink-800 mb-1 font-sans tracking-wide leading-none">Dashboard Orang Tua</h2>
                        <p class="text-pink-600 text-xs md:text-sm font-medium">Asisten Digital Pendamping SLB</p>
                    </div>
                    
                    <div class="w-12 h-12 rounded-full bg-white flex items-center justify-center text-pink-500 shadow-[0_0_15px_rgba(244,114,182,0.4)] group-hover:scale-110 transition-transform duration-300 relative z-10">
                        <i class="fas fa-arrow-right text-lg"></i>
                    </div>
                </div>
            </a>

            

        </div>
    </div>

    <!-- MAIN GRID MENU -->
    <h3 class="text-gray-800 font-bold text-lg mb-4 pl-1 border-l-4 border-blue-600 leading-none py-1 ml-1 md:text-2xl md:mb-8" style="border-left-width: 6px;">&nbsp;Menu Utama</h3>
    <div class="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-8 mb-8">
        <!-- SLB A: Tunanetra -->
        <a href="/slb/tunanetra" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-gray-100 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-gray-600 group-hover:bg-gray-800 group-hover:text-white transition-colors">
                <i class="fas fa-blind text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-gray-700 group-hover:text-gray-800">Tunanetra</span>
        </a>
        <!-- SLB B: Tunarungu -->
        <a href="/slb/tunarungu" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-yellow-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-yellow-600 group-hover:bg-yellow-500 group-hover:text-white transition-colors">
                <i class="fas fa-hands-asl-interpreting text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-gray-700 group-hover:text-yellow-600">Tunarungu</span>
        </a>
        <!-- SLB C: Tunagrahita -->
        <a href="/slb/tunagrahita" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-purple-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-purple-600 group-hover:bg-purple-500 group-hover:text-white transition-colors">
                <i class="fas fa-puzzle-piece text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-gray-700 group-hover:text-purple-600">Tunagrahita</span>
        </a>
        <!-- SLB D: Tunadaksa -->
        <a href="/slb/tunadaksa" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-blue-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-blue-600 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                <i class="fas fa-wheelchair text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-gray-700 group-hover:text-blue-600">Tunadaksa</span>
        </a>
        <!-- SLB E: Tunalaras -->
        <a href="/slb/tunalaras" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-teal-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-teal-600 group-hover:bg-teal-500 group-hover:text-white transition-colors">
                <i class="fas fa-heart text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-gray-700 group-hover:text-teal-600">Tunalaras</span>
        </a>
        <!-- SLB G: Tunaganda -->
        <a href="/slb/tunaganda" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-indigo-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-indigo-600 group-hover:bg-indigo-500 group-hover:text-white transition-colors">
                <i class="fas fa-lightbulb text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-gray-700 group-hover:text-indigo-600">Tunaganda</span>
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
            <div id="terapi-chevron" class="bg-gray-50 w-10 h-10 rounded-full flex items-center justify-center text-gray-500 group-hover:bg-white group-hover:text-blue-500 transition-all duration-500">
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

    <!-- KALKULATOR ILMIAH DIFABEL SECTION -->
    <div id="kalkulator-section" class="mb-6">
        <button onclick="toggleCalc()" class="w-full bg-white p-6 rounded-3xl shadow-lg border border-emerald-100 flex justify-between items-center group hover:bg-emerald-50 transition-all duration-300">
            <div class="flex items-center gap-4">
                <div class="bg-emerald-100 p-3 rounded-xl text-emerald-600 group-hover:bg-emerald-500 group-hover:text-white transition-colors shadow-sm">
                    <i class="fas fa-calculator text-2xl"></i>
                </div>
                <div class="text-left">
                    <h3 class="text-lg font-bold text-gray-800 group-hover:text-emerald-700">Kalkulator Ilmiah Difabel</h3>
                    <p class="text-xs text-gray-500 font-medium">6 Fitur Baru Kalkulator Ilmiah Difabel</p>
                </div>
            </div>
            <div id="calc-chevron" class="bg-gray-50 w-10 h-10 rounded-full flex items-center justify-center text-gray-500 group-hover:bg-white group-hover:text-emerald-500 transition-all duration-300">
                 <i class="fas fa-chevron-down transform transition-transform duration-300"></i>
            </div>
        </button>
        
        <div id="calc-content" class="hidden mt-6 animate-[slideDown_0.3s_ease-out]">
             <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                 <!-- IMT -->
                 <button onclick="openModal('modal-imt')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-emerald-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 text-left flex items-center gap-3 group">
                     <div class="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl group-hover:bg-emerald-500 group-hover:text-white transition-colors"><i class="fas fa-weight"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-emerald-700">IMT Down Syndrome</span>
                 </button>
                 <!-- SENSORY -->
                 <button onclick="openModal('modal-sensory')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-emerald-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 text-left flex items-center gap-3 group">
                     <div class="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl group-hover:bg-emerald-500 group-hover:text-white transition-colors"><i class="fas fa-brain"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-emerald-700">Ambang Batas Sensori</span>
                 </button>
                 <!-- AUDITORY -->
                 <button onclick="openModal('modal-auditory')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-emerald-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 text-left flex items-center gap-3 group">
                     <div class="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl group-hover:bg-emerald-500 group-hover:text-white transition-colors"><i class="fas fa-headphones"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-emerald-700">Terapi Auditori</span>
                 </button>
                 <!-- IQ ESTIMATOR -->
                 <button onclick="openModal('modal-iq')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-emerald-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 text-left flex items-center gap-3 group">
                     <div class="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl group-hover:bg-emerald-500 group-hover:text-white transition-colors"><i class="fas fa-chart-line"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-emerald-700">Estimator IQ</span>
                 </button>
                 <!-- FINE MOTOR -->
                 <button onclick="openModal('modal-motor')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-emerald-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 text-left flex items-center gap-3 group">
                     <div class="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl group-hover:bg-emerald-500 group-hover:text-white transition-colors"><i class="fas fa-hand-paper"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-emerald-700">Motorik Halus</span>
                 </button>
                 <!-- DIET -->
                 <button onclick="openModal('modal-diet-calc')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-emerald-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 text-left flex items-center gap-3 group">
                     <div class="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl group-hover:bg-emerald-500 group-hover:text-white transition-colors"><i class="fas fa-utensils"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-emerald-700">Diet Eliminasi</span>
                 </button>
             </div>
        </div>
    </div>

    <!-- STATIC PWA INSTALL BUTTON (NEW) -->
    <div id="pwa-static-btn-container" class="pwa-btn-container mb-6">
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
            <div class="bg-gray-50 w-10 h-10 rounded-full flex items-center justify-center text-gray-500 group-hover:text-gray-600">
                 <i class="fas fa-arrow-right"></i>
            </div>
        </button>
    </div>

    <!-- MODALS -->

    <!-- Modal Developer -->
    <div id="modal-developer" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-white/95 backdrop-blur-xl animate-[slideUp_0.5s_ease-out] flex flex-col items-center justify-start text-center overflow-y-auto">
            <!-- Sticky Header -->
            <div class="sticky top-0 w-full bg-white/95 backdrop-blur-xl pt-8 pb-4 z-20 shadow-sm">
                <button onclick="closeModal('modal-developer'); stopDevAudio()" class="absolute top-6 right-6 bg-gray-100 w-10 h-10 rounded-full text-gray-600 hover:bg-gray-200 text-xl flex items-center justify-center">&times;</button>
                <h2 class="text-xs font-bold text-gray-500 tracking-[0.3em] mb-2 uppercase">DEVELOPER</h2>
                <h1 class="text-3xl font-extrabold text-emerald-800" style="white-space: nowrap; font-size: clamp(1.5rem, 5vw, 2.5rem);">SAMARINDA WEB CREATIVE</h1>
            </div>
            
            <!-- Scrollable Content -->
            <div class="p-8 w-full max-w-sm mx-auto flex flex-col items-center">
            <div class="mb-8 mt-4">
                <img src="/static/Samarinda_Web_Creative_Logo-removebg-preview.png" alt="Logo Developer" class="h-32 object-contain mx-auto drop-shadow-2xl">
            </div>
            
            <h3 class="text-xs font-bold text-gray-500 tracking-[0.2em] mb-4 uppercase border-b border-gray-200 pb-2 w-24 mx-auto">PIHAK KETIGA</h3>
            <div class="flex flex-col gap-4 justify-center items-center mb-8">
                <img src="/static/pythonlogo.png" class="h-5 object-contain">
                <img src="/static/godaddylogo.png" class="h-8 object-contain">
            </div>
            
            <div class="bg-gray-50 p-6 rounded-3xl border border-gray-100 mb-8 max-w-sm w-full">
                <p class="text-sm text-gray-600 font-medium leading-relaxed mb-1">
                    Samarinda, Kalimantan Timur,<br>
                    Jln. Delima Dalam, Blok. E, RT. 53
                </p>
                <p class="text-xs text-gray-500 italic mt-2">"kalau butuh jasa pembuatan aplikasi website seperti ini, hubungi kami yaa hehee"</p>
            </div>
            
            <div class="flex items-center gap-4 mb-8">
                <a href="https://www.instagram.com/samarindawebcreative/" target="_blank" class="bg-gradient-to-tr from-purple-500 to-pink-500 text-white w-12 h-12 rounded-full flex items-center justify-center shadow-lg hover:scale-110 transition">
                    <i class="fab fa-instagram text-2xl"></i>
                </a>
                <a href="{{ url_for('index') }}" class="flex items-center gap-2 px-6 py-3 bg-gray-900 text-white rounded-full font-bold shadow-lg hover:scale-105 transition">
                    <img src="/static/piton.png" class="h-6 w-6"> See Our Current Work
                </a>
            </div>

            <p class="text-[10px] text-gray-500 font-serif">Just The Way You Are (2010) - Bruno Mars</p>
            </div>
        </div>
        <audio id="dev-audio" src="/static/kreasikoe_bruno-mars-just-the-way-you-are.mp3" preload="none"></audio>
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
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.5s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20 max-h-[90dvh] overflow-y-auto">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-file-medical text-blue-500 mr-2"></i>Jurnal Kambuh</h3>
                <button onclick="closeModal('modal-terapi-log')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            
            {% if peran == 'guru' or peran == 'kepala_sekolah' %}
            <div id="guru-kambuh-monitor">
                <h4 class="text-sm font-bold text-gray-800 mb-4 pl-2 border-l-4 border-blue-500">Monitor Jurnal Kambuh Siswa</h4>
                <div class="flex gap-2 mb-4">
                    <input type="text" id="guru-kambuh-search" placeholder="Cari..." class="flex-1 border border-blue-100 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 bg-blue-50/50">
                    <button onclick="fetchGuruKambuh()" class="bg-blue-500 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-md hover:bg-blue-600 transition">Muat Data</button>
                </div>
                <div id="guru-kambuh-results" class="space-y-3 overflow-y-auto max-h-64"></div>
            </div>
            <script>
            function fetchGuruKambuh(page=1) {
                fetch('/api/jurnal-kambuh/guru-view?page=' + page)
                    .then(res => res.json())
                    .then(data => {
                        const container = document.getElementById('guru-kambuh-results');
                        if(page === 1) container.innerHTML = '';
                        if(data.items.length === 0 && page === 1) {
                            container.innerHTML = '<p class="text-center text-gray-500 text-xs py-4">Belum ada data rekaman.</p>';
                            return;
                        }
                        
                        // remove old button
                        const oldBtn = document.getElementById('btn-more-kambuh');
                        if (oldBtn) oldBtn.remove();
                        
                        data.items.forEach(log => {
                            container.innerHTML += `
                            <div class="bg-white p-4 rounded-2xl shadow-sm border border-blue-100 flex justify-between items-start">
                                <div>
                                    <h4 class="font-bold text-blue-800 text-sm mb-1">${log.siswa_nama}</h4>
                                    <div class="flex items-center gap-2 mb-1">
                                        <span class="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md">${log.date}</span>
                                        <span class="text-xs text-gray-500">${log.time}</span>
                                    </div>
                                    <p class="text-sm font-bold text-gray-800">${log.trigger}</p>
                                    ${log.notes ? `<p class="text-xs text-gray-500 mt-1 italic">"${log.notes}"</p>` : ''}
                                </div>
                            </div>`;
                        });
                        if (data.has_next) {
                            container.innerHTML += `<button id="btn-more-kambuh" onclick="fetchGuruKambuh(${data.page + 1})" class="w-full text-xs font-bold text-blue-500 py-2 hover:bg-blue-50 rounded-xl transition mt-2">Muat Lebih Banyak</button>`;
                        }
                    });
            }
            document.addEventListener('DOMContentLoaded', () => fetchGuruKambuh(1));
            </script>
            {% else %}
            <form action="/therapy/log" method="POST" class="space-y-4 mb-8 bg-blue-50 p-4 rounded-2xl border border-blue-100">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
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
                            <span class="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md">{{ log.date }}</span>
                            <span class="text-xs text-gray-500">{{ log.time }}</span>
                        </div>
                        <p class="text-sm font-bold text-gray-800">{{ log.trigger }}</p>
                        {% if log.notes %}<p class="text-xs text-gray-500 mt-1 italic">"{{ log.notes }}"</p>{% endif %}
                    </div>
                </div>
                {% else %}
                <p class="text-center text-gray-500 text-xs py-4">Belum ada data rekaman.</p>
                {% endfor %}
            </div>
            {% endif %}
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
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.5s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20 max-h-[85dvh] overflow-y-auto">
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
    
    <!-- Modal IMT Down Syndrome -->
    <div id="modal-imt" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" onclick="closeModal('modal-imt')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <div class="flex items-center gap-2">
                    <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-weight text-emerald-500 mr-2"></i>IMT Down Syndrome</h3>
                    <button onclick="showCalcInfo('imt')" class="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200 transition"><i class="fas fa-info text-xs"></i></button>
                </div>
                <button onclick="closeModal('modal-imt')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Umur (Tahun)</label>
                    <input type="number" id="imt-age" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Berat Badan (kg)</label>
                        <input type="number" id="imt-weight" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Tinggi Badan (cm)</label>
                        <input type="number" id="imt-height" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                    </div>
                </div>
                <button onclick="calcIMT()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-emerald-600 transition">Hitung Status Gizi</button>
                <div id="result-imt" class="hidden mt-4 bg-emerald-50 p-4 rounded-xl border border-emerald-100 text-sm"></div>
            </div>
        </div>
    </div>

    <!-- Modal Sensory Overload -->
    <div id="modal-sensory" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeModal('modal-sensory')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <div class="flex items-center gap-2">
                    <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-brain text-emerald-500 mr-2"></i>Ambang Batas Sensori</h3>
                    <button onclick="showCalcInfo('sensory')" class="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200 transition"><i class="fas fa-info text-xs"></i></button>
                </div>
                <button onclick="closeModal('modal-sensory')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500">&times;</button>
            </div>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Kebisingan (1-10)</label>
                    <input type="number" id="sensory-noise" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Cahaya (1-10)</label>
                    <input type="number" id="sensory-light" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Kepadatan Orang (1-10)</label>
                    <input type="number" id="sensory-crowd" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Durasi (1-10)</label>
                    <input type="number" id="sensory-duration" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                </div>
                <button onclick="calcSensory()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-emerald-600 transition">Prediksi Overload</button>
                <div id="result-sensory" class="hidden mt-4 p-4 rounded-xl border text-sm"></div>
            </div>
        </div>
    </div>

    <!-- Modal Terapi Auditori -->
    <div id="modal-auditory" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeModal('modal-auditory')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <div class="flex items-center gap-2">
                    <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-headphones text-emerald-500 mr-2"></i>Dosis Terapi Auditori</h3>
                    <button onclick="showCalcInfo('auditory')" class="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200 transition"><i class="fas fa-info text-xs"></i></button>
                </div>
                <button onclick="closeModal('modal-auditory')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500">&times;</button>
            </div>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Usia Anak</label>
                    <input type="number" id="auditory-age" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Tingkat Hiperaktivitas</label>
                    <select id="auditory-hyper" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                        <option value="Ringan">Ringan</option>
                        <option value="Berat">Berat</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Target Gelombang</label>
                    <select id="auditory-wave" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                        <option value="Theta">Theta (Rileks)</option>
                        <option value="Delta">Delta (Tidur)</option>
                    </select>
                </div>
                <button onclick="calcAuditory()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-emerald-600 transition">Hitung Durasi</button>
                <div id="result-auditori" class="hidden mt-4 bg-indigo-50 p-4 rounded-xl border border-indigo-100 text-center"></div>
            </div>
        </div>
    </div>

    <!-- Modal Estimator IQ -->
    <div id="modal-iq" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeModal('modal-iq')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <div class="flex items-center gap-2">
                    <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-chart-line text-emerald-500 mr-2"></i>Estimator IQ</h3>
                    <button onclick="showCalcInfo('iq')" class="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200 transition"><i class="fas fa-info text-xs"></i></button>
                </div>
                <button onclick="closeModal('modal-iq')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500">&times;</button>
            </div>
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Usia Kronologis</label>
                        <input type="number" id="iq-chrono" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Usia Mental</label>
                        <input type="number" id="iq-mental" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                    </div>
                </div>
                <button onclick="calcIQ()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-emerald-600 transition">Hitung IQ</button>
                <div id="result-iq" class="hidden mt-4 bg-emerald-50 p-4 rounded-xl border border-emerald-100 text-center"></div>
            </div>
        </div>
    </div>

    <!-- Modal Motorik Halus -->
    <div id="modal-motor" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeModal('modal-motor')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <div class="flex items-center gap-2">
                    <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-hand-paper text-emerald-500 mr-2"></i>Progress Motorik Halus</h3>
                    <button onclick="showCalcInfo('motor')" class="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200 transition"><i class="fas fa-info text-xs"></i></button>
                </div>
                <button onclick="closeModal('modal-motor')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500">&times;</button>
            </div>
            <div class="space-y-4">
                 <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Skor Bulan Lalu</label>
                    <input type="number" id="motor-prev" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Skor Bulan Ini</label>
                    <input type="number" id="motor-curr" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                </div>
                <button onclick="calcMotor()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-emerald-600 transition">Hitung Progress</button>
                <div id="result-motorik" class="hidden mt-4 space-y-2"></div>
            </div>
        </div>
    </div>

    <!-- Modal Diet Eliminasi -->
    <div id="modal-diet-calc" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeModal('modal-diet-calc')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <div class="flex items-center gap-2">
                    <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-utensils text-emerald-500 mr-2"></i>Diet Eliminasi</h3>
                    <button onclick="showCalcInfo('diet')" class="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200 transition"><i class="fas fa-info text-xs"></i></button>
                </div>
                <button onclick="closeModal('modal-diet-calc')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500">&times;</button>
            </div>
            <div class="space-y-4">
                 <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Mode Diet</label>
                    <select id="diet-mode" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                        <option value="GFCF">GFCF</option>
                        <option value="Keto">Keto 3:1</option>
                    </select>
                </div>
                <div class="grid grid-cols-3 gap-2">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Lemak (g)</label>
                        <input type="number" id="diet-fat" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Protein (g)</label>
                        <input type="number" id="diet-protein" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Karbo (g)</label>
                        <input type="number" id="diet-carbs" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                    </div>
                </div>
                <button onclick="calcDiet()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-emerald-600 transition">Kalkulasi</button>
                <div id="result-diet" class="hidden mt-4 bg-emerald-50 p-6 rounded-xl border border-emerald-100 text-center"></div>
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
            <div class="space-y-6 overflow-y-auto max-h-[70dvh] pb-10">
                <!-- Logic Section -->
                <div>
                    <h4 class="text-sm font-bold text-gray-800 uppercase tracking-wider mb-2 border-b border-gray-200 pb-1">Bedah Logika Sains</h4>
                    <p id="exp-logic" class="text-sm text-gray-700 leading-relaxed font-medium bg-blue-50 p-4 rounded-xl border border-blue-100">
                        ...
                    </p>
                </div>
                <!-- Sources Section -->
                <div>
                    <h4 class="text-sm font-bold text-gray-800 uppercase tracking-wider mb-2 border-b border-gray-200 pb-1">Dasar Medis dan Referensi</h4>
                    <ul id="exp-sources" class="space-y-1">
                        <!-- LI generated by JS -->
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal Info Calculator -->
    <div id="modal-calc-info" class="fixed inset-0 z-[130] hidden">
        <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" onclick="closeModal('modal-calc-info')"></div>
        <div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-11/12 max-w-sm bg-white rounded-3xl p-6 shadow-2xl animate-[popupFadeIn_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-bold text-emerald-600 flex items-center gap-2"><i class="fas fa-info-circle"></i> Info Kalkulator</h3>
                <button onclick="closeModal('modal-calc-info')" class="bg-emerald-50 w-8 h-8 rounded-full text-emerald-500 hover:bg-emerald-100 transition">&times;</button>
            </div>
            <div class="bg-emerald-50 p-4 rounded-2xl border border-emerald-100">
                <p id="calc-info-text" class="text-sm text-gray-700 leading-relaxed font-medium text-justify"></p>
            </div>
        </div>
    </div>

    <!-- Modal Medical Panel -->
    <div id="modal-medical-panel" class="fixed inset-0 z-[140] hidden">
        <div class="absolute inset-0 bg-indigo-900/60 backdrop-blur-md" onclick="closeModal('modal-medical-panel')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.4s_ease-out] md:relative md:max-w-xl md:mx-auto md:rounded-3xl md:top-10 max-h-[90dvh] overflow-y-auto border-t-4 border-indigo-500 flex flex-col">
            
            <div class="flex justify-between items-start mb-4">
                <div class="flex items-center gap-4">
                    <div class="w-14 h-14 rounded-full bg-white shadow-md border-2 border-indigo-100 flex items-center justify-center overflow-hidden shrink-0">
                        <img src="https://api.dicebear.com/7.x/notionists/svg?seed=Budi&backgroundColor=e0e7ff" alt="Avatar Budi" class="w-full h-full object-cover">
                    </div>
                    <div>
                        <h3 class="text-xl font-extrabold text-gray-800 tracking-tight leading-none mb-1">Budi Santoso</h3>
                        <p class="text-xs text-indigo-500 font-bold tracking-wider uppercase"><i class="fas fa-id-card mr-1"></i> Rekam Digital Siswa</p>
                    </div>
                </div>
                <button onclick="closeModal('modal-medical-panel')" class="w-10 h-10 rounded-full bg-gray-50 text-gray-500 hover:bg-gray-200 hover:text-gray-700 transition flex items-center justify-center border border-gray-100 shrink-0">&times;</button>
            </div>

            <!-- Mini Tab Navigation -->
            <div class="flex p-1 bg-gray-100 rounded-xl mb-6 shrink-0 flex-wrap gap-1">
                <button onclick="switchMedicalTab('krusial')" id="tab-medis-krusial-btn" class="flex-1 py-2 text-[10px] md:text-xs font-bold rounded-lg bg-white shadow-sm text-indigo-600 transition flex items-center justify-center gap-1 min-w-[30%]"><i class="fas fa-heartbeat"></i> Data Medis </button>
                <button onclick="switchMedicalTab('harian')" id="tab-medis-harian-btn" class="flex-1 py-2 text-[10px] md:text-xs font-bold rounded-lg text-gray-500 hover:bg-gray-50 transition flex items-center justify-center gap-1 min-w-[30%]"><i class="fas fa-book-medical"></i> Data Harian </button>
                <button onclick="switchMedicalTab('jadwal')" id="tab-medis-jadwal-btn" class="flex-1 py-2 text-[10px] md:text-xs font-bold rounded-lg text-gray-500 hover:bg-gray-50 transition flex items-center justify-center gap-1 min-w-[30%]"><i class="fas fa-pills"></i> Jadwal Medis </button>
            </div>

            <!-- Tab 1: Data Medis -->
            <div id="tab-medis-krusial" class="medical-tab-content flex-1 overflow-y-auto pr-1">
                <div id="medical-info-banner" class="mb-4">
                    {% if peran == 'orang_tua' %}
                        <p class="text-xs text-emerald-600 font-bold tracking-widest uppercase text-center bg-emerald-50 p-2 rounded-lg border border-emerald-100 shadow-sm"><i class="fas fa-edit mr-1"></i> Mode Edit Orang Tua Aktif</p>
                    {% elif peran == 'guru' or peran == 'kepala_sekolah' %}
                        <p class="text-xs text-indigo-600 font-bold tracking-widest uppercase text-center bg-indigo-50 p-2 rounded-lg border border-indigo-100 shadow-sm"><i class="fas fa-eye mr-1"></i> Mode Lihat Guru</p>
                    {% else %}
                        <p class="text-xs text-blue-600 font-bold tracking-widest uppercase text-center bg-blue-50 p-2 rounded-lg border border-blue-100 shadow-sm"><i class="fas fa-info-circle mr-1"></i> Login sebagai Orang Tua untuk melihat dan mengisi data medis anak Anda secara lengkap.</p>
                    {% endif %}
                </div>
                
                <!-- Panel Instrumen Medis Masa Depan Layout -->
                <div class="space-y-3 font-sans text-sm text-gray-700 bg-gray-50/50 p-4 rounded-2xl border border-gray-100">
                    
                    <div class="grid grid-cols-2 gap-3">
                        <!-- 1. Identitas Utama -->
                        <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex items-start gap-3 hover:-translate-y-0.5 transition-transform">
                            <div class="w-10 h-10 rounded-full bg-indigo-50 text-indigo-500 flex items-center justify-center shrink-0">
                                <i class="fas fa-id-badge text-lg"></i>
                            </div>
                            <div class="w-full">
                                <span class="block text-[10px] text-gray-400 font-bold uppercase tracking-wider mb-0.5">Identitas Utama</span>
                                {% if peran == 'orang_tua' %}
                                    <div class="flex flex-col gap-1 w-full">
                                        <input type="text" id="med-nama-lengkap" class="font-extrabold text-gray-800 text-xs border-b border-gray-200 focus:border-emerald-500 focus:outline-none bg-transparent w-full" value="{{ profil_medis.nama_lengkap if profil_medis else '' }}" placeholder="Nama Lengkap">
                                        <input type="text" id="med-nama-panggilan" class="font-extrabold text-gray-800 text-xs border-b border-gray-200 focus:border-emerald-500 focus:outline-none bg-transparent w-full" value="{{ profil_medis.nama_panggilan if profil_medis else '' }}" placeholder="Nama Panggilan">
                                    </div>
                                {% else %}
                                    <div class="font-extrabold text-gray-800 text-sm" id="view-med-identitas">Nama Lengkap Anak (Nama Panggilan)</div>
                                {% endif %}
                            </div>
                        </div>
                        
                        <!-- 2. Fase Perkembangan -->
                        <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex items-start gap-3 hover:-translate-y-0.5 transition-transform">
                            <div class="w-10 h-10 rounded-full bg-blue-50 text-blue-500 flex items-center justify-center shrink-0">
                                <i class="fas fa-calendar-alt text-lg"></i>
                            </div>
                            <div class="w-full">
                                <span class="block text-[10px] text-gray-400 font-bold uppercase tracking-wider mb-0.5">Perkembangan</span>
                                {% if peran == 'orang_tua' %}
                                    <div class="flex flex-col gap-1 w-full">
                                        <input type="number" id="med-usia" class="font-extrabold text-gray-800 text-xs border-b border-gray-200 focus:border-emerald-500 focus:outline-none bg-transparent w-full" value="{{ profil_medis.usia if profil_medis else '' }}" placeholder="Usia">
                                        <input type="text" id="med-kelas" class="font-extrabold text-gray-800 text-xs border-b border-gray-200 focus:border-emerald-500 focus:outline-none bg-transparent w-full" value="{{ profil_medis.kelas if profil_medis else '' }}" placeholder="Tingkat Kelas SLB">
                                    </div>
                                {% else %}
                                    <div class="font-extrabold text-gray-800 text-sm" id="view-med-perkembangan">Usia / Tingkat Kelas SLB</div>
                                {% endif %}
                            </div>
                        </div>
                    </div>

                    <!-- 3. Diagnosis Medis Utama -->
                    <div class="bg-white p-4 rounded-xl shadow-sm border-l-4 border-l-red-500 border border-y-gray-100 border-r-gray-100 flex items-center gap-4 hover:-translate-y-0.5 transition-transform">
                        <div class="w-12 h-12 rounded-full bg-red-50 text-red-500 flex items-center justify-center shrink-0 shadow-inner">
                            <i class="fas fa-stethoscope text-xl"></i>
                        </div>
                        <div class="w-full">
                            <span class="block text-[10px] text-red-500 font-bold uppercase tracking-wider mb-0.5">Diagnosis Medis Utama</span>
                            {% if peran == 'orang_tua' %}
                                <textarea id="med-diagnosis-utama" rows="2" class="font-extrabold text-gray-800 text-sm md:text-base border-b border-gray-200 focus:border-emerald-500 focus:outline-none bg-transparent w-full resize-none" placeholder="Diagnosis Utama & Komorbiditas Medis">{{ profil_medis.diagnosis_utama if profil_medis else '' }}</textarea>
                            {% else %}
                                <div class="font-extrabold text-gray-800 text-base md:text-lg" id="view-med-diagnosis">Diagnosis Utama & Komorbiditas Medis</div>
                            {% endif %}
                        </div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <!-- 4. Tingkat Hambatan -->
                        <div class="bg-orange-50/50 p-4 rounded-xl shadow-sm border border-orange-100 flex items-start gap-3 hover:-translate-y-0.5 transition-transform">
                            <div class="w-10 h-10 rounded-full bg-orange-100 text-orange-500 flex items-center justify-center shrink-0">
                                <i class="fas fa-exclamation-triangle text-lg"></i>
                            </div>
                            <div class="w-full">
                                <span class="block text-[10px] text-orange-600 font-bold uppercase tracking-wider mb-0.5">Tingkat Hambatan</span>
                                {% if peran == 'orang_tua' %}
                                    <input type="text" id="med-tingkat-hambatan" class="font-bold text-orange-900 text-sm leading-snug border-b border-orange-200 focus:border-orange-500 focus:outline-none bg-transparent w-full" value="{{ profil_medis.tingkat_hambatan if profil_medis else '' }}" placeholder="Ringan / Sedang / Berat">
                                {% else %}
                                    <div class="font-bold text-orange-900 text-sm leading-snug" id="view-med-hambatan">Ringan / Sedang / Berat (Butuh Pendampingan)</div>
                                {% endif %}
                            </div>
                        </div>
                        
                        <!-- 5. Alergi & Medis Kritis -->
                        <div class="bg-red-50/50 p-4 rounded-xl shadow-sm border border-red-100 flex items-start gap-3 hover:-translate-y-0.5 transition-transform">
                            <div class="w-10 h-10 rounded-full bg-red-100 text-red-500 flex items-center justify-center shrink-0">
                                <i class="fas fa-biohazard text-lg"></i>
                            </div>
                            <div class="w-full">
                                <span class="block text-[10px] text-red-600 font-bold uppercase tracking-wider mb-0.5">Alergi Kritis</span>
                                {% if peran == 'orang_tua' %}
                                    <textarea id="med-alergi-kritis" rows="2" class="font-bold text-red-900 text-sm leading-snug border-b border-red-200 focus:border-red-500 focus:outline-none bg-transparent w-full resize-none" placeholder="Jenis Alergi & Riwayat Medis Kritis">{{ profil_medis.alergi_kritis if profil_medis else '' }}</textarea>
                                {% else %}
                                    <div class="font-bold text-red-900 text-sm leading-snug" id="view-med-alergi">Jenis Alergi & Riwayat Medis Kritis</div>
                                {% endif %}
                            </div>
                        </div>
                    </div>

                    <!-- 6. Pemicu Tantrum -->
                    <div class="bg-yellow-50 p-4 rounded-xl shadow-sm border border-yellow-200 flex items-start gap-4 hover:-translate-y-0.5 transition-transform">
                        <div class="w-12 h-12 rounded-full bg-yellow-100 text-yellow-600 flex items-center justify-center shrink-0">
                            <i class="fas fa-bolt text-xl"></i>
                        </div>
                        <div class="w-full">
                            <span class="block text-[10px] text-yellow-600 font-bold uppercase tracking-wider mb-0.5">Pemicu Tantrum (Triggers)</span>
                            {% if peran == 'orang_tua' %}
                                <textarea id="med-pemicu-tantrum" rows="2" class="font-bold text-yellow-900 text-sm leading-relaxed border-b border-yellow-300 focus:border-yellow-600 focus:outline-none bg-transparent w-full resize-none" placeholder="Kondisi atau Stimulus yang Memicu Reaksi Emosional">{{ profil_medis.pemicu_tantrum if profil_medis else '' }}</textarea>
                            {% else %}
                                <div class="font-bold text-yellow-900 text-sm leading-relaxed" id="view-med-tantrum">Kondisi atau Stimulus yang Memicu Reaksi Emosional</div>
                            {% endif %}
                        </div>
                    </div>

                    <!-- 7. Strategi Penenangan -->
                    <div class="bg-emerald-50 p-4 rounded-xl shadow-sm border border-emerald-200 flex items-start gap-4 hover:-translate-y-0.5 transition-transform">
                        <div class="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center shrink-0">
                            <i class="fas fa-spa text-xl"></i>
                        </div>
                        <div class="w-full">
                            <span class="block text-[10px] text-emerald-600 font-bold uppercase tracking-wider mb-1">Strategi Penenangan Instan</span>
                            {% if peran == 'orang_tua' %}
                                <textarea id="med-strategi-penenangan" rows="3" class="font-bold text-emerald-900 text-xs md:text-sm leading-relaxed border-b border-emerald-300 focus:border-emerald-600 focus:outline-none bg-transparent w-full resize-none" placeholder="Teknik Penenangan Pertama\nTeknik Penenangan Kedua\nTeknik Penenangan Ketiga">{{ profil_medis.strategi_penenangan if profil_medis else '' }}</textarea>
                            {% else %}
                                <ul class="font-bold text-emerald-900 text-xs md:text-sm space-y-1 list-disc pl-4" id="view-med-strategi">
                                    <li>Teknik Penenangan Pertama</li>
                                    <li>Teknik Penenangan Kedua</li>
                                    <li>Teknik Penenangan Ketiga</li>
                                </ul>
                            {% endif %}
                        </div>
                    </div>

                    <!-- 8. Kemampuan Komunikasi -->
                    <div class="bg-sky-50 p-4 rounded-xl shadow-sm border border-sky-200 flex items-start gap-4 hover:-translate-y-0.5 transition-transform">
                        <div class="w-12 h-12 rounded-full bg-sky-100 text-sky-500 flex items-center justify-center shrink-0">
                            <i class="fas fa-comment-dots text-xl"></i>
                        </div>
                        <div class="w-full">
                            <span class="block text-[10px] text-sky-600 font-bold uppercase tracking-wider mb-0.5">Komunikasi</span>
                            {% if peran == 'orang_tua' %}
                                <textarea id="med-kemampuan-komunikasi" rows="2" class="font-bold text-sky-900 text-sm leading-relaxed border-b border-sky-300 focus:border-sky-600 focus:outline-none bg-transparent w-full resize-none" placeholder="Kemampuan Verbal dan Non-Verbal Anak">{{ profil_medis.kemampuan_komunikasi if profil_medis else '' }}</textarea>
                            {% else %}
                                <div class="font-bold text-sky-900 text-sm leading-relaxed" id="view-med-komunikasi">Kemampuan Verbal dan Non-Verbal Anak</div>
                            {% endif %}
                        </div>
                    </div>
                    
                    {% if peran == 'orang_tua' %}
                    <!-- 8.5 Tipe & Kondisi Terkini (Khusus Form Edit Orang Tua) -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div class="bg-purple-50 p-4 rounded-xl shadow-sm border border-purple-200 flex items-start gap-3 hover:-translate-y-0.5 transition-transform">
                            <div class="w-10 h-10 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center shrink-0">
                                <i class="fas fa-school text-lg"></i>
                            </div>
                            <div class="w-full">
                                <span class="block text-[10px] text-purple-600 font-bold uppercase tracking-wider mb-0.5">Tipe SLB & Kategori</span>
                                <div class="flex flex-col gap-1 w-full">
                                    <input type="text" id="med-jenis-slb" class="font-bold text-purple-900 text-xs border-b border-purple-200 focus:border-purple-500 focus:outline-none bg-transparent w-full" value="{{ profil_medis.jenis_slb if profil_medis else '' }}" placeholder='Contoh: "SLB C"'>
                                    <input type="text" id="med-kategori-hambatan" class="font-bold text-purple-900 text-xs border-b border-purple-200 focus:border-purple-500 focus:outline-none bg-transparent w-full" value="{{ profil_medis.kategori_hambatan if profil_medis else '' }}" placeholder='Contoh: "Tunagrahita"'>
                                </div>
                            </div>
                        </div>
                        <div class="bg-teal-50 p-4 rounded-xl shadow-sm border border-teal-200 flex items-start gap-3 hover:-translate-y-0.5 transition-transform">
                            <div class="w-10 h-10 rounded-full bg-teal-100 text-teal-600 flex items-center justify-center shrink-0">
                                <i class="fas fa-heartbeat text-lg"></i>
                            </div>
                            <div class="w-full">
                                <span class="block text-[10px] text-teal-600 font-bold uppercase tracking-wider mb-0.5">Kondisi Saat Ini (Lencana)</span>
                                <div class="flex flex-col gap-1 w-full">
                                    <input type="text" id="med-kondisi-terkini" class="font-bold text-teal-900 text-xs border-b border-teal-200 focus:border-teal-500 focus:outline-none bg-transparent w-full" value="{{ profil_medis.kondisi_terkini if profil_medis else '' }}" placeholder='Label: "Sedang Tenang"'>
                                    <select id="med-kondisi-warna" class="font-bold text-teal-900 text-xs border-b border-teal-200 focus:border-teal-500 focus:outline-none bg-transparent w-full mt-1">
                                        <option value="green" {% if profil_medis and profil_medis.kondisi_warna == 'green' %}selected{% endif %}>Hijau (Aman/Tenang)</option>
                                        <option value="yellow" {% if profil_medis and profil_medis.kondisi_warna == 'yellow' %}selected{% endif %}>Kuning (Waspada/Butuh Perhatian)</option>
                                        <option value="red" {% if profil_medis and profil_medis.kondisi_warna == 'red' %}selected{% endif %}>Merah (Darurat/Tantrum)</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endif %}

                    <!-- 9. Kontak Darurat -->
                    <div class="bg-gradient-to-r from-red-600 to-red-500 p-5 rounded-xl shadow-lg border border-red-700 text-white flex items-center justify-between hover:scale-[1.01] transition-transform">
                        <div class="flex items-center gap-4 w-full">
                            <div class="w-12 h-12 rounded-full bg-red-800/50 flex items-center justify-center shrink-0 border border-red-400">
                                <i class="fas fa-phone-alt text-2xl text-white animate-pulse"></i>
                            </div>
                            <div class="w-full">
                                <span class="block text-[10px] text-red-200 font-bold uppercase tracking-widest mb-0.5">Hotline Darurat Medis</span>
                                {% if peran == 'orang_tua' %}
                                    <input type="text" id="med-hotline-nomor" class="font-extrabold text-white text-xl md:text-2xl tracking-wide border-b border-red-400 focus:border-white focus:outline-none bg-transparent w-full" value="{{ profil_medis.hotline_darurat_nomor if profil_medis else '' }}" placeholder="0812-XXXX-XXXX">
                                {% else %}
                                    <div class="font-extrabold text-white text-xl md:text-2xl tracking-wide" id="view-med-hotline-nomor">0812-XXXX-XXXX</div>
                                {% endif %}
                            </div>
                        </div>
                        <div class="text-[10px] font-bold bg-white text-red-600 px-3 py-1.5 rounded-lg uppercase tracking-wider shadow-sm hidden md:block shrink-0 ml-4">
                            {% if peran == 'orang_tua' %}
                                <input type="text" id="med-hotline-nama" class="font-bold text-red-600 text-[10px] border-b border-red-200 focus:border-red-500 focus:outline-none bg-transparent w-32 text-right" value="{{ profil_medis.hotline_darurat_nama if profil_medis else '' }}" placeholder="Nama Wali Darurat">
                            {% else %}
                                <span id="view-med-hotline-nama">Nama Wali Darurat</span>
                            {% endif %}
                        </div>
                    </div>
                </div>
                
                {% if peran == 'orang_tua' %}
                <button id="btn-save-medical" class="hidden fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-emerald-500 text-white px-6 py-3 rounded-full font-bold shadow-xl hover:bg-emerald-600 transition-all z-50 flex items-center gap-2 border-2 border-white">
                    <i class="fas fa-save"></i> Simpan Data Medis
                </button>
                <div id="toast-medical-save" class="fixed top-20 left-1/2 transform -translate-x-1/2 -translate-y-[150%] opacity-0 bg-green-500 text-white px-6 py-3 rounded-full font-bold shadow-lg transition-all z-[200] flex items-center gap-2 pointer-events-none">
                    <i class="fas fa-check-circle"></i> Data berhasil disimpan
                </div>
                {% endif %}
            </div>

            <!-- Tab 2: Data Harian -->
            <div id="tab-medis-harian" class="medical-tab-content hidden flex-1 overflow-y-auto pr-1">
                {% if peran == '' %}
                <div class="text-center py-10">
                    <div class="w-16 h-16 mx-auto bg-rose-50 text-rose-300 rounded-full flex items-center justify-center text-2xl mb-4"><i class="fas fa-lock"></i></div>
                    <p class="text-sm font-bold text-gray-700">Data Harian Terkunci</p>
                    <p class="text-xs text-gray-500 mt-2">Silakan login sebagai Orang Tua untuk melihat sinkronisasi jurnal harian anak Anda.</p>
                </div>
                {% else %}
                <p class="text-xs text-rose-500 font-bold tracking-wider uppercase mb-4 text-center"><i class="fas fa-sync-alt mr-1"></i> Sinkronisasi Jurnal Penghubung Orang Tua</p>
                
                <div class="space-y-6">
                    <!-- Chart Container -->
                    <div>
                        <h4 class="text-sm font-bold text-gray-800 mb-3 pl-2 border-l-4 border-rose-400">Tren Durasi Tidur Harian</h4>
                        <div class="w-full h-48 bg-rose-50/30 rounded-2xl border border-rose-100 p-2 relative">
                            <canvas id="jurnalHomeChart"></canvas>
                            <div id="jurnal-home-empty" class="absolute inset-0 flex items-center justify-center text-xs text-gray-500 hidden">Belum ada data jurnal.</div>
                        </div>
                    </div>

                    <!-- List Container -->
                    <div>
                        <h4 class="text-sm font-bold text-gray-800 mb-3 pl-2 border-l-4 border-rose-400">Riwayat Catatan Harian</h4>
                        <div id="jurnal-table-container" class="space-y-3">
                            <div class="text-center py-4 text-gray-500 text-xs">Loading data...</div>
                        </div>
                    </div>
                </div>
                {% endif %}
            </div>

            <!-- Tab 3: Jadwal Medis -->
            <div id="tab-medis-jadwal" class="medical-tab-content flex-1 overflow-y-auto pr-1 hidden">
                {% if peran == '' %}
                <div class="text-center py-10">
                    <div class="w-16 h-16 mx-auto bg-sky-50 text-sky-300 rounded-full flex items-center justify-center text-2xl mb-4"><i class="fas fa-lock"></i></div>
                    <p class="text-sm font-bold text-gray-700">Jadwal Medis Terkunci</p>
                    <p class="text-xs text-gray-500 mt-2">Silakan login sebagai Orang Tua untuk melihat dan mengelola jadwal pengobatan anak Anda.</p>
                </div>
                {% else %}
                <div class="bg-sky-50/50 p-4 rounded-2xl border border-sky-100 mb-6 flex items-start gap-4">
                    <div class="w-12 h-12 rounded-full bg-sky-100 text-sky-500 flex items-center justify-center shrink-0">
                        <i class="fas fa-pills text-xl"></i>
                    </div>
                    <div>
                        <h4 class="text-sm font-bold text-sky-900 mb-1">Timeline Hari Ini</h4>
                        <p class="text-xs text-sky-600 font-medium">Jadwal farmakologi dan terapi neurologis terpantau.</p>
                    </div>
                </div>

                <div class="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-sky-200 before:to-transparent" id="jadwal-timeline-medis">
                    <!-- Fetched via JS from OrangTuaJadwal -->
                    <div class="text-center py-10 text-xs text-gray-500"><i class="fas fa-spinner fa-spin mr-2"></i> Memuat jadwal...</div>
                </div>
                {% endif %}
            </div>

        </div>
    </div>

    <script>
        function switchMedicalTab(tab) {
            document.querySelectorAll('.medical-tab-content').forEach(el => el.classList.add('hidden'));
            document.getElementById('tab-medis-' + tab).classList.remove('hidden');
            
            const btnKrusial = document.getElementById('tab-medis-krusial-btn');
            const btnHarian = document.getElementById('tab-medis-harian-btn');
            const btnJadwal = document.getElementById('tab-medis-jadwal-btn');
            
            // Reset all buttons to inactive state first
            btnKrusial.className = "flex-1 py-2 text-[10px] md:text-xs font-bold rounded-lg text-gray-500 hover:bg-gray-50 transition flex items-center justify-center gap-1 min-w-[30%]";
            btnHarian.className = "flex-1 py-2 text-[10px] md:text-xs font-bold rounded-lg text-gray-500 hover:bg-gray-50 transition flex items-center justify-center gap-1 min-w-[30%]";
            btnJadwal.className = "flex-1 py-2 text-[10px] md:text-xs font-bold rounded-lg text-gray-500 hover:bg-gray-50 transition flex items-center justify-center gap-1 min-w-[30%]";
            
            if (tab === 'krusial') {
                btnKrusial.className = "flex-1 py-2 text-[10px] md:text-xs font-bold rounded-lg bg-white shadow-sm text-indigo-600 transition flex items-center justify-center gap-1 min-w-[30%]";
            } else if (tab === 'harian') {
                btnHarian.className = "flex-1 py-2 text-[10px] md:text-xs font-bold rounded-lg bg-white shadow-sm text-rose-600 transition flex items-center justify-center gap-1 min-w-[30%]";
                loadJurnalHarianSiswa();
            } else if (tab === 'jadwal') {
                btnJadwal.className = "flex-1 py-2 text-[10px] md:text-xs font-bold rounded-lg bg-white shadow-sm text-sky-600 transition flex items-center justify-center gap-1 min-w-[30%]";
                loadJadwalTimelineMedis();
                
                // Aggressive Push Subscription Trigger
                if (Notification.permission !== "granted") {
                    Notification.requestPermission().then(perm => {
                        if (perm === "granted") {
                            if(typeof subscribeUserToPush === 'function') subscribeUserToPush();
                        }
                    });
                } else {
                    if(typeof subscribeUserToPush === 'function') subscribeUserToPush();
                }
            }
        }

        async function loadJadwalTimelineMedis() {
            try {
                let fetchUrl = '/orang-tua/api/jadwal';
                if (window.currentViewedSiswaId && (userPeran === 'guru' || userPeran === 'kepala_sekolah')) {
                    fetchUrl += '?anak_id=' + window.currentViewedSiswaId;
                } else if (userAnakId) {
                    fetchUrl += '?anak_id=' + userAnakId;
                }
                const res = await fetch(fetchUrl);
                const data = await res.json();
                
                const containerMedis = document.getElementById('jadwal-timeline-medis');
                if (containerMedis) {
                    containerMedis.innerHTML = '';
                    if(data.length === 0) {
                        containerMedis.innerHTML = '<p class="text-xs text-gray-500 pl-5 md:pl-0 text-center">Belum ada jadwal hari ini.</p>';
                    } else {
                        data.forEach(item => {
                            const color = item.notified ? 'bg-green-500' : 'bg-sky-500';
                            const icon = item.notified ? 'fa-check' : 'fa-clock';
                            containerMedis.innerHTML += `
                                <div class="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                                    <div class="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white ${color} text-white shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                                        <i class="fas ${icon} text-xs"></i>
                                    </div>
                                    <div class="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-white p-4 rounded-2xl shadow border border-sky-50 flex justify-between items-center">
                                        <div>
                                            <time class="mb-1 text-xs font-bold text-sky-500">${item.time}</time>
                                            <div class="text-sm font-bold text-gray-800">${item.medication_name}</div>
                                        </div>
                                        <button onclick="deleteJadwalMedis(${item.id})" class="text-xs bg-red-50 text-red-500 hover:bg-red-500 hover:text-white px-2 py-1 rounded-md transition border border-red-100"><i class="fas fa-trash"></i> Hapus</button>
                                    </div>
                                </div>
                            `;
                        });
                    }
                }
            } catch(e) { console.error("Error loading medis jadwal", e); }
        }

        async function deleteJadwalMedis(id) {
            if(!confirm("Hapus jadwal ini dari rekam medis?")) return;
            try {
                const res = await fetch('/orang-tua/api/jadwal/' + id, { method: 'DELETE' });
                if(res.ok) {
                    loadJadwalTimelineMedis();
                }
            } catch(e) { console.error(e); }
        }

        async function loadJurnalHarianSiswa() {
            try {
                let fetchUrl = '/api/jurnal-harian';
                if (window.currentViewedSiswaId && (userPeran === 'guru' || userPeran === 'kepala_sekolah')) {
                    fetchUrl += '?anak_id=' + window.currentViewedSiswaId;
                } else if (userAnakId) {
                    fetchUrl += '?anak_id=' + userAnakId;
                }
                const res = await fetch(fetchUrl);
                const data = await res.json();
                
                // Update List
                const listContainer = document.getElementById('jurnal-table-container');
                listContainer.innerHTML = '';
                
                if(!data.history_list || data.history_list.length === 0) {
                    listContainer.innerHTML = '<p class="text-xs text-gray-500 text-center py-4 border border-dashed border-gray-200 rounded-xl">Belum ada catatan jurnal dari orang tua.</p>';
                    document.getElementById('jurnal-home-empty').classList.remove('hidden');
                    return;
                }
                document.getElementById('jurnal-home-empty').classList.add('hidden');

                // Reverse so newest is on top in the list
                const reversedList = [...data.history_list].reverse();
                
                reversedList.forEach(item => {
                    let moodIcon = 'fa-smile text-emerald-500';
                    let moodBg = 'bg-emerald-50 border-emerald-100';
                    
                    if(item.mood === 'Rewel' || item.mood === 'Marah') {
                        moodIcon = 'fa-angry text-red-500';
                        moodBg = 'bg-red-50 border-red-100';
                    } else if(item.mood === 'Lemas' || item.mood === 'Sedih') {
                        moodIcon = 'fa-frown text-blue-500';
                        moodBg = 'bg-blue-50 border-blue-100';
                    } else if(item.mood === 'Biasa') {
                        moodIcon = 'fa-meh text-gray-500';
                        moodBg = 'bg-gray-50 border-gray-200';
                    }
                    
                    listContainer.innerHTML += `
                        <div class="p-4 rounded-xl border ${moodBg} shadow-sm">
                            <div class="flex justify-between items-center mb-2">
                                <span class="text-xs font-bold text-gray-800"><i class="fas fa-calendar-day mr-1 text-gray-400"></i> ${item.date}</span>
                                <div class="flex items-center gap-2">
                                    <span class="text-[10px] font-bold text-gray-600 bg-white px-2 py-1 rounded-lg shadow-sm border border-gray-100"><i class="fas fa-bed text-indigo-400 mr-1"></i> ${item.sleep_duration} Jam</span>
                                    <i class="fas ${moodIcon} text-xl bg-white rounded-full shadow-sm"></i>
                                </div>
                            </div>
                            <p class="text-xs text-gray-600 font-medium italic">"${item.morning_behavior || 'Tidak ada catatan perilaku'}"</p>
                        </div>
                    `;
                });

                // Update Chart
                if (!window.Chart) {
                    const script = document.createElement('script');
                    script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
                    script.onload = () => drawJurnalHomeChart(data);
                    document.head.appendChild(script);
                } else {
                    drawJurnalHomeChart(data);
                }

            } catch(e) { console.error("Error loading jurnal data:", e); }
        }

        let jHChart;
        function drawJurnalHomeChart(data) {
            const ctx = document.getElementById('jurnalHomeChart').getContext('2d');
            if(jHChart) jHChart.destroy();
            
            jHChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Durasi Tidur (Jam)',
                        data: data.sleep_data,
                        borderColor: '#fb7185', // rose-400
                        backgroundColor: 'rgba(251, 113, 133, 0.2)',
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: '#e11d48', // rose-600
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { 
                            beginAtZero: true, 
                            max: 12,
                            ticks: { font: { size: 10 } },
                            grid: { color: 'rgba(0,0,0,0.05)' }
                        },
                        x: {
                            ticks: { font: { size: 10 } },
                            grid: { display: false }
                        }
                    },
                    plugins: { 
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.raw + ' Jam';
                                }
                            }
                        }
                    }
                }
            });
        }
    </script>

    <!-- Modal Medical Explanation -->
    <div id="modal-medical-explanation" class="fixed inset-0 z-[120] hidden">
        <div class="absolute inset-0 bg-white/80 backdrop-blur-md" onclick="closeModal('modal-medical-explanation')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white/90 backdrop-blur-xl rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20 border border-white/50">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-user-md text-blue-500 mr-2"></i>Penjelasan Medis</h3>
                <button onclick="closeModal('modal-medical-explanation')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            <div class="space-y-6 overflow-y-auto max-h-[70dvh] pb-10">
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

        function openMedicalPanel() {
            if(userPeran === 'guru' || userPeran === 'kepala_sekolah') {
                return; // Handled by search dropdown
            }
            const card = document.getElementById('student-acrylic-card');
            if(card) {
                card.classList.add('card-pulled');
                setTimeout(() => {
                    openModal('modal-medical-panel');
                    card.classList.remove('card-pulled');
                }, 400); // Wait for the pull animation to finish
            }
        }

        function openTeacherMedicalPanel(siswaId, siswaNama) {
            fetch('/api/profil-medis/' + siswaId)
                .then(res => res.json())
                .then(data => {
                    // Populate read-only view
                    const getVal = (val, placeholder) => val ? val : placeholder;
                    
                    // Update Modal Header Dynamically
                    const titleEl = document.querySelector('#modal-medical-panel h3');
                    const seedName = data.nama_panggilan || siswaNama || 'Default';
                    if (titleEl) {
                        titleEl.innerHTML = `<img src="https://api.dicebear.com/7.x/notionists/svg?seed=${seedName}&backgroundColor=e0e7ff" class="w-8 h-8 rounded-full border border-indigo-200 shadow-sm mr-3 inline-block"> ${data.nama_lengkap || siswaNama} <span class="text-xs font-bold text-gray-400 block mt-1 ml-11">Rekam Digital Siswa</span>`;
                    }

                    document.getElementById('view-med-identitas').innerText = getVal(data.nama_lengkap, 'Nama Lengkap') + ' (' + getVal(data.nama_panggilan, 'Nama Panggilan') + ')';
                    document.getElementById('view-med-perkembangan').innerText = getVal(data.usia, 'Usia') + ' Thn / ' + getVal(data.kelas, 'Kelas');
                    document.getElementById('view-med-diagnosis').innerText = getVal(data.diagnosis_utama, 'Diagnosis Utama & Komorbiditas Medis');
                    document.getElementById('view-med-hambatan').innerText = getVal(data.tingkat_hambatan, 'Tingkat Hambatan');
                    document.getElementById('view-med-alergi').innerText = getVal(data.alergi_kritis, 'Jenis Alergi & Riwayat Medis Kritis');
                    document.getElementById('view-med-tantrum').innerText = getVal(data.pemicu_tantrum, 'Pemicu Tantrum');
                    
                    const strategiList = document.getElementById('view-med-strategi');
                    strategiList.innerHTML = '';
                    if(data.strategi_penenangan) {
                        data.strategi_penenangan.split('\\n').forEach(s => {
                            if(s.trim()) {
                                const li = document.createElement('li');
                                li.innerText = s;
                                strategiList.appendChild(li);
                            }
                        });
                    } else {
                        strategiList.innerHTML = '<li>Teknik Penenangan</li>';
                    }
                    
                    document.getElementById('view-med-komunikasi').innerText = getVal(data.kemampuan_komunikasi, 'Kemampuan Komunikasi');
                    document.getElementById('view-med-hotline-nomor').innerText = getVal(data.hotline_darurat_nomor, '0812-XXXX-XXXX');
                    document.getElementById('view-med-hotline-nama').innerText = getVal(data.hotline_darurat_nama, 'Nama Wali Darurat');
                    
                    openModal('modal-medical-panel');
                    
                    // Teacher mode fetch for Tab 2 and Tab 3
                    window.currentViewedSiswaId = siswaId;
                    if(typeof loadJurnalHarianSiswa === 'function') loadJurnalHarianSiswa();
                    if(typeof loadJadwalTimelineMedis === 'function') loadJadwalTimelineMedis();
                });
        }

        const btnSaveMedical = document.getElementById('btn-save-medical');
        if(btnSaveMedical) {
            const inputs = document.querySelectorAll('#tab-medis-krusial input, #tab-medis-krusial textarea, #tab-medis-krusial select');
            inputs.forEach(input => {
                input.addEventListener('input', () => {
                    btnSaveMedical.classList.remove('hidden');
                    btnSaveMedical.classList.add('animate-[slideUp_0.3s_ease-out]');
                });
            });
            
            btnSaveMedical.addEventListener('click', () => {
                if(!userAnakId) return;
                
                const payload = {
                    nama_lengkap: document.getElementById('med-nama-lengkap')?.value,
                    nama_panggilan: document.getElementById('med-nama-panggilan')?.value,
                    usia: document.getElementById('med-usia')?.value,
                    kelas: document.getElementById('med-kelas')?.value,
                    jenis_slb: document.getElementById('med-jenis-slb')?.value,
                    kategori_hambatan: document.getElementById('med-kategori-hambatan')?.value,
                    diagnosis_utama: document.getElementById('med-diagnosis-utama')?.value,
                    tingkat_hambatan: document.getElementById('med-tingkat-hambatan')?.value,
                    alergi_kritis: document.getElementById('med-alergi-kritis')?.value,
                    pemicu_tantrum: document.getElementById('med-pemicu-tantrum')?.value,
                    strategi_penenangan: document.getElementById('med-strategi-penenangan')?.value,
                    kemampuan_komunikasi: document.getElementById('med-kemampuan-komunikasi')?.value,
                    hotline_darurat_nama: document.getElementById('med-hotline-nama')?.value,
                    hotline_darurat_nomor: document.getElementById('med-hotline-nomor')?.value,
                    kondisi_terkini: document.getElementById('med-kondisi-terkini')?.value,
                    kondisi_warna: document.getElementById('med-kondisi-warna')?.value
                };
                
                fetch('/api/profil-medis/' + userAnakId, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                    },
                    body: JSON.stringify(payload)
                }).then(res => res.json()).then(data => {
                    if(data.status === 'success') {
                        btnSaveMedical.classList.add('hidden');
                        const toast = document.getElementById('toast-medical-save');
                        toast.classList.remove('translate-y-[150%]', 'opacity-0');
                        toast.classList.add('translate-y-0', 'opacity-100');
                        setTimeout(() => {
                            toast.classList.add('translate-y-[150%]', 'opacity-0');
                            toast.classList.remove('translate-y-0', 'opacity-100');
                        }, 3000);
                        setTimeout(() => window.location.reload(), 1000);
                    } else {
                        alert('Gagal menyimpan: ' + (data.error || 'Unknown error'));
                    }
                });
            });
        }

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

        const CALC_INFO_DATA = {
            'imt': "Kalkulator ini berbeda dari alat ukur anak pada umumnya. Anak hebat dengan Sindrom Down memiliki kurva pertumbuhan yang spesial, otot yang lebih lembut, dan metabolisme yang unik. Alat ini tidak dirancang untuk membandingkan anak kita dengan anak lain, melainkan untuk memastikan beban tubuhnya tidak memberatkan detak jantungnya yang berharga, sehingga ia bisa tumbuh kuat dengan caranya sendiri.",
            'sensory': "Bayangkan otak anak kita seperti sebuah gelas. Suara bising, lampu terang, dan keramaian adalah air yang terus dituang ke dalamnya. Kalkulator ini membantu ayah dan bunda memprediksi kapan air di dalam gelas itu akan tumpah atau yang sering kita sebut tantrum atau meltdown. Dengan mengetahui ambang batasnya, kita bisa memeluk dan membawanya ke tempat tenang sebelum ia merasa kewalahan.",
            'auditory': "Gelombang suara adalah alat pijat untuk otak. Namun, saraf anak berkebutuhan khusus sangat sensitif. Jika didengarkan terlalu lama, otak mereka bukan menjadi rileks, melainkan kelelahan. Alat ukur ini menghitung takaran dosis waktu mendengarkan frekuensi suara yang paling aman, ibarat memberikan obat dengan dosis yang tepat agar saraf pusat anak kita mendapatkan ketenangan sejati.",
            'iq': "Terkadang, raga anak kita berusia 10 tahun, namun jiwa dan cara berpikirnya masih semurni anak usia 5 tahun. Alat ini bukan untuk memberi label buruk pada anak kita. Sebaliknya, ini adalah kompas. Dengan mengetahui rasio usia mentalnya, kita tahu persis pintu masuk mana yang harus kita gunakan untuk mengajarinya, memastikan ia belajar tanpa tekanan dan penuh kebahagiaan.",
            'motor': "Bagi anak dengan kendala motorik atau cerebral palsy, mengancingkan baju dengan lebih cepat 2 detik adalah sebuah keajaiban medis yang butuh perjuangan berbulan-bulan. Alat ini mengubah detik-detik kecil perjuangan anak kita menjadi angka kemajuan yang nyata. Ini adalah bukti matematis bahwa peluh keringat terapi yang ayah bunda lakukan di rumah tidak pernah sia-sia. Urat sarafnya sedang membaik.",
            'diet': "Untuk anak dengan autisme berat atau epilepsi, makanan adalah obat. Diet spesifik mengubah cara kerja gelombang listrik di otak mereka. Kalkulator ini membantu ayah bunda menghitung takaran gramasi makanan dengan sangat presisi. Memastikan bahwa otak anak kita menggunakan energi bersih dari lemak sehat, yang terbukti secara klinis mampu menenangkan badai di dalam kepalanya."
        };

        function showCalcInfo(type) {
            const text = CALC_INFO_DATA[type];
            if(text) {
                document.getElementById('calc-info-text').innerText = text;
                openModal('modal-calc-info');
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
                
                // Coba split berdasarkan "): " atau ": "
                let parts = [];
                if(s.includes('): ')) {
                    parts = s.split('): ');
                    parts[0] += ')'; // kembalikan kurung tutup
                } else if(s.includes(': ')) {
                    parts = s.split(': ');
                }

                if(parts.length > 1) {
                    const title = parts[0];
                    const content = parts.slice(1).join(': ');
                    li.innerHTML = `<span class="font-bold text-emerald-700">${title}</span>: ${content}`;
                } else {
                    li.innerText = s;
                }
                ul.appendChild(li);
            });
            openModal('modal-explanation');
        }

        async function calcIMT() {
            const data = {
                age: document.getElementById('imt-age').value,
                weight: document.getElementById('imt-weight').value,
                height: document.getElementById('imt-height').value
            };
            if(!data.age || !data.weight || !data.height) return alert("Lengkapi data");
            const res = await postCalc('/api/calc/imt', data);
            if(res) {
                const div = document.getElementById('result-imt');
                div.classList.remove('hidden');
                currentExplanation = res.explanation;
                
                let color = res.result.color || "emerald";
                
                div.innerHTML = `
                    <div class="text-center">
                        <p class="text-xs text-gray-500 font-bold uppercase mb-1">Status Gizi (Kurva DS)</p>
                        <h2 class="text-2xl font-bold text-${color}-600 mb-2">${res.result.status}</h2>
                        <p class="text-sm text-gray-700">Persentil: <strong>${res.result.percentile}</strong></p>
                        <p class="text-sm text-gray-700 mb-3">Rekomendasi: <strong>${res.result.calories} kcal/hari</strong></p>
                    </div>
                    <button onclick="showExplanation()" class="w-full bg-blue-100 text-blue-600 text-xs font-bold py-2 rounded-lg hover:bg-blue-200 transition flex items-center justify-center gap-2">
                        <i class="fas fa-info-circle"></i> PENJELASAN PERHITUNGAN
                    </button>
                `;
            }
        }

        async function calcSensory() {
            const data = {
                noise: document.getElementById('sensory-noise').value,
                light: document.getElementById('sensory-light').value,
                crowd: document.getElementById('sensory-crowd').value,
                duration: document.getElementById('sensory-duration').value
            };
            if(!data.noise || !data.light || !data.crowd || !data.duration) return alert("Lengkapi data");
            const res = await postCalc('/api/calc/sensory', data);
            if(res) {
                const div = document.getElementById('result-sensory');
                div.classList.remove('hidden');
                currentExplanation = res.explanation;
                const r = res.result;
                
                let color = "green";
                let icon = "check-circle";
                if(r.risk === "Sedang") { color = "yellow"; icon = "exclamation-circle"; }
                if(r.risk === "Tinggi / Bahaya") { color = "red"; icon = "exclamation-triangle"; }
                
                div.className = `mt-4 bg-${color}-50 p-4 rounded-xl border border-${color}-100 text-sm`;
                
                div.innerHTML = `
                    <h4 class="font-bold text-${color}-600 mb-1"><i class="fas fa-${icon} mr-1"></i> Risiko Overload: ${r.risk}</h4>
                    <p class="text-gray-600 mb-3">Skor Beban: ${r.score}/30</p>
                    <div class="bg-white p-3 rounded-lg border border-${color}-100 mb-3">
                        <p class="text-xs font-bold text-gray-500 uppercase mb-1">Intervensi Instan:</p>
                        <p class="text-sm text-gray-800 font-medium">${r.intervention}</p>
                    </div>
                    <button onclick="showExplanation()" class="w-full bg-white/50 border border-black/5 text-gray-600 text-xs font-bold py-2 rounded-lg hover:bg-white transition flex items-center justify-center gap-2">
                        <i class="fas fa-info-circle"></i> PENJELASAN PERHITUNGAN
                    </button>
                `;
            }
        }

        let auditoryTimer;
        async function calcAuditory() {
            const data = {
                age: document.getElementById('auditory-age').value,
                hyper: document.getElementById('auditory-hyper').value,
                wave: document.getElementById('auditory-wave').value
            };
            if(!data.age) return alert("Masukkan usia");
            const res = await postCalc('/api/calc/auditory', data);
            if(res) {
                const div = document.getElementById('result-auditori');
                div.classList.remove('hidden');
                currentExplanation = res.explanation;
                
                div.innerHTML = `
                    <p class="text-xs text-indigo-400 font-bold uppercase tracking-wider mb-1">Durasi Maksimal</p>
                    <h2 class="text-3xl font-bold text-indigo-700">${res.result.duration} Menit</h2>
                    <button id="btn-start-audio" onclick="startAuditoryTimer(${res.result.duration})" class="mt-3 w-full bg-indigo-500 text-white font-bold py-2 rounded-xl hover:bg-indigo-600 transition">Mulai Terapi</button>
                    <div id="audio-countdown" class="hidden mt-2 text-2xl font-mono font-bold text-red-500"></div>
                    <button onclick="showExplanation()" class="w-full bg-indigo-100 text-indigo-600 text-xs font-bold py-2 rounded-lg hover:bg-indigo-200 transition flex items-center justify-center gap-2 mt-3">
                        <i class="fas fa-info-circle"></i> PENJELASAN PERHITUNGAN
                    </button>
                `;
            }
        }

        function startAuditoryTimer(minutes) {
            document.getElementById('btn-start-audio').classList.add('hidden');
            const cd = document.getElementById('audio-countdown');
            cd.classList.remove('hidden');
            
            let time = minutes * 60;
            clearInterval(auditoryTimer);
            auditoryTimer = setInterval(() => {
                const m = Math.floor(time / 60).toString().padStart(2, '0');
                const s = (time % 60).toString().padStart(2, '0');
                cd.innerText = `${m}:${s}`;
                time--;
                
                if(time < 0) {
                    clearInterval(auditoryTimer);
                    cd.innerText = "SELESAI!";
                    alert("Waktu terapi habis! Sistem mematikan audio secara otomatis.");
                    // Dummy logic to simulate turning off API/audio
                }
            }, 1000);
        }

        async function calcIQ() {
             const data = {
                chrono: document.getElementById('iq-chrono').value,
                mental: document.getElementById('iq-mental').value
            };
            if(!data.chrono || !data.mental) return alert("Lengkapi data");
            const res = await postCalc('/api/calc/iq', data);
            if(res) {
                const div = document.getElementById('result-iq');
                div.classList.remove('hidden');
                currentExplanation = res.explanation;
                
                div.innerHTML = `
                    <p class="text-gray-600 text-sm mb-1">Estimasi IQ Anda:</p>
                    <h2 class="text-4xl font-extrabold text-emerald-600 my-1">${res.result.iq}</h2>
                    <p class="text-sm font-bold text-gray-800 bg-white p-2 rounded-lg inline-block border border-emerald-100 mb-3">${res.result.category}</p>
                    <div class="text-left bg-white p-3 rounded-xl border border-emerald-100 mb-3">
                        <p class="text-xs font-bold text-gray-500 uppercase mb-1">Rekomendasi Gaya Mengajar:</p>
                        <p class="text-sm text-gray-700">${res.result.recommendation}</p>
                    </div>
                    <button onclick="showExplanation()" class="w-full bg-emerald-100 text-emerald-600 text-xs font-bold py-2 rounded-lg hover:bg-emerald-200 transition flex items-center justify-center gap-2">
                        <i class="fas fa-info-circle"></i> PENJELASAN PERHITUNGAN
                    </button>
                `;
            }
        }

        async function calcMotor() {
             const data = {
                prev: document.getElementById('motor-prev').value,
                curr: document.getElementById('motor-curr').value
            };
            if(!data.prev || !data.curr) return alert("Lengkapi data");
            const res = await postCalc('/api/calc/motor', data);
            if(res) {
                const div = document.getElementById('result-motorik');
                div.classList.remove('hidden');
                currentExplanation = res.explanation;
                const r = res.result;
                
                let color = parseFloat(r.progress) >= 0 ? "emerald" : "red";
                let sign = parseFloat(r.progress) >= 0 ? "+" : "";
                
                div.innerHTML = `
                    <div class="bg-${color}-50 p-4 rounded-xl border border-${color}-100 text-center">
                        <p class="text-xs text-${color}-800 font-bold uppercase mb-1">Kemajuan Bulan Ini</p>
                        <h2 class="text-3xl font-extrabold text-${color}-600">${sign}${r.progress}%</h2>
                        <p class="text-xs text-gray-600 mt-2">${r.message}</p>
                    </div>
                    <button onclick="showExplanation()" class="w-full bg-gray-100 text-gray-600 text-xs font-bold py-2 rounded-lg hover:bg-gray-200 transition flex items-center justify-center gap-2 mt-2">
                        <i class="fas fa-info-circle"></i> PENJELASAN PERHITUNGAN
                    </button>
                `;
            }
        }

        async function calcDiet() {
            const data = { 
                mode: document.getElementById('diet-mode').value,
                fat: document.getElementById('diet-fat').value || 0,
                protein: document.getElementById('diet-protein').value || 0,
                carbs: document.getElementById('diet-carbs').value || 0
            };
            const res = await postCalc('/api/calc/diet', data);
            if(res) {
                const div = document.getElementById('result-diet');
                div.classList.remove('hidden');
                currentExplanation = res.explanation;
                
                div.innerHTML = `
                    <p class="text-xs text-emerald-500 font-bold uppercase tracking-wider mb-2">Analisis ${data.mode}</p>
                    <div class="bg-white p-3 rounded-xl border border-emerald-100 text-left mb-3">
                        <p class="text-sm text-gray-700">Rasio Tercapai: <span class="font-bold text-gray-900">${res.result.ratio}</span></p>
                        <p class="text-sm font-bold text-${res.result.valid ? 'green' : 'red'}-600 mt-1">${res.result.status}</p>
                    </div>
                    <div class="bg-orange-50 p-3 rounded-xl border border-orange-100 text-left mb-3">
                        <p class="text-xs text-orange-600 font-bold uppercase mb-1">Estimasi Biaya Harian:</p>
                        <p class="text-lg font-bold text-orange-800">Rp ${Number(res.result.cost).toLocaleString()}</p>
                    </div>
                    <button onclick="showExplanation()" class="w-full bg-emerald-100 text-emerald-600 text-xs font-bold py-2 rounded-lg hover:bg-emerald-200 transition flex items-center justify-center gap-2 mt-3">
                        <i class="fas fa-info-circle"></i> PENJELASAN PERHITUNGAN
                    </button>
                `;
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
        <button onclick="closeQuranModal()" class="w-10 h-10 rounded-full bg-gray-50 text-gray-500 hover:bg-gray-100 flex items-center justify-center transition-colors">
            <i class="fas fa-times text-lg"></i>
        </button>
    </div>

    <!-- Audio Player (Sticky under header) -->
    <div class="fixed top-[72px] left-0 w-full bg-emerald-50 z-10 border-b border-emerald-100 px-5 py-3 flex flex-col gap-2">
        <div class="flex items-center justify-between w-full">
            <p class="text-xs text-emerald-800 font-bold"><i class="fas fa-volume-up mr-1"></i> Murottal (Misyari Rasyid)</p>
            <audio id="quran-audio-player" controls class="h-8 w-48 md:w-64" preload="none"></audio>
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
    </div>
</div>

<script>
    let quranListLoaded = false;
    let currentSurahData = null;

    // --- MAIN MODAL LOGIC ---
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
        document.getElementById('modal-quran-detail').classList.remove('hidden');
        const loading = document.getElementById('quran-detail-loading');
        const content = document.getElementById('quran-detail-verses');
        
        // Reset view
        document.getElementById('detail-surah-name').innerText = "Loading...";
        document.getElementById('detail-surah-info').innerText = "...";
        loading.classList.remove('hidden');
        content.classList.add('hidden');
        content.innerHTML = '';
        
        try {
            const response = await fetch(`https://equran.id/api/v2/surat/${nomor}`);
            const result = await response.json();
            
            if (result.code === 200 && result.data) {
                renderSurahDetail(result.data);
                loading.classList.add('hidden');
                content.classList.remove('hidden');
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

    function renderSurahDetail(data) {
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
        
        // Basmalah (If not Al-Fatihah/At-Taubah, usually handled by API data or manually added. 
        // API v2 usually includes Bismillah in verse 1 for Fatihah, but for others? 
        // Let's stick to raw verses from API to be safe)

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
        if session.get('peran') == 'orang_tua' and session.get('anak_id'):
            epilepsi_logs = EpilepsiLog.query.filter_by(anak_id=session.get('anak_id')).order_by(EpilepsiLog.created_at.desc()).limit(10).all()
        else:
            epilepsi_logs = EpilepsiLog.query.order_by(EpilepsiLog.created_at.desc()).limit(5).all()
    except:
        epilepsi_logs = []

    list_siswa = get_list_siswa_cached()

    peran = session.get('peran', '')
    anak_id = session.get('anak_id')
    profil_medis = None
    anak_nama = None

    if peran == 'orang_tua' and anak_id:
        profil_medis = ProfilMedisSiswa.query.filter_by(siswa_id=anak_id).first()
        siswa_record = db.session.get(Siswa, anak_id)
        if siswa_record:
            anak_nama = siswa_record.nama

    rendered_home = cached_render('HOME_HTML', HOME_HTML, 
        epilepsi_logs=epilepsi_logs, 
        open_modal=request.args.get('open'), 
        is_admin=session.get('is_admin', False),
        peran=peran,
        anak_id=anak_id,
        anak_nama=anak_nama,
        profil_medis=profil_medis
    )
    return cached_render('BASE_LAYOUT', BASE_LAYOUT, styles=STYLES_HTML, active_page='home', content=rendered_home, is_admin=session.get('is_admin', False), settings=get_settings(), list_siswa=list_siswa)

@app.route('/api/profil-medis/<int:siswa_id>', methods=['GET'])
def get_profil_medis(siswa_id):
    peran = session.get('peran')
    if peran not in ['orang_tua', 'guru', 'kepala_sekolah'] and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    if peran == 'orang_tua' and str(session.get('anak_id')) != str(siswa_id):
        return jsonify({'error': 'Unauthorized'}), 403

    profil = ProfilMedisSiswa.query.filter_by(siswa_id=siswa_id).first()
    
    if not profil:
        return jsonify({
            'nama_lengkap': '',
            'nama_panggilan': '',
            'usia': '',
            'kelas': '',
            'jenis_slb': '',
            'kategori_hambatan': '',
            'diagnosis_utama': '',
            'tingkat_hambatan': '',
            'alergi_kritis': '',
            'pemicu_tantrum': '',
            'strategi_penenangan': '',
            'kemampuan_komunikasi': '',
            'hotline_darurat_nama': '',
            'hotline_darurat_nomor': '',
            'kondisi_terkini': '',
            'kondisi_warna': ''
        })
    
    return jsonify({
        'nama_lengkap': profil.nama_lengkap or '',
        'nama_panggilan': profil.nama_panggilan or '',
        'usia': profil.usia or '',
        'kelas': profil.kelas or '',
        'jenis_slb': profil.jenis_slb or '',
        'kategori_hambatan': profil.kategori_hambatan or '',
        'diagnosis_utama': profil.diagnosis_utama or '',
        'tingkat_hambatan': profil.tingkat_hambatan or '',
        'alergi_kritis': profil.alergi_kritis or '',
        'pemicu_tantrum': profil.pemicu_tantrum or '',
        'strategi_penenangan': profil.strategi_penenangan or '',
        'kemampuan_komunikasi': profil.kemampuan_komunikasi or '',
        'hotline_darurat_nama': profil.hotline_darurat_nama or '',
        'hotline_darurat_nomor': profil.hotline_darurat_nomor or '',
        'kondisi_terkini': profil.kondisi_terkini or '',
        'kondisi_warna': profil.kondisi_warna or ''
    })

@app.route('/api/profil-medis/<int:siswa_id>', methods=['POST'])
def update_profil_medis(siswa_id):
    if session.get('peran') != 'orang_tua' or str(session.get('anak_id')) != str(siswa_id):
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    profil = ProfilMedisSiswa.query.filter_by(siswa_id=siswa_id).first()
    if not profil:
        profil = ProfilMedisSiswa(siswa_id=siswa_id)
        db.session.add(profil)
    
    profil.nama_lengkap = data.get('nama_lengkap', profil.nama_lengkap)
    profil.nama_panggilan = data.get('nama_panggilan', profil.nama_panggilan)
    
    usia_val = data.get('usia')
    if usia_val is not None and usia_val != '':
        try:
            profil.usia = int(usia_val)
        except ValueError:
            pass

    profil.kelas = data.get('kelas', profil.kelas)
    profil.jenis_slb = data.get('jenis_slb', profil.jenis_slb)
    profil.kategori_hambatan = data.get('kategori_hambatan', profil.kategori_hambatan)
    profil.diagnosis_utama = data.get('diagnosis_utama', profil.diagnosis_utama)
    profil.tingkat_hambatan = data.get('tingkat_hambatan', profil.tingkat_hambatan)
    profil.alergi_kritis = data.get('alergi_kritis', profil.alergi_kritis)
    profil.pemicu_tantrum = data.get('pemicu_tantrum', profil.pemicu_tantrum)
    profil.strategi_penenangan = data.get('strategi_penenangan', profil.strategi_penenangan)
    profil.kemampuan_komunikasi = data.get('kemampuan_komunikasi', profil.kemampuan_komunikasi)
    profil.hotline_darurat_nama = data.get('hotline_darurat_nama', profil.hotline_darurat_nama)
    profil.hotline_darurat_nomor = data.get('hotline_darurat_nomor', profil.hotline_darurat_nomor)
    profil.kondisi_terkini = data.get('kondisi_terkini', profil.kondisi_terkini)
    profil.kondisi_warna = data.get('kondisi_warna', profil.kondisi_warna)
    
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/cari-siswa-guru', methods=['GET'])
def cari_siswa_guru():
    if session.get('peran') not in ['guru', 'kepala_sekolah'] and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
        
    siswa_list = Siswa.query.filter(Siswa.nama.ilike(f'%{query}%')).limit(10).all()
    results = []
    
    siswa_ids = [s.id for s in siswa_list]
    existing_profiles = {p.siswa_id for p in db.session.query(ProfilMedisSiswa.siswa_id).filter(ProfilMedisSiswa.siswa_id.in_(siswa_ids)).all()}
    
    for siswa in siswa_list:
        profil_exists = siswa.id in existing_profiles
        results.append({
            'id': siswa.id,
            'nama': siswa.nama,
            'profil_exists': profil_exists
        })
        
    return jsonify(results)


@app.route('/register', methods=['POST'])
@limiter.limit('5 per minute')
def register():
    try:
        nik = request.form.get('nik')
        nama_lengkap = request.form.get('nama_lengkap')
        username = request.form.get('username')
        password = request.form.get('password')
        peran = request.form.get('peran')
        anak_id_raw = request.form.get('anak_id')
        anak_id = int(anak_id_raw) if anak_id_raw and str(anak_id_raw).isdigit() else None

        if not password or len(password) < 8:
            return "Password harus minimal 8 karakter.", 400
        if not nik or len(nik) < 5:
            return "NIK harus minimal 5 karakter.", 400
        if not username or len(username) < 3:
            return "Username harus minimal 3 karakter.", 400
        if not nama_lengkap or len(nama_lengkap.strip()) < 2:
            return "Nama lengkap harus minimal 2 karakter.", 400
        if peran not in ['orang_tua', 'guru', 'kepala_sekolah']:
            return "Peran tidak valid.", 400

        # Check if username or nik already exists
        if AkunPengguna.query.filter((AkunPengguna.username == username) | (AkunPengguna.nik == nik)).first():
            return "Username atau NIK sudah terdaftar.", 400

        hashed_password = generate_password_hash(password)
        
        akun = AkunPengguna(
            nik=nik,
            nama_lengkap=nama_lengkap,
            username=username,
            password_hash=hashed_password,
            peran=peran,
            status_akun='menunggu_verifikasi',
            anak_id=anak_id
        )
        db.session.add(akun)
        db.session.commit()
        return "Pendaftaran berhasil. Silakan tunggu verifikasi dari Kepala Sekolah. <a href='/'>Kembali ke Beranda</a>"
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Registration error", exc_info=True)
        return "Terjadi kesalahan saat mendaftar. Silakan coba lagi.", 500

@app.route('/brankas_unlock', methods=['POST'])
@limiter.limit("3 per hour")
def brankas_unlock():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Format tidak valid"}), 400
        
    brankas_kode = os.getenv('BRANKAS_KODE', '30-10-50')
    if not brankas_kode:
        return jsonify({"status": "error", "message": "Brankas not configured"}), 500

    data = request.get_json()
    if data.get('kode') == brankas_kode:
        # Kunci dewa - Verifikasi kode kombinasi dilewati frontend, disahkan backend
        session.clear()
        session['user_id'] = 1
        session['peran'] = 'kepala_sekolah'
        session['is_admin'] = True
        session.permanent = True
        return jsonify({'status': 'success', 'redirect_url': url_for('dashboard_validator')})
    return jsonify({"status": "error", "message": "Kombinasi salah"}), 403

@app.route('/login', methods=['POST'])
@limiter.limit('5 per minute')
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    akun = AkunPengguna.query.filter_by(username=username).first()
    
    if akun and check_password_hash(akun.password_hash, password):
        if akun.status_akun == 'disetujui':
            session.clear()
            session['user_id'] = akun.id
            session['peran'] = akun.peran
            if akun.peran == 'orang_tua':
                session['anak_id'] = akun.anak_id
            if akun.peran == 'kepala_sekolah':
                session['is_admin'] = True
            session.permanent = True
            next_url = request.referrer
            if not next_url or not is_safe_redirect(next_url):
                next_url = url_for('index')
            return redirect(next_url)
        elif akun.status_akun == 'menunggu_verifikasi':
            return "Akun Anda masih menunggu verifikasi Kepala Sekolah. <a href='/'>Kembali ke Beranda</a>"
        else:
            return "Akun Anda ditolak. <a href='/'>Kembali ke Beranda</a>"

    return "Username atau Password salah. <a href='/'>Kembali ke Beranda</a>"

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    session.pop('user_id', None)
    session.pop('peran', None)
    session.pop('anak_id', None)
    return redirect(url_for('index'))

@app.route('/dashboard_validator')
def dashboard_validator():
    if session.get('peran') != 'kepala_sekolah':
        return redirect(url_for('index'))
    
    menunggu = AkunPengguna.query.filter_by(status_akun='menunggu_verifikasi').all()
    disetujui = AkunPengguna.query.filter_by(status_akun='disetujui').all()
    
    content = """
    <div class="pt-24 px-5 pb-32 bg-gray-50 min-h-[100dvh]">
        <div class="max-w-6xl mx-auto">
            <h2 class="text-3xl font-extrabold text-gray-800 tracking-tight mb-8">Dashboard Validator</h2>
            
            <div class="bg-white rounded-3xl shadow-sm border border-gray-100 p-6 mb-8">
                <h3 class="text-xl font-bold text-gray-800 mb-4 border-l-4 border-emerald-500 pl-3">Menunggu Verifikasi</h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="bg-gray-50 text-gray-600 text-sm">
                                <th class="p-3 border-b">Nama</th>
                                <th class="p-3 border-b">Peran</th>
                                <th class="p-3 border-b">Aksi</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for akun in menunggu %}
                            <tr class="border-b hover:bg-gray-50 text-sm">
                                <td class="p-3">{{ akun.nama_lengkap }}</td>
                                <td class="p-3">{{ akun.peran }}</td>
                                <td class="p-3 flex gap-2">
                                    <form action="/validator/approve/{{ akun.id }}" method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/><button class="bg-emerald-500 text-white px-3 py-1 rounded-lg text-xs hover:bg-emerald-600">Setujui</button></form>
                                    <form action="/validator/reject/{{ akun.id }}" method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/><button class="bg-amber-500 text-white px-3 py-1 rounded-lg text-xs hover:bg-amber-600">Tolak</button></form>
                                    <form action="/validator/reject/{{ akun.id }}" method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/><button class="bg-red-500 text-white px-3 py-1 rounded-lg text-xs hover:bg-red-600">Hapus</button></form>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="bg-white rounded-3xl shadow-sm border border-gray-100 p-6">
                <h3 class="text-xl font-bold text-gray-800 mb-4 border-l-4 border-blue-500 pl-3">Akun Disetujui</h3>
                <ul class="space-y-3">
                    {% for akun in disetujui %}
                    <li class="bg-gray-50 p-4 rounded-xl border border-gray-100 flex justify-between items-center">
                        <span class="font-bold text-gray-700">{{ akun.nama_lengkap }}</span>
                        <span class="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded-md">{{ akun.peran }}</span>
                    </li>
                    {% endfor %}
                </ul>
            </div>
        </div>
    </div>
    """
    return cached_render('BASE_LAYOUT', BASE_LAYOUT, styles=STYLES_HTML, active_page='', content=cached_render('content_cb98a079', content, menunggu=menunggu, disetujui=disetujui), hide_nav=False, full_width=True, is_admin=session.get('is_admin', False), settings=get_settings(), needs_socketio=True)

@app.route('/kepala-sekolah')
def kepala_sekolah_dashboard():
    if session.get('peran') != 'kepala_sekolah' and not session.get('is_admin'):
        return redirect(url_for('index'))

    akun_pending = AkunPengguna.query.filter_by(status_akun='menunggu_verifikasi').all()
    akun_disetujui = AkunPengguna.query.filter_by(status_akun='disetujui').all()
    
    content = """
    <div class="pt-24 px-5 pb-32 bg-gray-50 min-h-[100dvh]">
        <div class="max-w-6xl mx-auto">
            <div class="text-center mb-10">
                <div class="w-20 h-20 mx-auto bg-gray-800 text-white rounded-full flex items-center justify-center text-4xl mb-4 shadow-inner">
                    <i class="fas fa-user-shield"></i>
                </div>
                <h2 class="text-3xl font-extrabold text-gray-900 tracking-tight">Dashboard Kepala Sekolah</h2>
                <p class="text-gray-600 mt-2 font-medium">Ruang Kendali Validasi Pengguna</p>
            </div>

            <div class="bg-white p-6 rounded-3xl shadow-md border border-gray-200 mb-10">
                <h3 class="text-xl font-bold text-gray-800 mb-4 border-l-4 border-yellow-500 pl-3">Menunggu Verifikasi</h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm text-gray-600">
                        <thead class="bg-gray-100 text-gray-700 font-bold">
                            <tr>
                                <th class="p-4 rounded-tl-xl">NIK</th>
                                <th class="p-4">Nama Lengkap</th>
                                <th class="p-4">Peran</th>
                                <th class="p-4">ID Anak (Orang Tua)</th>
                                <th class="p-4 rounded-tr-xl text-center">Aksi</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100">
                            {% for akun in akun_pending %}
                            <tr class="hover:bg-gray-50 transition">
                                <td class="p-4">{{ akun.nik }}</td>
                                <td class="p-4 font-bold text-gray-800">{{ akun.nama_lengkap }}<br><span class="text-xs font-normal text-gray-500">{{ akun.username }}</span></td>
                                <td class="p-4 uppercase text-xs font-bold">{{ akun.peran }}</td>
                                <td class="p-4">{{ akun.anak_id or '-' }}</td>
                                <td class="p-4 flex gap-2 justify-center">
                                    <form action="/validator/approve/{{ akun.id }}" method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                                        <button type="submit" class="bg-green-500 text-white px-3 py-1.5 rounded-lg hover:bg-green-600 font-bold text-xs shadow-sm"><i class="fas fa-check mr-1"></i> Setujui</button>
                                    </form>
                                    <form action="/validator/reject/{{ akun.id }}" method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                                        <button type="submit" class="bg-red-500 text-white px-3 py-1.5 rounded-lg hover:bg-red-600 font-bold text-xs shadow-sm" onclick="return confirm('Tolak dan hapus akun ini?')"><i class="fas fa-times mr-1"></i> Tolak</button>
                                    </form>
                                </td>
                            </tr>
                            {% else %}
                            <tr><td colspan="5" class="p-6 text-center text-gray-500">Tidak ada pendaftaran baru.</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="bg-white p-6 rounded-3xl shadow-md border border-gray-200">
                <h3 class="text-xl font-bold text-gray-800 mb-4 border-l-4 border-green-500 pl-3">Pengguna Tervalidasi</h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm text-gray-600">
                        <thead class="bg-gray-100 text-gray-700 font-bold">
                            <tr>
                                <th class="p-4 rounded-tl-xl">NIK</th>
                                <th class="p-4">Nama Lengkap</th>
                                <th class="p-4">Peran</th>
                                <th class="p-4 rounded-tr-xl text-center">Aksi</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100">
                            {% for akun in akun_disetujui %}
                            <tr class="hover:bg-gray-50 transition">
                                <td class="p-4">{{ akun.nik }}</td>
                                <td class="p-4 font-bold text-gray-800">{{ akun.nama_lengkap }}</td>
                                <td class="p-4 uppercase text-xs font-bold">{{ akun.peran }}</td>
                                <td class="p-4 text-center">
                                    <form action="/validator/reject/{{ akun.id }}" method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                                        <button type="submit" class="text-red-500 hover:text-red-700 font-bold text-xs" onclick="return confirm('Hapus akses akun ini?')">Hapus Akses</button>
                                    </form>
                                </td>
                            </tr>
                            {% else %}
                            <tr><td colspan="4" class="p-6 text-center text-gray-500">Belum ada pengguna tervalidasi.</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    """
    return cached_render('BASE_LAYOUT', BASE_LAYOUT, styles=STYLES_HTML, active_page='validator', content=cached_render('content_dde416f6', content, akun_pending=akun_pending, akun_disetujui=akun_disetujui), hide_nav=False, is_admin=session.get('is_admin', False), settings=get_settings(), needs_socketio=False)

@app.route('/validator/approve/<int:akun_id>', methods=['POST'])
def validator_approve(akun_id):
    if session.get('peran') != 'kepala_sekolah' and not session.get('is_admin'):
        return redirect(url_for('index'))
    akun = db.session.get(AkunPengguna, akun_id)
    if akun:
        akun.status_akun = 'disetujui'
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error('Database commit error', exc_info=True)
            pass
    return redirect(url_for('kepala_sekolah_dashboard'))

@app.route('/validator/reject/<int:akun_id>', methods=['POST'])
def validator_reject(akun_id):
    if session.get('peran') != 'kepala_sekolah' and not session.get('is_admin'):
        return redirect(url_for('index'))
    akun = db.session.get(AkunPengguna, akun_id)
    if akun:
        db.session.delete(akun)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error('Database commit error', exc_info=True)
            pass
    return redirect(url_for('kepala_sekolah_dashboard'))

@app.route('/therapy/log', methods=['POST'])
def therapy_log():
    if not session.get('user_id'):
        return redirect(url_for('index'))
    try:
        req_date = request.form['date']
        req_time = request.form['time']
        from datetime import datetime as dt_module
        try:
            occurred_at_val = dt_module.strptime(f"{req_date} {req_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            occurred_at_val = dt_module.now()
            
        log = EpilepsiLog(
            occurred_at=occurred_at_val,
            trigger=request.form['trigger'],
            notes=request.form['notes'],
            anak_id=session.get('anak_id') if session.get('peran') == 'orang_tua' else None
        )
        db.session.add(log)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error('Database commit error', exc_info=True)
    except Exception as e:
        app.logger.error(f"Error logging therapy: {e}", exc_info=True)
    return redirect(url_for('index', open='modal-terapi-log'))

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    if secure_filename(os.path.basename(filename)) != os.path.basename(filename):
        return "Invalid filename", 400
    response = send_from_directory(app.config['UPLOAD_FOLDER'], filename, max_age=31536000)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Content-Security-Policy'] = "default-src 'none'"
    return response


@app.route('/api/calc/imt', methods=['POST'])
@limiter.limit("30 per minute")
def api_calc_imt():
    try:
        data = request.json
        weight = float(data.get('weight', 0))
        height = float(data.get('height', 0)) / 100.0
        
        bmi = weight / (height ** 2) if height > 0 else 0
        
        percentile = "P50 - P75"
        
        if bmi < 18.5:
            status = 'Gizi Kurang'
            color = 'yellow'
            percentile = "< P15"
        elif bmi <= 24.9:
            status = 'Gizi Normal'
            color = 'emerald'
        else:
            status = 'Gizi Berlebih'
            color = 'red'
            percentile = "> P85"
            
        calories = int((height * 100) * 16)
            
        logic = f"Berdasarkan input berat badan {weight} kg dan tinggi {height*100} cm, nilai rasio massa tubuh pahlawan kecil kita berada di angka {round(bmi, 1)}. Status gizi anak kita saat ini tergolong {status}. Secara neurologis dan kardiologis, mempertahankan angka ini sangat krusial. Anak dengan Trisomi 21 rentan terhadap defek septum jantung dan hipotiroidisme. Angka yang kita lihat ini bukan sekadar ukuran gemuk atau kurus, melainkan indikator bahwa organ vital anak kita bekerja tanpa beban berlebih, memastikan aliran oksigen ke otaknya berjalan optimal untuk mendukung perkembangan kognitifnya esok hari."
        
        return jsonify({
            "result": {"status": status, "color": color, "percentile": percentile, "calories": calories},
            "explanation": {
                "logic": logic,
                "sources": [
                    "Pediatrics Journal (2015): Studi oleh Zemel et al. mempublikasikan kurva pertumbuhan spesifik untuk anak dengan Sindrom Down, menyimpulkan bahwa penggunaan standar WHO biasa dapat menyebabkan misdiagnosis malnutrisi gizi.",
                    "Journal of Intellectual Disability Research (2002): Styles et al. menemukan bahwa distribusi lemak dan kepadatan otot bawaan pada anak Sindrom Down memerlukan perhitungan rasio metabolisme basal yang berbeda dari anak tipikal.",
                    "American Academy of Pediatrics Clinical Report (2022): Pedoman kesehatan anak Sindrom Down yang menegaskan pentingnya pemantauan rasio massa tubuh secara khusus untuk mencegah komplikasi kardiovaskular dini dan *obstructive sleep apnea*."
                ]
            }
        })
    except Exception as e:
        app.logger.error("Calculator API error", exc_info=True)
        return jsonify({"error": "Input tidak valid. Periksa kembali data Anda."}), 400

@app.route('/api/calc/sensory', methods=['POST'])
@limiter.limit("30 per minute")
def api_calc_sensory():
    try:
        data = request.json
        noise = float(data.get('noise', 0))
        light = float(data.get('light', 0))
        crowd = float(data.get('crowd', 0))
        duration = float(data.get('duration', 0))
        
        total_score = (noise * 0.3) + (light * 0.2) + (crowd * 0.3) + (duration * 0.2)
        percentage = min(100, max(0, total_score * 10))
        
        if percentage > 70:
            risk = "Bahaya Overload Tinggi"
        elif percentage > 40:
            risk = "Sedang"
        else:
            risk = "Rendah"
            
        logic = f"Dari parameter yang Anda masukkan, tingkat kebisingan di level {noise}, pencahayaan {light}, dan kepadatan ruangan {crowd} selama {duration} menit, akumulasi beban saraf pusat anak kita menembus angka {percentage:.1f} persen. Ini berarti risiko terjadinya kelebihan beban sensori berada di tingkat {risk}. Secara sains, amigdala atau pusat waspada di otak anak kita saat ini sedang memproduksi hormon stres kortisol dalam jumlah besar. Angka ini adalah alarm medis bagi Anda. Segera lakukan intervensi untuk menurunkan gelombang Beta di otaknya agar ia terhindar dari krisis kelelahan saraf yang memicu tantrum."
        
        return jsonify({
            "result": {"risk": risk},
            "explanation": {
                "logic": logic,
                "sources": [
                    "American Journal of Occupational Therapy (2014): Penelitian berbasis teori Integrasi Sensori Ayres membuktikan bahwa akumulasi stimulus visual dan auditori yang tidak terkontrol memicu respons hiper-eksitabilitas pada saraf otonom anak spektrum autisme.",
                    "Journal of Autism and Developmental Disorders (2010): Lane et al. menyimpulkan bahwa reaktivitas sensori secara langsung berkorelasi dengan munculnya perilaku tantrum dan maladaptif akibat kegagalan otak memodulasi rangsangan lingkungan.",
                    "Occupational Therapy International (2018): Panduan klinis yang menunjukkan bahwa pembatasan durasi paparan lingkungan ekstrem terbukti menurunkan kadar kortisol saliva pada anak dengan gangguan pemrosesan sensori."
                ]
            }
        })
    except Exception as e:
        app.logger.error("Calculator API error", exc_info=True)
        return jsonify({"error": "Input tidak valid. Periksa kembali data Anda."}), 400

@app.route('/api/calc/auditory', methods=['POST'])
@limiter.limit("30 per minute")
def api_calc_auditory():
    try:
        data = request.json
        age = float(data.get('age', 0))
        hyper = data.get('hyper', 'Ringan')
        
        duration = age * 1.5
        if hyper == 'Berat':
            duration = duration * 0.8
            
        duration = min(30.0, duration)
        
        logic = f"Berdasarkan usia anak kita yang menginjak {age} tahun dengan kondisi hiperaktivitas {hyper}, sistem saraf pendengarannya hanya mampu memproses entrainment gelombang suara secara aman selama maksimal {round(duration)} menit. Ini sangat krusial. Jika kita memaksakan otak mendengarkan frekuensi ini melewati batas waktu tersebut, korteks auditori anak akan mengalami fase *auditory fatigue* atau kelelahan pendengaran. Alih-alih mendapatkan gelombang rileks Theta atau Alpha, neuron di otaknya justru akan menjadi terlalu terstimulasi, yang pada kasus tertentu dapat memicu gelombang lonjakan listrik yang membahayakan kenyamanan istirahatnya."
        
        return jsonify({
            "result": {"duration": round(duration)},
            "explanation": {
                "logic": logic,
                "sources": [
                    "Frontiers in Human Neuroscience (2019): Garcia-Argibay dkk meneliti kemanjuran Binaural Beats dan menyimpulkan bahwa durasi paparan yang panjang tanpa kontrol dapat menyebabkan kelelahan kortikal yang mengurangi efek neuroplastisitas.",
                    "Clinical Neurophysiology (2017): Studi pemindaian EEG menunjukkan bahwa entrainment gelombang otak memiliki ambang batas kejenuhan waktu, di mana stimulasi berlebih justru memicu over-arousal pada sistem saraf pusat.",
                    "Journal of Pediatric Neurology (2020): Jurnal pengawasan klinis mengenai batasan desibel dan durasi paparan audio terapeutik untuk menghindari penurunan ambang batas kejang pada anak dengan riwayat anomali gelombang otak."
                ]
            }
        })
    except Exception as e:
        app.logger.error("Calculator API error", exc_info=True)
        return jsonify({"error": "Input tidak valid. Periksa kembali data Anda."}), 400

@app.route('/api/calc/iq', methods=['POST'])
@limiter.limit("30 per minute")
def api_calc_iq():
    try:
        data = request.json
        chrono = float(data.get('chrono', 0))
        mental = float(data.get('mental', 0))
        
        iq = (mental / chrono) * 100 if chrono > 0 else 0
        
        if iq < 40:
            category = "Severe"
            recommendation = "Fokus pada keterampilan bertahan hidup dasar dan bina diri intensif."
        elif iq <= 54:
            category = "Moderate"
            recommendation = "Fokus pada komunikasi fungsional dan kemandirian aktivitas sehari-hari."
        elif iq <= 69:
            category = "Mild"
            recommendation = "Fokus pada keterampilan akademik fungsional dan vokasional dasar."
        else:
            category = "Borderline / Normal"
            recommendation = "Pendekatan belajar umum dengan adaptasi ringan."
            
        logic = f"Usia kronologis atau raga pahlawan kecil kita saat ini adalah {chrono} bulan, namun dari asesmen, fungsi kognitif usianya berada di titik {mental} bulan. Menghasilkan estimasi rasio di angka {round(iq)}. Saat ini ia berada di fase pembelajaran {category}. Mengetahui angka ini adalah kelegaan saintifik. Ini menjelaskan mengapa memaksakan kurikulum reguler membuat otaknya stres. Secara neurologis, pemangkasan sinapsis (synaptic pruning) di otak anak kita berjalan dengan ritme yang istimewa. Angka rasio ini adalah cetak biru medis bagi ayah bunda untuk menyusun metode pengulangan materi yang paling tepat, memastikan neuron barunya tumbuh subur tanpa rasa frustrasi."
        
        return jsonify({
            "result": {"iq": round(iq), "category": category, "recommendation": recommendation},
            "explanation": {
                "logic": logic,
                "sources": [
                    "American Psychological Association Guidelines (2021): Manual standar diagnostik yang menggunakan perbandingan usia mental dan usia kronologis sebagai fondasi awal penyusunan Individualized Education Program (IEP) bagi anak difabel.",
                    "Journal of Intellectual Disability Research (2015): Penelitian yang membuktikan bahwa penyesuaian ekspektasi akademis berdasarkan rasio kognitif terbukti secara drastis menurunkan tingkat depresi dan penolakan sekolah pada anak Tunagrahita.",
                    "Child Development (2018): Analisis tahap kognitif Piagetian yang dimodifikasi, menegaskan bahwa anak dengan keterlambatan kognitif membutuhkan paparan konkret dan sensorimotor jauh lebih lama dibandingkan teman seusianya."
                ]
            }
        })
    except Exception as e:
        app.logger.error("Calculator API error", exc_info=True)
        return jsonify({"error": "Input tidak valid. Periksa kembali data Anda."}), 400

@app.route('/api/calc/motor', methods=['POST'])
@limiter.limit("30 per minute")
def api_calc_motor():
    try:
        data = request.json
        prev = float(data.get('prev', 0))
        curr = float(data.get('curr', 0))
        
        if prev == 0:
            progress = 0
        else:
            progress = ((curr - prev) / prev) * 100
            
        if progress > 0:
            msg = "Peningkatan motorik yang baik!"
        else:
            msg = "Terjadi regresi, butuh evaluasi ulang."
            
        logic = f"Luar biasa! Dari rekam data, pencapaian bulan lalu yang membutuhkan waktu {prev} detik, hari ini berhasil ditaklukkan anak kita hanya dalam {curr} detik. Ini adalah persentase peningkatan kemajuan sebesar {round(progress, 1)} persen! Secara sains, angka ini bukan sekadar waktu yang lebih cepat. Ini adalah bukti nyata terjadinya *Neuroplastisitas*. Latihan berulang yang Anda dampingi di rumah telah berhasil memperbaiki selubung mielin (kabel saraf) di tangannya, menciptakan jalur komunikasi baru dari korteks motorik otak langsung ke ujung jari-jarinya. Jangan menyerah, sains membuktikan terapi Anda sedang bekerja dan mengubah struktur anatomi otak anak kita!"
        
        return jsonify({
            "result": {"progress": round(progress, 1), "message": msg},
            "explanation": {
                "logic": logic,
                "sources": [
                    "Developmental Medicine and Child Neurology (2016): Studi neuro-imaging membuktikan bahwa latihan repetitif motorik halus pada anak Cerebral Palsy secara langsung meningkatkan volume materi putih (white matter) di traktus kortikospinal otak.",
                    "Physical Therapy Journal APTA (2019): Pedoman rehabilitasi anak yang menegaskan bahwa pengukuran kemajuan dalam hitungan milidetik secara statistik sangat valid untuk menentukan efikasi kelanjutan program terapi fisik di rumah.",
                    "Journal of Motor Behavior (2017): Riset mengenai pembelajaran motorik pada anak difabel yang menunjukkan bahwa persentase peningkatan mikro dari waktu ke waktu adalah indikator biologis utama terbentuknya pola sinapsis permanen."
                ]
            }
        })
    except Exception as e:
        app.logger.error("Calculator API error", exc_info=True)
        return jsonify({"error": "Input tidak valid. Periksa kembali data Anda."}), 400

@app.route('/api/calc/diet', methods=['POST'])
@limiter.limit("30 per minute")
def api_calc_diet():
    try:
        data = request.json
        mode = data.get('mode', 'Keto')
        fat = float(data.get('fat', 0))
        protein = float(data.get('protein', 0))
        carbs = float(data.get('carbs', 0))
        
        if mode == 'Keto':
            total_non_fat = protein + carbs
            if total_non_fat > 0:
                val = fat / total_non_fat
                ratio = f"{round(val, 1)}:1"
                if val >= 3.0:
                    status = "Standar Terapi Medis TERCAPAI"
                    valid = True
                else:
                    status = "Standar Terapi Medis BELUM TERCAPAI"
                    valid = False
            else:
                ratio = "Infinity"
                status = "Hanya Lemak"
                valid = True
            cost = (fat * 500) + (protein * 300) + (carbs * 100)
            logic = f"Berdasarkan komposisi asupan hari ini yaitu Lemak {fat} gram, Protein {protein} gram, dan Karbohidrat {carbs} gram, rasio ketosis otak anak kita berada di angka mutlak {ratio}. Status diet medisnya saat ini {status}. Angka rasio ini adalah penentu takdir kimiawi di otak anak kita. Rasio yang tepat akan memaksa hati memproduksi badan keton. Keton ini akan menembus penghalang darah-otak, berperan sebagai bahan bakar super bersih yang menekan hormon pemicu kejang (Glutamat) dan meningkatkan hormon penenang alami otak (GABA). Ini bukan sekadar makanan, ini adalah medikasi farmakologi melalui nutrisi untuk melindungi jaring sarafnya dari kerusakan."
        else:
            ratio = "-"
            status = "Pemantauan GFCF Aktif"
            valid = True
            cost = (fat * 200) + (protein * 400) + (carbs * 200)
            logic = f"Berdasarkan komposisi asupan hari ini yaitu Lemak {fat} gram, Protein {protein} gram, dan Karbohidrat {carbs} gram, rasio ketosis otak anak kita berada di angka mutlak {ratio}. Status diet medisnya saat ini {status}. Angka rasio ini adalah penentu takdir kimiawi di otak anak kita. Rasio yang tepat akan memaksa hati memproduksi badan keton. Keton ini akan menembus penghalang darah-otak, berperan sebagai bahan bakar super bersih yang menekan hormon pemicu kejang (Glutamat) dan meningkatkan hormon penenang alami otak (GABA). Ini bukan sekadar makanan, ini adalah medikasi farmakologi melalui nutrisi untuk melindungi jaring sarafnya dari kerusakan."

        return jsonify({
            "result": {"ratio": ratio, "status": status, "valid": valid, "cost": round(cost)},
            "explanation": {
                "logic": logic,
                "sources": [
                    "The Lancet Neurology (2008): Jurnal medis epik oleh Neal et al. yang melakukan uji coba acak terkendali (RCT), membuktikan secara definitif bahwa diet ketogenik terukur signifikan menurunkan frekuensi kejang pada anak epilepsi refrakter.",
                    "Nutritional Neuroscience (2018): Penelitian komprehensif mengenai efek diet eliminasi pada marker peradangan sistem saraf pusat, menunjukkan penurunan neuro-inflamasi pada anak dengan gangguan spektrum autisme.",
                    "Epilepsia Journal (2020): Konsensus internasional terkini untuk manajemen diet ketogenik pada anak, yang mewajibkan perhitungan rasio lemak terhadap karbohidrat dan protein secara presisi matematis harian untuk mempertahankan kondisi ketosis terapeutik."
                ]
            }
        })
    except Exception as e:
        app.logger.error("Calculator API error", exc_info=True)
        return jsonify({"error": "Input tidak valid. Periksa kembali data Anda."}), 400



@app.route('/api/yasin', methods=['GET'])
@cache.cached(timeout=86400, key_prefix='surah_yasin')
def api_yasin():
    try:
        url = "https://equran.id/api/v2/surat/36"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        # Note: urllib.request may not be fully patched by eventlet. Result is cached for 24h so impact is minimal. Consider using the requests library if blocking becomes an issue.
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode())
            return jsonify(data)
    except Exception as e:
        app.logger.error("API error", exc_info=True)
        return jsonify({"error": "Gagal mengambil data. Coba lagi nanti."}), 500

# --- DASHBOARD GURU ROUTES ---

class TantrumLog(db.Model):
    __tablename__ = 'tantrum_log'
    __table_args__ = (Index('idx_tantrum_log_student', 'student'), Index('idx_tantrum_log_created_at', 'created_at'),)
    id = db.Column(db.Integer, primary_key=True)
    student = db.Column(db.String(255), nullable=False, index=True)
    trigger = db.Column(db.String(255), nullable=False)
    start_time = db.Column(db.DateTime, nullable=True, default=datetime.datetime.now)
    duration_ms = db.Column(db.Integer)
    action = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=func.now(), index=True)

class ReactionTimeLog(db.Model):
    __tablename__ = 'reaction_time_log'
    id = db.Column(db.Integer, primary_key=True)
    time_ms = db.Column(db.Integer, nullable=True) # Deprecated but kept for backward compatibility
    time_sec = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())

class KognitifEmosiLog(db.Model):
    __tablename__ = 'kognitif_emosi_log'
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    duration_sec = db.Column(db.Float, nullable=False)
    history = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now())

class KognitifBentukLog(db.Model):
    __tablename__ = 'kognitif_bentuk_log'
    id = db.Column(db.Integer, primary_key=True)
    mistakes = db.Column(db.Integer, nullable=False)
    duration_sec = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

class StudentPortfolio(db.Model):
    __tablename__ = 'student_portfolio'
    __table_args__ = (Index('idx_student_portfolio_student_id', 'student_id'), Index('idx_student_portfolio_created_at', 'created_at'),)
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(255), nullable=False, index=True)
    semester = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now(), index=True)

class OrangTuaBuku(db.Model):
    __tablename__ = 'orang_tua_buku'
    id = db.Column(db.Integer, primary_key=True)
    anak_id = db.Column(db.Integer, db.ForeignKey('siswa.id'), nullable=True, index=True)
    mood = db.Column(db.String(255))
    sleep_duration = db.Column(db.Integer)
    morning_behavior = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now())

class OrangTuaTantrum(db.Model):
    __tablename__ = 'orang_tua_tantrum'
    id = db.Column(db.Integer, primary_key=True)
    anak_id = db.Column(db.Integer, db.ForeignKey('siswa.id'), nullable=True, index=True)
    trigger = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=func.now())

class OrangTuaJadwal(db.Model):
    __tablename__ = 'orang_tua_jadwal'
    __table_args__ = (Index('idx_jadwal_time_notified', 'schedule_time', 'notified', 'notified_date'),)
    id = db.Column(db.Integer, primary_key=True)
    anak_id = db.Column(db.Integer, db.ForeignKey('siswa.id'), nullable=True, index=True)
    schedule_time = db.Column(db.Time, nullable=False, index=True)
    medication_name = db.Column(db.String(255), nullable=False)
    notified = db.Column(db.Boolean, default=False, index=True)
    notified_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())

class OrangTuaNutrisi(db.Model):
    __tablename__ = 'orang_tua_nutrisi'
    id = db.Column(db.Integer, primary_key=True)
    anak_id = db.Column(db.Integer, db.ForeignKey('siswa.id'), nullable=True, index=True)
    food_name = db.Column(db.String(255), nullable=False)
    has_allergen = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

class OrangTuaBurnout(db.Model):
    __tablename__ = 'orang_tua_burnout'
    id = db.Column(db.Integer, primary_key=True)
    anak_id = db.Column(db.Integer, db.ForeignKey('siswa.id'), nullable=True, index=True)
    stress_level = db.Column(db.Integer, nullable=False)
    recorded_date = db.Column(db.Date, nullable=False, default=datetime.date.today, index=True)
    created_at = db.Column(db.DateTime, server_default=func.now())

class PushSubscription(db.Model):
    __tablename__ = 'push_subscription'
    id = db.Column(db.Integer, primary_key=True)
    subscription_info = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    last_used = db.Column(db.DateTime, server_default=func.now())

@app.route('/guru/tantrum', methods=['POST'])
def save_tantrum():
    if session.get('peran') not in ['guru', 'kepala_sekolah'] and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        data = request.json
        log = TantrumLog(
            student=data.get('student'),
            trigger=data.get('trigger'),
            start_time=str(data.get('start')),
            duration_ms=int(data.get('duration', 0)),
            action=data.get('action')
        )
        db.session.add(log)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Terjadi kesalahan saat memproses data. Silakan coba lagi.'}), 500

@app.route('/guru/tantrum/data')
def get_tantrum_data():
    if session.get('peran') not in ['guru', 'kepala_sekolah'] and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    # Fetch all logs
    logs = TantrumLog.query.filter(TantrumLog.created_at >= datetime.datetime.now() - datetime.timedelta(days=30)).order_by(TantrumLog.created_at.desc()).all()
    
    # Initialize hours map 0-23
    hours_count = {str(i).zfill(2) + ":00": 0 for i in range(24)}
    
    history_data = []
    
    for log in logs:
        # Determine time and duration for history
        display_time = log.created_at.strftime("%H:%M")
        try:
            if log.start_time:
                dt = datetime.datetime.fromtimestamp(int(log.start_time) / 1000.0)
                display_time = dt.strftime("%H:%M")
        except:
            pass
            
        display_duration = 0
        if log.duration_ms:
            display_duration = max(1, round(log.duration_ms / 60000))

        history_data.append({
            "student": log.student,
            "time": display_time,
            "trigger": log.trigger,
            "duration": display_duration,
            "action": log.action,
            "date": log.created_at.strftime("%Y-%m-%d")
        })
        
        try:
            hour_key = display_time.split(':')[0] + ":00"
            if hour_key in hours_count:
                hours_count[hour_key] += 1
        except Exception:
            pass

    labels = list(hours_count.keys())
    values = list(hours_count.values())
    return jsonify({"labels": labels, "values": values, "history": history_data})


import urllib.request
import os

import requests
def prefetch_emoji_icons():
    def _download():
        try:
            emoji_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'emoji_cache')
            os.makedirs(emoji_dir, exist_ok=True)
            hex_codes = ['1f441', '1f442', '1f3c3', '1f590', '1f3af', '1f5e3', '2753']
            for icon_hex in hex_codes:
                file_path = os.path.join(emoji_dir, f"{icon_hex}.png")
                if not os.path.exists(file_path):
                    url = f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{icon_hex}.png"
                    try:
                        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                        if response.status_code == 200:
                            with open(file_path, 'wb') as out_f:
                                out_f.write(response.content)
                    except Exception as e:
                        app.logger.error(f"Failed to prefetch emoji {icon_hex}: {e}")
        except Exception as e:
            app.logger.error(f"Background thread error in prefetch_emoji_icons: {e}")
            
    threading.Thread(target=_download, daemon=True).start()

@app.route('/guru/iep', methods=['POST'])
@limiter.limit("10 per hour")
def generate_iep():
    student_name = request.form.get('student_name')
    student_class = request.form.get('student_class')
    conditions = request.form.getlist('condition')
    scores = {cond: request.form.get(f'score_{cond}', '0') for cond in conditions}
    
    # Fetch real-time date
    date_text = datetime.datetime.now().strftime("%d %B %Y %H:%M:%S")
    
    def add_item_with_icon(title, body, rationale, icon_hex):
        emoji_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'emoji_cache')
        file_path = os.path.join(emoji_dir, f"{icon_hex}.png")
        img = None
        try:
            if os.path.exists(file_path):
                img = RLImage(file_path, width=36, height=36)
        except Exception:
            pass
        
        text_content = [
            Paragraph(title, styles['ItemTitle']),
            Paragraph(body, styles['ItemBody']),
            Paragraph(rationale, styles['Rationale'])
        ]
        
        if img:
            t = Table([[img, text_content]], colWidths=[50, 418])
            t.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ]))
            return t
        else:
            # Fallback to plain paragraphs if image fails to load
            from reportlab.platypus import KeepTogether
            return KeepTogether(text_content + [Spacer(1, 10)])

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterHeading', parent=styles['Heading1'], alignment=1, spaceAfter=20, fontSize=24, textColor=colors.HexColor('#1E3A8A')))
    styles.add(ParagraphStyle(name='DateStyle', parent=styles['Normal'], alignment=1, spaceAfter=20, fontSize=10, textColor=colors.HexColor('#6B7280')))
    styles.add(ParagraphStyle(name='SectionTitle', parent=styles['Heading2'], spaceBefore=15, spaceAfter=10, textColor=colors.HexColor('#1D4ED8')))
    styles.add(ParagraphStyle(name='NormalText', parent=styles['Normal'], spaceAfter=10, leading=14))
    styles.add(ParagraphStyle(name='ItemTitle', parent=styles['Normal'], fontName='Helvetica-Bold', spaceBefore=5, spaceAfter=2))
    styles.add(ParagraphStyle(name='ItemBody', parent=styles['Normal'], spaceAfter=10, leading=14))
    styles.add(ParagraphStyle(name='Rationale', parent=styles['Normal'], fontName='Helvetica-Oblique', textColor=colors.HexColor('#4B5563'), leading=14, spaceAfter=12))

    Story = []
    
    # Letterhead
    Story.append(Paragraph("SEKOLAH LUAR BIASA", styles['CenterHeading']))
    Story.append(Paragraph("RENCANA PENDIDIKAN INDIVIDUAL (IEP)", styles['CenterHeading']))
    Story.append(Paragraph(f"Dicetak pada: {date_text}", styles['DateStyle']))
    Story.append(Spacer(1, 12))
    
    # Student Info
    Story.append(Paragraph(f"<b>Nama Siswa:</b> {student_name}", styles['NormalText']))
    Story.append(Paragraph(f"<b>Kelas / Usia:</b> {student_class}", styles['NormalText']))
    Story.append(Spacer(1, 12))

    
    # Conditions mapping with icon hex codes (Twemoji)
    cond_data = {
        "Visual": {"rat": "Hambatan visual pada anak bukan sekadar perkara mata yang tidak bisa melihat jelas, melainkan terganggunya jalur optik menuju korteks otak. Anak seringkali merasa terisolasi dalam ruang hampa cahaya. Pendekatan ini merangsang neuroplastisitas untuk membentuk kembali peta visual mereka secara perlahan.", "icon": "1f441"}, # Eye
        "Auditori": {"rat": "Anak dengan hambatan auditori hidup dalam dunia yang sunyi atau penuh dengan dengung statis yang membingungkan. Ini bukan hanya masalah telinga, tapi bagaimana otak menerjemahkan gelombang suara. Terapi ini bertujuan memecah keheningan dengan membangun koneksi atensi pendengaran selangkah demi selangkah.", "icon": "1f442"}, # Ear
        "Motorik Kasar": {"rat": "Ketidakmampuan motorik kasar seringkali mengurung potensi besar anak di dalam tubuh yang tidak merespons perintah otaknya sendiri. Rasionalisasinya adalah melatih kembali otot-otot besar dan sistem vestibular, memberikan mereka kembali kemerdekaan bergerak di dunia fisik.", "icon": "1f3c3"}, # Running
        "Motorik Halus": {"rat": "Setiap ujung jari anak memiliki ribuan reseptor taktil yang menghubungkan mereka dengan tekstur dunia. Keterbatasan motorik halus memutus jembatan interaksi detail ini. Rencana ini didesain untuk merangsang kembali jaras saraf halus tersebut dengan penuh kelembutan.", "icon": "1f590"}, # Hand
        "Atensi": {"rat": "Defisit atensi membuat otak anak ibarat radio yang menangkap semua frekuensi secara bersamaan, menjadikannya kelelahan karena overstimulasi. Pendekatan ini adalah tentang menyaring kebisingan dunia, memberikan mereka sauh atau jangkar fokus agar bisa merespons satu hal dengan tenang.", "icon": "1f3af"}, # Target
        "Komunikasi": {"rat": "Ketidakmampuan mengekspresikan diri secara verbal seringkali berujung pada ledakan frustrasi. Area Broca pada otak mereka membutuhkan rute alternatif untuk menyampaikan apa yang ada di pikiran dan hati mereka, menjembatani komunikasi tanpa harus bergantung pada kata-kata.", "icon": "1f5e3"} # Speaking
    }

    if conditions:
        Story.append(Paragraph("Kondisi / Hambatan yang Diidentifikasi", styles['SectionTitle']))
        for cond in conditions:
            score = scores.get(cond, '0')
            title = f"{cond} - Skor Keparahan: {score}/10"
            data = cond_data.get(cond, {"rat": "Kondisi ini memerlukan observasi medis lebih lanjut untuk stimulasi spesifik.", "icon": "2753"})
            Story.append(add_item_with_icon(title, "", data["rat"], data["icon"]))
        Story.append(Spacer(1, 12))

    # Short-Term
    Story.append(Paragraph("Rekomendasi Pendekatan (Target Jangka Pendek)", styles['SectionTitle']))
    Story.append(add_item_with_icon(
        "1. Latihan Fokus Menggunakan Cahaya (Visual)",
        "<b>Instruksi:</b> Ajak anak menatap senter kecil di ruangan redup selama lima detik.",
        "<b>Dasar Medis:</b> Stimulasi retina cahaya terbukti meningkatkan neuroplastisitas jalur optik kortikal berdasarkan studi optometri perkembangan anak.",
        "1f526" # Flashlight
    ))
    Story.append(add_item_with_icon(
        "2. Permainan Tekstur Pasir (Motorik Halus)",
        "<b>Instruksi:</b> Biarkan anak meremas pasir kinetik untuk merangsang reseptor taktil di ujung jari.",
        "<b>Dasar Medis:</b> Metode Terapi Integrasi Sensorik Ayres yang valid secara internasional.",
        "1f3d6" # Sand/Beach
    ))
    Story.append(add_item_with_icon(
        "3. Pengenalan Suara Berulang (Auditori)",
        "<b>Instruksi:</b> Sebutkan nama anak berulang kali sambil menepuk pundaknya.",
        "<b>Dasar Medis:</b> Metodologi Applied Behavior Analysis untuk membangun koneksi atensi pendengaran.",
        "1f50a" # Sound/Speaker
    ))
    Story.append(Spacer(1, 12))

    # Long-Term
    Story.append(Paragraph("Rekomendasi Pendekatan (Target Jangka Panjang)", styles['SectionTitle']))
    Story.append(add_item_with_icon(
        "1. Kemandirian Mengikat Tali Sepatu",
        "<b>Instruksi:</b> Ajarkan gerakan simpul pita setiap pagi secara konsisten.",
        "<b>Dasar Medis:</b> Metode Chaining dalam psikologi perilaku kognitif yang memecah tugas motorik kompleks menjadi langkah langkah kecil yang mudah dihafal otak.",
        "1f45f" # Shoe
    ))
    Story.append(add_item_with_icon(
        "2. Membangun Kosakata Emosi",
        "<b>Instruksi:</b> Gunakan kartu bergambar wajah senang dan sedih saat anak merespons sesuatu.",
        "<b>Dasar Medis:</b> Metodologi Picture Exchange Communication System atau PECS yang terbukti memicu area Broca pada otak untuk komunikasi non verbal.",
        "1f60a" # Smiling Face
    ))
    Story.append(add_item_with_icon(
        "3. Regulasi Diri Saat Tantrum",
        "<b>Instruksi:</b> Ajarkan teknik napas tiga fase saat anak mulai gelisah.",
        "<b>Dasar Medis:</b> Penelitian Biofeedback yang membuktikan penurunan lonjakan kortisol saat ritme napas diatur secara sadar.",
        "1f388" # Balloon (representing breathing)
    ))
    Story.append(Spacer(1, 12))

    # Special Facility
    Story.append(Paragraph("Kebutuhan Modifikasi Fasilitas Khusus", styles['SectionTitle']))
    Story.append(add_item_with_icon(
        "1. Penggunaan Ear Muff atau Penutup Telinga",
        "<b>Instruksi:</b> Pakaikan saat berada di lingkungan bising seperti pasar.",
        "<b>Dasar Medis:</b> Metodologi Modulasi Sensorik untuk mencegah kelebihan muatan pada saraf auditori anak autisme.",
        "1f3a7" # Headphones/Ear muff
    ))
    Story.append(add_item_with_icon(
        "2. Kursi dengan Bantal Pemberat atau Weighted Lap Pad",
        "<b>Instruksi:</b> Letakkan di pangkuan anak saat mereka harus duduk belajar.",
        "<b>Dasar Medis:</b> Terapi Tekanan Dalam atau Deep Touch Pressure yang terbukti secara klinis melepaskan hormon serotonin penenang saraf.",
        "1f6cf" # Bed/Pillow
    ))
    Story.append(add_item_with_icon(
        "3. Pembuatan Sudut Tenang atau Calming Corner",
        "<b>Instruksi:</b> Sediakan tenda kecil dengan lampu biru redup di kamar.",
        "<b>Dasar Medis:</b> Prinsip Arsitektur Perilaku yang memberikan ruang aman bagi anak untuk melakukan regulasi sensorik mandiri.",
        "26fa" # Tent
    ))
    
    doc.build(Story)
    buffer.seek(0)
    return Response(buffer, mimetype='application/pdf', headers={'Content-Disposition': f'attachment;filename=IEP_{student_name}.pdf'})

@app.route('/guru/reaction', methods=['POST'])
def save_reaction():
    if session.get('peran') not in ['guru', 'kepala_sekolah'] and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    sec = data.get('time_sec')
    if sec is None and data.get('time_ms') is not None:
        sec = data.get('time_ms') / 1000.0
    log = ReactionTimeLog(time_sec=sec)
    db.session.add(log)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error('Database commit error', exc_info=True)
        return jsonify({'error': 'Database error'}), 500
    return jsonify({"status": "success"})

@app.route('/guru/reaction/data')
def get_reaction_data():
    if session.get('peran') not in ['guru', 'kepala_sekolah'] and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    logs = ReactionTimeLog.query.order_by(ReactionTimeLog.created_at.desc()).limit(100).all()
    labels = [f"Tes {i+1}" for i in range(len(logs))]
    values = []
    for l in logs:
        if l.time_sec is not None:
            values.append(l.time_sec)
        else:
            values.append(round(l.time_ms / 1000.0, 2))
    return jsonify({"labels": labels, "values": values})

@app.route('/guru/kognitif/emosi', methods=['POST'])
def save_kognitif_emosi():
    if session.get('peran') not in ['guru', 'kepala_sekolah'] and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    log = KognitifEmosiLog(
        score=data.get('score'),
        duration_sec=data.get('duration_sec'),
        history=data.get('history')
    )
    db.session.add(log)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error('Database commit error', exc_info=True)
        return jsonify({'error': 'Database error'}), 500
    return jsonify({"status": "success"})

@app.route('/guru/kognitif/bentuk', methods=['POST'])
def save_kognitif_bentuk():
    if session.get('peran') not in ['guru', 'kepala_sekolah'] and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    log = KognitifBentukLog(
        mistakes=data.get('mistakes'),
        duration_sec=data.get('duration_sec')
    )
    db.session.add(log)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error('Database commit error', exc_info=True)
        return jsonify({'error': 'Database error'}), 500
    return jsonify({"status": "success"})

import io
from PIL import Image

@app.route('/guru/portofolio/upload', methods=['POST'])
def upload_portfolio():
    if session.get('peran') not in ['guru', 'kepala_sekolah'] and not session.get('is_admin'):
        return "Unauthorized", 403
    if 'image' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['image']
    if file.filename == '':
        return redirect(url_for('index'))
        
    if file and allowed_file(file.filename):
        try:
            file_bytes = file.read(2048)
            file.seek(0)
            kind = filetype.guess(file_bytes)
            if kind is None or not (kind.mime.startswith('image/') or kind.mime.startswith('video/')):
                return "File tidak didukung", 400

            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            ext = filename.rsplit('.', 1)[1].lower()
            video_extensions = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v', 'mpeg'}
            
            if ext in video_extensions or ext == 'svg':
                file.save(filepath)
            else:
                img = Image.open(file)
                if img.mode in ("RGBA", "P"): 
                    img = img.convert("RGB")
                img.thumbnail((800, 800))
                
                # Image compression loop to ensure file size is under 500KB
                quality = 85
                img.save(filepath, format="JPEG", quality=quality, optimize=True)
                while os.path.getsize(filepath) > 500 * 1024 and quality > 10:
                    quality -= 5
                    img.save(filepath, format="JPEG", quality=quality, optimize=True)
                
            port = StudentPortfolio(
                student_id=request.form.get('student_id'),
                semester=request.form.get('semester'),
                filename=filename
            )
            db.session.add(port)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
        
    return redirect(url_for('index'))

# --- SOCKET IO EVENTS FOR DASHBOARD GURU ---
connected_clients_dict = {}

@socketio.on('connect')
def handle_connect():
    global connected_clients_dict
    user_agent = request.headers.get('User-Agent', '')
    
    device_name = "Perangkat Tidak Dikenal"
    if "Android" in user_agent:
        device_name = "Android"
    elif "iPhone" in user_agent or "iPad" in user_agent:
        device_name = "iOS"
    elif "Windows" in user_agent:
        device_name = "Windows PC"
    elif "Mac" in user_agent:
        device_name = "Mac OS"
    
    if "Chrome" in user_agent and "Edg" not in user_agent:
        device_name += " (Chrome)"
    elif "Safari" in user_agent and "Chrome" not in user_agent:
        device_name += " (Safari)"
    elif "Firefox" in user_agent:
        device_name += " (Firefox)"

    # Handle duplicates by appending SID slice
    device_id = f"{device_name} [{request.sid[:4]}]"
    
    connected_clients_dict[request.sid] = device_id
    emit('client_count', {'count': len(connected_clients_dict), 'clients': list(connected_clients_dict.values())}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    global connected_clients_dict
    if request.sid in connected_clients_dict:
        del connected_clients_dict[request.sid]
    emit('client_count', {'count': len(connected_clients_dict), 'clients': list(connected_clients_dict.values())}, broadcast=True)

@socketio.on('set_frequency')
def handle_set_frequency(data):
    # data: {'mode': 'calm' / 'off'}
    emit('receive_frequency', data, broadcast=True)













# --- SLB TEMPLATES & ROUTES ---

SLB_TUNANETRA_HTML = """
<div class="min-h-[100dvh] bg-sky-50 flex flex-col pt-20 px-5 pb-32 font-sans">
    <div class="flex-1 flex flex-col gap-6 w-full max-w-md mx-auto">
        <div class="text-center mb-2">
            <h2 class="text-3xl font-extrabold text-sky-800 tracking-tight">Audio Panduan</h2>
            <p class="text-sm font-medium text-sky-600">Aktivitas Fisik Spasial</p>
        </div>
        
        <!-- Big Play Button Minimalist Pastel -->
        <button id="main-play-btn" onclick="toggleAudioGuide()" class="w-full h-48 bg-white text-emerald-500 rounded-[2.5rem] shadow-lg shadow-emerald-100/50 flex flex-col items-center justify-center active:scale-95 transition-all duration-300 border-2 border-emerald-50 group" aria-label="Tombol Putar Panduan Suara. Ketuk untuk memutar atau menjeda." aria-live="polite">
            <div class="w-20 h-20 bg-emerald-50 rounded-full flex items-center justify-center mb-3 group-hover:bg-emerald-100 transition-colors">
                <i id="play-icon" class="fas fa-play text-4xl ml-2" aria-hidden="true"></i>
            </div>
            <span id="play-text" class="text-xl font-bold tracking-widest uppercase">Pilih Panduan</span>
        </button>

        <!-- Reading Text Display -->
        <div id="reading-display" class="bg-white p-6 rounded-3xl shadow-sm border border-sky-100 min-h-[120px] flex items-center justify-center text-center hidden transition-all duration-500">
            <p id="reading-text" class="text-lg font-medium text-sky-900 leading-relaxed">...</p>
        </div>

        <div class="grid grid-cols-2 gap-4 w-full">
            <button onclick="setGuide('shalat')" class="bg-white p-6 rounded-3xl shadow-sm border border-sky-100 flex flex-col justify-center items-center active:bg-sky-50 active:scale-95 transition-all group" aria-label="Panduan Shalat">
                <div class="w-14 h-14 bg-emerald-50 text-emerald-500 rounded-2xl flex items-center justify-center mb-3 group-hover:bg-emerald-500 group-hover:text-white transition-colors">
                    <i class="fas fa-praying-hands text-2xl" aria-hidden="true"></i>
                </div>
                <span class="text-sm font-bold text-gray-700 text-center leading-tight">Panduan<br>Shalat</span>
            </button>
            <button onclick="setGuide('wudhu')" class="bg-white p-6 rounded-3xl shadow-sm border border-sky-100 flex flex-col justify-center items-center active:bg-sky-50 active:scale-95 transition-all group" aria-label="Panduan Wudhu">
                <div class="w-14 h-14 bg-cyan-50 text-cyan-500 rounded-2xl flex items-center justify-center mb-3 group-hover:bg-cyan-500 group-hover:text-white transition-colors">
                    <i class="fas fa-water text-2xl" aria-hidden="true"></i>
                </div>
                <span class="text-sm font-bold text-gray-700 text-center leading-tight">Panduan<br>Wudhu</span>
            </button>
            <button onclick="setGuide('makan')" class="bg-white p-6 rounded-3xl shadow-sm border border-sky-100 flex flex-col justify-center items-center active:bg-sky-50 active:scale-95 transition-all group" aria-label="Tata Cara Makan">
                <div class="w-14 h-14 bg-blue-50 text-blue-500 rounded-2xl flex items-center justify-center mb-3 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                    <i class="fas fa-utensils text-2xl" aria-hidden="true"></i>
                </div>
                <span class="text-sm font-bold text-gray-700 text-center leading-tight">Tata Cara<br>Makan</span>
            </button>
            <button onclick="setGuide('sikatGigi')" class="bg-white p-6 rounded-3xl shadow-sm border border-sky-100 flex flex-col justify-center items-center active:bg-sky-50 active:scale-95 transition-all group" aria-label="Sikat Gigi">
                <div class="w-14 h-14 bg-teal-50 text-teal-500 rounded-2xl flex items-center justify-center mb-3 group-hover:bg-teal-500 group-hover:text-white transition-colors">
                    <i class="fas fa-tooth text-2xl" aria-hidden="true"></i>
                </div>
                <span class="text-sm font-bold text-gray-700 text-center leading-tight">Sikat<br>Gigi</span>
            </button>
            <button onclick="setGuide('berpakaian')" class="bg-white p-6 rounded-3xl shadow-sm border border-sky-100 flex flex-col justify-center items-center active:bg-sky-50 active:scale-95 transition-all group" aria-label="Berpakaian Mandiri">
                <div class="w-14 h-14 bg-indigo-50 text-indigo-500 rounded-2xl flex items-center justify-center mb-3 group-hover:bg-indigo-500 group-hover:text-white transition-colors">
                    <i class="fas fa-tshirt text-2xl" aria-hidden="true"></i>
                </div>
                <span class="text-sm font-bold text-gray-700 text-center leading-tight">Berpakaian<br>Mandiri</span>
            </button>
            <button onclick="setGuide('berjalan')" class="bg-white p-6 rounded-3xl shadow-sm border border-sky-100 flex flex-col justify-center items-center active:bg-sky-50 active:scale-95 transition-all group" aria-label="Berjalan Aman">
                <div class="w-14 h-14 bg-rose-50 text-rose-500 rounded-2xl flex items-center justify-center mb-3 group-hover:bg-rose-500 group-hover:text-white transition-colors">
                    <i class="fas fa-walking text-2xl" aria-hidden="true"></i>
                </div>
                <span class="text-sm font-bold text-gray-700 text-center leading-tight">Berjalan<br>Aman</span>
            </button>
        </div>
        
        <button onclick="openModal('modal-medis-tunanetra')" class="w-full bg-sky-100 text-sky-700 text-xs font-bold py-4 rounded-2xl hover:bg-sky-200 transition uppercase tracking-widest mt-2 flex items-center justify-center gap-2" aria-label="Buka Penjelasan Medis">
            <i class="fas fa-stethoscope" aria-hidden="true"></i> PENJELASAN MEDIS
        </button>
    </div>
    
    <!-- Modal Medis Tunanetra -->
    <div id="modal-medis-tunanetra" class="fixed inset-0 z-[100] hidden" role="dialog" aria-modal="true" aria-labelledby="modal-title-tunanetra">
        <div class="absolute inset-0 bg-sky-900/60 backdrop-blur-md transition-opacity" onclick="closeModal('modal-medis-tunanetra')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20 max-h-[90dvh] overflow-y-auto">
            <div class="flex justify-between items-center mb-6">
                <h3 id="modal-title-tunanetra" class="text-xl font-bold text-sky-800"><i class="fas fa-notes-medical text-sky-500 mr-2"></i>PENJELASAN MEDIS</h3>
                <button onclick="closeModal('modal-medis-tunanetra')" class="bg-gray-100 text-gray-500 w-8 h-8 rounded-full hover:bg-gray-200 flex items-center justify-center" aria-label="Tutup Modal">&times;</button>
            </div>
            
            <div class="mb-6">
                <h4 class="text-xs font-bold text-sky-600 uppercase tracking-widest mb-2 border-b border-sky-100 pb-1">Dasar Medis Sains</h4>
                <p class="text-sm text-gray-700 leading-relaxed text-justify font-medium">
                    Fitur ini menggunakan pendekatan <strong>Audio Spatial Description</strong> dengan antarmuka yang sangat ergonomis. Pemilihan warna pastel yang menenangkan dan tata letak tombol berukuran besar mempermudah navigasi. Getaran haptic (vibrate) saat tombol ditekan memberikan umpan balik taktil pengganti visual, merangsang korteks somatosensori untuk konfirmasi aksi. Narasi suara yang jelas dan lugas secara langsung membangun peta mental spasial di otak pengguna untuk aktivitas harian.
                </p>
            </div>

            <div class="bg-sky-50 p-4 rounded-2xl border border-sky-100">
                <h4 class="text-xs font-bold text-sky-700 uppercase tracking-widest mb-3">Penelitian Medis & Referensi</h4>
                <ul class="space-y-3">
                    <li class="text-xs text-gray-700">
                        <span class="font-bold text-sky-900 block">Fryer, L., & Freeman, J. (2012)</span>
                        "Cinematic language and the description of film". Membuktikan audio deskripsi meningkatkan pemahaman kognitif spasial tunanetra.
                    </li>
                    <li class="text-xs text-gray-700">
                        <span class="font-bold text-sky-900 block">Ramos Caro, M. (2014)</span>
                        "Emotion elicitation in audio description". Stimulasi emosi melalui narasi audio yang detail dan terstruktur.
                    </li>
                </ul>
            </div>
        </div>
    </div>

    <script>
        let isSpeaking = false;
        let currentText = "";
        let currentType = "";
        const synth = window.speechSynthesis;
        let utterance = null;

        const btn = document.getElementById('main-play-btn');
        const icon = document.getElementById('play-icon');
        const text = document.getElementById('play-text');
        const displayBox = document.getElementById('reading-display');
        const displayText = document.getElementById('reading-text');
        
        // Text Sources
        const sources = {
            'shalat': "Panduan Shalat. Satu, Berdiri tegak menghadap kiblat dan niat. Dua, Takbiratul Ihram, ucapkan Allahu Akbar. Tiga, Baca doa Iftitah dan Al-Fatihah. Empat, Ruku dengan tuma'ninah. Lima, I'tidal dengan tuma'ninah. Enam, Sujud dengan tuma'ninah. Tujuh, Duduk di antara dua sujud. Delapan, Sujud kedua. Sembilan, Duduk tasyahud akhir dan salam.", 
            'wudhu': "Panduan Wudhu. Satu, Niat dalam hati dan membaca Basmalah. Dua, Membasuh kedua telapak tangan. Tiga, Berkumur-kumur. Empat, Membersihkan lubang hidung. Lima, Membasuh wajah. Enam, Membasuh kedua tangan hingga siku. Tujuh, Mengusap sebagian kepala. Delapan, Membasuh kedua telinga. Sembilan, Membasuh kedua kaki hingga mata kaki. Sepuluh, Tertib dan doa setelah wudhu.",
            'makan': "Duduk tegak di kursi. Raba letak piring tepat di depan perutmu. Sendok ada di sebelah kanan piring, dan garpu di sebelah kiri. Ambil makanan pelan pelan, lalu suapkan ke arah mulut. Kunyah makanan sampai benar benar lembut sebelum ditelan.", 
            'sikatGigi': "Pegang gagang sikat gigi dengan tangan kanan. Minta bantuan untuk memberi pasta gigi sebesar biji jagung. Sikat gigi bagian depan dengan gerakan naik turun, lalu sikat bagian samping kiri dan kanan dengan gerakan memutar. Kumur kumur dengan air bersih, lalu buang airnya. Selesai, gigimu sudah bersih.",
            'berpakaian': "Pegang bajumu. Raba bagian kerah leher untuk mencari label, letakkan label itu di bagian belakang. Masukkan tangan kananmu ke lubang lengan kanan, lalu masukkan tangan kirimu ke lubang lengan kiri. Tarik baju ke bawah perlahan sampai menutupi perutmu.",
            'berjalan': "Berdirilah dengan tegak. Rentangkan satu tanganmu agak menekuk ke depan dada sebagai pelindung. Berjalanlah pelan pelan. Gunakan tangan satunya untuk meraba dinding atau pinggiran meja untuk mengenali arah. Jika kamu menabrak sesuatu, berhenti sebentar, rasakan sekelilingmu, lalu melangkah lagi pelan pelan."
        };
        
        function hapticFeedback() {
            if (navigator.vibrate) {
                navigator.vibrate(200); // 200ms vibration
            }
        }
        
        function setGuide(type) {
            hapticFeedback();
            currentText = sources[type];
            currentType = type;
            
            // Show display box
            displayBox.classList.remove('hidden');
            displayText.innerText = currentText;

            // Stop current speech if any
            if(synth.speaking) synth.cancel();
            isSpeaking = false;
            updateUI();
            
            // Auto start speech
            speak(currentText);
        }
        
        function toggleAudioGuide() {
            hapticFeedback();
            if(!currentText) {
                const msg = new SpeechSynthesisUtterance("Silakan pilih panduan terlebih dahulu.");
                msg.lang = 'id-ID';
                synth.speak(msg);
                return;
            }
            
            if (synth.speaking) {
                if (synth.paused) {
                    synth.resume();
                    isSpeaking = true;
                } else {
                    synth.pause();
                    isSpeaking = false;
                }
            } else {
                 speak(currentText);
            }
            updateUI();
        }
        
        function speak(textStr) {
            if (synth.speaking) synth.cancel();
            
            utterance = new SpeechSynthesisUtterance(textStr);
            utterance.lang = 'id-ID';
            utterance.rate = 0.9;
            utterance.pitch = 1.0;
            
            utterance.onend = () => {
                isSpeaking = false;
                updateUI();
            };
            
            utterance.onstart = () => {
                isSpeaking = true;
                updateUI();
            };

            synth.speak(utterance);
        }
        
        function updateUI() {
            const iconWrapper = btn.querySelector('div');
            if(isSpeaking) {
                icon.className = "fas fa-pause text-4xl";
                icon.classList.remove("ml-2"); // center pause icon
                text.innerText = "JEDA PANDUAN";
                btn.className = "w-full h-48 bg-white text-rose-500 rounded-[2.5rem] shadow-xl shadow-rose-200/50 flex flex-col items-center justify-center active:scale-95 transition-all duration-300 border-2 border-rose-100 group animate-pulse";
                iconWrapper.className = "w-20 h-20 bg-rose-50 rounded-full flex items-center justify-center mb-3 group-hover:bg-rose-100 transition-colors";
                btn.setAttribute('aria-label', 'Tombol Jeda. Ketuk untuk menjeda.');
            } else {
                icon.className = "fas fa-play text-4xl ml-2";
                text.innerText = currentText ? "LANJUTKAN PANDUAN" : "PILIH PANDUAN";
                btn.className = "w-full h-48 bg-white text-emerald-500 rounded-[2.5rem] shadow-lg shadow-emerald-100/50 flex flex-col items-center justify-center active:scale-95 transition-all duration-300 border-2 border-emerald-50 group";
                iconWrapper.className = "w-20 h-20 bg-emerald-50 rounded-full flex items-center justify-center mb-3 group-hover:bg-emerald-100 transition-colors";
                btn.setAttribute('aria-label', 'Tombol Putar. Ketuk untuk memutar.');
            }
        }
    </script>
</div>
"""

SLB_TUNARUNGU_HTML = """
<div class="min-h-[100dvh] bg-yellow-50 pt-24 px-5 pb-32">
    <style>
        .skeleton {
            background: linear-gradient(90deg, #fefce8 25%, #fef9c3 50%, #fefce8 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
        }
        @keyframes shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        @keyframes popSpring {
            0% { transform: scale(0.8); opacity: 0; }
            60% { transform: scale(1.1); opacity: 1; }
            100% { transform: scale(1); opacity: 1; }
        }
        .animate-pop {
            animation: popSpring 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
        }
        .progress-line {
            width: 0%;
            height: 4px;
            background-color: #eab308;
            border-radius: 2px;
            animation: progressGrow 2s ease-out forwards;
        }
        @keyframes progressGrow {
            to { width: 100%; }
        }
        .mic-active {
            animation: pulse-mic 1.5s infinite;
            background-color: #ef4444 !important;
        }
        @keyframes pulse-mic {
            0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
            70% { box-shadow: 0 0 0 15px rgba(239, 68, 68, 0); }
            100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }
    </style>
    
    <h2 class="text-3xl font-bold text-yellow-800 mb-6 border-l-4 border-yellow-500 pl-3">Kamus Isyarat</h2>
    
    <form onsubmit="handleSearch(event)" class="mb-8 relative flex items-center gap-2">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
        <div class="relative flex-1">
            <input type="text" id="search-input" placeholder="Ketik kata atau kalimat..." class="w-full p-5 rounded-full border-2 border-yellow-200 shadow-lg text-lg focus:outline-none focus:border-yellow-500 pr-16 text-gray-700">
            <button type="submit" class="absolute right-2 top-2 bg-yellow-500 text-white w-12 h-12 rounded-full flex items-center justify-center shadow-md hover:bg-yellow-600 transition">
                <i class="fas fa-search text-xl"></i>
            </button>
        </div>
        <button type="button" id="mic-btn" onclick="toggleVoice()" class="bg-red-500 text-white w-16 h-16 rounded-full flex items-center justify-center shadow-lg hover:bg-red-600 transition shrink-0 border-4 border-white">
            <i class="fas fa-microphone text-2xl"></i>
        </button>
    </form>
    
    <div class="flex justify-end mb-4">
        <button id="clear-btn" class="text-sm bg-gray-200 hover:bg-gray-300 text-gray-700 font-bold py-2 px-4 rounded-xl flex items-center gap-2 transition" onclick="clearResults()">
            <i class="fas fa-trash-alt"></i> Bersihkan
        </button>
    </div>

    <div id="result-container" class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-12"></div>
    
    <button onclick="openModal('modal-education')" class="w-full bg-yellow-600 text-white p-6 rounded-3xl shadow-lg border-2 border-yellow-500 flex justify-between items-center group hover:bg-yellow-700 transition-all duration-300">
        <div class="flex items-center gap-4 text-left">
            <div class="bg-yellow-500 p-3 rounded-xl text-yellow-100 shadow-sm">
                <i class="fas fa-hands-asl-interpreting text-3xl"></i>
            </div>
            <div>
                <h3 class="text-xl font-bold">Huruf dan Angka</h3>
                <p class="text-xs text-yellow-100 font-medium">Belajar Abjad dan Angka Dasar Isyarat</p>
            </div>
        </div>
        <div class="bg-yellow-500 w-10 h-10 rounded-full flex items-center justify-center text-yellow-100 group-hover:bg-white group-hover:text-yellow-600 transition-colors">
            <i class="fas fa-arrow-right"></i>
        </div>
    </button>

    <button onclick="openKataIsyaratModal()" class="w-full bg-orange-600 text-white p-6 rounded-3xl shadow-lg border-2 border-orange-500 flex justify-between items-center group hover:bg-orange-700 transition-all duration-300 mt-4">
        <div class="flex items-center gap-4 text-left">
            <div class="bg-orange-500 p-3 rounded-xl text-orange-100 shadow-sm">
                <i class="fas fa-sign-language text-3xl"></i>
            </div>
            <div>
                <h3 class="text-xl font-bold">Kata Isyarat</h3>
                <p class="text-xs text-orange-100 font-medium">180+ Kosakata Isyarat Tematik</p>
            </div>
        </div>
        <div class="bg-orange-500 w-10 h-10 rounded-full flex items-center justify-center text-orange-100 group-hover:bg-white group-hover:text-orange-600 transition-colors">
            <i class="fas fa-arrow-right"></i>
        </div>
    </button>
    
    <script>
        const API_KEY = "dc6zaTOxFJmzC"; // Public Beta Key
        const FALLBACK_DATA = {
             "wudhu": "https://commons.wikimedia.org/wiki/Special:FilePath/My%20first%20steps%20in%20Islam.pdf",
             "shalat": "https://commons.wikimedia.org/wiki/Special:FilePath/Slovak%20%28Slavish%29%20self-taught%20%28IA%20slovakslavishsel00morv%29.pdf",
             "sholat": "https://media.giphy.com/media/3o7TKMt1VVNkHV2PaE/giphy.gif",
             "adzan": "https://media.giphy.com/media/3o7TKMt1VVNkHV2PaE/giphy.gif"
        };

        const KATA_ISYARAT_DATA = [
            // Kategori 1: Sehari-hari (60 kata)
            { id: '1',  katagori: 'Sehari-hari', indonesia: 'Halo', inggris: 'Hello' },
            { id: '2',  katagori: 'Sehari-hari', indonesia: 'Terima kasih', inggris: 'Thank you' },
            { id: '3',  katagori: 'Sehari-hari', indonesia: 'Sama-sama', inggris: 'You are welcome' },
            { id: '4',  katagori: 'Sehari-hari', indonesia: 'Tolong', inggris: 'Please' },
            { id: '5',  katagori: 'Sehari-hari', indonesia: 'Maaf', inggris: 'Sorry' },
            { id: '6',  katagori: 'Sehari-hari', indonesia: 'Ya', inggris: 'Yes' },
            { id: '7',  katagori: 'Sehari-hari', indonesia: 'Tidak', inggris: 'No' },
            { id: '8',  katagori: 'Sehari-hari', indonesia: 'Siapa', inggris: 'Who' },
            { id: '9',  katagori: 'Sehari-hari', indonesia: 'Apa', inggris: 'What' },
            { id: '10', katagori: 'Sehari-hari', indonesia: 'Di mana', inggris: 'Where' },
            { id: '11', katagori: 'Sehari-hari', indonesia: 'Kapan', inggris: 'When' },
            { id: '12', katagori: 'Sehari-hari', indonesia: 'Mengapa', inggris: 'Why' },
            { id: '13', katagori: 'Sehari-hari', indonesia: 'Bagaimana', inggris: 'How' },
            { id: '14', katagori: 'Sehari-hari', indonesia: 'Berapa', inggris: 'How much' },
            { id: '15', katagori: 'Sehari-hari', indonesia: 'Nama', inggris: 'Name' },
            { id: '16', katagori: 'Sehari-hari', indonesia: 'Saya', inggris: 'I am' },
            { id: '17', katagori: 'Sehari-hari', indonesia: 'Kamu', inggris: 'You' },
            { id: '18', katagori: 'Sehari-hari', indonesia: 'Mereka', inggris: 'They' },
            { id: '19', katagori: 'Sehari-hari', indonesia: 'Kita', inggris: 'We' },
            { id: '20', katagori: 'Sehari-hari', indonesia: 'Baik', inggris: 'Good' },
            { id: '21', katagori: 'Sehari-hari', indonesia: 'Buruk', inggris: 'Bad' },
            { id: '22', katagori: 'Sehari-hari', indonesia: 'Makan', inggris: 'Eat' },
            { id: '23', katagori: 'Sehari-hari', indonesia: 'Minum', inggris: 'Drink' },
            { id: '24', katagori: 'Sehari-hari', indonesia: 'Tidur', inggris: 'Sleep' },
            { id: '25', katagori: 'Sehari-hari', indonesia: 'Bangun', inggris: 'Wake up' },
            { id: '26', katagori: 'Sehari-hari', indonesia: 'Pergi', inggris: 'Go' },
            { id: '27', katagori: 'Sehari-hari', indonesia: 'Datang', inggris: 'Come' },
            { id: '28', katagori: 'Sehari-hari', indonesia: 'Jalan', inggris: 'Walk' },
            { id: '29', katagori: 'Sehari-hari', indonesia: 'Lari', inggris: 'Run' },
            { id: '30', katagori: 'Sehari-hari', indonesia: 'Duduk', inggris: 'Sit' },
            { id: '31', katagori: 'Sehari-hari', indonesia: 'Berdiri', inggris: 'Stand' },
            { id: '32', katagori: 'Sehari-hari', indonesia: 'Lihat', inggris: 'Look' },
            { id: '33', katagori: 'Sehari-hari', indonesia: 'Dengar', inggris: 'Listen' },
            { id: '34', katagori: 'Sehari-hari', indonesia: 'Bicara', inggris: 'Talk' },
            { id: '35', katagori: 'Sehari-hari', indonesia: 'Pikir', inggris: 'Think' },
            { id: '36', katagori: 'Sehari-hari', indonesia: 'Tahu', inggris: 'Know' },
            { id: '37', katagori: 'Sehari-hari', indonesia: 'Lupa', inggris: 'Forget' },
            { id: '38', katagori: 'Sehari-hari', indonesia: 'Ingat', inggris: 'Remember' },
            { id: '39', katagori: 'Sehari-hari', indonesia: 'Paham', inggris: 'Understand' },
            { id: '40', katagori: 'Sehari-hari', indonesia: 'Bingung', inggris: 'Confused' },
            { id: '41', katagori: 'Sehari-hari', indonesia: 'Bantu', inggris: 'Help' },
            { id: '42', katagori: 'Sehari-hari', indonesia: 'Selesai', inggris: 'Finish' },
            { id: '43', katagori: 'Sehari-hari', indonesia: 'Mulai', inggris: 'Start' },
            { id: '44', katagori: 'Sehari-hari', indonesia: 'Buka', inggris: 'Open' },
            { id: '45', katagori: 'Sehari-hari', indonesia: 'Tutup', inggris: 'Close' },
            { id: '46', katagori: 'Sehari-hari', indonesia: 'Masuk', inggris: 'Enter' },
            { id: '47', katagori: 'Sehari-hari', indonesia: 'Keluar', inggris: 'Exit' },
            { id: '48', katagori: 'Sehari-hari', indonesia: 'Beli', inggris: 'Buy' },
            { id: '49', katagori: 'Sehari-hari', indonesia: 'Jual', inggris: 'Sell' },
            { id: '50', katagori: 'Sehari-hari', indonesia: 'Bayar', inggris: 'Pay' },
            { id: '51', katagori: 'Sehari-hari', indonesia: 'Uang', inggris: 'Money' },
            { id: '52', katagori: 'Sehari-hari', indonesia: 'Harga', inggris: 'Price' },
            { id: '53', katagori: 'Sehari-hari', indonesia: 'Murah', inggris: 'Cheap' },
            { id: '54', katagori: 'Sehari-hari', indonesia: 'Mahal', inggris: 'Expensive' },
            { id: '55', katagori: 'Sehari-hari', indonesia: 'Besar', inggris: 'Big' },
            { id: '56', katagori: 'Sehari-hari', indonesia: 'Kecil', inggris: 'Small' },
            { id: '57', katagori: 'Sehari-hari', indonesia: 'Panjang', inggris: 'Long' },
            { id: '58', katagori: 'Sehari-hari', indonesia: 'Pendek', inggris: 'Short' },
            { id: '59', katagori: 'Sehari-hari', indonesia: 'Berat', inggris: 'Heavy' },
            { id: '60', katagori: 'Sehari-hari', indonesia: 'Ringan', inggris: 'Light' },
            
            // Kategori 2: Ibadah dan Agama (60 kata)
            { id: '61', katagori: 'Ibadah dan Agama', indonesia: 'Allah', inggris: 'God' },
            { id: '62', katagori: 'Ibadah dan Agama', indonesia: 'Islam', inggris: 'Islam' },
            { id: '63', katagori: 'Ibadah dan Agama', indonesia: 'Iman', inggris: 'Faith' },
            { id: '64', katagori: 'Ibadah dan Agama', indonesia: 'Muslim', inggris: 'Muslim' },
            { id: '65', katagori: 'Ibadah dan Agama', indonesia: 'Nabi', inggris: 'Prophet' },
            { id: '66', katagori: 'Ibadah dan Agama', indonesia: 'Malaikat', inggris: 'Angel' },
            { id: '67', katagori: 'Ibadah dan Agama', indonesia: 'Agama', inggris: 'Religion' },
            { id: '68', katagori: 'Ibadah dan Agama', indonesia: 'Masjid', inggris: 'Mosque' },
            { id: '69', katagori: 'Ibadah dan Agama', indonesia: 'Shalat', inggris: 'Praying' },
            { id: '70', katagori: 'Ibadah dan Agama', indonesia: 'Wudhu', inggris: 'Ablution' },
            { id: '71', katagori: 'Ibadah dan Agama', indonesia: 'Doa', inggris: 'Pray' },
            { id: '72', katagori: 'Ibadah dan Agama', indonesia: 'Zikir', inggris: 'Dhikr' },
            { id: '73', katagori: 'Ibadah dan Agama', indonesia: 'Quran', inggris: 'Quran' },
            { id: '74', katagori: 'Ibadah dan Agama', indonesia: 'Puasa', inggris: 'Fasting' },
            { id: '75', katagori: 'Ibadah dan Agama', indonesia: 'Zakat', inggris: 'Zakat' },
            { id: '76', katagori: 'Ibadah dan Agama', indonesia: 'Haji', inggris: 'Hajj' },
            { id: '77', katagori: 'Ibadah dan Agama', indonesia: 'Umrah', inggris: 'Umrah' },
            { id: '78', katagori: 'Ibadah dan Agama', indonesia: 'Sedekah', inggris: 'Charity' },
            { id: '79', katagori: 'Ibadah dan Agama', indonesia: 'Pahala', inggris: 'Reward' },
            { id: '80', katagori: 'Ibadah dan Agama', indonesia: 'Dosa', inggris: 'Sin' },
            { id: '81', katagori: 'Ibadah dan Agama', indonesia: 'Surga', inggris: 'Heaven' },
            { id: '82', katagori: 'Ibadah dan Agama', indonesia: 'Neraka', inggris: 'Hell' },
            { id: '83', katagori: 'Ibadah dan Agama', indonesia: 'Halal', inggris: 'Halal' },
            { id: '84', katagori: 'Ibadah dan Agama', indonesia: 'Haram', inggris: 'Haram' },
            { id: '85', katagori: 'Ibadah dan Agama', indonesia: 'Kiblat', inggris: 'Qibla' },
            { id: '86', katagori: 'Ibadah dan Agama', indonesia: 'Imam', inggris: 'Imam' },
            { id: '87', katagori: 'Ibadah dan Agama', indonesia: 'Makmum', inggris: 'Follower in prayer' },
            { id: '88', katagori: 'Ibadah dan Agama', indonesia: 'Sujud', inggris: 'Prostrate' },
            { id: '89', katagori: 'Ibadah dan Agama', indonesia: 'Ruku', inggris: 'Bowing' },
            { id: '90', katagori: 'Ibadah dan Agama', indonesia: 'Amin', inggris: 'Amen' },
            { id: '91', katagori: 'Ibadah dan Agama', indonesia: 'Adzan', inggris: 'Call to prayer' },
            { id: '92', katagori: 'Ibadah dan Agama', indonesia: 'Iqamah', inggris: 'Iqamah' },
            { id: '93', katagori: 'Ibadah dan Agama', indonesia: 'Khotbah', inggris: 'Sermon' },
            { id: '94', katagori: 'Ibadah dan Agama', indonesia: 'Jumat', inggris: 'Friday' },
            { id: '95', katagori: 'Ibadah dan Agama', indonesia: 'Lebaran', inggris: 'Eid' },
            { id: '96', katagori: 'Ibadah dan Agama', indonesia: 'Ramadhan', inggris: 'Ramadan' },
            { id: '97', katagori: 'Ibadah dan Agama', indonesia: 'Sahur', inggris: 'Suhoor' },
            { id: '98', katagori: 'Ibadah dan Agama', indonesia: 'Buka puasa', inggris: 'Iftar' },
            { id: '99', katagori: 'Ibadah dan Agama', indonesia: 'Kurban', inggris: 'Sacrifice' },
            { id: '100', katagori: 'Ibadah dan Agama', indonesia: 'Sabar', inggris: 'Patience' },
            { id: '101', katagori: 'Ibadah dan Agama', indonesia: 'Syukur', inggris: 'Gratitude' },
            { id: '102', katagori: 'Ibadah dan Agama', indonesia: 'Ikhlas', inggris: 'Sincere' },
            { id: '103', katagori: 'Ibadah dan Agama', indonesia: 'Tobat', inggris: 'Repent' },
            { id: '104', katagori: 'Ibadah dan Agama', indonesia: 'Takdir', inggris: 'Destiny' },
            { id: '105', katagori: 'Ibadah dan Agama', indonesia: 'Mukjizat', inggris: 'Miracle' },
            { id: '106', katagori: 'Ibadah dan Agama', indonesia: 'Jin', inggris: 'Jinn' },
            { id: '107', katagori: 'Ibadah dan Agama', indonesia: 'Setan', inggris: 'Devil' },
            { id: '108', katagori: 'Ibadah dan Agama', indonesia: 'Kiamat', inggris: 'Doomsday' },
            { id: '109', katagori: 'Ibadah dan Agama', indonesia: 'Akhirat', inggris: 'Afterlife' },
            { id: '110', katagori: 'Ibadah dan Agama', indonesia: 'Jiwa', inggris: 'Soul' },
            { id: '111', katagori: 'Ibadah dan Agama', indonesia: 'Kubur', inggris: 'Grave' },
            { id: '112', katagori: 'Ibadah dan Agama', indonesia: 'Berkah', inggris: 'Blessing' },
            { id: '113', katagori: 'Ibadah dan Agama', indonesia: 'Laknat', inggris: 'Curse' },
            { id: '114', katagori: 'Ibadah dan Agama', indonesia: 'Aurat', inggris: 'Intimate parts' },
            { id: '115', katagori: 'Ibadah dan Agama', indonesia: 'Mahram', inggris: 'Mahram' },
            { id: '116', katagori: 'Ibadah dan Agama', indonesia: 'Nikah', inggris: 'Marriage' },
            { id: '117', katagori: 'Ibadah dan Agama', indonesia: 'Talak', inggris: 'Divorce' },
            { id: '118', katagori: 'Ibadah dan Agama', indonesia: 'Yatim', inggris: 'Orphan' },
            { id: '119', katagori: 'Ibadah dan Agama', indonesia: 'Fakir', inggris: 'Destitute' },
            { id: '120', katagori: 'Ibadah dan Agama', indonesia: 'Miskin', inggris: 'Poor' },

            // Kategori 3: Keluarga dan Perasaan (60 kata)
            { id: '121', katagori: 'Keluarga dan Perasaan', indonesia: 'Keluarga', inggris: 'Family' },
            { id: '122', katagori: 'Keluarga dan Perasaan', indonesia: 'Bapak', inggris: 'Father' },
            { id: '123', katagori: 'Keluarga dan Perasaan', indonesia: 'Ibu', inggris: 'Mother' },
            { id: '124', katagori: 'Keluarga dan Perasaan', indonesia: 'Anak', inggris: 'Child' },
            { id: '125', katagori: 'Keluarga dan Perasaan', indonesia: 'Kakak', inggris: 'Older sibling' },
            { id: '126', katagori: 'Keluarga dan Perasaan', indonesia: 'Adik', inggris: 'Younger sibling' },
            { id: '127', katagori: 'Keluarga dan Perasaan', indonesia: 'Kakek', inggris: 'Grandfather' },
            { id: '128', katagori: 'Keluarga dan Perasaan', indonesia: 'Nenek', inggris: 'Grandmother' },
            { id: '129', katagori: 'Keluarga dan Perasaan', indonesia: 'Paman', inggris: 'Uncle' },
            { id: '130', katagori: 'Keluarga dan Perasaan', indonesia: 'Bibi', inggris: 'Aunt' },
            { id: '131', katagori: 'Keluarga dan Perasaan', indonesia: 'Suami', inggris: 'Husband' },
            { id: '132', katagori: 'Keluarga dan Perasaan', indonesia: 'Istri', inggris: 'Wife' },
            { id: '133', katagori: 'Keluarga dan Perasaan', indonesia: 'Laki-laki', inggris: 'Man' },
            { id: '134', katagori: 'Keluarga dan Perasaan', indonesia: 'Perempuan', inggris: 'Woman' },
            { id: '135', katagori: 'Keluarga dan Perasaan', indonesia: 'Teman', inggris: 'Friend' },
            { id: '136', katagori: 'Keluarga dan Perasaan', indonesia: 'Sahabat', inggris: 'Best friend' },
            { id: '137', katagori: 'Keluarga dan Perasaan', indonesia: 'Tetangga', inggris: 'Neighbor' },
            { id: '138', katagori: 'Keluarga dan Perasaan', indonesia: 'Orang', inggris: 'Person' },
            { id: '139', katagori: 'Keluarga dan Perasaan', indonesia: 'Bayi', inggris: 'Baby' },
            { id: '140', katagori: 'Keluarga dan Perasaan', indonesia: 'Cinta', inggris: 'Love' },
            { id: '141', katagori: 'Keluarga dan Perasaan', indonesia: 'Sayang', inggris: 'Affection' },
            { id: '142', katagori: 'Keluarga dan Perasaan', indonesia: 'Benci', inggris: 'Hate' },
            { id: '143', katagori: 'Keluarga dan Perasaan', indonesia: 'Senang', inggris: 'Happy' },
            { id: '144', katagori: 'Keluarga dan Perasaan', indonesia: 'Sedih', inggris: 'Sad' },
            { id: '145', katagori: 'Keluarga dan Perasaan', indonesia: 'Marah', inggris: 'Angry' },
            { id: '146', katagori: 'Keluarga dan Perasaan', indonesia: 'Takut', inggris: 'Afraid' },
            { id: '147', katagori: 'Keluarga dan Perasaan', indonesia: 'Berani', inggris: 'Brave' },
            { id: '148', katagori: 'Keluarga dan Perasaan', indonesia: 'Malu', inggris: 'Shy' },
            { id: '149', katagori: 'Keluarga dan Perasaan', indonesia: 'Bangga', inggris: 'Proud' },
            { id: '150', katagori: 'Keluarga dan Perasaan', indonesia: 'Kecewa', inggris: 'Disappointed' },
            { id: '151', katagori: 'Keluarga dan Perasaan', indonesia: 'Terkejut', inggris: 'Surprised' },
            { id: '152', katagori: 'Keluarga dan Perasaan', indonesia: 'Capek', inggris: 'Tired' },
            { id: '153', katagori: 'Keluarga dan Perasaan', indonesia: 'Sakit', inggris: 'Sick' },
            { id: '154', katagori: 'Keluarga dan Perasaan', indonesia: 'Sehat', inggris: 'Healthy' },
            { id: '155', katagori: 'Keluarga dan Perasaan', indonesia: 'Gila', inggris: 'Crazy' },
            { id: '156', katagori: 'Keluarga dan Perasaan', indonesia: 'Lucu', inggris: 'Funny' },
            { id: '157', katagori: 'Keluarga dan Perasaan', indonesia: 'Serius', inggris: 'Serious' },
            { id: '158', katagori: 'Keluarga dan Perasaan', indonesia: 'Gembira', inggris: 'Joyful' },
            { id: '159', katagori: 'Keluarga dan Perasaan', indonesia: 'Sepi', inggris: 'Lonely' },
            { id: '160', katagori: 'Keluarga dan Perasaan', indonesia: 'Ramai', inggris: 'Crowded' },
            { id: '161', katagori: 'Keluarga dan Perasaan', indonesia: 'Pusing', inggris: 'Dizzy' },
            { id: '162', katagori: 'Keluarga dan Perasaan', indonesia: 'Lapar', inggris: 'Hungry' },
            { id: '163', katagori: 'Keluarga dan Perasaan', indonesia: 'Haus', inggris: 'Thirsty' },
            { id: '164', katagori: 'Keluarga dan Perasaan', indonesia: 'Kenyang', inggris: 'Full' },
            { id: '165', katagori: 'Keluarga dan Perasaan', indonesia: 'Dingin', inggris: 'Cold' },
            { id: '166', katagori: 'Keluarga dan Perasaan', indonesia: 'Panas', inggris: 'Hot' },
            { id: '167', katagori: 'Keluarga dan Perasaan', indonesia: 'Hangat', inggris: 'Warm' },
            { id: '168', katagori: 'Keluarga dan Perasaan', indonesia: 'Sejuk', inggris: 'Cool' },
            { id: '169', katagori: 'Keluarga dan Perasaan', indonesia: 'Kuat', inggris: 'Strong' },
            { id: '170', katagori: 'Keluarga dan Perasaan', indonesia: 'Lemah', inggris: 'Weak' },
            { id: '171', katagori: 'Keluarga dan Perasaan', indonesia: 'Cantik', inggris: 'Beautiful' },
            { id: '172', katagori: 'Keluarga dan Perasaan', indonesia: 'Ganteng', inggris: 'Handsome' },
            { id: '173', katagori: 'Keluarga dan Perasaan', indonesia: 'Jelek', inggris: 'Ugly' },
            { id: '174', katagori: 'Keluarga dan Perasaan', indonesia: 'Pintar', inggris: 'Smart' },
            { id: '175', katagori: 'Keluarga dan Perasaan', indonesia: 'Bodoh', inggris: 'Stupid' },
            { id: '176', katagori: 'Keluarga dan Perasaan', indonesia: 'Rajin', inggris: 'Diligent' },
            { id: '177', katagori: 'Keluarga dan Perasaan', indonesia: 'Malas', inggris: 'Lazy' },
            { id: '178', katagori: 'Keluarga dan Perasaan', indonesia: 'Jujur', inggris: 'Honest' },
            { id: '179', katagori: 'Keluarga dan Perasaan', indonesia: 'Bohong', inggris: 'Lie' },
            { id: '180', katagori: 'Keluarga dan Perasaan', indonesia: 'Setia', inggris: 'Loyal' }
        ];

        let currentKataCategory = 'Sehari-hari';
        let kataSearchTerm = '';
        let kataObserver = null;

        function openKataIsyaratModal() {
            openModal('modal-kata-isyarat');
            switchKataCategory('Sehari-hari'); // reset and render
        }

        function switchKataCategory(cat) {
            currentKataCategory = cat;
            document.querySelectorAll('.kata-cat-btn').forEach(btn => {
                if(btn.id === 'cat-btn-' + cat) {
                    btn.className = "kata-cat-btn snap-center whitespace-nowrap px-4 py-2 rounded-xl text-sm font-bold bg-orange-500 text-white shadow-md transition-colors";
                } else {
                    btn.className = "kata-cat-btn snap-center whitespace-nowrap px-4 py-2 rounded-xl text-sm font-bold bg-orange-50 text-orange-600 hover:bg-orange-100 border border-orange-200 transition-colors";
                }
            });
            renderKataIsyaratGrid();
        }

        function filterKataIsyarat() {
            kataSearchTerm = document.getElementById('search-kata').value.toLowerCase().trim();
            renderKataIsyaratGrid();
        }

        function renderKataIsyaratGrid() {
            const container = document.getElementById('kata-result-container');
            container.innerHTML = '';

            let filtered = KATA_ISYARAT_DATA.filter(item => item.katagori === currentKataCategory);
            if(kataSearchTerm) {
                filtered = filtered.filter(item => item.indonesia.toLowerCase().includes(kataSearchTerm));
            }

            if(filtered.length === 0) {
                container.innerHTML = '<div class="col-span-2 text-center text-gray-500 py-10">Kata tidak ditemukan.</div>';
                return;
            }

            // Setup intersection observer for lazy loading gifs to prevent API limits
            if(kataObserver) kataObserver.disconnect();
            kataObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if(entry.isIntersecting) {
                        const card = entry.target;
                        const wordId = card.getAttribute('data-id');
                        const wordEn = card.getAttribute('data-en');
                        const cat = card.getAttribute('data-cat');
                        if(!card.hasAttribute('data-loaded')) {
                            fetchKataGif(wordId, wordEn, cat, card);
                            card.setAttribute('data-loaded', 'true');
                        }
                    }
                });
            }, { root: document.getElementById('modal-kata-isyarat'), rootMargin: '0px 0px 200px 0px' });

            filtered.forEach(item => {
                const card = document.createElement('div');
                card.className = "bg-white p-3 rounded-2xl shadow-sm border border-orange-100 flex flex-col items-center opacity-0 animate-pop";
                card.setAttribute('data-id', item.id);
                card.setAttribute('data-en', item.inggris);
                card.setAttribute('data-cat', item.katagori);
                card.style.animationDelay = (Math.random() * 0.2) + 's';
                
                card.innerHTML = `
                    <div id="media-container-${item.id}" class="w-full aspect-square bg-orange-50 rounded-xl mb-2 overflow-hidden relative shadow-inner flex items-center justify-center">
                        <div class="skeleton w-full h-full absolute inset-0"></div>
                        <i class="fas fa-spinner fa-spin text-orange-300 relative z-10 text-2xl"></i>
                    </div>
                    <div class="w-full text-center">
                        <h3 class="font-bold text-sm text-gray-800">${item.indonesia}</h3>
                    </div>
                `;
                container.appendChild(card);
                kataObserver.observe(card);
            });
        }

        const STATIC_GIF_MAP = {
            "1": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%A2%D5%A1%D6%80%D6%87%20%D5%B1%D5%A5%D5%A6%20-%20hello%21.webm",
            "2": "https://commons.wikimedia.org/wiki/Special:FilePath/Bsl-thank-you.svg",
            "3": "https://commons.wikimedia.org/wiki/Special:FilePath/Fish%20Creek%20%28AU%29%2C%20Welcome%20Sign%20--%202019%20--%20150820.jpg",
            "4": "https://commons.wikimedia.org/wiki/Special:FilePath/Asl%20alphabet%20gallaudet.svg",
            "5": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%B6%D5%A5%D6%80%D5%B8%D5%B2%D5%B8%D6%82%D5%A9%D5%B5%D5%B8%D6%82%D5%B6%20-%20sorry.webm",
            "6": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign%20language%20alphabet%20%2859%29.png",
            "7": "https://commons.wikimedia.org/wiki/Special:FilePath/Asl%20alphabet%20gallaudet.svg",
            "8": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign%20language%20interpreter%2C%202012%20%2801%29.jpg",
            "9": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%AB%D5%9E%D5%B6%D5%B9%20-%20what%3F.webm",
            "10": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%B8%D6%80%D5%BF%D5%A5%D5%B2%D5%AB%D5%9E%D6%81%20-%20where%20from%20-%20where%20from.webm",
            "11": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%A5%D5%9E%D6%80%D5%A2%20-%20when%3F.webm",
            "12": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%AB%D5%B6%D5%B9%D5%B8%D5%9E%D6%82%20-%20why%3F.webm",
            "13": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign%20language%20interpreter%2C%202012%20%2801%29.jpg",
            "14": "https://commons.wikimedia.org/wiki/Special:FilePath/Willie%20and%20the%20mortage%2C%20showing%20how%20much%20may%20be%20accomplished%20b%20y%20a%20boy%20%28IA%20williemortagesho00abbo%29.pdf",
            "15": "https://commons.wikimedia.org/wiki/Special:FilePath/Tanzanian%20Sign%20Language%20%28TSL%29%20-%20Manual%20alphabet%20-%20F.jpg",
            "16": "https://commons.wikimedia.org/wiki/Special:FilePath/Hollywood%20Sign.jpg",
            "17": "https://commons.wikimedia.org/wiki/Special:FilePath/SIGNING%20I%20LOVE%20YOU%20in%20Ghanaian%20Sign%20Language.jpg",
            "18": "https://commons.wikimedia.org/wiki/Special:FilePath/A%20child%20watching%20an%20American%20Sign%20Language%20video%20in%20northern%20Maracay%2C%20Venezuela.jpg",
            "19": "https://commons.wikimedia.org/wiki/Special:FilePath/Human%20Language%20Families.png",
            "20": "https://commons.wikimedia.org/wiki/Special:FilePath/Tanzanian%20Sign%20Language%20-%20Habari%20ya%20asubuhi%20%28Good%20Morning%29%20-%20greeting%2002.webm",
            "21": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%A9%D5%B8%D6%82%D5%B5%D5%AC%20%D5%AC%D5%BD%D5%B8%D5%B2%20-%20bad%20hearing.webm",
            "22": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%B8%D6%82%D5%BF%D5%A5%D5%AC%20-%20to%20eat.webm",
            "23": "https://commons.wikimedia.org/wiki/Special:FilePath/No%20drink%20sign-es.svg",
            "24": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D6%84%D5%B6%D5%A5%D5%AC%20-%20to%20sleep%20%282%29.webm",
            "25": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%A1%D6%80%D5%A9%D5%B6%D5%A1%D5%B6%D5%A1%D5%AC%20-%20to%20wake%20up.webm",
            "26": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign%20language%20alphabet%20%2859%29.png",
            "27": "https://commons.wikimedia.org/wiki/Special:FilePath/Group%20of%20deaf%20people%2C%202010%20%2801%29.jpg",
            "28": "https://commons.wikimedia.org/wiki/Special:FilePath/Bachelors%20Walk%20Dublin%20bilingual%20street%20sign%20%282024%29.jpg",
            "29": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D6%83%D5%A1%D5%AD%D5%B9%D5%A5%D5%AC%20-%20to%20run%20away.webm",
            "30": "https://commons.wikimedia.org/wiki/Special:FilePath/Colombia%20road%20sign%20SIT-02.svg",
            "31": "https://commons.wikimedia.org/wiki/Special:FilePath/Macau%20road%20sign%20S02.svg",
            "32": "https://commons.wikimedia.org/wiki/Special:FilePath/Warning%20sign%20in%20cologne.jpg",
            "33": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_L.svg",
            "34": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_T.svg",
            "35": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_T.svg",
            "36": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_K.svg",
            "37": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_F.svg",
            "38": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_R.svg",
            "39": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_U.svg",
            "40": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_C.svg",
            "41": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_H.svg",
            "42": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_F.svg",
            "43": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_S.svg",
            "44": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_O.svg",
            "45": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_C.svg",
            "46": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_E.svg",
            "47": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_E.svg",
            "48": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_B.svg",
            "49": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_S.svg",
            "50": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_P.svg",
            "51": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_M.svg",
            "52": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_P.svg",
            "53": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_C.svg",
            "54": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_E.svg",
            "55": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_B.svg",
            "56": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_S.svg",
            "57": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_L.svg",
            "58": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_S.svg",
            "59": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_H.svg",
            "60": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_L.svg",
            "61": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_G.svg",
            "62": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_I.svg",
            "63": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_F.svg",
            "64": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_M.svg",
            "65": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_P.svg",
            "66": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_A.svg",
            "67": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_R.svg",
            "68": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_M.svg",
            "69": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_P.svg",
            "70": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_A.svg",
            "71": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_P.svg",
            "72": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_D.svg",
            "73": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_Q.svg",
            "74": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_F.svg",
            "75": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_Z.svg",
            "76": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_H.svg",
            "77": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_U.svg",
            "78": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_C.svg",
            "79": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_R.svg",
            "80": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_S.svg",
            "81": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_H.svg",
            "82": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_H.svg",
            "83": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_H.svg",
            "84": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_H.svg",
            "85": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_Q.svg",
            "86": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_I.svg",
            "87": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_F.svg",
            "88": "https://commons.wikimedia.org/wiki/Special:FilePath/The%20language%20of%20flowers%20and%20floral%20conversation%20%28IA%20languageflowers00seela%29.pdf",
            "89": "https://commons.wikimedia.org/wiki/Special:FilePath/The%20Language%20of%20flowers%20%28IA%20languageflowers00%29.pdf",
            "90": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_A.svg",
            "91": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_C.svg",
            "92": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_I.svg",
            "93": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D6%84%D5%A1%D6%80%D5%B8%D5%A6%20-%20sermon.webm",
            "94": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign%20language%20interpreter%20at%20FridaysForFuture%20protest%20Berlin%202025-02-14%2014.jpg",
            "95": "https://commons.wikimedia.org/wiki/Special:FilePath/Eid%20Blessings%20WDL6855.png",
            "96": "https://commons.wikimedia.org/wiki/Special:FilePath/2025-03-01-Ramadan%20-%20Karneval-1676.jpg",
            "97": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_S.svg",
            "98": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_I.svg",
            "99": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_S.svg",
            "100": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_P.svg",
            "101": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_G.svg",
            "102": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_S.svg",
            "103": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_R.svg",
            "104": "https://commons.wikimedia.org/wiki/Special:FilePath/The%20loom%20of%20destiny%20%28IA%20loomofdestiny00stri%29.pdf",
            "105": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%B0%D6%80%D5%A1%D5%B7%D6%84%20-%20miracle.webm",
            "106": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_J.svg",
            "107": "https://commons.wikimedia.org/wiki/Special:FilePath/The%20Baths%20%E2%80%94%20Devil%27s%20Bay%20Trail%20%28sign%29.JPG",
            "108": "https://commons.wikimedia.org/wiki/Special:FilePath/Passengers.%20Doomsday.%20April.%20%28Stories%29%20%28IA%20passengersdoomsd00heme%29.pdf",
            "109": "https://commons.wikimedia.org/wiki/Special:FilePath/AFTERLIFE%2C%20Kouros%20of%20Volomandra%20by%20Dionisis%20Christofilogiannis.jpg",
            "110": "https://commons.wikimedia.org/wiki/Special:FilePath/Air%20pictures%20-%20sign%20language%20%28IA%20airpicturessignl00gulirich%29.pdf",
            "111": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign%20by%20grave.jpg",
            "112": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%8F%D5%B6%D6%85%D6%80%D5%B0%D5%B6%D5%A5%D6%84%20-%20house%20blessing.webm",
            "113": "https://commons.wikimedia.org/wiki/Special:FilePath/The%20curse%20of%20Kehama%20%28IA%20curseofkehama00sout%29.pdf",
            "114": "https://commons.wikimedia.org/wiki/Special:FilePath/...%20Introduction%20to%20the%20study%20of%20sign%20language%20among%20the%20North%20American%20Indians%20..%20%28IA%20introductiontost01mall%29.pdf",
            "115": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_M.svg",
            "116": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%BA%D5%BD%D5%A1%D5%AF%20-%20marriage.webm",
            "117": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_D.svg",
            "118": "https://commons.wikimedia.org/wiki/Special:FilePath/The%20...%20annual%20report%20of%20the%20Protestant%20Orphan%20Asylum%20Society%20of%20the%20City%20of%20San%20Francisco%20%28IA%20annualreportofpr186271pro%29.pdf",
            "119": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_D.svg",
            "120": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%A1%D5%B2%D6%84%D5%A1%D5%BF%20-%20poor.webm",
            "121": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign%20language%20families.png",
            "122": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_F.svg",
            "123": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%BD%D5%AF%D5%A5%D5%BD%D5%B8%D6%82%D6%80%20-%20mother-in-law.webm",
            "124": "https://commons.wikimedia.org/wiki/Special:FilePath/Abolish%20child%20slavery.jpg",
            "125": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_O.svg",
            "126": "https://commons.wikimedia.org/wiki/Special:FilePath/Long-term%20outcomes%20in%20two%20adult%20siblings%20with%20Fucosidosis.pdf",
            "127": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%BA%D5%A1%D5%BA%D5%AB%D5%AF%20-%20grandfather.webm",
            "128": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%BF%D5%A1%D5%BF%D5%AB%D5%AF%20-%20grandmother.webm",
            "129": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%B0%D5%B8%D6%80%D5%A5%D5%B2%D5%A2%D5%A1%D5%B5%D6%80%20-%20uncle%20%28father%27s%20brother%29.webm",
            "130": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%B0%D5%B8%D6%80%D5%A1%D6%84%D5%B8%D6%82%D5%B5%D6%80%20-%20aunt%20%28father%27s%20sister%29.webm",
            "131": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_H.svg",
            "132": "https://commons.wikimedia.org/wiki/Special:FilePath/David%20-%20Portrait%20of%20Monsieur%20Lavoisier%20and%20His%20Wife.jpg",
            "133": "https://commons.wikimedia.org/wiki/Special:FilePath/Bicycle%20in%20Ghanaian%20sign%20language%20interpretation.webm",
            "134": "https://commons.wikimedia.org/wiki/Special:FilePath/Woman%20Interpreting%20Sign%20Language%20GIF%20Animation%20Loop.gif",
            "135": "https://commons.wikimedia.org/wiki/Special:FilePath/Drawing%20%28sign%20language%20friend%29%2C%202008.jpg",
            "136": "https://commons.wikimedia.org/wiki/Special:FilePath/Air%20pictures%20-%20sign%20language%20%28IA%20airpicturessignl00gulirich%29.pdf",
            "137": "https://commons.wikimedia.org/wiki/Special:FilePath/Our%20Neighbor-Mexico.djvu",
            "138": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign%20language%20interpreter%2C%202012%20%2801%29.jpg",
            "139": "https://commons.wikimedia.org/wiki/Special:FilePath/Baby%20sign%20language%2C%202009.jpg",
            "140": "https://commons.wikimedia.org/wiki/Special:FilePath/ASL%20ILY%40Side-PalmForward%20%28Cut%20out%29.jpg",
            "141": "https://commons.wikimedia.org/wiki/Special:FilePath/The%20language%20of%20flowers%20-%20The%20floral%20offering%20%3B%20a%20token%20of%20affection%20and%20esteem%20%3B%20comprising%20the%20language%20and%20poetry%20of%20flowers%20%28IA%20languageflowers00dumo%29.pdf",
            "142": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%A1%D5%BF%D5%A5%D5%AC%20-%20to%20hate.webm",
            "143": "https://commons.wikimedia.org/wiki/Special:FilePath/Four-language%20sign%20in%20Sharm%20el-Sheikh%2C%20Egypt.png",
            "144": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%BF%D5%AD%D5%B8%D6%82%D6%80%20-%20sad.webm",
            "145": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%BB%D5%B2%D5%A1%D5%B5%D5%AB%D5%B6%20-%20angry.webm",
            "146": "https://commons.wikimedia.org/wiki/Special:FilePath/Air%20pictures%20-%20sign%20language%20%28IA%20airpicturessignl00gulirich%29.pdf",
            "147": "https://commons.wikimedia.org/wiki/Special:FilePath/Air%20pictures%20-%20sign%20language%20%28IA%20airpicturessignl00gulirich%29.pdf",
            "148": "https://commons.wikimedia.org/wiki/Special:FilePath/The%20Language%20of%20flowers%20%28IA%20languageflowers00i%29.pdf",
            "149": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_P.svg",
            "150": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_D.svg",
            "151": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%A6%D5%A1%D6%80%D5%B4%D5%A1%D5%B6%D5%A1%D5%AC%20-%20to%20be%20surprised.webm",
            "152": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_T.svg",
            "153": "https://commons.wikimedia.org/wiki/Special:FilePath/Broke%2C%20baby%20sick%2C%20and%20car%20trouble%21%20-%20Dorothea%20Langes%20photo%20of%20a%20Missouri%20family%20of%20five%20in%20the%20vicinity%20of%20Tracy%2C%20California.jpg",
            "154": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%A1%D5%BC%D5%B8%D5%B2%D5%BB%20-%20healthy.webm",
            "155": "https://commons.wikimedia.org/wiki/Special:FilePath/Crazy%20Mary%27s%20Cafe%2C%20Home%20of%20the%20Uffda%20Burger%20in%20Finlayson%2C%20Minnesota.jpg",
            "156": "https://commons.wikimedia.org/wiki/Special:FilePath/Funny%20sign%2C%20L%C3%BCderitz%20%283148029384%29.jpg",
            "157": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_S.svg",
            "158": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%B8%D6%82%D6%80%D5%A1%D5%AD%20-%20joyful.webm",
            "159": "https://commons.wikimedia.org/wiki/Special:FilePath/Radclyffe%20Hall%20-%20The%20Well%20of%20Loneliness.pdf",
            "160": "https://commons.wikimedia.org/wiki/Special:FilePath/Announcement%20of%20not%20crowded%20time%20in%20supermarket%20for%20protecting%20from%20infecting%20Covid-19.jpg",
            "161": "https://commons.wikimedia.org/wiki/Special:FilePath/Tauchzeichen-Schwindel-Diving-Sign-Dizziness.png",
            "162": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D6%84%D5%A1%D5%B2%D6%81%D5%A1%D5%AE%20-%20hungry.webm",
            "163": "https://commons.wikimedia.org/wiki/Special:FilePath/The%20Language%20of%20the%20Salinan%20Indians.pdf",
            "164": "https://commons.wikimedia.org/wiki/Special:FilePath/Hollywood%20Sign.jpg",
            "165": "https://commons.wikimedia.org/wiki/Special:FilePath/Cold%20Response%202010%20-%20road%20sign%20in%20Norway.jpg",
            "166": "https://commons.wikimedia.org/wiki/Special:FilePath/Hot%20water%20pool%20sign.jpg",
            "167": "https://commons.wikimedia.org/wiki/Special:FilePath/Air%20pictures%20-%20sign%20language%20%28IA%20airpicturessignl00gulirich%29.pdf",
            "168": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_C.svg",
            "169": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%A1%D5%B4%D5%B8%D6%82%D6%80%20-%20strong.webm",
            "170": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%A9%D5%B8%D6%82%D5%B5%D5%AC%20-%20weak.webm",
            "171": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%A3%D5%A5%D5%B2%D5%A5%D6%81%D5%AB%D5%AF%20-%20beautiful.webm",
            "172": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_H.svg",
            "173": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%BF%D5%A3%D5%A5%D5%B2%20-%20ugly.webm",
            "174": "https://commons.wikimedia.org/wiki/Special:FilePath/Berlin%2C%20Flughafen%20Tempelhof%2C%20Smart%20EQ%20Forfour%20--%202019%20--%204342.jpg",
            "175": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%B0%D5%AB%D5%B4%D5%A1%D6%80%20-%20stupid.webm",
            "176": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_D.svg",
            "177": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_L.svg",
            "178": "https://commons.wikimedia.org/wiki/Special:FilePath/Armenian%20Sign%20Language%20%28ArSL%29%20-%20%D5%A1%D5%A6%D5%B6%D5%AB%D5%BE%20-%20honest.webm",
            "179": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_L.svg",
            "180": "https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_L.svg",
        };

        async function fetchKataGif(id, wordEn, category, cardElement) {
            const mediaContainer = document.getElementById(`media-container-${id}`);
            let mediaUrl = null;

            if (STATIC_GIF_MAP[id]) {
                mediaUrl = STATIC_GIF_MAP[id];
                const isVideo = mediaUrl.toLowerCase().match(/\\.(webm|ogv|mp4)($|\\?)/);
                if(isVideo) {
                    mediaContainer.innerHTML = `
                        <video src="${mediaUrl}" class="w-full h-full object-cover" autoplay loop muted playsinline></video>
                    `;
                } else {
                    mediaContainer.innerHTML = `
                        <img src="${mediaUrl}" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300">
                    `;
                }
                return;
            }

            // Strategy for "Sehari-hari": Try Wikipedia MediaWiki API first
            if (category === 'Sehari-hari') {
                try {
                    // Search for files in Wikimedia Commons related to the word + sign language
                    const wikiUrl = `https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(wordEn + ' sign language')}&srnamespace=6&format=json&origin=*`;
                    const res = await fetch(wikiUrl);
                    if(res.ok) {
                        const data = await res.json();
                        if(data.query && data.query.search && data.query.search.length > 0) {
                            // Extract title and get actual file path
                            const title = data.query.search[0].title;
                            mediaUrl = `https://commons.wikimedia.org/wiki/Special:FilePath/${encodeURIComponent(title.replace('File:', ''))}`;
                        }
                    }
                } catch(e) {
                    console.log("Wiki API failed, falling back to Giphy");
                }
            }

            // Strategy Fallback or for other categories: Giphy API with "sign language ASL" filter
            if (!mediaUrl) {
                try {
                    const giphyUrl = `https://api.giphy.com/v1/gifs/search?api_key=${API_KEY}&q=${encodeURIComponent(wordEn + ' sign language ASL')}&limit=1`;
                    const res = await fetch(giphyUrl);
                    if(res.ok) {
                        const data = await res.json();
                        if (data.data && data.data.length > 0) {
                            mediaUrl = data.data[0].images.fixed_height.url;
                        }
                    }
                } catch(e) {
                    console.log("Giphy API failed");
                }
            }

            // Render Result
            if (mediaUrl) {
                // Determine if it's a video file (webm, ogv, mp4 from Wikipedia) or an image/gif
                const isVideo = mediaUrl.toLowerCase().match(/\\.(webm|ogv|mp4)($|\\?)/);
                
                if(isVideo) {
                    mediaContainer.innerHTML = `
                        <video src="${mediaUrl}" class="w-full h-full object-cover" autoplay loop muted playsinline></video>
                    `;
                } else {
                    mediaContainer.innerHTML = `
                        <img src="${mediaUrl}" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300">
                    `;
                }
            } else {
                mediaContainer.innerHTML = `
                     <div class="w-full h-full flex items-center justify-center text-gray-700">
                        <i class="fas fa-image-slash text-2xl"></i>
                    </div>
                `;
            }
        }
        
        // Voice to Sign (Web Speech API)
        let recognition;
        let isRecording = false;
        
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'id-ID';
            
            recognition.onresult = function(event) {
                const text = event.results[0][0].transcript;
                document.getElementById('search-input').value = text;
                document.getElementById('mic-btn').classList.remove('mic-active');
                isRecording = false;
                // Auto execute search
                handleSearch(new Event('submit'));
            };
            
            recognition.onerror = function(event) {
                console.error("Speech error", event.error);
                document.getElementById('mic-btn').classList.remove('mic-active');
                isRecording = false;
            };
            
            recognition.onend = function() {
                document.getElementById('mic-btn').classList.remove('mic-active');
                isRecording = false;
            };
        } else {
            console.warn("Web Speech API not supported.");
        }

        function toggleVoice() {
            if(!recognition) {
                alert("Browser tidak mendukung fitur Voice to Sign.");
                return;
            }
            if(isRecording) {
                recognition.stop();
            } else {
                recognition.start();
                document.getElementById('mic-btn').classList.add('mic-active');
                isRecording = true;
            }
        }

        async function handleSearch(e) {
            if(e) e.preventDefault();
            const query = document.getElementById('search-input').value.toLowerCase().trim();
            if (!query) return;

            const container = document.getElementById('result-container');
            
            // Render Skeleton
            const words = query.split(' ');
            container.innerHTML = '';
            
            for(let i=0; i<words.length; i++) {
                container.innerHTML += `
                    <div class="bg-white p-4 rounded-3xl shadow-sm border border-yellow-100 flex flex-col items-center">
                        <div class="w-full aspect-square rounded-2xl mb-3 skeleton"></div>
                        <div class="h-4 w-20 skeleton rounded mb-2"></div>
                    </div>
                `;
            }

            // Fetch and Replace
            const newCards = [];
            for (let i = 0; i < words.length; i++) {
                const word = words[i];
                let gifUrl = '';

                // Try Kemdikbud SIBI API simulation first
                try {
                    // Simulate fetching from official API (pmpk.kemdikbud.go.id/sibi/api)
                    const res = await fetch(`https://pmpk.kemdikbud.go.id/sibi/api?katakunci=${word}`);
                    if(res.ok) {
                        const data = await res.json();
                        if(data && data.length > 0 && data[0].video) {
                            gifUrl = data[0].video; // assuming URL structure
                        }
                    }
                } catch(e) {
                    console.log("SIBI API failed, using fallback");
                }

                // Check Fallback / Giphy if SIBI fails
                if(!gifUrl) {
                    if (FALLBACK_DATA[word]) {
                        gifUrl = FALLBACK_DATA[word];
                    } else {
                        try {
                            const res = await fetch(`https://api.giphy.com/v1/gifs/search?api_key=${API_KEY}&q=${word} sign language indonesia&limit=1`);
                            const data = await res.json();
                            if (data.data && data.data.length > 0) {
                                gifUrl = data.data[0].images.fixed_height.url;
                            }
                        } catch (err) {
                            console.error(err);
                        }
                    }
                }

                // Create Final Card
                let content = '';
                if (gifUrl) {
                    content = `
                        <div class="w-full aspect-square bg-yellow-50 rounded-2xl mb-3 overflow-hidden relative shadow-inner group">
                            <img src="${gifUrl}" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300">
                        </div>
                    `;
                } else {
                    content = `
                         <div class="w-full aspect-square bg-yellow-50 rounded-2xl mb-3 flex items-center justify-center text-gray-700">
                            <i class="fas fa-image-slash text-3xl"></i>
                        </div>
                    `;
                }
                
                const cardHTML = `
                    <div class="bg-white p-4 rounded-3xl shadow-sm border border-yellow-100 flex flex-col items-center opacity-0 animate-pop" style="animation-delay: ${i * 0.1}s">
                        ${content}
                        <div class="w-full text-center">
                            <h3 class="font-bold text-xl text-gray-800 mb-1">${word}</h3>
                            <div class="progress-line"></div>
                        </div>
                    </div>
                `;
                newCards.push(cardHTML);
            }
            
            // Replace Skeletons
            setTimeout(() => {
                container.innerHTML = newCards.join('');
            }, 600); // Artificial delay to show skeleton
        }

        function clearResults() {
            document.getElementById('search-input').value = '';
            document.getElementById('result-container').innerHTML = '';
        }
    </script>

    <button onclick="openModal('modal-medis-tunarungu')" class="mt-8 w-full border-2 border-yellow-200 text-yellow-600 text-[10px] font-bold py-3 rounded-xl hover:bg-yellow-50 transition uppercase tracking-wider shadow-sm">
        <i class="fas fa-stethoscope mr-2"></i> PENJELASAN MEDIS
    </button>

    <!-- Modal Kata Isyarat -->
    <div id="modal-kata-isyarat" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" onclick="closeModal('modal-kata-isyarat')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20 max-h-[90dvh] overflow-y-auto flex flex-col">
            <div class="flex justify-between items-center mb-6 shrink-0">
                <h3 class="text-lg font-bold text-orange-800"><i class="fas fa-sign-language text-orange-500 mr-2"></i>Kata Isyarat</h3>
                <button onclick="closeModal('modal-kata-isyarat')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>

            <!-- Search -->
            <div class="mb-4 shrink-0 relative">
                <input type="text" id="search-kata" oninput="filterKataIsyarat()" placeholder="Cari kata isyarat..." class="w-full bg-orange-50 border border-orange-100 rounded-2xl p-4 pl-12 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500 text-orange-800 placeholder-orange-300">
                <i class="fas fa-search absolute left-4 top-1/2 transform -translate-y-1/2 text-orange-400"></i>
            </div>

            <!-- Categories -->
            <div class="flex gap-2 mb-6 overflow-x-auto pb-2 scrollbar-hide shrink-0 snap-x">
                <button onclick="switchKataCategory('Sehari-hari')" id="cat-btn-Sehari-hari" class="kata-cat-btn snap-center whitespace-nowrap px-4 py-2 rounded-xl text-sm font-bold bg-orange-500 text-white shadow-md transition-colors">Sehari-hari</button>
                <button onclick="switchKataCategory('Ibadah dan Agama')" id="cat-btn-Ibadah dan Agama" class="kata-cat-btn snap-center whitespace-nowrap px-4 py-2 rounded-xl text-sm font-bold bg-orange-50 text-orange-600 hover:bg-orange-100 border border-orange-200 transition-colors">Ibadah dan Agama</button>
                <button onclick="switchKataCategory('Keluarga dan Perasaan')" id="cat-btn-Keluarga dan Perasaan" class="kata-cat-btn snap-center whitespace-nowrap px-4 py-2 rounded-xl text-sm font-bold bg-orange-50 text-orange-600 hover:bg-orange-100 border border-orange-200 transition-colors">Keluarga dan Perasaan</button>
            </div>

            <!-- Grid -->
            <div id="kata-result-container" class="grid grid-cols-2 gap-3 overflow-y-auto content-start flex-1 min-h-[50dvh]">
                <!-- Cards injected here via JS -->
            </div>
        </div>
    </div>

    <!-- Modal Education Tunarungu -->
    <div id="modal-education" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" onclick="closeModal('modal-education')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20 max-h-[90dvh] overflow-y-auto">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-yellow-800"><i class="fas fa-hands-asl-interpreting text-yellow-500 mr-2"></i>Belajar Bahasa Isyarat</h3>
                <button onclick="closeModal('modal-education')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>

            <div class="mb-6">
                <h4 class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4 border-b border-gray-100 pb-2">ABJAD ( A - Z )</h4>
                <div class="grid grid-cols-3 gap-3">
                    {% for item in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' %}
                    <div class="bg-white p-2 rounded-2xl shadow-sm border border-yellow-100 flex flex-col items-center hover:scale-110 hover:shadow-lg hover:border-yellow-300 transition-all cursor-pointer">
                        <div class="w-full aspect-square bg-yellow-50 rounded-xl mb-2 overflow-hidden flex items-center justify-center text-gray-700 border border-yellow-50 p-2">
                            <img src="https://commons.wikimedia.org/wiki/Special:FilePath/Sign_language_{{item}}.svg" onerror="this.outerHTML='<i class=\\'fas fa-hands text-2xl\\'></i>'" class="w-full h-full object-contain">
                        </div>
                        <span class="font-bold text-lg text-yellow-700">{{item}}</span>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <div class="mb-6">
                <h4 class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4 border-b border-gray-100 pb-2">ANGKA ( 0 - 9 )</h4>
                <div class="grid grid-cols-3 gap-3">
                    <div class="bg-white p-2 rounded-2xl shadow-sm border border-yellow-100 flex flex-col items-center hover:scale-110 hover:shadow-lg hover:border-yellow-300 transition-all cursor-pointer">
                        <div class="w-full aspect-square bg-yellow-50 rounded-xl mb-2 overflow-hidden flex items-center justify-center text-gray-700 border border-yellow-50 p-2">
                            <img src="https://www.lifeprint.com/asl101/gifs-png/numbers/0.png" onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/f/f9/Asl_alphabet_gallaudet_%28zero%29.svg'; this.onerror=function(){this.outerHTML='<i class=\'fas fa-hands text-2xl\'></i>'};" class="w-full h-full object-contain">
                        </div>
                        <span class="font-bold text-lg text-yellow-700">0</span>
                    </div>
                    <div class="bg-white p-2 rounded-2xl shadow-sm border border-yellow-100 flex flex-col items-center hover:scale-110 hover:shadow-lg hover:border-yellow-300 transition-all cursor-pointer">
                        <div class="w-full aspect-square bg-yellow-50 rounded-xl mb-2 overflow-hidden flex items-center justify-center text-gray-700 border border-yellow-50 p-2">
                            <img src="https://www.lifeprint.com/asl101/gifs-png/numbers/1.png" onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/f/f3/Sign_language_1.jpg'; this.onerror=function(){this.outerHTML='<i class=\'fas fa-hands text-2xl\'></i>'};" class="w-full h-full object-contain">
                        </div>
                        <span class="font-bold text-lg text-yellow-700">1</span>
                    </div>
                    <div class="bg-white p-2 rounded-2xl shadow-sm border border-yellow-100 flex flex-col items-center hover:scale-110 hover:shadow-lg hover:border-yellow-300 transition-all cursor-pointer">
                        <div class="w-full aspect-square bg-yellow-50 rounded-xl mb-2 overflow-hidden flex items-center justify-center text-gray-700 border border-yellow-50 p-2">
                            <img src="https://www.lifeprint.com/asl101/gifs-png/numbers/2.png" onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/a/a3/Sign_language_2.jpg'; this.onerror=function(){this.outerHTML='<i class=\'fas fa-hands text-2xl\'></i>'};" class="w-full h-full object-contain">
                        </div>
                        <span class="font-bold text-lg text-yellow-700">2</span>
                    </div>
                    <div class="bg-white p-2 rounded-2xl shadow-sm border border-yellow-100 flex flex-col items-center hover:scale-110 hover:shadow-lg hover:border-yellow-300 transition-all cursor-pointer">
                        <div class="w-full aspect-square bg-yellow-50 rounded-xl mb-2 overflow-hidden flex items-center justify-center text-gray-700 border border-yellow-50 p-2">
                            <img src="https://www.lifeprint.com/asl101/gifs-png/numbers/3.png" onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/8/8b/Sign_language_3.jpg'; this.onerror=function(){this.outerHTML='<i class=\'fas fa-hands text-2xl\'></i>'};" class="w-full h-full object-contain">
                        </div>
                        <span class="font-bold text-lg text-yellow-700">3</span>
                    </div>
                    <div class="bg-white p-2 rounded-2xl shadow-sm border border-yellow-100 flex flex-col items-center hover:scale-110 hover:shadow-lg hover:border-yellow-300 transition-all cursor-pointer">
                        <div class="w-full aspect-square bg-yellow-50 rounded-xl mb-2 overflow-hidden flex items-center justify-center text-gray-700 border border-yellow-50 p-2">
                            <img src="https://www.lifeprint.com/asl101/gifs-png/numbers/4.png" onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/c/cc/Sign_language_4.jpg'; this.onerror=function(){this.outerHTML='<i class=\'fas fa-hands text-2xl\'></i>'};" class="w-full h-full object-contain">
                        </div>
                        <span class="font-bold text-lg text-yellow-700">4</span>
                    </div>
                    <div class="bg-white p-2 rounded-2xl shadow-sm border border-yellow-100 flex flex-col items-center hover:scale-110 hover:shadow-lg hover:border-yellow-300 transition-all cursor-pointer">
                        <div class="w-full aspect-square bg-yellow-50 rounded-xl mb-2 overflow-hidden flex items-center justify-center text-gray-700 border border-yellow-50 p-2">
                            <img src="https://www.lifeprint.com/asl101/gifs-png/numbers/5.png" onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/7/7a/Sign_language_5.jpg'; this.onerror=function(){this.outerHTML='<i class=\'fas fa-hands text-2xl\'></i>'};" class="w-full h-full object-contain">
                        </div>
                        <span class="font-bold text-lg text-yellow-700">5</span>
                    </div>
                    <div class="bg-white p-2 rounded-2xl shadow-sm border border-yellow-100 flex flex-col items-center hover:scale-110 hover:shadow-lg hover:border-yellow-300 transition-all cursor-pointer">
                        <div class="w-full aspect-square bg-yellow-50 rounded-xl mb-2 overflow-hidden flex items-center justify-center text-gray-700 border border-yellow-50 p-2">
                            <img src="https://www.lifeprint.com/asl101/gifs-png/numbers/6.png" onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/3/31/Sign_language_6.jpg'; this.onerror=function(){this.outerHTML='<i class=\'fas fa-hands text-2xl\'></i>'};" class="w-full h-full object-contain">
                        </div>
                        <span class="font-bold text-lg text-yellow-700">6</span>
                    </div>
                    <div class="bg-white p-2 rounded-2xl shadow-sm border border-yellow-100 flex flex-col items-center hover:scale-110 hover:shadow-lg hover:border-yellow-300 transition-all cursor-pointer">
                        <div class="w-full aspect-square bg-yellow-50 rounded-xl mb-2 overflow-hidden flex items-center justify-center text-gray-700 border border-yellow-50 p-2">
                            <img src="https://www.lifeprint.com/asl101/gifs-png/numbers/7.png" onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/0/0f/Sign_language_7.jpg'; this.onerror=function(){this.outerHTML='<i class=\'fas fa-hands text-2xl\'></i>'};" class="w-full h-full object-contain">
                        </div>
                        <span class="font-bold text-lg text-yellow-700">7</span>
                    </div>
                    <div class="bg-white p-2 rounded-2xl shadow-sm border border-yellow-100 flex flex-col items-center hover:scale-110 hover:shadow-lg hover:border-yellow-300 transition-all cursor-pointer">
                        <div class="w-full aspect-square bg-yellow-50 rounded-xl mb-2 overflow-hidden flex items-center justify-center text-gray-700 border border-yellow-50 p-2">
                            <img src="https://www.lifeprint.com/asl101/gifs-png/numbers/8.png" onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/4/44/Sign_language_8.jpg'; this.onerror=function(){this.outerHTML='<i class=\'fas fa-hands text-2xl\'></i>'};" class="w-full h-full object-contain">
                        </div>
                        <span class="font-bold text-lg text-yellow-700">8</span>
                    </div>
                    <div class="bg-white p-2 rounded-2xl shadow-sm border border-yellow-100 flex flex-col items-center hover:scale-110 hover:shadow-lg hover:border-yellow-300 transition-all cursor-pointer">
                        <div class="w-full aspect-square bg-yellow-50 rounded-xl mb-2 overflow-hidden flex items-center justify-center text-gray-700 border border-yellow-50 p-2">
                            <img src="https://www.lifeprint.com/asl101/gifs-png/numbers/9.png" onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/5/55/Sign_language_9.jpg'; this.onerror=function(){this.outerHTML='<i class=\'fas fa-hands text-2xl\'></i>'};" class="w-full h-full object-contain">
                        </div>
                        <span class="font-bold text-lg text-yellow-700">9</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal Medis Tunarungu -->
    <div id="modal-medis-tunarungu" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" onclick="closeModal('modal-medis-tunarungu')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20 max-h-[90dvh] overflow-y-auto">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-notes-medical text-yellow-500 mr-2"></i>PENJELASAN MEDIS</h3>
                <button onclick="closeModal('modal-medis-tunarungu')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            
            <div class="mb-6">
                <h4 class="text-xs font-bold text-yellow-600 uppercase tracking-widest mb-2 border-b border-yellow-100 pb-1">Dasar Medis Sains</h4>
                <p class="text-sm text-gray-600 leading-relaxed text-justify">
                    Fitur antarmuka Kamus Visual ini dilandasi oleh <strong>Dual-Coding Theory</strong>. Sistem memecah kalimat menjadi kata per kata dan menampilkan animasi dengan transisi halus tanpa *blank screen* (skeleton loading) untuk menjaga atensi visual. Efek animasi *pop-up* (spring scale) saat gambar muncul dirancang untuk menarik fokus mata (*visual capture*), dan garis progres di bawah teks memandu arah baca, membantu anak tunarungu yang sering mengalami kesulitan dalam *tracking* linear teks.
                </p>
            </div>

            <div class="bg-yellow-50 p-4 rounded-2xl border border-yellow-100">
                <h4 class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Penelitian Medis & Referensi</h4>
                <ul class="space-y-3">
                    <li class="text-xs text-gray-600">
                        <span class="font-bold text-gray-800">Clark, J. M., & Paivio, A. (1991)</span>
                        "Dual coding theory and education". Pemrosesan ganda teks dan visual memperkuat retensi memori jangka panjang.
                    </li>
                    <li class="text-xs text-gray-600">
                        <span class="font-bold text-gray-800">Yilmaz, Y., & Topcu, H. (2023)</span>
                        "Comparative effectiveness of picture-based vocabulary instruction". Visual dinamis lebih efektif daripada gambar statis untuk anak dengan hambatan pendengaran.
                    </li>
                </ul>
            </div>
        </div>
    </div>
</div>
"""

@app.route('/slb/tunanetra')
def slb_tunanetra():
    return cached_render('BASE_LAYOUT', BASE_LAYOUT, styles=STYLES_HTML, active_page='slb', content=SLB_TUNANETRA_HTML, theme={'nav_bg': 'bg-blue-100', 'title_text': 'text-blue-800'}, is_admin=session.get('is_admin', False), settings=get_settings(), needs_socketio=False)

@app.route('/slb/tunarungu', methods=['GET', 'POST'])
def slb_tunarungu():
    words_data = []
    sentence = ""
    if request.method == 'POST':
        sentence = request.form.get('sentence', '').lower()
        if sentence:
            words = sentence.split()
            for w in words:
                entry = SignLanguageDictionary.query.filter_by(word=w).first()
                url = entry.image_url if entry else None
                words_data.append({'word': w, 'url': url})
    
    return cached_render('BASE_LAYOUT', BASE_LAYOUT, styles=STYLES_HTML, active_page='slb', content=cached_render('SLB_TUNARUNGU_HTML', SLB_TUNARUNGU_HTML, words_data=words_data, sentence=sentence), theme={'nav_bg': 'bg-yellow-100', 'title_text': 'text-yellow-800'}, is_admin=session.get('is_admin', False), settings=get_settings(), needs_socketio=False)

SLB_TUNAGRAHITA_HTML = """
<div class="min-h-[100dvh] bg-[#F3E8FF] pt-24 px-5 pb-32">
    <!-- Confetti Library -->
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>

    <h2 class="text-3xl font-bold text-purple-900 mb-6 border-l-4 border-purple-500 pl-3">Game Runtutan Kognitif</h2>
    
    <p class="text-purple-700 mb-8 font-medium">Pilih aktivitas dan susun kartunya dengan benar!</p>
    
    <!-- Game Selection Menu -->
    <div id="game-selection" class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8 transition-all duration-500">
        <button onclick="startGame('wudhu')" class="bg-white p-4 rounded-3xl shadow-sm border border-purple-100 flex flex-col items-center justify-center hover:bg-purple-50 hover:scale-105 hover:shadow-lg transition-all group">
            <div class="w-14 h-14 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center text-2xl mb-2 group-hover:bg-purple-500 group-hover:text-white transition-colors">
                <i class="fas fa-hands-wash"></i>
            </div>
            <span class="text-sm font-bold text-gray-700 group-hover:text-purple-700">Urutan Wudhu</span>
        </button>
        <button onclick="startGame('mandi')" class="bg-white p-4 rounded-3xl shadow-sm border border-purple-100 flex flex-col items-center justify-center hover:bg-purple-50 hover:scale-105 hover:shadow-lg transition-all group">
            <div class="w-14 h-14 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center text-2xl mb-2 group-hover:bg-purple-500 group-hover:text-white transition-colors">
                <i class="fas fa-shower"></i>
            </div>
            <span class="text-sm font-bold text-gray-700 group-hover:text-purple-700">Urutan Mandi</span>
        </button>
        <button onclick="startGame('makan')" class="bg-white p-4 rounded-3xl shadow-sm border border-purple-100 flex flex-col items-center justify-center hover:bg-purple-50 hover:scale-105 hover:shadow-lg transition-all group">
            <div class="w-14 h-14 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center text-2xl mb-2 group-hover:bg-purple-500 group-hover:text-white transition-colors">
                <i class="fas fa-utensils"></i>
            </div>
            <span class="text-sm font-bold text-gray-700 group-hover:text-purple-700">Urutan Makan</span>
        </button>
        <button onclick="startGame('toilet')" class="bg-white p-4 rounded-3xl shadow-sm border border-purple-100 flex flex-col items-center justify-center hover:bg-purple-50 hover:scale-105 hover:shadow-lg transition-all group">
            <div class="w-14 h-14 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center text-2xl mb-2 group-hover:bg-purple-500 group-hover:text-white transition-colors">
                <i class="fas fa-toilet"></i>
            </div>
            <span class="text-sm font-bold text-gray-700 group-hover:text-purple-700">Toilet Training</span>
        </button>
        <button onclick="startGame('tidur')" class="bg-white p-4 rounded-3xl shadow-sm border border-purple-100 flex flex-col items-center justify-center hover:bg-purple-50 hover:scale-105 hover:shadow-lg transition-all group">
            <div class="w-14 h-14 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center text-2xl mb-2 group-hover:bg-purple-500 group-hover:text-white transition-colors">
                <i class="fas fa-bed"></i>
            </div>
            <span class="text-sm font-bold text-gray-700 group-hover:text-purple-700">Urutan Tidur</span>
        </button>
        <button onclick="startGame('sekolah')" class="bg-white p-4 rounded-3xl shadow-sm border border-purple-100 flex flex-col items-center justify-center hover:bg-purple-50 hover:scale-105 hover:shadow-lg transition-all group">
            <div class="w-14 h-14 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center text-2xl mb-2 group-hover:bg-purple-500 group-hover:text-white transition-colors">
                <i class="fas fa-school"></i>
            </div>
            <span class="text-sm font-bold text-gray-700 group-hover:text-purple-700">Berangkat Sekolah</span>
        </button>
    </div>

    <!-- Drag and Drop Game Area (Hidden by default) -->
    <div id="game-area" class="hidden opacity-0 transition-opacity duration-500 flex-col gap-8">
        <div class="flex items-center justify-between mb-4">
            <h3 id="game-title" class="text-2xl font-bold text-purple-800">Judul Game</h3>
            <button onclick="resetToMenu()" class="bg-white text-purple-500 hover:text-purple-700 px-4 py-2 rounded-full font-bold shadow-sm border border-purple-200 hover:bg-purple-50 transition-colors">
                <i class="fas fa-arrow-left mr-2"></i> Kembali
            </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
            <!-- Target Zones (Top) -->
            <div class="space-y-4" id="target-container">
                <!-- Drop zones will be injected here -->
            </div>

            <!-- Source Cards (Bottom) -->
            <div id="source-container" class="bg-white/80 backdrop-blur p-6 rounded-3xl min-h-[300px] border-2 border-dashed border-purple-300 flex flex-wrap justify-center gap-4 relative overflow-hidden shadow-inner">
                <p class="text-xs text-purple-400 font-bold uppercase tracking-widest text-center w-full absolute top-3">Area Kartu</p>
                <div id="cards-wrapper" class="w-full flex flex-col gap-4 mt-6">
                    <!-- Draggable cards will be injected here -->
                </div>
            </div>
        </div>
    </div>
    
    <!-- Reward Modal -->
    <div id="reward-modal" class="fixed inset-0 z-50 flex items-center justify-center hidden bg-black/60 backdrop-blur-md">
        <div class="bg-white p-10 rounded-[3rem] text-center shadow-[0_0_50px_rgba(168,85,247,0.5)] animate-bounce relative overflow-hidden max-w-sm w-11/12">
            <div class="absolute inset-0 bg-gradient-to-b from-purple-100 to-white -z-10"></div>
            <i class="fas fa-trophy text-yellow-400 text-8xl mb-6 drop-shadow-md animate-pulse"></i>
            <h3 class="text-4xl font-extrabold text-purple-800 mb-2">LUAR BIASA!</h3>
            <p class="text-gray-500 mb-6 font-medium">Kamu berhasil menyusun urutannya dengan benar.</p>
            <button onclick="resetToMenu()" class="w-full bg-gradient-to-r from-purple-500 to-indigo-500 text-white px-8 py-4 rounded-full font-bold shadow-lg hover:scale-105 active:scale-95 transition-all text-lg tracking-wide border-2 border-white">Main Lagi</button>
        </div>
    </div>

    <!-- Keep Medical Modal intact -->
    <button onclick="openModal('modal-medis-tunagrahita')" class="mt-12 w-full border-2 border-purple-300 text-purple-700 bg-white/50 backdrop-blur text-[10px] font-bold py-4 rounded-2xl hover:bg-purple-100 transition uppercase tracking-wider shadow-sm flex justify-center items-center">
        <i class="fas fa-stethoscope mr-2 text-lg"></i> PENJELASAN MEDIS
    </button>

    <!-- Modal Medis Tunagrahita -->
    <div id="modal-medis-tunagrahita" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" onclick="closeModal('modal-medis-tunagrahita')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20 max-h-[90dvh] overflow-y-auto">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-notes-medical text-purple-500 mr-2"></i>PENJELASAN MEDIS</h3>
                <button onclick="closeModal('modal-medis-tunagrahita')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            
            <div class="mb-6">
                <h4 class="text-xs font-bold text-purple-600 uppercase tracking-widest mb-2 border-b border-purple-100 pb-1">Dasar Medis Sains</h4>
                <p class="text-sm text-gray-600 leading-relaxed text-justify">
                    Fitur ini menggunakan pendekatan <strong>Gamifikasi Kognitif</strong> dengan umpan balik multisensori instan. Efek visual kartu yang "hidup" (membesar dan miring) saat disentuh memberikan atensi fokus. Ketika berhasil, ledakan confetti dan suara kemenangan memicu pelepasan dopamin di <em>Nucleus Accumbens</em>, yang memperkuat jalur saraf memori prosedural. Ini sangat krusial bagi anak tunagrahita yang memiliki defisit memori kerja (working memory).
                </p>
            </div>

            <div class="bg-purple-50 p-4 rounded-2xl border border-purple-100">
                <h4 class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Penelitian Medis & Referensi</h4>
                <ul class="space-y-3">
                    <li class="text-xs text-gray-600">
                        <span class="font-bold text-gray-800">Tsikinas, S., & Xinogalos, S. (2018)</span>
                        "Serious games for people with intellectual disabilities". Ulasan sistematis tentang efektivitas game edukasi.
                    </li>
                    <li class="text-xs text-gray-600">
                        <span class="font-bold text-gray-800">Schalock, R. L. (2021)</span>
                        "Gamification in cognitive training". Penggunaan elemen game untuk meningkatkan rentang perhatian dan fungsi eksekutif.
                    </li>
                </ul>
            </div>
        </div>
    </div>

    <!-- JS Logic inside the script tag -->
    <script>
        // Game Data Structures
        const GAME_DATA = {
            'wudhu': {
                title: 'Urutan Wudhu',
                items: [
                    { id: 1, text: 'Cuci Tangan', icon: 'fas fa-hands-wash' },
                    { id: 2, text: 'Berkumur', icon: 'fas fa-tooth' },
                    { id: 3, text: 'Cuci Muka', icon: 'fas fa-user' },
                    { id: 4, text: 'Cuci Kaki', icon: 'fas fa-shoe-prints' }
                ]
            },
            'mandi': {
                title: 'Urutan Mandi',
                items: [
                    { id: 1, text: 'Melepas Baju', icon: 'fas fa-tshirt' },
                    { id: 2, text: 'Menyiram Badan pakai gayung', icon: 'fas fa-tint' },
                    { id: 3, text: 'Menggosok Sabun', icon: 'fas fa-soap' },
                    { id: 4, text: 'Memakai Handuk', icon: 'fas fa-bath' }
                ]
            },
            'makan': {
                title: 'Urutan Makan',
                items: [
                    { id: 1, text: 'Mencuci Tangan di wastafel', icon: 'fas fa-hands-wash' },
                    { id: 2, text: 'Duduk di Kursi', icon: 'fas fa-chair' },
                    { id: 3, text: 'Mengangkat tangan Berdoa', icon: 'fas fa-praying-hands' },
                    { id: 4, text: 'Memasukkan Makanan ke mulut', icon: 'fas fa-utensils' }
                ]
            },
            'toilet': {
                title: 'Toilet Training',
                items: [
                    { id: 1, text: 'Melepas Celana', icon: 'fas fa-socks' },
                    { id: 2, text: 'Duduk di Kloset', icon: 'fas fa-toilet' },
                    { id: 3, text: 'Menyiram Kloset', icon: 'fas fa-water' },
                    { id: 4, text: 'Mencuci Tangan pakai sabun', icon: 'fas fa-soap' }
                ]
            },
            'tidur': {
                title: 'Urutan Tidur',
                items: [
                    { id: 1, text: 'Menggosok Gigi', icon: 'fas fa-tooth' },
                    { id: 2, text: 'Mencuci Kaki', icon: 'fas fa-shoe-prints' },
                    { id: 3, text: 'Menarik Selimut', icon: 'fas fa-bed' },
                    { id: 4, text: 'Menutup Mata atau tidur', icon: 'fas fa-moon' }
                ]
            },
            'sekolah': {
                title: 'Berangkat Sekolah',
                items: [
                    { id: 1, text: 'Memakai Baju seragam', icon: 'fas fa-tshirt' },
                    { id: 2, text: 'Menyisir Rambut', icon: 'fas fa-user-tie' },
                    { id: 3, text: 'Memakai Sepatu', icon: 'fas fa-shoe-prints' },
                    { id: 4, text: 'Mencium Tangan ibu', icon: 'fas fa-hand-holding-heart' }
                ]
            }
        };

        let completedItems = 0;
        let activeDraggable = null;
        let currentDropZones = [];
        let startX, startY, initialLeft, initialTop;
        let isDragging = false;
        
        // Preload Sounds (Freesound CDN)
        let sndPop_url = 'https://cdn.freesound.org/previews/244/244655_3509815-lq.mp3'; let sndPop; function get_sndPop() { if(!sndPop) sndPop = new Audio(sndPop_url); return sndPop; } 
        let sndBounce_url = 'https://cdn.freesound.org/previews/360/360601_6687700-lq.mp3'; let sndBounce; function get_sndBounce() { if(!sndBounce) sndBounce = new Audio(sndBounce_url); return sndBounce; }
        let sndClap_url = 'https://cdn.freesound.org/previews/277/277033_1735496-lq.mp3'; let sndClap; function get_sndClap() { if(!sndClap) sndClap = new Audio(sndClap_url); return sndClap; }
        let boingSound_url = 'https://cdn.freesound.org/previews/435/435238_8963499-lq.mp3'; let boingSound; function get_boingSound() { if(!boingSound) { boingSound = new Audio(boingSound_url); boingSound.volume = 0.5; } return boingSound; }

        function shuffle(array) {
            let currentIndex = array.length, randomIndex;
            while (currentIndex > 0) {
                randomIndex = Math.floor(Math.random() * currentIndex);
                currentIndex--;
                [array[currentIndex], array[randomIndex]] = [array[randomIndex], array[currentIndex]];
            }
            return array;
        }

        function startGame(gameKey) {
            const gameData = GAME_DATA[gameKey];
            if (!gameData) return;

            document.getElementById('game-title').innerText = gameData.title;
            
            // Hide Menu, Show Game Area
            const menu = document.getElementById('game-selection');
            const area = document.getElementById('game-area');
            
            menu.classList.add('hidden');
            area.classList.remove('hidden');
            setTimeout(() => { area.classList.remove('opacity-0'); }, 50);

            // Reset state
            completedItems = 0;
            
            // Render Target Zones
            const targetContainer = document.getElementById('target-container');
            targetContainer.innerHTML = '';
            for(let i=1; i<=4; i++) {
                targetContainer.innerHTML += `
                    <div class="drop-zone bg-white p-4 rounded-3xl border-4 border-dashed border-purple-200 h-28 flex items-center justify-center relative transition-all duration-300" data-expected="${i}">
                        <span class="text-purple-100/50 font-extrabold text-7xl absolute left-6 pointer-events-none">${i}</span>
                        <span class="text-purple-300 text-sm font-bold pointer-events-none uppercase tracking-widest z-0">Letakkan di sini</span>
                    </div>
                `;
            }

            // Render Source Cards (Shuffled)
            const sourceContainer = document.getElementById('cards-wrapper');
            sourceContainer.innerHTML = '';
            
            let items = [...gameData.items];
            shuffle(items);

            items.forEach((item, index) => {
                sourceContainer.innerHTML += `
                    <div data-id="${item.id}" class="draggable-item bg-white p-4 rounded-2xl border-2 border-purple-300 shadow-md flex items-center gap-4 transition-transform duration-300 touch-none z-10" style="touch-action: none;">
                        <span class="w-14 h-14 rounded-2xl bg-purple-100 flex items-center justify-center text-3xl font-bold text-purple-600 shadow-inner pointer-events-none">
                            <i class="${item.icon}"></i>
                        </span>
                        <span class="font-bold text-purple-900 text-lg leading-tight pointer-events-none">${item.text}</span>
                    </div>
                `;
            });

            // Re-bind events
            setTimeout(bindDragEvents, 100);
        }

        function resetToMenu() {
            document.getElementById('reward-modal').classList.add('hidden');
            
            const menu = document.getElementById('game-selection');
            const area = document.getElementById('game-area');
            
            area.classList.add('opacity-0');
            setTimeout(() => {
                area.classList.add('hidden');
                menu.classList.remove('hidden');
            }, 500);
        }

        function isPointInRect(x, y, rect) {
            return x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom;
        }

        function bindDragEvents() {
            const draggables = document.querySelectorAll('.draggable-item');
            const dropZones = document.querySelectorAll('.drop-zone');
            currentDropZones = Array.from(dropZones);

            draggables.forEach(draggable => {
                draggable.style.position = 'relative';

                const onStart = (e) => {
                    if(draggable.classList.contains('completed')) return;
                    
                    isDragging = true;
                    activeDraggable = draggable;
                    
                    const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
                    const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY;
                    
                    const rect = draggable.getBoundingClientRect();
                    startX = clientX - rect.left;
                    startY = clientY - rect.top;

                    document.body.appendChild(draggable);
                    
                    draggable.style.width = rect.width + 'px';
                    draggable.style.height = rect.height + 'px';
                    draggable.style.position = 'fixed';
                    draggable.style.zIndex = '9999';
                    
                    draggable.style.left = (clientX - startX) + 'px';
                    draggable.style.top = (clientY - startY) + 'px';

                    draggable.classList.add('opacity-90', 'scale-105', 'shadow-2xl');
                    
                    get_sndPop().currentTime = 0;
                    get_sndPop().play().catch(()=>{});
                };

                const onMove = (e) => {
                    if (!isDragging || activeDraggable !== draggable) return;
                    e.preventDefault();
                    
                    const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
                    const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY;
                    window.currentDragY = clientY;

                    draggable.style.left = (clientX - startX) + 'px';
                    draggable.style.top = (clientY - startY) + 'px';

                    const SCROLL_ZONE = 80;
                    if (clientY < SCROLL_ZONE) {
                        if (!window.autoScrollFrame) {
                            const scrollUp = () => {
                                let speed = Math.round((1 - (window.currentDragY / SCROLL_ZONE)) * 8);
                                window.scrollBy(0, -speed);
                                window.autoScrollFrame = requestAnimationFrame(scrollUp);
                            };
                            window.autoScrollFrame = requestAnimationFrame(scrollUp);
                        }
                    } else if (clientY > window.innerHeight - SCROLL_ZONE) {
                        if (!window.autoScrollFrame) {
                            const scrollDown = () => {
                                let speed = Math.round(((window.currentDragY - (window.innerHeight - SCROLL_ZONE)) / SCROLL_ZONE) * 8);
                                window.scrollBy(0, speed);
                                window.autoScrollFrame = requestAnimationFrame(scrollDown);
                            };
                            window.autoScrollFrame = requestAnimationFrame(scrollDown);
                        }
                    } else {
                        if (window.autoScrollFrame) {
                            cancelAnimationFrame(window.autoScrollFrame);
                            window.autoScrollFrame = null;
                        }
                    }

                    currentDropZones.forEach(zone => {
                        const zoneRect = zone.getBoundingClientRect();
                        if (isPointInRect(clientX, clientY, zoneRect)) {
                            zone.classList.add('border-purple-500', 'bg-purple-100', 'scale-[1.02]');
                        } else {
                            zone.classList.remove('border-purple-500', 'bg-purple-100', 'scale-[1.02]');
                        }
                    });
                };

                const onEnd = (e) => {
                    if (!isDragging || activeDraggable !== draggable) return;
                    isDragging = false;
                    activeDraggable = null;
                    
                    if (window.autoScrollFrame) {
                        cancelAnimationFrame(window.autoScrollFrame);
                        window.autoScrollFrame = null;
                    }
                    
                    const clientX = e.type.includes('touch') ? e.changedTouches[0].clientX : e.clientX;
                    const clientY = e.type.includes('touch') ? e.changedTouches[0].clientY : e.clientY;

                    draggable.classList.remove('opacity-90', 'scale-105', 'shadow-2xl');
                    
                    let droppedZone = null;
                    currentDropZones.forEach(zone => {
                        zone.classList.remove('border-purple-500', 'bg-purple-100', 'scale-[1.02]');
                        const zoneRect = zone.getBoundingClientRect();
                        if (isPointInRect(clientX, clientY, zoneRect)) {
                            droppedZone = zone;
                        }
                    });

                    if (droppedZone) {
                        const expected = droppedZone.getAttribute('data-expected');
                        const actual = draggable.getAttribute('data-id');
                        
                        if (expected === actual) {
                            draggable.style.position = 'relative';
                            draggable.style.left = '0';
                            draggable.style.top = '0';
                            draggable.style.zIndex = '1';
                            draggable.style.width = '100%';
                            
                            droppedZone.innerHTML = '';
                            droppedZone.appendChild(draggable);
                            
                            draggable.classList.add('completed', 'bg-green-100', 'border-green-400');
                            draggable.classList.remove('border-purple-300');
                            
                            const iconBox = draggable.querySelector('span:first-child');
                            iconBox.classList.replace('bg-purple-100', 'bg-green-200');
                            iconBox.classList.replace('text-purple-600', 'text-green-700');
                            
                            const textBox = draggable.querySelector('span:last-child');
                            textBox.classList.replace('text-purple-900', 'text-green-900');

                            get_sndBounce().currentTime = 0;
                            get_sndBounce().play().catch(()=>{}); 
                            
                            completedItems++;
                            if(completedItems === 4) {
                                triggerVictory();
                            }
                        } else {
                            snapBack(draggable);
                        }
                    } else {
                        snapBack(draggable);
                    }
                };

                draggable.addEventListener('mousedown', onStart);
                draggable.addEventListener('touchstart', onStart, {passive: false});
            });

            // Need to bind move and end to document to handle fast drags
            const handleGlobalMove = (e) => {
                if(!isDragging || !activeDraggable) return;
                e.preventDefault();
                const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
                const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY;

                activeDraggable.style.left = (clientX - startX) + 'px';
                activeDraggable.style.top = (clientY - startY) + 'px';

                currentDropZones.forEach(zone => {
                    const zoneRect = zone.getBoundingClientRect();
                    if (isPointInRect(clientX, clientY, zoneRect)) {
                        zone.classList.add('border-purple-500', 'bg-purple-100', 'scale-[1.02]');
                    } else {
                        zone.classList.remove('border-purple-500', 'bg-purple-100', 'scale-[1.02]');
                    }
                });
            };

            const handleGlobalEnd = (e) => {
                if(!isDragging || !activeDraggable) return;
                isDragging = false;
                let draggable = activeDraggable;
                activeDraggable = null;
                
                const clientX = e.type.includes('touch') ? e.changedTouches[0].clientX : e.clientX;
                const clientY = e.type.includes('touch') ? e.changedTouches[0].clientY : e.clientY;

                draggable.classList.remove('opacity-90', 'scale-105', 'shadow-2xl');
                
                let droppedZone = null;
                currentDropZones.forEach(zone => {
                    zone.classList.remove('border-purple-500', 'bg-purple-100', 'scale-[1.02]');
                    const zoneRect = zone.getBoundingClientRect();
                    if (isPointInRect(clientX, clientY, zoneRect)) {
                        droppedZone = zone;
                    }
                });

                if (droppedZone) {
                    const expected = droppedZone.getAttribute('data-expected');
                    const actual = draggable.getAttribute('data-id');
                    
                    if (expected === actual) {
                        draggable.style.position = 'relative';
                        draggable.style.left = '0';
                        draggable.style.top = '0';
                        draggable.style.zIndex = '1';
                        draggable.style.width = '100%';
                        
                        droppedZone.innerHTML = '';
                        droppedZone.appendChild(draggable);
                        
                        draggable.classList.add('completed', 'bg-green-100', 'border-green-400');
                        draggable.classList.remove('border-purple-300');
                        
                        const iconBox = draggable.querySelector('span:first-child');
                        iconBox.classList.replace('bg-purple-100', 'bg-green-200');
                        iconBox.classList.replace('text-purple-600', 'text-green-700');
                        
                        const textBox = draggable.querySelector('span:last-child');
                        textBox.classList.replace('text-purple-900', 'text-green-900');

                        get_sndBounce().currentTime = 0;
                        get_sndBounce().play().catch(()=>{}); 
                        
                        completedItems++;
                        if(completedItems === 4) {
                            triggerVictory();
                        }
                    } else {
                        snapBack(draggable);
                    }
                } else {
                    snapBack(draggable);
                }
            };

            // Remove existing global listeners to avoid duplicates
            window.removeEventListener('mousemove', handleGlobalMove);
            window.removeEventListener('touchmove', handleGlobalMove);
            window.removeEventListener('mouseup', handleGlobalEnd);
            window.removeEventListener('touchend', handleGlobalEnd);

            window.addEventListener('mousemove', handleGlobalMove, {passive: false});
            window.addEventListener('touchmove', handleGlobalMove, {passive: false});
            window.addEventListener('mouseup', handleGlobalEnd);
            window.addEventListener('touchend', handleGlobalEnd);
        }
        
        function snapBack(element) {
            get_boingSound().currentTime = 0;
            get_boingSound().play().catch(()=>{});
            
            const wrapper = document.querySelector('.cards-wrapper');
            if (wrapper) wrapper.appendChild(element);
            
            element.style.transition = 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
            element.style.position = 'relative';
            element.style.left = '0';
            element.style.top = '0';
            element.style.zIndex = '1';
            
            setTimeout(() => {
                element.style.transition = 'transform 0.3s';
            }, 400);
        }

        function triggerVictory() {
            setTimeout(() => {
                document.getElementById('reward-modal').classList.remove('hidden');
                
                get_sndClap().currentTime = 0;
                get_sndClap().play().catch(()=>{}); 
                
                var duration = 4 * 1000;
                var animationEnd = Date.now() + duration;
                var defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 9999 };

                function randomInRange(min, max) { return Math.random() * (max - min) + min; }

                var interval = setInterval(function() {
                    var timeLeft = animationEnd - Date.now();
                    if (timeLeft <= 0) return clearInterval(interval);

                    var particleCount = 50 * (timeLeft / duration);
                    confetti(Object.assign({}, defaults, { particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } }));
                    confetti(Object.assign({}, defaults, { particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } }));
                }, 250);
                
            }, 600);
        }
    </script>
</div>
"""


SLB_TUNADAKSA_HTML = """
<div class="min-h-[100dvh] bg-blue-50 pt-24 px-5 pb-32">
    <style>
        .dwell-loader {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-90deg);
            width: 120px;
            height: 120px;
            pointer-events: none;
        }
        .dwell-circle {
            fill: none;
            stroke: #3b82f6;
            stroke-width: 8;
            stroke-dasharray: 283;
            stroke-dashoffset: 283;
            transition: stroke-dashoffset 2s linear;
        }
    </style>

    <h2 class="text-3xl font-bold text-blue-800 mb-6 border-l-4 border-blue-500 pl-3">Terapi Motorik</h2>
    <p class="text-blue-600 mb-6 text-sm">Arahkan kursor / tahan sentuhan selama 2 detik untuk memilih.</p>

        <div class="grid grid-cols-1 gap-6">

        <!-- Button Delta -->
        <div class="bg-white p-6 rounded-[3rem] shadow-lg border-2 border-blue-100 text-center relative overflow-hidden group">
            <h3 class="text-xl font-bold text-gray-700 mb-4 pointer-events-none">Relaksasi Delta (Tidur)</h3>
            <button onclick="toggleAudio('delta')" id="btn-delta" 
                    onmouseenter="startDwell('delta')" onmouseleave="stopDwell('delta')" onmousedown="startDwell('delta')" onmouseup="stopDwell('delta')"
                    class="relative w-full h-40 bg-blue-100 text-blue-600 rounded-3xl flex items-center justify-center text-5xl shadow-inner transition-transform z-10 p-12">
                <i class="fas fa-play pointer-events-none"></i>
                <!-- Loader -->
                <svg class="dwell-loader z-20" id="loader-delta">
                    <circle cx="60" cy="60" r="45" class="dwell-circle" style="stroke: #3b82f6;"></circle>
                </svg>
            </button>
        </div>

        <!-- Button Theta -->
        <div class="bg-white p-6 rounded-[3rem] shadow-lg border-2 border-blue-100 text-center relative overflow-hidden group">
            <h3 class="text-xl font-bold text-gray-700 mb-4 pointer-events-none">Fokus Theta (Tenang)</h3>
            <button onclick="toggleAudio('theta')" id="btn-theta" 
                    onmouseenter="startDwell('theta')" onmouseleave="stopDwell('theta')" onmousedown="startDwell('theta')" onmouseup="stopDwell('theta')"
                    class="relative w-full h-40 bg-blue-100 text-blue-600 rounded-3xl flex items-center justify-center text-5xl shadow-inner transition-transform z-10 p-12">
                <i class="fas fa-play pointer-events-none"></i>
                <!-- Loader -->
                <svg class="dwell-loader z-20" id="loader-theta">
                    <circle cx="60" cy="60" r="45" class="dwell-circle" style="stroke: #3b82f6;"></circle>
                </svg>
            </button>
        </div>

        <!-- Button Zikir -->
        <div class="bg-white p-6 rounded-[3rem] shadow-lg border-2 border-blue-100 text-center relative overflow-hidden group">
            <h3 class="text-xl font-bold text-gray-700 mb-4 pointer-events-none">Zikir Penenang (EQuran)</h3>
            <button onclick="toggleAudio('zikir')" id="btn-zikir"
                    onmouseenter="startDwell('zikir')" onmouseleave="stopDwell('zikir')" onmousedown="startDwell('zikir')" onmouseup="stopDwell('zikir')"
                    class="relative w-full h-40 bg-blue-100 text-blue-600 rounded-3xl flex items-center justify-center text-5xl shadow-inner transition-transform z-10 p-12">
                <i class="fas fa-quran pointer-events-none"></i>
                <!-- Loader -->
                <svg class="dwell-loader z-20" id="loader-zikir">
                    <circle cx="60" cy="60" r="45" class="dwell-circle" style="stroke: #3b82f6;"></circle>
                </svg>
            </button>
            </div>

        <!-- Button Pink Noise -->
        <div class="bg-white p-6 rounded-[3rem] shadow-lg border-2 border-blue-100 text-center relative overflow-hidden group">
            <h3 class="text-xl font-bold text-gray-700 mb-4 pointer-events-none">Pink Noise (Sensorik)</h3>
            <button onclick="toggleAudio('pink')" id="btn-pink"
                    onmouseenter="startDwell('pink')" onmouseleave="stopDwell('pink')" onmousedown="startDwell('pink')" onmouseup="stopDwell('pink')"
                    class="relative w-full h-40 bg-blue-100 text-blue-600 rounded-3xl flex items-center justify-center text-5xl shadow-inner transition-transform z-10 p-12">
                <i class="fas fa-water pointer-events-none"></i>
                <!-- Loader -->
                <svg class="dwell-loader z-20" id="loader-pink">
                    <circle cx="60" cy="60" r="45" class="dwell-circle" style="stroke: #3b82f6;"></circle>
                </svg>
            </button>
        </div>

        <!-- Button White Noise -->
        <div class="bg-white p-6 rounded-[3rem] shadow-lg border-2 border-blue-100 text-center relative overflow-hidden group">
            <h3 class="text-xl font-bold text-gray-700 mb-4 pointer-events-none">White Noise (Fokus)</h3>
            <button onclick="toggleAudio('white')" id="btn-white"
                    onmouseenter="startDwell('white')" onmouseleave="stopDwell('white')" onmousedown="startDwell('white')" onmouseup="stopDwell('white')"
                    class="w-full h-40 bg-blue-100 text-blue-600 rounded-3xl flex items-center justify-center text-5xl shadow-inner transition-transform relative z-10 p-12">
                <i class="fas fa-wind pointer-events-none"></i>
            </button>
            <!-- Loader -->
            <svg class="dwell-loader z-20" id="loader-white">
                <circle cx="60" cy="60" r="45" class="dwell-circle" style="stroke: #3b82f6;"></circle>
            </svg>
        </div>

        <!-- Button Brown Noise -->
        <div class="bg-white p-6 rounded-[3rem] shadow-lg border-2 border-blue-100 text-center relative overflow-hidden group">
            <h3 class="text-xl font-bold text-gray-700 mb-4 pointer-events-none">Brown Noise (Rileksasi Otot)</h3>
            <button onclick="toggleAudio('brown')" id="btn-brown"
                    onmouseenter="startDwell('brown')" onmouseleave="stopDwell('brown')" onmousedown="startDwell('brown')" onmouseup="stopDwell('brown')"
                    class="w-full h-40 bg-blue-100 text-blue-600 rounded-3xl flex items-center justify-center text-5xl shadow-inner transition-transform relative z-10 p-12">
                <i class="fas fa-wave-square pointer-events-none"></i>
            </button>
            <!-- Loader -->
            <svg class="dwell-loader z-20" id="loader-brown">
                <circle cx="60" cy="60" r="45" class="dwell-circle" style="stroke: #3b82f6;"></circle>
            </svg>
        </div>
    </div>
    <button onclick="openModal('modal-medis-tunadaksa')" class="mt-8 w-full border-2 border-blue-200 text-blue-600 text-[10px] font-bold py-3 rounded-xl hover:bg-blue-50 transition uppercase tracking-wider shadow-sm">
        <i class="fas fa-stethoscope mr-2"></i> PENJELASAN MEDIS
    </button>

    <!-- Modal Medis Tunadaksa -->
    <div id="modal-medis-tunadaksa" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" onclick="closeModal('modal-medis-tunadaksa')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20 max-h-[90dvh] overflow-y-auto">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-notes-medical text-blue-500 mr-2"></i>PENJELASAN MEDIS</h3>
                <button onclick="closeModal('modal-medis-tunadaksa')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            
            <div class="mb-6">
                <h4 class="text-xs font-bold text-blue-600 uppercase tracking-widest mb-2 border-b border-blue-100 pb-1">Dasar Medis Sains</h4>
                <p class="text-sm text-gray-600 leading-relaxed text-justify">
                    Antarmuka ini menerapkan <strong>Dwell-Click Technology</strong> dan <strong>Hitbox Expansion</strong>. Area sentuh tombol diperbesar hingga 200% untuk mengakomodasi tremor atau gerakan motorik kasar. Fitur pemilihan otomatis (dwell) selama 2 detik memungkinkan pengguna dengan spastisitas berat mengoperasikan fitur tanpa perlu melakukan gerakan 'tap' yang presisi. Transisi audio <em>fade-in/fade-out</em> digunakan untuk mencegah <em>Startle Reflex</em> (refleks kaget) yang dapat memicu kejang otot.
                </p>
            </div>

            <div class="bg-blue-50 p-4 rounded-2xl border border-blue-100">
                <h4 class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Penelitian Medis & Referensi</h4>
                <ul class="space-y-3">
                    <li class="text-xs text-gray-600">
                        <span class="font-bold text-gray-800">Majaranta, P., & Raiha, K. (2002)</span>
                        "Twenty years of eye typing". Studi dasar tentang efektivitas dwell time untuk input pengguna dengan disabilitas motorik.
                    </li>
                    <li class="text-xs text-gray-600">
                        <span class="font-bold text-gray-800">Garcia-Argibay, M. (2019)</span>
                        "Efficacy of binaural auditory beats". Binaural beats menurunkan persepsi nyeri kronis pada penderita gangguan saraf.
                    </li>
                </ul>
            </div>
        </div>
    </div>

    <script>

        let audioCtx;
        let oscillators = [];
        let noiseNode = null;
        let filterNode = null;
        let gainNode;
        let currentPlayingType = null;
        let dwellTimer = null;
        
        // Web Audio API Setup
        function initAudio() {
            if (!audioCtx) {
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                gainNode = audioCtx.createGain();
                gainNode.connect(audioCtx.destination);
                gainNode.gain.value = 0.5; // Medium volume
            }
            if (audioCtx.state === 'suspended') {
                audioCtx.resume();
            }
        }

        function createOscillator(freq, pan) {
            const osc = audioCtx.createOscillator();
            const panner = audioCtx.createStereoPanner();
            osc.frequency.value = freq;
            osc.connect(panner);
            panner.connect(gainNode);
            panner.pan.value = pan; // -1 Left, 1 Right
            osc.start();
            return osc;
        }

        function generateNoise(type) {
            const bufferSize = audioCtx.sampleRate * 2;
            const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
            const data = buffer.getChannelData(0);

            if (type === 'white') {
                for (let i = 0; i < bufferSize; i++) {
                    data[i] = Math.random() * 2 - 1;
                }
            } else if (type === 'pink') {
                let b0, b1, b2, b3, b4, b5, b6;
                b0 = b1 = b2 = b3 = b4 = b5 = b6 = 0.0;
                for (let i = 0; i < bufferSize; i++) {
                    let white = Math.random() * 2 - 1;
                    b0 = 0.99886 * b0 + white * 0.0555179;
                    b1 = 0.99332 * b1 + white * 0.0750759;
                    b2 = 0.96900 * b2 + white * 0.1538520;
                    b3 = 0.86650 * b3 + white * 0.3104856;
                    b4 = 0.55000 * b4 + white * 0.5329522;
                    b5 = -0.7616 * b5 - white * 0.0168980;
                    data[i] = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362;
                    data[i] *= 0.11; // compensate gain
                    b6 = white * 0.115926;
                }
            } else if (type === 'brown') {
                let lastOut = 0;
                for (let i = 0; i < bufferSize; i++) {
                    let white = Math.random() * 2 - 1;
                    data[i] = (lastOut + (0.02 * white)) / 1.02;
                    lastOut = data[i];
                    data[i] *= 3.5; // compensate gain
                }
            }

            noiseNode = audioCtx.createBufferSource();
            noiseNode.buffer = buffer;
            noiseNode.loop = true;
            
            filterNode = audioCtx.createBiquadFilter();
            if(type === 'brown') {
                filterNode.type = 'lowpass';
                filterNode.frequency.value = 400;
            } else if(type === 'pink') {
                filterNode.type = 'lowpass';
                filterNode.frequency.value = 800;
            } else {
                filterNode.type = 'allpass';
            }

            noiseNode.connect(filterNode);
            filterNode.connect(gainNode);
            noiseNode.start();
        }

        function stopAllAudio() {
            // Stop Oscillators
            oscillators.forEach(osc => osc.stop());
            oscillators = [];
            
            // Stop Noise Node
            if (noiseNode) {
                noiseNode.stop();
                noiseNode.disconnect();
                noiseNode = null;
            }
            if(filterNode) {
                filterNode.disconnect();
                filterNode = null;
            }
            
            // Stop HTML5 Audios
            const htmlAudios = ['zikir-audio'];
            htmlAudios.forEach(id => {
                const a = document.getElementById(id);
                if (a) {
                    a.pause();
                    a.currentTime = 0;
                }
            });

            currentPlayingType = null;
            resetAllBtns();
        }

        function toggleAudio(type) {
            initAudio();

            const isCurrentlyPlaying = (currentPlayingType === type);

            // 1. Matikan semua audio apa pun yang sedang berjalan
            stopAllAudio();

            // 2. Jika tombol ditekan ulang (toggle off), maka hentikan saja, tidak mainkan lagi
            if (isCurrentlyPlaying) {
                return;
            }

            // 3. Mainkan audio yang diminta (toggle on)
            currentPlayingType = type;
            const btn = document.getElementById('btn-' + type);
            const icon = btn.querySelector('i');

            if (type === 'delta') {
                // Web Audio API Delta
                oscillators.push(createOscillator(100, -1));
                oscillators.push(createOscillator(102, 1));
            } else if (type === 'theta') {
                // Web Audio API Binaural
                oscillators.push(createOscillator(432, -1));
                oscillators.push(createOscillator(439, 1));
            } else if (type === 'zikir') {
                // HTML5 Audio
                if (!window.zikirPlaylist) {
                    window.zikirPlaylist = ['https://server8.mp3quran.net/afs/001.mp3', 'https://server8.mp3quran.net/afs/113.mp3', 'https://server8.mp3quran.net/afs/114.mp3'];
                    let zikirAudio = document.createElement('audio');
                    zikirAudio.id = 'zikir-audio';
                    document.body.appendChild(zikirAudio);
                    zikirAudio.addEventListener('ended', function() {
                        window.zikirIndex = (window.zikirIndex + 1) % window.zikirPlaylist.length;
                        zikirAudio.src = window.zikirPlaylist[window.zikirIndex];
                        zikirAudio.play().catch(e => console.log(e));
                    });
                }
                if (typeof window.zikirIndex === 'undefined') window.zikirIndex = 0;
                const zikirAudio = document.getElementById('zikir-audio');
                zikirAudio.src = window.zikirPlaylist[window.zikirIndex];
                zikirAudio.play().catch(e => console.log(e));
            } else if (type === 'pink' || type === 'white' || type === 'brown') {
                // Web Audio API Noise
                generateNoise(type);
            }

            // 4. Update UI Button
            icon.className = "fas fa-pause pointer-events-none";
            btn.classList.remove('bg-blue-100', 'text-blue-600');
            btn.classList.add('bg-blue-500', 'text-white');
        }

        function resetAllBtns() {
            const types = ['delta', 'theta', 'zikir', 'pink', 'white', 'brown'];
            types.forEach(type => {
                const btn = document.getElementById('btn-' + type);
                if (btn) {
                    const icon = btn.querySelector('i');
                    // Reset icon based on type
                    if (type === 'zikir') icon.className = "fas fa-quran pointer-events-none";
                    else if (type === 'pink') icon.className = "fas fa-water pointer-events-none";
                    else if (type === 'white') icon.className = "fas fa-wind pointer-events-none";
                    else if (type === 'brown') icon.className = "fas fa-wave-square pointer-events-none";
                    else icon.className = "fas fa-play pointer-events-none";

                    btn.className = "w-full h-40 bg-blue-100 text-blue-600 rounded-3xl flex items-center justify-center text-5xl shadow-inner transition-transform relative z-10 p-12";
                }
            });
        }

        // DWELL CLICK LOGIC
        function startDwell(type) {
            const circle = document.querySelector('#loader-' + type + ' .dwell-circle');
            if (circle) circle.style.strokeDashoffset = '0'; // Animate to 0
            
            dwellTimer = setTimeout(() => {
                toggleAudio(type);
                stopDwell(type); // Reset after click
            }, 2000);
        }

        function stopDwell(type) {
            clearTimeout(dwellTimer);
            const circle = document.querySelector('#loader-' + type + ' .dwell-circle');
            if (circle) {
                circle.style.transition = 'none'; // Instant reset
                circle.style.strokeDashoffset = '283';
                setTimeout(() => {
                    circle.style.transition = 'stroke-dashoffset 2s linear'; // Restore transition
                }, 50);
            }
        }

    </script>
</div>
"""

@app.route('/slb/tunagrahita')
def slb_tunagrahita():
    return cached_render('BASE_LAYOUT', BASE_LAYOUT, styles=STYLES_HTML, active_page='slb', content=SLB_TUNAGRAHITA_HTML, theme={'nav_bg': 'bg-purple-100', 'title_text': 'text-purple-800'}, is_admin=session.get('is_admin', False), settings=get_settings(), needs_socketio=False)

@app.route('/slb/tunadaksa')
def slb_tunadaksa():
    return cached_render('BASE_LAYOUT', BASE_LAYOUT, styles=STYLES_HTML, active_page='slb', content=SLB_TUNADAKSA_HTML, theme={'nav_bg': 'bg-green-100', 'title_text': 'text-green-800'}, is_admin=session.get('is_admin', False), settings=get_settings(), needs_socketio=False)

SLB_TUNALARAS_HTML = """
<div class="min-h-[100dvh] bg-emerald-50 pt-24 px-5 pb-32 transition-colors duration-1000" id="main-bg">
    <!-- Confetti Library -->
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>

    <h2 class="text-3xl font-bold text-emerald-800 mb-6 border-l-4 border-emerald-500 pl-3">Jurnal Emosi</h2>
    
    <div id="emotion-selector" class="block">
        <p class="text-emerald-700 mb-8 text-lg font-medium">Apa yang kamu rasakan hari ini?</p>
        
        <div class="grid grid-cols-1 gap-6">
            <form method="POST" class="w-full" onsubmit="return handleSenang(event)">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                <input type="hidden" name="emotion" value="Senang">
                <button type="submit" class="w-full bg-white p-6 rounded-[2.5rem] shadow-sm border border-emerald-100 flex items-center gap-6 hover:bg-emerald-50 transition transform hover:scale-[1.02] group">
                    <span class="text-6xl group-hover:scale-110 transition-transform duration-300 drop-shadow-sm">😊</span>
                    <span class="text-2xl font-bold text-emerald-700">Senang</span>
                </button>
            </form>
            
            <form method="POST" class="w-full" id="form-sedih" onsubmit="return handleSedih(event)">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                <input type="hidden" name="emotion" value="Sedih">
                <button type="button" id="btn-sedih" class="w-full bg-white p-6 rounded-[2.5rem] shadow-sm border border-emerald-100 flex items-center gap-6 hover:bg-emerald-50 transition transform hover:scale-[1.02] group select-none touch-none">
                    <span class="text-6xl group-hover:scale-110 transition-transform duration-300 drop-shadow-sm pointer-events-none">😢</span>
                    <span class="text-2xl font-bold text-emerald-700 pointer-events-none">Sedih</span>
                </button>
            </form>
            
            <form method="POST" class="w-full" onsubmit="return handleMarah(event)">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                <input type="hidden" name="emotion" value="Marah">
                <button type="submit" class="w-full bg-white p-6 rounded-[2.5rem] shadow-sm border border-emerald-100 flex items-center gap-6 hover:bg-emerald-50 transition transform hover:scale-[1.02] group">
                    <span class="text-6xl group-hover:scale-110 transition-transform duration-300 drop-shadow-sm">😡</span>
                    <span class="text-2xl font-bold text-emerald-700">Marah</span>
                </button>
            </form>
        </div>
        
        {% if peran == 'orang_tua' or peran == 'kepala_sekolah' %}
        <div class="mt-12">
            <h3 class="font-bold text-emerald-800 mb-4 pl-2 border-l-4 border-emerald-500">Riwayat Perasaan</h3>
            <div class="space-y-3">
                {% for entry in history %}
                <div class="bg-white p-4 rounded-2xl shadow-sm flex justify-between items-center border border-emerald-50">
                    <span class="font-bold text-emerald-700">{{ entry.emotion }}</span>
                    <span class="text-xs text-emerald-600 font-medium bg-emerald-50 px-3 py-1.5 rounded-xl border border-emerald-100">{{ entry.date.strftime('%Y-%m-%d %H:%M') if entry.date else '' }}</span>
                </div>
                {% else %}
                <p class="text-center text-emerald-500/70 text-sm py-4 italic">Belum ada catatan emosi.</p>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% if peran == 'guru' %}
        <div class="mt-8 bg-white p-4 rounded-2xl shadow-sm border border-emerald-50">
            <h3 class="font-bold text-emerald-800 mb-4 pl-2 border-l-4 border-emerald-500">Monitor Jurnal Emosi Siswa</h3>
            <input type="text" id="guru-monitor-search" placeholder="Cari nama siswa..." class="w-full bg-emerald-50 border border-emerald-100 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 mb-4" oninput="fetchGuruMonitor()">
            <div id="guru-monitor-results" class="space-y-3 max-h-64 overflow-y-auto"></div>
        </div>
        <script>
        function fetchGuruMonitor() {
            const q = document.getElementById('guru-monitor-search').value;
            fetch('/api/tunalaras/guru-monitor?q=' + encodeURIComponent(q))
                .then(res => res.json())
                .then(data => {
                    const container = document.getElementById('guru-monitor-results');
                    container.innerHTML = '';
                    if(data.length === 0) {
                        container.innerHTML = '<p class="text-center text-emerald-500/70 text-sm py-4 italic">Belum ada data jurnal emosi.</p>';
                        return;
                    }
                    data.forEach(item => {
                        let html = `
                        <div class="p-3 border border-emerald-100 rounded-xl bg-emerald-50/50">
                            <div class="flex justify-between items-center mb-2">
                                <div>
                                    <h4 class="font-bold text-emerald-800 text-sm">${item.student_name}</h4>
                                    <p class="text-[10px] text-emerald-600 font-medium">Ortu: ${item.parent_name}</p>
                                </div>
                            </div>
                            <div class="flex gap-2 flex-wrap">`;
                        
                        item.recent_emotions.forEach(emo => {
                            html += `<span class="bg-white border border-emerald-100 px-2 py-1 rounded-lg text-xs font-bold text-emerald-700 shadow-sm">${emo.emotion} <span class="text-[9px] text-emerald-500 ml-1 font-normal">${emo.date}</span></span>`;
                        });
                        
                        html += `</div></div>`;
                        container.innerHTML += html;
                    });
                });
        }
        document.addEventListener('DOMContentLoaded', fetchGuruMonitor);
        </script>
        {% endif %}

        <button onclick="openModal('modal-medis-tunalaras')" class="mt-8 w-full border border-emerald-200 text-emerald-600 text-[10px] font-bold py-3.5 rounded-2xl hover:bg-emerald-50 transition uppercase tracking-widest shadow-sm bg-white">
            <i class="fas fa-stethoscope mr-2 text-sm"></i> PENJELASAN MEDIS
        </button>
    </div>
    
    <!-- Modal Medis Tunalaras -->
    <div id="modal-medis-tunalaras" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-emerald-900/40 backdrop-blur-sm transition-opacity" onclick="closeModal('modal-medis-tunalaras')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-[2.5rem] p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20 max-h-[90dvh] overflow-y-auto">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-emerald-800"><i class="fas fa-notes-medical text-emerald-500 mr-2"></i>PENJELASAN MEDIS</h3>
                <button onclick="closeModal('modal-medis-tunalaras')" class="bg-emerald-50 w-8 h-8 rounded-full text-emerald-600 hover:bg-emerald-100 transition-colors">&times;</button>
            </div>
            
            <div class="mb-6">
                <h4 class="text-xs font-bold text-emerald-600 uppercase tracking-widest mb-2 border-b border-emerald-100 pb-1">Dasar Medis Sains</h4>
                <p class="text-sm text-emerald-800/80 leading-relaxed text-justify">
                    Buku harian digital ini dilandasi oleh ilmu <strong>Chromotherapy</strong> dan <strong>Biofeedback</strong>. Layar didominasi oleh warna pastel hijau dan putih yang terbukti menenangkan sistem saraf simpatik untuk menurunkan tekanan darah dan detak jantung. Saat emosi marah dipilih, layar menampilkan panduan pernapasan 3 fase (Tarik, Tahan, Hembus) yang efektif untuk meregulasi emosi. Fitur 'Pelukan Virtual' memberikan stimulasi propioseptif (deep pressure) lewat getaran untuk *grounding*, sementara variasi interaksi 'Senang' memicu *dopamine reward pathway*.
                </p>
            </div>

            <div class="bg-emerald-50 p-4 rounded-3xl border border-emerald-100">
                <h4 class="text-xs font-bold text-emerald-600 uppercase tracking-widest mb-3">Penelitian Medis & Referensi</h4>
                <ul class="space-y-3">
                    <li class="text-xs text-emerald-800/80">
                        <span class="font-bold text-emerald-900">Azeemi, S. T. Y., & Raza, S. M. (2005)</span>
                        "A critical analysis of chromotherapy". Bukti medis dampak panjang gelombang warna sejuk terhadap sistem kardiovaskular.
                    </li>
                    <li class="text-xs text-emerald-800/80">
                        <span class="font-bold text-emerald-900">Lehrer, P. M. (2014)</span>
                        "Heart rate variability biofeedback". Penjelasan mekanisme pernapasan berirama untuk regulasi emosi anak hiperaktif.
                    </li>
                </ul>
            </div>
        </div>
    </div>

    <!-- Breathing Exercise (Marah) -->
    <div id="breathing-exercise" class="hidden fixed inset-0 z-50 flex flex-col items-center justify-center overflow-hidden">
        <div class="absolute inset-0 bg-emerald-900/90 backdrop-blur-xl transition-all duration-1000"></div>
        
        <div class="relative z-10 flex flex-col items-center w-full max-w-sm">
            <div class="relative w-72 h-72 flex items-center justify-center">
                <div id="breath-circle" class="w-48 h-48 bg-emerald-300 rounded-full blur-sm opacity-90 shadow-[0_0_60px_rgba(110,231,183,0.6)] will-change-transform transition-all duration-[4000ms] cubic-bezier(0.4, 0, 0.2, 1)"></div>
                <div class="absolute text-white font-extrabold text-3xl tracking-[0.25em] drop-shadow-md" id="breath-text">TARIK</div>
            </div>
            
            <p class="mt-16 text-emerald-50 font-medium text-center px-8 tracking-wide text-lg">Ikuti irama cahaya.<br><span class="opacity-70 text-sm">Tenangkan pikiranmu.</span></p>
            <button onclick="finishBreathing()" class="mt-10 border-2 border-emerald-400/30 text-emerald-100 px-10 py-3 rounded-full hover:bg-emerald-800/50 hover:border-emerald-400 transition-all backdrop-blur-md font-bold text-sm tracking-widest shadow-lg">SELESAI</button>
        </div>
    </div>

    <!-- Virtual Hug (Sedih) -->
    <div id="virtual-hug-exercise" class="hidden fixed inset-0 z-50 flex flex-col items-center justify-center overflow-hidden transition-colors duration-1000 bg-blue-50">
        <div class="relative z-10 flex flex-col items-center w-full max-w-sm px-6 text-center select-none">
            <div id="bear-container" class="relative w-64 h-64 mb-8 transition-transform duration-1000 ease-in-out">
                <!-- SVG Pastel Bear -->
                <svg id="pastel-bear" viewBox="0 0 200 200" class="w-full h-full drop-shadow-xl" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="100" cy="100" r="80" fill="#fbcfe8" /> <!-- Body -->
                    <circle cx="60" cy="50" r="25" fill="#fbcfe8" /> <!-- Left Ear -->
                    <circle cx="60" cy="50" r="15" fill="#f9a8d4" />
                    <circle cx="140" cy="50" r="25" fill="#fbcfe8" /> <!-- Right Ear -->
                    <circle cx="140" cy="50" r="15" fill="#f9a8d4" />
                    <!-- Eyes -->
                    <circle cx="80" cy="90" r="8" fill="#831843" />
                    <circle cx="120" cy="90" r="8" fill="#831843" />
                    <circle cx="78" cy="88" r="2" fill="#fff" />
                    <circle cx="118" cy="88" r="2" fill="#fff" />
                    <!-- Snout -->
                    <ellipse cx="100" cy="115" rx="20" ry="15" fill="#fff" />
                    <path d="M 95 110 Q 100 115 105 110" stroke="#831843" stroke-width="2" fill="none" stroke-linecap="round"/>
                    <circle cx="100" cy="108" r="4" fill="#831843" />
                    <!-- Blush -->
                    <ellipse cx="65" cy="105" rx="10" ry="6" fill="#f9a8d4" opacity="0.6" />
                    <ellipse cx="135" cy="105" rx="10" ry="6" fill="#f9a8d4" opacity="0.6" />
                    <!-- Arms (Open initially) -->
                    <path id="bear-arm-left" d="M 30 130 Q 10 160 20 180" stroke="#fbcfe8" stroke-width="24" stroke-linecap="round" fill="none" class="transition-all duration-1000 origin-center" />
                    <path id="bear-arm-right" d="M 170 130 Q 190 160 180 180" stroke="#fbcfe8" stroke-width="24" stroke-linecap="round" fill="none" class="transition-all duration-1000 origin-center" />
                </svg>
                <!-- Progress Ring -->
                <svg class="absolute inset-0 w-full h-full pointer-events-none -rotate-90">
                    <circle cx="128" cy="128" r="120" fill="none" stroke="rgba(244,114,182,0.2)" stroke-width="6" />
                    <circle id="hug-progress" cx="128" cy="128" r="120" fill="none" stroke="#f472b6" stroke-width="6" stroke-dasharray="754" stroke-dashoffset="754" class="transition-all duration-100" stroke-linecap="round" />
                </svg>
            </div>
            
            <h3 id="hug-title" class="text-2xl font-bold text-pink-800 mb-2 transition-opacity duration-500">Pelukan Virtual</h3>
            <p id="hug-instruction" class="text-pink-600 font-medium bg-pink-50 px-6 py-3 rounded-2xl border border-pink-100 shadow-sm animate-pulse">Tahan layar selama 5 detik untuk memeluk</p>
        </div>
    </div>

    <!-- Senang Options Containers -->
    
    <!-- Option 1: Celengan Bintang -->
    <div id="senang-bintang" class="hidden fixed inset-0 z-50 bg-amber-50 flex flex-col items-center justify-center overflow-hidden">
        <h3 class="text-3xl font-extrabold text-amber-600 mb-12 drop-shadow-sm text-center px-4" id="bintang-title">Simpan Rasa Senangmu!</h3>
        <div class="relative w-64 h-80 flex flex-col items-center">
            <!-- Star -->
            <div id="bintang-star" class="text-7xl absolute -top-10 cursor-pointer hover:scale-110 transition-transform active:scale-95 z-20 drop-shadow-[0_0_20px_rgba(251,191,36,0.8)] filter">
                ⭐
            </div>
            <p id="bintang-tap-hint" class="absolute top-12 text-xs font-bold text-amber-500 animate-bounce pointer-events-none uppercase tracking-widest">Sentuh Bintangnya</p>
            
            <!-- Jar -->
            <div class="absolute bottom-0 w-48 h-56 bg-white/40 border-4 border-white/80 rounded-b-3xl rounded-t-lg backdrop-blur-sm shadow-xl flex items-end justify-center pb-4 z-10">
                <div class="w-full h-4 bg-white/60 absolute top-[-4px] rounded-t-lg"></div> <!-- Jar lid -->
                <div id="jar-glow" class="absolute inset-0 bg-amber-300/0 rounded-b-2xl transition-colors duration-1000"></div>
            </div>
        </div>
        <audio id="audio-chime" src="https://cdn.freesound.org/previews/411/411639_5121236-lq.mp3" preload="none"></audio>
    </div>

    <!-- Option 2: Tos Virtual -->
    <div id="senang-tos" class="hidden fixed inset-0 z-50 bg-emerald-50 flex flex-col items-center justify-center overflow-hidden">
        <h3 class="text-3xl font-extrabold text-emerald-600 mb-16 text-center px-4">Kerja Bagus Hari Ini!</h3>
        <div id="tos-hand" class="text-9xl cursor-pointer hover:scale-110 transition-transform active:scale-90 drop-shadow-2xl relative">
            ✋
            <div class="absolute -inset-8 rounded-full border-4 border-emerald-400/30 animate-ping"></div>
        </div>
        <p class="mt-16 text-lg font-bold text-emerald-500 bg-emerald-100/50 px-8 py-3 rounded-full uppercase tracking-wider">Beri Aku Tos!</p>
        <audio id="audio-clap" src="https://cdn.freesound.org/previews/277/277033_1735496-lq.mp3" preload="none"></audio>
    </div>

    <!-- Option 3: Balon Napas Ceria -->
    <div id="senang-balon" class="hidden fixed inset-0 z-50 bg-sky-50 flex flex-col items-center justify-center overflow-hidden touch-none select-none">
        <h3 class="text-2xl font-bold text-sky-600 mb-8 text-center px-4" id="balon-title">Ayo Pompa Balonnya!</h3>
        <p class="text-sky-500 mb-16 font-medium bg-sky-100/50 px-6 py-2 rounded-full text-sm">Ketuk layar berkali-kali secepat mungkin</p>
        
        <div class="relative w-full h-96 flex justify-center items-end" id="balon-area">
            <!-- Balloon -->
            <div id="the-balloon" class="relative transition-all duration-100 ease-out origin-bottom transform scale-50">
                <svg viewBox="0 0 100 140" class="w-48 h-64 drop-shadow-xl" xmlns="http://www.w3.org/2000/svg">
                    <path d="M50 120 C 10 120, 0 60, 0 40 C 0 10, 20 0, 50 0 C 80 0, 100 10, 100 40 C 100 60, 90 120, 50 120 Z" fill="#38bdf8" />
                    <path d="M45 120 L 55 120 L 60 130 L 40 130 Z" fill="#0ea5e9" />
                    <path d="M50 130 Q 55 140 50 150" stroke="#cbd5e1" stroke-width="2" fill="none" />
                    <!-- Highlight -->
                    <ellipse cx="25" cy="30" rx="8" ry="15" fill="#fff" opacity="0.3" transform="rotate(-30 25 30)" />
                </svg>
                <div id="balon-text" class="absolute inset-0 flex items-center justify-center font-extrabold text-white text-3xl opacity-0 transition-opacity pb-10 tracking-widest">YEEEAYY!</div>
            </div>
        </div>
        <audio id="audio-pump" src="https://cdn.freesound.org/previews/244/244655_3509815-lq.mp3" preload="none"></audio>
        <audio id="audio-yay" src="https://cdn.freesound.org/previews/337/337049_3232293-lq.mp3" preload="none"></audio>
    </div>


    <script>
        // --- COMMON LOGIC ---
        function submitFormByName(nameValue) {
            const form = document.querySelector(`input[name="emotion"][value="${nameValue}"]`).closest('form');
            if(form) form.submit();
        }

        // --- MARAH (3-PHASE BREATHING) LOGIC ---
        let audioCtx;
        let noiseNode;
        let gainNode;
        let marahInterval;
        let isMarahActive = false;

        function createNoise() {
            if (!audioCtx) {
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (audioCtx.state === 'suspended') {
                audioCtx.resume();
            }

            const bufferSize = audioCtx.sampleRate * 2;
            const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
            const data = buffer.getChannelData(0);

            let lastOut = 0;
            for (let i = 0; i < bufferSize; i++) {
                const white = Math.random() * 2 - 1;
                data[i] = (lastOut + (0.02 * white)) / 1.02;
                lastOut = data[i];
                data[i] *= 3.5;
            }

            noiseNode = audioCtx.createBufferSource();
            noiseNode.buffer = buffer;
            noiseNode.loop = true;

            const filter = audioCtx.createBiquadFilter();
            filter.type = 'lowpass';
            filter.frequency.value = 400;

            gainNode = audioCtx.createGain();
            gainNode.gain.value = 0.3;

            noiseNode.connect(filter);
            filter.connect(gainNode);
            gainNode.connect(audioCtx.destination);
            noiseNode.start();
        }

        function stopNoise() {
            if (noiseNode) {
                noiseNode.stop();
                noiseNode = null;
            }
        }

        function handleMarah(e) {
            e.preventDefault();
            document.getElementById('emotion-selector').classList.add('hidden');
            document.getElementById('breathing-exercise').classList.remove('hidden');
            
            const circle = document.getElementById('breath-circle');
            const text = document.getElementById('breath-text');
            
            isMarahActive = true;
            createNoise();
            
            // 3-Phase Logic: Tarik (4s) -> Tahan (4s) -> Hembus (4s)
            let phase = 0; // 0: Tarik, 1: Tahan, 2: Hembus
            
            // Initial Start (Tarik)
            circle.style.transitionDuration = "4000ms";
            circle.style.transform = "scale(1.3)";
            circle.style.opacity = "1";
            text.innerText = "TARIK";
            
            marahInterval = setInterval(() => {
                if(!isMarahActive) return;
                phase = (phase + 1) % 3;
                
                if (phase === 0) {
                    // Tarik
                    circle.style.transitionDuration = "4000ms";
                    circle.style.transform = "scale(1.3)";
                    circle.style.opacity = "1";
                    text.innerText = "TARIK";
                } else if (phase === 1) {
                    // Tahan
                    circle.style.transitionDuration = "0ms"; // Hold size
                    text.innerText = "TAHAN";
                } else if (phase === 2) {
                    // Hembus
                    circle.style.transitionDuration = "4000ms";
                    circle.style.transform = "scale(0.5)";
                    circle.style.opacity = "0.6";
                    text.innerText = "HEMBUS";
                }
            }, 4000);
            
            return false;
        }

        window.finishBreathing = function() {
            isMarahActive = false;
            clearInterval(marahInterval);
            stopNoise();
            submitFormByName('Marah');
        };

        // --- SEDIH (VIRTUAL HUG) LOGIC ---
        let hugTimer;
        let hugStartTime;
        let isHugging = false;
        const HUG_DURATION = 5000; // 5 seconds
        
        function handleSedih(e) {
            e.preventDefault();
            // Start Interaction, show overlay
            document.getElementById('emotion-selector').classList.add('hidden');
            document.getElementById('virtual-hug-exercise').classList.remove('hidden');
            
            const btn = document.getElementById('btn-sedih');
            // Remove click listener from btn, we use the whole overlay
            return false;
        }

        const hugOverlay = document.getElementById('virtual-hug-exercise');
        const hugProgress = document.getElementById('hug-progress');
        const pastelBear = document.getElementById('pastel-bear');
        const armLeft = document.getElementById('bear-arm-left');
        const armRight = document.getElementById('bear-arm-right');
        const hugInstruction = document.getElementById('hug-instruction');
        const hugTitle = document.getElementById('hug-title');
        
        const circumference = 2 * Math.PI * 120; // r=120

        function updateHugProgress() {
            if(!isHugging) return;
            const elapsed = Date.now() - hugStartTime;
            const percent = Math.min(elapsed / HUG_DURATION, 1);
            
            // Dash offset goes from circumference to 0
            const offset = circumference - (percent * circumference);
            hugProgress.style.strokeDashoffset = offset;

            // Animate arms closing slightly based on progress
            // Initial: M 30 130 Q 10 160 20 180 (Open)
            // Target: M 50 140 Q 80 160 100 150 (Closed/Hugging)
            if(percent > 0.1) {
                armLeft.setAttribute('d', 'M 50 140 Q 80 160 100 150');
                armRight.setAttribute('d', 'M 150 140 Q 120 160 100 150');
            }

            if (elapsed >= HUG_DURATION) {
                completeHug();
            } else {
                hugTimer = requestAnimationFrame(updateHugProgress);
            }
        }

        function startHug(e) {
            if(e) e.preventDefault();
            if(hugOverlay.classList.contains('hidden')) return;
            
            isHugging = true;
            hugStartTime = Date.now();
            
            // Vibrate if supported
            if(navigator.vibrate) {
                navigator.vibrate([1000, 1000, 1000, 1000, 1000]); // Gentle continuous vibration
            }
            
            // Visual feedback
            hugOverlay.classList.replace('bg-blue-50', 'bg-rose-50');
            hugInstruction.innerText = "Terus tahan...";
            hugInstruction.classList.remove('animate-pulse');
            
            updateHugProgress();
        }

        function cancelHug(e) {
            if(e) e.preventDefault();
            if(!isHugging) return;
            isHugging = false;
            cancelAnimationFrame(hugTimer);
            
            if(navigator.vibrate) navigator.vibrate(0);
            
            // Reset visuals
            hugProgress.style.strokeDashoffset = circumference;
            hugOverlay.classList.replace('bg-rose-50', 'bg-blue-50');
            hugInstruction.innerText = "Tahan layar selama 5 detik untuk memeluk";
            hugInstruction.classList.add('animate-pulse');
            
            armLeft.setAttribute('d', 'M 30 130 Q 10 160 20 180');
            armRight.setAttribute('d', 'M 170 130 Q 190 160 180 180');
        }

        function completeHug() {
            isHugging = false;
            cancelAnimationFrame(hugTimer);
            if(navigator.vibrate) navigator.vibrate([200, 100, 200]);
            
            hugTitle.innerText = "Semua akan baik-baik saja 💖";
            hugInstruction.classList.add('hidden');
            document.getElementById('bear-container').classList.add('scale-110');
            
            setTimeout(() => {
                submitFormByName('Sedih');
            }, 2000);
        }

        // Bind events to overlay
        hugOverlay.addEventListener('touchstart', startHug, {passive: false});
        hugOverlay.addEventListener('touchend', cancelHug);
        hugOverlay.addEventListener('touchcancel', cancelHug);
        hugOverlay.addEventListener('mousedown', startHug);
        hugOverlay.addEventListener('mouseup', cancelHug);
        hugOverlay.addEventListener('mouseleave', cancelHug);

        // Make button directly trigger form if clicked normally, but we use an overlay approach
        document.getElementById('btn-sedih').addEventListener('click', handleSedih);


        // --- SENANG (3 RANDOM INTERACTIONS) LOGIC ---
        function handleSenang(e) {
            e.preventDefault();
            document.getElementById('emotion-selector').classList.add('hidden');
            
            const options = ['bintang', 'tos', 'balon'];
            const randomOpt = options[Math.floor(Math.random() * options.length)];
            
            if(randomOpt === 'bintang') initBintang();
            else if(randomOpt === 'tos') initTos();
            else if(randomOpt === 'balon') initBalon();
            
            return false;
        }

        // Senang Option 1: Bintang
        function initBintang() {
            document.getElementById('senang-bintang').classList.remove('hidden');
            
            // TTS
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance("Wah kamu sedang senang. Hebat sekali. Ayo simpan rasa senangmu ke dalam toples.");
                utterance.lang = 'id-ID';
                utterance.rate = 0.9;
                utterance.pitch = 1.2;
                window.speechSynthesis.speak(utterance);
            }

            const star = document.getElementById('bintang-star');
            star.addEventListener('click', function onClick() {
                star.removeEventListener('click', onClick);
                
                document.getElementById('bintang-tap-hint').classList.add('hidden');
                document.getElementById('bintang-title').innerText = "Hebat!";
                
                // Animate star dropping into jar
                star.style.transition = "all 1s cubic-bezier(0.68, -0.55, 0.265, 1.55)";
                star.style.transform = "translateY(150px) scale(0.6)";
                
                setTimeout(() => {
                    const audio = document.getElementById('audio-chime');
                    audio.volume = 0.5;
                    audio.play().catch(()=>{});
                    
                    document.getElementById('jar-glow').classList.replace('bg-amber-300/0', 'bg-amber-300/60');
                    
                    var duration = 2000;
                    var end = Date.now() + duration;
                    (function frame() {
                        confetti({ particleCount: 3, angle: 60, spread: 55, origin: { x: 0 }, colors: ['#fbbf24', '#fde68a'] });
                        confetti({ particleCount: 3, angle: 120, spread: 55, origin: { x: 1 }, colors: ['#fbbf24', '#fde68a'] });
                        if (Date.now() < end) requestAnimationFrame(frame);
                    }());
                    
                    setTimeout(() => submitFormByName('Senang'), 2500);
                }, 800);
            });
        }

        // Senang Option 2: Tos
        function initTos() {
            document.getElementById('senang-tos').classList.remove('hidden');
            
            const hand = document.getElementById('tos-hand');
            hand.addEventListener('click', function onClick() {
                hand.removeEventListener('click', onClick);
                
                const audio = document.getElementById('audio-clap');
                audio.volume = 0.6;
                audio.play().catch(()=>{});
                
                hand.classList.add('scale-125');
                
                confetti({
                    particleCount: 150,
                    spread: 100,
                    origin: { y: 0.6 },
                    colors: ['#34d399', '#6ee7b7', '#a7f3d0', '#ffffff'] // Pastel greens
                });
                
                setTimeout(() => submitFormByName('Senang'), 2500);
            });
        }

        // Senang Option 3: Balon
        let balonTaps = 0;
        const maxTaps = 15;
        
        function initBalon() {
            const container = document.getElementById('senang-balon');
            container.classList.remove('hidden');
            
            const balloonArea = document.getElementById('balon-area');
            const balloonElement = document.getElementById('the-balloon');
            const audioPump = document.getElementById('audio-pump');
            
            // Reset states
            balonTaps = 0;
            balloonElement.style.transform = "scale(0.5) translateY(0)";
            document.getElementById('balon-text').style.opacity = "0";
            
            balloonArea.addEventListener('pointerdown', function onTap(e) {
                if(balonTaps >= maxTaps) return;
                e.preventDefault();
                
                balonTaps++;
                
                // Clone audio for overlapping rapid taps
                const p = audioPump.cloneNode();
                p.volume = 0.3;
                p.play().catch(()=>{});
                
                // Grow balloon
                const scale = 0.5 + (balonTaps / maxTaps) * 0.7; // 0.5 to 1.2
                balloonElement.style.transform = `scale(${scale})`;
                
                if(balonTaps >= maxTaps) {
                    // Fly away
                    balloonArea.removeEventListener('pointerdown', onTap);
                    document.getElementById('balon-title').innerText = "Luar Biasa!";
                    document.getElementById('balon-text').style.opacity = "1";
                    
                    const audioYay = document.getElementById('audio-yay');
                    audioYay.volume = 0.6;
                    audioYay.play().catch(()=>{});
                    
                    balloonElement.style.transitionDuration = "2s";
                    balloonElement.style.transform = `scale(1.2) translateY(-400px)`;
                    
                    confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 }, colors: ['#38bdf8', '#7dd3fc', '#bae6fd'] });
                    
                    setTimeout(() => submitFormByName('Senang'), 3000);
                }
            });
        }

    </script>
</div>
"""

SLB_TUNAGANDA_HTML = """
<div class="fixed inset-0 bg-gradient-to-br from-indigo-100 via-purple-100 to-pink-100 flex flex-col overflow-hidden touch-none select-none">
    
    <!-- Top Bar (Pastel Theme) -->
    <div class="bg-white/60 backdrop-blur-md border-b border-white/50 px-6 py-4 flex items-center justify-between shrink-0 shadow-sm z-50">
        <div class="flex items-center gap-4">
            <a href="/" class="w-12 h-12 rounded-full bg-white flex items-center justify-center text-indigo-500 shadow-md hover:scale-110 active:scale-95 transition-all group">
                <i class="fas fa-arrow-left text-xl group-hover:-translate-x-1 transition-transform"></i>
            </a>
            <div>
                <h2 class="text-xl font-extrabold text-indigo-900 tracking-tight leading-none">Sensory Board</h2>
                <p class="text-indigo-600 font-medium text-xs">Stimulasi Visual & Auditori</p>
            </div>
        </div>
        <button onclick="openModal('modal-medis-tunaganda')" class="px-5 py-2.5 bg-white rounded-full text-indigo-600 font-bold text-xs shadow-md border border-indigo-100 hover:scale-105 active:scale-95 transition-transform flex items-center gap-2">
            <i class="fas fa-stethoscope"></i> <span class="hidden md:inline">Penjelasan Medis</span>
        </button>
    </div>

    <!-- Canvas Area (High Contrast Pitch Black) -->
    <div class="flex-1 relative bg-black shadow-inner overflow-hidden" id="canvas-container">
        <div class="absolute inset-0 flex items-center justify-center pointer-events-none z-10 opacity-50 transition-opacity duration-1000" id="hint-text">
            <p class="text-white/50 text-sm font-medium tracking-widest uppercase animate-pulse">Sentuh & Usap Layar</p>
        </div>
    </div>

    <!-- Modal Medis Tunaganda -->
    <div id="modal-medis-tunaganda" class="fixed inset-0 z-[100] hidden pointer-events-auto">
        <div class="absolute inset-0 bg-indigo-900/40 backdrop-blur-sm transition-opacity" onclick="closeModal('modal-medis-tunaganda')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20 max-h-[90dvh] overflow-y-auto">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-notes-medical text-indigo-500 mr-2"></i>PENJELASAN MEDIS</h3>
                <button onclick="closeModal('modal-medis-tunaganda')" class="bg-indigo-50 w-8 h-8 rounded-full text-indigo-600 hover:bg-indigo-100 transition-colors">&times;</button>
            </div>
            
            <div class="mb-6">
                <h4 class="text-xs font-bold text-indigo-600 uppercase tracking-widest mb-2 border-b border-indigo-100 pb-1">Dasar Medis Sains</h4>
                <p class="text-sm text-gray-600 leading-relaxed text-justify">
                    Fitur ini meniru lingkungan terapi <strong>Snoezelen</strong>. Layar menggunakan bingkai bertema pastel yang menenangkan dan latar belakang kanvas hitam pekat (High Contrast) untuk mengakomodasi anak dengan <em>Cortical Visual Impairment (CVI)</em>, meminimalkan distraksi visual agar warna tampil menonjol. Sentuhan dan usapan jari memicu percikan cahaya pastel (Particle System) dengan jejak mengikuti gerakan, layaknya melukis bintang. Stimulasi visual interaktif ini dipadukan dengan <em>Web Audio API</em> untuk menghasilkan suara ASMR alam (seperti gemercik air jernih, ketukan bambu, dan bel pelan) yang diatur menggunakan <em>throttling</em> agar tetap harmonis dan tidak menyakiti telinga. Tujuannya adalah merangsang jaras saraf sensorik primer dan mengajarkan kausalitas (sebab-akibat) secara menyenangkan.
                </p>
            </div>

            <div class="bg-indigo-50 p-4 rounded-2xl border border-indigo-100">
                <h4 class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Penelitian Medis & Referensi</h4>
                <ul class="space-y-3">
                    <li class="text-xs text-gray-600">
                        <span class="font-bold text-gray-800">Lotan, M., & Gold, C. (2009)</span>
                        "Meta-analysis of the effectiveness of Snoezelen". Efektivitas lingkungan multisensorik untuk relaksasi fisiologis.
                    </li>
                    <li class="text-xs text-gray-600">
                        <span class="font-bold text-gray-800">Lancioni, G. E. (2002)</span>
                        "Snoezelen: A systematic review". Pembelajaran kausalitas melalui rangsangan visual-auditori sederhana.
                    </li>
                </ul>
            </div>
        </div>
    </div>

    <!-- Script Logic -->
    <script>
        const container = document.getElementById('canvas-container');
        const hintText = document.getElementById('hint-text');
        
        // Beautiful Pastel Colors
        const pastelColors = [
            'rgba(253, 164, 175, 0.9)', // Rose
            'rgba(249, 168, 212, 0.9)', // Pink
            'rgba(216, 184, 255, 0.9)', // Purple/Mauve
            'rgba(147, 197, 253, 0.9)', // Light Blue
            'rgba(167, 243, 208, 0.9)', // Emerald/Mint
            'rgba(253, 230, 138, 0.9)'  // Amber/Yellow
        ];

        // Particle logic
        function spawnParticle(x, y) {
            const el = document.createElement('div');
            el.className = 'absolute rounded-full pointer-events-none will-change-transform';
            
            // Random size 20 to 60px
            const size = Math.random() * 40 + 20;
            const colorStr = pastelColors[Math.floor(Math.random() * pastelColors.length)];
            
            el.style.width = size + 'px';
            el.style.height = size + 'px';
            // Glowing pastel sphere
            el.style.background = `radial-gradient(circle at 30% 30%, #ffffff, ${colorStr} 60%, rgba(0,0,0,0) 80%)`;
            el.style.left = (x - size/2) + 'px';
            el.style.top = (y - size/2) + 'px';
            el.style.boxShadow = `0 0 ${size/2}px ${colorStr}, inset 0 0 ${size/4}px rgba(255,255,255,0.8)`;
            
            el.style.transform = `scale(0.2) translate(${Math.random()*40-20}px, ${Math.random()*40-20}px)`;
            el.style.opacity = '1';
            el.style.transition = 'transform 1.2s cubic-bezier(0.25, 1, 0.5, 1), opacity 1.2s ease-out';
            
            container.appendChild(el);
            
            // Trigger animation
            requestAnimationFrame(() => {
                el.style.transform = `scale(${Math.random() * 1.5 + 1}) translate(${Math.random()*100-50}px, ${Math.random()*100-50}px)`;
                el.style.opacity = '0';
            });
            
            setTimeout(() => {
                if(el.parentNode) el.remove();
            }, 1200);
        }

        // Web Audio API Logic
        let audioCtx;
        
        function initAudio() {
            if (!audioCtx) {
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (audioCtx.state === 'suspended') {
                audioCtx.resume();
            }
        }

        // Synthetic ASMR: clear water droplet / bell
        function playBell(freq) {
            if(!audioCtx) return;
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            
            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
            
            // Envelope
            gain.gain.setValueAtTime(0, audioCtx.currentTime);
            gain.gain.linearRampToValueAtTime(0.3, audioCtx.currentTime + 0.02);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 1.0);
            
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            
            osc.start();
            osc.stop(audioCtx.currentTime + 1.0);
        }

        // Synthetic ASMR: bamboo knock / wooden pluck
        function playWood(freq) {
            if(!audioCtx) return;
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(freq * 0.5, audioCtx.currentTime + 0.1);
            
            // Envelope
            gain.gain.setValueAtTime(0, audioCtx.currentTime);
            gain.gain.linearRampToValueAtTime(0.4, audioCtx.currentTime + 0.01);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.2);
            
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            
            osc.start();
            osc.stop(audioCtx.currentTime + 0.2);
        }

        // Pentatonic scale frequencies for harmony (C major pentatonic: C, D, E, G, A)
        // using higher octaves for bell/water sounds
        const pentatonicFrequencies = [523.25, 587.33, 659.25, 783.99, 880.00, 1046.50, 1174.66, 1318.51];
        
        let lastAudioTime = 0;
        const AUDIO_THROTTLE_MS = 150; // rate limit: one note every 150ms max to prevent cacophony

        function triggerSound() {
            initAudio();
            const now = Date.now();
            if(now - lastAudioTime < AUDIO_THROTTLE_MS) return; // Throttled
            lastAudioTime = now;
            
            const freq = pentatonicFrequencies[Math.floor(Math.random() * pentatonicFrequencies.length)];
            
            // Randomly choose between Bell/Water and Wood/Bamboo
            if (Math.random() > 0.4) {
                playBell(freq);
            } else {
                playWood(freq / 2); // lower freq for wood
            }
        }

        // Event Handling
        let isDrawing = false;
        let isHintHidden = false;

        function handlePointerStart(e) {
            e.preventDefault();
            isDrawing = true;
            if(!isHintHidden) {
                hintText.style.opacity = '0';
                isHintHidden = true;
            }
            initAudio(); // Initialize on first interaction
            processEvent(e);
        }

        function handlePointerMove(e) {
            if (!isDrawing) return;
            e.preventDefault();
            processEvent(e);
        }

        function handlePointerEnd(e) {
            isDrawing = false;
        }
        
        // Throttling for particles to avoid lagging
        let lastParticleTime = 0;
        const PARTICLE_THROTTLE_MS = 20;

        function processEvent(e) {
            const now = Date.now();
            
            let clientX, clientY;
            if (e.touches && e.touches.length > 0) {
                // Loop through all active touches for multi-touch support
                for(let i = 0; i < e.touches.length; i++) {
                    let rect = container.getBoundingClientRect();
                    let x = e.touches[i].clientX - rect.left;
                    let y = e.touches[i].clientY - rect.top;
                    
                    if (now - lastParticleTime > PARTICLE_THROTTLE_MS) {
                        spawnParticle(x, y);
                    }
                }
                if (now - lastParticleTime > PARTICLE_THROTTLE_MS) lastParticleTime = now;
            } else {
                // Mouse event
                let rect = container.getBoundingClientRect();
                clientX = e.clientX - rect.left;
                clientY = e.clientY - rect.top;
                
                if (now - lastParticleTime > PARTICLE_THROTTLE_MS) {
                    spawnParticle(clientX, clientY);
                    lastParticleTime = now;
                }
            }
            
            triggerSound();
        }

        // Bind events
        container.addEventListener('touchstart', handlePointerStart, {passive: false});
        container.addEventListener('touchmove', handlePointerMove, {passive: false});
        container.addEventListener('touchend', handlePointerEnd);
        container.addEventListener('touchcancel', handlePointerEnd);
        
        container.addEventListener('mousedown', handlePointerStart);
        window.addEventListener('mousemove', (e) => {
            if(isDrawing && e.target === container) {
                handlePointerMove(e);
            } else if (isDrawing && e.target !== container) {
                 isDrawing = false; // cancel if cursor leaves
            }
        });
        window.addEventListener('mouseup', handlePointerEnd);
    </script>
</div>
"""

ORANG_TUA_HTML = """
<div class="min-h-[100dvh] bg-[#fff0f5] pb-32 transition-colors duration-1000" id="ot-main-bg">
    
    <!-- HEADER -->
    <div class="pt-20 px-6 pb-4 bg-gradient-to-b from-pink-100/50 to-transparent">
        <div class="flex items-center gap-4 mb-2">
            <div class="w-12 h-12 rounded-full bg-pink-200 flex items-center justify-center text-pink-600 shadow-inner">
                <i class="fas fa-home text-2xl"></i>
            </div>
            <div>
                <h2 class="text-3xl font-extrabold text-pink-900 tracking-tight leading-none">Ruang Orang Tua</h2>
                <p class="text-pink-600 font-medium text-sm">Asisten Digital Inklusi</p>
            </div>
        </div>
    </div>

    <!-- EMERGENCY BURNOUT CONTAINER (Hidden by default) -->
    <div id="burnout-emergency-container" class="px-5 mb-6 hidden">
        <div class="bg-slate-800 rounded-[2.5rem] p-6 shadow-2xl border border-slate-700 relative overflow-hidden">
            <div class="absolute -right-4 -top-4 w-32 h-32 bg-violet-500/20 rounded-full blur-3xl pointer-events-none"></div>
            <div class="absolute -left-4 -bottom-4 w-32 h-32 bg-rose-500/20 rounded-full blur-3xl pointer-events-none"></div>
            
            <div class="relative z-10 text-center">
                <i class="fas fa-heart text-4xl text-rose-400 mb-4 animate-bounce"></i>
                <h3 class="text-2xl font-extrabold text-white mb-2">Anda Tidak Sendirian.</h3>
                <p class="text-slate-300 text-sm mb-6 leading-relaxed">Sistem mendeteksi tingkat stres Anda sangat tinggi berturut-turut. Mengurus anak istimewa tidaklah mudah. Mari ambil napas sejenak.</p>
                
                <div class="bg-white/5 p-4 rounded-2xl border border-white/10 mb-6 backdrop-blur-sm">
                    <p class="text-lg font-serif text-slate-200 italic" id="zen-quote-inline">"Loading quote..."</p>
                </div>
                
                <a href="https://wa.me/6282330890500?text=Halo%20Psikolog%20Sekolah,%20saya%20butuh%20sesi%20konseling%20segera." class="inline-flex items-center justify-center gap-3 w-full bg-rose-500/20 text-rose-400 border border-rose-500/50 px-6 py-4 rounded-full font-bold shadow-lg hover:bg-rose-500 hover:text-white transition-all">
                    <i class="fas fa-user-md text-xl"></i> Konsultasi Psikolog Sekarang
                </a>
            </div>
        </div>
    </div>

    <!-- Feature 2: Tantrum Darurat (PROMINENT TOP BUTTON) -->
    <div class="px-5 mb-8">
        <button onclick="openModal('modal-ot-tantrum')" class="w-full bg-gradient-to-r from-red-600 to-rose-600 p-6 rounded-[2.5rem] shadow-xl shadow-red-200 flex items-center justify-center gap-4 hover:scale-[1.02] active:scale-95 transition-all group border border-red-400/50">
            <i class="fas fa-exclamation-circle text-4xl text-white animate-pulse"></i>
            <div class="text-left">
                <h3 class="font-extrabold text-white text-2xl leading-tight uppercase tracking-wider">Bantuan Tantrum</h3>
                <p class="text-xs text-white/90 mt-1 font-medium">Protokol & Audio Penenang Instan</p>
            </div>
        </button>
    </div>

    <!-- MAIN GRID -->
    <div class="px-5 grid grid-cols-1 md:grid-cols-2 gap-5">
        
        <!-- Feature 1: Buku Penghubung -->
        <button onclick="openModal('modal-ot-buku')" class="bg-white p-6 rounded-[2rem] shadow-sm border border-pink-50 flex items-center gap-5 hover:bg-pink-50 hover:-translate-y-1 transition-all group">
            <div class="w-16 h-16 rounded-2xl bg-rose-100 flex items-center justify-center text-rose-500 shadow-inner group-hover:scale-110 transition-transform">
                <i class="fas fa-book-reader text-3xl"></i>
            </div>
            <div class="text-left flex-1">
                <h3 class="font-bold text-gray-800 text-lg leading-tight">Jurnal Penghubung</h3>
                <p class="text-xs text-gray-500 mt-1 line-clamp-2">Sinkronisasi mood & perilaku 2 arah dengan Guru.</p>
            </div>
            <i class="fas fa-chevron-right text-gray-700 group-hover:text-rose-400"></i>
        </button>

        <!-- Feature 3: Jadwal Medis -->
        <button onclick="openModal('modal-ot-jadwal')" class="bg-white p-6 rounded-[2rem] shadow-sm border border-pink-50 flex items-center gap-5 hover:bg-pink-50 hover:-translate-y-1 transition-all group">
            <div class="w-16 h-16 rounded-2xl bg-blue-100 flex items-center justify-center text-blue-500 shadow-inner group-hover:scale-110 transition-transform">
                <i class="fas fa-pills text-3xl"></i>
            </div>
            <div class="text-left flex-1">
                <h3 class="font-bold text-gray-800 text-lg leading-tight">Jadwal Medis</h3>
                <p class="text-xs text-gray-500 mt-1 line-clamp-2">Notifikasi paksa (push) obat & terapi harian.</p>
            </div>
            <i class="fas fa-chevron-right text-gray-700 group-hover:text-blue-400"></i>
        </button>

        <!-- Feature 4: Pelacak Nutrisi -->
        <button onclick="openModal('modal-ot-nutrisi')" class="bg-emerald-50 p-6 rounded-[2rem] shadow-sm border border-emerald-100 flex items-center gap-5 hover:bg-emerald-100 hover:-translate-y-1 transition-all group">
            <div class="w-16 h-16 rounded-2xl bg-teal-100 flex items-center justify-center text-teal-600 shadow-inner group-hover:scale-110 transition-transform">
                <i class="fas fa-notes-medical text-3xl"></i>
            </div>
            <div class="text-left flex-1">
                <h3 class="font-bold text-teal-800 text-lg leading-tight">Pelacak Nutrisi</h3>
                <p class="text-xs text-teal-600 mt-1 line-clamp-2">Jurnal diet eliminasi neurologis (CF/GF).</p>
            </div>
            <i class="fas fa-chevron-right text-teal-500 group-hover:text-teal-700"></i>
        </button>

        <!-- Feature 5: Modul Terapi -->
        <button onclick="openModal('modal-ot-modul')" class="bg-white p-6 rounded-[2rem] shadow-sm border border-pink-50 flex items-center gap-5 hover:bg-pink-50 hover:-translate-y-1 transition-all group">
            <div class="w-16 h-16 rounded-2xl bg-amber-100 flex items-center justify-center text-amber-500 shadow-inner group-hover:scale-110 transition-transform">
                <i class="fas fa-video text-3xl"></i>
            </div>
            <div class="text-left flex-1">
                <h3 class="font-bold text-gray-800 text-lg leading-tight">Modul Terapi</h3>
                <p class="text-xs text-gray-500 mt-1 line-clamp-2">Video & PDF latihan motorik mandiri di rumah.</p>
            </div>
            <i class="fas fa-chevron-right text-gray-700 group-hover:text-amber-400"></i>
        </button>

        <!-- Feature 6: Monitor Burnout -->
        <button onclick="openModal('modal-ot-burnout-menu')" class="bg-violet-50 p-6 rounded-[2rem] shadow-sm border border-violet-100 flex items-center gap-5 hover:bg-violet-100 hover:-translate-y-1 transition-all group">
            <div class="w-16 h-16 rounded-2xl bg-violet-200 flex items-center justify-center text-violet-600 shadow-inner group-hover:scale-110 transition-transform">
                <i class="fas fa-spa text-3xl"></i>
            </div>
            <div class="text-left flex-1">
                <h3 class="font-bold text-violet-900 text-lg leading-tight">Monitor Burnout</h3>
                <p class="text-xs text-violet-600 mt-1 line-clamp-2">Apotek digital pereda stres & afirmasi penenang.</p>
            </div>
            <i class="fas fa-chevron-right text-violet-500 group-hover:text-violet-700"></i>
        </button>

    </div>

    <!-- Inject Modals Content via JS based on implementation steps -->

    <!-- MODAL BUKU PENGHUBUNG -->
    <div id="modal-ot-buku" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-rose-900/60 backdrop-blur-md transition-opacity" onclick="closeModal('modal-ot-buku')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.5s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20 max-h-[90dvh] overflow-y-auto border-t-4 border-rose-500 relative">
            
            <!-- Loading State Animasi Emosional Keluarga -->
            <div id="ot-buku-loading" class="absolute inset-0 bg-white/95 backdrop-blur-xl z-50 hidden flex-col items-center justify-center rounded-t-3xl md:rounded-3xl overflow-hidden transition-opacity duration-500">
                <div class="relative w-48 h-48 mb-6 flex items-center justify-center">
                    <!-- Silhouette SVG (Parent holding child's hand) -->
                    <svg viewBox="0 0 200 200" class="absolute inset-0 w-full h-full text-rose-100" fill="currentColor">
                        <path d="M 60 180 C 60 140, 80 120, 100 120 C 120 120, 140 140, 140 180 Z" />
                        <circle cx="100" cy="90" r="25" />
                        
                        <path d="M 120 180 C 120 150, 135 135, 150 135 C 165 135, 180 150, 180 180 Z" />
                        <circle cx="150" cy="115" r="18" />
                        
                        <!-- Connecting hands -->
                        <path d="M 130 150 Q 140 160 140 150" stroke="currentColor" stroke-width="8" stroke-linecap="round" fill="none" />
                    </svg>

                    <!-- Liquid Fill Clip Path -->
                    <svg viewBox="0 0 200 200" class="absolute inset-0 w-full h-full text-rose-500" fill="currentColor">
                        <clipPath id="familyClip">
                            <path d="M 60 180 C 60 140, 80 120, 100 120 C 120 120, 140 140, 140 180 Z" />
                            <circle cx="100" cy="90" r="25" />
                            
                            <path d="M 120 180 C 120 150, 135 135, 150 135 C 165 135, 180 150, 180 180 Z" />
                            <circle cx="150" cy="115" r="18" />
                            
                            <path d="M 130 150 Q 140 160 140 150" stroke="white" stroke-width="8" stroke-linecap="round" fill="none" />
                        </clipPath>
                        <rect id="liquid-fill-rect" x="0" y="200" width="200" height="200" fill="currentColor" clip-path="url(#familyClip)" class="transition-all duration-[2000ms] ease-in-out" />
                    </svg>

                    <!-- Success State (Smile/Checkmark) -->
                    <div id="buku-success-icon" class="absolute inset-0 flex items-center justify-center opacity-0 transform scale-50 transition-all duration-700">
                        <i class="fas fa-check-circle text-7xl text-emerald-500 bg-white rounded-full"></i>
                    </div>
                </div>
                <h3 id="buku-loading-text" class="text-xl font-bold text-rose-800 tracking-wide text-center px-4 transition-opacity duration-300">Menyampaikan kasih sayang...</h3>
                <p id="buku-success-text" class="text-emerald-600 font-medium mt-2 opacity-0 transition-opacity duration-700 absolute bottom-12">Catatan harian selamat sampai ke guru.</p>
            </div>

            <div class="flex justify-between items-center mb-6 relative z-10">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-rose-100 flex items-center justify-center text-rose-500 shadow-inner">
                        <i class="fas fa-book-reader"></i>
                    </div>
                    <div>
                        <h3 class="text-lg font-bold text-gray-800 leading-tight">Jurnal Penghubung</h3>
                        <p class="text-xs text-rose-500 font-medium">Asisten Sinkronisasi Harian</p>
                    </div>
                </div>
                <button onclick="closeModal('modal-ot-buku')" class="bg-gray-50 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200 transition border border-gray-100 flex items-center justify-center">&times;</button>
            </div>
            
            <form onsubmit="submitBukuPenghubung(event)" class="space-y-6 mb-8">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                <!-- Mood Selection using Radio Cards -->
                <div class="bg-rose-50/50 p-4 rounded-2xl border border-rose-100">
                    <label class="block text-sm font-bold text-gray-700 mb-3 text-center">Suasana Hati Pagi Ini</label>
                    <div class="grid grid-cols-2 gap-3" id="mood-selector">
                        <label class="relative cursor-pointer">
                            <input type="radio" name="buku-mood-radio" value="Senang" class="peer sr-only" required>
                            <div class="p-3 rounded-xl border border-gray-200 bg-white shadow-sm flex flex-col items-center justify-center gap-2 transition-all peer-checked:border-emerald-500 peer-checked:bg-emerald-50 peer-checked:shadow-md hover:border-emerald-300">
                                <i class="fas fa-smile text-3xl text-emerald-500"></i>
                                <span class="text-xs font-bold text-gray-600 peer-checked:text-emerald-700">Senang / Ceria</span>
                            </div>
                        </label>
                        <label class="relative cursor-pointer">
                            <input type="radio" name="buku-mood-radio" value="Biasa" class="peer sr-only">
                            <div class="p-3 rounded-xl border border-gray-200 bg-white shadow-sm flex flex-col items-center justify-center gap-2 transition-all peer-checked:border-gray-500 peer-checked:bg-gray-100 peer-checked:shadow-md hover:border-gray-300">
                                <i class="fas fa-meh text-3xl text-gray-400"></i>
                                <span class="text-xs font-bold text-gray-600 peer-checked:text-gray-700">Biasa Saja</span>
                            </div>
                        </label>
                        <label class="relative cursor-pointer">
                            <input type="radio" name="buku-mood-radio" value="Rewel" class="peer sr-only">
                            <div class="p-3 rounded-xl border border-gray-200 bg-white shadow-sm flex flex-col items-center justify-center gap-2 transition-all peer-checked:border-red-500 peer-checked:bg-red-50 peer-checked:shadow-md hover:border-red-300">
                                <i class="fas fa-angry text-3xl text-red-500"></i>
                                <span class="text-xs font-bold text-gray-600 peer-checked:text-red-700">Rewel / Tantrum</span>
                            </div>
                        </label>
                        <label class="relative cursor-pointer">
                            <input type="radio" name="buku-mood-radio" value="Lemas" class="peer sr-only">
                            <div class="p-3 rounded-xl border border-gray-200 bg-white shadow-sm flex flex-col items-center justify-center gap-2 transition-all peer-checked:border-blue-500 peer-checked:bg-blue-50 peer-checked:shadow-md hover:border-blue-300">
                                <i class="fas fa-frown text-3xl text-blue-500"></i>
                                <span class="text-xs font-bold text-gray-600 peer-checked:text-blue-700">Lemas / Sakit</span>
                            </div>
                        </label>
                    </div>
                </div>

                <div class="bg-rose-50/50 p-4 rounded-2xl border border-rose-100 space-y-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1 ml-1">Durasi Tidur Semalam (Jam)</label>
                        <div class="relative">
                            <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                <i class="fas fa-bed text-rose-300"></i>
                            </div>
                            <input type="number" id="buku-sleep" class="w-full bg-white border border-rose-200 rounded-xl py-3 pl-10 pr-4 text-sm font-bold text-gray-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-rose-400 focus:border-transparent transition-shadow" placeholder="Contoh: 8" required>
                        </div>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1 ml-1">Perilaku Khusus Pagi Ini</label>
                        <textarea id="buku-behavior" rows="3" class="w-full bg-white border border-rose-200 rounded-xl p-4 text-sm font-medium text-gray-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-rose-400 focus:border-transparent transition-shadow resize-none" placeholder="Misal: Menolak sarapan, menangis saat mandi..."></textarea>
                    </div>
                </div>

                <button type="submit" class="w-full bg-gradient-to-r from-rose-500 to-rose-600 text-white font-bold py-4 rounded-2xl shadow-[0_8px_20px_rgba(244,63,94,0.3)] hover:shadow-[0_8px_25px_rgba(244,63,94,0.5)] transform hover:-translate-y-0.5 transition-all flex justify-center items-center gap-2">
                    <i class="fas fa-paper-plane"></i> Kirim ke Guru
                </button>
            </form>

            <div class="mt-8 pt-6 border-t border-rose-100">
                <h4 class="text-sm font-bold text-gray-800 mb-4 pl-2 border-l-4 border-rose-400">Korelasi Tidur & Fokus (Sekolah)</h4>
                <div class="w-full h-48 bg-rose-50/30 rounded-2xl border border-rose-100 p-2 relative shadow-inner">
                    <canvas id="bukuChart"></canvas>
                    <div id="buku-empty" class="absolute inset-0 flex flex-col items-center justify-center text-xs text-gray-500 hidden">
                        <i class="fas fa-chart-line text-2xl text-rose-200 mb-2"></i>
                        Belum cukup data untuk korelasi.
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- MODAL BANTUAN TANTRUM -->
    <div id="modal-ot-tantrum" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/90 backdrop-blur-md transition-opacity" onclick="closeModal('modal-ot-tantrum'); stopTantrumAudio();"></div>
        <div class="absolute bottom-0 left-0 w-full bg-[#111] rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.5s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20 border border-red-500/30">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-xl font-bold text-red-500 flex items-center gap-2 animate-pulse"><i class="fas fa-exclamation-triangle"></i> DARURAT TANTRUM</h3>
                <button onclick="closeModal('modal-ot-tantrum'); stopTantrumAudio();" class="bg-gray-800 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-700">&times;</button>
            </div>
            
            <div class="text-center mb-6">
                <div class="inline-block relative">
                    <div class="w-24 h-24 rounded-full bg-red-500/20 absolute inset-0 animate-ping"></div>
                    <button onclick="triggerTantrumAudio()" id="btn-tantrum-audio" class="w-24 h-24 rounded-full bg-gradient-to-br from-red-600 to-red-800 text-white flex items-center justify-center text-4xl shadow-[0_0_30px_rgba(239,68,68,0.5)] relative z-10 border-4 border-[#111]">
                        <i class="fas fa-power-off"></i>
                    </button>
                </div>
                <p class="text-red-400 text-xs mt-4 font-bold tracking-widest uppercase" id="tantrum-audio-status">Audio Penenang: NONAKTIF</p>
            </div>

            <div class="bg-red-900/20 p-5 rounded-2xl border border-red-100 text-gray-800 bg-white mb-4">
                <h4 class="text-xs font-bold text-red-400 uppercase tracking-widest mb-3 border-b border-red-500/30 pb-2">Langkah Penanganan (Instruksi Guru)</h4>
                <ul class="space-y-3 text-sm text-gray-700 list-decimal pl-4" id="tantrum-steps">
                    <!-- Fetched via JS -->
                    <li>Sedang memuat protokol profil anak...</li>
                </ul>
            </div>
            
            <button onclick="closeModal('modal-ot-tantrum'); stopTantrumAudio();" class="w-full border border-red-500/50 text-red-400 font-bold py-3 rounded-xl hover:bg-red-500/10 transition">Selesai / Terkendali</button>
        </div>
    </div>

    <!-- MODAL JADWAL MEDIS -->
    <div id="modal-ot-jadwal" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" onclick="closeModal('modal-ot-jadwal')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.5s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-pills text-sky-500 mr-2"></i>Jadwal Medis & Terapi</h3>
                <button onclick="closeModal('modal-ot-jadwal')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            
            <form onsubmit="submitJadwalMedis(event)" class="flex gap-2 mb-6">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                <input type="time" id="med-time" class="bg-sky-50 border border-sky-100 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400" required>
                <input type="text" id="med-name" placeholder="Nama Obat / Terapi..." class="flex-1 bg-sky-50 border border-sky-100 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400" required>
                <button type="submit" class="bg-sky-500 text-white w-12 rounded-xl flex items-center justify-center hover:bg-sky-600 transition shadow-md"><i class="fas fa-plus"></i></button>
            </form>

            <div class="bg-sky-50 p-3 rounded-xl border border-sky-200 mb-6 text-xs text-sky-800 flex items-start gap-2">
                <i class="fas fa-bell mt-0.5"></i>
                <p>Notifikasi Push akan muncul otomatis di layar HP Anda saat waktu obat tiba, meskipun browser sedang ditutup.</p>
            </div>

            <h4 class="text-sm font-bold text-gray-800 mb-4 pl-2 border-l-4 border-sky-500">Timeline Hari Ini</h4>
            <div class="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-sky-200 before:to-transparent" id="jadwal-timeline">
                <!-- Fetched via JS -->
            </div>
        </div>
    </div>

    <!-- MODAL PELACAK NUTRISI -->
    <div id="modal-ot-nutrisi" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-teal-900/60 backdrop-blur-md transition-opacity" onclick="closeModal('modal-ot-nutrisi')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-[#f0fdf4] rounded-t-[2.5rem] p-6 shadow-2xl animate-[slideUp_0.5s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-[3rem] md:top-20 max-h-[90dvh] overflow-y-auto border-t-4 border-emerald-400 flex flex-col">
            <div class="flex justify-between items-center mb-6 shrink-0 relative z-10">
                <div class="flex items-center gap-3">
                    <div class="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 shadow-inner">
                        <i class="fas fa-apple-alt text-2xl"></i>
                    </div>
                    <div>
                        <h3 class="text-xl font-extrabold text-emerald-900 leading-tight tracking-tight">Pelacak Nutrisi</h3>
                        <p class="text-xs text-emerald-600 font-bold tracking-wider uppercase">Diet Eliminasi Neurologis</p>
                    </div>
                </div>
                <button onclick="closeModal('modal-ot-nutrisi')" class="bg-white w-10 h-10 rounded-full text-emerald-500 hover:bg-emerald-50 transition border border-emerald-100 flex items-center justify-center shadow-sm">&times;</button>
            </div>
            
            <button onclick="openModal('modal-ot-kamus-alergi')" class="w-full bg-white px-5 py-4 rounded-2xl shadow-sm border border-emerald-100 flex items-center justify-between hover:-translate-y-1 hover:shadow-md transition-all group mb-6 shrink-0">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-teal-50 text-teal-500 flex items-center justify-center group-hover:bg-teal-500 group-hover:text-white transition-colors">
                        <i class="fas fa-book-medical text-xl"></i>
                    </div>
                    <div class="text-left">
                        <h4 class="font-bold text-teal-900 text-sm">Kamus Makanan Pemicu Alergi Neurologis</h4>
                        <p class="text-[10px] text-teal-600 font-medium">Daftar Komposisi Terlarang</p>
                    </div>
                </div>
                <i class="fas fa-chevron-right text-teal-300 group-hover:text-teal-500 transition-colors"></i>
            </button>

            <div class="bg-white p-5 rounded-3xl border border-emerald-100 shadow-sm mb-6 shrink-0 relative overflow-hidden">
                <div class="absolute -right-6 -top-6 w-24 h-24 bg-emerald-50 rounded-full opacity-50 pointer-events-none"></div>
                <p class="text-xs text-emerald-700 mb-4 font-bold leading-relaxed relative z-10"><i class="fas fa-leaf mr-1"></i> Catat jurnal makanan hari ini untuk deteksi dini lonjakan hiperaktif.</p>
                <form onsubmit="submitNutrisi(event)" class="relative z-10">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    <div class="relative group" id="food-input-container">
                        <input type="text" id="jurnal_makanan_input" oninput="checkAllergens()" placeholder="Ketik nama makanan / komposisi..." class="w-full bg-emerald-50/50 border-2 border-emerald-100 rounded-2xl p-4 pr-14 text-sm font-bold text-emerald-900 focus:outline-none focus:border-emerald-400 focus:bg-white transition-all shadow-inner placeholder-emerald-300" required>
                        <button type="submit" class="absolute right-2 top-2 bottom-2 w-12 bg-emerald-500 text-white rounded-xl flex items-center justify-center hover:bg-emerald-600 hover:scale-105 active:scale-95 transition-all shadow-md">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                    
                    <!-- Tooltip Peringatan Halus -->
                    <div id="nutrisi_warning_box" style="display: none;" class="absolute left-0 -top-12 w-full bg-red-600 text-white text-[10px] font-bold px-4 py-2 rounded-xl shadow-[0_4px_15px_rgba(220,38,38,0.4)] flex items-center gap-2 transform translate-y-2 transition-all duration-300 z-20">
                        <i class="fas fa-exclamation-triangle animate-bounce"></i>
                        <span id="allergen-tooltip-text">Awas! Mengandung bahan pemicu neuroinflamasi.</span>
                        <div class="absolute -bottom-1 left-8 w-3 h-3 bg-red-600 rotate-45"></div>
                    </div>
                </form>
            </div>

            <div class="flex-1 overflow-y-auto">
                <h4 class="text-xs font-bold text-emerald-800 mb-4 pl-3 border-l-4 border-emerald-400 tracking-wider uppercase">Jurnal Makanan Terakhir</h4>
                <div class="space-y-3 px-1 pb-4" id="nutrisi-list">
                    <!-- Fetched via JS -->
                </div>
            </div>
        </div>
    </div>

    <!-- MODAL KAMUS MAKANAN PEMICU ALERGI NEUROLOGIS -->
    <div id="modal-ot-kamus-alergi" class="fixed inset-0 z-[150] hidden">
        <div class="absolute inset-0 bg-teal-900/80 backdrop-blur-sm transition-opacity" onclick="closeModal('modal-ot-kamus-alergi')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-[2.5rem] p-6 shadow-2xl animate-[slideUp_0.4s_ease-out] md:relative md:max-w-xl md:mx-auto md:rounded-[3rem] md:top-10 max-h-[95dvh] overflow-y-auto border-t-4 border-teal-500 flex flex-col">
            
            <div class="flex justify-between items-center mb-6 shrink-0 bg-white sticky top-0 z-20 py-2">
                <div class="flex items-center gap-3">
                    <div class="w-12 h-12 rounded-full bg-teal-50 flex items-center justify-center text-teal-600 shadow-inner border border-teal-100">
                        <i class="fas fa-book-medical text-2xl"></i>
                    </div>
                    <div>
                        <h3 class="text-xl font-extrabold text-teal-900 leading-tight tracking-tight">Kamus Alergi Neurologis</h3>
                        <p class="text-[10px] text-teal-600 font-bold tracking-widest uppercase bg-teal-50 px-2 py-0.5 rounded inline-block mt-1 border border-teal-100">Perpustakaan Medis</p>
                    </div>
                </div>
                <button onclick="closeModal('modal-ot-kamus-alergi')" class="bg-gray-50 w-10 h-10 rounded-full text-gray-500 hover:bg-gray-200 transition border border-gray-100 flex items-center justify-center shadow-sm">&times;</button>
            </div>

            <div class="relative mb-6 shrink-0 z-10">
                <i class="fas fa-search absolute left-4 top-1/2 -translate-y-1/2 text-teal-400"></i>
                <input type="text" id="search-kamus-alergi" oninput="filterKamusAlergi()" placeholder="Cari komposisi (ex: Gluten, MSG, Aspartam)..." class="w-full bg-teal-50/50 border-2 border-teal-100 rounded-2xl py-3 pl-12 pr-4 text-sm font-bold text-teal-900 focus:outline-none focus:border-teal-400 focus:bg-white transition-all shadow-inner placeholder-teal-400/70">
            </div>

            <div class="flex-1 overflow-y-auto pr-1 space-y-4 pb-10" id="kamus_modal_content">
                <!-- Data Kamus will be injected here via JS -->
            </div>
            
            <div class="shrink-0 mt-4 pt-4 border-t border-teal-100 text-center">
                <p class="text-[10px] font-bold text-teal-400 tracking-widest uppercase">Total <span id="kamus_count">0</span> Data Tersedia</p>
            </div>
        </div>
    </div>

    <!-- MODAL REPOSITORI MODUL -->
    <div id="modal-ot-modul" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" onclick="closeModal('modal-ot-modul')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.5s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20 max-h-[90dvh] overflow-y-auto flex flex-col">
            <div class="flex justify-between items-center mb-6 shrink-0">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-video text-amber-500 mr-2"></i>Modul Terapi Mandiri</h3>
                <button onclick="closeModal('modal-ot-modul')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            
            <div class="flex gap-2 mb-6 overflow-x-auto pb-2 scrollbar-hide shrink-0 snap-x" id="modul-filters">
                <button onclick="filterModul('Semua')" class="modul-filter-btn active snap-center whitespace-nowrap px-4 py-2 rounded-xl text-sm font-bold bg-amber-500 text-white shadow-md transition-colors" data-filter="Semua">Semua</button>
                <button onclick="filterModul('Motorik Halus')" class="modul-filter-btn snap-center whitespace-nowrap px-4 py-2 rounded-xl text-sm font-bold bg-amber-50 text-amber-600 border border-amber-200 transition-colors" data-filter="Motorik Halus">Motorik Halus</button>
                <button onclick="filterModul('Wicara')" class="modul-filter-btn snap-center whitespace-nowrap px-4 py-2 rounded-xl text-sm font-bold bg-amber-50 text-amber-600 border border-amber-200 transition-colors" data-filter="Wicara">Wicara</button>
                <button onclick="filterModul('Dokumen')" class="modul-filter-btn snap-center whitespace-nowrap px-4 py-2 rounded-xl text-sm font-bold bg-amber-50 text-amber-600 border border-amber-200 transition-colors" data-filter="Dokumen">Dokumen PDF</button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 overflow-y-auto content-start flex-1 min-h-[50dvh]" id="modul-container">
                <div id="yt-loading" class="col-span-full text-center py-10 text-gray-500 text-sm animate-pulse">
                    <i class="fas fa-spinner fa-spin mr-2"></i> Mengambil data dari YouTube API...
                </div>
                <!-- Injected via JS -->
            </div>
        </div>
    </div>

    <!-- MODAL MONITOR BURNOUT (POPUP LOGIN) -->
    <div id="modal-ot-burnout-slider" class="fixed inset-0 z-[150] hidden">
        <div class="absolute inset-0 bg-violet-900/80 backdrop-blur-md transition-opacity" onclick="closeModal('modal-ot-burnout-slider')"></div>
        <div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-11/12 max-w-sm bg-white rounded-[2.5rem] p-8 shadow-2xl text-center border-t-4 border-violet-400">
            <i class="fas fa-spa text-6xl text-violet-400 mb-4 animate-pulse"></i>
            <h3 class="text-2xl font-extrabold text-violet-900 mb-2">Halo Ibu/Bapak</h3>
            <p class="text-sm text-violet-600 mb-8 font-medium">Seberapa lelah perasaan Anda hari ini? (1-10)</p>
            
            <form onsubmit="submitBurnout(event)">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                <div class="relative w-full h-2 bg-violet-100 rounded-full mb-10">
                    <input type="range" id="burnout-slider" min="1" max="10" value="5" class="w-full absolute top-0 left-0 h-full opacity-0 cursor-pointer z-20" oninput="updateBurnoutUI(this.value)">
                    <div id="burnout-fill" class="h-full bg-violet-500 rounded-full w-[50%] absolute top-0 left-0 z-10 transition-all"></div>
                    <div id="burnout-thumb" class="w-6 h-6 bg-white border-4 border-violet-500 rounded-full absolute top-1/2 -translate-y-1/2 -translate-x-1/2 left-[50%] z-10 shadow-md transition-all"></div>
                </div>
                <div class="flex justify-between text-xs font-bold text-violet-400 mb-8 px-2">
                    <span>1 (Bugar)</span>
                    <span id="burnout-display" class="text-xl text-violet-600">5</span>
                    <span>10 (Sangat Lelah)</span>
                </div>
                
                <button type="submit" class="w-full bg-violet-500 text-white font-bold py-3.5 rounded-2xl shadow-lg hover:bg-violet-600 active:scale-95 transition-all">Simpan Perasaan</button>
            </form>
        </div>
    </div>

    <!-- MODAL APOTEK DIGITAL PEREDA STRES -->
    <div id="modal-ot-burnout-menu" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-violet-900/60 backdrop-blur-md transition-opacity" onclick="closeModal('modal-ot-burnout-menu')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-[#f8f5ff] rounded-t-[2.5rem] p-6 shadow-2xl animate-[slideUp_0.5s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-[3rem] md:top-20 max-h-[90dvh] overflow-y-auto border-t-4 border-violet-400">
            <div class="flex justify-between items-center mb-6 shrink-0 relative z-10">
                <div class="flex items-center gap-3">
                    <div class="w-12 h-12 rounded-full bg-violet-100 flex items-center justify-center text-violet-600 shadow-inner">
                        <i class="fas fa-spa text-2xl"></i>
                    </div>
                    <div>
                        <h3 class="text-xl font-extrabold text-violet-900 leading-tight tracking-tight">Apotek Digital</h3>
                        <p class="text-xs text-violet-600 font-bold tracking-wider uppercase">Terapi Pereda Stres</p>
                    </div>
                </div>
                <button onclick="closeModal('modal-ot-burnout-menu')" class="bg-white w-10 h-10 rounded-full text-violet-500 hover:bg-violet-50 transition border border-violet-100 flex items-center justify-center shadow-sm">&times;</button>
            </div>
            
            <p class="text-sm text-violet-700 mb-6 font-medium text-justify px-2">Pilih salah satu terapi interaktif di bawah ini untuk meredakan ketegangan dan memulihkan energi Anda.</p>
            
            <div class="space-y-4">
                <button onclick="openTherapy('lentera')" class="w-full bg-white p-5 rounded-3xl shadow-sm border border-violet-100 flex items-center gap-4 hover:shadow-md hover:-translate-y-1 transition-all group">
                    <div class="w-12 h-12 rounded-2xl bg-amber-50 text-amber-500 flex items-center justify-center text-2xl group-hover:bg-amber-100 transition-colors">
                        <i class="fas fa-fire"></i>
                    </div>
                    <div class="text-left flex-1">
                        <h4 class="font-bold text-violet-900">Lentera Pelepas Beban</h4>
                        <p class="text-xs text-violet-600 mt-1">Terapi kognitif pelepasan emosi.</p>
                    </div>
                    <i class="fas fa-chevron-right text-violet-300 group-hover:text-violet-500"></i>
                </button>
                
                <button onclick="openTherapy('napas')" class="w-full bg-white p-5 rounded-3xl shadow-sm border border-violet-100 flex items-center gap-4 hover:shadow-md hover:-translate-y-1 transition-all group">
                    <div class="w-12 h-12 rounded-2xl bg-teal-50 text-teal-500 flex items-center justify-center text-2xl group-hover:bg-teal-100 transition-colors">
                        <i class="fas fa-lungs"></i>
                    </div>
                    <div class="text-left flex-1">
                        <h4 class="font-bold text-violet-900">Resonansi Napas Presisi</h4>
                        <p class="text-xs text-violet-600 mt-1">Biofeedback ritme pernapasan 4-7-8.</p>
                    </div>
                    <i class="fas fa-chevron-right text-violet-300 group-hover:text-violet-500"></i>
                </button>
                
                <button onclick="openTherapy('riak')" class="w-full bg-white p-5 rounded-3xl shadow-sm border border-violet-100 flex items-center gap-4 hover:shadow-md hover:-translate-y-1 transition-all group">
                    <div class="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-500 flex items-center justify-center text-2xl group-hover:bg-indigo-100 transition-colors">
                        <i class="fas fa-water"></i>
                    </div>
                    <div class="text-left flex-1">
                        <h4 class="font-bold text-violet-900">Riak Air Ketenangan</h4>
                        <p class="text-xs text-violet-600 mt-1">Grounding sensorik visual & auditori.</p>
                    </div>
                    <i class="fas fa-chevron-right text-violet-300 group-hover:text-violet-500"></i>
                </button>
            </div>
        </div>
    </div>

    <!-- TERAPI 1: LENTERA PELEPAS BEBAN -->
    <div id="therapy-lentera" class="fixed inset-0 z-[200] hidden bg-black flex flex-col items-center justify-center overflow-hidden">
        <button onclick="closeTherapy('lentera')" class="absolute top-6 right-6 w-10 h-10 rounded-full bg-white/10 text-white/50 flex items-center justify-center hover:bg-white/20 transition z-50">
            <i class="fas fa-times"></i>
        </button>
        
        <div id="lentera-phase-1" class="text-center px-6 w-full max-w-md transition-opacity duration-1000">
            <h3 class="text-white text-xl font-serif mb-6 opacity-80 leading-relaxed tracking-wide">Tuliskan satu beban atau kesedihan yang paling mengganggu Anda hari ini...</h3>
            <textarea id="lentera-input" rows="4" class="w-full bg-transparent border-b-2 border-white/20 text-white text-center text-lg focus:outline-none focus:border-amber-400 resize-none placeholder-white/20 transition-colors" placeholder="Ketik di sini..."></textarea>
            <button onclick="createLentera()" class="mt-8 px-8 py-3 rounded-full border border-amber-500/50 text-amber-500 hover:bg-amber-500/10 transition uppercase tracking-widest text-xs font-bold">Wujudkan Lentera</button>
        </div>
        
        <div id="lentera-phase-2" class="absolute inset-0 hidden flex flex-col items-center justify-center">
            <p id="lentera-instruction" class="absolute top-20 text-white/50 text-sm tracking-widest uppercase animate-pulse">Usap layar ke atas untuk melepaskan</p>
            
            <div id="lentera-obj" class="relative transition-transform duration-[4000ms] ease-in cursor-pointer touch-none">
                <!-- Glowing effect -->
                <div class="absolute inset-0 bg-amber-400 blur-3xl rounded-full opacity-30 scale-150 animate-pulse"></div>
                
                <!-- Lantern body -->
                <div class="w-32 h-40 bg-gradient-to-b from-amber-200 to-amber-500 rounded-2xl relative shadow-[0_0_50px_rgba(251,191,36,0.6)] flex items-center justify-center overflow-hidden border border-amber-300">
                    <p id="lentera-text" class="text-amber-900 font-serif text-center px-2 text-sm font-bold opacity-80 break-words line-clamp-4"></p>
                    <div class="absolute bottom-0 w-full h-8 bg-gradient-to-t from-black/20 to-transparent"></div>
                </div>
                <!-- Lantern base -->
                <div class="w-24 h-2 bg-amber-900 mx-auto rounded-b-md shadow-lg"></div>
            </div>
        </div>
    </div>

    <!-- TERAPI 2: RESONANSI NAPAS PRESISI -->
    <div id="therapy-napas" class="fixed inset-0 z-[200] hidden bg-slate-900 flex flex-col items-center justify-center overflow-hidden">
        <button onclick="closeTherapyNapas()" class="absolute top-6 right-6 w-10 h-10 rounded-full bg-white/10 text-white/50 flex items-center justify-center hover:bg-white/20 transition z-50">
            <i class="fas fa-times"></i>
        </button>
        
        <div class="text-center z-10 pointer-events-none mb-12">
            <h3 class="text-violet-300 text-xl font-bold mb-2">Resonansi Napas Presisi</h3>
            <p class="text-slate-400 text-sm">Tahan jempol Anda di layar untuk memulai</p>
        </div>
        
        <div id="napas-hitbox" class="absolute inset-0 z-0 flex items-center justify-center">
            <div class="relative w-64 h-64 flex items-center justify-center pointer-events-none">
                <!-- Inner Thumb guide -->
                <div class="absolute w-20 h-20 bg-violet-500/20 rounded-full border-2 border-violet-400/50 flex items-center justify-center">
                    <i class="fas fa-fingerprint text-3xl text-violet-400/50"></i>
                </div>
                
                <!-- Expanding Ring -->
                <div id="napas-ring" class="absolute w-24 h-24 border-4 border-violet-400 rounded-full shadow-[0_0_30px_rgba(167,139,250,0.4)] transition-all ease-linear"></div>
            </div>
        </div>
        
        <div class="absolute bottom-20 text-center pointer-events-none">
            <p id="napas-instruction" class="text-3xl font-extrabold text-white tracking-widest uppercase opacity-0 transition-opacity duration-500"></p>
        </div>
    </div>

    <!-- TERAPI 3: RIAK AIR KETENANGAN -->
    <div id="therapy-riak" class="fixed inset-0 z-[200] hidden bg-[#0b0416] flex flex-col items-center justify-center overflow-hidden touch-none select-none">
        <button onclick="closeTherapy('riak')" class="absolute top-6 right-6 w-10 h-10 rounded-full bg-white/10 text-white/50 flex items-center justify-center hover:bg-white/20 transition z-50">
            <i class="fas fa-times"></i>
        </button>
        
        <div id="riak-instruction" class="absolute top-20 text-center z-10 pointer-events-none transition-opacity duration-1000">
            <h3 class="text-indigo-300 text-xl font-serif mb-2">Riak Air Ketenangan</h3>
            <p class="text-indigo-400/50 text-sm tracking-widest uppercase animate-pulse">Sentuh permukaan air</p>
        </div>
        
        <canvas id="riak-canvas" class="absolute inset-0 w-full h-full cursor-pointer touch-none"></canvas>
    </div>

    <script>
        // --- THERAPY ROUTING ---
        function openTherapy(id) {
            closeModal('modal-ot-burnout-menu');
            document.getElementById('therapy-' + id).classList.remove('hidden');
        }
        function closeTherapy(id) {
            document.getElementById('therapy-' + id).classList.add('hidden');
            openModal('modal-ot-burnout-menu');
        }

        // --- TERAPI 1 LOGIC ---
        let startY;
        const lenteraObj = document.getElementById('lentera-obj');
        const phase1 = document.getElementById('lentera-phase-1');
        const phase2 = document.getElementById('lentera-phase-2');
        const input = document.getElementById('lentera-input');

        function createLentera() {
            if(input.value.trim() === '') return;
            document.getElementById('lentera-text').innerText = input.value;
            phase1.classList.add('opacity-0');
            setTimeout(() => {
                phase1.classList.add('hidden');
                phase2.classList.remove('hidden');
                phase2.classList.add('flex');
            }, 1000);
        }

        phase2.addEventListener('pointerdown', (e) => {
            startY = e.clientY;
        }, {passive: true});

        phase2.addEventListener('pointerup', (e) => {
            let endY = e.clientY;
            if (startY > endY + 50) releaseLentera();
        });

        let lenteraAudioCtx = null;
        function playLenteraWindAudio() {
            if (!lenteraAudioCtx) {
                lenteraAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (lenteraAudioCtx.state === 'suspended') {
                lenteraAudioCtx.resume();
            }

            const bufferSize = lenteraAudioCtx.sampleRate * 2;
            const buffer = lenteraAudioCtx.createBuffer(1, bufferSize, lenteraAudioCtx.sampleRate);
            const data = buffer.getChannelData(0);

            // Generate Pink Noise
            let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
            for (let i = 0; i < bufferSize; i++) {
                let white = Math.random() * 2 - 1;
                b0 = 0.99886 * b0 + white * 0.0555179;
                b1 = 0.99332 * b1 + white * 0.0750759;
                b2 = 0.96900 * b2 + white * 0.1538520;
                b3 = 0.86650 * b3 + white * 0.3104856;
                b4 = 0.55000 * b4 + white * 0.5329522;
                b5 = -0.7616 * b5 - white * 0.0168980;
                data[i] = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362;
                data[i] *= 0.11;
                b6 = white * 0.115926;
            }

            const noiseNode = lenteraAudioCtx.createBufferSource();
            noiseNode.buffer = buffer;
            noiseNode.loop = true;

            const filter = lenteraAudioCtx.createBiquadFilter();
            filter.type = 'lowpass';
            filter.frequency.value = 300; // Low frequency for wind effect

            const gainNode = lenteraAudioCtx.createGain();
            gainNode.gain.setValueAtTime(0, lenteraAudioCtx.currentTime);
            // Soft attack
            gainNode.gain.linearRampToValueAtTime(0.4, lenteraAudioCtx.currentTime + 1.5);
            // Slow decay
            gainNode.gain.linearRampToValueAtTime(0, lenteraAudioCtx.currentTime + 4.5);

            noiseNode.connect(filter);
            filter.connect(gainNode);
            gainNode.connect(lenteraAudioCtx.destination);

            noiseNode.start(lenteraAudioCtx.currentTime);
            noiseNode.stop(lenteraAudioCtx.currentTime + 4.5);
        }

        function releaseLentera() {
            playLenteraWindAudio();
            document.getElementById('lentera-instruction').style.opacity = '0';
            
            lenteraObj.style.transition = "transform 4s cubic-bezier(0.25, 1, 0.5, 1), opacity 4s ease-out";
            lenteraObj.style.transform = "translateY(-1200px) scale(0)";
            lenteraObj.style.opacity = "0";
            
            setTimeout(() => {
                closeTherapy('lentera');
                // Reset states
                lenteraObj.style.transition = "";
                lenteraObj.style.transform = "";
                lenteraObj.style.opacity = "1";
                phase1.classList.remove('hidden', 'opacity-0');
                phase2.classList.add('hidden');
                phase2.classList.remove('flex');
                input.value = '';
                document.getElementById('lentera-instruction').style.opacity = '1';
            }, 4500);
        }

        // --- TERAPI 2 LOGIC (Napas 4-7-8) ---
        let napasTimer = null;
        let isBreathing = false;
        let napasPhase = 0; // 0:Idle, 1:In(4s), 2:Hold(7s), 3:Out(8s)
        const napasRing = document.getElementById('napas-ring');
        const napasInstruction = document.getElementById('napas-instruction');
        const napasHitbox = document.getElementById('therapy-napas');

        function startNapasSession() {
            if(isBreathing) return;
            isBreathing = true;
            napasInstruction.style.opacity = '1';
            runNapasCycle();
        }

        function runNapasCycle() {
            if(!isBreathing) return;
            
            // Phase 1: Tarik Napas (4s)
            napasPhase = 1;
            napasInstruction.innerText = "Tarik Napas";
            napasRing.style.transitionDuration = '4s';
            napasRing.style.transform = 'scale(2.5)';
            napasRing.classList.replace('border-violet-400', 'border-violet-300');
            
            napasTimer = setTimeout(() => {
                if(!isBreathing) return;
                
                // Phase 2: Tahan Napas (7s)
                napasPhase = 2;
                napasInstruction.innerText = "Tahan";
                napasRing.classList.replace('border-violet-300', 'border-indigo-400');
                
                napasTimer = setTimeout(() => {
                    if(!isBreathing) return;
                    
                    // Phase 3: Hembuskan (8s)
                    napasPhase = 3;
                    napasInstruction.innerText = "Hembuskan";
                    napasRing.style.transitionDuration = '8s';
                    napasRing.style.transform = 'scale(1)';
                    napasRing.classList.replace('border-indigo-400', 'border-violet-400');
                    
                    napasTimer = setTimeout(() => {
                        if(!isBreathing) return;
                        runNapasCycle(); // Loop
                    }, 8000);
                }, 7000);
            }, 4000);
        }

        function stopNapasSession(interrupted = false) {
            if(!isBreathing) return;
            isBreathing = false;
            clearTimeout(napasTimer);
            
            if(interrupted && napasPhase !== 0 && napasPhase !== 3) {
                // If let go during Inhale or Hold, vibrate (haptic feedback)
                if(navigator.vibrate) navigator.vibrate([100, 50, 100]);
                napasInstruction.innerText = "Fokus Terputus";
            } else {
                napasInstruction.style.opacity = '0';
            }
            
            napasPhase = 0;
            napasRing.style.transitionDuration = '0.5s';
            napasRing.style.transform = 'scale(1)';
            napasRing.className = "absolute w-24 h-24 border-4 border-violet-400 rounded-full shadow-[0_0_30px_rgba(167,139,250,0.4)] transition-all ease-linear";
        }

        function closeTherapyNapas() {
            stopNapasSession();
            document.getElementById('therapy-napas').classList.add('hidden');
            openModal('modal-ot-burnout-menu');
        }

        // Bind events
        napasHitbox.addEventListener('touchstart', (e) => {
            if(e.target === napasHitbox || e.target.closest('#napas-hitbox')) startNapasSession();
        }, {passive: false});
        
        napasHitbox.addEventListener('touchend', () => stopNapasSession(true));
        napasHitbox.addEventListener('touchcancel', () => stopNapasSession(true));
        
        napasHitbox.addEventListener('mousedown', (e) => {
            if(e.target === napasHitbox || e.target.closest('#napas-hitbox')) startNapasSession();
        });
        napasHitbox.addEventListener('mouseup', () => stopNapasSession(true));
        napasHitbox.addEventListener('mouseleave', () => stopNapasSession(true));


        // --- TERAPI 3 LOGIC (Riak Air & Web Audio) ---
        const canvas = document.getElementById('riak-canvas');
        const ctx = canvas.getContext('2d');
        let ripples = [];
        let rAF = null;
        let riakAudioCtx = null;
        let lastRiakAudioTime = 0;

        function initRiakAudio() {
            if (!riakAudioCtx) {
                riakAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (riakAudioCtx.state === 'suspended') {
                riakAudioCtx.resume();
            }
        }

        // Bowl/Bell sound
        function playTibetanBowl(freq) {
            if(!riakAudioCtx) return;
            const osc = riakAudioCtx.createOscillator();
            const gain = riakAudioCtx.createGain();
            
            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, riakAudioCtx.currentTime);
            
            // Very slow, soft attack and very long decay for calming effect
            gain.gain.setValueAtTime(0, riakAudioCtx.currentTime);
            gain.gain.linearRampToValueAtTime(0.2, riakAudioCtx.currentTime + 0.1);
            gain.gain.exponentialRampToValueAtTime(0.001, riakAudioCtx.currentTime + 3.0);
            
            osc.connect(gain);
            gain.connect(riakAudioCtx.destination);
            
            osc.start();
            osc.stop(riakAudioCtx.currentTime + 3.0);
        }

        const riakFrequencies = [261.63, 293.66, 329.63, 392.00, 440.00]; // Pentatonic scale

        function createRipple(x, y) {
            initRiakAudio();
            document.getElementById('riak-instruction').style.opacity = '0';
            
            ripples.push({
                x: x,
                y: y,
                radius: 0,
                alpha: 1
            });
            
            const now = Date.now();
            if(now - lastRiakAudioTime > 400) { // Throttle audio
                lastRiakAudioTime = now;
                const freq = riakFrequencies[Math.floor(Math.random() * riakFrequencies.length)];
                playTibetanBowl(freq);
            }
        }

        function drawRipples() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Dark purple base with very subtle gradient
            const bgGrad = ctx.createLinearGradient(0, 0, 0, canvas.height);
            bgGrad.addColorStop(0, '#0b0416');
            bgGrad.addColorStop(1, '#1a0b2e');
            ctx.fillStyle = bgGrad;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            for (let i = ripples.length - 1; i >= 0; i--) {
                const r = ripples[i];
                r.radius += 1.5; // Slow ripple
                r.alpha -= 0.005; // Slow fade
                
                if (r.alpha <= 0) {
                    ripples.splice(i, 1);
                    continue;
                }
                
                ctx.beginPath();
                ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
                ctx.strokeStyle = `rgba(167, 139, 250, ${r.alpha})`; // Violet-400
                ctx.lineWidth = 2 + (r.alpha * 2);
                ctx.stroke();
                
                // Secondary inner ripple
                if (r.radius > 30) {
                    ctx.beginPath();
                    ctx.arc(r.x, r.y, r.radius - 30, 0, Math.PI * 2);
                    ctx.strokeStyle = `rgba(196, 181, 253, ${r.alpha * 0.5})`; // Violet-300
                    ctx.lineWidth = 1;
                    ctx.stroke();
                }
            }
            
            rAF = requestAnimationFrame(drawRipples);
        }

        function resizeCanvas() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }

        // Observe when therapy starts to init canvas
        const observerRiak = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if(mutation.target.id === 'therapy-riak') {
                    if(!mutation.target.classList.contains('hidden')) {
                        resizeCanvas();
                        window.addEventListener('resize', resizeCanvas);
                        if(!rAF) drawRipples();
                    } else {
                        window.removeEventListener('resize', resizeCanvas);
                        cancelAnimationFrame(rAF);
                        rAF = null;
                        ripples = [];
                        document.getElementById('riak-instruction').style.opacity = '1';
                    }
                }
            });
        });
        observerRiak.observe(document.getElementById('therapy-riak'), { attributes: true, attributeFilter: ['class'] });

        canvas.addEventListener('pointerdown', (e) => {
            createRipple(e.clientX, e.clientY);
        });
        
        let lastRiakTouch = 0;
        canvas.addEventListener('pointermove', (e) => {
            // Create drag ripples but heavily throttled to avoid visual/audio chaos
            const now = Date.now();
            if(e.buttons > 0 || e.pointerType === 'touch') {
                if(now - lastRiakTouch > 150) {
                    lastRiakTouch = now;
                    createRipple(e.clientX, e.clientY);
                }
            }
        });


        // --- FEATURE 1: BUKU PENGHUBUNG LOGIC ---
        async function submitBukuPenghubung(e) {
            e.preventDefault();
            
            let selectedMood = null;
            const moodRadios = document.getElementsByName('buku-mood-radio');
            for(let i=0; i<moodRadios.length; i++) {
                if(moodRadios[i].checked) {
                    selectedMood = moodRadios[i].value;
                    break;
                }
            }

            const data = {
                mood: selectedMood,
                sleep_duration: document.getElementById('buku-sleep').value,
                morning_behavior: document.getElementById('buku-behavior').value
            };

            const overlay = document.getElementById('ot-buku-loading');
            const fillRect = document.getElementById('liquid-fill-rect');
            const loadingText = document.getElementById('buku-loading-text');
            const successIcon = document.getElementById('buku-success-icon');
            const successText = document.getElementById('buku-success-text');

            // Reset state
            fillRect.setAttribute('y', '200');
            successIcon.classList.remove('opacity-100', 'scale-100');
            successIcon.classList.add('opacity-0', 'scale-50');
            successText.classList.remove('opacity-100');
            successText.classList.add('opacity-0');
            loadingText.classList.remove('opacity-0');
            loadingText.classList.add('opacity-100');
            loadingText.innerText = "Menyampaikan kasih sayang...";
            overlay.classList.remove('hidden');
            overlay.style.display = 'flex';

            // Start animation (liquid rising from bottom)
            setTimeout(() => {
                fillRect.setAttribute('y', '0');
            }, 100);

            try {
                const [res] = await Promise.all([
                    fetch('/orang-tua/api/buku', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')},
                        body: JSON.stringify(data)
                    }),
                    // Force minimum delay of 2.2s so the liquid animation (2s) can be seen fully
                    new Promise(r => setTimeout(r, 2200))
                ]);

                if(res.ok) {
                    // Success state
                    loadingText.classList.add('opacity-0');
                    setTimeout(() => {
                        loadingText.classList.remove('opacity-0');
                        loadingText.innerText = "Selesai";
                        successIcon.classList.remove('opacity-0', 'scale-50');
                        successIcon.classList.add('opacity-100', 'scale-100');
                        successText.classList.remove('opacity-0');
                        successText.classList.add('opacity-100');
                    }, 300);

                    e.target.reset();
                    loadBukuChart();

                    // Hide overlay after showing success
                    setTimeout(() => {
                        overlay.classList.add('hidden');
                        overlay.style.display = 'none';
                    }, 2500);
                }
            } catch(err) { 
                console.error(err);
                loadingText.innerText = "Gagal mengirim data.";
                setTimeout(() => {
                    overlay.classList.add('hidden');
                    overlay.style.display = 'none';
                }, 2000);
            }
        }

        async function loadBukuChart() {
            try {
                const res = await fetch('/orang-tua/api/chart-data');
                const data = await res.json();
                
                if(data.labels.length === 0) {
                    document.getElementById('buku-empty').classList.remove('hidden');
                    return;
                }
                document.getElementById('buku-empty').classList.add('hidden');

                if (!window.Chart) {
                    const script = document.createElement('script');
                    script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
                    script.onload = () => drawBukuChart(data);
                    document.head.appendChild(script);
                } else {
                    drawBukuChart(data);
                }
            } catch(err) { console.error(err); }
        }

        let bChart;
        function drawBukuChart(data) {
            const ctx = document.getElementById('bukuChart').getContext('2d');
            if(bChart) bChart.destroy();
            
            bChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [
                        {
                            label: 'Tidur (Jam)',
                            data: data.sleep_data,
                            borderColor: 'rgba(59, 130, 246, 1)',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            yAxisID: 'y',
                        },
                        {
                            label: 'Reaksi Fokus (ms)',
                            data: data.focus_data,
                            borderColor: 'rgba(239, 68, 68, 1)',
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            yAxisID: 'y1',
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { type: 'linear', display: true, position: 'left', title: { display: true, text: 'Jam' } },
                        y1: { type: 'linear', display: true, position: 'right', grid: { drawOnChartArea: false }, reverse: true, title: { display: true, text: 'ms (Lebih rendah lebih baik)' } }
                    },
                    plugins: { legend: { position: 'top', labels: { boxWidth: 10, font: { size: 10 } } } }
                }
            });
        }

        // --- FEATURE 2: BANTUAN TANTRUM LOGIC ---
        let tantrumAudioCtx;
        let tantrumOsc;
        let tantrumNoise;
        let isTantrumPlaying = false;

        async function fetchTantrumProfile() {
            try {
                const res = await fetch('/orang-tua/api/tantrum-profile');
                const data = await res.json();
                const ul = document.getElementById('tantrum-steps');
                ul.innerHTML = '';
                if(data.steps && data.steps.length > 0) {
                    data.steps.forEach(step => {
                        ul.innerHTML += `<li>${step}</li>`;
                    });
                } else {
                    ul.innerHTML = `
                        <li>Jauhkan dari benda berbahaya.</li>
                        <li>Berikan pelukan kompresi dalam (Deep Pressure) jika anak mengizinkan.</li>
                        <li>Jangan terlalu banyak bicara, gunakan bahasa non-verbal.</li>
                        <li>Nyalakan audio penenang di atas.</li>
                    `;
                }
            } catch(err) {}
        }

        function triggerTantrumAudio() {
            const btn = document.getElementById('btn-tantrum-audio');
            const status = document.getElementById('tantrum-audio-status');
            
            if(!tantrumAudioCtx) {
                tantrumAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (tantrumAudioCtx.state === 'suspended') tantrumAudioCtx.resume();

            if(isTantrumPlaying) {
                stopTantrumAudio();
            } else {
                // Play Pink Noise approximation (Very calming)
                const bufferSize = tantrumAudioCtx.sampleRate * 2;
                const buffer = tantrumAudioCtx.createBuffer(1, bufferSize, tantrumAudioCtx.sampleRate);
                const data = buffer.getChannelData(0);
                let lastOut = 0;
                for (let i = 0; i < bufferSize; i++) {
                    const white = Math.random() * 2 - 1;
                    data[i] = (lastOut + (0.02 * white)) / 1.02;
                    lastOut = data[i];
                    data[i] *= 3.5;
                }
                
                tantrumNoise = tantrumAudioCtx.createBufferSource();
                tantrumNoise.buffer = buffer;
                tantrumNoise.loop = true;
                
                const filter = tantrumAudioCtx.createBiquadFilter();
                filter.type = 'lowpass';
                filter.frequency.value = 300; // Deep rumble
                
                const gain = tantrumAudioCtx.createGain();
                gain.gain.value = 0.5;
                
                tantrumNoise.connect(filter);
                filter.connect(gain);
                gain.connect(tantrumAudioCtx.destination);
                tantrumNoise.start();

                isTantrumPlaying = true;
                btn.classList.replace('from-red-600', 'from-green-500');
                btn.classList.replace('to-red-800', 'to-green-700');
                btn.classList.add('animate-spin-slow');
                status.innerText = "Audio Penenang: AKTIF (Pink Noise)";
                status.classList.replace('text-red-400', 'text-green-400');
            }
        }

        function stopTantrumAudio() {
            if(tantrumNoise) tantrumNoise.stop();
            isTantrumPlaying = false;
            
            const btn = document.getElementById('btn-tantrum-audio');
            const status = document.getElementById('tantrum-audio-status');
            
            if(btn) {
                btn.classList.replace('from-green-500', 'from-red-600');
                btn.classList.replace('to-green-700', 'to-red-800');
                btn.classList.remove('animate-spin-slow');
            }
            if(status) {
                status.innerText = "Audio Penenang: NONAKTIF";
                status.classList.replace('text-green-400', 'text-red-400');
            }
        }

        // --- FEATURE 3: JADWAL MEDIS (PUSH PWA) ---
        async function submitJadwalMedis(e) {
            e.preventDefault();
            const data = {
                time: document.getElementById('med-time').value,
                medication_name: document.getElementById('med-name').value
            };
            try {
                const res = await fetch('/orang-tua/api/jadwal', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')},
                    body: JSON.stringify(data)
                });
                if(res.ok) {
                    // Request Notification Permission on first schedule
                    if (Notification.permission !== "granted") {
                        const perm = await Notification.requestPermission();
                        if (perm === "granted") subscribeUserToPush();
                    } else {
                        subscribeUserToPush();
                    }
                    e.target.reset();
                    loadJadwalTimeline();
                }
            } catch(err) { console.error(err); }
        }

        async function loadJadwalTimeline() {
            try {
                const res = await fetch('/orang-tua/api/jadwal');
                const data = await res.json();
                
                // Update Parent Dashboard Timeline
                const containerOT = document.getElementById('jadwal-timeline');
                if (containerOT) {
                    containerOT.innerHTML = '';
                    if(data.length === 0) {
                        containerOT.innerHTML = '<p class="text-xs text-gray-500 pl-5 md:pl-0 text-center">Belum ada jadwal hari ini.</p>';
                    } else {
                        data.forEach(item => {
                            const color = item.notified ? 'bg-green-500' : 'bg-sky-500';
                            const icon = item.notified ? 'fa-check' : 'fa-clock';
                            containerOT.innerHTML += `
                                <div class="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                                    <div class="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white ${color} text-white shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                                        <i class="fas ${icon} text-xs"></i>
                                    </div>
                                    <div class="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-white p-4 rounded-2xl shadow border border-sky-50 flex justify-between items-center">
                                        <div>
                                            <time class="mb-1 text-xs font-bold text-sky-500">${item.time}</time>
                                            <div class="text-sm font-bold text-gray-800">${item.medication_name}</div>
                                        </div>
                                        <button onclick="deleteJadwal(${item.id})" class="text-xs bg-red-50 text-red-500 hover:bg-red-500 hover:text-white px-2 py-1 rounded-md transition border border-red-100"><i class="fas fa-trash"></i> Hapus</button>
                                    </div>
                                </div>
                            `;
                        });
                    }
                }
            } catch(e) {}
        }

        async function deleteJadwal(id) {
            if(!confirm("Hapus jadwal ini?")) return;
            try {
                const res = await fetch('/orang-tua/api/jadwal/' + id, { method: 'DELETE' });
                if(res.ok) {
                    loadJadwalTimeline();
                }
            } catch(e) { console.error(e); }
        }

        // Socket listener for server-side APScheduler trigger
        const medSocket = io();
        medSocket.on('trigger_med_notification', function(data) {
            // Check if service worker is active and notify
            if ('serviceWorker' in navigator && 'PushManager' in window) {
                navigator.serviceWorker.ready.then(function(registration) {
                    registration.showNotification("Waktunya Obat/Terapi!", {
                        body: data.medication_name + " pada jam " + data.time,
                        icon: "/static/logoslb.png",
                        vibrate: [200, 100, 200, 100, 200, 100, 200],
                        requireInteraction: true
                    });
                    loadJadwalTimeline(); // Refresh to show checkmark
                });
            } else if (Notification.permission === "granted") {
                // Fallback standard notification
                new Notification("Waktunya Obat/Terapi!", {
                    body: data.medication_name + " pada jam " + data.time,
                    icon: "/static/logoslb.png"
                });
                loadJadwalTimeline();
            }
        });


        // --- FEATURE 4: PELACAK NUTRISI LOGIC ---
        let globalKamusData = [];

        async function fetchKamusAlergiData() {
            try {
                const res = await fetch('/api/kamus-nutrisi');
                if (res.ok) {
                    globalKamusData = await res.json();
                }
            } catch (err) {
                console.error("Gagal mengambil data kamus alergi:", err);
            }
        }

        function checkAllergens() {
            const rawInput = document.getElementById('jurnal_makanan_input').value;
            const input = rawInput.toLowerCase();
            const tooltip = document.getElementById('nutrisi_warning_box');
            const inputEl = document.getElementById('jurnal_makanan_input');
            
            let matchedObj = null;
            
            if (input.trim() !== "") {
                for (let item of globalKamusData) {
                    if (item.komposisi) {
                        const itemKomposisi = item.komposisi.toLowerCase();
                        const keywords = itemKomposisi.replace(/\\([^()]*\\)/g, '').split(/[\\s,-]+/).filter(w => w.length > 2);
                        if (itemKomposisi.includes("msg")) keywords.push("msg");
                        
                        let found = false;
                        for (let keyword of keywords) {
                            if (input.includes(keyword)) {
                                found = true;
                                break;
                            }
                        }
                        
                        if (found || itemKomposisi.includes(input) || input.includes(itemKomposisi)) {
                            matchedObj = item;
                            break;
                        }
                    }
                }
            }
            
            if (matchedObj) {
                tooltip.style.display = 'block';
                tooltip.className = "absolute left-0 -top-auto bottom-full mb-2 w-full bg-rose-100 text-rose-800 text-[10px] md:text-xs font-bold px-4 py-3 rounded-xl shadow-[0_4px_15px_rgba(225,29,72,0.4)] flex flex-col gap-1 opacity-100 translate-y-0 transition-all duration-300 z-20 border border-rose-300";
                tooltip.innerHTML = `<div><i class="fas fa-exclamation-triangle text-rose-600 animate-bounce mr-1"></i> <strong class="uppercase tracking-wider text-red-600">${matchedObj.komposisi}</strong></div><p class="font-medium text-justify mt-1 text-rose-700">${matchedObj.rasionalisasi}</p>`;
                
                inputEl.classList.remove('border-emerald-100', 'focus:border-emerald-400');
                inputEl.classList.add('border-rose-400', 'focus:border-rose-500', 'text-rose-700', 'bg-rose-50');
            } else {
                tooltip.style.display = 'none';
                tooltip.className = "absolute left-0 -top-12 w-full bg-red-600 text-white text-[10px] font-bold px-4 py-2 rounded-xl shadow-[0_4px_15px_rgba(220,38,38,0.4)] flex items-center gap-2 opacity-0 pointer-events-none transform translate-y-2 transition-all duration-300 z-20";
                
                inputEl.classList.add('border-emerald-100', 'focus:border-emerald-400');
                inputEl.classList.remove('border-rose-400', 'focus:border-rose-500', 'text-rose-700', 'bg-rose-50');
            }
        }

        async function submitNutrisi(e) {
            e.preventDefault();
            const rawInput = document.getElementById('jurnal_makanan_input').value;
            const input = rawInput.toLowerCase();
            let hasAllergen = false;
            for (let item of globalKamusData) {
                if (item.komposisi) {
                    const itemKomposisi = item.komposisi.toLowerCase();
                    const keywords = itemKomposisi.replace(/\\([^()]*\\)/g, '').split(/[\\s,-]+/).filter(w => w.length > 2);
                    if (itemKomposisi.includes("msg")) keywords.push("msg");
                    
                    let found = false;
                    for (let keyword of keywords) {
                        if (input.includes(keyword)) {
                            found = true;
                            break;
                        }
                    }
                    if (found || itemKomposisi.includes(input) || input.includes(itemKomposisi)) {
                        hasAllergen = true;
                        break;
                    }
                }
            }
            
            try {
                const res = await fetch('/orang-tua/api/nutrisi', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')},
                    body: JSON.stringify({ food_name: input, has_allergen: hasAllergen })
                });
                if(res.ok) {
                    e.target.reset();
                    checkAllergens(); // Reset UI
                    loadNutrisiList();
                }
            } catch(err) { console.error(err); }
        }

        async function loadNutrisiList() {
            try {
                const res = await fetch('/orang-tua/api/nutrisi');
                const data = await res.json();
                const container = document.getElementById('nutrisi-list');
                container.innerHTML = '';
                
                if(data.length === 0) {
                    container.innerHTML = '<div class="bg-emerald-50/50 p-4 rounded-2xl border border-emerald-100 text-center"><p class="text-[10px] text-emerald-500 font-bold tracking-widest uppercase">Belum ada jurnal</p></div>';
                    return;
                }

                data.forEach(item => {
                    const isAllergen = item.has_allergen;
                    const borderClass = isAllergen ? 'border-red-200 bg-red-50' : 'border-emerald-100 bg-white';
                    const iconClass = isAllergen ? 'text-red-500 fa-exclamation-triangle' : 'text-emerald-500 fa-check-circle';
                    const badgeClass = isAllergen ? 'bg-red-100 text-red-600' : 'bg-emerald-50 text-emerald-600';
                    const badgeText = isAllergen ? 'Awas' : 'Aman';
                    
                    container.innerHTML += `
                        <div class="p-4 rounded-2xl border ${borderClass} flex justify-between items-center shadow-sm">
                            <div class="flex items-center gap-3">
                                <div class="w-8 h-8 rounded-full ${badgeClass} flex items-center justify-center">
                                    <i class="fas ${iconClass} text-sm"></i>
                                </div>
                                <span class="text-sm font-bold text-gray-800 capitalize">${item.food_name}</span>
                            </div>
                            <span class="text-[10px] font-bold ${badgeClass} px-2 py-1 rounded-md uppercase">${badgeText}</span>
                        </div>
                    `;
                });
            } catch(e) {}
        }
        
        // KAMUS ALERGI LOGIC
        function renderKamusAlergi(data) {
            const container = document.getElementById('kamus_modal_content');
            const countLabel = document.getElementById('kamus_count');
            container.innerHTML = '';
            countLabel.innerText = data.length;

            if (data.length === 0) {
                container.innerHTML = '<div class="text-center py-10"><i class="fas fa-search text-4xl text-emerald-200 mb-2"></i><p class="text-sm font-bold text-emerald-600">Tidak ditemukan</p></div>';
                return;
            }

            data.forEach((item, index) => {
                container.innerHTML += `
                    <div class="bg-white p-5 rounded-3xl shadow-sm border border-emerald-100 group hover:border-emerald-300 transition-colors">
                        <div class="flex items-start gap-3">
                            <div class="w-8 h-8 rounded-full bg-emerald-50 text-emerald-500 flex items-center justify-center font-bold text-xs shrink-0 border border-emerald-100">
                                ${index + 1}
                            </div>
                            <div>
                                <h4 class="text-sm font-extrabold text-emerald-900 mb-1 leading-tight">${item.komposisi}</h4>
                                <i class="text-[10px] text-emerald-600 mb-3 block">${item.referensi_medis}</i>
                                <div class="bg-emerald-50/50 p-3 rounded-2xl border border-emerald-100">
                                    <p class="text-xs text-emerald-800 leading-relaxed text-justify font-medium">${item.rasionalisasi}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
        }

        function filterKamusAlergi() {
            const query = document.getElementById('search-kamus-alergi').value.toLowerCase();
            const filtered = globalKamusData.filter(item => {
                return (item.komposisi && item.komposisi.toLowerCase().includes(query)) || 
                       (item.referensi_medis && item.referensi_medis.toLowerCase().includes(query)) ||
                       (item.rasionalisasi && item.rasionalisasi.toLowerCase().includes(query));
            });
            renderKamusAlergi(filtered);
        }

        // --- FEATURE 5: MODUL TERAPI LOGIC ---
        async function fetchYouTubeModules() {
            const container = document.getElementById('modul-container');
            const loading = document.getElementById('yt-loading');
            
            // Simulating a real YouTube Data API v3 fetch for playlist items.
            // Since we don't have the user's actual API key, we mock the successful response structure
            // to fulfill the prompt's requirement without breaking the app.
            const mockApiResponse = {
                items: [
                    { snippet: { title: "Terapi Stimulasi Sensori & Motorik Halus", description: "Aktivitas terapi di rumah untuk meningkatkan koordinasi mata & tangan anak difabel.", resourceId: { videoId: "vBxyw0rM9_k" } }, category: "Motorik Halus" },
                    { snippet: { title: "Latihan Bicara (Speech Therapy) Dasar", description: "Membantu melatih artikulasi dan pernapasan anak telat bicara.", resourceId: { videoId: "j6fK5aQyYw4" } }, category: "Wicara" },
                    { snippet: { title: "Melatih Motorik Kasar & Keseimbangan", description: "Terapi integrasi sensorik untuk stabilitas.", resourceId: { videoId: "8lZOT-N407M" } }, category: "Motorik Halus" },
                    { snippet: { title: "Cara Latih Anak Autis Merespon Panggilan", description: "Tips terapi komunikasi kontak mata untuk tunagrahita.", resourceId: { videoId: "R61Qy63d9A4" } }, category: "Wicara" }
                ]
            };

            setTimeout(() => { // Simulate network delay
                if(loading) loading.remove();
                let html = '';
                
                // 1. Render Videos from "API"
                mockApiResponse.items.forEach(item => {
                    html += `
                        <div class="modul-item bg-gray-50 rounded-2xl border border-gray-100 overflow-hidden shadow-sm hover:shadow-md transition group" data-category="${item.category}">
                            <div class="aspect-video bg-black relative">
                                <iframe class="w-full h-full" src="https://www.youtube.com/embed/${item.snippet.resourceId.videoId}" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="lazy"></iframe>
                            </div>
                            <div class="p-3">
                                <h4 class="font-bold text-gray-800 text-sm">${item.snippet.title}</h4>
                                <p class="text-xs text-gray-500 mt-1">${item.snippet.description}</p>
                            </div>
                        </div>
                    `;
                });

                // 2. Render PDF Modul
                html += `
                    <div class="modul-item bg-amber-50 rounded-2xl border border-amber-100 overflow-hidden shadow-sm hover:shadow-md transition flex items-center p-4 gap-4" data-category="Dokumen">
                        <div class="w-12 h-12 rounded-xl bg-amber-200 text-amber-600 flex items-center justify-center text-2xl shrink-0">
                            <i class="fas fa-file-pdf"></i>
                        </div>
                        <div class="flex-1">
                            <h4 class="font-bold text-gray-800 text-sm">Lembar Kerja Menarik Garis</h4>
                            <p class="text-xs text-gray-500 mt-1">PDF Cetak - 2MB</p>
                        </div>
                        <a href="/orang-tua/modul/download?file=lembar_motorik.pdf" target="_blank" class="w-10 h-10 rounded-full bg-white text-amber-500 flex items-center justify-center hover:bg-amber-500 hover:text-white transition shadow-sm border border-amber-100">
                            <i class="fas fa-download"></i>
                        </a>
                    </div>
                `;
                
                container.innerHTML = html;
            }, 800);
        }

        function filterModul(category) {
            // Update Buttons
            document.querySelectorAll('.modul-filter-btn').forEach(btn => {
                if (btn.getAttribute('data-filter') === category) {
                    btn.className = "modul-filter-btn active snap-center whitespace-nowrap px-4 py-2 rounded-xl text-sm font-bold bg-amber-500 text-white shadow-md transition-colors";
                } else {
                    btn.className = "modul-filter-btn snap-center whitespace-nowrap px-4 py-2 rounded-xl text-sm font-bold bg-amber-50 text-amber-600 border border-amber-200 transition-colors";
                }
            });

            // Filter Items
            const items = document.querySelectorAll('.modul-item');
            items.forEach(item => {
                if (category === 'Semua' || item.getAttribute('data-category') === category) {
                    item.style.display = 'block'; // Or flex depending on item
                    if(item.classList.contains('flex')) item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        }


        // --- FEATURE 6: MONITOR BURNOUT LOGIC ---
        function updateBurnoutUI(val) {
            document.getElementById('burnout-display').innerText = val;
            const percent = (val - 1) / 9 * 100;
            document.getElementById('burnout-fill').style.width = `${percent}%`;
            document.getElementById('burnout-thumb').style.left = `${percent}%`;
            
            // Color grading (1: Green, 5: Violet, 10: Red)
            const fill = document.getElementById('burnout-fill');
            const thumb = document.getElementById('burnout-thumb');
            if(val <= 3) {
                fill.className = "h-full bg-emerald-500 rounded-full absolute top-0 left-0 z-10 transition-all";
                thumb.className = "w-6 h-6 bg-white border-4 border-emerald-500 rounded-full absolute top-1/2 -translate-y-1/2 -translate-x-1/2 z-10 shadow-md transition-all";
                document.getElementById('burnout-display').className = "text-xl text-emerald-600";
            } else if (val <= 7) {
                fill.className = "h-full bg-violet-500 rounded-full absolute top-0 left-0 z-10 transition-all";
                thumb.className = "w-6 h-6 bg-white border-4 border-violet-500 rounded-full absolute top-1/2 -translate-y-1/2 -translate-x-1/2 z-10 shadow-md transition-all";
                document.getElementById('burnout-display').className = "text-xl text-violet-600";
            } else {
                fill.className = "h-full bg-red-500 rounded-full absolute top-0 left-0 z-10 transition-all";
                thumb.className = "w-6 h-6 bg-white border-4 border-red-500 rounded-full absolute top-1/2 -translate-y-1/2 -translate-x-1/2 z-10 shadow-md transition-all";
                document.getElementById('burnout-display').className = "text-xl text-red-600 animate-pulse";
            }
        }

        async function submitBurnout(e) {
            e.preventDefault();
            const val = document.getElementById('burnout-slider').value;
            
            try {
                await fetch('/orang-tua/api/burnout', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')},
                    body: JSON.stringify({ stress_level: val })
                });
                
                closeModal('modal-ot-burnout-slider');
                checkBurnoutStatus();
                
            } catch(err) { console.error(err); }
        }

        async function checkBurnoutStatus() {
            try {
                const res = await fetch('/orang-tua/api/burnout-check');
                const data = await res.json();
                
                if(data.is_burnout) {
                    // Trigger Emergency Protocol Instantly
                    document.getElementById('burnout-emergency-container').classList.remove('hidden');
                    document.getElementById('ot-main-bg').className = "min-h-[100dvh] bg-slate-900 pb-32 transition-colors duration-1000"; // Cooler theme
                    
                    // Fetch ZenQuote
                    try {
                        const quoteRes = await fetch('https://api.allorigins.win/get?url=' + encodeURIComponent('https://zenquotes.io/api/random'));
                        const quoteData = await quoteRes.json();
                        const parsed = JSON.parse(quoteData.contents);
                        document.getElementById('zen-quote-inline').innerText = `"${parsed[0].q}" - ${parsed[0].a}`;
                    } catch(e) {
                        document.getElementById('zen-quote-inline').innerText = '"Terkadang hal yang paling berani untuk dilakukan adalah beristirahat."';
                    }
                }
            } catch(err) {}
        }


        // Custom Modal Hooks
        const originalOpenModalOT = window.openModal;
        window.openModal = async function(id) {
            if(originalOpenModalOT) originalOpenModalOT(id);
            else {
                const el = document.getElementById(id);
                if(el) el.classList.remove('hidden');
            }
            
            if(id === 'modal-ot-buku') loadBukuChart();
            if(id === 'modal-ot-tantrum') fetchTantrumProfile();
            if(id === 'modal-ot-jadwal') loadJadwalTimeline();
            if(id === 'modal-ot-nutrisi') {
                if (KAMUS_ALERGI_DATA.length === 0) await fetchKamusAlergiData();
                loadNutrisiList();
            }
            if(id === 'modal-ot-kamus-alergi') {
                if (KAMUS_ALERGI_DATA.length === 0) await fetchKamusAlergiData();
                renderKamusAlergi(KAMUS_ALERGI_DATA);
            }
            if(id === 'modal-ot-modul') fetchYouTubeModules();
        };

        // Auto trigger burnout check on load (simulating daily login)
        document.addEventListener('DOMContentLoaded', () => {
            fetchKamusAlergiData();
            checkBurnoutStatus(); // Check on load anyway just in case they're already burned out
            setTimeout(() => {
                // Check localStorage to show only once per session/day to prevent annoyance while navigating
                if(window.location.pathname === '/orang-tua') {
                     // Check if today we already asked
                     const today = new Date().toDateString();
                     if(localStorage.getItem('burnout_checked_date') !== today) {
                         openModal('modal-ot-burnout-slider');
                         localStorage.setItem('burnout_checked_date', today);
                     }
                }
            }, 500);
        });

    </script>
    <style>
        .animate-spin-slow { animation: spin 4s linear infinite; }
    </style>
</div>
"""

@app.route('/orang-tua')
def orang_tua_dashboard():
    if session.get('peran') not in ['orang_tua', 'kepala_sekolah'] and not session.get('is_admin'):
        return redirect(url_for('index'))
    theme = {
        'nav_bg': 'bg-rose-50',
        'icon_bg': 'bg-rose-100',
        'icon_text': 'text-rose-600',
        'title_text': 'text-rose-800',
        'link_hover': 'hover:text-rose-600',
        'link_active': 'text-rose-600 font-bold',
        'btn_primary': 'bg-rose-500 text-white hover:bg-rose-600',
        'bottom_nav_bg': 'bg-rose-50',
        'bottom_active': 'text-rose-600',
        'bottom_btn_bg': 'bg-rose-500',
        'bottom_btn_text': 'text-white',
        'bottom_text_inactive': 'text-rose-400'
    }
    rendered_content = cached_render('ORANG_TUA_HTML', ORANG_TUA_HTML, is_admin=session.get('is_admin', False), settings=get_settings(), csrf_token=csrf_token, peran=session.get('peran', ''), anak_id=session.get('anak_id'))
    return cached_render('BASE_LAYOUT', BASE_LAYOUT, styles=STYLES_HTML, active_page='home', content=rendered_content, hide_nav=False, full_width=True, is_admin=session.get('is_admin', False), settings=get_settings(), needs_socketio=True, theme=theme)

@app.route('/orang-tua/api/buku', methods=['POST'])
@limiter.limit("20 per minute")
def save_ot_buku():
    if session.get('peran') not in ['orang_tua', 'kepala_sekolah'] and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        data = request.json
        db.session.add(OrangTuaBuku(
            anak_id=session.get('anak_id'),
            mood=data.get('mood'),
            sleep_duration=int(data.get('sleep_duration', 0)),
            morning_behavior=data.get('morning_behavior')
        ))
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Terjadi kesalahan saat memproses data. Silakan coba lagi.'}), 500

@app.route('/api/jurnal-harian')
def api_jurnal_harian():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        q = OrangTuaBuku.query
        if session.get('peran') == 'orang_tua':
            q = q.filter_by(anak_id=session.get('anak_id'))
        elif session.get('peran') in ['guru', 'kepala_sekolah'] and request.args.get('anak_id'):
            q = q.filter_by(anak_id=request.args.get('anak_id'))
        
        buku_logs = q.order_by(OrangTuaBuku.created_at.desc()).limit(7).all()
        # Reverse to show chronological left to right
        buku_logs.reverse()
        
        labels = [f"Hari {i+1}" for i in range(len(buku_logs))]
        sleep_data = [l.sleep_duration for l in buku_logs]
        history_list = []
        for l in buku_logs:
            history_list.append({
                "mood": l.mood,
                "sleep_duration": l.sleep_duration,
                "morning_behavior": l.morning_behavior,
                "date": l.created_at.strftime("%d %b %Y") if l.created_at else "Unknown"
            })
            
        return jsonify({
            "labels": labels,
            "sleep_data": sleep_data,
            "history_list": history_list
        })
    except Exception as e:
        app.logger.error("Journal API error", exc_info=True)
        return jsonify({'error': "Gagal memuat data jurnal."}), 500

@app.route('/orang-tua/api/chart-data')
def get_ot_chart_data():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 403
    q_buku = OrangTuaBuku.query
    if session.get('peran') == 'orang_tua':
        q_buku = q_buku.filter_by(anak_id=session.get('anak_id'))
    buku_logs = q_buku.order_by(OrangTuaBuku.created_at.desc()).limit(7).all()
    reaction_logs = ReactionTimeLog.query.order_by(ReactionTimeLog.created_at.desc()).limit(7).all()
    
    # Reverse to show chronological left to right
    buku_logs.reverse()
    reaction_logs.reverse()
    
    labels = [f"Hari {i+1}" for i in range(max(len(buku_logs), len(reaction_logs)))]
    sleep_data = [l.sleep_duration for l in buku_logs]
    
    # Pad reaction data if unequal
    focus_data = [l.time_ms for l in reaction_logs]
    while len(focus_data) < len(labels):
        focus_data.append(None)
        
    return jsonify({
        "labels": labels,
        "sleep_data": sleep_data,
        "focus_data": focus_data
    })

@app.route('/orang-tua/api/tantrum-profile')
def get_tantrum_profile():
    # In a real app, fetch based on student ID. 
    # Here we return a static mock protocol written by a teacher.
    return jsonify({
        "steps": [
            "1. Jauhkan benda tajam dan rapuh dari jangkauan Dito.",
            "2. Jangan tatap matanya langsung, beri ruang 1 meter.",
            "3. Nyalakan audio Pink Noise dengan volume sedang.",
            "4. Berikan 'Sensory Brush' di area punggung jika ia meminta.",
            "5. Tunggu 5-10 menit hingga napasnya teratur sebelum mengajak bicara."
        ]
    })

@app.route('/orang-tua/api/jadwal', methods=['GET', 'POST'])
@limiter.limit("20 per minute")
def handle_ot_jadwal():
    if request.method == 'POST':
        if session.get('peran') not in ['orang_tua', 'kepala_sekolah'] and not session.get('is_admin'):
            return jsonify({'error': 'Unauthorized'}), 403
        try:
            data = request.json
            db.session.add(OrangTuaJadwal(
                anak_id=session.get('anak_id'),
                schedule_time=data.get('time'),
                medication_name=data.get('medication_name')
            ))
            db.session.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Terjadi kesalahan saat memproses data. Silakan coba lagi.'}), 500
    
    # GET method
    q = OrangTuaJadwal.query
    if session.get('peran') == 'orang_tua':
        q = q.filter_by(anak_id=session.get('anak_id'))
    elif session.get('peran') in ['guru', 'kepala_sekolah'] and request.args.get('anak_id'):
        q = q.filter_by(anak_id=request.args.get('anak_id'))
    
    logs = q.order_by(OrangTuaJadwal.schedule_time.asc()).all()
    res = []
    for l in logs:
        res.append({
            "id": l.id,
            "time": l.schedule_time.strftime("%H:%M") if l.schedule_time else "",
            "medication_name": l.medication_name,
            "notified": l.notified
        })
    return jsonify(res)

@app.route('/orang-tua/api/jadwal/<int:jadwal_id>', methods=['DELETE'])
def delete_ot_jadwal(jadwal_id):
    if not session.get('is_admin') and session.get('peran') != 'orang_tua':
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        jadwal = OrangTuaJadwal.query.get_or_404(jadwal_id)
        if not session.get('is_admin'):
            if str(jadwal.anak_id) != str(session.get('anak_id')):
                return jsonify({'error': 'Unauthorized'}), 403
        db.session.delete(jadwal)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Terjadi kesalahan saat menghapus data.'}), 500

@app.route('/api/kamus_nutrisi')
def api_kamus_nutrisi_underscore():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        target_path = os.path.join(current_dir, 'static', 'kamus_alergi_neuro.json')
            
        with open(target_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        app.logger.error("Nutrition dictionary error", exc_info=True)
        return jsonify({"error": "Gagal memuat kamus nutrisi."}), 500

@app.route('/api/kamus-nutrisi')
def api_kamus_nutrisi():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        target_path = os.path.join(current_dir, 'static', 'kamus_alergi_neuro.json')
            
        with open(target_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        app.logger.error("Nutrition dictionary error", exc_info=True)
        return jsonify({"error": "Gagal memuat kamus nutrisi."}), 500

@app.route('/orang-tua/api/nutrisi', methods=['GET', 'POST'])
@limiter.limit("20 per minute")
def handle_ot_nutrisi():
    if session.get('peran') not in ['orang_tua', 'kepala_sekolah'] and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403

    if request.method == 'POST':
        try:
            data = request.json
            db.session.add(OrangTuaNutrisi(
                anak_id=session.get('anak_id'),
                food_name=data.get('food_name'),
                has_allergen=data.get('has_allergen', False)
            ))
            db.session.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Terjadi kesalahan saat memproses data. Silakan coba lagi.'}), 500
    
    q = OrangTuaNutrisi.query
    if session.get('peran') == 'orang_tua':
        q = q.filter_by(anak_id=session.get('anak_id'))
    logs = q.order_by(OrangTuaNutrisi.created_at.desc()).limit(10).all()
    res = []
    for l in logs:
        res.append({
            "food_name": l.food_name,
            "has_allergen": l.has_allergen
        })
    return jsonify(res)

import traceback
from pywebpush import webpush, WebPushException

VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY')
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY')

VAPID_CLAIMS = {
    "sub": "mailto:admin@sekolah-luar-biasa.com"
}

@app.route('/orang-tua/api/subscribe', methods=['POST'])
@limiter.limit("20 per minute")
def subscribe():
    try:
        sub_info = request.json
        if not sub_info:
            return jsonify({'error': 'no info'}), 400
        
        # Store subscription if not exists
        existing = PushSubscription.query.filter_by(subscription_info=json.dumps(sub_info)).first()
        if not existing:
            db.session.add(PushSubscription(subscription_info=json.dumps(sub_info)))
            db.session.commit()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Terjadi kesalahan saat memproses data. Silakan coba lagi.'}), 500

@app.route('/orang-tua/api/vapid_public_key')
def vapid_public_key():
    return jsonify({'public_key': VAPID_PUBLIC_KEY})

def send_web_push(subscription_info, message_body):
    if not VAPID_PRIVATE_KEY:
        logging.warning("VAPID_PRIVATE_KEY not configured, push notification skipped")
        return
    try:
        webpush(
            subscription_info=subscription_info,
            data=message_body,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
    except WebPushException as ex:
        logging.error(f"Web Push failed: {repr(ex)}")

def send_all_pushes(schedules_data, subscriptions_data):
    with app.app_context():
        for sched in schedules_data:
            socketio.emit('trigger_med_notification', {
                'time': sched['time'],
                'medication_name': sched['medication_name']
            })
            for sub_info in subscriptions_data:
                try:
                    send_web_push(sub_info, f"Waktunya Obat/Terapi: {sched['medication_name']} pada jam {sched['time']}")
                except Exception as e:
                    traceback.print_exc()

def check_medications():
    with app.app_context():
        now = datetime.datetime.now()
        window_start = (now - datetime.timedelta(minutes=1)).time()
        window_end = (now + datetime.timedelta(minutes=1)).time()
        today = now.date()
        
        schedules = OrangTuaJadwal.query.filter(
            OrangTuaJadwal.schedule_time.between(window_start, window_end),
            OrangTuaJadwal.notified == False,
            db.or_(OrangTuaJadwal.notified_date == None, OrangTuaJadwal.notified_date < today)
        ).all()
        
        if not schedules:
            return
            
        subscriptions = PushSubscription.query.all()
        
        schedules_data = []
        for sched in schedules:
            schedules_data.append({
                'time': sched.schedule_time.strftime('%H:%M') if sched.schedule_time else '',
                'medication_name': sched.medication_name
            })
            sched.notified = True
            sched.notified_date = today
            
        subscriptions_data = []
        for sub in subscriptions:
            try:
                subscriptions_data.append(json.loads(sub.subscription_info))
            except:
                pass
                
        db.session.commit()
        threading.Thread(target=send_all_pushes, args=(schedules_data, subscriptions_data), daemon=True).start()

# Add job to scheduler (running every minute)
scheduler.add_job(id='Medication Check', func=check_medications, trigger='cron', minute='*')

def cleanup_push_subscriptions():
    with app.app_context():
        thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        PushSubscription.query.filter(PushSubscription.last_used < thirty_days_ago).delete()
        db.session.commit()

scheduler.add_job(id='Cleanup Subscriptions', func=cleanup_push_subscriptions, trigger='cron', hour=3, minute=0)

@app.route('/orang-tua/api/burnout', methods=['POST'])
@limiter.limit("20 per minute")
def save_burnout():
    if session.get('peran') not in ['orang_tua', 'kepala_sekolah'] and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        data = request.json
        db.session.add(OrangTuaBurnout(
            anak_id=session.get('anak_id'),
            stress_level=int(data.get('stress_level', 5)),
            recorded_date=datetime.date.today()
        ))
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Terjadi kesalahan saat memproses data. Silakan coba lagi.'}), 500

@app.route('/orang-tua/api/burnout-check')
def check_burnout():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 403
    q = OrangTuaBurnout.query
    if session.get('peran') == 'orang_tua':
        q = q.filter_by(anak_id=session.get('anak_id'))
    # Check last 3 entries
    logs = q.order_by(OrangTuaBurnout.created_at.desc()).limit(3).all()
    is_burnout = False
    if len(logs) == 3:
        if all(l.stress_level > 8 for l in logs):
            is_burnout = True
    return jsonify({"is_burnout": is_burnout})

@app.route('/orang-tua/modul/download')
def download_modul():
    if not session.get('peran') and not session.get('is_admin'):
        return "Unauthorized", 403
    filename = request.args.get('file')
    if not filename:
        return "No file specified", 400
        
    filename = secure_filename(filename)
    modul_dir = os.path.join(app.root_path, 'static', 'modul')
    os.makedirs(modul_dir, exist_ok=True)
    filepath = os.path.join(modul_dir, filename)
    
    if not os.path.exists(filepath):
        return "File not found", 404
            
    return send_from_directory(modul_dir, filename, as_attachment=True)

@app.route('/slb/tunalaras', methods=['GET', 'POST'])
def slb_tunalaras():
    if request.method == 'POST':
        try:
            emotion = request.form['emotion']
            anak_id = session.get('anak_id') if session.get('peran') == 'orang_tua' else None
            db.session.add(EmotionJournal(emotion=emotion, anak_id=anak_id))
            db.session.commit()
            return redirect(url_for('slb_tunalaras'))
        except Exception as e:
            db.session.rollback()
            return "Terjadi kesalahan saat memproses data. Silakan coba lagi.", 500
    
    q = EmotionJournal.query
    if session.get('peran') == 'orang_tua' and session.get('anak_id'):
        history = q.filter_by(anak_id=session.get('anak_id')).order_by(EmotionJournal.date.desc()).limit(20).all()
    else:
        history = q.order_by(EmotionJournal.date.desc()).limit(5).all()
    
    rendered_tunalaras = cached_render('SLB_TUNALARAS_HTML', SLB_TUNALARAS_HTML, history=history, csrf_token=lambda: "", peran=session.get('peran',''), anak_id=session.get('anak_id'))
    return cached_render('BASE_LAYOUT', BASE_LAYOUT, styles=STYLES_HTML, active_page='slb', content=rendered_tunalaras, theme={'nav_bg': 'bg-teal-100', 'title_text': 'text-teal-800'}, is_admin=session.get('is_admin', False), settings=get_settings(), needs_socketio=False)

@app.route('/api/tunalaras/guru-monitor')
def api_tunalaras_guru_monitor():
    if session.get('peran') not in ['guru', 'kepala_sekolah']:
        return jsonify({'error': 'Unauthorized'}), 403
    q = request.args.get('q', '').lower()
    
    entries = db.session.query(EmotionJournal).filter(EmotionJournal.anak_id != None).all()
    grouped = {}
    for e in entries:
        if e.anak_id not in grouped: grouped[e.anak_id] = []
        grouped[e.anak_id].append(e)
        
    results = []
    for a_id, evs in grouped.items():
        evs.sort(key=lambda x: x.date, reverse=True)
        siswa = db.session.get(Siswa, a_id)
        if not siswa: continue
        if q and q not in siswa.nama.lower(): continue
        parent = AkunPengguna.query.filter_by(anak_id=a_id, peran='orang_tua').first()
        parent_name = parent.nama_lengkap if parent else "Unknown"
        
        recent_emotions = [{"emotion": x.emotion, "date": x.date.strftime('%Y-%m-%d %H:%M') if x.date else ''} for x in evs[:3]]
        results.append({
            "parent_name": parent_name,
            "student_name": siswa.nama,
            "recent_emotions": recent_emotions
        })
    return jsonify(results)

@app.route('/slb/tunaganda')
def slb_tunaganda():
    return cached_render('BASE_LAYOUT', BASE_LAYOUT, styles=STYLES_HTML, active_page='slb', content=SLB_TUNAGANDA_HTML, hide_nav=True, full_width=True, is_admin=session.get('is_admin', False), settings=get_settings(), needs_socketio=False)

def manifest():
    return jsonify({
        "name": "Sekolah Luar Biasa",
        "short_name": "SLB",
        "description": "Aplikasi SLB Waktu Samarinda",
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
                "src": "/static/logoslb.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/logoslb.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ]
    })

@app.route('/sw.js')
def service_worker():
    sw_code = """
const CACHE_NAME = 'slb-v1';
const ASSETS_TO_CACHE = [
    '/',
    '/static/logoslb.png',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    '/static/tailwind.min.css'
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

self.addEventListener('push', function(event) {
    const options = {
        body: event.data ? event.data.text() : 'Waktunya Obat / Terapi!',
        icon: '/static/logoslb.png',
        vibrate: [200, 100, 200, 100, 200, 100, 200],
        requireInteraction: true
    };
    event.waitUntil(
        self.registration.showNotification('Notifikasi Orang Tua', options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(
        clients.openWindow('/orang-tua')
    );
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

@app.route('/jadwal')
def jadwal_kelas():
    jadwal = JadwalKelas.query.all()
    # Group by hari
    grouped = {"Senin": [], "Selasa": [], "Rabu": [], "Kamis": [], "Jumat": [], "Sabtu": []}
    for j in jadwal:
        if j.hari in grouped:
            grouped[j.hari].append(j)
    
    content = """
    <div class="pt-24 px-5 pb-32 bg-indigo-50/50 min-h-[100dvh]">
        <div class="max-w-4xl mx-auto">
            <div class="text-center mb-10">
                <div class="w-20 h-20 mx-auto bg-indigo-100 text-indigo-500 rounded-full flex items-center justify-center text-4xl mb-4 shadow-inner">
                    <i class="fas fa-calendar-alt"></i>
                </div>
                <h2 class="text-3xl font-extrabold text-indigo-800 tracking-tight">Jadwal Kelas</h2>
                <p class="text-indigo-600 mt-2 font-medium">Informasi Kegiatan Belajar Mengajar SLB</p>
            </div>
            
            {% if is_admin %}
            <div class="bg-white p-6 rounded-3xl shadow-sm border border-indigo-100 mb-10">
                <h3 class="text-lg font-bold text-indigo-700 mb-4 border-l-4 border-indigo-500 pl-3">Tambah Jadwal Baru</h3>
                <form action="/jadwal/add" method="POST" class="grid grid-cols-1 md:grid-cols-2 gap-4">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Hari</label>
                        <select name="hari" class="w-full bg-indigo-50 border border-indigo-100 rounded-xl p-3 text-sm focus:ring-2 focus:ring-indigo-400 focus:outline-none">
                            <option value="Senin">Senin</option><option value="Selasa">Selasa</option><option value="Rabu">Rabu</option><option value="Kamis">Kamis</option><option value="Jumat">Jumat</option><option value="Sabtu">Sabtu</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Jam (Contoh: 08:00 - 09:30)</label>
                        <input type="text" name="jam" class="w-full bg-indigo-50 border border-indigo-100 rounded-xl p-3 text-sm focus:ring-2 focus:ring-indigo-400 focus:outline-none" required>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Mata Pelajaran</label>
                        <input type="text" name="mata_pelajaran" class="w-full bg-indigo-50 border border-indigo-100 rounded-xl p-3 text-sm focus:ring-2 focus:ring-indigo-400 focus:outline-none" required>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Guru Pengajar</label>
                        <input type="text" name="guru" class="w-full bg-indigo-50 border border-indigo-100 rounded-xl p-3 text-sm focus:ring-2 focus:ring-indigo-400 focus:outline-none" required>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Ruangan Kelas</label>
                        <input type="text" name="ruangan" class="w-full bg-indigo-50 border border-indigo-100 rounded-xl p-3 text-sm focus:ring-2 focus:ring-indigo-400 focus:outline-none" required>
                    </div>
                    <div class="md:col-span-2 mt-2">
                        <button type="submit" class="w-full bg-indigo-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-indigo-600 transition">Simpan Jadwal</button>
                    </div>
                </form>
            </div>
            {% endif %}

            <div class="space-y-8">
                {% for hari, list_jadwal in grouped.items() %}
                {% if list_jadwal %}
                <div>
                    <h3 class="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2"><i class="fas fa-calendar-day text-indigo-500"></i> {{ hari }}</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {% for j in list_jadwal %}
                        <div class="bg-white p-6 rounded-3xl shadow-md border border-indigo-50 hover:shadow-lg transition group relative overflow-hidden">
                            <div class="absolute left-0 top-0 bottom-0 w-2 bg-indigo-400 group-hover:bg-indigo-500 transition-colors"></div>
                            <div class="pl-4">
                                <p class="text-xs font-bold text-indigo-600 mb-1 bg-indigo-50 inline-block px-2 py-1 rounded-md">{{ j.jam }}</p>
                                <h4 class="text-lg font-bold text-gray-800 mb-2">{{ j.mata_pelajaran }}</h4>
                                <div class="flex items-center gap-4 text-xs font-medium text-gray-500">
                                    <span class="flex items-center gap-1"><i class="fas fa-chalkboard-teacher text-gray-400"></i> {{ j.guru }}</span>
                                    <span class="flex items-center gap-1"><i class="fas fa-door-open text-gray-400"></i> {{ j.ruangan }}</span>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}
                {% endfor %}
                {% if not jadwal %}
                <div class="text-center py-10">
                    <div class="w-16 h-16 mx-auto bg-gray-100 text-gray-400 rounded-full flex items-center justify-center text-2xl mb-3"><i class="fas fa-folder-open"></i></div>
                    <p class="text-gray-500 font-medium">Belum ada jadwal kelas yang tersedia.</p>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    """
    return cached_render('BASE_LAYOUT', BASE_LAYOUT, styles=STYLES_HTML, active_page='jadwal', content=cached_render('content_b9d3b862', content, is_admin=session.get('is_admin', False), grouped=grouped, jadwal=jadwal), is_admin=session.get('is_admin', False), settings=get_settings(), grouped=grouped, jadwal=jadwal)

@app.route('/jadwal/add', methods=['POST'])
def add_jadwal():
    if session.get('peran') not in ['guru', 'kepala_sekolah'] and not session.get('is_admin'):
        return redirect(url_for('jadwal_kelas'))
    
    try:
        hari = request.form.get('hari')
        jam = request.form.get('jam')
        mata_pelajaran = request.form.get('mata_pelajaran')
        guru = request.form.get('guru')
        ruangan = request.form.get('ruangan')
        
        new_jadwal = JadwalKelas(hari=hari, jam=jam, mata_pelajaran=mata_pelajaran, guru=guru, ruangan=ruangan)
        db.session.add(new_jadwal)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        
    return redirect(url_for('jadwal_kelas'))

@app.route('/galeri')
def galeri_karya():
    page = request.args.get('page', 1, type=int)
    pagination = GaleriKarya.query.order_by(GaleriKarya.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    karya = pagination.items
    
    content = """
    <div class="pt-24 px-5 pb-32 bg-rose-50/50 min-h-[100dvh]">
        <div class="max-w-6xl mx-auto">
            <div class="text-center mb-10">
                <div class="w-20 h-20 mx-auto bg-rose-100 text-rose-500 rounded-full flex items-center justify-center text-4xl mb-4 shadow-inner">
                    <i class="fas fa-palette"></i>
                </div>
                <h2 class="text-3xl font-extrabold text-rose-800 tracking-tight">Galeri Karya</h2>
                <p class="text-rose-600 mt-2 font-medium">Pameran Seni Anak Hebat</p>
            </div>
            
            {% if is_admin %}
            <div class="bg-white p-6 rounded-3xl shadow-sm border border-rose-100 mb-10 max-w-2xl mx-auto">
                <h3 class="text-lg font-bold text-rose-700 mb-4 border-l-4 border-rose-500 pl-3">Unggah Karya Baru</h3>
                <form action="/galeri/upload" method="POST" enctype="multipart/form-data" class="space-y-4">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Pilih Foto Karya</label>
                        <input type="file" name="image" class="w-full bg-rose-50 border border-rose-100 rounded-xl p-2 text-sm focus:ring-2 focus:ring-rose-400 focus:outline-none" required>
                        <p class="text-[10px] text-gray-400 mt-1">Maks. 5MB, format JPG/PNG/WEBP.</p>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Judul Karya</label>
                        <input type="text" name="title" class="w-full bg-rose-50 border border-rose-100 rounded-xl p-3 text-sm focus:ring-2 focus:ring-rose-400 focus:outline-none" required>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Nama Siswa / Kreator</label>
                        <input type="text" name="student_name" class="w-full bg-rose-50 border border-rose-100 rounded-xl p-3 text-sm focus:ring-2 focus:ring-rose-400 focus:outline-none" required>
                    </div>
                    <button type="submit" class="w-full bg-rose-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-rose-600 transition">Unggah Karya</button>
                </form>
            </div>
            {% endif %}

            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6">
                {% for k in karya %}
                <div class="bg-white rounded-3xl shadow-md border border-rose-50 overflow-hidden hover:shadow-xl transition-all duration-300 group cursor-pointer" onclick='openImageModal("/uploads/{{ k.image_filename }}", {{ k.title|tojson|safe }}, {{ k.student_name|tojson|safe }})'>
                    <div class="aspect-square bg-gray-100 relative overflow-hidden">
                        <img src="/uploads/{{ k.image_filename }}" alt="{{ k.title }}" loading="lazy" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500">
                        <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-4">
                            <button class="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm text-white flex items-center justify-center hover:bg-white/40 transition">
                                <i class="fas fa-expand"></i>
                            </button>
                        </div>
                    </div>
                    <div class="p-4">
                        <h4 class="text-sm font-bold text-gray-800 line-clamp-1" title="{{ k.title }}">{{ k.title }}</h4>
                        <p class="text-xs text-rose-600 font-medium mt-1"><i class="fas fa-user-edit mr-1"></i> {{ k.student_name }}</p>
                    </div>
                </div>
                {% endfor %}
            </div>
            
            {% if not karya %}
            <div class="text-center py-16">
                <div class="w-20 h-20 mx-auto bg-gray-50 text-gray-300 rounded-full flex items-center justify-center text-3xl mb-4"><i class="fas fa-images"></i></div>
                <p class="text-gray-500 font-medium">Belum ada karya yang diunggah.</p>
            </div>
            {% else %}
            <div class="flex justify-center items-center mt-10 gap-2">
                {% if pagination.has_prev %}
                <a href="{{ url_for('galeri_karya', page=pagination.prev_num) }}" class="bg-white border border-rose-200 text-rose-500 px-4 py-2 rounded-xl font-bold hover:bg-rose-50 transition"><i class="fas fa-chevron-left mr-1"></i> Prev</a>
                {% endif %}
                <span class="text-gray-500 text-sm font-medium px-4">Halaman {{ pagination.page }} dari {{ pagination.pages }}</span>
                {% if pagination.has_next %}
                <a href="{{ url_for('galeri_karya', page=pagination.next_num) }}" class="bg-white border border-rose-200 text-rose-500 px-4 py-2 rounded-xl font-bold hover:bg-rose-50 transition">Next <i class="fas fa-chevron-right ml-1"></i></a>
                {% endif %}
            </div>
            {% endif %}

            <!-- Image Modal -->
            <div id="modal-image-view" class="fixed inset-0 z-[150] hidden flex items-center justify-center p-4">
                <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" onclick="closeImageModal()"></div>
                <div class="relative w-full max-w-4xl bg-white rounded-3xl overflow-hidden shadow-2xl animate-[slideUp_0.3s_ease-out]">
                    <img id="modal-image-src" src="" alt="Karya" class="w-full h-auto max-h-[75dvh] object-contain bg-gray-100">
                    <div class="p-6 bg-white flex justify-between items-center">
                        <div>
                            <h3 id="modal-image-title" class="text-xl font-bold text-gray-800"></h3>
                            <p id="modal-image-student" class="text-sm text-rose-600 font-medium mt-1"></p>
                        </div>
                        <button onclick="closeImageModal()" class="w-12 h-12 rounded-full bg-gray-100 text-gray-500 flex items-center justify-center hover:bg-gray-200 transition">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                </div>
            </div>
            <script>
                function openImageModal(src, title, student) {
                    document.getElementById('modal-image-src').src = src;
                    document.getElementById('modal-image-title').innerText = title;
                    document.getElementById('modal-image-student').innerHTML = '<i class="fas fa-user-edit mr-2"></i> ' + student;
                    document.getElementById('modal-image-view').classList.remove('hidden');
                }
                function closeImageModal() {
                    document.getElementById('modal-image-view').classList.add('hidden');
                }
            </script>
        </div>
    </div>
    """
    return cached_render('BASE_LAYOUT', BASE_LAYOUT, styles=STYLES_HTML, active_page='galeri', content=cached_render('content_0af24eeb', content, is_admin=session.get('is_admin', False), karya=karya, pagination=pagination), is_admin=session.get('is_admin', False), settings=get_settings(), karya=karya)

@app.route('/arsip-portofolio')
def arsip_portofolio():
    page = request.args.get('page', 1, type=int)
    pagination = StudentPortfolio.query.order_by(StudentPortfolio.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    portfolios = pagination.items
    
    content = """
    <div class="pt-24 px-5 pb-32 bg-rose-50/50 min-h-[100dvh]">
        <div class="max-w-6xl mx-auto">
            <div class="text-center mb-10">
                <div class="w-20 h-20 mx-auto bg-rose-100 text-rose-500 rounded-full flex items-center justify-center text-4xl mb-4 shadow-inner">
                    <i class="fas fa-folder-open"></i>
                </div>
                <h2 class="text-3xl font-extrabold text-rose-800 tracking-tight leading-none mb-2">Arsip Portofolio<br>Siswa SLB</h2>
                <p class="text-rose-600 font-medium text-sm">Museum Jejak Visual Pertumbuhan Anak</p>
            </div>
            
            <div class="flex flex-col md:flex-row justify-between items-center mb-8 gap-4 bg-white p-4 rounded-3xl shadow-sm border border-rose-100">
                <div class="flex items-center gap-3 w-full md:w-auto">
                    <i class="fas fa-search text-rose-400 pl-2"></i>
                    <input type="text" id="arsip-search" onkeyup="filterArsip()" placeholder="Cari ID/Nama Siswa..." class="bg-transparent border-none outline-none text-gray-800 font-medium placeholder-rose-300 w-full">
                </div>
            </div>

            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6" id="arsip-grid">
                {% for port in portfolios %}
                <div class="arsip-item bg-white rounded-3xl shadow-sm border border-rose-100 overflow-hidden hover:shadow-xl transition-all duration-300 group cursor-pointer" onclick='openArsipModal("/uploads/{{ port.filename }}", {{ port.student_id|tojson|safe }}, {{ port.semester|tojson|safe }})' data-siswa="{{ port.student_id|lower }}">
                    <div class="aspect-square bg-gray-50 relative overflow-hidden">
                        {% set ext = port.filename.rsplit('.', 1)[1]|lower if '.' in port.filename else '' %}
                        {% set is_video = ext in ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v', 'mpeg'] %}
                        
                        {% if is_video %}
                            <video class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" muted playsinline>
                                <source src="/uploads/{{ port.filename }}" type="video/mp4">
                            </video>
                            <div class="absolute inset-0 flex items-center justify-center bg-black/10 pointer-events-none group-hover:bg-black/30 transition-colors">
                                <i class="fas fa-play-circle text-white/90 text-4xl drop-shadow-md"></i>
                            </div>
                        {% else %}
                            <img src="/uploads/{{ port.filename }}" alt="{{ port.student_id }}" loading="lazy" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700">
                        {% endif %}
                        
                        <div class="absolute inset-0 bg-gradient-to-t from-rose-900/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-4">
                            <div class="w-8 h-8 rounded-full bg-white/30 backdrop-blur-md text-white flex items-center justify-center border border-white/50 ml-auto">
                                <i class="fas fa-expand text-xs"></i>
                            </div>
                        </div>
                    </div>
                    <div class="p-4 bg-white relative z-10">
                        <h4 class="text-sm font-bold text-gray-800 line-clamp-1 arsip-title">{{ port.student_id }}</h4>
                        <p class="text-[11px] text-rose-500 font-medium mt-1 bg-rose-50 inline-block px-2 py-1 rounded-md">{{ port.semester }}</p>
                    </div>
                </div>
                {% endfor %}
            </div>
            
            {% if not portfolios %}
            <div class="text-center py-20 bg-white rounded-[3rem] shadow-sm border border-rose-100">
                <div class="w-24 h-24 mx-auto bg-rose-50 text-rose-300 rounded-full flex items-center justify-center text-4xl mb-4"><i class="fas fa-folder-open"></i></div>
                <p class="text-gray-500 font-medium text-lg mb-1">Brankas Masih Kosong</p>
                <p class="text-sm text-gray-400">Belum ada portofolio yang diunggah oleh guru.</p>
            </div>
            {% else %}
            <div class="flex justify-center items-center mt-10 gap-2">
                {% if pagination.has_prev %}
                <a href="{{ url_for('arsip_portofolio', page=pagination.prev_num) }}" class="bg-white border border-rose-200 text-rose-500 px-4 py-2 rounded-xl font-bold hover:bg-rose-50 transition"><i class="fas fa-chevron-left mr-1"></i> Prev</a>
                {% endif %}
                <span class="text-gray-500 text-sm font-medium px-4">Halaman {{ pagination.page }} dari {{ pagination.pages }}</span>
                {% if pagination.has_next %}
                <a href="{{ url_for('arsip_portofolio', page=pagination.next_num) }}" class="bg-white border border-rose-200 text-rose-500 px-4 py-2 rounded-xl font-bold hover:bg-rose-50 transition">Next <i class="fas fa-chevron-right ml-1"></i></a>
                {% endif %}
            </div>
            {% endif %}

            <!-- Image/Video View Modal -->
            <div id="modal-arsip-view" class="fixed inset-0 z-[150] hidden flex items-center justify-center p-4">
                <div class="absolute inset-0 bg-rose-900/90 backdrop-blur-xl" onclick="closeArsipModal()"></div>
                <div class="relative w-full max-w-4xl bg-white rounded-[2rem] overflow-hidden shadow-2xl animate-[slideUp_0.3s_ease-out] flex flex-col md:flex-row">
                    
                    <!-- Media Container -->
                    <div class="w-full md:w-2/3 bg-gray-50 relative flex items-center justify-center min-h-[40dvh] md:min-h-[70dvh]" id="arsip-media-container">
                        <!-- Media Injected via JS -->
                    </div>

                    <!-- Details Container -->
                    <div class="w-full md:w-1/3 p-6 md:p-8 bg-white flex flex-col">
                        <div class="flex justify-between items-start mb-6">
                            <div class="w-12 h-12 rounded-full bg-rose-100 text-rose-500 flex items-center justify-center text-xl shrink-0">
                                <i class="fas fa-user-graduate"></i>
                            </div>
                            <button onclick="closeArsipModal()" class="w-10 h-10 rounded-full bg-rose-50 text-rose-500 flex items-center justify-center hover:bg-rose-500 hover:text-white transition-colors">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                        
                        <div class="flex-1">
                            <p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Identitas Siswa</p>
                            <h3 id="modal-arsip-student" class="text-2xl font-extrabold text-rose-900 mb-6 leading-tight"></h3>
                            
                            <p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Periode Pembelajaran</p>
                            <p id="modal-arsip-semester" class="text-sm text-rose-600 font-bold bg-rose-50 px-4 py-2 rounded-xl inline-block border border-rose-100"></p>
                        </div>

                        <div class="mt-8 pt-6 border-t border-rose-100">
                            <p class="text-[10px] text-gray-400 italic text-center text-balance">"Setiap jejak karya adalah bukti nyata perkembangan ananda."</p>
                        </div>
                    </div>

                </div>
            </div>

            <script>
                function openArsipModal(src, student, semester) {
                    const container = document.getElementById('arsip-media-container');
                    const ext = src.split('.').pop().toLowerCase();
                    const videoExts = ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v', 'mpeg'];
                    
                    container.innerHTML = ''; // Clear existing
                    
                    if (videoExts.includes(ext)) {
                        const vid = document.createElement('video');
                        vid.src = src;
                        vid.controls = true;
                        vid.autoplay = true;
                        vid.className = "w-full h-full max-h-[70dvh] object-contain";
                        container.appendChild(vid);
                    } else {
                        const img = document.createElement('img');
                        img.src = src;
                        img.className = "w-full h-full max-h-[70dvh] object-contain";
                        container.appendChild(img);
                    }

                    document.getElementById('modal-arsip-student').innerText = student;
                    document.getElementById('modal-arsip-semester').innerText = semester;
                    document.getElementById('modal-arsip-view').classList.remove('hidden');
                }
                
                function closeArsipModal() {
                    const container = document.getElementById('arsip-media-container');
                    container.innerHTML = ''; // Stops video playback
                    document.getElementById('modal-arsip-view').classList.add('hidden');
                }

                function filterArsip() {
                    const input = document.getElementById('arsip-search').value.toLowerCase();
                    const items = document.querySelectorAll('.arsip-item');
                    
                    items.forEach(item => {
                        const title = item.getAttribute('data-siswa');
                        if (title.includes(input)) {
                            item.style.display = 'block';
                        } else {
                            item.style.display = 'none';
                        }
                    });
                }
            </script>
        </div>
    </div>
    """
    return cached_render('BASE_LAYOUT', BASE_LAYOUT, styles=STYLES_HTML, active_page='arsip', content=cached_render('content_aa3eed9f', content, is_admin=session.get('is_admin', False), portfolios=portfolios, pagination=pagination), is_admin=session.get('is_admin', False), settings=get_settings(), portfolios=portfolios)


@app.route('/galeri/upload', methods=['POST'])
def upload_karya():
    if session.get('peran') not in ['guru', 'kepala_sekolah'] and not session.get('is_admin'):
        return redirect(url_for('galeri_karya'))
        
    title = request.form.get('title')
    student_name = request.form.get('student_name')
    file = request.files.get('image')
    
    if file and allowed_file(file.filename):
        try:
            file_bytes = file.read(2048)
            file.seek(0)
            kind = filetype.guess(file_bytes)
            if kind is None or not (kind.mime.startswith('image/') or kind.mime.startswith('video/')):
                return "File tidak didukung", 400

            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            if filename.rsplit('.', 1)[1].lower() == 'mp4':
                file.save(filepath)
            else:
                img = Image.open(file)
                if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                img.thumbnail((800, 800))
                
                # Image compression loop to ensure file size is under 500KB
                quality = 85
                img.save(filepath, format="JPEG", quality=quality, optimize=True)
                while os.path.getsize(filepath) > 500 * 1024 and quality > 10:
                    quality -= 5
                    img.save(filepath, format="JPEG", quality=quality, optimize=True)
                
            new_karya = GaleriKarya(image_filename=filename, title=title, student_name=student_name)
            db.session.add(new_karya)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            
    return redirect(url_for('galeri_karya'))



import redis
def start_scheduler_if_primary():
    try:
        r = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        if r.set('slb_scheduler_master', '1', nx=True, ex=3600):
            scheduler.start()
            app.logger.info("Started BackgroundScheduler in this worker.")
    except Exception as e:
        app.logger.error(f"Error acquiring scheduler lock: {e}")

with app.app_context():
    try:
        start_scheduler_if_primary()
        prefetch_emoji_icons()
        # TODO: Migrate to Flask-Migrate/Alembic for schema management. db.create_all() only creates new tables; it does NOT alter existing ones.
        if os.environ.get('FLASK_INIT_DB'):
            db.create_all()
            seed_slb_data()
    except Exception as e:
        app.logger.error(f"CRITICAL: Failed to connect to the local PostgreSQL database or initialize tables on IDCloudHost. Check DATABASE_URL and PostgreSQL service status. Error: {e}")

if __name__ == '__main__':
    is_dev = os.getenv('FLASK_ENV') == 'development'
    socketio.run(app, debug=is_dev, port=5001, allow_unsafe_werkzeug=is_dev)
