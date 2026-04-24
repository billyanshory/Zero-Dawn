import re

with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Let's escape the { } in the script block in IDUL_ADHA_PANDUAN_HTML
new_panduan_html = re.sub(
    r"<script>(.*?)</script>",
    lambda m: "<script>" + m.group(1).replace("{", "{{").replace("}", "}}") + "</script>",
    content[content.find("IDUL_ADHA_PANDUAN_HTML = '''"):],
    flags=re.DOTALL
)

# And check IDUL_ADHA_LAPORAN_HTML for {} in script block
new_laporan_html = re.sub(
    r"<script>(.*?)</script>",
    lambda m: "<script>" + m.group(1).replace("{", "{{").replace("}", "}}") + "</script>",
    content[content.find("IDUL_ADHA_LAPORAN_HTML = '''"): content.find("IDUL_ADHA_HEWAN_ADMIN_HTML = '''")],
    flags=re.DOTALL
)

# Replace them back in content
content = content[:content.find("IDUL_ADHA_LAPORAN_HTML = '''")] + new_laporan_html + content[content.find("IDUL_ADHA_HEWAN_ADMIN_HTML = '''"):content.find("IDUL_ADHA_PANDUAN_HTML = '''")] + new_panduan_html

with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
