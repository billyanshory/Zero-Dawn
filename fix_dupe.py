import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# Did I accidentally define `_save_uploaded_media` twice?
# Let's count them.
print("Count of _save_uploaded_media:", content.count("def _save_uploaded_media"))
