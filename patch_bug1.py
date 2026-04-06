import re
import sys

filepath = "sekolah-luar-biasa-55 ( idcloudhost - Layer of Quality Cyber Security - Third Effort ).py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Create emoji prefetcher function
prefetcher_code = """
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
"""

if "def prefetch_emoji_icons():" not in content:
    content = content.replace("def generate_iep():", prefetcher_code + "\ndef generate_iep():")

# Replace add_item_with_icon to read from local file
search_add_item = """    def add_item_with_icon(title, body, rationale, icon_hex):
        url = f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{icon_hex}.png"
        img = None
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                img_data = io.BytesIO(response.read())
                img = RLImage(img_data, width=36, height=36)
        except Exception:
            pass"""

replace_add_item = """    def add_item_with_icon(title, body, rationale, icon_hex):
        emoji_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'emoji_cache')
        file_path = os.path.join(emoji_dir, f"{icon_hex}.png")
        img = None
        try:
            if os.path.exists(file_path):
                img = RLImage(file_path, width=36, height=36)
        except Exception:
            pass"""

if search_add_item in content:
    content = content.replace(search_add_item, replace_add_item)

# Call prefetch_emoji_icons at the bottom
search_startup = """with app.app_context():
    try:
        db.create_all()"""

replace_startup = """with app.app_context():
    try:
        prefetch_emoji_icons()
        db.create_all()"""

if search_startup in content:
    content = content.replace(search_startup, replace_startup)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("BUG-001 Patched.")
