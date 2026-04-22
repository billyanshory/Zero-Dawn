import re

with open("masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban ).py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "session[" in line:
        print(f"Line {i+1}: {line.strip()}")
    if "session.get(" in line:
        print(f"Line {i+1}: {line.strip()}")
