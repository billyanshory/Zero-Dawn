with open("app.py", "r") as f:
    content = f.read()

# 1. Update the compress imports fallback block
old_compress_import = """    _compress_available = True
except ImportError:
    _compress_available = False"""

new_compress_import = """    _compress_available = True
except ImportError:
    _compress_available = False
    import gzip as _gzip_fallback"""
content = content.replace(old_compress_import, new_compress_import)

# 2. Update the fallback logic and configuration
old_compress_init = """if _compress_available:
    compress = Compress(app)
else:
    app.logger.warning("flask_compress is not installed. Response compression is disabled.")"""

new_compress_init = """if _compress_available:
    compress = Compress(app)
else:
    app.logger.warning("Flask-Compress is not installed. Falling back to a minimal gzip handler. Install flask-compress for production-grade compression")
    @app.after_request
    def compress_fallback(response):
        accept_encoding = request.headers.get('Accept-Encoding', '')
        if 'gzip' not in accept_encoding.lower():
            return response
        if response.status_code < 200 or response.status_code >= 300:
            return response
        if response.content_length is not None and response.content_length < 500:
            return response
        content_type = response.headers.get('Content-Type', '').split(';')[0].strip()
        if content_type not in app.config.get('COMPRESS_MIMETYPES', []):
            return response
        if 'Content-Encoding' in response.headers:
            return response

        gzip_buffer = io.BytesIO()
        with _gzip_fallback.GzipFile(mode='wb', fileobj=gzip_buffer, compresslevel=6) as gzip_file:
            gzip_file.write(response.get_data())

        response.set_data(gzip_buffer.getvalue())
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = response.content_length
        response.headers.add('Vary', 'Accept-Encoding')
        return response"""
content = content.replace(old_compress_init, new_compress_init)

# 3. Add compress configs
old_compress_config = "app.config['COMPRESS_MIMETYPES'] = ['text/html', 'text/css', 'application/json', 'application/javascript']"
new_compress_config = """app.config['COMPRESS_MIMETYPES'] = ['text/html', 'text/css', 'application/json', 'application/javascript']
app.config['COMPRESS_LEVEL'] = 6
app.config['COMPRESS_MIN_SIZE'] = 500
app.config['COMPRESS_ALGORITHM'] = ['br', 'gzip']"""
content = content.replace(old_compress_config, new_compress_config)

with open("app.py", "w") as f:
    f.write(content)
