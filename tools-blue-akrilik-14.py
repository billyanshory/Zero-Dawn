import io
import os
import zipfile
import math
import sqlite3
from flask import Flask, request, send_file, render_template_string, jsonify, send_from_directory, redirect, url_for, session, flash
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter, Transformation, PageObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from werkzeug.utils import secure_filename

# --- KONFIGURASI FLASK ---
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB Limit
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff', 'ico', 'svg', 'mp3', 'wav', 'ogg', 'mp4', 'm4a', 'flac', 'srt', 'vtt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tabulasi (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    no_urut TEXT,
                    nama_lengkap TEXT,
                    nik TEXT,
                    jenis_kelamin TEXT,
                    tempat_lahir TEXT,
                    tanggal_lahir TEXT,
                    agama TEXT,
                    pendidikan TEXT,
                    jenis_pekerjaan TEXT,
                    golongan_darah TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# --- FRONTEND (HTML/CSS/JS) ---

# Navbar fragment to reuse
NAVBAR_HTML = """
    <style>
        .navbar {
            background-color: transparent !important;
            box-shadow: none !important;
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
        .logo-upload-btn {
            width: 55px; /* Increased size */
            height: 55px;
            border-radius: 50%;
            border: 2px solid rgba(255,255,255,0.5);
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(5px);
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        .logo-upload-btn:hover {
            border-color: white;
            box-shadow: 0 0 10px rgba(255,255,255,0.5);
        }
        .logo-upload-btn img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .logo-upload-btn i {
            color: rgba(255,255,255,0.7);
            font-size: 1.2rem;
        }
        /* Mobile Specific: Hide toggler, align logo right */
        .navbar-toggler {
            display: none !important;
        }
        .navbar .container {
            display: flex;
            justify-content: space-between; /* Brand Left, Logo Right */
            align-items: center;
        }
        /* Hide original collapse for safety/cleanup visually */
        .navbar-collapse {
            display: none !important;
        }
    </style>
    <nav class="navbar navbar-expand-lg sticky-top">
        <div class="container">
            <a class="navbar-brand" href="/">hamiart.<span>education</span></a>

            <!-- Direct Placement of Logo Button (Mobile & Desktop) -->
            <form action="/upload-logo" method="post" enctype="multipart/form-data" id="logo-form" style="margin: 0;">
                <input type="file" name="logo" id="logo-file" hidden onchange="document.getElementById('logo-form').submit()" accept="image/*">
                <div class="logo-upload-btn" onclick="document.getElementById('logo-file').click()" title="Upload Website Logo">
                    {% if logo_file %}
                        <img src="/uploads/{{ logo_file }}" alt="Logo">
                    {% else %}
                        <i class="fas fa-camera"></i>
                    {% endif %}
                </div>
            </form>

            <!-- Hidden Toggler & Menu (Deactivated) -->
            <button class="navbar-toggler" type="button" style="display:none"></button>
            <div class="collapse navbar-collapse" id="navbarNav" style="display:none">
                <ul class="navbar-nav me-auto"></ul>
            </div>
        </div>
    </nav>
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
    </style>
"""


# --- ROUTES ---

def render_page(content, **kwargs):
    # Inject fragments before rendering to allow Jinja to process them
    content = content.replace('{{ styles|safe }}', STYLES_HTML)
    content = content.replace('{{ navbar|safe }}', NAVBAR_HTML)
    return render_template_string(content, **kwargs)

@app.route('/')
def index():
    # Make doremifasolasido the main page
    bg_image = "default.jpg" # Fallback
    if os.path.exists('bg_config.txt'):
        with open('bg_config.txt', 'r') as f:
            content = f.read().strip()
            if content:
                bg_image = content

    logo_file = None
    if os.path.exists('logo_config.txt'):
         with open('logo_config.txt', 'r') as f:
            content = f.read().strip()
            if content:
                logo_file = content

    return render_page(HTML_DOREMI, bg_image=bg_image, logo_file=logo_file)

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


HTML_WALLPAPER = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wallpaper Blur Akrilik | ilikepdf</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    {{ styles|safe }}
    <style>
        body, html {
            height: 100%;
            margin: 0;
            overflow: hidden; /* Prevent scrolling if possible */
        }
        .wallpaper-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url('/uploads/{{ bg_image }}');
            background-size: cover;
            background-position: center;
            z-index: -2;
        }
        .acrylic-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            /* Config: [dark] r=0 g=0 b=0 a=120 -> rgba(0, 0, 0, 0.47) */
            background-color: rgba(0, 0, 0, 0.47);
            backdrop-filter: blur(20px) saturate(125%);
            -webkit-backdrop-filter: blur(20px) saturate(125%);
            z-index: -1;
        }
        .content-wrapper {
            position: relative;
            z-index: 1;
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        .center-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: white;
            text-align: center;
            width: 100%;
        }
        .upload-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 30px;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            max-width: 600px;
            width: 90%;
            margin-bottom: 20px;
        }
        .upload-card h2 {
            color: white !important;
        }
        .controls-container {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            justify-content: center;
            margin-bottom: 30px;
        }
        .acrylic-btn {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(5px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: white;
            padding: 10px 20px;
            border-radius: 10px;
            transition: 0.3s;
            text-decoration: none;
            cursor: pointer;
            display: inline-block;
            white-space: nowrap;
        }
        .acrylic-btn:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
            color: white;
        }
        .audio-player {
            position: fixed;
            bottom: 50px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px 30px;
            border-radius: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
            z-index: 100;
            box-shadow: 0 10px 40px rgba(0,0,0,0.6);
            width: 90%;
            max-width: 800px;
        }
        .player-row-top {
            width: 100%;
            padding: 0 5px;
        }
        .player-row-bottom {
            display: grid;
            grid-template-columns: 1fr auto 1fr; /* Left, Center (Play), Right */
            align-items: center;
            width: 100%;
        }
        .player-left {
            display: flex;
            align-items: center;
            gap: 15px;
            justify-content: flex-start;
        }
        .player-center {
            display: flex;
            align-items: center;
            gap: 20px;
            justify-content: center;
        }
        .player-right {
            display: flex;
            align-items: center;
            gap: 15px;
            justify-content: flex-end;
        }
        
        .player-btn {
            background: transparent;
            border: none;
            color: rgba(255,255,255,0.8);
            width: 35px;
            height: 35px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 1rem;
        }
        .player-btn:hover {
            color: white;
            transform: scale(1.1);
        }
        .player-btn.active {
            color: var(--brand-color);
        }
        .play-btn-large {
            width: 50px;
            height: 50px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            font-size: 1.4rem;
            color: white;
        }
        .play-btn-large:hover {
            background: white;
            color: black;
            transform: scale(1.05);
            box-shadow: 0 0 15px rgba(255,255,255,0.3);
        }

        /* Range Slider */
        input[type=range] {
            -webkit-appearance: none;
            width: 100%;
            background: transparent;
        }
        input[type=range]::-webkit-slider-thumb {
            -webkit-appearance: none;
            height: 14px;
            width: 14px;
            border-radius: 50%;
            background: white;
            cursor: pointer;
            margin-top: -5px;
            box-shadow: 0 0 5px rgba(0,0,0,0.3);
        }
        input[type=range]::-webkit-slider-runnable-track {
            width: 100%;
            height: 4px;
            cursor: pointer;
            background: rgba(255,255,255,0.2);
            border-radius: 2px;
        }
        
        .time-display, .db-display {
            font-size: 0.85rem;
            color: rgba(255,255,255,0.7);
            font-variant-numeric: tabular-nums;
            min-width: 40px;
        }
        
        #visualizer {
            position: absolute;
            top: 50%;
            left: 0;
            width: 100%;
            height: 300px;
            transform: translateY(-50%);
            z-index: 0;
            pointer-events: none;
            filter: blur(2px); /* Soft aesthetic blur */
        }

        #subtitle-overlay {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 10;
            color: white;
            font-size: 1.5rem;
            text-align: center;
            text-shadow: 0 0 10px rgba(255,255,255,0.8), 0 0 20px rgba(255,255,255,0.5);
            pointer-events: none;
            width: 80%;
            max-width: 800px;
            min-height: 1.5em;
        }
        
        /* Playlist Panel */
        .playlist-panel {
            position: fixed;
            bottom: 160px; /* Above player */
            right: 50px;
            width: 300px;
            max-height: 400px;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 15px;
            z-index: 101;
            display: none; /* Hidden by default */
            overflow-y: auto;
            color: white;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }
        .playlist-header {
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding-bottom: 10px;
            margin-bottom: 10px;
            font-weight: 700;
            display: flex;
            justify-content: space-between;
        }
        .playlist-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px;
            border-radius: 5px;
            cursor: pointer;
            transition: 0.2s;
            font-size: 0.9rem;
        }
        .playlist-item:hover {
            background: rgba(255,255,255,0.1);
        }
        .playlist-item.active {
            background: rgba(229, 50, 45, 0.2);
            color: var(--brand-color);
        }
        .playlist-actions {
            display: flex;
            gap: 5px;
        }
        .action-btn {
            background: transparent;
            border: none;
            color: rgba(255,255,255,0.5);
            cursor: pointer;
            font-size: 0.8rem;
        }
        .action-btn:hover { color: white; }
        .action-btn.delete:hover { color: #ff4444; }

        /* Fullscreen Button (Mobile Only) */
        #fullscreen-btn {
            display: none; /* Hidden by default */
            position: fixed;
            top: 72px; /* Adjusted to align better with menu button typically */
            right: 14px; /* Align with bootstrap container padding (approx 12px + 2px) */
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(5px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: rgba(255, 255, 255, 0.8);
            width: 56px;  /* Match standard toggler width approx */
            height: 40px; /* Match standard toggler height approx */
            border-radius: 5px; /* Match standard Bootstrap toggler radius */
            z-index: 1000;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        #fullscreen-btn .icon-container {
            position: relative;
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        #fullscreen-btn .corner {
            position: absolute;
            width: 8px;
            height: 8px;
            border-color: rgba(255, 255, 255, 0.8);
            border-style: solid;
        }
        #fullscreen-btn .tl { top: 3px; left: 3px; border-width: 2px 0 0 2px; }
        #fullscreen-btn .tr { top: 3px; right: 3px; border-width: 2px 2px 0 0; }
        #fullscreen-btn .bl { bottom: 3px; left: 3px; border-width: 0 0 2px 2px; }
        #fullscreen-btn .br { bottom: 3px; right: 3px; border-width: 0 2px 2px 0; }
        
        #fullscreen-btn .fa-lock, #fullscreen-btn .fa-lock-open {
            font-size: 0.9rem;
        }

        #fullscreen-btn.neon-glow {
            box-shadow: 0 0 15px rgba(255, 255, 255, 0.6), inset 0 0 10px rgba(255, 255, 255, 0.3);
            border-color: rgba(255, 255, 255, 0.8);
            color: white;
            text-shadow: 0 0 5px white;
        }

        /* Mobile Responsiveness */
        @media (max-width: 768px) {
            #fullscreen-btn {
                display: block;
            }
            /* Hide Dark/Light toggle on mobile */
            .navbar .btn-group {
                display: none !important;
            }
            /* Force white hamburger menu */
            .navbar-toggler {
                border-color: rgba(255,255,255,0.5) !important;
            }
            .navbar-toggler-icon {
                filter: brightness(0) invert(1) !important;
            }

            .audio-player {
                width: 95%;
                padding: 15px;
                bottom: 20px;
                gap: 10px;
            }
            .player-row-bottom {
                display: flex;
                flex-wrap: wrap;
                justify-content: space-between;
                row-gap: 15px;
            }
            .player-left {
                order: 2;
                width: 100%;
                justify-content: space-between;
                margin-top: 5px;
            }
            .player-center {
                order: 1;
                width: 100%;
                justify-content: center;
                margin-bottom: 5px;
            }
            .player-right {
                order: 3;
                width: 100%;
                justify-content: space-between;
                margin-top: 5px;
            }
            .player-right input[type=range] {
                width: 100% !important; 
            }
            /* Adjust playlist panel for mobile */
            .playlist-panel {
                right: 0;
                left: 0;
                margin: 0 auto;
                width: 95%;
                bottom: 240px; /* Above expanded player */
            }
        }

        /* Clean Mode Styles */
        body.clean-mode .navbar,
        body.clean-mode #fullscreen-btn,
        body.clean-mode .controls-container,
        body.clean-mode .audio-player,
        body.clean-mode .playlist-panel,
        body.clean-mode footer {
            display: none !important;
        }

        /* Restore/Broom Button */
        #restore-btn {
            display: none;
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: white;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            z-index: 3000;
            cursor: pointer;
            transition: 0.3s;
            justify-content: center;
            align-items: center;
            box-shadow: 0 0 15px rgba(255,255,255,0.2);
        }
        body.clean-mode #restore-btn {
            display: flex;
        }
        #restore-btn:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: scale(1.1);
        }

        /* Blur Config Panel */
        .blur-panel {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            padding: 25px;
            width: 300px;
            z-index: 2000;
            color: white;
            text-align: center;
            display: none;
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        }
        .blur-panel h4 { margin-bottom: 20px; font-weight: 700; }
        .blur-value { font-size: 1.2rem; margin-top: 10px; font-weight: bold; color: var(--brand-color); }
    </style>
</head>
<body>
    <div class="wallpaper-bg"></div>
    <div class="acrylic-overlay"></div>

    <div class="content-wrapper">
        {{ navbar|safe }}

        <!-- Fullscreen Button -->
        <button id="fullscreen-btn" onclick="toggleFullScreen()">
            <div class="icon-container">
                <div class="corner tl"></div>
                <div class="corner tr"></div>
                <div class="corner bl"></div>
                <div class="corner br"></div>
                <i class="fas fa-lock-open" id="fs-lock-icon"></i>
            </div>
        </button>

        <!-- Restore Button for Clean Mode -->
        <button id="restore-btn" onclick="exitCleanMode()" title="Clean All / Restore">
            <i class="fas fa-broom"></i>
        </button>

        <!-- Blur Settings Panel -->
        <div class="blur-panel" id="blur-panel">
            <h4>Blur Strength</h4>
            <input type="range" id="blur-slider" min="-100" max="100" value="0" oninput="updateBlur(this.value)">
            <div class="blur-value" id="blur-value-display">0</div>
            <button class="acrylic-btn mt-3" onclick="toggleBlurPanel()">Close</button>
        </div>
        
        <div class="center-content">
            <div class="controls-container">
                <!-- Wallpaper Upload -->
                <form action="/wallpaper-blur/upload" method="post" enctype="multipart/form-data" id="form-wall">
                    <input type="file" name="background" id="file-wall" hidden onchange="document.getElementById('form-wall').submit()" accept="image/*">
                    <button type="button" class="acrylic-btn" onclick="document.getElementById('file-wall').click()">
                        <i class="fas fa-image me-2"></i> Set Wallpaper
                    </button>
                </form>

                <!-- Audio Upload -->
                <form action="/wallpaper-blur/upload-audio" method="post" enctype="multipart/form-data" id="form-audio">
                    <input type="file" name="audio" id="file-audio" hidden onchange="document.getElementById('form-audio').submit()" accept="audio/*">
                    <button type="button" class="acrylic-btn" onclick="document.getElementById('file-audio').click()">
                        <i class="fas fa-music me-2"></i> Set Audio
                    </button>
                </form>

                <!-- Subtitle Upload -->
                <form action="/wallpaper-blur/upload-subtitle" method="post" enctype="multipart/form-data" id="form-sub">
                    <input type="file" name="subtitle" id="file-sub" hidden onchange="document.getElementById('form-sub').submit()" accept=".srt,.vtt">
                    <button type="button" class="acrylic-btn" onclick="document.getElementById('file-sub').click()">
                        <i class="fas fa-closed-captioning me-2"></i> Set Subtitle
                    </button>
                </form>

                <!-- Set Blur Button -->
                <button type="button" class="acrylic-btn" onclick="toggleBlurPanel()">
                    <i class="fas fa-sliders-h me-2"></i> Set Blur
                </button>

                <!-- Set Clean Button -->
                <button type="button" class="acrylic-btn" onclick="enterCleanMode()">
                    <i class="fas fa-broom me-2"></i> Set Clean
                </button>
            </div>
            
            {% if audio_file %}
            <!-- Visualizer Overlay -->
            <canvas id="visualizer"></canvas>
            
            <div id="subtitle-overlay"></div>

            <div class="audio-player">
                <audio id="main-audio" crossorigin="anonymous">
                    <source src="/uploads/{{ audio_file }}" id="audio-source">
                </audio>
                
                <!-- Top Row: Progress -->
                <div class="player-row-top">
                    <input type="range" id="seek-slider" min="0" max="100" value="0">
                </div>
                
                <!-- Bottom Row: Controls -->
                <div class="player-row-bottom">
                    <!-- Left Section: Time, Shuffle, Repeat -->
                    <div class="player-left">
                        <span class="time-display" id="time-display">00:00</span>
                        <button class="player-btn" onclick="toggleShuffle()" title="Shuffle" id="btn-shuffle"><i class="fas fa-random"></i></button>
                        <button class="player-btn" onclick="toggleRepeat()" title="Repeat" id="btn-repeat"><i class="fas fa-redo"></i></button>
                    </div>
                    
                    <!-- Center Section: Stop, Prev, PLAY, Next -->
                    <div class="player-center">
                        <button class="player-btn" onclick="stopAudio()" title="Stop"><i class="fas fa-stop"></i></button>
                        <button class="player-btn" onclick="skip(-5)"><i class="fas fa-backward"></i></button>
                        <button class="player-btn play-btn-large" onclick="togglePlay()"><i class="fas fa-play" id="play-icon"></i></button>
                        <button class="player-btn" onclick="skip(5)"><i class="fas fa-forward"></i></button>
                    </div>
                    
                    <!-- Right Section: Volume, Playlist -->
                    <div class="player-right">
                        <i class="fas fa-volume-up" id="vol-icon" style="color:rgba(255,255,255,0.7)"></i>
                        <div style="width: 80px;">
                            <input type="range" id="vol-slider" min="0" max="1" step="0.01" value="1">
                        </div>
                        <span class="db-display" id="db-display">0 dB</span>
                        <button class="player-btn" onclick="togglePlaylist()" title="Playlist" id="btn-playlist"><i class="fas fa-list"></i></button>
                    </div>
                </div>
            </div>

            <!-- Playlist Modal -->
            <div class="playlist-panel" id="playlist-panel">
                <div class="playlist-header">
                    <span>Playlist</span>
                    <i class="fas fa-times" onclick="togglePlaylist()" style="cursor:pointer"></i>
                </div>
                <div id="playlist-items">
                    <!-- Items injected by JS -->
                </div>
            </div>

            <form id="rename-form" action="/wallpaper-blur/rename-audio" method="post" style="display:none">
                <input type="hidden" name="old_name" id="rename-old">
                <input type="hidden" name="new_name" id="rename-new">
            </form>

            <script>
                const audio = document.getElementById('main-audio');
                const sourceEl = document.getElementById('audio-source');
                const playIcon = document.getElementById('play-icon');
                const seekSlider = document.getElementById('seek-slider');
                const timeDisplay = document.getElementById('time-display');
                const volSlider = document.getElementById('vol-slider');
                const dbDisplay = document.getElementById('db-display');
                const btnShuffle = document.getElementById('btn-shuffle');
                const btnRepeat = document.getElementById('btn-repeat');
                const playlistPanel = document.getElementById('playlist-panel');
                const subtitleOverlay = document.getElementById('subtitle-overlay');
                const fullscreenBtn = document.getElementById('fullscreen-btn');
                const fsLockIcon = document.getElementById('fs-lock-icon');
                const blurPanel = document.getElementById('blur-panel');
                
                // Fullscreen Logic
                function toggleFullScreen() {
                    if (!document.fullscreenElement) {
                        document.documentElement.requestFullscreen().catch(err => {
                            console.log(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
                        });
                        // Lock state UI (managed by event listener mostly, but helper here)
                    } else {
                        if (document.exitFullscreen) {
                            document.exitFullscreen();
                        }
                    }
                }

                // Listen for fullscreen change events (ESC key etc)
                document.addEventListener('fullscreenchange', () => {
                    if (!document.fullscreenElement) {
                        fullscreenBtn.classList.remove('neon-glow');
                        fsLockIcon.classList.remove('fa-lock');
                        fsLockIcon.classList.add('fa-lock-open');
                    } else {
                         fullscreenBtn.classList.add('neon-glow');
                         fsLockIcon.classList.remove('fa-lock-open');
                         fsLockIcon.classList.add('fa-lock');
                    }
                });

                // BLUR LOGIC
                function toggleBlurPanel() {
                    blurPanel.style.display = (blurPanel.style.display === 'block') ? 'none' : 'block';
                }

                function updateBlur(val) {
                    val = parseInt(val);
                    document.getElementById('blur-value-display').innerText = val;
                    
                    const overlay = document.querySelector('.acrylic-overlay');
                    
                    // Default: blur 20px, opacity 0.47 (approx 120/255)
                    let blurPx = 20;
                    let opacity = 0.47;
                    
                    if (val < 0) {
                        // -100 to 0: Scale down to 0
                        const ratio = (100 + val) / 100; // 0 to 1
                        blurPx = 20 * ratio;
                        opacity = 0.47 * ratio;
                    } else {
                        // 0 to 100: Scale up
                        const ratio = val / 100; // 0 to 1
                        // Max blur 60px, max opacity 0.85
                        blurPx = 20 + (40 * ratio);
                        opacity = 0.47 + (0.38 * ratio);
                    }
                    
                    overlay.style.backdropFilter = `blur(${blurPx}px) saturate(125%)`;
                    overlay.style.webkitBackdropFilter = `blur(${blurPx}px) saturate(125%)`;
                    overlay.style.backgroundColor = `rgba(0, 0, 0, ${opacity})`;
                }

                // CLEAN MODE LOGIC
                function enterCleanMode() {
                    document.body.classList.add('clean-mode');
                    // Play audio if paused
                    if(audio.paused) {
                        togglePlay();
                    }
                }

                function exitCleanMode() {
                    document.body.classList.remove('clean-mode');
                }

                // Audio List logic
                let playlist = {{ audio_files|tojson }};
                let currentFile = "{{ audio_file }}";
                let currentSubtitleFile = "{{ subtitle_file if subtitle_file else '' }}";
                let isShuffle = false;
                let isRepeat = false;

                // Subtitle Data
                let subtitles = [];

                // --- SUBTITLE LOGIC ---
                function parseTime(timeStr) {
                    // HH:MM:SS,mmm or HH:MM:SS.mmm
                    timeStr = timeStr.replace(',', '.');
                    const parts = timeStr.split(':');
                    let seconds = 0;
                    if (parts.length === 3) {
                        seconds = parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseFloat(parts[2]);
                    } else if (parts.length === 2) {
                        seconds = parseInt(parts[0]) * 60 + parseFloat(parts[1]);
                    }
                    return seconds;
                }

                function parseSRT(text) {
                    const subs = [];
                    const blocks = text.trim().replace(/\\r\\n/g, '\\n').split(/\\n\\n+/);
                    blocks.forEach(block => {
                        const lines = block.split('\\n');
                        if (lines.length >= 2) {
                            // First line index, second line time
                            let timeLine = lines[1];
                            // If first line is time (sometimes index is missing in loose formats)
                            if(lines[0].includes('-->')) timeLine = lines[0];
                            
                            if (timeLine && timeLine.includes('-->')) {
                                const times = timeLine.split('-->');
                                const start = parseTime(times[0].trim());
                                const end = parseTime(times[1].trim());
                                // Text is the rest
                                let textLines = lines.slice(lines[0].includes('-->') ? 1 : 2);
                                subs.push({ start, end, text: textLines.join('<br>') });
                            }
                        }
                    });
                    return subs;
                }
                
                function parseVTT(text) {
                    const subs = [];
                    const blocks = text.trim().replace(/\\r\\n/g, '\\n').split(/\\n\\n+/);
                    blocks.forEach(block => {
                        const lines = block.split('\\n');
                        // Remove WEBVTT header block
                        if (lines[0].includes('WEBVTT')) return;
                        
                        let timeLineIndex = 0;
                        if (!lines[0].includes('-->')) timeLineIndex = 1; // ID present
                        
                        if (lines[timeLineIndex] && lines[timeLineIndex].includes('-->')) {
                            const times = lines[timeLineIndex].split('-->');
                            const start = parseTime(times[0].trim());
                            const end = parseTime(times[1].trim());
                            let textLines = lines.slice(timeLineIndex + 1);
                            subs.push({ start, end, text: textLines.join('<br>') });
                        }
                    });
                    return subs;
                }

                if (currentSubtitleFile) {
                    fetch('/uploads/' + currentSubtitleFile)
                        .then(r => r.text())
                        .then(text => {
                            if (currentSubtitleFile.endsWith('.vtt')) {
                                subtitles = parseVTT(text);
                            } else {
                                subtitles = parseSRT(text);
                            }
                            console.log('Loaded subtitles:', subtitles.length);
                        })
                        .catch(e => console.error('Error loading subtitles', e));
                }

                // --- VISUALIZER ---
                const canvas = document.getElementById('visualizer');
                const ctx = canvas.getContext('2d');
                let audioCtx, analyser, source;
                let initialized = false;

                function resizeCanvas() {
                    canvas.width = window.innerWidth;
                    canvas.height = 300;
                }
                window.addEventListener('resize', resizeCanvas);
                resizeCanvas();

                function initAudio() {
                    if (!initialized) {
                        initialized = true;
                        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                        analyser = audioCtx.createAnalyser();
                        source = audioCtx.createMediaElementSource(audio);
                        source.connect(analyser);
                        analyser.connect(audioCtx.destination);
                        analyser.fftSize = 2048;
                        drawVisualizer();
                    }
                    if (audioCtx && audioCtx.state === 'suspended') {
                        audioCtx.resume();
                    }
                }

                function drawVisualizer() {
                    requestAnimationFrame(drawVisualizer);
                    const bufferLength = analyser.frequencyBinCount;
                    const dataArray = new Uint8Array(bufferLength);
                    analyser.getByteTimeDomainData(dataArray);
                    
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    ctx.lineWidth = 3;
                    ctx.strokeStyle = 'rgba(220, 220, 220, 0.6)';
                    ctx.shadowBlur = 10;
                    ctx.shadowColor = "white";
                    
                    ctx.beginPath();
                    const sliceWidth = canvas.width * 1.0 / bufferLength;
                    let x = 0;
                    
                    for(let i = 0; i < bufferLength; i++) {
                        const v = dataArray[i] / 128.0;
                        const y = v * canvas.height / 2;
                        if(i === 0) ctx.moveTo(x, y);
                        else ctx.lineTo(x, y);
                        x += sliceWidth;
                    }
                    ctx.lineTo(canvas.width, canvas.height/2);
                    ctx.stroke();
                }

                // --- PLAYER LOGIC ---
                function togglePlay() {
                    initAudio();
                    if (audio.paused) {
                        audio.play();
                        playIcon.classList.remove('fa-play');
                        playIcon.classList.add('fa-pause');
                    } else {
                        audio.pause();
                        playIcon.classList.add('fa-play');
                        playIcon.classList.remove('fa-pause');
                    }
                }

                function stopAudio() {
                    audio.pause();
                    audio.currentTime = 0;
                    playIcon.classList.add('fa-play');
                    playIcon.classList.remove('fa-pause');
                }

                function skip(seconds) {
                    audio.currentTime += seconds;
                }

                function toggleRepeat() {
                    isRepeat = !isRepeat;
                    btnRepeat.classList.toggle('active', isRepeat);
                    audio.loop = isRepeat;
                }

                function toggleShuffle() {
                    isShuffle = !isShuffle;
                    btnShuffle.classList.toggle('active', isShuffle);
                }

                function loadTrack(filename) {
                    currentFile = filename;
                    sourceEl.src = "/uploads/" + filename;
                    audio.load();
                    togglePlay();
                    renderPlaylist(); // Update active state
                }

                // --- PLAYLIST LOGIC ---
                function togglePlaylist() {
                    if(playlistPanel.style.display === 'block') {
                        playlistPanel.style.display = 'none';
                    } else {
                        playlistPanel.style.display = 'block';
                        renderPlaylist();
                    }
                }

                function renderPlaylist() {
                    const container = document.getElementById('playlist-items');
                    container.innerHTML = '';
                    
                    if(playlist.length === 0) {
                        container.innerHTML = '<div style="text-align:center; padding:10px; color:rgba(255,255,255,0.5)">No audio files</div>';
                        return;
                    }

                    playlist.forEach(file => {
                        const div = document.createElement('div');
                        div.className = `playlist-item ${file === currentFile ? 'active' : ''}`;
                        div.innerHTML = `
                            <span onclick="loadTrack('${file}')" style="flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${file}</span>
                            <div class="playlist-actions">
                                <button class="action-btn" onclick="renameTrack('${file}')"><i class="fas fa-pencil-alt"></i></button>
                                <button class="action-btn delete" onclick="deleteTrack('${file}')"><i class="fas fa-trash"></i></button>
                            </div>
                        `;
                        container.appendChild(div);
                    });
                }

                function deleteTrack(filename) {
                    if(confirm('Delete ' + filename + '?')) {
                        window.location.href = `/wallpaper-blur/delete-audio/${filename}`;
                    }
                }

                function renameTrack(filename) {
                    const newName = prompt('Rename ' + filename + ' to:', filename);
                    if(newName && newName !== filename) {
                        document.getElementById('rename-old').value = filename;
                        document.getElementById('rename-new').value = newName;
                        document.getElementById('rename-form').submit();
                    }
                }

                // Auto next track
                audio.addEventListener('ended', () => {
                    if (!isRepeat && playlist.length > 0) {
                        if (isShuffle) {
                            let nextIndex = Math.floor(Math.random() * playlist.length);
                            loadTrack(playlist[nextIndex]);
                        } else {
                            let idx = playlist.indexOf(currentFile);
                            let nextIdx = (idx + 1) % playlist.length;
                            loadTrack(playlist[nextIdx]);
                        }
                    }
                });

                // Update Progress & Time & Subtitles
                audio.addEventListener('timeupdate', () => {
                    const ct = audio.currentTime;
                    
                    // Subtitle Update
                    if (subtitles.length > 0) {
                        const cue = subtitles.find(s => ct >= s.start && ct <= s.end);
                        if (cue) {
                            if (subtitleOverlay.innerHTML !== cue.text) {
                                subtitleOverlay.innerHTML = cue.text;
                            }
                        } else {
                            subtitleOverlay.innerHTML = '';
                        }
                    }

                    if(audio.duration) {
                        const val = (ct / audio.duration) * 100;
                        seekSlider.value = val;
                        
                        let mins = Math.floor(ct / 60);
                        let secs = Math.floor(ct % 60);
                        if(secs < 10) secs = '0' + secs;
                        if(mins < 10) mins = '0' + mins;
                        timeDisplay.textContent = `${mins}:${secs}`;
                    }
                });

                seekSlider.addEventListener('input', () => {
                    if(audio.duration) {
                        const seekTime = (seekSlider.value / 100) * audio.duration;
                        audio.currentTime = seekTime;
                    }
                });

                // Volume & Decibels
                volSlider.addEventListener('input', (e) => {
                    const val = parseFloat(e.target.value);
                    audio.volume = val;
                    
                    // Convert linear 0-1 to approx dB
                    // Typically 0 is -inf, 1 is 0dB. 
                    // Formula: 20 * log10(val)
                    let db = -Infinity;
                    if(val > 0) {
                        db = 20 * Math.log10(val);
                    }
                    
                    // Clamp display
                    if(db < -60) dbDisplay.innerText = "Mute";
                    else dbDisplay.innerText = Math.round(db) + " dB";
                });
            </script>
            {% endif %}
        </div>
        
        <footer style="background: transparent; border: none; color: rgba(255,255,255,0.7);">
            <div class="container">
                <p>&copy; 2025 ourtools - Python 3.13.5 Powered. "We Making The Time"</p>
            </div>
        </footer>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Minimal theme logic for navbar compatibility
        function setTheme(theme) {
            document.documentElement.setAttribute('data-bs-theme', theme);
            localStorage.setItem('theme', theme);
        }
        (function() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-bs-theme', savedTheme);
        })();
    </script>
</body>
</html>
"""

HTML_DOREMI = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nada Dasar C | doremifasolasido</title>
    <link rel="icon" href="{{ url_for('static', filename='hamiartlogo.png') }}">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    {{ styles|safe }}
    <style>
        body, html {
            height: 100%;
            margin: 0;
            overflow: hidden;
        }
        .wallpaper-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url('/uploads/{{ bg_image }}');
            background-size: cover;
            background-position: center;
            z-index: -2;
        }
        .acrylic-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.47);
            backdrop-filter: blur(20px) saturate(125%);
            -webkit-backdrop-filter: blur(20px) saturate(125%);
            z-index: -1;
        }
        .content-wrapper {
            position: relative;
            z-index: 1;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }

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

        .btn-set-wallpaper {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 10px 20px;
            border-radius: 30px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
        }
        .btn-set-wallpaper:hover {
            background: rgba(255, 255, 255, 0.25);
            box-shadow: 0 0 15px rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
            color: white;
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
</head>
<body>
    <div class="wallpaper-bg"></div>
    <div class="acrylic-overlay"></div>

    <div class="content-wrapper">
        {{ navbar|safe }}

        <div style="flex:1; display:flex; flex-direction:column; justify-content:center; align-items:center;">

            <div class="header-controls">
                <h1 class="title-neon">nada dasar C</h1>

                <form action="{{ url_for('wallpaper_upload') }}" method="post" enctype="multipart/form-data" id="form-wall-header">
                    <input type="file" name="background" id="file-wall-header" hidden onchange="document.getElementById('form-wall-header').submit()" accept="image/*">
                    <button type="button" class="btn-set-wallpaper" onclick="document.getElementById('file-wall-header').click()">
                        <i class="fas fa-image"></i> Set Wallpaper
                    </button>
                </form>
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

        <footer style="background: transparent; border: none; color: rgba(255,255,255,0.7); padding: 20px; text-align: center;">
            <div class="container">
                <p>&copy; 2026 hamiart.education - All Rights Reserved. "We Making The Time"</p>
            </div>
        </footer>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        (function() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-bs-theme', savedTheme);
        })();

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
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)
