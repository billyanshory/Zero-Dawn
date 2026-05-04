import re

with open("app.py", "r") as f:
    content = f.read()

content = re.sub(
    r"(return render_template_string\(BASE_LAYOUT,\s*styles=STYLES_HTML,\s*active_page='idul-adha',\s*content=IDUL_ADHA_PANDUAN_HTML,\s*is_admin=session\.get\('is_admin',\s*False\),\s*settings=get_settings\(\)\))",
    r"return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', theme=IDUL_ADHA_THEME, content=IDUL_ADHA_PANDUAN_HTML, is_admin=session.get('is_admin', False), settings=get_settings())",
    content
)

with open("app.py", "w") as f:
    f.write(content)

print("Patch panduan applied.")
