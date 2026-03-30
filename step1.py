import re

with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "r") as f:
    content = f.read()

# 1. Add imports
import_insert = "from flask_limiter.util import get_remote_address\nfrom flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user\nfrom sqlalchemy.orm import joinedload"
content = content.replace("from flask_limiter.util import get_remote_address", import_insert)

# 2. Move helpers
# The block starts at PrayTimes class and ends before "def model_getitem" or similar.
# Let's find exact bounds for the cut.
start_str = "class PrayTimes:"
end_str = "def model_getitem(self, key):"

start_idx = content.find(start_str)
end_idx = content.find(end_str)

if start_idx != -1 and end_idx != -1:
    block_to_move = content[start_idx:end_idx]

    # Remove block
    content = content[:start_idx] + content[end_idx:]

    # Insert before if __name__ == '__main__':
    main_idx = content.find("if __name__ == '__main__':")

    header = "\n# ============================================================================\n# ZONA HELPER FUNGSI BAWAH\n# ============================================================================\n\n"
    content = content[:main_idx] + header + block_to_move + content[main_idx:]

# 3. Add Comments for routes
content = content.replace("@app.route('/mahasiswa')", "# ============================================================================\n# RUTE MAHASISWA\n# ============================================================================\n@app.route('/mahasiswa')")
content = content.replace("@app.route('/dosen')", "# ============================================================================\n# RUTE DOSEN\n# ============================================================================\n@app.route('/dosen')")
content = content.replace("@app.route('/tu_dashboard')", "# ============================================================================\n# RUTE TATA USAHA\n# ============================================================================\n@app.route('/tu_dashboard')")

# 4. Render Page Helper
render_page_func = """
def render_page(template, active_page, theme=None, content_kwargs=None, hide_nav=False, full_width=False):
    if content_kwargs is None:
        content_kwargs = {}

    settings = get_settings()
    is_admin = session.get('is_admin', False)

    rendered_content = render_template_string(template, open_modal=request.args.get('open'), is_admin=is_admin, settings=settings, **content_kwargs)

    return render_template_string(BASE_LAYOUT,
                                  styles=STYLES_HTML + (RAMADHAN_STYLES if active_page == 'ramadhan' else (IRMA_STYLES if active_page == 'irma' else '')),
                                  active_page=active_page,
                                  theme=theme,
                                  content=rendered_content,
                                  hide_nav=hide_nav,
                                  full_width=full_width,
                                  is_admin=is_admin,
                                  settings=settings)
"""

content = content.replace("# ============================================================================\n# ZONA HELPER FUNGSI BAWAH\n# ============================================================================\n\n", "# ============================================================================\n# ZONA HELPER FUNGSI BAWAH\n# ============================================================================\n" + render_page_func + "\n")

# Replace render_template_string in routes with render_page
# index
content = content.replace("rendered_home = render_template_string(HOME_HTML, epilepsi_logs=epilepsi_logs, verified_alumni_list=verified_alumni_list, open_modal=request.args.get('open'), is_admin=session.get('is_admin', False), settings=get_settings())\n    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='home', content=rendered_home, is_admin=session.get('is_admin', False), settings=get_settings())", "return render_page(HOME_HTML, 'home', content_kwargs={'epilepsi_logs': epilepsi_logs, 'verified_alumni_list': verified_alumni_list})")

with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "w") as f:
    f.write(content)
