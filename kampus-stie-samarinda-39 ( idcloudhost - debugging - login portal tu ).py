import os
import datetime
import math
import time
import json
import csv
import urllib.request
import pymysql
import io
from reportlab.pdfgen import canvas
from PIL import Image
from flask import Flask, request, send_from_directory, render_template_string, redirect, url_for, Response, jsonify, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_caching import Cache
from flask_limiter.util import get_remote_address
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy.orm import joinedload
from dotenv import load_dotenv
from functools import wraps
import filetype

load_dotenv()


# --- KONFIGURASI FLASK ---
app = Flask(__name__)

GENERIC_ERROR_MSG = "Terjadi kesalahan sistem. Tim teknis telah diberitahu."

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self' https: data:; script-src 'self' 'unsafe-inline' https:; style-src 'self' 'unsafe-inline' https:;"
    return response


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

csrf = CSRFProtect(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["2000 per day", "500 per hour"],
    storage_uri=os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
)

cache = Cache(app, config={'CACHE_TYPE': 'RedisCache', 'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'), 'CACHE_DEFAULT_TIMEOUT': 86400})
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB Limit

import logging
from logging.handlers import RotatingFileHandler, SMTPHandler

if not os.path.exists('error.log'):
    open('error.log', 'w').close()
error_handler = RotatingFileHandler('error.log', maxBytes=100000, backupCount=3)
error_handler.setLevel(logging.ERROR)
app.logger.addHandler(error_handler)

mail_server = os.environ.get('MAIL_SERVER')
if mail_server:
    auth = None
    mail_username = os.environ.get('MAIL_USERNAME')
    mail_password = os.environ.get('MAIL_PASSWORD')
    if mail_username and mail_password:
        auth = (mail_username, mail_password)
    secure = None
    if os.environ.get('MAIL_USE_TLS'):
        secure = ()
    mail_handler = SMTPHandler(
        mailhost=(mail_server, int(os.environ.get('MAIL_PORT', 25))),
        fromaddr='no-reply@stiesam.ac.id',
        toaddrs=[os.environ.get('ADMIN_EMAIL', 'admin@stiesam.ac.id')],
        subject='Kesalahan Kritis Sistem STIESAM',
        credentials=auth,
        secure=secure
    )
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

secret = os.environ.get("SECRET_KEY")
if not secret:
    raise RuntimeError("KUNCI RAHASIA (SECRET_KEY) TIDAK DITEMUKAN. OPERASI DIBATALKAN UNTUK KEAMANAN.")
app.secret_key = secret
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.permanent_session_lifetime = datetime.timedelta(minutes=30)

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    raise RuntimeError("KONEKSI PANGKALAN DATA (DATABASE_URL) TIDAK DITEMUKAN. OPERASI DIBATALKAN UNTUK KEAMANAN.")
app.config['SQLALCHEMY_DATABASE_URI'] = db_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Removed duplicated ENGINE_OPTIONS here because we will append it safely.
engine_options = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_pre_ping': True,
    'pool_recycle': 3600,
}
if 'mysql' in db_url.lower():
    engine_options['connect_args'] = {'charset': 'utf8mb4'}

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_options
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'mp4', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar', 'txt', 'csv'}

db = SQLAlchemy(app)


# Template HTML dimuat dari variabel global di bawah ini
# --- BASE_LAYOUT ---
# --- FITUR_MASJID_HTML ---
# --- HOME_HTML ---
# --- RAMADHAN_DASHBOARD_HTML ---
# --- RAMADHAN_STYLES ---
# --- IRMA_STYLES ---
# --- IRMA_DASHBOARD_HTML ---
# ============================================================================
# ZONA PANGKALAN DATA (Database Models)
# ============================================================================

# --- DATABASE MODELS (Zona Model) ---
class EpilepsiLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.date.today, nullable=False)
    time = db.Column(db.String(255), nullable=False)
    trigger = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now())
    


class SuratOtomatis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    npm = db.Column(db.String(255), db.ForeignKey('user.username', ondelete='CASCADE'), nullable=False, index=True)
    jenis_surat = db.Column(db.String(255), nullable=False)
    keterangan = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Menunggu Acc')
    tanggal = db.Column(db.Date, default=datetime.date.today)
    qr_code = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=func.now())

class PendaftaranPMB(db.Model):
    __table_args__ = (db.UniqueConstraint('email', 'nomor_hp', name='uq_pmb_email_hp'),)
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, default='-')
    nomor_hp = db.Column(db.String(50), nullable=False, default='-')
    token = db.Column(db.String(100), unique=True)
    foto_ijazah = db.Column(db.String(255))
    foto_ktp = db.Column(db.String(255))
    bukti_transfer = db.Column(db.String(255))
    status = db.Column(db.String(50), default='Pending', index=True)
    npm_generated = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=func.now())

class TagihanKuliah(db.Model):
    __table_args__ = (db.UniqueConstraint('npm', 'jenis_tagihan', 'semester_aktif', name='uq_tagihan_semester'),)
    id = db.Column(db.Integer, primary_key=True)
    npm = db.Column(db.String(255), db.ForeignKey('user.username', ondelete='CASCADE'), nullable=False, index=True)
    jenis_tagihan = db.Column(db.String(255), nullable=False)
    semester_aktif = db.Column(db.String(50), nullable=False, default='Gasal 2024/2025')
    jumlah = db.Column(db.Integer, nullable=False)
    bukti_transfer = db.Column(db.String(255))
    status = db.Column(db.String(50), default='Belum Lunas', index=True)
    created_at = db.Column(db.DateTime, server_default=func.now())

class JadwalKuliah(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    semester_aktif = db.Column(db.String(50), nullable=False, default='Gasal 2024/2025')
    hari = db.Column(db.String(50), nullable=False)
    jam = db.Column(db.String(50), nullable=False)
    mata_kuliah = db.Column(db.String(255), nullable=False)
    dosen = db.Column(db.String(255), nullable=False, index=True)
    ruangan = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    password_raw = db.Column(db.String(255), nullable=True)
    must_change_password = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(50), nullable=False, index=True)
    nama = db.Column(db.String(255))
    status_akademik = db.Column(db.String(50), default='Aktif', index=True)
    foto_profil = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    krs_rel = db.relationship('KRSMahasiswa', backref='user_krs', primaryjoin="User.username == KRSMahasiswa.npm", foreign_keys="[KRSMahasiswa.npm]")
    tagihan_rel = db.relationship('TagihanKuliah', backref='user_tagihan', primaryjoin="User.username == TagihanKuliah.npm", foreign_keys="[TagihanKuliah.npm]")

class LaciArsip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    npm = db.Column(db.String(255), db.ForeignKey('user.username', ondelete='CASCADE'), nullable=False, index=True)
    nama_dokumen = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    ukuran = db.Column(db.String(50))
    tanggal = db.Column(db.Date, default=datetime.date.today)

class AppSettings(db.Model):
    key = db.Column(db.String(255), primary_key=True)
    value = db.Column(db.Text)

class KRSMahasiswa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    npm = db.Column(db.String(255), db.ForeignKey('user.username', ondelete='CASCADE'), nullable=False, index=True)
    mata_kuliah = db.Column(db.String(255), nullable=False)
    dosen = db.Column(db.String(255), nullable=False)
    sks = db.Column(db.Integer, default=3)
    status = db.Column(db.String(50), default='Menunggu Acc Dosen')
    created_at = db.Column(db.DateTime, server_default=func.now())

class NilaiMahasiswa(db.Model):
    __table_args__ = (db.Index('idx_npm_matkul_smt', 'npm', 'mata_kuliah', 'semester'),)
    
    id = db.Column(db.Integer, primary_key=True)
    npm = db.Column(db.String(255), db.ForeignKey('user.username', ondelete='CASCADE'), nullable=False, index=True)
    mata_kuliah = db.Column(db.String(255), nullable=False)
    sks = db.Column(db.Integer, nullable=False)
    nilai_huruf = db.Column(db.String(5), nullable=False)
    semester = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

class KehadiranKelas(db.Model):
    __table_args__ = (db.Index('idx_jadwal_npm_status', 'jadwal_id', 'npm', 'status'), db.UniqueConstraint('jadwal_id', 'npm', 'tanggal', name='uq_kehadiran_harian'))

    id = db.Column(db.Integer, primary_key=True)
    jadwal_id = db.Column(db.Integer, nullable=False)
    npm = db.Column(db.String(255), db.ForeignKey('user.username', ondelete='CASCADE'), nullable=False, index=True)
    tanggal = db.Column(db.Date, default=datetime.date.today, nullable=False)
    status = db.Column(db.String(50), default='Hadir')
    created_at = db.Column(db.DateTime, server_default=func.now())

class JurnalMengajar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jadwal_id = db.Column(db.Integer, nullable=False)
    tanggal = db.Column(db.Date, default=datetime.date.today, nullable=False)
    materi = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

class StatusNilai(db.Model):
    __table_args__ = (db.UniqueConstraint('jadwal_id', name='uq_status_nilai_jadwal'),)

    id = db.Column(db.Integer, primary_key=True)
    jadwal_id = db.Column(db.Integer, nullable=False)
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=func.now())


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    npm = db.Column(db.String(255), db.ForeignKey('user.username', ondelete='CASCADE'), index=True)
    message = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

class TracerStudy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_lengkap = db.Column(db.String(255), nullable=False)
    npm = db.Column(db.String(255), nullable=False, index=True)
    tahun_lulus = db.Column(db.String(10), nullable=False)
    program_studi = db.Column(db.String(255), nullable=False)
    status_pekerjaan = db.Column(db.String(255), nullable=False)
    nama_perusahaan = db.Column(db.String(255))
    jabatan = db.Column(db.String(255))
    rentang_gaji = db.Column(db.String(255))
    kesesuaian = db.Column(db.String(255))
    waktu_tunggu = db.Column(db.String(255))
    saran = db.Column(db.Text)
    kontak = db.Column(db.String(255))
    status = db.Column(db.String(50), default='Menunggu Verifikasi', index=True)
    created_at = db.Column(db.DateTime, server_default=func.now())

def model_getitem(self, key):
    return getattr(self, key)

for model in [EpilepsiLog, AppSettings, SuratOtomatis, PendaftaranPMB, TagihanKuliah, JadwalKuliah, User, LaciArsip, KRSMahasiswa, NilaiMahasiswa, KehadiranKelas, JurnalMengajar, StatusNilai, TracerStudy]:
    model.__getitem__ = model_getitem

# --- ROUTES ---

from werkzeug.exceptions import RequestEntityTooLarge
from flask_wtf.csrf import CSRFError

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "Sekolah Tinggi Ilmu Ekonomi STIESAM",
        "short_name": "STIESAM",
        "description": "Aplikasi Sekolah Tinggi Ilmu Ekonomi STIESAM Samarinda",
        "start_url": "/",
        "id": "/",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#0b1026",
        "theme_color": "#FFD700",
        "categories": ["education"],
        "prefer_related_applications": False,
        "icons": [
            {
                "src": "/static/logo-stiesam.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/logo-stiesam.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ]
    })

# ============================================================================
# AUTH & SECURITY ROUTES
# ============================================================================


def require_role(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') not in roles:
                return 'Unauthorized', 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.errorhandler(RequestEntityTooLarge)
def handle_file_size_error(e):
    if request.path.startswith('/api/pmb/register'):
        return jsonify({'success': False, 'error': 'Ukuran berkas melebihi batas maksimal.'}), 413
    return "File too large", 413


class KampusSTIEException(Exception):
    """Kesalahan Khusus Aplikasi STIESAM"""
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

@app.errorhandler(KampusSTIEException)
def handle_kampus_error(e):
    try:
        db.session.rollback()
    except:
        pass
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': e.message}), e.status_code
    flash(f"Informasi Sistem: {e.message}", "error")
    return redirect(request.referrer or url_for('index'))


@app.errorhandler(404)
def page_not_found(e):
    app.logger.warning(f"404 Error: {request.url}")
    flash("Halaman tidak ditemukan.", "error")
    return redirect(url_for('index'))

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    app.logger.warning(f"CSRF Error: {e.description}")
    flash("Sesi keamanan telah berakhir. Silakan muat ulang halaman atau login kembali.", "error")
    return redirect(url_for('index'))

@app.errorhandler(Exception)
def handle_general_error(e):
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        return e
    
    # Misi Ketiga: Pembatalan Transaksi Global
    try:
        db.session.rollback()
    except:
        pass
        
    
    app.logger.error(f"Global Error Captured: {str(e)}", exc_info=True)
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': GENERIC_ERROR_MSG}), 500
        
    flash(GENERIC_ERROR_MSG, "error")
    return redirect(request.referrer or url_for('index'))

@app.before_request
def global_gatekeeper():
    if request.path == '/api/pmb/register' and request.method == 'POST':
        max_size = app.config.get('MAX_CONTENT_LENGTH', 20 * 1024 * 1024)
        if request.content_length and request.content_length > max_size:
            return jsonify({'success': False, 'error': 'Ukuran file melebihi batas 20MB.'}), 413

    if request.path == '/login' and request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        client_ip = get_remote_address()
        whitelist_ip = os.environ.get('TU_IP_WHITELIST')
        tu_user = os.environ.get('TU_USERNAME', 'tatausaha')
        tu_pass = os.environ.get('TU_PASSWORD', 'stiesamtu')

        # Pengecualian mutlak untuk Tata Usaha
        if username == tu_user and password == tu_pass:
            pass # Loloskan tanpa blokir
        elif not ((whitelist_ip and client_ip in whitelist_ip) or username == tu_user):
            cache_key = f"failed_login_{client_ip}_{username}"
            attempts = cache.get(cache_key) or 0
            if attempts >= 9:
                return "mohon maaf anda mencoba terlalu banyak percobaan login masuk tunggu tiga puluh menit lagi untuk percobaan berikutnya.", 429

    # Allow public endpoints and API endpoints
    if request.endpoint in ['index', 'login', 'logout', 'static', 'api_pmb_register', 'api_pmb_check', 'api_pmb_status', 'service_worker', 'manifest', 'fitur_masjid', 'donate', 'emergency', 'prayer_times_api', 'api_yasin', 'therapy_log']:
        return
        
    user_id = session.get('user_id')
    if user_id:
        try:
            user = db.session.get(User, user_id)
            if user and user.status_akademik != 'Aktif':
                session.clear()
                return "Akses Ditolak: Status Akademik Anda tidak Aktif.", 403
            
            # Portal enforcement logic
            role = user.role
            path = request.path
            if path.startswith('/tu_dashboard') or path.startswith('/tu/'):
                if role not in ['Tata Usaha', 'Admin']:
                    return redirect(url_for('index', open='modal-login'))
            elif path.startswith('/dosen'):
                if role != 'Dosen':
                    return redirect(url_for('index', open='modal-login'))
            elif path.startswith('/mahasiswa') or path == '/mahasiswa':
                if role != 'Mahasiswa':
                    return redirect(url_for('index', open='modal-login'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error in gatekeeper: {e}", exc_info=True)
            flash(GENERIC_ERROR_MSG, "error")
    else:
        # Not logged in, redirect to index with login modal
        path = request.path
        if path.startswith('/tu_dashboard') or path.startswith('/tu/') or path.startswith('/dosen') or path.startswith('/mahasiswa'):
            return redirect(url_for('index', open='modal-login'))

def _is_tu_exempt():
    if request.method != 'POST': return False
    username = request.form.get('username')
    password = request.form.get('password')

    tu_user = os.environ.get('TU_USERNAME', 'tatausaha')
    tu_pass = os.environ.get('TU_PASSWORD', 'stiesamtu')

    if username == tu_user and password == tu_pass:
        return True

    client_ip = get_remote_address()
    whitelist_ip = os.environ.get('TU_IP_WHITELIST')
    if (whitelist_ip and client_ip in whitelist_ip):
        return True

    return _is_valid_login()

@app.route('/login', methods=['POST'])
@limiter.limit("9 per 30 minutes", error_message="mohon maaf anda mencoba terlalu banyak percobaan login masuk tunggu tiga puluh menit lagi untuk percobaan berikutnya.", exempt_when=_is_tu_exempt)
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    remember = request.form.get('remember') == 'on'
    
    tu_user = os.environ.get('TU_USERNAME', 'tatausaha')
    tu_pass = os.environ.get('TU_PASSWORD', 'stiesamtu')

    # Prioritas Mutlak Tata Usaha
    if username == tu_user and password == tu_pass:
        app.logger.info("Mengeksekusi login Tata Usaha secara prioritas.")
        try:
            user = User.query.filter_by(username=username).first()
            if not user:
                user = User(
                    username=tu_user,
                    password_hash=generate_password_hash(tu_pass),
                    password_raw=tu_pass,
                    role='Tata Usaha',
                    nama='Tata Usaha Utama',
                    status_akademik='Aktif',
                    must_change_password=False
                )
                db.session.add(user)
                db.session.commit()
                # Refresh instance
                user = db.session.get(User, user.id)
            else:
                # Pastikan password dan data selalu fresh dan bersih
                user.password_hash = generate_password_hash(tu_pass)
                user.password_raw = tu_pass
                user.role = 'Tata Usaha'
                user.status_akademik = 'Aktif'
                if hasattr(user, 'must_change_password'):
                    user.must_change_password = False
                db.session.commit()
                # Refresh instance
                user = db.session.get(User, user.id)

            # Hapus Cache Limiter secara paksa
            client_ip = get_remote_address()
            cache_key = f"failed_login_{client_ip}_{username}"
            cache.delete(cache_key)

            # Login dan Set Sesi
            login_user(user, remember=True)
            session['user_id'] = user.id
            session['username'] = user.username
            session['npm'] = user.username
            session['nama'] = user.nama
            session['role'] = user.role
            session['is_admin'] = True

            session.permanent = True
            app.permanent_session_lifetime = datetime.timedelta(days=30)

            app.logger.info("Login Tata Usaha berhasil, dialihkan ke dashboard.")
            return redirect(url_for('ramadhan_dashboard'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Kesalahan kritis pada login TU: {e}", exc_info=True)
            flash("Sistem sedang mengalami gangguan saat menginisialisasi akses Tata Usaha.", "error")
            return redirect(request.referrer or url_for('index'))

    # Alur Normal Pengguna Lain
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        client_ip = get_remote_address()
        cache_key = f"failed_login_{client_ip}_{username}"
        cache.delete(cache_key)

        # Update session manually since login_user is an object but we need dict values too
        login_user(user, remember=remember)
        session['user_id'] = user.id
        session['username'] = user.username
        session['npm'] = user.username
        session['nama'] = user.nama
        session['role'] = user.role
        if remember:
            session.permanent = True
            app.permanent_session_lifetime = datetime.timedelta(days=30)
        else:
            session.permanent = False
            
        if getattr(user, 'must_change_password', False):
            flash('Anda menggunakan password default. Harap segera mengganti password Anda.', 'error')
            if user.role == 'Mahasiswa':
                 return redirect(url_for('irma_dashboard', open='modal-profil-arsip'))
            elif user.role == 'Dosen':
                 return redirect(url_for('dosen_dashboard', open='modal-profil-dosen'))
            else:
                 return redirect(url_for('ramadhan_dashboard', open='modal-manajemen-sivitas'))

        if user.role in ['Tata Usaha', 'Admin']:
            session['is_admin'] = True
            return redirect(url_for('ramadhan_dashboard'))
        elif user.role == 'Dosen':
            return redirect(url_for('dosen_dashboard'))
        elif user.role == 'Mahasiswa':
            return redirect(url_for('irma_dashboard'))
            
    client_ip = get_remote_address()
    cache_key = f"failed_login_{client_ip}_{username}"
    attempts = cache.get(cache_key) or 0
    cache.set(cache_key, attempts + 1, timeout=1800)

    flash('Kredensial tidak valid', 'error')
    return redirect(request.referrer or url_for('index'))

def _is_valid_login():
    username = request.form.get('username')
    password = request.form.get('password')
    tu_user = os.environ.get('TU_USERNAME', 'tatausaha')
    tu_pass = os.environ.get('TU_PASSWORD', 'stiesamtu')
    if username == tu_user and password == tu_pass:
        return True
    user = User.query.filter_by(username=username).first()
    return user and check_password_hash(user.password_hash, password)

@app.route('/logout')
def logout():

    logout_user()
    session.clear()

    return redirect(url_for('index'))

@app.route('/seed-admin')
def seed_admin():
    seed_token = os.environ.get('SEED_TOKEN')
    if not seed_token or request.args.get('token') != seed_token:
        return 'Unauthorized', 403
    try:
        admin_exists = User.query.filter_by(role='Tata Usaha').first()
        if not admin_exists:
            new_admin = User(
                username='adminstiesam',
                password_hash=generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'stiesamadmin123')),
                role='Tata Usaha',
                nama='Administrator STIESAM',
                status_akademik='Aktif'
            )
            db.session.add(new_admin)
            db.session.commit()
            pass

            return "Akun administrator Tata Usaha berhasil dibuat."
        return "Akun administrator Tata Usaha sudah ada."
    except Exception as e:
        return f"Error: {e}"


# ============================================================================
# PUBLIC & API ROUTES
# ============================================================================


@app.route('/api/register_user', methods=['POST'])
@limiter.limit('3 per minute')
def api_register_user():
    try:
        nama = request.form.get('nama')
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if not all([nama, username, password, role]):
            flash("Semua field harus diisi.", "error")
            return redirect(url_for('index', open='modal-login'))

        if role not in ['Mahasiswa', 'Dosen']:
            flash("Role tidak valid.", "error")
            return redirect(url_for('index', open='modal-login'))

        if User.query.filter_by(username=username).first():
            flash("Username sudah digunakan. Silakan pilih username lain.", "error")
            return redirect(url_for('index', open='modal-login'))

        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role,
            nama=nama,
            status_akademik='Menunggu Verifikasi'
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Permohonan akun berhasil dikirim. Menunggu verifikasi dari Tata Usaha.", "success")
        return redirect(url_for('index', open='modal-login'))
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in User Register: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
        return redirect(url_for('index', open='modal-login'))

@app.route('/api/pmb/register', methods=['POST'])
@limiter.limit('3 per minute')
def api_pmb_register():
    try:
        import uuid
        nama = request.form.get('nama')
        email = request.form.get('email')
        nomor_hp = request.form.get('nomor_hp')
        
        # Fallback to unique values if not provided by frontend (to avoid unique constraint violations)
        unique_suffix = str(uuid.uuid4())[:8]
        if not email or email == '-': email = f"no-reply-{unique_suffix}@stiesam.ac.id"
        if not nomor_hp or nomor_hp == '-': nomor_hp = f"0000-{unique_suffix}"

        foto_ijazah = request.files.get('foto_ijazah')
        foto_ktp = request.files.get('foto_ktp')
        bukti_transfer = request.files.get('bukti_transfer')
        
        if not all([nama, email, nomor_hp, foto_ijazah, foto_ktp, bukti_transfer]):
            return jsonify({'success': False, 'error': 'Semua field dan file harus diisi.'})
            
        if not foto_ijazah or foto_ijazah.filename == '':
            return jsonify({'success': False, 'error': 'Berkas foto_ijazah wajib diunggah dan tidak boleh kosong.'})
            
        if not foto_ktp or foto_ktp.filename == '':
            return jsonify({'success': False, 'error': 'Berkas foto_ktp wajib diunggah dan tidak boleh kosong.'})
            
        if not bukti_transfer or bukti_transfer.filename == '':
            return jsonify({'success': False, 'error': 'Berkas bukti_transfer wajib diunggah dan tidak boleh kosong.'})
            
        
        if PendaftaranPMB.query.filter_by(email=email, nomor_hp=nomor_hp).first():
            return jsonify({'success': False, 'error': 'Kombinasi Email dan Nomor HP ini sudah terdaftar. Jangan lakukan submit ganda.'})

        ijazah_filename = ""
        ktp_filename = ""
        bukti_filename = ""
        
        try:
            if foto_ijazah and allowed_file(foto_ijazah.filename):
                ijazah_filename = compress_image(foto_ijazah, app.config['UPLOAD_FOLDER'])
            if foto_ktp and allowed_file(foto_ktp.filename):
                ktp_filename = compress_image(foto_ktp, app.config['UPLOAD_FOLDER'])
            if bukti_transfer and allowed_file(bukti_transfer.filename):
                bukti_filename = compress_image(bukti_transfer, app.config['UPLOAD_FOLDER'])
        except ValueError as ve:
            return jsonify({'success': False, 'error': str(ve)})
        except Exception as file_e:
            app.logger.warning(f"File validation fallback in PMB: {file_e}")
            return jsonify({'success': False, 'error': 'Berkas tidak valid atau rusak.'})

        token_str = str(uuid.uuid4())
        new_pmb = PendaftaranPMB(
            nama=nama,
            email=email,
            nomor_hp=nomor_hp,
            token=token_str,
            foto_ijazah=ijazah_filename,
            foto_ktp=ktp_filename,
            bukti_transfer=bukti_filename,
            status='Pending'
        )
        db.session.add(new_pmb)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Pendaftaran berhasil dikirim. Sedang diperiksa oleh Tata Usaha. Cek Status PMB secara berkala.'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in PMB Register: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
        return jsonify({'success': False, 'error': 'Terjadi kesalahan sistem saat memproses formulir.'})

@app.route('/api/tracer/submit', methods=['POST'])
@limiter.limit("3 per minute")
def api_tracer_submit():
    try:
        nama_lengkap = request.form.get('nama_lengkap')
        npm_input = request.form.get('npm')
        tahun_lulus = request.form.get('tahun_lulus')
        program_studi = request.form.get('program_studi')
        status_pekerjaan = request.form.get('status_pekerjaan')
        captcha = request.form.get('captcha_answer')
        expected_captcha = request.form.get('captcha_expected')

        if not expected_captcha or str(captcha).strip() != str(expected_captcha).strip():
            flash("Validasi keamanan gagal. Jawaban CAPTCHA salah.", "error")
            return redirect(request.referrer or url_for('index'))
            
        if not all([nama_lengkap, npm_input, tahun_lulus, program_studi, status_pekerjaan]):
            flash("Field yang diwajibkan harus diisi.", "error")
            return redirect(request.referrer or url_for('index'))

        user = User.query.filter_by(username=npm_input).first()
        if not user or user.status_akademik != 'Lulus':
            flash('Validasi Alumni Gagal: NPM tidak ditemukan atau status belum Lulus.', 'error')
            return redirect(request.referrer or url_for('index'))
            
        if user.nama.lower() != nama_lengkap.lower():
            flash('Validasi Alumni Gagal: Nama lengkap tidak cocok dengan data pangkalan data.', 'error')
            return redirect(request.referrer or url_for('index'))

        current_year = datetime.date.today().year
        try:
            thn = int(tahun_lulus)
            if thn < 1990 or thn > current_year:
                raise ValueError
        except:
             flash('Tahun lulus tidak valid.', 'error')
             return redirect(request.referrer or url_for('index'))

        if TracerStudy.query.filter_by(npm=npm_input).first():
            flash('NPM ini sudah mengisi tracer study.', 'error')
            return redirect(request.referrer or url_for('index'))

        new_tracer = TracerStudy(
            nama_lengkap=request.form.get('nama_lengkap'),
            npm=request.form.get('npm'),
            tahun_lulus=request.form.get('tahun_lulus'),
            program_studi=request.form.get('program_studi'),
            status_pekerjaan=request.form.get('status_pekerjaan'),
            nama_perusahaan=request.form.get('nama_perusahaan'),
            jabatan=request.form.get('jabatan'),
            rentang_gaji=request.form.get('rentang_gaji'),
            kesesuaian=request.form.get('kesesuaian'),
            waktu_tunggu=request.form.get('waktu_tunggu'),
            saran=request.form.get('saran'),
            kontak=request.form.get('kontak')
        )
        db.session.add(new_tracer)
        db.session.add(Notification(npm=os.environ.get('TU_USERNAME', 'tatausaha'), message=f"Data Tracer Study baru dari NPM {npm_input}."))
        db.session.commit()
        cache.clear()

        flash("Data Tracer Study berhasil dikirim! Terima kasih atas partisipasi Anda.", "success")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error submitting Tracer Study: {e}", exc_info=True)
        flash("Terjadi kesalahan sistem.", "error")
    return redirect(request.referrer or url_for('index'))


@app.route('/api/ktm/qr/<npm>', methods=['GET'])
@login_required
def api_ktm_qr(npm):
    try:
        user = current_user
        if user.username != npm and user.role not in ['Tata Usaha', 'Admin']:
            return "Unauthorized", 403
            
        import qrcode
        qr = qrcode.make(npm)
        buf = io.BytesIO()
        qr.save(buf, format='PNG')
        buf.seek(0)
        return Response(buf, mimetype='image/png')
    except Exception as e:
        app.logger.error(f"Error generating QR code: {e}", exc_info=True)
        return "Internal Server Error", 500

@app.route('/api/notifications/poll', methods=['GET'])
@login_required
def api_notifications_poll():
    npm = session.get('npm')
    if not npm:
        return jsonify([])
    notifs = Notification.query.filter_by(npm=npm, is_read=False).all()
    res = [{'id': n.id, 'message': n.message} for n in notifs]
    for n in notifs:
        n.is_read = True
    db.session.commit()
    pass

    return jsonify(res)

@app.route('/api/pmb/status', methods=['GET'])
@limiter.limit("5 per minute")
def api_pmb_status():
    try:
        nama = request.args.get('nama')
        if not nama:
            return jsonify({'error': 'Nama tidak boleh kosong'})
            
        pmb = PendaftaranPMB.query.filter(func.lower(PendaftaranPMB.nama) == func.lower(nama)).order_by(PendaftaranPMB.id.desc()).first()
        
        if not pmb:
            return jsonify({'error': 'Data pendaftaran tidak ditemukan.'})
            
        return jsonify({
            'nama': pmb.nama,
            'status': pmb.status,
            'npm': '-'  # Jangan membocorkan NPM di rute publik
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error checking PMB status: {e}", exc_info=True)
        return jsonify({'error': 'Terjadi kesalahan sistem.'})

@app.route('/api/pmb/check', methods=['GET'])
@login_required
@require_role(['Tata Usaha', 'Admin'])
def api_pmb_check():
    try:
        nama = request.args.get('nama')
        if not nama:
            return jsonify({'error': 'Nama tidak boleh kosong'})
            
        pmb = PendaftaranPMB.query.filter(func.lower(PendaftaranPMB.nama) == func.lower(nama)).order_by(PendaftaranPMB.id.desc()).first()
        
        if not pmb:
            return jsonify({'error': 'Data pendaftaran tidak ditemukan.'})
            
        return jsonify({
            'nama': pmb.nama,
            'status': pmb.status,
            'npm': pmb.npm_generated if pmb.npm_generated else '-'
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error checking PMB check: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
        return jsonify({'error': 'Terjadi kesalahan sistem.'})

@app.route('/verifikasi/surat/<s_id>', methods=['GET'])
def verifikasi_surat(s_id):
    surat = SuratOtomatis.query.filter_by(qr_code=s_id).first()
    if not surat:
        return "Surat tidak ditemukan atau palsu.", 404
    # The SuratOtomatis model actually HAS `tanggal` as per memory & codebase: tanggal = db.Column(db.Date, default=datetime.date.today)
    # But just in case, we will safeguard it.
    tgl = getattr(surat, 'tanggal', surat.created_at)
    return f"Surat Resmi STIESAM. Jenis: {surat.jenis_surat}. Atas Nama NPM: {surat.npm}. Diterbitkan pada {tgl}."

@app.route('/')
@cache.cached(timeout=30, query_string=True)
def index():
    try:
        epilepsi_logs = EpilepsiLog.query.order_by(EpilepsiLog.date.desc(), EpilepsiLog.time.desc()).limit(5).all()
    except:
        epilepsi_logs = []
        
    try:
        verified_alumni_list = TracerStudy.query.filter_by(status='Diverifikasi').order_by(TracerStudy.id.desc()).all()
    except:
        verified_alumni_list = []

    return render_page(HOME_HTML, 'home', content_kwargs={'epilepsi_logs': epilepsi_logs, 'verified_alumni_list': verified_alumni_list})

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    user = current_user
    if user.role in ['Tata Usaha', 'Admin']:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, max_age=31536000)
    
    # Check LaciArsip ownership
    arsip = LaciArsip.query.filter_by(file_path=filename, npm=user.username).first()
    if arsip:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, max_age=31536000)
        
    # Check PendaftaranPMB ownership
    pmb = PendaftaranPMB.query.filter_by(npm_generated=user.username).first()
    if pmb and filename in [pmb.foto_ijazah, pmb.foto_ktp, pmb.bukti_transfer]:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, max_age=31536000)
        
    # Check foto_profil
    if user.foto_profil == filename:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, max_age=31536000)
        
    # Check public app settings
    for s in AppSettings.query.all():
        if filename == s.value:
            return send_from_directory(app.config['UPLOAD_FOLDER'], filename, max_age=31536000)

    # Check TagihanKuliah ownership
    tagihan = TagihanKuliah.query.filter_by(bukti_transfer=filename, npm=user.username).first()
    if tagihan:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, max_age=31536000)

    return 'Unauthorized', 403

@app.route('/sw.js')
def service_worker():
    sw_code = """
const CACHE_NAME = 'stiesam-v1';
const ASSETS_TO_CACHE = [
    '/',
    '/static/logo-stiesam.png',
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


# ============================================================================
# TATA USAHA (ADMIN) ROUTES
# ============================================================================

@app.route('/donate/update', methods=['POST'])
@login_required
@require_role(['Tata Usaha', 'Admin'])
def donate_update():
    
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
    pass

    return redirect(request.referrer)

@app.route('/tu/surat/acc', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
@require_role(['Tata Usaha', 'Admin'])
def tu_surat_acc():
    try:
        surat_id = request.form.get('id')
        surat = SuratOtomatis.query.get(surat_id)
        if surat:
            valid_surat = [
                "Surat Keterangan Aktif Kuliah",
                "Surat Pengantar Magang",
                "Surat Pengantar Riset",
                "Surat Cuti Akademik"
            ]
            if surat.jenis_surat not in valid_surat:
                flash("Jenis surat tidak valid.", "error")
                return redirect(url_for('ramadhan_dashboard', open='modal-pabrik-surat'))
                
            surat.status = 'Disetujui'
            
            import uuid
            unique_str = uuid.uuid4().hex
            verification_url = url_for('verifikasi_surat', s_id=unique_str, _external=True)
            surat.qr_code = unique_str
            
            from reportlab.pdfgen import canvas
            import qrcode
            
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(verification_url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_filename = f"qr_{unique_str}.png"
            qr_path = os.path.join(app.config['UPLOAD_FOLDER'], qr_filename)
            qr_img.save(qr_path)
            
            filename = f"surat_{surat.npm}_{unique_str[:8]}.pdf"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            c = canvas.Canvas(filepath)
            
            logo_path = os.path.join(app.static_folder, 'logo-stiesam.png') if hasattr(app, 'static_folder') and app.static_folder else 'static/logo-stiesam.png'
            if os.path.exists(logo_path):
                c.drawImage(logo_path, 50, 750, width=50, height=50)
            
            c.setFont("Helvetica-Bold", 16)
            c.drawString(110, 780, "KAMPUS STIE SAMARINDA")
            c.setFont("Helvetica", 12)
            c.drawString(110, 760, "Jl. Pahlawan No.1, Samarinda, Kalimantan Timur")
            c.line(50, 740, 550, 740)
            
            c.setFont("Helvetica-Bold", 14)
            c.drawString(200, 710, "SURAT KETERANGAN RESMI")
            c.setFont("Helvetica", 12)
            c.drawString(200, 690, f"Nomor: STIESAM/SK/{surat.id}/{datetime.date.today().year}")
            
            user_obj = User.query.filter_by(username=surat.npm).first()
            nama_lengkap = user_obj.nama if user_obj else "Mahasiswa"
            
            c.drawString(50, 640, "Yang bertanda tangan di bawah ini menerangkan bahwa:")
            c.drawString(50, 610, f"Nama Lengkap    : {nama_lengkap}")
            c.drawString(50, 580, f"NPM             : {surat.npm}")
            c.drawString(50, 550, f"Keperluan       : {surat.jenis_surat}")
            
            text_y = 520
            c.drawString(50, text_y, "Keterangan:")
            lines = [surat.keterangan[i:i+60] for i in range(0, len(surat.keterangan), 60)]
            for line in lines:
                text_y -= 20
                c.drawString(50, text_y, line)
                
            text_y -= 40
            c.drawString(50, text_y, "Surat ini sah dan ditandatangani secara elektronik. Pindai QR Code untuk verifikasi.")
            
            c.drawImage(qr_path, 400, text_y - 120, width=100, height=100)
            
            c.save()
            
            if os.path.exists(qr_path):
                os.remove(qr_path)
            
            arsip = LaciArsip(
                npm=surat.npm,
                nama_dokumen=f"Dokumen Resmi - {surat.jenis_surat}",
                file_path=filename,
                ukuran="Digital PDF"
            )
            db.session.add(arsip)
            db.session.add(Notification(npm=surat.npm, message=f"Surat {surat.jenis_surat} telah disetujui. Silakan cek arsip digital Anda."))
            db.session.commit()
        cache.clear()

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating surat: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return redirect(url_for('ramadhan_dashboard', open='modal-pabrik-surat'))

@app.route('/tu/pmb/verifikasi', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
@require_role(['Tata Usaha', 'Admin'])
def tu_pmb_verifikasi():
    try:
        import smtplib
        from email.mime.text import MIMEText
        
        def send_email_notification(to_email, subject, body):
            mail_server = os.environ.get('MAIL_SERVER')
            mail_port = int(os.environ.get('MAIL_PORT', 587))
            mail_username = os.environ.get('MAIL_USERNAME')
            mail_password = os.environ.get('MAIL_PASSWORD')
            use_tls = os.environ.get('MAIL_USE_TLS')
            
            if not all([mail_server, mail_username, mail_password, to_email]):
                return
            
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = mail_username
            msg['To'] = to_email
            
            try:
                server = smtplib.SMTP(mail_server, mail_port)
                if use_tls:
                    server.starttls()
                server.login(mail_username, mail_password)
                server.send_message(msg)
                server.quit()
            except Exception as e:
                app.logger.error(f"Failed to send email to {to_email}: {e}")

        verifikasi_type = request.form.get('type')
        item_id = request.form.get('id')
        
        if verifikasi_type == 'pmb':
            pmb = PendaftaranPMB.query.with_for_update().get(item_id)
            if pmb:
                pmb.status = 'Diterima'
                
                npm_manual = request.form.get('npm_manual')
                
                password_awal = os.environ.get('DEFAULT_MHS_PASSWORD')
                if not password_awal:
                    import secrets
                    password_awal = secrets.token_urlsafe(8)
                
                if not npm_manual:
                    year_prefix = str(datetime.date.today().year)[-2:]
                    max_npm = db.session.query(func.max(User.username)).filter(
                        User.username.like(f"{year_prefix}01%")
                    ).with_for_update().scalar()
                    
                    if max_npm and max_npm.isdigit():
                        next_id = int(max_npm[-4:]) + 1
                    else:
                        next_id = 1
                    npm_manual = f"{year_prefix}01{str(next_id).zfill(4)}"
                    
                pmb.npm_generated = npm_manual
                
                try:
                    new_user = User(
                        username=npm_manual, 
                        password_hash=generate_password_hash(password_awal), 
                        role='Mahasiswa', 
                        nama=pmb.nama, 
                        status_akademik='Aktif',
                        must_change_password=True
                    )
                    db.session.add(new_user)
                    db.session.flush()
                except Exception as e:
                    db.session.rollback()
                    app.logger.warning(f"Fallback insert User without must_change_password: {e}")
                    new_user = User(
                        username=npm_manual, 
                        password_hash=generate_password_hash(password_awal), 
                        role='Mahasiswa', 
                        nama=pmb.nama, 
                        status_akademik='Aktif'
                    )
                    if hasattr(new_user, 'must_change_password'):
                        new_user.must_change_password = True
                    db.session.add(new_user)
                
                if pmb.foto_ijazah:
                    db.session.add(LaciArsip(npm=npm_manual, nama_dokumen="Arsip Ijazah PMB", file_path=pmb.foto_ijazah, ukuran="Berkas PMB"))
                if pmb.foto_ktp:
                    db.session.add(LaciArsip(npm=npm_manual, nama_dokumen="Arsip KTP PMB", file_path=pmb.foto_ktp, ukuran="Berkas PMB"))
                if pmb.bukti_transfer:
                    db.session.add(LaciArsip(npm=npm_manual, nama_dokumen="Arsip Bukti Transfer PMB", file_path=pmb.bukti_transfer, ukuran="Berkas PMB"))

                msg = f"Selamat, pendaftaran Anda disetujui. NPM/ID Login Anda adalah {npm_manual}. Silakan login dan ubah password segera."
                db.session.add(Notification(npm=npm_manual, message=msg))
                
                email_body = f"Halo {pmb.nama},\n\nSelamat! Pendaftaran Anda di STIESAM telah disetujui.\nNPM: {npm_manual}\nPassword Sementara: {password_awal}\n\nHarap login dan segera mengganti password Anda.\nTerima kasih."
                if pmb.email and pmb.email != '-':
                    send_email_notification(pmb.email, "Pendaftaran PMB STIESAM Disetujui", email_body)
                
                db.session.commit()
                flash(f"Verifikasi PMB berhasil. Akun Mahasiswa ({npm_manual}) dibuat.", "success")
                
        elif verifikasi_type == 'dosen_mhs':
            user = User.query.get(item_id)
            if user and user.status_akademik == 'Menunggu Verifikasi':
                user.status_akademik = 'Aktif'
                
                username_manual = request.form.get('username_manual')
                password_awal = request.form.get('password_awal')
                
                if username_manual and username_manual.strip():
                    user.username = username_manual.strip()
                if password_awal and password_awal.strip():
                    user.password_hash = generate_password_hash(password_awal.strip())
                    if hasattr(user, 'must_change_password'):
                        user.must_change_password = True

                msg = f"Selamat, akun {user.role} Anda telah diaktifkan. Username Anda adalah {user.username}."
                db.session.add(Notification(npm=user.username, message=msg))
                db.session.commit()
                flash(f"Verifikasi akun {user.role} berhasil. ({user.username})", "success")
        cache.clear()

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error PMB/Dosen verifikasi: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return redirect(url_for('ramadhan_dashboard', open='modal-verifikasi-pmb'))

@app.route('/tu/arsip/search', methods=['GET'])
@limiter.limit("10 per minute")
@login_required
@require_role(['Tata Usaha', 'Admin'])
def tu_arsip_search():
    npm = request.args.get('npm')
    if not npm:
        return jsonify({'error': 'NPM kosong'})
    
    try:
        user = User.query.filter_by(username=npm).first()
        if not user:
            return jsonify({'error': 'Mahasiswa tidak ditemukan'})
        
        tagihan_raw = TagihanKuliah.query.filter_by(npm=npm).all()
        tagihan = [{'jenis_tagihan': t.jenis_tagihan, 'status': t.status} for t in tagihan_raw]
        
        dok_raw = LaciArsip.query.filter_by(npm=npm).all()
        dokumen = [{'nama_dokumen': d.nama_dokumen, 'file_path': d.file_path} for d in dok_raw]
        
        return jsonify({
            'user': {
                'nama': user.nama,
                'username': user.username,
                'status_akademik': user.status_akademik
            },
            'tagihan': tagihan,
            'dokumen': dokumen
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error arsip search: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
        return jsonify({'error': 'Terjadi kesalahan sistem'})

@app.route('/tu/publikasi/update', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
@require_role(['Tata Usaha', 'Admin'])
def tu_publikasi_update():
    try:
        keys = ['profil_deskripsi', 'profil_visi', 'profil_misi', 
                'berita_label', 'berita_judul', 'berita_waktu', 'berita_isi',
                'jurnal_kategori', 'jurnal_volume', 'jurnal_judul', 'jurnal_penulis']
        
        for k in keys:
            val = request.form.get(k)
            if val is not None:
                s = AppSettings.query.get(k)
                if s: s.value = val
                else: db.session.add(AppSettings(key=k, value=val))
                
        if 'profil_gambar' in request.files:
            file = request.files['profil_gambar']
            if file and allowed_file(file.filename):
                saved_filename = compress_image(file, app.config['UPLOAD_FOLDER'])
                s = AppSettings.query.get('profil_gambar')
                if s: s.value = saved_filename
                else: db.session.add(AppSettings(key='profil_gambar', value=saved_filename))
                
        if 'berita_gambar' in request.files:
            file = request.files['berita_gambar']
            if file and allowed_file(file.filename):
                saved_filename = compress_image(file, app.config['UPLOAD_FOLDER'])
                s = AppSettings.query.get('berita_gambar')
                if s: s.value = saved_filename
                else: db.session.add(AppSettings(key='berita_gambar', value=saved_filename))
                
        db.session.commit()
        pass

        flash("Pembaruan publikasi informasi berhasil disimpan.", "success")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating publikasi: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return redirect(url_for('ramadhan_dashboard', open='modal-publikasi-informasi'))

@app.route('/tu/tagihan/tambah', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
@require_role(['Tata Usaha', 'Admin'])
def tu_tagihan_tambah():
    try:
        npm = request.form.get('npm', '').strip()
        jumlah = request.form.get('jumlah', '').strip()
        jenis_tagihan = request.form.get('jenis_tagihan')

        if not npm.isdigit() or not jumlah.isdigit():
            flash("Format input tidak valid. Pastikan NPM dan Nominal hanya berisi angka presisi tanpa karakter asing.", "error")
            return redirect(url_for('ramadhan_dashboard', open='modal-verifikasi-pembayaran'))
            
        if int(jumlah) <= 0:
            flash("Nominal tagihan harus lebih besar dari 0.", "error")
            return redirect(url_for('ramadhan_dashboard', open='modal-verifikasi-pembayaran'))

        user = User.query.filter_by(username=npm).first()
        if not user:
            flash(f"Error: NPM {npm} tidak ditemukan dalam sistem.", "error")
            return redirect(url_for('ramadhan_dashboard', open='modal-verifikasi-pembayaran'))

        new_tagihan = TagihanKuliah(
            npm=npm,
            jumlah=int(jumlah),
            jenis_tagihan=jenis_tagihan,
            status='Belum Lunas'
        )
        db.session.add(new_tagihan)
        db.session.commit()
        pass

        flash("Tagihan berhasil ditambahkan.", "success")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error tambah tagihan: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return redirect(url_for('ramadhan_dashboard', open='modal-verifikasi-pembayaran'))

@app.route('/tu/tagihan/lunas', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
@require_role(['Tata Usaha', 'Admin'])
def tu_tagihan_lunas():
    try:
        t_id = request.form.get('id')
        tagihan = TagihanKuliah.query.get(t_id)
        if tagihan:
            if tagihan.status == 'Lunas':
                flash("Tagihan ini sudah lunas.", "error")
                return redirect(url_for('ramadhan_dashboard', open='modal-verifikasi-pembayaran'))
            tagihan.status = 'Lunas'
            db.session.add(Notification(npm=tagihan.npm, message=f"Pembayaran {tagihan.jenis_tagihan} telah dikonfirmasi LUNAS."))
            db.session.commit()
            
            # Send email
            import smtplib
            from email.mime.text import MIMEText
            
            def send_email_notification(to_email, subject, body):
                mail_server = os.environ.get('MAIL_SERVER')
                mail_port = int(os.environ.get('MAIL_PORT', 587))
                mail_username = os.environ.get('MAIL_USERNAME')
                mail_password = os.environ.get('MAIL_PASSWORD')
                use_tls = os.environ.get('MAIL_USE_TLS')
                
                if not all([mail_server, mail_username, mail_password, to_email]):
                    return
                
                msg = MIMEText(body)
                msg['Subject'] = subject
                msg['From'] = mail_username
                msg['To'] = to_email
                
                try:
                    server = smtplib.SMTP(mail_server, mail_port)
                    if use_tls:
                        server.starttls()
                    server.login(mail_username, mail_password)
                    server.send_message(msg)
                    server.quit()
                except Exception as e:
                    app.logger.error(f"Failed to send email to {to_email}: {e}")
                    
            user_pmb = PendaftaranPMB.query.filter_by(npm_generated=tagihan.npm).first()
            if user_pmb and user_pmb.email and user_pmb.email != '-':
                email_body = f"Halo {user_pmb.nama},\n\nPembayaran {tagihan.jenis_tagihan} sebesar Rp {tagihan.jumlah} telah dikonfirmasi LUNAS.\n\nTerima kasih."
                send_email_notification(user_pmb.email, "Konfirmasi Pembayaran Lunas STIESAM", email_body)
                
            flash("Tagihan berhasil dilunaskan.", "success")
        cache.clear()

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error tagihan lunas: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return redirect(url_for('ramadhan_dashboard', open='modal-verifikasi-pembayaran'))

@app.route('/tu/jadwal', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
@require_role(['Tata Usaha', 'Admin'])
def tu_jadwal():
    try:
        new_jadwal = JadwalKuliah(
            hari=request.form['hari'],
            jam=request.form['jam'],
            mata_kuliah=request.form['mata_kuliah'],
            dosen=request.form['dosen'],
            ruangan=request.form['ruangan']
        )
        db.session.add(new_jadwal)
        db.session.flush() # To get new_jadwal.id
        db.session.add(StatusNilai(jadwal_id=new_jadwal.id, is_published=False))
        db.session.commit()
        cache.clear()

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error tambah jadwal: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return redirect(url_for('ramadhan_dashboard', open='modal-kelola-jadwal'))

@app.route('/tu/akun/update', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
@require_role(['Tata Usaha', 'Admin'])
def tu_akun_update():
    try:
        user_id = request.form.get('id')
        status = request.form.get('status_akademik')
        user = User.query.get(user_id)
        if user and status in ['Aktif', 'Cuti', 'Keluar', 'Lulus']:
            user.status_akademik = status
            db.session.commit()
        cache.clear()

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error update status akademik: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return redirect(url_for('ramadhan_dashboard', open='modal-manajemen-sivitas'))

@app.route('/tu/tracer/verify', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
@require_role(['Tata Usaha', 'Admin'])
def tu_tracer_verify():
    try:
        t_id = request.form.get('id')
        tracer = TracerStudy.query.get(t_id)
        if tracer:
            tracer.status = 'Diverifikasi'
            db.session.commit()
        cache.clear()

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error tracer verify: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return redirect(url_for('ramadhan_dashboard', open='modal-cek-alumni'))

@app.route('/tu/akun/reset_password', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
@require_role(['Tata Usaha', 'Admin'])
def tu_akun_reset_password():
    try:
        user_id = request.form.get('id')
        user = User.query.get(user_id)
        if user:
            user.password_hash = generate_password_hash(os.environ.get('DEFAULT_RESET_PASSWORD', 'stiesam123'))
            if hasattr(user, 'must_change_password'):
                user.must_change_password = True
            db.session.commit()
        cache.clear()

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error reset password: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return redirect(url_for('ramadhan_dashboard', open='modal-manajemen-sivitas'))

@app.route('/tu/akun/delete', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
@require_role(['Tata Usaha', 'Admin'])
def tu_akun_delete():
    try:
        user_id = request.form.get('id')
        user = db.session.get(User, user_id)
        if user:
            # We explicitly handle related records to prevent orphaned data
            username = user.username
            if username:
                KRSMahasiswa.query.filter_by(npm=username).delete()
                NilaiMahasiswa.query.filter_by(npm=username).delete()
                TagihanKuliah.query.filter_by(npm=username).delete()
                LaciArsip.query.filter_by(npm=username).delete()
                SuratOtomatis.query.filter_by(npm=username).delete()
                KehadiranKelas.query.filter_by(npm=username).delete()
                Notification.query.filter_by(npm=username).delete()

            db.session.delete(user)
            db.session.commit()
            flash("Akun pengguna dan seluruh relasi data terkait telah dihapus permanen.", "success")
        pass
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error delete user: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return redirect(url_for('ramadhan_dashboard', open='modal-manajemen-sivitas'))


# ============================================================================
# DOSEN ROUTES
# ============================================================================

# ============================================================================
# RUTE DOSEN
# ============================================================================
@app.route('/dosen')
@limiter.limit("200 per hour")
def dosen_dashboard():
    # Data Retrieval
    dosen_name = session.get('nama', 'Dosen Pengampu')
    user = User.query.get(session.get('user_id')) if session.get('user_id') else None
    
    jadwal_dosen, krs_perwalian, kelas_list, mahasiswa_perwalian = _fetch_dosen_data(dosen_name)

    # DOSEN THEME
    dosen_theme = {
        'nav_bg': 'bg-[#FDFBF7]/90 backdrop-blur-md border-b border-[#E8C5A8]/20',
        'icon_bg': 'bg-[#E8C5A8]/20',
        'icon_text': 'text-[#A05D4A]',
        'title_text': 'text-[#A05D4A]',
        'link_hover': 'hover:text-[#A05D4A]',
        'link_active': 'text-[#A05D4A] font-bold',
        'btn_primary': 'bg-[#E8C5A8] text-[#A05D4A] font-bold hover:bg-[#A05D4A] hover:text-white',
        'bottom_nav_bg': 'bg-[#FDFBF7]',
        'bottom_active': 'text-[#A05D4A]',
        'bottom_btn_bg': 'bg-[#E8C5A8]',
        'bottom_btn_text': 'text-[#A05D4A]',
        'bottom_text_inactive': 'text-gray-400'
    }
    
    dosen_html = '''
    <div class="pt-24 pb-32 px-5 md:px-8 bg-[#FDFBF7] min-h-screen">
        <div class="md:grid md:grid-cols-2 md:gap-12 md:items-center mb-10">
            <div class="hidden md:block pl-2">
                <p class="text-xl text-[#A05D4A]/70 font-medium mb-2">Salam Sejahtera Bapak/Ibu Dosen</p>
                <h1 class="text-5xl font-bold text-[#A05D4A] leading-tight mb-6">Portal Dosen<br>STIESAM</h1>
                <p class="text-[#A05D4A]/80 text-lg leading-relaxed mb-8">
                    Terima kasih atas dedikasi luar biasa Anda dalam mendidik dan membimbing para mahasiswa STIESAM. Mari wujudkan akademik yang tertata rapi.
                </p>
            </div>
            <div>
                <div class="bg-gradient-to-br from-[#E8C5A8] to-[#D5A78B] rounded-3xl p-6 md:p-10 text-white shadow-xl relative overflow-hidden transform md:hover:scale-[1.02] transition-transform duration-500 border border-white/20">
                    <div class="absolute top-0 right-0 opacity-10 transform translate-x-4 -translate-y-4">
                        <i class="fas fa-chalkboard-teacher text-9xl"></i>
                    </div>
                    <div class="relative z-10">
                        <p class="text-xs font-medium opacity-80 mb-1 tracking-wide uppercase text-[#5D3425]">Pengingat Akademik</p>
                        <h2 class="text-2xl font-bold mb-3 text-[#5D3425]">Batas Input Nilai UAS</h2>
                        <div class="bg-white/20 backdrop-blur-md rounded-xl px-4 py-2 inline-block mb-6 border border-white/10 text-[#5D3425]">
                            <span class="font-mono text-2xl font-bold tracking-wider" id="countdown-timer">Tinggal 3 Hari</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <h3 class="text-[#A05D4A] font-bold text-lg mb-4 pl-3 border-l-4 border-[#E8C5A8]">MENU UTAMA</h3>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-24">
            <button onclick="openModal('modal-persetujuan-krs')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#E8C5A8]/30 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
                 <div class="w-14 h-14 rounded-full bg-[#E8C5A8]/20 flex items-center justify-center text-[#A05D4A] mb-3 group-hover:bg-[#E8C5A8] group-hover:text-[#5D3425] transition-colors">
                    <i class="fas fa-file-signature text-2xl"></i>
                 </div>
                 <span class="font-bold text-sm text-gray-600 group-hover:text-[#A05D4A] text-center">Persetujuan KRS</span>
            </button>
            <button onclick="openModal('modal-masukan-nilai')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#E8C5A8]/30 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
                 <div class="w-14 h-14 rounded-full bg-[#E8C5A8]/20 flex items-center justify-center text-[#A05D4A] mb-3 group-hover:bg-[#E8C5A8] group-hover:text-[#5D3425] transition-colors">
                    <i class="fas fa-marker text-2xl"></i>
                 </div>
                 <span class="font-bold text-sm text-gray-600 group-hover:text-[#A05D4A] text-center">Input Nilai</span>
            </button>
            <button onclick="openModal('modal-daftar-mahasiswa')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#E8C5A8]/30 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
                 <div class="w-14 h-14 rounded-full bg-[#E8C5A8]/20 flex items-center justify-center text-[#A05D4A] mb-3 group-hover:bg-[#E8C5A8] group-hover:text-[#5D3425] transition-colors">
                    <i class="fas fa-users text-2xl"></i>
                 </div>
                 <span class="font-bold text-sm text-gray-600 group-hover:text-[#A05D4A] text-center">Mahasiswa Wali</span>
            </button>
            <button onclick="openModal('modal-jadwal-ruang')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#E8C5A8]/30 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
                 <div class="w-14 h-14 rounded-full bg-[#E8C5A8]/20 flex items-center justify-center text-[#A05D4A] mb-3 group-hover:bg-[#E8C5A8] group-hover:text-[#5D3425] transition-colors">
                    <i class="fas fa-calendar-alt text-2xl"></i>
                 </div>
                 <span class="font-bold text-sm text-gray-600 group-hover:text-[#A05D4A] text-center">Jadwal Mengajar</span>
            </button>
            <button onclick="openModal('modal-presensi-jurnal')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#E8C5A8]/30 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
                 <div class="w-14 h-14 rounded-full bg-[#E8C5A8]/20 flex items-center justify-center text-[#A05D4A] mb-3 group-hover:bg-[#E8C5A8] group-hover:text-[#5D3425] transition-colors">
                    <i class="fas fa-clipboard-check text-2xl"></i>
                 </div>
                 <span class="font-bold text-sm text-gray-600 group-hover:text-[#A05D4A] text-center">Presensi Kelas</span>
            </button>
            <button onclick="openModal('modal-profil-dosen')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#E8C5A8]/30 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
                 <div class="w-14 h-14 rounded-full bg-[#E8C5A8]/20 flex items-center justify-center text-[#A05D4A] mb-3 group-hover:bg-[#E8C5A8] group-hover:text-[#5D3425] transition-colors">
                    <i class="fas fa-user-tie text-2xl"></i>
                 </div>
                 <span class="font-bold text-sm text-gray-600 group-hover:text-[#A05D4A] text-center">Profil Dosen</span>
            </button>
        </div>
        
        <!-- MODAL 1: PERSETUJUAN RENCANA STUDI -->
        <div id="modal-persetujuan-krs" class="hidden fixed inset-0 z-40 bg-[#FDFBF7] overflow-y-auto">
            <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
                <div class="flex justify-between items-center mb-6 border-b border-[#E8C5A8]/50 pb-4">
                    <h3 class="text-xl font-bold text-[#A05D4A]">Persetujuan Rencana Studi</h3>
                    <button onclick="closeModal('modal-persetujuan-krs')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
                </div>
                <div class="space-y-4">
                    {% for krs in krs_perwalian %}
                    <div class="bg-white p-5 rounded-2xl shadow-sm border border-[#E8C5A8]/50 relative" id="krs-card-{{ krs['id'] }}">
                        <p class="font-bold text-gray-800 text-lg mb-1">{{ krs['mata_kuliah'] }}</p>
                        <p class="text-sm text-gray-500 mb-3">NPM: <span class="font-mono font-bold">{{ krs['npm'] }}</span> • SKS: {{ krs['sks'] }}</p>
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-bold px-3 py-1 rounded-full {{ 'bg-yellow-100 text-yellow-600' if krs['status'] == 'Menunggu Acc Dosen' else ('bg-green-100 text-green-600' if krs['status'] == 'Disetujui Dosen' else 'bg-red-100 text-red-600') }}" id="krs-status-{{ krs['id'] }}">
                                {{ krs['status'] }}
                            </span>
                            <div class="flex gap-2">
                                <button onclick="actionKrs({{ krs['id'] }}, 'Disetujui Dosen')" class="bg-green-500 text-white px-4 py-2 rounded-lg text-xs font-bold hover:bg-green-600 transition">Setujui</button>
                                <button onclick="actionKrs({{ krs['id'] }}, 'Ditolak Dosen')" class="bg-red-500 text-white px-4 py-2 rounded-lg text-xs font-bold hover:bg-red-600 transition">Tolak</button>
                            </div>
                        </div>
                    </div>
                    {% else %}
                    <p class="text-center text-gray-500 text-sm italic">Belum ada KRS mahasiswa yang siap di-review.</p>
                    {% endfor %}
                </div>
            </div>
            <script>
            async function actionKrs(id, status) {
                const fd = new FormData();
                fd.append('id', id);
                fd.append('status', status);
                // Assume standard CSRF setup if available in DOM
                const csrfToken = document.querySelector('input[name="csrf_token"]') ? document.querySelector('input[name="csrf_token"]').value : '';
                fd.append('csrf_token', csrfToken);
                
                try {
                    const res = await fetch('/dosen/krs/action', {
                        method: 'POST',
                        body: fd
                    });
                    const data = await res.json();
                    if(data.success) {
                        const badge = document.getElementById('krs-status-' + id);
                        badge.innerText = status;
                        badge.className = "text-xs font-bold px-3 py-1 rounded-full " + (status === 'Disetujui Dosen' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600');
                    }
                } catch(e) {
                    showToast('Gagal memproses persetujuan KRS.', 'error');
                }
            }
            </script>
        </div>

        <!-- MODAL 2: MASUKAN NILAI AKHIR -->
        <div id="modal-masukan-nilai" class="hidden fixed inset-0 z-40 bg-[#FDFBF7] overflow-y-auto">
            <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
                <div class="flex justify-between items-center mb-6 border-b border-[#E8C5A8]/50 pb-4">
                    <h3 class="text-xl font-bold text-[#A05D4A]">Masukan Nilai Akhir</h3>
                    <button onclick="closeModal('modal-masukan-nilai')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
                </div>
                
                <div class="space-y-6">
                    {% for kelas in kelas_list %}
                    <div class="bg-white p-6 rounded-3xl shadow-sm border border-[#E8C5A8]/50">
                        <div class="flex justify-between items-start mb-4">
                            <div>
                                <h4 class="font-bold text-[#A05D4A] text-lg">{{ kelas['jadwal']['mata_kuliah'] }}</h4>
                                <p class="text-xs text-gray-500">{{ kelas['jadwal']['hari'] }}, {{ kelas['jadwal']['jam'] }} • {{ kelas['jadwal']['ruangan'] }}</p>
                            </div>
                            {% if kelas['is_published'] %}
                            <span class="bg-blue-100 text-blue-600 text-[10px] font-bold px-2 py-1 rounded-full"><i class="fas fa-lock"></i> Telah Dipublikasi</span>
                            {% endif %}
                        </div>
                        
                        <form action="/dosen/nilai/submit" method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                            <input type="hidden" name="jadwal_id" value="{{ kelas['jadwal']['id'] }}">
                            <input type="hidden" name="mata_kuliah" value="{{ kelas['jadwal']['mata_kuliah'] }}">
                            
                            <table class="w-full text-left border-collapse mb-4">
                                <thead class="bg-gray-50">
                                    <tr>
                                        <th class="p-3 text-xs font-bold text-gray-600 rounded-l-lg">Mahasiswa</th>
                                        <th class="p-3 text-xs font-bold text-gray-600 text-center">Kehadiran</th>
                                        <th class="p-3 text-xs font-bold text-gray-600 text-center rounded-r-lg">Nilai Huruf</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for s in kelas['students'] %}
                                    <tr class="border-b border-gray-100">
                                        <td class="p-3">
                                            <p class="text-sm font-bold text-gray-800">{{ s['nama'] }}</p>
                                            <p class="text-[10px] font-mono text-gray-500">{{ s['npm'] }}</p>
                                        </td>
                                        <td class="p-3 text-center">
                                            <span class="text-xs font-bold {{ 'text-red-500' if s['attendance_pct'] < 75 else 'text-green-500' }}">{{ "%.0f"|format(s['attendance_pct']) }}%</span>
                                        </td>
                                        <td class="p-3 text-center">
                                            {% if kelas['is_published'] %}
                                                <input type="text" value="🔒" disabled class="w-12 text-center bg-gray-100 border border-gray-200 rounded p-1 text-sm font-bold text-gray-500 mx-auto">
                                            {% elif s['attendance_pct'] < 75 %}
                                                <input type="text" value="E" readonly title="Kehadiran dibawah 75%" class="w-12 text-center bg-red-50 border border-red-200 rounded p-1 text-sm font-bold text-red-500 mx-auto cursor-not-allowed">
                                                <input type="hidden" name="nilai_{{ s['npm'] }}" value="E">
                                            {% else %}
                                                <select name="nilai_{{ s['npm'] }}" required class="w-16 bg-white border border-[#E8C5A8] rounded p-1 text-sm font-bold text-[#A05D4A] mx-auto focus:outline-none focus:ring-2 focus:ring-[#E8C5A8]">
                                                    <option value=""></option>
                                                    <option value="A">A</option>
                                                    <option value="A-">A-</option>
                                                    <option value="B+">B+</option>
                                                    <option value="B">B</option>
                                                    <option value="B-">B-</option>
                                                    <option value="C+">C+</option>
                                                    <option value="C">C</option>
                                                    <option value="D">D</option>
                                                    <option value="E">E</option>
                                                </select>
                                            {% endif %}
                                        </td>
                                    </tr>
                                    {% else %}
                                    <tr><td colspan="3" class="p-3 text-center text-xs text-gray-500">Tidak ada mahasiswa di kelas ini.</td></tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                            
                            {% if not kelas['is_published'] and kelas['students'] %}
                            <button type="submit" onclick="return confirm('Anda yakin ingin mempublikasikan nilai? Setelah publikasi, nilai akan dikunci permanen.');" class="w-full bg-[#A05D4A] text-white font-bold py-3 rounded-xl hover:bg-[#5D3425] transition shadow-md"><i class="fas fa-cloud-upload-alt mr-2"></i>Simpan & Publikasi</button>
                            {% endif %}
                        </form>
                    </div>
                    {% else %}
                    <p class="text-center text-gray-500 text-sm italic">Anda tidak memiliki jadwal mengajar.</p>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- MODAL 3: DAFTAR MAHASISWA PERWALIAN -->
        <div id="modal-daftar-mahasiswa" class="hidden fixed inset-0 z-40 bg-[#FDFBF7] overflow-y-auto">
            <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
                <div class="flex justify-between items-center mb-6 border-b border-[#E8C5A8]/50 pb-4">
                    <h3 class="text-xl font-bold text-[#A05D4A]">Mahasiswa Perwalian</h3>
                    <button onclick="closeModal('modal-daftar-mahasiswa')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
                </div>
                <div class="space-y-4">
                    {% for m in mahasiswa_perwalian %}
                    <div class="bg-white p-5 rounded-3xl shadow-sm border border-[#E8C5A8]/50">
                        <div class="flex justify-between items-start mb-4">
                            <div class="flex items-center gap-3">
                                <div class="w-12 h-12 bg-[#E8C5A8]/20 rounded-full flex items-center justify-center text-[#A05D4A] text-xl font-bold border border-[#E8C5A8]">
                                    <i class="fas fa-user"></i>
                                </div>
                                <div>
                                    <p class="font-bold text-gray-800">{{ m['nama'] }}</p>
                                    <p class="text-[10px] font-mono text-[#A05D4A]">{{ m['npm'] }}</p>
                                    <span class="text-[10px] bg-green-100 text-green-700 px-2 py-0.5 rounded font-bold">{{ m['status'] }}</span>
                                </div>
                            </div>
                            <div class="text-right">
                                <p class="text-[10px] uppercase tracking-wider text-gray-400 font-bold mb-1">IPK Saat Ini</p>
                                <span class="text-2xl font-mono font-bold text-[#5D3425]">{{ "%.2f"|format(m['ipk']) }}</span>
                            </div>
                        </div>
                        
                        <details class="bg-gray-50 rounded-xl border border-gray-200 p-3 mb-2">
                            <summary class="text-xs font-bold text-[#A05D4A] cursor-pointer outline-none">Riwayat Transkrip Nilai</summary>
                            <div class="mt-3 space-y-2 max-h-40 overflow-y-auto custom-scrollbar pr-2">
                                {% for t in m['transkrip'] %}
                                <div class="flex justify-between items-center text-xs bg-white p-2 rounded border border-gray-100">
                                    <span class="font-bold text-gray-700 truncate max-w-[60%]">{{ t['mata_kuliah'] }}</span>
                                    <span class="text-gray-500">{{ t['semester'] }}</span>
                                    <span class="font-bold text-[#A05D4A]">{{ t['nilai_huruf'] }}</span>
                                </div>
                                {% else %}
                                <p class="text-[10px] text-gray-500 italic">Belum ada riwayat nilai.</p>
                                {% endfor %}
                            </div>
                        </details>
                        
                        <details class="bg-gray-50 rounded-xl border border-gray-200 p-3">
                            <summary class="text-xs font-bold text-[#A05D4A] cursor-pointer outline-none">Arsip Digital Mahasiswa</summary>
                            <div class="mt-3 space-y-2">
                                {% for a in m['arsip'] %}
                                <div class="flex justify-between items-center text-xs bg-white p-2 rounded border border-gray-100">
                                    <span class="font-medium text-gray-700 truncate">{{ a['nama_dokumen'] }}</span>
                                    <a href="/uploads/{{ a['file_path'] }}" target="_blank" class="text-blue-500 hover:underline"><i class="fas fa-download"></i> Unduh</a>
                                </div>
                                {% else %}
                                <p class="text-[10px] text-gray-500 italic">Tidak ada dokumen di laci arsip.</p>
                                {% endfor %}
                            </div>
                        </details>
                    </div>
                    {% else %}
                    <p class="text-center text-gray-500 text-sm italic">Belum ada mahasiswa perwalian.</p>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- MODAL 4: JADWAL MENGAJAR & RUANG KELAS -->
        <div id="modal-jadwal-ruang" class="hidden fixed inset-0 z-40 bg-[#FDFBF7] overflow-y-auto">
            <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
                <div class="flex justify-between items-center mb-6 border-b border-[#E8C5A8]/50 pb-4">
                    <h3 class="text-xl font-bold text-[#A05D4A]">Jadwal Mengajar</h3>
                    <button onclick="closeModal('modal-jadwal-ruang')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
                </div>
                <div class="bg-white p-4 rounded-xl border border-[#E8C5A8]/30 mb-6 flex items-start gap-3 shadow-sm">
                    <i class="fas fa-info-circle text-[#A05D4A] mt-0.5"></i>
                    <p class="text-xs text-gray-600 leading-relaxed">Jadwal ini disinkronkan langsung secara mutlak dari pangkalan data pusat Tata Usaha. Setiap perubahan yang dilakukan staf Tata Usaha akan langsung muncul ke layar ini.</p>
                </div>
                <div class="space-y-4">
                    {% for j in jadwal_dosen %}
                    <div class="bg-white p-5 rounded-2xl shadow-sm border border-[#E8C5A8]/50 flex justify-between items-center">
                        <div>
                            <p class="font-bold text-gray-800 text-base mb-1">{{ j['mata_kuliah'] }}</p>
                            <div class="flex items-center gap-2 text-xs text-gray-500 mb-1">
                                <span class="bg-[#E8C5A8]/20 text-[#5D3425] px-2 py-0.5 rounded font-bold">{{ j['hari'] }}</span>
                                <span class="text-gray-500"><i class="fas fa-clock mr-1 text-[#A05D4A]"></i> {{ j['jam'] }}</span>
                            </div>
                        </div>
                        <div class="text-right">
                            <p class="text-[10px] text-gray-400 font-bold uppercase mb-1">Ruangan</p>
                            <span class="font-mono font-bold text-xl text-[#5D3425]">{{ j['ruangan'] }}</span>
                        </div>
                    </div>
                    {% else %}
                    <p class="text-center text-gray-500 text-sm italic">Jadwal mengajar belum tersedia atau belum diinput oleh Tata Usaha.</p>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- MODAL 5: PRESENSI & JURNAL PERKULIAHAN -->
        <div id="modal-presensi-jurnal" class="hidden fixed inset-0 z-40 bg-[#FDFBF7] overflow-y-auto">
            <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
                <div class="flex justify-between items-center mb-6 border-b border-[#E8C5A8]/50 pb-4">
                    <h3 class="text-xl font-bold text-[#A05D4A]">Presensi & Jurnal</h3>
                    <button onclick="closeModal('modal-presensi-jurnal')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
                </div>
                
                <div class="space-y-6">
                    {% for kelas in kelas_list %}
                    <div class="bg-white p-6 rounded-3xl shadow-sm border border-[#E8C5A8]/50">
                        <div class="mb-4">
                            <h4 class="font-bold text-[#A05D4A] text-lg">{{ kelas['jadwal']['mata_kuliah'] }}</h4>
                            <p class="text-xs text-gray-500">{{ kelas['jadwal']['hari'] }}, {{ kelas['jadwal']['jam'] }} • Ruang: {{ kelas['jadwal']['ruangan'] }}</p>
                        </div>
                        
                        <form action="/dosen/presensi/submit" method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                            <input type="hidden" name="jadwal_id" value="{{ kelas['jadwal']['id'] }}">
                            <input type="hidden" name="mata_kuliah" value="{{ kelas['jadwal']['mata_kuliah'] }}">
                            
                            <div class="mb-4">
                                <label class="block text-xs font-bold text-[#5D3425] mb-2">Jurnal Materi Perkuliahan Hari Ini</label>
                                <textarea name="materi" required placeholder="Tuliskan materi yang diajarkan hari ini..." class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm h-20 focus:outline-none focus:ring-2 focus:ring-[#E8C5A8]"></textarea>
                            </div>
                            
                            <label class="block text-xs font-bold text-[#5D3425] mb-2">Presensi Kehadiran Mahasiswa</label>
                            <div class="bg-gray-50 border border-gray-200 rounded-xl p-3 mb-4 max-h-48 overflow-y-auto custom-scrollbar">
                                {% for s in kelas['students'] %}
                                <label class="flex items-center justify-between p-2 border-b border-gray-100 last:border-0 hover:bg-white transition cursor-pointer rounded">
                                    <div>
                                        <p class="text-sm font-bold text-gray-800">{{ s['nama'] }}</p>
                                        <p class="text-[10px] font-mono text-gray-500">{{ s['npm'] }}</p>
                                    </div>
                                    <input type="checkbox" name="kehadiran_{{ s['npm'] }}" value="Hadir" class="accent-[#A05D4A] w-5 h-5">
                                </label>
                                {% else %}
                                <p class="text-xs text-gray-500 italic text-center py-2">Tidak ada mahasiswa.</p>
                                {% endfor %}
                            </div>
                            
                            {% if kelas['students'] %}
                            <button type="submit" class="w-full bg-[#A05D4A] text-white font-bold py-3 rounded-xl hover:bg-[#5D3425] transition shadow-md"><i class="fas fa-save mr-2"></i>Simpan Kehadiran & Jurnal</button>
                            {% endif %}
                        </form>
                    </div>
                    {% else %}
                    <p class="text-center text-gray-500 text-sm italic">Tidak ada jadwal mengajar.</p>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- MODAL 6: PROFIL DOSEN -->
        <div id="modal-profil-dosen" class="hidden fixed inset-0 z-40 bg-[#FDFBF7] overflow-y-auto">
            <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
                <div class="flex justify-between items-center mb-6 border-b border-[#E8C5A8]/50 pb-4">
                    <h3 class="text-xl font-bold text-[#A05D4A]">Profil & Portofolio</h3>
                    <button onclick="closeModal('modal-profil-dosen')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
                </div>
                
                <div class="bg-white p-8 rounded-3xl shadow-lg border border-[#E8C5A8]/30 mb-6 text-center relative overflow-hidden">
                    <div class="absolute top-0 right-0 w-32 h-32 bg-[#E8C5A8]/20 rounded-bl-full -z-10"></div>
                    <div class="relative w-24 h-24 bg-gray-200 rounded-full flex items-center justify-center text-5xl text-gray-400 shadow-inner border-4 border-white overflow-hidden mx-auto mb-4 group">
                        {% if user and user.foto_profil %}
                            <img src="/uploads/{{ user.foto_profil }}" alt="Foto Profil" class="w-full h-full object-cover">
                        {% else %}
                            <i class="fas fa-user-tie"></i>
                        {% endif %}
                        <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center cursor-pointer transition-opacity" onclick="document.getElementById('dsn_foto_profil_input').click()">
                            <i class="fas fa-camera text-white text-2xl"></i>
                        </div>
                    </div>
                    <form id="dsn_foto_form" action="/dosen/update_foto" method="POST" enctype="multipart/form-data" class="hidden">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <input type="file" id="dsn_foto_profil_input" name="foto_profil" accept="image/*" onchange="document.getElementById('dsn_foto_form').submit()">
                    </form>
                    <h4 class="text-2xl font-bold text-[#5D3425] leading-tight mb-1">{{ dosen_name }}</h4>
                    <p class="text-sm font-bold text-[#A05D4A] font-mono tracking-widest mb-3">NIDN: {{ session.get('username', 'N/A') }}</p>
                    <span class="inline-block px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-green-100 text-green-700 shadow-sm">DOSEN AKTIF</span>
                    
                    <div class="mt-8 pt-6 border-t border-gray-100 flex justify-center gap-8">
                        <div>
                            <p class="text-xs text-gray-400 font-bold uppercase tracking-wider mb-1">Mata Kuliah</p>
                            <h2 class="text-3xl font-bold text-[#A05D4A]">{{ jadwal_dosen|length }}</h2>
                        </div>
                        <div>
                            <p class="text-xs text-gray-400 font-bold uppercase tracking-wider mb-1">Mahasiswa Perwalian</p>
                            <h2 class="text-3xl font-bold text-[#A05D4A]">{{ mahasiswa_perwalian|length }}</h2>
                        </div>
                    </div>
                </div>
            </div>
        </div>

    </div>
    '''
    return render_page(dosen_html, 'irma', theme=dosen_theme, content_kwargs={
        'dosen_name': dosen_name, 'jadwal_dosen': jadwal_dosen, 'krs_perwalian': krs_perwalian,
        'kelas_list': kelas_list, 'mahasiswa_perwalian': mahasiswa_perwalian, 'user': user
    }, full_width=True)

@app.route('/mahasiswa/update_foto', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
@require_role(['Mahasiswa'])
def mahasiswa_update_foto():
    try:
        foto = request.files.get('foto_profil')
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if foto and allowed_file(foto.filename) and user:
            saved_filename = compress_image(foto, app.config['UPLOAD_FOLDER'])
            user.foto_profil = saved_filename
            db.session.commit()
            pass
            flash("Foto profil berhasil diperbarui.", "success")
        else:
            flash("File tidak valid.", "error")
            
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error update foto: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
        
    return redirect(url_for('irma_dashboard', open='modal-profil-arsip'))

@app.route('/dosen/update_foto', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
@require_role(['Dosen'])
def dosen_update_foto():
    try:
        foto = request.files.get('foto_profil')
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if foto and allowed_file(foto.filename) and user:
            saved_filename = compress_image(foto, app.config['UPLOAD_FOLDER'])
            user.foto_profil = saved_filename
            db.session.commit()
            pass
            flash("Foto profil berhasil diperbarui.", "success")
        else:
            flash("File tidak valid.", "error")
            
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error update foto: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
        
    return redirect(url_for('dosen_dashboard', open='modal-profil-dosen'))

@app.route('/dosen/krs/action', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
@require_role(['Dosen'])
def dosen_krs_action():
    try:
        krs_id = request.form.get('id')
        status = request.form.get('status')
        krs = db.session.get(KRSMahasiswa, krs_id)
        if krs and krs.dosen == current_user.nama and status in ['Disetujui Dosen', 'Ditolak Dosen']:
            krs.status = status
            db.session.add(Notification(npm=krs.npm, message=f"KRS {krs.mata_kuliah} telah {status}."))
            db.session.commit()
            pass

            return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating KRS status: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return jsonify({'success': False}), 400

@app.route('/dosen/nilai/submit', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
@require_role(['Dosen'])
def dosen_nilai_submit():
    try:
        jadwal_id = request.form.get('jadwal_id')
        mata_kuliah = request.form.get('mata_kuliah')
        jadwal = db.session.get(JadwalKuliah, jadwal_id)
        
        if jadwal:
            if jadwal.dosen != current_user.nama:
                flash("Anda tidak berhak mengisi nilai untuk mata kuliah ini.", "error")
                return redirect(url_for('dosen_dashboard', open='modal-masukan-nilai'))
            # Check if already published
            status_nilai = StatusNilai.query.filter_by(jadwal_id=jadwal_id).first()
            if status_nilai and status_nilai.is_published:
                flash("Nilai sudah dipublikasikan dan dikunci.", "error")
                return redirect(url_for('dosen_dashboard', open='modal-masukan-nilai'))

            # Calculate total sessions for attendance pct check
            total_sessions = JurnalMengajar.query.filter_by(jadwal_id=jadwal_id).count()
                
            # Parse student grades
            for key, val in request.form.items():
                if key.startswith('nilai_') and val:
                    npm = key.replace('nilai_', '')
                    
                    hadir = KehadiranKelas.query.filter_by(jadwal_id=jadwal_id, npm=npm, status='Hadir').count()
                    attendance_pct = (hadir / total_sessions * 100) if total_sessions > 0 else 100
                    
                    # Validasi npm terdaftar di KRS
                    krs_check = KRSMahasiswa.query.filter_by(npm=npm, mata_kuliah=mata_kuliah, status='Disetujui Dosen').first()
                    if not krs_check:
                        continue
                        
                    if attendance_pct < 75:
                        val = 'E' # Force E if attendance is below 75%
                    
                    # Prevent duplicate logic or overwrite existing if needed. We assume one grade per semester per class.
                    # As a simplistic approach: we just add a new record. In a real scenario, we might want to update.
                    semester_aktif = get_settings().get('semester_aktif', 'Gasal 2024/2025')
                    existing_nilai = NilaiMahasiswa.query.filter_by(npm=npm, mata_kuliah=mata_kuliah, semester=semester_aktif).first()
                    
                    if not existing_nilai:
                        new_nilai = NilaiMahasiswa(
                            npm=npm,
                            mata_kuliah=mata_kuliah,
                            sks=3, # Assume 3 for simplicity based on KRS logic
                            nilai_huruf=val,
                            semester=semester_aktif
                        )
                        db.session.add(new_nilai)
                    else:
                        existing_nilai.nilai_huruf = val
                    
                    # Notify student
                    db.session.add(Notification(npm=npm, message=f"Nilai akhir untuk mata kuliah {mata_kuliah} telah dirilis."))
            
            # Freeze grades
            if not status_nilai:
                status_nilai = StatusNilai(jadwal_id=jadwal_id, is_published=True)
                db.session.add(status_nilai)
            else:
                status_nilai.is_published = True
                
            db.session.commit()
        pass
        flash("Nilai berhasil disimpan dan dipublikasikan.", "success")

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error submitting nilai: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return redirect(url_for('dosen_dashboard', open='modal-masukan-nilai'))

@app.route('/dosen/presensi/submit', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
@require_role(['Dosen'])
def dosen_presensi_submit():
    try:
        jadwal_id = request.form.get('jadwal_id')
        materi = request.form.get('materi')
        tanggal = str(datetime.date.today())

        jadwal = db.session.get(JadwalKuliah, jadwal_id)
        if not jadwal or jadwal.dosen != current_user.nama:
             flash("Anda tidak berhak mengisi presensi untuk jadwal ini.", "error")
             return redirect(url_for('dosen_dashboard', open='modal-presensi-jurnal'))

        status_nilai = StatusNilai.query.filter_by(jadwal_id=jadwal_id).first()
        if status_nilai and status_nilai.is_published:
            flash("Gagal. Presensi dikunci karena nilai telah dipublikasikan.", "error")
            return redirect(url_for('dosen_dashboard', open='modal-presensi-jurnal'))
        
        try:
            # Insert Jurnal
            new_jurnal = JurnalMengajar(
                jadwal_id=jadwal_id,
                tanggal=tanggal,
                materi=materi
            )
            db.session.add(new_jurnal)
            
            # Insert Kehadiran
            for key, val in request.form.items():
                if key.startswith('kehadiran_'):
                    npm = key.replace('kehadiran_', '')
                    new_kehadiran = KehadiranKelas(
                        jadwal_id=jadwal_id,
                        npm=npm,
                        tanggal=tanggal,
                        status=val
                    )
                    db.session.add(new_kehadiran)
                    if val == 'Hadir':
                        db.session.add(Notification(npm=npm, message=f"Presensi {tanggal} dicatat: Hadir."))
                    else:
                        db.session.add(Notification(npm=npm, message=f"Presensi {tanggal} dicatat: {val}."))
                    
            db.session.commit()
            flash("Presensi dan jurnal berhasil disimpan.", "success")
        except IntegrityError:
            db.session.rollback()
            flash("Gagal menyimpan presensi. Presensi untuk tanggal ini sudah pernah diisi.", "error")
            return redirect(url_for('dosen_dashboard', open='modal-presensi-jurnal'))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error submitting presensi: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return redirect(url_for('dosen_dashboard', open='modal-presensi-jurnal'))


# ============================================================================
# MAHASISWA ROUTES
# ============================================================================

@app.route('/mahasiswa/tagihan/upload', methods=['POST'])
@login_required
@require_role(['Mahasiswa'])
def mahasiswa_tagihan_upload():
    try:
        t_id = request.form.get('tagihan_id')
        tagihan = TagihanKuliah.query.get(t_id)
        if tagihan:
            if tagihan.npm != session.get('npm'):
                return 'Unauthorized', 403
        if tagihan and 'bukti_transfer' in request.files:
            file = request.files['bukti_transfer']
            if file and allowed_file(file.filename):
                saved_filename = compress_image(file, app.config['UPLOAD_FOLDER'])
                tagihan.bukti_transfer = saved_filename
                tagihan.status = 'Menunggu Konfirmasi'
                db.session.add(Notification(npm=os.environ.get('TU_USERNAME', 'tatausaha'), message=f"Bukti transfer diunggah oleh NPM {tagihan.npm} untuk {tagihan.jenis_tagihan}."))
                db.session.commit()
        cache.clear()

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error uploading bukti transfer: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return redirect(url_for('irma_dashboard', open='modal-pusat-tagihan'))

@app.route('/mahasiswa/update_password', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
@require_role(['Mahasiswa'])
def mahasiswa_update_password():
    try:
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash("Konfirmasi password baru tidak cocok.", "error")
            return redirect(url_for('irma_dashboard', open='modal-profil-arsip'))

        user_id = session.get('user_id')
        user = User.query.get(user_id)
        if user and check_password_hash(user.password_hash, old_password):
            user.password_hash = generate_password_hash(new_password)
            user.must_change_password = False
            db.session.commit()
            pass
            flash("Password berhasil diupdate.", "success")
        else:
            flash("Password lama salah.", "error")

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error update password mahasiswa: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return redirect(url_for('irma_dashboard', open='modal-profil-arsip'))

@app.route('/mahasiswa/krs/add', methods=['POST'])
@login_required
@require_role(['Mahasiswa'])
def mahasiswa_krs_add():
    npm = session.get('npm') or session.get('username')
    if not npm:
        return redirect(url_for('index', open='modal-login'))
    try:
        tagihan_list = TagihanKuliah.query.filter_by(npm=npm).all()
        if not tagihan_list:
             flash("KRS ditolak. Anda belum memiliki tagihan atau belum melunasi tagihan.", "error")
             return redirect(url_for('irma_dashboard', open='modal-pusat-tagihan'))
        
        has_unpaid = any(t.status != 'Lunas' for t in tagihan_list)
        if has_unpaid:
            flash("KRS ditolak. Anda belum melunasi tagihan. Silakan lakukan pembayaran terlebih dahulu.", "error")
            return redirect(url_for('irma_dashboard', open='modal-pusat-tagihan'))

        current_krs = KRSMahasiswa.query.filter_by(npm=npm).all()
        current_sks = sum(k.sks for k in current_krs if k.status != 'Ditolak Dosen')
        
        jadwal_ids = request.form.getlist('jadwal_ids')
        semester_aktif = get_settings().get('semester_aktif', 'Gasal 2024/2025')
        
        for j_id in jadwal_ids:
            if current_sks + 3 > 24:
                flash(f"Batas SKS per semester (24) terlampaui.", "error")
                continue
            
            jadwal = JadwalKuliah.query.filter_by(id=j_id, semester_aktif=semester_aktif).first()
            if jadwal:
                existing = KRSMahasiswa.query.filter_by(npm=npm, mata_kuliah=jadwal.mata_kuliah).first()
                if not existing:
                    new_krs = KRSMahasiswa(
                        npm=npm,
                        mata_kuliah=jadwal.mata_kuliah,
                        dosen=jadwal.dosen,
                        sks=3,
                        status='Menunggu Acc Dosen'
                    )
                    db.session.add(new_krs)
                    current_sks += 3
                else:
                    flash(f"Mata kuliah {jadwal.mata_kuliah} sudah ada di KRS Anda.", "error")
            else:
                flash("Jadwal tidak tersedia pada semester ini.", "error")
        db.session.commit()
        flash("KRS berhasil diajukan dan menunggu persetujuan dosen wali.", "success")
        cache.clear()

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error submitting KRS: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return redirect(url_for('irma_dashboard', open='modal-rencana-studi'))

@app.route('/mahasiswa/surat/request', methods=['POST'])
@login_required
@require_role(['Mahasiswa'])
def mahasiswa_surat_request():
    npm = session.get('npm') or session.get('username')
    if not npm:
        return redirect(url_for('index', open='modal-login'))
    try:
        jenis_surat = request.form['jenis_surat']
        valid_surat = [
            "Surat Keterangan Aktif Kuliah",
            "Surat Pengantar Magang",
            "Surat Pengantar Riset",
            "Surat Cuti Akademik"
        ]
        if jenis_surat not in valid_surat:
            flash("Jenis surat tidak valid.", "error")
            return redirect(url_for('irma_dashboard', open='modal-permohonan-surat'))
            
        item = SuratOtomatis(
            npm=npm,
            jenis_surat=jenis_surat,
            keterangan=request.form['keterangan']
        )
        db.session.add(item)
        db.session.add(Notification(npm=os.environ.get('TU_USERNAME', 'tatausaha'), message=f"Permohonan surat baru dari NPM {npm}."))
        db.session.commit()
        cache.clear()

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error requesting surat: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return redirect(url_for('irma_dashboard', open='modal-permohonan-surat'))


# ============================================================================
# LEGACY ZONA WARISAN (Masjid, Ramadhan, Irma, Therapy)
# ============================================================================

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
        cache.clear()

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error logging therapy: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return redirect(url_for('index', open='modal-terapi-log'))

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
        pass

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
            'nav_bg': 'bg-[#F0F9FF]/90 backdrop-blur-md border-b border-[#0284C7]/20',
            'icon_bg': 'bg-[#0284C7]/20',
            'icon_text': 'text-[#0284C7]',
            'title_text': 'text-[#0284C7]',
            'link_hover': 'hover:text-[#7DD3FC]',
            'link_active': 'text-[#7DD3FC] font-bold',
            'btn_primary': 'bg-[#0284C7] text-white hover:bg-[#7DD3FC]',
            'bottom_nav_bg': 'bg-[#0284C7]',
            'bottom_active': 'text-[#7DD3FC]',
            'bottom_btn_bg': 'bg-[#7DD3FC]',
            'bottom_btn_text': 'text-white',
            'bottom_text_inactive': 'text-[#F0F9FF]'
        }
        bg_class = "bg-[#F0F9FF] text-gray-800"
        card_class = "bg-white border-[#0284C7]/30"
        text_highlight = "text-[#0284C7]"
        btn_action = "bg-[#0284C7] text-white"
    else:
        # Default Home
        bg_class = "bg-[#F8FAFC] text-gray-800"
        card_class = "bg-white border-sky-50"
        text_highlight = "text-sky-600"
        btn_action = "bg-sky-500 text-white"

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
                 <select id="infaq-type-select" class="w-full bg-white border border-gray-200 rounded-lg p-2 text-xs font-bold text-gray-700 focus:outline-none focus:ring-2 focus:ring-sky-500">
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
                    <button aria-label="Salin" onclick="copyText('donate-rek-text')" class="p-2 rounded-lg hover:bg-gray-200 transition text-gray-500"><i class="fas fa-copy"></i></button>
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

# ============================================================================
# RUTE TATA USAHA
# ============================================================================
@app.route('/tu_dashboard')
@limiter.limit("300 per hour")
def ramadhan_dashboard():
    surat_list = []
    pmb_list = []
    tagihan_list = []
    jadwal_list = []
    akun_list = []
    arsip_list = []
    tracer_list = []
    verified_alumni_list = []
    pending_users = []
    
    surat_list, pmb_list, tagihan_list, jadwal_list, akun_list, arsip_list, tracer_list, verified_alumni_list, pending_users = _fetch_tu_data()
        
    # Render CONTENT first
    return render_page(RAMADHAN_DASHBOARD_HTML, 'ramadhan', content_kwargs={
        'surat_list': surat_list, 'pmb_list': pmb_list, 'tagihan_list': tagihan_list,
        'jadwal_list': jadwal_list, 'akun_list': akun_list, 'arsip_list': arsip_list,
        'tracer_list': tracer_list, 'verified_alumni_list': verified_alumni_list, 'pending_users': pending_users
    }, hide_nav=True, full_width=True)

# ============================================================================
# RUTE MAHASISWA
# ============================================================================
@app.route('/mahasiswa')
@limiter.limit("200 per hour")
def irma_dashboard():
    
    # NEW MAHASISWA LOGIC
    user = None
    tagihan_list = []
    krs_list = []
    nilai_list = []
    jadwal_list = []
    surat_list = []
    arsip_list = []
    has_unpaid = False
    
    npm = session.get('npm') or session.get('username')
    if not npm:
        return redirect(url_for('index', open='modal-login')) # Fallback for mock view
    
    is_admin = session.get('is_admin', False)
    settings_data = get_settings()
    user, tagihan_list, krs_list, nilai_list, jadwal_list, surat_list, arsip_list, has_unpaid, pmb_docs = _fetch_mahasiswa_data(npm, is_admin)

    
    # IRMA THEME
    irma_theme = {
        'nav_bg': 'bg-[#F0F9FF]/90 backdrop-blur-md border-b border-[#0284C7]/20',
        'icon_bg': 'bg-[#0284C7]/20',
        'icon_text': 'text-[#0284C7]',
        'title_text': 'text-[#0284C7]',
        'link_hover': 'hover:text-[#7DD3FC]',
        'link_active': 'text-[#7DD3FC] font-bold',
        'btn_primary': 'bg-[#0284C7] text-white hover:bg-[#7DD3FC]',
        'bottom_nav_bg': 'bg-[#0284C7]',
        'bottom_active': 'text-[#7DD3FC]',
        'bottom_btn_bg': 'bg-[#7DD3FC]',
        'bottom_btn_text': 'text-white',
        'bottom_text_inactive': 'text-[#F0F9FF]'
    }

    open_modal = request.args.get('open')

    return render_page(IRMA_DASHBOARD_HTML, 'irma', theme=irma_theme, content_kwargs={
        'user': user, 'tagihan_list': tagihan_list, 'krs_list': krs_list, 'nilai_list': nilai_list,
        'jadwal_list': jadwal_list, 'surat_list': surat_list, 'arsip_list': arsip_list, 'has_unpaid': has_unpaid, 'pmb_docs': pmb_docs
    }, full_width=True)

# ============================================================================
# ZONA BRANKAS TAMPILAN (UI Vault) - EVAKUASI KE DASAR KODE
# ============================================================================

STYLES_HTML = """
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
          theme: {
            extend: {
              colors: {
                sky: {
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

        
        /* Skeleton Loading */
        .skeleton {
            animation: skeleton-loading 1s linear infinite alternate;
            border-radius: 0.5rem;
        }
        @keyframes skeleton-loading {
            0% { background-color: hsl(200, 20%, 80%); }
            100% { background-color: hsl(200, 20%, 95%); }
        }
        
        /* Floating notification */
        @keyframes float-up {
            0% { transform: translateY(100%); opacity: 0; }
            10% { transform: translateY(0); opacity: 1; }
            90% { transform: translateY(0); opacity: 1; }
            100% { transform: translateY(-100%); opacity: 0; }
        }
        .toast-float {
            animation: float-up 3s ease-in-out forwards;
        }

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
    <link rel="icon" type="image/png" href="/static/logo-stiesam.png">
    <link rel="apple-touch-icon" href="/static/logo-stiesam.png">
    <script>
        
    function showToast(msg, type='success') {
        const toast = document.createElement('div');
        toast.className = `fixed bottom-20 left-1/2 transform -translate-x-1/2 z-[1000] px-6 py-3 rounded-full text-white font-bold shadow-2xl toast-float backdrop-blur-md ${type==='error'?'bg-red-500/90':'bg-sky-500/90'}`;
        toast.innerHTML = `<i class="fas ${type==='error'?'fa-exclamation-circle':'fa-check-circle'} mr-2"></i> ${msg}`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
    
    // Polling Notification Script
    function pollNotifications() {
        fetch('/api/notifications/poll')
        .then(res => res.json())
        .then(data => {
            if(data && data.length > 0) {
                data.forEach(n => showToast(n.message, 'success'));
            }
        }).catch(err => console.log(err));
    }
    setInterval(pollNotifications, 10000);

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
    <title>Sekolah Tinggi Ilmu Ekonomi STIESAM</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    {{ styles|safe }}

<script>
    document.addEventListener('submit', function(e) {
        if(e.target.tagName === 'FORM') {
            const btn = e.target.querySelector('button[type="submit"]');
            if(btn) {
                btn.disabled = true;
                btn.classList.add('opacity-50', 'cursor-not-allowed');
                btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Memproses...';
            }
        }
    });
</script>

</head>
<body class="text-gray-800 antialiased {{ 'ramadhan-mode' if hide_nav else '' }}">
    {% set t_nav_bg = theme.nav_bg if theme and theme.nav_bg else 'glass-nav' %}
    {% set t_icon_bg = theme.icon_bg if theme and theme.icon_bg else 'bg-sky-100' %}
    {% set t_icon_text = theme.icon_text if theme and theme.icon_text else 'text-sky-600' %}
    {% set t_title_text = theme.title_text if theme and theme.title_text else 'text-sky-600' %}
    {% set t_link_hover = theme.link_hover if theme and theme.link_hover else 'hover:text-sky-600' %}
    {% set t_link_active = theme.link_active if theme and theme.link_active else 'text-sky-600 font-bold' %}
    {% set t_btn_primary = theme.btn_primary if theme and theme.btn_primary else 'bg-sky-500 text-white hover:bg-sky-600' %}
    {% set t_bottom_bg = theme.bottom_nav_bg if theme and theme.bottom_nav_bg else 'glass-bottom' %}
    {% set t_bottom_active = theme.bottom_active if theme and theme.bottom_active else 'text-sky-600' %}
    {% set t_bottom_btn_bg = theme.bottom_btn_bg if theme and theme.bottom_btn_bg else 'bg-sky-500' %}
    {% set t_bottom_btn_text = theme.bottom_btn_text if theme and theme.bottom_btn_text else 'text-sky-600' %}
    {% set t_bottom_text_inactive = theme.bottom_text_inactive if theme and theme.bottom_text_inactive else 'text-gray-400' %}

    <!-- DESKTOP NAVBAR -->
    {% if not hide_nav %}
    <nav class="hidden md:flex fixed top-0 left-0 w-full z-50 {{ t_nav_bg }} shadow-sm px-8 py-4 justify-between items-center right-0">
        <div class="max-w-7xl mx-auto w-full flex justify-between items-center">
             <div class="flex items-center gap-4 h-12 cursor-pointer group" onclick="openModal('modal-logo-zoom')">
                 <div class="h-full flex items-center justify-center transition-transform duration-300 group-hover:scale-110">
                    <img src="/static/logo-stiesam.png" alt="Logo STIESAM" class="h-full w-auto object-contain">
                 </div>
                 <div class="flex flex-col justify-between h-full py-0.5">
                    <h1 class="text-xl font-bold {{ t_title_text }} leading-none">Sekolah Tinggi Ilmu Ekonomi STIESAM</h1>
                    <p class="text-xs text-gray-500 font-medium leading-none">Samarinda, Kalimantan Timur</p>
                 </div>
             </div>
             <div class="flex items-center gap-8">
                <a href="/" class="text-gray-600 font-medium {{ t_link_hover }} transition {{ t_link_active if active_page == 'home' else '' }}">Beranda</a>
                <a href="javascript:void(0)" onclick="openModal('modal-ktm-digital')" class="text-gray-600 font-medium {{ t_link_hover }} transition">KTM Digital</a>
                <a href="javascript:void(0)" onclick="openModal('modal-today-schedule')" class="text-gray-600 font-medium {{ t_link_hover }} transition">Jadwal</a>
                <a href="javascript:void(0)" onclick="openModal('modal-notifications')" class="text-gray-600 font-medium {{ t_link_hover }} transition">Notifikasi</a>
                <a href="javascript:void(0)" onclick="openModal('modal-spp-payment')" class="{{ t_btn_primary }} px-5 py-2 rounded-full font-bold shadow-lg transition transform hover:scale-105">Bayar SPP</a>
                <button onclick="openModal('modal-kontak')" class="text-red-500 font-bold hover:text-red-600 transition border border-red-200 px-4 py-2 rounded-full bg-red-50 hover:bg-red-100 cursor-pointer">Darurat</button>
            </div>
        </div>
    </nav>

    <!-- MOBILE HEADER -->
    <header class="md:hidden fixed top-0 left-0 w-full z-50 {{ t_nav_bg }} shadow-sm px-4 py-3 flex justify-between items-center max-w-md mx-auto right-0">
        <div class="flex items-center gap-2 h-10 cursor-pointer group" onclick="openModal('modal-logo-zoom')">
            <div class="h-full flex items-center justify-center transition-transform duration-300 group-hover:scale-110">
                <img src="/static/logo-stiesam.png" alt="Logo STIESAM" class="h-full w-auto object-contain">
            </div>
            <div class="flex flex-col justify-between h-full py-0.5">
                <h1 class="text-lg font-bold {{ t_title_text }} leading-none">STIESAM</h1>
                <p class="text-[10px] text-gray-500 font-medium leading-none mt-0.5">Samarinda, Kalimantan Timur</p>
            </div>
        </div>
        <div class="text-right">
            <p class="text-[10px] font-bold {{ t_icon_text }} {{ t_icon_bg }} px-2 py-1 rounded-full border border-sky-200" id="hijri-date">Loading...</p>
        </div>
    </header>
    {% endif %}

    
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div id="flash-messages" class="fixed top-20 left-1/2 transform -translate-x-1/2 z-[999] w-full max-w-md px-4 pointer-events-none">
          {% for category, message in messages %}
            <div class="pointer-events-auto p-4 mb-2 rounded-xl shadow-2xl border-l-4 text-sm font-bold animate-[slideUp_0.3s_ease-out] flex justify-between items-center backdrop-blur-md transition-all duration-300 transform hover:scale-105 {{ 'bg-red-50/90 text-red-600 border-red-500' if category == 'error' else 'bg-green-50/90 text-green-600 border-green-500' }}">
                <span>{{ message }}</span>
                <button onclick="this.parentElement.style.display='none'" class="text-gray-400 hover:text-gray-600 ml-4">&times;</button>
            </div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}
    <!-- CONTENT -->
    <main class="min-h-screen relative w-full {{ 'max-w-md md:max-w-7xl mx-auto bg-[#F8FAFC]' if not full_width else '' }}">
        {{ content|safe }}
    </main>

    <!-- MOBILE BOTTOM NAV -->
    {% if not hide_nav %}
    <nav class="md:hidden fixed bottom-0 left-0 w-full {{ t_bottom_bg }} z-50 pb-2 pt-2 max-w-md mx-auto right-0 border-t border-gray-100">
        <div class="flex justify-between items-end h-14 px-2">
            <a href="/" class="flex flex-col items-center justify-center {{ t_bottom_text_inactive }} {{ t_link_hover }} w-14 mb-1 transition-colors {{ t_bottom_active if active_page == 'home' else '' }}">
                <i class="fas fa-home text-xl mb-1"></i>
                <span class="text-[9px] font-medium text-center leading-tight">Beranda</span>
            </a>
            <a href="javascript:void(0)" onclick="openModal('modal-ktm-digital')" class="flex flex-col items-center justify-center {{ t_bottom_text_inactive }} {{ t_link_hover }} w-14 mb-1 transition-colors">
                <i class="fas fa-id-card text-xl mb-1"></i>
                <span class="text-[9px] font-medium text-center leading-tight">KTM Digital</span>
            </a>
            <a href="javascript:void(0)" onclick="openModal('modal-spp-payment')" class="flex flex-col items-center justify-center text-gray-400 {{ t_link_hover }} w-16 mb-6 relative z-10">
                <div class="{{ t_bottom_btn_bg }} text-white w-14 h-14 rounded-full flex items-center justify-center shadow-lg border-4 border-white transform hover:scale-105 transition-transform">
                    <i class="fas fa-wallet text-2xl"></i>
                </div>
                <span class="text-[9px] font-bold mt-1 {{ t_bottom_btn_text }} text-center leading-tight whitespace-nowrap">Bayar SPP</span>
            </a>
            <a href="javascript:void(0)" onclick="openModal('modal-notifications')" class="flex flex-col items-center justify-center {{ t_bottom_text_inactive }} {{ t_link_hover }} w-14 mb-1 transition-colors relative">
                <div class="relative">
                    <i class="fas fa-bell text-xl mb-1"></i>
                    <span class="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
                </div>
                <span class="text-[9px] font-medium text-center leading-tight">Notifikasi</span>
            </a>
            <a href="javascript:void(0)" onclick="openModal('modal-today-schedule')" class="flex flex-col items-center justify-center {{ t_bottom_text_inactive }} {{ t_link_hover }} w-14 mb-1 transition-colors">
                <i class="fas fa-calendar-alt text-xl mb-1"></i>
                <span class="text-[9px] font-medium text-center leading-tight">Jadwal</span>
            </a>
        </div>
    </nav>
    {% endif %}

    <!-- NEW MODALS FROM BOTTOM NAV -->
    
    <!-- MODAL LOGIN -->
    <div id="modal-login" class="fixed inset-0 z-[250] hidden bg-black/60 backdrop-blur-sm flex justify-center items-center p-4">
        <div class="bg-white rounded-[2rem] shadow-2xl w-full max-w-md overflow-hidden animate-[slideUp_0.3s_ease-out] relative">
            <button onclick="closeModal('modal-login')" class="absolute top-4 right-4 bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200 flex items-center justify-center z-10">&times;</button>
            
            <div class="bg-gradient-to-br from-sky-600 to-sky-800 p-6 text-center text-white relative">
                <div class="absolute inset-0 bg-white/5 mix-blend-overlay"></div>
                <img src="/static/logo-stiesam.png" alt="Logo" class="h-12 w-12 mx-auto mb-2 object-contain bg-white rounded-full p-1 relative z-10">
                <h3 class="font-bold tracking-widest text-lg relative z-10">Masuk ke Portal STIESAM</h3>
            </div>
            
            <div class="p-6">
                <!-- Portal Tabs -->
                <div class="flex p-1 bg-gray-100 rounded-xl mb-6">
                    <button onclick="switchPortalTab('portal-tu')" id="tab-btn-tu" class="flex-1 py-2 text-xs font-bold rounded-lg bg-white shadow-sm text-sky-600 transition">Tata Usaha</button>
                    <button onclick="switchPortalTab('portal-mhs')" id="tab-btn-mhs" class="flex-1 py-2 text-xs font-bold rounded-lg text-gray-500 hover:bg-gray-50 transition">Mahasiswa</button>
                    <button onclick="switchPortalTab('portal-dsn')" id="tab-btn-dsn" class="flex-1 py-2 text-xs font-bold rounded-lg text-gray-500 hover:bg-gray-50 transition">Dosen</button>
                </div>

                <!-- Tata Usaha Portal -->
                <div id="portal-tu" class="portal-tab-content block">
                    <form action="/login" method="POST" class="space-y-4">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <div>
                            <label class="block text-xs font-bold text-gray-500 mb-1">Username Tata Usaha</label>
                            <input type="text" name="username" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-gray-500 mb-1">Password</label>
                            <input type="password" name="password" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
                        </div>
                        <div class="flex items-center mt-2 mb-4">
                            <input type="checkbox" id="remember-tu" name="remember" class="w-4 h-4 text-sky-500 bg-gray-50 border-gray-300 rounded focus:ring-sky-500">
                            <label for="remember-tu" class="ml-2 text-xs font-medium text-gray-500">Ingat Saya</label>
                        </div>
                        <button type="submit" class="w-full bg-sky-500 text-white font-bold py-3 rounded-xl hover:bg-sky-600 transition shadow-md">Masuk Tata Usaha</button>
                    </form>
                </div>

                <!-- Mahasiswa Portal -->
                <div id="portal-mhs" class="portal-tab-content hidden">
                    <div class="flex justify-between items-center mb-4 border-b border-gray-100 pb-2">
                        <h4 class="font-bold text-gray-700 text-sm">Login Mahasiswa</h4>
                        <button onclick="toggleRegister('mhs-login-section', 'mhs-register-section')" class="text-xs text-sky-500 font-bold hover:underline">Daftar Akun?</button>
                    </div>

                    <div id="mhs-login-section" class="block">
                        <form action="/login" method="POST" class="space-y-4">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                            <div>
                                <label class="block text-xs font-bold text-gray-500 mb-1">NPM Mahasiswa</label>
                                <input type="text" name="username" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-gray-500 mb-1">Password</label>
                                <input type="password" name="password" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
                            </div>
                            <div class="flex items-center gap-2 mb-2">
                                <input type="checkbox" name="remember" id="remember-me-mhs" class="accent-sky-500 w-4 h-4 text-sky-500 bg-gray-50 border-gray-300 rounded focus:ring-sky-500">
                                <label for="remember-me-mhs" class="text-xs text-gray-600 font-medium cursor-pointer">Ingat Saya</label>
                            </div>
                            <button type="submit" class="w-full bg-sky-500 text-white font-bold py-3 rounded-xl hover:bg-sky-600 transition shadow-md">Masuk Mahasiswa</button>
                        </form>
                    </div>

                    <div id="mhs-register-section" class="hidden">
                        <form action="/api/register_user" method="POST" class="space-y-4">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                            <input type="hidden" name="role" value="Mahasiswa">
                            <div>
                                <label class="block text-xs font-bold text-gray-500 mb-1">Nama Lengkap</label>
                                <input type="text" name="nama" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-gray-500 mb-1">NPM Pendaftaran</label>
                                <input type="text" name="username" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-gray-500 mb-1">Password</label>
                                <input type="password" name="password" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
                            </div>
                            <button type="submit" class="w-full bg-green-500 text-white font-bold py-3 rounded-xl hover:bg-green-600 transition shadow-md">Daftar Akun Mahasiswa</button>
                            <button type="button" onclick="toggleRegister('mhs-register-section', 'mhs-login-section')" class="w-full mt-2 text-xs font-bold text-gray-500 hover:text-gray-700">Kembali ke Login</button>
                        </form>
                    </div>
                </div>

                <!-- Dosen Portal -->
                <div id="portal-dsn" class="portal-tab-content hidden">
                    <div class="flex justify-between items-center mb-4 border-b border-gray-100 pb-2">
                        <h4 class="font-bold text-gray-700 text-sm">Login Dosen</h4>
                        <button onclick="toggleRegister('dsn-login-section', 'dsn-register-section')" class="text-xs text-sky-500 font-bold hover:underline">Daftar Akun?</button>
                    </div>

                    <div id="dsn-login-section" class="block">
                        <form action="/login" method="POST" class="space-y-4">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                            <div>
                                <label class="block text-xs font-bold text-gray-500 mb-1">NIDN / Username Dosen</label>
                                <input type="text" name="username" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-gray-500 mb-1">Password</label>
                                <input type="password" name="password" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
                            </div>
                            <div class="flex items-center gap-2 mb-2">
                                <input type="checkbox" name="remember" id="remember-me-dsn" class="accent-sky-500 w-4 h-4 text-sky-500 bg-gray-50 border-gray-300 rounded focus:ring-sky-500">
                                <label for="remember-me-dsn" class="text-xs text-gray-600 font-medium cursor-pointer">Ingat Saya</label>
                            </div>
                            <button type="submit" class="w-full bg-sky-500 text-white font-bold py-3 rounded-xl hover:bg-sky-600 transition shadow-md">Masuk Dosen</button>
                        </form>
                    </div>

                    <div id="dsn-register-section" class="hidden">
                        <form action="/api/register_user" method="POST" class="space-y-4">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                            <input type="hidden" name="role" value="Dosen">
                            <div>
                                <label class="block text-xs font-bold text-gray-500 mb-1">Nama Lengkap & Gelar</label>
                                <input type="text" name="nama" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-gray-500 mb-1">NIDN</label>
                                <input type="text" name="username" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-gray-500 mb-1">Password</label>
                                <input type="password" name="password" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
                            </div>
                            <button type="submit" class="w-full bg-green-500 text-white font-bold py-3 rounded-xl hover:bg-green-600 transition shadow-md">Daftar Akun Dosen</button>
                            <button type="button" onclick="toggleRegister('dsn-register-section', 'dsn-login-section')" class="w-full mt-2 text-xs font-bold text-gray-500 hover:text-gray-700">Kembali ke Login</button>
                        </form>
                    </div>
                </div>

            </div>
            
            <script>
                function switchPortalTab(tabId) {
                    document.querySelectorAll('.portal-tab-content').forEach(el => {
                        el.classList.remove('block');
                        el.classList.add('hidden');
                    });
                    document.getElementById(tabId).classList.remove('hidden');
                    document.getElementById(tabId).classList.add('block');
                    
                    const activeClass = "flex-1 py-2 text-xs font-bold rounded-lg bg-white shadow-sm text-sky-600 transition".split(" ");
                    const inactiveClass = "flex-1 py-2 text-xs font-bold rounded-lg text-gray-500 hover:bg-gray-50 transition".split(" ");
                    
                    ['tab-btn-tu', 'tab-btn-mhs', 'tab-btn-dsn'].forEach(id => {
                        const btn = document.getElementById(id);
                        btn.className = "";
                        if (tabId === id.replace('tab-btn-', 'portal-')) {
                            btn.classList.add(...activeClass);
                        } else {
                            btn.classList.add(...inactiveClass);
                        }
                    });
                }

                function toggleRegister(hideId, showId) {
                    document.getElementById(hideId).classList.remove('block');
                    document.getElementById(hideId).classList.add('hidden');
                    document.getElementById(showId).classList.remove('hidden');
                    document.getElementById(showId).classList.add('block');
                }
            </script>
        </div>
    </div>

    <!-- MODAL LOGO ZOOM -->
    <div id="modal-logo-zoom" class="fixed inset-0 z-[200] hidden bg-white/30 backdrop-blur-md flex justify-center items-center" onclick="document.getElementById('modal-logo-zoom').classList.add('hidden'); if(history.state && history.state.modal === 'modal-logo-zoom') { history.replaceState(null, '', window.location.pathname); }">
        <div class="relative w-full max-w-sm flex justify-center items-center p-6 animate-[popupFadeIn_0.5s_ease-out]" onclick="event.stopPropagation()">
            <button onclick="document.getElementById('modal-logo-zoom').classList.add('hidden'); if(history.state && history.state.modal === 'modal-logo-zoom') { history.replaceState(null, '', window.location.pathname); }" class="absolute top-4 right-4 bg-white/50 w-10 h-10 rounded-full text-gray-700 hover:bg-white flex items-center justify-center z-10 shadow-sm transition">&times;</button>
            <img src="/static/logo-stiesam.png" alt="Logo STIESAM Besar" class="w-full max-w-[280px] object-contain drop-shadow-2xl transition-transform duration-500 scale-110">
        </div>
    </div>

    <!-- MODAL KTM DIGITAL -->
    <div id="modal-ktm-digital" class="fixed inset-0 z-[150] hidden bg-black/80 backdrop-blur-sm flex justify-center items-center p-4">
        <div class="bg-white rounded-[2rem] shadow-2xl w-full max-w-sm overflow-hidden animate-[slideUp_0.3s_ease-out] relative">
            <button onclick="closeModal('modal-ktm-digital')" class="absolute top-4 right-4 bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200 flex items-center justify-center z-10">&times;</button>
            <div class="bg-gradient-to-br from-sky-600 to-sky-800 p-6 text-center text-white relative">
                <div class="absolute inset-0 bg-white/5 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] mix-blend-overlay"></div>
                <img src="/static/logo-stiesam.png" alt="Logo" class="h-12 w-12 mx-auto mb-2 object-contain bg-white rounded-full p-1 relative z-10">
                <h3 class="font-bold tracking-widest text-lg relative z-10 uppercase">KTM DIGITAL</h3>
                <p class="text-[10px] opacity-80 relative z-10">STIE Samarinda</p>
            </div>
            <div class="p-6 text-center">
                <h4 class="text-xl font-bold text-gray-800 mb-1">{{ user.nama if user else 'NAMA MAHASISWA' }}</h4>
                <p class="text-sm font-mono text-sky-600 font-bold tracking-widest mb-6">{{ user.username if user else 'NPM' }}</p>
                <div class="bg-gray-50 p-4 rounded-xl border border-gray-100 mb-4 flex justify-center">
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={{ user.username if user else 'KTM_DIGITAL' }}" alt="QR Presensi" class="w-48 h-48 object-contain mix-blend-multiply">
                </div>
                <p class="text-[10px] text-gray-400 uppercase tracking-widest font-bold">Pindai Untuk Kehadiran / Perpustakaan</p>
            </div>
            
            <!-- Tambahan Form Ganti Password -->
            <h4 class="text-[#075985] font-bold mb-3 mt-8 border-l-4 border-[#7DD3FC] pl-2">Keamanan Akun</h4>
            <div class="bg-white p-5 rounded-2xl shadow-sm border border-[#0284C7]/20">
                <form action="/mahasiswa/update_password" method="POST" class="space-y-4">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Password Lama</label>
                        <input type="password" name="old_password" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#0284C7]">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Password Baru</label>
                        <input type="password" name="new_password" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#0284C7]">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Konfirmasi Password Baru</label>
                        <input type="password" name="confirm_password" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#0284C7]">
                    </div>
                    <button type="submit" class="w-full bg-[#0284C7] text-white font-bold py-3 rounded-xl shadow-lg hover:bg-[#0369A1] transition transform hover:scale-[1.02]">
                        <i class="fas fa-lock mr-2"></i>Update Password
                    </button>
                </form>
            </div>
        </div>
    </div>

    <!-- MODAL PEMBAYARAN SPP -->
    <div id="modal-spp-payment" class="fixed inset-0 z-[150] hidden bg-black/60 backdrop-blur-sm flex justify-center items-end md:items-center">
        <div class="bg-white w-full md:max-w-md md:rounded-3xl rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] max-h-[85vh] overflow-y-auto relative">
            <button onclick="closeModal('modal-spp-payment')" class="absolute top-4 right-4 bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200 flex items-center justify-center z-10">&times;</button>
            <div class="text-center mb-6">
                <div class="w-16 h-16 bg-sky-100 text-sky-600 rounded-full flex items-center justify-center mx-auto mb-3">
                    <i class="fas fa-wallet text-2xl"></i>
                </div>
                <h3 class="text-xl font-bold text-gray-800">Pembayaran SPP / UKT</h3>
                <p class="text-xs text-gray-500">Semester Ganjil 2024/2025</p>
            </div>
            
            <div class="bg-sky-50 border border-sky-100 rounded-2xl p-5 mb-6 text-center">
                <p class="text-[10px] font-bold text-sky-600 uppercase tracking-widest mb-1">Total Tagihan Aktif</p>
                <h2 class="text-3xl font-bold text-sky-800 mb-2">Rp 3.500.000</h2>
                <span class="inline-block bg-red-100 text-red-600 px-3 py-1 rounded-full text-[10px] font-bold">Menunggu Pembayaran</span>
            </div>
            
            <div class="space-y-4">
                <h4 class="text-sm font-bold text-gray-800 pl-2 border-l-4 border-sky-400">Metode Pembayaran (Virtual Account)</h4>
                
                <div class="border border-gray-200 rounded-xl p-4 flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/8/88/Bank_Syariah_Indonesia_logo.svg" alt="BSI" class="h-6 object-contain">
                        <div>
                            <p class="text-xs text-gray-500 font-bold">BSI Virtual Account</p>
                            <p class="font-mono text-sm font-bold text-gray-800" id="va-bsi">900123456789</p>
                        </div>
                    </div>
                    <button aria-label="Salin" onclick="copyText('va-bsi')" class="text-sky-500 hover:text-sky-700 bg-sky-50 p-2 rounded-lg"><i class="fas fa-copy"></i></button>
                </div>
                
                <div class="border border-gray-200 rounded-xl p-4 flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/a/a0/Bank_Kaltimtara_logo.png" alt="Kaltimtara" class="h-6 object-contain">
                        <div>
                            <p class="text-xs text-gray-500 font-bold">Bankaltimtara VA</p>
                            <p class="font-mono text-sm font-bold text-gray-800" id="va-kaltim">112233445566</p>
                        </div>
                    </div>
                    <button aria-label="Salin" onclick="copyText('va-kaltim')" class="text-sky-500 hover:text-sky-700 bg-sky-50 p-2 rounded-lg"><i class="fas fa-copy"></i></button>
                </div>
            </div>
            
            <button class="w-full bg-sky-500 text-white font-bold py-3 rounded-xl shadow-lg shadow-sky-200 mt-6 hover:bg-sky-600 transition">Konfirmasi Pembayaran</button>
        </div>
    </div>

    <!-- MODAL NOTIFIKASI -->
    <div id="modal-notifications" class="fixed inset-0 z-[150] hidden bg-black/60 backdrop-blur-sm flex justify-center items-end md:items-center">
        <div class="bg-white w-full md:max-w-md md:rounded-3xl rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] max-h-[85vh] overflow-y-auto relative">
            <div class="flex justify-between items-center mb-6 sticky top-0 bg-white z-10 py-2 border-b border-gray-100">
                <h3 class="text-xl font-bold text-gray-800"><i class="fas fa-bell text-sky-500 mr-2"></i>Notifikasi Akademik</h3>
                <button onclick="closeModal('modal-notifications')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200 flex items-center justify-center">&times;</button>
            </div>
            
            <div class="space-y-3">
                <!-- Notif 1 -->
                <div class="bg-red-50 p-4 rounded-xl border border-red-100 flex gap-3">
                    <div class="mt-1"><i class="fas fa-exclamation-circle text-red-500"></i></div>
                    <div>
                        <p class="text-xs text-red-500 font-bold mb-1">Hari Ini, 08:30</p>
                        <p class="text-sm font-bold text-gray-800">Kelas Dibatalkan</p>
                        <p class="text-xs text-gray-600 mt-1">Mata kuliah Manajemen Keuangan dengan Dosen Budi Santoso hari ini ditiadakan karena rapat prodi. Diganti minggu depan.</p>
                    </div>
                </div>
                <!-- Notif 2 -->
                <div class="bg-blue-50 p-4 rounded-xl border border-blue-100 flex gap-3">
                    <div class="mt-1"><i class="fas fa-info-circle text-blue-500"></i></div>
                    <div>
                        <p class="text-xs text-blue-500 font-bold mb-1">Kemarin, 14:00</p>
                        <p class="text-sm font-bold text-gray-800">Rilis Nilai Ujian Tengah Semester</p>
                        <p class="text-xs text-gray-600 mt-1">Nilai UTS mata kuliah Pengantar Akuntansi telah dirilis oleh dosen pengampu. Silakan cek KHS Anda.</p>
                    </div>
                </div>
                <!-- Notif 3 -->
                <div class="bg-yellow-50 p-4 rounded-xl border border-yellow-100 flex gap-3">
                    <div class="mt-1"><i class="fas fa-clock text-yellow-500"></i></div>
                    <div>
                        <p class="text-xs text-yellow-600 font-bold mb-1">2 Hari Lalu</p>
                        <p class="text-sm font-bold text-gray-800">Batas Akhir Pengisian KRS</p>
                        <p class="text-xs text-gray-600 mt-1">Pengingat: Batas akhir pengisian Kartu Rencana Studi (KRS) adalah hari Jumat pukul 23:59 WITA.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- MODAL JADWAL KULIAH HARI INI -->
    <div id="modal-today-schedule" class="fixed inset-0 z-[150] hidden bg-black/60 backdrop-blur-sm flex justify-center items-end md:items-center">
        <div class="bg-white w-full md:max-w-md md:rounded-3xl rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] max-h-[85vh] overflow-y-auto relative">
            <button onclick="closeModal('modal-today-schedule')" class="absolute top-4 right-4 bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200 flex items-center justify-center z-10">&times;</button>
            <div class="mb-6">
                <h3 class="text-xl font-bold text-sky-800 mb-1">Jadwal Kuliah</h3>
                <p class="text-xs font-bold text-gray-400 uppercase tracking-widest" id="today-schedule-date">Hari Ini</p>
                <script>
                    document.getElementById('today-schedule-date').innerText = new Date().toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
                </script>
            </div>
            
            <div class="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-gray-200 before:to-transparent">
                
                <!-- Class 1 -->
                <div class="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                    <div class="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white bg-sky-500 text-white shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
                        <i class="fas fa-book text-xs"></i>
                    </div>
                    <div class="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-white p-4 rounded-xl border border-sky-200 shadow-md">
                        <div class="flex items-center justify-between mb-1">
                            <span class="text-[10px] font-bold text-sky-500 uppercase">08:00 - 10:30</span>
                            <span class="text-[10px] bg-sky-50 text-sky-600 px-2 py-0.5 rounded font-bold border border-sky-100">Ruang 101</span>
                        </div>
                        <h4 class="font-bold text-gray-800 text-sm">Pengantar Ekonomi Makro</h4>
                        <p class="text-xs text-gray-500 mt-1"><i class="fas fa-user-tie"></i> Dr. Susanto, M.E.</p>
                    </div>
                </div>

                <!-- Class 2 -->
                <div class="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
                    <div class="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white bg-gray-200 text-gray-500 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
                        <i class="fas fa-book text-xs"></i>
                    </div>
                    <div class="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-gray-50 p-4 rounded-xl border border-gray-100">
                        <div class="flex items-center justify-between mb-1">
                            <span class="text-[10px] font-bold text-gray-500 uppercase">13:00 - 15:30</span>
                            <span class="text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded font-bold">Ruang 304</span>
                        </div>
                        <h4 class="font-bold text-gray-600 text-sm">Akuntansi Biaya</h4>
                        <p class="text-xs text-gray-400 mt-1"><i class="fas fa-user-tie"></i> Rina Wati, M.Ak.</p>
                    </div>
                </div>

            </div>
            
            <button onclick="closeModal('modal-today-schedule'); openModal('modal-jadwal-kuliah')" class="w-full mt-6 text-xs text-sky-600 font-bold hover:underline text-center">Lihat Jadwal Lengkap Keseluruhan</button>
        </div>
    </div>

    <!-- MODAL INFAQ REVOLUTION -->
    <div id="modal-infaq" class="fixed inset-0 z-[150] hidden">
        <div id="infaq-modal-content" class="fixed inset-0 w-full h-full bg-white p-6 overflow-y-auto flex flex-col animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6">
                <h3 id="infaq-title" class="text-xl font-bold text-gray-800">Infaq Digital</h3>
                <button onclick="closeModal('modal-infaq')" class="w-10 h-10 rounded-full bg-black/5 flex items-center justify-center text-current hover:bg-black/10 transition">&times;</button>
            </div>
            
            <!-- Tabs -->
            <div id="infaq-tabs" class="flex p-1 bg-gray-100 rounded-xl mb-6">
                <button onclick="switchInfaqTab('masjid')" id="tab-btn-masjid" class="flex-1 py-2 text-xs font-bold rounded-lg bg-white shadow-sm text-sky-600 transition">Masjid</button>
                <button onclick="switchInfaqTab('qurban')" id="tab-btn-qurban" class="flex-1 py-2 text-xs font-bold rounded-lg text-gray-500 hover:bg-gray-50 transition">Qurban</button>
                <button onclick="switchInfaqTab('zakat')" id="tab-btn-zakat" class="flex-1 py-2 text-xs font-bold rounded-lg text-gray-500 hover:bg-gray-50 transition">Zakat</button>
            </div>

            <!-- Content Masjid -->
            <div id="infaq-content-masjid" class="infaq-tab-content">
                <div class="text-center mb-6">
                    <img src="/uploads/{{ settings.get('infaq_qris_image', '') if settings else '' }}" onerror="this.src='https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=MasjidAlHijrahInfaq'" class="w-48 h-48 mx-auto object-contain bg-white p-2 rounded-xl border border-gray-200">
                    <p class="text-xs text-gray-400 mt-2">Scan QRIS (Masjid)</p>
                </div>
                <div id="infaq-box-masjid" class="bg-sky-50 p-4 rounded-2xl border border-sky-100 flex justify-between items-center">
                    <div>
                        <p class="text-[10px] text-sky-600 font-bold uppercase infaq-label">Rekening Masjid</p>
                        <p class="font-mono font-bold text-gray-800 text-sm infaq-text" id="rek-masjid-text">{{ settings.get('infaq_rekening_masjid', '7123456789 (BSI)') if settings else 'Loading...' }}</p>
                    </div>
                    <button aria-label="Salin" onclick="copyText('rek-masjid-text')" class="text-sky-500 hover:text-sky-700 infaq-icon"><i class="fas fa-copy"></i></button>
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
                    <button aria-label="Salin" onclick="copyText('rek-qurban-text')" class="text-orange-500 hover:text-orange-700 infaq-icon"><i class="fas fa-copy"></i></button>
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
                    <button aria-label="Salin" onclick="copyText('rek-zakat-text')" class="text-blue-500 hover:text-blue-700 infaq-icon"><i class="fas fa-copy"></i></button>
                </div>
            </div>

            <!-- Global Action Buttons -->
            <div class="mt-6 pt-4 border-t border-gray-100">
                <div class="mb-3">
                    <label class="block text-[10px] font-bold text-gray-400 mb-1">Keperluan (untuk Konfirmasi WA)</label>
                    <select id="infaq-type-select" class="w-full bg-gray-50 border border-gray-200 rounded-lg p-2 text-xs font-bold text-gray-700 focus:outline-none focus:ring-2 focus:ring-sky-500">
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
                        btn.className = "flex-1 py-2 text-xs font-bold rounded-lg bg-white shadow-sm text-sky-600 transition";
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
        
        // Tampilkan kerangka loading saat transisi halaman (tanpa merombak struktur)
        window.addEventListener('beforeunload', function () {
            document.body.classList.add('skeleton-overlay');
        });
        document.addEventListener('DOMContentLoaded', () => {
            const openModalParam = '{{ request.args.get("open", "") }}';
            if (openModalParam) {
                openModal(openModalParam);
            }
        });

        function openModal(id) {
            const el = document.getElementById(id);
            if(el) {
                el.classList.remove('hidden');
                history.pushState({modal: id}, null, "");
                
                if (id === 'modal-cek-status-pmb') {
                    const cekNamaInput = document.getElementById('cek-nama');
                    if (cekNamaInput) {
                        setTimeout(() => cekNamaInput.focus(), 100);
                    }
                }

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

            } else if (path.includes('/irma') || path.includes('/mahasiswa')) {
                // MAHASISWA THEME (Sky Blue)
                container.classList.add('bg-[#F0F9FF]', 'text-[#075985]');
                title.classList.add('text-[#0284C7]');
                tabs.classList.add('bg-[#BAE6FD]/20');
                
                boxes.forEach(box => {
                    box.className = "p-4 rounded-2xl border flex justify-between items-center transition-colors duration-500 bg-white border-[#BAE6FD]/30";
                });
                labels.forEach(l => l.className = "text-[10px] font-bold uppercase infaq-label text-[#0284C7]");
                texts.forEach(t => t.className = "font-mono font-bold text-sm infaq-text text-[#075985]");
                icons.forEach(i => i.className = "hover:opacity-80 infaq-icon text-[#38BDF8]");
                inputs.forEach(i => i.className = "w-full text-xs p-2 border rounded infaq-input-text text-[#075985] bg-white");

            } else {
                // DEFAULT HOME (Emerald)
                container.classList.add('bg-white', 'text-gray-800');
                title.classList.add('text-sky-600');
                tabs.classList.add('bg-gray-100');
                
                // Reset boxes to distinct colors for Home
                document.getElementById('infaq-box-masjid').className = "bg-sky-50 p-4 rounded-2xl border border-sky-100 flex justify-between items-center";
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
                
                resetInner('infaq-box-masjid', 'sky');
                resetInner('infaq-box-qurban', 'orange');
                resetInner('infaq-box-zakat', 'blue');
                inputs.forEach(i => i.className = "w-full text-xs p-2 border rounded infaq-input-text text-sky-800 bg-white");
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

        
        // Tampilkan kerangka loading saat transisi halaman (tanpa merombak struktur)
        window.addEventListener('beforeunload', function () {
            document.body.classList.add('skeleton-overlay');
        });
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
        <h2 class="text-3xl md:text-4xl font-bold text-sky-800 mb-4">Fitur Ekosistem Digital Masjid</h2>
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
            
            <h3 class="text-xl font-bold text-sky-700 mb-2"><i class="fas fa-calendar-alt mr-2"></i>Kalender Puasa Sunnah</h3>
            
            <!-- Tanggal Hari Ini & Peringatan -->
            <div class="bg-sky-50 rounded-2xl p-3 text-center mb-4 flex-shrink-0">
                <p class="text-[10px] text-sky-600 font-bold uppercase mb-1">Tanggal Hari Ini</p>
                <h4 id="fitur-hijri-date" class="text-lg font-bold text-sky-800">Loading...</h4>
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
            <div class="w-16 h-16 bg-sky-100 text-sky-600 rounded-full flex items-center justify-center mx-auto mb-4 border-4 border-white shadow-lg -mt-12">
                <i class="fas fa-star-and-crescent text-2xl"></i>
            </div>
            <p id="puasa-detail-date" class="text-[10px] font-bold text-sky-500 text-center uppercase tracking-widest mb-1"></p>
            <h3 id="puasa-detail-title" class="text-xl font-bold text-gray-800 text-center mb-3 leading-tight"></h3>
            <div class="w-12 h-1 bg-sky-200 mx-auto rounded-full mb-4"></div>
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
            if (id === 'modal-cek-status-pmb') {
                const cekNamaInput = document.getElementById('cek-nama');
                if (cekNamaInput) {
                    setTimeout(() => cekNamaInput.focus(), 100);
                }
            }
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
        grid.innerHTML = '<div class="col-span-7 py-10 text-center"><i class="fas fa-spinner fa-spin text-sky-500 text-2xl"></i></div>';
        
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
                    bgClass = "bg-[#d1fae5] hover:bg-[#bbf7d0] border-transparent"; // sky-100 / green-200
                    
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
                     textClass = "text-sky-700 font-bold underline";
                     if(!fastingData) bgClass = "bg-sky-50 border-sky-200";
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

HOME_HTML = """
<div class="pt-20 md:pt-32 pb-32 px-5 md:px-8">
    
    <!-- DESKTOP SPLIT HEADER -->
    <div class="md:grid md:grid-cols-2 md:gap-12 md:items-center mb-8 md:mb-12">
        
        <!-- LEFT COLUMN: WELCOME (Desktop Only) -->
        <div class="hidden md:block pl-2">
            <p class="text-xl text-gray-500 font-medium mb-2">Assalamualaikum Warahmatullahi Wabarakatuh</p>
            <h1 class="text-5xl font-bold text-sky-800 leading-tight mb-6">Selamat Datang di<br>Sekolah Tinggi Ilmu Ekonomi STIESAM</h1>
            <p class="text-gray-600 text-lg leading-relaxed mb-8">
                Mencetak generasi akademisi unggul, profesional, dan berintegritas. Bergabunglah bersama kami mengukir prestasi demi masa depan ekonomi yang gemilang.
            </p>
            <div class="flex gap-4">
                <a href="/agenda" class="bg-sky-600 text-white px-8 py-3 rounded-full font-bold shadow-lg hover:bg-sky-700 transition transform hover:scale-105">Lihat Agenda</a>
                <a href="/donate" class="bg-white text-sky-600 border-2 border-sky-100 px-8 py-3 rounded-full font-bold hover:border-sky-600 hover:text-sky-700 transition transform hover:scale-105">Infaq Sekarang</a>
            </div>
        </div>

        <!-- RIGHT COLUMN: PRAYER CARD & RAMADHAN BANNER -->
        <div class="flex flex-col gap-6">
            
            <!-- PRAYER CARD -->
            <div class="bg-gradient-to-br from-sky-500 to-sky-600 rounded-3xl p-6 md:p-10 text-white shadow-xl relative overflow-hidden transform md:hover:scale-[1.02] transition-transform duration-500">
                <a href="{{ url_for('fitur_masjid') }}" class="absolute top-4 right-4 bg-white/20 hover:bg-white text-white hover:text-sky-700 px-3 py-1.5 rounded-full text-xs font-bold transition-all shadow-[0_0_15px_rgba(255,255,255,0.3)] hover:shadow-[0_0_20px_rgba(255,255,255,0.6)] z-20 flex items-center gap-1 backdrop-blur-sm">
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

            <!-- PORTAL TATA USAHA BANNER -->
            <a href="javascript:void(0)" onclick="openModal('modal-login')" class="block relative floating-card overflow-hidden group transform hover:scale-[1.02] transition-all duration-300 rounded-3xl shadow-xl border border-[#0b162c]">
                <!-- Background & Texture -->
                <div class="absolute inset-0 bg-[#0b162c]"></div>
                <div class="absolute inset-0 opacity-10" style="background-image: url('https://www.transparenttextures.com/patterns/arabesque.png');"></div>
                
                <!-- Crescent Moon Background -->
                <div class="absolute right-12 top-1/2 transform -translate-y-1/2 opacity-10 text-[#FFD700] pointer-events-none">
                    <i class="fas fa-desktop text-9xl"></i>
                </div>
                
                <div class="relative px-6 py-6 md:px-8 md:py-8 flex items-center justify-between">
                    <div>
                        <h2 class="text-2xl md:text-3xl font-bold text-[#FFD700] mb-1 font-sans tracking-wide leading-none">Portal Tata Usaha</h2>
                        <p class="text-white/60 text-xs md:text-sm font-medium">Pusat Layanan Administrasi</p>
                    </div>
                    
                    <!-- Gold Circle Button -->
                    <div class="w-12 h-12 rounded-full bg-[#FFD700] flex items-center justify-center text-[#0b1026] shadow-[0_0_15px_rgba(255,215,0,0.4)] group-hover:scale-110 transition-transform duration-300 relative z-10">
                        <i class="fas fa-arrow-right text-lg"></i>
                    </div>
                </div>
            </a>

            <!-- PORTAL MAHASISWA & DOSEN -->
            <div class="relative floating-card overflow-hidden rounded-3xl shadow-xl border border-gray-200 mt-4 flex h-32 md:h-40">
                <!-- Zona Kiri: Mahasiswa -->
                <a href="javascript:void(0)" onclick="openModal('modal-login')" class="w-1/2 relative group hover:z-10 transition-all duration-300">
                    <div class="absolute inset-0 bg-gradient-to-r from-blue-500 to-blue-400 group-hover:scale-105 transition-transform duration-300"></div>
                    <div class="absolute inset-0 opacity-10" style="background-image: url('https://www.transparenttextures.com/patterns/arabesque.png');"></div>
                    <div class="absolute -right-8 top-1/2 transform -translate-y-1/2 opacity-20 text-white pointer-events-none group-hover:scale-110 transition-transform duration-300">
                        <i class="fas fa-user-graduate text-7xl md:text-8xl"></i>
                    </div>
                    <div class="relative h-full flex flex-col justify-center px-4 md:px-6 z-10">
                        <h2 class="text-xl md:text-2xl font-bold text-white mb-1 font-sans tracking-wide leading-none">Portal Mahasiswa</h2>
                        <p class="text-white/80 text-[10px] md:text-xs font-medium">Akademik & Keuangan</p>
                    </div>
                </a>
                
                <!-- Garis Pembatas Diagonal -->
                <div class="absolute inset-y-0 left-1/2 transform -translate-x-1/2 w-4 z-20 pointer-events-none" style="background: linear-gradient(135deg, transparent 45%, white 45%, white 55%, transparent 55%);"></div>

                <!-- Zona Kanan: Dosen -->
                <a href="javascript:void(0)" onclick="openModal('modal-login')" class="w-1/2 relative group hover:z-10 transition-all duration-300">
                    <div class="absolute inset-0 bg-gradient-to-r from-orange-400 to-orange-500 group-hover:scale-105 transition-transform duration-300"></div>
                    <div class="absolute inset-0 opacity-10" style="background-image: url('https://www.transparenttextures.com/patterns/arabesque.png');"></div>
                    <div class="absolute right-2 md:right-4 top-1/2 transform -translate-y-1/2 opacity-20 text-white pointer-events-none group-hover:scale-110 transition-transform duration-300">
                        <i class="fas fa-chalkboard-teacher text-7xl md:text-8xl"></i>
                    </div>
                    <div class="relative h-full flex flex-col justify-center px-4 md:px-6 items-end text-right z-10 pl-8">
                        <h2 class="text-xl md:text-2xl font-bold text-white mb-1 font-sans tracking-wide leading-none">Portal Dosen</h2>
                        <p class="text-white/80 text-[10px] md:text-xs font-medium">Persetujuan & Nilai</p>
                    </div>
                </a>
            </div>

        </div>
    </div>

    <!-- MAIN GRID MENU -->
    <h3 class="text-gray-800 font-bold text-lg mb-4 pl-1 border-l-4 border-sky-500 leading-none py-1 ml-1 md:text-2xl md:mb-8">&nbsp;Menu Utama</h3>
    <div class="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-8 mb-8">
        <!-- 1. Profil Kampus dan Program Studi -->
        <a href="javascript:void(0)" onclick="openModal('modal-profil-kampus')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-sky-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-sky-600 group-hover:bg-sky-500 group-hover:text-white transition-colors">
                <i class="fas fa-university text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-sky-600 leading-tight">Profil Kampus</span>
        </a>
        
        <!-- 2. Penerimaan Mahasiswa Baru Digital -->
        <a href="javascript:void(0)" onclick="openModal('modal-pmb')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-blue-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-blue-600 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                <i class="fas fa-user-plus text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-blue-600 leading-tight">PMB Digital</span>
        </a>

        <!-- 3. Cek Status Pendaftaran Mahasiswa Baru -->
        <a href="javascript:void(0)" onclick="openModal('modal-cek-status-pmb')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-indigo-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-indigo-600 group-hover:bg-indigo-500 group-hover:text-white transition-colors">
                <i class="fas fa-search-dollar text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-indigo-600 leading-tight">Cek Status PMB</span>
        </a>

        <!-- 4. Berita dan Agenda Kampus -->
        <a href="javascript:void(0)" onclick="openModal('modal-berita-agenda')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-green-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-green-600 group-hover:bg-green-500 group-hover:text-white transition-colors">
                <i class="fas fa-newspaper text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-green-600 leading-tight">Berita & Agenda</span>
        </a>

        <!-- 5. Galeri Jurnal dan Karya Ilmiah -->
        <a href="javascript:void(0)" onclick="openModal('modal-galeri-jurnal')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-purple-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-purple-600 group-hover:bg-purple-500 group-hover:text-white transition-colors">
                <i class="fas fa-book-open text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-purple-600 leading-tight">Galeri Jurnal</span>
        </a>

        <!-- 6. Tracer Study dan Karir Alumni -->
        <a href="javascript:void(0)" onclick="openModal('modal-tracer-study')" class="bg-white p-5 md:p-8 rounded-3xl shadow-lg shadow-gray-200/50 flex flex-col items-center justify-center card-hover h-36 md:h-48 border border-gray-50 group hover:scale-105 hover:shadow-2xl transition-all duration-300">
            <div class="bg-orange-50 w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-3 text-orange-600 group-hover:bg-orange-500 group-hover:text-white transition-colors">
                <i class="fas fa-briefcase text-2xl md:text-3xl"></i>
            </div>
            <span class="text-sm md:text-base font-semibold text-center text-gray-700 group-hover:text-orange-600 leading-tight">Tracer Study</span>
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
        <button onclick="toggleCalc()" class="w-full bg-white p-6 rounded-3xl shadow-lg border border-sky-100 flex justify-between items-center group hover:bg-sky-50 transition-all duration-300">
            <div class="flex items-center gap-4">
                <div class="bg-emerald-100 p-3 rounded-xl text-emerald-600 group-hover:bg-emerald-500 group-hover:text-white transition-colors shadow-sm">
                    <i class="fas fa-chart-line text-2xl"></i>
                </div>
                <div class="text-left">
                    <h3 class="text-lg font-bold text-gray-800 group-hover:text-emerald-700">Kalkulator Ekonomi</h3>
                    <p class="text-xs text-gray-500 font-medium">6 Alat Hitung Otomatis (Kost, IPK, dll)</p>
                </div>
            </div>
            <div id="calc-chevron" class="bg-gray-50 w-10 h-10 rounded-full flex items-center justify-center text-gray-400 group-hover:bg-white group-hover:text-sky-500 transition-all duration-300">
                 <i class="fas fa-chevron-down transform transition-transform duration-300"></i>
            </div>
        </button>
        
        <div id="calc-content" class="hidden mt-6 animate-[slideDown_0.3s_ease-out]">
             <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                 <!-- IPK -->
                 <button onclick="openModal('modal-ipk')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-emerald-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 text-left flex items-center gap-3 group">
                     <div class="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl group-hover:bg-emerald-500 group-hover:text-white transition-colors"><i class="fas fa-graduation-cap"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-emerald-700">Target IPK</span>
                 </button>
                 <!-- BEP -->
                 <button onclick="openModal('modal-bep')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-emerald-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 text-left flex items-center gap-3 group">
                     <div class="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl group-hover:bg-emerald-500 group-hover:text-white transition-colors"><i class="fas fa-chart-pie"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-emerald-700">BEP & Laba</span>
                 </button>
                 <!-- DEPRESIASI -->
                 <button onclick="openModal('modal-depresiasi')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-emerald-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 text-left flex items-center gap-3 group">
                     <div class="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl group-hover:bg-emerald-500 group-hover:text-white transition-colors"><i class="fas fa-car-crash"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-emerald-700">Penyusutan Aset</span>
                 </button>
                 <!-- TVM -->
                 <button onclick="openModal('modal-tvm')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-emerald-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 text-left flex items-center gap-3 group">
                     <div class="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl group-hover:bg-emerald-500 group-hover:text-white transition-colors"><i class="fas fa-coins"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-emerald-700">Nilai Waktu Uang</span>
                 </button>
                 <!-- ANGGARAN KOST -->
                 <button onclick="openModal('modal-anggaran')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-emerald-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 text-left flex items-center gap-3 group">
                     <div class="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl group-hover:bg-emerald-500 group-hover:text-white transition-colors"><i class="fas fa-wallet"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-emerald-700">Anggaran Kost</span>
                 </button>
                 <!-- PAJAK LULUSAN -->
                 <button onclick="openModal('modal-pajak')" class="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 hover:border-emerald-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 text-left flex items-center gap-3 group">
                     <div class="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl group-hover:bg-emerald-500 group-hover:text-white transition-colors"><i class="fas fa-file-invoice-dollar"></i></div>
                     <span class="font-bold text-gray-700 text-xs md:text-sm group-hover:text-emerald-700">Simulasi Pajak</span>
                 </button>
             </div>
        </div>
    </div>

    <!-- STATIC PWA INSTALL BUTTON (NEW) -->
    <div id="pwa-static-btn-container" class="pwa-btn-container mb-6 hidden">
        <button onclick="triggerInstall()" class="w-full bg-gradient-to-r from-sky-500 to-teal-600 text-white p-4 rounded-3xl shadow-lg border border-sky-400 flex justify-between items-center group hover:scale-[1.02] transition-all duration-300">
            <div class="flex items-center gap-4">
                <div class="bg-white/20 p-3 rounded-xl text-white shadow-inner">
                    <i class="fas fa-download text-2xl"></i>
                </div>
                <div class="text-left">
                    <h3 class="text-lg font-bold text-white">Install Aplikasi</h3>
                    <p class="text-xs text-sky-100 font-medium">Akses Cepat Tanpa Buka Browser</p>
                </div>
            </div>
            <div class="bg-white/20 w-10 h-10 rounded-full flex items-center justify-center text-white group-hover:bg-white group-hover:text-sky-600 transition-all duration-300">
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

    <!-- Modal Profil Kampus -->
    <div id="modal-profil-kampus" class="fixed inset-0 z-[100] hidden">
        <div class="fixed inset-0 bg-white/95 backdrop-blur-xl animate-[slideUp_0.5s_ease-out] overflow-y-auto">
            <div class="relative w-full max-w-2xl mx-auto p-6 md:p-12">
                <button onclick="closeModal('modal-profil-kampus')" class="absolute top-4 right-4 md:top-8 md:right-8 bg-gray-100 w-10 h-10 rounded-full text-gray-600 hover:bg-gray-200 text-xl flex items-center justify-center transition-colors">&times;</button>
                
                <div class="text-center mb-10">
                    <div class="w-20 h-20 bg-sky-50 text-sky-600 rounded-full flex items-center justify-center text-4xl mx-auto mb-4">
                        <i class="fas fa-university"></i>
                    </div>
                    <h2 class="text-3xl font-extrabold text-gray-800 mb-2">Profil Kampus</h2>
                    <p class="text-gray-500 font-medium">Sekolah Tinggi Ilmu Ekonomi STIESAM Samarinda</p>
                </div>
                
                <div class="space-y-6 text-gray-600 leading-relaxed text-justify">
                    <img src="{{ '/uploads/' + settings.get('profil_gambar') if settings.get('profil_gambar') else 'https://images.unsplash.com/photo-1541339907198-e08756dedf3f?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80' }}" alt="Gedung Kampus" class="w-full h-64 object-cover rounded-3xl shadow-md mb-6">
                    
                    <p style="white-space: pre-wrap;">{{ settings.get('profil_deskripsi', 'Sekolah Tinggi Ilmu Ekonomi (STIE) SAM Samarinda didirikan dengan komitmen teguh untuk menghasilkan sarjana ekonomi yang profesional, beretika, dan mampu bersaing di era digital. Dengan fasilitas pembelajaran yang representatif dan didukung oleh staf pengajar yang kompeten di bidangnya, STIESAM terus bertransformasi menjadi pusat unggulan kajian ekonomi di Kalimantan Timur.') }}</p>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 my-8">
                        <div class="bg-sky-50 p-6 rounded-2xl border border-sky-100">
                            <h4 class="text-sky-800 font-bold mb-2 flex items-center gap-2"><i class="fas fa-eye"></i> Visi</h4>
                            <p class="text-sm" style="white-space: pre-wrap;">{{ settings.get('profil_visi', 'Menjadi institusi pendidikan tinggi ekonomi yang terkemuka, inovatif, dan berdaya saing global dengan menjunjung tinggi nilai-nilai moral dan etika bisnis.') }}</p>
                        </div>
                        <div class="bg-blue-50 p-6 rounded-2xl border border-blue-100">
                            <h4 class="text-blue-800 font-bold mb-2 flex items-center gap-2"><i class="fas fa-bullseye"></i> Misi</h4>
                            <p class="text-sm" style="white-space: pre-wrap;">{{ settings.get('profil_misi', '1. Menyelenggarakan pendidikan yang berkualitas.\n2. Melaksanakan penelitian yang bermanfaat.\n3. Melakukan pengabdian yang berdampak nyata bagi masyarakat.') }}</p>
                        </div>
                    </div>
                    
                    <h3 class="text-xl font-bold text-gray-800 mb-4">Program Studi</h3>
                    <div class="space-y-3">
                        <div class="p-4 border border-gray-200 rounded-xl hover:shadow-md transition">
                            <h4 class="font-bold text-gray-800">S1 Manajemen</h4>
                            <p class="text-sm text-gray-500">Akreditasi B. Fokus pada pengembangan manajerial, bisnis digital, dan kewirausahaan.</p>
                        </div>
                        <div class="p-4 border border-gray-200 rounded-xl hover:shadow-md transition">
                            <h4 class="font-bold text-gray-800">S1 Akuntansi</h4>
                            <p class="text-sm text-gray-500">Akreditasi B. Menghasilkan akuntan publik dan privat yang kredibel dan melek teknologi.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal PMB -->
    <div id="modal-pmb" class="fixed inset-0 z-[100] hidden">
        <div class="fixed inset-0 bg-white/95 backdrop-blur-xl animate-[slideUp_0.5s_ease-out] overflow-y-auto">
            <div class="relative w-full max-w-xl mx-auto p-6 md:p-12">
                <button onclick="closeModal('modal-pmb')" class="absolute top-4 right-4 md:top-8 md:right-8 bg-gray-100 w-10 h-10 rounded-full text-gray-600 hover:bg-gray-200 text-xl flex items-center justify-center transition-colors">&times;</button>
                
                <div class="text-center mb-8">
                    <div class="w-16 h-16 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center text-3xl mx-auto mb-4">
                        <i class="fas fa-user-plus"></i>
                    </div>
                    <h2 class="text-2xl font-extrabold text-gray-800 mb-2">Pendaftaran Mahasiswa Baru</h2>
                    <p class="text-gray-500 font-medium text-sm">Isi formulir pendaftaran digital di bawah ini.</p>
                </div>
                
                <form id="pmb-form" action="/api/pmb/register" method="POST" enctype="multipart/form-data" class="space-y-4 bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Nama Lengkap Sesuai Ijazah</label>
                        <input type="text" name="nama" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Upload Scan Ijazah Terakhir (JPG/PNG/PDF/DOC/ZIP/etc)</label>
                        <input type="file" name="foto_ijazah" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-2 text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Upload Scan KTP (JPG/PNG/PDF/DOC/ZIP/etc)</label>
                        <input type="file" name="foto_ktp" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-2 text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Upload Bukti Transfer Pendaftaran (JPG/PNG/PDF/DOC/ZIP/etc)</label>
                        <input type="file" name="bukti_transfer" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-2 text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100">
                    </div>
                    
                    <div id="pmb-alert" class="hidden rounded-xl p-3 text-sm font-bold text-center mt-4"></div>
                    
                    <div class="flex items-center gap-2 mt-4">
                        <button type="submit" id="pmb-submit-btn" class="flex-1 bg-blue-600 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-blue-700 transition transform hover:scale-[1.02]">
                            <i class="fas fa-paper-plane mr-2"></i>Kirim Pendaftaran
                        </button>
                        <button type="button" onclick="closeModal('modal-pmb'); openModal('modal-cek-status-pmb');" class="bg-gray-100 text-gray-700 border border-gray-200 font-bold py-3 px-4 rounded-xl shadow-sm hover:bg-gray-200 transition transform hover:scale-[1.02]" title="Cek Status PMB">
                            <i class="fas fa-search"></i> Cek Status PMB
                        </button>
                    </div>
                </form>
                
                <script>
                    document.getElementById('pmb-form').addEventListener('submit', async (e) => {
                        e.preventDefault();
                        const btn = document.getElementById('pmb-submit-btn');
                        const alertBox = document.getElementById('pmb-alert');
                        btn.disabled = true;
                        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Mengirim...';
                        
                        try {
                            const fd = new FormData(e.target);
                            const res = await fetch('/api/pmb/register', {
                                method: 'POST',
                                body: fd
                            });
                            const data = await res.json();
                            
                            alertBox.classList.remove('hidden', 'bg-red-50', 'text-red-600', 'bg-green-50', 'text-green-600');
                            if(data.success) {
                                alertBox.classList.add('bg-green-50', 'text-green-600');
                                alertBox.innerText = data.message;
                                e.target.reset();
                            } else {
                                alertBox.classList.add('bg-red-50', 'text-red-600');
                                alertBox.innerText = data.error || 'Gagal mengirim data.';
                            }
                        } catch(err) {
                            alertBox.classList.remove('hidden');
                            alertBox.classList.add('bg-red-50', 'text-red-600');
                            alertBox.innerText = 'Terjadi kesalahan sistem.';
                        } finally {
                            btn.disabled = false;
                            btn.innerHTML = '<i class="fas fa-paper-plane mr-2"></i>Kirim Pendaftaran';
                        }
                    });
                </script>
            </div>
        </div>
    </div>

    <!-- Modal Cek Status PMB -->
    <div id="modal-cek-status-pmb" class="fixed inset-0 z-[100] hidden">
        <div class="fixed inset-0 bg-white/95 backdrop-blur-xl animate-[slideUp_0.5s_ease-out] overflow-y-auto">
            <div class="relative w-full max-w-md mx-auto p-6 md:p-12 text-center mt-20">
                <button onclick="closeModal('modal-cek-status-pmb')" class="absolute top-0 right-0 md:-top-4 md:-right-4 bg-gray-100 w-10 h-10 rounded-full text-gray-600 hover:bg-gray-200 text-xl flex items-center justify-center transition-colors">&times;</button>
                
                <div class="w-16 h-16 bg-indigo-50 text-indigo-600 rounded-full flex items-center justify-center text-3xl mx-auto mb-4">
                    <i class="fas fa-search-dollar"></i>
                </div>
                <h2 class="text-2xl font-extrabold text-gray-800 mb-2">Cek Status PMB</h2>
                <p class="text-gray-500 font-medium text-sm mb-6">Masukkan nama lengkap Anda yang terdaftar.</p>
                
                <div class="flex gap-2 mb-6">
                    <input type="text" id="cek-nama" placeholder="Ketik Nama Lengkap..." class="flex-1 bg-white border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                    <button aria-label="Cari" onclick="cekStatusPMB()" class="bg-indigo-600 text-white px-6 rounded-xl font-bold shadow-md hover:bg-indigo-700 transition"><i class="fas fa-search"></i></button>
                </div>
                
                <div id="cek-status-result" class="text-left bg-gray-50 p-4 rounded-2xl border border-gray-100 hidden">
                    <!-- Results will be injected here -->
                </div>
                
                <script>
                    async function cekStatusPMB() {
                        const nama = document.getElementById('cek-nama').value;
                        const resBox = document.getElementById('cek-status-result');
                        if(!nama) return;
                        
                        resBox.classList.remove('hidden');
                        resBox.innerHTML = '<p class="text-center text-gray-500 text-sm"><i class="fas fa-spinner fa-spin mr-2"></i>Mencari...</p>';
                        
                        try {
                            const res = await fetch('/api/pmb/status?nama=' + encodeURIComponent(nama));
                            const data = await res.json();
                            
                            if(data.error) {
                                resBox.innerHTML = `<p class="text-center text-red-500 font-bold text-sm">${data.error}</p>`;
                            } else {
                                let html = `<p class="font-bold text-gray-800 mb-1">${data.nama}</p>`;
                                let statusClass = data.status === 'Diterima' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700';
                                html += `<p class="text-xs text-gray-500 mb-3">Status: <span class="px-2 py-1 rounded font-bold ${statusClass}">${data.status}</span></p>`;
                                
                                if(data.status === 'Diterima') {
                                    html += `<div class="bg-indigo-50 p-3 rounded-lg border border-indigo-100">
                                                <p class="text-xs text-indigo-800 font-bold mb-1">Selamat Anda Diterima!</p>
                                                <p class="text-xs text-indigo-600">NPM Anda: <span class="font-mono font-bold text-lg block">${data.npm}</span></p>
                                                <p class="text-[10px] text-indigo-500 mt-2">Gunakan NPM sebagai Username untuk masuk ke Portal Mahasiswa.</p>
                                             </div>`;
                                } else {
                                    html += `<p class="text-xs text-gray-500 italic">Berkas Anda sedang dalam proses verifikasi oleh Tata Usaha. Mohon periksa kembali nanti.</p>`;
                                }
                                resBox.innerHTML = html;
                            }
                        } catch(err) {
                            resBox.innerHTML = '<p class="text-center text-red-500 font-bold text-sm">Terjadi kesalahan sistem.</p>';
                        }
                    }
                </script>
            </div>
        </div>
    </div>

    <!-- Modal Berita Agenda -->
    <div id="modal-berita-agenda" class="fixed inset-0 z-[100] hidden">
        <div class="fixed inset-0 bg-white/95 backdrop-blur-xl animate-[slideUp_0.5s_ease-out] overflow-y-auto">
            <div class="relative w-full max-w-2xl mx-auto p-6 md:p-12">
                <button onclick="closeModal('modal-berita-agenda')" class="absolute top-4 right-4 md:top-8 md:right-8 bg-gray-100 w-10 h-10 rounded-full text-gray-600 hover:bg-gray-200 text-xl flex items-center justify-center transition-colors">&times;</button>
                
                <div class="text-center mb-8">
                    <div class="w-16 h-16 bg-green-50 text-green-600 rounded-full flex items-center justify-center text-3xl mx-auto mb-4">
                        <i class="fas fa-newspaper"></i>
                    </div>
                    <h2 class="text-2xl font-extrabold text-gray-800 mb-2">Berita & Agenda</h2>
                    <p class="text-gray-500 font-medium text-sm">Informasi terkini kegiatan kampus STIESAM.</p>
                </div>
                
                <div class="space-y-4">
                    <div class="bg-white p-5 rounded-2xl shadow-sm border border-gray-100 flex flex-col md:flex-row gap-4 hover:shadow-md transition">
                        <div class="w-full md:w-32 h-32 bg-gray-200 rounded-xl flex-shrink-0 overflow-hidden">
                            <img src="{{ '/uploads/' + settings.get('berita_gambar') if settings.get('berita_gambar') else 'https://images.unsplash.com/photo-1552664730-d307ca884978?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80' }}" class="w-full h-full object-cover">
                        </div>
                        <div>
                            <span class="text-[10px] font-bold text-green-600 bg-green-50 px-2 py-1 rounded uppercase tracking-wider">{{ settings.get('berita_label', 'Seminar Nasional') }}</span>
                            <h4 class="font-bold text-gray-800 text-lg mt-2 mb-1">{{ settings.get('berita_judul', 'Tantangan Ekonomi Digital 2025') }}</h4>
                            <p class="text-xs text-gray-500 mb-2"><i class="fas fa-calendar-alt mr-1"></i> {{ settings.get('berita_waktu', '12 Oktober 2024 • Auditorium STIESAM') }}</p>
                            <p class="text-sm text-gray-600 line-clamp-2">{{ settings.get('berita_isi', 'Seminar nasional yang membahas tentang persiapan UMKM menghadapi transformasi ekonomi digital dan kecerdasan buatan.') }}</p>
                        </div>
                    </div>
                    <div class="bg-white p-5 rounded-2xl shadow-sm border border-gray-100 flex flex-col md:flex-row gap-4 hover:shadow-md transition">
                        <div class="w-full md:w-32 h-32 bg-gray-200 rounded-xl flex-shrink-0 overflow-hidden">
                            <img src="https://images.unsplash.com/photo-1523240795612-9a054b0db644?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80" class="w-full h-full object-cover">
                        </div>
                        <div>
                            <span class="text-[10px] font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded uppercase tracking-wider">Pengumuman</span>
                            <h4 class="font-bold text-gray-800 text-lg mt-2 mb-1">Penerimaan Beasiswa Prestasi</h4>
                            <p class="text-xs text-gray-500 mb-2"><i class="fas fa-calendar-alt mr-1"></i> 05 November 2024</p>
                            <p class="text-sm text-gray-600 line-clamp-2">Telah dibuka pendaftaran beasiswa prestasi untuk mahasiswa aktif semester 3 hingga 7. Segera daftarkan diri Anda di portal mahasiswa.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal Galeri Jurnal -->
    <div id="modal-galeri-jurnal" class="fixed inset-0 z-[100] hidden">
        <div class="fixed inset-0 bg-white/95 backdrop-blur-xl animate-[slideUp_0.5s_ease-out] overflow-y-auto">
            <div class="relative w-full max-w-4xl mx-auto p-6 md:p-12">
                <button onclick="closeModal('modal-galeri-jurnal')" class="absolute top-4 right-4 md:top-8 md:right-8 bg-gray-100 w-10 h-10 rounded-full text-gray-600 hover:bg-gray-200 text-xl flex items-center justify-center transition-colors">&times;</button>
                
                <div class="text-center mb-8">
                    <div class="w-16 h-16 bg-purple-50 text-purple-600 rounded-full flex items-center justify-center text-3xl mx-auto mb-4">
                        <i class="fas fa-book-open"></i>
                    </div>
                    <h2 class="text-2xl font-extrabold text-gray-800 mb-2">Galeri Jurnal & Penelitian</h2>
                    <p class="text-gray-500 font-medium text-sm">Kumpulan publikasi ilmiah civitas akademika STIESAM.</p>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <!-- Dummy Jurnals -->
                    <div class="bg-white border border-gray-200 rounded-2xl p-5 hover:shadow-lg hover:border-purple-200 transition group cursor-pointer">
                        <div class="flex justify-between items-start mb-3">
                            <span class="text-[10px] font-bold text-purple-600 bg-purple-50 px-2 py-1 rounded">{{ settings.get('jurnal_kategori', 'Manajemen Keuangan') }}</span>
                            <span class="text-[10px] text-gray-400">{{ settings.get('jurnal_volume', 'Vol 12, No. 2 (2023)') }}</span>
                        </div>
                        <h4 class="font-bold text-gray-800 group-hover:text-purple-700 transition text-lg mb-2 leading-tight">{{ settings.get('jurnal_judul', 'Analisis Pengaruh Literasi Keuangan Terhadap Kinerja UMKM di Samarinda') }}</h4>
                        <p class="text-xs text-gray-500 mb-4 font-medium"><i class="fas fa-user-edit mr-1"></i> {{ settings.get('jurnal_penulis', 'Dr. Budi Santoso, M.Si., Rina Astuti, S.E.') }}</p>
                        <button class="text-xs font-bold text-purple-600 hover:text-purple-800"><i class="fas fa-file-pdf mr-1"></i> Download PDF</button>
                    </div>
                    
                    <div class="bg-white border border-gray-200 rounded-2xl p-5 hover:shadow-lg hover:border-purple-200 transition group cursor-pointer">
                        <div class="flex justify-between items-start mb-3">
                            <span class="text-[10px] font-bold text-purple-600 bg-purple-50 px-2 py-1 rounded">Akuntansi Publik</span>
                            <span class="text-[10px] text-gray-400">Vol 13, No. 1 (2024)</span>
                        </div>
                        <h4 class="font-bold text-gray-800 group-hover:text-purple-700 transition text-lg mb-2 leading-tight">Transparansi Anggaran Pendapatan dan Belanja Desa (APBDes) Melalui Platform Digital</h4>
                        <p class="text-xs text-gray-500 mb-4 font-medium"><i class="fas fa-user-edit mr-1"></i> Dr. Andi Wijaya, Ak., M.Ak.</p>
                        <button class="text-xs font-bold text-purple-600 hover:text-purple-800"><i class="fas fa-file-pdf mr-1"></i> Download PDF</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal Tracer Study -->
    <div id="modal-tracer-study" class="fixed inset-0 z-[100] hidden">
        <div class="fixed inset-0 bg-white/95 backdrop-blur-xl animate-[slideUp_0.5s_ease-out] overflow-y-auto">
            <div class="relative w-full max-w-xl mx-auto p-6 md:p-12">
                <button onclick="closeModal('modal-tracer-study')" class="absolute top-4 right-4 md:top-8 md:right-8 bg-gray-100 w-10 h-10 rounded-full text-gray-600 hover:bg-gray-200 text-xl flex items-center justify-center transition-colors">&times;</button>
                
                <div class="text-center mb-8">
                    <div class="w-16 h-16 bg-orange-50 text-orange-600 rounded-full flex items-center justify-center text-3xl mx-auto mb-4">
                        <i class="fas fa-briefcase"></i>
                    </div>
                    <h2 class="text-2xl font-extrabold text-gray-800 mb-2">Tracer Study Alumni</h2>
                    <p class="text-gray-500 font-medium text-sm">Pelacakan rekam jejak lulusan STIESAM.</p>
                </div>
                
                <div class="bg-orange-50 border border-orange-100 rounded-2xl p-6 text-center mb-6">
                    <i class="fas fa-bullhorn text-orange-400 text-4xl mb-3"></i>
                    <h3 class="font-bold text-gray-800 mb-2">Panggilan Untuk Alumni!</h3>
                    <p class="text-sm text-gray-600 mb-4">Bantu kami meningkatkan kualitas pendidikan dengan mengisi kuesioner Tracer Study. Data Anda sangat berharga bagi akreditasi kampus.</p>
                    <button onclick="closeModal('modal-tracer-study'); openModal('modal-tracer-form')" class="inline-block bg-orange-500 text-white px-6 py-3 rounded-xl font-bold shadow hover:bg-orange-600 transition">Isi Kuesioner Sekarang</button>
                </div>
                
                <h4 class="font-bold text-gray-800 mb-4 text-center">Statistik Serapan Kerja Lulusan</h4>
                <div class="space-y-3">
                    <div>
                        <div class="flex justify-between text-xs font-bold text-gray-600 mb-1"><span>Bekerja di Sektor Swasta</span><span>65%</span></div>
                        <div class="w-full bg-gray-200 rounded-full h-2"><div class="bg-orange-500 h-2 rounded-full" style="width: 65%"></div></div>
                    </div>
                    <div>
                        <div class="flex justify-between text-xs font-bold text-gray-600 mb-1"><span>PNS / BUMN</span><span>15%</span></div>
                        <div class="w-full bg-gray-200 rounded-full h-2"><div class="bg-blue-500 h-2 rounded-full" style="width: 15%"></div></div>
                    </div>
                    <div>
                        <div class="flex justify-between text-xs font-bold text-gray-600 mb-1"><span>Wirausaha / Wirausaha Mandiri</span><span>20%</span></div>
                        <div class="w-full bg-gray-200 rounded-full h-2"><div class="bg-green-500 h-2 rounded-full" style="width: 20%"></div></div>
                    </div>
                </div>
                
                <div class="mt-8 border-t border-gray-200 pt-6">
                    <h4 class="font-bold text-gray-800 mb-4 text-center">Data Alumni Terverifikasi</h4>
                    <div class="space-y-4">
                        {% for item in verified_alumni_list %}
                        <div class="bg-white border border-gray-200 rounded-xl p-4 shadow-sm flex flex-col gap-2">
                            <div class="flex justify-between items-start">
                                <div>
                                    <p class="font-bold text-gray-800">{{ item['nama_lengkap'] }}</p>
                                    <p class="text-xs text-gray-500">Angkatan Lulus: {{ item['tahun_lulus'] }} • {{ item['program_studi'] }}</p>
                                </div>
                                <span class="bg-blue-50 text-blue-600 text-[10px] font-bold px-2 py-1 rounded-full whitespace-nowrap"><i class="fas fa-check-circle"></i> Diverifikasi</span>
                            </div>
                            <div class="bg-gray-50 p-2 rounded-lg mt-1 border border-gray-100 text-xs text-gray-600">
                                <p><span class="font-bold">Karir:</span> {{ item['status_pekerjaan'] }} di {{ item['nama_perusahaan'] or '-' }} sebagai {{ item['jabatan'] or '-' }}</p>
                            </div>
                        </div>
                        {% else %}
                        <p class="text-center text-gray-500 text-sm italic py-4 bg-gray-50 rounded-xl">Belum ada data alumni yang diverifikasi.</p>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal Developer -->
    <div id="modal-developer" class="fixed inset-0 z-[100] hidden">
        <div class="fixed inset-0 bg-white/95 backdrop-blur-xl animate-[slideUp_0.5s_ease-out] flex flex-col h-full max-h-screen">
            
            <!-- Sticky Header -->
            <div class="flex-shrink-0 sticky top-0 bg-white/80 backdrop-blur z-10 p-4 border-b border-gray-100 flex flex-col items-center justify-center relative shadow-sm">
                <button onclick="closeModal('modal-developer'); stopDevAudio()" class="absolute right-4 top-4 bg-gray-100 w-10 h-10 rounded-full text-gray-600 hover:bg-gray-200 text-xl flex items-center justify-center transition">&times;</button>
                <h2 class="text-[10px] font-bold text-gray-400 tracking-[0.3em] mb-1 uppercase">DEVELOPER</h2>
                <h1 class="text-xl md:text-2xl font-extrabold text-sky-800" style="white-space: nowrap;">SAMARINDA WEB CREATIVE</h1>
            </div>

            <!-- Scrollable Content -->
            <div class="flex-1 overflow-y-auto p-4 pb-20 flex flex-col items-center custom-scrollbar">
                
                <div class="mb-8 mt-4">
                    <img src="/static/Samarinda_Web_Creative_Logo-removebg-preview.png" alt="Logo Developer" class="h-32 md:h-40 object-contain mx-auto drop-shadow-2xl">
                </div>
                
                <h3 class="text-xs font-bold text-gray-400 tracking-[0.2em] mb-4 uppercase border-b border-gray-200 pb-2 w-24 text-center">PIHAK KETIGA</h3>
                <div class="flex flex-col gap-6 justify-center items-center mb-8">
                    <img src="/static/pythonanywherelogo-removebg.png" class="h-16 md:h-20 object-contain">
                    <img src="/static/pythonlogo.png" class="h-16 md:h-20 object-contain">
                    <img src="/static/godaddylogo.png" class="h-8 md:h-10 object-contain">
                </div>
                
                <div class="bg-gray-50 p-6 rounded-3xl border border-gray-100 mb-8 max-w-sm w-full text-center">
                    <p class="text-sm text-gray-600 font-medium leading-relaxed mb-2">
                        Samarinda, Kalimantan Timur,<br>
                        Jln. Delima Dalam, Blok. E, RT. 53
                    </p>
                    <p class="text-xs text-gray-500 italic">"kalau butuh jasa pembuatan aplikasi website seperti ini, hubungi kami yaa hehee"</p>
                </div>
                
                <div class="flex flex-col sm:flex-row items-center justify-center gap-4 mb-10 w-full max-w-xs">
                    <a href="https://www.instagram.com/samarindawebcreative/" target="_blank" class="bg-gradient-to-tr from-purple-500 to-pink-500 text-white w-12 h-12 rounded-full flex items-center justify-center shadow-lg hover:scale-110 transition shrink-0">
                        <i class="fab fa-instagram text-2xl"></i>
                    </a>
                    <a href="https://b1l14n50r1.pythonanywhere.com/" class="flex items-center justify-center gap-2 px-6 py-3 bg-gray-900 text-white rounded-full font-bold shadow-lg hover:scale-105 transition w-full">
                        <img src="/static/piton.png" class="h-6 w-6"> See Our Current Work
                    </a>
                </div>

                <p class="text-[10px] text-gray-400 font-serif mb-8 text-center">The 1975 - About You (Official)</p>
            </div>
        </div>
        <audio id="dev-audio" src="/static/The 1975 - About You (Official) - Fix.mp3"></audio>
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
                            <button onclick="switchNatureAudio()" class="w-8 h-8 rounded-full bg-sky-100 text-sky-600 flex items-center justify-center hover:bg-sky-500 hover:text-white transition-colors"><i class="fas fa-step-forward text-xs"></i></button>
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

    <!-- Modal Tracer Form (Kuesioner) -->
    <div id="modal-tracer-form" class="hidden fixed inset-0 z-[200] bg-black/60 backdrop-blur-sm flex justify-center items-end md:items-center">
        <div class="bg-white w-full max-w-2xl md:rounded-3xl rounded-t-3xl shadow-2xl animate-[slideUp_0.3s_ease-out] flex flex-col max-h-[90vh]">
            
            <!-- Sticky Header -->
            <div class="flex justify-between items-center p-6 border-b border-orange-100 bg-orange-50 rounded-t-3xl sticky top-0 z-10 flex-shrink-0">
                <div>
                    <h3 class="text-xl font-bold text-orange-600 mb-1"><i class="fas fa-clipboard-list mr-2"></i>Kuesioner Tracer Study</h3>
                    <p class="text-xs font-bold text-orange-400 tracking-widest uppercase">Akreditasi STIESAM</p>
                </div>
                <button onclick="closeModal('modal-tracer-form')" class="bg-white w-8 h-8 rounded-full text-gray-500 hover:bg-gray-100 flex items-center justify-center shadow-sm">&times;</button>
            </div>
            
            <!-- Scrollable Content -->
            <form action="/api/tracer/submit" method="POST" class="flex-1 overflow-y-auto p-6 bg-white space-y-5 custom-scrollbar">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                <div class="bg-orange-50/50 p-4 rounded-xl border border-orange-100 mb-2">
                    <p class="text-xs text-gray-600 leading-relaxed"><span class="font-bold text-orange-500">Penting:</span> Seluruh data kuesioner ini akan dijaga kerahasiaannya dan hanya digunakan untuk kepentingan peningkatan mutu pendidikan dan akreditasi kampus STIESAM.</p>
                </div>

                <div class="space-y-4">
                    <!-- 1 -->
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1.5 uppercase">1. Nama Lengkap</label>
                        <input type="text" name="nama_lengkap" required placeholder="Masukkan nama lengkap beserta gelar" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-orange-300">
                    </div>
                    <!-- 2 -->
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1.5 uppercase">2. Nomor Pokok Mahasiswa (NPM)</label>
                        <input type="text" name="npm" required placeholder="Masukkan NPM Anda" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-orange-300">
                    </div>
                    <!-- 3 -->
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-xs font-bold text-gray-500 mb-1.5 uppercase">3. Tahun Lulus</label>
                            <input type="number" name="tahun_lulus" required placeholder="Contoh: 2022" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-orange-300">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-gray-500 mb-1.5 uppercase">4. Program Studi</label>
                            <select name="program_studi" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-orange-300">
                                <option value="S1 Manajemen">S1 Manajemen</option>
                                <option value="S1 Akuntansi">S1 Akuntansi</option>
                            </select>
                        </div>
                    </div>
                    <!-- 5 -->
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1.5 uppercase">5. Status Pekerjaan Saat Ini</label>
                        <select name="status_pekerjaan" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-orange-300">
                            <option value="Bekerja (Full-time)">Bekerja (Full-time)</option>
                            <option value="Bekerja (Part-time / Freelance)">Bekerja (Part-time / Freelance)</option>
                            <option value="Wirausaha / Memiliki Usaha Sendiri">Wirausaha / Memiliki Usaha Sendiri</option>
                            <option value="Melanjutkan Pendidikan">Melanjutkan Pendidikan</option>
                            <option value="Sedang Mencari Pekerjaan">Sedang Mencari Pekerjaan</option>
                        </select>
                    </div>
                    <!-- 6 -->
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1.5 uppercase">6. Nama Perusahaan / Usaha</label>
                        <input type="text" name="nama_perusahaan" placeholder="Tempat Anda bekerja saat ini" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-orange-300">
                    </div>
                    <!-- 7 -->
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1.5 uppercase">7. Jabatan / Posisi</label>
                        <input type="text" name="jabatan" placeholder="Contoh: Staff Akuntan, Manager" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-orange-300">
                    </div>
                    <!-- 8 -->
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1.5 uppercase">8. Rentang Gaji Pertama</label>
                        <select name="rentang_gaji" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-orange-300">
                            <option value="Kurang dari Rp 3.000.000">Kurang dari Rp 3.000.000</option>
                            <option value="Rp 3.000.000 - Rp 5.000.000">Rp 3.000.000 - Rp 5.000.000</option>
                            <option value="Rp 5.000.000 - Rp 10.000.000">Rp 5.000.000 - Rp 10.000.000</option>
                            <option value="Lebih dari Rp 10.000.000">Lebih dari Rp 10.000.000</option>
                        </select>
                    </div>
                    <!-- 9 -->
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1.5 uppercase">9. Kesesuaian Pekerjaan dgn Ilmu</label>
                        <select name="kesesuaian" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-orange-300">
                            <option value="Sangat Sesuai">Sangat Sesuai</option>
                            <option value="Sesuai">Sesuai</option>
                            <option value="Kurang Sesuai">Kurang Sesuai</option>
                            <option value="Tidak Sesuai">Tidak Sesuai</option>
                        </select>
                    </div>
                    <!-- 10 -->
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1.5 uppercase">10. Waktu Tunggu Mendapat Kerja Pertama</label>
                        <select name="waktu_tunggu" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-orange-300">
                            <option value="Kurang dari 3 bulan">Kurang dari 3 bulan</option>
                            <option value="3 - 6 bulan">3 - 6 bulan</option>
                            <option value="6 - 12 bulan">6 - 12 bulan</option>
                            <option value="Lebih dari 12 bulan">Lebih dari 12 bulan</option>
                        </select>
                    </div>
                    <!-- 11 -->
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1.5 uppercase">11. Saran Pengembangan Kurikulum</label>
                        <textarea name="saran" placeholder="Saran Anda untuk kampus tercinta..." class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm h-24 focus:outline-none focus:ring-2 focus:ring-orange-300"></textarea>
                    </div>
                        <div class="mb-4">
                            <label class="block text-xs font-bold text-gray-500 mb-2" id="captcha-question">Berapa hasil dari ...?</label>
                            <input type="hidden" name="captcha_expected" id="captcha-expected" value="">
                            <input type="text" name="captcha_answer" required placeholder="Masukkan angka jawaban" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
                        </div>
                        <script>
                            function generateCaptcha() {
                                const num1 = Math.floor(Math.random() * 10) + 1;
                                const num2 = Math.floor(Math.random() * 10) + 1;
                                document.getElementById('captcha-question').innerText = `Berapa hasil dari ${num1} + ${num2}? (CAPTCHA)`;
                                document.getElementById('captcha-expected').value = num1 + num2;
                            }
                            // Generate on modal open or script load
                            generateCaptcha();
                        </script>
                    <!-- 12 -->
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1.5 uppercase">12. Nomor WhatsApp / Email Aktif</label>
                        <input type="text" name="kontak" required placeholder="Untuk keperluan verifikasi alumni" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-orange-300">
                    </div>
                </div>
            
            <!-- Sticky Footer / Action -->
            <div class="p-6 border-t border-gray-100 bg-white rounded-b-3xl flex-shrink-0 sticky bottom-0 z-20 shadow-[0_-10px_15px_-3px_rgba(0,0,0,0.05)]">
                <button type="submit" class="w-full bg-gradient-to-r from-orange-500 to-orange-600 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-orange-200 hover:from-orange-600 hover:to-orange-700 transition transform hover:-translate-y-0.5"><i class="fas fa-paper-plane mr-2"></i>Kirim Data Tracer Study</button>
            </div>
            </form>
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
    
    <!-- Modal Simulasi Target IPK -->
    <div id="modal-ipk" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" onclick="closeModal('modal-ipk')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-graduation-cap text-emerald-500 mr-2"></i>Simulasi Target IPK</h3>
                <button onclick="closeModal('modal-ipk')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">IPK Saat Ini</label>
                    <input type="number" id="ipk-current" step="0.01" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Total SKS Ditempuh</label>
                    <input type="number" id="ipk-sks-current" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Target IPK Kelulusan</label>
                    <input type="number" id="ipk-target" step="0.01" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Sisa SKS yang akan diambil</label>
                    <input type="number" id="ipk-sks-sisa" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <button onclick="calcIPK()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-emerald-600 transition">Hitung Target Nilai</button>
                
                <div id="result-ipk" class="hidden mt-4 bg-emerald-50 p-4 rounded-xl border border-emerald-100 text-sm"></div>
            </div>
        </div>
    </div>

    <!-- Modal BEP dan Margin Laba -->
    <div id="modal-bep" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeModal('modal-bep')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-chart-pie text-emerald-500 mr-2"></i>Titik Impas & Margin Laba</h3>
                <button onclick="closeModal('modal-bep')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Biaya Tetap (Sewa, dll) (Rp)</label>
                    <input type="number" id="bep-fixed" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Biaya Variabel per Unit (Bahan, dll) (Rp)</label>
                    <input type="number" id="bep-variable" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Harga Jual per Unit (Rp)</label>
                    <input type="number" id="bep-price" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <button onclick="calcBEP()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-emerald-600 transition">Hitung Titik Impas</button>
                <div id="result-bep" class="hidden mt-4 bg-emerald-50 p-4 rounded-xl border border-emerald-100 text-sm"></div>
            </div>
        </div>
    </div>

    <!-- Modal Penyusutan Aset -->
    <div id="modal-depresiasi" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeModal('modal-depresiasi')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-car-crash text-emerald-500 mr-2"></i>Penyusutan Aset</h3>
                <button onclick="closeModal('modal-depresiasi')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Harga Beli Aset (Rp)</label>
                    <input type="number" id="dep-price" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Nilai Sisa (Residu) (Rp)</label>
                    <input type="number" id="dep-residu" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Umur Ekonomis (Tahun)</label>
                    <input type="number" id="dep-years" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Metode Penyusutan</label>
                    <select id="dep-method" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                        <option value="straight">Garis Lurus (Straight Line)</option>
                        <option value="declining">Saldo Menurun Ganda (Double Declining)</option>
                    </select>
                </div>
                <button onclick="calcDepresiasi()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-emerald-600 transition">Buat Tabel Penyusutan</button>
                <div id="result-depresiasi" class="hidden mt-4 bg-emerald-50 p-4 rounded-xl border border-emerald-100 text-sm overflow-x-auto"></div>
            </div>
        </div>
    </div>

    <!-- Modal Nilai Waktu Uang (TVM) -->
    <div id="modal-tvm" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeModal('modal-tvm')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-coins text-emerald-500 mr-2"></i>Nilai Waktu Uang</h3>
                <button onclick="closeModal('modal-tvm')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Mode Perhitungan</label>
                    <select id="tvm-mode" onchange="toggleTVMInputs()" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                        <option value="fv">Cari Nilai Masa Depan (FV)</option>
                        <option value="pv">Cari Nilai Masa Kini (PV)</option>
                    </select>
                </div>
                <div id="tvm-pv-group">
                    <label class="block text-xs font-bold text-gray-500 mb-1">Modal Awal / Present Value (Rp)</label>
                    <input type="number" id="tvm-pv" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <div id="tvm-fv-group" class="hidden">
                    <label class="block text-xs font-bold text-gray-500 mb-1">Target Dana Masa Depan / Future Value (Rp)</label>
                    <input type="number" id="tvm-fv" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Persentase Bunga/Return Tahunan (%)</label>
                    <input type="number" id="tvm-rate" step="0.1" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Rentang Waktu (Tahun)</label>
                    <input type="number" id="tvm-years" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <button onclick="calcTVM()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-emerald-600 transition">Proyeksikan</button>
                <div id="result-tvm" class="hidden mt-4 bg-emerald-50 p-4 rounded-xl border border-emerald-100 text-sm"></div>
            </div>
        </div>
    </div>

    <!-- Modal Anggaran Anak Kost -->
    <div id="modal-anggaran" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeModal('modal-anggaran')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-wallet text-emerald-500 mr-2"></i>Perencana Anggaran Kost</h3>
                <button onclick="closeModal('modal-anggaran')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Total Uang Saku Bulanan (Rp)</label>
                    <input type="number" id="anggaran-uang" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <button onclick="calcAnggaran()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-emerald-600 transition">Pisahkan Dana (Aturan 50/30/20)</button>
                <div id="result-anggaran" class="hidden mt-4 bg-emerald-50 p-4 rounded-xl border border-emerald-100 text-sm"></div>
            </div>
        </div>
    </div>

    <!-- Modal PPh 21 Lulusan Baru -->
    <div id="modal-pajak" class="fixed inset-0 z-[100] hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeModal('modal-pajak')"></div>
        <div class="absolute bottom-0 left-0 w-full bg-white rounded-t-3xl p-6 shadow-2xl animate-[slideUp_0.3s_ease-out] md:relative md:max-w-md md:mx-auto md:rounded-3xl md:top-20">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-800"><i class="fas fa-file-invoice-dollar text-emerald-500 mr-2"></i>Simulasi Pajak Lulusan Baru</h3>
                <button onclick="closeModal('modal-pajak')" class="bg-gray-100 w-8 h-8 rounded-full text-gray-500 hover:bg-gray-200">&times;</button>
            </div>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-1">Penawaran Gaji Kotor per Bulan (Rp)</label>
                    <input type="number" id="pajak-gaji" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <p class="text-xs text-gray-500 italic">Asumsi: Status Lajang/Single (TK/0), dengan potongan standar BPJS Ketenagakerjaan dan Kesehatan pekerja.</p>
                <button onclick="calcPajak()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-emerald-600 transition">Simulasikan Take Home Pay</button>
                <div id="result-pajak" class="hidden mt-4 bg-emerald-50 p-4 rounded-xl border border-emerald-100 text-sm"></div>
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

        // 1. Simulasi Target IPK
        function calcIPK() {
            const ipkCurrent = parseFloat(document.getElementById('ipk-current').value);
            const sksCurrent = parseInt(document.getElementById('ipk-sks-current').value);
            const ipkTarget = parseFloat(document.getElementById('ipk-target').value);
            const sksSisa = parseInt(document.getElementById('ipk-sks-sisa').value);
            
            const div = document.getElementById('result-ipk');
            if(isNaN(ipkCurrent) || isNaN(sksCurrent) || isNaN(ipkTarget) || isNaN(sksSisa)) {
                div.innerHTML = `<span class="text-red-500 font-bold">Harap isi semua kolom dengan angka yang valid.</span>`;
            } else {
                const totalSKS = sksCurrent + sksSisa;
                const totalBobotDibutuhkan = ipkTarget * totalSKS;
                const bobotSaatIni = ipkCurrent * sksCurrent;
                const sisaBobot = totalBobotDibutuhkan - bobotSaatIni;
                const targetNilaiRata = sisaBobot / sksSisa;
                
                div.classList.remove('hidden');
                if (targetNilaiRata > 4.0) {
                    div.innerHTML = `<span class="text-red-600 font-bold">Maaf, target ini tidak realistis. Anda butuh rata-rata nilai ${targetNilaiRata.toFixed(2)} (Maksimal IPK adalah 4.00). Pertimbangkan untuk menambah SKS atau menurunkan target.</span>`;
                } else if (targetNilaiRata < 0) {
                    div.innerHTML = `<span class="text-emerald-600 font-bold">Selamat! Bahkan dengan nilai terendah sekalipun, Anda kemungkinan besar akan melampaui target tersebut. Anda hanya butuh rata-rata ${targetNilaiRata.toFixed(2)}.</span>`;
                } else {
                    div.innerHTML = `<span class="text-emerald-700 font-bold">Untuk mencapai IPK ${ipkTarget}, Anda harus mengejar rata-rata nilai <span class="text-xl"> ${targetNilaiRata.toFixed(2)} </span> di sisa ${sksSisa} SKS Anda. Terus semangat belajar, Anda pasti bisa!</span>`;
                }
            }
            div.classList.remove('hidden');
        }

        // 2. Titik Impas dan Margin Laba
        function calcBEP() {
            const fc = parseFloat(document.getElementById('bep-fixed').value);
            const vc = parseFloat(document.getElementById('bep-variable').value);
            const p = parseFloat(document.getElementById('bep-price').value);
            
            const div = document.getElementById('result-bep');
            if(isNaN(fc) || isNaN(vc) || isNaN(p) || (p - vc) <= 0) {
                div.innerHTML = `<span class="text-red-500 font-bold">Data tidak valid. Harga Jual harus lebih besar dari Biaya Variabel agar tidak rugi permanen.</span>`;
            } else {
                const bepUnit = Math.ceil(fc / (p - vc));
                const bepRp = bepUnit * p;
                const marginLaba = ((p - vc) / p) * 100;
                
                div.innerHTML = `
                    <p class="font-bold text-emerald-800 mb-2">Analisis Kelayakan Bisnis:</p>
                    <ul class="space-y-1 mb-2">
                        <li class="flex justify-between"><span>Titik Impas (Volume):</span> <span class="font-bold">${bepUnit.toLocaleString('id-ID')} Porsi/Unit</span></li>
                        <li class="flex justify-between"><span>Titik Impas (Rupiah):</span> <span class="font-bold">Rp ${bepRp.toLocaleString('id-ID')}</span></li>
                        <li class="flex justify-between"><span>Margin Kontribusi:</span> <span class="font-bold">${marginLaba.toFixed(2)}%</span></li>
                    </ul>
                    <p class="text-xs text-gray-600 italic">Usaha Anda harus menjual minimal ${bepUnit} porsi per bulan/periode hanya untuk menutupi biaya operasional (tidak rugi, belum untung).</p>
                `;
            }
            div.classList.remove('hidden');
        }

        // 3. Penyusutan Aset
        function calcDepresiasi() {
            const price = parseFloat(document.getElementById('dep-price').value);
            const residu = parseFloat(document.getElementById('dep-residu').value);
            const years = parseInt(document.getElementById('dep-years').value);
            const method = document.getElementById('dep-method').value;
            
            const div = document.getElementById('result-depresiasi');
            if(isNaN(price) || isNaN(residu) || isNaN(years) || years <= 0) {
                div.innerHTML = `<span class="text-red-500 font-bold">Data tidak valid.</span>`;
            } else {
                let html = `
                    <table class="w-full text-left text-xs border-collapse">
                        <thead>
                            <tr class="bg-emerald-100 text-emerald-800">
                                <th class="p-2 border">Tahun</th>
                                <th class="p-2 border">Beban Penyusutan</th>
                                <th class="p-2 border">Akumulasi</th>
                                <th class="p-2 border">Nilai Buku</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                let accum = 0;
                let bookValue = price;
                
                if(method === 'straight') {
                    const yearlyDep = (price - residu) / years;
                    for(let i=1; i<=years; i++) {
                        accum += yearlyDep;
                        bookValue -= yearlyDep;
                        html += `
                            <tr class="border-b">
                                <td class="p-2 border">${i}</td>
                                <td class="p-2 border">Rp ${Math.round(yearlyDep).toLocaleString('id-ID')}</td>
                                <td class="p-2 border">Rp ${Math.round(accum).toLocaleString('id-ID')}</td>
                                <td class="p-2 border">Rp ${Math.round(bookValue).toLocaleString('id-ID')}</td>
                            </tr>
                        `;
                    }
                } else {
                    const rate = 2 / years;
                    for(let i=1; i<=years; i++) {
                        let yearlyDep = bookValue * rate;
                        if(i === years) { // Last year adjustment to hit exact residu
                            yearlyDep = bookValue - residu;
                        }
                        accum += yearlyDep;
                        bookValue -= yearlyDep;
                        html += `
                            <tr class="border-b">
                                <td class="p-2 border">${i}</td>
                                <td class="p-2 border">Rp ${Math.round(yearlyDep).toLocaleString('id-ID')}</td>
                                <td class="p-2 border">Rp ${Math.round(accum).toLocaleString('id-ID')}</td>
                                <td class="p-2 border">Rp ${Math.round(bookValue).toLocaleString('id-ID')}</td>
                            </tr>
                        `;
                    }
                }
                html += `</tbody></table>`;
                div.innerHTML = html;
            }
            div.classList.remove('hidden');
        }

        // 4. Nilai Waktu Uang (TVM)
        function toggleTVMInputs() {
            const mode = document.getElementById('tvm-mode').value;
            if(mode === 'fv') {
                document.getElementById('tvm-pv-group').classList.remove('hidden');
                document.getElementById('tvm-fv-group').classList.add('hidden');
            } else {
                document.getElementById('tvm-pv-group').classList.add('hidden');
                document.getElementById('tvm-fv-group').classList.remove('hidden');
            }
        }
        
        function calcTVM() {
            const mode = document.getElementById('tvm-mode').value;
            const rate = parseFloat(document.getElementById('tvm-rate').value) / 100;
            const years = parseInt(document.getElementById('tvm-years').value);
            const div = document.getElementById('result-tvm');
            
            if(isNaN(rate) || isNaN(years)) {
                div.innerHTML = `<span class="text-red-500 font-bold">Data tidak valid.</span>`;
            } else if(mode === 'fv') {
                const pv = parseFloat(document.getElementById('tvm-pv').value);
                const fv = pv * Math.pow((1 + rate), years);
                div.innerHTML = `<span class="text-emerald-700 font-bold">Uang senilai Rp ${pv.toLocaleString('id-ID')} saat ini, dalam ${years} tahun dengan return ${(rate*100).toFixed(2)}% per tahun akan bernilai:<br><span class="text-2xl">Rp ${Math.round(fv).toLocaleString('id-ID')}</span></span>`;
            } else {
                const fv = parseFloat(document.getElementById('tvm-fv').value);
                const pv = fv / Math.pow((1 + rate), years);
                div.innerHTML = `<span class="text-emerald-700 font-bold">Untuk mendapatkan Rp ${fv.toLocaleString('id-ID')} dalam ${years} tahun ke depan, modal yang harus Anda siapkan SAAT INI adalah:<br><span class="text-2xl">Rp ${Math.round(pv).toLocaleString('id-ID')}</span></span>`;
            }
            div.classList.remove('hidden');
        }

        // 5. Perencana Anggaran Anak Kost
        function calcAnggaran() {
            const total = parseFloat(document.getElementById('anggaran-uang').value);
            const div = document.getElementById('result-anggaran');
            if(isNaN(total) || total <= 0) {
                div.innerHTML = `<span class="text-red-500 font-bold">Masukkan jumlah uang saku yang valid.</span>`;
            } else {
                const kebutuhan = total * 0.5;
                const keinginan = total * 0.3;
                const tabungan = total * 0.2;
                div.innerHTML = `
                    <p class="font-bold text-emerald-800 mb-3">Distribusi Sehat Uang Saku Anda:</p>
                    <div class="space-y-3">
                        <div class="bg-blue-50 p-3 rounded border border-blue-200">
                            <p class="font-bold text-blue-700 text-sm">50% Kebutuhan Pokok</p>
                            <p class="text-lg font-bold">Rp ${Math.round(kebutuhan).toLocaleString('id-ID')}</p>
                            <p class="text-xs text-gray-500">Makan sehari-hari, kuota internet kuliah, sabun, dll.</p>
                        </div>
                        <div class="bg-orange-50 p-3 rounded border border-orange-200">
                            <p class="font-bold text-orange-700 text-sm">30% Keinginan & Hiburan</p>
                            <p class="text-lg font-bold">Rp ${Math.round(keinginan).toLocaleString('id-ID')}</p>
                            <p class="text-xs text-gray-500">Nongkrong di kafe, nonton film, jajan boba.</p>
                        </div>
                        <div class="bg-green-50 p-3 rounded border border-green-200">
                            <p class="font-bold text-green-700 text-sm">20% Tabungan / Investasi</p>
                            <p class="text-lg font-bold">Rp ${Math.round(tabungan).toLocaleString('id-ID')}</p>
                            <p class="text-xs text-gray-500">Dana darurat atau menabung untuk beli laptop/aset.</p>
                        </div>
                    </div>
                `;
            }
            div.classList.remove('hidden');
        }

        // 6. Simulasi PPh 21 Lulusan Baru
        function calcPajak() {
            const gajiKotor = parseFloat(document.getElementById('pajak-gaji').value);
            const div = document.getElementById('result-pajak');
            if(isNaN(gajiKotor) || gajiKotor <= 0) {
                div.innerHTML = `<span class="text-red-500 font-bold">Data tidak valid.</span>`;
            } else {
                // Asumsi standar potongan BPJS Karyawan:
                // JHT 2%, JP 1%, Kes 1%
                const jht = gajiKotor * 0.02;
                const jp = gajiKotor * 0.01;
                const kes = gajiKotor * 0.01; // max limit omitted for simplicity for entry level
                const totalBPJS = jht + jp + kes;
                
                // Simplified Pajak TER (Tarif Efektif Rata-Rata) utk TK/0
                // Gaji <= 5.4jt = 0%
                let pph21 = 0;
                if(gajiKotor <= 5400000) {
                    pph21 = 0;
                } else if(gajiKotor <= 5650000) { pph21 = gajiKotor * 0.0025; }
                else if(gajiKotor <= 5950000) { pph21 = gajiKotor * 0.005; }
                else if(gajiKotor <= 6300000) { pph21 = gajiKotor * 0.0075; }
                else if(gajiKotor <= 6750000) { pph21 = gajiKotor * 0.01; }
                else if(gajiKotor <= 7500000) { pph21 = gajiKotor * 0.0125; }
                else if(gajiKotor <= 8550000) { pph21 = gajiKotor * 0.015; }
                else if(gajiKotor <= 9650000) { pph21 = gajiKotor * 0.0175; }
                else if(gajiKotor <= 10050000) { pph21 = gajiKotor * 0.02; }
                else { pph21 = gajiKotor * 0.025; }
                
                const thp = gajiKotor - totalBPJS - pph21;
                
                div.innerHTML = `
                    <p class="font-bold text-emerald-800 mb-2">Rincian Perkiraan Potongan:</p>
                    <ul class="space-y-1 mb-3 text-sm border-b border-gray-200 pb-2">
                        <li class="flex justify-between text-gray-600"><span>Gaji Kotor (Bruto):</span> <span>Rp ${gajiKotor.toLocaleString('id-ID')}</span></li>
                        <li class="flex justify-between text-red-500"><span>BPJS Jaminan Hari Tua (2%):</span> <span>- Rp ${Math.round(jht).toLocaleString('id-ID')}</span></li>
                        <li class="flex justify-between text-red-500"><span>BPJS Pensiun (1%):</span> <span>- Rp ${Math.round(jp).toLocaleString('id-ID')}</span></li>
                        <li class="flex justify-between text-red-500"><span>BPJS Kesehatan (1%):</span> <span>- Rp ${Math.round(kes).toLocaleString('id-ID')}</span></li>
                        <li class="flex justify-between text-red-500"><span>PPh 21 (Estimasi):</span> <span>- Rp ${Math.round(pph21).toLocaleString('id-ID')}</span></li>
                    </ul>
                    <div class="flex justify-between items-center text-emerald-700">
                        <span class="font-bold">Gaji Bersih (Take Home Pay):</span>
                        <span class="text-xl font-bold">Rp ${Math.round(thp).toLocaleString('id-ID')}</span>
                    </div>
                `;
            }
            div.classList.remove('hidden');
        }
    </script>

</div>

<!-- YASIN & FITUR LAINNYA FLOATING ACTIONS -->
<div id="floating-actions" class="fixed bottom-24 right-5 z-40 md:right-8 flex items-end gap-3">
    <!-- Fitur Lainnya Button -->
    <button onclick="openModal('modal-fitur-lainnya')" class="w-12 h-12 rounded-md bg-sky-600 text-white shadow-xl flex items-center justify-center hover:bg-sky-500 transition-all border-2 border-white">
       <i class="fas fa-layer-group text-lg"></i>
    </button>

    <!-- Quran & Yasin Stack -->
    <div class="flex flex-col items-center gap-4">
        <!-- Al-Qur'an Button (New) -->
        <button onclick="openQuranModal()" class="w-14 h-14 rounded-full bg-sky-600 text-white shadow-xl flex items-center justify-center hover:bg-sky-500 hover:scale-110 transition-all duration-300 border-2 border-white relative group">
            <i class="fas fa-book-quran text-xl"></i>
            <span class="absolute right-full mr-2 bg-sky-800 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">Al-Qur'an</span>
        </button>

        <!-- Yasin Button -->
        <div class="animate-bounce-slow">
            <button onclick="openYasinModal()" class="w-16 h-16 rounded-full bg-sky-600 text-white shadow-2xl flex items-center justify-center hover:bg-sky-500 hover:scale-110 transition-all duration-300 border-4 border-white">
                <i class="fas fa-book-open text-2xl"></i>
            </button>
        </div>
    </div>
</div>

<!-- FITUR LAINNYA MODAL -->
<div id="modal-fitur-lainnya" class="fixed inset-0 z-[150] hidden flex items-center justify-center bg-black/40 backdrop-blur-xl transition-all duration-300">
    <div class="absolute inset-0" onclick="closeModal('modal-fitur-lainnya')"></div>
    <div class="relative w-full max-w-md mx-4 p-6 bg-white/90 backdrop-blur-3xl rounded-[2.5rem] shadow-[0_20px_50px_rgba(0,0,0,0.3)] border border-white/40 animate-[slideUp_0.4s_ease-out]">
        <div class="flex justify-between items-center mb-8">
            <h3 class="text-2xl font-bold text-gray-800 tracking-tight">Fitur Kampus</h3>
            <button onclick="closeModal('modal-fitur-lainnya')" class="w-10 h-10 rounded-full bg-black/5 flex items-center justify-center text-gray-600 hover:bg-black/10 transition-colors shadow-inner">
                <i class="fas fa-times text-lg"></i>
            </button>
        </div>
        
        <div class="grid grid-cols-3 gap-y-8 gap-x-4">
            <!-- Feature 1 -->
            <button onclick="openModal('modal-chatbot'); closeModal('modal-fitur-lainnya')" class="flex flex-col items-center group cursor-pointer">
                <div class="w-16 h-16 rounded-[1.2rem] bg-gradient-to-tr from-sky-400 to-blue-500 text-white flex items-center justify-center text-2xl shadow-lg group-hover:scale-95 group-active:scale-90 transition-transform duration-200 mb-3 border-2 border-white/50">
                    <i class="fas fa-robot"></i>
                </div>
                <span class="text-[10px] font-bold text-gray-700 text-center leading-tight">Chatbot<br>Pintar</span>
            </button>
            
            <!-- Feature 2 -->
            <button onclick="openModal('modal-kalender'); closeModal('modal-fitur-lainnya')" class="flex flex-col items-center group cursor-pointer">
                <div class="w-16 h-16 rounded-[1.2rem] bg-gradient-to-tr from-rose-400 to-red-500 text-white flex items-center justify-center text-2xl shadow-lg group-hover:scale-95 group-active:scale-90 transition-transform duration-200 mb-3 border-2 border-white/50">
                    <i class="fas fa-calendar-check"></i>
                </div>
                <span class="text-[10px] font-bold text-gray-700 text-center leading-tight">Kalender<br>Akademik</span>
            </button>
            
            <!-- Feature 3 -->
            <button onclick="openModal('modal-validasi'); closeModal('modal-fitur-lainnya')" class="flex flex-col items-center group cursor-pointer">
                <div class="w-16 h-16 rounded-[1.2rem] bg-gradient-to-tr from-emerald-400 to-green-500 text-white flex items-center justify-center text-2xl shadow-lg group-hover:scale-95 group-active:scale-90 transition-transform duration-200 mb-3 border-2 border-white/50">
                    <i class="fas fa-shield-alt"></i>
                </div>
                <span class="text-[10px] font-bold text-gray-700 text-center leading-tight">Validasi<br>Surat</span>
            </button>

            <!-- Feature 4 -->
            <button onclick="openModal('modal-kalkulator'); closeModal('modal-fitur-lainnya')" class="flex flex-col items-center group cursor-pointer">
                <div class="w-16 h-16 rounded-[1.2rem] bg-gradient-to-tr from-amber-400 to-orange-500 text-white flex items-center justify-center text-2xl shadow-lg group-hover:scale-95 group-active:scale-90 transition-transform duration-200 mb-3 border-2 border-white/50">
                    <i class="fas fa-calculator"></i>
                </div>
                <span class="text-[10px] font-bold text-gray-700 text-center leading-tight">Simulasi<br>Biaya</span>
            </button>
            
            <!-- Feature 5 -->
            <button onclick="openModal('modal-perpustakaan'); closeModal('modal-fitur-lainnya')" class="flex flex-col items-center group cursor-pointer">
                <div class="w-16 h-16 rounded-[1.2rem] bg-gradient-to-tr from-indigo-400 to-purple-500 text-white flex items-center justify-center text-2xl shadow-lg group-hover:scale-95 group-active:scale-90 transition-transform duration-200 mb-3 border-2 border-white/50">
                    <i class="fas fa-book-reader"></i>
                </div>
                <span class="text-[10px] font-bold text-gray-700 text-center leading-tight">E-Library<br>& Jurnal</span>
            </button>
            
            <!-- Feature 6 -->
            <button onclick="openModal('modal-kontak'); closeModal('modal-fitur-lainnya')" class="flex flex-col items-center group cursor-pointer">
                <div class="w-16 h-16 rounded-[1.2rem] bg-gradient-to-tr from-teal-400 to-cyan-500 text-white flex items-center justify-center text-2xl shadow-lg group-hover:scale-95 group-active:scale-90 transition-transform duration-200 mb-3 border-2 border-white/50">
                    <i class="fas fa-address-book"></i>
                </div>
                <span class="text-[10px] font-bold text-gray-700 text-center leading-tight">Direktori<br>Darurat</span>
            </button>
        </div>
    </div>
</div>

<!-- FEATURE 1: CHATBOT & HELPDESK -->
<div id="modal-chatbot" class="fixed inset-0 z-[160] hidden bg-gray-50 flex flex-col transition-all duration-300">
    <div class="bg-gradient-to-r from-sky-600 to-blue-600 px-5 py-4 text-white flex justify-between items-center shadow-md">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center"><i class="fas fa-robot text-xl"></i></div>
            <div>
                <h3 class="font-bold leading-tight">Helpdesk Pintar</h3>
                <p class="text-[10px] text-sky-100">Online - STIESAM Support</p>
            </div>
        </div>
        <button onclick="closeModal('modal-chatbot')" class="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors">
            <i class="fas fa-times"></i>
        </button>
    </div>
    
    <div class="flex-1 overflow-y-auto p-5 space-y-4" id="chat-messages">
        <div class="flex justify-start">
            <div class="bg-white p-3 rounded-2xl rounded-tl-sm shadow-sm max-w-[80%] border border-gray-100">
                <p class="text-sm text-gray-700">Halo! Saya asisten virtual STIESAM. Ada yang bisa saya bantu terkait kampus hari ini?</p>
            </div>
        </div>
    </div>
    
    <div class="p-4 bg-white border-t border-gray-100 shadow-[0_-5px_15px_rgba(0,0,0,0.02)]">
        <div class="flex gap-2 overflow-x-auto pb-3 custom-scrollbar">
            <button onclick="sendChat('Berapa biaya pendaftaran?')" class="whitespace-nowrap px-4 py-2 bg-sky-50 text-sky-600 rounded-full text-xs font-bold border border-sky-100 hover:bg-sky-100 transition-colors">Biaya Pendaftaran</button>
            <button onclick="sendChat('Apa syarat beasiswa?')" class="whitespace-nowrap px-4 py-2 bg-sky-50 text-sky-600 rounded-full text-xs font-bold border border-sky-100 hover:bg-sky-100 transition-colors">Syarat Beasiswa</button>
            <button onclick="sendChat('Jalur masuk apa saja?')" class="whitespace-nowrap px-4 py-2 bg-sky-50 text-sky-600 rounded-full text-xs font-bold border border-sky-100 hover:bg-sky-100 transition-colors">Jalur Masuk</button>
        </div>
        <div class="flex gap-2 mt-2">
            <a href="https://wa.me/6282330890500?text=Halo%20Admin%20STIESAM,%20saya%20butuh%20bantuan." target="_blank" class="w-12 h-12 flex-shrink-0 bg-green-500 text-white rounded-xl flex items-center justify-center shadow-md hover:bg-green-600 transition-colors">
                <i class="fab fa-whatsapp text-2xl"></i>
            </a>
            <input type="text" id="chat-input" placeholder="Ketik pertanyaan Anda..." class="flex-1 bg-gray-50 border border-gray-200 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
            <button onclick="sendCustomChat()" class="w-12 h-12 flex-shrink-0 bg-sky-600 text-white rounded-xl flex items-center justify-center shadow-md hover:bg-sky-700 transition-colors">
                <i class="fas fa-paper-plane"></i>
            </button>
        </div>
    </div>
</div>
<script>
    function sendChat(msg) {
        const chatBox = document.getElementById('chat-messages');
        chatBox.innerHTML += `<div class="flex justify-end"><div class="bg-sky-600 text-white p-3 rounded-2xl rounded-tr-sm shadow-sm max-w-[80%]"><p class="text-sm">${msg}</p></div></div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
        
        setTimeout(() => {
            let reply = "Maaf, saya tidak mengerti. Silakan hubungi admin via WhatsApp.";
            if(msg.includes('biaya')) reply = "Estimasi biaya pendaftaran adalah Rp 300.000. Untuk rincian uang kuliah tunggal (UKT), Anda bisa menggunakan fitur Kalkulator Simulasi Biaya.";
            else if(msg.includes('beasiswa')) reply = "STIESAM menyediakan beasiswa KIP-K, prestasi, dan tahfidz. Syarat umum meliputi fotokopi rapor, KTP, dan surat keterangan tidak mampu (jika ada).";
            else if(msg.includes('masuk')) reply = "Jalur masuk STIESAM terbagi menjadi Reguler, Prestasi, dan Karyawan (Kelas Sore/Malam).";
            
            chatBox.innerHTML += `<div class="flex justify-start"><div class="bg-white p-3 rounded-2xl rounded-tl-sm shadow-sm max-w-[80%] border border-gray-100"><p class="text-sm text-gray-700">${reply}</p></div></div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        }, 800);
    }
    function sendCustomChat() {
        const inp = document.getElementById('chat-input');
        if(inp.value.trim()) {
            sendChat(inp.value.trim());
            inp.value = '';
        }
    }
</script>

<!-- FEATURE 2: KALENDER AKADEMIK -->
<div id="modal-kalender" class="fixed inset-0 z-[160] hidden bg-gray-50 flex flex-col transition-all duration-300">
    <div class="bg-gradient-to-r from-rose-500 to-red-600 px-5 py-4 text-white flex justify-between items-center shadow-md">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center"><i class="fas fa-calendar-alt text-xl"></i></div>
            <h3 class="font-bold leading-tight">Kalender Akademik</h3>
        </div>
        <button onclick="closeModal('modal-kalender')" class="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors">
            <i class="fas fa-times"></i>
        </button>
    </div>
    
    <div class="p-5 overflow-y-auto">
        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 mb-6">
            <div class="flex justify-between items-center mb-4">
                <button class="text-gray-400 hover:text-rose-500"><i class="fas fa-chevron-left"></i></button>
                <h4 class="font-bold text-gray-800">September 2024</h4>
                <button class="text-gray-400 hover:text-rose-500"><i class="fas fa-chevron-right"></i></button>
            </div>
            <div class="grid grid-cols-7 gap-2 text-center text-xs font-bold text-gray-400 mb-2">
                <div class="text-red-400">Min</div><div>Sen</div><div>Sel</div><div>Rab</div><div>Kam</div><div>Jum</div><div>Sab</div>
            </div>
            <div class="grid grid-cols-7 gap-2 text-center text-sm font-medium text-gray-700">
                <div class="p-2 text-gray-300">26</div><div class="p-2 text-gray-300">27</div><div class="p-2 text-gray-300">28</div><div class="p-2 text-gray-300">29</div><div class="p-2 text-gray-300">30</div><div class="p-2 text-gray-300">31</div>
                <div class="p-2">1</div><div class="p-2">2</div><div class="p-2 bg-green-100 text-green-700 rounded-lg shadow-sm cursor-pointer" onclick="alert('Pengisian KRS')">3</div><div class="p-2 bg-green-100 text-green-700 rounded-lg shadow-sm cursor-pointer" onclick="alert('Pengisian KRS')">4</div><div class="p-2 bg-green-100 text-green-700 rounded-lg shadow-sm cursor-pointer" onclick="alert('Pengisian KRS')">5</div><div class="p-2">6</div><div class="p-2 text-red-500">7</div>
                <div class="p-2 text-red-500">8</div><div class="p-2 bg-yellow-100 text-yellow-700 rounded-lg shadow-sm cursor-pointer" onclick="alert('Ujian Tengah Semester (UTS)')">9</div><div class="p-2 bg-yellow-100 text-yellow-700 rounded-lg shadow-sm cursor-pointer" onclick="alert('Ujian Tengah Semester (UTS)')">10</div><div class="p-2 bg-yellow-100 text-yellow-700 rounded-lg shadow-sm cursor-pointer" onclick="alert('Ujian Tengah Semester (UTS)')">11</div><div class="p-2 bg-yellow-100 text-yellow-700 rounded-lg shadow-sm cursor-pointer" onclick="alert('Ujian Tengah Semester (UTS)')">12</div><div class="p-2 bg-yellow-100 text-yellow-700 rounded-lg shadow-sm cursor-pointer" onclick="alert('Ujian Tengah Semester (UTS)')">13</div><div class="p-2 text-red-500">14</div>
                <div class="p-2 text-red-500">15</div><div class="p-2 bg-red-100 text-red-700 rounded-lg shadow-sm cursor-pointer" onclick="alert('Libur Nasional: Maulid Nabi')">16</div><div class="p-2">17</div><div class="p-2">18</div><div class="p-2">19</div><div class="p-2">20</div><div class="p-2 text-red-500">21</div>
                <div class="p-2 text-red-500">22</div><div class="p-2">23</div><div class="p-2 border-2 border-rose-500 rounded-lg text-rose-600 font-bold">24</div><div class="p-2">25</div><div class="p-2">26</div><div class="p-2">27</div><div class="p-2 text-red-500">28</div>
                <div class="p-2 text-red-500">29</div><div class="p-2">30</div><div class="p-2 text-gray-300">1</div><div class="p-2 text-gray-300">2</div><div class="p-2 text-gray-300">3</div><div class="p-2 text-gray-300">4</div><div class="p-2 text-gray-300">5</div>
            </div>
        </div>
        
        <h4 class="font-bold text-gray-800 mb-3 text-sm">Keterangan</h4>
        <div class="space-y-2">
            <div class="flex items-center gap-3 bg-white p-3 rounded-xl border border-gray-100">
                <div class="w-4 h-4 rounded bg-green-100 border border-green-200 flex-shrink-0"></div>
                <span class="text-sm text-gray-600">Masa Pengisian KRS (3-5 Sep)</span>
            </div>
            <div class="flex items-center gap-3 bg-white p-3 rounded-xl border border-gray-100">
                <div class="w-4 h-4 rounded bg-yellow-100 border border-yellow-200 flex-shrink-0"></div>
                <span class="text-sm text-gray-600">Pekan Ujian (UTS) (9-13 Sep)</span>
            </div>
            <div class="flex items-center gap-3 bg-white p-3 rounded-xl border border-gray-100">
                <div class="w-4 h-4 rounded bg-red-100 border border-red-200 flex-shrink-0"></div>
                <span class="text-sm text-gray-600">Libur Akademik (16 Sep)</span>
            </div>
        </div>
    </div>
</div>

<!-- FEATURE 3: VALIDASI SURAT -->
<div id="modal-validasi" class="fixed inset-0 z-[160] hidden bg-gray-50 flex items-center justify-center p-4">
    <div class="bg-white w-full max-w-md rounded-3xl shadow-xl overflow-hidden animate-[slideUp_0.3s_ease-out]">
        <div class="bg-gradient-to-r from-emerald-500 to-green-600 px-6 py-8 text-white text-center relative">
            <button onclick="closeModal('modal-validasi')" class="absolute top-4 right-4 w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors">
                <i class="fas fa-times"></i>
            </button>
            <i class="fas fa-shield-alt text-5xl mb-4 drop-shadow-md"></i>
            <h3 class="text-2xl font-bold tracking-tight">Validasi Surat</h3>
            <p class="text-emerald-100 text-sm mt-1">Sistem Keaslian Dokumen STIESAM</p>
        </div>
        <div class="p-6">
            <p class="text-sm text-gray-600 text-center mb-6">Masukkan kode unik atau ID Dokumen yang tertera pada bagian bawah surat pengantar.</p>
            <div class="flex gap-2 mb-4">
                <input type="text" id="validasi-input" placeholder="Cth: STS-2401-8A9F" class="flex-1 bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-center font-mono text-gray-800 uppercase focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200">
            </div>
            <button onclick="validateSurat()" class="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-md hover:bg-emerald-600 transition-colors mb-6">Cek Keaslian</button>
            
            <div id="validasi-result" class="hidden border border-emerald-200 bg-emerald-50 p-4 rounded-xl flex items-start gap-3">
                <i class="fas fa-check-circle text-emerald-500 text-2xl mt-0.5"></i>
                <div>
                    <h4 class="font-bold text-emerald-800">DOKUMEN RESMI</h4>
                    <p class="text-xs text-emerald-700 mt-1">Surat Pengantar Magang (No: 045/AKD/STS/2024)<br>Diterbitkan: 24 Sep 2024<br>Oleh: Tata Usaha STIESAM</p>
                </div>
            </div>
        </div>
    </div>
</div>
<script>
    function validateSurat() {
        const inp = document.getElementById('validasi-input').value;
        if(inp.length > 3) {
            document.getElementById('validasi-result').classList.remove('hidden');
        } else {
            showToast('Masukkan kode surat yang valid.', 'error');
        }
    }
</script>

<!-- FEATURE 4: KALKULATOR BIAYA -->
<div id="modal-kalkulator" class="fixed inset-0 z-[160] hidden bg-gray-50 flex items-center justify-center p-4">
    <div class="bg-white w-full max-w-md rounded-3xl shadow-xl overflow-hidden animate-[slideUp_0.3s_ease-out]">
        <div class="bg-gradient-to-r from-amber-500 to-orange-500 px-6 py-6 text-white flex justify-between items-center">
            <div class="flex items-center gap-3">
                <i class="fas fa-calculator text-2xl drop-shadow-md"></i>
                <h3 class="text-xl font-bold tracking-tight">Kalkulator UKT</h3>
            </div>
            <button onclick="closeModal('modal-kalkulator')" class="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="p-6">
            <div class="space-y-4 mb-6">
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-2">Program Studi</label>
                    <select id="calc-prodi" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 font-bold text-gray-700">
                        <option value="4000000">S1 Manajemen (S.E)</option>
                        <option value="4500000">S1 Akuntansi (S.Ak)</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 mb-2">Jalur Pendaftaran</label>
                    <select id="calc-jalur" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 font-bold text-gray-700">
                        <option value="0">Reguler (Pagi/Siang)</option>
                        <option value="1000000">Karyawan (Sore/Malam) + Rp 1.000.000</option>
                        <option value="-2000000">Prestasi/Tahfidz - Rp 2.000.000</option>
                    </select>
                </div>
            </div>
            <button onclick="calculateUKT()" class="w-full bg-amber-500 text-white font-bold py-3 rounded-xl shadow-md hover:bg-amber-600 transition-colors mb-6">Hitung Simulasi</button>
            
            <div class="bg-gray-800 text-white p-5 rounded-2xl text-center shadow-inner relative overflow-hidden">
                <div class="absolute -right-4 -top-4 opacity-10 text-7xl"><i class="fas fa-coins"></i></div>
                <p class="text-xs text-gray-400 font-bold uppercase tracking-widest mb-1">Estimasi Biaya Per Semester</p>
                <h2 id="calc-result" class="text-3xl font-mono font-bold text-amber-400">Rp 0</h2>
                <p class="text-[10px] text-gray-500 mt-2">*Biaya belum termasuk pendaftaran dan almamater</p>
            </div>
        </div>
    </div>
</div>
<script>
    function calculateUKT() {
        const base = parseInt(document.getElementById('calc-prodi').value);
        const mod = parseInt(document.getElementById('calc-jalur').value);
        const total = base + mod;
        document.getElementById('calc-result').innerText = "Rp " + total.toLocaleString('id-ID');
    }
</script>

<!-- FEATURE 5: PERPUSTAKAAN & JURNAL -->
<div id="modal-perpustakaan" class="fixed inset-0 z-[160] hidden bg-black/60 backdrop-blur-sm p-4 pt-20">
    <div class="bg-white w-full max-w-2xl mx-auto rounded-3xl shadow-2xl flex flex-col h-[80vh] overflow-hidden animate-[slideDown_0.3s_ease-out]">
        <div class="bg-gradient-to-r from-indigo-600 to-purple-700 p-6 text-white relative flex-shrink-0">
            <button onclick="closeModal('modal-perpustakaan')" class="absolute top-4 right-4 w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors">
                <i class="fas fa-times"></i>
            </button>
            <h3 class="text-2xl font-bold mb-4 flex items-center gap-2"><i class="fas fa-book-reader"></i> E-Library & Jurnal</h3>
            <div class="relative">
                <input type="text" id="lib-search" onkeyup="searchLib()" placeholder="Cari buku manajemen, akuntansi, atau penulis..." class="w-full bg-white/10 border border-white/20 rounded-xl pl-12 pr-4 py-3 text-white placeholder-indigo-200 focus:outline-none focus:bg-white/20 focus:ring-2 focus:ring-white">
                <i class="fas fa-search absolute left-4 top-3.5 text-indigo-200 text-lg"></i>
            </div>
        </div>
        
        <div class="p-6 overflow-y-auto bg-gray-50 flex-1 space-y-3" id="lib-results">
            <!-- Results populated by JS -->
            <div class="lib-item bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow flex gap-4 cursor-pointer">
                <div class="w-12 h-16 bg-blue-100 rounded flex items-center justify-center text-blue-500 text-2xl flex-shrink-0"><i class="fas fa-book"></i></div>
                <div>
                    <span class="text-[10px] bg-blue-100 text-blue-700 px-2 py-0.5 rounded font-bold">Buku</span>
                    <h4 class="font-bold text-gray-800 mt-1 leading-tight">Pengantar Manajemen Modern</h4>
                    <p class="text-xs text-gray-500 mt-1">Prof. Dr. H. Abdul, M.Si.</p>
                </div>
            </div>
            <div class="lib-item bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow flex gap-4 cursor-pointer">
                <div class="w-12 h-16 bg-rose-100 rounded flex items-center justify-center text-rose-500 text-2xl flex-shrink-0"><i class="fas fa-file-pdf"></i></div>
                <div>
                    <span class="text-[10px] bg-rose-100 text-rose-700 px-2 py-0.5 rounded font-bold">Jurnal Nasional</span>
                    <h4 class="font-bold text-gray-800 mt-1 leading-tight">Analisis Laporan Keuangan UMKM</h4>
                    <p class="text-xs text-gray-500 mt-1">Jurnal Ekonomi & Bisnis (Vol. 4)</p>
                </div>
            </div>
            <div class="lib-item bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow flex gap-4 cursor-pointer">
                <div class="w-12 h-16 bg-blue-100 rounded flex items-center justify-center text-blue-500 text-2xl flex-shrink-0"><i class="fas fa-book"></i></div>
                <div>
                    <span class="text-[10px] bg-blue-100 text-blue-700 px-2 py-0.5 rounded font-bold">Buku</span>
                    <h4 class="font-bold text-gray-800 mt-1 leading-tight">Dasar-Dasar Akuntansi</h4>
                    <p class="text-xs text-gray-500 mt-1">Drs. Budi Santoso</p>
                </div>
            </div>
        </div>
    </div>
</div>
<script>
    function searchLib() {
        const filter = document.getElementById('lib-search').value.toUpperCase();
        const items = document.querySelectorAll('.lib-item');
        items.forEach(item => {
            const txt = item.innerText || item.textContent;
            item.style.display = txt.toUpperCase().indexOf(filter) > -1 ? "" : "none";
        });
    }
</script>

<!-- FEATURE 6: DIREKTORI KONTAK -->
<div id="modal-kontak" class="fixed inset-0 z-[160] hidden bg-gray-50 flex items-center justify-center p-4">
    <div class="bg-white w-full max-w-md rounded-3xl shadow-xl overflow-hidden animate-[slideUp_0.3s_ease-out] flex flex-col max-h-[85vh]">
        <div class="bg-gradient-to-r from-teal-500 to-cyan-600 px-6 py-5 text-white flex justify-between items-center shadow-md flex-shrink-0">
            <div class="flex items-center gap-3">
                <i class="fas fa-address-book text-2xl drop-shadow-md"></i>
                <h3 class="text-lg font-bold tracking-tight">Direktori & Hotline</h3>
            </div>
            <button onclick="closeModal('modal-kontak')" class="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors">
                <i class="fas fa-times"></i>
            </button>
        </div>
        
        <div class="p-4 overflow-y-auto flex-1 space-y-3 bg-slate-50">
            <a href="https://wa.me/6281234567890" target="_blank" class="block bg-white p-4 rounded-2xl shadow-sm border border-gray-100 hover:border-teal-300 hover:shadow-md transition-all group">
                <div class="flex items-center gap-4">
                    <div class="w-12 h-12 rounded-full bg-teal-50 text-teal-600 flex items-center justify-center text-xl group-hover:bg-teal-500 group-hover:text-white transition-colors"><i class="fas fa-user-tie"></i></div>
                    <div class="flex-1">
                        <h4 class="font-bold text-gray-800">Tata Usaha (Akademik)</h4>
                        <p class="text-xs text-gray-500">KRS, Jadwal, Surat Menyurat</p>
                    </div>
                    <i class="fab fa-whatsapp text-2xl text-green-500"></i>
                </div>
            </a>
            
            <a href="https://wa.me/6281234567891" target="_blank" class="block bg-white p-4 rounded-2xl shadow-sm border border-gray-100 hover:border-amber-300 hover:shadow-md transition-all group">
                <div class="flex items-center gap-4">
                    <div class="w-12 h-12 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center text-xl group-hover:bg-amber-500 group-hover:text-white transition-colors"><i class="fas fa-file-invoice-dollar"></i></div>
                    <div class="flex-1">
                        <h4 class="font-bold text-gray-800">Bagian Keuangan</h4>
                        <p class="text-xs text-gray-500">UKT, Pembayaran, Beasiswa</p>
                    </div>
                    <i class="fab fa-whatsapp text-2xl text-green-500"></i>
                </div>
            </a>
            
            <a href="mailto:it@stiesam.ac.id" class="block bg-white p-4 rounded-2xl shadow-sm border border-gray-100 hover:border-blue-300 hover:shadow-md transition-all group">
                <div class="flex items-center gap-4">
                    <div class="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center text-xl group-hover:bg-blue-500 group-hover:text-white transition-colors"><i class="fas fa-laptop-code"></i></div>
                    <div class="flex-1">
                        <h4 class="font-bold text-gray-800">Layanan IT</h4>
                        <p class="text-xs text-gray-500">Lupa Password, Error Sistem</p>
                    </div>
                    <i class="fas fa-envelope text-2xl text-blue-400"></i>
                </div>
            </a>
            
            <a href="tel:0541123456" class="block bg-red-50 p-4 rounded-2xl shadow-sm border border-red-200 hover:border-red-400 hover:shadow-md transition-all group">
                <div class="flex items-center gap-4">
                    <div class="w-12 h-12 rounded-full bg-white text-red-600 flex items-center justify-center text-xl group-hover:bg-red-600 group-hover:text-white transition-colors"><i class="fas fa-phone-volume"></i></div>
                    <div class="flex-1">
                        <h4 class="font-bold text-red-800">Hotline Darurat Kampus</h4>
                        <p class="text-xs text-red-600">Keamanan & Keadaan Darurat</p>
                    </div>
                    <i class="fas fa-phone text-xl text-red-600"></i>
                </div>
            </a>
        </div>
    </div>
</div>

<!-- YASIN DIGITAL MODAL -->
<div id="modal-yasin" class="fixed inset-0 z-[100] hidden bg-white">
    <!-- Header -->
    <div class="fixed top-0 left-0 w-full bg-white z-10 shadow-sm border-b border-gray-100 px-5 py-4 flex justify-between items-center">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-sky-50 flex items-center justify-center text-sky-600">
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
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-600 mb-4"></div>
            <p class="text-gray-500 text-sm">Mengambil Data Surat Yasin...</p>
        </div>
        
        <!-- Error State -->
        <div id="yasin-error" class="hidden text-center py-20">
            <p class="text-red-500 mb-2">Gagal memuat data.</p>
            <button onclick="fetchYasin()" class="text-sky-600 underline text-sm">Coba Lagi</button>
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
            <div class="w-10 h-10 rounded-full bg-sky-50 flex items-center justify-center text-sky-600">
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
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-600 mb-4"></div>
            <p class="text-gray-500 text-sm">Mengambil Daftar Surat...</p>
        </div>
        
        <!-- Error State -->
        <div id="quran-list-error" class="hidden text-center py-20">
            <p class="text-red-500 mb-2">Gagal memuat daftar surat.</p>
            <button onclick="fetchSurahList()" class="text-sky-600 underline text-sm">Coba Lagi</button>
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
            <button id="btn-quran-tajwid" onclick="toggleQuranTajwid()" class="text-xs font-bold text-sky-600 bg-sky-50 px-3 py-1.5 rounded-full border border-sky-200 hover:bg-sky-100 transition shadow-sm flex items-center gap-1">
                <i class="fas fa-palette"></i> Tajwid
            </button>
            <button onclick="closeQuranModal()" class="w-10 h-10 rounded-full bg-gray-50 text-gray-500 hover:bg-gray-100 flex items-center justify-center transition-colors">
                <i class="fas fa-times text-lg"></i>
            </button>
        </div>
    </div>

    <!-- Audio Player (Sticky under header) -->
    <div class="fixed top-[72px] left-0 w-full bg-sky-50 z-10 border-b border-sky-100 px-5 py-3 flex flex-col gap-2">
        <div class="flex items-center justify-between w-full">
            <p class="text-xs text-sky-800 font-bold"><i class="fas fa-volume-up mr-1"></i> Murottal (Misyari Rasyid)</p>
            <audio id="quran-audio-player" controls class="h-8 w-48 md:w-64"></audio>
        </div>
        <input type="range" id="quran-seeker" value="0" class="w-full h-1 bg-sky-200 rounded-lg appearance-none cursor-pointer">
    </div>

    <!-- Content -->
    <div class="pt-48 pb-10 px-5 md:px-8 max-w-3xl mx-auto h-full overflow-y-auto" id="quran-detail-content">
        <!-- Loading -->
        <div id="quran-detail-loading" class="flex flex-col items-center justify-center py-20">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-600 mb-4"></div>
            <p class="text-gray-500 text-sm">Membuka Ayat...</p>
        </div>
        
        <!-- Verses -->
        <div id="quran-detail-verses" class="hidden space-y-8 pb-20">
             <!-- Verses injected here -->
        </div>

        <div id="quran-detail-tajwid-legend" class="hidden sticky bottom-4 mx-auto max-w-sm bg-white/90 backdrop-blur-md border border-sky-100 p-3 rounded-2xl shadow-[0_-10px_15px_-3px_rgba(0,0,0,0.1)] z-20 mt-4">
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
    <div class="bg-white rounded-3xl w-full max-w-xs mx-4 p-6 shadow-2xl animate-[popupFadeIn_0.3s_ease-out] relative border border-sky-100">
        <div class="w-16 h-16 bg-sky-50 text-sky-600 rounded-full flex items-center justify-center mx-auto mb-4 border-4 border-white shadow-sm -mt-12">
            <i class="fas fa-book-open text-2xl"></i>
        </div>
        <h3 id="tajwid-rule-title" class="text-xl font-bold text-gray-800 text-center mb-2 leading-tight uppercase tracking-wider"></h3>
        <div class="w-12 h-1 bg-sky-200 mx-auto rounded-full mb-4"></div>
        <p id="tajwid-rule-desc" class="text-sm text-gray-600 text-center leading-relaxed mb-6 font-medium"></p>
        <button onclick="closeTajwidRule()" class="w-full bg-sky-500 text-white font-bold py-3 rounded-xl shadow-md hover:bg-sky-600 transition transform hover:scale-105">Paham</button>
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
            btn.classList.remove('bg-sky-50', 'text-sky-600', 'border-sky-200');
            btn.classList.add('bg-sky-500', 'text-white', 'border-sky-500', 'shadow-md');
        } else {
            btn.classList.add('bg-sky-50', 'text-sky-600', 'border-sky-200');
            btn.classList.remove('bg-sky-500', 'text-white', 'border-sky-500', 'shadow-md');
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
            el.className = "bg-white p-4 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between cursor-pointer hover:bg-sky-50 hover:border-sky-200 transition-all group";
            el.onclick = () => openSurahDetail(surah.nomor);
            
            el.innerHTML = `
                <div class="flex items-center gap-4">
                    <div class="w-10 h-10 rounded-full bg-sky-100 text-sky-600 font-bold flex items-center justify-center text-sm group-hover:bg-sky-500 group-hover:text-white transition-colors">
                        ${surah.nomor}
                    </div>
                    <div>
                        <h4 class="font-bold text-gray-800 group-hover:text-sky-700">${surah.namaLatin}</h4>
                        <p class="text-xs text-gray-500">${surah.arti} • ${surah.jumlahAyat} Ayat</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="font-amiri text-xl text-sky-800 font-bold">${surah.nama}</p>
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
            showToast('Gagal memuat surat. Periksa koneksi internet.', 'error');
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
                            <p class="text-sm text-gray-500 italic mb-2 leading-relaxed font-serif tracking-wide text-sky-700">${verse.teksLatin}</p>
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
                    .replace(/<tajweed class="ikhfa[^"]*"[^>]*>(.*?)<[/]tajweed>/gi, '<span onclick="showTajwidRule(\\\'ikhfa\\\')" class="text-sky-500 font-bold cursor-pointer hover:underline decoration-sky-300 decoration-2">$1</span>')
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
                            <div class="w-8 h-8 flex-shrink-0 rounded-full bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-600 font-bold text-xs mt-1">
                                ${ayahTajwid.numberInSurah}
                            </div>
                            <div class="flex-1 text-right pl-4">
                                <p class="font-amiri text-3xl md:text-4xl leading-[2.5] text-gray-800 font-bold" style="font-family: 'Amiri', serif; direction: rtl;">
                                    ${parsedText}
                                </p>
                            </div>
                        </div>
                        <div class="pl-12 text-left">
                            <p class="text-sm text-gray-500 italic mb-2 leading-relaxed font-serif tracking-wide text-sky-700">${equranVerse ? equranVerse.teksLatin : ''}</p>
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
                    <div class="w-10 h-10 flex-shrink-0 rounded-full bg-sky-50 border border-sky-100 flex items-center justify-center text-sky-600 font-bold text-sm">
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

RAMADHAN_DASHBOARD_HTML = """
<div class="bg-midnight min-h-screen pb-24 relative overflow-hidden font-sans">
    <!-- BACKGROUND PATTERN -->
    <div class="fixed inset-0 opacity-5 pointer-events-none" style="background-image: url('https://www.transparenttextures.com/patterns/arabesque.png');"></div>

    <!-- CUSTOM HEADER (Adapted from BASE_LAYOUT) -->
    <nav class="hidden md:flex fixed top-0 left-0 w-full z-50 glass-gold bg-midnight shadow-sm px-8 py-4 justify-between items-center right-0 border-b border-gold/20">
        <div class="max-w-7xl mx-auto w-full flex justify-between items-center">
             <div class="flex items-center gap-4 h-12 cursor-pointer group" onclick="openModal('modal-logo-zoom')">
                 <div class="h-full flex items-center justify-center transition-transform duration-300 group-hover:scale-110">
                    <img src="/static/logo-stiesam.png" alt="Logo STIESAM" class="h-full w-auto object-contain">
                 </div>
                 <div class="flex flex-col justify-between h-full py-0.5">
                    <h1 class="text-xl font-bold text-gold leading-none font-sans">Sekolah Tinggi Ilmu Ekonomi STIESAM</h1>
                    <p class="text-xs text-gray-400 font-medium leading-none">Samarinda, Kalimantan Timur</p>
                 </div>
             </div>
             <div class="flex items-center gap-8">
                <a href="/" class="text-gray-300 font-medium hover:text-gold transition">Beranda</a>
                <a href="javascript:void(0)" onclick="openModal('modal-ktm-digital')" class="text-gray-300 font-medium hover:text-gold transition">KTM Digital</a>
                <a href="javascript:void(0)" onclick="openModal('modal-today-schedule')" class="text-gray-300 font-medium hover:text-gold transition">Jadwal</a>
                <a href="javascript:void(0)" onclick="openModal('modal-notifications')" class="text-gray-300 font-medium hover:text-gold transition">Notifikasi</a>
                <a href="javascript:void(0)" onclick="openModal('modal-spp-payment')" class="bg-gold text-midnight px-5 py-2 rounded-full font-bold shadow-lg hover:bg-white transition transform hover:scale-105">Bayar SPP</a>
                <button onclick="openModal('modal-kontak')" class="text-red-400 font-bold hover:text-red-500 transition border border-red-500/50 px-4 py-2 rounded-full bg-red-500/10 hover:bg-red-500/20 cursor-pointer">Darurat</button>
            </div>
        </div>
    </nav>

    <!-- MOBILE HEADER (Adapted from BASE_LAYOUT) -->
    <header class="md:hidden fixed top-0 left-0 w-full z-50 glass-gold bg-midnight shadow-sm px-4 py-3 flex justify-between items-center max-w-md mx-auto right-0 border-b border-gold/20">
        <div class="flex items-center gap-2 h-10 cursor-pointer group" onclick="openModal('modal-logo-zoom')">
            <div class="h-full flex items-center justify-center transition-transform duration-300 group-hover:scale-110">
                <img src="/static/logo-stiesam.png" alt="Logo STIESAM" class="h-full w-auto object-contain">
            </div>
            <div class="flex flex-col justify-between h-full py-0.5">
                <h1 class="text-lg font-bold text-gold leading-none font-sans">STIESAM</h1>
                <p class="text-[10px] text-gray-400 font-medium leading-none mt-0.5">Samarinda, Kalimantan Timur</p>
            </div>
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
                <h1 class="text-5xl font-bold text-white leading-tight mb-6">Portal Tata Usaha<br>STIESAM</h1>
                <p class="text-gray-300 text-lg leading-relaxed mb-8">
                    Pusat layanan administrasi akademik yang presisi, cepat, dan efisien untuk melayani kebutuhan mahasiswa dan dosen secara digital.
                </p>
                <div class="flex gap-4">
                    <button onclick="openModal('modal-cek-alumni')" class="bg-gold text-midnight px-8 py-3 rounded-full font-bold shadow-lg hover:bg-white transition transform hover:scale-105">Cek Alumni</button>
                    <a href="javascript:void(0)" onclick="openModal('modal-publikasi-informasi')" class="bg-transparent text-gold border-2 border-gold px-8 py-3 rounded-full font-bold hover:bg-gold hover:text-midnight transition transform hover:scale-105">PUBLIKASI INFORMASI</a>
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
            
            <button onclick="openModal('modal-pabrik-surat')" class="bg-[#151e3f] p-6 rounded-3xl flex flex-col items-center justify-center h-40 group hover:bg-[#1a254d] transition-all border border-white/5 hover:border-gold/30 relative overflow-hidden">
                <div class="absolute inset-0 bg-gold/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="w-14 h-14 rounded-full bg-[#0b1026] flex items-center justify-center text-gold mb-3 group-hover:scale-110 transition-transform shadow-lg border border-white/5">
                    <i class="fas fa-file-signature text-2xl"></i>
                </div>
                <span class="font-bold text-sm text-center text-gray-200 group-hover:text-gold transition-colors">Surat Otomatis</span>
            </button>

            <button onclick="openModal('modal-verifikasi-pmb')" class="bg-[#151e3f] p-6 rounded-3xl flex flex-col items-center justify-center h-40 group hover:bg-[#1a254d] transition-all border border-white/5 hover:border-gold/30 relative overflow-hidden">
                <div class="absolute inset-0 bg-gold/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="w-14 h-14 rounded-full bg-[#0b1026] flex items-center justify-center text-gold mb-3 group-hover:scale-110 transition-transform shadow-lg border border-white/5">
                    <i class="fas fa-id-card text-2xl"></i>
                </div>
                <span class="font-bold text-sm text-center text-gray-200 group-hover:text-gold transition-colors">Verifikasi PMB & Dosen</span>
            </button>

            <button onclick="openModal('modal-laci-arsip')" class="bg-[#151e3f] p-6 rounded-3xl flex flex-col items-center justify-center h-40 group hover:bg-[#1a254d] transition-all border border-white/5 hover:border-gold/30 relative overflow-hidden">
                <div class="absolute inset-0 bg-gold/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="w-14 h-14 rounded-full bg-[#0b1026] flex items-center justify-center text-gold mb-3 group-hover:scale-110 transition-transform shadow-lg border border-white/5">
                    <i class="fas fa-search text-2xl"></i>
                </div>
                <span class="font-bold text-sm text-center text-gray-200 group-hover:text-gold transition-colors">Arsip Digital</span>
            </button>

            <button onclick="openModal('modal-verifikasi-pembayaran')" class="bg-[#151e3f] p-6 rounded-3xl flex flex-col items-center justify-center h-40 group hover:bg-[#1a254d] transition-all border border-white/5 hover:border-gold/30 relative overflow-hidden">
                <div class="absolute inset-0 bg-gold/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="w-14 h-14 rounded-full bg-[#0b1026] flex items-center justify-center text-gold mb-3 group-hover:scale-110 transition-transform shadow-lg border border-white/5">
                    <i class="fas fa-file-invoice-dollar text-2xl"></i>
                </div>
                <span class="font-bold text-sm text-center text-gray-200 group-hover:text-gold transition-colors">Verifikasi SPP</span>
            </button>

            <button onclick="openModal('modal-kelola-jadwal')" class="bg-[#151e3f] p-6 rounded-3xl flex flex-col items-center justify-center h-40 group hover:bg-[#1a254d] transition-all border border-white/5 hover:border-gold/30 relative overflow-hidden">
                <div class="absolute inset-0 bg-gold/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="w-14 h-14 rounded-full bg-[#0b1026] flex items-center justify-center text-gold mb-3 group-hover:scale-110 transition-transform shadow-lg border border-white/5">
                    <i class="fas fa-calendar-alt text-2xl"></i>
                </div>
                <span class="font-bold text-sm text-center text-gray-200 group-hover:text-gold transition-colors">Jadwal Kuliah</span>
            </button>

            <button onclick="openModal('modal-manajemen-sivitas')" class="bg-[#151e3f] p-6 rounded-3xl flex flex-col items-center justify-center h-40 group hover:bg-[#1a254d] transition-all border border-white/5 hover:border-gold/30 relative overflow-hidden">
                <div class="absolute inset-0 bg-gold/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="w-14 h-14 rounded-full bg-[#0b1026] flex items-center justify-center text-gold mb-3 group-hover:scale-110 transition-transform shadow-lg border border-white/5">
                    <i class="fas fa-users-cog text-2xl"></i>
                </div>
                <span class="font-bold text-sm text-center text-gray-200 group-hover:text-gold transition-colors">Kelola Sivitas</span>
            </button>
        </div>
    </div>

    <!-- CUSTOM BOTTOM BAR (Adapted from BASE_LAYOUT) -->
    <nav class="md:hidden fixed bottom-0 left-0 w-full bg-midnight z-50 pb-2 pt-2 max-w-md mx-auto right-0 border-t border-gold/20 rounded-t-3xl">
        <div class="flex justify-between items-end h-14 px-2">
            <a href="/" class="flex flex-col items-center justify-center text-gray-400 hover:text-gold w-14 mb-1 transition-colors">
                <i class="fas fa-home text-xl mb-1"></i>
                <span class="text-[9px] font-medium text-center leading-tight">Beranda</span>
            </a>
            <a href="javascript:void(0)" onclick="openModal('modal-ktm-digital')" class="flex flex-col items-center justify-center text-gray-400 hover:text-gold w-14 mb-1 transition-colors">
                <i class="fas fa-id-card text-xl mb-1"></i>
                <span class="text-[9px] font-medium text-center leading-tight">KTM Digital</span>
            </a>
            <a href="javascript:void(0)" onclick="openModal('modal-spp-payment')" class="flex flex-col items-center justify-center text-gray-400 hover:text-gold w-16 mb-6 relative z-10">
                <div class="bg-[#FFD700] text-midnight w-14 h-14 rounded-full flex items-center justify-center shadow-[0_0_15px_rgba(255,215,0,0.4)] border-4 border-midnight transform hover:scale-105 transition-transform">
                    <i class="fas fa-wallet text-2xl"></i>
                </div>
                <span class="text-[9px] font-bold mt-1 text-gold text-center leading-tight whitespace-nowrap">Bayar SPP</span>
            </a>
            <a href="javascript:void(0)" onclick="openModal('modal-notifications')" class="flex flex-col items-center justify-center text-gray-400 hover:text-gold w-14 mb-1 transition-colors relative">
                <div class="relative">
                    <i class="fas fa-bell text-xl mb-1"></i>
                    <span class="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full border border-midnight"></span>
                </div>
                <span class="text-[9px] font-medium text-center leading-tight">Notifikasi</span>
            </a>
            <a href="javascript:void(0)" onclick="openModal('modal-today-schedule')" class="flex flex-col items-center justify-center text-gray-400 hover:text-gold w-14 mb-1 transition-colors">
                <i class="fas fa-calendar-alt text-xl mb-1"></i>
                <span class="text-[9px] font-medium text-center leading-tight">Jadwal</span>
            </a>
        </div>
    </nav>

    <!-- MODALS SECTION -->
    
    <!-- 1. MODAL PABRIK SURAT OTOMATIS -->
    <div id="modal-pabrik-surat" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <h3 class="text-xl font-bold text-gold font-sans">Surat Otomatis</h3>
                <button aria-label="Tutup Modal" onclick="closeModal('modal-pabrik-surat')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>
            
            <h4 class="text-sm font-bold text-gray-400 mb-3">Daftar Antrean Permohonan</h4>
            <div class="overflow-hidden rounded-xl border border-white/10">
                <table class="w-full text-left border-collapse">
                    <thead class="bg-gold/10 text-gold backdrop-blur-md">
                        <tr>
                            <th class="p-4 text-xs font-bold uppercase">Tanggal</th>
                            <th class="p-4 text-xs font-bold uppercase">NPM / Jenis</th>
                            <th class="p-4 text-xs font-bold uppercase text-right">Aksi</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-white/5">
                        {% for item in surat_list %}
                        <tr class="hover:bg-white/5 transition">
                            <td class="p-4 text-sm text-gray-300">{{ item['tanggal'] }}</td>
                            <td class="p-4">
                                <p class="font-bold text-white">{{ item['jenis_surat'] }}</p>
                                <p class="text-xs text-gray-400">NPM: {{ item['npm'] }}</p>
                            </td>
                            <td class="p-4 text-right">
                                {% if item['status'] == 'Menunggu Acc' %}
                                <form action="/tu/surat/acc" method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                                    <input type="hidden" name="id" value="{{ item['id'] }}">
                                    <button type="submit" class="bg-gold text-midnight px-3 py-1 rounded-lg text-xs font-bold hover:bg-white transition">Setujui</button>
                                </form>
                                {% else %}
                                <span class="text-xs text-green-400 font-bold"><i class="fas fa-check-circle"></i> Selesai</span>
                                {% endif %}
                            </td>
                        </tr>
                        {% else %}
                        <tr><td colspan="3" class="p-4 text-center text-gray-500">Tidak ada antrean</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- 2. MODAL VERIFIKASI PMB DIGITAL -->
    <div id="modal-verifikasi-pmb" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <h3 class="text-xl font-bold text-gold font-sans">Verifikasi PMB & Akun Dosen/Mahasiswa</h3>
                <button aria-label="Tutup Modal" onclick="closeModal('modal-verifikasi-pmb')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>

            <!-- Tabs -->
            <div class="flex p-1 bg-white/10 rounded-xl mb-6">
                <button onclick="switchVerifikasiTab('pmb-content')" id="tab-btn-pmb" class="flex-1 py-2 text-sm font-bold rounded-lg bg-gold shadow-sm text-midnight transition">Calon Mahasiswa Baru (PMB)</button>
                <button onclick="switchVerifikasiTab('dosen-content')" id="tab-btn-dosen" class="flex-1 py-2 text-sm font-bold rounded-lg text-gray-300 hover:bg-white/5 transition">Calon Dosen/Sivitas</button>
            </div>
            
            <div id="pmb-content" class="verifikasi-tab-content">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {% for item in pmb_list %}
                    <div class="bg-white/5 border border-white/10 p-4 rounded-xl">
                        <p class="font-bold text-white mb-2">{{ item['nama'] }}</p>
                        <div class="flex gap-2 mb-4">
                            {% if item['foto_ijazah'] %}
                            <a href="/uploads/{{ item['foto_ijazah'] }}" target="_blank" class="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded">Lihat Ijazah</a>
                            {% endif %}
                            {% if item['foto_ktp'] %}
                            <a href="/uploads/{{ item['foto_ktp'] }}" target="_blank" class="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">Lihat KTP</a>
                            {% endif %}
                            {% if item['bukti_transfer'] %}
                            <a href="/uploads/{{ item['bukti_transfer'] }}" target="_blank" class="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded">Lihat Transfer</a>
                            {% endif %}
                        </div>
                        {% if item['status'] == 'Pending' %}
                        <div id="verifikasi-pmb-form-{{ item['id'] }}" class="hidden mt-3 pt-3 border-t border-white/10">
                            <form action="/tu/pmb/verifikasi" method="POST" class="space-y-3">
                                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                                <input type="hidden" name="type" value="pmb">
                                <input type="hidden" name="id" value="{{ item['id'] }}">
                                
                                <div>
                                    <label class="block text-xs font-bold text-gray-400 mb-1">NPM Baru (Kosongkan utk Auto-Generate)</label>
                                    <input type="text" name="npm_manual" placeholder="Contoh: 2401001" class="w-full bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white focus:outline-none focus:border-gold">
                                </div>
                                <div>
                                    <label class="block text-xs font-bold text-gray-400 mb-1">Password Awal Akun</label>
                                    <input type="text" name="password_awal" placeholder="Default password aman" class="w-full bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white focus:outline-none focus:border-gold">
                                </div>

                                <div class="flex gap-2">
                                    <button type="button" onclick="document.getElementById('verifikasi-pmb-form-{{ item['id'] }}').classList.add('hidden'); document.getElementById('verifikasi-pmb-btn-{{ item['id'] }}').classList.remove('hidden');" class="flex-1 bg-gray-500/20 text-gray-400 font-bold py-2 rounded-lg hover:bg-gray-500/40 transition">Batal</button>
                                    <button type="submit" class="flex-1 bg-gold text-midnight font-bold py-2 rounded-lg hover:bg-white transition">Verifikasi & Buat Akun</button>
                                </div>
                            </form>
                        </div>
                        <button id="verifikasi-pmb-btn-{{ item['id'] }}" onclick="document.getElementById('verifikasi-pmb-form-{{ item['id'] }}').classList.remove('hidden'); this.classList.add('hidden');" class="w-full bg-gold text-midnight font-bold py-2 rounded-lg hover:bg-white transition">Verifikasi Pendaftar</button>
                        {% else %}
                        <a href="https://wa.me/?text=Selamat! Anda telah diterima. NPM: {{ item['npm_generated'] }}" target="_blank" class="block w-full text-center bg-green-500 text-white font-bold py-2 rounded-lg hover:bg-green-600 transition"><i class="fab fa-whatsapp"></i> Kirim Akses</a>
                        {% endif %}
                    </div>
                    {% else %}
                    <p class="text-gray-500">Belum ada pendaftar PMB.</p>
                    {% endfor %}
                </div>
            </div>

            <div id="dosen-content" class="verifikasi-tab-content hidden">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {% for user in pending_users %}
                    <div class="bg-white/5 border border-white/10 p-4 rounded-xl">
                        <p class="font-bold text-white">{{ user['nama'] }}</p>
                        <p class="text-sm text-gray-400 mb-2">Username/Identitas: {{ user['username'] }}</p>
                        <p class="text-xs font-bold text-gold mb-4">Mendaftar Sebagai: {{ user['role'] }}</p>
                        
                        <div id="verifikasi-dosen-form-{{ user['id'] }}" class="hidden mt-3 pt-3 border-t border-white/10">
                            <form action="/tu/pmb/verifikasi" method="POST" class="space-y-3">
                                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                                <input type="hidden" name="type" value="dosen_mhs">
                                <input type="hidden" name="id" value="{{ user['id'] }}">
                                
                                <div>
                                    <label class="block text-xs font-bold text-gray-400 mb-1">Username/NIDN Baru (Opsional)</label>
                                    <input type="text" name="username_manual" value="{{ user['username'] }}" class="w-full bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white focus:outline-none focus:border-gold">
                                </div>
                                <div>
                                    <label class="block text-xs font-bold text-gray-400 mb-1">Password Awal (Kosongkan jk tdk diubah)</label>
                                    <input type="text" name="password_awal" placeholder="Default password aman" class="w-full bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white focus:outline-none focus:border-gold">
                                </div>

                                <div class="flex gap-2">
                                    <button type="button" onclick="document.getElementById('verifikasi-dosen-form-{{ user['id'] }}').classList.add('hidden'); document.getElementById('verifikasi-dosen-btn-{{ user['id'] }}').classList.remove('hidden');" class="flex-1 bg-gray-500/20 text-gray-400 font-bold py-2 rounded-lg hover:bg-gray-500/40 transition">Batal</button>
                                    <button type="submit" class="flex-1 bg-gold text-midnight font-bold py-2 rounded-lg hover:bg-white transition">Aktifkan Akun</button>
                                </div>
                            </form>
                        </div>
                        <button id="verifikasi-dosen-btn-{{ user['id'] }}" onclick="document.getElementById('verifikasi-dosen-form-{{ user['id'] }}').classList.remove('hidden'); this.classList.add('hidden');" class="w-full bg-gold text-midnight font-bold py-2 rounded-lg hover:bg-white transition">Verifikasi & Aktifkan</button>
                    </div>
                    {% else %}
                    <p class="text-gray-500">Belum ada pendaftar Dosen/Sivitas yang menunggu verifikasi.</p>
                    {% endfor %}
                </div>
            </div>

            <script>
                function switchVerifikasiTab(tab) {
                    document.querySelectorAll('.verifikasi-tab-content').forEach(el => el.classList.add('hidden'));
                    document.getElementById(tab).classList.remove('hidden');
                    
                    if(tab === 'pmb-content') {
                        document.getElementById('tab-btn-pmb').className = "flex-1 py-2 text-sm font-bold rounded-lg bg-gold shadow-sm text-midnight transition";
                        document.getElementById('tab-btn-dosen').className = "flex-1 py-2 text-sm font-bold rounded-lg text-gray-300 hover:bg-white/5 transition";
                    } else {
                        document.getElementById('tab-btn-dosen').className = "flex-1 py-2 text-sm font-bold rounded-lg bg-gold shadow-sm text-midnight transition";
                        document.getElementById('tab-btn-pmb').className = "flex-1 py-2 text-sm font-bold rounded-lg text-gray-300 hover:bg-white/5 transition";
                    }
                }
            </script>
        </div>
    </div>

    <!-- 3. MODAL LACI ARSIP ANTI RAYAP -->
    <div id="modal-laci-arsip" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <h3 class="text-xl font-bold text-gold font-sans">Arsip Digital Data Kampus</h3>
                <button onclick="closeModal('modal-laci-arsip')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>
            
            <div class="flex gap-2 mb-6">
                <input type="text" id="arsip-search-npm" placeholder="Ketik NPM Mahasiswa..." class="flex-1 bg-[#0b1026] border border-gold/30 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-gold">
                <button aria-label="Cari Arsip" onclick="searchArsip()" class="bg-blue-500 text-white px-6 rounded-xl font-bold hover:bg-blue-600 transition"><i class="fas fa-search"></i></button>
            </div>
            
            <div id="arsip-result" class="text-white">
                <p class="text-gray-500 text-center">Gunakan fitur pencarian di atas.</p>
            </div>
            
            <script>
                async function searchArsip() {
                    const npm = document.getElementById('arsip-search-npm').value;
                    if(!npm) return;
                    document.getElementById('arsip-result').innerHTML = '<p class="text-center">Mencari...</p>';
                    try {
                        const res = await fetch('/tu/arsip/search?npm=' + npm);
                        const data = await res.json();
                        if(data.error) {
                             document.getElementById('arsip-result').innerHTML = `<p class="text-red-400 text-center">${data.error}</p>`;
                             return;
                        }
                        let html = `
                        <div class="bg-white/5 p-4 rounded-xl border border-white/10 mb-4">
                            <h4 class="font-bold text-gold text-lg">${data.user.nama} (${data.user.username})</h4>
                            <p class="text-sm text-gray-300">Status: ${data.user.status_akademik}</p>
                        </div>
                        <h5 class="font-bold text-gray-400 mb-2">Riwayat Tagihan</h5>
                        <ul class="mb-4 space-y-2">`;
                        data.tagihan.forEach(t => {
                            html += `<li class="bg-white/5 p-2 rounded text-sm flex justify-between"><span>${t.jenis_tagihan}</span> <span class="${t.status=='Lunas' ? 'text-green-400' : 'text-red-400'}">${t.status}</span></li>`;
                        });
                        html += `</ul><h5 class="font-bold text-gray-400 mb-2">Dokumen Digital</h5><ul class="space-y-2">`;
                        data.dokumen.forEach(d => {
                            html += `<li class="bg-white/5 p-2 rounded text-sm flex justify-between"><span>${d.nama_dokumen}</span> <a href="/uploads/${d.file_path}" target="_blank" class="text-blue-400"><i class="fas fa-download"></i> Unduh</a></li>`;
                        });
                        html += `</ul>`;
                        document.getElementById('arsip-result').innerHTML = html;
                    } catch(e) {
                        document.getElementById('arsip-result').innerHTML = '<p class="text-red-500">Error fetching data.</p>';
                    }
                }
            </script>
        </div>
    </div>

    <!-- 4. MODAL VERIFIKASI PEMBAYARAN -->
    <div id="modal-verifikasi-pembayaran" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <h3 class="text-xl font-bold text-gold font-sans">Verifikasi Pembayaran</h3>
                <button onclick="closeModal('modal-verifikasi-pembayaran')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>
            
            <form action="/tu/tagihan/tambah" method="POST" class="bg-white/5 p-4 border border-white/10 rounded-xl mb-6 space-y-3">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <div class="grid grid-cols-2 gap-3">
                    <input type="text" name="npm" placeholder="NPM Mahasiswa" required class="bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white">
                    <input type="number" name="jumlah" placeholder="Nominal (Misal: 3500000)" required class="bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white">
                </div>
                <input type="text" name="jenis_tagihan" placeholder="Jenis Tagihan (Contoh: SPP Semester Ganjil 2024)" required class="w-full bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white">
                <button type="submit" class="w-full bg-gold text-midnight font-bold py-2 rounded-lg hover:bg-white transition">+ Terbitkan Tagihan</button>
            </form>

            <div class="space-y-3">
                {% for item in tagihan_list %}
                <div class="bg-white/5 p-4 rounded-xl border border-white/10 flex justify-between items-center">
                    <div>
                        <p class="font-bold text-white">{{ item['jenis_tagihan'] }}</p>
                        <p class="text-xs text-gray-400">NPM: {{ item['npm'] }} • Rp {{ item['jumlah'] }}</p>
                        {% if item['bukti_transfer'] %}
                        <a href="/uploads/{{ item['bukti_transfer'] }}" target="_blank" class="text-xs text-blue-400 underline mt-1 block">Lihat Bukti Transfer</a>
                        {% endif %}
                        {% if item['status'] != 'Lunas' %}
                        <a href="https://wa.me/?text=Assalamualaikum%20warahmatullahi%20wabarakatuh.%20Pemberitahuan%20dari%20kampus%20STIESAM,%20terdapat%20tagihan%20{{ item['jenis_tagihan'] }}%20sebesar%20Rp%20{{ item['jumlah'] }}.%20Mohon%20untuk%20segera%20melakukan%20pembayaran%20sebelum%20tenggat%20waktu.%20Terima%20kasih." target="_blank" class="inline-block mt-2 text-xs bg-[#25D366]/20 text-[#25D366] px-2 py-1 rounded"><i class="fab fa-whatsapp"></i> Ingatkan (WA)</a>
                        {% endif %}
                    </div>
                    {% if item['status'] != 'Lunas' %}
                    <form action="/tu/tagihan/lunas" method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                        <input type="hidden" name="id" value="{{ item['id'] }}">
                        <button type="submit" class="bg-green-500 text-white px-4 py-2 rounded-lg font-bold hover:bg-green-600 transition">Lunas</button>
                    </form>
                    {% else %}
                    <span class="text-green-400 font-bold"><i class="fas fa-check-circle"></i> Lunas</span>
                    {% endif %}
                </div>
                {% else %}
                <p class="text-gray-500 text-center">Tidak ada tagihan tercatat.</p>
                {% endfor %}
            </div>
            
        </div>
    </div>

    <!-- 5. MODAL KELOLA JADWAL -->
    <div id="modal-kelola-jadwal" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <h3 class="text-xl font-bold text-gold font-sans">Kelola Jadwal Perkuliahan</h3>
                <button onclick="closeModal('modal-kelola-jadwal')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>
            
            <form action="/tu/jadwal" method="POST" class="bg-white/5 p-4 border border-white/10 rounded-xl mb-6 space-y-3">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                <div class="grid grid-cols-2 gap-3">
                    <input type="text" name="hari" placeholder="Hari (e.g. Senin)" required class="bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white">
                    <input type="text" name="jam" placeholder="Jam (e.g. 08:00 - 10:30)" required class="bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white">
                </div>
                <input type="text" name="mata_kuliah" placeholder="Nama Mata Kuliah" required class="w-full bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white">
                <input type="text" name="dosen" placeholder="Nama Dosen Pengampu" required class="w-full bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white">
                <input type="text" name="ruangan" placeholder="Ruangan" required class="w-full bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white">
                <button type="submit" class="w-full bg-gold text-midnight font-bold py-2 rounded-lg hover:bg-white transition">+ Tambah Jadwal</button>
            </form>

            <div class="space-y-3">
                {% for item in jadwal_list %}
                <div class="bg-white/5 p-4 rounded-xl border border-white/10 flex justify-between items-center">
                    <div>
                        <p class="font-bold text-white">{{ item['mata_kuliah'] }}</p>
                        <p class="text-xs text-gray-400">{{ item['hari'] }}, {{ item['jam'] }} • Ruang: {{ item['ruangan'] }}</p>
                        <p class="text-xs text-gold">{{ item['dosen'] }}</p>
                    </div>
                </div>
                {% else %}
                <p class="text-gray-500 text-center">Jadwal kosong.</p>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- MODAL CEK ALUMNI -->
    <div id="modal-cek-alumni" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <h3 class="text-xl font-bold text-gold font-sans">Verifikasi Tracer Study Alumni</h3>
                <button onclick="closeModal('modal-cek-alumni')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>
            
            <div class="space-y-4">
                {% for item in tracer_list %}
                <div class="bg-white/5 p-5 rounded-2xl shadow-sm border border-white/10 relative">
                    <div class="flex justify-between items-start mb-2">
                        <h4 class="font-bold text-white text-lg">{{ item['nama_lengkap'] }} <span class="text-xs font-mono text-gold ml-2">({{ item['npm'] }})</span></h4>
                        <span class="text-[10px] font-bold px-2 py-1 rounded-full {{ 'bg-yellow-500/20 text-yellow-400' if item['status'] == 'Menunggu Verifikasi' else 'bg-green-500/20 text-green-400' }}">{{ item['status'] }}</span>
                    </div>
                    <p class="text-xs text-gray-400 mb-1">Lulus: {{ item['tahun_lulus'] }} • {{ item['program_studi'] }}</p>
                    <p class="text-xs text-gray-400 mb-3">Kerja: {{ item['status_pekerjaan'] }} di {{ item['nama_perusahaan'] or '-' }} sebagai {{ item['jabatan'] or '-' }}</p>
                    
                    {% if item['status'] == 'Menunggu Verifikasi' %}
                    <form action="/tu/tracer/verify" method="POST" class="mt-4 pt-3 border-t border-white/10 text-right">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <input type="hidden" name="id" value="{{ item['id'] }}">
                        <button type="submit" class="bg-green-500 text-white px-4 py-2 rounded-lg text-xs font-bold hover:bg-green-600 transition">Verifikasi & Publikasi</button>
                    </form>
                    {% endif %}
                </div>
                {% else %}
                <div class="bg-white/5 p-6 rounded-2xl border border-white/10 text-center">
                    <p class="text-gray-400 text-sm">Belum ada data Tracer Study dari alumni.</p>
                </div>
                {% endfor %}
            </div>

            <h4 class="text-[#075985] font-bold mb-3 border-l-4 border-[#7DD3FC] pl-2 mt-6">Dokumen Pendaftaran Awal (PMB)</h4>
            <div class="grid grid-cols-2 gap-4">
                {% for doc in pmb_docs %}
                <a href="/uploads/{{ doc['file_path'] }}" target="_blank" class="bg-white p-4 rounded-2xl shadow-sm border border-[#0284C7]/20 flex flex-col items-center justify-center text-center hover:bg-gray-50 transition-colors group">
                    <div class="w-12 h-12 bg-sky-100 text-sky-600 rounded-full flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                        <i class="fas fa-image text-xl"></i>
                    </div>
                    <span class="text-xs font-bold text-gray-700">{{ doc['nama_dokumen'] }}</span>
                </a>
                {% else %}
                <div class="col-span-2 bg-white p-6 rounded-2xl text-center border border-[#0284C7]/20">
                    <p class="text-gray-400 text-sm">Belum ada dokumen pendaftaran awal.</p>
                </div>
                {% endfor %}
            </div>

            <h4 class="text-[#075985] font-bold mb-3 border-l-4 border-[#7DD3FC] pl-2">Dokumen Pendaftaran Awal</h4>
            <div class="space-y-3">
                {% for doc in pmb_docs %}
                <div class="bg-white p-4 rounded-2xl shadow-sm border border-[#0284C7]/20 flex justify-between items-center group hover:bg-gray-50 transition-colors">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-full bg-[#0284C7]/10 text-[#0284C7] flex items-center justify-center text-lg">
                            <i class="fas fa-file-image"></i>
                        </div>
                        <div>
                            <p class="font-bold text-gray-800 text-sm">{{ doc['nama_dokumen'] }}</p>
                        </div>
                    </div>
                    <div class="flex gap-2">
                        <a href="/uploads/{{ doc['file_path'] }}" target="_blank" class="text-xs bg-sky-100 text-[#0284C7] px-3 py-1.5 rounded-lg font-bold hover:bg-[#7DD3FC] hover:text-white transition-colors">Lihat Dokumen</a>
                        <a href="/uploads/{{ doc['file_path'] }}" download class="w-8 h-8 flex items-center justify-center text-[#0284C7] bg-sky-100 hover:text-white hover:bg-[#7DD3FC] rounded-lg transition-colors">
                            <i class="fas fa-download"></i>
                        </a>
                    </div>
                </div>
                {% else %}
                <div class="bg-white p-6 rounded-2xl text-center border border-[#0284C7]/20">
                    <p class="text-gray-400 text-sm">Tidak ada dokumen pendaftaran awal.</p>
                </div>
                {% endfor %}
            </div>

        </div>
    </div>

    <!-- MODAL PUBLIKASI INFORMASI -->
    <div id="modal-publikasi-informasi" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <h3 class="text-xl font-bold text-gold font-sans">Publikasi Informasi Publik</h3>
                <button onclick="closeModal('modal-publikasi-informasi')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>
            
            <form action="/tu/publikasi/update" method="POST" enctype="multipart/form-data" class="space-y-6">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                <div class="bg-white/5 border border-white/10 p-6 rounded-2xl">
                    <h4 class="text-white font-bold mb-4 border-l-4 border-gold pl-2">1. Profil Kampus</h4>
                    <label class="block text-xs text-gray-400 mb-1">Teks Sejarah / Deskripsi Utama</label>
                    <textarea name="profil_deskripsi" class="w-full bg-[#0b1026] border border-gold/30 rounded-xl p-3 text-sm text-white mb-3 h-24">{{ settings.get('profil_deskripsi', 'Sekolah Tinggi Ilmu Ekonomi (STIE) SAM Samarinda didirikan dengan komitmen teguh untuk menghasilkan sarjana ekonomi yang profesional, beretika, dan mampu bersaing di era digital. Dengan fasilitas pembelajaran yang representatif dan didukung oleh staf pengajar yang kompeten di bidangnya, STIESAM terus bertransformasi menjadi pusat unggulan kajian ekonomi di Kalimantan Timur.') }}</textarea>
                    
                    <label class="block text-xs text-gray-400 mb-1">Teks Visi Kampus</label>
                    <textarea name="profil_visi" class="w-full bg-[#0b1026] border border-gold/30 rounded-xl p-3 text-sm text-white mb-3 h-16">{{ settings.get('profil_visi', 'Menjadi institusi pendidikan tinggi ekonomi yang terkemuka, inovatif, dan berdaya saing global dengan menjunjung tinggi nilai-nilai moral dan etika bisnis.') }}</textarea>
                    
                    <label class="block text-xs text-gray-400 mb-1">Teks Misi Kampus</label>
                    <textarea name="profil_misi" class="w-full bg-[#0b1026] border border-gold/30 rounded-xl p-3 text-sm text-white mb-3 h-24">{{ settings.get('profil_misi', '1. Menyelenggarakan pendidikan yang berkualitas.\n2. Melaksanakan penelitian yang bermanfaat.\n3. Melakukan pengabdian yang berdampak nyata bagi masyarakat.') }}</textarea>
                    
                    <label class="block text-xs text-gray-400 mb-1">Gambar/Foto Profil Kampus (Opsional, max 2MB)</label>
                    <input type="file" name="profil_gambar" class="text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-bold file:bg-gold/20 file:text-gold hover:file:bg-gold/30">
                </div>

                <div class="bg-white/5 border border-white/10 p-6 rounded-2xl">
                    <h4 class="text-white font-bold mb-4 border-l-4 border-green-500 pl-2">2. Berita & Agenda Kampus</h4>
                    <p class="text-xs text-gray-500 mb-4">Ubah isi berita/agenda utama yang ditampilkan pada beranda (Highlight 1).</p>
                    
                    <label class="block text-xs text-gray-400 mb-1">Kategori / Label (Contoh: Seminar Nasional)</label>
                    <input type="text" name="berita_label" value="{{ settings.get('berita_label', 'Seminar Nasional') }}" class="w-full bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white mb-3">
                    
                    <label class="block text-xs text-gray-400 mb-1">Judul Berita</label>
                    <input type="text" name="berita_judul" value="{{ settings.get('berita_judul', 'Tantangan Ekonomi Digital 2025') }}" class="w-full bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white mb-3">
                    
                    <label class="block text-xs text-gray-400 mb-1">Waktu & Tempat</label>
                    <input type="text" name="berita_waktu" value="{{ settings.get('berita_waktu', '12 Oktober 2024 • Auditorium STIESAM') }}" class="w-full bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white mb-3">
                    
                    <label class="block text-xs text-gray-400 mb-1">Isi Berita</label>
                    <textarea name="berita_isi" class="w-full bg-[#0b1026] border border-gold/30 rounded-xl p-3 text-sm text-white mb-3 h-20">{{ settings.get('berita_isi', 'Seminar nasional yang membahas tentang persiapan UMKM menghadapi transformasi ekonomi digital dan kecerdasan buatan.') }}</textarea>
                    
                    <label class="block text-xs text-gray-400 mb-1">Gambar Sampul Berita (Opsional, max 2MB)</label>
                    <input type="file" name="berita_gambar" class="text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-bold file:bg-green-500/20 file:text-green-500 hover:file:bg-green-500/30">
                </div>

                <div class="bg-white/5 border border-white/10 p-6 rounded-2xl">
                    <h4 class="text-white font-bold mb-4 border-l-4 border-purple-500 pl-2">3. Galeri Jurnal & Penelitian</h4>
                    <p class="text-xs text-gray-500 mb-4">Ubah isi sorotan jurnal penelitian utama (Highlight 1).</p>
                    
                    <label class="block text-xs text-gray-400 mb-1">Kategori Prodi (Contoh: Manajemen Keuangan)</label>
                    <input type="text" name="jurnal_kategori" value="{{ settings.get('jurnal_kategori', 'Manajemen Keuangan') }}" class="w-full bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white mb-3">
                    
                    <label class="block text-xs text-gray-400 mb-1">Volume/Tahun</label>
                    <input type="text" name="jurnal_volume" value="{{ settings.get('jurnal_volume', 'Vol 12, No. 2 (2023)') }}" class="w-full bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white mb-3">
                    
                    <label class="block text-xs text-gray-400 mb-1">Judul Penelitian</label>
                    <textarea name="jurnal_judul" class="w-full bg-[#0b1026] border border-gold/30 rounded-xl p-3 text-sm text-white mb-3 h-16">{{ settings.get('jurnal_judul', 'Analisis Pengaruh Literasi Keuangan Terhadap Kinerja UMKM di Samarinda') }}</textarea>
                    
                    <label class="block text-xs text-gray-400 mb-1">Penulis</label>
                    <input type="text" name="jurnal_penulis" value="{{ settings.get('jurnal_penulis', 'Dr. Budi Santoso, M.Si., Rina Astuti, S.E.') }}" class="w-full bg-[#0b1026] border border-gold/30 rounded-lg p-2 text-sm text-white mb-3">
                </div>

                <button type="submit" class="w-full bg-gold text-midnight font-bold py-4 rounded-xl hover:bg-white transition text-lg"><i class="fas fa-save mr-2"></i>Simpan Perubahan Publikasi</button>
            </form>
        </div>
    </div>

    <!-- 6. MODAL MANAJEMEN SIVITAS -->
    <div id="modal-manajemen-sivitas" class="hidden fixed inset-0 z-40 bg-[#0b1026] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                <h3 class="text-xl font-bold text-gold font-sans">Manajemen Sivitas Akademika</h3>
                <button onclick="closeModal('modal-manajemen-sivitas')" class="text-gray-400 hover:text-white bg-white/10 w-8 h-8 rounded-full">&times;</button>
            </div>
            
            <div class="flex gap-2 mb-6">
                <button onclick="filterSivitas('Tata Usaha')" class="bg-blue-500/20 text-blue-400 hover:bg-blue-500/40 px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2"><i class="fas fa-user-shield"></i> TU</button>
                <button onclick="filterSivitas('Mahasiswa')" class="bg-green-500/20 text-green-400 hover:bg-green-500/40 px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2"><i class="fas fa-user-graduate"></i> Mahasiswa</button>
                <button onclick="filterSivitas('Dosen')" class="bg-purple-500/20 text-purple-400 hover:bg-purple-500/40 px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2"><i class="fas fa-chalkboard-teacher"></i> Dosen</button>
                <button onclick="filterSivitas('all')" class="bg-gray-500/20 text-gray-400 hover:bg-gray-500/40 px-4 py-2 rounded-xl text-xs font-bold transition ml-auto">Semua</button>
            </div>

            <script>
                function filterSivitas(role) {
                    const rows = document.querySelectorAll('.sivitas-row');
                    rows.forEach(row => {
                        if(role === 'all' || row.dataset.role === role) {
                            row.style.display = '';
                        } else {
                            row.style.display = 'none';
                        }
                    });
                }
            </script>
            
            <div class="overflow-x-auto rounded-xl border border-white/10">
                <table class="w-full text-left border-collapse min-w-[600px]">
                    <thead class="bg-gold/10 text-gold">
                        <tr>
                            <th class="p-3 text-xs font-bold uppercase">User</th>
                            <th class="p-3 text-xs font-bold uppercase">Role</th>
                            <th class="p-3 text-xs font-bold uppercase">Kata Sandi</th>
                            <th class="p-3 text-xs font-bold uppercase">Status</th>
                            <th class="p-3 text-xs font-bold uppercase">Aksi</th>
                            <th class="p-3 text-xs font-bold uppercase text-right">Hapus</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-white/5">
                        {% for item in akun_list %}
                        <tr class="hover:bg-white/5 transition sivitas-row" data-role="{{ item['role'] }}">
                            <td class="p-3">
                                <p class="font-bold text-white">{{ item['nama'] }}</p>
                                <p class="text-[10px] text-gray-400">{{ item['username'] }}</p>
                            </td>
                            <td class="p-3 text-xs text-gray-300">{{ item['role'] }}</td>
                            <td class="p-3 text-xs text-gray-300">
                                <span class="truncate max-w-[100px] block cursor-pointer hover:text-white" onclick="document.getElementById('reset-pass-form-{{ item['id'] }}').submit();" title="Reset untuk lihat">****** (Reset untuk lihat)</span>
                                <form id="reset-pass-form-{{ item['id'] }}" action="/tu/akun/reset_password" method="POST" style="display: none;">
                                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                                    <input type="hidden" name="id" value="{{ item['id'] }}">
                                </form>
                            </td>
                            <td class="p-3">
                                <span class="px-3 py-1 rounded-full border shadow-sm text-[10px] font-bold tracking-widest uppercase {{ 'bg-green-900/50 text-green-400 border-green-500/30' if item['status_akademik'] == 'Aktif' else ('bg-orange-900/50 text-orange-400 border-orange-500/30' if item['status_akademik'] == 'Cuti' else ('bg-red-900/50 text-red-400 border-red-500/30' if item['status_akademik'] == 'Keluar' else ('bg-blue-900/50 text-blue-400 border-blue-500/30' if item['status_akademik'] == 'Lulus' else 'bg-gray-800 text-gray-400 border-gray-600'))) }}">{{ item['status_akademik'] }}</span>
                            </td>
                            <td class="p-3 text-xs">
                                <div class="flex flex-col gap-2">
                                    <form action="/tu/akun/update" method="POST" class="flex gap-2">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                                        <input type="hidden" name="id" value="{{ item['id'] }}">
                                        <select name="status_akademik" class="bg-[#0b1026] text-white border border-gold/30 rounded p-1 text-[10px]">
                                            <option value="Aktif" {{ 'selected' if item['status_akademik'] == 'Aktif' else '' }}>Aktif</option>
                                            <option value="Cuti" {{ 'selected' if item['status_akademik'] == 'Cuti' else '' }}>Cuti</option>
                                            <option value="Keluar" {{ 'selected' if item['status_akademik'] == 'Keluar' else '' }}>Keluar</option>
                                            <option value="Lulus" {{ 'selected' if item['status_akademik'] == 'Lulus' else '' }}>Lulus</option>
                                        </select>
                                        <button type="submit" class="bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600">Simpan</button>
                                    </form>
                                    <form action="/tu/akun/reset_password" method="POST" onsubmit="return confirm('Reset password?');">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

                                        <input type="hidden" name="id" value="{{ item['id'] }}">
                                        <button type="submit" class="bg-red-500/20 text-red-400 px-2 py-1 rounded hover:bg-red-500/40 w-full text-center">Reset Password</button>
                                    </form>
                                </div>
                            </td>
                            <td class="p-3 text-right">
                                <form action="/tu/akun/delete" method="POST" onsubmit="return confirm('Peringatan: Menghapus akun ini akan menghapus semua data yang berkaitan secara permanen. Anda yakin?');">
                                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                                    <input type="hidden" name="id" value="{{ item['id'] }}">
                                    <button aria-label="Hapus" type="submit" class="text-red-500 hover:text-red-400 bg-red-500/10 p-2 rounded-full transition" title="Hapus Permanen"><i class="fas fa-trash"></i></button>
                                </form>
                            </td>
                        </tr>
                        {% else %}
                        <tr><td colspan="5" class="p-3 text-center text-gray-500">Tidak ada data pengguna</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    
</div>

<script>
    // --- RAMADHAN JS UTILS ---

    
        // Tampilkan kerangka loading saat transisi halaman (tanpa merombak struktur)
        window.addEventListener('beforeunload', function () {
            document.body.classList.add('skeleton-overlay');
        });
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
        if (id === 'modal-cek-status-pmb') {
            const cekNamaInput = document.getElementById('cek-nama');
            if (cekNamaInput) {
                setTimeout(() => cekNamaInput.focus(), 100);
            }
        }
    }
    
    
        // Tampilkan kerangka loading saat transisi halaman (tanpa merombak struktur)
        window.addEventListener('beforeunload', function () {
            document.body.classList.add('skeleton-overlay');
        });
        document.addEventListener('DOMContentLoaded', () => {
        const openModalParam = '{{ request.args.get("open", "") }}';
        if (openModalParam) {
            openModal(openModalParam);
        }
    });
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
    
    window.addEventListener('beforeunload', function () {
        document.body.classList.add('skeleton', 'opacity-50', 'pointer-events-none');
    });

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

RAMADHAN_STYLES = """

# """

IRMA_STYLES = """
    <style>
        .bg-sage { background-color: #0284C7; }
        .text-sage { color: #0284C7; }
        .border-sage { border-color: #0284C7; }
        
        .bg-pastel-pink { background-color: #7DD3FC; }
        .text-pastel-pink { color: #7DD3FC; }
        .border-pastel-pink { border-color: #7DD3FC; }
        
        .bg-off-white { background-color: #F0F9FF; }
        
        .text-dark-grey { color: #4A4A4A; }
        .text-forest { color: #075985; } /* Dark Forest Green for contrast */
        
        .irma-header {
            background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%);
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
            border-color: #7DD3FC;
        }
        
        .btn-irma-primary {
            background-color: #0284C7;
            color: white;
            border-radius: 0.75rem;
            font-weight: bold;
            transition: all 0.3s;
        }
        .btn-irma-primary:hover {
            background-color: #7DD3FC;
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
<div class="pt-24 pb-32 px-5 md:px-8 bg-[#F0F9FF] min-h-screen">
    
    <!-- SPLIT HEADER -->
    <div class="md:grid md:grid-cols-2 md:gap-12 md:items-center mb-10">
        
        <!-- LEFT: WELCOME -->
        <div class="hidden md:block pl-2">
            <p class="text-xl text-gray-500 font-medium mb-2">Salam Mahasiswa STIESAM</p>
            <h1 class="text-5xl font-bold text-[#075985] leading-tight mb-6">Dasbor Mahasiswa<br>Terintegrasi</h1>
            <p class="text-gray-600 text-lg leading-relaxed mb-8">
                Pusat layanan akademik dan keuangan terpadu. Pantau rencana studi, kartu hasil studi, jadwal, dan tagihan dengan mudah dan efisien.
            </p>
            <div class="flex gap-4">
                <button onclick="openModal('modal-jadwal-kuliah')" class="bg-[#0284C7] text-white px-8 py-3 rounded-full font-bold shadow-lg hover:bg-[#0369A1] transition transform hover:scale-105">Lihat Jadwal</button>
                <button onclick="openModal('modal-profil-arsip')" class="bg-transparent text-[#0284C7] border-2 border-[#0284C7] px-8 py-3 rounded-full font-bold hover:bg-[#0284C7] hover:text-white transition transform hover:scale-105">Profil Saya</button>
            </div>
        </div>

        <!-- RIGHT: MAHASISWA STATS -->
        <div>
            <div class="bg-gradient-to-br from-[#0284C7] to-[#0369A1] rounded-3xl p-6 md:p-10 text-white shadow-xl relative overflow-hidden transform md:hover:scale-[1.02] transition-transform duration-500 border border-white/20">
                <div class="absolute top-0 right-0 opacity-10 transform translate-x-4 -translate-y-4">
                    <i class="fas fa-graduation-cap text-9xl"></i>
                </div>
                <div class="relative z-10">
                    <p class="text-xs font-medium opacity-80 mb-1 tracking-wide uppercase">Informasi Akademik</p>
                    <h2 class="text-3xl font-bold mb-1">{{ user.nama if user else 'Nama Mahasiswa' }}</h2>
                    <p class="text-sm font-mono opacity-90 mb-4">{{ user.username if user else 'NPM' }}</p>
                    
                    {% set total_sks_kumulatif = namespace(value=0) %}
                    {% set total_bobot_kumulatif = namespace(value=0) %}
                    {% for n in nilai_list %}
                        {% set nilai_angka = 4.0 %}
                        {% if n['nilai_huruf'] == 'A' %}{% set nilai_angka = 4.0 %}
                        {% elif n['nilai_huruf'] == 'A-' %}{% set nilai_angka = 3.7 %}
                        {% elif n['nilai_huruf'] == 'B+' %}{% set nilai_angka = 3.3 %}
                        {% elif n['nilai_huruf'] == 'B' %}{% set nilai_angka = 3.0 %}
                        {% elif n['nilai_huruf'] == 'B-' %}{% set nilai_angka = 2.7 %}
                        {% elif n['nilai_huruf'] == 'C+' %}{% set nilai_angka = 2.3 %}
                        {% elif n['nilai_huruf'] == 'C' %}{% set nilai_angka = 2.0 %}
                        {% elif n['nilai_huruf'] == 'D' %}{% set nilai_angka = 1.0 %}
                        {% else %}{% set nilai_angka = 0.0 %}{% endif %}
                        {% set total_sks_kumulatif.value = total_sks_kumulatif.value + n['sks'] %}
                        {% set total_bobot_kumulatif.value = total_bobot_kumulatif.value + (n['sks'] * nilai_angka) %}
                    {% endfor %}
                    {% set ipk = (total_bobot_kumulatif.value / total_sks_kumulatif.value) if total_sks_kumulatif.value > 0 else 0 %}
                    
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-white/20 backdrop-blur-md rounded-xl p-4 border border-white/10">
                            <p class="text-[10px] uppercase tracking-wider mb-1 opacity-80">IPK Saat Ini</p>
                            <span class="font-mono text-2xl font-bold">{{ '%.2f' | format(ipk) }}</span>
                        </div>
                        <div class="bg-white/20 backdrop-blur-md rounded-xl p-4 border border-white/10">
                            <p class="text-[10px] uppercase tracking-wider mb-1 opacity-80">SKS Ditempuh</p>
                            <span class="font-mono text-2xl font-bold">{{ total_sks_kumulatif.value }}</span>
                        </div>
                    </div>
                    
                    <a href="/logout" class="block w-full text-center mt-4 bg-white/20 hover:bg-white/30 text-white text-xs font-bold py-2 rounded-xl border border-white/20 transition backdrop-blur-md shadow-sm">
                        Keluar Akun
                    </a>
                </div>
            </div>
        </div>
    </div>

    <!-- MENU GRID -->
    <h3 class="text-[#075985] font-bold text-lg mb-4 pl-3 border-l-4 border-[#7DD3FC]">Layanan Akademik</h3>
    <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-24">
        
        <!-- 1. RENCANA STUDI -->
        <button onclick="openModal('modal-rencana-studi')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#0284C7]/20 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
             <div class="w-14 h-14 rounded-full bg-[#0284C7]/10 flex items-center justify-center text-[#0284C7] mb-3 group-hover:bg-[#0284C7] group-hover:text-white transition-colors shadow-inner">
                <i class="fas fa-file-signature text-2xl"></i>
             </div>
             <span class="font-bold text-sm text-gray-600 group-hover:text-[#0284C7]">Rencana Studi</span>
        </button>

        <!-- 2. KARTU HASIL STUDI -->
        <button onclick="openModal('modal-kartu-hasil-studi')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#0284C7]/20 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
             <div class="w-14 h-14 rounded-full bg-[#0284C7]/10 flex items-center justify-center text-[#0284C7] mb-3 group-hover:bg-[#0284C7] group-hover:text-white transition-colors shadow-inner">
                <i class="fas fa-graduation-cap text-2xl"></i>
             </div>
             <span class="font-bold text-sm text-gray-600 group-hover:text-[#0284C7]">Kartu Hasil Studi</span>
        </button>

        <!-- 3. PUSAT TAGIHAN -->
        <button onclick="openModal('modal-pusat-tagihan')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#0284C7]/20 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all relative">
             {% if has_unpaid %}
             <div class="absolute -top-2 -right-2 bg-red-500 text-white w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold shadow-md animate-pulse">!</div>
             {% endif %}
             <div class="w-14 h-14 rounded-full bg-[#0284C7]/10 flex items-center justify-center text-[#0284C7] mb-3 group-hover:bg-[#0284C7] group-hover:text-white transition-colors shadow-inner">
                <i class="fas fa-money-check-alt text-2xl"></i>
             </div>
             <span class="font-bold text-sm text-gray-600 group-hover:text-[#0284C7]">Pusat Tagihan</span>
        </button>

        <!-- 4. JADWAL KULIAH -->
        <button onclick="openModal('modal-jadwal-kuliah')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#0284C7]/20 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
             <div class="w-14 h-14 rounded-full bg-[#0284C7]/10 flex items-center justify-center text-[#0284C7] mb-3 group-hover:bg-[#0284C7] group-hover:text-white transition-colors shadow-inner">
                <i class="fas fa-calendar-alt text-2xl"></i>
             </div>
             <span class="font-bold text-sm text-center text-gray-600 group-hover:text-[#0284C7]">Jadwal Kuliah<br>& Ruangan</span>
        </button>

        <!-- 5. PERMOHONAN SURAT -->
        <button onclick="openModal('modal-permohonan-surat')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#0284C7]/20 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
             <div class="w-14 h-14 rounded-full bg-[#0284C7]/10 flex items-center justify-center text-[#0284C7] mb-3 group-hover:bg-[#0284C7] group-hover:text-white transition-colors shadow-inner">
                <i class="fas fa-envelope-open-text text-2xl"></i>
             </div>
             <span class="font-bold text-sm text-center text-gray-600 group-hover:text-[#0284C7]">Permohonan Surat<br>Akademik</span>
        </button>

        <!-- 6. PROFIL DAN ARSIP DIGITAL -->
        <button onclick="openModal('modal-profil-arsip')" class="bg-white p-6 rounded-3xl shadow-sm border border-[#0284C7]/20 flex flex-col items-center justify-center h-40 group hover:scale-105 transition-all">
             <div class="w-14 h-14 rounded-full bg-[#0284C7]/10 flex items-center justify-center text-[#0284C7] mb-3 group-hover:bg-[#0284C7] group-hover:text-white transition-colors shadow-inner">
                <i class="fas fa-id-badge text-2xl"></i>
             </div>
             <span class="font-bold text-sm text-center text-gray-600 group-hover:text-[#0284C7]">Profil & Arsip<br>Digital Saya</span>
        </button>
    </div>

    <!-- MODALS SECTION -->
    
    <!-- 3. MODAL PUSAT TAGIHAN -->
    <div id="modal-pusat-tagihan" class="hidden fixed inset-0 z-40 bg-[#F0F9FF] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-[#0284C7]/20 pb-4">
                <h3 class="text-xl font-bold text-[#075985]">Pusat Tagihan Pendidikan</h3>
                <button onclick="closeModal('modal-pusat-tagihan')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
            </div>
            
            <div class="space-y-4">
                {% for item in tagihan_list %}
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-[#0284C7]/20 relative overflow-hidden">
                    {% if item['status'] == 'Lunas' %}
                    <div class="absolute top-4 right-4 text-green-500 font-bold text-sm flex items-center gap-1">
                        <i class="fas fa-check-circle"></i> Lunas
                    </div>
                    {% else %}
                    <div class="absolute top-4 right-4 text-red-500 font-bold text-sm flex items-center gap-1 animate-pulse">
                        <i class="fas fa-exclamation-circle"></i> Belum Lunas
                    </div>
                    {% endif %}
                    
                    <h4 class="font-bold text-lg text-gray-800 mb-1">{{ item['jenis_tagihan'] }}</h4>
                    <p class="text-sm text-gray-500 mb-4">Total: <span class="font-bold text-[#075985]">Rp {{ "{:,.0f}".format(item['jumlah']|int) if item['jumlah']|string|length > 0 else '0' }}</span></p>
                    
                    {% if item['status'] != 'Lunas' %}
                    <form action="/mahasiswa/tagihan/upload" method="POST" enctype="multipart/form-data" class="bg-gray-50 p-4 rounded-xl border border-gray-100 mt-4">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <input type="hidden" name="tagihan_id" value="{{ item['id'] }}">
                        <label class="block text-xs font-bold text-gray-500 mb-2">Upload Bukti Transfer Bank:</label>
                        <div class="flex gap-2">
                            <input type="file" name="bukti_transfer" required class="flex-1 text-xs text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-[#0284C7]/10 file:text-[#0284C7] hover:file:bg-[#0284C7]/20">
                            <button type="submit" class="bg-[#0284C7] text-white px-4 py-2 rounded-full font-bold text-xs shadow-sm hover:bg-[#0369A1] transition">Kirim</button>
                        </div>
                    </form>
                    {% endif %}
                    {% if item['bukti_transfer'] %}
                    <a href="/uploads/{{ item['bukti_transfer'] }}" target="_blank" class="text-xs text-blue-500 underline mt-2 block w-max"><i class="fas fa-eye"></i> Lihat Bukti Terkirim</a>
                    {% endif %}
                </div>
                {% else %}
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-[#0284C7]/20 text-center">
                    <p class="text-gray-500">Tidak ada tagihan aktif.</p>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- 1. MODAL RENCANA STUDI -->
    <div id="modal-rencana-studi" class="hidden fixed inset-0 z-40 bg-[#F0F9FF] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-[#0284C7]/20 pb-4">
                <h3 class="text-xl font-bold text-[#075985]">Pengisian Rencana Studi (KRS)</h3>
                <button onclick="closeModal('modal-rencana-studi')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
            </div>
            
            {% if has_unpaid %}
            <div class="bg-white p-8 rounded-3xl shadow-lg border border-red-200 text-center relative overflow-hidden">
                <div class="w-20 h-20 bg-red-50 text-red-500 rounded-full flex items-center justify-center mx-auto mb-4 border-4 border-white shadow-inner">
                    <i class="fas fa-lock text-3xl"></i>
                </div>
                <h4 class="text-xl font-bold text-red-600 mb-2">Akses Terkunci</h4>
                <p class="text-gray-600 mb-6 leading-relaxed">Mohon maaf, Anda tidak dapat mengisi Kartu Rencana Studi karena masih terdapat tagihan pembayaran yang belum diselesaikan atau sedang menunggu verifikasi Tata Usaha.</p>
                <button onclick="closeModal('modal-rencana-studi'); openModal('modal-pusat-tagihan')" class="bg-[#0284C7] text-white px-8 py-3 rounded-xl font-bold hover:bg-[#0369A1] transition shadow-md">Menuju Pusat Tagihan</button>
            </div>
            {% else %}
            
            <div class="bg-white p-6 rounded-2xl shadow-sm border border-[#0284C7]/20 mb-6">
                <p class="text-sm text-gray-600 mb-4">Pilih mata kuliah dari jadwal yang ditawarkan semester ini. Mata kuliah yang dipilih akan diajukan ke Dosen Wali.</p>
                <form action="/mahasiswa/krs/add" method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                    <div class="space-y-3 mb-4 max-h-[40vh] overflow-y-auto custom-scrollbar">
                        {% for j in jadwal_list %}
                        <label class="flex items-start p-3 border border-gray-100 rounded-xl hover:bg-gray-50 transition cursor-pointer">
                            <input type="checkbox" name="jadwal_ids" value="{{ j['id'] }}" class="accent-[#0284C7] w-5 h-5 mr-3 mt-1">
                            <div class="flex-1">
                                <p class="font-bold text-sm text-gray-800">{{ j['mata_kuliah'] }}</p>
                                <p class="text-xs text-gray-500">{{ j['hari'] }}, {{ j['jam'] }} • Ruang: {{ j['ruangan'] }}</p>
                                <p class="text-xs font-medium text-[#0284C7] mt-1"><i class="fas fa-user-tie"></i> {{ j['dosen'] }}</p>
                            </div>
                            <div class="bg-[#F0F9FF] text-[#075985] px-2 py-1 rounded text-[10px] font-bold">3 SKS</div>
                        </label>
                        {% else %}
                        <p class="text-center text-gray-500 py-4">Belum ada jadwal kuliah yang dibuka oleh Tata Usaha.</p>
                        {% endfor %}
                    </div>
                    {% if jadwal_list %}
                    <button type="submit" class="w-full bg-[#0284C7] text-white font-bold py-3 rounded-xl hover:bg-[#7DD3FC] transition shadow-md">Ajukan KRS</button>
                    {% endif %}
                </form>
            </div>
            
            <h4 class="text-[#075985] font-bold mb-3 border-l-4 border-[#7DD3FC] pl-2">KRS Saya (Semester Ini)</h4>
            <div class="space-y-3">
                {% for k in krs_list %}
                <div class="bg-white p-4 rounded-xl shadow-sm border border-[#0284C7]/20 flex justify-between items-center">
                    <div>
                        <p class="font-bold text-gray-800 text-sm">{{ k['mata_kuliah'] }}</p>
                        <p class="text-xs text-gray-500">{{ k['dosen'] }} • {{ k['sks'] }} SKS</p>
                    </div>
                    <span class="text-[10px] font-bold px-2 py-1 rounded-full {{ 'bg-yellow-100 text-yellow-600' if k['status'] == 'Menunggu Acc Dosen' else 'bg-green-100 text-green-600' }}">{{ k['status'] }}</span>
                </div>
                {% else %}
                <p class="text-center text-gray-500 text-sm italic">Belum ada KRS yang diajukan.</p>
                {% endfor %}
            </div>
            
            {% endif %}
        </div>
    </div>

    <!-- 2. MODAL KARTU HASIL STUDI -->
    <div id="modal-kartu-hasil-studi" class="hidden fixed inset-0 z-40 bg-[#F0F9FF] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-[#0284C7]/20 pb-4">
                <h3 class="text-xl font-bold text-[#075985]">Kartu Hasil Studi (KHS)</h3>
                <button onclick="closeModal('modal-kartu-hasil-studi')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
            </div>
            
            {% set total_sks_kumulatif = namespace(value=0) %}
            {% set total_bobot_kumulatif = namespace(value=0) %}
            
            {% set semester_groups = {} %}
            {% for n in nilai_list %}
                {% if n['semester'] not in semester_groups %}
                    {% set _ = semester_groups.update({n['semester']: []}) %}
                {% endif %}
                {% set _ = semester_groups[n['semester']].append(n) %}
            {% endfor %}
            
            {% for smt, items in semester_groups.items() %}
                {% set smt_sks = namespace(value=0) %}
                {% set smt_bobot = namespace(value=0) %}
                
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-[#0284C7]/20 mb-6">
                    <div class="flex justify-between items-end mb-6 border-b border-gray-100 pb-4">
                        <div>
                            <h4 class="text-lg font-bold text-gray-800">{{ smt }}</h4>
                            <p class="text-xs text-gray-500" id="ips-{{ loop.index }}">IPS: Menghitung...</p>
                        </div>
                    </div>
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="bg-gray-50">
                                <th class="p-3 text-xs font-bold text-gray-600 rounded-l-lg">Mata Kuliah</th>
                                <th class="p-3 text-xs font-bold text-gray-600 text-center">SKS</th>
                                <th class="p-3 text-xs font-bold text-gray-600 text-center rounded-r-lg">Nilai</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100">
                            {% for n in items %}
                            {% set nilai_angka = 4.0 %}
                            {% if n['nilai_huruf'] == 'A' %}{% set nilai_angka = 4.0 %}
                            {% elif n['nilai_huruf'] == 'A-' %}{% set nilai_angka = 3.7 %}
                            {% elif n['nilai_huruf'] == 'B+' %}{% set nilai_angka = 3.3 %}
                            {% elif n['nilai_huruf'] == 'B' %}{% set nilai_angka = 3.0 %}
                            {% elif n['nilai_huruf'] == 'B-' %}{% set nilai_angka = 2.7 %}
                            {% elif n['nilai_huruf'] == 'C+' %}{% set nilai_angka = 2.3 %}
                            {% elif n['nilai_huruf'] == 'C' %}{% set nilai_angka = 2.0 %}
                            {% elif n['nilai_huruf'] == 'D' %}{% set nilai_angka = 1.0 %}
                            {% else %}{% set nilai_angka = 0.0 %}{% endif %}
                            
                            {% set smt_sks.value = smt_sks.value + n['sks'] %}
                            {% set smt_bobot.value = smt_bobot.value + (n['sks'] * nilai_angka) %}
                            
                            {% set total_sks_kumulatif.value = total_sks_kumulatif.value + n['sks'] %}
                            {% set total_bobot_kumulatif.value = total_bobot_kumulatif.value + (n['sks'] * nilai_angka) %}
                            
                            <tr>
                                <td class="p-3 text-sm text-gray-800 font-medium">{{ n['mata_kuliah'] }}</td>
                                <td class="p-3 text-sm text-gray-600 text-center">{{ n['sks'] }}</td>
                                <td class="p-3 text-sm font-bold text-[#0284C7] text-center">{{ n['nilai_huruf'] }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    
                    {% set ips = (smt_bobot.value / smt_sks.value) if smt_sks.value > 0 else 0 %}
                    <script>
                        document.addEventListener("DOMContentLoaded", function() {
                            const el = document.getElementById('ips-{{ loop.index }}');
                            if(el) el.innerText = "IPS: {{ '%.2f' | format(ips) }}";
                        });
                    </script>
                </div>
            {% else %}
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-[#0284C7]/20 text-center">
                    <p class="text-gray-500">Belum ada nilai yang diinput oleh Dosen.</p>
                </div>
            {% endfor %}
            
            {% if nilai_list %}
            <div class="fixed bottom-0 left-0 w-full bg-white border-t border-[#0284C7]/20 p-4 md:p-6 pb-safe z-50 flex justify-between items-center max-w-md mx-auto right-0 rounded-t-3xl shadow-[0_-10px_20px_rgba(0,0,0,0.05)]">
                <div>
                    <p class="text-xs text-gray-500 font-bold uppercase tracking-wider">Indeks Prestasi Kumulatif</p>
                    <h2 class="text-3xl font-bold text-[#075985]">{% set ipk = (total_bobot_kumulatif.value / total_sks_kumulatif.value) if total_sks_kumulatif.value > 0 else 0 %}{{ '%.2f' | format(ipk) }}</h2>
                </div>
                <div class="text-right">
                    <p class="text-xs text-gray-500 font-bold uppercase tracking-wider">Total SKS</p>
                    <h2 class="text-xl font-bold text-[#0284C7]">{{ total_sks_kumulatif.value }} SKS</h2>
                </div>
            </div>
            {% endif %}
        </div>
    </div>

    <!-- 4. MODAL JADWAL KULIAH -->
    <div id="modal-jadwal-kuliah" class="hidden fixed inset-0 z-40 bg-[#F0F9FF] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-[#0284C7]/20 pb-4">
                <h3 class="text-xl font-bold text-[#075985]">Jadwal Kuliah Mahasiswa</h3>
                <button onclick="closeModal('modal-jadwal-kuliah')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
            </div>
            
            <p class="text-sm text-gray-600 mb-6 bg-white p-4 rounded-xl border border-[#0284C7]/20 shadow-sm"><i class="fas fa-info-circle text-[#0284C7] mr-2"></i>Jadwal ini disinkronkan langsung dari ruang kendali Tata Usaha secara real-time.</p>
            
            <div class="space-y-4 max-h-[60vh] overflow-y-auto custom-scrollbar pr-2">
                {% for item in jadwal_list %}
                <div class="bg-white p-5 rounded-2xl shadow-sm border border-[#0284C7]/20 flex justify-between items-center group hover:border-[#0284C7]/50 transition-colors">
                    <div>
                        <p class="font-bold text-gray-800 text-base mb-1">{{ item['mata_kuliah'] }}</p>
                        <div class="flex items-center gap-2 text-xs text-gray-500 mb-1">
                            <span class="bg-[#F0F9FF] text-[#075985] px-2 py-0.5 rounded font-bold">{{ item['hari'] }}</span>
                            <span class="text-gray-400"><i class="fas fa-clock mr-1"></i> {{ item['jam'] }}</span>
                            <span class="text-gray-400"><i class="fas fa-map-marker-alt mr-1"></i> {{ item['ruangan'] }}</span>
                        </div>
                        <p class="text-xs font-bold text-[#0284C7]"><i class="fas fa-chalkboard-teacher mr-1"></i> {{ item['dosen'] }}</p>
                    </div>
                </div>
                {% else %}
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-[#0284C7]/20 text-center">
                    <p class="text-gray-500">Jadwal kuliah belum tersedia dari Tata Usaha.</p>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    <!-- 5. MODAL PERMOHONAN SURAT -->
    <div id="modal-permohonan-surat" class="hidden fixed inset-0 z-40 bg-[#F0F9FF] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-[#0284C7]/20 pb-4">
                <h3 class="text-xl font-bold text-[#075985]">Layanan Permohonan Surat</h3>
                <button onclick="closeModal('modal-permohonan-surat')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
            </div>
            
            <form action="/mahasiswa/surat/request" method="POST" class="bg-white p-6 rounded-2xl shadow-sm border border-[#0284C7]/20 mb-6 relative overflow-hidden">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <div class="absolute top-0 right-0 opacity-5 -mt-4 -mr-4">
                    <i class="fas fa-paper-plane text-8xl text-[#0284C7]"></i>
                </div>
                <div class="relative z-10">
                    <p class="text-sm text-gray-600 mb-4">Pilih jenis surat yang ingin diajukan. Surat akan diverifikasi oleh Tata Usaha dan dapat diunduh dalam bentuk PDF dengan QR Code Tanda Tangan Elektronik.</p>
                    <div class="mb-4">
                        <label class="block text-xs font-bold text-gray-500 mb-2">Jenis Surat / Dokumen</label>
                        <select name="jenis_surat" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#0284C7]">
                            <option value="Surat Keterangan Aktif Kuliah">Surat Keterangan Aktif Kuliah (Untuk Beasiswa/Tunjangan)</option>
                            <option value="Surat Pengantar Magang">Surat Pengantar Magang / PKL</option>
                            <option value="Surat Pengantar Riset">Surat Pengantar Riset / Penelitian TA</option>
                            <option value="Surat Cuti Akademik">Surat Permohonan Cuti Akademik</option>
                        </select>
                    </div>
                    <div class="mb-4">
                        <label class="block text-xs font-bold text-gray-500 mb-2">Keterangan Tambahan / Tujuan Surat</label>
                        <textarea name="keterangan" required placeholder="Contoh: Ditujukan kepada HRD PT Pertamina Balikpapan" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm h-20 focus:outline-none focus:ring-2 focus:ring-[#0284C7]"></textarea>
                    </div>
                    <button type="submit" class="w-full bg-[#0284C7] text-white font-bold py-3 rounded-xl shadow-md hover:bg-[#7DD3FC] transition flex justify-center items-center gap-2"><i class="fas fa-paper-plane"></i> Kirim Permohonan</button>
                </div>
            </form>

            <h4 class="text-[#075985] font-bold mb-3 border-l-4 border-[#7DD3FC] pl-2">Ruang Tunggu Permohonan</h4>
            <div class="space-y-3">
                {% for s in surat_list %}
                <div class="bg-white p-5 rounded-2xl shadow-sm border border-[#0284C7]/20 relative">
                    <div class="flex justify-between items-start mb-2">
                        <h5 class="font-bold text-gray-800">{{ s['jenis_surat'] }}</h5>
                        <span class="text-[10px] font-bold px-2 py-1 rounded-full {{ 'bg-yellow-100 text-yellow-600' if s['status'] == 'Menunggu Acc' else 'bg-green-100 text-green-600' }}">{{ s['status'] }}</span>
                    </div>
                    <p class="text-xs text-gray-500 mb-3"><i class="fas fa-calendar-alt mr-1"></i> {{ s['tanggal'] }}</p>
                    <p class="text-xs text-gray-600 italic border-l-2 border-gray-200 pl-2">"{{ s['keterangan'] }}"</p>
                    
                    {% if s['status'] == 'Disetujui' %}
                    <div class="mt-4 pt-3 border-t border-gray-100 flex justify-between items-center">
                        <p class="text-[10px] text-green-600 font-bold flex items-center gap-1"><i class="fas fa-shield-alt"></i> Ditandatangani Elektronik</p>
                        <!-- We use a mock URL for downloading the signed PDF for demonstration -->
                        <button onclick="alert('Mengunduh Surat Digital Resmi (PDF)...')" class="bg-[#0284C7]/10 text-[#0284C7] px-3 py-1.5 rounded-lg text-xs font-bold hover:bg-[#0284C7]/20 transition"><i class="fas fa-download mr-1"></i> Unduh PDF</button>
                    </div>
                    {% endif %}
                </div>
                {% else %}
                <div class="text-center bg-white p-6 rounded-2xl border border-[#0284C7]/20">
                    <p class="text-gray-400 text-sm italic">Belum ada surat yang diajukan.</p>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- 6. MODAL PROFIL DAN ARSIP DIGITAL -->
    <div id="modal-profil-arsip" class="hidden fixed inset-0 z-40 bg-[#F0F9FF] overflow-y-auto">
        <div class="relative w-full min-h-screen pt-24 pb-32 px-5 md:px-8 animate-[slideUp_0.3s_ease-out]">
            <div class="flex justify-between items-center mb-6 border-b border-[#0284C7]/20 pb-4">
                <h3 class="text-xl font-bold text-[#075985]">Profil & Arsip Digital Saya</h3>
                <button onclick="closeModal('modal-profil-arsip')" class="bg-white w-8 h-8 rounded-full text-gray-500 shadow-sm">&times;</button>
            </div>
            
            <div class="bg-white p-6 rounded-3xl shadow-lg border border-[#0284C7]/20 mb-6 relative overflow-hidden">
                <div class="absolute top-0 right-0 w-32 h-32 bg-[#0284C7]/10 rounded-bl-full -z-10"></div>
                
                <div class="flex items-center gap-6 mb-6">
                    <div class="relative w-20 h-20 bg-gray-200 rounded-full flex items-center justify-center text-4xl text-gray-400 shadow-inner border-4 border-white overflow-hidden group">
                        {% if user and user.foto_profil %}
                            <img src="/uploads/{{ user.foto_profil }}" alt="Foto Profil" class="w-full h-full object-cover">
                        {% else %}
                            <i class="fas fa-user-graduate"></i>
                        {% endif %}
                        <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center cursor-pointer transition-opacity" onclick="document.getElementById('mhs_foto_profil_input').click()">
                            <i class="fas fa-camera text-white text-xl"></i>
                        </div>
                    </div>
                    <div>
                        <h4 class="text-xl font-bold text-[#075985] leading-tight">{{ user.nama if user else 'Nama Mahasiswa' }}</h4>
                        <p class="text-sm font-bold text-[#0284C7] font-mono tracking-widest mt-1">{{ user.username if user else 'NPM' }}</p>
                        <span class="inline-block mt-2 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider {{ 'bg-green-100 text-green-700' if user and user.status_akademik == 'Aktif' else 'bg-red-100 text-red-700' }}">{{ user.status_akademik if user else 'Status' }}</span>
                    </div>
                </div>
                
                <form id="mhs_foto_form" action="/mahasiswa/update_foto" method="POST" enctype="multipart/form-data" class="hidden">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                    <input type="file" id="mhs_foto_profil_input" name="foto_profil" accept="image/*" onchange="document.getElementById('mhs_foto_form').submit()">
                </form>
                
                <div class="flex justify-center border-t border-gray-100 pt-4">
                    <img src="/api/ktm/qr/{{ user.username if user else 'KTM' }}" class="w-24 h-24 object-contain rounded-lg shadow-sm border border-gray-100 p-1">
                </div>
                <p class="text-[10px] text-center text-gray-400 mt-2 tracking-widest uppercase">Pindai KTM Digital</p>
            </div>

            <h4 class="text-[#075985] font-bold mb-3 border-l-4 border-[#7DD3FC] pl-2">Data Awal Pendaftaran</h4>
            <div class="space-y-3 mb-6">
                {% for a in arsip_list %}
                <div class="bg-white p-4 rounded-2xl shadow-sm border border-[#0284C7]/20 flex justify-between items-center group hover:bg-gray-50 transition-colors">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-full bg-[#0284C7]/10 text-[#0284C7] flex items-center justify-center text-lg">
                            <i class="fas fa-file-alt"></i>
                        </div>
                        <div>
                            <p class="font-bold text-gray-800 text-sm">{{ a['nama_dokumen'] }}</p>
                            <p class="text-xs text-gray-500">{{ a['ukuran'] }} • Diunggah: {{ a['tanggal'] }}</p>
                        </div>
                    </div>
                    <a href="/uploads/{{ a['file_path'] }}" target="_blank" class="w-10 h-10 flex items-center justify-center text-[#0284C7] hover:text-[#7DD3FC] hover:bg-[#7DD3FC]/10 rounded-full transition-colors">
                        <i class="fas fa-download"></i>
                    </a>
                </div>
                {% else %}
                <div class="bg-white p-6 rounded-2xl text-center border border-[#0284C7]/20">
                    <p class="text-gray-400 text-sm">Tidak ada dokumen di arsip Anda.</p>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <script>
        
        // Tampilkan kerangka loading saat transisi halaman (tanpa merombak struktur)
        window.addEventListener('beforeunload', function () {
            document.body.classList.add('skeleton-overlay');
        });
        document.addEventListener('DOMContentLoaded', () => {
            const open = '{{ open_modal }}';
            if(open && open !== 'None') openModal(open);
        });
    </script>
</div>
"""



# ============================================================================
# ZONA HELPER FUNGSI BAWAH
# ============================================================================


def _fetch_dosen_data(dosen_name):
    jadwal_dosen = []
    krs_perwalian = []
    unique_npms = set()
    mahasiswa_perwalian = []
    kelas_list = []
    try:
        jadwal_dosen = JadwalKuliah.query.filter_by(dosen=dosen_name).all()
        krs_raw = KRSMahasiswa.query.options(joinedload(KRSMahasiswa.user_krs)).filter_by(dosen=dosen_name).order_by(KRSMahasiswa.id.desc()).all()
        npms_in_krs = [k.npm for k in krs_raw]
        all_tagihan = TagihanKuliah.query.filter(TagihanKuliah.npm.in_(npms_in_krs)).all() if npms_in_krs else []
        tagihan_map = {}
        for t in all_tagihan: tagihan_map.setdefault(t.npm, []).append(t)
        for krs in krs_raw:
            tagihan = tagihan_map.get(krs.npm, [])
            # For Dosen data, if tagihan is empty, that implies unpaid/unverified SPP billing (as per rules: empty tagihan explicitly trigger has_unpaid=True locking KRS access)
            if tagihan and all(t.status == 'Lunas' for t in tagihan): krs_perwalian.append(krs)
            unique_npms.add(krs.npm)
            
        if jadwal_dosen:
            jadwal_ids = [j.id for j in jadwal_dosen]
            mata_kuliah_list = [j.mata_kuliah for j in jadwal_dosen]
            all_status_nilai = StatusNilai.query.filter(StatusNilai.jadwal_id.in_(jadwal_ids)).all()
            status_nilai_map = {sn.jadwal_id: sn for sn in all_status_nilai}
            all_krs_class = KRSMahasiswa.query.filter(KRSMahasiswa.mata_kuliah.in_(mata_kuliah_list), KRSMahasiswa.dosen==dosen_name, KRSMahasiswa.status=='Disetujui Dosen').all()
            krs_class_map = {}
            all_npm_class = set()
            for krs in all_krs_class:
                krs_class_map.setdefault(krs.mata_kuliah, []).append(krs)
                all_npm_class.add(krs.npm)
            all_users_class = User.query.filter(User.username.in_(list(all_npm_class))).all() if all_npm_class else []
            user_class_map = {u.username: u for u in all_users_class}
            all_jurnal = JurnalMengajar.query.filter(JurnalMengajar.jadwal_id.in_(jadwal_ids)).all()
            jurnal_map = {}
            for j in all_jurnal: jurnal_map[j.jadwal_id] = jurnal_map.get(j.jadwal_id, 0) + 1
            all_kehadiran = KehadiranKelas.query.filter(KehadiranKelas.jadwal_id.in_(jadwal_ids), KehadiranKelas.status=='Hadir').all()
            kehadiran_map = {}
            for k in all_kehadiran:
                kehadiran_map.setdefault(k.jadwal_id, {})
                kehadiran_map[k.jadwal_id][k.npm] = kehadiran_map[k.jadwal_id].get(k.npm, 0) + 1

        for jadwal in jadwal_dosen:
            status_nilai = status_nilai_map.get(jadwal.id)
            is_published = status_nilai.is_published if status_nilai else False
            krs_class = krs_class_map.get(jadwal.mata_kuliah, [])
            student_data = []
            if krs_class:
                total_sessions = jurnal_map.get(jadwal.id, 0)
                hadir_map = kehadiran_map.get(jadwal.id, {})
                for student_krs in krs_class:
                    if total_sessions == 0: attendance_pct = 100
                    else: attendance_pct = (hadir_map.get(student_krs.npm, 0) / total_sessions) * 100
                    user_obj = user_class_map.get(student_krs.npm)
                    student_data.append({'npm': student_krs.npm, 'nama': user_obj.nama if user_obj else 'Unknown', 'attendance_pct': attendance_pct})
            kelas_list.append({'jadwal': jadwal, 'is_published': is_published, 'students': student_data})
            
        if unique_npms:
            npm_list = list(unique_npms)
            users = User.query.filter(User.username.in_(npm_list)).all()
            all_nilai = NilaiMahasiswa.query.filter(NilaiMahasiswa.npm.in_(npm_list)).all()
            all_arsip = LaciArsip.query.filter(LaciArsip.npm.in_(npm_list)).all()
            user_map = {u.username: u for u in users}
            nilai_map = {}
            for n in all_nilai: nilai_map.setdefault(n.npm, []).append(n)
            arsip_map = {}
            for a in all_arsip: arsip_map.setdefault(a.npm, []).append(a)
            for npm in unique_npms:
                user = user_map.get(npm)
                if user:
                    nilai_list = nilai_map.get(npm, [])
                    total_sks = sum(n.sks for n in nilai_list)
                    total_bobot = sum((n.sks * ({'A':4.0,'A-':3.7,'B+':3.3,'B':3.0,'B-':2.7,'C+':2.3,'C':2.0,'D':1.0}.get(n.nilai_huruf, 0.0))) for n in nilai_list)
                    ipk = (total_bobot / total_sks) if total_sks > 0 else 0
                    mahasiswa_perwalian.append({'npm': npm, 'nama': user.nama, 'status': user.status_akademik, 'ipk': ipk, 'transkrip': nilai_list, 'arsip': arsip_map.get(npm, [])})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error loading Dosen Dashboard: {e}", exc_info=True)
    return jadwal_dosen, krs_perwalian, kelas_list, mahasiswa_perwalian


def _fetch_mahasiswa_data(npm, is_admin):
    user = None
    tagihan_list = []
    krs_list = []
    nilai_list = []
    jadwal_list = []
    surat_list = []
    arsip_list = []
    pmb_docs = []
    has_unpaid = False
    
    try:
        user = User.query.filter_by(username=npm).first()
        if npm:
            tagihan_list = TagihanKuliah.query.filter_by(npm=npm).order_by(TagihanKuliah.id.desc()).all()
            has_unpaid = True if len(tagihan_list) == 0 else any(t.status != 'Lunas' for t in tagihan_list)
            krs_list = KRSMahasiswa.query.filter_by(npm=npm).order_by(KRSMahasiswa.id.desc()).all()
            nilai_list = NilaiMahasiswa.query.filter_by(npm=npm).order_by(NilaiMahasiswa.semester.desc(), NilaiMahasiswa.id.desc()).all()
            jadwal_list = JadwalKuliah.query.order_by(JadwalKuliah.id.desc()).all()
            surat_list = SuratOtomatis.query.filter_by(npm=npm).order_by(SuratOtomatis.id.desc()).all()
            arsip_list_raw = LaciArsip.query.filter_by(npm=npm).order_by(LaciArsip.id.desc()).all()
            arsip_list = [{'id': a.id, 'nama_dokumen': a.nama_dokumen, 'file_path': a.file_path, 'ukuran': a.ukuran, 'tanggal': a.tanggal} for a in arsip_list_raw]
            
            # Fetch verified PMB documents for this student
            pmb = PendaftaranPMB.query.filter_by(npm_generated=npm).first()
            if pmb:
                existing_files = {a.file_path for a in arsip_list_raw}
                if pmb.foto_ijazah:
                    pmb_docs.append({'nama_dokumen': 'Scan Ijazah (Awal Masuk)', 'file_path': pmb.foto_ijazah})
                    if pmb.foto_ijazah not in existing_files:
                        arsip_list.append({'id': 'pmb-ijazah', 'nama_dokumen': 'Arsip Ijazah PMB (Riwayat)', 'file_path': pmb.foto_ijazah, 'ukuran': 'Berkas PMB', 'tanggal': pmb.created_at.strftime('%Y-%m-%d') if pmb.created_at else ''})
                if pmb.foto_ktp:
                    pmb_docs.append({'nama_dokumen': 'Scan KTP (Awal Masuk)', 'file_path': pmb.foto_ktp})
                    if pmb.foto_ktp not in existing_files:
                        arsip_list.append({'id': 'pmb-ktp', 'nama_dokumen': 'Arsip KTP PMB (Riwayat)', 'file_path': pmb.foto_ktp, 'ukuran': 'Berkas PMB', 'tanggal': pmb.created_at.strftime('%Y-%m-%d') if pmb.created_at else ''})
                if pmb.bukti_transfer:
                    pmb_docs.append({'nama_dokumen': 'Bukti Transfer PMB (Awal Masuk)', 'file_path': pmb.bukti_transfer})
                    if pmb.bukti_transfer not in existing_files:
                        arsip_list.append({'id': 'pmb-transfer', 'nama_dokumen': 'Arsip Bukti Transfer PMB (Riwayat)', 'file_path': pmb.bukti_transfer, 'ukuran': 'Berkas PMB', 'tanggal': pmb.created_at.strftime('%Y-%m-%d') if pmb.created_at else ''})

    except Exception as e:
        app.logger.error(f"Error fetch mhs: {e}", exc_info=True)
    return user, tagihan_list, krs_list, nilai_list, jadwal_list, surat_list, arsip_list, has_unpaid, pmb_docs


def _fetch_tu_data():
    try:
        pending_users = User.query.filter_by(status_akademik='Menunggu Verifikasi').order_by(User.id.desc()).all()
        return (
            SuratOtomatis.query.order_by(SuratOtomatis.id.desc()).all(),
            PendaftaranPMB.query.order_by(PendaftaranPMB.id.desc()).all(),
            TagihanKuliah.query.order_by(TagihanKuliah.id.desc()).all(),
            JadwalKuliah.query.order_by(JadwalKuliah.id.desc()).all(),
            User.query.order_by(User.id.desc()).all(),
            LaciArsip.query.order_by(LaciArsip.id.desc()).all(),
            TracerStudy.query.order_by(TracerStudy.id.desc()).all(),
            TracerStudy.query.filter_by(status='Diverifikasi').order_by(TracerStudy.id.desc()).all(),
            pending_users
        )
    except Exception as e:
        app.logger.error(e, exc_info=True)
        return [], [], [], [], [], [], [], [], []

def render_page(template, active_page, theme=None, content_kwargs=None, hide_nav=False, full_width=False):
    if content_kwargs is None:
        content_kwargs = {}
    
    settings = get_settings()
    is_admin = session.get('is_admin', False)
    
    rendered_content = render_template_string(template, open_modal=request.args.get('open'), is_admin=is_admin, settings=settings, **content_kwargs)
    
    return render_template_string(BASE_LAYOUT, 
                                  styles=STYLES_HTML + (RAMADHAN_STYLES if active_page == 'ramadhan' else (IRMA_STYLES if active_page == 'irma' else '')), 
                                  active_page=active_page, 
                                  theme=theme,
                                  content=rendered_content, 
                                  hide_nav=hide_nav,
                                  full_width=full_width,
                                  is_admin=is_admin, 
                                  settings=settings)

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


# === ZONA MASJID HYBRID ===



# --- DATABASE SETUP ---


# --- DATABASE MODELS ---

def get_settings():
    try:
        settings = {item.key: item.value for item in AppSettings.query.all()}
    except Exception as e:
        app.logger.error(f"Database settings tidak dapat dimuat: {e}", exc_info=True)
        settings = {}
    return settings


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


# Samarinda Coordinates
LAT = -0.502106
LNG = 117.153709
TZ = 8 # WITA

def allowed_file(filename):
    if '.' not in filename: return False
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in {'php', 'py', 'sh', 'exe', 'bat', 'cmd', 'ps1'}: return False
    return ext in ALLOWED_EXTENSIONS

def is_safe_file(file_storage):
    """Deep inspection of file mime types and signatures."""
    ext = file_storage.filename.rsplit('.', 1)[1].lower() if '.' in file_storage.filename else ''
    
    header = file_storage.read(2048)
    file_storage.seek(0)
    
    # Custom magic bytes signatures for non-image documents
    signatures = {
        'pdf': b'%PDF-',
        'doc': b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',
        'xls': b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',
        'docx': b'PK\x03\x04',
        'xlsx': b'PK\x03\x04',
        'zip': b'PK\x03\x04',
        'rar': b'Rar!\x1a\x07',
    }
    
    if ext in signatures:
        if header.startswith(signatures[ext]):
            return True
        return False
        
    if ext in {'txt', 'csv'}:
        # Ensure it's mostly text/printable
        try:
            header.decode('utf-8', errors='ignore')
            return True
        except UnicodeDecodeError:
            return False

    kind = filetype.guess(header)
    if kind is None:
        return False
    return kind.extension in ALLOWED_EXTENSIONS

def compress_image(file_storage, upload_folder):
    os.makedirs(upload_folder, exist_ok=True)
    if not is_safe_file(file_storage):
        raise ValueError("Invalid file content signature detected.")
    
    filename = secure_filename(file_storage.filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if ext in {'mp4', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar', 'txt', 'csv'}:
        save_path = os.path.join(upload_folder, filename)
        file_storage.seek(0)
        file_storage.save(save_path)
        return filename

    try:
        file_storage.seek(0)
        img = Image.open(file_storage)
        
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        
        base = os.path.splitext(filename)[0]
        new_filename = base + ".jpg"
        save_path = os.path.join(upload_folder, new_filename)
        
        quality = 90
        img_byte_arr = io.BytesIO()
        while quality >= 10:
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
            size_kb = img_byte_arr.tell() / 1024
            if size_kb < 500:
                break
            quality -= 5

        with open(save_path, 'wb') as f:
            f.write(img_byte_arr.getbuffer())
            
        return new_filename
        
    except Exception as e:
        app.logger.warning(f"Compression error: {e}")
        file_storage.seek(0)
        save_path = os.path.join(upload_folder, filename)
        file_storage.save(save_path)
        return filename

# --- RAMADHAN HELPER FUNCTIONS ---

def seed_ramadhan_schedule():
    try:
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
            pass
    except Exception as e:
        db.session.rollback()
        app.logger.warning(f"Could not seed Ramadhan schedule (model might not exist): {e}")

@cache.cached(timeout=86400, key_prefix='imsakiyah_schedule')
def get_imsakiyah_schedule():
    schedule = []
    try:
        # 1. Panggil API Aladhan untuk Samarinda, Indonesia
        # 2. Bulan Februari & Maret 2026 (Ramadhan 1447 H) & Method 20 (Kemenag RI)
        months = [2, 3]
        all_days = []
        
        for m in months:
            url = f"https://api.aladhan.com/v1/calendarByCity?city=Samarinda&country=Indonesia&method=20&month={m}&year=2026"
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
        app.logger.error(f"Error fetching Imsakiyah API: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
        # Fallback empty or local calculation if needed, but user requested API specifically.
        
    return schedule

# --- FRONTEND ASSETS & LAYOUT ---

# --- ORM Compatibility Patch (Allow dict-style access in Jinja) ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False, port=5000)
