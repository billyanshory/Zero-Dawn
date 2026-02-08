import os
import sqlite3
import datetime
from flask import Flask, request, send_from_directory, render_template_string, redirect, url_for, Response, jsonify
from werkzeug.utils import secure_filename

# --- KONFIGURASI FLASK ---
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB Limit
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff', 'ico', 'svg', 'mp3', 'wav', 'ogg', 'mp4', 'm4a', 'flac', 'srt', 'vtt'}

# --- DATABASE SETUP ---
DB_NAME = 'hamiart.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Gallery Table
    c.execute('''CREATE TABLE IF NOT EXISTS gallery (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image TEXT NOT NULL,
        student_name TEXT NOT NULL,
        title TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Tutors Table
    c.execute('''CREATE TABLE IF NOT EXISTS tutors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image TEXT NOT NULL,
        name TEXT NOT NULL,
        bio TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Pricing Table
    c.execute('''CREATE TABLE IF NOT EXISTS pricing (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        price TEXT NOT NULL,
        details TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Slots Table
    c.execute('''CREATE TABLE IF NOT EXISTS slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT NOT NULL,
        time TEXT NOT NULL,
        status TEXT DEFAULT 'Available',
        type TEXT DEFAULT 'General',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Join Requests Table
    c.execute('''CREATE TABLE IF NOT EXISTS join_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        interest TEXT NOT NULL,
        whatsapp TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # News Table
    c.execute('''CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        date TEXT NOT NULL,
        image TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

# --- PWA CONFIGURATION ---
MANIFEST_CONTENT = """
{
  "name": "hamiart.education",
  "short_name": "hamiart",
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
    <nav class="navbar navbar-expand-lg sticky-top">
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
                <a class="navbar-brand me-auto" href="/">hamiart.<span>education</span></a>
                
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
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            min-height: 80px; /* Allow growth */
            height: auto;
            z-index: 9999; /* Ensure on top */
            display: flex;
            justify-content: space-around;
            align-items: center;
            padding: 10px 0;
            background: rgba(0, 0, 0, 0.85) !important; /* Stronger contrast */
            backdrop-filter: blur(20px) !important;
            border-top: 1px solid rgba(255,255,255,0.2);
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
    <title>hamiart.education</title>
    <link rel="manifest" href="/manifest.json">
    <link rel="icon" href="{{ url_for('static', filename='hamiartlogo.png') }}">
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
        {{ navbar|safe }}
        
        <!-- Top Feature Navigation -->
        <div class="container">
            <div class="top-feature-nav">
                <a href="/gallery" class="feature-btn glass-panel">
                    <i class="fas fa-palette"></i>
                    Galeri Karya
                </a>
                <a href="/tutors" class="feature-btn glass-panel">
                    <i class="fas fa-chalkboard-teacher"></i>
                    Profil Pengajar
                </a>
                <a href="/pricing" class="feature-btn glass-panel">
                    <i class="fas fa-tags"></i>
                    Paket & Biaya
                </a>
                <a href="/slots" class="feature-btn glass-panel">
                    <i class="fas fa-calendar-alt"></i>
                    Jadwal Slot
                </a>
                <a href="/join" class="feature-btn glass-panel">
                    <i class="fas fa-file-signature"></i>
                    Pendaftaran
                </a>
                <a href="/news" class="feature-btn glass-panel">
                    <i class="fas fa-trophy"></i>
                    Prestasi & Event
                </a>
            </div>
        </div>

        <div class="container main-content" style="flex: 1;">
            {{ content|safe }}
        </div>
        
        <footer class="main-footer" style="background: transparent; border: none; color: rgba(255,255,255,0.7); padding: 20px; text-align: center;">
            <div class="container">
                <p>&copy; 2026 hamiart.education - All Rights Reserved. "We Making The Time"</p>
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
    conn = get_db_connection()
    if request.method == 'POST':
        if 'image' not in request.files:
            return redirect(request.url)
        file = request.files['image']
        student_name = request.form['student_name']
        title = request.form['title']
        
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            conn.execute('INSERT INTO gallery (image, student_name, title) VALUES (?, ?, ?)',
                         (filename, student_name, title))
            conn.commit()
            conn.close()
            return redirect(url_for('gallery'))
            
    items = conn.execute('SELECT * FROM gallery ORDER BY created_at DESC').fetchall()
    conn.close()
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
    conn = get_db_connection()
    if request.method == 'POST':
        if 'image' not in request.files:
            return redirect(request.url)
        file = request.files['image']
        name = request.form['name']
        bio = request.form['bio']
        
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            conn.execute('INSERT INTO tutors (image, name, bio) VALUES (?, ?, ?)',
                         (filename, name, bio))
            conn.commit()
            conn.close()
            return redirect(url_for('tutors'))
            
    items = conn.execute('SELECT * FROM tutors ORDER BY created_at DESC').fetchall()
    conn.close()
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
    conn = get_db_connection()
    if request.method == 'POST':
        title = request.form['title']
        price = request.form['price']
        details = request.form['details']
        
        conn.execute('INSERT INTO pricing (title, price, details) VALUES (?, ?, ?)',
                     (title, price, details))
        conn.commit()
        conn.close()
        return redirect(url_for('pricing'))
            
    items = conn.execute('SELECT * FROM pricing ORDER BY created_at ASC').fetchall()
    conn.close()
    return render_layout(PRICING_HTML_CONTENT, items=items)

PRICING_HTML_CONTENT = """
<div class="container glass-panel p-4 mb-5 position-relative" style="border-radius: 20px;">
    <a href="/" class="position-absolute top-0 end-0 m-3 text-white text-decoration-none" style="font-size: 1.5rem; opacity: 0.7; transition: 0.2s;" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0.7"><i class="fas fa-times"></i></a>

    <div class="d-flex justify-content-between align-items-center mb-4 pe-4">
        <h2 class="text-white mb-0"><i class="fas fa-tags me-2"></i>Paket & Biaya</h2>
        <button class="btn btn-light rounded-pill" data-bs-toggle="modal" data-bs-target="#pricingModal">
            <i class="fas fa-plus me-1"></i> Tambah Paket
        </button>
    </div>
    
    <div class="row g-4">
        {% for item in items %}
        <div class="col-md-4">
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
"""

@app.route('/slots', methods=['GET', 'POST'])
def slots():
    conn = get_db_connection()
    if request.method == 'POST':
        if 'day' in request.form:
            # Add Slot
            day = request.form['day']
            time = request.form['time']
            type_val = request.form['type']
            status = 'Available'
            
            conn.execute('INSERT INTO slots (day, time, status, type) VALUES (?, ?, ?, ?)',
                         (day, time, status, type_val))
            conn.commit()
            
        elif 'toggle_id' in request.form:
            # Toggle Status
            slot_id = request.form['toggle_id']
            current_status = conn.execute('SELECT status FROM slots WHERE id = ?', (slot_id,)).fetchone()['status']
            new_status = 'Booked' if current_status == 'Available' else 'Available'
            conn.execute('UPDATE slots SET status = ? WHERE id = ?', (new_status, slot_id))
            conn.commit()
            
        conn.close()
        return redirect(url_for('slots'))
            
    # Fetch and Group Slots
    slots_raw = conn.execute('SELECT * FROM slots ORDER BY day, time').fetchall()
    conn.close()
    
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
        conn = get_db_connection()
        name = request.form['name']
        age = request.form['age']
        interest = request.form['interest']
        whatsapp = request.form['whatsapp']
        
        conn.execute('INSERT INTO join_requests (name, age, interest, whatsapp) VALUES (?, ?, ?, ?)',
                     (name, age, interest, whatsapp))
        conn.commit()
        conn.close()
        
        message = f"Halo Admin Hamiart, saya ingin mendaftar.\nNama: {name}\nUmur: {age}\nMinat: {interest}\nNo WA: {whatsapp}"
        wa_url = f"https://wa.me/6285250861236?text={quote(message)}"
        
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
    conn = get_db_connection()
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
        
        conn.execute('INSERT INTO news (title, content, date, image) VALUES (?, ?, ?, ?)',
                     (title, content, date, filename))
        conn.commit()
        conn.close()
        return redirect(url_for('news'))
            
    items = conn.execute('SELECT * FROM news ORDER BY date DESC, created_at DESC').fetchall()
    conn.close()
    return render_layout(NEWS_HTML_CONTENT, items=items)

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
            <div class="card h-100 bg-transparent glass-panel border-0 overflow-hidden" style="border-radius: 20px;">
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

            osc.frequency.value = (beatNumber % 4 === 0) ? 1000 : 800;
            envelope.gain.value = 1;
            envelope.gain.exponentialRampToValueAtTime(0.001, time + 0.05);

            osc.connect(envelope);
            envelope.connect(this.audioContext.destination);

            osc.start(time);
            osc.stop(time + 0.05);
            
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

        <h2 class="text-white mb-4 fw-bold text-uppercase letter-spacing-1"><i class="fas fa-ear-listen me-2 text-warning"></i>Tebak Nada</h2>
        
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
            playTone(currentNote.freq);
        }
        document.getElementById('instruction').innerText = "Tebak nada apa ini?";
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

@app.route('/uploads/icon-192.png')
def icon_192():
    if os.path.exists('logo_config.txt'):
        with open('logo_config.txt', 'r') as f:
            filename = f.read().strip()
            if filename and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    # Fallback to static/hamiartlogo.png
    return send_from_directory('static', 'hamiartlogo.png')

@app.route('/uploads/icon-512.png')
def icon_512():
    if os.path.exists('logo_config.txt'):
        with open('logo_config.txt', 'r') as f:
            filename = f.read().strip()
            if filename and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    return send_from_directory('static', 'hamiartlogo.png')

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
