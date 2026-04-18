with open("app.py", "r") as f:
    content = f.read()

yasin_old = """def api_yasin() -> Response | str | tuple[Response, int]:
    \"\"\"Handles requests to the api_yasin endpoint.\"\"\"
    try:
        url = "https://equran.id/api/v2/surat/36"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        # Note: urllib.request may not be fully patched by eventlet. Result is cached for 24h so impact is minimal. Consider using the requests library if blocking becomes an issue.
        # TODO: Refactor to requests to avoid eventlet blocking
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return jsonify(data)
    except Exception:
        app.logger.error('Yasin fetch failed', exc_info=True)
        return jsonify({'error': 'Gagal memuat surat Yasin.'}), 500"""

yasin_new = """def api_yasin() -> Response | str | tuple[Response, int]:
    \"\"\"Handles requests to the api_yasin endpoint.\"\"\"
    try:
        url = "https://equran.id/api/v2/surat/36"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=(5, 8))
        response.raise_for_status()
        return jsonify(response.json())
    except requests.RequestException:
        app.logger.error('Yasin fetch failed', exc_info=True)
        return jsonify({'error': 'Gagal memuat surat Yasin.'}), 502"""

content = content.replace(yasin_old, yasin_new)

with open("app.py", "w") as f:
    f.write(content)
