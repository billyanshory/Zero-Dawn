import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, FileField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

# --- Configuration & Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sangat-rahasia-dan-sulit-ditebak-hacker-kelas-dunia-88' # Change this in production!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rt53_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Security & Extensions
db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# --- Hardcoded Admin Credentials (Hashed for "Impenetrable" comparison) ---
# ID: 'Ketua RT. 53'
# Password: 'NKRIhargamati'
ADMIN_ID = 'Ketua RT. 53'
ADMIN_PASS_HASH = generate_password_hash('NKRIhargamati')

# --- Database Models ---
class FamilyCardData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nomor_kk = db.Column(db.String(50), nullable=False)
    kepala_keluarga = db.Column(db.String(100), nullable=False)
    alamat = db.Column(db.String(200), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FamilyCardImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

# --- Forms ---
class LoginForm(FlaskForm):
    username = StringField('Username')
    password = PasswordField('Password')

class UploadForm(FlaskForm):
    photo = FileField('Foto KK', validators=[DataRequired()])

class DataForm(FlaskForm):
    nomor_kk = StringField('Nomor KK', validators=[DataRequired()])
    kepala_keluarga = StringField('Kepala Keluarga', validators=[DataRequired()])
    alamat = StringField('Alamat', validators=[DataRequired()])

# --- Helper Functions ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def is_admin():
    return session.get('is_admin', False)

def login_required_admin(f):
    """Decorator to require admin rights"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            flash('Akses ditolak! Anda bukan Ketua RT.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---

@app.route('/')
def index():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        role = request.form.get('role')

        if role == 'warga':
            session['logged_in'] = True
            session['is_admin'] = False
            flash('Masuk sebagai Warga. Akses hanya lihat.', 'success')
            return redirect(url_for('dashboard'))

        elif role == 'admin':
            # Verify CSRF is handled by form.validate_on_submit() or manual check if form used
            if form.validate_on_submit():
                user = form.username.data
                pwd = form.password.data

                if user == ADMIN_ID and check_password_hash(ADMIN_PASS_HASH, pwd):
                    session['logged_in'] = True
                    session['is_admin'] = True
                    flash('Login berhasil! Selamat datang Pak RT.', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('ID atau Password salah!', 'error')
            else:
                flash('Data tidak valid.', 'error')

        else:
            flash('Pilih role terlebih dahulu.', 'error')

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah keluar.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/gallery', methods=['GET', 'POST'])
def gallery():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    form = UploadForm()

    # Handle Upload (Admin Only)
    if is_admin() and form.validate_on_submit():
        file = form.photo.data
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Make unique to prevent overwrite
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_filename = f"{timestamp}_{filename}"

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))

            new_img = FamilyCardImage(filename=unique_filename)
            db.session.add(new_img)
            db.session.commit()
            flash('Foto berhasil diunggah!', 'success')
            return redirect(url_for('gallery'))
        else:
            flash('Format file tidak diizinkan.', 'error')

    images = FamilyCardImage.query.order_by(FamilyCardImage.upload_date.desc()).all()
    return render_template('gallery.html', images=images, form=form, is_admin=is_admin())

@app.route('/gallery/delete/<int:image_id>', methods=['POST'])
@login_required_admin
def delete_image(image_id):
    img = FamilyCardImage.query.get_or_404(image_id)
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img.filename))
    except FileNotFoundError:
        pass # File already gone

    db.session.delete(img)
    db.session.commit()
    flash('Foto dihapus.', 'success')
    return redirect(url_for('gallery'))

@app.route('/data', methods=['GET'])
def data_table():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    edit_id = request.args.get('edit_id')
    edit_data = None
    if edit_id and is_admin():
        edit_data = FamilyCardData.query.get(edit_id)

    data = FamilyCardData.query.order_by(FamilyCardData.updated_at.desc()).all()
    form = DataForm() # Empty form for CSRF token generation in template

    return render_template('table.html', data=data, form=form, edit_data=edit_data, is_admin=is_admin())

@app.route('/data/save', methods=['POST'])
@login_required_admin
def save_data():
    form = DataForm()
    if form.validate_on_submit():
        data_id = request.form.get('data_id')

        if data_id: # Edit
            entry = FamilyCardData.query.get(data_id)
            if entry:
                entry.nomor_kk = form.nomor_kk.data
                entry.kepala_keluarga = form.kepala_keluarga.data
                entry.alamat = form.alamat.data
                flash('Data diperbarui.', 'success')
        else: # Add
            new_entry = FamilyCardData(
                nomor_kk = form.nomor_kk.data,
                kepala_keluarga = form.kepala_keluarga.data,
                alamat = form.alamat.data
            )
            db.session.add(new_entry)
            flash('Data ditambahkan.', 'success')

        db.session.commit()
    else:
        flash('Input tidak valid.', 'error')

    return redirect(url_for('data_table'))

@app.route('/data/delete/<int:data_id>', methods=['POST'])
@login_required_admin
def delete_data(data_id):
    entry = FamilyCardData.query.get_or_404(data_id)
    db.session.delete(entry)
    db.session.commit()
    flash('Data dihapus.', 'success')
    return redirect(url_for('data_table'))

# --- Security Headers ---
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# --- Init DB ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
