import re

with open("app.py", "r") as f:
    content = f.read()

replacement = """if __name__ == '__main__':
    _is_dev_env = os.getenv('FLASK_ENV', 'production').lower() == 'development'
    _prod_indicators = [
        os.getenv('PRODUCTION') == '1',
        os.getenv('IDCLOUDHOST') == '1',
        any(x not in os.getenv('SQLALCHEMY_DATABASE_URI', '') for x in ['localhost', '127.0.0.1', '::1']) if os.getenv('SQLALCHEMY_DATABASE_URI') else False
    ]
    # The requirement is: string contains anything other than localhost or 127.0.0.1 or ::1
    # Actually, a better check for "contains anything other than" is to check if it's NOT containing localhost/127.0.0.1/::1, or if it does, it's NOT ONLY them, but we can do:
    _db_uri = os.getenv('SQLALCHEMY_DATABASE_URI', '')
    _db_is_remote = bool(_db_uri) and not any(local_host in _db_uri for local_host in ['localhost', '127.0.0.1', '::1', 'sqlite:///'])

    _any_prod_indicator = (os.getenv('PRODUCTION') == '1') or (os.getenv('IDCLOUDHOST') == '1') or _db_is_remote

    if _is_dev_env and _any_prod_indicator:
        raise RuntimeError("Refusing to start development server with production indicators present.")

    _secret = app.secret_key or ''
    if _secret in ['dev', 'changeme', 'secret', ''] or len(_secret) < 32:
        raise RuntimeError("Refusing to start: app.secret_key is insecure or too short.")

    _host = '0.0.0.0' if not _is_dev_env else '127.0.0.1'
    _port = int(os.getenv('PORT', 5001))
    _allow_unsafe = _is_dev_env and not _any_prod_indicator

    app.logger.warning("socketio.run() is a DEVELOPMENT server. For production, run: gunicorn -k eventlet -w 1 --bind 0.0.0.0:5001 module:app")
    socketio.run(app, debug=_is_dev_env, host=_host, port=_port, allow_unsafe_werkzeug=_allow_unsafe)
"""

# We need to accurately replace the last lines.
pattern = r"if __name__ == '__main__':\n\s+socketio\.run\(app, debug=os\.environ\.get\('FLASK_ENV'\) == 'development', port=5001, allow_unsafe_werkzeug=os\.environ\.get\('FLASK_ENV'\) == 'development'\)\n?"

new_content = re.sub(pattern, replacement, content)

with open("app.py", "w") as f:
    f.write(new_content)
