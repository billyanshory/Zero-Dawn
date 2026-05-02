import re

with open("masjid-al-hijrah-72 - alternate - ( idcloudhost - Second Layer of Quality Control - Error Handling & Resilience - v.71 - Opus 4.6 Ex. Think ).py", "r") as f:
    content = f.read()

kupon_search_target = """        kupon = QurbanKupon.query.filter((QurbanKupon.nomor_kupon == q) | (QurbanKupon.nama_penerima.like(f"%{q}%"))).first()"""
kupon_search_replacement = """        q_escaped = q.replace('%', r'\%').replace('_', r'\_')
        kupon = QurbanKupon.query.filter((QurbanKupon.nomor_kupon == q) | (QurbanKupon.nama_penerima.like(f"%{q_escaped}%", escape='\\\\'))).first()"""
content = content.replace(kupon_search_target, kupon_search_replacement)

with open("masjid-al-hijrah-72 - alternate - ( idcloudhost - Second Layer of Quality Control - Error Handling & Resilience - v.71 - Opus 4.6 Ex. Think ).py", "w") as f:
    f.write(content)

print("Patched successfully")
