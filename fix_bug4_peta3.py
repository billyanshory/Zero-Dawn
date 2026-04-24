import re

with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Let's escape the { } in the script block in IDUL_ADHA_PEMBAGIAN_CEK_HTML
new_pembagian_html = re.sub(
    r"<script>(.*?)</script>",
    lambda m: "<script>" + m.group(1).replace("{", "{{").replace("}", "}}") + "</script>",
    content[content.find("IDUL_ADHA_PEMBAGIAN_CEK_HTML = '''"): content.find("IDUL_ADHA_PEMBAGIAN_ADMIN_HTML = '''")],
    flags=re.DOTALL
)

# Replace them back in content
content = content[:content.find("IDUL_ADHA_PEMBAGIAN_CEK_HTML = '''")] + new_pembagian_html + content[content.find("IDUL_ADHA_PEMBAGIAN_ADMIN_HTML = '''"):]

with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
