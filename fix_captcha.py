import re

with open("kampus-stie-samarinda-34 ( idcloudhost - Eight Layer of Quality Control ).py", "r") as f:
    code = f.read()

# Fix the captcha on the HTML form
# Find the exact tracer study form location in HTML
html_tracer_form = """                        <div class="mb-4">
                            <label class="block text-xs font-bold text-gray-500 mb-2">Saran / Masukan untuk Kampus</label>
                            <textarea name="saran" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm h-20 focus:outline-none focus:ring-2 focus:ring-sky-500"></textarea>
                        </div>
                        <button type="submit" class="w-full bg-sky-500 text-white font-bold py-3 rounded-xl hover:bg-sky-600 transition shadow-md">Kirim Data Tracer Study</button>"""

html_tracer_repl = """                        <div class="mb-4">
                            <label class="block text-xs font-bold text-gray-500 mb-2">Saran / Masukan untuk Kampus</label>
                            <textarea name="saran" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm h-20 focus:outline-none focus:ring-2 focus:ring-sky-500"></textarea>
                        </div>
                        <div class="mb-4">
                            <label class="block text-xs font-bold text-gray-500 mb-2">Berapa hasil dari 2 + 2? (CAPTCHA)</label>
                            <input type="text" name="captcha_answer" required class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500">
                        </div>
                        <button type="submit" class="w-full bg-sky-500 text-white font-bold py-3 rounded-xl hover:bg-sky-600 transition shadow-md">Kirim Data Tracer Study</button>"""
code = code.replace(html_tracer_form, html_tracer_repl)

# Also fix the verifikasi_surat route bug (using hasattr instead of directly accessing)
verifikasi_orig = """@app.route('/verifikasi/surat/<s_id>', methods=['GET'])
def verifikasi_surat(s_id):
    surat = SuratOtomatis.query.filter_by(qr_code=s_id).first()
    if not surat:
        return "Surat tidak ditemukan atau palsu.", 404
    return f"Surat Resmi STIESAM. Jenis: {surat.jenis_surat}. Atas Nama NPM: {surat.npm}. Diterbitkan pada {surat.tanggal}."
"""
verifikasi_repl = """@app.route('/verifikasi/surat/<s_id>', methods=['GET'])
def verifikasi_surat(s_id):
    surat = SuratOtomatis.query.filter_by(qr_code=s_id).first()
    if not surat:
        return "Surat tidak ditemukan atau palsu.", 404
    # The SuratOtomatis model actually HAS `tanggal` as per memory & codebase: tanggal = db.Column(db.Date, default=datetime.date.today)
    # But just in case, we will safeguard it.
    tgl = getattr(surat, 'tanggal', surat.created_at)
    return f"Surat Resmi STIESAM. Jenis: {surat.jenis_surat}. Atas Nama NPM: {surat.npm}. Diterbitkan pada {tgl}."
"""
code = code.replace(verifikasi_orig, verifikasi_repl)

# Fix cache clearing. We used `pass` earlier. We should use `cache.clear()` where appropriate.
# All occurrences of `cache.delete('imsakiyah_schedule')` should be changed to `cache.clear()`. Let's revert and do that properly.
# Oh, we already stripped out `cache.delete('imsakiyah_schedule')` in patch 7!
# Let's fix the remaining `pass` that replaced `cache.delete`
code = re.sub(r'\n\s+pass\n\n\s+except Exception as e:', '\n        cache.clear()\n\n    except Exception as e:', code)
code = re.sub(r'\n\s+pass\s+#.*?\n\n\s+except Exception as e:', '\n        cache.clear()\n\n    except Exception as e:', code)

with open("kampus-stie-samarinda-34 ( idcloudhost - Eight Layer of Quality Control ).py", "w") as f:
    f.write(code)
