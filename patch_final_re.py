import re

with open('slb.py', 'r') as f:
    content = f.read()

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

content = re.sub(r'def prefetch_emoji_icons\(\) -> None:(.+?)eventlet\.spawn\(_download\)', new_emoji, content, flags=re.DOTALL)


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

content = re.sub(r'_settings_lock = threading\.Lock\(\)(.+?)_settings_lock\.release\(\)', new_settings, content, flags=re.DOTALL)


new_yasin_except = """    except requests.RequestException:
        app.logger.error("EQuran API unavailable", exc_info=True)
        return jsonify({"error": "Gagal memuat Surat Yasin. Silakan coba lagi."}), 502"""

content = re.sub(r'    except Exception:\n\s+# Expected delay or timeout handled by caching 86400s\n\s+app\.logger\.warning\("EQuran API unavailable", exc_info=True\)\n\s+return jsonify\(\{"error": "Gagal memuat Surat Yasin\. Silakan coba lagi\."\}\), 500', new_yasin_except, content, flags=re.DOTALL)

with open('slb.py', 'w') as f:
    f.write(content)
