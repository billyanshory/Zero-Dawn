import re

filepath = "sekolah-luar-biasa-55 ( idcloudhost - Layer of Quality Cyber Security - Third Effort ).py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# I messed up the replacement by inserting prefetch_emoji_icons before "def generate_iep():"
# but there were decorators before generate_iep. Wait, the replacement string was:
# content = content.replace("def generate_iep():", prefetcher_code + "\ndef generate_iep():")
# In the original file, it was:
# @app.route('/guru/iep', methods=['POST'])
# @limiter.limit("10 per hour")
# @cache.cached(timeout=300, key_prefix=iep_cache_key)
# def generate_iep():
# So the decorators remained, but `import urllib.request` was injected between the decorators and the function def!
# That causes a SyntaxError.

# Let's fix it by moving the decorators down or moving the prefetch_emoji_icons function out.
# Let's extract the prefetch_emoji_icons function and place it above the decorators.

search_str = """@app.route('/guru/iep', methods=['POST'])
@limiter.limit("10 per hour")
@cache.cached(timeout=300, key_prefix=iep_cache_key)

import urllib.request
import os

def prefetch_emoji_icons():
    emoji_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'emoji_cache')
    os.makedirs(emoji_dir, exist_ok=True)
    # The hex codes identified from the context
    hex_codes = ['1f441', '1f442', '1f3c3', '1f590', '1f3af', '1f5e3', '2753']
    for icon_hex in hex_codes:
        file_path = os.path.join(emoji_dir, f"{icon_hex}.png")
        if not os.path.exists(file_path):
            url = f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{icon_hex}.png"
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    with open(file_path, 'wb') as out_f:
                        out_f.write(response.read())
            except Exception as e:
                app.logger.error(f"Failed to prefetch emoji {icon_hex}: {e}")

# Note: this will be called in with app.app_context(): later.

def generate_iep():"""

replace_str = """
import urllib.request
import os

def prefetch_emoji_icons():
    emoji_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'emoji_cache')
    os.makedirs(emoji_dir, exist_ok=True)
    # The hex codes identified from the context
    hex_codes = ['1f441', '1f442', '1f3c3', '1f590', '1f3af', '1f5e3', '2753']
    for icon_hex in hex_codes:
        file_path = os.path.join(emoji_dir, f"{icon_hex}.png")
        if not os.path.exists(file_path):
            url = f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{icon_hex}.png"
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    with open(file_path, 'wb') as out_f:
                        out_f.write(response.read())
            except Exception as e:
                app.logger.error(f"Failed to prefetch emoji {icon_hex}: {e}")

@app.route('/guru/iep', methods=['POST'])
@limiter.limit("10 per hour")
@cache.cached(timeout=300, key_prefix=iep_cache_key)
def generate_iep():"""

if search_str in content:
    content = content.replace(search_str, replace_str)
else:
    print("Could not find the exact match to fix.")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
