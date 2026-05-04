import re

with open("app.py", "r") as f:
    content = f.read()

# 1. model_getitem
content = content.replace("def model_getitem(self, key):\n    return getattr(self, key)", "def model_getitem(self, key):\n    return getattr(self, key, None)")

# 2. index route
content = content.replace("rendered_home = render_template_string(HOME_HTML, epilepsi_logs=epilepsi_logs, open_modal=request.args.get('open'), is_admin=session.get('is_admin', False))", "rendered_home = render_template_string(HOME_HTML, epilepsi_logs=epilepsi_logs, is_admin=session.get('is_admin', False))")

# 3. fitur_masjid route
search_fitur = r"rendered_content = render_template_string\(FITUR_MASJID_HTML\)\s*return render_template_string\(BASE_LAYOUT,\s*styles=STYLES_HTML,\s*active_page='home',\s*content=rendered_content,\s*is_admin=session\.get\('is_admin',\s*False\),\s*settings=get_settings\(\)\)"
replace_fitur = "return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='home', content=FITUR_MASJID_HTML, is_admin=session.get('is_admin', False), settings=get_settings())"
content = re.sub(search_fitur, replace_fitur, content)

with open("app.py", "w") as f:
    f.write(content)

print("Patch 4 applied.")
