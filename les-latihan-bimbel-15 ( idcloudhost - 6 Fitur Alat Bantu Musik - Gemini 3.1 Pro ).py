import os
from dotenv import load_dotenv
load_dotenv()
import datetime
from flask import Flask, request, send_from_directory, render_template_string, redirect, url_for, Response, jsonify
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy

# --- KONFIGURASI FLASK ---
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB Limit
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff', 'ico', 'svg', 'mp3', 'wav', 'ogg', 'mp4', 'webm', 'm4a', 'flac', 'srt', 'vtt'}

# --- DATABASE SETUP ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///bimbel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELS ---
class BaseModel(db.Model):
    __abstract__ = True
    def __getitem__(self, item):
        return getattr(self, item)

class Gallery(BaseModel):
    __tablename__ = 'gallery'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    image = db.Column(db.Text, nullable=False)
    student_name = db.Column(db.Text, nullable=False)
    title = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Tutors(BaseModel):
    __tablename__ = 'tutors'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    image = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)
    bio = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Pricing(BaseModel):
    __tablename__ = 'pricing'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text, nullable=False)
    price = db.Column(db.Text, nullable=False)
    details = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Slots(BaseModel):
    __tablename__ = 'slots'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    day = db.Column(db.Text, nullable=False)
    time = db.Column(db.Text, nullable=False)
    status = db.Column(db.Text, default='Available')
    type = db.Column(db.Text, default='General')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class JoinRequests(BaseModel):
    __tablename__ = 'join_requests'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    interest = db.Column(db.Text, nullable=False)
    whatsapp = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class News(BaseModel):
    __tablename__ = 'news'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.Text, nullable=False)
    image = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Ensure tables are created
with app.app_context():
    db.create_all()

# --- PWA CONFIGURATION ---
MANIFEST_CONTENT = """
{
  "name": "LES BIMBEL GAMBAR & MUSIK",
  "short_name": "lesbimbel",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#E5322D",
  "icons": [
    {
      "src": "/uploads/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/uploads/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
"""

SW_CONTENT = """
self.addEventListener('install', (e) => {
  console.log('[Service Worker] Install');
});
self.addEventListener('fetch', (e) => {
  e.respondWith(fetch(e.request));
});
"""

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- FRONTEND (HTML/CSS/JS) ---

# Navbar fragment to reuse
NAVBAR_HTML = """
    <style>
        .navbar {
            background-color: transparent !important;
            box-shadow: none !important;
            padding-top: 20px;
            z-index: 1020;
        }
        .navbar-box {
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 30px;
            padding: 10px 20px;
            border: 1px solid rgba(255,255,255,0.2);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .navbar-brand {
             /* Pink Sage Gradient: Sage Green (#9DC183) to Pastel Pink (#FFD1DC) */
             background: linear-gradient(to right, #9DC183, #FFD1DC, #9DC183);
             background-size: 200% auto;
             -webkit-background-clip: text;
             -webkit-text-fill-color: transparent;
             text-shadow: 0 0 10px rgba(255,255,255,0.2);
             font-weight: 800;
             animation: shine 5s linear infinite;
        }
        @keyframes shine {
            to {
                background-position: 200% center;
            }
        }
        
        .nav-icon-btn {
            width: 45px;
            height: 45px;
            border-radius: 50%;
            border: 2px solid rgba(255,255,255,0.5);
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(5px);
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            transition: all 0.3s ease;
            color: rgba(255,255,255,0.8);
            text-decoration: none;
            overflow: hidden;
        }
        .nav-icon-btn:hover {
            background: rgba(255,255,255,0.3);
            border-color: white;
            color: white;
            transform: scale(1.05);
            box-shadow: 0 0 10px rgba(255,255,255,0.5);
        }
        
        .nav-icon-btn img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .nav-icon-btn i {
            font-size: 1.1rem;
        }

        /* Menu Overlay Styles */
        .menu-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 9999;
            background: rgba(0,0,0,0.5);
            backdrop-filter: blur(5px);
            display: none;
            justify-content: center;
            align-items: center;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        .menu-overlay.active {
            opacity: 1;
        }
        .menu-card {
            position: fixed;
            top: 20px;
            left: 20px;
            right: 20px;
            bottom: 20px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(30px);
            -webkit-backdrop-filter: blur(30px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            border-radius: 30px;
            display: flex;
            flex-direction: column;
            padding: 40px;
            color: white;
        }
        .close-btn {
            position: absolute;
            top: 20px;
            right: 20px;
            background: none;
            border: none;
            color: white;
            font-size: 2rem;
            cursor: pointer;
            opacity: 0.7;
            transition: 0.2s;
        }
        .close-btn:hover {
            opacity: 1;
            transform: scale(1.1);
        }
        .menu-btn {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            padding: 15px 20px;
            border-radius: 15px;
            margin-bottom: 15px;
            cursor: pointer;
            display: flex;
            align-items: center;
            font-size: 1.2rem;
            transition: 0.2s;
            color: white;
            text-decoration: none;
        }
        .menu-btn:hover {
            background: rgba(255,255,255,0.2);
            transform: translateX(5px);
        }
    </style>
    <nav class="navbar navbar-expand-lg">
        <div class="container">
            <div class="navbar-box">
                <!-- 1. Logo (Left) -->
                <form action="/upload-logo" method="post" enctype="multipart/form-data" id="logo-form" style="margin: 0; margin-right: 15px;">
                    <input type="file" name="logo" id="logo-file" hidden onchange="document.getElementById('logo-form').submit()" accept="image/*">
                    <div class="nav-icon-btn" onclick="document.getElementById('logo-file').click()" title="Upload Website Logo">
                        {% if logo_file %}
                            <img src="/uploads/{{ logo_file }}" alt="Logo">
                        {% else %}
                            <i class="fas fa-camera"></i>
                        {% endif %}
                    </div>
                </form>

                <!-- 2. Brand (Center/Left) -->
                <a class="navbar-brand me-auto" href="/">LES BIMBEL GAMBAR & MUSIK</a>
                
                <!-- 3. Hamburger Menu (Right) -->
                <button class="nav-icon-btn" onclick="toggleMenu()" style="border: none; background: transparent; color: white; display: flex;">
                    <i class="fas fa-bars" style="font-size: 1.5rem;"></i>
                </button>
            </div>
        </div>
    </nav>

    <!-- Menu Overlay -->
    <div id="menuOverlay" class="menu-overlay">
        <div class="menu-card glass-panel">
            <button class="close-btn" onclick="toggleMenu()">&times;</button>
            
            <h2 class="text-white fw-bold mb-5 ps-2 border-start border-4 border-light">Menu</h2>
            
            <div class="menu-items">
                <!-- Wallpaper Upload -->
                <form action="/wallpaper-blur/upload" method="post" enctype="multipart/form-data" id="nav-wall-form" style="margin: 0; width: 100%;">
                    <input type="file" name="background" id="nav-wall-file" hidden onchange="document.getElementById('nav-wall-form').submit()" accept="image/*">
                    <div class="menu-btn" onclick="document.getElementById('nav-wall-file').click()">
                        <i class="fas fa-image me-3"></i> Set Wallpaper
                    </div>
                </form>

                <!-- PWA Install Button -->
                <div id="pwa-install-btn-menu" class="menu-btn" style="display: flex;">
                    <i class="fas fa-download me-3"></i> Install App
                </div>
            </div>
        </div>
    </div>

    <script>
        function toggleMenu() {
            const overlay = document.getElementById('menuOverlay');
            if (overlay.style.display === 'flex') {
                overlay.classList.remove('active');
                setTimeout(() => { overlay.style.display = 'none'; }, 300);
            } else {
                overlay.style.display = 'flex';
                // Force reflow
                void overlay.offsetWidth; 
                overlay.classList.add('active');
            }
        }
    </script>
"""

# Base styles fragment to reuse
STYLES_HTML = """
    <style>
        :root {
            --brand-color: #E5322D; /* iLovePDF Red */
            --brand-hover: #c41b17;
            --bg-light: #f4f7fa;
            --card-bg: #ffffff;
            --text-dark: #333333;
            --text-muted: #666666;
            --glass-bg: rgba(255, 255, 255, 0.1);
            --glass-border: rgba(255, 255, 255, 0.2);
            --glass-blur: blur(20px);
        }

        [data-bs-theme="dark"] {
            --bg-light: #1a1a1a;
            --card-bg: #2d2d2d;
            --text-dark: #f1f1f1;
            --text-muted: #aaaaaa;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-light);
            color: var(--text-dark);
            transition: background-color 0.3s ease;
            padding-bottom: 120px !important; /* Ensure footer is visible above bottom nav */
        }
        
        /* Glassmorphism Utilities */
        .glass-panel {
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur);
            -webkit-backdrop-filter: var(--glass-blur);
            border: 1px solid var(--glass-border);
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        }

        /* NAVBAR */
        .navbar {
            background-color: var(--card-bg);
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            padding: 0.8rem 0;
        }
        .navbar-brand {
            font-weight: 800;
            font-size: 1.8rem;
            /* User request: "our" permanently white */
            color: white !important;
            letter-spacing: -1px;
        }
        /* Override any theme specific colors for the logo text part 'our' */
        [data-bs-theme="light"] .navbar-brand {
             color: white !important;
        }
        .navbar-brand span { color: var(--brand-color); }
        
        .btn-brand {
            background-color: var(--brand-color);
            color: white;
            font-weight: 600;
            border-radius: 6px;
            padding: 8px 20px;
            border: none;
            transition: 0.2s;
        }
        .btn-brand:hover { background-color: var(--brand-hover); color: white; }

        /* HERO */
        .hero {
            text-align: center;
            padding: 60px 20px 40px;
        }
        .hero h1 {
            font-weight: 800;
            font-size: 2.8rem;
            margin-bottom: 15px;
            color: var(--text-dark);
        }
        .hero p {
            font-size: 1.25rem;
            color: var(--text-muted);
            max-width: 800px;
            margin: 0 auto;
            font-weight: 300;
        }

        /* TOOL CARDS GRID */
        .tools-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }

        .tool-card {
            background-color: var(--card-bg);
            border-radius: 12px;
            padding: 30px 20px;
            text-decoration: none;
            color: var(--text-dark);
            transition: transform 0.2s, box-shadow 0.2s;
            border: 1px solid transparent;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            height: 100%;
        }

        .tool-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.08);
            border-color: rgba(229, 50, 45, 0.2);
        }

        .tool-icon {
            font-size: 2.5rem;
            color: var(--brand-color);
            margin-bottom: 20px;
        }

        .tool-title {
            font-weight: 700;
            font-size: 1.2rem;
            margin-bottom: 8px;
        }

        .tool-desc {
            font-size: 0.9rem;
            color: var(--text-muted);
            line-height: 1.4;
        }

        /* MODAL UPLOAD */
        .modal-content {
            background-color: var(--card-bg);
            border: none;
            border-radius: 16px;
        }
        
        .upload-zone {
            border: 2px dashed #ccc;
            border-radius: 12px;
            padding: 60px 20px;
            text-align: center;
            background-color: var(--bg-light);
            cursor: pointer;
            transition: 0.3s;
        }
        .upload-zone:hover {
            border-color: var(--brand-color);
            background-color: rgba(229, 50, 45, 0.05);
        }
        
        /* FOOTER */
        footer {
            background-color: var(--card-bg);
            padding: 40px 0;
            margin-top: 60px;
            border-top: 1px solid rgba(0,0,0,0.05);
            text-align: center;
            color: var(--text-muted);
        }

        /* OPTIONS PANEL (Inside Modal) */
        .options-panel {
            text-align: left;
            margin-top: 20px;
            padding: 15px;
            background: var(--bg-light);
            border-radius: 8px;
            display: none; /* Hidden by default */
        }
        
        /* GENERAL UTILS */
        .container-xl {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        /* --- HARD ACRYLIC MODAL STYLES --- */
        .hard-acrylic-modal .modal-dialog {
            max-width: 95vw;
            margin: 2.5vh auto;
            height: 95vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .hard-acrylic-modal .modal-content {
            width: 100%;
            height: 100%;
            background: rgba(30, 30, 30, 0.85); /* Hard acrylic */
            backdrop-filter: blur(25px) saturate(180%);
            -webkit-backdrop-filter: blur(25px) saturate(180%);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 20px;
            box-shadow: 0 0 50px rgba(0,0,0,0.6);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        
        .hard-acrylic-modal .modal-header {
            background: rgba(255, 255, 255, 0.1);
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            padding: 20px;
        }
        
        .hard-acrylic-modal .modal-body {
            overflow-y: auto;
            padding: 30px;
            scrollbar-width: thin;
            scrollbar-color: rgba(255,255,255,0.5) transparent;
        }
        
        .hard-acrylic-modal .modal-footer {
            background: rgba(255, 255, 255, 0.05);
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            padding: 20px;
        }
        
        .hard-acrylic-modal input, 
        .hard-acrylic-modal textarea, 
        .hard-acrylic-modal select {
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            color: white !important;
            border-radius: 12px;
            padding: 15px;
            font-size: 1rem;
        }
        
        .hard-acrylic-modal input:focus, 
        .hard-acrylic-modal textarea:focus, 
        .hard-acrylic-modal select:focus {
            background: rgba(255, 255, 255, 0.2) !important;
            box-shadow: 0 0 15px rgba(255, 255, 255, 0.3);
            outline: none;
            border-color: rgba(255, 255, 255, 0.8) !important;
        }
        
        .hard-acrylic-modal label {
            font-weight: 600;
            margin-bottom: 8px;
            color: rgba(255, 255, 255, 0.9);
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
            font-size: 0.95rem;
        }
        
        /* TOP NAV (Feature Buttons) */
        .top-feature-nav {
            display: flex;
            gap: 15px;
            overflow-x: auto;
            padding: 15px 5px;
            margin-top: 10px;
            margin-bottom: 20px;
            scrollbar-width: none; /* Firefox */
            -ms-overflow-style: none;  /* IE 10+ */
        }
        .top-feature-nav::-webkit-scrollbar { 
            display: none;  /* Chrome/Safari */
        }
        
        .feature-btn {
            flex: 0 0 auto;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            width: 100px;
            height: 100px;
            border-radius: 16px;
            text-decoration: none;
            color: white;
            transition: all 0.3s ease;
            text-align: center;
            padding: 10px;
            font-size: 0.8rem;
            font-weight: 600;
            background: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .feature-btn:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.25);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            color: white;
        }
        
        .feature-btn i, .feature-btn .icon {
            font-size: 2rem;
            margin-bottom: 8px;
            display: block;
        }

        /* BOTTOM NAV */
        .bottom-nav {
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            width: 100% !important;
            min-height: 80px; /* Allow growth */
            height: auto;
            z-index: 99999 !important; /* Ensure on top */
            display: flex;
            justify-content: flex-start;
            overflow-x: auto;
            flex-wrap: nowrap;
            gap: 15px;
            scrollbar-width: none;
            align-items: center;
            padding: 10px 0;
            padding-bottom: calc(10px + env(safe-area-inset-bottom)) !important;
            background: rgba(255, 255, 255, 0.1) !important; /* Clear transparent */
            backdrop-filter: blur(10px) !important; /* Modern Cool Blur */
            border-top: 1px solid rgba(255,255,255,0.2);
            box-shadow: 0 -5px 15px rgba(0,0,0,0.1);
        }
        
        .bottom-nav::-webkit-scrollbar { 
            display: none;
        }
        
        .bottom-nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-decoration: none;
            color: rgba(255,255,255,0.7);
            transition: 0.3s;
            font-size: 0.8rem;
            padding: 5px;
            flex: 0 0 85px;
        }
        
        .bottom-nav-item span {
            display: block !important;
            font-size: 0.75rem;
            margin-top: 4px;
            font-weight: 600;
            text-align: center;
            line-height: 1.2;
        }
        
        .bottom-nav-item i {
            font-size: 1.5rem;
            margin-bottom: 5px;
            background: rgba(255,255,255,0.1);
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            border: 1px solid rgba(255,255,255,0.2);
            transition: 0.3s;
        }
        
        .bottom-nav-item:hover i, .bottom-nav-item.active i {
            background: #9DC183; /* Sage Green */
            color: white;
            box-shadow: 0 0 15px #9DC183, 0 0 30px rgba(157, 193, 131, 0.4);
            transform: translateY(-5px);
            border-color: #9DC183;
        }
        
        .bottom-nav-item:hover {
            color: white;
        }
        
        /* FOOTER VISIBILITY FIX */
        .main-footer {
            margin-bottom: 20px;
        }

    </style>
"""

HEAD_HTML = """
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LES BIMBEL GAMBAR & MUSIK</title>
    <link rel="manifest" href="/manifest.json">
    <link rel="icon" href="{{ url_for('static', filename='logobimbel.PNG') }}">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    {{ styles|safe }}
</head>
"""

BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="light">
{{ head|safe }}
<body>
    <div class="wallpaper-bg" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-image: url('/uploads/{{ bg_image }}'); background-size: cover; background-position: center; z-index: -2;"></div>
    <div class="acrylic-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.47); backdrop-filter: blur(20px) saturate(125%); -webkit-backdrop-filter: blur(20px) saturate(125%); z-index: -1;"></div>
    
    <div class="content-wrapper" style="position: relative; z-index: 1; min-height: 100vh; display: flex; flex-direction: column;">
        
        <div class="fixed-top-header" style="position: fixed; top: 0; left: 0; width: 100%; z-index: 1030; background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-bottom: 1px solid rgba(255,255,255,0.2);">
            {{ navbar|safe }}
            
            <!-- Top Feature Navigation -->
            <div class="container">
                <div class="top-feature-nav">
                    <a href="/gallery" class="feature-btn glass-panel">
                        <i class="fas fa-palette"></i>
                        Galeri
                    </a>
                    <a href="/tutors" class="feature-btn glass-panel">
                        <i class="fas fa-chalkboard-teacher"></i>
                        Pengajar
                    </a>
                    <a href="/pricing" class="feature-btn glass-panel">
                        <i class="fas fa-tags"></i>
                        Biaya
                    </a>
                    <a href="/slots" class="feature-btn glass-panel">
                        <i class="fas fa-calendar-alt"></i>
                        Jadwal
                    </a>
                    <a href="/join" class="feature-btn glass-panel">
                        <i class="fas fa-file-signature"></i>
                        Daftar
                    </a>
                    <a href="/news" class="feature-btn glass-panel">
                        <i class="fas fa-trophy"></i>
                        Prestasi
                    </a>
                </div>
            </div>
        </div>

        <div class="container main-content" style="flex: 1; padding-top: 240px;">
            {{ content|safe }}
        </div>
        
        <footer class="main-footer" style="background: transparent; border: none; color: rgba(255,255,255,0.7); padding: 20px; text-align: center;">
            <div class="container">
                <p>&copy; 2026 LES BIMBEL GAMBAR & MUSIK - All Rights Reserved. "We Making The Time"</p>
            </div>
        </footer>
    </div>

    <!-- Bottom Navigation -->
    <div class="bottom-nav glass-panel">
        <a href="/" class="bottom-nav-item">
            <i class="fas fa-music"></i>
            <span>Home</span>
        </a>
        <a href="/metronome" class="bottom-nav-item">
            <i class="fas fa-stopwatch"></i>
            <span>Metronome</span>
        </a>
        <a href="/ear-training" class="bottom-nav-item">
            <i class="fas fa-ear-listen"></i>
            <span>Ear Training</span>
        </a>
        <a href="/rhythm-trainer" class="bottom-nav-item">
            <i class="fas fa-drum"></i>
            <span>Ritme</span>
        </a>
        <a href="/visual-chord" class="bottom-nav-item">
            <i class="fas fa-keyboard"></i>
            <span>Chord</span>
        </a>
        <a href="/vocal-detector" class="bottom-nav-item">
            <i class="fas fa-microphone"></i>
            <span>Vokal</span>
        </a>
        <a href="/recording-studio" class="bottom-nav-item">
            <i class="fas fa-video"></i>
            <span>Rekaman</span>
        </a>
        <a href="/scrolling-sheet" class="bottom-nav-item">
            <i class="fas fa-scroll"></i>
            <span>Partitur</span>
        </a>
        <a href="/jamming-track" class="bottom-nav-item">
            <i class="fas fa-compact-disc"></i>
            <span>Jamming</span>
        </a>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // PWA Installation Logic
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/service-worker.js')
                .then(() => console.log('Service Worker Registered'));
        }

        let deferredPrompt;
        const pwaBtn = document.getElementById('pwa-install-btn-menu');
        const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;

        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            if(pwaBtn) pwaBtn.style.display = 'flex';
        });

        if(pwaBtn) {
            pwaBtn.addEventListener('click', () => {
                if (deferredPrompt) {
                    deferredPrompt.prompt();
                    deferredPrompt.userChoice.then((choiceResult) => {
                        if (choiceResult.outcome === 'accepted') {
                            console.log('User accepted the A2HS prompt');
                        } else {
                            console.log('User dismissed the A2HS prompt');
                        }
                        deferredPrompt = null;
                    });
                } else if (isIOS) {
                    alert("To install on iOS: Tap the Share button and select 'Add to Home Screen'");
                } else {
                     alert("To install, look for 'Add to Home Screen' in your browser menu.");
                }
            });
        }

        (function() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-bs-theme', savedTheme);
        })();
        
        // Fix Modal Z-Index Issue by moving them to body
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('.modal').forEach(function(modal) {
                document.body.appendChild(modal);
            });
        });
    </script>
    {{ scripts|safe }}
</body>
</html>
"""

# --- ROUTES ---

def render_layout(content, scripts="", **kwargs):
    # Prepare global variables like bg_image
    bg_image = "default.jpg"
    if os.path.exists('bg_config.txt'):
        with open('bg_config.txt', 'r') as f:
            c = f.read().strip()
            if c: bg_image = c
            
    logo_file = None
    if os.path.exists('logo_config.txt'):
         with open('logo_config.txt', 'r') as f:
            c = f.read().strip()
            if c: logo_file = c

    # Pre-render the content fragment so Jinja tags inside it are processed
    rendered_content = render_template_string(content, **kwargs)
            
    # Render fragments
    head = HEAD_HTML.replace('{{ styles|safe }}', STYLES_HTML)
    navbar = NAVBAR_HTML # Jinja context will handle logo_file/bg_image if passed
    
    # Render Base Layout
    # Use render_template_string for the base layout
    # Pass all kwargs plus calculated ones
    return render_template_string(BASE_LAYOUT, 
                                  head=head, 
                                  navbar=render_template_string(navbar, logo_file=logo_file), 
                                  content=rendered_content,
                                  scripts=scripts,
                                  bg_image=bg_image,
                                  **kwargs)

@app.route('/')
def index():
    return render_layout(HTML_DOREMI_CONTENT)

@app.route('/gallery', methods=['GET', 'POST'])
def gallery():
    if request.method == 'POST':
        if 'image' not in request.files:
            return redirect(request.url)
        file = request.files['image']
        student_name = request.form['student_name']
        title = request.form['title']
        
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            new_item = Gallery(image=filename, student_name=student_name, title=title)
            db.session.add(new_item)
            db.session.commit()
            
            return redirect(url_for('gallery'))
            
    items = Gallery.query.order_by(Gallery.created_at.desc()).all()
    return render_layout(GALLERY_HTML_CONTENT, items=items)

GALLERY_HTML_CONTENT = """
<div class="container glass-panel p-4 mb-5 position-relative" style="border-radius: 20px;">
    <a href="/" class="position-absolute top-0 end-0 m-3 text-white text-decoration-none" style="font-size: 1.5rem; opacity: 0.7; transition: 0.2s;" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0.7"><i class="fas fa-times"></i></a>

    <div class="d-flex justify-content-between align-items-center mb-4 pe-4">
        <h2 class="text-white mb-0"><i class="fas fa-palette me-2"></i>Galeri Karya Siswa</h2>
        <button class="btn btn-light rounded-pill" data-bs-toggle="modal" data-bs-target="#uploadModal">
            <i class="fas fa-plus me-1"></i> Upload Karya
        </button>
    </div>
    
    <div class="row g-4">
        {% for item in items %}
        <div class="col-6 col-md-4 col-lg-3">
            <div class="card h-100 bg-transparent border-0">
                <div class="position-relative overflow-hidden rounded-3 shadow-sm" style="padding-top: 100%;">
                    <img src="/uploads/{{ item['image'] }}" class="position-absolute top-0 start-0 w-100 h-100 object-fit-cover" alt="{{ item['title'] }}">
                </div>
                <div class="card-body px-0 py-2 text-white">
                    <h5 class="card-title fw-bold mb-1 fs-6">{{ item['title'] }}</h5>
                    <p class="card-text small opacity-75"><i class="fas fa-user me-1"></i> {{ item['student_name'] }}</p>
                </div>
            </div>
        </div>
        {% else %}
        <div class="col-12 text-center text-white py-5">
            <i class="fas fa-image fa-3x mb-3 opacity-50"></i>
            <p>Belum ada karya yang diupload.</p>
        </div>
        {% endfor %}
    </div>
</div>

<!-- Upload Modal -->
<div class="modal fade" id="uploadModal" tabindex="-1" style="z-index: 99999;">
    <div class="modal-dialog modal-dialog-centered hard-acrylic-modal">
        <div class="modal-content glass-panel text-white">
            <div class="modal-header border-0">
                <h5 class="modal-title">Upload Karya Baru</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <form method="POST" enctype="multipart/form-data">
                <div class="modal-body">
                    <div class="mb-3">
                        <label class="form-label">Nama Siswa</label>
                        <input type="text" name="student_name" class="form-control bg-transparent text-white" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Judul Karya</label>
                        <input type="text" name="title" class="form-control bg-transparent text-white" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">File Gambar</label>
                        <input type="file" name="image" class="form-control bg-transparent text-white" accept="image/*" required>
                    </div>
                </div>
                <div class="modal-footer border-0">
                    <button type="button" class="btn btn-danger" data-bs-dismiss="modal">Tutup</button>
                    <button type="submit" class="btn btn-primary">Simpan</button>
                </div>
            </form>
        </div>
    </div>
</div>
"""

@app.route('/tutors', methods=['GET', 'POST'])
def tutors():
    if request.method == 'POST':
        if 'image' not in request.files:
            return redirect(request.url)
        file = request.files['image']
        name = request.form['name']
        bio = request.form['bio']
        
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            new_tutor = Tutors(image=filename, name=name, bio=bio)
            db.session.add(new_tutor)
            db.session.commit()
            
            return redirect(url_for('tutors'))
            
    items = Tutors.query.order_by(Tutors.created_at.desc()).all()
    return render_layout(TUTORS_HTML_CONTENT, items=items)

TUTORS_HTML_CONTENT = """
<div class="container glass-panel p-4 mb-5 position-relative" style="border-radius: 20px;">
    <a href="/" class="position-absolute top-0 end-0 m-3 text-white text-decoration-none" style="font-size: 1.5rem; opacity: 0.7; transition: 0.2s;" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0.7"><i class="fas fa-times"></i></a>

    <div class="d-flex justify-content-between align-items-center mb-4 pe-4">
        <h2 class="text-white mb-0"><i class="fas fa-chalkboard-teacher me-2"></i>Profil Pengajar</h2>
        <button class="btn btn-light rounded-pill" data-bs-toggle="modal" data-bs-target="#tutorModal">
            <i class="fas fa-plus me-1"></i> Tambah Pengajar
        </button>
    </div>
    
    <div class="row g-4">
        {% for item in items %}
        <div class="col-md-6 col-lg-4">
            <div class="d-flex align-items-center p-3 glass-panel" style="background: rgba(255,255,255,0.05); border-radius: 15px;">
                <div class="flex-shrink-0">
                    <img src="/uploads/{{ item['image'] }}" class="rounded-circle object-fit-cover" width="80" height="80" alt="{{ item['name'] }}" style="border: 2px solid rgba(255,255,255,0.5);">
                </div>
                <div class="flex-grow-1 ms-3 text-white">
                    <h5 class="mb-1 fw-bold">{{ item['name'] }}</h5>
                    <p class="mb-0 small opacity-75">{{ item['bio'] }}</p>
                </div>
            </div>
        </div>
        {% else %}
        <div class="col-12 text-center text-white py-5">
            <i class="fas fa-user-tie fa-3x mb-3 opacity-50"></i>
            <p>Belum ada data pengajar.</p>
        </div>
        {% endfor %}
    </div>
</div>

<!-- Tutor Modal -->
<div class="modal fade" id="tutorModal" tabindex="-1" style="z-index: 99999;">
    <div class="modal-dialog modal-dialog-centered hard-acrylic-modal">
        <div class="modal-content glass-panel text-white">
            <div class="modal-header border-0">
                <h5 class="modal-title">Tambah Pengajar Baru</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <form method="POST" enctype="multipart/form-data">
                <div class="modal-body">
                    <div class="mb-3">
                        <label class="form-label">Nama Pengajar</label>
                        <input type="text" name="name" class="form-control bg-transparent text-white" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Biodata Singkat</label>
                        <textarea name="bio" class="form-control bg-transparent text-white" rows="3" required></textarea>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Foto Profil</label>
                        <input type="file" name="image" class="form-control bg-transparent text-white" accept="image/*" required>
                    </div>
                </div>
                <div class="modal-footer border-0">
                    <button type="button" class="btn btn-danger" data-bs-dismiss="modal">Tutup</button>
                    <button type="submit" class="btn btn-primary">Simpan</button>
                </div>
            </form>
        </div>
    </div>
</div>
"""

@app.route('/pricing', methods=['GET', 'POST'])
def pricing():
    if request.method == 'POST':
        title = request.form['title']
        price = request.form['price']
        details = request.form['details']
        
        new_pricing = Pricing(title=title, price=price, details=details)
        db.session.add(new_pricing)
        db.session.commit()
        
        return redirect(url_for('pricing'))
            
    items = Pricing.query.order_by(Pricing.created_at.asc()).all()
    return render_layout(PRICING_HTML_CONTENT, items=items)

@app.route('/delete_pricing/<int:id>', methods=['POST'])
def delete_pricing(id):
    Pricing.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect(url_for('pricing'))

PRICING_HTML_CONTENT = """
<div class="container glass-panel p-4 mb-5 position-relative" style="border-radius: 20px;">
    <a href="/" class="position-absolute top-0 end-0 m-3 text-white text-decoration-none" style="font-size: 1.5rem; opacity: 0.7; transition: 0.2s;" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0.7"><i class="fas fa-times"></i></a>

    <div class="d-flex justify-content-between align-items-center mb-4 pe-4">
        <h2 class="text-white mb-0"><i class="fas fa-tags me-2"></i>Paket & Biaya</h2>
        <div>
             <button class="btn btn-danger rounded-pill me-2" onclick="toggleDeleteMode()">
                <i class="fas fa-trash-alt me-1"></i> Hapus Mode
            </button>
            <button class="btn btn-light rounded-pill" data-bs-toggle="modal" data-bs-target="#pricingModal">
                <i class="fas fa-plus me-1"></i> Tambah Paket
            </button>
        </div>
    </div>
    
    <div class="row g-4">
        {% for item in items %}
        <div class="col-md-4 position-relative">
            <form action="/delete_pricing/{{ item['id'] }}" method="POST" class="delete-btn-form position-absolute top-0 end-0 m-3 d-none" style="z-index: 10;">
                 <button type="submit" class="btn btn-danger btn-sm rounded-circle" onclick="return confirm('Hapus paket ini?')"><i class="fas fa-times"></i></button>
            </form>
            <div class="card h-100 bg-transparent border glass-panel text-white" style="border-radius: 20px;">
                <div class="card-body text-center p-4">
                    <h5 class="card-title text-uppercase letter-spacing-2 opacity-75 mb-3">{{ item['title'] }}</h5>
                    <h2 class="display-4 fw-bold mb-3">{{ item['price'] }}</h2>
                    <hr class="border-light opacity-25">
                    <p class="card-text opacity-75">{{ item['details'] }}</p>
                </div>
            </div>
        </div>
        {% else %}
        <div class="col-12 text-center text-white py-5">
            <i class="fas fa-money-bill-wave fa-3x mb-3 opacity-50"></i>
            <p>Belum ada paket harga.</p>
        </div>
        {% endfor %}
    </div>
</div>

<!-- Pricing Modal -->
<div class="modal fade" id="pricingModal" tabindex="-1" style="z-index: 99999;">
    <div class="modal-dialog modal-dialog-centered hard-acrylic-modal">
        <div class="modal-content glass-panel text-white">
            <div class="modal-header border-0">
                <h5 class="modal-title">Tambah Paket Baru</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <form method="POST">
                <div class="modal-body">
                    <div class="mb-3">
                        <label class="form-label">Nama Paket (Contoh: Paket 4x Pertemuan)</label>
                        <input type="text" name="title" class="form-control bg-transparent text-white" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Harga (Contoh: Rp. 350.000)</label>
                        <input type="text" name="price" class="form-control bg-transparent text-white" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Detail Keterangan</label>
                        <textarea name="details" class="form-control bg-transparent text-white" rows="3" required></textarea>
                    </div>
                </div>
                <div class="modal-footer border-0">
                    <button type="button" class="btn btn-danger" data-bs-dismiss="modal">Tutup</button>
                    <button type="submit" class="btn btn-primary">Simpan</button>
                </div>
            </form>
        </div>
    </div>
</div>

<script>
    function toggleDeleteMode() {
        document.querySelectorAll('.delete-btn-form').forEach(el => el.classList.toggle('d-none'));
    }
</script>
"""

@app.route('/slots', methods=['GET', 'POST'])
def slots():
    if request.method == 'POST':
        if 'day' in request.form:
            # Add Slot
            day = request.form['day']
            time = request.form['time']
            type_val = request.form['type']
            status = 'Available'
            
            new_slot = Slots(day=day, time=time, status=status, type=type_val)
            db.session.add(new_slot)
            db.session.commit()
            
        elif 'toggle_id' in request.form:
            # Toggle Status
            slot_id = request.form['toggle_id']
            slot = Slots.query.get(slot_id)
            if slot:
                slot.status = 'Booked' if slot.status == 'Available' else 'Available'
                db.session.commit()
            
        return redirect(url_for('slots'))
            
    # Fetch and Group Slots
    slots_raw = Slots.query.order_by(Slots.day, Slots.time).all()
    
    # Simple grouping
    days_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    grouped_slots = {d: [] for d in days_order}
    
    for slot in slots_raw:
        if slot['day'] in grouped_slots:
            grouped_slots[slot['day']].append(slot)
            
    return render_layout(SLOTS_HTML_CONTENT, grouped_slots=grouped_slots)

SLOTS_HTML_CONTENT = """
<div class="container glass-panel p-4 mb-5 position-relative" style="border-radius: 20px;">
    <a href="/" class="position-absolute top-0 end-0 m-3 text-white text-decoration-none" style="font-size: 1.5rem; opacity: 0.7; transition: 0.2s;" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0.7"><i class="fas fa-times"></i></a>

    <div class="d-flex justify-content-between align-items-center mb-4 pe-4">
        <h2 class="text-white mb-0"><i class="fas fa-calendar-alt me-2"></i>Jadwal Ketersediaan</h2>
        <button class="btn btn-light rounded-pill" data-bs-toggle="modal" data-bs-target="#slotModal">
            <i class="fas fa-plus me-1"></i> Tambah Slot
        </button>
    </div>
    
    <div class="row g-4">
        {% for day, slots in grouped_slots.items() %}
        <div class="col-md-6 col-lg-4">
            <div class="glass-panel p-3 h-100" style="background: rgba(255,255,255,0.05); border-radius: 15px;">
                <h5 class="text-white border-bottom border-light border-opacity-25 pb-2 mb-3">{{ day }}</h5>
                {% if slots %}
                    <div class="list-group list-group-flush bg-transparent">
                    {% for slot in slots %}
                        <div class="list-group-item bg-transparent text-white d-flex justify-content-between align-items-center px-0">
                            <div>
                                <span class="fw-bold">{{ slot['time'] }}</span>
                                <small class="d-block opacity-75">{{ slot['type'] }}</small>
                            </div>
                            <form method="POST" class="m-0">
                                <input type="hidden" name="toggle_id" value="{{ slot['id'] }}">
                                <button type="submit" class="btn btn-sm {{ 'btn-success' if slot['status'] == 'Available' else 'btn-danger' }} rounded-pill" style="width: 100px;">
                                    {{ slot['status'] }}
                                </button>
                            </form>
                        </div>
                    {% endfor %}
                    </div>
                {% else %}
                    <p class="text-white opacity-50 small">Tidak ada jadwal.</p>
                {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>
</div>

<!-- Slot Modal -->
<div class="modal fade" id="slotModal" tabindex="-1" style="z-index: 99999;">
    <div class="modal-dialog modal-dialog-centered hard-acrylic-modal">
        <div class="modal-content glass-panel text-white">
            <div class="modal-header border-0">
                <h5 class="modal-title">Tambah Slot Jadwal</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <form method="POST">
                <div class="modal-body">
                    <div class="mb-3">
                        <label class="form-label">Hari</label>
                        <select name="day" class="form-select bg-transparent text-white" required>
                            <option value="Senin" class="text-dark">Senin</option>
                            <option value="Selasa" class="text-dark">Selasa</option>
                            <option value="Rabu" class="text-dark">Rabu</option>
                            <option value="Kamis" class="text-dark">Kamis</option>
                            <option value="Jumat" class="text-dark">Jumat</option>
                            <option value="Sabtu" class="text-dark">Sabtu</option>
                            <option value="Minggu" class="text-dark">Minggu</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Jam (Contoh: 15:00 - 16:00)</label>
                        <input type="text" name="time" class="form-control bg-transparent text-white" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Tipe Les</label>
                        <select name="type" class="form-select bg-transparent text-white" required>
                            <option value="Piano" class="text-dark">Piano</option>
                            <option value="Gambar" class="text-dark">Gambar</option>
                            <option value="Umum" class="text-dark">Umum</option>
                        </select>
                    </div>
                </div>
                <div class="modal-footer border-0">
                    <button type="button" class="btn btn-danger" data-bs-dismiss="modal">Tutup</button>
                    <button type="submit" class="btn btn-primary">Simpan</button>
                </div>
            </form>
        </div>
    </div>
</div>
"""

@app.route('/join', methods=['GET', 'POST'])
def join_us():
    if request.method == 'POST':
        from urllib.parse import quote
        name = request.form['name']
        age = request.form['age']
        interest = request.form['interest']
        whatsapp = request.form['whatsapp']
        
        new_request = JoinRequests(name=name, age=age, interest=interest, whatsapp=whatsapp)
        db.session.add(new_request)
        db.session.commit()
        
        message = f"Halo Admin LES BIMBEL GAMBAR & MUSIK, saya ingin mendaftar.\nNama: {name}\nUmur: {age}\nMinat: {interest}\nNo WA: {whatsapp}"
        wa_url = f"https://wa.me/6281241865310?text={quote(message)}"
        
        return redirect(wa_url)
    
    return render_layout(JOIN_HTML_CONTENT)

JOIN_HTML_CONTENT = """
<div class="container glass-panel p-4 mb-5 position-relative" style="border-radius: 20px; max-width: 600px;">
    <a href="/" class="position-absolute top-0 end-0 m-3 text-white text-decoration-none" style="font-size: 1.5rem; opacity: 0.7; transition: 0.2s;" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0.7"><i class="fas fa-times"></i></a>

    <h2 class="text-white mb-4 text-center"><i class="fas fa-file-signature me-2"></i>Pendaftaran Online</h2>
    
    <form method="POST">
        <div class="mb-3">
            <label class="form-label text-white">Nama Calon Murid</label>
            <input type="text" name="name" class="form-control bg-transparent text-white" required>
        </div>
        <div class="mb-3">
            <label class="form-label text-white">Umur</label>
            <input type="number" name="age" class="form-control bg-transparent text-white" required>
        </div>
        <div class="mb-3">
            <label class="form-label text-white">Minat</label>
            <select name="interest" class="form-select bg-transparent text-white" required>
                <option value="Piano" class="text-dark">Piano</option>
                <option value="Gambar" class="text-dark">Gambar</option>
                <option value="Keduanya" class="text-dark">Keduanya</option>
            </select>
        </div>
        <div class="mb-3">
            <label class="form-label text-white">No WhatsApp Wali Murid</label>
            <input type="text" name="whatsapp" class="form-control bg-transparent text-white" placeholder="08..." required>
        </div>
        
        <div class="d-grid mt-4">
            <button type="submit" class="btn btn-success btn-lg rounded-pill">
                <i class="fab fa-whatsapp me-2"></i> Daftar Sekarang via WhatsApp
            </button>
        </div>
    </form>
</div>
"""

@app.route('/news', methods=['GET', 'POST'])
def news():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        date = request.form['date']
        filename = None
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
             filename = ""
        
        new_news = News(title=title, content=content, date=date, image=filename)
        db.session.add(new_news)
        db.session.commit()
        
        return redirect(url_for('news'))
            
    items = News.query.order_by(News.date.desc(), News.created_at.desc()).all()
    return render_layout(NEWS_HTML_CONTENT, items=items)

@app.route('/edit_news/<int:id>', methods=['POST'])
def edit_news(id):
    news_item = News.query.get(id)
    if not news_item:
        return redirect(url_for('news'))

    title = request.form['title']
    content = request.form['content']
    date = request.form['date']
    
    news_item.title = title
    news_item.content = content
    news_item.date = date

    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            news_item.image = filename
                     
    db.session.commit()
    return redirect(url_for('news'))

NEWS_HTML_CONTENT = """
<div class="container glass-panel p-4 mb-5 position-relative" style="border-radius: 20px;">
    <a href="/" class="position-absolute top-0 end-0 m-3 text-white text-decoration-none" style="font-size: 1.5rem; opacity: 0.7; transition: 0.2s;" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0.7"><i class="fas fa-times"></i></a>

    <div class="d-flex justify-content-between align-items-center mb-4 pe-4">
        <h2 class="text-white mb-0"><i class="fas fa-trophy me-2"></i>Prestasi & Event</h2>
        <button class="btn btn-light rounded-pill" data-bs-toggle="modal" data-bs-target="#newsModal">
            <i class="fas fa-plus me-1"></i> Tambah Berita
        </button>
    </div>
    
    <div class="row g-4">
        {% for item in items %}
        <div class="col-md-6 col-lg-4">
            <div class="card h-100 bg-transparent glass-panel border-0 overflow-hidden position-relative" style="border-radius: 20px;">
                <button class="btn btn-warning btn-sm rounded-circle position-absolute top-0 end-0 m-3 shadow" style="z-index: 10;" 
                        onclick='editNews({{ item["id"] }}, {{ item["title"]|tojson }}, {{ item["date"]|tojson }}, {{ item["content"]|tojson }})'>
                    <i class="fas fa-pencil-alt"></i>
                </button>
                {% if item['image'] %}
                <div class="position-relative" style="height: 200px;">
                    <img src="/uploads/{{ item['image'] }}" class="w-100 h-100 object-fit-cover" alt="{{ item['title'] }}">
                </div>
                {% endif %}
                <div class="card-body text-white">
                    <small class="text-white opacity-50 mb-2 d-block"><i class="far fa-calendar-alt me-1"></i> {{ item['date'] }}</small>
                    <h5 class="card-title fw-bold mb-3">{{ item['title'] }}</h5>
                    <p class="card-text opacity-75 small">{{ item['content'] }}</p>
                </div>
            </div>
        </div>
        {% else %}
        <div class="col-12 text-center text-white py-5">
            <i class="fas fa-newspaper fa-3x mb-3 opacity-50"></i>
            <p>Belum ada berita terbaru.</p>
        </div>
        {% endfor %}
    </div>
</div>

<!-- News Modal -->
<div class="modal fade" id="newsModal" tabindex="-1" style="z-index: 99999;">
    <div class="modal-dialog modal-dialog-centered hard-acrylic-modal">
        <div class="modal-content glass-panel text-white">
            <div class="modal-header border-0">
                <h5 class="modal-title">Tambah Berita / Prestasi</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <form method="POST" enctype="multipart/form-data">
                <div class="modal-body">
                    <div class="mb-3">
                        <label class="form-label">Judul Berita</label>
                        <input type="text" name="title" class="form-control bg-transparent text-white" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Tanggal</label>
                        <input type="date" name="date" class="form-control bg-transparent text-white" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Isi Berita</label>
                        <textarea name="content" class="form-control bg-transparent text-white" rows="4" required></textarea>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Gambar (Opsional)</label>
                        <input type="file" name="image" class="form-control bg-transparent text-white" accept="image/*">
                    </div>
                </div>
                <div class="modal-footer border-0">
                    <button type="button" class="btn btn-danger" data-bs-dismiss="modal">Tutup</button>
                    <button type="submit" class="btn btn-primary">Simpan</button>
                </div>
            </form>
        </div>
    </div>
</div>

<script>
    function editNews(id, title, date, content) {
        document.querySelector('#newsModal input[name="title"]').value = title;
        document.querySelector('#newsModal input[name="date"]').value = date;
        document.querySelector('#newsModal textarea[name="content"]').value = content;
        
        const form = document.querySelector('#newsModal form');
        form.action = '/edit_news/' + id;
        
        document.querySelector('#newsModal .modal-title').innerText = 'Edit Berita';
        
        const modal = new bootstrap.Modal(document.getElementById('newsModal'));
        modal.show();
    }
    
    // Reset form when modal is hidden
    const newsModalEl = document.getElementById('newsModal');
    if (newsModalEl) {
        newsModalEl.addEventListener('hidden.bs.modal', function () {
            const form = document.querySelector('#newsModal form');
            form.action = ''; 
            form.reset();
            document.querySelector('#newsModal .modal-title').innerText = 'Tambah Berita / Prestasi';
        });
    }
</script>
"""

@app.route('/metronome')
def metronome():
    return render_layout(METRONOME_HTML_CONTENT)

METRONOME_HTML_CONTENT = """
<div class="container d-flex justify-content-center align-items-center" style="min-height: 60vh;">
    <div class="glass-panel p-5 text-center position-relative overflow-hidden" style="border-radius: 30px; width: 100%; max-width: 400px; backdrop-filter: blur(20px);">
        
        <div class="position-absolute top-0 start-0 w-100 h-100 bg-gradient-primary opacity-10" style="z-index: -1;"></div>
        
        <h2 class="text-white mb-4 fw-bold text-uppercase letter-spacing-2"><i class="fas fa-stopwatch me-2 text-warning"></i>Metronome</h2>
        
        <div class="bpm-display-container mb-4 position-relative">
            <div class="display-1 fw-bold text-white" id="bpm-val">120</div>
            <span class="text-white-50 text-uppercase small letter-spacing-2">BPM</span>
            
            <div id="visual-beat" class="position-absolute top-50 start-50 translate-middle rounded-circle" 
                 style="width: 200px; height: 200px; border: 2px solid rgba(255,255,255,0.1); opacity: 0; transition: transform 0.1s, opacity 0.1s; pointer-events: none;"></div>
        </div>
        
        <input type="range" class="form-range mb-4" min="40" max="240" value="120" id="bpm-slider">
        
        <div class="d-flex justify-content-center gap-3 mb-5">
            <button class="btn btn-outline-light rounded-circle p-3" onclick="adjustBPM(-1)"><i class="fas fa-minus"></i></button>
            <button class="btn btn-outline-light rounded-circle p-3" onclick="adjustBPM(1)"><i class="fas fa-plus"></i></button>
        </div>
        
        <button class="btn btn-primary btn-lg rounded-pill w-100 py-3 fw-bold shadow-lg" id="play-btn">
            <i class="fas fa-play me-2"></i> START
        </button>
    </div>
</div>

<script>
    class Metronome {
        constructor(tempo = 120) {
            this.audioContext = null;
            this.notesInQueue = [];
            this.currentQuarterNote = 0;
            this.tempo = tempo;
            this.lookahead = 25.0;
            this.scheduleAheadTime = 0.1;
            this.nextNoteTime = 0.0;
            this.isRunning = false;
            this.intervalID = null;
        }

        nextNote() {
            const secondsPerBeat = 60.0 / this.tempo;
            this.nextNoteTime += secondsPerBeat;
            this.currentQuarterNote++;
            if (this.currentQuarterNote == 4) {
                this.currentQuarterNote = 0;
            }
        }

        scheduleNote(beatNumber, time) {
            this.notesInQueue.push({ note: beatNumber, time: time });

            const osc = this.audioContext.createOscillator();
            const envelope = this.audioContext.createGain();

            osc.type = 'square';
            osc.frequency.value = (beatNumber % 4 === 0) ? 1200 : 1000;
            envelope.gain.value = 3.0;
            envelope.gain.exponentialRampToValueAtTime(0.001, time + 0.1);

            osc.connect(envelope);
            envelope.connect(this.audioContext.destination);

            osc.start(time);
            osc.stop(time + 0.1);
            
            const drawTime = (time - this.audioContext.currentTime) * 1000;
            setTimeout(() => {
                const visual = document.getElementById('visual-beat');
                visual.style.opacity = '1';
                visual.style.transform = 'translate(-50%, -50%) scale(1.2)';
                visual.style.borderColor = (beatNumber % 4 === 0) ? '#ffc107' : 'rgba(255,255,255,0.5)';
                
                setTimeout(() => {
                    visual.style.opacity = '0';
                    visual.style.transform = 'translate(-50%, -50%) scale(1)';
                }, 100);
            }, Math.max(0, drawTime));
        }

        scheduler() {
            while (this.nextNoteTime < this.audioContext.currentTime + this.scheduleAheadTime ) {
                this.scheduleNote(this.currentQuarterNote, this.nextNoteTime);
                this.nextNote();
            }
            this.intervalID = window.setTimeout(this.scheduler.bind(this), this.lookahead);
        }

        start() {
            if (this.isRunning) return;

            if (this.audioContext == null) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            
            this.audioContext.resume();

            this.isRunning = true;
            this.currentQuarterNote = 0;
            this.nextNoteTime = this.audioContext.currentTime + 0.05;
            this.scheduler();
            
            const btn = document.getElementById('play-btn');
            btn.innerHTML = '<i class="fas fa-stop me-2"></i> STOP';
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-danger');
        }

        stop() {
            this.isRunning = false;
            window.clearTimeout(this.intervalID);
            
            const btn = document.getElementById('play-btn');
            btn.innerHTML = '<i class="fas fa-play me-2"></i> START';
            btn.classList.remove('btn-danger');
            btn.classList.add('btn-primary');
        }
    }

    const metronome = new Metronome(120);
    const bpmSlider = document.getElementById('bpm-slider');
    const bpmVal = document.getElementById('bpm-val');
    const playBtn = document.getElementById('play-btn');

    bpmSlider.addEventListener('input', (e) => {
        metronome.tempo = e.target.value;
        bpmVal.innerText = metronome.tempo;
    });

    function adjustBPM(delta) {
        let newBPM = parseInt(bpmSlider.value) + delta;
        if(newBPM >= 40 && newBPM <= 240) {
            bpmSlider.value = newBPM;
            metronome.tempo = newBPM;
            bpmVal.innerText = newBPM;
            
            // Trigger input event to update metronome if running
            bpmSlider.dispatchEvent(new Event('input'));
        }
    }

    playBtn.addEventListener('click', () => {
        if (metronome.isRunning) {
            metronome.stop();
        } else {
            metronome.start();
        }
    });
</script>
"""

@app.route('/ear-training')
def ear_training():
    return render_layout(EAR_TRAINING_HTML_CONTENT)

EAR_TRAINING_HTML_CONTENT = """
<div class="container d-flex flex-column justify-content-center align-items-center" style="min-height: 80vh;">
    <div class="glass-panel p-4 text-center w-100 position-relative overflow-hidden" style="border-radius: 30px; max-width: 600px; backdrop-filter: blur(20px);">
        
        <div class="position-absolute top-0 start-0 w-100 h-100 bg-gradient-info opacity-10" style="z-index: -1;"></div>

        <h2 class="text-white mb-4 fw-bold text-uppercase letter-spacing-1">
            <i class="fas fa-ear-listen me-2 text-warning"></i>Tebak Nada
            <button class="btn btn-sm btn-outline-light rounded-circle ms-2" onclick="toggleToneType()" title="Ganti Suara" style="width: 35px; height: 35px; vertical-align: middle;">
                <i class="fas fa-music" id="tone-icon"></i>
            </button>
        </h2>
        
        <div class="d-flex justify-content-center gap-4 mb-5">
            <div class="text-center">
                <div class="h4 fw-bold text-success mb-0" id="correct-score">0</div>
                <small class="text-white-50 text-uppercase" style="font-size: 0.7rem;">Benar</small>
            </div>
            <div class="text-center">
                <div class="h4 fw-bold text-danger mb-0" id="wrong-score">0</div>
                <small class="text-white-50 text-uppercase" style="font-size: 0.7rem;">Salah</small>
            </div>
        </div>
        
        <button id="play-btn" class="btn btn-light rounded-circle shadow-lg mb-4 position-relative" onclick="playCurrentNote()" style="width: 120px; height: 120px; border: 4px solid rgba(255,255,255,0.2);">
            <i class="fas fa-music fa-3x text-primary position-absolute top-50 start-50 translate-middle"></i>
            <span class="position-absolute bottom-0 start-50 translate-middle-x mb-3 text-dark fw-bold small">PLAY</span>
        </button>
        
        <div id="feedback-area" class="mb-4" style="min-height: 30px;">
            <p class="text-white opacity-75 fst-italic" id="instruction">Klik tombol Play untuk mendengar nada</p>
        </div>
        
        <div class="row g-2 px-2 mb-4" id="options-grid">
            <!-- JS Populated -->
        </div>
        
        <button class="btn btn-outline-light rounded-pill px-5 py-2" onclick="nextQuestion()" id="next-btn" style="display: none;">
            Soal Selanjutnya <i class="fas fa-arrow-right ms-2"></i>
        </button>
    </div>
</div>

<script>
    const notes = [
        { name: 'C', freq: 261.63 },
        { name: 'C#', freq: 277.18 },
        { name: 'D', freq: 293.66 },
        { name: 'D#', freq: 311.13 },
        { name: 'E', freq: 329.63 },
        { name: 'F', freq: 349.23 },
        { name: 'F#', freq: 369.99 },
        { name: 'G', freq: 392.00 },
        { name: 'G#', freq: 415.30 },
        { name: 'A', freq: 440.00 },
        { name: 'A#', freq: 466.16 },
        { name: 'B', freq: 493.88 }
    ];
    
    let audioCtx;
    let currentNote = null;
    let correct = 0;
    let wrong = 0;
    let isAnswered = false;
    let soundType = 'sine';

    function toggleToneType() {
        soundType = (soundType === 'sine') ? 'piano' : 'sine';
        const icon = document.getElementById('tone-icon');
        if (soundType === 'piano') {
            icon.className = 'fas fa-keyboard';
        } else {
            icon.className = 'fas fa-music';
        }
    }

    function initAudio() {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if(audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
    }

    function playTone(freq, type='sine', duration=1.0) {
        initAudio();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        
        osc.type = type;
        osc.frequency.value = freq;
        
        // Envelope to sound more like a piano/bell
        const now = audioCtx.currentTime;
        gain.gain.setValueAtTime(0, now);
        gain.gain.linearRampToValueAtTime(0.5, now + 0.05);
        gain.gain.exponentialRampToValueAtTime(0.001, now + duration);
        
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        
        osc.start(now);
        osc.stop(now + duration);
    }

    function playCurrentNote() {
        if(!currentNote) {
            nextQuestion();
        } else {
            if (soundType === 'piano') {
                playPianoTone(currentNote.freq);
            } else {
                playTone(currentNote.freq);
            }
        }
        document.getElementById('instruction').innerText = "Tebak nada apa ini?";
    }

    function playPianoTone(freq) {
        initAudio();
        const now = audioCtx.currentTime;
        const duration = 1.5;
        
        // 3 Oscillators for richness
        const osc1 = audioCtx.createOscillator();
        const osc2 = audioCtx.createOscillator();
        const osc3 = audioCtx.createOscillator();
        
        osc1.type = 'triangle';
        osc2.type = 'triangle';
        osc3.type = 'sawtooth';
        
        osc1.frequency.value = freq;
        osc2.frequency.value = freq;
        osc3.frequency.value = freq;
        
        osc2.detune.value = 10;
        osc3.detune.value = -10;
        
        const masterGain = audioCtx.createGain();
        const filter = audioCtx.createBiquadFilter();
        
        filter.type = 'lowpass';
        filter.frequency.value = 2000;
        
        osc1.connect(masterGain);
        osc2.connect(masterGain);
        osc3.connect(masterGain);
        
        masterGain.connect(filter);
        filter.connect(audioCtx.destination);
        
        masterGain.gain.setValueAtTime(0, now);
        masterGain.gain.linearRampToValueAtTime(0.6, now + 0.02);
        masterGain.gain.exponentialRampToValueAtTime(0.001, now + duration);
        
        osc1.start(now);
        osc2.start(now);
        osc3.start(now);
        
        osc1.stop(now + duration);
        osc2.stop(now + duration);
        osc3.stop(now + duration);
    }

    function generateOptions() {
        const grid = document.getElementById('options-grid');
        grid.innerHTML = '';
        notes.forEach(note => {
            const col = document.createElement('div');
            col.className = 'col-3 col-md-2';
            col.innerHTML = `<button class="btn btn-outline-light w-100 py-2 fw-bold" onclick="checkAnswer('${note.name}', this)">${note.name}</button>`;
            grid.appendChild(col);
        });
    }

    function checkAnswer(guess, btn) {
        if(isAnswered || !currentNote) return;
        isAnswered = true;
        
        const feedback = document.getElementById('feedback-area');
        
        if(guess === currentNote.name) {
            btn.classList.remove('btn-outline-light');
            btn.classList.add('btn-success');
            correct++;
            document.getElementById('correct-score').innerText = correct;
            feedback.innerHTML = `<h4 class="text-success fw-bold mb-0">Benar! 🎉 (${currentNote.name})</h4>`;
            playTone(880, 'sine', 0.2); // Ding
        } else {
            btn.classList.remove('btn-outline-light');
            btn.classList.add('btn-danger');
            wrong++;
            document.getElementById('wrong-score').innerText = wrong;
            feedback.innerHTML = `<h4 class="text-danger fw-bold mb-0">Salah! Jawabannya: ${currentNote.name}</h4>`;
            playTone(150, 'sawtooth', 0.3); // Buzz
        }
        
        document.getElementById('next-btn').style.display = 'inline-block';
    }

    function nextQuestion() {
        isAnswered = false;
        document.getElementById('next-btn').style.display = 'none';
        document.getElementById('feedback-area').innerHTML = '<p class="text-white opacity-75 fst-italic">Dengarkan baik-baik...</p>';
        
        // Random note
        currentNote = notes[Math.floor(Math.random() * notes.length)];
        
        generateOptions();
        setTimeout(() => playCurrentNote(), 500);
    }

    // Init
    generateOptions();
</script>
"""

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload-logo', methods=['POST'])
def upload_logo():
    if 'logo' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['logo']
    if file and file.filename != '' and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        with open('logo_config.txt', 'w') as f:
            f.write(filename)
            
    return redirect(url_for('index'))

@app.route('/manifest.json')
def manifest():
    return Response(MANIFEST_CONTENT, mimetype='application/json')

@app.route('/service-worker.js')
def service_worker():
    return Response(SW_CONTENT, mimetype='application/javascript')

@app.route('/static/audio/<filename>')
def serve_audio(filename):
    return send_from_directory('static/audio', filename)

@app.route('/uploads/icon-192.png')
def icon_192():
    if os.path.exists('logo_config.txt'):
        with open('logo_config.txt', 'r') as f:
            filename = f.read().strip()
            if filename and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    # Fallback to static/logobimbel.png
    return send_from_directory('static', 'logobimbel.png')

@app.route('/uploads/icon-512.png')
def icon_512():
    if os.path.exists('logo_config.txt'):
        with open('logo_config.txt', 'r') as f:
            filename = f.read().strip()
            if filename and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    return send_from_directory('static', 'logobimbel.png')

@app.route('/wallpaper-blur/upload', methods=['POST'])
def wallpaper_upload():
    if 'background' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['background']
    if file and file.filename != '' and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        with open('bg_config.txt', 'w') as f:
            f.write(filename)
            
    return redirect(url_for('index'))


HTML_DOREMI_CONTENT = """
    <style>
        .piano-container {
            position: relative;
            display: flex;
            justify-content: center;
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 0 30px rgba(255, 255, 255, 0.1);
        }

        .keys-wrapper {
            position: relative;
            display: flex;
        }

        .white-key {
            width: 60px;
            height: 220px;
            border: 2px solid rgba(255, 255, 255, 0.8);
            border-radius: 0 0 8px 8px;
            margin: 0 2px;
            background: #ffffff; /* Solid White */
            z-index: 1;
            position: relative;
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
            display: flex;
            justify-content: center;
            align-items: flex-end;
            padding-bottom: 20px;
        }

        .black-key {
            width: 40px;
            height: 130px;
            position: absolute;
            z-index: 2;
            background: #000000; /* Solid Black */
            border: 2px solid rgba(255, 255, 255, 0.5);
            border-radius: 0 0 5px 5px;
            top: 0;
            box-shadow: none; /* Removed dim effect */
            /* Flex alignment for sticker */
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            align-items: center;
            padding-bottom: 10px;
        }

        /* Neon Glow for C Major Scale (White Keys) */
        .white-key.glow {
            box-shadow: 0 0 15px rgba(255, 255, 255, 0.9), inset 0 0 20px rgba(255, 255, 255, 0.4);
            border-color: #fff;
            animation: pulse-glow 3s infinite alternate;
        }

        /* Sticker Styles */
        .key-sticker {
            width: 25px;
            height: 25px;
            background: #ffff00; /* Neon Yellow */
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            font-weight: 800;
            color: #000;
            font-size: 0.9rem;
            box-shadow: 0 0 10px #ffff00, inset 0 0 5px rgba(255,255,255,0.8);
        }

        @keyframes pulse-glow {
            0% { box-shadow: 0 0 15px rgba(255, 255, 255, 0.7), inset 0 0 10px rgba(255, 255, 255, 0.2); }
            100% { box-shadow: 0 0 25px rgba(255, 255, 255, 1), inset 0 0 25px rgba(255, 255, 255, 0.5); }
        }

        .title-neon {
            font-family: 'Inter', sans-serif;
            font-weight: 800;
            font-size: 3rem;
            color: white;
            text-align: center;
            margin: 0; /* reset margin for flex alignment */
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.8), 0 0 20px rgba(255, 255, 255, 0.4);
            letter-spacing: 2px;
        }
        
        .header-controls {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
            margin-bottom: 40px;
            flex-wrap: wrap;
        }

        /* Mobile Responsiveness */
        @media (max-width: 768px) {
            .white-key {
                width: 35px;
                height: 140px;
                padding-bottom: 10px;
            }
            .black-key {
                width: 24px;
                height: 85px;
            }
            .title-neon {
                font-size: 2rem;
            }
            .header-controls {
                margin-bottom: 20px;
                gap: 15px;
                flex-direction: column;
            }
            .key-sticker {
                width: 18px;
                height: 18px;
                font-size: 0.7rem;
            }
        }
    </style>

        <div style="width:100%; display:flex; flex-direction:column; align-items:center; padding-top: 40px;">
            
            <div class="header-controls">
                <h1 class="title-neon">nada dasar C</h1>
            </div>
            
            <div class="piano-container">
                <div class="keys-wrapper">
                    <!-- White Keys with Stickers -->
                    <div class="white-key glow"><div class="key-sticker">1</div></div> <!-- C -->
                    <div class="white-key glow"><div class="key-sticker">2</div></div> <!-- D -->
                    <div class="white-key glow"><div class="key-sticker">3</div></div> <!-- E -->
                    <div class="white-key glow"><div class="key-sticker">4</div></div> <!-- F -->
                    <div class="white-key glow"><div class="key-sticker">5</div></div> <!-- G -->
                    <div class="white-key glow"><div class="key-sticker">6</div></div> <!-- A -->
                    <div class="white-key glow"><div class="key-sticker">7</div></div> <!-- B -->
                    <div class="white-key glow"><div class="key-sticker">8</div></div> <!-- C (High) -->
                    
                    <!-- Black Keys -->
                    <div class="black-key" style="left: 45px;"></div>  <!-- C# -->
                    <div class="black-key" style="left: 109px;"></div> <!-- D# -->
                    <div class="black-key" style="left: 237px;"></div> <!-- F# -->
                    <div class="black-key" style="left: 301px;"></div> <!-- G# -->
                    <div class="black-key" style="left: 365px;"></div> <!-- A# -->
                </div>
            </div>

            <!-- D Major -->
            <h1 class="title-neon" style="margin-top:20px;">nada dasar D</h1>
            <div class="piano-container" data-scale="D">
                <div class="keys-wrapper">
                    <div class="white-key glow"><div class="key-sticker">1</div></div> <!-- D -->
                    <div class="white-key glow"><div class="key-sticker">2</div></div> <!-- E -->
                    <div class="white-key glow"></div> <!-- F -->
                    <div class="white-key glow"><div class="key-sticker">4</div></div> <!-- G -->
                    <div class="white-key glow"><div class="key-sticker">5</div></div> <!-- A -->
                    <div class="white-key glow"><div class="key-sticker">6</div></div> <!-- B -->
                    <div class="white-key glow"></div> <!-- C -->
                    <div class="white-key glow"><div class="key-sticker">8</div></div> <!-- D -->
                    
                    <div class="black-key"></div> <!-- D# -->
                    <div class="black-key"><div class="key-sticker">3</div></div> <!-- F# -->
                    <div class="black-key"></div> <!-- G# -->
                    <div class="black-key"></div> <!-- A# -->
                    <div class="black-key"><div class="key-sticker">7</div></div> <!-- C# -->
                </div>
            </div>

            <!-- E Major -->
            <h1 class="title-neon" style="margin-top:20px;">nada dasar E</h1>
            <div class="piano-container" data-scale="E">
                <div class="keys-wrapper">
                    <div class="white-key glow"><div class="key-sticker">1</div></div> <!-- E -->
                    <div class="white-key glow"></div> <!-- F -->
                    <div class="white-key glow"></div> <!-- G -->
                    <div class="white-key glow"><div class="key-sticker">4</div></div> <!-- A -->
                    <div class="white-key glow"><div class="key-sticker">5</div></div> <!-- B -->
                    <div class="white-key glow"></div> <!-- C -->
                    <div class="white-key glow"></div> <!-- D -->
                    <div class="white-key glow"><div class="key-sticker">8</div></div> <!-- E -->
                    
                    <div class="black-key"><div class="key-sticker">2</div></div> <!-- F# -->
                    <div class="black-key"><div class="key-sticker">3</div></div> <!-- G# -->
                    <div class="black-key"></div> <!-- A# -->
                    <div class="black-key"><div class="key-sticker">6</div></div> <!-- C# -->
                    <div class="black-key"><div class="key-sticker">7</div></div> <!-- D# -->
                </div>
            </div>

            <!-- F Major -->
            <h1 class="title-neon" style="margin-top:20px;">nada dasar F</h1>
            <div class="piano-container" data-scale="F">
                <div class="keys-wrapper">
                    <div class="white-key glow"><div class="key-sticker">1</div></div> <!-- F -->
                    <div class="white-key glow"><div class="key-sticker">2</div></div> <!-- G -->
                    <div class="white-key glow"><div class="key-sticker">3</div></div> <!-- A -->
                    <div class="white-key glow"></div> <!-- B -->
                    <div class="white-key glow"><div class="key-sticker">5</div></div> <!-- C -->
                    <div class="white-key glow"><div class="key-sticker">6</div></div> <!-- D -->
                    <div class="white-key glow"><div class="key-sticker">7</div></div> <!-- E -->
                    <div class="white-key glow"><div class="key-sticker">8</div></div> <!-- F -->
                    
                    <div class="black-key"></div> <!-- F# -->
                    <div class="black-key"></div> <!-- G# -->
                    <div class="black-key"><div class="key-sticker">4</div></div> <!-- Bb -->
                    <div class="black-key"></div> <!-- C# -->
                    <div class="black-key"></div> <!-- D# -->
                </div>
            </div>

            <!-- G Major -->
            <h1 class="title-neon" style="margin-top:20px;">nada dasar G</h1>
            <div class="piano-container" data-scale="G">
                <div class="keys-wrapper">
                    <div class="white-key glow"><div class="key-sticker">1</div></div> <!-- G -->
                    <div class="white-key glow"><div class="key-sticker">2</div></div> <!-- A -->
                    <div class="white-key glow"><div class="key-sticker">3</div></div> <!-- B -->
                    <div class="white-key glow"><div class="key-sticker">4</div></div> <!-- C -->
                    <div class="white-key glow"><div class="key-sticker">5</div></div> <!-- D -->
                    <div class="white-key glow"><div class="key-sticker">6</div></div> <!-- E -->
                    <div class="white-key glow"></div> <!-- F -->
                    <div class="white-key glow"><div class="key-sticker">8</div></div> <!-- G -->
                    
                    <div class="black-key"></div> <!-- G# -->
                    <div class="black-key"></div> <!-- A# -->
                    <div class="black-key"></div> <!-- C# -->
                    <div class="black-key"></div> <!-- D# -->
                    <div class="black-key"><div class="key-sticker">7</div></div> <!-- F# -->
                </div>
            </div>

            <!-- A Major -->
            <h1 class="title-neon" style="margin-top:20px;">nada dasar A</h1>
            <div class="piano-container" data-scale="A">
                <div class="keys-wrapper">
                    <div class="white-key glow"><div class="key-sticker">1</div></div> <!-- A -->
                    <div class="white-key glow"><div class="key-sticker">2</div></div> <!-- B -->
                    <div class="white-key glow"></div> <!-- C -->
                    <div class="white-key glow"><div class="key-sticker">4</div></div> <!-- D -->
                    <div class="white-key glow"><div class="key-sticker">5</div></div> <!-- E -->
                    <div class="white-key glow"></div> <!-- F -->
                    <div class="white-key glow"></div> <!-- G -->
                    <div class="white-key glow"><div class="key-sticker">8</div></div> <!-- A -->
                    
                    <div class="black-key"></div> <!-- A# -->
                    <div class="black-key"><div class="key-sticker">3</div></div> <!-- C# -->
                    <div class="black-key"></div> <!-- D# -->
                    <div class="black-key"><div class="key-sticker">6</div></div> <!-- F# -->
                    <div class="black-key"><div class="key-sticker">7</div></div> <!-- G# -->
                </div>
            </div>

            <!-- B Major -->
            <h1 class="title-neon" style="margin-top:20px;">nada dasar B</h1>
            <div class="piano-container" data-scale="B">
                <div class="keys-wrapper">
                    <div class="white-key glow"><div class="key-sticker">1</div></div> <!-- B -->
                    <div class="white-key glow"></div> <!-- C -->
                    <div class="white-key glow"></div> <!-- D -->
                    <div class="white-key glow"><div class="key-sticker">4</div></div> <!-- E -->
                    <div class="white-key glow"></div> <!-- F -->
                    <div class="white-key glow"></div> <!-- G -->
                    <div class="white-key glow"></div> <!-- A -->
                    <div class="white-key glow"><div class="key-sticker">8</div></div> <!-- B -->
                    
                    <div class="black-key"><div class="key-sticker">2</div></div> <!-- C# -->
                    <div class="black-key"><div class="key-sticker">3</div></div> <!-- D# -->
                    <div class="black-key"><div class="key-sticker">5</div></div> <!-- F# -->
                    <div class="black-key"><div class="key-sticker">6</div></div> <!-- G# -->
                    <div class="black-key"><div class="key-sticker">7</div></div> <!-- A# -->
                </div>
            </div>
        </div>

    <script>
        // PWA Installation Logic moved to BASE_LAYOUT
        
        const deferredPrompt = null; // Stub if referenced
        const pwaBtn = document.getElementById('pwa-install-btn'); // This is in Navbar
        
        // Key adjustment script
        function adjustBlackKeys() {
            const pianoContainers = document.querySelectorAll('.piano-container');
            
            const scaleIndices = {
                'C': [1, 2, 4, 5, 6],
                'D': [1, 3, 4, 5, 7],
                'E': [2, 3, 4, 6, 7],
                'F': [1, 2, 3, 5, 6],
                'G': [1, 2, 4, 5, 7],
                'A': [1, 3, 4, 6, 7],
                'B': [2, 3, 5, 6, 7]
            };

            pianoContainers.forEach(container => {
                const whiteKey = container.querySelector('.white-key');
                if(!whiteKey) return;
                
                const w = whiteKey.offsetWidth;
                const m = 4; // margin
                const slot = w + m;
                
                const blackKeys = container.querySelectorAll('.black-key');
                if(blackKeys.length === 0) return;
                
                const blackWidth = blackKeys[0].offsetWidth;
                
                const scaleType = container.getAttribute('data-scale') || 'C';
                const indices = scaleIndices[scaleType] || scaleIndices['C'];
                
                blackKeys.forEach((key, i) => {
                    if (i < indices.length) {
                        const idx = indices[i];
                        const leftPos = (idx * slot) - (blackWidth / 2);
                        key.style.left = leftPos + 'px';
                    }
                });
            });
        }
        
        window.addEventListener('resize', adjustBlackKeys);
        window.addEventListener('load', adjustBlackKeys);
        
        // Re-attach PWA handler logic if needed, but PWA button is in Navbar which is in Base Layout.
        // We'll move the PWA logic to the Base Layout's script block if possible, or keep it here if it's specific.
        // Actually, let's keep the adjustBlackKeys here as it's specific to this view.
    </script>
"""

@app.route('/rhythm-trainer')
def rhythm_trainer():
    return render_layout(RHYTHM_TRAINER_HTML)

RHYTHM_TRAINER_HTML = """
<style>
    .arcade-container {
        position: relative;
        width: 100%;
        max-width: 800px;
        height: 400px;
        background: rgba(10, 10, 15, 0.8);
        border-radius: 20px;
        border: 2px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 0 30px rgba(0, 0, 0, 0.5), inset 0 0 50px rgba(0,0,0,0.8);
        overflow: hidden;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
    }
    .target-line {
        position: absolute;
        bottom: 50px;
        left: 10%;
        width: 80%;
        height: 4px;
        background: rgba(255, 255, 255, 0.5);
        box-shadow: 0 0 10px rgba(255,255,255,0.8);
        z-index: 5;
    }
    #gameCanvas {
        width: 100%;
        flex: 1;
        display: block;
    }
    .score-board {
        position: absolute;
        top: 20px;
        left: 20px;
        color: white;
        font-family: 'Inter', sans-serif;
        z-index: 10;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
    }
    .feedback-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 3rem;
        font-weight: 800;
        opacity: 0;
        transition: opacity 0.2s, transform 0.2s;
        z-index: 20;
        pointer-events: none;
    }
    .feedback-text.show {
        opacity: 1;
        transform: translate(-50%, -60%) scale(1.2);
    }
    .particle {
        position: absolute;
        width: 8px;
        height: 8px;
        background: #00ffcc;
        border-radius: 50%;
        pointer-events: none;
        animation: pop 0.5s ease-out forwards;
        z-index: 15;
    }
    @keyframes pop {
        0% { transform: scale(1) translate(0, 0); opacity: 1; }
        100% { transform: scale(0) translate(var(--tx), var(--ty)); opacity: 0; }
    }
    .controls {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        margin-top: 20px;
    }
</style>

<div class="container d-flex flex-column justify-content-center align-items-center" style="min-height: 70vh;">
    <h2 class="text-white mb-4 fw-bold text-uppercase letter-spacing-1">
        <i class="fas fa-drum me-2 text-info"></i>Pelatih Ritme Interaktif
    </h2>
    
    <div class="arcade-container" id="arcadeContainer">
        <div class="score-board">
            <h4>Score: <span id="scoreVal">0</span></h4>
            <div class="small opacity-75">Combo: <span id="comboVal">0</span></div>
        </div>
        
        <div class="feedback-text" id="feedbackText">PERFECT!</div>
        <div class="target-line" id="targetLine"></div>
        <canvas id="gameCanvas"></canvas>
    </div>

    <div class="controls w-100 max-w-800 text-center">
        <button id="startGameBtn" class="btn btn-primary btn-lg rounded-pill px-5 py-3 fw-bold shadow-lg mb-3">
            <i class="fas fa-play me-2"></i> MULAI MAIN
        </button>
        <p class="text-white opacity-75 small mb-0">Tekan <kbd>Spasi</kbd> atau <kbd>Tap Layar</kbd> tepat saat balok menyentuh garis putih!</p>
    </div>
</div>

<script>
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    const container = document.getElementById('arcadeContainer');
    const scoreVal = document.getElementById('scoreVal');
    const comboVal = document.getElementById('comboVal');
    const feedbackText = document.getElementById('feedbackText');
    const startBtn = document.getElementById('startGameBtn');

    let audioCtx;
    let isPlaying = false;
    let score = 0;
    let combo = 0;
    let blocks = [];
    let speed = 4; // pixels per frame
    let lastTime = 0;
    let nextSpawnTime = 0;
    let bpm = 90;
    let msPerBeat = 60000 / bpm;
    let animationId;
    
    // Resize canvas
    function resizeCanvas() {
        canvas.width = container.clientWidth;
        canvas.height = container.clientHeight;
    }
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    const targetY = canvas.height - 50; // Matches CSS target-line bottom: 50px (approx)
    const hitWindow = 30; // +/- pixels for a hit

    function createClickSound() {
        if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        if (audioCtx.state === 'suspended') audioCtx.resume();
        
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'square';
        osc.frequency.setValueAtTime(800, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(10, audioCtx.currentTime + 0.1);
        gain.gain.setValueAtTime(1, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.1);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.1);
    }

    function spawnBlock() {
        blocks.push({
            x: canvas.width / 2 - 40,
            y: -20,
            width: 80,
            height: 20,
            active: true
        });
        createClickSound();
        nextSpawnTime = performance.now() + msPerBeat;
    }

    function showFeedback(text, color) {
        feedbackText.innerText = text;
        feedbackText.style.color = color;
        feedbackText.style.textShadow = `0 0 20px ${color}`;
        feedbackText.classList.add('show');
        setTimeout(() => feedbackText.classList.remove('show'), 400);
    }

    function createParticles(x, y) {
        for(let i=0; i<10; i++) {
            const p = document.createElement('div');
            p.className = 'particle';
            p.style.left = `${x}px`;
            p.style.top = `${y}px`;
            const angle = Math.random() * Math.PI * 2;
            const dist = 50 + Math.random() * 50;
            p.style.setProperty('--tx', `${Math.cos(angle) * dist}px`);
            p.style.setProperty('--ty', `${Math.sin(angle) * dist}px`);
            container.appendChild(p);
            setTimeout(() => p.remove(), 500);
        }
    }

    function registerHit() {
        if (!isPlaying) return;
        
        let hitRegistered = false;
        // Find lowest active block
        for (let i = 0; i < blocks.length; i++) {
            let b = blocks[i];
            if (b.active) {
                const dist = Math.abs(b.y - targetY);
                if (dist < hitWindow) {
                    b.active = false; // Mark hit
                    hitRegistered = true;
                    
                    if (dist < hitWindow / 3) {
                        score += 100;
                        combo++;
                        showFeedback("SEMPURNA!", "#00ffcc");
                        createParticles(container.clientWidth/2, targetY);
                    } else {
                        score += 50;
                        combo++;
                        showFeedback("BAIK!", "#ffcc00");
                    }
                    scoreVal.innerText = score;
                    comboVal.innerText = combo;
                    break; // Only hit one block
                }
            }
        }
        
        if (!hitRegistered) {
            combo = 0;
            comboVal.innerText = combo;
            showFeedback("MELESET!", "#ff3366");
        }
    }

    function gameLoop(timestamp) {
        if (!isPlaying) return;
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (timestamp >= nextSpawnTime) {
            spawnBlock();
        }
        
        // Draw blocks
        for (let i = blocks.length - 1; i >= 0; i--) {
            let b = blocks[i];
            b.y += speed;
            
            if (b.active) {
                ctx.fillStyle = '#00ffcc';
                ctx.shadowBlur = 15;
                ctx.shadowColor = '#00ffcc';
                ctx.fillRect(b.x, b.y, b.width, b.height);
                ctx.shadowBlur = 0; // reset
            }
            
            // Missed block
            if (b.active && b.y > targetY + hitWindow) {
                b.active = false;
                combo = 0;
                comboVal.innerText = combo;
                showFeedback("MELESET!", "#ff3366");
            }
            
            // Remove offscreen
            if (b.y > canvas.height + 50) {
                blocks.splice(i, 1);
            }
        }
        
        animationId = requestAnimationFrame(gameLoop);
    }

    function startGame() {
        if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        if (audioCtx.state === 'suspended') audioCtx.resume();
        
        if (isPlaying) {
            isPlaying = false;
            cancelAnimationFrame(animationId);
            startBtn.innerHTML = '<i class="fas fa-play me-2"></i> MULAI MAIN';
            startBtn.classList.replace('btn-danger', 'btn-primary');
        } else {
            isPlaying = true;
            score = 0;
            combo = 0;
            blocks = [];
            scoreVal.innerText = score;
            comboVal.innerText = combo;
            nextSpawnTime = performance.now() + 1000; // start in 1s
            startBtn.innerHTML = '<i class="fas fa-stop me-2"></i> BERHENTI';
            startBtn.classList.replace('btn-primary', 'btn-danger');
            requestAnimationFrame(gameLoop);
        }
    }

    startBtn.addEventListener('click', startGame);

    window.addEventListener('keydown', (e) => {
        if (e.code === 'Space') {
            e.preventDefault();
            registerHit();
        }
    });
    
    // Fix for touchscreen tap
    container.addEventListener('touchstart', (e) => {
        e.preventDefault();
        registerHit();
    });
</script>
"""

@app.route('/visual-chord')
def visual_chord():
    return render_layout(VISUAL_CHORD_HTML)

VISUAL_CHORD_HTML = """
<style>
    /* Borrow piano container styles from Home page */
    .piano-container {
        position: relative;
        display: flex;
        justify-content: center;
        padding: 20px;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 0 30px rgba(255, 255, 255, 0.1);
        overflow-x: auto;
    }
    .keys-wrapper {
        position: relative;
        display: flex;
        min-width: max-content;
    }
    .white-key {
        width: 50px;
        height: 200px;
        border: 1px solid #ccc;
        border-radius: 0 0 5px 5px;
        background: #ffffff;
        z-index: 1;
        position: relative;
        display: flex;
        justify-content: center;
        align-items: flex-end;
        padding-bottom: 15px;
        transition: all 0.2s;
    }
    .black-key {
        width: 30px;
        height: 120px;
        background: #000000;
        position: absolute;
        z-index: 2;
        border-radius: 0 0 4px 4px;
        display: flex;
        justify-content: center;
        align-items: flex-end;
        padding-bottom: 10px;
        transition: all 0.2s;
    }
    
    /* Dynamic Glow Colors based on chord type */
    .glow-major {
        box-shadow: 0 0 20px rgba(255, 105, 180, 0.8), inset 0 0 15px rgba(255, 105, 180, 0.5) !important;
        background: #ffe6f2 !important;
        border-color: #ff69b4 !important;
    }
    .glow-minor {
        box-shadow: 0 0 20px rgba(135, 206, 235, 0.8), inset 0 0 15px rgba(135, 206, 235, 0.5) !important;
        background: #e6f7ff !important;
        border-color: #87ceeb !important;
    }
    .glow-power {
        box-shadow: 0 0 20px rgba(255, 215, 0, 0.8), inset 0 0 15px rgba(255, 215, 0, 0.5) !important;
        background: #fffbe6 !important;
        border-color: #ffd700 !important;
    }
    
    .key-sticker {
        width: 20px;
        height: 20px;
        background: #ffcc00;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        font-weight: 800;
        font-size: 0.8rem;
        color: black;
        box-shadow: 0 2px 5px rgba(0,0,0,0.5);
    }
</style>

<div class="container d-flex flex-column justify-content-center align-items-center" style="min-height: 70vh;">
    <div class="glass-panel p-4 mb-4 text-center w-100" style="max-width: 800px; border-radius: 20px;">
        <h2 class="text-white mb-4 fw-bold"><i class="fas fa-keyboard me-2 text-warning"></i>Kamus Chord Visual</h2>
        
        <div class="row g-3 justify-content-center">
            <div class="col-md-4">
                <select id="baseNote" class="form-select bg-dark text-white border-secondary">
                    <option value="0">C</option>
                    <option value="1">C# / Db</option>
                    <option value="2">D</option>
                    <option value="3">D# / Eb</option>
                    <option value="4">E</option>
                    <option value="5">F</option>
                    <option value="6">F# / Gb</option>
                    <option value="7">G</option>
                    <option value="8">G# / Ab</option>
                    <option value="9">A</option>
                    <option value="10">A# / Bb</option>
                    <option value="11">B</option>
                </select>
            </div>
            <div class="col-md-4">
                <select id="chordType" class="form-select bg-dark text-white border-secondary">
                    <option value="major">Major</option>
                    <option value="minor">Minor</option>
                    <option value="power">Power Chord (5)</option>
                </select>
            </div>
        </div>
    </div>
    
    <div class="piano-container w-100" style="max-width: 900px;">
        <div class="keys-wrapper" id="pianoKeys">
            <!-- Rendered by JS -->
        </div>
    </div>
</div>

<script>
    const pianoKeys = document.getElementById('pianoKeys');
    const baseNoteSelect = document.getElementById('baseNote');
    const chordTypeSelect = document.getElementById('chordType');
    
    // 2 Octaves of notes: 0 to 23
    // Pattern of white (W) and black (B) keys starting from C
    const keyPattern = ['W','B','W','B','W','W','B','W','B','W','B','W'];
    
    function buildPiano() {
        pianoKeys.innerHTML = '';
        let whiteKeyCount = 0;
        
        for(let i=0; i<24; i++) {
            let noteType = keyPattern[i % 12];
            let keyDiv = document.createElement('div');
            keyDiv.setAttribute('data-note', i);
            
            if(noteType === 'W') {
                keyDiv.className = 'white-key';
                pianoKeys.appendChild(keyDiv);
                whiteKeyCount++;
            } else {
                keyDiv.className = 'black-key';
                // Calculate position based on previous white keys
                // White key width = 50px, border = 1px, total approx 52px
                // Black key width = 30px
                let leftPos = (whiteKeyCount * 50) - 15; 
                keyDiv.style.left = leftPos + 'px';
                pianoKeys.appendChild(keyDiv);
            }
        }
    }
    
    function updateChord() {
        // Clear old glows and stickers
        document.querySelectorAll('.white-key, .black-key').forEach(el => {
            el.classList.remove('glow-major', 'glow-minor', 'glow-power');
            el.innerHTML = '';
        });
        
        let root = parseInt(baseNoteSelect.value);
        let type = chordTypeSelect.value;
        
        let intervals = [];
        let glowClass = '';
        let fingerings = [];
        
        if(type === 'major') {
            intervals = [0, 4, 7];
            glowClass = 'glow-major';
            fingerings = [1, 3, 5]; // Jempol, Tengah, Kelingking
        } else if (type === 'minor') {
            intervals = [0, 3, 7];
            glowClass = 'glow-minor';
            fingerings = [1, 3, 5];
        } else if (type === 'power') {
            intervals = [0, 7];
            glowClass = 'glow-power';
            fingerings = [1, 5];
        }
        
        intervals.forEach((interval, index) => {
            let targetNote = root + interval;
            let keyEl = document.querySelector(`[data-note="${targetNote}"]`);
            if(keyEl) {
                keyEl.classList.add(glowClass);
                keyEl.innerHTML = `<div class="key-sticker">${fingerings[index]}</div>`;
            }
        });
    }
    
    baseNoteSelect.addEventListener('change', updateChord);
    chordTypeSelect.addEventListener('change', updateChord);
    
    // Init
    buildPiano();
    updateChord();
</script>
"""

@app.route('/vocal-detector')
def vocal_detector():
    return render_layout(VOCAL_DETECTOR_HTML)

VOCAL_DETECTOR_HTML = """
<style>
    .tuner-container {
        background: rgba(20, 20, 25, 0.85);
        border-radius: 30px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        box-shadow: 0 15px 35px rgba(0,0,0,0.5), inset 0 0 20px rgba(255,255,255,0.05);
        backdrop-filter: blur(20px);
        padding: 40px 20px;
        text-align: center;
        max-width: 500px;
        width: 100%;
        margin: 0 auto;
        position: relative;
        overflow: hidden;
    }
    .tuner-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 60%);
        pointer-events: none;
    }
    .note-display {
        font-size: 6rem;
        font-weight: 800;
        color: white;
        text-shadow: 0 0 20px rgba(255,255,255,0.5);
        line-height: 1;
        margin-bottom: 10px;
        transition: color 0.2s, text-shadow 0.2s;
    }
    .cents-display {
        font-size: 1.5rem;
        color: rgba(255,255,255,0.7);
        margin-bottom: 30px;
    }
    .tuning-meter {
        position: relative;
        width: 100%;
        height: 150px;
    }
    #meterCanvas {
        width: 100%;
        height: 100%;
        display: block;
    }
    .status-text {
        font-size: 1.2rem;
        font-weight: 600;
        margin-top: 20px;
        min-height: 30px;
    }
    
    .note-perfect {
        color: #00ff00 !important;
        text-shadow: 0 0 30px #00ff00 !important;
    }
    .note-low {
        color: #ff3333 !important;
        text-shadow: 0 0 20px #ff3333 !important;
    }
    .note-high {
        color: #ff9900 !important;
        text-shadow: 0 0 20px #ff9900 !important;
    }
</style>

<div class="container d-flex flex-column justify-content-center align-items-center" style="min-height: 70vh;">
    <div class="tuner-container">
        <h3 class="text-white opacity-75 mb-4 text-uppercase letter-spacing-1">
            <i class="fas fa-microphone-alt me-2"></i>Detektor Nada Vokal
        </h3>
        
        <div class="note-display" id="noteName">--</div>
        <div class="cents-display" id="centsDisplay">0 cents</div>
        
        <div class="tuning-meter">
            <canvas id="meterCanvas"></canvas>
        </div>
        
        <div class="status-text text-white" id="statusText">Tekan tombol untuk mulai</div>
        
        <button id="micBtn" class="btn btn-primary rounded-pill mt-4 px-5 py-2 fw-bold">
            <i class="fas fa-microphone me-2"></i> Mulai Deteksi
        </button>
    </div>
</div>

<script>
    const noteNameEl = document.getElementById('noteName');
    const centsDisplayEl = document.getElementById('centsDisplay');
    const statusTextEl = document.getElementById('statusText');
    const micBtn = document.getElementById('micBtn');
    const canvas = document.getElementById('meterCanvas');
    const ctx = canvas.getContext('2d');
    
    function resizeCanvas() {
        canvas.width = canvas.clientWidth;
        canvas.height = canvas.clientHeight;
    }
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    let audioCtx;
    let analyser;
    let microphone;
    let isDetecting = false;
    let animationId;
    let bufferLength;
    let dataArray;
    
    const noteStrings = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

    function noteFromPitch(frequency) {
        let noteNum = 12 * (Math.log(frequency / 440) / Math.log(2));
        return Math.round(noteNum) + 69;
    }

    function frequencyFromNoteNumber(note) {
        return 440 * Math.pow(2, (note - 69) / 12);
    }

    function centsOffFromPitch(frequency, note) {
        return Math.floor(1200 * Math.log(frequency / frequencyFromNoteNumber(note)) / Math.log(2));
    }

    // Autocorrelation algorithm for pitch detection
    function autoCorrelate(buf, sampleRate) {
        let SIZE = buf.length;
        let rms = 0;
        
        for (let i = 0; i < SIZE; i++) {
            let val = buf[i];
            rms += val * val;
        }
        rms = Math.sqrt(rms / SIZE);
        if (rms < 0.01) return -1; // Not enough signal

        let r1 = 0, r2 = SIZE - 1, thres = 0.2;
        for (let i = 0; i < SIZE / 2; i++)
            if (Math.abs(buf[i]) < thres) { r1 = i; break; }
        for (let i = 1; i < SIZE / 2; i++)
            if (Math.abs(buf[SIZE - i]) < thres) { r2 = SIZE - i; break; }

        buf = buf.slice(r1, r2);
        SIZE = buf.length;

        let c = new Array(SIZE).fill(0);
        for (let i = 0; i < SIZE; i++)
            for (let j = 0; j < SIZE - i; j++)
                c[i] = c[i] + buf[j] * buf[j + i];

        let d = 0; while (c[d] > c[d + 1]) d++;
        let maxval = -1, maxpos = -1;
        for (let i = d; i < SIZE; i++) {
            if (c[i] > maxval) {
                maxval = c[i];
                maxpos = i;
            }
        }
        let T0 = maxpos;
        
        // Parabolic interpolation
        let x1 = c[T0 - 1], x2 = c[T0], x3 = c[T0 + 1];
        let a = (x1 + x3 - 2 * x2) / 2;
        let b = (x3 - x1) / 2;
        if (a) T0 = T0 - b / (2 * a);

        return sampleRate / T0;
    }

    function drawMeter(cents) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        const cx = canvas.width / 2;
        const cy = canvas.height;
        const radius = canvas.height - 20;
        
        // Draw ticks
        for(let i = -50; i <= 50; i += 10) {
            let angle = Math.PI + (i * Math.PI / 100);
            ctx.beginPath();
            ctx.moveTo(cx + Math.cos(angle) * (radius - 10), cy + Math.sin(angle) * (radius - 10));
            ctx.lineTo(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius);
            ctx.strokeStyle = (i === 0) ? '#00ff00' : 'rgba(255,255,255,0.5)';
            ctx.lineWidth = (i === 0) ? 4 : 2;
            ctx.stroke();
        }
        
        // Draw Needle
        let c = Math.max(-50, Math.min(50, cents)); // Clamp
        let needleAngle = Math.PI + (c * Math.PI / 100);
        
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + Math.cos(needleAngle) * radius, cy + Math.sin(needleAngle) * radius);
        
        if (Math.abs(c) < 5) {
            ctx.strokeStyle = '#00ff00';
            ctx.shadowColor = '#00ff00';
        } else if (c < -5) {
            ctx.strokeStyle = '#ff3333';
            ctx.shadowColor = '#ff3333';
        } else {
            ctx.strokeStyle = '#ff9900';
            ctx.shadowColor = '#ff9900';
        }
        
        ctx.shadowBlur = 10;
        ctx.lineWidth = 4;
        ctx.stroke();
        ctx.shadowBlur = 0; // reset
        
        // Center pivot
        ctx.beginPath();
        ctx.arc(cx, cy, 10, 0, 2 * Math.PI);
        ctx.fillStyle = '#fff';
        ctx.fill();
    }

    function updatePitch() {
        if (!isDetecting) return;
        
        analyser.getFloatTimeDomainData(dataArray);
        let pitch = autoCorrelate(dataArray, audioCtx.sampleRate);
        
        if (pitch == -1) {
            // No sound
            drawMeter(0);
            noteNameEl.innerText = "--";
            centsDisplayEl.innerText = "";
            statusTextEl.innerText = "Mendengarkan...";
            noteNameEl.className = "note-display";
        } else {
            let note = noteFromPitch(pitch);
            let noteName = noteStrings[note % 12];
            let cents = centsOffFromPitch(pitch, note);
            
            noteNameEl.innerText = noteName;
            centsDisplayEl.innerText = `${cents > 0 ? '+' : ''}${cents} cents`;
            
            noteNameEl.className = "note-display"; // reset
            if (Math.abs(cents) < 5) {
                noteNameEl.classList.add("note-perfect");
                statusTextEl.innerText = "Tepat!";
                statusTextEl.style.color = "#00ff00";
            } else if (cents < -5) {
                noteNameEl.classList.add("note-low");
                statusTextEl.innerText = "Terlalu Rendah!";
                statusTextEl.style.color = "#ff3333";
            } else {
                noteNameEl.classList.add("note-high");
                statusTextEl.innerText = "Terlalu Tinggi!";
                statusTextEl.style.color = "#ff9900";
            }
            
            drawMeter(cents);
        }
        
        animationId = requestAnimationFrame(updatePitch);
    }

    async function startMic() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioCtx.createAnalyser();
            analyser.fftSize = 2048;
            
            microphone = audioCtx.createMediaStreamSource(stream);
            microphone.connect(analyser);
            
            bufferLength = analyser.fftSize;
            dataArray = new Float32Array(bufferLength);
            
            isDetecting = true;
            micBtn.innerHTML = '<i class="fas fa-stop me-2"></i> Berhenti Deteksi';
            micBtn.classList.replace('btn-primary', 'btn-danger');
            
            updatePitch();
            
        } catch (err) {
            alert("Error mengakses mikrofon: " + err);
        }
    }

    function stopMic() {
        isDetecting = false;
        cancelAnimationFrame(animationId);
        if (microphone) microphone.disconnect();
        if (audioCtx) audioCtx.close();
        
        micBtn.innerHTML = '<i class="fas fa-microphone me-2"></i> Mulai Deteksi';
        micBtn.classList.replace('btn-danger', 'btn-primary');
        noteNameEl.innerText = "--";
        noteNameEl.className = "note-display";
        centsDisplayEl.innerText = "0 cents";
        statusTextEl.innerText = "Tekan tombol untuk mulai";
        statusTextEl.style.color = "white";
        drawMeter(0);
    }

    micBtn.addEventListener('click', () => {
        if (isDetecting) {
            stopMic();
        } else {
            startMic();
        }
    });
    
    // Initial draw
    drawMeter(0);
</script>
"""

@app.route('/recording-studio')
def recording_studio():
    return render_layout(RECORDING_STUDIO_HTML)

RECORDING_STUDIO_HTML = """
<style>
    .studio-container {
        background: rgba(15, 15, 20, 0.85);
        border-radius: 30px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 10px 40px rgba(0,0,0,0.5), inset 0 0 20px rgba(255,255,255,0.05);
        backdrop-filter: blur(25px);
        padding: 30px;
        text-align: center;
        max-width: 700px;
        width: 100%;
        margin: 0 auto;
    }
    .viewfinder-wrapper {
        position: relative;
        width: 100%;
        border-radius: 20px;
        overflow: hidden;
        background: #000;
        margin-bottom: 20px;
        box-shadow: 0 0 20px rgba(0,0,0,0.8);
        border: 2px solid rgba(255,255,255,0.1);
    }
    #previewVideo, #playbackVideo {
        width: 100%;
        display: block;
        transform: scaleX(-1); /* Mirror effect like front camera */
    }
    #playbackVideo {
        transform: scaleX(1); /* Playback shouldn't be mirrored usually, but keeping consistent is fine. Let's not mirror playback. */
    }
    
    .record-btn-container {
        position: absolute;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 10;
    }
    .record-btn {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: #ff3333;
        border: 4px solid white;
        box-shadow: 0 0 15px rgba(255, 51, 51, 0.8);
        cursor: pointer;
        transition: all 0.3s;
    }
    .record-btn.recording {
        border-radius: 10px;
        animation: pulse-record 1.5s infinite;
    }
    @keyframes pulse-record {
        0% { box-shadow: 0 0 10px rgba(255, 51, 51, 0.8); }
        50% { box-shadow: 0 0 30px rgba(255, 51, 51, 1); }
        100% { box-shadow: 0 0 10px rgba(255, 51, 51, 0.8); }
    }
    .status-indicator {
        position: absolute;
        top: 20px;
        left: 20px;
        background: rgba(0,0,0,0.6);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .red-dot {
        width: 10px;
        height: 10px;
        background: red;
        border-radius: 50%;
        display: inline-block;
        opacity: 0;
    }
    .recording .red-dot {
        animation: blink 1s infinite;
    }
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
</style>

<div class="container d-flex flex-column justify-content-center align-items-center" style="min-height: 80vh;">
    <div class="studio-container">
        <h3 class="text-white opacity-90 mb-4 text-uppercase letter-spacing-1 fw-bold">
            <i class="fas fa-video me-2 text-danger"></i>Studio Sandbox Rekaman
        </h3>
        
        <div id="cameraSection">
            <div class="viewfinder-wrapper">
                <div class="status-indicator" id="statusIndicator">
                    <span class="red-dot"></span> <span id="statusText">Ready</span>
                </div>
                <video id="previewVideo" autoplay muted playsinline></video>
                <div class="record-btn-container">
                    <div class="record-btn" id="recordBtn" onclick="toggleRecording()"></div>
                </div>
            </div>
            <p class="text-white-50 small">Tekan tombol merah untuk merekam sesi latihanmu!</p>
        </div>
        
        <div id="playbackSection" style="display: none;">
            <div class="viewfinder-wrapper">
                <video id="playbackVideo" controls playsinline></video>
            </div>
            
            <div class="d-flex justify-content-center gap-3">
                <button class="btn btn-outline-light rounded-pill px-4" onclick="retakeVideo()">
                    <i class="fas fa-redo me-2"></i> Rekam Ulang
                </button>
                <button class="btn btn-primary rounded-pill px-4" onclick="uploadToGallery()" id="uploadBtn">
                    <i class="fas fa-cloud-upload-alt me-2"></i> Simpan ke Galeri
                </button>
            </div>
        </div>
    </div>
</div>

<script>
    const previewVideo = document.getElementById('previewVideo');
    const playbackVideo = document.getElementById('playbackVideo');
    const recordBtn = document.getElementById('recordBtn');
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    const cameraSection = document.getElementById('cameraSection');
    const playbackSection = document.getElementById('playbackSection');
    const uploadBtn = document.getElementById('uploadBtn');

    let mediaRecorder;
    let recordedChunks = [];
    let stream;
    let recordedBlob;

    async function initCamera() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            previewVideo.srcObject = stream;
        } catch (err) {
            alert("Error mengakses kamera/mikrofon: " + err);
        }
    }

    function toggleRecording() {
        if (!mediaRecorder || mediaRecorder.state === 'inactive') {
            startRecording();
        } else if (mediaRecorder.state === 'recording') {
            stopRecording();
        }
    }

    function startRecording() {
        recordedChunks = [];
        try {
            // Attempt to use webm, fallback to mp4
            let options = { mimeType: 'video/webm;codecs=vp9,opus' };
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                options = { mimeType: 'video/mp4' };
            }
            mediaRecorder = new MediaRecorder(stream, options);
        } catch(e) {
            mediaRecorder = new MediaRecorder(stream);
        }
        
        mediaRecorder.ondataavailable = handleDataAvailable;
        mediaRecorder.onstop = handleStop;
        
        mediaRecorder.start();
        recordBtn.classList.add('recording');
        statusIndicator.classList.add('recording');
        statusText.innerText = "REC";
    }

    function handleDataAvailable(event) {
        if (event.data.size > 0) {
            recordedChunks.push(event.data);
        }
    }

    function stopRecording() {
        mediaRecorder.stop();
        recordBtn.classList.remove('recording');
        statusIndicator.classList.remove('recording');
        statusText.innerText = "Ready";
    }

    function handleStop() {
        recordedBlob = new Blob(recordedChunks, { type: 'video/webm' });
        const videoURL = URL.createObjectURL(recordedBlob);
        
        playbackVideo.src = videoURL;
        
        // UI Transition
        cameraSection.style.display = 'none';
        playbackSection.style.display = 'block';
    }

    function retakeVideo() {
        playbackVideo.pause();
        playbackVideo.removeAttribute('src');
        playbackVideo.load();
        
        playbackSection.style.display = 'none';
        cameraSection.style.display = 'block';
    }

    function uploadToGallery() {
        if (!recordedBlob) return;
        
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Mengunggah...';
        
        // Construct FormData to match /gallery POST requirements
        const formData = new FormData();
        // Fallback filename. The allowed extensions in Python includes webm/mp4
        const file = new File([recordedBlob], "studio_recording.webm", { type: "video/webm" });
        formData.append('image', file); // Field name is 'image' in python code
        formData.append('student_name', "Siswa (Studio Mode)");
        
        let now = new Date();
        formData.append('title', "Latihan Rekaman " + now.toLocaleTimeString());

        fetch('/gallery', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) {
                alert("Berhasil disimpan ke Galeri Karya!");
                window.location.href = '/gallery';
            } else {
                alert("Gagal menyimpan video.");
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = '<i class="fas fa-cloud-upload-alt me-2"></i> Simpan ke Galeri';
            }
        })
        .catch(err => {
            console.error(err);
            alert("Terjadi kesalahan jaringan.");
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = '<i class="fas fa-cloud-upload-alt me-2"></i> Simpan ke Galeri';
        });
    }

    // Initialize camera on load
    window.addEventListener('load', initCamera);
    
    // Stop stream when leaving
    window.addEventListener('beforeunload', () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    });
</script>
"""

@app.route('/scrolling-sheet')
def scrolling_sheet():
    return render_layout(SCROLLING_SHEET_HTML)

SCROLLING_SHEET_HTML = """
<style>
    .sheet-container {
        background: rgba(10, 10, 15, 0.9);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 10px 40px rgba(0,0,0,0.8), inset 0 0 30px rgba(255,255,255,0.05);
        padding: 30px;
        text-align: center;
        max-width: 900px;
        width: 100%;
        margin: 0 auto;
    }
    .canvas-wrapper {
        position: relative;
        width: 100%;
        height: 250px;
        background: rgba(0, 0, 0, 0.5);
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 20px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    #sheetCanvas {
        width: 100%;
        height: 100%;
        display: block;
    }
    .target-box {
        position: absolute;
        top: 0;
        left: 20%;
        width: 40px;
        height: 100%;
        background: rgba(0, 255, 204, 0.1);
        border-left: 2px solid #00ffcc;
        border-right: 2px solid #00ffcc;
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.5);
        pointer-events: none;
    }
    .controls {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 20px;
        background: rgba(255,255,255,0.05);
        padding: 15px;
        border-radius: 15px;
    }
</style>

<div class="container d-flex flex-column justify-content-center align-items-center" style="min-height: 80vh;">
    <div class="sheet-container">
        <h3 class="text-white opacity-90 mb-4 text-uppercase letter-spacing-1 fw-bold">
            <i class="fas fa-scroll me-2 text-warning"></i>Papan Partitur Berjalan
        </h3>
        
        <div class="canvas-wrapper" id="canvasWrapper">
            <div class="target-box" id="targetBox"></div>
            <canvas id="sheetCanvas"></canvas>
        </div>
        
        <div class="controls flex-wrap">
            <div class="d-flex align-items-center gap-2">
                <span class="text-white-50 small fw-bold">TEMPO:</span>
                <input type="range" class="form-range" min="40" max="180" value="80" id="tempoSlider" style="width: 150px;">
                <span class="text-white fw-bold" id="tempoVal">80 BPM</span>
            </div>
            
            <button id="playSheetBtn" class="btn btn-primary rounded-pill px-4 fw-bold">
                <i class="fas fa-play me-2"></i> MULAI
            </button>
        </div>
        <p class="text-white-50 small mt-3 mb-0">Baca dan mainkan not yang melewati garis target hijau!</p>
    </div>
</div>

<script>
    const canvas = document.getElementById('sheetCanvas');
    const ctx = canvas.getContext('2d');
    const wrapper = document.getElementById('canvasWrapper');
    const tempoSlider = document.getElementById('tempoSlider');
    const tempoVal = document.getElementById('tempoVal');
    const playBtn = document.getElementById('playSheetBtn');
    
    function resizeCanvas() {
        canvas.width = wrapper.clientWidth;
        canvas.height = wrapper.clientHeight;
        drawStaffLines(); // Redraw static background immediately
    }
    window.addEventListener('resize', resizeCanvas);
    
    let isPlaying = false;
    let animationId;
    let notes = [];
    let bpm = 80;
    let speed = 2; // pixels per frame
    let nextSpawnTime = 0;
    let msPerBeat = 60000 / bpm;
    
    // Treble clef staff lines configuration
    const lineSpacing = 15;
    const staffTopY = 80;
    const staffLines = 5;
    
    // Note positions mapped to Y coordinates
    // Middle C is below the staff with a ledger line
    const notePositions = {
        'C4': staffTopY + (lineSpacing * 5), // Ledger line
        'D4': staffTopY + (lineSpacing * 4.5),
        'E4': staffTopY + (lineSpacing * 4), // Line 1
        'F4': staffTopY + (lineSpacing * 3.5),// Space 1
        'G4': staffTopY + (lineSpacing * 3), // Line 2
        'A4': staffTopY + (lineSpacing * 2.5),// Space 2
        'B4': staffTopY + (lineSpacing * 2), // Line 3
        'C5': staffTopY + (lineSpacing * 1.5),// Space 3
        'D5': staffTopY + (lineSpacing * 1), // Line 4
        'E5': staffTopY + (lineSpacing * 0.5),// Space 4
        'F5': staffTopY                            // Line 5
    };
    
    const noteKeys = Object.keys(notePositions);

    function drawStaffLines() {
        ctx.strokeStyle = "rgba(255, 255, 255, 0.4)";
        ctx.lineWidth = 1;
        ctx.shadowBlur = 5;
        ctx.shadowColor = "rgba(255, 255, 255, 0.5)";
        
        ctx.beginPath();
        for (let i = 0; i < staffLines; i++) {
            let y = staffTopY + (i * lineSpacing);
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
        }
        ctx.stroke();
        ctx.shadowBlur = 0;
    }

    function spawnNote() {
        const randomKey = noteKeys[Math.floor(Math.random() * noteKeys.length)];
        const yPos = notePositions[randomKey];
        
        notes.push({
            x: canvas.width + 20,
            y: yPos,
            name: randomKey,
            hasLedger: (randomKey === 'C4')
        });
        
        nextSpawnTime = performance.now() + msPerBeat;
    }

    function drawNote(note) {
        // Draw Ledger Line if needed (Middle C)
        if (note.hasLedger) {
            ctx.strokeStyle = "white";
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(note.x - 12, note.y);
            ctx.lineTo(note.x + 12, note.y);
            ctx.stroke();
        }
        
        // Draw Note Head (Ellipse)
        ctx.fillStyle = "#ffffff";
        ctx.shadowBlur = 15;
        ctx.shadowColor = "#ffffff";
        
        ctx.beginPath();
        ctx.ellipse(note.x, note.y, 8, 6, -Math.PI/4, 0, 2 * Math.PI);
        ctx.fill();
        
        // Draw Stem
        ctx.shadowBlur = 0;
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 2;
        ctx.beginPath();
        if (note.y > staffTopY + (lineSpacing * 2)) {
            // Stem goes up (right side)
            ctx.moveTo(note.x + 7, note.y - 2);
            ctx.lineTo(note.x + 7, note.y - 35);
        } else {
            // Stem goes down (left side)
            ctx.moveTo(note.x - 7, note.y + 2);
            ctx.lineTo(note.x - 7, note.y + 35);
        }
        ctx.stroke();
        
        // Text label
        ctx.fillStyle = "rgba(255,255,255,0.7)";
        ctx.font = "10px Inter";
        ctx.fillText(note.name, note.x - 6, note.y + 20);
    }

    function animate(timestamp) {
        if (!isPlaying) return;
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        drawStaffLines();
        
        if (timestamp >= nextSpawnTime) {
            spawnNote();
        }
        
        // Update and draw notes
        for (let i = notes.length - 1; i >= 0; i--) {
            let note = notes[i];
            note.x -= speed;
            
            drawNote(note);
            
            // Remove if offscreen
            if (note.x < -30) {
                notes.splice(i, 1);
            }
        }
        
        animationId = requestAnimationFrame(animate);
    }

    function togglePlay() {
        if (isPlaying) {
            isPlaying = false;
            cancelAnimationFrame(animationId);
            playBtn.innerHTML = '<i class="fas fa-play me-2"></i> MULAI';
            playBtn.classList.replace('btn-danger', 'btn-primary');
        } else {
            isPlaying = true;
            notes = [];
            nextSpawnTime = performance.now();
            playBtn.innerHTML = '<i class="fas fa-stop me-2"></i> BERHENTI';
            playBtn.classList.replace('btn-primary', 'btn-danger');
            requestAnimationFrame(animate);
        }
    }

    tempoSlider.addEventListener('input', (e) => {
        bpm = parseInt(e.target.value);
        tempoVal.innerText = bpm + " BPM";
        msPerBeat = 60000 / bpm;
        // Adjust speed pixel calculation roughly based on BPM
        speed = (bpm / 60) * 2; 
    });

    playBtn.addEventListener('click', togglePlay);
    
    // Initial setup
    resizeCanvas();
    drawStaffLines();
</script>
"""

@app.route('/jamming-track')
def jamming_track():
    return render_layout(JAMMING_TRACK_HTML)

JAMMING_TRACK_HTML = """
<style>
    .jamming-container {
        background: rgba(15, 20, 25, 0.85);
        border-radius: 30px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 10px 40px rgba(0,0,0,0.5), inset 0 0 20px rgba(255,255,255,0.05);
        backdrop-filter: blur(25px);
        padding: 40px 30px;
        text-align: center;
        max-width: 600px;
        width: 100%;
        margin: 0 auto;
    }
    .vinyl-record {
        width: 150px;
        height: 150px;
        background: #111;
        border-radius: 50%;
        margin: 0 auto 30px;
        border: 5px solid #333;
        position: relative;
        box-shadow: 0 10px 20px rgba(0,0,0,0.5);
        transition: transform 0.2s;
    }
    .vinyl-record::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 50px;
        height: 50px;
        background: var(--brand-color, #E5322D);
        border-radius: 50%;
    }
    .vinyl-record::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 10px;
        height: 10px;
        background: #fff;
        border-radius: 50%;
    }
    .vinyl-record.spinning {
        animation: spin 2s linear infinite;
    }
    @keyframes spin {
        100% { transform: rotate(360deg); }
    }
    
    .eq-bars {
        display: flex;
        justify-content: center;
        align-items: flex-end;
        height: 40px;
        gap: 4px;
        margin-bottom: 20px;
    }
    .eq-bar {
        width: 8px;
        background: #00ffcc;
        border-radius: 4px 4px 0 0;
        transition: height 0.1s ease;
    }
    
    .custom-select-wrapper {
        position: relative;
        margin-bottom: 20px;
    }
    .custom-select-wrapper select {
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        color: white;
        padding: 12px 20px;
        border-radius: 12px;
        width: 100%;
        appearance: none;
        cursor: pointer;
    }
    .custom-select-wrapper select:focus {
        outline: none;
        border-color: #00ffcc;
    }
    .custom-select-wrapper select option {
        background: #222;
        color: white;
    }
    .custom-select-wrapper::after {
        content: '▼';
        position: absolute;
        right: 20px;
        top: 50%;
        transform: translateY(-50%);
        color: rgba(255,255,255,0.5);
        pointer-events: none;
    }
</style>

<div class="container d-flex flex-column justify-content-center align-items-center" style="min-height: 80vh;">
    <div class="jamming-container">
        <h3 class="text-white opacity-90 mb-4 text-uppercase letter-spacing-1 fw-bold">
            <i class="fas fa-compact-disc me-2 text-primary"></i>Teman Jamming
        </h3>
        
        <div class="vinyl-record" id="vinyl"></div>
        
        <div class="eq-bars" id="eqBars">
            <div class="eq-bar" style="height: 10px;"></div>
            <div class="eq-bar" style="height: 10px;"></div>
            <div class="eq-bar" style="height: 10px;"></div>
            <div class="eq-bar" style="height: 10px;"></div>
            <div class="eq-bar" style="height: 10px;"></div>
            <div class="eq-bar" style="height: 10px;"></div>
            <div class="eq-bar" style="height: 10px;"></div>
        </div>
        
        <div class="row g-3">
            <div class="col-6">
                <div class="custom-select-wrapper">
                    <select id="keySelect">
                        <option value="C">C Major</option>
                        <option value="D">D Major</option>
                        <option value="E">E Major</option>
                        <option value="F">F Major</option>
                        <option value="G">G Major</option>
                        <option value="A">A Major</option>
                    </select>
                </div>
            </div>
            <div class="col-6">
                <div class="custom-select-wrapper">
                    <select id="genreSelect">
                        <option value="pop_rock.mp3">Pop Rock</option>
                        <option value="jazz_swing.mp3">Jazz Swing</option>
                    </select>
                </div>
            </div>
        </div>
        
        <div class="d-flex align-items-center justify-content-center gap-3 mt-4">
            <button class="btn btn-outline-light rounded-circle" style="width: 50px; height: 50px;">
                <i class="fas fa-backward"></i>
            </button>
            <button id="playBtn" class="btn btn-primary rounded-circle shadow-lg" style="width: 70px; height: 70px; font-size: 1.5rem;" onclick="toggleAudio()">
                <i class="fas fa-play" style="margin-left: 5px;"></i>
            </button>
            <button class="btn btn-outline-light rounded-circle" style="width: 50px; height: 50px;">
                <i class="fas fa-forward"></i>
            </button>
        </div>
        
        <div class="mt-4 d-flex align-items-center gap-3">
            <i class="fas fa-volume-down text-white-50"></i>
            <input type="range" class="form-range" id="volumeSlider" min="0" max="1" step="0.01" value="0.7">
            <i class="fas fa-volume-up text-white-50"></i>
        </div>
    </div>
</div>

<!-- Hidden audio element -->
<audio id="jamAudio" loop preload="none"></audio>

<script>
    const audioEl = document.getElementById('jamAudio');
    const playBtn = document.getElementById('playBtn');
    const vinyl = document.getElementById('vinyl');
    const genreSelect = document.getElementById('genreSelect');
    const volumeSlider = document.getElementById('volumeSlider');
    const eqBars = document.querySelectorAll('.eq-bar');
    
    let isPlaying = false;
    let eqInterval;

    function setAudioSource() {
        // Construct URL based on selection
        const genreFile = genreSelect.value;
        audioEl.src = '/static/audio/' + genreFile;
    }

    function animateEQ() {
        eqBars.forEach(bar => {
            const h = 5 + Math.random() * 35;
            bar.style.height = h + 'px';
        });
    }

    function stopEQ() {
        eqBars.forEach(bar => {
            bar.style.height = '10px';
        });
    }

    function toggleAudio() {
        if (!audioEl.src || audioEl.src === window.location.href) {
            setAudioSource();
        }
        
        if (isPlaying) {
            audioEl.pause();
            isPlaying = false;
            playBtn.innerHTML = '<i class="fas fa-play" style="margin-left: 5px;"></i>';
            playBtn.classList.replace('btn-danger', 'btn-primary');
            vinyl.classList.remove('spinning');
            clearInterval(eqInterval);
            stopEQ();
        } else {
            // Because files might not exist actually, we handle promise rejection to avoid console spam breaking things visually
            let playPromise = audioEl.play();
            if (playPromise !== undefined) {
                playPromise.then(_ => {
                    // Playback started!
                }).catch(error => {
                    console.log("Audio playback failed (dummy file likely empty). Simulating playback.");
                });
            }
            
            isPlaying = true;
            playBtn.innerHTML = '<i class="fas fa-pause"></i>';
            playBtn.classList.replace('btn-primary', 'btn-danger');
            vinyl.classList.add('spinning');
            eqInterval = setInterval(animateEQ, 100);
        }
    }

    genreSelect.addEventListener('change', () => {
        const wasPlaying = isPlaying;
        if (wasPlaying) {
            toggleAudio(); // Stop current
        }
        setAudioSource();
        if (wasPlaying) {
            toggleAudio(); // Play new
        }
    });

    volumeSlider.addEventListener('input', (e) => {
        audioEl.volume = e.target.value;
    });
    
    // Set initial volume
    audioEl.volume = volumeSlider.value;
</script>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)
