with open("app.py", "r") as f:
    content = f.read()

# 1. Imports
content = content.replace("from flask_sqlalchemy import SQLAlchemy", "from flask_sqlalchemy import SQLAlchemy\nfrom flask_migrate import Migrate, upgrade as alembic_upgrade")

# 2. Initialization
init_pattern = r"db = SQLAlchemy\(app\)"
init_replacement = """db = SQLAlchemy(app)
migrate = Migrate(app, db, directory='migrations', compare_type=True)"""
content = content.replace(init_pattern, init_replacement)

# 3. Startup logic
startup_old = """        # TODO: Migrate to Flask-Migrate/Alembic for schema management. db.create_all() only creates new tables; it does NOT alter existing ones. (see consolidated migration note above class Siswa)
        if os.environ.get('FLASK_INIT_DB'):
            db.create_all()
            seed_slb_data()"""

startup_new = """        # Migration workflows:
        # 1. flask db init (once)
        # 2. flask db migrate -m 'description' (when model changes)
        # 3. flask db upgrade (to apply)
        if os.environ.get('FLASK_INIT_DB') and os.environ.get('FLASK_ENV', '').lower() == 'development':
            app.logger.info("Dev-only bootstrap: running db.create_all() and seed_slb_data()")
            db.create_all()
            seed_slb_data()

        if os.environ.get('FLASK_AUTO_UPGRADE') == '1':
            try:
                alembic_upgrade()
                app.logger.info("Alembic migrations applied")
            except Exception:
                app.logger.error("Alembic migration failed", exc_info=True)
                raise"""
content = content.replace(startup_old, startup_new)

with open("app.py", "w") as f:
    f.write(content)
