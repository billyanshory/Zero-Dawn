import re

with open('slb.py', 'r') as f:
    content = f.read()

# 1. Settings Cache Refactor
old_settings = """_settings_lock = threading.Lock()
_settings_cache = {'data': {}, 'expires': 0}

def get_settings() -> dict[str, str]:
    \"\"\"Fetches and caches application settings from the database.\"\"\"
    now = time.time()
    if now < _settings_cache['expires']:
        return _settings_cache['data']
    acquired = _settings_lock.acquire(blocking=False)
    if not acquired:
        return _settings_cache['data']
    try:
        settings_rows = AppSettings.query.all()
        _settings_cache['data'] = {row.key: row.value for row in settings_rows}
        _settings_cache['expires'] = now + 1800  # 30 minutes
        return _settings_cache['data']
    except Exception as e:
        app.logger.error("Failed to fetch settings", exc_info=True)
        return _settings_cache['data']
    finally:
        _settings_lock.release()"""

new_settings = """@cache.memoize(timeout=1800)
def _get_settings_cached() -> dict[str, str]:
    try:
        settings_rows = AppSettings.query.all()
        return {row.key: row.value for row in settings_rows}
    except Exception as e:
        app.logger.warning("Failed to fetch settings", exc_info=True)
        return {}

def get_settings() -> dict[str, str]:
    \"\"\"Fetches and caches application settings from the database.\"\"\"
    return _get_settings_cached()

def invalidate_settings_cache() -> None:
    cache.delete_memoized(_get_settings_cached)"""

if old_settings in content:
    content = content.replace(old_settings, new_settings)
else:
    # Manual regex replace
    content = re.sub(
        r"_settings_lock = threading\.Lock\(\)\n_settings_cache = \{'data': \{\}, 'expires': 0\}\n\ndef get_settings\(\) -> dict\[str, str\]:\n\s+\"\"\"Fetches and caches application settings from the database\.\"\"\"\n\s+now = time\.time\(\)\n\s+if now < _settings_cache\['expires'\]:\n\s+return _settings_cache\['data'\]\n\s+acquired = _settings_lock\.acquire\(blocking=False\)\n\s+if not acquired:\n\s+return _settings_cache\['data'\] \n\s+try:\n\s+settings_rows = AppSettings\.query\.all\(\)\n\s+_settings_cache\['data'\] = \{row\.key: row\.value for row in settings_rows\}\n\s+_settings_cache\['expires'\] = now \+ 1800  # 30 minutes\n\s+return _settings_cache\['data'\]\n\s+except Exception as e:\n\s+app\.logger\.error\(\"Failed to fetch settings\", exc_info=True\)\n\s+return _settings_cache\['data'\] \n\s+finally:\n\s+_settings_lock\.release\(\)",
        new_settings,
        content
    )


# 2. Redis Leader Election & Writability Guards (Prefetch emoji)
old_emoji = """def prefetch_emoji_icons() -> None:
    def _download():
        try:
            emoji_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'emoji_cache')
            os.makedirs(emoji_dir, exist_ok=True)
            hex_codes = ['1f441', '1f442', '1f3c3', '1f590', '1f3af', '1f5e3', '2753']
            for code in hex_codes:
                file_path = os.path.join(emoji_dir, f'{code}.svg')
                if not os.path.exists(file_path):
                    url = f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/svg/{code}.svg"
                    try:
                        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=(3, 10))
                        response.raise_for_status()
                        with open(file_path, 'wb') as f:
                            f.write(response.content)
                    except Exception as e:
                        app.logger.warning(f"Emoji prefetch failed for {code}: {e}")
        except Exception as e:
            app.logger.warning(f"Emoji prefetch failed: {e}")

    eventlet.spawn(_download)"""

new_emoji = """def prefetch_emoji_icons() -> None:
    def _download():
        try:
            emoji_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'emoji_cache')
            try:
                os.makedirs(emoji_dir, exist_ok=True)
            except OSError:
                app.logger.info("Emoji cache directory not writable; skipping prefetch.")
                return

            _redis_url = os.getenv('REDIS_URL')
            if _redis_url:
                import redis
                try:
                    r = redis.from_url(_redis_url, socket_timeout=2.0)
                    if not r.set('slb_emoji_prefetch', '1', nx=True, ex=86400):
                        return
                except Exception:
                    pass

            hex_codes = ['1f441', '1f442', '1f3c3', '1f590', '1f3af', '1f5e3', '2753']
            for code in hex_codes:
                file_path = os.path.join(emoji_dir, f'{code}.svg')
                if not os.path.exists(file_path):
                    url = f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/svg/{code}.svg"
                    try:
                        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=(3, 10))
                        response.raise_for_status()
                        with open(file_path, 'wb') as f:
                            f.write(response.content)
                    except requests.RequestException:
                        app.logger.warning(f"Emoji prefetch failed for {code}", exc_info=True)
        except Exception as e:
            app.logger.warning("Emoji prefetch failed", exc_info=True)

    eventlet.spawn(_download)"""

if old_emoji in content:
    content = content.replace(old_emoji, new_emoji)
else:
    # manual regex replace
    content = re.sub(
        r"def prefetch_emoji_icons\(\) -> None:\n\s+def _download\(\):\n\s+try:\n\s+emoji_dir = os\.path\.join\(os\.path\.abspath\(os\.path\.dirname\(__file__\)\), 'emoji_cache'\)\n\s+os\.makedirs\(emoji_dir, exist_ok=True\)\n\s+hex_codes = \['1f441', '1f442', '1f3c3', '1f590', '1f3af', '1f5e3', '2753'\]\n\s+for code in hex_codes:\n\s+file_path = os\.path\.join\(emoji_dir, f'\{code\}\.svg'\)\n\s+if not os\.path\.exists\(file_path\):\n\s+url = f\"https://cdnjs\.cloudflare\.com/ajax/libs/twemoji/14\.0\.2/svg/\{code\}\.svg\"\n\s+try:\n\s+response = requests\.get\(url, headers=\{'User-Agent': 'Mozilla/5\.0'\}, timeout=\(3, 10\)\)\n\s+response\.raise_for_status\(\)\n\s+with open\(file_path, 'wb'\) as f:\n\s+f\.write\(response\.content\)\n\s+except Exception as e:\n\s+app\.logger\.warning\(f\"Emoji prefetch failed for \{code\}: \{e\}\"\)\n\s+except Exception as e:\n\s+app\.logger\.warning\(f\"Emoji prefetch failed: \{e\}\"\)\n\s+eventlet\.spawn\(_download\)",
        new_emoji,
        content
    )


# 3. Push Notifications Guards
old_sub = """@app.route('/orang-tua/api/subscribe', methods=['POST'])
@limiter.limit(RATE_LIMIT_OT_API)
@require_auth(roles=ALL_ROLES)
def subscribe() -> Response | str | tuple[Response, int]:"""

new_sub = """@app.route('/orang-tua/api/subscribe', methods=['POST'])
@limiter.limit(RATE_LIMIT_OT_API)
@require_auth(roles=ALL_ROLES)
def subscribe() -> Response | str | tuple[Response, int]:
    if not PUSH_NOTIFICATIONS_ENABLED: return jsonify({'error': 'Push not configured'}), 503"""

if old_sub in content:
    content = content.replace(old_sub, new_sub)


# 4. Exception Handling in API Yasin
old_api_yasin_except = """    except Exception:
        # Expected delay or timeout handled by caching 86400s
        app.logger.warning("EQuran API unavailable", exc_info=True)
        return jsonify({"error": "Gagal memuat Surat Yasin. Silakan coba lagi."}), 500"""

new_api_yasin_except = """    except requests.RequestException:
        app.logger.error("EQuran API unavailable", exc_info=True)
        return jsonify({"error": "Gagal memuat Surat Yasin. Silakan coba lagi."}), 502"""

if old_api_yasin_except in content:
    content = content.replace(old_api_yasin_except, new_api_yasin_except)
else:
    content = re.sub(
        r"except Exception:\n\s+# Expected delay or timeout handled by caching 86400s\n\s+app\.logger\.warning\(\"EQuran API unavailable\", exc_info=True\)\n\s+return jsonify\(\{\"error\": \"Gagal memuat Surat Yasin\. Silakan coba lagi\.\"\}\), 500",
        new_api_yasin_except,
        content
    )


with open('slb.py', 'w') as f:
    f.write(content)
