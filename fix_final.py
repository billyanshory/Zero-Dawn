import re

with open("kampus-stie-samarinda-34 ( idcloudhost - Eight Layer of Quality Control ).py", "r") as f:
    code = f.read()

# 1. Fix verifikasi surat (tanggal -> created_at or check if tanggal exists)
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
    return f"Surat Resmi STIESAM. Jenis: {surat.jenis_surat}. Atas Nama NPM: {surat.npm}. Diterbitkan pada {surat.tanggal if hasattr(surat, 'tanggal') else surat.created_at.strftime('%Y-%m-%d')}."
"""
code = code.replace(verifikasi_orig, verifikasi_repl)

# 2. Fix cache clearing (restore cache.clear() where appropriate)
# For routes that modify data but don't strictly need imsakiyah clear, we use cache.clear() as requested.
# Let's replace `pass # no cache clear` and `pass` with `cache.clear()` where data is updated.
code = re.sub(r'pass\s*#\s*no cache clear', 'cache.clear()', code)
code = re.sub(r'pass\s*#\s*removed cache delete', 'cache.clear()', code)

# Let's manually replace `pass` that was replacing `cache.delete('imsakiyah_schedule')`
# We can just do a mass replace of the specific `pass` we added
code = re.sub(r'\n\s+pass\n\n\s+except Exception as e:', '\n        cache.clear()\n\n    except Exception as e:', code)


# 3. Check tracer study CAPTCHA
# The user's prompt said "Tambahkan CAPTCHA pada form tracer study publik untuk mencegah spam otomatis."
# The reviewer said the frontend was not updated. BUT I DID update the HTML in `BASE_LAYOUT` for `tracer_html_repl` in my previous scripts.
# Let's verify if the HTML actually contains the captcha.
