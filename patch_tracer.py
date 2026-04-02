import re

with open('kampus-stie-samarinda-35 ( idcloudhost - Ninth Layer of Quality Control ).py', 'r') as f:
    code = f.read()

# 1. Modify HOME_HTML to add dynamic CAPTCHA to tracer study modal
# Find tracer study form in HOME_HTML and replace the CAPTCHA logic

tracer_captcha_search = """                        <div class="mb-4">
                            <label class="block text-xs font-bold text-gray-500 mb-2">Berapa hasil dari 2 + 2? (CAPTCHA)</label>
                            <input type="text" name="captcha_answer" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
                        </div>"""

tracer_captcha_replace = """                        <div class="mb-4">
                            <label class="block text-xs font-bold text-gray-500 mb-2" id="captcha-question">Berapa hasil dari ...?</label>
                            <input type="hidden" name="captcha_expected" id="captcha-expected" value="">
                            <input type="text" name="captcha_answer" required placeholder="Masukkan angka jawaban" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
                        </div>
                        <script>
                            function generateCaptcha() {
                                const num1 = Math.floor(Math.random() * 10) + 1;
                                const num2 = Math.floor(Math.random() * 10) + 1;
                                document.getElementById('captcha-question').innerText = `Berapa hasil dari ${num1} + ${num2}? (CAPTCHA)`;
                                document.getElementById('captcha-expected').value = num1 + num2;
                            }
                            // Generate on modal open or script load
                            generateCaptcha();
                        </script>"""

code = code.replace(tracer_captcha_search, tracer_captcha_replace)


# 2. Update api_tracer_submit to use dynamic CAPTCHA and check User.nama, and call cache.clear()
api_tracer_search = """        captcha = request.form.get('captcha_answer')

        if str(captcha).strip() != '4':
            flash("Validasi keamanan gagal. Jawaban CAPTCHA salah.", "error")
            return redirect(request.referrer or url_for('index'))

        if not all([nama_lengkap, npm_input, tahun_lulus, program_studi, status_pekerjaan]):
            flash("Field yang diwajibkan harus diisi.", "error")
            return redirect(request.referrer or url_for('index'))

        user = User.query.filter_by(username=npm_input).first()
        if not user or user.status_akademik != 'Lulus':
            flash('Validasi Alumni Gagal: NPM tidak ditemukan atau status belum Lulus.', 'error')
            return redirect(request.referrer or url_for('index'))"""

api_tracer_replace = """        captcha = request.form.get('captcha_answer')
        expected_captcha = request.form.get('captcha_expected')

        if not expected_captcha or str(captcha).strip() != str(expected_captcha).strip():
            flash("Validasi keamanan gagal. Jawaban CAPTCHA salah.", "error")
            return redirect(request.referrer or url_for('index'))

        if not all([nama_lengkap, npm_input, tahun_lulus, program_studi, status_pekerjaan]):
            flash("Field yang diwajibkan harus diisi.", "error")
            return redirect(request.referrer or url_for('index'))

        user = User.query.filter_by(username=npm_input).first()
        if not user or user.status_akademik != 'Lulus':
            flash('Validasi Alumni Gagal: NPM tidak ditemukan atau status belum Lulus.', 'error')
            return redirect(request.referrer or url_for('index'))

        if user.nama.lower() != nama_lengkap.lower():
            flash('Validasi Alumni Gagal: Nama lengkap tidak cocok dengan data pangkalan data.', 'error')
            return redirect(request.referrer or url_for('index'))"""

code = code.replace(api_tracer_search, api_tracer_replace)

api_tracer_cache_search = """        db.session.add(Notification(npm=os.environ.get('TU_USERNAME', 'tatausaha'), message=f"Data Tracer Study baru dari NPM {npm_input}."))
        db.session.commit()
        pass # no cache clear

        flash("Data Tracer Study berhasil dikirim! Terima kasih atas partisipasi Anda.", "success")"""

api_tracer_cache_replace = """        db.session.add(Notification(npm=os.environ.get('TU_USERNAME', 'tatausaha'), message=f"Data Tracer Study baru dari NPM {npm_input}."))
        db.session.commit()
        cache.clear()

        flash("Data Tracer Study berhasil dikirim! Terima kasih atas partisipasi Anda.", "success")"""

code = code.replace(api_tracer_cache_search, api_tracer_cache_replace)

with open('kampus-stie-samarinda-35 ( idcloudhost - Ninth Layer of Quality Control ).py', 'w') as f:
    f.write(code)

print("Patch applied for api_tracer_submit.")
