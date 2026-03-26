from importlib import import_module
module = import_module("masjid-al-hijrah-60 ( idcloudhost - warna 3 tombol fitur zakat )")
app = getattr(module, 'app')
db = getattr(module, 'db')
with app.app_context():
    db.create_all()
