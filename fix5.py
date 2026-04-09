import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # 5. Route-level caching for semi-static pages
    # The instructions say: "Add @cache.cached() decorators to every semi-static route. For the SLB category pages, use a timeout of 3600 seconds... with key_prefix... For data-driven pages like the home page and dashboards, use a shorter timeout of 30 to 60 seconds with a key that includes both the user's role and their anak_id."

    # SLB Tunatetra
    if "@cache.cached(timeout=3600, key_prefix=lambda: f\"tunanetra_{session.get('peran','anon')}\")" not in content:
        content = content.replace(
            "@app.route('/slb/tunanetra')",
            "@app.route('/slb/tunanetra')\n@cache.cached(timeout=3600, key_prefix=lambda: f\"tunanetra_{session.get('peran','anon')}\")"
        )
    # SLB Tunarungu
    if "@cache.cached(timeout=3600, key_prefix=lambda: f\"tunarungu_{session.get('peran','anon')}\")" not in content:
        content = content.replace(
            "@app.route('/slb/tunarungu')",
            "@app.route('/slb/tunarungu')\n@cache.cached(timeout=3600, key_prefix=lambda: f\"tunarungu_{session.get('peran','anon')}\")"
        )
    # SLB Tunagrahita
    if "@cache.cached(timeout=3600, key_prefix=lambda: f\"tunagrahita_{session.get('peran','anon')}\")" not in content:
        content = content.replace(
            "@app.route('/slb/tunagrahita')",
            "@app.route('/slb/tunagrahita')\n@cache.cached(timeout=3600, key_prefix=lambda: f\"tunagrahita_{session.get('peran','anon')}\")"
        )
    # SLB Tunadaksa
    if "@cache.cached(timeout=3600, key_prefix=lambda: f\"tunadaksa_{session.get('peran','anon')}\")" not in content:
        content = content.replace(
            "@app.route('/slb/tunadaksa')",
            "@app.route('/slb/tunadaksa')\n@cache.cached(timeout=3600, key_prefix=lambda: f\"tunadaksa_{session.get('peran','anon')}\")"
        )
    # SLB Tunalaras
    if "@cache.cached(timeout=3600, key_prefix=lambda: f\"tunalaras_{session.get('peran','anon')}\")" not in content:
        content = content.replace(
            "@app.route('/slb/tunalaras')",
            "@app.route('/slb/tunalaras')\n@cache.cached(timeout=3600, key_prefix=lambda: f\"tunalaras_{session.get('peran','anon')}\")"
        )
    # SLB Tunaganda
    if "@cache.cached(timeout=3600, key_prefix=lambda: f\"tunaganda_{session.get('peran','anon')}\")" not in content:
        content = content.replace(
            "@app.route('/slb/tunaganda')",
            "@app.route('/slb/tunaganda')\n@cache.cached(timeout=3600, key_prefix=lambda: f\"tunaganda_{session.get('peran','anon')}\")"
        )

    # Home Page
    if "@cache.cached(timeout=60, key_prefix=lambda: f\"home_{session.get('peran','anon')}_{session.get('anak_id','none')}\")" not in content:
        content = content.replace(
            "def index():\n    # Halaman Utama\n    from datetime import datetime",
            "@cache.cached(timeout=60, key_prefix=lambda: f\"home_{session.get('peran','anon')}_{session.get('anak_id','none')}\")\ndef index():\n    # Halaman Utama\n    from datetime import datetime"
        )

    # Dashboards
    if "@cache.cached(timeout=60, key_prefix=lambda: f\"kepala_sekolah_{session.get('peran','anon')}_{session.get('anak_id','none')}\")" not in content:
        content = content.replace(
            "def kepala_sekolah_dashboard():\n",
            "@cache.cached(timeout=60, key_prefix=lambda: f\"kepala_sekolah_{session.get('peran','anon')}_{session.get('anak_id','none')}\")\ndef kepala_sekolah_dashboard():\n"
        )

    if "@cache.cached(timeout=60, key_prefix=lambda: f\"orang_tua_dashboard_{session.get('peran','anon')}_{session.get('anak_id','none')}\")" not in content:
        content = content.replace(
            "def orang_tua_dashboard():\n",
            "@cache.cached(timeout=60, key_prefix=lambda: f\"orang_tua_dashboard_{session.get('peran','anon')}_{session.get('anak_id','none')}\")\ndef orang_tua_dashboard():\n"
        )

    if "@cache.cached(timeout=60, key_prefix=lambda: f\"validator_dashboard_{session.get('peran','anon')}_{session.get('anak_id','none')}\")" not in content:
        content = content.replace(
            "def validator_dashboard():\n",
            "@cache.cached(timeout=60, key_prefix=lambda: f\"validator_dashboard_{session.get('peran','anon')}_{session.get('anak_id','none')}\")\ndef validator_dashboard():\n"
        )


    # Cache-Control headers
    after_request_code = """
@app.after_request
def add_cache_headers(response):
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=86400'
    elif 'application/json' in response.content_type:
        response.headers['Cache-Control'] = 'no-cache'
    elif 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'public, max-age=60'
    return response
"""
    if "def add_cache_headers(response):" not in content:
        content = content.replace(
            "@app.after_request\ndef gzipper(response):",
            after_request_code + "\n@app.after_request\ndef gzipper(response):"
        )
        if "def add_cache_headers(response):" not in content:
            # Maybe there is no gzipper
            # Let's just put it near the bottom before the main block
            content = content.replace(
                "if __name__ == '__main__':",
                after_request_code + "\nif __name__ == '__main__':"
            )

    with open(filepath, 'w') as f:
        f.write(content)

process_file("app.py")
