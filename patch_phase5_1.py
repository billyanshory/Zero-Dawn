import re

with open("app.py", "r") as f:
    content = f.read()

# 1. Imports: add `import requests` if not exists, though the user noted it was at 6965.
# Let's first move it from the middle of the file to the top.
content = content.replace("import requests\n", "")
if "import requests" not in content:
    content = content.replace("import urllib.request", "import urllib.request\nimport requests")

# 2. Refactor api_yasin
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
