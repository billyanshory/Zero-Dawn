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
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff', 'ico', 'svg'}

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
    <nav class="navbar navbar-expand-lg sticky-top">
        <div class="container">
            <a class="navbar-brand" href="/">i<span>like</span>pdf</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item"><a class="nav-link fw-bold" href="/">PDF Tools</a></li>
                    <li class="nav-item"><a class="nav-link fw-bold" href="/bank-gambar">Bank Gambar</a></li>
                    <li class="nav-item"><a class="nav-link fw-bold" href="/data-tabulasi">Data Tabulasi</a></li>
                    <li class="nav-item"><a class="nav-link fw-bold" href="/wallpaper-blur">Wallpaper Blur Akrilik</a></li>
                </ul>
                <ul class="navbar-nav ms-auto align-items-center">
                    <li class="nav-item me-3">
                        <div class="btn-group" role="group">
                            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="setTheme('light')"><i class="fas fa-sun"></i></button>
                            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="setTheme('dark')"><i class="fas fa-moon"></i></button>
                        </div>
                    </li>
                    {% if session.get('logged_in') %}
                        <li class="nav-item">
                            <span class="badge bg-secondary me-2">{{ session.get('role', 'Guest') }}</span>
                        </li>
                        <li class="nav-item">
                            <a href="/logout" class="btn btn-dark">Logout</a>
                        </li>
                    {% else %}
                        <li class="nav-item">
                            <a href="#" class="btn btn-dark">Login</a>
                        </li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>
"""

LOGIN_OVERLAY = """
{% if not session.get('logged_in') %}
<style>
    .login-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        z-index: 10000;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    [data-bs-theme="dark"] .login-overlay {
        background: rgba(0, 0, 0, 0.4);
    }
    .login-card {
        background: var(--card-bg);
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        width: 100%;
        max-width: 400px;
        text-align: center;
        border: 1px solid rgba(0,0,0,0.1);
    }
</style>
<div class="login-overlay">
    <div class="login-card">
        <h2 class="mb-4 fw-bold">Login Access</h2>

        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="alert alert-danger mb-3" role="alert">
                {{ message }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <form action="/login" method="post" class="mb-4 text-start">
            <div class="mb-3">
                <label class="form-label">ID Pengguna</label>
                <input type="text" name="username" class="form-control" placeholder="Ketua RT. 53">
            </div>
            <div class="mb-3">
                <label class="form-label">Password</label>
                <input type="password" name="password" class="form-control" placeholder="••••••••">
            </div>
            <button type="submit" class="btn btn-brand w-100 py-2 fw-bold">Login sebagai Admin</button>
        </form>

        <div class="border-top pt-3">
            <p class="text-muted small mb-2">Hanya ingin melihat-lihat?</p>
            <form action="/login" method="post">
                <input type="hidden" name="role" value="guest">
                <button type="submit" class="btn btn-outline-secondary w-100">Login sebagai Warga</button>
            </form>
        </div>
    </div>
</div>
{% endif %}
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
            color: var(--text-dark);
            letter-spacing: -1px;
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

# Updated HTML_TEMPLATE with new Navbar and Styles
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ilikepdf | Online PDF Tools for PDF Lovers</title>
    <!-- Bootstrap 5 & FontAwesome -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

    {{ styles|safe }}
</head>
<body>

    {{ overlay|safe }}
    {{ navbar|safe }}

    <!-- HERO -->
    <div class="hero">
        <h1>Every tool you need to work with PDFs in one place</h1>
        <p>Every tool you need to use PDFs, at your fingertips. All are 100% FREE and easy to use! Merge, split, compress, convert, rotate, unlock and watermark PDFs with just a few clicks.</p>
    </div>

    <!-- TOOLS GRID -->
    <div class="tools-grid" id="toolsContainer">
        <!-- Tools will be injected by JS -->
    </div>

    <!-- UPLOAD MODAL -->
    <div class="modal fade" id="toolModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-xl modal-dialog-centered">
            <div class="modal-content shadow-lg">
                <div class="modal-header border-0">
                    <h5 class="modal-title fw-bold" id="modalTitle">Tool Name</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body p-5">

                    <!-- Upload State -->
                    <div id="uploadState">
                        <div class="upload-zone" onclick="document.getElementById('fileInput').click()">
                            <i class="fas fa-cloud-upload-alt fa-4x mb-3" style="color: var(--brand-color)"></i>
                            <h3>Select PDF files</h3>
                            <p class="text-muted">or drop PDFs here</p>
                            <input type="file" id="fileInput" hidden multiple onchange="handleFiles(this.files)">
                        </div>
                    </div>

                    <!-- Process State -->
                    <div id="processState" style="display:none; text-align: center;">
                        <h4 class="mb-3 text-success"><i class="fas fa-check-circle"></i> Files Selected</h4>
                        <div id="fileList" class="mb-4 text-muted small"></div>

                        <!-- Dynamic Options (Rotation, Pages, etc) -->
                        <div id="optionsPanel" class="options-panel">
                            <!-- Injected via JS based on tool -->
                        </div>

                        <button onclick="processAction()" class="btn btn-brand btn-lg px-5 py-3 mt-3">
                            <span id="actionBtnText">MERGE PDF</span> <i class="fas fa-arrow-right ms-2"></i>
                        </button>
                    </div>

                    <!-- Loading State -->
                    <div id="loadingState" style="display:none; text-align: center; padding: 40px;">
                        <div class="spinner-border text-danger" style="width: 4rem; height: 4rem;" role="status"></div>
                        <h4 class="mt-4">Processing your PDF...</h4>
                        <p class="text-muted">Please wait a moment.</p>
                    </div>

                </div>
            </div>
        </div>
    </div>

    <footer>
        <div class="container">
            <p>&copy; 2025 ilikepdf - Python 3.13.5 Powered. "iLovePDF Clone"</p>
        </div>
    </footer>

    <!-- LOGIC JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // --- DATA TOOLS CONFIGURATION ---
        const tools = [
            { id: 'merge', title: 'Merge PDF', icon: 'fa-object-group', desc: 'Combine PDFs in the order you want.', accept: '.pdf', multiple: true },
            { id: 'split', title: 'Split PDF', icon: 'fa-cut', desc: 'Separate one page or a whole set for easy conversion.', accept: '.pdf', multiple: false },
            { id: 'compress', title: 'Compress PDF', icon: 'fa-compress-arrows-alt', desc: 'Reduce file size while optimizing for maximal PDF quality.', accept: '.pdf', multiple: false },
            { id: 'pdf_to_jpg', title: 'PDF to JPG', icon: 'fa-image', desc: 'Convert each PDF page into a JPG or extract all images.', accept: '.pdf', multiple: false },
            { id: 'jpg_to_pdf', title: 'JPG to PDF', icon: 'fa-file-image', desc: 'Convert JPG images to PDF in seconds.', accept: '.jpg,.jpeg,.png', multiple: true },
            { id: 'word_to_pdf', title: 'Word to PDF', icon: 'fa-file-word', desc: 'Convert DOC and DOCX files to PDF.', accept: '.doc,.docx', multiple: false },
            { id: 'pdf_to_word', title: 'PDF to Word', icon: 'fa-file-word', desc: 'Convert your PDF to WORD documents.', accept: '.pdf', multiple: false },
            { id: 'excel_to_pdf', title: 'Excel to PDF', icon: 'fa-file-excel', desc: 'Convert Excel files to PDF.', accept: '.xlsx,.xls', multiple: false },
            { id: 'pdf_to_excel', title: 'PDF to Excel', icon: 'fa-file-excel', desc: 'Convert PDF to Excel spreadsheets.', accept: '.pdf', multiple: false },
            { id: 'ppt_to_pdf', title: 'PowerPoint to PDF', icon: 'fa-file-powerpoint', desc: 'Convert PPT files to PDF.', accept: '.ppt,.pptx', multiple: false },
            { id: 'pdf_to_ppt', title: 'PDF to PowerPoint', icon: 'fa-file-powerpoint', desc: 'Convert PDF to PowerPoint.', accept: '.pdf', multiple: false },
            { id: 'rotate', title: 'Rotate PDF', icon: 'fa-sync-alt', desc: 'Rotate your PDF pages.', accept: '.pdf', multiple: false },
            { id: 'page_numbers', title: 'Page Numbers', icon: 'fa-list-ol', desc: 'Add page numbers into PDFs.', accept: '.pdf', multiple: false },
            { id: 'watermark', title: 'Add Watermark', icon: 'fa-stamp', desc: 'Stamp an image or text over your PDF.', accept: '.pdf', multiple: false },
            { id: 'remove_pages', title: 'Remove Pages', icon: 'fa-trash-alt', desc: 'Select pages to remove from your PDF.', accept: '.pdf', multiple: false },
            { id: 'organize', title: 'Organize PDF', icon: 'fa-sort-amount-down', desc: 'Sort pages of your PDF file.', accept: '.pdf', multiple: false },
        ];

        let currentTool = null;
        const modal = new bootstrap.Modal(document.getElementById('toolModal'));

        // --- RENDER GRID ---
        const container = document.getElementById('toolsContainer');
        tools.forEach(tool => {
            const card = document.createElement('a');
            card.className = 'tool-card';
            card.href = '#';
            card.onclick = () => openTool(tool);
            card.innerHTML = `
                <div class="tool-icon"><i class="fas ${tool.icon}"></i></div>
                <div class="tool-title">${tool.title}</div>
                <div class="tool-desc">${tool.desc}</div>
            `;
            container.appendChild(card);
        });

        // --- THEME LOGIC ---
        function setTheme(theme) {
            document.documentElement.setAttribute('data-bs-theme', theme);
            localStorage.setItem('theme', theme);
            updateTableTheme(theme);
        }

        function updateTableTheme(theme) {
            const tables = document.querySelectorAll('.table');
            tables.forEach(table => {
                const thead = table.querySelector('thead');
                if (theme === 'dark') {
                    if (thead) {
                        thead.classList.remove('table-light');
                        thead.classList.add('table-dark');
                    }
                    table.classList.add('table-dark');
                } else {
                    if (thead) {
                        thead.classList.remove('table-dark');
                        thead.classList.add('table-light');
                    }
                    table.classList.remove('table-dark');
                }
            });
        }

        // Apply theme on load
        (function() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-bs-theme', savedTheme);
            document.addEventListener('DOMContentLoaded', () => {
                updateTableTheme(savedTheme);
            });
        })();

        // --- TOOL LOGIC ---
        function openTool(tool) {
            currentTool = tool;
            document.getElementById('modalTitle').innerText = tool.title;
            document.getElementById('actionBtnText').innerText = tool.title.toUpperCase();

            // Reset UI
            document.getElementById('uploadState').style.display = 'block';
            document.getElementById('processState').style.display = 'none';
            document.getElementById('loadingState').style.display = 'none';
            document.getElementById('optionsPanel').style.display = 'none';

            const input = document.getElementById('fileInput');
            input.value = '';
            input.accept = tool.accept;
            input.multiple = tool.multiple;

            modal.show();
        }

        function handleFiles(files) {
            if (files.length === 0) return;

            document.getElementById('uploadState').style.display = 'none';
            document.getElementById('processState').style.display = 'block';

            const list = document.getElementById('fileList');
            list.innerHTML = Array.from(files).map(f => `<div>${f.name} (${(f.size/1024).toFixed(1)} KB)</div>`).join('');

            // Inject Tool Specific Options
            const panel = document.getElementById('optionsPanel');
            panel.innerHTML = '';
            panel.style.display = 'none';

            if (currentTool.id === 'rotate') {
                panel.style.display = 'block';
                panel.innerHTML = `
                    <label>Rotation Angle:</label>
                    <select id="extraOption" class="form-select">
                        <option value="90">90 Degrees Clockwise</option>
                        <option value="180">180 Degrees</option>
                        <option value="270">270 Degrees Clockwise</option>
                    </select>`;
            } else if (currentTool.id === 'watermark') {
                panel.style.display = 'block';
                panel.innerHTML = `
                    <label>Watermark Text:</label>
                    <input type="text" id="extraOption" class="form-control" value="CONFIDENTIAL">`;
            } else if (currentTool.id === 'remove_pages') {
                panel.style.display = 'block';
                panel.innerHTML = `
                    <label>Pages to Remove (e.g., 1,3-5):</label>
                    <input type="text" id="extraOption" class="form-control" placeholder="1">`;
            }
        }

        async function processAction() {
            document.getElementById('processState').style.display = 'none';
            document.getElementById('loadingState').style.display = 'block';

            const formData = new FormData();
            formData.append('tool_id', currentTool.id);

            const files = document.getElementById('fileInput').files;
            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i]);
            }

            // Append extra option if exists
            const extra = document.getElementById('extraOption');
            if (extra) formData.append('option', extra.value);

            try {
                const response = await fetch('/process', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;

                    // Filename handling
                    let filename = "ilikepdf_result";
                    const disp = response.headers.get('Content-Disposition');
                    if (disp && disp.includes('filename=')) {
                        filename = disp.split('filename=')[1].replace(/"/g, '');
                    } else {
                        if (currentTool.id.includes('to_jpg') || currentTool.id === 'split') filename += ".zip";
                        else filename += ".pdf";
                    }

                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    modal.hide();
                } else {
                    const err = await response.text();
                    alert("Error: " + err);
                    modal.hide();
                }
            } catch (e) {
                alert("An error occurred: " + e);
                modal.hide();
            }
        }
    </script>
</body>
</html>
"""

HTML_BANK = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bank Gambar | ilikepdf</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    {{ styles|safe }}
    <style>
        .image-container {
            position: relative;
            border-radius: 8px;
            overflow: hidden;
            height: 200px;
            width: 100%;
        }
        .image-card {
            height: 100%;
            width: 100%;
            object-fit: cover;
            transition: 0.3s;
        }
        .image-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(8px); /* Acrylic Blur */
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .image-container:hover .image-overlay {
            opacity: 1;
        }
        .image-title {
            color: white;
            font-weight: 600;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
            margin-bottom: 10px;
            text-align: center;
            padding: 0 10px;
        }
        .gallery-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            padding: 20px 0;
        }
    </style>
</head>
<body>
    {{ overlay|safe }}
    {{ navbar|safe }}

    <div class="hero">
        <h1>Bank Gambar</h1>
        <p>Upload and manage your images. Supported formats: JPG, PNG, GIF, BMP, WEBP, TIFF, ICO, SVG.</p>
    </div>

    <div class="container container-xl">
        {% if session.get('role') == 'admin' %}
        <div class="card p-4 mb-4 border-0 shadow-sm">
            <h5>Upload Image (Multiple Supported)</h5>
            <form action="/bank-gambar" method="post" enctype="multipart/form-data" class="d-flex gap-2">
                <input type="file" name="file" class="form-control" multiple required>
                <button type="submit" class="btn btn-brand">Upload</button>
            </form>
        </div>
        {% endif %}

        <h4 class="mb-3">Gallery</h4>
        <div class="gallery-grid">
            {% for img in images %}
                <div class="image-container">
                    <img src="/uploads/{{ img }}" class="image-card" alt="{{ img }}">
                    <div class="image-overlay">
                        <div class="image-title">{{ img }}</div>
                        <div class="d-flex gap-2 justify-content-center mb-2">
                            {% if session.get('role') == 'admin' %}
                            <button class="btn btn-sm btn-light" onclick="openRename('{{ img }}')"><i class="fas fa-edit"></i> Rename</button>
                            <form action="/bank-gambar/delete" method="post" onsubmit="return confirm('Are you sure?')">
                                <input type="hidden" name="filename" value="{{ img }}">
                                <button type="submit" class="btn btn-sm btn-danger"><i class="fas fa-trash"></i></button>
                            </form>
                            {% endif %}
                        </div>
                        <a href="/uploads/{{ img }}" target="_blank" class="btn btn-sm btn-outline-light"><i class="fas fa-eye"></i> View</a>
                    </div>
                </div>
            {% endfor %}
        </div>
    </div>

    <!-- RENAME MODAL -->
    <div class="modal fade" id="renameModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Rename Image</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <form action="/bank-gambar/rename" method="post">
                    <div class="modal-body">
                        <input type="hidden" name="old_name" id="old_name">
                        <label>New Name (without extension):</label>
                        <input type="text" name="new_name" class="form-control" required placeholder="e.g. KK Udin">
                    </div>
                    <div class="modal-footer">
                        <button type="submit" class="btn btn-brand">Save Changes</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <footer>
        <div class="container">
            <p>&copy; 2025 ilikepdf - Python 3.13.5 Powered. "iLovePDF Clone"</p>
        </div>
    </footer>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function setTheme(theme) {
            document.documentElement.setAttribute('data-bs-theme', theme);
            localStorage.setItem('theme', theme);
            updateTableTheme(theme);
        }

        function updateTableTheme(theme) {
            // No tables here, but keep function for consistency or if added later
        }

        // Apply theme on load
        (function() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-bs-theme', savedTheme);
        })();

        function openRename(filename) {
            document.getElementById('old_name').value = filename;
            new bootstrap.Modal(document.getElementById('renameModal')).show();
        }
    </script>
</body>
</html>
"""

HTML_TABULASI = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Tabulasi | ilikepdf</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    {{ styles|safe }}
</head>
<body>
    {{ overlay|safe }}
    {{ navbar|safe }}

    <div class="hero">
        <h1>Data Tabulasi Tabel</h1>
        <p>Manage large tabular data efficiently.</p>
    </div>

    <div class="container container-xl">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h4>Data Table</h4>
            {% if session.get('role') == 'admin' %}
            <button class="btn btn-brand" data-bs-toggle="modal" data-bs-target="#addModal"><i class="fas fa-plus"></i> Add New</button>
            {% endif %}
        </div>

        <div class="table-responsive bg-white p-3 rounded shadow-sm">
            <table class="table table-hover align-middle">
                <thead class="table-light">
                    <tr>
                        <th>No.</th>
                        <th>Nama Lengkap</th>
                        <th>NIK</th>
                        <th>Jenis Kelamin</th>
                        <th>Tempat Lahir</th>
                        <th>Tanggal Lahir</th>
                        <th>Agama</th>
                        <th>Pendidikan</th>
                        <th>Pekerjaan</th>
                        <th>Gol. Darah</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in rows %}
                    <tr>
                        <td>{{ row[1] }}</td>
                        <td>{{ row[2] }}</td>
                        <td>{{ row[3] }}</td>
                        <td>{{ row[4] }}</td>
                        <td>{{ row[5] }}</td>
                        <td>{{ row[6] }}</td>
                        <td>{{ row[7] }}</td>
                        <td>{{ row[8] }}</td>
                        <td>{{ row[9] }}</td>
                        <td>{{ row[10] }}</td>
                        <td>
                            {% if session.get('role') == 'admin' %}
                            <button class="btn btn-sm btn-outline-primary" onclick='editRow({{ row | tojson }})'><i class="fas fa-edit"></i></button>
                            {% else %}
                            <span class="text-muted"><i class="fas fa-lock"></i></span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- ADD MODAL -->
    <div class="modal fade" id="addModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Add New Data</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <form action="/data-tabulasi" method="post">
                    <div class="modal-body">
                        <div class="row g-3">
                            <div class="col-md-2"><label class="form-label">No.</label><input type="text" name="no_urut" class="form-control" required></div>
                            <div class="col-md-5"><label class="form-label">Nama Lengkap</label><input type="text" name="nama_lengkap" class="form-control" required></div>
                            <div class="col-md-5"><label class="form-label">NIK</label><input type="text" name="nik" class="form-control" required></div>
                            <div class="col-md-4"><label class="form-label">Jenis Kelamin</label>
                                <select name="jenis_kelamin" class="form-select">
                                    <option>Laki-laki</option>
                                    <option>Perempuan</option>
                                </select>
                            </div>
                            <div class="col-md-4"><label class="form-label">Tempat Lahir</label><input type="text" name="tempat_lahir" class="form-control"></div>
                            <div class="col-md-4"><label class="form-label">Tanggal Lahir</label><input type="date" name="tanggal_lahir" class="form-control"></div>
                            <div class="col-md-4"><label class="form-label">Agama</label><input type="text" name="agama" class="form-control"></div>
                            <div class="col-md-4"><label class="form-label">Pendidikan</label><input type="text" name="pendidikan" class="form-control"></div>
                            <div class="col-md-4"><label class="form-label">Pekerjaan</label><input type="text" name="jenis_pekerjaan" class="form-control"></div>
                            <div class="col-md-4"><label class="form-label">Golongan Darah</label><input type="text" name="golongan_darah" class="form-control"></div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="submit" class="btn btn-brand">Save</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- EDIT MODAL -->
    <div class="modal fade" id="editModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Edit Data</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <form action="/data-tabulasi/edit" method="post">
                    <input type="hidden" name="id" id="edit_id">
                    <div class="modal-body">
                        <div class="row g-3">
                            <div class="col-md-2"><label class="form-label">No.</label><input type="text" name="no_urut" id="edit_no_urut" class="form-control" required></div>
                            <div class="col-md-5"><label class="form-label">Nama Lengkap</label><input type="text" name="nama_lengkap" id="edit_nama_lengkap" class="form-control" required></div>
                            <div class="col-md-5"><label class="form-label">NIK</label><input type="text" name="nik" id="edit_nik" class="form-control" required></div>
                            <div class="col-md-4"><label class="form-label">Jenis Kelamin</label>
                                <select name="jenis_kelamin" id="edit_jenis_kelamin" class="form-select">
                                    <option>Laki-laki</option>
                                    <option>Perempuan</option>
                                </select>
                            </div>
                            <div class="col-md-4"><label class="form-label">Tempat Lahir</label><input type="text" name="tempat_lahir" id="edit_tempat_lahir" class="form-control"></div>
                            <div class="col-md-4"><label class="form-label">Tanggal Lahir</label><input type="date" name="tanggal_lahir" id="edit_tanggal_lahir" class="form-control"></div>
                            <div class="col-md-4"><label class="form-label">Agama</label><input type="text" name="agama" id="edit_agama" class="form-control"></div>
                            <div class="col-md-4"><label class="form-label">Pendidikan</label><input type="text" name="pendidikan" id="edit_pendidikan" class="form-control"></div>
                            <div class="col-md-4"><label class="form-label">Pekerjaan</label><input type="text" name="jenis_pekerjaan" id="edit_jenis_pekerjaan" class="form-control"></div>
                            <div class="col-md-4"><label class="form-label">Golongan Darah</label><input type="text" name="golongan_darah" id="edit_golongan_darah" class="form-control"></div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="submit" class="btn btn-brand">Update</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <footer>
        <div class="container">
            <p>&copy; 2025 ilikepdf - Python 3.13.5 Powered. "iLovePDF Clone"</p>
        </div>
    </footer>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function setTheme(theme) {
            document.documentElement.setAttribute('data-bs-theme', theme);
            localStorage.setItem('theme', theme);
            updateTableTheme(theme);
        }

        function updateTableTheme(theme) {
            const tables = document.querySelectorAll('.table');
            tables.forEach(table => {
                const thead = table.querySelector('thead');
                if (theme === 'dark') {
                    if (thead) {
                        thead.classList.remove('table-light');
                        thead.classList.add('table-dark');
                    }
                    table.classList.add('table-dark');
                } else {
                    if (thead) {
                        thead.classList.remove('table-dark');
                        thead.classList.add('table-light');
                    }
                    table.classList.remove('table-dark');
                }
            });
        }

        // Apply theme on load
        (function() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-bs-theme', savedTheme);
            document.addEventListener('DOMContentLoaded', () => {
                updateTableTheme(savedTheme);
            });
        })();

        function editRow(data) {
            document.getElementById('edit_id').value = data[0];
            document.getElementById('edit_no_urut').value = data[1];
            document.getElementById('edit_nama_lengkap').value = data[2];
            document.getElementById('edit_nik').value = data[3];
            document.getElementById('edit_jenis_kelamin').value = data[4];
            document.getElementById('edit_tempat_lahir').value = data[5];
            document.getElementById('edit_tanggal_lahir').value = data[6];
            document.getElementById('edit_agama').value = data[7];
            document.getElementById('edit_pendidikan').value = data[8];
            document.getElementById('edit_jenis_pekerjaan').value = data[9];
            document.getElementById('edit_golongan_darah').value = data[10];

            new bootstrap.Modal(document.getElementById('editModal')).show();
        }
    </script>
</body>
</html>
"""

# --- BACKEND LOGIC (PDF ENGINE) ---

def process_merge(files):
    merger = PdfWriter()
    for f in files:
        merger.append(f)
    out = io.BytesIO()
    merger.write(out)
    out.seek(0)
    return out, "merged.pdf", "application/pdf"

def process_split(files):
    # Splits first file only
    pdf = PdfReader(files[0])
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
        for i, page in enumerate(pdf.pages):
            writer = PdfWriter()
            writer.add_page(page)
            tmp = io.BytesIO()
            writer.write(tmp)
            zf.writestr(f"page_{i+1}.pdf", tmp.getvalue())
    zip_buffer.seek(0)
    return zip_buffer, "split_pages.zip", "application/zip"

def process_compress(files):
    reader = PdfReader(files[0])
    writer = PdfWriter()
    for page in reader.pages:
        page.compress_content_streams() # Basic lossless compression
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out, "compressed.pdf", "application/pdf"

def process_jpg_to_pdf(files):
    images = []
    for f in files:
        img = Image.open(f)
        if img.mode != 'RGB': img = img.convert('RGB')
        images.append(img)
    out = io.BytesIO()
    images[0].save(out, "PDF", resolution=100.0, save_all=True, append_images=images[1:])
    out.seek(0)
    return out, "images.pdf", "application/pdf"

def process_rotate(files, angle):
    reader = PdfReader(files[0])
    writer = PdfWriter()
    angle = int(angle)
    for page in reader.pages:
        page.rotate(angle)
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out, "rotated.pdf", "application/pdf"

def process_remove_pages(files, pages_str):
    reader = PdfReader(files[0])
    writer = PdfWriter()

    # Parse pages "1,3-5" -> indices [0, 2, 3, 4]
    to_remove = set()
    try:
        parts = pages_str.split(',')
        for p in parts:
            if '-' in p:
                start, end = map(int, p.split('-'))
                for i in range(start, end + 1): to_remove.add(i - 1)
            else:
                to_remove.add(int(p) - 1)
    except:
        pass # Ignore parse errors, remove nothing

    for i, page in enumerate(reader.pages):
        if i not in to_remove:
            writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out, "removed_pages.pdf", "application/pdf"

def process_watermark(files, text):
    reader = PdfReader(files[0])
    writer = PdfWriter()

    # Create watermark PDF in memory
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica-Bold", 50)
    can.setFillColor(colors.grey, alpha=0.3)
    can.saveState()
    can.translate(300, 400)
    can.rotate(45)
    can.drawCentredString(0, 0, text)
    can.restoreState()
    can.save()
    packet.seek(0)

    watermark_pdf = PdfReader(packet)
    watermark_page = watermark_pdf.pages[0]

    for page in reader.pages:
        page.merge_page(watermark_page)
        writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out, "watermarked.pdf", "application/pdf"

def process_page_numbers(files):
    reader = PdfReader(files[0])
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        # Create number overlay
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        can.setFont("Helvetica", 10)
        can.drawString(500, 20, f"Page {i+1}") # Bottom right
        can.save()
        packet.seek(0)

        num_pdf = PdfReader(packet)
        page.merge_page(num_pdf.pages[0])
        writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out, "numbered.pdf", "application/pdf"

def process_organize(files):
    # Simply reversing order for demo
    reader = PdfReader(files[0])
    writer = PdfWriter()
    for page in reversed(reader.pages):
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out, "organized.pdf", "application/pdf"

# --- ROUTES ---

def render_page(content, **kwargs):
    # Inject fragments before rendering to allow Jinja to process them
    content = content.replace('{{ styles|safe }}', STYLES_HTML)
    content = content.replace('{{ navbar|safe }}', NAVBAR_HTML)
    content = content.replace('{{ overlay|safe }}', LOGIN_OVERLAY)
    return render_template_string(content, **kwargs)

@app.route('/login', methods=['POST'])
def login():
    role = request.form.get('role')
    if role == 'guest':
        session['logged_in'] = True
        session['role'] = 'guest'
        session.pop('login_attempts', None)
        return redirect(request.referrer or url_for('index'))

    username = request.form.get('username')
    password = request.form.get('password')

    if username == 'Ketua RT. 53' and password == 'nkrihargamati':
        session['logged_in'] = True
        session['role'] = 'admin'
        session.pop('login_attempts', None)
        return redirect(request.referrer or url_for('index'))

    # Handle failure
    attempts = session.get('login_attempts', 0) + 1
    session['login_attempts'] = attempts

    if attempts % 2 != 0:
        msg = 'lupa password, tanyakan dengan pihak pengembang'
    else:
        msg = 'anda bukan Pak RT. 53, pakai akun warga saja untuk melihat-lihat'

    flash(msg, 'error')

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_page(HTML_TEMPLATE)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/bank-gambar', methods=['GET', 'POST'])
def bank_gambar():
    if request.method == 'POST':
        if session.get('role') != 'admin':
            return "Unauthorized", 403

        if 'file' not in request.files:
            return 'No file part'

        files = request.files.getlist('file')
        for file in files:
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('bank_gambar'))

    images = os.listdir(app.config['UPLOAD_FOLDER']) if os.path.exists(app.config['UPLOAD_FOLDER']) else []
    # Filter only allowed images
    images = [img for img in images if allowed_file(img)]
    return render_page(HTML_BANK, images=images)

@app.route('/bank-gambar/delete', methods=['POST'])
def delete_image():
    if session.get('role') != 'admin':
        return "Unauthorized", 403

    filename = request.form.get('filename')
    if not filename:
        return "Missing filename", 400

    filename = secure_filename(filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    return redirect(url_for('bank_gambar'))

@app.route('/bank-gambar/rename', methods=['POST'])
def rename_image():
    if session.get('role') != 'admin':
        return "Unauthorized", 403

    old_name = request.form.get('old_name')
    new_name_base = request.form.get('new_name')

    if not old_name or not new_name_base:
        return "Missing arguments", 400

    # Security check: prevent path traversal
    old_name = secure_filename(old_name)
    new_name_base = secure_filename(new_name_base)

    # Get extension
    ext = os.path.splitext(old_name)[1]
    new_name = new_name_base + ext

    old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_name)
    new_path = os.path.join(app.config['UPLOAD_FOLDER'], new_name)

    if os.path.exists(old_path) and not os.path.exists(new_path):
        os.rename(old_path, new_path)

    return redirect(url_for('bank_gambar'))

@app.route('/data-tabulasi', methods=['GET', 'POST'])
def data_tabulasi():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()

    if request.method == 'POST':
        if session.get('role') != 'admin':
            return "Unauthorized", 403

        c.execute('''INSERT INTO tabulasi (no_urut, nama_lengkap, nik, jenis_kelamin, tempat_lahir,
                    tanggal_lahir, agama, pendidikan, jenis_pekerjaan, golongan_darah)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (request.form['no_urut'], request.form['nama_lengkap'], request.form['nik'],
                     request.form['jenis_kelamin'], request.form['tempat_lahir'], request.form['tanggal_lahir'],
                     request.form['agama'], request.form['pendidikan'], request.form['jenis_pekerjaan'],
                     request.form['golongan_darah']))
        conn.commit()
        conn.close()
        return redirect(url_for('data_tabulasi'))

    c.execute('SELECT * FROM tabulasi')
    rows = c.fetchall()
    conn.close()
    return render_page(HTML_TABULASI, rows=rows)

@app.route('/wallpaper-blur')
def wallpaper_blur():
    bg_image = "default.jpg" # Fallback
    if os.path.exists('bg_config.txt'):
        with open('bg_config.txt', 'r') as f:
            content = f.read().strip()
            if content:
                bg_image = content
    return render_page(HTML_WALLPAPER, bg_image=bg_image)

@app.route('/wallpaper-blur/upload', methods=['POST'])
def wallpaper_upload():
    if 'background' not in request.files:
        return redirect(url_for('wallpaper_blur'))

    file = request.files['background']
    if file and file.filename != '' and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        with open('bg_config.txt', 'w') as f:
            f.write(filename)

    return redirect(url_for('wallpaper_blur'))

@app.route('/data-tabulasi/edit', methods=['POST'])
def edit_tabulasi():
    if session.get('role') != 'admin':
        return "Unauthorized", 403

    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''UPDATE tabulasi SET no_urut=?, nama_lengkap=?, nik=?, jenis_kelamin=?, tempat_lahir=?,
                tanggal_lahir=?, agama=?, pendidikan=?, jenis_pekerjaan=?, golongan_darah=? WHERE id=?''',
                (request.form['no_urut'], request.form['nama_lengkap'], request.form['nik'],
                 request.form['jenis_kelamin'], request.form['tempat_lahir'], request.form['tanggal_lahir'],
                 request.form['agama'], request.form['pendidikan'], request.form['jenis_pekerjaan'],
                 request.form['golongan_darah'], request.form['id']))
    conn.commit()
    conn.close()
    return redirect(url_for('data_tabulasi'))

@app.route('/process', methods=['POST'])
def process():
    tool_id = request.form.get('tool_id')
    uploaded_files = request.files.getlist('files')
    option = request.form.get('option', '')

    if not uploaded_files or not uploaded_files[0]:
        return "No files uploaded", 400

    try:
        # --- LOGIC MAPPING ---
        if tool_id == 'merge':
            data, name, mime = process_merge(uploaded_files)
        elif tool_id == 'split':
            data, name, mime = process_split(uploaded_files)
        elif tool_id == 'compress':
            data, name, mime = process_compress(uploaded_files)
        elif tool_id == 'jpg_to_pdf':
            data, name, mime = process_jpg_to_pdf(uploaded_files)
        elif tool_id == 'rotate':
            data, name, mime = process_rotate(uploaded_files, option or 90)
        elif tool_id == 'remove_pages':
            data, name, mime = process_remove_pages(uploaded_files, option)
        elif tool_id == 'watermark':
            data, name, mime = process_watermark(uploaded_files, option or "DRAFT")
        elif tool_id == 'page_numbers':
            data, name, mime = process_page_numbers(uploaded_files)
        elif tool_id == 'organize':
            data, name, mime = process_organize(uploaded_files)

        # --- PLACEHOLDERS FOR COMPLEX CONVERSIONS ---
        # (PDF to Office requires LibreOffice/Heavy Libs not suitable for single file script)
        elif tool_id in ['pdf_to_word', 'word_to_pdf', 'excel_to_pdf', 'pdf_to_excel', 'ppt_to_pdf', 'pdf_to_ppt', 'pdf_to_jpg']:
            return "This feature requires server-side libraries (LibreOffice/Poppler) not available in this demo environment.", 501

        else:
            return "Tool logic not implemented yet", 400

        return send_file(
            data,
            as_attachment=True,
            download_name=name,
            mimetype=mime
        )

    except Exception as e:
        return f"Processing Error: {str(e)}", 500

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
        }
        .upload-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 40px;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            max-width: 500px;
            width: 90%;
        }
        /* Navbar transparency override for this page if needed, but keeping standard for consistency */
    </style>
</head>
<body>
    <div class="wallpaper-bg"></div>
    <div class="acrylic-overlay"></div>

    <div class="content-wrapper">
        {{ navbar|safe }}

        <div class="center-content">
            <div class="upload-card">
                <h2 class="fw-bold mb-4">Wallpaper Blur Akrilik</h2>
                <p class="mb-4">Upload an image to set it as the background with a modern cool acrylic blur effect.</p>

                <form action="/wallpaper-blur/upload" method="post" enctype="multipart/form-data">
                    <div class="mb-3">
                        <input type="file" name="background" class="form-control" accept="image/*" required>
                    </div>
                    <button type="submit" class="btn btn-brand w-100 fw-bold">
                        <i class="fas fa-magic me-2"></i> Set Background
                    </button>
                </form>
            </div>
        </div>

        <footer style="background: transparent; border: none; color: rgba(255,255,255,0.7);">
            <div class="container">
                <p>&copy; 2025 ilikepdf - Python 3.13.5 Powered. "iLovePDF Clone"</p>
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
