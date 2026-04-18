import re

with open('slb.py', 'r') as f:
    content = f.read()

# 1. Logging Rebuild
old_logging = """# Configure Logging
log_dir = os.path.join(os.path.expanduser('~'), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, 'slb_error.log')
file_handler = logging.handlers.RotatingFileHandler(log_path, maxBytes=10485760, backupCount=10)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.ERROR)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.ERROR)"""

new_logging = """# Configure Logging
import sys as _sys
_log_level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
_log_level = getattr(logging, _log_level_name, logging.INFO)
app.logger.setLevel(_log_level)
app.logger.handlers.clear()

_formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s [%(request_id)s] %(message)s [in %(pathname)s:%(lineno)d]')

class _RequestIdFilter(logging.Filter):
    def filter(self, record):
        from flask import has_request_context, g
        record.request_id = getattr(g, 'request_id', '-') if has_request_context() else '-'
        return True

_stream_handler = logging.StreamHandler(_sys.stdout)
_stream_handler.setFormatter(_formatter)
_stream_handler.addFilter(_RequestIdFilter())
_stream_handler.setLevel(_log_level)
app.logger.addHandler(_stream_handler)

try:
    log_dir = os.path.join(os.path.expanduser('~'), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    _file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'slb_error.log'), maxBytes=10485760, backupCount=10)
    _file_handler.setFormatter(_formatter)
    _file_handler.addFilter(_RequestIdFilter())
    _file_handler.setLevel(_log_level)
    app.logger.addHandler(_file_handler)
except OSError as e:
    app.logger.warning("Could not create log directory (read-only filesystem). Falling back to stdout-only logging.")

@app.before_request
def assign_request_id():
    from flask import g, request
    import uuid
    g.request_id = request.headers.get('X-Request-ID') or uuid.uuid4().hex[:12]

@app.after_request
def inject_request_id(response: Response) -> Response:
    from flask import g
    if hasattr(g, 'request_id'):
        response.headers['X-Request-ID'] = g.request_id
    return response

_sentry_dsn = os.getenv('SENTRY_DSN')
if _sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        _traces_rate = float(os.getenv('SENTRY_TRACES_RATE', '0.05'))
        sentry_sdk.init(
            dsn=_sentry_dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=_traces_rate
        )
        app.logger.info("Sentry initialization successful.")
    except ImportError:
        app.logger.warning("SENTRY_DSN provided but sentry_sdk not installed. Sentry initialization skipped.")"""

if old_logging in content:
    content = content.replace(old_logging, new_logging)
elif "app.logger.setLevel(logging.ERROR)" in content:
    # try regex
    content = re.sub(r'# Configure Logging.*?app\.logger\.setLevel\(logging\.ERROR\)', new_logging, content, flags=re.DOTALL)


# 2. Error Handlers
old_error_handler_block = """@app.errorhandler(Exception)
def handle_exception(e: Exception) -> tuple[str, int]:
    app.logger.error("Unhandled exception", exc_info=True)
    return ERROR_500_HTML, 500"""

new_error_handler_block = """from werkzeug.exceptions import HTTPException

def _wants_json() -> bool:
    from flask import request
    return request.is_json or request.path.startswith('/api/') or request.path.startswith('/orang-tua/api/') or 'application/json' in request.headers.get('Accept', '')

def _error_response(code: int, message: str, retry_after: int = None) -> tuple[Response, int]:
    if _wants_json():
        res = jsonify({"error": message})
        if retry_after is not None:
            res.headers['Retry-After'] = str(retry_after)
        return res, code
    else:
        html = f'''
        <!DOCTYPE html>
        <html lang="id">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Kesalahan {code}</title>
            </head>
            <body>
                <h1>Mohon Maaf (Kesalahan {code})</h1>
                <p>{message}</p>
                <p><a href="/">Kembali ke beranda</a></p>
            </body>
        </html>
        '''
        res = Response(html, status=code, mimetype='text/html')
        if retry_after is not None:
            res.headers['Retry-After'] = str(retry_after)
        return res, code

@app.errorhandler(400)
def handle_400(e):
    return _error_response(400, "Permintaan tidak valid.")

@app.errorhandler(401)
def handle_401(e):
    return _error_response(401, "Akses ditolak. Silakan login.")

@app.errorhandler(403)
def handle_403(e):
    return _error_response(403, "Anda tidak memiliki izin untuk mengakses halaman ini.")

@app.errorhandler(404)
def handle_404(e):
    return _error_response(404, "Halaman atau data tidak ditemukan.")

@app.errorhandler(405)
def handle_405(e):
    return _error_response(405, "Metode yang digunakan tidak diizinkan.")

@app.errorhandler(413)
def handle_413(e):
    return _error_response(413, "Ukuran file terlalu besar.")

@app.errorhandler(429)
def handle_429(e):
    return _error_response(429, "Terlalu banyak permintaan. Silakan tunggu beberapa saat.", retry_after=60)

@app.errorhandler(500)
def handle_500(e):
    return _error_response(500, "Terjadi kesalahan internal server.")

@app.errorhandler(502)
def handle_502(e):
    return _error_response(502, "Terjadi kesalahan jaringan hulu.", retry_after=10)

@app.errorhandler(503)
def handle_503(e):
    return _error_response(503, "Layanan sedang tidak tersedia.", retry_after=30)

@app.errorhandler(504)
def handle_504(e):
    return _error_response(504, "Waktu tunggu layanan habis.", retry_after=30)

@app.errorhandler(Exception)
def handle_exception(e: Exception):
    if isinstance(e, HTTPException):
        return e
    app.logger.error("Unhandled exception", exc_info=True)
    return _error_response(500, "Terjadi kesalahan sistem.")"""

if old_error_handler_block in content:
    content = content.replace(old_error_handler_block, new_error_handler_block)


# 3. Settings Cache
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


# 4. Webpush Guard
old_webpush_sub = """@app.route('/api/webpush_subscribe', methods=['POST'])
@csrf.exempt
def webpush_subscribe() -> Response | str | tuple[Response, int]:"""
new_webpush_sub = """@app.route('/api/webpush_subscribe', methods=['POST'])
@csrf.exempt
def webpush_subscribe() -> Response | str | tuple[Response, int]:
    if not PUSH_NOTIFICATIONS_ENABLED: return jsonify({'error': 'Push not configured'}), 503"""

if old_webpush_sub in content:
    content = content.replace(old_webpush_sub, new_webpush_sub)


# 5. Fix UPLOAD_FOLDER exception
content = content.replace(
    "    _probe_path = os.path.join(app.config['UPLOAD_FOLDER'], '.write_probe')\n    with open(_probe_path, 'w') as f:",
    "    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)\n    _probe_path = os.path.join(app.config['UPLOAD_FOLDER'], '.write_probe')\n    with open(_probe_path, 'w') as f:"
)


with open('slb.py', 'w') as f:
    f.write(content)
