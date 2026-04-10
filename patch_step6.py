import re

with open('app.py', 'r') as f:
    content = f.read()

# Add startup check
startup_old = """if __name__ == '__main__':
    with app.app_context():
        if os.environ.get('FLASK_INIT_DB'):
            db.create_all()"""
startup_new = """if __name__ == '__main__':
    with app.app_context():
        if os.environ.get('FLASK_INIT_DB'):
            db.create_all()

        # Verify kamus_alergi_neuro.json
        kamus_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'kamus_alergi_neuro.json')
        if not os.path.exists(kamus_path):
            app.logger.warning("kamus_alergi_neuro.json is missing from the static directory!")
        else:
            try:
                import json
                with open(kamus_path, 'r', encoding='utf-8') as fk:
                    json.load(fk)
            except Exception as e:
                app.logger.warning(f"kamus_alergi_neuro.json is invalid JSON: {e}")"""
content = content.replace(startup_old, startup_new)

with open('app.py', 'w') as f:
    f.write(content)
print("Done patching.")
