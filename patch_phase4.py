import re

with open('slb.py', 'r') as f:
    content = f.read()

# 1. BRANKAS_KODE
old_brankas = "    brankas_kode = os.getenv('BRANKAS_KODE', '30-10-50')"
new_brankas = """    brankas_kode = os.getenv('BRANKAS_KODE')
    if not brankas_kode:
        app.logger.error("BRANKAS_KODE is not configured")
        return jsonify({'error': 'Vault is not configured'}), 503"""

if old_brankas in content:
    content = content.replace(old_brankas, new_brankas)

# 2. PUSH_NOTIFICATIONS_ENABLED
old_vapid = """VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY')
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY')"""

new_vapid = """VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY')
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY')
PUSH_NOTIFICATIONS_ENABLED = bool(VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY)
if not PUSH_NOTIFICATIONS_ENABLED:
    app.logger.warning("VAPID_PUBLIC_KEY/VAPID_PRIVATE_KEY not configured. Push notifications are disabled. Generate keys: py-vapid --gen")"""

if old_vapid in content:
    content = content.replace(old_vapid, new_vapid)

# Patch push routes
# /api/webpush_subscribe
old_webpush_sub = """@app.route('/api/webpush_subscribe', methods=['POST'])
@csrf.exempt
def webpush_subscribe() -> Response | str | tuple[Response, int]:"""
new_webpush_sub = """@app.route('/api/webpush_subscribe', methods=['POST'])
@csrf.exempt
def webpush_subscribe() -> Response | str | tuple[Response, int]:
    if not PUSH_NOTIFICATIONS_ENABLED: return jsonify({'error': 'Push not configured'}), 503"""

if old_webpush_sub in content:
    content = content.replace(old_webpush_sub, new_webpush_sub)

# /orang-tua/api/vapid_public_key
old_vapid_pub = """@app.route('/orang-tua/api/vapid_public_key')
# INTENTIONALLY PUBLIC: VAPID public keys are inherently public by design.
def vapid_public_key() -> Response | str | tuple[Response, int]:
    \"\"\"Handles requests to the vapid_public_key endpoint.\"\"\"
    if not VAPID_PUBLIC_KEY:
        return jsonify({'error': 'Push notifications not configured'}), 503
    return jsonify({'public_key': VAPID_PUBLIC_KEY})"""

new_vapid_pub = """@app.route('/orang-tua/api/vapid_public_key')
# INTENTIONALLY PUBLIC: VAPID public keys are inherently public by design.
def vapid_public_key() -> Response | str | tuple[Response, int]:
    \"\"\"Handles requests to the vapid_public_key endpoint.\"\"\"
    if not PUSH_NOTIFICATIONS_ENABLED: return jsonify({'error': 'Push not configured'}), 503
    return jsonify({'public_key': VAPID_PUBLIC_KEY})"""

if old_vapid_pub in content:
    content = content.replace(old_vapid_pub, new_vapid_pub)


# 3. UPLOAD_FOLDER
old_upload = """app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')"""
new_upload = """app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads'))

try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    _probe_path = os.path.join(app.config['UPLOAD_FOLDER'], '.write_probe')
    with open(_probe_path, 'w') as f:
        f.write('ok')
    os.remove(_probe_path)
except OSError as e:
    raise RuntimeError(f"UPLOAD_FOLDER {app.config['UPLOAD_FOLDER']} is not writable: {e}")"""

if old_upload in content:
    content = content.replace(old_upload, new_upload)

# Also remove the isolated os.makedirs down below
content = re.sub(r'os\.makedirs\(app\.config\[\'UPLOAD_FOLDER\'\], exist_ok=True\)\n', '', content)


# 4. Connection Pool Size
old_db_options = """app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 3600,
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 30,
    'pool_pre_ping': True,
    'connect_args': {'options': '-c statement_timeout=30000'} if 'sqlite' not in os.environ.get('SQLALCHEMY_DATABASE_URI', '') else {},
}"""

new_db_options = """_web_concurrency = int(os.getenv('WEB_CONCURRENCY', '1'))
_db_max_connections = int(os.getenv('DB_MAX_CONNECTIONS', '80'))
_pool_size = max(2, _db_max_connections // max(1, _web_concurrency) // 2)

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 3600,
    'pool_size': _pool_size,
    'max_overflow': _pool_size,
    'pool_timeout': 30,
    'pool_pre_ping': True,
    'connect_args': {'options': '-c statement_timeout=30000'} if 'sqlite' not in os.environ.get('SQLALCHEMY_DATABASE_URI', '') else {},
}"""

if old_db_options in content:
    content = content.replace(old_db_options, new_db_options)


# 5. Settings Cache
old_settings = """_settings_lock = threading.Lock()
_settings_cache = {'data': {}, 'expires': 0}

def get_settings() -> dict[str, str]:
    \"\"\"Fetches and caches application settings from the database.\"\"\"
    now = time.time()
    if now < _settings_cache['expires']:
        return _settings_cache['data']
    acquired = _settings_lock.acquire(blocking=False)
    if not acquired:
        return _settings_cache['data']
    try:
        settings_rows = AppSettings.query.all()
        _settings_cache['data'] = {row.key: row.value for row in settings_rows}
        _settings_cache['expires'] = now + 1800  # 30 minutes
        return _settings_cache['data']
    except Exception as e:
        app.logger.error("Failed to fetch settings", exc_info=True)
        return _settings_cache['data']
    finally:
        _settings_lock.release()"""

new_settings = """@cache.memoize(timeout=1800)
def _get_settings_cached() -> dict[str, str]:
    try:
        settings_rows = AppSettings.query.all()
        return {row.key: row.value for row in settings_rows}
    except Exception as e:
        app.logger.warning("Failed to fetch settings", exc_info=True)
        return {}

def get_settings() -> dict[str, str]:
    \"\"\"Fetches and caches application settings from the database.\"\"\"
    return _get_settings_cached()

def invalidate_settings_cache() -> None:
    cache.delete_memoized(_get_settings_cached)"""

if old_settings in content:
    content = content.replace(old_settings, new_settings)


with open('slb.py', 'w') as f:
    f.write(content)
