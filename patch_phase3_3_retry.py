with open("app.py", "r") as f:
    content = f.read()

# Fix the compress instantiation block which is slightly different in the file:
# if _compress_available:
#     Compress(app)

old_compress_init = """if _compress_available:
    Compress(app)"""

new_compress_init = """if _compress_available:
    Compress(app)
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

with open("app.py", "w") as f:
    f.write(content)
