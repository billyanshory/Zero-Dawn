import re

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Fix Database Migration explicitly
db_old = """if __name__ == '__main__':
    with app.app_context():
        db.create_all()"""

db_new = """if __name__ == '__main__':
    with app.app_context():
        try:
            db.session.execute(text('SELECT verified_by_admin FROM qurban_attendance LIMIT 1'))
        except Exception as e:
            db.session.rollback()
            try:
                QurbanAttendance.__table__.drop(db.engine, checkfirst=True)
                print("Dropped QurbanAttendance table for schema migration")
            except:
                pass
        db.create_all()"""

if db_old in content:
    content = content.replace(db_old, db_new)

# Make sure we import text
import_old = "from sqlalchemy import func"
import_new = "from sqlalchemy import func, text"
if import_old in content and import_new not in content:
    content = content.replace(import_old, import_new)


with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
