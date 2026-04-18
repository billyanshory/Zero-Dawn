import re

with open('slb.py', 'r') as f:
    content = f.read()

# Fix RuntimeError: Working outside of application context in db.session.remove()
old_shutdown_db = """    try:
        db.session.remove()
        db.engine.dispose()
        app.logger.info("Database connections drained.")
    except Exception as e:
        app.logger.error("Error draining database connections", exc_info=True)"""

new_shutdown_db = """    try:
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        app.logger.info("Database connections drained.")
    except Exception as e:
        app.logger.error("Error draining database connections", exc_info=True)"""

if old_shutdown_db in content:
    content = content.replace(old_shutdown_db, new_shutdown_db)


with open('slb.py', 'w') as f:
    f.write(content)
