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

    audio_file = ""
    if os.path.exists('audio_config.txt'):
         with open('audio_config.txt', 'r') as f:
            content = f.read().strip()
            if content:
                audio_file = content

    sub_file = ""
    if os.path.exists('sub_config.txt'):
         with open('sub_config.txt', 'r') as f:
            content = f.read().strip()
            if content:
                sub_file = content

    return render_page(HTML_WALLPAPER, bg_image=bg_image, audio_file=audio_file, sub_file=sub_file)

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

@app.route('/upload/audio', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return redirect(url_for('index'))

    file = request.files['audio']
    if file and file.filename != '' and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        with open('audio_config.txt', 'w') as f:
            f.write(filename)

    return redirect(url_for('index'))

@app.route('/upload/subtitle', methods=['POST'])
def upload_subtitle():
    if 'subtitle' not in request.files:
        return redirect(url_for('index'))

    file = request.files['subtitle']
    if file and file.filename != '' and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        with open('sub_config.txt', 'w') as f:
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
        .controls-container {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            justify-content: center;
            margin-bottom: 30px;
            transition: all 0.8s ease-in-out;
        }

        /* Active State: Move controls to left */
        body.content-active .controls-container {
            position: fixed;
            left: 30px;
            top: 50%;
            transform: translateY(-50%);
            flex-direction: column;
            align-items: flex-start;
            margin: 0;
            z-index: 100;
        }

        body.content-active .center-content {
            margin-left: 0; /* Centered relative to viewport, visualizer takes center */
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

        /* Subtitle Area */
        #subtitle-display {
            font-size: 2.5rem;
            font-weight: 700;
            text-shadow: 0 2px 10px rgba(0,0,0,0.8);
            margin: 20px 0;
            min-height: 4rem;
            opacity: 0;
            transition: opacity 0.5s ease-in-out;
            max-width: 80%;
            pointer-events: none;
            text-align: center;
        }
        .subtitle-active {
            opacity: 1 !important;
        }

        /* Audio Player UI */
        .audio-player-ui {
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(15px);
            padding: 15px 30px;
            border-radius: 50px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
            gap: 20px;
            margin-top: 20px;
            z-index: 10;
        }

        /* Visualizer */
        #visualizer {
            width: 600px;
            height: 150px;
            margin-top: 30px;
            filter: drop-shadow(0 0 10px rgba(0, 255, 0, 0.5));
        }
        .player-btn {
            background: transparent;
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: 0.2s;
        }
        .player-btn:hover {
            background: rgba(255,255,255,0.2);
        }
    </style>
</head>
<body>
    <div class="wallpaper-bg"></div>
    <div class="acrylic-overlay"></div>

    <div class="content-wrapper">
        {{ navbar|safe }}

        <div class="center-content">
            <!-- Subtitle Display -->
            <div id="subtitle-display"></div>

            <!-- Audio Player UI -->
            <div class="audio-player-ui" id="playerUI" style="display:none;">
                <button class="player-btn" onclick="seek(-5)"><i class="fas fa-backward"></i></button>
                <button class="player-btn" onclick="togglePlay()" id="playBtn"><i class="fas fa-play"></i></button>
                <button class="player-btn" onclick="seek(5)"><i class="fas fa-forward"></i></button>
            </div>

            <audio id="audioPlayer" src="/uploads/{{ audio_file }}" crossorigin="anonymous"></audio>

            <!-- Heartbeat Visualizer -->
            <canvas id="visualizer" style="display:none;"></canvas>

            <div style="height: 50px;"></div>

            <div class="controls-container">
                <!-- Wallpaper Upload -->
                <form action="/wallpaper-blur/upload" method="post" enctype="multipart/form-data" id="form-wall">
                    <input type="file" name="background" id="file-wall" hidden onchange="document.getElementById('form-wall').submit()" accept="image/*">
                    <button type="button" class="acrylic-btn" onclick="document.getElementById('file-wall').click()">
                        <i class="fas fa-image me-2"></i> Set Wallpaper
                    </button>
                </form>

                <!-- Audio Upload -->
                <form action="/upload/audio" method="post" enctype="multipart/form-data" id="form-audio">
                    <input type="file" name="audio" id="file-audio" hidden onchange="document.getElementById('form-audio').submit()" accept=".mp3,.wav,.ogg,.mp4,.m4a,.flac">
                    <button type="button" class="acrylic-btn" onclick="document.getElementById('file-audio').click()">
                        <i class="fas fa-music me-2"></i> Set Audio
                    </button>
                </form>

                <!-- Subtitle Upload -->
                <form action="/upload/subtitle" method="post" enctype="multipart/form-data" id="form-sub">
                    <input type="file" name="subtitle" id="file-sub" hidden onchange="document.getElementById('form-sub').submit()" accept=".srt">
                    <button type="button" class="acrylic-btn" onclick="document.getElementById('file-sub').click()">
                        <i class="fas fa-closed-captioning me-2"></i> Set Subtitle
                    </button>
                </form>
            </div>
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

        // --- AUDIO & SUBTITLE LOGIC ---
        const audio = document.getElementById('audioPlayer');
        const playBtn = document.getElementById('playBtn');
        const playerUI = document.getElementById('playerUI');
        const subDisplay = document.getElementById('subtitle-display');

        let subtitles = [];

        // --- VISUALIZER ---
        const canvas = document.getElementById('visualizer');
        const canvasCtx = canvas.getContext('2d');
        let audioCtx, analyser, source;
        let isVisualizerInit = false;

        function initAudio() {
            if (isVisualizerInit) return;
            isVisualizerInit = true;

            try {
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                analyser = audioCtx.createAnalyser();
                source = audioCtx.createMediaElementSource(audio);
                source.connect(analyser);
                analyser.connect(audioCtx.destination);

                analyser.fftSize = 256;
                drawVisualizer();
            } catch(e) {
                console.log("Audio Context Error", e);
            }
        }

        function drawVisualizer() {
            if (!audioCtx) return;

            requestAnimationFrame(drawVisualizer);

            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            analyser.getByteFrequencyData(dataArray); // Use frequency for volume

            // Calc avg volume
            let sum = 0;
            for(let i = 0; i < bufferLength; i++) {
                sum += dataArray[i];
            }
            let average = sum / bufferLength;

            // Draw
            canvas.width = canvas.clientWidth;
            canvas.height = canvas.clientHeight;
            const w = canvas.width;
            const h = canvas.height;
            const cy = h / 2;

            canvasCtx.clearRect(0, 0, w, h);

            // Line Style (Heartbeat Green/White mix)
            canvasCtx.lineWidth = 3;
            canvasCtx.strokeStyle = 'rgba(100, 255, 100, 0.8)';
            canvasCtx.shadowBlur = 10;
            canvasCtx.shadowColor = 'rgba(0, 255, 0, 0.8)';

            canvasCtx.beginPath();

            // Simulate ECG pulse
            // We move a "point" across the screen based on time, but simplified:
            // Just draw a line that gets noisy in the middle based on volume

            canvasCtx.moveTo(0, cy);

            // A simple way: draw a flat line that vibrates based on volume
            // Let's make it look like the user image: Line... pulse... line...

            // To make it look cool, we can just map the waveform buffer
            // But let's use the requested "volume" to drive a pulse amplitude

            let scale = average / 50; // Sensitivity

            // Draw a waveform based on time domain?
            // Let's use time domain for the line look
            const timeData = new Uint8Array(bufferLength);
            analyser.getByteTimeDomainData(timeData);

            canvasCtx.beginPath();
            let sliceWidth = w * 1.0 / bufferLength;
            let x = 0;

            for(let i = 0; i < bufferLength; i++) {
                let v = timeData[i] / 128.0;
                let y = v * h/2;

                if(i === 0) canvasCtx.moveTo(x, y);
                else canvasCtx.lineTo(x, y);

                x += sliceWidth;
            }

            canvasCtx.lineTo(canvas.width, canvas.height/2);
            canvasCtx.stroke();
        }

        // --- STATE MANAGEMENT ---
        const hasAudio = audio.getAttribute('src') && audio.getAttribute('src') !== '/uploads/';
        const hasSub = "{{ sub_file }}" !== "";

        if (hasAudio || hasSub) {
            document.body.classList.add('content-active');
            if (hasAudio) {
                playerUI.style.display = 'flex';
                document.getElementById('visualizer').style.display = 'block';
            }
            loadSubtitles();
        }

        function togglePlay() {
            if (!isVisualizerInit) initAudio();
            if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();

            if (audio.paused) {
                audio.play();
                playBtn.innerHTML = '<i class="fas fa-pause"></i>';
            } else {
                audio.pause();
                playBtn.innerHTML = '<i class="fas fa-play"></i>';
            }
        }

        function seek(seconds) {
            audio.currentTime += seconds;
        }

        // Parse SRT
        function parseSRT(text) {
            // Regex double-escaped for Python string
            const pattern = /(\\d+)\\n(\\d{2}:\\d{2}:\\d{2},\\d{3}) --> (\\d{2}:\\d{2}:\\d{2},\\d{3})\\n([\\s\\S]*?)(?=\\n\\n|\\n*$)/g;
            const result = [];
            let match;
            while ((match = pattern.exec(text)) !== null) {
                result.push({
                    start: timeToSeconds(match[2]),
                    end: timeToSeconds(match[3]),
                    text: match[4].trim()
                });
            }
            return result;
        }

        function timeToSeconds(t) {
            const [h, m, s] = t.split(':');
            const [sec, ms] = s.split(',');
            return parseInt(h) * 3600 + parseInt(m) * 60 + parseInt(sec) + parseInt(ms) / 1000;
        }

        async function loadSubtitles() {
            const subFile = "{{ sub_file }}";
            if (!subFile) return;

            try {
                const response = await fetch('/uploads/' + subFile);
                if (response.ok) {
                    const text = await response.text();
                    subtitles = parseSRT(text.replace(/\r\n/g, '\n'));
                }
            } catch (e) {
                console.error("Failed to load subs", e);
            }
        }

        // Sync Logic
        audio.addEventListener('timeupdate', () => {
            const t = audio.currentTime;
            const active = subtitles.find(s => t >= s.start && t <= s.end);

            if (active) {
                if (subDisplay.innerText !== active.text) {
                    subDisplay.innerText = active.text;
                    subDisplay.classList.add('subtitle-active');
                }
            } else {
                subDisplay.classList.remove('subtitle-active');
                // Allow fade out before clearing text?
                // For smoother exp, we clear text after transition, but here we keep it simple.
            }
        });
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)
