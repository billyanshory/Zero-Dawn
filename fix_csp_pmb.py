import re

with open("kampus-stie-samarinda-34 ( idcloudhost - Eight Layer of Quality Control ).py", "r") as f:
    code = f.read()

# 1. Fix CSP strictly
# Original line:
# response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data:;"
csp_regex = r"response\.headers\['Content-Security-Policy'\] = \"default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data:;\""
csp_repl = "response.headers['Content-Security-Policy'] = \"default-src 'self' https: data:; script-src 'self' https:; style-src 'self' https:;\""

import re
code = re.sub(csp_regex, csp_repl, code)

# Let's ensure the fallback works and doesn't conflict
# In our previous attempt, we had `email = request.form.get('email')` followed by a check.
# Let's manually verify the unique_suffix logic
pmb_orig = """@app.route('/api/pmb/register', methods=['POST'])
@limiter.limit('3 per minute')
def api_pmb_register():
    try:
        import uuid
        nama = request.form.get('nama')
        email = request.form.get('email', '-')
        nomor_hp = request.form.get('nomor_hp', '-')"""

pmb_repl = """@app.route('/api/pmb/register', methods=['POST'])
@limiter.limit('3 per minute')
def api_pmb_register():
    try:
        import uuid
        nama = request.form.get('nama')
        email = request.form.get('email')
        nomor_hp = request.form.get('nomor_hp')

        # Fallback to unique values if not provided by frontend (to avoid unique constraint violations)
        unique_suffix = str(uuid.uuid4())[:8]
        if not email or email == '-': email = f"no-reply-{unique_suffix}@stiesam.ac.id"
        if not nomor_hp or nomor_hp == '-': nomor_hp = f"0000-{unique_suffix}"
"""
code = code.replace(pmb_orig, pmb_repl)

# 3. Check for PMB html checks
pmb_check_html_orig = """                            <div>
                                <label class="block text-xs font-bold text-gray-500 mb-1">Masukkan Token Pendaftaran</label>
                                <input type="text" id="check_token" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
                            </div>"""

pmb_check_html_repl = """                            <div>
                                <label class="block text-xs font-bold text-gray-500 mb-1">Nama Lengkap Saat Mendaftar</label>
                                <input type="text" id="check_nama" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
                            </div>"""
code = code.replace(pmb_check_html_orig, pmb_check_html_repl)

js_orig = """        async function checkPmb() {
            const token = document.getElementById('check_token').value;
            if(!token) return showToast('Masukkan token pendaftaran', 'error');
            try {
                const res = await fetch('/api/pmb/check?token=' + encodeURIComponent(token));"""

js_repl = """        async function checkPmb() {
            const nama = document.getElementById('check_nama').value;
            if(!nama) return showToast('Masukkan nama pendaftaran', 'error');
            try {
                const res = await fetch('/api/pmb/check?nama=' + encodeURIComponent(nama));"""
code = code.replace(js_orig, js_repl)

api_pmb_check_orig = """@app.route('/api/pmb/check', methods=['GET'])
def api_pmb_check():
    try:
        token = request.args.get('token')
        if not token:
            return jsonify({'error': 'Token tidak boleh kosong'})

        pmb = PendaftaranPMB.query.filter_by(token=token).first()

        if not pmb:
            return jsonify({'error': 'Data pendaftaran tidak ditemukan atau token salah.'})

        return jsonify({
            'nama': pmb.nama,
            'status': pmb.status,
            'npm': pmb.npm_generated if pmb.npm_generated else '-'
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error checking PMB status: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
        return jsonify({'error': 'Terjadi kesalahan sistem.'})"""

api_pmb_check_repl = """@app.route('/api/pmb/check', methods=['GET'])
@login_required
@require_role(['Tata Usaha', 'Admin'])
def api_pmb_check():
    try:
        nama = request.args.get('nama')
        if not nama:
            return jsonify({'error': 'Nama tidak boleh kosong'})

        # Case insensitive exact match or like query
        pmb = PendaftaranPMB.query.filter(func.lower(PendaftaranPMB.nama) == func.lower(nama)).order_by(PendaftaranPMB.id.desc()).first()

        if not pmb:
            return jsonify({'error': 'Data pendaftaran tidak ditemukan.'})

        return jsonify({
            'nama': pmb.nama,
            'status': pmb.status,
            'npm': pmb.npm_generated if pmb.npm_generated else '-'
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error checking PMB status: {e}", exc_info=True)
        return jsonify({'error': 'Terjadi kesalahan sistem.'})"""
code = code.replace(api_pmb_check_orig, api_pmb_check_repl)

with open("kampus-stie-samarinda-34 ( idcloudhost - Eight Layer of Quality Control ).py", "w") as f:
    f.write(code)
