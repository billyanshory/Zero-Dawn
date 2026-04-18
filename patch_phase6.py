import re

with open('slb.py', 'r') as f:
    content = f.read()

# Import block
if 'from flask_migrate import Migrate, upgrade as alembic_upgrade' not in content:
    content = re.sub(
        r'(from flask_sqlalchemy import SQLAlchemy)',
        r'\1\nfrom flask_migrate import Migrate, upgrade as alembic_upgrade',
        content,
        count=1
    )

# Instantiate Migrate
if 'migrate = Migrate(' not in content:
    content = re.sub(
        r'(db = SQLAlchemy\(app\))',
        r"\1\nmigrate = Migrate(app, db, directory='migrations', compare_type=True)",
        content,
        count=1
    )

# Replace FLASK_INIT_DB block
old_init_db = """        # TODO: Migrate to Flask-Migrate/Alembic for schema management. db.create_all() only creates new tables; it does NOT alter existing ones. (see consolidated migration note above class Siswa)
        if os.environ.get('FLASK_INIT_DB'):
            db.create_all()
            seed_slb_data()"""

new_init_db = """        # SCHEMA EVOLUTION:
        # Operator workflow:
        # 1. flask db init
        # 2. flask db migrate -m 'description'
        # 3. flask db upgrade
        _init_db = os.environ.get('FLASK_INIT_DB')
        _auto_upgrade = os.environ.get('FLASK_AUTO_UPGRADE')
        _is_dev = os.environ.get('FLASK_ENV', 'production').lower() == 'development'

        if _init_db and _is_dev:
            app.logger.info("Dev-only bootstrap: Creating tables and seeding data.")
            db.create_all()
            seed_slb_data()

        if _auto_upgrade == "1":
            try:
                alembic_upgrade()
                app.logger.info("Alembic migrations applied")
            except Exception as e:
                app.logger.error("Alembic upgrade failed", exc_info=True)
                raise"""

if old_init_db in content:
    content = content.replace(old_init_db, new_init_db)


with open('slb.py', 'w') as f:
    f.write(content)
