import os
from flask import Flask, request, send_from_directory, render_template_string, redirect, url_for, Response
from werkzeug.utils import secure_filename

# --- PWA CONFIGURATION (SINGLE FILE PATTERN) ---
MANIFEST_CONTENT = """{
  "name": "Hamiart Education",
  "short_name": "Hamiart",
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
}"""

SW_CONTENT = """
const CACHE_NAME = 'hamiart-v1';
const urlsToCache = [
  '/',
  '/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});
"""

# --- KONFIGURASI FLASK ---
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB Limit
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff', 'ico', 'svg', 'mp3', 'wav', 'ogg', 'mp4', 'm4a', 'flac', 'srt', 'vtt'}

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

        .nav-controls {
            display: flex;
            align-items: center;
            gap: 15px;
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
        /* Smaller button modifier */
        .nav-icon-btn.small-btn {
            width: 35px;
            height: 35px;
        }
        .nav-icon-btn.small-btn i {
            font-size: 0.9rem;
        }

        .nav-icon-btn img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .nav-icon-btn i {
            font-size: 1.1rem;
        }

        /* Mobile Specific */
        .navbar-toggler { display: none !important; }
        .navbar-collapse { display: none !important; }
    </style>
    <nav class="navbar navbar-expand-lg sticky-top">
        <div class="container">
            <div class="navbar-box">
                <a class="navbar-brand" href="/">hamiart.<span>education</span></a>

                <div class="nav-controls">
                    <!-- Logo Upload -->
                    <form action="/upload-logo" method="post" enctype="multipart/form-data" id="logo-form" style="margin: 0;">
                        <input type="file" name="logo" id="logo-file" hidden onchange="document.getElementById('logo-form').submit()" accept="image/*">
                        <div class="nav-icon-btn" onclick="document.getElementById('logo-file').click()" title="Upload Website Logo">
                            {% if logo_file %}
                                <img src="/uploads/{{ logo_file }}" alt="Logo">
                            {% else %}
                                <i class="fas fa-camera"></i>
                            {% endif %}
                        </div>
                    </form>

                    <!-- Wallpaper Upload (Moved from Body) -->
                    <form action="/wallpaper-blur/upload" method="post" enctype="multipart/form-data" id="nav-wall-form" style="margin: 0;">
                        <input type="file" name="background" id="nav-wall-file" hidden onchange="document.getElementById('nav-wall-form').submit()" accept="image/*">
                        <div class="nav-icon-btn small-btn" onclick="document.getElementById('nav-wall-file').click()" title="Set Wallpaper">
                            <i class="fas fa-image"></i>
                        </div>
                    </form>

                    <!-- Download PWA Button (Right of Wallpaper) -->
                    <div id="pwa-install-btn" class="nav-icon-btn small-btn" onclick="installPWA()" title="Download PWA" style="display:none;">
                        <i class="fas fa-download"></i>
                    </div>
                </div>
            </div>

            <!-- Hidden Toggler/Collapse -->
            <button class="navbar-toggler" type="button" style="display:none"></button>
            <div class="collapse navbar-collapse" id="navbarNav" style="display:none"></div>
        </div>
    </nav>

    <script>
        let deferredPrompt;
        const installBtn = document.getElementById('pwa-install-btn');

        window.addEventListener('beforeinstallprompt', (e) => {
            // Prevent Chrome 67 and earlier from automatically showing the prompt
            e.preventDefault();
            // Stash the event so it can be triggered later.
            deferredPrompt = e;
            // Update UI to notify the user they can add to home screen
            installBtn.style.display = 'flex';
        });

        function installPWA() {
            if (deferredPrompt) {
                // Show the prompt
                deferredPrompt.prompt();
                // Wait for the user to respond to the prompt
                deferredPrompt.userChoice.then((choiceResult) => {
                    if (choiceResult.outcome === 'accepted') {
                        console.log('User accepted the A2HS prompt');
                    } else {
                        console.log('User dismissed the A2HS prompt');
                    }
                    deferredPrompt = null;
                    installBtn.style.display = 'none';
                });
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

@app.route('/manifest.json')
def serve_manifest():
    return Response(MANIFEST_CONTENT, mimetype='application/manifest+json')

@app.route('/service-worker.js')
def serve_sw():
    return Response(SW_CONTENT, mimetype='application/javascript')

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


HTML_DOREMI = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- PWA Meta Tags -->
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#E5322D">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Hamiart">

    <title>Nada Dasar C | doremifasolasido</title>
    <link rel="icon" href="{{ url_for('static', filename='hamiartlogo.png') }}">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    {{ styles|safe }}
    <style>
        body, html {
            height: auto;
            min-height: 100%;
            margin: 0;
            overflow-y: auto;
            overflow-x: hidden;
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
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            /* Remove justify-content: center to allow top-down flow */
            padding-bottom: 50px;
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
</head>
<body>
    <div class="wallpaper-bg"></div>
    <div class="acrylic-overlay"></div>

    <div class="content-wrapper">
        {{ navbar|safe }}

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

        <footer style="background: transparent; border: none; color: rgba(255,255,255,0.7); padding: 20px; text-align: center;">
            <div class="container">
                <p>&copy; 2026 hamiart.education - All Rights Reserved. "We Making The Time"</p>
            </div>
        </footer>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Register Service Worker for PWA
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/service-worker.js')
                    .then(registration => {
                        console.log('ServiceWorker registration successful with scope: ', registration.scope);
                    })
                    .catch(err => {
                        console.log('ServiceWorker registration failed: ', err);
                    });
            });
        }

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
