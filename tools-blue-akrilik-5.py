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
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff', 'ico', 'svg', 'mp3', 'wav', 'ogg', 'mp4', 'm4a', 'flac', 'srt'}

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
    </style>
    <nav class="navbar navbar-expand-lg sticky-top">
        <div class="container">
            <a class="navbar-brand" href="/">Game of <span>Playstation</span></a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link fw-bold" href="/" style="color: white !important;">
                            <span class="lang-id">Daftar Game Playstation</span>
                            <span class="lang-en">List Game Playstation</span>
                        </a>
                    </li>
                </ul>
                <ul class="navbar-nav ms-auto align-items-center">
                    <li class="nav-item me-2">
                        <button type="button" class="btn btn-outline-secondary btn-sm" onclick="toggleLanguage()" id="lang-btn">ID</button>
                    </li>
                </ul>
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
    # Main page is now List Game Playstation
    # We still perform the image scan for the game list logic
    game_images = {}
    for i in range(1, 4):
        found = None
        for ext in ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif', 'tiff', 'svg', 'ico']:
             fname = f"game{i}.{ext}"
             if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], fname)):
                 found = fname
                 break
        game_images[f'game{i}'] = found if found else 'default_game.jpg'

    return render_page(HTML_GAME_LIST, game_images=game_images)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/wallpaper-blur')
def wallpaper_blur():
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

@app.route('/list-game-playstation')
def list_game_playstation():
    # Check for game images
    game_images = {}
    for i in range(1, 4):
        img_name = f"game{i}.jpg"
        found = None
        # Priority search
        for ext in ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif', 'tiff', 'svg', 'ico']:
             fname = f"game{i}.{ext}"
             if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], fname)):
                 found = fname
                 break
        game_images[f'game{i}'] = found if found else 'default_game.jpg'

    return render_page(HTML_GAME_LIST, game_images=game_images)

@app.route('/list-game-playstation/upload/<game_id>', methods=['POST'])
def upload_game_image(game_id):
    # Security check: whitelist allowed game_ids
    if game_id not in ['game1', 'game2', 'game3']:
        return "Invalid Game ID", 400

    if 'game_image' not in request.files:
        return redirect(url_for('list_game_playstation'))

    file = request.files['game_image']
    if file and file.filename != '' and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        # Remove old images for this game_id
        for e in ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif', 'tiff', 'svg', 'ico']:
            old_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{game_id}.{e}")
            if os.path.exists(old_path):
                os.remove(old_path)

        new_filename = f"{game_id}.{ext}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))

    return redirect(url_for('list_game_playstation'))

@app.route('/wallpaper-blur/delete-audio/<filename>')
def delete_audio(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    if os.path.exists(filepath):
        os.remove(filepath)
    return redirect(url_for('index'))

@app.route('/wallpaper-blur/rename-audio', methods=['POST'])
def rename_audio():
    old_name = request.form.get('old_name')
    new_name = request.form.get('new_name')

    if old_name and new_name:
        safe_old = secure_filename(old_name)
        safe_new = secure_filename(new_name)

        # Keep extension
        if '.' in safe_old:
            ext = safe_old.rsplit('.', 1)[1]
            if not safe_new.endswith(f'.{ext}'):
                safe_new += f'.{ext}'

        old_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_old)
        new_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_new)

        if os.path.exists(old_path) and not os.path.exists(new_path):
            os.rename(old_path, new_path)
            # Update config if active
            if os.path.exists('audio_config.txt'):
                with open('audio_config.txt', 'r') as f:
                    curr = f.read().strip()
                if curr == safe_old:
                    with open('audio_config.txt', 'w') as f:
                        f.write(safe_new)

    return redirect(url_for('index'))

@app.route('/wallpaper-blur/upload-audio', methods=['POST'])
def audio_upload():
    if 'audio' not in request.files:
        return redirect(url_for('index'))

    file = request.files['audio']
    if file and file.filename != '' and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        with open('audio_config.txt', 'w') as f:
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
    </style>
</head>
<body>
    <div class="wallpaper-bg"></div>
    <div class="acrylic-overlay"></div>

    <div class="content-wrapper">
        {{ navbar|safe }}
        
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
            </div>

            {% if audio_file %}
            <!-- Visualizer Overlay -->
            <canvas id="visualizer"></canvas>

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

                // Audio List logic
                let playlist = {{ audio_files|tojson }};
                let currentFile = "{{ audio_file }}";
                let isShuffle = false;
                let isRepeat = false;

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

                // Update Progress & Time
                audio.addEventListener('timeupdate', () => {
                    if(audio.duration) {
                        const val = (audio.currentTime / audio.duration) * 100;
                        seekSlider.value = val;

                        let mins = Math.floor(audio.currentTime / 60);
                        let secs = Math.floor(audio.currentTime % 60);
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

HTML_GAME_LIST = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Game of Playstation</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    {{ styles|safe }}
    <style>
        body {
            background-color: #0f0f0f;
            background-image: url('https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=2070&auto=format&fit=crop');
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
        }
        .acrylic-overlay-page {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(20px);
            z-index: -1;
        }
        .game-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            overflow: hidden;
            transition: transform 0.3s, box-shadow 0.3s;
            color: white;
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        .game-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.4);
            border-color: rgba(229, 50, 45, 0.5);
        }
        .game-poster-container {
            position: relative;
            width: 100%;
            padding-top: 140%;
            background: rgba(0,0,0,0.3);
            cursor: pointer;
            overflow: hidden;
        }
        .game-poster {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            object-fit: cover;
            transition: transform 0.5s;
        }
        .game-poster-container:hover .game-poster {
            transform: scale(1.05);
        }
        .upload-overlay {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.6);
            display: flex;
            justify-content: center;
            align-items: center;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .game-poster-container:hover .upload-overlay {
            opacity: 1;
        }
        .game-info {
            padding: 25px;
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        .game-title {
            font-weight: 800;
            font-size: 1.8rem;
            margin-bottom: 15px;
            color: #fff;
            text-shadow: 0 2px 10px rgba(0,0,0,0.5);
        }

        /* Expandable Description */
        .game-desc {
            position: relative;
            margin-bottom: 15px;
        }
        .game-desc-content {
            font-size: 0.95rem;
            line-height: 1.6;
            color: rgba(255, 255, 255, 0.8);
            font-weight: 300;
            max-height: 100px; /* Adjust based on ~1 paragraph */
            overflow: hidden;
            transition: max-height 0.5s ease;
        }
        .game-desc-content.expanded {
            max-height: 1000px; /* Large enough to fit full text */
        }
        .read-more-overlay {
            position: absolute;
            bottom: 0;
            /* Expand to edge of card (overcoming 25px padding of .game-info) */
            left: -25px;
            width: calc(100% + 50px);
            height: 80px;
            background: linear-gradient(transparent, rgba(0,0,0,0.6));
            /* Soft smooth acrylic blur */
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            display: flex;
            justify-content: center;
            align-items: center; /* Center text vertically in the overlay */
            cursor: pointer;
            transition: opacity 0.3s;
        }
        .game-desc-content.expanded + .read-more-overlay {
            display: none;
            /* Alternatively: opacity: 0; pointer-events: none; */
        }
        .read-more-btn {
            color: var(--brand-color);
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .game-price-tag {
            margin-top: auto;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
            font-size: 1.5rem;
            font-weight: 700;
            color: #4cd137;
            text-align: right;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .price-label {
            font-size: 0.9rem;
            color: rgba(255,255,255,0.5);
            font-weight: 400;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Language Toggle Classes */
        .lang-id, .lang-en { display: none; }

        body.lang-mode-id div.lang-id { display: block; }
        body.lang-mode-id span.lang-id { display: inline; }

        body.lang-mode-en div.lang-en { display: block; }
        body.lang-mode-en span.lang-en { display: inline; }

        /* Footer Styling */
        footer.acrylic-footer {
            margin-top: 80px;
            color: rgba(255,255,255,0.7);
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;

            /* Vertical and Horizontal Centering */
            display: flex;
            justify-content: center;
            align-items: center;
            height: 80px; /* Fixed height to ensure vertical centering space */
        }
        footer.acrylic-footer p {
            margin: 0; /* Remove default paragraph margin */
            padding: 0;
        }
    </style>
</head>
<body class="lang-mode-id"> <!-- Default to ID -->
    <div class="acrylic-overlay-page"></div>

    {{ navbar|safe }}

    <div class="container container-xl py-5">
        <div class="row g-5">
            <!-- Game 1: Horizon Zero Dawn -->
            <div class="col-lg-4">
                <div class="game-card">
                    <form action="/list-game-playstation/upload/game1" method="post" enctype="multipart/form-data" id="form-game1">
                        <input type="file" name="game_image" id="file-game1" hidden onchange="document.getElementById('form-game1').submit()" accept="image/*">
                        <div class="game-poster-container" onclick="document.getElementById('file-game1').click()">
                            {% if game_images.game1 != 'default_game.jpg' %}
                                <img src="/uploads/{{ game_images.game1 }}" class="game-poster" alt="Horizon Zero Dawn">
                            {% else %}
                                <div class="game-poster" style="background: #2d3436; display:flex; align-items:center; justify-content:center; color:rgba(255,255,255,0.2); font-size:3rem;"><i class="fas fa-gamepad"></i></div>
                            {% endif %}
                            <div class="upload-overlay">
                                <span class="text-white">
                                    <i class="fas fa-camera me-2"></i>
                                    <span class="lang-id">Ganti Sampul</span>
                                    <span class="lang-en">Change Cover</span>
                                </span>
                            </div>
                        </div>
                    </form>
                    <div class="game-info">
                        <h2 class="game-title">Horizon Zero Dawn</h2>
                        <div class="game-desc">
                            <div class="game-desc-content" id="desc-game1">
                                <div class="lang-en">
                                    <p>In a post-apocalyptic era where nature has reclaimed the ruins of a forgotten civilization, humanity is no longer the dominant species. Colossal machines, evolving with terrifying biological mimicry, roam the landscapes. This is not merely a survival story, but a profound scientific inquiry into the consequences of unchecked technological advancement and the resilience of life itself.</p>
                                    <p>You inhabit the soul of Aloy, an outcast shunned by her tribe, carrying the heavy burden of an unknown lineage. Her journey is a deeply emotional odyssey of self-discovery, driven by a primal need for acceptance and truth. Every step through the lush, vibrant wilderness is a testament to the human spirit's refusal to fade into oblivion, even when faced with mechanical gods.</p>
                                    <p>The narrative weaves a complex tapestry of ancient mysteries and futuristic despair. As you unravel the secrets of "Zero Dawn," you are confronted with the heartbreaking choices of those who came before. It is a poignant reminder of our fragility and the enduring legacy of hope that persists, even after the end of the world.</p>
                                </div>
                                <div class="lang-id">
                                    <p>Di era pasca-apokaliptik di mana alam telah merebut kembali reruntuhan peradaban yang terlupakan, umat manusia tidak lagi menjadi spesies dominan. Mesin-mesin raksasa, yang berevolusi dengan mimikri biologis yang menakutkan, berkeliaran di lanskap. Ini bukan sekadar kisah bertahan hidup, melainkan penyelidikan ilmiah mendalam tentang konsekuensi kemajuan teknologi yang tidak terkendali dan ketahanan kehidupan itu sendiri.</p>
                                    <p>Anda menghuni jiwa Aloy, seorang buangan yang dijauhi oleh sukunya, memikul beban berat garis keturunan yang tidak diketahui. Perjalanannya adalah pengembaraan emosional yang mendalam tentang penemuan jati diri, didorong oleh kebutuhan mendasar akan penerimaan dan kebenaran. Setiap langkah melalui hutan belantara yang subur dan hidup adalah bukti penolakan jiwa manusia untuk memudar dalam ketiadaan, bahkan saat berhadapan dengan dewa-dewa mekanis.</p>
                                    <p>Narasi ini menjalin permadani kompleks dari misteri kuno dan keputusasaan futuristik. Saat Anda mengungkap rahasia "Zero Dawn," Anda dihadapkan pada pilihan memilukan dari mereka yang datang sebelumnya. Ini adalah pengingat pedih akan kerapuhan kita dan warisan harapan abadi yang bertahan, bahkan setelah akhir dunia.</p>
                                </div>
                            </div>
                            <div class="read-more-overlay" onclick="toggleReadMore('desc-game1')">
                                <span class="read-more-btn"><span class="lang-id">Selengkapnya</span><span class="lang-en">Read More</span> <i class="fas fa-chevron-down"></i></span>
                            </div>
                        </div>
                        <div class="game-price-tag">
                            <span class="price-label">
                                <span class="lang-id">Harga (2026)</span>
                                <span class="lang-en">Price (2026)</span>
                            </span>
                            Rp 729.000
                        </div>
                    </div>
                </div>
            </div>

            <!-- Game 2: The Last Of Us Part I -->
            <div class="col-lg-4">
                <div class="game-card">
                    <form action="/list-game-playstation/upload/game2" method="post" enctype="multipart/form-data" id="form-game2">
                        <input type="file" name="game_image" id="file-game2" hidden onchange="document.getElementById('form-game2').submit()" accept="image/*">
                        <div class="game-poster-container" onclick="document.getElementById('file-game2').click()">
                            {% if game_images.game2 != 'default_game.jpg' %}
                                <img src="/uploads/{{ game_images.game2 }}" class="game-poster" alt="The Last Of Us Part I">
                            {% else %}
                                <div class="game-poster" style="background: #2d3436; display:flex; align-items:center; justify-content:center; color:rgba(255,255,255,0.2); font-size:3rem;"><i class="fas fa-gamepad"></i></div>
                            {% endif %}
                            <div class="upload-overlay">
                                <span class="text-white">
                                    <i class="fas fa-camera me-2"></i>
                                    <span class="lang-id">Ganti Sampul</span>
                                    <span class="lang-en">Change Cover</span>
                                </span>
                            </div>
                        </div>
                    </form>
                    <div class="game-info">
                        <h2 class="game-title">The Last Of Us Part I</h2>
                        <div class="game-desc">
                            <div class="game-desc-content" id="desc-game2">
                                <div class="lang-en">
                                    <p>Rooted in terrifying biological plausibility, the Cordyceps brain infection has decimated civilization, stripping humanity of its infrastructure and its morality. The world is a brutal, overgrown husk where survival is a daily negotiation with death. This scientific horror serves as the backdrop for a raw, unfiltered examination of the human condition under extreme duress.</p>
                                    <p>At its core, this is a heart-wrenching study of the bond between Joel, a hardened survivor haunted by loss, and Ellie, a girl who represents a glimmer of impossible hope. Their journey across a fractured America is an emotional tour de force, exploring the fierce, sometimes destructive nature of paternal love and the trauma of growing up in a world without innocence.</p>
                                    <p>The narrative challenges the binary of right and wrong, forcing players to confront the gray areas of morality. Every choice carries weight; every violent act leaves a scar on the soul. It is a masterpiece of storytelling that asks a haunting question: how far would you go to save the one thing that gives your life meaning in a godless world?</p>
                                </div>
                                <div class="lang-id">
                                    <p>Berakar pada kemungkinan biologis yang menakutkan, infeksi otak Cordyceps telah memusnahkan peradaban, melucuti infrastruktur dan moralitas umat manusia. Dunia adalah sekam brutal yang ditumbuhi tanaman liar di mana bertahan hidup adalah negosiasi harian dengan kematian. Horor ilmiah ini menjadi latar belakang bagi pemeriksaan mentah dan tanpa filter terhadap kondisi manusia di bawah tekanan ekstrem.</p>
                                    <p>Pada intinya, ini adalah studi yang menyayat hati tentang ikatan antara Joel, seorang penyintas keras yang dihantui oleh kehilangan, dan Ellie, seorang gadis yang mewakili secercah harapan yang mustahil. Perjalanan mereka melintasi Amerika yang retak adalah tour de force emosional, mengeksplorasi sifat cinta kebapakan yang ganas dan terkadang merusak serta trauma tumbuh di dunia tanpa kepolosan.</p>
                                    <p>Narasi ini menantang biner benar dan salah, memaksa pemain untuk menghadapi area abu-abu moralitas. Setiap pilihan memiliki bobot; setiap tindakan kekerasan meninggalkan bekas luka pada jiwa. Ini adalah mahakarya penceritaan yang mengajukan pertanyaan menghantui: seberapa jauh Anda akan pergi untuk menyelamatkan satu hal yang memberi hidup Anda makna di dunia tanpa tuhan?</p>
                                </div>
                            </div>
                            <div class="read-more-overlay" onclick="toggleReadMore('desc-game2')">
                                <span class="read-more-btn"><span class="lang-id">Selengkapnya</span><span class="lang-en">Read More</span> <i class="fas fa-chevron-down"></i></span>
                            </div>
                        </div>
                        <div class="game-price-tag">
                            <span class="price-label">
                                <span class="lang-id">Harga (2026)</span>
                                <span class="lang-en">Price (2026)</span>
                            </span>
                            Rp 1.029.000
                        </div>
                    </div>
                </div>
            </div>

            <!-- Game 3: Resident Evil 2 Remake -->
            <div class="col-lg-4">
                <div class="game-card">
                    <form action="/list-game-playstation/upload/game3" method="post" enctype="multipart/form-data" id="form-game3">
                        <input type="file" name="game_image" id="file-game3" hidden onchange="document.getElementById('form-game3').submit()" accept="image/*">
                        <div class="game-poster-container" onclick="document.getElementById('file-game3').click()">
                            {% if game_images.game3 != 'default_game.jpg' %}
                                <img src="/uploads/{{ game_images.game3 }}" class="game-poster" alt="Resident Evil 2 Remake">
                            {% else %}
                                <div class="game-poster" style="background: #2d3436; display:flex; align-items:center; justify-content:center; color:rgba(255,255,255,0.2); font-size:3rem;"><i class="fas fa-gamepad"></i></div>
                            {% endif %}
                            <div class="upload-overlay">
                                <span class="text-white">
                                    <i class="fas fa-camera me-2"></i>
                                    <span class="lang-id">Ganti Sampul</span>
                                    <span class="lang-en">Change Cover</span>
                                </span>
                            </div>
                        </div>
                    </form>
                    <div class="game-info">
                        <h2 class="game-title">Resident Evil 2 Remake</h2>
                        <div class="game-desc">
                            <div class="game-desc-content" id="desc-game3">
                                <div class="lang-en">
                                    <p>A catastrophic viral outbreak has transformed the bustling metropolis of Raccoon City into a nightmare of biological distortion. The G-Virus represents the pinnacle of corporate scientific hubris, a terrifying force that warps flesh and mind. The atmosphere is thick with the scent of decay and the oppressive dread of an unseen, mutating predator stalking the halls.</p>
                                    <p>Leon S. Kennedy and Claire Redfield are thrust into this chaos, their survival instincts pushed to the breaking point. The game masterfully manipulates fear and tension, creating an emotional rollercoaster where every shadow holds a threat. It captures the raw, visceral panic of being hunted, forcing players to manage scarce resources while their heart races in sync with the characters.</p>
                                    <p>Beneath the gore lies a tragic narrative of the Birkin family, destroyed by their own creation. It serves as a cautionary tale about the ethics of genetic manipulation and the cost of ambition. The reimagined experience elevates the horror to a poignant level, making the struggle for survival feel intimate, desperate, and utterly compelling.</p>
                                </div>
                                <div class="lang-id">
                                    <p>Wabah virus yang membawa bencana telah mengubah kota metropolis Raccoon City yang ramai menjadi mimpi buruk distorsi biologis. G-Virus mewakili puncak keangkuhan ilmiah korporat, kekuatan mengerikan yang membelokkan daging dan pikiran. Atmosfernya kental dengan aroma pembusukan dan ketakutan menindas akan predator tak terlihat yang bermutasi mengintai di lorong-lorong.</p>
                                    <p>Leon S. Kennedy dan Claire Redfield terdorong ke dalam kekacauan ini, naluri bertahan hidup mereka didorong hingga titik puncaknya. Game ini dengan ahli memanipulasi ketakutan dan ketegangan, menciptakan rollercoaster emosional di mana setiap bayangan menyimpan ancaman. Ini menangkap kepanikan mentah dan mendalam saat diburu, memaksa pemain untuk mengelola sumber daya yang langka sementara jantung mereka berpacu selaras dengan karakter.</p>
                                    <p>Di balik pertumpahan darah terdapat narasi tragis keluarga Birkin, yang dihancurkan oleh ciptaan mereka sendiri. Ini berfungsi sebagai kisah peringatan tentang etika manipulasi genetik dan harga dari ambisi. Pengalaman yang dirancang ulang ini mengangkat horor ke tingkat yang pedih, membuat perjuangan untuk bertahan hidup terasa intim, putus asa, dan sangat memikat.</p>
                                </div>
                            </div>
                            <div class="read-more-overlay" onclick="toggleReadMore('desc-game3')">
                                <span class="read-more-btn"><span class="lang-id">Selengkapnya</span><span class="lang-en">Read More</span> <i class="fas fa-chevron-down"></i></span>
                            </div>
                        </div>
                        <div class="game-price-tag">
                            <span class="price-label">
                                <span class="lang-id">Harga (2026)</span>
                                <span class="lang-en">Price (2026)</span>
                            </span>
                            Rp 559.000
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <footer class="acrylic-footer">
            <p>&copy; 2025 Game of Playstation - Powered by <i>emansipation</i>. "Life it's Game itself"</p>
        </footer>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function setTheme(theme) {
            document.documentElement.setAttribute('data-bs-theme', theme);
            localStorage.setItem('theme', theme);
        }
        (function() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-bs-theme', savedTheme);
        })();

        // Language Toggle
        function toggleLanguage() {
            const body = document.body;
            const btn = document.getElementById('lang-btn');

            if (body.classList.contains('lang-mode-id')) {
                body.classList.remove('lang-mode-id');
                body.classList.add('lang-mode-en');
                btn.textContent = 'EN';
            } else {
                body.classList.remove('lang-mode-en');
                body.classList.add('lang-mode-id');
                btn.textContent = 'ID';
            }
        }

        // Read More Toggle
        function toggleReadMore(id) {
            const content = document.getElementById(id);
            content.classList.toggle('expanded');
            // Hide overlay is handled by CSS
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)
