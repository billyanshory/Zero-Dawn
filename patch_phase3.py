import re

with open('slb.py', 'r') as f:
    content = f.read()

# 1. Edge Robustness: Error Handlers
old_error_handler_block = """ERROR_500_HTML = '''
    <!DOCTYPE html>
    <html lang="id">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Kesalahan Sistem</title>
        </head>
        <body>
            <h1>Mohon Maaf</h1>
            <p>Terjadi kesalahan teknis. Silakan coba beberapa saat lagi.</p>
        </body>
    </html>
    '''

@app.errorhandler(Exception)
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

if 'def handle_exception(e: Exception) -> tuple[str, int]:' in content:
    content = content.replace(old_error_handler_block, new_error_handler_block)


# 2. Add graceful shutdown logic
graceful_shutdown_code = """
import signal as _signal
import atexit as _atexit

def _graceful_shutdown(signum=None, frame=None):
    app.logger.info("Graceful shutdown requested (signal=%s)", signum)
    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            app.logger.info("Scheduler shutdown initiated.")
    except Exception as e:
        app.logger.error("Error shutting down scheduler", exc_info=True)

    try:
        _redis_url = os.getenv('REDIS_URL')
        if _redis_url:
            import redis
            r = redis.from_url(_redis_url, socket_timeout=2.0)
            r.delete('slb_scheduler_master')
            app.logger.info("Scheduler lock released.")
    except Exception as e:
        app.logger.error("Error releasing scheduler lock", exc_info=True)

    try:
        db.session.remove()
        db.engine.dispose()
        app.logger.info("Database connections drained.")
    except Exception as e:
        app.logger.error("Error draining database connections", exc_info=True)

    try:
        for handler in app.logger.handlers:
            handler.flush()
    except Exception as e:
        app.logger.error("Error flushing log handlers", exc_info=True)

_signal.signal(_signal.SIGTERM, _graceful_shutdown)
_signal.signal(_signal.SIGINT, _graceful_shutdown)
_atexit.register(_graceful_shutdown)
"""
if 'def _graceful_shutdown' not in content:
    content = re.sub(
        r'(with app\.app_context\(\):\n\s+try:\n\s+start_scheduler_if_primary\(\))',
        graceful_shutdown_code.strip() + '\n\n' + r'\1',
        content,
        count=1
    )


# 3. Enhance Flask-Compress logic
# Fallback import block
old_compress_import = """try:
    from flask_compress import Compress
    _compress_available = True
except ImportError:
    _compress_available = False"""

new_compress_import = """try:
    from flask_compress import Compress
    _compress_available = True
except ImportError:
    import gzip as _gzip_fallback
    _compress_available = False"""

if 'import gzip as _gzip_fallback' not in content:
    content = content.replace(old_compress_import, new_compress_import)

# Instantiation and config block
old_compress_init = """if _compress_available:
    Compress(app)"""

new_compress_init = """if _compress_available:
    Compress(app)
else:
    app.logger.warning("Flask-Compress is not installed. Falling back to a minimal gzip handler. Install flask-compress for production-grade compression")
    @app.after_request
    def fallback_gzip(response: Response) -> Response:
        accept_encoding = request.headers.get('Accept-Encoding', '')
        if 'gzip' not in accept_encoding.lower():
            return response
        if response.status_code < 200 or response.status_code >= 300:
            return response

        content_length = response.headers.get('Content-Length')
        if content_length is not None and int(content_length) < 500:
            return response

        content_type = response.content_type.split(';')[0].lower()
        if content_type not in app.config.get('COMPRESS_MIMETYPES', []):
            return response

        if 'Content-Encoding' in response.headers:
            return response

        import gzip as _gzip_fallback
        compressed_data = _gzip_fallback.compress(response.get_data(), compresslevel=6)
        response.set_data(compressed_data)
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = len(response.get_data())
        vary = response.headers.get('Vary')
        if not vary:
            response.headers['Vary'] = 'Accept-Encoding'
        elif 'accept-encoding' not in vary.lower():
            response.headers['Vary'] = f"{vary}, Accept-Encoding"
        return response"""

if 'fallback_gzip' not in content:
    content = content.replace(old_compress_init, new_compress_init)

# Config appending
old_compress_mimetypes = "app.config['COMPRESS_MIMETYPES'] = ['text/html', 'text/css', 'application/json', 'application/javascript']"
new_compress_mimetypes = """app.config['COMPRESS_MIMETYPES'] = ['text/html', 'text/css', 'application/json', 'application/javascript']
app.config['COMPRESS_LEVEL'] = 6
app.config['COMPRESS_MIN_SIZE'] = 500
app.config['COMPRESS_ALGORITHM'] = ['br', 'gzip']"""

if "COMPRESS_LEVEL" not in content:
    content = content.replace(old_compress_mimetypes, new_compress_mimetypes)

with open('slb.py', 'w') as f:
    f.write(content)
