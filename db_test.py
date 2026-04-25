from importlib import import_module
import sqlite3

app_module = import_module("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban )")

with app_module.app.app_context():
    app_module.db.session.execute(app_module.db.text("DROP TABLE IF EXISTS qurban_attendance"))
    app_module.db.session.commit()
    app_module.db.create_all()

    # Verify
    result = app_module.db.session.execute(app_module.db.text("PRAGMA table_info(qurban_attendance)"))
    columns = [row[1] for row in result.fetchall()]
    print("Columns:", columns)
