import re
import os

with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Did I accidentally leave "import secrets" added in a wrong place or break an import block?
import_block = content[:1000]
print("Imports check:")
print(import_block)
