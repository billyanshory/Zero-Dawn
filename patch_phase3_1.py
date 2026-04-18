import re

with open("app.py", "r") as f:
    content = f.read()

# Make sure HTTPException is imported
if "from werkzeug.exceptions import HTTPException" not in content:
    content = content.replace("from werkzeug.utils import secure_filename", "from werkzeug.exceptions import HTTPException\nfrom werkzeug.utils import secure_filename")

# Old error handler
old_error_handler = """@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled Exception: {e}", exc_info=True)
    return "Terjadi kesalahan sistem.", 500"""

new_error_handlers = """def _wants_json() -> bool:
    if request.is_json:
        return True
    if request.path.startswith('/api/') or request.path.startswith('/orang-tua/api/'):
        return True
    if 'application/json' in request.headers.get('Accept', ''):
        return True
    return False

def _error_response(code: int, message: str, retry_after: int | None = None) -> Response:
    if _wants_json():
        resp = jsonify({'error': message})
        resp.status_code = code
        if retry_after is not None:
            resp.headers['Retry-After'] = str(retry_after)
        return resp
    else:
        html = f'''<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error {code}</title>
    <style>body{{font-family:sans-serif;text-align:center;padding:50px;}} h1{{font-size:50px;}}</style>
</head>
<body>
    <h1>{code}</h1>
    <p>{message}</p>
    <a href="/">Kembali ke beranda</a>
</body>
</html>'''
        resp = Response(html, status=code, mimetype='text/html')
        if retry_after is not None:
            resp.headers['Retry-After'] = str(retry_after)
        return resp

@app.errorhandler(400)
def handle_400(e):
    return _error_response(400, "Permintaan tidak valid.")

@app.errorhandler(401)
def handle_401(e):
    return _error_response(401, "Autentikasi diperlukan.")

@app.errorhandler(403)
def handle_403(e):
    return _error_response(403, "Akses ditolak.")

@app.errorhandler(404)
def handle_404(e):
    return _error_response(404, "Halaman tidak ditemukan.")

@app.errorhandler(405)
def handle_405(e):
    return _error_response(405, "Metode tidak diizinkan.")

@app.errorhandler(413)
def handle_413(e):
    return _error_response(413, "Ukuran file terlalu besar.")

@app.errorhandler(429)
def handle_429(e):
    return _error_response(429, "Terlalu banyak permintaan.", retry_after=60)

@app.errorhandler(500)
def handle_500(e):
    return _error_response(500, "Terjadi kesalahan sistem internal.")

@app.errorhandler(502)
def handle_502(e):
    return _error_response(502, "Bad Gateway.", retry_after=10)

@app.errorhandler(503)
def handle_503(e):
    return _error_response(503, "Layanan tidak tersedia.", retry_after=30)

@app.errorhandler(504)
def handle_504(e):
    return _error_response(504, "Gateway Timeout.", retry_after=30)

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    app.logger.error("Unhandled Exception", exc_info=True)
    return _error_response(500, "Terjadi kesalahan sistem internal.")"""

content = content.replace(old_error_handler, new_error_handlers)

with open("app.py", "w") as f:
    f.write(content)
