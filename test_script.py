import re

text = '<tajweed class="idgh_ghn">idgham</tajweed> <tajweed class="ikhf">ikhfa</tajweed> <tajweed class="iqlb">iqlab</tajweed> <tajweed class="qlq">qalqalah</tajweed> <tajweed class="ghn">ghunnah</tajweed> <tajweed class="madd_normal">madd</tajweed> <tajweed class="ham_wasl">plain</tajweed>'

# Note: In python re.sub, \1 is used instead of $1
t1 = re.sub(r'<tajweed class="idgh[^"]*"[^>]*>(.*?)</tajweed>', r'<span onclick="showTajwidRule(\'idgham\')" class="text-red-500">\1</span>', text, flags=re.IGNORECASE)
t2 = re.sub(r'<tajweed class="ikhf[^"]*"[^>]*>(.*?)</tajweed>', r'<span onclick="showTajwidRule(\'ikhfa\')" class="text-emerald-500">\1</span>', t1, flags=re.IGNORECASE)
t3 = re.sub(r'<tajweed class="iqlb[^"]*"[^>]*>(.*?)</tajweed>', r'<span onclick="showTajwidRule(\'iqlab\')" class="text-blue-500">\1</span>', t2, flags=re.IGNORECASE)
t4 = re.sub(r'<tajweed class="qlq[^"]*"[^>]*>(.*?)</tajweed>', r'<span onclick="showTajwidRule(\'qalqalah\')" class="text-purple-500">\1</span>', t3, flags=re.IGNORECASE)
t5 = re.sub(r'<tajweed class="ghn[^"]*"[^>]*>(.*?)</tajweed>', r'<span onclick="showTajwidRule(\'ghunnah\')" class="text-orange-500">\1</span>', t4, flags=re.IGNORECASE)
t6 = re.sub(r'<tajweed class="madd[^"]*"[^>]*>(.*?)</tajweed>', r'<span onclick="showTajwidRule(\'madd\')" class="text-teal-500">\1</span>', t5, flags=re.IGNORECASE)
t7 = re.sub(r'<tajweed class="[^"]*"[^>]*>(.*?)</tajweed>', r'<span>\1</span>', t6, flags=re.IGNORECASE)

print("Parsed Text:")
print(t7)

assert "text-red-500" in t7
assert "text-emerald-500" in t7
assert "text-blue-500" in t7
assert "text-purple-500" in t7
assert "text-orange-500" in t7
assert "text-teal-500" in t7
assert "<span>plain</span>" in t7
print("Regex matches pass!")
