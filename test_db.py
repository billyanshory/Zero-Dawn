import sys
import importlib.util

spec = importlib.util.spec_from_file_location("app_module", "masjid-al-hijrah-64 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py")
app_module = importlib.util.module_from_spec(spec)
sys.modules["app_module"] = app_module
spec.loader.exec_module(app_module)

app_module.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
# Need to recreate engine with sqlite
from flask_sqlalchemy import SQLAlchemy
app_module.db.init_app(app_module.app)

with app_module.app.app_context():
    app_module.db.create_all()
    try:
        report = app_module.QurbanReport.query.first()
        print("Success! QurbanReport queried successfully.")

        if not report:
            report = app_module.QurbanReport()
            app_module.db.session.add(report)
            app_module.db.session.commit()
            print("Successfully created a new QurbanReport record.")

        sys.exit(0)
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)
