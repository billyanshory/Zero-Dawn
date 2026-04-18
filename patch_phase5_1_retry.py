import re

with open("app.py", "r") as f:
    content = f.read()

yasin_pattern = r"def api_yasin\(\) -> Response \| str \| tuple\[Response, int\]:.*?return jsonify\(\{'error': 'Gagal memuat surat Yasin\.'\}\), 500"
yasin_replacement = """def api_yasin() -> Response | str | tuple[Response, int]:
    \"\"\"Handles requests to the api_yasin endpoint.\"\"\"
    try:
        url = "https://equran.id/api/v2/surat/36"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=(5, 8))
        response.raise_for_status()
        return jsonify(response.json())
    except requests.RequestException:
        app.logger.error('Yasin fetch failed', exc_info=True)
        return jsonify({'error': 'Gagal memuat surat Yasin.'}), 502"""

content = re.sub(yasin_pattern, yasin_replacement, content, flags=re.DOTALL)

with open("app.py", "w") as f:
    f.write(content)
