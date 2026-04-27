import re

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "r") as f:
    content = f.read()

# Update QurbanAttendance
old_model = """class QurbanAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    check_in_time = db.Column(db.DateTime, server_default=func.now())
    status = db.Column(db.String(50), nullable=False) # 'Hadir Pagi' or 'Terlambat' / 'Siluman'"""

new_model = """class QurbanAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    no_hp = db.Column(db.String(20), nullable=True)
    tugas_diinginkan = db.Column(db.String(255), nullable=True)
    pos_tugas = db.Column(db.String(255), nullable=True)
    approval_status = db.Column(db.String(50), default='Menunggu') # 'Menunggu', 'Approved', 'Rejected'
    is_present = db.Column(db.Boolean, default=False)
    session_id = db.Column(db.String(255), nullable=True)
    check_in_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), nullable=True) # 'Hadir Pagi' or 'Terlambat' / 'Siluman'"""

content = content.replace(old_model, new_model)

# Add DB setup checks in the with app.app_context(): block
old_init = """with app.app_context():
    db.create_all()"""

new_init = """with app.app_context():
    db.create_all()
    # Safely add columns to QurbanAttendance if they don't exist
    try:
        if 'mysql' in app.config['SQLALCHEMY_DATABASE_URI']:
            engine = db.engine
            with engine.connect() as conn:
                try: conn.execute(text("ALTER TABLE qurban_attendance ADD COLUMN no_hp VARCHAR(20) NULL"))
                except Exception: pass
                try: conn.execute(text("ALTER TABLE qurban_attendance ADD COLUMN tugas_diinginkan VARCHAR(255) NULL"))
                except Exception: pass
                try: conn.execute(text("ALTER TABLE qurban_attendance ADD COLUMN pos_tugas VARCHAR(255) NULL"))
                except Exception: pass
                try: conn.execute(text("ALTER TABLE qurban_attendance ADD COLUMN approval_status VARCHAR(50) DEFAULT 'Menunggu'"))
                except Exception: pass
                try: conn.execute(text("ALTER TABLE qurban_attendance ADD COLUMN is_present BOOLEAN DEFAULT 0"))
                except Exception: pass
                try: conn.execute(text("ALTER TABLE qurban_attendance ADD COLUMN session_id VARCHAR(255) NULL"))
                except Exception: pass
                try: conn.execute(text("ALTER TABLE qurban_attendance MODIFY COLUMN check_in_time DATETIME NULL"))
                except Exception: pass
                try: conn.execute(text("ALTER TABLE qurban_attendance MODIFY COLUMN status VARCHAR(50) NULL"))
                except Exception: pass
    except Exception as e:
        app.logger.error(f"Error updating QurbanAttendance table schema: {e}")"""

content = content.replace(old_init, new_init)

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "w") as f:
    f.write(content)
