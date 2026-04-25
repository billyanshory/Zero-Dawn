from importlib import import_module

app_module = import_module("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban )")

app_module.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app_module.db.init_app(app_module.app)

with app_module.app.app_context():
    app_module.db.create_all()
    # Test creation of QurbanAttendance
    att = app_module.QurbanAttendance(name="Test", status="Hadir Pagi", verified_by_admin=True)
    app_module.db.session.add(att)
    app_module.db.session.commit()
    print("Database test passed!")
