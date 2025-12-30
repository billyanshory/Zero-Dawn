import os
import sqlite3
import functools
import uuid
from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory, flash, abort, g
from werkzeug.utils import secure_filename
from werkzeug.security import safe_join

# ==========================================
# CONFIGURATION & SECURITY
# ==========================================
app = Flask(__name__)
app.secret_key = os.urandom(64)  # Strong random key for sessions
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB Max Upload
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['DATABASE'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rt53_data.db')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Credentials (HARDCODED AS REQUESTED)
ADMIN_ID = 'Ketua RT. 53'
ADMIN_PASS = 'NKRIhargamati'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ==========================================
# DATABASE HELPERS
# ==========================================
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS kartu_keluarga (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                no_kk TEXT NOT NULL,
                kepala_keluarga TEXT NOT NULL,
                alamat TEXT NOT NULL,
                jumlah_anggota INTEGER NOT NULL,
                foto_path TEXT
            )
        ''')
        db.commit()

# Initialize DB on start
init_db()

# ==========================================
# SECURITY DECORATORS & CSRF
# ==========================================
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = uuid.uuid4().hex
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def csrf_protected(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == "POST":
            token = session.get('_csrf_token')
            if not token or token != request.form.get('_csrf_token'):
                abort(403)
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==========================================
# UI / TEMPLATES (JINJA2 + CSS)
# ==========================================
# Common Base Layout with iLovePDF Style
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bank Data RT. 53 - Secure Vault</title>

    <!-- Fonts & Icons -->
    <link href="https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <style>
        :root {
            --brand-red: #E5322D;
            --brand-red-hover: #c92622;
            --bg-white: #FFFFFF;
            --bg-grey: #F4F4F4;
            --text-dark: #333333;
            --text-light: #666666;
            --shadow: 0 4px 12px rgba(0,0,0,0.08);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Kanit', sans-serif;
            background-color: var(--bg-grey);
            color: var(--text-dark);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* Header */
        header {
            background: var(--bg-white);
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 1000;
        }

        .brand {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--brand-red);
            display: flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
        }

        .nav-items {
            display: flex;
            gap: 15px;
            align-items: center;
        }

        /* Buttons */
        .btn {
            padding: 10px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.2s ease;
            border: none;
            cursor: pointer;
            font-family: 'Kanit', sans-serif;
            font-size: 1rem;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .btn-primary {
            background-color: var(--brand-red);
            color: white;
        }
        .btn-primary:hover {
            background-color: var(--brand-red-hover);
            transform: translateY(-1px);
        }

        .btn-outline {
            border: 2px solid var(--brand-red);
            color: var(--brand-red);
            background: transparent;
        }
        .btn-outline:hover {
            background: rgba(229, 50, 45, 0.05);
        }

        .btn-icon {
            padding: 8px;
            font-size: 1.2rem;
            color: var(--text-light);
            background: transparent;
        }
        .btn-icon:hover { color: var(--brand-red); }

        .btn-sm { padding: 6px 12px; font-size: 0.9rem; }
        .btn-danger { background-color: #333; color: white; } /* Action Black */

        /* Layouts */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            flex: 1;
            width: 100%;
        }

        .card {
            background: var(--bg-white);
            border-radius: 12px;
            padding: 2rem;
            box-shadow: var(--shadow);
            transition: transform 0.2s;
        }

        /* Grid System */
        .grid-2 {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
        }

        /* Login Box */
        .login-box {
            max-width: 450px;
            margin: 4rem auto;
            text-align: center;
        }

        .role-selector {
            display: flex;
            gap: 1rem;
            margin-top: 2rem;
            justify-content: center;
        }

        .form-group {
            margin-bottom: 1.5rem;
            text-align: left;
        }

        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: var(--text-dark);
        }

        input[type="text"], input[type="password"], input[type="number"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 1rem;
            font-family: 'Kanit';
            transition: border-color 0.2s;
        }

        input:focus {
            outline: none;
            border-color: var(--brand-red);
        }

        /* Dashboard Cards */
        .tool-card {
            text-align: center;
            padding: 3rem 2rem;
            cursor: pointer;
            border: 2px solid transparent;
            text-decoration: none;
            color: var(--text-dark);
            display: block;
        }
        .tool-card:hover {
            transform: translateY(-5px);
            border-color: rgba(229, 50, 45, 0.2);
        }
        .tool-icon {
            font-size: 4rem;
            color: var(--brand-red);
            margin-bottom: 1.5rem;
        }

        /* Table */
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        th {
            font-weight: 500;
            color: var(--text-light);
            text-transform: uppercase;
            font-size: 0.85rem;
        }
        tr:hover { background-color: #f9f9f9; }

        /* Gallery */
        .gallery-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1.5rem;
        }
        .img-card {
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            position: relative;
        }
        .img-card img {
            width: 100%;
            height: 150px;
            object-fit: cover;
        }
        .img-actions {
            padding: 10px;
            text-align: center;
        }

        /* Modal / Forms */
        .form-box {
            display: none;
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #eee;
        }
        .show { display: block; }

        /* Flash Messages */
        .flash {
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 6px;
            background: #ffebee;
            color: var(--brand-red);
            border: 1px solid rgba(229, 50, 45, 0.2);
        }
    </style>
</head>
<body>
    <header>
        <a href="/" class="brand">
            <i class="fa-solid fa-folder-closed"></i>
            <span>DataRT.53</span>
        </a>
        <div class="nav-items">
            {% if session.get('role') %}
                <span style="font-weight:500; color: #666;">
                    <i class="fa-solid fa-user-circle"></i>
                    {% if session.role == 'admin' %}Ketua RT. 53{% else %}Warga Biasa{% endif %}
                </span>
                <a href="/logout" class="btn btn-outline btn-sm">Keluar</a>
            {% endif %}
        </div>
    </header>

    <div class="container">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="flash">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </div>

    <footer style="text-align: center; padding: 2rem; color: #999; font-size: 0.9rem;">
        &copy; 2023 Bank Data RT. 53 Sidodadi - Secure System v1.0
    </footer>

    <script>
        function toggleEdit(id, no_kk, kepala, alamat, jml) {
            // Populate form and scroll to it
            const form = document.getElementById('editForm');
            if (!form) return;

            form.style.display = 'block';
            document.getElementById('edit_id').value = id;
            document.getElementById('edit_no_kk').value = no_kk;
            document.getElementById('edit_kepala').value = kepala;
            document.getElementById('edit_alamat').value = alamat;
            document.getElementById('edit_jml').value = jml;

            form.scrollIntoView({behavior: 'smooth'});
        }

        function closeEdit() {
            document.getElementById('editForm').style.display = 'none';
        }
    </script>
</body>
</html>
"""

# LOGIN PAGE
LOGIN_TEMPLATE = """
{% extends "base" %}

{% block content %}
<div class="card login-box">
    <div style="margin-bottom: 2rem;">
        <i class="fa-solid fa-shield-halved" style="font-size: 3rem; color: var(--brand-red);"></i>
    </div>
    <h1 style="margin-bottom: 0.5rem;">Portal Data Kependudukan</h1>
    <p style="color: #666; margin-bottom: 2rem;">RT. 53, Jl. Delima Dalam, Sidodadi, Samarinda Ulu</p>

    {% if not show_admin_form %}
        <div class="role-selector">
            <a href="{{ url_for('login', mode='admin') }}" class="btn btn-primary">
                <i class="fa-solid fa-user-tie"></i> Ketua RT. 53
            </a>
            <a href="{{ url_for('guest_login') }}" class="btn btn-outline">
                <i class="fa-solid fa-users"></i> Warga Biasa
            </a>
        </div>
    {% else %}
        <form method="POST" action="{{ url_for('login_post') }}" style="text-align: left; margin-top: 2rem;">
            <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
            <div class="form-group">
                <label>ID Pengguna</label>
                <input type="text" name="username" placeholder="Masukkan ID Ketua RT" required autofocus>
            </div>
            <div class="form-group">
                <label>Kata Sandi</label>
                <input type="password" name="password" placeholder="Masukkan Kata Sandi" required>
            </div>
            <button type="submit" class="btn btn-primary" style="width: 100%; justify-content: center; padding: 14px;">
                Masuk Sistem
            </button>
            <div style="text-align: center; margin-top: 1rem;">
                <a href="{{ url_for('login') }}" style="color: #666; text-decoration: none;">Kembali</a>
            </div>
        </form>
    {% endif %}
</div>
{% endblock %}
"""

# DASHBOARD PAGE
DASHBOARD_TEMPLATE = """
{% extends "base" %}

{% block content %}
<div style="text-align: center; margin-bottom: 3rem;">
    <h1>Pilih Mode Tampilan Data</h1>
    <p style="color: #666; margin-top: 0.5rem;">Akses basis data kependudukan dengan aman dan cepat.</p>
</div>

<div class="grid-2">
    <a href="{{ url_for('view_images') }}" class="card tool-card">
        <i class="fa-regular fa-images tool-icon"></i>
        <h2>Data Visual</h2>
        <p style="color: #666; margin-top: 0.5rem;">Lihat arsip digital pindaian Kartu Keluarga dalam format gambar.</p>
    </a>

    <a href="{{ url_for('view_table') }}" class="card tool-card">
        <i class="fa-solid fa-table-list tool-icon"></i>
        <h2>Data Tabulasi</h2>
        <p style="color: #666; margin-top: 0.5rem;">Lihat, cari, dan kelola data terperinci dalam format tabel.</p>
    </a>
</div>
{% endblock %}
"""

# TABLE VIEW
TABLE_TEMPLATE = """
{% extends "base" %}

{% block content %}
<div class="card">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
        <div>
            <h2>Data Kependudukan (Tabel)</h2>
            <p style="color: #666;">Total Data Terinput: {{ total }} Kepala Keluarga</p>
        </div>
        {% if session.role == 'admin' %}
            <button onclick="document.getElementById('addForm').style.display='block'; closeEdit();" class="btn btn-primary">
                <i class="fa-solid fa-plus"></i> Tambah Data
            </button>
        {% endif %}
    </div>

    <!-- ADD FORM -->
    <div id="addForm" class="form-box">
        <h3 style="margin-bottom: 15px;">Input Data Baru</h3>
        <form method="POST" action="{{ url_for('add_data') }}">
            <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div class="form-group">
                    <label>Nomor KK</label>
                    <input type="text" name="no_kk" required>
                </div>
                <div class="form-group">
                    <label>Kepala Keluarga</label>
                    <input type="text" name="kepala_keluarga" required>
                </div>
                <div class="form-group">
                    <label>Alamat</label>
                    <input type="text" name="alamat" required>
                </div>
                <div class="form-group">
                    <label>Jumlah Anggota</label>
                    <input type="number" name="jumlah_anggota" required>
                </div>
            </div>
            <div style="margin-top: 15px; display: flex; gap: 10px;">
                <button type="submit" class="btn btn-primary">Simpan Data</button>
                <button type="button" onclick="document.getElementById('addForm').style.display='none'" class="btn btn-outline">Batal</button>
            </div>
        </form>
    </div>

    <!-- EDIT FORM -->
    <div id="editForm" class="form-box" style="border-left: 5px solid var(--brand-red);">
        <h3 style="margin-bottom: 15px;">Edit Data</h3>
        <form method="POST" action="{{ url_for('edit_data') }}">
            <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
            <input type="hidden" id="edit_id" name="id">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div class="form-group">
                    <label>Nomor KK</label>
                    <input type="text" id="edit_no_kk" name="no_kk" required>
                </div>
                <div class="form-group">
                    <label>Kepala Keluarga</label>
                    <input type="text" id="edit_kepala" name="kepala_keluarga" required>
                </div>
                <div class="form-group">
                    <label>Alamat</label>
                    <input type="text" id="edit_alamat" name="alamat" required>
                </div>
                <div class="form-group">
                    <label>Jumlah Anggota</label>
                    <input type="number" id="edit_jml" name="jumlah_anggota" required>
                </div>
            </div>
            <div style="margin-top: 15px; display: flex; gap: 10px;">
                <button type="submit" class="btn btn-primary">Update Data</button>
                <button type="button" onclick="closeEdit()" class="btn btn-outline">Batal</button>
            </div>
        </form>
    </div>

    <div style="overflow-x: auto;">
        <table>
            <thead>
                <tr>
                    <th>No. KK</th>
                    <th>Kepala Keluarga</th>
                    <th>Alamat</th>
                    <th>Jml Anggota</th>
                    {% if session.role == 'admin' %}
                    <th style="text-align: right;">Aksi</th>
                    {% endif %}
                </tr>
            </thead>
            <tbody>
                {% for row in data %}
                <tr>
                    <td style="font-weight: 500;">{{ row.no_kk }}</td>
                    <td>{{ row.kepala_keluarga }}</td>
                    <td>{{ row.alamat }}</td>
                    <td>{{ row.jumlah_anggota }}</td>
                    {% if session.role == 'admin' %}
                    <td style="text-align: right;">
                        <button class="btn-icon" onclick="toggleEdit('{{ row.id }}', '{{ row.no_kk }}', '{{ row.kepala_keluarga }}', '{{ row.alamat }}', '{{ row.jumlah_anggota }}')" title="Edit">
                            <i class="fa-solid fa-pen-to-square"></i>
                        </button>
                        <form action="{{ url_for('delete_data', id=row.id) }}" method="POST" style="display: inline;" onsubmit="return confirm('Hapus data ini?');">
                            <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
                            <button type="submit" class="btn-icon" style="color: #E5322D;" title="Hapus"><i class="fa-solid fa-trash"></i></button>
                        </form>
                    </td>
                    {% endif %}
                </tr>
                {% else %}
                <tr>
                    <td colspan="5" style="text-align: center; padding: 2rem; color: #999;">Belum ada data tabulasi tersedia.</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
"""

# GALLERY VIEW
GALLERY_TEMPLATE = """
{% extends "base" %}

{% block content %}
<div class="card">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
        <div>
            <h2>Arsip Visual (Scan KK)</h2>
            <p style="color: #666;">Galeri Foto Dokumen Fisik</p>
        </div>
        {% if session.role == 'admin' %}
            <button onclick="document.getElementById('uploadForm').style.display='block'" class="btn btn-primary">
                <i class="fa-solid fa-cloud-arrow-up"></i> Upload Foto
            </button>
        {% endif %}
    </div>

    {% if session.role == 'admin' %}
    <div id="uploadForm" class="form-box">
        <h3 style="margin-bottom: 15px;">Upload Dokumen Baru</h3>
        <form method="POST" action="{{ url_for('upload_image') }}" enctype="multipart/form-data">
            <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
            <div class="form-group">
                <label>Pilih File Gambar (JPG/PNG)</label>
                <input type="file" name="file" accept="image/*" required style="padding: 10px; background: white;">
            </div>
            <div class="form-group">
                <label>Keterangan (Opsional - Nama KK)</label>
                <input type="text" name="keterangan" placeholder="Contoh: KK Bpk. Santoso">
            </div>
            <div style="margin-top: 15px; display: flex; gap: 10px;">
                <button type="submit" class="btn btn-primary">Mulai Upload</button>
                <button type="button" onclick="document.getElementById('uploadForm').style.display='none'" class="btn btn-outline">Batal</button>
            </div>
        </form>
    </div>
    {% endif %}

    <div class="gallery-grid">
        {% for row in data %}
            <div class="img-card">
                <a href="{{ url_for('uploaded_file', filename=row.foto_path) }}" target="_blank">
                    <img src="{{ url_for('uploaded_file', filename=row.foto_path) }}" alt="Dokumen KK">
                </a>
                <div class="img-actions">
                    <p style="font-size: 0.9rem; font-weight: 500; margin-bottom: 5px;">{{ row.kepala_keluarga }}</p>
                    {% if session.role == 'admin' %}
                        <form action="{{ url_for('delete_image', id=row.id) }}" method="POST" onsubmit="return confirm('Hapus gambar ini?');">
                            <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
                            <button type="submit" class="btn btn-sm btn-danger" style="width: 100%;">Hapus</button>
                        </form>
                    {% endif %}
                </div>
            </div>
        {% else %}
            <p style="grid-column: 1/-1; text-align: center; color: #999;">Tidak ada dokumen gambar tersimpan.</p>
        {% endfor %}
    </div>
</div>
{% endblock %}
"""

# ==========================================
# ROUTING LOGIC
# ==========================================
@app.route('/')
def index():
    if 'role' in session:
        return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_TEMPLATE.replace('{% extends "base" %}', BASE_LAYOUT), show_admin_form=False)

@app.route('/login', methods=['GET'])
def login():
    mode = request.args.get('mode')
    if mode == 'admin':
        return render_template_string(LOGIN_TEMPLATE.replace('{% extends "base" %}', BASE_LAYOUT), show_admin_form=True)
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
@csrf_protected
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    if username == ADMIN_ID and password == ADMIN_PASS:
        session['role'] = 'admin'
        session.permanent = True
        return redirect(url_for('dashboard'))
    else:
        flash('Akses Ditolak: ID atau Password Salah!')
        return redirect(url_for('login', mode='admin'))

@app.route('/guest_login')
def guest_login():
    session['role'] = 'guest'
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template_string(DASHBOARD_TEMPLATE.replace('{% extends "base" %}', BASE_LAYOUT))

@app.route('/view/table')
@login_required
def view_table():
    db = get_db()
    # Only show records that don't have images (assuming Tabular mode is for pure data)
    # OR show all, but filter out pure uploads if desired.
    # Current requirement: "melihat data langsung dalam bentuk tabulasi" (input by Admin).
    # We filter out records where 'foto_path' IS NOT NULL to keep views clean.
    cur = db.execute('SELECT * FROM kartu_keluarga WHERE foto_path IS NULL ORDER BY id DESC')
    data = cur.fetchall()
    return render_template_string(TABLE_TEMPLATE.replace('{% extends "base" %}', BASE_LAYOUT), data=data, total=len(data))

@app.route('/view/images')
@login_required
def view_images():
    db = get_db()
    # Fetch entries that have images
    cur = db.execute('SELECT * FROM kartu_keluarga WHERE foto_path IS NOT NULL ORDER BY id DESC')
    data = cur.fetchall()
    return render_template_string(GALLERY_TEMPLATE.replace('{% extends "base" %}', BASE_LAYOUT), data=data)

# ==========================================
# CRUD ACTIONS (ADMIN ONLY)
# ==========================================
@app.route('/add', methods=['POST'])
@admin_required
@csrf_protected
def add_data():
    no_kk = request.form['no_kk']
    kepala = request.form['kepala_keluarga']
    alamat = request.form['alamat']
    jml = request.form['jumlah_anggota']

    db = get_db()
    db.execute('INSERT INTO kartu_keluarga (no_kk, kepala_keluarga, alamat, jumlah_anggota, foto_path) VALUES (?, ?, ?, ?, NULL)',
               (no_kk, kepala, alamat, jml))
    db.commit()
    flash('Data berhasil disimpan.')
    return redirect(url_for('view_table'))

@app.route('/edit', methods=['POST'])
@admin_required
@csrf_protected
def edit_data():
    id_ = request.form['id']
    no_kk = request.form['no_kk']
    kepala = request.form['kepala_keluarga']
    alamat = request.form['alamat']
    jml = request.form['jumlah_anggota']

    db = get_db()
    db.execute('''
        UPDATE kartu_keluarga
        SET no_kk = ?, kepala_keluarga = ?, alamat = ?, jumlah_anggota = ?
        WHERE id = ?
    ''', (no_kk, kepala, alamat, jml, id_))
    db.commit()
    flash('Data berhasil diperbarui.')
    return redirect(url_for('view_table'))

@app.route('/delete/<int:id>', methods=['POST'])
@admin_required
@csrf_protected
def delete_data(id):
    db = get_db()
    db.execute('DELETE FROM kartu_keluarga WHERE id = ?', (id,))
    db.commit()
    flash('Data berhasil dihapus.')
    return redirect(url_for('view_table'))

@app.route('/upload', methods=['POST'])
@admin_required
@csrf_protected
def upload_image():
    if 'file' not in request.files:
        flash('Tidak ada file dipilih')
        return redirect(url_for('view_images'))

    file = request.files['file']
    keterangan = request.form.get('keterangan', 'Dokumen Tanpa Nama')

    if file.filename == '':
        flash('Nama file kosong')
        return redirect(url_for('view_images'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))

        # Save to DB as a new entry (Visual Only)
        db = get_db()
        db.execute('INSERT INTO kartu_keluarga (no_kk, kepala_keluarga, alamat, jumlah_anggota, foto_path) VALUES (?, ?, ?, ?, ?)',
                   ('-', keterangan, '-', 0, unique_name))
        db.commit()

        flash('Foto berhasil diupload.')
        return redirect(url_for('view_images'))
    else:
        flash('Format file tidak diizinkan. Gunakan JPG/PNG.')
        return redirect(url_for('view_images'))

@app.route('/delete_image/<int:id>', methods=['POST'])
@admin_required
@csrf_protected
def delete_image(id):
    db = get_db()
    cur = db.execute('SELECT foto_path FROM kartu_keluarga WHERE id = ?', (id,))
    row = cur.fetchone()
    if row and row['foto_path']:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], row['foto_path']))
        except OSError:
            pass # File might already be gone

    db.execute('DELETE FROM kartu_keluarga WHERE id = ?', (id,))
    db.commit()
    flash('Gambar dihapus.')
    return redirect(url_for('view_images'))

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ==========================================
# MAIN ENTRY
# ==========================================
if __name__ == '__main__':
    app.run(debug=True)
