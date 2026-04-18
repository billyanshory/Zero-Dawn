import re

with open('slb.py', 'r') as f:
    content = f.read()

# remove import urllib.request, as it's not needed anymore
content = content.replace("import urllib.request\n", "")

with open('slb.py', 'w') as f:
    f.write(content)
