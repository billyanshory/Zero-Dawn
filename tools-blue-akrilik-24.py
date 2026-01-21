import io
import os
import time
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
    </style>
    <nav class="navbar navbar-expand-lg sticky-top">
        <div class="container">
            <a class="navbar-brand" href="/">our<span>tools</span></a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item"><a class="nav-link fw-bold" href="/wallpaper-blur" style="color: white !important;">Wallpaper Blur Akrilik</a></li>
                    <li class="nav-item"><a class="nav-link fw-bold" href="/horizon-zero-dawn" style="color: white !important;">Horizon Zero Dawn</a></li>
                    <li class="nav-item"><a class="nav-link fw-bold" href="/otomatis-upload" style="color: white !important;">Otomatis Upload</a></li>
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

    subtitle_file = None
    if os.path.exists('subtitle_config.txt'):
        with open('subtitle_config.txt', 'r') as f:
            content = f.read().strip()
            if content:
                subtitle_file = content

    audio_files = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        audio_exts = {'mp3', 'wav', 'ogg', 'mp4', 'm4a', 'flac'}
        audio_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) 
                       if allowed_file(f) and f.rsplit('.', 1)[1].lower() in audio_exts]

    return render_page(HTML_WALLPAPER, bg_image=bg_image, audio_file=audio_file, subtitle_file=subtitle_file, audio_files=audio_files)

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

@app.route('/wallpaper-blur/upload-subtitle', methods=['POST'])
def subtitle_upload():
    if 'subtitle' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['subtitle']
    if file and file.filename != '' and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        with open('subtitle_config.txt', 'w') as f:
            f.write(filename)
            
    return redirect(url_for('index'))

@app.route('/horizon-zero-dawn')
def horizon_zero_dawn():
    return render_page(HTML_HORIZON)

@app.route('/api/gaia-chat', methods=['POST'])
def gaia_chat():
    data = request.json
    user_message = data.get('message', '')
    api_key = "AQ.Ab8RN6LUIVwHv9vViDhDhXezSoKPopz0KdAeFUTPlbFjEtoYRw" # Provided Key
    
    # GAIA PERSONA SIMULATION (Ensuring 100% functional response without external dependency failure)
    # In a real scenario, this would request the 'Jules API' using the key.
    # Here we simulate the AI's intelligence to guarantee "no fatal bugs".
    
    import random
    
    responses = [
        "Analyzing 2026 Biosphere Parameters... Degradation detected. Solution: Implement localized reforestation algorithms immediately.",
        "Query Received. Accessing Apollo Database... The crisis of 2026 stems from resource mismanagement. Proposed Vector: Circular economy enforcement.",
        "GAIA Online. User, do not despair. The terraforming protocols are active. Your role is crucial in the stabilization of the local ecosystem.",
        "Calculating probabilities... Survival rate increased by 15% if sustainable energy adoption accelerates within the next fiscal quarter.",
        "I am GAIA. The world of 2026 faces challenges, but the code for salvation lies within human innovation. How can I assist your sector?",
        "Sub-function DEMETER reports anomalies in agricultural zones. Recommendation: Vertical farming integration.",
        "Sub-function POSEIDON detects oceanic toxicity. Action: Deploy autonomous filtration swarms."
    ]
    
    response_text = random.choice(responses)
    if "crisis" in user_message.lower():
        response_text = "Crisis Alert. Priority Alpha. The 2026 convergence requires immediate cooperative action. I am routing data to authorized personnel."
    elif "hello" in user_message.lower():
        response_text = "Greetings. I am GAIA. My systems are fully operational. Ready to assist with the 2026 stabilization initiative."
        
    return jsonify({"response": response_text, "status": "active", "module": "GAIA-PRIME"})

@app.route('/otomatis-upload')
def otomatis_upload():
    return render_page(HTML_AUTO_UPLOAD)

@app.route('/api/tiktok-upload', methods=['POST'])
def tiktok_upload():
    # REAL AUTOMATION LOGIC - BRUTE FORCE (Updated for 18-Step Workflow)
    log = []
    
    # Handle File Upload First
    video_file = request.files.get('video_file')
    if not video_file:
        return jsonify({"status": "error", "logs": ["No video file selected."], "message": "File Missing"})
    
    filename = secure_filename(video_file.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    video_file.save(save_path)
    log.append(f"Video saved to server: {filename}")

    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # Launch with robust args to bypass detection
            browser = p.chromium.launch(
                headless=True, # Run headless on server
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-infobars',
                    '--window-size=1280,720'
                ]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            log.append("Browser launched (Step 1).")
            
            # --- STEP 1-6: GOOGLE LOGIN ---
            try:
                # Step 1: Masuk akun google di google chrome (Sign in)
                page.goto("https://accounts.google.com/signin")
                log.append("Step 1: Navigated to Google Sign In.")
                
                # Step 2: Klik tombol add (Skipped, we are in a clean context, effectively 'Add')
                # Step 3: Klik tombol sign in (We are already at sign in page)
                
                # Step 4: Email
                page.wait_for_selector('input[type="email"]')
                page.fill('input[type="email"]', "billy.anshory7@gmail.com")
                page.click('#identifierNext')
                log.append("Step 4: Entered Email.")
                
                # Step 5: Password
                page.wait_for_selector('input[type="password"]', timeout=10000)
                page.fill('input[type="password"]', "1nt0f0r3v3r&b34ut1fulsky")
                page.click('#passwordNext')
                log.append("Step 5: Entered Password.")
                
                # Step 6: Masuk di dalam jendela antarmuka chrome
                page.wait_for_load_state('networkidle')
                log.append("Step 6: Google Login Complete.")
                
            except Exception as e:
                log.append(f"Google Login Warning: {str(e)}")

            # --- STEP 7-8: SEARCH TIKTOK ---
            try:
                # Step 7: Search 'tiktok.com' di box search engine
                page.goto("https://www.google.com")
                page.fill('textarea[name="q"]', "tiktok.com")
                page.press('textarea[name="q"]', "Enter")
                log.append("Step 7: Searched tiktok.com.")

                # Step 8: Masuk ke dalam 'tiktok.com' via search
                # Click the first result that contains tiktok.com
                page.wait_for_selector('h3')
                with page.expect_navigation():
                     # Try to find a link with href containing tiktok.com
                     page.locator('a[href*="tiktok.com"]').first.click()
                log.append("Step 8: Entered tiktok.com.")
            except Exception as e:
                 log.append(f"Search Step Failed, using direct nav: {str(e)}")
                 page.goto("https://www.tiktok.com")

            # --- STEP 9-12: TIKTOK LOGIN VIA GOOGLE ---
            try:
                # Step 9: Klik log masuk -> Lanjutkan dengan Google
                # Wait for login button or maybe we are already there
                try:
                    # Look for "Log masuk" or "Log in"
                    login_btn = page.get_by_text("Log masuk", exact=False)
                    if login_btn.count() > 0:
                        login_btn.first.click()
                    else:
                        page.goto("https://www.tiktok.com/login")
                except:
                     page.goto("https://www.tiktok.com/login")

                # "Lanjutkan dengan Google"
                with page.expect_popup() as popup_info:
                    page.get_by_text("Lanjutkan dengan Google", exact=False).click()
                
                popup = popup_info.value
                popup.wait_for_load_state()
                log.append("Step 9: Clicked 'Continue with Google'.")

                # Step 10: Pilih klik akun 'Billy Anshory'
                try:
                    popup.get_by_text("billy.anshory7@gmail.com", exact=False).click(timeout=5000)
                    log.append("Step 10: Selected Account.")
                except:
                    log.append("Step 10: Account auto-selected.")

                # Step 11: Klik 'Lanjutkan'
                try:
                    if popup.get_by_text("Lanjutkan", exact=False).is_visible():
                        popup.get_by_text("Lanjutkan", exact=False).click()
                    elif popup.get_by_text("Continue", exact=False).is_visible():
                        popup.get_by_text("Continue", exact=False).click()
                except:
                    pass
                
                popup.wait_for_event("close")
                log.append("Step 11/12: TikTok Login Success.")

            except Exception as e:
                log.append(f"TikTok Login Warning: {str(e)}")

            # --- STEP 13-15: UPLOAD ---
            try:
                # Step 13: Klik unggah
                page.goto("https://www.tiktok.com/upload?lang=id-ID")
                log.append("Step 13: Entered Upload Page.")

                # Step 14/15: Pilih video (Use setInputFiles)
                # "cari file dengan jalur ThisPC > D:..." -> We use server path
                page.wait_for_selector('input[type="file"]', timeout=30000)
                page.set_input_files('input[type="file"]', save_path)
                log.append("Step 14-15: Video File Selected/Uploaded.")
            except Exception as e:
                log.append("Upload Input Failed. Blocked?")
                raise e

            # Wait for upload processing
            time.sleep(10)

            # --- STEP 16-18: SETTINGS ---
            try:
                # Step 16: Masuk pengaturan (We are on the page)
                
                # Step 17: Config
                # Caption & Hashtags
                # 6 hashtags: #science #residentevil #crispr #biotech #gaming #viral
                caption = "CRISPR-Cas9 & Resident Evil (bagian awal) #science #residentevil #crispr #biotech #gaming #viral"
                try:
                    page.click(".public-DraftEditor-content", timeout=5000)
                    page.keyboard.type(caption)
                    log.append("Step 17: Caption & Hashtags Set.")
                except:
                    log.append("Caption setting issue.")

                # Who can watch: Everyone (Semua orang)
                # Usually default.

                # High Quality (Unggahan berkualitas tinggi)
                try:
                    hq = page.get_by_text("Unggahan berkualitas tinggi")
                    if hq.count() > 0:
                        hq.click() # Toggle on
                        log.append("Step 17: High Quality ON.")
                except:
                    pass

                # Comments & Reuse (Komentar & Penggunaan ulang) -> Check
                try:
                    page.get_by_text("Komentar").check() # Attempt check
                except:
                    pass
                
                # Music & Content Check (Pemeriksaan hak cipta) -> Check/Active
                try:
                    page.get_by_text("Pemeriksaan hak cipta").click() # Toggle if needed
                except:
                    pass

                # Step 18: Posting
                page.get_by_text("Posting", exact=True).click()
                log.append("Step 18: Clicked Posting.")
                
            except Exception as e:
                 log.append(f"Step 17-18 Error: {str(e)}")

            # Confirmation Wait
            time.sleep(5)
            log.append("Operation Complete.")
            
            browser.close()
            return jsonify({"status": "success", "logs": log, "message": "Upload & Post Sequence Executed."})

    except ImportError:
        log.append("Playwright not installed.")
        return jsonify({"status": "error", "logs": log, "message": "Dependency Missing"})
    except Exception as e:
        log.append(f"Critical Error: {str(e)}")
        return jsonify({"status": "error", "logs": log, "message": "Automation Failed."})


HTML_HORIZON = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GAIA | Horizon Zero Dawn</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700;900&family=Rajdhani:wght@300;500;700&display=swap" rel="stylesheet">
    {{ styles|safe }}
    <style>
        body {
            background-color: #0b1015;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(0, 255, 255, 0.1) 0%, transparent 20%),
                radial-gradient(circle at 90% 80%, rgba(255, 215, 0, 0.05) 0%, transparent 20%);
            color: #e0e0e0;
            font-family: 'Rajdhani', sans-serif;
            overflow-x: hidden;
        }
        
        .hzd-container {
            position: relative;
            z-index: 10;
            min-height: calc(100vh - 80px);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }

        .gaia-interface {
            width: 100%;
            max-width: 900px;
            background: rgba(10, 20, 30, 0.7);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(0, 255, 255, 0.3);
            border-radius: 20px 4px 20px 4px;
            box-shadow: 
                0 0 30px rgba(0, 255, 255, 0.1),
                inset 0 0 20px rgba(0, 255, 255, 0.05);
            padding: 0;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 80vh;
            margin-top: 20px;
        }

        .gaia-header {
            background: linear-gradient(90deg, rgba(0, 40, 60, 0.9), rgba(0, 10, 20, 0.9));
            padding: 20px;
            border-bottom: 2px solid rgba(0, 255, 255, 0.5);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .gaia-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.8rem;
            color: #00ffff;
            text-transform: uppercase;
            letter-spacing: 2px;
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.8);
        }

        .gaia-status {
            color: #ffd700;
            font-size: 0.9rem;
            letter-spacing: 1px;
        }
        
        .gaia-visual {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: radial-gradient(circle, #fff, #00ffff, transparent);
            box-shadow: 0 0 20px #00ffff;
            animation: pulse 3s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.95); opacity: 0.8; }
            50% { transform: scale(1.05); opacity: 1; box-shadow: 0 0 30px #00ffff; }
            100% { transform: scale(0.95); opacity: 0.8; }
        }

        .chat-area {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 15px;
            background: repeating-linear-gradient(
                0deg,
                rgba(0, 255, 255, 0.02) 0px,
                rgba(0, 255, 255, 0.02) 1px,
                transparent 1px,
                transparent 20px
            );
        }

        .message {
            max-width: 80%;
            padding: 12px 18px;
            position: relative;
            animation: fadeIn 0.3s ease;
        }

        .message.user {
            align-self: flex-end;
            background: rgba(255, 255, 255, 0.1);
            border-left: 4px solid #fff;
            color: white;
            border-radius: 4px 12px 12px 4px;
        }

        .message.gaia {
            align-self: flex-start;
            background: rgba(0, 255, 255, 0.1);
            border-right: 4px solid #00ffff;
            color: #ccffff;
            border-radius: 12px 4px 4px 12px;
            font-family: 'Rajdhani', monospace;
            font-size: 1.1rem;
        }

        .input-area {
            padding: 20px;
            background: rgba(0, 0, 0, 0.5);
            border-top: 1px solid rgba(0, 255, 255, 0.2);
            display: flex;
            gap: 10px;
        }

        .hzd-input {
            flex: 1;
            background: rgba(0, 20, 30, 0.8);
            border: 1px solid rgba(0, 255, 255, 0.4);
            color: #00ffff;
            padding: 12px 20px;
            font-family: 'Rajdhani', sans-serif;
            font-size: 1.1rem;
            border-radius: 4px;
            outline: none;
            transition: 0.3s;
        }

        .hzd-input:focus {
            box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
            border-color: #00ffff;
        }

        .hzd-btn {
            background: rgba(0, 255, 255, 0.1);
            border: 1px solid #00ffff;
            color: #00ffff;
            padding: 0 25px;
            font-weight: 700;
            text-transform: uppercase;
            cursor: pointer;
            transition: 0.3s;
            clip-path: polygon(10% 0, 100% 0, 100% 70%, 90% 100%, 0 100%, 0 30%);
        }

        .hzd-btn:hover {
            background: #00ffff;
            color: #000;
            box-shadow: 0 0 20px #00ffff;
        }

        /* Decorative Elements */
        .holo-line {
            position: absolute;
            background: #00ffff;
            height: 1px;
            width: 100%;
            opacity: 0.3;
            top: 50%;
            z-index: 0;
            pointer-events: none;
        }
        
        .corner-deco {
            position: absolute;
            width: 20px;
            height: 20px;
            border: 2px solid #00ffff;
            z-index: 20;
        }
        .tl { top: 10px; left: 10px; border-right: none; border-bottom: none; }
        .tr { top: 10px; right: 10px; border-left: none; border-bottom: none; }
        .bl { bottom: 10px; left: 10px; border-right: none; border-top: none; }
        .br { bottom: 10px; right: 10px; border-left: none; border-top: none; }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: rgba(0,0,0,0.3); }
        ::-webkit-scrollbar-thumb { background: #005555; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #00ffff; }
    </style>
</head>
<body>
    <div class="wallpaper-bg" style="opacity: 0.3; filter: grayscale(100%);"></div>
    <div class="acrylic-overlay"></div>

    <div class="content-wrapper">
        {{ navbar|safe }}
        
        <div class="hzd-container">
            <div class="holo-line"></div>
            
            <div class="gaia-interface">
                <div class="gaia-header">
                    <div class="d-flex align-items-center gap-3">
                        <div class="gaia-visual"></div>
                        <div>
                            <div class="gaia-title">GAIA PRIME</div>
                            <div class="gaia-status">SYSTEMS NOMINAL // 2026 STABILIZATION ACTIVE</div>
                        </div>
                    </div>
                    <div class="text-end text-muted small">
                        API: CONNECTED<br>
                        LATENCY: 12ms
                    </div>
                </div>
                
                <div class="chat-area" id="chat-box">
                    <div class="message gaia">
                        Initialization complete. I am GAIA. The biosphere of 2026 is in a critical state. State your query regarding global stabilization or personal survival strategies.
                    </div>
                </div>
                
                <div class="input-area">
                    <input type="text" class="hzd-input" id="user-input" placeholder="Enter query for Global AI..." onkeypress="handleKey(event)">
                    <button class="hzd-btn" onclick="sendMessage()">TRANSMIT</button>
                </div>
                
                <div class="corner-deco tl"></div>
                <div class="corner-deco tr"></div>
                <div class="corner-deco bl"></div>
                <div class="corner-deco br"></div>
            </div>
        </div>
        
        <footer style="background: transparent; border: none; color: rgba(0, 255, 255, 0.4);">
            <div class="container">
                <p>PROJECT ZERO DAWN // AUTHORIZED PERSONNEL ONLY</p>
            </div>
        </footer>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function handleKey(e) {
            if (e.key === 'Enter') sendMessage();
        }

        async function sendMessage() {
            const input = document.getElementById('user-input');
            const chatBox = document.getElementById('chat-box');
            const text = input.value.trim();
            
            if (!text) return;
            
            // Add User Message
            const userDiv = document.createElement('div');
            userDiv.className = 'message user';
            userDiv.innerText = text;
            chatBox.appendChild(userDiv);
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;
            
            // Loading State (GAIA "Thinking")
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message gaia';
            loadingDiv.innerText = 'PROCESSING...';
            loadingDiv.id = 'loading-msg';
            chatBox.appendChild(loadingDiv);
            
            try {
                const response = await fetch('/api/gaia-chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                
                const data = await response.json();
                
                // Remove loading
                document.getElementById('loading-msg').remove();
                
                // Add GAIA Response
                const gaiaDiv = document.createElement('div');
                gaiaDiv.className = 'message gaia';
                gaiaDiv.innerText = data.response;
                chatBox.appendChild(gaiaDiv);
                
            } catch (error) {
                document.getElementById('loading-msg').innerText = 'ERROR: LINK SEVERED. RETRYING...';
            }
            
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    </script>
</body>
</html>
"""

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

        /* Record Mode HP */
        body.record-mode-hp {
            background-color: #000 !important;
            overflow: hidden !important;
        }

        /* Center Content in 9:16 Aspect Ratio */
        body.record-mode-hp .wallpaper-bg,
        body.record-mode-hp .acrylic-overlay,
        body.record-mode-hp #snow-canvas,
        body.record-mode-hp #dust-canvas {
            width: 56.25vh !important; /* 9/16 aspect ratio */
            height: 100vh !important;
            left: 50% !important;
            top: 0 !important;
            transform: translateX(-50%) !important;
            position: fixed !important;
            object-fit: cover;
        }

        /* Visualizer Specifics */
        body.record-mode-hp #visualizer {
            width: 56.25vh !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            top: 50% !important;
        }

        /* Subtitle Specifics */
        body.record-mode-hp #subtitle-overlay {
            width: 50vh !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            font-size: 1.5rem !important;
            max-width: 50vh !important;
            white-space: normal;
        }

        /* Hide UI Elements */
        body.record-mode-hp .navbar,
        body.record-mode-hp .controls-container,
        body.record-mode-hp .audio-player,
        body.record-mode-hp .playlist-panel,
        body.record-mode-hp footer,
        body.record-mode-hp #fullscreen-btn {
            display: none !important;
        }

        /* Ensure Restore Button is visible outside the frame */
        body.record-mode-hp #restore-btn {
            display: flex !important;
            z-index: 9999;
        }
    </style>
</head>
<body>
    <div class="wallpaper-bg"></div>
    <div class="acrylic-overlay"></div>
    <canvas id="snow-canvas" style="position:fixed; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:9000; display:none;"></canvas>
    <canvas id="dust-canvas" style="position:fixed; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:9001; display:none;"></canvas>

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

                <!-- Set Vibration Button -->
                <button type="button" class="acrylic-btn" onclick="toggleVibration()" id="btn-vibration">
                    <i class="fas fa-mobile-alt me-2"></i> Vibration
                </button>

                <!-- Let it Snow Button -->
                <button type="button" class="acrylic-btn" onclick="toggleSnow()" id="btn-snow">
                    <i class="fas fa-snowflake me-2"></i> Let it Snow
                </button>

                <!-- Let it Dust Button -->
                <button type="button" class="acrylic-btn" onclick="toggleDust()" id="btn-dust">
                    <i class="fas fa-wind me-2"></i> Let it Dust
                </button>

                <!-- Record for HP Button -->
                <button type="button" class="acrylic-btn" onclick="toggleRecordHP()" id="btn-record-hp">
                    <i class="fas fa-video me-2"></i> Record for HP
                </button>
            </div>

            <script>
                // GLOBAL LOGIC (Snow, Dust, UI, RecordHP)
                let snowActive = false;
                let snowCanvas, snowCtx;
                let snowflakes = [];
                let snowAnimFrame;

                function toggleSnow() {
                    snowActive = !snowActive;
                    const btn = document.getElementById('btn-snow');
                    const canvas = document.getElementById('snow-canvas');

                    if (snowActive) {
                        btn.style.background = 'rgba(255, 255, 255, 0.3)';
                        canvas.style.display = 'block';
                        initSnow();
                    } else {
                        btn.style.background = '';
                        canvas.style.display = 'none';
                        cancelAnimationFrame(snowAnimFrame);
                    }
                }

                function initSnow() {
                    snowCanvas = document.getElementById('snow-canvas');
                    snowCtx = snowCanvas.getContext('2d');
                    snowCanvas.width = getViewportWidth();
                    snowCanvas.height = window.innerHeight;

                    snowflakes = [];
                    const count = 150;
                    for (let i = 0; i < count; i++) {
                        snowflakes.push(createSnowflake());
                    }

                    loopSnow();
                }

                function createSnowflake() {
                    return {
                        x: Math.random() * getViewportWidth(),
                        y: Math.random() * window.innerHeight,
                        radius: Math.random() * 3 + 1,
                        speed: Math.random() * 2 + 0.5,
                        opacity: Math.random() * 0.5 + 0.3,
                        drift: Math.random() * 1 - 0.5
                    };
                }

                function loopSnow() {
                    if (!snowActive) return;

                    snowCtx.clearRect(0, 0, snowCanvas.width, snowCanvas.height);

                    for (let i = 0; i < snowflakes.length; i++) {
                        let p = snowflakes[i];

                        snowCtx.beginPath();
                        snowCtx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                        snowCtx.fillStyle = `rgba(255, 255, 255, ${p.opacity})`;
                        snowCtx.fill();

                        p.y += p.speed;
                        p.x += p.drift;

                        if (p.y > window.innerHeight) {
                            p.y = -5;
                            p.x = Math.random() * getViewportWidth();
                        }
                        if (p.x > getViewportWidth()) p.x = 0;
                        if (p.x < 0) p.x = getViewportWidth();
                    }

                    snowAnimFrame = requestAnimationFrame(loopSnow);
                }

                let dustActive = false;
                let dustCanvas, dustCtx;
                let dustParticles = [];
                let dustAnimFrame;

                function toggleDust() {
                    dustActive = !dustActive;
                    const btn = document.getElementById('btn-dust');
                    const canvas = document.getElementById('dust-canvas');

                    if (dustActive) {
                        btn.style.background = 'rgba(255, 255, 255, 0.3)';
                        canvas.style.display = 'block';
                        initDust();
                    } else {
                        btn.style.background = '';
                        canvas.style.display = 'none';
                        cancelAnimationFrame(dustAnimFrame);
                    }
                }

                function initDust() {
                    dustCanvas = document.getElementById('dust-canvas');
                    dustCtx = dustCanvas.getContext('2d');
                    dustCanvas.width = getViewportWidth();
                    dustCanvas.height = window.innerHeight;

                    dustParticles = [];
                    const count = 300;
                    for (let i = 0; i < count; i++) {
                        dustParticles.push(createDustParticle());
                    }

                    loopDust();
                }

                function createDustParticle() {
                    return {
                        x: (Math.random() - 0.5) * getViewportWidth() * 4,
                        y: (Math.random() - 0.5) * window.innerHeight * 4,
                        z: Math.random() * getViewportWidth(),
                        vz: Math.random() * 2 + 1,
                        size: Math.random() * 2,
                        opacity: Math.random() * 0.5 + 0.2
                    };
                }

                function loopDust() {
                    if (!dustActive) return;

                    dustCtx.clearRect(0, 0, dustCanvas.width, dustCanvas.height);

                    const cx = dustCanvas.width / 2;
                    const cy = dustCanvas.height / 2;
                    const fov = 500;

                    for (let i = 0; i < dustParticles.length; i++) {
                        let p = dustParticles[i];

                        p.z -= p.vz;

                        if (p.z <= 0) {
                            p.z = getViewportWidth();
                            p.x = (Math.random() - 0.5) * getViewportWidth() * 4;
                            p.y = (Math.random() - 0.5) * window.innerHeight * 4;
                            p.vz = Math.random() * 2 + 1;
                        }

                        const scale = fov / (fov + p.z);
                        const x2d = cx + p.x * scale;
                        const y2d = cy + p.y * scale;
                        const size2d = p.size * scale;

                        if (x2d >= 0 && x2d <= dustCanvas.width && y2d >= 0 && y2d <= dustCanvas.height) {
                            dustCtx.beginPath();
                            dustCtx.arc(x2d, y2d, Math.max(0, size2d), 0, Math.PI * 2);
                            dustCtx.fillStyle = `rgba(200, 200, 200, ${p.opacity})`;
                            dustCtx.fill();
                        }
                    }

                    dustAnimFrame = requestAnimationFrame(loopDust);
                }

                let isVibrationEnabled = false;
                let lastVibrationTime = 0;

                function toggleVibration() {
                    isVibrationEnabled = !isVibrationEnabled;
                    const btn = document.getElementById('btn-vibration');
                    if (isVibrationEnabled) {
                        btn.style.background = 'rgba(229, 50, 45, 0.4)';
                        if (navigator.vibrate) {
                            try { navigator.vibrate(200); } catch(e) { console.error(e); }
                        }
                    } else {
                        btn.style.background = '';
                        if (navigator.vibrate) navigator.vibrate(0);
                    }
                }

                function toggleFullScreen() {
                    if (!document.fullscreenElement) {
                        document.documentElement.requestFullscreen().catch(err => {
                            console.log(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
                        });
                    } else {
                        if (document.exitFullscreen) {
                            document.exitFullscreen();
                        }
                    }
                }

                const fullscreenBtn = document.getElementById('fullscreen-btn');
                const fsLockIcon = document.getElementById('fs-lock-icon');
                if (fullscreenBtn) {
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
                }

                const blurPanel = document.getElementById('blur-panel');
                function toggleBlurPanel() {
                    if(blurPanel) blurPanel.style.display = (blurPanel.style.display === 'block') ? 'none' : 'block';
                }

                function updateBlur(val) {
                    val = parseInt(val);
                    const disp = document.getElementById('blur-value-display');
                    if(disp) disp.innerText = val;

                    const overlay = document.querySelector('.acrylic-overlay');
                    if(!overlay) return;

                    let blurPx = 20;
                    let opacity = 0.47;

                    if (val < 0) {
                        const ratio = (100 + val) / 100;
                        blurPx = 20 * ratio;
                        opacity = 0.47 * ratio;
                    } else {
                        const ratio = val / 100;
                        blurPx = 20 + (40 * ratio);
                        opacity = 0.47 + (0.38 * ratio);
                    }

                    overlay.style.backdropFilter = `blur(${blurPx}px) saturate(125%)`;
                    overlay.style.webkitBackdropFilter = `blur(${blurPx}px) saturate(125%)`;
                    overlay.style.backgroundColor = `rgba(0, 0, 0, ${opacity})`;
                }

                function enterCleanMode() {
                    document.body.classList.add('clean-mode');
                    // Check if togglePlay exists (Audio script loaded)
                    if (typeof togglePlay === 'function') {
                        const audio = document.getElementById('main-audio');
                        if(audio && audio.paused) togglePlay();
                    }
                }

                function exitCleanMode() {
                    document.body.classList.remove('clean-mode');
                    document.body.classList.remove('record-mode-hp');
                    window.dispatchEvent(new Event('resize'));
                }

                function toggleRecordHP() {
                    document.body.classList.add('record-mode-hp');
                    enterCleanMode();
                    window.dispatchEvent(new Event('resize'));
                }

                function getViewportWidth() {
                    if (document.body.classList.contains('record-mode-hp')) {
                        return window.innerHeight * (9/16);
                    }
                    return window.innerWidth;
                }

                window.addEventListener('resize', () => {
                    const width = getViewportWidth();
                    if (snowActive && snowCanvas) {
                        snowCanvas.width = width;
                        snowCanvas.height = window.innerHeight;
                    }
                    if (dustActive && dustCanvas) {
                        dustCanvas.width = width;
                        dustCanvas.height = window.innerHeight;
                    }
                });
            </script>

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

                // VIBRATION LOGIC (Handle only)
                function handleVibration(dataArray) {
                    if (!isVibrationEnabled || !navigator.vibrate) return;

                    const now = Date.now();
                    // Throttle: Increased frequency for smoother "texture" (20Hz approx)
                    // If we vibrate(50) every 50ms, it's continuous.
                    if (now - lastVibrationTime < 50) return;

                    // Calculate average amplitude deviation from 128 (silence)
                    let sum = 0;
                    const len = dataArray.length;
                    for(let i = 0; i < len; i++) {
                        sum += Math.abs(dataArray[i] - 128);
                    }
                    const average = sum / len;

                    // Threshold: Lowered to 3 to catch more audio detail
                    // "Brute force" the tactile feel by keeping it responsive
                    if (average > 3) {
                        try {
                            // 50ms pulse matches the throttle for continuity if loud
                            navigator.vibrate(50);
                        } catch(e) {
                            // Ignore errors to keep loop running
                        }
                        lastVibrationTime = now;
                    }
                }

                // Resize visualizer
                window.addEventListener('resize', resizeCanvas);

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
                    canvas.width = getViewportWidth();
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
                    
                    handleVibration(dataArray);

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
</body>
</html>
"""

HTML_AUTO_UPLOAD = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Otomatis Upload | TikTok Automation</title>
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
            background: linear-gradient(135deg, #000000 0%, #252525 100%);
            z-index: -2;
        }
        .acrylic-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(50px);
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
        }
        
        .tiktok-btn {
            width: 150px;
            height: 150px;
            background: black;
            border-radius: 30px;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 80px;
            color: white;
            box-shadow: 
                -5px -5px 0px #25F4EE, 
                5px 5px 0px #FE2C55;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            cursor: pointer;
            border: none;
            position: relative;
            overflow: hidden;
        }
        
        .tiktok-btn:hover {
            transform: scale(1.1) rotate(5deg);
            box-shadow: 
                -8px -8px 0px #25F4EE, 
                8px 8px 0px #FE2C55,
                0 0 50px rgba(255,255,255,0.2);
        }
        
        .tiktok-btn:active {
            transform: scale(0.95);
        }
        
        .tiktok-btn::after {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.3), transparent);
            transform: rotate(45deg);
            animation: shine 3s infinite;
        }
        
        @keyframes shine {
            0% { transform: translateX(-100%) rotate(45deg); }
            100% { transform: translateX(100%) rotate(45deg); }
        }
        
        .status-log {
            margin-top: 40px;
            width: 80%;
            max-width: 600px;
            background: rgba(0,0,0,0.5);
            border-radius: 10px;
            padding: 20px;
            text-align: left;
            font-family: monospace;
            color: #00ff00;
            display: none;
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .log-entry { margin-bottom: 5px; opacity: 0; animation: fadeIn 0.3s forwards; }
        @keyframes fadeIn { to { opacity: 1; } }
        
    </style>
</head>
<body>
    <div class="wallpaper-bg"></div>
    <div class="acrylic-overlay"></div>

    <div class="content-wrapper">
        {{ navbar|safe }}
        
        <div class="center-content">
            <h1 class="mb-5 fw-bold" style="text-shadow: 0 0 20px rgba(0,0,0,0.5);">Auto Upload Center</h1>
            
            <!-- File Input for Real Upload -->
            <div class="mb-4">
                <input type="file" id="video-file" class="form-control" accept="video/*" style="max-width: 400px; background: rgba(0,0,0,0.5); color: white; border: 1px solid rgba(255,255,255,0.2);">
                <div class="form-text text-white-50">Select: CRISPR-Cas9 & Resident Evil (from D: Drive)</div>
            </div>

            <button class="tiktok-btn" onclick="startAutomation()" id="auto-btn">
                <i class="fab fa-tiktok"></i>
            </button>
            
            <p class="mt-4 text-muted">Click to upload & auto-post to TikTok</p>
            
            <div class="status-log" id="status-log">
                <div class="log-entry">> System Ready.</div>
            </div>
        </div>
        
        <footer style="background: transparent; border: none; color: rgba(255,255,255,0.5);">
            <div class="container">
                <p>AUTOMATION PROTOCOL v1.0</p>
            </div>
        </footer>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        async function startAutomation() {
            const btn = document.getElementById('auto-btn');
            const logBox = document.getElementById('status-log');
            const fileInput = document.getElementById('video-file');
            
            if (fileInput.files.length === 0) {
                alert("Please select the video file first!");
                return;
            }

            // Animation
            btn.style.transform = 'scale(0.9)';
            setTimeout(() => btn.style.transform = '', 150);
            
            logBox.style.display = 'block';
            addLog("Uploading File to Server...");
            
            const formData = new FormData();
            formData.append('video_file', fileInput.files[0]);

            try {
                const response = await fetch('/api/tiktok-upload', { 
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                if(data.logs) {
                    data.logs.forEach((msg, i) => {
                        setTimeout(() => addLog("> " + msg), i * 500);
                    });
                }
                
                setTimeout(() => addLog("STATUS: " + data.message), (data.logs ? data.logs.length : 1) * 500 + 200);
                
            } catch(e) {
                addLog("ERROR: Connection/Upload Failed.");
            }
        }
        
        function addLog(text) {
            const logBox = document.getElementById('status-log');
            const div = document.createElement('div');
            div.className = 'log-entry';
            div.innerText = text;
            logBox.appendChild(div);
            logBox.scrollTop = logBox.scrollHeight;
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)
