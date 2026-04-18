import re

with open("app.py", "r") as f:
    content = f.read()

# 1. SQLALCHEMY_ENGINE_OPTIONS
sql_opts_old = """app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 3600,
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 30,
    'pool_pre_ping': True,
    'connect_args': {'options': '-c statement_timeout=30000'} if 'sqlite' not in os.environ.get('SQLALCHEMY_DATABASE_URI', '') else {},
}"""

sql_opts_new = """_web_concurrency = int(os.getenv('WEB_CONCURRENCY', 1))
_db_max_connections = int(os.getenv('DB_MAX_CONNECTIONS', 80))
_pool_size_calc = max(2, _db_max_connections // max(1, _web_concurrency * 2))

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 3600,
    'pool_size': _pool_size_calc,
    'max_overflow': _pool_size_calc,
    'pool_timeout': 30,
    'pool_pre_ping': True,
    'connect_args': {'options': '-c statement_timeout=30000'} if 'sqlite' not in os.environ.get('SQLALCHEMY_DATABASE_URI', '') else {},
}"""
content = content.replace(sql_opts_old, sql_opts_new)

# 2. _settings_cache
settings_cache_old = """_settings_lock = threading.Lock()
_settings_cache = {'data': {}, 'expires': 0}

def get_settings() -> dict:
    \"\"\"Fetches settings from cache or database.\"\"\"
    global _settings_cache
    now = time.time()
    if now < _settings_cache['expires']:
        return _settings_cache['data']
    with _settings_lock:
        if now < _settings_cache['expires']:
            return _settings_cache['data']
        try:
            settings = {s.key: s.value for s in AppSettings.query.all()}
            _settings_cache['data'] = settings
            _settings_cache['expires'] = now + 1800
            return settings
        except Exception:
            app.logger.error("Failed to load settings from DB", exc_info=True)
            return _settings_cache['data'] or {}

def invalidate_settings_cache() -> None:
    \"\"\"Invalidates the settings cache.\"\"\"
    global _settings_cache
    with _settings_lock:
        _settings_cache['data'] = {}
        _settings_cache['expires'] = 0"""

settings_cache_new = """@cache.memoize(timeout=1800)
def _get_settings_cached() -> dict:
    try:
        return {s.key: s.value for s in AppSettings.query.all()}
    except Exception:
        app.logger.warning("Failed to load settings from DB", exc_info=True)
        return {}

def get_settings() -> dict:
    \"\"\"Fetches settings from cache or database.\"\"\"
    return _get_settings_cached()

def invalidate_settings_cache() -> None:
    \"\"\"Invalidates the settings cache.\"\"\"
    cache.delete_memoized(_get_settings_cached)"""

content = content.replace(settings_cache_old, settings_cache_new)

with open("app.py", "w") as f:
    f.write(content)
