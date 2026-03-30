import re

with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "r") as f:
    content = f.read()

# 1. Fix relationships by using foreign() inside the relationship definition properly without string parsing issues
rel_replace = """    krs_rel = db.relationship('KRSMahasiswa', backref='user_krs', primaryjoin="User.username == KRSMahasiswa.npm", foreign_keys="[KRSMahasiswa.npm]")
    tagihan_rel = db.relationship('TagihanKuliah', backref='user_tagihan', primaryjoin="User.username == TagihanKuliah.npm", foreign_keys="[TagihanKuliah.npm]")"""

content = content.replace("    krs_rel = db.relationship('KRSMahasiswa', backref='user_krs', primaryjoin=\"User.username == foreign(KRSMahasiswa.npm)\")\n    tagihan_rel = db.relationship('TagihanKuliah', backref='user_tagihan', primaryjoin=\"User.username == foreign(TagihanKuliah.npm)\")", rel_replace)

with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "w") as f:
    f.write(content)
