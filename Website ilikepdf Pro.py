import io
import os
import zipfile
import math
from flask import Flask, request, send_file, render_template_string, jsonify
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter, Transformation, PageObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors

# --- KONFIGURASI FLASK ---
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB Limit
app.secret_key = "supersecretkey"

# --- FRONTEND (HTML/CSS/JS) ---
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
    </style>
</head>
<body>

    <!-- NAVBAR -->
    <nav class="navbar navbar-expand-lg sticky-top">
        <div class="container">
            <a class="navbar-brand" href="/">i<span>like</span>pdf</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto align-items-center">
                    <li class="nav-item me-3">
                        <a href="#" class="nav-link fw-bold">ALL PDF TOOLS</a>
                    </li>
                    <li class="nav-item me-3">
                        <div class="btn-group" role="group">
                            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="setTheme('light')"><i class="fas fa-sun"></i></button>
                            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="setTheme('dark')"><i class="fas fa-moon"></i></button>
                        </div>
                    </li>
                    <li class="nav-item">
                        <a href="#" class="btn btn-dark">Login</a>
                    </li>
                    <li class="nav-item ms-2">
                        <a href="#" class="btn btn-brand">Sign Up</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

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
        }

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

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
