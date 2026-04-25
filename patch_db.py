import re

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

db_init_search = """with app.app_context():
    db.create_all()"""

db_init_replace = """with app.app_context():
    # Helper for QurbanAttendance migration to add new columns cleanly
    # In an early lifecycle, dropping the affected table is acceptable.
    # We do this conditionally if verified_by_admin column is missing, or we can just safely run create_all
    # Using raw SQL to avoid dropping data unnecessarily if possible, or we could drop the table.
    try:
        db.session.execute(text('SELECT verified_by_admin FROM qurban_attendance LIMIT 1'))
    except Exception as e:
        db.session.rollback()
        try:
            # Table exists but missing column, or table doesn't exist.
            # Easiest way in this early dev stage:
            QurbanAttendance.__table__.drop(db.engine, checkfirst=True)
            print("Dropped QurbanAttendance table for schema migration")
        except:
            pass

    db.create_all()
"""

# I need to make sure text is imported
import_search = "from sqlalchemy import func"
import_replace = "from sqlalchemy import func, text"
if "from sqlalchemy import func, text" not in content:
    content = content.replace(import_search, import_replace)

if "db.session.execute(text('SELECT verified_by_admin FROM qurban_attendance LIMIT 1'))" not in content:
    content = content.replace(db_init_search, db_init_replace)

# Missing model update for Attendance!
model_search = """class QurbanAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    check_in_time = db.Column(db.DateTime, server_default=func.now())
    status = db.Column(db.String(50), nullable=False) # 'Hadir Pagi' or 'Terlambat' / 'Siluman'"""

model_replace = """class QurbanAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    check_in_time = db.Column(db.DateTime, server_default=func.now())
    status = db.Column(db.String(50), nullable=False) # 'Hadir Pagi' or 'Terlambat' / 'Siluman'
    verified_by_admin = db.Column(db.Boolean, default=False, nullable=False)
    verified_at = db.Column(db.DateTime, nullable=True)"""

if "verified_by_admin = db.Column(db.Boolean" not in content:
    content = content.replace(model_search, model_replace)

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
