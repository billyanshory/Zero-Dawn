from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
CONFIG_FILE = 'bg_config.txt'
DEFAULT_BG = 'resident-evil-2 remake-main-wallpaper.jpg'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure uploads directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Helper to get current background
def get_current_bg():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_BG
    with open(CONFIG_FILE, 'r') as f:
        return f.read().strip()

# Helper to set current background
def set_current_bg(filename):
    with open(CONFIG_FILE, 'w') as f:
        f.write(filename)

@app.route('/')
def index():
    current_bg = get_current_bg()
    return render_template('index.html', bg_image=current_bg)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        set_current_bg(filename)
        return redirect(url_for('index'))

if __name__ == '__main__':
    # Initialize default BG if not present in config
    if not os.path.exists(CONFIG_FILE):
        set_current_bg(DEFAULT_BG)
    app.run(host='0.0.0.0', port=5000)
