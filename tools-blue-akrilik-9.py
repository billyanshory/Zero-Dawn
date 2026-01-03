import io
import os
import zipfile
import math
import sqlite3
import speech_recognition as sr
from flask import Flask, request, send_file, render_template_string, jsonify, send_from_directory, redirect, url_for, session, flash
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter, Transformation, PageObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from werkzeug.utils import secure_filename
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

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
            <a class="navbar-brand" href="/">our<span>tools</span></a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item"><a class="nav-link fw-bold" href="/wallpaper-blur">Wallpaper Blur Akrilik</a></li>
                </ul>
                <ul class="navbar-nav ms-auto align-items-center">
                    <li class="nav-item me-3">
                        <div class="btn-group" role="group">
                            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="setTheme('light')"><i class="fas fa-sun"></i></button>
                            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="setTheme('dark')"><i class="fas fa-moon"></i></button>
                        </div>
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
    # Make wallpaper page the main page
    bg_image = "default.jpg" # Fallback
    if os.path.exists('bg_config.txt'):
        with open('bg_config.txt', 'r') as f:
            content = f.read().strip()
            if content:
                bg_image = content

    audio_file = None
    if os.path.exists('audio_config.txt'):
        with open('audio_config.txt', 'r') as f:
            content = f.read().strip()
            if content:
                audio_file = content

    audio_files = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        audio_exts = {'mp3', 'wav', 'ogg', 'mp4', 'm4a', 'flac'}
        audio_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) 
                       if allowed_file(f) and f.rsplit('.', 1)[1].lower() in audio_exts]

    return render_page(HTML_WALLPAPER, bg_image=bg_image, audio_file=audio_file, audio_files=audio_files)

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

@app.route('/generate-subtitle', methods=['POST'])
def generate_subtitle():
    data = request.get_json()
    filename = data.get('filename')

    if not filename:
        return jsonify({'error': 'No filename provided'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    try:
        # Load audio using pydub
        sound = AudioSegment.from_file(filepath)

        # Detect nonsilent chunks to determine timing
        # Adjust min_silence_len and silence_thresh as needed
        # Using dBFS - 16 as a relative threshold
        nonsilent_ranges = detect_nonsilent(sound, min_silence_len=500, silence_thresh=sound.dBFS-16)

        recognizer = sr.Recognizer()
        subtitles = []

        for start_ms, end_ms in nonsilent_ranges:
            # Extract the chunk
            chunk = sound[start_ms:end_ms]

            # Export to memory buffer as WAV for SpeechRecognition
            buf = io.BytesIO()
            chunk.export(buf, format="wav")
            buf.seek(0)

            with sr.AudioFile(buf) as source:
                # Record the audio from the file
                audio_data = recognizer.record(source)
                try:
                    # Recognize speech using Google Web Speech API (Indonesian)
                    text = recognizer.recognize_google(audio_data, language="id-ID")
                    subtitles.append({
                        "start": start_ms / 1000.0,
                        "end": end_ms / 1000.0,
                        "text": text
                    })
                except sr.UnknownValueError:
                    # Speech was unintelligible
                    pass
                except sr.RequestError as e:
                    # API was unreachable or failed
                    pass

        return jsonify({'subtitles': subtitles})

    except FileNotFoundError:
        return jsonify({'error': 'FFmpeg not found or file format not supported without FFmpeg. Please ensure FFmpeg is installed.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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

        /* Subtitle Overlay */
        #subtitle-overlay {
            position: absolute;
            top: 40%; /* Positioned slightly above the vertical center */
            left: 50%;
            transform: translate(-50%, -50%);
            color: white !important;
            font-size: 1.5rem; /* Medium pleasant font */
            font-weight: 600;
            text-align: center;
            text-shadow: 0 2px 4px rgba(0,0,0,0.8);
            z-index: 50; /* Above visualizer */
            width: 80%;
            pointer-events: none;
            transition: opacity 0.2s;
            min-height: 2em;
        }
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

                <!-- Audio To Subtitle Button -->
                <button type="button" class="acrylic-btn" id="btn-subtitle" onclick="generateSubtitle()">
                    <i class="fas fa-closed-captioning me-2"></i> Audio to Subtitle
                </button>
            </div>
            
            {% if audio_file %}
            <!-- Subtitle Overlay -->
            <div id="subtitle-overlay"></div>

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
                let currentSubtitles = [];

                // --- SUBTITLE LOGIC ---
                async function generateSubtitle() {
                    if(!currentFile) return alert("No audio selected");

                    const btn = document.getElementById('btn-subtitle');
                    const originalText = btn.innerHTML;
                    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Processing...';
                    btn.disabled = true;

                    try {
                        const response = await fetch('/generate-subtitle', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({filename: currentFile})
                        });
                        const data = await response.json();

                        if(response.ok && data.subtitles) {
                            currentSubtitles = data.subtitles;
                            alert("Subtitles generated successfully!");
                        } else {
                            alert("Failed: " + (data.error || "Unknown error"));
                        }
                    } catch(e) {
                        alert("Error: " + e);
                    } finally {
                        btn.innerHTML = originalText;
                        btn.disabled = false;
                    }
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
                    currentSubtitles = []; // Clear subtitles for new track
                    document.getElementById('subtitle-overlay').innerText = "";
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
                    if(audio.duration) {
                        const val = (audio.currentTime / audio.duration) * 100;
                        seekSlider.value = val;
                        
                        let mins = Math.floor(audio.currentTime / 60);
                        let secs = Math.floor(audio.currentTime % 60);
                        if(secs < 10) secs = '0' + secs;
                        if(mins < 10) mins = '0' + mins;
                        timeDisplay.textContent = `${mins}:${secs}`;

                        // Subtitle sync
                        const t = audio.currentTime;
                        const sub = currentSubtitles.find(s => t >= s.start && t <= s.end);
                        const overlay = document.getElementById('subtitle-overlay');
                        if(sub) {
                            if(overlay.innerText !== sub.text) {
                                overlay.innerText = sub.text;
                                overlay.style.opacity = 1;
                            }
                        } else {
                            overlay.innerText = "";
                            // overlay.style.opacity = 0; // Optional: fade out
                        }
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
