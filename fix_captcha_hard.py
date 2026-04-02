import re

with open("kampus-stie-samarinda-34 ( idcloudhost - Eight Layer of Quality Control ).py", "r") as f:
    code = f.read()

# Let's search for "Tracer Study" in the HTML string and inject it manually
# Look for <textarea name="saran"
import sys

idx = code.find('<textarea name="saran"')
if idx == -1:
    print("Could not find saran textarea")
    sys.exit(1)

# Find the end of that div
end_div_idx = code.find('</div>', idx)
if end_div_idx == -1:
    print("Could not find end of div")
    sys.exit(1)

captcha_html = """
                        <div class="mb-4">
                            <label class="block text-xs font-bold text-gray-500 mb-2">Berapa hasil dari 2 + 2? (CAPTCHA)</label>
                            <input type="text" name="captcha_answer" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
                        </div>"""

# Insert the captcha html right after the end of the div
new_code = code[:end_div_idx + 6] + captcha_html + code[end_div_idx + 6:]

# Let's also check for 'jenis_surat' validation in mahasiswa_surat_request
jenis_surat_orig = """@app.route('/mahasiswa/surat/request', methods=['POST'])
@login_required
@require_role(['Mahasiswa'])
def mahasiswa_surat_request():
    npm = session.get('npm') or session.get('username')
    if not npm:
        return redirect(url_for('index', open='modal-login'))
    try:
        item = SuratOtomatis(
            npm=npm,
            jenis_surat=request.form['jenis_surat'],
            keterangan=request.form['keterangan']
        )
        db.session.add(item)
        db.session.add(Notification(npm=os.environ.get('TU_USERNAME', 'tatausaha'), message=f"Permohonan surat baru dari NPM {npm}."))
        db.session.commit()
        pass

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error requesting surat: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return redirect(url_for('irma_dashboard', open='modal-permohonan-surat'))"""

jenis_surat_repl = """@app.route('/mahasiswa/surat/request', methods=['POST'])
@login_required
@require_role(['Mahasiswa'])
def mahasiswa_surat_request():
    npm = session.get('npm') or session.get('username')
    if not npm:
        return redirect(url_for('index', open='modal-login'))
    try:
        jenis_surat = request.form['jenis_surat']
        valid_surat = [
            "Surat Keterangan Aktif Kuliah",
            "Surat Pengantar Magang",
            "Surat Pengantar Riset",
            "Surat Cuti Akademik"
        ]
        if jenis_surat not in valid_surat:
            flash("Jenis surat tidak valid.", "error")
            return redirect(url_for('irma_dashboard', open='modal-permohonan-surat'))

        item = SuratOtomatis(
            npm=npm,
            jenis_surat=jenis_surat,
            keterangan=request.form['keterangan']
        )
        db.session.add(item)
        db.session.add(Notification(npm=os.environ.get('TU_USERNAME', 'tatausaha'), message=f"Permohonan surat baru dari NPM {npm}."))
        db.session.commit()
        cache.clear()

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error requesting surat: {e}", exc_info=True)
        flash(GENERIC_ERROR_MSG, "error")
    return redirect(url_for('irma_dashboard', open='modal-permohonan-surat'))"""
new_code = new_code.replace(jenis_surat_orig, jenis_surat_repl)

with open("kampus-stie-samarinda-34 ( idcloudhost - Eight Layer of Quality Control ).py", "w") as f:
    f.write(new_code)

print("CAPTCHA and jenis_surat hard-patched")
