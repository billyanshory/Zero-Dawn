import re

with open('app.py', 'r') as f:
    content = f.read()

# 1. Update orang_tua_dashboard route
ot_route_old = """@app.route('/orang-tua')
def orang_tua_dashboard():
    if session.get('peran') not in ['orang_tua', 'kepala_sekolah'] and not session.get('is_admin'):
        return redirect(url_for('index'))
    return cached_render('BASE_LAYOUT', BASE_LAYOUT, styles=STYLES_HTML, active_page='home', content=ORANG_TUA_HTML, hide_nav=False, full_width=True, is_admin=session.get('is_admin', False), settings=get_settings(), needs_socketio=True)"""
ot_route_new = """@app.route('/orang-tua')
def orang_tua_dashboard():
    if session.get('peran') not in ['orang_tua', 'kepala_sekolah'] and not session.get('is_admin'):
        return redirect(url_for('index'))

    anak_id = session.get('anak_id')
    peran = session.get('peran', '')
    profil_medis = ProfilMedisSiswa.query.filter_by(siswa_id=anak_id).first() if anak_id else None
    anak_nama = session.get('anak_nama', '')

    return cached_render('BASE_LAYOUT', BASE_LAYOUT, styles=STYLES_HTML, active_page='home', content=ORANG_TUA_HTML, hide_nav=False, full_width=True, is_admin=session.get('is_admin', False), settings=get_settings(), needs_socketio=True, anak_id=anak_id, peran=peran, profil_medis=profil_medis, anak_nama=anak_nama, csrf_token=csrf.generate_csrf)"""
content = content.replace(ot_route_old, ot_route_new)

# 2. Add const script to ORANG_TUA_HTML (check if it exists first)
# Let's see the beginning of ORANG_TUA_HTML
match = re.search(r'ORANG_TUA_HTML\s*=\s*"""(.*?)"""', content, re.DOTALL)
if match:
    ot_html = match.group(1)
    if 'const userPeran' not in ot_html:
        ot_html_new = f"""
<script>
    const userPeran = '{{{{ peran }}}}';
    const userAnakId = {{{{ anak_id|default('null') }}}};
</script>
{ot_html}"""
        content = content.replace(f'ORANG_TUA_HTML = """{ot_html}"""', f'ORANG_TUA_HTML = """{ot_html_new}"""')

# 3. Add alert to btnSaveMedical
btn_save_old = """            btnSaveMedical.addEventListener('click', () => {
                if(!userAnakId) return;"""
btn_save_new = """            btnSaveMedical.addEventListener('click', () => {
                if(!userAnakId) {
                    alert('Sesi login tidak valid. Silakan login ulang.');
                    return;
                }"""
content = content.replace(btn_save_old, btn_save_new)

with open('app.py', 'w') as f:
    f.write(content)
print("Done patching.")
