import re

with open('kampus-stie-samarinda-35 ( idcloudhost - Ninth Layer of Quality Control ).py', 'r') as f:
    code = f.read()

# 1. Modify api_pmb_check to add api_pmb_status logic and restrict api_pmb_check

pmb_routes_search = """@app.route('/api/pmb/check', methods=['GET'])
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
        flash(GENERIC_ERROR_MSG, "error")
        return jsonify({'error': 'Terjadi kesalahan sistem.'})"""

pmb_routes_replace = """@app.route('/api/pmb/status', methods=['GET'])
@limiter.limit("5 per minute")
def api_pmb_status():
    try:
        nama = request.args.get('nama')
        if not nama:
            return jsonify({'error': 'Nama tidak boleh kosong'})

        pmb = PendaftaranPMB.query.filter(func.lower(PendaftaranPMB.nama) == func.lower(nama)).order_by(PendaftaranPMB.id.desc()).first()

        if not pmb:
            return jsonify({'error': 'Data pendaftaran tidak ditemukan.'})

        return jsonify({
            'nama': pmb.nama,
            'status': pmb.status,
            'npm': '-'  # Jangan membocorkan NPM di rute publik
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error checking PMB status: {e}", exc_info=True)
        return jsonify({'error': 'Terjadi kesalahan sistem.'})

@app.route('/api/pmb/check', methods=['GET'])
@login_required
@require_role(['Tata Usaha', 'Admin'])
def api_pmb_check():
    try:
        nama = request.args.get('nama')
        if not nama:
            return jsonify({'error': 'Nama tidak boleh kosong'})

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
        app.logger.error(f"Error checking PMB check: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
        return jsonify({'error': 'Terjadi kesalahan sistem.'})"""

code = code.replace(pmb_routes_search, pmb_routes_replace)

# 2. Add 'api_pmb_status' to whitelist in global_gatekeeper
gatekeeper_search = """    if request.endpoint in ['index', 'login', 'logout', 'static', 'api_pmb_register', 'api_pmb_check', 'service_worker', 'manifest', 'fitur_masjid', 'donate', 'emergency', 'prayer_times_api', 'api_yasin', 'therapy_log']:
        return"""

gatekeeper_replace = """    if request.endpoint in ['index', 'login', 'logout', 'static', 'api_pmb_register', 'api_pmb_check', 'api_pmb_status', 'service_worker', 'manifest', 'fitur_masjid', 'donate', 'emergency', 'prayer_times_api', 'api_yasin', 'therapy_log']:
        return"""

code = code.replace(gatekeeper_search, gatekeeper_replace)

# 3. Modify HOME_HTML to call /api/pmb/status instead of /api/pmb/check
home_html_search = """                            const res = await fetch('/api/pmb/check?nama=' + encodeURIComponent(nama));"""

home_html_replace = """                            const res = await fetch('/api/pmb/status?nama=' + encodeURIComponent(nama));"""

code = code.replace(home_html_search, home_html_replace)

with open('kampus-stie-samarinda-35 ( idcloudhost - Ninth Layer of Quality Control ).py', 'w') as f:
    f.write(code)

print("Patch applied for api_pmb_status and api_pmb_check.")
