import re

with open("sekolah_luar_biasa.py", "r") as f:
    content = f.read()

# fix the duplicate imports correctly
# Find the FIRST occurrence and leave it, remove subsequent ones.
def deduplicate_import(import_stmt, text):
    parts = text.split(import_stmt + "\n")
    if len(parts) <= 2: return text
    return (import_stmt + "\n").join([parts[0], "".join(parts[1:])])

content = deduplicate_import("from flask import current_app", content)
content = deduplicate_import("import urllib.request", content)
content = deduplicate_import("import io", content)
content = deduplicate_import("from PIL import Image", content)

with open("sekolah_luar_biasa.py", "w") as f:
    f.write(content)
