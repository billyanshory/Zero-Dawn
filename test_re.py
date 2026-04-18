import re

with open('slb.py', 'r') as f:
    content = f.read()

emoji = re.search(r'def prefetch_emoji_icons\(\) -> None:(.+?)eventlet\.spawn\(_download\)', content, re.DOTALL)
if emoji:
    print("Found prefetch_emoji_icons")

settings = re.search(r'_settings_lock = threading\.Lock\(\)(.+?)_settings_lock\.release\(\)', content, re.DOTALL)
if settings:
    print("Found get_settings")

yasin = re.search(r'except Exception:\n\s+# Expected delay(.+?)Gagal memuat Surat Yasin', content, re.DOTALL)
if yasin:
    print("Found api_yasin except")
