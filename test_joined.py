import re

with open("backup.py", "r") as f:
    text = f.read()

# Let's find some N+1 queries.
# Specifically in dosen_dashboard:
# all_tagihan = TagihanKuliah.query.filter(TagihanKuliah.npm.in_(npms_in_krs)).all() if npms_in_krs else []
# That is already optimized! But let's check others.

print(text.find("joinedload"))
