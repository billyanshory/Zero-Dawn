import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# 1. Add specific comment for profil_medis query
# The query is `ProfilMedisSiswa.query.filter_by(siswa_id=anak_id).first()`
content = content.replace(
    "profil_medis = ProfilMedisSiswa.query.filter_by(siswa_id=anak_id).first()",
    "profil_medis = ProfilMedisSiswa.query.filter_by(siswa_id=anak_id).first()  # Result may be None for students with no medical profile; template guards handle this via conditional rendering"
)

# Wait, the instruction says to audit every `.first()` and `db.session.get(...)`
# Let's write a script to find them first to see if there are any others needing 404s.
# "add a four-hundred-four return when the result is None and the downstream code would otherwise crash on attribute access, or add the explanatory comment when the None case is already handled."
