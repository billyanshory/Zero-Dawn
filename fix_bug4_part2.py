import re

with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Make sure IDUL_ADHA_PETA_DISTRIBUSI_HTML does not have unescaped {}

html_part = re.search(r"IDUL_ADHA_PETA_DISTRIBUSI_HTML = '''(.*?)'''", content, re.DOTALL)
if html_part:
    # Just in case there are some {} hiding in JS, but there is no JS script block with { inside the HTML part
    pass
