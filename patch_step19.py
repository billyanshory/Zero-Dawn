with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

text = text.replace("profil_medis.id if profil_medis else \\'default\\'", "profil_medis.id if profil_medis and profil_medis.id else 'default'")
text = text.replace("akun.anak_id if akun and akun.anak_id else \\'default\\'", "akun.anak_id if akun and akun.anak_id else 'default'")

with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
    f.write(text)
