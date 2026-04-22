with open("masjid-al-hijrah-61 ( idcloudhost - tombol akses, page, & first fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

import re

# Look at the layout context around the new header
match = re.search(r'(<!-- DESKTOP SPLIT HEADER -->.*?<!-- MAIN CONTENT -->)', content, re.DOTALL)
if match:
    print(match.group(1)[:500])
else:
    print("Not found exactly.")

# Let's search for what's immediately after the new_hero block
start = content.find("<!-- DESKTOP SPLIT HEADER -->")
print(content[start:start+1000])
