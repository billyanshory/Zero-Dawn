import re

with open("app.py", "r") as f:
    content = f.read()

# Refactor Cookies
cookie_pattern = r"app\.config\['SESSION_COOKIE_SECURE'\] = True"
cookie_replacement = """_is_dev_env = os.getenv('FLASK_ENV', 'production').lower() == 'development'
app.config['SESSION_COOKIE_SECURE'] = not _is_dev_env
app.config['REMEMBER_COOKIE_SECURE'] = not _is_dev_env
app.config['REMEMBER_COOKIE_HTTPONLY'] = True"""
content = re.sub(cookie_pattern, cookie_replacement, content)

# Refactor SocketIO
socketio_pattern = r"_cors_origins = os\.environ\.get\('ALLOWED_ORIGINS', '\*'\)\nsocketio = SocketIO\(app, async_mode='eventlet', cors_allowed_origins=_cors_origins\)"
socketio_replacement = """_allowed_origins_raw = os.getenv('ALLOWED_ORIGINS', '').strip()
if _allowed_origins_raw:
    _cors_origins = [origin.strip() for origin in _allowed_origins_raw.split(',') if origin.strip()]
else:
    _is_dev_env = os.getenv('FLASK_ENV', 'production').lower() == 'development'
    if _is_dev_env:
        _cors_origins = '*'
    else:
        raise RuntimeError("ALLOWED_ORIGINS is not set in production. Refusing to start with wildcard origins.")

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
    app.logger.warning("SocketIO has no message_queue configured (REDIS_URL is unset). Multi-worker SocketIO broadcasts will be dropped. Set REDIS_URL for production")"""

# We'll use string replace since regex with multiline can be tricky
socketio_old = """_cors_origins = os.environ.get('ALLOWED_ORIGINS', '*')
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins=_cors_origins)"""

content = content.replace(socketio_old, socketio_replacement)

with open("app.py", "w") as f:
    f.write(content)
