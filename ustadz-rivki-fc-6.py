import os
import sqlite3
import time
from flask import Flask, request, send_from_directory, redirect, url_for, render_template_string, jsonify
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

def init_agenda_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    # Table to store text content for agenda items (both static and dynamic)
    c.execute('''CREATE TABLE IF NOT EXISTS agenda_content (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    status TEXT,
                    price TEXT
                )''')
    # Table to track the list of dynamic cards
    c.execute('''CREATE TABLE IF NOT EXISTS agenda_list (
                    id TEXT PRIMARY KEY,
                    section INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    conn.commit()
    conn.close()

init_agenda_db()

# --- DATA HELPER ---
def get_agenda_content_from_db():
    conn = sqlite3.connect('data.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get all text content
    c.execute("SELECT * FROM agenda_content")
    rows = c.fetchall()
    content_map = {row['id']: dict(row) for row in rows}
    
    # Get dynamic items
    c.execute("SELECT * FROM agenda_list ORDER BY created_at ASC")
    dynamic_rows = c.fetchall()
    
    conn.close()
    return content_map, dynamic_rows

def get_agenda_data():
    content_map, dynamic_rows = get_agenda_content_from_db()
    
    data = []
    # 1. Static items (agenda1 to agenda18)
    for i in range(1, 19):
        item_id = f"agenda{i}"
        # Use DB content if exists, else default
        if item_id in content_map:
            db_item = content_map[item_id]
            title = db_item['title']
            price = db_item['price']
            # status stored as text in DB
            status_text = db_item['status']
        else:
            title = "Judul Agenda"
            price = "Waktu/Tempat"
            status_text = "Tersedia"

        data.append({
            "id": item_id, 
            "title": title, 
            "price": price, 
            "status_text": status_text, # Passed to template
            "available": True,
            "desc_id": "Masih menunggu pengembangan",
            "desc_en": "Still waiting for development",
            "is_dynamic": False
        })
        
    # 2. Dynamic items
    for row in dynamic_rows:
        item_id = row['id']
        section = row['section']
        if item_id in content_map:
            db_item = content_map[item_id]
            title = db_item['title']
            price = db_item['price']
            status_text = db_item['status']
        else:
            title = "New Agenda"
            price = "Rp 0"
            status_text = "Tersedia"
            
        data.append({
            "id": item_id,
            "title": title,
            "price": price,
            "status_text": status_text,
            "available": True,
            "desc_id": "Masih menunggu pengembangan",
            "desc_en": "Still waiting for development",
            "section": section, # 1 or 2
            "is_dynamic": True
        })
        
    return data

# --- ROUTES ---

def render_page(content, **kwargs):
    # Inject fragments before rendering to allow Jinja to process them
    content = content.replace('{{ styles|safe }}', STYLES_HTML)
    content = content.replace('{{ navbar|safe }}', NAVBAR_HTML)
    return render_template_string(content, **kwargs)

@app.route('/')
def index():
    full_data = get_agenda_data()

    # Split static items (agenda1-18)
    # agenda1..9 -> Section 1
    # agenda10..18 -> Section 2
    # Plus dynamic items based on their 'section' field

    agenda1 = [x for x in full_data if (not x.get('is_dynamic') and int(x['id'].replace('agenda','')) <= 9) or (x.get('is_dynamic') and x['section'] == 1)]
    agenda2 = [x for x in full_data if (not x.get('is_dynamic') and int(x['id'].replace('agenda','')) > 9) or (x.get('is_dynamic') and x['section'] == 2)]

    # Scan for images for ALL items in full_data
    game_images = {}
    for item in full_data:
        item_id = item['id']
        found = None
        for ext in ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif', 'tiff', 'svg', 'ico']:
             fname = f"{item_id}.{ext}"
             if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], fname)):
                 found = fname
                 break
        game_images[item_id] = found if found else None

    # We reuse 'games' variable name in template for the modal data source
    return render_page(HTML_UR_FC, game_images=game_images, games=full_data, agenda1=agenda1, agenda2=agenda2)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload-agenda-image/<item_id>', methods=['POST'])
def upload_agenda_image(item_id):
    if 'game_image' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['game_image']
    if file and file.filename != '' and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        # Remove old images for this item_id
        for e in ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif', 'tiff', 'svg', 'ico']:
            old_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{item_id}.{e}")
            if os.path.exists(old_path):
                os.remove(old_path)
                
        new_filename = f"{item_id}.{ext}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))

    return redirect(url_for('index'))

@app.route('/api/update-agenda-text', methods=['POST'])
def api_update_agenda_text():
    data = request.json
    item_id = data.get('id')
    title = data.get('title')
    status = data.get('status')
    price = data.get('price')
    
    if not item_id:
        return jsonify({'error': 'Missing ID'}), 400
        
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    # Upsert logic (Insert or Replace)
    c.execute("""
        INSERT INTO agenda_content (id, title, status, price) 
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
        title=excluded.title,
        status=excluded.status,
        price=excluded.price
    """, (item_id, title, status, price))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/add-agenda-card', methods=['POST'])
def api_add_agenda_card():
    data = request.json
    section = data.get('section') # 1 or 2
    
    if not section:
        return jsonify({'error': 'Missing Section'}), 400

    new_id = f"agenda_dynamic_{int(time.time() * 1000)}"
    
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("INSERT INTO agenda_list (id, section) VALUES (?, ?)", (new_id, section))
    # Initialize content with defaults
    c.execute("INSERT INTO agenda_content (id, title, status, price) VALUES (?, ?, ?, ?)", 
              (new_id, "New Agenda", "Tersedia", "Rp 0"))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'id': new_id})


# --- FRONTEND FRAGMENTS ---

NAVBAR_HTML = """
    <style>
        .navbar {
            background-color: rgba(0, 0, 0, 0.6) !important;
            backdrop-filter: blur(15px) saturate(120%);
            -webkit-backdrop-filter: blur(15px) saturate(120%);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        }
        .navbar-brand {
            font-weight: 800;
            font-size: 1.8rem;
            color: white !important;
            letter-spacing: -1px;
            text-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
        }
        .brand-verse {
            color: #FFD700;
            text-shadow: 0 0 5px #FFD700, 0 0 10px #FFD700, 0 0 20px #FFD700;
            font-style: italic;
            font-family: 'Inter', sans-serif; /* Ensuring consistent font */
        }
        .nav-link {
            color: rgba(255, 255, 255, 0.8) !important;
            font-weight: 500;
            margin-right: 15px;
            transition: color 0.3s;
            white-space: nowrap !important;
        }
        .nav-link:hover {
            color: white !important;
            text-shadow: 0 0 8px rgba(255,255,255,0.5);
        }
        .join-btn {
            border: 1px solid #FFD700;
            color: #FFD700 !important;
            border-radius: 5px;
            padding: 5px 30px;
            box-shadow: 0 0 5px rgba(255, 215, 0, 0.2);
            transition: all 0.3s;
            white-space: nowrap !important;
        }
        .join-btn:hover {
            background: rgba(255, 215, 0, 0.1);
            box-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
        }
        /* Mobile Menu Toggler White Fix */
        .navbar-toggler {
            border-color: rgba(255,255,255,0.5) !important;
        }
        .navbar-toggler-icon {
            filter: brightness(0) invert(1) !important;
        }
        
        /* Mobile Menu Acrylic Box - Adjusted to be lighter/glassy */
        @media (max-width: 991px) {
            .navbar-collapse {
                background: transparent; /* Polos - blends with main navbar */
                border: none;
                border-radius: 0;
                padding: 0; /* Remove padding to blend perfectly */
                margin-top: 0;
                box-shadow: none;
            }
            .navbar-nav {
                padding: 15px 0; /* Add internal padding instead */
            }
            .nav-link {
                font-size: 0.9rem;
            }
            .navbar-brand {
                font-size: 1.4rem; /* Slightly smaller on mobile to prevent wrap */
            }
        }
        
        /* Logo Modal */
        #logo-modal {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.47); /* Acrylic blur aesthetic */
            backdrop-filter: blur(20px) saturate(125%);
            -webkit-backdrop-filter: blur(20px) saturate(125%);
            z-index: 9999;
            display: none;
            justify-content: center;
            align-items: center;
            opacity: 0;
            transition: opacity 0.3s;
        }
        #logo-modal.active {
            display: flex;
            opacity: 1;
        }
        #logo-modal img {
            max-width: 90%;
            max-height: 90%;
            object-fit: contain;
            border-radius: 50%; /* Keep circular aesthetic */
            box-shadow: 0 0 30px rgba(255, 255, 255, 0.2);
            transition: transform 0.3s;
        }
        #logo-modal img:hover {
            transform: scale(1.05);
        }
    </style>
    <nav class="navbar navbar-expand-lg sticky-top">
        <div class="container-fluid px-4 px-lg-4">
            <div class="d-flex align-items-center">
                <!-- Logo Image - Triggers Popup -->
                <img src="{{ url_for('static', filename='logo-tahkil-fc.png') }}" alt="Logo" 
                     onclick="viewLogo()" 
                     style="height: 50px; margin-right: 10px; cursor: pointer; transition: transform 0.2s;"
                     onmouseover="this.style.transform='scale(1.1)'" 
                     onmouseout="this.style.transform='scale(1)'">
                
                <!-- Brand Text - Triggers Scroll to Top -->
                <a class="navbar-brand m-0 p-0" href="#" onclick="window.scrollTo({top: 0, behavior: 'smooth'}); return false;">
                    TAHFIZH <span class="brand-verse ps-2">KILAT FC</span>
                </a>
            </div>
            
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon" style="filter: brightness(0) invert(1);"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav mx-lg-auto text-center">
                    <li class="nav-item">
                        <a class="nav-link" href="#popular-games" onclick="smoothScroll(event, 'popular-games')">
                            <span class="lang-id">Agenda Latihan TAHKIL FC</span>
                            <span class="lang-en" style="display:none">Practice Agenda TAHKIL FC</span>
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#next-agenda" onclick="smoothScroll(event, 'next-agenda')">
                            <span class="lang-id">Next Agenda</span>
                            <span class="lang-en" style="display:none">Next Agenda</span>
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#footer-social" onclick="smoothScroll(event, 'footer-social')">
                            <span class="lang-id">Social Media</span>
                            <span class="lang-en" style="display:none">Social Media</span>
                        </a>
                    </li>
                </ul>
                <ul class="navbar-nav ms-auto align-items-center">
                    <li class="nav-item">
                        <a class="nav-link join-btn" href="https://chat.whatsapp.com/invite/placeholder" target="_blank">
                            <span class="lang-id">Gabung Grup Whatsapp TAHKIL FC</span>
                            <span class="lang-en" style="display:none">Join TAHKIL FC WhatsApp Group</span>
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
    <script>
        function smoothScroll(e, id) {
            e.preventDefault();
            const el = document.getElementById(id);
            if(el) {
                el.scrollIntoView({ behavior: 'smooth' });
            } else {
                // Fallback if on a page where elements don't exist (legacy pages)
                window.location.href = '/#' + id;
            }
        }
    </script>
"""

STYLES_HTML = """
    <style>
        :root {
            --brand-color: #2ecc71;
            --brand-hover: #27ae60;
            --bg-light: #f4f7fa;
            --card-bg: #ffffff;
            --text-dark: #333333;
            --text-muted: #666666;
            --neon-blue: #FFD700;
            --neon-green: #2ecc71;
        }
        /* Keep existing variable definitions */
        [data-bs-theme="dark"] {
            --bg-light: #1a1a1a;
            --card-bg: #2d2d2d;
            --text-dark: #f1f1f1;
            --text-muted: #aaaaaa;
        }
        body {
            font-family: 'Inter', sans-serif;
        }
        html {
            scroll-behavior: smooth;
        }
        
        .text-blue-neon {
            color: var(--neon-blue);
            text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
        }
        
        .btn-cyan-neon {
            background: transparent;
            border: 2px solid var(--neon-blue);
            color: var(--neon-blue);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: 0 0 10px rgba(255, 215, 0, 0.2);
            transition: all 0.3s;
        }
        .btn-cyan-neon:hover {
            background: var(--neon-blue);
            color: black;
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.6);
            transform: translateY(-2px);
        }
        
        .btn-buy-card {
            background: transparent;
            border: 1px solid var(--neon-blue);
            color: var(--neon-blue);
            font-size: 0.8rem;
            padding: 5px 12px;
            border-radius: 20px;
            transition: 0.3s;
            cursor: pointer;
            text-transform: uppercase;
            font-weight: 700;
        }
        .btn-buy-card:hover {
            background: var(--neon-blue);
            color: black;
            box-shadow: 0 0 10px var(--neon-blue);
        }
    </style>
"""

HTML_UR_FC = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TAHFIZH KILAT FC</title>
    <link rel="shortcut icon" href="{{ url_for('static', filename='logo-tahkil-fc.png') }}">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    {{ styles|safe }}
    <style>
        body {
            background-color: #FFFFFF;
            background-image: url("{{ url_for('static', filename='logo-tahkil-fc.png') }}");
            background-size: contain;
            background-attachment: fixed;
            background-position: center;
            background-repeat: no-repeat;
            color: #333333; /* Dark text for readability on white bg */
        }
        .acrylic-overlay-page {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(255, 255, 255, 0.3);
            backdrop-filter: blur(20px);
            z-index: -1;
        }
        
        /* Hero Section */
        .hero-section {
            padding: 80px 20px;
            position: relative;
        }
        .hero-title {
            font-size: 2.5rem;
            font-weight: 800;
            line-height: 1.2;
            text-shadow: 0 4px 20px rgba(0,0,0,0.8);
            font-style: italic;
        }
        /* Responsive Font for Quote */
        @media (max-width: 768px) {
            .hero-title {
                font-size: 1.5rem; /* Ideal size for mobile */
                line-height: 1.4;
            }
        }
        
        /* Section Header */
        .section-header h2 {
            font-size: 2rem;
            margin-bottom: 20px;
            display: inline-block;
        }
        @media (max-width: 768px) {
            .section-header h2 {
                font-size: 1.5rem; /* Reduced font size for mobile to prevent wrap */
            }
        }

        /* Grid Layout */
        .games-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 20px;
            margin-bottom: 40px;
        }
        
        @media (max-width: 1400px) { .games-grid { grid-template-columns: repeat(4, 1fr); } }
        @media (max-width: 992px) { .games-grid { grid-template-columns: repeat(3, 1fr); } }
        @media (max-width: 768px) { .games-grid { grid-template-columns: repeat(2, 1fr); } }
        
        /* Mini Card */
        .mini-card {
            /* Dark card to maintain neon aesthetic contrast */
            background: rgba(20, 20, 20, 0.85);
            color: white; /* Force white text inside cards */
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
            display: flex;
            flex-direction: column;
        }
        .mini-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            border-color: rgba(255, 255, 255, 0.3);
        }
        .mini-poster {
            width: 100%;
            aspect-ratio: 1/1;
            object-fit: cover;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .mini-info {
            padding: 12px;
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .mini-title {
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 5px;
            line-height: 1.2;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .mini-status {
            font-size: 0.75rem;
            margin-bottom: 8px;
        }
        .status-avail { color: #4cd137; }
        
        .card-bottom-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .mini-price {
            font-size: 0.85rem;
            font-weight: 700;
            color: rgba(255,255,255,0.9);
        }
        
        /* Add Card Button Style */
        .add-card-btn {
            background: rgba(46, 204, 113, 0.1);
            border: 2px dashed #2ecc71;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #2ecc71;
            font-size: 2rem;
            cursor: pointer;
            transition: 0.3s;
            min-height: 300px; /* Match typical card height */
            border-radius: 12px;
        }
        .add-card-btn:hover {
            background: rgba(46, 204, 113, 0.2);
            box-shadow: 0 0 20px rgba(46, 204, 113, 0.3);
        }
        
        .btn-add-green {
            color: #2ecc71;
            border: 1px solid #2ecc71;
            background: transparent;
            padding: 8px 20px;
            border-radius: 5px;
            transition: 0.3s;
        }
        .btn-add-green:hover {
            background: #2ecc71;
            color: white;
            box-shadow: 0 0 10px rgba(46, 204, 113, 0.5);
        }

        /* Modal Overlay */
        .game-modal-overlay {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(25px); 
            -webkit-backdrop-filter: blur(25px);
            z-index: 2000;
            display: none;
            justify-content: center;
            align-items: center;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .game-modal-overlay.active {
            display: flex;
            opacity: 1;
        }
        .modal-card {
            background: rgba(20, 20, 20, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 20px;
            width: 90%;
            max-width: 1000px;
            max-height: 90vh;
            display: flex;
            flex-direction: row; 
            overflow: hidden;
            box-shadow: 0 25px 50px rgba(0,0,0,0.5);
            position: relative;
        }
        @media (max-width: 992px) {
            .modal-card { flex-direction: column; overflow-y: auto; }
        }
        
        .modal-poster-container {
            width: 40%;
            position: relative;
            background: black;
        }
        @media (max-width: 992px) { .modal-poster-container { width: 100%; height: 300px; } }
        
        .modal-poster {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .modal-info {
            width: 60%;
            padding: 40px;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }
        @media (max-width: 992px) { .modal-info { width: 100%; padding: 25px; } }

        .modal-title {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 20px;
            text-shadow: 0 0 10px rgba(0,0,0,0.5);
            color: #FFFFFF !important;
        }
        .modal-desc {
            font-size: 1rem;
            line-height: 1.7;
            color: rgba(255,255,255,0.85);
            font-weight: 300;
            margin-bottom: 30px;
        }
        .modal-desc p { margin-bottom: 15px; }
        
        .modal-price {
            font-size: 2rem;
            font-weight: 700;
            color: #4cd137;
            margin-top: auto;
            text-align: right;
        }
        
        .close-modal-btn {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(0,0,0,0.5);
            border: none;
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            font-size: 1.2rem;
            cursor: pointer;
            transition: 0.2s;
            z-index: 10;
        }
        .close-modal-btn:hover { background: rgba(255,255,255,0.2); }
        
        .upload-btn-modal {
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: 0.2s;
        }
        .upload-btn-modal:hover { background: var(--brand-color); }

        /* Footer Styling */
        footer.acrylic-footer {
            margin-top: 80px; 
            color: rgba(255,255,255,0.6);
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            padding: 40px 0;
            text-align: center;
        }
        .footer-logo {
            font-weight: 800;
            font-size: 1.5rem;
            color: white;
            margin-bottom: 10px;
        }
        .footer-logo span {
            color: #FFD700;
            text-shadow: 0 0 5px #FFD700, 0 0 10px #FFD700, 0 0 20px #FFD700;
            font-style: italic;
            font-family: 'Inter', sans-serif;
        }
        .social-icons {
            margin-top: 20px;
            display: flex;
            justify-content: center;
            gap: 20px;
        }
        .social-icon {
            color: rgba(255,255,255,0.6);
            font-size: 1.5rem;
            transition: 0.3s;
            cursor: pointer;
        }
        .social-icon:hover { color: white; transform: scale(1.1); text-shadow: 0 0 10px white; }

        /* Editable Styles */
        [contenteditable="true"] {
            outline: 1px dashed rgba(255, 255, 255, 0.2);
            transition: outline 0.2s;
            min-width: 50px;
            display: inline-block;
        }
        [contenteditable="true"]:focus {
            outline: 1px solid #FFD700;
            background: rgba(255, 215, 0, 0.1);
        }
        
        /* Language Toggle Classes */
        .lang-id, .lang-en { display: none; }
        body.lang-mode-id div.lang-id, body.lang-mode-id span.lang-id, body.lang-mode-id h1.lang-id { display: block; }
        body.lang-mode-id span.lang-id { display: inline; }
        body.lang-mode-en div.lang-en, body.lang-mode-en span.lang-en, body.lang-mode-en h1.lang-en { display: block; }
        body.lang-mode-en span.lang-en { display: inline; }
    </style>
</head>
<body class="lang-mode-id">
    <div class="acrylic-overlay-page"></div>
    
    {{ navbar|safe }}

    <div class="container container-xl py-5">
        
        <!-- HERO SECTION -->
        <div class="hero-section text-center mb-5">
            <h1 class="hero-title lang-id">"Sepak bola adalah permainan tentang kesalahan. Tim yang paling sedikit membuat kesalahan akan jadi pemenang" – Johan Cruyff</h1>
            <h1 class="hero-title lang-en">"Football is a game of mistakes. Whoever makes the fewest mistakes wins" – Johan Cruyff</h1>
            
            <button class="btn btn-cyan-neon mt-4 px-5 py-2 rounded-pill" onclick="scrollToPopular()">
                <span class="lang-id">Lihat Agenda Kami</span>
                <span class="lang-en">View Our Agenda</span>
            </button>
        </div>

        <!-- SECTION 1: AGENDA LATIHAN -->
        <div class="section-header mb-4" id="popular-games">
            <h2 class="fw-bold">
                <span class="lang-id">Agenda Latihan <span class="text-blue-neon" style="border-bottom: 3px solid #FFD700;">TAHKIL FC</span></span>
                <span class="lang-en">Training Agenda <span class="text-blue-neon" style="border-bottom: 3px solid #FFD700;">TAHKIL FC</span></span>
            </h2>
        </div>

        <div class="games-grid" id="grid-agenda-latihan">
            {% for item in agenda1 %}
            <div class="mini-card" onclick="openModal('{{ item.id }}')">
                {% if game_images[item.id] %}
                    <img src="/uploads/{{ game_images[item.id] }}" class="mini-poster" alt="Agenda">
                {% else %}
                    <!-- Empty/Placeholder as requested -->
                    <div class="mini-poster" style="background: #1e1e1e; display:flex; align-items:center; justify-content:center; color:rgba(255,255,255,0.1); font-size:2rem;">
                         <i class="fas fa-camera"></i>
                    </div>
                {% endif %}
                <div class="mini-info">
                    <div class="mini-title" id="title-{{ item.id }}" contenteditable="true" onclick="event.stopPropagation()" oninput="saveText(this, '{{ item.id }}_title')">{{ item.title }}</div>
                    <div class="mini-status">
                        <span class="status-avail" id="status-{{ item.id }}" contenteditable="true" onclick="event.stopPropagation()" oninput="saveText(this, '{{ item.id }}_status')"><i class="fas fa-check-circle me-1"></i> {{ item.status_text }}</span>
                    </div>
                    <div class="card-bottom-row">
                        <div class="mini-price" id="price-{{ item.id }}" contenteditable="true" onclick="event.stopPropagation()" oninput="saveText(this, '{{ item.id }}_price')">{{ item.price }}</div>
                    </div>
                </div>
            </div>
            {% endfor %}
            <!-- JS will append dynamic cards here -->
        </div>
        
        <!-- Add Card Button for Section 1 -->
        <div class="d-flex justify-content-end mb-5">
            <button class="btn btn-add-green" onclick="addCard('grid-agenda-latihan', 'agenda1_dynamic')">+ Tambah Card Agenda</button>
        </div>
        
        <!-- SECTION 2: NEXT AGENDA -->
        <div class="section-header mt-5 mb-4" id="next-agenda">
            <h2 class="fw-bold">
                <span class="lang-id">Next <span class="text-blue-neon" style="border-bottom: 3px solid #FFD700;">Agenda</span></span>
                <span class="lang-en">Next <span class="text-blue-neon" style="border-bottom: 3px solid #FFD700;">Agenda</span></span>
            </h2>
        </div>
        <div class="games-grid" id="grid-next-agenda">
            {% for item in agenda2 %}
             <div class="mini-card" onclick="openModal('{{ item.id }}')">
                {% if game_images[item.id] %}
                    <img src="/uploads/{{ game_images[item.id] }}" class="mini-poster" alt="Agenda">
                {% else %}
                    <div class="mini-poster" style="background: #1e1e1e; display:flex; align-items:center; justify-content:center; color:rgba(255,255,255,0.1); font-size:2rem;">
                         <i class="fas fa-camera"></i>
                    </div>
                {% endif %}
                <div class="mini-info">
                    <div class="mini-title" id="title-{{ item.id }}" contenteditable="true" onclick="event.stopPropagation()" oninput="saveText(this, '{{ item.id }}_title')">{{ item.title }}</div>
                    <div class="mini-status">
                        <span class="status-avail" id="status-{{ item.id }}" contenteditable="true" onclick="event.stopPropagation()" oninput="saveText(this, '{{ item.id }}_status')"><i class="fas fa-check-circle me-1"></i> {{ item.status_text }}</span>
                    </div>
                    <div class="card-bottom-row">
                        <div class="mini-price" id="price-{{ item.id }}" contenteditable="true" onclick="event.stopPropagation()" oninput="saveText(this, '{{ item.id }}_price')">{{ item.price }}</div>
                    </div>
                </div>
            </div>
            {% endfor %}
            <!-- JS will append dynamic cards here -->
        </div>
        
        <!-- Add Card Button for Section 2 -->
        <div class="d-flex justify-content-end mb-5">
            <button class="btn btn-add-green" onclick="addCard('grid-next-agenda', 'agenda2_dynamic')">+ Tambah Card Agenda</button>
        </div>

        <footer class="acrylic-footer" id="footer-social">
            <div class="container">
                <div class="footer-logo">TAHFIZH <span>KILAT FC</span></div>
                <p>&copy; 2026 TAHKIL FC. All rights reserved.</p>
                <div class="social-icons">
                    <!-- WA: Direct to number -->
                    <a href="https://wa.me/6281528455350" target="_blank" style="text-decoration:none;"><i class="fab fa-whatsapp social-icon"></i></a>
                    
                    <!-- Maps -->
                    <a href="https://maps.app.goo.gl/uWsamfYCzcMXiq6e6" target="_blank" style="text-decoration:none;"><i class="fas fa-map-marker-alt social-icon"></i></a>
                    
                    <!-- IG -->
                    <a href="https://www.instagram.com/adihidayatofficial?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==" target="_blank" style="text-decoration:none;"><i class="fab fa-instagram social-icon"></i></a>
                </div>
            </div>
        </footer>
    </div>

    <!-- LOGO POPUP MODAL -->
    <div id="logo-modal" onclick="closeLogoModal()">
        <img src="{{ url_for('static', filename='logo-tahkil-fc.png') }}" alt="Full Logo" onclick="event.stopPropagation()">
    </div>

    <!-- DETAIL POPUP -->
    <div id="modal-overlay" class="game-modal-overlay">
        <div class="modal-card" onclick="event.stopPropagation()">
            <button class="close-modal-btn" onclick="closeModal()"><i class="fas fa-times"></i></button>
            
            <div class="modal-poster-container">
                <img id="m-poster" src="" class="modal-poster">
                <form id="m-upload-form" method="post" enctype="multipart/form-data" style="display:none">
                    <input type="file" name="game_image" id="m-file-input" onchange="this.form.submit()" accept="image/*">
                </form>
                <div class="upload-btn-modal" onclick="triggerUpload()">
                    <i class="fas fa-camera me-1"></i> Change Cover
                </div>
            </div>
            
            <div class="modal-info">
                <h2 class="modal-title" id="m-title">Title</h2>
                <div class="modal-desc">
                    <p>Masih menunggu pengembangan</p>
                </div>
                <div class="modal-price" id="m-price">Price</div>
            </div>
        </div>
    </div>

    <script>
        const gamesData = {{ games|tojson }};
        const gameImages = {{ game_images|tojson }};

        function openModal(id) {
            const game = gamesData.find(g => g.id === id);
            
            // Fetch directly from DOM to sync with user edits
            const titleEl = document.getElementById('title-' + id);
            const priceEl = document.getElementById('price-' + id);
            
            const currentTitle = titleEl ? titleEl.innerText : (localStorage.getItem(id + '_title') || game.title);
            const currentPrice = priceEl ? priceEl.innerText : (localStorage.getItem(id + '_price') || game.price);

            document.getElementById('m-title').innerText = currentTitle;
            document.getElementById('m-price').innerText = currentPrice;
            
            const imgPath = gameImages[id] ? '/uploads/' + gameImages[id] : '';
            const posterImg = document.getElementById('m-poster');
            if (imgPath) {
                posterImg.src = imgPath;
                posterImg.style.display = 'block';
            } else {
                posterImg.src = '';
                posterImg.style.background = '#1e1e1e';
            }
            
            // Setup Upload Form
            const form = document.getElementById('m-upload-form');
            form.action = '/upload-agenda-image/' + id;
            
            const overlay = document.getElementById('modal-overlay');
            overlay.classList.add('active');
            
            // Re-apply language
            toggleLanguage(true);
        }

        function closeModal() {
            const overlay = document.getElementById('modal-overlay');
            overlay.classList.remove('active');
        }

        // Logo Modal Functions
        function viewLogo() {
            const modal = document.getElementById('logo-modal');
            modal.classList.add('active');
        }
        
        function closeLogoModal() {
            const modal = document.getElementById('logo-modal');
            modal.classList.remove('active');
        }

        function scrollToPopular() {
            const el = document.getElementById('popular-games');
            if(el) {
                el.scrollIntoView({ behavior: 'smooth' });
            }
        }
        document.getElementById('modal-overlay').addEventListener('click', closeModal);

        function triggerUpload() {
            document.getElementById('m-file-input').click();
        }

        // Save editable text to localStorage
        function saveText(el, key) {
            localStorage.setItem(key, el.innerText);
        }

        // --- DYNAMIC CARD LOGIC ---
        function addCard(gridId, sectionKey) {
            // Determine section integer
            const section = (sectionKey === 'agenda1_dynamic') ? 1 : 2;
            
            fetch('/api/add-agenda-card', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ section: section })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    location.reload(); // Reload to render new card from server
                } else {
                    alert('Error adding card');
                }
            });
        }
        
        let debounceTimer;
        // Save editable text to Server (Universal Persistence)
        function saveText(el, key) {
            // Key format: "agendaID_field" e.g., "agenda1_title"
            clearTimeout(debounceTimer);
            
            const parts = key.split('_');
            const field = parts.pop(); // 'title', 'status', 'price'
            const id = parts.join('_'); // 'agenda1' or 'agenda_dynamic_123'
            
            debounceTimer = setTimeout(() => {
                const payload = { id: id };
                payload[field] = el.innerText;
                
                // Find parent card
                const card = el.closest('.mini-card');
                if(!card) return;
                
                // Extract current values from DOM
                const titleVal = card.querySelector('.mini-title').innerText;
                const statusVal = card.querySelector('.status-avail').innerText.replace(' Tersedia', '').trim(); // Remove icon text if needed, or just save raw
                const priceVal = card.querySelector('.mini-price').innerText;
                
                const fullPayload = {
                    id: id,
                    title: titleVal,
                    status: statusVal, 
                    price: priceVal
                };
                
                fetch('/api/update-agenda-text', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(fullPayload)
                });
            }, 500); // 500ms debounce
        }

        // Language Toggle Logic (Disabled/Removed as per request, keeping function stub to prevent errors if called)
        function toggleLanguage(retainState = false) {
            // No-op
        }
    </script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)
