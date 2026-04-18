import re

with open('slb.py', 'r') as f:
    content = f.read()

# Try another search pattern for api_yasin
old_yasin = """@app.route('/api/yasin', methods=['GET'])
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

new_yasin = """@app.route('/api/yasin', methods=['GET'])
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

if old_yasin in content:
    content = content.replace(old_yasin, new_yasin)
elif "req = urllib.request.Request(url" in content:
    # Manual regex replace for api_yasin body
    content = re.sub(
        r"req = urllib\.request\.Request\(url, headers=\{'User-Agent': 'Mozilla/5\.0'\}\)\n\s+# Note: urllib\.request may not be fully patched by eventlet\..+?\n\s+with urllib\.request\.urlopen\(req, timeout=8\) as response:\n\s+data = json\.loads\(response\.read\(\)\.decode\(\)\)\n\s+return jsonify\(data\)",
        r"response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=(5, 8))\n        response.raise_for_status()\n        return jsonify(response.json())",
        content,
        flags=re.DOTALL
    )
    content = re.sub(
        r"except Exception:\n\s+# Expected delay or timeout handled by caching 86400s\n\s+app\.logger\.warning\(\"EQuran API unavailable\", exc_info=True\)\n\s+return jsonify\(\{\"error\": \"Gagal memuat Surat Yasin\. Silakan coba lagi\.\"\}\), 500",
        r"except requests.RequestException:\n        app.logger.error(\"EQuran API unavailable\", exc_info=True)\n        return jsonify({\"error\": \"Gagal memuat Surat Yasin. Silakan coba lagi.\"}), 502",
        content,
        flags=re.DOTALL
    )

# Try another search pattern for emoji threading
if "threading.Thread(target=_download, daemon=True).start()" in content:
    content = content.replace("threading.Thread(target=_download, daemon=True).start()", "eventlet.spawn(_download)")


with open('slb.py', 'w') as f:
    f.write(content)
