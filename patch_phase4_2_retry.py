import re

with open("app.py", "r") as f:
    content = f.read()

# We need to correctly match the entire get_settings block. Let's use re.DOTALL
settings_pattern = r"_settings_lock = threading\.Lock\(\)\n_settings_cache = \{'data': \{\}, 'expires': 0\}.*?def invalidate_settings_cache\(\) -> None:\n.*?_settings_cache\['expires'\] = 0"

settings_cache_new = """@cache.memoize(timeout=1800)
def _get_settings_cached() -> dict:
    try:
        return {s.key: s.value for s in AppSettings.query.all()}
    except Exception:
        app.logger.warning("Failed to load settings from DB", exc_info=True)
        return {}

def get_settings() -> dict:
    \"\"\"Fetches and caches application settings from the database.\"\"\"
    return _get_settings_cached()

def invalidate_settings_cache() -> None:
    \"\"\"Invalidates the settings cache.\"\"\"
    cache.delete_memoized(_get_settings_cached)"""

content = re.sub(settings_pattern, settings_cache_new, content, flags=re.DOTALL)

with open("app.py", "w") as f:
    f.write(content)
