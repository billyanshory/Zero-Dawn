import re

with open('app.py', 'r') as f:
    content = f.read()

# 1. Pass theme dictionary in orang_tua_dashboard route
ot_route_old = """    return cached_render('BASE_LAYOUT', BASE_LAYOUT, styles=STYLES_HTML, active_page='home', content=ORANG_TUA_HTML, hide_nav=False, full_width=True, is_admin=session.get('is_admin', False), settings=get_settings(), needs_socketio=True, anak_id=anak_id, peran=peran, profil_medis=profil_medis, anak_nama=anak_nama, csrf_token=csrf.generate_csrf)"""
ot_route_new = """    theme = {'nav_bg': 'bg-rose-50', 'icon_bg': 'bg-rose-100', 'icon_text': 'text-rose-600', 'title_text': 'text-rose-700', 'btn_primary': 'bg-rose-500 text-white hover:bg-rose-600', 'bottom_nav_bg': 'bg-rose-50/90 backdrop-blur-md', 'bottom_btn_bg': 'bg-rose-500', 'bottom_active': 'text-rose-600', 'bottom_text_inactive': 'text-rose-400', 'link_hover': 'hover:text-rose-600', 'link_active': 'text-rose-700 border-b-2 border-rose-500'}
    return cached_render('BASE_LAYOUT', BASE_LAYOUT, styles=STYLES_HTML, active_page='home', content=ORANG_TUA_HTML, hide_nav=False, full_width=True, is_admin=session.get('is_admin', False), settings=get_settings(), needs_socketio=True, anak_id=anak_id, peran=peran, profil_medis=profil_medis, anak_nama=anak_nama, csrf_token=csrf.generate_csrf, theme=theme)"""
content = content.replace(ot_route_old, ot_route_new)

# 2. Update BASE_LAYOUT theme variables
theme_vars_old = """    {% set t_nav_bg = theme.nav_bg if theme and theme.nav_bg else 'glass-nav' %}
    {% set t_icon_bg = theme.icon_bg if theme and theme.icon_bg else 'bg-emerald-100' %}
    {% set t_icon_text = theme.icon_text if theme and theme.icon_text else 'text-emerald-600' %}
    {% set t_title_text = theme.title_text if theme and theme.title_text else 'text-emerald-600' %}
    {% set t_link_hover = theme.link_hover if theme and theme.link_hover else 'hover:text-emerald-600' %}
    {% set t_link_active = theme.link_active if theme and theme.link_active else 'text-emerald-600 font-bold' %}
    {% set t_btn_primary = theme.btn_primary if theme and theme.btn_primary else 'bg-emerald-500 text-white hover:bg-emerald-600' %}
    {% set t_bottom_bg = theme.bottom_nav_bg if theme and theme.bottom_nav_bg else 'glass-bottom' %}
    {% set t_bottom_active = theme.bottom_active if theme and theme.bottom_active else 'text-emerald-600' %}
    {% set t_bottom_btn_bg = theme.bottom_btn_bg if theme and theme.bottom_btn_bg else 'bg-emerald-500' %}
    {% set t_bottom_btn_text = theme.bottom_btn_text if theme and theme.bottom_btn_text else 'text-emerald-600' %}
    {% set t_bottom_text_inactive = theme.bottom_text_inactive if theme and theme.bottom_text_inactive else 'text-gray-500' %}"""

# Let's read the exact content around these lines just to be safe
with open('app.py', 'w') as f:
    f.write(content)
print("Done step 1.")
