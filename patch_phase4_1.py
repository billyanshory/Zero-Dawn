import re

with open("app.py", "r") as f:
    content = f.read()

# 1. BRANKAS_KODE
brankas_pattern = r"brankas_kode = os\.getenv\('BRANKAS_KODE', '30-10-50'\)"
brankas_replacement = """brankas_kode = os.getenv('BRANKAS_KODE')
    if not brankas_kode:
        app.logger.error("BRANKAS_KODE is not configured")
        return jsonify({'error': 'Vault is not configured'}), 503"""
content = re.sub(brankas_pattern, brankas_replacement, content)

# 2. VAPID Keys
vapid_pattern = r"VAPID_PUBLIC_KEY = os\.getenv\('VAPID_PUBLIC_KEY'\)\nVAPID_PRIVATE_KEY = os\.getenv\('VAPID_PRIVATE_KEY'\)"
vapid_replacement = """VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY')
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY')
PUSH_NOTIFICATIONS_ENABLED = bool(VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY)
if not PUSH_NOTIFICATIONS_ENABLED:
    app.logger.warning("VAPID_PUBLIC_KEY/VAPID_PRIVATE_KEY not configured. Push notifications are disabled. Generate keys: py-vapid --gen")"""
content = re.sub(vapid_pattern, vapid_replacement, content)

# We also need to find API webpush routes and add the guard.
# Let's search for `@app.route('/api/webpush/subscribe'` or similar routes.
subscribe_pattern = r"(@app\.route\('[^']*webpush[^']*', methods=\[[^\]]+\]\)\n(?:@[^\n]+\n)*def [^\(]+\([^)]*\)(?: -> [^:]+)?:)"
subscribe_replacement = r"\1\n    if not PUSH_NOTIFICATIONS_ENABLED:\n        return jsonify({'error': 'Push not configured'}), 503"
content = re.sub(subscribe_pattern, subscribe_replacement, content)

# 3. UPLOAD_FOLDER
upload_pattern = r"app\.config\['UPLOAD_FOLDER'\] = os\.path\.join\(os\.path\.abspath\(os\.path\.dirname\(__file__\)\), 'uploads'\)"
upload_replacement = """app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads'))
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    _probe_path = os.path.join(app.config['UPLOAD_FOLDER'], '.write_probe')
    with open(_probe_path, 'w') as f:
        f.write('ok')
    os.remove(_probe_path)
except OSError as e:
    raise RuntimeError(f"UPLOAD_FOLDER {app.config['UPLOAD_FOLDER']} is not writable: {e}")"""
content = re.sub(upload_pattern, upload_replacement, content)

with open("app.py", "w") as f:
    f.write(content)
