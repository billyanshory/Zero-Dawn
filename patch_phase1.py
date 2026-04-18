import re

with open('slb.py', 'r') as f:
    content = f.read()

# 1. Import ProxyFix
if 'from werkzeug.middleware.proxy_fix import ProxyFix' not in content:
    content = re.sub(
        r'(from werkzeug\.utils import secure_filename)',
        r'\1\nfrom werkzeug.middleware.proxy_fix import ProxyFix',
        content,
        count=1
    )

# 2. Wrap app.wsgi_app = ProxyFix(...)
if 'app.wsgi_app = ProxyFix' not in content:
    content = re.sub(
        r'(app = Flask\(__name__\))',
        r'\1\napp.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)',
        content,
        count=1
    )

# 3. Rebuild if __name__ == '__main__':
old_main = """if __name__ == '__main__':
    is_dev = os.getenv('FLASK_ENV') == 'development'
    socketio.run(app, debug=is_dev, port=5001, allow_unsafe_werkzeug=is_dev)"""

new_main = """if __name__ == '__main__':
    is_dev = os.getenv('FLASK_ENV', 'production').lower() == 'development'
    is_prod_env = os.getenv('PRODUCTION') == '1'
    is_idcloudhost = os.getenv('IDCLOUDHOST') == '1'
    db_uri = os.getenv('SQLALCHEMY_DATABASE_URI', '')
    is_prod_db = db_uri and not any(localhost in db_uri for localhost in ('localhost', '127.0.0.1', '::1'))
    is_prod_indicator = is_prod_env or is_idcloudhost or is_prod_db

    if is_dev and is_prod_indicator:
        raise RuntimeError("Refusing to start development server with Werkzeug debugger against a production environment/database.")

    _sk = app.secret_key
    if not _sk or _sk in ('dev', 'changeme', 'secret', '') or len(_sk) < 32:
        raise RuntimeError("Refusing to start: SECRET_KEY is too short or uses a placeholder value.")

    _host = '127.0.0.1' if is_dev else '0.0.0.0'
    _port = int(os.getenv('PORT', 5001))
    _allow_unsafe = is_dev and not is_prod_indicator

    app.logger.warning("socketio.run() is a DEVELOPMENT server. For production, run: gunicorn -k eventlet -w 1 --bind 0.0.0.0:5001 module:app")
    socketio.run(app, host=_host, port=_port, debug=is_dev, allow_unsafe_werkzeug=_allow_unsafe)"""

if old_main in content:
    content = content.replace(old_main, new_main)


# 4. Set SESSION_COOKIE_SECURE and REMEMBER_COOKIE
old_session = """app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'"""

new_session = """_is_dev_env = os.getenv('FLASK_ENV', 'production').lower() == 'development'
app.config['SESSION_COOKIE_SECURE'] = not _is_dev_env
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['REMEMBER_COOKIE_SECURE'] = not _is_dev_env
app.config['REMEMBER_COOKIE_HTTPONLY'] = True"""

if old_session in content:
    content = content.replace(old_session, new_session)


# 5. Rewrite SocketIO initialization
old_socketio = """_cors_origins = os.getenv('ALLOWED_ORIGINS', '').split(',') if os.getenv('ALLOWED_ORIGINS') else '*'
_cors_origins = [o.strip() for o in _cors_origins if o.strip()] if isinstance(_cors_origins, list) else _cors_origins
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins=_cors_origins)"""

new_socketio = """_allowed_origins_env = os.getenv('ALLOWED_ORIGINS', '').strip()
if _allowed_origins_env:
    _cors_origins = [o.strip() for o in _allowed_origins_env.split(',') if o.strip()]
else:
    _is_dev_env_check = os.getenv('FLASK_ENV', 'production').lower() == 'development'
    if _is_dev_env_check:
        _cors_origins = '*'
    else:
        raise RuntimeError("ALLOWED_ORIGINS must be set in production to prevent open WebSocket access.")

_redis_url = os.getenv('REDIS_URL')
socketio = SocketIO(
    app,
    async_mode='eventlet',
    cors_allowed_origins=_cors_origins,
    message_queue=_redis_url,
    ping_interval=25,
    ping_timeout=60,
    logger=False,
    engineio_logger=False
)
if not _redis_url:
    app.logger.warning("SocketIO has no message_queue configured (REDIS_URL is unset). Multi-worker SocketIO broadcasts will be dropped. Set REDIS_URL for production.")"""

if old_socketio in content:
    content = content.replace(old_socketio, new_socketio)


with open('slb.py', 'w') as f:
    f.write(content)
