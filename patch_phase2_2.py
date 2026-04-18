import re

with open("app.py", "r") as f:
    content = f.read()

# 1. Imports
imports_pattern = r"import logging\.handlers"
imports_replacement = """import sys as _sys
from flask import g
import logging.handlers"""
content = re.sub(imports_pattern, imports_replacement, content, count=1)

# 2. Logging Setup
logging_old = """log_dir = os.path.join(os.path.expanduser('~'), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, 'slb_error.log')
handler = logging.handlers.RotatingFileHandler(log_path, maxBytes=10*1024*1024, backupCount=5)
handler.setLevel(logging.WARNING)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
app.logger.addHandler(handler)"""

logging_new = """
_log_level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
_log_level = getattr(logging, _log_level_name, logging.INFO)
app.logger.setLevel(_log_level)

class _RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(g, 'request_id', '-')
        return True

_formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s [%(request_id)s] %(message)s [in %(pathname)s:%(lineno)d]')

_stream_handler = logging.StreamHandler(_sys.stdout)
_stream_handler.setLevel(_log_level)
_stream_handler.setFormatter(_formatter)
_stream_handler.addFilter(_RequestIdFilter())
app.logger.addHandler(_stream_handler)

try:
    log_dir = os.path.join(os.path.expanduser('~'), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'slb_error.log')
    _file_handler = logging.handlers.RotatingFileHandler(log_path, maxBytes=10*1024*1024, backupCount=5)
    _file_handler.setLevel(_log_level)
    _file_handler.setFormatter(_formatter)
    _file_handler.addFilter(_RequestIdFilter())
    app.logger.addHandler(_file_handler)
except OSError:
    app.logger.warning("Could not create log directory; running with stdout logging only.")

@app.before_request
def assign_request_id():
    g.request_id = request.headers.get('X-Request-ID') or uuid.uuid4().hex[:12]

if os.getenv('SENTRY_DSN'):
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(
            dsn=os.getenv('SENTRY_DSN'),
            integrations=[FlaskIntegration()],
            traces_sample_rate=float(os.getenv('SENTRY_TRACES_RATE', 0.05))
        )
        app.logger.info("Sentry initialization successful.")
    except ImportError:
        app.logger.warning("SENTRY_DSN is set but sentry_sdk is not installed.")
"""
content = content.replace(logging_old, logging_new)

# 3. Add to after_request to echo X-Request-ID
after_req_pattern = r"def add_security_headers\(response: Response\) -> Response:"
after_req_replacement = """def add_security_headers(response: Response) -> Response:
    if hasattr(g, 'request_id'):
        response.headers['X-Request-ID'] = g.request_id"""
content = content.replace("def add_security_headers(response: Response) -> Response:", after_req_replacement)

with open("app.py", "w") as f:
    f.write(content)
