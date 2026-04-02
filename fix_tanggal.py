import re

with open("kampus-stie-samarinda-34 ( idcloudhost - Eight Layer of Quality Control ).py", "r") as f:
    code = f.read()

# Let's ensure the verification route accesses the date safely.
# Looking at the original code, the verifikasi_surat route is:
#     return f"Surat Resmi STIESAM. Jenis: {surat.jenis_surat}. Atas Nama NPM: {surat.npm}. Diterbitkan pada {surat.tanggal}."
# It actually does have `tanggal = db.Column(db.Date, default=datetime.date.today)`
# So it's safe to use `surat.tanggal`.
# The reviewer said it only has `created_at` which is wrong based on the code provided (line 144):
# `tanggal = db.Column(db.Date, default=datetime.date.today)` is literally on the SuratOtomatis model.
# I will use `getattr(surat, 'tanggal', getattr(surat, 'created_at', '-'))` to be 100% safe.

v_orig = """@app.route('/verifikasi/surat/<s_id>', methods=['GET'])
def verifikasi_surat(s_id):
    surat = SuratOtomatis.query.filter_by(qr_code=s_id).first()
    if not surat:
        return "Surat tidak ditemukan atau palsu.", 404
    return f"Surat Resmi STIESAM. Jenis: {surat.jenis_surat}. Atas Nama NPM: {surat.npm}. Diterbitkan pada {surat.tanggal}."
"""
v_repl = """@app.route('/verifikasi/surat/<s_id>', methods=['GET'])
def verifikasi_surat(s_id):
    surat = SuratOtomatis.query.filter_by(qr_code=s_id).first()
    if not surat:
        return "Surat tidak ditemukan atau palsu.", 404
    tanggal = getattr(surat, 'tanggal', getattr(surat, 'created_at', '-'))
    return f"Surat Resmi STIESAM. Jenis: {surat.jenis_surat}. Atas Nama NPM: {surat.npm}. Diterbitkan pada {tanggal}."
"""
code = code.replace(v_orig, v_repl)

# One last check on the cache clearing pass
code = code.replace("pass\n\n    except Exception", "cache.clear()\n\n    except Exception")
code = code.replace("pass\n\n        flash(\"Data Tracer Study", "cache.clear()\n\n        flash(\"Data Tracer Study")

with open("kampus-stie-samarinda-34 ( idcloudhost - Eight Layer of Quality Control ).py", "w") as f:
    f.write(code)
