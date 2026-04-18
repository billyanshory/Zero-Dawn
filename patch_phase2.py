import re

with open('slb.py', 'r') as f:
    content = f.read()

# Add endpoints /healthz and /readyz after add_security_headers
if '@app.route(\'/healthz\')' not in content:
    health_routes = """
@app.route('/healthz', methods=['GET'])
@csrf.exempt
def healthz() -> tuple[Response, int]:
    return jsonify({"status": "alive"}), 200

limiter.exempt(healthz)

@app.route('/readyz', methods=['GET'])
@csrf.exempt
def readyz() -> tuple[Response, int]:
    import traceback
    checks = {"db": False, "redis": False}
    status_code = 200
    try:
        db.session.execute(db.text('SELECT 1'))
        checks["db"] = True
    except Exception as e:
        app.logger.warning("Readiness probe DB check failed", exc_info=True)
        status_code = 503

    _redis_url = os.getenv('REDIS_URL')
    if not _redis_url:
        checks["redis"] = True
    else:
        try:
            import redis
            r = redis.from_url(_redis_url, socket_timeout=2.0)
            if r.ping():
                checks["redis"] = True
            else:
                status_code = 503
        except Exception as e:
            app.logger.warning("Readiness probe Redis check failed", exc_info=True)
            status_code = 503

    status_str = "ready" if status_code == 200 else "not_ready"
    response_body = {"status": status_str, "checks": checks}
    response = jsonify(response_body)
    if status_code == 503:
        response.headers['Retry-After'] = '5'
    return response, status_code

limiter.exempt(readyz)
"""

    content = re.sub(
        r'(@app\.after_request\ndef add_security_headers\(response: Response\) -> Response:.*?return response\n)',
        r'\1\n' + health_routes,
        content,
        flags=re.DOTALL
    )

# Rebuild Logging configuration
# Current logging:
# # Configure Logging
# log_dir = os.path.expanduser('~/logs')
# if not os.path.exists(log_dir):
#     os.makedirs(log_dir)
# file_handler = logging.handlers.RotatingFileHandler(
#     os.path.join(log_dir, 'slb_error.log'), maxBytes=10485760, backupCount=10)
# file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
# file_handler.setLevel(logging.ERROR)
# app.logger.addHandler(file_handler)
# app.logger.setLevel(logging.ERROR)

old_logging = """# Configure Logging
log_dir = os.path.expanduser('~/logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
file_handler = logging.handlers.RotatingFileHandler(
    os.path.join(log_dir, 'slb_error.log'), maxBytes=10485760, backupCount=10)
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
    log_dir = os.path.expanduser('~/logs')
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

if '# Configure Logging' in content:
    content = re.sub(r'# Configure Logging.*?app\.logger\.setLevel\(logging\.ERROR\)', new_logging, content, flags=re.DOTALL)


# Rebuild add_security_headers
old_security_headers = """@app.after_request
def add_security_headers(response: Response) -> Response:
    if 'text/html' in response.content_type:
        # TODO: Remove 'unsafe-eval' from CSP once Tailwind CDN is replaced with pre-built CSS file (see consolidated migration note above class Siswa)
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://cdn.tailwindcss.com; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; img-src 'self' data: https://api.dicebear.com https://commons.wikimedia.org https://www.lifeprint.com https://media.giphy.com; connect-src 'self' https://equran.id https://pmpk.kemdikbud.go.id https://api.giphy.com https://api.allorigins.win https://zenquotes.io; media-src 'self' blob:"
    return response"""

new_security_headers = """_CSP_HTML = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://cdn.tailwindcss.com; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; img-src 'self' data: https://api.dicebear.com https://commons.wikimedia.org https://www.lifeprint.com https://media.giphy.com; connect-src 'self' https://equran.id https://pmpk.kemdikbud.go.id https://api.giphy.com https://api.allorigins.win https://zenquotes.io; media-src 'self' blob:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
_CSP_JSON = "default-src 'none'; frame-ancestors 'none'"
_PERMISSIONS_POLICY = "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=(), interest-cohort=()"

@app.after_request
def add_security_headers(response: Response) -> Response:
    ct = response.content_type.lower()
    is_html = 'text/html' in ct
    is_json = 'application/json' in ct

    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = _PERMISSIONS_POLICY
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'

    if request.is_secure or request.headers.get('X-Forwarded-Proto', '').lower() == 'https':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

    response.headers.pop('Server', None)
    response.headers.pop('X-Powered-By', None)

    if is_html:
        response.headers['Content-Security-Policy'] = _CSP_HTML
    elif is_json:
        response.headers['Content-Security-Policy'] = _CSP_JSON

    return response"""

if 'def add_security_headers' in content:
    content = content.replace(old_security_headers, new_security_headers)

with open('slb.py', 'w') as f:
    f.write(content)
