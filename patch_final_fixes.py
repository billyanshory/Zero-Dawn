import re

with open('slb.py', 'r') as f:
    content = f.read()

# Remove '30-10-50'
content = content.replace("body: JSON.stringify({ kode: '30-10-50' })", "body: JSON.stringify({ kode: document.getElementById('brankas_kode_input') ? document.getElementById('brankas_kode_input').value : '' })")

# Remove urllib.request from api_yasin, it looks like it was partially patched or there was a duplicate api_yasin
old_api_yasin_2 = """@app.route('/api/yasin', methods=['GET'])
@cache.cached(timeout=86400, key_prefix='surah_yasin')
def api_yasin() -> Response | str | tuple[Response, int]:
    \"\"\"Handles requests to the api_yasin endpoint.\"\"\"
    try:
        url = "https://equran.id/api/v2/surat/36"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        # Note: urllib.request may not be fully patched by eventlet. Result is cached for 24h so impact is minimal. Consider using the requests library if blocking becomes an issue.
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode())
            return jsonify(data)
    except Exception:
        # Expected delay or timeout handled by caching 86400s
        app.logger.warning("EQuran API unavailable", exc_info=True)
        return jsonify({"error": "Gagal memuat Surat Yasin. Silakan coba lagi."}), 500"""

new_api_yasin_2 = """@app.route('/api/yasin', methods=['GET'])
@cache.cached(timeout=86400, key_prefix='surah_yasin')
def api_yasin() -> Response | str | tuple[Response, int]:
    \"\"\"Handles requests to the api_yasin endpoint.\"\"\"
    try:
        url = "https://equran.id/api/v2/surat/36"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=(5, 8))
        response.raise_for_status()
        return jsonify(response.json())
    except requests.RequestException:
        app.logger.error("EQuran API unavailable", exc_info=True)
        return jsonify({"error": "Gagal memuat Surat Yasin. Silakan coba lagi."}), 502"""

if old_api_yasin_2 in content:
    content = content.replace(old_api_yasin_2, new_api_yasin_2)


# Check if the other prefetch_emoji_icons uses threading.Thread
old_emoji_2 = """def prefetch_emoji_icons() -> None:
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

    threading.Thread(target=_download, daemon=True).start()"""

new_emoji_2 = """def prefetch_emoji_icons() -> None:
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

if old_emoji_2 in content:
    content = content.replace(old_emoji_2, new_emoji_2)

with open('slb.py', 'w') as f:
    f.write(content)
