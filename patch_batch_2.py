import re

with open("app.py", "r") as f:
    content = f.read()

# 1. Insert IDUL_ADHA_THEME
# Look for the end of IRMA_STYLES
pattern_irma = r'(IRMA_STYLES\s*=\s*""".*?""")'
theme_dict = """

IDUL_ADHA_THEME = {'nav_bg': 'bg-gradient-to-r from-[#78350f] to-[#451a03] shadow-lg', 'icon_bg': 'bg-[#fcd34d]/20', 'icon_text': 'text-[#fcd34d]', 'title_text': 'text-[#fcd34d]', 'link_hover': 'hover:text-[#fcd34d]', 'link_active': 'text-[#fcd34d] font-bold', 'btn_primary': 'bg-[#fcd34d] text-[#451a03] hover:bg-white', 'bottom_nav_bg': 'bg-gradient-to-r from-[#78350f] to-[#451a03] border-t border-[#fcd34d]/20', 'bottom_active': 'text-[#fcd34d]', 'bottom_btn_bg': 'bg-[#fcd34d]', 'bottom_btn_text': 'text-[#451a03]', 'bottom_text_inactive': 'text-[#d4a373]'}
"""

if "IDUL_ADHA_THEME = {" not in content:
    content = re.sub(pattern_irma, r'\1' + theme_dict, content, flags=re.DOTALL)

# 2. Add theme=IDUL_ADHA_THEME to the 7 specific outer render_template_string(BASE_LAYOUT, ... calls
# absen panitia
content = re.sub(
    r"(return render_template_string\(BASE_LAYOUT,\s*styles=STYLES_HTML,\s*active_page='idul-adha',\s*content=rendered_content,\s*is_admin=session\.get\('is_admin',\s*False\),\s*settings=settings\))",
    r"return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', theme=IDUL_ADHA_THEME, content=rendered_content, is_admin=session.get('is_admin', False), settings=settings)",
    content
)

# Other 6 pages which have settings=get_settings()
content = re.sub(
    r"(return render_template_string\(BASE_LAYOUT,\s*styles=STYLES_HTML,\s*active_page='idul-adha',\s*content=rendered_content,\s*is_admin=session\.get\('is_admin',\s*False\),\s*settings=get_settings\(\)\))",
    r"return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', theme=IDUL_ADHA_THEME, content=rendered_content, is_admin=session.get('is_admin', False), settings=get_settings())",
    content
)

with open("app.py", "w") as f:
    f.write(content)

print("Patch 2 applied.")
