import importlib
app_module = importlib.import_module("masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban )")
db = app_module.db
app = app_module.app
with app.app_context():
    print(db.engine.url)
